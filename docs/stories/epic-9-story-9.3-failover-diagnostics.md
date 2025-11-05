# Story 9.3: Two-Tier Failover & REST API Diagnostics

**Epic:** 9 - REST API-Based Board Communication  
**Story Type:** Component Enhancement  
**Estimated Effort:** 3-4 hours  
**Priority:** Critical (Safety)  
**Date:** November 5, 2025

## Status
Draft

---

## User Story

As a **system owner**,  
I want **template sensors that implement 2-tier failover (REST → Emergency) with comprehensive diagnostics**,  
So that **the system safely shuts down when REST API fails and I can monitor REST API health in real-time**.

---

## Story Context

**System Integration:**

- **Creates:** `components/rest_api_failover.yaml` - Reusable 2-tier failover component
- **Modifies:** Slave board device files to use failover component
- **Replaces:** Epic 5 3-tier failover (HA intermediary removed)
- **Technology:** ESPHome template sensors with lambda logic, diagnostic text sensors
- **Touch points:**
  - REST API sensors from Story 9.2
  - PID controllers expecting abstracted temperature sensors
  - Home Assistant dashboard for diagnostics visibility

**Architecture Pattern:**

- Tier 1: REST API (ESPHome-to-ESPHome direct)
- Tier 2: Emergency (local shutdown, return NaN)
- NO Tier 3: Home Assistant removed from critical path
- Diagnostic sensors expose REST API health for monitoring

---

## Acceptance Criteria

### Functional Requirements

1. **Two-Tier Template Sensors:**
   - Sensor: `{zone_slug}_room_temp_abstracted` (PID input)
   - Lambda logic:
     ```cpp
     if (id({zone_slug}_room_temp_rest).has_state() && !isnan(id({zone_slug}_room_temp_rest).state)) {
       return id({zone_slug}_room_temp_rest).state;  // Tier 1: REST
     } else {
       return NAN;  // Tier 2: Emergency
     }
     ```
   - Update interval: 5 seconds
   - Repeat for supply_temp sensors

2. **Emergency Detection:**
   - When REST sensor becomes unavailable (>10s no updates)
   - Template sensor returns NaN
   - PID controller receives invalid data
   - Epic 8 emergency condition detects 180s timeout
   - PID forced to OFF via coordinator

3. **Automatic Recovery:**
   - When REST sensor becomes available again
   - Template sensor returns valid temperature immediately
   - Epic 8 recovery state machine handles 60s stability check
   - PID resumes automatically after recovery complete

4. **REST API Health Sensor:**
   - Sensor: `rest_api_health`
   - Type: `text_sensor`
   - Values: "Healthy" | "Degraded" | "Failed"
   - Logic:
     - Healthy: All REST sensors have valid state
     - Degraded: Some REST sensors unavailable
     - Failed: All REST sensors unavailable
   - Update interval: 10 seconds

### Diagnostic Requirements

5. **REST Error Count Sensor:**
   - Sensor: `rest_api_error_count`
   - Type: `sensor` (integer)
   - Increments when REST sensor update fails
   - Resets to 0 on successful update
   - Exposed to Home Assistant for alerting

6. **REST Response Time Sensor:**
   - Sensor: `rest_api_response_time_ms`
   - Type: `sensor` (milliseconds)
   - Tracks average response time of REST requests
   - Calculated from http_request component metrics (if available)
   - Exposed to Home Assistant for monitoring

7. **Last Successful Poll Timestamp:**
   - Sensor: `rest_api_last_success`
   - Type: `text_sensor` (timestamp)
   - Updates on every successful REST poll
   - Allows calculation of "time since last success"
   - Useful for debugging intermittent failures

### Integration Requirements

8. **Component Packaging:**
   - Created as reusable component: `components/rest_api_failover.yaml`
   - Accepts vars:
     - `zone_slug` - Room identifier
     - `zone_name` - Display name
     - `supply_temp_enabled` - Boolean, if supply temps used (default: true)
   - Header documentation explains 2-tier failover logic

9. **Device Integration:**
   - Package included in distribuzione device files
   - Replaces Epic 5 3-tier failover logic
   - No Home Assistant sensor fallback
   - PID controllers work with existing `{zone_slug}_room_temp_abstracted` IDs

10. **Home Assistant Dashboard:**
    - REST API health sensor visible in HA
    - Error count sensor visible in HA
    - Response time sensor visible in HA (if implemented)
    - Can create HA alerts for "Failed" or high error counts

