---
adr: 0022
title: 'Merge Ethernet and WiFi into one config per board using ESPHome 2026.8.0 multi-interface networking'
status: 'Accepted'
date: '2026-08-20'
deciders: ['Alberto']
author: 'AI Assistant'
dependsOn:
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (chose the T-Connect Pro and, §109, Ethernet over WiFi for the controllers)'
  - 'ADR-0016: Shared SPI bus (the local ethernet fork; its 2026.8.0 rebase is what lets the touch builds declare both interfaces)'
amends:
  - 'ADR-0016 §3: that ADR removed light-controller-touch''s forced `enable_ethernet: false`; this ADR removes the `enable_ethernet` toggle itself.'
relatedDocuments:
  - boards/t-connect-pro.yaml
  - boards/an-penta-plus.yaml
  - boards/t-connect-pro-display.yaml
  - libs/esphome_overrides/ethernet/
  - devices/climate-control.yaml
  - devices/light-controller.yaml
  - devices/an-penta-1.yaml
---

# ADR-0022: Merge Ethernet and WiFi into one config per board (multi-interface networking)

## Status

**Accepted** (2026-08-20), as part of the ESPHome 2026.8.0 upgrade. Structural change only —
**not yet hardware-verified** (the pre-live controllers are not deployed, and the environment this
was authored in has no ESPHome CLI). The ADR-0016 hardware bring-up check on the shared-SPI touch
build still owes its runtime confirmation on the next flash; see Consequences → Verification debt.

## Context

Every T-Connect Pro and An-Penta-Plus board could run **either** Ethernet **or** WiFi, chosen at
**compile time**. The mechanism (pre-2026.8.0) was:

- two sibling packages per board — `<board>-ethernet.yaml` and `<board>-wifi.yaml`, mutually
  exclusive because ESPHome's `ethernet` and `wifi` components declared `CONFLICTS_WITH` each other;
- an `enable_ethernet` substitution and a `packages: network_package: ${ethernet_package if
  enable_ethernet else wifi_package}` selector in the board file;
- the toggle threaded down through every entry point (`vars: enable_ethernet: ${enable_ethernet}`),
  plus a whole `devices/locals/climate-control-touch-wifi.yaml` variant whose only reason to exist
  was to flip that toggle for the touch panel.

This was pure ceremony for a choice that hardware makes for us: a controller either has a cable
plugged in or it does not. It also could not fail over — an unplugged Ethernet cable meant the
device was simply off the network until reflashed.

ESPHome **2026.8.0 adds multi-interface networking**: `ethernet:` and `wifi:` may be declared in
the same YAML, and a new `network: priority:` list names the preferred interface. The default route
is arbitrated at runtime with automatic failover. Upstream dropped the ethernet↔wifi
`CONFLICTS_WITH` and added a validation requiring both interfaces to appear under `network:
priority:` when both are declared.

## Decision

**Declare both interfaces inline in each dual-network board file and let `network: priority:` pick
the active one at runtime.** Concretely:

1. **`boards/t-connect-pro.yaml`** and **`boards/an-penta-plus.yaml`** now contain the `ethernet:`
   and `wifi:` blocks directly, plus `network: priority: [ethernet, wifi]` (Ethernet preferred —
   preserving ADR-0014 §109 — with WiFi as the automatic fallback).
2. **Deleted**: `t-connect-pro-ethernet.yaml`, `t-connect-pro-wifi.yaml`,
   `an-penta-plus-ethernet.yaml`, `an-penta-plus-wifi.yaml`, the `enable_ethernet` /
   `network_package` machinery, and the now-redundant `devices/locals/climate-control-touch-wifi.yaml`
   (the base touch build already provides WiFi as a runtime fallback).
3. **Per-interface diagnostics coexist**: both `ethernet_info` and `wifi_info` text sensors are
   declared; only the top-level IP-address names are qualified (`… - Ethernet IP Address` /
   `… - Wi-Fi IP Address`) so the two do not collide on one entity name.
