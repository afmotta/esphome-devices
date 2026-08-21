---
adr: 0023
title: 'Standardize on the onboard-screen build; retire the screen-less and GitHub-remote controller variants'
status: 'Accepted'
date: '2026-08-21'
deciders: ['Alberto']
author: 'AI Assistant'
dependsOn:
  - 'ADR-0016: Shared SPI bus (the local ethernet fork; hardware-verified the screen build)'
  - 'ADR-0022: Merge Ethernet+WiFi (reduced shared_spi_pins to "is the display present")'
amends:
  - 'ADR-0016 §2 ("only touch builds take the fork") and §3: the display — and therefore the fork — is now standard on every build, not opt-in.'
relatedDocuments:
  - devices/climate-control.yaml
  - devices/light-controller.yaml
  - devices/locals/climate-control.yaml
  - boards/t-connect-pro.yaml
  - boards/t-connect-pro-display.yaml
---

# ADR-0023: The onboard screen is standard on every controller build

## Status

**Accepted** (2026-08-21). Config-validated with `esphome config` on both consolidated builds;
the ADR-0016 hardware bring-up check (Ethernet + panel under redraw load) still stands as the
runtime gate on the next flash. Follows ADR-0022 and the PR-review request to drop the
`shared_spi_pins` toggle.

## Context

ADR-0016 made the onboard ST7796 panel work by sharing one SPI controller between it and the W5500
Ethernet, via a local fork of ESPHome's `ethernet` component. It was verified on hardware and both
physical controllers (climate, lighting) carry the panel. But the panel was **opt-in**: a separate
`*-touch.yaml` build composed the display, while a plain screen-less build did not.

ADR-0022 (the 2026.8.0 Ethernet+WiFi merge) declared Ethernet unconditionally, which reduced the
`shared_spi_pins` substitution to a single meaning: *is the display present?* — `true` on a touch
build (display + W5500 co-claim GPIO12/11/13), `false` on a screen-less build (W5500 alone). A PR
reviewer asked to drop the toggle and just set `allow_other_uses: true`.

That is only valid if there is **no screen-less build**. ESPHome's pin validator
(`pins.py::PinRegistry.final_validate`) raises *"Pin N incorrectly sets allow_other_uses: true"*
when a pin is claimed exactly once with the flag set — which is what a screen-less build (Ethernet
pins, no display) would hit. Demonstrated directly: hardcoding `true` failed `esphome config` on
`devices/locals/climate-control.yaml` (screen-less) with that error on pins 12/11/13.

A related constraint sealed the direction: the screen build needs the local `ethernet` fork
(`external_components: type: local`), and the **GitHub-remote deployment**
(`devices/remotes/climate-control.yaml`, which pulled the config via ESPHome's `github://`
packages) **cannot fetch a `type: local` external component**. So the remote could only ever build
a screen-*less* config — a variant nothing physical needs, since every controller has a panel.

## Decision

**Make the onboard screen standard on every build, and delete the screen-less and GitHub-remote
variants.**

1. **Fold the display into the core entry points.** `devices/climate-control.yaml` and
   `devices/light-controller.yaml` now compose `boards/t-connect-pro-display.yaml` + their
   `*_touch_ui.yaml` package directly. The panel is part of every build.
2. **Delete the redundant variants**: `devices/locals/climate-control-touch.yaml`,
   `devices/light-controller-touch.yaml`, and `devices/remotes/climate-control.yaml`.
   `devices/locals/climate-control.yaml` (now the sole climate build) provides
   `esphome_overrides_path`; `devices/light-controller.yaml` (compiled directly) provides its own.
3. **Drop `shared_spi_pins`.** With no screen-less build left, the display's `spi:` bus always
   co-claims GPIO12/11/13 with the inline `ethernet:` block, so `allow_other_uses: true` is
   unconditionally correct in both `boards/t-connect-pro.yaml` and `boards/t-connect-pro-display.yaml`.
   The substitution is removed.
4. **Retire the GitHub-OTA path.** `devices/remotes/` is gone; the now-unused `github_username` /
   `github_pat` secrets are removed from the template and CI dummy secrets. Controllers are flashed
   / OTA-updated from a local ESPHome checkout (which they already required, for the fork).

## Consequences

### Positive
- One build per controller; four fewer entry-point files and the `shared_spi_pins` toggle gone.
- The PR-review simplification (`allow_other_uses: true`, no toggle) is now valid and applied.
- CI's `esphome compile devices/locals/climate-control.yaml` now exercises the fork + panel on the
  real config, instead of a screen-less variant — better coverage of the ADR-0016 arrangement.

### Negative / costs
- **No GitHub-pull OTA deployment.** It was never usable for the actual (screen) devices — the
  local fork can't travel through `github://` packages — so nothing deployable is lost, but the
  convenience of updating from GitHub without a local checkout is gone. Re-adding it would mean
  serving a screen-less firmware the physical controllers don't run.
- **A future screen-less T-Connect Pro would need the toggle back.** Unlikely (both controllers
  have panels); if one is ever built without a screen, re-introduce a per-pin `allow_other_uses`
  substitution rather than hardcoding.

## Alternatives considered

| Option | Why rejected |
|---|---|
| **Keep the GitHub remote as a screen-less fallback** | Forces `shared_spi_pins` to stay (the remote is a screen-less build), and serves no physical device — every controller has a panel. |
| **Reference the fork via `type: git` so the remote can carry it** | Breaks local development: `type: git` pulls the fork from GitHub, so you would test committed code, not your working tree. The `type: local` fork is deliberately for local iteration. |
| **Keep the `*-touch.yaml` variants, just delete the plain ones** | Leaves the screen build named `-touch` when it is now the only build; folding into the core is clearer and lets the board hardcode `allow_other_uses`. |

## Validation

`esphome config` passes on both consolidated builds (`devices/locals/climate-control.yaml`,
`devices/light-controller.yaml`); the climate run logs the fork's shared-SPI INFO line, confirming
the display pulls the fork in and `allow_other_uses: true` is accepted because the display co-claims
the pads. The inverse was demonstrated too: hardcoding `true` with no display present fails, which
is exactly why the screen-less variants had to be retired first.
