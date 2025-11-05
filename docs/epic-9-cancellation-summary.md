# Epic 9: Occupancy-Based Climate Control - Cancellation Summary

**Decision Date:** November 2025  
**Decision:** Epic 9 cancelled - Occupancy control will be implemented in Home Assistant, not ESPHome  
**Impact:** Low - No ESPHome code was written, only planning documents exist

---

## Executive Summary

Epic 9 (Occupancy-Based Climate Optimization) has been cancelled. The functionality will be implemented as **Home Assistant automations** rather than ESPHome firmware components. This decision was made during the planning phase before any code was written, minimizing impact and maximizing future flexibility.

---

## Decision Rationale

### Why Home Assistant is Better for Occupancy Control

1. **Superior Flexibility**
   - HA automations are YAML-based and can be modified instantly without firmware compilation
   - Testing changes takes seconds, not minutes (no OTA firmware deployment required)
   - Easier to experiment with different occupancy detection strategies

2. **No Deployment Overhead**
   - Changes don't require ESPHome compilation (20-30 seconds)
   - No OTA updates to multiple boards (30-60 seconds per board)
   - No risk of firmware update failures during deployment

3. **Richer Logic and Tools**
   - HA provides better tools for complex occupancy patterns (time-of-day, multi-sensor fusion, etc.)
   - HA has native occupancy entity types and history tracking
   - HA can integrate weather, calendar, and other contextual data easily

4. **Easier Debugging**
   - HA automation debugging via UI (trace mode, execution logs)
   - ESPHome lambda debugging requires serial logging and firmware reflashing
   - Faster iteration during troubleshooting

5. **Equipment-Aware Control**
   - HA can distinguish fancoil vs. radiant equipment via attributes or naming conventions
   - HA can apply appropriate control strategies (force OFF vs. setpoint reduction)
   - Easier to add new equipment types or control strategies over time

---

## Architectural Impact

### ESPHome Scope (Unchanged)

ESPHome boards continue to focus on:
- **Hardware Control:** Direct control of relays, valves, PIDs, sensors
- **Safety Conditions:** Emergency and window detection (Epic 8 coordinator)
- **Real-Time Control:** PID loops, failover logic, fast response

**No new ESPHome components required:**
- `room_occupancy_condition.yaml` - NOT created
- `room_occupancy_condition_stub.yaml` - NOT created

### Epic 8 Coordinator (Unchanged)

The Epic 8 coordinator architecture remains limited to:
- **Emergency Condition:** Priority 1 (highest)
- **Window Condition:** Priority 2

**No occupancy condition added** - coordinator handles 2 conditions, not 3.

**Note:** Epic 8 goal achieved - created extensible foundation that **could** support more conditions. The fact that occupancy is handled in HA doesn't invalidate the coordinator design.

### Home Assistant Scope (Expanded)

Home Assistant will handle:
- **Occupancy Detection:** Monitor PIR, mmWave, or composite occupancy sensors
- **Equipment Awareness:** Distinguish fancoil vs. radiant systems
- **Control Logic:** 
  - Fancoil rooms: Force PID OFF when unoccupied (fast response)
  - Radiant rooms: Reduce setpoints (preserve thermal mass)
- **Coordination:** Respect emergency and window conditions from ESPHome

---

## Implementation Approach (HA Automations)

### Example: Fancoil Room Occupancy Control

```yaml
# automation: Unoccupied Room - Fancoil Shutdown
trigger:
  - platform: state
    entity_id: binary_sensor.soggiorno_occupancy
    to: 'off'
    for:
      hours: 2  # Unoccupied for 2 hours
condition:
  - condition: state
    entity_id: binary_sensor.soggiorno_emergency
    state: 'off'  # No emergency condition
  - condition: state
    entity_id: binary_sensor.soggiorno_window_open
    state: 'off'  # Window closed
action:
  - service: climate.turn_off
    target:
      entity_id: climate.pid_soggiorno
```

### Example: Radiant Room Occupancy Control

```yaml
# automation: Unoccupied Room - Radiant Setpoint Reduction
trigger:
  - platform: state
    entity_id: binary_sensor.camera_letto_occupancy
    to: 'off'
    for:
      hours: 2
condition:
  - condition: state
    entity_id: binary_sensor.camera_letto_emergency
    state: 'off'
  - condition: state
    entity_id: binary_sensor.camera_letto_window_open
    state: 'off'
action:
  - service: climate.set_temperature
    target:
      entity_id: climate.pid_camera_letto
    data:
      temperature: >
        {% if state_attr('climate.pid_camera_letto', 'hvac_action') == 'heating' %}
          18  # Reduced heating setpoint
        {% else %}
          28  # Reduced cooling setpoint
        {% endif %}
```

---

## Documentation Updates

### Files Updated

