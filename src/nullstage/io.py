"""Strict JSON boundary for NullStage scenarios."""

from __future__ import annotations

import json
import math
import re
from typing import Any, NoReturn, cast

from nullstage.model import (
    PATTERN_COEFFICIENTS,
    Microphone,
    Point,
    PolarPattern,
    Scenario,
    SearchEnvelope,
    Source,
    Stage,
    distance_m,
)

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class ScenarioError(ValueError):
    """The external scenario cannot become a valid domain model."""


def _duplicate_checked_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ScenarioError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> NoReturn:
    raise ScenarioError(f"finite number required, got {value}")


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScenarioError(f"{path} must be an object")
    return cast(dict[str, Any], value)


def _array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ScenarioError(f"{path} must be an array")
    return value


def _fields(value: dict[str, Any], path: str, expected: set[str]) -> None:
    extras = sorted(value.keys() - expected)
    if extras:
        raise ScenarioError(f"unexpected field: {path}.{extras[0]}")
    missing = sorted(expected - value.keys())
    if missing:
        raise ScenarioError(f"missing field: {path}.{missing[0]}")


def _string(value: Any, path: str, *, maximum: int = 80) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScenarioError(f"{path} must be a non-empty string")
    if len(value) > maximum:
        raise ScenarioError(f"{path} must be at most {maximum} characters")
    return value


def _identifier(value: Any, path: str) -> str:
    identifier = _string(value, path, maximum=64)
    if ID_PATTERN.fullmatch(identifier) is None:
        raise ScenarioError(f"{path} must match {ID_PATTERN.pattern}")
    return identifier


def _number(
    value: Any,
    path: str,
    *,
    minimum: float,
    maximum: float,
    minimum_inclusive: bool = True,
) -> float:
    converted = _finite_number(value, path)
    below = converted < minimum if minimum_inclusive else converted <= minimum
    if below or converted > maximum:
        lower = ">=" if minimum_inclusive else ">"
        raise ScenarioError(f"{path} must be {lower} {minimum} and <= {maximum}")
    return converted


