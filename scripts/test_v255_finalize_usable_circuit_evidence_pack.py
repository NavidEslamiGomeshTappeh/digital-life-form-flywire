from __future__ import annotations

import csv

import json
from pathlib import Path
from types import SimpleNamespace

from scripts.v255_finalize_usable_circuit_evidence_pack import build

ROOTS = [
    "720575940632008007",
    "720575940616224414",
    "720575940625571465",
    "720575940617782941",
]


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tiny_swc(path: Path, rid: str):
    write(
        path,
        '# Meta: {"id": "' + rid + '", "units": "1 nanometer"}\n'
        "1 1 0 0 0 10 -1\n"
        "2 0 10 0 0 1 1\n"
        "3 6 20 0 0 1 2\n",
    )


def args_for(core, v230, ann, morph, out):
    return SimpleNamespace(
        core_dir=str(core),
        v230=str(v230),
        annotations=str(ann),
        morphology_dir=str(morph),
        output=str(out),
        zip=None,
        dataset="FAFB v783",
        annotation_tag="v3.2.0",
        annotation_commit="test-commit",
        annotation_url="https://example.invalid/annotations",
        software_revision="test",
        v254_command="python scripts/v254_build_circuit_evidence_pack.py ...",
        v255_command="python scripts/v255_finalize_usable_circuit_evidence_pack.py ...",
        max_distance_nm=None,
    )

def test_usable_pack_end_to_end(tmp_path):
    core = tmp_path / "core"
    morph = tmp_path / "morph"
    out = tmp_path / "pack"
    ann = tmp_path / "annotations.tsv"
    v230 = tmp_path / "V230_target_synapses.csv"

    core.mkdir()
    write(
        core / "connections_selected.csv",
        "pre_root_id,post_root_id,neuropil,syn_count,nt_type\n"
        f"{ROOTS[0]},999,A,2,chol\n",
    )
    write(
        core / "synapses_selected.csv",
        "pre_root_id,post_root_id,x,y,z\n"
        f"{ROOTS[0]},999,10,0,0\n"
        f"{ROOTS[0]},999,20,0,0\n",
    )
    write(core / "MANIFEST.json", json.dumps({"selected_directed_pairs": 1}) + "\n")
    write(
        v230,
        "pre_root_id,post_root_id,x,y,z\n"
        f"{ROOTS[0]},999,10,0,0\n"
        f"{ROOTS[0]},999,20,0,0\n",
    )

    morph.mkdir()
    for name, rid in zip(("T4a", "T4c", "T5a", "T5c"), ROOTS):
        tiny_swc(morph / f"{name}_{rid}.swc", rid)

    write(
        ann,
        "root_id\tcell_type\tcell_class\tsuper_class\tvfb_id\n"
        + "".join(f"{rid}\tType-{i}\tclass\tsuper\tfw{['077172','091869','056211','077474'][i]}\n" for i, rid in enumerate(ROOTS)),
    )

    build(args_for(core, v230, ann, morph, out))

    manifest = json.loads((out / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "PASS_CORE_WITH_GEOMETRY_MAPPING"
    assert manifest["counts"]["anchor_roots"] == 4
    assert manifest["counts"]["selected_synapse_rows"] == 2
    assert manifest["counts"]["geometry_mapping_rows"] == 2
    assert manifest["exact_identity"]["status"] == "PASS"
    assert manifest["exact_morphology"]["status"] == "PASS"
    identities = list(csv.DictReader((out / "identity.csv").open(encoding="utf-8")))
    assert {r["vfb_id_from_annotation"] for r in identities} == {
        "VFB_fw077172", "VFB_fw091869", "VFB_fw056211", "VFB_fw077474"
    }
    assert (out / "identity.csv").exists()
    assert (out / "morphology_manifest.csv").exists()
    assert (out / "synapse_geometry_mapping.csv").exists()


def test_fails_closed_on_missing_annotation(tmp_path):
    core = tmp_path / "core"
    morph = tmp_path / "morph"
    out = tmp_path / "pack"
    ann = tmp_path / "annotations.tsv"
    v230 = tmp_path / "V230_target_synapses.csv"

    core.mkdir()
    write(core / "connections_selected.csv", "pre_root_id,post_root_id,neuropil,syn_count,nt_type\n")
    write(core / "synapses_selected.csv", "pre_root_id,post_root_id,x,y,z\n")
    write(core / "MANIFEST.json", '{"selected_directed_pairs": 0}\n')
    write(v230, "pre_root_id,post_root_id,x,y,z\n")

    morph.mkdir()
    for name, rid in zip(("T4a", "T4c", "T5a", "T5c"), ROOTS):
        tiny_swc(morph / f"{name}_{rid}.swc", rid)

    write(ann, "root_id\tcell_type\n" + f"{ROOTS[0]}\tOnlyOne\n")

    try:
        build(args_for(core, v230, ann, morph, out))
    except RuntimeError as exc:
        assert "annotation evidence missing" in str(exc)
    else:
        raise AssertionError("missing annotation evidence must fail closed")


def test_fails_closed_on_root_unrelated_synapse(tmp_path):
    core = tmp_path / "core"
    morph = tmp_path / "morph"
    out = tmp_path / "pack"
    ann = tmp_path / "annotations.tsv"
    v230 = tmp_path / "V230_target_synapses.csv"

    core.mkdir()
    write(core / "connections_selected.csv", "pre_root_id,post_root_id,neuropil,syn_count,nt_type\n")
    write(core / "synapses_selected.csv", "pre_root_id,post_root_id,x,y,z\n111,222,10,0,0\n")
    write(core / "MANIFEST.json", '{"selected_directed_pairs": 1}\n')
    write(v230, "pre_root_id,post_root_id,x,y,z\n111,222,10,0,0\n")

    morph.mkdir()
    for name, rid in zip(("T4a", "T4c", "T5a", "T5c"), ROOTS):
        tiny_swc(morph / f"{name}_{rid}.swc", rid)

    write(
        ann,
        "root_id\tcell_type\n"
        + "".join(f"{rid}\tType-{i}\n" for i, rid in enumerate(ROOTS)),
    )

    try:
        build(args_for(core, v230, ann, morph, out))
    except RuntimeError as exc:
        assert "is not incident to an anchor root" in str(exc)
    else:
        raise AssertionError("unrelated synapse must fail closed")
