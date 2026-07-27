# Analysis Layer

> **Target audience:** Both — statistics and histogram physics for
> scientists, pluggable module architecture for engineers.

## Overview

The analysis layer extracts quantitative measurements from captured
digital images. It uses a pluggable module pattern — each
`AnalysisModule` computes a specific metric, and `ImageAnalyzer`
orchestrates multiple modules and merges their results into a single
`AnalysisReport`.

**File location:** `analysis/`

## Architecture

```
DigitalImage
    │
    ▼
ImageAnalyzer
    │
    ├── HistogramAnalyzer  →  histogram, mean/max/min
    └── (custom modules)   →  additional measurements
    │
    ▼
AnalysisReport
    ├── histogram:  ndarray or None
    └── measurements: dict (e.g. {"mean_intensity": 2048.0})
```

## Built-in Analysis Modules

Modules are organised by function:

### Quality Assessment

| Module | Class | Key Measurements | Use Case |
|---|---|---|---|
| Histogram | `HistogramAnalyzer` | mean_intensity, max_intensity, min_intensity | Basic statistics |
| Contrast | `ContrastAnalyzer` | rms_contrast, michelson_contrast, weber_contrast | Image quality, pattern detection |
| Saturation | `SaturationAnalyzer` | saturated_pixels, saturation_fraction | Overexposure detection |
| Focus | `FocusAnalyzer` | laplacian_variance, tenengrad, brenner | Auto-focus, sharpness metric |
| SNR | `SNRAnalyzer` | snr_db, signal_mean, noise_std | Sensor characterisation (UC3) |

### Optical Characterisation

| Module | Class | Key Measurements | Use Case |
|---|---|---|---|
| MTF | `MTFAnalyzer` | mtf_curve, mtf50, mtf50p | Resolution testing (UC3) |
| FFT | `FFTAnalyzer` | peak_spatial_frequency, radial_profile, dc_fraction | Frequency analysis (UC4/UC5) |
| Edge Detection | `EdgeDetectionAnalyzer` | edge_count, edge_density, mean_edge_strength | Feature location (UC7) |

### Metrology — Defect & Surface

| Module | Class | Key Measurements | Use Case |
|---|---|---|---|
| Defect Detection | `DefectAnalyzer` | defect_count, max_defect_area, pass_fail | Surface AOI (UC1) |
| Roughness from Speckle | `SpeckleRoughnessEstimator` | speckle_contrast, estimated_roughness | Roughness characterisation (UC1) |
| Intensity Profile | `IntensityProfileAnalyzer` | line_cross_section, contrast | Line width, feature size (UC1/UC5) |
| Error Map | `ErrorMapAnalyzer` | rmse, mae, max_error, psnr | Ground-truth comparison (UC5/UC7) |
| Tiled Acquisition | `TiledAcquisition` | tile_positions, stitched_image | Multi-FOV scanning (UC1) |

### Metrology — Sensor Characterisation (UC3)

| Module | Class | Key Measurements | Use Case |
|---|---|---|---|
| Photon Transfer Curve | `PTCAnalyzer` | gain_e_per_adu, read_noise_e, full_well_e | Camera characterisation |
| Dynamic Range | `DynamicRangeAnalyzer` | dynamic_range_db, saturation_level, noise_floor | Sensor performance |
| Linearity | `LinearityTestAnalyzer` | linearity_error_pct, r_squared | Exposure linearity |

### Metrology — Spectral (UC2)

| Module | Class | Key Measurements | Use Case |
|---|---|---|---|
| Spectral Analysis | `SpectralAnalyzer` | band_ratios, sam_map, classification_map | Material identification |

### Metrology — Goniometric (UC4)

| Module | Class | Key Measurements | Use Case |
|---|---|---|---|
| Goniometric Sweep | `GoniometricSweep` | theta_i_array, theta_r_array, brdf_table | Angle-resolved BRDF |
| BRDF Fitting | `BRDFFitter` | fitted_params, r_squared, residual_norm | Model parameter estimation |

### Metrology — Structured Light (UC5)

| Module | Class | Key Measurements | Use Case |
|---|---|---|---|
| Phase Extraction | `PhaseExtractor` | wrapped_phase, modulation | N-step phase shifting |
| Phase Unwrapping | `PhaseUnwrapper` | unwrapped_phase | Spatial flood-fill unwrapping |
| Height Reconstruction | `HeightReconstructor` | height_map | Phase → height triangulation |
| Surface Comparison | `SurfaceComparator` | rms_error, error_map | Reconstructed vs. ground truth |

### Metrology — Registration & SPC (UC7)

| Module | Class | Key Measurements | Use Case |
|---|---|---|---|
| Template Matching | `TemplateMatcher` | match_score, match_location | Normalised cross-correlation |
| Registration | `RegistrationAnalyzer` | dx, dy, rotation, scale | Translation/rotation alignment |
| SPC | `SPCAnalyzer` | cpk, mean_shift, trend_slope | Statistical process control |

### Metrology — LiDAR (UC6)

