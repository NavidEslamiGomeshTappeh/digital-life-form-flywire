from __future__ import annotations

from dlf_flywire import cli
from dlf_flywire.network_ptz import PTZProbeResult


def test_probe_camera_ptz_cli_uses_environment_credentials(monkeypatch, tmp_path):
    observed = PTZProbeResult(
        schema_version=1,
        observed_at_utc="2026-10-07T10:00:00+00:00",
        host="192.168.1.20",
        port=80,
        profile_token="profile-1",
        ptz_configuration_token="ptz-config-1",
        pan_tilt_position={"pan": 0.25, "tilt": -0.1},
        move_status={"pan_tilt": "IDLE", "zoom": "IDLE"},
        continuous_velocity_range={
            "pan_min": -1.0,
            "pan_max": 1.0,
            "tilt_min": -0.5,
            "tilt_max": 0.5,
        },
        movement_commands_issued=False,
    )

    def fake_probe(**kwargs):
        assert kwargs == {
            "host": "192.168.1.20",
            "port": 80,
            "username": "admin",
            "password": "secret",
        }
        return observed

    monkeypatch.setenv("TEST_CAMERA_HOST", "192.168.1.20")
    monkeypatch.setenv("TEST_CAMERA_USER", "admin")
    monkeypatch.setenv("TEST_CAMERA_PASS", "secret")
    monkeypatch.setattr("dlf_flywire.network_ptz.probe_onvif_ptz", fake_probe)

    output = tmp_path / "ptz.json"
    assert (
        cli.main(
            [
                "probe-camera-ptz",
                "--host-env",
                "TEST_CAMERA_HOST",
                "--username-env",
                "TEST_CAMERA_USER",
                "--password-env",
                "TEST_CAMERA_PASS",
                "--output",
                str(output),
            ]
        )
        == 0
    )

    payload = output.read_text(encoding="utf-8")
    assert '"movement_commands_issued": false' in payload
    assert '"profile_token": "profile-1"' in payload
    assert "secret" not in payload


def test_probe_camera_ptz_cli_fails_without_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("MISSING_CAMERA_HOST", raising=False)
    monkeypatch.delenv("MISSING_CAMERA_USER", raising=False)
    monkeypatch.delenv("MISSING_CAMERA_PASS", raising=False)

    assert (
        cli.main(
            [
                "probe-camera-ptz",
                "--host-env",
                "MISSING_CAMERA_HOST",
                "--username-env",
                "MISSING_CAMERA_USER",
                "--password-env",
                "MISSING_CAMERA_PASS",
                "--output",
                str(tmp_path / "ptz.json"),
            ]
        )
        == 2
    )
