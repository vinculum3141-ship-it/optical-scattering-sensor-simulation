# Test Strategy (ISTQB-Aligned)

> **Target audience:** Testers, QA engineers, developers, and anyone
> responsible for the quality of the framework.
>
> This page applies the vocabulary and structure of the
> [ISTQB® Foundation Level syllabus](https://www.istqb.org/)
> — test levels, test types, and test design techniques — to this
> codebase, so that QA engineers who know ISTQB can map their knowledge
> directly onto the project. The terminology follows the
> [ISTQB Glossary](https://glossary.istqb.org/).
>
> **Companion pages:** [Testing](testing.md) is the concrete test
> inventory and how-to-run guide. [Verification & Validation](verification-and-validation.md)
> maps the strategy onto ISO standards.

---

## 1. What We Are Testing

The framework is a pure-Python simulation library with:

- a six-layer numerical pipeline (illumination → surface → scattering →
  optics → detector → analysis),
- an orchestration facade (`SimulationPipeline`),
- seven end-to-end use cases,
- no external state, no I/O, no UI (terminal heatmaps only).

Because there is no UI or network, the test effort concentrates on
**functional correctness**, **numerical plausibility**, and **contract
stability** — not on integration with third-party systems.

## 2. Test Levels (ISTQB §1.2)

ISTQB defines four test levels. The framework's suites map onto them:

| ISTQB level | Scope | Where it lives here |
|---|---|---|
| **Component (unit)** | Each model/class in isolation | `tests/test_illumination.py`, `test_surface_new.py`, `test_scattering.py`, `test_optics_new.py`, `test_detector_new.py`, `test_analysis_new.py`, `test_pipeline.py`, `test_utils.py` |
| **Integration** | Interaction between layers/components | `tests/test_uc*_integration.py`; layer chaining inside `test_pipeline.py` |
| **System** | The whole framework as one product | `tests/test_uc*_example.py` (run the shipped scripts end-to-end) |
| **Acceptance** | Stakeholder-readable verification of real scenarios | Robot Framework suites (`tests/*.robot`) |

The test pyramid for this project:

```
         ▲   Acceptance (Robot)     96 tests — few, stakeholder-readable
        ▲ ▲   System (pytest)        ~10  — example scripts run end-to-end
       ▲ ▲ ▲   Integration           ~90  — layer/use-case interaction
      ▲ ▲ ▲ ▲   Component (unit)     ~250 — one behaviour per test, fast
```

**Rationale (why this shape):** unit tests are cheap and pinpoint the
failing model; acceptance tests are expensive but prove real scenarios
end-to-end. The bulk of coverage sits at the bottom, where failures are
cheapest to find, following the ISTQB guidance that lower levels find
defects earlier.

## 3. Test Types (ISTQB §2.x)

ISTQB groups tests by objective. Which types apply here:

| Test type | Objective | How it is covered |
|---|---|---|
| **Functional** | Does it do what it should? | Every model test asserts a specific behaviour (defaults, shapes, limits, edge cases). |
| **Data integrity** | Data survives transit correctly | Shape-contract assertions on every data container (`(H, W)`, `(H, W, 3)`). |
| **Performance efficiency** | Time/resource behaviour | Not automated (deferred — see `future-improvements.md` §1). Documented hot spot: PSF convolution. |
| **Compatibility** | Works across environments | CI runs pytest + Robot on GitHub Actions (Ubuntu, Python 3.14). |
| **Usability / accessibility** | Readable by non-coders | Acceptance tests written in natural-language Robot syntax. |
| **Portability / installability** | Installs cleanly | `pip install -e .` exercised in CI; dependency set is minimal (NumPy only for core). |

**Deliberately out of scope** (documented in [testing.md](testing.md#what-we-dont-verify)):
exact agreement with physical hardware, memory bounds, concurrency safety.

## 4. Test Design Techniques (ISTQB §4)

### 4.1 Black-Box Techniques

**Equivalence Partitioning** — divide inputs into classes that should
behave identically, test one representative per class.

- Detector bit depth: the valid digital range `[0, 2^bit_depth − 1]`
  partitions into *underflow*, *valid*, and *overflow*; tests assert the
  valid partition and clipping at both boundaries.
- Incidence angle: normal (`0`), oblique (`0 < θ < π/2`), grazing
  (`π/2`) behave differently in every scattering model and are each
  tested explicitly.

**Boundary Value Analysis** — test at and around the edges of a
partition, where most defects cluster.

- Grid sizes: odd vs. even (PSF kernels auto-adjust for odd sizes),
  and `shape` given as int vs. tuple (both accepted).
- Defect pass/fail: the threshold that flips the decision is tested on
  both sides (`DefectAnalyzer`).
- Grazing incidence: `θ = π/2` must produce zero radiance — tested for
  every scattering model.
- Convolution kernel sizes: minimum and one-past-minimum values.

**Decision Table Testing** — systematically cover combinations of
conditions and their outcomes.

- `SimulationPipeline` stages: each can be present/absent (`None`), so
  the combinations *source*, *surface*, *scattering*, *optics*, *detector*,
  *analysers* are exercised as partial pipelines in `test_pipeline.py`
  (illumination-only, detector-only with synthetic input, full chain).
- Defect pass/fail matrix: defect type × illumination mode × threshold.

**State Transition Testing** — test valid/invalid transitions between
states.

- Wavefront modes (`planar` → `spherical` → `converging`) and beam
  profile string conversion (`"uniform"`, `"gaussian"`, and an invalid
  string that must raise).
- Noise-model chaining: applying multiple noise stages in sequence and
  verifying each is applied.

### 4.2 White-Box Techniques

**Statement & Branch Coverage** — ensure every line/branch executes.

- Scattering models are tested for the *grazing* branch (dot product →
  0), the *normal-incidence* branch, and the *Fresnel* branch.
- `__post_init__` branches (direction normalisation, string-to-object
  conversion) are covered by constructor tests.

**Coverage measurement** is available but not a CI gate:
`pytest --cov=<layer>`. See [testing.md](testing.md#running-tests).

### 4.3 Experience-Based Techniques

- **Error guessing** — tests assert that unsupported values raise clear
  `ValueError`/`NotImplementedError` instead of silently misbehaving
  (fail-fast principle).

## 5. Verification of Stochastic Code

The detector stage uses Poisson-distributed shot/dark noise, so exact
values are not assertable. The strategy (a deliberate deviation from
naive value-equality testing):

- **Statistical bounds** — pixel values must fall in the valid range.
- **Distribution-agnostic invariants** — means, ranges, and monotonic
  trends rather than exact counts.
- **Determinism by default elsewhere** — surface geometry uses fixed
  seeds, so only the noise stage needs statistical treatment.

This matches the ISTQB principle that the *oracle* for stochastic
systems must be a property, not a literal value.

## 6. Test Planning & Control (ISTQB §5)

### What gets tested first (risk-based ordering)

Highest risk = numerical physics with edge-case branches. Order of
priority:

1. Scattering models (grazing/normal/Fresnel branches, non-negativity).
2. Detector (noise, range, ADC limits, chaining).
3. Optics (kernel normalisation, size handling, defocus).
4. Data contracts / shapes (cheap, catch most integration defects).
5. Use-case integration (proves the whole chain).

### Traceability

Every use-case feature is traceable to tests:

| Requirement area | Component tests | Integration tests | Acceptance tests |
|---|---|---|---|
| Illumination models | `test_illumination.py` | `test_uc*_integration.py` | `illumination.robot` |
| Scattering models | `test_scattering*.py` | `test_uc*_integration.py` | `scattering*.robot` |
| Defect inspection (UC1) | `test_surface_new.py` | `test_uc1_integration.py` | `defect_inspection.robot` |
| … and so on per layer / use case | … | … | … |

The full inventory is in [testing.md](testing.md#test-structure).

## 7. Regression Strategy

- **Every change** → `python -m pytest -q` (352 tests) gates correctness.
- **Every release/PR** → CI also runs the full Robot suite (96 tests)
  as living acceptance documentation.
- **Physics invariants** are regression-protected at component level
  (e.g. Lambertian radiance = albedo at normal incidence), so a model
  change cannot silently drift.

## 8. Roles & Responsibilities (ISTQB-informed)

| Role | Owns |
|---|---|
| Developer | Component & integration pytest; failure diagnosis |
| QA engineer | Acceptance test cases (`.robot` files) composed from keywords; reviewing coverage; reporting |
| QA engineer / developer | New Robot keywords (library methods) when a new scenario needs one |
| Maintainer | CI pipeline, coverage review, release gating |

Robot's separation of *specification* (`.robot`) from *implementation*
(Python libraries) is the deliberate hand-off point: a QA engineer can
write new test cases without writing Python (see
[testing.md](testing.md)).

## 9. CI Integration

The CI workflow (`.github/workflows/ci.yml`) runs on every push/PR to
`main`:

1. `python -m pytest -v`
2. `python -m robot --outputdir robot-output tests/`

Robot produces `report.html` / `log.html` / `output.xml` — timestamped,
self-contained evidence that can be shared with stakeholders.

## 10. Continuous Improvement

Tracked in [future-improvements.md](../future-improvements.md) §1
(performance benchmarks) and the QA-related deferred work. Suggested
next steps:

- Coverage thresholds and a coverage report in CI.
- A performance regression benchmark for the convolution hot spot.
- More acceptance-level `[Template]` data-driven Robot cases across
  parameter grids.
