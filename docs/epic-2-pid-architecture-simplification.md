# Epic 2: PID Architecture Simplification - Technical Debt Reduction

## Document Information

| Field             | Value                                          |
| ----------------- | ---------------------------------------------- |
| **Epic**          | Epic 2: PID Architecture Simplification        |
| **Version**       | 1.1                                            |
| **Date**          | October 22, 2025 (Last Updated)                |
| **Status**        | In Progress                                    |
| **Story Manager** | Bob (Scrum Master)                             |
| **Product Owner** | Sarah (Product Owner)                          |
| **Progress**      | Story 2.1 Complete ✅ / Story 2.2 & 2.3 Pending |

---

## Epic Title

**PID Architecture Simplification** - Technical Debt Reduction

---

## Epic Goal

Eliminate unnecessary architectural complexity by replacing the `dual_pid.yaml` component pattern with standard ESPHome single PID climate controllers, reducing code maintenance burden and improving system clarity without changing functionality.

---

## Epic Description

### Current System Analysis

**Identified Technical Debt:**

The current system uses a `dual_pid.yaml` component that creates **two separate PID climate entities** per zone (one for heat, one for cool) with external automation (`valve_trigger.yaml`) to coordinate mode switching. This pattern introduces unnecessary complexity:

**Current Architecture:**
```yaml
# Creates TWO climate entities
packages:
  pid_heat: pid.yaml (mode: "heat")
  pid_cool: pid.yaml (mode: "cool")
  heat_trigger: valve_trigger.yaml (activates heat PID)
  cool_trigger: valve_trigger.yaml (activates cool PID)

climate:
  - pid_${circuit}_heat    # Entity 1: heat-only
  - pid_${circuit}_cool    # Entity 2: cool-only
```

**Problems:**
1. **Redundant Entities**: Two climate entities per zone when ESPHome PID supports both modes natively
2. **Complex Coordination**: External `valve_trigger` automation required to switch between PIDs
3. **Mutual Exclusion Logic**: Custom code in `pid.yaml` to turn off opposite mode
4. **Same Output**: Both PIDs control the same physical output, making separation pointless
5. **Maintenance Burden**: More components = more code to maintain and debug
6. **Home Assistant Clutter**: Double the climate entities exposed to HA

**Root Cause:**

The original architecture was designed for mixing valves with **physical pump trigger inputs** that determine when each mode can operate. However, this external trigger pattern is unnecessary - the standard ESPHome PID climate component can:
- Support both `heat_output` and `cool_output` natively
- Respond to mode changes via Home Assistant or automation
- Integrate with climate mode coordination through simple automation

### Proposed Solution

**Replace dual_pid pattern with single PID climate per zone:**

```yaml
# Single climate entity with both modes
climate:
  - platform: pid
    id: pid_${circuit}
    name: "PID ${circuit_name}"
    sensor: ${sensor}
    heat_output: ${output}
    cool_output: ${output}
    # ESPHome handles mode internally
```

**Mode Coordination:**

Instead of physical triggers, use simple automation based on global climate mode:

```yaml
# Simple automation - no separate trigger component needed
on_...:  # When climate_mode changes
  - climate.control:
      id: pid_${circuit}
      mode: !lambda 'return id(climate_mode).state == "heat" ? CLIMATE_MODE_HEAT : ...'
```

**Benefits:**
1. **Single Entity**: One climate entity per zone instead of two
2. **Standard ESPHome**: Uses native PID climate features, no custom coordination
3. **Less Code**: Eliminate `dual_pid.yaml` and `valve_trigger.yaml` components
4. **Clearer Intent**: Architecture matches actual system behavior
5. **Easier Debugging**: Fewer moving parts, simpler logic
6. **HA Simplification**: Half the climate entities to manage

### Scope

**Components to Remove:**
- `components/dual_pid.yaml` - Replaced by direct PID climate platform usage
- `components/valve_trigger.yaml` - No longer needed
- `components/mixing_valve.yaml` - Replaced by simplified single-PID pattern

