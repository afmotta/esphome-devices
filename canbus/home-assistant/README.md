# canbus/home-assistant/

Home Assistant-side YAML for the CAN bus wall-button subsystem (see
`canbus/CLAUDE.md` and `canbus/README.md` for the protocol and
gateway-side detail). Copy or `!include` these into your Home Assistant config.

- `ha_arbitration_automations.yaml` — **hand-maintained**. The ADR-0003
  ha_ready/ACK arbitration prototype's HA-side ACK automation (log-only).
- `ha_manifest_package.yaml` — **generated**. Do not edit; regenerate with
  `python3 canbus/tools/generate_nodes.py`. Carries the
  readiness-heartbeat automation with the binding manifest hash baked in
  (ADR-0009 §4).

Looking for hold/hold_release dimmer and cover automations? Those are
lighting semantics, not CAN transport — see `lighting/home-assistant/`.
