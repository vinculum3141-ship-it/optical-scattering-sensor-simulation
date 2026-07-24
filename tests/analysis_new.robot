*** Settings ***
Documentation    Verification tests for new analysis modules.
Library          AnalysisLibrary.py

*** Test Cases ***
Contrast Analyzer Returns Measurements
    [Documentation]    ContrastAnalyzer should compute RMS, Michelson,
    ...                and Weber contrast from a known image.
    Create Contrast Analyzer
    Analyze Image    height=8    width=8    bit_depth=12
    Result Should Be Analysis Report
    Measurement Should Exist    rms_contrast
    Measurement Should Exist    michelson_contrast
    Measurement Should Exist    weber_contrast

Contrast Of Uniform Image Is Zero
    [Documentation]    A uniform image should have zero contrast.
    Create Contrast Analyzer
    Analyze Uniform Image    height=8    width=8    value=2048    bit_depth=12
    Result Should Be Analysis Report
    Measurement Should Be Close    rms_contrast    0.0
    Measurement Should Be Close    michelson_contrast    0.0

Saturation Analyzer Detects Saturated Pixels
    [Documentation]    SaturationAnalyzer should detect pixels at
    ...                the maximum digital value.
    Create Saturation Analyzer    threshold=0.99
    Analyze Image With Saturation    height=8    width=8    saturation_fraction=0.1    bit_depth=12
    Result Should Be Analysis Report
    Measurement Should Exist    saturated_pixels
    Measurement Should Exist    saturation_fraction

Saturation Analyzer Clean Image
    [Documentation]    An image with no saturated pixels should report
    ...                zero saturated pixels.
    Create Saturation Analyzer    threshold=0.99
    Analyze Uniform Image    height=8    width=8    value=100    bit_depth=12
    Result Should Be Analysis Report
    Measurement Should Be Close    saturated_pixels    0

Image Analyzer With Multiple New Modules
    [Documentation]    ImageAnalyzer can combine ContrastAnalyzer and
    ...                SaturationAnalyzer in one pass.
    Create Combined Analyzer
    Analyze Image    height=8    width=8    bit_depth=12
    Result Should Be Analysis Report
    Measurement Should Exist    rms_contrast
    Measurement Should Exist    saturated_pixels
