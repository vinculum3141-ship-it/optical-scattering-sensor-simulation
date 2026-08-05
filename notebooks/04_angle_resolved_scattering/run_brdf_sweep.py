#!/usr/bin/env python3
"""Run a UC4 angle-resolved scattering workflow from the command line."""

from __future__ import annotations

import argparse

import numpy as np

from optical_metrology.analysis import BRDFFitter, GoniometricSweep
from optical_metrology.illumination import Laser
from optical_metrology.scattering import BeckmannScattering, LambertianScattering
from optical_metrology.surface import RoughSurface, Material


def _coerce_range(values):
    start, stop, count = values
    return (float(start), float(stop), int(count))


def build_example_data(theta_i_range, theta_r_range, phi_range):
    surface = RoughSurface(shape=(16, 16), sigma=2.0, amplitude=0.2, material=Material("silicon"))
    source = Laser(wavelength=550e-9, power=1.0)
    source.propagation_direction = np.array([0.0, 0.0, -1.0])
    source.direction = np.array([0.0, 0.0, -1.0])
    model = BeckmannScattering(roughness=0.2)
    sweep = GoniometricSweep(theta_i_range=theta_i_range, theta_r_range=theta_r_range, phi_range=phi_range)
    measurements = sweep.sweep(model, source, surface, np.array([0.0, 0.0, 1.0]))
    return sweep, measurements


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a UC4 BRDF sweep")
    parser.add_argument("--theta-i-range", type=float, nargs=3, default=[0.0, 0.8, 4.0])
    parser.add_argument("--theta-r-range", type=float, nargs=3, default=[0.0, 0.8, 4.0])
    parser.add_argument("--phi-range", type=float, nargs=3, default=[0.0, 0.0, 1.0])
    args = parser.parse_args()

    sweep, measurements = build_example_data(
        theta_i_range=_coerce_range(tuple(args.theta_i_range)),
        theta_r_range=_coerce_range(tuple(args.theta_r_range)),
        phi_range=_coerce_range(tuple(args.phi_range)),
    )
    report = sweep.analyze([(m.theta_i, m.theta_r, m.phi_i, m.phi_r, m.brdf) for m in measurements])

    def model_fn(theta_i, theta_r, phi_i, phi_r, roughness, scale):
        return np.full_like(theta_i, scale, dtype=float) * np.exp(-0.5 * np.square(theta_r / max(roughness, 1e-6)))

    fitter = BRDFFitter(model_fn=model_fn, initial_params={"roughness": 0.2, "scale": 1.0}, param_bounds={"roughness": (1e-3, 1.0), "scale": (1e-6, 10.0)})
    fit_report = fitter.analyze(report.measurements["measurements"])

    print("UC4 BRDF sweep")
    print(f"  n_measurements={report.measurements['n_measurements']}")
    print(f"  mean_brdf={report.measurements['mean_brdf']}")
    print(f"  max_brdf={report.measurements['max_brdf']}")
    print("fit_summary=")
    for key, value in fit_report.measurements.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
