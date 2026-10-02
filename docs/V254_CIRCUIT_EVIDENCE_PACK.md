# V254 — Circuit Evidence Pack Specification

## Goal

Turn the existing V215–V230 evidence chain into a reusable, version-pinned circuit extraction product.

## Contract

Given:

- dataset/version;
- a finite list of exact root IDs;
- an explicit selection policy;

produce a self-contained evidence package.

The package must preserve the distinction between source observations, deterministic transformations, and biological interpretation.

## Required outputs

### 1. Identity

For each requested root:

- root ID;
- cell type annotation;
- annotation source/version;
- exact-match status.

### 2. Connectivity

For every selected directed pair:

- pre root ID;
- post root ID;
- neuropil;
- synapse count;
- neurotransmitter field as supplied by source;
- source dataset/version.

### 3. Individual synapses

For every selected synapse:

- pre root ID;
- post root ID;
- coordinate fields with explicit coordinate semantics;
- source table;
- source version;
- immutable source hash where available.

### 4. Morphology

For every requested neuron:

- exact root ID;
- morphology source;
- morphology version;
- morphology representation;
- file hash;
- structural validation.

No substitute morphology may be inserted because it looks similar.

### 5. Compartment mapping

For every individual synapse mapped to morphology:

- target root ID;
- morphology node or segment identifier;
- compartment label;
- mapping method;
- distance or error metric;
- acceptance or rejection reason.

### 6. Provenance

Every generated package must contain:

- source URLs or immutable source records;
- dataset versions;
- selection rules;
- transformation sequence;
- software revision;
- input hashes;
- output hashes;
- validation results;
- regeneration command.

## First regression case

The first V254 implementation must reproduce the established V230 case:

- four anchor roots;
- 75 directed pairs;
- 649 synapse rows.

The expected pair-selection reconstruction is:

**pair is incident to one of the four anchor roots in Codex FAFB v783.**

For the current snapshot, applying that rule to the public v783 connections table yields exactly 75 pairs and 649 summed synapses.

The observed V230 minimum of five rows per pair must not be treated as proof of a historical >=5 filter because thresholds 1 through 5 all reproduce the same 75-pair set for this target neighborhood.

## Acceptance criteria

V254 is not complete when a demo runs.

It is complete when a clean run can:

1. regenerate the four-neuron evidence package;
2. reproduce the same pair set;
3. reproduce the same individual synapse set;
4. preserve source and output hashes;
5. validate exact root identity;
6. expose every transformation in a machine-readable manifest;
7. fail closed when required evidence is missing.

## Design boundary

The Circuit Evidence Pack is the core product.

Whole-brain behavioral demos, UI work and additional cognitive experiments are secondary until this reusable extraction layer is stable.