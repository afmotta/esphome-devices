## Deferred from: code review of 1-3-author-canbus-protocol-header (2026-06-01)

- **`payload_room`/`payload_board` return wrong bytes for heartbeat frames** [`firmware/common/canbus_protocol.h`, `firmware/gateway.yaml:159`] — `payload_room(d)` reads `d[4]` which is `error_flags` in a heartbeat frame; `payload_board(d)` reads `d[5]` which is `room`. Gateway heartbeat handler calls these decoders (lines 159–160), silently staging wrong values into `evt_room`/`evt_board` globals on every heartbeat. Pre-existing; correct with heartbeat-specific decoders or split the layout in a future story.
- **`button_index` not range-checked in `button_payload`** [`firmware/common/canbus_protocol.h`] — Accepts `uint8_t button_index` (0–255) without validation; values 6–255 produce syntactically valid frames with out-of-spec button indices. Pre-existing design choice; the constraint (max 6 GPIOs) is enforced at Python codegen level in `generate_nodes.py`.
- **`static const` gives internal linkage for all protocol constants** [`firmware/common/canbus_protocol.h`] — Should prefer `inline constexpr` for a header-only constants file to avoid ODR issues if ESPHome's code generator ever emits multiple translation units. Pre-existing; no current practical impact under ESPHome's single-TU model.

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

## Deferred from: code review of 1-4-validate-code-generation-pipeline (2026-06-01)

- **Missing-CSV bootstrap still writes stale sample rows with obsolete GPIO values and node IDs** [`firmware/generate_nodes.py:80`] — If `nodes.csv` is absent, the script still seeds legacy example rows (`0/1/2/10/11/12/20`) with old button GPIO defaults before generating YAMLs from them. Pre-existing issue outside the lines changed for Story 1.4.
