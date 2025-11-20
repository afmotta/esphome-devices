# Story 10.1: Update room_sensors.yaml to v6 (UDP Tier Support) - Brownfield Addition

**Epic:** 10 - ESP32 Room Sensors & Zone Activity Tracking via UDP  
**Date:** November 20, 2025  
**Status:** Ready  
**Story Points:** 3  
**Version:** 1.0

---

## User Story

As a **system developer maintaining the ESPHome climate control codebase**,  
I want **room_sensors.yaml to support optional UDP sensor integration as Tier 1 with backward compatibility**,  
So that **distribution boards can receive room temperatures directly from ESP32 sensors while preserving existing HA-only deployments**.

---

## Story Context

**Existing System Integration:**

- **Integrates with:** `components/room_sensors.yaml` (v8), `components/sensor_failover_3tier.yaml` (v1.0), room component files in `components/rooms/`
- **Technology:** ESPHome YAML packages, packet_transport UDP platform (Epic 9), template sensors
- **Follows pattern:** Epic 9's 3-tier failover architecture (UDP → HA → Emergency)
- **Touch points:**
  - `components/room_sensors.yaml` - Current v8 provides HA-only sensor abstraction
  - `components/sensor_failover_3tier.yaml` - Proven 3-tier failover logic to be integrated
  - All room component files (e.g., `components/rooms/ground_floor/soggiorno.yaml`) - Call room_sensors.yaml with vars
  - Distribution board device files - Will add UDP receiver configuration

**Current State:**

- `room_sensors.yaml` v8 (Epic 8): Simple HA sensor abstraction, no failover logic
- `sensor_failover_3tier.yaml` exists but not used by room components yet
- Room components include room_sensors.yaml with `zone_slug`, `zone_name`, `ha_temperature_sensor_id`
- No UDP sensor support in room architecture

**Desired State:**

- `room_sensors.yaml` v6 (Epic 10): Conditional logic to use either HA-only (Epic 5/8 mode) or 3-tier failover (Epic 10 mode)
- Feature flag `use_udp: false` (default) maintains backward compatibility
- When `use_udp: true`, delegates to `sensor_failover_3tier.yaml` instead of direct HA sensor
- Existing room deployments continue working unchanged (v8 behavior preserved)

---

## Acceptance Criteria

### Functional Requirements

1. **UDP Feature Flag:**
   - Add optional `use_udp` variable (default: `false`) to room_sensors.yaml
   - When `use_udp: false`, component behaves exactly as v8 (direct HA sensor, no failover)
   - When `use_udp: true`, component includes sensor_failover_3tier.yaml package

2. **Conditional Package Inclusion:**
   - Use ESPHome conditional package inclusion or defaults mechanism
   - If `use_udp: true`, require `udp_sensor_id` variable (ESPHome sensor ID for UDP receiver)
   - Preserve all existing variables: `zone_slug`, `zone_name`, `ha_temperature_sensor_id`

3. **Sensor ID Consistency:**
   - Abstracted sensor ID remains `${zone_slug}_room_temp_abstracted` in both modes
   - PID controllers continue using same sensor reference (no changes to room components)
   - Diagnostic sensors (tier status) only present when `use_udp: true`

### Integration Requirements

4. **Existing Epic 8 Deployments:**
   - All current room components (soggiorno, cucina, bagno, etc.) continue working without modification
   - No changes required to room component YAML files unless enabling UDP
   - Compilation succeeds for all distribution board device files without changes

5. **Epic 10 UDP Mode:**
   - Room components can opt-in to UDP by adding `use_udp: true` and `udp_sensor_id` to vars
   - 3-tier failover logic (UDP → HA → Emergency) activates when UDP enabled
   - Diagnostic text_sensor for tier visibility exposed when UDP enabled

6. **sensor_failover_3tier.yaml Integration:**
   - When `use_udp: true`, include sensor_failover_3tier.yaml package
   - Pass through required vars: `zone_slug`, `zone_name`, `udp_sensor_id`, `ha_temperature_sensor_id`
   - Optional `emergency_timeout` var passed through (default: 180s)

### Quality Requirements

7. **Compilation Validation:**
   - All existing device configurations compile without errors (backward compatibility)
   - Test compilation with `use_udp: false` (default, v8 behavior)
   - Test compilation with `use_udp: true` (Epic 10 mode, requires udp_sensor_id)

8. **Documentation:**
   - Update component header comments to reflect v6 changes
   - Document `use_udp`, `udp_sensor_id`, and behavior differences
   - Add version history entry for v6

