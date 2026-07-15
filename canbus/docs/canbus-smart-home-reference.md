# CAN Bus Smart Home — ESPHome Protocol & Implementation Reference

## Overview

A CAN bus-based wall button system for Alberto's fienile (barn conversion) in Pioltello. The house has 3 floors (ground: 9 rooms, first: 8 rooms, second: 2 rooms) with up to 100+ button boards, each with a standard set of 8 buttons. The system uses ESPHome on RP2040 button nodes and two ESP32-S3 gateway-class devices (lighting controller + health monitor, ADR-0015), communicating over CAN bus at 125 kbps.

## Architecture

### Design principle: dumb nodes, smart gateway

The button boards are walled in and hard to reach after installation. The RP2040 boards have no WiFi, so no OTA updates. Therefore:

- **Nodes are frozen firmware.** They detect button clicks locally and send self-describing CAN frames. They do not know what any button "does."
- **The gateway is updatable.** It bridges CAN bus to Home Assistant via the ESPHome API over Ethernet. It decodes CAN frames and fires HA events.
- **Home Assistant owns all logic.** What happens when a button is pressed is defined entirely in HA automations, which can be changed at any time.

### Hardware

**Button nodes:** Seeed Studio / Longan Labs CANBed RP2040 (SKU 102991596). An off-the-shelf CAN bus development board with RP2040 MCU, on-board MCP2515 CAN controller (SPI0, CS on GPIO9) and MCP2551 CAN transceiver. CAN interface via 4-pin screw terminal or DB9 connector, with switchable 120Ω termination resistor. Accepts 9–28V power input on the CAN connector (provides regulated 3.3V/1A). Exposes 8 digital I/O, 3 analog inputs, I2C (Grove), UART (Grove), and SPI. The standard node firmware wires up 8 buttons. No WiFi, no OTA — flashed via USB (Micro-USB) before installation. ~$16 per board ($14 at 10+). Product link: https://www.seeedstudio.com/CANBed-RP2040-CAN-Bus-development-board-p-5262.html

**Gateway-class devices (two, since the ADR-0015 split):**

- **Lighting controller** (`devices/light-controller.yaml`): LilyGO T-Connect Pro (ESP32-S3-R8, 16MB flash / 8MB PSRAM), per ADR-0014 — the same standardized controller the HVAC master uses (`boards/t-connect-pro.yaml`). Connects to Home Assistant via W5500 Ethernet (no PoE; DC supply — ADR-0014 §5). Uses the ESP32-S3's native TWAI CAN controller (IO6 TX, IO7 RX) with the board's onboard CAN transceiver. RS485 (IO17 TX, IO18 RX, auto-direction transceiver) drives its Waveshare Modbus RTU Relay 32CH bank (address `0x2`, lighting fallback relays). W5500 Ethernet SPI: SCLK=IO12, MOSI=IO11, MISO=IO13, CS=IO10, INT=IO9, RST=IO48. The board's display/touch/LoRa peripherals are unused and left unconfigured.
- **Health monitor** (`devices/health-monitor.yaml`): Waveshare ESP32-S3-RS485-CAN (`boards/waveshare-s3-rs485-can.yaml`), WiFi-only, CAN transceiver on IO15 TX / IO16 RX. Hosts transport health only (heartbeat decode, aliveness, drift diagnostics); no relays, no RS485.

Both tap the same backbone segment. ADR-0015 split what ADR-0014 P4 had deployed as one combined `devices/gateway.yaml` (which itself retired the earlier three-way discrepancy where docs said POE-ETH-8DI-8DO with CAN on GPIO2/3 while the deployed config was a WiFi RS485-CAN board with CAN on GPIO15/16).

## CAN Protocol v1

### CAN ID (29-bit Extended, ADR-0007)

```
Bit: 28 27 26 25 │ 24 .............. 12 │ 11 ............. 0
     C  C  C  C  │ N  N  ........  N    │ r  r  ........  r

C = Category (4 bits, 0-15)   — message class + arbitration priority (lower = higher)
N = Node ID  (13 bits, 0-8191) — flat, meaningless, assigned at flash time
r = Reserved (12 bits)         — future per-category low fields; MUST be 0 for now
```

