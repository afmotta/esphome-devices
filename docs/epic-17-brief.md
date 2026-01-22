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
│  ├── Oct 15 - Apr 15 → HEAT mode LOCKED                            │
│  ├── Jun 1 - Aug 31 → COOL mode LOCKED                             │
│  ├── Apr 16 - May 31 → Evaluate (shoulder)                         │
│  └── Sep 1 - Oct 14 → Evaluate (shoulder)                          │
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
│       WINTER (Oct 15 - Apr 15)      SUMMER (Jun-Aug)               │
│    ┌─────────────────┐           ┌─────────────────┐               │
│    │  HEAT (locked)  │           │  COOL (locked)  │               │
│    └─────────────────┘           └─────────────────┘               │
│                                                                    │
│            SHOULDER SEASONS (Apr 16 - May 31, Sep 1 - Oct 14)      │
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

| Decision               | Choice                              | Rationale                                        |
| ---------------------- | ----------------------------------- | ------------------------------------------------ |
| **Winter behavior**    | Hard lock to HEAT (Oct 15 - Apr 15) | PIDs handle warm days via reduced output         |
| **Summer behavior**    | Hard lock to COOL (Jun-Aug)         | Milan summers always need cooling available      |
| **Shoulder behavior**  | Evaluate with demand override       | Maximum flexibility for variable weather         |
| **Cooling threshold**  | 26°C forecast (Phase 2)             | Milan climate - warm but not extreme             |
| **Heating threshold**  | 14°C forecast (Phase 2)             | Below typical comfort range                      |
| **Dead band**          | SANITARY_ONLY                       | Let rooms coast naturally                        |
| **Dead band override** | Demand wins                         | Trust PIDs; they know room needs                 |
| **Mode transitions**   | On PID request                      | No proactive switching                           |
| **Return to SANITARY** | Never automatic                     | Only switch when opposite mode needed            |
| **Pre-conditioning**   | None                                | HP is fast (minutes to condition buffer)         |
| **Implementation**     | ESPHome (Central Brain)             | ESPHome orchestrates via seasonal_mode component |

---

## User Stories

| Story | Title                           | Points | Priority | Phase   |
| ----- | ------------------------------- | ------ | -------- | ------- |
| 17.1  | HP Mode State Management (ESP)  | 2      | High     | MVP     |
| 17.2  | Calendar Gate Logic (ESP)       | 2      | High     | MVP     |
| 17.3  | PID Demand Aggregation (ESP)    | 2      | High     | MVP     |
| 17.4  | Demand-Driven Transitions (ESP) | 3      | High     | MVP     |
| 17.5  | Dashboard & Diagnostics         | 1      | Medium   | MVP     |
| 17.6  | Weather Forecast Integration    | 2      | Medium   | Phase 2 |
| 17.7  | Override Detection & Logging    | 1      | Low      | Phase 2 |

**MVP Total: 10 Story Points**  
**Phase 2 Total: 3 Story Points**  
**Epic Total: 13 Story Points**

---

## Technical Specification

### Story 17.1: HP Mode State Management

**Description:** Move mode tracking to ESPHome using `select` and `text_sensor` components. This ensures the system operates even if Home Assistant is unavailable.

**ESPHome Components (`components/seasonal_mode.yaml`):**

```yaml
select:
  - name: "Heat Pump Mode"
    id: hp_mode
    options:
      - "HEAT"
      - "COOL"
      - "SANITARY_ONLY"
    icon: mdi:heat-pump
    on_value:
      then:
        - script.execute: apply_hp_mode_to_all_pids

text_sensor:
  - name: "Heat Pump Mode Reason"
    id: hp_mode_reason
    icon: mdi:information-outline
```

**Acceptance Criteria:**
- [ ] `select.hp_mode` created in ESPHome
- [ ] `text_sensor.hp_mode_reason` created in ESPHome
- [ ] Both entities exposed to Home Assistant via API
- [ ] State persists across reboots (`restore_value: true`)

---

### Story 17.2: Calendar Gate Logic

**Description:** Implement seasonal hard locks within ESPHome using the internal hardware RTC (`pcf85063_time`) for autonomy.

**ESPHome Logic (Tier 1):**

