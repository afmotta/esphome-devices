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
// (lighting/packages/relay_bank.yaml numbers its channels 0-based natively,
// per ADR-0013's progressive-id convention: relay id N <-> coil N). Keep in
// sync with that bank's channel list and canbus/tools/bindings.py's
// MAX_RELAY_ID — a second bank (ADR-0014 open item 2) bumps all three in one
// commit, not silently.
inline constexpr std::size_t MAX_RELAYS = 32;

// --- Remote HTTP fallback outputs (ADR-0019) --------------------------------
// ADR-0013 §1 fixed the binding's relay id as *transport-agnostic*: an opaque
// progressive output id the gateway resolves to a physical output, so a remote
// output needs no registry/schema change — only gateway-side realization. We
// reserve the id range ABOVE the local bank for outputs the gateway reaches
// over HTTP (an ESPHome device on the LAN, e.g. an-penta-1's LED strips). The
// id->{host, object_id} realization lives in relay/remote glue (remote_store.h)
// + the gateway config, NOT here and NOT in registry/bindings.yaml.
//
// Keep MAX_REMOTE_ACTUATORS in sync with remote_store.h's object-id table and
// canbus/tools/bindings.py's MAX_RELAY_ID (which must span 0..MAX_OUTPUT_ID-1 so
// a `relay: 32` authoring validates) — one commit, not silently.
inline constexpr std::size_t REMOTE_ID_BASE = MAX_RELAYS;         // first remote id (32)
inline constexpr std::size_t MAX_REMOTE_ACTUATORS = 2;           // an-penta-1's two strips
inline constexpr std::size_t MAX_OUTPUT_ID = REMOTE_ID_BASE + MAX_REMOTE_ACTUATORS; // exclusive upper bound

enum OutputKind : uint8_t { OUTPUT_LOCAL, OUTPUT_REMOTE, OUTPUT_OUT_OF_RANGE };

// Classify a binding output id into the transport that realizes it. LOCAL ids
// drive the on-board relay bank (relay_store.h); REMOTE ids are actuated over
// HTTP (remote_store.h + remote_actuators.yaml); anything else is drift.
inline OutputKind output_id_kind(uint8_t id)
{
  if (id < MAX_RELAYS)
    return OUTPUT_LOCAL;
  if (id < MAX_OUTPUT_ID)
    return OUTPUT_REMOTE;
  return OUTPUT_OUT_OF_RANGE;
}

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
// (Local-bank-only primitive, retained for the native test and any caller that
// wants to reject remote ids too; the production path uses the generalized
// binding_outputs_in_bounds below.)
inline bool binding_relays_in_bounds(const BindingEntry &entry, std::size_t max_relays)
{
  for (uint8_t i = 0; i < entry.relay_count; i++)
    if (entry.relays[i] >= max_relays)
      return false;
  return true;
}

// True if every output id the binding lists resolves to a known transport —
// either a local relay (0..MAX_RELAYS-1) or a reserved remote id
// (REMOTE_ID_BASE..MAX_OUTPUT_ID-1). An id outside both is drift (a
// stale/hand-edited bindings.h past the Python validator) — callers log loudly.
// This supersedes the local-only bounds check as the fallback gate now that a
// binding may target a remote HTTP output (ADR-0019).
inline bool binding_outputs_in_bounds(const BindingEntry &entry)
{
  for (uint8_t i = 0; i < entry.relay_count; i++)
    if (output_id_kind(entry.relays[i]) == OUTPUT_OUT_OF_RANGE)
      return false;
  return true;
}
