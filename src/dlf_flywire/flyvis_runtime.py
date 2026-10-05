from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

FLYVIS_RELEASE = "v1.2.0"
FLYVIS_REVISION = "92b3845cc426dd309a1a0e1b3890156c42e14021"
PRETRAINED_ARCHIVE_SHA256 = (
    "71c78d4070556a536b13b23ee3139cd2788aa2a9d07d430a223b4edead281db1"
)

EXPECTED_PREFERRED_DIRECTION_DEG = {
    "T4a": 180.0,
    "T4c": 90.0,
    "T5a": 180.0,
    "T5c": 90.0,
}

DEFAULT_DIRECTION_TOLERANCE_DEG = 45.0


@dataclass(frozen=True)
class FlyVisDirectionObservation:
    """A measured preferred direction from a real FlyVis model run."""

    cell_type: str
    intensity: int
    expected_direction_deg: float
    observed_direction_deg: float
    angular_error_deg: float

    def __post_init__(self) -> None:
        if not isinstance(self.cell_type, str) or not self.cell_type.strip():
            raise ValueError("cell_type must not be empty")
        if type(self.intensity) is not int:
            raise ValueError("intensity must be an integer")
        for name, value in (
            ("expected_direction_deg", self.expected_direction_deg),
            ("observed_direction_deg", self.observed_direction_deg),
            ("angular_error_deg", self.angular_error_deg),
        ):
            if not isfinite(float(value)):
                raise ValueError(f"{name} must be finite")


def angular_distance_deg(first: float, second: float) -> float:
    """Return the smallest absolute circular distance in degrees."""

    first = float(first) % 360.0
    second = float(second) % 360.0
    return abs((first - second + 180.0) % 360.0 - 180.0)


def validate_direction_observation(
    observation: FlyVisDirectionObservation,
    tolerance_deg: float = DEFAULT_DIRECTION_TOLERANCE_DEG,
) -> None:
    """Fail closed when an observed direction is outside the accepted bound."""

    tolerance_deg = float(tolerance_deg)
    if not isfinite(tolerance_deg) or tolerance_deg < 0.0 or tolerance_deg > 180.0:
        raise ValueError("tolerance_deg must be finite and within [0, 180]")
    if observation.angular_error_deg > tolerance_deg:
        raise ValueError(
            f"{observation.cell_type} preferred direction error "
            f"{observation.angular_error_deg:.2f} exceeds "
            f"{tolerance_deg:.2f} degrees"
        )
