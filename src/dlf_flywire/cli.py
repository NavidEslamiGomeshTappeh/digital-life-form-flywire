from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .constants import ROOTS



def _load_run_plan(path: str):
    from .orchestrator import RunPlan, TaskStep

    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot read plan: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("steps"), list):
        raise ValueError("plan must be an object with a steps list")

    steps = []
    for index, item in enumerate(data["steps"]):
        if not isinstance(item, dict):
            raise ValueError(f"step {index} must be an object")
        required = ("step_id", "capability", "action", "destination")
        missing = [name for name in required if name not in item]
        if missing:
            raise ValueError(
                f"step {index} missing required fields: {', '.join(missing)}"
            )
        args = item.get("operation_args", [])
        deps = item.get("dependencies", [])
        if not isinstance(args, list) or not all(isinstance(x, str) for x in args):
            raise ValueError(f"step {index} operation_args must be a string list")
        if not isinstance(deps, list) or not all(isinstance(x, str) for x in deps):
            raise ValueError(f"step {index} dependencies must be a string list")
        steps.append(
            TaskStep(
                step_id=str(item["step_id"]),
                capability=str(item["capability"]),
                action=str(item["action"]),
                destination=str(item["destination"]),
                risk_tier=int(item.get("risk_tier", 0)),
                permission_granted=bool(item.get("permission_granted", False)),
                operation_args=tuple(args),
                dependencies=tuple(deps),
                backend_override=(
                    str(item["backend_override"])
                    if item.get("backend_override") is not None
                    else None
                ),
                idempotent=bool(item.get("idempotent", False)),
                network_access=bool(item.get("network_access", False)),
                system_mutation=bool(item.get("system_mutation", False)),
            )
        )
    return RunPlan(tuple(steps))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="dlf-flywire")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate the Version 1 evidence and provenance contract.")
    validate.add_argument(
        "--root",
        default=".",
        help="Project root containing data/ and evidence/ (default: current directory).",
    )

    audit = sub.add_parser("audit", help="Audit claim, artifact, cross-source, and version provenance.")
    audit.add_argument(
        "--root",
        default=".",
        help="Project root containing data/ and evidence/ (default: current directory).",
    )

    verify_sources = sub.add_parser("verify-sources", help="Validate frozen Codex/Zenodo cross-source receipts.")
    verify_sources.add_argument(
        "--root",
        default=".",
        help="Project root containing evidence/ (default: current directory).",
    )

    lineage = sub.add_parser("lineage", help="Validate the record-level synapse lineage index.")
    lineage.add_argument(
        "--root",
        default=".",
        help="Project root containing evidence/ (default: current directory).",
    )

    doctor = sub.add_parser(
        "doctor", help="Probe local capabilities and select healthy backends."
    )
    doctor.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    doctor.add_argument(
        "--backend",
        action="append",
        default=[],
        metavar="CAPABILITY=BACKEND",
        help="Promote an exact backend name for one capability.",
    )

    run_plan = sub.add_parser(
        "run-plan", help="Execute a checked JSON task plan and verify its receipts."
    )
    run_plan.add_argument("plan", help="Path to a JSON plan file.")
    run_plan.add_argument("--run-id", default=None, help="Stable ID used to resume a run.")
    run_plan.add_argument(
        "--state-root",
        default=".dlf/runtime",
        help="Directory for checkpoints, receipts, and run state.",
    )

    recover = sub.add_parser("recover", help="Recover exact FlyWire morphology.")
    recover.add_argument("--dataset", type=int, default=783)
    recover.add_argument("--output", default="data/morphology")
    recover.add_argument("--root", action="append", choices=list(ROOTS))

    args = parser.parse_args(argv)

    if args.command == "validate":
        from .validation import main as validate_main
        return validate_main(["--root", args.root])

    if args.command == "audit":
        from .provenance import audit_provenance
        from .validation import find_project_root
        root = find_project_root(args.root)
        print(json.dumps(audit_provenance(root), indent=2))
        return 0

    if args.command == "verify-sources":
        from .cross_source import validate_cross_source_receipts
        from .validation import find_project_root
        root = find_project_root(args.root)
        print(json.dumps(validate_cross_source_receipts(root), indent=2))
        return 0

    if args.command == "lineage":
        from .provenance import validate_synapse_lineage
        from .validation import find_project_root
        root = find_project_root(args.root)
        print(json.dumps(validate_synapse_lineage(root), indent=2))
        return 0

    if args.command == "run-plan":
        from .capabilities import CapabilityDoctor, default_capabilities
        from .execution import CapabilityExecutor, ExecutionError, ExecutionEngine
        from .orchestrator import OrchestrationError, TaskOrchestrator, verify_run

        try:
            plan = _load_run_plan(args.plan)
            engine = ExecutionEngine(args.state_root)
            executor = CapabilityExecutor(CapabilityDoctor(default_capabilities()), engine)
            orchestrator = TaskOrchestrator(executor, args.state_root)
            run_id, _ = orchestrator.run(plan, run_id=args.run_id)
            verification = verify_run(plan, run_id, state_root=args.state_root)
            print(json.dumps(verification.to_dict(), indent=2))
            return 0 if verification.status == "PASS" else 1
        except (ValueError, ExecutionError, OrchestrationError) as exc:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
            return 2

    if args.command == "doctor":
        from .capabilities import CapabilityDoctor, default_capabilities

        overrides = {}
        for value in args.backend:
            if "=" not in value:
                parser.error("--backend must use CAPABILITY=BACKEND")
            capability, backend = value.split("=", 1)
            if not capability or not backend:
                parser.error("--backend must use CAPABILITY=BACKEND")
            overrides[capability] = backend

        doctor = CapabilityDoctor(default_capabilities())
        report = doctor.check(overrides)
        print(json.dumps(report, indent=2) if args.json else doctor.format_report(report))
        return 0

    from .recovery import main as recovery_main
    sys.argv = [
        "dlf-flywire-recover",
        "--dataset",
        str(args.dataset),
        "--output",
        args.output,
    ]
    for root in args.root or []:
        sys.argv.extend(["--root", root])
    return recovery_main()
