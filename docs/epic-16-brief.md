# Epic 16: First Floor MEV Intelligent Control

**Date:** January 14, 2026  
**Status:** Draft  
**Priority:** High  
**Estimated Story Points:** 14

---

## Executive Summary

Implement intelligent control logic for the First Floor MEV (Mechanical Extract Ventilation) system using a dual-path architecture: **Air Quality Path** (CO₂ + VOC/IAQ) drives baseline ventilation, while **Humidity Cascade Path** provides escalating responses including dehumidifier activation and cooling integration with the Heat Pump. The system uses a "max demand wins" fusion strategy where the highest demand from either path determines fan speed, with humidity-specific stages controlling additional equipment.

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

### Architecture: Dual-Path Max Demand

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
│  ├── Stages:                                                       │
│  │   ├── Stage 0 (Normal): <55% → Fan at AQ demand only           │
│  │   ├── Stage 1 (Elevated): ≥55% → Fan boost +20%                │
│  │   ├── Stage 2 (High): ≥65% → Fan 70%+ + Dehumidifier ON        │
│  │   └── Stage 3 (Critical): ≥75% → + Cooling Pump ON             │
│  └── Pump Protection: 5min ON / 10min OFF minimum                 │
│                                                                    │
│  FINAL OUTPUT:                                                     │
│  ├── Fan Speed = max(Path A demand, Path B stage demand)          │
│  ├── Dehumidifier = Stage 2+ active                                │
│  └── Cooling Pump = Stage 3 active AND Summer Mode                │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision                  | Choice                    | Rationale                                                  |
| ------------------------- | ------------------------- | ---------------------------------------------------------- |
| **Fusion Strategy**       | Max Demand Wins           | Simple, debuggable, never under-ventilates                 |
| **Humidity Scope**        | All 8 first floor rooms   | Bedroom humidity impacts radiant cooling                   |
| **Cooling Prerequisites** | Summer Mode only          | Cold water only available in summer                        |
| **Pump Protection**       | 5min ON / 10min OFF       | Prevents short-cycling, protects pump                      |
| **Implementation**        | Home Assistant Automation | Follows Epic 5/6 pattern: ESPHome exposes, HA orchestrates |

---

## User Stories

| Story | Title                                    | Points | Priority |
| ----- | ---------------------------------------- | ------ | -------- |
| 16.1  | First Floor Humidity Aggregation         | 1      | High     |
| 16.2  | Air Quality → Fan Speed Mapping          | 2      | High     |
| 16.3  | Humidity Cascade State Machine           | 3      | High     |
| 16.4  | Cooling Integration with Pump Protection | 3      | High     |
| 16.5  | HA Helper Entities                       | 1      | High     |
| 16.6  | HA Automation Implementation             | 3      | High     |
| 16.7  | Dashboard & Diagnostics                  | 1      | Medium   |

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

### Story 16.3: Humidity Cascade State Machine

**States:**

| Stage | Name     | Entry Condition         | Exit Condition | Actions                          |
| ----- | -------- | ----------------------- | -------------- | -------------------------------- |
| 0     | Normal   | humidity <55%           | —              | Fan = AQ demand                  |
| 1     | Elevated | humidity ≥55% for 5min  | <55% for 10min | Fan = max(AQ, AQ+20%)            |
| 2     | High     | humidity ≥65% for 10min | <60% for 15min | Fan ≥70%, Dehumidifier ON        |
| 3     | Critical | humidity ≥75% for 10min | <65% for 20min | Fan ≥90%, Dehumid ON, Cooling ON |

**State Transitions:**
```
       ┌──────────────────────────────────────────────────────────┐
       │                                                          │
       ▼                                                          │
  ┌─────────┐    ≥55% for 5min     ┌──────────┐                  │
  │ NORMAL  │ ─────────────────▶   │ ELEVATED │                  │
  │ Stage 0 │                      │ Stage 1  │                  │
  └─────────┘ ◀───────────────────└──────────┘                   │
       ▲         <55% for 10min          │                        │
       │                                 │ ≥65% for 10min         │
       │                                 ▼                        │
       │                           ┌──────────┐                   │
       │                           │   HIGH   │                   │
       │                           │ Stage 2  │                   │
       │                           │ +Dehumid │                   │
       │                           └──────────┘                   │
       │                                 │                        │
       │                                 │ ≥75% for 10min         │
       │         <65% for 20min          ▼                        │
       │                           ┌──────────┐                   │
       └───────────────────────────│ CRITICAL │───────────────────┘
                                   │ Stage 3  │  <65% for 20min
                                   │ +Cooling │
                                   └──────────┘
```

