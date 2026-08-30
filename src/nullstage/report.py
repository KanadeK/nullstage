"""Canonical JSON data and human-readable NullStage reports."""

from __future__ import annotations

import html
import json
import math
from dataclasses import dataclass
from typing import Any

from nullstage import __version__
from nullstage.analysis import AnalysisReport, Contribution, MicrophoneAnalysis
from nullstage.model import Point, Scenario
from nullstage.optimize import OptimizationReport

MODEL_LIMITATIONS = (
    "direct paths only; reflections, room modes, phase, and barriers are not modeled",
    "source levels are relative dB at 1 m, not measured or predicted SPL",
    "polar patterns are ideal first-order curves clamped to each declared off-axis floor",
    "frequency response, proximity effect, movement during performance, "
    "and feedback are not modeled",
)


@dataclass(frozen=True, slots=True)
class OutputBundle:
    json_text: str
    svg_text: str
    html_text: str
    terminal_text: str
    failing_microphone_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _VisualMicrophone:
    microphone_id: str
    label: str
    baseline: MicrophoneAnalysis
    candidate: MicrophoneAnalysis | None


def _rounded(value: float) -> float:
    return round(value, 6)


def _point_document(point: Point) -> dict[str, float]:
    return {"x_m": _rounded(point.x_m), "y_m": _rounded(point.y_m)}


def _contribution_document(contribution: Contribution) -> dict[str, Any]:
    return {
        "source_id": contribution.source_id,
        "source_label": contribution.source_label,
        "level_db": _rounded(contribution.level_db),
        "distance_m": _rounded(contribution.distance_m),
        "incidence_deg": _rounded(contribution.incidence_deg),
        "directivity_db": _rounded(contribution.directivity_db),
    }


def _placement_document(analysis: MicrophoneAnalysis) -> dict[str, Any]:
    return {
        "position": _point_document(analysis.position),
        "aim_deg": _rounded(analysis.aim_deg),
        "target": _contribution_document(analysis.target),
        "spills": [_contribution_document(spill) for spill in analysis.spills],
        "combined_spill_db": _rounded(analysis.combined_spill_db),
        "margin_db": _rounded(analysis.margin_db),
    }


def _base_document(scenario: Scenario, mode: str) -> dict[str, Any]:
    return {
        "report_schema_version": 1,
        "tool": {"name": "NullStage", "version": __version__},
        "mode": mode,
        "model": {
            "name": "direct-field-2d",
            "distance_rule": "source_level_db - 20 * log10(distance_m)",
            "polar_rule": "ideal first-order response clamped to off_axis_floor_db",
            "limitations": list(MODEL_LIMITATIONS),
        },
        "stage": {
            "name": scenario.stage.name,
            "width_m": _rounded(scenario.stage.width_m),
            "depth_m": _rounded(scenario.stage.depth_m),
        },
        "sources": [
            {
                "id": source.id,
                "label": source.label,
                "position": _point_document(source.position),
                "level_db": _rounded(source.level_db),
            }
            for source in sorted(scenario.sources, key=lambda item: item.id)
        ],
    }


def _threshold_document(
    threshold_db: float | None, microphone_margins: tuple[tuple[str, float], ...]
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if threshold_db is None:
        return None, ()
    failing = tuple(
        microphone_id for microphone_id, margin_db in microphone_margins if margin_db < threshold_db
    )
    return (
        {
            "requested_db": _rounded(threshold_db),
            "failing_microphone_ids": list(failing),
        },
        failing,
    )


def _json_text(document: dict[str, Any]) -> str:
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )


def build_analysis_bundle(
    scenario: Scenario,
    report: AnalysisReport,
    *,
    threshold_db: float | None,
) -> OutputBundle:
    document = _base_document(scenario, "analyze")
    microphone_documents = [
        {
            "id": microphone.microphone_id,
            "label": microphone.microphone_label,
            "pattern": microphone.pattern,
            "off_axis_floor_db": _rounded(microphone.off_axis_floor_db),
            "baseline": _placement_document(microphone),
        }
        for microphone in report.microphones
    ]
    threshold, failing = _threshold_document(
        threshold_db,
        tuple(
            (microphone.microphone_id, microphone.margin_db) for microphone in report.microphones
        ),
    )
    document["summary"] = {
        "status": "below_threshold" if failing else "pass",
        "microphone_count": len(report.microphones),
        "worst_margin_db": _rounded(report.worst_margin_db),
    }
    document["microphones"] = microphone_documents
    document["threshold"] = threshold
    visuals = tuple(
        _VisualMicrophone(
            microphone_id=microphone.microphone_id,
            label=microphone.microphone_label,
            baseline=microphone,
            candidate=None,
        )
        for microphone in report.microphones
    )
    svg_text = _render_svg(scenario, visuals, mode="analyze")
    return OutputBundle(
        json_text=_json_text(document),
        svg_text=svg_text,
        html_text=_render_html(document, svg_text),
        terminal_text=_render_terminal(document),
        failing_microphone_ids=failing,
    )


