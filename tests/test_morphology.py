from pathlib import Path

from dlf_flywire.morphology import validate_swc_file

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "T4a": (
        "720575940632008007",
        "d17623da9812d0f2ef53ab6aed4a9d89a2c2820d34aa0294af2ba434b6107c2a",
    ),
    "T4c": (
        "720575940616224414",
        "7d9cc29226e092c233f35cfcf70f75ac137b8c9f8744a1ba319264f96da3857a",
    ),
    "T5a": (
        "720575940625571465",
        "6d4d2a33cfea8525449b7a1508c6e6c2d9550034aac3774e6b2d64c4e76bae5c",
    ),
    "T5c": (
        "720575940617782941",
        "83b287e914522b0b382e3e46d39ced36494ff257d835cac11d7f4243ae1d7745",
    ),
}


def test_exact_reference_morphologies():
    for name, (root_id, digest) in EXPECTED.items():
        result = validate_swc_file(
            ROOT / "data" / "morphology" / f"{name}.swc",
            root_id,
        )
        assert result["valid"]
        assert result["sha256"] == digest
