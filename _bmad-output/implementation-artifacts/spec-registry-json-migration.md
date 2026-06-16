---
title: 'Single JSON registry: merge nodes.csv + bindings.yaml + node_id_hwm into registry.json; drop map.json'
type: 'refactor'
created: '2026-06-16'
baseline_commit: '97617a0757873dd26b2a02c7abd0cb849e808db6'
status: 'ready'
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/planning-artifacts/adrs/0009-central-map-binding-manifest-system-of-record.md'
  - '{project-root}/_bmad-output/planning-artifacts/adrs/0007-flat-node-id-with-central-meaning-map.md'
  - '{project-root}/_bmad-output/planning-artifacts/adrs/0013-gateway-local-relays-single-click-fallback.md'
  - '{project-root}/_bmad-output/planning-artifacts/adrs/0011-health-monitoring-degraded-mode-visibility.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** the registry's system of record is split across three files in two formats — `registry/nodes.csv` (placement, written by the CLIs), `registry/bindings.yaml` (fallback behavior, hand-edited via a bespoke ~80-line scalars-only YAML reader), and `registry/node_id_hwm` (a 1-line allocation counter). A fourth file, the generated `registry/map.json`, is committed and guarded but has **no live consumer** (its only intended readers — ADR-0011 health monitoring and the external HVAC firmware — are Proposed/unconfirmed). Alberto wants **one source of truth to maintain**.

**Approach:** merge the three sources into a single node-centric **`registry/registry.json`** parsed with stdlib `json` (no PyYAML — JSON gives native nesting *and* deletes the hand-rolled reader), with each node's `bindings` nested under it. **Delete `map.json`** and its generator path. The `manifest_hash` keeps covering **behavior only** (hashed over the bindings subset, ignoring placement), so renaming a room never flips `ha_ready` — the exact property ADR-0009 §2 used to justify the original split is preserved differently. Ship a `registry/schema.json` (JSON Schema) so the field documentation JSON can't inline becomes enforced + editor-assisted. Record the decision in a new ADR-0014 that partially supersedes ADR-0009.

This subsumes the in-flight multi-relay work: `relay` becomes a native JSON array (`[3,4,5]`), retiring the `"3,4,5"` comma-string that only existed to dodge the no-nesting reader.

## Boundaries & Constraints

**Always:**
- One source file `registry/registry.json`; one stdlib loader `tools/registry.py`; one shared canonical **writer** (fixed key order, `indent=2`, `ensure_ascii=False`, trailing newline) used by every writer so diffs stay clean.
- Fold `node_id_hwm` in as a top-level integer field — `registry.json` is the *complete* source; delete the separate file.
- `manifest_hash` = SHA-256 over the **parsed bindings subset** in the **same canonical structure** ADR-0009 §3 froze (`{schema_version, bindings:[ sorted by (node_id,button), relay→sorted-unique int list ]}`), truncated to 16 hex — so the **empty-manifest hash stays `d66767448ba37b2f`** and placement edits never change it.
- `relay` accepts a single int or a native int array; normalized to a sorted, de-duplicated int list (`parse_relays`). `op ∈ {on,off,toggle}`. No `event` (ADR-0013 single-click). No Modbus addresses (progressive relay ids).
- Validate-before-persist: validate the whole registry, then write artifacts; an invalid `registry.json` leaves `nodes/`, `node_map.h`, `bindings.h` untouched.
- `registry.json` carries `"$schema": "schema.json"` and validates against `registry/schema.json`.
- Generated artifacts stay committed and byte-identical for the migrated data (proof of behavior preservation).

**Ask First:** (all three resolved 2026-06-16 — recorded here, do not re-litigate)
- File name → **`registry/registry.json`**.
- `node_id_hwm` → **folded into the JSON**.
- JSON Schema → **yes, `registry/schema.json`**.

**Never:**
- Do not add PyYAML or any third-party dependency; `json`/`csv`(migration only)/stdlib only.
- Do not let the manifest hash cover placement (floor/room/board/location/sensors) — behavior only.
- Do not change `canbus_protocol.h`, the wire protocol, CAN IDs, or the `NodeMapEntry`/`BindingEntry` struct shapes (frozen-additive).
- Do not hand-edit generated `nodes/`, `node_map.h`, `bindings.h`, `ha_manifest_package.yaml`.
- Do not keep `map.json` "just in case" — remove it from the generator, the push-gate, and docs; ADR-0011/HVAC read `registry.json` directly.
- Do not rewrite the historical `_bmad-output/implementation-artifacts/*.md` records; only live ADRs (0009/0011/0013/new 0014) and `firmware/README.md`.

## The source schema: `registry/registry.json`

```json
{
  "$schema": "schema.json",
  "schema_version": 1,
  "node_id_hwm": 101,
  "nodes": [
    {
      "node_id": 100,
      "floor": 0, "room": 7, "board": 0,
      "location": "Ground floor hallway",
      "sensors": 0,
      "bindings": []
    },
    {
      "node_id": 101,
      "floor": 0, "room": 8, "board": 0,
      "location": "Ground floor living room",
      "sensors": 0,
      "bindings": [
        { "button": 0, "relay": 0,         "op": "toggle" },
        { "button": 1, "relay": [3, 4, 5], "op": "toggle" }
      ]
    }
  ]
}
```

Validation rules (merged from `generate_nodes.py` row checks + `bindings.validate`):
- `schema_version == 1`; `node_id_hwm` int ≥ max(node_id).
- `node_id` unique, `0..8191`. `room`/`board` `0..255`; `(room,board)` unique among commissioned nodes (`(0,0)` placeholder exempt). `sensors ∈ {0,1}`.
- Per binding: `button 0..7`; `(node_id,button)` unique within a node; `relay` int(s) ≥ 0; `op ∈ {on,off,toggle}`.