### Testing & Validation

11. **Normal Operation Testing:**
    - Deploy failover component to test board
    - Verify template sensors return REST values
    - Verify PID controllers operate normally
    - Verify health sensor shows "Healthy"
    - Monitor for 1 hour, verify stable operation

12. **REST Failure Testing:**
    - Power off master board (gruppo-miscelazione)
    - Verify template sensors transition to NaN immediately
    - Verify health sensor changes to "Failed"
    - Verify error count increments
    - Wait 180 seconds, verify Epic 8 emergency triggers
    - Verify PID forced to OFF by coordinator

13. **REST Recovery Testing:**
    - Power on master board
    - Verify template sensors return valid temps within 10s
    - Verify health sensor changes to "Healthy"
    - Verify error count resets to 0
    - Wait 60 seconds, verify Epic 8 recovery completes
    - Verify PID resumes normal operation

14. **Partial Failure Testing (Degraded):**
    - Power off one room sensor device (not master)
    - Verify health sensor shows "Degraded"
    - Verify affected zone enters emergency
    - Verify other zones remain operational
    - Validate isolation of failures

### Quality Requirements

15. **Code Quality:**
    - Lambda logic clear and commented
    - No hardcoded values
    - Diagnostic sensors use meaningful names
    - Error logging at appropriate levels
    - Component follows ESPHome patterns

16. **Documentation:**
    - Update epic brief with 2-tier failover details
    - Document emergency transition times
    - Create troubleshooting guide for REST failures
    - Add HA dashboard card examples for diagnostics
    - Document difference from Epic 5 (no HA fallback)

---

## Tasks / Subtasks

- [ ] **Task 1: Create REST API Failover Component** (AC: 8, 15)
  - [ ] Create `components/rest_api_failover.yaml`
  - [ ] Add vars section (zone_slug, zone_name, supply_temp_enabled)
  - [ ] Add defaults section
  - [ ] Add header documentation explaining 2-tier failover
  - [ ] Verify YAML syntax

- [ ] **Task 2: Implement 2-Tier Template Sensors** (AC: 1)
  - [ ] Add template sensor `{zone_slug}_room_temp_abstracted`
  - [ ] Implement lambda: REST → NaN (no HA fallback)
  - [ ] Add comments explaining tier logic
  - [ ] Set update interval to 5s
  - [ ] Repeat for supply temp sensors if enabled

- [ ] **Task 3: Implement REST API Health Sensor** (AC: 4)
  - [ ] Add text_sensor `rest_api_health`
  - [ ] Implement lambda checking all REST sensor states
  - [ ] Logic: Healthy / Degraded / Failed
  - [ ] Set update interval to 10s
  - [ ] Expose to Home Assistant

- [ ] **Task 4: Implement Error Count Sensor** (AC: 5)
  - [ ] Add sensor `rest_api_error_count`
  - [ ] Add global variable for error count
  - [ ] Increment on REST sensor unavailable
  - [ ] Reset on REST sensor available
  - [ ] Expose to Home Assistant

- [ ] **Task 5: Implement Last Success Timestamp** (AC: 7)
  - [ ] Add text_sensor `rest_api_last_success`
  - [ ] Update timestamp on successful REST poll
  - [ ] Format as ISO 8601 or human-readable
  - [ ] Expose to Home Assistant

- [ ] **Task 6: Optional Response Time Sensor** (AC: 6)
  - [ ] Research http_request component metrics availability
  - [ ] If available, add sensor `rest_api_response_time_ms`
  - [ ] Calculate average response time
  - [ ] Expose to Home Assistant
  - [ ] If not available, document as future enhancement

- [ ] **Task 7: Integrate with distribuzione-piano-terra** (AC: 9)
  - [ ] Open `devices/distribuzione-piano-terra.yaml`
  - [ ] Add package include for `rest_api_failover.yaml`
  - [ ] Configure vars (zone_slug, zone_name)
  - [ ] Remove Epic 5 3-tier failover logic
  - [ ] Compile firmware and verify
  - [ ] Deploy to device

- [ ] **Task 8: Normal Operation Testing** (AC: 11)
  - [ ] Monitor ESPHome logs for template sensor updates
  - [ ] Verify REST values passed through correctly
  - [ ] Verify PID operates normally
  - [ ] Verify health sensor shows "Healthy"
  - [ ] Monitor for 1 hour, document stability

