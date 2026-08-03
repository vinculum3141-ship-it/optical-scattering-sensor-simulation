"""Robot Framework test library for UC1 Defect Inspection."""

from typing import Optional, Tuple

import numpy as np

from optical_metrology.analysis import DefectAnalyzer, TiledAcquisition
from optical_metrology.detector import CMOSDetector
from optical_metrology.illumination import bright_field, dark_field, ring_light
from optical_metrology.optics import GaussianPSF, OpticalPropagator, OpticalSystem
from optical_metrology.scattering import LambertianScattering
from optical_metrology.surface import (
    CrackSurface,
    DentSurface,
    FlatSurface,
    Material,
    PitSurface,
    ScratchedSurface,
    StainSurface,
)


class DefectInspectionLibrary:
    """Test library for UC1 defect inspection verification."""

    def __init__(self):
        self._results = {}

    def create_defect_analyzer(self, threshold: str = "0.1", min_area: str = "2"):
        self._analyzer = DefectAnalyzer(
            threshold=float(threshold),
            min_area=int(min_area),
        )
        return self._analyzer

    def create_scratched_surface(self, shape: str = "16x16", depth: str = "0.5", width: str = "3"):
        h, w = [int(s) for s in shape.split("x")]
        self._surface = ScratchedSurface(shape=(h, w), scratch_depth=float(depth), scratch_width=int(width))

    def create_flat_surface(self, shape: str = "8x8"):
        h, w = [int(s) for s in shape.split("x")]
        self._surface = FlatSurface(shape=(h, w))

    def create_dent_surface(self, shape: str = "16x16", depth: str = "0.5", radius: str = "3"):
        h, w = [int(s) for s in shape.split("x")]
        self._surface = DentSurface(shape=(h, w), depth=float(depth), radius=float(radius))

    def create_bright_field_source(self):
        self._source = bright_field(wavelength=532e-9, power=1e-3, incidence_angle=0.0)

    def create_dark_field_source(self):
        self._source = dark_field(wavelength=532e-9, power=2e-3, incidence_angle=0.785, azimuth=0.0)

    def create_scattering(self):
        self._scattering = LambertianScattering()
        self._view = np.array([0, 0, 1])

    def create_optical_system(self):
        self._optical_system = OpticalSystem(
            wavelength=532e-9, numerical_aperture=0.25,
            focal_length=50e-3, magnification=1.0,
        )

    def create_propagator(self):
        self._propagator = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)

    def create_detector(self, exposure_time: str = "1e-3", qe: str = "0.5"):
        self._detector = CMOSDetector(
            exposure_time=float(exposure_time),
            quantum_efficiency=float(qe),
        )

    def run_pipeline(self):
        lf = self._source.generate_light_field(
            shape=self._surface.height.shape, spacing=0.5
        )
        sf = self._scattering.evaluate(lf, self._surface, self._view)
        sensor = self._propagator.propagate(sf, self._optical_system)
        self._image = self._detector.capture(sensor)

    def analyze_for_defects(self):
        self._report = self._analyzer.analyze(self._image)
        self._results = self._report.measurements

    def defects_should_be_detected(self):
        if not self._results.get("has_defects", False):
            raise AssertionError("Expected defects but none detected")

    def no_defects_should_be_detected(self):
        if self._results.get("has_defects", True):
            raise AssertionError("Expected no defects but some were detected")

    def defect_count_should_be(self, expected: str):
        actual = self._results.get("defect_count", 0)
        expected_int = int(expected)
        if actual != expected_int:
            raise AssertionError(f"Expected {expected_int} defects, got {actual}")

    def surface_roughness_should_be_positive(self):
        roughness = self._surface.roughness
        if roughness <= 0:
            raise AssertionError(f"Expected positive roughness, got {roughness}")

    def pass_fail_should_pass(self):
        passed, reason = self._analyzer.pass_fail(require_zero=True)
        if not passed:
            raise AssertionError(f"Expected pass, got fail: {reason}")

    def pass_fail_should_fail(self):
        passed, reason = self._analyzer.pass_fail(require_zero=True)
        if passed:
            raise AssertionError("Expected fail, got pass")
