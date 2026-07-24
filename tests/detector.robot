*** Settings ***
Documentation       Verification tests for the detector package.
Library             DetectorLibrary.py

*** Test Cases ***
Default Detector Can Be Created
    [Documentation]    CMOSDetector() with no arguments creates a
    ...                detector with sensible defaults.
    Create Default Detector
    Detector Type Should Be    CMOSDetector

Detector Pipeline Returns DigitalImage
    [Documentation]    CMOSDetector.capture() returns a properly-shaped
    ...                DigitalImage with uint16 pixels.
    Create Default Detector
    Capture With Detector    height=8    width=8    wavelength=532e-9
    Image Should Be Digital Image
    Pixel Shape Should Be    8,8
    Pixel Dtype Should Be Uint16

Pixel Values Are Within Digital Range
    [Documentation]    For 12-bit mode, pixel values must be in [0, 4095].
    Create Detector    exposure_time=0.1    quantum_efficiency=0.9
    ...                dark_current=5.0    read_noise_sigma=2.0
    ...                full_well_capacity=80000.0    gain=2.0
    ...                bit_depth=12
    Capture With Detector    height=4    width=4    wavelength=532e-9
    Pixel Range Should Be Within    min_val=0    max_val=4095

8Bit Mode Produces Values In 0-255 Range
    [Documentation]    With bit_depth=8, the maximum pixel value is 255.
    Create Detector    exposure_time=0.01    quantum_efficiency=0.7
    ...                dark_current=1.0    read_noise_sigma=0.5
    ...                full_well_capacity=20000.0    gain=1.0
    ...                bit_depth=8
    Capture With Detector    height=4    width=4    wavelength=532e-9
    Pixel Range Should Be Within    min_val=0    max_val=255

Metadata Records Capture Parameters
    [Documentation]    The DigitalImage metadata should contain the
    ...                detector settings used during capture.
    Create Detector    exposure_time=0.05    quantum_efficiency=0.8
    ...                dark_current=2.0    read_noise_sigma=1.0
    ...                full_well_capacity=50000.0    gain=1.5
    ...                bit_depth=14
    Capture With Detector    height=4    width=4    wavelength=532e-9
    Metadata Should Contain Key    bit_depth
    Metadata Should Contain Key    exposure_time
    Metadata Should Contain Key    quantum_efficiency
    Metadata Should Contain Key    full_well_capacity
    Metadata Should Contain Key    gain
    Metadata Value Should Be    bit_depth    14
    Metadata Value Should Be    exposure_time    0.05

Detector Captures Different Shapes
    [Documentation]    The detector should handle non-square grids.
    Create Default Detector
    Capture With Detector    height=16    width=32    wavelength=532e-9
    Image Should Be Digital Image
    Pixel Shape Should Be    16,32
