# Story 9.3: Single-Room Validation (Test Room Deployment)

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

**As a** system administrator,  
**I want** to deploy and validate occupancy detection in a single test room with comprehensive testing,  
**so that** I can confirm the Epic 9 pattern works correctly before rolling out to all 15+ rooms.

---

## Business Context

This story represents the critical validation phase between component development (Stories 9.1, 9.2) and system-wide deployment (Story 9.4). By thoroughly testing a single room, we:

1. **De-risk Production Rollout:** Catch integration issues, edge cases, and performance problems before affecting all rooms
2. **Validate Epic 8 Interface:** Confirm zero coordinator modifications assumption is correct
3. **Establish Baseline Metrics:** Measure energy savings, response times, and false shutdown rates
4. **Refine Documentation:** Update migration guide based on real deployment experience

**Value Delivered:**
- Confidence to proceed with system-wide rollout (Story 9.4)
- Validated energy savings estimates (10-20% target)
- Proof of Epic 8 extensibility (no coordinator changes needed)
- Real-world tuning data for timeout recommendations

**Test Room Selection Criteria:**
- Has reliable HA occupancy sensor (PIR + mmWave preferred)
- Frequently occupied/unoccupied cycles (good test coverage)
- High HVAC energy consumption (measurable savings)
- Easy physical access for manual testing
- **Recommended:** Soggiorno (living room) - high traffic, reliable sensors, measurable usage

**Dependencies:**
- Story 9.1 completed (occupancy condition component)
- Story 9.2 completed (occupancy stub component)
- Test room has HA occupancy sensor configured and stable
- Energy monitoring configured in HA for test room

---

## Acceptance Criteria

### AC1: Test Room Configuration and Deployment

**Given** Soggiorno (test room) currently uses Epic 8 coordinator,  
**When** occupancy condition is added,  
**Then** the room configuration MUST be updated correctly:

**Before (Baseline - Epic 8 only):**
```yaml
# devices/distribuzione-piano-terra.yaml (Soggiorno section)
packages:
  # Room sensors and PID
  room_sensors_soggiorno:
    file: ../../components/room_sensors.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      ha_temperature_sensor_id: "sensor.soggiorno_temperature"
      pid_id: "pid_soggiorno"
  
  # Emergency condition (Epic 5/8)
  room_emergency_condition_soggiorno:
    file: ../../components/room_emergency_condition.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      ha_temperature_sensor_id: "sensor.soggiorno_temperature"
  
  # Window condition (Epic 7/8)
  room_window_condition_soggiorno:
    file: ../../components/room_window_condition.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      ha_window_sensor_id: "binary_sensor.soggiorno_window"
      pid_id: "pid_soggiorno"
      window_shutdown_modes: "cooling, heating"
  
  # Coordinator (Epic 8)
  room_control_coordinator_soggiorno:
    file: ../../components/room_control_coordinator.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      pid_id: "pid_soggiorno"
```

**After (With Occupancy - Epic 9):**
```yaml
# devices/distribuzione-piano-terra.yaml (Soggiorno section)
packages:
  # Room sensors and PID (UNCHANGED)
  room_sensors_soggiorno:
    file: ../../components/room_sensors.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      ha_temperature_sensor_id: "sensor.soggiorno_temperature"
      pid_id: "pid_soggiorno"
  
  # Emergency condition (UNCHANGED)
  room_emergency_condition_soggiorno:
    file: ../../components/room_emergency_condition.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      ha_temperature_sensor_id: "sensor.soggiorno_temperature"
  
  # Window condition (UNCHANGED)
  room_window_condition_soggiorno:
    file: ../../components/room_window_condition.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      ha_window_sensor_id: "binary_sensor.soggiorno_window"
      pid_id: "pid_soggiorno"
      window_shutdown_modes: "cooling, heating"
  
  # NEW: Occupancy condition (Epic 9)
  room_occupancy_condition_soggiorno:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      ha_occupancy_sensor_id: "binary_sensor.soggiorno_occupancy"
      unoccupied_timeout: "300"  # 5 minutes for testing (not production 2h)
  
  # Coordinator (UNCHANGED - validates Epic 8 interface)
  room_control_coordinator_soggiorno:
    file: ../../components/room_control_coordinator.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      pid_id: "pid_soggiorno"
```

