# Everyday Monitoring

This page explains what "healthy" looks like for this house's electronics, day to day, so you can catch a developing problem before it turns into a dead device. It also covers the basics of reading a device's logs when something looks off.

If you don't know what a term below means, check the [Glossary](reference/glossary.md). If something here points you at a hardware problem, the relevant page is [Hardware Died](hardware/index.md); for something that's misbehaving but not obviously broken hardware, see [Troubleshooting](troubleshooting/canbus.md).

!!! note "Confidence tags"
    This page uses 🟢 VERIFIED / 🔵 DESIGNED / ⚠️ KNOWN GAP tags, explained on the [Home](index.md) page. Almost everything below is 🔵 — designed and implemented, but this system is pre-live, so none of it has yet been watched operating through a real years-long stretch of house life.

## CAN bus health

The CAN bus is the shared pair of wires that wall buttons and room sensors use to talk to the rest of the house. A dedicated device (the **CAN bus health monitor**) watches every device on that bus and reports when one goes quiet.

🔵 **How "lost" is defined:** every device on the bus sends a heartbeat (a small "I'm still here" signal) every 30 seconds. If the health monitor misses **3 heartbeats in a row** from the same device — 90 seconds of silence — it declares that device **lost**.

When a device's status changes, the health monitor sends an event to Home Assistant (the home-automation software). The events to know:

| Event | Meaning |
|---|---|
| `esphome.canbus_node_lost` | A device just went silent (3 missed heartbeats). |
| `esphome.canbus_node_recovered` | A previously-lost device is back and sending heartbeats again. |
| `esphome.canbus_node_error` | A device reported a change in its own internal error state. |
| `esphome.canbus_node_unknown` | The health monitor heard from a device it doesn't recognize (not in the house's registry). |

Alongside those events, the health monitor also publishes a handful of always-on diagnostic entities in Home Assistant, refreshed every 5 seconds so they survive even a brief disconnect from Home Assistant itself:

- **Nodes Online** — how many devices are currently heard from.
- **Nodes Total** — how many devices are expected to exist, based on the house's registry.
- **Nodes Missing** — names of the devices that are expected but not currently heard from.
- **Fallback Events** — a running count of times the lighting system had to fall back to its own local logic because Home Assistant wasn't ready to respond in time. A rising count on an otherwise-quiet night is worth a look.
- **HA Ready** — whether Home Assistant is currently considered ready to receive events.

**What to do if "Nodes Missing" is not empty:** that means a specific physical device — a wall button, a room sensor, or similar — has stopped reporting in for at least 90 seconds. Note which device it names, then go to [CAN Node](hardware/can-node.md) for the physical troubleshooting steps. Don't panic on a single, brief blip — but a device that stays on the "Missing" list for more than a few minutes needs a physical check.

## Climate sensor failover tiers

Each room's climate control doesn't read a single sensor directly — it reads an "abstracted" (combined, best-available) temperature and humidity value that can silently fall back between up to three data sources. This is deliberate: a bad CAN sensor shouldn't be able to stop a room's heating or cooling outright.

The three tiers, in priority order:

1. **Primary (labeled "CAN")** — the room's own CAN bus sensor kit, read directly by the climate controller.
2. **Secondary (labeled "HA")** — a fallback reading pulled from Home Assistant instead, used only when the CAN reading is unavailable.
3. **Emergency** — no valid reading from either source. The abstracted value becomes invalid (mathematically "NaN," not-a-number) the moment both sources fail — 🔵 there is no built-in delay in this component before that happens.

    !!! warning "Known gap: the '5-minute' number"
        You may see other project documentation describe the Emergency tier as triggering "a safe shutdown after 5 minutes." ⚠️ That specific number does not appear in this failover component's own code — it returns an invalid reading immediately, with no delay coded here. If a 5-minute grace period exists anywhere before some larger safety action fires, it must live in a different part of the system; treat that number as unverified until confirmed. Don't assume it protects you.

Each room exposes a diagnostic **"Active Sensor Tier"** text entity in Home Assistant reporting which tier is currently supplying its data, following the pattern `{room}_temp_abstracted_sensor_tier` (for example, `soggiorno_temp_abstracted_sensor_tier` for the living room). There's a matching one for humidity.

**What to do based on what you see:**

