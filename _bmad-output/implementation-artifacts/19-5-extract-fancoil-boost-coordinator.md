# Story 19.5: Extract Fancoil Boost Coordinator (Hero)

Status: review

## Story

As a **multi-zone HVAC integrator using ESPHome**,
I want **the "Base + Boost" pattern as a reusable coordinator that automatically activates fancoils when radiant floor cooling reaches its limits**,
so that **I get efficient baseline cooling from radiant floors with responsive fancoil boost when conditions demand it, without manual switching**.

## Acceptance Criteria

1. **AC-1:** `packages/coordinators/fancoil_boost.yaml` compiles with declared dependencies
2. **AC-2:** All three activation triggers documented with rationale
3. **AC-3:** Deactivation AND-logic documented
4. **AC-4:** Hysteresis and anti-oscillation behavior explained
5. **AC-5:** Complete integration example provided
6. **AC-6:** Dependency on trend_sensor documented
7. **AC-7:** Diagnostic sensors listed and explained

## Tasks / Subtasks

- [x] Task 1: Extract and generalize fancoil_boost_coordinator.yaml (AC: #1, #6)
  - [x] 1.1: Copy source to `vesta/packages/coordinators/fancoil_boost.yaml`
  - [x] 1.2: Rename `room_slug` → `zone_slug`, `room_name` → `zone_name`
  - [x] 1.3: Parameterize 12 hardcoded entity references into required vars
  - [x] 1.4: Update trend sensor include path (`../utils/trend_sensor.yaml`)
  - [x] 1.5: Remove unused `saturated_duration_minutes_default` from defaults
  - [x] 1.6: Apply Vesta header format with Dependencies and Exposes sections
  - [x] 1.7: Remove `.gitkeep` from `packages/coordinators/`
- [x] Task 2: Create documentation page (AC: #2, #3, #4, #5, #7)
  - [x] 2.1: Create `vesta/docs/fancoil-boost.md`
  - [x] 2.2: Document the Base + Boost concept with architecture diagram
  - [x] 2.3: Document three activation triggers with rationale
  - [x] 2.4: Document deactivation AND-logic
  - [x] 2.5: Document hysteresis dead band and minimum time-in-state
  - [x] 2.6: Provide complete integration example
  - [x] 2.7: Document all diagnostic sensors
- [x] Task 3: Validate extraction (AC: #1)
  - [x] 3.1: Verify YAML syntax and header format
  - [x] 3.2: Verify no home-specific references remain
  - [x] 3.3: Verify all `room_slug`/`room_name` renamed to `zone_slug`/`zone_name`

## Dev Notes

### 12 External Entity References to Parameterize

| Source Reference | New Parameter | Type |
|-----------------|---------------|------|
| `${room_slug}_room_temp_abstracted` | `temperature_sensor` | sensor ID |
| `${room_slug}_room_humidity_abstracted` | `humidity_sensor` | sensor ID |
| `pid_radiant_${room_slug}` | `radiant_pid_id` | climate ID |
| `pid_radiant_${room_slug}_cool` | `radiant_pid_cool_sensor` | sensor ID |
| `pid_fancoil_${room_slug}` | `fancoil_pid_id` | climate ID |
| `${room_slug}_radiant_override_value` | `radiant_override_value_id` | number ID |
| `${room_slug}_radiant_override` | `radiant_override_switch_id` | switch ID |
| `slow_pwm_${room_slug}` | `radiant_pwm_id` | output ID |
| `summer_mode` | `cooling_mode_sensor` | binary_sensor ID |
| `effective_fancoil_boost_threshold` | `temp_threshold_sensor` | sensor ID |
| `effective_fancoil_humidity_threshold` | `humidity_threshold_sensor` | sensor ID |
| `effective_predictive_boost_minutes` | `predictive_minutes_sensor` | sensor ID |

### References

- [Source: components/fancoil_boost_coordinator.yaml] - 313 lines
- [Source: vesta/CONTRIBUTING.md] - Header format
- [Source: _bmad-output/planning-artifacts/epic-19-brief.md#Story 19.5]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via Dev Agent - Amelia)

### Debug Log References

No errors encountered.

### Completion Notes List

- Extracted fancoil_boost_coordinator.yaml (313 lines) as the hero component with extensive generalization:
  - Renamed `room_slug` → `zone_slug`, `room_name` → `zone_name`
  - Parameterized all 12 hardcoded entity references into explicit required vars
  - Updated trend sensor include path to `../utils/trend_sensor.yaml` (cross-directory)
  - Removed unused `saturated_duration_minutes_default` from defaults block
  - Removed duplicate comment line ("Coordinator logic - runs every 30 seconds")
  - Added comprehensive header with Dependencies, Activation Triggers, Deactivation, and Exposes sections
- Created deep-dive docs/fancoil-boost.md with:
  - Base + Boost architecture diagram
  - 3 activation triggers (reactive temp, reactive humidity, predictive saturation) with rationale
  - Deactivation AND-logic explanation
  - Hysteresis dead band ASCII diagram
  - Minimum time-in-state anti-oscillation
  - 7 diagnostic sensors reference table
  - Complete single-zone integration example with failover sensors
  - Multi-zone usage pattern
- Removed `.gitkeep` from `packages/coordinators/`
- Validation: 17 substitution vars verified, zero hardcoded entity references in code, zero `room_slug`/`room_name` references
- Story completed: 2026-02-08

### Change Log

- 2026-02-08: Story 19.5 implemented - Fancoil Boost Coordinator (hero component) extracted

### File List

- `vesta/packages/coordinators/fancoil_boost.yaml` (new - extracted and generalized from components/fancoil_boost_coordinator.yaml)
- `vesta/docs/fancoil-boost.md` (new - deep dive documentation)
- `vesta/packages/coordinators/.gitkeep` (deleted)
