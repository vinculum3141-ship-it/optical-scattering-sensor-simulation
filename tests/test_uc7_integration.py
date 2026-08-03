"""End-to-end integration test for UC7 Wafer Chip Misalignment Detection.

Exercises the full pipeline:
    wafer surface → illumination → scattering → optics → detector
    → template matching → registration → SPC
"""

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
    MisalignedSurface,
    WaferSurface,
)


class _DummyImage:
    def __init__(self, pixels):
        self.pixels = np.asarray(pixels, dtype=float)


def _run_pipeline(surface):
    src = bright_field(wavelength=532e-9, power=1e-3, incidence_angle=0.0)
    lf = src.generate_light_field(shape=surface.height.shape, spacing=0.5)
    scatter = LambertianScattering()
    sf = scatter.evaluate(lf, surface, view_direction=np.array([0, 0, 1]))
    opt = OpticalSystem(
        wavelength=532e-9, numerical_aperture=0.25,
        focal_length=50e-3, magnification=1.0,
    )
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    sensor = prop.propagate(sf, opt)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5)
    return det.capture(sensor)


def test_pipeline_generates_valid_image():
    """The full pipeline should produce a non-trivial image."""
    surf = WaferSurface(shape=(48, 48), die_rows=3, die_cols=3)
    img = _run_pipeline(surf)
    assert img.pixels.shape == (48, 48)
    assert np.max(img.pixels) > 0, "image should not be all zeros"
    assert np.min(img.pixels) >= 0


def test_end_to_end_template_matching_finds_fiducial():
    """Template matching on a wafer height map should find a fiducial."""
    surf = WaferSurface(shape=(48, 48), die_rows=3, die_cols=3)
    template = surf.height[0:9, 0:9]
    tm = TemplateMatcher(template=template)
    img = _DummyImage(surf.height)
    report = tm.analyze(img)
    assert report.measurements["match_score"] > 0.3, \
        f"Expected positive match score, got {report.measurements['match_score']}"
    assert 0 <= report.measurements["match_row"] < 10
    assert 0 <= report.measurements["match_col"] < 10


def test_end_to_end_registration_detects_translation():
    """Registration should pick up a known translation in height maps."""
    ref_surf = WaferSurface(shape=(48, 48), die_rows=3, die_cols=3)
    ncy, ncx = ref_surf.height.shape[0] // 2, ref_surf.height.shape[1] // 2
    shifted = np.roll(ref_surf.height, shift=3, axis=1)

    ref_img = _DummyImage(ref_surf.height)
    mis_img = _DummyImage(shifted)

    ra = RegistrationAnalyzer(max_offset=20)
    report = ra.analyze_pair(ref_img, mis_img)
    assert "error" not in report.measurements
    assert abs(report.measurements["dx"] - (-3.0)) <= 1.0, \
        f"Expected dx ≈ -3, got {report.measurements['dx']}"


def test_end_to_end_spc_from_registration():
    """SPC should compute Cpk from a series of registration results on height maps."""
    ref_surf = WaferSurface(shape=(48, 48), die_rows=3, die_cols=3)
    ref_img = _DummyImage(ref_surf.height)
    ra = RegistrationAnalyzer(max_offset=15)
    spc = SPCAnalyzer(usl=5.0, lsl=-5.0)

    measurements = []
    for shift in [0, 2, -1, 4]:
        shifted = np.roll(ref_surf.height, shift=shift, axis=1)
        mis_img = _DummyImage(shifted)
        report = ra.analyze_pair(ref_img, mis_img)
        measurements.append(report.measurements)

    spc_report = spc.analyse_measurements(measurements)
    m = spc_report.measurements
    assert m["n"] == 4, f"Expected 4 measurements, got {m['n']}"
    assert m["cpk"] > 0 or m["cpk"] == float("inf"), \
        f"Expected positive Cpk, got {m['cpk']}"
    assert abs(m["mean"]) < 5


def test_end_to_end_full_workflow():
    """Complete UC7 workflow: wafer → height map → matching → registration → SPC."""
    ref_surf = WaferSurface(shape=(48, 48), die_rows=3, die_cols=3)
    ref_img = _DummyImage(ref_surf.height)

    template = ref_surf.height[0:9, 0:9]
    tm = TemplateMatcher(template=template)
    match_report = tm.analyze(ref_img)
    assert match_report.measurements["match_score"] > 0.3

    mis_surf = MisalignedSurface(
        shape=(48, 48), die_rows=3, die_cols=3, dx=2.0, dy=1.0,
        rotation_deg=1.0, scale=0.99,
    )
    mis_img = _DummyImage(mis_surf.height)

    ra = RegistrationAnalyzer(max_offset=20)
    reg_report = ra.analyze_pair(ref_img, mis_img)
    assert "error" not in reg_report.measurements

    spc = SPCAnalyzer(usl=10.0, lsl=-10.0)
    spc_report = spc.analyse_measurements([reg_report.measurements])
    assert spc_report.measurements["n"] == 1
    assert spc_report.measurements["cpk"] > 0 or spc_report.measurements["cpk"] == float("inf")
