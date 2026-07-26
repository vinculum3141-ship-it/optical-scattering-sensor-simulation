# Scattering Layer

> **Target audience:** Both — BRDF physics for scientists, model interface
> and extension patterns for engineers.

## Overview

The scattering layer connects illumination with surface geometry: given
an incident light field, a surface, and an observation direction, it
computes the radiance scattered toward the observer. It produces a
`ScatteredField` containing per-pixel radiance and outgoing direction.

**File location:** `scattering/`

## Available Scattering Models

The framework currently provides eight scattering models:

| Model | Type | Parameters | Use Case |
|---|---|---|---|
| `LambertianScattering` | Diffuse | albedo | Matte surfaces, baseline reference |
| `PhongScattering` | Diffuse + specular | diffuse_albedo, specular_albedo, shininess | Glossy surfaces, plastics, painted finishes |
| `OrenNayarScattering` | Rough diffuse | albedo, roughness | Clay, paper, rough plastics, non-Lambertian matte |
| `CookTorranceScattering` | Specular microfacet | roughness, fresnel_reflectance, albedo | Physically based specular (metals, plastics, glass) |
| `BeckmannScattering` | Specular microfacet (skeleton) | roughness, albedo | UC4 — angle-resolved BRDF fitting candidate |
| `GGXScattering` | Specular microfacet (skeleton) | roughness, fresnel_reflectance, albedo | UC4 — modern PBR reference model |
| `RayleighScattering` | Particle volume (skeleton) | particle_density, depolarisation | UC6 — molecular / contaminant scattering |
| `MieScattering` | Particle volume (skeleton) | particle_radius, refractive_index | UC1/UC6 — aerosol / droplet scattering |

## Lambertian Scattering Model

The current implementation is the Lambertian (perfectly diffuse) model:

    L_r(x) = albedo × max( n(x) · ω_i , 0 )

where:

- `L_r` is the reflected radiance at grid point x.
- `albedo` is the fraction of incident power reflected diffusely (0-1).
- `n(x)` is the unit surface normal at x.
- `ω_i` is the direction from the surface toward the light source
  (the negative of `lightfield.direction`).

### Physical Assumptions

- Perfectly diffuse — radiance is the same in all viewing directions.
- No specular component.
- No wavelength dependence (albedo is a scalar, not a spectrum).
- No polarisation change on reflection.
- No subsurface scattering.
- No inter-reflection (single scattering only).

### Sign Convention

```
lightfield.direction       =  source → surface  (e.g. [0, 0, -1])
to_light = -lightfield.direction  =  surface → source  (e.g. [0, 0, +1])
Lambert's law:  L_r = albedo × max(dot(to_light, normal), 0)
```

## Scattering Model Interface

All scattering models implement the `ScatteringModel` base class with a
single method:

```python
class MyModel(ScatteringModel):
    def evaluate(self, lightfield, surface, view_direction):
        # Returns ScatteredField
        pass
```

### Inputs

| Parameter | Type | Shape | Description |
|---|---|---|---|
| `lightfield` | `LightField` | — | Incident irradiance + direction |
| `surface` | `Surface` | — | Height map + normals |
| `view_direction` | ndarray | (3,) | Unit vector from surface → observer |

### Output

`ScatteredField` with:

| Field | Shape | Description |
|---|---|---|
| `radiance` | (H, W) | Radiance scattered toward observer (W/(m² sr)) |
| `outgoing_direction` | (H, W, 3) | Direction from each point toward observer |
| `polarization` | — | Carried through from incident field |

## Key API

```python
from optical_metrology.scattering import LambertianScattering

model = LambertianScattering(albedo=0.7)
result = model.evaluate(
    lightfield=my_lightfield,
    surface=my_surface,
    view_direction=np.array([0.0, 0.0, 1.0]),
)

print(result.radiance.shape)      # (H, W)
print(result.radiance.min())      # ≥ 0
print(result.outgoing_direction.shape)  # (H, W, 3)
```

## Phong Scattering Model

The Phong model adds a view-dependent specular highlight to the
Lambertian diffuse component:

    L = diffuse_albedo × max(N·L, 0) + specular_albedo × (R·V)^shininess

where R = 2(N·L)N - L is the reflected light direction, V is the
view direction, and `shininess` controls the width of the highlight
(higher = sharper).

### Physical Assumptions

- Diffuse component follows Lambert's law (view-independent).
- Specular component reflects the light source colour (no wavelength
  shift).
- No Fresnel term (reflectivity is angle-independent).
- No physical energy conservation (diffuse + specular albedos can sum
  to more than 1).

```python
from optical_metrology.scattering import PhongScattering

model = PhongScattering(diffuse_albedo=0.6, specular_albedo=0.4, shininess=32.0)
result = model.evaluate(lf, surface, view_direction=np.array([0.0, 0.0, 1.0]))
```

## Oren-Nayar Scattering Model

The Oren-Nayar model extends Lambert's law for rough surfaces by
modelling the surface as a collection of V-shaped microfacets with
a Gaussian slope distribution. Rough surfaces appear brighter at
grazing angles than a Lambertian model predicts.

    L = albedo × cos(θ_i) × (A + B × cos(φ_diff) × sin(α) × tan(β))

