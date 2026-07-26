*** Settings ***
Documentation    Verification tests for new scattering models (Phong, Oren-Nayar).
Library          ScatteringLibrary.py

*** Test Cases ***
Phong Model Can Be Created
    [Documentation]    A PhongScattering model stores albedos and shininess.
    Create Phong Model    diffuse_albedo=0.6    specular_albedo=0.4    shininess=32
    Model Type Should Be    PhongScattering

Phong Normal Incidence Combines Diffuse And Specular
    [Documentation]    With aligned light and view, both diffuse and
    ...                specular terms contribute: 0.6 + 0.4 = 1.0.
    ${intensity}    Evaluate    [[1.0, 1.0], [1.0, 1.0]]
    ${direction}    Evaluate    [[[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]], [[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]]]
    ${normals}      Evaluate    [[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]]
    Evaluate Phong    intensity_arr=${intensity}
    ...               direction_arr=${direction}
    ...               normals_arr=${normals}
    ...               view_str=0,0,1
    ...               diffuse=0.6    specular=0.4    shininess=32
    Result Should Be Scattered Field
    Radiance Shape Should Be    2,2
    Radiance Should Be All Close To    1.0

Phong Grazing Angle Gives Zero
    [Documentation]    When the light is perpendicular to the normal,
    ...                both diffuse and specular are zero.
    ${intensity}    Evaluate    [[1.0, 1.0], [1.0, 1.0]]
    ${direction}    Evaluate    [[[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]], [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]]
    ${normals}      Evaluate    [[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]]
    Evaluate Phong    intensity_arr=${intensity}
    ...               direction_arr=${direction}
    ...               normals_arr=${normals}
    ...               view_str=0,0,1
    ...               diffuse=0.5    specular=0.5    shininess=32
    Radiance Should Be All Close To    0.0

OrenNayar Model Can Be Created
    [Documentation]    An OrenNayarScattering model stores albedo and roughness.
    Create OrenNayar Model    albedo=0.8    roughness=0.5
    Model Type Should Be    OrenNayarScattering

OrenNayar Smooth Approaches Lambertian
    [Documentation]    With roughness near zero, Oren-Nayar approaches
    ...                Lambertian: radiance ≈ albedo at normal incidence.
    ${intensity}    Evaluate    [[1.0, 1.0], [1.0, 1.0]]
    ${direction}    Evaluate    [[[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]], [[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]]]
    ${normals}      Evaluate    [[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]]
    Evaluate OrenNayar    intensity_arr=${intensity}
    ...                   direction_arr=${direction}
    ...                   normals_arr=${normals}
    ...                   view_str=0,0,1
    ...                   albedo=0.8    roughness=0.01
    Result Should Be Scattered Field
    Radiance Shape Should Be    2,2
    Radiance Should Be Non Negative
