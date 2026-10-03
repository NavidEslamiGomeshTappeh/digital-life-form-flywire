import tempfile, unittest
from pathlib import Path
import pandas as pd
from v259_published_point_provenance import extract_anchor_rows, legacy_optimal_partition_root, parse_swc

class V259Tests(unittest.TestCase):
    def test_anchor_selection_requires_all_four(self):
        base={"Neuron_type":"T4","Neuron_subtype":"a","Subtype":"T4a","hemisphere":"R",
              "root_x":1,"root_y":2,"root_z":3,"Segement_count":1,"Total_cable":1,"Total_nodes":2,
              "External_edges":1,"Intenal_edges":0,"Number_leaves":1,"Number_branches":1}
        rows=[]
        for rid,sub,typ in [("720575940632008007","a","T4a"),("720575940616224414","c","T4c"),
                            ("720575940625571465","a","T5a"),("720575940617782941","c","T5c")]:
            row=dict(base); row.update(ID=rid,Neuron_type=typ[:2],Neuron_subtype=sub,Subtype=typ); rows.append(row)
        out=extract_anchor_rows(pd.DataFrame(rows))
        self.assertEqual(out["ID"].tolist(),[x[0] for x in [
            ("720575940632008007","a","T4a"),("720575940616224414","c","T4c"),
            ("720575940625571465","a","T5a"),("720575940617782941","c","T5c")]])

    def test_legacy_score_chooses_expected_branch(self):
        swc="""1 1 0 0 0 1 -1
2 3 1 0 0 1 1
3 3 -1 0 0 1 1
4 3 0 1 0 1 2
5 3 2 0 0 1 2
6 3 -2 0 0 1 3
"""
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"fixture.swc"; path.write_text(swc,encoding="utf-8")
            result=legacy_optimal_partition_root(parse_swc(path))
            self.assertEqual(result["node_id"],2); self.assertEqual(result["leaf_count"],3)

if __name__=="__main__": unittest.main()
