---
title: 'Migration Phase 3 — HA split completes'
type: 'refactor'
created: '2026-07-06'
status: 'done'
review_loop_iteration: 0
baseline_commit: '015d8e941d1f1d0368120cfae4bc9281e72fb9b1'
context: ['{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/MIGRATION-MAP.md', '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The top-level `home-assistant/` directory still holds two unrelated things: canbus's remaining HA-import surface (`canbus/ha_arbitration_automations.yaml`, generated `ha_manifest_package.yaml`) and the HVAC dashboards (`dashboards/`). AD-5 says HA artifacts live with their owning system; a monolithic `home-assistant/` is exactly what AD-5 exists to prevent.

**Approach:** `git mv` the remaining canbus HA files to `canbus/home-assistant/`, and the whole `dashboards/` tree to `hvac/home-assistant/dashboards/` (first thing to land in a new `hvac/` directory — the rest of `hvac/` arrives in Phase 4). Teach `generate_nodes.py` the new manifest output path and regenerate. Delete the now-empty top-level `home-assistant/`. Port `home-assistant/canbus/README.md`'s content into `canbus/home-assistant/README.md`; write a small new README for `hvac/home-assistant/` since dashboards never had a folder-purpose README of its own (only usage docs).

## Boundaries & Constraints

**Always:**
- One commit: both moves, the generator path fix, and every in-repo consumer/doc update land together (AD-9).
- `dashboards/install-dashboards.py` and `install-dashboards.sh` are both self-relative (`Path(__file__).parent` / `$SCRIPT_DIR`) — confirmed neither breaks from the move; do not add any repo-root-relative logic to them.
- Full verification battery from MIGRATION-MAP.md must be green, and generator regeneration must write `ha_manifest_package.yaml` to the new path idempotently.

**Always (added on human review):** also update the ~28 lines of illustrative path examples across the four dashboard usage docs (`README.md`, `QUICK_START.md`, `API_INSTALLATION.md`, `INDEX.md`) to the new `hvac/home-assistant/dashboards/` path — human explicitly asked for this, confirmed no live CI file exists so nothing functional is at stake either way, purely doc accuracy.

**Ask First:**
- The human must perform the remaining manual HA package re-point (arbitration automation + manifest package includes) on their live Home Assistant instance after this commit lands.

**Never:**
- Do not update frozen/historical docs that mention the old paths (`canbus/_bmad-output/implementation-artifacts/{completed-work.md, spec-adr-0003-ha-ready-arbitration.md, spec-adr-0009-central-map-binding-manifest.md, spec-adr-0009-push-discipline-gate.md}`, `canbus/docs/merge-into-esphome-devices-proposal.md`) — human explicitly confirmed leaving these untouched, consistent with the Phase 1/2 frozen-history default.
- Do not touch `lighting/home-assistant/ha_hold_automations.yaml` (Phase 2, already done).
- Do not write any `hvac/` content beyond `home-assistant/dashboards/` in this phase — `hvac/rooms`, `hvac/CLAUDE.md`, etc. are Phase 4 scope.
- Do not trim the ported README's "hold_release moved to lighting" paragraph into something misleading — either drop it (it's about a prior move, not this one) or keep it verbatim; don't half-edit it.

</frozen-after-approval>

## Code Map

- `home-assistant/canbus/ha_arbitration_automations.yaml` -- `git mv` to `canbus/home-assistant/ha_arbitration_automations.yaml`
- `home-assistant/canbus/ha_manifest_package.yaml` -- `git mv` to `canbus/home-assistant/ha_manifest_package.yaml` (generated; will be rewritten byte-identical by the regeneration step anyway)
- `home-assistant/dashboards/` (whole tree, all subfiles) -- `git mv` to `hvac/home-assistant/dashboards/`
- `canbus/firmware/tools/generate_nodes.py:319,355,388,532` -- update `ha_path` construction and the three textual mentions (docstrings + print) to `repo_root / "canbus" / "home-assistant" / "ha_manifest_package.yaml"`
- `canbus/firmware/tools/check_registry_pushed.py:46` -- `GUARDED_PATHS` entry `"../../home-assistant/canbus/ha_manifest_package.yaml"` -- becomes `"../home-assistant/ha_manifest_package.yaml"` (one level up from `canbus/firmware/`, not two, since the target is now a sibling of `firmware/` inside `canbus/`)
- `home-assistant/canbus/README.md` -- content ports into new `canbus/home-assistant/README.md`
- `hvac/home-assistant/README.md` -- new file (no equivalent existed; dashboards only had usage docs, not a folder-purpose README)
- `canbus/CLAUDE.md:74-76` -- update the `home-assistant/canbus/` path reference
- `canbus/firmware/README.md:177,178,244` -- update the three path references
- `CLAUDE.md:163` (root) -- repo-structure tree's `home-assistant/` line goes stale once the directory is deleted; update to show `canbus/home-assistant/` and `hvac/home-assistant/dashboards/`
- `hvac/home-assistant/dashboards/{README.md,QUICK_START.md,API_INSTALLATION.md,INDEX.md}` -- ~28 lines of illustrative path examples (`cd`/`cp`/directory-tree diagrams) updated to the new path

