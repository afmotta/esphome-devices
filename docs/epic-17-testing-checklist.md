# Epic 17 Testing Checklist: Three-Tier Seasonal Mode Selection

**Date:** January 22, 2026
**Device:** climate-control (Waveshare ESP32-S3)
**Status:** MVP Complete (Stories 17.1-17.5)

---

## Pre-Deployment Validation

### Compilation
- [ ] `esphome compile devices/climate-control.yaml` succeeds
- [ ] No errors related to seasonal mode components
- [ ] `components/seasonal_mode.yaml` includes season classification sensor

### Code Review
- [x] `select.hp_mode` created with HEAT/COOL/SANITARY_ONLY options
- [x] `text_sensor.hp_mode_reason` tracks CALENDAR_LOCK/DEMAND/MANUAL
- [x] `text_sensor.season_classification` shows current season
- [x] `binary_sensor.any_pid_requesting_heat` aggregates all PIDs
- [x] `binary_sensor.any_pid_requesting_cool` aggregates cooling-capable PIDs
- [x] Calendar gate logic implemented (Winter/Summer locks)
- [x] Demand-driven transitions implemented (shoulder seasons)
- [x] PID mode synchronization implemented

---

## Story 17.1: HP Mode State Management

### ESPHome Entities
- [ ] `select.climate_control_heat_pump_mode` visible in Home Assistant
- [ ] Mode has three options: HEAT, COOL, SANITARY_ONLY
- [ ] `text_sensor.climate_control_heat_pump_mode_reason` visible
- [ ] Mode persists across ESP32 reboot
- [ ] Mode can be changed via Home Assistant UI

### State Persistence Test
1. [ ] Set mode to HEAT via HA
2. [ ] Reboot ESP32 device
3. [ ] Verify mode is still HEAT after reboot
4. [ ] Verify reason is preserved

---

## Story 17.2: Calendar Gate Logic

### Winter Lock (Oct 15 - Apr 15)
**Test Period:** Any date between Oct 15 and Apr 14

- [ ] Mode automatically set to HEAT
- [ ] Reason shows "CALENDAR_LOCK"
- [ ] Manual override to COOL/SANITARY_ONLY is immediately reverted to HEAT
- [ ] Check ESPHome logs: "Winter Lock: HEAT" message appears

### Summer Lock (Jun 1 - Aug 31)
**Test Period:** Any date between Jun 1 and Aug 31

- [ ] Mode automatically set to COOL
- [ ] Reason shows "CALENDAR_LOCK"
- [ ] Manual override to HEAT/SANITARY_ONLY is immediately reverted to COOL
- [ ] Check ESPHome logs: "Summer Lock: COOL" message appears

### Spring Shoulder Entry (Apr 15)
**Test Period:** Apr 15 at 00:00

- [ ] Mode resets to SANITARY_ONLY at midnight
- [ ] Reason shows "CALENDAR_LOCK"
- [ ] Season classification shows "Spring Shoulder"

### Autumn Shoulder Entry (Sep 1)
**Test Period:** Sep 1 at 00:00

- [ ] Mode resets to SANITARY_ONLY at midnight
- [ ] Reason shows "CALENDAR_LOCK"
- [ ] Season classification shows "Autumn Shoulder"

---

## Story 17.3: PID Demand Aggregation

### Heating Demand Detection
**Test Condition:** Set one room to high heating setpoint (e.g., 25°C) while room is cold

- [ ] `binary_sensor.climate_control_any_pid_requesting_heat` turns ON
- [ ] Sensor turns ON when ANY PID enters heating mode
- [ ] Check that sensor monitors all 16 zones (12 radiant + 4 fancoil)

### Cooling Demand Detection
**Test Condition:** Set one room to low cooling setpoint (e.g., 20°C) while room is warm (during shoulder season)

- [ ] `binary_sensor.climate_control_any_pid_requesting_cool` turns ON
- [ ] Sensor turns ON when ANY cooling-capable PID enters cooling mode
- [ ] Check that sensor monitors all 11 cooling-capable zones (7 radiant + 4 fancoil)

### Multiple Zone Detection
- [ ] Heating demand sensor is ON if any of the 16 zones request heat
- [ ] Cooling demand sensor is ON if any of the 11 zones request cool
- [ ] Both sensors can be ON simultaneously (different rooms, different needs)

---

## Story 17.4: Demand-Driven Mode Transitions

### Shoulder Season Heating Transition
**Test Period:** Apr 16 - May 31 OR Sep 1 - Oct 14

1. [ ] Start with mode = SANITARY_ONLY
2. [ ] Trigger heating demand (raise setpoint in one room)
3. [ ] Verify mode changes to HEAT
4. [ ] Verify reason changes to "DEMAND"
5. [ ] Check ESPHome logs: "Demand Transition: HEAT" message appears
6. [ ] Verify ALL PIDs switch to HEAT mode

