from __future__ import annotations

import argparse
import json
import os
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
    capture_network_camera = sub.add_parser(
        "capture-network-camera",
        help="Capture bounded RTSP network-camera frames with secret-safe provenance.",
    )
    discover_cameras = sub.add_parser(
        "discover-network-cameras",
        help="Discover ONVIF cameras on the local network without moving or configuring them.",
    )
    discover_cameras.add_argument("--timeout", type=int, default=4)
    discover_cameras.add_argument(
        "--interface",
        default=None,
        help="Local interface IP to use for multicast discovery.",
    )
    discover_cameras.add_argument(
        "--search",
        default=None,
        help="Optional ONVIF type/scope filter such as Uho-S2E.",
    )
    discover_cameras.add_argument("--https", action="store_true")
    discover_cameras.add_argument(
        "--output",
        default="data/vision/onvif-discovery.json",
    )

    probe_camera_ptz = sub.add_parser(
        "probe-camera-ptz",
        help="Inspect ONVIF PTZ capability and position without moving the camera.",
    )
    probe_camera_ptz.add_argument(
        "--host",
        default=None,
        help="ONVIF camera host; prefer --host-env when convenient.",
    )
    probe_camera_ptz.add_argument(
        "--host-env",
        default="DLF_CAMERA_HOST",
        help="Environment variable containing the ONVIF camera host.",
    )
    probe_camera_ptz.add_argument("--port", type=int, default=80)
    probe_camera_ptz.add_argument(
        "--username-env",
        default="DLF_CAMERA_USERNAME",
        help="Environment variable containing the ONVIF username.",
    )
    probe_camera_ptz.add_argument(
        "--password-env",
        default="DLF_CAMERA_PASSWORD",
        help="Environment variable containing the ONVIF password.",
    )
    probe_camera_ptz.add_argument("--output", default="data/vision/ptz-probe.json")

    capture_network_camera.add_argument(
        "--url",
        default=None,
        help="RTSP URL; prefer --url-env so credentials do not enter shell history.",
    )
    capture_network_camera.add_argument(
        "--url-env",
        default="DLF_RTSP_URL",
        help="Environment variable containing the RTSP URL (default: DLF_RTSP_URL).",
    )
    capture_network_camera.add_argument("--frames", type=int, default=1)
    capture_network_camera.add_argument("--output", default="data/vision/network-capture")
    capture_network_camera.add_argument("--width", type=int, default=None)
    capture_network_camera.add_argument("--height", type=int, default=None)
    capture_network_camera.add_argument("--timeout", type=float, default=5.0)

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
    camera_flyvis.add_argument(
        "--rtsp-url",
        default=None,
        help="RTSP URL; prefer --rtsp-url-env so credentials do not enter shell history.",
    )
    camera_flyvis.add_argument(
        "--rtsp-url-env",
        default="DLF_RTSP_URL",
        help="Environment variable containing the RTSP URL (default: DLF_RTSP_URL).",
    )
    camera_flyvis.add_argument(
        "--onvif-host",
        default=None,
        help="ONVIF camera host; use this instead of supplying a manual RTSP URL.",
    )
    camera_flyvis.add_argument(
        "--onvif-host-env",
        default="DLF_CAMERA_HOST",
        help="Environment variable containing the ONVIF camera host.",
    )
    camera_flyvis.add_argument("--onvif-port", type=int, default=80)
    camera_flyvis.add_argument(
        "--onvif-username-env",
        default="DLF_CAMERA_USERNAME",
        help="Environment variable containing the ONVIF username.",
    )
    camera_flyvis.add_argument(
        "--onvif-password-env",
        default="DLF_CAMERA_PASSWORD",
        help="Environment variable containing the ONVIF password.",
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

    if args.command == "discover-network-cameras":
        from .network_discovery import (
            NetworkDiscoveryError,
            build_discovery_receipt,
            discover_onvif_devices,
        )

        try:
            devices = discover_onvif_devices(
                timeout_s=args.timeout,
                interface=args.interface,
                search=args.search,
                prefer_https=args.https,
            )
            receipt = build_discovery_receipt(
                devices=devices,
                timeout_s=args.timeout,
                interface=args.interface,
                search=args.search,
            )
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(receipt, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            payload = dict(receipt)
            payload["output"] = output.as_posix()
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        except (TypeError, ValueError, NetworkDiscoveryError) as exc:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
            return 2

    if args.command == "probe-camera-ptz":
        from .network_ptz import PTZProbeError, probe_onvif_ptz

        try:
            host = args.host or os.environ.get(args.host_env)
            username = os.environ.get(args.username_env)
            password = os.environ.get(args.password_env)
            if not host:
                raise PTZProbeError(
                    f"no ONVIF host supplied; pass --host or set {args.host_env}"
                )
            if not username:
                raise PTZProbeError(
                    f"missing ONVIF username environment variable: {args.username_env}"
                )
            if not password:
                raise PTZProbeError(
                    f"missing ONVIF password environment variable: {args.password_env}"
                )
            result = probe_onvif_ptz(
                host=host,
                port=args.port,
                username=username,
                password=password,
            )
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(result.to_dict(), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            payload = result.to_dict()
            payload["status"] = "PASS"
            payload["output"] = output.as_posix()
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        except (TypeError, ValueError, PTZProbeError) as exc:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
            return 2

    if args.command == "capture-network-camera":
        from .network_camera import NetworkCameraSource
        from .vision_input import VisionInputError, build_capture_receipt

        try:
            stream_url = args.url or os.environ.get(args.url_env)
            if not stream_url:
                raise VisionInputError(
                    f"no RTSP URL supplied; pass --url or set {args.url_env}"
                )
            output = Path(args.output)
            output.mkdir(parents=True, exist_ok=True)
            source = NetworkCameraSource(
                stream_url,
                width=args.width,
                height=args.height,
                per_frame_timeout_s=args.timeout,
            )
            frames = source.capture(args.frames)
            artifact_paths = []
            for frame in frames:
                name = f"frame-{frame.frame_index:06d}.pgm"
                frame.write_pgm(output / name)
                artifact_paths.append((output / name).as_posix())
            receipt = build_capture_receipt(
                frames,
                source_kind="camera/rtsp",
                source_locator=source.source_locator,
                artifact_paths=artifact_paths,
            )
            receipt_path = output / "receipt.json"
            receipt_sha256 = receipt.write(receipt_path)
            print(
                json.dumps(
                    {
                        "status": "PASS",
                        "frame_count": len(frames),
                        "source": source.source_locator,
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
            stream_url = args.rtsp_url or os.environ.get(args.rtsp_url_env)
            if stream_url and args.onvif_host:
                raise CameraFlyVisError(
                    "choose either a direct RTSP URL or ONVIF stream resolution, not both"
                )
            if not stream_url and args.onvif_host:
                from .network_camera import resolve_rtsp_stream

                username = os.environ.get(args.onvif_username_env)
                password = os.environ.get(args.onvif_password_env)
                if not username or not password:
                    raise CameraFlyVisError(
                        "ONVIF username/password environment variables are required "
                        "when --onvif-host is used"
                    )
                resolution = resolve_rtsp_stream(
                    host=args.onvif_host,
                    port=args.onvif_port,
                    username=username,
                    password=password,
                )
                stream_url = resolution.connection_uri
            if not stream_url:
                onvif_host = os.environ.get(args.onvif_host_env)
                username = os.environ.get(args.onvif_username_env)
                password = os.environ.get(args.onvif_password_env)
                if onvif_host or username or password:
                    if not onvif_host or not username or not password:
                        raise CameraFlyVisError(
                            "ONVIF host, username, and password environment variables "
                            "must all be set together"
                        )
                    from .network_camera import resolve_rtsp_stream

                    resolution = resolve_rtsp_stream(
                        host=onvif_host,
                        port=args.onvif_port,
                        username=username,
                        password=password,
                    )
                    stream_url = resolution.connection_uri

            receipt = run_camera_to_flyvis(
                device_index=args.device,
                frame_count=args.frames,
                output=args.output,
                stream_url=stream_url,
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
