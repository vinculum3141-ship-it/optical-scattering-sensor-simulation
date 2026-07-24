# Extension Roadmap — Task Tracker

> Auto-generated from `docs/use-cases.md`. Update this file as work
> progresses. Each task should be toggled between `[ ]` (pending),
> `[x]` (completed), or `[~]` (in progress).

---

## Phase 1 — Foundational Infrastructure

- [ ] **Angular / divergent source model** — non-collimated direction maps (UC1, UC4, UC5, UC6)
- [ ] **Coordinate transforms for surfaces** — rotation, tilt, arbitrary pose (UC1, UC4, UC5, UC7)
- [ ] **Flat-field / stepped-intensity source** — programmable uniform source (UC3, UC6, UC7)
- [ ] **Spectral material model** — wavelength-dependent reflectance curves (UC2, UC4)

## Phase 2a — Surface Defect Inspection (UC1)

- [ ] Directional illumination models (ring light, dark-field, bright-field)
- [ ] Defect-specific surface generators (dents, pits, burrs, cracks, stains)
- [ ] Defect detection analysis module (blob finder, scratch segmentation)
- [ ] Pass/fail decision logic
- [ ] Tiled acquisition / multi-FOV stitching helper
- [ ] Robot Framework tests for defect inspection workflow
- [ ] Integration test: end-to-end defect inspection simulation

## Phase 2b — Sensor Performance Characterization (UC3)

- [ ] Photon transfer curve analysis module (variance vs. mean)
- [ ] SNR analysis module (signal / noise vs. intensity)
- [ ] Dynamic range calculation
- [ ] Linearity test module (% deviation from ideal)
- [ ] Standard test chart generators (Siemens star, slanted edge, greyscale wedge)
- [ ] Robot Framework tests for sensor characterisation
- [ ] Integration test: PTC + SNR end-to-end

## Phase 2c — Wafer Chip Misalignment Detection (UC7)

- [ ] Wafer-specific surface generators (fiducial marks, chip arrays)
- [ ] Misalignment models (translation, rotation, scale errors)
- [ ] Template matching analysis module (normalised cross-correlation)
- [ ] Edge detection / fiducial finding (sub-pixel, Hough transform)
- [ ] Registration / overlay analysis (nominal vs. measured positions)
- [ ] Statistical process control output (Cpk, mean shift, trend)
- [ ] Real-time performance model (latency budget, throughput)
- [ ] Robot Framework tests for wafer inspection workflow
- [ ] Integration test: misaligned chip detection end-to-end

## Phase 2d — Multi-Spectral Material Identification (UC2)

- [ ] Multi-channel light field (wavelength stack, shape H×W×N_λ)
- [ ] Multi-wavelength source (programmable filter wheel / AOTF)
- [ ] Spectral analysis module (ratio metrics, spectral angle mapper)
- [ ] Colour filter array model (Bayer pattern + demosaicing)
- [ ] Material classification output (label + confidence)
- [ ] Robot Framework tests for spectral identification workflow
- [ ] Integration test: multi-spectral material ID end-to-end

## Phase 2e — Angle-Resolved Scattering Measurement (UC4)

- [ ] Goniometric sweep workflow (auto-vary θ_i, θ_r, collect measurements)
- [ ] BRDF fitting analysis (fit model parameters to angle-resolved data)
- [ ] Polarised BRDF (Fresnel coefficients, Mueller matrix propagation)
- [ ] Standard reference materials (Spectralon, mirror)
- [ ] BSDF (transmissive scattering) model
- [ ] Angle-resolved output format (BRDF table, polar plot)
- [ ] Robot Framework tests for goniometric workflow
- [ ] Integration test: BRDF characterisation end-to-end

## Phase 2f — Structured Light 3D Scanning (UC5)

- [ ] Structured illumination source (fringe projection, phase-shifted patterns)
- [ ] Divergent projection model (projector fan-out geometry)
- [ ] Phase extraction analysis (phase-shifting algorithm, Fourier transform)
- [ ] Phase unwrapping (spatial flood-fill, multi-frequency temporal)
- [ ] Height reconstruction from phase → disparity map
- [ ] Projector-camera calibration model (intrinsic/extrinsic parameters)
- [ ] Surface comparison (RMS error map between reconstruction and ground truth)
- [ ] Robot Framework tests for structured light workflow
- [ ] Integration test: sinusoidal surface scan end-to-end

## Phase 2g — LiDAR Range Finding (UC6)

- [ ] Pulsed laser source (temporal pulse profile, peak power, PRR)
- [ ] Scanning mechanism (galvanometer, rotating polygon, MEMS mirror)
- [ ] LiDAR range equation implementation
- [ ] Time-of-flight propagation (time delay, pulse broadening, multiple returns)
- [ ] SPAD / Geiger-mode detector model (photon counting, dead time, jitter)
- [ ] Waveform analysis (peak detection, constant-fraction discriminator)
- [ ] Point cloud output data structure (x, y, z, intensity, timestamp)
- [ ] Atmospheric effects (extinction, backscatter, turbulence)
- [ ] Robot Framework tests for LiDAR workflow
- [ ] Integration test: LiDAR range measurement end-to-end

## Phase 3 — Consolidation

- [ ] End-to-end demo scripts for each use case
- [ ] Jupyter notebooks for each use case
- [ ] Integration tests covering multi-step workflows
- [ ] Performance benchmarks (grid scaling, convolution speed)
- [ ] User documentation for each use case in `docs/`
