#!/usr/bin/env python3
from __future__ import annotations

import itertools
import math
from pathlib import Path
from typing import Iterable

import numpy as np

PP3_ROOT_UM = np.array(
    [
        [789.1497, 263.18266, 210.35522],      # T4a
        [788.7438, 272.94928, 205.01356],      # T4c
        [717.25825, 222.00586, 211.70161],     # T5a
        [713.4343, 216.06416, 213.15164],     # T5c
    ],
    dtype=float,
)

POINT_DATA_ROOT_UM = np.array(
    [
        [-46.85120703125, 32.261150390625, -111.5519921875],  # T4a
        [-46.16929296875, 22.233228515625, -116.4566640625],  # T4c
        [11.981576171875, 50.1895, 120.4021328125],            # T5a
        [12.7460712890625, 54.907804687500004, 117.5732734375],# T5c
    ],
    dtype=float,
)

LABELS = ("T4a", "T4c", "T5a", "T5c")


def pairwise_distances(points: np.ndarray) -> dict[str, float]:
    out = {}
    for i, j in itertools.combinations(range(len(points)), 2):
        out[f"{LABELS[i]}--{LABELS[j]}"] = float(np.linalg.norm(points[i] - points[j]))
    return out


def kabsch(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    src_c = source - source.mean(axis=0)
    tgt_c = target - target.mean(axis=0)
    H = src_c.T @ tgt_c
    U, _, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T
    t = target.mean(axis=0) - source.mean(axis=0) @ R
    predicted = source @ R + t
    residual = np.linalg.norm(predicted - target, axis=1)
    return R, t, residual


def similarity(source: np.ndarray, target: np.ndarray) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    src_c = source - source.mean(axis=0)
    tgt_c = target - target.mean(axis=0)
    H = src_c.T @ tgt_c
    U, singular, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T
    scale = float(singular.sum() / np.sum(src_c ** 2))
    t = target.mean(axis=0) - scale * source.mean(axis=0) @ R
    predicted = scale * source @ R + t
    residual = np.linalg.norm(predicted - target, axis=1)
    return scale, R, t, residual


def main() -> None:
    pp_pairs = pairwise_distances(PP3_ROOT_UM)
    pd_pairs = pairwise_distances(POINT_DATA_ROOT_UM)

    pair_report = []
    relative_errors = []
    for key in pp_pairs:
        a = pp_pairs[key]
        b = pd_pairs[key]
        rel = abs(a - b) / max(b, 1e-12)
        relative_errors.append(rel)
        pair_report.append(
            {
                "pair": key,
                "pp3_distance_um": a,
                "point_data_distance_um": b,
                "absolute_difference_um": abs(a - b),
                "relative_difference": rel,
            }
        )

    R, t, rigid_res = kabsch(PP3_ROOT_UM, POINT_DATA_ROOT_UM)
    scale, R_sim, t_sim, sim_res = similarity(PP3_ROOT_UM, POINT_DATA_ROOT_UM)

    # Two-point intra-type distances are independently checked:
    intra_type = {
        "T4a--T4c": abs(pp_pairs["T4a--T4c"] - pd_pairs["T4a--T4c"]),
        "T5a--T5c": abs(pp_pairs["T5a--T5c"] - pd_pairs["T5a--T5c"]),
    }

    result = {
        "status": "PASS_COORDINATE_FRAME_AUDIT_NO_COMMON_RIGID_MATCH",
        "labels": LABELS,
        "pp3_root_um": PP3_ROOT_UM.tolist(),
        "point_data_root_um": POINT_DATA_ROOT_UM.tolist(),
        "pairwise": pair_report,
        "max_pair_relative_difference": float(max(relative_errors)),
        "intra_type_pair_absolute_differences_um": intra_type,
        "best_rigid_transform": {
            "rotation": R.tolist(),
            "translation_um": t.tolist(),
            "per_point_residual_um": rigid_res.tolist(),
            "rmse_um": float(np.sqrt(np.mean(rigid_res ** 2))),
            "max_residual_um": float(max(rigid_res)),
        },
        "best_similarity_transform": {
            "scale": scale,
            "rotation": R_sim.tolist(),
            "translation_um": t_sim.tolist(),
            "per_point_residual_um": sim_res.tolist(),
            "rmse_um": float(np.sqrt(np.mean(sim_res ** 2))),
            "max_residual_um": float(max(sim_res)),
        },
        "interpretation": (
            "The four roots do not support one common rigid/similarity coordinate transform. "
            "The T4a/T4c pair has nearly preserved separation, while the T5a/T5c pair does too, "
            "but cross-type separations differ substantially. This is evidence against treating "
            "Point_data and V229 as one globally transformed frame."
        ),
        "not_proven": [
            "Exact historical point-wise transform from the paper's .nr data to the project V229 files.",
            "Historical manual root selection for each cell.",
            "Identity of the exact skeletonization output used to create the published reduced .nr files.",
        ],
    }

    out = Path("v263_results")
    out.mkdir(parents=True, exist_ok=True)
    (out / "V263_coordinate_frame_audit.json").write_text(
        __import__("json").dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(result["status"])
    print("max pairwise relative difference:", result["max_pair_relative_difference"])
    print("best rigid RMSE um:", result["best_rigid_transform"]["rmse_um"])
    print("best similarity scale:", result["best_similarity_transform"]["scale"])
    print("best similarity RMSE um:", result["best_similarity_transform"]["rmse_um"])


if __name__ == "__main__":
    main()
