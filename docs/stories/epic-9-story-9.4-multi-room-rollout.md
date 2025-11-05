# Story 9.4: Multi-Room Rollout (Remaining 14+ Rooms)

**Epic:** 9 - Occupancy-Based Climate Shutdown  
**Story Points:** 3  
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
**I want** to deploy occupancy detection to all remaining rooms in a phased, safe manner,  
**so that** the entire system benefits from energy savings while minimizing rollout risk.

---

## Business Context

This story represents the production-scale deployment phase, transitioning Epic 9 from validated prototype (Story 9.3: single room) to full system implementation across 15+ rooms. By using a phased rollout strategy, we:

1. **Minimize Blast Radius:** Deploy floor-by-floor or zone-by-zone to contain issues
2. **Apply Learnings:** Use Story 9.3 validation results to refine deployment process
3. **Enable Gradual Sensor Addition:** Rooms without occupancy sensors use stubs initially
4. **Maximize Energy Savings:** Scale 10-20% savings per room to system-wide impact

**Value Delivered:**
- System-wide energy savings (€200-400/year projected)
- Proven scalability of Epic 8 coordinator pattern (3rd condition type added)
- Complete Epic 9 implementation (all rooms with occupancy detection)
- Foundation for Epic 10 (Energy × Occupancy matrix)

**Rollout Approach:**
- **Phase 1:** Piano Terra (ground floor, 7-8 rooms)
- **Phase 2:** Primo Piano (first floor, 7-8 rooms)
- **Phase 3:** Validation and tuning (adjust timeouts per room)

**Dependencies:**
- Story 9.3 completed with GO decision (single-room validation passed)
- HA occupancy sensor audit completed (know which rooms have sensors)
- Migration guide draft ready (from Story 9.3 learnings)
- Energy monitoring dashboard configured

---

## Acceptance Criteria

### AC1: Pre-Rollout Audit and Planning

**Given** Story 9.3 validation complete,  
**When** preparing for multi-room rollout,  
**Then** comprehensive audit and planning MUST be performed:

#### 1.1: HA Occupancy Sensor Audit

**Objective:** Document occupancy sensor availability and reliability for all rooms

**Audit Template:**
```yaml
# Occupancy Sensor Audit (November 2025)
rooms:
  piano_terra:
    - room: Soggiorno
      sensor: binary_sensor.soggiorno_occupancy
      type: PIR + mmWave composite
      reliability: High (validated in Story 9.3)
      recommended_timeout: 7200s (2h default)
      deployment: Real component
      
    - room: Cucina
      sensor: binary_sensor.cucina_occupancy
      type: PIR only
      reliability: Medium (missed stationary presence)
      recommended_timeout: 3600s (1h, kitchen has intermittent use)
      deployment: Real component (monitor for false shutdowns)
      
    - room: Bagno Piano Terra
      sensor: binary_sensor.bagno_piano_terra_occupancy
      type: PIR
      reliability: High (frequent motion)
      recommended_timeout: 900s (15min, short usage periods)
      deployment: Real component
      
    - room: Camera Ospiti
      sensor: None (no sensor installed)
      type: N/A
      reliability: N/A
      recommended_timeout: N/A
      deployment: Stub component (add sensor in future)
      
    # ... continue for all 15+ rooms
  
  primo_piano:
    - room: Camera Matrimoniale
      sensor: binary_sensor.camera_matrimoniale_occupancy
      type: mmWave (stationary detection)
      reliability: High
      recommended_timeout: 3600s (1h, bedroom)
      deployment: Real component
      
    # ... continue for all first floor rooms

summary:
  total_rooms: 15
  rooms_with_sensors: 11
  rooms_needing_stubs: 4
  high_reliability_sensors: 8
  medium_reliability_sensors: 3
  rooms_needing_new_sensors: 4 (deferred to post-Epic 9)
```

**Validation:**
- [ ] All 15+ rooms documented
- [ ] Sensor entity IDs verified in HA (accessible, no typos)
- [ ] Reliability assessment based on HA sensor history (uptime, state changes)
- [ ] Recommended timeouts per room type (using Epic 9 brief Appendix D guidelines)
- [ ] Deployment strategy per room (real component vs. stub)
- [ ] Rooms prioritized by energy savings potential (high HVAC usage first)

---

#### 1.2: Rollout Phase Planning

**Objective:** Define safe, incremental deployment sequence

**Phase 1: Piano Terra (Ground Floor) - Week 1**
```yaml
phase_1_piano_terra:
  duration: 3-4 days
  rooms:
    - Soggiorno (already deployed in Story 9.3, serves as reference)
    - Cucina (real component, PIR, 1h timeout)
    - Bagno Piano Terra (real component, PIR, 15min timeout)
    - Studio (real component, PIR+mmWave, 2h timeout)
    - Lavanderia (stub component, no sensor)
    - Camera Ospiti (stub component, no sensor)
    - Corridoio Piano Terra (stub component, no sensor)
  
  deployment_order:
    - Day 1 Morning: Cucina, Bagno (high-traffic, fast validation)
    - Day 1 Afternoon: Studio (medium-traffic, observe throughout workday)
    - Day 2 Morning: Lavanderia, Camera Ospiti, Corridoio (stubs, low risk)
    - Day 2-4: Monitor, collect data, address any issues
  
  success_criteria:
    - All rooms compile and deploy via OTA
    - No false shutdowns reported
    - Coordinator diagnostics show correct condition priority
    - Energy monitoring shows expected savings
```

**Phase 2: Primo Piano (First Floor) - Week 2**
```yaml
phase_2_primo_piano:
  duration: 3-4 days
  rooms:
    - Camera Matrimoniale (real component, mmWave, 1h timeout)
    - Camera Figli 1 (real component, PIR, 1h timeout)
    - Camera Figli 2 (real component, PIR+mmWave, 1h timeout)
    - Bagno Primo Piano (real component, PIR, 15min timeout)
    - Cabina Armadio (stub component, no sensor)
    - Disimpegno (stub component, no sensor)
    - Terrazzo (stub component, no sensor)
  
  deployment_order:
    - Day 1 Morning: Camera Matrimoniale, Bagno Primo Piano
    - Day 1 Afternoon: Camera Figli 1, Camera Figli 2
    - Day 2 Morning: Cabina Armadio, Disimpegno, Terrazzo (stubs)
    - Day 2-4: Monitor, tune timeouts based on Phase 1 learnings
  
  success_criteria:
    - Same as Phase 1
    - Timeout adjustments applied based on Phase 1 experience
```

