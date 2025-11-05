# Story 9.2: Slave REST Client - Direct ESPHome Sensor Polling

**Epic:** 9 - REST API-Based Board Communication  
**Story Type:** New Component Development  
**Estimated Effort:** 4-5 hours  
**Priority:** Critical (Foundation)  
**Date:** November 5, 2025

## Status
Draft

---

## User Story

As a **system owner**,  
I want **distribuzione slave boards to poll master and room sensor REST endpoints directly**,  
So that **temperature data flows between ESPHome devices without requiring Home Assistant as intermediary**.

---

## Story Context

**System Integration:**

- **Creates:** `components/rest_api_slave.yaml` - Reusable REST API client component
- **Modifies:** `devices/distribuzione-piano-terra.yaml` - Add REST client package
- **Replaces:** Epic 5 `platform: homeassistant` sensors with `platform: http_request` sensors
- **Technology:** ESPHome `http_request` component with JSON path extraction
- **Touch points:**
  - Master board REST API (gruppo-miscelazione)
  - ESPHome room sensor devices (e.g., sensor-soggiorno)
  - Existing PID controllers expecting temperature sensors

**Architecture Pattern:**

- Slave boards become REST API clients
- Poll master board for supply temperatures
- Poll room sensor devices for room temperatures
- Replace HA sensor platform with http_request platform
- Maintain same sensor IDs for backward compatibility with PIDs

---

## Acceptance Criteria

### Functional Requirements

1. **HTTP Request Component:**
   - ESPHome `http_request` component configured
   - ID: `http_client`
   - Timeout: 2 seconds
   - User agent: ESPHome-{device_name}

2. **Supply Temperature Sensors:**
   - Sensor: `supply_temp_piano_terra_rest`
   - Platform: `http_request`
   - URL: `http://gruppo-miscelazione.local/sensor/supply_temp_piano_terra`
   - Update interval: 10 seconds
   - JSON path: `$.value`
   - Device class: `temperature`
   - Unit: `°C`
   - Repeat for `supply_temp_primo_piano_rest`

3. **Room Temperature Sensors:**
   - Sensor: `{zone_slug}_room_temp_rest` (e.g., `soggiorno_room_temp_rest`)
   - Platform: `http_request`
   - URL: `http://sensor-{zone_slug}.local/sensor/temperature`
   - Update interval: 10 seconds
   - JSON path: `$.value`
   - Device class: `temperature`
   - Unit: `°C`
   - One sensor per room zone

4. **Polling Behavior:**
   - Update interval: 10 seconds for all REST sensors
   - Automatic retry on failure
   - Sensor state becomes `unavailable` if polling fails
   - Logs WARN on connection timeout
   - Logs ERROR on HTTP error codes (4xx, 5xx)

### Integration Requirements

5. **Component Packaging:**
   - Created as reusable component: `components/rest_api_slave.yaml`
   - Accepts vars:
     - `master_hostname` (e.g., "gruppo-miscelazione.local")
     - `room_zones` (list of zone slugs, e.g., ["soggiorno", "cucina"])
   - Optional vars:
     - `update_interval` (default: 10s)
     - `timeout` (default: 2s)
   - Header documentation explains usage and vars

6. **Device Integration:**
   - Package included in `devices/distribuzione-piano-terra.yaml`
   - Remove or comment out Epic 5 `platform: homeassistant` sensors
   - REST sensors use same IDs for PID compatibility (via template sensors)
   - Firmware compiles successfully
   - Flash size within limits

7. **Backward Compatibility:**
   - Existing PID controllers continue to work
   - Sensor IDs remain stable (via template sensor wrappers if needed)
   - No changes to PID configuration required

### Testing & Validation

8. **Polling Verification:**
   - Deploy firmware to distribuzione-piano-terra board
   - Monitor ESPHome logs for HTTP request activity
   - Verify successful GET requests every 10 seconds
   - Verify JSON value extraction from responses
   - Verify sensor values update in logs

9. **Sensor Value Accuracy:**
   - Compare REST sensor values to master board logs
   - Verify supply_temp_piano_terra matches gruppo-miscelazione Dallas sensor
   - Compare room temp REST sensor to original HA sensor values
   - Verify ±0.1°C accuracy (no data loss in REST transfer)

10. **Error Handling:**
    - Power off gruppo-miscelazione board temporarily
    - Verify slave sensors transition to `unavailable` state
    - Verify WARN logs for connection timeouts
    - Power on master board
    - Verify sensors recover automatically (within 10s)

11. **Network Resilience:**
    - Simulate network latency (if possible)
    - Verify 2s timeout prevents hanging
    - Monitor for request failures in logs
    - Verify system remains stable during network issues

### Quality Requirements

12. **Code Quality:**
    - Component follows ESPHome best practices
    - Vars clearly documented in header
    - JSON path extraction uses correct syntax
    - Error logging at appropriate levels (WARN/ERROR)
    - No hardcoded values (use vars)

