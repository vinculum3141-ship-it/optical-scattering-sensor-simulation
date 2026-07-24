*** Settings ***
Documentation       Verification tests for the illumination package.
Library             IlluminationLibrary.py

*** Test Cases ***
Laser Has Default Polarization
    [Documentation]    A Laser created with only wavelength and power
    ...                should be unpolarized.
    Create Laser        wavelength=532e-9    power=5e-3
    Polarization Should Be    unpolarized

Laser Uses Monochromatic Spectrum
    [Documentation]    A Laser must attach a MonochromaticSpectrum.
    Create Laser        wavelength=532e-9    power=5e-3
    Spectrum Kind Should Be        monochromatic
    Spectrum Type Should Be        MonochromaticSpectrum

Laser Wavelength Is Stored Correctly
    [Documentation]    The wavelength passed to the constructor is
    ...                preserved and accessible.
    Create Laser        wavelength=450e-9    power=1e-3
    Wavelength Should Be Close    4.5e-07

LED Uses Gaussian Spectrum
    [Documentation]    An LED source must attach a GaussianSpectrum.
    Create LED          peak_wavelength=530e-9    width=25e-9    power=10e-3
    Spectrum Kind Should Be        gaussian
    Spectrum Type Should Be        GaussianSpectrum

LED Default Beam Profile Is Gaussian
    [Documentation]    LED defaults to a GaussianBeamProfile.
    Create LED          peak_wavelength=530e-9    width=25e-9    power=10e-3
    Beam Profile Type Should Be    GaussianBeamProfile

Sunlight Uses Blackbody Spectrum
    [Documentation]    Sunlight source attaches a BlackbodySpectrum.
    Create Sunlight     temperature=5778.0    power=1.0
    Spectrum Kind Should Be        blackbody
    Spectrum Type Should Be        BlackbodySpectrum

BroadbandLamp Uses Broadband Spectrum
    [Documentation]    BroadbandLamp attaches a BroadbandSpectrum.
    Create Broadband Lamp    wl_min=400e-9    wl_max=700e-9    power=10.0
    Spectrum Kind Should Be        broadband
    Spectrum Type Should Be        BroadbandSpectrum

Generate Light Field Shape
    [Documentation]    Source.generate_light_field() returns the correct
    ...                grid dimensions.
    Create Laser        wavelength=532e-9    power=5e-3
    Generate Light Field    height=16    width=16    spacing=0.5
    Field Should Have Shape            16,16
    Field Direction Should Have Shape  16,16,3

Light Field Wavelength Matches Source
    [Documentation]    The wavelength in the generated LightField is the
    ...                same as the source wavelength.
    Create Laser        wavelength=633e-9    power=1e-3
    Generate Light Field    height=4    width=4    spacing=1.0
    Field Wavelength Should Be    6.33e-07

Light Field Polarization Matches Source
    [Documentation]    The polarization state is carried over to the
    ...                generated LightField.
    Create Custom Source    wavelength=532e-9    power=1e-3
    ...                     polarization=linear    profile_type=gaussian
    Generate Light Field    height=4    width=4    spacing=1.0
    Field Polarization Should Be    linear

Light Field Phase Is None By Default
    [Documentation]    Phase is None when no phase mask is provided.
    Create Laser        wavelength=532e-9    power=5e-3
    Generate Light Field    height=8    width=8    spacing=0.5
    Field Phase Should Be None

Direction Vectors Are Unit Length
    [Documentation]    Propagation direction vectors in the light field
    ...                should be normalised.
    Create Laser        wavelength=532e-9    power=5e-3
    Generate Light Field    height=8    width=8    spacing=1.0
    Direction Vector Should Be Normalized

Gaussian Beam Profile Intensity Varies Across Grid
    [Documentation]    A Gaussian profile produces higher intensity at
    ...                the centre and lower at the edges.
    Create Laser        wavelength=532e-9    power=5e-3    w0=1.0
    Generate Light Field    height=8    width=8    spacing=0.5
    Field Intensity Range Should Be    min_val=0    max_val=0.001839    tolerance=1e-5

Laser Default Divergence Is 1 Mrad
    [Documentation]    A plain Laser should have divergence = 1e-3 rad.
    Create Laser        wavelength=532e-9    power=5e-3
    Laser Divergence Should Be    0.001

Custom Source With TopHat Profile
    [Documentation]    A LightSource can be constructed with a
    ...                TopHatBeamProfile.
    Create Custom Source    wavelength=532e-9    power=1e-3
    ...                     polarization=unpolarized    profile_type=tophat
    Beam Profile Type Should Be    TopHatBeamProfile
    Generate Light Field    height=4    width=4    spacing=1.0
    Field Intensity Range Should Be    min_val=0.001    max_val=0.001

Custom Source With Uniform Profile
    [Documentation]    A LightSource with UniformBeamProfile produces
    ...                constant intensity.
    Create Custom Source    wavelength=532e-9    power=2e-3
    ...                     polarization=unpolarized    profile_type=uniform
    Beam Profile Type Should Be    UniformBeamProfile
    Generate Light Field    height=4    width=4    spacing=1.0
    Field Intensity Range Should Be    min_val=0.002    max_val=0.002
