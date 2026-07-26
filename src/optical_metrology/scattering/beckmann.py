"""Beckmann microfacet scattering model (skeleton).

A physically based BRDF using the Beckmann normal distribution function.
The full model is identical in structure to Cook-Torrance but uses the
Beckmann distribution D(h) as its primary specular lobe without the
additional Fresnel and geometry terms (or with simplified versions).

Required before UC4 (Angle-Resolved Scattering) — the BRDF fitting
pipeline needs this as one of the candidate models to fit against
angle-resolved data.

Implementation notes
--------------------
The Beckmann distribution is already implemented in
:mod:`scattering.cooktorrance`.  To complete this model:

1. Import ``distribution_beckmann`` from ``cooktorrance.py``.
2. Implement :meth:`evaluate` following the same pattern as
   :class:`~scattering.cooktorrance.CookTorranceScattering`.
3. Parameters: ``roughness`` (α), optionally ``albedo``.
"""

from __future__ import annotations

from .base import ScatteredField, ScatteringModel


class BeckmannScattering(ScatteringModel):
    """Beckmann microfacet scattering model (skeleton).

    .. note::

       This model is not yet implemented.  See module docstring for
       implementation guidance.  It is tracked in
       ``docs/roadmap-todo.md`` under the UC4 pre-deployment items.
    """

    def __init__(self, roughness: float = 0.1, albedo: float = 0.8):
        self.roughness = roughness
        self.albedo = albedo
        raise NotImplementedError(
            "BeckmannScattering is a skeleton.  Implement before UC4 "
            "(Angle-Resolved Scattering) is activated.  See "
            "scattering/beckmann.py for guidance."
        )

    def evaluate(self, lightfield, surface, view_direction):
        raise NotImplementedError(
            "BeckmannScattering is a skeleton.  Implement before UC4."
        )
