# Story 19.2: Extract Trend Sensor (Quick Win)

Status: review

## Story

As a **multi-zone HVAC integrator using ESPHome**,
I want **a reusable trend sensor package that calculates rate-of-change per minute with smoothing**,
so that **I can detect temperature/humidity trends and enable predictive climate control logic**.

## Acceptance Criteria

1. **AC-1:** `packages/utils/trend_sensor.yaml` is self-contained and compiles with only its declared parameters
2. **AC-2:** All parameters documented with types and defaults
3. **AC-3:** `docs/trend-sensor.md` written with usage example
4. **AC-4:** Extraction pattern established (header format, parameter naming convention, doc structure) matching CONTRIBUTING.md standards

## Tasks / Subtasks

- [x] Task 1: Extract trend_sensor.yaml to Vesta (AC: #1, #2, #4)
  - [x] 1.1: Copy `components/trend_sensor.yaml` to `vesta/packages/utils/trend_sensor.yaml`
  - [x] 1.2: Update header comment block to match Vesta CONTRIBUTING.md format (use `=====` separator, add Example section)
  - [x] 1.3: Verify no home-specific references remain (should be none)
  - [x] 1.4: Remove `vesta/packages/utils/.gitkeep` (no longer needed)
- [x] Task 2: Create documentation page (AC: #3)
  - [x] 2.1: Create `vesta/docs/trend-sensor.md` with sections: What It Does, How It Works, Parameter Reference, Usage Example, Integration Tips
  - [x] 2.2: Explain the sliding window moving average smoothing
  - [x] 2.3: Provide usage examples for temperature trend and humidity trend
- [x] Task 3: Validate extraction (AC: #1, #4)
  - [x] 3.1: Verify the extracted YAML is valid (no syntax errors)
  - [x] 3.2: Confirm header format matches CONTRIBUTING.md template exactly
  - [x] 3.3: Remove `vesta/docs/.gitkeep` (no longer needed)

## Dev Notes

### Source Component Analysis

**Source:** `components/trend_sensor.yaml` (48 lines)
**Extraction Difficulty:** LOW - already fully generic and parameterized

The source component is already in excellent shape for extraction:
- Header comment block documents purpose, required vars, optional vars
- All values are parameterized via `${variable}` substitution
- Uses `defaults:` block for optional parameters
- Zero home-specific or hardcoded references
- Standalone - no dependencies on other components

### Source Code (complete - 48 lines)

```yaml
# Header: purpose, required vars, optional vars
defaults:
  sensor_name: "Trend Sensor"
  accuracy_decimals: "2"
  window_size: "10"
  icon: "mdi:trending-up"
  internal: "false"

sensor:
  - platform: template
    id: ${sensor_id}
    name: "${sensor_name}"
    internal: ${internal}
    unit_of_measurement: "${unit_of_measurement}"
    accuracy_decimals: ${accuracy_decimals}
    icon: "${icon}"
    lambda: |-
      static float last_val = NAN;
      static uint32_t last_ts = 0;
      float cur_val = id(${source_sensor}).state;
      uint32_t now = millis();
      if (isnan(cur_val)) return NAN;
      float res = 0.0f;
      if (!isnan(last_val) && last_ts > 0 && now > last_ts) {
        float dt = (now - last_ts) / 60000.0f; // minutes
        if (dt > 0.01) res = (cur_val - last_val) / dt;
      }
      last_val = cur_val;
      last_ts = now;
      return res;
    filters:
      - sliding_window_moving_average:
          window_size: ${window_size}
          send_every: 1
```

### How It Works

1. Lambda calculates `(current - previous) / elapsed_minutes` on each update
2. Returns NAN if source sensor value is NAN (propagates unavailability)
3. First reading returns 0.0 (no previous value to compare)
4. `sliding_window_moving_average` filter smooths output over `window_size` samples
5. `send_every: 1` publishes every update (smoothed)

### Vesta Header Format (from CONTRIBUTING.md)

Must use this exact format:
```
# =============================================================================
# Component: trend_sensor.yaml
# Purpose:   Calculate rate of change per minute with sliding window smoothing
#
# Required vars:
#   sensor_id            - ID for the created trend sensor
#   source_sensor        - Sensor ID to analyze (e.g., sensor.room_temp)
#   unit_of_measurement  - Output unit (e.g., "°C/min", "%/min")
#
# Optional vars:
#   sensor_name          - Friendly name (default: "Trend Sensor")
#   window_size          - Smoothing window samples (default: 10)
#   accuracy_decimals    - Decimal precision (default: 2)
#   icon                 - MDI icon (default: "mdi:trending-up")
#   internal             - Hide from HA (default: false)
#
# Example:
#   packages:
#     trend: !include
#       file: packages/utils/trend_sensor.yaml
#       vars:
#         sensor_id: "living_room_trend"
#         source_sensor: sensor.living_room_temperature
#         unit_of_measurement: "°C/min"
# =============================================================================
```

### Doc Page Structure (for `docs/trend-sensor.md`)

Follow this structure for ALL future component docs:
1. **Title and one-line description**
2. **What It Does** - 2-3 sentences on the problem and solution
3. **How It Works** - Technical explanation of the algorithm
4. **Parameter Reference** - Table with name, type, required, default, description
5. **Usage Example** - Complete `!include` with vars showing typical use
6. **Integration Tips** - How this component connects with others (e.g., used by fancoil_boost, proportional_demand)

### Previous Story (19.1) Learnings

- `vesta/` directory is a separate git repo - all work inside it
- `.gitkeep` files exist in empty directories - remove them when real files are added
- CONTRIBUTING.md defines the header format and coding standards
- README.md already has the component table with doc links

### Testing Approach

- Verify YAML syntax is valid (no parse errors)
- Verify header matches CONTRIBUTING.md format
- No ESPHome `config` compilation needed for this extraction (component requires a device config wrapper to compile)

### Project Structure Notes

- Work in `vesta/` directory only
- Target: `vesta/packages/utils/trend_sensor.yaml`
- Doc target: `vesta/docs/trend-sensor.md`
- Clean up `.gitkeep` from `packages/utils/` and `docs/` once real files exist

### References

- [Source: components/trend_sensor.yaml] - Original 48-line source component
- [Source: vesta/CONTRIBUTING.md] - Header format template and coding standards
- [Source: _bmad-output/planning-artifacts/epic-19-brief.md#Story 19.2] - Story requirements
- [Source: _bmad-output/implementation-artifacts/19-1-repository-scaffolding.md] - Previous story context

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via Dev Agent - Amelia)

### Debug Log References

No errors encountered.

### Completion Notes List

- Extracted trend_sensor.yaml from `components/` to `vesta/packages/utils/` with updated Vesta header format
- Header updated: added `=====` separator borders, aligned parameter descriptions, added Example section
- Source component required zero code changes - already fully generic and parameterized
- Created comprehensive `docs/trend-sensor.md` with: What It Does, How It Works, Parameter Reference table, 3 usage examples (temperature, humidity, GitHub remote), Integration Tips
- Established extraction pattern: header format, doc structure, parameter naming convention
- Removed `.gitkeep` files from `packages/utils/` and `docs/` (replaced by real content)
- All 11 validation checks passed (header format, substitution vars, no hardcoded refs, etc.)
- Story completed: 2026-02-08

### Change Log

- 2026-02-08: Story 19.2 implemented - Trend Sensor extracted as first Vesta component

### File List

- `vesta/packages/utils/trend_sensor.yaml` (new - extracted from components/trend_sensor.yaml)
- `vesta/docs/trend-sensor.md` (new)
- `vesta/packages/utils/.gitkeep` (deleted)
- `vesta/docs/.gitkeep` (deleted)

