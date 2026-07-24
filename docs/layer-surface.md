# Surface Geometry Layer

> **Target audience:** Both — geometry and roughness physics for scientists,
> generator patterns and API for engineers.

## Overview

The surface layer models object geometry via 2D height maps and derives
geometric quantities — normals, slopes, curvature, and roughness — using
finite-difference methods. It does **not** know about light or scattering.

**File location:** `surface/`

## Surface Types

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

### ParticleSurface
- Localised Gaussian bumps at random (seeded) locations.
- Deterministic by default (`numpy.random.default_rng(0)`).
- Configurable particle count, amplitude, and width.

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
from surface import GeometryAnalyzer, Material
height = np.random.randn(32, 32) * 0.2
surface = GeometryAnalyzer.analyze(height, material=Material("custom"))
```

### Material

```python
Material(name="silicon")           # just a label
Material(name="gold", refractive_index=0.47)  # with approximate n
```

## Implementation Notes

### Dual Inheritance Pattern

Surface generators inherit from **both** `Surface` (data container) and
`SurfaceGenerator` (factory). The constructor generates the height map
and immediately unpacks the analysed result into the dataclass fields:

```python
class RoughSurface(Surface, SurfaceGenerator):
    def __init__(self, shape, sigma, amplitude, material):
        height = self.generate(shape)
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
from surface import RoughSurface, Material

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
from surface import SurfaceGenerator, GeometryAnalyzer, Material, Surface
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
