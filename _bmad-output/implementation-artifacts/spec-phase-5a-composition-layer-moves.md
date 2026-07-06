---
title: 'Migration Phase 5a — Composition layer moves'
type: 'refactor'
created: '2026-07-06'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'c9953fec4d62465958829e986aa54c3943b92aef'
context: ['{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/MIGRATION-MAP.md', '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `gateway.yaml` and `bridge.yaml` -- hand-maintained deployable entry points -- currently live inside `canbus/firmware/`, and `locals/`/`remotes/` (deployment variants) sit at repo root, disconnected from the `devices/` entry points they deploy. AD-4 says entry points and their variants belong together in `devices/`.

**Approach:** Sub-split of the original Phase 5 (see spec-phase-5b for the deferred code-extraction half). Pure relocation: `git mv` gateway.yaml + its secrets files to `devices/gateway.yaml`, bridge.yaml to `devices/bridge.yaml`, and the whole `locals/`/`remotes/` directories under `devices/`. Fix every relative include this breaks (C++ header includes in gateway/bridge, `!include` package refs in the moved locals/ files) and every functionally load-bearing doc reference. No behavior change, no code splitting -- that's Phase 5b.

## Boundaries & Constraints

**Always:**
- One commit: moves and every consumer/doc update land together (AD-9).
- `remotes/climate-control.yaml`'s GitHub package fetch (`files: [devices/climate-control.yaml]`) does not change -- confirmed it targets `devices/climate-control.yaml`, which already existed at that path before any of this migration started and is untouched by this phase.
- Untracked `secrets.yaml` files (gateway, locals, remotes) are NOT under git control -- `git mv` won't relocate them. Note this as a manual step; do not attempt to script a filesystem move of gitignored files.
- Full verification battery plus `esphome compile` of gateway and bridge from their new `devices/` location.

**Ask First:**
- Whether to retire `canbus/firmware/gateway/.gitignore` (anchored `/.esphome/`, `/secrets.yaml`) now that root's unanchored `.gitignore` patterns already cover the new location (already noted independently by a prior architecture review) -- default: retire it, don't recreate an anchored one under `devices/` (which is now a shared directory for multiple entry points).
- Whether to update root `CLAUDE.md`'s operator-facing command examples (`esphome compile/run/logs/config locals/climate-control.yaml` -> `devices/locals/climate-control.yaml`) and its Important Files table -- these are literally-wrong instructions post-move, same category as Phase 4's "Adding a New Room" fix, but root `CLAUDE.md`'s full rewrite is nominally Phase 6 scope.

**Never:**
- Do not touch `canbus/packages/`, `lighting/packages/`, or write the bindings-arbitration contract spec -- that's Phase 5b.
- Do not fix `docs/deployment-guide.md`, `docs/rs485-wiring-guide.md`, `docs/modbus-register-map.md`, or `.ai/*.md` -- these already reference `locals/` filenames that don't exist today (pre-existing drift from an earlier rename, confirmed independent of this migration). Not this phase's fault, not this phase's job.
- Do not create a new anchored `.gitignore` under `devices/` unless the human says otherwise (see Ask First).

</frozen-after-approval>

## Code Map

- `canbus/firmware/gateway/gateway.yaml` -- `git mv` to `devices/gateway.yaml`; fix 5 header includes (`gateway.yaml:46-51`, currently `../protocol/*.h`) to `../canbus/firmware/protocol/*.h` (devices/ and canbus/ are repo-root siblings)
- `canbus/firmware/gateway/secrets.yaml.example` -- `git mv` to `devices/secrets.yaml.example`
- `canbus/firmware/gateway/.gitignore` -- retire (Ask First; root's unanchored patterns already cover `devices/secrets.yaml` and `devices/.esphome/`)
- `canbus/firmware/bridge/bridge.yaml` -- `git mv` to `devices/bridge.yaml`; fix 2 header includes (`bridge.yaml:58-60`, currently `../protocol/*.h`) to `../canbus/firmware/protocol/*.h`
- `locals/` (whole directory: `.gitignore`, `climate-control.yaml`, `room-sensor-soggiorno.yaml`, `wall-sensor.yaml`) -- `git mv` to `devices/locals/`; fix each file's one-line `!include "../devices/X.yaml"` to `!include "../X.yaml"` (one less `../` level -- the cited file is now a sibling of `locals/`, not two levels up)
- `remotes/climate-control.yaml` -- `git mv` to `devices/remotes/climate-control.yaml`; no content change (GitHub URL reference, confirmed unaffected)
- `canbus/firmware/README.md:88,91` -- update `secrets.yaml`/`secrets.yaml.example` location prose
- `canbus/docs/reflash-campaign-runbook.md:42` -- update the bridge USB-flash instruction path
- `.github/copilot-instructions.md:12,24,38,39` -- update `locals/secrets.yaml` references
- `CLAUDE.md` (root) -- repo-structure tree, operator command examples (`esphome compile/run/logs/config locals/climate-control.yaml` etc.), and the Important Files table's `locals/`/`remotes/` rows

## Tasks & Acceptance

**Execution:**
- [x] `git mv canbus/firmware/gateway/gateway.yaml devices/gateway.yaml`
- [x] `git mv canbus/firmware/gateway/secrets.yaml.example devices/secrets.yaml.example`
- [x] Fixed `devices/gateway.yaml`'s 5 header includes to `../canbus/firmware/protocol/*.h`; verified with a full `esphome compile devices/gateway.yaml` (SUCCESS)
- [x] `git mv canbus/firmware/bridge/bridge.yaml devices/bridge.yaml`; fixed its 2 header includes; verified with `esphome compile devices/bridge.yaml` (SUCCESS)
- [x] `git mv locals devices/locals`; fixed the 3 moved files' `!include` lines (one fewer `../` level each)
- [x] `git mv remotes devices/remotes`
- [x] Retired `canbus/firmware/gateway/.gitignore` (human confirmed: root's unanchored patterns already cover it)
- [x] Removed now-empty `canbus/firmware/bridge/`
- [x] Left `canbus/firmware/gateway/` in place with its untracked leftovers (`.esphome/` build cache, `secrets.yaml`) -- confirmed not a git concern
- [x] `canbus/firmware/README.md`, `canbus/docs/reflash-campaign-runbook.md`, `.github/copilot-instructions.md` -- updated path references
- [x] Root `CLAUDE.md` -- updated the repo-structure tree (devices/ now shows gateway.yaml, bridge.yaml, secrets.yaml.example, locals/, remotes/ as children), operator command examples, and Important Files table rows (human confirmed: fix now, not deferred to Phase 6)

**Acceptance Criteria:**
- Given the moves are committed, when `git status` is checked, then `canbus/firmware/gateway/gateway.yaml`, `canbus/firmware/gateway/secrets.yaml.example`, `canbus/firmware/bridge/bridge.yaml`, `locals/`, `remotes/` no longer exist at their old paths, and their `devices/`-rooted equivalents exist with all content intact. -- confirmed.
- Given the standing verification battery plus `esphome compile devices/gateway.yaml` and `esphome compile devices/bridge.yaml`, when run after this phase, then all commands exit 0. -- confirmed, both compiled SUCCESS.
- Given `esphome config devices/locals/climate-control.yaml` (the renamed path), when run after this phase, then it fails identically to the pre-Phase-1 baseline (pre-existing, unrelated missing-ID bugs), confirming the `!include` fix worked before hitting the known bug. -- confirmed.
- Given a fresh grep for `canbus/firmware/gateway/gateway.yaml`, `canbus/firmware/bridge/bridge.yaml`, and standalone `locals/`/`remotes/` path prefixes (not `devices/locals`, `devices/remotes`), when run after this phase, then it returns hits only in frozen/historical docs and the pre-existing-stale docs explicitly left alone per Never. -- confirmed.

## Design Notes

Depth arithmetic differs by direction: gateway/bridge move *out* of a nested `canbus/firmware/{gateway,bridge}/` into flat `devices/`, so their C++ includes need *more* path segments (`../canbus/firmware/protocol/*.h`, not fewer). `locals/`'s files move *into* a new `devices/locals/` nesting, so their `!include`s need *fewer* segments (`../X.yaml`, not `../devices/X.yaml`) -- the cited file becomes a direct sibling of the new `locals/` directory. Two different directions, easy to swap by mistake; verify each with `esphome compile`/`config`, not just by inspection (this repo's history of off-by-one `.parent` mistakes in Phase 1 makes this worth stating explicitly).

`canbus/firmware/gateway/` is left in place, non-empty on disk (untracked `.esphome/` build cache and a real `secrets.yaml`), once `gateway.yaml` moves out -- git has nothing left to track there, but the directory physically remains until Phase 6 flattens `canbus/firmware/` entirely. The stale `secrets.yaml` there is a duplicate of the live one now at `devices/secrets.yaml`; delete it manually once `devices/secrets.yaml` is confirmed working, so it can't be mistaken for the current copy.

## Verification

**Commands:**
- `git mv canbus/firmware/gateway/gateway.yaml devices/gateway.yaml` -- expected: clean rename
- `git mv canbus/firmware/gateway/secrets.yaml.example devices/secrets.yaml.example` -- expected: clean rename
- `git mv canbus/firmware/bridge/bridge.yaml devices/bridge.yaml` -- expected: clean rename
- `git mv locals devices/locals` -- expected: clean rename, whole tree intact
- `git mv remotes devices/remotes` -- expected: clean rename
- `esphome compile devices/gateway.yaml` -- expected: compiles
- `esphome compile devices/bridge.yaml` -- expected: compiles
- `esphome config devices/locals/climate-control.yaml` -- expected: fails identically to the pre-Phase-1 baseline (pre-existing, unrelated bug), no "file not found" on the `!include`
- `python3 canbus/firmware/tests/test_bindings.py` -- expected: pass
- `python3 canbus/firmware/tests/test_generate_exports.py` -- expected: pass
- `python3 canbus/firmware/tests/test_push_gate.py` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_ha_arbitration.cpp -o /tmp/arb && /tmp/arb` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_node_health.cpp -o /tmp/health && /tmp/health` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge` -- expected: pass
- `esphome compile canbus/firmware/tests/compile_sensor_node.yaml` -- expected: compiles
- `python3 canbus/firmware/tools/generate_nodes.py && git diff --exit-code -- registry canbus/firmware/protocol canbus/firmware/nodes canbus/home-assistant/ha_manifest_package.yaml` -- expected: zero diff (idempotence; unaffected by this phase)
- `python3 canbus/firmware/tools/check_registry_pushed.py` -- expected: exit 0 once committed and pushed
- `grep -rn "canbus/firmware/gateway/gateway.yaml\|canbus/firmware/bridge/bridge.yaml" .` -- expected: hits only in frozen/historical docs and MIGRATION-MAP.md

**Manual checks (human, outside git):**
- `devices/secrets.yaml` (gateway) needed a manual copy from the old `canbus/firmware/gateway/secrets.yaml` -- done during implementation, verified by a successful `esphome compile devices/gateway.yaml`. `git mv` only moved the single tracked `gateway.yaml` file, not the untracked sibling.
- `devices/locals/secrets.yaml` and `devices/remotes/secrets.yaml` needed **no manual action** -- `git mv locals devices/locals` and `git mv remotes devices/remotes` operate on whole directories at the OS level, so their untracked `secrets.yaml` siblings moved automatically along with the tracked files. Confirmed present post-move.
- Delete `canbus/firmware/gateway/secrets.yaml` (stale duplicate, untracked) once `devices/secrets.yaml` is confirmed working in practice -- not deleted automatically to avoid unilaterally removing a credentials file; see Design Notes.

**Note (review-driven fixes):** two review passes (Blind Hunter, Edge Case Hunter) found: a stray `devices/.gitignore` (traced to ESPHome CLI auto-generating one on first compile in a new directory, not a git artifact -- deleted); `devices/locals/.gitignore` retired for consistency with the gateway `.gitignore` retirement (root's unanchored patterns cover both, and `remotes/` never had one either -- now symmetric); `hvac/CLAUDE.md` and root `CLAUDE.md`'s unexplained `AD-4` jargon citations reworded in plain English; `deferred-work.md`'s Phase 5b entry now cross-references this spec by name. Two claims were independently re-verified rather than fixed: `remotes/climate-control.yaml`'s content has no local relative path beyond the GitHub fetch block (read in full, confirmed), and the `baseline_commit` hash is exactly 40 hex characters matching HEAD exactly (a reviewer miscounted).

## Suggested Review Order

**The moves**

- Entry point: gateway relocated, header includes re-pointed to `canbus/firmware/protocol/` across a repo-root sibling boundary.
  [`devices/gateway.yaml:46`](../../devices/gateway.yaml#L46)
- Same pattern, fewer includes.
  [`devices/bridge.yaml:58`](../../devices/bridge.yaml#L58)
- The opposite depth direction: locals/ moved *into* a new nesting, so its includes lost a segment rather than gaining one.
  [`devices/locals/climate-control.yaml:8`](../../devices/locals/climate-control.yaml#L8)
- Confirmed unaffected: GitHub package fetch, not a local path.
  [`devices/remotes/climate-control.yaml:9`](../../devices/remotes/climate-control.yaml#L9)

**`.gitignore` consistency (found and fixed during review)**

- Retired both `canbus/firmware/gateway/.gitignore` and `devices/locals/.gitignore` -- root's unanchored patterns already cover `secrets.yaml`/`.esphome/` at any depth, and `remotes/` never had one either. Now symmetric across all three.

**Peripheral doc updates**

- [`canbus/firmware/README.md:87`](../../canbus/firmware/README.md#L87)
- [`canbus/docs/reflash-campaign-runbook.md:42`](../../canbus/docs/reflash-campaign-runbook.md#L42)
- [`.github/copilot-instructions.md:12`](../../.github/copilot-instructions.md#L12)
- Root `CLAUDE.md`'s tree, operator commands, and Important Files table -- also dropped an unexplained `AD-4` citation found during review.
  [`CLAUDE.md:162`](../../CLAUDE.md#L162)