## Code touch list

| File | Change |
|---|---|
| `registry/registry.json` | **New** single source (replaces nodes.csv + bindings.yaml + node_id_hwm). |
| `registry/schema.json` | **New** JSON Schema for `registry.json`. |
| `tools/registry.py` | **New**, replaces `bindings.py`. `load_registry()` (`json.load`), `validate()` (all node + binding rules), `manifest_hash()` (bindings-subset canonical hash, §3 logic reused), `parse_relays()` (int/array → sorted-unique), `iter_bindings()`, `write_registry()` (canonical formatter). |
| `tools/bindings.py` | **Deleted** — hand-rolled YAML subset reader gone (net code reduction). |
| `tools/allocate_node.py` | Read `registry.json`; `next_id = max(node_id_hwm, max(node_ids)) + 1`; append node (placeholder placement, `"bindings": []`); bump `node_id_hwm` field; `write_registry()`. Drop CSV + pre-ADR-0006 column migration. |
| `tools/commission.py` | `read/write/apply_assignment/cmd_list` against the JSON nodes list; UX unchanged; still calls `generate_nodes.main()`. |
| `tools/generate_nodes.py` | Read `registry.json`; iterate `nodes` for node configs + `node_map.h`; pull each node's `bindings` for `bindings.h`. **Remove** `build_map_export()` + `map.json` write; **keep** `compute_map_version()` for `NODE_MAP_VERSION`. Seed an example `registry.json` instead of CSV. Drop `csv` import. |
| `tools/check_registry_pushed.py` | `GUARDED_PATHS` keeps `"registry"` (now `registry.json` + `schema.json`) + headers + HA package; update comment (drop nodes.csv/bindings.yaml/node_id_hwm/map.json wording). |
| `registry/map.json` | **Deleted.** |

**Unchanged outputs:** `node_map.h`, `bindings.h`, `nodes/node*.yaml`, `ha_manifest_package.yaml` (byte-identical for current data); `protocol/*.h`; `gateway.yaml` lambdas.

## Hash & drift-visibility (preserved without map.json)

- `manifest_hash` — same canonical structure ⇒ empty hash stays `d66767448ba37b2f`; ADR-0009 §3 property intact.
- `map_version` — still computed (`compute_map_version(nodes, manifest_hash)`) and compiled as `NODE_MAP_VERSION`; just not written to a file.
- ADR-0009 §6 drift check — gateway's compiled `NODE_MAP_VERSION` vs the value in committed `node_map.h` (recomputable from `registry.json`); `map.json` was only a JSON copy, never load-bearing.

## Tests

| File | Change |
|---|---|
| `tests/test_bindings.py` → `tests/test_registry.py` | Hash determinism/sensitivity/empty-stability over the JSON structure; full validation matrix; multi-relay via native arrays. Drop the "unknown node_id" binding test — nesting makes a dangling binding unrepresentable. |
| `tests/test_generate_exports.py` | `render_bindings_header` tests unchanged. `map_version` tests call `compute_map_version()` (no file). Replace the `node_id 999` invalid-manifest test with bad-`op`/duplicate-button. Remove `build_map_export`/`map.json` assertions. |
| `tests/test_push_gate.py` | Repoint `nodes.csv`/`bindings.yaml`/`map.json` fixtures to `registry.json`. |

## Docs & ADRs

- `firmware/README.md` — registry section + workflow + the two `map.json` mentions (≈ lines 210, 230) → `registry.json`; point to `schema.json`.
- **New ADR-0014** — "Single JSON registry; drop map.json." Supersedes ADR-0009 §2 (two-file CSV+YAML split), §4/§7 (`map.json` artifact + export contract), and the no-PyYAML/hand-rolled-reader rationale. Must explicitly preserve the §3 "hash covers behavior only" property (bindings subset). New-ADR pattern as ADR-0013.
- ADR-0009 — "Partially superseded by ADR-0014" Status note.
- ADR-0011 (Proposed) — repoint `map.json` references to `registry.json`.
- ADR-0013 — light touch: bindings live in `registry.json`; `relay` is a native array.
- Historical `_bmad-output/implementation-artifacts/*.md` left as-is.

## One-time data migration

Throwaway `tools/migrate_to_json.py`: read nodes.csv + bindings.yaml + node_id_hwm → `write_registry()` → `registry/registry.json` (canonical bytes from commit one). Run once, verify, delete in the same PR.

## Sequencing (commit order)

Build on `bindings-multi-relay-fanout` (this subsumes the multi-relay + ADR-0013 work):
1. `registry.py` + `registry.json` + `schema.json` + migration script.
2. `generate_nodes.py`.
3. `allocate_node.py` + `commission.py`.
4. `check_registry_pushed.py`.
5. Tests (`test_registry.py`, update exports + push-gate).
6. Docs + ADR-0014 + ADR-0009/0011/0013 touches.
7. Delete `bindings.py` + `map.json` + migration script.

## Validation gates (must pass before commit)

- Empty-manifest `BINDINGS_MANIFEST_HASH` **still `d66767448ba37b2f`**.
- `node_map.h`, `bindings.h`, `nodes/*.yaml`, `ha_manifest_package.yaml` regenerate **byte-identical** to the migrated data.
- `registry.json` validates against `schema.json`.
- `test_registry.py` + `test_generate_exports.py` + `test_push_gate.py` green; `allocate → commission → generate` round-trip works.

</frozen-after-approval>
