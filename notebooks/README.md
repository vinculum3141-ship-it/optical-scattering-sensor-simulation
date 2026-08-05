# Notebooks

Self-contained, runnable units for learning and onboarding.  Each
numbered unit models one real-world optical-metrology scenario end to
end and bundles everything needed to run it: a tutorial notebook, a
CLI script, and a README that states the objective, expected outputs,
and pointers to the full documentation.

Everything runs against the installed package (`pip install -e .`) —
no extra setup per unit.

## Units

| # | Unit | Scenario | Audience | Run |
|---|---|---|---|---|
| 00 | [Getting Started](00_getting_started/) | Full pipeline overview (light → surface → scattering → optics → detector → analysis) | Everyone | `00_getting_started/basic_pipeline.ipynb` |
| 01 | [Surface Defect Inspection](01_surface_defect_inspection/) | AOI pass/fail under different illumination | Manufacturing / process engineers, AOI developers | `01_surface_defect_inspection/` |
| 02 | [Multi-Spectral Identification](02_multispectral_identification/) | Material ID from spectral reflectance | Spectroscopists, QA (recycling / food / pharma) | `02_multispectral_identification/` |
| 03 | [Sensor Characterization](03_sensor_characterization/) | Detector PTC, SNR, dynamic range, linearity | Camera designers, sensor integrators | `03_sensor_characterization/` |
| 04 | [Angle-Resolved Scattering](04_angle_resolved_scattering/) | Goniometric BRDF sweep + model fitting | Material scientists, coating QC, optics R&D | `04_angle_resolved_scattering/` |
| 05 | [Structured Light 3D](05_structured_light_3d/) | Fringe projection → phase → height reconstruction | Metrology engineers, 3D-scanner developers | `05_structured_light_3d/` |
| 06 | [LiDAR Range Finding](06_lidar_ranging/) | Pulsed-laser ToF ranging → point cloud | Automotive / robotics, LiDAR researchers | `06_lidar_ranging/` |
| 07 | [Wafer Metrology](07_wafer_metrology/) | Die-alignment + ASML-style defect capstone | Semiconductor process / metrology engineers | `07_wafer_metrology/` |

## How to use

1. `pip install -e .` in a virtual environment.
2. Open a unit's folder: read its `README.md`, then either run the
   CLI script or open the tutorial notebook.
3. Notebooks follow one pattern: a short intro (objective, what
   you'll see), an editable-parameters cell, the pipeline cells, and
   a "Try next" list of one-parameter-at-a-time experiments.

## Documentation

- Full use-case descriptions and status: [`docs/use-cases.md`](../docs/use-cases.md)
- Per-unit pages: [`docs/use-case-uc*.md`](../docs/)
- Layer reference docs: [`docs/layer-*.md`](../docs/)
