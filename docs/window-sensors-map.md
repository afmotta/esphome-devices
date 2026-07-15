# Window Sensors Map

Maps each room to its Home Assistant window/door sensor entity for the window
guard (`climate/packages/components/window_guard.yaml`, CLIMATE C4 — restores
the Epic 7 capability dropped in the layered restructure).

## Purpose

The window guard forces a room's **fancoil** off while a window stays open
(default: open ≥ 180 s), and restores the previous mode after the window has
been closed for a stability period (default: 60 s). Radiant circuits are
deliberately not guarded — their time constant makes brief airing negligible.

The sensors are HA-tier by design (Zigbee contacts): when HA or a sensor is
unavailable the guard treats the window as closed and does nothing. CAN-wired
contacts can replace the HA tier at electrical-install time (topology ADR,
parked).

## Wired rooms

| Room      | Window Sensor Entity ID          | Guarded PID             |
| --------- | -------------------------------- | ----------------------- |
| Soggiorno | `binary_sensor.soggiorno_window` | `soggiorno_fancoil_pid` |
| Cucina    | `binary_sensor.cucina_window`    | `cucina_fancoil_pid`    |

## Fancoil rooms without a guard yet

| Room           | Notes                                                     |
| -------------- | --------------------------------------------------------- |
| Locale Tecnico | Add when a contact sensor exists (technical room)         |
| Sottotetto     | Add when a contact sensor exists (attic skylight/windows) |

All other rooms are radiant-only and intentionally have no window guard.

## Adding a room

1. Only guard rooms with a **fancoil** (radiant-only rooms are skipped by design).
2. Ensure the HA window binary sensor exists (`device_class: window`).
3. Add a `window_guard` package include to the room YAML:

```yaml
  window_guard: !include
    file: ../../packages/components/window_guard.yaml
    vars:
      ha_window_sensor_id: "binary_sensor.<room>_window"
      guarded_pid_id: <room>_fancoil_pid
```

4. Add the room to the table above.
5. Verify: open the window (or toggle a mock `input_boolean`-backed template
   sensor in HA), wait the timeout, confirm the fancoil PID goes OFF and the
   `<Room> Window Guard` text sensor reads "Active"; close it and confirm
   restore after the recovery period.

## Mock sensors for bench testing

```yaml
# In Home Assistant configuration.yaml
template:
  - binary_sensor:
      - name: "Soggiorno Window"
        unique_id: soggiorno_window_mock
        state: "{{ states('input_boolean.soggiorno_window_mock') }}"
        device_class: window

input_boolean:
  soggiorno_window_mock:
    name: "Soggiorno Window (Mock)"
    icon: mdi:window-open-variant
```
