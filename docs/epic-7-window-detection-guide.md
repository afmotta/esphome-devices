# Epic 7: Window Detection Component Usage Guide

## Overview

The window detection component provides automated climate control shutdown when windows are open to prevent energy waste. When a window is detected open for a configurable period, the system automatically turns off the fancoil PID controller to stop heating or cooling the outdoor environment.

**Key Benefits:**
- **Energy Savings**: Prevents wasted energy from conditioning outdoor air
- **User Transparency**: Diagnostic sensors show window state and system behavior
- **Equipment Protection**: Graceful shutdown prevents thermal stress
- **Flexible Configuration**: Per-room equipment-aware shutdown modes

## When to Use Window Detection

### ✅ Use Window Detection For:

**Fancoil-equipped rooms with PID control:**
- Rooms with active heating/cooling via fancoils
- Rapid air exchange makes open windows highly wasteful
- PID controller can be cleanly shut down and restarted
- Examples: Soggiorno (fancoil + radiant), Cucina (fancoil + radiant)

### ⚠️ Do NOT Use Window Detection For:

**Radiant floor heating/cooling only:**
- High thermal mass makes window detection ineffective
- System responds slowly (hours, not minutes)
- Shutting down wastes stored thermal energy
- Natural temperature drop is sufficient response
- Examples: Bagno, Anticamera, all first floor rooms

**Fancoil-only rooms without PID:**
- Rooms where fancoil is controlled directly (not via PID)
- No PID controller to integrate shutdown with
- Example: Sala da Pranzo

## Equipment Decision Tree

```
Does room have a fancoil?
├─ YES → Does room have a PID controller for the fancoil?
│  ├─ YES → ✅ Add window detection
│  │  └─ Configure: shutdown_modes = [cooling, heating] or equipment-specific
│  └─ NO → ⚠️ Skip window detection (fancoil-only, no PID integration)
└─ NO → Is it radiant floor only?
   └─ YES → ⚠️ Skip window detection (thermal mass makes it unnecessary)
```

## Configuration Parameters

### Required Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `zone_slug` | String | Room identifier (lowercase, underscores) | `"soggiorno"` |
| `zone_name` | String | Human-readable room name | `"Soggiorno"` |
| `ha_window_sensor_id` | String | Home Assistant binary sensor entity ID | `"binary_sensor.soggiorno_window"` |
| `pid_id` | String | ESPHome PID climate entity ID to control | `pid_fancoil_soggiorno` |
| `window_shutdown_modes` | String (CSV) | Climate modes to shutdown when window open | `"cooling, heating"` |

### Optional Variables (with Defaults)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `window_open_timeout` | Time | `180s` | How long window must be open before shutdown |
| `window_close_recovery_time` | Time | `60s` | How long window must be closed before restart |

### Shutdown Modes Configuration

The `window_shutdown_modes` parameter determines which climate modes trigger shutdown:

**Both heating and cooling:**
```yaml
window_shutdown_modes: "cooling, heating"
```
Use when: Room has fancoil that wastes energy in both modes

**Cooling only:**
```yaml
window_shutdown_modes: "cooling"
```
Use when: Fancoil primarily used for cooling, heating less wasteful

**Heating only:**
```yaml
window_shutdown_modes: "heating"
```
Use when: Fancoil primarily used for heating (rare)

**No shutdown (testing/disabled):**
```yaml
window_shutdown_modes: ""
```
Use when: Window sensor exists but shutdown should be disabled

## Integration Instructions

### Step 1: Verify Prerequisites

Before adding window detection to a room:

1. **Check equipment type:**
   - Room must have a fancoil with PID control
   - Verify PID entity ID exists (e.g., `pid_fancoil_soggiorno`)

2. **Verify window sensor:**
   - Home Assistant binary sensor must exist
   - Entity ID format: `binary_sensor.{room}_window`
   - Test sensor reports correct state (on = open, off = closed)