where:

- A = 1 - 0.5σ²/(σ² + 0.33), B = 0.45σ²/(σ² + 0.09)
- σ = roughness (standard deviation of microfacet slopes in radians)
- α = max(θ_i, θ_r), β = min(θ_i, θ_r)
- θ_i = incident angle, θ_r = reflection angle
- φ_diff = azimuth difference between incident and view directions

### Physical behaviour

- **σ → 0**: model reduces to Lambertian (radiance = albedo × cos(θ_i)).
- **σ > 0**: surface appears brighter at grazing angles (non-Lambertian
  retro-reflection).
- The model conserves energy (albedo ≤ 1 ensures total reflectance ≤ 1).

```python
from optical_metrology.scattering import OrenNayarScattering

model = OrenNayarScattering(albedo=0.8, roughness=0.5)
result = model.evaluate(lf, surface, view_direction=np.array([0.0, 0.0, 1.0]))
```

## Cook-Torrance Scattering Model

The Cook-Torrance model is a physically based microfacet BRDF combining a Beckmann normal distribution, Schlick Fresnel approximation, and Smith geometry attenuation. A Lambertian diffuse term provides energy conservation. The specular/diffuse ratio is governed by the Fresnel term.

```python
from optical_metrology.scattering import CookTorranceScattering

model = CookTorranceScattering(roughness=0.1, fresnel_reflectance=0.04, albedo=0.5)
result = model.evaluate(lf, surface, view_direction=np.array([0.0, 0.0, 1.0]))
```

## Beckmann Scattering Model

**Skeleton** — Beckmann is a microfacet BRDF using the Beckmann normal distribution function. Required before UC4 (Angle-Resolved Scattering) as one of the candidate models for BRDF fitting. See `scattering/beckmann.py` for implementation guidance.

## GGX Scattering Model

**Skeleton** — GGX (Trowbridge–Reitz) is the modern PBR microfacet standard with a longer tail than Beckmann, producing more realistic highlights for rough surfaces and metals. See `scattering/ggx.py` for implementation guidance.

## Rayleigh Scattering Model

**Skeleton** — Rayleigh scattering operates on particles much smaller than the wavelength (d ≪ λ). It is strongly wavelength-dependent (∝ 1/λ⁴). Used for molecular scattering in the atmosphere and small contaminants. See `scattering/particle.py` for implementation guidance.

## Mie Scattering Model

**Skeleton** — Mie scattering operates on particles comparable to the wavelength (d ≈ λ). It is weakly wavelength-dependent. Used for aerosol scattering, droplets, and engineered particles. See `scattering/particle.py` for implementation guidance.

## Implementation Notes

### Vectorisation

The evaluation uses `numpy.einsum` for efficient per-pixel dot products:

```python
cosine = np.einsum("...i,...i->...", to_light, normals)
```

This is equivalent to element-wise dot products across the (H, W) grid
but avoids explicit Python loops.

### Outgoing Direction

The outgoing direction is currently constant across the grid (far-field
/ telecentric approximation), replicated to match the grid shape:

```python
outgoing = np.repeat(view_direction[None, None, :], H, axis=0)
outgoing = np.repeat(outgoing, W, axis=1)
```

### Edge Cases

- **Back-surface illumination** — when the light comes from behind
  (dot product negative), radiance is clipped to zero.
- **Grazing incidence** — when the light direction is perpendicular to
  the normal, radiance is zero.
- **Zero-intensity** — if the light field has zero irradiance, radiance
  is zero regardless of geometry.

## Complete Example

```python
import numpy as np
from optical_metrology.illumination import Laser, GaussianBeamProfile
from optical_metrology.surface import RoughSurface, Material
from optical_metrology.scattering import LambertianScattering

laser = Laser(532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0))
laser.propagation_direction = [0, 0, -1]
lf = laser.generate_light_field(shape=(32, 32), spacing=0.5)

surface = RoughSurface((32, 32), sigma=4.0, amplitude=0.5, material=Material("silicon"))

model = LambertianScattering(albedo=0.7)
result = model.evaluate(lf, surface, view_direction=np.array([0.0, 0.0, 1.0]))

print(f"Radiance: {result.radiance.min():.4g} — {result.radiance.max():.4g}")
```

## Creating a Custom Scattering Model

Implement the `ScatteringModel` interface:

```python
from optical_metrology.scattering import ScatteringModel, ScatteredField

class OrenNayarScattering(ScatteringModel):
    def __init__(self, albedo=0.8, roughness=0.5):
        self.albedo = albedo
        self.roughness = roughness

    def evaluate(self, lightfield, surface, view_direction):
        # Standard Oren-Nayar BRDF implementation
        # ...
        return ScatteredField(
            radiance=radiance,
            outgoing_direction=outgoing,
            polarization=lightfield.polarization,
        )
```

The only requirement is returning a `ScatteredField` with the correct
shape — the internals can use any physics model.
