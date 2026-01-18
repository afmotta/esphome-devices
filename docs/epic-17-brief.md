# Epic 17: Three-Tier Seasonal Mode Selection

**Date:** January 15, 2026  
**Status:** Draft  
**Priority:** High  
**Estimated Story Points:** 13

---

## Executive Summary

Implement automated heat pump mode selection that eliminates manual seasonal switching by combining **calendar-based hard locks**, **weather intelligence** (Phase 2), and **demand-driven transitions**. The system uses a three-tier decision architecture: calendar gates enforce mode during core seasons (Dec-Feb → HEAT, Jun-Aug → COOL), while shoulder seasons (Mar-May, Sep-Nov) use PID demand to trigger mode transitions. Demand always wins—if a PID requests heating or cooling, the system honors it regardless of forecast guidance.

### Key Innovation

The system trusts PID controllers to know actual room needs. Mode transitions are triggered **only when a PID requests** heating or cooling, not proactively. No automatic return to SANITARY_ONLY prevents mode churn. The heat pump's fast buffer conditioning (< 5 minutes) eliminates the need for pre-conditioning.

---

## Problem Statement

### Current State
- Binary `summer_mode` switch requires manual intervention to toggle between HEAT and COOL modes
- Homeowner must track weather patterns and decide when to switch
- No automation exists for seasonal mode transitions
- Mode state impacts other systems (Epic 16 MEV cooling integration depends on mode)

### Pain Points
- **Human Error:** Forgetting to switch modes leads to discomfort (house too hot in spring because still in HEAT mode)
- **Inflexibility:** Binary switch can't handle shoulder seasons where needs vary day-to-day
- **Reactive Response:** Mode changes happen after discomfort is noticed, not proactively
- **Mental Load:** Homeowner must track weather patterns and remember to adjust settings

### Why This Matters
- **Comfort:** Wrong mode means uncomfortable temperatures
- **Energy Efficiency:** Running wrong mode wastes energy
- **System Integration:** Epic 16 MEV cooling pump depends on reliable mode state
- **Autonomy:** True "set and forget" automation requires eliminating manual switches

---

## Proposed Solution

### Architecture: Three-Tier Decision Model