### Story 16.4: Cooling Integration with Pump Protection

**Prerequisites:**
- Summer Mode must be ON (`binary_sensor.summer_mode`)
- Cold water assumed available when in Summer Mode

**Pump Protection Timer:**
```yaml
timer:
  mev_cooling_pump_min_on:
    duration: "00:05:00"
  mev_cooling_pump_min_off:
    duration: "00:10:00"
```

**Logic:**
```yaml
# Can only START if:
#   - Summer Mode ON
#   - Stage 3 (Critical) active
#   - min_off timer not running (or idle)

# Can only STOP if:
#   - Stage <3 (exited Critical)
#   - min_on timer not running (or idle)
```

### Story 16.5: HA Helper Entities

**Required Home Assistant Helpers:**

Create these helpers in HA (Settings → Devices & Services → Helpers):

```yaml
# Input Select for Humidity Stage State Machine
input_select:
  mev_humidity_stage:
    name: "MEV Humidity Stage"
    options:
      - normal
      - elevated
      - high
      - critical
    initial: normal
    icon: mdi:water-percent

# Timers for Pump Protection
timer:
  mev_cooling_pump_min_on:
    name: "MEV Cooling Pump Min ON"
    duration: "00:05:00"
    icon: mdi:timer
  
  mev_cooling_pump_min_off:
    name: "MEV Cooling Pump Min OFF"  
    duration: "00:10:00"
    icon: mdi:timer-off

# Template Sensors for Diagnostics
template:
  - sensor:
      - name: "MEV Air Quality Demand"
        unique_id: mev_aq_demand
        unit_of_measurement: "%"
        icon: mdi:fan
        state: >
          {% set co2 = states('sensor.first_floor_max_co2') | float(600) %}
          {% set iaq = states('sensor.first_floor_max_iaq') | float(100) %}
          {% set co2_d = 90 if co2 > 1400 else 70 if co2 > 1000 else 50 if co2 > 800 else 35 if co2 > 600 else 20 %}
          {% set iaq_d = 90 if iaq > 350 else 70 if iaq > 250 else 50 if iaq > 150 else 35 if iaq > 100 else 20 %}
          {{ [co2_d, iaq_d] | max }}

      - name: "MEV Humidity Stage Demand"
        unique_id: mev_humidity_stage_demand
        unit_of_measurement: "%"
        icon: mdi:water-percent
        state: >
          {% set stage = states('input_select.mev_humidity_stage') %}
          {% set aq = states('sensor.mev_air_quality_demand') | int(20) %}
          {% if stage == 'critical' %}
            {{ [90, aq] | max }}
          {% elif stage == 'high' %}
            {{ [70, aq] | max }}
          {% elif stage == 'elevated' %}
            {{ [aq + 20, 100] | min }}
          {% else %}
            {{ aq }}
          {% endif %}
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

**Main Automation: MEV Intelligent Control**

```yaml
automation:
  - alias: "MEV First Floor Intelligent Control"
    id: mev_first_floor_intelligent_control
    mode: restart
    trigger:
      # Air quality changes
      - platform: state
        entity_id:
          - sensor.first_floor_max_co2
          - sensor.first_floor_max_iaq
      # Humidity changes
      - platform: state
        entity_id: sensor.first_floor_max_humidity
      # Periodic check
      - platform: time_pattern
        minutes: "/1"
    
    variables:
      # Air quality demand
      co2: "{{ states('sensor.first_floor_max_co2') | float(600) }}"
      iaq: "{{ states('sensor.first_floor_max_iaq') | float(100) }}"
      aq_demand: >
        {% set co2_d = 90 if co2 > 1400 else 70 if co2 > 1000 else 50 if co2 > 800 else 35 if co2 > 600 else 20 %}
        {% set iaq_d = 90 if iaq > 350 else 70 if iaq > 250 else 50 if iaq > 150 else 35 if iaq > 100 else 20 %}
        {{ [co2_d, iaq_d] | max }}
      
      # Humidity
      humidity: "{{ states('sensor.first_floor_max_humidity') | float(50) }}"
      
      # Current stage (from input_select or calculated)
      humidity_stage: "{{ states('input_select.mev_humidity_stage') }}"
      
      # Summer mode
      summer_mode: "{{ is_state('binary_sensor.summer_mode', 'on') }}"
    
    action:
      - choose:
          # Stage 3: Critical
          - conditions:
              - condition: template
                value_template: "{{ humidity_stage == 'critical' }}"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.first_floor_mev_fan_speed
                data:
                  value: "{{ [90, aq_demand] | max }}"
              - service: switch.turn_on
                target:
                  entity_id: switch.first_floor_mev_dehumidifier
              # Cooling only in summer (with pump protection)
              - if:
                  - condition: template
                    value_template: "{{ summer_mode }}"
                  - condition: state
                    entity_id: timer.mev_cooling_pump_min_off
                    state: "idle"
                then:
                  - service: switch.turn_on
                    target:
                      entity_id: switch.first_floor_mev_cooling
                  - service: timer.start
                    target:
                      entity_id: timer.mev_cooling_pump_min_on
          
          # Stage 2: High
          - conditions:
              - condition: template
                value_template: "{{ humidity_stage == 'high' }}"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.first_floor_mev_fan_speed
                data:
                  value: "{{ [70, aq_demand] | max }}"
              - service: switch.turn_on
                target:
                  entity_id: switch.first_floor_mev_dehumidifier
              # Turn off cooling (with protection)
              - if:
                  - condition: state
                    entity_id: timer.mev_cooling_pump_min_on
                    state: "idle"
                then:
                  - service: switch.turn_off
                    target:
                      entity_id: switch.first_floor_mev_cooling
                  - service: timer.start
                    target:
                      entity_id: timer.mev_cooling_pump_min_off
          
          # Stage 1: Elevated
          - conditions:
              - condition: template
                value_template: "{{ humidity_stage == 'elevated' }}"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.first_floor_mev_fan_speed
                data:
                  value: "{{ [aq_demand + 20, aq_demand] | max | min(100) }}"
              - service: switch.turn_off
                target:
                  entity_id: switch.first_floor_mev_dehumidifier
              - service: switch.turn_off
                target:
                  entity_id: switch.first_floor_mev_cooling
          
          # Stage 0: Normal
          - conditions:
              - condition: template
                value_template: "{{ humidity_stage == 'normal' }}"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.first_floor_mev_fan_speed
                data:
                  value: "{{ aq_demand }}"
              - service: switch.turn_off
                target:
                  entity_id: switch.first_floor_mev_dehumidifier
              - service: switch.turn_off
                target:
                  entity_id: switch.first_floor_mev_cooling
