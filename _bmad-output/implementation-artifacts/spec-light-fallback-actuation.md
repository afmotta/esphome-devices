---
title: 'Lighting fallback actuation — binding_actuation.h + relay store, wires both fallback branches (ADR-0013 items 1-2)'
type: 'feature'
created: '2026-07-10'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'bb7f173f4bc9499ce3722d4f164e2013d5441003'
baseline_commit: 'e3a19c30105f295f45e6529a0061ffd080577652'
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
- [x] Read `canbus/protocol/bindings.h`, `canbus/protocol/canbus_protocol.h` (for
  `EVT_CLICK` and the other `EVT_*` constants), `canbus/protocol/ha_arbitration.h` (the
  accessor-pattern precedent), and `lighting/packages/buttons.yaml` fully before writing code
- [x] Confirm P4's `id_offset` finding (0-based vs 1-based relay ids) from its spec's Design
  Notes before writing the `on_boot` registration or picking `MAX_RELAY_ID`'s exact value
- [x] Create `lighting/protocol/binding_actuation.h` per the Code Map
- [x] Create `lighting/protocol/relay_store.h` per the Code Map
- [x] Create `lighting/tests/test_binding_actuation.cpp` covering: in-bounds single relay,
  in-bounds fan-out, out-of-bounds rejection (including the exact boundary — `MAX_RELAYS - 1`
  in bounds, `MAX_RELAYS` itself out), and `is_fallback_gesture` true for `EVT_CLICK` / false
  for `EVT_DOUBLE_CLICK`/`EVT_TRIPLE_CLICK`/`EVT_HOLD`/`EVT_HOLD_RELEASE`
- [x] Add the two new header paths to `devices/gateway.yaml`'s `esphome.includes:`
- [x] Wire `lighting/packages/buttons.yaml`'s `on_boot` registration (32 explicit lines) and
  both fallback branches per the Code Map
- [x] Add `MAX_RELAY_ID = 31` + the validator check to `canbus/tools/bindings.py`
- [x] Add `test_validation_relay_out_of_bounds()` to `canbus/tests/test_bindings.py`
- [x] Run the full verification battery (below)

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

**P4 landed 0-based ids (`id_offset: -1`) → `relay_0..relay_31`.** Confirmed from P4's spec
Design Notes. `MAX_RELAY_ID = 31` (inclusive top), `MAX_RELAYS = 32` (count) in the two
mirrored constants; the `on_boot` registration is `relay_store(0) = id(relay_0);` through
`relay_store(31) = id(relay_31);`, 32 explicit lines, matching those ids exactly.

**Spec Code Map bug found and fixed: cross-directory includes must be flat, not relative.**
The Code Map called for `binding_actuation.h` to `#include "../../canbus/protocol/bindings.h"`
and `"../../canbus/protocol/canbus_protocol.h"`. This doesn't compile under `esphome compile`:
ESPHome flattens every `esphome.includes:` entry into one `src/` directory regardless of its
original repo location (confirmed against the existing convention in
`canbus/protocol/bridge_forwarding.h`/`node_health.h`, which only ever include same-directory
siblings by flat filename — this spec is the first cross-directory case). Fixed by switching
`binding_actuation.h` to flat includes (`"bindings.h"`, `"canbus_protocol.h"`), which resolve
correctly once ESPHome flattens the tree. `relay_store.h`'s `#include "binding_actuation.h"`
was already flat (same-directory sibling) and needed no change.

