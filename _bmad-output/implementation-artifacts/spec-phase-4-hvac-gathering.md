---
title: 'Migration Phase 4 — HVAC gathering'
type: 'refactor'
created: '2026-07-06'
status: 'done'
review_loop_iteration: 0
baseline_commit: '14c3112a18c406061f77c9a951e89058ca7ba1a8'
context: ['{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/MIGRATION-MAP.md', '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `components/` (13 room configs + `mev_modbus.yaml`/`mev_demand.yaml`/`room_sensors.yaml`) is the HVAC application's home today, but it's an ambiently-named top-level directory rather than a named system — exactly what AD-1 exists to prevent. `hvac/` already exists (Phase 3 put `hvac/home-assistant/dashboards/` there); this phase gathers the rest of the HVAC application into it.

**Approach:** `git mv components/rooms hvac/rooms`; `git mv` the 3 loose files into `hvac/`; remove the now-empty `components/`. Fix the 3 `!include` lines in `devices/climate-control.yaml`, the generator's `room_slug` validation path (an AD-6 contract edit: `generate_nodes.py`, `spec-map-json-contract`, and the one comment in its test move together in this commit), and every functionally-load-bearing doc reference (root `CLAUDE.md`'s path examples, `canbus/firmware/tools/commission.py`'s CLI help string). Write `hvac/CLAUDE.md`. One commit (AD-9): `remotes/climate-control.yaml` fetches `devices/climate-control.yaml@main` from GitHub in production, so a half-moved tree would strand that fetch.

## Boundaries & Constraints

**Always:**
- One commit: moves, every `!include` fix, the generator/spec/test AD-6 edit, and doc updates land together (AD-9).
- Files *inside* `hvac/rooms/**` and the 3 loose files keep their own `!include`s unchanged -- they all point out to `vesta/packages/components/*`, and that relative depth is unaffected by this move (confirmed: `hvac/` is a sibling of the old `components/` at the same tree depth as `vesta/`).
- `esphome config locals/climate-control.yaml` is already failing on pre-existing, unrelated bugs (multiple missing-ID errors -- `soggiorno_boost_active`/`cucina_boost_active` fail first, `soggiorno_last_mode_change_time`/`cucina_last_mode_change_time` fail later in the same run -- confirmed present on the pre-Phase-1 baseline too, byte-identical error set). This phase's verification battery will show the same failures; do not attempt to fix them here, it's out of scope.

**Always (added on human review):** also update `canbus/CLAUDE.md:70`'s cross-reference to `components/rooms/**` -- it documents the same room_slug contract as `commission.py`'s help string, so leaving it stale would create an inconsistency between two docs describing the same thing.

**Never:**
- Do not sweep the wider list of living (non-frozen) planning/analysis docs that also mention `components/` but aren't operationally load-bearing (PRD, architecture.md, epics.md, analysis docs, `MIGRATION-MAP.md`'s own Phase 4 bullet list) -- human explicitly confirmed leaving these, consistent with scope discipline from prior phases.
- The frozen-history convention continues to apply to `canbus/_bmad-output/**`, numbered epic docs under `_bmad-output/implementation-artifacts/`, and `canbus/docs/merge-into-esphome-devices-proposal.md` -- leave untouched, consistent with Phases 1-3.
- Do not touch `vesta/packages/**` -- unrelated, stable path, not part of this move.
- Do not rewrite root `CLAUDE.md` beyond the specific stale path examples this move breaks -- a full four-system rewrite is Phase 6 scope.

</frozen-after-approval>

## Code Map

