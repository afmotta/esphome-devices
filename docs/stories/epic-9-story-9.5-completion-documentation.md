# Story 9.5: Completion Documentation

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

**As a** product owner and system maintainer,  
**I want** to create comprehensive completion documentation for Epic 9,  
**so that** the implementation is properly documented, lessons learned are captured, and future maintainers understand the occupancy detection system.

---

## Business Context

This story represents the formal completion and knowledge capture phase of Epic 9. By creating comprehensive documentation, we:

1. **Validate Epic Success:** Confirm all MVP criteria met, energy savings achieved, goals delivered
2. **Capture Learnings:** Document what worked well, what didn't, and recommendations for future epics
3. **Enable Maintenance:** Provide complete reference for future troubleshooting and enhancements
4. **Close the Loop:** Formally complete Epic 9 and transition to Epic 10 planning

**Value Delivered:**
- Epic 9 formally validated and closed
- Knowledge base for future room additions
- Lessons learned feed into Epic 10+ planning
- Completion report demonstrates Epic 8 extensibility value

**Documentation Artifacts:**
- Epic 9 Completion Report (comprehensive summary)
- Migration Guide (how to add occupancy to new rooms)
- Energy Monitoring Dashboard (HA configuration)
- Known Issues and Workarounds (ongoing reference)

**Dependencies:**
- Story 9.4 completed (all 15+ rooms deployed and stable)
- 7+ days of system-wide energy data collected
- User feedback gathered
- Performance metrics validated

---

## Acceptance Criteria

### AC1: Epic 9 Completion Report Created

**Given** Epic 9 MVP complete (all Stories 9.1-9.4 done),  
**When** completion report is created,  
**Then** comprehensive documentation MUST be provided:

#### Report Structure

**File:** `docs/epic-9-completion-report.md`

**Required Sections:**

1. **Executive Summary**
   - Epic goal and scope
   - Implementation timeline (start → completion)
   - Key achievements (energy savings, zero coordinator mods, 15+ rooms deployed)
   - Success metrics summary

2. **MVP Validation**
   - All MVP criteria from Epic 9 brief validated
   - Energy savings: Target 10-20%, Achieved X%
   - Deployment success: All 15+ rooms with occupancy detection
   - Zero coordinator modifications confirmed
   - Priority hierarchy validated

3. **Story Completion Summary**
   ```yaml
   stories:
     story_9_1_occupancy_component:
       status: Complete
       story_points: 2
       duration: X days
       key_deliverables:
         - components/room_occupancy_condition.yaml (258 lines)
         - Interface compliant (state+priority globals)
         - Resource usage: 2KB firmware, 500B RAM, 0.1% CPU
       
     story_9_2_occupancy_stub:
       status: Complete
       story_points: 1
       duration: X days
       key_deliverables:
         - components/room_occupancy_condition_stub.yaml (44 lines)
         - Always-present pattern (state=0, priority=99)
         - Resource usage: <200B firmware, <100B RAM, 0% CPU
       
     story_9_3_single_room_validation:
       status: Complete
       story_points: 2
       duration: X days
       test_room: Soggiorno
       validation_results:
         - Energy savings: 18% (within 10-20% target)
         - False shutdowns: 0 (target: <1%)
         - Recovery time: 12 seconds (target: <15s)
       
     story_9_4_multi_room_rollout:
       status: Complete
       story_points: 3
       duration: X days
       deployment:
         - Phase 1 (Piano Terra): 7 rooms, 3 days
         - Phase 2 (Primo Piano): 7 rooms, 3 days
         - Phase 3 (Tuning): 7-14 days
       system_wide_results:
         - Energy savings: 15% average (target: 10-20%)
         - Financial savings: €1,584/year (target: €200-400/year)
         - False shutdown rate: 0.3% (target: <1%)
   
   total_story_points: 8
   estimated_story_points: 3-4 (Epic 9 brief)
   variance: +4 points (better estimation needed for multi-room rollout complexity)
   ```

4. **Energy Savings Analysis**
   ```yaml
   system_wide_metrics:
     baseline_hvac_runtime: X hours/week (pre-Epic 9)
     with_occupancy_runtime: Y hours/week (post-Epic 9)
     total_savings: Z% (target: 10-20%)
     
   per_room_breakdown:
     high_impact_rooms:
       - Camera Ospiti: 40% savings (rarely used)
       - Bagno Piano Terra: 25% savings (short usage)
       - Bagno Primo Piano: 25% savings (short usage)
       - Terrazzo: 30% savings (seasonal use)
     
     medium_impact_rooms:
       - Camera Matrimoniale: 22% savings
       - Camera Figli 1: 20% savings
       - Camera Figli 2: 21% savings
       - Soggiorno: 18% savings
     
     low_impact_rooms:
       - Cucina: 15% savings (high occupancy)
       - Studio: 12% savings (occupied 8h/day)
     
     stub_rooms_no_savings:
       - Lavanderia: 0% (stub)
       - Camera Ospiti: 0% (stub)
       - Corridoio Piano Terra: 0% (stub)
       - Cabina Armadio: 0% (stub)
       - Disimpegno: 0% (stub)
       - Terrazzo: 0% (stub initially, upgraded later)
   
   financial_impact:
     monthly_savings: €132 (11 rooms × 48 kWh/month × €0.25/kWh)
     annual_savings: €1,584
     target_annual_savings: €200-400
     achievement: 396% of target minimum ✅
     roi: Infinite (software-only, $0 cost)
   ```

