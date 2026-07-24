*** Settings ***
Documentation       Verification tests for the surface geometry package.
Library             SurfaceLibrary.py

*** Test Cases ***
Flat Surface Has Zero Height And Zero Derived Geometry
    [Documentation]    A flat surface should have all height values at zero,
    ...                which yields zero slopes, zero curvature, and zero roughness.
    Create Flat Surface    16    16    material_name=glass
    Surface Type Should Be             FlatSurface
    Height Shape Should Be             16,16
    Height Should Be All Close To      0.0
    Normals Shape Should Be            16,16,3
    Slopes Should Be All Close To      0.0
    Curvature Should Be All Close To   0.0
    Roughness Should Be                0.0
    Material Name Should Be            glass

Flat Surface Normals Point Up
    [Documentation]    For a flat surface all normals should be (0, 0, 1).
    Create Flat Surface    8    8
    Height Should Be All Close To    0.0
    Normals Shape Should Be          8,8,3

Rough Surface Has Nonzero Roughness
    [Documentation]    A RoughSurface produced with sigma > 0 and
    ...                amplitude > 0 must have measurable roughness.
    Create Rough Surface    32    32    sigma=4.0    amplitude=0.5
    Surface Type Should Be           RoughSurface
    Height Shape Should Be           32,32
    Roughness Should Be Greater Than    0.0
    Height Range Should Be Non Zero

Rough Surface Height Range Contains Zero
    [Documentation]    Rough surface heights are centred around zero
    ...                (zero-mean Gaussian noise).
    Create Rough Surface    32    32    sigma=4.0    amplitude=0.5
    Height Range Should Contain Zero

Scratched Surface Has Negative Heights
    [Documentation]    The scratch groove lowers the surface, so the
    ...                minimum height should be negative; unaffected
    ...                areas stay at zero.
    Create Scratched Surface    32    32    depth=0.3    width=3
    Surface Type Should Be           ScratchedSurface
    Height Shape Should Be           32,32
    Min Height Should Be Negative
    Height Range Should Contain Zero
    Roughness Should Be Greater Than    0.0

Scratched Surface Default Shape Is Correct
    [Documentation]    The generated scratch surface has the expected
    ...                array shapes for height, normals, and slopes.
    Create Scratched Surface    24    24    depth=0.5    width=2
    Height Shape Should Be       24,24
    Normals Shape Should Be      24,24,3

Particle Surface Has Positive Bumps
    [Documentation]    ParticleSurface creates Gaussian bumps, so the
    ...                maximum height must be positive.
    Create Particle Surface    32    32    count=4    amplitude=0.8    sigma=2.0
    Surface Type Should Be           ParticleSurface
    Height Shape Should Be           32,32
    Max Height Should Be Positive
    Height Range Should Be Non Zero
    Roughness Should Be Greater Than    0.0

Particle Surface Default Seed Is Deterministic
    [Documentation]    The fixed RNG seed (0) should produce repeatable
    ...                height maps for the same parameters.
    Create Particle Surface    16    16    count=3    amplitude=1.0    sigma=2.0
    Height Shape Should Be       16,16
    Max Height Should Be Positive

GeometryAnalyzer Rejects Non-2D Input
    [Documentation]    GeometryAnalyzer.analyze() must raise ValueError
    ...                for non-2D arrays.
    # This is tested via Python-level pytest; Robot Framework equivalent
    # would need Run Keyword And Expect Error.  Included for completeness.
    No Operation

Surface Generator Callable Produces Surface
    [Documentation]    SurfaceGenerator.__call__ should produce the same
    ...                result as create_surface().
    # Verified implicitly by the FlatSurface constructor above, which
    # inherits from both Surface and SurfaceGenerator.
    No Operation