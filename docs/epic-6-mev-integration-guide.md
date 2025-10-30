# Epic 6: MEV Home Assistant Integration Guide

**System:** First Floor MEV (Mechanical Extract Ventilation)  
**Board:** KC868-A6 ESPHome  
**Version:** 1.0  
**Date:** October 30, 2025

---

## Overview

This guide explains how to integrate the MEV Primo Piano board with Home Assistant for intelligent ventilation automation. The system follows the Epic 5 pattern: the board exposes control entities, Home Assistant provides all intelligence and automation logic.

---

## Exposed Entities

The MEV board exposes **6 entities** to Home Assistant:

### 1. Power Switch
**Entity ID:** `switch.mev_primo_piano_power`  
**Type:** Switch  
**Icon:** mdi:power

**Purpose:** Controls main MEV unit power

**States:**
- `on` - MEV unit powered and running
- `off` - MEV unit powered off

**Usage:**
```yaml
# Turn on MEV
service: switch.turn_on
target:
  entity_id: switch.mev_primo_piano_power

# Turn off MEV
service: switch.turn_off
target:
  entity_id: switch.mev_primo_piano_power
```

**Automation Example:**
```yaml
# Auto-start MEV during daytime
automation:
  - alias: "MEV Morning Start"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.house_occupied
        state: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.mev_primo_piano_power
```

---

### 2. Winter/Summer Mode Switch
**Entity ID:** `switch.mev_primo_piano_mode`  
**Type:** Switch  
**Icon:** mdi:thermometer

**Purpose:** Switches MEV between winter and summer operating modes

**States:**
- `on` - Summer mode (typically heat recovery OFF)
- `off` - Winter mode (typically heat recovery ON)

**Usage:**
```yaml
# Set summer mode
service: switch.turn_on
target:
  entity_id: switch.mev_primo_piano_mode

# Set winter mode
service: switch.turn_off
target:
  entity_id: switch.mev_primo_piano_mode
```

**Automation Example:**
```yaml
# Automatic seasonal mode switching
automation:
  - alias: "MEV Auto Season Mode"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temperature
        above: 22
        for:
          hours: 6
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.mev_primo_piano_mode
    
  - alias: "MEV Auto Winter Mode"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temperature
        below: 18
        for:
          hours: 6
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.mev_primo_piano_mode
```

---

### 3. Dehumidifier Switch
**Entity ID:** `switch.mev_primo_piano_dehumidifier`  
**Type:** Switch  
**Icon:** mdi:water-percent

**Purpose:** Activates integrated dehumidifier function

**States:**
- `on` - Dehumidifier active
- `off` - Normal ventilation mode

**Usage:**
```yaml
# Enable dehumidifier
service: switch.turn_on
target:
  entity_id: switch.mev_primo_piano_dehumidifier

# Disable dehumidifier
service: switch.turn_off
target:
  entity_id: switch.mev_primo_piano_dehumidifier
```

**Automation Example:**
```yaml
# Humidity-triggered dehumidifier
automation:
  - alias: "MEV Dehumidifier Auto"
    trigger:
      - platform: numeric_state
        entity_id: sensor.first_floor_average_humidity
        above: 65
        for:
          minutes: 10
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.mev_primo_piano_dehumidifier
      - service: number.set_value
        target:
          entity_id: number.mev_primo_piano_fan_speed
        data:
          value: 80  # Boost fan speed for dehumidification
    
  - alias: "MEV Dehumidifier Auto Off"
    trigger:
      - platform: numeric_state
        entity_id: sensor.first_floor_average_humidity
        below: 55
        for:
          minutes: 15
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.mev_primo_piano_dehumidifier
      - service: number.set_value
        target:
          entity_id: number.mev_primo_piano_fan_speed
        data:
          value: 40  # Return to normal speed
```

---

### 4. Cooling Integration Switch
**Entity ID:** `switch.mev_primo_piano_cooling`  
**Type:** Switch  
**Icon:** mdi:snowflake

**Purpose:** Enables MEV integration with cooling/AC system

**States:**
- `on` - Cooling coordination active
- `off` - Independent ventilation operation

**Usage:**
```yaml
# Enable cooling integration
service: switch.turn_on
target:
  entity_id: switch.mev_primo_piano_cooling

# Disable cooling integration
service: switch.turn_off
target:
  entity_id: switch.mev_primo_piano_cooling
```

