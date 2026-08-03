#!/usr/bin/env python3
"""Run a UC7 wafer-alignment workflow from the command line."""

from __future__ import annotations

import argparse

import numpy as np

from optical_metrology.analysis import RegistrationAnalyzer, SPCAnalyzer, TemplateMatcher
from optical_metrology.detector import DigitalImage


def build_example_data(shift=3, rotation=2.0):
    size = 64
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[:size, :size]
    reference = np.full((size, size), 0.12, dtype=float)

    center = size / 2
    wafer_radius = size * 0.3
    reference += 0.22 * np.exp(-((yy - center) ** 2 + (xx - center) ** 2) / (2 * wafer_radius ** 2))

    for cy in (size // 4, size // 2, size * 3 // 4):
        for cx in (size // 4, size // 2, size * 3 // 4):
            die_mask = ((xx - cx) ** 2 + (yy - cy) ** 2) <= 20
            reference[die_mask] = 0.9
            reference[np.abs(xx - cx) < 2] = 0.25
            reference[np.abs(yy - cy) < 2] = 0.25

    missing_dies = {(size // 2, size // 4), (size * 3 // 4, size * 3 // 4)}
    for cy, cx in missing_dies:
        reference[np.abs(xx - cx) < 8] = 0.08
        reference[np.abs(yy - cy) < 8] = 0.08

    reference[np.abs(xx - center) < 2] = 0.55
    reference[np.abs(yy - center) < 2] = 0.55
    reference += 0.03 * np.sin(0.14 * xx + 0.07 * yy)
    reference += rng.normal(0.0, 0.02, size=reference.shape)
    reference = np.clip(reference, 0.0, 1.0)

    test = reference.copy()
    if abs(rotation) > 0:
        try:
            from scipy.ndimage import rotate
            test = rotate(test, angle=float(rotation), mode="nearest", reshape=False)
        except Exception:
            pass
    if shift != 0:
        test = np.roll(test, shift=(shift, shift), axis=(0, 1))
    test += rng.normal(0.0, 0.015, size=test.shape)
    test = np.clip(test, 0.0, 1.0)

    ref_image = DigitalImage(pixels=reference, metadata={"bit_depth": 12})
    test_image = DigitalImage(pixels=test, metadata={"bit_depth": 12})

    matcher = TemplateMatcher(template=reference[16:40, 16:40])
    match_report = matcher.analyze(test_image)

    registration = RegistrationAnalyzer()
    registration_report = registration.analyze_pair(ref_image, test_image)

    dx = registration_report.measurements.get("dx", 0.0)
    dy = registration_report.measurements.get("dy", 0.0)

    spc = SPCAnalyzer(usl=2.0, lsl=-2.0, target=0.0, metric="dx")
    spc_report = spc.analyse_measurements([
        {"dx": dx},
        {"dx": dx + 0.2},
        {"dx": dx - 0.1},
    ])

    return match_report, registration_report, spc_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a UC7 wafer-alignment example")
    parser.add_argument("--shift", type=int, default=3)
    parser.add_argument("--rotation", type=float, default=2.0)
    args = parser.parse_args()

    match_report, registration_report, spc_report = build_example_data(shift=args.shift, rotation=args.rotation)

    print("UC7 wafer alignment")
    print(f"  match_score={match_report.measurements['match_score']:.4f}")
    print(f"  dx={registration_report.measurements['dx']:.4f}")
    print(f"  dy={registration_report.measurements['dy']:.4f}")
    print(f"  cpk={spc_report.measurements['cpk']:.4f}")
    print(f"  mean_shift={spc_report.measurements['mean_shift']:.4f}")


if __name__ == "__main__":
    main()
