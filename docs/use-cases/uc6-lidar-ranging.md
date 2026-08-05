# Use Case 6 — LiDAR Range Finding

This use case demonstrates a simple LiDAR ranging workflow.
The simulation uses a range equation, a time-of-flight model, a synthetic
waveform analyzer, and a point-cloud conversion helper to make ranging
behaviour visible without requiring a full scanner or hardware model.

## Workflow

1. Estimate received power from range and backscatter.
2. Convert range into a round-trip time-of-flight.
3. Model pulse broadening from target tilt and pulse duration.
4. Analyze a synthetic waveform for peak timing and width.
5. Convert range, azimuth, and elevation into a simple point cloud.

## Typical inputs

- Target range
- Backscatter coefficient
- Pulse duration
- Scan geometry (azimuth and elevation)

## Typical outputs

- Received power estimate
- Time-of-flight estimate
- Broadened pulse duration
- Waveform peak and timing information
- A simple Cartesian point cloud

## Run it from the command line

```bash
source .venv/bin/activate
python notebooks/06_lidar_ranging/run_lidar.py
```

## Explore it interactively in a notebook

Open the notebook at [notebooks/06_lidar_ranging/lidar_tutorial.ipynb](https://github.com/vinculum3141-ship-it/optical-scattering-sensor-simulation/blob/main/notebooks/06_lidar_ranging/lidar_tutorial.ipynb) to explore the workflow interactively.

## Why this use case matters

This workflow is useful for LiDAR system design, ranging studies, and
point-cloud generation experiments where the geometry and timing model are
more important than a full physical laser scanner.
