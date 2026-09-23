"""The Isentropic calculator's flow-regime banner and its two-column readout.

A regression guard: the banner was once bound to properties that did not exist
and the readout to an undefined model, and the calculator showed an empty
results panel while every other test passed.
"""

from __future__ import annotations

import pathlib
import re

import pytest

from rocketforge.application.analysis.isentropic_controller import IsentropicController

CALCULATOR = (pathlib.Path(__file__).resolve().parents[2]
              / "ui" / "pages" / "isentropic" / "IsentropicCalculator.qml")


@pytest.fixture()
def iso(qt_app):
    return IsentropicController()


@pytest.mark.parametrize("mach,regime", [(0.5, "Subsonic"), (1.0, "Sonic"), (2.0, "Supersonic")])
def test_the_regime_comes_from_the_solved_mach_number(iso, mach, regime):
    iso.setMachAndSolve(mach)
    assert iso.flowRegime == regime
    assert iso.flowRegimeNote


def test_a_supersonic_note_quotes_the_solved_mach_angle(iso):
    """30 degrees at M = 2: taken from the physics result, not recomputed."""
    iso.setMachAndSolve(2.0)
    assert "30" in iso.flowRegimeNote


def test_no_transonic_or_hypersonic_label_is_invented(iso):
    for mach in (0.9, 1.1, 6.0):
        iso.setMachAndSolve(mach)
        assert iso.flowRegime in ("Subsonic", "Supersonic")


def test_every_readout_group_is_placed_in_a_column():
    """A group named in one list and spelled differently in the other would
    silently disappear from the readout."""
    source = CALCULATOR.read_text(encoding="utf-8")
    groups = re.search(r"property var groups: \[([^\]]*)\]", source).group(1)
    columns = re.search(r"property var columns: \[(.*?)\]\s*\n", source, re.S).group(1)
    names = set(re.findall(r'"([^"]+)"', groups))
    placed = set(re.findall(r'"([^"]+)"', columns))
    assert names == placed


def test_the_calculator_binds_only_to_existing_regime_properties():
    source = CALCULATOR.read_text(encoding="utf-8")
    assert "page.regime" not in source
    for used in re.findall(r"Isentropic\.(flowRegime\w*)", source):
        assert hasattr(IsentropicController, used), used