**Configuration Changes:**
- ✅ **Added:** `room_occupancy_condition_soggiorno` package
- ✅ **Unchanged:** All other packages (sensors, emergency, window, coordinator)
- ✅ **Testing timeout:** 5 minutes (300s) instead of production 2 hours (7200s)
- ✅ **Rationale:** Short timeout enables rapid testing without waiting 2 hours per cycle

**Validation:**
- [ ] Configuration file compiles without errors
- [ ] No modifications to coordinator package (validates interface contract)
- [ ] OTA deployment succeeds
- [ ] All existing entities remain unchanged (climate, sensors, switches)
- [ ] New occupancy entities appear in HA: `text_sensor.soggiorno_occupancy_state`, `sensor.soggiorno_unoccupied_duration`

---

### AC2: Baseline Measurement (Pre-Occupancy)

**Given** the test room has NO occupancy detection yet,  
**When** baseline measurements are collected for 48 hours,  
**Then** we MUST document energy consumption and behavior:

**Baseline Metrics to Collect:**
1. **HVAC Runtime:**
   - Total heating/cooling runtime over 48 hours
   - Runtime during occupied periods (reference)
   - Runtime during unoccupied periods (target for savings)

2. **Temperature Control:**
   - Temperature accuracy: Average deviation from setpoint (target: ±0.5°C)
   - Temperature stability: Standard deviation of room temperature
   - Setpoint changes: Manual user adjustments frequency

3. **Occupancy Patterns:**
   - Occupied hours per day (from HA sensor)
   - Unoccupied periods >5 minutes (testing threshold)
   - Unoccupied periods >2 hours (production threshold)
   - Typical daily pattern (morning/afternoon/evening)

4. **Emergency/Window Conditions:**
   - Emergency triggers in baseline period (should be 0)
   - Window triggers in baseline period (reference)
   - Coordinator state distribution (expect "Normal" most of time)

**Data Collection Method:**
```yaml
# HA automation for baseline logging (pseudo-code)
automation:
  - alias: "Epic 9 Baseline - Soggiorno HVAC Runtime"
    trigger:
      - platform: state
        entity_id: climate.pid_soggiorno
    action:
      - service: logbook.log
        data:
          name: "Epic 9 Baseline"
          message: "Soggiorno PID: {{ states('climate.pid_soggiorno') }}"
```

**Validation:**
- [ ] 48 hours of continuous data collected
- [ ] No gaps in occupancy sensor data
- [ ] HVAC runtime data complete and accurate
- [ ] Temperature readings within expected range (18-25°C)
- [ ] Baseline report documented with metrics

**Expected Baseline Results:**
- HVAC runtime: ~40-60% of 48h period (high because no occupancy shutdown)
- Temperature accuracy: ±0.5°C (current proven performance)
- Unoccupied periods: Multiple 5+ minute periods per day (testing opportunities)
- Unoccupied periods: 2-4 extended (>2h) periods per 48h (savings opportunities)

---

### AC3: Occupancy Detection Functional Testing

**Given** occupancy condition deployed to test room,  
**When** comprehensive functional tests are executed,  
**Then** all core behaviors MUST work correctly:

#### Test 3.1: Normal Operation (Room Occupied)

**Scenario:** Room continuously occupied for 1 hour

**Steps:**
1. Ensure HA occupancy sensor shows `true` (occupied)
2. Monitor for 1 hour (12x 5-minute cycles)
3. Verify state remains Normal throughout

**Expected Results:**
- [ ] Occupancy state: 0 (Normal) for entire duration
- [ ] Occupancy text sensor: "Occupied"
- [ ] Unoccupied duration: 0 seconds
- [ ] PID control: Operating normally (heating/cooling per setpoint)
- [ ] Coordinator diagnostic: "Normal (All Clear)" or window/emergency if triggered
- [ ] No occupancy-related logs (state stays Normal)

