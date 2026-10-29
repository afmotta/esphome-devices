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
  assert(tx_health_track(h, true) && tx_health_flags(h) == ERR_NONE);
  assert(heartbeat(h, ERR_NONE, true) == ERR_NONE);

  // --- a refused send (button / sensor frame) sets the flag; track() passes the result through ---
  assert(!tx_health_track(h, false));
  assert(h.pending && tx_health_flags(h) == ERR_CAN_TX_FAIL);

  // --- a later successful non-heartbeat send does NOT clear it (only an accepted heartbeat clears it) ---
  tx_health_track(h, true);
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
  assert(heartbeat(h, ERR_NONE, true) == ERR_CAN_TX_FAIL && !h.pending);

  // --- a refused heartbeat on a previously clean node starts the latch itself ---
  assert(heartbeat(h, ERR_NONE, false) == ERR_NONE);   // nothing was pending to report yet
  assert(h.pending);
  assert(heartbeat(h, ERR_NONE, true) == ERR_CAN_TX_FAIL && !h.pending);

  // --- composes with a sticky profile bit and never clears it ---
  TxHealth b{};
  const uint8_t sticky = ERR_BRIDGE_QUEUE_OVERFLOW;
  assert(heartbeat(b, sticky, true) == ERR_BRIDGE_QUEUE_OVERFLOW);
  tx_health_track(b, false);
  assert(heartbeat(b, sticky, true) == (ERR_BRIDGE_QUEUE_OVERFLOW | ERR_CAN_TX_FAIL));
  assert(heartbeat(b, sticky, true) == ERR_BRIDGE_QUEUE_OVERFLOW);

  // --- the flag is the wire bit the gateway decodes ---
  assert(payload_errors(heartbeat_payload(1, tx_health_flags(h) | ERR_CAN_TX_FAIL)) == ERR_CAN_TX_FAIL);

  // --- the static store exists and is a single shared record ---
  tx_health() = TxHealth{};
  tx_health_track(tx_health(), false);
  assert(tx_health().pending && tx_health_flags(tx_health()) == ERR_CAN_TX_FAIL);

  printf("test_tx_health: all assertions passed\n");
  return 0;
}
