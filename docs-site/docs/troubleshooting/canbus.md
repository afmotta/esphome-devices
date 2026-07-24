# CAN Bus — Diagnose & Fix: Common Problems

The CAN bus is the wiring that carries button presses from wall-mounted button
boards ("nodes") to the two controller devices that listen to it: the
**lighting controller**, which turns button presses into light actions, and
the **health monitor**, which watches whether every node is still alive. This
page covers problems with that wiring and with the nodes/monitor themselves —
not with what a button press *does* (see
[Lighting](lighting.md) for that) and not with the separate RS485/Modbus wiring
used for relays and climate I/O (see [RS485 / Modbus](rs485-modbus.md)).

!!! note "How to read the confidence tags on this page"
    This house-wide system has not been physically installed yet (it is
    "pre-live"), so almost nothing here has been tested against a real fault
    in the field. Every non-trivial claim is tagged:

    - 🟢 **VERIFIED** — confirmed on a bench or in the field.
    - 🔵 **DESIGNED** — built and intended to work this way, but not yet
      proven against a real failure.
    - ⚠️ **KNOWN GAP** — genuinely unresolved; stated plainly rather than
      guessed at.

---

## A node isn't responding / Home Assistant shows it as "lost"

**Symptom:** A wall-button board stops reacting to presses, or a Home
Assistant notification/entity says a node is missing or lost.

**Likely causes:**

- The node has lost power (blown fuse, disconnected wire, dead supply).
- The node's CAN wiring at its tap has come loose or broken.
- The node's local segment lost its path to the controller (see the bridge
  section below).
- The node itself has failed (rare, but possible).

**Diagnostic steps:**

1. In Home Assistant, check the health monitor's diagnostic entities: **Nodes
   Online**, **Nodes Total**, and **Nodes Missing** (the last one names the
   missing node(s)). These are aggregate entities published by the health
   monitor device, so they survive Home Assistant restarts and reconnects.
   🔵 DESIGNED
2. Every node and bridge sends a heartbeat every 30 seconds. A node is
   declared "lost" after **3 missed heartbeats in a row — 90 seconds total**
   of silence. So a single missed heartbeat is not yet a fault; wait for the
   full 90 seconds before assuming a real problem. 🔵 DESIGNED (this timing
   rule is implemented and covered by automated logic tests, but has not been
   exercised against a real bench or field failure yet)
3. If Home Assistant confirms the node is lost, go physically check that
   node: is it powered? Is the CAN cable connector at its tap seated and
   undamaged?
4. If power and wiring at that node's tap look fine, check whether *other*
   nodes on the same physical run are also missing. Several nodes going
   missing together points at a shared cause — a wiring break upstream of all
   of them, or a dead bridge (see below) — rather than one bad node.

**Fix:**

- Loose or damaged CAN connector: reseat or repair it.
- No power at the node: trace back to the power source for that tap.
- Node genuinely dead (powered, wired correctly, still silent): it needs
  physical replacement — see [CAN node replacement](../hardware/can-node.md).

**When to escalate:** If checks 3–4 rule out power and wiring, or if you are
not confident opening up wall-mounted hardware, treat this as a hardware
question and go to [CAN node replacement](../hardware/can-node.md) rather
than guessing further.

---

## A button click, hold, or release isn't registering correctly

**Symptom:** A button seems unresponsive, double-fires, or a hold/release
gesture (e.g. hold-to-dim) doesn't behave as expected, even though the node
is shown as online.

**Likely causes:**

- Wiring fault on that specific button's connection inside the node (loose
  contact, damaged switch).
- The node is running an older firmware version than the rest of the fleet —
  button click/hold timing (including the 800 ms threshold before a press
  counts as a "hold") is baked into firmware at flash time and cannot be
  changed remotely. 🔵 DESIGNED
- This is very rarely a design fault in the gesture system itself — click,
  double-click, triple-click, hold, and hold-release are a well-defined,
  tested set of behaviors. Treat "one button acting up while everything else
  works" as a hardware or firmware-version problem on that node first.

**Diagnostic steps:**

1. Confirm the node is online (see the previous section).
2. Test the same physical button gesture on a *different* node of the same
   type. If it works fine elsewhere, the problem is local to this node or
   this specific button.
3. Check when this node was last reflashed compared to the rest of the
   fleet. Wall-button nodes have no WiFi and no over-the-air updates — they
   only get firmware changes when someone physically connects a USB cable
   and reflashes them, so it's easy for one node to silently fall behind.
4. If possible, open the node and check that specific button's wiring/switch
   for a loose or worn contact.

**Fix:**

- Firmware mismatch: reflash the node via USB with the current firmware.
- Wiring/switch fault: repair the connection, or replace the node if the
  switch itself has failed — see [CAN node replacement](../hardware/can-node.md).

**When to escalate:** If the button still misbehaves after confirming
firmware is current and wiring looks sound, escalate to
[CAN node replacement](../hardware/can-node.md).

