"""Polarisation state representation for optical sources.

Provides a validated description of a source's polarisation state,
supporting the common idealised types: unpolarized, linear, circular,
and elliptical.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PolarizationState:
    """A lightweight representation of the polarization state of a source.

    Attributes
    ----------
    kind : str
        One of ``"unpolarized"``, ``"linear"``, ``"circular"``, or
        ``"elliptical"``.  Case-sensitive.

    Raises
    ------
    ValueError
        If ``kind`` is not one of the allowed values.
    """

    kind: str = "unpolarized"

    def __post_init__(self):
        allowed = {"unpolarized", "linear", "circular", "elliptical"}
        if self.kind not in allowed:
            raise ValueError(f"Unsupported polarization kind: {self.kind}")
