# Hardware & Address Table

This page is the single consolidated reference for what hardware exists in this
house's three systems (CAN bus, lighting, climate), what each device's job is, and
every Modbus address and relay/channel assignment currently in use. If you only need
one page bookmarked while working on the physical installation, this is probably it.

!!! note "How to read the confidence tags on this page"
    🟢 **VERIFIED** — confirmed on a bench or in the field.
    🔵 **DESIGNED** — built and intended to work this way, not yet proven against a
    real installation (true for almost everything below — the house is not yet
    physically wired up).
    ⚠️ **KNOWN GAP** — genuinely unresolved.

## Hardware families, in plain language

The house standardized on a small family of interchangeable devices on purpose
(see [Document Map](doc-map.md) for where that decision — ADR-0014 — is recorded), so
that one shelf of spare boards can cover a failure in almost any part of the house.
🔵 DESIGNED

| Board model | Role | Used by | Spares story |
|---|---|---|---|
| **LilyGO T-Connect Pro** (ESP32-S3, W5500 Ethernet, native RS485 + CAN) | Controller | Climate controller (`devices/climate-control.yaml`) **and** lighting controller (`devices/light-controller.yaml`) — two separate physical boards, same model | One spare board type covers a dead controller on *either* system — reflash it with the right entry point and it becomes whichever controller failed. |
| **Waveshare ESP32-S3-RS485-CAN** (WiFi only, isolated CAN + RS485) | CAN bus health monitor | Only the dedicated health-monitor device (`devices/health-monitor.yaml`) | Single-purpose, WiFi-only board dedicated to watching bus health — see [Document Map](doc-map.md) for why this device was split out on its own (ADR-0015). |
| **Waveshare Modbus RTU Relay 32CH** | 32-channel relay bank | Climate (zone/pump switching) **and** lighting (light circuits) — one board per system, both at address `0x2` | A single spare relay board is a drop-in replacement for *either* system's relay bank — same model, same address, no re-addressing needed. |
| **Waveshare Modbus RTU Analog Output 8CH (B)** | 0–10V analog outputs | Climate only (fancoil fan speed, mixing-valve modulation) | Climate-only device; no lighting-side twin to share spares with. Confirm you have the **(B)** voltage variant, not the plain model, which outputs 0–20mA current instead — these are not interchangeable. |
| **S1 Pro Multi-Sense** | Room sensor board (temperature, humidity, air quality, LD2450 presence radar) | Climate (room sensing) | Custom board; see [Room Sensor Board](../hardware/room-sensor.md) for what's known about replacing one — currently ⚠️ **KNOWN GAP**, no documented replacement procedure exists yet. |
| **CANBed RP2040** | CAN bus node (behind wall buttons / built into sensor boards) | CAN bus / lighting (button decode) | Frozen firmware, no WiFi/OTA; identity lives in `registry/nodes.csv`, not on the board itself, so a spare board becomes any node once flashed with that node's config. |

## Modbus bus members and addresses

There are **two separate RS485 buses in the house**, not one shared bus: the climate
controller has its own, and the lighting controller has its own. They happen to use
the same relay-board address by design (see the note below).

### Climate bus (`rs485_bus`, target 38400 8E1)

| Device | Modbus address | Channels | Notes |
|---|---|---|---|
| T-Connect Pro (climate controller) | — (bus master) | — | The sole Modbus master on this bus; no other device may write to the bus. |
| Analog Outputs Board 8CH (B) | `0x1` | `analog_output_1`–`analog_output_8` | 0–10V outputs, holding registers `0x0000`–`0x0007`. |
| Relay Board 32CH | `0x2` | `relay_1`–`relay_32` | Coils `0x0000`–`0x001F`. |
| MEV (Cappellotto Air Fresh I, ventilation unit) | `0x10` | — | Its own device-specific register set; see `climate/mev_modbus.yaml` in the repo, not reproduced here. |

Room temperature/humidity/air-quality data does **not** travel over this bus at all —
it arrives over the CAN bus, with a Home Assistant fallback. See the
[Glossary](glossary.md) entry on failover tiers if that's unfamiliar.

