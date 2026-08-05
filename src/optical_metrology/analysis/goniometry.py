"""Goniometric sweep workflow for angle-resolved scattering measurement (UC4).

Auto-varies incidence and/or reflection angles, evaluates a scattering
model at each configuration, and collects BRDF measurements into a
structured table.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import copy

import numpy as np

from .base import AnalysisModule, AnalysisReport


@dataclass
class GoniometricMeasurement:
    theta_i: float
    theta_r: float
    phi_i: float
    phi_r: float
    brdf: float


class GoniometricSweep(AnalysisModule):
    """Perform an angle-resolved BRDF measurement sweep.

    Parameters
    ----------
    theta_i_range : tuple of (float, float, int)
        ``(start, stop, num)`` for incidence angle in radians.
    theta_r_range : tuple of (float, float, int)
        ``(start, stop, num)`` for reflection angle in radians.
    phi_range : tuple of (float, float, int) or None
        ``(start, stop, num)`` for azimuth in radians.  If ``None``,
        only in-plane (φ = 0) measurements are taken.
    """

    def __init__(
        self,
        theta_i_range: Tuple[float, float, int] = (0.0, 0.785, 5),
        theta_r_range: Tuple[float, float, int] = (0.0, 0.785, 5),
        phi_range: Optional[Tuple[float, float, int]] = None,
    ):
        self.theta_i_vals = np.linspace(*theta_i_range)
        self.theta_r_vals = np.linspace(*theta_r_range)
        self.phi_vals = (
            np.linspace(*phi_range) if phi_range else np.array([0.0])
        )

    def analyze(self, configs: List[Tuple]) -> AnalysisReport:
        measurements = []
        for theta_i, theta_r, phi_i, phi_r, brdf in configs:
            measurements.append(
                GoniometricMeasurement(
                    theta_i=theta_i, theta_r=theta_r,
                    phi_i=phi_i, phi_r=phi_r,
                    brdf=float(brdf),
                )
            )
        brdf_vals = [m.brdf for m in measurements]
        return AnalysisReport(measurements={
            "n_measurements": len(measurements),
            "mean_brdf": float(np.mean(brdf_vals)) if brdf_vals else 0.0,
            "max_brdf": float(np.max(brdf_vals)) if brdf_vals else 0.0,
            "theta_i_vals": self.theta_i_vals.tolist(),
            "theta_r_vals": self.theta_r_vals.tolist(),
            "phi_vals": self.phi_vals.tolist(),
            "measurements": [
                {
                    "theta_i": m.theta_i,
                    "theta_r": m.theta_r,
                    "phi_i": m.phi_i,
                    "phi_r": m.phi_r,
                    "brdf": m.brdf,
                }
                for m in measurements
            ],
        })

    def sweep(self, model, lightfield, surface, view_direction_base) -> List[GoniometricMeasurement]:
        """Run the sweep and return raw measurements."""
        measurements = []
        base_field = _prepare_lightfield(lightfield, surface)
        for theta_i in self.theta_i_vals:
            src = _rotate_source(base_field, theta_i)
            for theta_r in self.theta_r_vals:
                for phi in self.phi_vals:
                    vd = _rotate_view(view_direction_base, theta_r, phi)
                    try:
                        sf = model.evaluate(src, surface, vd)
                        mean_brdf = float(np.mean(sf.radiance))
                    except Exception:
                        mean_brdf = 0.0
                    measurements.append(
                        GoniometricMeasurement(
                            theta_i=theta_i, theta_r=theta_r,
                            phi_i=phi, phi_r=phi,
                            brdf=mean_brdf,
                        )
                    )
        return measurements


def _prepare_lightfield(lightfield, surface) -> object:
    if hasattr(lightfield, "generate_light_field"):
        shape = getattr(surface, "shape", (16, 16))
        return lightfield.generate_light_field(shape=shape, spacing=1.0)
    return lightfield


def _rotate_source(lightfield, theta_i: float) -> object:
    import copy
    lf = copy.copy(lightfield)
    # The lightfield's .direction is the *propagation* direction
    # (source -> surface), i.e. the negative of the incident direction.
    # Rotating the incident direction by theta_i about the y-axis gives
    # omega_i = [sin(theta_i), 0, cos(theta_i)], so the propagation
    # direction becomes its negative.
    direction = np.array([-np.sin(theta_i), 0.0, -np.cos(theta_i)], dtype=float)
    norm = np.linalg.norm(direction)
    if norm > 0:
        direction = direction / norm
    H, W = lf.direction.shape[:2]
    lf.direction = np.broadcast_to(direction.reshape(1, 1, 3), (H, W, 3))
    return lf


def _rotate_view(base: np.ndarray, theta_r: float, phi: float) -> np.ndarray:
    x = np.sin(theta_r) * np.cos(phi)
    y = np.sin(theta_r) * np.sin(phi)
    z = np.cos(theta_r)
    return np.array([x, y, z], dtype=float)
