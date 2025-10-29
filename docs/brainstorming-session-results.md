# Epic 5: HA-Only Sensors with Emergency Shutdown - Brainstorming Session Results

**Session Date:** October 29, 2025  
**Facilitator:** Business Analyst Mary 📊  
**Participant:** Alberto

---

## Executive Summary

**Topic:** Epic 5 - Remove Modbus Sensors, Migrate to HA-Only Sensor Architecture with 3-Minute Emergency Shutdown

**Session Goals:** Focused ideation on specific technical challenges for transitioning from Modbus-based room sensors to Home Assistant-only sensors while maintaining system safety through emergency shutdown logic.

**Techniques Used:** SCAMPER Method (Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse/Rearrange) - 45 minutes

**Total Ideas Generated:** 50+ actionable decisions across all SCAMPER dimensions

### Key Themes Identified:

- **Architectural Simplification** - Move from 3-tier to 2-tier sensor architecture (HA → Emergency)
- **Safety-First Design** - Complete shutdown on HA unavailability (relays OFF, PIDs OFF)
- **Configurability** - Multiple timeout and interval parameters for deployment flexibility
- **Room-Based Autonomy** - Emergency logic integrated per-room, aligning with Epic 4 architecture
- **Cost & Complexity Reduction** - Eliminate expensive Modbus sensors and complex RS485 wiring
- **Gradual Recovery** - Stability checks before auto-resume to prevent flapping

---

## Technique Sessions

### SCAMPER Method - 45 minutes

**Description:** Systematic exploration using Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse/Rearrange framework to comprehensively analyze the sensor architecture migration.

#### Ideas Generated:

##### S - SUBSTITUTE

1. **Replace Modbus RS485 sensors with HA sensor entities** (Zigbee, WiFi, Ethernet physical sensors)
2. **Keep Modbus only for outputs** (0-10V adapter fancoil control)
3. **Emergency fallback: Full shutdown** instead of proxy values (all relays OFF, PIDs OFF)
4. **Simplify from 3-tier to 2-state system:** HA Available OR Emergency Shutdown
5. **Remove sensor wiring complexity** - leverage existing HA sensor infrastructure

##### C - COMBINE

6. **Integrate emergency logic directly into `room_sensors.yaml`** (not separate component)
7. **Per-room emergency status** (distributed, not centralized) - each room autonomous
8. **Combine HA sensor platform + timeout tracking + emergency shutdown** → single component
9. **No system-wide aggregation** - keeps complexity low, aligns with room-based architecture

##### A - ADAPT

10. **Adapt existing failover lambda** - simplify from 3-tier (Modbus→HA→Emergency) to 2-tier (HA→Emergency)
11. **Configurable emergency timeout** via vars (default: 180s = 3 minutes)
12. **Keep modbus_controller structure** but only for devices with Modbus outputs (fancoils)
13. **Adapt existing globals and template sensors** - keep structure, gut Modbus tier
14. **Preserve logging and diagnostic patterns** from current implementation

##### M - MODIFY

15. **Emergency behavior:** Turn off relays + Set PID mode to OFF (complete shutdown)
16. **Recovery pattern:** Gradual resume with stability check (wait for stable HA before auto-resume)
17. **Configurable stability timeout** for recovery (suggest 60-120s default)
18. **Configurable check_interval** for sensor monitoring (suggest 10s default)
19. **Three configurable parameters:** `emergency_timeout`, `recovery_stability_timeout`, `check_interval`

##### P - PUT TO OTHER USE

20. **Repurpose `last_valid_time` global** - track both emergency detection AND recovery stability
21. **Expose diagnostics to HA** - time in current state (normal/emergency/recovering)
22. **Repurpose `text_sensor.{zone}_temp_source`** → state indicator showing "Normal/Emergency/Recovering"
23. **Dual-purpose timeout tracking** - single variable for multiple states

##### E - ELIMINATE

24. **Remove all Modbus sensor platforms** (temperature_modbus, humidity_modbus)
25. **Eliminate `modbus_controller` per room** (move to device-level for outputs only)
26. **Remove `modbus_controller_address` var requirement**
27. **Eliminate `ha_humidity_sensor_id` var** (humidity not needed for PID control)
28. **Remove all humidity sensor references** completely
29. **Remove Modbus-specific filters and timeouts**
30. **Eliminate `binary_sensor.{zone}_room_sensor_online`** (state tracked in text_sensor)
31. **Keep `sensor.{zone}_room_sensor_last_update`** (useful diagnostic remains)

##### R - REVERSE / REARRANGE

