# Window Sensors Map

This document maps each room to its corresponding Home Assistant window/door sensor entity ID for window detection integration.

## Purpose

Window detection requires a binary sensor from Home Assistant that indicates whether a window is open or closed. This map ensures consistent entity ID usage across room configurations.

## Ground Floor (distribuzione-piano-terra)

| Room           | Window Sensor Entity ID            | Status           | Notes                               |
| -------------- | ---------------------------------- | ---------------- | ----------------------------------- |
| Soggiorno      | `binary_sensor.soggiorno_window`   | ✅ Configured     | Window detection active for fancoil |
| Cucina         | `binary_sensor.cucina_window`      | ✅ Configured     | Window detection active for fancoil |
| Sala da Pranzo | `binary_sensor.sala_pranzo_window` | ✅ Configured     | Window detection active for fancoil |
| Bagno          | N/A                                | ⚠️ Not Applicable | Radiant floor only (no fancoil)     |
| Anticamera     | N/A                                | ⚠️ Not Applicable | Radiant floor only (no fancoil)     |

## First Floor (distribuzione-primo-piano)

| Room             | Window Sensor Entity ID | Status           | Notes                           |
| ---------------- | ----------------------- | ---------------- | ------------------------------- |
| Camera Padronale | N/A                     | ⚠️ Not Applicable | Radiant floor only (no fancoil) |
| Camera Nord      | N/A                     | ⚠️ Not Applicable | Radiant floor only (no fancoil) |
| Camera Sud       | N/A                     | ⚠️ Not Applicable | Radiant floor only (no fancoil) |
| Camera Ospiti    | N/A                     | ⚠️ Not Applicable | Radiant floor only (no fancoil) |
| Bagno Padronale  | N/A                     | ⚠️ Not Applicable | Radiant floor only (no fancoil) |
| Bagno Grande     | N/A                     | ⚠️ Not Applicable | Radiant floor only (no fancoil) |
| Bagno Ospiti     | N/A                     | ⚠️ Not Applicable | Radiant floor only (no fancoil) |
| Lavanderia       | N/A                     | ⚠️ Not Applicable | Radiant floor only (no fancoil) |

## Sensor Requirements

### Physical Sensors

For rooms with window detection configured, ensure the corresponding Home Assistant binary sensor entity exists:

- **Soggiorno**: `binary_sensor.soggiorno_window`
- **Cucina**: `binary_sensor.cucina_window`

### Mock Sensors (Testing Only)

If physical sensors are not yet installed, you can create mock sensors in Home Assistant for testing:

```yaml
# In Home Assistant configuration.yaml
template:
  - binary_sensor:
      - name: "Soggiorno Window"
        unique_id: soggiorno_window_mock
        state: "{{ states('input_boolean.soggiorno_window_mock') }}"
        device_class: window
      
      - name: "Cucina Window"
        unique_id: cucina_window_mock
        state: "{{ states('input_boolean.cucina_window_mock') }}"
        device_class: window

input_boolean:
  soggiorno_window_mock:
    name: "Soggiorno Window (Mock)"
    icon: mdi:window-open-variant
  
  cucina_window_mock:
    name: "Cucina Window (Mock)"
    icon: mdi:window-open-variant
```

After adding these to Home Assistant:
1. Reload template entities
2. Reload input boolean entities
3. Toggle the input_boolean to simulate window open/close

## Adding New Rooms

When adding window detection to a new room:

1. **Verify equipment type**: Only add window detection to rooms with **fancoils** that waste energy when windows are open
2. **Check sensor exists**: Ensure the Home Assistant window sensor entity exists
3. **Add to this map**: Document the entity ID in the appropriate floor section
4. **Configure room**: Add window detection package to room component YAML
5. **Test**: Validate state transitions and PID integration

## Equipment Decision Tree

```
Does room have a fancoil?
├─ YES → Does PID control fancoil?
│  ├─ YES → Add window detection ✅
│  └─ NO → Skip (fancoil-only, no PID) ⚠️
└─ NO → Skip (radiant floor only) ⚠️
```

## Related Documentation

- [Epic 7 Window Detection Guide](epic-7-window-detection-guide.md) - Usage and configuration guide
- [Epic 7 Testing Checklist](epic-7-testing-checklist.md) - Validation procedures
- [room_window_detection.yaml](../components/room_window_detection.yaml) - Component implementation
