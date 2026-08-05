# Use Case 7 Capstone — ASML-Style Wafer Defect Inspection

This use case demonstrates an advanced semiconductor metrology workflow inspired by high-end wafer inspection systems. It combines a synthetic wafer pattern, engineered surface roughness, coherent laser-induced speckle, and defect analysis to make critical imaging tradeoffs tangible.

## Workflow

1. Create a wafer surface with die grid fiducials and engineered roughness.
2. Simulate coherent bright-field imaging using a DUV-like source and a Gaussian PSF.
3. Capture a reference wafer image and a defect-containing image.
4. Run defect detection against the reference and measure SNR, speckle contrast, and reconstruction error.

## Typical inputs

- Wafer die-grid geometry and fiducial placement
- Surface roughness amplitude and correlation length
- Defect size, depth, and location
- Exposure time and source coherence length

## Typical outputs

- Defect count, type, and total defect area
- Signal-to-noise ratio (SNR) for the captured wafer image
- Estimated roughness from speckle contrast
- Error metrics versus the defect-free reference image

## Run it from the command line

```bash
source .venv/bin/activate
python notebooks/07_wafer_metrology/defect_capstone/run_asml_capstone.py
```

## Explore it interactively in a notebook

Open the notebook at [notebooks/07_wafer_metrology/defect_capstone/asml_capstone_tutorial.ipynb](../notebooks/07_wafer_metrology/defect_capstone/asml_capstone_tutorial.ipynb) to explore the workflow with editable parameters and a coherence-performance scan.

## Why this use case matters

ASML-style wafer metrology is driven by detection sensitivity and measurement stability under coherent illumination. This capstone shows how surface roughness, speckle noise, and exposure choices interact with defect detection and SNR in a realistic inspection context.
