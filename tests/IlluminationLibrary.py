"""Robot Framework test library for the illumination package."""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so that ``import illumination``
# works regardless of how robot is invoked.
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np

from illumination import (
    BroadbandLamp,
    LED,
    Laser,
    LightField,
    LightSource,
    MonochromaticSpectrum,
    GaussianSpectrum,
    BlackbodySpectrum,
    BroadbandSpectrum,
    Sunlight,
    GaussianBeamProfile,
    UniformBeamProfile,
    TopHatBeamProfile,
    PolarizationState,
)


class IlluminationLibrary:
    """Test library providing keywords for illumination model verification."""

    def create_laser(self, wavelength, power, w0=None):
        laser = Laser(wavelength=float(wavelength), power=float(power))
        if w0 is not None:
            laser.beam_profile = GaussianBeamProfile(w0=float(w0))
        self._source = laser
        return self._source

    def create_led(self, peak_wavelength, width, power):
        self._source = LED(
            peak_wavelength=float(peak_wavelength),
            width=float(width),
            power=float(power),
        )
        return self._source

    def create_sunlight(self, temperature, power):
        self._source = Sunlight(temperature=float(temperature), power=float(power))
        return self._source

    def create_broadband_lamp(self, wl_min, wl_max, power):
        self._source = BroadbandLamp(
            wavelength_range=(float(wl_min), float(wl_max)),
            power=float(power),
        )
        return self._source

    def create_custom_source(self, wavelength, power, polarization, profile_type):
        pol = PolarizationState(polarization)
        if profile_type == "gaussian":
            profile = GaussianBeamProfile(w0=1.0)
        elif profile_type == "uniform":
            profile = UniformBeamProfile()
        elif profile_type == "tophat":
            profile = TopHatBeamProfile()
        else:
            raise ValueError(f"Unknown profile: {profile_type}")
        self._source = LightSource(
            wavelength=float(wavelength),
            power=float(power),
            polarization=pol,
            beam_profile=profile,
        )
        return self._source

    def source_type_should_be(self, expected_type):
        actual = type(self._source).__name__
        if actual != expected_type:
            raise AssertionError(f"Expected {expected_type}, got {actual}")

    def spectrum_kind_should_be(self, expected_kind):
        kind = self._source.spectral_distribution().kind
        if kind != expected_kind:
            raise AssertionError(f"Expected spectrum kind {expected_kind}, got {kind}")

    def spectrum_type_should_be(self, expected_type):
        actual = type(self._source.spectral_distribution()).__name__
        if actual != expected_type:
            raise AssertionError(f"Expected {expected_type}, got {actual}")

    def polarization_should_be(self, expected_kind):
        kind = self._source.polarization.kind
        if kind != expected_kind:
            raise AssertionError(f"Expected polarization {expected_kind}, got {kind}")

    def wavelength_should_be_close(self, expected, tolerance=1e-12):
        diff = abs(self._source.wavelength - float(expected))
        if diff > float(tolerance):
            raise AssertionError(
                f"Wavelength {self._source.wavelength} != {expected} (±{tolerance})"
            )

    def power_should_be_close(self, expected, tolerance=1e-12):
        diff = abs(self._source.power - float(expected))
        if diff > float(tolerance):
            raise AssertionError(f"Power {self._source.power} != {expected} (±{tolerance})")

    def generate_light_field(self, height, width, spacing):
        shape = (int(height), int(width))
        self._field = self._source.generate_light_field(shape=shape, spacing=float(spacing))
        return self._field

    def field_should_have_shape(self, expected_shape_str):
        expected = tuple(int(x) for x in expected_shape_str.split(","))
        if self._field.intensity.shape != expected:
            raise AssertionError(
                f"Intensity shape {self._field.intensity.shape} != {expected}"
            )

    def field_direction_should_have_shape(self, expected_shape_str):
        expected = tuple(int(x) for x in expected_shape_str.split(","))
        if self._field.direction.shape != expected:
            raise AssertionError(
                f"Direction shape {self._field.direction.shape} != {expected}"
            )

    def field_intensity_range_should_be(self, min_val, max_val, tolerance=1e-6):
        actual_min = float(self._field.intensity.min())
        actual_max = float(self._field.intensity.max())
        if abs(actual_min - float(min_val)) > float(tolerance):
            raise AssertionError(
                f"Intensity min {actual_min} != {min_val} (tolerance {tolerance})"
            )
        if abs(actual_max - float(max_val)) > float(tolerance):
            raise AssertionError(
                f"Intensity max {actual_max} != {max_val} (tolerance {tolerance})"
            )

    def field_wavelength_should_be(self, expected):
        if abs(self._field.wavelength - float(expected)) > 1e-12:
            raise AssertionError(
                f"Field wavelength {self._field.wavelength} != {expected}"
            )

    def field_polarization_should_be(self, expected_kind):
        kind = self._field.polarization.kind
        if kind != expected_kind:
            raise AssertionError(
                f"Field polarization {kind} != {expected_kind}"
            )

    def field_phase_should_be_none(self):
        if self._field.phase is not None:
            raise AssertionError("Expected phase=None")

    def direction_vector_should_be_normalized(self):
        norms = np.linalg.norm(self._field.direction, axis=-1)
        if not np.allclose(norms, 1.0):
            raise AssertionError("Direction vectors are not unit length")

    def beam_profile_type_should_be(self, expected_type):
        actual = type(self._source.beam_profile).__name__
        if actual != expected_type:
            raise AssertionError(f"Expected beam profile {expected_type}, got {actual}")

    def laser_divergence_should_be(self, expected):
        diff = abs(self._source.divergence - float(expected))
        if diff > 1e-12:
            raise AssertionError(
                f"Divergence {self._source.divergence} != {expected}"
            )

    def source_name(self):
        return type(self._source).__name__

    def field_summary(self):
        fi = self._field
        return (
            f"intensity={fi.intensity.shape}, "
            f"direction={fi.direction.shape}, "
            f"wavelength={fi.wavelength:.3e}m, "
            f"polarization={fi.polarization.kind}"
        )
