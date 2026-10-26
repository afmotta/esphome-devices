#pragma once
#include <cstdint>
#include <cstddef>
#include <vector>

#include "canbus_protocol.h"

// =============================================================================
// Segment-bridge store-and-forward queues — ADR-0005 (segmented multi-bus)
// =============================================================================
//
// A bridge joins two CAN segments: a backbone (controller) side and a zone
// (secondary) side. Forwarding is forward-all both ways (ADR-0005 open item 3:
// the controller needs all node traffic, management must reach every segment);
// the loop-free tree topology and the controllers' no-self-reception (TWAI and
// MCP2515 alike in normal mode) mean a forwarded frame can never echo back
// through the same bridge.
//
// Frames are queued on receive and drained on a fixed tick, at most
// BRIDGE_DRAIN_MAX per direction per tick. The pacing matters more than the
// buffering: on the LilyGO T-2CAN the zone side is an MCP2515 with only 3 TX
// buffers, and a 125 kbps frame takes ~1 ms on the wire, so blasting a
// received burst straight into send_data() would overrun the TX side. The
// queue absorbs the burst; the drain cap meters it out at a rate the weaker
// transmitter can sustain (applied to both directions for symmetry).
//
// Pure logic only — no ESPHome includes — so the queue/pacing machinery is
// natively testable (see tests/test_bridge_forwarding.cpp).
// =============================================================================

// A received frame held for forwarding to the other segment.
struct BridgeFrame
{
  uint32_t can_id;
  bool extended;
  uint8_t len;
  uint8_t data[CAN_FRAME_MAX];
  uint8_t tx_attempts;   // TX attempts the controller has refused so far (bridge_drain_send)
};

// Cumulative per-direction counters. dropped_* never reset, so any nonzero
// value latches its heartbeat flag until reboot (conservative: a bridge that
// ever dropped a frame stays visibly degraded, ADR-0005 fail-safe posture).
// tx_failed counts refused TX ATTEMPTS, including ones a later retry recovered —
// it is a diagnostic, not a loss; only dropped_tx is a lost frame.
struct BridgeStats
{
  uint32_t enqueued;
  uint32_t forwarded;
  uint32_t dropped_overflow;
  uint32_t dropped_oversize;
  uint32_t tx_failed;
  uint32_t dropped_tx;
};

// Queue depth per direction: ~32 ms of a 100%-utilized 125 kbps segment
// (extended data frame ~1 ms on the wire) — far beyond any home-scale burst.
// Past this the segment itself is saturated and dropping is the honest outcome.
inline constexpr std::size_t BRIDGE_QUEUE_MAX = 32;
// Frames drained per direction per tick. At a 10 ms tick this paces TX to
// 200 frames/s per direction — under the 3 TX buffers and ~1 ms/frame the
// MCP2515 (the weaker TX side) can sustain, and far above expected load.
inline constexpr std::size_t BRIDGE_DRAIN_MAX = 2;
// TX attempts per frame before it is dropped. One attempt per tick, so a frame is held
// 5 ticks (~50 ms at the nominal 10 ms tick, ~100 ms where the loop is gated, e.g. T-2CAN):
// ~50+ frame times at 125 kbps, long enough to ride out a transient buffer-busy spell
// (arbitration loss against a busy segment) yet short enough that a genuinely dead segment
// is declared (dropped_tx -> heartbeat flag) within a heartbeat's worth of traffic instead
// of silently backing the queue up to overflow. The flip side, accepted: a dead egress
// leaves up to BRIDGE_QUEUE_MAX stale events queued, delivered late once it recovers.
inline constexpr uint8_t BRIDGE_TX_ATTEMPTS_MAX = 5;

// Queue a received frame for the other segment. Oversize frames (> 8 data
// bytes; impossible from a conformant CAN controller) are rejected. On a full
// queue the NEW frame is dropped (drop-newest): the already-queued frames are
// older and closer to delivery, and never re-ordering the FIFO keeps event
// sequence intact. Both drops only count — the caller decides what to log.
inline bool bridge_enqueue(std::vector<BridgeFrame> &q, BridgeStats &stats,
                           uint32_t can_id, bool extended,
                           const std::vector<uint8_t> &data)
{
  if (data.size() > CAN_FRAME_MAX) {
    stats.dropped_oversize++;
    return false;
  }
  if (q.size() >= BRIDGE_QUEUE_MAX) {
    stats.dropped_overflow++;
    return false;
  }
  BridgeFrame f{};
  f.can_id = can_id;
  f.extended = extended;
  f.len = (uint8_t) data.size();
  for (std::size_t i = 0; i < data.size(); ++i)
    f.data[i] = data[i];
  q.push_back(f);
  stats.enqueued++;
  return true;
}

