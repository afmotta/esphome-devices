# Home Assistant Climate Control Dashboards

Comprehensive dashboard system for monitoring and controlling the ESPHome-based multi-floor climate control system.

## Table of Contents

1. [Overview](#overview)
2. [Dashboard Structure](#dashboard-structure)
3. [Installation](#installation)
4. [Dashboard Descriptions](#dashboard-descriptions)
5. [Required Input Numbers](#required-input-numbers)
6. [Entity Naming Reference](#entity-naming-reference)
7. [Navigation Flow](#navigation-flow)
8. [Customization](#customization)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This dashboard system provides complete visibility and control over the 3-floor, 13-zone climate control system. The dashboards are organized hierarchically:

- **Main Overview**: System status and floor navigation
- **Floor Dashboards**: Per-floor system status and room navigation (3 floors)
- **Room Dashboards**: Detailed per-room controls and monitoring (14 rooms)
- **System Monitoring**: Technical diagnostics and hardware status

**Total Dashboards**: 19 YAML files
- 1 main overview
- 3 floor dashboards
- 14 room dashboards
- 1 system monitoring dashboard

---

## Dashboard Structure

```
home-assistant/dashboards/
├── climate-overview.yaml          # Main entry point
├── ground-floor.yaml              # Ground floor overview
├── first-floor.yaml               # First floor overview
├── second-floor.yaml              # Second floor overview
├── system-monitoring.yaml         # Technical diagnostics
└── rooms/
    ├── ground_floor/
    │   ├── soggiorno.yaml         # Living room (full detail)
    │   ├── cucina.yaml            # Kitchen
    │   ├── bagno-terra.yaml       # Bathroom
    │   ├── anticamera.yaml        # Entry hall
    │   └── locale-tecnico.yaml    # Technical room
    ├── first_floor/
    │   ├── camera-nord.yaml       # North bedroom
    │   ├── camera-sud.yaml        # South bedroom
    │   ├── camera-ospiti.yaml     # Guest bedroom
    │   ├── camera-padronale.yaml  # Master bedroom
    │   ├── bagno-grande.yaml      # Large bathroom
    │   ├── bagno-ospiti.yaml      # Guest bathroom
    │   ├── bagno-padronale.yaml   # Master bathroom
    │   └── lavanderia.yaml        # Laundry room
    └── second_floor/
        └── sottotetto.yaml        # Attic
```

---

## Installation

### ⚡ Quick Start (Recommended)

**Use the API installation script** for the fastest, easiest setup with no Home Assistant restart required:

```bash
cd /path/to/esphome-devices/home-assistant/dashboards

# Create a long-lived access token in HA first (Profile → Long-Lived Access Tokens)

python3 install-dashboards.py \
    --url http://homeassistant.local:8123 \
    --token YOUR_LONG_LIVED_TOKEN
```

✅ **Done!** Dashboards appear immediately in your Home Assistant sidebar.

📖 **Full API installation guide**: See [API_INSTALLATION.md](API_INSTALLATION.md)

---

### Method 1: API Installation (Recommended)

**Benefits**:
- ✅ No configuration.yaml edits required
- ✅ No Home Assistant restart needed
- ✅ Dashboards appear immediately
- ✅ UI-editable in Home Assistant
- ✅ Perfect for automated deployments

**Prerequisites**:
- Home Assistant running and accessible
- Long-lived access token (create in HA Profile)
- Python 3 with PyYAML (`pip3 install pyyaml`)

**Installation**:
```bash
python3 install-dashboards.py --url http://homeassistant.local:8123 --token YOUR_TOKEN
```

**Alternative (Bash)**:
```bash
./install-dashboards.sh http://homeassistant.local:8123 YOUR_TOKEN
```

📖 **Complete guide**: [API_INSTALLATION.md](API_INSTALLATION.md)

---

### Method 2: YAML Mode (For version control)

**Benefits**:
- Version-controlled dashboards
- Infrastructure-as-code approach
- Exact control over config files

1. **Enable YAML mode in Home Assistant**:

   Edit `configuration.yaml`:
   ```yaml
   lovelace:
     mode: yaml
     dashboards:
       # Main dashboard - shows in sidebar
       climate-overview:
         mode: yaml
         title: Climate Control
         icon: mdi:home-thermometer
         show_in_sidebar: true
         filename: /config/esphome-devices/home-assistant/dashboards/climate-overview.yaml

       # Floor dashboards - navigation only (not in sidebar)
       ground-floor:
         mode: yaml
         title: Ground Floor
         icon: mdi:home-floor-0
         show_in_sidebar: false
         filename: /config/esphome-devices/home-assistant/dashboards/ground-floor.yaml

       first-floor:
         mode: yaml
         title: First Floor
         icon: mdi:home-floor-1
         show_in_sidebar: false
         filename: /config/esphome-devices/home-assistant/dashboards/first-floor.yaml

       second-floor:
         mode: yaml
         title: Second Floor
         icon: mdi:home-floor-2
         show_in_sidebar: false
         filename: /config/esphome-devices/home-assistant/dashboards/second-floor.yaml

       # System monitoring - navigation only (not in sidebar)
       system-monitoring:
         mode: yaml
         title: System Monitoring
         icon: mdi:monitor-dashboard
         show_in_sidebar: false
         filename: /config/esphome-devices/home-assistant/dashboards/system-monitoring.yaml
   ```

   **Note**: Only the main "Climate Control" dashboard appears in the sidebar. All other dashboards are accessed via navigation buttons within the dashboard hierarchy.

2. **Copy dashboard files to Home Assistant**:

   ```bash
   # Option A: If this repo is inside HA config directory
   cd /config/esphome-devices/home-assistant/dashboards

   # Option B: Copy from external location
   cp -r /path/to/esphome-devices/home-assistant/dashboards /config/esphome-devices/home-assistant/
   ```

3. **Restart Home Assistant** to load the dashboard configurations.

4. **Navigate** to the dashboards from the sidebar.

### Method 2: Manual UI Mode Import

For individual dashboards or testing:

1. Go to **Settings → Dashboards → Add Dashboard**
2. Choose **New dashboard from scratch**
3. Open dashboard in **Edit mode**
4. Click **⋮ (three dots) → Raw configuration editor**
5. Paste the YAML content from any dashboard file
6. Save

**Note**: Room dashboards are intended to be navigated to, not shown in sidebar.

---

## Dashboard Descriptions

### Climate Overview (`climate-overview.yaml`)

**Main entry point** for the entire system. **This is the only dashboard shown in the Home Assistant sidebar.**

**Sections**:
- System Status: Heat pump mode, season classification, global demand
- Floor Navigation: Quick access to each floor
- Ground Floor Quick Status: Radiant, fancoil, dew point, boost
- First Floor Quick Status: Radiant, MEV system, air quality
- All Rooms Temperature: Grid view of all 14 zones

**Use Case**: Daily monitoring, quick temperature checks, system mode verification

**Access**: Home Assistant sidebar → Climate Control

---

### Ground Floor Dashboard (`ground-floor.yaml`)

**Navigation only** (not in sidebar) - Access from Climate Overview → "Ground Floor" button

**5 zones**: Soggiorno, Cucina, Bagno, Anticamera, Locale Tecnico

**Sections**:
- Floor System Status: Radiant and fancoil pump status
- Radiant Floor System: Mixing valve control, supply temperature, dew point protection
- Fancoil Boost System: Boost thresholds and predictive boost settings
- Room Navigation: Buttons to individual room dashboards
- All Rooms Quick Status: Temperature, humidity, dew point, system status per room

**Use Case**: Monitor ground floor climate, adjust mixing valve, manage boost system

**Access**: Climate Overview → "Ground Floor" button

---

### First Floor Dashboard (`first-floor.yaml`)

**Navigation only** (not in sidebar) - Access from Climate Overview → "First Floor" button

**8 zones**: 4 Bedrooms, 3 Bathrooms, Laundry Room

**Sections**:
- Floor System Status: Radiant pump and MEV power
- Radiant Floor System: Mixing valve control, supply temperature, dew point protection
- MEV (Mechanical Extract Ventilation) System: Fan controls, air quality sensors, demand sensors
- Room Navigation: Separate sections for bedrooms vs bathrooms/utility
- All Rooms Quick Status: Temperature, humidity, CO₂, radiant status per room

**Use Case**: Monitor first floor, control MEV ventilation, check air quality (CO₂/IAQ)

**Access**: Climate Overview → "First Floor" button

---

### Second Floor Dashboard (`second-floor.yaml`)

**Navigation only** (not in sidebar) - Access from Climate Overview → "Second Floor" button

**1 zone**: Sottotetto (Attic)

**Sections**:
- Floor System Status: Navigation and fancoil status
- Room Quick Status: Temperature, humidity, fancoil
- Fancoil System: PID control, fan speed
- Historical Data: Temperature and humidity trends

**Use Case**: Monitor attic climate (fancoil-only zone)

**Access**: Climate Overview → "Second Floor" button

---

### System Monitoring Dashboard (`system-monitoring.yaml`)

**Navigation only** (not in sidebar) - Access from Climate Overview → "System Monitoring" button

**Technical diagnostics dashboard** for advanced users.

**Sections**:
- ESPHome Device Status: Connection, uptime, WiFi signal
- Modbus Communication: Status of relay boards and analog output boards
- Ground Floor Relays: Individual relay switches (pumps, valves)
- First Floor Relays: Individual relay switches (pumps, valves, MEV)
- Analog Outputs (0-10V DAC): Mixing valves, fancoil speeds, MEV fan speed
- Mixing Valve Controllers: PID controls for supply temperature
- Pump Status: Radiant and fancoil pump states
- Sensor Failover Status: Active vs. Modbus vs. HA fallback sensors
- Dallas Temperature Sensors: 1-Wire supply temperature sensors
- System Configuration: HA input_number values (thresholds, margins, delays)
- All PID Controllers: Active status grid for all 13+ PIDs
- Boost Status: Fancoil boost triggers and reasons
- System Health Charts: Supply temps, dew points, air quality trends

**Use Case**: Troubleshooting, hardware verification, system health monitoring

**Access**: Climate Overview → "System Monitoring" button

---

### Room Dashboards (`rooms/*/*.yaml`)

Each room has a detailed dashboard with:

**Common Sections**:
- Room Environment: Temperature, humidity, dew point (+ CO₂/IAQ on first floor)
- Climate Control: Radiant and/or fancoil PID thermostats
- Hardware Controls: Relay switches, fan speeds, zone valves
- PID Diagnostics: P/I/D terms, output values, error values
- Auto-tune Controls: PID auto-tuning buttons
- Sensor Sources & Failover: Active sensor, Modbus sensor, HA fallback
- Historical Data: 24-hour graphs of temperature, humidity, PID output

**Variations by Room**:
- **Soggiorno, Cucina**: Radiant + Fancoil boost
- **Bagno Terra, Anticamera**: Radiant only (no boost)
- **Locale Tecnico**: Fancoil only
- **First Floor Bedrooms/Bathrooms**: Radiant + CO₂/IAQ sensors
- **Sottotetto**: Fancoil only

**Use Case**: Deep dive into specific room, diagnose issues, tune PID parameters

---

## Required Input Numbers

The dashboards reference Home Assistant `input_number` entities for runtime configuration. Create these in **Configuration → Helpers → Add Helper → Number**:

### Ground Floor Configuration

```yaml
# In Home Assistant UI: Settings → Devices & Services → Helpers
input_number:
  ground_floor_safe_margin:
    name: Ground Floor Safe Margin
    min: 0.5
    max: 3.0
    step: 0.1
    unit_of_measurement: "°C"
    mode: box
    icon: mdi:shield-half-full

  ground_floor_fancoil_boost_threshold:
    name: Ground Floor Fancoil Boost Threshold
    min: 1.0
    max: 10.0
    step: 0.5
    unit_of_measurement: "°C"
    mode: box
    icon: mdi:thermometer-alert

  ground_floor_fancoil_humidity_threshold:
    name: Ground Floor Fancoil Humidity Threshold
    min: 50
    max: 80
    step: 1
    unit_of_measurement: "%"
    mode: box
    icon: mdi:water-percent-alert

  ground_floor_predictive_boost_minutes:
    name: Ground Floor Predictive Boost Minutes
    min: 5
    max: 60
    step: 5
    unit_of_measurement: "min"
    mode: box
    icon: mdi:timer-alert
```

### First Floor Configuration

```yaml
input_number:
  first_floor_safe_margin:
    name: First Floor Safe Margin
    min: 0.5
    max: 3.0
    step: 0.1
    unit_of_measurement: "°C"
    mode: box
    icon: mdi:shield-half-full
```

### MEV Configuration

```yaml
input_number:
  mev_escalation_fan_threshold:
    name: MEV Escalation Fan Threshold
    min: 50
    max: 100
    step: 5
    unit_of_measurement: "%"
    mode: box
    icon: mdi:fan-alert

  mev_deescalation_fan_threshold:
    name: MEV Deescalation Fan Threshold
    min: 10
    max: 50
    step: 5
    unit_of_measurement: "%"
    mode: box
    icon: mdi:fan-alert

  mev_minimum_fan_speed:
    name: MEV Minimum Fan Speed
    min: 0
    max: 50
    step: 5
    unit_of_measurement: "%"
    mode: box
    icon: mdi:fan-speed-1

  mev_escalation_delay_minutes:
    name: MEV Escalation Delay Minutes
    min: 1
    max: 30
    step: 1
    unit_of_measurement: "min"
    mode: box
    icon: mdi:timer
```

**YAML Configuration Alternative** (add to `configuration.yaml`):

```yaml
input_number:
  # Copy the above YAML format here
```

---

## Entity Naming Reference

### Standard Entity Patterns

The dashboards reference entities following these patterns:

#### Climate Entities (PID Controllers)
- `climate.pid_radiant_{room_slug}` - Radiant floor PID
- `climate.pid_fancoil_{room_slug}` - Fancoil PID
- `climate.pid_mixing_valve_{area_slug}` - Mixing valve PID

Examples:
- `climate.pid_radiant_soggiorno`
- `climate.pid_fancoil_cucina`
- `climate.pid_mixing_valve_radiante_piano_terra`

#### Temperature Sensors
- `sensor.{room_slug}_room_temp_abstracted` - Active temperature (failover)
- `sensor.{room_slug}_modbus_temp` - Modbus sensor temperature
- `sensor.room_{room_slug}_temperature` - HA fallback temperature

#### Humidity Sensors
- `sensor.{room_slug}_room_humidity_abstracted` - Active humidity (failover)
- `sensor.{room_slug}_modbus_humidity` - Modbus sensor humidity
- `sensor.room_{room_slug}_humidity` - HA fallback humidity

#### Dew Point Sensors
- `sensor.{room_slug}_dew_point` - Calculated dew point

#### Air Quality Sensors (First Floor)
- `sensor.{room_slug}_co2` - CO₂ level (from room sensor via UDP)
- `sensor.{room_slug}_iaq` - Indoor Air Quality index

#### Relay Switches
- `switch.relay_{number}` - Relay switches (1-21+)

#### Analog Outputs
- `number.analog_output_{number}` - 0-10V DAC outputs (1-7+)
- `number.fancoil_{room_slug}_speed` - Fancoil fan speed

#### Binary Sensors
- `binary_sensor.pid_{type}_{room_slug}_is_active` - Zone active
- `binary_sensor.pid_{type}_{room_slug}_is_heating` - Heating mode
- `binary_sensor.pid_{type}_{room_slug}_is_cooling` - Cooling mode
- `binary_sensor.{room_slug}_boost_active` - Fancoil boost active
- `binary_sensor.{room_slug}_radiant_saturated` - Radiant output saturated

#### PID Diagnostic Sensors
- `sensor.pid_{type}_{room_slug}_output_value` - PID output percentage
- `sensor.pid_{type}_{room_slug}_error_value` - Temperature error
- `sensor.pid_{type}_{room_slug}_p_term` - Proportional term
- `sensor.pid_{type}_{room_slug}_i_term` - Integral term
- `sensor.pid_{type}_{room_slug}_d_term` - Derivative term
- `sensor.pid_{type}_{room_slug}_kp` - Kp gain
- `sensor.pid_{type}_{room_slug}_ki` - Ki gain
- `sensor.pid_{type}_{room_slug}_kd` - Kd gain

#### Boost Coordinator Sensors
- `sensor.{room_slug}_boost_trigger_reason` - Boost activation reason
- `sensor.{room_slug}_time_above_threshold` - Time above temp threshold
- `sensor.{room_slug}_time_radiant_saturated` - Time radiant saturated
- `sensor.{room_slug}_radiant_output_level` - Radiant output level

#### Auto-tune Buttons
- `button.autotune_pid_{type}_{room_slug}` - PID auto-tune trigger

#### MEV Controls
- `switch.vmc_primo_piano_power` - MEV power
- `switch.vmc_primo_piano_mode` - MEV winter/summer mode
- `switch.vmc_primo_piano_dehumidifier` - MEV dehumidifier
- `switch.vmc_primo_piano_cooling` - MEV cooling integration
- `number.vmc_primo_piano_target_fan_speed` - MEV fan speed
- `binary_sensor.vmc_primo_piano_alarm` - MEV alarm status

#### System-Wide Entities
- `select.heat_pump_mode` - HEAT / COOL / SANITARY_ONLY
- `sensor.season_classification` - Winter Lock / Summer Lock / Spring Shoulder / Autumn Shoulder
- `sensor.heat_pump_mode_reason` - CALENDAR_LOCK / DEMAND
- `binary_sensor.any_pid_requesting_heat` - Global heat demand
- `binary_sensor.any_pid_requesting_cool` - Global cool demand
- `binary_sensor.summer_mode` - Summer mode active

### Room Slug Reference

| Room Name (Italian) | Slug | Floor |
|---------------------|------|-------|
| Soggiorno | `soggiorno` | Ground |
| Cucina | `cucina` | Ground |
| Bagno | `bagno_terra` | Ground |
| Anticamera | `anticamera` | Ground |
| Locale Tecnico | `locale_tecnico` | Ground |
| Camera Nord | `camera_nord` | First |
| Camera Sud | `camera_sud` | First |
| Camera Ospiti | `camera_ospiti` | First |
| Camera Padronale | `camera_padronale` | First |
| Bagno Grande | `bagno_grande` | First |
| Bagno Ospiti | `bagno_ospiti` | First |
| Bagno Padronale | `bagno_padronale` | First |
| Lavanderia | `lavanderia` | First |
| Sottotetto | `sottotetto` | Second |

---

## Navigation Flow

### Sidebar Access

**Only the main Climate Overview dashboard appears in the Home Assistant sidebar.** All other dashboards are accessed via navigation buttons, creating a clean hierarchical structure:

```
[Sidebar] Climate Control (Main Entry)
    │
    ├─> Ground Floor Dashboard
    │   ├─> Soggiorno (detailed)
    │   ├─> Cucina (detailed)
    │   ├─> Bagno Terra (detailed)
    │   ├─> Anticamera (detailed)
    │   └─> Locale Tecnico (detailed)
    │
    ├─> First Floor Dashboard
    │   ├─> Camera Nord (detailed)
    │   ├─> Camera Sud (detailed)
    │   ├─> Camera Ospiti (detailed)
    │   ├─> Camera Padronale (detailed)
    │   ├─> Bagno Grande (detailed)
    │   ├─> Bagno Ospiti (detailed)
    │   ├─> Bagno Padronale (detailed)
    │   └─> Lavanderia (detailed)
    │
    ├─> Second Floor Dashboard
    │   └─> Sottotetto (detailed)
    │
    └─> System Monitoring Dashboard
```

### Navigation Pattern

1. **Start**: Click "Climate Control" in sidebar
2. **Navigate down**: Click floor/room buttons to drill into details
3. **Navigate up**: Use "Back" buttons to return to parent dashboard
4. **Direct access**: Bookmark specific dashboard URLs for quick access

Each room dashboard has a "Back" button to return to its floor dashboard.
Each floor dashboard has a "Back to Overview" button to return to the main dashboard.

---

## Customization

### Changing Card Layout

Dashboards use `sections` type with `grid` layouts. Adjust `columns` parameter:

```yaml
- type: grid
  title: Section Title
  columns: 3  # Change to 2, 4, etc.
  cards:
    # ...
```

### Adding Custom Cards

Insert additional cards in any section:

```yaml
- type: tile
  entity: sensor.custom_sensor
  name: My Custom Sensor
  icon: mdi:custom-icon
```

### Modifying History Graphs

Adjust time range and entities:

```yaml
- type: history-graph
  title: Custom History
  hours_to_show: 48  # Default: 24
  entities:
    - entity: sensor.entity_1
    - entity: sensor.entity_2
```

### Hiding Sections

Comment out entire sections you don't need:

```yaml
# - type: grid
#   title: Unwanted Section
#   cards:
#     # ...
```

### Custom Icons

Change icons using [Material Design Icons](https://pictogrammers.com/library/mdi/):

```yaml
icon: mdi:thermometer
icon: mdi:fan
icon: mdi:radiator
```

---

## Troubleshooting

### Dashboard Not Appearing

**Problem**: Dashboard doesn't show in sidebar after configuration.yaml update.

**Solution**:
1. Verify YAML syntax in `configuration.yaml`
2. Check file paths are correct (absolute paths recommended)
3. Restart Home Assistant
4. Check **Settings → System → Logs** for errors

### Missing Entities

**Problem**: Cards show "Entity not available" or "Unknown entity".

**Solution**:
1. Verify ESPHome device is online and connected
2. Check entity names match exactly (case-sensitive)
3. Use **Developer Tools → States** to find actual entity names
4. Update dashboard YAML with correct entity IDs
5. Ensure input_number helpers are created

### Input Numbers Missing

**Problem**: Configuration sensors show unavailable or fallback values.

**Solution**:
1. Create input_number helpers in **Settings → Devices & Services → Helpers**
2. Match entity IDs exactly as shown in [Required Input Numbers](#required-input-numbers)
3. Restart Home Assistant if added via `configuration.yaml`

### Navigation Not Working

**Problem**: "Back" buttons or room navigation buttons don't work.

**Solution**:
1. Verify dashboard paths match in `configuration.yaml`:
   - `path: climate-overview` matches `navigation_path: /lovelace/climate-overview`
2. Use lowercase, hyphenated paths
3. Check dashboard is registered in `configuration.yaml` under `lovelace:` → `dashboards:`

### Cards Overlapping or Layout Issues

**Problem**: Cards don't fit properly or overlap.

**Solution**:
1. Adjust `columns` parameter in grid sections
2. Mobile devices: Use fewer columns (2-3 max)
3. Desktop: Use more columns (3-5)
4. Some cards (like thermostats) take more space - place in dedicated grids

### History Graphs Empty

**Problem**: History graphs show no data.

**Solution**:
1. Wait 24 hours for data to accumulate (default `hours_to_show: 24`)
2. Verify entities have `state_class: measurement` in ESPHome config
3. Check **Developer Tools → History** to see if HA is recording data
4. Ensure recorder component is enabled in `configuration.yaml`

### MEV Dashboard Entities Missing

**Problem**: MEV-related entities not available.

**Solution**:
1. MEV only exists on first floor - check correct board is configured
2. Verify MEV component is included in first floor YAML
3. Check MEV relays and analog outputs are correctly assigned
4. Ensure UDP packet transport is configured for air quality sensors

---

## Advanced Configuration

### Adding Markdown Cards

Insert informational cards:

```yaml
- type: markdown
  content: |
    ## Room Information
    This room has **radiant floor heating** and **fancoil boost**.

    - Radiant: Primary system
    - Fancoil: Boost mode only
```

### Conditional Cards

Show cards only when conditions are met:

```yaml
- type: conditional
  conditions:
    - entity: binary_sensor.summer_mode
      state: "on"
  card:
    type: tile
    entity: sensor.max_dew_point_piano_terra
    name: Cooling Mode - Dew Point Protection
```

### Custom Button Actions

Add custom actions to buttons:

```yaml
- type: button
  name: Emergency Stop
  icon: mdi:alert-octagon
  tap_action:
    action: call-service
    service: climate.turn_off
    service_data:
      entity_id: all
```

---

## Support and Documentation

For more information on the ESPHome climate control system:

- **Main Documentation**: `/docs/` directory in repository
- **Architecture Diagram**: `/docs/architecture-diagram.md`
- **Product Requirements**: `/docs/prd.md`
- **CLAUDE.md**: Project overview and AI assistant guide
- **ESPHome Configs**: `/components/` and `/devices/` directories

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-24 | Initial dashboard system creation |

---

**Maintainer**: Climate Control System Development Team
**Repository**: esphome-devices
**Last Updated**: January 24, 2026
