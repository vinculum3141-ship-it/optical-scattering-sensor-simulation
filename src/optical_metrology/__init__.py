"""optical_metrology — virtual optical metrology platform.

End-to-end simulation of illumination, surface scattering, optical
propagation, detection, and image analysis.

Pipeline
--------
::

    Light Source  →  LightField  →  Surface  →  ScatteredField
     →  Optics (PSF)  →  SensorField  →  Detector  →  DigitalImage
     →  Analysis  →  Measurements

Sub-packages
------------
- ``illumination`` — light sources, beam profiles, spectra, polarisation
- ``surface`` — height map generators, geometry analysis
- ``scattering`` — BRDF models (Lambertian, Oren-Nayar, Phong, Cook-Torrance)
- ``optics`` — PSF convolution, optical system parameters
- ``detector`` — CMOS pipeline, noise models, digitisation
- ``analysis`` — histogram, contrast, saturation, and extensible modules
- ``utils`` — shared helper functions (terminal heatmap, etc.)
"""
