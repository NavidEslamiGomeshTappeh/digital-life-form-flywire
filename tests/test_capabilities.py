from __future__ import annotations

import subprocess

import pytest

from dlf_flywire.capabilities import (
    BackendSpec,
    CapabilityDoctor,
    CapabilitySpec,
    default_capabilities,
    probe_backend,
)


def backend(name: str) -> BackendSpec:
    return BackendSpec(name=name, executable=name)


def test_probe_missing(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _name: None)
    result = probe_backend(backend("missing-tool"))
    assert result.status == "missing"


def test_probe_broken(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _name: "/broken/tool")

    def fail(*_args, **_kwargs):
        raise FileNotFoundError("missing interpreter")

    monkeypatch.setattr(subprocess, "run", fail)
    assert probe_backend(backend("broken-tool")).status == "broken"


def test_probe_timeout(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _name: "/slow/tool")

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["slow-tool"], 1)

    monkeypatch.setattr(subprocess, "run", timeout)
    assert probe_backend(backend("slow-tool")).status == "timeout"


def test_probe_is_no_shell(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _name: "/usr/bin/tool")
    seen = {}

    def run(cmd, **kwargs):
        seen["cmd"] = cmd
        seen["shell"] = kwargs["shell"]
        return subprocess.CompletedProcess(cmd, 0, "tool 1.2.3", "")

    monkeypatch.setattr(subprocess, "run", run)
    result = probe_backend(backend("tool"))
    assert result.status == "ok"
    assert seen["cmd"] == ["/usr/bin/tool", "--version"]
    assert seen["shell"] is False


def test_doctor_falls_back_to_first_healthy(monkeypatch):
    calls = []

    def fake_probe(spec):
        calls.append(spec.name)
        if spec.name == "second":
            return type("R", (), {
                "ok": True,
                "status": "ok",
                "to_dict": lambda self: {"status": "ok", "output": "", "duration_ms": 0},
            })()
        return type("R", (), {
            "ok": False,
            "status": "missing",
            "to_dict": lambda self: {"status": "missing", "output": "", "duration_ms": 0},
        })()

    monkeypatch.setattr("dlf_flywire.capabilities.probe_backend", fake_probe)
    doctor = CapabilityDoctor(
        (CapabilitySpec("test", "test", (backend("first"), backend("second"), backend("third"))),)
    )
    report = doctor.check()
    assert report["capabilities"][0]["active_backend"] == "second"
    assert calls == ["first", "second"]


def test_doctor_override_moves_backend_to_front(monkeypatch):
    calls = []

    def fake_probe(spec):
        calls.append(spec.name)
        return type("R", (), {
            "ok": spec.name == "forced",
            "status": "ok" if spec.name == "forced" else "missing",
            "to_dict": lambda self: {
                "status": "ok" if spec.name == "forced" else "missing",
                "output": "",
                "duration_ms": 0,
            },
        })()

    monkeypatch.setattr("dlf_flywire.capabilities.probe_backend", fake_probe)
    spec = CapabilitySpec(
        "test", "test", (backend("preferred"), backend("forced"), backend("fallback"))
    )
    report = CapabilityDoctor((spec,)).check({"test": "forced"})
    assert report["capabilities"][0]["active_backend"] == "forced"
    assert calls == ["forced"]


def test_unknown_override_cannot_hide_candidates(monkeypatch):
    calls = []

    def fake_probe(spec):
        calls.append(spec.name)
        return type("R", (), {
            "ok": False,
            "status": "missing",
            "to_dict": lambda self: {"status": "missing", "output": "", "duration_ms": 0},
        })()

    monkeypatch.setattr("dlf_flywire.capabilities.probe_backend", fake_probe)
    spec = CapabilitySpec("test", "test", (backend("preferred"), backend("fallback")))
    report = CapabilityDoctor((spec,)).check({"test": "unknown"})
    assert calls == ["preferred", "fallback"]
    assert report["counts"] == {"ok": 0, "off": 1, "error": 0}


def test_capability_exceptions_are_isolated(monkeypatch):
    good = CapabilitySpec("good", "good", (backend("good"),))
    bad = CapabilitySpec("bad", "bad", (backend("bad"),))

    def fake_probe(spec):
        if spec.name == "bad":
            raise RuntimeError("boom")
        return type("R", (), {
            "ok": True,
            "status": "ok",
            "to_dict": lambda self: {"status": "ok", "output": "", "duration_ms": 0},
        })()

    monkeypatch.setattr("dlf_flywire.capabilities.probe_backend", fake_probe)
    by_name = {x["name"]: x for x in CapabilityDoctor((good, bad)).check()["capabilities"]}
    assert by_name["good"]["status"] == "ok"
    assert by_name["bad"]["status"] == "error"


def test_default_capabilities_are_stable():
    assert [x.name for x in default_capabilities()] == [
        "runtime.python",
        "runtime.git",
        "package.import",
        "tool.build",
    ]


def test_select_unknown_capability_fails_closed():
    from dlf_flywire.capabilities import CapabilitySelectionError

    with pytest.raises(CapabilitySelectionError, match="unknown capability"):
        CapabilityDoctor(default_capabilities()).select("does.not.exist")
