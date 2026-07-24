# optical-scattering-sensor-simulation

A physics-based simulation framework for optical scattering sensors. The
repository implements five layers of the simulation pipeline:

1. **Illumination** — describe a light source and generate a light field
   over a 2D grid.
2. **Surface geometry** — model a surface via a height map and derive
   geometric quantities (normals, slopes, curvature, roughness).
3. **Scattering** — given an incident light field, a surface, and a view
   direction, compute the radiance scattered toward the observer.
4. **Optics** — propagate a scattered field through an imaging system to
   produce a sensor-plane image.
5. **Detector** — convert the optical sensor field into a digital image
   with noise, full-well saturation, and ADC quantisation.

---

## Getting started

### Requirements

- Python 3.9+
- [NumPy](https://numpy.org/) (optional for Robot Framework tests: `robotframework`)

### Where to start

**New to the project?** The fastest way to see what the framework can do:

```bash
python playground.py --demo
```

This runs a non-interactive tour through all five layers with terminal
heatmap visualisations. Then dive into the interactive menu:

```bash
python playground.py
```

The playground has seven options covering each layer individually plus
an end-to-end custom pipeline example and a tinker mode with code snippets.

### Interactive explorer

The original explorer script works across three modes; switch between them
inside the menu with `[i]` (illumination), `[s]` (surface), or `[c]`
(scattering):

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

```python
from detector import CMOSDetector
from optics import SensorField
import numpy as np

sensor_field = SensorField(
    irradiance=np.ones((8, 8)) * 1e3,
    wavelength=532e-9,
)
detector = CMOSDetector(exposure_time=0.1, bit_depth=12)
image = detector.capture(sensor_field)
print(image.pixels.shape)   # (8, 8)
print(image.pixels.dtype)   # uint16
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

### Optics layer

| File | Contents |
|---|---|
| `optics/base.py` | `OpticalSystem` and `SensorField` containers |
| `optics/psf.py` | `GaussianPSF` for simple point-spread-function modelling |
| `optics/propagator.py` | `OpticalPropagator` that applies PSF-based blur to a scattered field |
| `optics/__init__.py` | Package exports |

### Detector layer

| File | Contents |
|---|---|
| `detector/base.py` | `CMOSDetector`, `DigitalImage`, `DetectorNoiseModel` |
| `detector/__init__.py` | Package exports |

### Scripts and tests

| File | Contents |
|---|---|
| `explore.py` | Interactive CLI (illumination / surface / scattering modes) |
| `playground.py` | Interactive playground with demos, custom pipeline, and code snippets |
| `tests/test_illumination.py` | Pytest (4 tests) |
| `tests/test_surface.py` | Pytest (4 tests) |
| `tests/test_scattering.py` | Pytest (5 tests) |
| `tests/test_optics.py` | Pytest (1 test) |
| `tests/test_detector.py` | Pytest (1 test) |
| `tests/IlluminationLibrary.py` | Robot Framework test library for illumination |
| `tests/illumination.robot` | Robot Framework acceptance tests (16 tests) |
| `tests/SurfaceLibrary.py` | Robot Framework test library for surface |
| `tests/surface.robot` | Robot Framework acceptance tests (10 tests) |
| `tests/ScatteringLibrary.py` | Robot Framework test library for scattering |
| `tests/scattering.robot` | Robot Framework acceptance tests (5 tests) |
| `tests/DetectorLibrary.py` | Robot Framework test library for detector |
| `tests/detector.robot` | Robot Framework acceptance tests (6 tests) |

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
- **Optics** transforms scattered radiance into a sensor-plane irradiance
  distribution via PSF-based convolution.
- **Detector** converts the optical field into a digital image, modelling
  shot noise, dark current, read noise, saturation, and ADC quantisation.

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

## Optics layer

The optics layer is the first stage that connects the physical scattering
response to a measurement-oriented representation. It does not create light
or decide what the surface should do; it transforms the scattered field into
what would appear at the sensor plane.

### What the optics module does

1. Accepts a `ScatteredField` and an `OpticalSystem` description.
2. Uses a point-spread-function (PSF) model to redistribute the radiance
   across the sensor plane.
3. Produces a `SensorField` containing the resulting irradiance and the
   wavelength and path-length context of the propagation.

### Current implementation

The current optics module uses a simple Gaussian PSF and a basic
propagator. The propagation step applies a blur kernel over the scattered
radiance field, which is the simplest way to represent the effect of an
optical system on a field before it reaches a detector. This gives the
simulator a working imaging-style pipeline that can later be extended to
more realistic PSFs, aberrations, and diffraction models.

## Detector layer

The detector layer is the final stage: it converts the optical sensor field
into a digital image that would be read out from a real sensor.

### Pipeline steps

1. **Photon conversion** — irradiance (W/m²) → incident photons via
   :math:`E = hc/λ`.
2. **Quantum efficiency** — scale by QE to get photoelectrons.
3. **Shot noise** — Poisson-distributed photon arrival statistics.
4. **Dark current** — thermally generated electrons (Poisson).
5. **Read noise** — Gaussian noise from the readout electronics.
6. **Full-well clip** — saturation at the maximum electron capacity.
7. **ADC quantisation** — convert electrons to digital counts (ADU) at
   the specified bit depth.

### Current implementation: `CMOSDetector`

```python
from detector import CMOSDetector, DetectorNoiseModel

detector = CMOSDetector(
    exposure_time=0.1,       # seconds
    quantum_efficiency=0.9,  # electrons per photon
    dark_current=5.0,        # electrons per second
    read_noise_sigma=2.0,    # electrons (standard deviation)
    full_well_capacity=80000.0,
    gain=2.0,                # electrons per ADU
    bit_depth=12,
)
```

Custom noise stages can be added by subclassing `DetectorNoiseModel` and
passing instances to the `noise_models` parameter.

---

## Testing

```bash
# Pytest (unit tests) — all five layers
python -m pytest -q
# 15 tests passed

# Robot Framework (acceptance tests)
pip install robotframework           # if not already installed
python -m robot tests/illumination.robot tests/surface.robot tests/scattering.robot tests/detector.robot
# 37 tests passed (16 illumination + 10 surface + 5 scattering + 6 detector)
```

---

## Design notes

- All physical quantities use SI units (metres, Watts, radians, seconds).
- The `CMOSDetector` uses stochastic noise models (Poisson shot noise,
  Poisson dark current, Gaussian read noise) so outputs vary between runs.
  Tests use statistical bounds rather than exact values.
- The `LightField.visualize()` method draws a Unicode block-character
  heatmap in the terminal — no plotting library required.
- Surface generators are deterministic by default where possible (fixed
  RNG seed in `ParticleSurface`).
- The `_gaussian_filter` helper in `surface/generators.py` is a pure-NumPy
  separable convolution that avoids a SciPy dependency.
- Lambert's law uses the direction from the surface toward the light
  source (`-lightfield.direction`), not the propagation direction itself.