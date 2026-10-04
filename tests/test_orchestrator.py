from __future__ import annotations

import json
import sys

import pytest

from dlf_flywire.capabilities import BackendSpec, CapabilityDoctor, CapabilitySpec
from dlf_flywire.execution import CapabilityExecutor, ExecutionEngine, ExecutionError
from dlf_flywire.orchestrator import (
    OrchestrationError,
    PlanChanged,
    RunPlan,
    TaskOrchestrator,
    TaskStep,
    verify_run,
)
from dlf_flywire.policy import ExecutionIntent


def make_executor(tmp_path):
    spec = CapabilitySpec(
        "runtime.python.test",
        "orchestration test capability",
        (BackendSpec("python", sys.executable),),
    )
    return CapabilityExecutor(
        CapabilityDoctor((spec,)),
        ExecutionEngine(tmp_path / "state"),
    )


def step(step_id, deps=(), command="print('ok')", granted=True):
    return TaskStep(
        step_id=step_id,
        capability="runtime.python.test",
        action=f"run {step_id}",
        destination="test-process",
        risk_tier=0,
        permission_granted=granted,
        operation_args=("-c", command),
        dependencies=tuple(deps),
        idempotent=True,
    )


def test_plan_orders_dependencies():
    plan = RunPlan((step("b", ("a",)), step("a")))
    assert [x.step_id for x in plan.ordered_steps()] == ["a", "b"]


def test_plan_rejects_cycles():
    with pytest.raises(OrchestrationError, match="cycle"):
        RunPlan((step("a", ("b",)), step("b", ("a",)))).ordered_steps()


def test_plan_rejects_unknown_dependency():
    with pytest.raises(ValueError, match="unknown dependencies"):
        RunPlan((step("a", ("missing",)),))


def test_orchestrator_runs_dependency_order_and_verifies(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    plan = RunPlan(
        (
            step("second", ("first",), "print('second')"),
            step("first", (), "print('first')"),
        )
    )
    run_id, receipts = orchestrator.run(plan, run_id="run-order")
    assert list(receipts) == ["first", "second"]
    verification = verify_run(plan, run_id, state_root=tmp_path / "state")
    assert verification.status == "PASS"
    assert verification.successful_steps == 2


def test_orchestrator_resume_does_not_reexecute_completed_step(tmp_path, monkeypatch):
    executor = make_executor(tmp_path)
    orchestrator = TaskOrchestrator(executor, tmp_path / "state")
    plan = RunPlan((step("first"),))
    run_id, first = orchestrator.run(plan, run_id="resume")
    calls = []
    original = executor.execute

    def spy(*args, **kwargs):
        calls.append(args[1])
        return original(*args, **kwargs)

    monkeypatch.setattr(executor, "execute", spy)
    _, second = orchestrator.run(plan, run_id=run_id)
    assert first["first"].receipt_sha256 == second["first"].receipt_sha256
    assert calls == []


def test_orchestrator_blocks_changed_plan_on_resume(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    first_plan = RunPlan((step("first", command="print('a')"),))
    _, _ = orchestrator.run(first_plan, run_id="changed")
    changed_plan = RunPlan((step("first", command="print('b')"),))
    with pytest.raises(PlanChanged):
        orchestrator.run(changed_plan, run_id="changed")


def test_orchestrator_stops_on_policy_denial(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    plan = RunPlan((step("blocked", granted=False),))
    with pytest.raises(ExecutionError, match="permission_granted"):
        orchestrator.run(plan, run_id="blocked")


def test_verifier_rejects_receipt_tamper(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    plan = RunPlan((step("one"),))
    run_id, _ = orchestrator.run(plan, run_id="tamper")
    state = json.loads(
        (tmp_path / "state" / "plans" / f"{run_id}.json").read_text(encoding="utf-8")
    )
    receipt_path = state["steps"]["one"]["receipt"]
    receipt = json.loads(open(receipt_path, encoding="utf-8").read())
    receipt["stdout"] = "tampered"
    open(receipt_path, "w", encoding="utf-8").write(json.dumps(receipt))
    verification = verify_run(plan, run_id, state_root=tmp_path / "state")
    assert verification.status == "FAIL"
    assert any("stdout hash mismatch" in e for e in verification.errors)