### Lighting bus (separate physical bus, same target 38400 8E1)

| Device | Modbus address | Channels | Notes |
|---|---|---|---|
| T-Connect Pro (lighting controller) | — (bus master) | — | Its own separate bus; not electrically connected to the climate bus. |
| Relay Board 32CH | `0x2` | `relay_0`–`relay_31` (0-based on this bus) | Lighting circuit switching. |

!!! note "Why `0x2` appears on both buses"
    ADR-0014 §4 deliberately mirrors the relay board's address (`0x2`) across both the
    climate and lighting buses, so a single spare Relay 32CH board can be dropped into
    *either* system without reconfiguring its address first. The analog output board
    (`0x1`) and the MEV unit (`0x10`) are climate-only addresses — there is no
    lighting-side device at those addresses to mirror against, so a spare for those two
    only ever goes back into the climate system. 🔵 DESIGNED

Bus parameters (38400 baud, 8 data bits, even parity, 1 stop bit — "38400 8E1") are
the **target** configuration on both buses, pending a bring-up check that every
physical device can actually run at that setting — the ventilation unit (MEV) is the
least flexible member and is the binding constraint if it can't. ⚠️ **KNOWN GAP** until
that check happens on real hardware (ADR-0014 §4, open item 1).

## Relay assignment table (climate bus, address `0x2`)

This is the live channel mapping for the climate system's 32-channel relay board.
Source of truth in the repository is `devices/climate-control.yaml` and the room/floor
files under `climate/rooms/**` — if you change an assignment there, update this table
to match, or the two will drift.

| Relay | Zone / circuit | Component |
|---|---|---|
| `relay_1` | Ground floor radiant | Mixing pump |
| `relay_2` | Ground floor fancoil | Direct pump |
| `relay_3` | First floor radiant | Mixing pump |
| `relay_4` | Second floor fancoil | Direct pump |
| `relay_5` | — | Unallocated |
| `relay_6` | Anticamera | Radiant |
| `relay_7` | Bagno (ground floor) | Radiant |
| `relay_8` | Cucina | Radiant |
| `relay_9` | Soggiorno | Radiant |
| `relay_10` | Bagno Grande | Radiant |
| `relay_11` | Bagno Ospiti | Radiant |
| `relay_12` | Bagno Padronale | Radiant |
| `relay_13` | Camera Nord | Radiant |
| `relay_14` | Camera Ospiti | Radiant |
| `relay_15` | Camera Padronale | Radiant |
| `relay_16` | Camera Sud | Radiant |
| `relay_17` | Lavanderia | Radiant |
| `relay_18`–`relay_21` | — | Reserved (freed by a past MEV migration; nothing currently uses these) |
| `relay_22`–`relay_32` | — | Unallocated spare capacity |

Fancoil units have no relay channel of their own. Each floor's fancoil circulation
runs off that floor's shared pump relay (`relay_2` or `relay_4` above); the fancoil's
fan speed itself is controlled separately, over the analog output board (next table).

If you're [adding a new room](../maintenance-tasks.md#adding-or-moving-a-climate-room),
pick an unallocated channel from `relay_22`–`relay_32` (or `relay_5`) and update this
table in the same change.

## Analog output channel assignments (climate bus, address `0x1`)

| Channel | Assignment |
|---|---|
| `analog_output_1` | Ground floor radiant mixing valve |
| `analog_output_2` | First floor radiant mixing valve |
| `analog_output_3` | Soggiorno fancoil |
| `analog_output_4` | Cucina fancoil |
| `analog_output_5` | Locale Tecnico fancoil |
| `analog_output_6` | Sottotetto fancoil |
| `analog_output_7` | First floor MEV fan speed |
| `analog_output_8` | Unallocated |

## Related

- [Which device died?](../hardware/index.md) — start there for hardware
  troubleshooting, this page is the address/assignment reference it points back to.
- [Routine Maintenance](../maintenance-tasks.md) — adding a room or a Modbus device
  walks through picking a free relay/channel from the tables above.
- [Document Map](doc-map.md) — where the underlying hardware decisions (ADR-0014,
  ADR-0015) are recorded in full.
