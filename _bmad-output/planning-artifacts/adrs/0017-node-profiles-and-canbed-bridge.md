---
adr: 0017
title: 'Node deployment profiles, and the two segment bridge boards'
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
  - 'ADR-0005: the bridge may run on either the LilyGO T-2CAN (preferred) or the fleet node board (CANBed RP2040 + a second MCP2515). The topology decision, the store-and-forward coupling method, the 125 kbps bit rate, and every mandatory reliability requirement are unchanged — only the board set is widened. ADR-0005 already named both "LilyGO T-2CAN" and "ESP32 + 2x MCP2515" as accepted forms of the same choice.'
relatedDocuments:
  - canbus/_bmad-output/planning-artifacts/adrs/0005-can-bus-topology-segmented-multi-bus.md
  - canbus/_bmad-output/planning-artifacts/adrs/0006-sensor-data-transport-over-can.md
  - registry/nodes.csv
  - canbus/tools/generate_nodes.py
  - canbus/packages/node_core.yaml
  - canbus/packages/bridge.yaml
  - boards/canbed-rp2040-can1.yaml
  - boards/lilygo-t-2can.yaml
---

# ADR-0017: Node deployment profiles, and the two segment bridge boards

## Status

**Accepted** (2026-08-04). Amends ADR-0005's bridge-hardware choice only. Root-tree ADR (spans
`canbus/` composition, the `registry/` schema, and the `climate/`-facing `map.json` export; the
frozen `canbus/_bmad-output/` tree is never edited, per AD-1). Implemented the same day.

**Amended the same day** (2026-08-04) to add the `buttons+bridge` profile: the segment plan
turned out to split at some button boxes, where a dedicated forwarder would mean two boards in
one back-box. §2 and §7 below carry the reasoning; it is a bounded relaxation of ADR-0005's
single-purpose rule for buttons only, and the sensor-kit exclusion is unchanged.

**Amended again** (2026-08-04, same day) after surveying what 3.3 V MCP2515 modules are
actually purchasable: the **T-2CAN is restored as the preferred bridge board**, and the
CANBed + add-on path is kept as a viable second source. §1 and §7 carry the reasoning. This
reverses the *hardware preference* only; the profile mechanism, both invariants, and the
registry integration are unchanged — the T-2CAN came back as one more `PROFILES` row, which
is the mechanism working as intended.

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

### 1. Two bridge boards, with the LilyGO T-2CAN preferred

| Board | Profile | Ports |
|---|---|---|
| **LilyGO T-2CAN** (preferred) | `bridge-t2can` | `can0` = built-in TWAI (backbone), `can1` = onboard MCP2515 (zone) |
| **CANBed RP2040 + add-on MCP2515** | `bridge`, `buttons+bridge` | both ports MCP2515; add-on CS `GP8`, 3.3 V module required |

**This reverses the original decision, which was CANBed-only.** The reversal is worth
recording in full, because the original argument was reasonable and still failed.

**The original case.** Putting bridges on the fleet node board buys what ADR-0014 bought for
the controllers: one spare board type covers nodes and bridges, one toolchain, one board file,
one USB/UF2 flashing procedure. It also strengthens two ADR-0005 requirements — "radios off"
becomes structural (the RP2040 has no radio at all, so it cannot be re-enabled by a careless
YAML edit) and the `rp2` platform exposes a first-class `watchdog_timeout`.