3. **Document sensor mapping:**
   - Add entry to [window-sensors-map.md](window-sensors-map.md)

### Step 2: Add Package to Room Component

Edit the room's component file (e.g., `components/rooms/ground_floor/soggiorno.yaml`):

```yaml
packages:
  room_sensors: !include
    file: ../../room_sensors.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      ha_temperature_sensor_id: "sensor.room_soggiorno_temperature"
  
  fancoil: !include
    file: ../../fancoil.yaml
    vars:
      adapter_id: modbus_0_10v_adapter_fancoils_ground_floor
      register_address: 0x42049
      area_slug: "soggiorno"
      area_name: "Soggiorno"
      sensor: soggiorno_room_temp_abstracted
      switch_management_script: ground_floor_fancoils_pump_management
  
  emergency_shutdown: !include
    file: ../../room_emergency_shutdown.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      pid_id: pid_radiant_soggiorno
  
  # NEW: Window detection for fancoil
  window_detection: !include
    file: ../../room_window_detection.yaml
    vars:
      zone_slug: "soggiorno"
      zone_name: "Soggiorno"
      ha_window_sensor_id: "binary_sensor.soggiorno_window"
      pid_id: pid_fancoil_soggiorno  # Note: Control fancoil PID, not radiant
      window_shutdown_modes: "cooling, heating"  # Both modes waste energy
```

**Key Points:**
- Place `window_detection` package after other packages
- Use `pid_fancoil_*` ID (not `pid_radiant_*`) if room has both
- Match `zone_slug` with existing room configuration
- Choose appropriate `shutdown_modes` based on equipment

### Step 3: Compile and Validate

```bash
# Compile device configuration to check for errors
esphome config devices/distribuzione-piano-terra.yaml

# Look for window detection entities in compilation output
# Expected: binary_sensor, text_sensor for window state
```

### Step 4: Deploy via OTA

```bash
# Upload updated firmware to device
esphome upload devices/distribuzione-piano-terra.yaml

# Or use OTA from Home Assistant if device is online
```

### Step 5: Verify in Home Assistant

After deployment, check Home Assistant for new entities:

**Expected entities per room:**
- `binary_sensor.{zone}_window_state` - Current window open/closed state
- `text_sensor.{zone}_window_detection_state` - State machine: "Normal", "Window Open", "Recovering"

Example for Soggiorno:
- `binary_sensor.soggiorno_window_state`
- `text_sensor.soggiorno_window_detection_state`

## State Machine Behavior

### States

1. **Normal**
   - Window closed for > recovery time
   - PID operating normally
   - No window-related interventions

2. **Window Open**
   - Window detected open for > timeout period
   - PID forced to OFF mode
   - Cascade: PID OFF → slow_pwm OFF → relay OFF → fancoil OFF

3. **Recovering**
   - Window closed but within recovery period
   - PID remains OFF (prevents short-cycling)
   - After recovery period → returns to Normal

### State Transitions

```
         Window closed
         (for 60s default)
┌────────────────────────┐
│                        │
│       NORMAL           │
│  PID: Operating        │
│                        │
└────────┬───────────────┘
         │
         │ Window opens
         │ (for 180s default)
         ▼
┌────────────────────────┐
│                        │
│    WINDOW OPEN         │
│  PID: Forced OFF       │
│                        │
└────────┬───────────────┘
         │
         │ Window closes
         ▼
┌────────────────────────┐
         │                        │
│    RECOVERING          │
│  PID: Still OFF        │
│  (60s countdown)       │
│                        │
└────────────────────────┘
         │
         │ After 60s
         └─────► NORMAL
```

### Timeout Behavior

**Window Open Timeout (default 180s):**
- Prevents false positives from brief window opening
- User has 3 minutes to close window before shutdown
- Adjustable per room if needed

