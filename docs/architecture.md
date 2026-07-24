# Software Architecture

> **Target audience:** Software engineers, R&D developers, contributors.

## Design Philosophy

The framework adopts a **layered pipeline architecture** where each stage
of the physical simulation is a self-contained package with a well-defined
data contract. The layers do not import from each other — they communicate
through simple data containers (`LightField`, `Surface`, `ScatteredField`,
`SensorField`, `DigitalImage`).

This design provides:

- **Independent replaceability** — swap any scattering model, detector
  model, or source type without touching other layers.
- **Testability** — each layer can be tested in isolation with synthetic
  inputs.
- **Extensibility** — adding a new surface generator, noise model, or
  analysis module does not require modifying existing code.

## Package Dependency Graph

```
illumination  (LightField)
      |
surface       (Surface)
      |
scattering    (ScatteredField) — depends on illumination + surface
      |
optics        (SensorField)    — depends on scattering
      |
detector      (DigitalImage)   — depends on optics
      |
analysis      (AnalysisReport) — depends on detector
```

The dependency is strictly **forward**: each layer consumes output from
the previous layer. No layer depends on a later one.

## Data Contracts (the "Glue")

Each layer communicates via a dataclass container:

| Container | Produced by | Consumed by | Key fields |
|---|---|---|---|
| `LightField` | `LightSource.generate_light_field()` | `ScatteringModel.evaluate()` | `intensity`, `direction`, `wavelength`, `polarization`, `phase` |
| `Surface` | `GeometryAnalyzer.analyze()` or surface generators | `ScatteringModel.evaluate()` | `height`, `normals`, `curvature`, `slope_x`, `slope_y`, `roughness`, `material` |
| `ScatteredField` | `ScatteringModel.evaluate()` | `OpticalPropagator.propagate()` | `radiance`, `outgoing_direction`, `polarization` |
| `SensorField` | `OpticalPropagator.propagate()` | `CMOSDetector.capture()` | `irradiance`, `wavelength`, `polarization`, `optical_path_length` |
| `DigitalImage` | `CMOSDetector.capture()` | `AnalysisModule.analyze()` | `pixels`, `metadata` |
| `AnalysisReport` | `ImageAnalyzer.analyze()` | — | `histogram`, `measurements` |

## Core Design Patterns

### 1. Strategy Pattern (Behavioural)

Used extensively for pluggable algorithms:

- **Beam profiles** — `UniformBeamProfile`, `GaussianBeamProfile`,
  `TopHatBeamProfile` all implement the same `BeamProfile.evaluate()`
  interface. The source holds a reference to one and delegates intensity
  computation to it.

- **Scattering models** — `LambertianScattering` implements the
  `ScatteringModel.evaluate()` interface. Adding a `PhongScattering` or
  `OrenNayarScattering` means subclassing `ScatteringModel` and
  implementing one method.

- **Noise models** — custom noise stages subclass `DetectorNoiseModel`
  and implement `apply(electrons)`. They are passed to the detector as
  a list.

- **Analysis modules** — `HistogramAnalyzer` implements `AnalysisModule.
  analyze()`. Multiple modules can be composed via `ImageAnalyzer`.

### 2. Template Method Pattern

`SurfaceGenerator` defines the skeleton algorithm (generate a height map,
then analyse it into a `Surface`). Subclasses override only the
`generate(shape)` method. The `create_surface()` and `__call__()` methods
handle the common pipeline.

### 3. Data Container + Factory

Surface generators like `RoughSurface` serve dual roles:

- **Data container** — they inherit from `Surface` and hold the computed
  geometry directly as attributes.
- **Factory** — they also inherit from `SurfaceGenerator`, so you can
  call them to produce a `Surface`.

This means a `RoughSurface` object *is* a surface, not a surface builder.
The constructor generates the height map and analyses it in one step.

### 4. Immutable / Frozen Configuration

