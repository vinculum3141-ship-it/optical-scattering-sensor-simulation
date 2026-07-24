# optical-scattering-sensor-simulation

A physics-based simulation framework for optical scattering sensors. The
repository implements three layers of the simulation pipeline:

1. **Illumination** — describe a light source and generate a light field
   over a 2D grid.
2. **Surface geometry** — model a surface via a height map and derive
   geometric quantities (normals, slopes, curvature, roughness).
3. **Scattering** — given an incident light field, a surface, and a view
   direction, compute the radiance scattered toward the observer.

---

## Quick start

### Requirements

- Python 3.9+
- [NumPy](https://numpy.org/)

### Interactive explorer

Three modes, switch between them inside the menu with `[i]` (illumination),
`[s]` (surface), or `[c]` (scattering):

```bash
python explore.py                # illumination scenarios
python explore.py --surface      # surface-geometry scenarios
python explore.py --scattering   # scattering scenarios (all layers combined)
```

Non-interactive commands (same flags for all three modes):

```bash
python explore.py --list                # list illumination scenarios
python explore.py --surface --list      # list surface scenarios
python explore.py --scattering --list   # list scattering scenarios
python explore.py --run 1               # run illumination scenario 1
python explore.py --surface --run 2     # run surface scenario 2
python explore.py --scattering --run 1  # run scattering scenario 1
python explore.py --all                 # run all illumination scenarios
python explore.py --surface --all       # run all surface scenarios
python explore.py --scattering --all    # run all scattering scenarios
```

Each scenario prints a description of the setup, then renders a 2D terminal
heatmap of the relevant field (intensity, height, or scattered radiance).

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

```python
from illumination import Laser, GaussianBeamProfile
from surface import FlatSurface, Material
from scattering import LambertianScattering

laser = Laser(wavelength=532e-9, power=5e-3,
              beam_profile=GaussianBeamProfile(w0=2.0))
laser.propagation_direction = [0, 0, -1]

lightfield = laser.generate_light_field(shape=(32, 32), spacing=0.5)
surface = FlatSurface((32, 32), material=Material("glass"))
model = LambertianScattering(albedo=0.8)

result = model.evaluate(lightfield, surface, view_direction=[0, 0, 1])
print(result.radiance.shape)   # (32, 32)
print(result.radiance.min(), result.radiance.max())
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
| `illumination/profiles.py` | `UniformBeamProfile`, `TopHatBeamProfile`, `GaussianBeamProfile` |
| `illumination/spectrum.py` | `MonochromaticSpectrum`, `GaussianSpectrum`, `BlackbodySpectrum`, `BroadbandSpectrum` |
| `illumination/polarization.py` | `PolarizationState` |
| `illumination/lightfield.py` | `LightField` with terminal heatmap (`visualize()`) |
| `illumination/__init__.py` | Package exports |

### Surface geometry layer

| File | Contents |
|---|---|
| `surface/base.py` | `Surface`, `Material`, `GeometryAnalyzer`, `SurfaceGenerator` |
| `surface/generators.py` | `FlatSurface`, `RoughSurface`, `ScratchedSurface`, `ParticleSurface` |
| `surface/__init__.py` | Package exports |

### Scattering layer

| File | Contents |
|---|---|
| `scattering/base.py` | `ScatteringModel` base, `ScatteredField` output container |
| `scattering/lambertian.py` | `LambertianScattering` (diffuse, cosine-law) |
| `scattering/__init__.py` | Package exports |

### Scripts and tests

| File | Contents |
|---|---|
| `explore.py` | Interactive CLI (illumination / surface / scattering modes) |
| `tests/test_illumination.py` | Pytest (4 tests) |
| `tests/test_surface.py` | Pytest (4 tests) |
| `tests/test_scattering.py` | Pytest (5 tests) |
| `tests/IlluminationLibrary.py` | Robot Framework test library for illumination |
| `tests/illumination.robot` | Robot Framework acceptance tests (16 tests) |
| `tests/SurfaceLibrary.py` | Robot Framework test library for surface |
| `tests/surface.robot` | Robot Framework acceptance tests (10 tests) |
| `tests/ScatteringLibrary.py` | Robot Framework test library for scattering |
| `tests/scattering.robot` | Robot Framework acceptance tests (5 tests) |

---

## Project goal

Simulate how a sensor responds to scattered light under different source,
geometry, and material conditions. Each layer is kept independent so that
they can be extended, replaced, or recombined without coupling.

- **Illumination** describes the incoming electromagnetic field. It does
  not know about surfaces or scattering models.
- **Surface** describes the object geometry via a 2D height map and derived
  quantities (normals, slopes, curvature, roughness). It does not know
  about light.
- **Scattering** connects the two: given an incident light field, a
  surface, and an observation direction, it computes the scattered
  radiance.

## Scattering layer

The scattering layer answers:

> given incoming light, a surface, and an observation direction, how much
> light is reflected toward that direction?

It produces a `ScatteredField` holding radiance and outgoing direction at
each grid point — a structured result that downstream modules (optics,
detectors, visualisation) can consume without knowing the scattering model
internals.

### Lambertian model

The current implementation is a Lambertian diffuse model:

```
radiance = albedo × max(dot(to_light, normal), 0)
```

where `to_light` is the direction from the surface toward the light source
(obtained by negating the light field's propagation direction). This
provides a clean baseline for future models (Phong, Oren–Nayar,
Cook–Torrance, etc.).

---

## Testing

```bash
# Pytest (unit tests) — all three layers
python -m pytest -q
# 13 tests

# Robot Framework (acceptance tests)
pip install robotframework           # if not already installed
python -m robot tests/illumination.robot tests/surface.robot tests/scattering.robot
# 31 tests (16 illumination + 10 surface + 5 scattering)
```

---

## Design notes

- All physical quantities use SI units (metres, Watts, radians).
- The `LightField.visualize()` method draws a Unicode block-character
  heatmap in the terminal — no plotting library required.
- Surface generators are deterministic by default where possible (fixed
  RNG seed in `ParticleSurface`).
- The `_gaussian_filter` helper in `surface/generators.py` is a pure-NumPy
  separable convolution that avoids a SciPy dependency.
- Lambert's law uses the direction from the surface toward the light
  source (`-lightfield.direction`), not the propagation direction itself.