def build_optimization_bundle(
    scenario: Scenario,
    report: OptimizationReport,
    *,
    threshold_db: float | None,
) -> OutputBundle:
    document = _base_document(scenario, "optimize")
    microphone_documents = [
        {
            "id": item.microphone_id,
            "label": item.baseline.microphone_label,
            "pattern": item.baseline.pattern,
            "off_axis_floor_db": _rounded(item.baseline.off_axis_floor_db),
            "baseline": _placement_document(item.baseline),
            "optimized": _placement_document(item.optimized),
            "change": {
                "improvement_db": _rounded(item.improvement_db),
                "movement_m": _rounded(item.movement_m),
                "rotation_deg": _rounded(item.rotation_deg),
                "evaluated_candidates": item.evaluated_candidates,
            },
        }
        for item in report.microphones
    ]
    threshold, failing = _threshold_document(
        threshold_db,
        tuple((item.microphone_id, item.optimized.margin_db) for item in report.microphones),
    )
    document["summary"] = {
        "status": "below_threshold" if failing else "pass",
        "microphone_count": len(report.microphones),
        "baseline_worst_margin_db": _rounded(report.baseline_worst_margin_db),
        "optimized_worst_margin_db": _rounded(report.optimized_worst_margin_db),
    }
    document["microphones"] = microphone_documents
    document["threshold"] = threshold
    visuals = tuple(
        _VisualMicrophone(
            microphone_id=item.microphone_id,
            label=item.baseline.microphone_label,
            baseline=item.baseline,
            candidate=item.optimized,
        )
        for item in report.microphones
    )
    svg_text = _render_svg(scenario, visuals, mode="optimize")
    return OutputBundle(
        json_text=_json_text(document),
        svg_text=svg_text,
        html_text=_render_html(document, svg_text),
        terminal_text=_render_terminal(document),
        failing_microphone_ids=failing,
    )


def _margin_color(margin_db: float) -> str:
    if margin_db >= 12.0:
        return "#1f9d70"
    if margin_db >= 6.0:
        return "#d08b24"
    return "#c44b4b"