```

**Stage Transition Automations:**

```yaml
# Normal → Elevated (≥55% for 5min)
automation:
  - alias: "MEV Stage: Normal → Elevated"
    trigger:
      - platform: numeric_state
        entity_id: sensor.first_floor_max_humidity
        above: 55
        for:
          minutes: 5
    condition:
      - condition: state
        entity_id: input_select.mev_humidity_stage
        state: "normal"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.mev_humidity_stage
        data:
          option: "elevated"

  # Elevated → High (≥65% for 10min)
  - alias: "MEV Stage: Elevated → High"
    trigger:
      - platform: numeric_state
        entity_id: sensor.first_floor_max_humidity
        above: 65
        for:
          minutes: 10
    condition:
      - condition: state
        entity_id: input_select.mev_humidity_stage
        state: "elevated"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.mev_humidity_stage
        data:
          option: "high"

  # High → Critical (≥75% for 10min)
  - alias: "MEV Stage: High → Critical"
    trigger:
      - platform: numeric_state
        entity_id: sensor.first_floor_max_humidity
        above: 75
        for:
          minutes: 10
    condition:
      - condition: state
        entity_id: input_select.mev_humidity_stage
        state: "high"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.mev_humidity_stage
        data:
          option: "critical"

  # De-escalation: Any stage → Normal (<55% for 10min from elevated, <60% for 15min from high, <65% for 20min from critical)
  - alias: "MEV Stage: De-escalate to Normal"
    trigger:
      - platform: numeric_state
        entity_id: sensor.first_floor_max_humidity
        below: 55
        for:
          minutes: 10
    condition:
      - condition: state
        entity_id: input_select.mev_humidity_stage
        state: "elevated"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.mev_humidity_stage
        data:
          option: "normal"

  - alias: "MEV Stage: High → Normal"
    trigger:
      - platform: numeric_state
        entity_id: sensor.first_floor_max_humidity
        below: 60
        for:
          minutes: 15
    condition:
      - condition: state
        entity_id: input_select.mev_humidity_stage
        state: "high"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.mev_humidity_stage
        data:
          option: "normal"

  - alias: "MEV Stage: Critical → Normal"
    trigger:
      - platform: numeric_state
        entity_id: sensor.first_floor_max_humidity
        below: 65
        for:
          minutes: 20
    condition:
      - condition: state
        entity_id: input_select.mev_humidity_stage
        state: "critical"
    action:
      - service: input_select.select_option
        target:
          entity_id: input_select.mev_humidity_stage
        data:
          option: "normal"
