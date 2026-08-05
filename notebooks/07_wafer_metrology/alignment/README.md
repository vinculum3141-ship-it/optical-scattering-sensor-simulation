# 07 — Wafer Metrology: Die Alignment

> Measure die placement errors (dx, dy, rotation) in semiconductor packaging via optical registration.

## Objective

Register a test image against a reference wafer pattern, estimate translation offsets, and summarise the result with statistical process-control metrics — alignment quality as a metrology result.

## What you'll see

- A synthetic reference pattern vs. a shifted test image
- Template matching (match score) and registration (translation offsets) from `TemplateMatcher` / `RegistrationAnalyzer`
- An SPC summary (control-chart style metrics, Cpk) from `SPCAnalyzer`

## Run it

- **Notebook:** open `alignment_tutorial.ipynb`, edit the parameters cell, run in order.
- **CLI:** `python run_alignment.py --help` (shift, rotation).

## Try next

- Increase the shift and see the registration estimate track it.
- Add rotation and watch the translation-only model struggle.
- Tighten the SPC tolerance and see pass/fail flip.

## Learn more

- [Use-case documentation](../../../docs/use-cases/uc7-alignment.md)
- Key modules: `analysis.TemplateMatcher/RegistrationAnalyzer/SPCAnalyzer`
