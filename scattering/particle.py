"""Particle-based volume scattering models (skeletons).

Rayleigh scattering and Mie scattering describe how light interacts
with particles in suspension (aerosols, contaminants, atmospheric
particulates).  Unlike the surface-scattering models in this package
(Lambertian, Phong, Cook-Torrance, Beckmann, GGX), these operate on
a particle size distribution rather than a surface height map.

Rayleigh scattering
    Particles much smaller than the wavelength (d << λ).  Strongly
    wavelength-dependent (∝ 1/λ⁴).  Used for molecular scattering in
    the atmosphere and small contaminant particles.

Mie scattering
    Particles comparable to the wavelength (d ≈ λ).  Weakly
    wavelength-dependent.  Used for aerosol scattering, droplet
    scattering, and engineered particles.

Required before
----------------
- UC1 (Defect Inspection) — modelling light scattering from
  particle contaminants on surfaces.
- UC6 (LiDAR) — atmospheric backscatter from aerosols and molecules.
"""

from __future__ import annotations

from .base import ScatteredField, ScatteringModel


class RayleighScattering(ScatteringModel):
    """Rayleigh scattering model (skeleton).

    .. note::

       This model is not yet implemented.  It operates on particle
       size and concentration rather than surface height, so the
       ``evaluate()`` signature may differ from the surface-scattering
       models.  Tracked in ``docs/roadmap-todo.md`` under UC6.
    """

    def __init__(self, particle_density: float = 1.0, depolarisation: float = 0.0):
        self.particle_density = particle_density
        self.depolarisation = depolarisation
        raise NotImplementedError(
            "RayleighScattering is a skeleton.  Implement before UC6 "
            "(LiDAR) or UC1 (contamination scattering)."
        )

    def evaluate(self, lightfield, surface, view_direction):
        raise NotImplementedError(
            "RayleighScattering is a skeleton.  Implement before UC6."
        )


class MieScattering(ScatteringModel):
    """Mie scattering model (skeleton).

    .. note::

       This model is not yet implemented.  Requires a Mie-theory
       computation (size parameter x = 2πr/λ, complex refractive index,
       scattering phase function via Legendre series).  Tracked in
       ``docs/roadmap-todo.md`` under UC6 and UC1.
    """

    def __init__(self, particle_radius: float = 1e-6, refractive_index: complex = 1.5 + 0j):
        self.particle_radius = particle_radius
        self.refractive_index = refractive_index
        raise NotImplementedError(
            "MieScattering is a skeleton.  Implement before UC6 "
            "(LiDAR) or UC1 (contamination scattering)."
        )

    def evaluate(self, lightfield, surface, view_direction):
        raise NotImplementedError(
            "MieScattering is a skeleton.  Implement before UC6."
        )
