#pragma once
#include <cstdint>

#include "canbus_protocol.h"

// =============================================================================
// tx_health.h — node-side CAN TX failure reporting (ERR_CAN_TX_FAIL)
// =============================================================================
//
// Every node's controller can refuse a frame: send_data() returns something other
// than ERROR_OK when all TX buffers are busy (MCP2515: a buffer stays busy until the
// frame is ACKed, so this is what a dead/unterminated/disconnected bus looks like) or
// the TWAI TX queue is full. Until this header the refusal was at best logged on the
// node, where nobody reads it, and the health monitor's node_error alert class only
// ever fired for the bridge's queue overflow. This tracks the failure so the node's
// next heartbeat carries ERR_CAN_TX_FAIL.
//
// LATCH / CLEAR POLICY — set on any failed send, transmitted by the next heartbeat,
// cleared once a heartbeat that carried it was ACCEPTED by the controller:
//   - NOT sticky until power cycle. Nodes are flashed once and walled in, so a
//     permanent "degraded" from one transient would never clear short of a power cycle
//     and would train everyone to ignore the alert. The gateway forwards error_flags
//     changes as edge events including the return to 0 (node_health.h
//     HEALTH_EDGE_ERROR), so HA sees both "TX failed" and "TX recovered".
//   - NOT cleared by a timer or by the next arbitrary success: only a successful
//     heartbeat proves the flag actually left the node. A refused heartbeat keeps (and
//     re-sets) the flag, so a node that was cut off reports the outage the first time its
//     bus works again, however long that takes.
//   - The segment bridge keeps its own STICKY bit for frames it gave up on
//     (bridge_forwarding.h): a dropped forwarded frame is a lost event, not a passing
//     condition. It ORs that into error_flags; this latch is OR-ed in separately at
//     heartbeat time, so neither can clear the other.
//
// ERR_CAN_BUS_OFF is deliberately not handled here: nothing in ESPHome exposes the
// controller's bus-off state (see the note at the constant in canbus_protocol.h).
//
// TX WATCHDOG (review R-17) — the second half of this header. ESPHome 2026.8.0's esp32_can
// never calls twai_initiate_recovery(), so an ESP32 (TWAI) node that goes bus-off stays off
// the bus until it is rebooted, and nothing in ESPHome tells us it happened. What it does
// show is the effect: the TX queue never drains, so heartbeats start being refused and keep
// being refused. This counts CONSECUTIVE refused heartbeats and decides when a reboot
// (canbus/packages/tx_watchdog.yaml) is the only remaining remedy. Why heartbeats and not any
// send: the heartbeat goes out on can0 (the controller-facing port, node_core.yaml invariant 1
// — on a T-2CAN bridge that is the TWAI side), is sent on a fixed 30 s cadence, and is never
// refused by the zone side's MCP2515, so a dead zone segment cannot make a bridge reboot.
//
//   REBOOT POLICY — reboot after TX_WDG_REBOOT_AFTER_REFUSED consecutive refused heartbeats
//   (10 = 5 min of heartbeats at 30 s), then back off: the threshold doubles for each
//   reboot that did not bring the bus back (10, 20, 40, 80 heartbeats; capped), so a node on
//   a bus that is genuinely dead reboots at most every ~43 min instead of looping. The
//   backoff level is persisted by the package (it must survive the reboot it causes) and
//   only cleared by proof of recovery: TX_WDG_PROVEN_ACCEPTED consecutive accepted
//   heartbeats. "Accepted" alone is NOT proof on TWAI — twai_transmit() succeeds as long as
//   the TX queue (default 5 + the hardware slot) has room, so a freshly rebooted node on a
//   dead bus is accepted ~6 times before refusals resume; 12 accepted in a row means the
//   queue provably drained. A transient full queue (a burst, a busy bus) refuses one or two
//   heartbeats at most and never reaches 10 in a row.
//
// Pure logic only — no ESPHome includes — natively tested (tests/test_tx_health.cpp).
// ESPHome is single-threaded for lambdas, so the heartbeat's read-send-clear sequence
// cannot interleave with another note.
// =============================================================================

