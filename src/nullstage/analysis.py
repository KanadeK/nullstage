"""Deterministic direct-field spill analysis."""

from __future__ import annotations

import math
from dataclasses import dataclass

from nullstage.model import (
    Microphone,
    Point,
    PolarPattern,
    Scenario,
    angle_delta_deg,
    bearing_deg,
    directivity_db,
    distance_m,
    received_level_db,
)


@dataclass(frozen=True, slots=True)
class Contribution:
    source_id: str
    source_label: str
    level_db: float
    distance_m: float
    incidence_deg: float
    directivity_db: float


@dataclass(frozen=True, slots=True)
class MicrophoneAnalysis:
    microphone_id: str
    microphone_label: str
    pattern: PolarPattern
    off_axis_floor_db: float
    position: Point
    aim_deg: float
    target: Contribution
    spills: tuple[Contribution, ...]
    combined_spill_db: float
    margin_db: float


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    stage_name: str
    microphones: tuple[MicrophoneAnalysis, ...]
    worst_margin_db: float


def combine_levels_db(levels_db: tuple[float, ...]) -> float:
    """Combine independent relative dB levels by summing linear power."""

    return 10.0 * math.log10(sum(10.0 ** (level_db / 10.0) for level_db in levels_db))


def _contribution(
    microphone: Microphone,
    source_id: str,
    source_label: str,
    source_position: Point,
    source_level_db: float,
    position: Point,
    aim_deg: float,
) -> Contribution:
    incidence_deg = angle_delta_deg(aim_deg, bearing_deg(position, source_position))
    return Contribution(
        source_id=source_id,
        source_label=source_label,
        level_db=received_level_db(
            source_level_db=source_level_db,
            source=source_position,
            microphone=position,
            aim_deg=aim_deg,
            pattern=microphone.pattern,
            floor_db=microphone.off_axis_floor_db,
        ),
        distance_m=distance_m(source_position, position),
        incidence_deg=incidence_deg,
        directivity_db=directivity_db(
            microphone.pattern,
            incidence_deg,
            floor_db=microphone.off_axis_floor_db,
        ),
    )


def analyze_microphone(
    scenario: Scenario,
    microphone: Microphone,
    *,
    position: Point | None = None,
    aim_deg: float | None = None,
) -> MicrophoneAnalysis:
    """Analyze one microphone at its declared or candidate placement."""

    candidate_position = microphone.position if position is None else position
    candidate_aim = microphone.aim_deg if aim_deg is None else aim_deg % 360.0
    contributions = {
        source.id: _contribution(
            microphone,
            source.id,
            source.label,
            source.position,
            source.level_db,
            candidate_position,
            candidate_aim,
        )
        for source in scenario.sources
    }
    target = contributions[microphone.target_source]
    spills = tuple(
        sorted(
            (
                contribution
                for source_id, contribution in contributions.items()
                if source_id != microphone.target_source
            ),
            key=lambda contribution: (-contribution.level_db, contribution.source_id),
        )
    )
    combined_spill_db = combine_levels_db(tuple(spill.level_db for spill in spills))
    return MicrophoneAnalysis(
        microphone_id=microphone.id,
        microphone_label=microphone.label,
        pattern=microphone.pattern,
        off_axis_floor_db=microphone.off_axis_floor_db,
        position=candidate_position,
        aim_deg=candidate_aim,
        target=target,
        spills=spills,
        combined_spill_db=combined_spill_db,
        margin_db=target.level_db - combined_spill_db,
    )


def analyze_scenario(scenario: Scenario) -> AnalysisReport:
    microphones = tuple(
        analyze_microphone(scenario, microphone)
        for microphone in sorted(scenario.microphones, key=lambda item: item.id)
    )
    return AnalysisReport(
        stage_name=scenario.stage.name,
        microphones=microphones,
        worst_margin_db=min(microphone.margin_db for microphone in microphones),
    )


def below_threshold_ids(report: AnalysisReport, threshold_db: float) -> tuple[str, ...]:
    return tuple(
        microphone.microphone_id
        for microphone in report.microphones
        if microphone.margin_db < threshold_db
    )
