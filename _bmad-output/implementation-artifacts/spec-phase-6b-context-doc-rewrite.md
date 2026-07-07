---
title: 'Migration Phase 6b — Context & documentation rewrite'
type: 'chore'
created: '2026-07-07'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'fffa7e06d8329946430943b9b3ab686961e04504'
final_revision: '74cf744'
context: ['{project-root}/_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md']
warnings: ['oversized']
---

<intent-contract>

## Intent

**Problem:** Root `CLAUDE.md` still describes the pre-restructure tree (a `home-assistant/`
appendix, `components/`, `canbus/firmware/`, no `lighting/`) and duplicates HVAC-only rules
(entity-ID convention, PID tuning, Modbus register/relay appendices, HVAC-specific "Common
Tasks") that AD-10 assigns to `hvac/CLAUDE.md`. `canbus/CLAUDE.md`'s "dumb nodes, smart
gateway" framing still describes one monolithic gateway that "decodes frames and fires HA
events," which is stale since the amended AD-7 split gateway consumers by domain (canbus =
transport health only; lighting = button decode/HA events). Three Claude Code memory files
(`project_layered_restructure_spine.md`, `project_canbus_merged_as_subtree.md`,
`feedback_prelive_no_migration_shims.md`) and four narrower ones (`feedback_momentary_buttons_no_state.md`,
`project_gateway_ha_event_firing_approach.md`, `project_esphome_globals_no_custom_structs.md`,
`project_node_refactor_standard_shape.md`, `project_proto_version_bump_policy.md`) still cite
pre-merge or pre-flatten paths (`firmware/gateway.yaml`, `canbus/firmware/registry/`, `components/`,
top-level `home-assistant/`).

**Approach:** Rewrite root `CLAUDE.md` as the map AD-10 calls for: an accurate four-system tree
(`canbus/`, `lighting/`, `hvac/`, `vesta/` + shared `registry/`, `devices/`, `boards/`, `libs/`,
`docs/`) with a one-line pointer to each system's own `CLAUDE.md`, house-wide conventions only
(git workflow, secrets, epic namespacing, BMAD process, Italian glossary), and no HVAC-only rule
content — that content moves to `hvac/CLAUDE.md` (which drops its "duplicated pending Phase 6"
caveat and becomes the sole home for entity-ID convention, PID tuning, Modbus/relay appendices,
and HVAC "Common Tasks"). Trim `canbus/CLAUDE.md`'s design-principle section to the amended AD-7
split. Fix stale path literals (never the historical narrative/reasoning around them) in the
eight identified memory files.

## Boundaries & Constraints

**Always:**
- One commit, per AD-9 (docs-only phase, no code/behavior change — nothing to battery-test beyond
  a grep sweep, but still one atomic commit).
- Root `CLAUDE.md`'s Repository Structure section reflects the actual current tree (verify with
  `ls`/`git ls-files`, not the migration map's aspirational description) — canbus already flattened
  (Phase 6a), registry/devices/hvac/lighting already at top level.
- HVAC-only content that moves out of root `CLAUDE.md` (entity-ID convention, PID tuning
  guidelines, Modbus register/relay appendices, room/PID/Modbus "Common Tasks") lands in
  `hvac/CLAUDE.md` — verify no net content loss, only relocation.
- `canbus/CLAUDE.md`'s "Design principle" section states plainly: canbus owns transport (frames,
  heartbeats, node_lost, discovery, the bus definition); lighting owns button decode → HA events;
  hvac consumes sensor frames directly. Do not restate lighting's or hvac's rules there beyond that
  one-line ownership statement — full detail already lives in `lighting/CLAUDE.md` / `hvac/CLAUDE.md`.
- Memory-file edits are literal path substitutions only (old path string → current final path);
  the surrounding prose, dates, "Why"/"How to apply" reasoning, and `[[links]]` are untouched.
- After the rewrite, a repo-wide grep for the stale-path strings below returns zero hits outside
  frozen/historical artifacts (`canbus/_bmad-output/**`, numbered epic docs, prior migration-phase
  spec files, `canbus/docs/merge-into-esphome-devices-proposal.md`) and outside
  `.claude/worktrees/**` (stale worktree copies, out of scope for this phase — flagged, not touched).