struct TxHealth
{
  bool pending;       // a failure has not yet been reported by an accepted heartbeat
  uint32_t failures;  // cumulative refused sends (diagnostic only; never reported on the wire)
  // Watchdog inputs (R-17): the current run of refused / accepted HEARTBEATS (saturating).
  // Only tx_health_heartbeat_sent() moves them, so frames refused on another port (a bridge's
  // zone side) or by a burst never count toward a reboot.
  uint16_t hb_refused_run;
  uint16_t hb_accepted_run;
};

// Record the outcome of one send_data() (ok = it returned ERROR_OK).
inline void tx_health_note(TxHealth &h, bool ok)
{
  if (!ok) {
    h.pending = true;
    h.failures++;
  }
}

// Same, passing the outcome through — wraps a send expression without an extra statement.
inline bool tx_health_track(TxHealth &h, bool ok)
{
  tx_health_note(h, ok);
  return ok;
}

// The flag byte contribution for the heartbeat about to be built. OR it with error_flags.
inline uint8_t tx_health_flags(const TxHealth &h)
{
  return h.pending ? ERR_CAN_TX_FAIL : ERR_NONE;
}

// Call right after the heartbeat built from tx_health_flags() was sent. Accepted: whatever
// was pending has been reported, clear it. Refused: that failure counts too, and the flag
// stays pending for the next heartbeat.
inline void tx_health_heartbeat_sent(TxHealth &h, bool ok)
{
  if (ok) {
    h.pending = false;
    h.hb_refused_run = 0;
    if (h.hb_accepted_run < 0xFFFF)
      h.hb_accepted_run++;
  } else {
    tx_health_note(h, false);
    h.hb_accepted_run = 0;
    if (h.hb_refused_run < 0xFFFF)
      h.hb_refused_run++;
  }
}

// --------------- TX watchdog decision (R-17) ---------------

inline constexpr uint16_t TX_WDG_REBOOT_AFTER_REFUSED = 10;  // consecutive refused heartbeats (5 min @ 30 s)
inline constexpr uint8_t TX_WDG_LEVEL_MAX = 3;               // backoff cap: threshold 10 << 3 = 80 heartbeats
// 2 x (TWAI TX queue 5 + 1 hardware slot): acceptance beyond the queue depth proves frames
// leave. Raise it with tx_queue_len if a node ever configures a deeper queue.
inline constexpr uint16_t TX_WDG_PROVEN_ACCEPTED = 12;

// Consecutive refused heartbeats that trigger a reboot at this persisted backoff level. The
// level comes from flash, so clamp it: garbage must not shift past the cap (or overflow).
inline uint16_t tx_watchdog_threshold(uint8_t level)
{
  return (uint16_t)(TX_WDG_REBOOT_AFTER_REFUSED << (level > TX_WDG_LEVEL_MAX ? TX_WDG_LEVEL_MAX : level));
}

// True when the refused-heartbeat run has reached the threshold: reboot now.
inline bool tx_watchdog_should_reboot(const TxHealth &h, uint8_t level)
{
  return h.hb_refused_run >= tx_watchdog_threshold(level);
}

// The level to persist BEFORE rebooting (saturating), so the next boot waits longer.
inline uint8_t tx_watchdog_level_after_reboot(uint8_t level)
{
  return level >= TX_WDG_LEVEL_MAX ? TX_WDG_LEVEL_MAX : (uint8_t)(level + 1);
}

// True when the persisted level can be cleared: the bus demonstrably works again.
inline bool tx_watchdog_recovered(const TxHealth &h, uint8_t level)
{
  return level != 0 && h.hb_accepted_run >= TX_WDG_PROVEN_ACCEPTED;
}

// The node's single TX-health record. Owned here instead of an ESPHome `globals:` entry
// because globals storage is emitted before user includes (same reasoning as
// ha_arbitration.h / bridge_forwarding.h).
inline TxHealth &tx_health()
{
  static TxHealth store{};
  return store;
}
