from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from dlf_flywire.execution import (
    ExecutionEngine,
    ExecutionRequest,
    RecoveryBlocked,
    verify_receipt,
)
from dlf_flywire.policy import ExecutionIntent


def request(step_id="hello", idempotent=True):
    return ExecutionRequest(
        capability="runtime.python",
        backend="current-python",
        argv=(sys.executable, "-c", "print('ok')"),
        step_id=step_id,
        idempotent=idempotent,
    )


def test_execution_writes_receipt_and_checkpoint(tmp_path):
    engine = ExecutionEngine(tmp_path / "state")
    receipt = engine.execute(request())
    assert receipt.status == "succeeded"
    assert receipt.returncode == 0
    assert receipt.stdout.strip() == "ok"

    checkpoint = json.loads(
        (tmp_path / "state" / "checkpoints" / f"{receipt.run_id}.json").read_text(
            encoding="utf-8"
        )
    )
    assert checkpoint["steps"]["hello"]["status"] == "succeeded"

    stored = json.loads(
        (
            tmp_path
            / "state"
            / "receipts"
            / receipt.run_id
            / "hello.json"
        ).read_text(encoding="utf-8")
    )
    assert verify_receipt(stored).receipt_sha256 == receipt.receipt_sha256


def test_resume_skips_completed_step(tmp_path):
    engine = ExecutionEngine(tmp_path / "state")
    first = engine.execute(request())
    second = engine.execute(request(), run_id=first.run_id)
    assert second.receipt_sha256 == first.receipt_sha256
    assert second.recovered is False


def test_interrupted_non_idempotent_step_is_blocked(tmp_path):
    engine = ExecutionEngine(tmp_path / "state")
    run_id = "recovery-test"
    engine._write_checkpoint(
        run_id,
        {
            "step": {
                "status": "running",
                "capability": "runtime.python",
                "backend": "current-python",
                "argv": [sys.executable, "-c", "print('danger')"],
            }
        },
    )
    with pytest.raises(RecoveryBlocked):
        engine.execute(
            ExecutionRequest(
                capability="runtime.python",
                backend="current-python",
                argv=(sys.executable, "-c", "print('danger')"),
                step_id="step",
                idempotent=False,
            ),
            run_id=run_id,
        )


def test_interrupted_idempotent_step_replays_and_marks_recovery(tmp_path):
    engine = ExecutionEngine(tmp_path / "state")
    run_id = "recovery-test"
    request_to_recover = ExecutionRequest(
        capability="runtime.python",
        backend="current-python",
        argv=(sys.executable, "-c", "print('recovered')"),
        step_id="step",
        cwd=str(Path.cwd().resolve()),
        idempotent=True,
    )
    from dlf_flywire.execution import _request_fingerprint

    engine._write_checkpoint(
        run_id,
        {
            "step": {
                "status": "running",
                "capability": request_to_recover.capability,
                "backend": request_to_recover.backend,
                "argv": list(request_to_recover.argv),
                "request_sha256": _request_fingerprint(
                    request_to_recover, str(Path.cwd().resolve())
                ),
            }
        },
    )
    receipt = engine.execute(request_to_recover, run_id=run_id)
    assert receipt.status == "succeeded"
    assert receipt.recovered is True


def test_receipt_tampering_is_rejected(tmp_path):
    engine = ExecutionEngine(tmp_path / "state")
    receipt = engine.execute(request())
    data = receipt.to_dict()
    data["stdout"] = "tampered"
    with pytest.raises(Exception, match="stdout hash mismatch"):
        verify_receipt(data)


def test_timeout_is_recorded(tmp_path):
    engine = ExecutionEngine(tmp_path / "state")
    receipt = engine.execute(
        ExecutionRequest(
            capability="runtime.python",
            backend="current-python",
            argv=(sys.executable, "-c", "import time; time.sleep(1)"),
            step_id="slow",
            timeout_seconds=0.05,
            idempotent=True,
        )
    )
    assert receipt.status == "timeout"
    assert receipt.returncode is None


def test_interrupted_step_with_changed_request_is_blocked(tmp_path):
    engine = ExecutionEngine(tmp_path / "state")
    run_id = "fingerprint-test"
    original = request(step_id="step")
    cwd = str(tmp_path.resolve())
    from dlf_flywire.execution import _request_fingerprint

    engine._write_checkpoint(
        run_id,
        {
            "step": {
                "status": "running",
                "capability": original.capability,
                "backend": original.backend,
                "argv": list(original.argv),
                "request_sha256": _request_fingerprint(original, cwd),
                "started_at": "2026-01-01T00:00:00+00:00",
            }
        },
    )
    changed = ExecutionRequest(
        capability=original.capability,
        backend=original.backend,
        argv=(sys.executable, "-c", "print('changed')"),
        step_id="step",
        idempotent=True,
    )
    with pytest.raises(RecoveryBlocked, match="fingerprint changed"):
        engine.execute(changed, run_id=run_id)


def test_malformed_checkpoint_fails_closed(tmp_path):
    engine = ExecutionEngine(tmp_path / "state")
    path = tmp_path / "state" / "checkpoints" / "bad.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(RecoveryBlocked, match="unreadable or malformed"):
        engine.execute(request(), run_id="bad")


def test_capability_executor_probes_before_execution(tmp_path):
    from dlf_flywire.capabilities import BackendSpec, CapabilityDoctor, CapabilitySpec
    from dlf_flywire.execution import CapabilityExecutor

    spec = CapabilitySpec(
        "runtime.python.test",
        "test python execution capability",
        (BackendSpec("python", sys.executable),),
    )
    executor = CapabilityExecutor(
        CapabilityDoctor((spec,)),
        ExecutionEngine(tmp_path / "state"),
    )
    receipt = executor.execute(
        "runtime.python.test",
        "probe-first",
        ("-c", "print('capability-routed')"),
        intent=ExecutionIntent(
            capability="runtime.python.test",
            action="print test output",
            destination="test-process",
            risk_tier=0,
            permission_granted=True,
        ),
        idempotent=True,
    )
    assert receipt.status == "succeeded"
    assert receipt.backend == "python"
    assert receipt.capability_probe["probe"]["status"] == "ok"
    assert receipt.stdout.strip() == "capability-routed"


def test_capability_executor_fails_when_capability_unavailable(tmp_path, monkeypatch):
    from dlf_flywire.capabilities import BackendSpec, CapabilityDoctor, CapabilitySpec
    from dlf_flywire.execution import CapabilityExecutor, ExecutionError

    spec = CapabilitySpec(
        "missing.capability",
        "missing executable",
        (BackendSpec("missing", "definitely-not-installed-dlf"),),
    )
    monkeypatch.setattr(
        "dlf_flywire.capabilities.shutil.which",
        lambda _name: None,
    )
    executor = CapabilityExecutor(
        CapabilityDoctor((spec,)),
        ExecutionEngine(tmp_path / "state"),
    )
    with pytest.raises(ExecutionError, match="no healthy backend"):
        executor.execute("missing.capability", "blocked", idempotent=True)
