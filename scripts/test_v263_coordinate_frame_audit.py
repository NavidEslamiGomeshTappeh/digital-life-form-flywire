import itertools
import math
import numpy as np

from v263_coordinate_frame_audit import PP3_ROOT_UM, POINT_DATA_ROOT_UM, kabsch, similarity, pairwise_distances


def test_intra_type_separation_is_nearly_preserved():
    a = pairwise_distances(PP3_ROOT_UM)
    b = pairwise_distances(POINT_DATA_ROOT_UM)
    assert abs(a["T4a--T4c"] - b["T4a--T4c"]) < 0.1
    assert abs(a["T5a--T5c"] - b["T5a--T5c"]) < 2.0


def test_one_common_rigid_transform_does_not_fit():
    _, _, residual = kabsch(PP3_ROOT_UM, POINT_DATA_ROOT_UM)
    assert math.sqrt(float(np.mean(residual ** 2))) > 50.0


def test_one_common_similarity_transform_does_not_fit():
    _, _, _, residual = similarity(PP3_ROOT_UM, POINT_DATA_ROOT_UM)
    assert math.sqrt(float(np.mean(residual ** 2))) > 50.0


def test_cross_type_distances_are_not_globally_preserved():
    a = pairwise_distances(PP3_ROOT_UM)
    b = pairwise_distances(POINT_DATA_ROOT_UM)
    cross = [k for k in a if "T4" in k and "T5" in k]
    assert max(abs(a[k] - b[k]) for k in cross) > 100.0
