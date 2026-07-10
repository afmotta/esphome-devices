- source_spec: none
  summary: Phase 6b — context rewrite (root CLAUDE.md rewritten as the four-system map, canbus/CLAUDE.md trimmed to infra-only, Claude memory files updated to final paths)
  evidence: Split from Phase 6 during scope routing on 2026-07-07 — the phase's own name has a "+" joining two different kinds of work; 6a (mechanical flatten) is battery-testable, 6b is judgment-call documentation authoring reviewed once final paths exist, per user's explicit choice

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-6b-context-doc-rewrite.md`
  summary: memory file `project_gateway_ha_event_firing_approach.md` cites `architecture.md (lines 153-162, 416, 579)` for the single-lambda-vs-YAML-action decision reversal; those line numbers were never verified against the current `architecture.md` and may have drifted independent of this restructure (architecture.md itself is a planning doc outside this phase's path-flatten scope)
  evidence: Surfaced by Blind Hunter review of Phase 6b; pre-existing citation-rot risk, not caused by this phase's path substitutions, but worth a follow-up check next time that memory file or architecture.md is touched

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-6b-context-doc-rewrite.md`
  summary: resolves which `architecture.md` the prior deferred entry (above) meant and finds the deeper issue: `canbus/_bmad-output/planning-artifacts/architecture.md` is the correct file (its lines ~156-167 and ~579 discuss the `homeassistant.event:` vs single-lambda decision), and it **already documents the reversal** ("Global staging: eliminated... An earlier design mandated a single-lambda direct internal-API call... that was reversed on 2026-06-02"). This means memory file `project_gateway_ha_event_firing_approach.md`'s claim that "architecture.md still contradicts this and should be updated... until then, the firmware is the source of truth" is itself now stale — architecture.md was already reconciled. Fixing the memory file's reasoning is out of this spec's scope (its intent-contract bars touching memory-file prose/reasoning, path substitutions only).
  evidence: Direct inspection of `canbus/_bmad-output/planning-artifacts/architecture.md` lines 156-167 and 579 during this review pass's verification of the prior deferred entry

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-6a-flatten-canbus.md`
  summary: canbus/packages/base_node.yaml and canbus/packages/health.yaml both declare `id: can0` for their respective CAN bus components (mcp2515 vs esp32_can) — a latent id collision if any future entry point ever composes both packages together. Confirmed no current entry point does (base_node.yaml: generated node YAMLs + compile_sensor_node.yaml only; health.yaml: devices/gateway.yaml only). Documented with a cross-reference comment in both files; renaming was out of scope for a mechanical flatten phase (base_node.yaml affects every generated node across the fleet)
  evidence: Surfaced by both Blind Hunter and Edge Case Hunter review of Phase 6a — pre-existing naming coincidence, made adjacency-visible (not caused) by merging the two packages into one directory this phase

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-1-registry-elevation.md`
  summary: allocate_node.py and commission.py have no automated test coverage at all (no test_allocate_node.py / test_commission.py exist)
  evidence: Surfaced by Blind Hunter review of Phase 1 — pre-existing gap, not introduced by the registry move, but their corrected path depth is currently verified only by manual/visual inspection

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-1-registry-elevation.md`
  summary: review-reality-check.md (added to git in the same commit as the Phase 1 move) documents pre-move state as if historical, but it is new content shipped already-stale by its own companion changes — worth a follow-up note or re-dating rather than treating it as frozen history
  evidence: Surfaced by Blind Hunter review of Phase 1; the file predates being tracked in git but not the repo's actual history, so the "frozen historical record" exception doesn't cleanly apply to it

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-2-lighting-is-born.md`
  summary: canbus/_bmad-output/implementation-artifacts/deferred-work.md:40 (frozen historical artifact) still calls ha_hold_automations.yaml "the template" without noting it moved to lighting/home-assistant/ — whoever picks up ADR-0012 open item 2 will look in the old canbus location and find nothing
  evidence: Surfaced by Edge Case Hunter review of Phase 2; left untouched by default since canbus/_bmad-output/ is frozen per AD-1, same policy applied to ADR-0012 and the merge-proposal doc this phase also left alone

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-2-lighting-is-born.md`, `_bmad-output/implementation-artifacts/spec-phase-3-ha-split-completes.md`
  summary: two manual HA-side package re-point steps need doing on the live Home Assistant instance once convenient — (1) hold/hold_release automations moved to lighting/home-assistant/ (Phase 2), (2) arbitration automation + manifest package moved to canbus/home-assistant/ (Phase 3). Bundle into one HA session; confirm HA reloads both packages without error.
  evidence: Surfaced by Blind Hunter review of Phase 2 and Phase 3; this repo has no visibility into the live HA config, so nothing in-repo can confirm the human actually did these steps

- source_spec: `_bmad-output/implementation-artifacts/spec-phase-4-hvac-gathering.md`
  summary: architectural invariants stated as prose in system CLAUDE.mds (e.g. hvac/CLAUDE.md's "hvac only reads registry/map.json, never writes it") have no mechanical enforcement (grep/lint/test) — matches this project's own documented pattern of status-hygiene drift needing a tooling gate, not another action item
  evidence: Surfaced by Blind Hunter review of Phase 4; fixing this needs a real check wired into the push gate or CI, out of scope for a docs/path-relocation phase


- source_spec: `_bmad-output/implementation-artifacts/spec-hvac-baseline-config-green.md`
  summary: `vesta/packages/components/pid_autotune_with_fancoil.yaml`'s autotune button writes `id(${boost_active_global}) = false;` directly in a lambda, bypassing `select.set`/`set_action` entirely — after an autotune-triggered deactivation the select still reads "Fancoil Boost", the radiant override switch/PWM stay locked at 100%, and `${zone_slug}_boost_active_sensor` stays stale, all disagreeing with the now-false raw global until the next real transition through the select.
  evidence: Surfaced independently by both Blind Hunter and Edge Case Hunter review of spec-hvac-baseline-config-green. Pre-existing design in `pid_autotune_with_fancoil.yaml`, which this spec's Boundaries explicitly forbid touching (its `boost_active_global` var contract was declared "already correct" — this spec only had to make the id exist to compile). The desync was latent and unobservable before this fix since the file didn't compile at all; now exposed at runtime.

- source_spec: `_bmad-output/implementation-artifacts/spec-hvac-baseline-config-green.md`
  summary: `vesta/docs/fancoil-boost.md`'s "Diagnostic Sensors" table lists 7 exposed entities including `{zone_slug}_cooling_mode`, `{zone_slug}_time_in_mode`, and `{zone_slug}_saturation_duration` — none of which exist in `fancoil_boost.yaml`, before or after this fix.
  evidence: Surfaced by Blind Hunter review of spec-hvac-baseline-config-green; pre-existing doc drift unrelated to this change (this fix implemented exactly one of the seven previously-fictitious rows, `boost_active_sensor`, and left the other three uncorrected — out of scope for a targeted bug fix).

- source_spec: `_bmad-output/implementation-artifacts/spec-hvac-baseline-config-green.md`
  summary: `vesta/packages/coordinators/fancoil_boost.yaml`'s boost-state `select` restores its option from flash on boot (`restore_value: true`) but nothing on boot replays the physical outputs `set_action` normally drives (locking `radiant_override_switch_id`/`radiant_override_value_id`/`radiant_pwm_id` at 100%, setting `fancoil_pid_id` to COOL) — a mid-boost reboot restores the *select* to "Fancoil Boost" but leaves the actual hardware at power-on defaults. This spec's on_boot fix (`${zone_slug}_boost_update_idle`) intentionally resyncs only the *reported* state (`boost_active_global`, the automation text_sensor, the new `boost_active_sensor`) to match the restored select option — it does not attempt to replay hardware actuation, since doing so safely (component-init ordering, whether motors/PWM/climate are ready at boot priority -100, whether this is even desirable vs. a manual re-confirm) is a separate design decision, not a two-id wiring fix.
  evidence: Surfaced by Edge Case Hunter round 2 review of spec-hvac-baseline-config-green. Pre-existing gap in the coordinator's boot-restore story that predates this spec (the select's `restore_value` never replayed `set_action`'s hardware side, before or after wiring the two globals) — this fix made the *reported* state trustworthy enough to newly expose the gap, but fixing it is out of scope for a targeted "wire the missing ids" bug fix.

- source_spec: `_bmad-output/implementation-artifacts/spec-vesta-modbus-relay-32ch.md`
  summary: `vesta/packages/devices/modbus-io/modbus_relay_board_32ch.yaml`'s `id_offset` var has no lower-bound guard — an `id_offset` below `-1` (e.g. `-2`) produces a negative `switch_number` for relay_1, which `modbus_relay_switch.yaml` turns into an invalid/malformed entity id like `switch.relay_-1`. The 8-ch board has the identical gap (unguarded `id_offset` arithmetic), but this spec newly documents and endorses negative `id_offset` as a supported 0-based pattern, raising the odds someone reaches for a value below `-1`.
  evidence: Surfaced independently by both Blind Hunter and Edge Case Hunter review of spec-vesta-modbus-relay-32ch (review-loop 1). Out of this spec's explicit scope — its Boundaries forbid adding speculative validation/guard vars ("do not invent a zero_based/start_at_zero var speculatively"); a bounds check would need either a lambda-based assertion or a documented convention, worth deciding deliberately in a follow-up rather than bolting on here.

- source_spec: `_bmad-output/implementation-artifacts/spec-vesta-modbus-relay-32ch.md`
  summary: `modbus_relay_board_32ch.yaml`'s `id_offset` var has no type check — a non-integer value (e.g. `0.5`) is not rejected and would produce a fractional/malformed `switch_number`, similar in kind to the existing negative-lower-bound gap already deferred above.
  evidence: Surfaced by Edge Case Hunter's second-pass review of spec-vesta-modbus-relay-32ch (review-loop 1, second pass). Same root cause and same out-of-scope rationale as the prior negative-`id_offset` deferral — no speculative validation vars per this spec's Boundaries.

- source_spec: `_bmad-output/implementation-artifacts/spec-vesta-modbus-relay-32ch.md`
  summary: the negative-`id_offset` finding (documented as supported, `id_offset: -1` → `relay_0..relay_31`) has no persisted regression check in this repo — it was verified with an uncommitted, deleted scratch config, and the committed compile-checked example (`vesta/examples/modbus_relay_board_32ch.yaml`) only exercises `id_offset: 0`. A future ESPHome version could silently regress the documented negative-offset behavior with nothing in-repo to catch it.
  evidence: Surfaced by Blind Hunter's second-pass review of spec-vesta-modbus-relay-32ch (review-loop 1, second pass). This spec's scope was limited to one example at `id_offset: 0` per its Code Map; adding a second compile-checked example (or extending the harness once `vesta/docs/testing-strategy.md`'s proposed layers exist) is a reasonable follow-up, not part of this additive package's minimum scope.
