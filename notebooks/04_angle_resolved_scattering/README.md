# 04 — Angle-Resolved Scattering Measurement

> Goniometric scatterometry: sweep incidence and reflection angles to characterise a surface BRDF.

## Objective

Sweep the reflection angle at a fixed incidence, record the scattered radiance, and fit a BRDF-like model to the angle-resolved data — the basis for material and coating characterisation.

## What you'll see

- A `GoniometricSweep` of scattered radiance across reflection angles
- A fitted BRDF-like model compared to the sweep (`BRDFFitter`)
- A cross-model parameter sweep (`ScatteringSweep`) comparing scattering models over roughness / angle / wavelength

## Run it

- **Notebook:** open `brdf_sweep_tutorial.ipynb`, edit the parameters cell, run in order.
- **CLI:** `python run_brdf_sweep.py --help`; multi-parameter sweep: `python run_parameter_sweep.py --help`.

## Try next

- Change surface roughness and watch the BRDF lobe broaden.
- Vary the incidence angle and see the peak shift.
- Compare Beckmann vs. GGX fits for the same surface.

## Learn more

- [Use-case documentation](../../docs/use-case-uc4-brdf-sweep.md)
- Key modules: `scattering.BeckmannScattering/GGXScattering`, `analysis.GoniometricSweep/BRDFFitter/ScatteringSweep`, `surface.RoughSurface`

> Note: `run_parameter_sweep.py` (the cross-model `ScatteringSweep` tool)
> lives here because it is a scattering-model comparison harness.
