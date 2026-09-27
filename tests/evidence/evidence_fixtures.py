"""Factories for evidence tests: one small, valid record and its registry.

Each test changes one field of a known-good object, so a failure points at the
one invariant it was written for.
"""

from __future__ import annotations

from rocketforge.evidence import (
    AccessClass,
    CustomDefinition,
    Dimension,
    EvidenceRecord,
    EvidenceStatus,
    IngredientReference,
    Missing,
    MissingReason,
    PropellantReference,
    RecordKind,
    ReportedValue,
    ShippingPolicy,
    SourceReference,
    ValueStatus,
)

SRC = "S-TEST-A"


def value(v=1.0, unit="K", source_id=SRC, locator="p.1, Table 1", **kw):
    return ReportedValue(v, unit, source_id, locator, ValueStatus.REPORTED, **kw)


def source(source_id=SRC, shipping=ShippingPolicy.VALUES_WITH_ATTRIBUTION, **kw):
    base = dict(source_id=source_id, organization="Test Org", authors=("A. Author",),
                title="A title", year=2000, identifiers={"report_number": "T-1"},
                locator="https://example.invalid/t1", source_type="report",
                access_class=AccessClass.PUBLIC_OPEN, rights_statement="stated",
                shipping=shipping, tier=1)
    base.update(kw)
    return SourceReference(**base)


def propellant(**kw):
    base = dict(
        propellant_id="P-1", source_ids=(SRC,), family="AP / binder",
        source_name="Blend", exact_formulation=True, basis="mass_fraction",
        ingredients=(
            IngredientReference("NH4CLO4(I)", value(0.8, "mass fraction"), "NH4CLO4(I)"),
            IngredientReference("Binder", value(0.2, "mass fraction"), None, CustomDefinition(
                formula={"C": value(1.0, "atoms per formula unit")},
                enthalpy=value(-100.0, "cal/mol"),
                reference_temperature=value(298.15, "K"),
                molecular_weight=Missing(MissingReason.NOT_REPORTED))),
        ),
        density=Missing(MissingReason.NOT_REPORTED, "not stated"),
        initial_temperature=value(298.15, "K"))
    base.update(kw)
    return PropellantReference(**base)


def capabilities(va=EvidenceStatus.REFERENCE_ONLY):
    return {Dimension.VA: va, Dimension.VB: EvidenceStatus.NOT_APPLICABLE,
            Dimension.VC: EvidenceStatus.NOT_APPLICABLE,
            Dimension.VD: EvidenceStatus.NOT_APPLICABLE}


def record(**kw):
    base = dict(record_id="DS-TEST", title="Test record", kind=RecordKind.PROPELLANT,
                source_ids=(SRC,), capabilities=capabilities(), capability_notes={},
                propellant=propellant(), comparison_case_ids=(), executable_key=None,
                blockers=(), notes="")
    base.update(kw)
    return EvidenceRecord(**base)
