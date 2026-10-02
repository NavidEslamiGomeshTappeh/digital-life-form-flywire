# Project Positioning

## The one-sentence problem

Make an exact, version-pinned subset of the FlyWire connectome reproducible all the way from neuron identity to synapse coordinates, morphology, and simulation-ready structure.

## Why another FlyWire repository?

There is already a strong ecosystem around FlyWire.

- FlyWire/Codex provide the underlying data and access paths.
- flyconnectome/flywire_annotations distributes systematic annotations and links the published FAFB v783 products.
- seung-lab/FlyConnectome teaches programmatic data access.
- fafbseg and navis provide practical analysis and morphology tooling.
- Many newer repositories build whole-brain LIF or embodied fly simulations.

The project should therefore not try to win by being another FlyWire simulator.

Its defensible niche is:

**cross-layer provenance + exact-cell identity + reproducible circuit packaging**

## The user we are building for

The primary user is a computational neuroscientist who has a small hypothesis-driven set of neurons and wants a trustworthy input bundle.

Their question is not:

> Can I visualize a fly brain?

It is:

> Can I give you these exact neurons, and get back exactly which synapses and morphology went into the model, with enough evidence that another person can regenerate it?

## The product

The central reusable artifact should become a Circuit Evidence Pack.

A pack should contain:

- dataset/version identifiers;
- exact root IDs;
- cell annotations;
- directed pair table;
- individual synapse table;
- morphology files or immutable source references;
- synapse-to-morphology mapping;
- transformation and selection rules;
- hashes;
- validation results;
- regeneration command.

The pack should be useful without this repository's history being mentally reconstructed.

## Why this could attract GitHub users

A new visitor should be able to answer three questions within a minute:

### What problem does it solve?

Reproducible extraction of a small real neural circuit from a large connectome.

### What is different?

The repository treats provenance as part of the computational artifact, not as prose added after the experiment.

### What can I use?

The same exact circuit can become input to another analysis or a biophysical simulator without guessing which cells, connections, coordinates, or transformations were intended.

## What would make it genuinely valuable

The following progression is deliberate:

1. reproduce the existing V230 evidence;
2. generalize it into the reusable Circuit Evidence Pack;
3. map synapses onto exact morphology;
4. export a compartmental representation;
5. support a standard downstream simulator without hiding assumptions.

The project should resist adding unrelated behavior demos until this core artifact is strong.

## What would be a bad direction

A large whole-brain demo with impressive visuals but unclear provenance would make the project less differentiated, because similar projects already exist.

More V-numbered experiments are useful only when they advance the reusable pipeline or establish an independently testable scientific property.

## Current reality check

The repository currently has no stars, no forks, no topics, and no declared license. That means there is not yet evidence of community traction.

That is not a scientific failure. It means the next work should make the repository easier to understand and reuse rather than simply increasing the version number.

The README and architecture should make the project's narrow value proposition obvious before additional major simulation layers are added.