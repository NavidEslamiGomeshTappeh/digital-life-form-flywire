from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


class PTZProbeError(RuntimeError):
    """Raised when ONVIF PTZ inspection cannot complete."""


@dataclass(frozen=True)
class PTZProbeResult:
    schema_version: int
    observed_at_utc: str
    host: str
    port: int
    profile_token: str
    ptz_configuration_token: str
    pan_tilt_position: dict[str, float | None]
    move_status: dict[str, str | None]
    continuous_velocity_range: dict[str, float | None]
    movement_commands_issued: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "observed_at_utc": self.observed_at_utc,
            "host": self.host,
            "port": self.port,
            "profile_token": self.profile_token,
            "ptz_configuration_token": self.ptz_configuration_token,
            "pan_tilt_position": dict(self.pan_tilt_position),
            "move_status": dict(self.move_status),
            "continuous_velocity_range": dict(self.continuous_velocity_range),
            "movement_commands_issued": self.movement_commands_issued,
        }


def _field(value: object, *names: str) -> object | None:
    if value is None:
        return None
    for name in names:
        observed = getattr(value, name, None)
        if observed is not None:
            return observed
    if isinstance(value, dict):
        for name in names:
            if name in value:
                return value[name]
    return None


def _float_or_none(value: object) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _str_or_none(value: object) -> str | None:
    return None if value is None else str(value)


def probe_onvif_ptz(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
) -> PTZProbeResult:
    if not isinstance(host, str) or not host.strip():
        raise PTZProbeError("ONVIF host must be a non-empty string")
    if isinstance(port, bool) or not isinstance(port, int) or not (1 <= port <= 65535):
        raise PTZProbeError("ONVIF port must be between 1 and 65535")
    if not isinstance(username, str) or not username:
        raise PTZProbeError("ONVIF username must not be empty")
    if not isinstance(password, str) or not password:
        raise PTZProbeError("ONVIF password must not be empty")

    try:
        from onvif import ONVIFClient
    except ImportError as exc:
        raise PTZProbeError(
            "onvif-python==0.4.4 is required for ONVIF PTZ inspection; "
            "install the optional ptz runtime"
        ) from exc

    try:
        client = ONVIFClient(host.strip(), port, username, password)
        media = client.media()
        profiles = list(media.GetProfiles())
        profile = next(
            (
                item
                for item in profiles
                if _field(item, "PTZConfiguration") is not None
            ),
            None,
        )
        if profile is None:
            raise PTZProbeError("ONVIF camera returned no PTZ-capable media profile")

        profile_token = _str_or_none(_field(profile, "token", "_token"))
        ptz_configuration = _field(profile, "PTZConfiguration")
        configuration_token = _str_or_none(
            _field(ptz_configuration, "token", "_token")
        )
        if not profile_token or not configuration_token:
            raise PTZProbeError("ONVIF PTZ profile/configuration token is missing")

        ptz = client.ptz()

        status = ptz.GetStatus(profile_token)
        position = _field(status, "Position")
        pan_tilt = _field(position, "PanTilt")
        move_status = _field(status, "MoveStatus")

        options = ptz.GetConfigurationOptions(configuration_token)
        spaces = _field(options, "Spaces")
        velocity_spaces = _field(spaces, "ContinuousPanTiltVelocitySpace") or []
        if isinstance(velocity_spaces, (list, tuple)):
            velocity_space = next(iter(velocity_spaces), None)
        else:
            velocity_space = velocity_spaces
        x_range = _field(velocity_space, "XRange")
        y_range = _field(velocity_space, "YRange")

        return PTZProbeResult(
            schema_version=1,
            observed_at_utc=datetime.now(UTC).isoformat(),
            host=host.strip(),
            port=port,
            profile_token=profile_token,
            ptz_configuration_token=configuration_token,
            pan_tilt_position={
                "pan": _float_or_none(_field(pan_tilt, "x", "_x")),
                "tilt": _float_or_none(_field(pan_tilt, "y", "_y")),
            },
            move_status={
                "pan_tilt": _str_or_none(_field(move_status, "PanTilt")),
                "zoom": _str_or_none(_field(move_status, "Zoom")),
            },
            continuous_velocity_range={
                "pan_min": _float_or_none(_field(x_range, "Min")),
                "pan_max": _float_or_none(_field(x_range, "Max")),
                "tilt_min": _float_or_none(_field(y_range, "Min")),
                "tilt_max": _float_or_none(_field(y_range, "Max")),
            },
            movement_commands_issued=False,
        )
    except PTZProbeError:
        raise
    except Exception as exc:
        raise PTZProbeError(f"ONVIF PTZ inspection failed: {exc}") from exc