## Tasks & Acceptance

**Execution:**
- [x] `git mv home-assistant/canbus/ha_arbitration_automations.yaml canbus/home-assistant/ha_arbitration_automations.yaml`
- [x] `git mv home-assistant/canbus/ha_manifest_package.yaml canbus/home-assistant/ha_manifest_package.yaml`
- [x] `git mv home-assistant/dashboards hvac/home-assistant/dashboards`
- [x] `canbus/firmware/tools/generate_nodes.py` -- fixed `ha_path` (line 388) and the three textual mentions (docstring, print, and the `write_exports` docstring's `repo_root` explanation) so the generator writes to `canbus/home-assistant/ha_manifest_package.yaml`
- [x] `canbus/firmware/tools/check_registry_pushed.py` -- fixed the `GUARDED_PATHS` entry to `../home-assistant/ha_manifest_package.yaml` (one level up, not two -- confirmed empirically: the gate correctly found the file at its new path when run)
- [x] `canbus/home-assistant/README.md` -- created by porting `home-assistant/canbus/README.md`'s content; dropped the "hold_release moved to lighting" paragraph (it was about the Phase 2 move, dead context in the renamed folder)
- [x] `hvac/home-assistant/README.md` -- created: short folder-purpose README
- [x] Deleted the now-empty top-level `home-assistant/` directory (via `git rm` on its last tracked file, which auto-removed the empty dirs)
- [x] `canbus/CLAUDE.md`, `canbus/firmware/README.md`, root `CLAUDE.md` -- updated path references per Code Map. `canbus/CLAUDE.md`'s `ha_*_automations.yaml` wildcard also had to become the specific `ha_arbitration_automations.yaml` filename as part of the same path-prefix edit, since the wildcard's other match (`ha_hold_automations.yaml`) left canbus's HA surface in Phase 2 -- a byproduct of the mechanical path fix, not a separately-found issue. Root `CLAUDE.md`'s tree diagram is pre-existing-stale beyond this phase's scope (doesn't show `canbus/`, `lighting/`, `hvac/` as top-level entries at all yet); added a note pointing to the real per-system locations instead of half-fixing the diagram -- full rewrite is Phase 6 scope.
- [x] `hvac/home-assistant/dashboards/{README.md,QUICK_START.md,API_INSTALLATION.md,INDEX.md}` -- updated all illustrative path examples, including two `cp -r` destination paths that needed manual follow-up beyond the bulk substitution (README.md:76,196)
- [x] Regenerated (`generate_nodes.py`) so `ha_manifest_package.yaml` lands at its new path -- byte-identical

**Acceptance Criteria:**
- Given the moves are committed, when `git status` is checked, then the top-level `home-assistant/` directory no longer exists, and `canbus/home-assistant/`, `hvac/home-assistant/dashboards/` exist with all content intact (100% similarity renames). -- confirmed.
- Given the standing verification battery, when run after this phase, then all commands exit 0, including `generate_nodes.py` writing `ha_manifest_package.yaml` to the new path and the idempotence check passing against it. -- confirmed.
- Given `check_registry_pushed.py`, when run after this phase, then it correctly reports on the manifest package at its new guarded path (no "file not found" mis-report from a stale guarded-path string). -- confirmed: gate correctly found `canbus/home-assistant/ha_manifest_package.yaml` as uncommitted (expected pre-commit state), proving the corrected relative path resolves.
- Given a fresh grep for `home-assistant/canbus`, when run after this phase, then it returns hits only in the frozen/historical docs left untouched per human decision, `MIGRATION-MAP.md`, this spec and Phase 2's spec (both describing the move itself), and one explanatory comment in `check_registry_pushed.py` describing the pre-move location. -- confirmed.
- Given a fresh grep for the old `home-assistant/dashboards` path in the four dashboard usage docs, when run after this phase, then it returns no hits. -- confirmed.

