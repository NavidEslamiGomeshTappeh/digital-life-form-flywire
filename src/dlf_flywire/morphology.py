from __future__ import annotations
import hashlib, math
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Node:
    point_id: int
    label: int
    x: float
    y: float
    z: float
    radius: float
    parent: int
    @property
    def point(self) -> tuple[float, float, float]:
        return self.x, self.y, self.z

def parse_swc(path: Path) -> dict[int, Node]:
    nodes: dict[int, Node] = {}
    errors: list[int] = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 7:
                errors.append(lineno)
                continue
            try:
                node = Node(int(parts[0]), int(parts[1]), float(parts[2]), float(parts[3]),
                            float(parts[4]), float(parts[5]), int(parts[6]))
            except ValueError:
                errors.append(lineno)
                continue
            if node.point_id in nodes:
                raise ValueError(f"duplicate SWC node id {node.point_id}")
            nodes[node.point_id] = node
    if errors:
        raise ValueError(f"malformed SWC lines: {errors}")
    return nodes

def validate_swc(nodes: dict[int, Node], expected_root_id: str) -> dict:
    roots = [n.point_id for n in nodes.values() if n.parent == -1]
    missing = sorted({n.parent for n in nodes.values() if n.parent != -1 and n.parent not in nodes})
    finite = all(math.isfinite(v) for n in nodes.values() for v in (n.x,n.y,n.z,n.radius))
    return {"requested_root_id": str(expected_root_id), "node_count": len(nodes),
            "structural_root_count": len(roots), "missing_parent_refs": missing,
            "finite_geometry": finite, "root_node_id": roots[0] if len(roots)==1 else None,
            "valid": bool(nodes) and len(roots)==1 and not missing and finite}

def validate_swc_file(path: Path, expected_root_id: str) -> dict:
    try:
        report = validate_swc(parse_swc(path), expected_root_id)
    except (OSError, ValueError) as exc:
        return {"requested_root_id": str(expected_root_id), "valid": False,
                "error": f"{type(exc).__name__}: {exc}"}
    report["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return report

def map_point_to_segments(point: tuple[float,float,float], nodes: dict[int,Node]) -> dict:
    best = None
    for node in nodes.values():
        if node.parent == -1:
            continue
        parent = nodes[node.parent]
        vx,vy,vz = node.x-parent.x,node.y-parent.y,node.z-parent.z
        wx,wy,wz = point[0]-parent.x,point[1]-parent.y,point[2]-parent.z
        vv = vx*vx+vy*vy+vz*vz
        t = 0.0 if vv == 0 else max(0.0,min(1.0,(wx*vx+wy*vy+wz*vz)/vv))
        q=(parent.x+t*vx,parent.y+t*vy,parent.z+t*vz)
        d=math.dist(point,q)
        cand=(d,parent.point_id,node.point_id,t,q)
        if best is None or cand < best:
            best=cand
    if best is None:
        raise ValueError("SWC has no usable segments")
    d,start,end,t,q=best
    return {"nearest_segment_start_node_id":start,"nearest_segment_end_node_id":end,
            "segment_fraction":t,"nearest_point":q,"centerline_distance_nm":d}
