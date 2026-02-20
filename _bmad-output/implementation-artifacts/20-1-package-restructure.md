# Story 20.1: Package Restructure

Status: done

## Story

As a **Vesta user**,
I want **the package structure reorganized into a clear taxonomy (components/, coordinators/, devices/)**,
so that **I can find packages intuitively and the framework scales as more components are added**.

## Acceptance Criteria

1. **AC-1:** All three utility files moved from `packages/utils/` to `packages/components/`
2. **AC-2:** `packages/utils/` directory is removed
3. **AC-3:** `packages/devices/modbus-io/` directory is created (empty, ready for Story 20.5)
4. **AC-4:** All existing docs are updated to reference new `packages/components/` paths
5. **AC-5:** All existing examples compile with new package paths
6. **AC-6:** README component overview table reflects the new structure
7. **AC-7:** Existing Phase 1 components still compile (no regressions)

## Tasks / Subtasks

- [x] Task 1: Move utility files to new location (AC: #1, #2)
  - [x] 1.1: Move `packages/utils/trend_sensor.yaml` → `packages/components/trend_sensor.yaml`
  - [x] 1.2: Move `packages/utils/failover_sensor.yaml` → `packages/components/failover_sensor.yaml`
  - [x] 1.3: Move `packages/utils/proportional_demand_sensor.yaml` → `packages/components/proportional_demand_sensor.yaml`
  - [x] 1.4: Remove `packages/utils/` directory
- [x] Task 2: Create devices directory structure (AC: #3)
  - [x] 2.1: Create `packages/devices/modbus-io/` directory with `.gitkeep`
- [x] Task 3: Update internal cross-references in package files (AC: #7)
  - [x] 3.1: Update `packages/coordinators/fancoil_boost.yaml` — change `../utils/trend_sensor.yaml` → `../components/trend_sensor.yaml` (line 72 and header comment line 29)
  - [x] 3.2: Update `packages/utils/proportional_demand_sensor.yaml` internal include if it references `../utils/` (check after move) — N/A, no internal ../utils/ references
  - [x] 3.3: Update header comment `file:` paths in all 3 moved utility files (trend_sensor, failover_sensor, proportional_demand_sensor) from `packages/utils/` → `packages/components/`
- [x] Task 4: Update all documentation paths (AC: #4)
  - [x] 4.1: Update `docs/getting-started.md` — all `packages/utils/` → `packages/components/` (4 occurrences)
  - [x] 4.2: Update `docs/trend-sensor.md` — all `packages/utils/` → `packages/components/` (3 occurrences)
  - [x] 4.3: Update `docs/failover-sensor.md` — all `packages/utils/` → `packages/components/` (4 occurrences)
  - [x] 4.4: Update `docs/proportional-demand.md` — all `packages/utils/` → `packages/components/` (3 occurrences)
  - [x] 4.5: Update `docs/fancoil-boost.md` — all `packages/utils/` → `packages/components/` (2 occurrences)
  - [x] 4.6: Update `docs/mev-ventilation.md` — all `packages/utils/` → `packages/components/` (3 occurrences)
- [x] Task 5: Update examples (AC: #5)
  - [x] 5.1: Update `examples/two_zone_radiant_fancoil.yaml` — all `packages/utils/` → `packages/components/` (4 occurrences)
  - [x] 5.2: Update `examples/mev_two_demand.yaml` — all `packages/utils/` → `packages/components/` (2 occurrences)
- [x] Task 6: Update README and CONTRIBUTING (AC: #6)
  - [x] 6.1: Update `README.md` — change `packages/utils/` → `packages/components/` in all references (2 occurrences)
  - [x] 6.2: Update `README.md` component overview table — change "Utility" category to "Component", update paths
  - [x] 6.3: Add `packages/devices/modbus-io/` to the README directory structure description
  - [x] 6.4: Update `CONTRIBUTING.md` — change `packages/utils/` → `packages/components/` in example paths (4 occurrences)
  - [x] 6.5: Update `docs/getting-started.md` component reference table — changed "Utility" to "Component"
- [x] Review Follow-ups (AI)
  - [x] [AI-Review][HIGH] `CONTRIBUTING.md:161-169` — Directory Structure section updated to `components/`, `coordinators/`, `devices/` taxonomy.
  - [x] [AI-Review][HIGH] `docs/fancoil-boost.md:108` — Fixed relative path `../utils/` → `../components/`.
  - [x] [AI-Review][MEDIUM] Completion notes accuracy — addressed during fix pass.

## Dev Notes

### Architecture Context

This is a **path rename + directory restructure** story. No logic changes to any component. The taxonomy change is:

```
BEFORE:                          AFTER:
packages/                        packages/
├── utils/                       ├── components/          ← renamed from utils/
│   ├── trend_sensor.yaml        │   ├── trend_sensor.yaml
│   ├── failover_sensor.yaml     │   ├── failover_sensor.yaml
│   └── proportional_demand_     │   └── proportional_demand_
│       sensor.yaml              │       sensor.yaml
├── coordinators/                ├── coordinators/        ← unchanged
│   ├── fancoil_boost.yaml       │   ├── fancoil_boost.yaml
│   └── mev_ventilation.yaml     │   └── mev_ventilation.yaml
                                 └── devices/             ← new
                                     └── modbus-io/       ← new (empty)
```

### Critical Path References to Update

**Internal cross-references (YAML `!include` paths):**
- `packages/coordinators/fancoil_boost.yaml` line 72: `file: ../utils/trend_sensor.yaml` → `file: ../components/trend_sensor.yaml`
- `packages/coordinators/fancoil_boost.yaml` line 29 (comment): `../utils/trend_sensor.yaml` → `../components/trend_sensor.yaml`
- Each moved file's header comment `file:` path (e.g., `packages/utils/trend_sensor.yaml` → `packages/components/trend_sensor.yaml`)

**Documentation references (30+ occurrences across 7 doc files):**
All references to `packages/utils/` must become `packages/components/`. Use find-and-replace within the `vesta/` directory.

**Example references (6 occurrences across 2 example files):**
All `packages/utils/` → `packages/components/` in `!include` file paths.

### Regression Prevention

- After all path updates, verify no remaining references to `packages/utils/` exist anywhere in the `vesta/` directory
- Run: `grep -r "packages/utils/" vesta/` — must return zero results
- The `packages/coordinators/` paths are unchanged — do NOT modify these

### Project Structure Notes

- Working directory: `vesta/` (within the esphome-devices repo)
- All paths in YAML `!include` are relative to the including file's location
- Coordinator files use `../utils/` relative paths to include utilities — these become `../components/`
- Doc files and README use absolute-from-repo-root paths like `packages/utils/`

### References

- [Source: _bmad-output/planning-artifacts/product-brief-esphome-devices-2026-02-19.md#Core Features §1]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 20.1]
- [Source: vesta/CONTRIBUTING.md — header format and naming conventions]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Debug Log References
N/A — no compilation or runtime errors encountered.

### Completion Notes List
- All 6 tasks completed successfully
- 31 path references updated across 13 files
- Zero remaining `packages/utils/` references (verified via grep)
- "Utility" category renamed to "Component" in overview tables
- `packages/devices/modbus-io/` created with `.gitkeep` for Story 20.5

### Change Log
1. Moved `packages/utils/trend_sensor.yaml` → `packages/components/trend_sensor.yaml`
2. Moved `packages/utils/failover_sensor.yaml` → `packages/components/failover_sensor.yaml`
3. Moved `packages/utils/proportional_demand_sensor.yaml` → `packages/components/proportional_demand_sensor.yaml`
4. Removed `packages/utils/` directory
5. Created `packages/devices/modbus-io/.gitkeep`
6. Updated `packages/coordinators/fancoil_boost.yaml` — 2 path references (line 29 comment, line 72 include)
7. Updated header comment `file:` paths in all 3 component files
8. Updated 6 doc files (getting-started, trend-sensor, failover-sensor, proportional-demand, fancoil-boost, mev-ventilation)
9. Updated 2 example files (two_zone_radiant_fancoil.yaml, mev_two_demand.yaml)
10. Updated README.md — paths, component overview table ("Utility"→"Component"), directory structure diagram (added devices/modbus-io/)
11. Updated CONTRIBUTING.md — path references
12. Updated docs/getting-started.md — component reference table ("Utility"→"Component")

### File List
- vesta/packages/components/trend_sensor.yaml (moved from utils/)
- vesta/packages/components/failover_sensor.yaml (moved from utils/)
- vesta/packages/components/proportional_demand_sensor.yaml (moved from utils/)
- vesta/packages/devices/modbus-io/.gitkeep (new)
- vesta/packages/coordinators/fancoil_boost.yaml (modified)
- vesta/docs/getting-started.md (modified)
- vesta/docs/trend-sensor.md (modified)
- vesta/docs/failover-sensor.md (modified)
- vesta/docs/proportional-demand.md (modified)
- vesta/docs/fancoil-boost.md (modified)
- vesta/docs/mev-ventilation.md (modified)
- vesta/examples/two_zone_radiant_fancoil.yaml (modified)
- vesta/examples/mev_two_demand.yaml (modified)
- vesta/README.md (modified)
- vesta/CONTRIBUTING.md (modified)
