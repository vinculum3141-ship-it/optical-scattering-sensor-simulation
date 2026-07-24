import numpy as np

from analysis import AnalysisReport, HistogramAnalyzer, ImageAnalyzer
from detector import DigitalImage


def test_histogram_analyzer_returns_report():
    image = DigitalImage(
        pixels=np.array([[0, 1, 2], [3, 4, 5]], dtype=np.uint16),
        metadata={"bit_depth": 8},
    )
    analyzer = HistogramAnalyzer()
    report = analyzer.analyze(image)

    assert isinstance(report, AnalysisReport)
    assert report.histogram is not None
    assert report.histogram.shape == (6,)
    assert report.measurements["mean_intensity"] > 0.0
