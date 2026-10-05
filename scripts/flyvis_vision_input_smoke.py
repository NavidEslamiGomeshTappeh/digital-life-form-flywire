from __future__ import annotations

import json

from dlf_flywire.vision_input import VisionFrame, render_with_flyvis_boxeye


def main() -> None:
    width = height = 64
    pixels = bytes(
        (x + 3 * y) % 256
        for y in range(height)
        for x in range(width)
    )
    frame = VisionFrame.from_gray8(
        frame_index=0,
        width=width,
        height=height,
        pixels_gray8=pixels,
        captured_at_utc="2026-10-05T00:00:00+00:00",
    )
    rendered = render_with_flyvis_boxeye(frame)
    assert rendered.hexal_count == 721
    assert rendered.rendered_shape == (1, 1, 1, 721)
    print(json.dumps(
        {
            "status": "PASS",
            "source_pixel_sha256": rendered.source_pixel_sha256,
            "hexal_count": rendered.hexal_count,
            "rendered_shape": list(rendered.rendered_shape),
            "rendered_sha256": rendered.rendered_sha256,
        },
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
