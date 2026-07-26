# Illumination Layer

> **Target audience:** Both — physics models for scientists, API and
> implementation details for engineers.

## Overview

The illumination layer models optical sources in physically meaningful
terms. It produces a `LightField` — a structured array of intensity,
direction, wavelength, and polarisation over a 2D grid.

**File location:** `illumination/`

## Source Types

### Laser (`Laser`)
- Monochromatic (single-wavelength) spectrum.
- Low divergence (default 1 mrad).
- Configurable beam profile (default uniform).

### LED (`LED`)
- Gaussian-shaped emission spectrum (default 530 nm peak, 25 nm FWHM).
- Moderate divergence (default 0.5 rad).
- Defaults to a Gaussian beam profile.

### Sunlight (`Sunlight`)
- Black-body spectrum at 5778 K (effective solar temperature).
- Divergence of 0.53 rad (solar angular diameter from Earth).

### Broadband Lamp (`BroadbandLamp`)
- Flat spectrum over a configurable range (default 400-700 nm).
- Moderate divergence (default 0.5 rad).

## Beam Profiles

| Profile | Class | Equation | Use case |
|---|---|---|---|
| Uniform | `UniformBeamProfile` | I(x,y) = 1 | Idealised collimated beam |
| Gaussian | `GaussianBeamProfile` | I(r) = exp(-2r²/w₀²) | Laser TEM00 mode |
| TopHat | `TopHatBeamProfile` | I = 1 within aperture | Beam-expander output |

## Spectral Models

| Model | Class | Parameters |
|---|---|---|
| Monochromatic | `MonochromaticSpectrum` | wavelength |
| Gaussian line | `GaussianSpectrum` | peak_wavelength, width (FWHM) |
| Blackbody | `BlackbodySpectrum` | temperature |
| Broadband | `BroadbandSpectrum` | wavelength_range |

## Key API

### LightSource

```python
source = LightSource(
    wavelength=532e-9,       # centre wavelength (m)
    power=1.0,                # total optical power (W)
    polarization="unpolarized",  # or PolarizationState
    beam_profile="uniform",   # or BeamProfile instance
    propagation_direction=[0, 0, 1],  # auto-normalised
    divergence=0.0,           # full-angle divergence (rad)
    coherence_length=1e-3,    # temporal coherence length (m)
    wavefront="planar",       # "planar" or "spherical"
)
field = source.generate_light_field(shape=(64, 64), spacing=1.0)
```

### LightField

```python
field.intensity    # ndarray (H, W) — irradiance in W/m²
field.direction    # ndarray (H, W, 3) — unit propagation vectors
field.wavelength   # float — centre wavelength in m
field.polarization # PolarizationState
field.coherence_length  # float — temporal coherence length (m)
field.phase        # ndarray or None

print(field.visualize(max_width=80, color=True))  # terminal heatmap
```

## Implementation Notes

### LightSource Dataclass

`LightSource` is a `@dataclass` with `__post_init__` normalisation:

- `propagation_direction` is normalised to unit length. Zero vectors
  raise `ValueError`.
- String-typed parameters (`polarization`, `beam_profile`) are converted
  to their object counterparts.
- `spectrum` defaults to `default_spectrum()` which subclasses override.

### LightField Generation

`generate_light_field()`:

1. Evaluates the beam profile on the requested grid.
2. Scales by total power.
3. Replicates the propagation direction across every grid point.
4. Returns a `LightField` with the computed intensity and direction.

The direction is **constant** across the grid — the beam is always
collimated at the available resolution. Divergence is recorded as a
parameter but not used to modify the direction map.

### Wavefront

Set ``wavefront="planar"`` (default) for a collimated beam with a
constant direction, or ``wavefront="spherical"`` for a point source
that emits from ``origin`` with per-pixel directions computed
automatically.

### Incidence Angle

``incidence_angle`` (radians) and ``incidence_angle_degrees`` derive
from ``propagation_direction`` assuming a surface normal of [0, 0, 1].
Setting one updates the other.

```python
source = Laser(wavelength=532e-9)
source.incidence_angle = np.radians(30)  # sets propagation_direction
```

### Coherence Length

``coherence_length`` (default 1 mm for lasers, 10 µm for LEDs) sets
the temporal coherence length of the source. This propagates into the
``LightField`` and is consumed by downstream speckle models.

### Subclass Pattern

Concrete sources override `default_spectrum()`:

```python
class Laser(LightSource):
    def default_spectrum(self):
        return MonochromaticSpectrum(wavelength=self.wavelength)
```

This lets the base `__post_init__` handle everything else uniformly.

## Complete Example

```python
from illumination import Laser, GaussianBeamProfile, PolarizationState

laser = Laser(
    wavelength=532e-9,
    power=5e-3,
    beam_profile=GaussianBeamProfile(w0=2.0),
    polarization=PolarizationState("linear"),
)
laser.propagation_direction = [0, 0, -1]
field = laser.generate_light_field(shape=(32, 32), spacing=0.5)

print(f"Peak intensity: {field.intensity.max():.4g} W/m²")
print(f"Polarisation:   {field.polarization.kind}")
```

## Creating a Custom Source

Subclass `LightSource` and override `default_spectrum()`:

```python
from illumination import LightSource, MonochromaticSpectrum

class MySource(LightSource):
    def default_spectrum(self):
        return MonochromaticSpectrum(wavelength=self.wavelength)
```
