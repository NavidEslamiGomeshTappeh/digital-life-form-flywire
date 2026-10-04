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
