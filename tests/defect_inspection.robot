*** Settings ***
Documentation    Acceptance tests for UC1 Surface Defect Inspection.
Library          DefectInspectionLibrary.py

*** Test Cases ***
Bright Field Detects Scratch
    [Documentation]    A scratched surface under bright-field illumination
    ...                should produce detectable defects.
    Create Defect Analyzer    threshold=0.1    min_area=2
    Create Scratched Surface    shape=16x16    depth=0.5    width=3
    Create Bright Field Source
    Create Scattering
    Create Optical System
    Create Propagator
    Create Detector    exposure_time=1e-3    qe=0.5
    Run Pipeline
    Analyze For Defects
    Defects Should Be Detected

Dark Field Highlights Scratch
    [Documentation]    Dark-field illumination should also highlight
    ...                a scratch.
    Create Defect Analyzer    threshold=0.05    min_area=2
    Create Scratched Surface    shape=16x16    depth=0.5    width=3
    Create Dark Field Source
    Create Scattering
    Create Optical System
    Create Propagator
    Create Detector    exposure_time=1e-3    qe=0.5
    Run Pipeline
    Analyze For Defects
    Defects Should Be Detected

Clean Surface Passes Inspection
    [Documentation]    A defect-free surface should pass pass/fail.
    Create Defect Analyzer    threshold=1.5    min_area=2
    Create Flat Surface    shape=8x8
    Create Bright Field Source
    Create Scattering
    Create Optical System
    Create Propagator
    Create Detector    exposure_time=1e-3    qe=0.5
    Run Pipeline
    Analyze For Defects
    No Defects Should Be Detected
    Pass Fail Should Pass

Dent Surface Is Detectable
    [Documentation]    A dent should be detected as a defect.
    Create Defect Analyzer    threshold=0.02    min_area=2
    Create Dent Surface    shape=16x16    depth=0.5    radius=3
    Create Bright Field Source
    Create Scattering
    Create Optical System
    Create Propagator
    Create Detector    exposure_time=1e-3    qe=0.5
    Run Pipeline
    Analyze For Defects
    Defects Should Be Detected

Scratched Surface Has Roughness
    [Documentation]    A scratched surface should have non-zero roughness.
    Create Scratched Surface    shape=16x16    depth=0.5    width=3
    Surface Roughness Should Be Positive
