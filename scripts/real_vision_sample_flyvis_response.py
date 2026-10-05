from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import flyvis
import numpy as np
import torch
from flyvis import NetworkView
from flyvis.utils.activity_utils import LayerActivity


SOURCE_SHA256 = "33e32880c36d3cd589bb620498ced8bf77d5796d32141a297624039d37355707"
SOURCE_BYTES = 425857
FLYVIS_REVISION = "92b3845cc426dd309a1a0e1b3890156c42e14021"
OUT = Path(os.environ.get("VISION_FLYVIS_OUT", "artifacts/vision-real-sample"))
CELL_TYPES = ("T4a", "T4c", "T5a", "T5c")
DT_S = 1 / 100
N_FRAMES = 20


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def main() -> None:
    source_path = OUT / "source.jpg"
    values_path = OUT / "boxeye-721-values.json"
    receipt_path = OUT / "boxeye-receipt.json"
    if not source_path.is_file():
        raise RuntimeError(f"missing upstream real-image artifact: {source_path}")
    if not values_path.is_file():
        raise RuntimeError(f"missing upstream BoxEye values: {values_path}")
    if not receipt_path.is_file():
        raise RuntimeError(f"missing upstream BoxEye receipt: {receipt_path}")

    source_bytes = source_path.read_bytes()
    source_sha256 = sha256_bytes(source_bytes)
    if len(source_bytes) != SOURCE_BYTES or source_sha256 != SOURCE_SHA256:
        raise RuntimeError(
            "upstream source identity mismatch: "
            f"bytes={len(source_bytes)} sha256={source_sha256}"
        )

    upstream = json.loads(receipt_path.read_text(encoding="utf-8"))
    if upstream["source"]["source_file_sha256"] != SOURCE_SHA256:
        raise RuntimeError("upstream receipt source SHA does not match pinned source")
    if upstream["boxeye"]["hexal_count"] != 721:
        raise RuntimeError("upstream receipt does not contain the expected 721 BoxEye outputs")
    if upstream["scientific_boundary"]["physical_camera_device"]:
        raise RuntimeError("upstream receipt incorrectly claims a physical camera")
    if upstream["scientific_boundary"]["spike_conversion"]:
        raise RuntimeError("upstream receipt incorrectly claims spike conversion")

    boxeye_values = np.asarray(
        json.loads(values_path.read_text(encoding="utf-8")),
        dtype=np.float32,
    )
    if boxeye_values.shape != (721,):
        raise RuntimeError(f"expected 721 BoxEye values, got {boxeye_values.shape}")

    flyvis_version = str(getattr(flyvis, "__version__", ""))
    if not (flyvis_version == "1.2.0" or f"+g{FLYVIS_REVISION[:9]}" in flyvis_version):
        raise RuntimeError(
            f"FlyVis package identity mismatch: got {flyvis_version!r}"
        )

    flyvis_root = Path(flyvis.root_dir).resolve()
    network_dir = Path(flyvis.results_dir) / "flow" / "0000" / "000"
    network_view = NetworkView(network_dir)
    checkpoint_path = Path(network_view.get_checkpoint("best"))
    if not checkpoint_path.is_file():
        raise RuntimeError(f"best checkpoint not found: {checkpoint_path}")
    checkpoint_sha256 = sha256_file(checkpoint_path)

    movie_input = torch.from_numpy(
        np.repeat(boxeye_values.reshape(1, 721), N_FRAMES, axis=0)
    ).unsqueeze(1)
    network = network_view.init_network()
    stationary_state = network.fade_in_state(
        1.0,
        DT_S,
        movie_input[:1],
    )
    responses = network.simulate(
        movie_input[None],
        DT_S,
        initial_state=stationary_state,
    ).detach().cpu()

    if tuple(responses.shape) != (1, N_FRAMES, network.n_nodes):
        raise RuntimeError(
            f"unexpected FlyVis response shape {tuple(responses.shape)}; "
            f"expected (1, {N_FRAMES}, {network.connectome.n_nodes})"
        )

    response_np = responses.numpy()
    response_path = OUT / "flyvis-real-image-response.npy"
    np.save(response_path, response_np, allow_pickle=False)
    response_sha256 = sha256_file(response_path)

    activity = LayerActivity(responses, network.connectome, keepref=True)
    central_traces: dict[str, list[float]] = {}
    for cell_type in CELL_TYPES:
        trace = activity.central[cell_type].squeeze().numpy()
        if trace.shape != (N_FRAMES,):
            raise RuntimeError(
                f"unexpected central trace shape for {cell_type}: {trace.shape}"
            )
        if not np.isfinite(trace).all():
            raise RuntimeError(f"non-finite FlyVis response for {cell_type}")
        central_traces[cell_type] = [float(value) for value in trace.tolist()]

    trace_blob = json.dumps(
        central_traces,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    central_traces_sha256 = sha256_bytes(trace_blob)

    receipt = {
        "schema_version": 1,
        "status": "observed_success",
        "observed_at_utc": datetime.now(UTC).isoformat(),
        "input_chain": {
            "real_image_source_sha256": source_sha256,
            "real_image_source_bytes": len(source_bytes),
            "upstream_boxeye_receipt_sha256": upstream["artifact"]["receipt_sha256"],
            "boxeye_values_sha256": upstream["artifact"]["boxeye_values_sha256"],
            "boxeye_hexal_count": upstream["boxeye"]["hexal_count"],
        },
        "flyvis": {
            "release": "1.2.0",
            "revision": FLYVIS_REVISION,
            "network_path": str(network_dir.relative_to(flyvis_root)),
            "best_checkpoint": str(checkpoint_path.relative_to(flyvis_root)),
            "best_checkpoint_sha256": checkpoint_sha256,
        },
        "protocol": {
            "input_kind": "single real public image repeated as a stationary movie",
            "frame_count": N_FRAMES,
            "dt_s": DT_S,
            "movie_shape": list(movie_input.shape),
            "response_shape": list(response_np.shape),
        },
        "artifact": {
            "full_response_path": str(response_path),
            "full_response_sha256": response_sha256,
            "central_traces_sha256": central_traces_sha256,
        },
        "central_traces": central_traces,
        "scientific_boundary": {
            "real_image_input": True,
            "physical_camera_device": False,
            "flyvis_continuous_model_response": True,
            "spike_conversion": False,
            "exact_fafb_root_activity": False,
            "biological_control_claim": False,
        },
    }

    final_path = OUT / "flyvis-real-image-response-receipt.json"
    final_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print("REAL_VISION_FLYVIS_RESPONSE_RECEIPT_BEGIN")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print("REAL_VISION_FLYVIS_RESPONSE_RECEIPT_END")


if __name__ == "__main__":
    main()
