"""Robot Framework test library for multi-spectral material identification (UC2)."""

import numpy as np

from optical_metrology.illumination import (
    ChannelConfig,
    FilterWheelSource,
    LightField,
    LightSource,
    MultiChannelLightField,
    MultiSpectralSource,
)
from optical_metrology.analysis.spectral import ReferenceSpectrum, SpectralAnalyzer
from optical_metrology.detector.cfa import CFAConfig, CFADetector


class MultiSpectralLibrary:
    """Test library for UC2 multi-spectral material identification."""

    def __init__(self):
        self._source = None
        self._field = None
        self._analyzer = None
        self._result = None
        self._labels = None
        self._confidence = None

    def create_multispectral_source(self, *channel_args):
        """Create a multi-spectral source with wavelength, power triples.

        ``channel_args`` is a sequence of ``wavelength, power`` pairs.
        """
        channels = []
        args = list(channel_args)
        for i in range(0, len(args), 2):
            channels.append(ChannelConfig(
                wavelength=float(args[i]),
                power=float(args[i + 1]),
            ))
        self._source = MultiSpectralSource(channels)
        return self._source

    def create_filter_wheel_source(self, *channel_args):
        channels = []
        args = list(channel_args)
        for i in range(0, len(args), 2):
            channels.append(ChannelConfig(
                wavelength=float(args[i]),
                power=float(args[i + 1]),
            ))
        self._source = FilterWheelSource(channels)
        return self._source

    def create_spectral_analyzer(self, *ref_labels_values):
        """Create analyzer with reference spectra.

        Arguments are triples of ``label, v0, v1, ...``.
        """
        refs = []
        args = list(ref_labels_values)
        idx = 0
        while idx < len(args):
            label = str(args[idx])
            idx += 1
            values = []
            while idx < len(args) and not isinstance(args[idx], str):
                values.append(float(args[idx]))
                idx += 1
            refs.append(ReferenceSpectrum(label, np.array(values)))
        self._analyzer = SpectralAnalyzer(reference_library=refs)
        return self._analyzer

    def add_reference_spectrum(self, label, *values):
        vals = np.array([float(v) for v in values])
        self._analyzer.add_reference(ReferenceSpectrum(str(label), vals))

    def generate_light_field(self, height, width, spacing=1.0):
        shape = (int(height), int(width))
        self._field = self._source.generate_light_field(shape=shape, spacing=float(spacing))
        return self._field

    def number_of_channels_should_be(self, expected):
        actual = self._field.n_channels
        if actual != int(expected):
            raise AssertionError(f"Expected {expected} channels, got {actual}")

    def intensities_at_channel_should_be(self, channel, expected_val, tolerance=1e-10):
        f = self._field[int(channel)]
        actual = float(f.intensity.mean())
        expected = float(expected_val)
        if abs(actual - expected) > float(tolerance):
            raise AssertionError(
                f"Mean intensity channel {channel}: {actual} != {expected} (±{tolerance})"
            )

    def classify_data(self, *data_values):
        """Flattened data values as H*W*N array, then reshape."""
        data = np.array([float(v) for v in data_values])
        n = self._analyzer.reference_library[0].values.shape[0] if self._analyzer.reference_library else 1
        size = int(np.sqrt(len(data) // n))
        data = data.reshape(size, size, n)
        self._labels, self._confidence = self._analyzer.classify(data)

    def classification_labels_should_be(self, *expected):
        expected_arr = np.array([int(v) for v in expected])
        expected_arr = expected_arr.reshape(self._labels.shape)
        if not np.all(self._labels == expected_arr):
            raise AssertionError(
                f"Labels:\n{self._labels}\n!=\n{expected_arr}"
            )

    def classification_confidence_should_be_above(self, threshold):
        if float(self._confidence.min()) < float(threshold):
            raise AssertionError(
                f"Min confidence {self._confidence.min():.3f} < {threshold}"
            )

    def spectral_angle_should_be_close(self, r0, r1, r2, t0, t1, t2, expected, tolerance=1e-6):
        r = np.array([float(r0), float(r1), float(r2)])
        t = np.array([float(t0), float(t1), float(t2)])
        angle = SpectralAnalyzer.spectral_angle(r, t)
        if abs(angle - float(expected)) > float(tolerance):
            raise AssertionError(
                f"SAM {angle} != {expected} (±{tolerance})"
            )

    def band_ratio_should_be(self, band_a, band_b, expected, tolerance=1e-6):
        spectrum = self._field.intensity_stack()[
            self._field.shape[0] // 2, self._field.shape[1] // 2, :
        ]
        analyzer = SpectralAnalyzer()
        ratio = analyzer.band_ratio(spectrum, int(band_a), int(band_b))
        if abs(ratio - float(expected)) > float(tolerance):
            raise AssertionError(f"Band ratio {ratio} != {expected} (±{tolerance})")