```
┌────────────────────────────────────────────────────────────────────┐
│              THREE-TIER SEASONAL MODE SELECTION                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  TIER 1: CALENDAR GATE (Hard Locks)                                │
│  ├── Dec 1 - Feb 28 → HEAT mode LOCKED                             │
│  ├── Jun 1 - Aug 31 → COOL mode LOCKED                             │
│  ├── Mar 1 - May 31 → Evaluate (shoulder)                          │
│  └── Sep 1 - Nov 30 → Evaluate (shoulder)                          │
│                                                                    │
│  TIER 2: WEATHER INTELLIGENCE (Phase 2 - Shoulder Seasons)         │
│  ├── 24h forecast high temperature                                 │
│  ├── ≥26°C → Cooling likely needed                                 │
│  ├── ≤14°C → Heating likely needed                                 │
│  └── 15-25°C → Dead band (SANITARY_ONLY guidance)                  │
│                                                                    │
│  TIER 3: DEMAND-DRIVEN TRANSITIONS (Shoulder Seasons)              │
│  ├── CRITICAL: Demand ALWAYS wins over forecast                    │
│  ├── Any PID requests HEAT → Switch to HEAT mode                   │
│  ├── Any PID requests COOL → Switch to COOL mode                   │
│  └── No automatic return to SANITARY (stays until opposite)        │
│                                                                    │
│  STATE MACHINE:                                                    │
│                                                                    │
│       WINTER (Dec-Feb)              SUMMER (Jun-Aug)               │
│    ┌─────────────────┐           ┌─────────────────┐               │
│    │  HEAT (locked)  │           │  COOL (locked)  │               │
│    └─────────────────┘           └─────────────────┘               │
│                                                                    │
│            SHOULDER SEASONS (Mar-May, Sep-Nov)                     │
│    ┌─────────────────────────────────────────────┐                 │
│    │             SANITARY_ONLY                   │                 │
│    │          (initial state)                    │                 │
│    └──────────┬─────────────────┬────────────────┘                 │
│               │                 │                                  │
│    PID HEAT   │                 │  PID COOL                        │
│    request    ▼                 ▼  request                         │
│    ┌──────────────┐   ┌──────────────┐                             │
│    │    HEAT      │◀─▶│    COOL      │                             │
│    │ (stays here) │   │ (stays here) │                             │
│    └──────────────┘   └──────────────┘                             │
│         Direct transitions (no SANITARY stop)                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision               | Choice                        | Rationale                                   |
| ---------------------- | ----------------------------- | ------------------------------------------- |
| **Winter behavior**    | Hard lock to HEAT (Dec-Feb)   | PIDs handle warm days via reduced output    |
| **Summer behavior**    | Hard lock to COOL (Jun-Aug)   | Milan summers always need cooling available |
| **Shoulder behavior**  | Evaluate with demand override | Maximum flexibility for variable weather    |
| **Cooling threshold**  | 26°C forecast (Phase 2)       | Milan climate - warm but not extreme        |
| **Heating threshold**  | 14°C forecast (Phase 2)       | Below typical comfort range                 |
| **Dead band**          | SANITARY_ONLY                 | Let rooms coast naturally                   |
| **Dead band override** | Demand wins                   | Trust PIDs; they know room needs            |
| **Mode transitions**   | On PID request                | No proactive switching                      |
| **Return to SANITARY** | Never automatic               | Only switch when opposite mode needed       |
| **Pre-conditioning**   | None                          | HP is fast (minutes to condition buffer)    |
| **Implementation**     | Home Assistant Automations    | HA orchestrates, ESPHome PIDs expose state  |

---

## User Stories

| Story | Title                          | Points | Priority | Phase   |
| ----- | ------------------------------ | ------ | -------- | ------- |
| 17.1  | HP Mode State Management       | 2      | High     | MVP     |
| 17.2  | Calendar Gate Automations      | 2      | High     | MVP     |
| 17.3  | PID Demand Detection           | 2      | High     | MVP     |
| 17.4  | Demand-Driven Mode Transitions | 3      | High     | MVP     |
| 17.5  | Dashboard & Diagnostics        | 1      | Medium   | MVP     |
| 17.6  | Weather Forecast Integration   | 2      | Medium   | Phase 2 |
| 17.7  | Override Detection & Logging   | 1      | Low      | Phase 2 |

**MVP Total: 10 Story Points**  
**Phase 2 Total: 3 Story Points**  
**Epic Total: 13 Story Points**

---

## Technical Specification

### Story 17.1: HP Mode State Management

**Description:** Create Home Assistant input helpers to track heat pump mode and the reason for the current mode selection.

**Home Assistant Helpers:**

```yaml
# ============================================================
# INPUT SELECTS - Mode State Tracking
# ============================================================

input_select:
  hp_mode:
    name: "Heat Pump Mode"
    options:
      - "HEAT"
      - "COOL"
      - "SANITARY_ONLY"
    icon: mdi:heat-pump

  hp_mode_reason:
    name: "Heat Pump Mode Reason"
    options:
      - "CALENDAR_LOCK"
      - "DEMAND"
      - "MANUAL"
    icon: mdi:information-outline
```

**Acceptance Criteria:**
- [ ] `input_select.hp_mode` created with HEAT/COOL/SANITARY_ONLY options
- [ ] `input_select.hp_mode_reason` created with CALENDAR_LOCK/DEMAND/MANUAL options
- [ ] Both entities visible in Home Assistant UI
- [ ] Initial state can be set manually

---

### Story 17.2: Calendar Gate Automations

**Description:** Implement automations that enforce hard locks during core seasons and reset to SANITARY_ONLY when entering shoulder seasons.

**Automation 1: Winter Lock (Dec 1)**
```yaml
alias: "HP Mode - Winter Lock (Dec 1)"
description: "Lock heat pump to HEAT mode for winter season"
trigger:
  - platform: time
    at: "00:01:00"
condition:
  - condition: template
    value_template: "{{ now().month == 12 and now().day == 1 }}"
action:
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode
    data:
      option: "HEAT"
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode_reason
    data:
      option: "CALENDAR_LOCK"
  - service: notify.persistent_notification
    data:
      title: "HP Mode: Winter Lock"
      message: "Heat pump locked to HEAT mode for winter season (Dec-Feb)"
