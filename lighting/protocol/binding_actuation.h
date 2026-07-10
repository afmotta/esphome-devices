#pragma once
#include <cstddef>
// Flat includes, not relative paths: ESPHome flattens every esphome.includes:
// entry into one src/ directory regardless of its original repo location
// (confirmed against bridge_forwarding.h/node_health.h's established
// convention), so a "../../canbus/protocol/..." path does not resolve at
// compile time even though it does in the repo tree.
#include "bindings.h"
#include "canbus_protocol.h"

// =============================================================================
// binding_actuation.h — lighting fallback actuation, pure logic (ADR-0013 §1-2)
// =============================================================================
// No ESPHome includes — natively testable exactly like ha_arbitration.h. Owns
// the two small rules worth pulling out of the fallback branches: which gesture
// types the fallback acts on at all, and whether a binding's relay ids are
// within the physical bank (defense in depth against a stale/hand-edited
// bindings.h — the Python validator in canbus/tools/bindings.py should make an
// out-of-range id un-committable, but firmware doesn't get to assume that held).
// =============================================================================

// One Waveshare Modbus RTU Relay 32CH bank (ADR-0014) on the gateway, ids 0-31
// (devices/gateway.yaml's `id_offset: -1` -> relay_0..relay_31, per P4's Design
// Notes). Keep in sync with canbus/tools/bindings.py's MAX_RELAY_ID — a second
// bank (ADR-0014 open item 2) is a find-both-and-bump change, not silent drift.
inline constexpr std::size_t MAX_RELAYS = 32;

// Fallback acts on the single click ONLY (ADR-0013 §2, explicit, not a
// suggestion): double/triple-click and hold do nothing when HA is unreachable
// — those gestures are HA-only, by design, not a gap to fill in later.
inline bool is_fallback_gesture(uint8_t event_type)
{
  return event_type == EVT_CLICK;
}

// True if every relay id the binding lists is within the physical bank
// (0..max_relays). A stale/hand-edited bindings.h passing an out-of-range id
// is a real defect, not routine fallback noise — callers should log it loudly.
inline bool binding_relays_in_bounds(const BindingEntry &entry, std::size_t max_relays)
{
  for (uint8_t i = 0; i < entry.relay_count; i++)
    if (entry.relays[i] >= max_relays)
      return false;
  return true;
}
