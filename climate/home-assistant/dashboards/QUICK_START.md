# Quick Start Guide - Climate Control Dashboards

Fast setup guide for getting your dashboards up and running.

## ⚡ Recommended Method (5 Minutes) - YAML Mode

**Note**: Home Assistant's dashboard API only works for UI-created dashboards, not for loading YAML configurations. The API installation scripts included in this directory are therefore not functional. Use YAML mode instead.

### Step 1: Copy Files (1 minute)

```bash
# If inside HA container or SSH addon
cd /config
mkdir -p esphome-devices/climate/home-assistant/dashboards

# Copy all dashboard files to this location
# (Adjust source path as needed)
```

### Step 2: Configure Home Assistant (2 minutes)

Edit `/config/configuration.yaml`:

```yaml
# Add this section (or merge with existing lovelace: section)
lovelace:
  mode: yaml
  dashboards:
    # Main dashboard - only this one shows in sidebar
    climate-overview:
      mode: yaml
      title: Climate Control
      icon: mdi:home-thermometer
      show_in_sidebar: true
      filename: esphome-devices/climate/home-assistant/dashboards/climate-overview.yaml

    # All other dashboards - navigation only (hidden from sidebar)
    ground-floor:
      mode: yaml
      title: Ground Floor
      icon: mdi:home-floor-0
      show_in_sidebar: false
      filename: esphome-devices/climate/home-assistant/dashboards/ground-floor.yaml

    first-floor:
      mode: yaml
      title: First Floor
      icon: mdi:home-floor-1
      show_in_sidebar: false
      filename: esphome-devices/climate/home-assistant/dashboards/first-floor.yaml

    second-floor:
      mode: yaml
      title: Second Floor
      icon: mdi:home-floor-2
      show_in_sidebar: false
      filename: esphome-devices/climate/home-assistant/dashboards/second-floor.yaml

    system-monitoring:
      mode: yaml
      title: System Monitoring
      icon: mdi:monitor-dashboard
      show_in_sidebar: false
      filename: esphome-devices/climate/home-assistant/dashboards/system-monitoring.yaml
```

**Navigation Hierarchy**: Climate Control (sidebar) → Floor Dashboards → Room Dashboards

### Step 3: Install the MEV helpers (1 minute)

Copy `climate/home-assistant/mev_helpers.yaml` into your HA packages: it holds the only `input_number`
helpers the controller still reads (the MEV demand bounds). Without them the demand falls back to a
flat 20 %.

Dew-point margins and fancoil-boost tuning are **not** HA helpers: they are persisted `number`
entities on the controller (they keep working with HA down). Tune them from the `climate-control`
device page:

| Number entity (on the controller) | Range | Default |
|------|-------|---------|
| `number.climate_control_ground_floor_radiant_safe_margin` | 1.0–5.0 °C | 2.0 °C |
| `number.climate_control_first_floor_radiant_safe_margin` | 1.0–5.0 °C | 2.0 °C |
| `number.climate_control_ground_floor_fancoil_boost_threshold` | 0.5–10.0 °C | 4.0 °C |
| `number.climate_control_ground_floor_fancoil_humidity_threshold` | 30–90 % | 60 % |
| `number.climate_control_ground_floor_fancoil_predictive_boost_minutes` | 1–120 min | 20 min |

The safe margin sets the COOL supply target (max room dew point + margin); the mixing valve's
dew-point interlock shuts the chilled water below dew point + margin/2 (review N-01).

If you created the old `input_number.*_safe_margin` / `*_fancoil_*` helpers from an earlier version
of this guide, delete them — nothing reads them.

### Step 4: Restart Home Assistant

Settings → System → Restart

### Step 5: Verify

1. Check sidebar - you should see **only one new entry**: "Climate Control"
2. Click "Climate Control" in sidebar to open the main dashboard
3. Verify entities are showing data (not "unavailable")
4. Test navigation buttons to floor dashboards
5. Test navigation from floor → room dashboards
6. Use "Back" buttons to navigate back up the hierarchy

**Important**: Only the main "Climate Control" dashboard appears in the sidebar. All floor dashboards, room dashboards, and system monitoring are accessed via navigation buttons within the dashboard hierarchy.

---

## Common Issues & Instant Fixes

### "Entity not available" errors

**Cause**: ESPHome device offline or entity names don't match.

**Fix**:
```bash
# Check ESPHome device status
# Settings → Devices & Services → ESPHome
# Click on "climate-control" device
# Verify it's online

# Find actual entity names
# Developer Tools → States
# Search for "climate" or "sensor"
```

### Dashboards not in sidebar

**Cause**: `configuration.yaml` not updated or syntax error.

**Fix**:
```bash
# Check YAML syntax
# Developer Tools → YAML → Check Configuration

# View errors
# Settings → System → Logs
```

### Input numbers missing

**Cause**: Not created yet.

**Fix**: Install `mev_helpers.yaml` (Step 3). The only helpers left are the MEV demand bounds; everything else is a controller `number`.

---

## Dashboard Tour

### Main Dashboard (Climate Control - in sidebar)

**Location**: Home Assistant sidebar → "Climate Control"

**What you'll see**:
- Current heat pump mode (HEAT/COOL/SANITARY_ONLY)
- Season classification
- All room temperatures at a glance
- Navigation buttons to all floors and system monitoring

**What to do here**:
- Daily temperature check
- Change heat pump mode (select dropdown)
- Navigate to specific floors (click buttons)
- Access system monitoring

**This is your entry point** - all other dashboards are accessed from here.

### Floor Dashboards

**What you'll see**:
- Floor-specific system status
- Mixing valve control (radiant floors)
- Room temperature grid
- MEV system (first floor only)

