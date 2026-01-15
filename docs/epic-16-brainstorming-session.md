# Brainstorming Session: First Floor MEV Logic

**Date:** January 14, 2026  
**Facilitator:** Mary (Business Analyst)  
**Participants:** Alberto (System Owner)  
**Duration:** ~45 minutes

---

## Session Objective

Define intelligent control logic for the First Floor MEV (Mechanical Extract Ventilation) system, including:
- Primary control triggers
- Humidity management strategy
- Air quality response
- Cooling integration with Heat Pump

---

## Context Summary

### Existing Infrastructure (Epic 6)
- MEV board exposes 6 entities:
  - `switch.first_floor_mev_power` - Main power
  - `switch.first_floor_mev_mode` - Winter/Summer mode
  - `switch.first_floor_mev_dehumidifier` - Built-in dehumidifier
  - `switch.first_floor_mev_cooling` - Cooling integration relay
  - `number.first_floor_mev_fan_speed` - 0-100% via 0-10V DAC
  - `binary_sensor.first_floor_mev_alarm` - Alarm monitoring

### Available Sensors
- 8 first floor rooms with temperature + humidity via room sensors
- CO₂ (SCD40) and VOC/IAQ (BME688) on each room sensor ESP32
- Dew point calculations per room
- Summer mode binary sensor

### Key Discovery During Session
The cooling integration relay controls a **circulation pump** that draws chilled water from the Heat Pump buffer to the MEV's cooling coil. This is a dehumidification mechanism, not just ventilation coordination.

---

## Decision Areas Explored

### Area 1: Primary Control Trigger

**Options Presented:**
1. Humidity-First
2. Air Quality-First
3. Multi-Signal Fusion ✅ **SELECTED**
4. Schedule-Based + Override
5. Room-Specific Priority

**Decision:** Combine Humidity + CO₂ + VOC using "max demand wins" fusion.

**Rationale:** 
- Humidity drives moisture events (showers, cooking)
- CO₂ drives occupancy response
- VOC drives air quality (cooking odors, cleaning products)
- Max demand ensures never under-ventilating

---

### Area 2: Humidity Management

**Key Insight:** MEV has THREE humidity control mechanisms:

| Mechanism           | Control        | Energy Cost |
| ------------------- | -------------- | ----------- |
| Fan Speed           | DAC output     | Low         |
| Dehumidifier        | Relay 3        | Medium      |
| Cooling Integration | Relay 4 (pump) | High        |

**Decision:** Implement 4-stage humidity cascade with escalating responses.

**Cascade Design:**

| Stage      | Trigger        | Actions                           |
| ---------- | -------------- | --------------------------------- |
| 0 Normal   | <55%           | Fan at AQ demand only             |
| 1 Elevated | ≥55% for 5min  | Fan boost +20%                    |
| 2 High     | ≥65% for 10min | Fan 70%+ + Dehumidifier ON        |
| 3 Critical | ≥75% for 10min | Fan 90%+ + Dehumid + Cooling Pump |

---

### Area 3: Air Quality Thresholds

**CO₂ Mapping:**

| Level     | ppm       | Fan Demand |
| --------- | --------- | ---------- |
| Excellent | <600      | 20%        |
| Good      | 600-800   | 35%        |
| Moderate  | 800-1000  | 50%        |
| Poor      | 1000-1400 | 70%        |
| Bad       | >1400     | 90%        |

**IAQ/VOC Mapping:**

| Level      | Index   | Fan Demand |
| ---------- | ------- | ---------- |
| Clean      | <100    | 20%        |
| Acceptable | 100-150 | 35%        |
| Elevated   | 150-250 | 50%        |
| High       | 250-350 | 70%        |
| Polluted   | >350    | 90%        |

---

### Area 4: Cooling Integration

**Clarifications from Alberto:**
- Relay directly controls circulation pump (dry contact closure)
- Pump draws chilled water from HP buffer to MEV cooling coil
- No additional HP control needed—self-contained system

**Prerequisites Decided:**
- Only activate when Summer Mode = ON
- Assume cold water always available in summer

**Pump Protection:**
- Minimum ON time: 5 minutes
- Minimum OFF time: 10 minutes
- Prevents short-cycling that damages pump

---

### Area 5: Humidity Scope

**Question:** Which rooms should feed humidity cascade?

**Options:**
- A: Wet rooms only (3 bathrooms + laundry)
- B: All 8 first floor rooms ✅ **SELECTED**

**Rationale:** Bedroom humidity impacts radiant cooling effectiveness. High bedroom humidity can reduce cooling capacity, so MEV should respond to all rooms.

---

### Area 6: Implementation Pattern

**Decision:** Follow Epic 5/6 pattern—ESPHome exposes controls, Home Assistant orchestrates logic.

