# Routine Configuration & Maintenance Tasks

This page walks through the maintenance and configuration tasks you're most likely to
need over the life of the house: adding a room, registering a new wall button,
rewiring what a button controls, tuning temperature control, switching the system
between heating and cooling season, upgrading the toolchain, and rotating credentials.

Each section is a self-contained, numbered walkthrough. If a term is unfamiliar, check
the [Glossary](reference/glossary.md).

!!! note "How to read the confidence tags on this page"
    🟢 **VERIFIED** — confirmed on a bench or in the field.
    🔵 **DESIGNED** — built and intended to work this way, not yet proven against a
    real installation (true for most of this pre-live house).
    ⚠️ **KNOWN GAP** — genuinely unresolved.

---

## Adding or moving a climate room

Use this when a room is added to the house, a room is split/merged, or a zone needs
moving to a different relay/channel.

1. **Create the room's config file.** Add a new file at
   `climate/rooms/[floor]/[room_name].yaml` (floor is `ground_floor`, `first_floor`,
   or `second_floor`; room name in snake_case, e.g. `camera_est.yaml`).
2. **Include the standard packages with room-specific values.** The file needs to
   include the sensor, radiant, and fancoil component packages, each parameterized
   with this room's values (slug, display name, sensor entity, relay number). Copy the
   shape of an existing room file in the same floor folder as your starting point —
   consistency matters more here than memorizing the exact fields.
3. **Register the room with its floor.** Add the new room's package include to that
   floor's aggregator file (`[floor]-floor.yaml` in the same folder). A room file that
   isn't included from its floor aggregator is invisible to the rest of the system.
