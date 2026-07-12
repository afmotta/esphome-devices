# Dashboard Index

Complete listing of all Home Assistant dashboards for the climate control system.

## Summary

- **Total Dashboards**: 19
- **Sidebar Dashboard**: 1 (Climate Overview only)
- **Navigation Dashboards**: 4 (floor + system monitoring)
- **Room Dashboards**: 14 (deep navigation)
- **Format**: YAML (Home Assistant Lovelace)

## Navigation Hierarchy

```
[Sidebar] Climate Control
    ├─> Ground Floor Dashboard
    │   ├─> Soggiorno
    │   ├─> Cucina
    │   ├─> Bagno Terra
    │   ├─> Anticamera
    │   └─> Locale Tecnico
    ├─> First Floor Dashboard
    │   ├─> Camera Nord
    │   ├─> Camera Sud
    │   ├─> Camera Ospiti
    │   ├─> Camera Padronale
    │   ├─> Bagno Grande
    │   ├─> Bagno Ospiti
    │   ├─> Bagno Padronale
    │   └─> Lavanderia
    ├─> Second Floor Dashboard
    │   └─> Sottotetto
    └─> System Monitoring Dashboard
```

---

## Sidebar Dashboard

### Climate Overview (Main Entry Point)
**File**: `climate-overview.yaml`
**Path**: `/lovelace/climate-overview`
**Icon**: `mdi:home-thermometer`
**Purpose**: Main entry point, system status, all room temperatures

**Sections**:
- System Status (heat pump mode, season, demand)
- Floor Navigation
- Ground Floor Quick Status
- First Floor Quick Status
- All Rooms Temperature Grid

---

## Navigation Dashboards

### Ground Floor
**File**: `ground-floor.yaml`
**Path**: `/lovelace/ground-floor`
**Icon**: `mdi:home-floor-0`
**Purpose**: Ground floor system monitoring and room navigation

**Rooms** (5):
- Soggiorno (Living Room)
- Cucina (Kitchen)
- Bagno (Bathroom)
- Anticamera (Entry Hall)
- Locale Tecnico (Technical Room)

**Sections**:
- Floor System Status
- Radiant Floor System (mixing valve)
- Fancoil Boost System
- Room Navigation
- All Rooms Quick Status Grid

---

### First Floor
**File**: `first-floor.yaml`
**Path**: `/lovelace/first-floor`
**Icon**: `mdi:home-floor-1`
**Purpose**: First floor system monitoring, MEV control, room navigation

**Rooms** (8):
- Camera Nord (North Bedroom)
- Camera Sud (South Bedroom)
- Camera Ospiti (Guest Bedroom)
- Camera Padronale (Master Bedroom)
- Bagno Grande (Large Bathroom)
- Bagno Ospiti (Guest Bathroom)
- Bagno Padronale (Master Bathroom)
- Lavanderia (Laundry Room)

**Sections**:
- Floor System Status
- Radiant Floor System (mixing valve)
- MEV System (ventilation, air quality)
- Room Navigation (Bedrooms / Bathrooms & Utility)
- Bedrooms Quick Status Grid
- Bathrooms & Utility Quick Status Grid

---

### Second Floor
**File**: `second-floor.yaml`
**Path**: `/lovelace/second-floor`
**Icon**: `mdi:home-floor-2`
**Purpose**: Second floor monitoring (attic only)

**Rooms** (1):
- Sottotetto (Attic)

**Sections**:
- Floor System Status
- Room Quick Status
- Fancoil System
- Historical Data

---

### System Monitoring
**File**: `system-monitoring.yaml`
**Path**: `/lovelace/system-monitoring`
**Icon**: `mdi:monitor-dashboard`
**Purpose**: Technical diagnostics, hardware monitoring, system health