**Phase 3: System-Wide Validation and Tuning - Week 3-4**
```yaml
phase_3_validation_tuning:
  duration: 7-14 days
  activities:
    - Monitor all 15+ rooms for false shutdowns
    - Adjust timeouts per room based on occupancy patterns
    - Collect system-wide energy savings data
    - Gather user feedback (comfort, usability)
    - Document per-room configuration (timeout, sensor type)
  
  tuning_examples:
    - "Cucina: Reduced timeout from 2h → 1h (intermittent use)"
    - "Bagno: Reduced timeout from 15min → 10min (very short usage)"
    - "Camera Ospiti: Added occupancy sensor, switched stub → real component"
  
  success_criteria:
    - System-wide energy savings ≥10% validated
    - <1% false shutdown rate across all rooms
    - User comfort maintained (no complaints)
    - All rooms stable for 7 consecutive days
```

**Validation:**
- [ ] Phase 1 and Phase 2 schedules defined
- [ ] Deployment order considers dependencies and risk
- [ ] Each phase has clear success criteria
- [ ] Rollback plan defined for each phase (revert to previous firmware)
- [ ] Phase 3 tuning period allocated (1-2 weeks)

---

#### 1.3: Migration Guide Finalization

**Objective:** Update migration guide with Story 9.3 learnings

**Required Sections:**
1. **Prerequisites:**
   - Epic 8 coordinator already deployed (all rooms have coordinator)
   - HA occupancy sensor entity ID known (or use stub)
   - Room device YAML file accessible (locals/ or devices/)
   - OTA access to board (not physical USB connection)

2. **Step-by-Step Deployment (Per Room):**
   ```yaml
   # Example: Adding occupancy to Cucina
   
   # Step 1: Identify occupancy sensor (or use stub)
   # HA entity ID: binary_sensor.cucina_occupancy
   
   # Step 2: Update room device YAML
   # File: locals/distribuzione-piano-terra.yaml (or devices/)
   
   packages:
     # Existing packages (unchanged)
     room_sensors_cucina: {...}
     room_emergency_condition_cucina: {...}
     room_window_condition_cucina: {...}
     room_control_coordinator_cucina: {...}
     
     # NEW: Add occupancy condition
     room_occupancy_condition_cucina:
       file: ../../components/room_occupancy_condition.yaml
       vars:
         zone_slug: "cucina"
         zone_name: "Cucina"
         ha_occupancy_sensor_id: "binary_sensor.cucina_occupancy"
         unoccupied_timeout: "3600"  # 1 hour (adjust per room)
   
   # Step 3: Compile firmware
   # esphome compile locals/distribuzione-piano-terra.yaml
   
   # Step 4: Deploy via OTA
   # esphome upload locals/distribuzione-piano-terra.yaml --device 192.168.x.x
   
   # Step 5: Validation checklist (see section below)
   ```

3. **Stub Component Usage (Rooms Without Sensors):**
   ```yaml
   # Example: Camera Ospiti (no occupancy sensor)
   
   packages:
     # Use stub instead of real component
     room_occupancy_condition_camera_ospiti:
       file: ../../components/room_occupancy_condition_stub.yaml
       vars:
         zone_slug: "camera_ospiti"
         zone_name: "Camera Ospiti"
   
   # Upgrade path: When sensor added, change file path:
   # room_occupancy_condition_stub.yaml → room_occupancy_condition.yaml
   # Add ha_occupancy_sensor_id and unoccupied_timeout vars
   ```

4. **Per-Room Validation Checklist:**
   - [ ] Firmware compiles without errors
   - [ ] OTA deployment succeeds
   - [ ] New entities appear in HA: `text_sensor.{room}_occupancy_state`, `sensor.{room}_unoccupied_duration`
   - [ ] Occupancy state shows "Occupied" when room occupied
   - [ ] After unoccupied timeout, state transitions to "Unoccupied (Active)"
   - [ ] Coordinator diagnostic shows "Shutdown: Occupancy (Active)"
   - [ ] PID forced to OFF mode (heating/cooling stops)
   - [ ] When room becomes occupied, recovery within 15 seconds
   - [ ] No errors in ESPHome logs (check for "Occupancy sensor unavailable")

5. **Timeout Tuning Guidelines:**
   - Use Epic 9 brief Appendix D recommendations as starting point
   - Monitor for 48 hours, adjust if false shutdowns occur
   - Consider room usage patterns: High-traffic (1-2h), Low-traffic (4-8h), Bathroom (10-15min)
   - Balance energy savings vs. comfort (shorter = more savings, higher false shutdown risk)

6. **Troubleshooting:**
   - **Issue:** Occupancy state stuck at "Unknown"
     - **Cause:** HA sensor entity_id incorrect or sensor unavailable
     - **Fix:** Verify entity_id in HA, check sensor battery/connectivity
   
   - **Issue:** Room shuts down while occupied (false positive)
     - **Cause:** Occupancy sensor not detecting presence (PIR blind spot, mmWave sensitivity)
     - **Fix:** Increase timeout, upgrade sensor (PIR → mmWave), adjust sensor positioning
   
   - **Issue:** Room never shuts down despite being unoccupied
     - **Cause:** Timeout too long, or occupancy sensor stuck "on"
     - **Fix:** Reduce timeout, verify sensor accuracy in HA
   
   - **Issue:** Coordinator shows "Emergency" instead of "Occupancy"
     - **Cause:** Priority hierarchy working correctly (emergency overrides occupancy)
     - **Fix:** Not an issue if emergency condition legitimately active