```

### Story 16.7: Dashboard & Diagnostics

**Entities to expose:**
- `input_select.mev_humidity_stage` - Current cascade stage
- `sensor.mev_aq_demand` - Calculated air quality fan demand
- `sensor.mev_final_fan_speed` - Actual commanded fan speed
- `binary_sensor.mev_cooling_active` - Cooling pump state
- `timer.mev_cooling_pump_min_on` - Pump protection timer
- `timer.mev_cooling_pump_min_off` - Pump protection timer

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
- [ ] Humidity cascade triggers stages correctly
- [ ] Dehumidifier activates at Stage 2
- [ ] Cooling pump activates at Stage 3 (summer mode only)
- [ ] Pump protection prevents cycling <5min ON / <10min OFF

### Safety
- [ ] Cooling pump never activates in Winter mode
- [ ] Pump protection timers work correctly
- [ ] System degrades gracefully if sensors unavailable

### Integration
- [ ] All diagnostic entities visible in HA
- [ ] Dashboard shows current state clearly
- [ ] Alarm notifications still work (Epic 6)

---

## Risks & Mitigations

| Risk                  | Likelihood | Impact | Mitigation                          |
| --------------------- | ---------- | ------ | ----------------------------------- |
| Sensor unavailability | Low        | Medium | Fallback to safe defaults (40% fan) |
| Pump short-cycling    | Low        | High   | Timer-based protection              |
| Stage oscillation     | Medium     | Low    | Hysteresis in thresholds            |
| Over-ventilation      | Low        | Low    | Max fan speed caps                  |

---

## Definition of Done

- [ ] Air quality path working (CO₂ + IAQ → fan speed)
- [ ] Humidity cascade state machine working
- [ ] Dehumidifier activates at correct stage
- [ ] Cooling integration with pump protection working
- [ ] Dashboard shows all diagnostic info
- [ ] Documentation complete
- [ ] Testing checklist passed

---

## Appendix: Brainstorming Session Summary

This epic emerged from a structured brainstorming session (January 14, 2026) that explored:

1. **Primary Control Trigger:** Selected multi-signal fusion (humidity + CO₂ + VOC)
2. **Humidity Management:** Identified 3-tier escalation (fan → dehumidifier → cooling coil)
3. **Cooling Integration:** Clarified that relay directly controls circulation pump to HP buffer
4. **Buffer Availability:** Simplified to "assume available in Summer Mode"
5. **Pump Protection:** Agreed on 5min ON / 10min OFF minimums
6. **Humidity Scope:** All 8 rooms (bedrooms impact radiant cooling effectiveness)

Key insight: MEV cooling integration is a **dehumidification tool**, not just ventilation—it draws chilled water through a coil to condense moisture from the air.
