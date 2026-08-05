# 06 — LiDAR Range Finding

> Simulate a pulsed-laser rangefinder: estimate received power, compute time-of-flight, and build a point cloud.

## Objective

Walk the full ranging chain: received power from the LiDAR range equation, round-trip time-of-flight, detection of a noisy return, and conversion of range/angle into a Cartesian point cloud — showing that distance is derived from waveform analysis, not a single value.

## What you'll see

- Received-power estimate vs. range and backscatter (`LiDARRangeEquation`)
- Round-trip time-of-flight and pulse broadening (`TimeOfFlightPropagator`)
- Peak and timing extraction from a synthetic return (`WaveformAnalyzer`) and a Cartesian point cloud (`generate_point_cloud`)
- Optional photon-counting path via `SPADDetector`

## Run it

- **Notebook:** open `lidar_tutorial.ipynb`, edit the parameters cell, run in order.
- **CLI:** `python run_lidar.py --help` (range, backscatter, pulse duration).

## Try next

- Increase the target range and watch received power fall off as R⁴.
- Widen the pulse and see the range estimate's timing precision drop.
- Add more scan points and see the point cloud densify.

## Learn more

- [Use-case documentation](../../docs/use-case-uc6-lidar.md)
- Key modules: `analysis.LiDARRangeEquation/TimeOfFlightPropagator/WaveformAnalyzer`, `analysis.generate_point_cloud`, `detector.SPADDetector`
