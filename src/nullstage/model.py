"""Domain values and direct-field microphone geometry."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

PolarPattern = Literal["omni", "cardioid", "supercardioid", "hypercardioid", "figure8"]

PATTERN_COEFFICIENTS: dict[str, tuple[float, float]] = {
    "omni": (1.0, 0.0),
    "cardioid": (0.5, 0.5),
    "supercardioid": ((math.sqrt(3.0) - 1.0) / 2.0, (3.0 - math.sqrt(3.0)) / 2.0),
    "hypercardioid": (0.25, 0.75),
    "figure8": (0.0, 1.0),
}


@dataclass(frozen=True, slots=True)
class Point:
    x_m: float
    y_m: float


@dataclass(frozen=True, slots=True)
class Stage:
    name: str
    width_m: float
    depth_m: float


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    label: str
    position: Point
    level_db: float


@dataclass(frozen=True, slots=True)
class SearchEnvelope:
    move_radius_m: float
    position_step_m: float
    aim_range_deg: float
    aim_step_deg: float
    min_target_distance_m: float
    max_target_distance_m: float


@dataclass(frozen=True, slots=True)
class Microphone:
    id: str
    label: str
    target_source: str
    pattern: PolarPattern
    off_axis_floor_db: float
    position: Point
    aim_deg: float
    search: SearchEnvelope


@dataclass(frozen=True, slots=True)
class Scenario:
    schema_version: int
    stage: Stage
    sources: tuple[Source, ...]
    microphones: tuple[Microphone, ...]


def angle_delta_deg(reference_deg: float, target_deg: float) -> float:
    """Return the shortest signed turn from reference to target."""

    return (target_deg - reference_deg + 180.0) % 360.0 - 180.0


def directivity_db(pattern: str, incidence_deg: float, *, floor_db: float) -> float:
    """Return ideal first-order polar response, clamped to the declared mic floor."""

    pressure, gradient = PATTERN_COEFFICIENTS[pattern]
    amplitude = abs(pressure + gradient * math.cos(math.radians(incidence_deg)))
    if amplitude == 0.0:
        return floor_db
    return max(20.0 * math.log10(amplitude), floor_db)


def distance_m(left: Point, right: Point) -> float:
    return math.hypot(left.x_m - right.x_m, left.y_m - right.y_m)


def bearing_deg(origin: Point, target: Point) -> float:
    return math.degrees(math.atan2(target.y_m - origin.y_m, target.x_m - origin.x_m)) % 360.0


def received_level_db(
    *,
    source_level_db: float,
    source: Point,
    microphone: Point,
    aim_deg: float,
    pattern: str,
    floor_db: float,
) -> float:
    """Estimate relative received level from direct distance and polar response."""

    separation_m = distance_m(source, microphone)
    if separation_m < 0.05:
        raise ValueError("each source and microphone must be at least 0.05 m apart")
    incidence_deg = angle_delta_deg(aim_deg, bearing_deg(microphone, source))
    return (
        source_level_db
        - 20.0 * math.log10(separation_m)
        + directivity_db(pattern, incidence_deg, floor_db=floor_db)
    )
