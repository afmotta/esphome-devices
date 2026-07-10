---
title: 'HVAC controller swap — boards/t-connect-pro.yaml + devices/climate-control.yaml onto it'
type: 'feature'
created: '2026-07-10'
status: 'done'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'bb7f173f4bc9499ce3722d4f164e2013d5441003'
final_revision: ''
baseline_commit: '9dafe8225d7a14197f7993e6d87049836afc4478'
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
| I²C | SDA=IO39, SCL=IO40 — hosts the (unused) onboard touch controller plus one new external board this spec adds: a DS2484 1-Wire bridge |
| No PoE, no onboard relay/GPIO-expander usable for climate relays (all relays now live on the Modbus bank); no dedicated RTC hardware for now (SNTP instead — see below) |

**Revised 2026-07-10 (Alberto, after this spec was first drafted):** 1-Wire moves to a
**DS2484 I²C→1-Wire bridge** (ESPHome `one_wire` platform `ds2484`, address `0x18`) instead of
a bare GPIO one-wire bus on IO4 — the I²C bridge supplies correct bus power to the two
DS18B20 supply-water sensors, which a plain GPIO one-wire bus does not. This is hvac-only
(lighting has no use for 1-Wire sensors), so per AD-4 it belongs in
`devices/climate-control.yaml`, not the shared board file (see Code Map).

**Revised 2026-07-10 (Alberto, second pass, same day):** the RTC question (this spec first
proposed restoring a PCF85063 breakout) is deferred — **start with ESPHome's native `sntp`
time platform** (no hardware, syncs over the network; confirmed present in ESPHome 2026.5.0,
`DEPENDENCIES = ["network"]`) and revisit dedicated RTC hardware only if operational
experience shows it's needed (ADR-0014 Open item 4). `seasonal_mode`'s `time_id` var takes
this SNTP source instead of the old board's `pcf85063_time`. SNTP is also hvac-only in this
spec's scope (nothing in lighting currently consumes wall-clock time), so it lands in
`devices/climate-control.yaml` alongside DS2484, not the shared board file — same AD-4
reasoning, kept consistent with the 1-Wire placement above.

