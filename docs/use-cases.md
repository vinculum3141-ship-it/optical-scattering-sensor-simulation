# Use-Case-Driven Extension Roadmap

> **Target audience:** Product managers, R&D leads, simulation engineers,
> and anyone planning the future direction of the framework.
>
> **Industry alignment note:** Additions in this iteration — incidence
> angle convenience, coherence/speckle model, and spherical wavefront —
> are all directly relevant to **semiconductor manufacturing inspection**.
> Incidence angle control is fundamental to dark-field defect detection
> and angle-resolved scatterometry (CD metrology). Coherence modelling
> addresses speckle noise in laser-based DUV inspection tools (e.g.
> KLA, Applied Materials). Spherical wavefronts enable divergent
> point-source models for proximity inspection and structured light.

## Overview

This document defines seven concrete application use cases that serve as
extension drivers for the framework. Each use case describes a real-world
sensing scenario, maps existing capabilities to it, identifies gaps, and
specifies the new models, workflows, or analyses required.

The use cases are **not** independent — they share common building blocks
(directional sources, spectral stacks, analysis modules). Implementing
shared infrastructure first (the "core gaps") will unlock multiple use
cases at once.

---

## Use Case 1: Surface Defect Inspection Workcell

### Description

Automated optical inspection (AOI) station: a camera images a manufactured
part under controlled illumination, and software detects surface defects
(scratches, particles, dents, roughness anomalies, stains). Common in
semiconductor, automotive, and consumer-goods manufacturing.

### Workflow

```
Configure illumination (ring light / dark-field / bright-field)
    → Place part (surface with known or unknown defects)
    → Capture image through optics + detector
    → Analyse for defects (segmentation, classification)
    → Pass / fail decision
```

### Existing Coverage

| Component | Status |
|---|---|
| Surface generators | `ScratchedSurface`, `ParticleSurface`, `RoughSurface` exist |
| Scattering models | Lambertian, Phong, Oren-Nayar available |
| Imaging optics | PSF propagator, CMOS detector pipeline |
| Analysis | ContrastAnalyzer, HistogramAnalyzer |

### Gaps and Required Extensions

| Gap | Extension needed | Shared with |
|---|---|---|
| Directional / structured illumination (ring light, dark-field, grazing) | Angular source models with configurable direction maps | UC4, UC5 |
| Defect-specific surface shapes (dents, pits, burrs, stains, cracks) | `DentSurface`, `StainSurface`, `CrackSurface` generators | — |
| Defect detection analysis (blob finder, scratch segmentation, anomaly detection) | `DefectAnalyzer` module | — |
| Pass/fail decision logic | Threshold-based or ML-based classification output | UC7 |
| Surface scanning / stage motion | Tiled acquisition, multi-FOV stitching | UC6, UC7 |

### Additions in this iteration

| Addition | Benefit for UC1 |
|---|---|
| **Incidence angle property** (`source.incidence_angle_degrees`) | Enables quick switching between bright-field (0°) and dark-field/grazing (>45°) illumination — key for highlighting scratches and particles |
| **Speckle noise** (`SpeckleNoise` + `coherence_length`) | Adds realistic speckle when using a laser source; defect visibility changes under coherent vs. incoherent illumination — critical for semiconductor AOI |
| **Spherical wavefront** (`source.wavefront = "spherical"`) | Models a point source at finite distance — direction varies per pixel. Enables divergent dark-field illumination from a near-field emitter. Partially addresses the "divergent source" gap |

### Effort estimate

- **Shared prerequisites**: Angular sources (medium) — needed by UC4, UC5. Spherical wavefront partially closes this gap.
- **Use-case-specific**: Defect generators (low), defect analysis (medium),
  pass/fail logic (low)

---

## Use Case 2: Multi-Spectral Material Identification

### Description

Illuminate a surface at multiple discrete wavelengths, measure the
reflected intensity at each, and use the spectral signature to identify
the material. Applications: recycling sorters, mineral identification,
food quality inspection, pharmaceutical verification.

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

