from __future__ import annotations

import json

from nullstage.analysis import analyze_scenario
from nullstage.io import parse_scenario_text
from nullstage.optimize import optimize_scenario
from nullstage.report import build_analysis_bundle, build_optimization_bundle


def scenario_text() -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "stage": {"name": "Basement stage", "width_m": 8.0, "depth_m": 5.0},
            "sources": [
                {
                    "id": "voice",
                    "label": "Lead voice",
                    "x_m": 4.0,
                    "y_m": 4.0,
                    "level_db": 0.0,
                },
                {
                    "id": "drums",
                    "label": "Drum kit",
                    "x_m": 6.5,
                    "y_m": 1.5,
                    "level_db": 8.0,
                },
            ],
            "microphones": [
                {
                    "id": "lead",
                    "label": "Lead vocal mic",
                    "target_source": "voice",
                    "pattern": "cardioid",
                    "off_axis_floor_db": -24.0,
                    "x_m": 4.0,
                    "y_m": 3.5,
                    "aim_deg": 90.0,
                    "search": {
                        "move_radius_m": 0.5,
                        "position_step_m": 0.25,
                        "aim_range_deg": 30.0,
                        "aim_step_deg": 15.0,
                    },
                }
            ],
        }
    )


def test_analysis_bundle_is_deterministic_and_cross_format_consistent() -> None:
    scenario = parse_scenario_text(scenario_text())
    report = analyze_scenario(scenario)

    first = build_analysis_bundle(scenario, report, threshold_db=12.0)
    second = build_analysis_bundle(scenario, report, threshold_db=12.0)
    document = json.loads(first.json_text)

    assert first == second
    assert document["mode"] == "analyze"
    assert document["summary"]["microphone_count"] == 1
    assert document["threshold"]["requested_db"] == 12.0
    assert "lead" in first.svg_text
    assert "lead" in first.html_text
    assert f"{report.microphones[0].margin_db:.2f}" in first.html_text
    assert "direct-field 2D estimate" in first.terminal_text
    assert "NaN" not in first.json_text
    assert "Infinity" not in first.json_text


def test_optimization_bundle_reports_baseline_and_candidate_change() -> None:
    scenario = parse_scenario_text(scenario_text())
    report = optimize_scenario(scenario)

    bundle = build_optimization_bundle(scenario, report, threshold_db=None)
    document = json.loads(bundle.json_text)
    microphone = document["microphones"][0]

    assert document["mode"] == "optimize"
    assert microphone["baseline"]["margin_db"] <= microphone["optimized"]["margin_db"]
    assert microphone["change"]["evaluated_candidates"] > 1
    assert document["threshold"] is None
    assert "Baseline" in bundle.html_text
    assert "Candidate" in bundle.html_text
    assert "baseline" in bundle.svg_text