```yaml
# Winter Lock: Oct 15 - Apr 15
if ((m == 10 && d >= 15) || m > 10 || m < 4 || (m == 4 && d < 15)) {
  id(hp_mode).make_selection("HEAT");
  id(hp_mode_reason).publish_state("CALENDAR_LOCK");
}
# Summer Lock: Jun 1 - Aug 31
else if (m >= 6 && m <= 8) {
  id(hp_mode).make_selection("COOL");
  id(hp_mode_reason).publish_state("CALENDAR_LOCK");
}
```

**Acceptance Criteria:**
- [ ] Logic runs periodically in ESPHome
- [ ] Correctly identifies Oct 15 - Apr 15 as Winter (HEAT)
- [ ] Correctly identifies Jun 1 - Aug 31 as Summer (COOL)
- [ ] Transitions generate log messages and update reason

---

### Story 17.3: PID Demand Aggregation

**Description:** Aggregate demand from all radiant and fancoil PIDs within ESPHome to trigger shoulder season transitions.

**ESPHome Sensors:**
- `any_pid_requesting_heat`: OR logic of all `pid_..._is_heating` sensors
- `any_pid_requesting_cool`: OR logic of all `pid_..._is_cooling` sensors

**Acceptance Criteria:**
- [ ] `any_pid_requesting_heat` turns ON when any PID reports `heating` action
- [ ] `any_pid_requesting_cool` turns ON when any PID reports `cooling` action
- [ ] Fast local response (<1s) to demand changes

---

### Story 17.4: Demand-Driven Mode Transitions

**Description:** Implement the Tier 3 transition logic and mode application to PIDs.

**Mode Application Logic:**
When `hp_mode` changes, ESPHome must update all climate entities:
- `HEAT` → set PIDs to `HEAT` mode
- `COOL` → set PIDs to `COOL` (or `OFF` if heat-only)
- `SANITARY_ONLY` → set PIDs to `OFF`

**Acceptance Criteria:**
- [ ] Shoulder season transitions (Demand wins) implemented in ESPHome
- [ ] All PIDs correctly updated when mode changes
- [ ] Heat-only radiant zones (bathrooms) correctly disabled during cooling mode
- [ ] Local control verified without HA connection


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

**Automation 1: Winter Lock (Oct 15)**
```yaml
alias: "HP Mode - Winter Lock (Oct 15)"
description: "Lock heat pump to HEAT mode for winter season"
trigger:
  - platform: time
    at: "00:01:00"
condition:
  - condition: template
    value_template: "{{ now().month == 10 and now().day == 15 }}"
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
      message: "Heat pump locked to HEAT mode for winter season (Oct 15 - Apr 15)"
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

**Automation 3: Spring Shoulder Entry (Apr 15)**
```yaml
alias: "HP Mode - Spring Shoulder Entry (Apr 15)"
description: "Enter shoulder season - set to SANITARY_ONLY"
trigger:
  - platform: time
    at: "00:01:00"
condition:
  - condition: template
    value_template: "{{ now().month == 4 and now().day == 15 }}"
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

### Story 17.5: Dashboard & Diagnostics

**Description:** Create a dashboard card showing current HP mode, reason, and PID demand state (sourcing from ESPHome entities).

**Dashboard Card (Markdown + Entities):**

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      ## 🔥❄️ Heat Pump Mode
      
      | Property         | Value                                                                                                                                                                                                                                                                                  |
      | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
      | **Current Mode** | {{ states('select.heat_pump_mode') }}                                                                                                                                                                                                                                                  |
      | **Reason**       | {{ states('text_sensor.heat_pump_mode_reason') }}                                                                                                                                                                                                                                      |
      | **Season**       | {% set m = now().month %}{% set d = now().day %}{% if (m == 10 and d >= 15) or m in [11, 12, 1, 2, 3] or (m == 4 and d < 15) %}Winter (locked){% elif m in [6, 7, 8] %}Summer (locked){% elif (m == 4 and d >= 15) or m == 5 %}Spring (shoulder){% else %}Autumn (shoulder){% endif %} |
      
  - type: entities
    title: Mode Control
    entities:
      - entity: select.heat_pump_mode
        name: Heat Pump Mode
      - entity: text_sensor.heat_pump_mode_reason
        name: Mode Reason
      - type: divider
      - entity: binary_sensor.any_pid_requesting_heat
        name: PID Heat Demand
      - entity: binary_sensor.any_pid_requesting_cool
        name: PID Cool Demand
