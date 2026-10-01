# Validation Contract

## Identity
The requested FlyWire root ID must match the source neuron's own ID before SWC serialization.

## Morphology
The SWC must contain at least one node, exactly one structural root, no missing parent references and finite x/y/z/radius values.

## Provenance
Successful recovery records the requested root ID, cell label, VFB identifier, selected route, execution time and SWC SHA-256.

## Evidence levels
Unit PASS = local implementation checks.
Network PASS = external endpoint reachable.
Recovery PASS = requested source neuron retrieved and resulting SWC structurally validated.
Only the third level is recovery evidence.