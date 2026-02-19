# Story 20.4: Extract Seasonal Mode Coordinator

Status: done

## Story

As a **multi-zone HVAC integrator using ESPHome**,
I want **a seasonal mode coordinator that manages heat/cool mode transitions based on calendar and demand signals**,
so that **my system switches between heating and cooling seasons automatically without manual intervention**.

## Acceptance Criteria

1. **AC-1:** `seasonal_mode.yaml` extracted to `packages/coordinators/` with full Vesta header
2. **AC-2:** The component compiles standalone with only its declared parameters
3. **AC-3:** No references to esphome-devices-specific entities remain
4. **AC-4:** Calendar-based mode locking is parameterized (configurable date ranges)
5. **AC-5:** Demand-driven shoulder season transitions are parameterized
6. **AC-6:** All parameters have header comment blocks with purpose, required vars, optional vars, example
7. **AC-7:** The Epic 19 extraction pattern is followed (header format per CONTRIBUTING.md)

## Tasks / Subtasks

- [x] Task 1: Extract `seasonal_mode.yaml` to coordinators (AC: #1, #2, #3, #6, #7)
  - [x] 1.1: Create `vesta/packages/coordinators/seasonal_mode.yaml` with full Vesta header
  - [x] 1.2: Parameterize `hp_mode` → `${seasonal_mode_id}` throughout
  - [x] 1.3: Parameterize `pcf85063_time` → `${time_id}` as required var
  - [x] 1.4: Parameterize `hp_mode_reason` → `${seasonal_mode_id}_reason`
  - [x] 1.5: Parameterize `season_classification` → `${seasonal_mode_id}_season`
  - [x] 1.6: Keep `any_pid_requesting_heat` / `any_pid_requesting_cool` as stub binary sensors with parameterized IDs (`${heat_demand_id}` / `${cool_demand_id}`)
  - [x] 1.7: Keep `summer_mode` compatibility sensor, parameterize ID → `${seasonal_mode_id}_summer`
- [x] Task 2: Parameterize calendar date ranges (AC: #4)
  - [x] 2.1: Add optional vars for winter lock dates (default: Oct 15 – Apr 15)
  - [x] 2.2: Add optional vars for summer lock dates (default: Jun 1 – Aug 31)
  - [x] 2.3: Spring/autumn shoulder seasons derived from lock boundaries (no extra vars needed)
- [x] Task 3: Parameterize demand-driven transitions (AC: #5)
  - [x] 3.1: Binary sensor stubs defined with parameterized IDs (`${heat_demand_id}`, `${cool_demand_id}`)
  - [x] 3.2: Documented in header that device config must `!extend` stubs with actual demand aggregation
- [x] Task 4: Cross-component validation (AC: #2, #3)
  - [x] 4.1: Zero esphome-devices-specific references — verified via grep (only in header examples)
  - [x] 4.2: All entity IDs use substitution variables

## Dev Notes

### Architecture Context

The seasonal mode coordinator is the only coordinator-category package in this epic. It provides a three-tier decision system:
- **Tier 1 (Calendar Gates):** Hard locks during winter (Oct 15–Apr 15 → HEAT) and summer (Jun 1–Aug 31 → COOL)
- **Tier 2 (Weather):** Placeholder for future weather API integration (not implemented yet)
- **Tier 3 (Demand-Driven):** During shoulder seasons, PID demand signals trigger HEAT/COOL transitions

### Source File Analysis

**`components/seasonal_mode.yaml` (~100 lines):**
- `select` entity `hp_mode` with 3 options: HEAT, COOL, SANITARY_ONLY
- `text_sensor` for mode reason (CALENDAR_LOCK / DEMAND) and season classification
- `binary_sensor` stubs: `any_pid_requesting_heat`, `any_pid_requesting_cool` (extended by device config)
- `binary_sensor` compatibility: `summer_mode` (true when COOL)
- Two `script`s: `check_calendar_gates` and `check_demand_transitions`
- `interval` runs both scripts every 1 minute
- **PARAMETERIZED:** `hp_mode` → `${seasonal_mode_id}`, `pcf85063_time` → `${time_id}`
- **PARAMETERIZED:** Calendar date boundaries as optional vars with production defaults

### Generalization Notes

1. **`hp_mode` → `${seasonal_mode_id}`:** All references to the select entity ID use the substitution variable. Downstream components (radiant, heat_only_radiant, fancoil) already accept `seasonal_mode_id` as a required var.
2. **`pcf85063_time` → `${time_id}`:** The RTC/time source ID is hardware-specific. Different boards use different time platforms (SNTP, DS1307, PCF85063, etc.).
3. **Date ranges as optional vars:** Calendar boundaries are configurable and default to production values (Milan, Italy climate). Integer substitutions for month/day.
4. **Demand sensor stubs:** `${heat_demand_id}` and `${cool_demand_id}` are template binary sensors with no lambda (stubs). Device config extends them with room-specific demand aggregation.
5. **Derived entity IDs:** `${seasonal_mode_id}` is base for derived IDs: `_reason`, `_season`, `_summer`.
6. **Script IDs:** Namespaced to avoid collisions: `${seasonal_mode_id}_check_calendar`, `${seasonal_mode_id}_check_demand`.
7. **Shoulder season derivation:** Spring shoulder = winter_end to summer_start, autumn shoulder = summer_end+1 to winter_start. No extra vars needed.

### Previous Story Learnings

- Document dependency chains fully (including transitive deps)
- Add comments for implicit var passthrough in layered includes
- Keep naming conventions consistent: coordinators use conceptual names, not room/area names

### Project Structure Notes

- New file goes in `vesta/packages/coordinators/`
- This is a coordinator (orchestrates system behavior), not a component (single function)

### References

- [Source: components/seasonal_mode.yaml — ~100 lines, fully parameterized]
- [Source: vesta/CONTRIBUTING.md — header format]
- [Source: vesta/packages/components/radiant.yaml — seasonal_mode_id usage pattern]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 20.4]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Debug Log References
N/A

### Completion Notes List
- 1 new coordinator file created
- All entity IDs parameterized (select, text_sensors, binary_sensors, scripts)
- Calendar date ranges fully configurable via 8 optional vars
- Demand sensor IDs configurable via `heat_demand_id` / `cool_demand_id`
- Shoulder seasons derived from lock boundaries (no redundant vars)
- Script IDs namespaced to `${seasonal_mode_id}_check_*` to avoid collisions
- Zero esphome-devices-specific references

### Change Log
- Created coordinator file (2026-02-19)

### File List
- vesta/packages/coordinators/seasonal_mode.yaml (new)
