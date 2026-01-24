# Epic 16: First Floor MEV Intelligent Control

**Date:** January 14, 2026  
**Updated:** January 15, 2026  
**Status:** Draft  
**Priority:** High  
**Estimated Story Points:** 14

---

## Executive Summary

Implement intelligent control logic for the First Floor MEV (Mechanical Extract Ventilation) system using a dual-path architecture: **Air Quality Path** (CO₂ + VOC/IAQ) drives baseline ventilation, while **Humidity Control Path** uses a **fan-speed-triggered state machine** to keep humidity within a configurable window (40-60%). Fan speed is the **primary control variable**, modulating continuously based on humidity position and rate of change. Equipment (dehumidifier, cooling pump) escalates when **fan speed is high but humidity is still rising**, and de-escalates when **humidity is low and fan is coasting**.

### MEV System Capabilities

The MEV is an intelligent heat-recovery ventilation unit with:
- **Variable outside air intake** - Adjustable vent controlling fresh air vs recirculation ratio
- **Internal humidity logic** - Compares inside vs outside humidity to optimize air exchange
- **Heat recovery** - Up to 90% heat retention via heat exchanger
- **Built-in dehumidifier** - For active moisture removal when recirculating
- **Cooling coil** - Connected to HP chilled water buffer via circulation pump

---

## Problem Statement

### Current State
- Epic 6 deployed MEV hardware control (4 relays + DAC fan speed + alarm sensor)
- MEV entities exposed to Home Assistant but **no automation logic implemented**
- Manual control only—no automatic response to humidity or air quality
- Cooling integration relay controls a pump that draws chilled water from HP buffer
- Room sensors have humidity, CO₂, and VOC/IAQ data (Epic 15 makes CO₂/IAQ available on ESPHome)

### Pain Points
- **No automatic humidity response:** Showers, cooking, laundry create humidity spikes without MEV response
- **No air quality response:** CO₂ builds up with occupancy; VOC spikes from cooking/cleaning ignored
- **Cooling integration unused:** Dehumidification via HP chilled water coil never activates
- **Energy waste:** MEV either runs constantly or not at all—no demand-based modulation
- **User burden:** Requires manual adjustment for different conditions

### Why This Matters
- **Health:** Poor air quality (CO₂ >1000ppm) causes fatigue, headaches, reduced cognitive function
- **Comfort:** High humidity (>65%) causes discomfort and can impact radiant cooling effectiveness
- **Building Protection:** Persistent high humidity risks condensation and mold
- **Energy Efficiency:** Demand-based control reduces unnecessary ventilation

---

## Proposed Solution

### Architecture: Dual-Path with Fan-Speed-Triggered State Machine

