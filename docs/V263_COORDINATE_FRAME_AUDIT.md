# V263 — coordinate-frame audit

V263 tests whether the four reconstructed PP3 root coordinates and the four Point_data root coordinates can be related by one common rigid or similarity transform.

Result: no common rigid/similarity transform fits all four roots. Intra-type pair distances are much closer than cross-type separations, so the mismatch cannot safely be repaired with one global translation, rotation, or uniform scale.

This keeps the provenance boundary explicit: no guessed transform is written into project data.