mode: single
```

**Automation 2: Summer Lock (Jun 1)**
```yaml
alias: "HP Mode - Summer Lock (Jun 1)"
description: "Lock heat pump to COOL mode for summer season"
trigger:
  - platform: time
    at: "00:01:00"
condition:
  - condition: template
    value_template: "{{ now().month == 6 and now().day == 1 }}"
action:
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode
    data:
      option: "COOL"
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode_reason
    data:
      option: "CALENDAR_LOCK"
  - service: notify.persistent_notification
    data:
      title: "HP Mode: Summer Lock"
      message: "Heat pump locked to COOL mode for summer season (Jun-Aug)"
mode: single
```

**Automation 3: Spring Shoulder Entry (Mar 1)**
```yaml
alias: "HP Mode - Spring Shoulder Entry (Mar 1)"
description: "Enter shoulder season - set to SANITARY_ONLY"
trigger:
  - platform: time
    at: "00:01:00"
condition:
  - condition: template
    value_template: "{{ now().month == 3 and now().day == 1 }}"
action:
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode
    data:
      option: "SANITARY_ONLY"
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode_reason
    data:
      option: "CALENDAR_LOCK"
  - service: notify.persistent_notification
    data:
      title: "HP Mode: Spring Shoulder"
      message: "Entering spring shoulder season - mode will follow PID demand"
mode: single
```

**Automation 4: Autumn Shoulder Entry (Sep 1)**
```yaml
alias: "HP Mode - Autumn Shoulder Entry (Sep 1)"
description: "Enter shoulder season - set to SANITARY_ONLY"
trigger:
  - platform: time
    at: "00:01:00"
condition:
  - condition: template
    value_template: "{{ now().month == 9 and now().day == 1 }}"
action:
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode
    data:
      option: "SANITARY_ONLY"
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode_reason
    data:
      option: "CALENDAR_LOCK"
  - service: notify.persistent_notification
    data:
      title: "HP Mode: Autumn Shoulder"
      message: "Entering autumn shoulder season - mode will follow PID demand"
mode: single
```

**Acceptance Criteria:**
- [ ] Dec 1 automation sets mode to HEAT with CALENDAR_LOCK reason
- [ ] Jun 1 automation sets mode to COOL with CALENDAR_LOCK reason
- [ ] Mar 1 automation sets mode to SANITARY_ONLY
- [ ] Sep 1 automation sets mode to SANITARY_ONLY
- [ ] Each transition generates a persistent notification
- [ ] Automations only fire once per day (mode: single)

---

### Story 17.3: PID Demand Detection

**Description:** Create template sensors that detect when any PID is requesting heating or cooling action.

**Template Sensors:**

```yaml
template:
  - binary_sensor:
      - name: "Any PID Requesting Heat"
        unique_id: any_pid_requesting_heat
        icon: mdi:fire
        device_class: heat
        state: >
          {{
            is_state_attr('climate.pid_radiant_soggiorno', 'hvac_action', 'heating') or
            is_state_attr('climate.pid_radiant_cucina', 'hvac_action', 'heating') or
            is_state_attr('climate.pid_radiant_bagno_grande', 'hvac_action', 'heating') or
            is_state_attr('climate.pid_fancoil_camera_nord', 'hvac_action', 'heating') or
            is_state_attr('climate.pid_fancoil_camera_sud', 'hvac_action', 'heating') or
            is_state_attr('climate.pid_fancoil_camera_ospiti', 'hvac_action', 'heating') or
            is_state_attr('climate.pid_fancoil_camera_padronale', 'hvac_action', 'heating') or
            is_state_attr('climate.pid_fancoil_lavanderia', 'hvac_action', 'heating')
          }}

      - name: "Any PID Requesting Cool"
        unique_id: any_pid_requesting_cool
        icon: mdi:snowflake
        device_class: cold
        state: >
          {{
            is_state_attr('climate.pid_radiant_soggiorno', 'hvac_action', 'cooling') or
            is_state_attr('climate.pid_radiant_cucina', 'hvac_action', 'cooling') or
            is_state_attr('climate.pid_radiant_bagno_grande', 'hvac_action', 'cooling') or
            is_state_attr('climate.pid_fancoil_camera_nord', 'hvac_action', 'cooling') or
            is_state_attr('climate.pid_fancoil_camera_sud', 'hvac_action', 'cooling') or
            is_state_attr('climate.pid_fancoil_camera_ospiti', 'hvac_action', 'cooling') or
            is_state_attr('climate.pid_fancoil_camera_padronale', 'hvac_action', 'cooling') or
            is_state_attr('climate.pid_fancoil_lavanderia', 'hvac_action', 'cooling')
          }}