13. **Documentation:**
    - Update epic brief with slave client architecture
    - Document required vars and examples
    - Add troubleshooting section for common issues
    - Note firmware size impact (~5-10KB for http_request)

---

## Tasks / Subtasks

- [ ] **Task 1: Create REST API Slave Component** (AC: 5, 12)
  - [ ] Create `components/rest_api_slave.yaml`
  - [ ] Add `http_request` component configuration
  - [ ] Add vars section with master_hostname and room_zones
  - [ ] Add defaults section
  - [ ] Add header documentation
  - [ ] Verify YAML syntax

- [ ] **Task 2: Implement Supply Temperature Sensors** (AC: 2)
  - [ ] Add sensor `supply_temp_piano_terra_rest`
  - [ ] Configure http_request platform with master URL
  - [ ] Set JSON path extraction `$.value`
  - [ ] Set device class and unit
  - [ ] Set update interval to 10s
  - [ ] Repeat for `supply_temp_primo_piano_rest`

- [ ] **Task 3: Implement Room Temperature Sensors** (AC: 3)
  - [ ] Add template loop for room zones
  - [ ] Create sensor `{zone_slug}_room_temp_rest` per zone
  - [ ] Configure http_request platform with room sensor URLs
  - [ ] Set JSON path extraction `$.value`
  - [ ] Set device class and unit
  - [ ] Set update interval to 10s

- [ ] **Task 4: Add Polling and Error Handling** (AC: 4)
  - [ ] Configure update_interval from var
  - [ ] Configure timeout from var
  - [ ] Add error logging on connection failures
  - [ ] Add WARN logs for timeouts
  - [ ] Add ERROR logs for HTTP errors
  - [ ] Test with master offline

- [ ] **Task 5: Integrate with distribuzione-piano-terra** (AC: 6, 7)
  - [ ] Open `devices/distribuzione-piano-terra.yaml`
  - [ ] Add package include for `rest_api_slave.yaml`
  - [ ] Configure vars (master_hostname, room_zones)
  - [ ] Comment out Epic 5 homeassistant platform sensors
  - [ ] Add template sensors if needed for PID compatibility
  - [ ] Compile firmware and check flash size
  - [ ] Deploy to device

- [ ] **Task 6: Polling Verification Testing** (AC: 8)
  - [ ] Connect to ESPHome logs via serial or OTA
  - [ ] Monitor HTTP GET requests every 10s
  - [ ] Verify successful responses (HTTP 200)
  - [ ] Verify JSON parsing successful
  - [ ] Verify sensor value updates in logs
  - [ ] Screenshot logs showing polling activity

- [ ] **Task 7: Sensor Value Accuracy Validation** (AC: 9)
  - [ ] Compare supply_temp_piano_terra REST value to master logs
  - [ ] Compare supply_temp_primo_piano REST value to master logs
  - [ ] Compare room temp REST value to HA sensor value
  - [ ] Verify ±0.1°C accuracy
  - [ ] Document any discrepancies

- [ ] **Task 8: Error Handling Testing** (AC: 10)
  - [ ] Power off gruppo-miscelazione board
  - [ ] Verify slave sensors show `unavailable`
  - [ ] Verify WARN logs appear
  - [ ] Power on master board
  - [ ] Verify sensors recover within 10s
  - [ ] Document recovery behavior

- [ ] **Task 9: Network Resilience Testing** (AC: 11)
  - [ ] Simulate network latency (if possible)
  - [ ] Verify 2s timeout prevents hanging
  - [ ] Monitor logs for timeout errors
  - [ ] Verify system stability
  - [ ] Document resilience characteristics

- [ ] **Task 10: Documentation Updates** (AC: 13)
  - [ ] Update epic brief with slave client details
  - [ ] Document component vars and examples
  - [ ] Add troubleshooting section
  - [ ] Note firmware size impact
  - [ ] Create completion notes with test results

---

## Dev Notes

### Relevant Source Tree

**Existing Components:**
- `components/room_sensors.yaml` (Epic 5) - Currently uses `platform: homeassistant`, will be replaced by REST client
- `components/pid.yaml` - PID controllers that consume room_temp_abstracted sensor
- `boards/a6_ethernet.yaml` - Slave board hardware with Ethernet

**Device Configurations:**
- `devices/distribuzione-piano-terra.yaml` - First slave board to migrate
- `devices/distribuzione-primo-piano.yaml` - Second slave board (future story)
- `locals/distribuzione-piano-terra.yaml` - Local config with zone definitions

**Key Sensor IDs (Epic 5 baseline):**
- `{zone_slug}_room_temp_abstracted` - Temperature input for PID controllers
- `supply_temp_piano_terra` - Supply temp from master (currently via HA)
- `supply_temp_primo_piano` - Supply temp from master (currently via HA)

### ESPHome http_request Component Reference

**Component Configuration:**
```yaml
http_request:
  id: http_client
  timeout: 2s
  useragent: "ESPHome-{device_name}"
```

