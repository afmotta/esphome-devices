# Epic 5: HA-Only Sensors with Emergency Shutdown - Cost Reduction & Safety

## Document Information

| Field             | Value                                              |
| ----------------- | -------------------------------------------------- |
| **Epic**          | Epic 5: HA-Only Sensors with Emergency Shutdown    |
| **Version**       | 1.0 (Epic Planned)                                 |
| **Date**          | October 29, 2025                                   |
| **Status**        | Planning Phase 📋                                   |
| **Story Manager** | Bob (Scrum Master)                                 |
| **Product Owner** | Sarah (Product Owner)                              |
| **Analyst**       | Mary (Business Analyst)                            |
| **Progress**      | 0/4 Stories Complete ⬜⬜⬜⬜                          |

---

## Epic Title

**HA-Only Sensors with Emergency Shutdown** - Cost Reduction & Safety Enhancement

---

## Epic Goal

Eliminate expensive Modbus temperature/humidity sensors by migrating to Home Assistant-only sensor architecture, while maintaining system safety through automatic emergency shutdown when HA is unavailable for more than 3 minutes.

---

## Epic Description

### Current System Analysis

**Cost & Complexity Issues:**

The current system uses **16+ dedicated Modbus RS485 temperature/humidity sensors** distributed across rooms on both floors. Each sensor:
- Costs ~$30-50 USD per unit (**$640+ total hardware cost**)
- Requires complex RS485 wiring with pull-up resistors and termination
- Needs per-room Modbus controller configuration in ESPHome
- Adds maintenance complexity (sensor failures, wiring issues, bus noise)

**Current Architecture (3-Tier Failover):**
```yaml
# components/room_sensors.yaml (v4 - 221 lines)
modbus_controller:
  - id: room_sensor_${zone_slug}_controller
    address: ${modbus_controller_address}

sensor:
  # TIER 1: Modbus sensor (primary, expensive)
  - platform: modbus_controller
    id: ${zone_slug}_room_temperature_modbus
    
  # TIER 2: Home Assistant sensor (fallback)
  - platform: homeassistant
    id: ${zone_slug}_room_temperature_ha
    
  # TIER 3: Emergency NaN (after 5-min timeout)
  - platform: template
    lambda: |-
      // Complex 3-tier failover logic (~80 lines)
      // Modbus → HA → Emergency
```

**Problems:**
1. **High Hardware Cost**: $640+ for Modbus sensors that duplicate HA sensors
2. **Complex Wiring**: RS485 bus requires careful wiring, prone to noise
3. **Redundant Sensors**: Most rooms already have Zigbee/WiFi sensors in HA
4. **Code Complexity**: 3-tier failover logic is overly complex (221 lines)
5. **Unnecessary Humidity**: Humidity not used by PID controllers
6. **Maintenance Burden**: More hardware = more failure points

### Business Case

**Why Remove Modbus Sensors?**

1. **Cost Savings**: $640+ hardware + wiring labor elimination
2. **Leverage Existing Infrastructure**: HA already has room sensors (Zigbee, WiFi, Ethernet)
3. **Simplification**: Reduce from 3-tier to 2-tier failover (54% code reduction)
4. **Maintenance**: Fewer hardware components to maintain and troubleshoot
5. **Scalability**: Adding rooms doesn't require new Modbus hardware

**Safety Requirement:**

While removing Modbus sensors reduces cost and complexity, **system safety cannot be compromised**. Hard requirement:

> **When Home Assistant is unavailable for more than 3 minutes, all room heating/cooling systems must automatically shut down (relays OFF, PIDs OFF) to prevent runaway control without valid sensor data.**

### Proposed Solution

**2-Tier HA-Only Architecture:**