def _render_svg(
    scenario: Scenario, microphones: tuple[_VisualMicrophone, ...], *, mode: str
) -> str:
    canvas_width = 960.0
    scale = min(800.0 / scenario.stage.width_m, 440.0 / scenario.stage.depth_m)
    stage_width = scenario.stage.width_m * scale
    stage_height = scenario.stage.depth_m * scale
    left = (canvas_width - stage_width) / 2.0
    top = 116.0 + (440.0 - stage_height) / 2.0

    def canvas(point: Point) -> tuple[float, float]:
        return (
            left + point.x_m * scale,
            top + (scenario.stage.depth_m - point.y_m) * scale,
        )

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 640" role="img" '
        f'aria-label="NullStage {html.escape(mode)} report">',
        "<style>text{font-family:Segoe UI,Arial,sans-serif}.label{font-size:14px;fill:#18202a}"
        ".small{font-size:12px;fill:#586473}.title{font-size:28px;font-weight:700;fill:#15263a}"
        ".stage{fill:#f7f3e9;stroke:#283d4f;stroke-width:2}.grid{stroke:#d9d3c6;stroke-width:1}"
        ".baseline{fill:none;stroke:#7e8791;stroke-width:2;stroke-dasharray:5 4}</style>",
        '<rect width="960" height="640" fill="#edf2f1"/>',
        f'<text x="60" y="50" class="title">{html.escape(scenario.stage.name)}</text>',
        f'<text x="60" y="78" class="small">NullStage {html.escape(mode)} · '
        "direct-field 2D estimate · stage front is at the bottom</text>",
        f'<rect class="stage" x="{left:.2f}" y="{top:.2f}" width="{stage_width:.2f}" '
        f'height="{stage_height:.2f}" rx="8"/>',
        f'<text x="{left:.2f}" y="{top - 12:.2f}" class="small">UPSTAGE</text>',
        f'<text x="{left:.2f}" y="{top + stage_height + 24:.2f}" class="small">STAGE FRONT</text>',
    ]
    for source in sorted(scenario.sources, key=lambda item: item.id):
        x, y = canvas(source.position)
        parts.extend(
            [
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="10" fill="#e7684b" '
                'stroke="#712d22" stroke-width="2"/>',
                f'<text x="{x + 14:.2f}" y="{y - 6:.2f}" class="label">'
                f"{html.escape(source.id)}</text>",
                f'<text x="{x + 14:.2f}" y="{y + 11:.2f}" class="small">'
                f"{source.level_db:.1f} dB @ 1 m</text>",
            ]
        )
    for visual in microphones:
        selected = visual.baseline if visual.candidate is None else visual.candidate
        if visual.candidate is not None:
            baseline_x, baseline_y = canvas(visual.baseline.position)
            candidate_x, candidate_y = canvas(visual.candidate.position)
            parts.extend(
                [
                    f'<circle id="{html.escape(visual.microphone_id)}-baseline" '
                    f'class="baseline" cx="{baseline_x:.2f}" cy="{baseline_y:.2f}" r="9"/>',
                    f'<line class="baseline" x1="{baseline_x:.2f}" y1="{baseline_y:.2f}" '
                    f'x2="{candidate_x:.2f}" y2="{candidate_y:.2f}"/>',
                ]
            )
        x, y = canvas(selected.position)
        angle = math.radians(selected.aim_deg)
        arrow_x = x + math.cos(angle) * 34.0
        arrow_y = y - math.sin(angle) * 34.0
        color = _margin_color(selected.margin_db)
        parts.extend(
            [
                f'<g id="{html.escape(visual.microphone_id)}">',
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="10" fill="{color}" '
                'stroke="#173042" stroke-width="2"/>',
                f'<line x1="{x:.2f}" y1="{y:.2f}" x2="{arrow_x:.2f}" y2="{arrow_y:.2f}" '
                f'stroke="{color}" stroke-width="4" stroke-linecap="round"/>',
                f'<text x="{x + 14:.2f}" y="{y - 6:.2f}" class="label">'
                f"{html.escape(visual.microphone_id)}</text>",
                f'<text x="{x + 14:.2f}" y="{y + 11:.2f}" class="small">'
                f"{selected.margin_db:.2f} dB margin</text>",
                "</g>",
            ]
        )
    parts.extend(
        [
            '<circle cx="660" cy="600" r="7" fill="#e7684b"/><text x="674" y="604" '
            'class="small">source</text>',
            '<circle cx="750" cy="600" r="7" fill="#1f9d70"/><text x="764" y="604" '
            'class="small">microphone / margin</text>',
            "</svg>\n",
        ]
    )
    return "".join(parts)


def _render_terminal(document: dict[str, Any]) -> str:
    mode = str(document["mode"])
    stage = document["stage"]
    summary = document["summary"]
    microphones = document["microphones"]
    lines = [
        f"NullStage {mode} — {stage['name']}",
        "Model: direct-field 2D estimate; verify the candidate by listening and measurement.",
        "",
    ]
    if mode == "analyze":
        lines.append("Microphone                 Target dB   Spill dB   Margin dB")
        for microphone in microphones:
            baseline = microphone["baseline"]
            lines.append(
                f"{microphone['id']:<26} {baseline['target']['level_db']:>9.2f} "
                f"{baseline['combined_spill_db']:>10.2f} {baseline['margin_db']:>11.2f}"
            )
        lines.append(f"\nWorst margin: {summary['worst_margin_db']:.2f} dB")
    else:
        lines.append("Microphone                 Baseline   Candidate   Change")
        for microphone in microphones:
            lines.append(
                f"{microphone['id']:<26} {microphone['baseline']['margin_db']:>8.2f} "
                f"{microphone['optimized']['margin_db']:>11.2f} "
                f"{microphone['change']['improvement_db']:>8.2f} dB"
            )
        lines.append(
            f"\nWorst margin: {summary['baseline_worst_margin_db']:.2f} -> "
            f"{summary['optimized_worst_margin_db']:.2f} dB"
        )
    threshold = document["threshold"]
    if threshold is not None:
        failing = threshold["failing_microphone_ids"]
        status = "PASS" if not failing else f"BELOW THRESHOLD: {', '.join(failing)}"
        lines.append(f"Threshold {threshold['requested_db']:.2f} dB: {status}")
    return "\n".join(lines) + "\n"