**Sensor Platform:**
```yaml
sensor:
  - platform: http_request
    id: supply_temp_rest
    name: "Supply Temperature REST"
    url: "http://gruppo-miscelazione.local/sensor/supply_temp_piano_terra"
    update_interval: 10s
    method: GET
    json_path: "$.value"
    device_class: temperature
    unit_of_measurement: "°C"
```

**JSON Path Syntax:**
- `$.value` - Extracts the "value" key from JSON root
- `$.state` - Alternative if "value" not present
- Handles nested JSON with dot notation

**Error Handling:**
- Timeout: Sensor becomes `unavailable` after timeout expires
- HTTP errors: Logged at ERROR level, sensor unavailable
- JSON parse errors: Logged at ERROR level, sensor unavailable
- Automatic retry on next update_interval

### Epic 9 Architecture Context

**Story 9.1 Deliverable (Prerequisite):**
- Master board REST API operational
- Endpoints tested and validated with curl
- JSON format confirmed

**Story 9.2 Deliverable:**
- Slave boards poll master REST endpoints
- Room sensors polled via REST (ESPHome-to-ESPHome)
- HA dependency eliminated for sensor data

**Next Steps (Story 9.3):**
- Implement 2-tier failover (REST → Emergency)
- Add REST API health diagnostics
- Remove HA from sensor chain completely

### Room Sensor Device Assumptions

**Expected Room Sensor Architecture:**
- Each room has ESPHome device (e.g., `sensor-soggiorno`)
- Devices have `web_server` enabled (like Story 9.1)
- Expose `/sensor/temperature` endpoint
- Same JSON format as master board

**If Room Sensors Not Ready:**
- Story 9.2 can proceed with supply temps only
- Room sensor REST integration deferred
- Epic 5 HA room sensors remain temporarily
- Coordinate with hardware team on room sensor web_server enablement

### PID Controller Compatibility

**Current PID Input:**
```yaml
climate:
  - platform: pid
    sensor: ${zone_slug}_room_temp_abstracted
```

**Strategy 1: Direct ID Replacement**
- Rename REST sensor to `{zone_slug}_room_temp_abstracted`
- No PID config changes needed

**Strategy 2: Template Sensor Wrapper (Safer)**
```yaml
sensor:
  - platform: template
    id: ${zone_slug}_room_temp_abstracted
    lambda: |-
      if (id(${zone_slug}_room_temp_rest).has_state()) {
        return id(${zone_slug}_room_temp_rest).state;
      }
      return NAN;  // Emergency (Story 9.3 will handle)
```

**Recommendation:** Use Strategy 2 (template wrapper) for:
- Easier debugging (separate REST sensor and abstraction)
- Foundation for Story 9.3 failover logic
- Clear separation of concerns

### Firmware Size Considerations

**http_request Component Impact:**
- Adds ~5-10KB to firmware size
- Includes HTTP client, JSON parser
- Much smaller than web_server component
- Should fit comfortably on A6/A16 boards

**Monitor During Compilation:**
- Check flash usage percentage
- Should remain <85% for safety margin

### Testing Standards

**Manual Testing Required:**
- Log monitoring (ESPHome serial/OTA)
- Value accuracy verification (compare to baseline)
- Error handling validation (power off master)
- Network resilience testing (timeout behavior)

**Success Criteria:**
- All REST sensors poll successfully every 10s
- Values match master board within ±0.1°C
- Sensors recover automatically after failures
- System stable with REST polling active

**Test Environment:**
- Physical distribuzione-piano-terra board
- Master board (gruppo-miscelazione) operational
- Stable network connection (Ethernet preferred)
- Access to ESPHome logs (serial or OTA)

### Known Dependencies

**Requires:**
- Story 9.1 completed (Master REST API operational)
- Room sensor devices have web_server enabled (or defer room sensors)
- Ethernet/WiFi connectivity stable
- mDNS working on local network

**Blocks:**
- Story 9.3 (Failover Logic) - Needs REST sensors operational
- Story 9.4 (Reliability Testing) - Needs full REST client deployed

### Common Issues & Troubleshooting

**Issue: mDNS hostname not resolving**
- Symptom: "Connection failed" errors in logs
- Solution: Use IP address instead of .local hostname
- Prevention: Assign static IPs or fix mDNS

**Issue: JSON path extraction fails**
- Symptom: Sensor value remains unknown
- Solution: Verify JSON format with curl, adjust json_path
- Prevention: Test endpoints with curl before deployment

**Issue: Polling too frequent (network load)**
- Symptom: High network traffic, board instability
- Solution: Increase update_interval to 20s or 30s
- Prevention: Start with conservative 10s interval

**Issue: Timeout too short**
- Symptom: Sensors frequently unavailable despite network working
- Solution: Increase timeout to 3s or 5s
- Prevention: Test network latency before deployment

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

**Story Status:** Draft - Ready for Development (Depends on Story 9.1)  
**Next Story:** 9.3 - Failover Logic & Diagnostics
