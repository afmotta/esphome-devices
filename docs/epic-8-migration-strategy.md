# Epic 8: Migration Strategy

**Document Version:** 1.0  
**Date:** October 31, 2025  
**Status:** Draft  
**Epic:** 8 - Unified State Machine Architecture  
**Dependencies:** epic-8-condition-interface-spec.md v1.0, epic-8-coordinator-design.md v1.0

---

## Purpose

This document provides a **step-by-step migration plan** for transitioning rooms from the Epic 5/7 architecture (separate emergency shutdown and window detection components) to the Epic 8 unified architecture (condition components + coordinator).

**Migration Goals:**
1. Zero downtime during migration (rooms remain operational)
2. Incremental rollout with validation at each step
3. Clear rollback procedure if issues arise
4. Preserve all existing functionality during transition

---

## Architecture Comparison

### Current Architecture (Epic 5 + Epic 7)

```yaml
# Per room: 3 separate components
packages:
  - file: components/room_sensors.yaml            # Emergency detection
    vars: { zone_slug, zone_name, ha_temperature_sensor_id }
  
  - file: components/room_emergency_shutdown.yaml  # Emergency control (PID shutdown)
    vars: { zone_slug, zone_name, pid_id }
  
  - file: components/room_window_detection.yaml    # Window detection + control (monolithic)
    vars: { zone_slug, zone_name, ha_window_sensor_id, pid_id, window_shutdown_modes }
```

**Issues:**
- 60+ lines of duplicated PID control logic (emergency_shutdown vs window_detection)
- No coordination between conditions (race conditions possible)
- Each condition independently controls PID (no priority hierarchy)
- Future extensibility blocked (occupancy would require copying pattern again)

---

### Target Architecture (Epic 8)

```yaml
# Per room: 3 condition components + 1 coordinator
packages:
  - file: components/room_emergency_condition.yaml  # Emergency detection only (NEW)
    vars: { zone_slug, zone_name, ha_temperature_sensor_id }
  
  - file: components/room_window_condition.yaml     # Window detection only (NEW)
    vars: { zone_slug, zone_name, ha_window_sensor_id, window_shutdown_modes }
  
  - file: components/room_control_coordinator.yaml  # Unified PID control (NEW)
    vars: { zone_slug, zone_name, pid_id }
```

**Benefits:**
- Single source of PID control logic (coordinator only)
- Priority hierarchy prevents race conditions (emergency > window > occupancy)
- Conditions are independently testable (no PID coupling)
- Extensible architecture (add occupancy without touching existing conditions)
- 40% code reduction (eliminate duplicated control logic)

---

## Migration Prerequisites

### 1. Component Development

**Must be completed before any migration:**

- [ ] Create `components/room_emergency_condition.yaml` (refactored from `room_sensors.yaml`)
- [ ] Create `components/room_window_condition.yaml` (refactored from `room_window_detection.yaml`)
- [ ] Create `components/room_control_coordinator.yaml` (new component)
- [ ] Validate all components comply with interface spec (checklist in `epic-8-condition-interface-spec.md`)

### 2. Test Environment

**Prepare validation infrastructure:**

- [ ] Select test room (recommendation: **Soggiorno** — has both emergency + window)
- [ ] Document baseline behavior (capture 48h of sensor data before migration)
- [ ] Create HA automation for coordinator-driven resume (see below)
- [ ] Prepare monitoring dashboard showing all condition states + coordinator status

### 3. Rollback Preparation

**Have rollback ready before migration:**

- [ ] Git commit all working Epic 5/7 configurations
- [ ] Tag commit: `epic-7-stable`
- [ ] Document rollback procedure (see section below)
- [ ] Test rollback procedure on test room first

---

## Migration Phases

### Phase 1: Test Room Migration (Week 1, Days 1-3)

**Target:** Single room (Soggiorno recommended)

#### Step 1.1: Backup Current Configuration