**Sections**:
- ESPHome Device Status
- Modbus Communication Status
- Ground Floor Relays (Board 1)
- First Floor Relays (Board 2)
- Analog Outputs (0-10V DAC)
- Mixing Valve Controllers
- Pump Status
- Sensor Failover Status
- Dallas Temperature Sensors
- System Configuration (Input Numbers)
- All PID Controllers Status
- Boost Status
- System Health Charts

---

## Room Dashboards (Navigation Only)

### Ground Floor Rooms

#### Soggiorno (Living Room)
**File**: `rooms/ground_floor/soggiorno.yaml`
**Path**: `/lovelace/soggiorno`
**Icon**: `mdi:sofa`
**System**: Radiant Floor + Fancoil Boost

**Features**:
- Full PID diagnostics (radiant + fancoil)
- Boost coordinator (temperature & humidity triggers)
- Sensor failover display
- Auto-tune controls
- Historical charts (24h)

---

#### Cucina (Kitchen)
**File**: `rooms/ground_floor/cucina.yaml`
**Path**: `/lovelace/cucina`
**Icon**: `mdi:chef-hat`
**System**: Radiant Floor + Fancoil Boost

**Features**:
- Radiant PID control
- Fancoil boost system
- Boost trigger reasons
- Auto-tune controls
- Historical charts

---

#### Bagno (Bathroom)
**File**: `rooms/ground_floor/bagno-terra.yaml`
**Path**: `/lovelace/bagno-terra`
**Icon**: `mdi:toilet`
**System**: Radiant Floor Only

**Features**:
- Radiant PID control
- Temperature/humidity monitoring
- Auto-tune control
- Historical charts
- Note: Excluded from dew point calculations (shower humidity)

---

#### Anticamera (Entry Hall)
**File**: `rooms/ground_floor/anticamera.yaml`
**Path**: `/lovelace/anticamera`
**Icon**: `mdi:door`
**System**: Radiant Floor Only

**Features**:
- Radiant PID control
- Temperature/humidity/dew point monitoring
- Auto-tune control
- Historical charts

---

#### Locale Tecnico (Technical Room)
**File**: `rooms/ground_floor/locale-tecnico.yaml`
**Path**: `/lovelace/locale-tecnico`
**Icon**: `mdi:toolbox`
**System**: Fancoil Only

**Features**:
- Fancoil PID control
- 0-10V fan speed control
- Auto-tune control
- Historical charts

---

### First Floor Rooms

#### Camera Nord (North Bedroom)
**File**: `rooms/first_floor/camera-nord.yaml`
**Path**: `/lovelace/camera-nord`
**Icon**: `mdi:bed`
**System**: Radiant Floor

**Features**:
- Radiant PID control
- Temperature/humidity/dew point
- CO₂ and IAQ sensors
- Auto-tune control
- Historical charts

---

#### Camera Sud (South Bedroom)
**File**: `rooms/first_floor/camera-sud.yaml`
**Path**: `/lovelace/camera-sud`
**Icon**: `mdi:bed`
**System**: Radiant Floor

**Features**:
- Radiant PID control
- Temperature/humidity/dew point
- CO₂ and IAQ sensors
- Auto-tune control
- Historical charts

---

#### Camera Ospiti (Guest Bedroom)
**File**: `rooms/first_floor/camera-ospiti.yaml`
**Path**: `/lovelace/camera-ospiti`
**Icon**: `mdi:bed`
**System**: Radiant Floor

**Features**:
- Radiant PID control
- Temperature/humidity/dew point
- CO₂ and IAQ sensors
- Auto-tune control
- Historical charts

---

#### Camera Padronale (Master Bedroom)
**File**: `rooms/first_floor/camera-padronale.yaml`
**Path**: `/lovelace/camera-padronale`
**Icon**: `mdi:bed-king`
**System**: Radiant Floor

**Features**:
- Radiant PID control
- Temperature/humidity/dew point
- CO₂ and IAQ sensors
- Auto-tune control
- Historical charts

---

#### Bagno Grande (Large Bathroom)
**File**: `rooms/first_floor/bagno-grande.yaml`
**Path**: `/lovelace/bagno-grande`
**Icon**: `mdi:toilet`
**System**: Radiant Floor

