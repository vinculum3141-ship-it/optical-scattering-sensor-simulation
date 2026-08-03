#!/usr/bin/env python3
"""Run a UC6 LiDAR/ranging workflow from the command line."""

from __future__ import annotations

import argparse

import numpy as np

from optical_metrology.analysis import LiDARRangeEquation, TimeOfFlightPropagator, WaveformAnalyzer, generate_point_cloud


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a UC6 LiDAR example")
    parser.add_argument("--range-m", type=float, default=12.0)
    parser.add_argument("--backscatter", type=float, default=1e-4)
    parser.add_argument("--pulse-duration", type=float, default=1e-9)
    args = parser.parse_args()

    range_eq = LiDARRangeEquation(transmitter_power=1.0, receiver_aperture_diameter=0.1)
    received_power = range_eq.compute_range(args.range_m, backscatter_coeff=args.backscatter)

    tof_prop = TimeOfFlightPropagator()
    tof, broadened_duration = tof_prop.compute_tof(args.range_m, pulse_duration=args.pulse_duration)

    waveform = np.array([0.0, 0.2, 0.7, 1.0, 0.8, 0.4, 0.1], dtype=float)
    waveform_analysis = WaveformAnalyzer(cf_fraction=0.5).analyze(waveform)

    azimuths = np.array([0.0, 0.4, 0.8])
    elevations = np.array([0.0, 0.1, -0.1])
    ranges = np.array([args.range_m, args.range_m + 1.0, args.range_m + 2.0])
    point_cloud = generate_point_cloud(ranges, azimuths, elevations)

    print("UC6 LiDAR ranging")
    print(f"  received_power={received_power:.6e}")
    print(f"  tof={tof:.6e}")
    print(f"  broadened_duration={broadened_duration:.6e}")
    print(f"  waveform_peak_index={waveform_analysis.measurements['peak_index']}")
    print(f"  waveform_peak_amplitude={waveform_analysis.measurements['peak_amplitude']:.4f}")
    print(f"  point_cloud_shape={point_cloud.shape}")


if __name__ == "__main__":
    main()
