# Optics Layer

> **Target audience:** Both — imaging physics for scientists, PSF
> convolution and propagation API for engineers.

## Overview

The optics layer propagates a scattered radiance field through an imaging
system to produce the sensor-plane irradiance distribution. It is the
first layer that connects physical scattering to a measurement-oriented
representation.

**File location:** `optics/`

## Model

The propagation is modelled as a spatially invariant convolution of the
scattered radiance with a point-spread function (PSF):

    E_sensor(x, y) = (L_scattered ∗ PSF)(x, y)

where ∗ denotes 2D convolution. This models an **incoherent, paraxial**
imaging system with a **spatially invariant** PSF.

### Optical System

```python
OpticalSystem(
    aperture_diameter=0.01,   # entrance pupil diameter (m)
    focal_length=0.1,          # effective focal length (m)
    numerical_aperture=None,   # auto-computed as D/(2f)
    magnification=1.0,         # lateral magnification
    wavelength=532e-9,         # design wavelength (m)
    psf=None,                  # PSF model reference
    aberrations=None,          # reserved for future use
)
```

### PSF Models

| Model | Class | Parameters | Use Case |
|---|---|---|---|
| Gaussian | `GaussianPSF` | sigma (pixels) | Simple blur, fast convolution |
| Airy disk | `AiryPSF` | wavelength, numerical_aperture, pixel_size | Diffraction-limited imaging |

### Gaussian PSF

An isotropic 2D Gaussian kernel:

    PSF(x, y) ∝ exp(-(x² + y²) / (2σ²))

The kernel is normalised to unit sum so energy is conserved during
convolution. The **σ** parameter controls the blur width (in pixels).

### Airy Disk PSF

The Airy disk is the PSF of a perfect circular aperture in the
Fraunhofer diffraction regime.  It represents the theoretical best
focus achievable by an aberration-free optical system.

    I(r) = (2 × J1(k × NA × r) / (k × NA × r))²

where J1 is the first-order Bessel function, k = 2π/λ is the
wavenumber, NA is the numerical aperture, and r is the radial
coordinate in the image plane.

```python
from optics import AiryPSF

psf = AiryPSF(wavelength=532e-9, numerical_aperture=0.25, pixel_size=5e-6)
kernel = psf.kernel(size=31)  # normalised 31×31 kernel
```

The Bessel function J1 is computed via a series expansion — no SciPy
dependency required.

## Propagation

`OpticalPropagator` performs direct 2D convolution of the scattered
radiance with the PSF kernel:

1. Pad the radiance array (zero-padding).
2. For each pixel, extract the overlapping PSF-sized patch.
3. Compute the dot product with the PSF kernel.
4. The result becomes the sensor-plane irradiance.

This is O(H·W·K²) where K is the kernel size. For larger grids, the
commentary in the code suggests replacing with FFT-based convolution
(e.g. `scipy.signal.fftconvolve`).

### Default PSF

If no PSF model is provided, a 3×3 box filter (uniform average) is used:

    PSF_default = [[1/9, 1/9, 1/9], ...]

## Key API

```python
from optics import OpticalSystem, GaussianPSF, OpticalPropagator

# Configure the imaging system
optics = OpticalSystem(
    focal_length=0.05,         # 50 mm
    aperture_diameter=0.008,   # 8 mm → NA = 0.08
    wavelength=532e-9,
)

# Create the propagator with a PSF model
propagator = OpticalPropagator(psf_model=GaussianPSF(sigma=1.5))

# Propagate a scattered field to the sensor plane
sensor_field = propagator.propagate(scattered_field, optics)

# Result
sensor_field.irradiance        # (H, W) ndarray — W/m²
sensor_field.wavelength        # carried through from optics config
sensor_field.polarization      # carried through from scattered field
sensor_field.optical_path_length  # set to focal_length
```

## Implementation Notes

### Convolution Strategy

The propagator uses a manual sliding-window convolution for clarity and
zero-dependency operation. Key points:

- **Padding** — zero-padding with half-kernel width on each side.
- **No FFT** — the O(HWK²) approach is intentional for transparency.
  The code comment explicitly identifies this as a point for optimisation.
- **PSF kernel generation** — `psf_model.kernel(size)` returns a
  normalised 2D array. The size is `max(3, int(4σ))`.

### SensorField Container

```python
@dataclass
class SensorField:
    irradiance: np.ndarray         # W/m²
    wavelength: float              # m
    polarization: object | None
    optical_path_length: float     # m
```

This is the output data contract consumed by the detector layer.

### Limitation: No Coordinate Transform

The current implementation does **not** apply magnification, image
inversion, or coordinate transformations. The grid dimensions of the
`SensorField` are the same as the input `ScatteredField`. Magnification
is stored in `OpticalSystem` but is not yet used for grid resampling.

## Complete Example

```python
from optics import OpticalSystem, GaussianPSF, OpticalPropagator

optics = OpticalSystem(
    focal_length=0.1,
    aperture_diameter=0.01,
    wavelength=532e-9,
    magnification=1.0,
)
propagator = OpticalPropagator(psf_model=GaussianPSF(sigma=1.2))
sensor = propagator.propagate(scattered_field, optics)

print(f"NA = {optics.numerical_aperture:.4f}")
print(f"Irradiance: {sensor.irradiance.min():.4g} — {sensor.irradiance.max():.4g} W/m²")
```

## Custom PSF Models

Implement an object with a `kernel(size)` method:

```python
class AiryPSF:
    def __init__(self, wavelength, numerical_aperture):
        self.wavelength = wavelength
        self.na = numerical_aperture

    def kernel(self, size=15):
        # Compute Airy disk pattern
        # ...
        return kernel / kernel.sum()  # normalised
```

The propagator only calls `.kernel(size)` and expects a 2D array
normalised to unit sum.
