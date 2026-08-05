"""Multi-parameter sweep over the scattering distribution.

Provides :class:`ScatteringSweep`, a harness that varies surface
roughness, incidence angle, wavelength, refractive index, and/or
scattering model in any combination, and records how the angular
radiance distribution changes for each configuration.

This is the generalisation of :class:`GoniometricSweep`: instead of
sweeping only the *geometry* angles, the user supplies factories for the
scattering model, light source, and surface, and any of the five knobs
can be swept independently or together.

Each case is evaluated over a range of reflection angles ``theta_r`` at a
fixed incidence angle ``theta_i``, producing a distribution curve
``radiance(theta_r)``.  Summary metrics (peak, peak angle, integrated
power, half-width) are computed per case and returned in a structured
report, so the effect of each parameter on the scattering distribution
can be read off directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import inspect
import itertools

import numpy as np

from .base import AnalysisModule, AnalysisReport
from .goniometry import _prepare_lightfield, _rotate_source, _rotate_view


def _filter_kwargs(fn: Callable, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only keyword arguments accepted by *fn*.

    Callables with a ``**kwargs`` catch-all receive everything; others
    receive only the parameters they declare.  This lets one factory be
    used for several sweep dimensions without error.
    """
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return kwargs
    accepts_var_kw = any(
        p.kind is inspect.Parameter.VAR_KEYWORD
        for p in sig.parameters.values()
    )
    if accepts_var_kw:
        return kwargs
    return {k: v for k, v in kwargs.items() if k in sig.parameters}


@dataclass
class SweepCase:
    """Result of evaluating one parameter combination.

    Attributes
    ----------
    parameters : dict
        The swept parameter values for this case (only the dimensions
        that were varied; missing keys mean "left at factory default").
    model : str
        Name of the scattering model used.
    theta_r : np.ndarray
        Reflection angles in radians at which the distribution was sampled.
    radiance : np.ndarray
        Radiance (or BRDF-like aggregate) at each reflection angle.
    """

    parameters: Dict[str, float]
    model: str
    theta_r: np.ndarray
    radiance: np.ndarray

    @property
    def peak(self) -> float:
        """Maximum radiance of the distribution."""
        return float(np.max(self.radiance))

    @property
    def peak_angle(self) -> float:
        """Reflection angle at the peak, in radians."""
        return float(self.theta_r[int(np.argmax(self.radiance))])

    @property
    def total_power(self) -> float:
        """Integrated radiance over the sampled angle range."""
        return float(np.trapezoid(self.radiance, self.theta_r))

    @property
    def half_width(self) -> float:
        """Full width at half maximum of the distribution, in radians."""
        half = 0.5 * self.peak
        if half <= 0:
            return 0.0
        above = np.where(self.radiance >= half)[0]
        if len(above) == 0:
            return 0.0
        return float(self.theta_r[above[-1]] - self.theta_r[above[0]])