**Automation Example:**
```yaml
# Coordinate with AC system
automation:
  - alias: "MEV AC Coordination"
    trigger:
      - platform: state
        entity_id: climate.first_floor_ac
        to: "cool"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.mev_primo_piano_cooling
      - service: number.set_value
        target:
          entity_id: number.mev_primo_piano_fan_speed
        data:
          value: 60  # Moderate speed during cooling
    
  - alias: "MEV AC Coordination Off"
    trigger:
      - platform: state
        entity_id: climate.first_floor_ac
        to: "off"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.mev_primo_piano_cooling
```

---

### 5. Fan Speed Control
**Entity ID:** `number.mev_primo_piano_fan_speed`  
**Type:** Number (Slider)  
**Icon:** mdi:fan  
**Unit:** %

**Purpose:** Controls MEV fan speed continuously from 0-100%

**Range:** 0-100 (maps to 0-10V DAC output)  
**Step:** 1%

**Usage:**
```yaml
# Set specific fan speed
service: number.set_value
target:
  entity_id: number.mev_primo_piano_fan_speed
data:
  value: 60  # 60% = 6V

# Increment fan speed
service: number.increment
target:
  entity_id: number.mev_primo_piano_fan_speed

# Decrement fan speed
service: number.decrement
target:
  entity_id: number.mev_primo_piano_fan_speed
```

**Automation Example - Humidity-Based Control:**
```yaml
automation:
  - alias: "MEV Fan Speed - Humidity Response"
    mode: restart
    trigger:
      - platform: state
        entity_id: sensor.first_floor_average_humidity
    action:
      - choose:
          # High humidity - boost ventilation
          - conditions:
              - condition: numeric_state
                entity_id: sensor.first_floor_average_humidity
                above: 65
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.mev_primo_piano_fan_speed
                data:
                  value: 80
          
          # Moderate humidity - standard ventilation
          - conditions:
              - condition: numeric_state
                entity_id: sensor.first_floor_average_humidity
                above: 55
                below: 65
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.mev_primo_piano_fan_speed
                data:
                  value: 50
          
          # Low humidity - minimal ventilation
          - conditions:
              - condition: numeric_state
                entity_id: sensor.first_floor_average_humidity
                below: 55
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.mev_primo_piano_fan_speed
                data:
                  value: 30
```

**Automation Example - Time-Based Profiles:**
```yaml
automation:
  - alias: "MEV Fan Speed - Daily Profile"
    trigger:
      - platform: time
        at:
          - "07:00:00"  # Morning boost
          - "09:00:00"  # Day standard
          - "22:00:00"  # Night reduced
    action:
      - choose:
          - conditions:
              - condition: time
                after: "07:00:00"
                before: "09:00:00"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.mev_primo_piano_fan_speed
                data:
                  value: 70  # Morning boost
          
          - conditions:
              - condition: time
                after: "09:00:00"
                before: "22:00:00"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.mev_primo_piano_fan_speed
                data:
                  value: 45  # Day standard
          
          - conditions:
              - condition: time
                after: "22:00:00"
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.mev_primo_piano_fan_speed
                data:
                  value: 25  # Night quiet
```

---

### 6. Alarm Sensor
**Entity ID:** `binary_sensor.mev_primo_piano_alarm`  
**Type:** Binary Sensor  
**Device Class:** problem  
**Icon:** mdi:alert-circle

**Purpose:** Monitors MEV unit alarm/fault condition

**States:**
- `on` - Alarm active (problem detected)
- `off` - Normal operation

**Automation Example:**
```yaml
# MEV alarm notification
automation:
  - alias: "MEV Alarm Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.mev_primo_piano_alarm
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ MEV System Alarm"
          message: "First floor ventilation system has triggered an alarm. Check immediately."
          data:
            priority: high
            ttl: 0
      - service: persistent_notification.create
        data:
          title: "MEV System Alarm"
          message: "Check first floor MEV unit - alarm condition detected"
      - service: light.turn_on  # Optional: visual indicator
        target:
          entity_id: light.status_led
        data:
          rgb_color: [255, 0, 0]
          brightness: 255
```

---

