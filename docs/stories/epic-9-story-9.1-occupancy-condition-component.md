# Story 9.1: Occupancy Condition Component Implementation

**Epic:** 9 - Occupancy-Based Climate Shutdown  
**Story Points:** 2  
**Priority:** High  
**Status:** ❌ **CANCELLED - Home Assistant Implementation**  
**Cancellation Date:** October 2025  
**Owner:** Developer (James)

---

## ⚠️ CANCELLATION NOTICE

This story has been cancelled. Occupancy-based climate control will be implemented as **Home Assistant automations** rather than ESPHome firmware components. See Epic 9 brief for full rationale.

---

## ~~Original Story~~ (Preserved for Historical Reference)

**As a** room climate control system,  
**I want** an occupancy condition component that monitors HA occupancy sensors and triggers PID shutdown after configurable unoccupied periods,  
**so that** I can automatically save energy in empty rooms while maintaining the Epic 8 coordinator interface contract.

---

## Business Context

This story implements the core Epic 9 deliverable: a new condition component that extends the Epic 8 coordinator architecture with occupancy-based shutdown capability. By conforming to the Epic 8 condition interface contract (state+priority globals), this component integrates seamlessly with the existing coordinator across all 15+ rooms without requiring any coordinator modifications.

**Value Delivered:**
- Foundation for 10-20% HVAC energy savings through automated unoccupied room shutdown
- Validates Epic 8's extensibility promise (condition additions with zero coordinator changes)
- Enables gradual rollout (test room → full system) via component inclusion

**Dependencies:**
- Epic 8 completed (coordinator proven across 15+ rooms)
- HA occupancy sensors already deployed and stable
- Room device YAML structure supports package inclusion

---

## Acceptance Criteria

### AC1: Component Structure and Interface Compliance

**Given** the Epic 8 condition interface specification,  
**When** `room_occupancy_condition.yaml` is created,  
**Then** it MUST expose the following interface:

```yaml
# Required globals (Epic 8 interface contract)
globals:
  - id: ${zone_slug}_occupancy_state        # int: 0=Normal, 1=Active, 2=Recovering
    type: int
    restore_value: false
    initial_value: "0"
  
  - id: ${zone_slug}_occupancy_priority     # int: 3 (below emergency=1, window=2)
    type: int
    restore_value: false
    initial_value: "3"

# Required diagnostic sensor
text_sensor:
  - platform: template
    id: ${zone_slug}_occupancy_state_sensor
    name: "${zone_name} Occupancy State"
    # Values: "Occupied" / "Unoccupied (Active)" / "Resuming"
```

**Validation:**
- [ ] Component compiles without errors
- [ ] Globals are accessible via `id(${zone_slug}_occupancy_state)` in lambdas
- [ ] Text sensor exposed to Home Assistant with correct entity_id
- [ ] Interface contract checklist from `epic-8-condition-interface-spec.md` passes 100%

---

### AC2: Home Assistant Occupancy Sensor Integration

**Given** a Home Assistant occupancy sensor entity,  
**When** the component is configured with `ha_occupancy_sensor_id` var,  
**Then** it MUST monitor the sensor state correctly:

```yaml
# Component vars interface
vars:
  zone_slug: "soggiorno"                          # Required: Room identifier
  zone_name: "Soggiorno"                          # Required: Room display name
  ha_occupancy_sensor_id: "binary_sensor.soggiorno_occupancy"  # Required: HA entity
  unoccupied_timeout: "7200"                      # Optional: Seconds (default 2 hours)
  
# HA sensor integration
binary_sensor:
  - platform: homeassistant
    id: ${zone_slug}_occupancy_sensor
    entity_id: ${ha_occupancy_sensor_id}
    # Monitors: true=occupied, false=unoccupied
```

