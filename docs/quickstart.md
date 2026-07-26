# Quickstart

## Requirements

- Python 3.9+
- NumPy (installed automatically with the framework)
- Optional: `matplotlib` for plotting, `jupyter` for notebooks,
  `robotframework` for acceptance tests

## Installation

No package installation is required — the framework is used directly
from the repository root. Clone or copy the repository, then:

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# or .venv\Scripts\activate        # Windows
pip install numpy
```

## Running the Full Pipeline Demo

The fastest way to see every layer in action:

```bash
python playground.py --demo
```

This runs a non-interactive tour through all six layers — illumination,
surface geometry, scattering, optics, detector, and analysis — printing
terminal heatmaps at each stage.

## Interactive Exploration

```bash
python playground.py
```

Opens a numbered menu. Choose any layer to inspect it in detail, or
select the custom pipeline to build an end-to-end simulation from scratch.

## Using the Pipeline Orchestrator

For a cleaner single-call approach, use `SimulationPipeline`:

```python
from pipeline import SimulationPipeline
from illumination import Laser, GaussianBeamProfile
from surface import RoughSurface, Material
from scattering import LambertianScattering
from optics import OpticalSystem, GaussianPSF, OpticalPropagator
from detector import CMOSDetector
from analysis import HistogramAnalyzer

pipeline = SimulationPipeline(
    source=Laser(532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
    surface=RoughSurface((16, 16), sigma=4.0, amplitude=0.3, material=Material("silicon")),
    scattering=LambertianScattering(albedo=0.7),
    optics=OpticalSystem(focal_length=0.05, aperture_diameter=0.008),
    propagator=OpticalPropagator(GaussianPSF(sigma=1.0)),
    detector=CMOSDetector(exposure_time=1e-5, gain=1.0),
    analysers=[HistogramAnalyzer()],
)
result = pipeline.run(shape=(16, 16), spacing=0.5)
print(result.digital_image.pixels.min(), "-", result.digital_image.pixels.max(), "ADU")
print(result.report.measurements)
```

Every component is optional — set any to `None` to skip that stage.

## A Complete Six-Line Pipeline

```python
from illumination import Laser, GaussianBeamProfile
from surface import RoughSurface, Material
from scattering import LambertianScattering
from optics import OpticalSystem, GaussianPSF, OpticalPropagator
from detector import CMOSDetector

laser = Laser(532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0))
laser.propagation_direction = [0, 0, -1]
lf = laser.generate_light_field(shape=(16, 16), spacing=0.5)
surface = RoughSurface((16, 16), sigma=4.0, amplitude=0.3, material=Material("silicon"))
scattered = LambertianScattering(albedo=0.7).evaluate(lf, surface, view=[0, 0, 1])
optics = OpticalSystem(focal_length=0.05, aperture_diameter=0.008, wavelength=532e-9)
sensor = OpticalPropagator(GaussianPSF(sigma=1.0)).propagate(scattered, optics)
image = CMOSDetector(exposure_time=1e-5, gain=1.0).capture(sensor)
print(image.pixels.min(), "-", image.pixels.max(), "ADU")
```

## Visualising Results in the Terminal

Every data container has a `visualize()` method that renders a Unicode
block-character heatmap:

```python
print(lf.visualize())              # intensity map
print(image.visualize(max_width=72, color=True))  # digital image
```

## Running Tests

```bash
# Unit tests (pytest)
python -m pytest -q

# Acceptance tests (Robot Framework — requires robotframework)
python -m robot tests/
```

## Next Steps

- Read the [Architecture](architecture.md) overview to understand the
  data flow and design patterns.
- Explore the [Physics Foundations](physics-foundations.md) for the
  governing equations behind each layer.
- Work through the layer-specific docs for detailed API references,
  implementation notes, and examples.
