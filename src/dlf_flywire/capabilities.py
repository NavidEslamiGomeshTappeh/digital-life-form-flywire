from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

ProbeStatus = Literal["ok", "missing", "broken", "timeout", "error"]
CapabilityStatus = Literal["ok", "off", "error"]


class CapabilitySelectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackendSpec:
    name: str
    executable: str
    args: tuple[str, ...] = ("--version",)
    timeout_seconds: float = 10.0
    env: Mapping[str, str] = ()
    remove_env: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.executable.strip():
            raise ValueError("backend name and executable must not be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("backend timeout must be positive")


@dataclass(frozen=True)
class ProbeResult:
    status: ProbeStatus
    output: str = ""
    duration_ms: int = 0

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "output": self.output,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    description: str
    backends: tuple[BackendSpec, ...]
    tier: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.description.strip():
            raise ValueError("capability name and description must not be empty")
        if self.tier not in {0, 1, 2}:
            raise ValueError("capability tier must be 0, 1, or 2")
        if not self.backends:
            raise ValueError("capability must define at least one backend")
        names = [item.name for item in self.backends]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate backend in capability {self.name}")


@dataclass(frozen=True)
class BackendSelection:
    capability: CapabilitySpec
    backend: BackendSpec
    probe: ProbeResult
    candidates: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "capability": self.capability.name,
            "backend": self.backend.name,
            "probe": self.probe.to_dict(),
            "candidates": list(self.candidates),
        }


def _elapsed_ms(start: float) -> int:
    return max(0, int((time.monotonic() - start) * 1000))


def _resolve_executable(executable: str) -> str | None:
    candidate = Path(executable).expanduser()
    if candidate.is_absolute() or os.sep in executable or (
        os.altsep and os.altsep in executable
    ):
        return str(candidate) if candidate.is_file() else None
    return shutil.which(executable)


def resolve_backend_executable(backend: BackendSpec) -> str | None:
    """Resolve a declared backend without invoking it."""
    return _resolve_executable(backend.executable)


def probe_backend(backend: BackendSpec) -> ProbeResult:
    """Run only the backend's declared health command; never use a shell."""
    start = time.monotonic()
    path = _resolve_executable(backend.executable)
    if path is None:
        return ProbeResult("missing", duration_ms=_elapsed_ms(start))

    child_env = os.environ.copy()
    for key in backend.remove_env:
        child_env.pop(key, None)
    child_env.update(dict(backend.env))

    try:
        result = subprocess.run(
            [path, *backend.args],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=backend.timeout_seconds,
            env=child_env,
            shell=False,
            check=False,
        )
    except FileNotFoundError:
        return ProbeResult("broken", duration_ms=_elapsed_ms(start))
    except OSError:
        return ProbeResult("broken", duration_ms=_elapsed_ms(start))
    except subprocess.TimeoutExpired as exc:
        output = str(exc.stdout or exc.stderr or "").strip()[:1000]
        return ProbeResult("timeout", output=output, duration_ms=_elapsed_ms(start))
    except Exception as exc:  # defensive boundary  # noqa: BLE001
        return ProbeResult("error", output=str(exc)[:1000], duration_ms=_elapsed_ms(start))

    output = ((result.stdout or "") + (result.stderr or "")).strip()[:1000]
    if result.returncode == 0:
        return ProbeResult("ok", output=output, duration_ms=_elapsed_ms(start))
    if result.returncode in (126, 127):
        return ProbeResult("broken", output=output, duration_ms=_elapsed_ms(start))
    return ProbeResult("error", output=output, duration_ms=_elapsed_ms(start))


