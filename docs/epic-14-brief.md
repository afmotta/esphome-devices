# Epic 14: Per-Room Fancoil Boost Control

**Date:** December 26, 2025  
**Status:** Draft  
**Priority:** Medium  
**Estimated Story Points:** 8-10

---

## Executive Summary

Refactor the ground floor fancoil boost coordinator from a shared floor-wide decision to independent per-room control. Each room (Soggiorno, Cucina) will evaluate its own temperature delta against a shared threshold and independently activate its fancoil boost mode, affecting only its own radiant and fancoil systems.

---

## Problem Statement

### Current Behavior (Epic 13)
- **Shared Decision:** A single `boost_mode_active` global controls both rooms
- **Max Delta Logic:** `max(soggiorno_delta, cucina_delta)` triggers boost for BOTH rooms
- **Wasted Energy:** If only Soggiorno is hot, Cucina's fancoil also activates unnecessarily
- **All-or-Nothing Radiant:** ALL radiant zones go to 100% when ANY room triggers boost

### Desired Behavior (Epic 14)
- **Independent Decisions:** Each room evaluates its own delta independently
- **Per-Room Activation:** Only the room that exceeds threshold enters boost mode
- **Targeted Response:** Only the triggering room's radiant goes to 100% and fancoil activates
- **Energy Efficiency:** Unused fancoils remain OFF, radiant PIDs continue normal control

---

## User Stories

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| 14.1 | Per-Room Delta Sensors | 1 | High |
| 14.2 | Per-Room Boost Globals and State | 2 | High |
| 14.3 | Independent Room Boost Coordinator | 3 | High |
| 14.4 | Per-Room Diagnostic Sensors | 1 | Medium |
| 14.5 | Integration Testing | 2 | High |

---

## Architecture

### Before (Epic 13)
```
┌────────────────────────────────────────────────────────────┐
│              Shared Coordinator (30s interval)             │
├────────────────────────────────────────────────────────────┤
│  max_delta = max(soggiorno_delta, cucina_delta)            │
│                        ↓                                   │
│  if (max_delta > threshold) → boost_mode_active = true     │
│                        ↓                                   │
│  ALL radiant to 100% + ALL fancoils to COOL                │
└────────────────────────────────────────────────────────────┘
```

### After (Epic 14)
```
┌─────────────────────────────┐    ┌─────────────────────────────┐
│   Soggiorno Coordinator     │    │     Cucina Coordinator      │
├─────────────────────────────┤    ├─────────────────────────────┤
│ soggiorno_delta             │    │ cucina_delta                │
│         ↓                   │    │         ↓                   │
│ if (delta > threshold)      │    │ if (delta > threshold)      │
│         ↓                   │    │         ↓                   │
│ soggiorno_boost_active=true │    │ cucina_boost_active=true    │
│         ↓                   │    │         ↓                   │
│ slow_pwm_soggiorno = 100%   │    │ slow_pwm_cucina = 100%      │
│ pid_fancoil_soggiorno=COOL  │    │ pid_fancoil_cucina=COOL     │
└─────────────────────────────┘    └─────────────────────────────┘
        (independent)                      (independent)
```

---

## Technical Design

### Shared Components (Unchanged)
- `effective_fancoil_boost_threshold` - Shared threshold from HA (4°C default)
- `fancoil_boost_hysteresis` - threshold/2 for deactivation
- `summer_mode` - Season detection from HA

### Per-Room Components (New)

| Component | Soggiorno | Cucina |
|-----------|-----------|--------|
| Delta Sensor | `soggiorno_temp_delta` | `cucina_temp_delta` |
| Boost Global | `soggiorno_boost_active` | `cucina_boost_active` |
| Mode Change Time | `soggiorno_last_mode_change` | `cucina_last_mode_change` |
| Cooling Mode Text | `soggiorno_cooling_mode` | `cucina_cooling_mode` |
| Boost Active Binary | `soggiorno_fancoil_boost_active` | `cucina_fancoil_boost_active` |
| Time in Mode | `soggiorno_time_in_mode` | `cucina_time_in_mode` |

### Coordinator Logic (Per Room)

