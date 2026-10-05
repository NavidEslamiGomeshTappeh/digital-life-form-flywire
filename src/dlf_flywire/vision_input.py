from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic


class VisionInputError(ValueError):
    """Raised when a visual input frame or capture source is invalid."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class VisionFrame:
    """Immutable grayscale camera/frame artifact with content provenance."""

    frame_index: int
    captured_at_utc: str
    width: int
    height: int
    pixels_gray8: bytes
    pixels_sha256: str

    def __post_init__(self) -> None:
        if isinstance(self.frame_index, bool) or not isinstance(self.frame_index, int):
            raise VisionInputError("frame_index must be an integer")
        if self.frame_index < 0:
            raise VisionInputError("frame_index must be non-negative")
        if not self.captured_at_utc.strip():
            raise VisionInputError("captured_at_utc must not be empty")
        for name, value in (("width", self.width), ("height", self.height)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise VisionInputError(f"{name} must be a positive integer")
        expected_size = self.width * self.height
        if len(self.pixels_gray8) != expected_size:
            raise VisionInputError(
                f"gray8 payload length {len(self.pixels_gray8)} != {expected_size}"
            )
        observed = _sha256_bytes(self.pixels_gray8)
        if observed != self.pixels_sha256:
            raise VisionInputError(
                f"pixel SHA-256 mismatch: expected {self.pixels_sha256}, observed {observed}"
            )

    @classmethod
    def from_gray8(
        cls,
        *,
        frame_index: int,
        width: int,
        height: int,
        pixels_gray8: bytes,
        captured_at_utc: str | None = None,
    ) -> VisionFrame:
        payload = bytes(pixels_gray8)
        return cls(
            frame_index=frame_index,
            captured_at_utc=captured_at_utc or _utc_now_iso(),
            width=width,
            height=height,
            pixels_gray8=payload,
            pixels_sha256=_sha256_bytes(payload),
        )

    def to_float_rows(self) -> tuple[tuple[float, ...], ...]:
        """Return normalized grayscale rows in [0, 1]."""
        return tuple(
            tuple(
                value / 255.0
                for value in self.pixels_gray8[row_start : row_start + self.width]
            )
            for row_start in range(0, len(self.pixels_gray8), self.width)
        )

    def write_pgm(self, path: str | Path) -> str:
        """Persist the exact gray8 payload as a binary PGM and return file SHA-256."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        header = f"P5\n{self.width} {self.height}\n255\n".encode("ascii")
        raw = header + self.pixels_gray8
        destination.write_bytes(raw)
        return _sha256_bytes(raw)

    def receipt_record(self, *, artifact_path: str | None = None) -> dict[str, object]:
        record: dict[str, object] = {
            "frame_index": self.frame_index,
            "captured_at_utc": self.captured_at_utc,
            "width": self.width,
            "height": self.height,
            "encoding": "gray8",
            "pixel_sha256": self.pixels_sha256,
        }
        if artifact_path is not None:
            record["artifact_path"] = artifact_path
        return record


@dataclass(frozen=True)
class VisionCaptureReceipt:
    """Machine-readable record of a bounded visual capture."""

    schema_version: int
    source_kind: str
    source_locator: str
    frames: tuple[dict[str, object], ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise VisionInputError("unsupported vision receipt schema")
        if not self.source_kind.strip() or not self.source_locator.strip():
            raise VisionInputError("source metadata must not be empty")
        if not self.frames:
            raise VisionInputError("capture receipt must contain at least one frame")
        seen_indices: set[int] = set()
        for record in self.frames:
            if not isinstance(record, dict):
                raise VisionInputError("each receipt frame must be an object")
            frame_index = record.get("frame_index")
            if (
                isinstance(frame_index, bool)
                or not isinstance(frame_index, int)
                or frame_index < 0
            ):
                raise VisionInputError("receipt frame_index must be non-negative")
            if frame_index in seen_indices:
                raise VisionInputError(
                    f"duplicate receipt frame_index: {frame_index}"
                )
            seen_indices.add(frame_index)
            for field in ("captured_at_utc", "encoding", "pixel_sha256"):
                value = record.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise VisionInputError(
                        f"receipt frame field {field} must be a non-empty string"
                    )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_kind": self.source_kind,
            "source_locator": self.source_locator,
            "frame_count": len(self.frames),
            "frames": list(self.frames),
        }

    def write(self, path: str | Path) -> str:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, indent=2
        ).encode("utf-8")
        destination.write_bytes(raw)
        return _sha256_bytes(raw)