## Complete Automation Examples

### Intelligent Humidity-Based Ventilation

This automation combines multiple entities for comprehensive humidity management:

```yaml
automation:
  - alias: "MEV Intelligent Humidity Control"
    mode: restart
    trigger:
      - platform: state
        entity_id:
          - sensor.bathroom_1_humidity
          - sensor.bathroom_2_humidity
          - sensor.bathroom_3_humidity
          - sensor.laundry_humidity
    action:
      # Calculate max humidity across wet rooms
      - variables:
          max_humidity: >
            {% set humidities = [
              states('sensor.bathroom_1_humidity') | float(0),
              states('sensor.bathroom_2_humidity') | float(0),
              states('sensor.bathroom_3_humidity') | float(0),
              states('sensor.laundry_humidity') | float(0)
            ] %}
            {{ humidities | max }}
      
      # Ensure MEV is powered on if needed
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ max_humidity > 60 }}"
              - condition: state
                entity_id: switch.mev_primo_piano_power
                state: "off"
            sequence:
              - service: switch.turn_on
                target:
                  entity_id: switch.mev_primo_piano_power
              - delay:
                  seconds: 5
      
      # Set appropriate fan speed
      - service: number.set_value
        target:
          entity_id: number.mev_primo_piano_fan_speed
        data:
          value: >
            {% if max_humidity > 75 %}
              100
            {% elif max_humidity > 65 %}
              80
            {% elif max_humidity > 55 %}
              50
            {% else %}
              30
            {% endif %}
      
      # Enable dehumidifier if very high humidity
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ max_humidity > 70 }}"
            sequence:
              - service: switch.turn_on
                target:
                  entity_id: switch.mev_primo_piano_dehumidifier
        default:
          - service: switch.turn_off
            target:
              entity_id: switch.mev_primo_piano_dehumidifier
```

### Air Quality Response

Integrate with CO2/VOC sensors for air quality management:

```yaml
automation:
  - alias: "MEV Air Quality Response"
    mode: restart
    trigger:
      - platform: numeric_state
        entity_id: sensor.first_floor_co2
        above: 1000
        for:
          minutes: 5
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.mev_primo_piano_power
      - service: number.set_value
        target:
          entity_id: number.mev_primo_piano_fan_speed
        data:
          value: 75  # Boost for air quality
      - delay:
          minutes: 30
      - service: number.set_value
        target:
          entity_id: number.mev_primo_piano_fan_speed
        data:
          value: 40  # Return to normal
```

### Post-Shower Boost

Bathroom-specific humidity boost:

```yaml
automation:
  - alias: "MEV Post-Shower Boost"
    trigger:
      - platform: numeric_state
        entity_id:
          - sensor.bathroom_1_humidity
          - sensor.bathroom_2_humidity
          - sensor.bathroom_3_humidity
        above: 70
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.mev_primo_piano_power
      - service: number.set_value
        target:
          entity_id: number.mev_primo_piano_fan_speed
        data:
          value: 90
      - wait_for_trigger:
          - platform: numeric_state
            entity_id: "{{ trigger.entity_id }}"
            below: 60
        timeout:
          hours: 2
      - service: number.set_value
        target:
          entity_id: number.mev_primo_piano_fan_speed
        data:
          value: 40
```

---

## Dashboard Configuration

### Lovelace Card Examples

**Entities Card:**
```yaml
type: entities
title: MEV Primo Piano
entities:
  - entity: switch.mev_primo_piano_power
    name: Power
  - entity: switch.mev_primo_piano_mode
    name: Season Mode
    state_color: true
  - entity: number.mev_primo_piano_fan_speed
    name: Fan Speed
  - entity: switch.mev_primo_piano_dehumidifier
    name: Dehumidifier
  - entity: switch.mev_primo_piano_cooling
    name: AC Integration
  - entity: binary_sensor.mev_primo_piano_alarm
    name: System Status
```

**Gauge Card (Fan Speed):**
```yaml
type: gauge
entity: number.mev_primo_piano_fan_speed
name: MEV Fan Speed
unit: "%"
min: 0
max: 100
severity:
  green: 0
  yellow: 50
  red: 80
```