def _finite_number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScenarioError(f"{path} must be a finite number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ScenarioError(f"{path} must be a finite number")
    return converted


def _point(value: dict[str, Any], path: str, stage: Stage) -> Point:
    x_m = _finite_number(value["x_m"], f"{path}.x_m")
    y_m = _finite_number(value["y_m"], f"{path}.y_m")
    if not 0.0 <= x_m <= stage.width_m or not 0.0 <= y_m <= stage.depth_m:
        raise ScenarioError(
            f"{path} must be inside the stage: "
            f"0 <= x_m <= {stage.width_m} and 0 <= y_m <= {stage.depth_m}"
        )
    return Point(x_m=x_m, y_m=y_m)


def _parse_stage(value: Any) -> Stage:
    item = _object(value, "stage")
    _fields(item, "stage", {"name", "width_m", "depth_m"})
    return Stage(
        name=_string(item["name"], "stage.name", maximum=120),
        width_m=_number(item["width_m"], "stage.width_m", minimum=0.5, maximum=200.0),
        depth_m=_number(item["depth_m"], "stage.depth_m", minimum=0.5, maximum=200.0),
    )


def _parse_sources(value: Any, stage: Stage) -> tuple[Source, ...]:
    items = _array(value, "sources")
    if not 2 <= len(items) <= 64:
        raise ScenarioError("sources must contain between 2 and 64 items")
    result: list[Source] = []
    seen: set[str] = set()
    expected = {"id", "label", "x_m", "y_m", "level_db"}
    for index, raw in enumerate(items):
        path = f"sources[{index}]"
        item = _object(raw, path)
        _fields(item, path, expected)
        identifier = _identifier(item["id"], f"{path}.id")
        if identifier in seen:
            raise ScenarioError(f"duplicate source id: {identifier}")
        seen.add(identifier)
        result.append(
            Source(
                id=identifier,
                label=_string(item["label"], f"{path}.label"),
                position=_point(item, path, stage),
                level_db=_number(
                    item["level_db"], f"{path}.level_db", minimum=-120.0, maximum=200.0
                ),
            )
        )
    return tuple(result)


def _parse_search(value: Any, path: str) -> SearchEnvelope:
    item = _object(value, path)
    _fields(
        item,
        path,
        {
            "move_radius_m",
            "position_step_m",
            "aim_range_deg",
            "aim_step_deg",
            "min_target_distance_m",
            "max_target_distance_m",
        },
    )
    min_target_distance_m = _number(
        item["min_target_distance_m"],
        f"{path}.min_target_distance_m",
        minimum=0.05,
        maximum=20.0,
    )
    max_target_distance_m = _number(
        item["max_target_distance_m"],
        f"{path}.max_target_distance_m",
        minimum=0.05,
        maximum=20.0,
    )
    if min_target_distance_m > max_target_distance_m:
        raise ScenarioError(f"{path}.min_target_distance_m must be <= max_target_distance_m")
    return SearchEnvelope(
        move_radius_m=_number(
            item["move_radius_m"], f"{path}.move_radius_m", minimum=0.0, maximum=5.0
        ),
        position_step_m=_number(
            item["position_step_m"],
            f"{path}.position_step_m",
            minimum=0.01,
            maximum=2.0,
        ),
        aim_range_deg=_number(
            item["aim_range_deg"], f"{path}.aim_range_deg", minimum=0.0, maximum=180.0
        ),
        aim_step_deg=_number(
            item["aim_step_deg"], f"{path}.aim_step_deg", minimum=0.1, maximum=180.0
        ),
        min_target_distance_m=min_target_distance_m,
        max_target_distance_m=max_target_distance_m,
    )


def _parse_microphones(
    value: Any, stage: Stage, sources: tuple[Source, ...]
) -> tuple[Microphone, ...]:
    items = _array(value, "microphones")
    if not 1 <= len(items) <= 32:
        raise ScenarioError("microphones must contain between 1 and 32 items")
    result: list[Microphone] = []
    seen: set[str] = set()
    source_ids = {source.id for source in sources}
    expected = {
        "id",
        "label",
        "target_source",
        "pattern",
        "off_axis_floor_db",
        "x_m",
        "y_m",
        "aim_deg",
        "search",
    }
    for index, raw in enumerate(items):
        path = f"microphones[{index}]"
        item = _object(raw, path)
        _fields(item, path, expected)
        identifier = _identifier(item["id"], f"{path}.id")
        if identifier in seen:
            raise ScenarioError(f"duplicate microphone id: {identifier}")
        seen.add(identifier)
        target_source = _identifier(item["target_source"], f"{path}.target_source")
        if target_source not in source_ids:
            raise ScenarioError(
                f"{path}.target_source references unknown target_source: {target_source}"
            )
        pattern = _string(item["pattern"], f"{path}.pattern")
        if pattern not in PATTERN_COEFFICIENTS:
            choices = ", ".join(PATTERN_COEFFICIENTS)
            raise ScenarioError(f"{path}.pattern must be one of: {choices}")
        microphone = Microphone(
            id=identifier,
            label=_string(item["label"], f"{path}.label"),
            target_source=target_source,
            pattern=cast(PolarPattern, pattern),
            off_axis_floor_db=_number(
                item["off_axis_floor_db"],
                f"{path}.off_axis_floor_db",
                minimum=-80.0,
                maximum=0.0,
            ),
            position=_point(item, path, stage),
            aim_deg=_number(item["aim_deg"], f"{path}.aim_deg", minimum=0.0, maximum=360.0),
            search=_parse_search(item["search"], f"{path}.search"),
        )
        for source in sources:
            if distance_m(microphone.position, source.position) < 0.05:
                raise ScenarioError(f"{path} and source {source.id} must be at least 0.05 m apart")
        target = next(source for source in sources if source.id == microphone.target_source)
        target_distance_m = distance_m(microphone.position, target.position)
        if not (
            microphone.search.min_target_distance_m
            <= target_distance_m
            <= microphone.search.max_target_distance_m
        ):
            raise ScenarioError(
                f"{path} baseline target distance {target_distance_m:.3f} m is outside "
                f"search.min_target_distance_m..max_target_distance_m"
            )
        result.append(microphone)
    return tuple(result)


def parse_scenario_text(text: str) -> Scenario:
    """Parse and validate one complete scenario JSON document."""

    try:
        raw = json.loads(
            text,
            object_pairs_hook=_duplicate_checked_object,
            parse_constant=_invalid_constant,
        )
    except json.JSONDecodeError as error:
        raise ScenarioError(
            f"invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error
    root = _object(raw, "scenario")
    _fields(root, "scenario", {"schema_version", "stage", "sources", "microphones"})
    if root["schema_version"] != 1:
        raise ScenarioError("schema_version must be 1")
    stage = _parse_stage(root["stage"])
    sources = _parse_sources(root["sources"], stage)
    microphones = _parse_microphones(root["microphones"], stage, sources)
    return Scenario(schema_version=1, stage=stage, sources=sources, microphones=microphones)
