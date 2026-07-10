---
title: 'HVAC controller swap — boards/t-connect-pro.yaml + devices/climate-control.yaml onto it'
type: 'feature'
created: '2026-07-10'
status: 'ready-for-dev'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'bb7f173f4bc9499ce3722d4f164e2013d5441003'
final_revision: ''
context: ['{project-root}/_bmad-output/planning-artifacts/adrs/0014-standardized-controller-modbus-io-hardware.md', '{project-root}/_bmad-output/implementation-artifacts/spec-hvac-baseline-config-green.md', '{project-root}/_bmad-output/implementation-artifacts/spec-vesta-modbus-relay-32ch.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** Per ADR-0014, the HVAC master swaps from the Waveshare ESP32-S3-POE
(`boards/waveshare-s3.yaml` — 8 onboard PCA9554 relays, two 8-ch Modbus relay boards, a
PCF85063 RTC, and several onboard peripherals with no consumers outside that file) to a
**LilyGO T-Connect Pro** driving a single **Waveshare Modbus RTU Relay 32CH** bank. No board
file for the T-Connect Pro exists yet, and per AD-4/AD-9 a board file with no consumer is
dead weight — it must land in the same commit as its first real user.

**Approach:** Create `boards/t-connect-pro.yaml` (+ `-ethernet`/`-wifi` network variants),
modeled directly on the existing `boards/waveshare-s3.yaml` / `waveshare-s3-ethernet.yaml` /
`waveshare-s3-wifi.yaml` triad (read all three first), and swap
`devices/climate-control.yaml` onto it in the same commit. This is a **hardware swap only**
— every room/floor file, every vesta component, and the analog-output/MEV wiring are
untouched; only the board include and the two relay-board includes change.

**Verified pin facts** (LilyGO GitHub `Xinyuan-LilyGO/T-Connect-Pro` — the Waveshare wiki
403s automated fetchers, don't re-fetch either source):

| Function | Pins |
|---|---|
| RS485 (Modbus, auto-direction transceiver) | TX=IO17, RX=IO18 — **identical to the current `modbus_uart` pins**, so `uart:` config carries over unchanged except the board itself |
| CAN (TWAI, onboard transceiver) | TX=IO6, RX=IO7 — unconsumed by HVAC (hvac-on-CAN stays deferred); only matters if this board is later reused for a CAN-consuming entry point |
| W5500 Ethernet (SPI) | SCLK=IO12, MOSI=IO11, MISO=IO13, CS=IO10, INT=IO9, RST=IO48 |
| RS232 | TX=IO4, RX=IO5 — **unused, free** (an earlier revision of this plan repurposed IO4 for 1-Wire; superseded below) |
| I²C | SDA=IO39, SCL=IO40 — hosts the (unused) onboard touch controller plus two new external boards this spec adds: a DS2484 1-Wire bridge and a PCF85063 RTC breakout |
| No PoE, no onboard relay/GPIO-expander usable for climate relays (all relays now live on the Modbus bank) |

**Revised 2026-07-10 (Alberto, after this spec was first drafted):** 1-Wire moves to a
**DS2484 I²C→1-Wire bridge** (ESPHome `one_wire` platform `ds2484`, address `0x18`) instead of
a bare GPIO one-wire bus on IO4 — the I²C bridge supplies correct bus power to the two
DS18B20 supply-water sensors, which a plain GPIO one-wire bus does not. **The RTC is also
restored** (not dropped) via a cheap external **PCF85063** I²C breakout (address `0x51`) on
the same bus — the exact chip/ESPHome component `boards/waveshare-s3.yaml` already used
onboard, just moved to an external breakout on the new board's I²C pins (IO39/40) instead of
its old onboard PCA9554-adjacent bus (IO42/41). (Alberto's example part, Adafruit #5188, is a
DS3231 board — ESPHome 2026.5.0 has no native `ds3231` time component; source a PCF85063- or
DS1307-based breakout instead, both natively supported.) Both new I²C devices, and the RTC's
`homeassistant`-time sync source, are **hvac-only** — lighting has no use for wall-clock time
or 1-Wire sensors — so per AD-4 they belong in `devices/climate-control.yaml`, not the shared
board file (see Code Map).

**Confirmed zero-consumer sweep** (so dropping the OLD onboard peripherals is safe, not a
guess): grepped the full repo for `\bdi[1-8]\b`, `rgb_led`, `rtttl_buzzer`, `rtttl_play`,
`homeassistant_time`, `pcf85063` outside `boards/waveshare-s3.yaml` itself — the **only** hit
is `devices/climate-control.yaml:46` (`time_id: pcf85063_time`, the `seasonal_mode` var —
**unchanged by this spec**, since the restored RTC keeps the same id, see Code Map). Every
other onboard-peripheral id (`di1..di8`, `rgb_led`, `rtttl_buzzer`/`rtttl_play`,
`homeassistant_time`) has no other consumer in the repo and is dropped cleanly. Note this
sweep is about the OLD board's onboard PCF85063 instance (wired to different pins, part of
the hardware being retired) — it is not evidence against the NEW external PCF85063 breakout
this spec adds; that's a different physical device that happens to share a component name.

## Boundaries & Constraints

**Always:**
- Read `boards/waveshare-s3.yaml`, `boards/waveshare-s3-ethernet.yaml`,
  `boards/waveshare-s3-wifi.yaml` fully before writing anything — the new files are siblings
  in the same pattern (the `enable_ethernet` substitution selecting between an ethernet and
  a wifi network package, `esphome.name`/`friendly_name` from device vars, `api.encryption`,
  `ota`), not a reinvention.
- **esp32 block style:** use the `variant: esp32s3` + explicit `flash_size`/`framework` shape
  already proven in this repo for a non-Waveshare-catalog S3 board (`devices/gateway.yaml`'s
  `esp32: {variant: esp32s3, flash_size: 16MB, framework: {type: esp-idf}}`), not a `board:
  <catalog-id>` shorthand — the T-Connect Pro has no ESPHome board-catalog entry.
- **Framework: attempt `esp-idf` first** (matches gateway/bridge convention). This is a real
  compile-time risk, not a formality: the full HVAC stack (`pid` climate, `slow_pwm`,
  `modbus_controller`, `dallas`/`one_wire`, `packet_transport`/`udp`, `combination` sensor)
  must actually compile under esp-idf on ESPHome 2026.5.0+. If `esphome compile` fails on a
  genuine framework incompatibility (not a typo), fall back to `framework: {type: arduino}`
  in the board file and record exactly which component failed and why in this spec's Design
  Notes — do not silently swallow a real compile error by guessing arduino up front.
- **The board file owns:** `esphome`/`esp32`/`psram`, `logger`, `api.encryption`, `ota`,
  the network package selection (`enable_ethernet`), the RS485 `uart: {id: modbus_uart, ...}`
  (IO17/IO18, keep the existing bus params: `baud_rate: 38400, data_bits: 8, parity: EVEN,
  stop_bits: 1` — ADR-0014 keeps these pending the bring-up parity check, so don't change
  them here), and the physical `i2c: {sda: GPIO39, scl: GPIO40, id: i2cbus}` bus (universal —
  every T-Connect Pro has this trace; harmless to declare even for a consumer, like the
  gateway, that populates it with no devices).
- **The board file does NOT own** (stays entry-point composition per AD-4, matching how
  `devices/climate-control.yaml` already owns its own `modbus:`/`one_wire:` blocks today):
  the `modbus:` bus binding (`id: rs485_bus`), the CAN bus (unconsumed by hvac; would be
  canbus's `health.yaml` if this board were ever composed into a CAN-consuming entry point),
  no relay/analog output definitions (those come entirely from the Modbus boards), and —
  **revised from this spec's first draft** — no `one_wire:`, no RTC, and no
  `time: platform: homeassistant` either: all three are hvac-only (the DS18B20 supply-water
  sensors and `seasonal_mode`'s calendar logic are hvac concerns; lighting has no use for
  wall-clock time), so they belong in `devices/climate-control.yaml`, consuming the board's
  shared `i2cbus`.
- `devices/climate-control.yaml` changes: board include → `t-connect-pro.yaml`; the two 8-ch
  relay includes (`relays_1` @0x2 offset 8, `relays_2` @0x3 offset 16) collapse into **one**
  `modbus_relay_board_32ch.yaml` include (`controller_id: relay_board_1`, `modbus_address:
  0x2`, `id_offset: 0` → `relay_1..relay_32`, mirroring the gateway's relay-bank address per
  ADR-0014 §4); the analog board include (`analog_outputs_1` @0x1) is untouched; MEV
  (`hvac/mev_modbus.yaml` @0x10, included from `first-floor.yaml`) is untouched; the
  `one_wire_01` block changes from a bare GPIO bus (`pin: GPIO21`) to the DS2484 I²C bridge
  (`i2c_id: i2cbus, address: 0x18`) — its id stays `one_wire_01`, so `mixing_pump.yaml`'s
  `one_wire_bus_id` references need no change; a new `time:` block (two entries:
  `platform: homeassistant` syncing a `platform: pcf85063` RTC, id kept as `pcf85063_time` —
  same id as before, so `seasonal_mode`'s `time_id` var needs **no change**) plus an
  `esphome.on_boot: [pcf85063.read_time]` hook (restoring the exact boot-time RTC read the
  old board file used to do) are added.
- **Depends on P1 and P2 being done first**: this spec's own verification (`esphome config`/
  `compile` on the full climate-control tree) is only meaningful once P1's baseline fix is in
  place, and the 32-ch relay package (P2) must exist before it can be included here.
- One commit (AD-9): the new board files and the entry-point swap land together — a board
  file with no consumer, or an entry point pointing at a nonexistent board file, both leave
  the tree red.

**Block If:** none — every disposition here follows directly from ADR-0014 and the confirmed
zero-consumer sweep above; there's no open design choice for Alberto.

**Never:**
- Do not touch any file under `hvac/rooms/**` — every room/floor file already references
  `relay_N`/`analog_output_N` ids that resolve unchanged under the new topology
  (`id_offset: 0` on the 32-ch board reproduces exactly `relay_1..relay_32`; the analog board
  is untouched). If you find yourself wanting to edit a room file, stop — that means the
  channel mapping drifted from ADR-0014 and the board/entry-point change needs fixing instead.
- Do not touch `hvac/mev_modbus.yaml`, `hvac/mev_demand.yaml`, or any `vesta/packages/**`
  file — MEV and every component/coordinator are hardware-agnostic and already correct.
- Do not touch `devices/gateway.yaml` or anything under `lighting/`/`canbus/` — the gateway
  swap is P4's job, on its own timeline.
- Do not add a `board:` catalog shorthand for the T-Connect Pro speculatively — if you find
  one exists in a newer ESPHome release, that's a nice-to-have for a later cleanup, not
  something to chase down mid-spec; the `variant:` form is the verified-working baseline.
- Do not invent replacement onboard peripherals (buzzer, RGB status LED, digital inputs) for
  the ones being dropped — they have zero consumers (confirmed above); adding new ones "to
  not lose functionality" is scope creep nobody asked for.
- Do not add a version bump or compatibility shim (pre-live, in-place edits only).

</intent-contract>

## Code Map

- `boards/t-connect-pro.yaml` — **new file**, modeled on `boards/waveshare-s3.yaml`:
  - `substitutions:` — `wifi_package`/`ethernet_package` (`!include` the two new network
    variant files), `enable_ethernet: true` default.
  - `packages: network_package: ${ethernet_package if enable_ethernet else wifi_package}`
  - `esphome: {name: ${device_name}, friendly_name: ${friendly_name}, min_version:
    2026.3.0, comment: "LilyGO T-Connect Pro"}` — no `on_boot` RTC-write hook (no RTC).
  - `esp32: {variant: esp32s3, flash_size: 16MB, framework: {type: esp-idf}}` (fallback
    `arduino` only if compile proves esp-idf incompatible — see Boundaries).
  - `psram: {mode: octal, speed: 80MHz}` (T-Connect Pro is 8MB octal PSRAM, same as today).
  - `logger:`, `api: {encryption: {key: ${encryption_key}}}` (no custom `rtttl_play` action
    — that action and its `rtttl_buzzer` output/`buzzer` ledc output are dropped, zero other
    consumers confirmed), `ota: [{platform: esphome, password: ${ota_password}}]`.
  - `uart: [{id: modbus_uart, tx_pin: GPIO17, rx_pin: GPIO18, baud_rate: 38400, stop_bits: 1,
    data_bits: 8, parity: EVEN}]` — same params as today, same physical pins (T-Connect
    Pro's RS485 happens to share IO17/18 with the old board).
  - `i2c: [{sda: GPIO39, scl: GPIO40, id: i2cbus, scan: false, frequency: 100kHz}]` — the
    bus only; no devices declared here (RTC and DS2484 are hvac-only, see Boundaries).
  - No `time:` block at all in the board file — moved entirely to `devices/climate-control.yaml`.
  - No `pca9554:`, `binary_sensor:` (di1-8/status/boot-button), `output:` (buzzer),
    `rtttl:`, `light:` (RGB), `switch:` (the 8 onboard relays), or custom `api.actions:` —
    all dropped per the confirmed zero-consumer sweep. Keep `button:` (restart/factory_reset/
    safe_mode) — generic ESPHome housekeeping buttons, not board-specific hardware.
- `boards/t-connect-pro-ethernet.yaml` — **new file**, modeled on
  `waveshare-s3-ethernet.yaml`'s shape (same `ethernet_info` text_sensor block) but with the
  T-Connect Pro's actual W5500 pins: `type: W5500, clk_pin: GPIO12, mosi_pin: GPIO11,
  miso_pin: GPIO13, cs_pin: GPIO10, interrupt_pin: GPIO9, reset_pin: GPIO48` (the old board
  has no reset pin wired; this one does — include it).
- `boards/t-connect-pro-wifi.yaml` — **new file**, identical shape to
  `waveshare-s3-wifi.yaml` (wifi + wifi_info text_sensor), no pin differences (WiFi has no
  board-specific pins).
- `devices/climate-control.yaml`:
  - `packages.base` (~line 6-10): `file: ../boards/waveshare-s3.yaml` → `../boards/t-connect-pro.yaml` (vars unchanged: `enable_ethernet: true`).
  - `packages.relays_1`/`packages.relays_2` (~lines 20-37): delete both; replace with one
    `relays: !include {file: ../vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml,
    vars: {controller_id: relay_board_1, controller_name: "Relay Board 1", modbus_address:
    0x2, modbus_bus_id: rs485_bus, update_interval: 2s, id_offset: 0}}`.
  - `packages.seasonal_mode.vars.time_id` (~line 46): **unchanged** — stays `pcf85063_time`
    (the restored RTC keeps the same id the old board file used).
  - `one_wire` block (~lines 74-77): replace the `platform: gpio, pin: GPIO21` entry with
    `platform: ds2484, id: one_wire_01, i2c_id: i2cbus, address: 0x18` (id unchanged, so
    `mixing_pump.yaml`'s `one_wire_bus_id: one_wire_01` var passes need no edits).
  - New `time:` block (add near the `one_wire:` block): `platform: homeassistant` with
    `on_time_sync: [pcf85063.write_time]`, plus `platform: pcf85063, id: pcf85063_time,
    i2c_id: i2cbus` (default address `0x51`) — restores the exact two-source time setup
    `boards/waveshare-s3.yaml` used to provide, just moved here since it's hvac-only.
  - New `esphome.on_boot` entry: `[pcf85063.read_time]` (the old board file's boot hook,
    now here since `esphome.climate-control.yaml` doesn't otherwise set `esphome:` — check
    whether `defaults:`-only composition still lets you add an `esphome:` key alongside it;
    it does, ESPHome merges top-level keys from packages and the entry point additively).
  - `analog_outputs_1` package block: untouched (still `modbus_address: 0x1, id_offset: 0`).
  - The two `binary_sensor: !extend any_pid_requesting_{heat,cool}` blocks: untouched (they
    reference room-level PID ids, not board hardware).
- `hvac/CLAUDE.md` — Appendices A ("Modbus Register Quick Reference"), B ("Relay Assignment
  Reference"), C ("Sensor Address Assignments") describe the Gen-1 KC868 A6/A16 topology and
  are now doubly stale (already stale before this spec per the repo's own history; this spec
  makes them describe hardware that no longer exists at all). Rewrite them to reflect the
  live topology: one Modbus master (the T-Connect Pro) on `rs485_bus` at 38400 8E1, analog
  board @0x1 (channels → `analog_output_1..8`), relay board @0x2 (channels →
  `relay_1..relay_32`), MEV @0x10 — and the channel-assignment table from ADR-0014/this
  spec's own Code Map (which relay/output id drives which zone — already documented in
  `devices/climate-control.yaml` and the room files; Appendix B should describe that live
  mapping, not invent a new one). The "Master/Slave Pattern" section describing KC868-A6/
  A16 board-to-board Modbus goes — there is one master, no slaves. Leave the PID architecture
  and entity-ID convention sections alone (they're hardware-independent and already correct).

## Tasks & Acceptance

**Execution:**
- [ ] Read `boards/waveshare-s3.yaml`/`-ethernet.yaml`/`-wifi.yaml` fully
- [ ] Create `boards/t-connect-pro.yaml`, `boards/t-connect-pro-ethernet.yaml`,
  `boards/t-connect-pro-wifi.yaml` per the Code Map
- [ ] Swap `devices/climate-control.yaml`'s board include, collapse the two relay-board
  includes into one 32-ch include, switch `one_wire_01` to the DS2484 bridge, add the
  restored `time:` block (homeassistant + pcf85063) and its `on_boot` RTC-read hook
  (`seasonal_mode`'s `time_id` needs no change — same id, `pcf85063_time`)
- [ ] Run `esphome config` then `esphome compile` on `devices/locals/climate-control.yaml`;
  if compile fails on a genuine esp-idf incompatibility, switch the board file's framework to
  `arduino` and record the failing component in Design Notes
- [ ] Rewrite `hvac/CLAUDE.md` Appendices A-C (and the "Master/Slave Pattern" section) to the
  live one-master/one-relay-bank/one-analog-board/MEV topology

**Acceptance Criteria:**
- Given `esphome config devices/locals/climate-control.yaml`, when run after this swap, then
  it exits 0 (building on P1's baseline fix) with no missing-ID or unresolved-include errors.
- Given `esphome compile devices/locals/climate-control.yaml`, when run after this swap, then
  it exits 0 on the ESP32-S3 target (esp-idf, or arduino if the framework fallback was
  needed — record which).
- Given `git diff --stat` after this spec, when compared against the file list above, then
  **no file under `hvac/rooms/**` or `vesta/packages/**` appears** — the swap changed only
  the board layer and the entry point.
- Given the compiled config, when every existing `switch.relay_N` / `output.analog_output_N`
  entity id is enumerated, then the set is identical to before this swap (`relay_1..relay_32`,
  `analog_output_1..analog_output_8`) — same names, same count, different backing hardware.
- Given `hvac/CLAUDE.md` after the rewrite, when Appendices A-C are read, then they describe
  the live single-master/32-ch-relay/8-ch-analog/MEV topology, not KC868-A6/A16.

## Design Notes

_Fill in during execution: which framework (esp-idf or arduino) was actually used, and if
esp-idf failed, exactly which component/error forced the fallback to arduino._

The T-Connect Pro's CAN transceiver (IO6/IO7) is wired but genuinely unused by this entry
point — hvac-on-CAN sensor consumption is a separate, still-unimplemented frozen contract
(ADR-0006), explicitly out of this spec's scope. Don't add a `canbus:` block "since the pins
are there" — that would be scope creep against ADR-0014's own non-goals list.

The relay bank's `modbus_address: 0x2` matches the gateway's relay bank address (also `0x2`,
per P4) — this is ADR-0014 §4's mirrored-addressing decision so a spare 32CH board swaps into
either system without re-addressing. Don't "helpfully" pick a different address to avoid
confusion between the two systems' banks; the whole point is that they're identical.

## Verification

**Commands:**
- `esphome config devices/locals/climate-control.yaml` -- expected: exits 0
- `esphome compile devices/locals/climate-control.yaml` -- expected: exits 0
- `git diff --stat` -- expected: `boards/t-connect-pro.yaml` (new),
  `boards/t-connect-pro-ethernet.yaml` (new), `boards/t-connect-pro-wifi.yaml` (new),
  `devices/climate-control.yaml` (modified), `hvac/CLAUDE.md` (modified) — nothing else
- `grep -c "relay_" devices/climate-control.yaml` -- sanity check the relay include block
  collapsed to one entry (compare against the pre-spec two-entry baseline)
- `grep -n "GPIO21" devices/climate-control.yaml boards/t-connect-pro*.yaml` -- expected: no
  hits (the bare-GPIO one-wire bus is fully retired)
- `grep -n "pcf85063" devices/climate-control.yaml` -- expected: hits (the restored RTC lives
  here now); `grep -n "pcf85063" boards/t-connect-pro.yaml` -- expected: no hits (RTC is
  entry-point-owned, not board-owned)
- `grep -n "ds2484" devices/climate-control.yaml` -- expected: one hit (the `one_wire:` block)

**Manual checks (if no CLI):**
- Read the new `boards/t-connect-pro.yaml` top to bottom against `boards/waveshare-s3.yaml`:
  confirm every section either has a clear T-Connect Pro equivalent or was deliberately
  dropped per the zero-consumer sweep — nothing silently missing, nothing silently invented.

## Spec Change Log

### 2026-07-10 — Revision before execution (spec not yet run)
Alberto reconsidered two of ADR-0014's original mitigations while reviewing the plan:
1-Wire moves from a bare-GPIO repurposing of the RS232 pins to a DS2484 I²C bridge (correct
sensor bus power); the RTC, originally dropped in favor of `homeassistant` time only, is
restored via an external PCF85063 I²C breakout. Both now live on the board's I²C bus
(SDA=IO39/SCL=IO40) at the entry-point level (hvac-only), not the shared board file. Updated
throughout this spec before any execution began — no code was written against the superseded
design.

## Review Triage Log

## Auto Run Result

Status: ready-for-dev — not yet executed.