**Validation:**
- [ ] Component reads HA binary_sensor state correctly
- [ ] Supports both binary_sensor (true/false) and sensor (1/0) entity types
- [ ] Handles sensor unavailable state gracefully (assume occupied, don't shutdown)
- [ ] Sensor state changes logged at DEBUG level

---

### AC3: Unoccupied Timeout State Machine

**Given** the occupancy sensor reports "unoccupied" (false),  
**When** the unoccupied duration exceeds `unoccupied_timeout` (default 2 hours),  
**Then** the condition MUST transition to Active state:

**State Machine Logic:**
```cpp
// Polling interval: 10 seconds
interval:
  - interval: 10s
    then:
      - lambda: |-
          bool is_occupied = id(${zone_slug}_occupancy_sensor).state;
          int current_state = id(${zone_slug}_occupancy_state);
          
          if (is_occupied) {
            // Room occupied → Normal or immediate recovery
            if (current_state == 1) {  // Active → Recovering
              id(${zone_slug}_occupancy_state) = 2;
              id(${zone_slug}_occupancy_state_sensor).publish_state("Resuming");
            } else if (current_state == 2) {  // Recovering → Normal (immediate)
              id(${zone_slug}_occupancy_state) = 0;
              id(${zone_slug}_occupancy_state_sensor).publish_state("Occupied");
            }
            // Reset unoccupied timer
            unoccupied_seconds = 0;
          } else {
            // Room unoccupied → increment timer
            if (current_state == 0) {  // Normal → check timeout
              unoccupied_seconds += 10;
              if (unoccupied_seconds >= ${unoccupied_timeout}) {
                // Transition to Active
                id(${zone_slug}_occupancy_state) = 1;
                id(${zone_slug}_occupancy_state_sensor).publish_state("Unoccupied (Active)");
                ESP_LOGW("occupancy", "${zone_name}: Unoccupied timeout reached, PID shutdown triggered");
              }
            }
          }
```

**State Transitions:**
```
Normal (0) ─[unoccupied >timeout]→ Active (1)
Active (1) ─[room occupied]→ Recovering (2)
Recovering (2) ─[immediate, 0s]→ Normal (0)
```

**Validation:**
- [ ] State remains Normal (0) while room occupied
- [ ] State remains Normal (0) while unoccupied <timeout
- [ ] State transitions to Active (1) when unoccupied ≥timeout
- [ ] State transitions to Recovering (2) immediately when room becomes occupied (from Active)
- [ ] State transitions to Normal (0) immediately from Recovering (no 60s wait)
- [ ] Unoccupied timer resets to 0 when room becomes occupied

---

### AC4: Immediate Recovery Behavior

**Given** the occupancy condition is in Active state (PID OFF),  
**When** the room becomes occupied (sensor changes to true),  
**Then** recovery MUST be immediate (0 seconds, no stability period):

**Recovery Logic:**
```cpp
// No recovery timeout (different from emergency/window)
if (is_occupied && current_state == 1) {  // Active
  id(${zone_slug}_occupancy_state) = 2;   // → Recovering
  id(${zone_slug}_occupancy_state_sensor).publish_state("Resuming");
}

if (current_state == 2) {  // Recovering
  // Immediate transition to Normal (no 60s wait)
  id(${zone_slug}_occupancy_state) = 0;
  id(${zone_slug}_occupancy_state_sensor).publish_state("Occupied");
}
```

**Rationale:** Unlike sensor failures (emergency) or window state (needs stability), occupancy detection is reliable. Users expect immediate climate resumption when entering room.

**Validation:**
- [ ] Transition Recovering → Normal happens in next polling cycle (≤10s)
- [ ] No 60-second recovery timeout enforced
- [ ] Text sensor shows "Occupied" immediately after recovery completes
- [ ] Coordinator resumes PID control within 15 seconds total (10s occupancy poll + 5s coordinator poll)

---

### AC5: Configurable Timeout Per Room

**Given** different room types have different occupancy patterns,  
**When** the component is included in room device YAML,  
**Then** timeout MUST be configurable via vars with sensible default:

```yaml
# Example usage in device YAML
packages:
  occupancy_condition:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "bagno"
      zone_name: "Bagno"
      ha_occupancy_sensor_id: "binary_sensor.bagno_occupancy"
      unoccupied_timeout: "900"   # 15 minutes (bathroom = short timeout)
      
  occupancy_condition_guest:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "camera_ospiti"
      zone_name: "Camera Ospiti"
      ha_occupancy_sensor_id: "binary_sensor.camera_ospiti_occupancy"
      unoccupied_timeout: "14400"  # 4 hours (guest room = long timeout)
```

**Default Timeout:** 7200 seconds (2 hours)

**Validation:**
- [ ] Component accepts `unoccupied_timeout` var (integer seconds)
- [ ] Default value 7200s used if var not provided
- [ ] Timeout range validated: 60s minimum, 86400s (24h) maximum
- [ ] Invalid timeout logs warning and falls back to default

---

### AC6: Diagnostic and Observability

**Given** the need to debug occupancy-based shutdowns,  
**When** the component is operating,  
**Then** it MUST provide comprehensive diagnostics:

```yaml
# Required diagnostic sensors
text_sensor:
  - platform: template
    id: ${zone_slug}_occupancy_state_sensor
    name: "${zone_name} Occupancy State"
    # Shows: "Occupied" | "Unoccupied (Active)" | "Resuming"

# Optional detailed diagnostics
sensor:
  - platform: template
    id: ${zone_slug}_unoccupied_duration
    name: "${zone_name} Unoccupied Duration"
    unit_of_measurement: "s"
    accuracy_decimals: 0
    # Shows seconds since room became unoccupied (0 if occupied)
    
binary_sensor:
  - platform: homeassistant
    id: ${zone_slug}_occupancy_sensor
    name: "${zone_name} Occupancy Sensor"
    entity_id: ${ha_occupancy_sensor_id}
    # Mirror HA sensor state for debugging
```

**Logging Requirements:**
- State transitions logged at WARN level: `"${zone_name}: Normal → Active (unoccupied 2h 5m)"`
- Sensor state changes logged at DEBUG level: `"${zone_name}: Occupancy sensor: true → false"`
- Configuration logged at INFO level: `"${zone_name}: Occupancy timeout: 7200s (2h)"`

**Validation:**
- [ ] Text sensor updates within 10 seconds of state transitions
- [ ] Unoccupied duration sensor increments every 10 seconds when unoccupied
- [ ] Unoccupied duration resets to 0 when room becomes occupied
- [ ] Logs visible in ESPHome logger and HA logs
- [ ] All entities exposed to HA with correct entity_ids

---

### AC7: Sensor Unavailability Handling

**Given** the HA occupancy sensor may become unavailable,  
**When** the sensor state is "unavailable" or "unknown",  
**Then** the component MUST fail-safe (assume occupied, don't shutdown):

```cpp
// Safe default behavior
if (!id(${zone_slug}_occupancy_sensor).has_state()) {
  // Sensor unavailable → assume occupied (safe default)
  ESP_LOGW("occupancy", "${zone_name}: Occupancy sensor unavailable, assuming occupied");
  unoccupied_seconds = 0;
  if (current_state != 0) {
    id(${zone_slug}_occupancy_state) = 0;  // Force Normal
    id(${zone_slug}_occupancy_state_sensor).publish_state("Occupied (Sensor Unavailable)");
  }
  return;
}
```

**Validation:**
- [ ] When sensor unavailable, state forced to Normal (0)
- [ ] Unoccupied timer resets to 0 when sensor unavailable
- [ ] Warning logged when sensor becomes unavailable
- [ ] Text sensor shows "Occupied (Sensor Unavailable)" for visibility
- [ ] When sensor recovers, normal operation resumes

---

### AC8: Component Documentation

**Given** future developers will add occupancy detection to new rooms,  
**When** the component is complete,  
**Then** comprehensive documentation MUST be included:

**Component File Header:**
```yaml
# Room Occupancy Condition Component (Epic 9)
#
# Monitors Home Assistant occupancy sensors and triggers PID shutdown
# after configurable unoccupied timeout. Conforms to Epic 8 condition
# interface contract (state+priority globals).
#
# REQUIRED VARS:
#   zone_slug: Room identifier (e.g., "soggiorno")
#   zone_name: Room display name (e.g., "Soggiorno")
#   ha_occupancy_sensor_id: HA occupancy entity (e.g., "binary_sensor.soggiorno_occupancy")
#
# OPTIONAL VARS:
#   unoccupied_timeout: Seconds before shutdown (default: 7200 = 2 hours)
#
# INTERFACE (Epic 8 Contract):
#   Exposes: ${zone_slug}_occupancy_state (0=Normal, 1=Active, 2=Recovering)
#   Exposes: ${zone_slug}_occupancy_priority (=3, below emergency=1, window=2)
#
# BEHAVIOR:
#   - State: Normal (0) when room occupied or recently occupied
#   - State: Active (1) when unoccupied >timeout (coordinator forces PID OFF)
#   - State: Recovering (2) when room becomes occupied (immediate resume)
#   - Recovery timeout: 0s (immediate Normal transition, no stability period)
#
# USAGE EXAMPLE:
#   packages:
#     occupancy_condition:
#       file: ../../components/room_occupancy_condition.yaml
#       vars:
#         zone_slug: "soggiorno"
#         zone_name: "Soggiorno"
#         ha_occupancy_sensor_id: "binary_sensor.soggiorno_occupancy"
#         unoccupied_timeout: "3600"  # 1 hour
#
# SEE ALSO:
#   - docs/epic-9-brief.md - Epic overview
#   - docs/epic-8-condition-interface-spec.md - Interface contract
#   - components/room_emergency_condition.yaml - Similar pattern (priority 1)
#   - components/room_window_condition.yaml - Similar pattern (priority 2)
```

**Validation:**
- [ ] Header comment includes all required information
- [ ] Usage example is copy-paste ready
- [ ] References to related documentation accurate
- [ ] Vars interface clearly documented

---

## Integration Verification

### IV1: Existing Functionality Preserved

**Objective:** Ensure no disruption to current system operation

**Test Scenarios:**
1. **Room without occupancy condition:**
   - PID control continues using existing logic
   - Temperature accuracy maintained (±0.5°C)
   - Emergency and window conditions unaffected

2. **Coordinator operation:**
   - No modifications made to `room_control_coordinator.yaml`
   - Coordinator continues polling at 5-second interval
   - Other conditions (emergency, window) operate normally

3. **HA integration:**
   - Existing climate entities unchanged
   - Temperature sensors continue reporting
   - No entity_id conflicts introduced

**Validation Checklist:**
- [ ] Compile all existing device configurations successfully
- [ ] No errors in ESPHome logs for rooms without occupancy
- [ ] Temperature control accuracy unchanged across all rooms
- [ ] Coordinator diagnostic shows correct state for all rooms

---

### IV2: Interface Contract Compliance

**Objective:** Validate Epic 8 condition interface conformance

**Test Scenarios:**
1. **State global verification:**
   - `id(soggiorno_occupancy_state)` readable in coordinator
   - Value is 0 (Normal) when room occupied
   - Value is 1 (Active) when room unoccupied >timeout
   - Value is 2 (Recovering) during resume (immediate)

2. **Priority global verification:**
   - `id(soggiorno_occupancy_priority)` readable in coordinator
   - Value is 3 (below emergency=1, window=2)
   - Value remains constant (static priority for MVP)

3. **Coordinator integration:**
   - Coordinator polls occupancy globals automatically
   - Priority hierarchy enforced: Emergency > Window > Occupancy
   - Coordinator diagnostic shows "Shutdown: Occupancy (Active)"

**Validation Checklist:**
- [ ] Globals accessible from coordinator lambdas
- [ ] State enum values correct (0/1/2)
- [ ] Priority value correct (3)
- [ ] Coordinator recognizes occupancy condition without modifications
- [ ] Interface contract compliance checklist 100% pass

---

### IV3: Single-Room End-to-End Test

**Objective:** Validate complete shutdown→resume cycle in test room (Soggiorno)

**Test Room Configuration:**
```yaml
# devices/distribuzione-piano-terra.yaml (partial)
packages:
  # Existing packages (unchanged)
  room_sensors:
    file: ../../components/room_sensors.yaml
    vars: { zone_slug: "soggiorno", ... }
  
  room_emergency_condition:
    file: ../../components/room_emergency_condition.yaml
    vars: { zone_slug: "soggiorno", ... }
    
  room_window_condition:
    file: ../../components/room_window_condition.yaml
    vars: { zone_slug: "soggiorno", ... }
  
  # NEW: Occupancy condition
  room_occupancy_condition:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      ha_occupancy_sensor_id: "binary_sensor.soggiorno_occupancy"
      unoccupied_timeout: "300"  # 5 minutes for testing (not 2 hours)
  
  room_control_coordinator:
    file: ../../components/room_control_coordinator.yaml
    vars: { zone_slug: "soggiorno", ... }
```

**Test Sequence:**
1. **Initial State (Room Occupied):**
   - [ ] HA occupancy sensor: `true` (occupied)
   - [ ] Occupancy state: 0 (Normal)
   - [ ] Text sensor: "Occupied"
   - [ ] PID control: Operating normally
   - [ ] Coordinator diagnostic: "Normal (All Clear)"

2. **Trigger Unoccupied (T+0m):**
   - [ ] Change HA occupancy sensor to `false` (simulate leaving room)
   - [ ] Occupancy state: Still 0 (Normal, within timeout)
   - [ ] Text sensor: Still "Occupied"
   - [ ] PID control: Still operating
   - [ ] Unoccupied duration sensor: Starts incrementing (10s, 20s, 30s...)

3. **Timeout Exceeded (T+5m):**
   - [ ] Unoccupied duration: 300s (5 minutes)
   - [ ] Occupancy state: 1 (Active)
   - [ ] Text sensor: "Unoccupied (Active)"
   - [ ] Coordinator state: "Shutdown: Occupancy (Active)"
   - [ ] PID control: OFF (forced by coordinator)
   - [ ] Log entry: "Soggiorno: Unoccupied timeout reached, PID shutdown triggered"

4. **Room Becomes Occupied (T+10m):**
   - [ ] Change HA occupancy sensor to `true`
   - [ ] Occupancy state: 2 (Recovering) immediately
   - [ ] Text sensor: "Resuming"
   - [ ] Next poll cycle (≤10s): State 0 (Normal)
   - [ ] Text sensor: "Occupied"
   - [ ] Coordinator state: "Normal (All Clear)" (within 15s total)
   - [ ] PID control: Resumed (heating/cooling per setpoint)
   - [ ] Unoccupied duration: Reset to 0

5. **Priority Hierarchy Test:**
   - [ ] Simulate sensor failure (emergency state=1) while occupancy active (state=1)
   - [ ] Coordinator shows "Shutdown: Emergency (Active)" (priority 1 wins)
   - [ ] Fix sensor → Emergency clears → Coordinator shows "Shutdown: Occupancy (Active)"
   - [ ] Room occupied → Occupancy clears → Coordinator shows "Normal (All Clear)"

**Validation Checklist:**
- [ ] Complete test sequence passes without errors
- [ ] State transitions occur within expected timing (±5s)
- [ ] PID shutdown confirmed (heating/cooling stops)
- [ ] PID resume confirmed (heating/cooling restarts)
- [ ] Priority hierarchy correctly enforced
- [ ] No unexpected warnings or errors in logs

---

### IV4: Performance and Resource Impact

**Objective:** Validate acceptable performance impact

**Measurements:**
1. **Firmware Size:**
   - [ ] Compiled firmware size increase documented
   - [ ] Flash usage remains within ESP32 limits (≤90% capacity)
   
2. **Memory Usage:**
   - [ ] RAM usage increase measured (globals + lambdas)
   - [ ] Free heap remains >20KB during operation

3. **CPU Usage:**
   - [ ] Polling overhead ≤1% CPU (10s interval is low-frequency)
   - [ ] No impact on PID control loop timing

4. **Response Time:**
   - [ ] Occupancy detection latency: ≤10s (polling interval)
   - [ ] Coordinator recognition: ≤5s (coordinator polling)
   - [ ] Total shutdown/resume delay: ≤15s (acceptable for energy savings)

**Validation Checklist:**
- [ ] Performance metrics documented in story completion notes
- [ ] No degradation in temperature control accuracy
- [ ] No increase in OTA update failures
- [ ] System remains responsive to user commands

---

## Definition of Done

**This story is complete when:**

- [ ] `components/room_occupancy_condition.yaml` created and documented
- [ ] All 8 acceptance criteria validated and passing
- [ ] Epic 8 interface contract compliance verified (state+priority globals)
- [ ] Single test room (Soggiorno) deployed and validated
- [ ] Complete shutdown→resume cycle tested successfully
- [ ] Priority hierarchy tested (occupancy < emergency, window)
- [ ] No modifications made to `room_control_coordinator.yaml`
- [ ] Component header documentation complete with usage example
- [ ] Code review completed (self-review + peer review if available)
- [ ] ESPHome logs reviewed (no warnings or errors)
- [ ] Performance impact measured and documented
- [ ] Story completion notes document any learnings or deviations

**Ready for Story 9.2:** Occupancy stub component implementation

---

## Technical Notes

### Implementation Approach

**Recommended Structure:**
```yaml
# components/room_occupancy_condition.yaml

# 1. Substitutions (defaults)
substitutions:
  unoccupied_timeout: "7200"  # 2 hours default

# 2. Globals (Epic 8 interface)
globals:
  - id: ${zone_slug}_occupancy_state
    type: int
    restore_value: false
    initial_value: "0"
  - id: ${zone_slug}_occupancy_priority
    type: int
    restore_value: false
    initial_value: "3"
  - id: ${zone_slug}_unoccupied_seconds
    type: int
    restore_value: false
    initial_value: "0"

# 3. HA sensor integration
binary_sensor:
  - platform: homeassistant
    id: ${zone_slug}_occupancy_sensor
    entity_id: ${ha_occupancy_sensor_id}

# 4. State machine logic
interval:
  - interval: 10s
    then:
      - lambda: |-
          // Full state machine implementation here
          // (see AC3 for logic)

# 5. Diagnostic sensors
text_sensor:
  - platform: template
    id: ${zone_slug}_occupancy_state_sensor
    name: "${zone_name} Occupancy State"

sensor:
  - platform: template
    id: ${zone_slug}_unoccupied_duration
    name: "${zone_name} Unoccupied Duration"
    unit_of_measurement: "s"
    lambda: |-
      return id(${zone_slug}_unoccupied_seconds);
```

**Key Considerations:**
- Use `interval` platform (not `time` component) for polling simplicity
- Store unoccupied seconds in global for persistence across lambda calls
- Use `has_state()` to check sensor availability before reading
- Log state transitions at appropriate levels (WARN for state changes, DEBUG for sensor reads)
- Keep diagnostic sensors `internal: false` for HA visibility

---

## Testing Strategy

### Unit Testing (Component Level)

**Test 1: Normal State Maintenance**
- Room occupied → State stays 0 for extended period
- Verify unoccupied_seconds stays 0

**Test 2: Unoccupied Timer Increment**
- Room unoccupied (but <timeout) → State stays 0
- Verify unoccupied_seconds increments by 10 each cycle

**Test 3: Active State Trigger**
- Room unoccupied ≥timeout → State transitions 0 → 1
- Verify text sensor updates to "Unoccupied (Active)"

**Test 4: Immediate Recovery**
- Room occupied (from Active) → State transitions 1 → 2 → 0
- Verify <10s recovery (no 60s wait)

**Test 5: Timer Reset**
- Room occupied → Verify unoccupied_seconds resets to 0

**Test 6: Sensor Unavailable**
- Sensor unavailable → State forced to 0, timer reset

### Integration Testing (Coordinator Level)

**Test 7: Coordinator Recognition**
- Verify coordinator reads occupancy_state global
- Verify coordinator forces PID OFF when state=1

**Test 8: Priority Hierarchy**
- Multiple conditions active → Verify lowest priority number wins
- Emergency (1) + Occupancy (3) → Emergency controls PID

**Test 9: Coordinator Diagnostic**
- Occupancy active → Verify coordinator shows "Shutdown: Occupancy (Active)"

### Production Validation (Test Room)

**Test 10: 24-Hour Soak Test**
- Deploy to Soggiorno with 2-hour timeout
- Monitor for false shutdowns during normal occupancy
- Collect energy data (compare HVAC runtime before/after)

---

## Dependencies

**Requires (must be complete first):**
- ✅ Epic 8 completion (coordinator operational across 15+ rooms)
- ✅ HA occupancy sensors deployed and entity_ids documented
- ✅ Test room identified (Soggiorno with reliable occupancy sensor)

**Blocks (waiting on this story):**
- ⏳ Story 9.2: Occupancy stub component (needs real component as reference)
- ⏳ Story 9.3: Single-room validation (needs component to deploy)
- ⏳ Story 9.4: Multi-room rollout (needs validated component)

---

## Risks and Mitigations

**Risk 1: False Shutdowns**
- **Description:** Occupancy sensor fails to detect presence, shuts down occupied room
- **Likelihood:** Medium (depends on sensor quality)
- **Impact:** High (comfort complaint)
- **Mitigation:** Conservative 2-hour default timeout, sensor unavailability handling
- **Contingency:** Increase timeout for affected room, upgrade sensor

**Risk 2: Slow Resume**
- **Description:** Room takes too long to resume (users feel cold when entering)
- **Likelihood:** Low (immediate recovery designed)
- **Impact:** Medium (user experience)
- **Mitigation:** 0s recovery timeout, 10s polling validates responsiveness
- **Contingency:** Reduce polling interval to 5s if needed

**Risk 3: Interface Contract Misunderstanding**
- **Description:** Globals not exposed correctly, coordinator doesn't recognize condition
- **Likelihood:** Low (well-documented interface)
- **Impact:** High (blocks Epic 9)
- **Mitigation:** Reference `epic-8-condition-interface-spec.md` during implementation
- **Contingency:** Code review against interface checklist before testing

---

## Story Completion Notes

*[To be filled in by developer upon completion]*

**Implementation Summary:**
- Actual implementation time: ___ hours
- Deviations from acceptance criteria: ___
- Bugs found during testing: ___
- Performance measurements: ___

**Lessons Learned:**
- What went well: ___
- What could be improved: ___
- Recommendations for Story 9.2: ___

**Artifacts Created:**
- Component file: `components/room_occupancy_condition.yaml`
- Test results: ___
- Performance data: ___

---

**Story Status:** Ready for Development  
**Next Story:** 9.2 - Occupancy Stub Component Implementation

---

*Story created for Epic 9: Occupancy-Based Climate Shutdown*  
*Story Date: November 5, 2025*
