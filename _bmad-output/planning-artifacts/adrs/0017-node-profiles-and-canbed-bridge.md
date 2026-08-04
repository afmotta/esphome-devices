---
adr: 0017
title: 'Node deployment profiles, and the segment bridge on the fleet node board'
status: 'Accepted'
date: '2026-08-04'
deciders: ['Alberto']
author: 'Claude'
dependsOn:
  - 'ADR-0005: CAN bus topology — segmented multi-bus with inter-segment coupling (chose software bridges; this ADR changes only the board they run on, and keeps the single-purpose requirement)'
  - 'ADR-0006: Sensor data transport over CAN (the sensor kit that profiles now select)'
  - 'ADR-0007: Flat node_id with central meaning map (bridges carry node_ids like any node)'
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (the one-spare-per-role doctrine this ADR extends to bridges)'
amends:
  - 'ADR-0005: the bridge hardware moves from the LilyGO T-2CAN to the fleet node board (CANBed RP2040 + a second MCP2515). The topology decision, the store-and-forward coupling method, the 125 kbps bit rate, and every mandatory reliability requirement are unchanged — only the board is replaced. ADR-0005 already named "ESP32 + 2x MCP2515" as an accepted DIY form of the same choice.'
relatedDocuments:
  - canbus/_bmad-output/planning-artifacts/adrs/0005-can-bus-topology-segmented-multi-bus.md
  - canbus/_bmad-output/planning-artifacts/adrs/0006-sensor-data-transport-over-can.md
  - registry/nodes.csv
  - canbus/tools/generate_nodes.py
  - canbus/packages/node_core.yaml
  - canbus/packages/bridge.yaml
  - boards/canbed-rp2040-can1.yaml
  - canbus/archive/bridge-t2can.yaml
---

# ADR-0017: Node deployment profiles, and the segment bridge on the fleet node board

## Status

**Accepted** (2026-08-04). Amends ADR-0005's bridge-hardware choice only. Root-tree ADR (spans
`canbus/` composition, the `registry/` schema, and the `climate/`-facing `map.json` export; the
frozen `canbus/_bmad-output/` tree is never edited, per AD-1). Implemented the same day.

**Not hardware-verified.** Every claim below about pins, config validity, and package
composition was checked with `esphome config` against real repo packages; nothing has been
compiled or flashed. The bring-up checks are open items 1-3.

## Context

Two questions arrived together and turn out to have one answer.

**1. What board runs a segment bridge?** ADR-0005 accepted software bridges and landed a first
firmware on the **LilyGO T-2CAN** — an ESP32-S3 whose two CAN ports are one built-in TWAI
controller plus one MCP2515. That board is a one-off in the fleet: exactly one is owned, and it
is the only ESP32-S3 in the house that is neither a controller nor the health monitor.

The alternative ADR-0005 itself named — "ESP32 + 2x MCP2515" — has a cheaper local form. The
**CANBed RP2040** is already the fleet node board, and it breaks out its SPI0 bus on a dedicated
2x3 header (SCK GP2 / MOSI GP3 / MISO GP4 / 3V3 / GND) **plus a spare GP8**. A second MCP2515
therefore costs six wires and no pin conflicts:

| Consumer | Pins |
|---|---|
| Onboard MCP2515 + SPI0 | GP2, GP3, GP4, GP9 (CS), GP11 (INT, unused by ESPHome) |
| 8-button wall set | GP10, GP19, GP20, GP21, GP22, GP23, GP24, GP25 |
| Sensor-kit I2C | GP6, GP7 |
| **Free** | **GP0, GP1, GP8, GP26-29** |

GP8 is the only free pin that sits on the SPI header itself, so it is the natural CS and is
hereby fleet-fixed. (The RP2040's second SPI peripheral is *not* usable here: SPI1 requires
CLK on GP10 and MISO on GP24, both of which are buttons.)

**2. Can one board be a bridge and a sensor node at once?** Evaluated and **rejected** — see
Alternatives. The decision to keep them separate is what makes the composition question
tractable, because "sensors or bridge, never both" is a property the config schema can enforce
structurally rather than by validation.

The existing composition cannot express either answer. `canbus/packages/base_node.yaml`
unconditionally includes the 8-button set, so a bridge in a junction box would instantiate eight
GPIO binary sensors on floating pins and emit phantom presses. And the registry's `sensors`
column is a boolean bolted onto a schema that has no concept of what a node *is*.

## Decision

### 1. The bridge runs on the fleet node board

A segment bridge is a **CANBed RP2040 with a second MCP2515** on the SPI header, CS `GP8`,
16 MHz, 125 kbps. The add-on module must be a 3.3 V one (MCP2515 + SN65HVD230 / MCP2562FD /
TJA1042T,3): the RP2040 is not 5 V tolerant, and a 5 V module's MISO would drive 5 V into GP4.
No reset line is wired — ESPHome's `mcp2515` component issues the SPI RESET instruction in
`setup()`.