5. **Technical Implementation Summary**
   - Component architecture: Condition interface pattern
   - Zero coordinator modifications confirmed
   - Priority hierarchy: Emergency (1) > Window (2) > Occupancy (3)
   - Performance: Firmware +14KB, RAM +4KB, CPU +0.8% (system-wide)
   - Stability: 7+ days uptime, no crashes or memory leaks

6. **Deployment Statistics**
   ```yaml
   deployment_summary:
     total_rooms: 15
     rooms_with_real_component: 11
     rooms_with_stub_component: 4
     boards_updated: 2 (Piano Terra, Primo Piano)
     total_deployment_time: X days (target: 4-6 weeks)
     average_time_per_room: X minutes (target: 15 minutes)
     ota_deployments: X (all successful)
     rollbacks_required: 0 (no critical issues)
   ```

7. **User Experience Validation**
   - Comfort complaints: X (target: 0)
   - False shutdown reports: X (target: <1%)
   - Manual overrides used: X/week (target: <5/week)
   - User feedback summary: "Positive / Neutral / Negative"
   - Transparency: HA dashboard shows occupancy state clearly

8. **Lessons Learned**
   
   **What Went Well:**
   - Epic 8 interface contract worked perfectly (zero coordinator mods)
   - Phased rollout caught issues early (Phase 1 → Phase 2 → Phase 3)
   - Stub pattern enabled gradual sensor rollout
   - Energy savings exceeded expectations (15% vs. 10-20% target)
   - Immediate recovery (0s timeout) provided excellent UX
   
   **What Could Be Improved:**
   - Story point estimation: Underestimated multi-room rollout complexity (3-4 estimated, 8 actual)
   - Timeout tuning: More upfront data collection would have reduced trial-and-error
   - PIR sensor limitations: mmWave sensors significantly more reliable (upgrade recommendation)
   - Documentation: Migration guide needed more troubleshooting scenarios
   
   **Challenges Encountered:**
   - Cucina PIR sensor: Missed stationary presence (cooking), increased timeout to 2h
   - Bagno timeouts: Initial 15min too long, reduced to 10min for more savings
   - HA sensor entity_id changes: One sensor renamed during rollout, broke deployment
   - User education: Household members initially confused by "room cold when entering"
   
   **Recommendations for Future Epics:**
   - Story estimation: Add 50% buffer for multi-room rollout complexity
   - Sensor quality: Prioritize mmWave over PIR for new sensor installations
   - Data collection: Collect 2 weeks baseline per room before deploying
   - User communication: Proactive education reduces confusion and complaints

9. **Known Issues and Workarounds**
   ```yaml
   known_issues:
     issue_1_cucina_pir_false_negatives:
       severity: Low
       description: "Cucina PIR sensor occasionally misses stationary presence (user standing at stove)"
       impact: "Rare false shutdowns (1-2 per month)"
       workaround: "Increased timeout from 1h → 2h (reduces false shutdowns)"
       permanent_fix: "Upgrade to mmWave sensor (planned for Q1 2026)"
     
     issue_2_stub_room_no_savings:
       severity: Low
       description: "4 rooms with stubs have 0% energy savings (no occupancy detection)"
       impact: "Missed savings opportunity (~120 kWh/month potential)"
       workaround: "None (stubs by design)"
       permanent_fix: "Add occupancy sensors to stub rooms (priority: Camera Ospiti, Lavanderia)"
     
     issue_3_ha_sensor_rename_breaks_deployment:
       severity: Medium
       description: "If HA occupancy sensor entity_id changes, ESPHome deployment fails"
       impact: "Compilation error, requires manual fix in device YAML"
       workaround: "Lock HA entity_id naming, avoid renames during active deployment"
       permanent_fix: "None (ESPHome limitation, entity_id must be stable)"
   ```

10. **Future Enhancements**
    - **Epic 10 (Immediate):** Energy state × Occupancy matrix (thermal banking)
    - **Post-Epic 10:** Add sensors to 4 stub rooms (120 kWh/month additional savings)
    - **Epic 12+ (Long-term):** Predictive occupancy ML model (pre-condition before arrival)
    - **Continuous Improvement:** Per-room timeout tuning based on 3 months data

11. **References and Artifacts**
    - Epic 9 Brief: `docs/epic-9-brief.md`
    - Stories: `docs/stories/epic-9-story-9.1-*.md` through `9.5`
    - Components: `components/room_occupancy_condition.yaml`, `*_stub.yaml`
    - Configuration: `docs/epic-9-final-configuration.yaml` (from Story 9.4)
    - Migration Guide: `docs/epic-9-migration-guide.md` (AC2)
    - Energy Dashboard: `docs/epic-9-energy-dashboard.yaml` (AC3)

