# Heat Pump Integration — Stiebel Eltron HPA-O (CLIMATE C7 investigation)

| Field | Value |
|---|---|
| **Status** | **Decided 2026-07-15: ISG web (Alberto)** — installer remote monitoring/assistance is the deciding factor; ISG takes precedence over any conflicting recommendation below. DIY CAN tap dropped. SG Ready remains a separate open decision (no conflict with the ISG). |
| **Date** | 2026-07-15 |
| **Candidate units** | Stiebel Eltron **HPA-O 07.2 Plus HC 230** or **HPA-O 07.1 CS Premium** |
| **Related** | TODO.md "heat pump temperature management"; C3 weather compensation (`climate/packages/coordinators/weather_compensation.yaml`); ADR-0014 hardware family; parked physical/electrical topology ADR |

## Findings

Both candidates are WPM-managed air/water monoblocks from the same controls
ecosystem, so **the model choice does not change the integration architecture**
— everything below applies to either. Verify at purchase: SG Ready terminals
on the WPM and the WPM CAN service connector (both are standard on this
series; confirm in the installation manual of the exact unit).

Neither unit speaks Modbus RTU natively, so the original idea of "hang the HP
off the controller's `rs485_bus`" is **out**. The three real interfaces:

### 1. SG Ready dry contacts — the autonomous control tier

Two dry-contact inputs on the WPM give four operating states:

| SG2 | SG1 | State |
|---|---|---|
| 0 | 1 | 1 — utility lock (EVU block, off) |
| 0 | 0 | 2 — normal operation |
| 1 | 0 | 3 — recommended-on (raised setpoints / eco surplus) |
| 1 | 1 | 4 — forced-on (max boost within limits) |

This maps perfectly onto the existing architecture: the climate controller is
already the Modbus master of a 32-channel relay bank with **relay_18–21 freed**
by the Epic 18 MEV migration (see `climate/CLAUDE.md` Appendix B). Two relays
wired to SG1/SG2 give the controller **fully autonomous, protocol-free,
warranty-neutral demand steering** — no HA, no gateway, no CAN tap in the
loop. It is also the natural actuator for the future energy items (C6
metering, PV-surplus boost from TODO.md).

Cost: two relay channels + a twisted pair to the WPM. Decide the channel
assignment in the topology ADR; relay_18/relay_19 are the obvious candidates.

### 2. WPM CAN bus tap (Elster/Kromschröder protocol) — the telemetry tier, DIY

The WPM's service CAN carries everything (flow/return temps, DHW, compressor
state, energy counters, setpoints — readable and largely writable):

- Protocol: Elster/Kromschröder frames; WPM listens on CAN ID `0x180`,
  the tap should present itself as `0x680`. Values are scaled ints (÷10 for
  temperatures, e.g. flow temp index `0x0016`, DHW `0x0012`).
- Community ESPHome support exists (e.g.
  `roberreiter/StiebelEltron-heatpump-over-esphome-can-bus`) with ready YAML +
  decoding headers — no from-scratch protocol work.
- Multi-master bus: a tap coexists with an ISG if one is added later.
  **Do not enable the 120 Ω termination on the tap.**
- Cost: <€20 in parts; caveat: unsupported by Stiebel, potential warranty
  argument, and write operations should be treated with the same caution as
  any reverse-engineered interface.

**Hardware fit:** this must be a **dedicated device**, not the climate
controller — the ESP32-S3 has a single TWAI controller and the climate
controller's CAN is already bound to the 125 kbps house sensor bus; the WPM
bus is a different, incompatible bus (different speed, different protocol).
The standardized **Waveshare ESP32-S3-RS485-CAN** (the health-monitor board,
already on the spares shelf per ADR-0014) is exactly right: isolated CAN,
WiFi, ESPHome. A third instance of the family → `devices/hp-gateway.yaml`.

**Hard rule if built:** the WPM bus is never bridged onto the house CAN bus.
The HP gateway exposes entities via the HA native API only (plus optional
local web server for HA-down inspection). House-canbus frame IDs/protocol are
untouched — this is a separate transport with its own CLAUDE.md-level
boundary if it becomes a system.

### 3. ISG web (Modbus TCP) — the official route, optional

~€500+, plug-and-play, warranty-clean, and Home Assistant has a native
`stiebel_eltron` integration over it. Two architectural caveats:

- ESPHome has **no Modbus TCP client**, so the ISG can only ever feed the
  **HA tier** — the climate controller cannot consume it directly. Anything
  ISG-sourced dies with HA (acceptable for telemetry, not for control).
