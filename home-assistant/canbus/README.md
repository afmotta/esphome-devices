# home-assistant/canbus/

Home Assistant-side YAML for the CAN bus wall-button subsystem (see
`canbus/CLAUDE.md` and `canbus/firmware/README.md` for the protocol and
gateway-side detail). Copy or `!include` these into your Home Assistant config.

- `ha_hold_automations.yaml` — **hand-maintained**. Reference automations for
  hold/hold_release button gestures (ADR-0012), including the derived
  long-press example.
- `ha_arbitration_automations.yaml` — **hand-maintained**. The ADR-0003
  ha_ready/ACK arbitration prototype's HA-side ACK automation (log-only).
- `ha_manifest_package.yaml` — **generated**. Do not edit; regenerate with
  `python3 canbus/firmware/tools/generate_nodes.py`. Carries the
  readiness-heartbeat automation with the binding manifest hash baked in
  (ADR-0009 §4).
