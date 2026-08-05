# Use Cases

> **Target audience:** Product managers, R&D leads, simulation engineers,
> students, and anyone learning what the framework can model.

The framework is demonstrated through seven application use cases that
cover real-world sensing scenarios in semiconductor manufacturing,
inspection, and metrology.  Each use case maps a concrete measurement
problem onto the simulation chain — illumination → surface → scattering
→ optics → detector → analysis.

The use cases are **not independent**: they share common building blocks
(directional and spectral sources, surface generators, scattering models,
PSF propagation, analysis modules).  Each one ships as a self-contained
notebook unit under `notebooks/` (tutorial notebook + CLI script +
README) and has a dedicated page under `docs/use-cases/`.

## Industry alignment

The scenarios reflect current semiconductor manufacturing inspection:
incidence-angle control is fundamental to dark-field defect detection and
angle-resolved scatterometry (CD metrology); coherence modelling addresses
speckle noise in laser-based DUV inspection tools; spherical wavefronts
enable divergent point-source models for proximity inspection and
structured light.

---

## Use Case 1 — Surface Defect Inspection

Automated optical inspection (AOI): a camera images a manufactured part
under controlled illumination and software detects surface defects
(scratches, particles, dents, roughness anomalies, stains).  Common in
semiconductor, automotive, and consumer-goods manufacturing.

### Objective

Detect defects on a surface — dents, pits, cracks, stains — and make a
pass/fail decision.  Illustrates the canonical end-to-end chain and how
illumination geometry (bright-field vs. dark-field) changes defect
visibility.

### Workflow

```
Configure illumination (ring light / dark-field / bright-field)
    → Place part (surface with known or unknown defects)
    → Capture image through optics + detector
    → Analyse for defects (segmentation, classification)
    → Pass / fail decision
```

### What it demonstrates

- Defect-specific surface generators (`DentSurface`, `PitSurface`,
  `CrackSurface`, `StainSurface`) and directional illumination
  (`bright_field`, `dark_field`, `ring_light`)
- `DefectAnalyzer` for blob/scratch segmentation, contrast, and pass/fail
- The full pipeline orchestrated by `SimulationPipeline`

### Learn more

- [Use-case documentation](uc1-surface-defect-inspection.md)
- [Notebook unit](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/tree/main/notebooks/01_surface_defect_inspection/)

---

## Use Case 2 — Multi-Spectral Material Identification

Illuminate a surface at multiple discrete wavelengths, measure the
reflected intensity at each, and use the spectral signature to identify
the material.  Applications: recycling sorters, mineral identification,
food quality inspection, pharmaceutical verification.

### Objective

Build a spectral stack, extract per-pixel spectral vectors, and classify
each pixel against a reference library — showing that material identity
comes from a vector of reflectance values, not a single grayscale image.

### Workflow

```
Configure multi-wavelength source (N discrete channels)
    → For each wavelength:
        → Generate light field at λ_i
        → Evaluate scattering (wavelength-dependent albedo)
        → Capture with detector
    → Assemble spectral response vector R(λ_i)
    → Classify material against spectral library
```

### What it demonstrates

- Multi-channel light fields and multi-wavelength sources
  (`MultiChannelLightField`, `MultiSpectralSource`, `FilterWheelSource`)
- `SpectralAnalyzer` (spectral angle mapping, band ratios, classification)
- Optional colour-filter-array path via `CFAConfig` / `CFADetector`

### Learn more

- [Use-case documentation](uc2-multispectral-identification.md)
- [Notebook unit](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/tree/main/notebooks/02_multispectral_identification/)

---

## Use Case 3 — Sensor Performance Characterization

Characterise a simulated detector's performance: photon transfer curve
(PTC), signal-to-noise ratio vs. illumination, dynamic range, linearity,
noise floor, and full-well capacity verification.  Essential for camera
designers and system integrators choosing a sensor.

### Objective

Run a flat-field illumination sweep and turn sensor physics into
engineering metrics: gain (e⁻/ADU), read noise, full-well capacity,
dynamic range, and linearity error.

### Workflow

```
Configure detector under test
    → Generate flat-field illumination at stepped intensities
    → Capture N frames per intensity level
    → For each level: compute mean signal, variance, SNR
    → Plot PTC (log variance vs log mean)
    → Report: dynamic range, gain (e⁻/ADU), read noise, FWC, linearity
```

### What it demonstrates

- Stepped flat-field illumination (`FlatFieldSource`) and the CMOS
  detector noise pipeline
- `PTCAnalyzer`, `DynamicRangeAnalyzer`, `LinearityTestAnalyzer`,
  `SNRAnalyzer`
- Standard test charts: `siemens_star()`, `slanted_edge()`,
  `greyscale_wedge()`

### Learn more

- [Use-case documentation](uc3-sensor-characterization.md)
- [Notebook unit](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/tree/main/notebooks/03_sensor_characterization/)

---

## Use Case 4 — Angle-Resolved Scattering Measurement

Simulate a goniometric scatterometer: incident and/or view angle are
swept systematically and the scattered radiance is recorded at each
configuration.  The resulting angle-resolved data characterises the BRDF
of a surface.  Applications: material science, quality control of
coatings, BRDF database generation for rendering.

### Objective

Sweep the reflection angle at a fixed incidence, record the scattered
radiance, and fit a BRDF-like model to the angle-resolved data — the
basis for material and coating characterisation.

### Workflow

