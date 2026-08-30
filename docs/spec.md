# Spec: NullStage v0.1.0

## Objective

NullStage is an offline command-line planner for small live stages and rehearsal rooms. It reads a measured 2D stage, fixed sound sources, and microphones, then estimates each microphone's direct target-to-spill margin from relative source level, free-field distance loss, and an ideal first-order polar pattern. It can search a declared movement/aim envelope and produce a better, auditable candidate layout.

The primary user is a musician, volunteer sound engineer, or small venue that needs to answer “which source is leaking into which mic, and which allowed move or rotation improves the geometry?” before rehearsal. Success means a real JSON scenario becomes deterministic terminal, JSON, SVG, and self-contained HTML evidence; invalid or below-threshold plans fail with documented exit codes.

NullStage is a geometry preflight, not room-acoustics simulation, a microphone database, feedback certification, or a substitute for listening and measurement. It ignores reflections, frequency-dependent polar response, phase, room modes, wind, barriers, mic self-noise, proximity effect, and loudspeaker directivity.

## Tech Stack

- CPython 3.11–3.14.
- Standard-library-only runtime (`argparse`, `dataclasses`, `json`, `math`, `pathlib`).
- Hatchling build backend.
- Pytest, pytest-cov, Ruff, mypy, and `uv audit` as development/release gates.
- GitHub Actions on Ubuntu/Python 3.11 and Windows/Python 3.14.

## Commands

```powershell
# One-time environment synchronization
uv sync --dev --locked

# Analyze the declared layout without changing it
uv run --no-sync nullstage analyze examples/live-band.json --output-dir out/analyze

# Search each microphone's declared movement and aim envelope
uv run --no-sync nullstage optimize examples/live-band.json --output-dir out/optimize

# Turn the result into a policy gate
uv run --no-sync nullstage analyze examples/live-band.json --fail-below-db 8

# Focused and full verification
uv run --no-sync pytest tests/test_model.py --basetemp=.tmp/pytest-model -p no:cacheprovider
uv run --no-sync python scripts/check.py
```

Exit codes:

- `0`: valid report and every microphone meets the optional threshold.
- `1`: valid report, but at least one microphone is below `--fail-below-db`.
- `2`: invalid input, unsafe output collision, or command/I/O failure.

## Project Structure

```text
src/nullstage/       -> domain model, scoring, optimizer, reports, CLI
tests/               -> unit, integration, CLI, and deterministic-output tests
examples/            -> one useful scenario and explicit failure fixtures
docs/                -> model, research, troubleshooting, and generated preview
tasks/               -> implementation plan and progress checklist
scripts/check.py      -> release-equivalent local gate
.github/workflows/   -> cross-platform CI and tagged-release automation
```

## Code Style

Use typed, immutable domain values and direct functions. Validate only at the JSON/CLI boundary; internal functions trust constructed domain objects and fail loudly on broken invariants.

```python
@dataclass(frozen=True, slots=True)
class Point:
    x_m: float
    y_m: float


def distance_m(left: Point, right: Point) -> float:
    return math.hypot(left.x_m - right.x_m, left.y_m - right.y_m)
```

Names include units (`distance_m`, `margin_db`). JSON keys are stable snake_case. Sorting is explicit anywhere input order should not affect output.

## Testing Strategy

- Unit tests: polar sensitivity, angle normalization, distance loss, power summation, ranking, and deterministic tie-breaking.
- Integration tests: parse a real scenario, analyze, optimize, and prove the optimized plan does not reduce any microphone's margin.
- CLI tests: output bundle, exit codes `0/1/2`, input/output collision, malformed and out-of-bounds scenarios.
- Property/exhaustive cross-check: compare optimizer output to an independent enumeration on a small fixture.
- Release gate: Ruff format/check, strict mypy, 90% branch coverage, examples, reproducibility, wheel/sdist inspection, clean wheel install, and installed console execution.

## Boundaries

- Always: stay offline at runtime; validate external JSON; cap stage/source/microphone/candidate counts; make approximations visible; produce deterministic output; preserve input files.
- Ask first: change the public schema or exit-code contract after release; add runtime dependencies; add measured manufacturer microphone data; add a 3D or room-reflection model.
- Never: claim a real-world safety, feedback, or recording-quality guarantee; infer actual SPL from relative levels; overwrite an input file; send scenarios to a service; hide threshold failure behind exit code 0.

## Success Criteria

1. A valid scenario produces terminal, JSON, SVG, and standalone HTML reports using the installed CLI.
2. Optimization searches only declared envelopes, uses deterministic tie-breaking, and proves the included live-band fixture improves its worst microphone margin.
3. Invalid references, duplicate IDs, non-finite numbers, out-of-stage positions, candidate explosions, and output collisions fail with exit code 2 and repair-oriented messages.
4. `--fail-below-db` returns exit code 1 without suppressing the report.
5. The full local gate passes with at least 90% branch coverage and no skipped tests.
6. GitHub CI passes on both declared platforms; an annotated `v0.1.0` tag and public non-draft Release contain the wheel, sdist, example bundle, and checksums.
7. A clean environment installs a downloaded release wheel and reproduces the example; only the intended GitHub account appears as contributor; Gmail notification is sent after remote verification.

## Open Questions

No blocking product question remains. The user explicitly authorized independent concept selection and the full repository-to-release lifecycle. The idealized model and its limitations are accepted as v0.1 scope and must remain prominent in every report.
