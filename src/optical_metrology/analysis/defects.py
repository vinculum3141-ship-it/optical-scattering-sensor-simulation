"""Defect detection and classification for wafer/chip inspection (UC1).

Provides blob finding (connected-component analysis), scratch
segmentation, defect classification, and pass/fail decision logic.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from .base import AnalysisModule, AnalysisReport


class DefectAnalyzer(AnalysisModule):
    """Detect, characterise, and classify defects in an inspection image.

    Parameters
    ----------
    threshold : float
        Fractional intensity threshold above which pixels are considered
        defect candidates (relative to the image maximum).  Lower values
        detect fainter defects but increase false positives.
    min_area : int
        Minimum area in pixels for a connected component to be
        considered a defect.
    max_area : int
        Maximum area in pixels (larger regions are ignored as
        background).
    connectivity : int
        Pixel connectivity for connected-component labelling.
        ``4`` (edges) or ``8`` (edges + corners).
    reference_image : ndarray or None
        Defect-free reference.  If provided, defect candidates are
        identified by deviation from this reference rather than by
        absolute threshold.
    """

    def __init__(
        self,
        threshold: float = 0.1,
        min_area: int = 3,
        max_area: int = 10000,
        connectivity: int = 8,
        reference_image=None,
    ):
        self.threshold = float(threshold)
        self.min_area = min_area
        self.max_area = max_area
        self.connectivity = connectivity
        self._reference = (
            np.asarray(reference_image, dtype=float)
            if reference_image is not None
            else None
        )

    def analyze(self, image) -> AnalysisReport:
        pixels = np.asarray(image.pixels, dtype=float)

        if self._reference is not None:
            diff = np.abs(pixels - self._reference)
        else:
            diff = pixels

        norm = diff / np.max(diff) if np.max(diff) > 0 else diff

        binary = norm > self.threshold

        labels, num_features = self._label(binary)
        defects = self._extract_defects(labels, num_features, pixels, binary)

        defect_count = len(defects)
        has_defects = defect_count > 0
        total_defect_area = sum(d["area"] for d in defects)

        result = {
            "defect_count": defect_count,
            "has_defects": has_defects,
            "total_defect_area": total_defect_area,
            "defects": defects,
            "threshold": self.threshold,
        }

        result.update(self._classify(defects))

        self._last_measurements = result
        return AnalysisReport(measurements=result)

    def _label(self, binary: np.ndarray) -> Tuple[np.ndarray, int]:
        labels = np.zeros_like(binary, dtype=int)
        next_label = 1
        equivalences = []

        for i in range(binary.shape[0]):
            for j in range(binary.shape[1]):
                if not binary[i, j]:
                    continue
                neighbors = []
                if self.connectivity == 8:
                    offsets = [(0, -1), (-1, -1), (-1, 0), (-1, 1)]
                else:
                    offsets = [(0, -1), (-1, 0)]
                for di, dj in offsets:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < binary.shape[0] and 0 <= nj < binary.shape[1]:
                        if labels[ni, nj] > 0:
                            neighbors.append(labels[ni, nj])
                if not neighbors:
                    labels[i, j] = next_label
                    equivalences.append({next_label})
                    next_label += 1
                else:
                    min_label = min(neighbors)
                    labels[i, j] = min_label
                    for n in neighbors:
                        if n != min_label:
                            self._merge(equivalences, min_label, n)

        resolved = self._resolve_equivalences(equivalences)
        mapping = {}
        for s in resolved:
            mapped = min(s)
            for l in s:
                mapping[l] = mapped

        for i in range(labels.shape[0]):
            for j in range(labels.shape[1]):
                if labels[i, j] > 0:
                    labels[i, j] = mapping.get(labels[i, j], labels[i, j])

        unique = set(labels.flat) - {0}
        renumber = {old: new + 1 for new, old in enumerate(sorted(unique))}
        for i in range(labels.shape[0]):
            for j in range(labels.shape[1]):
                if labels[i, j] > 0:
                    labels[i, j] = renumber[labels[i, j]]

        return labels, len(unique)

    def _merge(self, equivs: List[set], a: int, b: int):
        sa = sb = None
        for s in equivs:
            if a in s:
                sa = s
            if b in s:
                sb = s
        if sa is not None and sb is not None and sa is not sb:
            sa.update(sb)
            equivs.remove(sb)

    def _resolve_equivalences(self, equivs: List[set]) -> List[set]:
        changed = True
        while changed:
            changed = False
            for i in range(len(equivs)):
                for j in range(i + 1, len(equivs)):
                    if equivs[i] & equivs[j]:
                        equivs[i].update(equivs[j])
                        equivs[j] = set()
                        changed = True
            equivs = [s for s in equivs if s]
        return equivs

    def _extract_defects(
        self, labels: np.ndarray, num_features: int, pixels: np.ndarray, binary: np.ndarray
    ) -> List[Dict]:
        defects = []
        for label_id in range(1, num_features + 1):
            mask = labels == label_id
            area = int(np.sum(mask))
            if area < self.min_area or area > self.max_area:
                continue
            ys, xs = np.where(mask)
            defect = {
                "label": label_id,
                "area": area,
                "centroid_row": float(np.mean(ys)),
                "centroid_col": float(np.mean(xs)),
                "bbox": (
                    int(np.min(ys)),
                    int(np.min(xs)),
                    int(np.max(ys)) - int(np.min(ys)) + 1,
                    int(np.max(xs)) - int(np.min(xs)) + 1,
                ),
                "mean_intensity": float(np.mean(pixels[mask])),
                "max_intensity": float(np.max(pixels[mask])),
                "min_intensity": float(np.min(pixels[mask])),
            }
            defects.append(defect)
        return defects

    def _classify(self, defects: List[Dict]) -> Dict:
        scratch_count = 0
        blob_count = 0
        for d in defects:
            bh, bw = d["bbox"][2], d["bbox"][3]
            aspect = max(bh, bw) / (min(bh, bw) + 1)
            if aspect > 3.0:
                d["defect_type"] = "scratch"
                scratch_count += 1
            else:
                d["defect_type"] = "blob"
                blob_count += 1
        return {
            "scratch_count": scratch_count,
            "blob_count": blob_count,
        }

    def pass_fail(
        self,
        max_defects: int = 5,
        max_defect_area: int = 50,
        require_zero: bool = False,
    ) -> Tuple[bool, str]:
        """Evaluate pass/fail from the last :meth:`analyze` call.

        Parameters
        ----------
        max_defects : int
            Maximum number of allowed defects.
        max_defect_area : int
            Maximum total defect area in pixels.
        require_zero : bool
            If ``True``, any defect causes a FAIL.

        Returns
        -------
        passed : bool
        reason : str
        """
        m = self._last_measurements
        if m is None:
            return True, "No analysis run"
        count = m["defect_count"]
        area = m["total_defect_area"]
        if require_zero:
            return count == 0, f"{count} defects found (require zero)"
        if count > max_defects:
            return False, f"{count} defects exceeds limit {max_defects}"
        if area > max_defect_area:
            return False, f"defect area {area} exceeds limit {max_defect_area}"
        return True, f"OK ({count} defects, area {area})"
