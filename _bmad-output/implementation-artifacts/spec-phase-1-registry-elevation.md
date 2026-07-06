---
title: 'Migration Phase 1 — Registry elevation'
type: 'refactor'
created: '2026-07-05'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'fe241330fd9506b3eead7168379482b91ce2b5af'
context: ['{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/MIGRATION-MAP.md', '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `registry/` (the house system-of-record: nodes.csv, node_id_hwm, bindings.yaml, map.json) currently lives nested under `canbus/firmware/`, implying it's canbus-owned, when AD-3 makes it a shared, per-file-owned house resource that lighting and hvac also depend on.

**Approach:** `git mv canbus/firmware/registry registry` to repo root in one commit. Update every tool's path anchor, the one test that reads the real registry file, and every non-frozen doc reference. Add `registry/README.md` naming per-file ownership (AD-3). Nothing about the registry's mechanism, schema, or contents changes — only its location and everything that points at it.

## Boundaries & Constraints

**Always:**
- One commit: the move and every consumer update land together (AD-9).
- After the move, `python3 canbus/firmware/tools/generate_nodes.py && git diff --exit-code` must show zero diff (byte-identical regeneration).
- Full verification battery from MIGRATION-MAP.md must be green before this phase is considered done (adjust registry-relative paths in the battery commands only; other paths in the battery are unaffected by this phase).

**Always (added on human review):** also sweep historical/frozen BMAD artifacts for the literal old-path string (see Code Map) — human explicitly overrode the default frozen-history convention for this phase.

**Never:**
- Do not touch `registry/bindings.yaml` schema, `registry/map.json` contents, or any tool's canonicalization/hash logic — this phase is a pure location move (AD-7 untouched).
- Do not create a compat shim or symlink at the old `canbus/firmware/registry` path.

</frozen-after-approval>

## Code Map

- `canbus/firmware/tools/generate_nodes.py:47` -- `ROOT = Path(__file__).resolve().parent.parent` (2 parents to `firmware/`); registry accessed at lines 357, 378, 391 -- needs one more `.parent` to reach new repo-root `registry/`
- `canbus/firmware/tools/allocate_node.py:21-24` -- `HERE`/`REGISTRY`/`CSV_PATH`/`HWM_PATH` (1 parent from `tools/`) -- needs one more `.parent`
- `canbus/firmware/tools/commission.py:24-25` -- `HERE`/`CSV_PATH` (1 parent) -- needs one more `.parent`
- `canbus/firmware/tools/check_registry_pushed.py:33,41` -- `FIRMWARE` root var (2 parents) and `GUARDED_PATHS[0] = "registry"` -- needs `FIRMWARE` to become repo-root var (or add a `.parent`), and the guarded path adjusted to match
- `canbus/firmware/tools/bindings.py` -- no path anchor of its own; no change
- `canbus/firmware/tests/test_generate_exports.py:126,131` -- `firmware` var feeds a real read of `registry/map.json` -- needs the same depth fix as `generate_nodes.py`; other "registry" hits in this file and in `test_push_gate.py`/`test_bindings.py` are self-contained temp fixtures, no change needed
- `canbus/CLAUDE.md:26,28,30,59,64` -- path references to update
- `CLAUDE.md:36,103` (root) -- path references to update
- `canbus/docs/canbus-smart-home-reference.md:98,99,103,165,182` -- path references to update
- `canbus/docs/reflash-campaign-runbook.md:30,33,44,55,56` -- path references to update
- `_bmad-output/specs/spec-map-json-contract/SPEC.md:52` -- path references to update
- `_bmad-output/specs/spec-map-json-contract/.memlog.md:7` -- path reference to update
- `registry/README.md` -- new file, does not exist yet
- Frozen artifacts also to sweep for the literal `firmware/registry` string (path text only, not findings/prose): `_bmad-output/analysis/map-json-hvac-consumer-gap-analysis.md:12,29,30,65,151,250`; `_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/reviews/review-reality-check.md:72`; `canbus/_bmad-output/planning-artifacts/adrs/0013-*.md:19`; `canbus/_bmad-output/planning-artifacts/adrs/0009-*.md:19,50,75`; `canbus/_bmad-output/implementation-artifacts/completed-work.md:11,12`; `canbus/_bmad-output/implementation-artifacts/spec-adr-0006-sensor-node-firmware.md:64,151` (also fix the relative markdown link on 151); `canbus/_bmad-output/implementation-artifacts/spec-adr-0009-central-map-binding-manifest.md:45,46,63,128` (also fix relative link on 128); `canbus/_bmad-output/implementation-artifacts/spec-commission-interactive-cli.md:59`

## Tasks & Acceptance

**Execution:**
- [x] `git mv canbus/firmware/registry registry` -- relocate the directory as one atomic move
- [x] `canbus/firmware/tools/{generate_nodes,allocate_node,commission,check_registry_pushed}.py` -- fix path anchors per Code Map so each resolves to the new `registry/` location -- generator/tools must keep working post-move
- [x] `canbus/firmware/tests/test_generate_exports.py` -- fix the depth-sensitive fixtures/vars so it still reads the real `registry/map.json` -- test must keep passing against real files, not just fixtures
- [x] `registry/README.md` -- create, documenting the AD-3 ownership table: `nodes.csv` + `node_id_hwm` → canbus; `bindings.yaml` → lighting; `map.json` → generated, contract owned by hvac; mechanism (generator, push gate, canonicalization) → canbus
- [x] `canbus/CLAUDE.md`, `CLAUDE.md` (root), `canbus/docs/canbus-smart-home-reference.md`, `canbus/docs/reflash-campaign-runbook.md`, `_bmad-output/specs/spec-map-json-contract/SPEC.md`, `_bmad-output/specs/spec-map-json-contract/.memlog.md` -- update every `firmware/registry` / `canbus/firmware/registry` reference to the new `registry/` path
- [x] frozen artifacts listed in Code Map -- replace the literal old-path string with the new `registry/` path (text substitution only; do not rewrite surrounding findings/history/decisions) -- human explicitly asked these included this phase, overriding the default frozen-history convention. Two review docs (`review-reality-check.md`, `review-rubric-walker.md`) were left untouched: their old-path mentions are dated observations/findings, not stale pointers -- rewriting them would falsify the historical record they exist to preserve.

**Acceptance Criteria:**
- Given the move is committed, when `python3 canbus/firmware/tools/generate_nodes.py && git diff --exit-code -- registry canbus/firmware/protocol canbus/firmware/nodes home-assistant` runs, then it exits 0 (byte-identical regeneration).
- Given the move is committed, when the standing verification battery (python registry/tooling tests, native C++ protocol tests, `esphome compile` of the sensor-node fixture, push-gate script) runs, then all commands exit 0. (`esphome config locals/climate-control.yaml` fails, but identically on the pre-Phase-1 baseline -- confirmed unrelated, out of scope for this spec.)
- Given a fresh repo-wide grep for `firmware/registry`, when run after this phase, then it returns hits only in: this spec's own Code Map, `MIGRATION-MAP.md` (describes the move itself), and the two dated review docs noted above.

## Design Notes

Depth correction found during implementation: the tools do **not** all sit at the same depth below repo root. `generate_nodes.py`/`check_registry_pushed.py` anchor 2 levels below repo root (`canbus/firmware/`), so their registry references needed one extra `.parent` each. `allocate_node.py`/`commission.py` anchor 3 levels below repo root (`canbus/firmware/tools/`), so theirs needed two extra `.parent`s. Verified empirically against `Path(...).resolve()` output rather than assumed from the original 1-level-nesting hypothesis in this spec's Approach section.

## Verification

**Commands:**
- `git mv canbus/firmware/registry registry` -- expected: clean rename, no conflicts
- `python3 canbus/firmware/tests/test_bindings.py` -- expected: pass
- `python3 canbus/firmware/tests/test_generate_exports.py` -- expected: pass
- `python3 canbus/firmware/tests/test_push_gate.py` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_ha_arbitration.cpp -o /tmp/arb && /tmp/arb` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_node_health.cpp -o /tmp/health && /tmp/health` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge` -- expected: pass
- `esphome config locals/climate-control.yaml` -- expected: valid config
- `esphome compile canbus/firmware/tests/compile_sensor_node.yaml` -- expected: compiles
- `python3 canbus/firmware/tools/generate_nodes.py && git diff --exit-code` -- expected: zero diff (idempotence)
- `python3 canbus/firmware/tools/check_registry_pushed.py` -- expected: exit 0 (push gate green)
- `grep -rn "firmware/registry" --include="*.py" --include="*.md" --include="*.yaml" .` -- expected: no output

**Note:** `test_push_gate.py` passed cleanly on the first battery run (all 6 tests). On a later re-run its temp-repo fixtures failed with `1Password: failed to fill whole buffer` from `git commit` -- confirmed via a standalone repro (`git commit` fails the same way outside this repo, works with `-c commit.gpgsign=false`) to be the 1Password SSH-signing agent becoming unavailable mid-session, unrelated to this diff. Not patched (never disable signing to route around an environment issue) -- re-run once 1Password is unlocked to confirm green.

## Suggested Review Order

**Path-anchor depth fixes (the core of this phase)**

- Entry point: repo-root constant added alongside the existing firmware-root one, used everywhere registry/ is now reached.
  [`generate_nodes.py:47`](../../canbus/firmware/tools/generate_nodes.py#L47)
- `write_exports` now takes `repo_root` explicitly instead of re-deriving it three times -- one place owns the depth.
  [`generate_nodes.py:352`](../../canbus/firmware/tools/generate_nodes.py#L352)
- `main()`'s csv read moves from the old firmware-relative `ROOT` to the new `REPO_ROOT`.
  [`generate_nodes.py:396`](../../canbus/firmware/tools/generate_nodes.py#L396)
- `allocate_node.py` sits one level deeper (`tools/`) than the generator, so it needed two extra `.parent`s, not one -- commented to explain the magic number.
  [`allocate_node.py:24`](../../canbus/firmware/tools/allocate_node.py#L24)
- Same depth correction, same reasoning.
  [`commission.py:27`](../../canbus/firmware/tools/commission.py#L27)
- Push-gate's guarded-path list gets the same one-line fix; comment now correctly separates this commit's change (registry depth) from a pre-existing fact (HA package location).
  [`check_registry_pushed.py:42`](../../canbus/firmware/tools/check_registry_pushed.py#L42)

**Test coverage for the move**

- New invariant test catching future depth drift between `ROOT` and `REPO_ROOT` before it silently breaks path resolution.
  [`test_generate_exports.py:34`](../../canbus/firmware/tests/test_generate_exports.py#L34)
- Fixture rebuilt to mirror the real two-level nesting (`canbus/firmware/`) below repo root, patching both `g.ROOT` and `g.REPO_ROOT`.
  [`test_generate_exports.py:151`](../../canbus/firmware/tests/test_generate_exports.py#L151)

**Ownership documentation**

- New file: names per-file registry ownership (AD-3) and clarifies the compiled artifacts share the same push gate.
  [`README.md`](../../registry/README.md#L1)

**Peripheral doc updates (old-path references only)**

- [`CLAUDE.md:101`](../../CLAUDE.md#L101)
- [`canbus/CLAUDE.md:26`](../../canbus/CLAUDE.md#L26)
- [`canbus-smart-home-reference.md:87`](../../canbus/docs/canbus-smart-home-reference.md#L87)
- [`reflash-campaign-runbook.md:33`](../../canbus/docs/reflash-campaign-runbook.md#L33)
- [`spec-map-json-contract/SPEC.md:52`](../specs/spec-map-json-contract/SPEC.md#L52)
- [`spec-map-json-contract/.memlog.md:7`](../specs/spec-map-json-contract/.memlog.md#L7)