**Components to Modify:**
- `devices/gruppo-miscelazione.yaml` - Update to use single PID per mixing valve
- `devices/distribuzione-piano-terra.yaml` - Update zone PIDs to single entity
- `devices/distribuzione-primo-piano.yaml` - Update zone PIDs to single entity

**New Components to Create:**
- `components/simple_pid.yaml` - Single PID with mode coordination (if reusable pattern emerges)
- Or inline PID definitions directly in device files for clarity

**Documentation to Update:**
- `docs/architecture.md` - Update PID control section
- `docs/epic-1-modbus-coordination.md` - Reference this epic for Story 1.6 changes
- `.github/copilot-instructions.md` - Update component patterns

---

## Stories

This epic consists of **3 focused stories** for incremental refactoring:

### 1. **Story 2.1: Mixing Valve PID Simplification (gruppo-miscelazione)**
   - Replace dual_pid pattern in mixing valve configuration
   - Create single PID climate per mixing valve (Piano Terra, Primo Piano)
   - Add climate mode coordination automation
   - Test in local environment before production
   - **Status**: ✅ Complete (Oct 22, 2025)
   - **Details**: See `docs/stories/2.1.mixing-valve-simplification.md`

### 2. **Story 2.2: Distribution Zone PID Simplification**
   - Update distribuzione-piano-terra.yaml zones
   - Update distribuzione-primo-piano.yaml zones
   - Maintain existing PID tuning parameters
   - Verify failover logic still works correctly
   - **Status**: ⏳ Not Started

### 3. **Story 2.3: Component Cleanup and Documentation**
   - Remove unused components (dual_pid.yaml, valve_trigger.yaml, mixing_valve.yaml)
   - Update architecture documentation
   - Update copilot instructions
   - Create migration guide for future component authors
   - **Status**: ⏳ Not Started

---

## Compatibility Requirements

- [x] **Existing functionality preserved**: All temperature control behavior remains identical
- [x] **Entity ID strategy**: New climate entity IDs will be `pid_${circuit}` (without `_heat`/`_cool` suffix)
  - **Note**: This is a breaking change for HA automations that reference old entity IDs
  - Migration plan required for HA dashboard/automation updates
- [x] **PID tuning unchanged**: All Kp, Ki, Kd parameters remain identical
- [x] **Output control identical**: Same physical outputs controlled in same way
- [x] **Performance impact**: Slight improvement (less entity overhead, simpler logic)

---

## Risk Mitigation

### Primary Risk
**Breaking existing Home Assistant automations/dashboards** that reference the dual PID climate entity IDs.

### Mitigation Strategy

1. **Inventory Phase** (Story 2.1):
   - Document all HA automations that reference old entity IDs
   - Create mapping: old entity IDs → new entity IDs
   - Test in development HA instance first

2. **Parallel Testing**:
   - Deploy to test board first (one mixing valve only)
   - Verify temperature control accuracy unchanged
   - Validate mode switching works correctly
   - Monitor for 48 hours before proceeding

3. **Gradual Rollout**:
   - Story 2.1: Mixing valves only (gruppo-miscelazione)
   - Story 2.2: Distribution zones (after mixing valve validation)
   - Each story includes HA automation update checklist

4. **Rollback Plan**:
   - Keep backup of old component files in `components/deprecated/`
   - Revert device YAML to use dual_pid pattern if issues found
   - OTA update back to previous firmware within minutes

### Home Assistant Migration Plan

**Before Deployment:**
1. Export all HA automations and dashboards
2. Search for entity ID references: `pid_*_heat`, `pid_*_cool`
3. Create update script or manual checklist

**After Deployment:**
1. Update HA automations to use new entity IDs
2. Update HA dashboards/cards
3. Update any Node-RED flows (if applicable)
4. Verify all climate controls still work

