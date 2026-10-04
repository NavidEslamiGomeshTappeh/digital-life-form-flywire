from __future__ import annotations

import json
import sys
from pathlib import Path

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


def test_receipt_state_reference_is_relative_and_portable(tmp_path, monkeypatch):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    plan = RunPlan((step("portable"),))
    run_id, _ = orchestrator.run(plan, run_id="portable")
    state_path = tmp_path / "state" / "plans" / f"{run_id}.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    receipt_reference = state["steps"]["portable"]["receipt"]
    assert not Path(receipt_reference).is_absolute()
    assert Path(receipt_reference).parts[:2] == ("receipts", run_id)
    monkeypatch.chdir(tmp_path)
    verification = verify_run(plan, run_id, state_root=tmp_path / "state")
    assert verification.status == "PASS"


def test_verifier_rejects_receipt_intent_mismatch(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    plan = RunPlan((step("one", command="print('intent')"),))
    run_id, _ = orchestrator.run(plan, run_id="intent-check")
    state_path = tmp_path / "state" / "plans" / f"{run_id}.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    receipt_path = tmp_path / "state" / state["steps"]["one"]["receipt"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["intent"]["destination"] = "other-process"
    payload = dict(receipt)
    payload.pop("receipt_sha256")
    import hashlib

    receipt["receipt_sha256"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    verification = verify_run(plan, run_id, state_root=tmp_path / "state")
    assert verification.status == "FAIL"
    assert any("intent mismatch" in e for e in verification.errors)


def test_verifier_rejects_receipt_path_escape(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    plan = RunPlan((step("one"),))
    run_id, _ = orchestrator.run(plan, run_id="receipt-path")
    state_path = tmp_path / "state" / "plans" / f"{run_id}.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["steps"]["one"]["receipt"] = "../outside.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    verification = verify_run(plan, run_id, state_root=tmp_path / "state")
    assert verification.status == "FAIL"
    assert any("escapes the run receipt directory" in e for e in verification.errors)


def test_verifier_rejects_receipt_tamper(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    plan = RunPlan((step("one"),))
    run_id, _ = orchestrator.run(plan, run_id="tamper")
    state = json.loads(
        (tmp_path / "state" / "plans" / f"{run_id}.json").read_text(encoding="utf-8")
    )
    receipt_path = state["steps"]["one"]["receipt"]
    receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    receipt["stdout"] = "tampered"
    Path(receipt_path).write_text(json.dumps(receipt), encoding="utf-8")
    verification = verify_run(plan, run_id, state_root=tmp_path / "state")
    assert verification.status == "FAIL"
    assert any("stdout hash mismatch" in e for e in verification.errors)


def test_orchestrator_denies_network_by_default(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    plan = RunPlan(
        (
            TaskStep(
                step_id="network",
                capability="runtime.python.test",
                action="network test",
                destination="remote",
                risk_tier=0,
                permission_granted=True,
                network_access=True,
                operation_args=("-c", "print('must-not-run')"),
                idempotent=True,
            ),
        )
    )
    with pytest.raises(ExecutionError, match="network_allowed"):
        orchestrator.run(plan, run_id="network-denied")


def test_run_plan_cli_executes_and_verifies(tmp_path):
    from dlf_flywire.cli import main

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "step_id": "cli",
                        "capability": "runtime.python",
                        "action": "run CLI regression",
                        "destination": "test-process",
                        "risk_tier": 0,
                        "permission_granted": True,
                        "operation_args": ["-c", "print('cli-ok')"],
                        "idempotent": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert main(
        [
            "run-plan",
            str(plan_path),
            "--run-id",
            "cli-run",
            "--state-root",
            str(tmp_path / "state"),
        ]
    ) == 0


def test_run_plan_cli_rejects_string_permission(tmp_path):
    from dlf_flywire.cli import main

    plan_path = tmp_path / "unsafe.json"
    plan_path.write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "step_id": "unsafe",
                        "capability": "runtime.python",
                        "action": "unsafe parsing regression",
                        "destination": "test-process",
                        "permission_granted": "false",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert main(
        [
            "run-plan",
            str(plan_path),
            "--state-root",
            str(tmp_path / "state"),
        ]
    ) == 2


def test_orchestrator_rejects_path_traversal_run_id(tmp_path):
    orchestrator = TaskOrchestrator(make_executor(tmp_path), tmp_path / "state")
    with pytest.raises(ValueError, match="run_id"):
        orchestrator.run(RunPlan((step("safe"),)), run_id="../escape")
