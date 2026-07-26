"""GGX (Trowbridge–Reitz) microfacet scattering model (skeleton).

GGX is the standard microfacet distribution used in modern physically
based rendering and BRDF measurement.  Its key property is a longer
tail than Beckmann — it falls off as :math:`1/\\cos^4\\theta_m` rather
than Gaussian, producing more realistic highlights for rough surfaces
and metals.

Required before UC4 (Angle-Resolved Scattering) — the BRDF fitting
pipeline should include GGX as a candidate model.

Implementation notes
--------------------
To complete this model, follow the same structure as
:class:`~scattering.cooktorrance.CookTorranceScattering` but replace the
Beckmann distribution with the GGX distribution::

    D_GGX(α, n·h) = α² / (π * ((n·h)² * (α² - 1) + 1)²)

The Fresnel and geometry functions in ``cooktorrance.py`` can be reused
unchanged.  Parameters: ``roughness`` (α), ``fresnel_reflectance`` (F₀),
``albedo``.
"""

from __future__ import annotations

from .base import ScatteredField, ScatteringModel


class GGXScattering(ScatteringModel):
    """GGX microfacet scattering model (skeleton).

    .. note::

       This model is not yet implemented.  See module docstring for
       implementation guidance.  It is tracked in
       ``docs/roadmap-todo.md`` under the UC4 pre-deployment items.
    """

    def __init__(self, roughness: float = 0.1, fresnel_reflectance: float = 0.04, albedo: float = 0.5):
        self.roughness = roughness
        self.fresnel_reflectance = fresnel_reflectance
        self.albedo = albedo
        raise NotImplementedError(
            "GGXScattering is a skeleton.  Implement before UC4 "
            "(Angle-Resolved Scattering) is activated.  See "
            "scattering/ggx.py for guidance."
        )

    def evaluate(self, lightfield, surface, view_direction):
        raise NotImplementedError(
            "GGXScattering is a skeleton.  Implement before UC4."
        )
