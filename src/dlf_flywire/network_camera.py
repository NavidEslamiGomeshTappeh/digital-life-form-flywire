from __future__ import annotations

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
