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
// cleared once a heartbeat that carried it was ACCEPTED by the controller
// (MCP2515: loaded into a TX buffer, not ACKed; TWAI: queued):
//   - NOT sticky until power cycle. Nodes are flashed once and walled in, so a
//     permanent "degraded" from one transient would never clear short of a power cycle
//     and would train everyone to ignore the alert. The gateway forwards error_flags
//     changes as edge events including the return to 0 (node_health.h
//     HEALTH_EDGE_ERROR), so HA sees both "TX failed" and "TX recovered".
//   - NOT cleared by a timer or by the next arbitrary success: only an accepted
//     heartbeat clears it, because that is the one frame known to carry the flag. A refused
//     heartbeat keeps (and re-sets) the flag, so a node that was cut off reports the outage
//     the first time its bus works again, however long that takes. Acceptance is not
//     delivery: a dead bus only surfaces once the TX buffers stay full.
//   - The segment bridge keeps its own STICKY bit for frames it gave up on
//     (bridge_forwarding.h): a dropped forwarded frame is a lost event, not a passing
//     condition. It ORs that into error_flags; this latch is OR-ed in separately at
//     heartbeat time, so neither can clear the other.
//
// ERR_CAN_BUS_OFF is deliberately not handled here: nothing in ESPHome exposes the
// controller's bus-off state (see the note at the constant in canbus_protocol.h).
//
// Pure logic only — no ESPHome includes — natively tested (tests/test_tx_health.cpp).
// ESPHome is single-threaded for lambdas, so the heartbeat's read-send-clear sequence
// cannot interleave with another note.
// =============================================================================

struct TxHealth
{
  bool pending;   // a failure has not yet been reported by an accepted heartbeat
};

// Record the outcome of one send_data() (ok = it returned ERROR_OK).
inline void tx_health_note(TxHealth &h, bool ok)
{
  if (!ok)
    h.pending = true;
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

// Call right after the heartbeat built from tx_health_flags() was sent. Accepted by the
// controller (not necessarily delivered): whatever was pending was handed off, clear it. Refused: that failure counts too, and the flag
// stays pending for the next heartbeat.
inline void tx_health_heartbeat_sent(TxHealth &h, bool ok)
{
  if (ok)
    h.pending = false;
  else
    tx_health_note(h, false);
}

// The node's single TX-health record. Owned here instead of an ESPHome `globals:` entry
// because globals storage is emitted before user includes (same reasoning as
// ha_arbitration.h / bridge_forwarding.h).
inline TxHealth &tx_health()
{
  static TxHealth store{};
  return store;
}
