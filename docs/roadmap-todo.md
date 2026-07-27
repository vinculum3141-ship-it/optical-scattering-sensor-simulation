# Extension Roadmap — Task Tracker

> Auto-generated from `docs/use-cases.md`. Update this file as work
> progresses. Each task should be toggled between `[ ]` (pending),
> `[x]` (completed), or `[~]` (in progress).

---

## Phase 0 — Framework Finalisation

Turn the codebase into a proper installable scientific Python framework
before any use-case work begins.  These tasks are about identity,
packaging, and developer experience.

- [x] **Choose a project name** — ``optical-metrology`` (PyPI) / ``optical_metrology`` (Python import).  Updated package directory to ``src/optical_metrology/`` and all internal references.
- [x] **Production-grade ``pyproject.toml``** — filled in with author, description, keywords, classifiers, Python version bounds, and optional dependency groups (dev, analysis, visualisation, docs).
- [x] **``pip install`` workflow** — ``pip install -e .`` and ``pip install -e ".[dev]"`` verified from a clean venv.  Adopted ``src/`` layout.
- [x] **Continuous integration** — GitHub Actions workflow ``.github/workflows/ci.yml`` that runs pytest on every PR/push against Python 3.9–3.12.  CI badge added to README.
- [x] **Example Jupyter notebooks** — two created:
  - ``examples/basic_pipeline.ipynb`` — light → surface → scatter → optics → detector → image
  - ``examples/defect_inspection.ipynb`` — scratched surface with inspection (UC1)
- [~] **Documentation site** — all markdown content in ``docs/`` updated with new import paths.  GitHub Pages deployment (``mkdocs`` + ``mkdocstrings``) deferred.
- [x] **License** — MIT license file already present.
- [x] **Contributing guide** — ``CONTRIBUTING.md`` with setup steps, test commands, and PR workflow.

## Phase 1 — Foundational Infrastructure

- [x] **Angular / divergent source model** — non-collimated direction maps (UC1, UC4, UC5, UC6). Spherical wavefront, converging wavefront, Gaussian beam propagation with configurable waist position all implemented.
- [x] **Coordinate transforms for surfaces** — rotation, tilt, arbitrary pose (UC1, UC4, UC5, UC7)
- [x] **Flat-field / stepped-intensity source** — programmable uniform source (UC3, UC6, UC7)
- [x] **Spectral material model** — wavelength-dependent reflectance curves (UC2, UC4)

### Phase 1 — Completed

- [x] **Spectral material model** — `SellmeierCoefficients`, `Material.refractive_index_at(λ)`, `Material.F0(λ)`, tabulated n/k interpolation, `refractive_index_fn` callable; `CookTorranceScattering` auto-derives F₀ from surface material (UC2, UC4)
- [x] **Flat-field / stepped-intensity source** — `FlatFieldSource` with configurable intensity levels and `generate_intensity_sweep()` (UC3, UC6, UC7)
- [x] **Coordinate transforms for surfaces** — `Surface.transform(R)`, `rotate_x/y/z(angle)`, rotation of normals and slopes (UC1, UC4, UC5, UC7)
- [x] **Incidence angle convenience** — `source.incidence_angle` / `incidence_angle_degrees` on LightSource (UC1, UC4)
- [x] **Coherence / speckle model** — `SpeckleNoise` detector noise model, `Surface.phase_screen()`, pipeline integration (UC1, UC7)
- [x] **Spherical wavefront** — `source.wavefront = "spherical"` with per-pixel direction from origin (UC1, UC4, UC5, UC6)
- [x] **Cook-Torrance microfacet BRDF** — full physically based specular model with Beckmann D, Schlick F, Smith G; Lambertian diffuse term for energy conservation (UC1, UC4)
- [x] **BloomingNoise** — charge spill from saturated pixels to cardinal neighbours with configurable bloom factor and iterations (UC1, UC3)

