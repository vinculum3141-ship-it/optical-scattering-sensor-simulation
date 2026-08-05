# Research Workflows: From Prototyping to Production

> **Target audience:** Optical researchers, scientists, R&D engineers who
> use the framework to develop, evaluate, and hand off measurement
> concepts.

Simulation exists to let you ask "what if" about a measurement before
(and alongside) building hardware. This page shows a repeatable path
from a one-off prototype to a maintainable, hand-offable workflow — and
maps each stage to concrete framework features.

---

## 1. Why Simulate First

- **Controlled variables.** Every physical parameter is explicit and
  changeable in one place — incidence angle, roughness, albedo, noise,
  exposure, defocus. In hardware these are entangled; in the framework
  they are independent.
- **Fast iteration.** A parameter change is a one-line edit and a
  sub-second rerun, not a new experimental setup.
- **Reproducibility.** Deterministic seeds mean the same configuration
  gives the same image, so results are shareable and reviewable.
- **Noise isolation.** Detector noise is the *only* stochastic stage, so
  you can study physics and electronics effects separately.

---

## 2. The Prototyping Loop

The core loop is short and deliberately small:

```
1. State the question        e.g. "Does dark-field beat bright-field for
                              a 2 µm dent on silicon?"
2. Build the smallest config source + surface + scattering + detector
3. Run and inspect           terminal heatmap, DigitalImage, report
4. Analyse                   contrast, SNR, defect score, PTC, ...
5. Decide / iterate          change one parameter at a time
```

Every step maps to a framework primitive:

| Step | Framework tool |
|---|---|
| Build the smallest config | `SimulationPipeline` (`pipeline.py`) — assemble only what you need |
| Run and inspect | `DigitalImage.visualize()`, `utils.visualize.heatmap()` |
| Analyse | `ImageAnalyzer` with `ContrastAnalyzer`, `SNRAnalyzer`, `DefectAnalyzer`, … |
| Iterate | `GoniometricSweep` / `ScatteringSweep` / exposure sweeps for parameter studies |

**Worked mini-example** (run this to prototype a contrast question):

```python
from optical_metrology.pipeline import SimulationPipeline
from optical_metrology.illumination import Laser
from optical_metrology.surface import DentSurface, Material
from optical_metrology.scattering import LambertianScattering
from optical_metrology.optics import OpticalSystem, GaussianPSF, OpticalPropagator
from optical_metrology.detector import CMOSDetector
from optical_metrology.analysis import ImageAnalyzer, ContrastAnalyzer, HistogramAnalyzer

def run_config(illumination, scattering):
    return SimulationPipeline(
        source=illumination,
        surface=DentSurface((64, 64), radius=3.0, depth=2.0, material=Material("silicon")),
        scattering=scattering,
        optics=OpticalSystem(focal_length=0.05, aperture_diameter=0.008),
        propagator=OpticalPropagator(GaussianPSF(sigma=1.0)),
        detector=CMOSDetector(exposure_time=1e-5),
        analysers=[HistogramAnalyzer(), ContrastAnalyzer()],
    ).run(shape=(64, 64), spacing=0.5)

report_bf = run_config(Laser(532e-9, power=5e-3), LambertianScattering(albedo=0.7)).report
print("Bright-field RMS contrast:", report_bf.measurements["rms_contrast"])
```

> **Prototyping rule:** change exactly one parameter between runs, record
> everything, and keep the noise stage fixed until the physics question is
> answered. This keeps the experiment honest.

---

## 3. The Path to Production

A production-grade workflow is a prototype that has been made
reproducible, parameterised, validated, and documented. Five stages:

### Stage A — Prototype (notebook)

Work interactively in the tutorial notebooks (`notebooks/`, units
`00`–`07`). Everything is exploratory here: quick shapes, fast grids,
terminal visualisation.

### Stage B — Parameterise (CLI script)

Turn the working notebook into a script that takes parameters as
arguments. Each notebook unit already ships one
(e.g. `notebooks/04_angle_resolved_scattering/run_brdf_sweep.py`,
`notebooks/06_lidar_ranging/run_lidar.py`).

```bash
python notebooks/06_lidar_ranging/run_lidar.py --target-range 10.0 --reflectance 0.8
```

**Why:** the same simulation is now runnable across a matrix of inputs —
the raw material for a study, a report, or a regression suite.

### Stage C — Sweep & Validate (analysis)

Use the built-in sweep and fitting tools to map behaviour across the
parameter space and compare against expectations:

