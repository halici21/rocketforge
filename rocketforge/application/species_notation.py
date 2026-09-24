"""How a species name is shown: in chemical case, with its identity untouched.

NASA CEA writes most two-letter element symbols in capitals inside a species
name -- ``HCL``, ``AL2O3(L)``, ``NH4CLO4(I)``, and, in the same library,
``MgCL2``. Those names are identities: they key the composition, the sweep
selection and the provider's own records, and nothing here ever changes them.
What changes is the *label* a person reads, which is written the way chemists
write it: ``HCl``, ``Al2O3(L)``, ``NH4ClO4(I)``, ``MgCl2``.

The rewrite is deliberately conservative, because a species name is not a
parsed formula and guessing wrongly would put a different element on screen:

* Only a capital pair that is one of the elements named in ``_RECASED`` is
  lowered (``AL`` -> ``Al``, ``CL`` -> ``Cl``) -- and never a pair that also
  reads as two one-letter elements, so ``CO`` stays carbon monoxide rather
  than becoming cobalt, ``NO`` stays nitric oxide, ``HO2`` stays a radical.
* The result must parse, symbol by symbol, as a formula of real elements.
  If it does not -- ``HTPB``, ``RP-1``, ``CHOS-Binder``, ``TAGN`` -- the name
  is shown exactly as written.
* A phase qualifier -- ``(L)``, ``(cr)``, ``(a)``, ``(I)``, ``(II)`` -- and a
  ``,name`` suffix are part of the identity's meaning and are never recased.

``ui/theme/Notation.qml`` implements the same rule for QML (``Notation.
species``), where it also lowers the counts to subscripts;
``tests/application/test_species_notation.py`` holds the two to the same
answers.
"""

from __future__ import annotations

import re

__all__ = ["species_label"]

#: Every element symbol, for the "does it still read as a formula" check.
_ELEMENTS = frozenset("""
H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu
Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs
Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl
Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh
Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og""".split())

#: The capital pairs that are recased. The elements a propellant product set
#: actually carries, and none whose capital form also reads as two one-letter
#: elements (checked below, not just asserted here).
_RECASED = frozenset("""AL AR BA BE BR CA CL CR FE GA GE HE HG KR LI MG MN MO
NA NE RB SE SR TI XE ZN ZR""".split())

_ONE_LETTER = frozenset(e for e in _ELEMENTS if len(e) == 1)

#: A trailing phase qualifier: (L), (cr), (gr), (a), (b), (c), (s), (g), (I)...(IV).
_QUALIFIER = re.compile(r"\((?:L|cr|gr|a|b|c|s|g|I|II|III|IV)\)$")

_FORMULA_CHARS = re.compile(r"^[A-Za-z0-9()]+$")


def _recase(core: str) -> str:
    out = []
    i = 0
    while i < len(core):
        pair = core[i:i + 2]
        if (len(pair) == 2 and pair.isupper() and pair.isalpha()
                and pair in _RECASED
                and not (pair[0] in _ONE_LETTER and pair[1] in _ONE_LETTER)):
            out.append(pair[0] + pair[1].lower())
            i += 2
        else:
            out.append(core[i])
            i += 1
    return "".join(out)


def _reads_as_formula(core: str) -> bool:
    i = 0
    depth = 0
    while i < len(core):
        ch = core[i]
        if ch == "(":
            depth += 1
            i += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
            i += 1
        elif ch.isdigit():
            i += 1
        elif ch.isupper():
            two = core[i:i + 2]
            if len(two) == 2 and two[1].islower() and two in _ELEMENTS:
                i += 2
            elif ch in _ELEMENTS:
                i += 1
            else:
                return False
        else:
            return False
    return depth == 0


def species_label(name: str) -> str:
    """The chemical-case label for a species name; the name itself if unsure.

    ``species_label("MgCL2") == "MgCl2"``, ``species_label("CO") == "CO"``,
    ``species_label("HTPB") == "HTPB"``. Idempotent: a label already in
    chemical case comes back unchanged.
    """
    if not isinstance(name, str) or not name:
        return name
    text = name
    prefix = "*" if text.startswith("*") else ""
    text = text[len(prefix):]
    suffix = ""
    comma = text.find(",")
    if comma >= 0:
        text, suffix = text[:comma], text[comma:]
    qualifier = _QUALIFIER.search(text)
    if qualifier:
        suffix = qualifier.group(0) + suffix
        text = text[:qualifier.start()]
    charge = ""
    if text[-1:] in ("+", "-"):
        text, charge = text[:-1], text[-1]
    if not text or not _FORMULA_CHARS.match(text):
        return name
    recased = _recase(text)
    if recased == text or not _reads_as_formula(recased):
        return name
    return prefix + recased + charge + suffix
