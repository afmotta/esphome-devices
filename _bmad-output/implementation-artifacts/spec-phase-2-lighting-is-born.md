---
title: 'Migration Phase 2 — Lighting is born'
type: 'refactor'
created: '2026-07-06'
status: 'done'
review_loop_iteration: 0
baseline_commit: '1b0715cb61dbf8bcb37e072281677cbf0aeda496'
context: ['{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/MIGRATION-MAP.md', '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `home-assistant/canbus/ha_hold_automations.yaml` (hold/hold_release dimmer & cover automations, ADR-0012) currently lives under the canbus HA-import surface, but its content is lighting semantics, not canbus infra — AD-5 says HA artifacts live with their owning system, and `lighting/` doesn't exist yet as a named system (AD-1).

**Approach:** Create `lighting/`, `git mv` the hold-automations file into `lighting/home-assistant/`, and write `lighting/CLAUDE.md` establishing the system (owns `registry/bindings.yaml` schema + fallback semantics per ADR-0013 lineage, never touches canonicalization/hash per AD-7, epic prefix **LIGHT-**). Update the doc references left behind and flag the one manual, out-of-repo step (re-pointing the HA package include) for the human — this repo has no HA config to edit; that step happens on the live Home Assistant instance.

## Boundaries & Constraints

**Always:**
- One commit: the move and every in-repo consumer/doc update land together (AD-9).
- `home-assistant/canbus/ha_arbitration_automations.yaml` and `home-assistant/canbus/ha_manifest_package.yaml` stay put — Phase 3 moves those, not this phase.
- Full verification battery from MIGRATION-MAP.md must be green after this phase.

**Ask First:**
- Whether to also update `canbus/_bmad-output/planning-artifacts/adrs/0012-hold-release-button-gestures-continuous-control.md` (frozen historical ADR, already stale at an even older path `firmware/gateway/ha_hold_automations.yaml`) and `canbus/docs/merge-into-esphome-devices-proposal.md` (historical merge-proposal doc) — default is to leave both untouched per the frozen-history convention, but flag explicitly since Phase 1 set a precedent of sweeping frozen artifacts on request.
- The human must perform the actual HA package re-point on their live Home Assistant instance after this commit lands — nothing in this repo can do that for them.

**Never:**
- Do not touch `home-assistant/canbus/ha_arbitration_automations.yaml` or `ha_manifest_package.yaml` (Phase 3 scope).
- Do not write any lighting fallback/relay package code — ADR-0013's actual fallback implementation is explicitly deferred to Phase 5.

</frozen-after-approval>

## Code Map

- `home-assistant/canbus/ha_hold_automations.yaml` -- `git mv` to `lighting/home-assistant/ha_hold_automations.yaml`
- `lighting/CLAUDE.md` -- new file: system charter (owns `registry/bindings.yaml` schema + fallback semantics, ADR-0013 lineage; never touches canonicalization/hash, AD-7; epic prefix **LIGHT-**)
- `home-assistant/canbus/README.md` -- remove the `ha_hold_automations.yaml` entry (file moved out); note its new home
- `canbus/firmware/README.md:146,155,177,178` -- update the four `home-assistant/canbus/ha_hold_automations.yaml` references to `lighting/home-assistant/ha_hold_automations.yaml`
- `canbus/_bmad-output/planning-artifacts/adrs/0012-hold-release-button-gestures-continuous-control.md` -- frozen ADR, already stale at an older path; leave untouched unless human says otherwise (Ask First)
- `canbus/docs/merge-into-esphome-devices-proposal.md` -- historical proposal doc; leave untouched unless human says otherwise (Ask First)

## Tasks & Acceptance

**Execution:**
- [x] `git mv home-assistant/canbus/ha_hold_automations.yaml lighting/home-assistant/ha_hold_automations.yaml` -- create the directory implicitly via the move
- [x] `lighting/CLAUDE.md` -- create, following the same shape as `canbus/CLAUDE.md`/root `CLAUDE.md`: design principle, hard rules (owns bindings.yaml schema + fallback semantics; never touches canonicalization/hash), epic prefix **LIGHT-**
- [x] `home-assistant/canbus/README.md` -- drop the moved file's entry, add a one-line pointer to its new location
- [x] `canbus/firmware/README.md` -- update the 2 references to `ha_hold_automations.yaml` (lines 146, 155). Correction from Code Map: the other 2 grep hits originally counted (177-178) reference `ha_manifest_package.yaml`/`ha_arbitration_automations.yaml`, which stay in `home-assistant/canbus/` untouched by this phase -- not part of this task.
- [x] Confirmed no in-repo YAML actually `!include`s the old path (verified during investigation: none does — it's a copy-into-HA template, not a live include) so no ESPHome/YAML config needed editing beyond the doc references above

**Acceptance Criteria:**
- Given the move is committed, when `git status` is checked, then `home-assistant/canbus/` no longer contains `ha_hold_automations.yaml` and `lighting/home-assistant/ha_hold_automations.yaml` exists with identical content (100% similarity rename). -- confirmed.
- Given the standing verification battery, when run after this phase, then all commands exit 0 (this phase touches no Python/C++/ESPHome logic, so behavior is unaffected). -- confirmed; push gate reports only "unpushed to remote", same pre-existing environment condition as Phase 1, not a regression.
- Given a fresh grep for `home-assistant/canbus/ha_hold_automations`, when run after this phase, then it returns no hits outside the two Ask-First-flagged frozen/historical docs (left untouched per human decision) and `MIGRATION-MAP.md`. -- confirmed.

## Design Notes

`lighting/CLAUDE.md` is the first artifact for a system that otherwise has no code yet (ADR-0013's actual fallback/relay packages land in Phase 5) — it exists to stake out the system's home and rules ahead of the code, per AD-1/AD-10 ("each system directory carries its own CLAUDE.md").

## Verification

**Commands:**
- `git mv home-assistant/canbus/ha_hold_automations.yaml lighting/home-assistant/ha_hold_automations.yaml` -- expected: clean rename
- `python3 canbus/firmware/tests/test_bindings.py` -- expected: pass
- `python3 canbus/firmware/tests/test_generate_exports.py` -- expected: pass
- `python3 canbus/firmware/tests/test_push_gate.py` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_protocol.cpp -o /tmp/proto && /tmp/proto` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_ha_arbitration.cpp -o /tmp/arb && /tmp/arb` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_node_health.cpp -o /tmp/health && /tmp/health` -- expected: pass
- `g++ -std=c++17 -Wall -Wextra canbus/firmware/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge` -- expected: pass
- `esphome compile canbus/firmware/tests/compile_sensor_node.yaml` -- expected: compiles
- `python3 canbus/firmware/tools/generate_nodes.py && git diff --exit-code -- registry canbus/firmware/protocol canbus/firmware/nodes home-assistant` -- expected: zero diff (idempotence; unaffected by this phase)
- `python3 canbus/firmware/tools/check_registry_pushed.py` -- expected: exit 0 once committed and pushed
- `grep -rn "home-assistant/canbus/ha_hold_automations" --include="*.py" --include="*.md" --include="*.yaml" .` -- expected: hits only in `MIGRATION-MAP.md` and the two Ask-First-flagged historical docs (if left untouched)

**Manual checks (human, outside this repo):**
- Re-point the Home Assistant package include for hold automations from the old `home-assistant/canbus/ha_hold_automations.yaml` path to the new `lighting/home-assistant/ha_hold_automations.yaml` path on the live HA instance, then confirm HA reloads the package without error. **Tracked in `deferred-work.md`** so this doesn't get lost once this spec flips to done.

## Suggested Review Order

**The move and its new charter**

- Entry point: the file move itself — 100% similarity rename, no content change.
  [`ha_hold_automations.yaml`](../../lighting/home-assistant/ha_hold_automations.yaml#L1)
- New system charter: establishes lighting's ownership boundary (bindings.yaml schema, fallback semantics) against canbus's (canonicalization, the gate) per AD-7.
  [`lighting/CLAUDE.md:1`](../../lighting/CLAUDE.md#L1)

**Doc references left behind**

- Drops the moved file's entry from the old directory listing; points to the new home without leaning on internal phase/AD jargon.
  [`home-assistant/canbus/README.md:1`](../../home-assistant/canbus/README.md#L1)
- Updates the two literal old-path mentions in canbus's own operational doc; the two other similar-looking hits (ha_manifest_package.yaml, ha_arbitration_automations.yaml) correctly stay put.
  [`canbus/firmware/README.md:146`](../../canbus/firmware/README.md#L146)

**Peripheral**

- Superseded queue entry removed now that this phase is done.
  [`deferred-work.md:1`](deferred-work.md#L1)
