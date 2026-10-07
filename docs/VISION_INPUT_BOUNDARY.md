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

## Uho-S2E network camera boundary

The repository now includes a bounded RTSP network-camera adapter for cameras that expose an RTSP stream.

The identified office camera is **Uniarch Uho-S2E**. Uniarch's published datasheet specifies 2 MP imaging, RJ45 Ethernet, 2.4 GHz Wi-Fi, H.264/H.265 video, RTSP authentication, ONVIF/API integration, human-body and motion detection, auto tracking, and Pan 360° / Tilt 105° for the Uho-S2E datasheet revision inspected by the project. The vendor also documents RTSP as a supported network protocol. These upstream capabilities are the basis for the network-camera integration; they are not treated as evidence that the user's physical device has already been connected or exercised.

NetworkCameraSource opens an explicit rtsp:// or rtsps:// URL through OpenCV, captures a bounded frame count, converts each frame to the same VisionFrame contract used by the local-camera path, and releases the stream in all exit paths.

For secret hygiene, the provenance locator strips RTSP username/password, query strings, and fragments before recording the source in a receipt. Credentials should preferably be supplied through an environment variable rather than a shell argument.

Example on the user's local machine:

```powershell
$env:DLF_RTSP_URL = "rtsp://USERNAME:PASSWORD@CAMERA-IP:554/STREAM-PATH"
dlf-flywire capture-network-camera --url-env DLF_RTSP_URL --frames 10 --output data/vision/network-capture
```

The exact RTSP stream path is intentionally not hard-coded because the public Uho-S2E datasheet confirms RTSP support but does not establish one universal stream URL for every firmware/configuration.

A successful run proves only that the configured RTSP endpoint returned bounded frames and that those frames entered the project's provenance-bearing gray8 pipeline. It does not prove PTZ control, internet reachability, human detection correctness, or camera-driven biological control.

The next hardware-integration layer is a separate PTZ controller. It should use an explicit ONVIF/API contract, record the requested and observed camera position, and remain independent from the vision-frame provenance path.