---

#### Test 3.2: Unoccupied Timeout Trigger

**Scenario:** Room becomes unoccupied and stays unoccupied for 5+ minutes

**Steps:**
1. Ensure room occupied initially (state: Normal)
2. Leave room (occupancy sensor → `false`)
3. Wait for unoccupied duration to reach 300 seconds (5 minutes)
4. Observe state transition to Active

**Expected Results:**
- [ ] **T+0s:** Occupancy sensor changes to `false`
- [ ] **T+0-290s:** State remains 0 (Normal), unoccupied duration increments (10s, 20s, ... 290s)
- [ ] **T+300s:** State transitions 0 → 1 (Active)
- [ ] Text sensor updates: "Occupied" → "Unoccupied (Active)"
- [ ] Coordinator diagnostic changes: "Normal (All Clear)" → "Shutdown: Occupancy (Active)"
- [ ] **PID control:** Forced to OFF mode (heating/cooling stops)
- [ ] **Log entry:** `"Soggiorno: Unoccupied timeout reached, PID shutdown triggered"` (WARN level)
- [ ] Temperature begins to drift from setpoint (expected during shutdown)

**Timing Validation:**
- [ ] Transition occurs within ±10 seconds of 300s threshold (polling interval tolerance)
- [ ] Coordinator recognizes Active state within 5 seconds (coordinator polling)
- [ ] Total shutdown delay: ≤15 seconds from timeout (10s occupancy poll + 5s coordinator poll)

---

#### Test 3.3: Immediate Recovery on Occupancy

**Scenario:** Room becomes occupied while occupancy condition is Active

**Steps:**
1. Start with room in Active state (PID OFF)
2. Enter room (occupancy sensor → `true`)
3. Observe immediate recovery

**Expected Results:**
- [ ] **T+0s:** Occupancy sensor changes to `true`
- [ ] **T+0-10s:** State transitions 1 (Active) → 2 (Recovering)
- [ ] Text sensor updates: "Unoccupied (Active)" → "Resuming"
- [ ] **T+10-20s:** State transitions 2 (Recovering) → 0 (Normal)
- [ ] Text sensor updates: "Resuming" → "Occupied"
- [ ] Unoccupied duration resets to 0
- [ ] Coordinator diagnostic changes: "Shutdown: Occupancy (Active)" → "Normal (All Clear)"
- [ ] **PID control:** Resumes normal operation (heating/cooling per setpoint)
- [ ] Total resume time: ≤15 seconds from entry (10s occupancy poll + 5s coordinator poll)

**Key Difference from Emergency/Window:**
- [ ] **No 60-second recovery timeout** (immediate Recovering → Normal transition)
- [ ] Rationale: Occupancy detection reliable, no stability period needed

---

#### Test 3.4: Priority Hierarchy - Emergency Overrides Occupancy

**Scenario:** Emergency condition triggers while room is unoccupied (occupancy Active)

**Steps:**
1. Room unoccupied, occupancy Active (PID already OFF)
2. Simulate emergency: Disconnect HA temperature sensor or stop HA
3. Wait for emergency timeout (180 seconds)
4. Observe emergency takes priority

**Expected Results:**
- [ ] **Initial state:** Occupancy Active (priority 3), emergency Normal (priority 1)
- [ ] Coordinator shows: "Shutdown: Occupancy (Active)"
- [ ] **T+180s:** Emergency transitions to Active
- [ ] Coordinator diagnostic changes: "Shutdown: Occupancy (Active)" → "Shutdown: Emergency (Active)"
- [ ] **Priority hierarchy enforced:** Emergency (1) < Occupancy (3), emergency wins
- [ ] PID remains OFF (already off due to occupancy, now off due to emergency)
- [ ] **Restore sensor:** Emergency clears → Coordinator shows "Shutdown: Occupancy (Active)" again
- [ ] Occupancy still Active (still unoccupied)

---

#### Test 3.5: Priority Hierarchy - Window Overrides Occupancy

