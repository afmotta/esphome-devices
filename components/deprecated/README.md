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

## Migration Guide

See `docs/epic-2-migration-guide.md` for complete migration instructions and examples.

## Reference Purposes Only

These components are retained for:
- Historical reference
- Understanding old device configurations
- Rollback scenarios (if needed)

**Do not use these components in new configurations.**