### Shoulder Season Cooling Transition
**Test Period:** Apr 16 - May 31 OR Sep 1 - Oct 14

1. [ ] Start with mode = SANITARY_ONLY (or HEAT)
2. [ ] Trigger cooling demand (lower setpoint in one room)
3. [ ] Verify mode changes to COOL
4. [ ] Verify reason changes to "DEMAND"
5. [ ] Check ESPHome logs: "Demand Transition: COOL" message appears
6. [ ] Verify cooling-capable PIDs switch to COOL mode
7. [ ] Verify heat-only PIDs (bathrooms) turn OFF

### Direct HEAT↔COOL Transitions
**Test Period:** Shoulder season only

1. [ ] Start in HEAT mode (via demand)
2. [ ] Trigger cooling demand
3. [ ] Verify direct transition to COOL (no SANITARY_ONLY stop)
4. [ ] Start in COOL mode
5. [ ] Trigger heating demand
6. [ ] Verify direct transition to HEAT (no SANITARY_ONLY stop)

### No Automatic Return to SANITARY_ONLY
**Test Period:** Shoulder season

1. [ ] Trigger heating demand → mode = HEAT
2. [ ] Heating demand stops (all PIDs satisfied)
3. [ ] Verify mode STAYS in HEAT (does not return to SANITARY_ONLY)
4. [ ] Mode should only change when opposite demand occurs

### Calendar Lock Override During Shoulder Season
**Test Period:** Shoulder season

1. [ ] Manually set mode to SANITARY_ONLY
2. [ ] Trigger heating or cooling demand
3. [ ] Verify demand overrides manual setting
4. [ ] Verify reason changes to "DEMAND"

---

## Story 17.5: Dashboard & Diagnostics

### Home Assistant Dashboard Setup
- [ ] Open `docs/ha-dashboard-config.yaml`
- [ ] Copy "Seasonal Mode" view to Home Assistant dashboard
- [ ] Navigate to new "Seasonal Mode" tab in HA
- [ ] Verify tab icon shows `mdi:calendar-sync`

### Current Mode Status Card
- [ ] Card displays current mode (HEAT/COOL/SANITARY_ONLY)
- [ ] Card displays mode reason (CALENDAR_LOCK/DEMAND/MANUAL)
- [ ] Card displays season classification (Winter Lock/Summer Lock/Spring Shoulder/Autumn Shoulder)
- [ ] Icons display correctly for each entity

### PID Demand Aggregation Display
- [ ] "Any PID Requesting Heat" sensor shows current state
- [ ] "Any PID Requesting Cool" sensor shows current state
- [ ] Gauge displays correctly for heating demand (green when off, red when on)
- [ ] Gauge displays correctly for cooling demand (green when off, blue when on)

### Calendar Gates Documentation
- [ ] Dashboard shows correct calendar gate schedule
- [ ] Winter Lock dates: Oct 15 - Apr 15
- [ ] Summer Lock dates: Jun 1 - Aug 31
- [ ] Spring Shoulder dates: Apr 16 - May 31
- [ ] Autumn Shoulder dates: Sep 1 - Oct 14

### Mode History Graphs
- [ ] Heat Pump Mode history graph displays correctly (24 hours)
- [ ] Mode Reason history graph displays correctly (24 hours)
- [ ] PID Demand history graph displays correctly (24 hours)
- [ ] Graphs update in real-time as mode changes

### Manual Override
- [ ] Manual mode dropdown displays correctly
- [ ] Can select HEAT mode via dropdown
- [ ] Can select COOL mode via dropdown
- [ ] Can select SANITARY_ONLY mode via dropdown
- [ ] Reason changes to "MANUAL" after manual override
- [ ] During shoulder season, demand overrides manual setting
- [ ] During locked season, calendar gate overrides manual setting (within 1 minute)

### System Behavior Documentation
- [ ] Dashboard includes explanation of CALENDAR_LOCK
- [ ] Dashboard includes explanation of DEMAND
- [ ] Dashboard includes explanation of MANUAL
- [ ] Dashboard includes success metrics

---

## Integration Tests

### PID Mode Synchronization
**Verify all PIDs update when hp_mode changes**

1. [ ] Set hp_mode = HEAT
2. [ ] Verify `climate.pid_radiant_soggiorno` mode = HEAT
3. [ ] Verify `climate.pid_fancoil_soggiorno` mode = HEAT
4. [ ] Verify all 16 PIDs are in HEAT mode

5. [ ] Set hp_mode = COOL
6. [ ] Verify `climate.pid_radiant_soggiorno` mode = COOL
7. [ ] Verify `climate.pid_fancoil_soggiorno` mode = COOL
8. [ ] Verify heat-only PIDs (bathrooms) mode = OFF
9. [ ] Verify cooling-capable PIDs are in COOL mode

10. [ ] Set hp_mode = SANITARY_ONLY
11. [ ] Verify all PIDs mode = OFF

