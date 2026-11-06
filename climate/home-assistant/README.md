# climate/home-assistant/

Home Assistant-side artifacts for the HVAC (climate control) system.

- `dashboards/` — hand-authored Lovelace dashboard YAML and installer
  scripts/docs for the climate system (per-room cards, floor overviews,
  system monitoring). Not generated — see `dashboards/README.md` for
  installation and `dashboards/INDEX.md` for what's in each file.
- `ha-dashboard-config.yaml` — system-monitor dashboard (Modbus health,
  sensor failover), pasted into the HA raw dashboard editor.
- `ha-override-detection-config.yaml`, `ha-weather-config.yaml` — HA-side
  override-detection and weather configuration for the seasonal-mode
  coordinator. Nothing in ESPHome includes these files.
- `mev_helpers.yaml` — HA package with the `input_number` helpers the MEV
  demand stack reads (`climate/mev_demand.yaml`).
