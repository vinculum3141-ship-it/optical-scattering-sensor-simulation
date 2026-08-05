# Testing & Verification Strategy

> **Target audience:** Software engineers, QA engineers, contributors.

## Overview

The framework employs a two-tier testing strategy:

- **Unit / integration tests (pytest)** — 352 tests across all seven
  layers plus pipeline, utilities, and seven use-case integration
  suites. Covers core functionality, edge cases, all models, and
  end-to-end workflows. Fast, run on every change.
- **Acceptance tests (Robot Framework)** — 96 tests across 16 files,
  covering realistic usage scenarios. Documents expected behaviour
  in natural-language form.

## Test Structure

```
tests/
├── Core layer tests
│   ├── test_illumination.py                 # pytest — 35 tests
│   ├── test_surface.py                      # pytest — 4 tests
│   ├── test_surface_new.py                  # pytest — 35 tests
│   ├── test_scattering.py                   # pytest — 11 tests
│   ├── test_scattering_new.py               # pytest — 6 tests
│   ├── test_optics.py                       # pytest — 1 test
│   ├── test_optics_new.py                   # pytest — 34 tests
│   ├── test_detector.py                     # pytest — 1 test
│   ├── test_detector_new.py                 # pytest — 19 tests
│   ├── test_analysis.py                     # pytest — 1 test
│   ├── test_analysis_new.py                 # pytest — 39 tests
│   ├── test_pipeline.py                     # pytest — 5 tests
│   └── test_utils.py                        # pytest — 4 tests
├── Use-case integration tests
│   ├── test_uc1_integration.py              # pytest — 6 tests
│   ├── test_uc2_example.py                  # pytest — 1 test
│   ├── test_uc2_multispectral.py            # pytest — 24 tests
│   ├── test_uc2_integration.py              # pytest — 5 tests
│   ├── test_uc3_ptc.py                      # pytest — 25 tests
│   ├── test_uc3_integration.py              # pytest — 3 tests
│   ├── test_uc4_example.py                  # pytest — 1 test
│   ├── test_uc5_example.py                  # pytest — 1 test
│   ├── test_uc5_structured_light.py          # pytest — 18 tests
│   ├── test_uc5_integration.py              # pytest — 2 tests
│   ├── test_uc6_example.py                  # pytest — 1 test
│   ├── test_uc6_lidar.py                    # pytest — 17 tests
│   ├── test_uc6_integration.py              # pytest — 5 tests
│   ├── test_uc7_example.py                  # pytest — 1 test
│   ├── test_uc7_asml_capstone_example.py    # pytest — 1 test
│   ├── test_uc7_wafer.py                    # pytest — 22 tests
│   └── test_uc7_integration.py              # pytest — 5 tests
├── Robot Framework test files
│   ├── illumination.robot                   # Robot — 16 tests
│   ├── surface.robot                        # Robot — 10 tests
│   ├── surface_new.robot                    # Robot — 5 tests
│   ├── scattering.robot                     # Robot — 5 tests
│   ├── scattering_new.robot                 # Robot — 5 tests
│   ├── optics_new.robot                     # Robot — 3 tests
│   ├── detector.robot                       # Robot — 6 tests
│   ├── detector_new.robot                   # Robot — 3 tests
│   ├── analysis.robot                       # Robot — 6 tests
│   ├── analysis_new.robot                   # Robot — 5 tests
│   ├── defect_inspection.robot              # Robot — 5 tests (UC1)
│   ├── multispectral_identification.robot    # Robot — 6 tests (UC2)
│   ├── sensor_characterization.robot         # Robot — 8 tests (UC3)
│   ├── structured_light.robot               # Robot — 4 tests (UC5)
│   ├── lidar_ranging.robot                  # Robot — 5 tests (UC6)
│   └── wafer_inspection.robot               # Robot — 4 tests (UC7)
├── Robot keyword libraries
│   ├── IlluminationLibrary.py
│   ├── SurfaceLibrary.py
│   ├── ScatteringLibrary.py
│   ├── OpticsLibrary.py
│   ├── DetectorLibrary.py
│   ├── AnalysisLibrary.py
│   ├── DefectInspectionLibrary.py
│   ├── MultiSpectralLibrary.py
│   ├── SensorCharLibrary.py
│   ├── StructuredLightLibrary.py
│   ├── LiDARLibrary.py
│   └── WaferLibrary.py
```

## Running Tests

### Pytest (Unit Tests)

