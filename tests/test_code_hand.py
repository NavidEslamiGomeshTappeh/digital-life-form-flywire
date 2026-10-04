from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from dlf_flywire.code_hand import CodeHand, CodeHandError


def test_code_hand_creates_tests_and_verifies_python_file(tmp_path):
    hand = CodeHand(tmp_path, tmp_path / "state")
    result = hand.execute(
        "generated.py",
        "def add(a, b):\n    return a + b\n",
        "assert add(2, 3) == 5\nassert add(-2, 5) == 3",
        run_id="code-hand",
        permission_granted=True,
    )

    assert result.status == "PASS"
    assert result.verification.successful_steps == 2
    assert Path(result.file_path).read_text(encoding="utf-8") == (
        "def add(a, b):\n    return a + b\n"
    )
    assert result.receipts["create-file"].status == "succeeded"
    assert result.receipts["test-file"].stdout.strip() == "CODE_HAND_TEST_PASS"
    assert result.receipts["create-file"].policy_decision["status"] == "allow"
    assert result.receipts["test-file"].policy_decision["status"] == "allow"


def test_code_hand_edits_with_exact_hash_precondition_and_verifies(tmp_path):
    hand = CodeHand(tmp_path, tmp_path / "state")
    original = "def add(a, b):\n    return a + b\n"
    created = hand.execute(
        "generated.py",
        original,
        "assert add(2, 3) == 5",
        run_id="create-edit-target",
        permission_granted=True,
    )
    updated = "def add(a, b):\n    return a + b + 1\n"
    result = hand.edit(
        "generated.py",
        created.content_sha256.upper(),
        updated,
        "assert add(2, 3) == 6",
        run_id="edit",
        permission_granted=True,
    )

    assert result.status == "PASS"
    assert result.verification.successful_steps == 2
    assert result.receipts["edit-file"].stdout.find("OLD_CONTENT_SHA256") >= 0
    assert result.receipts["edit-file"].stdout.find("NEW_CONTENT_SHA256") >= 0
    assert Path(result.file_path).read_text(encoding="utf-8") == updated


def test_code_hand_edit_rejects_stale_hash_without_mutating_file(tmp_path):
    hand = CodeHand(tmp_path, tmp_path / "state")
    target = Path(tmp_path) / "generated.py"
    original = "value = 1\n"
    target.write_text(original, encoding="utf-8")
    stale_hash = hashlib.sha256(b"value = 999\n").hexdigest()

    with pytest.raises(Exception, match="ended with status='failed'"):
        hand.edit(
            "generated.py",
            stale_hash,
            "value = 2\n",
            "assert value == 2",
            run_id="stale-edit",
            permission_granted=True,
        )

    assert target.read_text(encoding="utf-8") == original


def test_code_hand_requires_explicit_permission(tmp_path):
    hand = CodeHand(tmp_path, tmp_path / "state")
    with pytest.raises(Exception, match="permission_granted"):
        hand.execute(
            "generated.py",
            "print('no')\n",
            "assert False",
            run_id="denied",
            permission_granted=False,
        )


@pytest.mark.parametrize(
    "relative_path",
    [
        "../outside.py",
        "/absolute.py",
        "..\\outside.py",
    ],
)
def test_code_hand_rejects_paths_outside_workspace(tmp_path, relative_path):
    hand = CodeHand(tmp_path, tmp_path / "state")
    with pytest.raises(CodeHandError, match="workspace"):
        hand.build_plan(
            relative_path,
            "print('x')\n",
            "assert True",
            permission_granted=True,
        )


def test_code_hand_refuses_overwrite(tmp_path):
    target = Path(tmp_path) / "existing.py"
    target.write_text("value = 1\n", encoding="utf-8")
    hand = CodeHand(tmp_path, tmp_path / "state")
    with pytest.raises(CodeHandError, match="already exists"):
        hand.build_plan(
            "existing.py",
            "value = 2\n",
            "assert value == 2",
            permission_granted=True,
        )