### Existing Coverage

| Component | Status |
|---|---|
| Sources at different λ | Any source can be created at any wavelength |
| Material | `Material` class exists (name + refractive index) |
| Analysis measurements | Dict-based output, extensible |

### Gaps and Required Extensions

| Gap | Extension needed | Shared with |
|---|---|---|
| Multi-channel light field | `LightField` stack with shape `(H, W, N_λ)` | — |
| Wavelength-dependent albedo / reflectance | `SpectralMaterial` with reflectance curve `R(λ)` | UC4 |
| Spectral analysis module | Ratio metrics, spectral angle mapper (SAM), library comparison | — |
| Multi-wavelength source | Programmable filter wheel / AOTF / monochromator source | — |
| Colour filter array on detector | Bayer pattern + demosaicing | — |
| Classification output | Material label + confidence score | — |

### Effort estimate

- **Shared prerequisites**: Spectral stacks (medium), spectral materials (low)
- **Use-case-specific**: Spectral analysis (medium), CFA/demosaicing (medium)

---

## Use Case 3: Sensor Performance Characterization

### Description

Characterise a simulated detector's performance metrics: photon transfer
curve (PTC), signal-to-noise ratio vs. illumination, dynamic range,
linearity, noise floor, full-well capacity verification. Essential for
camera designers and system integrators choosing a sensor.

### Workflow

```
Configure detector under test
    → Generate flat-field illumination at stepped intensities
    → Capture N frames per intensity level
    → For each level: compute mean signal, variance, SNR
    → Plot PTC (log variance vs log mean)
    → Report: dynamic range, gain (e⁻/ADU), read noise, FWC, linearity
```

### Existing Coverage

| Component | Status |
|---|---|
| CMOS detector pipeline | Complete (shot noise, dark current, read noise, FWC, ADC) |
| Built-in noise models | FPN, PRNU, hot pixels, column defects, dead pixels |
| Analysis | ContrastAnalyzer, SaturationAnalyzer, HistogramAnalyzer |
| Variable exposure / gain | Parameters are configurable |

### Gaps and Required Extensions

| Gap | Extension needed | Shared with |
|---|---|---|
| Stepped flat-field source | `FlatFieldSource` with programmable intensity levels | UC6, UC7 |
| Multiple-frame capture | Burst / sequence mode on detector | UC6 |
| Photon transfer curve analysis | `PTCAnalyzer` (variance vs. mean, linearity fit) | — |
| SNR analysis | `SNRAnalyzer` (signal / noise vs. intensity) | — |
| Dynamic range calculation | Ratio of saturation level to noise floor | — |
| Linearity test | Deviation from best-fit line, % non-linearity | — |
| Standard test charts | Siemens star, slanted edge, greyscale step wedge | — |

### Effort estimate

- **Shared prerequisites**: Flat-field source (low)
- **Use-case-specific**: PTC/SNR analysers (medium), test charts (medium)

---

## Use Case 4: Angle-Resolved Scattering Measurement

### Description

Simulate a goniometric scatterometer: incident angle and/or view angle
are swept systematically, and the scattered radiance is recorded at each
configuration. The resulting angle-resolved data characterises the BRDF
of a surface. Applications: material science, quality control of
coatings, BRDF database generation for rendering.

### Workflow

```
Configure source + surface + detector
    → For each incident angle θ_i (sweep):
        → Set source direction
        → For each view angle θ_r (sweep):
            → Set view direction
            → Evaluate scattering
            → Record: θ_i, θ_r, φ_diff, radiance
    → Output: BRDF table or polar plot
    → (Optional) Fit model parameters to measured data
```

### Existing Coverage

| Component | Status |
|---|---|
| Source direction | Configurable (constant across grid) |
| View direction | Configurable (constant across grid) |
| Scattering models | Lambertian, Phong, Oren-Nayar |
| Surface with normals | Full surface geometry pipeline |

