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

## HistogramAnalyzer

The only built-in module. For each unique pixel value in the image,
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
from analysis import HistogramAnalyzer

analyzer = HistogramAnalyzer()
report = analyzer.analyze(image)

report.histogram                    # 1D ndarray
report.measurements["mean_intensity"]  # float
```

### ImageAnalyzer

```python
from analysis import ImageAnalyzer, HistogramAnalyzer

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

## Complete Example

```python
from analysis import HistogramAnalyzer, ImageAnalyzer
from detector import DigitalImage
import numpy as np

# Create a synthetic image
pixels = np.array(
    [[0, 1, 2],
     [3, 4, 5]], dtype=np.uint16
)
image = DigitalImage(pixels=pixels, metadata={"bit_depth": 8})

# Analyse
analyzer = ImageAnalyzer(modules=[HistogramAnalyzer()])
report = analyzer.analyze(image)

print(f"Mean intensity:  {report.measurements['mean_intensity']:.1f}")
print(f"Max intensity:   {report.measurements['max_intensity']}")
print(f"Histogram bins:  {len(report.histogram)}")
print(f"Histogram:       {report.histogram}")
```

## Creating a Custom Analysis Module

```python
from analysis import AnalysisModule, AnalysisReport

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
