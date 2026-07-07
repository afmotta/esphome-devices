---
title: 'Migration Phase 6a — Flatten canbus'
type: 'refactor'
created: '2026-07-07'
status: 'done'
review_loop_iteration: 0
baseline_commit: '1400a7cc1c94db921479d8095399b1a25213906b'
context: ['{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `canbus/firmware/` is now empty ceremony — registry (Phase 1), gateway/bridge (Phase 5a), and the gateway-side package (Phase 5b-2) already moved out; only protocol/nodes/tools/tests remain nested one level deeper than every other system's content. Separately, an unrelated bug from Phase 1 left `canbus/firmware/registry/{nodes.csv,bindings.yaml,node_id_hwm,map.json}` still tracked in git — a stale, unused duplicate of the real `registry/` (content frozen-identical, confirmed no drift, but dead weight in the tree).

**Approach:** `git mv canbus/firmware/{protocol,nodes,tools,tests} canbus/`. Merge the 3 node-side packages into `canbus/packages/` file-by-file (that directory already holds `health.yaml` from Phase 5b-2 — a plain directory rename would fail). Fix every path that assumed the old `canbus/firmware/X/` depth. `git rm` the stale registry duplicate. Relocate `canbus/firmware/README.md` to `canbus/README.md`; retire `canbus/firmware/.gitignore` (redundant with root's unanchored patterns, same reasoning as the Phase 5a `.gitignore` retirements). No context/CLAUDE.md rewrite here — that's Phase 6b.

## Boundaries & Constraints

**Always:**
- One commit: moves, path fixes, and doc updates land together (AD-9).
- Depth arithmetic is verified empirically before AND after each edit — this project has a demonstrated history of off-by-one errors here (Phase 1's original REPO_ROOT mistake; this very investigation caught two more reasoning errors, one mine, one a subagent's). Use `python3 -c "from pathlib import Path; print(...)"` against the real post-move paths, not armchair arithmetic. Every fixed path gets a real command run against it (test execution or `esphome compile`), not just a visual check.
- `canbus/packages/` merge is 3 individual `git mv` commands (base_node.yaml, button.yaml, sensor_kit.yaml), not a directory rename — the destination already exists and is non-empty.
- Registry duplicate content is confirmed byte-identical to the real `registry/` (verified during scoping) — `git rm`, not a diff/merge.
- Full battery + `esphome compile devices/gateway.yaml` + `esphome compile devices/bridge.yaml` + `esphome compile canbus/tests/compile_sensor_node.yaml` green, byte-identical regeneration.

**Ask First:** none identified — every disposition (packages merge, README/`.gitignore` relocation, registry cleanup) was already decided in this session's scoping.

**Never:**
- No CLAUDE.md rewrites (root or `canbus/CLAUDE.md` beyond literal path substitutions already covered elsewhere) and no Claude memory-file edits — both are Phase 6b.
- Do not touch `canbus/packages/health.yaml`, `lighting/packages/buttons.yaml`, `devices/gateway.yaml`'s composition logic, or the bindings contract/drift test beyond the include-path fixes this move forces.
- Do not rewrite the historical/frozen `canbus/_bmad-output/**`, numbered epic docs, or prior migration-phase spec files that describe old paths as history — consistent with every prior phase's convention.

</frozen-after-approval>

## Code Map

- `canbus/firmware/protocol/*.h` (6 files) -- `git mv` to `canbus/protocol/`
- `canbus/firmware/nodes/{.gitignore,node100.yaml,node101.yaml}` -- `git mv` to `canbus/nodes/`
- `canbus/firmware/tools/*.py` (5 files) -- `git mv` to `canbus/tools/`
- `canbus/firmware/tests/*` (9 files + `.gitignore`) -- `git mv` to `canbus/tests/`
- `canbus/firmware/packages/{base_node.yaml,button.yaml,sensor_kit.yaml}` -- individual `git mv` into existing `canbus/packages/` (alongside `health.yaml`)
- `canbus/firmware/registry/{nodes.csv,bindings.yaml,node_id_hwm,map.json}` -- `git rm` (stale duplicate, confirmed byte-identical to `registry/`, no drift)
- `canbus/firmware/README.md` -- `git mv` to `canbus/README.md`
- `canbus/firmware/.gitignore` -- `git rm` (root's unanchored `.esphome/`/`secrets.yaml` patterns already cover it)
- `canbus/firmware/tools/generate_nodes.py:47-48` -- `ROOT`'s 2-hop definition is unchanged code but now resolves to `canbus/` (update comment only, `# firmware/` → `# canbus/`); `REPO_ROOT` drops one hop: `ROOT.parent.parent` → `ROOT.parent`
- `canbus/firmware/tools/allocate_node.py:24` -- `REGISTRY` drops one hop: `HERE.parent.parent.parent` → `HERE.parent.parent`
- `canbus/firmware/tools/commission.py:27` -- `CSV_PATH` drops one hop, same pattern
- `canbus/firmware/tools/check_registry_pushed.py:33,42-46` -- `FIRMWARE`'s 2-hop definition unchanged code, now resolves to `canbus/` (rename to `CANBUS_ROOT`, update comment); `GUARDED_PATHS`: `"../../registry"` → `"../registry"` (one fewer level), `"protocol/node_map.h"`/`"protocol/bindings.h"` unchanged (self-correct), `"../home-assistant/ha_manifest_package.yaml"` → `"home-assistant/ha_manifest_package.yaml"` (drop the leading `../`)
- `canbus/firmware/tests/test_generate_exports.py:22` -- `sys.path.insert` 2-hop pattern unchanged code, self-corrects (verify, don't just trust)
- `canbus/firmware/tests/test_generate_exports.py:39` -- `assert g.REPO_ROOT == g.ROOT.parent.parent` → `g.ROOT.parent` (tracks the generator's fix)
- `canbus/firmware/tests/test_generate_exports.py:134-135` -- `firmware` var (line 134) unchanged code, self-corrects to `canbus/`; `repo_root = firmware.parent.parent` (line 135) → `firmware.parent` (one fewer hop)
- `canbus/firmware/tests/test_generate_exports.py:154,222` -- fixture `root = repo_root / "canbus" / "firmware"` → `root = repo_root / "canbus"` (drop the now-nonexistent `firmware` component; `saved_root`/`g.ROOT` patch sites unaffected)
- `canbus/firmware/tests/test_bindings.py:15`, `test_push_gate.py:17` -- same `sys.path.insert` 2-hop pattern, verify self-correction
- `canbus/firmware/tests/test_generate_exports.py:10-13` docstring, `compile_sensor_node.yaml:10-11` comment -- stale `firmware/tests/...` path text
- `devices/gateway.yaml:40-44`, `devices/bridge.yaml:59-60` -- includes `../canbus/firmware/protocol/*.h` → `../canbus/protocol/*.h`
- `canbus/firmware/README.md` (moved content) -- internal path references reviewed for the new `canbus/` (not `canbus/firmware/`) vantage point
- `registry/README.md:16,19-20` -- update `canbus/firmware/tools/generate_nodes.py` references to `canbus/tools/generate_nodes.py`
- Found during implementation, same load-bearing-doc category fixed every prior phase: `canbus/CLAUDE.md` (test battery block, hard rules, integration section -- literal path substitutions only, full trim to infra-only is Phase 6b), `hvac/CLAUDE.md:98`, `canbus/README.md` (the just-relocated content, several `canbus/firmware/tests/*` command examples), `canbus/docs/reflash-campaign-runbook.md` (5 command paths), `canbus/home-assistant/README.md`, `canbus/docs/canbus-smart-home-reference.md`'s tree diagram -- doubly stale (still showed `gateway/` nested here even though it moved to `devices/` back in Phase 5a, apparently missed then)

## Tasks & Acceptance

**Execution:**
- [x] `git mv canbus/firmware/protocol canbus/protocol`
- [x] `git mv canbus/firmware/nodes canbus/nodes`
- [x] `git mv canbus/firmware/tools canbus/tools`
- [x] `git mv canbus/firmware/tests canbus/tests`
- [x] `git mv canbus/firmware/packages/{base_node,button,sensor_kit}.yaml canbus/packages/` -- no collision with `health.yaml`
- [x] Confirmed byte-identical to `registry/` immediately before removal, then `git rm` the 4 stale `canbus/firmware/registry/` files
- [x] `git mv canbus/firmware/README.md canbus/README.md`
- [x] `git rm canbus/firmware/.gitignore`
- [x] Fixed `generate_nodes.py`, `allocate_node.py`, `commission.py`, `check_registry_pushed.py` per Code Map; every hop verified empirically via `python3 -c` one-liners before trusting it, per Design Notes
- [x] Fixed `test_generate_exports.py` (line 22 verified self-correcting, no change; lines 39, 134-135, 154, 222 patched), `test_bindings.py:15`/`test_push_gate.py:17` verified self-correcting, no change
- [x] Fixed `devices/gateway.yaml`, `devices/bridge.yaml` includes
- [x] Updated stale path prose: `test_generate_exports.py` docstring, `compile_sensor_node.yaml` comment, `registry/README.md`
- [x] Confirmed `canbus/firmware/` has zero tracked files remaining (`git ls-files canbus/firmware` empty)
- [x] Found during implementation (same load-bearing-doc category as every prior phase): fixed `canbus/CLAUDE.md`, `hvac/CLAUDE.md`, `canbus/README.md`, `canbus/docs/reflash-campaign-runbook.md`, `canbus/home-assistant/README.md`, and `canbus/docs/canbus-smart-home-reference.md`'s tree diagram (also fixed a Phase-5a-era staleness there: it still showed `gateway/` nested under this directory)

**Acceptance Criteria:**
- Given the moves are committed, when `git ls-files canbus/firmware` is checked, then it returns nothing. -- confirmed.
- Given `canbus/packages/`, when listed, then it contains `health.yaml`, `base_node.yaml`, `button.yaml`, `sensor_kit.yaml` — four files, no collision. -- confirmed.
- Given the standing battery (all Python tests, all native C++ tests including `test_bindings_contract`, `esphome compile` of `canbus/tests/compile_sensor_node.yaml`, `devices/gateway.yaml`, `devices/bridge.yaml`) plus regeneration idempotence and the push gate, when run after this phase, then all green. -- confirmed; gateway/bridge both compile SUCCESS, push gate correctly finds the newly-regenerated files at their new paths (expected pre-commit "uncommitted" state).
- Given a fresh grep for `canbus/firmware/`, when run after this phase, then it returns hits only in frozen/historical docs, prior migration-phase spec files, and `canbus/docs/merge-into-esphome-devices-proposal.md` (a closed proposal doc marked `Status: Implemented 2026-07-05`, same historical category, initially missed from the Never list and confirmed by review). -- confirmed.

## Design Notes

The core insight, verified against real file content rather than assumed: every file whose `.parent` chain is anchored **directly on `Path(__file__)`** (`ROOT` in `generate_nodes.py`, `HERE` in `allocate_node.py`/`commission.py`, `FIRMWARE` in `check_registry_pushed.py`, the `sys.path.insert` lines, the `firmware` var in `test_generate_exports.py`) needs **no change to its own hop count** — the file itself moved one level shallower, so the same hop count now lands one directory shallower too, which is exactly the new target. Only variables defined **relative to one of those anchors** (`REPO_ROOT = ROOT.parent.parent`, `REGISTRY = HERE.parent.parent.parent`, `GUARDED_PATHS`'s `"../../registry"`, `repo_root = firmware.parent.parent`) need one *fewer* hop, since their anchor already absorbed the depth reduction. Getting this backwards (as both a subagent and I did at least once during scoping, independently, before cross-checking against real file content) silently produces a path that resolves to the wrong directory without necessarily erroring — hence the Always rule mandating empirical verification, not arithmetic alone.

## Verification

**Commands:**
- `git mv canbus/firmware/protocol canbus/protocol` (and the other 4 top-level moves) -- expected: clean renames
- `git mv canbus/firmware/packages/{base_node,button,sensor_kit}.yaml canbus/packages/` -- expected: clean renames, no collision with `health.yaml`
- `python3 canbus/tests/test_bindings.py` -- expected: pass
- `python3 canbus/tests/test_generate_exports.py` -- expected: pass, including `test_repo_root_depth_invariant`
- `python3 canbus/tests/test_push_gate.py` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto` -- expected: pass (and the other 4 C++ tests, including `test_bindings_contract`)
- `esphome compile canbus/tests/compile_sensor_node.yaml` -- expected: compiles
- `esphome compile devices/gateway.yaml` -- expected: compiles
- `esphome compile devices/bridge.yaml` -- expected: compiles
- `python3 canbus/tools/generate_nodes.py && git diff --exit-code -- registry canbus/protocol canbus/nodes canbus/home-assistant/ha_manifest_package.yaml` -- expected: zero diff
- `python3 canbus/tools/check_registry_pushed.py` -- expected: exit 0 once committed and pushed
- `git ls-files canbus/firmware` -- expected: empty
- `grep -rn "canbus/firmware/" --include="*.py" --include="*.md" --include="*.yaml" .` -- expected: hits only in frozen/historical docs and closed migration-phase specs

**Note (review):** two review agents ran successfully this time (last phase's spend-limit outage was transient). Both independently verified every depth-arithmetic fix by resolving real paths — no errors found in the core mechanical work. Both found real gaps in the doc sweep: `canbus/CLAUDE.md` still had one stray `firmware/README.md` reference (missed despite other hunks touching this same file — patched), my own tree-diagram edit in `canbus-smart-home-reference.md` introduced a *new* wrong relative path (`../registry` when the doc's own established convention elsewhere is repo-root-relative prose with no `../` at all — corrected) plus a dangling `│` box-drawing character (fixed) and an incomplete file listing (added `canbus/README.md`). Two stale test docstrings (`test_bindings.py`, `test_push_gate.py` — both said `firmware/tests/...`, predating even this phase) were patched. A genuinely new file, `devices/.gitignore`, kept reappearing from ESPHome's CLI auto-generating one on every `esphome compile` run against a directory without one (same phenomenon first seen in Phase 5a) — deleted again, will keep recurring on future compiles. One real latent finding, not code-fixed: `canbus/packages/base_node.yaml` and `health.yaml` both use `id: can0` for unrelated CAN components; confirmed no current entry point composes both, documented with cross-reference comments in each file, logged to `deferred-work.md` rather than renaming an id that would touch every generated node file (out of scope for a mechanical flatten). My own acceptance criterion's claim about grep hits was corrected to honestly include `canbus/docs/merge-into-esphome-devices-proposal.md` (a closed, dated proposal doc — same historical category as the frozen docs, just not originally named in my Never list).

## Suggested Review Order

**The flatten**

- Entry point: the generator's ROOT/REPO_ROOT redefinition — the crux of the whole phase's depth arithmetic.
  [`generate_nodes.py:47`](../../canbus/tools/generate_nodes.py#L47)
- The registry-duplicate bug fix, folded in from an unrelated Phase 1 mistake found during scoping.
  [`canbus/nodes/`](../../canbus/nodes#L1)
- The package merge -- four files, one pre-existing naming coincidence made visible (not caused) by the merge.
  [`canbus/packages/health.yaml:126`](../../canbus/packages/health.yaml#L126)

**Path fixes (verify the empirical-not-assumed claim)**

- [`allocate_node.py:21`](../../canbus/tools/allocate_node.py#L21)
- [`check_registry_pushed.py:32`](../../canbus/tools/check_registry_pushed.py#L32) -- the `FIRMWARE`→`CANBUS_ROOT` rename and the three-way `GUARDED_PATHS` depth changes.
- [`test_generate_exports.py:34`](../../canbus/tests/test_generate_exports.py#L34) -- the dedicated depth-invariant test, updated in lockstep.

**Doc sweep (where the review actually found things)**

- [`canbus/CLAUDE.md:19`](../../canbus/CLAUDE.md#L19)
- The tree diagram -- fixed a wrong path my own earlier edit introduced, plus the dangling bar and missing README entry.
  [`canbus-smart-home-reference.md:92`](../../canbus/docs/canbus-smart-home-reference.md#L92)
