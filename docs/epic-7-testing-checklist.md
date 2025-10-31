# Epic 7: Window Detection Testing Checklist

## Purpose

This checklist ensures comprehensive validation of window detection rollout across all fancoil-equipped rooms. Follow this checklist for each room with window detection enabled and for system-wide regression testing.

---

## Pre-Deployment Checks

### Configuration Validation

- [ ] **Room equipment verified:**
  - Room has fancoil equipment
  - Room has PID controller for fancoil (not fancoil-only)
  - Equipment type documented in room YAML comments

- [ ] **Window sensor exists in Home Assistant:**
  - Entity ID exists: `binary_sensor.{room}_window`
  - Sensor device_class is `window` or `door`
  - Sensor reports correct state (test by toggling if available)

- [ ] **Room component YAML updated:**
  - `window_detection` package added
  - Required vars provided: `zone_slug`, `zone_name`, `ha_window_sensor_id`, `pid_id`, `window_shutdown_modes`
  - `pid_id` references fancoil PID (not radiant PID)
  - `shutdown_modes` appropriate for equipment type

- [ ] **Configuration compiles:**
  ```bash
  esphome config devices/{device_name}.yaml
  ```
  - No compilation errors
  - Window detection entities appear in output
  - PID entity IDs match expectations

- [ ] **Window sensor mapped:**
  - Entry added to `docs/window-sensors-map.md`
  - Entity ID documented correctly
  - Status marked as "Configured"

---

## Deployment Validation

### OTA Upload

- [ ] **Firmware uploaded successfully:**
  ```bash
  esphome upload devices/{device_name}.yaml
  ```
  - OTA connection established
  - Firmware transferred without errors
  - Device rebooted successfully

- [ ] **Device online and responsive:**
  - Device appears online in Home Assistant
  - API connection established (check device status)
  - Log streaming available: `esphome logs devices/{device_name}.yaml`

- [ ] **New entities visible in Home Assistant:**
  - Per room with window detection:
    - `binary_sensor.{zone}_window_state` exists
    - `text_sensor.{zone}_window_detection_state` exists
  - Example for Soggiorno:
    - `binary_sensor.soggiorno_window_state`
    - `text_sensor.soggiorno_window_detection_state`

- [ ] **Initial state correct:**
  - `text_sensor.{zone}_window_detection_state` shows "Normal"
  - `binary_sensor.{zone}_window_state` reflects actual window state
  - PID climate entity operating normally (if in HEAT/COOL mode)

---

## Functional Validation (Per Room)

### Room: _________________ (Fill in)

#### Open Window Test

- [ ] **Preconditions:**
  - Window currently closed
  - PID in HEAT or COOL mode (one of configured shutdown_modes)
  - System in "Normal" state
  - Fancoil running (if duty cycle > 0)

- [ ] **Action: Open window** (or toggle mock sensor ON)

- [ ] **Immediately after opening (< 3 min):**
  - `binary_sensor.{zone}_window_state` shows ON/Open
  - `text_sensor.{zone}_window_detection_state` still shows "Normal"
  - PID still operating (shutdown not triggered yet)

- [ ] **After 3 minutes (window_open_timeout):**
  - `text_sensor.{zone}_window_detection_state` changes to "Window Open"
  - PID climate entity mode changes to OFF
  - Fancoil stops running (audible confirmation if possible)
  - Device log shows climate.control call: `mode: OFF`

#### Close Window Test

- [ ] **Preconditions:**
  - Window currently open
  - System in "Window Open" state
  - PID in OFF mode

- [ ] **Action: Close window** (or toggle mock sensor OFF)

- [ ] **Immediately after closing:**
  - `binary_sensor.{zone}_window_state` shows OFF/Closed
  - `text_sensor.{zone}_window_detection_state` changes to "Recovering"
  - PID remains in OFF mode (not yet resumed)

