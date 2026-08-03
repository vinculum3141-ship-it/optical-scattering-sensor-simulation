"""End-to-end integration test for UC3 Sensor Performance Characterization.

Exercises the full pipeline:
    flat-field source → scattering → optics → detector → PTC analysis
"""

import numpy as np

from optical_metrology.analysis import PTCAnalyzer
from optical_metrology.detector import CMOSDetector
from optical_metrology.illumination import FlatFieldSource
from optical_metrology.optics import GaussianPSF, OpticalPropagator, OpticalSystem
from optical_metrology.scattering import LambertianScattering
from optical_metrology.surface import FlatSurface


def test_ptc_end_to_end_gain_positive():
    levels = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    src = FlatFieldSource(wavelength=550e-9, power=1.0, intensity_levels=levels)
    surf = FlatSurface(shape=(16, 16))
    scatter = LambertianScattering()
    view = np.array([0, 0, 1])
    opt = OpticalSystem(wavelength=550e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5, gain=2.0, rng_seed=42)

    images = []
    for lf in src.generate_intensity_sweep(shape=(16, 16), spacing=1.0):
        sf = scatter.evaluate(lf, surf, view)
        sensor = prop.propagate(sf, opt)
        img = det.capture(sensor)
        images.append(img)

    m = PTCAnalyzer().analyze(images).measurements
    assert m["gain"] > 0, f"Expected positive gain, got {m['gain']}"
    assert "read_noise_electrons" in m


def test_ptc_end_to_end_read_noise_reasonable():
    levels = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    src = FlatFieldSource(wavelength=550e-9, power=1.0, intensity_levels=levels)
    surf = FlatSurface(shape=(16, 16))
    scatter = LambertianScattering()
    view = np.array([0, 0, 1])
    opt = OpticalSystem(wavelength=550e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5, gain=2.0, read_noise_sigma=2.0, rng_seed=42)

    images = []
    for lf in src.generate_intensity_sweep(shape=(16, 16), spacing=1.0):
        sf = scatter.evaluate(lf, surf, view)
        sensor = prop.propagate(sf, opt)
        img = det.capture(sensor)
        images.append(img)

    m = PTCAnalyzer().analyze(images).measurements
    assert m["gain"] > 0
    rn = m["read_noise_electrons"]
    assert 0 <= rn < 10, f"Expected read noise 0–10 e⁻, got {rn}"


def test_ptc_end_to_end_full_well_reported():
    levels = [0.1, 0.3, 0.5, 0.7, 1.0]
    src = FlatFieldSource(wavelength=550e-9, power=1.0, intensity_levels=levels)
    surf = FlatSurface(shape=(16, 16))
    scatter = LambertianScattering()
    view = np.array([0, 0, 1])
    opt = OpticalSystem(wavelength=550e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    prop = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    det = CMOSDetector(exposure_time=1e-3, quantum_efficiency=0.5, gain=2.0, rng_seed=42)

    images = []
    for lf in src.generate_intensity_sweep(shape=(16, 16), spacing=1.0):
        sf = scatter.evaluate(lf, surf, view)
        sensor = prop.propagate(sf, opt)
        img = det.capture(sensor)
        images.append(img)

    m = PTCAnalyzer().analyze(images).measurements
    assert m["full_well_signal"] > 0
    assert m["dynamic_range_db"] >= 0
