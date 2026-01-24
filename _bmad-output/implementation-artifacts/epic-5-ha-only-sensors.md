# Epic 5: HA-Only Sensor Architecture

## Overview

Epic 5 introduces a simplified 2-tier temperature sensing architecture for room climate control, replacing the previous 3-tier Modbus-based system with a Home Assistant-centric approach that includes automatic emergency shutdown.

### Key Design Principles

1. **Simplicity:** 2 tiers instead of 3 reduces complexity by ~60%
2. **Cost Efficiency:** Leverages existing HA sensors, eliminates Modbus hardware
3. **Safety First:** 3-minute emergency shutdown ensures fail-safe operation
4. **Reliability:** Fewer components = fewer failure points
5. **Maintainability:** Clearer code, better documentation, easier debugging

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Home Assistant                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  sensor.room_bagno_grande_temperature                  │ │
│  │  (Zigbee/WiFi/Z-Wave temperature sensor)              │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │ API
                             ▼
┌─────────────────────────────────────────────────────────────┐
│             ESPHome Device (distribuzione-primo-piano)       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  room_sensors.yaml (v5)                                │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Platform: homeassistant                         │ │ │
│  │  │  Entity: sensor.room_bagno_grande_temperature    │ │ │
│  │  │  ↓                                                │ │ │
│  │  │  State Machine:                                  │ │ │
│  │  │   ┌───────┐  timeout(180s)  ┌───────────┐      │ │ │
│  │  │   │Normal │─────────────────→│ Emergency │      │ │ │
│  │  │   └───────┘                  └───────────┘      │ │ │
│  │  │       ▲                            │             │ │ │
│  │  │       │ stability(60s)             │             │ │ │
│  │  │       │                     │             │ │ │
│  │  │   ┌───────────┐ sensor_fails │             │ │ │
│  │  │   │Recovering │◄─────────────┘             │ │ │
│  │  │   └───────────┘ sensor_ok                  │ │ │
│  │  │       ▲                                     │ │ │
│  │  │       └─────────────────────────────────────┘ │ │
│  │  │                                                │ │ │
│  │  │  Output: sensor.bagno_grande_room_temp_abstracted│ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  room_emergency_shutdown.yaml                    │ │ │
│  │  │  • Monitors emergency_triggered flag             │ │ │
│  │  │  • Forces PID to OFF when emergency              │ │ │
│  │  │  • PID → slow_pwm → relay (automatic OFF)        │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  PID Climate Controller                          │ │ │
│  │  │  • Input: bagno_grande_room_temp_abstracted      │ │ │
│  │  │  • Output: slow_pwm_bagno_grande                 │ │ │
│  │  │  • Mode: Heat/Cool/OFF                           │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Slow PWM Output                                 │ │ │
│  │  │  • turn_on_action: relay_12.turn_on              │ │ │
│  │  │  • turn_off_action: relay_12.turn_off            │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                             │                                │
│                             ▼                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Physical Relay (relay_12)                            │ │
│  │  • Controls radiant floor heating valve                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Component Structure

### room_sensors.yaml (v5)

The core sensor component implementing 2-tier failover logic.

**File:** `components/room_sensors.yaml`  
**Lines of Code:** ~100 (vs. 221 in v4)  
**Complexity:** Low (single HA sensor input, state machine logic)

#### Required Variables

```yaml
vars:
  zone_slug: "bagno_grande"          # Room identifier
  zone_name: "Bagno Grande"          # Display name
  ha_temperature_sensor_id: "sensor.room_bagno_grande_temperature"  # HA entity ID
```

#### Optional Variables (with defaults)

```yaml
vars:
  emergency_timeout: 180             # Seconds before emergency (3 min)
  recovery_stability_timeout: 60     # Seconds of stability for recovery (1 min)
  check_interval: 10                 # Sensor check frequency (10s)
```

#### Exposed Entities

1. **`sensor.{zone}_room_temp_abstracted`** (internal)
   - Device class: `temperature`
   - Unit: `°C`
   - Purpose: Temperature value for PID controller
   - Visibility: Internal (not exposed to HA)
   - Value: HA sensor value OR NaN (during emergency)

2. **`text_sensor.{zone}_sensor_state`** (exposed)
   - Values: "Normal" | "Emergency" | "Recovering"
   - Purpose: Visual indicator of system state
   - Use case: HA dashboard monitoring, automations

3. **`sensor.{zone}_room_sensor_last_update`** (exposed)
   - Device class: `timestamp`
   - Purpose: Shows when last valid sensor data received
   - Use case: Debugging, monitoring sensor freshness

## State Machine

### States

#### 1. Normal

