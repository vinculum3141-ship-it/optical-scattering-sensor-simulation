#!/usr/bin/env python3
"""Run a UC3 sensor-performance-characterization workflow from the command line."""

from __future__ import annotations

import argparse

import numpy as np

from optical_metrology.analysis import DynamicRangeAnalyzer, LinearityTestAnalyzer, PTCAnalyzer, greyscale_wedge
from optical_metrology.detector import CMOSDetector
from optical_metrology.illumination import FlatFieldSource
from optical_metrology.optics import GaussianPSF, OpticalPropagator, OpticalSystem
from optical_metrology.scattering import LambertianScattering
from optical_metrology.surface import FlatSurface


def build_images(levels: list[float], exposure_time: float, gain: float, read_noise_sigma: float, shape: tuple[int, int]):
    src = FlatFieldSource(wavelength=550e-9, power=1.0, intensity_levels=levels)
    surf = FlatSurface(shape=shape)
    scatter = LambertianScattering()
    view = np.array([0.0, 0.0, 1.0])
    optics = OpticalSystem(wavelength=550e-9, numerical_aperture=0.25, focal_length=50e-3, magnification=1.0)
    propagator = OpticalPropagator(GaussianPSF(sigma=1.0), throughput_enabled=False)
    detector = CMOSDetector(
        exposure_time=exposure_time,
        quantum_efficiency=0.5,
        gain=gain,
        read_noise_sigma=read_noise_sigma,
        rng_seed=42,
    )

    images = []
    for light_field in src.generate_intensity_sweep(shape=shape, spacing=1.0):
        scattered = scatter.evaluate(light_field, surf, view)
        sensor_field = propagator.propagate(scattered, optics)
        images.append(detector.capture(sensor_field))
    return images


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a UC3 sensor-characterization simulation")
    parser.add_argument("--levels", type=float, nargs="+", default=[0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    parser.add_argument("--exposure-time", type=float, default=1e-3)
    parser.add_argument("--gain", type=float, default=2.0)
    parser.add_argument("--read-noise-sigma", type=float, default=2.0)
    parser.add_argument("--shape", type=int, nargs=2, default=(16, 16))
    args = parser.parse_args()

    images = build_images(
        levels=args.levels,
        exposure_time=args.exposure_time,
        gain=args.gain,
        read_noise_sigma=args.read_noise_sigma,
        shape=tuple(args.shape),
    )

    ptc_result = PTCAnalyzer().analyze(images)
    dynamic_range_result = DynamicRangeAnalyzer().analyze(images[-1])
    linearity_result = LinearityTestAnalyzer(ideal_exposures=args.levels).analyze(images)

    print("UC3 sensor characterization")
    print(f"  levels={args.levels}")
    print("PTC summary:")
    for key, value in ptc_result.measurements.items():
        print(f"  {key}: {value}")
    print("Dynamic range summary:")
    for key, value in dynamic_range_result.measurements.items():
        print(f"  {key}: {value}")
    print("Linearity summary:")
    for key, value in linearity_result.measurements.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