class ScatteringSweep(AnalysisModule):
    """Sweep scattering parameters and observe the angular distribution.

    Parameters
    ----------
    theta_i : float
        Fixed incidence angle in radians for all evaluations.  A swept
        ``incident_angle`` overrides this per case.
    theta_r_range : tuple of (float, float, int)
        ``(start, stop, num)`` reflection-angle axis in radians along
        which the distribution is sampled.
    view_direction : array_like, shape (3,)
        Base view direction used with the reflection-angle rotation.
    metric : str
        How radiance is aggregated over the pixel grid before sampling:
        ``"mean"`` (default) or ``"peak"``.
    shape : tuple of (int, int)
        Light-field / surface grid dimensions.
    spacing : float
        Grid spacing in physical units.
    """

    def __init__(
        self,
        theta_i: float = 0.0,
        theta_r_range: Tuple[float, float, int] = (0.0, 1.4, 40),
        view_direction: Sequence[float] = (0.0, 0.0, 1.0),
        metric: str = "mean",
        shape: Tuple[int, int] = (16, 16),
        spacing: float = 1.0,
    ):
        if metric not in ("mean", "peak"):
            raise ValueError(f"Unsupported metric: {metric!r}")
        self.theta_i = float(theta_i)
        self.theta_r_vals = np.linspace(*theta_r_range)
        self.view_direction = np.asarray(view_direction, dtype=float)
        self.metric = metric
        self.shape = tuple(shape)
        self.spacing = float(spacing)

    def sweep(
        self,
        models: Dict[str, Callable],
        source_factory: Callable,
        surface_factory: Callable,
        roughness: Optional[Sequence[float]] = None,
        incident_angle: Optional[Sequence[float]] = None,
        wavelength: Optional[Sequence[float]] = None,
        refractive_index: Optional[Sequence[float]] = None,
    ) -> List[SweepCase]:
        """Evaluate every combination of the swept parameters.

        Parameters
        ----------
        models : dict of str -> callable
            Mapping from model name to a factory that builds a scattering
            model.  Each factory is called as ``factory(**parameters)``
            where ``parameters`` contains only the swept dimensions for
            that case.
        source_factory : callable
            Builds a :class:`~illumination.LightSource` (or any object
            with ``generate_light_field``).  Called as
            ``source_factory(**parameters)``.
        surface_factory : callable
            Builds a :class:`~surface.Surface`.  Called as
            ``surface_factory(**parameters)``.  The typical mapping is
            ``amplitude=parameters["roughness"]`` and
            ``material=Material(refractive_index=parameters["refractive_index"])``.
        roughness : sequence of float or None
            Values to sweep for surface/model roughness.
        incident_angle : sequence of float or None
            Incidence angles in radians to sweep.
        wavelength : sequence of float or None
            Wavelengths in metres to sweep.
        refractive_index : sequence of float or None
            Refractive indices to sweep.
        models_... : (see models)

        Returns
        -------
        list of SweepCase
            One result per parameter combination, ordered as the product
            of the swept dimensions (roughness × incident angle ×
            wavelength × refractive index), for each model in ``models``.
        """
        if not models:
            raise ValueError("models must be non-empty")
        dimensions: Dict[str, List[Optional[float]]] = {
            "roughness": list(roughness) if roughness is not None else [None],
            "incident_angle": list(incident_angle) if incident_angle is not None else [None],
            "wavelength": list(wavelength) if wavelength is not None else [None],
            "refractive_index": list(refractive_index) if refractive_index is not None else [None],
        }
        keys = [k for k, v in dimensions.items() if v != [None]]

        cases: List[SweepCase] = []
        for model_name, model_factory in models.items():
            for combo in itertools.product(*(dimensions[k] for k in keys)):
                parameters = {k: v for k, v in zip(keys, combo) if v is not None}
                theta_i = float(parameters.get("incident_angle", self.theta_i))

                model = model_factory(**_filter_kwargs(model_factory, parameters))
                source = source_factory(**_filter_kwargs(source_factory, parameters))
                surface = surface_factory(**_filter_kwargs(surface_factory, parameters))

                dist = self._distribution(model, source, surface, theta_i)
                cases.append(SweepCase(parameters, model_name, dist[0], dist[1]))
        return cases

    def _distribution(
        self, model, source, surface, theta_i: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Sample radiance(theta_r) for one configuration."""
        lightfield = _prepare_lightfield(source, surface)
        lightfield = _rotate_source(lightfield, theta_i)

        radiance = np.zeros_like(self.theta_r_vals, dtype=float)
        for idx, theta_r in enumerate(self.theta_r_vals):
            vd = _rotate_view(self.view_direction, float(theta_r), 0.0)
            sf = model.evaluate(lightfield, surface, vd)
            if self.metric == "mean":
                radiance[idx] = float(np.mean(sf.radiance))
            else:
                radiance[idx] = float(np.max(sf.radiance))
        return self.theta_r_vals.copy(), radiance

    def analyze(self, cases: List[SweepCase]) -> AnalysisReport:
        """Summarise a list of :class:`SweepCase` results.

        Parameters
        ----------
        cases : list of SweepCase
            Results from :meth:`sweep`.

        Returns
        -------
        AnalysisReport
            Measurements include ``n_cases``, ``swept_parameters``,
            ``theta_r`` (the shared angle axis), and ``cases`` — a list
            of per-case dicts with the swept parameters, model name, and
            summary metrics (``peak``, ``peak_angle``, ``total_power``,
            ``half_width``) plus the full radiance curve.
        """
        if not cases:
            return AnalysisReport(measurements={
                "n_cases": 0,
                "swept_parameters": [],
                "cases": [],
            })

        swept = sorted({k for c in cases for k in c.parameters})
        case_rows = []
        for c in cases:
            row: Dict[str, Any] = dict(c.parameters)
            row["model"] = c.model
            row["peak"] = c.peak
            row["peak_angle"] = c.peak_angle
            row["total_power"] = c.total_power
            row["half_width"] = c.half_width
            row["radiance"] = c.radiance.tolist()
            case_rows.append(row)

        return AnalysisReport(measurements={
            "n_cases": len(cases),
            "swept_parameters": swept,
            "theta_r": cases[0].theta_r.tolist(),
            "cases": case_rows,
        })
