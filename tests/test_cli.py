from __future__ import annotations

import json
from pathlib import Path

from nullstage.cli import main


def payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "stage": {"name": "CLI stage", "width_m": 8.0, "depth_m": 5.0},
        "sources": [
            {"id": "voice", "label": "Voice", "x_m": 4.0, "y_m": 4.0, "level_db": 0.0},
            {"id": "drums", "label": "Drums", "x_m": 6.5, "y_m": 1.5, "level_db": 8.0},
        ],
        "microphones": [
            {
                "id": "lead",
                "label": "Lead mic",
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
                    "min_target_distance_m": 0.25,
                    "max_target_distance_m": 1.0,
                },
            }
        ],
    }


def write_scenario(path: Path) -> None:
    path.write_text(json.dumps(payload()), encoding="utf-8")


def test_analyze_writes_complete_bundle(tmp_path: Path, capsys: object) -> None:
    source = tmp_path / "scenario.json"
    output = tmp_path / "report"
    write_scenario(source)

    exit_code = main(["analyze", str(source), "--output-dir", str(output)])

    assert exit_code == 0
    assert {path.name for path in output.iterdir()} == {"report.json", "stage.svg", "report.html"}
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["mode"] == "analyze"
    assert "Artifacts:" in capsys.readouterr().out  # type: ignore[attr-defined]


def test_threshold_failure_keeps_evidence_and_returns_one(tmp_path: Path) -> None:
    source = tmp_path / "scenario.json"
    output = tmp_path / "report"
    write_scenario(source)

    exit_code = main(
        [
            "analyze",
            str(source),
            "--output-dir",
            str(output),
            "--fail-below-db",
            "100",
        ]
    )

    assert exit_code == 1
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["threshold"]["failing_microphone_ids"] == ["lead"]


def test_invalid_input_returns_two_without_output(tmp_path: Path, capsys: object) -> None:
    source = tmp_path / "invalid.json"
    output = tmp_path / "report"
    invalid = payload()
    invalid["microphones"][0]["target_source"] = "missing"  # type: ignore[index]
    source.write_text(json.dumps(invalid), encoding="utf-8")

    exit_code = main(["analyze", str(source), "--output-dir", str(output)])

    assert exit_code == 2
    assert not output.exists()
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert "unknown target_source" in captured.err
    assert "Repair:" in captured.err


def test_existing_output_is_preserved_and_returns_two(tmp_path: Path, capsys: object) -> None:
    source = tmp_path / "scenario.json"
    output = tmp_path / "report"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    write_scenario(source)

    exit_code = main(["optimize", str(source), "--output-dir", str(output)])

    assert exit_code == 2
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert "already exists" in capsys.readouterr().err  # type: ignore[attr-defined]


def test_version_command(capsys: object) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "NullStage 0.1.0"  # type: ignore[attr-defined]
