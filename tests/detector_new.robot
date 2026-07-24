*** Settings ***
Documentation    Verification tests for built-in detector noise models.
Library          DetectorLibrary.py

*** Test Cases ***
Fixed Pattern Noise Can Be Added
    [Documentation]    FixedPatternNoise adds a constant offset per pixel.
    Create Detector    exposure_time=0.1    quantum_efficiency=0.9
    ...                dark_current=5.0    read_noise_sigma=2.0
    ...                full_well_capacity=80000.0    gain=2.0
    ...                bit_depth=12
    Add Fixed Pattern Noise    magnitude=10.0
    Capture With Detector    height=8    width=8    wavelength=532e-9
    Image Should Be Digital Image
    Pixel Shape Should Be    8,8

Column Defect Zeroes Out Column
    [Documentation]    ColumnDefectNoise with scale=0 should zero out
    ...                the affected column.
    Create Detector    exposure_time=0.1    quantum_efficiency=0.9
    ...                dark_current=5.0    read_noise_sigma=2.0
    ...                full_well_capacity=80000.0    gain=2.0
    ...                bit_depth=12
    Add Column Defect    column=0    scale=0.0
    Capture With Detector    height=8    width=8    wavelength=532e-9
    Column Should Be Zero    column=0

Multiple Noise Models Can Be Chained
    [Documentation]    Multiple noise models can be applied sequentially.
    Create Detector    exposure_time=0.1    quantum_efficiency=0.9
    ...                dark_current=5.0    read_noise_sigma=2.0
    ...                full_well_capacity=80000.0    gain=2.0
    ...                bit_depth=12
    Add Fixed Pattern Noise    magnitude=5.0
    Add Hot Pixel Noise    density=0.1    hot_current=100.0    exposure_time=0.1
    Capture With Detector    height=8    width=8    wavelength=532e-9
    Image Should Be Digital Image
    Pixel Shape Should Be    8,8
