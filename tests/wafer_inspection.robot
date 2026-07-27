*** Settings ***
Documentation    Acceptance tests for UC7 Wafer Chip Misalignment Detection.
Library          WaferLibrary.py

*** Test Cases ***
Wafer Surface Has Detectable Features
    [Documentation]    A wafer surface height map should have features
    ...                detectable by template matching.
    Create Wafer Surface    shape=64x64    rows=4    cols=4    street=4
    Create Template Matcher
    Perform Template Matching
    Match Score Should Be Positive

Registration Detects Misalignment
    [Documentation]    Registration on height maps should report a
    ...                non-zero displacement for shifted surfaces.
    Create Wafer Surface    shape=48x48    rows=3    cols=3    street=4
    Create Registration Analyzer    max_offset=20
    Create Scattering
    Create Optical System
    Create Propagator
    Create Detector    exposure_time=1e-3    qe=0.5
    Create Bright Field Source
    Run Pipeline
    Perform Registration
    Registration Should Report Displacement

SPC Computes Cpk From Registration
    [Documentation]    SPC analyser should compute a positive Cpk from
    ...                multiple registration measurements on height maps.
    Create Wafer Surface    shape=48x48    rows=3    cols=3    street=4
    Create Registration Analyzer    max_offset=15
    Create SPC Analyzer    usl=5.0    lsl=-5.0
    Perform Registration On Height Map
    Perform Registration On Height Map
    Perform Registration On Height Map
    Perform SPC Analysis
    Cpk Should Be Positive
    SPC Should Report N Measurements    expected=3

Aligned Wafer Pipeline Runs Without Error
    [Documentation]    The full pipeline should run without errors
    ...                for an aligned wafer.
    Create Wafer Surface    shape=48x48    rows=3    cols=3    street=4
    Create Registration Analyzer    max_offset=20
    Create Bright Field Source
    Create Scattering
    Create Optical System
    Create Propagator
    Create Detector    exposure_time=1e-3    qe=0.5
    Run Pipeline
    Perform Registration
    Registration Should Report No Error
