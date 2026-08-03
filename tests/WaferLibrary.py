"""Robot Framework test library for UC7 Wafer Inspection."""

from typing import Optional

import numpy as np

from optical_metrology.analysis import (
    RegistrationAnalyzer,
    SPCAnalyzer,
    TemplateMatcher,
)
from optical_metrology.detector import CMOSDetector, DigitalImage
from optical_metrology.illumination import bright_field
from optical_metrology.optics import GaussianPSF, OpticalPropagator, OpticalSystem
from optical_metrology.scattering import LambertianScattering
from optical_metrology.surface import (
    Material,
    MisalignedSurface,
    WaferSurface,
)


class _DummyImage:
    def __init__(self, pixels):
        self.pixels = np.asarray(pixels, dtype=float)


class WaferLibrary:
    """Test library for UC7 wafer inspection verification."""

    def __init__(self):
        self._results = {}
        self._measurements = []
        self._registration_measurements = []
        self._registration = None

    def create_wafer_surface(self, shape: str = "64x64", rows: str = "4",
                              cols: str = "4", street: str = "4"):
        h, w = [int(s) for s in shape.split("x")]
        self._surface = WaferSurface(
            shape=(h, w), die_rows=int(rows), die_cols=int(cols),
            street_width=int(street),
        )

    def create_misaligned_surface(self, shape: str = "64x64",
                                    dx: str = "2.0", dy: str = "1.0",
                                    rot: str = "2.0", scale: str = "0.98"):
        h, w = [int(s) for s in shape.split("x")]
        self._surface = MisalignedSurface(
            shape=(h, w), dx=float(dx), dy=float(dy),
            rotation_deg=float(rot), scale=float(scale),
        )

    def create_bright_field_source(self):
        self._source = bright_field(wavelength=532e-9, power=1e-3, incidence_angle=0.0)

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

    def create_template_matcher(self):
        self._template = self._surface.height[0:9, 0:9]
        self._matcher = TemplateMatcher(template=self._template)

    def create_registration_analyzer(self, max_offset: str = "20"):
        self._registration = RegistrationAnalyzer(max_offset=int(max_offset))

    def create_spc_analyzer(self, usl: str = "5.0", lsl: str = "-5.0"):
        self._spc = SPCAnalyzer(usl=float(usl), lsl=float(lsl))

    def run_pipeline(self):
        lf = self._source.generate_light_field(
            shape=self._surface.height.shape, spacing=0.5,
        )
        sf = self._scattering.evaluate(lf, self._surface, self._view)
        sensor = self._propagator.propagate(sf, self._optical_system)
        self._image = self._detector.capture(sensor)

    def perform_template_matching(self):
        """Match template against the height map (not pipeline image)."""
        img = _DummyImage(self._surface.height)
        self._report = self._matcher.analyze(img)
        self._results = self._report.measurements

    def perform_registration(self):
        """Register pipeline image against a reference wafer image."""
        ref_wafer = WaferSurface(shape=self._surface.shape)
        ref_lf = self._source.generate_light_field(
            shape=ref_wafer.height.shape, spacing=0.5,
        )
        ref_sf = self._scattering.evaluate(ref_lf, ref_wafer, self._view)
        ref_sensor = self._propagator.propagate(ref_sf, self._optical_system)
        self._ref_image = self._detector.capture(ref_sensor)

        self._report = self._registration.analyze_pair(self._ref_image, self._image)
        self._results = self._report.measurements
        self._registration_measurements.append(self._results.copy())

    def perform_registration_on_height_map(self):
        """Register shifted height map against reference height map (stable)."""
        ref_wafer = WaferSurface(shape=self._surface.shape)
        dy = int(getattr(self, '_reg_dy', 0))
        dx = int(getattr(self, '_reg_dx', 0))
        shifted = np.roll(ref_wafer.height, shift=dy, axis=0)
        shifted = np.roll(shifted, shift=dx, axis=1)

        ref_img = _DummyImage(ref_wafer.height)
        mis_img = _DummyImage(shifted)
        self._report = self._registration.analyze_pair(ref_img, mis_img)
        self._results = self._report.measurements
        self._registration_measurements.append(self._results.copy())

    def perform_spc_analysis(self):
        self._report = self._spc.analyse_measurements(self._registration_measurements)
        self._results = self._report.measurements

    def match_score_should_be_positive(self):
        score = self._results.get("match_score", 0)
        if score <= 0:
            raise AssertionError(f"Expected positive match score, got {score}")

    def registration_should_report_displacement(self):
        dx = abs(self._results.get("dx", 0))
        dy = abs(self._results.get("dy", 0))
        if dx < 0.1 and dy < 0.1:
            raise AssertionError(f"Expected non-zero displacement, got dx={dx}, dy={dy}")

    def cpk_should_be_positive(self):
        cpk = self._results.get("cpk", 0)
        if cpk <= 0:
            raise AssertionError(f"Expected positive Cpk, got {cpk}")

    def registration_should_report_no_error(self):
        if "error" in self._results:
            raise AssertionError(f"Registration error: {self._results['error']}")

    def spc_should_report_n_measurements(self, expected: str):
        n = self._results.get("n", 0)
        expected_n = int(expected)
        if n != expected_n:
            raise AssertionError(f"Expected {expected_n} measurements, got {n}")