**Rationale:**
- Consistent with existing architecture
- HA provides flexible automation editing
- State machines easier to implement in HA
- Dashboard integration built-in

---

## Implementation Gap Identified

**Current state:** CO₂ and VOC/IAQ sensors exist on room sensor ESP32s but are NOT broadcast via UDP to the climate-control board.

**Required infrastructure (Epic 15):**
1. Modify `s1-pro-multi-sense.yaml` to broadcast CO₂ and IAQ
2. Add packet_transport receivers in climate-control.yaml
3. Create floor-wide aggregation sensors

This is a **prerequisite** for Epic 16.

---

## Final Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     MEV CONTROL LOGIC                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  PATH A: AIR QUALITY                                               │
│  ├── Inputs: first_floor_max_co2, first_floor_max_iaq             │
│  ├── Output: Fan Speed Demand (20-90%)                            │
│  └── Mode: Always active                                           │
│                                                                    │
│  PATH B: HUMIDITY CASCADE                                          │
│  ├── Input: first_floor_max_humidity                              │
│  ├── Stages: Normal → Elevated → High → Critical                  │
│  ├── Equipment: Dehumidifier (Stage 2+), Cooling (Stage 3)        │
│  └── Pump Protection: 5min ON / 10min OFF minimum                 │
│                                                                    │
│  FUSION: Fan Speed = max(Path A demand, Path B stage demand)      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

> **UPDATE (January 15, 2026):** The humidity management approach was significantly refined after this session. See "Refinement Session" section below.

---

## Resulting Epics

| Epic   | Title                               | Points | Dependency |
| ------ | ----------------------------------- | ------ | ---------- |
| **15** | Air Quality Sensor Broadcasting     | 5      | None       |
| **16** | First Floor MEV Intelligent Control | 16     | Epic 15    |

---

## Refinement Session (January 15, 2026)

After reviewing the initial stories, the humidity management approach was deemed "too naïve" and refined to use **trend-based escalation** instead of **threshold-based stages**.

### Problem with Original Approach
- Fixed thresholds (55%, 65%, 75%) were reactive, not proactive
- No configurable target for users
- Step-wise fan speed changes instead of continuous modulation
- Equipment triggered by absolute values, not by "rate of failure to control"

### Refined Approach: Trend-Based Control

Inspired by the **fancoil boost predictive mode** (Epic 14), the humidity control now:

1. **Monitors rate of change** (%/min) over a 5-minute rolling window
2. **Keeps humidity below a configurable target** (default 55%, range 40-60%)
3. **Modulates fan speed continuously** via 0-10V DAC proportional to rate + distance
4. **Escalates equipment based on rate persistence**, not absolute humidity

### New State Machine

| State             | Entry Condition                  | Exit Condition           | Actions                 |
| ----------------- | -------------------------------- | ------------------------ | ----------------------- |
| **NORMAL**        | humidity < target-5% OR rate ≤ 0 | —                        | Fan = max(AQ, 20%)      |
| **CONTROLLING**   | rate > 0, approaching target     | rate ≤ 0 for 5min        | Fan = f(rate, distance) |
| **DEHUMIDIFYING** | rate > 1%/min for 2min           | rate ≤ 0.5%/min for 5min | Fan + Dehumidifier      |
| **COOLING**       | rate > 2%/min for 2min           | rate ≤ 1%/min for 5min   | Fan + Dehumid + Pump    |

### Key Insight
The goal is not to react when humidity gets high, but to **actively prevent humidity from exceeding the target** with the minimum necessary energy expenditure.

---

## Open Questions for Future

1. **Night mode:** Should air quality override quiet mode if CO₂ >1200ppm?
2. **Seasonal thresholds:** Should humidity cascade adjust for summer vs winter?
3. **Radiant cooling coordination:** Reduce MEV extraction when radiant cooling active?
4. **Occupancy integration:** Reduce ventilation when house unoccupied?

These were noted but deferred to avoid scope creep.

---

## Session Techniques Used

- **Structured Options Presentation:** Each decision area presented with numbered alternatives
- **Probing Questions:** Clarified cooling integration mechanism
- **Constraint Identification:** Discovered pump protection need
- **Gap Analysis:** Identified missing CO₂/VOC broadcast infrastructure
- **Architecture Diagramming:** Visual representation of dual-path logic
- **Pattern Matching:** Referenced Epic 14 predictive boost for humidity control refinement

---

## Artifacts Produced

1. `docs/epic-15-brief.md` - Air Quality Sensor Broadcasting
2. `docs/epic-16-brief.md` - First Floor MEV Intelligent Control (updated Jan 15)
3. `docs/epic-16-brainstorming-session.md` - This document

---

## Next Steps

1. Review Epic 15 brief
2. Review Epic 16 brief (updated with trend-based humidity control)
3. Prioritize in backlog
4. Begin implementation (Epic 15 first as prerequisite)