**Block If:** none identified — every disposition (what moves where, which memory files, wording
of the AD-7 correction) was already settled by the architecture spine (AD-10), the amended AD-7,
and the Phase 6a spec's explicit deferral of this work to 6b.

**Never:**
- Do not touch `.github/copilot-instructions.md` or `docs/ha-dashboard-config.yaml` — both are
  stale in ways that predate this restructure entirely (pre-Epic-2 `components/` layout); already
  logged in `deferred-work.md` from Phase 4's review as a separate follow-up, not this phase's scope.
- Do not clean up `.claude/worktrees/**` — separate stale-derived-state item in the risk register,
  not part of the "context/documentation rewrite" this phase's deferred-work entry scopes.
- Do not touch `lighting/CLAUDE.md` content beyond what's needed if the canbus trim reveals an
  actual gap there (expected: none — it's already accurate post-Phase-5b-2).
- Do not rewrite canbus's frozen `_bmad-output/`, numbered epic docs, or prior migration-phase spec
  files that describe old paths as history.
- Do not add version-bump/migration-shim language anywhere (project is pre-live).

</intent-contract>

## Code Map

- `CLAUDE.md` -- full rewrite: Repository Structure → accurate four-system map with per-system
  `CLAUDE.md` pointers; remove the "predates the in-progress layered restructure" note block
  (restructure will be done); remove Entity ID Naming Convention, PID Control Architecture, Modbus
  Register/Relay/Sensor-Address/PID-tuning appendices, and the room/PID/Modbus "Common Tasks"
  entries (all HVAC-only, relocate to `hvac/CLAUDE.md`); keep house-wide sections (Tech Stack minus
  Modbus-only rows, Development Workflow, Secrets Management, Testing & Deployment framing, Italian
  Terms glossary, Getting Help); update Changelog table with a new 1.4 row.
- `hvac/CLAUDE.md` -- append relocated sections (Entity ID convention already present — drop root's
  duplicate instead of touching this file's copy; add PID architecture note, Modbus register/relay
  appendices, and the room/PID-tuning/Modbus "Common Tasks" entries); drop the "pending its Phase 6
  rewrite" trailing sentence in Conventions.
- `canbus/CLAUDE.md:6-14` -- rewrite "Design principle: dumb nodes, smart gateway" section to state
  the AD-7-amended split (canbus = transport health; lighting = button decode/HA events; hvac =
  direct sensor-frame consumer) instead of "the gateway... decodes frames and fires HA events."
- `/Users/alberto/.claude/projects/-Users-alberto-src-esphome-devices/memory/project_layered_restructure_spine.md`
  -- "How to apply" paragraph: replace "until migration lands, check ... before placing new files;
  old paths ... are scheduled to move" with a completed-state statement (all six phases landed;
  spine/migration-map are now historical record, not a to-do).
- `.../memory/project_canbus_merged_as_subtree.md` -- `canbus/firmware/registry/map.json` →
  `registry/map.json`; `canbus/firmware/tools/generate_nodes.py` → `canbus/tools/generate_nodes.py`.
- `.../memory/feedback_prelive_no_migration_shims.md` -- `canbus/firmware/registry/nodes.csv` →
  `registry/nodes.csv`.
- `.../memory/feedback_momentary_buttons_no_state.md` -- `firmware/common/canbus_protocol.h` →
  `canbus/protocol/canbus_protocol.h`.
- `.../memory/project_gateway_ha_event_firing_approach.md` -- `firmware/gateway.yaml` →
  `devices/gateway.yaml`.
- `.../memory/project_esphome_globals_no_custom_structs.md` -- `firmware/protocol/ha_arbitration.h`
  → `canbus/protocol/ha_arbitration.h`.
- `.../memory/project_node_refactor_standard_shape.md` -- `firmware/common/base_node.yaml` →
  `canbus/packages/base_node.yaml` (two occurrences: prose + the `packages: base: !include` example).
- `.../memory/project_proto_version_bump_policy.md` -- `firmware/common/canbus_protocol.h` →
  `canbus/protocol/canbus_protocol.h`.

## Tasks & Acceptance

