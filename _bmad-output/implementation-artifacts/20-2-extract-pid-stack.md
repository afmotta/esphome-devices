# Story 20.2: Extract PID Stack

Status: done

## Story

As a **multi-zone HVAC integrator using ESPHome**,
I want **production-tested PID controller wrappers with presets for radiant and fancoil systems**,
so that **I can set up proportional zone control with proven defaults instead of tuning from scratch**.

## Acceptance Criteria

1. **AC-1:** `pid.yaml` extracted to `packages/components/` with full Vesta header comment block
2. **AC-2:** `pid_sensors.yaml` extracted to `packages/components/` with full header
3. **AC-3:** `pid_autotune.yaml` extracted to `packages/components/` with full header
4. **AC-4:** `pid_autotune_with_fancoil.yaml` extracted to `packages/components/` with full header
5. **AC-5:** `radiant.yaml` extracted to `packages/components/` with full header
6. **AC-6:** `fancoil.yaml` extracted to `packages/components/` with full header
7. **AC-7:** Each component compiles standalone with only its declared parameters (no external entity references)
8. **AC-8:** No component references esphome-devices-specific entities (Italian room names, hardcoded hardware IDs)
9. **AC-9:** Dependency chains are documented in headers (e.g., pid → pid_sensors, radiant → pid, fancoil → pid)
10. **AC-10:** All parameters have header comment blocks with purpose, required vars, optional vars, and example
11. **AC-11:** The Epic 19 extraction pattern is followed (header format per CONTRIBUTING.md)

## Tasks / Subtasks

