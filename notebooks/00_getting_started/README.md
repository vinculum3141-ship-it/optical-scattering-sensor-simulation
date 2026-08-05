# 00 — Getting Started

> Run the full simulation pipeline once, end to end, to see how the layers fit together.

## Objective

Trace a single scene through every stage of the framework: illumination → surface → scattering → optics → detector → analysis.  The mental model for all other units.

## What you'll see

- A light source generating a field over a surface
- Scattered radiance convolved by the imaging optics
- A detector capture and the resulting analysis measurements
- `SimulationPipeline` orchestrating the whole chain

## Run it

- **Notebook:** open `basic_pipeline.ipynb`, edit the parameters cell, run in order.

## Try next

- Swap the scattering model (e.g. Lambertian → Phong) and watch the image change.
- Increase the PSF sigma and see the blur.
- Change the surface from flat to rough.

## Learn more

- Framework overview: [`../../docs/engineering/architecture.md`](../../docs/engineering/architecture.md)
- Key module: `optical_metrology.pipeline.SimulationPipeline`