```
Configure source + surface + detector
    → For each incident angle θ_i (sweep):
        → For each view angle θ_r (sweep):
            → Evaluate scattering
            → Record: θ_i, θ_r, φ_diff, radiance
    → Output: BRDF table or polar plot
    → (Optional) Fit model parameters to measured data
```

### What it demonstrates

- Microfacet scattering models (`BeckmannScattering`, `GGXScattering`)
- `GoniometricSweep` for angle-resolved data and `BRDFFitter` for
  least-squares model fitting
- Cross-model parameter comparison via `ScatteringSweep`

### Learn more

- [Use-case documentation](uc4-angle-resolved-scattering.md)
- [Notebook unit](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/tree/main/notebooks/04_angle_resolved_scattering/)

---

## Use Case 5 — Structured Light 3D Scanning

Project a known pattern (sinusoidal fringes, Gray code, random dots) onto
a surface, capture the deformed pattern with a camera, and reconstruct the
3D surface shape from the pattern deformation.  Applications: metrology,
reverse engineering, quality control, face scanning.

### Objective

Reconstruct a 3D surface from deformed fringe patterns: extract the
wrapped phase, unwrap it, and triangulate to a height map, then compare
the reconstruction to ground truth.

### Workflow

```
Configure projector + camera system (baseline, angles)
    → Generate fringe patterns at N phase shifts
    → For each pattern: project onto surface, capture deformed pattern
    → Extract wrapped phase (Fourier or phase-shifting)
    → Unwrap phase (spatial or temporal)
    → Reconstruct height from phase → disparity map
    → Compare reconstructed height to ground truth
```

### What it demonstrates

- Phase-shifted fringe projection (`FringeProjector`)
- The phase → geometry chain: `PhaseExtractor`, `PhaseUnwrapper`,
  `HeightReconstructor`
- Ground-truth comparison via `SurfaceComparator` (RMS error)

### Learn more

- [Use-case documentation](uc5-structured-light-3d.md)
- [Notebook unit](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/tree/main/notebooks/05_structured_light_3d/)

---

## Use Case 6 — LiDAR Range Finding

Simulate a pulsed laser rangefinder: a laser pulse is emitted, reflects
off a surface, and a portion of the return pulse is detected.  Distance
is calculated from time-of-flight.  Applications: autonomous vehicles,
robotics, surveying, atmospheric sensing.

### Objective

Walk the full ranging chain — received power from the range equation,
round-trip time-of-flight, detection of a noisy return, and conversion of
range/angle into a point cloud — showing that distance is derived from
waveform analysis, not a single value.

### Workflow

```
Configure laser source (pulse energy, width, repetition rate)
    → Define target surface (range, reflectance, angle)
    → Compute received power via LiDAR range equation
    → Add noise (ambient light, detector dark count, jitter)
    → Detect pulse (threshold crossing, peak detection, centroid)
    → Compute range = c × ToF / 2
    → (Scanning) Repeat at each beam position
    → Output: point cloud (x, y, z, intensity)
```

### What it demonstrates

- The LiDAR range equation (`LiDARRangeEquation`) and time-of-flight
  propagation (`TimeOfFlightPropagator`)
- Waveform analysis (`WaveformAnalyzer`) and point-cloud generation
  (`generate_point_cloud`)
- Optional photon-counting path via `SPADDetector`; particle scattering
  via `RayleighScattering` / `MieScattering`

### Learn more

- [Use-case documentation](uc6-lidar-ranging.md)
- [Notebook unit](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/tree/main/notebooks/06_lidar_ranging/)

---

## Use Case 7 — Wafer Metrology

Covers semiconductor packaging and lithography inspection.  Two related
scenarios share one notebook unit.

### Scenario 7a — Die Alignment

In semiconductor packaging, chips (dies) are placed onto substrate tracks
or fiducial marks.  An optical inspection system measures the position of
each chip relative to the expected location, detecting translation
(dx, dy), rotation (dθ), and scale errors.

**Objective:** register a test image against a reference wafer pattern,
estimate translation offsets, and summarise the result with statistical
process-control metrics.

```
Define nominal pattern (fiducial marks, track layout, chip outline)
    → Generate surface with known misalignment (dx, dy, dθ, scale)
    → Capture image through inspection optics
    → Measure actual positions (template matching, edge detection)
    → Compare to nominal → compute error vector
    → Report: dx, dy, dθ, Cpk, pass/fail
```

**What it demonstrates:** `WaferSurface` / `MisalignedSurface`
generators, `TemplateMatcher`, `RegistrationAnalyzer`, `SPCAnalyzer`.

- [Alignment documentation](uc7-alignment.md)

### Scenario 7b — ASML-Style Defect Capstone

A high-end semiconductor metrology workflow combining wafer pattern,
engineered surface roughness, coherent speckle noise, defect detection,
and signal-to-noise analysis — inspired by wafer inspection in ASML-style
lithography systems.

**Objective:** show how surface roughness, speckle, and exposure choices
interact with defect detection and SNR in a realistic inspection context.

**What it demonstrates:** `WaferSurface` + `RoughSurface`, coherent
`SpeckleNoise`, `DefectAnalyzer` / `ErrorMapAnalyzer` /
`SNRAnalyzer` / `SpeckleRoughnessEstimator`.

- [Capstone documentation](uc7-defect-capstone.md)

### Learn more

- [Notebook unit](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/tree/main/notebooks/07_wafer_metrology/)
