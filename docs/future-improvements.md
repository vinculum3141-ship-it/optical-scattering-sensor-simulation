# Future Improvements — Deferred Architectural Notes

> **Purpose:** Track design ideas explicitly **not** in the current
> roadmap (see `docs/roadmap-todo.md` for planned work).  Items here
> are deferred because no use case requires them yet, not because they
> lack priority.

---

## 1. Separate BeamGenerator from LightSource

**What:** Split `LightSource.generate_light_field()` into a standalone
`BeamGenerator` class that samples a physical source onto a grid.

**Why excluded:** No use case needs multiple beam models per source.
The current method is convenient and blocks nothing.  This is a pure
architectural refactor.

**Trigger:** UC5 (structured light) — projecting different fringe
patterns from the same projector, or composing a segmented ring-light
from multiple beam profiles.

**Sketch:**
```python
class BeamGenerator:
    def generate(self, source: LightSource, shape, spacing) -> LightField: ...

# LightSource becomes a pure parameter container:
laser = Laser(532e-9, power=5e-3)
gen = PlanarBeamGenerator(beam_profile=GaussianBeamProfile(w0=2.0))
lf = gen.generate(laser, shape=(32, 32), spacing=0.5)
```

---

## 2. Spatially Varying LightField Properties

**What:** Promote `wavelength`, `polarization`, and `coherence_length`
from scalar to per-pixel arrays on `LightField`.

**Why excluded:** No use case demands it.  Keeping them scalar keeps
the interface simple.

**Trigger:** UC2 (multi-spectral) — wavelength stack; or modelling a
spatially varying polariser / colour filter array.

**Sketch:**
```python
@dataclass
class LightField:
    intensity: np.ndarray           # (H, W)
    direction: np.ndarray           # (H, W, 3)
    wavelength: np.ndarray          # (H, W)
    polarization: np.ndarray        # (H, W)
    coherence_length: float | np.ndarray
    power: float
    phase: np.ndarray | None
```
Backwards compatible if scalar inputs are broadcast to full grid.

---

## 3. Holography / Coherent Imaging

**What:** Full complex-amplitude propagation through the optical chain
(not just intensity PSF convolution).  Requires coherent illumination
and phase-retrieval / digital holography reconstruction.

**Why excluded:** None of the 7 use cases require it.  It would be a
new physics engine rather than an extension of the current radiometric
pipeline.

**Trigger:** A future use case involving digital holographic
microscopy or interferometric surface profiling.

---

## 4. Modular Decomposition of Cook-Torrance (D × F × G)

**What:** Extract the three components of the Cook-Torrance BRDF into
swappable modules:

- **Distributions:** Beckmann, GGX, Blinn
- **Fresnel models:** Schlick (fast), exact Fresnel (polarised)
- **Geometry functions:** Smith (Schlick-GGX), Cook (original 1982)

Currently these are inlined as module-level functions in
`scattering/cooktorrance.py`, which is sufficient for the single
Cook-Torrance variant we have.  Extracting them would let new models
(e.g. a GGX-based Cook-Torrance) be built by composing existing pieces
instead of copying.

**Why excluded:** No use case needs more than one variant of
Cook-Torrance.  The indirection adds files without benefit until UC4
(BRDF fitting) or polarised BRDF work begins.

**Trigger:** UC4 (Angle-Resolved Scattering) — BRDF fitting needs
Beckmann, GGX, and other candidate models.  At that point,
`distribution_beckmann` and `distribution_ggx` should be imported from
a shared location rather than duplicated or coupled to
Cook-Torrance.  Also, UC4's polarised BRDF work will need the exact
Fresnel equations (`fresnel_exact`).
