# 02 — Multi-Spectral Material Identification

> Identify a material from its spectral reflectance measured at several wavelengths.

## Objective

Build a spectral stack, extract per-pixel spectral vectors, and classify each pixel against a small reference library — showing that material identity comes from a vector of reflectance values, not a single grayscale image.

## What you'll see

- A synthetic multispectral image with distinct material regions
- `SpectralAnalyzer` classification — spectral angle mapping and band ratios — with a dominant label per pixel
- Optional CFA / demosaicing path via `CFADetector`

## Run it

- **Notebook:** open `identification_tutorial.ipynb`, edit the parameters cell, run in order.
- **CLI:** `python run_classification.py --help`.

## Try next

- Change the reference spectrum for one region and watch the label change.
- Add a third band and see classification confidence shift.
- Make the two material spectra more similar and find the point where they blur together.

## Learn more

- [Use-case documentation](../../docs/use-cases/uc2-multispectral-identification.md)
- Key modules: `illumination.MultiSpectralSource/FilterWheelSource`, `analysis.SpectralAnalyzer`, `detector.CFAConfig/CFADetector`
