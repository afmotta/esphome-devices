# Story 19.6: Extract MEV Ventilation Coordinator

Status: review

## Story

As a **multi-zone HVAC integrator using ESPHome**,
I want **a reusable MEV ventilation coordinator with multi-demand orchestration and humidity cascade state machine**,
so that **I can control mechanical extract ventilation systems that respond to CO2, IAQ, and humidity with automatic mode escalation**.

## Acceptance Criteria

1. **AC-1:** `packages/coordinators/mev_ventilation.yaml` compiles with declared dependencies
2. **AC-2:** Multi-demand orchestration pattern documented
3. **AC-3:** Humidity cascade state machine documented with state diagram
4. **AC-4:** Escalation/de-escalation timing explained
5. **AC-5:** Season awareness documented
6. **AC-6:** Dependency chain documented (proportional_demand → trend_sensor)
7. **AC-7:** Hardware requirements listed (relays, DAC, sensors)

## Tasks / Subtasks

- [x] Task 1: Extract and generalize mev.yaml (AC: #1, #6, #7)
  - [x] 1.1: Copy source to `vesta/packages/coordinators/mev_ventilation.yaml`
  - [x] 1.2: Rename `mev_slug` → `component_id`, `mev_name` → `component_name`
  - [x] 1.3: Parameterize hardcoded sensor IDs (`first_floor_max_co2`, `first_floor_max_iaq`)
  - [x] 1.4: Parameterize hardcoded HA entity patterns (`input_number.mev_*`)
  - [x] 1.5: Parameterize `summer_mode` → `cooling_mode_sensor`
  - [x] 1.6: Update proportional_demand_sensor include paths and pass new params
  - [x] 1.7: Apply Vesta header format
- [x] Task 2: Create documentation page (AC: #2, #3, #4, #5)
  - [x] 2.1: Create `vesta/docs/mev-ventilation.md`
  - [x] 2.2: Document multi-demand MAX aggregation
  - [x] 2.3: Document humidity cascade state machine with ASCII diagram
  - [x] 2.4: Document escalation/de-escalation timing
  - [x] 2.5: Document season awareness
  - [x] 2.6: Complete parameter reference and integration example
- [x] Task 3: Validate extraction (AC: #1, #2)
  - [x] 3.1: Verify YAML syntax and header format
  - [x] 3.2: Verify no home-specific references remain
  - [x] 3.3: Verify all `mev_slug`/`mev_name` renamed

## Dev Notes

### Hardcoded References to Parameterize

| Source Reference | New Parameter | Type |
|-----------------|---------------|------|
| `first_floor_max_co2` | `co2_sensor` | sensor ID |
| `first_floor_max_iaq` | `iaq_sensor` | sensor ID |
| `summer_mode` | `cooling_mode_sensor` | binary_sensor ID |
| `input_number.mev_escalation_fan_threshold` | `escalation_threshold_entity` | HA entity |
| `input_number.mev_deescalation_fan_threshold` | `deescalation_threshold_entity` | HA entity |
| `input_number.mev_minimum_fan_speed` | `min_fan_speed_entity` | HA entity |
| `input_number.mev_escalation_delay_minutes` | `escalation_delay_entity` | HA entity |
| `input_number.mev_deescalation_delay_minutes` | `deescalation_delay_entity` | HA entity |

Plus 6 demand bound entities for the 3 proportional_demand_sensor includes.

### References

- [Source: components/mev.yaml] - 365 lines
- [Source: vesta/CONTRIBUTING.md] - Header format
- [Source: _bmad-output/planning-artifacts/epic-19-brief.md#Story 19.6]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via Dev Agent - Amelia)

### Debug Log References

No errors encountered.

### Completion Notes List

- Extracted mev.yaml (365 lines) as the most complex component with extensive generalization:
  - Renamed `mev_slug` → `component_id`, `mev_name` → `component_name`
  - Parameterized 2 hardcoded sensor IDs (`first_floor_max_co2` → `co2_sensor`, `first_floor_max_iaq` → `iaq_sensor`)
  - Parameterized 5 hardcoded HA entity patterns (`input_number.mev_*` → explicit entity params)
  - Parameterized `summer_mode` → `cooling_mode_sensor`
  - Added 6 demand bound entity params for the 3 proportional_demand_sensor includes
  - Updated all proportional_demand_sensor include paths to `../utils/` and passed `component_id`/`component_name` through
  - Added 3 optional rate_multiplier params (co2: 0.05, iaq: 2.0, humidity: 20.0)
  - 26 total substitution vars (23 required + 3 optional)
- Aligned transition logic with mev_modbus.yaml event-driven architecture:
  - Replaced counter-based interval polling with scripts (mode: restart) + template binary sensors
  - on_press starts delay timer, on_release cancels it
- **Major refactor: Decoupled hardware and demands from controller:**
  - Vesta component is now a pure controller (no hardware, no demand calculation)
  - Removed: 4 relay switches, fan speed number/DAC, alarm binary_sensor, 3 proportional_demand_sensor includes
  - Added external entity references: demand_sensor, humidity_rate_sensor, dehumidifier_switch, cooling_switch, alarm_sensor, fan_speed_number
  - Added humidity_lower_bound_entity HA import (was implicit from demand sensor include)
  - Reduced from 26 vars (23 required + 3 optional) to 16 required, 0 optional
  - Dominant demand text_sensor removed from controller (belongs with demand aggregation)
  - Controller exposes 3 entities: final_fan_speed, automation_state, humidity_state
- Also refactored components/mev.yaml in the same way:
  - Removed 3 proportional_demand_sensor includes
  - Added demand_sensor, humidity_rate_sensor, humidity_lower_sensor params
  - Simplified final_fan_speed lambda to read single aggregated demand
  - Kept hardware (switches, alarm, fan speed number) since it's home-specific
- Created components/mev_demand.yaml (NEW):
  - Contains the 3 proportional_demand_sensor includes (CO2, IAQ, humidity)
  - MAX aggregation template sensor
  - Dominant demand text_sensor
- Updated docs/mev-ventilation.md:
  - Rewritten for decoupled architecture
  - 3-step integration guide (create demands, create hardware, include controller)
  - Flexible demands section explaining arbitrary demand count support
- Story completed: 2026-02-08

### Change Log

- 2026-02-08: Story 19.6 implemented - MEV Ventilation Coordinator extracted with full generalization
- 2026-02-08: Transition logic aligned with mev_modbus.yaml event-driven architecture
- 2026-02-08: Major refactor - decoupled hardware and demands from controller (16 params, pure controller)
- 2026-02-09: DRY refactor - both mev.yaml and mev_modbus.yaml now reuse Vesta controller + mev_demand.yaml. Replaced humidity_lower_bound_entity (HA import) with humidity_lower_sensor (sensor ID ref) to avoid duplicate ID conflict with proportional_demand_sensor. mev.yaml: 377→151 lines. mev_modbus.yaml: 1081→808 lines.

### File List

- `vesta/packages/coordinators/mev_ventilation.yaml` (rewritten - pure controller, 16 required params)
- `vesta/docs/mev-ventilation.md` (rewritten - decoupled architecture docs)
- `components/mev.yaml` (refactored - demand orchestration removed, takes external demand_sensor)
- `components/mev_demand.yaml` (new - MAX demand aggregation for 3 proportional demands)
