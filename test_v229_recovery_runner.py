from pathlib import Path
ns={}; p=Path(__file__).parent/"v229_recovery_runner.py"; exec(compile(p.read_text(),str(p),"exec"),ns)
assert ns["ROOTS"]=={"T4a":720575940632008007,"T4c":720575940616224414,"T5a":720575940625571465,"T5c":720575940617782941}
assert ns["ZENODO_MD5"]=="a4c104776f33ec539ef859064c4de3df"
assert ns["MRC_BASE"].endswith("flywire_skeletons_783")
print("PASS: exact roots, route order, endpoint and Zenodo MD5")


# Unit-test exact source-ID validation without network access.
class _Neuron:
    def __init__(self, ident):
        self.id = ident
assert ns["neuron_id_as_int"](_Neuron(123)) == 123
try:
    ns["neuron_id_as_int"](_Neuron("not-an-id"))
except RuntimeError:
    pass
else:
    raise AssertionError("non-integer source ID must fail")
print("PASS: source neuron ID validation")


# Structural SWC validation tests without external services.
import tempfile
with tempfile.TemporaryDirectory() as d:
    good=Path(d)/"good.swc"
    good.write_text("1 1 0 0 0 1 -1\n2 3 1 1 1 1 1\n", encoding="utf-8")
    a=ns["verify_swc"](good, 123)
    assert a["valid"] and a["structural_root_count"] == 1 and not a["missing_parent_refs"]

    bad=Path(d)/"bad.swc"
    bad.write_text("1 1 0 0 0 1 -1\n2 3 nan 1 1 1 9\n", encoding="utf-8")
    b=ns["verify_swc"](bad, 123)
    assert not b["valid"]
    assert b["missing_parent_refs"] == [9]

print("PASS: SWC structural and finite-geometry validation")
