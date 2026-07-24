"""Phong reflection model: diffuse + specular scattering.

The Phong model combines a Lambertian diffuse component with a
specular highlight that depends on the view direction.  It is a
simple, fast approximation for glossy surfaces such as plastic,
painted surfaces, and dielectrics with a smooth finish.
"""

from __future__ import annotations

import numpy as np

from .base import ScatteredField, ScatteringModel


class PhongScattering(ScatteringModel):
    """Phong reflection model with diffuse and specular components.

    Diffuse term follows Lambert's cosine law.
    Specular term follows the Phong approximation: (R * V)^shininess,
    where R is the reflected light direction and V is the view direction.

    Parameters
    ----------
    diffuse_albedo : float
        Fraction of incident power reflected diffusely (0-1).
    specular_albedo : float
        Fraction of incident power reflected specularly (0-1).
    shininess : float
        Phong exponent controlling the width of the specular highlight.
        Higher values give sharper, more mirror-like highlights.
        Typical range: 1 (very dull) to 200 (nearly mirror).
    """

    def __init__(self, diffuse_albedo=0.6, specular_albedo=0.4, shininess=32.0):
        self.diffuse_albedo = diffuse_albedo
        self.specular_albedo = specular_albedo
        self.shininess = shininess

    def evaluate(self, lightfield, surface, view_direction):
        incoming = np.asarray(lightfield.direction, dtype=float)
        normals = np.asarray(surface.normals, dtype=float)
        if incoming.ndim != 3 or normals.ndim != 3:
            raise ValueError("lightfield.direction and surface.normals must have shape (H, W, 3)")

        view_direction = np.asarray(view_direction, dtype=float)
        view_direction = view_direction / np.linalg.norm(view_direction)

        to_light = -incoming

        # Diffuse term: max(N·L, 0)
        cos_i = np.einsum("...i,...i->...", to_light, normals)
        cos_i = np.clip(cos_i, 0.0, None)
        diffuse = self.diffuse_albedo * cos_i

        # Specular term: (R·V)^shininess, where R = 2(N·L)N - L
        R = 2.0 * cos_i[..., None] * normals - to_light
        cos_r = np.einsum("...i,...i->...", R, view_direction[None, None, :])
        cos_r = np.clip(cos_r, 0.0, None)
        specular = self.specular_albedo * (cos_r ** self.shininess)

        radiance = diffuse + specular
        H, W = radiance.shape
        outgoing = np.broadcast_to(view_direction, (H, W, 3)).copy()

        return ScatteredField(
            radiance=radiance,
            outgoing_direction=outgoing,
            polarization=lightfield.polarization,
        )