```

**Note:** The actual PID entity names should be verified against the ESPHome configuration. The pattern is `climate.pid_{type}_{room}`.

**Acceptance Criteria:**
- [ ] `binary_sensor.any_pid_requesting_heat` turns ON when any PID has hvac_action = heating
- [ ] `binary_sensor.any_pid_requesting_cool` turns ON when any PID has hvac_action = cooling
- [ ] Sensors update immediately when PID state changes
- [ ] All PID entities on all ESPHome boards are included

---

### Story 17.4: Demand-Driven Mode Transitions

**Description:** Implement automations that switch HP mode when PIDs request heating or cooling during shoulder seasons.

**Automation 1: Demand → HEAT**
```yaml
alias: "HP Mode - Demand Switch to HEAT"
description: "Switch to HEAT when any PID requests heating (shoulder seasons only)"
trigger:
  - platform: state
    entity_id: binary_sensor.any_pid_requesting_heat
    to: "on"
condition:
  - condition: not
    conditions:
      - condition: state
        entity_id: input_select.hp_mode
        state: "HEAT"
  - condition: template
    value_template: >
      {{ now().month in [3, 4, 5, 9, 10, 11] }}
action:
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode
    data:
      option: "HEAT"
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode_reason
    data:
      option: "DEMAND"
  - service: notify.persistent_notification
    data:
      title: "HP Mode: Demand Switch"
      message: "Switched to HEAT mode - PID requested heating"
mode: single
```

**Automation 2: Demand → COOL**
```yaml
alias: "HP Mode - Demand Switch to COOL"
description: "Switch to COOL when any PID requests cooling (shoulder seasons only)"
trigger:
  - platform: state
    entity_id: binary_sensor.any_pid_requesting_cool
    to: "on"
condition:
  - condition: not
    conditions:
      - condition: state
        entity_id: input_select.hp_mode
        state: "COOL"
  - condition: template
    value_template: >
      {{ now().month in [3, 4, 5, 9, 10, 11] }}
action:
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode
    data:
      option: "COOL"
  - service: input_select.select_option
    target:
      entity_id: input_select.hp_mode_reason
    data:
      option: "DEMAND"
  - service: notify.persistent_notification
    data:
      title: "HP Mode: Demand Switch"
      message: "Switched to COOL mode - PID requested cooling"
mode: single
```

**Key Design Points:**
- Automations only fire during shoulder months (Mar-May, Sep-Nov)
- No automation returns to SANITARY_ONLY (stays in mode until opposite requested)
- Direct HEAT↔COOL transitions are allowed (no SANITARY stop required)
- Persistent notifications provide audit trail

**Acceptance Criteria:**
- [ ] First PID heating request during shoulder season triggers HEAT mode
- [ ] First PID cooling request during shoulder season triggers COOL mode
- [ ] Automations do NOT fire during core seasons (Dec-Feb, Jun-Aug)
- [ ] Mode stays locked after demand transition (no return to SANITARY)
- [ ] Direct HEAT→COOL transition works when opposite demand occurs
- [ ] Each transition generates a persistent notification

---

### Story 17.5: Dashboard & Diagnostics

**Description:** Create a dashboard card showing current HP mode, reason, and PID demand state.

**Dashboard Card (Markdown + Entities):**

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      ## 🔥❄️ Heat Pump Mode
      
      | Property         | Value                                                                                                                                                                                         |
      | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
      | **Current Mode** | {{ states('input_select.hp_mode') }}                                                                                                                                                          |
      | **Reason**       | {{ states('input_select.hp_mode_reason') }}                                                                                                                                                   |
      | **Season**       | {% if now().month in [12, 1, 2] %}Winter (locked){% elif now().month in [6, 7, 8] %}Summer (locked){% elif now().month in [3, 4, 5] %}Spring (shoulder){% else %}Autumn (shoulder){% endif %} |
      
  - type: entities
    title: Mode Control
    entities:
      - entity: input_select.hp_mode
        name: Heat Pump Mode
      - entity: input_select.hp_mode_reason
        name: Mode Reason
      - type: divider
      - entity: binary_sensor.any_pid_requesting_heat
        name: PID Heat Demand
      - entity: binary_sensor.any_pid_requesting_cool
        name: PID Cool Demand
```