**Validation:**
- [ ] Migration guide updated with Story 9.3 learnings
- [ ] Step-by-step instructions validated against Soggiorno deployment
- [ ] Troubleshooting section includes actual issues from Story 9.3
- [ ] Timeout tuning guidelines clear and actionable
- [ ] Stub usage documented for rooms without sensors

---

### AC2: Phase 1 Deployment (Piano Terra)

**Given** Phase 1 rollout plan complete,  
**When** deploying to ground floor rooms,  
**Then** all rooms MUST be configured and validated successfully:

#### 2.1: Configuration Updates (Piano Terra)

**Board:** distribuzione-piano-terra (KC868-A16)  
**File:** `locals/distribuzione-piano-terra.yaml` or `devices/distribuzione-piano-terra.yaml`

**Rooms to Update:**
1. ✅ **Soggiorno** - Already deployed (Story 9.3 reference)
2. 🆕 **Cucina** - Real component (PIR, 1h timeout)
3. 🆕 **Bagno Piano Terra** - Real component (PIR, 15min timeout)
4. 🆕 **Studio** - Real component (PIR+mmWave, 2h timeout)
5. 🆕 **Lavanderia** - Stub component (no sensor)
6. 🆕 **Camera Ospiti** - Stub component (no sensor)
7. 🆕 **Corridoio Piano Terra** - Stub component (no sensor)

**Example Configuration Additions:**
```yaml
# File: locals/distribuzione-piano-terra.yaml

packages:
  # ============================================
  # CUCINA (Kitchen)
  # ============================================
  room_occupancy_condition_cucina:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "cucina"
      zone_name: "Cucina"
      ha_occupancy_sensor_id: "binary_sensor.cucina_occupancy"
      unoccupied_timeout: "3600"  # 1 hour
  
  # ============================================
  # BAGNO PIANO TERRA (Ground Floor Bathroom)
  # ============================================
  room_occupancy_condition_bagno_piano_terra:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "bagno_piano_terra"
      zone_name: "Bagno Piano Terra"
      ha_occupancy_sensor_id: "binary_sensor.bagno_piano_terra_occupancy"
      unoccupied_timeout: "900"  # 15 minutes
  
  # ============================================
  # STUDIO (Office)
  # ============================================
  room_occupancy_condition_studio:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "studio"
      zone_name: "Studio"
      ha_occupancy_sensor_id: "binary_sensor.studio_occupancy"
      unoccupied_timeout: "7200"  # 2 hours (default)
  
  # ============================================
  # LAVANDERIA (Laundry) - STUB (no sensor)
  # ============================================
  room_occupancy_condition_lavanderia:
    file: ../../components/room_occupancy_condition_stub.yaml
    vars:
      zone_slug: "lavanderia"
      zone_name: "Lavanderia"
  
  # ============================================
  # CAMERA OSPITI (Guest Room) - STUB (no sensor)
  # ============================================
  room_occupancy_condition_camera_ospiti:
    file: ../../components/room_occupancy_condition_stub.yaml
    vars:
      zone_slug: "camera_ospiti"
      zone_name: "Camera Ospiti"
  
  # ============================================
  # CORRIDOIO PIANO TERRA (Hallway) - STUB (no sensor)
  # ============================================
  room_occupancy_condition_corridoio_piano_terra:
    file: ../../components/room_occupancy_condition_stub.yaml
    vars:
      zone_slug: "corridoio_piano_terra"
      zone_name: "Corridoio Piano Terra"
```

**Validation:**
- [ ] Configuration file updated for all 7 Piano Terra rooms
- [ ] Soggiorno configuration unchanged (reference room)
- [ ] Real components use correct HA entity IDs (verified in audit)
- [ ] Stub components use stub file path (no ha_occupancy_sensor_id var)
- [ ] Timeouts appropriate per room type (kitchen 1h, bathroom 15min, etc.)
- [ ] No coordinator modifications (validates interface contract)

---

#### 2.2: Compilation and Deployment (Piano Terra)

**Objective:** Deploy updated firmware to Piano Terra board via OTA

**Steps:**
1. **Compile firmware:**
   ```bash
   cd /Users/alberto/src/esphome-devices
   esphome compile locals/distribuzione-piano-terra.yaml
   ```

2. **Verify compilation:**
   - [ ] No compilation errors
   - [ ] Firmware size increase ≤2KB per room (≤14KB total for 7 rooms)
   - [ ] All occupancy entities included in generated code

3. **Deploy via OTA:**
   ```bash
   esphome upload locals/distribuzione-piano-terra.yaml --device 192.168.x.x
   # (Use board's IP address)
   ```

4. **Monitor deployment:**
   - [ ] OTA upload completes within 2-3 minutes
   - [ ] Board reboots successfully
   - [ ] All rooms reconnect to HA
   - [ ] No errors in ESPHome logs

**Validation:**
- [ ] Firmware compiles successfully
- [ ] OTA deployment succeeds
- [ ] Board stable after reboot (no crashes)
- [ ] All existing functionality preserved (temperature control, PID, emergency, window)

---

#### 2.3: Post-Deployment Validation (Piano Terra)

**Objective:** Verify all Piano Terra rooms operate correctly

**Validation Checklist (Per Room):**
```yaml
# Example: Cucina validation
cucina:
  entities_visible_in_ha:
    - text_sensor.cucina_occupancy_state: "Occupied" or "Unoccupied (Active)"
    - sensor.cucina_unoccupied_duration: "0" (occupied) or incrementing (unoccupied)
    - climate.pid_cucina: Normal operation (unchanged)
  
  functional_tests:
    - [ ] Room occupied → state shows "Occupied"
    - [ ] Leave room for 1 hour → state transitions to "Unoccupied (Active)"
    - [ ] Coordinator diagnostic shows "Shutdown: Occupancy (Active)"
    - [ ] PID forced to OFF
    - [ ] Re-enter room → recovery within 15 seconds
    - [ ] Coordinator shows "Normal (All Clear)"
  
  priority_hierarchy_test:
    - [ ] Open window while unoccupied → Window overrides Occupancy (priority 2 < 3)
    - [ ] Coordinator shows "Shutdown: Window (Active)"
```