4. **The shared-SPI touch build is unchanged in spirit** (ADR-0016): `shared_spi_pins` still gates
   `allow_other_uses` on GPIO12/11/13. Because Ethernet is now *always* declared on the T-Connect
   Pro, `shared_spi_pins` reduces to "is the display present" — true on a touch build (display +
   W5500 co-claim the pads), false on a screen-less build (W5500 owns them). The 2026.8.0 rebase of
   the ethernet fork (ADR-0016) carries upstream's multi-interface support, so the forked component
   accepts the ethernet+wifi coexistence exactly as the stock component does.

Boards with only one interface are untouched: the health monitor (Waveshare ESP32-S3-RS485-CAN) and
the An-Quad (no Ethernet PHY) keep their single inline `wifi:` and need no `network:` block.

## Consequences

### Positive

- **Runtime failover**: an unplugged cable no longer strands a controller — it drops to WiFi within
  milliseconds and recovers when the cable returns. Pure upside for the wired-primary controllers.
- **Less ceremony**: four board files, one locals variant, one substitution, and the
  `network_package` indirection all deleted; no toggle to thread through entry points.
- **One image per board** instead of an Ethernet build and a WiFi build.

### Negative / costs

- **Both network stacks run at once.** Fine on the ESP32-S3 T-Connect Pro (8 MB PSRAM). On the
  classic-ESP32 An-Penta it costs RAM; the board file documents the `enable_on_boot: false` escape
  hatch (start WiFi from an action on Ethernet loss) if bring-up shows memory pressure, trading
  automatic failover for a smaller boot footprint.
- **WiFi credentials are now required on the wired-primary controllers**: the inline `wifi:` block
  references `!secret wifi_ssid` / `!secret wifi_password`, so `light-controller` and `an-penta-1`
  (compiled directly) now need them. They were already in `secrets.yaml` (climate used them) and in
  CI's dummy-secrets, so nothing broke, but `secrets.yaml.example` now says so explicitly.
- **No more pure-WiFi (no-W5500) touch build.** The deleted `climate-control-touch-wifi.yaml` let
  you build the panel with Ethernet compiled *out*, sidestepping the ADR-0016 shared-SPI fork
  entirely. With Ethernet always declared, every touch build runs the W5500 on the shared bus. This
  is acceptable because that shared-bus arrangement is already the primary, hardware-verified touch
  configuration (ADR-0016); the WiFi-only build was only ever a fork-avoidance convenience.

### Verification debt

Not hardware-verified here. Two things need confirming on the next real flash:
1. The ADR-0016 shared-SPI bring-up check on `devices/locals/climate-control-touch.yaml` under
   2026.8.0 (boot log shows the shared-host line; liveness dot pulses; API stays up under redraw).
2. That both interfaces enumerate and the `network: priority:` default route + failover behave as
   documented, on at least one dual-network board.

## Alternatives considered

| Option | Why rejected |
|---|---|
| **Keep the `enable_ethernet` toggle + separate packages** | The thing the request asked to remove; keeps compile-time-only selection and no failover. |
| **Merge but keep both `enable_on_boot: false` by default** | Defeats automatic failover for a memory saving that only the classic-ESP32 An-Penta might need; left as a documented escape hatch instead. |
| **WiFi-primary on the An-Penta** (`priority: [wifi, ethernet]`) | The board's deployed default was `enable_ethernet: true`; preserving Ethernet-primary is the behaviour-preserving choice. Reorder the list if the deployment wants otherwise. |
| **Keep `climate-control-touch-wifi.yaml`** | After the merge it is identical to the base touch build (both interfaces, Ethernet preferred); it can no longer express "Ethernet compiled out" without re-introducing the toggle. |

## Open items

1. **Hardware-verify** both points under Verification debt on the first 2026.8.0 flash of a touch
   controller.
2. **Watch An-Penta RAM** at bring-up; apply the `enable_on_boot: false` escape hatch if the dual
   stack is tight.
