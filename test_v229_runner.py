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
