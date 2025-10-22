# Room Sensor Technology Selection

**Project:** ESPHome Multi-Floor Climate Control  
**Story:** 1.6 - Room Temperature and Humidity Sensor Integration  
**Date:** October 22, 2025  
**Decision:** Modbus RS485 Temperature/Humidity Sensors (Option A)

---

## Executive Summary

After comprehensive evaluation of two sensor technology approaches, **Modbus RS485 temperature/humidity sensors** have been selected for room-level climate sensing. This decision prioritizes system integration consistency, professional-grade reliability, and scalability over initial cost savings.

**Key Factors:**
- Seamless integration with existing Modbus infrastructure (Stories 1.1-1.5)
- Industrial-grade accuracy and reliability
- Simplified future expansion to first and second floors
- Standardized protocol across all inter-board communication

---

## Technology Comparison

### Option A: Modbus RS485 Temperature/Humidity Sensors

**Architecture:**
- Each room sensor = standalone Modbus slave device
- Master (gruppo-miscelazione A6) polls sensors every 30 seconds
- Sensor data written to master holding registers (400-407)
- Slave boards (distribuzione-piano-terra A16) read room data from master
- Digital communication eliminates analog noise and wiring complexity

**Recommended Sensor Models:**
- **XY-MD02**: Modbus RTU temperature/humidity sensor (~$35-45)
  - Temperature: -40°C to +80°C, ±0.3°C accuracy
  - Humidity: 0-100% RH, ±3% accuracy
  - RS485 interface, configurable address (0-247)
  - 12-24V DC powered
  
- **AM2301-MB**: Industrial Modbus temp/humidity sensor (~$40-50)
  - Temperature: -40°C to +80°C, ±0.5°C accuracy
  - Humidity: 0-100% RH, ±2% accuracy
  - Built-in RS485 converter
  - DIN rail mountable

**Specifications:**
- **Communication:** RS485 Modbus RTU, 9600 baud 8N1
- **Polling Interval:** 30 seconds (configurable)
- **Cable Runs:** Up to 1200m (RS485 specification)
- **Addressing:** Unique slave address per sensor (10-13 for ground floor)
- **Power:** 12-24V DC (can share power supply with ESP32 boards)

**Advantages:**
✅ **Protocol Consistency:** Same Modbus infrastructure as master/slave coordination  
✅ **Industrial Grade:** Professional sensors designed for HVAC/building automation  
✅ **Long Cable Runs:** RS485 supports up to 1200m (far exceeds residential needs)  
✅ **Digital Communication:** No analog noise, no ADC calibration required  
✅ **Easy Expansion:** Add sensors by assigning new Modbus addresses  
✅ **Standardized Wiring:** Same twisted-pair shielded cable as existing RS485 bus  
✅ **Self-Contained:** Sensors include microcontroller, no external components needed  
✅ **Proven Technology:** Decades of industrial HVAC deployment experience  

**Disadvantages:**
❌ **Higher Initial Cost:** ~$40/sensor vs ~$8 for 1-Wire/I2C approach  
❌ **Bus Loading:** 4 additional Modbus devices increase polling cycle time  
❌ **Power Requirements:** Each sensor needs 12-24V DC power connection  
❌ **Address Configuration:** Sensors must be configured with unique addresses (DIP switches or software)  

**Cost Analysis (Ground Floor - 4 Zones):**
- 4× Modbus temp/humidity sensors: $160-180
- RS485 wiring (twisted-pair shielded): $20-30
- Power distribution (12V splitters): $15-20
- **Total:** ~$195-230

**Wiring Complexity:**
- Single RS485 bus shared with existing master/slave communication
- Daisy-chain topology: Master → Slave 2 → Sensor 10 → Sensor 11 → Sensor 12 → Sensor 13
- 2-wire communication (A/B) + 2-wire power (12V/GND) = 4 conductors total
- Termination resistor at last device (120Ω between A and B)

---

### Option B: 1-Wire + I2C Sensors (Not Selected)

**Architecture:**
- Dallas DS18B20 on existing 1-Wire buses (temperature)
- SHT3x or DHT22 on I2C bus (humidity)
- Local reading on slave board (no master involvement)
- Mixed technology stack (1-Wire + I2C)

**Specifications:**
- **Temperature:** Dallas DS18B20, ±0.5°C accuracy, 1-Wire protocol
- **Humidity:** SHT3xd (I2C, ±2% RH) or DHT22 (1-Wire, ±5% RH)
- **Cable Runs:** 1-Wire: ~100m, I2C: ~5m (extenders required)
- **Power:** 3.3V from ESP32 board

