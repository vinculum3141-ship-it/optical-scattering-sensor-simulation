#!/usr/bin/env python3
"""Run a UC5 structured-light workflow from the command line."""

from __future__ import annotations

import argparse

import numpy as np

from optical_metrology.analysis import HeightReconstructor, PhaseExtractor, PhaseUnwrapper, SurfaceComparator
from optical_metrology.illumination import FringeProjector


def build_example_data(shape=(48, 64), period=16.0, projection_angle=0.5):
    projector = FringeProjector(period=period, orientation="vertical")
    patterns = projector.generate_patterns(shape=shape)

    height_map = np.zeros(shape, dtype=float)
    height_map[10:30, 20:40] = 3.0
    height_map[30:40, 10:30] = -2.0

    fringe_images = []
    for field in patterns:
        intensity = 0.5 * (1.0 + np.sin(2.0 * np.pi * (field.intensity - 0.5)))
        fringe_images.append(intensity)

    phase_extractor = PhaseExtractor(phase_shifts=[0.0, np.pi / 2.0, np.pi, 3.0 * np.pi / 2.0])
    wrapped_phase = phase_extractor.extract(fringe_images)
    unwrapped_phase = PhaseUnwrapper().unwrap(wrapped_phase)

    reconstructor = HeightReconstructor()
    reconstructed = reconstructor.reconstruct(
        measured_phase=unwrapped_phase,
        reference_phase=np.zeros_like(unwrapped_phase),
        period=period,
        projection_angle=projection_angle,
    )
    comparison = SurfaceComparator().compare(reconstructed, height_map)
    return {
        "wrapped_phase": wrapped_phase,
        "unwrapped_phase": unwrapped_phase,
        "reconstructed": reconstructed,
        "comparison": comparison,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a UC5 structured-light example")
    parser.add_argument("--period", type=float, default=16.0)
    parser.add_argument("--projection-angle", type=float, default=0.5)
    args = parser.parse_args()

    data = build_example_data(period=args.period, projection_angle=args.projection_angle)
    print("UC5 structured light")
    print(f"  wrapped_phase_mean={float(np.mean(data['wrapped_phase'])):.4f}")
    print(f"  unwrapped_phase_mean={float(np.mean(data['unwrapped_phase'])):.4f}")
    print(f"  reconstructed_rms={data['comparison']['rms']:.4f}")
    print(f"  reconstructed_mae={data['comparison']['mae']:.4f}")
    print(f"  reconstructed_max_error={data['comparison']['max_error']:.4f}")


if __name__ == "__main__":
    main()
