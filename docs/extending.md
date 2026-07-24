# Extending the Framework

> **Target audience:** Software engineers, R&D developers, contributors.

## Introduction

The framework is designed for extension. Each layer defines abstract
interfaces and data contracts that you can implement without modifying
existing code. This document walks through every extension point with
complete examples.

## 1. Custom Light Source

**Interface:** Subclass `LightSource` and override `default_spectrum()`.

```python
from illumination import LightSource, BlackbodySpectrum

class HalogenLamp(LightSource):
    """A halogen lamp modelled as a high-temperature black-body."""
    def __init__(self, temperature=3200.0, power=50.0, **kwargs):
        super().__init__(
            wavelength=700e-9,  # approximate centre
            power=power,
            divergence=0.8,     # wide divergence
            **kwargs,
        )
        self.spectrum = BlackbodySpectrum(temperature=temperature)

    def default_spectrum(self):
        return BlackbodySpectrum(temperature=3200.0)
```

The base class handles beam-profile evaluation, direction normalisation,
and `generate_light_field()`. You only provide the spectral model.

## 2. Custom Beam Profile

**Interface:** Subclass `BeamProfile` and implement `evaluate(shape, spacing)`.

```python
from illumination.profiles import BeamProfile
import numpy as np

class DonutBeamProfile(BeamProfile):
    """A 'donut' (Laguerre-Gaussian LG01) transverse profile."""
    def __init__(self, w0=1.0, ring_radius=2.0):
        self.w0 = w0
        self.ring_radius = ring_radius

    def evaluate(self, shape, spacing=1.0):
        h, w = shape
        y = np.arange(h) - (h - 1) / 2
        x = np.arange(w) - (w - 1) / 2
        yy, xx = np.meshgrid(y, x, indexing="ij")
        r = np.sqrt(xx**2 + yy**2)
        # LG01-like: intensity peaks at a ring
        return (r**2 / self.w0**2) * np.exp(-r**2 / self.w0**2)
```

## 3. Custom Surface Generator

**Option A:** Subclass `SurfaceGenerator` (implement `generate()` only):

```python
from surface import SurfaceGenerator, GeometryAnalyzer, Material

class SinusoidalSurface(SurfaceGenerator):
    def __init__(self, wavelength=16.0, amplitude=0.5):
        self.wavelength = wavelength
        self.amplitude = amplitude

    def generate(self, shape):
        h, w = shape
        x = np.arange(w) - w / 2
        y = np.arange(h) - h / 2
        yy, xx = np.meshgrid(y, x, indexing="ij")
        return self.amplitude * np.sin(2 * np.pi * xx / self.wavelength)

# Usage:
gen = SinusoidalSurface(wavelength=20, amplitude=0.3)
surface = gen.create_surface((64, 64), material=Material("glass"))
```

**Option B:** Create a class that **is** both a surface and a generator
(follows the existing pattern):

```python
from surface import Surface, SurfaceGenerator, GeometryAnalyzer, Material
import numpy as np

class CheckerboardSurface(Surface, SurfaceGenerator):
    def __init__(self, shape, tile_size=8, material=None):
        self.tile_size = tile_size
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material or Material())
        self.__dict__.update(surface.__dict__)

    def generate(self, shape):
        h, w = shape
        # Creates a checkerboard pattern of height 0 and 1
        indices = np.indices((h, w))
        return ((indices[0] // self.tile_size + indices[1] // self.tile_size) % 2).astype(float)

# Usage — constructor produces a Surface directly:
surf = CheckerboardSurface((32, 32), tile_size=8, material=Material("ceramic"))
print(surf.height.min(), surf.height.max())
```

## 4. Custom Scattering Model

**Interface:** Subclass `ScatteringModel` and implement `evaluate()`.

```python
from scattering import ScatteringModel, ScatteredField
import numpy as np

class PhongScattering(ScatteringModel):
    """Phong reflection model: diffuse + specular."""
    def __init__(self, diffuse_albedo=0.6, specular_albedo=0.4, shininess=32):
        self.diffuse = diffuse_albedo
        self.specular = specular_albedo
        self.shininess = shininess

    def evaluate(self, lightfield, surface, view_direction):
        incoming = np.asarray(lightfield.direction, dtype=float)
        normals = np.asarray(surface.normals, dtype=float)
        view = np.asarray(view_direction, dtype=float)
        view = view / np.linalg.norm(view)
        to_light = -incoming

        # Diffuse (Lambertian)
        cos_i = np.einsum("...i,...i->...", to_light, normals)
        cos_i = np.clip(cos_i, 0.0, None)
        diffuse = self.diffuse * cos_i

        # Specular (Phong)
        # R = 2 * (N·L) * N - L
        R = 2 * cos_i[..., None] * normals - to_light
        cos_r = np.einsum("...i,...i->...", R, view[None, None, :])
        cos_r = np.clip(cos_r, 0.0, None)
        specular = self.specular * (cos_r ** self.shininess)

        radiance = diffuse + specular
        H, W = radiance.shape
        outgoing = np.broadcast_to(view, (H, W, 3))

        return ScatteredField(
            radiance=radiance,
            outgoing_direction=outgoing.copy(),
            polarization=lightfield.polarization,
        )
```

## 5. Custom PSF Model

**Interface:** Any object with a `kernel(size)` method returning a
normalised 2D array.

