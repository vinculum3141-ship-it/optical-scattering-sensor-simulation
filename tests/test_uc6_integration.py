"""End-to-end integration tests for UC6 LiDAR Range Finding."""

import numpy as np

from optical_metrology.analysis.lidar import (
    LiDARRangeEquation,
    TimeOfFlightPropagator,
    WaveformAnalyzer,
    generate_point_cloud,
)
from optical_metrology.detector.spad import SPADDetector
from optical_metrology.illumination import LightSource, TemporalEnvelope
from optical_metrology.illumination.scanning import ScanningMechanism
from optical_metrology.scattering import RayleighScattering


def test_lidar_range_equation_integration():
    lre = LiDARRangeEquation(transmitter_power=100, receiver_aperture_diameter=0.15)
    pr = lre.compute_range(range_m=50, backscatter_coeff=2e-4)
    assert 0 < pr < 100


def test_tof_propagation():
    tofp = TimeOfFlightPropagator()
    tof, broadened = tofp.compute_tof(range_m=100, pulse_duration=5e-9, target_tilt_deg=10)
    expected_tof = 200.0 / 3e8
    assert abs(tof - expected_tof) < 1e-9
    assert broadened > 5e-9


def test_rayleigh_scattering_and_tof():
    src = LightSource(wavelength=532e-9, power=1e6)
    lf = src.generate_light_field(shape=(4, 4), spacing=1.0)
    model = RayleighScattering(particle_density=1e6)
    sf = model.evaluate(lf, None, np.array([0, 0, 1]))
    assert np.mean(sf.radiance) > 0
    lre = LiDARRangeEquation(transmitter_power=1e6, receiver_aperture_diameter=0.1)
    pr = lre.compute_range(range_m=100, backscatter_coeff=2e-4)
    tofp = TimeOfFlightPropagator()
    tof, broadened = tofp.compute_tof(range_m=100, pulse_duration=5e-9)
    assert pr > 0
    assert tof > 0


def test_spad_with_waveform():
    spad = SPADDetector(dead_time=10e-9, photon_detection_efficiency=1.0, dark_count_rate=0)
    timestamps = np.linspace(0, 100e-9, 50)
    events = spad.detect(timestamps, pixel=0)
    counts = np.zeros(50)
    for e in events:
        idx = int(e.timestamp / (100e-9 / 50))
        if idx < 50:
            counts[idx] += 1
    wa = WaveformAnalyzer()
    m = wa.analyze(counts).measurements
    assert m["peak_index"] >= 0


def test_scanning_to_point_cloud():
    sm = ScanningMechanism(scan_pattern="raster", field_of_view_deg=10, resolution=10, scan_rate=10)
    points = sm.generate_scan_points(duration=0.1)
    az = np.array([p[0] for p in points])
    el = np.array([p[1] for p in points])
    ranges = np.ones(len(points)) * 50.0
    pc = generate_point_cloud(ranges, az, el)
    assert pc.shape[1] == 4
    assert np.all(pc[:, 3] == 50.0)
