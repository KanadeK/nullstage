"""Bounded, deterministic microphone placement search."""

from __future__ import annotations

import math
from dataclasses import dataclass

from nullstage.analysis import MicrophoneAnalysis, analyze_microphone
from nullstage.model import Microphone, Point, Scenario, angle_delta_deg, distance_m

MAX_CANDIDATES_PER_MICROPHONE = 50_000


class OptimizationError(ValueError):
    """A declared search cannot be executed within the public resource contract."""


@dataclass(frozen=True, slots=True)
class MicrophoneOptimization:
    microphone_id: str
    baseline: MicrophoneAnalysis
    optimized: MicrophoneAnalysis
    evaluated_candidates: int
    improvement_db: float
    movement_m: float
    rotation_deg: float


@dataclass(frozen=True, slots=True)
class OptimizationReport:
    stage_name: str
    microphones: tuple[MicrophoneOptimization, ...]
    baseline_worst_margin_db: float
    optimized_worst_margin_db: float


def _candidate_upper_bound(microphone: Microphone) -> int:
    position_steps = math.floor(microphone.search.move_radius_m / microphone.search.position_step_m)
    aim_steps = math.floor(microphone.search.aim_range_deg / microphone.search.aim_step_deg)
    return (2 * position_steps + 1) ** 2 * (2 * aim_steps + 1)


def _positions(scenario: Scenario, microphone: Microphone) -> tuple[Point, ...]:
    radius = microphone.search.move_radius_m
    step = microphone.search.position_step_m
    step_count = math.floor(radius / step)
    coordinates: set[tuple[float, float]] = {
        (round(microphone.position.x_m, 12), round(microphone.position.y_m, 12))
    }
    for x_step in range(-step_count, step_count + 1):
        for y_step in range(-step_count, step_count + 1):
            x_m = microphone.position.x_m + x_step * step
            y_m = microphone.position.y_m + y_step * step
            candidate = Point(x_m=x_m, y_m=y_m)
            if (
                distance_m(microphone.position, candidate) <= radius + 1e-12
                and 0.0 <= x_m <= scenario.stage.width_m
                and 0.0 <= y_m <= scenario.stage.depth_m
            ):
                coordinates.add((round(x_m, 12), round(y_m, 12)))
    return tuple(Point(x_m=x_m, y_m=y_m) for x_m, y_m in sorted(coordinates))


def _aims(microphone: Microphone) -> tuple[float, ...]:
    step_count = math.floor(microphone.search.aim_range_deg / microphone.search.aim_step_deg)
    aims = {
        round(
            (microphone.aim_deg + offset * microphone.search.aim_step_deg) % 360.0,
            12,
        )
        for offset in range(-step_count, step_count + 1)
    }
    aims.add(round(microphone.aim_deg % 360.0, 12))
    return tuple(sorted(aims))


def _rank_key(
    analysis: MicrophoneAnalysis, microphone: Microphone
) -> tuple[float, float, float, float, float, float]:
    movement_m = distance_m(microphone.position, analysis.position)
    rotation_deg = abs(angle_delta_deg(microphone.aim_deg, analysis.aim_deg))
    return (
        analysis.margin_db,
        -movement_m,
        -rotation_deg,
        -analysis.position.x_m,
        -analysis.position.y_m,
        -analysis.aim_deg,
    )


def _optimize_microphone(scenario: Scenario, microphone: Microphone) -> MicrophoneOptimization:
    upper_bound = _candidate_upper_bound(microphone)
    if upper_bound > MAX_CANDIDATES_PER_MICROPHONE:
        raise OptimizationError(
            f"microphone {microphone.id} candidate limit exceeded: "
            f"upper bound {upper_bound} > {MAX_CANDIDATES_PER_MICROPHONE}; "
            "increase position_step_m or aim_step_deg, or reduce the search ranges"
        )
    baseline = analyze_microphone(scenario, microphone)
    candidates: list[MicrophoneAnalysis] = []
    target = next(source for source in scenario.sources if source.id == microphone.target_source)
    for position in _positions(scenario, microphone):
        if any(distance_m(position, source.position) < 0.05 for source in scenario.sources):
            continue
        target_distance_m = distance_m(position, target.position)
        if not (
            microphone.search.min_target_distance_m
            <= target_distance_m
            <= microphone.search.max_target_distance_m
        ):
            continue
        for aim_deg in _aims(microphone):
            candidates.append(
                analyze_microphone(scenario, microphone, position=position, aim_deg=aim_deg)
            )
    optimized = max(candidates, key=lambda analysis: _rank_key(analysis, microphone))
    movement_m = distance_m(baseline.position, optimized.position)
    rotation_deg = abs(angle_delta_deg(baseline.aim_deg, optimized.aim_deg))
    return MicrophoneOptimization(
        microphone_id=microphone.id,
        baseline=baseline,
        optimized=optimized,
        evaluated_candidates=len(candidates),
        improvement_db=optimized.margin_db - baseline.margin_db,
        movement_m=movement_m,
        rotation_deg=rotation_deg,
    )


def optimize_scenario(scenario: Scenario) -> OptimizationReport:
    microphones = tuple(
        _optimize_microphone(scenario, microphone)
        for microphone in sorted(scenario.microphones, key=lambda item: item.id)
    )
    return OptimizationReport(
        stage_name=scenario.stage.name,
        microphones=microphones,
        baseline_worst_margin_db=min(item.baseline.margin_db for item in microphones),
        optimized_worst_margin_db=min(item.optimized.margin_db for item in microphones),
    )
