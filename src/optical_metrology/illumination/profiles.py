"""Beam profile models for optical illumination sources.

Each profile describes how the intensity of a source is distributed
across a 2D spatial grid. Profiles are used by :class:`LightSource`
and its subclasses when generating a light field.
"""

import numpy as np


class BeamProfile:
    """Base class for describing the spatial intensity profile of a source.

    Subclasses must override :meth:`evaluate` to return a 2D array of
    relative intensity values on a grid of the given shape.
    """

    def evaluate(self, shape, spacing=1.0):
        """Evaluate the intensity profile on a 2D grid.

        Parameters
        ----------
        shape : tuple of int
            Grid dimensions ``(height, width)`` in pixels.
        spacing : float
            Physical spacing between grid points in arbitrary units.

        Returns
        -------
        np.ndarray
            2D array of relative intensity values (dimensionless).
        """
        raise NotImplementedError


class UniformBeamProfile(BeamProfile):
    """Profile with constant intensity across the entire grid.

    This models an idealised, perfectly uniform beam (e.g. a
    collimated top-hat after a beam expander with no roll-off).
    """

    def evaluate(self, shape, spacing=1.0):
        return np.ones(shape, dtype=float)


class TopHatBeamProfile(BeamProfile):
    """Profile with uniform intensity within a circular aperture, zero outside.

    .. note::
       The current implementation returns a uniform array over the
       whole grid.  A true circular-mask implementation is planned.
    """

    def evaluate(self, shape, spacing=1.0):
        return np.ones(shape, dtype=float)


class GaussianBeamProfile(BeamProfile):
    """Gaussian (TEM\\ :sub:`00`) transverse intensity profile.

    The intensity at radial distance ``r`` from the beam centre is

        I(r) = exp(-2 r² / w₀²)

    where ``w0`` is the beam waist radius (the 1/e² half-width).

    Parameters
    ----------
    w0 : float
        Beam waist radius in the same spatial units as ``spacing``.
    """

    def __init__(self, w0=1.0):
        self.w0 = w0

    def evaluate(self, shape, spacing=1.0):
        if isinstance(shape, int):
            shape = (shape, shape)
        height, width = shape
        y = np.arange(height, dtype=float) - (height - 1) / 2.0
        x = np.arange(width, dtype=float) - (width - 1) / 2.0
        yy, xx = np.meshgrid(y, x, indexing="ij")
        radius_sq = xx**2 + yy**2
        return np.exp(-2.0 * radius_sq / (self.w0**2))
