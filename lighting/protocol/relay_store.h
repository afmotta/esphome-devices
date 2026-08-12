#pragma once
#include "binding_actuation.h"
#include "esphome/components/switch/switch.h"
#include "esphome/components/canbus/canbus.h"
#include "esphome/core/log.h"
#include <cstring>

// =============================================================================
// relay_store.h — lighting fallback actuation, ESPHome-dependent glue (ADR-0013, ADR-0020)
// =============================================================================
// Owns the relay-id -> Switch* lookup table, the gateway's CAN bus handle, the on/off/toggle
// dispatcher, and fire_binding_fallback() — the one actuation entry point both buttons.yaml
// fallback branches (ha-not-ready, ack-timeout sweep) call. It dispatches each single-click
// binding by target_kind: a "relay" target drives the local Waveshare bank's Switch* directly;
// an "output" target (ADR-0020) sends a CAT_OUTPUT command over CAN to a remote actuator node
// (an An-Penta LED strip). Not natively testable (needs real esphome objects); the pure
// classification/op-mapping it leans on lives in binding_actuation.h and IS tested.
// =============================================================================

// A fixed store of relay-id -> Switch* pointers, same header-accessor shape as
// pending_acks_store() in ha_arbitration.h — ESPHome globals can't hold an array of raw pointers.
// Out-of-range i returns a static dummy slot rather than indexing store[] out of bounds — defense
// in depth matching binding_relays_in_bounds()'s own stance.
inline esphome::switch_::Switch *&relay_store(uint8_t i)
{
  static esphome::switch_::Switch *store[MAX_RELAYS] = {};
  static esphome::switch_::Switch *dummy = nullptr;
  if (i >= MAX_RELAYS)
    return dummy;
  return store[i];
}

// The gateway's CAN bus, registered in on_boot (mirrors relay_store()'s switch registration), so
// fire_binding_fallback() can emit a CAT_OUTPUT command for an output-target binding (ADR-0020).
// nullptr until registered — a gateway with no CAN never sets it, and an output binding then
// no-ops loudly rather than dereferencing null.
inline esphome::canbus::Canbus *&can_output_sender()
{
  static esphome::canbus::Canbus *bus = nullptr;
  return bus;
}

// Applies op ("on"/"off"/"toggle") to sw. Null-guards both sw (a relay id that
// binding_relays_in_bounds() passed but was never registered in on_boot would otherwise
// dereference nullptr) and op (a stale/hand-edited bindings.h could carry a null op pointer). An
// unrecognized-but-non-null op logs loudly — can't happen against a validated manifest, but
// doesn't fail silently on one that somehow isn't.
inline void relay_apply_op(esphome::switch_::Switch *sw, const char *op)
{
  if (sw == nullptr || op == nullptr)
    return;
  if (strcmp(op, "on") == 0)
    sw->turn_on();
  else if (strcmp(op, "off") == 0)
    sw->turn_off();
  else if (strcmp(op, "toggle") == 0)
    sw->toggle();
  else
    ESP_LOGE("arb", "FALLBACK actuation: unrecognized op '%s' (manifest/firmware drift)", op);
}

// The one fallback-actuation entry point (ADR-0013 §1-2, ADR-0020). Callers gate this call on
// is_fallback_gesture(event_type) themselves, keeping the existing unconditional
// fallback_events++/ESP_LOGW visible at the call site (only the actuation is click-gated). Looks
// up the binding and dispatches by target_kind:
//   - "output" (ADR-0020): send a CAT_OUTPUT MSG_OUT_SET_CHANNEL command to target_node_id/channel
//     over CAN — the HA-down path for a remote actuator (e.g. an An-Penta strip). CAN TX is
//     non-blocking, so this fires inline (no queue).
//   - "relay" (default): drive each listed relay's Switch* directly.
// A nullptr binding (the common case while registry/bindings.yaml is empty), an unregistered CAN
// bus, an unrecognized op, or an out-of-bounds relay id are all handled without touching hardware
// for a bad match — the drift cases log loudly since they mean a stale/hand-edited bindings.h.
inline void fire_binding_fallback(uint16_t node_id, uint8_t button)
{
  const BindingEntry *b = binding_find(node_id, button);
  if (b == nullptr)
    return;

  if (binding_is_output(*b)) {
    const uint8_t out_op = out_op_from_str(b->op);
    esphome::canbus::Canbus *bus = can_output_sender();
    if (bus == nullptr || out_op == 0xFF) {
      ESP_LOGE("arb", "FALLBACK output: node=%u btn=%u -> target=%u ch=%u dropped (%s)",
               (unsigned) node_id, (unsigned) button, (unsigned) b->target_node_id,
               (unsigned) b->channel, bus == nullptr ? "no CAN bus registered" : "unrecognized op");
      return;
    }
    bus->send_data(can_id(CAT_OUTPUT, b->target_node_id), true,
                   output_payload(b->channel, out_op));
    return;
  }

  if (!binding_relays_in_bounds(*b, MAX_RELAYS)) {
    ESP_LOGE("arb", "FALLBACK actuation: binding for node=%u btn=%u has an "
                     "out-of-bounds relay id (manifest/firmware drift)",
             (unsigned) node_id, (unsigned) button);
    return;
  }
  for (uint8_t i = 0; i < b->relay_count; i++)
    relay_apply_op(relay_store(b->relays[i]), b->op);
}
