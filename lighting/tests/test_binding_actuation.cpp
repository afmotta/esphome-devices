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
    BindingEntry e{100, 0, 1, relays, "toggle"};
    assert(binding_relays_in_bounds(e, MAX_RELAYS));
  }

  // --- fan-out, all in bounds ---
  {
    const uint8_t relays[] = {0, 5, 31};
    BindingEntry e{100, 0, 3, relays, "on"};
    assert(binding_relays_in_bounds(e, MAX_RELAYS));
  }

  // --- exact boundary: MAX_RELAYS - 1 in bounds, MAX_RELAYS itself out ---
  {
    const uint8_t relays_ok[] = {(uint8_t) (MAX_RELAYS - 1)};
    BindingEntry ok{100, 0, 1, relays_ok, "on"};
    assert(binding_relays_in_bounds(ok, MAX_RELAYS));

    const uint8_t relays_bad[] = {(uint8_t) MAX_RELAYS};
    BindingEntry bad{100, 0, 1, relays_bad, "on"};
    assert(!binding_relays_in_bounds(bad, MAX_RELAYS));
  }

  // --- fan-out with one bad channel among otherwise-valid ones ---
  {
    const uint8_t relays[] = {0, 1, (uint8_t) MAX_RELAYS};
    BindingEntry e{100, 0, 3, relays, "off"};
    assert(!binding_relays_in_bounds(e, MAX_RELAYS));
  }

  printf("test_binding_actuation: all assertions passed\n");
  return 0;
}
