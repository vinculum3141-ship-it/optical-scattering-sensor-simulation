from __future__ import annotations

from typing import Optional

import numpy as np

from .base import ScatteredField, ScatteringModel
from .cooktorrance import distribution_beckmann, fresnel_schlick, geometry_smith


class BeckmannScattering(ScatteringModel):
    def __init__(self, roughness: float = 0.1, fresnel_reflectance: Optional[float] = 0.04):
        self.roughness = max(roughness, 1e-6)
        self.fresnel_reflectance = fresnel_reflectance

    def _resolve_F0(self, lightfield, surface) -> float:
        if self.fresnel_reflectance is not None:
            return self.fresnel_reflectance
        if hasattr(surface, 'material') and surface.material is not None:
            wl = getattr(lightfield, 'wavelength', 550e-9)
            return surface.material.F0(wl)
        return 0.04

    def evaluate(self, lightfield, surface, view_direction):
        incoming = np.asarray(lightfield.direction, dtype=float)
        normals = np.asarray(surface.normals, dtype=float)
        if incoming.ndim != 3 or normals.ndim != 3:
            raise ValueError("lightfield.direction and surface.normals must have shape (H, W, 3)")

        view_direction = np.asarray(view_direction, dtype=float)
        view_direction = view_direction / np.linalg.norm(view_direction)

        F0 = self._resolve_F0(lightfield, surface)

        H, W = incoming.shape[0], incoming.shape[1]
        wi = -incoming
        wo = np.broadcast_to(view_direction.reshape(1, 1, 3), (H, W, 3))

        n_dot_l = np.clip(np.einsum("hwi,hwi->hw", normals, wi), 0.0, None)
        n_dot_v = np.clip(np.einsum("hwi,hwi->hw", normals, wo), 0.0, None)

        h = wi + wo
        h_norm = np.linalg.norm(h, axis=2, keepdims=True)
        h = h / np.where(h_norm == 0.0, 1.0, h_norm)

        n_dot_h = np.clip(np.einsum("hwi,hwi->hw", normals, h), 0.0, None)
        l_dot_h = np.clip(np.einsum("hwi,hwi->hw", wi, h), 0.0, None)

        valid = (n_dot_l > 1e-6) & (n_dot_v > 1e-6) & (n_dot_h > 1e-6)

        radiance = np.zeros((H, W), dtype=float)

        if np.any(valid):
            D = distribution_beckmann(n_dot_h[valid], self.roughness)
            F = fresnel_schlick(l_dot_h[valid], F0)
            G = geometry_smith(n_dot_l[valid], n_dot_v[valid], self.roughness)

            brdf = F * G * D / (4.0 * n_dot_l[valid] * n_dot_v[valid] + 1e-10)
            radiance[valid] = brdf * n_dot_l[valid]

        outgoing = np.broadcast_to(wo, (H, W, 3)).copy()
        return ScatteredField(
            radiance=radiance,
            outgoing_direction=outgoing,
            polarization=lightfield.polarization,
        )