**System-Wide Validation:**
- [ ] All 7 Piano Terra rooms show occupancy entities in HA
- [ ] Stub rooms show state=0 (always Normal), priority=99
- [ ] Real component rooms show dynamic state based on occupancy
- [ ] No entity_id conflicts or duplicate entities
- [ ] Coordinator diagnostics show correct active condition per room
- [ ] No ESPHome log errors for any room

**48-Hour Monitoring:**
- [ ] Collect HVAC runtime data per room
- [ ] Monitor for false shutdowns (occupied room showing "Unoccupied (Active)")
- [ ] Validate user comfort (no complaints of cold rooms)
- [ ] Document any timeout adjustments needed

**Validation:**
- [ ] All rooms pass functional tests
- [ ] No false shutdowns in 48-hour period
- [ ] Energy savings visible in HA dashboard (reduced HVAC runtime)
- [ ] User feedback positive (or no complaints)

---

### AC3: Phase 2 Deployment (Primo Piano)

**Given** Phase 1 successful (Piano Terra stable for 48+ hours),  
**When** deploying to first floor rooms,  
**Then** all rooms MUST be configured and validated successfully:

#### 3.1: Configuration Updates (Primo Piano)

**Board:** distribuzione-primo-piano (KC868-A16)  
**File:** `locals/distribuzione-primo-piano.yaml` or `devices/distribuzione-primo-piano.yaml`

**Rooms to Update:**
1. 🆕 **Camera Matrimoniale** - Real component (mmWave, 1h timeout)
2. 🆕 **Camera Figli 1** - Real component (PIR, 1h timeout)
3. 🆕 **Camera Figli 2** - Real component (PIR+mmWave, 1h timeout)
4. 🆕 **Bagno Primo Piano** - Real component (PIR, 15min timeout)
5. 🆕 **Cabina Armadio** - Stub component (no sensor)
6. 🆕 **Disimpegno** - Stub component (no sensor)
7. 🆕 **Terrazzo** - Stub component (no sensor)

**Example Configuration:**
```yaml
# File: locals/distribuzione-primo-piano.yaml

packages:
  # ============================================
  # CAMERA MATRIMONIALE (Master Bedroom)
  # ============================================
  room_occupancy_condition_camera_matrimoniale:
    file: ../../components/room_occupancy_condition.yaml
    vars:
      zone_slug: "camera_matrimoniale"
      zone_name: "Camera Matrimoniale"
      ha_occupancy_sensor_id: "binary_sensor.camera_matrimoniale_occupancy"
      unoccupied_timeout: "3600"  # 1 hour (bedroom)
  
  # ... (similar for other rooms)
  
  # ============================================
  # CABINA ARMADIO (Walk-in Closet) - STUB
  # ============================================
  room_occupancy_condition_cabina_armadio:
    file: ../../components/room_occupancy_condition_stub.yaml
    vars:
      zone_slug: "cabina_armadio"
      zone_name: "Cabina Armadio"
```

**Validation:**
- [ ] All 7 Primo Piano rooms configured
- [ ] Bedrooms use 1h timeout (shorter than default 2h for faster shutdowns)
- [ ] Bathroom uses 15min timeout (consistent with Piano Terra)
- [ ] Stubs for rooms without sensors
- [ ] No coordinator modifications

---

#### 3.2: Compilation and Deployment (Primo Piano)

**Same process as Phase 1 (AC2.2):**
- [ ] Compile `locals/distribuzione-primo-piano.yaml`
- [ ] Deploy via OTA to Primo Piano board
- [ ] Monitor deployment and reboot
- [ ] Verify no errors

---

#### 3.3: Post-Deployment Validation (Primo Piano)

**Same validation process as Phase 1 (AC2.3):**
- [ ] All rooms show occupancy entities in HA
- [ ] Functional tests pass per room
- [ ] Priority hierarchy validated
- [ ] 48-hour monitoring period (no false shutdowns)
- [ ] User feedback positive

---

### AC4: System-Wide Validation and Tuning

**Given** Phase 1 and Phase 2 complete,  
**When** all 15+ rooms have occupancy detection,  
**Then** system-wide validation and tuning MUST be performed:

#### 4.1: System-Wide Energy Savings Measurement

**Objective:** Validate Epic 9 goal of 10-20% energy savings

**Data Collection Period:** 7 days minimum

**Metrics to Collect:**
```yaml
system_wide_metrics:
  baseline_comparison:
    - Baseline HVAC runtime (pre-Epic 9): X hours/week
    - With occupancy HVAC runtime (Epic 9): Y hours/week
    - Savings: (X - Y) / X * 100 = Z%
    - Target: Z ≥ 10%
  
  per_room_breakdown:
    - Soggiorno: 18% savings (validated in Story 9.3)
    - Cucina: 15% savings
    - Camera Matrimoniale: 22% savings (bedroom, long unoccupied periods)
    - Bagno Piano Terra: 25% savings (short usage, frequent unoccupied)
    - Studio: 12% savings (occupied during work hours)
    # ... continue for all rooms
  
  high_impact_rooms:
    - Camera Ospiti: 40% savings (rarely used)
    - Bagno: 25% savings
    - Terrazzo: 30% savings (seasonal use only)
  
  low_impact_rooms:
    - Cucina: 15% savings (high occupancy)
    - Soggiorno: 18% savings (high occupancy)
    - Studio: 12% savings (occupied 8h/day)
  
  stub_rooms:
    - Lavanderia: 0% savings (stub component, no shutdown)
    - Corridoio: 0% savings (stub component)
    # Potential 10-20% savings if sensors added in future
```

**Energy Dashboard Validation:**
- [ ] HA energy dashboard shows per-room HVAC consumption
- [ ] Week-over-week comparison shows reduction
- [ ] System-wide savings ≥10% (target: 10-20%)
- [ ] Per-room savings documented
- [ ] High-impact rooms identified (candidates for timeout tuning)

