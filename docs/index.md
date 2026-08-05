# Physics-Based Optical Sensor Simulation Framework

A modular, physics-based simulation framework for modelling how optical
sensors respond to scattered light under different source, geometry, and
material conditions. The pipeline is organised into six independent
layers, each of which can be extended, replaced, or recombined without
coupling.

## Choose Your Path

This documentation is organised around the people who use it. Pick the
path that matches what you want to do.

| If you are… | You probably want… | Start here |
|---|---|---|
| **New to the framework** | To get a simulation running today | [Getting Started](getting-started/quickstart.md) → [Training modules](getting-started/training/index.md) |
| **Optical researcher / scientist** | The physics, equations, assumptions, and how to take a workflow to production | [Science section](science/index.md) |
| **Software engineer** | The architecture, design patterns, OOP principles, and how to extend the framework | [Engineering section](engineering/architecture.md) |
| **Tester / QA engineer** | The test strategy, test design, and verification methodology | [Quality Assurance section](quality-assurance/test-strategy.md) |
| **Anyone** | A concrete end-to-end scenario | [Use Cases](use-cases/index.md) |

## Getting Started

Start here if you have never run the framework.

- [Quickstart](getting-started/quickstart.md) — install, run your first
  simulation, and print a terminal heatmap in minutes.
- [Training Modules](getting-started/training/index.md) — a guided,
  hands-on track: first pipeline → the six layers → running the example
  projects → building your own simulation.

## Use Cases

Seven application scenarios, each shipping as a notebook unit (tutorial
+ CLI script + README) with a dedicated page:

- [UC1 — Surface Defect Inspection](use-cases/uc1-surface-defect-inspection.md)
- [UC2 — Multi-Spectral Material Identification](use-cases/uc2-multispectral-identification.md)
- [UC3 — Sensor Performance Characterization](use-cases/uc3-sensor-characterization.md)
- [UC4 — Angle-Resolved Scattering Measurement](use-cases/uc4-angle-resolved-scattering.md)
- [UC5 — Structured Light 3D Scanning](use-cases/uc5-structured-light-3d.md)
- [UC6 — LiDAR Range Finding](use-cases/uc6-lidar-ranging.md)
- [UC7 — Wafer Metrology: Die Alignment](use-cases/uc7-alignment.md) and
  [UC7 — ASML-Style Defect Capstone](use-cases/uc7-defect-capstone.md)

## Science

For optical researchers and scientists: the governing physics, the
models behind each layer, and how to carry a workflow from prototyping
to production.

- [Physics Foundations](science/physics-foundations.md)
- [Layer reference](science/index.md) — illumination, surface,
  scattering, optics, detector, analysis
- [Research Workflows: Prototyping to Production](science/research-workflows.md)

## Engineering

For software engineers: how the framework is designed, the patterns and
principles behind the implementation (and why), and how to extend it.

- [Architecture](engineering/architecture.md) — packages, data flow,
  data contracts
- [Design Patterns & Software Principles](engineering/design-patterns.md)
  — OOP principles, SOLID, GoF patterns, and the *why* behind each
- [Extending the Framework](engineering/extending.md) — every extension
  point with complete examples

## Quality Assurance

For testers and QA engineers: the testing strategy, test design
techniques, and the verification methodology mapped to industry
standards.

- [Test Strategy (ISTQB-aligned)](quality-assurance/test-strategy.md)
- [Testing & Verification](quality-assurance/testing.md) — test
  inventory and how to run the suites
- [Verification & Validation (ISO references)](quality-assurance/verification-and-validation.md)

## Project

- [Future Improvements](future-improvements.md) — single tracker for all
  remaining and deferred work.

## Package Overview

```
src/optical_metrology/
├── illumination/   → Light sources and light-field generation
├── surface/        → Surface geometry (height maps, normals, roughness)
├── scattering/     → Scattering models (BRDF implementations)
├── optics/         → Imaging-system propagation (PSF convolution)
├── detector/       → Digital sensor pipeline (CMOS model)
├── analysis/       → Image analysis (histograms, statistics)
├── pipeline.py     → Pipeline orchestrator (single-call simulation)
└── utils/          → Shared utilities (heatmap visualisation)
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
