# V263 — coordinate-frame audit

V263 tests whether the four reconstructed PP3 root coordinates and the four Point_data root coordinates can be related by one common rigid or similarity transform.

Result: no common rigid/similarity transform fits all four roots. Intra-type pair distances are much closer than cross-type separations, so the mismatch cannot safely be repaired with one global translation, rotation, or uniform scale.

This keeps the provenance boundary explicit: no guessed transform is written into project data.

Observed values from the four-root audit:

- T4a-T4c: 11.1393 µm vs 11.1839 µm.
- T5a-T5c: 7.2131 µm vs 5.5542 µm.
- Cross-type differences are 148.6–157.5 µm.
- Best common rigid transform RMSE: 103.76 µm.
- Best common similarity transform RMSE: 115.55 µm (scale 2.7061).
- Maximum pairwise relative difference: 0.6547.
