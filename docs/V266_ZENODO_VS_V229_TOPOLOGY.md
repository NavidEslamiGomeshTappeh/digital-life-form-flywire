# V266 — Zenodo Point_data versus exact V229 SWCs

The current official Zenodo record is 10.5281/zenodo.21876510, published August 10, 2026. The archive contains Data/point_data.pkl.

The current Zenodo Point_data bytes extracted by V264 are:
- size: 2,144,531 bytes
- SHA-256: 46772ccabc609ab0f7136854024e7665727ff0f58f53c69126ea3e641ce7f891
- Git blob: 0db640c17d820bed016da793648cf6b3f27f4738

The historical Git-tracked Point_data blob is different:
- Git blob: b85caf49f45677f2075f7b5f2c8830141cd96d02
- SHA-256: 76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f

The Git file history identifies fe9779d (December 9, 2025) as the last modification of Data/Point_data.pkl and 8700efd (August 10, 2026) as the commit that removed the tracked Data directory.

Current Zenodo Point_data anchors:

| Cell | Node | Leaves | Branches | Segment_count | Total_cable (um) |
|---|---:|---:|---:|---:|---:|
| T4a | 223 | 115 | 108 | 222 | 318.835752 |
| T4c | 206 | 109 | 97 | 205 | 301.209868 |
| T5a | 135 | 72 | 63 | 134 | 190.180084 |
| T5c | 153 | 80 | 73 | 152 | 195.601050 |

No exact subtree in any of the four full V229 SWCs has the published Leaf_count + Branch_count pair from current Zenodo Point_data.

The differences versus the automatically selected V258 subtrees are:

| Cell | V258 nodes | Point_data nodes | Node delta | V258 leaves | Point leaves | Leaf delta | V258 branches | Point branches | Branch delta | Cable delta (um) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| T4a | 213 | 223 | -10 | 109 | 115 | -6 | 104 | 108 | -4 | -19.7253 |
| T4c | 212 | 206 | +6 | 113 | 109 | +4 | 99 | 97 | +2 | -12.7584 |
| T5a | 181 | 135 | +46 | 94 | 72 | +22 | 87 | 63 | +24 | +75.0202 |
| T5c | 153 | 153 | 0 | 82 | 80 | +2 | 71 | 73 | -2 | -9.0344 |

These topology differences are independent of the coordinate-frame mismatch. They are compatible with manual curation and/or different morphology generation, but they do not by themselves identify which operation caused each edit.

No guessed coordinate transform, re-rooting, pruning, or branch insertion is applied to V229.
