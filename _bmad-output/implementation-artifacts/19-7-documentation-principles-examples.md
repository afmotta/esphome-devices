# Story 19.7: Documentation, Principles & Examples

Status: review

## Story

As a **potential Vesta user discovering the project**,
I want **clear documentation of the architectural philosophy, a getting-started guide, and a complete working example**,
so that **I can understand how the components fit together and start using them in my own ESPHome installation**.

## Acceptance Criteria

1. **AC-1:** `docs/principles.md` documents all 9 principles with explanations
2. **AC-2:** `docs/getting-started.md` provides clear onboarding path
3. **AC-3:** `examples/two_zone_radiant_fancoil.yaml` is a complete, commented example
4. **AC-4:** README links to all component docs
5. **AC-5:** README includes component overview table

## Tasks / Subtasks

- [x] Task 1: Create `docs/principles.md` (AC: #1)
  - [x] 1.1: Document all 9 foundational principles from brainstorming session
  - [x] 1.2: Add practical explanations and examples for each
- [x] Task 2: Create `docs/getting-started.md` (AC: #2)
  - [x] 2.1: Prerequisites (ESPHome version, hardware)
  - [x] 2.2: How to include Vesta packages (local and GitHub remote)
  - [x] 2.3: Recommended starting point (trend sensor → build up)
  - [x] 2.4: Link to component docs
- [x] Task 3: Create `examples/two_zone_radiant_fancoil.yaml` (AC: #3)
  - [x] 3.1: Complete working example showing 2 zones
  - [x] 3.2: Radiant floor PID, fancoil, boost coordinator, trend sensor, failover sensor
  - [x] 3.3: Commented throughout
- [x] Task 4: Polish README (AC: #4, #5)
  - [x] 4.1: Verify component overview table
  - [x] 4.2: Verify all doc links work

## Dev Notes

### Source Documents

- Brainstorming session: `_bmad-output/analysis/brainstorming-session-2026-02-05.md`
- Epic brief: `_bmad-output/planning-artifacts/epic-19-brief.md` (Story 19.7 section)
- Existing docs in `vesta/docs/` for style reference

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No errors encountered.

### Completion Notes List

- Created `docs/principles.md` with all 9 foundational principles from brainstorming session, each with practical explanations
- Created `docs/getting-started.md` with prerequisites, local/GitHub include instructions, 4-step learning path, dependency map, component reference table
- Created `examples/two_zone_radiant_fancoil.yaml` with complete 2-zone setup: failover sensors, radiant PID, fancoil PID, boost coordinators, threshold sensors, override entities. Fully commented with summary of exposed entities and required HA helpers
- Polished README: added link to example in Documentation section, verified all doc links resolve to existing files
- Story completed: 2026-02-09

### Change Log

- 2026-02-09: Story 19.7 implemented - principles, getting-started, example, README polish

### File List

- `vesta/docs/principles.md` (new)
- `vesta/docs/getting-started.md` (new)
- `vesta/examples/two_zone_radiant_fancoil.yaml` (new)
- `vesta/README.md` (polish)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status update)