```
┌────────────────────────────────────────────────────────────────────┐
│                     MEV CONTROL LOGIC (v5)                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  PATH A: AIR QUALITY (always active)                               │
│  ├── Inputs: first_floor_max_co2, first_floor_max_iaq              │
│  ├── Output: Fan Speed Demand (20-90%)                             │
│  └── Mapping: CO₂/IAQ levels → proportional fan demand             │
│                                                                    │
│  PATH B: HUMIDITY CONTROL (fan-speed-triggered)                    │
│  ├── Window: 40-60% (both configurable via HA)                     │
│  ├── Goal: Keep humidity in window with MINIMUM equipment          │
│  │                                                                 │
│  │  FAN SPEED = Primary control AND escalation signal              │
│  │  ├── Modulates based on position in 40-60% window + rate        │
│  │  ├── High fan + rising humidity = escalate equipment            │
│  │  └── Low fan + low humidity = de-escalate equipment             │
│  │                                                                 │
│  │  STATES:                                                        │
│  │  ┌───────────┐     ┌──────────────┐     ┌───────────┐           │
│  │  │  FAN_ONLY │────▶│ DEHUMIDIFYING│────▶│  COOLING  │           │
│  │  └───────────┘◀────└──────────────┘◀────└───────────┘           │
│  │                                                                 │
│  │  ESCALATION (fan working hard, losing battle):                  │
│  │  ├── Fan ≥ 70% for 5min AND rate > 0 → add Dehumidifier         │
│  │  └── Fan ≥ 80% for 5min AND rate > 0 → add Cooling (summer)     │
│  │                                                                 │
│  │  DE-ESCALATION (humidity low, fan coasting):                    │
│  │  ├── Humidity < 40% AND fan < 30% for 10min → remove Cooling    │
│  │  └── Humidity < 40% AND fan < 30% for 10min → remove Dehumid    │
│  │                                                                 │
│  └── Night: Organic de-escalation as ambient humidity drops        │
│                                                                    │
│  FINAL OUTPUT:                                                     │
│  ├── Fan Speed = max(Path A demand, Path B demand, 20%)            │
│  ├── Dehumidifier = DEHUMIDIFYING or COOLING state                 │
│  └── Cooling Pump = COOLING state AND Summer Mode                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision                  | Choice                            | Rationale                                                  |
| ------------------------- | --------------------------------- | ---------------------------------------------------------- |
| **Humidity Window**       | 40-60% (both configurable)        | Simple bounds, runtime tunable                             |
| **Fan as Signal**         | Escalate when fan high + rising   | Fan effort indicates "losing the battle"                   |
| **Equipment Philosophy**  | Normal in summer, not emergency   | Milan summer = humid; dehumidifier often needed            |
| **De-escalation Trigger** | Low humidity + coasting fan       | Only remove equipment when clearly not needed              |
| **Night Mode**            | Organic via ambient humidity      | No special logic; system naturally de-escalates            |
| **MEV Intelligence**      | Trust internal air exchange logic | MEV optimizes fresh/recirculated mix automatically         |
| **Minimum Fan Speed**     | 20% always                        | Continuous air exchange for health                         |
| **Cooling Prerequisites** | Summer Mode only                  | Chilled water only available in summer                     |
| **Implementation**        | Home Assistant Automation         | Follows Epic 5/6 pattern: ESPHome exposes, HA orchestrates |

---

## User Stories

| Story | Title                             | Points | Priority |
| ----- | --------------------------------- | ------ | -------- |
| 16.1  | First Floor Humidity Aggregation  | 1      | High     |
| 16.2  | Air Quality → Fan Speed Mapping   | 2      | High     |
| 16.3  | Humidity Rate Calculation         | 2      | High     |
| 16.4  | Fan-Speed-Triggered State Machine | 3      | High     |
| 16.5  | HA Configuration Entities         | 2      | High     |
| 16.6  | HA Automation Implementation      | 3      | High     |
| 16.7  | Dashboard & Diagnostics           | 1      | Medium   |

**Total: 14 Story Points**

---

## Technical Specification

### Story 16.1: First Floor Humidity Aggregation

**File:** `components/rooms/first_floor/first-floor.yaml`

Create max humidity sensor across all 8 first floor rooms:

```yaml
sensor:
  - platform: combination
    id: first_floor_max_humidity
    name: "First Floor Max Humidity"
    type: max
    unit_of_measurement: "%"
    device_class: humidity
    icon: "mdi:water-percent"
    sources:
      - source: bagno_grande_room_humidity_abstracted
      - source: bagno_ospiti_room_humidity_abstracted
      - source: bagno_padronale_room_humidity_abstracted
      - source: camera_nord_room_humidity_abstracted
      - source: camera_sud_room_humidity_abstracted
      - source: camera_ospiti_room_humidity_abstracted
      - source: camera_padronale_room_humidity_abstracted
      - source: lavanderia_room_humidity_abstracted
```

### Story 16.2: Air Quality → Fan Speed Mapping

**Thresholds:**

| Signal     | Excellent | Good    | Moderate | Poor      | Bad   |
| ---------- | --------- | ------- | -------- | --------- | ----- |
| CO₂ (ppm)  | <600      | 600-800 | 800-1000 | 1000-1400 | >1400 |
| IAQ Index  | <100      | 100-150 | 150-250  | 250-350   | >350  |
| Fan Demand | 20%       | 35%     | 50%      | 70%       | 90%   |

**Logic (HA Template):**
```yaml
{% set co2 = states('sensor.first_floor_max_co2') | float(600) %}
{% set iaq = states('sensor.first_floor_max_iaq') | float(100) %}

