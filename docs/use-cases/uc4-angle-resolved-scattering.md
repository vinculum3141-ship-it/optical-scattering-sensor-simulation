# Use Case 4 — Angle-Resolved Scattering Measurement

This use case demonstrates how the framework can model an angle-resolved
scattering workflow for a rough surface and summarise the result with a
BRDF-style sweep.

## Workflow

1. Choose incidence and reflection angle ranges.
2. Sweep a scattering model across those angles.
3. Summarise the measurements and fit a simple BRDF-like model.

This is the core idea behind many angle-resolved scatterometry workflows, even though this starter example uses a simplified synthetic surface and a compact fitting model rather than a full instrument calibration workflow.

For a *multi-parameter* sweep — varying surface roughness, incidence
angle, wavelength, refractive index, and/or scattering model together —
use [`ScatteringSweep`](../science/layer-analysis.md#metrology-goniometric-uc4):

```bash
python notebooks/04_angle_resolved_scattering/run_parameter_sweep.py
```

## Typical inputs

- Incidence angle range
- Reflection angle range
- Surface roughness and scattering model

## Typical outputs

- A collection of BRDF measurements
- Summary statistics such as mean and maximum BRDF response
- A fit report for a simple parameterised BRDF model
- A sense of how the angular response changes with roughness and geometry

## What to try

- Widen the incidence or reflection angle range to see how the response changes.
- Change the surface roughness to compare smoother versus rougher behaviour.
- Keep the surface fixed and vary only the incidence angle to isolate the effect of geometry.
- Compare the fitted values against the raw sweep to understand how the simple model behaves.

## Run it from the command line

```bash
source .venv/bin/activate
python notebooks/04_angle_resolved_scattering/run_brdf_sweep.py
```

## Explore it interactively in a notebook

Open the notebook at [notebooks/04_angle_resolved_scattering/brdf_sweep_tutorial.ipynb](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/blob/main/notebooks/04_angle_resolved_scattering/brdf_sweep_tutorial.ipynb) to explore the sweep interactively.

## Why this use case matters

This workflow is useful for material characterisation and optical metrology
work where scattering behaviour is analysed as a function of geometry.
