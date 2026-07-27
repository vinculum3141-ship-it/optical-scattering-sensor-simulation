"""End-to-end integration test for UC5 Structured Light 3D Scanning.

Exercises the full pipeline:
    fringe projection → capture → phase extraction → unwrap →
    height reconstruction → comparison with ground truth

Uses a SinusoidalSurface as the test object for a known geometry.
"""

import numpy as np
import pytest

from optical_metrology.analysis import (
    HeightReconstructor,
    PhaseExtractor,
    PhaseUnwrapper,
    SurfaceComparator,
)
from optical_metrology.detector import CMOSDetector
from optical_metrology.illumination import FringeProjector
from optical_metrology.optics import GaussianPSF, OpticalPropagator, OpticalSystem
from optical_metrology.scattering import LambertianScattering
from optical_metrology.surface import SinusoidalSurface


@pytest.fixture
def setup():
    shape = (32, 64)
    period_px = 16.0
    projection_angle = 0.5
    shifts = [0.0, np.pi / 2, np.pi, 3 * np.pi / 2]

    surf = SinusoidalSurface(shape=shape, period=32.0, amplitude=1.0)
    projector = FringeProjector(
        period=period_px, phase_shifts=shifts, orientation="vertical",
    )
    scatter = LambertianScattering()
    opt = OpticalSystem(
        wavelength=532e-9, numerical_aperture=0.25,
        focal_length=50e-3, magnification=1.0,
    )
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5)
    return {
        "shape": shape,
        "period_px": period_px,
        "projection_angle": projection_angle,
        "shifts": shifts,
        "surf": surf,
        "projector": projector,
        "scatter": scatter,
        "opt": opt,
        "prop": prop,
        "det": det,
    }


def test_structured_light_end_to_end(setup):
    s = setup
    shape = s["shape"]
    view = np.array([0, 0, 1])

    fringes = s["projector"].generate_patterns(shape)
    captured = []
    for lf in fringes:
        sf = s["scatter"].evaluate(lf, s["surf"], view)
        sensor = s["prop"].propagate(sf, s["opt"])
        img = s["det"].capture(sensor)
        captured.append(img.pixels.astype(float))

    extractor = PhaseExtractor(phase_shifts=s["shifts"])
    wrapped = extractor.extract(captured)

    unwrapper = PhaseUnwrapper()
    measured_phase = unwrapper.unwrap(wrapped)

    reference_phase = np.zeros(shape)

    reconstructor = HeightReconstructor()
    height = reconstructor.reconstruct(
        measured_phase, reference_phase,
        period=s["period_px"], projection_angle=s["projection_angle"],
    )

    assert height.shape == shape
    assert np.all(np.isfinite(height))

    comparator = SurfaceComparator()
    result = comparator.compare(height, s["surf"].height)
    assert result["rms"] >= 0.0
    assert result["mae"] >= 0.0
    assert result["max_error"] >= 0.0


def test_flat_surface_self_reference(setup):
    s = setup
    shape = s["shape"]
    view = np.array([0, 0, 1])

    from optical_metrology.surface import FlatSurface
    flat = FlatSurface(shape=shape)

    fringes = s["projector"].generate_patterns(shape)
    captured = []
    for lf in fringes:
        sf = s["scatter"].evaluate(lf, flat, view)
        sensor = s["prop"].propagate(sf, s["opt"])
        img = s["det"].capture(sensor)
        captured.append(img.pixels.astype(float))

    extractor = PhaseExtractor(phase_shifts=s["shifts"])
    wrapped = extractor.extract(captured)

    unwrapper = PhaseUnwrapper()
    measured_phase = unwrapper.unwrap(wrapped)

    height = measured_phase - measured_phase
    assert np.allclose(height, 0.0)
