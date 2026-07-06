---
title: 'Migration Phase 5b-1 — Bindings→arbitration contract spec + drift test'
type: 'feature'
created: '2026-07-06'
status: 'done'
review_loop_iteration: 0
baseline_commit: '548dd5cc83aa14a98da758e42683bfcc29b26db2'
context: ['{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md', '{project-root}/_bmad-output/specs/spec-map-json-contract/SPEC.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** AD-6 says a cross-system boundary is not a contract until it has a frozen spec and a drift-breaking test. The compiled `BindingEntry`/`bindings.h` surface — the seam between the canbus generator that emits it and lighting's gate instance that will consume it (AD-7 as amended 2026-07-06) — has neither. Existing tests cover the generator's string output (Python) and the arbitration logic (C++), but nothing compiles the real generated header and pins the consumer-visible C++ surface; a silent field-type or signature change would pass every test today.

**Approach:** Write the frozen contract spec at `_bmad-output/specs/spec-bindings-arbitration-contract/SPEC.md`, following the `spec-map-json-contract` pattern: contract owned by lighting (the consumer), emission mechanism owned by canbus — mirroring map.json (canbus generates, hvac owns the contract). Add a native C++ drift test that includes the real `protocol/bindings.h` and pins the frozen surface with compile-time checks. Wire it into the standing battery. Low-risk, purely additive: no existing code changes.

## Boundaries & Constraints

**Always:**
- Frozen-additive semantics, same as map.json: the five `BindingEntry` fields (`node_id: uint16_t`, `button: uint8_t`, `relay_count: uint8_t`, `relays: const uint8_t*`, `op: const char*`), `BINDINGS`/`BINDINGS_SIZE`, `binding_find(node_id, button)` keyed lookup with nullptr-on-miss, `BINDINGS_MANIFEST_HASH` as a 16-hex `constexpr char[]`, and empty-manifest behavior (`BINDINGS == nullptr`, `BINDINGS_SIZE == 0`) are frozen; fields/ops may be *added*, never renamed, retyped, or removed without a new spec. The drift test must allow additions (no `sizeof` pinning) while breaking on rename/retype/removal.
- Single-click-only doctrine carries into the contract: `BindingEntry` has no event field by design (ADR-0013 §single-click; momentary buttons emit events, not state) — the spec must state this as intentional, not an omission.
- The op vocabulary (`on` | `off` | `toggle`) is frozen-additive too; its *meaning* is lighting's (AD-7), its validation lives in canbus's `bindings.py` reader.
- One commit; battery green including the new test.

**Ask First:**
- None identified — this slice is additive-only and the ownership call (lighting owns contract, canbus owns mechanism) follows directly from the AD-7 amendment approved this session.

**Never:**
- Do not touch `gateway.yaml`, `generate_nodes.py`'s render logic, `bindings.py`, or any existing test — if the drift test won't pass against today's real generated header as-is, that's a finding to surface, not code to "fix" in this slice.
- Do not start the package extraction (Phase 5b-2) or create `lighting/packages/`.

</frozen-after-approval>

## Code Map

- `_bmad-output/specs/spec-bindings-arbitration-contract/SPEC.md` -- new frozen contract doc, formatted after `_bmad-output/specs/spec-map-json-contract/SPEC.md` (id, companions frontmatter; Why / Capabilities / Constraints / Non-goals / Success signal)
- `canbus/firmware/tests/test_bindings_contract.cpp` -- new native drift test: `#include "../protocol/bindings.h"`; compile-time field-type pins via `decltype`/`std::is_same` static_asserts, `binding_find` signature check, runtime asserts for the empty-manifest case (nullptr table, size 0, miss returns nullptr) and 16-hex hash shape
- `canbus/firmware/protocol/bindings.h` -- read-only reference (the real generated artifact the test compiles against; regenerated fresh in the battery each slice, so generator drift surfaces as a compile failure here)
- `canbus/CLAUDE.md` -- add the new test to the "Test & verify" battery block
- `_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/MIGRATION-MAP.md` -- add the new test to the standing battery; AD-6 instance list in `ARCHITECTURE-SPINE.md` updates from "spec + test due when the lighting carve-out lands" to "spec + tests exist"
- `canbus/firmware/tests/test_generate_exports.py` -- reference only; its existing string-level render assertions stay as the Python-side half of the drift net (no changes expected)

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/specs/spec-bindings-arbitration-contract/SPEC.md` -- authored: surface inventory, ownership split (lighting owns contract / canbus owns mechanism, LIGHT- acks), deliberate-absences section (no event field by design; table contents are data; actuation is ADR-0013's slice)
- [x] `canbus/firmware/tests/test_bindings_contract.cpp` -- written; passes against today's committed header with zero changes to existing files
- [x] `canbus/CLAUDE.md` -- battery block updated
- [x] `MIGRATION-MAP.md` battery + `ARCHITECTURE-SPINE.md` AD-6 instance list -- contract recorded as existing (Phase 5b-1)
- [x] SPEC companions reference ADR-0013 and the spine carrying the AD-7 amendment

**Acceptance Criteria:**
- Given the committed, freshly-regenerated `protocol/bindings.h`, when `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_bindings_contract.cpp -o /tmp/bcontract && /tmp/bcontract` runs, then it compiles and passes with zero changes to any existing file. -- confirmed.
- Given a simulated drift (retyping `button` to `uint16_t` in a scratch copy of the header), when the test compiles against it, then compilation fails on a static_assert naming the drifted field. -- confirmed: `error: static assertion failed ... contract drift: BindingEntry::button must be uint8_t`. Scratch copy deleted, not committed.
- Given the standing battery including the new test, when run, then all commands exit 0 and regeneration stays byte-identical. -- confirmed (push gate reports only the expected not-yet-pushed local commit, same pre-push state as every phase).

## Design Notes

The drift net is two-sided by construction: `test_generate_exports.py` (Python) pins what the generator *renders*; the new C++ test pins what a consumer *compiles*. Ordering correction found during review: the battery compiles tests against the *committed* header and regenerates *afterward* — so generator-side drift is caught in the same run by the idempotence check (`git diff --exit-code`), and the contract test pins the recommitted header thereafter; the net still closes in one battery run, just via a different tripwire than first described. Compile-time `static_assert` + `std::is_same` on `decltype(BindingEntry::field)` breaks on rename/retype/removal but tolerates added fields — matching frozen-additive exactly. No `sizeof` or aggregate-layout pinning, which would false-alarm on legitimate additions.

## Verification

**Commands:**
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_bindings_contract.cpp -o /tmp/bcontract && /tmp/bcontract` -- expected: pass
- Full standing battery (python tests, all native C++ tests, sensor-node compile, regeneration idempotence, push gate) -- expected: green, unchanged

**Note (review):** both review subagents stalled twice on infrastructure errors, so the review ran inline against the same verification points their prompts specified — disclosed, not skipped. Verified sound: the 0xFFFF miss-probe (NODE_ID_MAX=8191 makes 65535 unbindable), the hash-shape asserts (sha256 hexdigest[:16] is always 16 lowercase hex), the decltype member pins (proven by drift simulation). Patched from findings: added the missing `BINDINGS` pointer-type pin and a constexpr-usability pin on the hash constant; corrected the battery-ordering claim in both the contract SPEC and this spec's Design Notes (generator drift is caught by the idempotence step, not by pre-test regeneration). Deferred: an explicit `VALID_OPS` frozen-tuple pin (barred by this slice's Never against touching existing tests). A second drift simulation (dropping `constexpr` from `BINDINGS`) compiled clean — correct, since the SPEC promises constexpr only for the hash constant; this confirmed the test tolerates non-contract changes without false-alarming.

## Suggested Review Order

**The contract**

- Entry point: the frozen surface, ownership split, and deliberate absences.
  [`SPEC.md`](../specs/spec-bindings-arbitration-contract/SPEC.md#L1)

**The drift test**

- Compile-time pins: five field types, table pointer type, binding_find signature, constexpr hash.
  [`test_bindings_contract.cpp:24`](../../canbus/firmware/tests/test_bindings_contract.cpp#L24)
- Runtime half: hash shape, empty-manifest semantics, the 0xFFFF miss-probe that stays valid if the manifest ever gains rows.
  [`test_bindings_contract.cpp:57`](../../canbus/firmware/tests/test_bindings_contract.cpp#L57)

**Battery wiring**

- [`canbus/CLAUDE.md:54`](../../canbus/CLAUDE.md#L54)
- [`MIGRATION-MAP.md:23`](../planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/MIGRATION-MAP.md#L23)
- AD-6 instance list now records this contract as existing.
  [`ARCHITECTURE-SPINE.md:77`](../planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md#L77)
