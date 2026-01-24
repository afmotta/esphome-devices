# Epic 6: MEV Wiring Diagram

**Board:** KC868-A6 (ESP32)  
**MEV Unit:** Cappellotto AIR FRESH I H EVO  
**Location:** First Floor Mechanical Room  
**Date:** October 30, 2025

---

## Overview

This document provides complete wiring instructions for connecting the KC868-A6 ESPHome board to the Cappellotto AIR FRESH I H EVO MEV unit. The board controls 4 relay outputs, 1 analog 0-10V fan speed output, and monitors 1 alarm input.

---

## Hardware Required

### Components
- **KC868-A6 Board** (1x) - Main controller
- **12V DC Power Supply** (1x) - Board power (min 1A)
- **Wire 18-22 AWG** - For relay connections
- **Shielded 2-conductor wire** - For 0-10V analog signal
- **Ferrule crimps or terminal blocks** - Connection termination
- **Multimeter** - Pre-installation testing

### Optional
- **DIN rail mount** - For board mounting
- **Enclosure** - Protect board from dust/moisture
- **Cable labels** - Document connections

---

## Safety Warnings

⚠️ **CRITICAL SAFETY NOTES:**

1. **Disconnect MEV Unit Power** before starting any wiring work
2. **Verify Voltage Levels** - All relay contacts must match MEV input voltage ratings
3. **Never Hot-Wire** - Always power off before connecting/disconnecting
4. **0-10V Polarity** - Incorrect polarity may damage MEV controller
5. **Test First** - Verify all outputs with multimeter before connecting to MEV
6. **Follow Local Codes** - Ensure electrical work complies with local regulations

---

## KC868-A6 Pin Reference

### Relay Outputs (PCF8574 I2C Expander at 0x24)
The KC868-A6 uses a PCF8574 I2C expander for relay control. Relays are **active-low** (inverted in software).

| Relay ID | PCF8574 Pin | Physical Terminal  | Contact Type | MEV Function  |
| -------- | ----------- | ------------------ | ------------ | ------------- |
| relay_1  | Output 0    | RELAY1 (NO/NC/COM) | SPDT         | Power         |
| relay_2  | Output 1    | RELAY2 (NO/NC/COM) | SPDT         | Winter/Summer |
| relay_3  | Output 2    | RELAY3 (NO/NC/COM) | SPDT         | Dehumidifier  |
| relay_4  | Output 3    | RELAY4 (NO/NC/COM) | SPDT         | Cooling       |

**Contact Ratings:** 10A @ 250VAC, 10A @ 30VDC (verify MEV requirements)

### DAC Output (0-10V Analog)
Built-in ESP32 DAC with 0-10V output capability.

| Output ID | GPIO Pin | Physical Terminal | Voltage Range | MEV Function |
| --------- | -------- | ----------------- | ------------- | ------------ |
| dac_1     | GPIO26   | DAC1 (+/-)        | 0-10V DC      | Fan Speed    |

**Signal:** Linear 0%=0V, 100%=10V  
**Load:** High impedance (>10kΩ typical for 0-10V inputs)  
**Wire:** Use shielded twisted pair for noise immunity

### Binary Input (Alarm Monitoring)
PCF8574 I2C expander at 0x22 for digital inputs.

| Input ID | PCF8574 Pin | Physical Terminal | Logic       | MEV Function |
| -------- | ----------- | ----------------- | ----------- | ------------ |
| input_1  | Input 0     | INPUT1 (+/-)      | Active HIGH | Alarm        |

**Logic:** Closed circuit = HIGH (alarm active), Open = LOW (normal)  
**Voltage:** 3.3V logic (internal pull-up)

---

## Wiring Connections

### Connection 1: Main Power Relay

**Purpose:** Turns MEV unit on/off

**KC868-A6 Side:**
- Terminal: RELAY1
- Use: COM and NO (Normally Open)

**MEV Unit Side:**
- Terminal: [Verify with MEV manual - typically "POWER" or "ON/OFF"]
- Function: Main power enable

**Wiring:**
```
KC868-A6 RELAY1 COM  ──────┐
                           │  [MEV Power Control Input]
KC868-A6 RELAY1 NO   ──────┘
```

**Wire:** 18-20 AWG, rated for MEV control voltage  
**State Logic:** Relay ON (closed) = MEV powered, Relay OFF (open) = MEV off

---

### Connection 2: Winter/Summer Mode Relay

**Purpose:** Switches MEV between winter and summer operating modes

**KC868-A6 Side:**
- Terminal: RELAY2
- Use: COM and NO

**MEV Unit Side:**
- Terminal: [Verify with MEV manual - typically "MODE" or "W/S"]
- Function: Season mode select