```cpp
// For each room independently:
if (!summer_mode) {
  // Winter: ensure fancoil OFF, radiant PID controls
  if (room_boost_active) {
    room_boost_active = false;
    fancoil.set_mode("OFF");
  }
  return;
}

// Summer: evaluate boost need
float delta = room_temp - room_target;
float threshold = effective_fancoil_boost_threshold;
float hysteresis = threshold / 2.0;

// Check min time-in-state (10 min)
if (time_since_last_change < 10min) return;

// Activation: delta > threshold
if (!room_boost_active && delta > threshold) {
  room_boost_active = true;
  slow_pwm_room.set_level(1.0);  // Only THIS room's radiant
  fancoil_room.set_mode("COOL"); // Only THIS room's fancoil
}

// Deactivation: delta < hysteresis
if (room_boost_active && delta < hysteresis) {
  room_boost_active = false;
  fancoil_room.set_mode("OFF");
  // Radiant PID resumes control automatically
}
```

---

## Component Changes

### Files to Modify

| File | Change |
|------|--------|
| `components/fancoil_boost_coordinator.yaml` | Refactor to per-room logic |
| `components/rooms/ground_floor/ground-floor.yaml` | Update aggregation sensors |

### Files to Create

| File | Purpose |
|------|---------|
| (none - inline in coordinator) | All logic stays in coordinator |

### Sensors to Deprecate

| Sensor | Replacement |
|--------|-------------|
| `ground_floor_max_delta` | `soggiorno_temp_delta` + `cucina_temp_delta` |
| `ground_floor_cooling_mode` | `soggiorno_cooling_mode` + `cucina_cooling_mode` |
| `fancoil_boost_active` | `soggiorno_fancoil_boost_active` + `cucina_fancoil_boost_active` |
| `ground_floor_time_in_current_mode` | `soggiorno_time_in_mode` + `cucina_time_in_mode` |

---

## Acceptance Criteria

### Functional
1. [ ] Soggiorno boost activates only when soggiorno_delta > threshold
2. [ ] Cucina boost activates only when cucina_delta > threshold
3. [ ] When Soggiorno enters boost, only slow_pwm_soggiorno goes to 100%
4. [ ] When Soggiorno enters boost, only pid_fancoil_soggiorno activates
5. [ ] Cucina remains in radiant-only mode while Soggiorno is in boost (and vice versa)
6. [ ] Each room has independent 10-minute minimum time-in-state

### Energy Efficiency
7. [ ] If only one room is hot, only that room's fancoil runs
8. [ ] Radiant zones not in boost continue PID control
9. [ ] Fancoil pump (relay_2) activates when ANY room is in boost

### Diagnostics
10. [ ] Per-room cooling mode visible in HA
11. [ ] Per-room boost status visible in HA
12. [ ] Per-room delta visible in HA

### Safety
13. [ ] Dew point protection unchanged (floor-wide)
14. [ ] Winter mode handling correct for both rooms
15. [ ] HA unavailability uses fallback threshold

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Epic 13 Complete | ✅ | Base hybrid cooling implementation |
| `radiant.yaml` | ✅ | Per-room radiant control |
| `fancoil.yaml` | ✅ | Per-room fancoil control |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Race conditions between rooms | Low | Low | Independent state machines |
| Increased complexity | Medium | Low | Clear per-room naming convention |
| More sensors in HA | Low | Low | Logical grouping in dashboard |

---

## Testing Strategy

1. **Scenario A:** Soggiorno hot (delta=5°C), Cucina cool (delta=1°C)
   - Expected: Only Soggiorno enters boost
   
2. **Scenario B:** Both rooms hot (delta=5°C each)
   - Expected: Both rooms enter boost independently
   
3. **Scenario C:** Soggiorno cools down while Cucina stays hot
   - Expected: Soggiorno exits boost, Cucina remains in boost
   
4. **Scenario D:** Winter mode transition
   - Expected: Both rooms exit boost, fancoils OFF

---

## Success Metrics

- **Energy Savings:** Reduced fancoil runtime when only one room needs boost
- **Comfort:** Each room reaches setpoint independently
- **Observability:** Clear per-room status in HA dashboard

---

## Out of Scope

- Per-room threshold configuration (uses shared threshold)
- Locale Tecnico fancoil integration (no radiant, standalone)
- First floor extension (future epic)

---

## Notes

- This is a refactoring epic - no new hardware or HA entities required
- Shared threshold simplifies configuration while allowing independent evaluation
- Fancoil pump relay logic needs update: ON when `soggiorno_boost OR cucina_boost`
