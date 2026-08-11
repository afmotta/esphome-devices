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

  // --- output_id_kind: local bank, remote range, and beyond (ADR-0019) ---
  assert(output_id_kind(0) == OUTPUT_LOCAL);
  assert(output_id_kind(MAX_RELAYS - 1) == OUTPUT_LOCAL);   // 31, last local
  assert(output_id_kind(REMOTE_ID_BASE) == OUTPUT_REMOTE);  // 32, first remote
  assert(output_id_kind(MAX_OUTPUT_ID - 1) == OUTPUT_REMOTE); // last remote
  assert(output_id_kind(MAX_OUTPUT_ID) == OUTPUT_OUT_OF_RANGE); // first past the end
  // REMOTE_ID_BASE is exactly the local-bank size — no gap, no overlap.
  assert(REMOTE_ID_BASE == MAX_RELAYS);

  // --- binding_outputs_in_bounds: accepts local, remote, and mixed fan-out ---
  {
    const uint8_t local_only[] = {0, 31};
    BindingEntry e{100, 0, 2, local_only, "toggle"};
    assert(binding_outputs_in_bounds(e));
  }
  {
    const uint8_t remote_only[] = {(uint8_t) REMOTE_ID_BASE, (uint8_t) (MAX_OUTPUT_ID - 1)};
    BindingEntry e{100, 1, 2, remote_only, "on"};
    assert(binding_outputs_in_bounds(e));
    // ...and the local-only primitive correctly rejects those same remote ids.
    assert(!binding_relays_in_bounds(e, MAX_RELAYS));
  }
  {
    const uint8_t mixed[] = {0, (uint8_t) REMOTE_ID_BASE};  // one local + one remote
    BindingEntry e{100, 2, 2, mixed, "toggle"};
    assert(binding_outputs_in_bounds(e));
  }
  {
    const uint8_t out_of_range[] = {0, (uint8_t) MAX_OUTPUT_ID};  // one past the remote range
    BindingEntry e{100, 3, 2, out_of_range, "toggle"};
    assert(!binding_outputs_in_bounds(e));
  }

  printf("test_binding_actuation: all assertions passed\n");
  return 0;
}
