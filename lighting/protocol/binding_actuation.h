#pragma once
#include <cstddef>
#include <cstring>
// Flat includes, not relative paths: ESPHome flattens every esphome.includes:
// entry into one src/ directory regardless of its original repo location
// (confirmed against bridge_forwarding.h/node_health.h's established
// convention), so a "../../canbus/protocol/..." path does not resolve at
// compile time even though it does in the repo tree.
#include "bindings.h"
#include "canbus_protocol.h"

// =============================================================================
// binding_actuation.h — lighting fallback actuation, pure logic (ADR-0013 §1-2, ADR-0020)
// =============================================================================
// No ESPHome includes — natively testable exactly like ha_arbitration.h. Owns the small rules
// worth pulling out of the fallback branches: which gesture types the fallback acts on at all;
// whether a relay-target binding's ids are within the physical bank; whether a binding targets a
// CAN output vs a local relay (target_kind); and the op-string -> OUT_OP_* mapping for a CAN
// output command. The ESPHome-dependent dispatch (drive a Switch* / send a CAN frame) lives in
// relay_store.h.
// =============================================================================

// One Waveshare Modbus RTU Relay 32CH bank (ADR-0014) on the gateway, ids 0-31
// (lighting/packages/relay_bank.yaml numbers its channels 0-based natively,
// per ADR-0013's progressive-id convention: relay id N <-> coil N). Keep in
// sync with that bank's channel list and canbus/tools/bindings.py's
// MAX_RELAY_ID — a second bank (ADR-0014 open item 2) bumps both in one
// commit, not silently.
inline constexpr std::size_t MAX_RELAYS = 32;

// Fallback acts on the single click ONLY (ADR-0013 §2, explicit, not a
// suggestion): double/triple-click and hold do nothing when HA is unreachable
// — those gestures are HA-only, by design, not a gap to fill in later.
inline bool is_fallback_gesture(uint8_t event_type)
{
  return event_type == EVT_CLICK;
}

// True if the binding targets a CAN OUTPUT (a remote actuator node reached over the bus, ADR-0020)
// rather than a gateway-local relay. target_kind is "relay" or "output" (generator-emitted); a
// null (stale/hand-edited bindings.h) is treated as "relay", the always-present local transport.
inline bool binding_is_output(const BindingEntry &entry)
{
  return entry.target_kind != nullptr && std::strcmp(entry.target_kind, "output") == 0;
}

// Map a binding op string ("on"/"off"/"toggle") to the wire OUT_OP_* code (canbus_protocol.h) for
// a CAN OUTPUT command. Returns 0xFF for an unrecognized/null op (the class of defect a
// stale/hand-edited bindings.h can carry) — callers must not send on 0xFF.
inline uint8_t out_op_from_str(const char *op)
{
  if (op == nullptr)
    return 0xFF;
  if (std::strcmp(op, "on") == 0)
    return OUT_OP_ON;
  if (std::strcmp(op, "off") == 0)
    return OUT_OP_OFF;
  if (std::strcmp(op, "toggle") == 0)
    return OUT_OP_TOGGLE;
  return 0xFF;
}

// True if every relay id a RELAY-target binding lists is within the physical bank (0..max_relays).
// A stale/hand-edited bindings.h passing an out-of-range id is a real defect, not routine fallback
// noise — callers should log it loudly. (Only meaningful for relay targets; an output target
// carries no relay list — relay_count 0, relays nullptr — so this passes it vacuously.)
inline bool binding_relays_in_bounds(const BindingEntry &entry, std::size_t max_relays)
{
  for (uint8_t i = 0; i < entry.relay_count; i++)
    if (entry.relays[i] >= max_relays)
      return false;
  return true;
}
