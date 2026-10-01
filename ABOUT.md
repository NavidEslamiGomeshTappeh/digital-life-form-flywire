# About Digital Life Form — FlyWire

Digital Life Form — FlyWire is a research-engineering repository for recovering and validating real fly-neuron morphology from FlyWire-derived data.

V229 focuses on four exact visual neurons: T4a, T4c, T5a and T5c.

The core rule is simple: a requested neuron is either recovered with evidence tied to its exact root ID, or the operation fails.

Three evidence layers are kept separate:
1. Implementation validity — local code and tests.
2. Network availability — external services can be reached.
3. Recovery evidence — the requested morphology was retrieved and structurally validated.

V229 does not claim to be a complete fly brain or a biologically equivalent simulation.