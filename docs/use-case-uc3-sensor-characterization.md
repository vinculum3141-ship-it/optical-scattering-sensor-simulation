# Use Case 3 — Sensor Performance Characterization

This use case demonstrates how the framework can model a detector
characterization workflow, including flat-field sweeps and basic sensor
performance analysis.

## Workflow

1. Generate a sequence of flat-field illumination levels
2. Propagate those signals through the optics and detector model
3. Analyze the resulting images with PTC, dynamic range, and linearity
   metrics

## Typical inputs

- Illumination levels for the sweep
- Exposure time and detector gain
- Read noise and image size

## Typical outputs

- Gain and read-noise estimates from the PTC analysis
- Dynamic range in decibels
- Linearity deviation metrics

## Run it from the command line

```bash
source .venv/bin/activate
python examples/run_uc3_sensor_characterization.py --levels 0.05 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0
```

## Why this use case matters

This workflow is useful for camera designers, quality engineers, and
simulation teams who want to understand how detector response changes with
illumination, noise, and exposure settings.
