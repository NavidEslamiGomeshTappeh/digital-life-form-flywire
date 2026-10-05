from __future__ import annotations  # noqa: I001

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import flyvis
import numpy as np
from flyvis import NetworkView
from flyvis.datasets.moving_bar import MovingEdge
from flyvis.analysis.moving_bar_responses import preferred_direction

from dlf_flywire.flyvis_adapter import FlyVisResponseAdapter
from dlf_flywire.flyvis_runtime import (
    DEFAULT_DIRECTION_TOLERANCE_DEG,
    EXPECTED_PREFERRED_DIRECTION_DEG,
    FLYVIS_RELEASE,
    FLYVIS_REVISION,
    PRETRAINED_ARCHIVE_SHA256,
    FlyVisDirectionObservation,
    angular_distance_deg,
    validate_direction_observation,
)


TARGET_INTENSITY = {
    "T4a": 1,
    "T4c": 1,
    "T5a": 0,
    "T5c": 0,
}
ANGLES_DEG = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_pretrained_archive(root: Path) -> Path:
    direct = root / "results_pretrained_models.zip"
    if direct.is_file():
        return direct
    matches = sorted(root.rglob("results_pretrained_models.zip"))
    if len(matches) != 1:
        raise RuntimeError(
            "expected exactly one results_pretrained_models.zip under FLYVIS_ROOT_DIR"
        )
    return matches[0]


def summarize_direction(
    responses,
    cell_type: str,
    intensity: int,
) -> tuple[float, list[float]]:
    cell_mask = responses["cell_type"] == cell_type
    selected = responses["responses"].sel(network_id=0).where(cell_mask, drop=True)
    if selected.sizes.get("neuron", 0) == 0:
        raise RuntimeError(f"FlyVis returned no neurons for cell type {cell_type}")

    selected = selected.where(
        responses["intensity"] == intensity,
        drop=True,
    )
    if selected.sizes.get("sample", 0) == 0:
        raise RuntimeError(
            f"FlyVis returned no {intensity} intensity samples for {cell_type}"
        )

    peaks = selected.clip(min=0).max(dim="frame").mean(dim="neuron")
    per_angle = peaks.groupby("angle").mean(dim="sample")
    values = np.asarray(per_angle.values, dtype=float)
    angles = [float(value) for value in per_angle["angle"].values]
    if values.size == 0 or not np.isfinite(values).any():
        raise RuntimeError(f"FlyVis returned no finite response peaks for {cell_type}")
    return angles[int(np.nanargmax(values))], [float(value) for value in values]


def extract_trace_signal(
    responses,
    stimulus_dataset,
    cell_type: str,
    intensity: int,
    expected_direction_deg: float,
    checkpoint_sha256: str,
):
    cell_mask = responses["cell_type"] == cell_type
    response_da = responses["responses"].sel(network_id=0)
    selected = response_da.where(cell_mask, drop=True)

    matches = stimulus_dataset.arg_df[
        (stimulus_dataset.arg_df["angle"] == expected_direction_deg)
        & (stimulus_dataset.arg_df["intensity"] == intensity)
        & (stimulus_dataset.arg_df["width"] == 80)
        & (stimulus_dataset.arg_df["speed"] == 19)
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one trace row in FlyVis stimulus dataset for {cell_type}, "
            f"found {len(matches)}"
        )

    sample_index = int(matches.index[0])
    if sample_index >= selected.sizes.get("sample", 0):
        raise RuntimeError(
            f"FlyVis response sample index {sample_index} is outside the response dataset"
        )

    trace = selected.isel(sample=sample_index).mean(dim="neuron").values
    time_ms = responses["time"].values.astype(float) * 1000.0
    if len(time_ms) < 2:
        raise RuntimeError("FlyVis response trace must contain at least two frames")

    return FlyVisResponseAdapter.extract(
        [float(value) for value in trace.tolist()],
        cell_type=cell_type,
        start_ms=float(time_ms[0]),
        dt_ms=float(time_ms[1] - time_ms[0]),
        source_revision=FLYVIS_REVISION,
        model_artifact_sha256=checkpoint_sha256,
    )


