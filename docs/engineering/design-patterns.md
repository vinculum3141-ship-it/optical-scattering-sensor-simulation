# Design Patterns & Software Principles

> **Target audience:** Software engineers, R&D developers, contributors.
>
> **What this page covers:** the object-oriented principles, GoF design
> patterns, and general software-engineering principles used throughout
> the implementation — with the specific code location of each and the
> *reason* (the benefit) it is applied. This is the "why" companion to
> [Architecture](architecture.md), which covers the overall shape.

---

## How to Read This Page

Each section names a principle or pattern, points to where it lives in
the code, and explains the concrete benefit. File references are relative
to `src/optical_metrology/`.

| Pattern / Principle | Category | Where |
|---|---|---|
| Layered architecture | Architecture | whole package |
| Strategy pattern | Behavioural | `illumination/profiles.py`, `scattering/`, `detector/noise_models.py`, `analysis/` |
| Template Method | Behavioural | `illumination/source.py`, `surface/base.py` |
| Factory (convenience) | Creational | `surface/generators.py` |
| Facade | Structural | `pipeline.py` |
| Composite | Structural | `analysis/base.py` (`ImageAnalyzer`) |
| Null Object / Optional chaining | Behavioural | `pipeline.py` (stages can be `None`) |
| Data container (DTO) | Structural | `illumination/lightfield.py`, `scattering/base.py`, `detector/base.py`, `optics/base.py` |
| Immutable configuration | Principle | `illumination/polarization.py`, `illumination/spectrum.py` |
| Property-synced state | OOP | `illumination/source.py` (`incidence_angle`) |

---

## 1. OOP Principles

### 1.1 Abstraction — "hide the details behind a contract"

Every layer exposes a small, stable interface (an abstract base class
with a single method to implement) and hides its internals.

- `ScatteringModel.evaluate()` — subclasses only implement the physics;
  callers never see how radiance is computed
  (`scattering/base.py:55`).
- `BeamProfile.evaluate(shape, spacing)` — the source calls this without
  knowing which profile is plugged in (`illumination/profiles.py`).

**Why / benefit:** callers depend on the contract, not the concrete
implementation. Physics can be swapped, extended, or corrected without
touching any consumer, and the public API surface stays tiny and
discoverable.

### 1.2 Encapsulation — "keep state and behaviour together"

Configuration is validated and normalised **inside** the object at
construction (`__post_init__`), so a `LightSource` is always in a
consistent state when handed to other code.

```python
# illumination/source.py:87
def __post_init__(self):
    if self.propagation_direction is None:
        self.propagation_direction = np.array([0.0, 0.0, 1.0])
    else:
        norm = np.linalg.norm(self.propagation_direction)
        if norm == 0.0:
            raise ValueError("propagation_direction must be non-zero")
        self.propagation_direction = self.propagation_direction / norm
```

**Why / benefit:** invalid objects are rejected at the boundary instead
of failing mid-pipeline. Every object that escapes its constructor is
guaranteed normalised, so the rest of the codebase can stop re-checking.

### 1.3 Inheritance — "specialise by overriding one hook"

Concrete sources specialise the base dataclass by overriding a single
method:

```python
# illumination/laser.py
class Laser(LightSource):
    def __init__(self, wavelength=532e-9, power=5e-3, **kwargs):
        super().__init__(wavelength=wavelength, power=power, **kwargs)
        self.coherence_length = 1e-2

    def default_spectrum(self):
        return SpectralDistribution(kind="monochromatic", wavelength=self.wavelength)
```

**Why / benefit:** adding a new source type is a ~10-line subclass. The
base class already handles beam-profile evaluation, direction
normalisation, grid generation, and light-field construction
(`generate_light_field()`), so subclasses only supply what is unique to
them.

### 1.4 Polymorphism — "one interface, many behaviours"

The pipeline calls `evaluate()` on whatever scattering model it is given;
each model behaves differently behind the same signature. Robot
Framework tests and the pipeline never branch on model *type*.

**Why / benefit:** new models (Phong, Oren-Nayar, Beckmann, GGX,
Cook-Torrance, Rayleigh, Mie) slot in with zero changes to callers.
Polymorphism is what makes the layers independently replaceable.

### 1.5 Composition over Inheritance

Where behaviour varies at *runtime* or is orthogonal to the object's
identity, the framework composes rather than subclasses:

- `LightSource` **holds** a `BeamProfile` and a `SpectralDistribution`
  rather than inheriting from them (`illumination/source.py:78,85`).
- `CMOSDetector` **holds** a list of `DetectorNoiseModel` instances
  rather than subclassing per noise type.
- `ImageAnalyzer` **holds** a list of `AnalysisModule` instances.

**Why / benefit:** composition avoids the deep, brittle inheritance
hierarchies that make change expensive. Combining two profiles or two
noise models is impossible with inheritance alone but trivial with
composition — and there is no "diamond" ambiguity.

---

## 2. SOLID Principles

