# optical-metrology

[![CI](https://github.com/vinculum3141/optical-scattering-sensor-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/vinculum3141/optical-scattering-sensor-simulation/actions/workflows/ci.yml)

A physics-based virtual optical metrology platform — end-to-end
simulation of illumination, surface scattering, optical propagation,
detection, and image analysis.

## Quick start

```bash
pip install -e .            # install from source
python playground.py --demo  # non-interactive tour
```

```bash
python playground.py                         # interactive menu
python playground.py --detector              # jump to detector demo
python playground.py --analysis              # jump to analysis demo
```

### Repository layout

```
src/optical_metrology/   → Installable Python package (the library)
scripts/                 → Not used — entry-point scripts live at repo root
examples/                → Jupyter notebooks
tests/                   → Pytest unit tests + Robot Framework acceptance tests
docs/                    → Markdown documentation
```

The scripts at the repository root (`playground.py`, `explore.py`,
`plot_pipeline.py`) are standalone entry points that use the installed
``optical_metrology`` package. They are kept at root for easy discovery.

### Requirements

- Python 3.9+
- [NumPy](https://numpy.org/) (optional: `robotframework` for Robot tests)

Install with extra dependencies:

```bash
pip install -e ".[dev]"          # + pytest, robotframework
pip install -e ".[analysis]"     # + scipy
pip install -e ".[visualisation]" # + matplotlib, jupyter
```

---

## Pipeline overview

```
Light Source  →  LightField  →  Surface  →  ScatteredField
 →  Optics (PSF)  →  SensorField  →  Detector  →  DigitalImage
 →  Analysis  →  Measurements
```

Each stage transforms one physical representation into the next.
All modules are independently reusable.

### Layers

1. **Illumination** — light sources (laser, LED, sunlight, broadband
   lamp) with configurable wavelength, power, beam profile, wavefront
   (planar/spherical), polarisation, and incidence angle.
2. **Surface geometry** — height map generators (flat, rough,
   scratched, particle-contaminated, sinusoidal, anisotropic,
   imported) with derived normals, slopes, curvature, and roughness.
3. **Scattering** — BRDF models (Lambertian, Oren-Nayar, Phong,
   Cook-Torrance) that compute radiance scattered toward an observer.
4. **Optics** — imaging system (aperture, focal length, NA,
   magnification) with point-spread function convolution (Gaussian,
   Airy disk).
5. **Detector** — CMOS sensor pipeline: irradiance → photons → QE →
   photoelectrons → shot noise → dark current → read noise → custom
   noise models → full-well clip → ADC quantisation → digital image.
6. **Analysis** — pluggable measurement modules organised in three
   groups: Quality Assessment (histogram, contrast, saturation, focus,
   SNR), Optical Characterisation (MTF, FFT), and Metrology (edge
   detection, roughness estimation, intensity profile).

---

## Examples

### Use the API directly

```python
from optical_metrology.illumination import Laser, GaussianBeamProfile

laser = Laser(
    wavelength=532e-9,
    power=5e-3,
    beam_profile=GaussianBeamProfile(w0=1.0),
    wavefront="spherical",
)
field = laser.generate_light_field(shape=(64, 64), spacing=1.0)
print(field.intensity.shape)          # (64, 64)
print(field.direction.shape)          # (64, 64, 3)  — per-pixel direction
print(field.coherence_length)         # from source temporal coherence
```

```python
from optical_metrology.surface import RoughSurface, Material

surf = RoughSurface(
    shape=(64, 64), sigma=6.0, amplitude=0.5,
    material=Material(name="silicon"),
)
print(surf.height.shape)              # (64, 64)
print(surf.roughness)                 # e.g. 0.049
print(surf.phase_screen(532e-9).shape)  # (64, 64) — 4πh/λ phase delay
```

```python
from optical_metrology.illumination import Laser, GaussianBeamProfile
from optical_metrology.surface import FlatSurface, Material
from optical_metrology.scattering import CookTorranceScattering

laser = Laser(wavelength=532e-9, power=5e-3,
              beam_profile=GaussianBeamProfile(w0=2.0))
laser.propagation_direction = [0, 0, -1]

lightfield = laser.generate_light_field(shape=(32, 32), spacing=0.5)
surface = FlatSurface((32, 32), material=Material("glass"))
model = CookTorranceScattering(roughness=0.1, fresnel_reflectance=0.04, albedo=0.5)

result = model.evaluate(lightfield, surface, view_direction=[0, 0, 1])
print(result.radiance.shape)          # (32, 32)
print(result.outgoing_direction.shape) # (32, 32, 3)
```

```python
from optical_metrology.detector import CMOSDetector, BloomingNoise
from optical_metrology.optics import SensorField
import numpy as np

sensor_field = SensorField(
    irradiance=np.ones((8, 8)) * 1e4,   # W/m² — bright spot
    wavelength=532e-9,
)
detector = CMOSDetector(
    exposure_time=0.1, bit_depth=12,
    noise_models=[BloomingNoise(bloom_factor=0.05, iterations=2)],
)
image = detector.capture(sensor_field)
print(image.pixels.shape)              # (8, 8)
print(image.pixels.dtype)              # uint16
print(detector.pipeline_describe())    # step-by-step summary
print(image.visualize(max_width=48))   # terminal heatmap
```

```python
from optical_metrology.analysis import HistogramAnalyzer, ContrastAnalyzer, ImageAnalyzer

analyzer = ImageAnalyzer(modules=[HistogramAnalyzer(), ContrastAnalyzer()])
report = analyzer.analyze(image)
print(report.measurements["mean_intensity"])     # e.g. 2048.0
print(report.measurements["michelson_contrast"]) # e.g. 0.12
print(report.histogram.shape)                    # e.g. (4096,)
```

```python
# Full end-to-end pipeline in one shot
from optical_metrology.illumination import Laser, GaussianBeamProfile
from optical_metrology.surface import RoughSurface, Material
from optical_metrology.scattering import LambertianScattering
from optical_metrology.optics import OpticalSystem, GaussianPSF, OpticalPropagator
from optical_metrology.detector import CMOSDetector

laser = Laser(532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0))
laser.propagation_direction = [0, 0, -1]
lf = laser.generate_light_field(shape=(16, 16), spacing=0.5)
surface = RoughSurface((16, 16), sigma=4.0, amplitude=0.3,
                       material=Material("silicon"))
scattered = LambertianScattering(albedo=0.7).evaluate(lf, surface, view=[0, 0, 1])
optics = OpticalSystem(focal_length=0.05, aperture_diameter=0.008,
                       wavelength=532e-9)
sensor = OpticalPropagator(GaussianPSF(sigma=1.0)).propagate(scattered, optics)
image = CMOSDetector(exposure_time=1e-5, gain=1.0).capture(sensor)
print(image.pixels.min(), "-", image.pixels.max(), "ADU")
```

### Entry-point scripts

The scripts at the repository root are standalone entry points (not part of
the installable library). They use the installed ``optical_metrology``
package and serve as interactive demos/exploration tools:

| Command | What it does |
|---------|-------------|
| `python playground.py --demo` | Full pipeline tour |
| `python playground.py` | Interactive menu |
| `python playground.py --detector` | Detector demo only |
| `python playground.py --analysis` | Analysis demo only |
| `python playground.py --custom` | Custom pipeline from scratch |
| `python playground.py --tinker` | Code snippets to copy-paste |
| `python explore.py` | Interactive explorer (illumination/surface/scattering) |
| `python plot_pipeline.py` | Matplotlib PNG output (needs `matplotlib`) |

### Jupyter notebooks

| Notebook | What it shows |
|----------|---------------|
| `examples/basic_pipeline.ipynb` | Light → surface → scatter → optics → detector → analysis |
| `examples/defect_inspection.ipynb` | Scratched surface inspection (UC1 preview) |
| `pipeline.ipynb` | Root-level notebook with inline matplotlib plots |

---

## Package structure

### Illumination

All source code lives under `src/optical_metrology/`.

| File | Contents |
|------|----------|
| `src/optical_metrology/illumination/source.py` | `LightSource` — base source with wavefront, incidence angle, coherence length |
| `src/optical_metrology/illumination/laser.py` | `Laser` — monochromatic, configurable divergence |
| `src/optical_metrology/illumination/led.py` | `LED` — Gaussian spectrum, 0.5 rad divergence |
| `src/optical_metrology/illumination/sunlight.py` | `Sunlight` — black-body at 5778 K |
| `src/optical_metrology/illumination/broadband.py` | `BroadbandLamp` — flat spectrum over a range |
| `src/optical_metrology/illumination/flatfield.py` | `FlatFieldSource` — programmable uniform source with intensity sweep |
| `src/optical_metrology/illumination/profiles.py` | `GaussianBeamProfile`, `UniformBeamProfile`, `TopHatBeamProfile` |
| `src/optical_metrology/illumination/spectrum.py` | `MonochromaticSpectrum`, `GaussianSpectrum`, `BlackbodySpectrum`, `BroadbandSpectrum` |
| `src/optical_metrology/illumination/polarization.py` | `PolarizationState` — unpolarised, linear, circular, elliptical |
| `src/optical_metrology/illumination/lightfield.py` | `LightField` with per-pixel intensity, direction, coherence, power, terminal heatmap |

### Surface geometry

| File | Contents |
|------|----------|
| `src/optical_metrology/surface/base.py` | `Surface`, `Material` (with `SellmeierCoefficients`, `n(λ)`, `F0(λ)`), `GeometryAnalyzer`, `SurfaceGenerator`, `phase_screen()`, `visualize()` |
| `src/optical_metrology/surface/generators.py` | `FlatSurface`, `RoughSurface`, `ScratchedSurface`, `ParticleSurface`, `SinusoidalSurface`, `AnisotropicRoughSurface`, `ImportedSurface` |
| `src/optical_metrology/surface/thinfilm.py` | `ThinFilmStack` — transfer-matrix thin-film reflectance/transmittance |

### Scattering

| File | Contents |
|------|----------|
| `src/optical_metrology/scattering/base.py` | `ScatteringModel` base, `ScatteredField` container |
| `src/optical_metrology/scattering/lambertian.py` | `LambertianScattering` — ideal diffuse |
| `src/optical_metrology/scattering/orennayar.py` | `OrenNayarScattering` — rough diffuse |
| `src/optical_metrology/scattering/phong.py` | `PhongScattering` — diffuse + empirical specular |
| `src/optical_metrology/scattering/cooktorrance.py` | `CookTorranceScattering` — physically based specular (Beckmann D, Schlick F, Smith G) |
| `src/optical_metrology/scattering/beckmann.py` | `BeckmannScattering` (skeleton — implement before UC4) |
| `src/optical_metrology/scattering/ggx.py` | `GGXScattering` (skeleton — implement before UC4) |
| `src/optical_metrology/scattering/particle.py` | `RayleighScattering`, `MieScattering` (skeletons — implement before UC6) |

### Optics

| File | Contents |
|------|----------|
| `src/optical_metrology/optics/base.py` | `OpticalSystem`, `SensorField` |
| `src/optical_metrology/optics/psf.py` | `GaussianPSF` — isotropic Gaussian blur |
| `src/optical_metrology/optics/airy.py` | `AiryPSF` — diffraction-limited Airy disk (self-contained Bessel, no scipy dep) |
| `src/optical_metrology/optics/zernike.py` | `ZernikePolynomials`, `Wavefront`, `ZernikePSF` — Zernike-aberrated PSF via FFT |
| `src/optical_metrology/optics/propagator.py` | `OpticalPropagator` — PSF convolution, radiance → irradiance |

### Detector

| File | Contents |
|------|----------|
| `src/optical_metrology/detector/base.py` | `CMOSDetector` (7-step pipeline), `DigitalImage` (terminal heatmap), `DetectorNoiseModel` base |
| `src/optical_metrology/detector/noise_models.py` | `FixedPatternNoise`, `PhotoResponseNonUniformity`, `HotPixelNoise`, `ColumnDefectNoise`, `DeadPixelNoise`, `SpeckleNoise`, `BloomingNoise` |

### Analysis

| File | Contents | Group |
|------|----------|-------|
| `src/optical_metrology/analysis/base.py` | `AnalysisModule`, `AnalysisReport`, `ImageAnalyzer` | Orchestration |
| `src/optical_metrology/analysis/histogram.py` | `HistogramAnalyzer` — pixel histogram, mean/min/max | Quality Assessment |
| `src/optical_metrology/analysis/contrast.py` | `ContrastAnalyzer` (RMS, Michelson, Weber), `SaturationAnalyzer` | Quality Assessment |
| `src/optical_metrology/analysis/focus.py` | `FocusAnalyzer` — laplacian-variance, tenengrad, brenner | Quality Assessment |
| `src/optical_metrology/analysis/intensity_profile.py` | `IntensityProfileAnalyzer` — 1D line profile with bilinear interpolation | Metrology |
| `src/optical_metrology/analysis/error_map.py` | `ErrorMapAnalyzer` — RMSE, MAE, max error, PSNR vs ground truth | Metrology |
| `src/optical_metrology/analysis/speckle_roughness.py` | `SpeckleRoughnessEstimator` — roughness from speckle contrast | Metrology |

### Scripts and tests

| File | Contents |
|------|----------|
| `explore.py` | Interactive CLI — illumination / surface / scattering modes |
| `playground.py` | Interactive playground with demos, custom pipeline, code snippets |
| `plot_pipeline.py` | Standalone — runs pipeline, saves matplotlib PNGs |
| `examples/basic_pipeline.ipynb` | Jupyter notebook — basic pipeline example |
| `examples/defect_inspection.ipynb` | Jupyter notebook — UC1 defect inspection |
| `tests/test_illumination.py` | Pytest (24 tests) |
| `tests/test_surface.py` | Pytest (4 tests) |
| `tests/test_surface_new.py` | Pytest (31 tests) |
| `tests/test_scattering.py` | Pytest (11 tests) |
| `tests/test_scattering_new.py` | Pytest (6 tests) |
| `tests/test_optics.py` | Pytest (1 test) |
| `tests/test_optics_new.py` | Pytest (13 tests) |
| `tests/test_detector.py` | Pytest (1 test) |
| `tests/test_detector_new.py` | Pytest (16 tests) |
| `tests/test_analysis.py` | Pytest (1 test) |
| `tests/test_analysis_new.py` | Pytest (23 tests) |
| `tests/test_pipeline.py` | Pytest (5 tests) |
| `tests/test_utils.py` | Pytest (4 tests) |
| `tests/*.robot` | Robot Framework acceptance tests (43 tests) |

---

## Testing

```bash
# Pytest — 140 unit tests across all layers
python -m pytest -q

# Robot Framework — 43 acceptance tests (requires pip install -e ".[dev]")
python -m robot tests/
```

---

## Scattering models

The scattering layer answers one question:

> Given incoming light, a surface, and an observation direction, how
> much light is reflected toward that direction?

It returns a `ScatteredField` with radiance and outgoing direction —
a structured result that downstream modules consume without knowing
the scattering model internals.

| Model | Type | Description |
|-------|------|-------------|
| `LambertianScattering` | Diffuse | Ideal diffuse: radiance ∝ cos(θ) × albedo |
| `OrenNayarScattering` | Rough diffuse | Diffuse with microfacet shadowing — broader lobe for rough surfaces (concrete, ceramics) |
| `PhongScattering` | Diffuse + specular | Empirical: diffuse lobe + specular peak controlled by shininess |
| `CookTorranceScattering` | Physically based specular | Beckmann distribution × Schlick Fresnel × Smith geometry + Lambertian diffuse term |

Additional models (Beckmann, GGX, Rayleigh, Mie) are documented as
skeletons and will be implemented before their respective use cases.

---

## Detector pipeline

The `CMOSDetector` pipeline steps:

1. **Photon conversion** — irradiance (W/m²) → incident photons via
   `E = hc/λ`, scaled by pixel area and exposure time.
2. **Quantum efficiency** — fraction of photons converted to
   photoelectrons.
3. **Shot noise** — Poisson-distributed photon arrival (√N noise).
4. **Dark current** — thermally generated electrons (Poisson).
5. **Read noise** — Gaussian noise from readout electronics.
6. **Custom noise models** — pluggable stages applied in order.
7. **Full-well clip** — saturation at maximum electron capacity.
8. **ADC quantisation** — divide by gain, round, clamp to bit-depth
   range, cast to `uint16`.

Custom noise models available:

| Model | Effect |
|-------|--------|
| `FixedPatternNoise` | Per-pixel additive offset |
| `PhotoResponseNonUniformity` | Per-pixel multiplicative gain variation |
| `HotPixelNoise` | Random bright spots from elevated dark current |
| `ColumnDefectNoise` | Column-wide gain reduction |
| `DeadPixelNoise` | Random pixels stuck at a fixed value |
| `SpeckleNoise` | Coherent speckle from surface roughness |
| `BloomingNoise` | Charge spill from saturated pixels to neighbours |

---

## Design notes

- All physical quantities use SI units (metres, Watts, radians,
  seconds).
- Stochastic noise models (Poisson shot/dark, Gaussian read) produce
  run-to-run variation.  Tests use statistical bounds, not exact values.
- `LightField.visualize()` and `DigitalImage.visualize()` render
  Unicode-block heatmaps in the terminal — no plotting library required.
- Surface generators are deterministic where possible (fixed RNG seed
  in `ParticleSurface`, `ImportedSurface` loads external data).
- The `_gaussian_filter` helper in `surface/generators.py` is a
  pure-NumPy separable convolution — no SciPy dependency.
- The seven surface generators all use the pattern
  `self.__dict__.update(surface.__dict__)` — adding a field to
  `Surface` requires no generator changes.
- See `docs/roadmap-todo.md` for the full use-case-driven development
  plan and `docs/future-improvements.md` for deferred architectural
  ideas.

---

## Roadmap

The project follows a use-case-driven roadmap with 7 phases (2a–2g)
covering semiconductor inspection, LiDAR, structured light, sensor
characterisation, and multi-spectral material identification.  See
`docs/roadmap-todo.md` for the complete task tracker.

Phase 0 (Framework Finalisation) covers packaging, CI, documentation
site, and example notebooks before any use-case implementation begins.