**What to do here**:
- Monitor floor-level systems
- Adjust mixing valve target temperature
- Control MEV ventilation
- Navigate to specific rooms

### Room Dashboards

**What you'll see**:
- Full environmental data (temp, humidity, dew point, CO₂, IAQ)
- Climate controls (thermostats for radiant and/or fancoil)
- PID diagnostics (P/I/D terms, output values)
- Historical graphs (24 hours)
- Auto-tune buttons

**What to do here**:
- Set room temperature targets
- Monitor PID performance
- Trigger PID auto-tuning
- Diagnose issues (sensor failover, boost triggers)
- Check historical trends

### System Monitoring Dashboard

**What you'll see**:
- ESPHome device connectivity
- All relay states
- All analog outputs
- Modbus communication status
- Complete PID controller grid
- System health charts

**What to do here**:
- Verify hardware operation
- Check relay switching
- Monitor communication health
- Diagnose system-wide issues
- View aggregate trends

---

## Quick Actions

### Change Room Temperature

1. Navigate to room dashboard
2. Click thermostat card
3. Drag slider or click +/- buttons
4. Temperature updates immediately

### Switch Heat Pump Mode

1. Go to Climate Overview
2. Click "Heat Pump Mode" tile
3. Select HEAT / COOL / SANITARY_ONLY
4. System switches mode (may take 1-2 minutes)

### Activate Fancoil Boost (Manual)

1. Navigate to room with boost (Soggiorno or Cucina)
2. Scroll to "Fancoil Boost System"
3. Click "Fancoil Control" thermostat
4. Increase temperature target above radiant capacity
5. Boost activates when conditions met

### Auto-tune PID Controller

1. Navigate to room dashboard
2. Scroll to "PID Auto-tune"
3. Click "Auto-tune Radiant" or "Auto-tune Fancoil"
4. Wait 2-4 hours for completion
5. Check logs for results

### Check Sensor Failover

1. Navigate to room dashboard
2. Scroll to "Sensor Sources & Failover"
3. Compare "Active" vs "Modbus" vs "HA Fallback"
4. If Modbus is NAN, system uses HA fallback

### Control MEV Ventilation

1. Go to First Floor dashboard
2. Scroll to "MEV System"
3. Toggle power, mode, dehumidifier, cooling
4. Adjust target fan speed (0-100%)
5. Monitor CO₂ and IAQ demand sensors

---

## Mobile vs Desktop View

### Mobile Recommendations

- Use 2-3 columns max in grid sections
- Main dashboard: Best for quick checks
- Floor dashboards: Good for zone monitoring
- Room dashboards: May need scrolling
- System monitoring: Desktop recommended

### Desktop Recommendations

- Use 4-5 columns for better density
- Room dashboards: Full detail visible
- System monitoring: Ideal layout
- Multiple windows: Open floor + room side-by-side

---

## What to Monitor Daily

### Morning Check (30 seconds)

1. Climate Overview → Check all room temps
2. Verify heat pump mode matches season
3. Check for any "unavailable" entities

### Evening Check (1 minute)

1. Floor dashboards → Verify pumps running as expected
2. First floor → Check MEV air quality (CO₂ < 1000 ppm)
3. System Monitoring → Verify ESPHome uptime (no crashes)

### Weekly Check (5 minutes)

1. Room dashboards → Review PID output values (should be stable)
2. Historical graphs → Check for temperature oscillations
3. Boost status → Verify boost triggers make sense
4. Sensor failover → Ensure Modbus sensors healthy

---

## Advanced Tips

### Bookmark Favorite Dashboards

- Main: `http://homeassistant.local:8123/lovelace/climate-overview`
- Your bedroom: `http://homeassistant.local:8123/lovelace/camera-padronale`
- System monitoring: `http://homeassistant.local:8123/lovelace/system-monitoring`

### Create Automations

Use dashboard entities in automations:

```yaml
# Example: Alert on high CO₂
automation:
  - alias: High CO2 Alert
    trigger:
      - platform: numeric_state
        entity_id: sensor.max_co_primo_piano
        above: 1200
    action:
      - service: notify.mobile_app
        data:
          message: "High CO₂ detected on first floor: {{ states('sensor.max_co_primo_piano') }} ppm"
```

### Use Templates

Monitor multiple rooms at once:

```yaml
sensor:
  - platform: template
    sensors:
      all_rooms_max_temp:
        friendly_name: "Max Temperature (All Rooms)"
        unit_of_measurement: "°C"
        value_template: >
          {{ [
            states('sensor.soggiorno_room_temp_abstracted'),
            states('sensor.cucina_room_temp_abstracted'),
            states('sensor.camera_nord_room_temp_abstracted')
            ] | map('float') | max }}
```

---

## Getting Help

**Dashboard not working?**
1. Check README.md (full documentation)
2. Verify configuration.yaml syntax
3. Check Home Assistant logs
4. Ensure ESPHome device online

**Entity names wrong?**
1. Use Developer Tools → States to find correct names
2. Update dashboard YAML files
3. Reload dashboard

**Performance issues?**
1. Reduce history graph time span
2. Use fewer columns on mobile
3. Check HA recorder database size

---

## Next Steps

- ✅ Dashboards installed and working
- 📖 Read full README.md for advanced features
- 🎨 Customize layouts and add custom cards
- 🤖 Create automations using dashboard entities
- 📊 Add custom sensors and charts

**Documentation**: See `README.md` in the same directory for complete guide.

**ESPHome Source**: See `/components/` and `/devices/` for entity definitions.

---

**Happy monitoring!** 🏠🌡️