**Scenario:** Window opens while room is unoccupied (occupancy Active)

**Steps:**
1. Room unoccupied, occupancy Active (PID already OFF)
2. Open window (in heating or cooling mode)
3. Wait for window timeout (180 seconds)
4. Observe window takes priority

**Expected Results:**
- [ ] **Initial state:** Occupancy Active (priority 3), window Normal (priority 2)
- [ ] Coordinator shows: "Shutdown: Occupancy (Active)"
- [ ] **T+180s:** Window transitions to Active
- [ ] Coordinator diagnostic changes: "Shutdown: Occupancy (Active)" → "Shutdown: Window (Active)"
- [ ] **Priority hierarchy enforced:** Window (2) < Occupancy (3), window wins
- [ ] PID remains OFF (already off, now off due to window)
- [ ] **Close window:** Window recovers (60s stability) → Coordinator shows "Shutdown: Occupancy (Active)" again

---

#### Test 3.6: Sensor Unavailability Handling

**Scenario:** HA occupancy sensor becomes unavailable

**Steps:**
1. Room in any state (Normal or Active)
2. Stop Home Assistant or disconnect occupancy sensor
3. Wait for sensor to show "unavailable" in ESPHome
4. Observe fail-safe behavior

**Expected Results:**
- [ ] Occupancy state forced to 0 (Normal) - safe default
- [ ] Text sensor shows: "Occupied (Sensor Unavailable)"
- [ ] Unoccupied duration resets to 0
- [ ] PID control resumes if occupancy was only active condition
- [ ] **Log entry:** `"Soggiorno: Occupancy sensor unavailable, assuming occupied"` (WARN level)
- [ ] When sensor recovers: Normal operation resumes

**Rationale:** Fail-safe to occupied prevents shutting down potentially-occupied rooms

---

#### Test 3.7: Multiple Occupy/Vacate Cycles

**Scenario:** Rapid occupancy changes (stress test)

**Steps:**
1. Enter room (occupied) → Wait 1 min → Leave room
2. Wait 4 min (below 5min threshold) → Enter room
3. Leave room → Wait 6 min (above threshold) → Enter room
4. Repeat cycle 3 times

**Expected Results:**
- [ ] **Cycle 1:** Unoccupied 4 min → Never reaches Active (threshold = 5 min)
- [ ] **Cycle 2:** Unoccupied 6 min → Reaches Active → Immediate recovery on re-entry
- [ ] Unoccupied timer correctly resets on each entry
- [ ] No state machine lock-ups or stuck states
- [ ] PID control tracks occupancy state correctly (OFF during Active only)
- [ ] No memory leaks (free heap stable across cycles)

---

### AC4: Performance and Resource Validation

**Given** occupancy condition running in test room,  
**When** performance measurements are taken,  
**Then** resource usage MUST meet expectations:

#### Performance Metrics

**Firmware Size:**
- [ ] Before occupancy: Baseline firmware size (e.g., 850KB)
- [ ] After occupancy: Firmware size increase ≤2KB
- [ ] Percentage increase: ≤0.25%
- [ ] Flash usage remains <90% total capacity

**Memory (RAM) Usage:**
- [ ] Free heap before: Baseline (e.g., 150KB)
- [ ] Free heap after: Decrease ≤500 bytes
- [ ] Free heap remains >20KB minimum
- [ ] No memory leaks over 24 hours (heap stable)

**CPU Usage:**
- [ ] Baseline CPU usage: X%
- [ ] With occupancy: CPU usage increase ≤0.2%
- [ ] Polling overhead: 10-second interval is negligible
- [ ] No impact on PID control loop timing (1-second update)

**Network Traffic:**
- [ ] HA API calls: +1 subscription (occupancy sensor)
- [ ] HA entity updates: +2 entities (occupancy state, unoccupied duration)
- [ ] Network bandwidth increase: negligible (<1 KB/min)

