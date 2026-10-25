// Standalone native test for tx_health.h (no ESPHome required).
// Build & run (from repo root):
//   g++ -std=c++17 -Wall -Wextra -Icanbus/protocol canbus/tests/test_tx_health.cpp -o /tmp/txh && /tmp/txh
//
// Covers the node-side ERR_CAN_TX_FAIL latch: set by any refused send, carried by the
// next heartbeat, cleared only once a heartbeat carrying it was accepted, and the way it
// composes with a profile's sticky error_flags.

#include "../protocol/tx_health.h"
#include <cassert>
#include <cstdio>

// One heartbeat tick exactly as node_core.yaml / led_can_actuator.yaml run it: build the
// flags, "send", record the outcome. Returns the error byte that went on the wire (or
// would have, if accepted).
static uint8_t heartbeat(TxHealth &h, uint8_t sticky, bool accepted)
{
  const uint8_t flags = sticky | tx_health_flags(h);
  tx_health_heartbeat_sent(h, accepted);
  return flags;
}

int main()
{
  // --- clean node: no flag, successful sends change nothing ---
  TxHealth h{};
  assert(tx_health_flags(h) == ERR_NONE);
  assert(tx_health_track(h, true) && tx_health_flags(h) == ERR_NONE && h.failures == 0);
  assert(heartbeat(h, ERR_NONE, true) == ERR_NONE);

  // --- a refused send (button / sensor frame) sets the flag; track() passes the result through ---
  assert(!tx_health_track(h, false));
  assert(h.pending && h.failures == 1 && tx_health_flags(h) == ERR_CAN_TX_FAIL);

  // --- a later successful non-heartbeat send does NOT clear it (only a heartbeat proves delivery) ---
  tx_health_note(h, true);
  assert(h.pending);

  // --- next heartbeat carries the flag, and once accepted the latch clears ---
  assert(heartbeat(h, ERR_NONE, true) == ERR_CAN_TX_FAIL);
  assert(!h.pending && tx_health_flags(h) == ERR_NONE);
  // ...so the heartbeat after that is clean again (gateway sees 0x01 then 0x00: set + recovered edges)
  assert(heartbeat(h, ERR_NONE, true) == ERR_NONE);

  // --- a refused heartbeat keeps the flag pending until the bus works again, however long ---
  assert(!tx_health_track(h, false));
  for (int i = 0; i < 5; ++i)
    assert(heartbeat(h, ERR_NONE, false) == ERR_CAN_TX_FAIL && h.pending);
  assert(h.failures == 7);                       // 2 refused frames + 5 refused heartbeats
  assert(heartbeat(h, ERR_NONE, true) == ERR_CAN_TX_FAIL && !h.pending);

  // --- a refused heartbeat on a previously clean node starts the latch itself ---
  assert(heartbeat(h, ERR_NONE, false) == ERR_NONE);   // nothing was pending to report yet
  assert(h.pending);
  assert(heartbeat(h, ERR_NONE, true) == ERR_CAN_TX_FAIL && !h.pending);

  // --- composes with a sticky profile bit and never clears it ---
  TxHealth b{};
  const uint8_t sticky = ERR_BRIDGE_QUEUE_OVERFLOW;
  assert(heartbeat(b, sticky, true) == ERR_BRIDGE_QUEUE_OVERFLOW);
  tx_health_note(b, false);
  assert(heartbeat(b, sticky, true) == (ERR_BRIDGE_QUEUE_OVERFLOW | ERR_CAN_TX_FAIL));
  assert(heartbeat(b, sticky, true) == ERR_BRIDGE_QUEUE_OVERFLOW);

  // --- the flag is the wire bit the gateway decodes ---
  assert(payload_errors(heartbeat_payload(1, tx_health_flags(h) | ERR_CAN_TX_FAIL)) == ERR_CAN_TX_FAIL);

  // --- the static store exists and is a single shared record ---
  tx_health() = TxHealth{};
  tx_health_note(tx_health(), false);
  assert(tx_health().pending && tx_health_flags(tx_health()) == ERR_CAN_TX_FAIL);

  // ===========================================================================
  // TX watchdog (R-17)
  // ===========================================================================

  // --- thresholds: 10, 20, 40, 80, capped; a garbage persisted level cannot shift past the cap ---
  assert(tx_watchdog_threshold(0) == 10 && tx_watchdog_threshold(1) == 20);
  assert(tx_watchdog_threshold(2) == 40 && tx_watchdog_threshold(3) == 80);
  assert(tx_watchdog_threshold(4) == 80 && tx_watchdog_threshold(255) == 80);
  assert(tx_watchdog_level_after_reboot(0) == 1 && tx_watchdog_level_after_reboot(2) == 3);
  assert(tx_watchdog_level_after_reboot(3) == 3 && tx_watchdog_level_after_reboot(255) == 3);

  // --- run counters: only HEARTBEAT outcomes move them ---
  TxHealth w{};
  tx_health_note(w, false);                          // refused non-heartbeat frame (e.g. a button)
  assert(w.hb_refused_run == 0 && w.hb_accepted_run == 0);
  tx_health_heartbeat_sent(w, false);
  tx_health_heartbeat_sent(w, false);
  assert(w.hb_refused_run == 2 && w.hb_accepted_run == 0);
  tx_health_heartbeat_sent(w, true);                 // one accepted heartbeat ends the refused run
  assert(w.hb_refused_run == 0 && w.hb_accepted_run == 1);
  tx_health_heartbeat_sent(w, false);                // and a refusal ends the accepted run
  assert(w.hb_refused_run == 1 && w.hb_accepted_run == 0);

  // --- a transient never reaches the threshold: 9 refused then one accepted, repeatedly ---
  TxHealth t{};
  for (int round = 0; round < 5; ++round) {
    for (int i = 0; i < 9; ++i) {
      tx_health_heartbeat_sent(t, false);
      assert(!tx_watchdog_should_reboot(t, 0));
    }
    tx_health_heartbeat_sent(t, true);
  }

  // --- saturation: runs stop at 0xFFFF instead of wrapping to 0 ---
  TxHealth sat{};
  sat.hb_refused_run = 0xFFFF;
  tx_health_heartbeat_sent(sat, false);
  assert(sat.hb_refused_run == 0xFFFF && tx_watchdog_should_reboot(sat, 3));
  sat.hb_accepted_run = 0xFFFF;
  tx_health_heartbeat_sent(sat, true);
  assert(sat.hb_accepted_run == 0xFFFF);

  // --- dead bus on TWAI: the queue (5 + 1 slot) accepts 6 heartbeats, then refuses forever.
  // A reboot empties the queue and the run counters (RAM) but NOT the backoff level (flash).
  // Heartbeats from boot to the reboot decision, per level -> 16, 26, 46, 86, 86, ...
  {
    const int queue_slots = 6;
    uint8_t level = 0;                               // the persisted global
    const int expected[] = {16, 26, 46, 86, 86, 86};
    for (int reboot = 0; reboot < 6; ++reboot) {
      TxHealth h{};                                  // fresh RAM after boot
      int beats = 0;
      for (;;) {
        // watchdog tick follows each heartbeat (30 s cadence, same order as the package's interval)
        tx_health_heartbeat_sent(h, beats < queue_slots);   // dead bus: nothing ever leaves the queue
        ++beats;
        assert(!tx_watchdog_recovered(h, level));    // never "proven" on a dead bus: accepted run <= 6
        if (tx_watchdog_should_reboot(h, level))
          break;
        assert(beats < 200);
      }
      assert(beats == expected[reboot]);
      level = tx_watchdog_level_after_reboot(level);
    }
    assert(level == TX_WDG_LEVEL_MAX);
    // Worst-case reboot period for a genuinely dead bus: 86 heartbeats x 30 s = 43 min.
    static_assert(86 * 30 / 60 == 43, "documented worst-case period");
  }

  // --- bus-off, then the reboot fixes it: level is cleared only after 12 accepted in a row ---
  {
    uint8_t level = 1;                               // one earlier reboot that did not help
    TxHealth h{};
    for (int i = 0; i < 11; ++i) {
      tx_health_heartbeat_sent(h, true);
      assert(!tx_watchdog_recovered(h, level));
    }
    tx_health_heartbeat_sent(h, true);
    assert(tx_watchdog_recovered(h, level));
    assert(!tx_watchdog_recovered(h, 0));            // nothing to clear at level 0
    // a refusal in the middle restarts the proof
    tx_health_heartbeat_sent(h, false);
    assert(!tx_watchdog_recovered(h, level));
  }

  // --- the proof is deeper than the TWAI queue, so a dead bus can't fake it ---
  static_assert(TX_WDG_PROVEN_ACCEPTED >= 2 * (5 + 1), "must exceed the default TWAI TX depth");

  printf("test_tx_health: all assertions passed\n");
  return 0;
}
