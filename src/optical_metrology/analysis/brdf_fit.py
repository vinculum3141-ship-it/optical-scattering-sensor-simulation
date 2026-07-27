"""BRDF fitting analysis module (UC4).

Fits scattering model parameters (roughness, F₀) to angle-resolved
BRDF data using non-linear least-squares optimisation.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import numpy as np

from .base import AnalysisModule, AnalysisReport


class BRDFFitter(AnalysisModule):
    """Fit BRDF model parameters to measured angle-resolved data.

    Parameters
    ----------
    model_fn : callable
        ``model_fn(theta_i, theta_r, phi_i, phi_r, **params) -> brdf``
        that computes the BRDF for given angles and parameters.
    initial_params : dict
        Initial guesses for the model parameters.
    param_bounds : dict of (float, float) or None
        Per-parameter (min, max) bounds.
    """

    def __init__(
        self,
        model_fn: Callable,
        initial_params: Dict[str, float],
        param_bounds: Optional[Dict[str, tuple]] = None,
    ):
        self.model_fn = model_fn
        self.initial_params = initial_params
        self.param_bounds = param_bounds or {}

    def analyze(self, data: List[Dict]) -> AnalysisReport:
        theta_i = np.array([d["theta_i"] for d in data])
        theta_r = np.array([d["theta_r"] for d in data])
        phi_i = np.array([d.get("phi_i", 0.0) for d in data])
        phi_r = np.array([d.get("phi_r", 0.0) for d in data])
        measured = np.array([d["brdf"] for d in data])

        fitted = self._fit(theta_i, theta_r, phi_i, phi_r, measured)

        predicted = self.model_fn(theta_i, theta_r, phi_i, phi_r, **fitted)
        residuals = measured - predicted
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((measured - np.mean(measured)) ** 2)
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        fitted_params = {k: float(v) for k, v in fitted.items()}
        return AnalysisReport(measurements={
            "fitted_params": fitted_params,
            "r_squared": float(r_squared),
            "rmse": float(np.sqrt(np.mean(residuals ** 2))),
        })

    def _fit(self, theta_i, theta_r, phi_i, phi_r, measured) -> Dict[str, float]:
        import warnings
        p0 = [self.initial_params[k] for k in self.initial_params]
        p_names = list(self.initial_params.keys())

        bounds_lower = []
        bounds_upper = []
        for k in p_names:
            if k in self.param_bounds:
                lo, hi = self.param_bounds[k]
            else:
                lo, hi = -np.inf, np.inf
            bounds_lower.append(lo)
            bounds_upper.append(hi)

        def residual(p):
            kwargs = dict(zip(p_names, p))
            pred = self.model_fn(theta_i, theta_r, phi_i, phi_r, **kwargs)
            return (pred - measured).ravel()

        try:
            from scipy.optimize import least_squares
            result = least_squares(residual, p0, bounds=(bounds_lower, bounds_upper))
            fitted = result.x
        except ImportError:
            p, _, _, _ = np.linalg.lstsq(
                np.column_stack([theta_i, theta_r, np.ones_like(theta_i)]),
                measured, rcond=None
            )
            fitted = np.zeros(len(p0))
            fitted[:min(len(p0), 3)] = p[:min(len(p0), 3)]

        return dict(zip(p_names, fitted))
