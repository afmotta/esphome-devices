# Climate Deployment Runbook — Season-Phased Progressive Rollout

| Field | Value |
|---|---|
| **Status** | Active — the deployment procedure for the pre-live climate system |
| **Date** | 2026-07-23 |
| **Applies to** | `devices/climate-control.yaml` on ADR-0014 hardware (T-Connect Pro, single Modbus master) |
| **Supersedes** | `docs/deployment-guide.md` (historical, Gen-1 A6/A16 topology) |
| **Related** | ADR-0014 §4 bring-up checks; `docs/heat-pump-integration.md` (curve envelope); `climate/CLAUDE.md` App. B/C/D |

Bring the house online at a bare-minimum, safe feature set, prove it, then unlock
advanced features gradually — with a verification window and an instant rollback at
each step.

## Two physical realities that shape this runbook

1. **One seasonal mode, house-wide, set at the source.** The heat pump produces
   *either* hot water *or* chilled water, and the changeover happens at the source.
   The `hp_mode` select only **mirrors** that so the zone PIDs pick heat-vs-cool
   behaviour — ESPHome never drives a changeover (there is no changeover relay).
   **You can only commission the emitters for the season the source is currently
   producing**, so full feature coverage spans **both seasons (~a year)**.
2. **First-floor cooling requires MEV.** The first floor cools via a radiant
   **ceiling**; its dew-point-limited supply only cools effectively and safely once
   MEV dehumidification has pulled the room dew point down. MEV runs year-round and
   is therefore commissioned in Phase 0, ahead of any cooling.

## Mechanism: one image, runtime-gated

Everything is compiled into a single firmware image; you advance by flipping Home
Assistant controls, never by reflashing. This is deliberate — the
`any_pid_requesting_heat/cool` aggregation in `devices/climate-control.yaml`
hard-references every zone's PID (enforced by
`scripts/verify_seasonal_mode_aggregation.py`), so compiling zones out would break
the build. Rollback at every step is a switch flip.

Most gates reuse controls that already existed. Three commissioning gates were added:

| Gate | Default | Effect when off/held |
|---|---|---|
| `hp_mode_manual_hold` | **ON** | Calendar + demand tiers suspended; operator owns `hp_mode` |
| `{zone}_boost_enabled` (Soggiorno, Cucina) | **OFF** | No hybrid radiant+fancoil boost; an active boost is dropped to "Radiant Only" |
| `first_floor_mev_enabled` | **OFF** | Fan forced to 0; cascade released to "Fan Only" |

## Fresh-boot safe state

A freshly flashed controller comes up idle. Confirm before energising anything:

| Control | Expected | Effect |
|---|---|---|
| `hp_mode_manual_hold` | ON | `hp_mode` will not move on its own |
| `hp_mode` | SANITARY_ONLY | No space conditioning; all zone PIDs idle |
| every zone `climate` entity | OFF | No radiant/fancoil actuation |
| `{floor}_heat_curve_slope` | set to **0** | Flat curve → mixing valve holds a fixed `{floor}_heat_curve_base` supply |
| `{zone}_boost_enabled` | OFF | Boost suppressed |
| `first_floor_mev_enabled` | OFF | Ventilation off |
| window-guard sensor vars | unmapped | Guard is a no-op |

Verify `SANITARY_ONLY` genuinely idles all zone PIDs. If any emitter still actuates,
per-zone `climate` OFF is the backstop.

## Pre-deploy gate (before every deploy)

There is no staging environment — the green build is the gate:

```bash
bash scripts/verification-battery.sh          # or --native-only if ESPHome absent
esphome config  devices/locals/climate-control.yaml
esphome compile devices/locals/climate-control.yaml
```

The battery's generator-idempotence step requires a clean tree under `canbus/`,
`climate/`, and `registry/` — commit or stash first. The pinned CLI lives in
`climate/tests/.venv` (esphome 2026.7.0); a system ESPHome below the repo's
2026.7.0 floor will fail on `min_version`.

---

## Phase 0 — Infrastructure & ventilation *(any season; do first)*

### 0.1 First light

Deploy with the fresh-boot safe state above. Nothing should control anything.

**Hardware bring-up checks (ADR-0014 §4 + open item 1):**
- RS485 parity/baud: target **38400 8E1**. If the Waveshare boards or the MEV can't
  do EVEN parity, reconcile the *whole* bus as a substitution-level change (the MEV
  is the least flexible member and therefore the binding constraint).
- Onboard-relay / free-GPIO audit; confirm the analog board is the **(B)** variant;
  confirm no I²C collision (DS2484 `0x18` vs the touch chip).

**Verify:**
- [ ] HA API connected; SNTP time valid
- [ ] CAN receiver publishing room temp/humidity + air-quality
- [ ] Failover tier text sensors report CAN (or HA fallback)
- [ ] Relay board (`0x2`) and analog board (`0x1`) respond; MEV (`0x10`) readable
- [ ] **Manually pulse each relay and analog channel** to confirm the wiring/actuator
      map against `climate/CLAUDE.md` App. B/C — pumps, mixing valves, fancoil fans
- [ ] No control loop has moved anything on its own

**Rollback:** n/a (nothing is actuating).

### 0.2 Ventilation (MEV)