def main() -> None:
    flyvis_version = str(getattr(flyvis, "__version__", ""))
    revision_token = FLYVIS_REVISION[:10]
    if flyvis_version != "1.2.0" and f"+g{revision_token}" not in flyvis_version:
        raise RuntimeError(
            "FlyVis package identity mismatch: "
            f"expected release {FLYVIS_RELEASE} or git revision token "
            f"{revision_token!r}, got {flyvis_version!r}"
        )

    flyvis_root = Path(flyvis.root_dir).resolve()
    archive_path = find_pretrained_archive(flyvis_root)
    archive_sha256 = sha256_file(archive_path)
    if archive_sha256 != PRETRAINED_ARCHIVE_SHA256:
        raise RuntimeError(
            "pretrained archive checksum mismatch: "
            f"expected {PRETRAINED_ARCHIVE_SHA256}, got {archive_sha256}"
        )

    network_dir = Path(flyvis.results_dir) / "flow" / "0000" / "000"
    network_view = NetworkView(network_dir)
    checkpoint_path = Path(network_view.get_checkpoint("best"))
    if not checkpoint_path.is_file():
        raise RuntimeError(f"best checkpoint not found: {checkpoint_path}")
    checkpoint_sha256 = sha256_file(checkpoint_path)

    dataset = MovingEdge(
        widths=[1],
        offsets=(-10, 11),
        intensities=[0, 1],
        speeds=[19],
        height=80,
        dt=1 / 200,
        device="cpu",
        post_pad_mode="continue",
        t_pre=1.0,
        t_post=1.0,
        angles=ANGLES_DEG,
    )
    response_dataset = network_view.moving_edge_responses(
        dataset=dataset,
        batch_size=4,
    )
    official_preferred_directions = preferred_direction(response_dataset)

    observed = []
    trace_receipts = {}
    for cell_type, expected_direction_deg in EXPECTED_PREFERRED_DIRECTION_DEG.items():
        intensity = TARGET_INTENSITY[cell_type]
        observed_direction_deg, peak_values = summarize_direction(
            response_dataset,
            cell_type,
            intensity,
        )
        manual_angular_error_deg = angular_distance_deg(
            observed_direction_deg, expected_direction_deg
        )
        official_direction_rad = official_preferred_directions.custom.where(
            cell_type=cell_type, intensity=intensity
        ).item()
        official_direction_deg = float(np.degrees(official_direction_rad) % 360.0)
        official_angular_error_deg = angular_distance_deg(
            official_direction_deg, expected_direction_deg
        )
        extraction_crosscheck_error_deg = angular_distance_deg(
            observed_direction_deg, official_direction_deg
        )
        direction_observation = FlyVisDirectionObservation(
            cell_type=cell_type,
            intensity=intensity,
            expected_direction_deg=expected_direction_deg,
            observed_direction_deg=official_direction_deg,
            angular_error_deg=official_angular_error_deg,
        )
        validate_direction_observation(direction_observation)

        signal = extract_trace_signal(
            response_dataset,
            dataset,
            cell_type,
            intensity,
            expected_direction_deg,
            checkpoint_sha256,
        )
        trace_receipts[cell_type] = {
            "start_ms": signal.start_ms,
            "dt_ms": signal.dt_ms,
            "frame_count": len(signal.responses),
            "response_sha256": signal.response_sha256,
            "source_sha256": signal.source_sha256,
        }
        observed.append(
            {
                "cell_type": cell_type,
                "intensity": intensity,
                "expected_direction_deg": expected_direction_deg,
                "manual_peak_direction_deg": observed_direction_deg,
                "manual_peak_angular_error_deg": manual_angular_error_deg,
                "official_preferred_direction_deg": official_direction_deg,
                "official_angular_error_deg": official_angular_error_deg,
                "manual_vs_official_error_deg": extraction_crosscheck_error_deg,
                "peak_values": peak_values,
            }
        )

    receipt = {
        "schema_version": 1,
        "status": "observed_success",
        "observed_at": datetime.now(UTC).isoformat(),
        "dlf_commit": os.environ.get("GITHUB_SHA", "local"),
        "flyvis": {
            "release": FLYVIS_RELEASE,
            "revision": FLYVIS_REVISION,
            "pretrained_archive": str(archive_path.relative_to(flyvis_root)),
            "pretrained_archive_sha256": archive_sha256,
            "network_path": str(network_dir.relative_to(flyvis_root)),
            "best_checkpoint": str(checkpoint_path.relative_to(flyvis_root)),
            "best_checkpoint_sha256": checkpoint_sha256,
        },
        "protocol": {
            "stimulus": "MovingEdge",
            "angles_deg": ANGLES_DEG,
            "intensities": [0, 1],
            "target_intensity": TARGET_INTENSITY,
            "rendered_edge_width": 80,
            "speed": 19,
            "offsets": [-10, 11],
            "dt_s": 1 / 200,
            "direction_tolerance_deg": DEFAULT_DIRECTION_TOLERANCE_DEG,
        },
        "direction_observations": observed,
        "continuous_trace_fingerprints": trace_receipts,
        "scientific_boundary": {
            "continuous_model_response": True,
            "spike_conversion": False,
            "exact_fafb_root_identity": False,
            "camera_activity_source": False,
            "code_hand_capability_mapping": False,
            "biological_control_claim": False,
        },
        "final_assertion": (
            "flyvis_model -> continuous_response -> "
            "direction_evidence -> provenance_adapter PASS"
        ),
    }

    print("FLYVIS_RECEIPT_BEGIN")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print("FLYVIS_RECEIPT_END")


if __name__ == "__main__":
    main()