**Response Times:**
- [ ] Occupancy detection latency: ≤10 seconds (polling interval)
- [ ] Coordinator recognition: ≤5 seconds (coordinator polling)
- [ ] Total shutdown delay: ≤15 seconds (acceptable for energy savings)
- [ ] Recovery delay: ≤15 seconds (acceptable for user experience)

**Temperature Control Impact:**
- [ ] Temperature accuracy: ±0.5°C (unchanged from baseline)
- [ ] Temperature stability: No increase in oscillation
- [ ] No overshoot on resume (PID resumes smoothly)

**Validation:**
- [ ] All performance metrics documented
- [ ] No degradation vs. baseline (Story 9.1 measurements)
- [ ] Meets NFRs from Epic 9 brief

---

### AC5: Energy Savings Measurement

**Given** 48 hours of operation with occupancy detection,  
**When** energy consumption is compared to baseline,  
**Then** measurable savings MUST be demonstrated:

#### Energy Metrics Comparison

**HVAC Runtime Comparison:**
```
Baseline (no occupancy):
  Total runtime: 28 hours (58% of 48h)
  Occupied runtime: 22 hours
  Unoccupied runtime: 6 hours ← TARGET FOR SAVINGS

With Occupancy (5-min timeout):
  Total runtime: 23 hours (48% of 48h)
  Occupied runtime: 22 hours (unchanged)
  Unoccupied runtime: 1 hour (83% reduction)
  
Savings: 5 hours / 28 hours = 17.9% reduction ✅ (within 10-20% target)
```

**Estimated kWh Savings:**
- Assuming 2kW average HVAC power: 5h × 2kW = 10 kWh saved over 48h
- Monthly projection: 10 kWh × 15 = 150 kWh/month per room
- Cost savings (€0.25/kWh): €37.50/month per room
- System-wide (15 rooms): €562.50/month potential savings

**Validation Requirements:**
- [ ] Energy savings ≥10% of baseline HVAC consumption
- [ ] Occupied runtime unchanged (±5% tolerance)
- [ ] Unoccupied runtime reduced significantly (>50%)
- [ ] Temperature control during occupied periods unaffected

**Data Collection:**
```yaml
# HA energy dashboard or SQL query
SELECT 
  SUM(CASE WHEN state = 'heating' OR state = 'cooling' THEN 1 ELSE 0 END) / 60.0 AS runtime_hours,
  SUM(CASE WHEN occupancy.state = 'on' THEN 1 ELSE 0 END) / 60.0 AS occupied_hours
FROM states
WHERE entity_id = 'climate.pid_soggiorno'
  AND last_updated >= NOW() - INTERVAL 48 HOUR
```

---

### AC6: User Experience Validation

**Given** occupancy detection active for 48 hours,  
**When** user experience is evaluated,  
**Then** comfort and usability MUST be acceptable:

#### User Acceptance Criteria

**Comfort:**
- [ ] No complaints of "room too cold when I enter"
- [ ] Room temperature within ±1°C of setpoint when entering (after being off)
- [ ] Recovery to setpoint within 15 minutes of occupancy (acceptable lag)
- [ ] No unexpected shutdowns during actual occupancy (false positives)

**Usability:**
- [ ] HA dashboard clearly shows occupancy state (Occupied / Unoccupied)
- [ ] Coordinator diagnostic clearly indicates shutdown reason ("Occupancy" vs "Window")
- [ ] User can manually override via HA climate entity (set mode to heat/cool)
- [ ] Manual override persists until next unoccupied trigger (no fight with automation)

**Transparency:**
- [ ] User understands when/why room shut down (coordinator diagnostic visible)
- [ ] Unoccupied duration sensor shows time until shutdown (e.g., "240s / 300s")
- [ ] Energy savings visible in HA energy dashboard (motivates continued use)

