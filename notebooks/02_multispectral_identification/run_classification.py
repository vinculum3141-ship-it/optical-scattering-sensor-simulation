#!/usr/bin/env python3
"""Run a UC2 multispectral material-classification workflow from the command line."""

from __future__ import annotations

import argparse

import numpy as np

from optical_metrology.analysis import ReferenceSpectrum, SpectralAnalyzer
from optical_metrology.detector import DigitalImage


def build_example_data():
    wavelengths = np.array([450.0, 550.0, 650.0])
    reference = np.array([0.85, 0.15, 0.05])
    background = np.array([0.10, 0.20, 0.80])

    pixels = np.zeros((32, 32, 3), dtype=float)
    pixels[:, :, :] = background
    pixels[8:24, 8:16, :] = reference
    pixels[8:24, 16:24, :] = np.array([0.25, 0.45, 0.25])

    image = DigitalImage(pixels=pixels, metadata={"bit_depth": 12, "wavelengths": wavelengths})

    analyzer = SpectralAnalyzer(
        reference_library=[
            ReferenceSpectrum("coating", reference, wavelengths),
            ReferenceSpectrum("substrate", background, wavelengths),
        ]
    )
    report = analyzer.analyze(image)
    return report, wavelengths


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a UC2 multispectral classification example")
    parser.add_argument("--bands", type=int, default=3)
    args = parser.parse_args()

    report, wavelengths = build_example_data()
    classification = report.measurements["classification"]
    labels = classification["labels"]
    confidence = classification["confidence"]

    print("UC2 multispectral classification")
    print(f"  bands={len(wavelengths)}")
    print(f"  dominant_label={labels[16, 16]}")
    print(f"  dominant_confidence={confidence[16, 16]:.3f}")
    print(f"  sample_band_ratio={report.measurements['band_ratios']['b0_1']:.3f}")


if __name__ == "__main__":
    main()