```bash
# Run all unit tests
python -m pytest -q

# Run tests for a specific layer
python -m pytest tests/test_illumination.py -v

# Run with coverage
pip install pytest-cov
python -m pytest --cov=illumination --cov=surface --cov=scattering \
    --cov=optics --cov=detector --cov=analysis
```

### Robot Framework (Acceptance Tests)

```bash
# Requires: pip install robotframework

# Run all acceptance tests
python -m robot tests/

# Run tests for a specific layer
python -m robot tests/illumination.robot

# Generate HTML reports
python -m robot --outputdir robot_output tests/
# → robot_output/report.html, robot_output/log.html
```

## Unit Test Philosophy

Each unit test verifies a single, specific behaviour:

| Layer / Use Case | Tests | What it verifies |
|---|---|---|---|
| Illumination | 35 tests | Laser/LED/Sunlight/BroadbandLamp defaults, light field generation, direction normalisation, spectral models, wavefront (planar/spherical), incidence angle, FlatFieldSource, MultiSpectralSource, FilterWheelSource, FringeProjector, ScanningMechanism, TemporalEnvelope, SourceExtent, directional helpers |
| Surface (original) | 4 tests | Flat/rough/scratched/particle surface geometry |
| Surface (extended) | 35 tests | Sinusoidal periodicity, anisotropic roughness, imported surfaces, phase screen, visualisation, defect generators (Dent/Pit/Crack/Stain), WaferSurface, MisalignedSurface, ThinFilmStack, coordinate transforms, geometry analysis |
| Scattering (original) | 11 tests | Lambertian (4) + scattering base + Cook-Torrance (6: shape, nonnegativity, roughness monotonicity, Fresnel response, grazing limit, non-square grid) |
| Scattering (extended) | 14 tests | Phong (diffuse/specular/grazing), Oren-Nayar (return/shape/roughness→Lambertian limit), Beckmann (shape/roughness monotonicity/Fresnel/grazing), GGX (shape/roughness monotonicity/Fresnel/grazing), Rayleigh, Mie |
| Optics (original) | 1 test | Propagation output shapes |
| Optics (extended) | 24 tests | Airy PSF normalisation, central peak, symmetry, odd-size auto, invalid size; J1 accuracy; ZernikePSF (coefficients, wavefront, Noll indexing, defocus/astigmatism broadening, matches Airy when aberration-free, pixel-size diffraction scaling); GaussianPSF; optical throughput (NA²); magnification resampling; propagator with diffraction PSF models |
| Detector (original) | 1 test | Capture returns correctly-shaped DigitalImage |
| Detector (extended) | 19 tests | Fixed-pattern noise, hot pixels, column defect, PRNU, dead pixels, multiple noise chaining, speckle (smooth/coherent/incoherent), capture with surface, blooming (no spill / neighbour spill / integrated); CFAConfig/CFADetector (Bayer, demosaic); SPADDetector (dead time, PDE, jitter, dark counts) |
| Analysis (original) | 1 test | Histogram shape and measurements |
| Analysis (extended) | 49 tests | Contrast (RMS/Michelson/Weber/uniform/high-contrast), saturation detection, ImageAnalyzer; FocusAnalyzer (Laplacian/Tenengrad/Brenner); SNRAnalyzer (single/pair); MTFAnalyzer (sinusoidal); FFTAnalyzer (radial profile); EdgeDetectionAnalyzer; ErrorMapAnalyzer; IntensityProfileAnalyzer; SpeckleRoughnessEstimator; DefectAnalyzer (blob/scratch/pass-fail); PTCAnalyzer; DynamicRangeAnalyzer; LinearityTestAnalyzer; SpectralAnalyzer (SAM/ratios); GoniometricSweep; BRDFFitter; ScatteringSweep (multi-parameter); TemplateMatcher; RegistrationAnalyzer; SPCAnalyzer; PhaseExtractor; PhaseUnwrapper; HeightReconstructor; SurfaceComparator; LiDARRangeEquation; TimeOfFlightPropagator; WaveformAnalyzer |
| Pipeline | 5 tests | Full pipeline stages, partial illumination/detector only, pipeline description, surface generator integration |
| Utilities | 4 tests | Heatmap rendering, dimensions, uniform input, downsampling |
| UC1 (Defect) | 6 tests | End-to-end defect inspection: bright-field/dark-field/ring-light, dent/pit/crack/stain surfaces, pass/fail decision |
| UC2 (Multi-spectral) | 29 tests | Multi-channel light fields, filter wheel sweeps, CFA capture/demosaic, spectral analysis (SAM, band ratios), material classification |
| UC3 (Sensor char) | 28 tests | PTC (gain, read noise, FWC), dynamic range, linearity error, stepped exposure sweeps, test chart generation (Siemens star, slanted edge, greyscale wedge) |
| UC5 (Structured light) | 20 tests | Fringe projection with N phase shifts, phase extraction, flood-fill unwrapping, height reconstruction, surface comparison |
| UC6 (LiDAR) | 22 tests | LiDAR range equation, ToF propagation, SPAD detection, waveform analysis (peak/CFD), point cloud generation, scanning patterns |
| UC7 (Wafer) | 27 tests | Wafer surface (fiducial marks, die grid), affine misalignment, template matching (NCC), registration (FFT cross-correlation), SPC (Cpk, trend) |

