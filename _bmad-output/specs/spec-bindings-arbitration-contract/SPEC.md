---
id: SPEC-bindings-arbitration-contract
companions:
  - ../../planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md
  - ../../../canbus/_bmad-output/planning-artifacts/adrs/0013-gateway-local-relays-single-click-fallback.md
  - ../../../canbus/_bmad-output/planning-artifacts/adrs/0009-central-map-binding-manifest-system-of-record.md
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete contract for the compiled binding surface. Consult sources only for narrative rationale this contract intentionally omits.

# Freeze the Bindings→Arbitration Compiled Contract

## Why

AD-6 (architecture spine) rules that a cross-system boundary is not a contract until it has a frozen spec and a test that fails when either side drifts. The compiled `bindings.h` surface is exactly such a boundary: the canbus generator (`tools/generate_nodes.py`, `render_bindings_header()`) emits it from lighting-owned `registry/bindings.yaml`, and lighting's gate instance consumes it — today for the manifest-hash agreement with Home Assistant, and per ADR-0013 open item 2 eventually as the fallback action table driving real relays. AD-7 (as amended 2026-07-06) names this shape as the contract surface between the two systems. Freezing it now, before the Phase 5b-2 package extraction and before ADR-0013's actuation slice, means both of those land against a pinned surface instead of a moving one.

## Ownership

Mirrors `spec-map-json-contract` symmetrically: **canbus owns the emission mechanism** (the generator, canonicalization, the hash algorithm); **lighting owns this consumer contract** (what the compiled surface means and when it may change). A change to the frozen surface below is led by lighting, updating this spec + the drift test + the generator in one commit (AD-9), acked under the **LIGHT-** epic prefix.

## The frozen surface

All items frozen-additive: new fields, new ops, and new symbols may be *added*; nothing listed here may be renamed, retyped, removed, or reinterpreted without a new spec revision.

- **`BINDINGS_MANIFEST_HASH`** — `inline constexpr char[]`, the 16-hex canonical hash of `registry/bindings.yaml` (ADR-0009 §3, `bindings.py` `canonical_hash`). Home Assistant echoes it in the readiness heartbeat; the gate instance compares. An empty manifest still has a stable, real hash.
- **`struct BindingEntry`** — exactly these five fields with these types (order not frozen; additions allowed):
  | Field | Type | Meaning |
  | --- | --- | --- |
  | `node_id` | `uint16_t` | source node (flat id, ADR-0007) |
  | `button` | `uint8_t` | button index 0–7 |
  | `relay_count` | `uint8_t` | number of entries in `relays` |
  | `relays` | `const uint8_t *` | gateway relay ids, fan-out per ADR-0009 open item 1 |
  | `op` | `const char *` | one op applied to every listed relay |
- **`BINDINGS` / `BINDINGS_SIZE`** — the compiled table and its size. Empty manifest ⇒ `BINDINGS == nullptr` and `BINDINGS_SIZE == 0`; consumers must handle this without special-casing beyond the size check.
- **`binding_find(uint16_t node_id, uint8_t button)`** — keyed lookup on exactly `(node_id, button)`; returns a pointer into `BINDINGS` on match, `nullptr` on miss. First match wins (the generator emits sorted, duplicate-free rows — `bindings.py` validation rejects duplicate keys).
- **Op vocabulary** — `on` | `off` | `toggle` (validated by canbus's `bindings.py` reader; *meaning* is lighting's, AD-7). Frozen-additive: new ops may be added; existing ops keep their meaning.

## Deliberate absences (not omissions)

- **No event field.** A binding is a single-click action by construction (ADR-0013 §single-click; ADR-0012 gesture doctrine): momentary buttons emit events, never state, and fallback acts on the single click only. Adding an event dimension to `BindingEntry` requires renegotiating this spec, not just the struct.
- **Table contents are data, not contract.** Which bindings exist is registry state (`bindings.yaml`), reviewed by git diff, outside this freeze.
- **Actuation semantics** (what executing `op` on relay N physically does) land with ADR-0013 open items 2–3 and will bind to this surface, not modify it.

## Drift test

`canbus/firmware/tests/test_bindings_contract.cpp` compiles the real generated `protocol/bindings.h` and pins this surface: `static_assert`/`std::is_same` on each field's `decltype` and on `BINDINGS`'s own pointer type (breaks on rename/retype/removal, tolerates additions — no `sizeof`/layout pinning), a constexpr-usability pin on the hash constant, a signature check on `binding_find`, and runtime asserts on the empty-manifest behavior and the 16-hex hash shape. The Python-side half of the net is `test_generate_exports.py`'s render assertions. Drift-catch ordering: the battery compiles tests against the *committed* header, then regenerates and checks idempotence — so a generator-side render drift is caught in the same battery run by the idempotence step (`git diff --exit-code`), and this test pins the recommitted header from then on. The op vocabulary is enforced at validation time by `bindings.py`'s `VALID_OPS` (rejection covered by `test_bindings.py`); an explicit frozen-tuple pin on `VALID_OPS` itself is queued in `deferred-work.md`.

## Success signal

Both Phase 5b-2 (package extraction) and ADR-0013's actuation slice can be written against this document alone, without reading `render_bindings_header()`'s source to learn the surface. Any generator change that would alter the compiled shape fails `test_bindings_contract.cpp` before it ships.