**Characteristics:**
- HA sensor providing valid data
- PID controller operating normally
- Relays under PID control
- `emergency_triggered` = false
- `recovery_start_time` = 0

**Transitions From:**
- Initial state (on boot)
- Recovering state (after stability period)

**Transitions To:**
- Emergency (after timeout with no valid sensor)

#### 2. Emergency

**Characteristics:**
- No valid HA sensor data for >180 seconds
- PID forced to OFF mode
- Relays turned OFF (via PID → slow_pwm chain)
- `emergency_triggered` = true
- `recovery_start_time` = 0

**Transitions From:**
- Normal (after 180s timeout)
- Recovering (if sensor fails during recovery)

**Transitions To:**
- Recovering (when HA sensor becomes valid again)

#### 3. Recovering

**Characteristics:**
- HA sensor providing valid data again
- Waiting for stability confirmation (60 seconds)
- PID still in emergency mode during recovery
- `emergency_triggered` = true
- `recovery_start_time` = current_time

**Transitions From:**
- Emergency (when sensor becomes valid)

**Transitions To:**
- Normal (after 60s of continuous valid sensor data)
- Emergency (if sensor fails again before 60s)

### State Transitions

```
┌─────────────────────────────────────────────────────┐
│                     NORMAL                           │
│  • HA sensor valid                                   │
│  • PID operating                                     │
│  • emergency_triggered = false                       │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ No valid sensor for 180s
                   ▼
┌─────────────────────────────────────────────────────┐
│                   EMERGENCY                          │
│  • No HA sensor data                                 │
│  • PID OFF                                           │
│  • Relays OFF                                        │
│  • emergency_triggered = true                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ HA sensor becomes valid
                   ▼
┌─────────────────────────────────────────────────────┐
│                  RECOVERING                          │
│  • HA sensor valid (monitoring)                      │
│  • Waiting 60s for stability                         │
│  • emergency_triggered = true                        │
│  • recovery_start_time = now                         │
└──────────────────┬────────────┬─────────────────────┘
                   │            │
     60s stability │            │ Sensor fails
                   │            │
                   ▼            ▼
               NORMAL       EMERGENCY
```

## Emergency Logic

### Timeout Tracking

The system tracks time since last valid sensor reading:

```cpp
unsigned long now = millis();
unsigned long time_since_valid = (now - id(zone_slug_last_valid_time)) / 1000;  // seconds

if (time_since_valid >= emergency_timeout) {
  // Trigger emergency
}
```

### Emergency Trigger

When timeout exceeded:

1. Set `emergency_triggered = true`
2. Log ERROR: "EMERGENCY TRIGGERED - No valid sensor for X seconds"
3. Return NaN from abstracted sensor (PID sees invalid data)
4. Emergency shutdown component monitors flag and forces PID OFF

### Emergency Actions

**Performed by `room_emergency_shutdown.yaml`:**

```yaml
# Every 5 seconds, check emergency flag
interval:
  - interval: 5s
    then:
      - lambda: |-
          if (id(zone_slug_emergency_triggered)) {
            // Force PID to OFF mode
            auto pid = id(pid_id);
            if (pid->mode != climate::CLIMATE_MODE_OFF) {
              auto pid_call = pid->make_call();
              pid_call.set_mode(climate::CLIMATE_MODE_OFF);
              pid_call.perform();
            }
          }
```

**Cascade Effect:**
- PID OFF → Output = 0%
- slow_pwm receives 0% → Triggers `turn_off_action`
- Relay turns OFF (physical output de-energized)

### Safety Guarantees

1. **Fail-Safe:** Invalid sensor data cannot control relays
2. **Timeout-Based:** 3 minutes is sufficient for transient issues but fast enough for safety
3. **Idempotent:** Emergency actions can be called repeatedly without harm
4. **Automatic:** No manual intervention required

## Recovery Logic

### Recovery Initiation

When HA sensor becomes valid while in emergency:

1. Set `recovery_start_time = current_time`
2. Log WARN: "RECOVERING - Sensor back online (X°C)"
3. Monitor sensor validity continuously

### Stability Requirements

Recovery requires **60 seconds of continuous valid sensor data:**

```cpp
unsigned long recovery_duration = (now - id(zone_slug_recovery_start_time)) / 1000;

if (recovery_duration >= recovery_stability_timeout) {
  // Recovery complete
  id(zone_slug_emergency_triggered) = false;
  id(zone_slug_recovery_start_time) = 0;
}
```

### Flapping Prevention

If sensor fails during recovery:

1. Reset `recovery_start_time = 0`
2. Remain in Emergency state
3. Log WARN: "RECOVERY FAILED - Sensor lost again"
4. Prevents rapid on/off cycling

### Auto-Resume

