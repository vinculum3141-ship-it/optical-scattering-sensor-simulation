"""Unit tests for UC7 Wafer Chip Misalignment Detection.

Tests wafer surface generators, template matching, registration, and SPC.
"""

import numpy as np
import pytest

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
    FlatSurface,
    Material,
    MisalignedSurface,
    WaferSurface,
)


class _DummyImage:
    """Minimal stand-in for DigitalImage when only .pixels is needed."""
    def __init__(self, pixels):
        self.pixels = pixels


class TestWaferSurface:
    def test_wafer_surface_creates_die_grid(self):
        surf = WaferSurface(shape=(64, 64))
        assert surf.height.shape == (64, 64)
        assert np.any(surf.height > 0), "expected raised die areas"

    def test_wafer_surface_has_fiducial_marks(self):
        surf = WaferSurface(shape=(64, 64))
        h, w = surf.height.shape
        assert surf.height[0, 0] > 1.0, "top-left fiducial missing"
        assert surf.height[0, w - 1] > 1.0, "top-right fiducial missing"
        assert surf.height[h - 1, 0] > 1.0, "bottom-left fiducial missing"
        assert surf.height[h - 1, w - 1] > 1.0, "bottom-right fiducial missing"

    def test_wafer_surface_has_scribe_streets(self):
        surf = WaferSurface(shape=(64, 64), die_rows=2, die_cols=2,
                            street_width=8)
        h, w = surf.height.shape
        mid = h // 2
        assert np.all(surf.height[mid - 4:mid + 4, :] == 0.0), \
            "horizontal scribe street should be at zero"

    def test_wafer_surface_small_shape_does_not_crash(self):
        surf = WaferSurface(shape=(16, 16), die_rows=10, die_cols=10)
        assert surf.height.shape == (16, 16)

    def test_wafer_with_material(self):
        mat = Material("silicon")
        surf = WaferSurface(shape=(32, 32), material=mat)
        assert surf.material is not None
        assert surf.material.name == "silicon"

    def test_wafer_surface_die_count(self):
        surf = WaferSurface(shape=(100, 100), die_rows=3, die_cols=5)
        assert surf.die_rows == 3
        assert surf.die_cols == 5
        assert np.max(surf.height) > 0


class TestMisalignedSurface:
    def test_misaligned_with_translation(self):
        ref = WaferSurface(shape=(64, 64))
        mis = MisalignedSurface(shape=(64, 64), dx=4.0, dy=0.0)
        assert mis.height.shape == (64, 64)
        assert not np.array_equal(mis.height, ref.height), \
            "misaligned surface should differ from reference"

    def test_misaligned_with_rotation(self):
        mis = MisalignedSurface(shape=(64, 64), rotation_deg=5.0)
        assert mis.height.shape == (64, 64)

    def test_misaligned_with_scale(self):
        mis = MisalignedSurface(shape=(64, 64), scale=0.9)
        assert mis.height.shape == (64, 64)

    def test_misaligned_with_material(self):
        mat = Material("silicon")
        mis = MisalignedSurface(shape=(64, 64), dx=2.0, material=mat)
        assert mis.material.name == "silicon"


class TestTemplateMatching:
    def test_template_matcher_finds_fiducial(self):
        ref = WaferSurface(shape=(48, 48))
        template = ref.height[0:7, 0:7]
        tm = TemplateMatcher(template=template)
        img = _DummyImage(ref.height.copy())
        report = tm.analyze(img)
        assert report.measurements["match_score"] > 0.3

    def test_template_matcher_reports_position(self):
        ref = WaferSurface(shape=(48, 48))
        template = ref.height[0:7, 0:7]
        tm = TemplateMatcher(template=template)
        img = _DummyImage(ref.height.copy())
        report = tm.analyze(img)
        assert "match_row" in report.measurements
        assert "match_col" in report.measurements


class TestRegistration:
    def test_registration_identical_images(self):
        arr = np.random.rand(32, 32).astype(float)
        ref = _DummyImage(arr.copy())
        tst = _DummyImage(arr.copy())
        ra = RegistrationAnalyzer(max_offset=10)
        report = ra.analyze_pair(ref, tst)
        assert report.measurements["dx"] == 0.0
        assert report.measurements["dy"] == 0.0

    def test_registration_detects_shift(self):
        arr = np.random.rand(32, 32).astype(float)
        shifted = np.roll(arr, shift=3, axis=1)
        ref = _DummyImage(arr)
        tst = _DummyImage(shifted)
        ra = RegistrationAnalyzer(max_offset=10)
        report = ra.analyze_pair(ref, tst)
        assert abs(report.measurements["dx"] - (-3.0)) <= 1.0

    def test_registration_shape_mismatch(self):
        ref = _DummyImage(np.zeros((16, 16)))
        tst = _DummyImage(np.zeros((32, 32)))
        ra = RegistrationAnalyzer()
        report = ra.analyze_pair(ref, tst)
        assert "error" in report.measurements


class TestSPC:
    def test_spc_cpk_perfect(self):
        spc = SPCAnalyzer(usl=1.0, lsl=-1.0, target=0.0)
        measurements = [{"dx": 0.0}, {"dx": 0.0}, {"dx": 0.0}]
        report = spc.analyse_measurements(measurements)
        assert report.measurements["cpk"] == float("inf")

    def test_spc_cpk_finite(self):
        spc = SPCAnalyzer(usl=1.0, lsl=-1.0, target=0.0)
        measurements = [{"dx": 0.5}, {"dx": 0.6}, {"dx": 0.4},
                         {"dx": 0.7}, {"dx": 0.3}]
        report = spc.analyse_measurements(measurements)
        assert 0 < report.measurements["cpk"] < 5

    def test_spc_mean_shift(self):
        spc = SPCAnalyzer(usl=2.0, lsl=-2.0, target=0.0)
        measurements = [{"dx": 1.0}, {"dx": 1.0}, {"dx": 1.0}]
        report = spc.analyse_measurements(measurements)
        assert abs(report.measurements["mean_shift"] - 1.0) < 1e-6

    def test_spc_trend_slope(self):
        spc = SPCAnalyzer(usl=5.0, lsl=-5.0)
        measurements = [{"dx": float(i)} for i in range(10)]
        report = spc.analyse_measurements(measurements)
        assert abs(report.measurements["trend_slope"] - 1.0) < 0.01

    def test_spc_empty_measurements(self):
        spc = SPCAnalyzer()
        report = spc.analyse_measurements([])
        assert report.measurements["n"] == 0

    def test_spc_single_measurement(self):
        spc = SPCAnalyzer(usl=1.0, lsl=-1.0)
        report = spc.analyse_measurements([{"dx": 0.1}])
        assert report.measurements["n"] == 1

    def test_spc_different_metric(self):
        spc = SPCAnalyzer(usl=1.0, lsl=-1.0, metric="rotation_deg")
        measurements = [{"rotation_deg": 0.05}, {"rotation_deg": -0.03}]
        report = spc.analyse_measurements(measurements)
        assert report.measurements["n"] == 2
