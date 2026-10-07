import struct

import pytest

from dlf_flywire.recovery import decode_skeleton


def _payload(vertices, edges, radii):
    blob = struct.pack("<II", len(vertices), len(edges))
    blob += b"".join(struct.pack("<fff", *vertex) for vertex in vertices)
    blob += b"".join(struct.pack("<II", *edge) for edge in edges)
    blob += b"".join(struct.pack("<f", radius) for radius in radii)
    return blob


def _info(transform=None):
    return {
        "@type": "neuroglancer_skeletons",
        "transform": transform or [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
        "vertex_attributes": [
            {"id": "radius", "data_type": "float32", "num_components": 1}
        ],
    }


def test_decode_standard_precomputed_skeleton():
    payload = _payload(
        [(0, 0, 0), (1, 0, 0), (2, 0, 0)],
        [(1, 0), (1, 2)],
        [10, 2, 1],
    )
    rows = decode_skeleton(payload, _info())

    assert [row["parent"] for row in rows] == [2, -1, 2]
    assert [row["label"] for row in rows] == [6, 1, 6]
    assert [row["radius"] for row in rows] == [10, 2, 1]


def test_decode_applies_transform():
    payload = _payload(
        [(1, 2, 3)],
        [],
        [4],
    )
    rows = decode_skeleton(
        payload,
        _info([2, 0, 0, 1, 0, 3, 0, 2, 0, 0, 4, 3]),
    )

    assert rows[0]["x"] == 3
    assert rows[0]["y"] == 8
    assert rows[0]["z"] == 15


def test_decode_rejects_invalid_edge():
    payload = _payload([(0, 0, 0)], [(0, 2)], [1])
    with pytest.raises(ValueError, match="invalid vertex"):
        decode_skeleton(payload, _info())


def test_decode_rejects_disconnected_skeleton():
    payload = _payload(
        [(0, 0, 0), (1, 0, 0), (10, 0, 0), (11, 0, 0)],
        [(0, 1), (2, 3)],
        [1, 1, 1, 1],
    )
    with pytest.raises(ValueError, match="single tree"):
        decode_skeleton(payload, _info())


def test_decode_rejects_cycle():
    payload = _payload(
        [(0, 0, 0), (1, 0, 0), (0, 1, 0)],
        [(0, 1), (1, 2), (2, 0)],
        [1, 1, 1],
    )
    with pytest.raises(ValueError, match="single tree"):
        decode_skeleton(payload, _info())


def test_decode_rejects_trailing_bytes():
    payload = _payload([(0, 0, 0)], [], [1]) + b"junk"
    with pytest.raises(ValueError, match="trailing"):
        decode_skeleton(payload, _info())
