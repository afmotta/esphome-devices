# Story 9.2: Occupancy Stub Component Implementation

**Epic:** 9 - Occupancy-Based Climate Shutdown  
**Story Points:** 1  
**Priority:** High  
**Status:** ❌ **CANCELLED - Home Assistant Implementation**  
**Cancellation Date:** October 2025  
**Owner:** Developer (James)

---

## ⚠️ CANCELLATION NOTICE

This story has been cancelled. Occupancy-based climate control will be implemented as **Home Assistant automations** rather than ESPHome firmware components. See Epic 9 brief for full rationale.

---

## ~~Original Story~~ (Preserved for Historical Reference)

---

## Story

**As a** room climate control system,  
**I want** a stub occupancy condition component for rooms without occupancy sensors,  
**so that** the coordinator can operate uniformly across all rooms while enabling gradual sensor rollout without modifying coordinator logic.

---

## Business Context

This story implements the "always-present" pattern from Epic 8, ensuring that all rooms expose occupancy condition globals regardless of whether they have actual occupancy sensors. This enables:

1. **Gradual Rollout:** Deploy occupancy detection room-by-room without system-wide changes
2. **Coordinator Simplicity:** Coordinator reads occupancy globals from all rooms without conditional logic
3. **Future Expansion:** Add occupancy sensors to stubbed rooms by replacing stub package (no coordinator changes)
4. **Consistent Interface:** All rooms conform to Epic 8 condition interface contract

**Value Delivered:**
- Enables phased Epic 9 deployment (test room → selected rooms → all rooms)
- Maintains coordinator simplicity (no "if room has occupancy" checks)
- Zero-cost for rooms without sensors (minimal globals, no polling logic)
- Future-proof: Stub → real component upgrade is trivial package swap

**Dependencies:**
- Story 9.1 completed (real occupancy component exists as reference)
- Epic 8 stub pattern proven (emergency_stub, window_stub in production)

---

## Acceptance Criteria

### AC1: Stub Component Structure and Minimal Interface

**Given** the Epic 8 condition interface specification,  
**When** `room_occupancy_condition_stub.yaml` is created,  
**Then** it MUST expose the required interface with minimal resource usage:

```yaml
# Room Occupancy Condition Stub Component (Epic 9)
#
# Provides minimal occupancy condition interface for rooms without
# occupancy sensors. Exposes always-Normal state (0) with low priority (99)
# to satisfy coordinator's always-present pattern.
#
# REQUIRED VARS:
#   zone_slug: Room identifier (e.g., "soggiorno")
#   zone_name: Room display name (e.g., "Soggiorno")
#
# INTERFACE (Epic 8 Contract):
#   Exposes: ${zone_slug}_occupancy_state = 0 (always Normal)
#   Exposes: ${zone_slug}_occupancy_priority = 99 (never active)
#
# BEHAVIOR:
#   - State: Always Normal (0) - never triggers shutdown
#   - Priority: 99 - coordinator ignores (far below real conditions 1-3)
#   - No polling, no HA sensors, no state machine logic
#
# USAGE EXAMPLE:
#   packages:
#     occupancy_condition:
#       file: ../../components/room_occupancy_condition_stub.yaml
#       vars:
#         zone_slug: "ripostiglio"
#         zone_name: "Ripostiglio"
#
# SEE ALSO:
#   - components/room_occupancy_condition.yaml - Real occupancy component
#   - components/room_emergency_condition_stub.yaml - Similar stub pattern
#   - components/room_window_condition_stub.yaml - Similar stub pattern

# Required globals (Epic 8 interface contract)
globals:
  - id: ${zone_slug}_occupancy_state
    type: int
    restore_value: false
    initial_value: "0"           # Always Normal (never Active/Recovering)
  
  - id: ${zone_slug}_occupancy_priority
    type: int
    restore_value: false
    initial_value: "99"          # Never active (far below real priorities 1-3)

# Optional: Diagnostic text sensor (for consistency with real component)
text_sensor:
  - platform: template
    id: ${zone_slug}_occupancy_state_sensor
    name: "${zone_name} Occupancy State"
    internal: true               # Not exposed to HA (stub doesn't provide value)
    lambda: |-
      return {"No Sensor (Stub)"};
```

