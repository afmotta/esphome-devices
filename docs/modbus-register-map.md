# Modbus Register Map

This document defines the Modbus register layout for the ESPHome climate control system implementing RS485 Modbus RTU communication between master and slave controllers.

## Master Device: gruppo-miscelazione (Modbus Address 0x01)

**Board:** KC868-A6  
**Role:** Modbus Master  
**RS485:** TX=GPIO27, RX=GPIO14, 9600 baud, 8N1

### Holding Registers (Function Code 0x03 - Read by Slaves)

| Address (Hex) | Address (Dec) | Name                    | Type   | Description                     | Units | Scaling                 | Update Rate | Access |
| ------------- | ------------- | ----------------------- | ------ | ------------------------------- | ----- | ----------------------- | ----------- | ------ |
| 0x0064        | 100           | dallas_piano_terra_temp | INT16  | Ground floor supply temperature | °C    | ×100 (0.01°C precision) | 10s         | Read   |
| 0x00C8        | 200           | climate_mode            | UINT16 | System operation mode           | enum  | 0=off, 1=heat, 2=cool   | 10s         | Read   |
| 0x012C        | 300           | master_heartbeat        | UINT16 | Master liveness counter         | count | Increments from 0       | 10s         | Read   |
| 0x0190        | 400           | soggiorno_temp          | INT16  | Soggiorno room temperature      | °C    | ×100 (0.01°C precision) | 30s         | Read   |
| 0x0191        | 401           | soggiorno_humidity      | UINT16 | Soggiorno room humidity         | %RH   | ×10 (0.1% precision)    | 30s         | Read   |
| 0x0192        | 402           | cucina_temp             | INT16  | Cucina room temperature         | °C    | ×100 (0.01°C precision) | 30s         | Read   |
| 0x0193        | 403           | cucina_humidity         | UINT16 | Cucina room humidity            | %RH   | ×10 (0.1% precision)    | 30s         | Read   |
| 0x0194        | 404           | bagno_temp              | INT16  | Bagno room temperature          | °C    | ×100 (0.01°C precision) | 30s         | Read   |
| 0x0195        | 405           | bagno_humidity          | UINT16 | Bagno room humidity             | %RH   | ×10 (0.1% precision)    | 30s         | Read   |
| 0x0196        | 406           | anticamera_temp         | INT16  | Anticamera room temperature     | °C    | ×100 (0.01°C precision) | 30s         | Read   |
| 0x0197        | 407           | anticamera_humidity     | UINT16 | Anticamera room humidity        | %RH   | ×10 (0.1% precision)    | 30s         | Read   |

### Register Details

#### Register 100: Ground Floor Supply Temperature
- **Purpose:** Exposes the Dallas DS18B20 sensor reading for the ground floor (Piano Terra) mixing valve supply line
- **Source Sensor:** `dallas_0x81000000b3e6f628` (1-Wire bus on GPIO32)
- **Data Type:** Signed 16-bit integer (range: -327.68°C to +327.67°C)
- **Scaling:** Temperature in °C × 100
  - Example: 23.45°C → register value 2345
  - Example: -5.20°C → register value -520