**Acceptance Criteria:**
- [ ] Dashboard shows current mode (HEAT/COOL/SANITARY_ONLY)
- [ ] Dashboard shows reason (CALENDAR_LOCK/DEMAND/MANUAL)
- [ ] Dashboard shows current season classification
- [ ] PID demand sensors visible
- [ ] Manual mode override possible via dropdown

---

### Story 17.6: Weather Forecast Integration (Phase 2)

**Description:** Add weather forecast guidance to show what the forecast suggests during shoulder seasons.

**Required Input Numbers:**
```yaml
input_number:
  hp_cooling_threshold:
    name: "HP Cooling Threshold"
    min: 20
    max: 35
    step: 1
    unit_of_measurement: "°C"
    icon: mdi:thermometer-high
    initial: 26

  hp_heating_threshold:
    name: "HP Heating Threshold"
    min: 5
    max: 20
    step: 1
    unit_of_measurement: "°C"
    icon: mdi:thermometer-low
    initial: 14
```

**Forecast Guidance Sensor:**
```yaml
template:
  - sensor:
      - name: "HP Forecast Guidance"
        unique_id: hp_forecast_guidance
        icon: mdi:weather-partly-cloudy
        state: >
          {% set forecast_high = state_attr('weather.home', 'forecast')[0].temperature | float(20) %}
          {% set cool_thresh = states('input_number.hp_cooling_threshold') | float(26) %}
          {% set heat_thresh = states('input_number.hp_heating_threshold') | float(14) %}
          
          {% if forecast_high >= cool_thresh %}
            COOL
          {% elif forecast_high <= heat_thresh %}
            HEAT
          {% else %}
            NEUTRAL
          {% endif %}
        attributes:
          forecast_high: >
            {{ state_attr('weather.home', 'forecast')[0].temperature | float(20) }}
          cooling_threshold: >
            {{ states('input_number.hp_cooling_threshold') | float(26) }}
          heating_threshold: >
            {{ states('input_number.hp_heating_threshold') | float(14) }}
```

**Acceptance Criteria:**
- [ ] Forecast guidance sensor created
- [ ] Shows HEAT/COOL/NEUTRAL based on 24h forecast
- [ ] Thresholds configurable via input_number
- [ ] Attributes expose raw values for debugging

---

### Story 17.7: Override Detection & Logging (Phase 2)

**Description:** Create a sensor that detects when demand override differs from forecast guidance, for diagnostic purposes.

**Override Detection Sensor:**
```yaml
template:
  - binary_sensor:
      - name: "HP Mode Override Active"
        unique_id: hp_mode_override_active
        icon: mdi:alert-circle
        device_class: problem
        state: >
          {% set mode = states('input_select.hp_mode') %}
          {% set reason = states('input_select.hp_mode_reason') %}
          {% set guidance = states('sensor.hp_forecast_guidance') %}
          
          {{ reason == 'DEMAND' and 
             ((mode == 'HEAT' and guidance == 'COOL') or
              (mode == 'COOL' and guidance == 'HEAT')) }}
        attributes:
          current_mode: "{{ states('input_select.hp_mode') }}"
          forecast_guidance: "{{ states('sensor.hp_forecast_guidance') }}"
          mode_reason: "{{ states('input_select.hp_mode_reason') }}"
```

**Acceptance Criteria:**
- [ ] Override sensor turns ON when demand differs from forecast
- [ ] Only active when mode_reason is DEMAND (not CALENDAR_LOCK)
- [ ] Attributes provide context for debugging

---

## Dependencies

### Prerequisites
- Home Assistant 2024.x or later
- ESPHome devices with PID climate entities exposing `hvac_action` attribute
- Weather integration configured (Phase 2)

