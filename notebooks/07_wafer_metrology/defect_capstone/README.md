# 07 — Wafer Metrology: ASML-Style Defect Capstone

> High-end semiconductor inspection workflow combining the framework's full metrology chain.

## Objective

Combine wafer pattern, engineered surface roughness, coherent speckle noise, defect detection, and signal-to-noise analysis in one workflow inspired by wafer inspection in ASML-style lithography systems.

## What you'll see

- A wafer-like surface with roughness and defects under coherent illumination (speckle)
- Defect detection (`DefectAnalyzer`) and error-map comparison (`ErrorMapAnalyzer`)
- Signal-to-noise and speckle-roughness metrics (`SNRAnalyzer`, `SpeckleRoughnessEstimator`)

## Run it

- **Notebook:** open `asml_capstone_tutorial.ipynb`, edit the parameters cell, run in order.
- **CLI:** `python run_asml_capstone.py --help` (wafer roughness, defect depth, exposure).

## Try next

- Increase surface roughness and watch speckle degrade detection.
- Change defect depth and see the SNR estimate shift.
- Toggle exposure and observe saturation vs. low-signal trade-offs.

## Learn more

- [Use-case documentation](../../../docs/use-cases/uc7-defect-capstone.md)
- Key modules: `surface.WaferSurface/RoughSurface`, `detector.noise_models.SpeckleNoise`, `analysis.DefectAnalyzer/ErrorMapAnalyzer/SNRAnalyzer/SpeckleRoughnessEstimator`