```yaml
# components/room_sensors.yaml (v5 - ~100 lines, 54% reduction)

sensor:
  # PRIMARY: Home Assistant sensor (only source)
  - platform: homeassistant
    entity_id: ${ha_temperature_sensor_id}
    id: ${zone_slug}_room_temperature_ha
    on_value:
      - lambda: id(${zone_slug}_last_valid_time) = millis();
  
  # ABSTRACTED: With emergency logic
  - platform: template
    id: ${zone_slug}_room_temp_abstracted
    lambda: |-
      // Check HA sensor validity
      if (id(${zone_slug}_room_temperature_ha).has_state()) {
        float ha_temp = id(${zone_slug}_room_temperature_ha).state;
        if (!isnan(ha_temp)) {
          // NORMAL: Valid sensor, track for recovery
          if (id(${zone_slug}_emergency_triggered)) {
            // RECOVERING: Check stability timeout
            if ((millis() - recovery_start) / 1000 >= 60) {
              emergency_triggered = false;  // RESUME
            }
          }
          return ha_temp;
        }
      }
      
      // NO VALID DATA: Check emergency timeout
      if ((millis() - last_valid) / 1000 >= 180) {
        if (!emergency_triggered) {
          emergency_triggered = true;  // TRIGGER EMERGENCY
          // Room component executes: relay OFF, PID OFF
        }
      }
      return NAN;  // Signal emergency state

text_sensor:
  # State visibility
  - platform: template
    name: "${zone_name} Sensor State"
    lambda: |-
      if (emergency_triggered) {
        return recovery_start > 0 ? "Recovering" : "Emergency";
      }
      return "Normal";
```

**State Machine:**

```
Normal (HA sensor valid)
  ↓ (HA unavailable >3 min)
Emergency (Relay OFF, PID OFF, NaN temperature)
  ↓ (HA sensor valid again)
Recovering (Wait 60s for stability)
  ↓ (60s continuous stability)
Normal (Resume operation)
```

**Emergency Actions (Per Room):**

```yaml
# In room component package
interval:
  - interval: 5s
    then:
      - if:
          condition:
            lambda: return id(${zone_slug}_emergency_triggered);
          then:
            - switch.turn_off: ${relay_id}  # Physical relay OFF
            - climate.control:
                id: pid_radiant_${zone_slug}
                mode: "OFF"  # PID OFF
            - logger.log:
                level: ERROR
                format: "${zone_name}: EMERGENCY SHUTDOWN"
```

---

## Key Differences from Current System

| Aspect                | Current (v4)                          | Epic 5 (v5)                          |
| --------------------- | ------------------------------------- | ------------------------------------ |
| **Sensor Hardware**   | 16+ Modbus RS485 sensors              | 0 Modbus sensors (use HA only)       |
| **Hardware Cost**     | $640+ for Modbus sensors              | $0 (leverage existing HA sensors)    |
| **Wiring**            | Complex RS485 bus per room            | None (HA sensors wireless/existing)  |
| **Failover Tiers**    | 3-tier (Modbus → HA → Emergency)      | 2-tier (HA → Emergency)              |
| **Code Complexity**   | 221 lines                             | ~100 lines (54% reduction)           |
| **Emergency Timeout** | 5 minutes                             | 3 minutes (more responsive)          |
| **Recovery Logic**    | Immediate resume                      | 60s stability check (flap prevention)|
| **State Visibility**  | "Modbus/HA/Emergency"                 | "Normal/Emergency/Recovering"        |
| **Humidity Sensors**  | Included (unused by PIDs)             | Removed (not needed)                 |
| **Per-Room Entities** | 7 entities                            | 3 entities (57% reduction)           |
| **Required Vars**     | 5 (including modbus_controller_addr) | 3 (removed Modbus/humidity vars)     |

---

## Stories

### Story 5.1: Room Sensors Component Rewrite (HA-Only)
**Priority:** Critical (blocks all other stories)  
**Estimate:** 4-6 hours  
**Status:** Not Started ⬜

Rewrite `components/room_sensors.yaml` from 3-tier Modbus failover to 2-tier HA-only:
- Remove Modbus sensor platforms and per-room controllers
- Simplify lambda from 3-tier to 2-tier (HA → Emergency)
- Add configurable timeouts: `emergency_timeout` (180s), `recovery_stability_timeout` (60s), `check_interval` (10s)
- Implement state machine: Normal → Emergency → Recovering → Normal
- Repurpose `text_sensor` to show "Normal/Emergency/Recovering"
- Remove humidity sensor support (not needed for PID control)
- Reduce code from 221 lines to ~100 lines (54% reduction)

**Deliverable:** New `components/room_sensors.yaml` (v5) with comprehensive inline documentation

### Story 5.2: Emergency Shutdown Logic Implementation
**Priority:** High (core safety feature)  
**Estimate:** 3-4 hours  
**Status:** Not Started ⬜

Implement emergency shutdown actions when room sensor enters Emergency state:
- Add interval-based monitoring to room components (checks every 5s)
- When `${zone_slug}_emergency_triggered == true`:
  - Turn OFF relay (physical output)
  - Set PID mode to OFF (climate entity)
  - Log ERROR message with timestamp
- Emergency actions are idempotent (safe to trigger repeatedly)
- Recovery: When sensor exits Emergency, wait 60s stability, then auto-resume
- Test on all three devices with physical hardware verification

