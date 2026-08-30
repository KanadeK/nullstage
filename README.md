# NullStage

[![CI](https://github.com/KanadeK/nullstage/actions/workflows/ci.yml/badge.svg)](https://github.com/KanadeK/nullstage/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/KanadeK/nullstage)](https://github.com/KanadeK/nullstage/releases/latest)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-1f6b62)](https://www.python.org/)
[![MIT](https://img.shields.io/badge/license-MIT-d66f45)](LICENSE)

**Point the microphone's quiet side before rehearsal tells you where it should have gone.**

NullStage is an offline command-line preflight for microphone spill on small live stages and in rehearsal rooms. Give it a measured 2D stage, relative source levels, microphone positions, ideal polar patterns, and honest movement limits. It ranks the spill reaching every mic, searches only the declared physical envelope, and writes an auditable candidate plan.

[简体中文](README.zh-CN.md) · [Model](docs/model.md) · [Research](docs/research.md) · [Troubleshooting](docs/troubleshooting.md) · [Open the standalone demo report](docs/demo/report.html)

![NullStage optimized Harbor Room example with sources, baseline positions, aim arrows, and margin labels](docs/demo/stage.svg)

## The 60-second proof

Requires Python 3.11–3.14 and [`uv`](https://docs.astral.sh/uv/).

```powershell
git clone https://github.com/KanadeK/nullstage.git
cd nullstage
uv sync --dev --locked
uv run --no-sync nullstage optimize examples/live-band.json `
  --output-dir out/live-band `
  --fail-below-db 8
```

The committed fixture performs a real bounded search for three microphones. On v0.1.0 it evaluates 50–65 valid placements per mic and changes the worst target-to-spill margin from `5.66 dB` to `8.82 dB` while respecting each mic's movement, aim, and target-distance limits.

```text
Microphone                 Baseline   Candidate   Change
drum-overhead                 28.89       36.78     7.88 dB
guitar-close                  20.72       32.75    12.03 dB
lead-vocal                     5.66        8.82     3.16 dB

Worst margin: 5.66 -> 8.82 dB
Threshold 8.00 dB: PASS
```

The command writes:

- `report.json` — versioned machine evidence, every source contribution, positions, margins, and limitations;
- `stage.svg` — a standalone stage map with sources, baseline ghosts, candidate positions, and aim arrows;
- `report.html` — a script-free report that opens from disk and embeds the same stage map;
- terminal output — a compact gate for rehearsal notes and CI.

## What NullStage actually computes

```text
measured stage JSON
        ↓ strict boundary validation
relative source level - free-field distance loss + declared polar response
        ↓ power-summed unwanted sources
target-to-spill margin for every microphone
        ↓ bounded position × aim enumeration
ranked candidate with deterministic tie-breaking
        ↓
terminal + JSON + SVG + standalone HTML
```

The optimizer is not allowed to “solve” spill by putting a microphone on top of its target. Every microphone declares:

- maximum movement radius and position step;
- maximum aim change and angle step;
- minimum and maximum working distance from its target;
- an off-axis rejection floor instead of pretending an ideal null is infinitely quiet.

The baseline is always one candidate, so optimization cannot make a margin worse.

## Input contract

Coordinates are metres. `(0, 0)` is the downstage-left corner; positive `x` moves right on the report and positive `y` moves upstage. Angles are degrees counter-clockwise from positive `x`.

```json
{
  "schema_version": 1,
  "stage": {"name": "Quartet", "width_m": 10, "depth_m": 6},
  "sources": [
    {"id": "voice", "label": "Lead voice", "x_m": 5, "y_m": 1.6, "level_db": 0},
    {"id": "drums", "label": "Drum kit", "x_m": 7.5, "y_m": 4.6, "level_db": 12}
  ],
  "microphones": [
    {
      "id": "lead",
      "label": "Lead vocal mic",
      "target_source": "voice",
      "pattern": "cardioid",
      "off_axis_floor_db": -24,
      "x_m": 5,
      "y_m": 1.05,
      "aim_deg": 90,
      "search": {
        "move_radius_m": 0.5,
        "position_step_m": 0.25,
        "aim_range_deg": 30,
        "aim_step_deg": 15,
        "min_target_distance_m": 0.35,
        "max_target_distance_m": 0.9
      }
    }
  ]
}
```

Supported ideal patterns are `omni`, `cardioid`, `supercardioid`, `hypercardioid`, and `figure8`. A scenario needs at least two sources because a spill margin without an unwanted source is undefined.

## Analyze, optimize, and gate

```powershell
# Preserve the declared layout and explain its spill
uv run --no-sync nullstage analyze examples/live-band.json

# Search declared envelopes and write evidence to a new directory
uv run --no-sync nullstage optimize examples/live-band.json --output-dir out/optimized

# Produce the report but fail a policy threshold
uv run --no-sync nullstage analyze examples/crowded-rehearsal.json --fail-below-db 8

# Inspect the installed build
uv run --no-sync nullstage version
```

| Exit | Meaning | Next action |
|---:|---|---|
| `0` | Valid report; selected placements meet the optional threshold | Rehearse and measure the candidate |
| `1` | Valid report; one or more mics are below the threshold | Open the report and change the physical plan |
| `2` | Invalid JSON, unsafe output path, search explosion, or I/O failure | Apply the printed repair step and rerun |

NullStage never replaces an output directory. This makes a typo fail closed instead of overwriting earlier rehearsal evidence.

## Model boundary

NullStage uses a direct-field 2D estimate: relative source level at 1 m, `-20 log10(distance_m)`, an ideal first-order polar curve clamped to the mic's declared off-axis floor, power summation for spills, then `target - combined spill`.

It does **not** model reflections, room modes, barriers, phase, source directivity, frequency-dependent microphone behavior, proximity effect, performance movement, feedback, or absolute SPL. A higher margin is a better candidate under the declared model, not a guarantee of sound quality or safety. See [the model and its sources](docs/model.md).

## Failure and repair examples

```powershell
# Expected exit 1: valid evidence, deliberately impossible 8 dB policy
uv run --no-sync nullstage analyze examples/crowded-rehearsal.json --fail-below-db 8

# Expected exit 2: target source does not exist
uv run --no-sync nullstage analyze examples/invalid-unknown-target.json
```

For candidate-limit, existing-output, invalid-field, permission, and Windows `uv` cache repairs, see [Troubleshooting](docs/troubleshooting.md).

## Development acceptance

```powershell
uv sync --dev --locked
uv run --no-sync python scripts/check.py
```

The release gate covers format, lint, strict types, branch coverage, all three example outcomes, deterministic artifacts, package contents, a clean wheel install, and installed console exit codes. CI runs the same gate on Ubuntu/Python 3.11 and Windows/Python 3.14.

## Why another live-sound tool?

Stage-plot suites document where equipment is; hardware plugins reshape a specific microphone; acoustic simulators model rooms or arrays. NullStage makes a narrower decision inspectable: **given this small stage and these allowed physical moves, which direct source dominates each mic and which candidate geometry improves the declared target-to-spill margin?** The [research note](docs/research.md) records the comparison and search limits.

## License

MIT. NullStage does not bundle manufacturer polar data or microphone trademarks.

