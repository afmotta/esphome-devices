# Epic 8: Condition Interface Specification

**Document Version:** 1.0  
**Date:** October 31, 2025  
**Status:** Draft  
**Epic:** 8 - Unified State Machine Architecture

---

## Purpose

This document defines the **mandatory interface contract** that all shutdown condition components must implement to work with the `room_control_coordinator.yaml` component. This contract ensures conditions can be developed independently while remaining interoperable through a standardized communication protocol.

**Key Principle:** Conditions are "dumb sensors" that detect and report state; the coordinator is the "smart engine" that interprets state and controls equipment.

---

## Interface Contract Overview

Each condition component MUST expose exactly **two globals** per room:

1. **State Global** - Tri-state enum representing condition operational state
2. **Priority Global** - Integer representing condition importance in hierarchy

These globals serve as the "event bus" through which conditions publish their state to the coordinator.

---

## Required Globals

### 1. State Global

**Naming Convention:**
```yaml
globals:
  - id: ${zone_slug}_${condition_id}_state
    type: int
    restore_value: false
    initial_value: "0"
```

**Parameters:**
- `${zone_slug}` - Room identifier (e.g., `soggiorno`, `bagno_grande`)
- `${condition_id}` - Condition identifier (e.g., `emergency`, `window`, `occupancy`)

**State Enum Values:**

| Value | State Name     | Semantic Meaning                                 | Coordinator Action                                  |
| ----- | -------------- | ------------------------------------------------ | --------------------------------------------------- |
| `0`   | **Normal**     | Condition not triggered; room operating normally | No action; PID operates per HA climate entity state |
| `1`   | **Active**     | Condition triggered; shutdown required           | Force PID to OFF mode                               |
| `2`   | **Recovering** | Condition cleared; stability period in progress  | Keep PID OFF until recovery completes               |

**State Transitions:**

```
Normal (0) ──[trigger detected + timeout exceeded]──> Active (1)
Active (1) ──[condition clears]──> Recovering (2)
Recovering (2) ──[stability timeout completes]──> Normal (0)
Recovering (2) ──[condition re-triggers]──> Active (1)
```

**Implementation Rules:**
- Condition MUST set state to `1` (Active) when trigger condition persists beyond configured timeout
- Condition MUST set state to `2` (Recovering) immediately when trigger condition clears while in Active state
- Condition MUST set state back to `0` (Normal) after recovery stability period completes
- State MUST be updated within one condition check interval (typically 5-10s)
- State MUST NOT transition directly from Active (1) to Normal (0) without passing through Recovering (2)

---

### 2. Priority Global

**Naming Convention:**
```yaml
globals:
  - id: ${zone_slug}_${condition_id}_priority
    type: int
    restore_value: false
    initial_value: "${priority_value}"
```

**Priority Hierarchy:**

| Priority | Condition Type                  | Rationale                                                      |
| -------- | ------------------------------- | -------------------------------------------------------------- |
| `1`      | **Emergency** (sensor failure)  | Safety-critical; sensor data invalid, cannot operate safely    |
| `2`      | **Window** (open window)        | Energy efficiency; heating/cooling outdoor air is wasteful     |
| `3`      | **Occupancy** (room unoccupied) | Energy savings; no one present to benefit from climate control |
| `4+`     | Future conditions               | Reserved for future expansion                                  |

**Priority Rules:**
- **Lower number = Higher priority** (1 is highest, 2 is second, etc.)
- When multiple conditions are Active simultaneously, coordinator applies action for **highest priority** condition (lowest number)
- Priority values MUST be unique per room (no two conditions with same priority)
- Priority values MUST be static (not change at runtime) for MVP
- Valid range: `1-99` (allows 99 future condition types)

**Implementation Rules:**
- Priority global MUST be set to a constant value at component initialization
- Priority MUST NOT change during runtime (static hierarchy for MVP)
- Coordinator will ignore conditions with invalid priorities (0, negative, >99)

---

## Optional Debugging Globals

Conditions SHOULD expose additional globals for debugging and diagnostics:

### Last Trigger Timestamp

```yaml
globals:
  - id: ${zone_slug}_${condition_id}_last_trigger_time
    type: unsigned long
    restore_value: false
    initial_value: "0"
```

**Purpose:** Record `millis()` timestamp when condition last transitioned to Active state.

**Use Case:** Post-mortem debugging, diagnostic sensors showing "last triggered X minutes ago"

---

### Trigger Count

```yaml
globals:
  - id: ${zone_slug}_${condition_id}_trigger_count
    type: int
    restore_value: false
    initial_value: "0"
```

**Purpose:** Count total number of times condition has triggered since boot.

**Use Case:** Frequency analysis, detect flapping conditions

---

## Diagnostic Text Sensor (Required)

Each condition MUST expose a `text_sensor` showing its current state for HA dashboard visibility:

```yaml
text_sensor:
  - platform: template
    id: ${zone_slug}_${condition_id}_state_sensor
    name: "${zone_name} ${condition_name} State"
    icon: "mdi:state-machine"
    update_interval: 5s
    lambda: |-
      int state = id(${zone_slug}_${condition_id}_state);
      if (state == 0) {
        return {"Normal"};
      } else if (state == 1) {
        return {"Active"};
      } else if (state == 2) {
        return {"Recovering"};
      } else {
        return {"Unknown"};
      }
```

**Naming Convention:**
- ID: `${zone_slug}_${condition_id}_state_sensor`
- Name: `"${zone_name} ${condition_name} State"` (e.g., "Soggiorno Emergency State")

**Display Values:**
- `"Normal"` - Condition not triggered
- `"Active"` - Condition triggered, shutdown active
- `"Recovering"` - Condition cleared, stability period
- `"Unknown"` - Invalid state (should never occur)

---

## Complete Example: Emergency Condition

Here's a complete example showing interface compliance:

```yaml
# File: components/room_emergency_condition.yaml
# Purpose: Detect HA sensor failures and expose state+priority to coordinator
# Interface: Epic 8 Condition Contract v1.0

# Required vars:
#   - zone_slug: Room identifier (e.g., "soggiorno")
#   - zone_name: Display name (e.g., "Soggiorno")
#   - ha_temperature_sensor_id: HA entity ID for temperature sensor
#   - emergency_timeout: Seconds before triggering (default: 180)
#   - recovery_timeout: Seconds of stability before Normal (default: 60)

defaults:
  emergency_timeout: 180
  recovery_timeout: 60
  condition_id: "emergency"
  priority_value: 1

# ============================================================================
# INTERFACE CONTRACT: Required Globals
# ============================================================================

globals:
  # State: 0=Normal, 1=Active, 2=Recovering
  - id: ${zone_slug}_${condition_id}_state
    type: int
    restore_value: false
    initial_value: "0"
  
  # Priority: 1=highest (emergency is most critical)
  - id: ${zone_slug}_${condition_id}_priority
    type: int
    restore_value: false
    initial_value: "${priority_value}"
  
  # Optional debugging: Last trigger timestamp
  - id: ${zone_slug}_${condition_id}_last_trigger_time
    type: unsigned long
    restore_value: false
    initial_value: "0"
  
  # Internal state management (not part of interface)
  - id: ${zone_slug}_last_valid_sensor_time
    type: unsigned long
    restore_value: false
    initial_value: "0"
  
  - id: ${zone_slug}_recovery_start_time
    type: unsigned long
    restore_value: false
    initial_value: "0"

# ============================================================================
# CONDITION DETECTION LOGIC
# ============================================================================

sensor:
  - platform: homeassistant
    entity_id: ${ha_temperature_sensor_id}
    id: ${zone_slug}_ha_temperature
    internal: true
    on_value:
      then:
        - lambda: |-
            id(${zone_slug}_last_valid_sensor_time) = millis();

# ============================================================================
# STATE MACHINE
# ============================================================================

interval:
  - interval: 10s
    then:
      - lambda: |-
          unsigned long now = millis();
          int current_state = id(${zone_slug}_${condition_id}_state);
          
          // Check if sensor is available
          bool sensor_valid = false;
          if (id(${zone_slug}_ha_temperature).has_state()) {
            float value = id(${zone_slug}_ha_temperature).state;
            if (!isnan(value)) {
              sensor_valid = true;
            }
          }
          
          unsigned long time_since_valid = (now - id(${zone_slug}_last_valid_sensor_time)) / 1000;
          
          if (!sensor_valid && time_since_valid >= ${emergency_timeout}) {
            // Sensor failed, trigger emergency
            if (current_state == 0) {
              // Transition: Normal -> Active
              id(${zone_slug}_${condition_id}_state) = 1;
              id(${zone_slug}_${condition_id}_last_trigger_time) = now;
              ESP_LOGW("condition", "${zone_name}: Emergency ACTIVE (sensor unavailable ${emergency_timeout}s)");
            } else if (current_state == 2) {
              // Transition: Recovering -> Active (sensor failed again)
              id(${zone_slug}_${condition_id}_state) = 1;
              id(${zone_slug}_recovery_start_time) = 0;
              ESP_LOGW("condition", "${zone_name}: Emergency re-triggered during recovery");
            }
            // else: already Active, no change
            
          } else if (sensor_valid) {
            // Sensor is valid
            if (current_state == 1) {
              // Transition: Active -> Recovering
              id(${zone_slug}_${condition_id}_state) = 2;
              id(${zone_slug}_recovery_start_time) = now;
              ESP_LOGI("condition", "${zone_name}: Emergency RECOVERING (sensor restored)");
              
            } else if (current_state == 2) {
              // Check if recovery period complete
              unsigned long recovery_duration = (now - id(${zone_slug}_recovery_start_time)) / 1000;
              if (recovery_duration >= ${recovery_timeout}) {
                // Transition: Recovering -> Normal
                id(${zone_slug}_${condition_id}_state) = 0;
                id(${zone_slug}_recovery_start_time) = 0;
                ESP_LOGI("condition", "${zone_name}: Emergency NORMAL (recovery complete)");
              }
            }
            // else: already Normal, no change
          }

# ============================================================================
# INTERFACE CONTRACT: Required Diagnostic Sensor
# ============================================================================

text_sensor:
  - platform: template
    id: ${zone_slug}_${condition_id}_state_sensor
    name: "${zone_name} Emergency State"
    icon: "mdi:alert-circle"
    update_interval: 5s
    lambda: |-
      int state = id(${zone_slug}_${condition_id}_state);
      if (state == 0) {
        return {"Normal"};
      } else if (state == 1) {
        return {"Active"};
      } else if (state == 2) {
        return {"Recovering"};
      } else {
        return {"Unknown"};
      }
```