### Pre-deployment gaps — add before the relevant use case

The following should be implemented **just before** (not ahead of) the use case that first needs them:

- [x] **Pulsed source model** (standalone, needed by UC6 LiDAR) — `TemporalEnvelope` dataclass with Gaussian/rectangular pulse shapes, pulse energy/peak power, repetition rate, duty cycle, average power computation.
- [x] **Source extent model** (standalone, needed by UC5 Structured Light) — `SourceExtent` dataclass with uniform_disk/gaussian/rectangle apertures, coherence factor, aperture function evaluation.
- [x] **Spectral quantum efficiency** `QE(λ)` (needed by UC3 Sensor Char first, then UC2 Multi-Spectral) — `CMOSDetector.quantum_efficiency` accepts a callable ``QE(wavelength)`` for wavelength-dependent photoresponse.
- [x] **Dark current non-uniformity (DCNU) and temporal noise characterisation** (needed by UC3 Sensor Char) — two refinements required for realistic PTC and SNR analysis:

   - [x] **DCNU:** `_dcnu_map` drawn per-detector-instance from narrow Gaussian; pixel-wise dark-current scaling.
   - [x] **Fixed temporal noise seeds:** `CMOSDetector.rng_seed` parameter; reproducible noise via `np.random.default_rng(seed)`.

- [x] **Thin-film interference model** — `ThinFilmStack` with transfer-matrix method, supports single/multi-layer coatings, arbitrary angle, TE/TM/unpolarized (UC1)
- [x] **Gaussian beam divergence / waist propagation** (needed by UC6 LiDAR) — `_effective_waist()` computes waist from `divergence`; Gaussian beam propagation scaling in `generate_light_field()`.
- [x] **Optical throughput / radiometric scaling** (needed by UC3 Sensor Char first) — `OpticalPropagator.propagate()` scales convolved irradiance by ``π · NA²`` when `throughput_enabled=True`.

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

- [x] **Optical magnification / field mapping** (needed by UC7 Wafer Alignment first, then UC5 Structured Light) — `OpticalPropagator.propagate()` resamples the scattered radiance via bilinear interpolation when `magnification_enabled=True` and system magnification differs from 1.0.

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

- [x] **Zernike wavefront → PSF model** — `ZernikePolynomials`, `Wavefront`, `ZernikePSF` with FFT-based generalised pupil function, Noll indexing (UC1, UC7)

- [x] **Intensity profile / line cross-section** — `IntensityProfileAnalyzer` with bilinear interpolation, configurable linewidth, contrast metric (UC1, UC5, UC7)

- [x] **FFT / power spectrum analyser** (needed by UC5 Structured Light first, then UC4 Angle-Resolved Scattering) — compute the 2D power spectrum of an image via FFT and extract radial and angular profiles.

  **What to add:**
  ```python
  class FFTAnalyzer(AnalysisModule):
      def analyze(self, image) -> AnalysisReport:
          ...
  ```
  Steps: `np.fft.fft2` → `np.fft.fftshift` → power `|F|²`.  Report:
  - `peak_spatial_frequency` — location of the brightest non-DC peak in cycles/pixel
  - `radial_profile` — mean power vs. radial frequency (1D array)
  - `dc_fraction` — fraction of total power in the DC component
  - `power_spectrum_slope` — slope of log-log radial profile (useful for roughness characterisation)

  Edge case: DC removal before FFT for better dynamic range; windowing (Hann) to reduce spectral leakage; correct frequency axis labelling.

