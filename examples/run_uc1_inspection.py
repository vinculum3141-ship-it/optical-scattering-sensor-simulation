#!/usr/bin/env python3
"""Run a UC1 defect-inspection simulation from the command line.

This script demonstrates the framework end to end and exposes a small
set of useful knobs for experimenting with defect visibility and
inspection analysis.
"""

from __future__ import annotations

import argparse

import numpy as np

from optical_metrology.analysis import DefectAnalyzer
from optical_metrology.detector import CMOSDetector
from optical_metrology.illumination import bright_field, dark_field
from optical_metrology.optics import GaussianPSF, OpticalPropagator, OpticalSystem
from optical_metrology.pipeline import SimulationPipeline
from optical_metrology.scattering import LambertianScattering
from optical_metrology.surface import CrackSurface, DentSurface, Material, PitSurface, StainSurface


def build_surface(defect_type: str, shape: tuple[int, int]):
    surface_map = {
        "dent": DentSurface,
        "pit": PitSurface,
        "crack": CrackSurface,
        "stain": StainSurface,
    }
    cls = surface_map[defect_type]
    kwargs = {
        "shape": shape,
        "material": Material("silicon"),
    }
    if defect_type in {"dent", "pit"}:
        kwargs.update(depth=0.5, radius=4.0)
    elif defect_type == "crack":
        kwargs.update(depth=0.25, width=2, length=24, jaggedness=1.0)
    else:
        kwargs.update(depth=0.15, radius=6.0)
    return cls(**kwargs)


def build_source(illumination: str):
    if illumination == "brightfield":
        return bright_field(wavelength=532e-9, power=1.0, incidence_angle=0.0)
    if illumination == "darkfield":
        return dark_field(wavelength=532e-9, power=2.0, incidence_angle=0.785)
    raise ValueError(f"Unsupported illumination: {illumination}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a UC1 defect inspection simulation")
    parser.add_argument("--defect", choices=["dent", "pit", "crack", "stain"], default="dent")
    parser.add_argument("--illumination", choices=["brightfield", "darkfield"], default="darkfield")
    parser.add_argument("--threshold", type=float, default=0.08)
    parser.add_argument("--shape", type=int, nargs=2, default=(64, 64))
    parser.add_argument("--exposure-time", type=float, default=1e-5)
    args = parser.parse_args()

    shape = tuple(args.shape)
    surface = build_surface(args.defect, shape)
    source = build_source(args.illumination)

    pipeline = SimulationPipeline(
        source=source,
        surface=surface,
        scattering=LambertianScattering(albedo=0.7),
        optics=OpticalSystem(focal_length=0.05, aperture_diameter=0.008, wavelength=532e-9),
        propagator=OpticalPropagator(GaussianPSF(sigma=1.0)),
        detector=CMOSDetector(exposure_time=args.exposure_time, gain=1.0),
        analysers=[DefectAnalyzer(threshold=args.threshold)],
    )

    result = pipeline.run(shape=shape, spacing=0.5, view_direction=np.array([0.0, 0.0, 1.0]))

    analyzer = DefectAnalyzer(threshold=args.threshold)
    analysis_report = analyzer.analyze(result.digital_image)
    measurements = analysis_report.measurements

    print(f"defect={args.defect}")
    print(f"illumination={args.illumination}")
    print(f"threshold={args.threshold}")
    print("analysis_results=")
    for key, value in measurements.items():
        print(f"  {key}: {value}")
    ok, reason = analyzer.pass_fail(max_defects=3, max_defect_area=200)
    print(f"pass_fail={ok}")
    print(f"reason={reason}")


if __name__ == "__main__":
    main()