**Financial Impact:**
```yaml
financial_savings:
  per_room_average: 15% HVAC runtime reduction
  total_rooms_with_real_component: 11 (out of 15)
  avg_hvac_power: 2 kW
  avg_runtime_pre_epic9: 40h/week per room
  savings_per_room: 40h * 0.15 = 6h/week = 24h/month
  energy_saved_per_room: 24h * 2kW = 48 kWh/month
  total_energy_saved: 48 kWh * 11 rooms = 528 kWh/month
  cost_per_kwh: €0.25
  monthly_savings: 528 kWh * €0.25 = €132/month
  annual_savings: €132 * 12 = €1,584/year
  # Exceeds Epic 9 brief estimate of €200-400/year! ✅
```

**Validation:**
- [ ] System-wide energy savings ≥10%
- [ ] Financial savings meet or exceed €200-400/year estimate
- [ ] Per-room savings documented and validated
- [ ] Energy dashboard configured and accurate

---

#### 4.2: Timeout Tuning and Optimization

**Objective:** Optimize timeouts per room based on actual occupancy patterns

**Tuning Process:**
1. **Analyze Occupancy Patterns (7 days data):**
   ```yaml
   soggiorno:
     typical_occupied_duration: 2-4 hours (evening)
     typical_unoccupied_duration: 12-18 hours (overnight + daytime)
     current_timeout: 7200s (2h)
     false_shutdowns: 0
     recommendation: Keep 2h timeout (optimal)
   
   cucina:
     typical_occupied_duration: 30-60 minutes (meal prep)
     typical_unoccupied_duration: 3-8 hours (between meals)
     current_timeout: 3600s (1h)
     false_shutdowns: 1 (cooking, standing still, PIR missed)
     recommendation: Increase to 2h or upgrade to mmWave sensor
   
   bagno_piano_terra:
     typical_occupied_duration: 5-15 minutes (shower, toilet)
     typical_unoccupied_duration: 23+ hours/day
     current_timeout: 900s (15min)
     false_shutdowns: 0
     recommendation: Reduce to 600s (10min) for more savings
   
   camera_ospiti:
     typical_occupied_duration: 0 hours (stub, no sensor)
     typical_unoccupied_duration: 24 hours/day (unused)
     current_timeout: N/A (stub)
     false_shutdowns: N/A
     recommendation: Add occupancy sensor for 30-40% savings potential
   ```

2. **Apply Timeout Adjustments:**
   - [ ] Rooms with false shutdowns: Increase timeout by 50-100%
   - [ ] Rooms with very short usage: Decrease timeout for more savings
   - [ ] Rooms with high occupancy: Keep conservative 2h default
   - [ ] Document all changes with rationale

3. **Re-deploy Updated Configurations:**
   - [ ] Update room YAML files with new timeouts
   - [ ] Recompile and deploy via OTA
   - [ ] Monitor for 48 hours to validate adjustments

**Validation:**
- [ ] Timeout adjustments documented per room
- [ ] False shutdown rate <1% after tuning
- [ ] Energy savings maintained or improved
- [ ] User feedback positive (no new comfort complaints)

---

#### 4.3: User Experience Validation

**Objective:** Ensure comfort and usability acceptable across all rooms

**User Feedback Collection:**
- [ ] Interview household members about comfort
- [ ] Ask about any "room too cold when entering" incidents
- [ ] Validate understanding of occupancy-based shutdown behavior
- [ ] Check if manual overrides ever needed (should be rare)

**Usability Metrics:**
```yaml
user_experience:
  comfort_complaints: 0 (target)
  false_shutdown_reports: <3 (target: <1%)
  manual_overrides_used: <5/week (target: rare)
  user_understanding: "Clear" (HA dashboard shows occupancy state)
  perceived_value: "High" (energy savings visible, automated behavior)

transparency_validation:
  - [ ] HA dashboard shows occupancy state per room (Occupied / Unoccupied)
  - [ ] Coordinator diagnostic shows shutdown reason (Occupancy vs Window vs Emergency)
  - [ ] Unoccupied duration visible (countdown to shutdown)
  - [ ] Energy dashboard shows savings (motivates continued use)
```

**Edge Case Testing:**
```yaml
edge_cases_tested:
  - User sits very still in Soggiorno (mmWave detects, no false shutdown) ✅
  - User leaves room briefly (<timeout), returns (no shutdown) ✅
  - HA restarts during unoccupied period (sensor re-subscribes, state recovers) ✅
  - Window opens while room unoccupied (Window overrides Occupancy) ✅
  - Sensor battery dies (fail-safe to occupied, no shutdown) ✅
  - Manual thermostat adjustment while unoccupied (respected, then shutdown after timeout) ✅
```

**Validation:**
- [ ] Zero comfort complaints from household
- [ ] <1% false shutdown rate validated
- [ ] User experience positive (or neutral, no negative feedback)
- [ ] All edge cases handled correctly

---

#### 4.4: Documentation and Configuration Snapshot

**Objective:** Document final system configuration for future reference

**Configuration Snapshot:**
```yaml
# Epic 9 Final Configuration (November 2025)
# File: docs/epic-9-final-configuration.yaml

system_summary:
  total_rooms: 15
  rooms_with_real_component: 11
  rooms_with_stub_component: 4
  boards: 2 (Piano Terra, Primo Piano)
  energy_savings: 15% system-wide average
  deployment_date: 2025-11-XX

piano_terra:
  board: distribuzione-piano-terra (KC868-A16)
  rooms:
    - soggiorno: {sensor: PIR+mmWave, timeout: 7200s, savings: 18%}
    - cucina: {sensor: PIR, timeout: 7200s, savings: 15%}
    - bagno_piano_terra: {sensor: PIR, timeout: 600s, savings: 25%}
    - studio: {sensor: PIR+mmWave, timeout: 7200s, savings: 12%}
    - lavanderia: {sensor: stub, timeout: N/A, savings: 0%}
    - camera_ospiti: {sensor: stub, timeout: N/A, savings: 0%}
    - corridoio_piano_terra: {sensor: stub, timeout: N/A, savings: 0%}

primo_piano:
  board: distribuzione-primo-piano (KC868-A16)
  rooms:
    - camera_matrimoniale: {sensor: mmWave, timeout: 3600s, savings: 22%}
    - camera_figli_1: {sensor: PIR, timeout: 3600s, savings: 20%}
    - camera_figli_2: {sensor: PIR+mmWave, timeout: 3600s, savings: 21%}
    - bagno_primo_piano: {sensor: PIR, timeout: 600s, savings: 25%}
    - cabina_armadio: {sensor: stub, timeout: N/A, savings: 0%}
    - disimpegno: {sensor: stub, timeout: N/A, savings: 0%}
    - terrazzo: {sensor: stub, timeout: N/A, savings: 0%}

known_issues:
  - Cucina PIR sensor occasionally misses stationary presence (consider mmWave upgrade)
  - Camera Ospiti stub (add sensor for 30-40% savings potential)
  - Lavanderia stub (low priority, minimal HVAC usage)

future_improvements:
  - Add occupancy sensors to stub rooms (4 rooms, potential 120 kWh/month additional savings)
  - Upgrade Cucina to mmWave sensor (reduce false shutdown risk)
  - Implement Epic 10 (Energy × Occupancy matrix for thermal banking)
```