32. **Keep standard ESPHome polling pattern** (homeassistant platform polls HA)
33. **Unavailability-based emergency logic** (simpler, proven pattern vs. heartbeat)
34. **Sensor-first check order** (maintain current logic flow vs. API-first)

#### Insights Discovered:

- **Architecture becomes dramatically simpler** - 2-state system vs. 3-tier failover reduces code complexity by ~60%
- **Room autonomy scales better** - distributed emergency checks avoid single points of failure
- **Configurability enables experimentation** - timeout parameters can be tuned per deployment without code changes
- **Safety through simplicity** - full shutdown is more predictable than fallback values
- **Epic 4 alignment is natural** - room-based emergency fits perfectly with existing room component pattern

#### Notable Connections:

- **Emergency shutdown pattern mirrors existing failover** but inverted (shutdown vs. fallback)
- **State machine emerges:** Normal → Emergency → Recovering → Normal (clear lifecycle)
- **Diagnostic exposure serves dual purpose:** debugging AND HA automation triggers
- **Modbus elimination is selective:** outputs stay (necessary hardware), sensors go (cost/complexity)

---

## Idea Categorization

### Immediate Opportunities
*Ideas ready to implement now*

1. **Simplified `room_sensors.yaml` Component**
   - Description: Rewrite `room_sensors.yaml` to remove Modbus tiers, keep only HA sensor → Emergency logic
   - Why immediate: Clear requirements, existing pattern to adapt, blocks other Epic 5 work
   - Resources needed: 1 developer, 4-6 hours, existing component as template

2. **Configurable Timeout Parameters**
   - Description: Add vars: `emergency_timeout` (180s), `recovery_stability_timeout` (60s), `check_interval` (10s)
   - Why immediate: Simple vars addition, enables flexible testing and deployment tuning
   - Resources needed: Minimal, part of component rewrite

3. **State Tracking Text Sensor**
   - Description: Repurpose `text_sensor.{zone}_temp_source` to show "Normal/Emergency/Recovering"
   - Why immediate: Clear UI value for HA dashboards, simple lambda modification
   - Resources needed: 1 hour, integrated with component rewrite

### Future Innovations
*Ideas requiring development/research*

1. **HA-Side Monitoring Dashboard**
   - Description: Create HA dashboard card showing all room emergency states, time since last valid sensor
   - Development needed: HA Lovelace configuration, sensor aggregation
   - Timeline estimate: Post Epic 5 implementation (1-2 weeks after)

2. **Recovery Automation Testing**
   - Description: Automated testing framework for HA unavailability scenarios (kill HA, wait, restore, verify recovery)
   - Development needed: Test harness, CI integration, scenario scripting
   - Timeline estimate: 2-3 weeks (can be parallel with implementation)

3. **Multi-Threshold Warning System**
   - Description: Add warning state at 2 min, emergency at 3 min (vs. single threshold)
   - Development needed: Additional state logic, HA notification integration
   - Timeline estimate: Future enhancement if simple approach proves insufficient

### Moonshots
*Ambitious, transformative concepts*

1. **Predictive Emergency Prevention**
   - Description: ML model predicting HA unavailability from network metrics, pre-emptive safe mode
   - Transformative potential: Zero unplanned shutdowns, graceful degradation
   - Challenges to overcome: Complexity vs. benefit ratio, false positives, requires extensive data collection

2. **Mesh Sensor Fallback Network**
   - Description: ESPHome nodes share sensor data peer-to-peer when HA unavailable (ESP-NOW protocol)
   - Transformative potential: True HA-independent operation while maintaining sensor accuracy
   - Challenges to overcome: Network topology complexity, synchronization, Epic 5 goal is simplification

### Insights & Learnings
*Key realizations from the session*

- **"Simplicity is a feature"**: Removing the 3rd failover tier actually improves safety by making behavior predictable
- **"Emergency is not failure"**: The 3-minute emergency shutdown is a designed safety feature, not a system failure to be avoided at all costs
- **"Configuration over code"**: Making timeouts configurable via vars enables field tuning without reflashing devices
- **"Room autonomy scales"**: Distributed emergency logic avoids cascading failures and scales linearly with room count
- **"Cost drives architecture"**: The move from Modbus is fundamentally economic (expensive sensors, complex wiring), not technical
- **"State visibility matters"**: Exposing Normal/Emergency/Recovering states enables HA automations (notifications, alternative heating strategies)

---

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: Rewrite `room_sensors.yaml` Component

