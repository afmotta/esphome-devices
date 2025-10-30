# Epic 5 Migration Guide: HA-Only Sensors

## Overview

Epic 5 migrates the room temperature sensing architecture from a 3-tier Modbus-based failover system to a simplified 2-tier HA-only system with emergency shutdown. This eliminates 16+ expensive Modbus sensor devices and reduces code complexity by ~60%.

### What Changed

**Before (v4):**
- 3-tier failover: Modbus sensor → HA sensor → Emergency
- Required Modbus sensor hardware per room (~$40 each)
- Complex RS485 wiring
- `room_sensors.yaml` with 221 lines of code

**After (v5):**
- 2-tier failover: HA sensor → Emergency
- No Modbus sensor hardware required
- Leverages existing HA sensors (Zigbee, WiFi, etc.)
- `room_sensors.yaml` with ~100 lines of code

### Why the Change

1. **Cost Reduction:** Eliminate ~$640 in Modbus sensor hardware
2. **Simplification:** Remove complex RS485 wiring and Modbus coordination
3. **Reliability:** Fewer components = fewer failure points
4. **Safety:** Emergency shutdown (3-min timeout) ensures safe operation

## Prerequisites

### Required Home Assistant Sensors

Each room must have a temperature sensor entity in Home Assistant:

```yaml
# Example entity IDs needed:
sensor.room_bagno_grande_temperature
sensor.room_camera_nord_temperature
sensor.room_soggiorno_temperature
# etc...
```

**Sensor Requirements:**
- Must report temperature in °C
- Must update regularly (at least every 60 seconds recommended)
- Must be available when HA is running

### Verify Sensor Availability

Before migration, verify all required HA sensors exist:

```bash
# In Home Assistant, check Developer Tools → States
# Search for: sensor.room_*_temperature
# Verify all rooms have corresponding entities
```

## Migration Sequence

Epic 5 follows a phased rollout strategy to minimize risk:

1. **Phase 1: Pilot** - Migrate 1 room, monitor 24 hours
2. **Phase 2: First Floor Batch** - Migrate remaining 7 first floor rooms
3. **Phase 3: Ground Floor Batch** - Migrate 4 ground floor rooms
4. **Phase 4: Production** - 7-day monitoring, sign-off

### Recommended Timeline

- Day 1: Pilot room (bagno_grande)
- Day 2-3: First floor batch
- Day 4-5: Ground floor batch
- Day 6-12: Production monitoring
- Day 13: Epic 5 sign-off

## Step-by-Step Migration Instructions

### Step 1: Backup Current Configuration

```bash
cd /path/to/esphome-devices
git checkout -b epic-5-backup
git add -A
git commit -m "Backup before Epic 5 migration"
```

### Step 2: Update Room Component (Example: bagno_grande)

**Before:**
```yaml
packages:
  room_sensors: !include
    file: ../../room_sensors.yaml
    vars:
      zone_slug: "bagno_grande"
      zone_name: "Bagno Grande"
      modbus_controller_address: 0x0C  # ← REMOVE
      ha_temperature_sensor_id: "sensor.room_bagno_grande_temperature"
      ha_humidity_sensor_id: "sensor.room_bagno_grande_humidity"  # ← REMOVE
```

**After:**
```yaml
packages:
  room_sensors: !include
    file: ../../room_sensors.yaml
    vars:
      zone_slug: "bagno_grande"
      zone_name: "Bagno Grande"
      ha_temperature_sensor_id: "sensor.room_bagno_grande_temperature"
      # Optional overrides (defaults shown):
      # emergency_timeout: 180  # 3 minutes
      # recovery_stability_timeout: 60  # 1 minute
      # check_interval: 10  # 10 seconds
```

**Changes Made:**
1. ✅ Removed `modbus_controller_address` var
2. ✅ Removed `ha_humidity_sensor_id` var
3. ✅ Kept `ha_temperature_sensor_id` (required)

### Step 3: Compile and Validate

```bash
# Compile the device configuration
esphome compile locals/distribuzione-primo-piano.yaml

# Check for errors
# Expected: "Successfully compiled program"
```

### Step 4: Flash Device

```bash
# OTA flash (recommended if device is online)
esphome upload locals/distribuzione-primo-piano.yaml

# OR USB flash (if device is accessible)
esphome run locals/distribuzione-primo-piano.yaml
```

### Step 5: Verify Operation

#### 5.1 Check Device Online

```bash
# ESPHome logs
esphome logs locals/distribuzione-primo-piano.yaml

# Look for:
# - "WiFi connected"
# - "API connection established"
# - "Valid sensor update received"
```

#### 5.2 Check Sensor State

In Home Assistant, verify:
- `text_sensor.bagno_grande_sensor_state` shows **"Normal"**
- `sensor.bagno_grande_room_temp_abstracted` has valid temperature
- `sensor.bagno_grande_room_sensor_last_update` shows recent timestamp

