from __future__ import annotations

import argparse
import json
import sys

from .constants import ROOTS


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
