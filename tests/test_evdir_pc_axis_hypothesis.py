import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_historical_evdir_pc_axis_rule_remains_a_hypothesis():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_evdir_pc_axis_hypothesis.json").read_text(
            encoding="utf-8"
        )
    )

    assert evidence["status"] == "HYPOTHESIS_ONLY_SUBTYPE_DEPENDENT_PC_AXIS_SELECTION"
    assert evidence["source"]["rows"] == 5828
    assert evidence["source"]["sha256"] == (
        "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f"
    )

    rule = evidence["candidate_rule"]
    assert rule["classification"] == "HYPOTHESIS_ONLY"
    assert math.isclose(
        rule["weighted_global_rmse_rad"],
        0.42643560211880194,
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert rule["weighted_global_rmse_rad"] < evidence["results"]["universal_y"]["rmse_rad"]

    groups = evidence["results"]["by_subtype"]
    for subtype in ("T4c", "T4d", "T5c", "T5d"):
        assert groups[subtype]["y_rmse_rad"] < 2e-6

    for subtype in ("T4a", "T4b", "T5a", "T5b"):
        assert groups[subtype]["x_rmse_rad"] < groups[subtype]["y_rmse_rad"]

    # The poorer T5 a/b planar fit is visible in the larger z-components and must not
    # be silently converted into an exact PC2 identity claim.
    assert groups["T5a"]["median_abs_z_component"] > 0.6
    assert groups["T5b"]["median_abs_z_component"] > 0.4
    assert any(
        "literally PC2" in item or "eigenvector index" in item
        for item in evidence["provenance_boundary"]["not_proven"]
    )

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    generator_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert generator_claim["status"] == "UNRESOLVED"


def test_pre_artifact_geojax_ordering_capability_is_not_misreported_as_producer_proof():
    geojax = json.loads(
        (ROOT / "evidence" / "public_geojax_preartifact_jax_pca.json").read_text(
            encoding="utf-8"
        )
    )
    snapshot = geojax["pre_artifact_axis_ordering_snapshot"]
    assert snapshot["source"]["commit"] == "33b0f8727ab447eff86e35a69c60c1f33b4d1513"
    align = snapshot["functions"]["align_point_cloud"]
    assert "Required caller-supplied eigenvector index order" in align["parameters"]["order"]
    assert "sign(sum(E * target_basis, axis=1))" in align["sign_rule"]
    assert "does not directly emit" in align["output_limit"]
    assert any("producer called" in item for item in snapshot["provenance_boundary"]["not_proven"])

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    capability_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-025")
    assert producer_claim["status"] == "UNRESOLVED"
    assert capability_claim["status"] == "PROVEN"
    assert "not that this code generated Subtype_evDir" in capability_claim["statement"]


def test_historical_point_data_public_history_keeps_producer_boundary_unresolved():
    history = json.loads(
        (ROOT / "evidence" / "point_data_historical_path_history.json").read_text(
            encoding="utf-8"
        )
    )
    events = {item["kind"]: item for item in history["events"]}
    consumer = events["consumer_notebook_added_before_artifact"]
    artifact = events["historical_binary_added"]
    duplicate = events["duplicate_add_commit_same_binary"]
    later = events["public_generator_notebooks_added_after_artifact_and_binary_removed"]

    assert consumer["timestamp"] == "2025-12-09T19:40:07Z"
    assert consumer["absolute_local_path_in_notebook"].endswith(
        "T45_Morpho_data/Data/Pickled_data/Point_data.pkl"
    )
    assert consumer["timing_seconds_before_first_binary_commit"] == 103
    assert artifact["timestamp"] == "2025-12-09T19:41:50Z"
    assert artifact["changed_paths"] == ["Data/Point_data.pkl"]
    assert artifact["blob_sha1"] == "b85caf49f45677f2075f7b5f2c8830141cd96d02"
    assert duplicate["blob_sha1"] == artifact["blob_sha1"]
    assert later["point_data_status"] == "removed"
    assert not later["later_metrics_notebook_observation"]["contains_literal_Subtype_evDir"]
    assert history["conclusions"]["unresolved_claim_id"] == "C-POINTDATA-002"

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    timeline_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-026")
    assert producer_claim["status"] == "UNRESOLVED"
    assert timeline_claim["status"] == "PROVEN"


def test_current_neurosetta_pca_history_is_post_artifact_and_not_producer_proof():
    history = json.loads(
        (ROOT / "evidence" / "public_neurosetta_geometry_timeline.json").read_text(
            encoding="utf-8"
        )
    )
    events = {item["kind"]: item for item in history["events"]}
    initial = events["repository_initial_commit"]
    first_pca = events["first_pca_module_in_public_git_history"]
    refactor = events["pca_refactored_into_geometry_utils"]

    assert history["source"]["repository_created_at"] == "2026-01-20T22:42:16Z"
    assert initial["timestamp"] == "2025-10-21T09:23:42Z"
    assert initial["files_at_this_commit"] == [".gitignore", "LICENSE.md", "README.md"]
    assert first_pca["timestamp"] == "2026-07-27T15:05:30Z"
    assert "np.linalg.svd" in first_pca["implementation_summary"]["principal_components"]
    assert refactor["timestamp"] == "2026-07-28T22:03:34Z"
    assert refactor["implementation_summary"]["eigensolver"] == "numpy.linalg.eigh"
    assert history["conclusion"]["unresolved_claim_id"] == "C-POINTDATA-002"

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    timeline_claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-027")
    assert producer_claim["status"] == "UNRESOLVED"
    assert timeline_claim["status"] == "PROVEN"


def test_legacy_neurosetta_eigen_alignment_is_a_pre_artifact_capability_not_producer_proof():
    evidence = json.loads(
        (ROOT / "evidence" / "legacy_neurosetta_eig_alignment.json").read_text(
            encoding="utf-8"
        )
    )
    impl = evidence["implementation"]
    assert evidence["source"]["pinned_commit"] == "9c27f226128d98ea5420e7a3a32acf2adc8ce138"
    assert evidence["source"]["commit_timestamp"] == "2025-01-15T11:30:24Z"
    assert impl["coord_eig_decomp"]["eigensolver"] == "numpy.linalg.eig"
    assert any(
        "via eig_order" in item for item in impl["eig_align"]["capabilities"]
    )
    assert any("eigenvector index" in item for item in impl["eig_align"]["capabilities"])
    assert impl["jax_declared_directly_in_environment_yml"] is False
    assert "does not define the historical Subtype_evDir_x/y/z" in impl["eig_align"]["output_behavior"]

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-002")
    legacy = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-028")
    assert producer["status"] == "UNRESOLVED"
    assert legacy["status"] == "PROVEN"
    assert "does not prove that this code produced Subtype_evDir" in legacy["statement"]


def test_jax_scalar_fingerprint_ranks_runtime_family_only_as_inference():
    matrix = json.loads(
        (ROOT / "evidence" / "point_data_revision_candidate_matrix.json").read_text(
            encoding="utf-8"
        )
    )
    comparison = matrix["runtime_type_fingerprint_assessment"]
    historical = comparison["historical_pickle"]
    assert historical["object_type"] == "jaxlib._jax.ArrayImpl"
    assert historical["scalar_cells"] == 46624
    assert len(historical["columns"]) == 8
    assert historical["rows"] * len(historical["columns"]) == historical["scalar_cells"]
    assert comparison["relative_compatibility"]["geojax"]["source_commit"] == (
        "33b0f8727ab447eff86e35a69c60c1f33b4d1513"
    )
    assert comparison["relative_compatibility"]["legacy_neurosetta"]["source_commit"] == (
        "9c27f226128d98ea5420e7a3a32acf2adc8ce138"
    )
    assert comparison["conclusion"]["status"] == "INFERENCE_ONLY"
    assert comparison["conclusion"]["unresolved_claim_id"] == "C-POINTDATA-002"

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-002")
    family_claim = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-029")
    assert producer["status"] == "UNRESOLVED"
    assert family_claim["status"] == "INFERENCE_ONLY"


def test_same_week_geojax_consumer_is_not_misidentified_as_point_data_producer():
    bridge = json.loads(
        (ROOT / "evidence" / "contemporaneous_pointdata_geojax_consumer.json").read_text(
            encoding="utf-8"
        )
    )
    observed = bridge["random_bifurcations_nonproducer_check"]
    nonproducer = observed["non_producer_indicators"]
    figure5 = observed["figure5_binding"]
    assert figure5["loads_exact_historical_point_data_blob"] is True
    assert figure5["notebook_blob_sha1"] == "a65df260ce2b118d44e58388349b91a6c9483333"
    assert figure5["consumes_from_point_data"] == ["PC1", "PC2", "PC3"]
    assert nonproducer["mentions_subtype_evdir_literal"] is False
    assert nonproducer["calls_coord_eig_decomp"] is False
    assert nonproducer["calls_align_point_cloud"] is False
    assert nonproducer["writes_point_data_pickle"] is False

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-002")
    consumer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-030")
    assert producer["status"] == "UNRESOLVED"
    assert consumer["status"] == "PROVEN"


def test_public_legacy_install_metadata_does_not_pin_geojax_revision():
    evidence = json.loads(
        (ROOT / "evidence" / "legacy_geojax_dependency_pin_audit.json").read_text(
            encoding="utf-8"
        )
    )
    dep = evidence["snapshots"][0]
    latest = evidence["snapshots"][1]
    assert dep["environment_yml"]["python"] == "3.10"
    assert dep["environment_yml"]["mentions_jax"] is False
    assert dep["requirements_txt"]["mentions_geoJax"] is False
    assert dep["requirements_txt"]["mentions_jax"] is False
    assert latest["source_file"]["observed_import"] == "import GeoJax"
    assert latest["environment_yml"]["jax"] == "listed without a version pin"
    assert latest["environment_yml"]["geoJax"] == "not listed"
    assert "does not pass install_requires=requirements" in dep["setup_py"]["observed"]
    assert evidence["conclusion"]["exact_dependency_revision"] == "UNRESOLVED"

    matrix = json.loads(
        (ROOT / "evidence" / "point_data_revision_candidate_matrix.json").read_text(
            encoding="utf-8"
        )
    )
    assert matrix["dependency_installation_metadata"]["status"] == (
        "PROVEN_PUBLIC_INSTALL_METADATA_DOES_NOT_PIN_GEOJAX"
    )
    assert matrix["dependency_installation_metadata"]["interpretation"].endswith(
        "Exact dependency resolution remains unresolved."
    )
    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-002")
    dependency = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-031")
    assert producer["status"] == "UNRESOLVED"
    assert dependency["status"] == "PROVEN"


def test_pre_artifact_geojax_package_version_does_not_bind_neurosetta_runtime():
    evidence = json.loads(
        (ROOT / "evidence" / "legacy_geojax_dependency_pin_audit.json").read_text(
            encoding="utf-8"
        )
    )
    upstream = evidence["upstream_geojax_package_metadata"]
    assert upstream["source"]["commit"] == "33b0f8727ab447eff86e35a69c60c1f33b4d1513"
    assert upstream["package_version"] == "0.2"
    assert upstream["packaging"]["install_requires"] == ["jax", "jaxlib"]
    assert upstream["packaging"]["pins_versions"] is False
    assert upstream["packaging"]["readme_installation_path"] == "pip install -e ."
    assert any(
        "installed GeoJax using this documented path" in item
        for item in upstream["interpretation"]["not_proven"]
    )
    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-002")
    dependency = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-031")
    assert producer["status"] == "UNRESOLVED"
    assert dependency["status"] == "PROVEN"


def test_bounded_public_producer_search_does_not_claim_global_absence():
    receipt = json.loads(
        (ROOT / "evidence" / "point_data_bounded_public_producer_search.json").read_text(
            encoding="utf-8"
        )
    )
    queries = receipt["code_searches"]
    assert len(queries) == 6
    assert all(item["result_count"] == 0 for item in queries)
    assert receipt["conclusion"]["independent_public_copy_found"] is False
    assert receipt["conclusion"]["exact_historical_producer_identity"] == "UNRESOLVED"
    assert "does not establish" in receipt["conclusion"]["limitation"]

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    producer = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-002")
    search_claim = next(c for c in claims["claims"] if c["id"] == "C-POINTDATA-032")
    assert producer["status"] == "UNRESOLVED"
    assert search_claim["status"] == "PROVEN"


def test_august_2026_archive_inventory_boundary_is_regression_guarded():
    archive = json.loads(
        (ROOT / "evidence" / "zenodo_2026_publication_archive_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    assert archive["status"] == "PROVEN_PUBLIC_2026_ARCHIVE_INVENTORY_BOUNDARY"
    assert "Notebooks/PP3_Dendrite_extraction.ipynb" in (
        archive["observed_publication_inventory"]["software_archive_includes"]
    )
    assert "Data/point_data.pkl" in archive["observed_publication_inventory"]["data_archive_includes"]
    assert "Reduced_dendrites/" in (
        archive["observed_publication_inventory"]["software_archive_paths_not_found_in_preview"]
    )
    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-033")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-ZENODO-2026-ARCHIVE" in claim["evidence"]


def test_public_pp1_pp3_pipeline_snapshot_preserves_historical_limitations():
    evidence = json.loads(
        (ROOT / "evidence" / "public_pp1_pp3_morphology_pipeline_snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_LATER_PUBLIC_PP1_PP3_PIPELINE_CALLS"
    sources = {item["path"]: item for item in evidence["source_release"]["notebooks"]}
    assert sources["Notebooks/PP1_Fetch_flywire.ipynb"]["git_blob_sha1"] == (
        "30d3376dcee3a09b9a0e305d4e18f16f6b35bb27"
    )
    assert any("100 nanometer" in call for call in sources["Notebooks/PP1_Fetch_flywire.ipynb"]["observed_calls"])
    assert any("max_workers=10" in call for call in sources["Notebooks/PP2_nr_conversion.ipynb"]["observed_inputs_and_calls"])
    assert any("reduce_forest" in call for call in sources["Notebooks/PP3_Dendrite_extraction.ipynb"]["observed_inputs_and_calls"])
    assert evidence["source_release"]["readme"]["git_blob_sha1"] == (
        "a70bc212f005ac730ec2dcfbfe8638dd6469fe80"
    )
    assert ".nr files" in evidence["source_release"]["readme"]["statement"]
    assert evidence["observed_pipeline_boundary"]["producer_binding"] == "UNRESOLVED"
    limitations = " ".join(evidence["observed_pipeline_boundary"]["reasons"])
    assert "df/n_ids" in limitations
    assert evidence["conclusions"]["unresolved_claim_id"] == "C-POINTDATA-002"

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    for claim_id in ("C-POINTDATA-034", "C-POINTDATA-035"):
        claim = next(item for item in claims["claims"] if item["id"] == claim_id)
        assert claim["status"] == "PROVEN"
        assert "E-POINTDATA-PUBLIC-PP1-PP3-PIPELINE" in claim["evidence"]
    unresolved = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert unresolved["status"] == "UNRESOLVED"


def test_legacy_neurosetta_root_selection_timeline_is_explicitly_bounded():
    evidence = json.loads(
        (ROOT / "evidence" / "legacy_neurosetta_subtree_root_timeline.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["status"] == "PROVEN_LEGACY_ROOT_SELECTION_RULE_AND_REVISION_BOUNDARY"
    timeline = {item["commit"]: item for item in evidence["revision_timeline"]}
    april = timeline["94ff9e5a956d5a91c40bb386f33e3dfa60896987"]
    june = timeline["b9681b64163a3e3a2937f8bb2058c06f1460b55a"]
    july_fix = timeline["9816dad67180ebf5937ae05316ae14d1f190aae4"]
    latest = timeline["25c911a28030deb5204eb7ab5a18ff4643363d96"]
    assert "optimal_partition_root" in april["absent_functions_in_inspected_snapshot"]
    assert "optimal_partition_root" in june["present_functions"]
    assert "g_vert_coords(simp_N, subset=b_inds)[scores.argmax()]" in july_fix["patch_observation"]
    assert "Subtree_root" in latest["interpretation"] or "Subtree_root" in evidence["observed_legacy_algorithm"]["procedure"][-1]
    assert evidence["observed_legacy_algorithm"]["score_formula"] == (
        "(1 - (sub_cable / total_cable)) + (sub_leaves / total_leaves)"
    )
    assert evidence["later_neurosetta_api_boundary"]["created_at"] > (
        evidence["historical_target"]["first_public_ingest_date"] + "T00:00:00Z"
    )
    assert evidence["conclusions"]["unresolved_claim_id"] == "C-POINTDATA-002"

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-036")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-LEGACY-ROOT-TIMELINE" in claim["evidence"]
    unresolved = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert unresolved["status"] == "UNRESOLVED"


def test_legacy_neurosetta_installer_metadata_does_not_reconstruct_runtime():
    evidence = json.loads(
        (ROOT / "evidence" / "legacy_neurosetta_subtree_root_timeline.json").read_text(
            encoding="utf-8"
        )
    )
    dependency = evidence["legacy_repository"]["dependency_metadata_observation"]
    setup = dependency["setup_behavior"]
    assert setup["reads_requirements_txt"] is True
    assert setup["passes_requirements_as_install_requires"] is False
    requirements = {entry.lower() for entry in dependency["requirements_entries"]}
    assert not any("geojax" in item for item in requirements)
    assert not any(item.startswith("jax") for item in requirements)
    assert dependency["environment_yml_python"] == "3.10"
    assert dependency["environment_yml_has_unpinned_jax"] is True
    assert dependency["environment_yml_has_explicit_geojax"] is False
    assert "does not prove the session lacked these packages" in (
        " ".join(evidence["conclusions"]["not_proven"])
    )

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-037")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-LEGACY-ROOT-TIMELINE" in claim["evidence"]
    unresolved = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert unresolved["status"] == "UNRESOLVED"


def test_public_metrics1_notebook_is_later_than_pointdata_and_not_a_complete_producer():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_pca_and_subtree_api_revision_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    historical = evidence["historical_artifact"]
    notebook = evidence["public_metrics1_notebook"]
    assert historical["commit_date"] == "2025-12-09T19:41:50Z"
    assert historical["changed_files_in_commit"] == ["Data/Point_data.pkl"]
    assert historical["rows"] == 5828
    assert historical["columns"] == 24
    assert notebook["first_public_commit_date"] == "2026-08-10T15:49:32Z"
    assert notebook["git_blob_sha1"] == "2c31080a7f6f69d1c603bf287e4a5da7d4c3712b"
    assert notebook["metric_function_column_count"] == 23
    assert notebook["bulk_apply_is_commented_out"] is True
    assert notebook["concat_is_commented_out"] is True
    assert notebook["save_operation_present"] is False
    assert set(notebook["missing_historical_direction_columns"]) == {
        "Subtype_evDir_x", "Subtype_evDir_y", "Subtype_evDir_z"
    }
    assert notebook["timeline_gap_from_historical_artifact_days"] == 244

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    for claim_id in ("C-POINTDATA-038",):
        claim = next(item for item in claims["claims"] if item["id"] == claim_id)
        assert claim["status"] == "PROVEN"
        assert "E-POINTDATA-PCA-SUBTREE-REVISION-BOUNDARY" in claim["evidence"]
    unresolved = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert unresolved["status"] == "UNRESOLVED"


def test_geojax_and_neurosetta_pca_revision_difference_is_bounded():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_pca_and_subtree_api_revision_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    versions = evidence["pca_implementation_chronology"]
    geo = versions["earlier_public_geojax_snapshot"]
    neuro = versions["later_public_neurosetta_pca"]
    assert geo["file_blob_sha1"] == "53560fd7de0463a51e1283b4a9c0e0db5bb33e8e"
    assert geo["implementation"]["covariance_denominator"] == "n (population covariance)"
    assert geo["implementation"]["eigenvector_output_layout_default"] == "rows because transpose=True by default"
    assert geo["implementation"]["explicit_right_handed_basis_correction"] is False
    assert neuro["pca_blob_sha1"] == "0539fe529e28f79e19785c1ac651a064bc8ddddb"
    assert neuro["implementation"]["covariance_denominator"] == "n-1 (unbiased sample covariance in covariance_xyz)"
    assert neuro["implementation"]["eigenvector_output_layout"] == "columns"
    assert "third eigenvector" in neuro["implementation"]["explicit_right_handed_basis_correction"]
    assert neuro["coordinate_wrapper_first_public_commit_date"] > (
        evidence["historical_artifact"]["commit_date"]
    )
    assert "Which PCA implementation or source revision produced" in (
        " ".join(evidence["conclusions"]["not_proven"])
    )

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-039")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-PCA-SUBTREE-REVISION-BOUNDARY" in claim["evidence"]


def test_legacy_and_current_subtree_scores_share_formula_not_method_identity():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_pca_and_subtree_api_revision_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    api = evidence["subtree_api_comparison"]
    assert api["formula"] == (
        "(1 - subtree_cable / total_cable) + (subtree_leaves / total_leaves)"
    )
    assert api["legacy_file_blob_sha1"] == "4406880c0fd8711d29f05fea006fa9c84ecf58b7"
    assert api["public_pp3_call"] == "forest.convert_forest_to_subtrees(max_workers=10)"
    assert "convert_forest_to_subtrees" not in api["current_neurosetta_paths"]["visible_method_surface"]
    assert api["current_neurosetta_paths"]["convert_forest_to_subtrees_found_by_current_code_search"] is False
    assert "same algebraic formula" in api["comparison"]
    assert "not shown to be byte-identical" in api["comparison"]

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-040")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-PCA-SUBTREE-REVISION-BOUNDARY" in claim["evidence"]
    unresolved = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert unresolved["status"] == "UNRESOLVED"


def test_early_neurosetta_public_source_does_not_bind_historical_pca_producer():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_pca_and_subtree_api_revision_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    chronology = evidence["pca_implementation_chronology"]["earliest_public_code_boundary"]
    old_tree = chronology["oldest_visible_git_commit"]
    code = chronology["first_inspected_code_snapshot"]
    editor = chronology["dated_editor_history_snapshot"]
    assert chronology["repository_api_created_at"] == "2026-01-20T22:42:16Z"
    assert old_tree["tree_file_count"] == 3
    assert old_tree["tree_blob_paths"] == [".gitignore", "LICENSE.md", "README.md"]
    assert code["commit"] == "f2d8778671a9c5e0ff97b8af44cf1bcefc4da57b"
    assert code["date"] > evidence["historical_artifact"]["commit_date"]
    assert code["coordinates_functions"] == ["vertex_coordinates", "edge_coordinates"]
    assert code["tree_class_has_coordinate_pca"] is False
    assert code["active_pca_module_found"] is False
    assert editor["source_timestamp_from_filename"] == "2025-10-21T17:13:21"
    assert editor["definitions"] == ["__init__", "get_coordinates"]
    assert editor["coordinate_pca_found"] is False
    assert "does not exclude private/local code" in chronology["conclusion"]

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-041")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-PCA-SUBTREE-REVISION-BOUNDARY" in claim["evidence"]
    unresolved = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert unresolved["status"] == "UNRESOLVED"


def test_legacy_neurosetta_pca_candidate_is_recorded_without_producer_attribution():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_pca_and_subtree_api_revision_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    legacy = evidence["pca_implementation_chronology"]["legacy_neurosetta_pca_candidate"]
    impl = legacy["observed_implementation"]
    assert legacy["function"] == (
        "coord_eig_decomp(coords, robust=True, center=False, PCA=True, sort=True, transpose=True)"
    )
    assert impl["robust_covariance"] == "sklearn.covariance.MinCovDet().fit(coords).covariance_"
    assert impl["nonrobust_covariance"] == "sklearn.covariance.EmpiricalCovariance().fit(coords).covariance_"
    assert impl["eigensolver"] == "numpy.linalg.eig"
    assert impl["eigenvector_layout_when_transpose_true"] == "rows; PC1 eigenvector is evecs[0]"
    assert legacy["producer_binding"] == "NOT_ESTABLISHED"
    assert legacy["runtime_reproducibility_caveat"]["scikit_learn_in_requirements_txt"] is False
    assert legacy["runtime_reproducibility_caveat"]["scikit_learn_explicit_in_environment_yml"] is False

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-042")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-PCA-SUBTREE-REVISION-BOUNDARY" in claim["evidence"]
    unresolved = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert unresolved["status"] == "UNRESOLVED"


def test_paper_repository_parent_tree_does_not_contain_public_producer_notebook():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_pca_and_subtree_api_revision_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    pre = evidence["paper_repository_preartifact_snapshot"]
    assert pre["parent_of_historical_pointdata_commit"] == "61fd0f176d73932ad87ece04153945501b4c405c"
    assert set(pre["parent_tree_paths"]) == {
        ".gitignore", "Notebooks/ANOVA_analysis.ipynb", "README.md"
    }
    assert pre["notebook_blob_sha1"] == "93eb31b90a738f64f5d803aaecda22f80edd6178"
    assert pre["observed_notebook_input_path"].endswith("/T45_Morpho_data/Data/Pickled_data/Point_data.pkl")
    assert pre["producer_notebook_in_parent_tree"] is False
    assert pre["changed_files_in_historical_data_commit"] == ["Data/Point_data.pkl"]

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-043")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-PCA-SUBTREE-REVISION-BOUNDARY" in claim["evidence"]
    unresolved = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert unresolved["status"] == "UNRESOLVED"


def test_pre_artifact_geojax_pca_candidate_matches_jax_value_family_without_producer_claim():
    evidence = json.loads(
        (ROOT / "evidence" / "point_data_pca_and_subtree_api_revision_boundary.json").read_text(
            encoding="utf-8"
        )
    )
    candidate = evidence["pca_implementation_chronology"]["pre_artifact_geojax_jax_candidate"]
    pca = candidate["pca_contract"]
    serializer = candidate["serializer_compatibility"]
    assert candidate["first_public_pca_commit"]["sha"] == "4dfc82bbc6dbe37b64a540758d6ea3ed6c9829aa"
    assert candidate["last_inspected_pre_artifact_public_head"]["sha"] == "33b0f8727ab447eff86e35a69c60c1f33b4d1513"
    assert candidate["last_inspected_pre_artifact_public_head"]["observed_public_commits_between_head_and_pointdata"] == 0
    assert pca["framework"] == "JAX"
    assert pca["robust_covariance"]["defaults"] == {"c": 1.5, "tol": 0.000001, "max_iter": 100}
    assert pca["eigensolver"] == "jnp.linalg.eigh"
    assert pca["default_eigenvector_layout"] == "rows when transpose=True"
    assert serializer["historical_jax_value_type"] == "jaxlib._jax.ArrayImpl"
    assert serializer["public_release_family"]["incompatible_standard_release"] == "jax-v0.4.30"
    assert serializer["public_release_family"]["first_checked_compatible_standard_release"] == "jax-v0.4.31"
    assert serializer["conditional_python_constraint"]["status"] == "CONDITIONAL_ONLY_NOT_A_PRODUCER_LOCK"
    assert candidate["comparison_to_legacy_numpy_candidate"]["certainty"] == (
        "COMPATIBILITY_COMPARISON_NOT_PRODUCER_IDENTIFICATION"
    )
    assert "strongest public-source candidate" in candidate["conclusion"]

    claims = json.loads((ROOT / "evidence" / "claims.json").read_text(encoding="utf-8"))
    claim = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-044")
    assert claim["status"] == "PROVEN"
    assert "E-POINTDATA-PCA-SUBTREE-REVISION-BOUNDARY" in claim["evidence"]
    unresolved = next(item for item in claims["claims"] if item["id"] == "C-POINTDATA-002")
    assert unresolved["status"] == "UNRESOLVED"
