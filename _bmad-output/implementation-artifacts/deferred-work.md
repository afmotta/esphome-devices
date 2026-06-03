## Closed During Epic 3 Deferred-Work Follow-Up (2026-06-03)

- **project-context.md staging-globals mandate corrected** [`_bmad-output/project-context.md:61-64,150-153`] — both the `homeassistant.event` data rule and the "key non-obvious facts" note claimed values must be staged into globals first. Shipped CAT_INPUT handler (`firmware/gateway.yaml:102-108`) uses a per-field `!lambda` re-decoding directly from frame vector `x` — no globals. Doc now describes the actual per-field re-decode pattern, narrows the real constraint (cannot reference a var from a *separate preceding* `lambda:` action), and records it as the deliberate [[project_gateway_ha_event_firing_approach]] decision.
- **README ESPHome version reframed as known-good, not pinned + HA re-adoption note added** [`firmware/README.md:68-83`] — "Pinned version" relabeled "Known-good version" with an explicit "Not enforced (no `esphome: min_version:`)" caveat; password→encryption migration note now states an already-adopted gateway must be deleted and re-added in HA with the new encryption key.
- **Secrets onboarding documented** [`firmware/README.md`] — new "Onboarding: `secrets.yaml`" section lists the three required keys (`wifi_ssid`, `wifi_password`, `api_encryption_key`) and states the build fails at config load if any is missing (no pre-flight validation; ESPHome default).

## Deferred from: code review of 3-3-gateway-cat-status-handler-heartbeat-logging.md (2026-06-03)

- **`%u`/`%02u` format specifiers receive `uint8_t` args promoted to signed `int`, not `unsigned int`** [`firmware/gateway.yaml:124-128`] — formally undefined behavior per the C standard, but harmless in practice for `uint8_t` values on this platform (and `-Wformat` may flag it). Pre-existing codebase convention: the error-path `ESP_LOGW` and the CAT_INPUT handler use the same pattern. Story 3.3 only extends it to one new `errors` argument on the normal-path `ESP_LOGD`. Not introduced by this change; revisit codebase-wide if a stricter format-safety pass is ever warranted.

## Deferred from: code review of 3-2-gateway-cat-input-handler-button-events-to-home-assistant.md (2026-06-02)

- **No rate-limit/dedup on HA event firing** [`firmware/gateway.yaml:97`] — `homeassistant.event:` fires on every matching CAT_INPUT frame; a noisy bus or a stuck/repeating frame floods the HA event bus. Low risk for human-paced button clicks; pre-existing design, not introduced by Story 3.2. Revisit if a chatty-bus scenario emerges.

## Deferred from: code review of 3-1-gateway-base-configuration-twai-esp-idf-and-native-api.md (2026-06-02)

- **Service send_data() error handling** [`firmware/gateway.yaml:53-76`] — Services log canbus errors but don't implement recovery, retry, or user notification. Pre-existing design pattern; not regression. Defer to future story on command reliability and timeout handling.


## Deferred from: code review of 2-3-node-heartbeat-and-can-frame-receive-lambda-safety.md (2026-06-02)

- **`uptime_h` silently overflows at 255 hours (~10.6 days)** [`firmware/common/base_node.yaml`] — `(uint8_t)((millis() / 3600000UL) & 0xFF)` wraps to 0 with no flag or epoch counter; a receiver cannot distinguish a rebooted node from a 256-hour-old one. Pre-existing.

## Remaining Epic 1 Residuals (2026-06-01)

- **`button_index` is still not range-checked inside `button_payload`** [`firmware/common/canbus_protocol.h`] — Epic 1 continues to enforce the 0–5 invariant at the generator/config layer (`generate_nodes.py` emits at most 6 buttons, `button.yaml` uses those generated indices). No wire-spec-defined invalid-button encoding was added in this follow-up.

## Closed During Epic 2 Deferred-Work Follow-Up (2026-06-02)