**Advantages:**
✅ **Lower Cost:** ~$3 DS18B20 + ~$5 SHT3x = $8/zone vs $40 Modbus  
✅ **No Bus Loading:** Local sensors don't impact Modbus polling  
✅ **Simple Power:** 3.3V from ESP32 board (no external power supply)  
✅ **Proven ESPHome:** Native platform support, well-documented  

**Disadvantages:**
❌ **Mixed Technologies:** Two different protocols for temp/humidity  
❌ **Limited Cable Runs:** I2C requires <5m without extenders  
❌ **Bus Scanning Overhead:** 1-Wire discovery adds CPU load  
❌ **Less Professional:** Consumer-grade sensors vs industrial Modbus  
❌ **Expansion Complexity:** First floor needs separate I2C buses or extenders  
❌ **Master Independence Lost:** Sensors only available to local board  

**Cost Analysis (Ground Floor - 4 Zones):**
- 4× Dallas DS18B20: $12
- 4× SHT3x I2C humidity: $20-40
- 1-Wire/I2C wiring: $10-15
- **Total:** ~$42-67

**Why Not Selected:**
- Inconsistent with system architecture (Modbus master/slave coordination)
- I2C cable length restrictions problematic for distributed rooms
- Mixed technology stack increases maintenance complexity
- Doesn't leverage existing RS485 infrastructure investment
- Future expansion to first/second floors requires different approach

---

## Decision Rationale

### 1. **System Architecture Consistency**

The existing climate control system (Stories 1.1-1.5) is built on Modbus RTU master/slave coordination:
- Master (A6) coordinates climate mode and mixing valve temperatures
- Slaves (A16 ground/first floor) read coordination data via Modbus
- Adding Modbus room sensors extends this pattern naturally

