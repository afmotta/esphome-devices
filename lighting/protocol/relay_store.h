#pragma once
#include "binding_actuation.h"
#include "esphome/components/switch/switch.h"
#include "esphome/core/log.h"
#include <cstring>

// =============================================================================
// relay_store.h — lighting fallback actuation, ESPHome-dependent glue (ADR-0013)
// =============================================================================
// Owns the fixed-size relay-id -> Switch* lookup table, the tiny on/off/toggle
// dispatcher, and fire_binding_fallback() — the one actuation entry point both
// buttons.yaml fallback branches (ha-not-ready, ack-timeout sweep) call, so the
// gesture-gate -> binding_find -> bounds-check -> relay-loop sequence lives in
// exactly one place instead of being duplicated per branch. Not natively
// testable (needs real esphome::switch_::Switch objects that only exist inside
// a compiled ESPHome binary) — same reason pending_acks_store() lives in
// ha_arbitration.h as ESPHome-adjacent glue, not in a pure-tested file.
// =============================================================================

// A fixed store of relay-id -> Switch* pointers, same header-accessor shape as
// pending_acks_store() in ha_arbitration.h — ESPHome globals can't hold this
// either (an array of raw pointers isn't a primitive `globals:` type).
// Out-of-range i returns a static dummy slot rather than indexing store[] out
// of bounds — defense in depth matching binding_relays_in_bounds()'s own
// stance, in case a future caller reaches this without checking bounds first
// (every call site in this file already does, via binding_relays_in_bounds()
// or a hardcoded 0-31 literal in on_boot).
inline esphome::switch_::Switch *&relay_store(uint8_t i)
{
  static esphome::switch_::Switch *store[MAX_RELAYS] = {};
  static esphome::switch_::Switch *dummy = nullptr;
  if (i >= MAX_RELAYS)
    return dummy;
  return store[i];
}

// Applies op ("on"/"off"/"toggle") to sw. Null-guards both sw (a relay id that
// binding_relays_in_bounds() passed but was never registered in on_boot would
// otherwise dereference nullptr) and op (a stale/hand-edited bindings.h could
// carry a null op pointer — the same class of defect binding_relays_in_bounds()
// defends against for relay ids). An unrecognized-but-non-null op logs loudly,
// symmetric with binding_relays_in_bounds()'s out-of-bounds handling — can't
// happen against a validated manifest, but doesn't fail silently on one that
// somehow isn't.
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

// The one fallback-actuation entry point (ADR-0013 §1-2). Callers gate this
// call on is_fallback_gesture(event_type) themselves, keeping the existing
// unconditional fallback_events++/ESP_LOGW visible at the call site (only the
// actuation is click-gated, not the counter/log). Looks up the binding, checks
// bounds, and applies op to every listed relay; a nullptr binding (the common
// case while registry/bindings.yaml is empty) or an out-of-bounds relay id are
// both handled without ever touching hardware for a bad match — the latter
// logs loudly since it means a stale/hand-edited bindings.h slipped past the
// Python validator.
inline void fire_binding_fallback(uint16_t node_id, uint8_t button)
{
  const BindingEntry *b = binding_find(node_id, button);
  if (b == nullptr)
    return;
  if (!binding_relays_in_bounds(*b, MAX_RELAYS)) {
    ESP_LOGE("arb", "FALLBACK actuation: binding for node=%u btn=%u has an "
                     "out-of-bounds relay id (manifest/firmware drift)",
             (unsigned) node_id, (unsigned) button);
    return;
  }
  for (uint8_t i = 0; i < b->relay_count; i++)
    relay_apply_op(relay_store(b->relays[i]), b->op);
}
