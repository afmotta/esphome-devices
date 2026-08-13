#pragma once
#include <cstdint>
#include <cstddef>

// =============================================================================
// bindings.h — GENERATED from registry/bindings.yaml by tools/generate_nodes.py. DO NOT EDIT.
// Binding-manifest identity + compiled fallback table for the ha_ready arbitration
// (ADR-0009 §3/§4). BINDINGS_MANIFEST_HASH is the canonical hash of bindings.yaml,
// which the gateway compares against the hash Home Assistant echoes in its readiness
// heartbeat (ADR-0003); a mismatch keeps ha_ready off. BINDINGS[] is the controller's
// fallback action table — frozen-additive, currently log-only (ADR-0003 open item 7).
// Keyed by (node_id, button): fallback fires on the single click only. target_kind is
// "relay" (drive gateway relays[0..relay_count) — fan-out, ADR-0009 open item 1) or
// "output" (send a CAT_OUTPUT command to target_node_id/channel — a CAN actuator like an
// An-Penta LED strip, ADR-0020); the single `op` applies to the target.
// =============================================================================

inline constexpr char BINDINGS_MANIFEST_HASH[] = "d66767448ba37b2f";

struct BindingEntry { uint16_t node_id; uint8_t button; uint8_t relay_count; const uint8_t *relays; const char *op; const char *target_kind; uint16_t target_node_id; uint8_t channel; };

inline constexpr const BindingEntry *BINDINGS = nullptr;
inline constexpr std::size_t BINDINGS_SIZE = 0;

inline const BindingEntry *binding_find(uint16_t node_id, uint8_t button) {
  for (std::size_t i = 0; i < BINDINGS_SIZE; i++)
    if (BINDINGS[i].node_id == node_id && BINDINGS[i].button == button)
      return &BINDINGS[i];
  return nullptr;
}