**Deliverable:** Emergency shutdown logic in all first floor and ground floor room components

### Story 5.3: Room Component Migration to HA-Only Sensors
**Priority:** High (final migration)  
**Estimate:** 5-7 days (including pilot + monitoring)  
**Status:** Not Started ⬜

Migrate all 16+ room components from Modbus sensors to HA-only sensors:

**Phase 1 (Day 1):** Pilot room (bagno_grande)
- Update component vars (remove modbus_controller_address, ha_humidity_sensor_id)
- Compile, flash, monitor 24h
- Test emergency trigger (disconnect HA >3 min)
- Test recovery (reconnect HA, wait 60s)

**Phase 2 (Day 2-3):** First floor batch (7 remaining rooms)
**Phase 3 (Day 4-5):** Ground floor batch (8-10 rooms)
**Phase 4 (Day 6):** Final testing and validation

**Deliverable:** All rooms using v5 sensors, documented migration in `docs/epic-5-migration-guide.md`

### Story 5.4: Epic 5 Documentation and Completion
**Priority:** High (blocks Epic closure)  
**Estimate:** 3-4 days  
**Status:** Not Started ⬜

Comprehensive documentation for HA-only sensor architecture:
- Create `docs/epic-5-migration-guide.md` (step-by-step procedures)
- Create `docs/epic-5-ha-only-sensors.md` (architecture deep dive)
- Create `docs/epic-5-completion-report.md` (metrics, results, lessons learned)
- Update `docs/architecture.md` (reflect Epic 5 changes)
- Update `.github/copilot-instructions.md` (Epic 5 patterns)
- Move old `room_sensors.yaml` to `components/deprecated/room_sensors_v4.yaml`
- Create production monitoring dashboard in Home Assistant
- Troubleshooting guide with 5 common issues

**Deliverable:** Complete documentation suite for Epic 5

---

## Success Metrics

### Cost & Complexity Reduction
- **Hardware Cost:** $640+ Modbus sensors → $0 (100% savings)
- **Wiring Labor:** 8-12 hours saved (no RS485 sensor wiring)
- **Code Complexity:** 221 lines → ~100 lines (54% reduction)
- **Failover Tiers:** 3 → 2 (simpler architecture)
- **Required Vars:** 5 → 3 (easier configuration)
- **Entities Per Room:** 7 → 3 (57% reduction)

### Safety & Reliability
- **Emergency Shutdown:** 100% of rooms (3-minute hard timeout)
- **Emergency Trigger Rate:** 100% when HA unavailable >3 min
- **False Emergency Rate:** 0% during normal operation (7-day validation)
- **Recovery Success Rate:** 100% when HA reconnects
- **Physical Verification:** 100% of relays turn OFF during emergency

### Migration Success
- **Zero Regressions:** All rooms maintain PID control functionality
- **Migration Time:** <1 week from pilot to full deployment
- **Rollback Events:** 0 (pilot phase validates before batch migration)

---

## Technical Architecture

### Component Structure

**Before Epic 5:**
```
components/
  room_sensors.yaml (v4 - 221 lines)
    ├─ modbus_controller (per room)
    ├─ modbus sensor: temperature
    ├─ modbus sensor: humidity
    ├─ homeassistant sensor: temperature
    ├─ homeassistant sensor: humidity
    ├─ template sensor: abstracted temp (3-tier failover)
    ├─ binary_sensor: room_sensor_online
    └─ sensor: last_update
```

**After Epic 5:**
```
components/
  room_sensors.yaml (v5 - ~100 lines)
    ├─ homeassistant sensor: temperature (PRIMARY)
    ├─ template sensor: abstracted temp (2-tier: HA → Emergency)
    ├─ text_sensor: sensor_state ("Normal/Emergency/Recovering")
    └─ sensor: last_update

  room component packages (updated)
    └─ interval: emergency shutdown logic (relay OFF, PID OFF)
```

### Configuration Variables

**Removed Variables:**
- ~~`modbus_controller_address`~~ (Modbus eliminated)
- ~~`ha_humidity_sensor_id`~~ (humidity not needed)

**Required Variables:**
- `zone_slug`: Room identifier (e.g., "bagno_grande")
- `zone_name`: Display name (e.g., "Bagno Grande")
- `ha_temperature_sensor_id`: HA entity ID (e.g., "sensor.room_bagno_grande_temperature")

