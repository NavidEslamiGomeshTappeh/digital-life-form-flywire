from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from urllib.parse import urlsplit, urlunsplit

from .vision_input import VisionFrame, VisionInputError


def redact_stream_url(stream_url: str) -> str:
    """Return a log-safe RTSP locator without credentials or query secrets."""
    if not isinstance(stream_url, str) or not stream_url.strip():
        raise VisionInputError("RTSP stream URL must be a non-empty string")
    parsed = urlsplit(stream_url)
    if parsed.scheme.lower() not in {"rtsp", "rtsps"}:
        raise VisionInputError("network camera URL must use rtsp:// or rtsps://")
    if not parsed.hostname:
        raise VisionInputError("network camera URL must include a host")
    if parsed.username is not None or parsed.password is not None:
        host = parsed.hostname
        if parsed.port is not None:
            host = f"{host}:{parsed.port}"
        netloc = host
    else:
        netloc = parsed.netloc.rsplit("@", 1)[-1]
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path, "", ""))


class NetworkCameraSource:
    """Bounded RTSP camera capture with secret-safe provenance metadata."""

    def __init__(
        self,
        stream_url: str,
        *,
        width: int | None = None,
        height: int | None = None,
        per_frame_timeout_s: float = 5.0,
    ) -> None:
        self.stream_url = stream_url.strip() if isinstance(stream_url, str) else stream_url
        self.source_locator = redact_stream_url(self.stream_url)
        if width is not None and (
            isinstance(width, bool) or not isinstance(width, int) or width <= 0
        ):
            raise VisionInputError("width must be positive when provided")
        if height is not None and (
            isinstance(height, bool) or not isinstance(height, int) or height <= 0
        ):
            raise VisionInputError("height must be positive when provided")
        if per_frame_timeout_s <= 0:
            raise VisionInputError("per_frame_timeout_s must be positive")
        self.width = width
        self.height = height
        self.per_frame_timeout_s = float(per_frame_timeout_s)

    def capture(self, frame_count: int = 1) -> tuple[VisionFrame, ...]:
        if isinstance(frame_count, bool) or not isinstance(frame_count, int):
            raise VisionInputError("frame_count must be an integer")
        if frame_count <= 0:
            raise VisionInputError("frame_count must be positive")

        try:
            import cv2
        except ImportError as exc:
            raise VisionInputError(
                "OpenCV is required for RTSP camera capture; "
                "install the optional vision runtime dependency"
            ) from exc

        camera = cv2.VideoCapture(self.stream_url)
        try:
            if hasattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC"):
                camera.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self.per_frame_timeout_s * 1000)
            if hasattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC"):
                camera.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, self.per_frame_timeout_s * 1000)

            if not camera.isOpened():
                raise VisionInputError(
                    f"RTSP camera stream could not be opened: {self.source_locator}"
                )

            if self.width is not None:
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            if self.height is not None:
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

            frames: list[VisionFrame] = []
            for frame_index in range(frame_count):
                started = monotonic()
                ok, frame = camera.read()
                elapsed = monotonic() - started
                if not ok or frame is None:
                    raise VisionInputError(
                        f"RTSP camera read failed at frame {frame_index}"
                    )
                if elapsed > self.per_frame_timeout_s:
                    raise VisionInputError(
                        f"RTSP camera read exceeded timeout at frame {frame_index}: "
                        f"{elapsed:.3f}s"
                    )

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                height, width = gray.shape[:2]
                frames.append(
                    VisionFrame.from_gray8(
                        frame_index=frame_index,
                        width=int(width),
                        height=int(height),
                        pixels_gray8=gray.tobytes(),
                    )
                )
            return tuple(frames)
        finally:
            camera.release()



@dataclass(frozen=True)
class ONVIFStreamResolution:
    profile_token: str
    source_uri: str
    connection_uri: str

    def to_dict(self) -> dict[str, str]:
        return {
            "profile_token": self.profile_token,
            "source_uri": redact_stream_url(self.source_uri),
            "connection_uri": redact_stream_url(self.connection_uri),
        }


def _uri_field(value: object) -> str:
    uri = getattr(value, "Uri", None)
    if uri is None and isinstance(value, dict):
        uri = value.get("Uri")
    if not isinstance(uri, str) or not uri.strip():
        raise VisionInputError("ONVIF GetStreamUri returned no RTSP URI")
    return uri.strip()


def _profile_token(profile: object) -> str:
    token = getattr(profile, "token", None)
    if token is None:
        token = getattr(profile, "_token", None)
    if not isinstance(token, str) or not token.strip():
        raise VisionInputError("ONVIF media profile has no token")
    return token.strip()


def _with_rtsp_credentials(
    uri: str,
    username: str,
    password: str,
) -> str:
    parsed = urlsplit(uri)
    if parsed.scheme.lower() not in {"rtsp", "rtsps"} or not parsed.hostname:
        raise VisionInputError("ONVIF returned an invalid RTSP URI")
    if parsed.username is not None or parsed.password is not None:
        return uri

    from urllib.parse import quote

    user = quote(username, safe="")
    secret = quote(password, safe="")
    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return urlunsplit(
        (parsed.scheme, f"{user}:{secret}@{host}", parsed.path, parsed.query, "")
    )


def resolve_rtsp_stream(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
) -> ONVIFStreamResolution:
    if not isinstance(host, str) or not host.strip():
        raise VisionInputError("ONVIF host must be a non-empty string")
    if isinstance(port, bool) or not isinstance(port, int) or not (1 <= port <= 65535):
        raise VisionInputError("ONVIF port must be between 1 and 65535")
    if not isinstance(username, str) or not username:
        raise VisionInputError("ONVIF username must not be empty")
    if not isinstance(password, str) or not password:
        raise VisionInputError("ONVIF password must not be empty")

    try:
        from onvif import ONVIFClient
    except ImportError as exc:
        raise VisionInputError(
            "onvif-python==0.4.4 is required for ONVIF stream resolution; "
            "install the optional ptz runtime"
        ) from exc

    try:
        client = ONVIFClient(host.strip(), port, username, password)
        media = client.media()
        profiles = list(media.GetProfiles())
        if not profiles:
            raise VisionInputError("ONVIF camera returned no media profiles")

        profile = next(
            (
                item
                for item in profiles
                if getattr(item, "VideoSourceConfiguration", None) is not None
                and getattr(item, "VideoEncoderConfiguration", None) is not None
            ),
            profiles[0],
        )
        token = _profile_token(profile)
        stream = media.GetStreamUri(
            ProfileToken=token,
            StreamSetup={
                "Stream": "RTP-Unicast",
                "Transport": {"Protocol": "RTSP"},
            },
        )
        source_uri = _uri_field(stream)
        connection_uri = _with_rtsp_credentials(
            source_uri,
            username,
            password,
        )
        return ONVIFStreamResolution(
            profile_token=token,
            source_uri=source_uri,
            connection_uri=connection_uri,
        )
    except VisionInputError:
        raise
    except Exception as exc:
        raise VisionInputError(f"ONVIF stream resolution failed: {exc}") from exc
