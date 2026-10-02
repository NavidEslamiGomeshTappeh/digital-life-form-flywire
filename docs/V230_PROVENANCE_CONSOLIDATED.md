# V230 Provenance — consolidated evidence

## Executive result

`v230_results/V230_target_synapses.csv` is now source-proven as a deterministic extraction from the public FlyWire Codex FAFB v783 data products.

V230 contains 649 individual coordinate rows across 75 directed `(pre_root_id, post_root_id)` pairs.

### Direct coordinate proof

GitHub Actions V250 run `37068547506` scanned all 34,156,320 rows of:

`https://storage.googleapis.com/flywire-data/codex/data/fafb/783/synapse_coordinates.csv.gz`

Source SHA-256: `dfcb423d9f685d56c81160e50ca158c9ab589871cb01922af2a5b8c4442216b1`.

Results:

- 649/649 exact full-tuple matches: pre root ID, post root ID, x, y, z.
- 0 missing.
- 0 duplicate coordinate matches.
- 649 unique V230 rows recovered.

The source header is exactly `pre_root_id,post_root_id,x,y,z`. The source uses sparse IDs that are carried forward between rows; the V250 scanner reproduces this format explicitly.

### Pair-count proof

GitHub Actions V251 run `37068749864` scanned all 3,869,878 rows of:

`https://storage.googleapis.com/flywire-data/codex/data/fafb/783/connections.csv.gz`

Results:

- 75/75 V230 directed pairs have a corresponding Codex connection row or rows.
- 75/75 pair-level synapse totals are exactly equal to the number of V230 coordinate rows for that pair.
- total pair count from `connections.csv.gz`: 649.
- total V230 coordinate rows: 649.

This establishes the reconstruction route:

1. Start with the 75 directed pair keys represented in V230.
2. Read Codex v783 `synapse_coordinates.csv.gz` with forward-filled pre/post IDs.
3. Keep the rows belonging to those 75 pairs.
4. Emit `pre_root_id,post_root_id,x,y,z`.

The historical producer script is not preserved in the Git history, so this is a deterministic reconstruction of the original data product rather than a recovery of the original source code text.

### Independent frozen-v783 corroboration

A separate analysis used the frozen Zenodo `flywire_synapses_783.feather` release. For all 649 rows, V230 coordinates equal the component-wise midpoint of the canonical frozen pre/post coordinate pair, with 649 unique mappings.

Frozen source MD5: `f8f1b97c9d4b0ea9b4c8b287f6b99091`.

Midpoint mapping SHA-256: `045183a5cbc268216c237a9708d44dd9a3ebb1d34b92e932226e7ce7e0e85d60`.

This corroborates the coordinates from an independent frozen FlyWire release. It does not change the direct provenance result: the authoritative data-product match is Codex v783 `synapse_coordinates.csv.gz`.

### What is and is not established

Established: source dataset, schema, exact 649 coordinate tuples, exact 75 pair counts, and a deterministic public-data reconstruction route.

Not established from the preserved history: the original script/command that selected those exact 75 directed pairs.

Also not claimed: that the V230 x/y/z field is itself an explicitly named biological 'cleft center'. The proven statement is that it is the exact Codex v783 synapse-coordinate field and that the same coordinates independently equal the frozen Zenodo pre/post midpoint.

## CI evidence

- V250 run: `37068547506` — artifact digest `sha256:62ff74e710550dee21c3a2584fe1c909de1eade74a0b999aadae36cd911353cc`.
- V251 run: `37068749864` — artifact digest `sha256:ea7c0e60690b3d0dcbfddf050f3f898171eb997620888090fe120c1cb4829c1d`.
- Initial V230 commit: `e57b1ccc5b9f64964af223b6bf8e853579985fe0`.
- V230 blob SHA: `507fc706cc29781457ed502ae0ebdf328a4bae33`.

## Public lineage used

Codex's public data loader defines the v783 GCS data root and downloads `connections.csv.gz` and the other snapshot files from the same v783 data tree. Independent published analysis code and papers also document `synapse_coordinates.csv` as the individual-synapse coordinate product used with Codex FAFB v783.