- [x] **Edge detection analyser** (needed by UC7 Wafer Alignment first, then UC1 Defect Inspection) — locate and characterise step edges in the image.

  **What to add:**
  ```python
  class EdgeDetectionAnalyzer(AnalysisModule):
      def __init__(self, method="sobel", low_threshold=0.1, high_threshold=0.3):
          ...
  ```
  Implement a basic Sobel magnitude (zero dependencies) as the default method, with an optional Canny-style hysteresis threshold.  Report:
  - `edge_count` — number of detected edge pixels
  - `edge_density` — fraction of pixels classified as edges
  - `mean_edge_strength` — mean gradient magnitude at edge pixels
  - Optionally: centroid of edge pixels (for fiducial finding in UC7)

  Edge cases: normalise gradient magnitudes to [0, 1] so thresholds are independent of bit depth; handle single-intensity images (no edges → all zeros).

- [x] **Surface roughness estimation from speckle** — `SpeckleRoughnessEstimator` using inverse speckle contrast model, optional ROI (UC1)

- [x] **Focus / sharpness metric** — `FocusAnalyzer` with laplacian-variance, tenengrad, and brenner methods (UC1, UC5)

- [x] **Signal-to-noise ratio estimator** (needed by UC3 Sensor Char) — `SNRAnalyzer` with single-image and flat-field-pair methods.

  **What to add:**
  ```python
  class SNRAnalyzer(AnalysisModule):
      def __init__(self, method="single_image", signal_region=None, noise_region=None):
          ...
  ```
  Two methods:
  1. ``single_image`` — estimate signal as the mean of a bright region (or the whole image), noise as the standard deviation of a dark region or the full image after high-pass filtering.
  2. ``flat_field_pair`` — two identically exposed flat-field images; signal = mean of (im1 + im2) / 2, noise = std of (im1 − im2) / √2 (removes fixed-pattern noise from the estimate).

  Report ``snr_db`` (20 log₁₀(μ/σ)), ``signal_mean``, ``noise_std``.  Accept optional ``signal_region`` and ``noise_region`` as (row, col, height, width) tuples for ROI-based estimation.

- [x] **MTF (modulation transfer function) analyser** (needed by UC3 Sensor Char first, then UC4 Angle-Resolved Scattering) — `MTFAnalyzer` with sinusoidal-target method.

  **What to add:**
  ```python
  class MTFAnalyzer(AnalysisModule):
      def __init__(self, target_type="slanted_edge", lp_per_mm=None):
          ...
  ```
  Methods:
  1. ``slanted_edge`` — locate a slanted knife-edge, extract the edge spread function (ESF), differentiate to get the line spread function (LSF), FFT to get the MTF.  Implementation follows the ISO 12233 standard.
  2. ``sinusoidal`` — if the image contains a known-frequency sinusoidal pattern, compute MTF as the ratio of measured modulation to input modulation at that frequency.

  Report ``mtf_curve`` (frequency vs. MTF value as two 1D arrays), ``mtf50`` (frequency where MTF = 0.5), ``mtf50p`` (frequency where MTF = 0.5 / pixel pitch in lp/mm).  The frequency axis should be in both cycles/pixel and lp/mm (requires ``pixel_size`` from image metadata or a constructor parameter).

  Edge cases: slanted edge not found → raise a clear error; the edge must be at a small angle (2–10°) for proper oversampling; requires a sufficiently large ROI around the edge.

- [x] **Error map / ground-truth comparison** — `ErrorMapAnalyzer` with RMSE, MAE, max error, PSNR; accepts ``DigitalImage`` or raw array (UC5, UC7)
  - ``max_error`` — maximum absolute pixel difference.
  - ``psnr`` — peak signal-to-noise ratio (dB): 20 log₁₀(max_val / rmse).

  Edge cases: shape mismatch → raise ``ValueError``; both images identical → rmse = 0, psnr = ∞ (clamp to a large finite value like 120 dB).

## Phase 2a — Surface Defect Inspection (UC1)

