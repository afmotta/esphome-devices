#!/usr/bin/env python3
"""Compare each entry point's RESOLVED `esphome: on_boot` triggers with a baseline.

Companion to scripts/check_on_boot_form.py (review R-18). The form check proves
the sources are list-form; this one proves the merged result still has one
trigger per source hook at its declared priority, by resolving the real configs
with `esphome config` and counting triggers per priority. A hook silently
dropped or folded into another trigger by the package merge changes the counts.

The baseline (scripts/on_boot_baseline.json) is {entry point: {priority: count}}.
When you add or remove a hook on purpose, regenerate it and commit the diff:

  python3 scripts/check_on_boot_resolved.py --update

Needs the `esphome` CLI (pip install "esphome==2026.8.0") and CI dummy secrets
(bash scripts/ci-dummy-secrets.sh). Run from the repo root.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml  # a dependency of esphome

BASELINE = Path(__file__).with_name("on_boot_baseline.json")

# Entry points whose resolved config is checked (those that carry, or could
# silently lose, an on_boot). Kept to the standalone-resolvable ones.
TARGETS = [
    "devices/locals/climate-control.yaml",
    "devices/locals/room-sensor-soggiorno.yaml",
    "devices/light-controller.yaml",
    "devices/health-monitor.yaml",
    "devices/an-penta-1.yaml",
    "devices/an-quad-1.yaml",
    "canbus/tests/compile_bridge.yaml",
    "canbus/tests/compile_buttons_bridge.yaml",
    "canbus/tests/compile_bridge_t2can.yaml",
    "canbus/tests/compile_sensor_node.yaml",
    "canbus/nodes/node100.yaml",
    "canbus/nodes/node101.yaml",
    "climate/tests/harness/fancoil_boost.yaml",
    "climate/tests/harness/pid_behaviour.yaml",
    "climate/tests/harness/radiant_direction.yaml",
]


class _Loader(yaml.SafeLoader):
    """Reads `esphome config` output: ESPHome tags (!lambda, !secret ...) become plain values."""


def _any_tag(loader: yaml.SafeLoader, _suffix: str, node: yaml.Node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


_Loader.add_multi_constructor("!", _any_tag)


def resolved_priorities(entry_point: str) -> dict[str, int]:
    proc = subprocess.run(["esphome", "config", entry_point], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"esphome config {entry_point} failed:\n{proc.stderr[-800:]}")
    config = yaml.load(proc.stdout, Loader=_Loader) or {}
    hooks = (config.get("esphome") or {}).get("on_boot") or []
    if isinstance(hooks, dict):  # defensive: the validated config is always a list
        hooks = [hooks]
    counts = Counter(str(float(hook.get("priority", 600.0))) for hook in hooks)
    return dict(sorted(counts.items(), key=lambda kv: -float(kv[0])))


def main(argv: list[str]) -> int:
    update = argv[:1] == ["--update"]
    current: dict[str, dict[str, int]] = {}
    for target in TARGETS:
        current[target] = resolved_priorities(target)

    if update:
        BASELINE.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {BASELINE}")
        return 0

    expected = json.loads(BASELINE.read_text(encoding="utf-8"))
    failed = False
    for target in TARGETS:
        want, got = expected.get(target), current[target]
        if want != got:
            failed = True
            print(f"{target}: resolved on_boot triggers changed\n  baseline: {want}\n  resolved: {got}", file=sys.stderr)
    if failed:
        print(
            "\nA hook was dropped, merged into another trigger, or its priority changed.\n"
            "If intentional, run `python3 scripts/check_on_boot_resolved.py --update`.\n"
            "Background: review R-18 (docs/reviews/2026-10-25-repo-review.md).",
            file=sys.stderr,
        )
        return 1
    total = sum(sum(c.values()) for c in current.values())
    print(f"resolved on_boot: {len(TARGETS)} entry points, {total} triggers match the baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