| Letter | Principle | How the framework honours it |
|---|---|---|
| **S** | Single Responsibility | Each module has one job: `psf.py` only builds PSF kernels, `noise_models.py` only applies noise, `spc.py` only computes statistical-process-control metrics. |
| **O** | Open/Closed | Layers are open for extension (new subclasses) and closed for modification (no layer code changes when a new model is added). |
| **L** | Liskov Substitution | Any subclass can be used wherever its base is expected — e.g. any `ScatteringModel` can be passed to `SimulationPipeline` or a Robot library. |
| **I** | Interface Segregation | Interfaces are one method wide (`evaluate`, `apply`, `analyze`, `kernel`, `generate`). No model is forced to implement methods it does not need. |
| **D** | Dependency Inversion | High-level code (`SimulationPipeline`) depends on abstractions (`LightSource`, `ScatteringModel`, `AnalysisModule`), not on concrete implementations. |

**Why / benefit (in one line each):**

- **S** → small files, few reasons to change, easy review.
- **O** → adding a feature is adding a file, not editing existing code;
  regressions are localised.
- **L** → tests written against a base class validate every subclass
  (see the shared scattering test suites).
- **I** → extension authors implement exactly one method and no more.
- **D** → the pipeline can be reconfigured with `None`/real/stub
  components without editing `pipeline.py`.

---

## 3. Design Patterns (GoF & Idiomatic)

### 3.1 Strategy Pattern

The most-used pattern in the framework. Algorithms are extracted into
interchangeable objects behind a common interface:

- **Beam profiles** — `UniformBeamProfile`, `GaussianBeamProfile`,
  `TopHatBeamProfile` implement `BeamProfile.evaluate()`; the source
  delegates intensity computation to whichever profile it holds.
- **Scattering models** — `LambertianScattering`, `PhongScattering`,
  `BeckmannScattering`, `GGXScattering`, `CookTorranceScattering`,
  `OrenNayarScattering` implement `ScatteringModel.evaluate()`.
- **Detector noise** — each `DetectorNoiseModel.apply(electrons)` is a
  strategy, and they compose into a chain.
- **Analysis** — every `AnalysisModule.analyze(image)` is a strategy.

```python
# Selecting a strategy at configuration time:
scattering = GGXScattering(roughness=0.2)   # or any other model
scattered = scattering.evaluate(lightfield, surface, view)
```

**Why / benefit:** run-time interchangeability without `if/else`
chains. A strategy can be replaced, wrapped, or tested in isolation,
and the same object graph can be reused across all seven use cases.

### 3.2 Template Method Pattern

The base class defines the skeleton of an algorithm; subclasses override
only the varying step.

- `SurfaceGenerator` defines `create_surface(shape, material)` → analyse
  the height map into a `Surface`; subclasses override only
  `generate(shape)` (`surface/base.py`).
- `LightSource.generate_light_field()` fixes the algorithm (grid →
  profile → wavefront direction → container); subclasses override only
  `default_spectrum()`.

**Why / benefit:** every surface generator produces a fully-analysed,
correctly-typed `Surface` for free. The invariant parts (coordinate
grid, normal computation, curvature) are written once and cannot be
subtly re-implemented differently by each author.

### 3.3 Factory (Constructor-as-Factory)

Concrete generators both *describe* and *produce* the geometry:

```python
# surface/generators.py
class RoughSurface(Surface):
    def __init__(self, shape, sigma=1.0, amplitude=0.3, material=None):
        height = self.generate(shape)          # height map
        surface = GeometryAnalyzer.analyze(height, material=material)
        self.__dict__.update(surface.__dict__) # result IS the surface
```

**Why / benefit:** the caller receives a finished `Surface` in one
expression (`RoughSurface((32, 32), sigma=5.0)`), which reads naturally
and composes cleanly inside `SimulationPipeline`. There is no separate
builder step to forget.

### 3.4 Facade Pattern

`SimulationPipeline` is a facade over the six-layer chain
(`pipeline.py:73`). One object, one `run()` call, one structured
`PipelineResult`.

```python
result = SimulationPipeline(
    source=laser, scattering=LambertianScattering(albedo=0.7),
    detector=CMOSDetector(), analysers=[HistogramAnalyzer()],
).run(shape=(64, 64), spacing=0.5)
```

**Why / benefit:** hides assembly complexity from the 90% of users who
just want an end-to-end image. The underlying layer objects remain fully
reachable for the 10% who need the granular path, so the facade adds a
convenient entry point without removing capability.

### 3.5 Composite Pattern

`ImageAnalyzer` treats one module and many modules uniformly
(`analysis/base.py`):

```python
analyzer = ImageAnalyzer(modules=[HistogramAnalyzer(), ContrastAnalyzer()])
report = analyzer.analyze(image)   # runs every module, merges reports
```

**Why / benefit:** individual analysis modules stay small and
single-purpose, while "run them all" is a first-class operation. Adding
a new metric is adding a module and listing it — no orchestration code
changes.

### 3.6 Data Container / DTO