### Additions in this iteration

| Addition | Benefit for UC4 |
|---|---|
| **Incidence angle property** (`source.incidence_angle_degrees`) | Directly enables the goniometric sweep: ``for θ in range(0, 90, 5): source.incidence_angle_degrees = θ`` — replaces manual propagation_direction vector construction |
| **Spherical wavefront** (`source.wavefront = "spherical"`) | Enables finite-distance source for goniometric sweeps; direction varies across grid for realistic near-field scattering |

### Gaps and Required Extensions

| Gap | Extension needed | Shared with |
|---|---|---|
| **Divergent / finite-distance source** (partially closed) | Spherical wavefront addresses fixed point-source geometry; still needed: converging/diverging beam control, configurable waist | UC1, UC5, UC6 |
| Goniometric sweep workflow | Loop over angles, collect measurements into structured output | — |
| BRDF fitting analysis | Fit model parameters (albedo, roughness, shininess) to angle data | — |
| Polarized BRDF | Fresnel coefficients, Mueller matrix propagation | — |
| Standard reference materials | Spectralon (Lambertian), mirror (specular) as built-in | — |
| BSDF (transmissive) | Scattering for transmitted light through translucent materials | — |
| Coordinate transforms | Surface rotation, tilt, arbitrary orientation | UC1, UC5, UC7 |

### Effort estimate

- **Shared prerequisites**: Divergent sources (medium), coordinate transforms (medium)
- **Use-case-specific**: Sweep workflow (low), BRDF fitting (medium), polarized BRDF (high)

---

## Use Case 5: Structured Light 3D Scanning

### Description

Project a known pattern (sinusoidal fringes, Gray code, random dots) onto
a surface, capture the deformed pattern with a camera, and reconstruct the
3D surface shape from the pattern deformation. Applications: metrology,
reverse engineering, quality control, face scanning.

### Workflow

```
Configure projector + camera system (baseline, angles)
    → Generate fringe patterns at N phase shifts
    → For each pattern:
        → Project onto surface (structured illumination)
        → Capture deformed pattern with camera
    → Extract wrapped phase (Fourier or phase-shifting)
    → Unwrap phase (spatial or temporal)
    → Reconstruct height from phase → disparity map
    → Compare reconstructed height to ground truth
```

### Existing Coverage

| Component | Status |
|---|---|
| Sinusoidal surface | `SinusoidalSurface` generator (for ground truth) |
| Imaging model | Optics + detector pipeline |
| Height maps | Grid-based, analysable |

### Gaps and Required Extensions

| Gap | Extension needed | Shared with |
|---|---|---|
| **Structured illumination source** | Project fringe/pattern as illumination, not analytic profile | UC1 (patterned light) |
| **Divergent projection** (partially closed) | Spherical wavefront gives point-source fan-out; still needed: projector aperture model, Keystone distortion | UC4, UC6 |
| Phase extraction analysis | Phase-shifting algorithm (N-step), Fourier transform profilometry | — |
| Phase unwrapping | Spatial (flood-fill) or temporal (multi-frequency) unwrapping | — |
| Height reconstruction | Triangulation from phase → height, system calibration model | — |
| Projector-camera calibration | Intrinsic/extrinsic parameters of both devices | — |
| Surface comparison | RMS error map between reconstructed and ground truth | UC7 |

### Effort estimate

- **Shared prerequisites**: Divergent sources (medium), coordinate transforms (medium)
- **Use-case-specific**: Phase algorithms (high), calibration model (medium),
  height reconstruction (medium)

---

## Use Case 6: LiDAR Range Finding

### Description

Simulate a pulsed laser rangefinder: a laser pulse is emitted, reflects
off a surface, and a portion of the return pulse is detected. Distance
is calculated from time-of-flight. Applications: autonomous vehicles,
robotics, surveying, atmospheric sensing.

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

### Existing Coverage

