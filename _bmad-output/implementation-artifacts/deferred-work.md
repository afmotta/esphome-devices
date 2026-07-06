- source_spec: none
  summary: Phase 3 — HA split completes (move arbitration automations + manifest package to canbus/home-assistant/, dashboards to hvac/home-assistant/, retire top-level home-assistant/)
  evidence: Split from MIGRATION-MAP.md multi-phase restructure; user chose one-phase-at-a-time on 2026-07-05

- source_spec: none
  summary: Phase 4 — HVAC gathering (move components/rooms and components/*.yaml into hvac/, update all !include paths and the spec-map-json-contract room_slug glob)
  evidence: Split from MIGRATION-MAP.md multi-phase restructure; user chose one-phase-at-a-time on 2026-07-05

- source_spec: none
  summary: Phase 5 — composition layer (move gateway.yaml/bridge.yaml into devices/, extract gateway monolith into canbus/packages/ and lighting/packages/, write bindings-arbitration contract spec)
  evidence: Split from MIGRATION-MAP.md multi-phase restructure; user chose one-phase-at-a-time on 2026-07-05

- source_spec: none
  summary: Phase 6 — flatten canbus (move protocol/packages/nodes/tools/tests up out of firmware/, rewrite root CLAUDE.md as system map, trim canbus/CLAUDE.md)
  evidence: Split from MIGRATION-MAP.md multi-phase restructure; user chose one-phase-at-a-time on 2026-07-05

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-1-registry-elevation.md`
  summary: allocate_node.py and commission.py have no automated test coverage at all (no test_allocate_node.py / test_commission.py exist)
  evidence: Surfaced by Blind Hunter review of Phase 1 — pre-existing gap, not introduced by the registry move, but their corrected path depth is currently verified only by manual/visual inspection

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-1-registry-elevation.md`
  summary: review-reality-check.md (added to git in the same commit as the Phase 1 move) documents pre-move state as if historical, but it is new content shipped already-stale by its own companion changes — worth a follow-up note or re-dating rather than treating it as frozen history
  evidence: Surfaced by Blind Hunter review of Phase 1; the file predates being tracked in git but not the repo's actual history, so the "frozen historical record" exception doesn't cleanly apply to it

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-2-lighting-is-born.md`
  summary: canbus/_bmad-output/implementation-artifacts/deferred-work.md:40 (frozen historical artifact) still calls ha_hold_automations.yaml "the template" without noting it moved to lighting/home-assistant/ — whoever picks up ADR-0012 open item 2 will look in the old canbus location and find nothing
  evidence: Surfaced by Edge Case Hunter review of Phase 2; left untouched by default since canbus/_bmad-output/ is frozen per AD-1, same policy applied to ADR-0012 and the merge-proposal doc this phase also left alone

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-2-lighting-is-born.md`
  summary: manual step "re-point the HA package include for hold automations on the live Home Assistant instance" needs a durable tracking home beyond the spec file, since the spec flips to done once merged and the reminder could get lost
  evidence: Surfaced by Blind Hunter review of Phase 2; this repo has no visibility into the live HA config, so nothing in-repo can confirm the human actually did this step