- **Usage:** Slaves can read this to coordinate their heating/cooling based on master supply temperature
- **Update Frequency:** Every 10 seconds (faster than Dallas sensor's native 60s update)

#### Register 200: Climate Mode
- **Purpose:** Broadcast system-wide operating mode to all slaves
- **Source:** Home Assistant text sensor `sensor.thermostat_mode`
- **Data Type:** Unsigned 16-bit integer (enum)
- **Values:**
  - `0` = System off / idle
  - `1` = Heating mode active
  - `2` = Cooling mode active
- **Usage:** Slaves use this to switch their control logic without HA connectivity
- **Update Frequency:** Every 10 seconds

#### Register 300: Master Heartbeat
- **Purpose:** Liveness indicator for master controller
- **Data Type:** Unsigned 16-bit integer (0-65535)
- **Behavior:** Increments by 1 every 10 seconds, wraps to 0 at 65535
- **Usage:** Slaves monitor this register; if unchanged for >30s, master may be offline
- **Update Frequency:** Every 10 seconds

#### Registers 400-407: Room Temperature and Humidity (Story 1.6)
- **Purpose:** Expose Modbus RS485 room sensor data from ground floor zones
- **Source:** XY-MD02 or AM2301-MB Modbus temp/humidity sensors (addresses 10-13)
- **Master Polling:** Master polls sensors every 30 seconds, writes to these registers
- **Slave Reading:** Ground floor slave (Address 0x02) reads these registers for PID control

**Register 400: Soggiorno (Living Room) Temperature**
- **Data Type:** Signed 16-bit integer
- **Scaling:** Temperature in °C × 100
- **Modbus Sensor Address:** 10 (0x0A)
- **Usage:** PID controller uses this instead of supply temperature for precise room control

**Register 401: Soggiorno Humidity**
- **Data Type:** Unsigned 16-bit integer
- **Scaling:** Humidity in %RH × 10
- **Example:** 65.3% RH → register value 653

**Registers 402-403: Cucina (Kitchen) Temperature/Humidity**
- **Modbus Sensor Address:** 11 (0x0B)
- **Usage:** Same as Soggiorno (temperature control + humidity monitoring)

**Registers 404-405: Bagno (Bathroom) Temperature/Humidity**
- **Modbus Sensor Address:** 12 (0x0C)
- **Usage:** Critical for humidity monitoring (bathroom = highest humidity zone)

**Registers 406-407: Anticamera (Entryway) Temperature/Humidity**
- **Modbus Sensor Address:** 13 (0x0D)
- **Usage:** Buffer zone between indoor and outdoor conditions

### Reserved Register Ranges

| Address Range (Hex) | Address Range (Dec) | Purpose                                   | Notes                                  |
| ------------------- | ------------------- | ----------------------------------------- | -------------------------------------- |
| 0x0065 - 0x00C7     | 101 - 199           | Future temperature sensors                | Reserved for additional Dallas sensors |
| 0x00C9 - 0x012B     | 201 - 299           | Future coordination data                  | Reserved for setpoints, overrides      |
| 0x012D - 0x018F     | 301 - 399           | Master expansion                          | Reserved for future features           |
| 0x0198 - 0x01FF     | 408 - 511           | Future room sensors (first/second floor)  | Addresses 414-427 for expansion        |
| 0x0200 - 0x03FF     | 512 - 1023          | Reserved for slave device status readback | Not yet implemented                    |

## Slave Devices

### Room Temperature/Humidity Sensors (Modbus Addresses 10-13)

**Sensor Model:** XY-MD02 or AM2301-MB Modbus RS485 Temperature/Humidity Sensor  
**Protocol:** Modbus RTU Slave, 9600 baud, 8N1  
**Power:** 12-24V DC  
**Role:** Provide room-level temperature and humidity data for precise zone control

#### Sensor Addresses (Ground Floor)

| Modbus Address | Location   | Zone Name   | Purpose                          |
| -------------- | ---------- | ----------- | -------------------------------- |
| 10 (0x0A)      | Soggiorno  | Living Room | Primary living space control     |
| 11 (0x0B)      | Cucina     | Kitchen     | High-activity zone with humidity |
| 12 (0x0C)      | Bagno      | Bathroom    | Highest humidity monitoring      |
| 13 (0x0D)      | Anticamera | Entryway    | Buffer zone (indoor/outdoor)     |

#### Sensor Registers (Standard for XY-MD02/AM2301-MB)

Sensors typically expose their data at the following addresses (check sensor manual):

| Register Address | Name        | Type   | Description               | Scaling       |
| ---------------- | ----------- | ------ | ------------------------- | ------------- |
| 0x0001           | temperature | INT16  | Current temperature       | ×100 (0.01°C) |
| 0x0002           | humidity    | UINT16 | Current relative humidity | ×10 (0.1% RH) |

**Master Polling Sequence (Story 1.6):**
1. Master polls sensor address 10 → Read registers 0x0001-0x0002
2. Master polls sensor address 11 → Read registers 0x0001-0x0002
3. Master polls sensor address 12 → Read registers 0x0001-0x0002
4. Master polls sensor address 13 → Read registers 0x0001-0x0002
5. Master writes sensor data to master registers 400-407
6. Slaves read master registers 400-407 for local PID control
7. Repeat every 30 seconds

### Ground Floor Slave: distribuzione-piano-terra (Modbus Address 0x02)

**Board:** KC868-A16  
**Role:** Modbus Slave  
**RS485:** TX=GPIO13, RX=GPIO16, 9600 baud, 8N1

#### Holding Registers (Read by Master)

| Address (Hex) | Address (Dec) | Name                              | Type   | Description                       | Units | Scaling | Update Rate | Access |
| ------------- | ------------- | --------------------------------- | ------ | --------------------------------- | ----- | ------- | ----------- | ------ |
| 0x0001        | 1             | test_register                     | UINT16 | Test register for communication   | -     | Direct  | On-demand   | R/W    |
| 0x0400        | 1024          | slave_heartbeat                   | UINT16 | Slave liveness counter (reserved) | count | -       | 10s         | Read   |
| 0x0401-0x04FF | 1025-1279     | Reserved for zone status (future) | -      | -                                 | -     | -       |

*Note: Detailed slave register map will be defined in Story 1.3 (Slave Data Reading)*

## Example Modbus Commands

### Reading Master Registers from Slave

**Read Ground Floor Temperature (Register 100):**
```
Function Code: 0x03 (Read Holding Registers)
Slave Address: 0x01 (Master)
Starting Address: 0x0064 (100 decimal)
Quantity: 1 register (2 bytes)

Request (RTU): 01 03 00 64 00 01 [CRC]
Response: 01 03 02 09 29 [CRC]
  → 0x0929 = 2345 decimal = 23.45°C
```

**Read Climate Mode (Register 200):**
```
Function Code: 0x03 (Read Holding Registers)
Slave Address: 0x01 (Master)
Starting Address: 0x00C8 (200 decimal)
Quantity: 1 register

Request (RTU): 01 03 00 C8 00 01 [CRC]
Response: 01 03 02 00 01 [CRC]
  → 0x0001 = 1 = Heating mode
```

**Read Master Heartbeat (Register 300):**
```
Function Code: 0x03 (Read Holding Registers)
Slave Address: 0x01 (Master)
Starting Address: 0x012C (300 decimal)
Quantity: 1 register

Request (RTU): 01 03 01 2C 00 01 [CRC]
Response: 01 03 02 00 7B [CRC]
  → 0x007B = 123 decimal (heartbeat count)
```

### Reading All Master Coordination Data (Burst Read)

**Read Registers 100-300 in one transaction:**
```
Function Code: 0x03 (Read Holding Registers)
Slave Address: 0x01 (Master)
Starting Address: 0x0064 (100 decimal)
Quantity: 3 registers (temperature, mode, heartbeat)

Request (RTU): 01 03 00 64 00 03 [CRC]
Response: 01 03 06 09 29 00 01 00 7B [CRC]
  → Reg 100: 0x0929 = 2345 = 23.45°C
  → Reg 200: 0x0001 = 1 = Heating
  → Reg 300: 0x007B = 123 = Heartbeat
```

*Note: Burst reads may not work correctly depending on register spacing; test individually first.*

## Error Handling

### Modbus Exception Codes

| Code | Name                  | Description                                      |
| ---- | --------------------- | ------------------------------------------------ |
| 0x01 | Illegal Function      | Unsupported function code                        |
| 0x02 | Illegal Data Address  | Register address not implemented                 |
| 0x03 | Illegal Data Value    | Invalid value for write operation                |
| 0x04 | Slave Device Failure  | Device error (e.g., sensor unavailable)          |
| 0x0B | Gateway Target Failed | Slave not responding (for master querying slave) |

### Testing Invalid Register Reads

**Read Unimplemented Register 500:**
```
Request: 01 03 01 F4 00 01 [CRC]
Expected Response: 01 83 02 [CRC]
  → 0x83 = Function code 0x03 | 0x80 (exception flag)
  → 0x02 = Exception code (Illegal Data Address)
```

## Data Precision and Update Rates

| Data Type    | Source Update Rate  | Modbus Update Rate  | Precision       | Notes                                   |
| ------------ | ------------------- | ------------------- | --------------- | --------------------------------------- |
| Temperature  | 60s (Dallas native) | 10s (register sync) | 0.01°C (×100)   | Faster Modbus updates than sensor polls |
| Climate Mode | On-change (HA)      | 10s (register sync) | Enum (discrete) | Polling ensures slaves see changes      |
| Heartbeat    | N/A                 | 10s (increment)     | 1 count         | Monotonic counter with wraparound       |

## Implementation Notes

### Temperature Scaling Rationale

**Why ×100 scaling?**
- Dallas DS18B20 sensors provide 0.0625°C resolution (12-bit)
- ESPHome reports as float (e.g., 23.45°C)
- Modbus registers are 16-bit integers (no float support)
- Multiply by 100 preserves 0.01°C precision, sufficient for HVAC
- Range: -327.68°C to +327.67°C (adequate for climate control)

**Alternative Considered (×10):**
- 0.1°C precision (e.g., 23.5°C → 235)
- Deemed insufficient; temperature control benefits from 0.01°C precision
- Larger range (-3276.8°C to +3276.7°C) not needed

### Register Address Spacing

Registers are spaced at intervals of 100 decimal (0x64 hex) to allow future expansion within each category:
- **100-199:** Temperature sensors
- **200-299:** Coordination/control data
- **300-399:** Status/diagnostic data

This prevents conflicts when adding new registers in future stories.

### Feature Flag Integration

All register updates respect the `use_modbus` substitution flag:
- When `use_modbus: "false"` → No register updates, saves CPU
- When `use_modbus: "true"` → Registers update every 10 seconds

This allows safe deployment with Modbus infrastructure present but inactive.

## Version History

| Date       | Version | Changes                                         | Author            |
| ---------- | ------- | ----------------------------------------------- | ----------------- |
| 2025-10-16 | 1.0     | Initial register map for master (Story 1.2)     | James (Dev Agent) |
| 2025-10-22 | 1.1     | Added room sensor registers 400-407 (Story 1.6) | James (Dev Agent) |

## References

- Architecture Document: `docs/architecture.md`
- Story 1.1: Modbus Infrastructure Foundation
- Story 1.2: Master Data Exposure (this implementation)
- Story 1.3: Slave Data Reading (future)

---

**Next Steps:** Story 1.3 will define slave-side registers for exposing zone temperatures and valve positions back to the master.
