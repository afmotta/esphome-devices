- source_spec: none
  summary: Phase 2 — lighting is born (move ha_hold_automations.yaml into new lighting/ system, write lighting/CLAUDE.md)
  evidence: Split from MIGRATION-MAP.md multi-phase restructure; user chose one-phase-at-a-time on 2026-07-05

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
