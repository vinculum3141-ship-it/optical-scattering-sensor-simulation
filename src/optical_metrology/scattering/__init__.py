"""Scattering models for the optical simulation pipeline.

Provides physically based BRDF models.  The base class is
:class:`ScatteringModel`, which returns a :class:`ScatteredField`
containing direction, intensity, and polarisation.

Analytical BRDFs
    - :class:`LambertianScattering` — ideal diffuse
    - :class:`PhongScattering` — empirical specular lobe
    - :class:`OrenNayarScattering` — rough diffuse (microfacet)
    - :class:`CookTorranceScattering` — Torrance–Sparrow microfacet
    - :class:`BeckmannScattering` — Beckmann–Spizzichino microfacet (UC4)
    - :class:`GGXScattering` — GGX/TR microfacet (UC4)

Atmospheric / particle scattering (UC6)
    - :class:`RayleighScattering` — elastic dipole scattering ∝ 1/λ⁴
    - :class:`MieScattering` — Henyey–Greenstein phase function
"""

from .base import ScatteringModel, ScatteredField
from .lambertian import LambertianScattering
from .phong import PhongScattering
from .orennayar import OrenNayarScattering
from .cooktorrance import CookTorranceScattering
from .beckmann import BeckmannScattering
from .ggx import GGXScattering
from .particle import RayleighScattering, MieScattering

__all__ = [
    "BeckmannScattering",
    "CookTorranceScattering",
    "GGXScattering",
    "LambertianScattering",
    "MieScattering",
    "OrenNayarScattering",
    "PhongScattering",
    "RayleighScattering",
    "ScatteredField",
    "ScatteringModel",
]