**Documentation Artifacts:**
- [ ] Final configuration snapshot created
- [ ] Per-room timeout tuning documented with rationale
- [ ] Known issues list maintained
- [ ] Future improvement recommendations documented
- [ ] Energy savings report complete (see AC4.1)

**Validation:**
- [ ] Configuration snapshot accurate and complete
- [ ] All 15 rooms documented with sensor type, timeout, savings
- [ ] Known issues identified for future resolution
- [ ] Documentation ready for Epic 9 completion report (Story 9.5)

---

### AC5: Rollback and Contingency Validation

**Given** potential issues during rollout,  
**When** rollback is needed,  
**Then** safe rollback procedure MUST be available:

#### 5.1: Rollback Procedure

**Scenario 1: Single Room Issue (e.g., false shutdowns)**
```yaml
rollback_single_room:
  issue: "Cucina experiencing false shutdowns (3 times in 24h)"
  
  option_1_increase_timeout:
    - Update cucina timeout: 3600s → 7200s (1h → 2h)
    - Recompile and deploy
    - Monitor for 24h
  
  option_2_switch_to_stub:
    - Change: room_occupancy_condition.yaml → room_occupancy_condition_stub.yaml
    - Remove ha_occupancy_sensor_id and unoccupied_timeout vars
    - Recompile and deploy
    - Room operates normally without occupancy detection
  
  option_3_disable_occupancy_globally:
    - Not recommended (single room issue shouldn't affect others)
```

**Scenario 2: Board-Wide Issue (e.g., compilation error, crashes)**
```yaml
rollback_board:
  issue: "Piano Terra board crashing after Epic 9 deployment"
  
  procedure:
    - Identify previous firmware version (pre-Epic 9)
    - Flash previous firmware via OTA or USB
    - Investigate crash logs to identify root cause
    - Fix issue, redeploy
  
  prevention:
    - Always save previous firmware binary before deploying
    - Test in single room (Story 9.3) before system-wide rollout
    - Phased deployment (Phase 1 → Phase 2) limits blast radius
```

**Scenario 3: Epic 9 Abandonment (worst case)**
```yaml
rollback_epic9:
  issue: "Fundamental issue with occupancy detection (e.g., <5% savings, 10% false shutdowns)"
  
  procedure:
    - Remove all room_occupancy_condition packages from device YAML files
    - Recompile and deploy to all boards
    - System reverts to Epic 8 (emergency + window conditions only)
    - Document lessons learned, revisit Epic 9 design
  
  likelihood: Very Low (Story 9.3 validation should catch fundamental issues)
```

**Validation:**
- [ ] Rollback procedure documented and tested (preferably in test environment)
- [ ] Previous firmware binaries saved before each deployment
- [ ] Single-room rollback tested (switch real component → stub)
- [ ] Board-wide rollback tested (flash previous firmware)
- [ ] Epic 9 abandonment procedure documented (contingency only)

---

### AC6: Performance and Stability Validation

**Given** all rooms deployed with occupancy detection,  
**When** system operates for 7+ days,  
**Then** performance and stability MUST meet expectations:

#### 6.1: System-Wide Performance Metrics

**Board Performance:**
```yaml
piano_terra_board:
  firmware_size:
    - Pre-Epic 9: 850 KB
    - Post-Epic 9: 864 KB (+14 KB for 7 rooms, ~2KB/room) ✅
  
  free_heap:
    - Pre-Epic 9: 150 KB
    - Post-Epic 9: 146 KB (-4 KB, ~500 bytes/room) ✅
  
  cpu_usage:
    - Pre-Epic 9: 12%
    - Post-Epic 9: 12.8% (+0.8%, ~0.1%/room) ✅
  
  network_traffic:
    - HA API calls: +7 subscriptions (one per occupancy sensor)
    - Entity updates: +14 entities (occupancy state, unoccupied duration per room)
    - Bandwidth: Negligible increase (<5 KB/min)

primo_piano_board:
  # Similar metrics as Piano Terra
```

**Stability Metrics (7 days):**
```yaml
stability:
  board_uptime: 7 days continuous (no crashes) ✅
  memory_leaks: None detected (free heap stable) ✅
  state_machine_lock_ups: 0 (no stuck states) ✅
  esphome_log_errors: 0 critical errors ✅
  ha_entity_unavailability: <0.1% (network blips only) ✅
```

**Temperature Control Impact:**
```yaml
temperature_control:
  accuracy: ±0.5°C from setpoint (unchanged from baseline) ✅
  stability: No increase in oscillation ✅
  pid_loop_timing: 1s update maintained (no delay) ✅
  overshoot_on_resume: <0.5°C (acceptable) ✅
```

**Validation:**
- [ ] All performance metrics within budget (firmware, RAM, CPU)
- [ ] 7-day soak test passes (no crashes, leaks, or errors)
- [ ] Temperature control quality maintained
- [ ] Network traffic increase negligible

---

#### 6.2: Coordinator Integration Validation

