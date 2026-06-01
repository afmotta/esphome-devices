## Deferred from: code review of 1-2-resolve-hardware-open-questions (2026-06-01)

- **SPI pin corrections (SCK=GPIO2, MOSI=GPIO3, MISO=GPIO4) not explicitly assigned to downstream stories** — Confirmed corrections documented in README table but not added as explicit subtasks in Stories 1.4 or 2.1. Risk of being overlooked when those stories are executed.
- **Source URLs not pinned to commit SHA** — OQ citations link to `main` branch of `CANBED_RP2040_V11_EAGLE` repo; if the schematic is ever revised, the reference is no longer reproducible.
- **`can_clock: "16MHZ"` capitalization unverified against ESPHome** — Schematic confirms 16 MHz but ESPHome's expected string format (`16MHZ` vs `16MHz`) is unverified. Confirm case-sensitivity in Story 2.1 when writing `base_node.yaml`.
- **Existing node YAMLs may still contain `can_int_pin: GPIO20`** — The wrong INT pin value is flagged but not corrected in this story. Audit and update in Stories 1.4 and 2.1.

## Deferred from: code review of 1-1-move-firmware-to-firmware-directory (2026-06-01)

- **MSG_BUTTON_EVENT and MSG_HEARTBEAT share value 0x01** [`firmware/common/canbus_protocol.h:20-21`] — Both constants are `0x01`; any dispatch on payload type will misroute one. Gateway currently disambiguates via CAN ID category mask, but a future refactor routing by type alone will silently break.
- **`includes:` path is CWD-sensitive** [`firmware/common/base_node.yaml`, `firmware/gateway.yaml`] — ESPHome resolves `includes:` relative to compile CWD, not the YAML file location. Must run `esphome compile` from project root; running from `firmware/` or `firmware/nodes/` will fail to find `common/canbus_protocol.h`.
- **`generate_nodes.py` silently overwrites node files on re-run** [`firmware/generate_nodes.py`] — No prompt, diff, or backup before overwriting. Manually edited node YAMLs will be lost without warning.
- **`generate_nodes.py` no duplicate GPIO validation within a row** [`firmware/generate_nodes.py`] — A CSV row with repeated GPIO values (e.g. `"2,2,3"`) passes validation and generates a YAML where two buttons share a pin; ESPHome compiles it but runtime behavior is unpredictable.
- **`generate_nodes.py` uses `assert` for all validation** [`firmware/generate_nodes.py`] — `assert` statements are disabled with `python -O`, silently bypassing all range checks for node_id, room, board, and button count.