def _render_html(document: dict[str, Any], svg_text: str) -> str:
    mode = str(document["mode"])
    stage = document["stage"]
    microphones = document["microphones"]
    if mode == "analyze":
        header = "<th>Microphone</th><th>Pattern</th><th>Target</th><th>Spill</th><th>Margin</th>"
        rows = "".join(
            "<tr>"
            f"<td><code>{html.escape(microphone['id'])}</code><br>{html.escape(microphone['label'])}</td>"
            f"<td>{html.escape(microphone['pattern'])}</td>"
            f"<td>{microphone['baseline']['target']['level_db']:.2f} dB</td>"
            f"<td>{microphone['baseline']['combined_spill_db']:.2f} dB</td>"
            f"<td><strong>{microphone['baseline']['margin_db']:.2f} dB</strong></td>"
            "</tr>"
            for microphone in microphones
        )
    else:
        header = (
            "<th>Microphone</th><th>Pattern</th><th>Baseline</th><th>Candidate</th>"
            "<th>Change</th><th>Search</th>"
        )
        rows = "".join(
            "<tr>"
            f"<td><code>{html.escape(microphone['id'])}</code><br>{html.escape(microphone['label'])}</td>"
            f"<td>{html.escape(microphone['pattern'])}</td>"
            f"<td>{microphone['baseline']['margin_db']:.2f} dB</td>"
            f"<td><strong>{microphone['optimized']['margin_db']:.2f} dB</strong></td>"
            f"<td>+{microphone['change']['improvement_db']:.2f} dB</td>"
            f"<td>{microphone['change']['evaluated_candidates']} candidates</td>"
            "</tr>"
            for microphone in microphones
        )
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in MODEL_LIMITATIONS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NullStage · {html.escape(stage["name"])}</title>
<style>
:root{{--ink:#172536;--muted:#617080;--paper:#fffdf8;--accent:#167c68}}
*{{box-sizing:border-box}}
body{{margin:0;background:#e7efed;color:var(--ink);font:16px/1.5 Segoe UI,Arial,sans-serif}}
main{{max-width:1100px;margin:auto;padding:36px 24px 64px}}
h1{{margin:0;font-size:clamp(2rem,5vw,4rem);letter-spacing:-.04em}}
.eyebrow{{color:var(--accent);font-weight:700;text-transform:uppercase;letter-spacing:.12em}}
.card{{background:var(--paper);border:1px solid #cad6d3;border-radius:18px}}
.card{{box-shadow:0 14px 40px #1f493e18;margin-top:24px;overflow:hidden}}
.pad{{padding:24px}}
.notice{{border-left:5px solid #db9634;background:#fff5df;padding:16px 18px;margin-top:22px}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:12px 14px;text-align:left;border-bottom:1px solid #e1e7e5}}
th{{color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.08em}}
code{{font-family:Cascadia Code,Consolas,monospace}}
svg{{display:block;width:100%;height:auto}}
ul{{margin-bottom:0}}
</style>
</head>
<body><main>
<div class="eyebrow">NullStage · {html.escape(mode)}</div>
<h1>{html.escape(stage["name"])}</h1>
<p>Measured geometry in. Ranked spill evidence out.</p>
<div class="notice">
<strong>Planning estimate, not acoustic certification.</strong>
Verify every candidate by listening and measurement in the real room.
</div>
<section class="card">{svg_text}</section>
<section class="card pad">
<h2>{"Baseline" if mode == "analyze" else "Baseline → Candidate"}</h2>
<div style="overflow:auto"><table><thead><tr>{header}</tr></thead>
<tbody>{rows}</tbody></table></div>
</section>
<section class="card pad"><h2>Model boundary</h2><ul>{limitations}</ul></section>
</main></body></html>
"""