Configuration objects use `@dataclass(frozen=True)` where the state should
not change after construction:

- `PolarizationState` — frozen, validated on construction.
- `SpectralDistribution` subclasses — frozen, immutable wavelength/range/
  temperature parameters.

Mutable objects (`LightSource`, `CMOSDetector`) use regular `@dataclass`
with `__post_init__` for normalisation.

## Data Flow Through the Pipeline

```
User specifies:      LightSource, SurfaceGenerator, ScatteringModel,
                     OpticalSystem, PSFModel, DetectorConfig, AnalysisModules

Step 1: source.generate_light_field(shape, spacing) → LightField
Step 2: generator(shape, material) → Surface
Step 3: model.evaluate(lightfield, surface, view) → ScatteredField
Step 4: propagator.propagate(scattered_field, optical_system) → SensorField
Step 5: detector.capture(sensor_field) → DigitalImage
Step 6: analyzer.analyze(image) → AnalysisReport
```

Each step is optional — you can create a `LightField` by hand (its
dataclass constructor), skip optics, or feed an arbitrary irradiance
array directly to the detector.

## Pipeline Orchestrator

`pipeline.py` at the repository root provides a `SimulationPipeline`
class that wires the six layers together in a single call:

```python
from pipeline import SimulationPipeline

pipeline = SimulationPipeline(
    source=laser,
    surface=RoughSurface,
    scattering=LambertianScattering(albedo=0.7),
    optics=OpticalSystem(),
    propagator=OpticalPropagator(GaussianPSF(sigma=1.0)),
    detector=CMOSDetector(),
    analysers=[HistogramAnalyzer()],
    surface_material=Material("silicon"),
)
result = pipeline.run(shape=(64, 64), spacing=0.5)
# result.light_field, result.surface, result.scattered_field,
# result.sensor_field, result.digital_image, result.report
```

Every component is optional — set any to `None` to skip that stage.
The surface parameter accepts either a Surface instance or a callable
generator (which is called with `(shape, material)`).

## Shared Utilities

`utils/` provides shared helpers that were previously duplicated:

- `utils.visualize.heatmap()` — terminal block-character heatmap
  (replaces 4 separate implementations in LightField, DigitalImage,
  explore.py, and playground.py).

## Package Organisation Conventions

Every package follows the same layout:

```
package/
    __init__.py       — re-exports public API, package docstring
    base.py           — base classes, core data structures
    <model>.py        — concrete implementations
```

For example, `illumination/` has:

- `__init__.py` — re-exports `Laser`, `LED`, etc.
- `source.py` — `LightSource` base dataclass
- `laser.py`, `led.py`, `sunlight.py`, `broadband.py` — concrete sources
- `profiles.py` — beam profile strategies
- `spectrum.py` — spectral distribution models
- `polarization.py` — `PolarizationState`
- `lightfield.py` — `LightField` container

## SI Units Convention

All physical quantities use SI units exclusively:

| Quantity | Unit | Symbol |
|---|---|---|
| Wavelength | metre | m |
| Power | watt | W |
| Intensity / Irradiance | watt per square metre | W/m^2 |
| Radiance | watt per square metre per steradian | W/(m^2 sr) |
| Time | second | s |
| Length (height, focal length, aperture) | metre | m |
| Angle | radian | rad |
| Temperature | kelvin | K |
| Electron count | dimensionless | e^- |
| Digital count | dimensionless | ADU |

## Comparison with Alternative Approaches

| Approach | This framework | Pros | Cons |
|---|---|---|---|
| Grid-based | 2D regular grid (pixel array) | Simple, fast, matrix-friendly | No curved surfaces, no global illumination |
| Ray tracing | No (future option) | Handles complex geometry | Slower, harder to parallelise |
| Analytical BRDF | Lambertian only | Simple, physically based | No specular, no subsurface scattering |
| PSF model | Gaussian convolution | Simple, fast, energy-conserving | No aberrations, no diffraction |