---

## Coordinator Consumption Pattern

The coordinator reads condition globals as follows:

```yaml
interval:
  - interval: 5s
    then:
      - lambda: |-
          // Read all condition states
          int emergency_state = id(${zone_slug}_emergency_state);
          int emergency_priority = id(${zone_slug}_emergency_priority);
          
          int window_state = id(${zone_slug}_window_state);
          int window_priority = id(${zone_slug}_window_priority);
          
          // Find highest priority active condition
          int highest_priority_active = 99;  // No active condition
          std::string active_condition_name = "None";
          
          if (emergency_state == 1 || emergency_state == 2) {
            if (emergency_priority < highest_priority_active) {
              highest_priority_active = emergency_priority;
              active_condition_name = "Emergency";
            }
          }
          
          if (window_state == 1 || window_state == 2) {
            if (window_priority < highest_priority_active) {
              highest_priority_active = window_priority;
              active_condition_name = "Window";
            }
          }
          
          // Apply control action
          auto pid = id(${pid_id});
          if (highest_priority_active < 99) {
            // At least one condition is active or recovering
            if (pid->mode != climate::CLIMATE_MODE_OFF) {
              ESP_LOGW("coordinator", "${zone_name}: Shutdown due to %s", active_condition_name.c_str());
              auto call = pid->make_call();
              call.set_mode(climate::CLIMATE_MODE_OFF);
              call.perform();
            }
          } else {
            // All conditions normal - PID resumes based on HA state
            ESP_LOGV("coordinator", "${zone_name}: Normal - all conditions clear");
          }
```

---

## Contract Compliance Checklist

Use this checklist to validate condition components:

### Required Elements

- [ ] **State global** defined: `${zone_slug}_${condition_id}_state`
- [ ] **State global** type is `int`
- [ ] **State global** initial value is `"0"`
- [ ] **Priority global** defined: `${zone_slug}_${condition_id}_priority`
- [ ] **Priority global** type is `int`
- [ ] **Priority global** value is in range 1-99
- [ ] **Priority global** value is unique per room
- [ ] **Text sensor** defined showing state as "Normal"/"Active"/"Recovering"
- [ ] **Text sensor** update interval ≤ 10s

### State Machine Behavior

- [ ] Condition transitions to **Active (1)** when trigger persists beyond timeout
- [ ] Condition transitions to **Recovering (2)** when trigger clears from Active
- [ ] Condition transitions to **Normal (0)** after recovery stability period
- [ ] State updates within 10 seconds of transition trigger
- [ ] No direct Active → Normal transition (must pass through Recovering)

### Logging & Observability

- [ ] Log messages at state transitions (INFO/WARN level)
- [ ] Log messages include zone name and new state
- [ ] Optional: Last trigger timestamp tracked
- [ ] Optional: Trigger count tracked

### Documentation

- [ ] Component header documents required vars
- [ ] Component header references this interface spec version
- [ ] Example usage provided in component or docs

---

## Version History

| Version | Date         | Changes                                        |
| ------- | ------------ | ---------------------------------------------- |
| 1.0     | Oct 31, 2025 | Initial interface specification for Epic 8 MVP |

---

## Future Considerations

Items deferred to post-MVP:

- **Dynamic priorities:** Context-aware priority adjustment (Epic 10+)
- **Bidirectional communication:** Coordinator signals to conditions (e.g., "master disable")
- **Condition registration:** Auto-discovery vs. explicit configuration
- **State validation:** Coordinator validates state transitions are legal
- **Timeout overrides:** Per-room timeout configuration via coordinator vars
- **Mode-awareness coordination:** Centralized vs. per-condition mode logic

---

**Document Status:** Ready for implementation  
**Next Steps:** Use this spec to refactor `room_sensors.yaml` (emergency) and `room_window_detection.yaml` (window) components

---

*Interface specification created for Epic 8: Unified State Machine Architecture*
