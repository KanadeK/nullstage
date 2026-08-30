from __future__ import annotations

import math

import pytest

from nullstage.model import Point, angle_delta_deg, directivity_db, received_level_db


@pytest.mark.parametrize(
    ("pattern", "angle_deg", "expected_db"),
    [
        ("omni", 137.0, 0.0),
        ("cardioid", 0.0, 0.0),
        ("cardioid", 90.0, 20.0 * math.log10(0.5)),
        ("cardioid", 180.0, -30.0),
        ("supercardioid", 125.2643897, -30.0),
        ("hypercardioid", 109.4712206, -30.0),
        ("figure8", 90.0, -30.0),
        ("figure8", 180.0, 0.0),
    ],
)
def test_directivity_uses_ideal_first_order_pattern_with_declared_floor(
    pattern: str, angle_deg: float, expected_db: float
) -> None:
    assert directivity_db(pattern, angle_deg, floor_db=-30.0) == pytest.approx(
        expected_db, abs=1e-6
    )


def test_angle_delta_wraps_to_shortest_signed_turn() -> None:
    assert angle_delta_deg(350.0, 10.0) == pytest.approx(20.0)
    assert angle_delta_deg(10.0, 350.0) == pytest.approx(-20.0)


def test_doubling_distance_reduces_received_level_by_six_db() -> None:
    source = Point(0.0, 0.0)
    one_metre = received_level_db(
        source_level_db=0.0,
        source=source,
        microphone=Point(1.0, 0.0),
        aim_deg=180.0,
        pattern="omni",
        floor_db=-30.0,
    )
    two_metres = received_level_db(
        source_level_db=0.0,
        source=source,
        microphone=Point(2.0, 0.0),
        aim_deg=180.0,
        pattern="omni",
        floor_db=-30.0,
    )

    assert one_metre - two_metres == pytest.approx(20.0 * math.log10(2.0))


def test_received_level_rejects_coincident_source_and_microphone() -> None:
    with pytest.raises(ValueError, match=r"at least 0\.05 m apart"):
        received_level_db(
            source_level_db=0.0,
            source=Point(1.0, 1.0),
            microphone=Point(1.0, 1.0),
            aim_deg=0.0,
            pattern="cardioid",
            floor_db=-30.0,
        )