**Confirmed zero-consumer sweep** (so dropping the OLD onboard peripherals is safe, not a
guess): grepped the full repo for `\bdi[1-8]\b`, `rgb_led`, `rtttl_buzzer`, `rtttl_play`,
`homeassistant_time`, `pcf85063` outside `boards/waveshare-s3.yaml` itself — the **only** hit
is `devices/climate-control.yaml:46` (`time_id: pcf85063_time`, the `seasonal_mode` var —
**this spec changes it** to the new SNTP source's id, see Code Map). Every onboard-peripheral
id from the old board (`di1..di8`, `rgb_led`, `rtttl_buzzer`/`rtttl_play`,
`homeassistant_time`, `pcf85063` itself — the old board's onboard RTC instance, a different
physical device from anything this spec adds) has no other consumer in the repo and is
dropped cleanly.

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
  **revised from this spec's first draft** — no `one_wire:` and no `time:` block of any kind
  (neither the originally-planned `homeassistant`/`pcf85063` pair nor the current `sntp`
  platform): both are hvac-only (the DS18B20 supply-water sensors and `seasonal_mode`'s
  calendar logic are hvac concerns; lighting has no current use for wall-clock time), so they
  belong in `devices/climate-control.yaml`, and `one_wire` additionally consumes the board's
  shared `i2cbus`.
- `devices/climate-control.yaml` changes: board include → `t-connect-pro.yaml`; the two 8-ch
  relay includes (`relays_1` @0x2 offset 8, `relays_2` @0x3 offset 16) collapse into **one**
  `modbus_relay_board_32ch.yaml` include (`controller_id: relay_board_1`, `modbus_address:
  0x2`, `id_offset: 0` → `relay_1..relay_32`, mirroring the gateway's relay-bank address per
  ADR-0014 §4); the analog board include (`analog_outputs_1` @0x1) is untouched; MEV
  (`hvac/mev_modbus.yaml` @0x10, included from `first-floor.yaml`) is untouched; the
  `one_wire_01` block changes from a bare GPIO bus (`pin: GPIO21`) to the DS2484 I²C bridge
  (`i2c_id: i2cbus, address: 0x18`) — its id stays `one_wire_01`, so `mixing_pump.yaml`'s
  `one_wire_bus_id` references need no change; a new `time: [{platform: sntp, id: sntp_time}]`
  block is added (no RTC, no on_boot hook — SNTP needs neither); `seasonal_mode`'s `time_id`
  var changes from `pcf85063_time` to `sntp_time`.
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
    2026.3.0, comment: "LilyGO T-Connect Pro"}` — no `on_boot` hook (no RTC to sync).
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
    bus only; no devices declared here (DS2484 is hvac-only, see Boundaries).
  - No `time:` block at all in the board file — SNTP lives in `devices/climate-control.yaml`
    (hvac-only for now; nothing in lighting currently needs wall-clock time).
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
  - `packages.seasonal_mode.vars.time_id` (~line 46): `pcf85063_time` → `sntp_time`.
  - `one_wire` block (~lines 74-77): replace the `platform: gpio, pin: GPIO21` entry with
    `platform: ds2484, id: one_wire_01, i2c_id: i2cbus, address: 0x18` (id unchanged, so
    `mixing_pump.yaml`'s `one_wire_bus_id: one_wire_01` var passes need no edits).
  - New `time:` block (add near the `one_wire:` block): a single entry,
    `platform: sntp, id: sntp_time` — no RTC, no `on_boot` hook, no `on_time_sync` action;
    SNTP needs none of them (it syncs itself over the network on its own schedule).
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
- [x] Read `boards/waveshare-s3.yaml`/`-ethernet.yaml`/`-wifi.yaml` fully
- [x] Create `boards/t-connect-pro.yaml`, `boards/t-connect-pro-ethernet.yaml`,
  `boards/t-connect-pro-wifi.yaml` per the Code Map
- [x] Swap `devices/climate-control.yaml`'s board include, collapse the two relay-board
  includes into one 32-ch include, switch `one_wire_01` to the DS2484 bridge, add a
  `time: platform: sntp` block, and update `seasonal_mode`'s `time_id` to `sntp_time`
- [x] Run `esphome config` then `esphome compile` on `devices/locals/climate-control.yaml`;
  if compile fails on a genuine esp-idf incompatibility, switch the board file's framework to
  `arduino` and record the failing component in Design Notes
- [x] Rewrite `hvac/CLAUDE.md` Appendices A-C (and the "Master/Slave Pattern" section) to the
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

**Framework: esp-idf, no fallback needed.** `esphome compile devices/locals/climate-control.yaml`
succeeded on the first attempt under `framework: {type: esp-idf}` (74.55s, RAM 27.4%, Flash
9.0%) — the full HVAC stack (`pid` climate, `slow_pwm`, `modbus_controller`, `dallas`/
`ds2484`/`one_wire`, `packet_transport`/`udp`, `combination` sensor) compiles cleanly under
esp-idf on ESPHome 2026.5.0. The `arduino` fallback path in the board file was never
exercised.

`esphome config` also passed clean: no missing-ID or unresolved-include errors. Entity-id
sweep post-compile confirmed `relay_1..relay_32` (32) and `analog_output_1..analog_output_8`
(8) — identical names/count to the pre-swap topology, different backing hardware, as required.

`hvac/CLAUDE.md`'s "Modbus Communication Architecture" section and Appendices A-C were
rewritten to the live single-master/32-ch-relay/8-ch-analog/MEV topology (mode sync now
correctly attributed to the `seasonal_mode` coordinator, not a fictional register). Two
"Common Tasks"/debugging bullets outside the Code Map's named sections (`9600, 8N1` baud
claims in "Debugging Modbus Issues" and "Debugging Modbus and PID issues") directly
contradicted the new Appendix C (`38400 8E1`) once it was written, so they were corrected too
for internal coherence — a narrow, load-bearing fix, not a broader doc pass.

The T-Connect Pro's CAN transceiver (IO6/IO7) is wired but genuinely unused by this entry
point — hvac-on-CAN sensor consumption is a separate, still-unimplemented frozen contract
(ADR-0006), explicitly out of this spec's scope. Don't add a `canbus:` block "since the pins
are there" — that would be scope creep against ADR-0014's own non-goals list.

The relay bank's `modbus_address: 0x2` matches the gateway's relay bank address (also `0x2`,
per P4) — this is ADR-0014 §4's mirrored-addressing decision so a spare 32CH board swaps into
either system without re-addressing. Don't "helpfully" pick a different address to avoid
confusion between the two systems' banks; the whole point is that they're identical.

SNTP (not a hardware RTC) is a deliberate ADR-0014 decision, not a placeholder to silently
upgrade during this spec — if `seasonal_mode`'s calendar logic needs a clock that survives a
reboot with no network, that's ADR-0014 Open item 4 (a future spec adding a PCF85063
breakout on the same `i2cbus`), not something to preempt here.

## Verification

**Commands:**
- `esphome config devices/locals/climate-control.yaml` -- expected: exits 0
- `esphome compile devices/locals/climate-control.yaml` -- expected: exits 0
- `git status --short` -- expected: `boards/t-connect-pro.yaml` (new),
  `boards/t-connect-pro-ethernet.yaml` (new), `boards/t-connect-pro-wifi.yaml` (new),
  `devices/climate-control.yaml` (modified), `hvac/CLAUDE.md` (modified) — nothing else.
  (`git diff --stat` alone won't show the three new files — they're untracked, not
  modified — use `git status --short` or stage first.)
- `grep -c "relay_" devices/climate-control.yaml` -- sanity check the relay include block
  collapsed to one entry (compare against the pre-spec two-entry baseline)
- `grep -n "GPIO21" devices/climate-control.yaml boards/t-connect-pro*.yaml` -- expected: no
  hits (the bare-GPIO one-wire bus is fully retired)
- `grep -n "pcf85063" devices/climate-control.yaml boards/t-connect-pro.yaml` -- expected: no
  hits (no RTC hardware in this spec's scope; SNTP replaces it)
- `grep -n "ds2484" devices/climate-control.yaml` -- expected: one hit (the `one_wire:` block)
- `grep -n "platform: sntp\|sntp_time" devices/climate-control.yaml` -- expected: hits in the
  new `time:` block and the `seasonal_mode` include's `time_id` var

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

### 2026-07-10 — Second revision, same day (spec still not yet run)
Alberto reconsidered the RTC piece of the prior revision: instead of adding the PCF85063
breakout now, start with ESPHome's native `sntp` time platform (no hardware) and only add
dedicated RTC hardware later if operational experience shows it's needed (now ADR-0014 Open
item 4). The DS2484 1-Wire decision from the previous revision is unaffected. Updated
throughout this spec before any execution began.

## Review Triage Log

### 2026-07-10 — Blind Hunter + Edge Case Hunter (parallel, review-loop 1)

No `intent_gap` or `bad_spec` findings — no loopback triggered. `esphome config`/`compile`
independently re-verified passing by Blind Hunter.

**Patched (6, applied directly to this diff):**
1. `hvac/CLAUDE.md` intro paragraph said "controller hardware is not yet finalized" —
   stale now that ADR-0014 decided and this spec implemented the swap (still pre-live:
   decided ≠ physically deployed). Corrected.
2. `hvac/CLAUDE.md` Appendix C overstated ADR-0014 §4's address mirroring — only the
   relay bank (`0x2`) mirrors across the gateway/hvac buses; `0x1`/`0x10` are hvac-only
   with nothing to mirror against. Corrected.
3. `boards/t-connect-pro.yaml` inherited `min_version: 2026.3.0` from the waveshare-s3
   template, but `sntp`/`ds2484` were only verified against 2026.5.0. Bumped, with a
   comment explaining why.
4. Added a comment noting the T-Connect Pro's unused CAN TWAI pins (IO6/IO7), for the
   same AD-4 "entry-point composition, not board concern" reasoning already given to I²C.
5. `hvac/home-assistant/dashboards/system-monitoring.yaml`'s "Modbus Communication" grid
   had tiles for `relay_board_1_status`/`relay_board_2_status` — both entities stop
   existing once the two 8-ch boards collapse into one 32-ch board with no status sensor
   (by the 32-ch driver's own design, see its doc comment). Removed the two dead tiles,
   left a comment explaining why no replacement tile exists.
6. This spec's own Verification section said `git diff --stat` would show the 3 new
   board files — untracked files don't appear in plain `git diff --stat`. Corrected to
   `git status --short`.

**Deferred (4, appended to `deferred-work.md`):**
- DS2484 `active_pullup`/`strong_pullup` left at component defaults (both `false`);
  correctness depends on whether the two supply-water DS18B20 probes are wired
  parasitic or externally-powered, which nothing in the repo documents and which only a
  hardware bring-up can confirm. Ties into ADR-0014 Open item 1.
- Pre-existing HA dashboard relay-id mismatches for 7 rooms, confirmed via `git log` to
  predate this spec entirely (not caused by the swap) — needs its own dashboard-fix pass.
- `boards/waveshare-s3.yaml`(+ network variants) now fully orphaned by this swap; flagged
  for P6 (`spec-hardware-docs-sweep`) to sweep alongside the already-planned a6/a16
  deletion, since its current scope text doesn't mention waveshare-s3.
- 32-ch relay board's `update_interval: 2s` (spec-directed, carried forward unchanged
  from the 8-ch default) still has the P2-documented "not re-validated for 32 coils'
  traffic" caveat — this spec is the first to actually exercise it against real bus
  timing, but validating requires hardware bring-up, not code. Ties into ADR-0014 Open
  item 1.

**Rejected (3, no action — noise or already correctly out of scope):**
- Analog board's status sensor aliasing channel 1's own register (pre-existing, minor,
  functionally fine for connectivity purposes).
- `i2c:` list-form vs. the old board's flat-mapping form — functionally equivalent, and
  actually more consistent with this same file's `uart:` list style.
- Root `CLAUDE.md` still describing KC868 hardware — explicitly P6's job per ADR-0014's
  phase table, correctly untouched by a P3 spec.

## Auto Run Result

Status: in-review — implementation complete, `esphome config`/`compile` both pass on
esp-idf (no arduino fallback), all acceptance criteria met, review findings triaged with
6 patches applied directly and 4 items deferred to `deferred-work.md`. Awaiting Alberto's
disposition on the deferred DS2484 pullup-mode question in particular before hardware
bring-up.

## Suggested Review Order

**Board hardware definition (new files, entry point)**

- Start here: esp32/framework block, modeled on `waveshare-s3.yaml` but esp-idf-verified.
  [`t-connect-pro.yaml:26`](../../boards/t-connect-pro.yaml#L26)

- RS485 bus on the same physical pins as the old board — only the board changed.
  [`t-connect-pro.yaml:61`](../../boards/t-connect-pro.yaml#L61)

- New shared I²C bus (bus only, no devices) — feeds the DS2484 bridge added at the entry point.
  [`t-connect-pro.yaml:53`](../../boards/t-connect-pro.yaml#L53)

- Version floor bumped to the only version actually verified end-to-end.
  [`t-connect-pro.yaml:15`](../../boards/t-connect-pro.yaml#L15)

- W5500 Ethernet pins are T-Connect Pro-specific, not copied from the old board.
  [`t-connect-pro-ethernet.yaml:4`](../../boards/t-connect-pro-ethernet.yaml#L4)

**Entry-point swap (`devices/climate-control.yaml`)**

- Board include swap — the one line that actually changes the physical controller.
  [`climate-control.yaml:8`](../../devices/climate-control.yaml#L8)

- Two 8-ch relay includes collapse into one 32-ch include at `id_offset: 0`.
  [`climate-control.yaml:20`](../../devices/climate-control.yaml#L20)

- 1-Wire moves from bare GPIO to the DS2484 I²C bridge — same `id`, no downstream edits needed.
  [`climate-control.yaml:66`](../../devices/climate-control.yaml#L66)

- SNTP replaces the PCF85063 RTC as the time source — no hardware, network-only.
  [`climate-control.yaml:72`](../../devices/climate-control.yaml#L72)

- `seasonal_mode`'s `time_id` repointed to the new SNTP source.
  [`climate-control.yaml:37`](../../devices/climate-control.yaml#L37)

**Documentation: live topology rewrite (`hvac/CLAUDE.md`)**

- Master/slave framing replaced with the real single-master pattern.
  [`CLAUDE.md:122`](../../hvac/CLAUDE.md#L122)

- Appendix A: real register semantics (coils/holding registers) replace a fictional register map.
  [`CLAUDE.md:213`](../../hvac/CLAUDE.md#L213)

- Appendix B: live relay-to-zone mapping sourced from the actual room files.
  [`CLAUDE.md:221`](../../hvac/CLAUDE.md#L221)

- Appendix C: real bus members and addresses, with the mirroring claim scoped correctly.
  [`CLAUDE.md:249`](../../hvac/CLAUDE.md#L249)

**Review-driven fix: dead dashboard tile**

- Removed two tiles pointing at connectivity sensors the 32-ch board doesn't expose.
  [`system-monitoring.yaml:47`](../../hvac/home-assistant/dashboards/system-monitoring.yaml#L47)
