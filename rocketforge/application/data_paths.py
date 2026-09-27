"""Where the application's shipped data lives, in a source tree and in a frozen build.

One rule for both: a frozen build unpacks its data under ``sys._MEIPASS`` and
says so; a source run finds it beside the package. Kept free of any analysis
import so that anything needing a data path -- the reference tables, the
evidence corpus -- can ask without importing a solver.
"""
from __future__ import annotations

import pathlib
import sys

__all__ = ["data_root"]


def data_root() -> pathlib.Path:
    """``rocketforge/data``, wherever this build keeps it."""
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return pathlib.Path(bundled) / "rocketforge" / "data"
    return pathlib.Path(__file__).resolve().parents[1] / "data"