**Features**:
- Radiant PID control
- Temperature/humidity/dew point
- CO₂ and IAQ sensors
- Auto-tune control
- Historical charts

---

#### Bagno Ospiti (Guest Bathroom)
**File**: `rooms/first_floor/bagno-ospiti.yaml`
**Path**: `/lovelace/bagno-ospiti`
**Icon**: `mdi:toilet`
**System**: Radiant Floor

**Features**:
- Radiant PID control
- Temperature/humidity/dew point
- CO₂ and IAQ sensors
- Auto-tune control
- Historical charts

---

#### Bagno Padronale (Master Bathroom)
**File**: `rooms/first_floor/bagno-padronale.yaml`
**Path**: `/lovelace/bagno-padronale`
**Icon**: `mdi:toilet`
**System**: Radiant Floor

**Features**:
- Radiant PID control
- Temperature/humidity/dew point
- CO₂ and IAQ sensors
- Auto-tune control
- Historical charts

---

#### Lavanderia (Laundry Room)
**File**: `rooms/first_floor/lavanderia.yaml`
**Path**: `/lovelace/lavanderia`
**Icon**: `mdi:washing-machine`
**System**: Radiant Floor

**Features**:
- Radiant PID control
- Temperature/humidity/dew point
- CO₂ and IAQ sensors
- Auto-tune control
- Historical charts

---

### Second Floor Rooms

#### Sottotetto (Attic)
**File**: `rooms/second_floor/sottotetto.yaml`
**Path**: `/lovelace/sottotetto`
**Icon**: `mdi:home-roof`
**System**: Fancoil Only

**Features**:
- Full PID diagnostics (fancoil)
- 0-10V fan speed control
- Sensor failover display
- Auto-tune control
- Historical charts (24h)

---

## File Structure

```
climate/home-assistant/dashboards/
├── INDEX.md                       # This file
├── README.md                      # Full documentation
├── QUICK_START.md                 # Quick setup guide
├── climate-overview.yaml          # Main dashboard
├── ground-floor.yaml              # Ground floor
├── first-floor.yaml               # First floor
├── second-floor.yaml              # Second floor
├── system-monitoring.yaml         # System diagnostics
└── rooms/
    ├── ground_floor/
    │   ├── soggiorno.yaml
    │   ├── cucina.yaml
    │   ├── bagno-terra.yaml
    │   ├── anticamera.yaml
    │   └── locale-tecnico.yaml
    ├── first_floor/
    │   ├── camera-nord.yaml
    │   ├── camera-sud.yaml
    │   ├── camera-ospiti.yaml
    │   ├── camera-padronale.yaml
    │   ├── bagno-grande.yaml
    │   ├── bagno-ospiti.yaml
    │   ├── bagno-padronale.yaml
    │   └── lavanderia.yaml
    └── second_floor/
        └── sottotetto.yaml
```

---

## Entity Count by Dashboard

### Climate Overview
- **Entities**: ~30
  - Selects: 1
  - Text Sensors: 2
  - Binary Sensors: 2
  - Sensors: ~25 (room temps)

### Ground Floor
- **Entities**: ~50
  - Climate: 10 (radiant + fancoil + mixing valve)
  - Sensors: ~25 (temps, humidity, dew points, boost)
  - Binary Sensors: ~10 (zone active, boost active)
  - Switches: 5 (relays)
  - Numbers: 3 (fan speeds)

### First Floor
- **Entities**: ~80
  - Climate: 9 (radiant + mixing valve)
  - Sensors: ~40 (temps, humidity, CO₂, IAQ, MEV demand)
  - Binary Sensors: ~15 (zone active, MEV alarm)
  - Switches: 12 (relays, MEV controls)
  - Numbers: 2 (mixing valve, MEV fan speed)

