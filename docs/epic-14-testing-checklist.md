# Epic 14 Testing Checklist: Per-Room Fancoil Boost Control

**Date:** December 26, 2025  
**Device:** climate-control (KC868-A16)

---

## Pre-Deployment Validation

### Compilation
- [x] `esphome compile locals/climate-control.yaml` succeeds
- [x] No errors related to global references
- [x] Flash usage: 16.1%, RAM usage: 15.1%

### Code Review
- [x] Per-room delta sensors created (`soggiorno_temp_delta`, `cucina_temp_delta`)
- [x] Per-room boost globals created (`soggiorno_boost_active`, `cucina_boost_active`)
- [x] Per-room timing globals created (`soggiorno_last_mode_change_time`, `cucina_last_mode_change_time`)
- [x] Zone demand aggregation updated to use per-room globals
- [x] Coordinator interval uses independent per-room evaluation

---

## Test Scenarios

### Scenario 1: Soggiorno Boost Only
**Condition:** Soggiorno delta > threshold, Cucina delta < threshold

Expected behavior:
- [ ] `soggiorno_boost_active` = true
- [ ] `cucina_boost_active` = false
- [ ] `slow_pwm_soggiorno` at 100%
- [ ] `pid_fancoil_soggiorno` in COOL mode
- [ ] `pid_fancoil_cucina` remains OFF
- [ ] `soggiorno_cooling_mode` shows "Fancoil Boost"
- [ ] `cucina_cooling_mode` shows "Radiant Only"

### Scenario 2: Cucina Boost Only
**Condition:** Cucina delta > threshold, Soggiorno delta < threshold

Expected behavior:
- [ ] `soggiorno_boost_active` = false
- [ ] `cucina_boost_active` = true
- [ ] `slow_pwm_cucina` at 100%
- [ ] `pid_fancoil_cucina` in COOL mode
- [ ] `pid_fancoil_soggiorno` remains OFF
- [ ] `cucina_cooling_mode` shows "Fancoil Boost"
- [ ] `soggiorno_cooling_mode` shows "Radiant Only"

### Scenario 3: Both Rooms Boost
**Condition:** Both rooms delta > threshold

Expected behavior:
- [ ] `soggiorno_boost_active` = true
- [ ] `cucina_boost_active` = true
- [ ] Both `slow_pwm` at 100%
- [ ] Both fancoil PIDs in COOL mode
- [ ] `ground_floor_cooling_mode` shows "Fancoil Boost"

### Scenario 4: Independent Timing
**Condition:** Soggiorno enters boost, wait 5 minutes, Cucina enters boost

Expected behavior:
- [ ] Soggiorno timing independent from Cucina
- [ ] `soggiorno_time_in_mode` shows ~5 min when Cucina enters
- [ ] `cucina_time_in_mode` shows 0 when it first enters
- [ ] Each room respects 10-minute minimum independently

### Scenario 5: Asymmetric Exit
**Condition:** Both rooms in boost, Soggiorno exits (delta < hysteresis), Cucina stays

Expected behavior:
- [ ] `soggiorno_boost_active` = false
- [ ] `cucina_boost_active` = true (stays)
- [ ] `pid_fancoil_soggiorno` OFF
- [ ] `pid_fancoil_cucina` remains COOL
- [ ] `ground_floor_fancoil_any_zone_open` = true (Cucina still active)

---

## Home Assistant Entities

### Binary Sensors
- [ ] `binary_sensor.fancoil_boost_active` (any room boost)
- [ ] `binary_sensor.soggiorno_boost_active_sensor`
- [ ] `binary_sensor.cucina_boost_active_sensor`

### Text Sensors
- [ ] `text_sensor.ground_floor_cooling_mode`
- [ ] `text_sensor.soggiorno_cooling_mode`
- [ ] `text_sensor.cucina_cooling_mode`

### Sensors
- [ ] `sensor.soggiorno_temp_delta`
- [ ] `sensor.cucina_temp_delta`
- [ ] `sensor.ground_floor_max_delta`
- [ ] `sensor.soggiorno_time_in_mode`
- [ ] `sensor.cucina_time_in_mode`
- [ ] `sensor.ground_floor_time_in_current_mode`

---

## Validation Commands

```bash
# Compile
esphome compile locals/climate-control.yaml

# Upload (when ready)
esphome upload locals/climate-control.yaml

# View logs
esphome logs locals/climate-control.yaml
```

---

## Sign-off

- [ ] All scenarios tested
- [ ] All HA entities verified
- [ ] No regressions in existing functionality
- [ ] Energy savings observable (rooms boost independently)

**Tested by:** ________________  
**Date:** ________________