## Design Notes

`check_registry_pushed.py`'s guarded path needs *fewer* `../` segments after this move, not the same or more — a naive find-replace of the string `home-assistant/canbus` → `canbus/home-assistant` would silently produce a wrong relative path (`../../canbus/home-assistant/...`, which happens to still resolve correctly via repo root, but obscures the reasoning the file's own comment gives for its `../..`). Compute the correct depth explicitly rather than pattern-substituting.

## Verification

**Commands:**
- `git mv home-assistant/canbus/ha_arbitration_automations.yaml canbus/home-assistant/ha_arbitration_automations.yaml` -- expected: clean rename
- `git mv home-assistant/canbus/ha_manifest_package.yaml canbus/home-assistant/ha_manifest_package.yaml` -- expected: clean rename
- `git mv home-assistant/dashboards hvac/home-assistant/dashboards` -- expected: clean rename, whole tree intact
- `python3 canbus/firmware/tests/test_bindings.py` -- expected: pass
- `python3 canbus/firmware/tests/test_generate_exports.py` -- expected: pass
- `python3 canbus/firmware/tests/test_push_gate.py` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_ha_arbitration.cpp -o /tmp/arb && /tmp/arb` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_node_health.cpp -o /tmp/health && /tmp/health` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge` -- expected: pass
- `esphome compile canbus/firmware/tests/compile_sensor_node.yaml` -- expected: compiles
- `python3 canbus/firmware/tools/generate_nodes.py && git diff --exit-code -- registry canbus/firmware/protocol canbus/firmware/nodes canbus/home-assistant/ha_manifest_package.yaml` -- expected: zero diff (idempotence at the new path)
- `python3 canbus/firmware/tools/check_registry_pushed.py` -- expected: exit 0 once committed and pushed
- `grep -rn "home-assistant/canbus" --include="*.py" --include="*.md" --include="*.yaml" .` -- expected: hits only in `MIGRATION-MAP.md` and any frozen/historical docs left untouched per Ask First

**Manual checks (human, outside this repo):**
- Re-point the remaining Home Assistant package includes (arbitration automation, manifest package) from `home-assistant/canbus/` to `canbus/home-assistant/` on the live HA instance; confirm HA reloads without error. **Tracked in `deferred-work.md`**, merged into the same entry as the Phase 2 hold-automations re-point so both land in one HA-side session.

## Suggested Review Order

**The moves**

- Entry point: two clean renames out of the old canbus HA surface.
  [`ha_arbitration_automations.yaml`](../../canbus/home-assistant/ha_arbitration_automations.yaml#L1)
- The whole dashboards tree relocated intact — first content in the new `hvac/` system.
  [`hvac/home-assistant/dashboards/`](../../hvac/home-assistant/dashboards#L1)

**Path-depth fixes (the subtle part of this phase)**

- Manifest output path corrected to the new two-level nesting under `canbus/`.
  [`generate_nodes.py:389`](../../canbus/firmware/tools/generate_nodes.py#L389)
- Guarded path went from two `../` to one -- the target is now a sibling of `firmware/` inside `canbus/`, not a repo-root sibling. Verified empirically: the gate found the file correctly.
  [`check_registry_pushed.py:46`](../../canbus/firmware/tools/check_registry_pushed.py#L46)

**Ownership documentation**

- Ported from the deleted `home-assistant/canbus/README.md`; kept a breadcrumb pointing to lighting for hold-automation history (added back after review).
  [`canbus/home-assistant/README.md`](../../canbus/home-assistant/README.md#L1)
- New: `hvac/`'s first folder-purpose README.
  [`hvac/home-assistant/README.md`](../../hvac/home-assistant/README.md#L1)

**Peripheral doc updates**

- Root `CLAUDE.md`'s repo-structure tree note -- flags it as pre-existing-stale pending Phase 6 rather than half-fixing it.
  [`CLAUDE.md:97`](../../CLAUDE.md#L97)
- [`canbus/CLAUDE.md:74`](../../canbus/CLAUDE.md#L74)
- [`canbus/firmware/README.md:177`](../../canbus/firmware/README.md#L177)
- Illustrative path examples across the four dashboard usage docs.
  [`hvac/home-assistant/dashboards/README.md:76`](../../hvac/home-assistant/dashboards/README.md#L76)