**Wiring:**
```
KC868-A6 RELAY2 COM  ──────┐
                           │  [MEV Mode Control Input]
KC868-A6 RELAY2 NO   ──────┘
```

**Wire:** 18-20 AWG  
**State Logic:** Relay ON = Summer mode, Relay OFF = Winter mode  
*(Verify exact logic with MEV documentation - may be inverted)*

---

### Connection 3: Dehumidifier Relay

**Purpose:** Activates integrated dehumidifier function

**KC868-A6 Side:**
- Terminal: RELAY3
- Use: COM and NO

**MEV Unit Side:**
- Terminal: [Verify with MEV manual - typically "DEHUMID" or "DRY"]
- Function: Dehumidification mode enable

**Wiring:**
```
KC868-A6 RELAY3 COM  ──────┐
                           │  [MEV Dehumidifier Control]
KC868-A6 RELAY3 NO   ──────┘
```

**Wire:** 18-20 AWG  
**State Logic:** Relay ON = Dehumidifier active, Relay OFF = Normal ventilation

---

### Connection 4: Cooling Integration Relay

**Purpose:** Enables MEV integration with cooling system

**KC868-A6 Side:**
- Terminal: RELAY4
- Use: COM and NO

**MEV Unit Side:**
- Terminal: [Verify with MEV manual - typically "COOLING" or "AC"]
- Function: Cooling integration enable

**Wiring:**
```
KC868-A6 RELAY4 COM  ──────┐
                           │  [MEV Cooling Integration]
KC868-A6 RELAY4 NO   ──────┘
```

**Wire:** 18-20 AWG  
**State Logic:** Relay ON = Cooling coordination active, Relay OFF = Independent operation

---

### Connection 5: Fan Speed (0-10V DAC Output)

**Purpose:** Controls MEV fan speed continuously from 0-100%

**KC868-A6 Side:**
- Terminal: DAC1
- Pins: DAC1(+) and GND(-)

**MEV Unit Side:**
- Terminal: [Verify with MEV manual - typically "0-10V" or "SPEED"]
- Polarity: Check MEV manual (usually + and GND)

**Wiring:**
```
KC868-A6 DAC1(+)  ────────────  MEV 0-10V Input (+)
                   Shielded
                   Twisted Pair
KC868-A6 GND(-)   ────────────  MEV 0-10V Input (-)
```

**Wire:** 22-24 AWG shielded twisted pair  
**Shield Connection:** Ground shield at ONE end only (KC868-A6 side) to prevent ground loops  
**Voltage:** 0V = 0% fan speed, 10V = 100% fan speed (linear)  
**Impedance:** MEV input should be >10kΩ (verify specification)

**⚠️ Important Notes:**
- Verify polarity before connecting—reversed polarity may damage MEV controller
- Keep 0-10V wire away from AC power wires to minimize noise
- Maximum wire length: 30m (100ft) for shielded cable
- Test voltage with multimeter before connecting to MEV

---

### Connection 6: Alarm Input (Binary Sensor)

**Purpose:** Monitors MEV alarm/fault condition

**KC868-A6 Side:**
- Terminal: INPUT1
- Pins: INPUT1(+) and GND(-)

**MEV Unit Side:**
- Terminal: [Verify with MEV manual - typically "ALARM" or "FAULT"]
- Type: Dry contact or open collector output

**Wiring:**
```
KC868-A6 INPUT1(+) ────────────  MEV Alarm Output (+)

KC868-A6 GND(-)    ────────────  MEV Alarm Output (-)
```

**Wire:** 22-24 AWG  
**Logic:** Closed circuit = Alarm active (HA shows "problem"), Open = Normal  
**Pull-up:** Internal 3.3V pull-up enabled in software

**⚠️ Note:** If MEV alarm output is voltage-based (not dry contact), verify it's 3.3V compatible

---

## Power Supply Connections

### KC868-A6 Power Input

**Requirements:**
- Voltage: 12V DC
- Current: Minimum 1A (2A recommended for margin)
- Type: Regulated DC power supply

**Wiring:**
```
12V Power Supply (+) ────────────  KC868-A6 VIN(+)

12V Power Supply (-) ────────────  KC868-A6 GND(-)
```

**⚠️ Important:**
- Verify polarity before connecting power
- Use power supply with overcurrent protection
- Mount power supply in ventilated location
- Consider UPS backup for continuous operation

---

## Installation Steps

### Pre-Installation Testing (Critical!)

Before connecting to MEV unit, test all outputs on bench:

1. **Power Test:**
   - Connect 12V power supply to KC868-A6
   - Verify board LED illuminates
   - Check WiFi connectivity (board should appear in HA)

