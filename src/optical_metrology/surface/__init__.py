"""Surface models for the optical simulation pipeline.

Provides height-field surface representations, thin-film interference,
and parameterised defect generators.

Base
    - :class:`Surface` — abstract height field
    - :class:`SurfaceGenerator` — factory that maps params → Surface
    - :class:`GeometryAnalyzer` — curvature, slope, aspect ratio
    - :class:`Material` — optical constants (n, k)
    - :class:`SellmeierCoefficients` — dispersion coefficients

Thin film
    - :class:`ThinFilmStack` — multi-layer interference coating

Generators
    - :class:`FlatSurface` — perfectly flat reference
    - :class:`RoughSurface` — Gaussian random roughness
    - :class:`AnisotropicRoughSurface` — directional roughness
    - :class:`SinusoidalSurface` — periodic grating
    - :class:`ScratchedSurface` — single/multiple scratches
    - :class:`DentSurface` — spherical/elliptical dent (UC1)
    - :class:`PitSurface` — sharp conic/cylindrical pit (UC1)
    - :class:`CrackSurface` — branched crack geometry (UC1)
    - :class:`StainSurface` — local absorptive/reflective stain (UC1)
    - :class:`ParticleSurface` — spherical particles on surface (UC6)
    - :class:`ImportedSurface` — load height map from file
    - :class:`WaferSurface` — die grid + fiducial crosses (UC7)
    - :class:`MisalignedSurface` — affine-warped wafer (UC7)
"""

from .base import Surface, SurfaceGenerator, GeometryAnalyzer, Material, SellmeierCoefficients
from .thinfilm import ThinFilmStack
from .generators import (
    AnisotropicRoughSurface,
    CrackSurface,
    DentSurface,
    FlatSurface,
    ImportedSurface,
    MisalignedSurface,
    ParticleSurface,
    PitSurface,
    RoughSurface,
    ScratchedSurface,
    SinusoidalSurface,
    StainSurface,
    WaferSurface,
)

__all__ = [
    "AnisotropicRoughSurface",
    "CrackSurface",
    "DentSurface",
    "FlatSurface",
    "GeometryAnalyzer",
    "ImportedSurface",
    "Material",
    "MisalignedSurface",
    "ParticleSurface",
    "PitSurface",
    "RoughSurface",
    "ScratchedSurface",
    "SinusoidalSurface",
    "StainSurface",
    "WaferSurface",
    "Surface",
    "SurfaceGenerator",
    "ThinFilmStack",
]