**Entity ID Mapping Example:**
```
OLD: climate.pid_piano_terra_heat    → NEW: climate.pid_piano_terra
OLD: climate.pid_piano_terra_cool    → NEW: climate.pid_piano_terra (same entity, different mode)
OLD: climate.pid_primo_piano_heat    → NEW: climate.pid_primo_piano
OLD: climate.pid_primo_piano_cool    → NEW: climate.pid_primo_piano
```

---

## Definition of Done

This epic is complete when:

- [ ] **All 3 stories completed** with acceptance criteria met
- [ ] **Existing functionality verified through testing**:
  - Temperature control accuracy maintained (±0.5°C)
  - PID tuning parameters work correctly
  - Mode switching (heat/cool) functions properly
  - Output control identical to before
- [ ] **Components removed**:
  - `components/dual_pid.yaml` deleted or moved to `deprecated/`
  - `components/valve_trigger.yaml` deleted or moved to `deprecated/`
  - `components/mixing_valve.yaml` simplified or removed
- [ ] **All devices updated**:
  - gruppo-miscelazione.yaml uses single PID pattern
  - distribuzione-piano-terra.yaml uses single PID pattern
  - distribuzione-primo-piano.yaml uses single PID pattern
- [ ] **Documentation updated**:
  - Architecture docs reflect new PID pattern
  - Copilot instructions updated
  - Migration guide created
- [ ] **Home Assistant integration working**:
  - All automations updated to new entity IDs
  - All dashboards updated
  - No broken climate controls
- [ ] **Production deployment successful**:
  - All boards running simplified architecture
  - 7-day monitoring period shows stable operation
  - No temperature control regressions

---

## Dependencies and Sequencing

### Epic Dependencies

```
Epic 1 (Modbus Coordination)
    │
    └──> Story 1.4 (Failover Logic) ──> COMPLETE
              │
              └──> Epic 2 can start (Independent refactoring)
```

**Note**: Epic 2 is **independent** from Epic 1 Stories 1.5-1.8. It can proceed in parallel or after Epic 1 completion.

### Story Dependencies

```
Story 2.1 (Mixing Valves) ──────────┐
                                     ├──> Story 2.3 (Cleanup)
Story 2.2 (Distribution Zones) ─────┘
```

**Critical Path**: Stories 2.1 and 2.2 can proceed in parallel on different device files, but both must complete before Story 2.3 cleanup.

---

## Technical Constraints

### Code Constraints

- **ESPHome Platform**: Must use standard ESPHome PID climate platform
- **Entity ID Length**: Keep entity IDs short for HA compatibility
- **Substitution Variables**: Maintain existing substitution pattern for consistency

### Testing Constraints

- **Production System**: Cannot test extensively in production without risk
- **Test Environment**: Need equivalent test setup or careful staging
- **Temperature Stability**: Must verify PID behavior over multiple heating/cooling cycles

### Migration Constraints

- **Home Assistant Downtime**: Entity ID changes require HA restart
- **Firmware Size**: Simplified code should reduce firmware size (not increase)
- **Backward Compatibility**: Cannot support old and new patterns simultaneously (clean break)

---

## Success Metrics

- **Code Reduction**: Remove ~150 lines of YAML (dual_pid + valve_trigger components)
- **Entity Count**: Reduce climate entities from 8 to 4 (gruppo-miscelazione + distribution zones)
- **Firmware Size**: Reduce by ~10KB (fewer entities, simpler logic)
- **Maintenance Time**: Easier to understand = faster future development
- **Bug Surface**: Fewer components = fewer places for bugs to hide

---

## Progress Update

### Story 2.1: Mixing Valve PID Simplification ✅ COMPLETE

**Completed**: October 22, 2025  
**Branch**: `bmad-epic-2`

**Implementation Summary:**
- ✅ Replaced `mixing_valve.yaml` component with direct PID climate configuration
- ✅ Removed dual_pid pattern (2 entities → 1 per circuit)
- ✅ Implemented mode coordination via `climate_mode` sensor
- ✅ Added PID output sensors for HA compatibility
- ✅ Configuration validates successfully
- ✅ Firmware compiles successfully

