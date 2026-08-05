# Use Case 1 — Surface Defect Inspection

This use case shows how the framework can model an automated optical
inspection (AOI) workflow for surface defects such as dents, pits,
cracks, stains, and other local anomalies.

## What the workflow models

The simulation follows the full framework pipeline:

1. Choose an illumination geometry
2. Generate a defect-containing surface
3. Scatter light from the surface through an optical model
4. Capture the sensor image
5. Run a defect analysis module and inspect the result

## Typical inputs

- Defect type: `dent`, `pit`, `crack`, or `stain`
- Illumination mode: `brightfield` or `darkfield`
- Detection threshold for the analyzer
- Surface size and detector exposure settings

## Typical outputs

- A simulated detector image
- Defect count and total defect area
- A pass/fail decision based on the chosen thresholding rules
- Optional defect metadata such as centroid and bounding box

## Run it from the command line

```bash
source .venv/bin/activate
python notebooks/01_surface_defect_inspection/run_inspection.py --defect dent --illumination darkfield --threshold 0.08
```

This produces a short analysis report showing whether defects were found
and how the chosen settings affect the result.

## Explore it interactively in a notebook

Open the notebook at [notebooks/01_surface_defect_inspection/inspection_tutorial.ipynb](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/blob/main/notebooks/01_surface_defect_inspection/inspection_tutorial.ipynb)
for a parameter-driven walkthrough. The notebook is designed so you can
change one setting at a time and compare how the inspection result changes.

## Suggested experiments

- Switch from `darkfield` to `brightfield` and compare contrast
- Increase or decrease the threshold to change the defect count
- Try a different defect type such as `crack` or `stain`
- Increase the exposure time to see how the detector signal changes

## Why this use case matters

This workflow is representative of semiconductor, electronics, and
consumer-goods inspection where optical contrast and defect visibility are
strongly dependent on illumination geometry and analysis thresholds.
