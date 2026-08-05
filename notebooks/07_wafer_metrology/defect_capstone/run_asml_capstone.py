#!/usr/bin/env python3
"""Run a UC7 ASML-style wafer defect-inspection capstone workflow."""

from __future__ import annotations

import argparse
import numpy as np

from optical_metrology.analysis import (
    DefectAnalyzer,
    ErrorMapAnalyzer,
    SNRAnalyzer,
    SpeckleRoughnessEstimator,
)
from optical_metrology.detector import CMOSDetector, DigitalImage
from optical_metrology.detector.noise_models import SpeckleNoise
from optical_metrology.illumination import bright_field
from optical_metrology.optics import GaussianPSF, OpticalPropagator, OpticalSystem
from optical_metrology.scattering import LambertianScattering
from optical_metrology.surface import RoughSurface, WaferSurface
from optical_metrology.surface.base import GeometryAnalyzer, Material


def build_asml_wafer_surface(
    shape=(96, 96),
    roughness_amplitude=0.20,
    defect_depth=1.8,
    defect_radius=5,
    defect_center=None,
) -> object:
    wafer = WaferSurface(
        shape=shape,
        die_rows=4,
        die_cols=4,
        street_width=3,
        fiducial_size=4,
        fiducial_height=1.8,
        die_height_val=1.0,
    )
    rough = RoughSurface(shape=shape, sigma=8.0, amplitude=roughness_amplitude)

    height = wafer.height + 0.12 * rough.height
    if defect_center is None:
        defect_center = (shape[0] * 3 // 4, shape[1] // 2)

    yy, xx = np.mgrid[: shape[0], : shape[1]]
    distance_sq = (yy - defect_center[0]) ** 2 + (xx - defect_center[1]) ** 2
    height -= defect_depth * np.exp(-distance_sq / (2.0 * defect_radius**2))

    return GeometryAnalyzer.analyze(height, material=Material("silicon", refractive_index=3.9))


def capture_image(
    surface,
    wavelength=193e-9,
    spacing=0.5,
    exposure_time=1e-3,
    quantum_efficiency=0.45,
    read_noise_sigma=1.8,
    coherence_length=1e-4,
    rng_seed=1,
) -> DigitalImage:
    source = bright_field(wavelength=wavelength, power=1.0, incidence_angle=0.05)
    lf = source.generate_light_field(shape=surface.height.shape, spacing=spacing)

    scatter = LambertianScattering(albedo=0.75)
    scattered = scatter.evaluate(lf, surface, view_direction=np.array([0.0, 0.0, 1.0]))

    optics = OpticalSystem(
        wavelength=wavelength,
        aperture_diameter=8e-3,
        focal_length=50e-3,
        magnification=1.0,
    )
    propagator = OpticalPropagator(GaussianPSF(sigma=1.2), throughput_enabled=True)
    sensor = propagator.propagate(scattered, optics)

    detector = CMOSDetector(
        exposure_time=exposure_time,
        quantum_efficiency=quantum_efficiency,
        read_noise_sigma=read_noise_sigma,
        gain=2.0,
        bit_depth=12,
        pixel_area=25e-12,
        rng_seed=rng_seed,
        noise_models=[SpeckleNoise(coherence_length=coherence_length)],
    )
    return detector.capture(sensor, surface=surface)


def summarize_workflow(
    defect_image,
    reference_image,
    coherence_length=1e-4,
    wavelength=193e-9,
) -> dict:
    defect_analyzer = DefectAnalyzer(
        threshold=0.06,
        min_area=10,
        max_area=600,
        reference_image=reference_image.pixels,
    )
    defect_report = defect_analyzer.analyze(defect_image)

    error_analyzer = ErrorMapAnalyzer(reference_image)
    error_report = error_analyzer.analyze(defect_image)

    snr_analyzer = SNRAnalyzer(
        method="single_image",
        signal_region=(20, 20, 40, 40),
        noise_region=(0, 0, 12, 12),
    )
    snr_report = snr_analyzer.analyze(defect_image)

    roughness_analyzer = SpeckleRoughnessEstimator(
        coherence_length=coherence_length,
        wavelength=wavelength,
        roi=(20, 20, 40, 40),
    )
    roughness_report = roughness_analyzer.analyze(defect_image)

    return {
        "defect": defect_report.measurements,
        "error": {
            "mae": error_report.measurements["mae"],
            "rmse": error_report.measurements["rmse"],
            "psnr_db": error_report.measurements["psnr_db"],
        },
        "snr": snr_report.measurements,
        "roughness": roughness_report.measurements,
    }


def build_reference_image(
    surface,
    wavelength=193e-9,
    spacing=0.5,
    exposure_time=1e-3,
) -> DigitalImage:
    source = bright_field(wavelength=wavelength, power=1.0, incidence_angle=0.05)
    lf = source.generate_light_field(shape=surface.height.shape, spacing=spacing)

    scatter = LambertianScattering(albedo=0.75)
    scattered = scatter.evaluate(lf, surface, view_direction=np.array([0.0, 0.0, 1.0]))

    optics = OpticalSystem(
        wavelength=wavelength,
        aperture_diameter=8e-3,
        focal_length=50e-3,
        magnification=1.0,
    )
    propagator = OpticalPropagator(GaussianPSF(sigma=1.2), throughput_enabled=True)
    sensor = propagator.propagate(scattered, optics)

    detector = CMOSDetector(
        exposure_time=exposure_time,
        quantum_efficiency=0.45,
        read_noise_sigma=0.0,
        gain=2.0,
        bit_depth=12,
        pixel_area=25e-12,
        rng_seed=0,
        noise_models=[],
    )
    return detector.capture(sensor, surface=surface)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a UC7 ASML-style wafer defect inspection example")
    parser.add_argument("--coherence", type=float, default=1e-4)
    parser.add_argument("--exposure", type=float, default=1e-3)
    parser.add_argument("--roughness", type=float, default=0.20)
    parser.add_argument("--defect-depth", type=float, default=2.0)
    args = parser.parse_args()

    clean_surface = build_asml_wafer_surface(roughness_amplitude=args.roughness, defect_depth=0.0)
    defect_surface = build_asml_wafer_surface(
        roughness_amplitude=args.roughness,
        defect_depth=args.defect_depth,
    )

    reference_image = build_reference_image(clean_surface, exposure_time=args.exposure)
    defect_image = capture_image(
        defect_surface,
        exposure_time=args.exposure,
        coherence_length=args.coherence,
        rng_seed=3,
    )

    summary = summarize_workflow(defect_image, reference_image, coherence_length=args.coherence)

    print("ASML-style wafer defect inspection capstone")
    print(f"  coherence_length={args.coherence:.1e} m")
    print(f"  exposure_time={args.exposure:.3e} s")
    print(f"  roughness_amplitude={args.roughness:.3f}")
    print(f"  defect_depth={args.defect_depth:.3f}")
    print("\nCapture result:")
    print(f"  defect_count={summary['defect']['defect_count']}")
    print(f"  total_defect_area={summary['defect']['total_defect_area']:.1f} px")
    print(f"  snr_db={summary['snr']['snr_db']:.2f} dB")
    print(f"  speckle_contrast={summary['roughness']['speckle_contrast']:.3f}")
    print(f"  estimated_roughness_rms={summary['roughness']['estimated_roughness_rms']:.4f} m")
    print(f"  error_rmse={summary['error']['rmse']:.4f}")
    print(f"  error_psnr={summary['error']['psnr_db']:.2f} dB")

    if summary['defect']['has_defects']:
        print("  defect_types:")
        for defect in summary['defect']['defects']:
            print(f"    - label={defect['label']} type={defect['defect_type']} area={defect['area']} bbox={defect['bbox']}")


if __name__ == "__main__":
    main()
