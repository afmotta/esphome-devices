# Contributing

This repository is a layered ESPHome monorepo. Start from the root `CLAUDE.md`, then read the owning subsystem guide before editing inside `canbus/`, `lighting/`, or `climate/`. Shared packages under top-level `packages/` are cross-system infrastructure and should stay generic.

## Secrets

Never commit real ESPHome secrets. Local secret files such as `secrets.yaml` are ignored and may exist on a deployment machine, but tracked files must use `!secret` references or `.example` placeholders.

Before committing, run:

```bash
python3 scripts/check_repo_hygiene.py
```

If a real secret file was ever pushed, rotate the affected credential before reflashing or sharing the repo.

## Logging

Deployable configs use the `logger_level` substitution. The default is `INFO`.

Use a local wrapper override while debugging:

```yaml
substitutions:
  logger_level: DEBUG
```

Do not hardcode production `logger.level: DEBUG` in device, board, or node packages. The verification battery checks this.

## Registry Workflow

The registry is the house system of record. After editing `registry/nodes.csv` or `registry/bindings.yaml`:

```bash
python3 canbus/tools/generate_nodes.py
python3 canbus/tests/test_generate_exports.py
git diff -- canbus climate registry
```

Commit the registry edit and generated artifacts together. Before reflashing a controller, push the commit and run:

```bash
python3 canbus/tools/check_registry_pushed.py
```

## Verification

For a fast local gate that does not need ESPHome:

```bash
bash scripts/verification-battery.sh --native-only
```

For deploy-affecting changes on a machine with ESPHome 2026.6.5 and the HVAC package test dependencies:

```bash
bash scripts/verification-battery.sh
```

The generator idempotence step requires tracked files under `canbus/`, `climate/`, and `registry/` to be clean before it runs. Commit or stash in-progress changes first.

## Git Hygiene

Stage specific files only. Avoid `git add .` because this repo has local deployment files and ESPHome build output nearby.

Good pattern:

```bash
git status --short
git add path/to/file1 path/to/file2
git diff --staged
```
