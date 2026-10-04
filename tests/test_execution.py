from __future__ import annotations

import json
import sys

import pytest

from dlf_flywire.execution import (
    ExecutionEngine,
    ExecutionRequest,
    RecoveryBlocked,
    verify_receipt,
)


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
    engine._write_checkpoint(
        run_id,
        {
            "step": {
                "status": "running",
                "capability": "runtime.python",
                "backend": "current-python",
                "argv": [sys.executable, "-c", "print('recovered')"],
            }
        },
    )
    receipt = engine.execute(
        ExecutionRequest(
            capability="runtime.python",
            backend="current-python",
            argv=(sys.executable, "-c", "print('recovered')"),
            step_id="step",
            idempotent=True,
        ),
        run_id=run_id,
    )
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
