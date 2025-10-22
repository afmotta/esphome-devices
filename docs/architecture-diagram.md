# ESPHome Climate Control - Architecture Diagrams

**Project:** ESPHome Multi-Floor Climate Control - Modbus RTU Enhancement  
**Version:** 1.0  
**Date:** October 22, 2025

This document provides visual representations of the system architecture, data flows, and key interactions using Mermaid diagrams.

## 1. System Overview - RS485 Bus Topology

```mermaid
graph TB
    subgraph "Master Controller"
        Master[gruppo-miscelazione<br/>KC868-A6<br/>Address: 0x01<br/>GPIO27/14 RS485]
    end
    
    subgraph "Slave Controllers"
        Slave1[distribuzione-piano-terra<br/>KC868-A16<br/>Address: 0x02<br/>GPIO13/16 RS485]
        Slave2[distribuzione-primo-piano<br/>KC868-A16<br/>Address: 0x03<br/>GPIO13/16 RS485]
    end
    
    subgraph "Room Sensors (Ground Floor)"
        Sensor1[Soggiorno Sensor<br/>XY-MD02<br/>Address: 0x0A]
        Sensor2[Cucina Sensor<br/>XY-MD02<br/>Address: 0x0B]
        Sensor3[Bagno Sensor<br/>XY-MD02<br/>Address: 0x0C]
        Sensor4[Anticamera Sensor<br/>XY-MD02<br/>Address: 0x0D]
    end
    
    subgraph "0-10V Devices"
        Modbus0_10V[0-10V Adapter<br/>Address: 0x1E<br/>2nd Floor Fancoil]
    end
    
    Master -->|RS485 Bus<br/>A/B Twisted Pair<br/>9600 baud 8N1| Slave1
    Master -->|RS485 Bus| Slave2
    Master -->|RS485 Bus| Sensor1
    Master -->|RS485 Bus| Sensor2
    Master -->|RS485 Bus| Sensor3
    Master -->|RS485 Bus| Sensor4
    Master -->|RS485 Bus| Modbus0_10V
    
    Term1[120Ω Termination]
    Term2[120Ω Termination]
    
    Master --- Term1
    Modbus0_10V --- Term2
    
    style Master fill:#e1f5e1
    style Slave1 fill:#e3f2fd
    style Slave2 fill:#e3f2fd
    style Sensor1 fill:#fff3e0
    style Sensor2 fill:#fff3e0
    style Sensor3 fill:#fff3e0
    style Sensor4 fill:#fff3e0
    style Modbus0_10V fill:#f3e5f5
    style Term1 fill:#ffebee
    style Term2 fill:#ffebee
```

**Key Points:**
- Daisy-chain topology: Master → Slaves → Sensors → 0-10V devices
- 120Ω termination resistors at BOTH ends (master + last device)
- All devices share common A/B bus (twisted pair, shielded)
- Maximum cable length: ~1200m total (RS485 standard)

---

## 2. Network Topology - All Communication Paths