class CapabilityDoctor:
    """Independently probe capabilities and select the first healthy backend."""

    def __init__(self, capabilities: Sequence[CapabilitySpec]) -> None:
        self._capabilities = tuple(capabilities)
        names = [item.name for item in self._capabilities]
        if len(names) != len(set(names)):
            raise ValueError("duplicate capability name")

    @property
    def capabilities(self) -> tuple[CapabilitySpec, ...]:
        return self._capabilities

    @staticmethod
    def ordered_backends(
        spec: CapabilitySpec, override: str | None = None
    ) -> tuple[BackendSpec, ...]:
        backends = list(spec.backends)
        if override:
            for index, backend in enumerate(backends):
                if backend.name == override:
                    backends.insert(0, backends.pop(index))
                    break
        return tuple(backends)

    def _find(self, capability_name: str) -> CapabilitySpec:
        for spec in self._capabilities:
            if spec.name == capability_name:
                return spec
        raise CapabilitySelectionError(f"unknown capability: {capability_name}")

    def _probe_selection(
        self, spec: CapabilitySpec, override: str | None = None
    ) -> tuple[BackendSelection | None, tuple[dict[str, object], ...], tuple[ProbeStatus, ...]]:
        candidates: list[dict[str, object]] = []
        statuses: list[ProbeStatus] = []
        for backend in self.ordered_backends(spec, override):
            try:
                result = probe_backend(backend)
            except Exception as exc:  # isolated probe boundary  # noqa: BLE001
                result = ProbeResult("error", output=str(exc)[:1000])
            statuses.append(result.status)
            candidates.append({"backend": backend.name, "probe": result.to_dict()})
            if result.ok:
                return (
                    BackendSelection(
                        capability=spec,
                        backend=backend,
                        probe=result,
                        candidates=tuple(candidates),
                    ),
                    tuple(candidates),
                    tuple(statuses),
                )
        return None, tuple(candidates), tuple(statuses)

    def select(
        self, capability_name: str, override: str | None = None
    ) -> BackendSelection:
        """Probe and return one healthy declared backend, or fail closed."""
        selection, _, _ = self._probe_selection(self._find(capability_name), override)
        if selection is None:
            raise CapabilitySelectionError(
                f"no healthy backend for capability {capability_name}"
            )
        return selection

    def check(self, overrides: Mapping[str, str] | None = None) -> dict[str, object]:
        """Return a point-in-time, machine-readable capability snapshot."""

        overrides = overrides or {}
        observed_at = datetime.now(UTC).isoformat()
        results: list[dict[str, object]] = []

        for spec in self._capabilities:
            try:
                selection, candidates, statuses = self._probe_selection(
                    spec, overrides.get(spec.name)
                )
                if selection is not None:
                    results.append(
                        {
                            "name": spec.name,
                            "description": spec.description,
                            "tier": spec.tier,
                            "status": "ok",
                            "active_backend": selection.backend.name,
                            "backends": list(candidates),
                            "message": (
                                "selected healthy backend: "
                                f"{selection.backend.name}"
                            ),
                        }
                    )
                    continue

                if statuses and all(value == "missing" for value in statuses):
                    status: CapabilityStatus = "off"
                    message = "no candidate backend is installed"
                else:
                    status = "error"
                    message = "no healthy backend was found"

                results.append(
                    {
                        "name": spec.name,
                        "description": spec.description,
                        "tier": spec.tier,
                        "status": status,
                        "active_backend": None,
                        "backends": list(candidates),
                        "message": message,
                    }
                )
            except Exception as exc:  # defensive boundary  # noqa: BLE001
                results.append(
                    {
                        "name": spec.name,
                        "description": spec.description,
                        "tier": spec.tier,
                        "status": "error",
                        "active_backend": None,
                        "backends": [],
                        "message": f"capability probe exception: {exc}",
                    }
                )

        counts = {
            "ok": sum(item["status"] == "ok" for item in results),
            "off": sum(item["status"] == "off" for item in results),
            "error": sum(item["status"] == "error" for item in results),
        }
        return {
            "schema_version": 1,
            "observed_at": observed_at,
            "capabilities": results,
            "counts": counts,
        }

    @staticmethod
    def format_report(report: Mapping[str, object]) -> str:
        lines = [
            "Digital Life Form Capability Doctor",
            "=" * 36,
            f"observed_at: {report['observed_at']}",
        ]
        for item in report["capabilities"]:
            lines.append(
                f"{str(item['status']).upper():>5}  "
                f"{item['name']}  backend={item['active_backend'] or '-'}  "
                f"{item['message']}"
            )
        counts = report["counts"]
        lines.append(
            f"summary: {counts['ok']} ok / "
            f"{counts['off']} off / {counts['error']} error"
        )
        return "\n".join(lines)


def default_capabilities() -> tuple[CapabilitySpec, ...]:
    """Conservative local capabilities; no install, login, or network action."""
    return (
        CapabilitySpec(
            "runtime.python",
            "Python interpreter available for local execution",
            (
                BackendSpec("current-python", sys.executable),
                BackendSpec("python3", "python3"),
                BackendSpec("python", "python"),
            ),
        ),
        CapabilitySpec(
            "runtime.git",
            "Git command available for repository operations",
            (BackendSpec("git-cli", "git"),),
        ),
        CapabilitySpec(
            "package.import",
            "Digital Life Form package imports in the active runtime",
            (
                BackendSpec(
                    "current-python",
                    sys.executable,
                    ("-c", "import dlf_flywire; print(dlf_flywire.__version__)"),
                ),
            ),
        ),
        CapabilitySpec(
            "tool.build",
            "Python build frontend available for distribution checks",
            (BackendSpec("python-build", sys.executable, ("-m", "build", "--version")),),
            tier=1,
        ),
        CapabilitySpec(
            "code.write",
            "Create one UTF-8 source file inside the declared workspace",
            (BackendSpec("current-python", sys.executable),),
        ),
        CapabilitySpec(
            "code.edit",
            "Edit one existing UTF-8 source file with an exact SHA-256 precondition",
            (BackendSpec("current-python", sys.executable),),
        ),
        CapabilitySpec(
            "code.test.python",
            "Execute a generated Python source file with explicit assertions",
            (BackendSpec("current-python", sys.executable),),
        ),
    )
