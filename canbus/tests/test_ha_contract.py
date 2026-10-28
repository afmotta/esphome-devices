#!/usr/bin/env python3
"""
Contract test: the Home Assistant YAML must call the names the lighting controller really
exposes (review R-03). Stdlib only. Run:  python3 canbus/tests/test_ha_contract.py

ESPHome registers an API user service in HA as `esphome.<device_name, '-' -> '_'>_<service>`,
but names an entity after the HA *device* name (`friendly_name` when set):
`<domain>.<friendly_name slug>_<entity name slugified>`. Nothing at build time checks
that HA-side YAML agrees: a stale name compiles, loads, and fails silently — the heartbeat
never arrives, ha_ready stays false, every press takes the local fallback and no
esphome.canbus_button event reaches HA. This test reads the real files on both sides:

  devices/light-controller.yaml            device_name -> service prefix; friendly_name -> entity slug
  devices/health-monitor.yaml              friendly_name      -> health-monitor entity slug
  lighting/packages/buttons.yaml           `- service:` names, "HA Ready" / "Fallback Events"
  generate_nodes.render_ha_package         heartbeat action (rendered fresh)
  canbus/home-assistant/ha_manifest_package.yaml        same, as committed (generated drift)
  canbus/home-assistant/ha_arbitration_automations.yaml hand-maintained ACK action
  canbus/home-assistant/ha_node_health_package.yaml     entity ids the health alerts watch

and fails if any of them disagrees. Both service calls go to the lighting controller
(ha_readiness_heartbeat, ha_ack_event) — the gate instance lives in lighting/, not on the
health monitor.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import generate_nodes as g  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DEVICE_YAML = REPO / "devices" / "light-controller.yaml"
HEALTH_YAML = REPO / "devices" / "health-monitor.yaml"
BUTTONS_YAML = REPO / "lighting" / "packages" / "buttons.yaml"
HEALTH_PKG = REPO / "canbus" / "packages" / "health.yaml"
HA_DIR = REPO / "canbus" / "home-assistant"
HASH = "d66767448ba37b2f"


def _substitution(path: Path, key: str) -> str:
    m = re.search(rf"^\s+{key}:\s*[\"']?([^\"'#\n]+?)[\"']?\s*(?:#.*)?$", path.read_text(), re.M)
    assert m, f"no `{key}:` substitution found in {path}"
    return m.group(1)


def _device_name() -> str:
    return _substitution(DEVICE_YAML, "device_name")


def _declared_services() -> list:
    return re.findall(r"^\s+-\s+service:\s*([A-Za-z0-9_]+)\s*$", BUTTONS_YAML.read_text(), re.M)


def _entity_name(path: Path, domain: str, label: str) -> str:
    """Assert `path` declares an ESPHome `<domain>:` entity with this display name; return its slug.

    Only the top-level `<domain>:` block is searched, so an entity moved to another platform
    (which can change its HA domain, and so its entity id) fails here instead of passing on a
    stale id.
    """
    block = re.search(rf"^{domain}:\s*\n((?:[ \t].*\n|\s*\n)*)", path.read_text(), re.M)
    assert block and re.search(rf'^\s+name:\s*"{re.escape(label)}"\s*$', block.group(1), re.M), \
        f'{path.name} no longer declares a {domain} named "{label}"'
    return g.ha_slug(label)


def _actions(text: str) -> list:
    return re.findall(r"^\s*-\s+action:\s*(esphome\.\S+)\s*$", text, re.M)


def test_generator_constant_matches_device_yaml():
    assert g.LIGHTING_DEVICE_NAME == _device_name(), (
        f"generate_nodes.LIGHTING_DEVICE_NAME={g.LIGHTING_DEVICE_NAME!r} but "
        f"devices/light-controller.yaml has device_name={_device_name()!r}")
    assert g.LIGHTING_SERVICE_PREFIX == f"esphome.{g.ha_slug(_device_name())}_"
    for const, entity_slug, yaml in ((g.LIGHTING_FRIENDLY_NAME, g.LIGHTING_ENTITY_SLUG, DEVICE_YAML),
                                     (g.HEALTH_FRIENDLY_NAME, g.HEALTH_ENTITY_SLUG, HEALTH_YAML)):
        friendly = _substitution(yaml, "friendly_name")
        assert const == friendly, f"generate_nodes friendly name {const!r} but {yaml.name} has {friendly!r}"
        assert entity_slug == g.ha_slug(friendly)


def test_lighting_declares_the_arbitration_services():
    services = _declared_services()
    assert "ha_readiness_heartbeat" in services, services
    assert "ha_ack_event" in services, services


def test_every_ha_action_is_a_declared_lighting_service():
    prefix = f"esphome.{g.ha_slug(_device_name())}_"
    declared = {prefix + s for s in _declared_services()}
    sources = {
        "render_ha_package()": g.render_ha_package(HASH),
        "ha_manifest_package.yaml (generated, on disk)": (HA_DIR / "ha_manifest_package.yaml").read_text(),
        "ha_arbitration_automations.yaml": (HA_DIR / "ha_arbitration_automations.yaml").read_text(),
    }
    for label, text in sources.items():
        actions = _actions(text)
        assert actions, f"{label}: no esphome.* action found"
        for a in actions:
            assert a in declared, f"{label}: {a} is not a service the lighting controller exposes ({sorted(declared)})"
    # Each service the arbitration relies on is actually called, by the right file.
    assert prefix + "ha_readiness_heartbeat" in _actions(sources["render_ha_package()"])
    assert prefix + "ha_readiness_heartbeat" in _actions(sources["ha_manifest_package.yaml (generated, on disk)"])
    assert prefix + "ha_ack_event" in _actions(sources["ha_arbitration_automations.yaml"])


def test_health_package_entity_ids_match_device_entities():
    # Entity ids follow the HA device name, i.e. friendly_name (services follow device_name).
    light, health = g.LIGHTING_ENTITY_SLUG, g.HEALTH_ENTITY_SLUG
    ha_ready = f"binary_sensor.{light}_{_entity_name(BUTTONS_YAML, 'binary_sensor', 'HA Ready')}"
    fallback = f"sensor.{light}_{_entity_name(BUTTONS_YAML, 'sensor', 'Fallback Events')}"
    online = f"sensor.{health}_{_entity_name(HEALTH_PKG, 'sensor', 'Nodes Online')}"
    # "Nodes Missing" is an ESPHome text_sensor, which HA exposes in the `sensor` domain.
    missing = f"sensor.{health}_{_entity_name(HEALTH_PKG, 'text_sensor', 'Nodes Missing')}"
    for label, text in {
        "render_ha_node_health_package()": g.render_ha_node_health_package([]),
        "ha_node_health_package.yaml (generated, on disk)": (HA_DIR / "ha_node_health_package.yaml").read_text(),
    }.items():
        for eid in (ha_ready, fallback, online):
            assert re.search(rf"^\s+entity_id:\s*{re.escape(eid)}\s*$", text, re.M), \
                f"{label}: expected a trigger on {eid}"
        assert f"states('{missing}')" in text, f"{label}: expected a template reading {missing}"


def test_no_retired_gateway_device_name_in_ha_yaml():
    # The pre-ADR-0015 combined device ("canbus-gateway") no longer exists; any HA name
    # derived from it points at nothing.
    for f in HA_DIR.glob("*.yaml"):
        text = f.read_text()
        assert "canbus_gateway" not in text and "canbus-gateway" not in text, \
            f"{f.name} still references the retired canbus-gateway device"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\nAll {len(tests)} HA-contract tests passed.")


if __name__ == "__main__":
    main()
