"""Structural rules for Solid Propellant R1, enforced rather than asserted.

R1's scope was narrowed at the Phase-A gate: formulation, chamber equilibrium,
gas and condensed products, provenance. Solid *reference performance* -- c*,
Cf, Isp, equilibrium and frozen expansion -- was deferred to R1.1.

A deferral that lives only in a document is a deferral that erodes. These tests
put it in the suite, so the first commit that quietly reaches for the rocket
solver fails rather than ships.
"""

from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

SOLID_SOURCES = sorted(
    (ROOT / "rocketforge" / "physics" / "solid_propellant").rglob("*.py")
) + sorted(
    (ROOT / "rocketforge" / "providers" / "cea_solid").rglob("*.py")
)

FROZEN_ROOTS = (
    "rocketforge/physics/thermochemistry",
    "rocketforge/providers/cea",
)


def code_only(path: pathlib.Path) -> str:
    """The module's executable text, with comments and string literals removed.

    These modules explain at length what they deliberately do *not* do, naming
    ``RocketSolver`` and ``of_ratio_to_weights`` in prose to say why each was
    unreachable. A raw substring search cannot tell that explanation apart from
    a use, and would force the docstrings to stop being specific -- which is the
    wrong thing to optimise. Tokenising drops comments and every string literal,
    so what is left is identifiers and syntax: what the module actually runs.
    """
    import io
    import tokenize

    source = path.read_text(encoding="utf-8")
    kept = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(token.string)
    return " ".join(kept)


def test_the_solid_packages_actually_exist():
    """A guard on the guards: these tests are worthless against an empty set."""
    assert len(SOLID_SOURCES) >= 4
    for path in SOLID_SOURCES:
        assert path.read_text(encoding="utf-8").strip()


@pytest.mark.parametrize("path", SOLID_SOURCES, ids=lambda p: p.name)
def test_no_solid_module_reaches_for_the_rocket_solver(path):
    """Section 7: no reference performance in R1.

    ``RocketSolver`` would solve an expansion nobody asked for and would make
    the chamber state a by-product of a nozzle calculation R1 does not own.
    """
    code = code_only(path)
    assert "RocketSolver" not in code
    assert "FROZEN" not in code


@pytest.mark.parametrize("path", SOLID_SOURCES, ids=lambda p: p.name)
def test_no_solid_module_computes_a_performance_quantity(path):
    """Section 24: no performance panel, and nothing behind one either.

    Checked on identifiers rather than prose, so the modules stay free to
    explain in their docstrings exactly what they do not do -- which they do.
    """
    code = code_only(path).lower()

    for forbidden in ("c_star", "cstar", "characteristic_velocity",
                      "specific_impulse", "thrust_coefficient",
                      "def isp", "expansion_ratio", "area_ratio"):
        assert forbidden not in code, (
            f"{path.name} names {forbidden!r}; solid reference performance is "
            "deferred to R1.1")


def test_the_solid_work_added_nothing_inside_a_frozen_package():
    """Both freeze manifests are checked by file list *and* by directory.

    ``test_each_manifest_covers_its_whole_package`` already enforces this, but
    it fails on the first offending manifest and stops. This names the rule
    directly for both roots, so a reader of this package learns the constraint
    here rather than by tripping it.
    """
    import json

    for root in FROZEN_ROOTS:
        stem = ("freeze_thermochemistry_api_v1"
                if "thermochemistry" in root else "freeze_cea_provider_v1_1")
        manifest = json.loads(
            next((ROOT / "acceptance").rglob(f"{stem}.json")).read_text(
                encoding="utf-8"))
        recorded = {entry["path"] for entry in manifest["files"]}
        on_disk = {
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / root).rglob("*.py")
            if "__pycache__" not in p.parts
        }
        assert on_disk == recorded, (
            f"{root} gained or lost a module; the freeze covers the whole "
            f"directory, so solid work belongs in a sibling package")


def test_the_solid_provider_reuses_the_frozen_helpers_rather_than_copying_them():
    """Section 11: no duplicated unit conversion or condensed-mass logic.

    Two pieces genuinely could not be reused -- the solver invocation and the
    ``ChamberGas`` assembly -- and the design document records why. Everything
    else is imported.
    """
    source = (ROOT / "rocketforge" / "providers" / "cea_solid"
              / "provider.py").read_text(encoding="utf-8")
    for reused in ("from rocketforge.providers.cea.mapping import",
                   "from rocketforge.providers.cea.units import",
                   "from rocketforge.providers.cea.species import",
                   "from rocketforge.providers.cea.errors import",
                   "condensed_mass_fraction",
                   "CEARawChamberResult",
                   "enthalpy_argument"):
        assert reused in source, f"expected the solid path to reuse {reused!r}"


def test_no_solid_module_fabricates_a_mixture_ratio():
    """Section 10: no synthetic O/F to satisfy the bipropellant request object.

    CEA reports ``o/f = 0.000`` for a solid case. The absence of a ratio is the
    correct representation; a fabricated one is the failure this forbids.
    """
    for path in SOLID_SOURCES:
        code = code_only(path)
        assert "MixtureRatio" not in code
        assert "of_ratio_to_weights" not in code
        assert "PropellantStream" not in code


def test_no_solid_module_sets_a_frozen_expansion_station():
    """Section 20: ``n_frz`` is a 1-based station number and easy to mislabel.

    R1 has no expansion, so no solid module has any business naming it. When
    R1.1 adds one, ``tests/providers/cea_solid/test_solid_mechanisms.py``
    already pins what the index means; this test makes sure R1 does not start
    using it early.
    """
    for path in SOLID_SOURCES:
        assert "n_frz" not in code_only(path), path.name
