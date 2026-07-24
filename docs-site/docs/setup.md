# Getting Started

This page walks a fresh computer, with nothing installed, all the way to being able to build ("compile") and install ("flash") this house's firmware, and read its logs. It gathers steps that are otherwise scattered across several files in the project's repository (its source-code storage folder, managed by a tool called git) into one place.

If you don't know what a "repository," "compile," or "flash" means yet, keep reading — each term is explained the first time it's used. If you already have a working setup and just want the day-to-day commands, jump to [Step 5](#step-5-day-to-day-commands).

!!! note "Who this page is for"
    This page assumes you're comfortable typing commands into a terminal (a text-based command window), but nothing more advanced than that. If you're standing next to failed hardware right now and don't need to set up a development computer, go to [Hardware Died](hardware/index.md) instead.

## Step 1: Install the prerequisites

You need four things on your computer before starting:

1. **git** — the tool that downloads and tracks changes to the project's code. On macOS, installing git also installs itself the first time you run `git` in a terminal (it will prompt you). On Linux, install it via your package manager (e.g. `sudo apt install git`).
2. **Python, version 3.12 or newer** — the language some of the project's helper tools are written in. Check your version with `python3 --version`.
3. **A C++ build toolchain (specifically, `g++`)** — needed to run this project's "native tests," small self-contained programs that check core logic without needing any ESPHome hardware tooling installed. On macOS this comes from installing Apple's Xcode Command Line Tools (`xcode-select --install`); on Linux, install `build-essential` (Debian/Ubuntu) or your distribution's equivalent.
4. **A text editor** — for editing configuration files, which are plain text (YAML format). Any editor works; VS Code is a common choice for this kind of project.

## Step 2: Clone the repository and set up your secrets file

"Cloning" means downloading a full working copy of the project, including its history.

1. Clone the repository:

    ```
    git clone git@github.com:afmotta/esphome-devices.git
    ```

    (If you haven't set up an SSH key with GitHub, use the HTTPS form instead: `git clone https://github.com/afmotta/esphome-devices.git`.)

2. Copy the secrets template to create your own, real secrets file:

    ```
    cp devices/secrets.yaml.example devices/secrets.yaml
    ```

    `devices/secrets.yaml` is **deliberately excluded from git** (it's "gitignored") — it holds real passwords and keys, and must never be committed or pushed. Only the `.example` template, with placeholder values, is tracked.

3. Open `devices/secrets.yaml` in your text editor and fill in each value. Here's what each one means:

    | Key | What it is | How to get a value |
    |---|---|---|
    | `wifi_ssid` / `wifi_password` | The house WiFi network name and password. Every device needs this, even devices that mainly use a wired Ethernet connection — it's used as a fallback. | Your actual WiFi credentials. |
    | `api_encryption_key` | A secret key that encrypts communication between the **lighting controller** and Home Assistant (the home-automation software this project integrates with). This is not a password you choose — it's a random key. | Generate one with `openssl rand -base64 32` in a terminal. |
    | `health_monitor_encryption_key` | The same kind of key, but for the **CAN bus health monitor** device specifically. It must be a *different* random value from `api_encryption_key` — each device gets its own key. | `openssl rand -base64 32` again — run it a second time for a new value. |
    | `encryption_key` | The same kind of key again, but shared by the **climate controller** and the standalone room/wall sensor devices. | `openssl rand -base64 32` — a third distinct value. |
    | `ota_password` | A password that protects "OTA" (over-the-air, i.e. wireless) firmware updates from being pushed to a device by anyone who isn't authorized. | `openssl rand -base64 32`, or any strong password. |
    | `github_username` / `github_pat` | Only needed if you'll use the GitHub-based production deployment method (`devices/remotes/`, explained in Step 5) — a GitHub username and a "personal access token" (a kind of password scoped to just what's needed) that lets a device pull its own configuration directly from GitHub. | Create a token in your GitHub account settings under Developer Settings → Personal Access Tokens. |

    Every ESPHome device should get its own distinct encryption key — never reuse one key across devices. Each `openssl rand -base64 32` command prints a new random 32-byte value encoded as text; run it once per key you need to fill in.

## Step 3: Install ESPHome, pinned to the right version

ESPHome is the framework that turns the project's YAML configuration files into real firmware for the ESP32 microcontrollers used throughout the house. Install the exact version this repository is built and tested against:

```
pip install "esphome==2026.7.0"
```

A few notes on why this specific version matters:

- The project pins `esphome==2026.7.0` deliberately in `climate/tests/pyproject.toml`. 🟢 This is the only version that has been verified end-to-end for the main controller build paths (the climate controller and the CAN bus node firmware).
- Individual hardware definitions ("boards") in the repository declare their own minimum ESPHome version, ranging from 2026.3.0 up to 2026.7.0 depending on the board. 🟢 But 2026.7.0 is the version to actually install — it satisfies every board's floor and is the one this project's own tests run against.

!!! warning "Intel Mac caveat"
    🟢 If you're on an **Intel-based (x86_64) Mac** specifically, installing `esphome==2026.7.0` can conflict with `esptool` (a tool ESPHome depends on for flashing): ESPHome 2026.7.0 pins a security library (`cryptography==49.0.0`) that `esptool 5.3.1` refuses to accept on that platform. This is a real, confirmed conflict — not a hypothetical one — but it's specific to Intel macOS. If you're on an **Apple Silicon (M-series/arm64) Mac** or on **Linux**, this doesn't affect you; those are the two environments this project actually develops and tests on. If you're stuck on an Intel Mac, ask whoever maintains this repository for the current workaround before spending time on it yourself.

## Step 4: Smoke-test your environment

Before touching real hardware, confirm your setup actually works using the project's built-in verification script.

1. First, run the "native-only" subset. This works even *before* ESPHome is installed, because it only exercises the plain Python and C++ test programs (no ESPHome build tooling needed):

    ```
    bash scripts/verification-battery.sh --native-only
    ```

2. Once ESPHome is installed (Step 3), run the full battery, which additionally validates and compiles real device configurations:

    ```
    bash scripts/verification-battery.sh
    ```

Both commands print a PASS/FAIL summary line per check, and on failure show you the last 50 lines of the relevant log. 🟢 If either command fails on a fresh checkout with no local changes, something is wrong with your environment setup, not with the project — recheck Steps 1–3 before going further.

!!! note
    The full battery includes a check that regenerates certain auto-generated files and expects a byte-for-byte match against what's already committed. It requires your working copy to have no uncommitted changes under `canbus/`, `climate/`, or `registry/` before you run it — commit or stash first if you've been editing.

## Step 5: Day-to-day commands

Once your environment is set up, here are the commands you'll use routinely. All of them are run from the root of the repository.

| Command | What it does |
|---|---|
| `esphome config devices/locals/climate-control.yaml` | **Validates only** — checks the configuration for errors without building firmware. Fast; use it first when you've changed something. |
| `esphome compile devices/locals/climate-control.yaml` | **Builds** the firmware into a binary file, without installing it anywhere. Useful to confirm something compiles before flashing. |
| `esphome run devices/locals/climate-control.yaml --device /dev/ttyUSB0` | Builds **and installs** ("flashes") the firmware onto a device connected by USB cable. The `--device` path tells it which USB port to use (this varies by computer and cable — `/dev/ttyUSB0` is a typical Linux example; on macOS it looks more like `/dev/cu.usbserial-XXXX`). **You only need this over-USB step once per physical device** — after that first flash, later updates can go out wirelessly ("OTA," over-the-air). |
| `esphome logs devices/locals/climate-control.yaml` | Connects to a running device and streams its live log output to your terminal — the main way to watch what a device is doing in real time. |

### `devices/locals/` vs. `devices/remotes/`

You'll notice two different folders with similar-looking files:

- **`devices/locals/*.yaml`** — configurations you build yourself, on your own computer, using the commands above. This is what you use for development, testing, and any USB-cable flash.
- **`devices/remotes/*.yaml`** — production configurations that don't contain the actual firmware definition directly; instead they tell ESPHome to pull it straight from GitHub (`github://...`). These are deployed differently: through the Home Assistant ESPHome add-on, by clicking **"Install"** on the device's card. No laptop or terminal is needed for that path, once a device has already been provisioned this way — which makes it the right choice for routine updates to a device that's already living in a wall.

!!! note "Not every device has both variants yet"
    As of today, **only the climate controller** has both a `devices/locals/climate-control.yaml` and a `devices/remotes/climate-control.yaml`. The lighting controller does not — there is no `devices/locals/light-controller.yaml` or `devices/remotes/light-controller.yaml`. If you're working on the lighting controller, compile its entry-point file directly instead: `devices/light-controller.yaml`. Don't assume every device follows the climate controller's two-variant pattern; check what actually exists in the `devices/` folder first.

## A gotcha worth knowing about

!!! warning "Re-provisioning a device after an authentication scheme change"
    🟢 ESPHome version 2026.1.0 removed an older way devices authenticate to Home Assistant (`api: password:`) in favor of a newer, encrypted scheme (`api: encryption:`, the one this project uses — see `api_encryption_key` etc. in Step 2). If you're re-flashing a device that was originally set up in Home Assistant under the old password scheme, Home Assistant **will not accept** the new encryption key against that old registration. You must first **delete the device from Home Assistant** (Settings → Devices & Services → ESPHome) and then **re-add it** using the new encryption key. Simply reflashing the device and leaving its old Home Assistant entry in place will not work.

## Where to go next

- Ready to check whether the system is behaving normally day to day? See [Everyday Monitoring](monitoring.md).
- Setting up a brand-new physical device for the first time, or replacing a dead one? See [Hardware Died](hardware/index.md) for the device-specific procedure.
- Need to look up an unfamiliar term? See the [Glossary](reference/glossary.md).
