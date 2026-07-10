---
adr: 0014
title: 'Standardized controller & Modbus I/O hardware: LilyGO T-Connect Pro + Waveshare RTU family for both lighting and HVAC, interchangeable spares'
status: 'Proposed'
date: '2026-07-10'
deciders: ['Alberto']
author: 'Claude (Fable 5)'
dependsOn:
  - 'ADR-0003: Centralized single-controller with on-board fallback (its open item 7 — board selection — is resolved here)'
  - 'ADR-0005: CAN bus topology — segmented multi-bus (gateway sits on the backbone at 125 kbps; unchanged, constrains the controller''s CAN port)'
  - 'ADR-0013: Gateway-local relays, single-click fallback (its §1 transport-agnostic design is exercised here; open item 1 resolved, items 2–3 scheduled)'
supersedes:
  - 'ADR-0013 §1 (realization only): relays as gateway-local outputs → Modbus RTU relay banks over RS485. The progressive-id meaning, single-click fallback semantics, and one-file binding manifest all stand.'
relatedDocuments:
  - canbus/_bmad-output/planning-artifacts/adrs/0013-gateway-local-relays-single-click-fallback.md
  - _bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md
  - devices/gateway.yaml
  - devices/climate-control.yaml
  - boards/waveshare-s3.yaml
  - vesta/packages/devices/modbus-io/modbus_relay_board.yaml
  - lighting/packages/buttons.yaml
  - registry/bindings.yaml
---

# ADR-0014: Standardized controller & Modbus I/O hardware

## Status

**Proposed.** First root-tree ADR (per AD-1 the frozen `canbus/_bmad-output/` tree is never
edited; this file is the disposition record for frozen ADR-0013, which stays marked Proposed in
place). Partially supersedes ADR-0013: only §1's *realization* (gateway-local outputs) is
replaced — by the Modbus relay banks its own transport-agnostic design anticipated. Resolves
ADR-0013 open item 1 (relay count/bound) and ADR-0003 open item 7 (board selection); schedules
ADR-0013 open items 2–3 as implementation phases. Also resolves two Deferred rows in the
architecture spine (master-controller swap; physical gateway split) and the gateway-hardware
documentation discrepancy.

## Context

Three hardware questions had been circling separately:

1. **Lighting needs relay outputs.** ADR-0013's fallback is log-only until they exist, and the
   current gateway — a WiFi-only Waveshare ESP32-S3-RS485-CAN — has none. Docs and config also
   disagree about what the gateway even is (docs: POE-ETH-8DI-8DO with CAN on GPIO2/3; deployed
   config: RS485-CAN board, WiFi, CAN on GPIO15/16).
2. **The HVAC master was due for a swap.** The Waveshare ESP32-S3-POE's W5500 Ethernet occupies
   GPIO15/16 — the very pins the gateway wiring uses for CAN — so that board cannot gain a CAN
   transceiver by copying the known-good wiring, and hvac-on-CAN (the frozen map.json / ADR-0006
   contracts) will eventually want one.
3. **Both systems are pre-live with no spares story.** A different one-off board per system
   makes a failed controller a redesign, not a swap.

Meanwhile the repo already converged on the target *pattern*: the HVAC entry point drives
commodity Modbus RTU I/O boards over one RS485 bus through the reusable
`vesta/packages/devices/modbus-io/` drivers, and the Kincony KC868-A6/A16 generation is orphaned
dead code. What is missing is a controller both systems can share, a 32-channel relay driver,
and lighting's actuation wiring.

## Decision

The stance in one line: **both systems run the same three devices — LilyGO T-Connect Pro
controller, Waveshare Modbus RTU Relay 32CH, Waveshare Modbus RTU Analog Output 8CH (B) — so one
shelf of spares serves the whole house; lighting's relays become a Modbus bank, the move
ADR-0013 §1 explicitly kept registry-free.**

### 1. One device family, interchangeable spares

| Role | Device | Used by |
|---|---|---|
| Controller | LilyGO T-Connect Pro (ESP32-S3-R8, 16MB flash / 8MB PSRAM, W5500 Ethernet, native RS485 + CAN transceivers) | gateway (lighting + canbus), climate-control (hvac) |
| Relays | Waveshare Modbus RTU Relay 32CH (RS485) | both systems |
| 0-10V | Waveshare Modbus RTU Analog Output **8CH (B)** — the voltage variant; the non-B model is 0-20mA current | hvac |