```bash
# Commit current working state
git add devices/distribuzione-primo-piano.yaml
git add components/rooms/first_floor/soggiorno.yaml
git commit -m "Pre-Epic-8: Soggiorno baseline (Epic 5+7)"
git tag epic-7-soggiorno-baseline
```

#### Step 1.2: Update Room Component Package

**File:** `components/rooms/first_floor/soggiorno.yaml`

**Before (Epic 5 + 7):**

```yaml
packages:
  # Epic 5: Emergency shutdown (2 components)
  - file: ../../room_sensors.yaml
    vars:
      zone_slug: soggiorno
      zone_name: Soggiorno
      ha_temperature_sensor_id: sensor.soggiorno_temperature
  
  - file: ../../room_emergency_shutdown.yaml
    vars:
      zone_slug: soggiorno
      zone_name: Soggiorno
      pid_id: soggiorno_pid
  
  # Epic 7: Window detection (monolithic)
  - file: ../../room_window_detection.yaml
    vars:
      zone_slug: soggiorno
      zone_name: Soggiorno
      ha_window_sensor_id: binary_sensor.soggiorno_window
      pid_id: soggiorno_pid
      window_shutdown_modes: "cooling, heating"
```

**After (Epic 8):**

```yaml
packages:
  # Epic 8: Emergency condition (detection only)
  - file: ../../room_emergency_condition.yaml
    vars:
      zone_slug: soggiorno
      zone_name: Soggiorno
      ha_temperature_sensor_id: sensor.soggiorno_temperature
      emergency_timeout: 180
      recovery_timeout: 60
  
  # Epic 8: Window condition (detection only)
  - file: ../../room_window_condition.yaml
    vars:
      zone_slug: soggiorno
      zone_name: Soggiorno
      ha_window_sensor_id: binary_sensor.soggiorno_window
      window_shutdown_modes: "cooling, heating"
      window_timeout: 180
      recovery_timeout: 60
  
  # Epic 8: Coordinator (unified control)
  - file: ../../room_control_coordinator.yaml
    vars:
      zone_slug: soggiorno
      zone_name: Soggiorno
      pid_id: soggiorno_pid
```

#### Step 1.3: Validate Configuration

```bash
# Validate YAML syntax and component compilation
cd /Users/alberto/src/alberto/esphome-devices
esphome config devices/distribuzione-primo-piano.yaml

# Look for errors related to:
# - Missing global references
# - Duplicate entity IDs
# - Invalid variable substitutions
```

**Expected Changes:**
- New entities: `text_sensor.soggiorno_emergency_state`, `text_sensor.soggiorno_window_state`, `text_sensor.soggiorno_coordinator_status`
- Removed entities: `text_sensor.soggiorno_sensor_state`, `text_sensor.soggiorno_window_detection_state`

#### Step 1.4: Deploy to Test Room

```bash
# Compile and upload
esphome compile devices/distribuzione-primo-piano.yaml
esphome upload devices/distribuzione-primo-piano.yaml

# Monitor logs during boot
esphome logs devices/distribuzione-primo-piano.yaml
```

**Watch for:**
- All conditions initialize to Normal (state=0)
- Coordinator reports "Normal (All Clear)"
- PID climate entity operates normally
- No ERROR or WARN logs related to Epic 8 components

#### Step 1.5: Functional Testing (48-72 hours)

**Test Emergency Condition:**

1. **Trigger:** Disconnect HA temperature sensor (or simulate via HA Developer Tools)
2. **Expected:** After 180s, `soggiorno_emergency_state` → Active (1), coordinator → "Shutdown: Emergency (Active)", PID forced OFF
3. **Clear:** Reconnect sensor
4. **Expected:** Immediate transition to Recovering (2), after 60s → Normal (0), PID resumes via HA automation

**Test Window Condition:**