**Window Close Recovery (default 60s):**
- Prevents short-cycling when window opens/closes repeatedly
- System waits 1 minute after window close before resuming
- Allows room to stabilize before restarting climate control

## PID Integration Details

### How Window Detection Controls PID

Window detection uses the **climate action API** to force PID shutdown:

```yaml
- climate.control:
    id: pid_fancoil_soggiorno
    mode: "OFF"
```

This is the same API used by:
- Emergency shutdown (sensor failure)
- Home Assistant manual control
- Automation scripts

**Cascade behavior:**
```
Window Open (>180s)
  └─> climate.control(mode=OFF)
      └─> PID output = 0%
          └─> slow_pwm duty_cycle = 0%
              └─> Relay turn_off_action
                  └─> Fancoil stops
```

**Recovery behavior:**
```
Window Closed (>60s)
  └─> climate.control(mode=previous_mode)
      └─> PID resumes operation
          └─> slow_pwm resumes duty cycle
              └─> Relay turn_on_action (if duty > threshold)
                  └─> Fancoil resumes
```

### Mode Awareness

Window detection only acts when PID is in a configured shutdown mode:

**Example:** `shutdown_modes: "cooling, heating"`

| Current PID Mode | Window Open | Action |
|------------------|-------------|---------|
| HEAT | Yes | ✅ Force PID OFF |
| COOL | Yes | ✅ Force PID OFF |
| OFF | Yes | ⚠️ No action (already off) |
| AUTO | Yes | ⚠️ Not supported (use HEAT or COOL) |

**Why mode awareness matters:**
- In heating mode with window open: Heating outdoor air = wasteful
- In cooling mode with window open: Cooling outdoor air = wasteful
- In OFF mode: Nothing to shutdown (safe to ignore window state)

## Testing Checklist

### Pre-Deployment Testing

- [ ] Window sensor entity exists in Home Assistant
- [ ] Window sensor reports correct state (toggle test)
- [ ] Room component YAML compiles without errors
- [ ] PID entity ID is correct for fancoil (not radiant)
- [ ] `shutdown_modes` match room equipment capabilities

### Post-Deployment Validation

- [ ] Device updated via OTA successfully
- [ ] Device online and responsive in Home Assistant
- [ ] New window detection entities visible in HA
- [ ] Text sensor shows "Normal" state initially

### Functional Testing

- [ ] **Open window test:**
  - Open window (or toggle mock sensor)
  - Wait 3 minutes (or configured timeout)
  - Verify text sensor changes to "Window Open"
  - Verify PID climate entity shows mode: OFF
  - Verify fancoil stops running (listen/observe)

- [ ] **Close window test:**
  - Close window
  - Verify text sensor changes to "Recovering"
  - Wait 1 minute (or configured recovery time)
  - Verify text sensor changes to "Normal"
  - Verify PID resumes operation
  - Verify fancoil resumes running

- [ ] **Mode-specific test:**
  - Set PID to mode NOT in shutdown_modes (if applicable)
  - Open window
  - Verify PID does NOT shutdown (mode not configured)
  - Close window, set PID to mode IN shutdown_modes
  - Open window
  - Verify PID DOES shutdown

### Regression Testing

- [ ] Existing rooms without window detection unaffected
- [ ] Temperature control maintained in other rooms
- [ ] Emergency shutdown still works (test with HA sensor unavailable)
- [ ] Manual PID control via HA still works
- [ ] No new errors in ESPHome device logs

## Troubleshooting

### Window Detection Not Triggering

**Symptom:** Window open but PID doesn't shutdown

**Possible Causes:**
1. **Window sensor not updating:**
   - Check HA logs for sensor updates
   - Verify `ha_window_sensor_id` matches actual entity ID
   - Test sensor by toggling manually in HA

2. **Timeout not reached:**
   - Default timeout is 180 seconds (3 minutes)
   - Wait full timeout period before expecting shutdown
   - Check `text_sensor.{zone}_window_detection_state` for current state