2. **Relay Test:**
   - Use multimeter in continuity mode
   - For each relay (1-4):
     - Measure COM to NO (should be OPEN when relay OFF)
     - Activate relay from HA
     - Verify COM to NO closes (continuity)
   - Document any reversed behavior

3. **DAC Output Test:**
   - Set multimeter to DC voltage mode
   - Measure DAC1(+) to GND(-)
   - Set fan speed to 0% in HA → expect ~0V
   - Set fan speed to 50% in HA → expect ~5V
   - Set fan speed to 100% in HA → expect ~10V
   - Verify linear response across range

4. **Alarm Input Test:**
   - Monitor alarm sensor in HA
   - Short INPUT1(+) to GND → expect "problem" state
   - Open INPUT1 → expect "clear" state

### Physical Installation

1. **Mount Board:**
   - Choose location near MEV unit (minimize wire runs)
   - Ensure ventilation (ESP32 generates heat)
   - Protect from moisture and dust (consider enclosure)
   - Allow access for future maintenance

2. **Route Wiring:**
   - Plan wire paths before cutting
   - Separate low-voltage (0-10V) from relay wires if possible
   - Use cable management (conduit, wire loom)
   - Label all wires at both ends

3. **Terminate Connections:**
   - Strip wire to appropriate length (5-7mm typical)
   - Use ferrule crimps for solid termination
   - Double-check polarity on 0-10V and power connections
   - Verify wire gauge matches terminal capacity

4. **Final MEV Connection:**
   - **Power off MEV unit** at breaker
   - Connect all 6 interfaces following diagrams above
   - Double-check all connections against this document
   - Verify no loose strands or exposed conductors

5. **Power-Up Sequence:**
   - Apply power to KC868-A6 first
   - Verify board boots and connects to WiFi
   - Verify all entities appear in Home Assistant
   - **Then** restore power to MEV unit
   - Test each relay function individually
   - Test fan speed control across range
   - Verify alarm input reads correctly

---

## Testing Procedures

See `docs/epic-6-mev-testing-checklist.md` for complete testing procedures.

Quick verification:
- ✅ All 4 relays toggle when commanded from HA
- ✅ Fan speed slider adjusts output voltage linearly
- ✅ Alarm sensor responds to MEV alarm condition
- ✅ MEV unit operates correctly under ESPHome control

---

## Troubleshooting

### Issue: Relay doesn't toggle MEV function

**Check:**
- Verify relay makes/breaks contact with multimeter
- Check wire connections at both ends
- Verify MEV input voltage matches relay contact rating
- Check if MEV requires different contact (NO vs NC)

### Issue: 0-10V output doesn't control fan speed

**Check:**
- Measure voltage at KC868-A6 DAC terminal (should vary 0-10V)
- Measure voltage at MEV input terminal (should match KC868-A6)
- Verify wire continuity (no breaks)
- Check for ground loops (shield connected at one end only)
- Verify MEV 0-10V input impedance is >10kΩ

### Issue: Alarm input always shows "problem"

**Check:**
- Verify alarm wire isn't shorted to ground
- Check MEV alarm output type (dry contact vs voltage)
- Measure voltage at INPUT1 (should be 3.3V when open)
- Verify alarm logic isn't inverted (may need software adjustment)

---

## Wire Schedule Reference

| From          | To               | Wire Type          | Length | Function      |
| ------------- | ---------------- | ------------------ | ------ | ------------- |
| RELAY1 COM/NO | MEV Power        | 18 AWG             | [TBD]  | Power Control |
| RELAY2 COM/NO | MEV Mode         | 18 AWG             | [TBD]  | W/S Mode      |
| RELAY3 COM/NO | MEV Dehumidifier | 18 AWG             | [TBD]  | Dehumidifier  |
| RELAY4 COM/NO | MEV Cooling      | 18 AWG             | [TBD]  | Cooling       |
| DAC1/GND      | MEV 0-10V Input  | 22 AWG Shielded TP | [TBD]  | Fan Speed     |
| INPUT1/GND    | MEV Alarm Output | 22 AWG             | [TBD]  | Alarm Monitor |
| VIN/GND       | 12V PSU          | 18 AWG             | [TBD]  | Board Power   |

*TP = Twisted Pair*

---

## Revision History

| Version | Date         | Changes                        |
| ------- | ------------ | ------------------------------ |
| 1.0     | Oct 30, 2025 | Initial wiring diagram created |

---

**⚠️ FINAL REMINDER:** Always verify MEV unit terminal functions and voltage requirements with manufacturer documentation before making connections. This diagram provides the KC868-A6 interface; MEV-side terminals must be confirmed for your specific model.