```mermaid
graph TB
    subgraph "Home Assistant Server"
        HA[Home Assistant<br/>Supervisor + ESPHome Addon]
    end
    
    subgraph "Master Controller - gruppo-miscelazione"
        MasterESP[ESP32 - A6 Board]
        MasterRS485[RS485 UART<br/>GPIO27 TX / GPIO14 RX]
        MasterEth[Ethernet W5500<br/>192.168.1.x]
        MasterI2C[I2C Bus<br/>PCF8574 Expanders]
        Master1Wire[1-Wire Bus<br/>Dallas Sensors]
    end
    
    subgraph "Ground Floor Slave - distribuzione-piano-terra"
        Slave1ESP[ESP32 - A16 Board]
        Slave1RS485[RS485 UART<br/>GPIO13 TX / GPIO16 RX]
        Slave1Eth[Ethernet RJ45<br/>192.168.1.x]
        Slave1I2C[I2C Bus<br/>PCF8574 Expanders]
    end
    
    subgraph "First Floor Slave - distribuzione-primo-piano"
        Slave2ESP[ESP32 - A16 Board]
        Slave2RS485[RS485 UART<br/>GPIO13 TX / GPIO16 RX]
        Slave2Eth[Ethernet RJ45<br/>192.168.1.x]
        Slave2I2C[I2C Bus<br/>PCF8574 Expanders]
    end
    
    HA <-->|ESPHome API<br/>WiFi/Ethernet<br/>Native API| MasterEth
    HA <-->|ESPHome API<br/>Ethernet<br/>Native API| Slave1Eth
    HA <-->|ESPHome API<br/>Ethernet<br/>Native API| Slave2Eth
    
    MasterRS485 <-->|Modbus RTU Master<br/>9600 baud 8N1| Slave1RS485
    MasterRS485 <-->|Modbus RTU Master<br/>9600 baud 8N1| Slave2RS485
    MasterRS485 <-->|Poll Room Sensors<br/>Addresses 10-13| RoomSensors[Ground Floor<br/>Room Sensors]
    
    MasterI2C --> Relays1[6× Relays<br/>Mixing Valves]
    Master1Wire --> DallasSensors[Dallas DS18B20<br/>Supply Temp Sensors]
    
    Slave1I2C --> Relays2[16× Relays<br/>Zone Distribution]
    Slave2I2C --> Relays3[16× Relays<br/>Zone Distribution]
    
    style HA fill:#4caf50,color:#fff
    style MasterESP fill:#e1f5e1
    style Slave1ESP fill:#e3f2fd
    style Slave2ESP fill:#e3f2fd
    style RoomSensors fill:#fff3e0
```

**Communication Paths:**
1. **Home Assistant ↔ All Boards:** ESPHome Native API over Ethernet (sensor data, control commands)
2. **Master → Slaves:** Modbus RTU over RS485 (temperature, mode, heartbeat, room sensors)
3. **Master → Room Sensors:** Modbus RTU polling (room temperature/humidity)
4. **Local I2C/1-Wire:** On-board sensor/relay communication

---

## 3. Data Flow - Temperature Control Loop

```mermaid
sequenceDiagram
    participant RoomSensor as Room Sensor<br/>(Modbus Address 10)
    participant Master as Master<br/>gruppo-miscelazione
    participant Slave as Slave<br/>distribuzione-piano-terra
    participant PID as PID Controller<br/>(Soggiorno Zone)
    participant Relay as Zone Relay<br/>(PCF8574)
    participant HA as Home Assistant

    Note over Master: Every 30 seconds
    Master->>RoomSensor: Poll Temp/Humidity<br/>Read Registers 0x0001-0x0002
    RoomSensor-->>Master: Temperature: 2245 (22.45°C)<br/>Humidity: 653 (65.3% RH)
    Master->>Master: Write to Registers 400-401<br/>(Soggiorno temp/humidity)
    
    Note over Slave: Every 10 seconds
    Slave->>Master: Read Register 400<br/>(Modbus Function 0x03)
    Master-->>Slave: Temperature: 2245 (22.45°C)
    
    Slave->>Slave: Convert to Float<br/>2245 / 100 = 22.45°C
    Slave->>PID: Update Sensor Input<br/>Current Temp: 22.45°C
    
    Note over PID: Setpoint: 23.00°C<br/>Error: +0.55°C
    PID->>PID: Calculate Control Output<br/>kp=0.8, ki=0.005, kd=0.05
    PID->>Relay: Turn ON Zone Relay<br/>(Heat demand)
    
    Relay->>Relay: Energize Relay<br/>(Open mixing valve)
    
    Note over HA: Monitoring
    Slave->>HA: Expose Sensor Data<br/>ESPHome Native API
    HA->>HA: Display in Dashboard<br/>Log History
    
    Note over Master,HA: Failover Available
    alt Room Sensor Offline
        Slave->>HA: Request HA Sensor Fallback<br/>sensor.termometro_soggiorno
        HA-->>Slave: Temperature: 22.50°C
        Slave->>PID: Use HA Temperature
    end
```

**Data Flow Summary:**
1. Master polls room sensors every 30s
2. Master writes sensor data to registers 400-407
3. Slave reads room data from master every 10s
4. Slave converts scaled integers to floats
5. PID controller uses room temperature for control
6. Relay output controls zone heating/cooling
7. Home Assistant monitors all entities

---

## 4. Sensor Failover Decision Tree