**1-Wire/I2C Approach Would Create Architectural Inconsistency:**
- Room sensors isolated to local board (can't share with master or other slaves)
- Master has no visibility into room conditions
- Future multi-zone coordination features (e.g., load balancing) more complex

**Modbus Approach Maintains Consistency:**
- All inter-board communication uses single protocol (Modbus RTU)
- Master can log/monitor all room temperatures centrally
- Future features (e.g., "first floor borrows heat from ground floor") trivial to implement

### 2. **Long-Term Scalability**

**Near-Term Expansion (Story 1.6 → 1.7+):**
- First floor: Add 4 more Modbus sensors (addresses 14-17)
- Second floor: Add 2-3 more Modbus sensors (addresses 18-20)
- **Total:** 10-11 sensors on same RS485 bus

**Modbus Scales Naturally:**
- Single bus supports up to 247 devices
- Polling 10 sensors @ 30s interval = negligible impact (<1s total cycle time)
- Wiring: extend daisy-chain to new floor (same cable type)

**1-Wire/I2C Scaling Challenges:**
- I2C requires extenders for first floor (additional hardware cost/complexity)
- Multiple I2C buses needed to avoid address conflicts
- 1-Wire bus loading increases with sensor count (slower scans)

### 3. **Professional-Grade Reliability**

**Target Use Case:** Year-round climate control for primary residence
- System must operate 24/7 with minimal maintenance
- Sensor failures impact comfort and energy efficiency
- Industrial-grade components reduce failure risk

**Modbus Sensors:**
- Designed for building automation (HVAC, industrial controls)
- Self-contained (microcontroller, power regulation, RS485 driver onboard)
- Proven reliability (decades of industrial deployment)

**1-Wire/I2C Sensors:**
- Consumer-grade (hobbyist/maker market)
- Bare sensor chips (require PCB design, soldering, enclosure)
- More susceptible to electromagnetic interference

### 4. **Installation and Maintenance**

**Modbus Sensors:**
- Pre-assembled units with screw terminals (no soldering)
- DIN rail mountable or wall-mount enclosures available
- Address configuration via DIP switches (one-time setup)
- Standardized troubleshooting (Modbus scan tools)

**1-Wire/I2C Sensors:**
- Requires custom PCB or breadboard assembly
- Soldering required for cable connections
- Address conflicts harder to diagnose (requires oscilloscope/logic analyzer)
- No standardized enclosures (3D printing or custom fabrication)

### 5. **Future-Proofing**

**Modbus Ecosystem:**
- Standardized protocol (IEC 61158, widely adopted)
- Extensive industrial sensor catalog (CO2, pressure, light, occupancy available)
- Easy to integrate third-party HVAC equipment (VRF systems, heat pumps)

**1-Wire/I2C Ecosystem:**
- Limited to hobby/maker sensors
- No industrial-grade room sensors with both temp/humidity on single I2C address
- Third-party HVAC equipment rarely supports 1-Wire/I2C

### 6. **Cost-Benefit Analysis**

**Initial Cost Difference:**
- Modbus: $195-230 for ground floor
- 1-Wire/I2C: $42-67 for ground floor
- **Delta:** ~$150 additional for Modbus

**Long-Term Value:**
- **Reliability:** Industrial-grade sensors reduce failure rate (fewer service calls)
- **Scalability:** No architectural changes needed for first/second floor expansion
- **Maintenance:** Standardized troubleshooting reduces repair time
- **Resale Value:** Professional-grade system increases home value

**Payback Period:**
- Improved temperature control accuracy: ~2-5% energy savings
- Typical residential HVAC cost: $1500/year
- Annual savings: $30-75/year
- Payback: 2-5 years (plus reduced maintenance costs)

---

## Wiring Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Master (A6 - gruppo-miscelazione)                               │
│ Address 1                                                       │
│ RS485 TX: GPIO27, RX: GPIO14                                    │
└───────────────┬─────────────────────────────────────────────────┘
                │ RS485 Bus (A/B twisted pair + 12V/GND)
                ├─ 120Ω termination resistor
                │
┌───────────────▼─────────────────────────────────────────────────┐
│ Slave (A16 - distribuzione-piano-terra)                        │
│ Address 2                                                       │
│ RS485 TX: GPIO13, RX: GPIO16                                    │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ├─ Daisy-chain to room sensors
                │
┌───────────────▼─────────────────────────────────────────────────┐
│ Room Sensor: Soggiorno                                          │
│ Modbus Address 10                                               │
│ Temp: -40 to +80°C, Humidity: 0-100% RH                         │
└───────────────┬─────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────┐
│ Room Sensor: Cucina                                             │
│ Modbus Address 11                                               │
└───────────────┬─────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────┐
│ Room Sensor: Bagno                                              │
│ Modbus Address 12                                               │
└───────────────┬─────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────┐
│ Room Sensor: Anticamera                                         │
│ Modbus Address 13                                               │
└───────────────┬─────────────────────────────────────────────────┘
                │
                └─ 120Ω termination resistor (at last device)

Cable: 4-conductor shielded
- A (RS485+): Twisted pair conductor 1
- B (RS485-): Twisted pair conductor 2
- 12V: Power positive
- GND: Power ground
- Shield: Connected to earth ground at master only
```

**Wiring Notes:**
1. **Topology:** Daisy-chain (not star) to minimize reflections
2. **Termination:** 120Ω resistor between A and B at both ends (master and last sensor)
3. **Cable:** Cat5e/Cat6 works (use one twisted pair for A/B, another for power)
4. **Shield:** Connect shield to earth ground at master end only (avoid ground loops)
5. **Power:** 12V DC regulated supply (ESP32 boards already have 12V available)
6. **Length:** Each sensor typically <10m from previous device (ground floor rooms)

---

## Modbus Register Allocation

### Master Holding Registers (gruppo-miscelazione A6)

**Room Sensor Data (Read by Slaves):**

| Register | Address | Name                  | Type   | Description                 | Scaling | Unit    |
| -------- | ------- | --------------------- | ------ | --------------------------- | ------- | ------- |
| 400      | 0x0190  | `soggiorno_temp`      | INT16  | Soggiorno room temperature  | ×100    | 0.01°C  |
| 401      | 0x0191  | `soggiorno_humidity`  | UINT16 | Soggiorno room humidity     | ×10     | 0.1% RH |
| 402      | 0x0192  | `cucina_temp`         | INT16  | Cucina room temperature     | ×100    | 0.01°C  |
| 403      | 0x0193  | `cucina_humidity`     | UINT16 | Cucina room humidity        | ×10     | 0.1% RH |
| 404      | 0x0194  | `bagno_temp`          | INT16  | Bagno room temperature      | ×100    | 0.01°C  |
| 405      | 0x0195  | `bagno_humidity`      | UINT16 | Bagno room humidity         | ×10     | 0.1% RH |
| 406      | 0x0196  | `anticamera_temp`     | INT16  | Anticamera room temperature | ×100    | 0.01°C  |
| 407      | 0x0197  | `anticamera_humidity` | UINT16 | Anticamera room humidity    | ×10     | 0.1% RH |

**Scaling Rationale:**
- **Temperature ×100:** Preserves 0.01°C precision in 16-bit register (e.g., 22.35°C = 2235)
- **Humidity ×10:** Preserves 0.1% RH precision (e.g., 65.3% = 653)
- **INT16 for temp:** Allows negative temperatures (-40°C to +80°C range)
- **UINT16 for humidity:** Humidity is always positive (0-100% RH)

### Room Sensor Modbus Addresses

| Modbus Address | Location   | Physical Location | Notes                 |
| -------------- | ---------- | ----------------- | --------------------- |
| 10 (0x0A)      | Soggiorno  | Living room       | Primary zone          |
| 11 (0x0B)      | Cucina     | Kitchen           | High humidity zone    |
| 12 (0x0C)      | Bagno      | Bathroom          | Highest humidity zone |
| 13 (0x0D)      | Anticamera | Entryway          | Buffer zone           |

**Address Configuration:**
- Configured via DIP switches on sensor or software command (see sensor manual)
- Verify addresses before installation using Modbus scan tool
- Document actual addresses in installation notes

---

## Polling Sequence and Timing

### Master Polling Cycle (30 seconds)

```
Master (A6) Polling Sequence:
  ┌─ Start of cycle ─────────────────────────────────────────────┐
  │                                                               │
  ├─ 1. Poll Slave 2 (Ground Floor A16) ─────────── ~100ms       │
  │    Read status registers 0-5                                 │
  │                                                               │
  ├─ 2. Poll Slave 3 (First Floor A16) ──────────── ~100ms       │
  │    Read status registers 0-5                                 │
  │                                                               │
  ├─ 3. Poll Room Sensor 10 (Soggiorno) ───────── ~50ms         │
  │    Read temp/humidity registers                              │
  │                                                               │
  ├─ 4. Poll Room Sensor 11 (Cucina) ─────────── ~50ms          │
  │    Read temp/humidity registers                              │
  │                                                               │
  ├─ 5. Poll Room Sensor 12 (Bagno) ──────────── ~50ms          │
  │    Read temp/humidity registers                              │
  │                                                               │
  ├─ 6. Poll Room Sensor 13 (Anticamera) ────── ~50ms           │
  │    Read temp/humidity registers                              │
  │                                                               │
  ├─ 7. Write room data to master registers ───── ~20ms          │
  │    Update registers 400-407 with sensor values               │
  │                                                               │
  └─ Total cycle time: ~420ms ──────────────────────────────────┘
      (leaves ~29.5s idle time until next cycle)
```

**Performance Analysis:**
- **Total Polling Time:** ~420ms per cycle
- **Cycle Interval:** 30 seconds
- **Bus Utilization:** 1.4% (420ms / 30000ms)
- **Slack Time:** 29.5 seconds (ample margin for retries/errors)

**Error Handling:**
- Timeout per device: 1 second
- Retry on error: 2 attempts
- Failed device marked stale (slaves failover to HA sensors)
- Master continues polling other devices even if one fails

---

## Installation Guide

### Pre-Installation Checklist

- [ ] Modbus sensors procured (4× XY-MD02 or AM2301-MB)
- [ ] Sensors configured with unique addresses (10-13)
- [ ] RS485 cable available (4-conductor shielded, ~50m total)
- [ ] 12V DC power supply (1A minimum for 4 sensors)
- [ ] Termination resistors (2× 120Ω, 1/4W)
- [ ] Screwdriver set (for sensor terminals)
- [ ] Multimeter (for cable testing)
- [ ] Modbus scan tool (optional, for verification)

### Installation Steps

**Step 1: Sensor Address Configuration**
1. Connect each sensor to 12V power + RS485 bus (temporary bench setup)
2. Configure address via DIP switches (see sensor manual)
   - Sensor 1: Address 10 (0x0A)
   - Sensor 2: Address 11 (0x0B)
   - Sensor 3: Address 12 (0x0C)
   - Sensor 4: Address 13 (0x0D)
3. Verify addresses using Modbus scan tool (optional)
4. Label sensors with physical location (Soggiorno, Cucina, etc.)

**Step 2: Physical Installation**
1. **Soggiorno (Living Room):**
   - Mount sensor at ~1.5m height, away from windows/doors
   - Avoid direct sunlight, heating vents, and air return locations
   - Route cable back to master location (A6 board)

2. **Cucina (Kitchen):**
   - Mount sensor away from stove, oven, and refrigerator
   - Avoid placement near range hood (high airflow)

3. **Bagno (Bathroom):**
   - Mount sensor away from shower/tub (avoid direct water spray)
   - Good air circulation location (humidity monitoring critical)

4. **Anticamera (Entryway):**
   - Mount sensor in central location (buffer zone between outdoor/indoor)

**Step 3: Wiring**
1. Run 4-conductor shielded cable from master (A6) to first sensor (Soggiorno)
2. Daisy-chain to remaining sensors: Soggiorno → Cucina → Bagno → Anticamera
3. Connect terminals:
   - **A (RS485+):** Green or White/Blue wire
   - **B (RS485-):** Yellow or Blue wire
   - **12V:** Red wire
   - **GND:** Black wire
   - **Shield:** Connect to earth ground at master only
4. Install 120Ω termination resistor at master (between A and B)
5. Install 120Ω termination resistor at last sensor (Anticamera, between A and B)

**Step 4: Power-On and Verification**
1. Apply 12V power to sensor chain
2. Verify all sensors power on (LED indicators if available)
3. Deploy updated master firmware (includes room sensor polling)
4. Monitor ESPHome logs for successful Modbus communication
5. Verify room temperature/humidity sensors appear in Home Assistant

### Troubleshooting

**Issue: No Communication with Sensors**
- Check termination resistors installed at both ends
- Verify 12V power reaching all sensors
- Check A/B wiring polarity (swap if needed)
- Verify sensor addresses configured correctly

**Issue: Intermittent Communication**
- Check cable shield grounded at master only (not at sensors)
- Verify cable routing away from high-voltage AC lines
- Check cable terminations (no loose connections)

**Issue: Incorrect Temperature/Humidity Readings**
- Verify sensor placement away from heat sources
- Check for direct sunlight exposure
- Allow 1-2 hours for sensors to stabilize after power-on

---

## Future Expansion Path

### First Floor (Story 1.7+)

**Additional Sensors:**
- 4× Modbus temp/humidity sensors (addresses 14-17)
- Extend RS485 daisy-chain from ground floor to first floor
- Update master polling to include addresses 14-17
- Update master registers 408-415 for first floor data

**Wiring:**
- Extend cable from last ground floor sensor (Anticamera) to first floor
- Cable run: ~5-10m vertical + ~20-30m horizontal (within RS485 limits)
- Move termination resistor from Anticamera to last first-floor sensor

### Second Floor (Future)

**Additional Sensors:**
- 2-3× Modbus temp/humidity sensors (addresses 18-20)
- Continue daisy-chain to second floor
- Update master registers 416-421

**Total System Capacity:**
- Master: Address 1
- Slave 1 (Ground floor A16): Address 2
- Slave 2 (First floor A16): Address 3
- 0-10V Adapter: Address 4
- Room Sensors (Ground): Addresses 10-13 (4 sensors)
- Room Sensors (First): Addresses 14-17 (4 sensors)
- Room Sensors (Second): Addresses 18-20 (3 sensors)
- **Total:** 18 devices on single RS485 bus (well within 247 device limit)

### Alternative Sensors (Future)

**CO2 Monitoring:**
- Add Modbus CO2 sensors (addresses 30-35)
- Demand-based ventilation control
- Air quality monitoring

**Occupancy Detection:**
- Add Modbus PIR/radar sensors (addresses 40-45)
- Automatic setpoint adjustment based on occupancy
- Energy savings when rooms unoccupied

---

## Conclusion

**Modbus RS485 temperature/humidity sensors** provide the optimal balance of:
- **Integration Consistency:** Extends existing Modbus architecture naturally
- **Professional Reliability:** Industrial-grade components for 24/7 operation
- **Scalability:** Easy expansion to additional floors without architectural changes
- **Maintainability:** Standardized protocol simplifies troubleshooting

While the initial cost is higher than 1-Wire/I2C alternatives, the long-term benefits in reliability, scalability, and system consistency justify the investment for a critical residential climate control system.

**Next Steps:**
1. Procure 4× Modbus temp/humidity sensors (XY-MD02 or equivalent)
2. Configure sensor addresses (10-13)
3. Install sensors in ground floor zones
4. Update ESPHome master component to poll sensors
5. Update slave component to read room data from master
6. Implement PID controller migration (supply temp → room temp)

---

**Document Revision History:**
- v1.0 (October 22, 2025): Technology selection complete - Option A (Modbus) selected
