*** Settings ***
Documentation       Verification tests for UC2 multi-spectral material identification.
Library             MultiSpectralLibrary.py

*** Test Cases ***
Multi-Spectral Source Generates Correct Channels
    [Documentation]    A MultiSpectralSource with 3 channels produces
    ...                a 3-channel light field with correct wavelengths.
    Create Multispectral Source    450e-9    1.0    550e-9    2.0    650e-9    3.0
    Generate Light Field    height=4    width=4
    Number Of Channels Should Be    3
    Intensities At Channel Should Be    channel=0    expected_val=1.0
    Intensities At Channel Should Be    channel=1    expected_val=2.0
    Intensities At Channel Should Be    channel=2    expected_val=3.0

Filter Wheel Source Cycles Wavelengths
    [Documentation]    FilterWheelSource cycles through channels
    ...                sequentially.
    Create Filter Wheel Source    450e-9    2.0    550e-9    4.0
    Generate Light Field    height=2    width=2
    Intensities At Channel Should Be    channel=0    expected_val=2.0

Spectral Angle Mapper Identical Spectra
    [Documentation]    SAM between identical vectors is zero.
    Spectral Angle Should Be Close    r0=1.0    r1=2.0    r2=3.0
    ...    t0=1.0    t1=2.0    t2=3.0
    ...    expected=0.0

Spectral Angle Mapper Orthogonal Spectra
    [Documentation]    SAM between orthogonal vectors is π/2.
    Spectral Angle Should Be Close    r0=1.0    r1=0.0    r2=0.0
    ...    t0=0.0    t1=1.0    t2=0.0
    ...    expected=1.570796    tolerance=1e-5

Spectral Analyzer Classifies Materials
    [Documentation]    SpectralAnalyzer correctly classifies pixels
    ...    by minimum SAM distance.
    Create Spectral Analyzer    mat_A    1.0    0.0    0.0    mat_B    0.0    1.0    0.0
    Classify Data    1.0    0.0    0.0    0.0    1.0    0.0    1.0    0.0    0.0    0.0    1.0    0.0
    Classification Labels Should Be    0    1    0    1
    Classification Confidence Should Be Above    threshold=0.9

Classification With Multiple References
    [Documentation]    Classification with 3 reference materials.
    Create Spectral Analyzer    Si    1.0    0.0    0.5    Au    0.0    1.0    0.5    Cu    0.5    0.5    1.0
    Add Reference Spectrum    Al    0.8    0.2    0.1
    Classify Data    1.0    0.0    0.5    0.0    1.0    0.5
    Classification Labels Should Be    0    1