This buys what ADR-0014 bought for the controllers: **one spare board type covers nodes and
bridges**, one toolchain, one board file, one USB/UF2 flashing procedure. It also strengthens
two of ADR-0005's mandatory reliability requirements rather than weakening them:

- **"Radios off"** becomes structural. The RP2040 has no radio at all, so it cannot be
  re-enabled by a careless YAML edit. On the T-2CAN it was a comment you had to keep honoring.
- **"Hardware watchdog"** gets a first-class knob: ESPHome's `rp2` platform exposes
  `watchdog_timeout` (default 8388 ms, the RP2040 maximum) plus a crash handler.

One requirement is genuinely weaker: **brownout**. The T-2CAN's firmware pinned
`CONFIG_ESP_BROWNOUT_DET`; the RP2040's brown-out detector is fixed-function and not observable
from ESPHome. Accepted — the failure it guards against still degrades to "silent", which is the
required direction.

### 2. `registry/nodes.csv` gains a single-valued `profile` column

The `sensors` boolean is replaced by `profile`, one value per row:

| `profile` | Packages composed | Deployment |
|---|---|---|
| `buttons` | `buttons_8` | wall plate, no sensing (was `sensors=0`) |
| `buttons+sensors` | `buttons_8` + `sensor_kit` | wall plate with the ADR-0006 kit (was `sensors=1`) |
| `sensors` | `sensor_kit` | sensor puck, no switch plate (newly expressible) |
| `bridge` | `bridge` | segment forwarder, ADR-0005 single-purpose |

**Mutual exclusion is structural, not validated.** A single-valued enum cannot express
"bridge and sensors"; two boolean columns could, and would rely on the generator to reject it.
This is the mechanism by which ADR-0005's single-purpose-firmware requirement stops being a
rule someone has to remember.

The column is named `profile` because ADR-0006 §5 already calls this a *"deployment profile"*.
Adding a future combination (e.g. `bridge+buttons`, the one mixed profile that carries no
blocking I/O) is a new enum value and a new package tuple — no schema change.

### 3. `base_node.yaml` splits into `node_core.yaml` + `buttons_8.yaml`

`node_core.yaml` keeps identity, globals, the board include, and the heartbeat. `buttons_8.yaml`
carries the 8-button set and the `debounce_ms` requirement. Generated nodes compose
`node_core` plus their profile's packages, and nothing else.

Two invariants make `node_core.yaml` completely profile-agnostic — it contains no conditional
of any kind:

- **`can0` is always the controller-facing port.** On a plain node it is the only port; on a
  bridge it is the backbone side, and `can1` is the zone side. So the heartbeat says
  `id(can0).send_data(...)` unconditionally and is correct everywhere. This is also forced
  rather than chosen: an MCP2515 does not receive its own transmissions, so a heartbeat sent on
  the zone side would never be picked up by its own bridge's forwarding handler.
- **`error_flags` is the shared contribution point, and `node_core` is its sole transmitter.**
  The bridge has no heartbeat of its own; it ORs `ERR_BRIDGE_QUEUE_OVERFLOW` into
  `id(error_flags)` on its drain tick. The `ERR_*` bits in `canbus_protocol.h` are disjoint, so
  this composes. It also removes, structurally, the duplicate-CAT_STATUS-per-node_id failure
  that a naive merge of the two heartbeat blocks would have produced.

### 4. Bridges are ordinary registry rows

A bridge carries a `node_id` from the same allocation space (ADR-0005 already required it to
heartbeat as a normal node), so it lands in `node_map.h`, in `map.json`, and in the generated
per-node Home Assistant health entities **for free**. The retired T-2CAN firmware had a
hand-written placeholder `node_id: "200"` and none of that observability.

### 5. `map.json`'s frozen contract is preserved by derivation

`nodes[].sensors` is frozen-additive (`spec-map-json-contract`) and keeps being emitted,
derived as `1 if profile has a sensor kit else 0`. `profile` is added alongside as a new
frozen-additive field. Climate consumers require no change.

### 6. The bridge forwarder requests the high-frequency loop

ESPHome's `mcp2515` has no interrupt support and polls from `loop()`, and `Application::loop()`
gates the component phase on `loop_interval_` (16 ms default; ~20 ms in practice once the 10 ms
drain tick is scheduling wake-ups). The MCP2515 has two RX buffers, and a 125 kbps extended
frame occupies the wire for ~1.1 ms — so a ~20 ms poll window can see ~18 frames arrive and keep
two. On the T-2CAN this only exposed the zone side, because the backbone side was TWAI with an
interrupt-driven driver queue; with two MCP2515s it exposes the aggregate side too.