- **Click-timing dead-zones fixed** [`firmware/common/button.yaml`] — double/triple inter-press windows tightened from `OFF for 0.05s to 0.4s` to `0.05s to 0.29s` so they no longer overlap single-click's `OFF for at least 0.3s`; long press capped at `1s to 2999ms` so the extra-long (`>= 3s`) pattern is reachable. De-risks the Epic 4 acceptance matrix for double-click and extra-long-press.
- **`send_data()` TX failures now logged** [`firmware/common/button.yaml`] — the shared `btn*_send_event` script captures the `canbus::Error` return and emits `ESP_LOGW` on non-OK, so dropped events on a busy bus are observable (NFR-8 spirit).
- **CAN ID direction convention resolved + documented** [`firmware/common/base_node.yaml`, `firmware/generate_nodes.py`, `firmware/nodes/*`] — platform-level (default TX) `can_id` now uses `${input_can_id}` (CAT_INPUT, node → gateway) instead of `${output_can_id}`; the `on_frame` RX filter keeps `${output_can_id}` (CAT_OUTPUT, gateway → node) with an explicit comment. `input_can_id` is regenerated into node files (no longer stale/unused). Direction convention is documented in the base-node header and generator node comment.
- **`(x[3] << 8)` integer promotion fixed** [`firmware/common/base_node.yaml`] — now `(static_cast<uint16_t>(x[3]) << 8) | x[4]`; portable across `int` widths.
- **`CAN_FRAME_SIZE` retyped to `std::size_t`** [`firmware/common/canbus_protocol.h`] — exact comparison against `std::vector::size()` with no implicit promotion; added `#include <cstddef>`.
- Validation: `esphome compile nodes/node100.yaml` and `node101.yaml` both SUCCESS on ESPHome 2026.5.0.

## Closed During Epic 1 Deferred-Work Follow-Up (2026-06-01)

- **Heartbeat room/board decoding fixed** [`firmware/common/canbus_protocol.h`, `firmware/gateway.yaml`] — added `payload_heartbeat_room()` / `payload_heartbeat_board()` and switched the gateway heartbeat handler to use them.
- **Header-only constants promoted to `inline constexpr`** [`firmware/common/canbus_protocol.h`] — removes the internal-linkage concern from the previous `static const` definitions while preserving the approved wire values.
- **Generator now rejects duplicate GPIOs in a row** [`firmware/generate_nodes.py`] — rows such as `"20,20"` now fail with a clear error and non-zero exit.
- **Missing-CSV bootstrap updated and made non-destructive** [`firmware/generate_nodes.py`] — the script now seeds current PoC rows (`100` / `101`, GPIO20/21) and exits before generating node YAMLs.
- **Pinned schematic references recorded** [`firmware/README.md`] — README citations now point to commit `fdefed9e521864c67a05bf19a4e5046428b86662` instead of `main`.
- **`can_clock: "16MHZ"` validated** [`firmware/nodes/node100.yaml`] — `esphome compile nodes/node100.yaml` succeeded with the current spelling.
- **Generated node INT pin audit passed** [`firmware/nodes/node100.yaml`, `firmware/nodes/node101.yaml`] — current generated nodes already use `can_int_pin: "GPIO11"`.
- **Include-path concern not reproducible** [`firmware/common/base_node.yaml`, `firmware/gateway.yaml`] — `esphome config` succeeded both from repo root (`firmware/nodes/node100.yaml`) and from `firmware/` (`nodes/node100.yaml`).
- **`MSG_BUTTON_EVENT` / `MSG_HEARTBEAT` sharing `0x01` remains intentional** [`firmware/common/canbus_protocol.h`] — confirmed by the PRD wire spec; category bits disambiguate button vs heartbeat frames.
- **`assert`-based validation note was stale** [`firmware/generate_nodes.py`] — generator validation already used explicit `print + sys.exit(1)` checks before this follow-up.
- **SPI pin corrections are already propagated downstream** [`firmware/generate_nodes.py`, `firmware/nodes/node100.yaml`, `firmware/nodes/node101.yaml`] — template and generated nodes now carry GPIO2 / GPIO3 / GPIO4 and GPIO11.

## Deferred from: code review of 2-2-per-button-package-5-event-types-via-on-multi-click.md (2026-06-02)

- **node_id ≥ 512 silently produces colliding CAN IDs** [`firmware/common/canbus_protocol.h`] — `can_id()` masks `node_id & 0x1FF` (max 511); node IDs 512+ wrap and collide. Currently safe because `generate_nodes.py` validates node IDs to 0–399. Pre-existing.

## Deferred from: code review of 2-1-base-node-configuration-spi-and-mcp2515-setup.md (2026-06-01)

- `can_int_pin` substitution is generated in node YAMLs but not consumed by `canbus.mcp2515` config in `firmware/common/base_node.yaml`; keep as deferred pre-existing cleanup until platform support or template strategy is revisited.