| Component | Status |
|---|---|
| Laser source | `Laser` class exists (continuous-wave) |
| Surface reflectance | Albedo parameter |
| Detector noise | Read noise, dark current, shot noise |

### Gaps and Required Extensions

| Gap | Extension needed | Shared with |
|---|---|---|
| **Pulsed laser source** | Temporal pulse model (Gaussian, rectangular), peak power, pulse energy, repetition rate | — |
| **Scanning mechanism** | Galvanometer, rotating polygon, MEMS mirror, Risley prism | UC1 (tiled acquisition) |
| LiDAR range equation | `P_received = P_transmitted × (D²_r / (4π R⁴)) × ρ × cos(θ) × η_sys` (diffuse target) | — |
| **Time-of-flight propagation** | Time delay = 2R/c, pulse broadening, multiple returns | — |
| SPAD / Geiger-mode detector | Photon counting, dead time, afterpulsing, timing jitter | — |
| Waveform analysis | Peak detection, constant-fraction discriminator, centroid | — |
| Point cloud output | (x, y, z, intensity, timestamp) data structure | — |
| Atmospheric effects | Extinction, backscatter, turbulence (long-range) | — |
| **Divergent beam** | Beam divergence → spot size at target | UC4, UC5 |

### Effort estimate

- **Shared prerequisites**: Divergent sources (medium)
- **Use-case-specific**: Pulsed laser (medium), scanning (high), SPAD detector (high),
  ToF propagation (medium), waveform analysis (medium), point cloud (low)

---

## Use Case 7: Wafer Chip Misalignment Detection

### Description

In semiconductor packaging, chips (dies) are placed onto substrate tracks
or fiducial marks. An optical inspection system measures the position of
each chip relative to the expected location in real time, detecting
translation (dx, dy), rotation (dθ), and scale errors.

### Workflow

```
Define nominal pattern (fiducial marks, track layout, chip outline)
    → Generate surface with known misalignment (dx, dy, dθ, scale)
    → Capture image through inspection optics
    → Measure actual positions (template matching, edge detection)
    → Compare to nominal → compute error vector
    → Report: dx, dy, dθ, Cpk, pass/fail
```

### Existing Coverage

| Component | Status |
|---|---|
| High-resolution grid surface | Any surface generator |
| Imaging pipeline | Optics + detector |
| Analysis measurements | Dict-based output |

### Additions in this iteration

| Addition | Benefit for UC7 |
|---|---|
| **Speckle noise** (`SpeckleNoise`) | Semiconductor wafer inspection uses coherent DUV lasers — speckle is a primary noise source that limits overlay and CD measurement precision. The `SpeckleNoise` model captures this effect, enabling realistic simulations of alignment accuracy under shot-to-shot speckle variation |

### Gaps and Required Extensions

| Gap | Extension needed | Shared with |
|---|---|---|
| **Wafer / chip surface generators** | `FiducialSurface`, `ChipArraySurface` with programmable patterns, `MisalignedSurface` with dx/dy/dθ | — |
| **Template matching analysis** | Normalised cross-correlation, geometric pattern matching | UC1 (defect detection) |
| **Edge detection / fiducial finding** | Sub-pixel edge detection, blob centroiding, Hough transform | — |
| **Registration / overlay analysis** | Compare measured positions to nominal → error vector | UC5 (height comparison) |
| **Statistical process control output** | Cpk, mean shift, standard deviation, trend across multiple parts | — |
| **Real-time performance model** | Latency budget, processing pipeline, throughput estimation | — |
| **Defect classification per chip** | OK / reject / rework label per die | UC1 |

### Effort estimate

- **Shared prerequisites**: Coordinate transforms (medium), template matching (medium)
- **Use-case-specific**: Wafer generators (medium), registration analysis (medium),
  SPC output (low), real-time model (low)

---

## Shared Infrastructure Map

The following capabilities are needed by multiple use cases and should
be prioritised first:

| Capability | Needed by | Estimated effort |
|---|---|---|---|
| **Angular / divergent sources** (non-collimated direction maps) | UC1, UC4, UC5, UC6 | Medium (partially closed) |
| **Coordinate transforms** (surface rotation, tilt, arbitrary pose) | UC1, UC4, UC5, UC7 | Medium |
| **Multi-channel / spectral light field** (wavelength stacks) | UC2 | Medium |
| **Spectral material model** (wavelength-dependent reflectance) | UC2, UC4 | Low |
| **Flat-field / stepped-intensity source** | UC3, UC6, UC7 | Low |
| **Template matching / pattern analysis** | UC1, UC7 | Medium |
| **Surface comparison / registration** | UC5, UC7 | Medium |
| **Incidence angle convenience** (set source angle in degrees) | UC1, UC4 | Implemented |
| **Coherence / speckle model** (partial coherence, speckle noise) | UC1, UC7 | Implemented |
| **Spherical wavefront** (point source, per-pixel direction) | UC1, UC4, UC5, UC6 | Implemented |

---

## Dependency Graph

```
Angular sources ─┬─ UC1 (defect inspection)
                  ├─ UC4 (angle-resolved scattering)
                  ├─ UC5 (structured light)
                  └─ UC6 (LiDAR)

Coordinate transforms ─┬─ UC1 (defect inspection)
                        ├─ UC4 (angle-resolved scattering)
                        ├─ UC5 (structured light)
                        └─ UC7 (wafer alignment)

Spectral materials ─┬─ UC2 (multi-spectral ID)
                     └─ UC4 (angle-resolved BRDF)

Template matching ─┬─ UC1 (defect detection)
                     └─ UC7 (wafer alignment)

Incidence angle ─┬─ UC1 (dark-field/grazing illumination)
                  └─ UC4 (goniometric sweep)

Coherence / speckle ─┬─ UC1 (laser-based AOI realism)
                       └─ UC7 (DUV inspection noise floor)

Spherical wavefront ─┬─ UC1 (divergent dark-field)
                      ├─ UC4 (finite-distance source)
                      ├─ UC5 (projector fan-out)
                      └─ UC6 (beam divergence)
```

---

## Suggested Implementation Roadmap

### Phase 1 — Foundational (shared infrastructure)
1. Angular / divergent source model
2. Coordinate transforms for surfaces
3. Flat-field / stepped-intensity source
4. Spectral material model

**Completed (this iteration):**
- **Incidence angle convenience** — `source.incidence_angle` / `incidence_angle_degrees` property on `LightSource`
- **Coherence / speckle model** — `SpeckleNoise` detector noise model, `Surface.phase_screen()` method, pipeline integration
- **Spherical wavefront** — `source.wavefront = "spherical"` with per-pixel direction from origin (partially closes the divergent source gap)

### Phase 2 — Use-case delivery (pick order by priority)
The use cases are largely independent once Phase 1 is complete.
Suggested order based on complexity:

| Order | Use case | Key deliverables | Est. effort |
|---|---|---|---|
| 1 | **Sensor Characterization (UC3)** | PTC/SNR analysers, test charts | Medium |
| 2 | **Defect Inspection (UC1)** | Defect generators, defect analysis, pass/fail | Medium |
| 3 | **Wafer Alignment (UC7)** | Wafer surface generators, template matching, registration, SPC | Medium |
| 4 | **Multi-spectral ID (UC2)** | Spectral stacks, spectral analysis, classification | Medium |
| 5 | **Angle-Resolved Scattering (UC4)** | Sweep workflow, BRDF fitting, polarized BRDF | Medium-high |
| 6 | **Structured Light 3D (UC5)** | Phase algorithms, calibration, height reconstruction | High |
| 7 | **LiDAR (UC6)** | Pulsed laser, scanning, SPAD detector, ToF, point cloud | High |

### Phase 3 — Consolidation
- End-to-end demo scenarios for each use case
- Integration tests covering multi-step workflows
- Performance benchmarks
- User documentation for each use case

