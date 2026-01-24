# Epic 8: Coordinator State Machine Engine Design

**Document Version:** 1.0  
**Date:** October 31, 2025  
**Status:** Draft  
**Epic:** 8 - Unified State Machine Architecture  
**Dependencies:** epic-8-condition-interface-spec.md v1.0

---

## Purpose

This document specifies the design of the **Room Control Coordinator** component (`room_control_coordinator.yaml`), a stateless aggregation engine that:

1. Reads condition states from multiple condition components
2. Applies priority hierarchy to determine active condition
3. Controls PID climate entity based on highest-priority condition
4. Provides diagnostic observability into coordination decisions

**Key Principle:** The coordinator is a "stateless smart engine" — all state lives in condition components; the coordinator reads, aggregates, and acts.

---

## Architecture Overview

### Component Responsibility Model

The coordinator operates as the central control point in a room's climate control ecosystem, reading state from independent condition components and making unified PID control decisions.

**Coordination Pattern:**
- **Conditions (Emergency, Window, Occupancy):** Detect trigger events, manage state transitions (Normal/Active/Recovering), publish state+priority to globals
- **Coordinator:** Polls condition globals every 5s, applies priority hierarchy, controls PID based on highest-priority active condition
- **PID Climate Entity:** Receives control commands from coordinator (force OFF when conditions trigger, resume when clear)

---

## State Aggregation Algorithm

### Priority Resolution Logic

The coordinator uses a simple min-priority selection algorithm to determine which condition should control PID behavior:

**Algorithm Steps:**
1. Read all condition state+priority globals
2. Filter conditions where state > 0 (Active or Recovering)
3. Among filtered conditions, select the one with lowest priority number (highest importance)
4. Apply control action based on selected condition

**Pseudocode:**

```cpp
int highest_priority_value = 99;  // Sentinel: no active condition
string active_condition_id = "None";

// Check emergency condition
int emergency_state = id(zone_emergency_state);
int emergency_priority = id(zone_emergency_priority);
if (emergency_state > 0 && emergency_priority < highest_priority_value) {
  highest_priority_value = emergency_priority;
  active_condition_id = "Emergency";
}

// Check window condition
int window_state = id(zone_window_state);
int window_priority = id(zone_window_priority);
if (window_state > 0 && window_priority < highest_priority_value) {
  highest_priority_value = window_priority;
  active_condition_id = "Window";
}

// Determine action
bool shutdown_required = (highest_priority_value < 99);
```

### State Transition Matrix

| Highest Priority State | Current PID Mode | Coordinator Action       | Rationale                                 |
| ---------------------- | ---------------- | ------------------------ | ----------------------------------------- |
| **All Normal (0)**     | OFF              | Resume to HA state       | Conditions clear; restore climate control |
| **All Normal (0)**     | Heating/Cooling  | No action                | Already operating normally                |
| **Any Active (1)**     | Heating/Cooling  | Force to OFF             | Safety/efficiency requires shutdown       |
| **Any Active (1)**     | OFF              | No action (maintain OFF) | Already shut down                         |
| **Any Recovering (2)** | Heating/Cooling  | Force to OFF             | Stability period, keep shutdown           |
| **Any Recovering (2)** | OFF              | No action (maintain OFF) | Wait for recovery completion              |

---

## PID Control Decision Tree

```
START: Coordinator Interval (5s)
│
├─ Read condition states/priorities
│
├─ Apply priority resolution
│  └─ Find highest priority (lowest number) with state > 0
│
├─ Any condition active/recovering?
│  │
│  ├─ YES → Check PID mode
│  │  ├─ PID = OFF → No action (log: "Shutdown maintained")
│  │  └─ PID = ON → Force PID to OFF (log: "Shutdown triggered")
│  │
│  └─ NO → All conditions normal
│     ├─ PID = OFF → Resume via HA automation (MVP)
│     └─ PID = ON → No action (log: "Normal operation")
│
END: Update diagnostic sensor
```

### Edge Cases

#### 1. Simultaneous Triggers
**Scenario:** Emergency and window both trigger within same interval.
**Resolution:** Priority hierarchy (Emergency=1 < Window=2) determines which is reported. PID remains OFF regardless.

#### 2. Recovery Interruption
**Scenario:** Emergency recovering, window triggers.
**Resolution:** Window becomes active condition (if higher priority after emergency clears). PID stays OFF throughout.

#### 3. Invalid Priority
**Scenario:** Condition has priority=0 or >99.
**Resolution:** Log warning, ignore that condition, process remaining valid conditions.

---

## Diagnostic Observability

### Diagnostic Text Sensor

