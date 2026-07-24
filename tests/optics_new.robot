*** Settings ***
Documentation    Verification tests for new optics models (AiryPSF).
Library          OpticsLibrary.py

*** Test Cases ***
Airy PSF Kernel Is Normalised
    [Documentation]    The Airy PSF kernel must sum to 1 (energy conservation).
    Create Airy PSF    wavelength=532e-9    na=0.25    pixel_size=5e-6
    Generate Kernel    size=31
    Kernel Should Be Normalised
    Kernel Shape Should Be    31,31

Airy PSF Centre Is Peak
    [Documentation]    The central pixel of an Airy disk should be the maximum.
    Create Airy PSF    wavelength=532e-9    na=0.25    pixel_size=5e-6
    Generate Kernel    size=21
    Centre Should Be Maximum

Airy PSF Is Symmetric
    [Documentation]    The Airy disk should be radially symmetric.
    Create Airy PSF    wavelength=532e-9    na=0.25    pixel_size=5e-6
    Generate Kernel    size=21
    Kernel Should Be Symmetric