**Validation:**
- [ ] Completion report created with all 11 sections
- [ ] All MVP criteria from Epic 9 brief validated
- [ ] Energy savings documented and exceed target
- [ ] Lessons learned capture actionable insights
- [ ] Known issues documented with workarounds
- [ ] Future enhancements identified

---

### AC2: Migration Guide Finalized

**Given** Stories 9.3 and 9.4 learnings captured,  
**When** migration guide is finalized,  
**Then** comprehensive how-to documentation MUST be provided:

#### Migration Guide Structure

**File:** `docs/epic-9-migration-guide.md`

**Required Sections:**

1. **Overview**
   - Purpose: Add occupancy detection to new rooms or upgrade stubs
   - Prerequisites: Epic 8 coordinator deployed, HA occupancy sensor available
   - Estimated time: 15-30 minutes per room

2. **Prerequisites Checklist**
   ```yaml
   before_starting:
     - [ ] Room has Epic 8 coordinator deployed and stable
     - [ ] HA occupancy sensor entity_id known (or using stub)
     - [ ] Room device YAML file accessible (locals/ or devices/)
     - [ ] OTA access to board (IP address or mDNS name)
     - [ ] ESPHome CLI installed and working
     - [ ] Backup of current firmware binary (for rollback)
   ```

3. **Adding Occupancy to New Room (Step-by-Step)**
   
   **Scenario 1: Room with Occupancy Sensor (Real Component)**
   ```yaml
   # Example: Adding occupancy to Cucina
   
   step_1_identify_sensor:
     - Open Home Assistant
     - Navigate to Developer Tools → States
     - Search for occupancy sensor: "cucina_occupancy" or "cucina motion"
     - Note entity_id: "binary_sensor.cucina_occupancy"
     - Verify sensor state updates when you enter/leave room
   
   step_2_update_device_yaml:
     - Open room device YAML file
     - File: locals/distribuzione-piano-terra.yaml (or devices/)
     - Locate room's package section (search for "cucina")
     - Add new occupancy condition package:
   
   packages:
     # ... existing packages (sensors, emergency, window, coordinator)
     
     # NEW: Occupancy condition
     room_occupancy_condition_cucina:
       file: ../../components/room_occupancy_condition.yaml
       vars:
         zone_slug: "cucina"            # Must match room's zone_slug
         zone_name: "Cucina"            # Human-readable name
         ha_occupancy_sensor_id: "binary_sensor.cucina_occupancy"  # From Step 1
         unoccupied_timeout: "3600"     # 1 hour in seconds (adjust per room type)
   
   step_3_validate_timeout:
     - Choose timeout based on room type (see Appendix A)
     - Bedroom: 3600s (1h)
     - Bathroom: 600s (10min)
     - Living Room: 7200s (2h)
     - Guest Room: 14400s (4h)
     - Office: 7200s (2h)
     - Default: 7200s (2h)
   
   step_4_compile_firmware:
     - cd /Users/alberto/src/esphome-devices
     - esphome compile locals/distribuzione-piano-terra.yaml
     - Verify compilation succeeds (no errors)
     - Check firmware size increase: ~2KB per room (acceptable)
   
   step_5_deploy_via_ota:
     - esphome upload locals/distribuzione-piano-terra.yaml --device 192.168.x.x
     - Monitor deployment progress (2-3 minutes)
     - Wait for board reboot
     - Verify board reconnects to HA
   
   step_6_validation:
     - Open Home Assistant
     - Navigate to room climate entity (climate.pid_cucina)
     - Check new entities visible:
       - text_sensor.cucina_occupancy_state: "Occupied" or "Unoccupied (Active)"
       - sensor.cucina_unoccupied_duration: "0" (occupied) or incrementing
     - Test occupancy detection:
       - Leave room for >timeout duration
       - Verify state changes to "Unoccupied (Active)"
       - Verify coordinator shows "Shutdown: Occupancy (Active)"
       - Verify PID forced to OFF
       - Re-enter room
       - Verify recovery within 15 seconds
       - Verify coordinator shows "Normal (All Clear)"
   ```

   **Scenario 2: Room without Occupancy Sensor (Stub Component)**
   ```yaml
   # Example: Adding stub to Lavanderia (no sensor)
   
   step_1_decide_on_stub:
     - Room has no occupancy sensor installed
     - No immediate plans to add sensor
     - Want to maintain coordinator compatibility
   
   step_2_update_device_yaml:
     - Use stub component instead of real component
   
   packages:
     # ... existing packages
     
     # Stub component (no occupancy detection, always Normal)
     room_occupancy_condition_lavanderia:
       file: ../../components/room_occupancy_condition_stub.yaml
       vars:
         zone_slug: "lavanderia"
         zone_name: "Lavanderia"
       # No ha_occupancy_sensor_id or unoccupied_timeout needed
   
   step_3_compile_and_deploy:
     - Same as Scenario 1 (compile, upload via OTA)
   
   step_4_validation:
     - Verify entities visible in HA
     - State always shows "Normal" (stub never triggers)
     - Priority always 99 (coordinator ignores)
     - No PID shutdown from occupancy (by design)
   
   step_5_upgrade_path:
     - When occupancy sensor added in future:
       - Change file path: room_occupancy_condition_stub.yaml → room_occupancy_condition.yaml
       - Add vars: ha_occupancy_sensor_id, unoccupied_timeout
       - Recompile and deploy
       - Validate occupancy detection works
   ```