- `ScatteringSweep` / `GoniometricSweep` — BRDF versus angle
  (UC4), material identification (UC2)
- `PTCAnalyzer`, `DynamicRangeAnalyzer`, `LinearityTestAnalyzer` —
  sensor characterisation (UC3)
- `SurfaceComparator` — reconstructed vs. ground-truth surface (UC5)
- `SPCAnalyzer` — statistical control metrics (UC7)

**Validation pattern:** compute a *known-answer* case (e.g. normal
incidence on a flat Lambertian surface → radiance = albedo) and assert
the sweep reproduces it before trusting the full sweep. The Robot
acceptance suites encode exactly this style of test.

### Stage D — Codify (tests + docs)

Protect the workflow against regressions:

- Add pytest cases to `tests/` for the physics invariants you rely on.
- Add a Robot acceptance test for the end-to-end scenario
  (`tests/*.robot` + `tests/*Library.py`) so non-programmer reviewers
  can read and re-run it.
- Document assumptions and limitations in the layer docs
  (`docs/science/layer-*.md`) — every model's assumptions are listed
  there.

See [Test Strategy](../quality-assurance/test-strategy.md) and
[Testing](../quality-assurance/testing.md) for the details.

### Stage E — Hand Off

A hand-off is reproducible when a colleague (or a CI pipeline) can:

1. Install: `pip install -e ".[dev,analysis]"`.
2. Run the CLI script with documented flags.
3. Run the test suites: `python -m pytest -q` and `python -m robot tests/`.
4. Read why each parameter exists in the use-case page
   (`docs/use-cases/uc*.md`).

---

## 4. Worked Example: Taking UC6 (LiDAR) from Notebook to Study

| Stage | Action | Tool |
|---|---|---|
| A. Prototype | Explore range vs. received power in `notebooks/06_lidar_ranging/lidar_tutorial.ipynb` | notebook |
| B. Parameterise | Run `run_lidar.py --target-range R --reflectance ρ` for a range grid | CLI script |
| C. Validate | Check the range equation against the inverse-square law at a known reflectance | `LiDARRangeEquation` + pytest |
| D. Codify | Add a sweep test; write a Robot case "Lidar Range Equation Inverse Square" | `tests/test_uc6_lidar.py`, `tests/lidar_ranging.robot` |
| E. Hand off | Document assumptions (scalar atmospheric transmission, single scattering) in the UC6 page | `docs/use-cases/uc6-lidar-ranging.md` |

---

## 5. Researcher Best Practices

1. **Fix the seed early.** Surface geometry should be identical between
   runs; only detector noise varies. This makes before/after comparisons
   meaningful.
2. **Start coarse, refine.** Use small grids (16×16, 32×32) while
   iterating on physics; grow resolution only for the final figures.
3. **Document model assumptions.** The layer docs list the validity
   envelope of each model (e.g. Lambertian: diffuse, no specular;
   GGX/Beckmann: microfacet; defocus: within the paraxial/PSF regime).
   Cite them in papers and reports.
4. **Prefer the built-in sweeps** over hand-rolled loops — they already
   handle angle grids, radiance bookkeeping, and fitting
   (`BRDFFitter`).
5. **Treat the acceptance suite as living documentation.** A Robot test
   that states the expected physics in English is the fastest way to
   communicate a result to a non-simulator colleague.

---

## 6. From Simulation to Real Hardware

Simulation cannot replace calibration, but it de-risks it:

- **Predict before you measure** — the simulated image tells you what
  feature contrast to expect, informing camera/exposure choices.
- **Tune the pipeline before hardware exists** — detector stage,
  exposure, and noise budgets can be prototyped and reviewed.
- **Compare, don't match** — validate *trends* (contrast vs. angle,
  SNR vs. exposure) rather than absolute pixel values; the framework is
  self-consistent, not calibrated to a specific instrument (see
  [Verification & Validation](../quality-assurance/verification-and-validation.md)).
- **Hand hardware data back into the loop** — feed a measured `DigitalImage`
  into the analysis stage to exercise the same metrics on real data.

---

## Further Reading

- [Physics Foundations](physics-foundations.md) — governing equations and assumptions.
- [Layer reference](index.md) — what each layer models.
- [Use Cases](../use-cases/index.md) — seven concrete workflows to build on.
- [Verification & Validation](../quality-assurance/verification-and-validation.md) — what the framework does and does not guarantee.