- [ ] **Task 9: REST Failure Testing** (AC: 12)
  - [ ] Power off gruppo-miscelazione board
  - [ ] Verify template sensors return NaN
  - [ ] Verify health sensor shows "Failed"
  - [ ] Verify error count increments
  - [ ] Wait 180s, verify emergency triggers
  - [ ] Verify PID OFF
  - [ ] Document transition times

- [ ] **Task 10: REST Recovery Testing** (AC: 13)
  - [ ] Power on master board
  - [ ] Verify template sensors valid within 10s
  - [ ] Verify health sensor "Healthy"
  - [ ] Verify error count resets
  - [ ] Wait 60s, verify recovery complete
  - [ ] Verify PID resumes
  - [ ] Document recovery behavior

- [ ] **Task 11: Partial Failure Testing** (AC: 14)
  - [ ] Power off one room sensor device
  - [ ] Verify health sensor "Degraded"
  - [ ] Verify affected zone emergency
  - [ ] Verify other zones operational
  - [ ] Document isolation behavior

- [ ] **Task 12: Home Assistant Dashboard Setup** (AC: 10)
  - [ ] Add rest_api_health to HA dashboard
  - [ ] Add rest_api_error_count to HA dashboard
  - [ ] Add rest_api_last_success to HA dashboard
  - [ ] Create alert automation for "Failed" state
  - [ ] Screenshot dashboard cards for documentation

- [ ] **Task 13: Documentation Updates** (AC: 16)
  - [ ] Update epic brief with 2-tier failover
  - [ ] Document emergency transition times
  - [ ] Create REST failure troubleshooting guide
  - [ ] Add HA dashboard card examples
  - [ ] Document Epic 5 comparison (no HA fallback)

---

## Dev Notes

### Relevant Source Tree

**Existing Components:**
- `components/room_emergency_condition.yaml` (Epic 8) - Detects 180s sensor timeout, triggers emergency
- `components/room_control_coordinator.yaml` (Epic 8) - Forces PID OFF when emergency active
- `components/rest_api_slave.yaml` (Story 9.2) - REST sensors to wrap with failover

**Device Configurations:**
- `devices/distribuzione-piano-terra.yaml` - First device to migrate
- `locals/distribuzione-piano-terra.yaml` - Zone definitions

**Epic 5 Baseline (Being Replaced):**
- 3-tier failover: Modbus → HA → Emergency (or Tier 1 REST → Tier 2 HA → Tier 3 Emergency in some designs)
- Epic 9 simplifies to: Tier 1 REST → Tier 2 Emergency (no HA)

### ESPHome Template Sensor Reference

**Basic Template Sensor:**
```yaml
sensor:
  - platform: template
    id: ${zone_slug}_room_temp_abstracted
    name: "${zone_name} Room Temp"
    device_class: temperature
    unit_of_measurement: "°C"
    update_interval: 5s
    lambda: |-
      // Tier 1: REST API
      if (id(${zone_slug}_room_temp_rest).has_state() && 
          !isnan(id(${zone_slug}_room_temp_rest).state)) {
        return id(${zone_slug}_room_temp_rest).state;
      }
      // Tier 2: Emergency
      ESP_LOGW("failover", "${zone_name}: REST unavailable, returning NaN");
      return NAN;
```

**Text Sensor for Health:**
```yaml
text_sensor:
  - platform: template
    id: rest_api_health
    name: "REST API Health"
    update_interval: 10s
    lambda: |-
      int total = 0;
      int available = 0;
      
      // Check each REST sensor
      if (id(soggiorno_room_temp_rest).has_state()) available++;
      total++;
      
      // More sensors...
      
      if (available == total) return {"Healthy"};
      if (available == 0) return {"Failed"};
      return {"Degraded"};
```

**Global Variable for Error Count:**
```yaml
globals:
  - id: rest_api_error_count_global
    type: int
    initial_value: '0'

sensor:
  - platform: template
    id: rest_api_error_count
    name: "REST API Error Count"
    accuracy_decimals: 0
    lambda: |-
      return id(rest_api_error_count_global);
```

### Epic 8 Integration Context

**Emergency Condition Component (Story 8.1):**
- Monitors `{zone_slug}_room_temp_abstracted` sensor
- Detects 180s timeout (no valid data)
- Sets `{zone_slug}_emergency_state = 1` (Active)
- Exposed via global variable

**Coordinator Component (Story 8.3):**
- Reads `{zone_slug}_emergency_state` every 5s
- If state == 1 (Active) or 2 (Recovering), forces PID OFF
- Uses `climate.control` API to set mode OFF