- **Rationale:** Blocks all other Epic 5 work; clear requirements emerged from SCAMPER; existing pattern to adapt
- **Next steps:**
  1. Create `components/room_sensors_v5.yaml` (new file, preserve old for reference)
  2. Remove Modbus platforms and controller definitions
  3. Simplify lambda to 2-tier: HA sensor → Emergency
  4. Add configurable vars: `emergency_timeout`, `recovery_stability_timeout`, `check_interval`
  5. Implement state machine: Normal → Emergency → Recovering
  6. Update text_sensor to show current state
- **Resources needed:** 
  - Developer: 4-6 hours
  - Testing device: 1 A16 board with room components
  - HA test environment for unavailability simulation
- **Timeline:** 1-2 days for implementation + initial testing

#### #2 Priority: Integrate Emergency Shutdown Logic

- **Rationale:** Core safety requirement (3-min hard requirement); must be reliable and well-tested
- **Next steps:**
  1. Add globals: `emergency_triggered`, `last_valid_time`, `recovery_start_time`
  2. Implement timeout tracking in template sensor lambda
  3. Create emergency action: turn off relay + set PID mode OFF
  4. Implement recovery logic with stability check
  5. Add logging (WARN at pre-emergency intervals, ERROR at trigger)
  6. Expose binary_sensor or text_sensor for HA visibility
- **Resources needed:**
  - Developer: 3-4 hours (part of component rewrite)
  - Physical testing: simulate HA down for >3 min, verify relays OFF
- **Timeline:** Concurrent with Priority #1 (integrated work)

#### #3 Priority: Update Room Component Packages

- **Rationale:** All 15+ room components need to switch from old to new `room_sensors.yaml`; migration path must be clean
- **Next steps:**
  1. Update `components/rooms/first_floor/*.yaml` to use new component
  2. Remove `modbus_controller_address` var from all room package calls
  3. Remove `ha_humidity_sensor_id` var (if present)
  4. Add optional timeout overrides if specific rooms need different values
  5. Test one room fully before mass migration
  6. Document migration in `docs/epic-5-migration-guide.md`
- **Resources needed:**
  - Developer: 2-3 hours for updates
  - Testing time: 1 room thoroughly, then batch update
- **Timeline:** After Priority #1 & #2 complete (1 day for testing, 2 hours for migration)

---

## Reflection & Follow-up

### What Worked Well

- **SCAMPER framework** provided systematic coverage - ensured we didn't miss key architectural decisions
- **Focused session goal** (technical challenges) kept discussion concrete and actionable
- **Real-time decision making** (A/B/C choices) maintained momentum and captured clear preferences
- **Building on Epic 4** - room-based architecture made many decisions obvious (distributed vs. centralized)
- **Cost context** (Modbus sensors expensive/complex) clarified the "why" behind simplification

### Areas for Further Exploration

- **Testing strategy:** How to reliably simulate HA unavailability in CI/local testing? Mock API? Network rules?
- **Migration sequence:** Should we pilot on one floor, or migrate all rooms simultaneously?
- **HA-side coordination:** Does HA need automations to handle ESPHome emergency states? Notification strategy?
- **Hardware implications:** Can we physically remove Modbus wiring/hardware after migration, or keep as fallback during transition?
- **Performance:** Impact of 8+ rooms polling HA sensors simultaneously? Stagger check intervals?

### Recommended Follow-up Techniques

- **"Yes, And..." Building:** For recovery automation ideas - explore what HA should do when it detects emergency states
- **Five Whys:** For testing strategy - dig into root requirements for reliable emergency testing
- **Assumption Reversal:** Challenge "3 minutes is right" - explore if timeout should be dynamic based on time of day, season, etc.

### Questions That Emerged

- **Q1:** Should emergency timeout differ between radiant (slow response) and fancoil (fast response) rooms?
- **Q2:** What happens if HA goes down during the night when heating is minimal? Still enforce emergency or context-aware?
- **Q3:** Should we log emergency events to persistent storage (SD card) for later analysis?
- **Q4:** Do we need a "manual override" switch in ESPHome to force relays on even during HA unavailability? (maintenance scenario)
- **Q5:** How does the radiant pump management script interact with per-room emergency states? Needs coordination logic?

### Next Session Planning

- **Suggested topics:**
  - Testing strategy brainstorming (CI/CD, manual testing, HA unavailability simulation)
  - Migration rollout plan (phased approach, rollback strategy)
  - HA automation design (what HA does when it sees emergency states)
- **Recommended timeframe:** After Priority #1 is implemented (1 week out)
- **Preparation needed:**
  - Working prototype of new `room_sensors.yaml`
  - One test room fully migrated
  - Initial test results from HA unavailability simulation

---

*Session facilitated using the BMAD-METHOD™ brainstorming framework*
