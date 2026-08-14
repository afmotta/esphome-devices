---
adr: 0021
title: 'QuinLED An-Quad as a second CAN LED actuator board: a 4-channel, WiFi-only sibling to the An-Penta, on one shared board-neutral actuator package'
status: 'Proposed'
date: '2026-08-14'
deciders: ['Alberto']
author: 'Claude'
dependsOn:
  - 'ADR-0020: CAN actuator nodes and the CAT_OUTPUT command slice (this board is a second consumer of that slice; the protocol, binding target, and gateway dispatch are reused unchanged)'
  - 'ADR-0017: Node deployment profiles (adds a second external-actuator profile, led-quad, through the existing profile.external seam)'
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (the An-Quad joins the An-Penta as a QuinLED analog-LED actuator board; the T-Connect Pro gateway is unchanged)'
extends:
  - 'ADR-0020: applies the same CAN-actuator pattern to a different board (4 channels instead of 5, WiFi-only instead of LAN8720) AND generalizes ADR-0020''s per-board an_penta_can.yaml into one shared, board-neutral led_can_actuator.yaml. No load-bearing decision of ADR-0020 changes.'
relatedDocuments:
  - docs/adr/0020-can-actuator-nodes-output-slice.md
  - boards/an-quad.yaml
  - lighting/packages/led_can_actuator.yaml
  - devices/an-quad-1.yaml
  - devices/an-penta-1.yaml
  - canbus/tools/generate_nodes.py
  - registry/nodes.csv
  - .github/workflows/verify.yml
---

# ADR-0021: QuinLED An-Quad as a second CAN LED actuator board

## Status

**Proposed** (2026-08-14). Implemented; the registry artifacts regenerate cleanly (node 103,
profile `led-quad`) and the native/Python test battery passes. Both An-Penta and An-Quad entry
points were added to CI's `esphome config` validate list (`.github/workflows/verify.yml` +
`scripts/ci-dummy-secrets.sh`), closing the gap where the An-Penta entry point (ADR-0020) had no CI
config-validation. Not yet hardware-verified — the CAN bench test (a gateway + An-Quad on a
terminated pair) is the outstanding proof. Extends ADR-0020; changes none of its load-bearing
decisions.

## Context