9. **No Regression:**
   - Existing room_emergency_condition.yaml and room_window_condition.yaml components continue working
   - room_control_coordinator.yaml continues consuming `${zone_slug}_room_temp_abstracted` sensor

---

## Technical Notes

### Integration Approach

**Conditional Logic Strategy:**

Option A (ESPHome substitutions with defaults - RECOMMENDED):
```yaml
defaults:
  use_udp: false
  udp_sensor_id: "" # Empty when not using UDP

# Conditional include based on use_udp flag
# If use_udp=false: Direct HA sensor (Epic 8 v8 behavior)
# If use_udp=true: Include sensor_failover_3tier.yaml
```

Option B (Dual-mode in single file):
- Keep both HA-only sensor definition and failover package inclusion in room_sensors.yaml
- Use ESPHome `!include` with conditional logic
- More complex but potentially cleaner for users

**Recommended: Option A** - Use defaults and conditional package inclusion for clarity.

### Existing Pattern Reference

- **Epic 9 sensor_failover_3tier.yaml:** Already implements UDP → HA → Emergency failover
- **Epic 8 room_sensors.yaml v8:** Simple HA sensor abstraction (current implementation)
- **Epic 7/8 feature flags:** `window_shutdown_modes` pattern for optional features

### Key Constraints

- **Backward Compatibility:** Default behavior MUST match v8 (HA-only, no UDP)
- **Sensor ID Stability:** `${zone_slug}_room_temp_abstracted` must remain unchanged for PID references
- **Minimal Complexity:** Avoid over-engineering; simple conditional inclusion sufficient
- **No Breaking Changes:** Existing room component files must not require modification

### Implementation Notes

**File Structure:**

```yaml
# room_sensors.yaml v6
# Version: Epic 10 - UDP Sensor Support
# Backward compatible with Epic 8 deployments

defaults:
  use_udp: false
  emergency_timeout: 180

# Mode 1: HA-Only (Epic 8 v8 behavior, default)
# Mode 2: 3-Tier Failover (Epic 10, when use_udp=true)

# Implementation approaches:
# A. Conditional package inclusion (if ESPHome supports)
# B. Dual sensor definitions with conditional logic
# C. Template-based delegation
```

**Variable Contract:**

- **Required (all modes):** `zone_slug`, `zone_name`, `ha_temperature_sensor_id`
- **Required (UDP mode):** `udp_sensor_id` (when `use_udp: true`)
- **Optional (all modes):** `emergency_timeout` (default: 180)
- **Optional (feature flag):** `use_udp` (default: false)

---

## Definition of Done

- [x] **Functional requirements met:**
  - [ ] `use_udp` flag added with default `false`
  - [ ] HA-only mode (use_udp=false) preserves v8 behavior exactly
  - [ ] UDP mode (use_udp=true) includes sensor_failover_3tier.yaml
  - [ ] Abstracted sensor ID consistent across both modes

- [x] **Integration requirements verified:**
  - [ ] Existing room components compile without modification (backward compatibility test)
  - [ ] New room component with `use_udp: true` compiles successfully (forward compatibility test)
  - [ ] sensor_failover_3tier.yaml correctly included when UDP enabled

- [x] **Existing functionality regression tested:**
  - [ ] room_emergency_condition.yaml still detects sensor failures
  - [ ] room_control_coordinator.yaml still consumes abstracted sensor
  - [ ] PID controllers still reference correct sensor ID

- [x] **Code follows existing patterns:**
  - [ ] Component header format matches Epic 8 conventions
  - [ ] Variable naming follows zone_slug/zone_name pattern
  - [ ] Defaults mechanism used consistently

- [x] **Tests pass (compilation validation):**
  - [ ] `esphome config devices/distribuzione-piano-terra.yaml` succeeds (HA-only mode)
  - [ ] `esphome config devices/distribuzione-primo-piano.yaml` succeeds (HA-only mode)
  - [ ] Test room component with `use_udp: true` compiles (mock UDP sensor)

- [x] **Documentation updated:**
  - [ ] room_sensors.yaml header comments updated for v6
  - [ ] Version history section added
  - [ ] Variable contract documented (use_udp, udp_sensor_id)
  - [ ] Mode behavior differences explained

---

## Risk and Compatibility Check

### Minimal Risk Assessment

**Primary Risk:** Breaking existing Epic 8 deployments if default behavior changes

- **Impact:** HIGH - All room components would fail, require immediate rollback
- **Likelihood:** LOW - Default `use_udp: false` preserves v8 behavior
- **Mitigation:**
  - Set `use_udp: false` as explicit default
  - Compile-test all existing device files before commit
  - Document rollback procedure (git revert to v8)

