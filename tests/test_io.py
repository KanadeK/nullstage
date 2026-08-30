from __future__ import annotations

import json

import pytest

from nullstage.io import ScenarioError, parse_scenario_text


def valid_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "stage": {"name": "Club stage", "width_m": 8.0, "depth_m": 5.0},
        "sources": [
            {"id": "voice", "label": "Lead voice", "x_m": 4.0, "y_m": 4.0, "level_db": 0.0},
            {"id": "drums", "label": "Drum kit", "x_m": 6.5, "y_m": 1.5, "level_db": 8.0},
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
                    "min_target_distance_m": 0.25,
                    "max_target_distance_m": 1.0,
                },
            }
        ],
    }


def test_parse_valid_scenario() -> None:
    scenario = parse_scenario_text(json.dumps(valid_payload()))

    assert scenario.stage.name == "Club stage"
    assert scenario.sources[1].id == "drums"
    assert scenario.microphones[0].target_source == "voice"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: data["sources"].append(dict(data["sources"][0])), "duplicate source id"),
        (
            lambda data: data["microphones"][0].update({"target_source": "missing"}),
            "unknown target_source",
        ),
        (lambda data: data["sources"][0].update({"x_m": 8.1}), "inside the stage"),
        (lambda data: data["stage"].update({"width_m": float("nan")}), "finite number"),
        (
            lambda data: data["microphones"][0]["search"].update(  # type: ignore[index]
                {"min_target_distance_m": 1.1}
            ),
            "min_target_distance_m must be <= max_target_distance_m",
        ),
    ],
)
def test_parse_rejects_invalid_scenario(mutate: object, message: str) -> None:
    payload = valid_payload()
    mutate(payload)  # type: ignore[operator]

    with pytest.raises(ScenarioError, match=message):
        parse_scenario_text(json.dumps(payload))


def test_parse_rejects_duplicate_json_keys() -> None:
    payload = json.dumps(valid_payload())
    duplicated = payload.replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1')

    with pytest.raises(ScenarioError, match="duplicate JSON key: schema_version"):
        parse_scenario_text(duplicated)


def test_parse_rejects_unexpected_fields() -> None:
    payload = valid_payload()
    payload["stage"]["mystery"] = True  # type: ignore[index]

    with pytest.raises(ScenarioError, match=r"unexpected field: stage\.mystery"):
        parse_scenario_text(json.dumps(payload))