- [ ] **After 1 minute (window_close_recovery_time):**
  - `text_sensor.{zone}_window_detection_state` changes to "Normal"
  - PID climate entity mode restored to previous mode (HEAT or COOL)
  - Fancoil resumes operation (audible confirmation if possible)
  - Device log shows climate.control call: `mode: {previous_mode}`

#### Mode-Specific Test (If Applicable)

- [ ] **Preconditions:**
  - Room has both heating and cooling modes
  - Only one mode configured in `shutdown_modes` (e.g., only "cooling")

- [ ] **Test non-shutdown mode:**
  - Set PID to mode NOT in shutdown_modes (e.g., HEAT if only cooling configured)
  - Open window
  - Wait 3+ minutes
  - Verify `text_sensor.{zone}_window_detection_state` remains "Normal"
  - Verify PID does NOT shutdown

- [ ] **Test shutdown mode:**
  - Close window, wait for recovery
  - Set PID to mode IN shutdown_modes (e.g., COOL)
  - Open window
  - Wait 3+ minutes
  - Verify `text_sensor.{zone}_window_detection_state` changes to "Window Open"
  - Verify PID shuts down

---

## Regression Testing

### Existing Room Functionality

- [ ] **Rooms without window detection unaffected:**
  - Bagno Terra: Climate control operates normally
  - Anticamera: Climate control operates normally
  - All first floor rooms: Climate control operates normally

- [ ] **Temperature control maintained:**
  - All rooms maintain setpoint temperatures (±0.5°C)
  - No unexpected temperature deviations
  - PID tuning still effective

- [ ] **Emergency shutdown still functional:**
  - Test: Disable Home Assistant or make temperature sensor unavailable
  - Verify emergency shutdown triggers after 180s
  - Verify state machine transitions to "Emergency"
  - Re-enable sensor, verify recovery to "Normal"

- [ ] **Manual PID control works:**
  - Set PID mode via Home Assistant UI
  - Adjust target temperature
  - Verify changes reflected in device
  - Verify fancoil responds to manual changes

### Device-Level Validation

- [ ] **No new errors in device logs:**
  ```bash
  esphome logs devices/{device_name}.yaml
  ```
  - No ERROR or WARN messages related to window detection
  - Window sensor updates logged correctly
  - State transitions logged correctly

- [ ] **Pump management scripts functional:**
  - Ground floor radiant pump: Activates when any radiant zone active
  - Ground floor fancoil pump: Deactivates when any fancoil active
  - Relays respond correctly to pump management calls

- [ ] **Modbus communication intact:**
  - 0-10V adapter communication stable
  - Fancoil register writes successful
  - No increase in Modbus errors/timeouts

---

## System-Wide Validation

### 24-Hour Burn-In Test

- [ ] **Deploy to all devices with window detection rooms:**
  - `distribuzione-piano-terra.yaml`: Soggiorno, Cucina
  - (Add other devices as applicable)

- [ ] **Monitor for 24 hours:**
  - Record start time: _______________
  - Record end time: _______________

- [ ] **Check every 4-6 hours:**
  - All devices online
  - All PIDs operating correctly
  - No unexpected shutdowns (false positives)
  - Temperature control stable

- [ ] **After 24 hours:**
  - Zero climate control failures
  - No repeated window detection false positives
  - User reports normal behavior (if applicable)
  - System logs clean (no errors or warnings)

### Performance Metrics

- [ ] **CPU usage:** Check ESPHome device diagnostics in HA
  - Before window detection: _____%
  - After window detection: _____%
  - Increase: < 5% (acceptable)

- [ ] **Memory usage:** Check device diagnostics
  - Free memory before: _____KB
  - Free memory after: _____KB
  - Per-room overhead: ~2KB (expected)

- [ ] **Network traffic:** Monitor Home Assistant API calls
  - No excessive polling or API calls
  - State transitions trigger single API call
  - Normal update rate maintained

---

## User Acceptance Testing