**Secondary Risk:** sensor_failover_3tier.yaml incompatibility with room_sensors.yaml variable contract

- **Impact:** MEDIUM - UDP mode fails to compile
- **Likelihood:** LOW - sensor_failover_3tier.yaml designed for this integration
- **Mitigation:**
  - Review variable contracts before implementation
  - Test UDP mode with mock udp_sensor_id

### Compatibility Verification

- [x] **No breaking changes to existing APIs:**
  - Sensor ID `${zone_slug}_room_temp_abstracted` unchanged
  - Existing variables (zone_slug, zone_name, ha_temperature_sensor_id) unchanged
  - New variables are optional with safe defaults

- [x] **Database changes:** N/A (ESPHome firmware only)

- [x] **UI changes:** None for HA-only mode; diagnostic sensor added in UDP mode (non-breaking)

- [x] **Performance impact:** Negligible - conditional package inclusion at compile time, no runtime overhead

---

## Validation Checklist

### Scope Validation

- [x] **Story can be completed in one development session:** Yes (estimated 2-3 hours: implementation 1hr, testing 1hr, documentation 30min)
- [x] **Integration approach is straightforward:** Yes (conditional package inclusion, proven Epic 9 pattern)
- [x] **Follows existing patterns exactly:** Yes (sensor_failover_3tier.yaml, defaults mechanism, Epic 8 component structure)
- [x] **No design or architecture work required:** Yes (architecture defined in Epic 10 brief, Epic 9 foundation exists)

### Clarity Check

- [x] **Story requirements are unambiguous:** Yes (clear v8→v6 transformation, explicit feature flag behavior)
- [x] **Integration points are clearly specified:** Yes (room_sensors.yaml, sensor_failover_3tier.yaml, room components)
- [x] **Success criteria are testable:** Yes (compilation tests, backward compatibility validation)
- [x] **Rollback approach is simple:** Yes (git revert to v8, or set use_udp: false)

---

## Notes and Open Questions

### Implementation Decision Required

**Question:** Should room_sensors.yaml v6 use conditional `!include` or dual-mode sensor definitions?

**Options:**

1. **Conditional Package Inclusion (Recommended):**
   ```yaml
   # When use_udp=false: Define HA sensor directly
   # When use_udp=true: Include sensor_failover_3tier.yaml
   ```
   - **Pros:** Clear separation, reuses sensor_failover_3tier.yaml
   - **Cons:** May require ESPHome conditional include support

2. **Dual-Mode Single File:**
   - Embed 3-tier failover logic directly in room_sensors.yaml
   - **Pros:** Self-contained, no external dependency
   - **Cons:** Duplicates sensor_failover_3tier.yaml logic

**Recommendation:** Use Option 1 (conditional package inclusion) to maintain Epic 9's sensor_failover_3tier.yaml as reusable component.

### Testing Strategy

**Backward Compatibility Test:**
```bash
# Test existing devices compile without changes
esphome config devices/distribuzione-piano-terra.yaml
esphome config devices/distribuzione-primo-piano.yaml
```

**Forward Compatibility Test (UDP Mode):**
```yaml
# Create test room component with UDP enabled
sensors: !include
  file: ../../room_sensors.yaml
  vars:
    zone_slug: "test_room"
    zone_name: "Test Room"
    ha_temperature_sensor_id: "sensor.test_room_temperature"
    use_udp: true
    udp_sensor_id: "test_room_udp_sensor" # Mock sensor ID
```

### Dependencies

- **Prerequisite:** sensor_failover_3tier.yaml exists (Epic 9) ✅
- **Prerequisite:** ESPHome supports conditional package inclusion (verify)
- **Follows:** Story 10.2 will add UDP receiver configuration to distribution boards
- **Blocks:** Story 10.3 cannot complete without v6 room_sensors.yaml

---

## Success Criteria Summary

This story is **successful** when:

1. ✅ room_sensors.yaml v6 compiles in both HA-only mode (default) and UDP mode
2. ✅ All existing device configurations compile unchanged (backward compatibility)
3. ✅ Test room component with `use_udp: true` compiles successfully
4. ✅ Abstracted sensor ID remains consistent for PID controller references
5. ✅ Component documentation clearly explains v6 changes and variable contract
6. ✅ Rollback procedure is simple (git revert or use_udp: false)

**Estimated Effort:** 2-3 hours focused development work

---

**Ready for Implementation** ✅
