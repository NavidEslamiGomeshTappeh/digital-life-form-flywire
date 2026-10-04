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
