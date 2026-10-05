from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from dlf_flywire.vision_input import (
    VisionFrame,
    build_capture_receipt,
    render_with_flyvis_boxeye,
)

SOURCE_URL = "https://upload.wikimedia.org/wikipedia/commons/0/01/Street_city.jpg"
OUT = Path(os.environ.get("VISION_SAMPLE_OUT", "artifacts/vision-real-sample"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source_path = OUT / "source.jpg"
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
        source_bytes = response.read()
    source_path.write_bytes(source_bytes)
    source_sha256 = sha256_bytes(source_bytes)

    captured_at = datetime.now(UTC).isoformat()
    decoded = cv2.imdecode(np.frombuffer(source_bytes, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if decoded is None:
        raise RuntimeError("OpenCV could not decode the real sample image")

    max_side = 320
    scale = min(1.0, max_side / max(decoded.shape))
    if scale < 1.0:
        decoded = cv2.resize(
            decoded,
            (
                max(1, round(decoded.shape[1] * scale)),
                max(1, round(decoded.shape[0] * scale)),
            ),
            interpolation=cv2.INTER_AREA,
        )

    height, width = decoded.shape[:2]
    frame = VisionFrame.from_gray8(
        frame_index=0,
        width=width,
        height=height,
        pixels_gray8=decoded.tobytes(),
        captured_at_utc=captured_at,
    )
    frame_path = OUT / "frame-000000.pgm"
    frame_file_sha256 = frame.write_pgm(frame_path)
    capture_receipt = build_capture_receipt(
        (frame,),
        source_kind="real-sample/opencv-image",
        source_locator=SOURCE_URL,
        artifact_paths=(str(frame_path),),
    )
    receipt_path = OUT / "capture-receipt.json"
    receipt_sha256 = capture_receipt.write(receipt_path)

    boxeye = render_with_flyvis_boxeye(frame)
    boxeye_values_path = OUT / "boxeye-721-values.json"
    boxeye_values = list(boxeye.rendered_values)
    boxeye_values_path.write_text(
        json.dumps(boxeye_values, separators=(",", ":")),
        encoding="utf-8",
    )
    boxeye_values_sha256 = sha256_bytes(boxeye_values_path.read_bytes())
    if len(boxeye_values) != 721:
        raise RuntimeError(f"BoxEye returned {len(boxeye_values)} values, expected 721")

    receipt = {
        "schema_version": 2,
        "status": "observed_success",
        "source": {
            "url": SOURCE_URL,
            "source_file_sha256": source_sha256,
            "source_bytes": len(source_bytes),
        },
        "capture": capture_receipt.to_dict(),
        "artifact": {
            "pgm_sha256": frame_file_sha256,
            "receipt_sha256": receipt_sha256,
            "boxeye_values_path": str(boxeye_values_path),
            "boxeye_values_sha256": boxeye_values_sha256,
        },
        "boxeye": {
            "hexal_count": boxeye.hexal_count,
            "rendered_shape": list(boxeye.rendered_shape),
            "rendered_sha256": boxeye.rendered_sha256,
            "source_pixel_sha256": boxeye.source_pixel_sha256,
            "values_count": len(boxeye_values),
            "values": boxeye_values,
        },
        "scientific_boundary": {
            "real_image_input": True,
            "physical_camera_device": False,
            "continuous_flyvis_contract": True,
            "spike_conversion": False,
            "exact_fafb_root_activity": False,
            "biological_control_claim": False,
        },
    }
    final_path = OUT / "boxeye-receipt.json"
    final_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print("REAL_VISION_SAMPLE_RECEIPT_BEGIN")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    print("REAL_VISION_SAMPLE_RECEIPT_END")


if __name__ == "__main__":
    main()
