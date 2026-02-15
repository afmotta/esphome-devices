# Story 19.4: Extract Proportional Demand Sensor

Status: review

## Story

As a **multi-zone HVAC integrator using ESPHome**,
I want **a reusable proportional demand sensor that converts any sensor reading into a 0-100% demand signal with optional rate-of-change boost**,
so that **I can drive ventilation fan speeds, valve positions, or other actuators proportionally based on environmental conditions**.

## Acceptance Criteria

1. **AC-1:** `packages/utils/proportional_demand_sensor.yaml` compiles with trend_sensor as dependency
2. **AC-2:** Parameter names are component-agnostic (no `mev_` prefix)
3. **AC-3:** Dependency on trend_sensor clearly documented
4. **AC-4:** Rate boost feature explained with practical example
5. **AC-5:** At least 2 usage examples (humidity, CO2)

## Tasks / Subtasks

- [x] Task 1: Extract and generalize proportional_demand_sensor.yaml (AC: #1, #2)
  - [x] 1.1: Copy source to `vesta/packages/utils/proportional_demand_sensor.yaml`
  - [x] 1.2: Rename `mev_slug` → `component_id`, `mev_name` → `component_name`
  - [x] 1.3: Parameterize hardcoded HA entity IDs (`input_number.mev_*`) into `lower_bound_entity` and `upper_bound_entity`
  - [x] 1.4: Update trend sensor include path for Vesta package structure
  - [x] 1.5: Update all internal entity IDs to use `component_id` instead of `mev_slug`
  - [x] 1.6: Apply Vesta header format with `=====` separators, Example section, Exposes section
- [x] Task 2: Create documentation page (AC: #3, #4, #5)
  - [x] 2.1: Create `vesta/docs/proportional-demand.md`
  - [x] 2.2: Document the math (linear mapping with clamping + rate boost)
  - [x] 2.3: Document dependency on trend_sensor
  - [x] 2.4: Provide usage examples for humidity demand and CO2 demand
  - [x] 2.5: Document rate boost feature with practical explanation
- [x] Task 3: Validate extraction (AC: #1, #2)
  - [x] 3.1: Verify YAML syntax and header format
  - [x] 3.2: Verify no home-specific references remain
  - [x] 3.3: Verify all `mev_` prefixes removed from parameter names

## Dev Notes

### Generalization Required

Source has these issues to fix:
1. **`mev_slug`/`mev_name` prefix** - MEV-specific, should be component-agnostic (`component_id`/`component_name`)
2. **Hardcoded HA entity patterns** - `input_number.mev_${demand_slug}_lower_bound` and `upper_bound` are hardcoded entity_id patterns
3. **No Vesta header format** - Original header uses simple comment format, needs `=====` separators
4. **Trend sensor include path** - `file: trend_sensor.yaml` needs to remain relative (same directory works)

### Source Parameters (actual code usage)

| Used in Code | Generalized Name | Purpose |
|-------------|-----------------|---------|
| `mev_slug` | `component_id` | Rename - prefix for entity IDs |
| `mev_name` | `component_name` | Rename - friendly name prefix |
| `demand_slug` | `demand_slug` | Keep as-is |
| `demand_name` | `demand_name` | Keep as-is |
| `source_sensor_id` | `source_sensor_id` | Keep as-is |
| `min_val_id` | `min_output_id` | Rename for clarity |
| (hardcoded) `input_number.mev_*_lower_bound` | `lower_bound_entity` | New required param |
| (hardcoded) `input_number.mev_*_upper_bound` | `upper_bound_entity` | New required param |
| `rate_multiplier` | `rate_multiplier` | Keep as-is (default: 0.0) |
| `window_size` | `window_size` | Keep as-is (default: 15) |
| `unit_of_measurement` | `unit_of_measurement` | Keep as-is (default: %) |
| `icon` | `icon` | Keep as-is (default: mdi:gauge) |
| `accuracy_decimals` | `accuracy_decimals` | Keep as-is (default: 0) |
| `fallback_value` | `fallback_value` | Keep as-is (default: 20.0) |

### References

- [Source: components/proportional_demand_sensor.yaml] - 84 lines
- [Source: vesta/CONTRIBUTING.md] - Header format
- [Source: _bmad-output/planning-artifacts/epic-19-brief.md#Story 19.4]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via Dev Agent - Amelia)

### Debug Log References

No errors encountered.

### Completion Notes List

- Extracted proportional_demand_sensor.yaml with significant generalization:
  - Renamed `mev_slug` → `component_id`, `mev_name` → `component_name`
  - Renamed `min_val_id` → `min_output_id` for clarity
  - Parameterized hardcoded HA entity patterns into `lower_bound_entity` and `upper_bound_entity` (new required params)
  - Updated all internal entity IDs to use `component_id` prefix
  - Added Vesta header format with Dependencies and Exposes sections
- Created comprehensive docs/proportional-demand.md with: linear mapping math, rate boost explanation, dependency chain diagram, 3 usage examples (humidity, CO2, GitHub remote), integration tips
- Validation: 14 substitution vars verified, zero `mev_` references in component, YAML syntax clean, header format correct
- Story completed: 2026-02-08

### Change Log

- 2026-02-08: Story 19.4 implemented - Proportional Demand Sensor extracted with generalized naming

### File List

- `vesta/packages/utils/proportional_demand_sensor.yaml` (new - extracted and generalized from components/proportional_demand_sensor.yaml)
- `vesta/docs/proportional-demand.md` (new)