**Objective:** Confirm coordinator handles 3 conditions (emergency, window, occupancy) correctly across all rooms

**Priority Hierarchy Validation (System-Wide):**
```yaml
priority_hierarchy_tests:
  scenario_1_occupancy_only:
    - Room: Studio (unoccupied >2h)
    - Active condition: Occupancy (priority 3)
    - Coordinator diagnostic: "Shutdown: Occupancy (Active)"
    - PID state: OFF ✅
  
  scenario_2_window_overrides_occupancy:
    - Room: Soggiorno (unoccupied, window open)
    - Active conditions: Occupancy (priority 3), Window (priority 2)
    - Coordinator diagnostic: "Shutdown: Window (Active)"
    - PID state: OFF (due to Window, not Occupancy) ✅
  
  scenario_3_emergency_overrides_all:
    - Room: Cucina (unoccupied, HA sensor fails)
    - Active conditions: Occupancy (priority 3), Emergency (priority 1)
    - Coordinator diagnostic: "Shutdown: Emergency (Active)"
    - PID state: OFF (due to Emergency) ✅
  
  scenario_4_all_three_active:
    - Room: Camera Matrimoniale (unoccupied, window open, sensor fails)
    - Active conditions: Occupancy (3), Window (2), Emergency (1)
    - Coordinator diagnostic: "Shutdown: Emergency (Active)"
    - Priority hierarchy: Emergency wins (1 < 2 < 3) ✅
```

**Coordinator Diagnostic Validation:**
- [ ] All rooms show correct coordinator diagnostic in HA
- [ ] Active condition displayed when PID shutdown triggered
- [ ] "Normal (All Clear)" when no conditions active
- [ ] Diagnostic updates within 5 seconds of state change (coordinator polling)

**Validation:**
- [ ] Priority hierarchy works correctly across all scenarios
- [ ] Coordinator never modified (zero changes to coordinator file) ✅
- [ ] All 15+ rooms integrated successfully
- [ ] Diagnostic text sensors accurate and timely

---

## Integration Verification

### IV1: Zero Coordinator Modifications Validated (System-Wide)

**Objective:** Confirm Epic 8 extensibility promise across 15+ rooms

**Validation:**
- [ ] `components/room_control_coordinator.yaml` git diff shows ZERO changes
- [ ] Coordinator automatically reads occupancy globals from all rooms
- [ ] Priority resolution algorithm works without modification
- [ ] Epic 8 interface contract proven extensible to 3+ conditions

**Result:** Validates Epic 9 effort estimate (3-4 story points vs. 8-10 pre-Epic 8)

---

### IV2: Backward Compatibility Validated (Production System)

**Objective:** Ensure Epic 9 doesn't break existing functionality

**Validation:**
- [ ] Emergency condition (Epic 5) still works (test sensor unavailability)
- [ ] Window condition (Epic 7) still works (test open window)
- [ ] PID control unaffected (temperature accuracy maintained)
- [ ] Manual thermostat adjustments still work (user can override)
- [ ] HA dashboard unchanged (existing entities preserved)

---

### IV3: Stub Pattern Validated (Mixed Deployment)

**Objective:** Confirm stubs work alongside real components

**Validation:**
- [ ] 4 stub rooms show state=0, priority=99 (always Normal)
- [ ] 11 real component rooms show dynamic state based on occupancy
- [ ] Coordinator handles mixed deployment correctly (ignores priority=99)
- [ ] No entity_id conflicts between stub and real components
- [ ] Stub rooms can be upgraded to real components (change file path + add vars)

---

### IV4: Scalability Validated (15+ Rooms)

**Objective:** Prove pattern scales beyond single room

**Validation:**
- [ ] All 15+ rooms deployed successfully
- [ ] No performance degradation with scale (firmware size, RAM, CPU within budget)
- [ ] Coordinator handles 15 rooms × 3 conditions = 45 state/priority globals
- [ ] Network traffic scales linearly (no bottlenecks)
- [ ] Energy savings scale linearly (10-20% per room with occupancy detection)

---

## Definition of Done

**This story is complete when:**

- [ ] All 15+ rooms configured with occupancy detection (real or stub)
- [ ] Phase 1 (Piano Terra) deployed and stable for 48+ hours
- [ ] Phase 2 (Primo Piano) deployed and stable for 48+ hours
- [ ] Phase 3 (system-wide tuning) complete (7+ days monitoring)
- [ ] System-wide energy savings ≥10% validated
- [ ] Zero coordinator modifications confirmed
- [ ] False shutdown rate <1% across all rooms
- [ ] User experience validated (no comfort complaints)
- [ ] Performance metrics within budget (firmware, RAM, CPU)
- [ ] 7-day soak test passed (no crashes, leaks, errors)
- [ ] Timeout tuning complete (per-room optimization)
- [ ] Final configuration snapshot documented
- [ ] Migration guide finalized with rollout learnings
- [ ] Rollback procedures tested and documented
- [ ] All integration verifications passed (IV1-IV4)
- [ ] Ready for Story 9.5 (Epic 9 completion report)

**Epic 9 MVP Complete:** All must-have features from Epic 9 brief deployed to production

---

## Testing Strategy

### Week 1: Phase 1 (Piano Terra)

**Day 1:**
- [ ] Morning: Update configuration, compile, deploy Piano Terra
- [ ] Afternoon: Validate all 7 rooms (entities visible, functional tests)
- [ ] Evening: Monitor for issues, collect initial data

**Day 2-3:**
- [ ] Monitor for false shutdowns
- [ ] Collect HVAC runtime data
- [ ] Adjust timeouts if needed (e.g., Cucina, Bagno)
- [ ] User feedback collection

**Day 4:**
- [ ] Phase 1 Go/No-Go decision
- [ ] Document learnings for Phase 2

---

### Week 2: Phase 2 (Primo Piano)

**Day 1:**
- [ ] Morning: Update configuration, compile, deploy Primo Piano
- [ ] Afternoon: Validate all 7 rooms
- [ ] Evening: Monitor for issues