1. **Trigger:** Open window (or simulate via HA binary_sensor)
2. **Expected:** After 180s, `soggiorno_window_state` → Active (1), coordinator → "Shutdown: Window (Active)", PID forced OFF
3. **Clear:** Close window
4. **Expected:** Immediate transition to Recovering (2), after 60s → Normal (0), PID resumes

**Test Priority Hierarchy:**

1. **Trigger:** Trigger both emergency and window simultaneously
2. **Expected:** Coordinator shows "Shutdown: Emergency (Active)" (higher priority)
3. **Clear:** Clear emergency first
4. **Expected:** Coordinator switches to "Shutdown: Window (Active)" (window still active)
5. **Clear:** Clear window
6. **Expected:** Coordinator → "Normal (All Clear)", PID resumes

**Test Mode-Aware Shutdown (Window):**

1. **Setup:** PID in heating mode, window configured for `window_shutdown_modes: "cooling"`
2. **Trigger:** Open window
3. **Expected:** Window condition remains Normal (heating not in shutdown modes)
4. **Setup:** Switch PID to cooling mode
5. **Trigger:** Open window (still open)
6. **Expected:** Window condition triggers after 180s

#### Step 1.6: Validation Criteria

**✅ Migration successful if:**

- [ ] Emergency condition triggers/clears correctly (2+ test cycles)
- [ ] Window condition triggers/clears correctly (2+ test cycles)
- [ ] Priority hierarchy behaves correctly (emergency overrides window)
- [ ] PID shutdown/resume operates as expected
- [ ] No ERROR logs in 48h monitoring period
- [ ] Room climate control functions normally (temperature maintained)
- [ ] HA dashboard shows all new sensors correctly

**❌ Rollback if:**

- [ ] PID fails to shutdown when condition triggers
- [ ] PID fails to resume when conditions clear
- [ ] Coordinator reports incorrect active condition
- [ ] Frequent ERROR logs related to Epic 8 components
- [ ] Room temperature deviates >2°C from setpoint (climate control degraded)

---

### Phase 2: Rollback Procedure

**If validation fails, immediate rollback:**

#### Rollback Step 1: Revert to Epic 7 Configuration

```bash
# Revert room component to Epic 5+7 packages
git checkout epic-7-soggiorno-baseline -- components/rooms/first_floor/soggiorno.yaml

# Validate reverted config
esphome config devices/distribuzione-primo-piano.yaml
```

#### Rollback Step 2: Redeploy Previous Version

```bash
# Compile and upload Epic 7 configuration
esphome compile devices/distribuzione-primo-piano.yaml
esphome upload devices/distribuzione-primo-piano.yaml

# Monitor restoration
esphome logs devices/distribuzione-primo-piano.yaml
```

#### Rollback Step 3: Verify Restoration

- [ ] `text_sensor.soggiorno_sensor_state` (Epic 5) restored
- [ ] `text_sensor.soggiorno_window_detection_state` (Epic 7) restored
- [ ] PID operates normally
- [ ] No Epic 8 entities remain in HA

**Rollback Time:** <10 minutes (compile + upload)

---

### Phase 3: Remaining Rooms Migration (Week 1-2, Days 4-14)

**Once test room validated for 72h+, proceed with remaining rooms.**

#### Migration Order (Priority-Based)

**Tier 1: High-Priority Rooms (Days 4-7)**

Rooms with critical climate control + both conditions:

1. **Bagno Grande** (Epic 5 + 7) — Master bathroom, high occupancy
2. **Camera da Letto** (Epic 5 + 7) — Bedroom, sleep quality critical
3. **Studio** (Epic 5 + 7) — Office, daytime occupancy

**Tier 2: Medium-Priority Rooms (Days 8-11)**

Rooms with single condition or lower criticality:

4. **Cucina** (Epic 5 only) — Kitchen, emergency detection only
5. **Bagno Piccolo** (Epic 5 only) — Guest bathroom, lower occupancy
6. **Corridoio** (Epic 5 only) — Hallway, minimal climate needs

**Tier 3: Low-Priority Rooms (Days 12-14)**

