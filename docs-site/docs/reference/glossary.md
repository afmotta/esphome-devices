# Glossary (Italian Terms + Acronyms)

This house's automation was built for an Italian residence, so a lot of entity names,
room names, and file names use Italian words. Documentation and code comments are in
English, but you will constantly run into Italian terms in the actual system. This
page collects both that vocabulary and the technical acronyms/jargon used throughout
the site, each defined in one plain sentence.

## Italian terms

These words show up in room names, entity IDs (the names of sensors/switches in Home
Assistant), and file names throughout the repository.

| Italian | English | Context |
|---|---|---|
| soggiorno | living room | The most common zone name in the house. |
| cucina | kitchen | A room type. |
| bagno | bathroom | There are several; they're distinguished with an extra word (e.g. "Bagno Grande", "Bagno Padronale"). |
| camera | bedroom | Usually paired with a direction or descriptor (e.g. "Camera Nord" = north bedroom). |
| anticamera | entry hall / foyer | A ground-floor zone. |
| lavanderia | laundry room | A first-floor utility room. |
| sottotetto | attic | The only second-floor zone. |
| locale tecnico | technical room | The room that houses the heating/cooling equipment. |
| piano terra | ground floor | Building level 0. |
| primo piano | first floor | Building level 1. |
| secondo piano | second floor | Building level 2. |
| gruppo miscelazione | mixing valve group | A name used by the retired first-generation controller hardware; you may see it in old documentation, but it's not part of the current system. |
| distribuzione | distribution | Another retired first-generation naming pattern (for old slave boards); also not part of the current system. |
| radiante | radiant | Refers to radiant floor (or ceiling) heating/cooling — the water-based system embedded in the floor or ceiling rather than a fan-driven unit. |

## Acronyms and technical jargon

| Term | Plain-language definition |
|---|---|
| **ADR** (Architecture Decision Record) | A written record of a significant design decision and the reasoning behind it — used here to document things like "which controller hardware to use" so the reasoning isn't lost later. |
| **PID** (Proportional-Integral-Derivative) | A control algorithm that smoothly drives a temperature toward its target by constantly adjusting output based on how far off, how long it's been off, and how fast it's changing — the standard way this system runs both radiant floor and fancoil heating/cooling. |
| **MEV** (Mechanical Extract Ventilation) | The house's ventilation system — it pulls stale/humid air out and helps control indoor air quality and humidity; called "VMC" in Italian documentation and product manuals. |
| **RS485** | A type of wired electrical connection (two wires, "A" and "B") used to link the controller to relay boards, analog output boards, and the ventilation unit. It's the physical wire; Modbus (below) is the language spoken over it. |
| **CAN** (Controller Area Network) / **CAN bus** | A different wired network, separate from RS485, used to connect wall-mounted buttons and room sensor boards back to the controllers. Originally developed for cars; well suited to a house because a break or fault in one section doesn't necessarily take down the whole network. |
| **HA** (Home Assistant) | The open-source home automation software this system integrates with for monitoring, dashboards, and manual overrides. The house's core climate and lighting control keeps working even if HA is offline — HA adds visibility and convenience on top. |
| **OTA** (Over-The-Air update) | Updating a device's firmware over the network (WiFi/Ethernet) instead of plugging in a USB cable. Most controllers in this house support it; the small CAN bus wall-button boards deliberately do not (see the node entry below). |
| **`node_id`** | The unique number identifying one CAN bus board (a wall button or sensor board) in the system-of-record file `registry/nodes.csv`. A physical board has no identity of its own — it becomes whichever `node_id` it was most recently flashed with. |
| **Modbus** (specifically Modbus RTU) | A messaging format spoken over an RS485 wire — it defines how the controller asks a relay board "turn on channel 5" or asks the ventilation unit "what's your current fan speed," and how those devices reply. |
| **Coil** / **register** (Modbus terms) | Two kinds of "memory slots" a Modbus device exposes. A **coil** is a single on/off value (used for relay channels — on or off). A **register** holds a numeric value (used, for example, for a 0–10V analog output level or a temperature reading). |
| **Failover tier** | This system reads some sensor values from more than one source, in a priority order: try the primary source first, fall back to a secondary source if the primary is unavailable, and fall back to a safe "emergency" state if both are unavailable. Each of those sources is a "tier." See the [Confidence Ledger](confidence-ledger.md) for a known gap in how the emergency tier currently behaves. |
| **Commissioning** | The process of bringing a new or replaced piece of hardware fully into service — assigning it an identity, verifying it reports correctly, and (for climate zones) gradually proving the control loop is safe before trusting it unattended. See [Routine Maintenance](../maintenance-tasks.md) for the step-by-step versions of this. |
| **Pre-live** | This project's term for "designed and largely built, but not yet physically installed in the house." Almost everything in this documentation is pre-live, which is why so many claims are tagged 🔵 DESIGNED rather than 🟢 VERIFIED — see the [Confidence Ledger](confidence-ledger.md). |

## Related

- [Hardware & Address Table](hardware-table.md) — where several of these terms (relay,
  coil, register, Modbus address) are used in a concrete table.
- [Confidence Ledger](confidence-ledger.md) — explains the 🟢/🔵/⚠️ tags used
  throughout this site.
- [Document Map](doc-map.md) — if a term here points you to a file in the repository
  and you're not sure which document is current versus historical.