4. **Timeout Tuning Guide**
   ```yaml
   initial_deployment:
     - Use recommended timeout from Appendix A (by room type)
     - Deploy and monitor for 7 days
     - Collect data: False shutdowns, energy savings, user feedback
   
   tuning_criteria:
     too_many_false_shutdowns:
       symptoms: Room shuts down while occupied (>1/week)
       action: Increase timeout by 50-100% (1h → 2h)
       example: "Cucina PIR sensor misses stationary presence, increased 1h → 2h"
     
     insufficient_savings:
       symptoms: Room rarely unoccupied for full timeout duration
       action: Reduce timeout by 25-50% (2h → 1h)
       example: "Bagno only occupied 5-10 min, reduced 15min → 10min for more savings"
     
     user_complaints:
       symptoms: "Room too cold when I enter" feedback
       action: Add 30-60 minutes to timeout (reduces shutdown frequency)
       example: "Camera Matrimoniale 1h → 1.5h to reduce cold-room perception"
   
   iterative_process:
     - Week 1-2: Deploy with default timeout, collect data
     - Week 3: Analyze data, identify tuning opportunities
     - Week 4: Apply adjustments, monitor for 7 days
     - Week 5+: Fine-tune based on continued data collection
   ```

5. **Troubleshooting Guide**
   ```yaml
   problem_1_compilation_error:
     error: "ERROR Error while reading config: ..."
     causes:
       - Typo in ha_occupancy_sensor_id
       - Missing required vars (zone_slug, zone_name)
       - File path incorrect (../../components/room_occupancy_condition.yaml)
     solution:
       - Check YAML indentation (use spaces, not tabs)
       - Verify all required vars present
       - Verify file path relative to device YAML location
   
   problem_2_entities_not_visible_in_ha:
     error: "New occupancy entities don't appear in HA"
     causes:
       - OTA deployment failed (check ESPHome logs)
       - Board didn't reboot after deployment
       - HA not recognizing new entities (needs restart)
     solution:
       - Check ESPHome logs for deployment errors
       - Manually reboot board (power cycle)
       - Restart Home Assistant (Configuration → Server Controls → Restart)
   
   problem_3_state_stuck_at_unknown:
     error: "Occupancy state shows 'Unknown' or 'Unavailable'"
     causes:
       - HA sensor entity_id incorrect or doesn't exist
       - HA sensor unavailable (battery dead, connectivity issue)
       - ESPHome can't communicate with HA
     solution:
       - Verify entity_id in HA (Developer Tools → States)
       - Check HA sensor status (battery, connectivity)
       - Check ESPHome API connection to HA (logs)
   
   problem_4_false_shutdowns:
     error: "Room shuts down while occupied"
     causes:
       - Occupancy sensor not detecting presence (PIR blind spot, mmWave sensitivity)
       - Timeout too short for room usage pattern
       - Sensor stuck "off" (hardware issue)
     solution:
       - Test sensor reliability: Enter room, verify HA shows "on"
       - Increase timeout by 50-100%
       - Consider upgrading PIR → mmWave sensor
   
   problem_5_never_shuts_down:
     error: "Room never reaches Unoccupied (Active) state"
     causes:
       - Timeout too long for room usage pattern
       - Occupancy sensor stuck "on" (hardware issue)
       - Room actually always occupied
     solution:
       - Verify sensor accuracy: Leave room, check HA shows "off"
       - Reduce timeout (if appropriate for room)
       - Check sensor for false positives (stuck relay, etc.)
   
   problem_6_coordinator_shows_wrong_condition:
     error: "Coordinator shows 'Emergency' instead of 'Occupancy'"
     causes:
       - Priority hierarchy working correctly (Emergency=1 < Occupancy=3)
       - Emergency condition actually active (sensor unavailable)
     solution:
       - Verify this is NOT a bug (priority hierarchy by design)
       - Check emergency condition status
       - If emergency active, resolve that first
   ```

6. **Rollback Procedure**
   ```yaml
   when_to_rollback:
     - Critical issue preventing room operation
     - Continuous false shutdowns causing user complaints
     - Firmware compilation or deployment failure
   
   rollback_steps:
     option_1_switch_to_stub:
       - Fastest rollback (5 minutes)
       - Change: room_occupancy_condition.yaml → room_occupancy_condition_stub.yaml
       - Remove ha_occupancy_sensor_id and unoccupied_timeout vars
       - Recompile and deploy
       - Room operates normally without occupancy detection
     
     option_2_flash_previous_firmware:
       - Use if stub not viable
       - Locate previous firmware binary (saved before deployment)
       - esphome upload --file previous_firmware.bin --device 192.168.x.x
       - Board reverts to pre-Epic 9 state
     
     option_3_remove_package_entirely:
       - Last resort (breaks coordinator if not careful)
       - Remove room_occupancy_condition package from device YAML
       - Coordinator still expects occupancy globals (will show errors)
       - Better to use stub (option 1) instead
   ```

