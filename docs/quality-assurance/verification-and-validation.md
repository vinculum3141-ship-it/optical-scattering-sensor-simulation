# Verification & Validation (ISO References)

> **Target audience:** Testers, QA engineers, researchers, and
> engineering managers who need to know what the framework's test
> evidence does — and does not — guarantee, mapped to international
> standards.

This page defines the project's **verification** and **validation**
positions using standard terminology, then maps the two-tier test
strategy onto relevant ISO / IEC / IEEE standards and the ISTQB
syllabus. It is the "assurance" companion to
[Test Strategy](test-strategy.md) and [Testing](testing.md).

---

## 1. Verification vs. Validation — Definitions

Following the definitions in **ISO/IEC/IEEE 12207** (Software life cycle
processes, §6.4) and echoed by **ISO/IEC/IEEE 29119** (Software testing):

> **Verification** — confirmation, through the provision of objective
> evidence, that specified requirements have been fulfilled
> ("did we build it right?").
>
> **Validation** — confirmation that the requirements for a specific
> intended use are fulfilled ("did we build the right thing?").

Applied to this project:

| Concept | Question | Evidence here |
|---|---|---|
| **Verification** | Does the framework compute what its models say they compute? | pytest suites: constructor defaults, shape contracts, physical invariants, edge cases |
| **Validation** | Does the framework behave like a realistic optical sensor? | Robot acceptance suites describe and check realistic scenarios end-to-end |
| **Model calibration** | Do absolute numbers match specific hardware? | **Not claimed** — see §5 |

## 2. Applicable Standards

| Standard | What it is | How this project relates |
|---|---|---|
| **ISO/IEC/IEEE 29119** (parts 1–4) | International standard for software testing: test process, levels, types, design techniques | The test levels and design techniques in [Test Strategy](test-strategy.md) follow its vocabulary and structure |
| **ISO/IEC/IEEE 12207** | Software life cycle processes; defines verification (6.4.8) and validation (6.4.9) processes | The verification/validation split in §1 uses its definitions |
| **ISO/IEC 25010** (SQuaRE) | Software quality model: 8 quality characteristics | Used in §3 to classify what is / is not assured |
| **ISO 9001:2015** | Quality management systems; §8.6 (release of product and services) requires verification evidence before release | CI gates (`pytest`, `robot`) provide repeatable, objective evidence of verification |
| **ISO 5725** (parts 1–6) | Accuracy (trueness and precision) of measurement methods and results | Relevant framing for any future comparison of simulated vs. measured values (bias and precision, not just point estimates) |
| **JCGM 100:2008 (GUM)** | Guide to the Expression of Uncertainty in Measurement | Guidance if the framework is used to propagate uncertainty budgets into simulated measurement uncertainty |
| **ISTQB Foundation Level** | Competence scheme and common vocabulary for software testing | The terminology used throughout the QA section |

> Note: referencing a standard is **not** a claim of certification.
> These standards inform vocabulary, structure, and good practice; the
> project does not claim formal conformance to any of them.

## 3. Quality Characteristics (ISO/IEC 25010)

ISO/IEC 25010's quality model gives an honest way to state what is
assured and what is not:

| Quality characteristic | Status in this project |
|---|---|
| **Functional correctness** | Assured by the component + integration pytest suites (352 tests). |
| **Functional suitability / completeness** | Assured at acceptance level by Robot scenarios (96 tests) covering all seven use cases. |
| **Reliability** | Reasonable confidence from the regression suite; no formal fault-injection or soak testing. |
| **Performance efficiency** | **Not assured** — deferred to a benchmark harness (see `../future-improvements.md` §1). |
| **Compatibility** | CI executes on Ubuntu / Python 3.14; package requires Python ≥ 3.9, NumPy only. |
| **Maintainability** | Supported by architecture (layered, low coupling), docstring coverage, and the design-patterns documentation. |
| **Portability / installability** | `pip install -e .` verified in CI; core has no optional-dependency requirements. |
| **Security** | Not in scope for a numerical library with no I/O surface. |

## 4. What We Verify (and How) — ISO 9001 §8.6 framing

ISO 9001:2015 §8.6 requires objective evidence that acceptance criteria
are met before release. The project's acceptance criteria:

1. **Constructor correctness** — defaults, validation, type conversion.
2. **Shape contracts** — every data container preserves `(H, W)` /
   `(H, W, 3)` shapes.
3. **Physical plausibility** — non-negative radiance, positive roughness
   for non-flat surfaces, in-range digital values.
4. **Edge cases** — grazing incidence (zero), back-surface illumination
   (zero), flat surfaces (all zeros), non-square grids.
5. **Interface enforcement** — abstract bases raise `NotImplementedError`.

Evidence is produced by `python -m pytest -q` (unit + integration) and
`python -m robot tests/` (acceptance), both gated in CI.

## 5. What We Do NOT Claim (Validation Boundaries)

Honesty about scope is part of good validation reporting:

- **No calibration to specific hardware.** The framework is
  self-consistent, not instrument-calibrated. Absolute pixel values are
  not asserted against physical experiments.
- **No performance/memory guarantees.** Convolution throughput is a
  known hot spot with a documented FFT-based path (see `../future-improvements.md` §1).
- **No concurrency guarantees.** Multi-threading safety is not a design
  goal.
- **Model validity envelopes apply.** Each layer doc lists assumptions
  (e.g. Lambertian has no specular component; microfacet models assume
  locally-flat facets; defocus is modelled in the paraxial/PSF regime).
  Using a model outside its envelope is a user decision, not a tested
  guarantee.

## 6. Statistical Approach to Stochastic Code

Detector noise is Poisson-distributed, so verification uses statistical
bounds rather than exact values — a deliberate, documented deviation
from literal-value assertions. This aligns with the ISO 5725 concept of
**precision**: we verify the *spread* behaviour (in-range values,
trends, monotonicity) rather than point estimates. See
[Test Strategy](test-strategy.md#5-verification-of-stochastic-code).

## 7. Traceability Example

| Requirement | Verification evidence | Validation evidence |
|---|---|---|
| "Lambertian surface at normal incidence reflects radiance equal to albedo" | `test_scattering.py` (component) | `scattering.robot` (acceptance) |
| "Digital image pixel range is `[0, 2^bit_depth − 1]`" | `test_detector_new.py` | `detector.robot` |
| "Defect inspection returns a pass/fail decision" | `test_uc1_integration.py` | `defect_inspection.robot` |

## 8. If You Need Formal Assurance

If a downstream project requires documented conformance (e.g. to
ISO 9001 for quality-managed delivery, or ISO/IEC 29119 for a defined
test process), the steps are:

1. Adopt the Robot reports (`report.html` / `log.html` / `output.xml`)
   as retained, timestamped records of acceptance-test execution.
2. Add a coverage gate and a performance benchmark (tracked in
   `../future-improvements.md`).
3. Maintain a requirements-to-tests traceability matrix (see §7 pattern)
   as a controlled document.

---

## Further Reading

- [Test Strategy (ISTQB-aligned)](test-strategy.md)
- [Testing & Verification](testing.md) — the concrete inventory
- [Research Workflows](../science/research-workflows.md) — how to use
  simulation validation when moving toward hardware
