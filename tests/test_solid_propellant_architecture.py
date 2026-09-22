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


#: The one module allowed to call the rocket solver, because CEA reports c*
#: only from it. Everywhere else it stays forbidden.
CSTAR_MODULE = "cstar.py"


@pytest.mark.parametrize("path", SOLID_SOURCES, ids=lambda p: p.name)
def test_only_the_cstar_module_reaches_for_the_rocket_solver(path):
    """c* is allowed; nothing else the rocket solver computes is.

    CEA reports c* only from ``RocketSolver``, which will also return Isp, a
    thrust coefficient and exit conditions for whatever exit it is handed. So
    the solver is confined to one module, and the next test forbids that module
    from reading anything but the chamber and c*.
    """
    code = code_only(path)
    if path.name != CSTAR_MODULE:
        assert "RocketSolver" not in code, path.name
    assert "FROZEN" not in code


#: What the rocket solver exposes and no solid module may read. Matched as
#: attribute accesses in executable code, so the docstrings stay free to name
#: what the modules deliberately do not do.
FORBIDDEN_SOLUTION_ATTRIBUTES = (
    "Isp", "Isp_vacuum", "coefficient_of_thrust", "ae_at", "Mach",
    "sonic_velocity",
)


def reads_attribute(code: str, name: str) -> bool:
    """Whether tokenised code reads ``.name``.

    :func:`code_only` joins every token with one space, so ``solution.Isp[0]``
    arrives as ``solution . Isp [ 0 ]``. A pattern written for the raw source
    -- ``".Isp["`` -- never matches that, which is exactly the vacuous guard
    the negative control below was written to catch, and did.
    """
    import re

    return re.search(rf"\. {name}\b", code) is not None

#: Identifiers that would mean a motor or nozzle claim, anywhere in solid code.
FORBIDDEN_IDENTIFIERS = (
    "specific_impulse", "thrust_coefficient", "def isp", "expansion_ratio",
    "area_ratio", "thrust_curve", "burn_rate",
)


@pytest.mark.parametrize("path", SOLID_SOURCES, ids=lambda p: p.name)
def test_no_solid_module_computes_a_performance_quantity(path):
    """c* yes; Isp, thrust coefficient, thrust, expansion, internal ballistics no.

    Those belong to later phases and need nozzle and internal-ballistic
    modelling this one does not have.
    """
    code = code_only(path)
    for attribute in FORBIDDEN_SOLUTION_ATTRIBUTES:
        assert not reads_attribute(code, attribute), (
            f"{path.name} reads {attribute!r} from a CEA rocket solution")
    lowered = code.lower()
    for identifier in FORBIDDEN_IDENTIFIERS:
        assert identifier not in lowered, (
            f"{path.name} names {identifier!r}; not part of this phase")


def test_the_cstar_module_reads_only_the_chamber_and_cstar():
    """A positive statement of what may come out of the rocket solve."""
    import re

    path = next(p for p in SOLID_SOURCES if p.name == CSTAR_MODULE)
    code = code_only(path)
    read = set(re.findall(r"solution \. ([A-Za-z_]+)", code))
    # The chamber temperature (cross-checked against the HP solve), c* itself,
    # and the two convergence signals. Nothing at the throat or exit.
    assert read == {"T", "c_star", "converged", "last_error"}, read


def test_the_architecture_guards_can_fail():
    """A negative control on the performance guard itself."""
    import io
    import tokenize

    offending = "value = solution.Isp[0]" + chr(10)
    tokens = [tok.string for tok in tokenize.generate_tokens(
        io.StringIO(offending).readline)
        if tok.type not in (tokenize.COMMENT, tokenize.STRING)]
    code = " ".join(tokens)
    assert reads_attribute(code, "Isp")
    assert not reads_attribute(code, "Isp_vacuum")   # whole name, not prefix
    assert not reads_attribute("solution . c_star [ 0 ]", "Isp")


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