**Conditional Card (Alarm):**
```yaml
type: conditional
conditions:
  - entity: binary_sensor.mev_primo_piano_alarm
    state: "on"
card:
  type: markdown
  content: |
    ## ⚠️ MEV System Alarm
    Check first floor ventilation unit immediately.
  card_mod:
    style: |
      ha-card {
        background: rgba(255,0,0,0.1);
        border: 2px solid red;
      }
```

**Complete Control Card:**
```yaml
type: vertical-stack
cards:
  - type: entities
    title: MEV Control
    entities:
      - entity: switch.mev_primo_piano_power
      - type: divider
      - entity: number.mev_primo_piano_fan_speed
      - type: divider
      - entity: switch.mev_primo_piano_mode
        name: Winter/Summer
      - entity: switch.mev_primo_piano_dehumidifier
      - entity: switch.mev_primo_piano_cooling
  
  - type: conditional
    conditions:
      - entity: binary_sensor.mev_primo_piano_alarm
        state: "on"
    card:
      type: markdown
      content: "## ⚠️ System Alarm Active"
  
  - type: history-graph
    title: Fan Speed History
    hours_to_show: 24
    entities:
      - entity: number.mev_primo_piano_fan_speed
```

---

## Troubleshooting

### Issue: Entities not appearing in Home Assistant

**Symptoms:** MEV entities don't show up after board installation

**Solutions:**
1. Verify board is connected to WiFi (check ESPHome dashboard)
2. Check Home Assistant → Settings → Devices → ESPHome → Add Integration
3. Verify board name matches: `mev-primo-piano`
4. Check logs: Settings → System → Logs → Filter "esphome"
5. Try restarting Home Assistant core

---

### Issue: Switch commands don't control MEV

**Symptoms:** Switches toggle in HA but MEV doesn't respond

**Solutions:**
1. Verify physical wiring connections (see wiring diagram)
2. Check relay operation with multimeter
3. Verify MEV unit is powered independently
4. Check ESPHome logs for errors: `esphome logs locals/mev-primo-piano.yaml`
5. Verify relay contact ratings match MEV requirements

---

### Issue: Fan speed doesn't affect MEV

**Symptoms:** Number slider changes but fan speed stays constant

**Solutions:**
1. Measure DAC output voltage with multimeter (should vary 0-10V)
2. Verify 0-10V wire connections (polarity correct?)
3. Check for ground loops (shield connected at one end only)
4. Verify MEV 0-10V input impedance is >10kΩ
5. Test with static values: 0%, 50%, 100%

---

### Issue: Alarm sensor always "on"

**Symptoms:** Alarm binary sensor constantly shows "problem"

**Solutions:**
1. Check alarm wire isn't shorted to ground
2. Verify MEV alarm output type (dry contact vs voltage)
3. Measure voltage at INPUT1 (should be 3.3V when open)
4. May need to invert logic in component if MEV uses inverse logic
5. Temporarily disconnect alarm wire to verify sensor works

---

### Issue: Automations not triggering

**Symptoms:** Manual control works but automations don't run

**Solutions:**
1. Check automation mode (single/restart/parallel/queued)
2. Verify trigger conditions are met
3. Check automation traces: Settings → Automations → [Select] → Traces
4. Enable automation if disabled
5. Check for conflicting automations

---

## Best Practices

### Performance
- **Avoid rapid changes:** Limit fan speed adjustments to every 30-60 seconds
- **Use debouncing:** Add `for:` delays to humidity triggers to avoid oscillation
- **Mode setting:** Use `mode: restart` for automations that should override themselves

### Reliability
- **Test autonomous operation:** Disconnect HA and verify board maintains last settings
- **Implement failsafes:** Always have manual override capability
- **Monitor alarms:** Ensure alarm notifications reach multiple recipients

### Energy Efficiency
- **Seasonal optimization:** Adjust fan speeds based on outdoor temperature
- **Occupancy awareness:** Reduce ventilation when house is unoccupied
- **Coordinate with HVAC:** Don't fight heating/cooling systems with excessive ventilation

---

## Revision History

| Version | Date         | Changes                                |
|---------|--------------|----------------------------------------|
| 1.0     | Oct 30, 2025 | Initial integration guide created      |

---

**Need Help?** Check ESPHome logs, HA automation traces, and refer to the wiring diagram for physical troubleshooting.
