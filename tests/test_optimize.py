from __future__ import annotations

from itertools import product

import pytest

from nullstage.analysis import MicrophoneAnalysis, analyze_microphone
from nullstage.model import Microphone, Point, Scenario, SearchEnvelope, Source, Stage, distance_m
from nullstage.optimize import OptimizationError, optimize_scenario


def movable_scenario(*, envelope: SearchEnvelope | None = None) -> Scenario:
    search = envelope or SearchEnvelope(
        move_radius_m=0.5,
        position_step_m=0.5,
        aim_range_deg=30.0,
        aim_step_deg=15.0,
        min_target_distance_m=0.4,
        max_target_distance_m=1.5,
    )
    return Scenario(
        schema_version=1,
        stage=Stage(name="Optimization test", width_m=6.0, depth_m=4.0),
        sources=(
            Source(id="voice", label="Voice", position=Point(2.0, 1.0), level_db=0.0),
            Source(id="drums", label="Drums", position=Point(1.0, 3.0), level_db=10.0),
        ),
        microphones=(
            Microphone(
                id="voice-mic",
                label="Voice mic",
                target_source="voice",
                pattern="cardioid",
                off_axis_floor_db=-24.0,
                position=Point(1.0, 1.0),
                aim_deg=0.0,
                search=search,
            ),
        ),
    )


def test_optimizer_improves_margin_without_leaving_envelope() -> None:
    scenario = movable_scenario()
    result = optimize_scenario(scenario)
    microphone = result.microphones[0]

    assert microphone.optimized.margin_db > microphone.baseline.margin_db
    assert microphone.improvement_db == pytest.approx(
        microphone.optimized.margin_db - microphone.baseline.margin_db
    )
    assert distance_m(microphone.baseline.position, microphone.optimized.position) <= 0.5 + 1e-12
    assert 0.4 <= microphone.optimized.target.distance_m <= 1.5
    assert microphone.rotation_deg <= 30.0
    assert result.optimized_worst_margin_db >= result.baseline_worst_margin_db


def test_optimizer_matches_independent_exhaustive_enumeration() -> None:
    scenario = movable_scenario()
    microphone = scenario.microphones[0]
    positions = (
        Point(0.5, 1.0),
        Point(1.0, 0.5),
        Point(1.0, 1.0),
        Point(1.0, 1.5),
        Point(1.5, 1.0),
    )
    aims = (330.0, 345.0, 0.0, 15.0, 30.0)
    analyses = [
        analyze_microphone(scenario, microphone, position=position, aim_deg=aim)
        for position, aim in product(positions, aims)
    ]

    def independent_key(
        analysis: MicrophoneAnalysis,
    ) -> tuple[float, float, float, float, float, float]:
        movement = distance_m(microphone.position, analysis.position)
        rotation = abs((analysis.aim_deg - microphone.aim_deg + 180.0) % 360.0 - 180.0)
        return (
            analysis.margin_db,
            -movement,
            -rotation,
            -analysis.position.x_m,
            -analysis.position.y_m,
            -analysis.aim_deg,
        )

    expected = max(analyses, key=independent_key)
    optimized = optimize_scenario(scenario).microphones[0].optimized

    assert optimized.position == expected.position
    assert optimized.aim_deg == pytest.approx(expected.aim_deg)
    assert optimized.margin_db == pytest.approx(expected.margin_db)


def test_optimizer_prefers_baseline_when_every_candidate_ties() -> None:
    scenario = movable_scenario()
    omni = Microphone(
        id="voice-mic",
        label="Voice mic",
        target_source="voice",
        pattern="omni",
        off_axis_floor_db=-24.0,
        position=Point(1.0, 1.0),
        aim_deg=0.0,
        search=SearchEnvelope(
            move_radius_m=0.0,
            position_step_m=0.5,
            aim_range_deg=30.0,
            aim_step_deg=15.0,
            min_target_distance_m=0.4,
            max_target_distance_m=1.5,
        ),
    )
    scenario = Scenario(
        schema_version=1,
        stage=scenario.stage,
        sources=scenario.sources,
        microphones=(omni,),
    )

    optimized = optimize_scenario(scenario).microphones[0]

    assert optimized.optimized.position == optimized.baseline.position
    assert optimized.optimized.aim_deg == optimized.baseline.aim_deg


def test_optimizer_rejects_candidate_explosion_before_search() -> None:
    scenario = movable_scenario(
        envelope=SearchEnvelope(
            move_radius_m=5.0,
            position_step_m=0.01,
            aim_range_deg=180.0,
            aim_step_deg=0.1,
            min_target_distance_m=0.4,
            max_target_distance_m=1.5,
        )
    )

    with pytest.raises(OptimizationError, match="candidate limit"):
        optimize_scenario(scenario)
