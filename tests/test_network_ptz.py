from __future__ import annotations

import sys
import types

import pytest

from dlf_flywire.network_ptz import PTZProbeError, probe_onvif_ptz


class FakeValue:
    def __init__(self, **values):
        self.__dict__.update(values)


def test_ptz_probe_reads_status_and_velocity_ranges_without_moving(monkeypatch):
    profile = FakeValue(
        token="profile-1",
        PTZConfiguration=FakeValue(token="ptz-config-1"),
    )
    status = FakeValue(
        Position=FakeValue(PanTilt=FakeValue(x=0.25, y=-0.10)),
        MoveStatus=FakeValue(PanTilt="IDLE", Zoom="IDLE"),
    )
    options = FakeValue(
        Spaces=FakeValue(
            ContinuousPanTiltVelocitySpace=[
                FakeValue(
                    XRange=FakeValue(Min=-1.0, Max=1.0),
                    YRange=FakeValue(Min=-0.5, Max=0.5),
                )
            ]
        )
    )

    class FakeMedia:
        def GetProfiles(self):
            return [profile]

    class FakePTZ:
        def GetStatus(self, ProfileToken):
            assert ProfileToken == "profile-1"
            return status

        def GetConfigurationOptions(self, ConfigurationToken):
            assert ConfigurationToken == "ptz-config-1"
            return options

    class FakeClient:
        def __init__(self, host, port, username, password):
            assert (host, port, username, password) == (
                "192.168.1.20",
                80,
                "admin",
                "secret",
            )

        def media(self):
            return FakeMedia()

        def ptz(self):
            return FakePTZ()

    monkeypatch.setitem(
        sys.modules,
        "onvif",
        types.SimpleNamespace(ONVIFClient=FakeClient),
    )

    result = probe_onvif_ptz(
        host="192.168.1.20",
        port=80,
        username="admin",
        password="secret",
    )

    assert result.profile_token == "profile-1"
    assert result.ptz_configuration_token == "ptz-config-1"
    assert result.pan_tilt_position == {"pan": 0.25, "tilt": -0.1}
    assert result.move_status == {"pan_tilt": "IDLE", "zoom": "IDLE"}
    assert result.continuous_velocity_range == {
        "pan_min": -1.0,
        "pan_max": 1.0,
        "tilt_min": -0.5,
        "tilt_max": 0.5,
    }
    assert result.movement_commands_issued is False


def test_ptz_probe_validates_arguments_before_optional_dependency():
    with pytest.raises(PTZProbeError, match="host"):
        probe_onvif_ptz(host="", port=80, username="a", password="b")
    with pytest.raises(PTZProbeError, match="port"):
        probe_onvif_ptz(host="192.168.1.20", port=0, username="a", password="b")


def test_ptz_probe_fails_closed_when_optional_runtime_is_missing(monkeypatch):
    def blocked_import(name, *args, **kwargs):
        if name == "onvif":
            raise ImportError("blocked")
        return __import__(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", blocked_import)

    with pytest.raises(PTZProbeError, match="onvif-python==0.4.4"):
        probe_onvif_ptz(
            host="192.168.1.20",
            port=80,
            username="admin",
            password="secret",
        )