`bridge.yaml` therefore starts a `HighFrequencyLoopRequester` at boot, which drops the poll
period to the SPI transaction cost (tens of microseconds) — comfortably below the minimum frame
arrival interval. A pure forwarder has nothing else to spend CPU on, so the 100 % duty cycle is
free. This uses an ESPHome-internal C++ API, not a YAML option: it is called out here and in the
package comment so an ESPHome upgrade re-checks it.

The drops this guards against would otherwise be **invisible**: they occur at the MCP2515
before `bridge_enqueue()`, so `ERR_BRIDGE_QUEUE_OVERFLOW` never latches; ESPHome's own overrun
detection is compiled out at `logger: level: INFO`; and the protocol carries no sequence
numbers, so a receiver cannot infer a gap.

### 7. The T-2CAN firmware is archived, not deleted

One T-2CAN is owned. Maintaining a second bridge profile for a single board is not worth the
code, so `devices/bridge.yaml` moves to `canbus/archive/bridge-t2can.yaml`, out of the build
and out of the generator, with a header describing how to revive it. Reviving it means adding
one `PROFILES` entry — the table was designed to absorb exactly that.

## Consequences

### Positive
- One spare board type for nodes and bridges; no one-off hardware in the fleet.
- "Bridge and sensors on one board" becomes unrepresentable rather than merely forbidden.
- Bridges inherit node health monitoring, the central map, and the HA entity generation.
- `sensors`-without-buttons becomes expressible — a real deployment the old schema could not describe.
- Every generator branch becomes a `PROFILES` lookup instead of an `if has_sensors` chain.
- Radios-off and the watchdog get stronger; one fewer MCU family in the bridge role.

### Negative / costs
- Brownout protection is weaker than the ESP32's (accepted; failure direction is still "silent").
- Both bridge ports are now polled 2-buffer MCP2515s, where the T-2CAN had one TWAI side. Mitigated by §6, but §6 leans on an ESPHome-internal API.
- The add-on module on flying leads is mechanically the weakest part of a device that lives behind a wall for years. A small carrier PCB would close this, and is not in scope here.
- Neither CAN port is galvanically isolated, so a bridge ties two segments' grounds together.
- `nodes.csv` changes shape; pre-live doctrine means editing the header and the committed CSV in place, with no migration shim.

## Alternatives considered

- **Keep the T-2CAN as the bridge board.** Better integrated (two ports, no flying leads) and
  keeps an interrupt-driven backbone RX path. Rejected on fleet economics: one board, one spare
  line, one more firmware shape, for a role the existing node board can fill.
- **A board that is both a bridge and a sensor node.** Evaluated in detail and rejected. It
  fits on the pins (GP8 is still free with the full 8 buttons and the sensor kit), and the
  config validates — but it escalates a sensor fault's blast radius from "one room degraded"
  to "one segment dark". The specific new failure mode: `sensor_kit.yaml` sets no `i2c:
  timeout:`, and ESPHome's I2C timeout is optional with no default, so a sensor wedging SDA low
  has no firmware-level bound; with a watchdog that reboots the board, a repeatedly-wedging
  sensor becomes a flapping segment. ADR-0005's single-purpose requirement stands.
  (The blocking I2C read itself is a lesser issue than expected: ESPHome's `sen6x` is an async
  chain, leaving one ~5.5 ms blocking measurement fetch per 30 s at the 50 kHz rp2 I2C default.)
- **Two boolean columns (`sensors`, `bridge`) with a cross-check.** Rejected: it makes the
  invalid state representable and pushes the guarantee into validation code.
- **A separate registry file for bridges.** Rejected: `node_id` uniqueness is the one
  load-bearing bus invariant, and splitting the allocation space across two files puts it at
  risk for no gain.

## Open items

1. **Compile and flash.** Nothing here has been compiled. The first bring-up must confirm the
   two-MCP2515 build links and that both controllers enumerate.
2. **Soak-test the forwarder** (inherits ADR-0005 open item 5). Specifically: three sensor
   nodes on one segment, which is the burst profile `sensor_kit.yaml`'s own 25 ms inter-frame
   spacing says is marginal against a polled 2-buffer RX. Confirm the high-frequency loop
   closes it, and that a wedged/hung bridge goes silent rather than babbling.
3. **Verify the 3.3 V add-on module** end to end, including that its 120 Ω termination jumper
   matches the bridge's position on the segment (fitted only at a segment end).
4. **Segment count and bridge count** — still ADR-0005 open item 1. This ADR makes bridges
   cheap to build; it does not decide how many the house needs.
5. **`i2c: timeout:` on `sensor_kit.yaml`.** Out of scope here (it affects sensor nodes, not
   the profile mechanism), but the missing bound found during this evaluation should be closed
   on its own.

## Notes

This ADR does not touch the wire protocol (ADR-0001/0007), the control model (ADR-0003), or the
`map.json` consumer contract. It changes which board a bridge runs on, and how a node's config
is composed from the registry.