**Edge Cases:**
- [ ] Test: User sits very still (mmWave detects, PIR doesn't) → No false shutdown
- [ ] Test: User leaves briefly (<5min) → No shutdown (timeout prevents)
- [ ] Test: User manually adjusts thermostat while unoccupied → Respected, then shutdown after timeout
- [ ] Test: HA restart during unoccupied period → State recovers correctly (sensor re-subscribes)

---

### AC7: Documentation and Migration Guide Update

**Given** single-room validation complete,  
**When** learnings are documented,  
**Then** migration guide MUST be updated with real-world experience:

#### Documentation Updates Required

**1. Migration Guide (`docs/epic-9-migration-guide.md` - to be created in Story 9.4):**
- Soggiorno test room results as case study
- Actual deployment time (target: <30 minutes)
- Configuration issues encountered and resolutions
- Validation checklist based on AC1-AC6 tests
- Timeout tuning recommendations based on occupancy patterns

**2. Component Documentation Updates:**
- Add "Validation Results" section to `room_occupancy_condition.yaml` header
- Document typical resource usage (firmware size, RAM, CPU)
- Add troubleshooting tips based on test room issues

**3. Energy Savings Report:**
- Baseline vs. occupancy comparison table
- Per-room savings projection (€/month)
- System-wide savings estimate (15 rooms)
- ROI calculation (software-only, instant payback)

**4. Known Issues / Limitations:**
- Sensor-specific quirks (e.g., PIR blind spots, mmWave sensitivity)
- Timeout tuning challenges (too short = false shutdowns, too long = less savings)
- Recovery lag perception (room slightly cool on entry)
- Manual override behavior (how long does it persist?)

**Validation:**
- [ ] All learnings documented
- [ ] Migration guide draft ready for Story 9.4
- [ ] Troubleshooting section includes actual issues encountered
- [ ] Energy savings report complete with charts/tables

---

## Integration Verification

### IV1: Zero Coordinator Modifications Validated

**Objective:** Confirm Epic 8 interface contract assumption

**Test:**
1. Review `room_control_coordinator.yaml` git diff
2. Confirm zero code changes to coordinator
3. Validate coordinator reads occupancy globals correctly

**Expected:**
- [ ] Coordinator file unchanged (git shows no diff)
- [ ] Coordinator automatically reads `soggiorno_occupancy_state` and `soggiorno_occupancy_priority`
- [ ] Priority resolution algorithm works without modification
- [ ] Diagnostic text sensor shows occupancy state when Active

**Result:** Validates Epic 8 extensibility claim (60% effort reduction vs. pre-Epic 8)

---

### IV2: Multi-Condition Coexistence Validated

**Objective:** Confirm occupancy works alongside emergency and window

**Test Scenarios:**
1. **Occupancy + Emergency:** Trigger both, verify emergency wins (priority 1 < 3)
2. **Occupancy + Window:** Trigger both, verify window wins (priority 2 < 3)
3. **All three + Occupancy:** Trigger emergency/window/occupancy, verify highest priority (emergency) wins

**Expected:**
- [ ] Priority hierarchy correctly enforced in all scenarios
- [ ] Coordinator diagnostic shows correct active condition
- [ ] When higher-priority condition clears, next priority takes over
- [ ] All conditions operate independently (no cross-talk)

---

### IV3: Backward Compatibility Validated

**Objective:** Ensure existing functionality unaffected

**Test:**
1. Deploy occupancy to Soggiorno (test room)
2. Verify other rooms (Cucina, Bagno, etc.) unaffected
3. Confirm no entity_id conflicts
4. Validate no performance impact on other rooms

**Expected:**
- [ ] Other rooms compile and deploy successfully
- [ ] Other rooms' temperature control unchanged
- [ ] No increase in coordinator CPU usage globally
- [ ] HA shows new occupancy entities for Soggiorno only

---

### IV4: OTA Deployment Validated

**Objective:** Confirm safe production deployment method

**Test:**
1. Deploy via OTA (not USB)
2. Monitor deployment progress
3. Verify no downtime during deployment
4. Confirm rollback capability if needed

**Expected:**
- [ ] OTA update succeeds within 2 minutes
- [ ] No climate control interruption during update
- [ ] Room recovers immediately post-update
- [ ] Previous firmware binary saved for emergency rollback

---

## Definition of Done

**This story is complete when:**

- [ ] Soggiorno configured with occupancy detection and deployed
- [ ] All 7 acceptance criteria validated and passing
- [ ] All 18 functional tests (AC3) pass successfully
- [ ] Performance metrics meet requirements (AC4)
- [ ] Energy savings ≥10% demonstrated (AC5)
- [ ] User experience acceptable (AC6)
- [ ] Documentation updated with learnings (AC7)
- [ ] All 4 integration verifications pass (IV1-IV4)
- [ ] Zero coordinator modifications confirmed
- [ ] 48-hour soak test completed (stability validation)
- [ ] Energy savings report complete
- [ ] Migration guide draft ready for Story 9.4
- [ ] Lessons learned documented
- [ ] Go/No-Go decision made for Story 9.4 (multi-room rollout)

**Ready for Story 9.4:** Multi-room rollout (remaining 14+ rooms)

---

## Testing Strategy

### Phase 1: Deployment and Basic Validation (Day 1)

**Morning (2 hours):**
- [ ] Update Soggiorno configuration with occupancy condition
- [ ] Compile and validate firmware
- [ ] Deploy via OTA
- [ ] Verify all entities appear in HA
- [ ] Run functional tests 3.1-3.3 (basic operation)

**Afternoon (2 hours):**
- [ ] Run functional tests 3.4-3.7 (priority hierarchy, edge cases)
- [ ] Collect initial performance metrics
- [ ] Document any issues encountered
- [ ] Adjust timeout if needed (initially 5 min testing)

---

### Phase 2: Baseline Collection (Days 1-3)

**48-Hour Baseline (No Occupancy):**
- [ ] Disable occupancy condition temporarily (use stub)
- [ ] Collect HVAC runtime, occupancy patterns, temperature data
- [ ] Document unoccupied periods for savings calculation
- [ ] Baseline report generated

**48-Hour With Occupancy (Testing):**
- [ ] Re-enable occupancy condition (5-min timeout)
- [ ] Collect same metrics as baseline
- [ ] Monitor for false shutdowns or issues
- [ ] User experience feedback

---

### Phase 3: Extended Soak Test (Days 4-7)

**7-Day Stability Test:**
- [ ] Run with occupancy detection continuously
- [ ] Adjust timeout to production value (2 hours) after 48h testing
- [ ] Monitor for:
  - Memory leaks (heap stability)
  - State machine lock-ups
  - False shutdowns
  - User complaints
  - Energy savings consistency
- [ ] Collect weekly energy report

---

### Phase 4: Go/No-Go Decision (Day 7)

**Evaluation Criteria:**
- [ ] Energy savings ≥10% validated
- [ ] Zero coordinator modifications confirmed
- [ ] No critical bugs or state machine issues
- [ ] User experience acceptable (no comfort complaints)
- [ ] Performance meets requirements
- [ ] Documentation complete

**Decision:**
- ✅ **GO:** Proceed to Story 9.4 (multi-room rollout)
- ❌ **NO-GO:** Address issues, extend validation period

---

## Dependencies

**Requires (must be complete first):**
- ✅ Story 9.1: Occupancy condition component
- ✅ Story 9.2: Occupancy stub component
- ✅ Test room (Soggiorno) has reliable HA occupancy sensor
- ✅ Energy monitoring configured in HA

**Blocks (waiting on this story):**
- ⏳ Story 9.4: Multi-room rollout (needs validation success)
- ⏳ Story 9.5: Epic 9 completion report (needs final metrics)

---

## Risks and Mitigations

**Risk 1: Energy Savings Below 10% Target**
- **Likelihood:** Medium (depends on occupancy patterns)
- **Impact:** High (questions Epic 9 value proposition)
- **Mitigation:** 
  - Choose high-traffic room with clear occupied/unoccupied cycles
  - Adjust timeout if needed (shorter = more savings, higher false shutdown risk)
  - Extend measurement period to 1 week for better averaging
- **Contingency:** Proceed if savings ≥5% (still valuable), document lessons

**Risk 2: False Shutdowns During Occupancy**
- **Likelihood:** Low-Medium (depends on sensor quality)
- **Impact:** High (user comfort complaints, loss of trust)
- **Mitigation:**
  - Use room with reliable mmWave sensor (not just PIR)
  - Conservative 2-hour timeout in production (5 min only for testing)
  - Fail-safe to occupied on sensor unavailability
- **Contingency:** Increase timeout for affected room, upgrade sensor if needed

**Risk 3: Coordinator Modifications Required**
- **Likelihood:** Very Low (interface contract well-defined)
- **Impact:** High (invalidates Epic 8 extensibility claim)
- **Mitigation:**
  - Thorough code review of occupancy component vs. interface spec
  - Story 9.1 AC1 validates interface compliance
- **Contingency:** Document required changes, update Epic 8 interface spec, revisit Epic 9 effort estimates

**Risk 4: Performance Degradation**
- **Likelihood:** Low (10s polling is low frequency)
- **Impact:** Medium (could affect other rooms)
- **Mitigation:**
  - Performance measurements in Story 9.1 establish baseline
  - Monitor free heap, CPU usage during validation
- **Contingency:** Optimize polling interval, reduce logging verbosity

**Risk 5: User Resistance to Behavior**
- **Likelihood:** Low-Medium (depends on communication)
- **Impact:** Medium (adoption failure)
- **Mitigation:**
  - Clear documentation of expected behavior
  - HA dashboard visibility (occupancy state, shutdown reason)
  - Manual override capability always available
  - User education: "Room may be slightly cool when entering, warms up in 10-15 min"
- **Contingency:** Disable occupancy for specific rooms if user requests

---

## Success Metrics

**Technical Success:**
- ✅ Zero coordinator modifications (validates Epic 8 interface)
- ✅ All 18 functional tests pass
- ✅ Performance within budget (≤2KB firmware, ≤500B RAM, ≤0.2% CPU)
- ✅ 7-day soak test passes (no crashes, leaks, or lock-ups)

**Business Success:**
- ✅ Energy savings ≥10% (target: 10-20%)
- ✅ User experience acceptable (no major comfort complaints)
- ✅ Deployment time ≤30 minutes (configuration + OTA + validation)
- ✅ Documentation complete (migration guide ready for Story 9.4)

**Go/No-Go Decision:**
- ✅ **GO to Story 9.4** if all above criteria met
- ⚠️ **Extend validation** if minor issues (1-2 criteria missed)
- ❌ **No-Go** if critical issues (coordinator changes needed, <5% savings, major bugs)

---

## Story Completion Notes

*[To be filled in by developer upon completion]*

**Test Room:** Soggiorno  
**Deployment Date:** ___  
**Validation Period:** ___ days

**Energy Savings Results:**
- Baseline HVAC runtime: ___ hours
- With occupancy runtime: ___ hours
- Savings: ___% (target: ≥10%)
- Estimated monthly savings: €___

**Performance Results:**
- Firmware size increase: ___ KB
- RAM usage increase: ___ bytes
- CPU usage increase: ___%
- All within budget: ✅ / ❌

**Functional Testing:**
- Tests passed: ___ / 18
- Critical failures: ___
- Minor issues: ___

**User Experience:**
- Comfort complaints: ___
- False shutdowns: ___
- Recovery time acceptable: ✅ / ❌

**Lessons Learned:**
- What went well: ___
- What could be improved: ___
- Timeout tuning insights: ___
- Sensor reliability notes: ___

**Go/No-Go Decision:**
- Decision: GO / NO-GO / EXTEND
- Rationale: ___
- Recommendations for Story 9.4: ___

**Artifacts Created:**
- Energy savings report: ___
- Performance measurements: ___
- Migration guide draft: ___
- Known issues list: ___

---

**Story Status:** Ready for Development  
**Dependencies:** Stories 9.1, 9.2 (Occupancy condition + stub)  
**Next Story:** 9.4 - Multi-Room Rollout (Remaining 14+ Rooms)

---

*Story created for Epic 9: Occupancy-Based Climate Shutdown*  
*Story Date: November 5, 2025*