```mermaid
graph TD
    Start[PID Controller<br/>Needs Temperature]
    
    Start --> CheckModbus{Local Room Sensor<br/>Available?<br/>Registers 400-407}
    
    CheckModbus -->|Yes - Data Fresh<br/>Age < 30s| UseModbus[Use Room Sensor<br/>Best Accuracy<br/>Direct Room Control]
    CheckModbus -->|No - Timeout| CheckHA{Home Assistant<br/>Sensor Available?<br/>sensor.termometro_*}
    
    CheckHA -->|Yes - HA Online| UseHA[Use HA Sensor<br/>Fallback Mode<br/>Proven Reliability]
    CheckHA -->|No - HA Offline| Emergency[Return NAN<br/>Emergency Shutdown<br/>After 5 Minutes]
    
    UseModbus --> MonitorHealth[Monitor Sensor Health<br/>Log: 'Using Modbus Sensor']
    UseHA --> MonitorHealth
    Emergency --> MonitorHealth
    
    MonitorHealth --> Recovery{Sensor Recovered?}
    Recovery -->|Modbus Back Online| AutoRecover[Automatic Recovery<br/>Switch to Modbus<br/>Log Event]
    Recovery -->|Still Offline| Continue[Continue Current Mode]
    
    style Start fill:#e1f5e1
    style UseModbus fill:#4caf50,color:#fff
    style UseHA fill:#ff9800,color:#fff
    style Emergency fill:#f44336,color:#fff
    style AutoRecover fill:#2196f3,color:#fff
```

**Failover Tiers:**
1. **Primary (Best):** Local Modbus room sensor - Fastest, most accurate
2. **Fallback (Good):** Home Assistant sensor - Proven, reliable
3. **Emergency (Degraded):** NAN → Safe shutdown after 5 minutes

**Recovery:** Automatic transition back to Modbus when sensor recovers

---

## 5. Climate Mode Synchronization

```mermaid
sequenceDiagram
    participant User as User<br/>(HA Dashboard)
    participant HA as Home Assistant
    participant Master as Master Controller
    participant Slave1 as Ground Floor Slave
    participant Slave2 as First Floor Slave
    
    User->>HA: Change Climate Mode<br/>"heat" → "cool"
    HA->>HA: Update text_sensor<br/>thermostat_mode = "cool"
    
    Note over Master: Every 10 seconds
    Master->>HA: Read thermostat_mode<br/>(ESPHome homeassistant platform)
    HA-->>Master: Mode: "cool"
    
    Master->>Master: Convert to Integer<br/>"cool" = 2<br/>Write to Register 200
    
    Note over Slave1,Slave2: Every 10 seconds
    Slave1->>Master: Read Register 200<br/>(Modbus Function 0x03)
    Slave2->>Master: Read Register 200
    
    Master-->>Slave1: Mode: 2 (cool)
    Master-->>Slave2: Mode: 2 (cool)
    
    Slave1->>Slave1: Convert to String<br/>2 = "cool"
    Slave2->>Slave2: Convert to String<br/>2 = "cool"
    
    Slave1->>Slave1: Switch Active PID<br/>Disable Heat PID<br/>Enable Cool PID
    Slave2->>Slave2: Switch Active PID<br/>Disable Heat PID<br/>Enable Cool PID
    
    Slave1->>HA: Update Climate Entities<br/>Mode: cool
    Slave2->>HA: Update Climate Entities<br/>Mode: cool
    
    HA->>User: Display Updated Status<br/>All Zones: Cool Mode
    
    Note over Master,Slave2: Synchronized without HA
    alt Home Assistant Offline
        Master->>Master: Use Last Known Mode<br/>or Local Override
        Slave1->>Master: Continue Reading Register 200
        Slave2->>Master: Continue Reading Register 200
        Note over Master,Slave2: System continues autonomous operation
    end
```

**Synchronization Benefits:**
- All zones switch modes simultaneously
- No per-zone mode configuration needed
- System continues if Home Assistant offline
- Mode persists across slave reboots (read from master)

---

## 6. Room Sensor Integration Architecture

