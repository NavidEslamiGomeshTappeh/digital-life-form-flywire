from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


REMOTE = "https://github.com/borstlab/T4_T5_Dendrite_Morphology_Paper.git"

INITIAL = "79cf52212935de6bddf996c9f46c0df89f5c5442"
POINT_FIRST = "cd17d34afd0d46a3c2947e83a1f0fdd835a9959a"
POINT_SECOND = "fe9779d4ca425613eec44b19e961610d117e7232"
PUBLIC_PREPROCESSING = "8700efd40bccfa3e74ac7c4df02da83a968b9b52"

PP1 = "Notebooks/PP1_Fetch_flywire.ipynb"
PP3 = "Notebooks/PP3_Dendrite_extraction.ipynb"
POINT = "Data/Point_data.pkl"


def run(*args: str, cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def paths_at(repo: Path, sha: str) -> set[str]:
    out = run("ls-tree", "-r", "--name-only", sha, cwd=repo)
    return {line for line in out.splitlines() if line}


def commit_time(repo: Path, sha: str) -> str:
    return run("show", "-s", "--format=%cI", sha, cwd=repo)


def commit_message(repo: Path, sha: str) -> str:
    return run("show", "-s", "--format=%s", sha, cwd=repo)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="v280-study-") as td:
        repo = Path(td)
        run("init", "-q", cwd=repo)
        run("remote", "add", "origin", REMOTE, cwd=repo)

        for sha in (INITIAL, POINT_FIRST, POINT_SECOND, PUBLIC_PREPROCESSING):
            run("fetch", "--no-tags", "--depth=1", "origin", sha, cwd=repo)

        initial_paths = paths_at(repo, INITIAL)
        point_first_paths = paths_at(repo, POINT_FIRST)
        point_second_paths = paths_at(repo, POINT_SECOND)
        preprocessing_paths = paths_at(repo, PUBLIC_PREPROCESSING)

        checks = {
            "initial_contains_only_baseline_files": initial_paths == {".gitignore", "README.md"},
            "initial_has_no_pp1": PP1 not in initial_paths,
            "initial_has_no_pp3": PP3 not in initial_paths,
            "initial_has_no_point_data": POINT not in initial_paths,
            "first_point_commit_contains_point_data": POINT in point_first_paths,
            "first_point_commit_has_no_pp1": PP1 not in point_first_paths,
            "first_point_commit_has_no_pp3": PP3 not in point_first_paths,
            "first_point_commit_has_no_later_preprocessing_package": not any(
                p.startswith("Notebooks/PP") for p in point_first_paths
            ),
            "second_point_commit_contains_point_data": POINT in point_second_paths,
            "public_preprocessing_contains_pp1": PP1 in preprocessing_paths,
            "public_preprocessing_contains_pp3": PP3 in preprocessing_paths,
        }

        initial_dt = datetime.fromisoformat(commit_time(repo, INITIAL).replace("Z", "+00:00"))
        point_dt = datetime.fromisoformat(commit_time(repo, POINT_FIRST).replace("Z", "+00:00"))
        public_dt = datetime.fromisoformat(
            commit_time(repo, PUBLIC_PREPROCESSING).replace("Z", "+00:00")
        )

        report = {
            "status": "PASS_HISTORICAL_GENERATOR_TEMPORAL_BOUNDARY"
            if all(checks.values())
            else "FAIL",
            "repository": "borstlab/T4_T5_Dendrite_Morphology_Paper",
            "remote": REMOTE,
            "commits": {
                "initial": {
                    "sha": INITIAL,
                    "timestamp": commit_time(repo, INITIAL),
                    "message": commit_message(repo, INITIAL),
                    "path_count": len(initial_paths),
                    "paths": sorted(initial_paths),
                },
                "first_point_data": {
                    "sha": POINT_FIRST,
                    "timestamp": commit_time(repo, POINT_FIRST),
                    "message": commit_message(repo, POINT_FIRST),
                    "path_present": POINT in point_first_paths,
                },
                "second_point_data": {
                    "sha": POINT_SECOND,
                    "timestamp": commit_time(repo, POINT_SECOND),
                    "message": commit_message(repo, POINT_SECOND),
                    "path_present": POINT in point_second_paths,
                },
                "public_preprocessing_release": {
                    "sha": PUBLIC_PREPROCESSING,
                    "timestamp": commit_time(repo, PUBLIC_PREPROCESSING),
                    "message": commit_message(repo, PUBLIC_PREPROCESSING),
                    "pp1_present": PP1 in preprocessing_paths,
                    "pp3_present": PP3 in preprocessing_paths,
                },
            },
            "elapsed_seconds": {
                "initial_to_first_point_data": (point_dt - initial_dt).total_seconds(),
                "first_point_data_to_public_preprocessing": (
                    public_dt - point_dt
                ).total_seconds(),
            },
            "checks": checks,
            "interpretation": {
                "proven": (
                    "The currently public PP1/PP3 preprocessing notebooks were not "
                    "present in the study repository when Point_data.pkl was first committed."
                ),
                "not_proven": (
                    "The historical December 2025 generator implementation is not recovered."
                ),
            },
        }

        out = Path("v280_results")
        out.mkdir(parents=True, exist_ok=True)
        (out / "V280_historical_generator_boundary.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        if report["status"] != "PASS_HISTORICAL_GENERATOR_TEMPORAL_BOUNDARY":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