The CAN ID is intentionally generic. It carries no semantic meaning about rooms or buttons — only a flat node identifier and a category for bus arbitration priority and hardware filtering. A node's identity is its flat `node_id`; (room, board, name) live in a central `node_id → {...}` map compiled into the gateway-class devices (`protocol/node_map.h`, generated from `registry/nodes.csv`) — never on the node. All message content lives in the payload; all frames are sent with `use_extended_id: true`.

**Categories** (lower value = higher CAN bus priority):

| Value | Name         | Direction         | Purpose                                        |
|-------|--------------|-------------------|------------------------------------------------|
| 0     | CAT_SYSTEM   | bidirectional     | Emergency, errors, controller liveness         |
| 1     | CAT_INPUT    | node → gateway    | Button events                                  |
| 2     | CAT_OUTPUT   | gateway → node    | Commands / config (defined; not yet wired)     |
| 3     | CAT_STATUS   | node → gateway    | Heartbeat, health                              |
| 4     | CAT_SENSOR   | node → controller | Environmental measurements (ADR-0006)          |
| 5–14  | *(reserved)* | —                 | Future classes (e.g. CONFIG, DISCOVERY)        |
| 15    | CAT_EXTENDED | —                 | Escape: real class is a subtype in the payload |

Consumers use CAN mask filtering on the category bits (`can_id_mask: 0x1E000000` = `CAN_MASK_CATEGORY`) to match all messages of a given category regardless of node ID; `CAN_MASK_ADDR` additionally matches the node_id field (a node's RX filter for OUTPUT frames addressed to it).

### Data payloads (variable length, ≤ 8 bytes)

Frames are variable-length; receivers guard against the per-message minimum (`BUTTON_PAYLOAD_MIN`, `HEARTBEAT_PAYLOAD_MIN`, `SENSOR_PAYLOAD_MIN`), never a fixed 8.

**Button event** (CAT_INPUT, 4 bytes):

```
Byte 0: Protocol version (0x01)
Byte 1: Message type (0x01 = MSG_BUTTON_EVENT)
Byte 2: Button index (0–7)
Byte 3: Event type
         0x01 = click
         0x02 = double_click
         0x03 = triple_click
         0x06 = hold          (fires while the button is still down, at hold_ms)
         0x07 = hold_release  (fires when that hold ends)
```

`0x04`/`0x05` were long/extra-long press, removed pre-live (ADR-0012 §2: a "long press" is derived centrally from the hold → hold_release pair). They are left unassigned so a frame from a not-yet-reflashed node decodes as "unknown" (logged, never forwarded).

**Heartbeat** (CAT_STATUS, 5 bytes, sent every 30 seconds):

```
Byte 0:   Protocol version (0x01)
Byte 1:   Message type (0x01 = MSG_HEARTBEAT)
Byte 2:   Error flags (0x00 = healthy, 0x01 = CAN TX fail,
          0x02 = bus off, 0x04 = bridge queue overflow — segment bridge only)
Byte 3–4: Uptime in hours (uint16 LE; 0xFFFF = "at least 65535 h")
```

Heartbeats carry no button state — momentary buttons have no state (hard rule); buttons emit events only.

**Sensor measurement** (CAT_SENSOR, 8 bytes, ADR-0006):

```
Byte 0:   Protocol version (0x01)
Byte 1:   Status (0 = OK/publish; 1 warming up, 2 unavailable, 3 error,
          4 out of range — all "ignore value")
Byte 2–3: Measurement type (uint16 LE — SHT45 temp/RH, SEN66 temp/RH/PM/VOC/NOx/CO2)
Byte 4–7: Value (32-bit LE; int32 for temperatures, uint32 otherwise,
          scaling implied by the measurement type)
```

### Identity: node_id in the CAN ID, semantics in the central map

ESPHome's `on_frame` trigger exposes the received CAN ID as the `can_id` lambda variable, so consumers decode the sender with `can_id_node(can_id)` even when mask-filtering a whole category. Room/board/name are resolved at the gateway from the compiled `node_map.h` (generated from `registry/nodes.csv`); an unknown node resolves to `255`/`"unknown"`. Frames therefore stay minimal, and renaming a room is a registry edit plus gateway reflash — never a node reflash.

## Project file structure

```
registry/                    # house system-of-record, elevated out of firmware/ (migration Phase 1)
├── nodes.csv                # Node registry: node_id, floor, room, board, location
├── node_id_hwm               # persistent monotonic node_id high-water mark
├── bindings.yaml             # binding manifest (owned by lighting)
└── map.json                  # GENERATED read-only export (contract owned by hvac)
canbus/                       # flattened out of firmware/ (Phase 6a); the gateway-class configs
                              #   (light-controller.yaml, health-monitor.yaml) + bridge.yaml
                              #   live in devices/ (Phase 5a; split by ADR-0015)
├── README.md                 # Operational detail: pins, arbitration, health, manifest
├── protocol/
│   ├── canbus_protocol.h    # C++ header: all constants, CAN ID helpers, payload builders/decoders
│   └── node_map.h           # GENERATED central node_id -> {room, board, name} map (gateway include)
├── packages/                # node-side (base_node, button, sensor_kit) + gateway-side (health.yaml,
│   │                        #   canbus's half of the Phase 5b-2 gateway split)
│   ├── base_node.yaml       # Shared CAN node behavior: protocol include, heartbeat, standard 8-button set
│   ├── button.yaml          # Per-button package: GPIO + on_multi_click with 5 event types
│   ├── sensor_kit.yaml      # Opt-in ADR-0006 sensor kit (SHT45 + SEN66)
│   └── health.yaml          # Health-monitor-side: transport health, !extends can0 (see devices/health-monitor.yaml)
├── tools/
│   ├── allocate_node.py     # allocate the next node_id and register it
│   ├── generate_nodes.py    # reads registry/nodes.csv -> per-node YAML + protocol/node_map.h,
│   │                        #   protocol/bindings.h, climate routing artifacts, map.json
│   ├── commission.py        # assign room/board to a node_id, regenerate node_map.h
│   ├── bindings.py          # strict bindings.yaml reader + canonical manifest hash
│   └── check_registry_pushed.py # ADR-0009 push-discipline gate (run before gateway reflash)
├── tests/
│   ├── test_protocol.cpp    # native round-trip test for canbus_protocol.h
│   ├── test_ha_arbitration.cpp / test_node_health.cpp / test_bridge_forwarding.cpp
│   │                        # native tests for the pure-logic headers
│   ├── test_bindings_contract.cpp # drift test for the frozen bindings.h consumer contract
│   ├── test_bindings.py / test_generate_exports.py / test_push_gate.py # Python (stdlib-only)
│   └── compile_sensor_node.yaml   # ESPHome compile check without touching generated nodes
└── nodes/                   # Generated node YAML files (one per board)
    ├── node100.yaml
    ├── node101.yaml
    └── ...
```

Each generated node file is minimal: it declares the concrete device identity, the `node_id`
and `debounce_ms` substitutions, then composes `packages/base_node.yaml`. `base_node.yaml`
pulls in `boards/canbed-rp2040.yaml`, so board hardware (`rp2040`, logger, SPI, MCP2515
`can0`) stays behind the base-node abstraction while CAN node behavior (protocol include,
boot logging, standard buttons, heartbeat) lives beside it. So all nodes are identical apart
from their `node_id` (the node's only identity) and optional sensor-kit package.

### Why the C++ header exists

ESPHome `!lambda` blocks are inline C++. Without the header, every lambda would contain raw bit shifts and magic numbers (e.g. `return {0x01, 0x01, ${button_index}, 0x01};`). The header provides named constants (`EVT_CLICK`, `CAT_INPUT`) and helper functions (`can_id()`, `button_payload()`) so that lambdas are one-liners. It also provides decoder functions (`can_id_node()`, `payload_event_type()`, `event_type_str()`) used by the gateway-class devices. Both nodes and gateways include the same header, so the protocol definition cannot drift.

### Per-button package pattern

Every node carries the same standard set of **8 buttons** (`btn0`–`btn7`). These are
declared once in `packages/base_node.yaml`, so individual node files do not configure
buttons at all — they include the base node package:

```yaml
# packages/base_node.yaml
packages:
  btn0: !include { file: button.yaml, vars: { button_index: "0", button_gpio: "24" } }
  btn1: !include { file: button.yaml, vars: { button_index: "1", button_gpio: "23" } }
  btn2: !include { file: button.yaml, vars: { button_index: "2", button_gpio: "22" } }
  btn3: !include { file: button.yaml, vars: { button_index: "3", button_gpio: "21" } }
  btn4: !include { file: button.yaml, vars: { button_index: "4", button_gpio: "25" } }
  btn5: !include { file: button.yaml, vars: { button_index: "5", button_gpio: "20" } }
  btn6: !include { file: button.yaml, vars: { button_index: "6", button_gpio: "19" } }
  btn7: !include { file: button.yaml, vars: { button_index: "7", button_gpio: "10" } }
```

The `button.yaml` template creates a `binary_sensor` with `on_multi_click` handling the ADR-0012 gesture vocabulary: click / double_click / triple_click (release-time) plus hold / hold_release (press-phase — hold fires *while the button is still down*, once the press reaches `hold_ms`, default 800 ms; hold_release fires when that hold ends). Click detection runs locally on the node (not on the gateway) because multi-click timing requires consistent millisecond-level precision that would be affected by CAN bus latency. The timing thresholds are compile-time constants in ESPHome's `on_multi_click` and cannot be changed at runtime.

Click patterns are ordered longest-first (triple → double → single) so the longest sequence matches before shorter ones; the hold pair coexists because it is timing-disjoint from clicks (ON ≤ 0.5 s vs ≥ hold_ms — the gap is deliberate gesture separation). long_press is not emitted by nodes; it is derived centrally from the hold → hold_release pair (ADR-0012 §2).

### CANBed RP2040 SPI pin mapping

The MCP2515 CAN controller on the CANBed RP2040 is connected via SPI0. These pins are fixed by the board design and are declared once in `boards/canbed-rp2040.yaml` (not passed as per-node substitutions):

| Function | GPIO | Source |
|----------|------|--------|
| SPI CS   | GPIO9  | Confirmed — CANBed RP2040 V1.1 Eagle schematic (`CANCS`) |
| SPI SCK  | GPIO2  | Confirmed — CANBed RP2040 V1.1 Eagle schematic (`SCK`) |
| SPI MOSI | GPIO3  | Confirmed — CANBed RP2040 V1.1 Eagle schematic (`MOSI`) |
| SPI MISO | GPIO4  | Confirmed — CANBed RP2040 V1.1 Eagle schematic (`MISO`) |
| INT      | GPIO11 | Confirmed — schematic `INT` net. Not configured: the ESPHome `mcp2515` component polls over SPI and exposes no INT-pin option |
| Clock    | 16MHZ  | Confirmed — schematic crystal `X1` value |

The board exposes 8 digital I/O and 4 analog inputs (usable as digital) on the main 9x2 header, plus Grove connectors for I2C (Wire1) and UART (Serial1). The exact GPIO numbers for button-usable pins need to be confirmed from the pinout diagram (https://www.longan-labs.cc/media/wysiwyg/CAN-Bus/CANBed/Details_of_CANBed-04.png).

Note: the board ships as a kit with unsoldered through-hole components (terminal blocks, DB9 connector, pin headers, 120Ω termination switch). These must be soldered before use.

### Node config generation

`tools/generate_nodes.py` reads `registry/nodes.csv` and produces one minimal YAML file per
node. Because `packages/base_node.yaml` pulls in `boards/canbed-rp2040.yaml` and shared node
behavior lives in the same base package, each generated node file only needs its identity,
substitutions, and package composition:

```yaml
substitutions:
  node_id: "100"
  debounce_ms: "50"

esphome:
  name: node_100
  friendly_name: "Node 100"

packages:
  base: !include ../packages/base_node.yaml
```

To add a node, add a row to `registry/nodes.csv` and re-run `tools/generate_nodes.py`. `node_id` is the
node's only flashed identity (a flat value carried in the 29-bit Extended CAN ID per
ADR-0007); room/board/location live in a central `node_id → {...}` map on the controller/HA,
not on the node. Node files in `nodes/` are generated output — do not hand-edit them; put
board hardware in `boards/canbed-rp2040.yaml` via `base_node.yaml`, and shared node behavior
in `base_node.yaml` itself.

## Gateway → Home Assistant integration

Since the ADR-0015 split the HA surface is split by device: the **lighting controller** fires button events and hosts the ha_ready arbitration services (`lighting/packages/buttons.yaml`); the **health monitor** fires transport-health events (`canbus/packages/health.yaml`).

### Events fired

**`esphome.canbus_button`** (lighting controller) — on every recognized button event:
```yaml
event_data:
  node_id: "101"   # string — the identity; everything below is resolved from node_map.h
  room: "7"        # string
  board: "2"       # string
  name: "soggiorno-south"  # string ("unknown" for unmapped nodes)
  button: "3"      # string (0-7)
  event: "click"   # click | double_click | triple_click | hold | hold_release
  event_id: "42"   # string — ACK correlation id (ADR-0003 arbitration)
```
Unknown event types are logged, never fired. Events are only forwarded while `ha_ready` holds (heartbeat fresh + manifest hash match); otherwise the local fallback path runs instead (ADR-0013: click-only actuation against the relay bank).

**Health-monitor events** (ADR-0011): `esphome.canbus_node_lost` / `canbus_node_recovered` (node_id, name), `canbus_node_error` (node_id, name, error_flags as hex bitmask), and `canbus_node_unknown` (node_id — a live, uncommissioned node heartbeating; press its button to identify, then commission it). Heartbeats themselves are not forwarded as events — fleet state is exposed as entities (Nodes Online / Nodes Total / Nodes Missing) that survive HA reconnects.

### HA services exposed (lighting controller, ADR-0003 arbitration)

**`ha_readiness_heartbeat`** — HA calls this every few seconds with its `manifest_hash` (string); a mismatch with the compiled `BINDINGS_MANIFEST_HASH` disables HA authority.

**`ha_ack_event`** — HA's generated automation ACKs each forwarded button event by `event_id` (int); an ACK not arriving within `ack_timeout_ms` triggers the local fallback for that event.

OUTPUT-command services (controller → node commands/config over CAT_OUTPUT) are defined in the protocol header but not yet wired; they land with the commissioning slice (CAN-Epic 5 track).

### Example HA automation

```yaml
automation:
  - alias: "Kitchen light toggle"
    trigger:
      - platform: event
        event_type: esphome.canbus_button
        event_data:
          node_id: "102"
          button: "0"
          event: "click"
    action:
      - service: light.toggle
        target:
          entity_id: light.kitchen_main
```

Hold-gesture reference automations (hold-to-dim, hold-to-move covers, derived long press) live in `lighting/home-assistant/ha_hold_automations.yaml`; the arbitration heartbeat/ACK automations in `canbus/home-assistant/ha_arbitration_automations.yaml` plus the generated `ha_manifest_package.yaml`.

## Known limitations and future work

- **No OTA for nodes.** RP2040 boards without WiFi must be flashed via USB. ADR-0008 §4 considered and deliberately rejected a CAN bootloader (no category is allocated to it); the reflash story is the USB campaign runbook (`reflash-campaign-runbook.md`, still a bench-timing stub).
- **Click/hold timing is compile-time.** ESPHome's `on_multi_click` timing values (including `hold_ms`) are baked into firmware. `MSG_CONFIG_WRITE`/`MSG_CONFIG_ACK` are defined in the protocol header but the CAT_OUTPUT path is not wired, so thresholds cannot yet be changed at runtime.
- **No node actuation over CAN.** The transport currently carries button events, heartbeats, and sensor frames inbound only; all actuation is the lighting controller's local Modbus relay bank. Wiring CAT_OUTPUT (plus command retry/fault surfacing, Epic 5) is the planned next transport slice.
- **Single backbone consumer pair.** The lighting controller and health monitor tap one backbone segment (a store-and-forward bridge exists for a second segment, ADR-0005). For very long bus runs, per-floor gateways could use the category mask filtering to partition traffic.
- **Node health surfacing is aggregate-only.** The health monitor exposes fleet aggregates and fires per-node edge events (lost/recovered/error/unknown), but the generated per-node HA status entities, alerting automations, and "degraded last night" report are still deferred (ADR-0011 open item 2).