4. **Pick an unallocated relay.** Every radiant zone needs its own relay channel on
   the climate relay board. Check the **live** assignment table in
   [Hardware & Address Table](reference/hardware-table.md#relay-assignment-table-climate-bus-address-0x2)
   for a free channel (currently `relay_5` or `relay_22`–`relay_32`), and update that
   table in the same change so it doesn't drift out of sync with the actual
   configuration. Fancoils don't get their own relay — they share their floor's pump
   relay and are separately modulated over the analog output board.
5. **Test the configuration before touching any hardware.**
   ```bash
   esphome config devices/locals/climate-control.yaml
   ```
   This checks the YAML is valid and every reference resolves — it does not need a
   physical device connected. Fix any errors it reports before moving on.
6. **Deploy.** Follow your normal deployment path (local USB/network flash for
   development, or the GitHub-based remote deployment for production — see the
   project's `climate/CLAUDE.md` if you need the full deployment mechanics). Watch the
   new zone's logs for the first few minutes after deploying, the same way you would
   for any change that touches actuation.

!!! warning "New rooms join a pre-live commissioning sequence"
    Climate zones in this house are brought online gradually and deliberately, not
    all at once — see the deployment runbook referenced from
    [Document Map](reference/doc-map.md) if this is a first-time commissioning rather
    than a routine addition to an already-live house.

---

## Adding or re-registering a CAN node

Use this when a new wall-button board or sensor board joins the CAN bus, or an
existing one is being re-registered (moved to a different room, or swapped for a
replacement board).

!!! danger "Read this before you start"
    The registry file this task edits (`registry/nodes.csv`) is the **only** record of
    which physical board is which node. It is not stored on the board itself — a board
    becomes whichever `node_id` it was most recently flashed with. Git is the only
    backup of that identity. The order of steps below exists specifically to make sure
    your change is safely backed up **before** you reflash anything, so a mistake
    costs you a retry, not a lost or duplicated identity.

1. **Make the registry change.** Either edit `registry/nodes.csv` directly, or use the
   provided tools: `canbus/tools/allocate_node.py` to reserve a fresh `node_id` for a
   brand-new board, or `canbus/tools/commission.py` to assign a room/location to a
   board (it supports a "press a button to identify yourself" flow).
2. **Regenerate the generated files.**
   ```bash
   python3 canbus/tools/generate_nodes.py
   ```
   This rebuilds the per-node firmware configs and related generated artifacts from
   the registry. Never hand-edit the generated files directly — the next regeneration
   would silently overwrite your edit.
3. **Run the generator's own check.** The project has an idempotence/consistency
   check that confirms the registry and the generated files agree:
   ```bash
   git diff --exit-code canbus climate registry
   ```
   run right after step 2 with a clean working tree, this should show no unexpected
   differences. If it does, something about the registry change or the regeneration
   needs another look before you continue.
4. **Commit the registry file and the generated files together, in the same commit.**
   They must never be committed separately — a generated file that doesn't match its
   registry source is worse than no generated file at all, because it looks correct
   until something actually reads the mismatched part.
5. **Push to the remote.** This is the step that actually creates a backup. Until this
   push completes, the only copy of your change is the disk it was typed on.
6. **Run the push gate before reflashing anything.**
   ```bash
   python3 canbus/tools/check_registry_pushed.py
   ```
   This must exit with code 0 ("success"). It checks that the registry/generated
   files are clean (nothing uncommitted) and that your latest commit is actually
   reachable from the remote repository — i.e. genuinely backed up, not just
   committed locally.
7. **Only now, reflash the affected board(s).** See
   [CAN Node replacement](hardware/can-node.md) for the flashing steps themselves.

**Why this order matters:** if you reflash a board *before* pushing, and something
then goes wrong on your laptop (disk failure, a bad `git reset`, an accidental
overwrite) before you get around to pushing, the board in the wall now has an identity
that exists nowhere else — not on the remote, not in any other backup. Rebuilding that
identity later means physically re-identifying every affected board by hand. Pushing
first, and confirming it with the gate script, means the worst case is "redo a
five-minute registry edit," never "lost the mapping between a board and its room."

---

## Changing a lighting binding

A "binding" is the mapping from a specific wall-button gesture (click, double-click,
hold) to what it controls (which relay, which action). Use this when you're rewiring
what a button does — no physical change needed, just logic.

1. **Edit `registry/bindings.yaml`** to change, add, or remove a binding.
2. **Regenerate the generated files**, exactly as in the CAN node task above:
   ```bash
   python3 canbus/tools/generate_nodes.py
   ```
3. **Run the same consistency check:**
   ```bash
   git diff --exit-code canbus climate registry
   ```
4. **Commit the registry file and generated files together**, push, and run the same
   push gate before reflashing:
   ```bash
   python3 canbus/tools/check_registry_pushed.py
   ```
5. **Reflash the lighting controller** (not the wall-button node — bindings are
   interpreted by the lighting controller and by Home Assistant, not by the button
   board itself, which just reports raw gestures).

This is the exact same push-before-reflash discipline as the CAN node task above, and
for the same reason: `registry/bindings.yaml` is unrebuildable house data, and git is
its only backup. See that task above if you want the fuller explanation of why the
order matters.

---

## Adjusting PID gains for a radiant or fancoil zone

PID (proportional-integral-derivative) control is what smoothly drives each zone's
temperature toward its target. Each zone has separate gains for heating and cooling,
and radiant and fancoil systems need very different starting points because they
behave very differently — radiant floors are slow to respond, fancoils are fast.

**Where the values live:** PID gains (`kp`, `ki`, `kd`) are set where the PID
component package is included for that zone/circuit — they are parameters passed in
at inclusion time, not buried in the shared component logic itself. Look for the
`vars:` block accompanying that zone's PID package include.

**Starting-point ranges:**

| System | Kp | Ki | Kd |
|---|---|---|---|
| Radiant floor (slow system) | 0.5–1.0 (start 0.8) | 0.001–0.01 (start 0.005) | 0.01–0.1 (start 0.05) |
| Fancoil (fast system) | 1.0–2.0 (start 1.2) | 0.005–0.02 (start 0.008) | 0.05–0.2 (start 0.08) |

Cooling mode typically needs higher gains than heating (increase all three by roughly
20–50%) because cooling responds faster once fan-driven air circulation is involved.

**Try auto-tune first.** Before hand-tuning, use the `pid_autotune.yaml` component —
it's built for exactly this and will usually get you closer, faster, than guessing
from the ranges above. Hand-tune from there only if the result still isn't tracking
well.

**Tuning process, once you have a starting point:**

1. Start conservative — low `kp`, very low `ki`/`kd`.
2. Increase gradually while watching for oscillation (temperature overshooting and
   swinging back repeatedly is a sign you've gone too far).
3. Tune heat and cool modes separately — they are genuinely different control
   problems on the same hardware.
4. Give a radiant zone real time to show its behavior — because it's a slow system, a
   change you make now won't show its full effect for hours, not minutes. Don't
   over-correct based on the first 20 minutes of data.

---

## Seasonal changeover

**This is a recurring task, roughly twice a year — not a one-time setup step.**

The heat pump produces either hot water or chilled water for the whole house at a
time, and the physical changeover between the two happens at the heat pump itself —
there is no changeover relay, and nothing in this software system detects which one
the heat pump is currently producing. `hp_mode` (and its companion,
`hp_mode_manual_hold`) are software controls the operator sets **manually** to tell
the system which one is actually happening, so the zone PID controllers pick the
matching heating-vs-cooling behavior.

1. **Know when your heat pump's installer switches the source over** — this is a
   mechanical/plumbing changeover on their side, and typically happens close to the
   change of season.
2. **After the source has changed, update `hp_mode`** in Home Assistant to mirror
   what's actually being produced now (e.g. from `HEAT` to `COOL`). Do this only
   *after* the source has actually changed — setting `hp_mode` ahead of the real
   changeover will make zones try to condition using water that isn't actually being
   produced yet.
3. **Leave `hp_mode_manual_hold` ON** unless your installation has already completed
   the cross-season automation phase described in the deployment runbook (see
   [Document Map](reference/doc-map.md)) — with the hold on, `hp_mode` only moves when
   you move it, which is the safer default.

!!! warning "This will keep happening"
    Every seasonal changeover — heating to cooling, and back again — needs this same
    manual step. There is no reminder built into the system; put it on a recurring
    calendar reminder tied to when your heat pump installer actually flips the source,
    not a fixed calendar date, since the real-world changeover date can shift year to
    year.

---

## ESPHome/toolchain upgrades

The project pins an **exact** ESPHome version rather than "latest" — currently tracked
in `climate/tests/pyproject.toml`. This is deliberate: an untested new ESPHome version
could silently change behavior in a system that runs unattended climate/lighting
actuation, so upgrades are a controlled event, not a background `pip install
--upgrade`.

1. **Update the version pin** in `climate/tests/pyproject.toml` to the new target
   ESPHome version.
2. **Run the full verification battery** — do not skip this, and do not treat a
   successful `pip install` as sufficient on its own:
   ```bash
   bash scripts/verification-battery.sh
   ```
   (use `--native-only` only if you genuinely don't have ESPHome installed in this
   environment — that skips the ESPHome-specific compile/config checks, which is not
   the full picture for a version upgrade).
3. **Only trust the new version once the battery passes clean.** If it doesn't, do not
   deploy the new version — either the upgrade introduced a real incompatibility that
   needs fixing, or the pin needs to move back down until the incompatibility is
   resolved upstream.
4. **Commit the pin change together with anything the battery required you to fix** —
   don't separate "bump the version" from "fix what broke because of it" into two
   commits that could be deployed independently.

---

## Credential/secret rotation

The system's secrets live in `devices/secrets.yaml` (gitignored — never committed).
The template at `devices/secrets.yaml.example` documents which ones exist:

| Secret | Scope |
|---|---|
| `wifi_ssid` / `wifi_password` | Shared WiFi credentials, used by every device (even ones normally on Ethernet — they still need WiFi configured as a fallback). |
| `api_encryption_key` | The lighting controller's Home Assistant API encryption key. |
| `health_monitor_encryption_key` | The CAN bus health monitor's own API encryption key — separate from the lighting controller's. |
| `encryption_key` | Shared by the climate controller and the standalone sensor devices (room sensor, wall sensor). |
| `ota_password` | Authenticates over-the-air firmware updates, house-wide. |
| `github_username` / `github_pat` | Used only by the GitHub-based remote deployment path, to pull this repository's config during an OTA update via the Home Assistant ESPHome add-on. |

**Rotate one credential at a time, in this order, so you can't lock yourself out:**

1. **Generate the new value first**, without touching anything live yet (for
   encryption keys: `openssl rand -base64 32`).
2. **Update `devices/secrets.yaml` locally** with the new value for just the one
   credential you're rotating.
3. **Reflash the affected device while the old credential still works, or over a
   direct USB connection.** For an API encryption key or OTA password, this usually
   means flashing over the network one last time using the *old* credential
   (before you finalize the change on the Home Assistant side), or connecting via USB
   if you're not confident the network path will still authenticate afterward. Either
   way, the point is: don't put yourself in a position where the only way to reach the
   device requires a credential you've already changed everywhere else but on the
   device itself.
4. **Verify connectivity** — confirm the device reconnects to Home Assistant / the
   network with the new credential before moving on to the next device.
5. **Only then consider that credential's rotation complete.** If you're rotating a
   credential shared across multiple devices (like `wifi_password` or `ota_password`),
   repeat steps 3–4 for every affected device before you can safely say the rotation
   is finished — a shared secret isn't "rotated" until every device that used the old
   value has been updated.

!!! danger "Don't update the secrets file and stop there"
    Changing `devices/secrets.yaml` alone does nothing to a device that's already
    running — it only takes effect the next time that specific device is reflashed. A
    half-finished rotation (file updated, some devices not yet reflashed) is a state
    you should get out of quickly: it means different devices in the house are
    currently trusting different values for the same nominal secret.

## Related

- [Hardware & Address Table](reference/hardware-table.md) — the live relay/channel
  assignment tables referenced above.
- [Glossary](reference/glossary.md) — definitions for any unfamiliar term on this
  page.
- [Confidence Ledger](reference/confidence-ledger.md) — several of the behaviors
  referenced above (commissioning gates, MEV cascade, boost coordination) are still
  🔵 DESIGNED, not yet field-verified.
- [Which device died?](hardware/index.md) — if you're here because something broke,
  not because you're making a planned change.