// What one drain tick did: frames the controller accepted, TX attempts it refused, and
// frames given up on (BRIDGE_TX_ATTEMPTS_MAX refusals) — the caller logs the latter.
struct BridgeDrainResult
{
  std::size_t sent;
  std::size_t failed;
  std::size_t dropped;
};

// Forward up to max_frames from the front of the queue, oldest first, via send(frame)
// -> bool (true = the controller accepted it). The frame leaves the queue only on
// acceptance, and `forwarded` counts only accepted frames.
//
// A refused frame STAYS at the front: it is retried on the next tick, which preserves FIFO
// order (event sequence intact, same reason overflow drops the newest) and keeps retries
// paced at one tick apart — a retry storm into already-busy TX buffers would be the exact
// overrun the drain cap exists to prevent. A refusal always ends that direction's tick
// (head-of-line blocking), including the one that drops the frame: the frames behind it
// face the same busy buffers and are tried on the next tick. That bounds a direction to at
// most ONE refused attempt per tick, which matters because a refused twai_transmit_v2 on
// the T-2CAN backbone blocks the main loop for its enqueue timeout. After
// BRIDGE_TX_ATTEMPTS_MAX refusals the frame is dropped (dropped_tx) — a dead segment must
// surface as a counted loss, not as a queue that wedges forever behind one frame. The O(n)
// front-erase is trivially cheap at these sizes (same trade as ha_arbitration.h).
template <typename Send>
inline BridgeDrainResult bridge_drain_send(std::vector<BridgeFrame> &q, BridgeStats &stats,
                                           Send &&send, std::size_t max_frames = BRIDGE_DRAIN_MAX)
{
  BridgeDrainResult r{};
  while (!q.empty() && r.sent < max_frames) {
    BridgeFrame &f = q.front();
    if (send(static_cast<const BridgeFrame &>(f))) {
      stats.forwarded++;
      r.sent++;
      q.erase(q.begin());
      continue;
    }
    stats.tx_failed++;
    r.failed++;
    if (++f.tx_attempts < BRIDGE_TX_ATTEMPTS_MAX)
      break;   // retry next tick
    stats.dropped_tx++;
    r.dropped++;
    q.erase(q.begin());
    break;   // a refusal always ends this direction's tick
  }
  return r;
}

// Heartbeat error flags from both directions' stats; stats are cumulative, so every flag
// here is sticky by construction. Two distinct causes, two bits (they compose in the one
// heartbeat byte): any ingress drop (full queue / oversize) latches
// ERR_BRIDGE_QUEUE_OVERFLOW; any frame abandoned after repeated TX refusals latches
// ERR_CAN_TX_FAIL — the same bit every node uses for "my controller refused a frame", but
// sticky here because a dropped forwarded frame is a lost event, not a passing condition.
// (Transient refusals that a retry recovered do NOT latch this; they surface through
// tx_health.h's non-sticky flag like on any other node.)
inline uint8_t bridge_error_flags(const BridgeStats &to_backbone, const BridgeStats &to_zone)
{
  const uint32_t overflow = to_backbone.dropped_overflow + to_backbone.dropped_oversize +
                            to_zone.dropped_overflow + to_zone.dropped_oversize;
  const uint32_t tx_drops = to_backbone.dropped_tx + to_zone.dropped_tx;
  return (uint8_t) ((overflow > 0 ? ERR_BRIDGE_QUEUE_OVERFLOW : ERR_NONE) |
                    (tx_drops > 0 ? ERR_CAN_TX_FAIL : ERR_NONE));
}

// The bridge's queues and counters. Owned here instead of ESPHome `globals:`
// entries because ESPHome emits globals storage declarations before user
// includes in the generated main.cpp, so a custom struct type never compiles
// as a global (same reasoning as ha_arbitration.h).
inline std::vector<BridgeFrame> &bridge_queue_to_backbone()
{
  static std::vector<BridgeFrame> store;
  return store;
}

inline std::vector<BridgeFrame> &bridge_queue_to_zone()
{
  static std::vector<BridgeFrame> store;
  return store;
}

inline BridgeStats &bridge_stats_to_backbone()
{
  static BridgeStats store{};
  return store;
}

inline BridgeStats &bridge_stats_to_zone()
{
  static BridgeStats store{};
  return store;
}
