# Use-Case-Driven Extension Roadmap

> **Target audience:** Product managers, R&D leads, simulation engineers,
> and anyone planning the future direction of the framework.

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

### Effort estimate

- **Shared prerequisites**: Angular sources (medium) — needed by UC4, UC5
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

### Gaps and Required Extensions

| Gap | Extension needed | Shared with |
|---|---|---|
| **Divergent / finite-distance source** | Direction varies across grid (point source, converging/diverging beam) | UC1, UC5, UC6 |
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
| **Divergent projection** | Projector model with fan-out geometry | UC4, UC6 |
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
|---|---|---|
| **Angular / divergent sources** (non-collimated direction maps) | UC1, UC4, UC5, UC6 | Medium |
| **Coordinate transforms** (surface rotation, tilt, arbitrary pose) | UC1, UC4, UC5, UC7 | Medium |
| **Multi-channel / spectral light field** (wavelength stacks) | UC2 | Medium |
| **Spectral material model** (wavelength-dependent reflectance) | UC2, UC4 | Low |
| **Flat-field / stepped-intensity source** | UC3, UC6, UC7 | Low |
| **Template matching / pattern analysis** | UC1, UC7 | Medium |
| **Surface comparison / registration** | UC5, UC7 | Medium |

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
```

---

## Suggested Implementation Roadmap

### Phase 1 — Foundational (shared infrastructure)
1. Angular / divergent source model
2. Coordinate transforms for surfaces
3. Flat-field / stepped-intensity source
4. Spectral material model

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