### Statistical Bounds for Stochastic Tests

The detector tests use **statistical bounds** rather than exact values
because shot noise and dark current are Poisson-distributed:

- `pixel_range_should_be_within` checks that pixel values fall within
  the valid digital range [0, 2^bit_depth - 1].
- No test asserts exact pixel values for stochastic computations.

## Robot Framework Acceptance Tests

### What Is Robot Framework?

[Robot Framework](https://robotframework.org/) is an open-source,
keyword-driven test automation framework. Tests are written in a
tabular, natural-language format (`.robot` files) and executed by
the `robot` runner. The actual test logic is implemented in Python
keyword libraries — Robot itself is language-agnostic and simply
orchestrates keyword calls.

### Architecture

```
.robot file (test specification)
    │
    ▼
Robot Framework runner (robot)
    │  parses keyword tables, resolves arguments, calls library methods
    │
    ▼
<Layer>Library.py (Python)
    │  one class per layer, methods become Robot keywords
    │
    ▼
Framework API (Laser, RoughSurface, CMOSDetector, ...)
    │
    ▼
numpy, Python standard library
```

For this project specifically:

```
tests/illumination.robot         ← plain-text test cases
    │  "Create Laser    wavelength=532e-9    power=5e-3"
    │  "Polarization Should Be    unpolarized"
    ▼
tests/IlluminationLibrary.py    ← Python keyword implementations
    │  def create_laser(self, wavelength, power): ...
    │  def polarization_should_be(self, expected_kind): ...
    ▼
illumination.Laser              ← the actual framework code being tested
```

### Why Robot Framework for This Project?

| Concern | What Robot Framework provides |
|---|---|
| **Domain readability** | Physics/engineering stakeholders can read test cases without knowing Python. A test like `Radiance Should Be All Close To 0.7` is self-documenting. |
| **Separation of concerns** | Test *specification* lives in `.robot` files; test *implementation* lives in Python libraries. Either can change independently. |
| **Reporting** | Every run produces `report.html` and `log.html` — rich, interactive documents showing exactly which keywords passed or failed, with argument values and timings. |
| **Layered testing** | Each simulation layer has its own library and test suite, mirroring the code architecture. A QA engineer can inspect just the detector tests without touching scattering. |
| **Data-driven capability** | Robot supports data-driven tests (same test logic, different parameter sets via `[Template]`), useful for verifying a model across multiple input configurations. |
| **CI-friendly** | Exits with non-zero code on failure, produces JUnit-compatible XML output, and integrates with Jenkins, GitLab CI, GitHub Actions, etc. |

### How Keywords Work

Every public method on a Python library class becomes a Robot keyword.
Arguments in the `.robot` file are passed as positional or named
parameters. The library stores state in instance variables.

```
.robot file call:
    Create Laser    wavelength=532e-9    power=5e-3

maps to Python:
    def create_laser(self, wavelength, power):
        self._source = Laser(wavelength=float(wavelength), power=float(power))
```

Robot handles argument parsing — `wavelength=532e-9` is received as
the string `"532e-9"`, which the library converts to float. Assertion
keywords raise `AssertionError` to signal test failure:

```
.robot file call:
    Polarization Should Be    unpolarized

maps to Python:
    def polarization_should_be(self, expected_kind):
        if self._source.polarization.kind != expected_kind:
            raise AssertionError(
                f"Expected polarization {expected_kind}, got {kind}"
            )
```

### Full Library-to-Test Walkthrough

**Step 1 — Define a Python library**
(`tests/IlluminationLibrary.py`):

```python
class IlluminationLibrary:
    def create_laser(self, wavelength, power):
        self._source = Laser(wavelength=float(wavelength), power=float(power))
        return self._source

    def generate_light_field(self, height, width, spacing):
        shape = (int(height), int(width))
        self._field = self._source.generate_light_field(shape=shape, spacing=float(spacing))
        return self._field

    def field_should_have_shape(self, expected_shape_str):
        expected = tuple(int(x) for x in expected_shape_str.split(","))
        if self._field.intensity.shape != expected:
            raise AssertionError(f"Shape {self._field.intensity.shape} != {expected}")
```

**Step 2 — Write the Robot test case**
(`tests/illumination.robot`):

```robot
*** Settings ***
Library    IlluminationLibrary.py

*** Test Cases ***
Generate Light Field Shape
    [Documentation]    Source.generate_light_field() returns the correct
    ...                grid dimensions.
    Create Laser        wavelength=532e-9    power=5e-3
    Generate Light Field    height=16    width=16    spacing=0.5
    Field Should Have Shape    16,16
```

**Step 3 — Execute**:

```bash
python -m robot tests/illumination.robot
```

Robot prints a console summary and writes `report.html` + `log.html`
to the output directory.

### Test Report Output

After running `python -m robot tests/`, Robot produces:

| File | What it contains |
|---|---|
| `report.html` | High-level pass/fail summary per test suite and per test case. Shareable with non-technical stakeholders. |
| `log.html` | Detailed, expandable log of every keyword call, its arguments, return values, and duration. Invaluable for debugging. |
| `output.xml` | Machine-readable XML output for CI tooling or custom post-processing. |

### Library Design Patterns

**1. State-per-object.** Each library creates and stores the object
under test:

```python
self._source    → LightSource instance
self._field     → LightField instance
self._surface   → Surface instance
self._result    → ScatteredField instance
self._image     → DigitalImage instance
self._report    → AnalysisReport instance
```

**2. Chaining.** A test case chains keywords — setup, action, assertion:

```robot
Create Laser    wavelength=532e-9    power=5e-3
Generate Light Field    height=8    width=8    spacing=1.0
Field Should Have Shape    8,8
```

**3. Assertion naming convention.** Assertion keywords use `Should Be`
to read naturally in the Robot syntax:

| Style | Example | Read as |
|---|---|---|
| Positive | `Roughness Should Be 0.0` | "roughness should be 0.0" |
| Comparative | `Roughness Should Be Greater Than 0.0` | "roughness should be greater than 0.0" |
| Existence | `Histogram Should Exist` | "histogram should exist" |
| Range | `Pixel Range Should Be Within 0 4095` | "pixel range should be within 0 to 4095" |

### Keyword Reference by Layer

| Library | Sample Keywords | Description |
|---|---|---|
| IlluminationLibrary | `Create Laser`, `Create LED`, `Generate Light Field`, `Field Should Have Shape`, `Direction Vector Should Be Normalized` | Core source types, light field generation, field validation |
| SurfaceLibrary | `Create Flat Surface`, `Create Rough Surface`, `Create Dent Surface`, `Height Should Be All Close To`, `Roughness Should Be Greater Than` | Surface generators (flat, rough, scratched, particle, dent, pit, crack, stain), geometry assertions |
| ScatteringLibrary | `Create Lambertian Model`, `Evaluate Scattering`, `Radiance Should Be All Close To`, `Radiance Should Be Non Negative` | Lambertian, Phong, Oren-Nayar, Cook-Torrance, Beckmann, GGX, Rayleigh, Mie models |
| OpticsLibrary | `Create Optical System`, `Propagate Field`, `Sensor Field Should Have Shape` | Optical system config, propagation, sensor field validation |
| DetectorLibrary | `Create Default Detector`, `Capture With Detector`, `Pixel Range Should Be Within`, `Metadata Should Contain Key` | CMOSDetector pipeline, noise model chaining, digital image validation |
| AnalysisLibrary | `Create Histogram Analyzer`, `Analyze Known Image`, `Histogram Should Exist`, `Measurement Should Exist` | Histogram, contrast, saturation, ImageAnalyzer orchestration |
| DefectInspectionLibrary | `Create Bright Field Source`, `Create Dent Surface`, `Detect Defects`, `Pass Fail Should Be` | UC1 directional lighting, defect generators, DefectAnalyzer, pass/fail |
| MultiSpectralLibrary | `Create Multi Spectral Source`, `Add Channel`, `Capture Channels`, `Spectral Angle Should Be` | UC2 filter wheel sweeps, multi-channel capture, SAM classification |
| SensorCharLibrary | `Create Flat Field Source`, `Step Exposure`, `Compute PTC`, `Dynamic Range Should Be` | UC3 flat-field sweeps, PTC/DR/linearity analysis, test charts |
| StructuredLightLibrary | `Create Fringe Projector`, `Capture Phase Shifts`, `Extract Phase`, `Unwrap Phase`, `Reconstruct Height` | UC5 fringe projection, N-step phase extraction, unwrapping, height map |
| LiDARLibrary | `Create Laser Pulse`, `Set Target Range`, `Compute Received Power`, `Detect SPAD`, `Generate Point Cloud` | UC6 pulsed laser, ToF, SPAD detection, waveform analysis, point cloud |
| WaferLibrary | `Create Wafer Surface`, `Apply Misalignment`, `Match Template`, `Compute Registration`, `Cpk Should Be` | UC7 wafer generators, template matching, registration, SPC |

### Comparing Robot Tests with Pytest

| Aspect | pytest | Robot Framework |
|---|---|---|
| **Language** | Python | Table-based `.robot` syntax |
| **Readable by non-coders** | No (requires Python literacy) | Yes (natural-language keywords) |
| **Test granularity** | Single function per behaviour | Multiple keywords per test case |
| **Reporting** | Terminal output + optional plugins | Built-in HTML reports with keyword-level logs |
| **Setup/teardown** | Fixtures | `[Setup]`, `[Teardown]`, suite-level settings |
| **Data-driven** | `@pytest.mark.parametrize` | `[Template]` keyword |
| **Takeaway** | Fast, precise developer tests | Stakeholder-readable acceptance tests |

### Why Robot Framework Is a Good Fit Here

1. **Multi-layer domain.** Optical scattering simulation spans
   illumination, surface geometry, scattering physics, optics,
   detector electronics, and analysis. Each layer has its own
   vocabulary and concerns. Robot libraries isolate these perfectly.

2. **Living documentation.** A Robot test case like:

   ```robot
   Lambertian Normal Incidence Gives Albedo
       [Documentation]    When light propagates toward the surface (-z)
       ...                and the normal points up (+z), the dot product
       ...                of to-light (+z) with normal (+z) = 1,
       ...                so radiance = albedo.
       ...
       Radiance Should Be All Close To    0.7
   ```

   serves as both a test and executable specification. It documents
   the expected physics in plain English.

3. **QA engineer independence.** A QA engineer can write new test
   cases by composing existing keywords in a `.robot` file without
   writing any Python. If a new keyword is needed, they add a method
   to the library — a simple, well-scoped task.

4. **Traceability.** Every test run produces a timestamped,
   self-contained HTML report. When a stakeholder asks "did we verify
   that the scattering model works for grazing angles?", the answer
   is a link to the report showing the passing test case.

## Verification Strategy

### What We Verify

1. **Constructor correctness** — default values, parameter validation,
   type conversions.
2. **Shape contracts** — every data container preserves the expected
   (H, W) or (H, W, 3) shapes.
3. **Physical plausibility** — radiance is non-negative, roughness is
   positive for non-flat surfaces, digital values are in range.
4. **Edge cases** — grazing-angle scattering (zero), back-surface
   illumination (zero), flat surfaces (all zeros), non-square grids.
5. **Interface enforcement** — abstract base classes raise
   `NotImplementedError`.

### What We Don't Verify

- **Exact numerical agreement with physical experiments** — this is a
  simulation framework, not a validated instrument model. Numerical
  values are self-consistent but not calibrated to specific hardware.
- **Performance or memory bounds** — not measured in CI.
- **Multi-threading / concurrency safety** — not currently a concern.

### Adding a New Test

For a **unit test**:

1. Create a function `test_<feature>()` in the appropriate
   `tests/test_<layer>.py` file.
2. Construct the test inputs directly (no fixtures needed).
3. Assert the expected behaviour with `assert` statements.
4. Run with `python -m pytest tests/test_<layer>.py -v`.

For an **acceptance test**:

1. Add a keyword method to the appropriate `<Layer>Library.py`.
2. Add a test case to the corresponding `.robot` file.
3. Run with `python -m robot tests/<layer>.robot`.

### Continuous Integration

The tests are designed for local execution. CI integration would:

1. `python -m pytest -q` — gate on all unit tests passing.
2. `python -m robot tests/` — gate on all acceptance tests passing.
3. (Optional) `python playground.py --demo` — verify the pipeline runs
   without error.
