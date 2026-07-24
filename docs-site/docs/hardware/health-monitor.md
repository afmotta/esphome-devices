# Health Monitor Died

The health monitor is a dedicated device (a Waveshare ESP32-S3-RS485-CAN board) whose
only job is watching the CAN bus and reporting to Home Assistant which nodes are alive
or missing. It doesn't control anything — lights, relays, and climate all keep working
normally even if this device is completely dead. What you lose is *visibility*: you
stop getting "node lost" / "node recovered" notifications and the diagnostic counts
(Nodes Online/Total/Missing) go stale.

That said, this device is your early-warning system for every *other* failure in this
guide — fix it promptly even though nothing is on fire.

!!! warning "This is the one device without a same-model spare by default"
    Every other controller/relay/analog board in the house was deliberately
    standardized so one shelf of spares covers all of them. This device is the single
    documented exception — see the fallback procedure below.

## If you have a spare Waveshare ESP32-S3-RS485-CAN board

This is the straightforward case — same model, same pins, no changes needed.

1. Flash the standard config to the spare: `esphome compile devices/health-monitor.yaml`
   then `esphome upload devices/health-monitor.yaml` (it has WiFi/OTA, so once the
   original is provisioned you can normally update it over the air — an initial flash
   needs USB).
2. Make sure `devices/secrets.yaml`'s `health_monitor_encryption_key` is available to
   the build (this device has its own distinct encryption key, separate from the
   lighting controller's).
3. Swap the physical board and confirm it reconnects to Home Assistant and starts
   reporting node health again.

## If no Waveshare spare is available: fall back to a spare T-Connect Pro

Because the health-monitoring logic (`canbus/packages/health.yaml`) only needs a CAN
transceiver — no RS485, no relay bank — it can run on a spare T-Connect Pro controller
board instead, by changing two pin substitutions. `devices/health-monitor.yaml`
already declares its CAN pins as substitutions (`can_tx_pin: GPIO15`,
`can_rx_pin: GPIO16` — the Waveshare board's pins). A T-Connect Pro's CAN transceiver
sits on different pins (`GPIO6`/`GPIO7`, per this house's hardware standard).

1. Create a new device config that composes `boards/t-connect-pro.yaml` (or the
   Ethernet/WiFi variant you want) instead of `boards/waveshare-s3-rs485-can.yaml`,
   keeping everything else from `devices/health-monitor.yaml` the same
   (`canbus/packages/health.yaml`, the same includes, the same identity/OTA
   substitutions pattern).
2. Override the two CAN pin substitutions to the T-Connect Pro's values:
   `can_tx_pin: GPIO6`, `can_rx_pin: GPIO7`.
3. Compile, flash, and verify it starts reporting node health.

⚠️ **Known gap**: no such fallback config file exists yet in this repository as of
this writing — you'd be creating it fresh from the template above, not editing an
existing one. The pin-portability itself is documented and deliberate (ADR-0015), but
nobody has needed to actually build this fallback config yet, so treat the steps above
as a solid starting point, not a copy-paste-ready file.

## Related

- [Controller (T-Connect Pro)](controller.md) — if you're improvising the fallback
  above, this page covers the shared controller board in more depth.
- [Everyday Monitoring](../monitoring.md) — what the health monitor's diagnostic
  entities look like when things are healthy.
