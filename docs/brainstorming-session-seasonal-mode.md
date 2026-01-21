# Brainstorming Session Results: Three-Tier Seasonal Mode Selection

## Executive Summary

This session explored alternatives to the current binary `summer_mode` switch for heat pump mode control. The outcome is a **Three-Tier Seasonal Mode Selection** model that combines calendar-based gates, weather intelligence, and demand-driven transitions for robust, automated seasonal operation.

**Key Innovation:** The system eliminates manual seasonal switching by using PID demand as the trigger for mode transitions, with calendar and forecast providing contextual awareness rather than hard constraints.

---

## Problem Statement

The current `summer_mode` binary switch requires manual intervention to toggle between heating and cooling seasons. This is:
- Error-prone (forgetting to switch)
- Inflexible (doesn't handle shoulder seasons well)
- Reactive (switches after discomfort occurs)

---

## Recommended Solution: Three-Tier Model

### Tier 1: Calendar Gate (Hard Locks)

| Period              | Behavior         | Rationale                                     |
| ------------------- | ---------------- | --------------------------------------------- |
| **Oct 15 - Apr 15** | HEAT mode locked | Core winter; PIDs handle warm days internally |
| **Apr 16 - May 31** | Evaluate         | Spring shoulder season                        |
| **Jun 1 - Aug 31**  | COOL mode locked | Core summer; full humidity logic active       |
| **Sep 1 - Oct 14**  | Evaluate         | Autumn shoulder season                        |

### Tier 2: Weather Intelligence (24h Forecast)

Applies only during **Evaluate** periods (shoulder seasons):

| Forecast High | Guidance              |
| ------------- | --------------------- |
| ≥ 26°C        | Cooling likely needed |
| ≤ 14°C        | Heating likely needed |
| 15-25°C       | Dead band (coast)     |

**MVP Implementation:** Temperature forecast only (via HA weather integration)

**Future Iterations:**
- Humidity forecast (dehumidifier decisions)
- Cloud cover (solar gain prediction)

### Tier 3: Demand-Driven Transitions

Applies only during **Evaluate** periods (shoulder seasons):

**Critical Design Decision:** Demand always wins.

- Mode transitions occur **only when a PID requests** heating or cooling
- No automatic return to SANITARY_ONLY (stays in mode until opposite requested)
- Forecast gates are soft guidance, not hard constraints
- Dead band override: If a PID requests heat/cool, honor it regardless of forecast

---

## State Machine

```
                         WINTER (Oct 15 - Apr 15)
                    ┌─────────────────────────────┐
                    │      HEAT (locked)          │
                    │  Calendar hard lock         │
                    └─────────────────────────────┘

                         SUMMER (Jun 1 - Aug 31)
                    ┌─────────────────────────────┐
                    │      COOL (locked)          │
                    │  Calendar hard lock         │
                    │  Full humidity logic active │
                    └─────────────────────────────┘
                    
              SHOULDER SEASONS (Apr 16 - May 31, Sep 1 - Oct 14)
    ┌────────────────────────────────────────────────┐
    │                                                │
    │              SANITARY_ONLY                     │
    │         (initial/neutral state)                │
    │      Buffer untouched, DHW only                │
    │                                                │
    └──────────┬──────────────────────┬──────────────┘
               │                      │
    Any PID requests HEAT             │    Any PID requests COOL
    (demand override)                 │    (demand override)
               │                      │
               ▼                      ▼
    ┌────────────────────┐  ┌────────────────────┐
    │       HEAT         │  │       COOL         │
    │   (buffer hot)     │  │   (buffer cold)    │
    │                    │  │                    │
    │  Stays until COOL  │  │  Stays until HEAT  │
    │  is requested      │  │  is requested      │
    └────────────────────┘  └────────────────────┘
               │                      │
               └──────────────────────┘
                    Direct transitions
                   (no SANITARY_ONLY stop)
```

---

## Configuration Entities (ESPHome)

### Selects
| Entity                       | Options                       | Purpose                        |
| ---------------------------- | ----------------------------- | ------------------------------ |
| `select.hp_mode`             | HEAT, COOL, SANITARY_ONLY     | Current operating mode (Brain) |
| `text_sensor.hp_mode_reason` | CALENDAR_LOCK, DEMAND, MANUAL | Why current mode was selected  |

### Sensors (Diagnostic)
| Entity                                  | Purpose                          |
| --------------------------------------- | -------------------------------- |
| `sensor.hp_forecast_guidance`           | What forecast suggests (from HA) |
| `binary_sensor.any_pid_requesting_heat` | Global heat demand aggregation   |
| `binary_sensor.any_pid_requesting_cool` | Global cool demand aggregation   |

---

## ESPHome Implementation (Tier 1 & 3)

The logic is moved from Home Assistant to ESPHome for autonomy. The coordinator runs on the `climate-control` device.

```yaml
# Winter Lock (Oct 15 - Apr 15)
- if: Oct 15 <= date < Apr 15
  then: set hp_mode to HEAT, set hp_mode_reason to CALENDAR_LOCK

# Demand-Driven (Shoulder Seasons Only)
- if: any_pid_requesting_heat == ON and in_shoulder_season
  then: set hp_mode to HEAT, set hp_mode_reason to DEMAND
```

---

## Automation Logic (Pseudocode)

```yaml
# Winter Lock (Oct 15 - Apr 15)
- trigger: date is Oct 15
  action: set hp_mode to HEAT, set hp_mode_reason to CALENDAR_LOCK

# Summer Lock (Jun 1 - Aug 31)
- trigger: date is Jun 1
  action: set hp_mode to COOL, set hp_mode_reason to CALENDAR_LOCK

# Exit Winter Lock → Spring Shoulder (Apr 15)
- trigger: date is Apr 15
  action: set hp_mode to SANITARY_ONLY, set hp_mode_reason to CALENDAR_LOCK

# Exit Summer Lock → Autumn Shoulder (Sep 1)
- trigger: date is Sep 1
  action: set hp_mode to SANITARY_ONLY, set hp_mode_reason to CALENDAR_LOCK

# Demand-Driven: Any PID Requests Heat (Shoulder Seasons Only)
- trigger: any PID action == HEATING
  condition: 
    - hp_mode != HEAT
    - current month in [Apr, May, Sep, Oct]  # Shoulder only
  action:
    - set hp_mode to HEAT
    - set hp_mode_reason to DEMAND
    - set override_active if forecast_guidance != HEAT

# Demand-Driven: Any PID Requests Cool (Shoulder Seasons Only)
- trigger: any PID action == COOLING
  condition:
    - hp_mode != COOL
    - current month in [Mar, Apr, May, Sep, Oct, Nov]  # Shoulder only
  action:
    - set hp_mode to COOL
    - set hp_mode_reason to DEMAND
    - set override_active if forecast_guidance != COOL
```

---

## Design Decisions Summary

| Decision           | Choice                        | Rationale                                   |
| ------------------ | ----------------------------- | ------------------------------------------- |
| Winter behavior    | Hard lock to HEAT (Dec-Feb)   | PIDs handle warm days via reduced output    |
| Summer behavior    | Hard lock to COOL (Jun-Aug)   | Milan summers always need cooling available |
| Shoulder behavior  | Evaluate with demand override | Maximum flexibility                         |
| Cooling threshold  | 26°C                          | Milan climate - warm but not extreme        |
| Heating threshold  | 14°C                          | Below typical comfort range                 |
| Dead band          | SANITARY_ONLY                 | Let rooms coast naturally                   |
| Dead band override | Demand wins                   | Trust PIDs; they know room needs            |
| Mode transitions   | On PID request                | No proactive switching                      |
| Return to SANITARY | Never automatic               | Only switch when opposite mode needed       |
| Pre-conditioning   | None                          | HP is fast (minutes to condition buffer)    |
| Forecast window    | 24 hours                      | Daily planning horizon                      |

---

## Rejected Alternatives

| Alternative                  | Reason Rejected                                                   |
| ---------------------------- | ----------------------------------------------------------------- |
| Pure calendar-based          | "Too constricted" - can't handle unusual weather                  |
| Pure temperature-driven      | "Outdoor temp may be misleading" - doesn't reflect building state |
| Proactive mode switching     | Not needed - HP conditions buffer in minutes                      |
| Automatic return to SANITARY | Creates unnecessary mode churn                                    |
| Forecast as hard gate        | Too rigid - demand should override when needed                    |
| Summer as "evaluate"         | Milan summers reliably need cooling; no benefit to evaluate       |

---

## Implementation Phases

### Phase 1: Core Logic (MVP)
- Calendar gate implementation (hard locks for winter/summer)
- Demand-driven transitions for shoulder seasons
- Basic `hp_mode` input_select
- Automations for mode switching

### Phase 2: Weather Intelligence
- Integrate HA weather forecast
- Add `hp_forecast_guidance` sensor
- Add `hp_mode_override_active` indicator
- Dashboard showing forecast vs actual mode

### Phase 3: Enhanced Diagnostics
- Humidity forecast integration
- Mode transition logging
- Energy impact analysis
- Override frequency tracking

---

## Success Metrics

| Metric                   | Target                             |
| ------------------------ | ---------------------------------- |
| Manual interventions     | Zero (fully automated)             |
| Mode transition accuracy | >95% appropriate for conditions    |
| Comfort complaints       | None related to wrong mode         |
| Energy efficiency        | No degradation vs manual switching |

---

## Open Questions for Implementation

1. **PID action detection:** How to reliably detect "PID requests heat/cool" in HA?
   - Option A: Check `climate.*.hvac_action` attribute
   - Option B: Monitor PID output percentage
   - Option C: Check slow_pwm/relay states

2. **Multi-board coordination:** With PIDs on multiple ESPHome boards, how to aggregate demand?
   - Option A: HA automation checks all climate entities
   - Option B: UDP broadcast aggregation (Epic 10 pattern)

---

*Session Date: January 15, 2026*
*Participants: User + Mary (Business Analyst)*
