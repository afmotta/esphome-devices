---
title: 'Lighting fallback actuation — binding_actuation.h + relay store, wires both fallback branches (ADR-0013 items 1-2)'
type: 'feature'
created: '2026-07-10'
status: 'ready-for-dev'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'bb7f173f4bc9499ce3722d4f164e2013d5441003'
final_revision: ''
context: ['{project-root}/_bmad-output/planning-artifacts/adrs/0014-standardized-controller-modbus-io-hardware.md', '{project-root}/_bmad-output/implementation-artifacts/spec-light-gateway-swap-t-connect-pro.md', '{project-root}/canbus/_bmad-output/planning-artifacts/adrs/0013-gateway-local-relays-single-click-fallback.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** After P4, the gateway has 32 real relay switches on HA's live path, but
`lighting/packages/buttons.yaml`'s fallback — what happens when HA is down — is still
**log-only** in both places it fires: the `ha not ready` branch inside the CAT_INPUT
`on_frame` handler, and the 250ms pending-ACK expiry sweep. This is ADR-0013 open items 1
("max-relay-id validation bound") and 2 ("wire the gateway fallback to drive outputs").

**Approach:** Two pieces of new C++, one new Python-side validation bound, and edits to
exactly two existing lambda blocks:

1. **`lighting/protocol/binding_actuation.h`** — pure logic, no ESPHome includes, natively
   testable (mirrors `canbus/protocol/ha_arbitration.h`'s pure/tested style). Owns the two
   small, genuinely-worth-pulling-out rules: is this event type eligible for fallback at all
   (ADR-0013 §2: **click only** — double/triple/hold do nothing offline, by design), and are
   every relay id a binding lists actually within the physical bank (defense in depth: the
   Python validator added in this same spec should make an out-of-range id un-committable,
   but a stale/hand-edited manifest is still worth guarding against in firmware).
2. **`lighting/protocol/relay_store.h`** — ESPHome-dependent glue (real `Switch*` pointers,
   so it can't be pure/natively tested — same reason `pending_acks_store()` lives in
   `ha_arbitration.h` as an ESPHome-adjacent accessor, not in a natively-tested file). Owns
   the fixed-size relay-id → `Switch*` lookup table and the tiny on/off/toggle dispatcher.
3. **Two edits to `lighting/packages/buttons.yaml`**: an `on_boot` block registering all 32
   relay switches into the store (ESPHome packages have no loops — this is 32 explicit
   lines, not a loop), and the actual actuation call inserted into the two existing fallback
   branches, gated on the click-only filter.
4. **`canbus/tools/bindings.py`**: add `MAX_RELAY_ID = 31` and a validator check — resolves
   ADR-0013 open item 1. This is a canbus-owned file (the validator/generator mechanism), but
   the *value* comes from lighting's hardware decision (ADR-0014, one 32-channel bank); note
   that ownership split in the commit, matching how `BUTTON_MAX` already documents its
   source (`packages/base_node.yaml`'s 8-button set) in a comment right next to the constant.

**Frozen surface this binds to, never modifies** (verify by reading
`canbus/protocol/bindings.h` and `canbus/tests/test_bindings_contract.cpp` first):
`struct BindingEntry { uint16_t node_id; uint8_t button; uint8_t relay_count; const uint8_t
*relays; const char *op; }` and `const BindingEntry *binding_find(uint16_t node_id, uint8_t
button)`. `binding_find` returning `nullptr` means "no binding for this (node, button)" — the
overwhelmingly common case while `registry/bindings.yaml` stays empty (out of this epic's
scope, ADR-0013 open item 4) — and every touch point below must handle that cleanly, not as
an error.

## Boundaries & Constraints

**Always:**
- `binding_actuation.h` has **zero ESPHome includes** — only `#include
  "../../canbus/protocol/bindings.h"` (for `BindingEntry`) and `#include
  "../../canbus/protocol/canbus_protocol.h"` (for `EVT_CLICK`), both canbus-owned/frozen
  headers it depends on but never modifies. This is what makes it g++-natively-testable
  exactly like `ha_arbitration.h`.
- The fallback acts **only on the single click** (ADR-0013 §2, explicit, not a suggestion):
  double-click/triple-click/hold do nothing when HA is down — check this in both fallback
  branches before calling `binding_find` at all.
- `MAX_RELAYS` in `binding_actuation.h` (C++) and `MAX_RELAY_ID` in `bindings.py` (Python)
  encode the same fact (one 32-channel Waveshare Relay 32CH bank, ids 0-31) from two
  languages with no shared build step to keep them in sync — comment **both** constants
  noting the other side by name, so a future second bank (ADR-0014 open item 2) is a
  find-both-and-bump change, not a silent drift.
- The relay-id numbering (0-based `relay_0..relay_31` vs 1-based `relay_1..relay_32`) must
  match whatever P4's spec actually landed with (check its Design Notes for the `id_offset`
  finding) — the `on_boot` registration in `relay_store.h`'s consumer and `MAX_RELAY_ID`'s
  exact value both follow from that, don't assume 0-based.
- The 32 `relay_store(i) = id(relay_N)` registration lines are written out explicitly, one
  per relay — ESPHome YAML/lambdas have no loop construct that can synthesize `id(relay_N)`
  for a compile-time-variable N; do not attempt a clever macro or code-gen shortcut here.
- Both fallback branches keep their existing `fallback_events++` increment and `ESP_LOGW`
  call **unconditionally** (for every fallback firing, regardless of gesture type) — this
  aggregate is degraded-mode visibility (ADR-0011 §3) over *all* fallback events, not just
  actuated ones; only the new actuation call itself is click-gated. Do not narrow the
  existing counter/log semantics while adding the new behavior.
- One commit (AD-9): both headers, the `buttons.yaml` wiring, the `bindings.py` bound, its
  test, and the new native test land together — this closes ADR-0013 items 1-2 completely,
  not partially.

**Block If:** none — every rule here is fixed by ADR-0013 §2-3 (already-accepted semantics)
and the frozen `BindingEntry` contract; nothing here is an open design question for Alberto.

**Never:**
- Do not modify `canbus/protocol/bindings.h`'s shape, `canbus/tools/generate_nodes.py`'s
  `render_bindings_header`, or anything that would change `BindingEntry`'s fields or
  `binding_find`'s signature — `test_bindings_contract.cpp` passing unmodified is exactly the
  proof this constraint held.
- Do not touch `registry/bindings.yaml` itself (still empty) or attempt to author real
  bindings — that is explicitly ADR-0013 open item 4, out of scope until the light-circuit
  inventory exists.
- Do not touch `canbus/packages/health.yaml`, `canbus/protocol/ha_arbitration.h`, or any
  other canbus-owned transport/arbitration file beyond the one `bindings.py` bound.
- Do not change `ha_ready`/ACK-timeout timing behavior, the manifest-hash agreement, or
  anything else in `buttons.yaml` outside the two named branches.
- Do not build a general-purpose "act on any gesture" fallback — ADR-0013 deliberately
  narrowed this to click-only; resist the urge to make it configurable "for later."
- Do not add a version bump or compatibility shim (pre-live, in-place edits only).

</intent-contract>

## Code Map

- `lighting/protocol/binding_actuation.h` — **new file**, new directory. Contents:
  - `#pragma once`, includes as above.
  - `inline constexpr std::size_t MAX_RELAYS = 32;` // one Waveshare Relay 32CH bank (ADR-0014); keep in sync with `bindings.py`'s `MAX_RELAY_ID`
  - `inline bool is_fallback_gesture(uint8_t event_type)` — `return event_type == EVT_CLICK;`
    with a comment citing ADR-0013 §2 (double/triple/hold are HA-only, fallback does nothing).
  - `inline bool binding_relays_in_bounds(const BindingEntry &entry, std::size_t max_relays)`
    — loops `entry.relays[0..relay_count)`, returns false if any `>= max_relays`.
- `lighting/protocol/relay_store.h` — **new file**. Contents:
  - `#pragma once`, `#include "esphome/components/switch/switch.h"` (confirmed path/class:
    `esphome::switch_::Switch` with public `turn_on()`/`turn_off()`/`toggle()` — verified
    against the installed ESPHome 2026.5.0 component source; don't re-derive, just use it).
  - `inline esphome::switch_::Switch *&relay_store(uint8_t i)` — a fixed
    `static esphome::switch_::Switch *store[MAX_RELAYS] = {};` array accessor, same
    header-accessor shape as `pending_acks_store()` in `ha_arbitration.h` (ESPHome globals
    can't hold this either — an array of raw pointers isn't a primitive `globals:` type this
    codebase's convention reaches for; the accessor pattern is the established alternative).
  - `inline void relay_apply_op(esphome::switch_::Switch *sw, const char *op)` — null-guards
    `sw`, then `strcmp`s `op` against `"on"`/`"off"`/`"toggle"` and calls the matching
    method; unrecognized `op` is a no-op (can't happen against a validated manifest, but
    don't crash on one that somehow isn't).
- `lighting/packages/buttons.yaml`:
  - `esphome.on_boot` (~line 29-33 today, one entry already publishing
    `binding_manifest_hash`): add a second `then:` entry — 32 explicit lines,
    `relay_store(0) = id(relay_0);` through `relay_store(31) = id(relay_31);` (or
    `relay_store(0) = id(relay_1);` etc. if P4 landed 1-based ids — match whichever P4 used).
  - The `esphome.includes:` list this file depends on (set by the composing entry point,
    `devices/gateway.yaml`) gains two new header paths: `../lighting/protocol/
    binding_actuation.h`, `../lighting/protocol/relay_store.h` — add them to
    `devices/gateway.yaml`'s `esphome.includes:` list (this is the one line this spec touches
    outside `lighting/`, since that's where the include list lives per the existing
    convention for `canbus_protocol.h`/`node_map.h`/etc).
  - **`on_frame` handler, the `ha not ready` else-branch** (today ~lines 225-230): keep the
    existing `fallback_events++` and `ESP_LOGW` lines unconditionally; add, gated on
    `is_fallback_gesture(payload_event_type(x))`: look up `binding_find(can_id_node(can_id),
    payload_button_index(x))`, and if non-null and `binding_relays_in_bounds(*b, MAX_RELAYS)`,
    loop `b->relay_count` calling `relay_apply_op(relay_store(b->relays[i]), b->op)`; if
    non-null but NOT in bounds, log a distinct `ESP_LOGE` (a corrupt/stale manifest is a real
    defect, not routine fallback noise).
  - **The 250ms pending-ACK sweep `interval:`** (today ~lines 148-164): same actuation logic,
    keyed on the expired `PendingAck` entry's `e.node_id`/`e.button`, gated on
    `is_fallback_gesture(e.event_type)` (the stored event type from when the event was
    originally forwarded) — this is the ADR-0003 "double-action window" case: HA had the
    event but didn't ACK in time, so the fallback now does what HA might also still do.
- `canbus/tools/bindings.py`:
  - Add `MAX_RELAY_ID = 31` near the existing `BUTTON_MAX = 7` (~line 44), with a comment
    mirroring `BUTTON_MAX`'s style, citing the source: one Waveshare Relay 32CH bank
    (ADR-0014), and noting `lighting/protocol/binding_actuation.h`'s `MAX_RELAYS` must move
    with it.
  - In `validate()` (~lines 186-189), extend the existing `relay >= 0` check to also reject
    `relay > MAX_RELAY_ID`, same error-list style as the existing message.
- `canbus/tests/test_bindings.py`: add `test_validation_relay_out_of_bounds()` mirroring
  `test_validation_button_out_of_range()`'s shape — `relay: 32` rejected, `relay: 31`
  accepted, a fan-out `relay: "0,32"` rejected for the one bad channel.
- `lighting/tests/test_binding_actuation.cpp` — **new file**, new directory, g++-native
  style matching `canbus/tests/test_*.cpp` (`#include "../protocol/binding_actuation.h"`,
  plain `assert`s, a `main()` that runs each check and prints, no ESPHome deps).

## Tasks & Acceptance

**Execution:**
- [ ] Read `canbus/protocol/bindings.h`, `canbus/protocol/canbus_protocol.h` (for
  `EVT_CLICK` and the other `EVT_*` constants), `canbus/protocol/ha_arbitration.h` (the
  accessor-pattern precedent), and `lighting/packages/buttons.yaml` fully before writing code
- [ ] Confirm P4's `id_offset` finding (0-based vs 1-based relay ids) from its spec's Design
  Notes before writing the `on_boot` registration or picking `MAX_RELAY_ID`'s exact value
- [ ] Create `lighting/protocol/binding_actuation.h` per the Code Map
- [ ] Create `lighting/protocol/relay_store.h` per the Code Map
- [ ] Create `lighting/tests/test_binding_actuation.cpp` covering: in-bounds single relay,
  in-bounds fan-out, out-of-bounds rejection (including the exact boundary — `MAX_RELAYS - 1`
  in bounds, `MAX_RELAYS` itself out), and `is_fallback_gesture` true for `EVT_CLICK` / false
  for `EVT_DOUBLE_CLICK`/`EVT_TRIPLE_CLICK`/`EVT_HOLD`/`EVT_HOLD_RELEASE`
- [ ] Add the two new header paths to `devices/gateway.yaml`'s `esphome.includes:`
- [ ] Wire `lighting/packages/buttons.yaml`'s `on_boot` registration (32 explicit lines) and
  both fallback branches per the Code Map
- [ ] Add `MAX_RELAY_ID = 31` + the validator check to `canbus/tools/bindings.py`
- [ ] Add `test_validation_relay_out_of_bounds()` to `canbus/tests/test_bindings.py`
- [ ] Run the full verification battery (below)

**Acceptance Criteria:**
- Given `lighting/tests/test_binding_actuation.cpp`, when compiled and run with
  `g++ -std=c++17 -Wall -Wextra`, then all assertions pass with no ESPHome dependency in the
  build command.
- Given `canbus/tests/test_bindings_contract.cpp`, when run after this spec, then it still
  passes unmodified — proof `BindingEntry`/`binding_find` were only consumed, never changed.
- Given `python3 canbus/tests/test_bindings.py`, when run after this spec, then all tests
  pass including the new `test_validation_relay_out_of_bounds` — `relay: 32` is rejected,
  `relay: 31` is accepted.
- Given `esphome compile devices/gateway.yaml`, when run after this spec, then it exits 0.
- Given a hand-constructed test scenario (single click on a bound node/button while HA is
  unreachable — exercised via the compiled config's logic, or reasoned through by inspection
  if hardware isn't available yet), when the fallback fires, then exactly the relays listed
  in the matching binding change state according to `op`, and a double-click/hold on the same
  node/button does nothing.
- Given `git diff --stat` after this spec, when compared against the file list above, then no
  file outside that list changed — in particular, `canbus/protocol/bindings.h` and
  `canbus/tools/generate_nodes.py` are untouched.

## Design Notes

_Fill in during execution: confirm which `id_offset`/relay-id numbering P4 actually used,
and the exact 32-line `on_boot` registration block that resulted._

`relay_store.h` is deliberately **not** natively tested — it requires real
`esphome::switch_::Switch` objects that only exist inside a compiled ESPHome binary. This
mirrors the existing split in this codebase: `ha_arbitration.h`'s pure timing/pending-ack
logic is g++-tested, while the ESPHome-side lambda code that calls
`homeassistant.event`/`pending_add` in `buttons.yaml` is only exercised by `esphome compile`.
The same split applies here: `binding_actuation.h` (pure) is tested; `relay_store.h` (glue)
is proven by the gateway compiling and, eventually, by hardware bring-up.

The out-of-bounds branch logs `ESP_LOGE` rather than the routine `ESP_LOGW` the rest of the
fallback path uses — a relay id past the physical bank can only mean a stale/hand-edited
`bindings.h` slipped past the Python validator (which this same spec makes reject it), so it
deserves a distinct, louder signal, not to be lost among ordinary fallback-firing noise.

## Verification

**Commands:**
- `g++ -std=c++17 -Wall -Wextra lighting/tests/test_binding_actuation.cpp -o /tmp/act && /tmp/act`
- `g++ -std=c++17 -Wall -Wextra canbus/tests/test_bindings_contract.cpp -o /tmp/bcontract && /tmp/bcontract`
- `python3 canbus/tests/test_bindings.py`
- `python3 canbus/tests/test_generate_exports.py`
- `python3 canbus/tests/test_push_gate.py`
- `esphome compile devices/gateway.yaml`
- `python3 canbus/tools/generate_nodes.py && git diff --exit-code canbus registry` -- generator idempotence, proves this spec didn't accidentally regenerate anything
- `git diff --stat` -- expected file set: `lighting/protocol/binding_actuation.h` (new),
  `lighting/protocol/relay_store.h` (new), `lighting/tests/test_binding_actuation.cpp` (new),
  `lighting/packages/buttons.yaml` (modified), `devices/gateway.yaml` (modified, includes
  list only), `canbus/tools/bindings.py` (modified), `canbus/tests/test_bindings.py`
  (modified)

**Manual checks (if no CLI):**
- Read both new fallback-branch edits side by side: confirm the click-only gate, the
  bounds-check, and the unconditional counter/log are all present in both, symmetrically.

## Spec Change Log

## Review Triage Log

## Auto Run Result

Status: ready-for-dev — not yet executed.