```mermaid
graph TB
    subgraph "Physical Rooms - Ground Floor"
        Room1[Soggiorno<br/>Living Room]
        Room2[Cucina<br/>Kitchen]
        Room3[Bagno<br/>Bathroom]
        Room4[Anticamera<br/>Entryway]
    end
    
    subgraph "Modbus Room Sensors"
        Sens1[XY-MD02<br/>Address 10<br/>Temp: 22.45°C<br/>Humidity: 65.3%]
        Sens2[XY-MD02<br/>Address 11<br/>Temp: 23.10°C<br/>Humidity: 58.2%]
        Sens3[XY-MD02<br/>Address 12<br/>Temp: 24.20°C<br/>Humidity: 72.5%]
        Sens4[XY-MD02<br/>Address 13<br/>Temp: 21.80°C<br/>Humidity: 60.1%]
    end
    
    subgraph "Master Polling & Register Mapping"
        MasterPoll[Master Polls Every 30s]
        Reg400[Register 400<br/>Soggiorno Temp]
        Reg401[Register 401<br/>Soggiorno Humidity]
        Reg402[Register 402<br/>Cucina Temp]
        Reg403[Register 403<br/>Cucina Humidity]
        Reg404[Register 404<br/>Bagno Temp]
        Reg405[Register 405<br/>Bagno Humidity]
        Reg406[Register 406<br/>Anticamera Temp]
        Reg407[Register 407<br/>Anticamera Humidity]
    end
    
    subgraph "Slave PID Controllers"
        PID1[Soggiorno PID<br/>Setpoint: 23°C<br/>Sensor: Reg 400]
        PID2[Cucina PID<br/>Setpoint: 22°C<br/>Sensor: Reg 402]
        PID3[Bagno PID<br/>Setpoint: 24°C<br/>Sensor: Reg 404]
        PID4[Anticamera PID<br/>Setpoint: 20°C<br/>Sensor: Reg 406]
    end
    
    subgraph "Zone Outputs"
        Out1[Zone Relay 1<br/>Floor Heating]
        Out2[Zone Relay 2<br/>Floor Heating]
        Out3[Zone Relay 3<br/>Floor Heating]
        Out4[Zone Relay 4<br/>Floor Heating]
    end
    
    Room1 --> Sens1
    Room2 --> Sens2
    Room3 --> Sens3
    Room4 --> Sens4
    
    Sens1 -->|RS485 Modbus| MasterPoll
    Sens2 -->|RS485 Modbus| MasterPoll
    Sens3 -->|RS485 Modbus| MasterPoll
    Sens4 -->|RS485 Modbus| MasterPoll
    
    MasterPoll --> Reg400
    MasterPoll --> Reg401
    MasterPoll --> Reg402
    MasterPoll --> Reg403
    MasterPoll --> Reg404
    MasterPoll --> Reg405
    MasterPoll --> Reg406
    MasterPoll --> Reg407
    
    Reg400 --> PID1
    Reg402 --> PID2
    Reg404 --> PID3
    Reg406 --> PID4
    
    PID1 --> Out1
    PID2 --> Out2
    PID3 --> Out3
    PID4 --> Out4
    
    Out1 --> Room1
    Out2 --> Room2
    Out3 --> Room3
    Out4 --> Room4
    
    style Room1 fill:#e1f5e1
    style Room2 fill:#e1f5e1
    style Room3 fill:#e1f5e1
    style Room4 fill:#e1f5e1
    style Sens1 fill:#fff3e0
    style Sens2 fill:#fff3e0
    style Sens3 fill:#fff3e0
    style Sens4 fill:#fff3e0
    style MasterPoll fill:#2196f3,color:#fff
    style PID1 fill:#ff9800,color:#fff
    style PID2 fill:#ff9800,color:#fff
    style PID3 fill:#ff9800,color:#fff
    style PID4 fill:#ff9800,color:#fff
```

**Room Sensor Flow:**
1. Physical sensors measure room conditions
2. Master polls sensors via Modbus (30s interval)
3. Master writes sensor data to registers 400-407
4. Slave PID controllers read room temperature from registers
5. PIDs adjust zone outputs to maintain setpoints
6. Closed-loop control: Room → Sensor → Register → PID → Output → Room

---

## 7. Master Heartbeat Monitoring

