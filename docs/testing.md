# Testing & Verification Strategy

> **Target audience:** Software engineers, QA engineers, contributors.

## Overview

The framework employs a two-tier testing strategy:

- **Unit tests (pytest)** — 55 tests across all six layers, covering
  core functionality, edge cases, and all new models. Fast, run on
  every change.
- **Acceptance tests (Robot Framework)** — 64 tests across all six
  layers, covering realistic usage scenarios. Documents expected
  behaviour in natural-language form.

## Test Structure

```
tests/
├── test_illumination.py    # pytest — 4 tests
├── test_surface.py         # pytest — 4 tests
├── test_scattering.py      # pytest — 5 tests
├── test_optics.py          # pytest — 1 test
├── test_detector.py        # pytest — 1 test
├── test_analysis.py        # pytest — 1 test
├── illumination.robot      # Robot Framework — 16 tests
├── surface.robot           # Robot Framework — 10 tests
├── scattering.robot        # Robot Framework — 5 tests
├── detector.robot          # Robot Framework — 6 tests
├── analysis.robot          # Robot Framework — 6 tests
├── IlluminationLibrary.py  # Robot keyword library
├── SurfaceLibrary.py       # Robot keyword library
├── ScatteringLibrary.py    # Robot keyword library
├── DetectorLibrary.py      # Robot keyword library
└── AnalysisLibrary.py      # Robot keyword library
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

| Layer | Test | What it verifies |
|---|---|---|
| Illumination | `test_laser_defaults_and_spectrum` | Laser constructor defaults and spectral model |
| Illumination | `test_lightfield_generation_uses_beam_profile` | `generate_light_field()` output shapes and values |
| Illumination | `test_source_direction_is_normalized` | Direction vector normalisation |
| Illumination | `test_subclasses_expose_expected_spectral_models` | LED/Sunlight/Lamp spectral attachments |
| Surface | `test_flat_surface_has_zero_height_and_zero_derived_geometry` | Flat surface is all zeros |
| Surface | `test_rough_surface_has_nonzero_roughness_and_shape` | Rough surface has valid geometry |
| Surface | `test_scratched_surface_creates_a_visible_groove` | Scratch creates negative heights |
| Surface | `test_particle_surface_creates_localized_bumps` | Particles produce positive bumps |
| Scattering | `test_lambertian_scattering_returns_scattered_field` | Output types and shapes |
| Scattering | `test_lambertian_radiance_scales_with_albedo` | Proportionality to albedo |
| Scattering | `test_lambertian_normal_incidence_gives_peak_radiance` | Normal incidence → radiance = albedo |
| Scattering | `test_lambertian_grazing_angle_gives_zero_radiance` | Perpendicular → zero |
| Scattering | `test_scattering_model_base_raises_not_implemented` | Abstract base enforces interface |
| Optics | `test_optical_propagator_returns_sensor_field` | Propagation output shapes and attributes |
| Detector | `test_detector_pipeline_creates_digital_image` | Capture returns correctly-shaped DigitalImage |
| Analysis | `test_histogram_analyzer_returns_report` | Histogram shape and measurements |

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

| Library | Keyword | Arguments | Description |
|---|---|---|---|
| IlluminationLibrary | `Create Laser` | wavelength, power | Create a default Laser instance |
| | `Create LED` | peak_wavelength, width, power | Create an LED |
| | `Create Sunlight` | temperature, power | Create a Sunlight source |
| | `Create Custom Source` | wavelength, power, polarization, profile_type | LightSource with specific profile |
| | `Generate Light Field` | height, width, spacing | Generate and store a LightField |
| | `Field Should Have Shape` | expected_shape_str | Assert intensity shape |
| | `Field Direction Should Have Shape` | expected_shape_str | Assert direction shape |
| | `Field Wavelength Should Be` | expected | Assert field wavelength |
| | `Direction Vector Should Be Normalized` | — | Assert all direction vectors are unit length |
| SurfaceLibrary | `Create Flat Surface` | height, width, material_name | Flat surface |
| | `Create Rough Surface` | height, width, sigma, amplitude | Rough surface |
| | `Create Scratched Surface` | height, width, depth, width | Scratched surface |
| | `Create Particle Surface` | height, width, count, amplitude, sigma | Particle surface |
| | `Height Should Be All Close To` | expected | Assert height values |
| | `Roughness Should Be Greater Than` | threshold | Assert roughness > threshold |
| | `Min Height Should Be Negative` | — | Assert min height < 0 |
| ScatteringLibrary | `Create Lambertian Model` | albedo | Create model |
| | `Evaluate Lambertian` | intensity_arr, direction_arr, normals_arr, view_str, albedo | Run scattering with raw arrays |
| | `Radiance Should Be All Close To` | expected | Assert radiance values |
| | `Radiance Should Be Non Negative` | — | Assert no negative radiance |
| DetectorLibrary | `Create Detector` | exposure_time, quantum_efficiency, ... | Full detector config |
| | `Create Default Detector` | — | Detector with defaults |
| | `Capture With Detector` | height, width, wavelength | Capture a uniform field |
| | `Pixel Range Should Be Within` | min_val, max_val | Assert digital range |
| | `Metadata Should Contain Key` | key | Assert metadata presence |
| AnalysisLibrary | `Create Histogram Analyzer` | — | Standalone histogram analyser |
| | `Create Image Analyzer` | — | ImageAnalyzer with HistogramAnalyzer |
| | `Analyze Known Image` | — | Analyse a fixed [0..5] image |
| | `Histogram Should Exist` | — | Assert histogram is not None |
| | `Measurement Should Exist` | name | Assert measurement key present |

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