The layers exchange plain, validated dataclasses carrying arrays and
scalars: `LightField`, `ScatteredField`, `SensorField`, `DigitalImage`,
`AnalysisReport`. They carry the *data contract* documented in
[Architecture](architecture.md#data-contracts-the-glue).

**Why / benefit:** layers are decoupled by data, not by object
references — you can build a `ScatteredField` by hand and feed it to
the detector, skipping the scattering layer entirely. DTOs are trivially
copyable, comparable, and inspectable.

### 3.7 Null Object / Optional-Stage Chaining

Every `SimulationPipeline` stage accepts `None` to mean "skip this
stage" (`pipeline.py:160-190`). `PipelineResult` fields are `Optional`,
so callers can always read `.digital_image` and handle `None` explicitly.

**Why / benefit:** partial pipelines (illumination-only, detector-with-
synthetic-input, etc.) are first-class configurations. This is what
makes the framework usable as a unit-level tool as well as an
end-to-end simulator — and it is exactly what the use-case and test
suites exploit.

### 3.8 Immutable Configuration (Frozen Dataclass)

State that must never change after construction is frozen:

```python
# illumination/polarization.py
@dataclass(frozen=True)
class PolarizationState:
    kind: str
```

Mutable configuration (e.g. `LightSource`, `CMOSDetector`) uses a
regular dataclass with `__post_init__` normalisation.

**Why / benefit:** frozen config objects can be shared across threads
and cached without copies, and accidental mutation (the classic source
of hard-to-find bugs) raises immediately instead of silently corrupting
a simulation.

---

## 4. Other Software Principles

### 4.1 DRY — Don't Repeat Yourself

One implementation per concern, shared through composition:

- Terminal heatmaps were previously implemented four times; now a single
  `utils/visualize.py:heatmap()` is used by `LightField`,
  `DigitalImage`, `explore.py`, and `playground.py`.
- Grid-coordinate math lives in `LightSource._compute_grid_coords()`
  instead of being re-derived in every wavefront branch.

**Why / benefit:** one source of truth means one place to fix, and no
drift between "copies" of the same logic.

### 4.2 Fail Fast

Validation happens at the boundary — constructor and `__post_init__`:
unknown beam profiles and wavefronts raise `ValueError`, zero-length
direction vectors raise `ValueError`, and abstract base methods raise
`NotImplementedError`.

**Why / benefit:** a configuration error surfaces with a clear message
at construction time rather than as a confusing numerical artefact ten
stages later.

### 4.3 Separation of Concerns

The six layers split the physical pipeline; within each layer, *model
definition* (data + physics) and *orchestration* (pipeline, ImageAnalyzer)
are separate. UI/visualisation (`visualize`, `explore.py`,
`playground.py`) is separate from computation.

**Why / benefit:** each concern can be understood, tested, and changed
in isolation. The visualisation helpers are optional imports, so the
core pipeline stays dependency-light.

### 4.4 Minimal Public API / Discoverable Imports

Each package's `__init__.py` re-exports its public surface (e.g.
`from optical_metrology.illumination import Laser, LED, ...`), so users
import from the package root rather than deep modules.

**Why / benefit:** the public API is a curated, stable list; internals
can be reorganised without breaking user code, and IDEs/autocomplete
present exactly what is meant to be used.

### 4.5 Determinism by Default

Surface generators accept and default to fixed RNG seeds; stochastic
variation is confined to the detector noise stage by design.

**Why / benefit:** the same configuration reproduces the same image,
which is essential for debugging, regression testing, and scientific
reproducibility. Where noise *must* vary, it is explicit and documented.

### 4.6 Program to an Interface, Not an Implementation

Every cross-layer call goes through a base-class method (`evaluate`,
`apply`, `analyze`, `kernel`, `generate`). Concrete classes are named
only at construction time.

**Why / benefit:** this is what makes the [Strategy](#31-strategy-pattern)
and [Dependency Inversion](#2-solid-principles) entries work; without it,
replacing a model would require editing every call site.

---

## 5. How the Principles Connect

The principles reinforce each other:

```
Separation of Concerns → six layers
        ↓
Program to an interface → Strategy + Polymorphism
        ↓
Open/Closed            → new models = new files, not edits
        ↓
Facade (pipeline)      → easy assembly of any combination
        ↓
Fail fast + Immutability → trustworthy objects at every boundary
```

When extending the framework, [Extending the Framework](extending.md)
shows the practical mechanics of each hook; this page explains why the
hooks exist.

---

## 6. Anti-Patterns We Deliberately Avoid

| Anti-pattern | Why avoided here |
|---|---|
| **God objects** | The pipeline orchestrates but computes nothing; every layer stays single-purpose. |
| **Deep inheritance chains** | Maximum depth is two levels (base → concrete); variation comes from composition. |
| **Leaky abstraction** | Data contracts are plain arrays/scalars; no hidden coupling between layers. |
| **Premature optimisation** | The hot spot (PSF convolution) is documented and deferred to an FFT-based approach — see `../future-improvements.md`. |
| **Global mutable state** | No module-level mutable configuration; all state lives in objects. |
