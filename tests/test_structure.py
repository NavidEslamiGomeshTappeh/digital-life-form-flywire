import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_versioned_product_surfaces():
    pattern = re.compile(r"(?i)^v\d+[_-]")
    for path in ROOT.rglob("*"):
        if ".git" not in path.parts:
            assert not any(pattern.match(part) for part in path.parts), path


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