### Related Epics
- **Epic 2:** PID architecture (provides hvac_action attribute)
- **Epic 10:** UDP zone activity (pattern for multi-board coordination)
- **Epic 16:** MEV control (depends on hp_mode for cooling pump decisions)

---

## Testing Checklist

### Story 17.1: HP Mode State Management
- [ ] Create input_select.hp_mode manually
- [ ] Create input_select.hp_mode_reason manually
- [ ] Verify both appear in HA entity list
- [ ] Verify options can be selected via UI

### Story 17.2: Calendar Gate Automations
- [ ] Test Dec 1 automation (use time trigger test or temporarily change condition)
- [ ] Test Jun 1 automation
- [ ] Test Mar 1 automation
- [ ] Test Sep 1 automation
- [ ] Verify notifications appear

### Story 17.3: PID Demand Detection
- [ ] Manually set a PID to heating mode
- [ ] Verify binary_sensor.any_pid_requesting_heat turns ON
- [ ] Manually set a PID to cooling mode
- [ ] Verify binary_sensor.any_pid_requesting_cool turns ON
- [ ] Verify sensor turns OFF when PID stops requesting

### Story 17.4: Demand-Driven Mode Transitions
- [ ] Set hp_mode to SANITARY_ONLY
- [ ] Trigger a PID heating request
- [ ] Verify mode changes to HEAT with reason DEMAND
- [ ] Trigger a PID cooling request
- [ ] Verify mode changes to COOL with reason DEMAND
- [ ] Verify automations don't fire during core season months

### Story 17.5: Dashboard & Diagnostics
- [ ] Add dashboard card to Lovelace
- [ ] Verify mode and reason display correctly
- [ ] Verify season classification is correct
- [ ] Test manual mode override via dropdown

---

## Risks & Mitigations

| Risk                        | Impact                   | Likelihood | Mitigation                                         |
| --------------------------- | ------------------------ | ---------- | -------------------------------------------------- |
| PID hvac_action unreliable  | Mode transitions delayed | Low        | Test with actual PIDs; fall back to output %       |
| Multi-board latency         | Slow demand detection    | Low        | HA state triggers are fast; consider UDP if needed |
| Manual override forgotten   | Mode stuck wrong         | Medium     | Dashboard clearly shows current mode/reason        |
| HP mode integration missing | Can't control HP         | High       | Verify existing HP integration before starting     |

---

## Success Metrics

| Metric                   | Target     | Measurement                      |
| ------------------------ | ---------- | -------------------------------- |
| Manual interventions     | 0 per year | Count manual mode changes        |
| Mode transition accuracy | >95%       | Review transitions vs conditions |
| Calendar lock compliance | 100%       | Verify mode during core seasons  |
| System availability      | 100%       | No automation failures           |

---

## Implementation Timeline

| Week | Stories    | Milestone                          |
| ---- | ---------- | ---------------------------------- |
| 1    | 17.1, 17.2 | State management + calendar gates  |
| 2    | 17.3, 17.4 | PID detection + demand transitions |
| 3    | 17.5       | Dashboard + MVP complete           |
| 4+   | 17.6, 17.7 | Phase 2 weather intelligence       |

**Target MVP Completion:** February 15, 2026 (before Mar 1 shoulder season)

---

## Appendices

### A. Source Documents

- **Brainstorming Session:** `docs/brainstorming-session-seasonal-mode.md`
- **Project Brief:** `docs/brief-seasonal-mode.md`

### B. PID Entity Discovery

To find all PID entities for Story 17.3, run in HA Developer Tools → Template:

```jinja2
{% for entity in states.climate %}
  {% if 'pid' in entity.entity_id %}
    {{ entity.entity_id }}: {{ state_attr(entity.entity_id, 'hvac_action') }}
  {% endif %}
{% endfor %}
```

### C. Rejected Alternatives

| Alternative                  | Reason Rejected                     |
| ---------------------------- | ----------------------------------- |
| Pure calendar-based          | Too constricted for unusual weather |
| Pure temperature-driven      | Outdoor temp misleading             |
| Automatic return to SANITARY | Creates mode churn                  |
| Forecast as hard gate        | Too rigid; demand should override   |
| Pre-conditioning buffer      | HP is fast enough without it        |

---

*Epic Brief Created: January 15, 2026*
*Based on: Project Brief (docs/brief-seasonal-mode.md)*