| Module | Class | Key Measurements | Use Case |
|---|---|---|---|
| LiDAR Range Equation | `LiDARRangeEquation` | received_power_w | Link budget calculation |
| Time-of-Flight | `TimeOfFlightPropagator` | tof_s, pulse_width_s | Pulse delay and broadening |
| Waveform Analysis | `WaveformAnalyzer` | peak_location, peak_amplitude, cfd_location | Pulse detection |
| Point Cloud | `generate_point_cloud()` | xyz, intensity, timestamp | Range data → 3D points |

### HistogramAnalyzer

For each unique pixel value in the image,
it counts how many pixels share that value.

### Output Measurements

| Key | Description |
|---|---|
| `mean_intensity` | Mean pixel value (ADU) |
| `max_intensity` | Maximum pixel value (ADU) |
| `min_intensity` | Minimum pixel value (ADU) |

### Histogram

The histogram is a 1D array where element `i` is the count of pixels
with the `i`-th unique value. The values themselves are obtained via
`numpy.unique()`. This gives the full-resolution histogram — no bin
width approximation.

## Key API

### HistogramAnalyzer

```python
from optical_metrology.analysis import HistogramAnalyzer

analyzer = HistogramAnalyzer()
report = analyzer.analyze(image)

report.histogram                    # 1D ndarray
report.measurements["mean_intensity"]  # float
```

### ImageAnalyzer

```python
from optical_metrology.analysis import ImageAnalyzer, HistogramAnalyzer

analyzer = ImageAnalyzer(modules=[HistogramAnalyzer()])
report = analyzer.analyze(image)

# Merged measurements and histogram from all modules
report.measurements  # combined dict
report.histogram     # last non-None histogram wins
```

### AnalysisReport

```python
@dataclass
class AnalysisReport:
    histogram: np.ndarray | None = None
    measurements: Dict[str, Any] = field(default_factory=dict)
```

## Implementation Notes

### Pluggable Module Pattern

The architecture mirrors scikit-learn's transformer pattern:

1. Define an abstract base (`AnalysisModule`) with a single method
   `analyze(image)`.
2. Implement concrete modules (`HistogramAnalyzer`).
3. Compose them via `ImageAnalyzer`.

This makes it trivial to add new analysis capabilities without modifying
existing code.

### Merging Strategy

`ImageAnalyzer.analyze()`:

- Measurements are merged via `dict.update()` — later modules'
  measurements overwrite earlier ones with the same key.
- The last non-`None` histogram wins.

### Duck Typing

`analyze()` only requires that the input has a `.pixels` attribute
(2D array). This works with `DigitalImage` directly or any
duck-typed equivalent.

### ContrastAnalyzer

Computes three standard contrast metrics:

- **RMS contrast** — σ(I) / μ(I), the coefficient of variation.
- **Michelson contrast** — (I_max - I_min) / (I_max + I_min), for
  periodic patterns.
- **Weber contrast** — (I_max - I_bg) / I_bg, relative to a
  background level (defaults to the image mean).

```python
from optical_metrology.analysis import ContrastAnalyzer

analyzer = ContrastAnalyzer(background=None)
report = analyzer.analyze(image)
print(report.measurements["rms_contrast"])
```

### SaturationAnalyzer

Detects pixels at or near the maximum digital value.

```python
from optical_metrology.analysis import SaturationAnalyzer

analyzer = SaturationAnalyzer(threshold=0.99)  # ≥ 99% of max
report = analyzer.analyze(image)
print(f"Saturated pixels: {report.measurements['saturated_pixels']}")
print(f"Saturation fraction: {report.measurements['saturation_fraction']:.2%}")
```

## Complete Example

```python
from optical_metrology.analysis import (
    ContrastAnalyzer,
    HistogramAnalyzer,
    ImageAnalyzer,
    SaturationAnalyzer,
)
from optical_metrology.detector import DigitalImage
import numpy as np

pixels = np.array(
    [[0, 1, 2],
     [3, 4, 5]], dtype=np.uint16
)
image = DigitalImage(pixels=pixels, metadata={"bit_depth": 8})

# Compose multiple analysis modules
analyzer = ImageAnalyzer(modules=[
    HistogramAnalyzer(),
    ContrastAnalyzer(),
    SaturationAnalyzer(),
])
report = analyzer.analyze(image)

print(report.measurements)
# {
#   "mean_intensity": ..., "max_intensity": ...,
#   "rms_contrast": ..., "saturated_pixels": 0,
#   ...
# }
```

## Creating a Custom Analysis Module

```python
from optical_metrology.analysis import AnalysisModule, AnalysisReport

class EntropyAnalyzer(AnalysisModule):
    def analyze(self, image):
        pixels = image.pixels.astype(float)
        # Normalise to probability distribution
        hist, _ = np.histogram(pixels, bins=256)
        probs = hist / hist.sum()
        probs = probs[probs > 0]
        entropy = -np.sum(probs * np.log2(probs))
        return AnalysisReport(measurements={"entropy": entropy})

analyzer = ImageAnalyzer(modules=[HistogramAnalyzer(), EntropyAnalyzer()])
report = analyzer.analyze(image)
print(report.measurements)
```
