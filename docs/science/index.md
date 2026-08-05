# Science — Layer Reference

> **Target audience:** Optical researchers, scientists, and engineers who
> want the physics behind each layer of the pipeline.

This section documents the physical models, their assumptions, and their
numerical implementation, layer by layer. Start with the physics
foundations for the governing equations, then dive into any layer.

## Physics Foundations

- [Physics Foundations](physics-foundations.md) — governing equations,
  SI units, and the assumptions shared across all layers.

## The Six Layers

| Layer | Page | What it models |
|---|---|---|
| 1. Illumination | [layer-illumination.md](layer-illumination.md) | Light sources (laser, LED, sunlight, broadband), beam profiles, spectral models, polarisation, wavefronts |
| 2. Surface | [layer-surface.md](layer-surface.md) | Height maps, normals, roughness, defect generators, wafer surfaces |
| 3. Scattering | [layer-scattering.md](layer-scattering.md) | BRDF models — Lambertian, Phong, Oren-Nayar, Beckmann, GGX, Cook-Torrance, Rayleigh, Mie |
| 4. Optics | [layer-optics.md](layer-optics.md) | Imaging systems, PSF convolution (Gaussian, Airy, Zernike), defocus, propagation |
| 5. Detector | [layer-detector.md](layer-detector.md) | Photon conversion, noise models, ADC, CMOS pipeline, CFA, SPAD |
| 6. Analysis | [layer-analysis.md](layer-analysis.md) | Metrics, statistics, and pluggable analysis modules (contrast, SNR, MTF, defects, PTC, …) |

## Research Workflows

- [Research Workflows: Prototyping to Production](research-workflows.md)
  — a repeatable path from a one-off notebook to a validated,
  hand-offable measurement workflow.