7. **Best Practices**
   - Always backup firmware binary before deploying changes
   - Test in single room before system-wide rollout
   - Monitor for 7 days before considering stable
   - Document per-room timeout with rationale
   - Use stubs for rooms without sensors (maintain compatibility)
   - Communicate behavior to household members (education reduces complaints)

8. **Appendix A: Timeout Recommendations by Room Type**
   - [Copy from Epic 9 brief Appendix D]

9. **Appendix B: Example Room Configurations**
   - [Include 3-4 real-world examples from Story 9.4 deployment]

**Validation:**
- [ ] Migration guide complete with all 9 sections
- [ ] Step-by-step instructions validated against actual deployments
- [ ] Troubleshooting covers all issues from Stories 9.3-9.4
- [ ] Rollback procedures tested and documented
- [ ] Examples include real room configurations from production

---

### AC3: Energy Monitoring Dashboard Configuration

**Given** energy savings need to be visible and trackable,  
**When** HA energy dashboard is configured,  
**Then** comprehensive energy monitoring MUST be available:

#### Dashboard Configuration

**File:** `docs/epic-9-energy-dashboard.yaml`

**Required Components:**

1. **Overview Card**
   ```yaml
   # HA Dashboard Card Configuration
   type: vertical-stack
   title: "Epic 9: Occupancy-Based Energy Savings"
   cards:
     - type: markdown
       content: |
         **System-Wide Savings:** 15% average
         **Monthly Savings:** €132 (528 kWh)
         **Annual Savings:** €1,584
         
         **Rooms with Occupancy:** 11 / 15
         **Stub Rooms:** 4 / 15
   ```

2. **Per-Room Energy Savings Card**
   ```yaml
   - type: entities
     title: "Energy Savings by Room"
     entities:
       - entity: sensor.soggiorno_hvac_runtime_savings
         name: "Soggiorno"
         secondary_info: "18% savings"
       - entity: sensor.cucina_hvac_runtime_savings
         name: "Cucina"
         secondary_info: "15% savings"
       - entity: sensor.camera_matrimoniale_hvac_runtime_savings
         name: "Camera Matrimoniale"
         secondary_info: "22% savings"
       # ... continue for all rooms
   ```

3. **Occupancy State Overview Card**
   ```yaml
   - type: glance
     title: "Occupancy Status (Live)"
     columns: 3
     entities:
       - entity: text_sensor.soggiorno_occupancy_state
         name: "Soggiorno"
       - entity: text_sensor.cucina_occupancy_state
         name: "Cucina"
       - entity: text_sensor.camera_matrimoniale_occupancy_state
         name: "Camera"
       # ... continue for all rooms
   ```

4. **Coordinator Shutdown Reasons Card**
   ```yaml
   - type: entities
     title: "Coordinator Status"
     entities:
       - entity: text_sensor.soggiorno_coordinator_state
         name: "Soggiorno Coordinator"
       - entity: text_sensor.cucina_coordinator_state
         name: "Cucina Coordinator"
       # ... continue for all rooms
   ```

5. **HVAC Runtime Comparison Chart**
   ```yaml
   - type: history-graph
     title: "HVAC Runtime: Before vs After Epic 9"
     hours_to_show: 168  # 7 days
     entities:
       - entity: sensor.system_hvac_runtime_baseline
         name: "Baseline (Pre-Epic 9)"
       - entity: sensor.system_hvac_runtime_current
         name: "Current (With Occupancy)"
   ```

6. **Energy Consumption Chart**
   ```yaml
   - type: energy-date-selection
     title: "Energy Consumption Trend"
   
   - type: energy-sources-table
     title: "HVAC Energy by Room"
   ```

7. **HA Sensor Configuration (configuration.yaml additions)**
   ```yaml
   # Add to configuration.yaml for energy tracking
   
   template:
     - sensor:
         # System-wide HVAC runtime tracking
         - name: "System HVAC Runtime Current"
           unique_id: system_hvac_runtime_current
           unit_of_measurement: "h"
           state: >
             {% set rooms = [
               'climate.pid_soggiorno',
               'climate.pid_cucina',
               # ... all rooms
             ] %}
             {% set runtime = namespace(total=0) %}
             {% for room in rooms %}
               {% if states(room) in ['heating', 'cooling'] %}
                 {% set runtime.total = runtime.total + 1 %}
               {% endif %}
             {% endfor %}
             {{ runtime.total }}
         
         # Per-room savings calculation
         - name: "Soggiorno HVAC Runtime Savings"
           unique_id: soggiorno_hvac_savings
           unit_of_measurement: "%"
           state: >
             {% set baseline = state_attr('sensor.soggiorno_hvac_runtime_baseline', 'weekly_hours') | float %}
             {% set current = state_attr('sensor.soggiorno_hvac_runtime_current', 'weekly_hours') | float %}
             {% if baseline > 0 %}
               {{ ((baseline - current) / baseline * 100) | round(1) }}
             {% else %}
               0
             {% endif %}
   ```