```python
import numpy as np

class BoxPSF:
    """Simple uniform box blur."""
    def __init__(self, radius=2):
        self.radius = radius

    def kernel(self, size=None):
        k = self.radius * 2 + 1
        return np.ones((k, k), dtype=float) / (k * k)

class AiryPSF:
    """Diffraction-limited Airy disk (approximate)."""
    def __init__(self, wavelength=532e-9, na=0.25, pixel_size=1e-6):
        self.wavelength = wavelength
        self.na = na
        self.pixel_size = pixel_size

    def kernel(self, size=31):
        coords = np.arange(size) - size // 2
        xx, yy = np.meshgrid(coords, coords)
        r = np.sqrt(xx**2 + yy**2) * self.pixel_size
        k = 2 * np.pi * self.na / self.wavelength
        # Jinc function: (J1(kr) / kr)^2
        kr = k * r
        with np.errstate(divide="ignore", invalid="ignore"):
            airy = (2 * np.sin(kr) / kr) ** 2  # far-field approx
        airy[kr == 0] = 1.0
        return airy / airy.sum()

# Usage:
propagator = OpticalPropagator(psf_model=AiryPSF(na=0.4))
```

## 6. Custom Detector Noise Model

**Interface:** Subclass `DetectorNoiseModel` and implement `apply(electrons)`.

```python
from detector import DetectorNoiseModel
import numpy as np

class ColumnDefectNoise(DetectorNoiseModel):
    """Simulates a defective column with reduced sensitivity."""
    def __init__(self, column_index=0, scale_factor=0.5):
        self.col = column_index
        self.scale = scale_factor

    def apply(self, electrons):
        electrons[:, self.col] *= self.scale
        return electrons

class HotPixelNoise(DetectorNoiseModel):
    """Random hot pixels with high dark current."""
    def __init__(self, density=0.001, hot_current=1000.0, exposure_time=0.1):
        self.density = density
        self.hot_current = hot_current * exposure_time

    def apply(self, electrons):
        mask = np.random.random(electrons.shape) < self.density
        electrons[mask] += np.random.poisson(self.hot_current, size=mask.sum())
        return electrons

# Usage:
detector = CMOSDetector(
    exposure_time=0.1,
    noise_models=[ColumnDefectNoise(column_index=32), HotPixelNoise(density=0.0005)],
)
```

## 7. Custom Analysis Module

**Interface:** Subclass `AnalysisModule` and implement `analyze(image)`.

```python
from analysis import AnalysisModule, AnalysisReport
from scipy import ndimage  # optional dependency

class ContrastAnalyzer(AnalysisModule):
    """Compute RMS contrast of the image."""
    def analyze(self, image):
        pixels = image.pixels.astype(float)
        rms_contrast = float(pixels.std() / pixels.mean()) if pixels.mean() > 0 else 0.0
        return AnalysisReport(measurements={"rms_contrast": rms_contrast})

class MTFAnalyzer(AnalysisModule):
    """Estimate modulation transfer function from edge."""
    def analyze(self, image):
        # Edge detection, line spread function, MTF computation
        # ...
        return AnalysisReport(measurements={"mtf50": mtf50_value})

# Compose:
analyzer = ImageAnalyzer(modules=[
    HistogramAnalyzer(),
    ContrastAnalyzer(),
    MTFAnalyzer(),
])
```

## 8. Full Custom Pipeline

```python
from illumination import LightSource, UniformBeamProfile, PolarizationState
from surface import SurfaceGenerator, GeometryAnalyzer, Material
from scattering import ScatteringModel, ScatteredField
from optics import OpticalPropagator, OpticalSystem
from detector import CMOSDetector, DetectorNoiseModel
from analysis import ImageAnalyzer, HistogramAnalyzer

# Create a custom source
source = LightSource(
    wavelength=780e-9,
    power=10e-3,
    beam_profile=UniformBeamProfile(),
    polarization=PolarizationState("circular"),
)
source.propagation_direction = [0.5, 0, -0.87]  # 30° incidence

# Generate light field
lf = source.generate_light_field(shape=(32, 32), spacing=0.5)

# Custom surface + scattering (using built-in for brevity)
from surface import RoughSurface
from scattering import LambertianScattering
surface = RoughSurface((32, 32), sigma=5.0, amplitude=0.3, material=Material("silicon"))
scattered = LambertianScattering(albedo=0.7).evaluate(lf, surface, view=[0, 0, 1])

# Custom noise
class SaltAndPepperNoise(DetectorNoiseModel):
    def __init__(self, salt_prob=0.01, pepper_prob=0.01, salt_val=1e6, pepper_val=0):
        self.p_salt = salt_prob
        self.p_pepper = pepper_prob
        self.salt = salt_val
        self.pepper = pepper_val

    def apply(self, electrons):
        salt = np.random.random(electrons.shape) < self.p_salt
        pepper = np.random.random(electrons.shape) < self.p_pepper
        electrons = np.where(salt, self.salt, electrons)
        electrons = np.where(pepper, self.pepper, electrons)
        return electrons

# Run the full pipeline with custom noise
optics = OpticalSystem(focal_length=0.05, aperture_diameter=0.008, wavelength=780e-9)
sensor = OpticalPropagator().propagate(scattered, optics)
detector = CMOSDetector(exposure_time=1e-5, noise_models=[SaltAndPepperNoise()])
image = detector.capture(sensor)
report = ImageAnalyzer(modules=[HistogramAnalyzer()]).analyze(image)
print(report.measurements)
```

## Extension Summary

| What to extend | Interface | Method to implement |
|---|---|---|
| Light source | `LightSource` | `default_spectrum()` |
| Beam profile | `BeamProfile` | `evaluate(shape, spacing)` |
| Surface generator | `SurfaceGenerator` | `generate(shape)` |
| Scattering model | `ScatteringModel` | `evaluate(lightfield, surface, view_direction)` |
| PSF model | Any object | `kernel(size)` → normalised 2D array |
| Detector noise | `DetectorNoiseModel` | `apply(electrons)` |
| Analysis module | `AnalysisModule` | `analyze(image)` |

In every case, the framework handles orchestration, data flow, and
I/O — you only provide the domain-specific computation.