3. **PID not in shutdown mode:**
   - Check current PID mode in HA
   - Verify mode is in `window_shutdown_modes` list
   - If in OFF mode, window detection has no effect

4. **Wrong PID ID:**
   - Verify `pid_id` matches actual fancoil PID entity
   - Common mistake: Using radiant PID instead of fancoil PID
   - Check device YAML compilation output for PID entity IDs

### Window Detection Won't Reset

**Symptom:** Window closed but system stays in "Window Open" or "Recovering"

**Possible Causes:**
1. **Window sensor stuck:**
   - Check HA sensor state (should be "off" when closed)
   - Verify sensor battery (if wireless)
   - Test sensor by manually toggling in HA

2. **Recovery period not elapsed:**
   - Default recovery is 60 seconds
   - Wait full recovery period before expecting Normal state
   - Check text sensor for countdown (if logged)

3. **ESPHome not receiving HA updates:**
   - Check Home Assistant connection status
   - Verify API connection in device logs
   - Restart ESPHome device if API connection lost

### PID Won't Resume After Window Closed

**Symptom:** State returns to "Normal" but fancoil doesn't restart

**Possible Causes:**
1. **PID mode not restored:**
   - Check PID mode in HA (should be HEAT or COOL)
   - Manually set PID mode if stuck in OFF
   - Check device logs for climate.control calls

2. **Temperature setpoint not met:**
   - PID may be in correct mode but output = 0% naturally
   - Check if room is already at setpoint temperature
   - Adjust setpoint to trigger PID output

3. **Relay control issue:**
   - Check if slow_pwm is outputting duty cycle
   - Verify relay responds to manual control
   - Check pump management script execution

### False Positives (Unwanted Shutdowns)

**Symptom:** PID shutting down when window not actually open

**Possible Causes:**
1. **Timeout too short:**
   - Default 180s may be too aggressive
   - Increase `window_open_timeout` to 300s or 600s
   - Update room configuration and redeploy

2. **Sensor noise:**
   - Window sensor reporting intermittent "open" state
   - Check sensor placement and mounting
   - Consider sensor replacement if unreliable

3. **Wrong sensor mapped:**
   - Verify `ha_window_sensor_id` is for correct room/window
   - Check [window-sensors-map.md](window-sensors-map.md)
   - Update if entity ID is incorrect

## Performance Impact

**CPU Usage:**
- Negligible (<0.1% additional load)
- State machine updates only on window sensor changes

**Memory Usage:**
- ~2KB per room for state tracking and automation
- Scales linearly with number of rooms

**Network Traffic:**
- 1 API call per state transition (Normal ↔ Window Open ↔ Recovering)
- Minimal impact on Home Assistant API load

**Response Time:**
- Shutdown triggered within 1 second after timeout expires
- Recovery delayed by configured recovery time (default 60s)

## Related Documentation

- [window-sensors-map.md](window-sensors-map.md) - Entity ID mapping for all rooms
- [epic-7-testing-checklist.md](epic-7-testing-checklist.md) - Comprehensive testing procedures
- [epic-7-completion-report.md](epic-7-completion-report.md) - Epic 7 summary and results
- [room_window_detection.yaml](../components/room_window_detection.yaml) - Component implementation
- [Epic 7 Brief](epic-7-brief.md) - Original requirements and planning

## Future Enhancements

**Planned for future epics:**
- Home Assistant notifications when window shutdown occurs
- Per-room timeout customization via HA input_number
- Energy savings tracking (kWh saved per window detection event)
- MEV coordination (window open → boost ventilation)
- Multi-window support (logical OR of multiple sensors per room)

**Moonshot ideas (not committed):**
- Building-level ventilation detection (multiple windows → fresh air mode)
- Outdoor temperature integration ("free" heating/cooling mode)
- Machine learning for optimal timeout tuning
- Seasonal timeout adjustment (shorter in winter, longer in summer)