**Validation:**
- [ ] Dashboard configuration file created
- [ ] All 7 cards configured and displaying data
- [ ] HA sensors configured for energy tracking
- [ ] System-wide savings visible at a glance
- [ ] Per-room savings breakdown available
- [ ] Occupancy state live status visible
- [ ] Coordinator shutdown reasons displayed

---

### AC4: Known Issues Documentation Maintained

**Given** ongoing system operation,  
**When** issues are discovered or workarounds implemented,  
**Then** known issues list MUST be kept current:

#### Known Issues File

**File:** `docs/epic-9-known-issues.md`

**Structure:**
```yaml
# Epic 9: Known Issues and Workarounds

last_updated: 2025-11-XX
status: Active (ongoing maintenance)

issues:
  - id: EPIC9-001
    title: "Cucina PIR Sensor False Negatives"
    severity: Low
    status: Open (workaround applied)
    description: "PIR sensor occasionally misses stationary presence (e.g., user standing at stove cooking)"
    impact: "Rare false shutdowns (1-2 per month)"
    affected_rooms: ["Cucina"]
    workaround: "Increased timeout from 1h → 2h (reduces false shutdown frequency)"
    permanent_fix: "Upgrade to mmWave sensor (planned Q1 2026)"
    date_reported: 2025-11-XX
  
  - id: EPIC9-002
    title: "Stub Rooms Have Zero Energy Savings"
    severity: Low
    status: Expected Behavior
    description: "4 rooms use stub component (no occupancy sensor), provide 0% energy savings"
    impact: "Missed savings opportunity (~120 kWh/month potential)"
    affected_rooms: ["Lavanderia", "Camera Ospiti", "Corridoio Piano Terra", "Cabina Armadio"]
    workaround: "None (stubs by design)"
    permanent_fix: "Add occupancy sensors to stub rooms (priority: Camera Ospiti, Lavanderia)"
    date_reported: 2025-11-XX
  
  - id: EPIC9-003
    title: "HA Entity ID Rename Breaks Deployment"
    severity: Medium
    status: Open (no fix available)
    description: "If HA occupancy sensor entity_id changes, ESPHome compilation fails"
    impact: "Deployment blocked until entity_id updated in device YAML"
    affected_rooms: ["All rooms with real occupancy component"]
    workaround: "Lock HA entity_id naming convention, avoid renames during active operation"
    permanent_fix: "None (ESPHome limitation, entity_id must be stable)"
    date_reported: 2025-11-XX

resolved_issues:
  - id: EPIC9-004
    title: "Bagno Timeout Too Long"
    severity: Low
    status: Resolved
    description: "Initial 15min timeout too long for bathroom usage (typically 5-10min)"
    impact: "Suboptimal energy savings (room runs longer than needed)"
    affected_rooms: ["Bagno Piano Terra", "Bagno Primo Piano"]
    resolution: "Reduced timeout to 10 minutes (600s)"
    date_resolved: 2025-11-XX
```

**Validation:**
- [ ] Known issues file created
- [ ] All issues from Stories 9.3-9.4 documented
- [ ] Severity levels assigned (Low, Medium, High, Critical)
- [ ] Workarounds provided for open issues
- [ ] Permanent fix plans documented
- [ ] Resolved issues tracked separately

---

### AC5: Epic 9 Metrics and KPIs Validated

**Given** Epic 9 brief defined success metrics,  
**When** final validation is performed,  
**Then** all KPIs MUST be measured and reported:

#### KPI Validation Report

**From Epic 9 Brief:**
```yaml
kpi_validation:
  interface_compliance:
    target: 100% compliance with Epic 8 interface contract
    actual: 100% ✅
    evidence: "Zero coordinator modifications, state+priority globals used"
  
  coordinator_stability:
    target: Zero modifications to room_control_coordinator.yaml
    actual: Zero modifications ✅
    evidence: "Git diff shows no changes to coordinator file"
  
  implementation_effort:
    target: ≤4 story points (vs. 8-10 pre-Epic 8, 60% reduction)
    actual: 8 story points (2+1+2+3)
    variance: +4 points (100% over estimate)
    analysis: "Underestimated multi-room rollout complexity (Story 9.4)"
    adjusted_target: "6-8 story points more realistic for future similar epics"
  
  energy_savings:
    target: 10-20% reduction in HVAC runtime
    actual: 15% average ✅
    range: 12-40% per room (varies by occupancy pattern)
    evidence: "HA energy dashboard, 7+ days measurement"
  
  false_shutdown_rate:
    target: <1%
    actual: 0.3% ✅
    calculation: "4 false shutdowns / 1,155 room-days (15 rooms × 77 days) = 0.35%"
    evidence: "User reports, ESPHome logs"
  
  resume_responsiveness:
    target: Climate resumes within 10 seconds
    actual: 12 seconds average ✅ (within tolerance)
    measurement: "Occupancy detection (10s) + coordinator polling (2-5s) = 12s avg"
    evidence: "Manual testing in Stories 9.3-9.4"
  
  migration_complexity:
    target: Average 15 minutes per room
    actual: 22 minutes average (range: 10-45 minutes)
    variance: +47% (acceptable, first-time deployment learning curve)
    evidence: "Story 9.4 deployment logs"
  
  documentation_completeness:
    target: Experienced ESPHome user can add occupancy using guide only
    actual: ✅ (validated with test user)
    evidence: "Migration guide reviewed by 3rd party, successfully followed"

business_objectives_validation:
  energy_savings_goal:
    target: "Reduce HVAC energy consumption by 10-20%"
    actual: 15% ✅
  
  implementation_velocity_goal:
    target: "Prove Epic 8 extensibility (3-4 points vs. 8-10 pre-Epic 8)"
    actual: 8 points (vs. estimated 15-20 pre-Epic 8) ✅
    analysis: "Still 50-60% reduction vs. pre-Epic 8, extensibility validated"
  
  comfort_preservation_goal:
    target: "±0.5°C from setpoint in occupied rooms"
    actual: ±0.4°C average ✅
    evidence: "Temperature monitoring, no degradation from baseline"
  
  user_experience_goal:
    target: "Zero manual thermostat adjustments for occupancy control"
    actual: <2 manual adjustments/week ✅
    evidence: "User feedback, HA automation logs"

user_success_metrics_validation:
  deployment_success:
    target: "All 15+ rooms with occupancy detection within 6 weeks"
    actual: All 15 rooms deployed in 4 weeks ✅
  
  energy_savings_validation:
    target: "Measurable HVAC runtime reduction"
    actual: 15% average, €1,584/year savings ✅
  
  comfort_complaints:
    target: Zero complaints
    actual: 2 minor complaints (resolved with timeout adjustment) ✅
  
  instant_resume_validation:
    target: "Climate resumes within 10 seconds"
    actual: 12 seconds average ✅
  
  rollout_flexibility:
    target: "Rooms without sensors continue normally with stub"
    actual: 4 stub rooms operating normally ✅
```

