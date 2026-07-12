# Firmware

## Hardware Verification

Hardware open questions resolved from the official Longan Labs CANBed RP2040 V1.1 Eagle schematic pinned to commit `fdefed9e521864c67a05bf19a4e5046428b86662`.

### OQ-1: Button GPIO numbers (CANBed RP2040)

**Status:** Confirmed  
**Value:** GPIO20, GPIO21, GPIO22, GPIO23, GPIO24, GPIO25, GPIO26, GPIO27 — the 8 digital I/O pins
exposed on the 9×2 expansion header (J1). Wire external push-button switches (active low,
internal pull-up) to these pins.

> **⚠️ Template correction required:** The existing `generate_nodes.py` template uses
> GPIO2, GPIO3, GPIO4, GPIO5 as button placeholder defaults. GPIO2/3/4 are **wrong** —
> they are the SPI SCK/MOSI/MISO lines used internally by MCP2515 (confirmed by schematic).
> Update template defaults to use GPIO20–GPIO27 instead.

**Source:** CANBed RP2040 V1.1 Eagle schematic — `CANBED_RP2040_V11_EAGLE` repository,
GitHub (pinned): <https://github.com/Longan-Labs/CANBED_RP2040_V11_EAGLE/blob/fdefed9e521864c67a05bf19a4e5046428b86662/CANBed2040_V1.1.sch> — J1 header net connections confirm
8 GPIO lines with no external pull-up resistors (internal pull-up required on each line).

---

### OQ-2: MCP2515 INT pin (CANBed RP2040)

**Status:** Confirmed  
**Value:** GPIO11  
**Source:** CANBed RP2040 V1.1 Eagle schematic — `CANBED_RP2040_V11_EAGLE` repository,
GitHub (pinned): <https://github.com/Longan-Labs/CANBED_RP2040_V11_EAGLE/blob/fdefed9e521864c67a05bf19a4e5046428b86662/CANBed2040_V1.1.sch> — `INT` net explicitly
connects `U5(!INT)` (MCP2515 interrupt output) to `U2(GPIO11)` (RP2040).

> **⚠️ Template correction required:** The existing template assumes `can_int_pin: "GPIO20"`.
> This is **wrong** — GPIO20 is a general-purpose digital I/O header pin, not the INT line.
> Update to `can_int_pin: "GPIO11"`. An incorrect INT pin causes MCP2515 to fall back to
> polling mode, which will miss CAN frames under burst conditions at 125 kbps.

---

### OQ-3: Oscillator frequency (MCP2515 on CANBed RP2040)

**Status:** Confirmed  
**Value:** 16 MHz  
**Source:** CANBed RP2040 V1.1 Eagle schematic — `CANBED_RP2040_V11_EAGLE` repository,
GitHub (pinned): <https://github.com/Longan-Labs/CANBED_RP2040_V11_EAGLE/blob/fdefed9e521864c67a05bf19a4e5046428b86662/CANBed2040_V1.1.sch> — part `X1` (crystal
connected to MCP2515 OSC1/OSC2) has `value="16MHz"`.

> Existing assumption `can_clock: "16MHZ"` is **correct** — no change required.

---

## Complete MCP2515 SPI Pin Reference (CANBed RP2040 V1.1)

All values confirmed from V1.1 Eagle schematic. Use these in Story 2.1
(`canbus/packages/base_node.yaml`) and Story 1.4 (`canbus/tools/generate_nodes.py` template).

| Signal      | RP2040 GPIO | Net name | Template assumption | Correct?  |
| ----------- | ----------- | -------- | ------------------- | --------- |
| SPI SCK     | GPIO2       | SCK      | GPIO18              | ❌ Wrong   |
| SPI MOSI    | GPIO3       | MOSI     | GPIO19              | ❌ Wrong   |
| SPI MISO    | GPIO4       | MISO     | GPIO16              | ❌ Wrong   |
| MCP2515 CS  | GPIO9       | CANCS    | GPIO9               | ✅ Correct |
| MCP2515 INT | GPIO11      | INT      | GPIO20              | ❌ Wrong   |
| Oscillator  | —           | —        | 16 MHz              | ✅ Correct |

---

## ESPHome Version