**Advance:** `first_floor_mev_enabled` → **ON**; tune demand bounds via the HA
`input_number` entities.

**Verify:**
- [ ] Fan tracks the aggregated demand (CO2 / VOC / NOx / PM / humidity)
- [ ] Humidity cascade escalates and de-escalates (Fan Only → Dehumidifying →
      Integration and back) with the configured delays
- [ ] Dehumidification measurably lowers room dew point — this is what makes
      first-floor cooling safe later
- [ ] Alarm-forces-zero safety holds (any of the 39 alarm types → fan 0)

**Rollback:** `first_floor_mev_enabled` → OFF (fan forced to 0, cascade released).

---

## Phase A — Active-season climate campaign

Set `hp_mode` to mirror **what the source is actually producing** (keep
`hp_mode_manual_hold` ON). Commission **mid-season**, not in a shoulder period where
the source may be idle. Bring zones online **one at a time**. Run the campaign that
matches the source; the other one becomes Phase B.

### If the source is HEATING

| Step | Advance | Verify | Rollback |
|---|---|---|---|
| **A-H1 Radiant heat** *(bare minimum)* | `hp_mode` → HEAT; `slope = 0` and `{floor}_heat_curve_base` set conservative (floor warmer than ceiling); zone `climate` OFF→HEAT one at a time | ±0.5 °C tracking; no PID oscillation; mixing valve + pumps behave; tune with the `pid_autotune*` buttons using App. D radiant gains; **24–48 h** | Zone → OFF, or `hp_mode` → SANITARY_ONLY |
| **A-H2 Fancoil heat** | Bring fancoil `climate` entities online (verify 0-10V output and fan first) | Modulation tracks setpoint | Fancoil zone → OFF |
| **A-H3 Weather compensation** | Dial `{floor}_heat_curve_slope` to real values using the commissioning envelope in `docs/heat-pump-integration.md` | Supply follows outdoor temp; valve not saturating; per-emitter curves respected (radiant ceiling runs cooler than radiant floor) | `slope` → 0 (back to flat/fixed) |

> The curve params (`slope`/`base`/`supply_min`/`supply_max`) have **no package
> defaults** on purpose — each floor states its own, because a radiant floor and a
> radiant ceiling need very different curves.

### If the source is COOLING

| Step | Advance | Verify | Rollback |
|---|---|---|---|
| **A-C1 Dew-point protection** | `hp_mode` → COOL with all zone cooling still OFF | `{floor}_supply_temp_minimum` computes (dew point + safe margin); mixing valve is ready to mix **up** | `hp_mode` → SANITARY_ONLY |
| **A-C2 Radiant cool** | Zone `climate` OFF→COOL one at a time; ground floor first, then first floor (safe because MEV from Phase 0 is dehumidifying) | No condensation on either floor; supply held above dew point + margin; **24–48 h** | Zone → OFF |
| **A-C3 Fancoil cool** | Bring fancoil `climate` entities online | Modulation tracks | Fancoil zone → OFF |
| **A-C4 Fancoil boost** | `{zone}_boost_enabled` → ON (Soggiorno, Cucina) | Boost entry/exit and anti-cycling delays; radiant locks to 100% and releases cleanly; no fighting with the radiant override | `{zone}_boost_enabled` → OFF (an active boost drops to "Radiant Only" immediately) |

> Dew-point protection is **not** an optional later step — it ships live with any
> radiant cooling. `hp_mode = COOL` must never be reachable before A-C1, and never
> before MEV is proven.

---

## Phase B — Other-season campaign *(at the next source changeover)*

Months later, when the installer switches the source over: update `hp_mode` to mirror
the new mode (keep the hold ON) and run the **opposite** campaign table from Phase A,
with the same per-step verification and rollback.

---

## Phase C — Cross-season automation & optimization

Only after **both** campaigns are proven.

1. **Window guard** — map the HA window sensors per `docs/window-sensors-map.md`. It
   self-activates (fancoil off on open, radiant untouched) and stays a no-op where
   unmapped or where HA is down.
2. **Release automatic seasonal transitions** — flip `hp_mode_manual_hold` → **OFF**
   so the calendar and demand-driven shoulder logic run on their own.
   > **First align the `seasonal_mode` calendar date ranges to the installer's real
   > source-changeover schedule.** Otherwise the calendar can drive `hp_mode` to a
   > mode the source is not producing.
3. **Weather-comp refinement** after a full heating season of data.
4. **Backlog** — ISG-web HA telemetry (`stiebel_eltron`); SG-Ready relays
   (`relay_18`/`relay_19`, pending the parked topology ADR); the deferred runtime
   setpoint-optimization overlay (only after a season on the static envelope, and it
   must fail safe to the static curve when HA is down). See
   `docs/heat-pump-integration.md` and `TODO.md`.

---

## Monitoring windows and rollback discipline

- Hold a **24–48 h** window on every step that moves an emitter before advancing.
- Watch: temperature tracking (±0.5 °C), PID stability (no oscillation), Modbus error
  rate, failover tier transitions, and — in cooling — dew-point margin.
- Every step's rollback is a single runtime control. No reflash, no config edit. If a
  step misbehaves, roll it back first and diagnose from the prior known-good tier.