```mermaid
sequenceDiagram
    participant Master as Master Controller
    participant Reg300 as Register 300<br/>(Heartbeat)
    participant Slave as Slave Controller
    participant Emergency as Emergency<br/>Shutdown Logic
    
    loop Every 10 seconds
        Master->>Master: Increment Counter
        Master->>Reg300: Write Heartbeat Value<br/>(0 → 1 → 2 → ... → 65535 → 0)
    end
    
    loop Every 10 seconds
        Slave->>Reg300: Read Heartbeat Value
        Reg300-->>Slave: Current Value: 123
        
        Slave->>Slave: Compare with Last Value<br/>Last: 122, Current: 123<br/>Delta: +1 ✓
        
        alt Heartbeat Changing
            Slave->>Slave: Master Online<br/>Reset Offline Timer
        else Heartbeat Stuck (Same Value for 30s)
            Slave->>Slave: Master Possibly Offline<br/>Start Timeout Counter
            
            alt Timeout > 5 Minutes
                Slave->>Emergency: Trigger Emergency Shutdown<br/>Log Error Event
                Emergency->>Emergency: Turn Off All Outputs<br/>Wait for Recovery
            else Timeout < 5 Minutes
                Slave->>Slave: Continue Operation<br/>Log Warning
            end
        end
    end
    
    Master->>Reg300: Heartbeat Resumes<br/>Value Changes
    Slave->>Reg300: Detect Change
    Slave->>Slave: Master Recovered!<br/>Auto-Resume Operation<br/>Log Recovery Event
```

**Heartbeat Purpose:**
- Slave detects master failures
- Timeout protection (emergency shutdown after 5 minutes)
- Automatic recovery when master returns
- Prevents stale data from controlling climate

---

## 8. Component Package Composition

```mermaid
graph TD
    Device[Device Configuration<br/>devices/gruppo-miscelazione.yaml]
    
    Board[Board Package<br/>boards/a6.yaml]
    Base[Base Package<br/>boards/base.yaml]
    WiFi[WiFi Package<br/>boards/wifi.yaml]
    
    MixingValve1[Mixing Valve Package<br/>components/mixing_valve.yaml<br/>Circuit: piano_terra]
    MixingValve2[Mixing Valve Package<br/>components/mixing_valve.yaml<br/>Circuit: primo_piano]
    
    DualPID[Dual PID Package<br/>components/dual_pid.yaml]
    PID[PID Package<br/>components/pid.yaml<br/>Mode: heat/cool]
    
    ModbusMaster[Modbus Master Package<br/>components/modbus_master.yaml]
    RoomSensorPoller[Room Sensor Poller<br/>components/modbus_room_sensor_poller.yaml]
    
    Device --> Board
    Board --> Base
    Board --> WiFi
    
    Device --> MixingValve1
    Device --> MixingValve2
    
    MixingValve1 --> DualPID
    MixingValve2 --> DualPID
    
    DualPID --> PID
    DualPID --> PID
    
    Device --> ModbusMaster
    Device --> RoomSensorPoller
    
    style Device fill:#4caf50,color:#fff
    style Board fill:#2196f3,color:#fff
    style MixingValve1 fill:#ff9800,color:#fff
    style MixingValve2 fill:#ff9800,color:#fff
    style ModbusMaster fill:#9c27b0,color:#fff
    style RoomSensorPoller fill:#9c27b0,color:#fff
```

**Package Composition Pattern:**
- Top-level device config includes board + components
- Components are reusable with `vars:` parameterization
- Multi-level composition (mixing_valve → dual_pid → pid)
- Modular architecture enables easy expansion

---

## Diagram Export

These diagrams are written in Mermaid syntax and can be:
1. **Viewed in GitHub:** Mermaid renders automatically in GitHub markdown
2. **Exported as PNG:** Use Mermaid Live Editor (https://mermaid.live) → Export → PNG
3. **Embedded in Documentation:** Copy PNG files to `docs/images/` folder

---

## References

- **Architecture Documentation:** `docs/architecture.md`
- **Modbus Register Map:** `docs/modbus-register-map.md`
- **RS485 Wiring Guide:** `docs/rs485-wiring-guide.md`
- **Deployment Guide:** `docs/deployment-guide.md`

---

**Version History:**

| Date       | Version | Changes                        | Author            |
| ---------- | ------- | ------------------------------ | ----------------- |
| 2025-10-22 | 1.0     | Initial diagrams (Story 1.7)   | James (Dev Agent) |
