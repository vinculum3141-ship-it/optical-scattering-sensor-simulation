# Detector Layer

> **Target audience:** Both — sensor physics for scientists, pipeline
> architecture and noise models for engineers.

## Overview

The detector layer converts the optical sensor field (irradiance) into
a digital image (ADU counts) by modelling the complete CMOS imaging
chain: photon conversion, quantum efficiency, shot noise, dark current,
read noise, saturation, and ADC quantisation.

**File location:** `detector/`

## Pipeline Steps

```
Irradiance (W/m²)
    ↓ Step 1:  E = hc/λ → photon count per pixel
Photons
    ↓ Step 2:  × quantum efficiency
Photoelectrons
    ↓ Step 3:  Poisson noise (shot noise + dark current)
Noisy electrons
    ↓ Step 4:  Gaussian read noise
Noisy electrons
    ↓ Step 5:  Custom noise models (optional)
Noisy electrons
    ↓ Step 6:  Clip to full-well capacity
Clipped electrons
    ↓ Step 7:  ÷ gain, round, clip to [0, 2^bit_depth - 1]
Digital counts (ADU)
```

### Step 1: Photon Conversion

    N_photons = (E × A_pixel × t_exposure) / (h × c / λ)

where h = 6.62607015×10⁻³⁴ J·s, c = 2.99792458×10⁸ m/s.

### Step 2: Quantum Efficiency

    N_electrons = N_photons × QE

QE is a scalar in [0, 1] (default 0.9).

### Step 3: Shot Noise + Dark Current

- **Shot noise**: Poisson-distributed with mean = N_electrons.
  Variance equals the mean — the fundamental photon-counting noise.
- **Dark current**: Poisson-distributed with mean = I_dark × t_exposure.
  Added to the shot-noise electrons.

### Step 4: Read Noise

Gaussian noise with zero mean and σ = read_noise_sigma (electrons):

    N_read ~ N(0, σ_read)

### Step 5: Custom Noise (Optional)

User-supplied `DetectorNoiseModel` instances are applied in order.
Each receives and returns the electron array.

### Step 6: Full-Well Saturation

    N_clipped = clip(N, 0, FWC)

Any pixel exceeding the full-well capacity is saturated at FWC.

### Step 7: ADC Quantisation

    DN = round(N_clipped / gain)
    DN = clip(DN, 0, 2^bit_depth - 1)

Where gain is in electrons per ADU.

## Key API

### CMOSDetector

```python
detector = CMOSDetector(
    exposure_time=0.01,          # seconds
    quantum_efficiency=0.9,      # e⁻ per photon
    dark_current=5.0,            # e⁻ per second
    read_noise_sigma=2.0,        # e⁻ (std dev)
    full_well_capacity=80000.0,  # e⁻
    gain=2.0,                    # e⁻ per ADU
    bit_depth=12,                # bits (→ 4096 levels)
    pixel_area=25e-12,           # m² (5 µm × 5 µm)
    noise_models=None,           # list of DetectorNoiseModel
)
```

### Capture

```python
image = detector.capture(sensor_field)

image.pixels       # (H, W) uint16 ndarray — ADU counts
image.metadata     # dict of capture parameters
image.visualize()  # terminal heatmap
```

### Pipeline Description

```python
print(detector.pipeline_describe())
# CMOS detector pipeline:
#   Step 1  Irradiance → photons    (E = hc/λ, ...)
#   Step 2  Quantum efficiency       (0.9 e⁻/photon)
#   Step 3  Shot noise (Poisson)     + dark current (...)
#   Step 4  Read noise (Gaussian)    σ = 2.0 e⁻
#   Step 5  Custom noise:       (none)
#   Step 6  Full-well clip         ≤ 80000.0 e⁻
#   Step 7  ADC quantisation       gain=2.0 e⁻/ADU, 12-bit
```

### DigitalImage

```python
image.pixels              # (H, W) uint16
image.metadata            # dict with bit_depth, exposure_time, etc.
print(image.visualize(max_width=72, color=True))  # terminal heatmap
```

## Implementation Notes

### Stochastic Noise

Shot noise, dark current, and read noise are all stochastic — outputs
vary between runs. Tests use **statistical bounds** rather than exact
values.

### Custom Noise Models

```python
from detector import DetectorNoiseModel

class FixedPatternNoise(DetectorNoiseModel):
    def __init__(self, pattern):
        self.pattern = pattern

    def apply(self, electrons):
        return electrons * self.pattern   # example: gain non-uniformity

detector = CMOSDetector(noise_models=[FixedPatternNoise(...)])
```

### Data Flow

The `capture()` method accepts any object with `.irradiance` and
`.wavelength` attributes (duck typing). This allows testing with
synthetic data without constructing a full `SensorField`.

## Complete Example

```python
from detector import CMOSDetector
from optics import SensorField
import numpy as np

sensor_field = SensorField(
    irradiance=np.ones((16, 16)) * 1e3,   # uniform 1 kW/m²
    wavelength=532e-9,
)

detector = CMOSDetector(
    exposure_time=1e-5,
    bit_depth=12,
    gain=1.0,
)

image = detector.capture(sensor_field)
print(f"Image shape: {image.pixels.shape}")
print(f"Pixel range: {image.pixels.min()} — {image.pixels.max()} ADU")
print(f"Mean:        {image.pixels.mean():.0f} ADU")
print(image.visualize())
```

## Noise Model Reference

| Noise | Distribution | Parameter | Typical Value |
|---|---|---|---|
| Shot noise | Poisson(μ=N_e) | N_e = photoelectrons | √N variance |
| Dark current | Poisson(μ=I_d·t) | I_d = dark current | 5 e⁻/s |
| Read noise | Gaussian(0, σ) | σ = read_noise_sigma | 2 e⁻ |
| Full-well | Deterministic clip | FWC | 80000 e⁻ |
| ADC | Round + clip | bit_depth | 12-bit |