### User Education

- [ ] **Documentation provided:**
  - [Window Detection Guide](epic-7-window-detection-guide.md) shared with user
  - [Window Sensors Map](window-sensors-map.md) reviewed
  - Expected behavior explained (3-minute timeout, 1-minute recovery)

- [ ] **Diagnostic visibility:**
  - User can view window detection state in Home Assistant
  - Dashboard or Lovelace card configured (if desired)
  - User understands "Normal", "Window Open", "Recovering" states

### User Validation

- [ ] **User confirms expected behavior:**
  - Window open → fancoil stops after 3 minutes: ✅ / ❌
  - Window close → fancoil resumes after 1 minute: ✅ / ❌
  - System behavior predictable and consistent: ✅ / ❌

- [ ] **User reports no issues:**
  - No false positives (unwanted shutdowns): ✅ / ❌
  - No failures to resume (stuck in recovery): ✅ / ❌
  - No confusion about system behavior: ✅ / ❌

- [ ] **User feedback collected:**
  - Timeout duration appropriate (3 min): ✅ / ❌ / Needs adjustment
  - Recovery time appropriate (1 min): ✅ / ❌ / Needs adjustment
  - Overall satisfaction: _____ / 10

---

## Rollback Procedures (If Needed)

### Per-Room Rollback

If specific room has issues:

1. [ ] **Identify affected room:** _________________
2. [ ] **Remove window detection from room YAML:**
   - Comment out or delete `window_detection` package
3. [ ] **Recompile and upload device:**
   ```bash
   esphome upload devices/{device_name}.yaml
   ```
4. [ ] **Verify room returns to pre-Epic-7 behavior:**
   - PID operates normally
   - No window detection entities
   - Temperature control unaffected

### Full Device Rollback

If entire device has issues:

1. [ ] **Identify affected device:** _________________
2. [ ] **Revert all room components with window detection:**
   - Remove window detection packages from all rooms
3. [ ] **Recompile and upload device:**
   ```bash
   esphome upload devices/{device_name}.yaml
   ```
4. [ ] **Verify device returns to pre-Epic-7 behavior:**
   - All rooms operate normally
   - No window detection functionality
   - System stable

---

## Success Criteria

- [ ] **All fancoil rooms configured:**
  - Soggiorno: Window detection active
  - Cucina: Window detection active

- [ ] **All functional tests passed:**
  - Open window tests: 100% pass rate
  - Close window tests: 100% pass rate
  - Mode-specific tests: 100% pass rate (if applicable)

- [ ] **All regression tests passed:**
  - Existing rooms unaffected: ✅
  - Temperature control maintained: ✅
  - Emergency shutdown functional: ✅
  - Manual control functional: ✅

- [ ] **24-hour burn-in successful:**
  - Zero climate control failures
  - Zero false positives
  - System logs clean

- [ ] **User acceptance achieved:**
  - User confirms expected behavior
  - User reports no issues
  - User satisfaction ≥ 8/10

- [ ] **Documentation complete:**
  - Window Detection Guide created
  - Window Sensors Map created
  - Testing Checklist completed (this document)
  - Completion Report created

---

## Notes and Observations

### Issues Encountered

_Document any issues found during testing and their resolutions:_

---

### Performance Observations

_Document any performance metrics or notable observations:_

---

### User Feedback

_Document any user feedback or requests for future enhancements:_

---

**Tester:** _________________  
**Date Started:** _________________  
**Date Completed:** _________________  
**Overall Result:** ✅ PASS / ❌ FAIL / ⚠️ PASS WITH NOTES

---

## Related Documentation

- [Epic 7 Window Detection Guide](epic-7-window-detection-guide.md)
- [Window Sensors Map](window-sensors-map.md)
- [Epic 7 Completion Report](epic-7-completion-report.md)
- [Story 7.3: Rollout & Documentation](stories/7.3-window-detection-rollout.md)
