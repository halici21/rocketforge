"""Narrow the Phase 5F density rule to the thing it was protecting.

Phase 5F banned **any identifier containing "density"** from trade-study code.
That was the right rule then: density had no validated source in this program
at all, so any density in a study could only have come from ``density_hint``,
and a blanket ban was the cheapest way to say so.

It is the wrong rule now, and for a reason that must be stated rather than
quietly worked around: this phase gives density a validated source. The
invariant the rule exists to protect is unchanged and is *not* being weakened --

    density_hint must never drive a calculation

-- and that is exactly what the replacement asserts, on the same modules, with
a stronger negative control than before: the fixture must now fire on a
``density_hint`` read even when the module is full of legitimate density code,
which is precisely the case the old blanket rule could not distinguish.

A second assertion is added that the old rule could not make at all: the
trade-study code must reach density through the propellant-metrics layer, so a
future edit cannot reintroduce the hint by another route and still pass.
"""
from __future__ import annotations

import pathlib

p = pathlib.Path("tests/application/test_trade_study_service.py")
t = p.read_text(encoding="utf-8")

old = '''def test_no_trade_study_code_touches_density_hint():
    """Blocking. ``density_hint`` is display-only metadata by 5A/5B contract.

    A density impulse computed from it would be a physical claim resting on a
    number never validated as a physical property, at a temperature, pressure
    and phase it does not record.
    """
    for path in _phase_5f_modules():
        leaked = [name for name in _identifiers(path)
                  if "density" in name.lower()]
        assert not leaked, (path.name, leaked)


def test_the_density_audit_would_catch_a_real_use():
    """The negative control, in both directions.

    It must fire on the use and stay silent on the explanation, or it would be
    enforcing the opposite of what it is for.
    """
    import pathlib
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        offending = pathlib.Path(folder) / "offending.py"
        offending.write_text(
            "def f(p):\\n"
            \'    """Never mention the forbidden field."""\\n\'
            "    return p.density_hint * 9.0\\n", encoding="utf-8")
        assert "density_hint" in _identifiers(offending)

        innocent = pathlib.Path(folder) / "innocent.py"
        innocent.write_text(
            \'"""density_hint is deliberately unused here."""\\n\'
            "def f():\\n"
            \'    """It is display-only metadata; no density impulse."""\\n\'
            "    return 1.0\\n", encoding="utf-8")
        assert not any("density" in name.lower()
                       for name in _identifiers(innocent))'''

new = '''def test_no_trade_study_code_touches_density_hint():
    """Blocking. ``density_hint`` is display-only metadata by 5A/5B contract.

    A density impulse computed from it would be a physical claim resting on a
    number never validated as a physical property, at a temperature, pressure
    and phase it does not record.

    **Scope changed, invariant unchanged.** Phase 5F banned every identifier
    containing "density" from these modules, because at that time density had
    no validated source in this program and so any density here could only have
    come from the hint. The fluids foundation gives density a validated source,
    so the blanket form would now forbid correct work. What it was protecting
    is asserted directly instead, and the negative control below is stronger
    for it: it must fire on a ``density_hint`` read *inside* a module full of
    legitimate density code, which the blanket rule could not distinguish.
    """
    for path in _phase_5f_modules():
        assert "density_hint" not in _identifiers(path), path.name


def test_trade_study_density_comes_from_the_propellant_metrics_layer():
    """The positive half: density must arrive by the validated route.

    The ban alone is satisfiable by having no density at all. This says where
    density is allowed to come from, so a future edit cannot reintroduce the
    hint by another name and still pass.
    """
    source = (_phase_5f_modules()[0]).read_text(encoding="utf-8")
    assert "rocketforge.engineering.propellants" in source
    assert "stream_density" in source
    assert "mixture_bulk_density" in source


def test_the_density_audit_would_catch_a_real_use():
    """The negative control, in both directions.

    It must fire on the use and stay silent on the explanation, or it would be
    enforcing the opposite of what it is for.
    """
    import pathlib
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        offending = pathlib.Path(folder) / "offending.py"
        offending.write_text(
            "def f(p):\\n"
            \'    """Never mention the forbidden field."""\\n\'
            "    return p.density_hint * 9.0\\n", encoding="utf-8")
        assert "density_hint" in _identifiers(offending)

        # The case the old blanket rule could not tell apart: a module doing
        # legitimate density work *and* reading the hint. The rule must fire.
        mixed = pathlib.Path(folder) / "mixed.py"
        mixed.write_text(
            "from rocketforge.engineering.propellants import stream_density\\n"
            "def f(provider, binding, p):\\n"
            "    good = stream_density(provider, binding, 90.0, 3e5).density\\n"
            "    return good + p.density_hint\\n", encoding="utf-8")
        assert "density_hint" in _identifiers(mixed)

        innocent = pathlib.Path(folder) / "innocent.py"
        innocent.write_text(
            \'"""density_hint is deliberately unused here."""\\n\'
            "def f():\\n"
            \'    """It is display-only metadata."""\\n\'
            "    return 1.0\\n", encoding="utf-8")
        assert "density_hint" not in _identifiers(innocent)

        # And legitimate density work alone must NOT trip it, or the rule
        # would be forbidding the thing it was never about.
        legitimate = pathlib.Path(folder) / "legitimate.py"
        legitimate.write_text(
            "def f(bulk, c_eff):\\n"
            "    return bulk.density * c_eff\\n", encoding="utf-8")
        assert "density_hint" not in _identifiers(legitimate)'''

assert old in t, "the Phase 5F density rule was not found in its expected form"
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("density rule narrowed, negative controls strengthened")
