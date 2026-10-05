from __future__ import annotations  # noqa: I001

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from .vision_input import OpenCVCameraSource, build_capture_receipt, render_with_flyvis_boxeye


CELL_TYPES = ("T4a", "T4c", "T5a", "T5c")
FLYVIS_RELEASE = "1.2.0"
FLYVIS_REVISION = "92b3845cc426dd309a1a0e1b3890156c42e14021"


class CameraFlyVisError(RuntimeError):
    """Raised when the physical-camera -> FlyVis pipeline cannot complete."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def run_camera_to_flyvis(
    *,
    device_index: int,
    frame_count: int,
    output: str | Path,
    width: int | None = None,
    height: int | None = None,
    per_frame_timeout_s: float = 5.0,
    dt_s: float = 1 / 100,
) -> dict[str, object]:
    if frame_count <= 0:
        raise CameraFlyVisError("frame_count must be positive")
    if dt_s <= 0:
        raise CameraFlyVisError("dt_s must be positive")

    try:
        import flyvis
        import numpy as np
        import torch
        from flyvis import NetworkView
        from flyvis.utils.activity_utils import LayerActivity
    except ImportError as exc:
        raise CameraFlyVisError(
            "FlyVis, PyTorch, and their runtime dependencies are required; "
            "install the pinned FlyVis environment first"
        ) from exc

    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    frame_dir = output_path / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)

    frames = OpenCVCameraSource(
        device_index=device_index,
        width=width,
        height=height,
        per_frame_timeout_s=per_frame_timeout_s,
    ).capture(frame_count)

    artifact_paths: list[str] = []
    for frame in frames:
        frame_path = frame_dir / f"frame-{frame.frame_index:06d}.pgm"
        frame.write_pgm(frame_path)
        artifact_paths.append(frame_path.as_posix())

    capture_receipt = build_capture_receipt(
        frames,
        source_kind="camera/opencv",
        source_locator=f"device-index:{device_index}",
        artifact_paths=artifact_paths,
    )
    capture_receipt_path = output_path / "capture-receipt.json"
    capture_receipt_sha256 = capture_receipt.write(capture_receipt_path)

    rendered = [render_with_flyvis_boxeye(frame) for frame in frames]
    if not rendered:
        raise CameraFlyVisError("camera returned no frames")
    if any(item.hexal_count != 721 for item in rendered):
        raise CameraFlyVisError("FlyVis BoxEye did not return 721 receptors for every frame")
    if any(item.rendered_shape != (1, 1, 1, 721) for item in rendered):
        raise CameraFlyVisError("unexpected BoxEye tensor shape")

    movie_input_np = np.asarray(
        [
            np.asarray(item.rendered_values, dtype=np.float32).reshape(1, 721)
            for item in rendered
        ],
        dtype=np.float32,
    )
    movie_input = torch.from_numpy(movie_input_np).to(flyvis.device)
    network_root = Path(flyvis.results_dir) / "flow" / "0000" / "000"
    network_view = NetworkView(network_root)
    checkpoint_path = Path(network_view.get_checkpoint("best"))
    if not checkpoint_path.is_file():
        raise CameraFlyVisError(f"FlyVis best checkpoint not found: {checkpoint_path}")

    network = network_view.init_network()
    stationary_state = network.fade_in_state(1.0, dt_s, movie_input[:1])
    responses = network.simulate(
        movie_input[None],
        dt_s,
        initial_state=stationary_state,
    ).detach().cpu()
    expected_shape = (1, len(frames), network.n_nodes)
    if tuple(responses.shape) != expected_shape:
        raise CameraFlyVisError(
            f"unexpected FlyVis response shape {tuple(responses.shape)}; "
            f"expected {expected_shape}"
        )

    response_np = responses.numpy()
    response_path = output_path / "flyvis-response.npy"
    np.save(response_path, response_np, allow_pickle=False)

    activity = LayerActivity(responses, network.connectome, keepref=True)
    central_traces: dict[str, list[float]] = {}
    for cell_type in CELL_TYPES:
        trace = activity.central[cell_type].squeeze().numpy()
        if trace.shape != (len(frames),):
            raise CameraFlyVisError(
                f"unexpected central trace shape for {cell_type}: {trace.shape}"
            )
        if not np.isfinite(trace).all():
            raise CameraFlyVisError(f"non-finite response for {cell_type}")
        central_traces[cell_type] = [float(value) for value in trace.tolist()]

    traces_sha256 = _sha256_bytes(
        json.dumps(
            central_traces,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )

    receipt = {
        "schema_version": 1,
        "status": "observed_success",
        "observed_at_utc": datetime.now(UTC).isoformat(),
        "physical_source": {
            "device_index": device_index,
            "frame_count": len(frames),
            "capture_receipt_sha256": capture_receipt_sha256,
        },
        "flyvis": {
            "release": FLYVIS_RELEASE,
            "revision": FLYVIS_REVISION,
            "network_path": str(network_root),
            "best_checkpoint": str(checkpoint_path),
            "best_checkpoint_sha256": _sha256_file(checkpoint_path),
        },
        "input": {
            "boxeye_hexal_count": 721,
            "movie_shape": list(movie_input.shape),
            "frame_pixel_sha256": [frame.pixels_sha256 for frame in frames],
            "boxeye_rendered_sha256": [item.rendered_sha256 for item in rendered],
        },
        "response": {
            "shape": list(response_np.shape),
            "full_response_path": response_path.as_posix(),
            "full_response_sha256": _sha256_file(response_path),
            "central_traces_sha256": traces_sha256,
            "central_traces": central_traces,
        },
        "scientific_boundary": {
            "physical_camera_device": True,
            "real_camera_frames": True,
            "flyvis_continuous_model_response": True,
            "spike_conversion": False,
            "exact_fafb_root_activity": False,
            "biological_control_claim": False,
        },
    }

    receipt_path = output_path / "camera-flyvis-receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return receipt
