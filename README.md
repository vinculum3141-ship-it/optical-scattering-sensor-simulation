# optical-metrology

[![CI](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-online-blue)](https://vinculum3141-ship-it.github.io/optical-scattering-sensor-simulation/)

A physics-based virtual optical metrology platform — end-to-end
simulation of illumination, surface scattering, optical propagation,
detection, and image analysis.

- **Six independent layers** — illumination, surface, scattering,
  optics, detector, analysis — connected by well-defined data contracts
  and independently reusable.
- **Physically based models** — Lambertian, Oren-Nayar, Phong,
  Beckmann, GGX, and Cook-Torrance BRDFs; particle (Rayleigh/Mie)
  scattering; Gaussian/Airy/Zernike PSFs with defocus; a full CMOS
  detector pipeline with pluggable noise.
- **Seven use cases** — defect inspection, multispectral material ID,
  sensor characterisation, BRDF measurement, structured-light 3D, LiDAR
  ranging, and wafer metrology — each with a tutorial notebook, a CLI
  script, and acceptance tests.
- **Terminal-native** — every field and image renders as a Unicode
  heatmap; the core requires only NumPy.

## Quick start

```bash
pip install -e .             # install from source
python playground.py --demo   # non-interactive tour of every layer
```

```bash
python playground.py                         # interactive menu
python playground.py --detector              # jump to detector demo
python playground.py --analysis              # jump to analysis demo
```

### Requirements

- Python 3.9+
- [NumPy](https://numpy.org/)

Optional extras:

```bash
pip install -e ".[dev]"           # + pytest, robotframework
pip install -e ".[analysis]"      # + scipy
pip install -e ".[visualisation]" # + matplotlib, jupyter
pip install -e ".[docs]"          # + mkdocs material (build the docs site)
```

### Makefile

Common tasks are one command (see [CONTRIBUTING.md](CONTRIBUTING.md) for
details):

```bash
make install     # pip install -e .
make dev         # install with dev + analysis + visualisation extras
make demo        # python playground.py --demo
make test        # pytest -q
make acceptance  # robot tests/
make docs        # serve the docs locally at http://127.0.0.1:8000
make docs-build  # strict docs build (what CI runs)
```

### Repository layout

```
src/optical_metrology/   → Installable Python package (the library)
notebooks/               → Self-contained use-case units (tutorial + CLI script + README)
tests/                   → Pytest unit tests + Robot Framework acceptance tests
docs/                    → Documentation (mkdocs site) — audience-oriented sections
mkdocs.yml               → Documentation site configuration
```

The scripts at the repository root (`playground.py`, `explore.py`,
`plot_pipeline.py`) are standalone entry points that use the installed
``optical_metrology`` package. They are kept at root for easy discovery.

---

## Pipeline overview

```
Light Source  →  LightField  →  Surface  →  ScatteredField
 →  Optics (PSF)  →  SensorField  →  Detector  →  DigitalImage
 →  Analysis  →  Measurements
```

Each stage transforms one physical representation into the next. The
layers do not import each other — they communicate only through these
data containers, so any stage can be swapped, skipped, or reused.

| Layer | What it models | Detail |
|---|---|---|
| Illumination | Laser, LED, sunlight, broadband sources; beam profiles, spectra, polarisation, wavefronts (planar/spherical/converging), incidence angle | [`science/layer-illumination.md`](docs/science/layer-illumination.md) |
| Surface | Height-map generators (flat, rough, scratched, particle, sinusoidal, anisotropic, defect, wafer, misaligned) with derived normals, curvature, roughness | [`science/layer-surface.md`](docs/science/layer-surface.md) |
| Scattering | BRDF models — Lambertian, Oren-Nayar, Phong, Beckmann, GGX, Cook-Torrance — plus Rayleigh/Mie particle scattering | [`science/layer-scattering.md`](docs/science/layer-scattering.md) |
| Optics | Optical system (aperture, focal length, NA, magnification); Gaussian, Airy, and Zernike-aberrated PSF convolution; defocus | [`science/layer-optics.md`](docs/science/layer-optics.md) |
| Detector | CMOS pipeline: photons → photoelectrons → shot/dark/read noise → pluggable noise models → full-well clip → ADC; CFA and SPAD variants | [`science/layer-detector.md`](docs/science/layer-detector.md) |
| Analysis | Pluggable measurement modules — quality (histogram, contrast, focus, SNR), optical characterisation (MTF, FFT), metrology (defects, PTC, BRDF fit, registration, SPC, …) | [`science/layer-analysis.md`](docs/science/layer-analysis.md) |

---

## Examples

### Build a light field

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
```

### Full end-to-end pipeline in one shot

```python
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
print(image.visualize(max_width=48))   # terminal heatmap — no plotting lib
```

Or assemble the same chain through the single-call `SimulationPipeline`
(see the [Quickstart](docs/getting-started/quickstart.md) for the
one-liner).

### Detector noise and analysis

```python
from optical_metrology.detector import CMOSDetector, HotPixelNoise
from optical_metrology.optics import SensorField
from optical_metrology.analysis import ImageAnalyzer, HistogramAnalyzer, ContrastAnalyzer
import numpy as np

sensor_field = SensorField(irradiance=np.ones((8, 8)) * 1e4, wavelength=532e-9)
detector = CMOSDetector(
    exposure_time=0.1, bit_depth=12,
    noise_models=[HotPixelNoise(density=0.001)],
)
image = detector.capture(sensor_field)
report = ImageAnalyzer(modules=[HistogramAnalyzer(), ContrastAnalyzer()]).analyze(image)
print(report.measurements)
```

---

## Use cases and notebooks

Seven application scenarios ship as self-contained notebook units —
tutorial notebook, CLI script, and README per folder under `notebooks/`.
The full index is [`notebooks/README.md`](notebooks/README.md).

| Use case | Docs page |
|---|---|
| UC1 — Surface defect inspection | [uc1](docs/use-cases/uc1-surface-defect-inspection.md) |
| UC2 — Multi-spectral material identification | [uc2](docs/use-cases/uc2-multispectral-identification.md) |
| UC3 — Sensor performance characterisation | [uc3](docs/use-cases/uc3-sensor-characterization.md) |
| UC4 — Angle-resolved scattering (BRDF sweep) | [uc4](docs/use-cases/uc4-angle-resolved-scattering.md) |
| UC5 — Structured-light 3D scanning | [uc5](docs/use-cases/uc5-structured-light-3d.md) |
| UC6 — LiDAR range finding | [uc6](docs/use-cases/uc6-lidar-ranging.md) |
| UC7 — Wafer metrology (alignment + defect capstone) | [uc7](docs/use-cases/uc7-alignment.md) · [capstone](docs/use-cases/uc7-defect-capstone.md) |

## Entry-point scripts

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

---

## Documentation

The full documentation is published at
**[optical-scattering-sensor-simulation docs](https://vinculum3141-ship-it.github.io/optical-scattering-sensor-simulation/)**
and organised by audience:

| Section | For | Covers |
|---|---|---|
| [Getting Started](docs/getting-started/quickstart.md) | Everyone | Quickstart + guided [training modules](docs/getting-started/training/index.md) |
| [Use Cases](docs/use-cases/index.md) | Everyone | Seven end-to-end scenarios with notebooks and CLI scripts |
| [Science](docs/science/index.md) | Researchers | Physics foundations, per-layer models and assumptions, research workflows (prototyping → production) |
| [Engineering](docs/engineering/architecture.md) | Software engineers | Architecture, [design patterns & OOP principles](docs/engineering/design-patterns.md), extending the framework |
| [Quality Assurance](docs/quality-assurance/test-strategy.md) | Testers / QA | ISTQB-aligned test strategy, test inventory, verification & validation (ISO references) |

To build or preview the docs locally:

```bash
pip install -e ".[docs]"
make docs        # preview at http://127.0.0.1:8000
make docs-build  # strict build, as run in CI
```

## Testing

```bash
python -m pytest -q              # 352 unit/integration tests
python -m robot tests/           # 96 acceptance tests (requires .[dev])
```

Both suites run in CI on every push/PR. See
[Quality Assurance docs](docs/quality-assurance/testing.md) for the full
inventory and how the suites map onto ISTQB test levels and techniques.

---

## Design notes

- **SI units everywhere** — metres, Watts, radians, seconds; no ambiguous
  conventions.
- **Independent, contract-driven layers** — the illumination package
  knows nothing about surfaces; layers connect only through the data
  containers documented in [Architecture](docs/engineering/architecture.md).
- **Deterministic where possible** — surface generators use fixed RNG
  seeds by default; detector noise is the only stochastic stage, and
  tests use statistical bounds, not exact values.
- **Minimal core dependencies** — NumPy only for the core pipeline;
  matplotlib, Jupyter, and Robot Framework are optional.
- **Terminal-native visualisation** — `visualize()` renders Unicode-block
  heatmaps everywhere, no plotting library required.
- See [Design Patterns & Software Principles](docs/engineering/design-patterns.md)
  for the *why* behind the implementation.

## License

MIT — see [LICENSE](LICENSE).
