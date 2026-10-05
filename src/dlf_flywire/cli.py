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
        raise TypeError("plan must be an object with a steps list")

    steps = []
    for index, item in enumerate(data["steps"]):
        if not isinstance(item, dict):
            raise TypeError(f"step {index} must be an object")
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

        for name in ("step_id", "capability", "action", "destination"):
            if not isinstance(item[name], str) or not item[name].strip():
                raise ValueError(f"step {index} {name} must be a non-empty string")

        risk = item.get("risk_tier", 0)
        if isinstance(risk, bool) or not isinstance(risk, int) or risk not in {0, 1, 2}:
            raise ValueError(f"step {index} risk_tier must be 0, 1, or 2")

        flags = {}
        for name in ("permission_granted", "idempotent", "network_access", "system_mutation"):
            value = item.get(name, False)
            if not isinstance(value, bool):
                raise TypeError(f"step {index} {name} must be a JSON boolean")
            flags[name] = value

        backend_override = item.get("backend_override")
        if backend_override is not None and (
            not isinstance(backend_override, str) or not backend_override.strip()
        ):
            raise ValueError(f"step {index} backend_override must be a string or null")

        steps.append(
            TaskStep(
                step_id=item["step_id"],
                capability=item["capability"],
                action=item["action"],
                destination=item["destination"],
                risk_tier=risk,
                permission_granted=flags["permission_granted"],
                operation_args=tuple(args),
                dependencies=tuple(deps),
                backend_override=backend_override,
                idempotent=flags["idempotent"],
                network_access=flags["network_access"],
                system_mutation=flags["system_mutation"],
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

    claim = sub.add_parser("claim", help="Trace one claim to its immutable evidence artifacts.")
    claim.add_argument("claim_id", help="Claim identifier, for example C-FLYVIS-RUNTIME-001.")
    claim.add_argument(
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

    capture_camera = sub.add_parser(
        "capture-camera",
        help="Capture bounded physical-camera frames with provenance receipts.",
    )
    capture_camera.add_argument("--device", type=int, default=0)
    capture_camera.add_argument("--frames", type=int, default=1)
    capture_camera.add_argument("--output", default="data/vision/capture")
    capture_camera.add_argument("--width", type=int, default=None)
    capture_camera.add_argument("--height", type=int, default=None)
    capture_camera.add_argument("--timeout", type=float, default=5.0)

    camera_flyvis = sub.add_parser(
        "camera-flyvis",
        help="Capture physical-camera frames and run them through pinned FlyVis.",
    )
    camera_flyvis.add_argument("--device", type=int, default=0)
    camera_flyvis.add_argument("--frames", type=int, default=20)
    camera_flyvis.add_argument("--output", default="data/vision/camera-flyvis")
    camera_flyvis.add_argument("--width", type=int, default=None)
    camera_flyvis.add_argument("--height", type=int, default=None)
    camera_flyvis.add_argument("--timeout", type=float, default=5.0)
    camera_flyvis.add_argument("--dt", type=float, default=1 / 100)

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

    if args.command == "claim":
        from .provenance import trace_claim
        from .validation import find_project_root
        root = find_project_root(args.root)
        print(json.dumps(trace_claim(root, args.claim_id), indent=2))
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

    if args.command == "capture-camera":
        from .vision_input import (
            OpenCVCameraSource,
            VisionInputError,
            build_capture_receipt,
        )

        try:
            output = Path(args.output)
            output.mkdir(parents=True, exist_ok=True)
            frames = OpenCVCameraSource(
                device_index=args.device,
                width=args.width,
                height=args.height,
                per_frame_timeout_s=args.timeout,
            ).capture(args.frames)
            artifact_paths = []
            for frame in frames:
                name = f"frame-{frame.frame_index:06d}.pgm"
                frame.write_pgm(output / name)
                artifact_paths.append((output / name).as_posix())
            receipt = build_capture_receipt(
                frames,
                source_kind="camera/opencv",
                source_locator=f"device-index:{args.device}",
                artifact_paths=artifact_paths,
            )
            receipt_path = output / "receipt.json"
            receipt_sha256 = receipt.write(receipt_path)
            print(
                json.dumps(
                    {
                        "status": "PASS",
                        "frame_count": len(frames),
                        "output": output.as_posix(),
                        "receipt": receipt_path.as_posix(),
                        "receipt_sha256": receipt_sha256,
                    },
                    indent=2,
                )
            )
            return 0
        except (TypeError, ValueError, VisionInputError) as exc:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
            return 2

    if args.command == "camera-flyvis":
        from .camera_flyvis import CameraFlyVisError, run_camera_to_flyvis

        try:
            receipt = run_camera_to_flyvis(
                device_index=args.device,
                frame_count=args.frames,
                output=args.output,
                width=args.width,
                height=args.height,
                per_frame_timeout_s=args.timeout,
                dt_s=args.dt,
            )
            print(json.dumps(receipt, indent=2, sort_keys=True))
            return 0
        except (TypeError, ValueError, CameraFlyVisError) as exc:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
            return 2

    if args.command == "run-plan":
        from .capabilities import CapabilityDoctor, default_capabilities
        from .execution import CapabilityExecutor, ExecutionEngine, ExecutionError
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
        except (TypeError, ValueError, ExecutionError, OrchestrationError) as exc:
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