After successful recovery (60s stability):

1. `emergency_triggered` set to false
2. PID controller automatically resumes based on HA setpoint/mode
3. Relay control restored through normal PID → slow_pwm → relay chain
4. No manual intervention required

## Configuration Reference

### Minimal Configuration

```yaml
packages:
  room_sensors: !include
    file: ../../room_sensors.yaml
    vars:
      zone_slug: "bagno_grande"
      zone_name: "Bagno Grande"
      ha_temperature_sensor_id: "sensor.room_bagno_grande_temperature"
```

### Custom Timeouts

```yaml
packages:
  room_sensors: !include
    file: ../../room_sensors.yaml
    vars:
      zone_slug: "bagno_grande"
      zone_name: "Bagno Grande"
      ha_temperature_sensor_id: "sensor.room_bagno_grande_temperature"
      emergency_timeout: 300         # 5 minutes (more tolerant)
      recovery_stability_timeout: 120  # 2 minutes (more conservative)
      check_interval: 5              # 5 seconds (more responsive)
```

### Rationale for Defaults

- **emergency_timeout: 180s (3 min)**
  - Long enough for transient HA restarts (~30-60s)
  - Short enough for safety (won't heat/cool for extended period with no feedback)
  - Prevents nuisance alarms during brief network issues

- **recovery_stability_timeout: 60s (1 min)**
  - Ensures sensor is truly stable, not flapping
  - Short enough for quick recovery
  - Long enough to detect intermittent issues

- **check_interval: 10s**
  - Balances responsiveness vs. log spam
  - Aligns with typical HA sensor update frequencies
  - ESPHome timer resolution suitable

## Lambda Code Walkthrough

### Section 1: Sensor Validity Check

```cpp
if (id(${zone_slug}_room_temperature_ha).has_state()) {
  float ha_temp = id(${zone_slug}_room_temperature_ha).state;
  
  if (!isnan(ha_temp)) {
    // Valid sensor data available
```

**Purpose:** Check if HA sensor has a state and that state is a valid number.

**Edge Cases:**
- Sensor entity doesn't exist: `has_state()` returns false
- Sensor value is NaN: Detected by `isnan()` check
- Sensor is `unavailable`: Treated as NaN

### Section 2: Emergency → Recovering Transition

```cpp
if (id(${zone_slug}_emergency_triggered)) {
  if (id(${zone_slug}_recovery_start_time) == 0) {
    id(${zone_slug}_recovery_start_time) = now;
    ESP_LOGW("room_sensors", "${zone_name}: RECOVERING");
  }
  
  unsigned long recovery_duration = (now - id(${zone_slug}_recovery_start_time)) / 1000;
  if (recovery_duration >= ${recovery_stability_timeout}) {
    // Recovery complete
    id(${zone_slug}_emergency_triggered) = false;
    id(${zone_slug}_recovery_start_time) = 0;
  }
}
```

**Purpose:** Manage recovery state with stability checking.

**Logic:**
1. If in emergency and sensor becomes valid, start recovery timer
2. Wait for stability period (60s default)
3. After stability period, clear emergency flag and exit recovery

### Section 3: Emergency Trigger

```cpp
if (time_since_valid >= ${emergency_timeout}) {
  if (!id(${zone_slug}_emergency_triggered)) {
    id(${zone_slug}_emergency_triggered) = true;
    ESP_LOGE("room_sensors", "${zone_name}: EMERGENCY TRIGGERED");
  }
}
```

**Purpose:** Trigger emergency when timeout exceeded.

**Logic:**
1. Calculate time since last valid sensor reading
2. If timeout exceeded and not already in emergency, set flag
3. Log ERROR for visibility

### Section 4: Return Value

```cpp
return ha_temp;  // Valid sensor data
// OR
return NAN;      // No valid sensor data
```

**Purpose:** Provide temperature to PID controller OR indicate invalid data.

**PID Behavior:**
- Valid float: PID calculates output based on temperature
- NaN: PID cannot operate (requires valid sensor for control)

## Diagnostic Sensors

### text_sensor.{zone}_sensor_state

**Purpose:** Human-readable state indicator

**Values:**
- **"Normal":** System operating correctly
- **"Emergency":** No valid sensor, emergency shutdown active
- **"Recovering":** Sensor valid, waiting for stability

**Usage:**

```yaml
# HA Dashboard Card
type: entities
entities:
  - entity: text_sensor.bagno_grande_sensor_state
    name: Bagno Grande Status
    icon: mdi:state-machine
```

**Automations:**

```yaml
# Alert on emergency
automation:
  - alias: "HVAC Emergency Alert"
    trigger:
      - platform: state
        entity_id: text_sensor.bagno_grande_sensor_state
        to: "Emergency"
    action:
      - service: notify.mobile_app
        data:
          message: "Bagno Grande in EMERGENCY mode - sensor unavailable"
```

### sensor.{zone}_room_sensor_last_update

**Purpose:** Timestamp of last valid sensor reading

**Device Class:** `timestamp`

**Usage:**

```yaml
# Show freshness of sensor data
type: entities
entities:
  - entity: sensor.bagno_grande_room_sensor_last_update
    name: Last Sensor Update
```

**Debugging:**
- Check if sensor is updating regularly
- Identify stale sensor issues
- Calculate time since last update

## Integration with Epic 4

Epic 5 builds on Epic 4's room-based component architecture:

**Epic 4 Provided:**
- Room component structure (`components/rooms/*/room_name.yaml`)
- Per-room PID controllers
- Slow PWM → relay control chain
- Room-specific configuration isolation

**Epic 5 Added:**
- HA-only sensor input (replacing Modbus)
- Emergency shutdown logic
- State visibility (text sensors)
- Simplified 2-tier failover

**Synergy:**
- Room components are self-contained (sensors + PID + relays)
- Emergency logic operates per-room (isolated failures)
- Easy to migrate one room at a time (pilot testing)

## Comparison with Epic 3

### Epic 3: HA-Coordinated Independent Boards

**Architecture:**
- ESPHome devices independent (no inter-device Modbus)
- Home Assistant coordinates between devices
- Removed Modbus master/slave between ESPHome nodes

**Focus:** Device independence

### Epic 5: HA-Only Sensors

**Architecture:**
- Sensors from HA only (no Modbus sensors on ESPHome)
- Emergency shutdown for safety
- Simplified sensor failover

**Focus:** Sensor simplification, cost reduction

**Complementary:**
- Epic 3 removed inter-device Modbus (coordination)
- Epic 5 removed intra-device Modbus (sensors)
- Combined result: Modbus only for outputs (0-10V adapters)

## Performance Characteristics

### Sensor Latency

**HA Sensor → ESPHome:**
- Typical: 1-5 seconds
- Depends on: HA sensor update frequency, API responsiveness
- ESPHome polls HA sensor every update interval (default: sensor-specific)

**Emergency Detection:**
- Minimum: `emergency_timeout` (180s)
- Check frequency: `check_interval` (10s)
- Precision: ±10s (check interval)

**Recovery Confirmation:**
- Minimum: `recovery_stability_timeout` (60s)
- Check frequency: `check_interval` (10s)
- Precision: ±10s

### Resource Usage

**RAM:**
- 3 globals per room: ~12 bytes
- Total for 8 rooms: ~96 bytes (negligible)

**Flash:**
- Component code: ~100 lines → ~2-3 KB compiled
- Total for 8 rooms: ~16-24 KB (minimal)

**CPU:**
- Template sensor update: 10s interval
- Lambda execution: <1ms
- Negligible CPU impact

## Code Quality Improvements

### From v4 to v5

| Metric                | v4 (Modbus)     | v5 (HA-Only) | Change  |
| --------------------- | --------------- | ------------ | ------- |
| Lines of Code         | 221             | ~100         | -54%    |
| Failover Tiers        | 3               | 2            | -33%    |
| Required Vars         | 5               | 3            | -40%    |
| Entity Count/Room     | 7               | 3            | -57%    |
| External Dependencies | Modbus hardware | HA sensors   | Simpler |

### Maintainability

**Improved:**
- Fewer code paths (2 tiers vs. 3)
- Clearer state machine (explicit states)
- Better logging (state transitions visible)
- Comprehensive documentation

**Simplified:**
- No Modbus polling logic
- No sensor priority management
- No humidity handling (not needed)
- Single sensor source (HA)

## Future Enhancements

Potential improvements identified during Epic 5:

1. **Multi-Threshold Warnings**
   - Add "Warning" state at 60s (before 180s emergency)
   - Give users advance notice of potential sensor issues

2. **Configurable Recovery Actions**
   - Allow custom lambdas to run on recovery
   - E.g., restore specific PID setpoint, notify HA

3. **Per-Room Timeout Customization**
   - Different rooms may warrant different timeouts
   - E.g., critical rooms (bathrooms) shorter timeout

4. **HA Notifications**
   - Automatic HA notifications on emergency
   - Built into component vs. requiring HA automation

5. **Sensor Quality Metrics**
   - Track sensor update frequency
   - Alert if sensor updates become irregular (before emergency)

---

**Document Version:** 1.0  
**Last Updated:** October 30, 2025  
**Epic:** Epic 5 - HA-Only Sensors with Emergency Shutdown
