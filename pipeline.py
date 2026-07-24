"""Pipeline orchestrator: run a full simulation in one call.

The :class:`SimulationPipeline` assembles a source, surface, scattering
model, optical system, detector, and analysers, then runs the full chain
with a single ``.run()`` invocation.  Every component is optional —
set any to ``None`` to skip that stage.

Usage
-----
>>> from illumination import Laser, GaussianBeamProfile
>>> from surface import RoughSurface, Material
>>> from scattering import LambertianScattering
>>> from optics import OpticalSystem, GaussianPSF, OpticalPropagator
>>> from detector import CMOSDetector
>>> from analysis import HistogramAnalyzer
>>>
>>> pipeline = SimulationPipeline(
...     source=Laser(532e-9, power=5e-3, beam_profile=GaussianBeamProfile(w0=2.0)),
...     surface=RoughSurface((32, 32), sigma=4.0, amplitude=0.3, material=Material("silicon")),
...     scattering=LambertianScattering(albedo=0.7),
...     optics=OpticalSystem(focal_length=0.05, aperture_diameter=0.008),
...     propagator=OpticalPropagator(GaussianPSF(sigma=1.0)),
...     detector=CMOSDetector(exposure_time=1e-5, gain=1.0),
...     analysers=[HistogramAnalyzer()],
... )
>>> result = pipeline.run(shape=(32, 32), spacing=0.5,
...                       view_direction=[0, 0, 1])
>>> result.digital_image.pixels.shape
(32, 32)
>>> result.report.measurements["mean_intensity"]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from analysis import AnalysisReport, ImageAnalyzer
from detector import DigitalImage
from optics import SensorField
from scattering import ScatteredField


@dataclass
class PipelineResult:
    """Structured output from a complete simulation pipeline run.

    Attributes
    ----------
    light_field : LightField or None
        Output from the illumination stage.
    surface : Surface or None
        Surface geometry used (may be passed in directly).
    scattered_field : ScatteredField or None
        Output from the scattering stage.
    sensor_field : SensorField or None
        Output from the optics stage.
    digital_image : DigitalImage or None
        Output from the detector stage.
    report : AnalysisReport or None
        Output from the analysis stage.
    """
    light_field: Optional[object] = None
    surface: Optional[object] = None
    scattered_field: Optional[ScatteredField] = None
    sensor_field: Optional[SensorField] = None
    digital_image: Optional[DigitalImage] = None
    report: Optional[AnalysisReport] = None


class SimulationPipeline:
    """Orchestrate a full sensor-simulation pipeline.

    Each parameter is optional — set to ``None`` to skip that layer.
    This allows running partial pipelines (e.g. illumination only,
    or detector + analysis with a synthetic sensor field).

    Parameters
    ----------
    source : LightSource or None
        Illumination source used to generate the light field.
    surface : Surface or SurfaceGenerator or None
        Surface geometry.  If a generator (callable) is given, it is
        called with ``(shape, material)`` to produce the surface.
    scattering : ScatteringModel or None
        Scattering model evaluated on the light field and surface.
    optics : OpticalSystem or None
        Optical system description passed to the propagator.
    propagator : OpticalPropagator or None
        Propagator that applies PSF convolution.  Ignored if
        ``optics`` is ``None``.
    detector : CMOSDetector or None
        Detector that captures a sensor field into a digital image.
    analysers : list of AnalysisModule or None
        Analysis modules run on the digital image.
    surface_material : Material or None
        Material passed to the surface generator if ``surface`` is
        callable.
    """

    def __init__(
        self,
        source=None,
        surface=None,
        scattering=None,
        optics=None,
        propagator=None,
        detector=None,
        analysers=None,
        surface_material=None,
    ):
        self.source = source
        self.surface = surface
        self.scattering = scattering
        self.optics = optics
        self.propagator = propagator
        self.detector = detector
        self.analysers = analysers or []
        self.surface_material = surface_material

    def run(
        self,
        shape=(16, 16),
        spacing=0.5,
        view_direction=None,
    ) -> PipelineResult:
        """Execute the full pipeline and return all intermediate results.

        Parameters
        ----------
        shape : tuple of int
            Grid dimensions ``(height, width)`` for the light field
            and surface.
        spacing : float
            Grid spacing passed to the light source.
        view_direction : array-like, shape ``(3,)``
            Direction from surface toward the observer (normalised
            internally).  Defaults to ``[0, 0, 1]``.

        Returns
        -------
        PipelineResult
            Every stage's output, plus the analysis report.
        """
        if view_direction is None:
            view_direction = np.array([0.0, 0.0, 1.0], dtype=float)
        view_direction = np.asarray(view_direction, dtype=float)
        view_direction = view_direction / np.linalg.norm(view_direction)

        lf = None
        surface = None
        scattered = None
        sensor = None
        image = None
        report = None

        # --- Stage 1: Illumination ---
        if self.source is not None:
            if hasattr(self.source, "propagation_direction") and self.source.propagation_direction is not None:
                pass
            lf = self.source.generate_light_field(shape=shape, spacing=spacing)

        # --- Stage 2: Surface ---
        if self.surface is not None:
            if callable(self.surface):
                surface = self.surface(shape, material=self.surface_material)
            else:
                surface = self.surface

        # --- Stage 3: Scattering ---
        if self.scattering is not None and lf is not None and surface is not None:
            scattered = self.scattering.evaluate(
                lf, surface, view_direction=view_direction,
            )

        # --- Stage 4: Optics ---
        if self.optics is not None and self.propagator is not None and scattered is not None:
            sensor = self.propagator.propagate(scattered, self.optics)

        # --- Stage 5: Detector ---
        if self.detector is not None and sensor is not None:
            image = self.detector.capture(sensor)

        # --- Stage 6: Analysis ---
        if self.analysers and image is not None:
            analyzer = ImageAnalyzer(modules=self.analysers)
            report = analyzer.analyze(image)

        return PipelineResult(
            light_field=lf,
            surface=surface,
            scattered_field=scattered,
            sensor_field=sensor,
            digital_image=image,
            report=report,
        )

    def describe(self) -> str:
        """Return a human-readable summary of the configured pipeline."""
        lines = ["SimulationPipeline:"]
        pairs = [
            ("Illumination", self.source),
            ("Surface", self.surface),
            ("Scattering", self.scattering),
            ("Optical system", self.optics),
            ("Propagator", self.propagator),
            ("Detector", self.detector),
            ("Analysers", self.analysers),
        ]
        for label, obj in pairs:
            if obj is None:
                lines.append(f"  {label}:  (skipped)")
            elif isinstance(obj, list):
                for m in obj:
                    lines.append(f"  {label}:  {type(m).__name__}")
            else:
                lines.append(f"  {label}:  {type(obj).__name__}")
        return "\n".join(lines)
