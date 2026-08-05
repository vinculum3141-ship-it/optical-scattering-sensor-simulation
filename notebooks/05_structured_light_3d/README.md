# 05 — Structured Light 3D Scanning

> Reconstruct a 3D surface from deformed projected fringe patterns.

## Objective

Project phase-shifted sinusoidal fringes, convert the captured fringes to a wrapped phase map, unwrap it, and triangulate to a height estimate — then compare the reconstruction to ground truth.

## What you'll see

- Phase-shifted fringe patterns over a synthetic surface (`FringeProjector`)
- Wrapped phase (`PhaseExtractor`) → unwrapped phase (`PhaseUnwrapper`) → reconstructed height (`HeightReconstructor`)
- RMS error comparison against the reference surface (`SurfaceComparator`)

## Run it

- **Notebook:** open `structured_light_tutorial.ipynb`, edit the parameters cell, run in order.
- **CLI:** `python run_structured_light.py --help` (fringe period, phase shifts, projection angle).

## Try next

- Reduce the number of phase shifts and watch the wrapped phase degrade.
- Increase the surface height amplitude and see reconstruction error grow.
- Change the fringe period and observe height resolution change.

## Learn more

- [Use-case documentation](../../docs/use-case-uc5-structured-light.md)
- Key modules: `illumination.FringeProjector`, `analysis.PhaseExtractor/PhaseUnwrapper/HeightReconstructor/SurfaceComparator`
