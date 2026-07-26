"""Oren-Nayar reflectance model: diffuse scattering from rough surfaces.

The Oren-Nayar model extends Lambert's law to account for surface
roughness.  It models the surface as a collection of V-shaped cavities
(microfacets) with a Gaussian distribution of slopes.  Rough surfaces
appear brighter at grazing angles than a Lambertian model predicts —
a phenomenon known as "retro-reflection" or "non-Lambertian" diffuse
behaviour.

Reference: M. Oren and S. K. Nayar, "Generalization of Lambert's
Reflectance Model", SIGGRAPH 1994.
"""

from __future__ import annotations

import numpy as np

from .base import ScatteredField, ScatteringModel


class OrenNayarScattering(ScatteringModel):
    """Oren-Nayar diffuse reflectance model for rough surfaces.

    This model is appropriate for matte surfaces where roughness
    causes non-Lambertian behaviour — clay, paper, plaster, rough
    plastics, etc.  Smoother surfaces approach Lambertian as the
    roughness parameter approaches zero.

    Parameters
    ----------
    albedo : float
        Surface albedo (fraction of incident power reflected).
        Ranges from 0 (fully absorbing) to 1 (fully reflecting).
    roughness : float
        Standard deviation of the microfacet slope distribution
        in radians.  Typical range: 0 (smooth → Lambertian) to
        about 1 (very rough).  Values above ~1.5 produce highly
        non-Lambertian behaviour.
    """

    def __init__(self, albedo=0.8, roughness=0.5):
        self.albedo = albedo
        self.roughness = roughness

    def evaluate(self, lightfield, surface, view_direction):
        incoming = np.asarray(lightfield.direction, dtype=float)
        normals = np.asarray(surface.normals, dtype=float)
        if incoming.ndim != 3 or normals.ndim != 3:
            raise ValueError("lightfield.direction and surface.normals must have shape (H, W, 3)")

        view_direction = np.asarray(view_direction, dtype=float)
        view_direction = view_direction / np.linalg.norm(view_direction)

        to_light = -incoming
        V = view_direction[None, None, :]
        L = to_light
        N = normals

        # Cosines of incident and viewing angles
        cos_theta_i = np.einsum("...i,...i->...", L, N)
        cos_theta_r = np.einsum("...i,...i->...", V, N)
        cos_theta_i = np.clip(cos_theta_i, 0.0, None)
        cos_theta_r = np.clip(cos_theta_r, 0.0, None)

        # Avoid division by zero at grazing angles
        theta_i = np.arccos(np.clip(cos_theta_i, 1e-10, 1.0))
        theta_r = np.arccos(np.clip(cos_theta_r, 1e-10, 1.0))

        # Azimuth difference between light and view projections
        # Project L and V onto the tangent plane, then compute angle between them
        L_proj = L - cos_theta_i[..., None] * N
        L_proj_norm = np.linalg.norm(L_proj, axis=-1, keepdims=True)
        L_proj = L_proj / np.where(L_proj_norm == 0, 1.0, L_proj_norm)

        V_proj = V - cos_theta_r[..., None] * N
        V_proj_norm = np.linalg.norm(V_proj, axis=-1, keepdims=True)
        V_proj = V_proj / np.where(V_proj_norm == 0, 1.0, V_proj_norm)

        cos_phi_diff = np.einsum("...i,...i->...", L_proj, V_proj)
        cos_phi_diff = np.clip(cos_phi_diff, 0.0, 1.0)

        # Oren-Nayar coefficients
        sigma2 = self.roughness * self.roughness
        A = 1.0 - 0.5 * sigma2 / (sigma2 + 0.33)
        B = 0.45 * sigma2 / (sigma2 + 0.09)

        # alpha = max(theta_i, theta_r), beta = min(theta_i, theta_r)
        alpha = np.maximum(theta_i, theta_r)
        beta = np.minimum(theta_i, theta_r)

        radiance = self.albedo * cos_theta_i * (
            A + B * cos_phi_diff * np.sin(alpha) * np.tan(beta)
        )
        radiance = np.clip(radiance, 0.0, None)

        H, W = radiance.shape
        outgoing = np.broadcast_to(view_direction, (H, W, 3)).copy()

        return ScatteredField(
            radiance=radiance,
            outgoing_direction=outgoing,
            polarization=lightfield.polarization,
        )