**Validation:**
- [ ] All KPIs from Epic 9 brief measured
- [ ] Targets met or variance explained
- [ ] Evidence provided for each metric
- [ ] Business objectives validated
- [ ] User success metrics validated

---

### AC6: Epic 9 Closure and Transition

**Given** all documentation complete and validated,  
**When** Epic 9 is formally closed,  
**Then** proper closure and transition MUST occur:

#### Closure Checklist

```yaml
epic_9_closure:
  documentation_complete:
    - [ ] Epic 9 Completion Report (AC1)
    - [ ] Migration Guide (AC2)
    - [ ] Energy Dashboard Configuration (AC3)
    - [ ] Known Issues Documentation (AC4)
    - [ ] KPI Validation Report (AC5)
  
  deliverables_complete:
    - [ ] components/room_occupancy_condition.yaml (Story 9.1)
    - [ ] components/room_occupancy_condition_stub.yaml (Story 9.2)
    - [ ] All 15 rooms deployed with occupancy detection (Story 9.4)
    - [ ] Zero coordinator modifications confirmed
  
  validation_complete:
    - [ ] 7+ days system-wide stability confirmed
    - [ ] Energy savings ≥10% validated
    - [ ] User experience acceptable
    - [ ] Performance within budget
  
  knowledge_transfer:
    - [ ] Migration guide enables future room additions
    - [ ] Troubleshooting guide covers common issues
    - [ ] Known issues documented with workarounds
    - [ ] Lessons learned captured for future epics
  
  transition_to_operations:
    - [ ] System in production, stable operation
    - [ ] Monitoring dashboard configured (HA)
    - [ ] Support documentation available
    - [ ] Handoff to maintenance team (if applicable)
  
  epic_10_preparation:
    - [ ] Epic 9 foundation ready (occupancy data available)
    - [ ] Energy × Occupancy matrix concept validated
    - [ ] Epic 10 brief can reference Epic 9 results
    - [ ] Coordinator extensibility proven (ready for 4th condition)
```

**Formal Epic 9 Closure:**
- Date: 2025-11-XX
- Status: Complete ✅
- MVP Criteria: All met
- Success Metrics: All validated
- Ready for Epic 10: Yes

**Validation:**
- [ ] All closure checklist items complete
- [ ] Epic 9 marked as "Complete" in project tracker
- [ ] Transition to Epic 10 planning initiated
- [ ] Epic 9 artifacts archived for future reference

---

## Integration Verification

### IV1: Documentation Cross-References Validated

**Objective:** Ensure all Epic 9 documentation is complete and interconnected

**Validation:**
- [ ] Completion report references all stories (9.1-9.5)
- [ ] Migration guide references completion report for metrics
- [ ] Energy dashboard references migration guide for setup
- [ ] Known issues referenced in troubleshooting section
- [ ] All documents link to Epic 9 brief as source

---

### IV2: Epic 8 Extensibility Validated

**Objective:** Confirm Epic 8 coordinator pattern enabled Epic 9 efficiency gains

**Validation:**
- [ ] Zero coordinator modifications confirmed (git diff)
- [ ] Implementation effort 50-60% less than pre-Epic 8 estimate
- [ ] Interface contract proven extensible to 3+ conditions
- [ ] Foundation ready for Epic 10 (4th condition)

---

### IV3: Production Readiness Validated

**Objective:** Confirm Epic 9 is production-stable and maintainable

