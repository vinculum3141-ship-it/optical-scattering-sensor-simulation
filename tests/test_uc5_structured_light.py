"""Unit tests for UC5 Structured Light 3D Scanning modules.

Tests FringeProjector, PhaseExtractor, PhaseUnwrapper,
HeightReconstructor, and SurfaceComparator.
"""

import numpy as np
import pytest

from optical_metrology.analysis.phase import PhaseExtractor, PhaseUnwrapper
from optical_metrology.analysis.reconstruction import HeightReconstructor, SurfaceComparator
from optical_metrology.illumination.structured import FringeProjector


class TestFringeProjector:
    def test_default_parameters(self):
        fp = FringeProjector()
        assert fp.period == 16.0
        assert len(fp.phase_shifts) == 4
        assert fp.orientation == "vertical"

    def test_invalid_orientation_raises(self):
        with pytest.raises(ValueError, match="orientation"):
            FringeProjector(orientation="diagonal")

    def test_pattern_shape(self):
        fp = FringeProjector(period=16.0)
        patterns = fp.generate_patterns((32, 64))
        assert len(patterns) == 4
        for lf in patterns:
            assert lf.intensity.shape == (32, 64)

    def test_intensity_range(self):
        fp = FringeProjector(period=16.0, phase_shifts=[0.0])
        patterns = fp.generate_patterns((16, 16))
        intensity = patterns[0].intensity
        assert np.all(intensity >= 0.0)
        assert np.all(intensity <= 1.0)

    def test_phase_shift_produces_different_patterns(self):
        fp = FringeProjector(period=32.0, phase_shifts=[0.0, np.pi])
        patterns = fp.generate_patterns((16, 32))
        assert not np.allclose(patterns[0].intensity, patterns[1].intensity)

    def test_horizontal_orientation(self):
        fp = FringeProjector(period=16.0, orientation="horizontal")
        patterns = fp.generate_patterns((32, 32))
        col0 = patterns[0].intensity[:, 0]
        col1 = patterns[0].intensity[:, 1]
        assert np.allclose(col0, col1)

    def test_vertical_orientation(self):
        fp = FringeProjector(period=16.0, orientation="vertical")
        patterns = fp.generate_patterns((32, 32))
        row0 = patterns[0].intensity[0, :]
        row1 = patterns[0].intensity[1, :]
        assert np.allclose(row0, row1)


class TestPhaseExtractor:
    def test_extract_known_phase(self):
        h, w = 16, 32
        period = 32.0
        shifts = [0.0, np.pi / 2, np.pi, 3 * np.pi / 2]
        x = np.arange(w, dtype=float)
        X = np.broadcast_to(x, (h, w))
        true_phase = 2.0 * np.pi * X / period
        fringes = [0.5 * (1.0 + np.sin(true_phase + s)) for s in shifts]
        ex = PhaseExtractor(phase_shifts=shifts)
        wrapped = ex.extract(fringes)
        expected_wrapped = -np.arctan2(
            np.sum([f * np.sin(s) for f, s in zip(fringes, shifts)], axis=0),
            np.sum([f * np.cos(s) for f, s in zip(fringes, shifts)], axis=0),
        )
        assert np.allclose(wrapped, expected_wrapped, atol=1e-10)

    def test_wrong_number_of_images_raises(self):
        ex = PhaseExtractor(phase_shifts=[0.0, np.pi / 2])
        with pytest.raises(ValueError, match="Expected 2"):
            ex.extract([np.ones((4, 4))])

    def test_extract_uniform_phase(self):
        h, w = 8, 8
        shifts = [0.0, np.pi / 2, np.pi, 3 * np.pi / 2]
        fringes = [0.5 * np.ones((h, w)) for _ in shifts]
        ex = PhaseExtractor(phase_shifts=shifts)
        wrapped = ex.extract(fringes)
        assert np.allclose(wrapped, wrapped[0, 0])


class TestPhaseUnwrapper:
    def test_unwrap_flat_phase(self):
        phase = np.zeros((16, 16))
        uw = PhaseUnwrapper()
        result = uw.unwrap(phase)
        assert np.allclose(result, 0.0)

    def test_unwrap_removes_discontinuity(self):
        h, w = 8, 8
        phase = np.zeros((h, w))
        phase[:, w // 2:] = 2.0 * np.pi - 0.1
        uw = PhaseUnwrapper()
        result = uw.unwrap(phase)
        diff = result[:, w // 2] - result[:, w // 2 - 1]
        assert np.all(np.abs(diff) < np.pi)

    def test_unwrap_preserves_shape(self):
        phase = np.random.uniform(-np.pi, np.pi, (10, 15))
        uw = PhaseUnwrapper()
        result = uw.unwrap(phase)
        assert result.shape == phase.shape


class TestHeightReconstructor:
    def test_reconstruct_flat(self):
        hr = HeightReconstructor()
        measured = np.zeros((8, 8))
        reference = np.zeros((8, 8))
        height = hr.reconstruct(measured, reference, period=16.0, projection_angle=0.5)
        assert np.allclose(height, 0.0)

    def test_reconstruct_positive_height(self):
        hr = HeightReconstructor()
        measured = np.full((4, 4), np.pi)
        reference = np.zeros((4, 4))
        height = hr.reconstruct(measured, reference, period=16.0, projection_angle=0.5)
        expected = (np.pi * 16.0) / (2.0 * np.pi * np.tan(0.5))
        assert np.allclose(height, expected)


class TestSurfaceComparator:
    def test_identical_maps(self):
        sc = SurfaceComparator()
        gt = np.ones((8, 8))
        result = sc.compare(gt, gt)
        assert result["rms"] == 0.0
        assert result["mae"] == 0.0
        assert result["max_error"] == 0.0

    def test_constant_offset(self):
        sc = SurfaceComparator()
        rec = np.zeros((4, 4))
        gt = np.ones((4, 4))
        result = sc.compare(rec, gt)
        assert np.isclose(result["rms"], 1.0)
        assert np.isclose(result["mae"], 1.0)
        assert np.isclose(result["max_error"], 1.0)

    def test_shape_mismatch_raises(self):
        sc = SurfaceComparator()
        with pytest.raises(ValueError, match="Shape mismatch"):
            sc.compare(np.ones((4, 4)), np.ones((8, 8)))
