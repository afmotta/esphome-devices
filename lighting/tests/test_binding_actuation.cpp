// Standalone native test for binding_actuation.h (no ESPHome required).
// Build & run (from repo root; -I flags required because binding_actuation.h
// uses the flat includes ESPHome's flattened build needs — see its own header
// comment and this spec's Design Notes):
//   g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Ilighting/protocol \
//     lighting/tests/test_binding_actuation.cpp -o /tmp/act && /tmp/act

#include "../protocol/binding_actuation.h"
#include <cassert>
#include <cstdio>

int main()
{
  // --- is_fallback_gesture: click only, every other gesture is HA-only (ADR-0013 §2) ---
  assert(is_fallback_gesture(EVT_CLICK));
  assert(!is_fallback_gesture(EVT_DOUBLE_CLICK));
  assert(!is_fallback_gesture(EVT_TRIPLE_CLICK));
  assert(!is_fallback_gesture(EVT_HOLD));
  assert(!is_fallback_gesture(EVT_HOLD_RELEASE));

  // --- binding_relays_in_bounds: single relay, in bounds ---
  {
    const uint8_t relays[] = {0};
    BindingEntry e{100, 0, 1, relays, "toggle", "relay", 0, 0};
    assert(binding_relays_in_bounds(e, MAX_RELAYS));
  }

  // --- fan-out, all in bounds ---
  {
    const uint8_t relays[] = {0, 5, 31};
    BindingEntry e{100, 0, 3, relays, "on", "relay", 0, 0};
    assert(binding_relays_in_bounds(e, MAX_RELAYS));
  }

  // --- exact boundary: MAX_RELAYS - 1 in bounds, MAX_RELAYS itself out ---
  {
    const uint8_t relays_ok[] = {(uint8_t) (MAX_RELAYS - 1)};
    BindingEntry ok{100, 0, 1, relays_ok, "on", "relay", 0, 0};
    assert(binding_relays_in_bounds(ok, MAX_RELAYS));

    const uint8_t relays_bad[] = {(uint8_t) MAX_RELAYS};
    BindingEntry bad{100, 0, 1, relays_bad, "on", "relay", 0, 0};
    assert(!binding_relays_in_bounds(bad, MAX_RELAYS));
  }

  // --- fan-out with one bad channel among otherwise-valid ones ---
  {
    const uint8_t relays[] = {0, 1, (uint8_t) MAX_RELAYS};
    BindingEntry e{100, 0, 3, relays, "off", "relay", 0, 0};
    assert(!binding_relays_in_bounds(e, MAX_RELAYS));
  }

  // --- binding_is_output: target_kind discriminates relay vs CAN output (ADR-0020) ---
  {
    const uint8_t relays[] = {0};
    BindingEntry relay_default{100, 0, 1, relays, "toggle", nullptr, 0, 0};  // null target_kind
    assert(!binding_is_output(relay_default));
    BindingEntry relay_explicit{100, 0, 1, relays, "toggle", "relay", 0, 0};
    assert(!binding_is_output(relay_explicit));
    // An output target carries no relay list (relay_count 0, relays nullptr) + a target node/ch.
    BindingEntry out_target{101, 1, 0, nullptr, "toggle", "output", 102, 0};
    assert(binding_is_output(out_target));
    // binding_relays_in_bounds is vacuously true for an output target (no relays to check).
    assert(binding_relays_in_bounds(out_target, MAX_RELAYS));
  }

  // --- out_op_from_str: op string -> wire OUT_OP_* code; unknown/null -> 0xFF sentinel ---
  assert(out_op_from_str("on") == OUT_OP_ON);
  assert(out_op_from_str("off") == OUT_OP_OFF);
  assert(out_op_from_str("toggle") == OUT_OP_TOGGLE);
  assert(out_op_from_str("explode") == 0xFF);
  assert(out_op_from_str(nullptr) == 0xFF);

  printf("test_binding_actuation: all assertions passed\n");
  return 0;
}
