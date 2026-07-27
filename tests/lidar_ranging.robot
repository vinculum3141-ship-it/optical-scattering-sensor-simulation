*** Settings ***
Documentation    Acceptance tests for UC6 LiDAR Range Finding.
Library          LiDARLibrary.py

*** Test Cases ***
Range Equation Computes Positive Power
    [Documentation]    The LiDAR range equation should produce
    ...                positive received power.
    Create Range Equation    power=10    aperture=0.1
    Compute Received Power    range_m=10    backscatter=1e-4
    Received Power Should Be Positive

Time Of Flight Propagation
    [Documentation]    Time-of-flight should be positive.
    Create TOF Propagator
    Compute TOF    range_m=15
    TOF Should Be Reasonable

SPAD Detects Photons
    [Documentation]    SPAD detector should register events.
    Create SPAD    dead_time=50e-9    pde=1.0    dcr=0
    Detect Photons
    Events Should Be Detected

Scanner Generates Points
    [Documentation]    Scanner should produce scan points.
    Create Scanner    pattern=raster
    Generate Scan Points    duration=0.1
    Scan Points Should Exist

Point Cloud From Scan
    [Documentation]    Scan points should convert to point cloud.
    Create Scanner    pattern=raster
    Generate Scan Points    duration=0.1
    Generate Cloud
    Cloud Should Have Points
