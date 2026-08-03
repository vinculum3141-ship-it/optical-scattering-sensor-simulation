"""Unit tests for UC6 LiDAR range finding modules."""

import numpy as np
import pytest

from optical_metrology.analysis.lidar import (
    LiDARRangeEquation,
    TimeOfFlightPropagator,
    WaveformAnalyzer,
    generate_point_cloud,
)
from optical_metrology.detector.spad import SPADDetector
from optical_metrology.illumination.scanning import ScanningMechanism
from optical_metrology.scattering import RayleighScattering, MieScattering


def test_rayleigh_scattering_evaluates():
    from optical_metrology.illumination import LightSource
    src = LightSource(wavelength=532e-9)
    lf = src.generate_light_field(shape=(8, 8), spacing=1.0)
    model = RayleighScattering(particle_density=1e6)
    sf = model.evaluate(lf, None, np.array([0, 0, 1]))
    assert sf.radiance.shape == (8, 8)
    assert np.any(sf.radiance > 0)


def test_rayleigh_wavelength_dependence():
    from optical_metrology.illumination import LightSource
    lf_red = LightSource(wavelength=700e-9).generate_light_field(shape=(4, 4), spacing=1.0)
    lf_blue = LightSource(wavelength=450e-9).generate_light_field(shape=(4, 4), spacing=1.0)
    model = RayleighScattering(particle_density=1e6, reference_wavelength=532e-9)
    sf_red = model.evaluate(lf_red, None, np.array([0, 0, 1]))
    sf_blue = model.evaluate(lf_blue, None, np.array([0, 0, 1]))
    assert np.mean(sf_blue.radiance) > np.mean(sf_red.radiance)


def test_mie_scattering_evaluates():
    from optical_metrology.illumination import LightSource
    src = LightSource(wavelength=532e-9)
    lf = src.generate_light_field(shape=(8, 8), spacing=1.0)
    model = MieScattering(particle_density=1e5, particle_radius=1e-6)
    sf = model.evaluate(lf, None, np.array([0, 0, 1]))
    assert sf.radiance.shape == (8, 8)


def test_scanning_mechanism_raster():
    sm = ScanningMechanism(scan_pattern="raster", field_of_view_deg=30, resolution=16, scan_rate=10)
    points = sm.generate_scan_points(duration=0.1)
    assert len(points) > 0
    assert len(points[0]) == 3


def test_scanning_mechanism_spiral():
    sm = ScanningMechanism(scan_pattern="spiral", field_of_view_deg=30, resolution=16, scan_rate=10)
    points = sm.generate_scan_points(duration=0.1)
    assert len(points) > 0


def test_scanning_mechanism_invalid_pattern():
    with pytest.raises(ValueError, match="Unsupported scan pattern"):
        ScanningMechanism(scan_pattern="invalid")


def test_lidar_range_equation():
    lre = LiDARRangeEquation(transmitter_power=10, receiver_aperture_diameter=0.1)
    pr = lre.compute_range(range_m=10, backscatter_coeff=1e-4)
    assert pr > 0
    assert pr < 10


def test_lidar_range_inverse_square():
    lre = LiDARRangeEquation(transmitter_power=10, receiver_aperture_diameter=0.1)
    pr1 = lre.compute_range(range_m=10)
    pr2 = lre.compute_range(range_m=20)
    ratio = pr1 / pr2
    assert abs(ratio - 4.0) < 0.01


def test_tof_propagator():
    tofp = TimeOfFlightPropagator()
    tof, broadened = tofp.compute_tof(range_m=15, pulse_duration=1e-9)
    assert abs(tof - 1e-7) < 1e-8
    assert broadened >= 1e-9


def test_tof_tilt_broadening():
    tofp = TimeOfFlightPropagator()
    _, broadened_tilt = tofp.compute_tof(range_m=15, pulse_duration=1e-9, target_tilt_deg=45)
    _, broadened_flat = tofp.compute_tof(range_m=15, pulse_duration=1e-9, target_tilt_deg=0)
    assert broadened_tilt > broadened_flat


def test_waveform_analyzer_peak():
    wf = np.zeros(50)
    wf[25] = 1.0
    wa = WaveformAnalyzer()
    m = wa.analyze(wf).measurements
    assert m["peak_index"] == 25


def test_waveform_analyzer_fwhm():
    wf = np.zeros(50)
    wf[20:31] = 1.0
    wa = WaveformAnalyzer()
    m = wa.analyze(wf).measurements
    assert m["fwhm_samples"] == 10


def test_waveform_analyzer_cfd():
    wf = np.zeros(50)
    wf[10:40] = np.linspace(0, 1, 30)
    wa = WaveformAnalyzer(cf_fraction=0.5)
    m = wa.analyze(wf).measurements
    assert m["cfd_crossing_index"] >= 10


def test_generate_point_cloud():
    ranges = np.array([10.0, 20.0])
    az = np.array([0.0, np.pi / 4])
    el = np.array([0.0, 0.0])
    pc = generate_point_cloud(ranges, az, el)
    assert pc.shape == (2, 4)


def test_spad_detector_detect():
    spad = SPADDetector(dead_time=50e-9, photon_detection_efficiency=1.0, dark_count_rate=0)
    timestamps = np.array([1e-9, 2e-9, 3e-9])
    events = spad.detect(timestamps, pixel=0)
    assert len(events) > 0


def test_spad_detector_dead_time():
    spad = SPADDetector(dead_time=100e-9, photon_detection_efficiency=1.0, dark_count_rate=0)
    timestamps = np.array([1e-9, 2e-9, 150e-9])
    events = spad.detect(timestamps, pixel=0)
    assert len(events) == 2


def test_spad_detector_count():
    spad = SPADDetector(dead_time=10e-9, photon_detection_efficiency=1.0, dark_count_rate=0)
    timestamps = np.array([1e-9, 2e-9, 3e-9])
    count = spad.count_events(timestamps, pixel=0)
    assert count > 0
