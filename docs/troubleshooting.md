# Troubleshooting and repair flow

NullStage has three exit classes. Keep the first failing command and repair only its named cause.

## Exit 1: the report is valid but below policy

```powershell
uv run --no-sync nullstage analyze examples/crowded-rehearsal.json --fail-below-db 8
```

Open the emitted report if `--output-dir` was supplied. The first spill row is the strongest declared contributor. Change measured geometry, aim, pattern/floor evidence, source level, or the allowed envelope; do not lower the threshold merely to make the command green.

## Exit 2: unknown target or invalid field

Example message:

```text
error: microphones[0].target_source references unknown target_source: missing-source
Repair: Repair the named field in the scenario JSON, then rerun the same command.
```

IDs are exact and case-sensitive. Every microphone target must name one item in `sources`.

## Exit 2: baseline target distance is outside the search contract

The declared baseline must already satisfy `min_target_distance_m..max_target_distance_m`. Either correct the measured baseline position or correct the physical working-distance bounds. Do not expand them just to admit an impossible setup.

## Exit 2: candidate limit exceeded

Each microphone may evaluate at most 50,000 candidates. Increase `position_step_m` or `aim_step_deg`, or reduce `move_radius_m` / `aim_range_deg`. NullStage reports the upper bound before performing the search.

## Exit 2: output directory already exists

NullStage never overwrites report directories. Choose a new evidence path:

```powershell
uv run --no-sync nullstage optimize examples/live-band.json --output-dir out/rehearsal-02
```

Delete or archive the old directory yourself only after deciding its evidence is no longer needed.

## `uv` cannot initialize the Windows global cache

The repository includes `uv.toml` with a project-local `.uv-cache`. Run from the repository root:

```powershell
uv sync --dev --locked
uv run --no-sync python scripts/check.py
```

Do not remove the lock file or use `--no-lock`; a changed dependency set is not the same release input.

## Dependency or audit network failure

`uv sync` and `uv audit --locked` need package-index/OSV network access. A socket or DNS failure is an environment failure, not a passing audit. Restore network access and rerun the same gate. The runtime CLI itself is offline and dependency-free.

## Installed command is missing

From a checkout, resynchronize the editable package:

```powershell
uv sync --dev --locked
uv run --no-sync nullstage version
```

For a Release asset, install the wheel into a clean environment and run the generated console script. Do not test an unrelated globally installed copy.
