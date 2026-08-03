"""Thin-film interference model for multi-layer optical coatings.

Computes reflectance and transmittance of arbitrary multi-layer thin-film
stacks using the transfer-matrix (characteristic matrix) method.
Supports coherent interference, arbitrary incidence angle, and
TE/TM/unpolarized light.

Relevant for semiconductor coating inspection (UC1), anti-reflection
layer characterisation, and any use case involving dielectric or metal
films on a substrate.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


class ThinFilmStack:
    """Multi-layer thin-film stack with characteristic-matrix reflectance.

    Parameters
    ----------
    layers : list of (thickness, n, k)
        Each tuple is ``(thickness_m, refractive_index, extinction)``.
        Ordered from incident-medium side to substrate.
    substrate_n : float
        Refractive index of the substrate (semi-infinite).
    substrate_k : float
        Extinction coefficient of the substrate.
    incident_n : float
        Refractive index of the incident medium (default 1.0 for air).
    """

    def __init__(
        self,
        layers: List[Tuple[float, float, float]],
        substrate_n: float = 1.5,
        substrate_k: float = 0.0,
        incident_n: float = 1.0,
    ):
        self.layer_data = [(d, complex(n, k)) for d, n, k in layers]
        self.substrate_n = complex(substrate_n, substrate_k)
        self.incident_n = complex(incident_n, 0.0)

    def reflectance(
        self,
        wavelength: float,
        angle: float = 0.0,
        polarisation: str = "unpolarized",
    ) -> float:
        """Reflectance at *wavelength* (m) and incidence *angle* (rad).

        Parameters
        ----------
        wavelength : float
            Vacuum wavelength in metres.
        angle : float
            Incidence angle in radians (0 = normal incidence).
        polarisation : str
            ``"te"``, ``"tm"``, or ``"unpolarized"`` (average of TE+TM).

        Returns
        -------
        float
            Fraction of incident power reflected.
        """
        if polarisation == "unpolarized":
            R_te = self._calc(wavelength, angle, "te")
            R_tm = self._calc(wavelength, angle, "tm")
            return float(0.5 * (R_te + R_tm))
        return float(self._calc(wavelength, angle, polarisation))

    def transmittance(
        self,
        wavelength: float,
        angle: float = 0.0,
        polarisation: str = "unpolarized",
    ) -> float:
        R = self.reflectance(wavelength, angle, polarisation)
        return float(max(0.0, 1.0 - R))

    def _admittance(self, n: complex, theta: complex, pol: str) -> complex:
        cos_t = np.cos(theta)
        if pol == "te":
            return n * cos_t
        return n / cos_t

    def _calc(self, wavelength: float, angle: float, pol: str) -> float:
        k0 = 2.0 * np.pi / wavelength
        theta_inc = complex(angle)
        n_inc = self.incident_n
        n_sub = self.substrate_n

        sin_theta_inc = np.sin(theta_inc)

        M = np.eye(2, dtype=complex)
        n_prev = n_inc
        theta_prev = theta_inc

        for d_j, n_j in self.layer_data:
            sin_theta_j = n_prev * np.sin(theta_prev) / n_j
            if abs(sin_theta_j) > 1.0:
                theta_j = np.pi / 2.0 - 1j * np.arccosh(abs(sin_theta_j))
            else:
                theta_j = np.arcsin(sin_theta_j)

            delta = k0 * n_j * d_j * np.cos(theta_j)
            p_j = self._admittance(n_j, theta_j, pol)

            M_j = np.array([
                [np.cos(delta), 1j * np.sin(delta) / p_j],
                [1j * p_j * np.sin(delta), np.cos(delta)],
            ], dtype=complex)
            M = M @ M_j

            n_prev = n_j
            theta_prev = theta_j

        sin_theta_sub = n_prev * np.sin(theta_prev) / n_sub
        if abs(sin_theta_sub) > 1.0:
            theta_sub = np.pi / 2.0 - 1j * np.arccosh(abs(sin_theta_sub))
        else:
            theta_sub = np.arcsin(sin_theta_sub)

        p_inc = self._admittance(n_inc, theta_inc, pol)
        p_sub = self._admittance(n_sub, theta_sub, pol)

        m11, m12 = M[0, 0], M[0, 1]
        m21, m22 = M[1, 0], M[1, 1]

        num = p_inc * m11 + p_inc * p_sub * m12 - m21 - p_sub * m22
        den = p_inc * m11 + p_inc * p_sub * m12 + m21 + p_sub * m22
        r = num / den
        return float(abs(r) ** 2)