**Files Modified:**
1. `devices/gruppo-miscelazione.yaml` - Main refactor
   - Removed 2x mixing_valve package references
   - Added 2x simplified PID climate definitions
   - Added mode coordination automation
   - Net: ~66 lines removed, +73 lines added (simpler pattern)

2. `components/fancoil.yaml` - Fixed pre-existing bugs
   - Fixed indentation error in `on_state`
   - Fixed `binary_sensors` → `binary_sensor` typo
   - Reorganized packages section

3. `components/modbus_0_10v_output.yaml` - Architecture fix
   - Removed duplicate `modbus_controller` definition
   - Fixed template output `write_action` syntax
   - Updated documentation

**Entity ID Changes:**
| Old                                                              | New                       | Circuit     |
| ---------------------------------------------------------------- | ------------------------- | ----------- |
| `climate.pid_piano_terra_heat`<br>`climate.pid_piano_terra_cool` | `climate.pid_piano_terra` | Piano Terra |
| `climate.pid_primo_piano_heat`<br>`climate.pid_primo_piano_cool` | `climate.pid_primo_piano` | Primo Piano |
| `sensor.pid_*_output_heat`<br>`sensor.pid_*_output_cool`         | `sensor.pid_*_output`     | Both        |

**Next Steps:**
- ⚠️ Update Home Assistant automations before deployment
- ⚠️ Update HA dashboards to use new entity IDs
- Test mode switching in controlled environment
- Monitor temperature stability over 48 hours

**Metrics:**
- Climate entities reduced: 4 → 2 (50% reduction for gruppo-miscelazione)
- Component dependencies removed: 3 files (dual_pid, valve_trigger, mixing_valve)
- Code complexity: Significantly reduced (no mutual exclusion logic)

---

## Change Log

| Date       | Version | Description                           | Author                  |
| ---------- | ------- | ------------------------------------- | ----------------------- |
| 2025-10-21 | 1.0     | Epic created from architecture review | Mary (Business Analyst) |
| 2025-10-22 | 1.1     | Story 2.1 completed                   | Claude 3.5 Sonnet       |

---

## Notes

### Relationship to Epic 1 Story 1.6

Epic 1 Story 1.6 originally planned to "extend dual_pid component for mode-specific outputs" to support different outputs for heating (floor radiators) vs cooling (fancoils).

**With Epic 2 simplification:**
- Story 1.6 should use **single PID climate** with separate `heat_output` and `cool_output` parameters
- No dual_pid extension needed - standard ESPHome PID supports this natively
- Story 1.6 task list should be updated to remove dual_pid extension task

### Alternative Approach: Keep dual_pid for Story 1.6 Only

If Epic 2 is deemed too risky or time-consuming, an alternative is:
1. Keep existing dual_pid usage for mixing valves (gruppo-miscelazione)
2. Use single PID pattern ONLY for Story 1.6 ground floor fancoils
3. Accept mixed architecture temporarily
4. Defer full Epic 2 cleanup to future sprint

This allows Story 1.6 to proceed with simpler pattern without requiring full system refactoring.

---

## Story Manager Handoff

**This epic addresses technical debt identified during Epic 1 Story 1.6 planning.**

The current dual_pid pattern was designed for physical trigger inputs that are no longer necessary. Simplifying to standard ESPHome single PID climate will:
- Reduce maintenance burden
- Improve code clarity
- Eliminate unnecessary entity duplication
- Make future development easier

**Recommendation**: Start Story 2.1 after Epic 1 Story 1.4 completion, allowing parallel work on Story 1.5 and Epic 2.

**Risk Level**: Medium (entity ID changes affect HA integration)  
**Effort**: Small (mostly YAML refactoring, minimal logic changes)  
**Value**: High (simplifies all future PID-related development)
