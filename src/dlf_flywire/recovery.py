from __future__ import annotations

import argparse
import json
import struct
import urllib.error
import urllib.request
from pathlib import Path

from .constants import ROOTS
from .morphology import validate_swc_file

SKELETON_BASE_URL = {
    783: "https://flyem.mrc-lmb.cam.ac.uk/flyconnectome/flywire_skeletons_783",
}

DEFAULT_TIMEOUT = 60.0
USER_AGENT = "digital-life-form-flywire/1.0.1"


def _fetch(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc


def _validate_info(info: dict) -> list[dict]:
    if info.get("@type") != "neuroglancer_skeletons":
        raise ValueError("unsupported skeleton info @type")
    if "sharding" in info:
        raise ValueError("sharded Neuroglancer skeletons are not supported by V1 recovery")

    transform = info.get("transform")
    if (
        not isinstance(transform, list)
        or len(transform) != 12
        or not all(isinstance(v, (int, float)) for v in transform)
    ):
        raise ValueError("invalid Neuroglancer skeleton transform")

    attrs = info.get("vertex_attributes", [])
    if isinstance(attrs, dict):
        attrs = [attrs]
    if not isinstance(attrs, list):
        raise ValueError("invalid Neuroglancer vertex_attributes")

    normalized = []
    for attr in attrs:
        if not isinstance(attr, dict):
            raise ValueError("invalid Neuroglancer vertex attribute")
        if not all(k in attr for k in ("id", "data_type", "num_components")):
            raise ValueError("incomplete Neuroglancer vertex attribute")
        if not isinstance(attr["id"], str) or attr["num_components"] < 1:
            raise ValueError("invalid Neuroglancer vertex attribute definition")
        normalized.append(attr)
    return normalized


def _dtype_size(data_type: str) -> int:
    sizes = {
        "float32": 4,
        "int8": 1,
        "uint8": 1,
        "int16": 2,
        "uint16": 2,
        "int32": 4,
        "uint32": 4,
    }
    try:
        return sizes[data_type]
    except KeyError as exc:
        raise ValueError(f"unsupported Neuroglancer attribute type: {data_type}") from exc


def _decode_values(payload: bytes, offset: int, count: int, data_type: str) -> tuple[list, int]:
    formats = {
        "float32": "f",
        "int8": "b",
        "uint8": "B",
        "int16": "h",
        "uint16": "H",
        "int32": "i",
        "uint32": "I",
    }
    try:
        fmt = formats[data_type]
    except KeyError as exc:
        raise ValueError(f"unsupported Neuroglancer attribute type: {data_type}") from exc
    size = _dtype_size(data_type) * count
    end = offset + size
    if end > len(payload):
        raise ValueError("truncated Neuroglancer attribute data")
    values = list(struct.iter_unpack(f"<{fmt}", payload[offset:end]))
    return [item[0] for item in values], end


def _orient_edges(edges: list[tuple[int, int]], num_vertices: int) -> list[int]:
    if not edges:
        if num_vertices == 1:
            return [-1]
        raise ValueError("skeleton has multiple vertices but no edges")

    root_hints: list[int] | None = None
    for child_column in (0, 1):
        children = [edge[child_column] for edge in edges]
        if len(set(children)) == len(children):
            hinted = [i for i in range(num_vertices) if i not in set(children)]
            root_hints = hinted or None
            if root_hints:
                break

    adjacency: list[list[int]] = [[] for _ in range(num_vertices)]
    for a, b in edges:
        if a == b:
            raise ValueError("skeleton contains a self-edge")
        if not (0 <= a < num_vertices and 0 <= b < num_vertices):
            raise ValueError("skeleton edge references an invalid vertex")
        adjacency[a].append(b)
        adjacency[b].append(a)

    for neighbors in adjacency:
        neighbors.sort()

    parents = [-2] * num_vertices
    seeds = root_hints[:] if root_hints else []
    seeds.extend(i for i in range(num_vertices) if i not in seeds)

    for seed in seeds:
        if parents[seed] != -2:
            continue
        parents[seed] = -1
        stack = [seed]
        while stack:
            current = stack.pop()
            for neighbor in reversed(adjacency[current]):
                if parents[neighbor] != -2:
                    continue
                parents[neighbor] = current
                stack.append(neighbor)

    return parents


def decode_skeleton(payload: bytes, info: dict) -> list[dict]:
    if len(payload) < 8:
        raise ValueError("truncated Neuroglancer skeleton header")

    attrs = _validate_info(info)
    num_vertices, num_edges = struct.unpack_from("<II", payload, 0)
    offset = 8

    vertex_bytes = 12 * num_vertices
    edge_bytes = 8 * num_edges
    if offset + vertex_bytes + edge_bytes > len(payload):
        raise ValueError("truncated Neuroglancer skeleton geometry")

    vertex_data = payload[offset : offset + vertex_bytes]
    vertices = [item for item in struct.iter_unpack("<fff", vertex_data)]
    offset += vertex_bytes

    edge_data = payload[offset : offset + edge_bytes]
    edges = [item for item in struct.iter_unpack("<II", edge_data)]
    offset += edge_bytes

    attributes: dict[str, list] = {}
    for attr in attrs:
        count = num_vertices * int(attr["num_components"])
        values, offset = _decode_values(payload, offset, count, attr["data_type"])
        if int(attr["num_components"]) == 1:
            attributes[attr["id"]] = values
        else:
            width = int(attr["num_components"])
            attributes[attr["id"]] = [
                values[i : i + width] for i in range(0, len(values), width)
            ]

    if offset != len(payload):
        raise ValueError("unexpected trailing bytes in Neuroglancer skeleton payload")

    radius = attributes.get("radius")
    if radius is None or len(radius) != num_vertices:
        raise ValueError("V1 recovery requires a scalar radius vertex attribute")

    transform = info["transform"]
    transformed = []
    for x, y, z in vertices:
        tx = transform[0] * x + transform[1] * y + transform[2] * z + transform[3]
        ty = transform[4] * x + transform[5] * y + transform[6] * z + transform[7]
        tz = transform[8] * x + transform[9] * y + transform[10] * z + transform[11]
        transformed.append((tx, ty, tz))

    parents = _orient_edges(edges, num_vertices)
    child_counts = [0] * num_vertices
    for parent in parents:
        if parent >= 0:
            child_counts[parent] += 1

    rows = []
    for index, (x, y, z) in enumerate(transformed):
        label = 1 if parents[index] == -1 else 5 if child_counts[index] > 1 else 6 if child_counts[index] == 0 else 0
        rows.append(
            {
                "point_id": index + 1,
                "label": label,
                "x": x,
                "y": y,
                "z": z,
                "radius": radius[index],
                "parent": -1 if parents[index] == -1 else parents[index] + 1,
            }
        )
    return rows


def write_swc(path: Path, root_id: int, rows: list[dict]) -> None:
    lines = [
        "# SWC format file",
        "# Neuroglancer precomputed skeleton recovered directly by dlf-flywire",
        f'# Meta: {json.dumps({"id": str(root_id), "name": "skeleton", "units": "1 nanometer"}, separators=(", ", ": "))}',
        "# PointNo Label X Y Z Radius Parent",
        "# Labels:",
        "# 0 = undefined, 1 = soma/root, 5 = fork point, 6 = end point",
    ]
    for row in rows:
        lines.append(
            "{} {} {} {} {} {} {}".format(
                row["point_id"],
                row["label"],
                repr(float(row["x"])),
                repr(float(row["y"])),
                repr(float(row["z"])),
                repr(float(row["radius"])),
                row["parent"],
            )
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temp.replace(path)


def recover_one(name: str, root_id: int, output: Path, timeout: float) -> dict:
    base_url = SKELETON_BASE_URL[783]
    info = json.loads(_fetch(f"{base_url}/info", timeout=timeout).decode("utf-8"))
    payload = _fetch(f"{base_url}/{root_id}", timeout=timeout)

    rows = decode_skeleton(payload, info)
    output_path = output / f"{name}.swc"
    write_swc(output_path, root_id, rows)

    report = validate_swc_file(output_path, str(root_id))
    if not report.get("valid") or report.get("node_count") != len(rows):
        raise RuntimeError(f"{name}: recovered SWC failed structural validation: {report}")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Recover exact FlyWire FAFB v783 skeletons directly from the public Neuroglancer endpoint."
    )
    parser.add_argument("--dataset", type=int, default=783)
    parser.add_argument("--output", type=Path, default=Path("data/morphology"))
    parser.add_argument("--root", action="append", choices=list(ROOTS))
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = parser.parse_args(argv)

    if args.dataset != 783:
        raise SystemExit("Version 1.0.1 recovery supports the FAFB v783 skeleton endpoint only.")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")

    for name in args.root or list(ROOTS):
        root_id = ROOTS[name]
        report = recover_one(name, root_id, args.output, args.timeout)
        print(f"PASS {name} root={root_id} nodes={report['node_count']} sha256={report['sha256']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
