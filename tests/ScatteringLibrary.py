"""Robot Framework test library for the scattering package."""

import numpy as np

from optical_metrology.illumination import LightField
from optical_metrology.scattering import (
    LambertianScattering,
    OrenNayarScattering,
    PhongScattering,
    CookTorranceScattering,
    ScatteredField,
)
from optical_metrology.surface import Material, Surface


class ScatteringLibrary:
    """Test library providing keywords for scattering model verification."""

    def create_lambertian_model(self, albedo):
        self._model = LambertianScattering(albedo=float(albedo))
        return self._model

    def create_scattered_field(self, radiance, outgoing_str, polarization=None):
        """Create a ScatteredField directly for inspection (not from evaluation)."""
        h, w = radiance.shape[:2]
        out = np.zeros((h, w, 3), dtype=float)
        parts = [float(x) for x in outgoing_str.split(",")]
        out[...] = np.array(parts)
        self._field = ScatteredField(
            radiance=np.asarray(radiance, dtype=float),
            outgoing_direction=out,
            polarization=polarization,
        )
        return self._field

    def evaluate_lambertian(self, intensity_arr, direction_arr, normals_arr, view_str, albedo):
        """Run LambertianScattering.evaluate() with raw arrays."""
        intensity_arr = np.asarray(intensity_arr, dtype=float)
        direction_arr = np.asarray(direction_arr, dtype=float)
        normals_arr = np.asarray(normals_arr, dtype=float)
        h, w = intensity_arr.shape[:2]
        lightfield = LightField(
            intensity=np.asarray(intensity_arr, dtype=float),
            direction=np.asarray(direction_arr, dtype=float),
            wavelength=532e-9,
            polarization=None,
        )
        surface = Surface(
            height=np.zeros((h, w), dtype=float),
            normals=np.asarray(normals_arr, dtype=float),
            curvature=np.zeros((h, w), dtype=float),
            slope_x=np.zeros((h, w), dtype=float),
            slope_y=np.zeros((h, w), dtype=float),
            roughness=0.0,
            material=Material(),
        )
        view = np.array([float(x) for x in view_str.split(",")])
        model = LambertianScattering(albedo=float(albedo))
        self._result = model.evaluate(lightfield, surface, view)
        return self._result

    def result_should_be_scattered_field(self):
        if not isinstance(self._result, ScatteredField):
            raise AssertionError(
                f"Expected ScatteredField, got {type(self._result)}"
            )

    def radiance_shape_should_be(self, expected_str):
        expected = tuple(int(x) for x in expected_str.split(","))
        if self._result.radiance.shape != expected:
            raise AssertionError(
                f"Radiance shape {self._result.radiance.shape} != {expected}"
            )

    def outgoing_shape_should_be(self, expected_str):
        expected = tuple(int(x) for x in expected_str.split(","))
        if self._result.outgoing_direction.shape != expected:
            raise AssertionError(
                f"Outgoing shape {self._result.outgoing_direction.shape} != {expected}"
            )

    def radiance_should_be_all_close_to(self, expected, tolerance=1e-6):
        if not np.allclose(self._result.radiance, float(expected), atol=float(tolerance)):
            raise AssertionError(
                f"Radiance not close to {expected} (tolerance={tolerance})"
            )

    def radiance_should_be_non_negative(self):
        if np.any(self._result.radiance < 0.0):
            raise AssertionError("Radiance contains negative values")

    def model_type_should_be(self, expected_type):
        actual = type(self._model).__name__
        if actual != expected_type:
            raise AssertionError(f"Expected {expected_type}, got {actual}")

    def create_phong_model(self, diffuse_albedo, specular_albedo, shininess):
        self._model = PhongScattering(
            diffuse_albedo=float(diffuse_albedo),
            specular_albedo=float(specular_albedo),
            shininess=float(shininess),
        )
        return self._model

    def evaluate_phong(self, intensity_arr, direction_arr, normals_arr, view_str, diffuse, specular, shininess):
        intensity_arr = np.asarray(intensity_arr, dtype=float)
        direction_arr = np.asarray(direction_arr, dtype=float)
        normals_arr = np.asarray(normals_arr, dtype=float)
        h, w = intensity_arr.shape[:2]
        lightfield = LightField(
            intensity=np.asarray(intensity_arr, dtype=float),
            direction=np.asarray(direction_arr, dtype=float),
            wavelength=532e-9,
            polarization=None,
        )
        surface = Surface(
            height=np.zeros((h, w), dtype=float),
            normals=np.asarray(normals_arr, dtype=float),
            curvature=np.zeros((h, w), dtype=float),
            slope_x=np.zeros((h, w), dtype=float),
            slope_y=np.zeros((h, w), dtype=float),
            roughness=0.0,
            material=Material(),
        )
        view = np.array([float(x) for x in view_str.split(",")])
        model = PhongScattering(
            diffuse_albedo=float(diffuse),
            specular_albedo=float(specular),
            shininess=float(shininess),
        )
        self._result = model.evaluate(lightfield, surface, view)
        return self._result

    def create_orennayar_model(self, albedo, roughness):
        self._model = OrenNayarScattering(albedo=float(albedo), roughness=float(roughness))
        return self._model

    def evaluate_orennayar(self, intensity_arr, direction_arr, normals_arr, view_str, albedo, roughness):
        intensity_arr = np.asarray(intensity_arr, dtype=float)
        direction_arr = np.asarray(direction_arr, dtype=float)
        normals_arr = np.asarray(normals_arr, dtype=float)
        h, w = intensity_arr.shape[:2]
        lightfield = LightField(
            intensity=np.asarray(intensity_arr, dtype=float),
            direction=np.asarray(direction_arr, dtype=float),
            wavelength=532e-9,
            polarization=None,
        )
        surface = Surface(
            height=np.zeros((h, w), dtype=float),
            normals=np.asarray(normals_arr, dtype=float),
            curvature=np.zeros((h, w), dtype=float),
            slope_x=np.zeros((h, w), dtype=float),
            slope_y=np.zeros((h, w), dtype=float),
            roughness=0.0,
            material=Material(),
        )
        view = np.array([float(x) for x in view_str.split(",")])
        model = OrenNayarScattering(albedo=float(albedo), roughness=float(roughness))
        self._result = model.evaluate(lightfield, surface, view)
        return self._result