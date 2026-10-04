from __future__ import annotations

import json
import sys

from dlf_flywire.capabilities import BackendSpec, CapabilityDoctor, CapabilitySpec
from dlf_flywire.execution import CapabilityExecutor, ExecutionEngine
from dlf_flywire.orchestrator import RunPlan, TaskOrchestrator, TaskStep
from dlf_flywire.verifier import verify_run


def make_executor(tmp_path):
    spec = CapabilitySpec(
        "runtime.python.test",
        "verifier test capability",
        (BackendSpec("python", sys.executable),),
    )
    return CapabilityExecutor(
        CapabilityDoctor((spec,)),
        ExecutionEngine(tmp_path / "state"),
    )


def step(step_id):
    return TaskStep(
        step_id=step_id,
        capability="runtime.python.test",
        action=f"run {step_id}",
        destination="test-process",
        risk_tier=0,
        permission_granted=True,
        operation_args=("-c", "print('ok')"),
        idempotent=True,
    )


def test_independent_verifier_requires_succeeded_run_state(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    plan = RunPlan((step("one"),))
    run_id, _ = orchestrator.run(plan, run_id="verify-state")
    state_path = tmp_path / "state" / "plans" / f"{run_id}.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["status"] = "running"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    verification = verify_run(plan, run_id, state_root=tmp_path / "state")
    assert verification.status == "FAIL"
    assert "run state is not succeeded" in verification.errors


def test_independent_verifier_rejects_unexpected_state_step(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    plan = RunPlan((step("one"),))
    run_id, _ = orchestrator.run(plan, run_id="verify-extra")
    state_path = tmp_path / "state" / "plans" / f"{run_id}.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["steps"]["unexpected"] = {"status": "succeeded"}
    state_path.write_text(json.dumps(state), encoding="utf-8")
    verification = verify_run(plan, run_id, state_root=tmp_path / "state")
    assert verification.status == "FAIL"
    assert any("unexpected state steps" in e for e in verification.errors)