**Validation:**
- [ ] Component compiles without errors
- [ ] Globals accessible via `id(${zone_slug}_occupancy_state)` in coordinator
- [ ] State global always returns 0
- [ ] Priority global always returns 99
- [ ] No interval polling logic present
- [ ] No homeassistant platform sensors
- [ ] Resource usage minimal (≤100 bytes RAM)

---

### AC2: Vars Interface Consistency

**Given** the real occupancy component requires specific vars,  
**When** the stub is configured,  
**Then** it MUST accept the same minimal vars for consistency:

```yaml
# Minimal vars interface (subset of real component)
vars:
  zone_slug: "ripostiglio"      # Required: Room identifier
  zone_name: "Ripostiglio"      # Required: Room display name
  # NOTE: Stub does NOT require:
  #   - ha_occupancy_sensor_id (no sensor to monitor)
  #   - unoccupied_timeout (no timeout logic)
```

**Rationale:** Stub requires only vars needed for globals naming (`zone_slug`) and optional diagnostics (`zone_name`). Sensor-specific vars are intentionally omitted to make stub usage clear.

**Validation:**
- [ ] Stub compiles with only `zone_slug` and `zone_name` vars
- [ ] No warnings about unused vars
- [ ] Clear distinction from real component (different required vars)

---

### AC3: Coordinator Integration - Always Ignored

**Given** the coordinator polls all condition states,  
**When** a room uses the occupancy stub,  
**Then** the coordinator MUST recognize but ignore the stub condition:

**Coordinator Priority Resolution Logic:**
```cpp
// Coordinator reads all condition states
int occupancy_state = id(${zone_slug}_occupancy_state);      // Stub: always 0
int occupancy_priority = id(${zone_slug}_occupancy_priority); // Stub: always 99

// Priority resolution (lowest number wins)
std::vector<std::pair<int, std::string>> active_conditions;

if (emergency_state > 0) 
  active_conditions.push_back({1, "Emergency"});
if (window_state > 0) 
  active_conditions.push_back({2, "Window"});
if (occupancy_state > 0) 
  active_conditions.push_back({99, "Occupancy"});  // Never true for stub (state=0)

// Stub never added to active_conditions (state always 0)
// If added (impossible), priority 99 ensures it never wins
```

**Expected Behavior:**
- Room with stub → Occupancy state always 0 → Never added to active conditions
- Room with real occupancy → State can be 1 (Active) → Added with priority 3
- Coordinator diagnostic never shows "Shutdown: Occupancy" for stubbed rooms

**Validation:**
- [ ] Coordinator reads stub globals without errors
- [ ] Stub never triggers PID shutdown (state always 0)
- [ ] Stub never appears in coordinator diagnostic (never active)
- [ ] Priority 99 ensures stub loses to any real condition (if logic bug causes state>0)

---

### AC4: Upgrade Path - Stub to Real Component

**Given** a room initially uses stub but later gets occupancy sensor,  
**When** the room configuration is updated,  
**Then** upgrading from stub to real component MUST be trivial:

**Before (Stub):**
```yaml
# devices/distribuzione-piano-terra.yaml
packages:
  # Room packages (existing)
  room_sensors:
    file: ../../components/room_sensors.yaml
    vars: { zone_slug: "ripostiglio", ... }
  
  room_emergency_condition:
    file: ../../components/room_emergency_condition.yaml
    vars: { zone_slug: "ripostiglio", ... }
  
  room_window_condition_stub:
    file: ../../components/room_window_condition_stub.yaml
    vars: { zone_slug: "ripostiglio", ... }
  
  # Stub occupancy (no sensor yet)
  room_occupancy_condition:
    file: ../../components/room_occupancy_condition_stub.yaml
    vars:
      zone_slug: "ripostiglio"
      zone_name: "Ripostiglio"
  
  room_control_coordinator:
    file: ../../components/room_control_coordinator.yaml
    vars: { zone_slug: "ripostiglio", ... }
```