### Second Floor
- **Entities**: ~10
  - Climate: 1 (fancoil)
  - Sensors: 3 (temp, humidity, dew point)
  - Binary Sensors: 1 (zone active)
  - Numbers: 1 (fan speed)

### System Monitoring
- **Entities**: ~150+
  - All relays: 21+
  - All analog outputs: 7+
  - All climate controllers: 15+
  - All PID sensors: 50+
  - All binary sensors: 30+
  - Input numbers: 9

### Room Dashboards (Average)
- **Entities per room**: 15-25
  - Climate: 1-2
  - Sensors: 5-10 (temp, humidity, PID terms, etc.)
  - Binary Sensors: 3-5
  - Switches: 1-2
  - Numbers: 0-1
  - Buttons: 1-2 (auto-tune)

---

## Total Entity References

Across all dashboards, the following unique entities are referenced:

- **Climate Controllers**: 15+ (PIDs + mixing valves)
- **Sensors**: 150+ (temperature, humidity, dew point, CO₂, IAQ, PID diagnostics)
- **Binary Sensors**: 50+ (zone active, heating, cooling, boost, alarms)
- **Switches**: 25+ (relays, MEV controls)
- **Numbers**: 15+ (analog outputs, fan speeds)
- **Buttons**: 15+ (auto-tune triggers)
- **Selects**: 1 (heat pump mode)
- **Text Sensors**: 5+ (season, mode reason, boost reasons)
- **Input Numbers**: 9 (configuration values)

**Total Unique Entities**: ~280+

---

## Dashboard Characteristics

### Complexity Levels

| Dashboard | Complexity | Best For |
|-----------|------------|----------|
| Climate Overview | Low | Daily use, quick checks |
| Ground Floor | Medium | Floor monitoring, boost tuning |
| First Floor | Medium | Floor monitoring, MEV control, air quality |
| Second Floor | Low | Simple attic monitoring |
| System Monitoring | High | Diagnostics, troubleshooting |
| Room Dashboards | Medium-High | Detailed room control, PID tuning |

### Data Density

| Dashboard | Cards | Sections | Avg Load Time |
|-----------|-------|----------|---------------|
| Climate Overview | ~40 | 5 | Fast |
| Ground Floor | ~50 | 6 | Fast |
| First Floor | ~80 | 7 | Medium |
| Second Floor | ~15 | 4 | Fast |
| System Monitoring | ~150+ | 14 | Slow (data-heavy) |
| Room (Full) | ~40 | 7 | Medium |
| Room (Simple) | ~20 | 4 | Fast |

### Mobile Friendliness

| Dashboard | Mobile Score | Notes |
|-----------|--------------|-------|
| Climate Overview | ⭐⭐⭐⭐⭐ | Perfect for mobile |
| Floor Dashboards | ⭐⭐⭐⭐ | Good, some scrolling |
| Room Dashboards | ⭐⭐⭐ | Requires scrolling |
| System Monitoring | ⭐⭐ | Desktop recommended |

---

## Quick Navigation

**I want to...**

- **Check all room temps** → Climate Overview
- **Adjust ground floor boost** → Ground Floor
- **Control ventilation** → First Floor (MEV section)
- **Set bedroom temperature** → First Floor → Camera Nord/Sud/Ospiti/Padronale
- **Tune PID controller** → Room Dashboard → Auto-tune section
- **Check relay status** → System Monitoring → Relays section
- **View historical trends** → Room Dashboard → Historical Data
- **Monitor sensor failover** → Room Dashboard → Sensor Sources
- **Check MEV air quality** → First Floor → MEV System
- **Diagnose system issues** → System Monitoring

---

## Related Documentation

- **README.md**: Complete setup and usage guide
- **QUICK_START.md**: 5-minute setup instructions
- **../../../CLAUDE.md**: Project overview and conventions
- **../../../docs/prd.md**: Product requirements
- **../../../docs/architecture-diagram.md**: System architecture

---

**Last Updated**: January 24, 2026
**Dashboard Version**: 1.0
**Total Dashboards**: 19
