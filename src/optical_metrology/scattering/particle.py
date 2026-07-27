"""Particle-based volume scattering models (Rayleigh and Mie).

Rayleigh scattering — particles much smaller than wavelength (d << λ).
Mie scattering — particles comparable to wavelength (d ≈ λ) using
Henyey-Greenstein phase function approximation.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from .base import ScatteredField, ScatteringModel


class RayleighScattering(ScatteringModel):
    """Rayleigh scattering from particles much smaller than λ.

    Parameters
    ----------
    particle_density : float
        Number density of scattering particles (m⁻³).
    depolarisation : float
        Depolarisation ratio (0 = fully polarised, 1 = unpolarised).
    reference_wavelength : float
        Wavelength at which *particle_density* * cross-section was
        calibrated (metres).
    """

    def __init__(self, particle_density: float = 1e6, depolarisation: float = 0.0, reference_wavelength: float = 532e-9):
        self.particle_density = float(particle_density)
        self.depolarisation = float(depolarisation)
        self.reference_wavelength = float(reference_wavelength)

    def evaluate(self, lightfield, surface, view_direction) -> ScatteredField:
        incoming = np.asarray(lightfield.direction, dtype=float)
        intensity = np.asarray(lightfield.intensity, dtype=float)
        wl = getattr(lightfield, "wavelength", 532e-9)

        lambda_ratio = self.reference_wavelength / wl
        beta = self.particle_density * lambda_ratio ** 4

        view_direction = np.asarray(view_direction, dtype=float)
        view_direction = view_direction / np.linalg.norm(view_direction)

        cos_theta = np.clip(
            np.einsum("hwi,i->hw", incoming, view_direction), -1.0, 1.0
        )
        phase = 0.75 * (1.0 + cos_theta ** 2) * (1.0 - self.depolarisation) + 0.5 * self.depolarisation

        radiance = intensity * beta * phase

        return ScatteredField(
            radiance=radiance,
            outgoing_direction=np.broadcast_to(view_direction.reshape(1, 1, 3), (*incoming.shape[:2], 3)).copy(),
            polarization=lightfield.polarization,
        )


class MieScattering(ScatteringModel):
    """Mie scattering from particles comparable to λ.

    Uses the Henyey-Greenstein phase function as an angular approximation.

    Parameters
    ----------
    particle_density : float
        Number density of scattering particles (m⁻³).
    particle_radius : float
        Mean particle radius in metres.
    refractive_index : complex
        Complex refractive index of the particle material.
    asymmetry : float
        Henyey-Greenstein asymmetry parameter g in [-1, 1].
        g > 0 → forward scattering, g < 0 → backward scattering.
    """

    def __init__(self, particle_density: float = 1e5, particle_radius: float = 1e-6, refractive_index: complex = 1.5 + 0j, asymmetry: float = 0.7):
        self.particle_density = float(particle_density)
        self.particle_radius = float(particle_radius)
        self.refractive_index = refractive_index
        self.asymmetry = float(asymmetry)

    def evaluate(self, lightfield, surface, view_direction) -> ScatteredField:
        incoming = np.asarray(lightfield.direction, dtype=float)
        intensity = np.asarray(lightfield.intensity, dtype=float)

        size_param = 2.0 * np.pi * self.particle_radius / getattr(lightfield, "wavelength", 532e-9)
        q_ext = 2.0
        cross_section = q_ext * np.pi * self.particle_radius ** 2
        beta = self.particle_density * cross_section

        view_direction = np.asarray(view_direction, dtype=float)
        view_direction = view_direction / np.linalg.norm(view_direction)

        cos_theta = np.clip(
            np.einsum("hwi,i->hw", incoming, view_direction), -1.0, 1.0
        )
        g = self.asymmetry
        phase = (1.0 - g ** 2) / (4.0 * np.pi * (1.0 + g ** 2 - 2.0 * g * cos_theta) ** 1.5)

        radiance = intensity * beta * phase

        return ScatteredField(
            radiance=radiance,
            outgoing_direction=np.broadcast_to(view_direction.reshape(1, 1, 3), (*incoming.shape[:2], 3)).copy(),
            polarization=lightfield.polarization,
        )
