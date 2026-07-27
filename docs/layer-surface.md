# Surface Geometry Layer

> **Target audience:** Both — geometry and roughness physics for scientists,
> generator patterns and API for engineers.

## Overview

The surface layer models object geometry via 2D height maps and derives
geometric quantities — normals, slopes, curvature, and roughness — using
finite-difference methods. It does **not** know about light or scattering.

**File location:** `surface/`

## Surface Types

| Generator | Class | Parameters | Use Case |
|---|---|---|---|---|
| Flat | `FlatSurface` | shape, material | Ideal reference surface |
| Rough (isotropic) | `RoughSurface` | shape, sigma, amplitude, material | Random correlated roughness |
| Rough (anisotropic) | `AnisotropicRoughSurface` | shape, sigma_x, sigma_y, amplitude, material | Directional roughness (machined metal, brushed surfaces) |
| Sinusoidal | `SinusoidalSurface` | shape, period, amplitude, phase, material | Diffraction gratings, periodic textures, wavy substrates |
| Scratched | `ScratchedSurface` | shape, scratch_depth, scratch_width, material | Defect modelling, groove artefacts |
| Particle | `ParticleSurface` | shape, particle_count, amplitude, sigma, material | Contamination, dust, localized bumps |
| Imported | `ImportedSurface` | source, spacing, material | Loading external height maps (AFM, profilometry, CSV) |
| Dent | `DentSurface` | shape, radius, depth, material | Spherical/elliptical dents (UC1) |
| Pit | `PitSurface` | shape, radius, depth, material | Sharp conic/cylindrical pits (UC1) |
| Crack | `CrackSurface` | shape, length, width, depth, material | Branched crack geometry (UC1) |
| Stain | `StainSurface` | shape, radius, intensity, material | Local absorptive/reflective stain (UC1) |
| Wafer | `WaferSurface` | shape, die_size, fiducial_type, material | Die grid + fiducial crosses (UC7) |
| Misaligned | `MisalignedSurface` | shape, dx, dy, rotation, scale, material | Affine-warped wafer (UC7) |

### FlatSurface
- Zero height everywhere.
- Zero roughness, zero slopes, normals all pointing exactly +z.
- Ideal reference / baseline surface.

### RoughSurface
- Starts as white Gaussian noise, blurred with a Gaussian kernel.
- Configurable correlation length (σ in pixels) and RMS amplitude.
- Produces spatially correlated random topography.

### ScratchedSurface
- A diagonal groove with programmable depth and width.
- All heights are zero except for the groove pixels, which are lowered
  by `scratch_depth`.

### SinusoidalSurface
- A sinusoidal wave along the x-axis: h(x) = amplitude × sin(2πx / period + phase).
- Zero-mean height, useful for diffraction-grating simulations.
- Normals capture the periodic slope variation.

```python
from optical_metrology.surface import SinusoidalSurface
surf = SinusoidalSurface((64, 64), period=16.0, amplitude=0.5)
```

### AnisotropicRoughSurface
- Starts as white noise, blurred with different sigma in x and y.
- Produces directionally correlated roughness (e.g. ground glass,
  machined metal, brushed plastic).

```python
from optical_metrology.surface import AnisotropicRoughSurface
surf = AnisotropicRoughSurface((64, 64), sigma_x=8.0, sigma_y=2.0, amplitude=0.5)
```

### ImportedSurface

Loads an external height map from a `.npy`, `.csv`, or `.txt` file, or directly from a NumPy array. Geometry (normals, slopes, curvature, roughness) is derived automatically via `GeometryAnalyzer`. Useful for bringing in real AFM or profilometry data.

```python
from optical_metrology.surface import ImportedSurface
surf = ImportedSurface("measurement.npy", material=Material("silicon"))
```

### ParticleSurface
- Localised Gaussian bumps at random (seeded) locations.
- Deterministic by default (`numpy.random.default_rng(0)`).
- Configurable particle count, amplitude, and width.

### Thin-Film Stack (`ThinFilmStack`)
- Multi-layer interference coating using the transfer-matrix method.
- Supports arbitrary number of layers, each with material, thickness,
  and refractive index.
- Computes reflectance and transmittance for TE, TM, or unpolarised
  light at configurable incidence angles.

```python
from optical_metrology.surface import ThinFilmStack, Material

stack = ThinFilmStack([
    (Material("sio2"), 100e-9),   # 100 nm SiO₂
    (Material("si"), 500e-9),     # 500 nm Si
], substrate=Material("silicon"))
R, T = stack.reflectance(wavelength=532e-9, angle=0.0)
```

### DentSurface (`DentSurface`)
- Spherical or elliptical dent defect (UC1).
- Configurable radius and depth; smooth Gaussian-profile depression.
- Useful for simulating mechanical impact damage.

```python
from optical_metrology.surface import DentSurface
dent = DentSurface((64, 64), radius=8.0, depth=0.5)
```

### PitSurface (`PitSurface`)
- Sharp conical or cylindrical pit defect (UC1).
- Smaller, deeper than dents — simulates corrosion or pitting.
- Configurable radius, depth, and wall steepness.

### CrackSurface (`CrackSurface`)
- Branched crack geometry with configurable length, width, and depth (UC1).
- Main crack with optional side branches for realistic fracture patterns.
- Depth follows a Gaussian profile along the crack centreline.

```python
from optical_metrology.surface import CrackSurface
crack = CrackSurface((64, 64), length=30.0, width=2.0, depth=0.4)
```

### StainSurface (`StainSurface`)
- Local absorptive or reflective stain region (UC1).
- Modifies the effective albedo/reflectance of a circular area.
- Configurable radius and intensity (0 = fully absorbing, 1 = fully reflective).

