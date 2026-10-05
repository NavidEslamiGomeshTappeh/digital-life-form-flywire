# Vision input boundary

The project now has an explicit input boundary for future real-camera integration.

## Contract

The physical path is intentionally split:

`camera -> gray8 VisionFrame -> persisted frame artifact -> provenance receipt -> FlyVis stimulus rendering`

`VisionFrame` stores:

- frame index;
- UTC capture timestamp;
- width and height;
- exact grayscale byte payload;
- SHA-256 of the grayscale payload.

The payload can be written byte-for-byte to a binary PGM artifact. The receipt records the source kind/locator and each frame's content fingerprint.

## Physical capture

`OpenCVCameraSource` is a bounded physical-device capture adapter. OpenCV is imported only when physical capture is requested, so the core package remains dependency-free.

A physical-camera run is successful only when a real device opens and returns frames. No CI test or synthetic test is treated as evidence that a physical camera works.

## FlyVis boundary

The output is deliberately a grayscale image frame. It does not:

- claim exact FAFB v783 root activity;
- convert pixels directly into spikes;
- assign a biological neuron identifier;
- grant a Code Hand capability;
- claim camera-driven biological control.

The next integration stage is a separate, provenance-bearing bridge from grayscale frame sequences into the pinned FlyVis `BoxEye` rendering contract. That bridge must preserve the source frame hashes and prove the resulting tensor shape/ordering against the upstream implementation before any neural-activity claim is made.

## Physical camera -> FlyVis

The runtime also exposes an end-to-end local bridge:

`physical camera -> gray8 frames -> PGM + capture receipt -> BoxEye (721) -> pinned FlyVis network -> continuous responses`

Run it with:

```bash
dlf-flywire camera-flyvis --device 0 --frames 20 --output data/vision/camera-flyvis
```

This command is intentionally bounded. It only returns success after the camera opens and all requested frames are read, each frame is fingerprinted, BoxEye returns the expected 721-receptor contract, and the pinned FlyVis network produces finite responses.

The resulting `camera-flyvis-receipt.json` records the physical device index, frame hashes, BoxEye hashes, pinned FlyVis revision/checkpoint hash, response hash, and the scientific boundary flags.

A successful local run is evidence of a real camera-to-model software path. It is not evidence of exact FAFB v783 root-level electrical activity, biological spikes, or biological control.
