"""GGX (Trowbridge-Reitz) microfacet specular scattering model.

Implements a physically based specular BRDF built from the GGX normal
distribution function, the Schlick Fresnel approximation, and a Smith
geometry attenuation factor.  It is a specular-only model — there is
no diffuse term, unlike :class:`~scattering.cooktorrance.CookTorranceScattering`.

GGX is the modern PBR microfacet standard.  Its NDF has a longer tail
than Beckmann, producing softer, more realistic highlights for rough
surfaces and metals.

References
----------
- Trowbridge, T. S. & Reitz, K. P. "Average irregularity representation
  of a rough surface for ray reflection." J. Opt. Soc. Am. 65(5), 1975.
- Walter, B. et al. "Microfacet models for refraction through rough
  surfaces." EGSR, 2007.
- Schlick, C. "An inexpensive BRDF model for physically-based
  rendering." Computer Graphics Forum 13(3), 1994.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from .base import ScatteredField, ScatteringModel
from .cooktorrance import distribution_ggx, fresnel_schlick, geometry_smith


class GGXScattering(ScatteringModel):
    """GGX microfacet specular scattering model.

    The specular BRDF is the Cook-Torrance product :math:`F \\cdot G
    \\cdot D / (4 \\cos\\theta_i \\cos\\theta_o)`, using the GGX
    (Trowbridge-Reitz) normal distribution function:

        D(h) = α² / (π cos⁴(α) (α² + tan²(α))²)

    where α is the angle between the half-vector h and the surface
    normal, and α = *roughness*².  The model is specular-only; use
    :class:`~scattering.cooktorrance.CookTorranceScattering` for a
    combined diffuse + specular BRDF.

    Parameters
    ----------
    roughness : float
        Roughness parameter α (not α²).  Typical values: 0.01 (nearly
        mirror) to 0.5 (very rough).  Default 0.1.
    fresnel_reflectance : float or None
        Reflectance at normal incidence F₀.  If ``None``, the model
        derives F₀ from ``surface.material.F0(lightfield.wavelength)``
        at evaluation time.  Common explicit values: 0.04 (glass),
        0.5 (silicon), 0.9+ (aluminium, gold).  Default 0.04.
    """

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
        """Evaluate GGX scattering over the grid.

        Parameters
        ----------
        lightfield : LightField
            Incident illumination.  ``lightfield.direction`` is the
            propagation direction (source → surface); it is negated
            internally to obtain the incident direction ω_i.
        surface : Surface
            Surface geometry providing per-pixel normals.
        view_direction : ndarray, shape ``(3,)``
            Unit vector from the surface toward the observer
            (normalised internally).

        Returns
        -------
        ScatteredField
            Specular radiance at each grid point and a constant outgoing
            direction equal to *view_direction*.
        """
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
            D = distribution_ggx(n_dot_h[valid], self.roughness)
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
