from __future__ import annotations

import sys
import types

import pytest

from dlf_flywire.network_camera import (
    NetworkCameraSource,
    redact_stream_url,
)
from dlf_flywire.vision_input import VisionInputError


def test_redact_stream_url_removes_credentials_and_query():
    assert (
        redact_stream_url(
            "rtsp://operator:secret@example.local:554/live/main?token=hidden#x"
        )
        == "rtsp://example.local:554/live/main"
    )


def test_network_camera_requires_rtsp_scheme():
    with pytest.raises(VisionInputError, match="rtsp"):
        NetworkCameraSource("http://example.local/video")


def test_network_camera_validates_frame_count_before_optional_dependency():
    source = NetworkCameraSource("rtsp://example.local/live")
    with pytest.raises(VisionInputError, match="frame_count must be positive"):
        source.capture(frame_count=0)


def test_network_camera_capture_converts_frames_to_gray8(monkeypatch):
    class FakeFrame:
        def __init__(self, payload: bytes, width: int, height: int):
            self._payload = payload
            self.shape = (height, width, 3)

    class FakeGray:
        def __init__(self, payload: bytes, width: int, height: int):
            self._payload = payload
            self.shape = (height, width)

        def tobytes(self):
            return self._payload

    class FakeCapture:
        def __init__(self):
            self.released = False
            self.set_calls = []
            self.frames = [
                FakeFrame(b"ignored", 2, 1),
                FakeFrame(b"ignored", 2, 1),
            ]

        def set(self, prop, value):
            self.set_calls.append((prop, value))
            return True

        def isOpened(self):
            return True

        def read(self):
            frame = self.frames.pop(0)
            return True, frame

        def release(self):
            self.released = True

    capture = FakeCapture()
    fake_cv2 = types.SimpleNamespace(
        CAP_PROP_OPEN_TIMEOUT_MSEC=100,
        CAP_PROP_READ_TIMEOUT_MSEC=101,
        CAP_PROP_FRAME_WIDTH=3,
        CAP_PROP_FRAME_HEIGHT=4,
        COLOR_BGR2GRAY=5,
        VideoCapture=lambda url: capture,
        cvtColor=lambda frame, code: FakeGray(
            b" ", frame.shape[1], frame.shape[0]
        ),
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)

    source = NetworkCameraSource(
        "rtsp://user:pass@example.local/live",
        width=640,
        height=360,
    )
    frames = source.capture(frame_count=2)

    assert source.source_locator == "rtsp://example.local/live"
    assert [frame.pixels_gray8 for frame in frames] == [b" ", b" "]
    assert [frame.frame_index for frame in frames] == [0, 1]
    assert capture.released is True
    assert capture.set_calls[0][0] == fake_cv2.CAP_PROP_OPEN_TIMEOUT_MSEC
    assert capture.set_calls[1][0] == fake_cv2.CAP_PROP_READ_TIMEOUT_MSEC
    assert (fake_cv2.CAP_PROP_FRAME_WIDTH, 640) in capture.set_calls
    assert (fake_cv2.CAP_PROP_FRAME_HEIGHT, 360) in capture.set_calls


def test_network_camera_releases_capture_when_open_fails(monkeypatch):
    class FakeCapture:
        released = False

        def isOpened(self):
            return False

        def set(self, prop, value):
            return True

        def release(self):
            self.released = True

    capture = FakeCapture()
    fake_cv2 = types.SimpleNamespace(VideoCapture=lambda url: capture)
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)

    source = NetworkCameraSource("rtsp://example.local/live")
    with pytest.raises(VisionInputError, match="could not be opened"):
        source.capture()

    assert capture.released is True
