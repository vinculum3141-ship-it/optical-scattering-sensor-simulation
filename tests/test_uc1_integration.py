"""End-to-end integration test for UC1 Surface Defect Inspection.

Exercises the full pipeline:
    surface (with defect) → illumination → scattering → optics → detector → analysis
"""

import numpy as np
import pytest

from optical_metrology.analysis import DefectAnalyzer, TiledAcquisition
from optical_metrology.detector import CMOSDetector
from optical_metrology.illumination import Laser, bright_field, dark_field, ring_light
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


def test_bright_field_detects_scratch():
    """Bright-field illumination should detect a scratch as a contrast feature."""
    surf = ScratchedSurface(shape=(16, 16), scratch_depth=0.5, scratch_width=3)
    src = bright_field(wavelength=532e-9, power=1e-3, incidence_angle=0.0)
    lf = src.generate_light_field(shape=surf.height.shape, spacing=0.5)
    scatter = LambertianScattering()
    sf = scatter.evaluate(lf, surf, view_direction=np.array([0, 0, 1]))
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    sensor = prop.propagate(sf, opt)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5)
    img = det.capture(sensor)
    da = DefectAnalyzer(threshold=0.1, min_area=2)
    m = da.analyze(img).measurements
    assert m["has_defects"], "Bright-field should detect scratch"


def test_dark_field_highlights_scratch():
    """Dark-field illumination should produce higher contrast from scratch."""
    surf = ScratchedSurface(shape=(16, 16), scratch_depth=0.5, scratch_width=3)
    src = dark_field(wavelength=532e-9, power=2e-3, incidence_angle=0.785, azimuth=0.0)
    lf = src.generate_light_field(shape=surf.height.shape, spacing=0.5)
    scatter = LambertianScattering()
    sf = scatter.evaluate(lf, surf, view_direction=np.array([0, 0, 1]))
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    sensor = prop.propagate(sf, opt)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5)
    img = det.capture(sensor)
    da = DefectAnalyzer(threshold=0.05, min_area=2)
    m = da.analyze(img).measurements
    assert m["has_defects"], "Dark-field should highlight scratch"


def test_defect_types_all_detectable():
    """Multiple defect types should all be detectable."""
    surfaces = [
        ("dent", DentSurface(shape=(16, 16), depth=0.5, radius=3.0)),
        ("pit", PitSurface(shape=(16, 16), depth=0.5, radius=3.0)),
        ("crack", CrackSurface(shape=(16, 16), depth=0.4, width=1, length=10)),
        ("scratch", ScratchedSurface(shape=(16, 16), scratch_depth=0.5, scratch_width=2)),
        ("stain", StainSurface(shape=(16, 16), depth=0.15, radius=6.0)),
    ]
    src = bright_field(wavelength=532e-9, power=5e-3, incidence_angle=0.0)
    scatter = LambertianScattering()
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5)

    for name, surf in surfaces:
        lf = src.generate_light_field(shape=surf.height.shape, spacing=0.5)
        sf = scatter.evaluate(lf, surf, view_direction=np.array([0, 0, 1]))
        sensor = prop.propagate(sf, opt)
        img = det.capture(sensor)
        da = DefectAnalyzer(threshold=0.02, min_area=2)
        m = da.analyze(img).measurements
        assert m["has_defects"], f"{name} should be detectable"


def test_tiled_acquisition_scratch():
    """Tiled acquisition of a scratched surface should cover the full FOV."""
    src = bright_field(wavelength=532e-9, power=5e-3, incidence_angle=0.0)
    scatter = LambertianScattering()
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5)

    def tile_pipeline(r, c, h, w):
        sub = ScratchedSurface(shape=(h, w), scratch_depth=0.5, scratch_width=3)
        lf = src.generate_light_field(shape=sub.height.shape, spacing=0.5)
        sf = scatter.evaluate(lf, sub, view_direction=np.array([0, 0, 1]))
        sensor = prop.propagate(sf, opt)
        return det.capture(sensor).pixels.astype(float)

    ta = TiledAcquisition(tile_height=16, tile_width=16, overlap=0.0)
    result = ta.acquire(tile_pipeline, 32, 32)
    assert result.shape == (32, 32)
    assert np.max(result) > 0


def test_ring_light_illuminates_defect():
    """Ring-light illumination should make defects visible."""
    surf = ScratchedSurface(shape=(16, 16), scratch_depth=0.5, scratch_width=3)
    scatter = LambertianScattering()
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5)

    combined = np.zeros_like(surf.height, dtype=float)
    for src in ring_light(wavelength=532e-9, power=1e-3, ring_angle=0.698, n_segments=8):
        lf = src.generate_light_field(shape=surf.height.shape, spacing=0.5)
        sf = scatter.evaluate(lf, surf, view_direction=np.array([0, 0, 1]))
        sensor = prop.propagate(sf, opt)
        img = det.capture(sensor)
        combined += img.pixels.astype(float)

    da = DefectAnalyzer(threshold=0.02, min_area=2)
    m = da.analyze(img).measurements
    assert m["has_defects"], "Ring light should make defect visible"


def test_pass_fail_clean_surface():
    """A defect-free surface should pass inspection."""
    surf = FlatSurface(shape=(8, 8))
    src = bright_field(wavelength=532e-9, power=1e-3, incidence_angle=0.0)
    lf = src.generate_light_field(shape=surf.height.shape, spacing=0.5)
    scatter = LambertianScattering()
    sf = scatter.evaluate(lf, surf, view_direction=np.array([0, 0, 1]))
    opt = OpticalSystem(wavelength=532e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    sensor = prop.propagate(sf, opt)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5)
    img = det.capture(sensor)
    da = DefectAnalyzer(threshold=1.5)
    da.analyze(img)
    passed, reason = da.pass_fail(require_zero=True)
    assert passed, f"Clean surface should pass: {reason}"
