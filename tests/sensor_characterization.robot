*** Settings ***
Documentation    Acceptance tests for UC3 Sensor Performance Characterization.
Library          SensorCharLibrary.py

*** Test Cases ***
PTC Measures Gain From Poisson Images
    [Documentation]    PTC analysis should recover gain ≈ 1.0 from
    ...                Poisson-distributed flat-field images.
    Create Poisson Images    count=15    size=32    low=50    high=500    seed=42
    Run PTC Analysis
    Gain Should Be Approx    1.0    tolerance=0.2

PTC Gain Is Positive
    [Documentation]    PTC should always report positive gain.
    Create Poisson Images    count=10    size=16    low=100    high=400    seed=123
    Run PTC Analysis
    Gain Should Be Positive

Dynamic Range Of Uniform Image Is Zero
    [Documentation]    A uniform image has a dynamic range of 0 dB.
    Create Uniform Image    value=2048    size=8
    Run Dynamic Range Analysis
    Dynamic Range Should Be Zero

Dynamic Range Of Varied Image Is Positive
    [Documentation]    An image with varied pixel values should have
    ...                non-zero dynamic range.
    Create Varied Image
    Run Dynamic Range Analysis
    Dynamic Range Should Be Positive

Linearity Test Detects Linear Response
    [Documentation]    Linear sensor response should yield high R²
    ...                and low linearity error.
    Create Linear Response Images    count=6
    Run Linearity Analysis
    Linearity R Squared Should Be High
    Linearity Error Should Be Low

Siemens Star Has Correct Shape
    [Documentation]    Siemens star chart should have the expected
    ...                dimensions and max pixel value.
    Generate Siemens Star    size=128    spokes=36    bit_depth=12
    Image Shape Should Be    128x128
    Max Value Should Be    4095

Slanted Edge Has Two Halves
    [Documentation]    Slanted edge chart should have distinct bright
    ...                and dark halves.
    Generate Slanted Edge    height=64    width=64    angle=5.0    bit_depth=12
    Image Should Have Both Halves

Greyscale Wedge Is Linear Ramp
    [Documentation]    Greyscale wedge should be a monotonically
    ...                increasing linear ramp.
    Generate Greyscale Wedge    height=16    width=64    bit_depth=12
    Greyscale Wedge Should Be Linear
