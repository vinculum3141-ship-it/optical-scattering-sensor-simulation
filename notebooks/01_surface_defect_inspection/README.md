# 01 — Surface Defect Inspection

> Automated optical inspection (AOI): detect surface defects on a manufactured part under controlled illumination and make a pass/fail decision.

## Objective

Detect defects — dents, pits, cracks, stains — on a surface and decide pass/fail.  Demonstrates the canonical end-to-end chain and how illumination geometry (bright-field vs. dark-field) changes defect visibility.

## What you'll see

- Defect-laden surfaces rendered through illumination → surface → scattering → optics → detector → analysis
- Bright-field vs. dark-field comparison
- `DefectAnalyzer` output: defect count, contrast, pass/fail

## Run it

- **Notebook:** open `inspection_tutorial.ipynb`, edit the parameters cell, run in order.
- **CLI:** `python run_inspection.py --help` (defect type, illumination, threshold, exposure).

## Try next

- Switch `defect_type` between dent / pit / crack / stain.
- Toggle `illumination` between brightfield and darkfield and compare contrast.
- Raise or lower `threshold` and watch the pass/fail flip.
- Increase exposure time to see detector saturation effects.

## Learn more

- [Use-case documentation](../../docs/use-cases/uc1-surface-defect-inspection.md)
- Key modules: `illumination.bright_field/dark_field`, `surface.Dent/Pit/Crack/StainSurface`, `analysis.DefectAnalyzer`

> Note: this unit consolidates the earlier `defect_inspection.ipynb` and
> `uc1_defect_inspection_playground.ipynb` notebooks into one tutorial.