**Story 9.3 Ties Together:**
- REST failure → Template sensor returns NaN
- Emergency condition detects NaN after 180s
- Coordinator forces PID OFF
- Full safety chain: REST → Template → Emergency → Coordinator → PID

### Transition Time Expectations

**REST Failure → Emergency:**
- REST poll failure detected: 0-10s (next poll cycle)
- Template sensor returns NaN: immediate
- Emergency condition timeout: 180s (configurable)
- **Total: ~180-190s from REST failure to PID OFF**

**REST Recovery → Normal:**
- REST poll success: 0-10s (next poll cycle)
- Template sensor returns valid temp: immediate
- Epic 8 recovery stability: 60s
- **Total: ~60-70s from REST recovery to PID resume**

**Faster Than Epic 5:**
- Epic 5: HA intermediary added latency (~30-60s)
- Epic 9: Direct REST API faster response

### Home Assistant Dependency Clarification

**Epic 9 Architecture:**
- **Sensor Data:** ESPHome-to-ESPHome REST API only (no HA)
- **Diagnostics:** Exposed to HA for monitoring (optional)
- **Manual Overrides:** HA can still control PIDs manually
- **Not Required:** System operates autonomously without HA

**HA Restart Behavior:**
- **Epic 5:** Sensor data breaks, emergency triggers
- **Epic 9:** Sensor data unaffected, system continues
- **Win:** True autonomous operation during HA maintenance

### Diagnostic Sensor Use Cases

**rest_api_health:**
- Quick glance at REST API status
- HA dashboard card shows Healthy/Degraded/Failed
- Mobile app notification when Failed

**rest_api_error_count:**
- Trending data for reliability analysis
- Alert when count exceeds threshold (e.g., >10)
- Identify intermittent network issues

**rest_api_last_success:**
- Calculate "time since last success"
- Useful for debugging rare failures
- Historical tracking in HA database

**rest_api_response_time_ms:**
- Network performance monitoring
- Detect latency increases before failure
- Capacity planning (add more boards?)

### Testing Standards

**Manual Testing Required:**
- Failure testing (power off master)
- Recovery testing (power on master)
- Partial failure testing (power off room sensor)
- Long-term stability (1+ hour normal operation)

**Success Criteria:**
- Template sensors return REST values when available
- Template sensors return NaN when REST unavailable
- Health sensor accurately reflects REST status
- Emergency triggers after 180s REST failure
- Recovery completes after 60s REST restoration

**Test Environment:**
- Physical distribuzione-piano-terra board
- Master board (gruppo-miscelazione)
- At least one room sensor device
- Access to power controls for failure simulation
- ESPHome logs via serial or OTA

### Known Dependencies

**Requires:**
- Story 9.2 completed (REST API client operational)
- Epic 8 completed (Emergency condition + Coordinator)
- Stable network for normal operation testing

**Blocks:**
- Story 9.4 (Reliability Testing) - Needs full failover deployed

### Common Issues & Troubleshooting

**Issue: Template sensor always returns NaN**
- Symptom: PID never operates, always in emergency
- Solution: Check REST sensor ID matches template lambda
- Prevention: Test REST sensors (Story 9.2) thoroughly first

**Issue: Health sensor shows "Failed" but REST working**
- Symptom: False alarm on health sensor
- Solution: Debug lambda logic, check all sensor IDs
- Prevention: Test health lambda with known good/bad states

**Issue: Error count never resets**
- Symptom: Error count keeps incrementing
- Solution: Add reset logic on successful poll
- Prevention: Test error count increment and reset separately

**Issue: Emergency doesn't trigger on REST failure**
- Symptom: PID continues running with NaN input
- Solution: Verify Epic 8 emergency condition monitoring correct sensor
- Prevention: Validate Epic 8 integration before Story 9.3

---

## Change Log

| Date       | Version | Description            | Author     |
| ---------- | ------- | ---------------------- | ---------- |
| 2025-11-05 | 1.0     | Initial story creation | Sarah (PO) |

---

## Dev Agent Record

### Agent Model Used
*To be populated during implementation*

### Debug Log References
*To be populated during implementation*

### Completion Notes List
*To be populated during implementation*

### File List
*To be populated during implementation*

---

## QA Results

*To be populated after QA review*

---

**Story Status:** Draft - Ready for Development (Depends on Stories 9.2 + Epic 8)  
**Next Story:** 9.4 - Reliability Testing & Validation