**Known-good version:** ESPHome 2026.6.5 — confirmed by successful `esphome compile devices/gateway.yaml` (2026-07-12; see `_bmad-output/implementation-artifacts/spec-esphome-2026-6-5-modbus-controller-server-compat.md` for full compile evidence).

> **Not enforced:** no YAML carries an `esphome: min_version:` constraint, so this version is recorded, not pinned — a different installed ESPHome will still build. Treat 2026.6.5 as the last validated baseline; add `esphome: min_version:` if a hard floor becomes necessary.

> **Note:** As of ESPHome 2026.1.0 the `api: password:` option was removed. The gateway uses
> API encryption instead (`api: encryption: key: !secret api_encryption_key`). Generate a key with
> `openssl rand -base64 32` and add it to `secrets.yaml`.
>
> **Migration — re-adopt in HA:** switching from `api: password:` to `api: encryption:` changes the
> gateway's API identity. A gateway already adopted in Home Assistant must be **deleted and re-added**
> in HA (Settings → Devices & Services → ESPHome) with the new encryption key — it will not reconnect
> on the old password entry.

---

## Onboarding: `secrets.yaml`

The gateway reads three secrets at config load. ESPHome resolves `!secret` from a
`secrets.yaml` next to the config file, so it lives in `devices/` (the gateway is the
only secrets user there). There is no pre-flight validation — if `secrets.yaml` is missing or any key
is absent, `esphome compile`/`run` **fails at config load** with a missing-secret error (ESPHome
default behavior). Copy `devices/secrets.yaml.example` to `devices/secrets.yaml` before
the first build:

| Key                  | Value                                            |
| -------------------- | ------------------------------------------------ |
| `wifi_ssid`          | WiFi network name                                |
| `wifi_password`      | WiFi password                                    |
| `api_encryption_key` | base64 key from `openssl rand -base64 32`        |

Nodes have no WiFi/API and require no secrets.

---

## Sensor kit (ADR-0006)

Per-room environment sensors — **SHT45** (precision T/RH, `sht4x` component, addr `0x44`) and
**SEN66** (PM/T/RH/VOC/NOx/CO₂, official ESPHome `sen6x` component, addr `0x6B`) — ship as the
opt-in package `packages/sensor_kit.yaml`. Every measurement is sent as its own CAN frame on
`can_id(CAT_SENSOR, node_id)` every 30 s: `[PROTO_V1, status, meas_type LE16, value LE32]`,
using the `canbus_protocol.h` constants/helpers merged in PR #19.

- **Enable per node** via the `sensors` column in `registry/nodes.csv` (blank/`0` = none,
  `1` = kit) and re-run `tools/generate_nodes.py`. Never hand-edit `nodes/`.
- **Binding rule:** sensor frames carry the host node's `node_id` — a sensor-equipped node's
  registry room must be the sensors' physical room (ADR-0006 §5).
