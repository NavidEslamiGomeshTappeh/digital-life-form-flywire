from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .execution import (
    CapabilityExecutor,
    ExecutionError,
    ExecutionReceipt,
    _atomic_write_json,
    _canonical_bytes,
    verify_receipt_file,
)
from .policy import ExecutionIntent



def _safe_run_id(run_id: str) -> str:
    if not run_id or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", run_id):
        raise ValueError(
            "run_id must contain only letters, digits, dot, underscore, or hyphen"
        )
    return run_id


class OrchestrationError(RuntimeError):
    pass


class PlanChanged(OrchestrationError):
    pass


@dataclass(frozen=True)
class TaskStep:
    step_id: str
    capability: str
    action: str
    destination: str
    risk_tier: int
    permission_granted: bool
    operation_args: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    backend_override: str | None = None
    idempotent: bool = False
    network_access: bool = False
    system_mutation: bool = False

    def __post_init__(self) -> None:
        if not self.step_id.strip():
            raise ValueError("step_id must not be empty")
        if self.risk_tier not in {0, 1, 2}:
            raise ValueError("risk_tier must be 0, 1, or 2")


@dataclass(frozen=True)
class RunPlan:
    steps: tuple[TaskStep, ...]

    def __post_init__(self) -> None:
        ids = [step.step_id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate step_id in run plan")
        known = set(ids)
        for step in self.steps:
            missing = sorted(set(step.dependencies) - known)
            if missing:
                raise ValueError(
                    f"step {step.step_id!r} has unknown dependencies: {', '.join(missing)}"
                )

    def fingerprint(self) -> str:
        payload = [
            {
                "step_id": step.step_id,
                "capability": step.capability,
                "action": step.action,
                "destination": step.destination,
                "risk_tier": step.risk_tier,
                "permission_granted": step.permission_granted,
                "operation_args": list(step.operation_args),
                "dependencies": list(step.dependencies),
                "backend_override": step.backend_override,
                "idempotent": step.idempotent,
                "network_access": step.network_access,
                "system_mutation": step.system_mutation,
            }
            for step in self.steps
        ]
        return hashlib.sha256(_canonical_bytes(payload)).hexdigest()

    def ordered_steps(self) -> tuple[TaskStep, ...]:
        remaining = {step.step_id: step for step in self.steps}
        ordered: list[TaskStep] = []
        satisfied: set[str] = set()
        while remaining:
            ready = [
                step
                for step in remaining.values()
                if set(step.dependencies) <= satisfied
            ]
            if not ready:
                raise OrchestrationError("dependency cycle detected in run plan")
            for step in sorted(ready, key=lambda item: item.step_id):
                ordered.append(step)
                satisfied.add(step.step_id)
                remaining.pop(step.step_id)
        return tuple(ordered)


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


class TaskOrchestrator:
    """Leader boundary: validate a plan, execute dependency-ordered steps, and resume."""

    def __init__(self, executor: CapabilityExecutor, state_root: str | Path = ".dlf/runtime") -> None:
        self.executor = executor
        self.state_root = Path(state_root)
        self.run_root = self.state_root / "plans"

    def _state_path(self, run_id: str) -> Path:
        return self.run_root / f"{run_id}.json"

    def _load_state(self, run_id: str) -> dict[str, Any] | None:
        path = self._state_path(run_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OrchestrationError("run state is unreadable or malformed") from exc
        if data.get("schema_version") != 1 or data.get("run_id") != run_id:
            raise OrchestrationError("run state structure is invalid")
        return data

    def _write_state(
        self,
        run_id: str,
        plan_sha256: str,
        steps: dict[str, dict[str, Any]],
        status: str,
    ) -> None:
        _atomic_write_json(
            self._state_path(run_id),
            {
                "schema_version": 1,
                "run_id": run_id,
                "plan_sha256": plan_sha256,
                "status": status,
                "steps": steps,
            },
        )

    def run(self, plan: RunPlan, *, run_id: str | None = None) -> tuple[str, dict[str, ExecutionReceipt]]:
        plan_sha256 = plan.fingerprint()
        run_id = _safe_run_id(run_id or uuid.uuid4().hex)
        prior = self._load_state(run_id)
        steps_state: dict[str, dict[str, Any]] = {}
        if prior:
            if prior.get("plan_sha256") != plan_sha256:
                raise PlanChanged("run plan fingerprint changed")
            steps_state = dict(prior.get("steps", {}))

        receipts: dict[str, ExecutionReceipt] = {}
        for step in plan.ordered_steps():
            previous = steps_state.get(step.step_id)
            if previous and previous.get("status") == "succeeded":
                receipt_path = previous.get("receipt")
                if not isinstance(receipt_path, str):
                    raise OrchestrationError(
                        f"successful step {step.step_id!r} has no receipt path"
                    )
                receipt = verify_receipt_file(receipt_path)
                receipts[step.step_id] = receipt
                continue

            unresolved = [
                dep
                for dep in step.dependencies
                if steps_state.get(dep, {}).get("status") != "succeeded"
            ]
            if unresolved:
                raise OrchestrationError(
                    f"step {step.step_id!r} has unresolved dependencies: {', '.join(unresolved)}"
                )

            self._write_state(run_id, plan_sha256, steps_state, "running")
            intent = ExecutionIntent(
                capability=step.capability,
                action=step.action,
                destination=step.destination,
                risk_tier=step.risk_tier,
                permission_granted=step.permission_granted,
                network_access=step.network_access,
                system_mutation=step.system_mutation,
            )
            try:
                receipt = self.executor.execute(
                    step.capability,
                    step.step_id,
                    step.operation_args,
                    intent=intent,
                    backend_override=step.backend_override,
                    idempotent=step.idempotent,
                    run_id=run_id,
                )
            except ExecutionError:
                self._write_state(run_id, plan_sha256, steps_state, "failed")
                raise

            receipts[step.step_id] = receipt
            steps_state[step.step_id] = {
                "status": receipt.status,
                "receipt": str(
                    self.executor.engine._receipt_path(run_id, step.step_id)
                ),
                "receipt_sha256": receipt.receipt_sha256,
            }
            self._write_state(run_id, plan_sha256, steps_state, "running")

        self._write_state(run_id, plan_sha256, steps_state, "succeeded")
        return run_id, receipts


def verify_run(
    plan: RunPlan,
    run_id: str,
    *,
    state_root: str | Path = ".dlf/runtime",
) -> RunVerification:
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
    if state.get("plan_sha256") != plan.fingerprint():
        errors.append("plan fingerprint mismatch")

    step_state = state.get("steps", {})
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
            receipt = verify_receipt_file(receipt_path)
            if receipt.step_id != step.step_id:
                raise ExecutionError("receipt step ID mismatch")
            if receipt.run_id != run_id:
                raise ExecutionError("receipt run ID mismatch")
            if receipt.capability != step.capability:
                raise ExecutionError("receipt capability mismatch")
            if receipt.policy_decision.get("status") != "allow":
                raise ExecutionError("receipt policy decision is not allow")
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