ADR-0020 made the QuinLED An-Penta-Plus a first-class CAN actuator node: the lighting gateway drives
its LED strips over a dedicated `CAT_OUTPUT` CAN command when Home Assistant is down, independent of
WiFi/router/HA/HTTP, while HA still drives them normally over the WiFi native API. The mechanism —
the `CAT_OUTPUT` / `MSG_OUT_SET_CHANNEL` protocol slice, the `output:` binding target, the
`external`-profile registry seam, and the gateway's `fire_binding_fallback()` dispatch — was
deliberately built as a general actuator layer, not an An-Penta special case ("any future CAN
actuator reuses it", ADR-0020 §1).

The QuinLED **An-Quad** is that future actuator: a smaller, cheaper ESP32 analog-LED board with
**four** PWM channels and, unlike the An-Penta-Plus, **no Ethernet PHY** (WiFi only). Alberto wants
it supported as a second LED controller, integrated with a CAN transceiver in exactly the way the
An-Penta is.

**Hardware (quinled.info An-Quad pinout + its ESPHome sample):** classic ESP32-WROOM-32; four LEDC
channels on `GPIO16 / GPIO17 / GPIO5 / GPIO19` (`GPIO5` is a strapping pin the board is designed to
drive — the same situation as the An-Penta's `GPIO12`/`GPIO2`); an onboard DS18B20 on `GPIO18`; and
two spare GPIOs broken out on the expansion header. The An-Quad has no QWIIC/I²C header, so those
two spare header GPIOs — not a repurposed I²C bus — host the external **SN65HVD230** 3.3 V CAN
transceiver (2 GPIOs for TWAI TX/RX plus power). The two pins are `GPIO22` (tx → CTX) and `GPIO23`
(rx ← CRX), confirmed from the An-Quad schematic (quinled.info was unreachable from the build
environment, so they were supplied directly); neither is a strapping pin, so the tx/rx assignment is
free. As with any mid-bus node, its bus-end termination discipline applies (only the two physical
ends terminate).

## Decision

Add the An-Quad following ADR-0020's pattern, differing only where the board differs, and take the
second actuator as the trigger to generalize the actuator package:

1. **Board package `boards/an-quad.yaml` — WiFi-only, no network indirection.** Four LEDC channels
   (`led_ch1..led_ch4`); `ignore_strapping_warning` on the `GPIO5` channel; `esp32dev` / esp-idf.
   Because the board has no Ethernet, there is **no `-ethernet`/`-wifi` split, no `network_package`
   substitution, and no `enable_ethernet` toggle** — the WiFi config is declared inline in the board
   file. (The swappable-network-package pattern only earns its keep on a board that has both, like
   the An-Penta-Plus.) The two spare header GPIOs are exposed as `aux_gpio_1`/`aux_gpio_2`
   substitutions and left UNCLAIMED (AD-4: the entry point decides their use).

2. **One shared, board-neutral actuator package `lighting/packages/led_can_actuator.yaml`.** The
   An-Penta's `an_penta_can.yaml` is renamed and generalized: `can0` (esp32_can on the entry point's
   `can_tx_pin`/`can_rx_pin`, 125 kbps) with the `on_frame` that applies `CAT_OUTPUT`
   `MSG_OUT_SET_CHANNEL` commands addressed to its node_id (channel 0 → `tw1`, channel 1 → `tw2`)
   plus a `CAT_STATUS` heartbeat. Both boards group their channels into two `cwww` strips with ids
   `tw1`/`tw2`, and the transceiver pins already come from the entry point, so nothing in the package
   was board-specific except comments — one file now serves both. (`devices/an-penta-1.yaml` and
   `devices/an-quad-1.yaml` both `!include` it.) This is ADR-0020's "any future CAN actuator reuses
   it" made literal.

3. **Entry point `devices/an-quad-1.yaml`.** Two tunable-white (`cwww`) strips over the four channels
   (ch1/ch2 and ch3/ch4), WiFi + HA API (the normal path, `api: reboot_timeout: 0s` to survive HA
   outages), an authenticated `web_server` for local diagnostics, and the shared actuator package
   wired to `aux_gpio_1`/`aux_gpio_2`.

4. **A second external-actuator profile, `led-quad`.** `generate_nodes.py` gains a `led-quad`
   Profile beside `led-penta` — same empty `boards`/`packages`, gated by the existing
   `profile.external` attribute (no `if profile ==` branch). `registry/nodes.csv` gets node 103, so
   the An-Quad reserves a node_id and lands in `node_map.h` / `map.json` / HA health and heartbeats
   like any node, but generates no `canbus/nodes/*.yaml`.

5. **CI config-validation for both actuator entry points.** `devices/an-penta-1.yaml` and
   `devices/an-quad-1.yaml` are added to `verify.yml`'s `esphome config` list, with their
   `an_penta_1`/`an_quad_1` keys added to `ci-dummy-secrets.sh`. ADR-0020 left the An-Penta entry
   point out of CI; adding the An-Quad was the moment to close that for both.

The `CAT_OUTPUT` protocol, `bindings.py` validation/canonicalization, `BindingEntry`, and the
gateway dispatch are **unchanged** — a channel is already bounded by a coarse constant (`MAX_CHANNEL
= 7`), which covers both boards, so no per-actuator channel count enters the registry. The
empty-manifest hash `d66767448ba37b2f` is unchanged.

## Consequences

### Positive

- **Pure reuse, now also DRY.** The protocol slice, binding target, arbitration spine, and gateway
  dispatch are untouched; the actuator YAML is one shared file instead of one per board. The addition
  is board scaffolding + one registry row + one profile row.
- **A cheaper/smaller actuator option.** Deployments that need four channels and have WiFi coverage
  get a lower-cost board on the same one-shelf-of-spares family, driven by the same gateway fallback.
- **No fork, no Ethernet complexity, no network indirection.** WiFi-only means the An-Quad never
  touches the ADR-0016 shared-SPI Ethernet fork or its mandatory upgrade check, and its board file
  has no swappable-network-package machinery — strictly simpler than the An-Penta-Plus.
- **Both actuator entry points now CI-validated**, where before neither was.

### Negative / costs

- **A transceiver per An-Quad**, and its onboard termination removed unless it sits at a bus end —
  identical to the An-Penta cost.
- **One shared file couples the two boards.** A change to `led_can_actuator.yaml` now affects both
  the An-Penta and the An-Quad at once — the price of DRY. It is mitigated by the file being tiny and
  board-neutral (all board specifics — pins, channel wiring — live in the entry points), and by both
  boards being CI-config-validated so a break surfaces immediately.
- **WiFi-only fallback caveat.** The An-Quad has no wired network at all, so its *normal* (HA-up)
  path depends on WiFi. This is exactly why the CAN fallback matters: the HA-down path is wired and
  survives a WiFi/router/HA outage regardless.

## Alternatives considered

- **Keep a dedicated `an_quad_can.yaml` beside `an_penta_can.yaml`** (one file per board). Rejected in
  favour of the shared package (Decision §2): the two files differed only in comments, and both
  boards already supply their board specifics from the entry point, so the duplication bought nothing
  but drift risk. A third board with a genuinely different channel layout could still fork the file if
  needed.
- **Reuse the `led-penta` profile for the An-Quad.** Rejected: the profile name is the human-readable
  board identity in `ls canbus/nodes/`, `map.json`, and health entities; a 4-channel WiFi-only board
  labelled `led-penta` would misreport what is on the bus. A distinct `led-quad` costs one table row.
- **A swappable `-wifi` network package (as the An-Penta-Plus has).** Rejected for a board with no
  second network to swap to: it is indirection with one possible value. WiFi is inlined in the board
  file instead (Decision §1).
- **Treat the An-Quad as an HTTP/`web_server` actuator.** The withdrawn ADR-0020 predecessor, rejected
  for the same reasons there: it leans on the WiFi/HA/HTTP stack the fallback must survive.