A spare of each swaps into either system: same controller family, mirrored Modbus addressing
(§4), same in-repo drivers.

Integration facts, recorded here because the Waveshare wiki 403-blocks automated fetchers:

- **T-Connect Pro pins:** CAN TWAI TX=IO6 / RX=IO7; RS485 TX=IO17 / RX=IO18 (same pins as
  today's `modbus_uart`); W5500 SPI SCLK=IO12, MOSI=IO11, MISO=IO13, CS=IO10, INT=IO9, RST=IO48;
  RS232 TX=IO4 / RX=IO5 — **unused, free** (§5 revises the original plan to repurpose these; the
  I²C bridge below replaces that); I²C SDA=IO39 / SCL=IO40 — hosts the (unused) onboard touch
  controller plus one new external board added in §5: a DS2484 1-Wire bridge (0x18); display/LoRa
  unused. No PoE, no hardware RTC for now (§5 — SNTP first).
- **Relay 32CH:** coils 0x0000–0x001F (channels 1–32), FC 0x01 read / 0x05 write single /
  0x0F write multiple; write values 0xFF00=on, 0x0000=off, 0x5500=toggle; device address via
  holding register 0x4000 (works on broadcast address 0x00); defaults 9600 8N1, address 0x01.
- **Analog 8CH (B):** holding registers 0x0000–0x0007 (channels 1–8), value in mV
  (0–10000 = 0–10.00V), FC 0x03/0x06/0x10 — matches the existing vesta driver scaling
  (`modbus_analog_output.yaml`, number 0–10000 U_WORD) with zero driver changes.

### 2. Lighting relays are a Modbus bank; ADR-0013's model stands

The relay *transport* moves to a Waveshare 32CH bank on the gateway's RS485 — exactly the "later
move to Modbus relay banks" that ADR-0013 §1 declared needs no registry change. Everything else
in ADR-0013 stands: progressive ids, single-click-only fallback, one binding file, no addresses
anywhere in `registry/`. The promised "`relay_N` → coil map in the gateway config" is realized
as: binding relay id N ↔ coil N ↔ ESPHome switch `relay_N` (0-based), instantiated by the vesta
32CH driver and registered into a fixed-size store that the fallback path indexes.

**Relay-id bound (resolves ADR-0013 open item 1): 0–31** — one bank. Raising it means adding a
bank and amending the validator bound in the same commit.

### 3. Device composition (AD-4: systems own packages, devices own composition)

- **`devices/gateway.yaml`** stays the one physical device composing canbus
  (`canbus/packages/health.yaml` — the bus definition, CAN now at IO6/IO7) and lighting
  (`lighting/packages/buttons.yaml` gate instance, plus the relay bank and fallback actuation).
  **Ethernet replaces WiFi.** The spine's deferred "physical gateway split" resolves as: no
  further split — hvac is already a separate physical device; lighting + canbus continue
  sharing the gateway per AD-4.
- **`devices/climate-control.yaml`**: T-Connect Pro + Analog 8CH (B) @0x1 + Relay 32CH @0x2
  (replacing both the 8 onboard PCA9554 relays and the two 8-ch boards @0x2/0x3) + MEV @0x10.
  Channel ids `relay_1..relay_32` (`id_offset: 0`) keep every room/floor file untouched. The CAN
  transceiver is present but unconsumed — hvac-on-CAN stays deferred.
- **`devices/bridge.yaml`** (LilyGO T-2CAN) unchanged.

### 4. Bus parameters and addressing

Target serial params: **38400 8E1** (today's `rs485_bus`), pending one bring-up check — if the
Waveshare boards' firmware cannot do EVEN parity (both are baud/parity-configurable per their
protocol V2; the MEV unit is the least flexible bus member), the whole bus reconciles at
bring-up as a substitution-level change. Addresses are mirrored across the two buses so
pre-addressed spares swap without re-addressing: relay bank **0x2** on both buses; analog
**0x1** (hvac only); MEV **0x10** (hvac only).

### 5. Known gaps and their mitigations

| Gap | Mitigation |
|---|---|
| No PoE | DC supply; power topology remains with the parked power/electrical ADR (gap-analysis queue #2) |
| No free GPIO for 1-Wire (2× DS18B20 supply-water sensors, the mixing-valve PID inputs) | **Revised 2026-07-10, Alberto:** use a DS2484 I²C→1-Wire bridge (ESPHome `one_wire` platform `ds2484`, address 0x18) on the shared I²C bus (SDA=IO39/SCL=IO40) as the primary design, not a GPIO-repurposing fallback — the I²C bridge supplies correct bus power to the DS18B20s, which a bare GPIO one-wire bus does not. This also frees the RS232 pins (IO4/IO5) entirely; they're unused, not repurposed. |
| No RTC | **Revised 2026-07-10, Alberto (second pass):** start with ESPHome's native **SNTP** time source (`time: platform: sntp`, ESPHome 2026.5.0 confirmed) — no hardware, syncs over the network directly (WiFi/Ethernet — its only dependency), and is strictly more autonomous than the `homeassistant` platform this ADR first proposed: it needs only an NTP server, not HA's API being up. `seasonal_mode`'s `time_id` takes this source (`sntp_time`). Add dedicated RTC hardware **only if operational experience shows it's needed** (e.g. extended outages where neither NTP nor HA is reachable across a reboot, and `seasonal_mode`'s calendar gates need to survive that) — tracked as Open item 4. If/when that happens: a **PCF85063** I²C breakout is the zero-new-component-risk choice (the exact chip `boards/waveshare-s3.yaml` already used, address 0x51) on the same I²C bus DS2484 already puts on this board; Alberto's example part (Adafruit #5188) is a **DS3231** board, which has no native ESPHome `time` component in 2026.5.0 (only `pcf85063` and `ds1307` exist) — source a PCF85063/DS1307 breakout instead, or accept external-component risk for DS3231 specifically. |
| Onboard relay / free-GPIO map undocumented | Verify from the LilyGO schematic during the board-file phase; not part of any contract |
| Two new I²C devices share one bus with the unused touch controller | Confirm no address collision with the onboard CST226SE touch chip at bring-up (DS2484 default 0x18, PCF85063 default 0x51 — neither is a documented touch-chip address, but touch was never characterized for this decision) |
| Display / touch / LoRa unused | Left unconfigured; backlight (IO46) held off |

## Implementation plan

Phased per the approved 2026-07-10 plan — each phase is one spec in
`_bmad-output/implementation-artifacts/`, sized for a single Sonnet 5 session, cut as AD-9
slices (in-place edits, no shims, each slice lands green with its consumers):

| Phase | Spec | Scope | Depends on |
|---|---|---|---|
| P1 | `spec-hvac-baseline-config-green` | Clear the pre-existing `esphome config devices/locals/climate-control.yaml` failures (missing IDs documented as baseline in `spec-phase-4-hvac-gathering.md`) so later gates are meaningful | — |
| P2 | `spec-vesta-modbus-relay-32ch` | 32-ch aggregator package reusing `modbus_relay_switch.yaml`; verify negative `id_offset` substitution arithmetic (else document the 1-based fallback); vesta docs + example compile | — |
| P3 | `spec-hvac-controller-swap-t-connect-pro` | `boards/t-connect-pro*.yaml` (esp-idf, W5500, `modbus_uart`, shared I²C bus) + swap `devices/climate-control.yaml` onto them, adding SNTP time and the DS2484 1-Wire bridge there, as the board's first consumer | P1, P2 |
| P4 | `spec-light-gateway-swap-t-connect-pro` | Gateway board swap + Ethernet + CAN pins IO6/7 + relay bank (`relay_0..31`) exposed as HA switches + the on-boot store registration; fallback stays log-only | P2, P3 |
| P5 | `spec-light-fallback-actuation` | `lighting/protocol/binding_actuation.h` + native test; wire both fallback branches (single-click only, `binding_find`, op fan-out); `bindings.py` MAX_RELAY_ID=31 + tests; fix the stale "input-only/Modbus" gateway comment | P4 |
| P6 | `spec-hardware-docs-sweep` | CLAUDE.md/docs/runbooks; commissioning utilities (address reg 0x4000); delete orphaned `boards/a6*.yaml`/`a16*.yaml`; annotate the resolved spine Deferred rows | P3–P5 |

ADR-0013 open item 3 closes with P4, item 2 with P5, item 4 (generated HA automations) remains
open pending the circuit inventory.

## Consequences

### Positive

- **One spares shelf covers every controller/relay/analog failure in the house** — replacement
  is a re-flash plus an address check, not a redesign.
- Native CAN + RS485 + Ethernet transceivers end the GPIO15/16 collision that blocked the old
  master board, and give the gateway wired networking for the arbitration heartbeats.
- ADR-0013's transport-agnostic bet pays out as designed: zero registry/schema change; the
  validator bound is the only tooling edit.
- Relay placement becomes remoteable again (ADR-0003's original wish) — banks sit where the
  load wiring is short, not where the controller happens to be.
- The driver family already exists in-repo (`modbus-io`); the analog board needs zero driver
  changes and the room/floor configs need zero edits.

### Negative / costs

- **Modbus addressing returns as a maintenance surface** — but in *device config* (one `0x2`
  per entry point), never in the registry; ADR-0013's "no addresses in the registry" holds.
- Fallback actuation now traverses an RS485 write (tens of ms at 38400) instead of a local GPIO;
  acceptable for a lights-on/off safety floor, and the relay bank itself becomes a fallback
  dependency (bank offline ⇒ neither HA nor fallback can switch — same blast radius as the old
  local-relay design, one cable more).
- One more small board to source, mount, and wire (DS2484 bridge) versus the original
  single-board design — cheap, on an I²C bus the board already exposes.
- SNTP's clock has no memory across a reboot when the network is also down (unlike a real
  RTC) — accepted for now; `seasonal_mode`'s calendar gates just don't evaluate correctly
  until the network (and SNTP) come back. Revisit with hardware RTC (Open item 4) if this
  proves to matter in practice.
- Vendor concentration (LilyGO + Waveshare families); accepted for a house.
- The T-Connect Pro's display/touch/LoRa are dead weight; the Lite (no screen) variant is the
  natural buy where offered.

## Alternatives considered

- **Gateway-local relays as ADR-0013 §1 wrote them** (expander/HAT on the gateway board):
  rejected — requires home-run wiring of every fallback-critical circuit to the gateway, has no
  symmetry with hvac, and offers no spare-swap story. §1's transport-agnostic wording
  anticipated exactly this reversal.
- **Keep per-system hardware** (Waveshare-S3 stays for hvac; add some relay-capable one-off for
  lighting): rejected — perpetuates one-off boards, no shared spares, keeps the doc/config
  hardware confusion alive.
- **Revive the Kincony A6/A16 generation**: dead code, no CAN path, legacy 9600 8N1 assumptions;
  the repo already moved past it.
- **One mega-controller hosting lighting + hvac**: rejected 2026-07-06 (AD-7 amendment) —
  separate physical devices per domain; AD-4 already makes the composition cheap either way.

## Open items

1. **Bring-up verification list** (first hardware session): Waveshare parity/baud support vs
   the 38400 8E1 target (MEV is the constraint); onboard-relay pins and free-GPIO audit from the
   LilyGO schematic; confirm the physical analog board is the (B) voltage variant; confirm the
   DS2484 (0x18) doesn't collide on the I²C bus with the unused onboard touch controller.
2. **Lighting circuit inventory** → binding authoring + generated HA automations (ADR-0013 open
   item 4), and whether one 32-ch bank suffices (else raise the §2 bound with a second bank).
3. **Power/PoE**: deferred to the parked power/electrical ADR (gap-analysis queue #2, blocked on
   the house's corrugated tubes).
4. **Hardware RTC re-evaluation**: SNTP is the time source for now (§5). If operation shows the
   controller needs to keep correct time across a reboot with no network reachable (e.g.
   `seasonal_mode`'s calendar gates misbehaving during an outage), add a PCF85063 I²C breakout on
   the already-present I²C bus (address 0x51) — a small, well-understood addition, not a redesign
   (a PCF85063, not the DS3231/Adafruit-5188 example — see §5 for why).

## Notes

The frozen-tree ADR-0013 file keeps its Proposed status untouched (AD-1); this ADR is its
disposition record. Hardware quantities (how many spares to buy) are a purchasing note, not
architecture. Implementation phases start only after this ADR is Accepted.
