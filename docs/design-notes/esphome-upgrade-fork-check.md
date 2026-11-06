# Upgrading ESPHome — required fork check

`libs/esphome_overrides/ethernet/` is a **local fork of a core ESPHome component**, rebased onto the
repo's pinned ESPHome (currently 2026.8.0) and carrying two changes that let the W5500 share an SPI
controller with the onboard display (ADR-0016). Upstream owes it no compatibility, so **every
ESPHome version bump must**:

1. Diff the new upstream `esphome/components/ethernet/` against `libs/esphome_overrides/ethernet/`
   and re-apply the two changes (tolerate `ESP_ERR_INVALID_STATE` in
   `ethernet_component_esp32.cpp`; downgrade `_final_validate_spi`'s same-interface error in
   `__init__.py`). Both are marked `LOCAL FORK (esphome-devices)` in the source. Take everything
   else from the new upstream — the 2026.8.0 rebase, for instance, adopted upstream's multi-interface
   support (dropped ethernet↔wifi `CONFLICTS_WITH`, added the `network: priority:` coexistence
   validation), which ADR-0022's inline Ethernet+WiFi merge depends on.
2. Re-run the bring-up check by flashing `devices/locals/climate-control.yaml` — the Ethernet +
   panel build (the panel is standard on every build now, ADR-0023) is itself the regression
   harness, since it exercises the shared bus in exactly the arrangement the fork enables. Confirm
   all three:
   - the boot log shows `SPI host 2 already initialized (shared with 'spi:')` — proof the shared
     path was taken rather than the old two-controller failure;
   - the status strip's liveness dot keeps pulsing, i.e. the display is still being flushed (a
     frozen dot is the "panel died" signal the old debug build's tick counter provided);
   - the dot stays green, i.e. the API — and therefore Ethernet — survived alongside it.

   Under load: switch tabs repeatedly (each is a full-screen repaint) while pinging the device.
   The fork's risk is the display holding the SPI bus long enough to stall the W5500, so packet
   loss or API drops during redraws is the failure to watch for.

Skipping this does not fail the build — it fails the *panel*, silently, at runtime.

The dedicated `t-connect-pro-debug*.yaml` bring-up harness that originally proved this was removed
on 2026-07-26 (its diagnosis is preserved in ADR-0016 and in the comments in
`boards/t-connect-pro-display.yaml`). If a future upgrade breaks the shared bus and you need to
bisect it away from the full climate config, ADR-0016 §Verification describes the three-way
experiment — spi3+Ethernet (fails), spi3+WiFi (control), spi2+Ethernet (fix) — well enough to
rebuild a throwaway harness from the board file.