### Heat-Only Zone Handling
**Bathrooms should not enter cooling mode**

1. [ ] Set hp_mode = COOL
2. [ ] Verify `climate.pid_radiant_bagno_terra` mode = OFF
3. [ ] Verify `climate.pid_radiant_bagno_grande` mode = OFF
4. [ ] Verify `climate.pid_radiant_bagno_ospiti` mode = OFF
5. [ ] Verify `climate.pid_radiant_bagno_padronale` mode = OFF
6. [ ] Verify other radiant zones can enter COOL mode

### Season Classification Accuracy
- [ ] During Oct 15 - Apr 14: Classification = "Winter Lock"
- [ ] During Apr 15 - May 31: Classification = "Spring Shoulder"
- [ ] During Jun 1 - Aug 31: Classification = "Summer Lock"
- [ ] During Sep 1 - Oct 14: Classification = "Autumn Shoulder"

---

## Edge Cases & Stress Tests

### Rapid Mode Changes
1. [ ] Rapidly switch between HEAT/COOL/SANITARY_ONLY manually
2. [ ] Verify all PIDs follow mode changes
3. [ ] Verify no crashes or hangs
4. [ ] Check ESPHome logs for errors

### Multiple Simultaneous PID Demands
1. [ ] Trigger heating demand in 5+ zones simultaneously
2. [ ] Verify `any_pid_requesting_heat` turns ON
3. [ ] Verify mode transitions correctly
4. [ ] Trigger cooling demand in 5+ zones simultaneously
5. [ ] Verify `any_pid_requesting_cool` turns ON

### Conflicting Demands (Same Time)
1. [ ] Have some rooms requesting heat, others requesting cool
2. [ ] Verify system handles gracefully
3. [ ] Verify mode switches based on first detected demand

### Calendar Boundary Transitions
**Critical Dates to Test:**
- [ ] Oct 14 23:59 → Oct 15 00:01 (Enter Winter Lock)
- [ ] Apr 14 23:59 → Apr 15 00:01 (Enter Spring Shoulder)
- [ ] May 31 23:59 → Jun 1 00:01 (Enter Summer Lock)
- [ ] Aug 31 23:59 → Sep 1 00:01 (Enter Autumn Shoulder)

### System Reboot During Shoulder Season
1. [ ] During shoulder season, set mode = HEAT via demand
2. [ ] Reboot ESP32
3. [ ] Verify mode persists as HEAT after reboot
4. [ ] Verify reason persists correctly

### Home Assistant Unavailable
1. [ ] Disconnect Home Assistant
2. [ ] Verify seasonal mode continues operating in ESPHome
3. [ ] Trigger PID demands locally
4. [ ] Verify mode transitions work without HA
5. [ ] Reconnect HA and verify sync

---

## Validation Commands

```bash
# Compile
esphome compile devices/climate-control.yaml

# Upload (when ready)
esphome upload devices/climate-control.yaml

# View logs
esphome logs devices/climate-control.yaml

# Search for seasonal mode log messages
esphome logs devices/climate-control.yaml | grep "seasonal_mode"
```

---

## Expected Log Messages

When system is working correctly, you should see:

```
[seasonal_mode] Winter Lock: HEAT
[seasonal_mode] Summer Lock: COOL
[seasonal_mode] Demand Transition: HEAT
[seasonal_mode] Demand Transition: COOL
```

---

## Success Metrics

### Epic 17 Goals
- [ ] **Manual interventions:** 0 per year (fully automated)
- [ ] **Mode transition accuracy:** >95% appropriate for conditions
- [ ] **Calendar lock compliance:** 100% (correct mode during core seasons)
- [ ] **System availability:** 100% (no automation failures)

### MVP Completion Checklist
- [ ] Story 17.1: HP Mode State Management ✅
- [ ] Story 17.2: Calendar Gate Logic ✅
- [ ] Story 17.3: PID Demand Aggregation ✅
- [ ] Story 17.4: Demand-Driven Transitions ✅
- [ ] Story 17.5: Dashboard & Diagnostics ✅

---

## Known Limitations (Phase 2 Features Not Yet Implemented)

- [ ] Weather forecast integration (Story 17.6)
- [ ] Override detection & logging (Story 17.7)

These features are planned for Phase 2 and will add weather intelligence to shoulder season mode selection.

---

## Sign-off

- [ ] All calendar gates tested at boundary dates
- [ ] All PID demand aggregation scenarios tested
- [ ] All demand-driven transitions tested
- [ ] All dashboard entities visible and functional
- [ ] Manual override tested
- [ ] State persistence verified
- [ ] Heat-only zones properly disabled during cooling
- [ ] No regressions in existing functionality
- [ ] ESPHome logs show correct seasonal mode messages

**Tested by:** ________________
**Date:** ________________
**Epic 17 MVP Status:** COMPLETE ✅
