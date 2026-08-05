# 03 — Sensor Performance Characterization

> Characterise a simulated detector: photon transfer curve, SNR vs. exposure, dynamic range, and linearity.

## Objective

Run a flat-field illumination sweep and turn sensor physics into engineering metrics: gain (e⁻/ADU), read noise, full-well capacity, dynamic range, and linearity error.

## What you'll see

- Flat-field captures at stepped illumination levels (`FlatFieldSource`)
- PTC (variance vs. mean) with gain fit (`PTCAnalyzer`)
- Dynamic range (`DynamicRangeAnalyzer`) and linearity error (`LinearityTestAnalyzer`)
- Standard test charts: `siemens_star()`, `slanted_edge()`, `greyscale_wedge()`

## Run it

- **Notebook:** open `characterization_tutorial.ipynb`, edit the parameters cell, run in order.
- **CLI:** `python run_characterization.py --help` (illumination levels, exposure, gain, read noise).

## Try next

- Increase read noise and watch the PTC floor rise.
- Push exposure toward full-well and watch the variance curve roll over.
- Raise gain and see the e⁻/ADU estimate change.

## Learn more

- [Use-case documentation](../../docs/use-case-uc3-sensor-characterization.md)
- Key modules: `illumination.FlatFieldSource`, `analysis.PTCAnalyzer/DynamicRangeAnalyzer/LinearityTestAnalyzer`, `detector.CMOSDetector`
