---
adr: 0016
title: 'Share one SPI controller between the W5500 Ethernet and the onboard display, via a local fork of ESPHome''s ethernet component'
status: 'Accepted'
date: '2026-07-26'
deciders: ['Alberto']
author: 'Claude (Opus 5)'
dependsOn:
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (chose the LilyGO T-Connect Pro for both controllers, and §109 chose Ethernet over WiFi; this ADR is what makes those two choices compatible with the onboard panel)'
  - 'ADR-0015: Split canbus health monitoring onto its own device (fixes the two T-Connect Pro entry points this ADR affects)'
amends:
  - 'ADR-0014: the T-Connect Pro board notes assumed the onboard display and the W5500 could coexist by sitting on separate SPI controllers arbitrated by their CS lines. That is electrically impossible; this ADR replaces the mechanism with a single shared controller. No hardware selection in ADR-0014 changes — the board, the relay/analog banks, and the Ethernet-over-WiFi decision all stand.'
relatedDocuments:
  - _bmad-output/planning-artifacts/adrs/0014-standardized-controller-modbus-io-hardware.md
  - libs/esphome_overrides/ethernet/
  - boards/t-connect-pro-display.yaml
  - boards/t-connect-pro-ethernet.yaml
  - devices/locals/climate-control-touch.yaml
  - devices/light-controller-touch.yaml
  - climate/packages/ui/climate_touch_ui.yaml
  - lighting/packages/ui/light_touch_ui.yaml
---

# ADR-0016: Share one SPI controller between Ethernet and the onboard display

## Status

**Accepted** (2026-07-26). Hardware-verified on the T-Connect Pro before acceptance, including a
30 fps full-screen-redraw stress test. Amends ADR-0014's SPI-sharing mechanism only. Implemented
the same day across both T-Connect Pro touch entry points.

## Context

The LilyGO T-Connect Pro wires the onboard ST7796 panel and the W5500 Ethernet controller to the
**same three pads** — SCLK GPIO12, MOSI GPIO11, MISO GPIO13 — with distinct chip selects
(display CS=21, W5500 CS=10). ADR-0014 chose this board for both controllers, and §109 chose
Ethernet over WiFi for the wired reliability its arbitration heartbeats want.

The repo's first attempt at supporting the panel assumed those two facts were compatible: it put
the display bus on a *second* SPI controller (`interface: spi3`) and marked the pins
`allow_other_uses`, on the theory that "bus access is arbitrated by the distinct CS lines."

**That theory is wrong, and the panel never worked.** Bring-up showed random static pixels — an
uninitialised ST7796 displaying whatever was in its GRAM, meaning not one frame had ever reached
it. The root cause, traced through the ESPHome 2026.7.1 sources and confirmed against generated
code:

1. An **ESP32-S3 pad has exactly one output source.** Two SPI controllers aimed at one pad cannot
   both drive it; the pad's routing is a single selector, so the last peripheral configured wins.
2. ESPHome's W5500 driver **hardcodes its own `spi_bus_initialize()`** on `SPI2_HOST`
   (`ethernet_component_esp32.cpp:182`) rather than going through the `spi:` hub — so the display
   was pushed to SPI3_HOST, a different controller on the same pads.
3. GPIO11/12/13 are **SPI2's native IO_MUX pads**, so the W5500's initialisation takes them
   directly.
4. **Setup order sealed it:** `spi:` is priority BUS (1000), the display DATA (600), ethernet
   WIFI (250). The panel was initialised and turned on *first*; the W5500 then took the pads;
   LVGL's first flush happens later still, from `loop()`. So the panel was correctly configured
   and then permanently starved.

CS-line arbitration is real, but only among devices on **one** controller. The original mechanism
never had a chance, and `allow_other_uses` merely silenced ESPHome's own pin bookkeeping — it
cannot make silicon drive a pad from two sources.

