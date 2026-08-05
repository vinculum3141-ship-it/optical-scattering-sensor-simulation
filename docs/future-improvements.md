# Future Improvements — Deferred and Not-Yet-Started Work

> **Purpose:** Single tracker for all work that is **not done yet**.
> Toggle each item between `[ ]` (pending) and `[~]` (in progress); when
> you pick an item up, implement it on a branch.
>
> Completed work is not tracked here — see the layer docs,
> `docs/architecture.md`, and the test suite in `docs/testing.md`.

---

## 1. Performance Benchmarks

No benchmark harness exists yet.  The manual O(H·W·K²) sliding-window
convolution in `OpticalPropagator` is the known hot spot; the FFT-based
replacement is called out in the code and `docs/layer-optics.md`.

- [ ] Image-size scaling benchmark (propagation / detection / analysis
      throughput as grid size grows)
- [ ] Convolution cost benchmark (PSF kernel size vs. image size, current
      convolution vs. FFT-based approach)
- [ ] Reconstruction runtime (phase unwrap / height reconstruction for UC5)

## 2. Deferred Use-Case Capabilities

- [ ] **UC4 — Polarised BRDF (Mueller matrix).** Full polarimetric
      scattering.  Depends on the exact-Fresnel / Cook-Torrance
      decomposition in §7.
- [ ] **UC4 — Standard reference materials.** Calibrated reflectance /
      scattering standards for material-characterisation comparisons.
- [ ] **UC4 — BSDF (transmissive scattering).** Transmissive analogue of
      the existing BRDF models.
- [ ] **UC5 — Projector-camera calibration.** Geometric calibration between
      projector and camera for structured-light measurement.
- [ ] **UC5 — Divergent projection model.** More realistic non-parallel
      projection than the current fringe projector.
- [ ] **UC6 — Atmospheric effects.** Long-range LiDAR realism.  A scalar
      `atmospheric_transmission` placeholder already exists in
      `LiDARRangeEquation`; this item is the full atmospheric scattering /
      attenuation model.
- [ ] **UC7 — Real-time performance model.** Lightweight, non-functional
      model for alignment assessment during wafer processing.

## 3. Documentation Site

All `docs/` content is written; only the site build is missing.

- [ ] Create `mkdocs.yml` (with `mkdocstrings[python]`) and deploy to
      GitHub Pages.

---

# Deferred Architectural Notes

Items below are deferred because **no use case requires them yet**, not
because they lack priority.

## 4. Separate BeamGenerator from LightSource

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

## 5. Spatially Varying LightField Properties

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

## 6. Holography / Coherent Imaging

**What:** Full complex-amplitude propagation through the optical chain
(not just intensity PSF convolution).  Requires coherent illumination
and phase-retrieval / digital holography reconstruction.

**Why excluded:** None of the 7 use cases require it.  It would be a
new physics engine rather than an extension of the current radiometric
pipeline.

**Trigger:** A future use case involving digital holographic
microscopy or interferometric surface profiling.

---

## 7. Modular Decomposition of Cook-Torrance (D × F × G)

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
