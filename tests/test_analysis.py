from __future__ import annotations

import math

import pytest

from nullstage.analysis import analyze_scenario, below_threshold_ids, combine_levels_db
from nullstage.model import Microphone, Point, Scenario, SearchEnvelope, Source, Stage


def scenario_with_two_equal_spills() -> Scenario:
    return Scenario(
        schema_version=1,
        stage=Stage(name="Test stage", width_m=6.0, depth_m=4.0),
        sources=(
            Source(id="target", label="Target", position=Point(2.0, 1.0), level_db=0.0),
            Source(id="spill-a", label="Spill A", position=Point(0.0, 1.0), level_db=0.0),
            Source(id="spill-b", label="Spill B", position=Point(1.0, 2.0), level_db=-20.0),
        ),
        microphones=(
            Microphone(
                id="mic",
                label="Mic",
                target_source="target",
                pattern="cardioid",
                off_axis_floor_db=-20.0,
                position=Point(1.0, 1.0),
                aim_deg=0.0,
                search=SearchEnvelope(
                    move_radius_m=0.0,
                    position_step_m=0.25,
                    aim_range_deg=0.0,
                    aim_step_deg=15.0,
                ),
            ),
        ),
    )


def test_combine_levels_adds_equal_powers() -> None:
    assert combine_levels_db((0.0, 0.0)) == pytest.approx(10.0 * math.log10(2.0))


def test_analysis_reports_ranked_spill_and_margin() -> None:
    report = analyze_scenario(scenario_with_two_equal_spills())
    microphone = report.microphones[0]

    assert microphone.target.level_db == pytest.approx(0.0)
    assert [spill.source_id for spill in microphone.spills] == ["spill-a", "spill-b"]
    assert microphone.spills[0].level_db == pytest.approx(-20.0)
    assert microphone.spills[1].level_db == pytest.approx(-26.0205999)
    assert microphone.combined_spill_db == pytest.approx(-19.0308999)
    assert microphone.margin_db == pytest.approx(19.0308999)
    assert report.worst_margin_db == pytest.approx(microphone.margin_db)


def test_threshold_policy_lists_only_failing_microphones() -> None:
    report = analyze_scenario(scenario_with_two_equal_spills())

    assert below_threshold_ids(report, 20.0) == ("mic",)
    assert below_threshold_ids(report, 19.0) == ()


def test_analysis_order_is_stable_by_microphone_id() -> None:
    scenario = scenario_with_two_equal_spills()
    second = Microphone(
        id="aaa",
        label="Earlier",
        target_source="target",
        pattern="omni",
        off_axis_floor_db=-20.0,
        position=Point(1.0, 0.5),
        aim_deg=0.0,
        search=scenario.microphones[0].search,
    )
    permuted = Scenario(
        schema_version=1,
        stage=scenario.stage,
        sources=scenario.sources,
        microphones=(scenario.microphones[0], second),
    )

    report = analyze_scenario(permuted)

    assert [microphone.microphone_id for microphone in report.microphones] == ["aaa", "mic"]
