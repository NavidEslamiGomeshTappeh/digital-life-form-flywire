from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .capabilities import (
    CapabilityDoctor,
    CapabilitySelectionError,
    resolve_backend_executable,
)


class ExecutionError(RuntimeError):
    pass


class RecoveryBlocked(ExecutionError):
    pass


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_step_name(step_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", step_id).strip("._")
    if not safe:
        raise ValueError("step_id does not produce a safe receipt filename")
    return safe


def _request_fingerprint(request: ExecutionRequest, cwd: str) -> str:
    payload = {
        "capability": request.capability,
        "backend": request.backend,
        "argv": list(request.argv),
        "cwd": cwd,
        "timeout_seconds": request.timeout_seconds,
        "idempotent": request.idempotent,
        "env": dict(sorted(request.env.items())),
        "remove_env": list(request.remove_env),
    }
    return _sha256_bytes(_canonical_bytes(payload))


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(_canonical_bytes(value) + b"\n")
    temp.replace(path)


@dataclass(frozen=True)
class ExecutionRequest:
    capability: str
    backend: str
    argv: tuple[str, ...]
    step_id: str
    cwd: str | None = None
    timeout_seconds: float = 120.0
    idempotent: bool = False
    env: dict[str, str] = field(default_factory=dict)
    remove_env: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.capability.strip() or not self.backend.strip():
            raise ValueError("capability and backend must not be empty")
        if not self.argv or any(not item for item in self.argv):
            raise ValueError("argv must contain a non-empty executable command")
        if not self.step_id.strip():
            raise ValueError("step_id must not be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True)
class ExecutionReceipt:
    schema_version: int
    run_id: str
    step_id: str
    capability: str
    backend: str
    argv: tuple[str, ...]
    cwd: str
    started_at: str
    finished_at: str
    status: str
    returncode: int | None
    stdout_sha256: str
    stderr_sha256: str
    stdout: str
    stderr: str
    duration_ms: int
    recovered: bool
    request_sha256: str
    capability_probe: dict[str, Any]
    receipt_sha256: str

    def unsigned_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("receipt_sha256")
        return data

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionEngine:
    """Crash-aware local execution with atomic checkpoints and sealed receipts."""

    def __init__(self, state_root: str | Path = ".dlf/runtime") -> None:
        self.state_root = Path(state_root)
        self.checkpoint_root = self.state_root / "checkpoints"
        self.receipt_root = self.state_root / "receipts"

    def _checkpoint_path(self, run_id: str) -> Path:
        return self.checkpoint_root / f"{run_id}.json"

    def _receipt_path(self, run_id: str, step_id: str) -> Path:
        return self.receipt_root / run_id / f"{_safe_step_name(step_id)}.json"

    def _load_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        path = self._checkpoint_path(run_id)
        if not path.is_file():
            return None
        try:
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RecoveryBlocked("checkpoint is unreadable or malformed") from exc
        if (
            checkpoint.get("schema_version") != 1
            or checkpoint.get("run_id") != run_id
            or not isinstance(checkpoint.get("steps"), dict)
        ):
            raise RecoveryBlocked("checkpoint structure is invalid")
        return checkpoint

    def _write_checkpoint(
        self,
        run_id: str,
        steps: dict[str, dict[str, Any]],
    ) -> None:
        _atomic_write_json(
            self._checkpoint_path(run_id),
            {
                "schema_version": 1,
                "run_id": run_id,
                "updated_at": _now(),
                "steps": steps,
            },
        )

    @staticmethod
    def _new_receipt(
        request: ExecutionRequest,
        run_id: str,
        cwd: str,
        started_at: str,
        finished_at: str,
        status: str,
        returncode: int | None,
        stdout: str,
        stderr: str,
        duration_ms: int,
        recovered: bool,
        capability_probe: dict[str, Any] | None = None,
    ) -> ExecutionReceipt:
        unsigned = {
            "schema_version": 1,
            "run_id": run_id,
            "step_id": request.step_id,
            "capability": request.capability,
            "backend": request.backend,
            "argv": request.argv,
            "cwd": cwd,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "returncode": returncode,
            "stdout_sha256": _sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": _sha256_bytes(stderr.encode("utf-8")),
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": duration_ms,
            "recovered": recovered,
            "request_sha256": _request_fingerprint(request, cwd),
            "capability_probe": capability_probe or {},
        }
        return ExecutionReceipt(
            **unsigned,
            receipt_sha256=_sha256_bytes(_canonical_bytes(unsigned)),
        )

    def execute(
        self,
        request: ExecutionRequest,
        *,
        run_id: str | None = None,
        resume: bool = True,
        capability_probe: dict[str, Any] | None = None,
    ) -> ExecutionReceipt:
        run_id = run_id or str(uuid.uuid4())
        cwd = str(Path(request.cwd or os.getcwd()).resolve())
        request_sha256 = _request_fingerprint(request, cwd)
        checkpoint = self._load_checkpoint(run_id)
        steps = dict(checkpoint["steps"]) if checkpoint else {}

        previous = steps.get(request.step_id)
        if previous:
            if previous.get("request_sha256") != request_sha256:
                raise RecoveryBlocked(
                    f"step {request.step_id!r} request fingerprint changed"
                )
            if previous.get("status") == "succeeded":
                receipt_path = self._receipt_path(run_id, request.step_id)
                if not receipt_path.is_file():
                    raise ExecutionError("checkpoint says succeeded but receipt is missing")
                receipt = verify_receipt_file(receipt_path)
                if receipt.request_sha256 != request_sha256:
                    raise RecoveryBlocked("stored receipt request fingerprint changed")
                return receipt

        recovered = bool(previous and previous.get("status") == "running")
        if recovered and (not resume or not request.idempotent):
            raise RecoveryBlocked(
                f"step {request.step_id!r} was interrupted and is not safe to replay"
            )

        started_at = _now()
        child_env = os.environ.copy()
        for key in request.remove_env:
            child_env.pop(key, None)
        child_env.update(request.env)

        steps[request.step_id] = {
            "status": "running",
            "capability": request.capability,
            "backend": request.backend,
            "argv": list(request.argv),
            "request_sha256": request_sha256,
            "started_at": started_at,
        }
        self._write_checkpoint(run_id, steps)

        start = time.monotonic()
        try:
            completed = subprocess.run(
                list(request.argv),
                cwd=cwd,
                env=child_env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=request.timeout_seconds,
                shell=False,
                check=False,
            )
            stdout = completed.stdout
            stderr = completed.stderr
            returncode = completed.returncode
            status = "succeeded" if returncode == 0 else "failed"
        except subprocess.TimeoutExpired as exc:
            stdout = str(exc.stdout or "")
            stderr = str(exc.stderr or "")
            returncode = None
            status = "timeout"
        except OSError as exc:
            stdout = ""
            stderr = str(exc)
            returncode = None
            status = "error"
        finished_at = _now()
        duration_ms = max(0, int((time.monotonic() - start) * 1000))

        receipt = self._new_receipt(
            request,
            run_id,
            cwd,
            started_at,
            finished_at,
            status,
            returncode,
            stdout,
            stderr,
            duration_ms,
            recovered,
            capability_probe,
        )
        receipt_path = self._receipt_path(run_id, request.step_id)
        _atomic_write_json(receipt_path, receipt.to_dict())

        steps[request.step_id] = {
            "status": status,
            "capability": request.capability,
            "backend": request.backend,
            "argv": list(request.argv),
            "request_sha256": request_sha256,
            "started_at": started_at,
            "finished_at": finished_at,
            "receipt": str(receipt_path),
            "receipt_sha256": receipt.receipt_sha256,
            "recovered": recovered,
        }
        self._write_checkpoint(run_id, steps)
        return receipt


class CapabilityExecutor:
    """Route declared capabilities through the doctor before local execution."""

    def __init__(
        self,
        doctor: CapabilityDoctor,
        engine: ExecutionEngine | None = None,
    ) -> None:
        self.doctor = doctor
        self.engine = engine or ExecutionEngine()

    def execute(
        self,
        capability: str,
        step_id: str,
        operation_args: tuple[str, ...] = (),
        *,
        backend_override: str | None = None,
        cwd: str | None = None,
        timeout_seconds: float = 120.0,
        idempotent: bool = False,
        env: dict[str, str] | None = None,
        remove_env: tuple[str, ...] = (),
        run_id: str | None = None,
    ) -> ExecutionReceipt:
        try:
            selection = self.doctor.select(capability, backend_override)
        except CapabilitySelectionError as exc:
            raise ExecutionError(str(exc)) from exc

        resolved = resolve_backend_executable(selection.backend)
        if resolved is None:
            raise ExecutionError("selected backend disappeared before execution")

        request = ExecutionRequest(
            capability=capability,
            backend=selection.backend.name,
            argv=(resolved, *operation_args),
            step_id=step_id,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            idempotent=idempotent,
            env=env or {},
            remove_env=remove_env,
        )
        snapshot = selection.to_dict()
        snapshot["resolved_executable"] = resolved
        return self.engine.execute(
            request,
            run_id=run_id,
            capability_probe=snapshot,
        )


def verify_receipt(receipt: dict[str, Any]) -> ExecutionReceipt:
    required = {
        "schema_version",
        "run_id",
        "step_id",
        "capability",
        "backend",
        "argv",
        "cwd",
        "started_at",
        "finished_at",
        "status",
        "returncode",
        "stdout_sha256",
        "stderr_sha256",
        "stdout",
        "stderr",
        "duration_ms",
        "recovered",
        "request_sha256",
        "capability_probe",
        "receipt_sha256",
    }
    missing = sorted(required - set(receipt))
    if missing:
        raise ExecutionError(f"receipt missing fields: {', '.join(missing)}")
    expected_stdout = _sha256_bytes(str(receipt["stdout"]).encode("utf-8"))
    expected_stderr = _sha256_bytes(str(receipt["stderr"]).encode("utf-8"))
    if receipt["stdout_sha256"] != expected_stdout:
        raise ExecutionError("receipt stdout hash mismatch")
    if receipt["stderr_sha256"] != expected_stderr:
        raise ExecutionError("receipt stderr hash mismatch")
    unsigned = dict(receipt)
    observed_hash = unsigned.pop("receipt_sha256")
    expected_hash = _sha256_bytes(_canonical_bytes(unsigned))
    if observed_hash != expected_hash:
        raise ExecutionError("receipt seal mismatch")
    return ExecutionReceipt(
        schema_version=int(receipt["schema_version"]),
        run_id=str(receipt["run_id"]),
        step_id=str(receipt["step_id"]),
        capability=str(receipt["capability"]),
        backend=str(receipt["backend"]),
        argv=tuple(str(x) for x in receipt["argv"]),
        cwd=str(receipt["cwd"]),
        started_at=str(receipt["started_at"]),
        finished_at=str(receipt["finished_at"]),
        status=str(receipt["status"]),
        returncode=receipt["returncode"],
        stdout_sha256=str(receipt["stdout_sha256"]),
        stderr_sha256=str(receipt["stderr_sha256"]),
        stdout=str(receipt["stdout"]),
        stderr=str(receipt["stderr"]),
        duration_ms=int(receipt["duration_ms"]),
        recovered=bool(receipt["recovered"]),
        request_sha256=str(receipt["request_sha256"]),
        capability_probe=dict(receipt["capability_probe"]),
        receipt_sha256=str(receipt["receipt_sha256"]),
    )


def verify_receipt_file(path: str | Path) -> ExecutionReceipt:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    receipt = verify_receipt(data)
    if receipt.status != "succeeded" or receipt.returncode != 0:
        raise ExecutionError(
            f"receipt is not a successful execution: status={receipt.status!r}, "
            f"returncode={receipt.returncode!r}"
        )
    return receipt