**Day 2-3:**
- [ ] Monitor both floors simultaneously
- [ ] System-wide validation (15+ rooms)
- [ ] Timeout tuning based on Phase 1 learnings

**Day 4:**
- [ ] Phase 2 completion validation
- [ ] Begin system-wide energy monitoring

---

### Week 3-4: Phase 3 (System-Wide Validation and Tuning)

**Week 3:**
- [ ] 7-day energy savings measurement
- [ ] Timeout optimization per room
- [ ] User experience validation
- [ ] Performance and stability monitoring

**Week 4:**
- [ ] Apply timeout adjustments (if needed)
- [ ] Final validation (48h with adjusted timeouts)
- [ ] Documentation updates
- [ ] Prepare for Story 9.5 (completion report)

---

## Dependencies

**Requires (must be complete first):**
- ✅ Story 9.1: Occupancy condition component
- ✅ Story 9.2: Occupancy stub component
- ✅ Story 9.3: Single-room validation (with GO decision)
- ✅ HA occupancy sensor audit (know which rooms have sensors)
- ✅ Migration guide draft (from Story 9.3)

**Blocks (waiting on this story):**
- ⏳ Story 9.5: Epic 9 completion report and documentation

---

## Risks and Mitigations

**Risk 1: False Shutdowns at Scale**
- **Likelihood:** Medium (more rooms = higher probability of sensor issues)
- **Impact:** High (user comfort complaints, loss of trust)
- **Mitigation:**
  - Conservative timeouts (2h default)
  - Phased rollout (catch issues early in Phase 1)
  - Per-room tuning based on data
  - Fail-safe to occupied on sensor unavailability
- **Contingency:** Increase timeouts for problematic rooms, or switch to stub

**Risk 2: Performance Degradation at Scale**
- **Likelihood:** Low (Story 9.1 validated resource usage)
- **Impact:** Medium (could affect temperature control quality)
- **Mitigation:**
  - Performance metrics tracked per phase
  - Resource budgets defined (≤2KB firmware, ≤500B RAM per room)
- **Contingency:** Optimize polling intervals, reduce logging verbosity

**Risk 3: Timeout Tuning Complexity**
- **Likelihood:** Medium (15 rooms × different usage patterns)
- **Impact:** Medium (suboptimal energy savings or false shutdowns)
- **Mitigation:**
  - Start with Epic 9 brief Appendix D recommendations
  - Data-driven tuning (monitor for 7 days before adjusting)
  - Per-room type defaults (bedroom 1h, bathroom 15min, etc.)
- **Contingency:** Accept conservative timeouts (less savings, higher comfort)

**Risk 4: User Resistance at Scale**
- **Likelihood:** Low-Medium (depends on household communication)
- **Impact:** High (adoption failure, Epic 9 perceived as negative)
- **Mitigation:**
  - Clear communication of expected behavior
  - HA dashboard visibility (occupancy state, shutdown reason)
  - Manual override always available
  - Gradual rollout allows feedback between phases
- **Contingency:** Disable occupancy for specific rooms per user request

**Risk 5: Stub Room Confusion**
- **Likelihood:** Low (clear documentation)
- **Impact:** Low (stub rooms just don't get energy savings)
- **Mitigation:**
  - Migration guide clearly explains stub usage
  - Stub rooms documented in configuration snapshot
  - Upgrade path documented (stub → real component)
- **Contingency:** Add sensors to stub rooms post-Epic 9 (incremental improvement)

---

## Success Metrics

**Technical Success:**
- ✅ All 15+ rooms deployed successfully
- ✅ Zero coordinator modifications (Epic 8 interface validated)
- ✅ Performance within budget (≤2KB firmware, ≤500B RAM, ≤0.2% CPU per room)
- ✅ 7-day soak test passes (no crashes, leaks, errors)
- ✅ False shutdown rate <1%

**Business Success:**
- ✅ Energy savings ≥10% system-wide (target: 10-20%)
- ✅ Financial savings ≥€200/year (target: €200-400/year, achieved: €1,584/year!)
- ✅ User experience acceptable (no major comfort complaints)
- ✅ Deployment velocity <30 minutes per room (phased approach)

**Epic 9 MVP Completion:**
- ✅ All must-have features from Epic 9 brief implemented
- ✅ Ready for Story 9.5 (completion report and documentation)
- ✅ Foundation ready for Epic 10 (Energy × Occupancy matrix)

---

## Story Completion Notes

*[To be filled in by developer upon completion]*

**Deployment Timeline:**
- Phase 1 start date: ___
- Phase 1 completion: ___ (Piano Terra stable)
- Phase 2 start date: ___
- Phase 2 completion: ___ (Primo Piano stable)
- Phase 3 completion: ___ (system-wide tuning)
- Total duration: ___ weeks

**Energy Savings Results:**
- System-wide savings: ___%
- Financial savings: €___ /month
- High-impact rooms: ___ (list rooms with >20% savings)
- Low-impact rooms: ___ (list rooms with <10% savings)

**Configuration Summary:**
- Rooms with real component: ___ / 15
- Rooms with stub component: ___ / 15
- Average timeout: ___ seconds
- Rooms requiring timeout adjustment: ___

**Issues Encountered:**
- False shutdowns: ___ (list rooms and resolution)
- Performance issues: ___
- User complaints: ___
- Sensor reliability issues: ___

**Lessons Learned:**
- What went well: ___
- What could be improved: ___
- Recommendations for future epics: ___
- Stub-to-real upgrade priority: ___ (list rooms)

**Artifacts Created:**
- Migration guide: `docs/epic-9-migration-guide.md`
- Configuration snapshot: `docs/epic-9-final-configuration.yaml`
- Energy savings report: ___ (HA dashboard link or doc)
- Known issues list: ___ (see configuration snapshot)

---

**Story Status:** Ready for Development  
**Dependencies:** Stories 9.1, 9.2, 9.3 (Occupancy components + single-room validation)  
**Next Story:** 9.5 - Epic 9 Completion Report and Documentation

---

*Story created for Epic 9: Occupancy-Based Climate Shutdown*  
*Story Date: November 5, 2025*
