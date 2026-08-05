# Use Case 5 — Structured Light 3D Scanning

This use case demonstrates a simple fringe-projection profilometry workflow.
The simulation generates phase-shifted fringe patterns, extracts a wrapped
phase map, unwraps it, reconstructs a height map, and compares the result
against a synthetic ground-truth surface.

## Workflow

1. Generate sinusoidal fringe patterns with a projector.
2. Extract wrapped phase from phase-shifted fringe images.
3. Unwrap the phase to remove $2\pi$ discontinuities.
4. Reconstruct a height map from phase difference via triangulation.
5. Compare the reconstruction against a reference surface.

This is the core logic behind many industrial profilometry systems, even though this starter example uses a simplified synthetic surface rather than a full camera-projector calibration pipeline.

## Typical inputs

- Fringe period
- Projection angle
- Synthetic surface height map

## Typical outputs

- Wrapped and unwrapped phase maps
- Reconstructed height map
- Reconstruction error metrics such as RMS and MAE
- A visual sense of how well the phase-based geometry matches the reference surface

## What to try

- Change the fringe period to see how spatial resolution changes.
- Change the projection angle to see how triangulation sensitivity changes.
- Make the synthetic surface taller or more sharply stepped to see where the simple model breaks down.
- Compare a flat reference surface against a stepped surface to make the phase effect easier to understand.

## Run it from the command line

```bash
source .venv/bin/activate
python notebooks/05_structured_light_3d/run_structured_light.py
```

## Explore it interactively in a notebook

Open the notebook at [notebooks/05_structured_light_3d/structured_light_tutorial.ipynb](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/blob/main/notebooks/05_structured_light_3d/structured_light_tutorial.ipynb) to explore the workflow interactively.

## Why this use case matters

This workflow is useful for 3D surface measurement, profilometry, and
structured-light inspection systems where accurate depth recovery is key.
