# Story 19.3: Extract Failover Sensor

Status: review

## Story

As a **multi-zone HVAC integrator using ESPHome**,
I want **a reusable 3-tier sensor failover package that automatically switches between sensor sources**,
so that **my climate control system degrades gracefully when sensors fail instead of shutting down**.

## Acceptance Criteria

1. **AC-1:** `packages/utils/failover_sensor.yaml` compiles with declared parameters
2. **AC-2:** Tier architecture documented with ASCII/text diagram
3. **AC-3:** Parameter reference complete
4. **AC-4:** Usage example shows a realistic climate control scenario
5. **AC-5:** Automatic recovery behavior explained

## Tasks / Subtasks

- [x] Task 1: Extract and generalize failover_sensor.yaml (AC: #1)
  - [x] 1.1: Copy source to `vesta/packages/utils/failover_sensor.yaml`
  - [x] 1.2: Fix header (source says "room_sensors.yaml" - wrong filename)
  - [x] 1.3: Generalize parameter names: `ha_sensor` → `primary_sensor`, `udp_sensor` → `secondary_sensor`
  - [x] 1.4: Update tier display names: "HA" → "Primary", "UDP" → "Secondary"
  - [x] 1.5: Update log messages to use generic tier names
  - [x] 1.6: Add `defaults:` block for optional params (internal, accuracy_decimals, update_interval)
  - [x] 1.7: Apply Vesta header format with `=====` separators and Example section
- [x] Task 2: Create documentation page (AC: #2, #3, #4, #5)
  - [x] 2.1: Create `vesta/docs/failover-sensor.md`
  - [x] 2.2: Include tier priority diagram (ASCII table)
  - [x] 2.3: Parameter reference table
  - [x] 2.4: Usage example with HA + UDP + emergency scenario
  - [x] 2.5: Document automatic recovery behavior
- [x] Task 3: Validate extraction (AC: #1)
  - [x] 3.1: Verify YAML syntax and header format
  - [x] 3.2: Verify no home-specific references remain

## Dev Notes

### Generalization Required

Source has these issues to fix:
1. **Wrong header filename** - says "room_sensors.yaml", should be "failover_sensor.yaml"
2. **Header vars don't match code** - header documents `zone_slug`, `zone_name` etc. but code uses `sensor_id`, `sensor_name`, `ha_sensor`, `udp_sensor`
3. **No defaults block** - `internal: true`, `accuracy_decimals: 1`, `update_interval: 10s` are hardcoded
4. **Tier names** - "HA" and "UDP" should become "Primary" and "Secondary" for generic use
5. **Parameter names** - `ha_sensor`/`udp_sensor` → `primary_sensor`/`secondary_sensor`

### Source Parameters (actual code usage)

| Used in Code | Generalized Name | Purpose |
|-------------|-----------------|---------|
| `sensor_id` | `sensor_id` | Keep as-is |
| `sensor_name` | `sensor_name` | Keep as-is |
| `unit_of_measurement` | `unit_of_measurement` | Keep as-is |
| `device_class` | `device_class` | Keep as-is |
| `ha_sensor` | `primary_sensor` | Rename for generality |
| `udp_sensor` | `secondary_sensor` | Rename for generality |
| (hardcoded) `internal: true` | `internal` | Make configurable, default true |
| (hardcoded) `accuracy_decimals: 1` | `accuracy_decimals` | Make configurable, default 1 |
| (hardcoded) `update_interval: 10s` | `update_interval` | Make configurable, default 10s |

### References

- [Source: components/failover_sensor.yaml] - 111 lines
- [Source: vesta/CONTRIBUTING.md] - Header format
- [Source: _bmad-output/planning-artifacts/epic-19-brief.md#Story 19.3]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via Dev Agent - Amelia)

### Debug Log References

No errors encountered.

### Completion Notes List

- Extracted failover_sensor.yaml with significant generalization work:
  - Fixed incorrect header filename (was "room_sensors.yaml")
  - Renamed `ha_sensor` → `primary_sensor`, `udp_sensor` → `secondary_sensor`
  - Updated tier display names: "HA" → "Primary", "UDP" → "Secondary"
  - Updated all log messages to use generic tier names
  - Added `defaults:` block for `internal` (true), `accuracy_decimals` (1), `update_interval` (10s)
  - Added Tier Priority table and Exposes section to header
- Created comprehensive docs/failover-sensor.md with ASCII tier diagram, priority table, recovery behavior, 3 usage examples
- 15/15 validation checks passed
- Story completed: 2026-02-08

### Change Log

- 2026-02-08: Story 19.3 implemented - Failover Sensor extracted with generalized tier naming

### File List

- `vesta/packages/utils/failover_sensor.yaml` (new - extracted and generalized from components/failover_sensor.yaml)
- `vesta/docs/failover-sensor.md` (new)

