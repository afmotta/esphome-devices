---
stepsCompleted: [1, 2]
inputDocuments:
  - "docs/VMC MODBUS.pdf"
  - "components/mev.yaml"
date: 2026-02-01
author: Alberto
project_name: MEV Modbus Migration
---

# Product Brief: MEV Modbus Migration

## Executive Summary

This project implements a Modbus-first integration for the Cappellotto Air Fresh I VMC (Mechanical Extract Ventilation) as part of a greenfield installation. The VMC exposes a comprehensive Modbus RTU interface enabling direct register-based control, rich telemetry, and detailed diagnostics. By using Modbus for control signals (on/off, mode, dehumidify, integration) while retaining the existing 0-10V DAC for continuous fan speed modulation, the integration achieves a lean architecture that frees 4 relays for future use, provides access to 5 internal temperature sensors, exposes 39 distinct alarm types, and enables component-level visibility and predictive maintenance through filter hour tracking.

---

## Core Vision

### Problem Statement

The planned MEV installation requires a control interface. Two approaches are possible:

1. **Relay-based control** (legacy pattern): 4 relays for power/mode/dehumidify/cooling + 0-10V DAC for fan speed
2. **Modbus-first control** (proposed): Modbus writes for all control signals + 0-10V DAC for fan speed

The relay-based approach:
- **Consumes 4 relays** that could serve other purposes
- **Provides no diagnostic visibility** - only a single generic alarm binary sensor
- **Cannot access internal VMC sensors** (outdoor temp, water temp, exhaust temp, etc.)
- **Lacks maintenance tracking** - no visibility into filter hours or equipment runtime

### Problem Impact

- **Resource inefficiency**: 4 relays dedicated to VMC control that could serve zone expansion
- **Troubleshooting blind spots**: When alarms occur, physical inspection of the VMC would be required
- **Suboptimal automation**: Control logic cannot factor in VMC internal temperatures
- **Reactive maintenance**: No visibility into filter hours means calendar-based, not condition-based maintenance

### Why Existing Solutions Fall Short

The relay-based pattern in `components/mev.yaml` was designed before the VMC's Modbus capabilities were documented. The Cappellotto Air Fresh I (electronics version K) exposes a full Modbus RTU interface at 9600 baud that provides:
- Read/write control registers for all operating modes
- Read-only sensor registers for 5 internal temperature probes
- Packed bit registers for component states and 39 alarm types
- Maintenance counters for filter and fan runtime

This capability was discovered via the manufacturer's Modbus protocol manual (`docs/VMC MODBUS.pdf`).

### Proposed Solution

Implement a **Modbus-first integration** that:

1. **Uses Modbus writes for control**:
   - On/Off control (register 1106) - replaces relay_18
   - Summer/Winter mode (register 1584) - replaces relay_19
   - Dehumidify request (register 1141) - replaces relay_20
   - Integration request (register 1140) - replaces relay_21

2. **Retains 0-10V DAC for fan speed**: Modbus only supports min/max speed configuration per mode, not continuous real-time control. The existing analog_output_7 provides 0-100% continuous modulation required by the demand-based algorithm.

3. **Adds comprehensive Modbus reads**:
   - Temperature sensors: outdoor (501), water (502), exhaust (503), freecooling (511), evaporation (512)
   - Component states: fans, compressor, dampers, valves (registers 385-386, 640-643)
   - Detailed alarms: 39 types via packed registers (769-771) plus cumulative (1104)
   - Maintenance: filter hours limit and current count (1603-1606)

4. **Requires one-time VMC configuration**: Set Modbus address (0x10) and parity (None) via external Modbus tool before connecting to the bus.

### Key Differentiators

| Aspect | Relay Approach | Modbus-First Approach |
|--------|---------------|----------------------|
| Relays consumed | 4 | 0 |
| Alarms | 1 generic | 39 detailed types |
| Internal sensors | 0 | 5 temperatures |
| Component visibility | None | Full (fans, compressor, dampers, valves) |
| Maintenance tracking | None | Filter hours counter |
| Fan speed control | 0-10V continuous | 0-10V continuous (unchanged) |
| Failover | N/A | None (greenfield) |

### Architectural Notes (from Party Mode Review)

**Serial Configuration:**
- VMC defaults: 9600 baud, 8E2 (Even parity, 2 stop bits)
- System bus: 9600 baud, 8N1 (No parity, 1 stop bit)
- **Action required**: Configure VMC parity to None via external Modbus tool before integration

**Bus Topology:**
- VMC joins existing shared bus with analog output board (0x01) and relay boards (0x02, 0x03)
- Address 0x10 assigned to VMC (gap left for potential future relay boards at 0x04-0x0F)

**Timeout Behavior:**
- No failover architecture (greenfield installation, strategy C)
- VMC holds last commanded state on Modbus communication loss
- ESP32 implements robust retry logic and Home Assistant alerting

**Headless Operation:**
- No wall panel connected
- Registers 500 (room temp) and 506 (room humidity) unavailable - not needed since S1 Pro sensors provide room data

