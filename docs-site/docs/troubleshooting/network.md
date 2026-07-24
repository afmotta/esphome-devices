# Network / Home Assistant — Diagnose & Fix: Common Problems

This page covers general connectivity problems that aren't specific to any
one subsystem: a controller going offline in Home Assistant, firmware
updates over the network (OTA) failing, and Home Assistant failing to
discover or accept a device. If the device in question is otherwise working
fine and only a specific subsystem (climate, lighting, CAN bus) is
misbehaving, start on that subsystem's page instead — this page is for when
the device itself can't be reached at all.

!!! note "How to read the confidence tags on this page"
    This house-wide system has not been physically installed yet. 🟢
    VERIFIED = confirmed on a bench or in the field. 🔵 DESIGNED = built and
    intended to work this way, not yet proven against a real fault. ⚠️ KNOWN
    GAP = genuinely unresolved.

---

## A device shows offline / unavailable in Home Assistant

**Symptom:** A controller or device that normally reports to Home Assistant
shows as unavailable, greyed out, or simply stops updating.

**Likely causes:**

- The device's network link is down (Ethernet cable unplugged, switch port
  dead, WiFi out of range or credentials wrong).
- The device's IP address changed (if it's using DHCP rather than a fixed
  address, a router reboot or lease expiry can hand it a new address, which
  breaks anything pointing at the old one).
- The device has crashed or is stuck in a boot loop.
- Home Assistant itself is having a problem, not the device.

**Diagnostic steps:**

1. Confirm Home Assistant itself is healthy first — if *every* device shows
   offline at once, the problem is Home Assistant or your network as a
   whole, not any individual controller.
2. Check the physical network link on the specific device: Ethernet cable
   fully seated, link light on the switch/port active; or, for WiFi devices,
   signal strength and credentials.
3. If the device normally uses a fixed/static IP address, confirm it's still
   answering on that address. If it's using DHCP, check your router's
   client list for what address it currently holds — it may have changed.
4. If networking looks fine but the device still won't respond, it may be
   crashed or stuck; a power cycle is a reasonable next step.

**Fix:**

- Repair or reseat the physical network connection.
- If the IP address changed, update whatever references the old address (or
  move the device to a fixed/static IP so this doesn't recur — see
  [Getting Started](../setup.md) for initial network setup guidance).
- Power-cycle the device as a last resort if it appears crashed and a simple
  network fix doesn't bring it back.

**When to escalate:** If the device won't come back after a power cycle and
confirmed-good networking, and you can get physical access to it, check
whether it's responding at all on a direct USB/serial connection — if not,
this may be a hardware fault; see the matching page under Hardware Died
(start at [Which device died?](../hardware/index.md)).

---

## An OTA (over-the-air) firmware update fails

**Symptom:** Pushing a firmware update to a device from Home Assistant's
ESPHome integration fails partway through, times out, or the device doesn't
come back afterward.

**Likely causes:**

- The OTA password configured in the update tool doesn't match the
  password baked into the device's current firmware.
- The device isn't reachable on the network at the moment of the update
  (see the previous section).
- The device doesn't have enough free flash storage for the new firmware
  image.

**Diagnostic steps:**

1. Confirm the OTA password being used matches what's in the device's
   secrets/configuration — a mismatch here is one of the most common causes
   of a failed update and produces an authentication-style failure rather
   than a clean error.
2. Confirm the device is reachable on the network right now (see the
   previous section) — an update can't complete against a device that's
   already offline.
3. Check available flash space if the update log mentions storage or
   partition errors; this is more likely on older/smaller boards than on
   the current controller hardware.

**Fix:**

- Correct the OTA password so both sides agree.
- Resolve the underlying network-reachability problem first, then retry.
- If flash space is the issue, that typically means firmware has grown
  beyond what the board supports — this needs a firmware-size investigation,
  not just a retry.

**When to escalate:** If a device fails to come back after a failed OTA
update and normal network troubleshooting doesn't restore it, physical
access with a USB cable to reflash directly is the fallback — this is a
firmware-recovery situation, not a wiring one.

---

## Home Assistant can't discover or add a device

**Symptom:** A device that should be visible to Home Assistant's ESPHome
integration doesn't show up to be added, or an existing device that used to
work now refuses to reconnect after some kind of update.

**Likely causes — the most common one is a known encryption-scheme change:**

ESPHome version 2026.1.0 changed how devices authenticate to Home Assistant,
moving from a simple `api: password:` scheme to a stronger `api:
encryption:` scheme (an encryption key rather than a plain password). A
device that was originally added to Home Assistant under the **old**
password-based scheme, but has since been reflashed with firmware using the
**new** encryption-key scheme, will not silently keep working — Home
Assistant needs to be told about the change. This project's firmware targets
current ESPHome, so this specifically affects devices added to Home
Assistant a long time ago that haven't been re-added since.

**Diagnostic steps:**

1. Check whether the device in question was added to Home Assistant a long
   time ago (before the device's own firmware moved to encryption-based
   authentication) — this history mismatch is the signature of this
   specific problem.
2. Confirm basic network reachability first (see the first section on this
   page) — discovery can't work at all if the device isn't reachable.

**Fix:** Remove the old device entry from Home Assistant entirely and
re-add it from scratch, so Home Assistant picks up the current encryption
key rather than trying to reuse the old password-based credentials. See
[Getting Started](../setup.md) for the full walkthrough of adding a device
to Home Assistant, including where the encryption key comes from.

**When to escalate:** If a fresh delete-and-re-add doesn't work and basic
network reachability is confirmed, double check the encryption key
configured on the device actually matches what you're entering in Home
Assistant — a copy/paste mismatch here looks identical to a discovery
failure.