Rooms with minimal usage or radiant-only control:

7. **Ripostiglio** (Epic 5 only) — Storage, minimal climate control
8. *(Any future rooms)*

#### Migration Cadence

**Recommendation:** 1 room per day, staggered deployment

- **Morning (9-10 AM):** Deploy migration to next room
- **Daytime monitoring:** Watch logs and HA sensors for anomalies
- **Evening validation:** Test trigger/clear cycles manually
- **Overnight soak:** 12+ hours of autonomous operation
- **Next morning:** Review logs, proceed to next room if validated

**Rationale:** Staggered deployment limits blast radius if issues arise. If Room #4 has problems, Rooms #1-3 remain operational.

---

### Phase 4: Cleanup & Documentation (Week 3, Days 15-21)

#### Step 4.1: Deprecate Old Components

**Once all rooms migrated:**

```bash
# Move Epic 5/7 components to deprecated folder
mv components/room_sensors.yaml components/deprecated/room_sensors_v5.yaml
mv components/room_emergency_shutdown.yaml components/deprecated/room_emergency_shutdown_v5.yaml
mv components/room_window_detection.yaml components/deprecated/room_window_detection_v7.yaml

# Update deprecated README
cat >> components/deprecated/README.md << 'EOF'

## Epic 8 Migration (October 2025)

Deprecated components replaced by unified architecture:
- `room_sensors_v5.yaml` → `room_emergency_condition.yaml` (detection only)
- `room_emergency_shutdown_v5.yaml` → `room_control_coordinator.yaml` (control delegated)
- `room_window_detection_v7.yaml` → `room_window_condition.yaml` (detection only)

See `docs/epic-8-migration-strategy.md` for migration details.
EOF
```

#### Step 4.2: Update Documentation

- [ ] Update `docs/architecture.md` with Epic 8 coordinator pattern
- [ ] Update `docs/epic-8-brief.md` status → "Complete"
- [ ] Create `docs/epic-8-completion-report.md` with migration results
- [ ] Update room component README files with Epic 8 usage examples
- [ ] Update `.github/copilot-instructions.md` to reference Epic 8 patterns

#### Step 4.3: Create Completion Report

**File:** `docs/epic-8-completion-report.md`

**Contents:**
- Migration timeline (actual dates for each room)
- Issues encountered and resolutions
- Performance metrics (code reduction %, entity count change)
- Lessons learned for future migrations
- Validation results (test cycles passed per room)

#### Step 4.4: Git Tagging

```bash
# Tag successful completion
git add .
git commit -m "Epic 8 Complete: Unified state machine architecture deployed to all rooms"
git tag epic-8-complete
git push origin epic-8
git push origin epic-8-complete
```

---

## Backward Compatibility

### Coexistence During Migration

**Can Epic 5/7 and Epic 8 rooms coexist?**

✅ **YES** — The architectures are completely independent per room.

**Example Safe State:**

```
Rooms migrated to Epic 8:
- Soggiorno (Epic 8 coordinator + conditions)
- Bagno Grande (Epic 8 coordinator + conditions)

Rooms still on Epic 5+7:
- Camera da Letto (Epic 5+7 separate components)
- Studio (Epic 5+7 separate components)
```

**No conflicts because:**
- Each room uses isolated component instances (via `zone_slug`)
- Global variable names are scoped per room
- PID control is room-local (no shared state)
- HA entities have unique names per room

**Recommendation:** Migrate all rooms within 2 weeks to avoid maintaining two architectures long-term.

---

## HA Automation Updates

### Required: Coordinator Resume Automation