class OpenCVCameraSource:
    """Bounded physical-camera capture; OpenCV remains an optional dependency."""

    def __init__(
        self,
        device_index: int = 0,
        *,
        width: int | None = None,
        height: int | None = None,
        per_frame_timeout_s: float = 5.0,
    ) -> None:
        if isinstance(device_index, bool) or not isinstance(device_index, int):
            raise VisionInputError("device_index must be an integer")
        if device_index < 0:
            raise VisionInputError("device_index must be non-negative")
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
        self.device_index = device_index
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
                "OpenCV is required for physical-camera capture; "
                "install the optional vision runtime dependency"
            ) from exc

        camera = cv2.VideoCapture(self.device_index)
        try:
            if not camera.isOpened():
                raise VisionInputError(
                    f"camera device {self.device_index} could not be opened"
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
                        f"camera read failed at frame {frame_index}"
                    )
                if elapsed > self.per_frame_timeout_s:
                    raise VisionInputError(
                        f"camera read exceeded timeout at frame {frame_index}: "
                        f"{elapsed:.3f}s"
                    )

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                height, width = gray.shape[:2]
                payload = gray.tobytes()
                frames.append(
                    VisionFrame.from_gray8(
                        frame_index=frame_index,
                        width=int(width),
                        height=int(height),
                        pixels_gray8=payload,
                    )
                )
            return tuple(frames)
        finally:
            camera.release()


def build_capture_receipt(
    frames: Sequence[VisionFrame],
    *,
    source_kind: str,
    source_locator: str,
    artifact_paths: Sequence[str | None] | None = None,
) -> VisionCaptureReceipt:
    """Bind bounded frame content to its source metadata."""
    frozen_frames = tuple(frames)
    if not frozen_frames:
        raise VisionInputError("frames must not be empty")
    if artifact_paths is not None and len(artifact_paths) != len(frozen_frames):
        raise VisionInputError("artifact_paths length must match frames length")
    records = tuple(
        frame.receipt_record(
            artifact_path=None if artifact_paths is None else artifact_paths[index]
        )
        for index, frame in enumerate(frozen_frames)
    )
    return VisionCaptureReceipt(
        schema_version=1,
        source_kind=source_kind,
        source_locator=source_locator,
        frames=records,
    )



@dataclass(frozen=True)
class FlyVisBoxEyeFrame:
    """One VisionFrame rendered through FlyVis' published BoxEye contract."""

    source_pixel_sha256: str
    hexal_count: int
    rendered_shape: tuple[int, int, int, int]
    rendered_sha256: str


def render_with_flyvis_boxeye(
    frame: VisionFrame,
    *,
    extent: int = 15,
    kernel_size: int = 13,
) -> FlyVisBoxEyeFrame:
    """Render one grayscale frame through the pinned upstream BoxEye implementation."""
    if extent <= 0 or kernel_size <= 0:
        raise VisionInputError("extent and kernel_size must be positive")
    try:
        import torch
        from flyvis.datasets.rendering import BoxEye
    except ImportError as exc:
        raise VisionInputError(
            "FlyVis and PyTorch are required for BoxEye rendering; "
            "use the pinned FlyVis integration environment"
        ) from exc

    rows = frame.to_float_rows()
    tensor = torch.tensor([[list(row) for row in rows]], dtype=torch.float32)
    rendered = BoxEye(extent=extent, kernel_size=kernel_size)(tensor)
    shape = tuple(int(value) for value in rendered.shape)
    expected_shape = (1, 1, 1, 1 + 3 * extent * (extent + 1))
    if shape != expected_shape:
        raise VisionInputError(
            f"unexpected BoxEye output shape {shape}; expected {expected_shape}"
        )
    rendered_cpu = rendered.detach().cpu().contiguous()
    rendered_bytes = rendered_cpu.numpy().tobytes()
    return FlyVisBoxEyeFrame(
        source_pixel_sha256=frame.pixels_sha256,
        hexal_count=shape[-1],
        rendered_shape=shape,
        rendered_sha256=_sha256_bytes(rendered_bytes),
    )
