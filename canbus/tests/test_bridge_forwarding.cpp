// Standalone native test for bridge_forwarding.h (no ESPHome required).
// Build & run (from repo root):
//   g++ -std=c++17 -Wall -Wextra canbus/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge
//
// Covers the ADR-0005 store-and-forward queue: FIFO order and payload fidelity,
// the oversize/overflow drop rules (drop-newest, counted), the paced drain cap,
// TX-failure handling (a refused send is not "forwarded": bounded in-order retry,
// then a counted drop), and the latched heartbeat flags.

#include "../protocol/bridge_forwarding.h"
#include <cassert>
#include <cstdio>

// Drain through an always-accepting sender and return what was handed to it.
static std::vector<BridgeFrame> drain_ok(std::vector<BridgeFrame> &q, BridgeStats &s,
                                         std::size_t max_frames = BRIDGE_DRAIN_MAX)
{
  std::vector<BridgeFrame> out;
  bridge_drain_send(q, s, [&](const BridgeFrame &f) { out.push_back(f); return true; }, max_frames);
  return out;
}

int main()
{
  // --- enqueue/drain round-trip preserves id, flag, length, bytes, order ---
  std::vector<BridgeFrame> q;
  BridgeStats s{};
  assert(bridge_enqueue(q, s, can_id(CAT_INPUT, 100), true, button_payload(3, EVT_CLICK)));
  assert(bridge_enqueue(q, s, can_id(CAT_STATUS, 101), true, heartbeat_payload(7, ERR_NONE)));
  assert(q.size() == 2 && s.enqueued == 2);
  auto out = drain_ok(q, s);                  // default cap = BRIDGE_DRAIN_MAX = 2
  assert(out.size() == 2 && q.empty() && s.forwarded == 2);
  assert(out[0].can_id == can_id(CAT_INPUT, 100) && out[0].extended);
  assert(out[0].len == 4 && out[0].data[2] == 3 && out[0].data[3] == EVT_CLICK);
  assert(out[1].can_id == can_id(CAT_STATUS, 101));
  assert(out[1].len == 5 && out[1].data[3] == 7 && out[1].data[4] == 0);  // uptime LE

  // --- drain of an empty queue is a no-op ---
  assert(drain_ok(q, s).empty() && s.forwarded == 2);

  // --- oversize frame rejected, queue untouched ---
  std::vector<uint8_t> nine(9, 0xAA);
  assert(!bridge_enqueue(q, s, 0x123, true, nine));
  assert(q.empty() && s.dropped_oversize == 1 && s.enqueued == 2);
  std::vector<uint8_t> eight(8, 0xBB);            // exactly CAN_FRAME_MAX is fine
  assert(bridge_enqueue(q, s, 0x123, true, eight));
  assert(q.size() == 1 && q[0].len == 8 && q[0].data[7] == 0xBB);
  q.clear();

  // --- overflow drops the NEW frame; queued frames and their order survive ---
  std::vector<BridgeFrame> full;
  BridgeStats fs{};
  for (uint32_t i = 0; i < BRIDGE_QUEUE_MAX; ++i)
    assert(bridge_enqueue(full, fs, 1000 + i, true, {PROTO_V1}));
  assert(full.size() == BRIDGE_QUEUE_MAX);
  assert(!bridge_enqueue(full, fs, 9999, true, {PROTO_V1}));
  assert(full.size() == BRIDGE_QUEUE_MAX && fs.dropped_overflow == 1);
  assert(full.front().can_id == 1000 && full.back().can_id == 1000 + BRIDGE_QUEUE_MAX - 1);

  // --- drain cap: at most max_frames per call, oldest first, FIFO across calls ---
  auto batch = drain_ok(full, fs);
  assert(batch.size() == BRIDGE_DRAIN_MAX);
  assert(batch[0].can_id == 1000 && batch[1].can_id == 1001);
  batch = drain_ok(full, fs, 3);              // explicit cap
  assert(batch.size() == 3 && batch[0].can_id == 1002 && batch[2].can_id == 1004);
  assert(full.size() == BRIDGE_QUEUE_MAX - 5);
  assert(fs.forwarded == 5);

  // --- heartbeat flag: clean stats -> ERR_NONE; any drop in either direction latches ---
  BridgeStats clean{};
  assert(bridge_error_flags(clean, clean) == ERR_NONE);
  assert(bridge_error_flags(fs, clean) == ERR_BRIDGE_QUEUE_OVERFLOW);   // overflow side
  assert(bridge_error_flags(clean, s) == ERR_BRIDGE_QUEUE_OVERFLOW);    // oversize side
  // cumulative counters never reset -> the flag is sticky by construction
  assert(bridge_error_flags(fs, s) == ERR_BRIDGE_QUEUE_OVERFLOW);

  // --- TX failure: a refused frame is NOT forwarded, stays at the head, keeps FIFO order ---
  {
    std::vector<BridgeFrame> tq;
    BridgeStats ts{};
    assert(bridge_enqueue(tq, ts, 1, true, {PROTO_V1}));
    assert(bridge_enqueue(tq, ts, 2, true, {PROTO_V1}));
    assert(bridge_enqueue(tq, ts, 3, true, {PROTO_V1}));
    std::vector<uint32_t> sent_ids;
    bool bus_up = false;
    auto sender = [&](const BridgeFrame &f) {
      if (!bus_up) return false;
      sent_ids.push_back(f.can_id);
      return true;
    };
    // Tick 1, bus busy: one refused attempt, rest of the tick skipped (head-of-line).
    auto r = bridge_drain_send(tq, ts, sender);
    assert(r.sent == 0 && r.failed == 1 && r.dropped == 0);
    assert(ts.forwarded == 0 && ts.tx_failed == 1 && ts.dropped_tx == 0);
    assert(tq.size() == 3 && tq.front().can_id == 1 && tq.front().tx_attempts == 1);
    // Bus recovers: the retried frame goes first, order preserved, nothing lost.
    bus_up = true;
    r = bridge_drain_send(tq, ts, sender);
    assert(r.sent == 2 && r.failed == 0 && ts.forwarded == 2 && ts.dropped_tx == 0);
    assert(sent_ids.size() == 2 && sent_ids[0] == 1 && sent_ids[1] == 2);
    r = bridge_drain_send(tq, ts, sender);
    assert(sent_ids.size() == 3 && sent_ids[2] == 3 && tq.empty());
    // A recovered failure latches nothing in the bridge flags (it only counted).
    assert(ts.tx_failed == 1 && bridge_error_flags(ts, BridgeStats{}) == ERR_NONE);
  }

  // --- TX failure past the retry bound: dropped, counted, draining moves on ---
  {
    std::vector<BridgeFrame> dq;
    BridgeStats ds{};
    assert(bridge_enqueue(dq, ds, 10, true, {PROTO_V1}));
    assert(bridge_enqueue(dq, ds, 11, true, {PROTO_V1}));
    int attempts_on_10 = 0;
    bool b11_ok = true;
    auto dead_head = [&](const BridgeFrame &f) {
      if (f.can_id == 10) { attempts_on_10++; return false; }
      return b11_ok;
    };
    for (unsigned tick = 1; tick < BRIDGE_TX_ATTEMPTS_MAX; ++tick) {
      auto r = bridge_drain_send(dq, ds, dead_head);
      assert(r.failed == 1 && r.dropped == 0 && r.sent == 0 && dq.size() == 2);
    }
    assert(ds.dropped_tx == 0 && bridge_error_flags(ds, BridgeStats{}) == ERR_NONE);
    // Final attempt: frame 10 is given up on, and frame 11 behind it is sent the same tick.
    auto r = bridge_drain_send(dq, ds, dead_head);
    assert(attempts_on_10 == (int) BRIDGE_TX_ATTEMPTS_MAX);
    assert(r.failed == 1 && r.dropped == 1 && r.sent == 1);
    assert(ds.dropped_tx == 1 && ds.tx_failed == BRIDGE_TX_ATTEMPTS_MAX && ds.forwarded == 1);
    assert(dq.empty());
    // Sticky ERR_CAN_TX_FAIL, from either direction, distinct from the overflow bit.
    assert(bridge_error_flags(ds, BridgeStats{}) == ERR_CAN_TX_FAIL);
    assert(bridge_error_flags(BridgeStats{}, ds) == ERR_CAN_TX_FAIL);
    BridgeStats of{};
    of.dropped_overflow = 1;
    assert(bridge_error_flags(ds, of) == (ERR_CAN_TX_FAIL | ERR_BRIDGE_QUEUE_OVERFLOW));
    // A frame's attempt budget is its own: the next frame starts fresh.
    assert(bridge_enqueue(dq, ds, 12, true, {PROTO_V1}));
    assert(dq.front().tx_attempts == 0);
  }

  // --- max_frames caps SENT frames per tick, even when failures are interleaved ---
  {
    std::vector<BridgeFrame> cq;
    BridgeStats cs{};
    for (uint32_t i = 0; i < 5; ++i) assert(bridge_enqueue(cq, cs, 20 + i, true, {PROTO_V1}));
    auto r = bridge_drain_send(cq, cs, [](const BridgeFrame &) { return true; });
    assert(r.sent == BRIDGE_DRAIN_MAX && cq.size() == 5 - BRIDGE_DRAIN_MAX);
  }

  // --- static stores exist and are distinct per direction ---
  bridge_queue_to_backbone().clear();
  bridge_queue_to_zone().clear();
  assert(bridge_enqueue(bridge_queue_to_backbone(), bridge_stats_to_backbone(),
                        can_id(CAT_INPUT, 100), true, button_payload(0, EVT_CLICK)));
  assert(bridge_queue_to_backbone().size() == 1 && bridge_queue_to_zone().empty());

  printf("test_bridge_forwarding: all assertions passed\n");
  return 0;
}