{% set co2_demand = 
  90 if co2 > 1400 else
  70 if co2 > 1000 else
  50 if co2 > 800 else
  35 if co2 > 600 else 20 %}

{% set iaq_demand = 
  90 if iaq > 350 else
  70 if iaq > 250 else
  50 if iaq > 150 else
  35 if iaq > 100 else 20 %}

{{ [co2_demand, iaq_demand] | max }}
```

### Story 16.3: Humidity Rate Calculation

**Purpose:** Calculate rolling humidity rate of change (%/min) for fan speed modulation.

**Configuration Variables:**

| Variable              | Default | Range | Description                         |
| --------------------- | ------- | ----- | ----------------------------------- |
| `rate_window_minutes` | 5       | 2-10  | Rolling window for rate calculation |

**HA Template Sensor:**
```yaml
template:
  - trigger:
      - platform: time_pattern
        minutes: "/1"
    sensor:
      - name: "First Floor Humidity Rate"
        unique_id: first_floor_humidity_rate
        unit_of_measurement: "%/min"
        state_class: measurement
        icon: mdi:trending-up
        state: >
          {% set window = states('input_number.mev_rate_window_minutes') | int(5) %}
          {% set current = states('sensor.first_floor_max_humidity') | float(none) %}
          {% set history = state_attr('sensor.first_floor_humidity_rate', 'history') | default([]) %}
          
          {# Add current reading to history #}
          {% set ns = namespace(hist = history + [{'time': now().timestamp(), 'value': current}]) %}
          
          {# Keep only readings within window #}
          {% set cutoff = now().timestamp() - (window * 60) %}
          {% set ns.hist = ns.hist | selectattr('time', '>=', cutoff) | list %}
          
          {# Calculate rate if we have enough data #}
          {% if ns.hist | length >= 2 and current is not none %}
            {% set oldest = ns.hist | first %}
            {% set dt_min = (now().timestamp() - oldest.time) / 60 %}
            {% if dt_min > 0 %}
              {{ ((current - oldest.value) / dt_min) | round(2) }}
            {% else %}
              0
            {% endif %}
          {% else %}
            0
          {% endif %}
        attributes:
          history: >
            {% set window = states('input_number.mev_rate_window_minutes') | int(5) %}
            {% set current = states('sensor.first_floor_max_humidity') | float(none) %}
            {% set history = state_attr('sensor.first_floor_humidity_rate', 'history') | default([]) %}
            {% set cutoff = now().timestamp() - (window * 60) %}
            {{ (history + [{'time': now().timestamp(), 'value': current}]) 
               | selectattr('time', '>=', cutoff) | list }}
```

### Story 16.4: Fan-Speed-Triggered State Machine

**States:**

| State             | Equipment                         | Entry Condition                            | Exit Condition                                                                        |
| ----------------- | --------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------- |
| **FAN_ONLY**      | Fan (20-90%)                      | Default / de-escalated from DEHUMIDIFYING  | Fan ≥ 70% for 5min AND rate > 0                                                       |
| **DEHUMIDIFYING** | Fan + Dehumidifier                | Escalated from FAN_ONLY                    | Fan ≥ 80% for 5min AND rate > 0 (up) OR humidity < 40% AND fan < 30% for 10min (down) |
| **COOLING**       | Fan + Dehumidifier + Cooling Pump | Escalated from DEHUMIDIFYING (summer only) | Humidity < 40% AND fan < 30% for 10min                                                |

**State Transitions:**
```
                         ESCALATION (humidity rising, fan maxed out)
                         ─────────────────────────────────────────▶

  ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
  │               │          │               │          │               │
  │   FAN_ONLY    │          │ DEHUMIDIFYING │          │    COOLING    │
  │               │          │               │          │               │
  │  Fan: 20-90%  │          │  Fan: 20-90%  │          │  Fan: 20-90%  │
  │  Dehum: OFF   │          │  Dehum: ON    │          │  Dehum: ON    │
  │  Cooling: OFF │          │  Cooling: OFF │          │  Cooling: ON  │
  │               │          │               │          │  (summer)     │
  └───────────────┘          └───────────────┘          └───────────────┘
         │                          │                          │
         │    fan ≥ 70%             │    fan ≥ 80%             │
         │    rate > 0              │    rate > 0              │
         │    for 5min              │    for 5min              │
         │─────────────────────────▶│─────────────────────────▶│
         │                          │                          │
         │◀─────────────────────────│◀─────────────────────────│
         │    humidity < 40%        │    humidity < 40%        │
         │    fan < 30%             │    fan < 30%             │
         │    for 10min             │    for 10min             │

                         ◀─────────────────────────────────────────
                         DE-ESCALATION (humidity low, fan coasting)
```

**Fan Speed Formula:**
```yaml
{% set upper = states('input_number.mev_humidity_upper_bound') | float(60) %}
{% set lower = states('input_number.mev_humidity_lower_bound') | float(40) %}
{% set humidity = states('sensor.first_floor_max_humidity') | float(50) %}
{% set rate = states('sensor.first_floor_humidity_rate') | float(0) %}
{% set aq_demand = states('sensor.mev_air_quality_demand') | int(20) %}
{% set min_fan = states('input_number.mev_minimum_fan_speed') | int(20) %}

{# Position in the humidity window (0% at lower, 100% at upper) #}
{% set window_size = upper - lower %}
{% set position = ((humidity - lower) / window_size) | float %}
{% set position_clamped = [[position, 0] | max, 1] | min %}

{# Position contributes 0-50% fan speed #}
{% set position_factor = (position_clamped * 50) | int %}

{# Rate contributes +20% per 1%/min (only when rising) #}
{% set rate_factor = [[rate * 20, 0] | max, 30] | min | int %}

{# Final calculation #}
{% set humidity_demand = min_fan + position_factor + rate_factor %}
{{ [[aq_demand, humidity_demand] | max, 90] | min }}
```

**Key Principle:** Fan speed is both the **control variable** (modulates to maintain humidity) AND the **escalation signal** (high fan + rising = add equipment).

### Story 16.5: HA Configuration Entities

**Required Home Assistant Helpers:**

Create these helpers in HA (Settings → Devices & Services → Helpers):

```yaml
# ============================================================
# INPUT NUMBERS - Runtime Configurable Parameters
# ============================================================

input_number:
  # Humidity window bounds
  mev_humidity_upper_bound:
    name: "MEV Humidity Upper Bound"
    min: 50
    max: 70
    step: 1
    unit_of_measurement: "%"
    icon: mdi:water-percent-alert
    initial: 60

  mev_humidity_lower_bound:
    name: "MEV Humidity Lower Bound"
    min: 30
    max: 50
    step: 1
    unit_of_measurement: "%"
    icon: mdi:water-percent
    initial: 40

  # Fan thresholds for escalation/de-escalation
  mev_escalation_fan_threshold:
    name: "MEV Escalation Fan Threshold (Dehumidifier)"
    min: 50
    max: 90
    step: 5
    unit_of_measurement: "%"
    icon: mdi:fan-alert
    initial: 70

  mev_escalation_fan_threshold_cooling:
    name: "MEV Escalation Fan Threshold (Cooling)"
    min: 60
    max: 95
    step: 5
    unit_of_measurement: "%"
    icon: mdi:fan-alert
    initial: 80

  mev_deescalation_fan_threshold:
    name: "MEV De-escalation Fan Threshold"
    min: 20
    max: 50
    step: 5
    unit_of_measurement: "%"
    icon: mdi:fan-off
    initial: 30

  # Timing
  mev_escalation_delay_minutes:
    name: "MEV Escalation Delay"
    min: 2
    max: 10
    step: 1
    unit_of_measurement: "min"
    icon: mdi:timer
    initial: 5

  mev_deescalation_delay_minutes:
    name: "MEV De-escalation Delay"
    min: 5
    max: 20
    step: 1
    unit_of_measurement: "min"
    icon: mdi:timer
    initial: 10

  # Rate calculation window
  mev_rate_window_minutes:
    name: "MEV Rate Calculation Window"
    min: 2
    max: 10
    step: 1
    unit_of_measurement: "min"
    icon: mdi:timer-sand
    initial: 5

  # Minimum fan speed (continuous air exchange)
  mev_minimum_fan_speed:
    name: "MEV Minimum Fan Speed"
    min: 10
    max: 40
    step: 5
    unit_of_measurement: "%"
    icon: mdi:fan
    initial: 20

# ============================================================
# INPUT SELECT - State Machine State
# ============================================================

input_select:
  mev_humidity_state:
    name: "MEV Humidity Control State"
    options:
      - fan_only
      - dehumidifying
      - cooling
    initial: fan_only
    icon: mdi:state-machine

# ============================================================
# TEMPLATE SENSORS - Diagnostics
# ============================================================

template:
  - sensor:
      - name: "MEV Air Quality Demand"
        unique_id: mev_aq_demand
        unit_of_measurement: "%"
        icon: mdi:fan
        state: >
          {% set co2 = states('sensor.first_floor_max_co2') | float(600) %}
          {% set iaq = states('sensor.first_floor_max_iaq') | float(100) %}
          {% set min_fan = states('input_number.mev_minimum_fan_speed') | int(20) %}
          {% set co2_d = 90 if co2 > 1400 else 70 if co2 > 1000 else 50 if co2 > 800 else 35 if co2 > 600 else min_fan %}
          {% set iaq_d = 90 if iaq > 350 else 70 if iaq > 250 else 50 if iaq > 150 else 35 if iaq > 100 else min_fan %}
          {{ [co2_d, iaq_d] | max }}

      - name: "MEV Humidity Demand"
        unique_id: mev_humidity_demand
        unit_of_measurement: "%"
        icon: mdi:water-percent
        state: >
          {% set upper = states('input_number.mev_humidity_upper_bound') | float(60) %}
          {% set lower = states('input_number.mev_humidity_lower_bound') | float(40) %}
          {% set humidity = states('sensor.first_floor_max_humidity') | float(50) %}
          {% set rate = states('sensor.first_floor_humidity_rate') | float(0) %}
          {% set min_fan = states('input_number.mev_minimum_fan_speed') | int(20) %}
          
          {# Position in the humidity window (0% at lower, 100% at upper) #}
          {% set window_size = upper - lower %}
          {% set position = ((humidity - lower) / window_size) | float %}
          {% set position_clamped = [[position, 0] | max, 1] | min %}
          
          {# Position contributes 0-50% fan speed #}
          {% set position_factor = (position_clamped * 50) | int %}
          
          {# Rate contributes +20% per 1%/min (only when rising) #}
          {% set rate_factor = [[rate * 20, 0] | max, 30] | min | int %}
          
          {# Final calculation #}
          {{ [[min_fan + position_factor + rate_factor, 90] | min, min_fan] | max }}

      - name: "MEV Final Fan Speed"
        unique_id: mev_final_fan_speed
        unit_of_measurement: "%"
        icon: mdi:fan
        state: >
          {% set aq = states('sensor.mev_air_quality_demand') | int(20) %}
          {% set humidity = states('sensor.mev_humidity_demand') | int(20) %}
          {% set min_fan = states('input_number.mev_minimum_fan_speed') | int(20) %}
          {{ [[aq, humidity, min_fan] | max, 100] | min }}
```

**Configuration Location:**

Add to `configuration.yaml` or create `packages/mev_helpers.yaml`:

```yaml
# packages/mev_helpers.yaml
homeassistant:
  packages:
    mev_helpers: !include mev_helpers.yaml
```

### Story 16.6: HA Automation Implementation

**Main Automations: Fan-Speed-Triggered State Machine**

```yaml
automation:
  # ============================================================
  # ESCALATION: FAN_ONLY → DEHUMIDIFYING
  # Fan working hard (≥70%) but humidity still rising
  # ============================================================
  - alias: "MEV Escalate: Fan Only → Dehumidifying"
    id: mev_escalate_to_dehumidifying
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.mev_final_fan_speed') | float(0) >= 
             states('input_number.mev_escalation_fan_threshold') | float(70) and
             states('sensor.first_floor_humidity_rate') | float(0) > 0 }}
        for:
          minutes: "{{ states('input_number.mev_escalation_delay_minutes') | int(5) }}"
    condition:
      - condition: state
        entity_id: input_select.mev_humidity_state
        state: "fan_only"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.mev_humidity_state
        data:
          option: "dehumidifying"
      - service: switch.turn_on
        target:
          entity_id: switch.first_floor_mev_dehumidifier
      - service: system_log.write
        data:
          message: "MEV: Escalated to DEHUMIDIFYING (fan ≥70%, humidity rising)"
          level: info

  # ============================================================
  # ESCALATION: DEHUMIDIFYING → COOLING
  # Fan still maxed (≥80%) despite dehumidifier
  # ============================================================
  - alias: "MEV Escalate: Dehumidifying → Cooling"
    id: mev_escalate_to_cooling
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.mev_final_fan_speed') | float(0) >= 
             states('input_number.mev_escalation_fan_threshold_cooling') | float(80) and
             states('sensor.first_floor_humidity_rate') | float(0) > 0 }}
        for:
          minutes: "{{ states('input_number.mev_escalation_delay_minutes') | int(5) }}"
    condition:
      - condition: state
        entity_id: input_select.mev_humidity_state
        state: "dehumidifying"
      - condition: state
        entity_id: binary_sensor.summer_mode
        state: "on"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.mev_humidity_state
        data:
          option: "cooling"
      - service: switch.turn_on
        target:
          entity_id: switch.first_floor_mev_cooling
      - service: system_log.write
        data:
          message: "MEV: Escalated to COOLING (dehumidifier not enough)"
          level: warning

  # ============================================================
  # DE-ESCALATION: COOLING → DEHUMIDIFYING
  # Humidity low AND fan coasting
  # ============================================================
  - alias: "MEV De-escalate: Cooling → Dehumidifying"
    id: mev_deescalate_from_cooling
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.first_floor_max_humidity') | float(100) < 
             states('input_number.mev_humidity_lower_bound') | float(40) and
             states('sensor.mev_final_fan_speed') | float(100) < 
             states('input_number.mev_deescalation_fan_threshold') | float(30) }}
        for:
          minutes: "{{ states('input_number.mev_deescalation_delay_minutes') | int(10) }}"
      - platform: state
        entity_id: binary_sensor.summer_mode
        to: "off"
    condition:
      - condition: state
        entity_id: input_select.mev_humidity_state
        state: "cooling"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.mev_humidity_state
        data:
          option: "dehumidifying"
      - service: switch.turn_off
        target:
          entity_id: switch.first_floor_mev_cooling
      - service: system_log.write
        data:
          message: "MEV: De-escalated to DEHUMIDIFYING (humidity < 40%, fan coasting)"
          level: info

  # ============================================================
  # DE-ESCALATION: DEHUMIDIFYING → FAN_ONLY
  # Humidity low AND fan coasting
  # ============================================================
  - alias: "MEV De-escalate: Dehumidifying → Fan Only"
    id: mev_deescalate_from_dehumidifying
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.first_floor_max_humidity') | float(100) < 
             states('input_number.mev_humidity_lower_bound') | float(40) and
             states('sensor.mev_final_fan_speed') | float(100) < 
             states('input_number.mev_deescalation_fan_threshold') | float(30) }}
        for:
          minutes: "{{ states('input_number.mev_deescalation_delay_minutes') | int(10) }}"
    condition:
      - condition: state
        entity_id: input_select.mev_humidity_state
        state: "dehumidifying"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.mev_humidity_state
        data:
          option: "fan_only"
      - service: switch.turn_off
        target:
          entity_id: switch.first_floor_mev_dehumidifier
      - service: system_log.write
        data:
          message: "MEV: De-escalated to FAN_ONLY (humidity < 40%, fan coasting)"
          level: info

  # ============================================================
  # FAN SPEED CONTROL - Continuous modulation
  # ============================================================
  - alias: "MEV Fan Speed Control"
    id: mev_fan_speed_control
    mode: restart
    trigger:
      - platform: state
        entity_id:
          - sensor.mev_final_fan_speed
          - input_select.mev_humidity_state
      - platform: time_pattern
        seconds: "/30"
    action:
      - service: number.set_value
        target:
          entity_id: number.first_floor_mev_fan_speed
        data:
          value: "{{ states('sensor.mev_final_fan_speed') | int(20) }}"
```

### Story 16.7: Dashboard & Diagnostics

**Entities to expose:**

| Entity                                              | Type   | Description                                   |
| --------------------------------------------------- | ------ | --------------------------------------------- |
| `input_number.mev_humidity_upper_bound`             | number | Upper humidity bound (default 60%)            |
| `input_number.mev_humidity_lower_bound`             | number | Lower humidity bound (default 40%)            |
| `input_number.mev_escalation_fan_threshold`         | number | Fan % to trigger dehumidifier (70%)           |
| `input_number.mev_escalation_fan_threshold_cooling` | number | Fan % to trigger cooling (80%)                |
| `input_number.mev_deescalation_fan_threshold`       | number | Fan % for de-escalation (30%)                 |
| `input_select.mev_humidity_state`                   | select | Current state: fan_only/dehumidifying/cooling |
| `sensor.first_floor_humidity_rate`                  | sensor | Rate of humidity change (%/min)               |
| `sensor.mev_air_quality_demand`                     | sensor | Air quality fan demand (%)                    |
| `sensor.mev_humidity_demand`                        | sensor | Humidity-based fan demand (%)                 |
| `sensor.mev_final_fan_speed`                        | sensor | Final commanded fan speed (%)                 |
| `sensor.first_floor_max_humidity`                   | sensor | Maximum humidity across all rooms             |
| `switch.first_floor_mev_dehumidifier`               | switch | Dehumidifier state                            |
| `switch.first_floor_mev_cooling`                    | switch | Cooling pump state                            |

**Dashboard Card Example:**
```yaml
type: entities
title: MEV Humidity Control
entities:
  - entity: sensor.first_floor_max_humidity
    name: Current Max Humidity
  - entity: sensor.first_floor_humidity_rate
    name: Rate of Change
  - entity: input_select.mev_humidity_state
    name: Control State
  - type: divider
  - entity: sensor.mev_final_fan_speed
    name: Fan Speed
  - entity: switch.first_floor_mev_dehumidifier
    name: Dehumidifier
  - entity: switch.first_floor_mev_cooling
    name: Cooling Pump
  - type: divider
  - entity: input_number.mev_humidity_upper_bound
    name: Upper Bound
  - entity: input_number.mev_humidity_lower_bound
    name: Lower Bound
```

---

## Dependencies

| Dependency                      | Status     | Notes                            |
| ------------------------------- | ---------- | -------------------------------- |
| Epic 6 (MEV Hardware)           | ✅ Complete | Exposes all MEV control entities |
| Epic 15 (Air Quality Broadcast) | 🔄 Required | CO₂/IAQ on climate-control board |
| Summer Mode sensor              | ✅ Exists   | `binary_sensor.summer_mode`      |
| First floor humidity sensors    | ✅ Working  | Via room_sensors.yaml            |

---

## Acceptance Criteria

### Functional
- [ ] Fan speed responds to CO₂ levels (test: breathe in closed room)
- [ ] Fan speed responds to IAQ/VOC (test: cook something aromatic)
- [ ] Fan speed modulates based on position in 40-60% humidity window
- [ ] Fan speed increases with positive humidity rate of change
- [ ] State machine escalates FAN_ONLY → DEHUMIDIFYING when fan ≥70% for 5min AND rate > 0
- [ ] State machine escalates DEHUMIDIFYING → COOLING when fan ≥80% for 5min AND rate > 0 (summer only)
- [ ] State machine de-escalates when humidity < 40% AND fan < 30% for 10min
- [ ] Minimum 20% fan speed maintained at all times
- [ ] All thresholds configurable via HA input_numbers

### Safety
- [ ] Cooling pump never activates in Winter mode
- [ ] System degrades gracefully if sensors unavailable (defaults to 20% fan)
- [ ] No equipment oscillation due to time delays

### Integration
- [ ] All configuration entities visible and editable in HA
- [ ] All diagnostic sensors visible in HA
- [ ] Dashboard shows current state clearly
- [ ] Alarm notifications still work (Epic 6)

---

## Risks & Mitigations

| Risk                   | Likelihood | Impact | Mitigation                                           |
| ---------------------- | ---------- | ------ | ---------------------------------------------------- |
| Sensor unavailability  | Low        | Medium | Fallback to safe defaults (20% fan, rate=0)          |
| Rate calculation noise | Medium     | Low    | 5-minute rolling window smooths spikes               |
| State oscillation      | Low        | Low    | Time-based delays (5min escalate, 10min de-escalate) |
| Over-ventilation       | Low        | Low    | Proportional control minimizes fan speed             |
| Equipment wear         | Low        | Medium | Fan-speed signal prevents unnecessary cycling        |

---

## Definition of Done

- [ ] Air quality path working (CO₂ + IAQ → fan speed)
- [ ] Humidity rate sensor calculating correctly
- [ ] Fan-speed-triggered state machine working
- [ ] Fan speed modulates based on humidity window position + rate
- [ ] Dehumidifier activates when fan high + humidity rising
- [ ] Cooling pump activates when fan maxed + humidity still rising (summer only)
- [ ] De-escalation works when humidity low + fan coasting
- [ ] All HA configuration entities created and working
- [ ] Dashboard shows all diagnostic info
- [ ] Documentation complete
- [ ] Testing checklist passed

---

## Appendix A: Brainstorming Session Summary

This epic emerged from a structured brainstorming session (January 14, 2026) that explored:

1. **Primary Control Trigger:** Selected multi-signal fusion (humidity + CO₂ + VOC)
2. **Humidity Management:** Identified 3-tier escalation (fan → dehumidifier → cooling coil)
3. **Cooling Integration:** Clarified that relay directly controls circulation pump to HP buffer
4. **Buffer Availability:** Simplified to "assume available in Summer Mode"
5. **Humidity Scope:** All 8 rooms (bedrooms impact radiant cooling effectiveness)

Key insight: MEV cooling integration is a **dehumidification tool**, not just ventilation—it draws chilled water through a coil to condense moisture from the air.

---

## Appendix B: Humidity Control Evolution (January 15, 2026)

The humidity control approach evolved through several iterations:

### v1: Threshold-Based Stages (Original)
- Fixed thresholds: ≥55% → Elevated, ≥65% → High, ≥75% → Critical
- **Problem:** Reactive, not proactive; treated equipment as emergency escalation

### v2-v3: Rate-Based Control
- Trigger equipment based on humidity rate of change
- **Problem:** In Milan summer, dehumidifier/cooling are normal operation, not exceptions

### v4: Threshold + Rate Hybrid
- Equipment ON/OFF based on humidity thresholds, fan modulated by rate
- **Problem:** Still treated equipment as exceptional

### v5: Fan-Speed-Triggered State Machine (Final)
- **Key insight:** Fan speed is both the control AND the escalation signal
- Simple 40-60% humidity window
- **Escalate** when fan working hard (≥70%) but losing the battle (rate > 0)
- **De-escalate** when humidity low (<40%) AND fan coasting (<30%)
- **Night behavior:** Organic de-escalation as ambient humidity drops
- **MEV intelligence:** Trust internal air exchange optimization

### MEV System Understanding

The MEV is more sophisticated than a simple extract fan:
- Variable outside air vent (fresh vs recirculated)
- Internal logic comparing inside/outside humidity
- Up to 90% heat recovery via exchanger
- Built-in dehumidifier for recirculated air
- Cooling coil for HP chilled water integration

This means we can trust the MEV to optimize air exchange internally, and focus our automation on **when to use each capability level** (fan only → +dehumidifier → +cooling).
