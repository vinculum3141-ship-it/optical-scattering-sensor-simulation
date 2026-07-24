# Extension Roadmap — Task Tracker

> Auto-generated from `docs/use-cases.md`. Update this file as work
> progresses. Each task should be toggled between `[ ]` (pending),
> `[x]` (completed), or `[~]` (in progress).

---

## Phase 1 — Foundational Infrastructure

- [~] **Angular / divergent source model** — non-collimated direction maps (UC1, UC4, UC5, UC6). Partially closed: spherical wavefront implemented; still needed: converging beam, configurable waist position, Gaussian beam propagation
- [ ] **Coordinate transforms for surfaces** — rotation, tilt, arbitrary pose (UC1, UC4, UC5, UC7)
- [ ] **Flat-field / stepped-intensity source** — programmable uniform source (UC3, UC6, UC7)
- [ ] **Spectral material model** — wavelength-dependent reflectance curves (UC2, UC4)

### Phase 1 — Completed

- [x] **Incidence angle convenience** — `source.incidence_angle` / `incidence_angle_degrees` on LightSource (UC1, UC4)
- [x] **Coherence / speckle model** — `SpeckleNoise` detector noise model, `Surface.phase_screen()`, pipeline integration (UC1, UC7)
- [x] **Spherical wavefront** — `source.wavefront = "spherical"` with per-pixel direction from origin (UC1, UC4, UC5, UC6)
- [x] **Cook-Torrance microfacet BRDF** — full physically based specular model with Beckmann D, Schlick F, Smith G; Lambertian diffuse term for energy conservation (UC1, UC4)

### Pre-deployment gaps — add before the relevant use case

The following should be implemented **just before** (not ahead of) the use case that first needs them:

- [ ] **Pulsed source model** (standalone, needed by UC6 LiDAR) — temporal pulse envelope (Gaussian/rectangular), pulse energy, peak power, repetition rate. Add as a `TemporalEnvelope` class composed into `Laser` when UC6 is activated.
- [ ] **Source extent model** (standalone, needed by UC5 Structured Light) — extended source aperture, partially coherent extended sources. Add as a `SourceExtent` class when UC5 is activated.
- [ ] **Spectral quantum efficiency** `QE(λ)` (needed by UC3 Sensor Char first, then UC2 Multi-Spectral) — change `CMOSDetector.quantum_efficiency` from a single float to a callable `QE(wavelength)` or interpolated curve. Enables wavelength-dependent photoresponse for multi-spectral simulation.
- [ ] **Thin-film interference model** (needed by UC1 Defect Inspection) — model for reflectance/transmittance of single or multi-layer coatings as a function of wavelength, incidence angle, and film thickness. Relevant for semiconductor coatings inspection and anti-reflection layer characterisation.
- [ ] **Gaussian beam divergence / waist propagation** (needed by UC6 LiDAR) — functional wiring of the stored `divergence` parameter to compute beam waist at range, spot size at target surface, and intensity falloff with distance. Partially closes the remaining divergent-source gap.
- [ ] **Optical throughput / radiometric scaling** (needed by UC3 Sensor Char first) — the propagator currently converts scattered radiance (W·m⁻²·sr⁻¹) to sensor irradiance (W/m²) by PSF convolution alone, without accounting for the optical system's throughput.  Absent this, absolute irradiance values are incorrect for SNR, PTC, or any physically calibrated measurement.

  **What to change:**
  `OpticalPropagator.propagate()` must scale the convolved irradiance by the system's collection efficiency.  For a simple paraxial model the throughput is:

      τ = π · (D/(2f))² = π · NA²

  (the solid angle subtended by the exit pupil from the image plane, assuming no vignetting or transmission loss).

  Implementation sketch:
  ```python
  def propagate(self, scattered_field, optical_system):
      radiance = np.asarray(scattered_field.radiance, dtype=float)
      psf = self._get_psf(optical_system)
      convolved = self._convolve(radiance, psf)
      na = optical_system.numerical_aperture
      irradiance = convolved * (np.pi * na ** 2)
      return SensorField(irradiance=irradiance, ...)
  ```

  The same factor should be applied regardless of PSF model.  Later extensions (vignetting, obscuration, coating transmission) can be added as multiplicative correction maps.

  **Side effect:** fixes `AiryPSF` being decoupled from `OpticalSystem` — the `_get_psf()` helper should pass `optical_system.wavelength` and `optical_system.numerical_aperture` to the PSF kernel so both PSFs are consistent with the system they belong to.

