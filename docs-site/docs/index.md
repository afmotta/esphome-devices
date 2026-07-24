# Home

If you scanned a QR code stuck to a piece of hardware, you almost certainly want **[Hardware Died](hardware/index.md)**, not this page. That section is a decision tree: pick the device that failed and it tells you what to do. Come back here later if you want the bigger picture.

Otherwise — welcome. This is the maintenance and support guide for the house's electronics: three systems that share wiring, hardware, and a common set of rules. Read this page once, in about five minutes, and you'll know enough to find your way around the rest of the guide.

## The three systems, in one sentence each

- **`canbus`** — a wiring bus (CAN bus) that lets wall buttons and room sensors talk to the rest of the house over a pair of shared wires, plus a "health monitor" device that watches for anything that's gone quiet.
- **`lighting`** — listens for button presses coming over the CAN bus and turns them into light switching, through a relay board.
- **`climate`** — runs heating, cooling, and ventilation for 13 rooms across 3 floors: it reads room temperature/humidity (arriving over the CAN bus), decides what each room needs, and drives pumps, valves, and fans through Modbus-controlled relay and analog-output boards.

Each system has its own, more detailed guide pages under **Troubleshooting** and **Hardware Died**. This page is only the map.

!!! note "This system is not live yet"
    As of today, this house's electronics are **pre-live**: the design is finished and the firmware exists, but the hardware has not all been physically installed and exercised for years the way a lived-in house would. That matters for you as a reader, because almost nothing in this guide has been proven against a real, multi-year failure yet — most of it is "built as intended, never yet tested by time." That is exactly why every procedure in this guide is tagged with a confidence level. Don't assume a 🔵 tag means "wrong" — it means "not proven wrong or right yet, so double-check before you trust it blindly."

## How to read the confidence tags

Every procedure, timing number, or hard technical claim in this guide carries one of three tags:

| Tag | Meaning |
|---|---|
| 🟢 **VERIFIED** | Confirmed on a real bench or in the field. You can trust this. |
| 🔵 **DESIGNED** | Built and intended to work this way, but not yet exercised against a real failure or field condition. This is the honest state of almost everything in a pre-live system — treat it as "probably right, watch for surprises." |
| ⚠️ **KNOWN GAP** | The repository this guide is generated from explicitly does not have an answer here. We say so plainly instead of guessing. If you hit one of these, you're on your own for now — consider writing down what you learn so the gap can be closed. |

You'll see these tags throughout the site, including on the [Confidence Ledger](reference/confidence-ledger.md), which lists every known gap in one place.

## The one rule that matters most

🟢 **All button-to-room, sensor-to-room, and light-to-switch mappings for this house live in one place: a folder called `registry/` inside the project's git repository (its source-code version control). Git is the *only* backup of that data.**

Concretely, before you re-flash (re-program) any device whose firmware is built from that registry data — the lighting controller, the CAN bus health monitor, or the climate controller — you (or whoever is doing the technical work) must run:

```
python3 canbus/tools/check_registry_pushed.py
```

This is a mechanical check, not a suggestion: it looks at the git repository and refuses to say "safe" unless every change is both committed *and* pushed to a remote server (like GitHub), which is what makes it an actual backup rather than a file sitting only on one laptop. It exits with code `0` if it's safe to proceed, `1` if the check failed, or `2` if something went wrong reading git itself.

Why this matters so much: this project's own documentation describes reflashing a device with unpushed registry changes as **"an unbacked-up house."** If that device's memory is ever wiped — a bad flash, a dead board, a mistake — and the only record of which button controls which light, or which sensor belongs to which room, existed solely on one laptop's disk, that information is gone. Every wall button and room sensor mapping would have to be rediscovered by hand, room by room. Running the check above takes a few seconds and prevents that entirely.

If you are a technician who doesn't normally touch git: this is the one thing to insist on before you let anyone reflash a device after making a mapping change. If in doubt, ask whoever manages this repository to confirm the check passed before you proceed.

## The physical shelf of spares

This house deliberately reuses the same handful of hardware models across both the climate and lighting systems, specifically so that most failures become "swap the board for an identical spare and reflash it," not "redesign something." Keeping one shelf stocked with these covers nearly the whole house.

| Device | Model | Used for | Spare story |
|---|---|---|---|
| Controller | LilyGO T-Connect Pro (ESP32-S3, with Ethernet, RS485, and CAN bus built in) | **Both** the climate controller (`devices/climate-control.yaml`) and the lighting controller (`devices/light-controller.yaml`) | 🔵 One spare board covers either role — it's the firmware you flash onto it that decides which job it does. |
| Relay board | Waveshare Modbus RTU Relay 32CH (address `0x2`) | Switching zone pumps/valves (climate) and light circuits (lighting) | 🔵 The address is deliberately mirrored on both systems' RS485 wiring, so a spare relay board works in either system, unmodified. |
| Analog output board | Waveshare Modbus RTU Analog Output 8CH (B) (address `0x1`) | Fancoil fan speed and mixing-valve modulation (0–10V outputs) | 🔵 Climate system only — no lighting counterpart. |
| CAN bus health monitor | Waveshare ESP32-S3-RS485-CAN (WiFi-only) | Watches the CAN bus and reports which devices have gone quiet | ⚠️ **Known gap**: this is currently the one device in the house with no "identical spare on the shelf" plan by default — see the [Confidence Ledger](reference/confidence-ledger.md). Its logic can, if needed, be moved onto a spare T-Connect Pro instead, since the two boards share compatible wiring. |
| CAN bus segment bridge | LilyGO T-2CAN | Joins separate sections of the CAN bus wiring together | 🔵 Deliberately has no WiFi and no over-the-air update capability — it can only be reprogrammed over a USB cable, by design, for reliability. |
| Room sensor (advanced) | S1-Pro Multi-Sense | Room temperature/humidity/air-quality plus radar-based presence sensing | 🔵 |
| Room sensor (simple) | Wall-mounted sensor board | Room temperature/humidity/air-quality only, no radar | 🔵 |

The full detail — exact addresses, which entry-point file matches which device, and part numbers — lives on the [Hardware & Address Table](reference/hardware-table.md) reference page. If a device in front of you has actually failed, go to [Hardware Died](hardware/index.md) instead of trying to work it out from this table.

## Where to go next

- **First time setting up a computer to work on this repository?** Start at [Getting Started](setup.md).
- **Want to know what "healthy" looks like day to day, or how to read the logs?** Go to [Everyday Monitoring](monitoring.md).
- **Something's misbehaving but nothing looks physically dead?** Check [Troubleshooting](troubleshooting/canbus.md) first.
- **A physical device has actually died?** Go straight to [Hardware Died](hardware/index.md).
- **Doing a scheduled check-up, not reacting to a problem?** See [Routine Maintenance](maintenance-tasks.md).
- **Need a term defined, or want to know which document is authoritative for a given fact?** See the [Glossary](reference/glossary.md) and [Document Map](reference/doc-map.md).
