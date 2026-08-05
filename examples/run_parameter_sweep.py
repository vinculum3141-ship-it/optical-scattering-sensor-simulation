#!/usr/bin/env python3
"""Run a multi-parameter scattering sweep (roughness, angle, wavelength,
refractive index, model) and print how the distribution changes."""

from __future__ import annotations

import argparse

import numpy as np

from optical_metrology.analysis import ScatteringSweep
from optical_metrology.illumination import Laser
from optical_metrology.scattering import BeckmannScattering, GGXScattering
from optical_metrology.surface import Material, RoughSurface


def _source_factory(**kw):
    src = Laser(wavelength=kw.get("wavelength", 550e-9), power=1.0)
    src.propagation_direction = np.array([0.0, 0.0, -1.0])
    return src


def _surface_factory(**kw):
    return RoughSurface(
        shape=(16, 16),
        sigma=2.0,
        amplitude=kw.get("roughness", 0.2),
        material=Material(refractive_index=kw.get("refractive_index", 1.5)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a multi-parameter scattering sweep")
    parser.add_argument("--roughness", type=float, nargs="+", default=[0.05, 0.15, 0.3])
    parser.add_argument("--theta-i", type=float, nargs="+", default=[0.0, 0.3])
    parser.add_argument("--wavelength", type=float, nargs="+", default=[450e-9, 650e-9])
    parser.add_argument("--refractive-index", type=float, nargs="+", default=[1.5, 3.5])
    args = parser.parse_args()

    sweep = ScatteringSweep(theta_r_range=(0.0, 1.2, 60))
    cases = sweep.sweep(
        models={
            "beckmann": lambda **kw: BeckmannScattering(roughness=kw.get("roughness", 0.1)),
            "ggx": lambda **kw: GGXScattering(roughness=kw.get("roughness", 0.1)),
        },
        source_factory=_source_factory,
        surface_factory=_surface_factory,
        roughness=args.roughness,
        incident_angle=args.theta_i,
        wavelength=args.wavelength,
        refractive_index=args.refractive_index,
    )
    report = sweep.analyze(cases)

    print("Multi-parameter scattering sweep")
    print(f"  swept parameters: {', '.join(report.measurements['swept_parameters'])}")
    print(f"  n_cases:          {report.measurements['n_cases']}")
    print(f"  models:           {sorted({c['model'] for c in report.measurements['cases']})}")
    print("  per-case summary (first 8):")
    for row in report.measurements["cases"][:8]:
        params = ", ".join(f"{k}={v:.3g}" for k, v in sorted(row.items())
                           if k in ("roughness", "incident_angle", "wavelength", "refractive_index"))
        print(
            f"    {row['model']:9s} {params:55s} "
            f"peak={row['peak']:.4f} @{row['peak_angle']:.2f} rad, "
            f"FWHM={row['half_width']:.2f} rad"
        )


if __name__ == "__main__":
    main()
