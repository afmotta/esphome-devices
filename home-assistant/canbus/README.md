# home-assistant/canbus/

Home Assistant-side YAML for the CAN bus wall-button subsystem (see
`canbus/CLAUDE.md` and `canbus/firmware/README.md` for the protocol and
gateway-side detail). Copy or `!include` these into your Home Assistant config.

Hold/hold_release dimmer and cover automations moved to
`lighting/home-assistant/ha_hold_automations.yaml` — that content is lighting
semantics (what a gesture does), not CAN transport, so it lives with the
lighting system. See `lighting/CLAUDE.md` for that system's rules.

- `ha_arbitration_automations.yaml` — **hand-maintained**. The ADR-0003
  ha_ready/ACK arbitration prototype's HA-side ACK automation (log-only).
- `ha_manifest_package.yaml` — **generated**. Do not edit; regenerate with
  `python3 canbus/firmware/tools/generate_nodes.py`. Carries the
  readiness-heartbeat automation with the binding manifest hash baked in
  (ADR-0009 §4).
