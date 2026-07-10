- source_spec: none
  summary: Phase 6b — context rewrite (root CLAUDE.md rewritten as the four-system map, canbus/CLAUDE.md trimmed to infra-only, Claude memory files updated to final paths)
  evidence: Split from Phase 6 during scope routing on 2026-07-07 — the phase's own name has a "+" joining two different kinds of work; 6a (mechanical flatten) is battery-testable, 6b is judgment-call documentation authoring reviewed once final paths exist, per user's explicit choice

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-6b-context-doc-rewrite.md`
  summary: memory file `project_gateway_ha_event_firing_approach.md` cites `architecture.md (lines 153-162, 416, 579)` for the single-lambda-vs-YAML-action decision reversal; those line numbers were never verified against the current `architecture.md` and may have drifted independent of this restructure (architecture.md itself is a planning doc outside this phase's path-flatten scope)
  evidence: Surfaced by Blind Hunter review of Phase 6b; pre-existing citation-rot risk, not caused by this phase's path substitutions, but worth a follow-up check next time that memory file or architecture.md is touched

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-6b-context-doc-rewrite.md`
  summary: resolves which `architecture.md` the prior deferred entry (above) meant and finds the deeper issue: `canbus/_bmad-output/planning-artifacts/architecture.md` is the correct file (its lines ~156-167 and ~579 discuss the `homeassistant.event:` vs single-lambda decision), and it **already documents the reversal** ("Global staging: eliminated... An earlier design mandated a single-lambda direct internal-API call... that was reversed on 2026-06-02"). This means memory file `project_gateway_ha_event_firing_approach.md`'s claim that "architecture.md still contradicts this and should be updated... until then, the firmware is the source of truth" is itself now stale — architecture.md was already reconciled. Fixing the memory file's reasoning is out of this spec's scope (its intent-contract bars touching memory-file prose/reasoning, path substitutions only).
  evidence: Direct inspection of `canbus/_bmad-output/planning-artifacts/architecture.md` lines 156-167 and 579 during this review pass's verification of the prior deferred entry

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-6a-flatten-canbus.md`
  summary: canbus/packages/base_node.yaml and canbus/packages/health.yaml both declare `id: can0` for their respective CAN bus components (mcp2515 vs esp32_can) — a latent id collision if any future entry point ever composes both packages together. Confirmed no current entry point does (base_node.yaml: generated node YAMLs + compile_sensor_node.yaml only; health.yaml: devices/gateway.yaml only). Documented with a cross-reference comment in both files; renaming was out of scope for a mechanical flatten phase (base_node.yaml affects every generated node across the fleet)
  evidence: Surfaced by both Blind Hunter and Edge Case Hunter review of Phase 6a — pre-existing naming coincidence, made adjacency-visible (not caused) by merging the two packages into one directory this phase

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-1-registry-elevation.md`
  summary: allocate_node.py and commission.py have no automated test coverage at all (no test_allocate_node.py / test_commission.py exist)
  evidence: Surfaced by Blind Hunter review of Phase 1 — pre-existing gap, not introduced by the registry move, but their corrected path depth is currently verified only by manual/visual inspection

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-1-registry-elevation.md`
  summary: review-reality-check.md (added to git in the same commit as the Phase 1 move) documents pre-move state as if historical, but it is new content shipped already-stale by its own companion changes — worth a follow-up note or re-dating rather than treating it as frozen history
  evidence: Surfaced by Blind Hunter review of Phase 1; the file predates being tracked in git but not the repo's actual history, so the "frozen historical record" exception doesn't cleanly apply to it

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-2-lighting-is-born.md`
  summary: canbus/_bmad-output/implementation-artifacts/deferred-work.md:40 (frozen historical artifact) still calls ha_hold_automations.yaml "the template" without noting it moved to lighting/home-assistant/ — whoever picks up ADR-0012 open item 2 will look in the old canbus location and find nothing
  evidence: Surfaced by Edge Case Hunter review of Phase 2; left untouched by default since canbus/_bmad-output/ is frozen per AD-1, same policy applied to ADR-0012 and the merge-proposal doc this phase also left alone

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-2-lighting-is-born.md`, `_bmad-output/implementation-artifacts/spec-phase-3-ha-split-completes.md`
  summary: two manual HA-side package re-point steps need doing on the live Home Assistant instance once convenient — (1) hold/hold_release automations moved to lighting/home-assistant/ (Phase 2), (2) arbitration automation + manifest package moved to canbus/home-assistant/ (Phase 3). Bundle into one HA session; confirm HA reloads both packages without error.
  evidence: Surfaced by Blind Hunter review of Phase 2 and Phase 3; this repo has no visibility into the live HA config, so nothing in-repo can confirm the human actually did these steps

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-4-hvac-gathering.md`
  summary: architectural invariants stated as prose in system CLAUDE.mds (e.g. hvac/CLAUDE.md's "hvac only reads registry/map.json, never writes it") have no mechanical enforcement (grep/lint/test) — matches this project's own documented pattern of status-hygiene drift needing a tooling gate, not another action item
  evidence: Surfaced by Blind Hunter review of Phase 4; fixing this needs a real check wired into the push gate or CI, out of scope for a docs/path-relocation phase

