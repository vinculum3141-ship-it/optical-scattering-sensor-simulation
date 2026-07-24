# Physics-Based Optical Sensor Simulation Framework

A modular, physics-based simulation framework for modelling how optical
sensors respond to scattered light under different source, geometry, and
material conditions. The pipeline is organised into six independent layers,
each of which can be extended, replaced, or recombined without coupling.

## Audience

This documentation targets two primary audiences:

- **Physics scientists / optical engineers** — readers interested in the
  physical models, their assumptions and limitations, the numerical methods
  used, and how to configure simulations for specific use cases.
- **Software engineers / R&D developers** — readers interested in the
  software architecture, code patterns, extension points, testing strategy,
  and how to integrate or adapt the framework into larger systems.

Each section calls out which audience it primarily addresses.

## Documentation Map

| Section | Audience | What it covers |
|---|---|---|
| [Quickstart](quickstart.md) | Both | Install, run demos, first simulation |
| [Architecture](architecture.md) | Engineers | Package structure, design patterns, data flow |
| [Physics Foundations](physics-foundations.md) | Scientists | Governing equations, units, assumptions |
| [Illumination Layer](layer-illumination.md) | Both | Source models, beam profiles, spectra |
| [Surface Geometry Layer](layer-surface.md) | Both | Height maps, normals, roughness, generators |
| [Scattering Layer](layer-scattering.md) | Both | BRDF models, Lambert's law, extensions |
| [Optics Layer](layer-optics.md) | Both | Imaging systems, PSF convolution, propagation |
| [Detector Layer](layer-detector.md) | Both | Photon conversion, noise, ADC, CMOS pipeline |
| [Analysis Layer](layer-analysis.md) | Both | Histograms, statistics, pluggable modules |
| [Testing & Verification](testing.md) | Engineers | Unit tests, Robot Framework, verification strategy |
| [Extending the Framework](extending.md) | Engineers | Custom sources, surfaces, scattering, noise, analysis |

## Package Overview

```
illumination/     → Light sources and light-field generation
surface/          → Surface geometry (height maps, normals, roughness)
scattering/       → Scattering models (BRDF implementations)
optics/           → Imaging-system propagation (PSF convolution)
detector/         → Digital sensor pipeline (CMOS model)
analysis/         → Image analysis (histograms, statistics)
```

## Key Design Principles

1. **Physical quantities in SI units** — every parameter uses metres,
   Watts, radians, seconds. No ambiguous unit conventions.
2. **Independent layers** — the illumination package knows nothing about
   surfaces; the surface package knows nothing about light. They connect
   only through the well-defined data contracts (`LightField`, `Surface`,
   `ScatteredField`, `SensorField`, `DigitalImage`).
3. **Deterministic where possible** — surface generators use fixed RNG
   seeds by default; detector noise is the primary source of stochastic
   variation.
4. **No optional dependencies for core use** — the core pipeline requires
   only NumPy. Matplotlib, Jupyter, and Robot Framework are optional.
5. **Terminal-native visualisation** — every field and image can be
   rendered as a Unicode heatmap without any plotting library.
