from __future__ import annotations

import numpy as np

from .base import ScatteredField, ScatteringModel


class LambertianScattering(ScatteringModel):
    """Simple diffuse (Lambertian) scattering model.

    Evaluates Lambert's cosine law: the radiance scattered toward the
    viewer is proportional to the cosine of the angle between the
    surface normal and the direction from the surface toward the light
    source.  The result is independent of the view direction (perfectly
    diffuse).

    Parameters
    ----------
    albedo : float
        Fraction of incident power that is reflected diffusely.
        Ranges from 0 (fully absorbing) to 1 (fully reflecting).
    """

    def __init__(self, albedo: float = 0.8):
        self.albedo = albedo

    def evaluate(self, lightfield, surface, view_direction):
        """Evaluate Lambertian scattering over the grid.

        Parameters
        ----------
        lightfield : LightField
            Incident illumination.  ``lightfield.direction`` is the
            propagation direction of the light (from source toward
            surface).  It is negated internally to obtain the
            direction from the surface toward the light, as required
            by Lambert's law.
        surface : Surface
            Surface geometry providing per-pixel normals.
        view_direction : ndarray, shape ``(3,)``
            Unit vector from the surface toward the observer
            (normalised internally).

        Returns
        -------
        ScatteredField
            Radiance at each grid point and a constant outgoing
            direction equal to *view_direction*.
        """
        incoming = np.asarray(lightfield.direction, dtype=float)
        normals = np.asarray(surface.normals, dtype=float)
        if incoming.ndim != 3 or normals.ndim != 3:
            raise ValueError("lightfield.direction and surface.normals must have shape (H, W, 3)")

        view_direction = np.asarray(view_direction, dtype=float)
        view_direction = view_direction / np.linalg.norm(view_direction)

        # Lambert's law uses the direction from the surface toward the
        # light source.  Since lightfield.direction is the propagation
        # direction of the light (source → surface), we negate it.
        to_light = -incoming
        cosine = np.einsum("...i,...i->...", to_light, normals)
        cosine = np.clip(cosine, 0.0, None)
        radiance = self.albedo * cosine

        outgoing_direction = np.repeat(view_direction[None, None, :], incoming.shape[0], axis=0)
        outgoing_direction = np.repeat(outgoing_direction, incoming.shape[1], axis=1)
        return ScatteredField(
            radiance=radiance,
            outgoing_direction=outgoing_direction,
            polarization=lightfield.polarization,
        )