```yaml
text_sensor:
  - platform: template
    id: ${zone_slug}_coordinator_status
    name: "${zone_name} Control Status"
    icon: "mdi:state-machine"
    update_interval: 5s
    lambda: |-
      int emergency_state = id(${zone_slug}_emergency_state);
      int window_state = id(${zone_slug}_window_state);
      
      if (emergency_state > 0) {
        string state_name = (emergency_state == 1) ? "Active" : "Recovering";
        return {"Shutdown: Emergency (" + state_name + ")"};
      }
      
      if (window_state > 0) {
        string state_name = (window_state == 1) ? "Active" : "Recovering";
        return {"Shutdown: Window (" + state_name + ")"};
      }
      
      return {"Normal (All Clear)"};
```

**Example Outputs:**
- `"Normal (All Clear)"` — All conditions normal
- `"Shutdown: Emergency (Active)"` — Sensor failed, PID OFF
- `"Shutdown: Window (Recovering)"` — Window closed, waiting for stability
  
---

## HA Resume Strategy (MVP)

**MVP Approach:** HA-Driven Resume

The coordinator forces PID OFF when conditions trigger but does NOT automatically resume PID when conditions clear. Instead, a Home Assistant automation monitors coordinator status and resumes climate control.

**Rationale:**
- Simpler coordinator implementation
- Leverages existing HA automation infrastructure
- HA knows desired climate mode better than ESPHome

**HA Automation Example:**

```yaml
automation:
  - alias: "Resume Climate After Conditions Clear"
    trigger:
      - platform: state
        entity_id: text_sensor.soggiorno_coordinator_status
        to: "Normal (All Clear)"
        for: "00:00:30"
    action:
      - service: climate.set_hvac_mode
        target:
          entity_id: climate.soggiorno_pid
        data:
          hvac_mode: "heat"  # Or dynamic based on season/time
```

---

## Component Interface

### Required Variables

```yaml
vars:
  zone_slug: string         # Room identifier (e.g., "soggiorno")
  zone_name: string         # Display name (e.g., "Soggiorno")
  pid_id: string            # PID climate entity ID
```

### Exposed Sensors

```yaml
text_sensor:
  - id: ${zone_slug}_coordinator_status
    name: "${zone_name} Control Status"
```

---

## Performance Characteristics

| Parameter             | Value      | Impact                                                      |
| --------------------- | ---------- | ----------------------------------------------------------- |
| Coordinator interval  | 5s         | Balance responsiveness vs CPU                               |
| Max detection latency | 15s        | Worst case: condition@T=0, coordinator@T=5, next check@T=10 |
| Shutdown propagation  | <1s        | PID OFF executes immediately                                |
| Memory per room       | ~134 bytes | Negligible on ESP32                                         |
| CPU utilization       | 0.2%       | <10ms every 5s                                              |

---

## Testing Strategy

### Unit Tests

1. **Single Condition Active:** emergency=1, window=0 → PID OFF, diagnostic="Shutdown: Emergency (Active)"
2. **Multiple Conditions:** emergency=1, window=1 → PID OFF, diagnostic="Shutdown: Emergency (Active)" (priority)
3. **All Normal:** emergency=0, window=0 → No PID change, diagnostic="Normal (All Clear)"
4. **Recovery State:** emergency=2, window=0 → PID OFF, diagnostic="Shutdown: Emergency (Recovering)"

### Integration Tests

1. **Emergency Flow:** Disconnect HA sensor → Wait 180s → Verify PID OFF → Reconnect → Wait 60s → Verify resume
2. **Window Flow:** Open window → Wait 180s → Verify PID OFF → Close window → Wait 60s → Verify resume
3. **Cascading:** Trigger both conditions → Clear emergency first → Verify PID stays OFF (window active) → Clear window → Verify resume

---

## Future Enhancements

Post-MVP features:

1. **Dynamic Condition Registration** — Auto-discovery instead of explicit vars
2. **Bidirectional Communication** — Coordinator publishes "master disable" signal
3. **Mode-Aware Coordination** — Window only shuts down cooling, not heating
4. **Advanced Diagnostics** — Countdown timers, trigger history
5. **Coordinator-Driven Resume** — Read HA climate entity, apply target mode directly

---

## Version History

| Version | Date         | Changes                                   |
| ------- | ------------ | ----------------------------------------- |
| 1.0     | Oct 31, 2025 | Initial coordinator design for Epic 8 MVP |

---

## References

- **Interface Specification:** `epic-8-condition-interface-spec.md`
- **Project Brief:** `epic-8-brief.md`
- **Brainstorming Session:** `epic-8-brainstorming-session.md`

---

**Document Status:** Ready for implementation  
**Next Steps:** 
1. Create `components/room_control_coordinator.yaml` based on this design
2. Refactor emergency condition to match interface spec
3. Refactor window condition to match interface spec

---

*Coordinator design created for Epic 8: Unified State Machine Architecture*