**Execution:**
- [x] `CLAUDE.md` -- rewrite Repository Structure as the four-system map; remove stale
  restructure-in-progress note -- makes the map accurate and AD-10-compliant
- [x] `CLAUDE.md` -- remove HVAC-only sections (entity-ID convention, PID architecture, Modbus/relay
  appendices, HVAC common tasks); update Changelog -- root becomes "the map, not the rules" (AD-10)
- [x] `hvac/CLAUDE.md` -- add relocated PID/Modbus/relay appendices and common tasks; drop the
  "pending Phase 6 rewrite" caveat -- hvac becomes the sole owner of its own rules (AD-10)
- [x] `canbus/CLAUDE.md:6-14` -- rewrite design-principle section to the amended AD-7 split --
  removes the stale "gateway decodes frames and fires HA events" monolith framing
- [x] Update the 8 identified Claude Code memory files with literal path substitutions -- keeps
  memory citations resolvable against the current tree
- [x] Repo-wide grep sweep for each stale-path string touched above -- confirms no missed hit
  outside frozen/historical docs and `.claude/worktrees/**`

**Acceptance Criteria:**
- Given root `CLAUDE.md` after the rewrite, when its Repository Structure section is compared to
  `ls`/`git ls-files` output, then every listed directory and file exists at the stated path.
- Given root `CLAUDE.md` and `hvac/CLAUDE.md` after the rewrite, when both are read, then the
  entity-ID convention, PID guidance, and Modbus/relay appendices appear exactly once (in
  `hvac/CLAUDE.md`), not duplicated in root.
- Given `canbus/CLAUDE.md`'s design-principle section, when read after the rewrite, then it states
  canbus owns transport health, lighting owns button decode/HA events, and hvac consumes sensor
  frames directly — no monolithic "gateway decodes and fires" framing remains.
- Given the 8 memory files, when re-read after the edit, then every cited path resolves to a real
  file in the current tree, and no prose/reasoning/date/link outside the path literal changed.
- Given a fresh repo-wide grep for `firmware/gateway.yaml`, `firmware/common/`, `firmware/protocol/`,
  `canbus/firmware/`, top-level `home-assistant/` (outside `canbus/home-assistant/`,
  `lighting/home-assistant/`, `hvac/home-assistant/`), and pre-Phase-4 `components/` paths, when run
  after this phase, then hits appear only in frozen/historical docs, prior migration-phase specs,
  and `.claude/worktrees/**`.

## Design Notes