**Epic 8 MVP uses HA-driven resume** (coordinator forces shutdown but doesn't auto-resume).

**Create HA Automation:**

```yaml
# File: home-assistant/automations/epic-8-coordinator-resume.yaml

automation:
  - id: epic8_coordinator_resume_soggiorno
    alias: "Epic 8: Resume Soggiorno Climate After Conditions Clear"
    description: "Resume PID control when all conditions return to Normal"
    
    trigger:
      - platform: state
        entity_id: text_sensor.soggiorno_coordinator_status
        to: "Normal (All Clear)"
        for: "00:00:30"  # Wait 30s for stability
    
    condition:
      - condition: state
        entity_id: climate.soggiorno_pid
        state: "off"  # Only resume if PID is currently OFF
    
    action:
      - service: climate.set_hvac_mode
        target:
          entity_id: climate.soggiorno_pid
        data:
          hvac_mode: "{{ state_attr('climate.soggiorno_pid', 'last_hvac_mode') | default('heat') }}"
      
      - service: system_log.write
        data:
          message: "Epic 8: Resumed Soggiorno climate control (all conditions normal)"
          level: info
```

**Replicate for each room** (or use template automation with room list).

---

## Monitoring & Observability

### Dashboard Additions

**Add to HA Dashboard per room:**

```yaml
# Epic 8 Condition Monitoring Card
type: entities
title: Soggiorno - Epic 8 Status
entities:
  - entity: text_sensor.soggiorno_coordinator_status
    name: Control Status
  - entity: text_sensor.soggiorno_emergency_state
    name: Emergency Condition
  - entity: text_sensor.soggiorno_window_state
    name: Window Condition
  - entity: climate.soggiorno_pid
    name: PID Climate
```

### Log Monitoring

**Watch ESPHome logs during migration:**

```bash
# Real-time monitoring
esphome logs devices/distribuzione-primo-piano.yaml | grep -E "(coordinator|condition|Emergency|Window)"

# Look for patterns:
# - "Emergency ACTIVE" / "Emergency NORMAL"
# - "Window ACTIVE" / "Window NORMAL"  
# - "Shutdown due to <condition>"
# - "Resuming climate control"
```

### Metrics to Track

| Metric                            | Pre-Epic-8    | Post-Epic-8   | Target             |
| --------------------------------- | ------------- | ------------- | ------------------ |
| **Code lines per room**           | ~180 lines    | ~110 lines    | -40% reduction     |
| **PID control logic duplication** | 2 copies      | 1 copy        | -50%               |
| **Entity count per room**         | 5 entities    | 4 entities    | -20%               |
| **State machine components**      | 2 independent | 2 coordinated | +100% coordination |
| **Condition trigger latency**     | 10-15s        | 10-15s        | No regression      |
| **PID shutdown latency**          | <1s           | <1s           | No regression      |

---

## Risk Mitigation

### Identified Risks & Mitigations

#### Risk 1: PID Fails to Shutdown When Condition Triggers

**Probability:** Low  
**Impact:** High (safety/energy waste)  
**Mitigation:**
- Test emergency+window triggers extensively in test room (48h validation)
- Monitor coordinator logs for "Shutdown due to X" confirmations
- Keep Epic 7 components available for quick rollback

**Detection:** PID remains in heating/cooling mode when condition Active

**Response:** Immediate rollback to Epic 7 configuration

---

#### Risk 2: Coordinator Never Resumes PID (Stuck in OFF)

**Probability:** Medium  
**Impact:** Medium (loss of climate control)  
**Mitigation:**
- Test HA automation thoroughly before rollout
- Add HA automation logging (confirm resume action triggered)
- Manual override available via HA dashboard

**Detection:** Coordinator shows "Normal (All Clear)" but PID remains OFF

**Response:** Check HA automation fired; manual PID enable if needed

---

#### Risk 3: Priority Hierarchy Incorrect (Window Overrides Emergency)

**Probability:** Low  
**Impact:** Medium (wrong condition shown in diagnostics)  
**Mitigation:**
- Validate priority values in component defaults (emergency=1, window=2)
- Test simultaneous trigger scenario explicitly in test room

**Detection:** Coordinator diagnostic shows wrong active condition

**Response:** Fix priority values in condition components, redeploy

---

#### Risk 4: Migration Breaks Existing HA Automations

**Probability:** Medium  
**Impact:** Low (automations need updates)  
**Mitigation:**
- Audit all HA automations referencing old sensor names
- Update automation entity references during migration
- Test automations post-migration

**Detection:** HA automations fail to trigger or show "entity unavailable"

**Response:** Update automation entity_id references to new sensor names

---

## Success Criteria

### Phase 1 Success (Test Room)

- [ ] 72+ hours of stable operation post-migration
- [ ] Emergency condition tested: 3+ trigger/clear cycles successful
- [ ] Window condition tested: 3+ trigger/clear cycles successful
- [ ] Priority hierarchy validated (simultaneous trigger test passed)
- [ ] Zero ERROR logs related to Epic 8 components
- [ ] Temperature control quality maintained (±1°C of pre-migration)

### Overall Migration Success

- [ ] All production rooms migrated to Epic 8 architecture
- [ ] Old Epic 5/7 components deprecated and moved to `deprecated/`
- [ ] Documentation updated (architecture.md, completion report)
- [ ] HA automations updated for all rooms
- [ ] 40%+ code reduction achieved (measured)
- [ ] Zero regressions in climate control quality
- [ ] Team trained on Epic 8 patterns (condition contract, coordinator)

---

## Timeline Summary

| Phase                     | Duration   | Activities                              | Validation          |
| ------------------------- | ---------- | --------------------------------------- | ------------------- |
| **Phase 1: Test Room**    | Days 1-3   | Migrate Soggiorno, intensive testing    | 48-72h soak test    |
| **Phase 2: Tier 1 Rooms** | Days 4-7   | Migrate 3 high-priority rooms           | Per-room validation |
| **Phase 3: Tier 2 Rooms** | Days 8-11  | Migrate 3 medium-priority rooms         | Per-room validation |
| **Phase 4: Tier 3 Rooms** | Days 12-14 | Migrate remaining rooms                 | Per-room validation |
| **Phase 5: Cleanup**      | Days 15-21 | Deprecate old components, finalize docs | Completion report   |

**Total Timeline:** 3 weeks (21 days)

---

## Post-Migration

### Future Enhancements Enabled

With Epic 8 foundation in place, these become straightforward:

1. **Epic 9: Occupancy Detection** — Add `room_occupancy_condition.yaml` (priority=3), no coordinator changes needed
2. **Dynamic Priorities** — Upgrade coordinator to read priorities from HA (context-aware)
3. **Advanced Diagnostics** — Add countdown timers to coordinator status sensor
4. **Bidirectional Communication** — Coordinator publishes "master disable" signal to conditions

### Lessons for Future Epics

- **Interface contracts accelerate development** — Well-defined contracts allowed conditions and coordinator to be developed independently
- **Stateless coordination simplifies testing** — Coordinator has no state, just reads+aggregates
- **Always-present pattern better than conditional includes** — Disabled conditions (state=0) cleaner than complex YAML conditionals
- **Phased migration reduces risk** — 1 room/day cadence caught issues early without widespread impact

---

## Version History

| Version | Date         | Changes                                       |
| ------- | ------------ | --------------------------------------------- |
| 1.0     | Oct 31, 2025 | Initial migration strategy for Epic 8 rollout |

---

## References

- **Interface Specification:** `epic-8-condition-interface-spec.md`
- **Coordinator Design:** `epic-8-coordinator-design.md`
- **Project Brief:** `epic-8-brief.md`
- **Epic 5 Documentation:** `epic-5-ha-only-sensors.md`, `epic-5-completion-report.md`
- **Epic 7 Documentation:** `epic-7-window-detection-guide.md`, `epic-7-completion-report.md`

---

**Document Status:** Ready for execution  
**Next Steps:** Begin Phase 1 by creating Epic 8 components (emergency condition, window condition, coordinator)

---

*Migration strategy created for Epic 8: Unified State Machine Architecture*