- [x] Task 1: Extract `pid.yaml` (AC: #1, #7, #8, #10, #11)
  - [x] 1.1: Create `vesta/packages/components/pid.yaml` with full Vesta header comment block
  - [x] 1.2: Copy logic from `components/pid.yaml` — preserve all substitution variables
  - [x] 1.3: Update `!include` path for pid_sensors dependency (`./pid_sensors.yaml` → `pid_sensors.yaml`)
  - [x] 1.4: Verify no esphome-devices-specific references remain
- [x] Task 2: Extract `pid_sensors.yaml` (AC: #2, #7, #8, #10, #11)
  - [x] 2.1: Create `vesta/packages/components/pid_sensors.yaml` with full Vesta header
  - [x] 2.2: Copy logic from `components/pid_sensors.yaml` — preserve all 10 sensors + 3 binary sensors
  - [x] 2.3: Verify no esphome-devices-specific references remain
- [x] Task 3: Extract `pid_autotune.yaml` (AC: #3, #7, #8, #10, #11)
  - [x] 3.1: Create `vesta/packages/components/pid_autotune.yaml` with full Vesta header (source already has partial header — expand to full format)
  - [x] 3.2: Copy logic from `components/pid_autotune.yaml`
  - [x] 3.3: Verify no esphome-devices-specific references remain
- [x] Task 4: Extract `pid_autotune_with_fancoil.yaml` (AC: #4, #7, #8, #10, #11)
  - [x] 4.1: Create `vesta/packages/components/pid_autotune_with_fancoil.yaml` with full Vesta header
  - [x] 4.2: Copy logic from `components/pid_autotune_with_fancoil.yaml`
  - [x] 4.3: Generalize `${room_slug}_boost_active` reference — documented as required var `boost_active_global`
  - [x] 4.4: Verify no esphome-devices-specific references remain
- [x] Task 5: Extract `radiant.yaml` (AC: #5, #7, #8, #9, #10, #11)
  - [x] 5.1: Create `vesta/packages/components/radiant.yaml` with full Vesta header (dual heat+cool radiant)
  - [x] 5.2: Kept layered architecture: `radiant.yaml` includes `heat_only_radiant.yaml` which includes `pid.yaml`
  - [x] 5.3: Create `vesta/packages/components/heat_only_radiant.yaml` with full Vesta header (prerequisite for radiant.yaml)
  - [x] 5.4: Parameterized `hp_mode` → `${seasonal_mode_id}` as required var
  - [x] 5.5: Update `!include` paths for Vesta directory structure
  - [x] 5.6: Document dependency chain in header: radiant → heat_only_radiant → pid → pid_sensors
- [x] Task 6: Extract `fancoil.yaml` (AC: #6, #7, #8, #9, #10, #11)
  - [x] 6.1: Create `vesta/packages/components/fancoil.yaml` with full Vesta header
  - [x] 6.2: Make PID gains parameterizable with defaults matching production values (kp: 0.2, ki: 0.01, kd: 0.05)
  - [x] 6.3: Parameterized `hp_mode` → `${seasonal_mode_id}` as required var
  - [x] 6.4: Update `!include` path for pid.yaml dependency
  - [x] 6.5: Document dependency chain in header: fancoil → pid → pid_sensors
- [x] Task 7: Cross-component validation (AC: #7, #8, #9)
  - [x] 7.1: Zero esphome-devices-specific references (Italian names, hardcoded IDs) — verified via grep
  - [x] 7.2: All `!include` paths correct (same-directory filenames)
  - [x] 7.3: All dependency chains documented in headers

## Dev Notes

### Architecture Context

This story extracts the **PID zone control stack** — the core building blocks that every zone in the climate system uses. The dependency chain is:

```
pid_sensors.yaml           ← standalone, no dependencies
pid.yaml                   ← includes pid_sensors.yaml
pid_autotune.yaml          ← standalone (references pid_id at runtime)
pid_autotune_with_fancoil.yaml ← standalone (references pid_id + boost global at runtime)
heat_only_radiant.yaml     ← includes pid.yaml (heat-only zones)
radiant.yaml               ← includes heat_only_radiant.yaml (adds cool output + dual-mode)
fancoil.yaml               ← includes pid.yaml (fast-response cooling)
```

### Source File Analysis

**Files that need NO generalization (already fully parameterized):**
- `components/pid.yaml` (28 lines) — uses `${circuit_slug}`, `${circuit_name}`, `${sensor}`, `${kp/ki/kd}`
- `components/pid_sensors.yaml` (70 lines) — uses only `${pid_id}`, `${pid_name}`
- `components/pid_autotune.yaml` (28 lines) — uses `${pid_name}`, `${pid_id}`, already has partial header

**Files that need generalization:**
- `components/pid_autotune_with_fancoil.yaml` (39 lines) — references `${room_slug}_boost_active` which assumes a specific global naming pattern from the boost coordinator. Must be parameterized as a declared var.
- `components/radiant.yaml` (24 lines) — extends `hp_mode` global select (hardcoded ID). Must parameterize to `${seasonal_mode_id}`.
- `components/fancoil.yaml` (31 lines) — extends `hp_mode` global select + has hardcoded PID gains. Must parameterize both.
- `components/heat_only_radiant.yaml` (91 lines) — extends `hp_mode`, references `${relay_id}` and `slow_pwm_${room_slug}`. All need to stay as vars but `hp_mode` must become `${seasonal_mode_id}`.

### Critical Generalization Decisions

1. **`hp_mode` → `${seasonal_mode_id}`**: All three zone types (radiant, heat_only_radiant, fancoil) extend a global `select` entity for seasonal mode switching. In esphome-devices this is hardcoded as `hp_mode`. For Vesta, this becomes a required parameter `seasonal_mode_id` — the user passes the ID of their seasonal mode select entity.

2. **`${room_slug}_boost_active` → `${boost_active_global}`**: The autotune-with-fancoil component disables boost mode during autotuning. The global variable name is currently derived from room_slug. For Vesta, accept the full global variable ID as a parameter.

3. **Fancoil PID gains**: Currently hardcoded (kp: 0.2, ki: 0.01, kd: 0.05). Make these optional vars with the current values as defaults — users get production-tested defaults but can override.

4. **heat_only_radiant.yaml**: Although listed under Story 20.3 in the epics, `radiant.yaml` DEPENDS on it via `!include`. Must be created in this story as a prerequisite. Story 20.3 should note it's already done.

### Vesta Header Format (from CONTRIBUTING.md)

```yaml
# =============================================================================
# Component: {filename}
# Purpose:   {one-line description}
#
# Required vars:
#   {var_name}               - {description}
#
# Optional vars:
#   {var_name}               - {description} (default: {value})
#
# Dependencies:
#   - {dependency_file} (included automatically)
#
# Exposes:
#   {entity_type}.{entity_id_pattern} - {description}
#
# Example:
#   packages:
#     {name}: !include
#       file: packages/components/{filename}
#       vars:
#         {var}: "{value}"
# =============================================================================
```

### Previous Story (20.1) Learnings

- Bulk `replace_all` can miss references that use different path forms (e.g., `../utils/` vs `packages/utils/` vs bare `utils/`). Always run a final grep for ANY form of the old string.
- CONTRIBUTING.md has a directory structure section that needs updating separately from path references.
- The subagent for bulk replacements is effective but doesn't catch semantic variations — always verify manually.

### Project Structure Notes

- Working directory: `vesta/` (within esphome-devices repo, separate git repo)
- All new files go in `vesta/packages/components/`
- `!include` paths within components are relative to the including file's location
- Since all components are in the same directory, cross-includes use just the filename (e.g., `file: pid_sensors.yaml`)

### References

- [Source: components/pid.yaml — 28 lines, fully parameterized]
- [Source: components/pid_sensors.yaml — 70 lines, fully parameterized]
- [Source: components/pid_autotune.yaml — 28 lines, partial header exists]
- [Source: components/pid_autotune_with_fancoil.yaml — 39 lines, partial header, needs boost_active generalization]
- [Source: components/heat_only_radiant.yaml — 91 lines, needs hp_mode generalization]
- [Source: components/radiant.yaml — 24 lines, needs hp_mode generalization]
- [Source: components/fancoil.yaml — 31 lines, needs hp_mode + PID gains generalization]
- [Source: vesta/CONTRIBUTING.md — header format and naming conventions]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 20.2]
- [Source: _bmad-output/planning-artifacts/product-brief-esphome-devices-2026-02-19.md#Core Features §2]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Debug Log References
N/A — no compilation errors encountered.

### Completion Notes List
- 7 new component files created in `vesta/packages/components/`
- All 6 epic-specified components extracted + `heat_only_radiant.yaml` as prerequisite
- Key generalizations applied:
  - `hp_mode` → `${seasonal_mode_id}` in radiant, heat_only_radiant, and fancoil
  - `${room_slug}_boost_active` → `${boost_active_global}` in pid_autotune_with_fancoil
  - Fancoil PID gains made optional with production defaults (kp: 0.2, ki: 0.01, kd: 0.05)
- Zero esphome-devices-specific references (verified via grep)
- All `!include` paths use same-directory filenames
- All headers follow CONTRIBUTING.md format with Dependencies and Exposes sections
- Note for Story 20.3: `heat_only_radiant.yaml` already extracted here as radiant.yaml prerequisite

### Change Log
- Created 7 component files (2026-02-19)

### File List
- vesta/packages/components/pid.yaml (new)
- vesta/packages/components/pid_sensors.yaml (new)
- vesta/packages/components/pid_autotune.yaml (new)
- vesta/packages/components/pid_autotune_with_fancoil.yaml (new)
- vesta/packages/components/heat_only_radiant.yaml (new)
- vesta/packages/components/radiant.yaml (new)
- vesta/packages/components/fancoil.yaml (new)