**After (Real Sensor Added):**
```yaml
# devices/distribuzione-piano-terra.yaml
packages:
  # Room packages (unchanged)
  room_sensors:
    file: ../../components/room_sensors.yaml
    vars: { zone_slug: "ripostiglio", ... }
  
  room_emergency_condition:
    file: ../../components/room_emergency_condition.yaml
    vars: { zone_slug: "ripostiglio", ... }
  
  room_window_condition_stub:
    file: ../../components/room_window_condition_stub.yaml
    vars: { zone_slug: "ripostiglio", ... }
  
  # CHANGED: Stub → Real component
  room_occupancy_condition:
    file: ../../components/room_occupancy_condition.yaml  # Changed from _stub
    vars:
      zone_slug: "ripostiglio"
      zone_name: "Ripostiglio"
      ha_occupancy_sensor_id: "binary_sensor.ripostiglio_occupancy"  # Added
      unoccupied_timeout: "7200"                                      # Added
  
  room_control_coordinator:
    file: ../../components/room_control_coordinator.yaml  # Unchanged
    vars: { zone_slug: "ripostiglio", ... }
```

**Upgrade Requirements:**
1. Change file path: `_stub.yaml` → `.yaml`
2. Add required vars: `ha_occupancy_sensor_id`, optionally `unoccupied_timeout`
3. No coordinator changes required
4. OTA update deploys new firmware with real occupancy logic

