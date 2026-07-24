# optical-scattering-sensor-simulation

A physics-based simulation framework for optical scattering sensors. The
repository implements two layers of the simulation pipeline:

1. **Illumination** — describe a light source and generate a light field
   over a 2D grid.
2. **Surface geometry** — model a surface via a height map and derive
   geometric quantities (normals, slopes, curvature, roughness).

---

## Quick start

### Requirements

- Python 3.9+
- [NumPy](https://numpy.org/)

### Interactive explorer

Run `explore.py` with no arguments to get an interactive menu:

```bash
python explore.py          # illumination scenarios
python explore.py --surface   # surface-geometry scenarios
```

Inside the menu, press `[m]` to switch between illumination and surface
mode, or `[q]` to quit.

Non-interactive commands (same flags for both modes):

```bash
python explore.py --list          # list all scenarios
python explore.py --run 1         # run scenario 1
python explore.py --all           # run every scenario
python explore.py --surface --run 3   # run surface scenario 3
```

Each scenario prints a description of the source or surface, then renders
a 2D terminal heatmap of the intensity or height field.

### Use the API directly

```python
from illumination import Laser, GaussianBeamProfile

laser = Laser(
    wavelength=532e-9,
    power=5e-3,
    beam_profile=GaussianBeamProfile(w0=1.0),
)
field = laser.generate_light_field(shape=(64, 64), spacing=1.0)
print(field.intensity.shape)   # (64, 64)
```

```python
from surface import RoughSurface, Material

surf = RoughSurface(
    shape=(64, 64), sigma=6.0, amplitude=0.5,
    material=Material(name="silicon"),
)
print(surf.height.shape)   # (64, 64)
print(surf.roughness)      # e.g. 0.049
```

---

## Package structure

### Illumination layer

| File | Contents |
|---|---|
| `illumination/source.py` | Base `LightSource` dataclass |
| `illumination/laser.py` | `Laser` — monochromatic, 1 mrad divergence |
| `illumination/led.py` | `LED` — Gaussian spectrum, 0.5 rad divergence |
| `illumination/sunlight.py` | `Sunlight` — black-body at 5778 K |
| `illumination/broadband.py` | `BroadbandLamp` — flat spectrum over a range |
| `illumination/profiles.py` | Beam profiles: `UniformBeamProfile`, `TopHatBeamProfile`, `GaussianBeamProfile` |
| `illumination/spectrum.py` | Spectral models: `MonochromaticSpectrum`, `GaussianSpectrum`, `BlackbodySpectrum`, `BroadbandSpectrum` |
| `illumination/polarization.py` | `PolarizationState` |
| `illumination/lightfield.py` | `LightField` — output container with terminal heatmap (`visualize()`) |
| `illumination/__init__.py` | Package exports |

### Surface geometry layer

| File | Contents |
|---|---|
| `surface/base.py` | `Surface` dataclass, `Material`, `GeometryAnalyzer`, `SurfaceGenerator` base |
| `surface/generators.py` | `FlatSurface`, `RoughSurface`, `ScratchedSurface`, `ParticleSurface` |
| `surface/__init__.py` | Package exports |

### Scripts and tests

| File | Contents |
|---|---|
| `explore.py` | Interactive CLI explorer (illumination + surface modes) |
| `tests/test_illumination.py` | Pytest unit tests for illumination (4 tests) |
| `tests/test_surface.py` | Pytest unit tests for surface (4 tests) |
| `tests/IlluminationLibrary.py` | Robot Framework test library for illumination |
| `tests/illumination.robot` | Robot Framework acceptance tests for illumination (16 tests) |
| `tests/SurfaceLibrary.py` | Robot Framework test library for surface |
| `tests/surface.robot` | Robot Framework acceptance tests for surface (10 tests) |

---

## Project goal

Simulate how a sensor responds to scattered light under different source,
geometry, and material conditions. Each layer is kept independent so that
they can be extended, replaced, or recombined without coupling.

- The **illumination layer** describes the incoming electromagnetic field.
  It does not know about surfaces or scattering.
- The **surface layer** describes the object being illuminated via a 2D
  height map and derived geometric quantities (normals, slopes, curvature,
  roughness). It does not know about light.

The next step will connect these layers so that a light field can be
scattered by a surface and sensed by a detector.

---

## Testing

```bash
# Pytest (unit tests) — all layers
python -m pytest -q
# 8 tests

# Robot Framework (acceptance tests)
pip install robotframework           # if not already installed
python -m robot tests/illumination.robot tests/surface.robot
# 26 tests (16 illumination + 10 surface)
```

---

## Design notes

- All physical quantities use SI units (metres, Watts, radians).
- The `LightField.visualize()` method draws a Unicode block-character
  heatmap in the terminal — no plotting library required.
- Surface generators are deterministic by default where possible
  (fixed RNG seed in `ParticleSurface`).
- The `_gaussian_filter` helper in `surface/generators.py` is a
  pure-NumPy separable convolution that avoids a SciPy dependency.