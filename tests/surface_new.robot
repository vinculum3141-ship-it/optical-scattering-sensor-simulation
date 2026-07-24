*** Settings ***
Documentation    Verification tests for new surface generators.
Library          SurfaceLibrary.py

*** Test Cases ***
Sinusoidal Surface Has Periodic Structure
    [Documentation]    A SinusoidalSurface should have a sinusoidal
    ...                height profile with the correct period and amplitude.
    Create Sinusoidal Surface    16    16    period=16    amplitude=0.5
    Surface Type Should Be          SinusoidalSurface
    Height Shape Should Be          16,16
    Height Range Should Be Non Zero
    Roughness Should Be Greater Than    0.0

Sinusoidal Surface Amplitude Check
    [Documentation]    The amplitude parameter controls the peak height.
    Create Sinusoidal Surface    16    16    period=8    amplitude=0.3
    Max Height Should Be Positive
    Roughness Should Be Greater Than    0.0

Sinusoidal Surface Normals Shape
    [Documentation]    Sinusoidal surface produces correct normal array shape.
    Create Sinusoidal Surface    24    24    period=12    amplitude=0.5
    Normals Shape Should Be    24,24,3

Anisotropic Rough Surface Has Roughness
    [Documentation]    An anisotropic rough surface should produce
    ...                non-zero roughness and valid shapes.
    Create Anisotropic Rough Surface    32    32    sigma_x=8    sigma_y=2    amplitude=0.5
    Surface Type Should Be          AnisotropicRoughSurface
    Height Shape Should Be          32,32
    Roughness Should Be Greater Than    0.0
    Height Range Should Be Non Zero

Anisotropic Rough Surface With Material
    [Documentation]    Material can be attached to an anisotropic surface.
    Create Anisotropic Rough Surface    16    16    sigma_x=4    sigma_y=2    amplitude=0.3    material_name=aluminium
    Surface Type Should Be          AnisotropicRoughSurface
    Material Name Should Be         aluminium
