"""Spectral analysis module for multi-spectral material identification.

Provides:
- :class:`SpectralAnalyzer` — computes band ratios, spectral angle
  mapper (SAM), and material classification from multi-spectral data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..analysis.base import AnalysisModule, AnalysisReport


@dataclass
class ReferenceSpectrum:
    """A reference spectral signature for material identification.

    Parameters
    ----------
    label : str
        Human-readable material name (e.g. ``"silicon"``, ``"gold"``).
    values : np.ndarray
        Spectral response at each wavelength channel (length N_λ).
    wavelengths : np.ndarray or None
        Wavelengths corresponding to *values*.  If ``None``, the
        reference is assumed to be on the same wavelength grid as the
        measurement.
    """

    label: str
    values: np.ndarray
    wavelengths: Optional[np.ndarray] = None


class SpectralAnalyzer(AnalysisModule):
    """Multi-spectral material classification and spectral analysis.

    Computes band-ratio metrics and the spectral angle mapper (SAM)
    between measured and reference spectra.

    Parameters
    ----------
    reference_library : list of ReferenceSpectrum
        Known material spectral signatures for classification.
    wavelengths : np.ndarray or None
        Wavelength grid for the measurement channels.  If ``None``,
        wavelengths are taken from the input metadata or data array.
    """

    def __init__(
        self,
        reference_library: Optional[List[ReferenceSpectrum]] = None,
        wavelengths: Optional[np.ndarray] = None,
    ):
        self.reference_library = reference_library or []
        self.wavelengths = wavelengths

    def add_reference(self, spectrum: ReferenceSpectrum):
        """Add a reference spectrum to the library."""
        self.reference_library.append(spectrum)

    def band_ratio(self, spectrum: np.ndarray, band_a: int, band_b: int) -> float:
        """Compute the ratio ``spectrum[band_a] / spectrum[band_b]``.

        Parameters
        ----------
        spectrum : np.ndarray
            Measured spectrum vector (length N_λ).
        band_a, band_b : int
            Channel indices.

        Returns
        -------
        float
            Band ratio.  Returns ``inf`` if denominator is zero.
        """
        if spectrum[band_b] == 0:
            return float("inf")
        return float(spectrum[band_a] / spectrum[band_b])

    @staticmethod
    def spectral_angle(r: np.ndarray, t: np.ndarray) -> float:
        """Spectral angle mapper (SAM) between two spectra.

        θ = arccos( (r · t) / (‖r‖ · ‖t‖) )

        Parameters
        ----------
        r : np.ndarray
            Reference spectrum vector.
        t : np.ndarray
            Test (measured) spectrum vector.

        Returns
        -------
        float
            Spectral angle in radians.  Returns 0 if either vector
            is zero.
        """
        r_norm = np.linalg.norm(r)
        t_norm = np.linalg.norm(t)
        if r_norm == 0.0 or t_norm == 0.0:
            return 0.0
        cos_angle = np.clip(np.dot(r, t) / (r_norm * t_norm), -1.0, 1.0)
        return float(np.arccos(cos_angle))

    @staticmethod
    def spectral_angle_map(
        data: np.ndarray, reference: np.ndarray
    ) -> np.ndarray:
        """Compute SAM for every pixel in a hyperspectral data cube.

        Parameters
        ----------
        data : np.ndarray
            Data cube ``(H, W, N_λ)``.
        reference : np.ndarray
            Reference spectrum ``(N_λ,)``.

        Returns
        -------
        np.ndarray
            Per-pixel SAM map ``(H, W)`` in radians.
        """
        r_norm = np.linalg.norm(reference)
        if r_norm == 0.0:
            return np.zeros(data.shape[:2], dtype=float)
        t_norm = np.linalg.norm(data, axis=2)
        dot = np.dot(data.reshape(-1, data.shape[2]), reference).reshape(data.shape[:2])
        cos_angle = np.clip(dot / (t_norm * r_norm), -1.0, 1.0)
        zero_mask = t_norm == 0.0
        cos_angle[zero_mask] = 1.0
        return np.arccos(cos_angle)

    def classify(
        self, data: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Classify each pixel by minimum SAM distance to reference spectra.

        Parameters
        ----------
        data : np.ndarray
            Data cube ``(H, W, N_λ)``.

        Returns
        -------
        labels : np.ndarray
            Integer class label per pixel ``(H, W)``.  -1 means
            unclassified (no references available).
        confidence : np.ndarray
            Confidence score per pixel ``(H, W)`` in [0, 1].
            1 - (sam / π) for the best-matching reference.
        """
        H, W = data.shape[:2]
        if not self.reference_library:
            return -np.ones((H, W), dtype=int), np.zeros((H, W), dtype=float)

        n_refs = len(self.reference_library)
        ref_vectors = np.array([r.values for r in self.reference_library])

        sams = np.zeros((H, W, n_refs), dtype=float)
        for i in range(n_refs):
            sams[:, :, i] = self.spectral_angle_map(data, ref_vectors[i])

        labels = np.argmin(sams, axis=2)
        min_sams = np.min(sams, axis=2)

        confidence = 1.0 - (min_sams / np.pi)
        confidence = np.clip(confidence, 0.0, 1.0)

        return labels, confidence

    def analyze(self, image) -> AnalysisReport:
        """Run spectral analysis on a digital image.

        Expects the input image to have a ``.pixels`` attribute that
        is a 2D (single-band) or 3D (multi-band, ``(H, W, N_λ)``)
        array.

        Returns
        -------
        AnalysisReport
            Measurements include:
            - ``n_channels`` — number of spectral bands detected
            - ``band_ratios`` — dict of ``"b{a}_{b}" → float``
            - ``classification`` — dict with ``labels`` and
              ``confidence`` arrays if references are available.
        """
        pixels = image.pixels if hasattr(image, "pixels") else np.asarray(image)

        if pixels.ndim == 2:
            data = pixels[..., np.newaxis]
        else:
            data = pixels

        N = data.shape[2]
        measurements: Dict[str, Any] = {"n_channels": N}

        if N >= 2:
            ratios = {}
            for a in range(min(N, 4)):
                for b in range(a + 1, min(N, 4)):
                    spec = data[data.shape[0] // 2, data.shape[1] // 2, :]
                    ratios[f"b{a}_{b}"] = self.band_ratio(spec, a, b)
            measurements["band_ratios"] = ratios

        if self.reference_library:
            labels, confidence = self.classify(data)
            measurements["classification"] = {
                "labels": labels,
                "confidence": confidence,
            }

        return AnalysisReport(measurements=measurements)