- It is therefore *redundant* with the CAN tap for telemetry, and inferior to
  SG Ready for autonomous control. Its real value is vendor support/service
  diagnostics and warranty peace of mind.

## Decision (2026-07-15)

**ISG web is the chosen telemetry/service interface.** The deciding factor is
that it lets the installer monitor the HP remotely and offer assistance —
value the DIY tap cannot provide. Where the analysis above conflicts with the
ISG, the ISG wins:

- **DIY WPM CAN tap: dropped.** Redundant for telemetry once the ISG is in,
  and it would muddy the installer's supported setup. No `devices/hp-gateway.yaml`,
  no extra Waveshare board.
- **Telemetry path:** ISG → Modbus TCP → Home Assistant's native
  `stiebel_eltron` integration → HA tier. Accepted consequence: HP telemetry
  and any HP parameter writes are **HA-tier only** (ESPHome has no Modbus TCP
  client, so the climate controller never consumes the ISG directly). The
  house's autonomy doctrine is unaffected — nothing implemented depends on HP
  telemetry; the controller's actuation (valves, pumps, fancoils, MEV) runs
  regardless.
- **Bonus for C3:** the WPM's own outdoor sensor is exposed through the ISG,
  so the HA fallback tier of `climate/outdoor.yaml` can point at it (override
  `ha_outdoor_temperature_sensor_id` with the `stiebel_eltron` outdoor-temp
  entity) instead of, or in addition to, an OpenWeather entity. The dedicated
  outdoor CAN node remains the autonomous Tier 1.

**SG Ready: still recommended, still open.** It does not conflict with the
ISG — it is an official WPM feature and the two coexist by design. It remains
the *only* HA-independent control path (two spare relay channels, relay_18/19
candidates → four HP states) and the natural actuator for the backlogged
energy items (C6, PV-surplus). Decide at install time in the topology ADR.

Division of labour stands: the WPM runs its own weather-compensated curve for
the HP outgoing temperature (own outdoor sensor); the repo's C3 compensation
governs the mixing valves downstream. Complementary, not competing.

## Curve coordination (evaluated 2026-07-16)

The mixing valves can only mix **down**, so the C3 curve targets are reachable
only while the WPM supply stays above the hottest downstream request plus a
valve-authority margin (~2–3 K). Symmetrically, supply above what is needed
wastes COP (~2–2.5% per K). Coordination is therefore required — but because
the WPM curve and both C3 curves are functions of the **same input** (outdoor
temperature), the relationship is established once, at commissioning, and then
holds across the whole outdoor range by construction. No runtime protocol.

**Commissioning rule (heating):** shape the WPM curve to envelope the hottest
consumer at every outdoor temperature. That consumer is **not** the radiant
curves (GF floor caps at 40 °C, FF ceiling at 33 °C) — it is the **unmixed
fancoil circuits** (Locale Tecnico, Sottotetto heat on direct-pump primary
water), which want warmer supply in deep winter than either mixing curve.
Practically: WPM curve ≥ max(fancoil heating need, GF curve + 3 K, FF curve
+ 3 K) at design outdoor temperature.

**Cooling:** safe by construction — dew-point protection mixes *up* from the
cold primary, so the WPM cooling setpoint only needs to be cold enough for
fancoil dehumidification; radiant circuits blend to their floor regardless.

**Runtime optimization (optional, later):** dynamically lowering the WPM
setpoint toward the actual max C3 target would recover COP whenever fancoils
are idle. Only possible via the ISG/HA tier (Modbus TCP writes), so it must be
an *optimization overlay* that fails safe: HA down ⇒ the WPM's static envelope
curve carries on, merely less efficient. Do not build until the system has run
a season on the static envelope.

**Cheap autonomous diagnostic (recommended small work item):** the controller
already knows each circuit's supply temperature (Dallas) and target — a
"supply deficit" sensor (valve PID ≥ 95% while supply < target − 1 K for
N minutes) surfaces an under-enveloped WPM curve as a dashboard warning
instead of an unexplained cold floor.

## Open items

- [ ] Order the ISG web with the heat pump (or confirm the chosen unit ships
      with it integrated)
- [ ] Confirm SG Ready terminals in the chosen unit's manual; decide SG Ready
      yes/no at install (topology ADR: relay channels + wiring)
- [ ] HA: install the `stiebel_eltron` integration once the ISG is online
- [ ] Optionally point `ha_outdoor_temperature_sensor_id` at the ISG-exposed
      outdoor temperature entity (see `climate/outdoor.yaml`)
