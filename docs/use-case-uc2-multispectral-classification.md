# Use Case 2 — Multispectral Material Classification

This use case demonstrates a compact multispectral material-identification workflow.
It uses a small spectral reference library and a simple spectral-angle-based classifier to show how a multi-band image can be interpreted.

## Workflow

1. Create a synthetic multispectral image with a few distinct material regions.
2. Compare the measured spectra against reference signatures.
3. Summarise the result with band-ratio values and pixel-wise classification output.

## Typical inputs

- A multispectral image cube with several wavelength bands
- One or more reference spectra for known materials

## Typical outputs

- Band-ratio metrics
- A per-pixel classification map
- A confidence score for each pixel

## Run it from the command line

```bash
source .venv/bin/activate
python examples/run_uc2_multispectral_classification.py
```

## Explore it interactively in a notebook

Open the notebook at [examples/uc2_multispectral_classification_playground.ipynb](../examples/uc2_multispectral_classification_playground.ipynb) to explore the workflow interactively.

## Why this use case matters

This workflow is useful for coating inspection, material sorting, and rapid spectral identification tasks where a simple reference library is enough to explain the underlying classification logic.
