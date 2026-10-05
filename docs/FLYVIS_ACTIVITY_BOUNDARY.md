# FlyVis activity boundary

## Why this boundary exists

The official TuragaLab/flyvis implementation publishes a connectome-constrained deep mechanistic network for the Drosophila visual system. The associated Nature paper states that the released model predicts T4/T5 responses and direction-selective motion computations, and the reference implementation exposes cell-type response traces including T4a, T4c, T5a, and T5c.

This is useful for the Digital Life Form project, but it is not the same thing as a recorded spike train from the four exact FAFB v783 root IDs in this repository.

## Frozen upstream reference

For the first bounded integration target, the upstream FlyVis release is pinned to:

- repository: TuragaLab/flyvis
- release: v1.2.0
- commit: 92b3845cc426dd309a1a0e1b3890156c42e14021
- pretrained-model archive SHA-256: 71c78d4070556a536b13b23ee3139cd2788aa2a9d07d430a223b4edead281db1

The official installation path downloads the pretrained models separately from the source tree. See the upstream install instructions for the exact download procedure.

## Implemented adapter

src/dlf_flywire/flyvis_adapter.py provides FlyVisResponseAdapter.

It accepts a validated continuous response trace for one supported T4/T5 subtype and records:

- upstream source revision;
- immutable pretrained-model artifact SHA-256;
- trace start time and sampling interval;
- complete response trace;
- separate trace and source fingerprints.

The adapter deliberately imports no FlyVis package and has no new runtime dependency.

## Activity semantics contract

FlyVis response values are continuous model responses / voltage-like activities reported in arbitrary units in the published analysis. The published model uses passive, leaky, linear, **non-spiking** voltage dynamics; the project therefore preserves this signal class instead of silently interpreting it as spikes.

`FlyVisResponseSignal` exposes three explicit semantics:

- `signal_kind = continuous_voltage_response`
- `signal_units = arbitrary_units`
- `spike_conversion_allowed = false`

A direct `to_neural_observation()` conversion is deliberately fail-closed. A future spike/rate encoder must be introduced as a separate, evidence-backed modeling artifact with its own assumptions, calibration, tests, and provenance.

## Hard boundary

FlyVis response values are continuous model responses, reported in arbitrary units in the published analysis. They are not treated as spike counts here.

Therefore this adapter does not:

- convert voltage/response values to spikes;
- create NeuralObservation instances;
- create a biological root-ID mapping;
- claim that a particular FAFB v783 root was individually measured by the FlyVis training/evaluation experiments;
- assign a Code Hand capability.

The next unresolved bridge is explicit:

FlyVis cell-type response -> validated response signal -> unknown spike/rate encoding -> NeuralObservation

The unknown encoding step is a scientific/modeling decision and must not be silently invented.

## Exact-root distinction

The project anchors are exact FAFB v783 root IDs. FlyVis uses a connectome-constrained optic-lobe model with cell-type and retinotopic structure. A successful FlyVis response trace therefore provides cell-type/model evidence, not exact-root identity evidence for the four project neurons.

The correct future join, if one becomes defensible, must carry an explicit mapping artifact and source evidence for that mapping.

## References

- https://github.com/TuragaLab/flyvis/releases/tag/v1.2.0
- https://github.com/TuragaLab/flyvis/blob/v1.2.0/docs/docs/install.md
- https://github.com/TuragaLab/flyvis/blob/v1.2.0/docs/docs/examples/04_flyvision_moving_edge_responses.md
- https://www.nature.com/articles/s41586-024-07939-3