- **Status mapping:** reading `NaN` → `SENSOR_STATUS_UNAVAILABLE` (covers SEN66 warm-up);
  ±inf / int32 overflow or negative raw for an unsigned quantity → `SENSOR_STATUS_OUT_OF_RANGE`;
  otherwise `SENSOR_STATUS_OK` with the scaled value. Degraded frames are sent when the
  component publishes a reading at all (`sen6x` publishes NaN sentinels; `sht4x` publishes
  nothing on a hard I2C failure — there the consumer's 90 s staleness rule is the only cover).
  The consumer (the dedicated HVAC controller, external firmware) ignores non-OK values.
- **Frame pacing:** the send script runs `mode: queued` with 25 ms inter-frame spacing — a
  SEN66 update bursts 9 channels at once and the MCP2515 has only 3 TX mailboxes, so unspaced
  sends would systematically drop the later measurements every cycle.
- **I2C pins (verified):** SDA = `GPIO6`, SCL = `GPIO7` (RP2040 I2C1 pair, clear of MCP2515
  GPIO2/3/4/9/11 and buttons GPIO20–27) — confirmed by Alberto, 2026-06-11. If the wiring
  ever changes, update the `i2c_sda`/`i2c_scl` defaults **in `packages/sensor_kit.yaml`
  itself** (the board design is fixed, so the wiring is fleet-wide; generated node files
  carry no per-node pin substitutions).
- > **⚠️ Still unverified:** SEN66 power over the QwiicBus run (ADR-0006 open item 3) —
  > confirm voltage/current against the host rail and fan inrush per run.
- Compile check without touching generated nodes:
  `esphome compile canbus/tests/compile_sensor_node.yaml`.

---

## Button gestures (ADR-0012)

Every button speaks one vocabulary (`packages/button.yaml`): **single / double / triple
click** (release-time, node-detected) plus the press-phase pair — **`hold`** fires *while
the button is still down* (once the press reaches `hold_ms`, default 800 ms, a substitution
in `button.yaml`), **`hold_release`** fires when that hold ends. The pair drives continuous
control: hold-to-dim, hold-to-move a cover.

- **`long_press`/`extra_long_press` no longer exist** — a long press is *derived* in HA
  as hold → hold_release (see the example in `lighting/home-assistant/ha_hold_automations.yaml`); their
  node-side patterns would match a hold too and fire duplicates (ADR-0012 §2). The
  constants were removed outright (pre-LIVE, nothing fielded); wire values 0x04/0x05 stay
  unassigned so a not-yet-reflashed node's frames decode as `unknown` (logged, dropped)
  instead of misreading as hold. If a binding ever needs the old long vs extra-long (3 s)
  split, HA measures the hold→release gap — no firmware involved.
- **Gateway:** no logic change — `hold`/`hold_release` forward to HA through the existing
  ha_ready/ACK arbitration like any click (recompile picks up the new
  `canbus_protocol.h` strings).
- **HA-side:** copy `lighting/home-assistant/ha_hold_automations.yaml` into Home Assistant as the starting
  point. **Runaway rule (ADR-0012 §5):** every action started by `hold` must reach a bound
  on its own (count-bounded dim loop; covers bound at their end stops) so a lost
  `hold_release` can never run away. Derived long presses satisfy it by construction — a
  lost release means the action just doesn't fire.
- Compile check without touching generated nodes:
  `esphome compile canbus/tests/compile_sensor_node.yaml` (base node + all 8 buttons +
  sensor kit).

---

## ha_ready Arbitration Prototype (ADR-0003)

The gateway carries a prototype of ADR-0003's HA-readiness arbitration: HA proves liveness
(and that it runs the same binding manifest) by calling the `ha_readiness_heartbeat` API
service every 5 s; each button event forwarded to HA carries an `event_id` that HA must ACK
via `ha_ack_event` before the fallback timeout. When HA is not ready — API disconnected,
heartbeat stale, or manifest-hash mismatch — or an ACK is missed, the **fallback only logs**
(`FALLBACK ...` at WARN): no relays exist yet. The manifest hash is now real — the gateway
compares the generated `BINDINGS_MANIFEST_HASH` (see Binding Manifest below), no longer a
placeholder.

- HA-side counterpart: wire the **generated** `canbus/home-assistant/ha_manifest_package.yaml` (readiness
  heartbeat, hash baked in) into HA as a package, and copy `canbus/home-assistant/ha_arbitration_automations.yaml`
  (the hand-maintained ACK automation) into Home Assistant. See Binding Manifest below.
- Observability: the gateway exposes a diagnostic **HA Ready** binary sensor, and the logs
  carry the tuning data: `ACK ... rtt=` (round-trip per event), `FALLBACK ... waited=`
  (actual fallback latency — `ack_timeout_ms` plus up to 250 ms sweep granularity), and
  `LATE ACK ... late=+` (an ACK landing after its fallback fired: the double-action window).
- Tuning (resolves ADR-0003 open item 2 empirically) via `devices/gateway.yaml` substitutions:
  `ha_heartbeat_ttl_ms` (default 15000) and `ack_timeout_ms` (default 500). The manifest hash
  HA must echo is the generated `BINDINGS_MANIFEST_HASH`, not a substitution (see below).
- Since migration Phase 5b-2 the arbitration instance lives in
  `lighting/packages/buttons.yaml` and transport health + the bus in
  `canbus/packages/health.yaml`; `devices/gateway.yaml` composes both (canbus
  package first — it defines `can0`, lighting `!extend`s it).
- Pure logic lives in `protocol/ha_arbitration.h`; native test:
  `g++ -std=c++17 -Wall -Wextra canbus/tests/test_ha_arbitration.cpp -o /tmp/arb && /tmp/arb`

### Health monitoring (ADR-0011)

The gateway watches the **mapped** fleet and surfaces degraded operation to HA. Aliveness lives
on the gateway because only it knows the expected fleet (the compiled map) and hears every
heartbeat; HA cannot notice the silence of a device it has never heard from.

- **One staleness doctrine:** a node is **lost** after 3 missed 30 s heartbeats (90 s,
  `node_lost_timeout_ms`) — the same 3× cadence as ADR-0006 sensor staleness, not a second rule.
- **Edge events to HA** (transition only, never a per-heartbeat stream): `esphome.canbus_node_lost`,
  `canbus_node_recovered`, `canbus_node_error` (carries the changed `error_flags`), alongside the
  existing `canbus_node_unknown`.
- **Aggregate entities** (diagnostic, re-published every 5 s so they survive an HA disconnect):
  **Nodes Online**, **Nodes Total**, **Fallback Events** (count of ha-not-ready + ack-timeout
  fallbacks — a degraded night made visible), **Nodes Missing** (names from the map), plus the
  existing **HA Ready**. ~6 entities regardless of fleet size — per-node entities are materialized
  HA-side from the edge events by the generated package (ADR-0011 open item 2, deferred).
- Pure logic lives in `protocol/node_health.h` (no ESPHome deps, like `ha_arbitration.h`); native test:
  `g++ -std=c++17 -Wall -Wextra canbus/tests/test_node_health.cpp -o /tmp/health && /tmp/health`

---

## Binding Manifest (ADR-0009)

`registry/bindings.yaml` is the binding manifest — ADR-0003's fallback behavior as data:
each binding maps a gesture `(node_id, button, event)` to a controller action (`relay`/`op`).
With `registry/nodes.csv` (identity + placement) it forms the central map; **git is the
system of record** (ADR-0009), so push registry changes promptly — bindings are unrebuildable.

- **Canonical hash:** `tools/bindings.py` computes the `manifest_hash` as SHA-256 over the
  *parsed* manifest with sorted keys (formatting/comments don't matter), truncated to 16 hex.
  `tools/generate_nodes.py` stamps it into `protocol/bindings.h` as `BINDINGS_MANIFEST_HASH`,
  which the gateway compares against the hash HA echoes — agreement un-stubs `ha_ready`.
- **Stdlib-only:** `bindings.py` ships a small reader for a strict YAML subset (scalars only,
  no nesting) so the generator stays dependency-free. Native tests:
  `python3 canbus/tests/test_bindings.py` and `python3 canbus/tests/test_generate_exports.py`.
- **Generated artifacts (ADR-0009 §4/§7), one generator run, all committed:**
  - `protocol/bindings.h` — `BINDINGS_MANIFEST_HASH` **plus** the compiled `BINDINGS[]`
    fallback table (`struct BindingEntry`, `binding_find()`), frozen-additive and currently
    empty (fallback is log-only, ADR-0003 open item 7).
  - `registry/map.json` — the read-only export for non-C consumers (HVAC controller,
    dashboards): `schema_version`, a deterministic `map_version` content marker (not a
    wall-clock — unchanged input regenerates byte-for-byte), `manifest_hash`, and `nodes[]`.
    **Frozen HVAC-consumer contract** (ADR-0009 open item 5, closed 2026-07-05 by
    `spec-map-json-contract`): the frozen-additive field list is `schema_version`,
    `map_version`, `nodes[].node_id`, `nodes[].room_slug`, `nodes[].location`,
    `nodes[].sensors` — fields may be added, never renamed, removed, or reinterpreted
    without a new spec. `manifest_hash` (ha_ready arbitration) and `board` (wall-box
    disambiguation) are explicitly **outside** the freeze: changing them needs no HVAC-side
    compatibility review. `room_slug` joins a node to a climate zone — validated by the
    generator against the climate room packages (`hvac/rooms/**`, never freehand),
    required when `sensors=1`, empty = no climate zone. Numeric `floor` stays canbus
    map-seed metadata; consumers derive the climate floor slug via the fixed table
    0→`ground_floor`, 1→`first_floor`, 2→`second_floor` (`FLOOR_SLUGS` in
    `generate_nodes.py`).
  - `canbus/home-assistant/ha_manifest_package.yaml` — the HA readiness-heartbeat automation with the hash
    baked in, so HA echoes it automatically (no hand-paste). Wire it into HA once as a package.
- **Workflow:** edit `bindings.yaml` → `python3 tools/generate_nodes.py` (validates every
  binding against `nodes.csv`, prints the hash, regenerates all artifacts above) → commit and
  **push** → `python3 tools/check_registry_pushed.py` → recompile/flash the gateway. No
  re-paste step: the HA package carries the hash.
- **Push-discipline gate (ADR-0009 §6 / open item 4):** `tools/check_registry_pushed.py` is
  the mechanical pre-reflash check — it fails (non-zero) unless the registry (and the
  generated artifacts compiled into the controller) is committed *and* `HEAD` is pushed to a
  remote. ADR-0009 §6 makes the remote the backup; bindings are unrebuildable, so reflashing
  a controller whose registry only exists locally is an unbacked-up house. Exit `0` = safe to
  flash, `1` = gate failed, `2` = git error.
- **Drift visibility (ADR-0009 §6):** the gateway exposes two read-only HA diagnostic
  `text_sensor`s — **Binding Manifest Hash** (`BINDINGS_MANIFEST_HASH`) and **Node Map
  Version** (`NODE_MAP_VERSION`, mirroring `map.json`'s `map_version`). Both are compile-time
  constants published once at boot. Compare them on a dashboard against the committed
  `registry/map.json`: a mismatch means "committed in git but not yet reflashed" — the static
  map's failure mode — shows up there instead of as a misbehaving button.

---

## CAN Segment Bridge (ADR-0005)

The bus is segmented (ADR-0005, accepted 2026-06-10): a backbone segment plus per-zone
secondaries in a strict loop-free tree, joined by store-and-forward **software bridges**.
`devices/bridge.yaml` is the bridge firmware, targeting the **LilyGO T-2CAN** (ESP32-S3).
The board's two CAN ports are asymmetric: one is the S3's built-in TWAI controller
(backbone side — interrupt-driven RX with a deep driver queue, suiting the aggregate
backbone traffic), the other an MCP2515 on SPI (zone side) with a hardware reset line on
GPIO9 pulsed at boot. Forward-all in both directions, plus its own node-style heartbeat on
the backbone side so the gateway sees a dead bridge as a missing heartbeat.

ADR-0005's mandatory reliability requirements are mapped directly in the config:
single-purpose firmware, **no radios** (no `wifi:`/`api:`/`ota:` — logs and flashing are
USB-serial), esp-idf watchdogs + brownout detector with panic-reboot, and conservative
paced forwarding (queues buffer bursts; the drain cap meters TX to what the MCP2515 — the
weaker TX side, 3 buffers — sustains at 125 kbps). A drop anywhere latches
`ERR_BRIDGE_QUEUE_OVERFLOW` into the heartbeat until reboot.

- Identity: bridges share the flat `node_id` space (ADR-0007). Allocate an id with
  `tools/allocate_node.py`, set it as the `node_id` substitution, and commission it like a
  node so the gateway names it. (`generate_nodes.py` will also emit an unused
  `nodes/nodeNNN.yaml` for a bridge id — ignore it; `devices/bridge.yaml` is the config.)
- Board, pins, MCP2515 clock (16 MHz), and the GPIO9 reset sequence come from LilyGO's
  reference firmware:
  <https://github.com/Xinyuan-LilyGO/T-2Can/blob/main/esphome/can.yaml>
- Pure forwarding logic lives in `protocol/bridge_forwarding.h`; native test:
  `g++ -std=c++17 -Wall -Wextra canbus/tests/test_bridge_forwarding.cpp -o /tmp/bridge && /tmp/bridge`
- Before wall installation, the ADR-0005 open item 5 soak test must observe on hardware:
  zone-side RX behavior under bursts (ESPHome polls the MCP2515 from `loop()`; 2 RX
  buffers), and watchdog/brownout recovery degrading to *silent* — never holding a segment
  dominant.