This is not a T-Connect Pro quirk. Upstream ESPHome documents the limitation
("SPI based chips do *not* use Spi. This means that SPI pins can't be shared with other devices"),
its ethernet validator explicitly rejects a matching interface, and
[esphome#9882](https://github.com/esphome/esphome/issues/9882) — the same collision on an M5Stack
CoreS3 with a LAN PoE base — was **closed as not planned**, with a maintainer responding that
"having a display and ethernet on the same spi bus is a terrible idea."

Without a fix, the options were: WiFi + display (surrendering ADR-0014 §109's wired decision), or
Ethernet + no display (making the commissioning UI dead code). Both were considered and rejected
in favour of the option below.

## Decision

**Put both devices on ONE SPI controller (`spi2`), arbitrated by their CS lines, using a local
fork of ESPHome's `ethernet` component that lets it attach to a bus `spi:` already owns.**

### 1. The fork (`libs/esphome_overrides/ethernet/`)

A copy of the 2026.7.1 core component with **two** changes:

- **`ethernet_component_esp32.cpp`** — `spi_bus_initialize()` now treats `ESP_ERR_INVALID_STATE`
  as the success path. `spi:` (BUS 1000) brings the host up first with the correct pins; ethernet
  (WIFI 250) finds it already up, and `esp_eth_mac_new_w5500()` only needs `spi_bus_add_device()`
  onto it — which ESPHome's own `w5500_custom_spi.cpp` already does. Every other error stays
  fatal, and on an unshared bus the behaviour is byte-identical to upstream.
- **`__init__.py`** — `_final_validate_spi` no longer raises when `ethernet` and `spi` name the
  same interface; it logs at INFO instead. Sharing is now the intended configuration.

External components are inserted at `sys.meta_path` position 0, so this shadows the built-in.

### 2. Only touch builds take the fork

The `external_components` block lives in **`boards/t-connect-pro-display.yaml`**, not in the
ethernet board file. Screen-less Ethernet builds — `devices/climate-control.yaml` and
`devices/light-controller.yaml`, the ones that actually matter for control — keep the stock
upstream component and are wholly unaffected. Only a build that creates the sharing takes on the
fork.

### 3. Both controllers keep Ethernet

`devices/light-controller-touch.yaml` previously forced `enable_ethernet: false` purely to dodge
this bug. That override is removed: the lighting controller regains the wired networking ADR-0014
specified for its arbitration heartbeats. `devices/locals/climate-control-touch.yaml` now works
as originally intended.

### 4. The panel idles asleep

Both UI packages gain `on_idle` (5 min) → `lvgl.pause` + backlight off, waking on touch. A paused
LVGL renders nothing, so the display's share of the shared bus falls to **zero** whenever nobody
is using it — which, for a panel behind an enclosure door in the technical room, is essentially
always. Waking is safe because `Touchscreen::loop()` fires its own `on_touch` trigger
(`touchscreen.cpp:139`) before notifying LVGL's listener, so the screen cannot get stuck dark.

## Consequences

### Positive

- ADR-0014's two independent choices — this board, and Ethernet over WiFi — become compatible
  with the onboard panel instead of mutually exclusive.
- Both T-Connect Pros run the same arrangement, preserving the one-spares-shelf logic of ADR-0014.
- The climate commissioning UI survives, which matters for a season-phased rollout where the
  operator is standing at the manifold rather than at a laptop.
- `spi2` is the better bus regardless: GPIO11/12/13 are its native IO_MUX pads, so the panel gets
  direct routing rather than the GPIO matrix.

### Negative — the maintenance obligation

**This forks a core networking component and pins it to ESPHome 2026.7.1.** Every ESPHome upgrade
must re-verify the fork against the new upstream source, because upstream can change
`ethernet_component_esp32.cpp` or `_final_validate_spi` freely — they owe us nothing. Concretely,
on each upgrade: diff `esphome/components/ethernet/` against `libs/esphome_overrides/ethernet/`,
re-apply the two changes, and re-run the bring-up check below. This obligation belongs with the
toolchain-upgrade procedure, not in someone's memory.

### Known limits

- Verified for **W5500 only**. The fork's change is PHY-agnostic in principle, but DM9051 and
  ENC28J60 are untested here.
- The fork tolerates `ESP_ERR_INVALID_STATE` **unconditionally**. If some other component ever
  initialised that host with *different* pins, ethernet would silently proceed onto the wrong
  pads. Safe as configured — the display bus is the only other claimant and its pins match — but
  it is an unguarded assumption, tracked as open item 2.
- Display and ethernet now share bus bandwidth. Measured as a non-issue under a 30 fps
  full-screen redraw, and §4 takes the idle case to zero, but heavy continuous UI animation would
  couple the two.

## Alternatives considered

| Option | Why rejected |
|---|---|
| **WiFi + display** | Surrenders ADR-0014 §109's wired decision on both controllers. Tolerable for climate (control is autonomous; sensors are CAN-primary, so the network carries monitoring, the HA fallback tier, OTA and SNTP) but a real regression for the lighting controller's arbitration heartbeats. |
| **Ethernet + no display** | Keeps wired networking but makes `climate_touch_ui.yaml` and `light_touch_ui.yaml` dead code, and removes the on-device commissioning aid precisely when the season-phased rollout needs it. |
| **Move the display to other GPIOs** | Not possible — both peripherals are hardwired on the module. |
| **Upstream the change first, then adopt** | The related issue is closed as not planned and a maintainer is on record against it; waiting would block the rollout indefinitely. Proposing upstream remains worthwhile (open item 3) but must not gate deployment. |

## Verification

Performed on hardware 2026-07-26 with `devices/locals/t-connect-pro-debug-shared.yaml`, a
self-contained bring-up build carrying no repo packages so the composition layering was not a
variable. That file has since been deleted (see below); the experiment it ran is recorded here
because the record, not the file, is what the next person needs:

1. **Boot log** shows `SPI host 2 already initialized (shared with 'spi:'); adding W5500 as a
   device` — proof the shared path was taken rather than the old failure.
2. **Both peripherals live simultaneously**: the UI renders and its 1 s tick advances while the
   Ethernet IP and API state are displayed and updating.
3. **Stress**: continuous full-screen invalidation at ~30 fps with concurrent ping — no packet
   loss, no API disconnects, no W5500 timeouts.
4. **Touch**: the corner-tap test also established that the CST226SE and ST7796 do **not** share a
   coordinate system — touch needed both mirror flags inverted relative to the display's
   transform, now recorded in `boards/t-connect-pro-display.yaml`.

### The debug harness (removed 2026-07-26)

The four bring-up entry points — `t-connect-pro-debug-panel.yaml` (display + touch + a minimal
tick UI) and the three network variants below — were originally retained as the reproduction and
regression harness. They were deleted once the arrangement was proven on hardware and the climate
touch build gained its own liveness indicator, which makes it a better regression target: it
exercises the fork in the real composition rather than in isolation. The upgrade check in
`CLAUDE.md` now points there.

The three-way experiment is recorded here so a throwaway harness can be rebuilt from
`boards/t-connect-pro-display.yaml` if a future ESPHome bump breaks the shared bus and it needs to
be bisected away from the full climate config:

| Variant | `interface:` | Network | Expected result |
|---|---|---|---|
| `-debug.yaml` | `spi3` | Ethernet | **Fails** — two controllers on GPIO11/12/13; the W5500 (setup_priority WIFI 250) takes the pads from the display bus (BUS 1000) after the panel is already initialised, so the panel shows uninitialised GRAM forever while Ethernet works |
| `-debug-wifi.yaml` | `spi3` | WiFi | **Control** — WiFi touches none of those pads, so the panel renders; isolates pad contention from a bad panel config (mipi_spi geometry, `invert_colors`, the missing reset line) |
| `-debug-shared.yaml` | `spi2` | Ethernet | **The fix** — one controller, CS lines arbitrating; requires the fork |

Recovering the deleted files themselves is a `git show` away — they were removed in the commit
that reworked the climate touch UI.

## Open items

1. **Fold the fork's re-verification into the ESPHome upgrade procedure**, alongside the existing
   version pins in `climate/tests/pyproject.toml` and the board `min_version` floors.
2. **Harden the pin-mismatch assumption** — validate in Python that the referenced `spi:` bus's
   pins match ethernet's declared pins, instead of trusting them to agree.
3. **Propose the feature upstream**, behind an explicit `spi_id:` opt-in with pin validation and
   coverage for all three SPI PHYs, referencing esphome#9882 and this hardware evidence. If
   declined, publishing the fork as a public external component is a legitimate fallback that
   would serve the same users.
4. **Long-soak the shared bus** on the climate controller through commissioning, watching for
   ethernet stalls correlated with UI use.