- [x] All modules complete — see [UC1](use-cases.md#use-case-1-surface-defect-inspection-workcell) for details
  - `DentSurface`, `PitSurface`, `CrackSurface`, `StainSurface`
  - `bright_field()`, `dark_field()`, `ring_light()`
  - `DefectAnalyzer`, `TiledAcquisition`
  - 6 integration tests + 5 Robot tests

## Phase 2b — Sensor Performance Characterization (UC3)

- [x] All modules complete — see [UC3](use-cases.md#use-case-3-sensor-performance-characterization) for details
  - `PTCAnalyzer`, `DynamicRangeAnalyzer`, `LinearityTestAnalyzer`
  - `siemens_star()`, `slanted_edge()`, `greyscale_wedge()`
  - 28 integration tests + 8 Robot tests

## Phase 2c — Wafer Chip Misalignment Detection (UC7)

- [x] All modules complete — see [UC7](use-cases.md#use-case-7-wafer-chip-misalignment-detection) for details
  - `WaferSurface`, `MisalignedSurface`, `TemplateMatcher`, `RegistrationAnalyzer`, `SPCAnalyzer`
  - 22 integration tests + 4 Robot tests
- [ ] Real-time performance model — deferred (non-functional)

## Phase 2d — Multi-Spectral Material Identification (UC2)

- [x] All modules complete — see [UC2](use-cases.md#use-case-2-multi-spectral-material-identification) for details
  - `MultiChannelLightField`, `MultiSpectralSource`, `FilterWheelSource`
  - `SpectralAnalyzer`, `CFAConfig`, `CFADetector`
  - 24 integration tests + 6 Robot tests

## Phase 2e — Angle-Resolved Scattering Measurement (UC4)

- [x] Core modules complete — see [UC4](use-cases.md#use-case-4-angle-resolved-scattering-measurement) for details
  - `BeckmannScattering`, `GGXScattering`, `GoniometricSweep`, `BRDFFitter`
- [ ] Polarised BRDF (Mueller matrix) — deferred
- [ ] Standard reference materials — deferred
- [ ] BSDF (transmissive scattering) — deferred

## Phase 2f — Structured Light 3D Scanning (UC5)

- [x] Core modules complete — see [UC5](use-cases.md#use-case-5-structured-light-3d-scanning) for details
  - `FringeProjector`, `PhaseExtractor`, `PhaseUnwrapper`, `HeightReconstructor`, `SurfaceComparator`
  - 16 integration tests + 4 Robot tests
- [ ] Divergent projection model — deferred
- [ ] Projector-camera calibration — deferred

## Phase 2g — LiDAR Range Finding (UC6)

- [x] Core modules complete — see [UC6](use-cases.md#use-case-6-lidar-range-finding) for details
  - `RayleighScattering`, `MieScattering`, `ScanningMechanism`
  - `LiDARRangeEquation`, `TimeOfFlightPropagator`, `SPADDetector`, `WaveformAnalyzer`
  - `TemporalEnvelope` (pre-deployment), `generate_point_cloud()`
  - 22 integration tests + 5 Robot tests
- [ ] Atmospheric effects — deferred

## Before Phase 2 — final architecture review pass

Run this **after completing all module reviews** (illumination, surface,
scattering, optics, detector, analysis) and **before starting any use
case implementation**.

- [x] Update `README.md` — refresh file reference table, test counts,
      document new classes (`ImportedSurface`, `SpeckleNoise`,
      `wavefront`, `incidence_angle`, Cook-Torrance, BloomingNoise,
      analysis three-group classification, etc.) — **done in session**
- [x] Review and update all package `__init__.py` exports for consistency
      — **all 7 packages verified, all `__all__` match imports**
- [x] Run full test suite and update any stale line/class references
      in docstrings

## Phase 3 — Consolidation

Detailed notebook/script specs for each UC: see [Learning & Playability Roadmap](use-cases.md#learning--playability-roadmap) in `use-cases.md`.

- [ ] End-to-end demo scripts + Jupyter notebooks for each use case
- [ ] Integration tests covering multi-step workflows
- [ ] Performance benchmarks (grid scaling, convolution speed)
- [ ] User documentation for each use case in `docs/`