- [ ] **Optical magnification / field mapping** (needed by UC7 Wafer Alignment first, then UC5 Structured Light) — `OpticalSystem.magnification` is stored but never used by the propagator.  The scattered field and sensor field currently share identical pixel dimensions, which is incorrect for any system with non-unity magnification.

  **What to change:**
  `OpticalPropagator.propagate()` must resample the scattered radiance to account for magnification before convolution.  For a system with magnification M:

      sensor_pixel_spacing = object_pixel_spacing / M

  The radiance map should be scaled (resampled) so that features in object space map to the correct size in sensor space.  Simple implementation uses `scipy.ndmap.zoom` or `np.interp` along each axis; a future FFT-based propagator can incorporate magnification directly in the Fourier scaling.

  Implementation sketch:
  ```python
  from scipy.ndimage import zoom

  M = optical_system.magnification
  if abs(M - 1.0) > 1e-6:
      scaled = zoom(radiance, M, order=1)  # bilinear interpolation
  else:
      scaled = radiance
  # then apply PSF convolution on scaled
  ```

  **Edge cases:** M < 1 (demagnification, minifying), M > 1 (magnifying), non-integer scaling factors.  The zoom factor must preserve total energy (irradiance × area should be conserved).

- [ ] **Zernike wavefront → PSF model** (needed by UC1 Defect Inspection with aberrated objectives, then UC7 Wafer Alignment for telecentric lens characterisation) — currently `OpticalSystem.aberrations` is an empty dict placeholder with no associated model.  The physically correct approach models wavefront error via Zernike polynomials and computes the PSF from the generalised pupil function.

  **Design:**
  ```
  Zernike coefficients (z4, z7, z11, ...)
          ↓
  Wavefront error map W(ρ, θ) over the pupil
          ↓
  Generalised pupil function P(ρ, θ) = A(ρ, θ) · exp(i · 2π/λ · W(ρ, θ))
          ↓
  FFT of P → Coherent PSF (amplitude)
          ↓
  |FFT(P)|² → Incoherent PSF (intensity)
          ↓
  Convolution with scattered radiance
  ```

  **What to add:**
  1. `ZernikePolynomials` — evaluate individual Zernike modes (Noll indexing) on a pupil grid.  Self-contained implementation using `math`/`numpy` only (no PyZDEP dependency needed).
  2. `Wavefront` — container for Zernike coefficients, method `map(pupil_grid) → np.ndarray` returning wavefront error in metres.
  3. `ZernikePSF` — PSF model implementing the same `kernel(size, optical_system)` interface as `GaussianPSF` and `AiryPSF`.  Internally:
      - Build pupil coordinate grid (size × size, normalised to unit radius)
      - Evaluate wavefront error from coefficients
      - Build `P = exp(i·2π/λ·W)` within the pupil (zero outside)
      - FFT → intensity → normalise to unit sum
  4. Update `OpticalSystem.__post_init__` to accept a `Wavefront` object; the propagator passes it through when generating the PSF.

  **Parameters of `ZernikePSF`:**
  ```python
  class ZernikePSF:
      def __init__(self, wavefront: Wavefront, wavelength: float, numerical_aperture: float):
          ...
      def kernel(self, size: int = 31) -> np.ndarray:
          ...
  ```

  **Edge cases:** pupil radius must fit within the kernel; zero coefficients → diffraction-limited (Airy) PSF; undersampled pupil (too few pixels across the pupil diameter) will alias the PSF.

  **Trigger:** implement when a use case requires simulating a specific optical defect (e.g. spherical aberration in a high-NA microscope objective for UC1, or field curvature in a wafer inspection tool for UC7).

## Phase 2a — Surface Defect Inspection (UC1)

- [ ] **RayleighScattering / MieScattering** (skeletons in `scattering/particle.py`) — implement when particle-contamination scattering is needed for defect inspection
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

- [ ] **BeckmannScattering** — implement full model (skeleton exists in `scattering/beckmann.py`, uses `distribution_beckmann()` from `cooktorrance.py`) — needed as a candidate model in BRDF fitting
- [ ] **GGXScattering** — implement full model (skeleton exists in `scattering/ggx.py`, uses GGX distribution D = α² / (π((n·h)²(α²-1)+1)²)) — needed as a candidate model in BRDF fitting
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

- [ ] **RayleighScattering** — implement full model (skeleton exists in `scattering/particle.py`) — needed for atmospheric molecular backscatter (∝ 1/λ⁴)
- [ ] **MieScattering** — implement full model (skeleton exists in `scattering/particle.py`, requires Mie-theory computation for size parameter x = 2πr/λ) — needed for aerosol and droplet scattering
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

## Before Phase 2 — final architecture review pass

Run this **after completing all module reviews** (illumination, surface,
scattering, optics, detector, analysis) and **before starting any use
case implementation**.

- [ ] Update `README.md` — refresh file reference table, test counts,
      document new classes (`ImportedSurface`, `SpeckleNoise`,
      `wavefront`, `incidence_angle`, etc.)
- [ ] Review and update all package `__init__.py` exports for consistency
- [ ] Verify every `__all__` list matches actual public API
- [ ] Run full test suite and update any stale line/class references
      in docstrings

## Phase 3 — Consolidation

- [ ] End-to-end demo scripts for each use case
- [ ] Jupyter notebooks for each use case
- [ ] Integration tests covering multi-step workflows
- [ ] Performance benchmarks (grid scaling, convolution speed)
- [ ] User documentation for each use case in `docs/`
