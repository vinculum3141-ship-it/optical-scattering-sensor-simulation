*** Settings ***
Documentation       Verification tests for the scattering package.
Library             ScatteringLibrary.py

*** Test Cases ***
Lambertian Model Can Be Created
    [Documentation]    A LambertianScattering model stores the albedo.
    Create Lambertian Model    albedo=0.8
    Model Type Should Be       LambertianScattering

Lambertian Evaluate Returns ScatteredField
    [Documentation]    LambertianScattering.evaluate() returns a
    ...                properly-shaped ScatteredField.
    ${intensity}    Evaluate    [[1.0, 1.0], [1.0, 1.0]]
    ${direction}    Evaluate    [[[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]], [[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]]]
    ${normals}      Evaluate    [[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]]
    Evaluate Lambertian    intensity_arr=${intensity}
    ...                   direction_arr=${direction}
    ...                   normals_arr=${normals}
    ...                   view_str=0,0,1
    ...                   albedo=0.8
    Result Should Be Scattered Field
    Radiance Shape Should Be    2,2
    Outgoing Shape Should Be    2,2,3
    Radiance Should Be Non Negative

Lambertian Normal Incidence Gives Albedo
    [Documentation]    When the light propagates toward the surface (-z)
    ...                and the normal points up (+z), the dot product of
    ...                to-light (+z) with normal (+z) = 1, so radiance = albedo.
    ${intensity}    Evaluate    [[1.0, 1.0], [1.0, 1.0]]
    ${direction}    Evaluate    [[[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]], [[0.0, 0.0, -1.0], [0.0, 0.0, -1.0]]]
    ${normals}      Evaluate    [[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]]
    Evaluate Lambertian    intensity_arr=${intensity}
    ...                   direction_arr=${direction}
    ...                   normals_arr=${normals}
    ...                   view_str=0,0,1
    ...                   albedo=0.7
    Radiance Should Be All Close To    0.7

Lambertian Grazing Angle Gives Zero
    [Documentation]    When the light direction is perpendicular to the
    ...                normal, cosine = 0 and radiance = 0.
    ${intensity}    Evaluate    [[1.0, 1.0], [1.0, 1.0]]
    ${direction}    Evaluate    [[[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]], [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]]
    ${normals}      Evaluate    [[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]]
    Evaluate Lambertian    intensity_arr=${intensity}
    ...                   direction_arr=${direction}
    ...                   normals_arr=${normals}
    ...                   view_str=0,0,1
    ...                   albedo=0.8
    Radiance Should Be All Close To    0.0

Lambertian Back-Surface Gives Zero
    [Documentation]    When the light comes from behind the surface
    ...                (propagating +z, same as normal), to-light = -z,
    ...                dot(-z, +z) = -1, clipped to 0.
    ${intensity}    Evaluate    [[1.0, 1.0], [1.0, 1.0]]
    ${direction}    Evaluate    [[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]]
    ${normals}      Evaluate    [[[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]]
    Evaluate Lambertian    intensity_arr=${intensity}
    ...                   direction_arr=${direction}
    ...                   normals_arr=${normals}
    ...                   view_str=0,0,1
    ...                   albedo=0.8
    Radiance Should Be All Close To    0.0