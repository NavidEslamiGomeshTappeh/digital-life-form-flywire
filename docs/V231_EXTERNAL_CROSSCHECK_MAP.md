# V231 External Cross-Check Map

## Purpose

V230 has two distinct verification problems:

1. **Coordinate membership** — requires the canonical `flywire_synapses_783.feather` release because it contains the pre/post coordinate columns.
2. **Pair-level topology** — can be cross-checked against smaller v783-derived connectivity products.

## Canonical source

The authoritative public release is FlyWire FAFB v783 on Zenodo (DOI 10.5281/zenodo.10676866). Its full synapse table contains roughly 130 million synapses and explicitly provides both `pre_pt_position_{x,y,z}` and `post_pt_position_{x,y,z}`. The release also provides `proofread_connections_783.feather`, summarized by neuron pair and neuropil.

## Independent derivative

ConnectomeKG v0.2.1, published in September 2026, describes a queryable knowledge graph whose first corpus is FlyWire FAFB v783. Its compact distribution can be useful as an **independent topology cross-check**, not as a replacement for the canonical coordinate test.

## Evidence boundary

An agreement between V230 and an independent v783-derived graph can strengthen confidence that the observed neuron-pair topology is not a parsing accident. It cannot prove that the 649 coordinate rows came from the historical extraction unless the actual source rows and coordinate fields are matched.

Therefore the project uses this hierarchy:

    v783 full synapse release
        -> exact coordinate membership
        -> coordinate-side identification
        -> pair-level connectivity
        -> biological interpretation

    independent v783 derivatives
        -> topology cross-check only

Never promote a derivative cross-check into exact coordinate provenance.
