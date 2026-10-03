import tempfile
import unittest
from pathlib import Path

import pandas as pd

from v261_coordinate_provenance_audit import (
    anchor_rows,
    load_point_data,
    parse_swc,
    subtree_metrics,
)


class V261Tests(unittest.TestCase):
    def test_anchor_rows_require_exact_ids(self):
        df = pd.DataFrame(
            {
                "ID": ["1", "2", "3", "4"],
                "Root_x": [0, 1, 2, 3],
                "Root_y": [0, 1, 2, 3],
                "Root_z": [0, 1, 2, 3],
            }
        )
        with self.assertRaises(RuntimeError):
            anchor_rows(df)

    def test_historical_schema_normalizes(self):
        df = pd.DataFrame(
            {
                "ID": [720575940632008007],
                "Type": ["T4"],
                "Subtype": ["T4a"],
                "Hemisphere": ["R"],
                "Root_x": [1.5],
                "Root_y": [2.5],
                "Root_z": [3.5],
            }
        )
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "point.pkl"
            df.to_pickle(p)
            out = load_point_data(p)
            self.assertIn("Root_x", out.columns)
            self.assertEqual(out.loc[0, "ID"], "720575940632008007")
            self.assertAlmostEqual(float(out.loc[0, "Root_z"]), 3.5)

    def test_subtree_reduction_invariants(self):
        swc = """1 1 0 0 0 1 -1
2 5 1 0 0 1 1
3 0 2 0 0 1 2
4 0 0 1 0 1 2
5 0 3 0 0 1 3
6 0 -1 1 0 1 4
"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "fixture.swc"
            p.write_text(swc, encoding="utf-8")
            tree = parse_swc(p)
            m = subtree_metrics(tree, 2)
            self.assertEqual(m["node_count_full"], 5)
            self.assertEqual(m["leaf_count"], 2)
            self.assertEqual(m["branch_count"], 1)
            self.assertEqual(m["reduced_node_count"], 4)
            self.assertEqual(m["reduced_edge_count"], 3)


if __name__ == "__main__":
    unittest.main()