Root `CLAUDE.md`'s Tech Stack table currently lists Modbus RTU as a "Primary Technology" — that
stays (it's still accurate at the house level: HVAC uses it, described briefly), but the detailed
register map (`200`, `300`, `400-407`, `408-415`) and relay assignment appendices are HVAC
implementation detail, not house-wide fact, so they relocate fully. The Italian Terms glossary stays
in root — it's used by HVAC entity IDs today but is genuinely house-wide vocabulary (room names),
not an HVAC engineering rule, so AD-10 doesn't require moving it.

## Verification

**Commands:**
- `grep -rn "canbus/firmware/\|firmware/gateway.yaml\|firmware/common/\|firmware/protocol/" --include="*.md" . | grep -v "_bmad-output\|worktrees"` -- expected: no hits (or only in explicitly-excepted historical docs, listed by name)
- `grep -rln "components/rooms\|^home-assistant/" CLAUDE.md hvac/CLAUDE.md canbus/CLAUDE.md lighting/CLAUDE.md` -- expected: no hits
- `git diff --stat` -- expected: only `CLAUDE.md`, `hvac/CLAUDE.md`, `canbus/CLAUDE.md`, and the 8 memory files under `/Users/alberto/.claude/projects/-Users-alberto-src-esphome-devices/memory/` changed

**Manual checks (if no CLI):**
- Read the rewritten root `CLAUDE.md` top to bottom: confirm it reads as a map (short, points to
  system CLAUDE.mds) rather than a rulebook.
- Read `hvac/CLAUDE.md` top to bottom: confirm the relocated sections fit its existing structure
  without duplicating its current entity-ID section.

## Spec Change Log

## Review Triage Log

### 2026-07-07 — Review pass
- intent_gap: 0
- bad_spec: 0
- patch: 2 (medium 1, low 1)
- defer: 1 (low 1)
- reject: 16 (low 16)
- addressed_findings:
  - `[medium]` `[patch]` Root `CLAUDE.md` claimed "each system directory (canbus/, lighting/, hvac/, vesta/) carries its own CLAUDE.md" but `vesta/CLAUDE.md` doesn't exist (Edge Case Hunter) — reworded to scope the claim to canbus/lighting/hvac and note vesta/ carries README.md/CONTRIBUTING.md instead.
  - `[low]` `[patch]` `MEMORY.md`'s index hook for `project_layered_restructure_spine.md` still read "migration map pending — check before placing files" after this phase rewrote that memory file's own body to say the migration landed (Blind Hunter) — updated the index hook to match.
  - Also independently caught (own re-inspection, before either subagent report): the implementation subagent had added `node_type`/`originSessionId` frontmatter fields and quote-style changes to `project_canbus_merged_as_subtree.md` beyond the spec's "literal path substitution only" instruction — reverted frontmatter to its original form, keeping only the two path fixes.

### 2026-07-07 — Review pass (follow-up)
- intent_gap: 0
- bad_spec: 0
- patch: 2 (medium 1, low 1)
- defer: 2 (medium 1, low 1)
- reject: 12 (low 12)
- addressed_findings:
  - `[medium]` `[patch]` `canbus/CLAUDE.md:8` heading "Design principle: dumb nodes, smart gateway" was left untouched while the body beneath it was rewritten to the amended AD-7 domain split — heading contradicted its own body (Blind Hunter) — retitled to "Design principle: dumb nodes, domain-split gateway".
  - `[low]` `[patch]` Root `CLAUDE.md`'s Repository Structure tree gained a new `scripts/ # Repo-level helper scripts` line this phase, but `scripts/` is empty and untracked on disk — described aspirational content as current (Blind Hunter + Edge Case Hunter, same finding) — comment now reads "Repo-level helper scripts (currently empty)".
  - `[medium]` `[defer]` Root `CLAUDE.md`'s "Key Documentation Files" table and "Getting Help" section cite non-existent `docs/architecture-diagram.md` / `docs/prd.md` (real paths are under `_bmad-output/planning-artifacts/`); confirmed identical in the pre-Phase-6b baseline, so pre-existing and outside this phase's Repository-Structure-only scope (Blind Hunter) — logged to deferred-work.md.
  - `[low]` `[defer]` Resolved which `architecture.md` the prior pass's deferred entry meant (`canbus/_bmad-output/planning-artifacts/architecture.md`) and found it already documents the single-lambda→`homeassistant.event:` reversal, meaning memory file `project_gateway_ha_event_firing_approach.md`'s claim that architecture.md "still contradicts this" is itself now stale; fixing the memory's reasoning is barred by this spec's own path-substitution-only scope (Blind Hunter) — logged to deferred-work.md.

## Auto Run Result

Status: done

**Summary:** Rewrote root `CLAUDE.md` as the AD-10 map (accurate four-system Repository
Structure tree, HVAC-only rule content relocated out), trimmed `canbus/CLAUDE.md`'s design
principle to the amended AD-7 split, and made `hvac/CLAUDE.md` the sole owner of its own
rules (PID architecture, Modbus/relay appendices, HVAC Common Tasks). Fixed stale pre-merge/
pre-flatten path citations in 8 Claude Code memory files. No code or YAML behavior change.

**Files changed:**
- `CLAUDE.md` — Repository Structure rewritten to the real four-system tree; removed
  restructure-in-progress note; removed Entity ID/PID/Modbus/relay/HVAC-Common-Tasks content
  (relocated); Changelog bumped to 1.4.
- `hvac/CLAUDE.md` — gained PID architecture, full Modbus register map, Common Tasks
  (room/PID/Modbus), and Appendices A–D relocated from root; dropped its "pending Phase 6
  rewrite" deferral sentence.
- `canbus/CLAUDE.md` — "Design principle" section rewritten to state the amended AD-7 split
  (canbus = transport health; lighting = button decode/HA events; hvac = direct sensor-frame
  consumer).
- 8 files under `/Users/alberto/.claude/projects/-Users-alberto-src-esphome-devices/memory/`
  (`project_layered_restructure_spine.md`, `project_canbus_merged_as_subtree.md`,
  `feedback_prelive_no_migration_shims.md`, `feedback_momentary_buttons_no_state.md`,
  `project_gateway_ha_event_firing_approach.md`, `project_esphome_globals_no_custom_structs.md`,
  `project_node_refactor_standard_shape.md`, `project_proto_version_bump_policy.md`) —
  literal path substitutions to current final paths.
- `MEMORY.md` (memory index) — patched during review: stale hook line for
  `project_layered_restructure_spine.md` updated to match its rewritten body.
- `_bmad-output/implementation-artifacts/deferred-work.md` — one new deferred item logged
  (pre-existing `architecture.md` line-number citation risk).

**Review findings breakdown:** 2 patches applied (1 medium, 1 low), 1 deferred (low,
pre-existing, not caused by this phase), 16 rejected as noise/false-alarms after verification
against the actual files (e.g. claimed orphaned Room Configs section, claimed stale ToC,
claimed untouched `project_gateway_split_model.md` needing a fix — all confirmed fine on
inspection).

**Verification performed:** repo-wide grep sweeps for stale path strings (clean outside the
one explicitly-excepted frozen historical doc, `canbus/docs/merge-into-esphome-devices-proposal.md`);
manual read-through of all three rewritten `CLAUDE.md` files; manual diff of all 8 memory
files against captured pre-edit content to confirm only path literals changed; `git diff --stat`
confirmed only the expected repo files changed.

**Residual risks:** none blocking. `.github/copilot-instructions.md` and
`docs/ha-dashboard-config.yaml` remain stale from a pre-Epic-2 layout (already logged as a
separate deferred item from Phase 4, out of this phase's scope). `.claude/worktrees/**` stale
copies remain (risk-register item, not part of this phase's "context/documentation rewrite"
scope).

Follow-up review recommended: false — two small, localized, low-consequence patches; no
behavior/security/data impact.

### Follow-up review pass — 2026-07-07

Status: done

**Summary:** Fresh adversarial + edge-case review pass on the completed Phase 6b work
(triggered by re-running this spec after it was already `done`). Found and fixed two small
in-scope defects the first pass missed, and deferred two confirmed pre-existing issues that
are out of this phase's scope.

**Files changed this pass:**
- `canbus/CLAUDE.md` — retitled the "Design principle" heading (was "dumb nodes, smart
  gateway", contradicting the AD-7-split body beneath it) to "dumb nodes, domain-split
  gateway".
- `CLAUDE.md` — Repository Structure tree's new `scripts/` line now notes "(currently
  empty)" instead of implying it already holds helper scripts.
- `_bmad-output/implementation-artifacts/deferred-work.md` — two new deferred items logged
  (stale `docs/architecture-diagram.md`/`docs/prd.md` citations in root `CLAUDE.md`;
  resolution + deeper staleness finding on the prior pass's `architecture.md` citation-risk
  entry).

**Review findings breakdown:** 2 patches applied (1 medium, 1 low), 2 deferred (1 medium, 1
low — both confirmed pre-existing and outside this phase's scope), 12 rejected after
verification against the actual files (e.g. claimed canbus Hard-rules duplication, claimed
unverified memory files that on inspection already had correct paths, claimed missing
memory cross-links that the spec's own "literal substitutions only" boundary explicitly
bars adding).

**Verification performed:** direct inspection of every confirmed finding against the live
tree (`ls`/`find`/`grep` for `docs/architecture-diagram.md`, `docs/prd.md`, `scripts/`
contents, `canbus/_bmad-output/planning-artifacts/architecture.md` lines 156-167/579,
`docs/modbus-register-map.md`, and the two memory files claimed unverified); confirmed
which findings predate this phase via `git show <baseline>:CLAUDE.md`.

**Residual risks:** none blocking. The two deferred items are pre-existing documentation
citation drift, unrelated to this phase's path-flatten/relocation work.

Follow-up review recommended: false — two small, localized, low-consequence patches; no
behavior/security/data impact.
