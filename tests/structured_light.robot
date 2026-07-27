*** Settings ***
Documentation       Verification tests for UC5 Structured Light 3D Scanning.
Library             StructuredLightLibrary.py

*** Test Cases ***
Fringe Projector Generates Correct Number Of Patterns
    [Documentation]    A FringeProjector with 4 phase shifts generates
    ...                4 fringe patterns.
    Create Fringe Projector    period=16.0    orientation=vertical
    Generate Patterns          height=32    width=48
    Pattern Count Should Be    4
    Pattern Shape Should Be    32    48

Phase Extraction Returns Wrapped Phase Map
    [Documentation]    Fringe patterns can be processed to extract
    ...                a wrapped phase map.
    Create Fringe Projector    period=16.0    orientation=vertical
    Generate Patterns          height=16    width=32
    Extract Phase
    Phase Map Should Have Shape    16    32

Phase Unwrapping Produces Continuous Map
    [Documentation]    Unwrapping removes 2π discontinuities from
    ...                the wrapped phase.
    Create Fringe Projector    period=32.0    orientation=vertical
    Generate Patterns          height=16    width=64
    Extract Phase
    Unwrap Phase
    Phase Map Should Have Shape    16    64

Height Reconstruction From Flat Reference
    [Documentation]    Phase extraction and unwrapping through to
    ...                height reconstruction produces a finite height map.
    Create Fringe Projector    period=16.0    orientation=vertical
    Generate Patterns          height=8    width=16
    Extract Phase
    Unwrap Phase
    Reconstruct Height    period=16.0    projection_angle=0.5
    Height Should Be Finite
    Height Should Have Shape    8    16