#### 5.3 Check PID Operation

Verify PID controller is working:
- `climate.pid_radiant_bagno_grande` shows correct mode (Heat/Cool)
- Relay operates when PID calls for heating/cooling
- Room temperature control functions normally

## Testing Procedures

### Test 1: Normal Operation (24 hours)

**Purpose:** Verify system operates correctly under normal conditions

**Procedure:**
1. Deploy migrated room configuration
2. Monitor for 24 hours
3. Check `text_sensor.*_sensor_state` remains "Normal"
4. Verify no unexpected errors in logs

**Success Criteria:**
- ✅ Sensor state = "Normal" for entire 24h period
- ✅ PID control operates correctly
- ✅ No emergency events triggered
- ✅ Room temperature maintained within setpoint ±0.5°C

### Test 2: Emergency Trigger

**Purpose:** Verify emergency shutdown activates when HA sensor unavailable

**Procedure:**
1. Note current system state (relay ON/OFF, PID mode)
2. Disconnect Home Assistant OR disable HA sensor entity
3. Wait 180 seconds (3 minutes)
4. Observe system behavior

**Expected Behavior:**
- T+0s: HA sensor becomes unavailable
- T+0-180s: WARNING logs "No sensor data for X / 180 seconds"
- T+180s: ERROR log "EMERGENCY TRIGGERED"
- T+180s: `text_sensor.*_sensor_state` changes to "Emergency"
- T+180s: Relay turns OFF (physical click/LED off)
- T+180s: PID mode changes to OFF

**Success Criteria:**
- ✅ Emergency triggers after exactly 180 seconds
- ✅ Relay physically turns OFF
- ✅ PID mode = OFF
- ✅ Sensor state = "Emergency"

### Test 3: Recovery

**Purpose:** Verify system recovers automatically when HA sensor returns

**Procedure:**
1. Start with system in Emergency state (from Test 2)
2. Reconnect Home Assistant OR re-enable HA sensor entity
3. Wait for sensor data to flow
4. Monitor recovery process

**Expected Behavior:**
- T+0s: HA sensor provides valid data
- T+0s: WARN log "RECOVERING - Sensor back online"
- T+0s: `text_sensor.*_sensor_state` changes to "Recovering"
- T+0-60s: INFO logs "RECOVERING - X / 60 seconds"
- T+60s: INFO log "NORMAL - Recovery complete"
- T+60s: `text_sensor.*_sensor_state` changes to "Normal"
- T+60s: PID resumes previous mode (Heat/Cool based on HA)
- T+60s+: Relay control restored (via PID → slow_pwm → relay)

**Success Criteria:**
- ✅ Recovery starts immediately when sensor available
- ✅ 60-second stability period observed
- ✅ Sensor state = "Normal" after 60s
- ✅ PID resumes operation
- ✅ Relay control restored

### Test 4: Flapping Prevention

**Purpose:** Verify system doesn't cycle rapidly with intermittent connectivity

**Procedure:**
1. Simulate unstable HA connection (connect/disconnect every 30s)
2. Monitor system behavior
3. Verify recovery requires sustained stability

**Expected Behavior:**
- System enters Emergency after 180s total unavailability
- Each reconnection starts recovery timer
- If disconnected before 60s stability, recovery resets
- Prevents rapid on/off cycling of relays

**Success Criteria:**
- ✅ System requires continuous 60s sensor validity for recovery
- ✅ No rapid relay cycling observed
- ✅ Recovery timer resets if sensor fails during recovery

## Rollback Procedures

If critical issues are discovered during migration, you can rollback:

### Option 1: Revert Single Room

```bash
# Revert room component file to previous version
git checkout HEAD~1 components/rooms/first_floor/bagno_grande.yaml

# Recompile and flash
esphome run locals/distribuzione-primo-piano.yaml
```

### Option 2: Full Rollback

```bash
# Switch to backup branch
git checkout epic-5-backup

# Recompile all devices
esphome compile locals/distribuzione-primo-piano.yaml
esphome compile locals/distribuzione-piano-terra.yaml

# Flash devices
esphome upload locals/distribuzione-primo-piano.yaml --device IP_ADDRESS
esphome upload locals/distribuzione-piano-terra.yaml --device IP_ADDRESS
```

### Option 3: Use Deprecated v4

```yaml
# In room component, temporarily use old version
packages:
  room_sensors: !include
    file: ../../deprecated/room_sensors_v4.yaml  # Old version
    vars:
      zone_slug: "bagno_grande"
      zone_name: "Bagno Grande"
      modbus_controller_address: 0x0C
      ha_temperature_sensor_id: "sensor.room_bagno_grande_temperature"
      ha_humidity_sensor_id: "sensor.room_bagno_grande_humidity"
```

## Entity ID Mapping

