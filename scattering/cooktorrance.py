"""Cook-Torrance microfacet BRDF model.

Implements the Cook-Torrance specular BRDF with Beckmann distribution,
Schlick Fresnel approximation, and Smith geometry attenuation.  A
Lambertian diffuse term is included for energy conservation.

References
----------
- Cook, R. L. & Torrance, K. E. "A reflectance model for computer
  graphics." ACM Trans. Graph. 1(1), 1982.
- Schlick, C. "An inexpensive BRDF model for physically-based
  rendering." Computer Graphics Forum 13(3), 1994.
"""

from __future__ import annotations

import numpy as np

from .base import ScatteredField, ScatteringModel


def fresnel_schlick(cos_theta: np.ndarray, F0: float) -> np.ndarray:
    return F0 + (1.0 - F0) * (1.0 - cos_theta) ** 5


def distribution_beckmann(n_dot_h: np.ndarray, roughness: float) -> np.ndarray:
    cos2 = n_dot_h ** 2
    tan2 = (1.0 - cos2) / cos2
    return np.exp(-tan2 / roughness ** 2) / (np.pi * roughness ** 2 * cos2 ** 2)


def geometry_smith(n_dot_l: np.ndarray, n_dot_v: np.ndarray, roughness: float) -> np.ndarray:
    a_l = n_dot_l / np.sqrt(roughness ** 2 + (1.0 - roughness ** 2) * n_dot_l ** 2)
    a_v = n_dot_v / np.sqrt(roughness ** 2 + (1.0 - roughness ** 2) * n_dot_v ** 2)
    return 1.0 / (a_l + a_v + 1e-10)


class CookTorranceScattering(ScatteringModel):
    """Cook-Torrance microfacet scattering model.

    Combines a specular microfacet BRDF with a Lambertian diffuse term.
    The specular component uses a Beckmann distribution, Schlick Fresnel,
    and Smith geometry.  The diffuse / specular ratio is governed by the
    Fresnel term (energy conservation).

    Parameters
    ----------
    roughness : float
        RMS slope of the microfacet distribution α.  Typical values:
        0.01 (nearly mirror) to 0.5 (very rough).  Default 0.1.
    fresnel_reflectance : float
        Reflectance at normal incidence F₀.  Common values: 0.04 (glass),
        0.5 (silicon), 0.9+ (aluminium, gold).  Default 0.04.
    albedo : float
        Diffuse albedo — fraction of non-specular reflected power.
        Default 0.5.
    """

    def __init__(self, roughness: float = 0.1, fresnel_reflectance: float = 0.04, albedo: float = 0.5):
        self.roughness = max(roughness, 1e-6)
        self.fresnel_reflectance = float(fresnel_reflectance)
        self.albedo = float(albedo)

    def evaluate(self, lightfield, surface, view_direction):
        incoming = np.asarray(lightfield.direction, dtype=float)
        normals = np.asarray(surface.normals, dtype=float)
        if incoming.ndim != 3 or normals.ndim != 3:
            raise ValueError("lightfield.direction and surface.normals must have shape (H, W, 3)")

        view_direction = np.asarray(view_direction, dtype=float)
        view_direction = view_direction / np.linalg.norm(view_direction)

        H, W = incoming.shape[0], incoming.shape[1]
        wi = -incoming  # direction from surface toward light
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
            F = fresnel_schlick(l_dot_h[valid], self.fresnel_reflectance)
            G = geometry_smith(n_dot_l[valid], n_dot_v[valid], self.roughness)

            brdf = F * G * D / (4.0 * n_dot_l[valid] * n_dot_v[valid] + 1e-10)

            diffuse = self.albedo / np.pi * n_dot_l[valid]

            radiance[valid] = (1.0 - F) * diffuse + brdf * n_dot_l[valid]

        outgoing = np.broadcast_to(wo, (H, W, 3)).copy()
        return ScatteredField(
            radiance=radiance,
            outgoing_direction=outgoing,
            polarization=lightfield.polarization,
        )