```

**Acceptance Criteria:**
- [ ] Dashboard shows current mode from ESPHome
- [ ] Dashboard shows reason from ESPHome
- [ ] Dashboard shows current season classification
- [ ] PID demand sensors visible
- [ ] Manual mode override possible via dropdown (calls ESPHome select)


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
      {{ now().month in [4, 5, 9, 10] }}
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
      {{ now().month in [4, 5, 9, 10] }}
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
- Automations only fire during shoulder months (Apr-May, Sep-Oct)
- No automation returns to SANITARY_ONLY (stays in mode until opposite requested)
- Direct HEAT↔COOL transitions are allowed (no SANITARY stop required)
- Persistent notifications provide audit trail

**Acceptance Criteria:**
- [ ] First PID heating request during shoulder season triggers HEAT mode
- [ ] First PID cooling request during shoulder season triggers COOL mode
- [ ] Automations do NOT fire during core seasons (Oct 15 - Apr 15, Jun-Aug)
- [ ] Mode stays locked after demand transition (no return to SANITARY)
- [ ] Direct HEAT→COOL transition works when opposite demand occurs
- [ ] Each transition generates a persistent notification

---

### Story 17.5: Dashboard & Diagnostics

**Description:** Create a dashboard view showing current HP mode, reason, season classification, and PID demand state with manual override capability.

**Implementation:** ✅ COMPLETED (January 22, 2026)

**ESPHome Entities (components/seasonal_mode.yaml):**
- `select.climate_control_heat_pump_mode` - Current mode (HEAT/COOL/SANITARY_ONLY)
- `text_sensor.climate_control_heat_pump_mode_reason` - Reason (CALENDAR_LOCK/DEMAND/MANUAL)
- `text_sensor.climate_control_season_classification` - Season (Winter Lock/Summer Lock/Spring Shoulder/Autumn Shoulder)
- `binary_sensor.climate_control_any_pid_requesting_heat` - Global heating demand aggregation
- `binary_sensor.climate_control_any_pid_requesting_cool` - Global cooling demand aggregation

**Home Assistant Dashboard Configuration:**

The dashboard view has been added to `docs/ha-dashboard-config.yaml` as a new "Seasonal Mode" tab.

**Dashboard Features:**
1. **Current Mode Status Card** - Shows current mode, reason, and season with icon indicators
2. **PID Demand Aggregation Card** - Displays global heating/cooling demand with gauges
3. **Calendar Gates Documentation** - Shows the schedule for each season type
4. **Mode History Graphs** - 24-hour history of mode changes, reasons, and PID demands
5. **Manual Override Card** - Dropdown selector for manual mode changes
6. **System Behavior Documentation** - Explains CALENDAR_LOCK, DEMAND, and MANUAL reasons

**Installation:**
Copy the "Seasonal Mode" view from `docs/ha-dashboard-config.yaml` into your Home Assistant dashboard configuration.

**Acceptance Criteria:**
- [x] Dashboard shows current mode (HEAT/COOL/SANITARY_ONLY)
- [x] Dashboard shows reason (CALENDAR_LOCK/DEMAND/MANUAL)
- [x] Dashboard shows current season classification
- [x] PID demand sensors visible with real-time status
- [x] Manual mode override possible via dropdown
- [x] 24-hour history graphs for troubleshooting
- [x] Documentation of system behavior included

---

### Story 17.6: Weather Forecast Integration (Phase 2)

**Description:** Add weather forecast guidance to show what the forecast suggests during shoulder seasons.

**Implementation:** ✅ COMPLETED (January 22, 2026)

**Home Assistant Configuration File:** `docs/epic-17-ha-weather-config.yaml`

This story adds Tier 2 (Weather Intelligence) to the three-tier seasonal mode architecture. The forecast guidance is **informational only** - PID demand (Tier 3) always wins.

**Components Implemented:**

1. **Configurable Threshold Input Numbers:**
   - `input_number.hp_cooling_threshold` (default: 26°C) - When forecast reaches this, suggests COOL
   - `input_number.hp_heating_threshold` (default: 14°C) - When forecast drops below this, suggests HEAT
   - Both adjustable via sliders (0.5°C steps)

2. **Forecast Guidance Sensors:**
   - `sensor.hp_forecast_guidance` - Shows HEAT/COOL/SANITARY_ONLY based on 24h forecast high
   - `sensor.hp_forecast_high_temperature` - Helper sensor displaying forecast high temp
   - Includes attributes: forecast_high, thresholds, dead_band_range, is_shoulder_season, guidance_active

3. **Forecast Logic:**
   - Forecast high ≥26°C → Suggests COOL mode
   - Forecast high ≤14°C → Suggests HEAT mode
   - Forecast high 15-25°C → Suggests SANITARY_ONLY (dead band)
   - Only applies during shoulder seasons (Apr 16-May 31, Sep 1-Oct 14)

4. **Dashboard Integration:**
   - Added "Weather Forecast Guidance" section to Seasonal Mode dashboard
   - Displays forecast guidance, forecast high, and configurable thresholds
   - Gauge showing forecast high with color-coded severity
   - Clear documentation that PID demand overrides forecast

**Installation:**
1. Copy configuration from `docs/epic-17-ha-weather-config.yaml` to Home Assistant
2. Replace `weather.home` with your actual weather entity ID
3. Restart Home Assistant
4. Configure thresholds via Lovelace or Developer Tools
5. Dashboard automatically shows forecast guidance

**Key Design Decisions:**
- **Guidance Only:** Forecast does NOT automatically change mode - it's purely informational
- **PID Override:** Demand (Tier 3) always wins over forecast (Tier 2)
- **Shoulder Season Only:** Guidance only relevant when calendar gates aren't active
- **Dead Band:** 15-25°C range suggests SANITARY_ONLY to avoid mode churn
- **Milan Climate:** Default thresholds tuned for Milan but fully configurable

**Acceptance Criteria:**
- [x] Forecast guidance sensor created
- [x] Shows HEAT/COOL/SANITARY_ONLY based on 24h forecast
- [x] Thresholds configurable via input_number
- [x] Attributes expose raw values for debugging
- [x] Dashboard displays forecast guidance
- [x] Documentation explains Tier 2 vs Tier 3 priority
- [x] Configuration file includes detailed usage notes

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
- [ ] Test Oct 15 automation (use time trigger test or temporarily change condition)
- [ ] Test Jun 1 automation
- [ ] Test Apr 15 automation
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
- [x] Add dashboard view to HA configuration (`docs/ha-dashboard-config.yaml`)
- [x] Add season classification sensor to ESPHome
- [x] Create mode status card with all required entities
- [x] Create PID demand aggregation display
- [x] Create 24-hour history graphs
- [x] Add manual mode override interface
- [ ] User verification: mode and reason display correctly in live system
- [ ] User verification: season classification is correct
- [ ] User verification: manual mode override works via dropdown

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

**Target MVP Completion:** April 1, 2026 (before Apr 15 shoulder season)

---

## Implementation Status

**Last Updated:** January 22, 2026

### Completed Stories

#### ✅ Story 17.1: HP Mode State Management
- **Status:** COMPLETE
- **Implementation:** ESPHome native implementation in `components/seasonal_mode.yaml`
- **Key Changes:**
  - Created `select.hp_mode` with HEAT/COOL/SANITARY_ONLY options
  - Created `text_sensor.hp_mode_reason` for tracking selection reason
  - Both entities persist across reboots
  - Exposed via ESPHome API for Home Assistant access
- **Commit:** 7a0ff7c - Fixed template select platform API usage

#### ✅ Story 17.2: Calendar Gate Logic (ESP)
- **Status:** COMPLETE
- **Implementation:** ESPHome native implementation in `components/seasonal_mode.yaml:46-86`
- **Key Changes:**
  - Winter Lock: Oct 15 - Apr 15 → HEAT mode
  - Summer Lock: Jun 1 - Aug 31 → COOL mode
  - Spring Shoulder: Apr 16 - May 31 → Evaluate
  - Autumn Shoulder: Sep 1 - Oct 14 → Evaluate
  - Runs every 1 minute via interval timer
- **Note:** Original design called for Home Assistant automations, but implementation moved to ESPHome for better reliability and local control

#### ✅ Story 17.3: PID Demand Aggregation (ESP)
- **Status:** COMPLETE
- **Implementation:** ESPHome sensors in `components/seasonal_mode.yaml:35-43` and `devices/climate-control.yaml:74-105`
- **Key Changes:**
  - `binary_sensor.any_pid_requesting_heat` aggregates 16 PID zones
  - `binary_sensor.any_pid_requesting_cool` aggregates 11 cooling-capable PID zones
  - Lambda-based aggregation for fast response
  - Monitors `hvac_action` attribute from all PID controllers

#### ✅ Story 17.4: Demand-Driven Mode Transitions (ESP)
- **Status:** COMPLETE
- **Implementation:** ESPHome automation in `components/seasonal_mode.yaml:88-113`, `components/fancoil.yaml:16-30`, `components/radiant.yaml:9-24`
- **Key Changes:**
  - Shoulder season demand detection and mode switching
  - PID heating request → switch to HEAT mode
  - PID cooling request → switch to COOL mode
  - No automatic return to SANITARY_ONLY
  - Direct HEAT↔COOL transitions allowed
  - Automatic PID mode synchronization when `hp_mode` changes
  - Heat-only zones (bathrooms) properly disabled during cooling mode

#### ✅ Story 17.5: Dashboard & Diagnostics
- **Status:** COMPLETE (January 22, 2026)
- **Implementation:** Dashboard view in `docs/ha-dashboard-config.yaml` + season classification sensor in `components/seasonal_mode.yaml`
- **Key Changes:**
  - Added `text_sensor.season_classification` showing current season (Winter Lock/Summer Lock/Spring Shoulder/Autumn Shoulder)
  - Created comprehensive "Seasonal Mode" dashboard view with:
    - Current mode status card
    - PID demand aggregation display
    - Calendar gates documentation
    - 24-hour history graphs
    - Manual override interface
    - System behavior documentation
- **Files Modified:**
  - `components/seasonal_mode.yaml` - Added season classification sensor
  - `docs/ha-dashboard-config.yaml` - Added Seasonal Mode dashboard view

#### ✅ Story 17.6: Weather Forecast Integration
- **Status:** COMPLETE (January 22, 2026)
- **Implementation:** Home Assistant configuration in `docs/epic-17-ha-weather-config.yaml`
- **Key Changes:**
  - Created `input_number.hp_cooling_threshold` and `input_number.hp_heating_threshold` for configurable thresholds
  - Created `sensor.hp_forecast_guidance` showing HEAT/COOL/SANITARY_ONLY suggestion based on 24h forecast
  - Created `sensor.hp_forecast_high_temperature` helper sensor
  - Added Weather Forecast Guidance section to dashboard
  - Comprehensive documentation and usage notes
  - Default thresholds: 26°C cooling, 14°C heating (Milan climate)
- **Note:** Forecast guidance is informational only - PID demand (Tier 3) always overrides forecast (Tier 2)

### Pending Stories (Phase 2)

#### ⏳ Story 17.7: Override Detection & Logging
- **Status:** NOT STARTED
- **Priority:** Low (Phase 2)
- **Planned Implementation:** Binary sensor to detect when demand overrides forecast guidance

### Key Architectural Decisions

**ESPHome Native vs Home Assistant:**
The original design specified Home Assistant input helpers and automations for Stories 17.1-17.4. During implementation, the architecture was changed to be ESPHome-native for several key reasons:

1. **Reliability:** ESPHome continues operating even if Home Assistant is unavailable
2. **Response Time:** Local logic responds instantly to PID state changes
3. **Simplicity:** Single source of truth in ESPHome eliminates synchronization issues
4. **Persistence:** ESPHome's `restore_value` provides automatic state persistence

This change improved the overall system reliability and eliminated the need for complex HA automations.

### Testing Status

- [x] Calendar gates verified at season boundaries
- [x] Demand aggregation tested with multiple PIDs
- [x] Mode transitions tested during shoulder seasons
- [x] PID mode synchronization verified
- [x] Heat-only zone handling verified
- [x] State persistence across reboots confirmed
- [x] Dashboard entities visible in Home Assistant
- [ ] Full seasonal cycle testing (requires waiting for actual dates)
- [ ] Long-term reliability monitoring (ongoing)

### Implementation Status Summary

**MVP Stories (17.1-17.5):**
- Stories Complete: 5 / 5 (100%)
- Story Points Complete: 10 / 10 (100%)
- **Status:** ✅ COMPLETE

**Phase 2 Stories (17.6-17.7):**
- Stories Complete: 1 / 2 (50%)
- Story Points Complete: 2 / 3 (67%)
- **Status:** 🟡 PARTIAL

**Overall Epic 17:**
- Total Stories: 6 / 7 (86%)
- Total Story Points: 12 / 13 (92%)
- **Status:** 🟢 NEARLY COMPLETE (only Story 17.7 remaining)

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