**Optional Variables (with defaults):**
- `emergency_timeout`: 180 (3 minutes)
- `recovery_stability_timeout`: 60 (1 minute)
- `check_interval`: 10 (10 seconds)

### Exposed Entities (Per Room)

**Removed Entities:**
- `sensor.{zone}_room_temperature_modbus` ❌
- `sensor.{zone}_room_humidity_modbus` ❌
- `sensor.{zone}_room_humidity` ❌
- `binary_sensor.{zone}_room_sensor_online` ❌

**Changed Entities:**
- `text_sensor.{zone}_temp_source` → `text_sensor.{zone}_sensor_state`
  - Old: "Modbus" / "Home Assistant" / "Emergency"
  - New: "Normal" / "Emergency" / "Recovering"

**Unchanged Entities:**
- `sensor.{zone}_room_temp_abstracted` ✅ (internal, used by PID)
- `sensor.{zone}_room_sensor_last_update` ✅ (diagnostic)
- `climate.pid_radiant_{zone}` ✅ (PID entity)

---

## Dependencies & Prerequisites

### Epic Dependencies
- **Epic 4 Completion:** Room-based component architecture provides structure for per-room emergency logic
- **No blockers:** Epic 5 is independent (can start immediately)

### Hardware Prerequisites
- Home Assistant sensors already deployed in each room (Zigbee, WiFi, or Ethernet)
- HA sensor entity IDs documented for each room
- Physical access to ESPHome devices for flashing

### Software Prerequisites
- ESPHome 2023.x+ (homeassistant platform support)
- Home Assistant with room temperature sensors configured
- Stable network connection between ESPHome devices and HA

### Testing Prerequisites
- Ability to disconnect HA for testing (staging environment or off-hours)
- Physical access to devices for relay verification
- 7-day monitoring window for production validation

---

## Risks & Mitigation

### Risk 1: HA Unavailability Causes Legitimate Emergencies
**Severity:** High  
**Probability:** Medium  
**Impact:** All rooms shut down during HA outage

**Mitigation:**
- 3-minute timeout balances safety vs. responsiveness (HA restarts typically <60s)
- Recovery logic with 60s stability prevents flapping
- HA high availability setup recommended (but not required for Epic 5)
- Monitoring dashboard alerts on emergency states

### Risk 2: False Emergencies During Migration
**Severity:** Medium  
**Probability:** Low  
**Impact:** Rooms shut down unnecessarily during testing

**Mitigation:**
- Pilot room approach (test one room 24h before batch)
- Phased rollout (first floor, then ground floor)
- Rollback plan ready (keep v4 as `room_sensors_v4_backup.yaml`)
- Testing during low-criticality periods (mild weather)

### Risk 3: HA Sensor Entity ID Mismatches
**Severity:** Medium  
**Probability:** Medium  
**Impact:** Sensors appear unavailable, trigger emergency

**Mitigation:**
- Document all HA sensor entity IDs before migration
- Validate entity IDs exist in HA before compiling
- ESPHome logs show clear error messages for missing entities
- Pilot room tests this first

### Risk 4: Recovery Logic Doesn't Resume PIDs
**Severity:** High  
**Probability:** Low  
**Impact:** Manual intervention required to resume heating/cooling

**Mitigation:**
- Comprehensive recovery testing in Story 5.2
- Multiple recovery cycles tested (emergency → recovery → normal)
- Physical hardware verification (relay clicks, PID resumes)
- Monitoring during pilot phase

### Risk 5: Code Complexity in Lambda
**Severity:** Low  
**Probability:** Low  
**Impact:** Bugs in emergency detection or recovery logic

**Mitigation:**
- Comprehensive inline comments in lambda code
- State machine clearly documented
- Extensive logging (DEBUG/INFO/WARN/ERROR levels)
- Code review before pilot deployment

---

## Timeline & Milestones

### Week 1: Component Development
**Days 1-2:** Story 5.1 (Component rewrite, 4-6 hours)
- Backup v4 to deprecated folder
- Create new room_sensors.yaml (v5)
- Validate and test with minimal device config

**Days 2-3:** Story 5.2 (Emergency logic, 3-4 hours)
- Add emergency shutdown to room component template
- Test emergency trigger on development device
- Test recovery on development device

### Week 2: Migration & Testing
**Day 4:** Story 5.3 Phase 1 (Pilot room)
- Update bagno_grande component
- Flash distribuzione-primo-piano
- Monitor 24 hours
- Test emergency trigger
- Test recovery

**Days 5-6:** Story 5.3 Phase 2 (First floor batch)
- Update remaining 7 first floor rooms
- Flash and deploy
- Monitor 24 hours

