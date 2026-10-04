import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_milestone_product_surfaces():
    forbidden = (
        "v229_",
        "v230_",
        "v231_",
        "v233_",
        "v235_",
        "v236_",
        "v237_",
        "v238_",
        "v239_",
        "v240_",
        "v241_",
        "v253_",
        "v254_",
        "v255_",
        "v256_",
        "v257_",
        "v258_",
        "v259_",
        "v261_",
        "v262_",
        "v264_",
        "v280_",
    )
    for path in ROOT.rglob("*"):
        if ".git" not in path.parts:
            assert not any(part.startswith(forbidden) for part in path.parts), path


def test_github_actions_are_pinned_to_full_commit_shas():
    pattern = re.compile(r"^\s*(?:-\s*)?uses:\s+[^@\s]+@([0-9a-f]{40})\s*(?:#.*)?$")
    workflow_dir = ROOT / ".github" / "workflows"
    assert workflow_dir.is_dir()

    for path in sorted(workflow_dir.glob("*.yml")):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if "uses:" not in line:
                continue
            assert pattern.match(line), f"{path}:{lineno}: unpinned action: {line}"