---

## `ha_ready` reads false, or the system falls back to local relay control when it shouldn't

**Symptom:** Lights start behaving like Home Assistant is offline — simple
on/off only, no dimming, no scenes — even though Home Assistant looks fine
to you. Or a diagnostic entity called `ha_ready` shows `false`.

**What this actually means:** `ha_ready` is not a property of any single
button node — nodes don't know or care whether Home Assistant is reachable.
It's a readiness gate computed by the **lighting controller**, the device
that decides whether to hand a button press to Home Assistant (the rich
path: dimming, scenes, colour) or act on it immediately using its own local
relay logic (the resilient fallback path, so lights still work if Home
Assistant is down). This design exists specifically so the house keeps
working when Home Assistant can't be reached. 🔵 DESIGNED

The lighting controller only considers Home Assistant "ready" when **all**
of the following are true:

1. Its Home Assistant API connection is up.
2. Home Assistant has sent a fresh readiness heartbeat recently (within a
   configured timeout).
3. Home Assistant's reported binding-manifest hash matches the hash compiled
   into the controller — i.e. Home Assistant and the controller agree on
   what each button is supposed to do.

**Likely causes (in rough order of likelihood):**

- Home Assistant itself is down, restarting, or unreachable over the
  network.
- The lighting controller has lost network connectivity (Ethernet cable,
  switch port, DHCP/IP issue) — see [Network / Home Assistant](network.md).
- The binding manifest (`registry/bindings.yaml`, which defines what each
  button does) was changed and pushed to Home Assistant, but the lighting
  controller was never reflashed with the matching update — so the two
  sides' hashes disagree. This is a maintenance-process gap, not a fault.
- The readiness heartbeat automation in Home Assistant isn't running (e.g.
  the automation was disabled or deleted).

**Diagnostic steps:**

1. Check whether Home Assistant itself is reachable and healthy — this is
   the most common cause, and it is *not* a node or bus fault.
2. Check the lighting controller's network connectivity.
3. If both look fine, suspect a manifest-hash mismatch: was
   `registry/bindings.yaml` edited recently without reflashing the lighting
   controller?

**Fix:**

- Restore Home Assistant / network connectivity — `ha_ready` should recover
  automatically once the underlying condition clears.
- Manifest mismatch: regenerate and push the updated binding artifacts, then
  reflash the lighting controller so both sides agree again.

**When to escalate:** This is essentially never a reason to replace CAN
hardware — it's a connectivity or configuration problem upstream of the bus.
If Home Assistant and networking both check out and `ha_ready` still won't
recover, that's worth treating as a software/configuration investigation,
not a hardware one.

---

## A CAN bridge segment appears down

**Background:** The house's CAN bus is split into segments joined by small
bridge devices (`devices/bridge.yaml`) rather than one single wire run. A
bridge just forwards traffic between the segment it sits on and the rest of
the bus.

**Symptom:** Every node on one particular segment shows as missing/lost at
the same time, while nodes elsewhere are fine.

**What this actually means:** The bridge is deliberately built to fail
*safe*. It has a hardware watchdog and brownout detector, so if it ever
hangs, it reboots itself rather than getting stuck in a bad state. And if it
does fail, it's designed to go **silent** — it simply stops passing traffic —
rather than ever jamming or flooding the bus with garbage. 🔵 DESIGNED That's
why a dead bridge shows up as "one whole segment went quiet together," not
as chaos across the entire house.

If the bridge ever has to drop frames because its internal queue filled up,
it latches an `ERR_BRIDGE_QUEUE_OVERFLOW` marker in its own heartbeat, which
stays set until the bridge is power-cycled — so a transient overload leaves
a visible trace instead of silently going away. 🔵 DESIGNED

**Likely causes:**

- The bridge lost power.
- The bridge itself needs a reboot (the watchdog should already handle
  hangs, but a full power cycle is the simplest manual reset).
- A wiring fault between the bridge and that segment.

**Diagnostic steps:**

1. Confirm it really is "one segment, all at once" rather than scattered
   individual nodes — that pattern is the signature of a bridge problem, not
   a per-node problem.
2. Check the bridge device's own heartbeat/status if visible in Home
   Assistant, including whether the overflow marker above is set.
3. Physically check the bridge has power and its CAN connections (both the
   segment side and the backbone side) are intact.

**Fix:**

- Power-cycle the bridge — this also clears a latched overflow marker.
- Repair loose/damaged wiring at the bridge's connectors.

**When to escalate:** If the bridge has power, wiring looks fine, and a
power cycle doesn't bring the segment back, treat it as failed hardware —
see [CAN bridge replacement](../hardware/bridge.md). If instead individual
nodes scattered across *multiple* segments are missing (not one clean
segment), that points back to the [node](../hardware/can-node.md) or
[health monitor](../hardware/health-monitor.md) pages instead.
