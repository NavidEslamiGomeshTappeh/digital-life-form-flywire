from __future__ import annotations

import base64
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

from .capabilities import BackendSpec, CapabilityDoctor, CapabilitySpec
from .execution import CapabilityExecutor, ExecutionEngine, ExecutionError, ExecutionReceipt
from .orchestrator import RunPlan, TaskOrchestrator, TaskStep
from .verifier import RunVerification, verify_run


class CodeHandError(ValueError):
    """Raised when Code Hand input violates its workspace contract."""


@dataclass(frozen=True)
class CodeHandResult:
    run_id: str
    file_path: str
    content_sha256: str
    receipts: dict[str, ExecutionReceipt]
    verification: RunVerification

    @property
    def status(self) -> str:
        return self.verification.status

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "file_path": self.file_path,
            "content_sha256": self.content_sha256,
            "receipts": {key: value.to_dict() for key, value in self.receipts.items()},
            "verification": self.verification.to_dict(),
        }


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _safe_relative_file(workspace_root: Path, relative_path: str) -> Path:
    candidate = Path(relative_path.replace("\\", "/"))
    if candidate.is_absolute():
        raise CodeHandError("Code Hand paths must be relative to the workspace")
    if not relative_path.strip():
        raise CodeHandError("Code Hand file path must not be empty")
    try:
        resolved = (workspace_root / candidate).resolve()
    except OSError as exc:
        raise CodeHandError("Code Hand file path could not be resolved") from exc
    if not resolved.is_relative_to(workspace_root):
        raise CodeHandError("Code Hand file path escapes the workspace")
    return resolved


def code_capabilities() -> tuple[CapabilitySpec, ...]:
    """Real local Code Hand capabilities using the current Python interpreter."""
    backend = BackendSpec("current-python", sys.executable)
    return (
        CapabilitySpec(
            "code.write",
            "Create one UTF-8 source file inside the declared workspace",
            (backend,),
        ),
        CapabilitySpec(
            "code.test.python",
            "Execute a generated Python source file with explicit assertions",
            (backend,),
        ),
    )


def _write_script(relative_path: str, content: str) -> str:
    return (
        "from pathlib import Path; import base64; "
        f"p=Path(base64.b64decode({_b64(relative_path)!r}).decode('utf-8')); "
        f"data=base64.b64decode({_b64(content)!r}); "
        "p.parent.mkdir(parents=True, exist_ok=True); "
        "assert not p.exists(), 'target file already exists'; "
        "p.write_bytes(data); "
        "print('CODE_HAND_FILE_CREATED', p.as_posix()); "
        "print('CONTENT_SHA256', __import__('hashlib').sha256(data).hexdigest())"
    )


def _test_script(relative_path: str, test_code: str) -> str:
    return (
        "from pathlib import Path; import base64; "
        f"p=Path(base64.b64decode({_b64(relative_path)!r}).decode('utf-8')).resolve(); "
        "source=p.read_text(encoding='utf-8'); "
        "namespace={'__name__':'__code_hand_target__','__file__':str(p)}; "
        "exec(compile(source, str(p), 'exec'), namespace); "
        f"tests=base64.b64decode({_b64(test_code)!r}).decode('utf-8'); "
        "exec(compile(tests, '<code-hand-test>', 'exec'), namespace); "
        "print('CODE_HAND_TEST_PASS')"
    )


class CodeHand:
    """Create and test source files through the guarded project execution path."""

    def __init__(
        self,
        workspace_root: str | Path,
        state_root: str | Path | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        if not self.workspace_root.is_dir():
            raise CodeHandError(f"workspace does not exist: {self.workspace_root}")
        self.state_root = Path(state_root).resolve() if state_root is not None else (
            self.workspace_root / ".dlf" / "runtime"
        )
        engine = ExecutionEngine(self.state_root)
        self.executor = CapabilityExecutor(
            CapabilityDoctor(code_capabilities()),
            engine,
        )
        self.orchestrator = TaskOrchestrator(self.executor, self.state_root)

    def build_plan(
        self,
        relative_path: str,
        content: str,
        test_code: str,
        *,
        permission_granted: bool,
    ) -> RunPlan:
        target = _safe_relative_file(self.workspace_root, relative_path)
        if target.exists():
            raise CodeHandError(f"Code Hand target already exists: {relative_path!r}")
        if not isinstance(content, str) or not content:
            raise CodeHandError("Code Hand source content must be a non-empty string")
        if not isinstance(test_code, str) or not test_code.strip():
            raise CodeHandError("Code Hand test code must be a non-empty string")

        return RunPlan(
            (
                TaskStep(
                    step_id="create-file",
                    capability="code.write",
                    action="Code Hand create source file",
                    destination="code-workspace",
                    risk_tier=0,
                    permission_granted=permission_granted,
                    operation_args=("-c", _write_script(relative_path, content)),
                    idempotent=False,
                ),
                TaskStep(
                    step_id="test-file",
                    capability="code.test.python",
                    action="Code Hand execute and test generated Python file",
                    destination="code-workspace",
                    risk_tier=0,
                    permission_granted=permission_granted,
                    operation_args=("-c", _test_script(relative_path, test_code)),
                    dependencies=("create-file",),
                    idempotent=True,
                ),
            )
        )

    def execute(
        self,
        relative_path: str,
        content: str,
        test_code: str,
        *,
        run_id: str | None = None,
        permission_granted: bool = False,
    ) -> CodeHandResult:
        plan = self.build_plan(
            relative_path,
            content,
            test_code,
            permission_granted=permission_granted,
        )
        run_id, receipts = self.orchestrator.run(plan, run_id=run_id)
        verification = verify_run(plan, run_id, state_root=self.state_root)
        if verification.status != "PASS":
            raise ExecutionError(
                "Code Hand run did not pass independent verification: "
                + "; ".join(verification.errors)
            )
        target = _safe_relative_file(self.workspace_root, relative_path)
        observed = target.read_bytes()
        expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if hashlib.sha256(observed).hexdigest() != expected_hash:
            raise CodeHandError("generated file content hash does not match requested content")
        return CodeHandResult(
            run_id=run_id,
            file_path=str(target),
            content_sha256=expected_hash,
            receipts=receipts,
            verification=verification,
        )