**Validation:**
- [ ] Upgrade process documented in stub component header
- [ ] Test upgrade in single room (compile before/after)
- [ ] Verify OTA update succeeds
- [ ] Confirm occupancy detection works post-upgrade
- [ ] No entity_id conflicts (stub's internal sensor → real sensor)

---

### AC5: Resource Efficiency

**Given** stubbed rooms don't need occupancy detection,  
**When** stub is deployed,  
**Then** resource usage MUST be minimal:

**Resource Budget:**
- **Flash:** ≤200 bytes (2 globals + minimal template sensor)
- **RAM:** ≤100 bytes (2 int globals + optional string)
- **CPU:** 0% (no polling intervals, no lambdas)
- **Network:** 0 (no HA sensor subscriptions)

**Comparison to Real Component:**
- Real component: ~2KB flash, ~500 bytes RAM, 0.1% CPU (10s polling)
- Stub component: ~200 bytes flash, ~100 bytes RAM, 0% CPU (static only)
- **Savings:** 90% flash, 80% RAM, 100% CPU when sensor not needed

**Validation:**
- [ ] Firmware size increase ≤200 bytes per stubbed room
- [ ] Free heap unchanged (stub uses no dynamic allocation)
- [ ] No CPU usage measurable (no intervals)
- [ ] ESPHome logs show no stub-related polling

---

### AC6: Documentation and Usage Clarity

**Given** developers will choose between stub and real component,  
**When** reviewing component documentation,  
**Then** clear guidance MUST be provided:

**Component File Header (see AC1 for full header):**
- **When to use stub:** Room has no occupancy sensor and none planned
- **When to use real:** Room has HA occupancy sensor available
- **Upgrade path:** How to switch from stub → real when sensor added
- **Vars differences:** Stub requires fewer vars (zone_slug, zone_name only)

**Decision Matrix (to be included in Epic 9 migration guide):**

| Scenario                           | Component to Use                | Rationale                                  |
| ---------------------------------- | ------------------------------- | ------------------------------------------ |
| Room has PIR/mmWave sensor         | `room_occupancy_condition`      | Enable energy savings                      |
| Room has no sensor, none planned   | `room_occupancy_condition_stub` | Satisfy coordinator interface              |
| Room has no sensor, will add later | `room_occupancy_condition_stub` | Start with stub, upgrade when sensor ready |
| Testing occupancy logic            | `room_occupancy_condition`      | Use real component even if testing         |
| Disabling occupancy temporarily    | Keep real component             | Set `unoccupied_timeout` very high (24h)   |

**Validation:**
- [ ] Component header includes when-to-use guidance
- [ ] Migration guide documents stub vs. real decision process
- [ ] Examples show both stub and real component usage
- [ ] Upgrade path clearly documented

---

### AC7: Multi-Room Stub Deployment Test

**Given** multiple rooms may use stub during initial rollout,  
**When** 3+ rooms are configured with stub,  
**Then** system MUST operate correctly:

**Test Configuration:**
```yaml
# Scenario: 5 rooms total
# - 2 rooms with real occupancy (Soggiorno, Cucina)
# - 3 rooms with stub (Bagno, Ripostiglio, Anticamera)

# Soggiorno (real occupancy)
packages:
  room_occupancy_condition:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "soggiorno"
      ha_occupancy_sensor_id: "binary_sensor.soggiorno_occupancy"

# Cucina (real occupancy)
packages:
  room_occupancy_condition:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "cucina"
      ha_occupancy_sensor_id: "binary_sensor.cucina_occupancy"

# Bagno (stub)
packages:
  room_occupancy_condition:
    file: ../../components/room_occupancy_condition_stub.yaml
    vars:
      zone_slug: "bagno"

# Ripostiglio (stub)
packages:
  room_occupancy_condition:
    file: ../../components/room_occupancy_condition_stub.yaml
    vars:
      zone_slug: "ripostiglio"

# Anticamera (stub)
packages:
  room_occupancy_condition:
    file: ../../components/room_occupancy_condition_stub.yaml
    vars:
      zone_slug: "anticamera"
```

**Expected Behavior:**
- **Soggiorno:** Occupancy detection active, can trigger PID shutdown
- **Cucina:** Occupancy detection active, can trigger PID shutdown
- **Bagno:** No occupancy detection, PID operates normally
- **Ripostiglio:** No occupancy detection, PID operates normally
- **Anticamera:** No occupancy detection, PID operates normally
- **Coordinator:** Operates uniformly across all rooms (always reads occupancy globals)

**Validation:**
- [ ] Firmware compiles with 2 real + 3 stub occupancy conditions
- [ ] Real occupancy rooms show "Occupied" / "Unoccupied (Active)"
- [ ] Stub rooms show "No Sensor (Stub)" (internal only)
- [ ] Coordinator diagnostic correct for all rooms
- [ ] No global naming conflicts between stub and real components

---

## Integration Verification

### IV1: Existing Functionality Preserved

**Objective:** Ensure stub doesn't disrupt current operation

**Test Scenarios:**
1. **Room with stub occupancy + emergency condition:**
   - Emergency can still trigger (priority 1)
   - Stub occupancy never interferes (priority 99, state 0)
   - Coordinator diagnostic shows "Emergency" when triggered, not "Occupancy"

2. **Room with stub occupancy + window condition:**
   - Window can still trigger (priority 2)
   - Stub occupancy never interferes
   - Priority hierarchy intact

3. **Room with all stubs (emergency, window, occupancy):**
   - PID operates normally (no conditions ever active)
   - Coordinator shows "Normal (All Clear)"
   - Temperature control unaffected

**Validation Checklist:**
- [ ] All existing conditions (emergency, window) unaffected by stub
- [ ] Temperature control accuracy maintained (±0.5°C)
- [ ] No increase in coordinator polling time
- [ ] No unexpected warnings or errors

---

### IV2: Interface Contract Compliance

**Objective:** Validate stub conforms to Epic 8 interface

**Test Scenarios:**
1. **State global verification:**
   - `id(ripostiglio_occupancy_state)` readable from coordinator
   - Value is always 0 (never 1 or 2)
   - Value persists across reboots (restore_value=false means starts at 0)

2. **Priority global verification:**
   - `id(ripostiglio_occupancy_priority)` readable from coordinator
   - Value is always 99 (far below real priorities 1-3)

3. **Coordinator recognition:**
   - Coordinator reads stub globals without errors
   - Stub never triggers coordinator shutdown (state always 0)
   - Coordinator diagnostic never mentions "Occupancy" for stubbed rooms

**Validation Checklist:**
- [ ] Globals accessible from coordinator lambdas
- [ ] State always 0, priority always 99
- [ ] Coordinator logs show stub globals read successfully
- [ ] Interface contract compliance checklist 100% pass
- [ ] Stub behavior identical to Epic 8 emergency/window stubs

---

### IV3: Stub vs. Real Component Coexistence

**Objective:** Validate mixed stub/real deployments

**Test Configuration:**
```yaml
# Device: distribuzione-piano-terra.yaml (4 rooms)

# Soggiorno: Real occupancy (priority 3)
packages:
  room_occupancy_condition_soggiorno:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "soggiorno"
      ha_occupancy_sensor_id: "binary_sensor.soggiorno_occupancy"
      unoccupied_timeout: "7200"

# Cucina: Stub occupancy (priority 99)
packages:
  room_occupancy_condition_cucina:
    file: ../../components/room_occupancy_condition_stub.yaml
    vars:
      zone_slug: "cucina"

# Bagno: Real occupancy (priority 3)
packages:
  room_occupancy_condition_bagno:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "bagno"
      ha_occupancy_sensor_id: "binary_sensor.bagno_occupancy"
      unoccupied_timeout: "900"  # 15 min (bathroom)

# Anticamera: Stub occupancy (priority 99)
packages:
  room_occupancy_condition_anticamera:
    file: ../../components/room_occupancy_condition_stub.yaml
    vars:
      zone_slug: "anticamera"
```

**Test Sequence:**
1. **Soggiorno unoccupied >2h:**
   - [ ] Soggiorno PID shuts down (real occupancy active)
   - [ ] Cucina PID continues (stub never active)
   - [ ] Coordinator: Soggiorno shows "Shutdown: Occupancy (Active)"
   - [ ] Coordinator: Cucina shows "Normal (All Clear)"

2. **Bagno unoccupied >15min:**
   - [ ] Bagno PID shuts down (real occupancy active)
   - [ ] Anticamera PID continues (stub never active)
   - [ ] Both real occupancy rooms can be Active simultaneously

3. **All rooms occupied:**
   - [ ] All PIDs operating normally
   - [ ] Real occupancy rooms show "Occupied"
   - [ ] Stub rooms show "No Sensor (Stub)" (internal)
   - [ ] Coordinator shows "Normal (All Clear)" for all

**Validation Checklist:**
- [ ] Real and stub components coexist without conflicts
- [ ] Each room's occupancy state independent
- [ ] Coordinator handles mixed stub/real correctly
- [ ] No entity_id conflicts
- [ ] No global naming conflicts

---

### IV4: Performance Impact

**Objective:** Validate stub has zero overhead

**Measurements:**
1. **Firmware Size:**
   - [ ] Baseline firmware size (no occupancy components)
   - [ ] Firmware with 3 stub components (+200 bytes per stub)
   - [ ] Firmware with 3 real components (+2KB per real)
   - [ ] Confirm stub overhead ~90% less than real

2. **Runtime Performance:**
   - [ ] CPU usage identical to baseline (stub has no intervals)
   - [ ] RAM usage +100 bytes per stub (2 int globals)
   - [ ] No increase in coordinator polling time

3. **OTA Update:**
   - [ ] OTA update speed unchanged (firmware size increase minimal)
   - [ ] No OTA failures due to stub addition

**Validation Checklist:**
- [ ] Performance measurements documented
- [ ] Stub overhead negligible (≤1% firmware size per room)
- [ ] No measurable CPU/RAM impact
- [ ] OTA updates succeed reliably

---

## Definition of Done

**This story is complete when:**

- [ ] `components/room_occupancy_condition_stub.yaml` created and documented
- [ ] All 7 acceptance criteria validated and passing
- [ ] Epic 8 interface contract compliance verified (state=0, priority=99)
- [ ] Multi-room test (2 real + 3 stub) deployed and validated
- [ ] Stub never triggers PID shutdown (state always 0)
- [ ] Upgrade path from stub → real component tested
- [ ] Component header documentation complete with usage guidance
- [ ] Code review completed
- [ ] Performance measurements confirm zero overhead
- [ ] Story completion notes document stub behavior

**Ready for Story 9.3:** Single-room validation (test room deployment with real occupancy)

---

## Technical Notes

### Implementation Approach

**Complete Stub Component:**
```yaml
# components/room_occupancy_condition_stub.yaml

# [Full header documentation from AC1]

# Required globals (Epic 8 interface contract)
globals:
  - id: ${zone_slug}_occupancy_state
    type: int
    restore_value: false
    initial_value: "0"           # Always Normal
  
  - id: ${zone_slug}_occupancy_priority
    type: int
    restore_value: false
    initial_value: "99"          # Never wins priority

# Optional: Diagnostic text sensor (internal only)
text_sensor:
  - platform: template
    id: ${zone_slug}_occupancy_state_sensor
    name: "${zone_name} Occupancy State"
    internal: true               # Not exposed to HA
    lambda: |-
      return {"No Sensor (Stub)"};
```

**Key Design Decisions:**
1. **No interval polling:** Stub is static, no need for periodic updates
2. **Priority 99:** Ensures stub never wins if logic bug causes state>0
3. **Internal text sensor:** Provides consistency but doesn't clutter HA
4. **No HA sensor:** Stub explicitly avoids sensor dependency
5. **Minimal vars:** Only zone_slug and zone_name (no sensor-specific vars)

---

## Testing Strategy

### Unit Testing (Stub Component Level)

**Test 1: Static State**
- Deploy stub → Verify state always 0 (read global 100 times)

**Test 2: Static Priority**
- Deploy stub → Verify priority always 99 (read global 100 times)

**Test 3: Coordinator Reads**
- Coordinator polls stub globals → No errors, values correct

**Test 4: Resource Usage**
- Measure RAM before/after stub → Confirm ≤100 bytes increase

### Integration Testing (Mixed Deployment)

**Test 5: Stub + Real Coexistence**
- 2 real + 2 stub in same device → Both types work independently

**Test 6: Stub Never Triggers**
- Run for 24 hours → Stub never appears in coordinator diagnostic

**Test 7: Upgrade Path**
- Stub → Real component swap → Verify seamless transition

### Production Validation

**Test 8: System-Wide Stub Rollout**
- Deploy stub to 10+ rooms without sensors
- Monitor for 1 week
- Confirm zero performance impact, zero false triggers

---

## Dependencies

**Requires (must be complete first):**
- ✅ Story 9.1: Occupancy condition component (real component as reference)
- ✅ Epic 8 stub pattern (emergency_stub, window_stub proven in production)

**Blocks (waiting on this story):**
- ⏳ Story 9.3: Single-room validation (needs both real and stub available)
- ⏳ Story 9.4: Multi-room rollout (needs stub for rooms without sensors)

---

## Risks and Mitigations

**Risk 1: Stub vs. Real Confusion**
- **Description:** Developer uses stub when real component intended
- **Likelihood:** Low (clear file naming: `_stub.yaml`)
- **Impact:** Medium (no occupancy detection when expected)
- **Mitigation:** Clear documentation, distinct file names, usage guidance in headers
- **Detection:** Energy monitoring shows no savings in rooms expected to save

**Risk 2: Upgrade Path Issues**
- **Description:** Stub → real upgrade causes entity_id conflicts
- **Likelihood:** Low (stub sensor is internal=true)
- **Impact:** Low (OTA update fails, rollback needed)
- **Mitigation:** Test upgrade path in Story 9.2 completion
- **Detection:** Compilation errors when switching components

**Risk 3: Global Naming Conflicts**
- **Description:** Stub and real use same global names, causing overwrite
- **Likelihood:** Very Low (both use same naming convention by design)
- **Impact:** Low (correct behavior: single component per room)
- **Mitigation:** Both components use identical global naming (intentional)
- **Note:** Only one component (stub OR real) should be included per room

---

## Story Completion Notes

*[To be filled in by developer upon completion]*

**Implementation Summary:**
- Actual implementation time: ___ hours
- Deviations from acceptance criteria: ___
- Bugs found during testing: ___
- Resource usage measurements: ___

**Lessons Learned:**
- Stub pattern effectiveness: ___
- Upgrade path validation: ___
- Recommendations for Story 9.3: ___

**Artifacts Created:**
- Component file: `components/room_occupancy_condition_stub.yaml`
- Test results (2 real + 3 stub deployment): ___
- Performance measurements: ___

---

**Story Status:** Ready for Development  
**Dependencies:** Story 9.1 (Occupancy Condition Component)  
**Next Story:** 9.3 - Single-Room Validation (Test Room Deployment)

---

*Story created for Epic 9: Occupancy-Based Climate Shutdown*  
*Story Date: November 5, 2025*
