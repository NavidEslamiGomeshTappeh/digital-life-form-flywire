from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .execution import ExecutionError, verify_receipt_file


class VerificationError(RuntimeError):
    pass


def _safe_run_id(run_id: str) -> str:
    if not run_id or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", run_id):
        raise ValueError(
            "run_id must contain only letters, digits, dot, underscore, or hyphen"
        )
    return run_id


def _resolve_receipt_path(state_root: Path, run_id: str, reference: str) -> Path:
    if not isinstance(reference, str) or not reference:
        raise ExecutionError("receipt path is missing")
    root = state_root.resolve()
    allowed_root = (root / "receipts" / _safe_run_id(run_id)).resolve()
    candidate = Path(reference)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if not candidate.is_relative_to(allowed_root):
        raise ExecutionError("receipt path escapes the run receipt directory")
    return candidate


@dataclass(frozen=True)
class RunVerification:
    status: str
    run_id: str
    plan_sha256: str
    steps_checked: int
    successful_steps: int
    failed_steps: int
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "run_id": self.run_id,
            "plan_sha256": self.plan_sha256,
            "steps_checked": self.steps_checked,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "errors": list(self.errors),
        }





def verify_run(
    plan: Any,
    run_id: str,
    *,
    state_root: str | Path = ".dlf/runtime",
) -> RunVerification:
    run_id = _safe_run_id(run_id)
    root = Path(state_root)
    state_path = root / "plans" / f"{run_id}.json"
    if not state_path.is_file():
        return RunVerification(
            status="FAIL",
            run_id=run_id,
            plan_sha256=plan.fingerprint(),
            steps_checked=0,
            successful_steps=0,
            failed_steps=0,
            errors=("run state is missing",),
        )
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return RunVerification(
            status="FAIL",
            run_id=run_id,
            plan_sha256=plan.fingerprint(),
            steps_checked=0,
            successful_steps=0,
            failed_steps=0,
            errors=("run state is unreadable or malformed",),
        )

    errors: list[str] = []
    if state.get("schema_version") != 1:
        errors.append("unsupported run-state schema")
    if state.get("run_id") != run_id:
        errors.append("run id mismatch")
    if state.get("status") != "succeeded":
        errors.append("run state is not succeeded")
    if state.get("plan_sha256") != plan.fingerprint():
        errors.append("plan fingerprint mismatch")

    step_state = state.get("steps")
    if not isinstance(step_state, dict):
        errors.append("run state steps are missing or malformed")
        step_state = {}

    expected_ids = {step.step_id for step in plan.steps}
    unexpected_ids = sorted(set(step_state) - expected_ids)
    if unexpected_ids:
        errors.append(
            "unexpected state steps: " + ", ".join(unexpected_ids)
        )

    successful = 0
    failed = 0
    for step in plan.ordered_steps():
        record = step_state.get(step.step_id)
        if not isinstance(record, dict):
            errors.append(f"missing state for step {step.step_id}")
            failed += 1
            continue
        if record.get("status") != "succeeded":
            errors.append(f"step {step.step_id} is not succeeded")
            failed += 1
            continue
        receipt_path = record.get("receipt")
        try:
            receipt = verify_receipt_file(
                _resolve_receipt_path(root, run_id, receipt_path)
            )
            if receipt.step_id != step.step_id:
                raise ExecutionError("receipt step ID mismatch")
            if receipt.run_id != run_id:
                raise ExecutionError("receipt run ID mismatch")
            if receipt.capability != step.capability:
                raise ExecutionError("receipt capability mismatch")
            expected_intent = {
                "capability": step.capability,
                "action": step.action,
                "destination": step.destination,
                "risk_tier": step.risk_tier,
                "permission_granted": step.permission_granted,
                "network_access": step.network_access,
                "system_mutation": step.system_mutation,
            }
            if receipt.intent != expected_intent:
                raise ExecutionError("receipt intent mismatch")
            if receipt.policy_decision.get("status") != "allow":
                raise ExecutionError("receipt policy decision is not allow")
            checks = receipt.policy_decision.get("checks")
            if not isinstance(checks, dict) or not all(
                value is True for value in checks.values()
            ):
                raise ExecutionError("receipt policy checks are not all true")
            if record.get("receipt_sha256") != receipt.receipt_sha256:
                raise ExecutionError("run-state receipt hash mismatch")
            successful += 1
        except (ExecutionError, OSError, TypeError, ValueError) as exc:
            errors.append(f"step {step.step_id}: {exc}")
            failed += 1

    status = "PASS" if not errors and successful == len(plan.steps) else "FAIL"
    return RunVerification(
        status=status,
        run_id=run_id,
        plan_sha256=plan.fingerprint(),
        steps_checked=len(plan.steps),
        successful_steps=successful,
        failed_steps=failed,
        errors=tuple(errors),
    )