1. **Epic 9 Brief** (`docs/epic-9-brief.md`)
   - Added cancellation notice at top
   - Status changed to "❌ CANCELLED"
   - Original content preserved for historical reference

2. **All Epic 9 Stories** (5 files in `docs/stories/`)
   - Story 9.1: Occupancy Condition Component
   - Story 9.2: Occupancy Stub Component
   - Story 9.3: Single-Room Validation
   - Story 9.4: Multi-Room Rollout
   - Story 9.5: Completion Documentation
   - All marked "❌ CANCELLED - Home Assistant Implementation"
   - Original content preserved

3. **PRD** (`docs/prd.md`)
   - Version bumped to 1.3 (November 2025)
   - Added "Important Note: Occupancy-Based Climate Control" section
   - Clarified two-tier architecture (ESPHome = hardware control, HA = intelligence)

4. **Project Brief** (`docs/brief.md`)
   - Updated "Long-Term Vision" section
   - Added note that occupancy control will be HA automations

5. **Epic 8 Completion Report** (`docs/epic-8-completion-report.md`)
   - Removed "Epic 9: Next Epic" section
   - Added "Occupancy-Based Climate Control (Home Assistant Implementation)" section
   - Clarified that coordinator extensibility goal was achieved even without occupancy condition

---

## Design Change Summary

The `docs/epic-9-design-change-summary.md` file documented a mid-epic design change (equipment-aware control: fancoil shutdown vs. radiant setpoint reduction). With Epic 9 cancelled, this file is now **obsolete** but preserved for historical reference.

**Status:** Design change document archived - decisions remain valid but will be implemented in HA automations, not ESPHome.

---

## Benefits of This Decision

### Immediate Benefits

1. **No Code Debt:** No ESPHome components created that would need maintenance
2. **Faster Implementation:** HA automations are quicker to write and test
3. **Lower Risk:** No firmware changes to production boards
4. **Easier Evolution:** Can refine occupancy logic without firmware deployments

### Long-Term Benefits

1. **Flexibility:** Easy to add new occupancy strategies (calendar-based, weather-aware, etc.)
2. **Maintainability:** HA automations are easier for future maintainers to understand
3. **Integration:** Simpler to integrate with other HA features (notifications, energy monitoring, etc.)
4. **Debugging:** HA's automation trace and execution logs provide excellent debugging

---

## What Was Preserved

### Epic 8 Architecture (Fully Validated)

- Coordinator pattern proven successful for emergency + window conditions
- Condition interface contract (state + priority globals) works perfectly
- Extensibility goal achieved - **could** add more conditions if needed

### Historical Documentation (All Preserved)

- Epic 9 brief documents requirements and analysis (valuable for HA implementation)
- Stories document acceptance criteria and testing approach (reusable for HA)
- Design change summary documents equipment-aware control rationale (still valid)

### Project Knowledge (Captured)

- Occupancy control strategies analyzed and documented
- Equipment-aware control requirements clearly defined
- Implementation approach validated (fancoil shutdown, radiant setpoint reduction)

---

## Next Steps

### For Home Assistant Implementation

1. **Create occupancy sensors** (if not already present)
   - PIR sensors for high-traffic rooms
   - mmWave sensors for bedrooms (better occupancy detection)
   - Composite occupancy entities combining multiple sensors

2. **Write HA automations** using examples above
   - Start with 1-2 test rooms (fancoil + radiant)
   - Validate 2-hour delay period is appropriate
   - Test recovery behavior (room becomes occupied again)

3. **Create HA dashboard** for occupancy monitoring
   - Show occupancy status per room
   - Display energy savings estimates
   - Log occupancy-triggered shutdowns

4. **Document HA automation patterns** for future rooms
   - Template automations for easy replication
   - Document testing procedures
   - Create troubleshooting guide

---

## Lessons Learned

### Planning Value

- Thorough Epic planning valuable even if not implemented in ESPHome
- Requirements analysis transferable to HA implementation
- Early design decisions (equipment-aware control) remain valid

### Architectural Flexibility

- Two-tier architecture (ESPHome hardware, HA intelligence) provides flexibility
- Not everything needs to be in ESPHome firmware
- HA automations complement ESPHome's strengths

### Decision Timing

- Made decision during planning phase (before code written)
- Minimal sunk cost (planning documents only)
- Better to decide now than after ESPHome components created

---

## Conclusion

Epic 9 cancellation is a **positive architectural decision** that:
- Leverages HA's strengths for complex automation logic
- Preserves ESPHome's focus on hardware control and safety
- Provides better flexibility and maintainability long-term
- Minimizes technical debt and deployment complexity

The Epic 8 coordinator architecture remains successful and validated. The decision not to extend it to occupancy doesn't invalidate its design - it simply clarifies the boundary between ESPHome (hardware + safety) and Home Assistant (intelligence + automation).

---

**Document Status:** Complete  
**Last Updated:** November 2025  
**Author:** Mary (Business Analyst)
