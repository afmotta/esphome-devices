# Controller Died (T-Connect Pro)

The same board model — a LilyGO T-Connect Pro (ESP32-S3 with Ethernet, RS485, and
CAN built in) — is used for **two different roles** in this house: the climate
controller and the lighting controller. They run completely different firmware, but a
genuine spare of this board model works for either role — that's the point of
standardizing on one controller family.

Figure out which role died before doing anything else:

- **Climate controller** dead: no room is heating/cooling/ventilating, PID entities
  in Home Assistant are unreachable, or the whole climate device is offline.
- **Lighting controller** dead: no lights respond to Home Assistant *or* to wall
  buttons at all (a single unresponsive light is more likely a
  [relay board](relay-board.md) or [CAN node](can-node.md) issue — this page is for
  "the whole lighting system is down").

## Climate controller

1. Get a spare T-Connect Pro board (Ethernet variant).
2. Copy the secrets it needs. The local development build's secrets live in
   `devices/locals/secrets.yaml`; the production/OTA build's live in
   `devices/remotes/secrets.yaml` — these are separate files with (likely) different
   encryption keys, so use whichever matches how this specific controller was
   provisioned. If in doubt, start from `devices/secrets.yaml.example` and see
   [Environment Setup](../setup.md) for what each key means.
3. Flash it:
   - For a local/bench build: `esphome run devices/locals/climate-control.yaml
     --device /dev/ttyUSB0` (first flash needs USB; afterwards `esphome run` can go
     over the network).
   - For the production GitHub-pull deployment pattern: `devices/remotes/climate-control.yaml`
     pulls its firmware definition from GitHub and is normally installed by clicking
     "Install" on the device's card in the Home Assistant ESPHome add-on — see
     [Environment Setup](../setup.md) for the difference between these two patterns.
4. **Before energizing anything**, confirm the controller comes up in its safe idle
   state (🔵 designed, described in the project's own deployment runbook, not yet
   exercised after a real hardware swap):

   | Control | Expected after a fresh flash | Why it matters |
   |---|---|---|
   | `hp_mode_manual_hold` | ON | `hp_mode` won't move on its own |
   | `hp_mode` | SANITARY_ONLY | No space heating/cooling anywhere |
   | Every zone's `climate` entity | OFF | No radiant/fancoil actuation |
   | Each floor's heat-curve slope | 0 | Flat curve, fixed supply, no weather compensation surprise |
   | Boost-enabled switches | OFF | No hybrid radiant+fancoil boost |
   | MEV (ventilation) enabled | OFF | Fan stays off until you turn it on deliberately |

   If anything is actuating that shouldn't be, turn that specific zone's `climate`
   entity OFF as an immediate backstop, then investigate.
5. Once confirmed safe, bring zones back online deliberately and watch behavior for
   a day or two rather than restoring everything at once — see the maintenance-tasks
   [seasonal changeover](../maintenance-tasks.md) guidance for the same discipline
   applied routinely.

## Lighting controller

1. Get a spare T-Connect Pro board (Ethernet variant).
2. This controller is compiled directly — there's currently no `devices/locals/` or
   `devices/remotes/` variant for it (⚠️ unlike climate, only one config file exists:
   `devices/light-controller.yaml`). Flash it with
   `esphome run devices/light-controller.yaml --device /dev/ttyUSB0` for the first
   flash.
3. This device also carries the relay bank and the button-fallback logic — after
   flashing, confirm relays respond to Home Assistant commands, and that the
   `ha_ready` diagnostic looks correct (see
   [Everyday Monitoring](../monitoring.md) and
   [Lighting troubleshooting](../troubleshooting/lighting.md) if something looks
   wrong).
4. ⚠️ Unlike the climate controller, there's no documented "fresh-boot safe state"
   checklist for the lighting controller in this repository. Until one exists, the
   safest approach after a swap is to verify each relay manually before trusting the
   system unattended.

## Related

- [Environment Setup](../setup.md) — installing the tools and secrets needed to
  compile/flash in the first place.
- [Relay Board](relay-board.md) / [Analog Output Board](analog-board.md) — if it's
  actually one of the I/O boards, not the controller itself, that's down.
