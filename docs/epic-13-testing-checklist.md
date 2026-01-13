# Epic 13: Ground Floor Hybrid Cooling - Testing Checklist

**Date:** December 26, 2025  
**Epic:** 13 - Ground Floor Hybrid Radiant-Fancoil Cooling  
**Device:** climate-control.yaml (KC868-A16 Distribution Board)

---

## Pre-Deployment Verification

### Compilation & Resource Usage
- [x] `esphome config` passes without errors
- [x] `esphome compile` succeeds
- [x] Flash usage: 16.1% (well under 80% limit)
- [x] RAM usage: 15.1% (reasonable for ESP32-S3)

### Component Inventory
- [x] 3 rooms migrated to dual-mode radiant (Soggiorno, Cucina, Anticamera)
- [x] 1 room remains heat-only (Bagno - by design)
- [x] Dew point sensors for 3 rooms
- [x] Max dew point aggregation sensor
- [x] HA-configurable boost threshold
- [x] Fancoil boost coordinator
- [x] Diagnostic sensors (8 total)
- [x] PID autotune buttons (4 total)

---

## Functional Tests

### Test 1: Normal Mode Operation
**Conditions:** summer_mode = true, delta < threshold

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Radiant PIDs mode | COOL | | |
| Radiant PIDs action | COOLING (when demand exists) | | |
| Fancoil PIDs mode | OFF | | |
| Mixing pump (relay_1) | ON when any zone active | | |
| Fancoil pump (relay_2) | OFF | | |
| `ground_floor_cooling_mode` | "Radiant Only" | | |
| `fancoil_boost_active` | false | | |

### Test 2: Boost Mode Activation
**Conditions:** summer_mode = true, delta > threshold (4.0°C default)

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| `ground_floor_max_delta` | > threshold | | |
| `ground_floor_cooling_mode` | "Fancoil Boost" | | |
| `fancoil_boost_active` | true | | |
| Radiant slow_pwm levels | 100% (1.0) | | |
| Fancoil PIDs mode | COOL | | |
| Fancoil pump (relay_2) | ON | | |

### Test 3: Boost Mode Deactivation
**Conditions:** delta < hysteresis (threshold/2 = 2.0°C), min time elapsed

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| `ground_floor_max_delta` | < hysteresis | | |
| `ground_floor_time_in_current_mode` | > 10 min | | |
| `ground_floor_cooling_mode` | "Radiant Only" | | |
| Fancoil PIDs mode | OFF | | |
| Radiant PIDs | Resume PID control | | |

### Test 4: Hysteresis Validation
**Purpose:** Verify no rapid cycling

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Delta between hysteresis and threshold | Mode unchanged | | |
| Mode change before 10 min elapsed | Mode unchanged | | |
| Multiple cycles in 1 hour | 0 (stable) | | |

---

## Safety Tests

### Test 5: Dew Point Protection
**Conditions:** Increase humidity in monitored room

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| `ground_floor_max_dew_point` | Increases with humidity | | |
| `ground_floor_supply_temp_minimum` | dew_point + 1.0°C | | |
| Mixing valve target | ≥ supply_temp_minimum | | |
| Supply temp (measured) | Never below minimum | | |

### Test 6: Threshold Fallback
**Conditions:** HA input_number unavailable

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| `effective_fancoil_boost_threshold` | 4.0°C (fallback) | | |
| Log message | "HA unavailable, using fallback" | | |
| System operation | Continues normally | | |

---

## Autonomy Tests

### Test 7: HA Unavailability (5 minutes)
**Procedure:** Stop Home Assistant for 5 minutes

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| System crashes | No | | |
| Cooling continues | Yes | | |
| Fallback threshold used | Yes | | |
| HA reconnection | System resumes normal | | |

### Test 8: Boot Behavior
**Procedure:** Reboot ESPHome device

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Boots successfully | Yes | | |
| Mode restored | From stored state | | |
| No unsafe transients | Yes | | |
| Sensors initialize | Within 30s | | |

---

## Season Transition Tests

### Test 9: Summer → Winter Transition
**Procedure:** Set summer_mode = false

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Boost mode deactivates | Yes (if active) | | |
| Radiant PIDs mode | HEAT | | |
| Fancoil PIDs mode | OFF | | |
| Dew point protection | Inactive (not cooling) | | |

### Test 10: Winter → Summer Transition
**Procedure:** Set summer_mode = true

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Radiant PIDs mode | COOL | | |
| Coordinator starts evaluating | Yes | | |
| Normal/Boost mode as needed | Based on delta | | |

---

## Edge Case Tests

### Test 11: Asymmetric Room Conditions
**Conditions:** Soggiorno delta = 5°C, Cucina delta = 1°C

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| `ground_floor_max_delta` | 5°C (from Soggiorno) | | |
| Boost activates | Yes (max > threshold) | | |
| Both rooms enter boost | Yes | | |

### Test 12: Bagno Excluded from Cooling
**Conditions:** summer_mode = true

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Bagno PID mode | HEAT (always) | | |
| Bagno in dew point aggregation | No | | |
| Bagno in delta calculation | No | | |

---

## Performance Tests

### Test 13: 24-Hour Stability
**Procedure:** Monitor for 24 hours of normal operation

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Memory usage stable | No increase | | |
| No unexpected restarts | Yes | | |
| Mode transitions logged | Yes | | |
| No oscillation | Yes | | |

### Test 14: Response Times

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Coordinator interval | 30s | | |
| Mode transition complete | < 30s | | |
| Sensor update interval | 30s | | |
| Dew point protection response | Immediate | | |

---

## Diagnostic Sensor Verification

| Sensor ID | Expected Range | Verified? |
|-----------|----------------|-----------|
| `ground_floor_cooling_mode` | "Radiant Only" / "Fancoil Boost" | |
| `fancoil_boost_active` | true / false | |
| `ground_floor_max_delta` | -5°C to +10°C | |
| `effective_fancoil_boost_threshold` | 1°C to 10°C | |
| `fancoil_boost_hysteresis` | threshold/2 | |
| `ground_floor_max_dew_point` | 5°C to 25°C | |
| `ground_floor_supply_temp_minimum` | dew_point + 1°C | |
| `ground_floor_time_in_current_mode` | 0 to 1440 min | |

---

## HA Entities to Create

Before testing, ensure these exist in Home Assistant:

1. **Binary sensor:** `binary_sensor.summer_mode` - Season indicator
2. **Input number:** `input_number.ground_floor_fancoil_boost_threshold` - Configurable threshold (1-10°C, default 4°C)

---

## Test Log

| Date | Tester | Test | Result | Notes |
|------|--------|------|--------|-------|
| | | | | |

---

## Sign-Off

- [ ] All critical tests passed
- [ ] No safety issues identified
- [ ] System ready for production use

**Tested by:** ________________  
**Date:** ________________