- **Stuck on "HA" for a long time** — the room's CAN sensor has likely stopped reporting. The room is still being controlled (using the Home Assistant fallback reading), so this isn't an emergency, but it should be looked at soon. See [Climate Troubleshooting](troubleshooting/climate.md) and, if it turns out to be the physical sensor, [CAN Node](hardware/can-node.md).
- **Shows "Emergency"** — neither data source is working for that room. Escalate immediately; that room's climate control has no valid temperature data to act on. Start at [Climate Troubleshooting](troubleshooting/climate.md).

## Lighting: the binding manifest hash

The mapping from "which button press does what" (which relay/light it controls) lives in the house's registry, in git, and gets compiled into the lighting controller's firmware as a "binding manifest." Two related diagnostic values exist to sanity-check that the compiled firmware actually matches what's currently committed:

- **Binding Manifest Hash** — a short fingerprint of the binding rules baked into the running firmware.
- **Node Map Version** — a version marker for the device/room map baked into the running firmware.

🔵 If either of these doesn't match what's currently committed in the registry (`registry/map.json` / `registry/bindings.yaml`), it means: **"the mapping has been changed and committed, but that device hasn't been reflashed with the new firmware yet."** This is a completely normal, expected state during active development — it is not, by itself, a fault. It only becomes a problem if it persists after you believed a reflash had already happened, in which case the reflash itself is worth double-checking.

## Routine check cadence

A simple rhythm for keeping an eye on things without obsessing over them:

- **Weekly** — skim the Home Assistant diagnostic entities described above for anything that looks unusual: nonzero "Nodes Missing," a rising "Fallback Events" count, or any room stuck off "CAN"/"Primary" tier.
- **Monthly** — check that every room's sensor tier is back on its Primary ("CAN") tier. A room quietly living on its Secondary tier for a month is easy to miss if you only glance at "is it Emergency or not."
- **Quarterly / at each season change** — review that `hp_mode` (the heat-pump/season mode selector) and the ventilation (MEV) settings actually match the season you're now in. This system's heating/cooling source produces either hot or cold water house-wide with no automatic changeover, so a stale seasonal setting after the season has actually turned is a realistic way to end up heating when you meant to cool, or vice versa.

## Reading the logs

For live troubleshooting, the main tool is streaming a device's logs to your terminal:

```
esphome logs <entry-point-file.yaml>
```

For example, `esphome logs devices/locals/climate-control.yaml` for the climate controller, or `esphome logs devices/light-controller.yaml` for the lighting controller. (See [Getting Started](setup.md) if you don't yet have a working ESPHome install to run this command.)

### Turning on verbose Modbus logging

Modbus is the wired protocol the climate controller uses to talk to the relay and analog-output boards. If you suspect a Modbus communication problem (see [RS485 / Modbus Troubleshooting](troubleshooting/rs485-modbus.md)), you can get much more detailed logs by adding this to the device's configuration before compiling and flashing:

```yaml
logger:
  level: DEBUG
  logs:
    modbus_controller: DEBUG
    modbus: DEBUG
```

This is a temporary diagnostic setting — turn it back off (or don't commit it) once you're done, since verbose logging is noisier and not meant for everyday production use.

### Reading failover log lines

🟢 The exact wording below is taken directly from the failover component's own source code (`climate/packages/components/failover_sensor.yaml`), not guessed:

- Falling from the Primary tier to the Secondary tier logs at **INFO** level: `Failover: <from tier> → <to tier> (primary sensor unavailable)`.
- Falling to the Emergency tier — from either Primary or Secondary — logs at **ERROR** level: `Failover: <from tier> → <to tier> (all sensors unavailable)`.
- Recovering back up a tier (Secondary → Primary, Emergency → Primary, or Emergency → Secondary) logs at **INFO** level, with the word `Recovery` in place of `Failover`.

So in this component specifically, only the drop into Emergency is logged as an error; the drop from Primary to Secondary is informational, not a warning. If you're grepping logs for trouble, search for `"failover"` (the log tag used) and look at the word right after the room name — `Failover` versus `Recovery` tells you the direction immediately.

## Where to go next

- Room stuck on a fallback tier or in Emergency? [Climate Troubleshooting](troubleshooting/climate.md)
- A device is missing from the CAN bus? [CAN Node](hardware/can-node.md)
- Something is actually dead? [Hardware Died](hardware/index.md)
- Scheduled check-up rather than reacting to an alert? [Routine Maintenance](maintenance-tasks.md)
