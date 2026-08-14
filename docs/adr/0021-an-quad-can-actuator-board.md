---
adr: 0021
title: 'QuinLED An-Quad as a second CAN LED actuator board: a 4-channel, WiFi-only sibling to the An-Penta, reusing the CAT_OUTPUT slice unchanged'
status: 'Proposed'
date: '2026-08-14'
deciders: ['Alberto']
author: 'Claude'
dependsOn:
  - 'ADR-0020: CAN actuator nodes and the CAT_OUTPUT command slice (this board is a second consumer of that slice; the protocol, binding target, and gateway dispatch are reused unchanged)'
  - 'ADR-0017: Node deployment profiles (adds a second external-actuator profile, led-quad, through the existing profile.external seam)'
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (the An-Quad joins the An-Penta as a QuinLED analog-LED actuator board; the T-Connect Pro gateway is unchanged)'
extends:
  - 'ADR-0020: applies the same CAN-actuator pattern to a different board (4 channels instead of 5, WiFi-only instead of LAN8720). No load-bearing decision of ADR-0020 changes; only board-specific facts differ.'
relatedDocuments:
  - docs/adr/0020-can-actuator-nodes-output-slice.md
  - boards/an-quad.yaml
  - boards/an-quad-wifi.yaml
  - lighting/packages/an_quad_can.yaml
  - devices/an-quad-1.yaml
  - canbus/tools/generate_nodes.py
  - registry/nodes.csv
---

# ADR-0021: QuinLED An-Quad as a second CAN LED actuator board

## Status

**Proposed** (2026-08-14). Implemented; the registry artifacts regenerate cleanly (node 103,
profile `led-quad`) and the native/Python test battery passes. Not yet ESPHome-compiled in CI (the
An-Quad entry point, like the An-Penta's, is compiled directly with device secrets and is not in
`scripts/verification-battery.sh`) and not yet hardware-verified — the CAN transceiver pins are the
one detail to confirm against the QuinLED An-Quad schematic at bring-up (see Consequences). Extends
ADR-0020; changes none of its load-bearing decisions.

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
transceiver (2 GPIOs for TWAI TX/RX plus power). As with any mid-bus node, its bus-end termination
discipline applies (only the two physical ends terminate).

## Decision

Add the An-Quad following ADR-0020's pattern verbatim, differing only where the board differs:

1. **Board package `boards/an-quad.yaml` — WiFi-only.** Four LEDC channels (`led_ch1..led_ch4`);
   `ignore_strapping_warning` on the `GPIO5` channel; `esp32dev` / esp-idf. Because the board has no
   Ethernet, there is **no `-ethernet` variant and no `enable_ethernet` toggle** — the network
   package is always `an-quad-wifi.yaml`. The two spare header GPIOs are exposed as
   `aux_gpio_1`/`aux_gpio_2` substitutions and left UNCLAIMED (AD-4: the entry point decides their
   use), exactly as the An-Penta board exposes its QWIIC pins.

2. **CAN actuator package `lighting/packages/an_quad_can.yaml`.** `can0` (esp32_can on the spare-
   header pins, 125 kbps) with the same `on_frame` that applies `CAT_OUTPUT` `MSG_OUT_SET_CHANNEL`
   commands addressed to its node_id (channel 0 → `tw1`, channel 1 → `tw2`) plus a `CAT_STATUS`
   heartbeat. It is structurally identical to `an_penta_can.yaml` — the reused general slice — kept
   as a dedicated, self-documenting per-board file to match the repo's explicit per-device style and
   so a change to one actuator cannot silently alter the other.

3. **Entry point `devices/an-quad-1.yaml`.** Two tunable-white (`cwww`) strips over the four
   channels (ch1/ch2 and ch3/ch4), WiFi + HA API (the normal path, `api: reboot_timeout: 0s` to
   survive HA outages), an authenticated `web_server` for local diagnostics, and the CAN actuator
   package wired to the spare-header pins.

4. **A second external-actuator profile, `led-quad`.** `generate_nodes.py` gains a `led-quad`
   Profile beside `led-penta` — same empty `boards`/`packages`, gated by the existing
   `profile.external` attribute (no `if profile ==` branch). `registry/nodes.csv` gets node 103, so
   the An-Quad reserves a node_id and lands in `node_map.h` / `map.json` / HA health and heartbeats
   like any node, but generates no `canbus/nodes/*.yaml`.

The `CAT_OUTPUT` protocol, `bindings.py` validation/canonicalization, `BindingEntry`, and the
gateway dispatch are **unchanged** — a channel is already bounded by a coarse constant (`MAX_CHANNEL
= 7`), which covers both boards, so no per-actuator channel count enters the registry.

## Consequences

### Positive

- **Pure reuse.** The protocol slice, binding target, arbitration spine, and gateway dispatch are
  untouched; the addition is board scaffolding + one registry row + one profile row. ADR-0020's
  "any future CAN actuator reuses it" is realized with no new mechanism.
- **A cheaper/smaller actuator option.** Deployments that need four channels and have WiFi coverage
  get a lower-cost board on the same one-shelf-of-spares family, driven by the same gateway fallback.
- **No fork, no Ethernet complexity.** WiFi-only means the An-Quad never touches the ADR-0016 shared-
  SPI Ethernet fork or its mandatory upgrade check — strictly simpler than the An-Penta-Plus.

### Negative / costs

- **A transceiver per An-Quad**, and its onboard termination removed unless it sits at a bus end —
  identical to the An-Penta cost.
- **CAN transceiver pins to confirm.** quinled.info is unreachable from the build environment's
  egress proxy, so the two spare-header GPIOs (`aux_gpio_1`/`aux_gpio_2`, defaulted to
  `GPIO13`/`GPIO23`) were chosen as free, TWAI-valid, non-strapping pins rather than read off the
  schematic. They are isolated as substitutions so confirming/adjusting them against the QuinLED
  An-Quad expansion-header pinout at bring-up is a one-line change, and no other pin depends on them.
- **Near-duplicate CAN package.** `an_quad_can.yaml` and `an_penta_can.yaml` differ only in comments
  and the board they compose onto. Accepted for isolation and self-documentation (see §2); if a
  third board arrives, folding them into one parameterized include is the point to reconsider.
- **WiFi-only fallback caveat.** The An-Quad has no wired network at all, so its *normal* (HA-up)
  path depends on WiFi. This is exactly why the CAN fallback matters: the HA-down path is wired and
  survives a WiFi/router/HA outage regardless.

## Alternatives considered

- **Generalize `an_penta_can.yaml` into one shared `led_can_actuator.yaml` used by both boards.**
  DRYer, but it edits the working An-Penta path for a second board and the two files are already tiny;
  deferred until a third actuator justifies the parameterization (see §2 / Consequences).
- **Reuse the `led-penta` profile for the An-Quad.** Rejected: the profile name is the human-readable
  board identity in `ls canbus/nodes/`, `map.json`, and health entities; a 4-channel WiFi-only board
  labelled `led-penta` would misreport what is on the bus. A distinct `led-quad` costs one table row.
- **Treat the An-Quad as an HTTP/`web_server` actuator.** The withdrawn ADR-0020 predecessor, rejected
  for the same reasons there: it leans on the WiFi/HA/HTTP stack the fallback must survive.
