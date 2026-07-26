import numpy as np

from utils import heatmap


def test_heatmap_returns_string():
    arr = np.random.rand(8, 8)
    result = heatmap(arr)
    assert isinstance(result, str)
    assert len(result) > 0


def test_heatmap_includes_dimensions():
    arr = np.ones((4, 8))
    result = heatmap(arr, max_width=80)
    assert "4" in result
    assert "8" in result or "6" in result  # may be downsampled


def test_heatmap_uniform():
    arr = np.ones((4, 4))
    result = heatmap(arr, color=False)
    assert isinstance(result, str)


def test_heatmap_downsampling():
    arr = np.random.rand(100, 200)
    result = heatmap(arr, max_width=40, color=False)
    # Should be downsampled to ~40 wide
    lines = result.strip().split("\n")
    for line in lines[1:]:
        assert len(line) <= 45