---

## Learning & Playability Roadmap

This framework is built for **learning** — understanding how optical
metrology pipelines work by running and modifying real simulations.
Every use case should ship with **modular, fully playable notebooks and
Python scripts** that use ``optical_metrology`` as an **imported library**
(``pip install -e .`` in an environment).

### UC1 — Surface Defect Inspection
- **Notebook:** Walk through bright-field vs. dark-field vs. ring-light
  inspection of a scratched wafer.  Let the user toggle defect type
  (dent, pit, crack, stain), illumination geometry, and threshold to
  see pass/fail flip in real time.
- **Script:** ``python -m examples.run_uc1_inspection --defect scratch --illumination darkfield``
- **Interactive:** Sliders for scratch depth, incidence angle, detector
  noise level.

### UC2 — Multi-Spectral Material ID
- **Notebook:** Load a multi-spectral light field, sweep wavelengths,
  compute SAM per pixel, classify materials.  Let the user add reference
  spectra and see classification confidence maps update.
- **Script:** ``python -m examples.run_uc2_material_id --materials silicon,sio2,al``
- **Interactive:** Click on the image to add a reference spectrum.

### UC3 — Sensor Characterisation
- **Notebook:** Generate flat-field images at increasing exposures,
  compute PTC, fit gain, plot variance vs. mean.  Show dynamic range
  and linearity error as adjustable exposure sweeps run.
- **Script:** ``python -m examples.run_uc3_sensor_char --exposure-range 1e-6 1e-3 --steps 20``
- **Interactive:** Slider for exposure time updates PTC plot live.

### UC4 — Angle-Resolved Scattering
- **Notebook:** Sweep incidence / reflection angles, collect BRDF
  table, fit Beckmann vs. GGX models, compare goodness-of-fit.
- **Script:** ``python -m examples.run_uc4_brdf --model beckmann --roughness 0.15``
- **Interactive:** 2D polar plot of BRDF that updates as roughness changes.

### UC5 — Structured Light 3D Scanning
- **Notebook:** Project fringe patterns onto a sinusoidal surface,
  extract phase, unwrap, reconstruct height, compare to ground truth.
- **Script:** ``python -m examples.run_uc5_structured_light --period 16 --phase-shifts 4``
- **Interactive:** Animate fringe projection and show phase map, height map,
  error map side-by-side.

### UC6 — LiDAR Range Finding
- **Notebook:** Simulate a LiDAR pulse, propagate to target at 50 m,
  detect return with SPAD, compute ToF, convert to point cloud.
- **Script:** ``python -m examples.run_uc6_lidar --range 50 --aerosol-density 1e5``
- **Interactive:** Drag the target distance slider and see received
  power, ToF histogram, and point cloud update in real time.

### UC7 — Wafer Alignment
- **Notebook:** Create a wafer with fiducial marks, apply misalignment,
  run template matching, measure dx/dy/rotation, compute Cpk.
- **Script:** ``python -m examples.run_uc7_alignment --dx 3 --dy -1 --rotation 0.5``
- **Interactive:** Drag misalignment sliders and watch the overlay
  error heatmap update.

### Deliverable Format
Each use case ships three things:

| Artifact | Description |
|----------|-------------|
| ``examples/uc<N>_playground.ipynb`` | Jupyter notebook with markdown narrative, side-by-side plots, interactive widgets |
| ``examples/run_uc<N>_pipeline.py`` | CLI script with argparse (``--help`` lists all knobs) |
| ``tests/test_uc<N>_integration.py`` | Existing pytest integration test (already done for all 7 UCs) |

The notebooks should be **self-contained** — they install nothing beyond
``pip install -e .`` in the venv, import ``optical_metrology``, and work.
Widget sliders (``ipywidgets``) are preferred for interactivity; if that
adds a dependency, use ``¶``-driven code cells the user can re-run with
different parameters.
