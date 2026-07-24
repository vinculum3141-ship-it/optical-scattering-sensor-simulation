# optical-scattering-sensor-simulation

A physics-based simulation framework for optical scattering sensors. The repository currently focuses on the illumination side of the system: describing a light source in a physically meaningful way and turning that description into a light field that can later be used by downstream scattering, optics, and detector modules.

## Quick start

### Requirements

- Python 3.9+
- [NumPy](https://numpy.org/)

### Try the interactive explorer

The fastest way to get a feel for the code is to run the explorer script:

```bash
python explore.py
```

This starts an interactive menu with six predefined scenarios (laser, LED, sunlight, broadband lamp, etc.). You can also run a single scenario non-interactively:

```bash
python explore.py --run 1
python explore.py --list      # list all available scenarios
python explore.py --all       # run all scenarios
```

### Use the API directly

```python
from illumination import Laser, GaussianBeamProfile

laser = Laser(
    wavelength=532e-9,
    power=5e-3,
    beam_profile=GaussianBeamProfile(w0=1.0),
)

field = laser.generate_light_field(shape=(64, 64), spacing=1.0)
print(field.intensity.shape)
print(field.direction.shape)
```

This creates a laser source, assigns a Gaussian beam profile, and generates a light field over a 2D grid.

## Project goal

The long-term goal is to simulate how a sensor responds to scattered light under different source, geometry, and material conditions. The current implementation establishes the first building block of that pipeline: a reusable representation of optical illumination.

## What is implemented

The project now includes an illumination package with a small, modular API for describing light sources.

### Core concepts

- **Light source**: a physical description of an emitter, including wavelength, power, direction, polarization, coherence, beam shape, and divergence.
- **Light field**: a structured output describing the illumination over a spatial grid, including intensity, direction, wavelength, and polarization state.
- **Spectral model**: a representation of the wavelength content of the source.
- **Beam profile**: a model for how intensity is distributed across space.

### Source types

| Class | Spectrum | Default beam shape | Typical divergence |
|---|---|---|---|
| `illumination.Laser` | Monochromatic | Uniform (top-hat) | 1 mrad |
| `illumination.LED` | Gaussian | Gaussian | 0.5 rad |
| `illumination.Sunlight` | Black-body | Uniform | 0.53 rad |
| `illumination.BroadbandLamp` | Flat (broadband) | Uniform | 0.5 rad |

### Package structure

| File | Contents |
|---|---|
| `illumination/source.py` | Base `LightSource` dataclass |
| `illumination/laser.py` | Laser source |
| `illumination/led.py` | LED source |
| `illumination/sunlight.py` | Sunlight source |
| `illumination/broadband.py` | Broadband lamp |
| `illumination/profiles.py` | `UniformBeamProfile`, `TopHatBeamProfile`, `GaussianBeamProfile` |
| `illumination/spectrum.py` | `MonochromaticSpectrum`, `GaussianSpectrum`, `BlackbodySpectrum`, `BroadbandSpectrum` |
| `illumination/polarization.py` | `PolarizationState` |
| `illumination/lightfield.py` | `LightField` data structure |
| `illumination/__init__.py` | Package exports |
| `explore.py` | Interactive exploration script |
| `tests/test_illumination.py` | Pytest unit tests |
| `tests/illumination.robot` | Robot Framework acceptance tests |
| `tests/IlluminationLibrary.py` | Robot Framework test library |

## Design philosophy

The illumination layer is intentionally kept independent of the scene. Its job is to describe the incoming electromagnetic field, not to decide how that field interacts with a surface. That separation makes the code easier to extend later when scattering, reflection, propagation, and detector behavior are added.

## Testing

### Pytest (unit tests)

```bash
python -m pytest -q
```

4 tests covering default values, light field generation, direction normalisation, and subclass spectral models.

### Robot Framework (acceptance tests)

```bash
# install Robot Framework if needed
pip install robotframework

# run the tests
robot tests/illumination.robot
```

16 tests covering source creation, spectrum types, polarization states, light field generation, beam profile evaluation, and field properties.

## Next steps

The next logical step is to connect this illumination model to a surface interaction module so that the generated light field can be used to simulate scattering, reflection, and sensor response.
