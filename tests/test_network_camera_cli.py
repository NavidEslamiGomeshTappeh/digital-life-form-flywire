from __future__ import annotations

import json

from dlf_flywire import cli
from dlf_flywire.network_camera import redact_stream_url
from dlf_flywire.vision_input import VisionFrame


def test_capture_network_camera_cli_uses_environment_url_and_writes_receipt(
    monkeypatch, tmp_path
):
    frame = VisionFrame.from_gray8(
        frame_index=0,
        width=2,
        height=1,
        pixels_gray8=b"\x10\xf0",
        captured_at_utc="2026-10-07T10:00:00+00:00",
    )

    class FakeSource:
        def __init__(self, stream_url, **kwargs):
            assert stream_url == "rtsp://user:secret@example.local:554/live/main?token=hidden"
            assert kwargs["width"] == 640
            assert kwargs["height"] == 360
            self.source_locator = redact_stream_url(stream_url)

        def capture(self, frame_count):
            assert frame_count == 1
            return (frame,)

    monkeypatch.setenv(
        "TEST_DLF_RTSP_URL",
        "rtsp://user:secret@example.local:554/live/main?token=hidden",
    )
    monkeypatch.setattr("dlf_flywire.network_camera.NetworkCameraSource", FakeSource)

    output = tmp_path / "capture"
    assert (
        cli.main(
            [
                "capture-network-camera",
                "--url-env",
                "TEST_DLF_RTSP_URL",
                "--frames",
                "1",
                "--width",
                "640",
                "--height",
                "360",
                "--output",
                str(output),
            ]
        )
        == 0
    )

    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["source_kind"] == "camera/rtsp"
    assert receipt["source_locator"] == "rtsp://example.local:554/live/main"
    assert receipt["frame_count"] == 1
    assert (output / "frame-000000.pgm").is_file()


def test_capture_network_camera_cli_fails_when_url_is_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("MISSING_DLF_RTSP_URL", raising=False)

    assert (
        cli.main(
            [
                "capture-network-camera",
                "--url-env",
                "MISSING_DLF_RTSP_URL",
                "--output",
                str(tmp_path / "capture"),
            ]
        )
        == 2
    )
