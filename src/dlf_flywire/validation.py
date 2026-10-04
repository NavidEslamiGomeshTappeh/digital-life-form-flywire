from __future__ import annotations

import argparse
import json
from pathlib import Path

from .constants import ROOTS
from .morphology import validate_swc_file
from .provenance import audit_provenance

EXPECTED_SHA256 = {
    "T4a": "d17623da9812d0f2ef53ab6aed4a9d89a2c2820d34aa0294af2ba434b6107c2a",
    "T4c": "7d9cc29226e092c233f35cfcf70f75ac137b8c9f8744a1ba319264f96da3857a",
    "T5a": "6d4d2a33cfea8525449b7a1508c6e6c2d9550034aac3774e6b2d64c4e76bae5c",
    "T5c": "83b287e914522b0b382e3e46d39ced36494ff257d835cac11d7f4243ae1d7745",
}


def find_project_root(candidate: str | Path) -> Path:
    start = Path(candidate).resolve()
    if start.is_file():
        start = start.parent

    for root in (start, *start.parents):
        if (root / "evidence" / "manifest.json").is_file():
            return root

    raise RuntimeError(
        f"Cannot find the Version 1 project root from {start}. "
        "Expected evidence/manifest.json."
    )


def validate_project(root: Path) -> dict:
    for name, root_id in ROOTS.items():
        path = root / "data" / "morphology" / f"{name}.swc"
        report = validate_swc_file(path, str(root_id))
        if not report["valid"]:
            raise RuntimeError(f"{name}: invalid morphology: {report}")
        if report["sha256"] != EXPECTED_SHA256[name]:
            raise RuntimeError(f"{name}: morphology hash drift")

    from .evidence import validate_reference_evidence

    evidence = validate_reference_evidence(root / "evidence")
    provenance = audit_provenance(root)
    return {"status": "PASS", "version": provenance["product_version"], **evidence, "provenance": provenance}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate the consolidated Version 1 repository.")
    parser.add_argument(
        "--root",
        default=".",
        help="Project root containing data/ and evidence/ (default: current directory).",
    )
    args = parser.parse_args(argv)

    root = find_project_root(args.root)
    result = validate_project(root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