```python
from optical_metrology.surface import StainSurface
stain = StainSurface((64, 64), radius=10.0, intensity=0.2)
```

### WaferSurface (`WaferSurface`)
- Semiconductor wafer with die grid and fiducial marks (UC7).
- Configurable `die_size`, `fiducial_type` (cross, circle, square).
- Regular grid of die with alignment targets at specified positions.

### MisalignedSurface (`MisalignedSurface`)
- Applies an affine warp to a nominal wafer pattern (UC7).
- Parameters: `dx`, `dy` (translation in pixels), `rotation` (degrees),
  `scale` (multiplicative).
- Internally uses `scipy.ndimage.affine_transform` for the warp.

```python
from optical_metrology.surface import WaferSurface, MisalignedSurface

nominal = WaferSurface((256, 256), die_size=32, fiducial_type="cross")
misaligned = MisalignedSurface.from_nominal(
    nominal, dx=3.0, dy=-1.5, rotation=0.5, scale=1.02
)
```

## Geometry Analysis

`GeometryAnalyzer.analyze()` takes a raw 2D height array and computes:

| Quantity | Method | Formula |
|---|---|---|
| Slope x | `numpy.gradient` along axis 1 | ∂h/∂x |
| Slope y | `numpy.gradient` along axis 0 | ∂h/∂y |
| Normals | Cross-product of gradient | n = (-∂h/∂x, -∂h/∂y, 1) / norm |
| Curvature | Laplacian of height | ∇²h = ∂²h/∂x² + ∂²h/∂y² |
| Roughness | RMS deviation | R_q = √(mean((h - h̄)²)) |

The normal convention: n points upward (+z). For a flat surface at
z = 0, n = (0, 0, 1).

## Key API

### Surface

```python
surface = Surface(
    height=height_array,       # (H, W) ndarray
    normals=normals_array,     # (H, W, 3) ndarray
    curvature=curvature_array, # (H, W) ndarray
    slope_x=dx_array,          # (H, W) ndarray
    slope_y=dy_array,          # (H, W) ndarray
    roughness=0.0,             # float
    material=Material("silicon"),
)

# Terminal visualisation (height, slope, curvature panels):
print(surface.visualize(max_width=72, color=True))

# Phase delay map for coherent illumination:
phi = surface.phase_screen(wavelength=532e-9)  # radians
```

### Surface Generators

```python
# The constructor IS the factory — it generates + analyses in one step:
flat = FlatSurface((64, 64), material=Material("glass"))
rough = RoughSurface((64, 64), sigma=6.0, amplitude=0.5, material=Material("silicon"))
scratch = ScratchedSurface((64, 64), scratch_depth=0.3, scratch_width=3)
particles = ParticleSurface((64, 64), particle_count=6, amplitude=0.8, sigma=2.0)

# Each exposes Surface attributes directly:
print(rough.height.shape)    # (64, 64)
print(rough.roughness)       # 0.049 (example)
print(rough.normals[0, 0])   # [x, y, z] unit vector
```

### GeometryAnalyzer

```python
from optical_metrology.surface import GeometryAnalyzer, Material
height = np.random.randn(32, 32) * 0.2
surface = GeometryAnalyzer.analyze(height, material=Material("custom"))
```

### Material

```python
Material(name="silicon")           # just a label
Material(name="gold", refractive_index=0.47)  # with approximate n
```

## Implementation Notes

### Single Inheritance Pattern

Surface generators inherit from `Surface` (data container). The
`SurfaceGenerator` base class is available for pipeline callable
detection but concrete generators do not subclass it — they implement
the factory behaviour directly in `__init__`:

```python
class RoughSurface(Surface):
    def __init__(self, shape, sigma, amplitude, material):
        height = RoughSurface._generate(shape, sigma, amplitude)
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.height = surface.height
        self.normals = surface.normals
        # ... etc.
```

This means the object **is** the surface, not just a builder for one.

### Pure-NumPy Gaussian Blur

The `_gaussian_filter()` helper implements a separable convolution to
avoid a SciPy dependency:

1. Convolve each row with a 1D Gaussian kernel.
2. Convolve each column with the same kernel.
3. Kernel radius = ceil(3σ), clipped by array edges via `mode="edge"`.

### Fixed RNG Seed

`ParticleSurface` uses `numpy.random.default_rng(0)` for deterministic,
reproducible output. `RoughSurface` uses the global `numpy.random`
seed for variety.

## Complete Example

```python
from optical_metrology.surface import RoughSurface, Material

surface = RoughSurface(
    shape=(64, 64),
    sigma=8.0,        # correlation length in pixels
    amplitude=0.5,    # RMS scaling
    material=Material("silicon"),
)

print(f"Height range:  {surface.height.min():.3f} to {surface.height.max():.3f}")
print(f"RMS roughness: {surface.roughness:.4f}")
print(f"Normal at origin: {surface.normals[32, 32]}")
```

## Creating a Custom Surface Generator

```python
from optical_metrology.surface import SurfaceGenerator, GeometryAnalyzer, Material, Surface
import numpy as np

class CheckerboardSurface(SurfaceGenerator):
    def __init__(self, shape, square_size=8, material=None):
        height = self.generate(shape)
        surface = GeometryAnalyzer.analyze(height, material=material or Material())
        self.__dict__.update(surface.__dict__)
        self.shape = shape

    def generate(self, shape):
        h, w = shape
        pattern = np.indices((h, w)).sum(axis=0) // self.square_size % 2
        return pattern.astype(float)
```

Alternatively, implement just `generate()` and use the base class
`create_surface()` method.
