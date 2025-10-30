# Deprecated Components

This directory contains ESPHome component packages that have been deprecated and should not be used in new device configurations.

## Epic 2: PID Architecture Simplification (October 2025)

The following components were deprecated as part of Epic 2, which simplified the PID climate control architecture:

### dual_pid.yaml
**Deprecated:** October 22, 2025  
**Replaced by:** Direct `climate: - platform: pid` with both `heat_output` and `cool_output`  
**Reason:** Unnecessary complexity - ESPHome PID supports both modes natively

### valve_trigger.yaml
**Deprecated:** October 22, 2025  
**Replaced by:** Simple lambda automation based on `climate_mode` sensor  
**Reason:** Physical trigger pattern no longer needed for mode coordination

### mixing_valve.yaml
**Deprecated:** October 22, 2025  
**Replaced by:** Direct PID configuration in device files  
**Reason:** High-level wrapper around deprecated dual_pid pattern

## Epic 5: HA-Only Sensors with Emergency Shutdown (October 2025)

The following components were deprecated as part of Epic 5, which eliminated expensive Modbus sensors in favor of HA-only sensors:

### room_sensors_v4.yaml
**Deprecated:** October 29, 2025  
**Replaced by:** New `components/room_sensors.yaml` (v5)  
**Reason:** Cost reduction - eliminates Modbus RS485 sensors ($640+ hardware savings)

**Key Changes:**
- 3-tier failover (Modbus → HA → Emergency) simplified to 2-tier (HA → Emergency)
- Removed per-room `modbus_controller` definitions
- Removed humidity sensors (not needed for PID control)
- Emergency timeout: 5 min → 3 min (more responsive)
- Added recovery stability check (60s, prevents flapping)
- Code reduction: 220 lines → 211 lines (4% reduction)
- Entity reduction: 7 entities/room → 3 entities/room (57% reduction)

**Migration:**
- See `docs/epic-5-migration-guide.md` for step-by-step migration procedures
- Remove `modbus_controller_address` and `ha_humidity_sensor_id` vars from room component calls
- Update HA dashboards to use `text_sensor.{zone}_sensor_state` instead of `binary_sensor.{zone}_room_sensor_online`

## Migration Guides

- **Epic 2:** See `docs/epic-2-migration-guide.md` for PID simplification
- **Epic 5:** See `docs/epic-5-migration-guide.md` for HA-only sensor migration

## Reference Purposes Only

These components are retained for:
- Historical reference
- Understanding old device configurations
- Rollback scenarios (if needed)

**Do not use these components in new configurations.**