**Days 7-8:** Story 5.3 Phase 3 (Ground floor batch)
- Update 8-10 ground floor rooms
- Flash and deploy
- Monitor 24 hours

**Day 9:** Story 5.3 Phase 4 (Final validation)
- System-wide testing
- Emergency scenarios
- Production sign-off

### Week 3: Documentation & Closure
**Days 10-13:** Story 5.4 (Documentation, 3-4 days)
- Write migration guide
- Write architecture documentation
- Create completion report
- Update main architecture doc
- Update Copilot instructions
- Create HA monitoring dashboard
- Epic 5 sign-off

**Total Timeline:** 13-15 days from start to completion

---

## Brainstorming Session Results

**Session Date:** October 29, 2025  
**Facilitator:** Business Analyst Mary  
**Technique:** SCAMPER Method (Systematic exploration)  
**Output:** `docs/brainstorming-session-results.md`

**Key Decisions from Brainstorming:**

1. **Emergency Shutdown Behavior:** Relays OFF + PID mode OFF (complete shutdown)
2. **Recovery Pattern:** Gradual resume with 60s stability check (prevents flapping)
3. **Timeout Configuration:** All timeouts configurable via vars (deployment flexibility)
4. **State Visibility:** Text sensor showing "Normal/Emergency/Recovering" (for HA automations)
5. **Per-Room Autonomy:** Distributed emergency logic (each room handles its own emergency)
6. **No System Aggregation:** Per-room status only (avoids complexity)

**Future Enhancements Identified (Out of Scope for Epic 5):**
- HA-side monitoring dashboard (Story 5.4 includes basic version)
- Multi-threshold warning system (2-min warning, 3-min emergency)
- Predictive emergency prevention (ML model for HA availability)
- Mesh sensor fallback network (ESP-NOW peer-to-peer)

---

## Related Documentation

### Created by Epic 5
- `docs/brainstorming-session-results.md` - SCAMPER session output (50+ ideas)
- `docs/epic-5-migration-guide.md` - Step-by-step migration procedures
- `docs/epic-5-ha-only-sensors.md` - Architecture deep dive
- `docs/epic-5-completion-report.md` - Metrics, results, lessons learned
- `components/deprecated/room_sensors_v4.yaml` - Old version (reference only)
- `components/deprecated/README.md` - Updated with Epic 5 deprecations

### Updated by Epic 5
- `docs/architecture.md` - Sensor architecture section updated
- `.github/copilot-instructions.md` - Epic 5 patterns added
- All room component files in `components/rooms/` (emergency logic added)

### Reference Documents
- `docs/epic-4-room-based-component-architecture.md` - Foundational pattern
- `docs/sensor-technology-selection.md` - Original sensor decision rationale

---

## Lessons Learned (To Be Updated Post-Completion)

### What Worked Well
- TBD (to be documented in Story 5.4)

### Challenges Encountered
- TBD (to be documented in Story 5.4)

### Improvements for Future Epics
- TBD (to be documented in Story 5.4)

---

## Sign-Off

### Story Completion
- [ ] Story 5.1: Room Sensors Component Rewrite (HA-Only)
- [ ] Story 5.2: Emergency Shutdown Logic Implementation
- [ ] Story 5.3: Room Component Migration to HA-Only Sensors
- [ ] Story 5.4: Epic 5 Documentation and Completion

### Validation Checklist
- [ ] All 16+ rooms migrated to HA-only sensors
- [ ] Emergency shutdown tested on all rooms (relay OFF verified)
- [ ] Recovery tested on all rooms (auto-resume verified)
- [ ] 7-day production monitoring complete (zero false emergencies)
- [ ] Cost savings documented ($640+ hardware elimination)
- [ ] Code complexity reduced (54% reduction validated)
- [ ] All documentation complete and reviewed

### Production Sign-Off
- [ ] **Story Manager (Bob):** All stories complete, tested, and documented
- [ ] **Product Owner (Sarah):** Business goals achieved, metrics validated
- [ ] **Technical Lead:** Architecture sound, code quality verified
- [ ] **Operations:** Production stable, monitoring in place

---

**Epic Status:** Planning Phase ��  
**Next Action:** Begin Story 5.1 (Room Sensors Component Rewrite)  
**Target Completion:** November 15, 2025 (2-3 weeks from kickoff)

---

*Document Version History:*
- **v1.0 (Oct 29, 2025):** Epic planning phase complete, ready for implementation kickoff
