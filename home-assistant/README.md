# Home Assistant Configuration

This directory contains Home Assistant configuration files for the ESPHome climate control system. These configurations work alongside the ESPHome devices to provide intelligent automation, monitoring, and control.

## Directory Structure

```
home-assistant/
├── automations/           # Automation YAML files
│   ├── seasonal-mode.yaml # Epic 17: Calendar gates & demand transitions
│   ├── mev-control.yaml   # Epic 16: MEV state machine automations
│   └── climate-control.yaml # Epic 5/8: Resume & emergency alerts
├── templates/             # Template sensors
│   ├── seasonal-mode.yaml # Epic 17: Weather forecast & override detection
│   └── mev-control.yaml   # Epic 16: Fan speed demand calculations
├── helpers/               # Input helpers (input_select, input_number)
│   ├── seasonal-mode.yaml # Epic 17: HP mode & threshold settings
│   └── mev-control.yaml   # Epic 16: MEV control parameters
├── dashboards/            # Lovelace dashboard configurations
│   └── climate-control.yaml # Main monitoring dashboard
└── README.md              # This file
```

## Installation

### Method 1: Packages (Recommended)

Add to your `configuration.yaml`:

```yaml
homeassistant:
  packages:
    # Helpers
    seasonal_mode_helpers: !include home-assistant/helpers/seasonal-mode.yaml
    mev_control_helpers: !include home-assistant/helpers/mev-control.yaml

    # Templates
    seasonal_mode_templates: !include home-assistant/templates/seasonal-mode.yaml
    mev_control_templates: !include home-assistant/templates/mev-control.yaml

    # Automations
    seasonal_mode_automations: !include home-assistant/automations/seasonal-mode.yaml
    mev_control_automations: !include home-assistant/automations/mev-control.yaml
    climate_control_automations: !include home-assistant/automations/climate-control.yaml
```

### Method 2: Direct Include

Copy contents of each file into your `configuration.yaml` under the appropriate sections:

- `input_select:` and `input_number:` sections from helpers/
- `template:` section from templates/
- `automation:` section from automations/

### Dashboard Installation

Copy `dashboards/climate-control.yaml` content into:
- Home Assistant → Settings → Dashboards → Add Dashboard → Edit in YAML

## Feature Overview

### Seasonal Mode (Epic 17)

Three-tier automated heat pump mode selection:

1. **Tier 1: Calendar Gates** (Highest Priority)
   - Winter Lock: Oct 15 - Apr 15 → HEAT mode
   - Summer Lock: Jun 1 - Aug 31 → COOL mode
   - Shoulder seasons: Apr 16 - May 31, Sep 1 - Oct 14

2. **Tier 2: Weather Forecast Guidance** (Informational)
   - Forecast high ≥26°C → Suggests COOL
   - Forecast high ≤14°C → Suggests HEAT
   - Dead band 15-25°C → Suggests SANITARY_ONLY

3. **Tier 3: Demand-Driven Transitions** (Overrides Tier 2)
   - Any PID requests heating → Switch to HEAT
   - Any PID requests cooling → Switch to COOL
   - PID demand ALWAYS wins over forecast guidance

### MEV Control (Epic 16)

Fan-speed-triggered state machine for humidity control:

- **States**: FAN_ONLY → DEHUMIDIFYING → COOLING
- **Escalation**: Fan working hard (≥70%) + humidity rising → add equipment
- **De-escalation**: Humidity low (<40%) + fan coasting (<30%) → remove equipment
- **Air Quality**: CO₂ and IAQ levels drive baseline fan speed

### Climate Control (Epic 5/8)

- **Resume Automation**: Restarts climate after conditions clear
- **Emergency Alerts**: Notifications on sensor failures
- **MEV Alarms**: Alerts on ventilation system faults

## Dependencies

### ESPHome Entities Required

```yaml
# From ESPHome devices
- select.climate_control_heat_pump_mode
- text_sensor.climate_control_heat_pump_mode_reason
- text_sensor.climate_control_season_classification
- binary_sensor.climate_control_any_pid_requesting_heat
- binary_sensor.climate_control_any_pid_requesting_cool
- sensor.first_floor_max_humidity
- sensor.first_floor_max_co2
- sensor.first_floor_max_iaq
- switch.first_floor_mev_dehumidifier
- switch.first_floor_mev_cooling
- number.first_floor_mev_fan_speed
- binary_sensor.mev_primo_piano_alarm
- climate.{room}_pid (various rooms)
- text_sensor.{room}_coordinator_status (various rooms)
```

### External Integrations

- **Weather**: Any weather integration with forecast support (Met.no, OpenWeatherMap, etc.)
- **Mobile App**: For push notifications (optional)

## Configuration

### Weather Entity

Replace `weather.home` in `templates/seasonal-mode.yaml` with your actual weather entity:

```yaml
{% set forecast_high = state_attr('weather.YOUR_ENTITY', 'forecast')[0].temperature | float(20) %}
```

### Threshold Tuning

Adjust via Home Assistant UI or Developer Tools:

| Helper | Default | Description |
|--------|---------|-------------|
| `input_number.hp_cooling_threshold` | 26°C | Forecast temp suggesting COOL |
| `input_number.hp_heating_threshold` | 14°C | Forecast temp suggesting HEAT |
| `input_number.mev_humidity_upper_bound` | 60% | Target high humidity |
| `input_number.mev_humidity_lower_bound` | 40% | Target low humidity |
| `input_number.mev_minimum_fan_speed` | 20% | Always-on ventilation |

## Source Epics

- **Epic 5**: HA-Only Sensors with Emergency Shutdown
- **Epic 6**: MEV Hardware Integration
- **Epic 8**: Coordinator State Machine
- **Epic 16**: First Floor MEV Intelligent Control
- **Epic 17**: Three-Tier Seasonal Mode Selection

## Version

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | January 24, 2026 | Initial consolidation from epics |
