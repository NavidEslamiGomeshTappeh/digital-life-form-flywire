from __future__ import annotations

import hashlib

import pytest

from dlf_flywire.vision_input import (
    OpenCVCameraSource,
    VisionFrame,
    VisionInputError,
    build_capture_receipt,
)


def test_gray8_frame_preserves_content_and_normalizes_without_rescaling():
    frame = VisionFrame.from_gray8(
        frame_index=3,
        width=2,
        height=2,
        pixels_gray8=bytes([0, 64, 128, 255]),
        captured_at_utc="2026-10-05T10:30:00+00:00",
    )

    assert frame.pixels_sha256 == hashlib.sha256(bytes([0, 64, 128, 255])).hexdigest()
    assert frame.to_float_rows() == (
        (0.0, 64 / 255.0),
        (128 / 255.0, 1.0),
    )


def test_gray8_frame_writes_exact_binary_pgm(tmp_path):
    frame = VisionFrame.from_gray8(
        frame_index=0,
        width=2,
        height=1,
        pixels_gray8=bytes([7, 251]),
        captured_at_utc="2026-10-05T10:30:00+00:00",
    )

    path = tmp_path / "frame-0000.pgm"
    file_sha256 = frame.write_pgm(path)

    expected = b"P5\n2 1\n255\n\x07\xfb"
    assert path.read_bytes() == expected
    assert file_sha256 == hashlib.sha256(expected).hexdigest()


def test_capture_receipt_binds_each_frame_to_its_artifact():
    frames = (
        VisionFrame.from_gray8(
            frame_index=0,
            width=1,
            height=1,
            pixels_gray8=b"\x10",
            captured_at_utc="2026-10-05T10:30:00+00:00",
        ),
        VisionFrame.from_gray8(
            frame_index=1,
            width=1,
            height=1,
            pixels_gray8=b"\x20",
            captured_at_utc="2026-10-05T10:30:00.005000+00:00",
        ),
    )

    receipt = build_capture_receipt(
        frames,
        source_kind="camera/opencv",
        source_locator="device-index:0",
        artifact_paths=("frames/0000.pgm", "frames/0001.pgm"),
    )

    assert receipt.to_dict() == {
        "schema_version": 1,
        "source_kind": "camera/opencv",
        "source_locator": "device-index:0",
        "frame_count": 2,
        "frames": [
            {
                "frame_index": 0,
                "captured_at_utc": "2026-10-05T10:30:00+00:00",
                "width": 1,
                "height": 1,
                "encoding": "gray8",
                "pixel_sha256": hashlib.sha256(b"\x10").hexdigest(),
                "artifact_path": "frames/0000.pgm",
            },
            {
                "frame_index": 1,
                "captured_at_utc": "2026-10-05T10:30:00.005000+00:00",
                "width": 1,
                "height": 1,
                "encoding": "gray8",
                "pixel_sha256": hashlib.sha256(b"\x20").hexdigest(),
                "artifact_path": "frames/0001.pgm",
            },
        ],
    }


def test_frame_rejects_bad_payload_length():
    with pytest.raises(VisionInputError, match="payload length"):
        VisionFrame.from_gray8(
            frame_index=0,
            width=2,
            height=2,
            pixels_gray8=b"\x00",
        )


def test_frame_rejects_tampered_hash():
    with pytest.raises(VisionInputError, match="SHA-256 mismatch"):
        VisionFrame(
            frame_index=0,
            captured_at_utc="2026-10-05T10:30:00+00:00",
            width=1,
            height=1,
            pixels_gray8=b"\x01",
            pixels_sha256="0" * 64,
        )


def test_camera_source_validates_bounds_before_optional_dependency():
    source = OpenCVCameraSource(device_index=0)
    with pytest.raises(VisionInputError, match="frame_count must be positive"):
        source.capture(frame_count=0)