**Consequence for native testing: the g++ command needs `-I` flags.** GCC's quote-include
lookup for a nested `#include "bindings.h"` starts at the directory of the file containing
that directive (`lighting/protocol/`, not the top-level test file's directory), so the flat
include that ESPHome needs does *not* resolve for a bare `g++ ... test_binding_actuation.cpp`
compile — a genuinely new problem, since no existing native test in this repo has a
cross-directory header dependency. Fixed by adding `-Icanbus/protocol -Ilighting/protocol` to
the compile command (see Verification, which now differs from this spec's original literal
command list). This is a deviation from the spec's literal Verification section, not from any
Boundary — no ESPHome dependency was introduced, only an include-path search directory.

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
- `g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Ilighting/protocol lighting/tests/test_binding_actuation.cpp -o /tmp/act && /tmp/act`
  (`-I` flags added post-hoc — see Design Notes: ESPHome's flattened-include build needs flat
  filenames, which a bare g++ compile of a nested file can't resolve without them)
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

### 2026-07-10 — Blind Hunter + Edge Case Hunter (parallel, review-loop 1)

No `intent_gap` or `bad_spec` findings — no loopback triggered. `esphome compile`/native/
Python tests re-verified passing after patches applied.

**Patched (6, applied directly to this diff):**
1. `lighting/tests/test_binding_actuation.cpp`'s own build/run comment omitted the `-I` flags
   this spec's Design Notes had already discovered were required — anyone following the
   file's own instructions hit `fatal error: 'bindings.h' file not found`. Corrected the
   comment to the working command.
2. Neither `canbus/CLAUDE.md` (which lists every other native test's exact `g++` invocation)
   nor `lighting/CLAUDE.md` (no "Test & verify" section at all) documented how to run the new
   test. Added the correct `-I`-flagged command to `canbus/CLAUDE.md`'s existing list and
   added a new "Test & verify" section to `lighting/CLAUDE.md`.
3. The ~13-line actuation sequence (gesture-gate → `binding_find` → bounds-check → relay loop
   / `ESP_LOGE`) was duplicated near-verbatim across both fallback branches in
   `buttons.yaml`. Extracted into one shared `fire_binding_fallback(node_id, button)` helper
   in `relay_store.h`; both branches now call it behind their own `is_fallback_gesture` gate,
   keeping the counter/log unconditional at each call site as before.
4. Asymmetric defensive posture: an out-of-bounds relay id logged loudly (`ESP_LOGE`), but an
   unrecognized `op` string was a silent no-op, and `relay_apply_op` didn't null-guard `op`
   at all (a stale/hand-edited `bindings.h` with a null `op` would crash `strcmp`). Both
   fixed together: `relay_apply_op` now null-guards `op` and logs `ESP_LOGE` on an
   unrecognized-but-non-null value, symmetric with the relay-bounds handling.
5. `binding_actuation.h` used `std::size_t` without directly including `<cstddef>` — compiled
   today only via transitive includes from `bindings.h`/`canbus_protocol.h`, both described
   elsewhere as generated/frozen (so churn dropping that transitive include is plausible).
   Added the direct include.
6. `relay_store(uint8_t i)` indexed its fixed 32-entry array with no internal bounds check —
   every call site in this diff happens to be pre-guarded, but the function itself provided
   none of the defense-in-depth `binding_relays_in_bounds()` already established as this
   spec's own philosophy. Added a bounds check returning a static dummy slot for
   out-of-range `i`, preserving the `Switch *&` return signature.

**Deferred (3, appended to `deferred-work.md`):**
- `toggle` op across the double-action window can silently revert a relay to its start state
  with no error — real, but fixing it needs an architectural idempotency/dedup decision, out
  of scope for "wire the fallback."
- `relay_apply_op`'s dispatch logic (including its new null-guard/logging paths) has no
  automated test coverage — could use a mock Switch, but that's a new testing pattern this
  spec didn't introduce, matching the existing pure/glue architectural split.
- `MAX_RELAY_ID` (Python) vs `MAX_RELAYS` (C++) sync has no automated cross-language contract
  check, only a "find-both-and-bump" comment — independently flagged by both reviewers.

**Rejected (4, no action — noise or already-accounted-for design choices):**
- 32 hand-written `relay_store(i) = id(relay_i);` lines as a drift risk — deliberately scoped
  this way per this spec's own explicit Boundaries (no macro/loop synthesis), already
  cross-referenced in comments across all three artifacts that must move together.
- Two test-fragility notes about `FORM_A.replace()` (no occurrence-count assertion, `any()`
  instead of exact-error-count checks) — both match the pre-existing convention used by every
  other test in `canbus/tests/test_bindings.py`, not introduced by this diff.
- No lint/validation warning when a fan-out binding uses `op: toggle` across multiple relays —
  ADR-0013 §3 already documents this as prose guidance, not enforcement; adding validation
  for it is scope creep this spec's Boundaries explicitly warn against ("do not invent...
  speculatively").

## Auto Run Result

Status: in-review — implementation complete, review-loop 1 complete (parallel Blind Hunter +
Edge Case Hunter, zero bad_spec/intent_gap findings), 6 patches applied directly and
re-verified, 3 items deferred to `deferred-work.md`, 4 rejected as noise or already
out-of-scope. `esphome compile devices/gateway.yaml` exits 0 (esp-idf, ~68-75s build);
`lighting/tests/test_binding_actuation.cpp` and all 5 canbus native tests pass; all 3 canbus
Python test suites pass (15/15 binding-manifest tests including the new
`test_validation_relay_out_of_bounds`); generator idempotence holds (`generate_nodes.py`
touched no tracked file under `canbus/`/`registry/` beyond this spec's own source edits).
`git diff --stat` matches the expected file set exactly. One spec Code Map bug found and
fixed during implementation (documented in Design Notes): cross-directory includes must be
flat, not relative, because ESPHome flattens `esphome.includes:` into one `src/` directory —
this also meant the native test's g++ invocation needed `-I` flags, propagated into this
spec's Verification section and both CLAUDE.md files during review. Ready to present.

## Suggested Review Order

**Pure logic (the natively-tested core)**

- Start here: which gesture types the fallback acts on, and the relay-bounds defense-in-depth check.
  [`binding_actuation.h:31`](../../lighting/protocol/binding_actuation.h#L31)

- The mirrored Python-side bound this pure logic must stay in sync with.
  [`bindings.py:50`](../../canbus/tools/bindings.py#L50)

**ESPHome glue (the review-driven refactor)**

- `fire_binding_fallback()` — the one actuation entry point, extracted during review to remove duplication between both fallback branches.
  [`relay_store.h:68`](../../lighting/protocol/relay_store.h#L68)

- `relay_apply_op()` — null-guards both `sw` and `op`, logs loudly on an unrecognized op (review-driven symmetry fix).
  [`relay_store.h:45`](../../lighting/protocol/relay_store.h#L45)

- `relay_store()` — added its own bounds check as defense-in-depth (review-driven).
  [`relay_store.h:28`](../../lighting/protocol/relay_store.h#L28)

**Call sites (`lighting/packages/buttons.yaml`)**

- The 32-line `on_boot` registration — explicit lines, not a loop, because ESPHome lambdas can't synthesize `id(relay_N)` for a compile-time-variable N.
  [`buttons.yaml:44`](../../lighting/packages/buttons.yaml#L44)

- `ha not ready` branch: click-gated call to the shared helper (was ~13 duplicated lines before review).
  [`buttons.yaml:282`](../../lighting/packages/buttons.yaml#L282)

- ACK-timeout sweep branch: the same pattern, the ADR-0003 double-action window case.
  [`buttons.yaml:209`](../../lighting/packages/buttons.yaml#L209)

**Validation bound (closes ADR-0013 open item 1)**

- `MAX_RELAY_ID` validator check — the Python half of the two-language constant this spec introduces.
  [`bindings.py:195`](../../canbus/tools/bindings.py#L195)

**Peripherals**

- New native test for the pure logic, including the exact `MAX_RELAYS` boundary.
  [`test_binding_actuation.cpp`](../../lighting/tests/test_binding_actuation.cpp)

- New Python test for the validator bound.
  [`test_bindings.py:169`](../../canbus/tests/test_bindings.py#L169)

- Two new `esphome.includes:` entries wiring the new headers into the gateway.
  [`gateway.yaml:75`](../../devices/gateway.yaml#L75)
