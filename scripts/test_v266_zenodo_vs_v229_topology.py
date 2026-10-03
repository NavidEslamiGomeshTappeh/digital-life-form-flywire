import json
import subprocess
from pathlib import Path


def test_zenodo_source_snapshot():
    x = json.loads(
        Path("v264_results/V264_Point_data_anchor_rows.json").read_text(encoding="utf-8")
    )
    assert x["source"]["zenodo_record"] == "10.5281/zenodo.21876510"
    assert x["source"]["sha256"] == "46772ccabc609ab0f7136854024e7665727ff0f58f53c69126ea3e641ce7f891"
    assert x["source"]["git_blob"] == "0db640c17d820bed016da793648cf6b3f27f4738"
    assert x["source"]["historical_git_blob"] == "b85caf49f45677f2075f7b5f2c8830141cd96d02"


def test_no_exact_subtree_matches_all_four_cells():
    subprocess.run(["python", "scripts/v266_zenodo_vs_v229_topology.py"], check=True)
    x = json.loads(
        Path("v266_results/V266_Zenodo_vs_V229_topology.json").read_text(encoding="utf-8")
    )
    assert x["summary"]["all_four_exact_leaf_branch_matches"] is False
    assert all(not cell["exact_subtree_count_candidates"] for cell in x["cells"].values())
