from __future__ import annotations

import pytest

from dlf_flywire.flyvis_runtime import (
    DEFAULT_DIRECTION_TOLERANCE_DEG,
    EXPECTED_PREFERRED_DIRECTION_DEG,
    FLYVIS_RELEASE,
    FLYVIS_REVISION,
    FlyVisDirectionObservation,
    angular_distance_deg,
    validate_direction_observation,
)


def test_flyvis_reference_is_frozen():
    assert FLYVIS_RELEASE == "v1.2.0"
    assert FLYVIS_REVISION == "92b3845cc426dd309a1a0e1b3890156c42e14021"
    assert EXPECTED_PREFERRED_DIRECTION_DEG == {
        "T4a": 180.0,
        "T4c": 90.0,
        "T5a": 180.0,
        "T5c": 90.0,
    }


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [(0, 359, 1.0), (180, 0, 180.0), (90, 450, 0.0)],
)
def test_angular_distance_is_circular(first, second, expected):
    assert angular_distance_deg(first, second) == expected


def test_direction_observation_accepts_expected_result():
    observation = FlyVisDirectionObservation(
        cell_type="T4c",
        intensity=1,
        expected_direction_deg=90.0,
        observed_direction_deg=120.0,
        angular_error_deg=30.0,
    )
    validate_direction_observation(observation)


def test_direction_observation_fails_closed():
    observation = FlyVisDirectionObservation(
        cell_type="T4c",
        intensity=1,
        expected_direction_deg=90.0,
        observed_direction_deg=180.0,
        angular_error_deg=90.0,
    )
    with pytest.raises(ValueError, match="exceeds"):
        validate_direction_observation(
            observation, tolerance_deg=DEFAULT_DIRECTION_TOLERANCE_DEG
        )


def test_direction_observation_rejects_invalid_tolerance():
    observation = FlyVisDirectionObservation(
        cell_type="T4c",
        intensity=1,
        expected_direction_deg=90.0,
        observed_direction_deg=90.0,
        angular_error_deg=0.0,
    )
    with pytest.raises(ValueError, match="tolerance"):
        validate_direction_observation(observation, tolerance_deg=181.0)