- `components/rooms/` -- `git mv` to `hvac/rooms/` (13 room files + 3 floor aggregators across 3 floor dirs)
- `components/{mev_modbus.yaml,mev_demand.yaml,room_sensors.yaml}` -- `git mv` to `hvac/`
- `devices/climate-control.yaml:38-40` -- `../components/rooms/...` -> `../hvac/rooms/...` (3 lines)
- `canbus/firmware/tools/generate_nodes.py:125` -- `load_climate_zones`'s `rooms_dir` default: `ROOT.parent.parent / "components" / "rooms"` -> `REPO_ROOT / "hvac" / "rooms"` (reusing the existing module-level constant rather than re-deriving `ROOT.parent.parent`, per Edge Case Hunter's observation); also fix the two docstring/comment mentions at lines 19-20 and 120
- `canbus/firmware/tools/allocate_node.py` -- checked, no path reference to `components/` exists (only a `room_slug` mention in a comment, no path) -- no change needed
- `canbus/firmware/tools/commission.py:214` -- CLI `help=` string mentioning `components/rooms/**` (found during investigation, not in the original plan bullets, but same contract)
- `_bmad-output/specs/spec-map-json-contract/SPEC.md:39,61` -- path references (line 61 is an open question mentioning the path, not a hard contract statement -- update for consistency)
- `canbus/firmware/tests/test_generate_exports.py:12-13` -- comment only; the actual test (`test_load_climate_zones_reads_real_room_packages`, `test_validate_room_slug_branches`) doesn't hardcode the path, so it will pick up the fixed default automatically once `generate_nodes.py` is fixed
- `hvac/CLAUDE.md` -- new file: entity-ID convention (ported from root `CLAUDE.md`'s existing convention section), epic prefix **HVAC-**
- `CLAUDE.md` (root) -- the repo-structure tree's `components/` entry, the "Component/Room Configs" naming-convention headers, the composition-hierarchy diagram's `components/room_sensors.yaml` mention, the "Adding a New Room" task example, and the Important Files Reference table's `components/mev_modbus.yaml` row -- all become `hvac/`-rooted
- `canbus/CLAUDE.md:70` -- cross-reference to `components/rooms/**` -- becomes `hvac/rooms/**`

## Tasks & Acceptance

**Execution:**
- [x] `git mv components/rooms hvac/rooms`
- [x] `git mv components/mev_modbus.yaml components/mev_demand.yaml components/room_sensors.yaml hvac/`
- [x] Removed the now-empty `components/` directory
- [x] `devices/climate-control.yaml` -- fixed the 3 `!include` lines
- [x] `canbus/firmware/tools/generate_nodes.py` -- fixed `load_climate_zones`'s `rooms_dir` default and the two docstring/comment mentions
- [x] `canbus/firmware/tools/commission.py` -- fixed the CLI help string (verified only by manual read-through; `commission.py` has no automated test coverage at all, a pre-existing gap already logged in `deferred-work.md` from Phase 1's review, not newly introduced here)
- [x] `_bmad-output/specs/spec-map-json-contract/SPEC.md` -- fixed both path mentions
- [x] `canbus/firmware/tests/test_generate_exports.py` -- fixed the comment (logic itself needed no change, confirmed by test passing)
- [x] `hvac/CLAUDE.md` -- created, ported the entity-ID convention section from root `CLAUDE.md` as hvac's own per-system convention (AD-10); epic prefix **HVAC-**; also documents the room_slug/canbus contract
- [x] Root `CLAUDE.md` -- updated the repo-structure tree (now a real `hvac/` tree node, not a comment), naming-convention headers, composition-hierarchy diagram, "Adding a New Room" example, and Important Files Reference table. Left three pre-existing-stale `components/` mentions (Hardware Packages, Radiant, Fancoil, Boost Coordinator lines) untouched -- those predate this move entirely (from an earlier Vesta extraction, no such files ever existed in `components/`), out of this phase's scope.
- [x] `canbus/CLAUDE.md:70` -- fixed the `components/rooms/**` cross-reference
- [x] `canbus/firmware/README.md:239` -- found during the final grep sweep (missed by the original investigation), same operational-doc category as every other canbus README fix this migration -- fixed for consistency

**Acceptance Criteria:**
- Given the moves are committed, when `git status` is checked, then `components/` no longer exists, `hvac/rooms/` and the 3 loose files exist under `hvac/` with all content intact (100% similarity renames). -- confirmed.
- Given the standing verification battery plus `esphome compile locals/climate-control.yaml`, when run after this phase, then all commands exit 0 *except* the pre-existing `esphome config`/`compile` failures (multiple missing-ID errors, first is `soggiorno_boost_active`), confirmed byte-identical to the pre-Phase-1 baseline and unrelated to this phase -- crucially no "file not found" on the `!include` paths, proving the fix worked before hitting the pre-existing bugs. -- confirmed.
- Given `python3 canbus/firmware/tests/test_generate_exports.py`, when run after this phase, then `test_load_climate_zones_reads_real_room_packages` still finds 14 zones (reading from the new `hvac/rooms/**` location via the fixed default). -- confirmed (full suite passed).
- Given a fresh grep for `components/rooms` and `components/mev_modbus\|components/mev_demand\|components/room_sensors`, when run after this phase, then it returns hits only in frozen/historical docs and the wider living-docs list left untouched per Ask First -- plus `docs/ha-dashboard-config.yaml` and `.github/copilot-instructions.md`, two additional living docs in the same "wider list, leave alone" category not enumerated by name in the original Ask First but covered by the same human decision. -- confirmed.

## Design Notes

`load_climate_zones(rooms_dir: Path = None)` accepts an optional override -- the two tests that exercise it against a real tree (`test_load_climate_zones_reads_real_room_packages`) call it with no argument, so they'll transparently pick up the corrected default. No test code needs to hardcode the new path.

## Verification

**Commands:**
- `git mv components/rooms hvac/rooms` -- expected: clean rename
- `git mv components/mev_modbus.yaml components/mev_demand.yaml components/room_sensors.yaml hvac/` -- expected: clean rename
- `python3 canbus/firmware/tests/test_bindings.py` -- expected: pass
- `python3 canbus/firmware/tests/test_generate_exports.py` -- expected: pass, including the 14-zone check
- `python3 canbus/firmware/tests/test_push_gate.py` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_ha_arbitration.cpp -o /tmp/arb && /tmp/arb` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_node_health.cpp -o /tmp/health && /tmp/health` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge` -- expected: pass
- `esphome compile canbus/firmware/tests/compile_sensor_node.yaml` -- expected: compiles
- `esphome config locals/climate-control.yaml` -- expected: fails identically to the pre-Phase-1 baseline (pre-existing, unrelated bug)
- `esphome compile locals/climate-control.yaml` -- expected: fails identically, same reason
- `python3 canbus/firmware/tools/generate_nodes.py && git diff --exit-code -- registry canbus/firmware/protocol canbus/firmware/nodes canbus/home-assistant/ha_manifest_package.yaml` -- expected: zero diff (idempotence; unaffected by this phase)
- `python3 canbus/firmware/tools/check_registry_pushed.py` -- expected: exit 0 once committed and pushed
- `grep -rn "components/rooms\|components/mev_modbus\|components/mev_demand\|components/room_sensors" --include="*.py" --include="*.md" --include="*.yaml" .` -- expected: hits only in frozen/historical docs and the wider living-docs list left untouched per Ask First

**Note:** `test_push_gate.py`'s temp-repo fixtures transiently failed with `1Password: failed to fill whole buffer` from `git commit` during this review -- the same environment issue (1Password SSH-signing agent unavailable) seen in Phase 1, confirmed via a standalone repro outside this repo, unrelated to this diff. Not patched. All 6 tests passed on the initial battery run before this transient failure; re-run once 1Password is unlocked to reconfirm.

## Suggested Review Order

**The moves**

- Entry point: room configs and floor aggregators relocated intact.
  [`hvac/rooms/`](../../hvac/rooms#L1)
- The 3 loose files, gathered alongside.
  [`hvac/mev_modbus.yaml`](../../hvac/mev_modbus.yaml#L1)

**The AD-6 contract edit (spec + code + test move together)**

- The validation path itself -- now reuses the existing `REPO_ROOT` constant instead of re-deriving it (a fix applied during review).
  [`generate_nodes.py:125`](../../canbus/firmware/tools/generate_nodes.py#L125)
- The frozen contract spec, including an Open Question closed out during review since this same commit already answers it.
  [`SPEC.md:61`](../specs/spec-map-json-contract/SPEC.md#L61)
- `devices/climate-control.yaml`'s 3 `!include` lines -- the one place a wrong fix would have broken `esphome compile` outright.
  [`climate-control.yaml:38`](../../devices/climate-control.yaml#L38)

**System charter**

- New `hvac/CLAUDE.md` -- ports the entity-ID convention (deliberately duplicated pending Phase 6, tracked in `deferred-work.md`) and documents the room_slug/canbus contract.
  [`hvac/CLAUDE.md:1`](../../hvac/CLAUDE.md#L1)

**Peripheral doc updates**

- Root `CLAUDE.md`'s composition-hierarchy diagram -- also fixed 3 filenames that were wrong entirely (not just stale-path), found during review.
  [`CLAUDE.md:323`](../../CLAUDE.md#L323)
- [`canbus/CLAUDE.md:70`](../../canbus/CLAUDE.md#L70)
- [`canbus/firmware/README.md:239`](../../canbus/firmware/README.md#L239)
- [`canbus/firmware/tools/commission.py:214`](../../canbus/firmware/tools/commission.py#L214)