**What broke it: the add-on module is not a commodity.** It must satisfy three independent
conditions — raw SPI (no MCU in front of the MCP2515), a 3.3 V transceiver (the RP2040 is not
5 V tolerant, and a 5 V part's RXD would drive 5 V into GP4), and a crystal ESPHome supports
(8/12/16/20 MHz only). A survey of what is actually purchasable:

| Candidate | Fails on |
|---|---|
| MikroE CAN SPI Click 3.3V | **10 MHz crystal** — electrically ideal, unsupported by ESPHome |
| Adafruit CAN Bus BFF (MCP25625) | needs **VDDA 4.5–5.5 V**; the CANBed exposes only 3V3 and raw VIN (verified against the V1.1 schematic — J1 and J4 both end in 3V3) |
| Longan 1030001 / 1030017 | MCP2515 sits **behind an ATmega168PA** (UART / I2C AT-command interface) — unreachable by an SPI driver |
| Longan 1030016 | raw SPI, but **5 V MCP2551** in an Arduino UNO shield footprint |
| **Seeed 105100001** | **passes** — MCP2515 + SN65HVD230, 8 MHz, unfitted 120 Ω pad |

Exactly one clean fit, and it is a XIAO/QT Py carrier that mounts by soldering to socket pads.

**So the economics inverted.** The Seeed module is ~$10 on top of a CANBed; a whole T-2CAN is
~$30. The saving is nominal, and it buys a *worse* physical result: two boards and flying
leads in a back-box instead of one integrated board with two terminals.

**And the T-2CAN is technically better on the axis that matters most here.** Its backbone side
is the ESP32-S3's built-in TWAI controller — interrupt-driven with a deep driver queue —
where the CANBed must poll a 2-buffer MCP2515 on *both* sides. That is precisely the weakness
§6 exists to work around, and the T-2CAN simply does not have it on the aggregate-traffic side.

**Costs accepted in the reversal**, stated plainly:

- **A fifth board type in the fleet.** The one-spare-per-role property is genuinely weakened;
  it was the original argument and it loses to cost parity plus physical cleanliness.
- **"Radios off" reverts to a discipline** on the T-2CAN rather than a structural guarantee.
  Never add `wifi:`/`api:`/`ota:`/`bluetooth:` to a bridge entry point.
- **Brownout is the mirror image of before:** the T-2CAN pins `CONFIG_ESP_BROWNOUT_DET`
  explicitly, where the RP2040's detector is fixed-function and not observable from ESPHome.
  This one favours the T-2CAN.

**The CANBed path is kept, not deleted**, for two reasons: it is a second source if T-2CANs
become unobtainable, and it is the **only** board that can carry `buttons+bridge` — the
T-2CAN has no 8-button set. Both paths are CI-compile-gated.

### 2. `registry/nodes.csv` gains a single-valued `profile` column

The `sensors` boolean is replaced by `profile`, one value per row:

| `profile` | Packages composed | Deployment |
|---|---|---|
| `buttons` | `buttons_8` | wall plate, no sensing (was `sensors=0`) |
| `buttons+sensors` | `buttons_8` + `sensor_kit` | wall plate with the ADR-0006 kit (was `sensors=1`) |
| `sensors` | `sensor_kit` | sensor puck, no switch plate (newly expressible) |
| `bridge-t2can` | `bridge` on the T-2CAN board | segment forwarder only — **preferred** |
| `bridge` | `bridge` on CANBed + add-on | segment forwarder only, second source |
| `buttons+bridge` | `buttons_8` + `bridge` on CANBed + add-on | wall plate that is also a forwarder (CANBed only) |

**Mutual exclusion is structural, not validated.** A single-valued enum cannot express
"bridge and sensors"; two boolean columns could, and would rely on the generator to reject it.
This is the mechanism by which ADR-0005's single-purpose-firmware requirement stops being a
rule someone has to remember. `bridge+sensors` is not merely absent from the table — it is a
string the registry rejects, and a test asserts no profile ever pairs those two packages.

**`buttons+bridge` is a deliberate, bounded relaxation of that rule.** Some CAN segments
split at a button box; insisting on a dedicated forwarder there would put two boards in one
back-box for no reliability gain. Buttons are the only package that can ride along, because
they are the only one that adds neither blocking I/O nor a new way to hang the forwarding
loop — GPIO edges and timers, nothing more. The sensor kit stays excluded for exactly the
reason it always was (see Alternatives): its unbounded I2C hang path turns a room fault into
a dark segment. The pin budget closes with no conflict — buttons hold GP10 and GP19-25, the
onboard MCP2515 holds GP2/3/4/9/11, and `can1`'s chip select takes the last free header pin,
GP8 — and `canbus/tests/compile_buttons_bridge.yaml` is the gate that keeps it closing.

A `buttons+bridge` row is filed under the `bridge` prefix and kind. Bridging is the
high-consequence role: its failure darkens a segment, where a button failure darkens one
switch. `ls canbus/nodes/` should surface the former.

One cost is accepted here: ADR-0005 asks for "clean, adequate power" to each bridge, and a
wall back-box is a worse power environment than a junction box. That is the trade for not
running a separate forwarder to a place the cable already passes through.

The column is named `profile` because ADR-0006 §5 already calls this a *"deployment profile"*.
Adding a combination is a new enum value and a new package tuple — no schema change. That is
exactly how `buttons+bridge` arrived, one table row, hours after this ADR was accepted.

### 3. `base_node.yaml` splits into `node_core.yaml` + `buttons_8.yaml`

`node_core.yaml` keeps identity, globals, and the heartbeat — and, since the second
amendment, **no board include at all**: the profile supplies the board, because a bridge may
target an ESP32-S3 while every other profile targets the RP2040. All `node_core.yaml` asks of
a board is that it declare `can0`. `buttons_8.yaml`
carries the 8-button set and the `debounce_ms` requirement. Generated nodes compose
`node_core` plus their profile's packages, and nothing else. The split is what makes both a
button-less bridge and a `buttons+bridge` wall plate expressible from the same parts — before
it, every node got 8 GPIO binary sensors whether or not it had a switch plate.

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

**Gated per board** via the `bridge_hf_loop` substitution, which each board file sets:

- **CANBed: on.** Both ports are polled MCP2515s, so the loop gate is the binding constraint,
  and there is no RTOS idle task to starve.
- **T-2CAN: off.** Less needed (the backbone side is interrupt-driven TWAI, so only the
  single-segment zone side is polled) and actively risky: spinning the loop task without
  yielding can starve the FreeRTOS idle task, and `CONFIG_ESP_TASK_WDT_PANIC` would turn that
  into a reboot loop — the exact opposite of the fail-safe posture. Revisit only with evidence
  from the open-item-2 soak test, and only alongside the idle-task watchdog settings.

The drops this guards against would otherwise be **invisible**: they occur at the MCP2515
before `bridge_enqueue()`, so `ERR_BRIDGE_QUEUE_OVERFLOW` never latches; ESPHome's own overrun
detection is compiled out at `logger: level: INFO`; and the protocol carries no sequence
numbers, so a receiver cannot infer a gap.

### 7. The T-2CAN firmware is restored as a first-class board package

The first version of this ADR archived `devices/bridge.yaml` to `canbus/archive/`, on the
reasoning that maintaining a second bridge profile for a single owned board was not worth the
code. §1 explains why that was reversed within the day.

It came back split the way every other board is: hardware in **`boards/lilygo-t-2can.yaml`**
(ESP32-S3 platform and sdkconfig, SPI, the GPIO9 reset pulse, `can0` TWAI + `can1` MCP2515),
behaviour staying in the shared, now board-agnostic `canbus/packages/bridge.yaml`. The archive
directory is gone — nothing is parked there any more.

Reviving it cost exactly what the table was designed to cost: **one `PROFILES` row**, plus
lifting the board include out of `node_core.yaml` so a profile can choose its own MCU. That
second part is a genuine structural improvement the reversal forced, and it is why a future
third bridge board would be cheaper still.

## Consequences

### Positive
- Two independently-sourceable bridge boards, so a supply failure in either does not block the
  build-out.
- "Bridge and sensors on one board" becomes unrepresentable rather than merely forbidden.
- Bridges inherit node health monitoring, the central map, and the HA entity generation.
- `sensors`-without-buttons becomes expressible — a real deployment the old schema could not describe.
- Every generator branch becomes a `PROFILES` lookup instead of an `if has_sensors` chain.
- Radios-off and the watchdog get stronger; one fewer MCU family in the bridge role.

### Negative / costs
- **A fifth board type in the fleet.** The one-spare-per-role property that motivated the
  original CANBed-only decision is weakened; see §1 for why that trade was accepted.
- Two bridge paths to keep working, hence three bridge compile fixtures rather than one.
- On the CANBed path both ports are polled 2-buffer MCP2515s. Mitigated by §6, but §6 leans on
  an ESPHome-internal API. The T-2CAN path does not have this problem on the backbone side.
- On the CANBed path the add-on module on flying leads is mechanically the weakest part of a
  device that lives behind a wall for years. A small carrier PCB would close this; not in scope.
- Neither board isolates its CAN ports, so a bridge ties two segments' grounds together.
- `nodes.csv` changes shape; pre-live doctrine means editing the header and the committed CSV in place, with no migration shim.

## Alternatives considered

- **CANBed-only (no T-2CAN).** The first version of this ADR. Rejected on the second
  amendment: the add-on module turned out not to be a commodity, cost parity killed the
  saving, and the physical result was worse. See §1.
- **T-2CAN-only (delete the CANBed path).** Rejected: it would leave a single supply source
  for a load-bearing device, and `buttons+bridge` would become inexpressible.
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
3. **On the CANBed path only:** verify the 3.3 V add-on module end to end, including that its
   120 Ω termination jumper matches the bridge's position on the segment (fitted only at a
   segment end), and set `clock:` in `boards/canbed-rp2040-can1.yaml` to the module's actual
   crystal — it currently says 16 MHz, and the one candidate that passes the survey (Seeed
   105100001) is **8 MHz**. Getting this wrong yields correct-looking config, no frames, and a
   fault that presents as bad wiring.
3b. **Identify the CANBed's own transceiver.** The pinned V1.1 Eagle schematic shows
   `U3 = MCP2551` with VDD on the 3V3 net, while the Zephyr board port documents an
   SN65HVD230. The parts are pin-identical SOIC-8, so the symbol may simply be stale — but an
   actual MCP2551 at 3.3 V is out of spec (4.5–5.5 V) with a weak dominant differential. Read
   the chip marking on a board in hand and correct the docs to match.
4. **Segment count and bridge count** — still ADR-0005 open item 1. This ADR makes bridges
   cheap to build; it does not decide how many the house needs.
5. **`i2c: timeout:` on `sensor_kit.yaml`.** Out of scope here (it affects sensor nodes, not
   the profile mechanism), but the missing bound found during this evaluation should be closed
   on its own.

## Notes

This ADR does not touch the wire protocol (ADR-0001/0007), the control model (ADR-0003), or the
`map.json` consumer contract. It changes which board a bridge runs on, and how a node's config
is composed from the registry.