**Validation:**
- [ ] 7+ days uptime with no crashes
- [ ] Energy savings sustained and measurable
- [ ] User experience acceptable (minimal complaints)
- [ ] Documentation enables self-service maintenance
- [ ] Support burden minimal (<1 hour/week)

---

## Definition of Done

**This story is complete when:**

- [ ] Epic 9 Completion Report created with all 11 sections (AC1)
- [ ] Migration Guide finalized with step-by-step instructions (AC2)
- [ ] Energy Monitoring Dashboard configured in HA (AC3)
- [ ] Known Issues documentation maintained (AC4)
- [ ] All KPIs from Epic 9 brief validated and reported (AC5)
- [ ] Epic 9 formally closed with transition checklist complete (AC6)
- [ ] All documentation cross-references validated (IV1)
- [ ] Epic 8 extensibility validated and documented (IV2)
- [ ] Production readiness confirmed (IV3)
- [ ] Epic 9 marked as "Complete" in project tracker
- [ ] Ready to transition to Epic 10 planning

**Epic 9 Fully Complete:** All must-have features deployed, documented, and validated in production

---

## Testing Strategy

### Week 1: Data Collection and Analysis

**Days 1-3: Gather Final Metrics**
- [ ] Collect 7+ days of energy data (system-wide)
- [ ] Calculate per-room savings percentages
- [ ] Gather user feedback (comfort, usability)
- [ ] Review ESPHome logs for errors

**Days 4-5: Analysis and Reporting**
- [ ] Analyze energy data, create charts
- [ ] Compare actual vs. target KPIs
- [ ] Document lessons learned
- [ ] Identify known issues

---

### Week 2: Documentation Creation

**Days 1-2: Completion Report**
- [ ] Write Epic 9 Completion Report (AC1)
- [ ] Include all 11 required sections
- [ ] Validate metrics and KPIs

**Days 3-4: Migration Guide and Dashboard**
- [ ] Finalize Migration Guide (AC2)
- [ ] Configure Energy Dashboard (AC3)
- [ ] Test migration guide with 3rd party

**Day 5: Closure and Review**
- [ ] Complete Known Issues documentation (AC4)
- [ ] Validate KPI report (AC5)
- [ ] Execute closure checklist (AC6)
- [ ] Submit for review

---

## Dependencies

**Requires (must be complete first):**
- ✅ Story 9.1: Occupancy condition component
- ✅ Story 9.2: Occupancy stub component
- ✅ Story 9.3: Single-room validation
- ✅ Story 9.4: Multi-room rollout (all 15+ rooms deployed and stable)
- ✅ 7+ days of system-wide energy data collected

**Blocks (waiting on this story):**
- ⏳ Epic 10 planning (requires Epic 9 completion)
- ⏳ Future room additions (require migration guide)

---

## Success Metrics

**Documentation Quality:**
- ✅ Completion report comprehensive (all 11 sections)
- ✅ Migration guide enables self-service deployment
- ✅ Energy dashboard provides actionable insights
- ✅ Known issues maintained and current

**Epic 9 Validation:**
- ✅ All MVP criteria from Epic 9 brief met
- ✅ Energy savings ≥10% validated (achieved: 15%)
- ✅ Financial savings ≥€200/year (achieved: €1,584/year)
- ✅ User experience acceptable (minimal complaints)
- ✅ Zero coordinator modifications confirmed

**Knowledge Transfer:**
- ✅ Future maintainers can add occupancy to new rooms
- ✅ Troubleshooting guide covers common issues
- ✅ Lessons learned captured for Epic 10+

**Epic Closure:**
- ✅ Epic 9 formally closed and archived
- ✅ Transition to Epic 10 planning initiated
- ✅ Foundation ready for energy optimization matrix

---

## Story Completion Notes

*[To be filled in by product owner upon completion]*

**Documentation Artifacts Created:**
- Epic 9 Completion Report: `docs/epic-9-completion-report.md`
- Migration Guide: `docs/epic-9-migration-guide.md`
- Energy Dashboard: `docs/epic-9-energy-dashboard.yaml`
- Known Issues: `docs/epic-9-known-issues.md`

**Final Epic 9 Metrics:**
- Total story points: 8 (estimated: 3-4, variance: +100%)
- Duration: ___ weeks (target: 4-6 weeks)
- Energy savings: ___% (target: 10-20%)
- Financial savings: €___ /year (target: €200-400/year)
- Deployment success: ___/15 rooms (target: 15/15)

**Epic 9 Status:**
- Date completed: 2025-11-XX
- MVP criteria: All met ✅
- Production status: Stable, operational
- Support burden: Low (<1 hour/week)

**Epic 10 Readiness:**
- Occupancy data: Available (7+ days)
- Coordinator extensibility: Proven (3 conditions working)
- Energy × Occupancy matrix: Ready to implement
- Foundation: Complete

---

**Story Status:** Ready for Development  
**Dependencies:** Stories 9.1-9.4 (All Epic 9 implementation complete)  
**Next Epic:** Epic 10 - Energy State × Occupancy Matrix

---

*Story created for Epic 9: Occupancy-Based Climate Shutdown*  
*Story Date: November 5, 2025*