### Entities Removed

| Old Entity                                | Status    |
| ----------------------------------------- | --------- |
| `sensor.{zone}_room_temperature_modbus`   | ❌ Removed |
| `sensor.{zone}_room_humidity_modbus`      | ❌ Removed |
| `sensor.{zone}_room_humidity`             | ❌ Removed |
| `binary_sensor.{zone}_room_sensor_online` | ❌ Removed |

### Entities Changed

| Old Entity                       | New Entity                        | Change              |
| -------------------------------- | --------------------------------- | ------------------- |
| `text_sensor.{zone}_temp_source` | `text_sensor.{zone}_sensor_state` | Renamed, new values |

**Old Values:** "Modbus" / "Home Assistant" / "Emergency"  
**New Values:** "Normal" / "Emergency" / "Recovering"

### Entities Unchanged

| Entity                                  | Status                              |
| --------------------------------------- | ----------------------------------- |
| `sensor.{zone}_room_temp_abstracted`    | ✅ Unchanged (internal, used by PID) |
| `sensor.{zone}_room_sensor_last_update` | ✅ Unchanged                         |
| `climate.pid_radiant_{zone}`            | ✅ Unchanged                         |

## Home Assistant Dashboard Updates

### Update Required Cards

**Replace sensor status cards:**

```yaml
# OLD: Shows Modbus vs HA source
type: entities
entities:
  - entity: text_sensor.bagno_grande_temp_source

# NEW: Shows Normal/Emergency/Recovering state
type: entities
entities:
  - entity: text_sensor.bagno_grande_sensor_state
    icon: mdi:state-machine
```

**Add emergency monitoring:**

```yaml
# Monitor all room states
type: custom:auto-entities
card:
  type: entities
  title: Room Sensor States
filter:
  include:
    - entity_id: "text_sensor.*_sensor_state"
      options:
        tap_action:
          action: more-info
  exclude: []
sort:
  method: name
```

### Recommended New Dashboard

See `docs/epic-5-ha-only-sensors.md` for complete dashboard configuration.

## Troubleshooting

### Issue: Room Stuck in Emergency

**Symptoms:** `text_sensor.{zone}_sensor_state` shows "Emergency", won't clear

**Check:**
1. HA sensor exists: `sensor.room_{zone}_temperature`
2. Entity ID matches room component `ha_temperature_sensor_id`
3. HA sensor has valid state (not `unavailable`)

**Fix:**
```bash
# Check ESPHome logs
esphome logs locals/distribuzione-primo-piano.yaml

# Look for errors like:
# "WARNING - No sensor data for X / 180 seconds"
```

### Issue: Emergency Doesn't Trigger

**Symptoms:** HA disconnected >3 min, system still operating

**Check:**
1. Verify `emergency_timeout` = 180s (default)
2. Check `sensor.{zone}_room_sensor_last_update` timestamp
3. Ensure HA sensor is actually unavailable (not just old value)

**Fix:**
Review lambda timeout calculation in logs.

### Issue: Recovery Takes Too Long

**Symptoms:** HA reconnected, system stays "Recovering"

**Check:**
1. Verify `recovery_stability_timeout` = 60s (default)
2. Monitor HA sensor for continuous validity (no flapping)
3. Check network stability

**Fix:**
Wait for full 60s continuous sensor validity.

### Issue: Relay Doesn't Turn Off

**Symptoms:** Emergency triggered, relay still energized

**Check:**
1. Emergency shutdown component included in room
2. PID mode actually changed to OFF
3. Physical relay operation (test manually)

**Fix:**
Verify emergency_shutdown package in room component.

## Performance Metrics

### Before Epic 5

- Modbus sensor devices: 16+
- RS485 wiring: Complex
- Cost per sensor: ~$40
- Code lines: 221
- Entity count/room: 7

### After Epic 5

- Modbus sensor devices: 0
- RS485 wiring: None (sensors)
- Cost per sensor: $0 (uses HA sensors)
- Code lines: ~100 (60% reduction)
- Entity count/room: 3

### Cost Savings

- Hardware: $640+ saved
- Wiring labor: 8-12 hours saved
- Maintenance: Simpler, fewer failure points

## Next Steps

After successful migration:

1. ✅ Monitor system for 7 days
2. ✅ Create HA monitoring dashboard
3. ✅ Document any issues encountered
4. ✅ Update Epic 5 completion report
5. ✅ Sign off on Epic 5 closure

## Support

For issues or questions:
- Review ESPHome logs: `esphome logs locals/{device}.yaml`
- Check `docs/epic-5-ha-only-sensors.md` for architecture details
- See `docs/epic-5-completion-report.md` for known issues

---

**Document Version:** 1.0  
**Last Updated:** October 30, 2025  
**Epic:** Epic 5 - HA-Only Sensors with Emergency Shutdown
