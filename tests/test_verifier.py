from __future__ import annotations

import json

from dlf_flywire.orchestrator import RunPlan, TaskOrchestrator
from dlf_flywire.verifier import verify_run

from test_orchestrator import make_executor, step


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
