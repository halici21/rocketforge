"""Test-only engine-evidence fixtures built from DB-0.5 findings.

These are schema stress cases, not the production corpus (DB-2). Values and
locators are the ones DB-0.5 read in opened documents
(``docs/research/engine_database/db05``); the corpus exists to prove the
schema can hold them without flattening configuration, conditions,
provenance, conflicts, rights or topology.
"""

from __future__ import annotations

import hashlib

from rocketforge.evidence import AccessClass, Missing, MissingReason, ShippingPolicy, SourceReference, ValueStatus
from rocketforge.evidence.engines import (
    Admissibility,
    Assertion,
    ComponentType,
    Component,
    Completeness,
    Conditions,
    Conflict,
    ConflictCategory,
    ConflictResolution,
    EdgeKind,
    EngineConfiguration,
    EngineEvidenceCorpus,
    EngineFamily,
    EngineSource,
    EngineVariant,
    EnumValue,
    Environment,
    IspBasis,
    LineageEdge,
    LineageKind,
    MixtureRatioBasis,
    MixtureRatioForm,
    NumberValue,
    OperatingPoint,
    Ownership,
    PressureBasis,
    PressureStation,
    PropulsionUnit,
    PropulsionUnitKind,
    Qualifier,
    RIGHTS_IN_RECORD,
    RangeValue,
    RightsNotice,
    RightsRecord,
    RightsReview,
    Schematic,
    SchematicProvenance,
    Setting,
    SourceAccess,
    SourceAuthority,
    SourcePrimacy,
    SubjectKind,
    SubjectRef,
    TextValue,
    TopologyEdge,
    TopologyEvidence,
    TopologyGraph,
    TopologyNode,
    UnitMember,
    ValueKind,
)

V = ShippingPolicy.VALUES_WITH_ATTRIBUTION
REVIEW = ShippingPolicy.RIGHTS_REVIEW_REQUIRED
RESTRICTED = ShippingPolicy.RESTRICTED_REFERENCE
OPENED, SEARCH, BLOCKED = SourceAccess.OPENED, SourceAccess.SEARCH_RESULT_ONLY, SourceAccess.ACCESS_BLOCKED
SH, TX, BO, INF = (TopologyEvidence.SHOWN_IN_SCHEMATIC, TopologyEvidence.REPORTED_IN_TEXT,
                   TopologyEvidence.DERIVED_FROM_BOTH, TopologyEvidence.INFERRED)
FLUID, SHAFT, GEAR, LINK, ACT = (EdgeKind.FLUID_FLOW, EdgeKind.MECHANICAL_SHAFT, EdgeKind.GEARED_DRIVE,
                                 EdgeKind.MECHANICAL_LINKAGE, EdgeKind.CONTROL_ACTUATION)
ENG, STG, VEH, AMB = Ownership.ENGINE, Ownership.STAGE, Ownership.VEHICLE, Ownership.AMBIENT
T = ComponentType


def h(n: int) -> str:
    """A distinct, valid content hash for test document n."""
    return f"{n:064x}"


def rights(values=V, *, host=None, printed=None, disagree=False, review=RightsReview.CONSISTENT, figures=None):
    return RightsRecord(
        host_metadata=host if host is not None else Missing(MissingReason.NOT_AUDITED),
        printed_notice=printed if printed is not None else Missing(MissingReason.NOT_REPORTED),
        values=values, figures=figures or values, tables=values, text=values,
        notices_disagree=disagree, review=review)


def source(sid, authority=SourceAuthority.A, access=OPENED, *, digest=None, rights_=None,
           same=None, primacy=SourcePrimacy.PRIMARY, title=None):
    r = rights_ or rights()
    tier = {SourceAuthority.A: 1, SourceAuthority.B: 1, SourceAuthority.C: 2,
            SourceAuthority.D: 3, SourceAuthority.E: 3}[authority]
    fetched = access in (OPENED, SourceAccess.FETCHED_NOT_READ)
    return EngineSource(
        reference=SourceReference(
            source_id=sid, organization="test", authors=(), title=title or sid, year=None,
            identifiers={}, locator=f"https://example.invalid/{sid}", source_type="report",
            access_class=AccessClass.PUBLIC_OPEN, rights_statement=RIGHTS_IN_RECORD,
            shipping=r.values, tier=tier),
        authority=authority, primacy=primacy, access=access,
        content_sha256=(digest if digest is not None else hashlib.sha256(sid.encode()).hexdigest()) if fetched else None,
        same_document_as=same, rights=r)


def ref(kind: SubjectKind, id_: str) -> SubjectRef:
    return SubjectRef(kind, id_)


CFG, OP, COMP, VAR, FAM, UNIT = (SubjectKind.CONFIGURATION, SubjectKind.OPERATING_POINT, SubjectKind.COMPONENT,
                                 SubjectKind.VARIANT, SubjectKind.FAMILY, SubjectKind.PROPULSION_UNIT)


def num(aid, subject, field, printed, value, unit, src, loc, *, op=None, kind=ValueKind.NOMINAL,
        status=ValueStatus.REPORTED, cond=None, access=OPENED, adm=Admissibility.ADMITTED, note="", **extra):
    return Assertion(assertion_id=aid, subject=subject, field_path=field, value=NumberValue(value),
                     value_as_printed=printed, unit_as_printed=unit, conditions=cond or Conditions(),
                     value_kind=kind, status=status, admissibility=adm, source_id=src, locator=loc,
                     access=access, operating_point_id=op, note=note, **extra)


def pc(basis=PressureBasis.ABSOLUTE, station=PressureStation.UNKNOWN, **kw):
    return Conditions(pressure_basis=basis, pressure_station=station, **kw)


def node(nid, kind, label, owner, ev, loc, comp=None):
    return TopologyNode(nid, kind, label, owner, ev, loc, comp)


def edge(eid, a, b, kind, carrier, role, ev, loc, split=None, merge=None):
    return TopologyEdge(eid, a, b, kind, carrier, role, ev, loc, split, merge)


# --------------------------------------------------------------------- RS-25


def rs25():
    s = [
        source("SRC-L3H-RS25", rights_=rights(printed=RightsNotice("(c) 2024 L3Harris Technologies", "p.2"))),
        source("SRC-JSC19041"),
        source("SRC-BC9804", rights_=rights(RESTRICTED, printed=RightsNotice("BOEING PROPRIETARY", "every page"))),
        source("SRC-AIAA972687", rights_=rights(
            REVIEW, host=RightsNotice("GOV_PUBLIC_USE_PERMITTED", "NTRS citation API copyright.determinationType"),
            printed=RightsNotice("Copyright 1997 by the AIAA, Inc. All rights reserved.", "PDF p.3"),
            disagree=True, review=RightsReview.CONFLICT_UNRESOLVED)),
        source("SRC-NTRS-19860012108"),
        source("SRC-NTRS-20180006338"),
        source("SRC-WIKI-RS25", SourceAuthority.D, SEARCH, primacy=SourcePrimacy.TERTIARY),
    ]
    fam = [EngineFamily("FAM-RS25", "RS-25 (SSME)")]
    var = [EngineVariant("VAR-SSME", "FAM-RS25", "SSME / RS-25")]
    cfg = [EngineConfiguration("CFG-SSME-PRE-LT", "VAR-SSME", "pre-large-throat MCC (Phase II / Block I)",
                               Missing(MissingReason.NOT_AUDITED)),
           EngineConfiguration("CFG-SSME-IIA", "VAR-SSME", "Block IIA", Missing(MissingReason.NOT_AUDITED)),
           EngineConfiguration("CFG-SSME-II", "VAR-SSME", "Block II (RS-25D)",
                               "first flight STS-104, July 2001 (AIAA 2002-3581)")]
    ops = [OperatingPoint("OP-PRE-109", "CFG-SSME-PRE-LT", "109% RPL"),
           OperatingPoint("OP-IIA-104.5", "CFG-SSME-IIA", "104.5% RPL"),
           OperatingPoint("OP-II-RPL", "CFG-SSME-II", "100% RPL"),
           OperatingPoint("OP-II-109", "CFG-SSME-II", "109% RPL")]
    iia = "CFG-SSME-IIA"
    comps = [Component(f"RS25IIA-{k}", SubjectRef(CFG, iia), t, label, o) for k, t, label, o in [
        ("LH2-IN", T.INTERFACE_PORT, "Hydrogen inlet", ENG), ("LPFTP-P", T.BOOSTER_PUMP, "LPFTP pump", ENG),
        ("LPFTP-T", T.TURBINE, "LPFTP turbine (GH2 drive)", ENG), ("HPFTP-P", T.PUMP, "HPFTP pump", ENG),
        ("HPFT", T.TURBINE, "HPFTP turbine", ENG), ("MFV", T.VALVE, "Main fuel valve", ENG),
        ("MCC-COOL", T.COOLING_JACKET, "MCC coolant channels", ENG), ("NOZ-TUBES", T.COOLING_JACKET, "Nozzle tubes", ENG),
        ("CCV", T.VALVE, "Chamber coolant valve", ENG), ("FPB", T.PREBURNER, "Fuel preburner", ENG),
        ("OPB", T.PREBURNER, "Oxidizer preburner", ENG), ("HGM", T.MANIFOLD, "Hot gas manifold", ENG),
        ("MI", T.INJECTOR, "Main injector", ENG), ("MCC", T.COMBUSTION_CHAMBER, "Main combustion chamber", ENG),
        ("NOZ", T.NOZZLE, "Nozzle", ENG), ("AMB", T.AMBIENT_SINK, "Exhaust", AMB),
        ("LOX-IN", T.INTERFACE_PORT, "Oxygen inlet", ENG), ("LPOTP-P", T.BOOSTER_PUMP, "LPOTP pump", ENG),
        ("LPOTP-T", T.HYDRAULIC_TURBINE, "LPOTP turbine (LOX-driven)", ENG), ("HPOTP-P", T.PUMP, "HPOTP main pump", ENG),
        ("HPOTP-BP", T.PUMP, "Preburner oxidizer boost pump", ENG), ("HPOT", T.TURBINE, "HPOTP turbine", ENG),
        ("MOV", T.VALVE, "Main oxidizer valve", ENG), ("FPOV", T.VALVE, "FPOV", ENG), ("OPOV", T.VALVE, "OPOV", ENG),
        ("HEX", T.HEAT_EXCHANGER, "Heat exchanger coil", ENG),
        ("ET-LH2", T.INTERFACE_PORT, "ET fuel tank pressurization", VEH),
        ("ET-LOX", T.INTERFACE_PORT, "ET oxidizer tank pressurization", VEH)]]
    comps += [Component("RS25II-HPOT", SubjectRef(CFG, "CFG-SSME-II"), T.TURBINE, "HPOTP turbine", ENG),
              Component("RS25II-HPOTP-P", SubjectRef(CFG, "CFG-SSME-II"), T.PUMP, "HPOTP main pump", ENG),
              Component("RS25II-HPFTP", SubjectRef(CFG, "CFG-SSME-II"), T.TURBOPUMP_ASSEMBLY, "HPFTP (P&W)", ENG),
              Component("RS25II-HPOTP", SubjectRef(CFG, "CFG-SSME-II"), T.TURBOPUMP_ASSEMBLY, "HPOTP", ENG)]
    sch = [Schematic("SCH-BC9804-S19", "SRC-BC9804", "BC98-04 p.25 (slide 19)",
                     "Block IIA SSME Propellant Flow Schematic, 104.5% of RPL",
                     SchematicProvenance.ORIGINAL_MANUFACTURER, "Rocketdyne", "all annotations legible"),
           Schematic("SCH-AIAA972687-F1", "SRC-AIAA972687", "PDF p.3, Figure 1",
                     "SSME Propellant Flow Schematic", SchematicProvenance.ORIGINAL_CONTRACTOR,
                     "Rocketdyne (AIAA paper)", "labels legible; state annotations ILLEGIBLE")]
    c = lambda k: f"RS25IIA-{k}"  # noqa: E731
    LS, LT = "BC98-04 p.25 slide 19", "BC98-04 pp.24-27"
    nodes = [node(c(k), comp.component_type, comp.label, comp.ownership,
                  TX if k in ("MCC-COOL", "LPOTP-T", "HEX", "ET-LH2", "ET-LOX") else BO,
                  LT if k in ("MCC-COOL", "LPOTP-T", "HEX", "ET-LH2", "ET-LOX") else LS, comp.component_id)
             for comp in comps if comp.scope.id == iia for k in [comp.component_id.removeprefix("RS25IIA-")]]
    nodes.append(node("MIX", T.JUNCTION, "Nozzle coolant + CCV merge", ENG, BO, LT))
    edges = [
        edge("e1", c("LH2-IN"), c("LPFTP-P"), FLUID, "LH2", "feed", BO, LS),
        edge("e2", c("LPFTP-P"), c("HPFTP-P"), FLUID, "LH2", "low-pressure fuel duct", BO, LT),
        edge("e3", c("HPFTP-P"), c("MFV"), FLUID, "LH2", "high-pressure fuel duct", BO, LT),
        edge("e4", c("MFV"), c("MCC-COOL"), FLUID, "H2", "MCC cooling, 19%", BO, LT, split="F1"),
        edge("e5", c("MFV"), c("NOZ-TUBES"), FLUID, "H2", "nozzle cooling, 27.5%", BO, LT, split="F1"),
        edge("e6", c("MFV"), c("CCV"), FLUID, "H2", "nozzle bypass, 48.5%", BO, LT, split="F1"),
        edge("e7", c("MCC-COOL"), c("LPFTP-T"), FLUID, "GH2", "turbine drive", BO, LT),
        edge("e8", c("LPFTP-T"), c("ET-LH2"), FLUID, "GH2", "tank pressurization tap", BO, LT),
        edge("e9", c("LPFTP-T"), c("HGM"), FLUID, "GH2", "HGM coolant", BO, LT),
        edge("e10", c("NOZ-TUBES"), "MIX", FLUID, "H2", "merge", BO, LT, merge="F2"),
        edge("e11", c("CCV"), "MIX", FLUID, "H2", "merge", BO, LT, merge="F2"),
        edge("e12", "MIX", c("FPB"), FLUID, "H2", "preburner fuel", BO, LT),
        edge("e13", "MIX", c("OPB"), FLUID, "H2", "preburner fuel", BO, LT),
        edge("e14", c("FPB"), c("HPFT"), FLUID, "H2-rich gas", "turbine drive", BO, LS),
        edge("e15", c("OPB"), c("HPOT"), FLUID, "H2-rich gas", "turbine drive", BO, LS),
        edge("e16", c("HPFT"), c("HGM"), FLUID, "H2-rich gas", "turbine exhaust", BO, LS),
        edge("e17", c("HPOT"), c("HGM"), FLUID, "H2-rich gas", "turbine exhaust", BO, LS),
        edge("e18", c("HGM"), c("MI"), FLUID, "H2-rich gas", "hot gas to injector", BO, LS),
        edge("e19", c("MI"), c("MCC"), FLUID, "propellants", "injection", BO, LS),
        edge("e20", c("MCC"), c("NOZ"), FLUID, "combustion gas", "expansion", SH, LS),
        edge("e21", c("NOZ"), c("AMB"), FLUID, "combustion gas", "exhaust", SH, LS),
        edge("e22", c("LOX-IN"), c("LPOTP-P"), FLUID, "LOX", "feed", BO, LS),
        edge("e23", c("LPOTP-P"), c("HPOTP-P"), FLUID, "LOX", "low-pressure oxidizer duct", BO, LT),
        edge("e24", c("HPOTP-P"), c("MOV"), FLUID, "LOX", "main flow", BO, LT),
        edge("e25", c("MOV"), c("MI"), FLUID, "LOX", "main oxidizer", BO, LS),
        edge("e26", c("HPOTP-P"), c("LPOTP-T"), FLUID, "LOX", "hydraulic turbine drive", BO, LT),
        edge("e27", c("HPOTP-P"), c("HEX"), FLUID, "LOX", "branch to heat exchanger", TX, LT),
        edge("e28", c("HEX"), c("ET-LOX"), FLUID, "GOX", "tank pressurization", TX, LT),
        edge("e29", c("HPOTP-P"), c("HPOTP-BP"), FLUID, "LOX", "11% branch", BO, LT),
        edge("e30", c("HPOTP-BP"), c("FPOV"), FLUID, "LOX", "preburner oxidizer", BO, LS),
        edge("e31", c("HPOTP-BP"), c("OPOV"), FLUID, "LOX", "preburner oxidizer", BO, LS),
        edge("e32", c("FPOV"), c("FPB"), FLUID, "LOX", "preburner oxidizer", BO, LS),
        edge("e33", c("OPOV"), c("OPB"), FLUID, "LOX", "preburner oxidizer", BO, LS),
        edge("e34", c("HPFT"), c("HPFTP-P"), SHAFT, None, "common shaft", BO, LS),
        edge("e35", c("HPOT"), c("HPOTP-P"), SHAFT, None, "common shaft", SH, LS),
        edge("e36", c("HPOT"), c("HPOTP-BP"), SHAFT, None, "common shaft", SH, LS),
        edge("e37", c("LPFTP-T"), c("LPFTP-P"), SHAFT, None, "common shaft", BO, LT),
        edge("e38", c("LPOTP-T"), c("LPOTP-P"), SHAFT, None, "common shaft (hydraulic turbine)", BO, LT),
    ]
    topo = [TopologyGraph("TOPO-RS25-IIA", SubjectRef(CFG, iia), "Block IIA propellant flow", SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH,
                          ("SCH-BC9804-S19",), ("SRC-BC9804",),
                          Completeness(False, ("helium purge and pneumatics", "ASI supply", "bleed valves", "start sequence")),
                          tuple(nodes), tuple(edges))]
    P = SubjectRef
    a = [
        num("RS25-PC-109", P(CFG, "CFG-SSME-II"), "performance.chamber_pressure", "2,994 psia", 2994, "psia",
            "SRC-L3H-RS25", "p.1 SPECIFICATIONS", op="OP-II-109", kind=ValueKind.RATED, cond=pc()),
        num("RS25-PC-IIA-104", P(CFG, iia), "performance.chamber_pressure", "2,871 psia", 2871, "psia",
            "SRC-BC9804", "p.25 MCC callout", op="OP-IIA-104.5", status=ValueStatus.DIGITISED,
            cond=pc(), schematic_id="SCH-BC9804-S19"),
        num("RS25-PC-LT-PRED", P(CFG, "CFG-SSME-II"), "performance.chamber_pressure", "3010 psia", 3010, "psia",
            "SRC-NTRS-19860012108", "p.8", op="OP-II-109", kind=ValueKind.PREDICTION, cond=pc()),
        num("RS25-PC-PRE-109", P(CFG, "CFG-SSME-PRE-LT"), "performance.chamber_pressure", "3285 (109% power level)",
            3285, "psia", "SRC-NTRS-19860012108", "p.8", op="OP-PRE-109", cond=pc()),
        num("RS25-HPOT-LIMIT", P(COMP, "RS25II-HPOT"), "turbine.speed", "approximately 30,000 rpm", 30000, "rpm",
            "SRC-JSC19041", "p.97 §1.5.2", kind=ValueKind.LIMIT,
            note="maximum allowable HPOT speed (shutdown overspeed); burst 38,000 rpm"),
        num("RS25-HPOTP-SPEED-IIA", P(COMP, c("HPOTP-P")), "pump.speed", "22,250 rpm", 22250, "rpm", "SRC-BC9804",
            "p.25 HPOTP callout", op="OP-IIA-104.5", status=ValueStatus.DIGITISED, schematic_id="SCH-BC9804-S19"),
        num("RS25-HPOTP-SPEED-WIKI", P(COMP, "RS25II-HPOTP-P"), "pump.speed", "28,120 rpm", 28120, "rpm",
            "SRC-WIKI-RS25", "search summary", access=SEARCH, kind=ValueKind.UNKNOWN),
        num("RS25-EPS-L3H", P(CFG, "CFG-SSME-II"), "nozzle.area_ratio", "69:1", 69, ":1", "SRC-L3H-RS25", "p.1"),
        num("RS25-EPS-LT", P(CFG, "CFG-SSME-II"), "nozzle.area_ratio", "77.5 to 69.5:1", 69.5, ":1",
            "SRC-NTRS-19860012108", "p.8"),
        num("RS25-EPS-STALE", P(CFG, "CFG-SSME-II"), "nozzle.area_ratio", "77.5 to 1", 77.5, ":1", "SRC-JSC19041",
            "p.1.1-1", adm=Admissibility.REJECTED_STALE_TEXT, note="pre-large-throat value reprinted in a 2003 Block II brief"),
        num("RS25-EPS-PRE", P(CFG, "CFG-SSME-PRE-LT"), "nozzle.area_ratio", "77.5", 77.5, ":1",
            "SRC-NTRS-19860012108", "p.8"),
        Assertion("RS25-IIA-CHANGE", P(CFG, iia), "identity.change_from_previous",
                  TextValue("The modification between the Block IA SSME and the Block IIA was a larger throat MCC"),
                  "The modification between the Block IA SSME and the Block IIA was a larger throat MCC", "",
                  Conditions(), ValueKind.OTHER, ValueStatus.REPORTED, Admissibility.ADMITTED,
                  "SRC-JSC19041", "p.1.1-2 §1.1.2", OPENED),
        num("RS25-HPFTP-POWER-L3H", P(COMP, "RS25II-HPFTP"), "turbopump.power", "71,140 hp", 71140, "hp",
            "SRC-L3H-RS25", "p.1 Power: High Pressure Pumps"),
        num("RS25-HPFTP-POWER-NTRS", P(COMP, "RS25II-HPFTP"), "turbopump.power", "69,000 horsepower", 69000, "hp",
            "SRC-NTRS-20180006338", "p.2"),
        Assertion("RS25-FPB-RICH", P(COMP, c("FPB")), "combustion.rich_side", EnumValue("FUEL_RICH"), "fuel-rich", "",
                  Conditions(), ValueKind.NOMINAL, ValueStatus.REPORTED, Admissibility.ADMITTED,
                  "SRC-BC9804", "p.24", OPENED),
        Assertion("RS25-OPB-RICH", P(COMP, c("OPB")), "combustion.rich_side", EnumValue("FUEL_RICH"), "fuel-rich", "",
                  Conditions(), ValueKind.NOMINAL, ValueStatus.REPORTED, Admissibility.ADMITTED,
                  "SRC-BC9804", "p.24", OPENED),
        num("RS25-THRUST-VAC-109", P(CFG, "CFG-SSME-II"), "performance.thrust", "512,300 lb", 512300, "lb",
            "SRC-L3H-RS25", "p.1", op="OP-II-109", kind=ValueKind.MAXIMUM, cond=Conditions(environment=Environment.VACUUM)),
        Assertion("RS25-THROTTLE", P(CFG, "CFG-SSME-II"), "performance.throttle_range", RangeValue(67, 109),
                  "67% - 109%", "%", Conditions(), ValueKind.RATED, ValueStatus.REPORTED, Admissibility.ADMITTED,
                  "SRC-L3H-RS25", "p.1 Throttle Range", OPENED),
        num("RS25-MR", P(CFG, "CFG-SSME-II"), "propellants.mixture_ratio", "6.03:1", 6.03, ":1", "SRC-L3H-RS25", "p.1",
            cond=Conditions(mixture_ratio_form=MixtureRatioForm.OXIDIZER_TO_FUEL,
                            mixture_ratio_basis=MixtureRatioBasis.UNKNOWN)),
        num("RS25-ISP-VAC", P(CFG, "CFG-SSME-II"), "performance.specific_impulse", "452.3 sec", 452.3, "sec",
            "SRC-L3H-RS25", "p.1", op="OP-II-109", kind=ValueKind.RATED,
            cond=Conditions(environment=Environment.VACUUM, isp_basis=IspBasis.UNKNOWN)),
    ]
    x = [
        Conflict("CF-RS25-EPS", "nozzle.area_ratio", ("RS25-EPS-L3H", "RS25-EPS-LT", "RS25-EPS-STALE"),
                 ConflictResolution.EXPLAINED, (ConflictCategory.DIFFERENT_CONFIGURATION, ConflictCategory.ROUNDING),
                 "Large-throat MCC reduced 77.5 to 69.5 (NTRS 19860012108 p.8); 69 is 69.5 rounded; 77.5 in a 2003 brief is stale text."),
        Conflict("CF-RS25-JSC-INTRA", "nozzle throat configuration", ("RS25-EPS-STALE", "RS25-IIA-CHANGE"),
                 ConflictResolution.EXPLAINED, (ConflictCategory.DIFFERENT_CONFIGURATION,),
                 "JSC-19041 prints the pre-large-throat ratio on p.1.1-1 and the larger-throat change on p.1.1-2."),
        Conflict("CF-RS25-PUMPPOWER", "turbopump.power", ("RS25-HPFTP-POWER-L3H", "RS25-HPFTP-POWER-NTRS"),
                 ConflictResolution.UNRESOLVED, (), "Neither prints a power level."),
    ]
    return s, fam, var, cfg, ops, comps, sch, topo, a, x


# --------------------------------------------------------------------- J-2


def j2():
    s = [source("SRC-COFFMAN-J2", rights_=rights(V, figures=REVIEW)),
         source("SRC-MSFC-MAN-503", rights_=rights(
             REVIEW, host=RightsNotice("GOV_PUBLIC_USE_PERMITTED", "NTRS API"),
             printed=RightsNotice("Reproduction for non-government use ... not permitted without specific approval",
                                  "PDF p.3 (page A)"), disagree=True, review=RightsReview.CONFLICT_UNRESOLVED))]
    fam = [EngineFamily("FAM-J2", "J-2")]
    var = [EngineVariant("VAR-J2", "FAM-J2", "J-2")]
    cfg = [EngineConfiguration("CFG-J2-225K", "VAR-J2", "225,000 lb version", "qualification (Coffman text p.3)"),
           EngineConfiguration("CFG-J2-230K", "VAR-J2", "230,000 lb version", Missing(MissingReason.NOT_REPORTED))]
    ops = [OperatingPoint("OP-J2-MR55", "CFG-J2-230K", "MR 5.5"), OperatingPoint("OP-J2-MR45", "CFG-J2-230K", "MR 4.5")]
    k = "CFG-J2-230K"
    parts = [("LOX-IN", T.INTERFACE_PORT, ENG), ("OTP-P", T.PUMP, ENG), ("OTP-T", T.TURBINE, ENG),
             ("FTP-P", T.PUMP, ENG), ("FTP-T", T.TURBINE, ENG), ("MRCV", T.VALVE, ENG), ("MOV", T.VALVE, ENG),
             ("MFV", T.VALVE, ENG), ("GGV", T.VALVE, ENG), ("GG", T.GAS_GENERATOR, ENG), ("OTBV", T.VALVE, ENG),
             ("HEX", T.HEAT_EXCHANGER, ENG), ("STANK", T.START_ENERGY_STORE, ENG), ("INJ", T.INJECTOR, ENG),
             ("TC", T.THRUST_CHAMBER, ENG), ("NOZ-DUMP", T.MANIFOLD, ENG), ("AMB", T.AMBIENT_SINK, AMB),
             ("LOX-PRESS", T.INTERFACE_PORT, STG), ("LH2-PRESS", T.INTERFACE_PORT, STG),
             ("HYD-PUMP", T.HYDRAULIC_PUMP, ENG)]
    comps = [Component(f"J2-{n}", SubjectRef(CFG, k), t, n, o) for n, t, o in parts]
    sch = [Schematic("SCH-J2-S4", "SRC-COFFMAN-J2", "PDF p.15 slide J2-4", "J-2 Engine Schematic",
                     SchematicProvenance.ORIGINAL_MANUFACTURER, "Rocketdyne", "legible")]
    c = lambda n: f"J2-{n}"  # noqa: E731
    L = "slide J2-4; MSFC-MAN-503 pp.5-5..5-7"
    nodes = [node(x.component_id, x.component_type, x.label, x.ownership, BO, L, x.component_id) for x in comps]
    edges = [
        edge("e1", c("LOX-IN"), c("OTP-P"), FLUID, "LOX", "feed", SH, L),
        edge("e2", c("OTP-P"), c("MOV"), FLUID, "LOX", "main oxidizer", SH, L),
        edge("e3", c("MOV"), c("INJ"), FLUID, "LOX", "main oxidizer", SH, L),
        edge("e4", c("OTP-P"), c("GGV"), FLUID, "LOX", "GG oxidizer", SH, L),
        edge("e5", c("GGV"), c("GG"), FLUID, "LOX", "GG oxidizer", SH, L),
        edge("e6", c("OTP-P"), c("MRCV"), FLUID, "LOX", "discharge-to-inlet bypass", BO, L),
        edge("e7", c("MRCV"), c("OTP-P"), FLUID, "LOX", "return to pump inlet", BO, L),
        edge("e8", c("OTP-P"), c("HEX"), FLUID, "LOX", "to heat exchanger", BO, L),
        edge("e9", c("HEX"), c("LOX-PRESS"), FLUID, "GOX", "stage LOX tank pressurization", BO, L),
        edge("e10", c("FTP-P"), c("MFV"), FLUID, "LH2", "main fuel", SH, L),
        edge("e11", c("MFV"), c("INJ"), FLUID, "H2", "regen coolant then injector", BO, L),
        edge("e12", c("FTP-P"), c("GG"), FLUID, "LH2", "GG fuel", SH, L),
        edge("e13", c("INJ"), c("LH2-PRESS"), FLUID, "GH2", "stage LH2 tank pressurization", BO, L),
        edge("e14", c("STANK"), c("FTP-T"), FLUID, "GH2", "spin start", BO, L),
        edge("e15", c("GG"), c("FTP-T"), FLUID, "hot gas", "first turbine in series", BO, L),
        edge("e16", c("FTP-T"), c("OTP-T"), FLUID, "hot gas", "crossover to second turbine", BO, L, split="H1"),
        edge("e17", c("FTP-T"), c("OTBV"), FLUID, "hot gas", "oxidizer turbine bypass", BO, L, split="H1"),
        edge("e18", c("OTP-T"), c("HEX"), FLUID, "hot gas", "turbine exhaust", BO, L),
        edge("e19", c("HEX"), c("NOZ-DUMP"), FLUID, "hot gas", "dump at nozzle 2:1 split", BO, L, merge="H2"),
        edge("e20", c("OTBV"), c("NOZ-DUMP"), FLUID, "hot gas", "bypass rejoins", SH, L, merge="H2"),
        edge("e21", c("INJ"), c("TC"), FLUID, "propellants", "injection", SH, L),
        edge("e22", c("TC"), c("AMB"), FLUID, "combustion gas", "exhaust", SH, L),
        edge("e23", c("NOZ-DUMP"), c("AMB"), FLUID, "turbine exhaust", "exhaust via nozzle", TX, L),
        edge("e24", c("FTP-T"), c("FTP-P"), SHAFT, None, "direct drive", TX, L),
        edge("e25", c("OTP-T"), c("OTP-P"), SHAFT, None, "direct drive", TX, L),
        edge("e26", c("OTP-T"), c("HYD-PUMP"), SHAFT, None, "drives main hydraulic pump", TX, L),
    ]
    topo = [TopologyGraph("TOPO-J2", SubjectRef(CFG, k), "J-2 flow and drives", SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH,
                          ("SCH-J2-S4",), ("SRC-COFFMAN-J2", "SRC-MSFC-MAN-503"),
                          Completeness(False, ("pneumatic control", "ASI supply", "bleed valves")),
                          tuple(nodes), tuple(edges))]
    P = SubjectRef
    a = [
        num("J2-PC", P(CFG, k), "performance.chamber_pressure", "717", 717, "psia", "SRC-COFFMAN-J2",
            "slide J2-3", op="OP-J2-MR55", cond=pc(station=PressureStation.NOZZLE_STAGNATION)),
        num("J2-THRUST-230", P(CFG, k), "performance.thrust", "230,000", 230000, "lb", "SRC-COFFMAN-J2", "slide J2-3",
            op="OP-J2-MR55", cond=Conditions(environment=Environment.VACUUM)),
        num("J2-THRUST-225", P(CFG, "CFG-J2-225K"), "performance.thrust", "the 225,000-pound version", 225000, "lb",
            "SRC-COFFMAN-J2", "text p.3", kind=ValueKind.RATED, cond=Conditions(environment=Environment.UNKNOWN)),
        num("J2-MR-ALT", P(CFG, k), "propellants.mixture_ratio", "4.5:1", 4.5, ":1", "SRC-COFFMAN-J2", "text p.2",
            op="OP-J2-MR45", cond=Conditions(mixture_ratio_form=MixtureRatioForm.OXIDIZER_TO_FUEL,
                                             mixture_ratio_basis=MixtureRatioBasis.ENGINE)),
        Assertion("J2-TURB-SERIES", P(CFG, k), "turbines.arrangement", EnumValue("SERIES_FUEL_THEN_OXIDIZER"),
                  "series turbine arrangement, through the fuel turbopump and then over into the oxidizer turbopump",
                  "", Conditions(), ValueKind.NOMINAL, ValueStatus.REPORTED, Admissibility.ADMITTED,
                  "SRC-COFFMAN-J2", "text p.2", OPENED),
    ]
    return s, fam, var, cfg, ops, comps, sch, topo, a, []


# --------------------------------------------------------------------- RL10A-3-3A


def rl10():
    s = [source("SRC-CR195478"), source("SRC-NTRS-19910018888")]
    fam = [EngineFamily("FAM-RL10", "RL10")]
    var = [EngineVariant("VAR-RL10A33A", "FAM-RL10", "RL10A-3-3A")]
    cfg = [EngineConfiguration("CFG-RL10A33A", "VAR-RL10A33A", "RL10A-3-3A (Centaur)", Missing(MissingReason.NOT_AUDITED))]
    ops = [OperatingPoint("OP-RL10-NOM", "CFG-RL10A33A", "normal operating point (475 psia, O/F 5.0)")]
    k = "CFG-RL10A33A"
    parts = [("FINV", T.VALVE), ("FP1", T.PUMP), ("FP2", T.PUMP), ("FCV1", T.VALVE), ("FCV2", T.VALVE),
             ("ORIF", T.ORIFICE), ("JACKET", T.COOLING_JACKET), ("VENT", T.VENTURI), ("TURB", T.TURBINE),
             ("TCV", T.VALVE), ("FSOV", T.VALVE), ("OINV", T.VALVE), ("LOXP", T.PUMP), ("OCV", T.VALVE),
             ("GEAR", T.GEARBOX), ("INJ", T.INJECTOR), ("IGN", T.IGNITER), ("TC", T.THRUST_CHAMBER)]
    comps = [Component(f"RL10-{n}", SubjectRef(CFG, k), t, n, ENG) for n, t in parts] + [
        Component("RL10-OVBD", SubjectRef(CFG, k), T.AMBIENT_SINK, "Vent overboard", AMB)]
    sch = [Schematic("SCH-CR195478-F1", "SRC-CR195478", "Figure 1 (PDF p.13)", "RL10A-3-3A Engine System Schematic",
                     SchematicProvenance.ORIGINAL_AGENCY, "NASA Lewis / NYMA", "all labels legible")]
    c = lambda n: f"RL10-{n}"  # noqa: E731
    L = "CR-195478 Fig. 1; §§2.0, 3.1"
    nodes = [node(x.component_id, x.component_type, x.label, x.ownership, BO, L, x.component_id) for x in comps]
    edges = [
        edge("e1", c("FINV"), c("FP1"), FLUID, "LH2", "feed", SH, L),
        edge("e2", c("FP1"), c("FP2"), FLUID, "LH2", "interstage", SH, L),
        edge("e3", c("FP1"), c("FCV1"), FLUID, "LH2", "interstage cooldown", BO, L),
        edge("e4", c("FCV1"), c("OVBD"), FLUID, "H2", "cooldown vent", BO, L),
        edge("e5", c("FP2"), c("FCV2"), FLUID, "LH2", "discharge cooldown", SH, L),
        edge("e6", c("FCV2"), c("OVBD"), FLUID, "H2", "cooldown vent", BO, L),
        edge("e7", c("FP2"), c("ORIF"), FLUID, "LH2", "pump discharge", SH, L),
        edge("e8", c("ORIF"), c("JACKET"), FLUID, "LH2", "coolant", BO, L),
        edge("e9", c("JACKET"), c("VENT"), FLUID, "GH2", "jacket exit", SH, L),
        edge("e10", c("VENT"), c("TURB"), FLUID, "GH2", "turbine drive", BO, L, split="T1"),
        edge("e11", c("VENT"), c("TCV"), FLUID, "GH2", "turbine bypass", SH, L, split="T1"),
        edge("e12", c("TCV"), c("FSOV"), FLUID, "GH2", "bypass rejoins", SH, L, merge="T2"),
        edge("e13", c("TURB"), c("FSOV"), FLUID, "GH2", "turbine exhaust", SH, L, merge="T2"),
        edge("e14", c("FSOV"), c("INJ"), FLUID, "GH2", "warm hydrogen to injector", BO, L),
        edge("e15", c("OINV"), c("LOXP"), FLUID, "LOX", "feed", SH, L),
        edge("e16", c("LOXP"), c("OCV"), FLUID, "LOX", "discharge", SH, L),
        edge("e17", c("OCV"), c("INJ"), FLUID, "LOX", "oxidizer", SH, L),
        edge("e18", c("INJ"), c("TC"), FLUID, "propellants", "injection", SH, L),
        edge("e19", c("TURB"), c("FP1"), SHAFT, None, "common shaft", BO, L),
        edge("e20", c("TURB"), c("FP2"), SHAFT, None, "common shaft", BO, L),
        edge("e21", c("TURB"), c("GEAR"), SHAFT, None, "shaft to gearbox", BO, L),
        edge("e22", c("GEAR"), c("LOXP"), GEAR, None, "geared LOX pump drive", BO, L),
    ]
    topo = [TopologyGraph("TOPO-RL10A33A", SubjectRef(CFG, k), "RL10A-3-3A expander cycle", SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH,
                          ("SCH-CR195478-F1",), ("SRC-CR195478",),
                          Completeness(False, ("igniter supply", "tank pressurization taps", "control solenoids")),
                          tuple(nodes), tuple(edges))]
    P = SubjectRef
    a = [
        num("RL10-PC", P(CFG, k), "performance.chamber_pressure", "475 psia", 475, "psia", "SRC-CR195478",
            "§4.3 (PDF p.7)", op="OP-RL10-NOM", cond=pc()),
        num("RL10-FP-SPEED", P(COMP, c("FP1")), "pump.speed", "32000 rpm", 32000, "rpm", "SRC-CR195478",
            "§3.1", op="OP-RL10-NOM"),
        num("RL10-LOXP-SPEED", P(COMP, c("LOXP")), "pump.speed", "12800 rpm", 12800, "rpm", "SRC-CR195478",
            "§3.1", op="OP-RL10-NOM"),
        num("RL10-THRUST", P(CFG, k), "performance.thrust", "16,500", 16500, "lb", "SRC-NTRS-19910018888", "p.3",
            op="OP-RL10-NOM", cond=Conditions(environment=Environment.VACUUM)),
        num("RL10-ISP", P(CFG, k), "performance.specific_impulse", "444.4", 444.4, "sec", "SRC-NTRS-19910018888",
            "p.3", op="OP-RL10-NOM", cond=Conditions(environment=Environment.VACUUM, isp_basis=IspBasis.UNKNOWN,
                                                     mixture_ratio=Setting(5.0, ":1"),
                                                     mixture_ratio_form=MixtureRatioForm.OXIDIZER_TO_FUEL,
                                                     mixture_ratio_basis=MixtureRatioBasis.ENGINE)),
        num("RL10-CD", P(CFG, k), "nozzle.discharge_coefficient", "0.975", 0.975, "-", "SRC-CR195478", "§4.3",
            adm=Admissibility.REJECTED_MODEL_PARAMETER, note="model trim, not a hardware fact"),
    ]
    return s, fam, var, cfg, ops, comps, sch, topo, a, []


# --------------------------------------------------------------------- LMDE (pressure-fed, stage-owned pressurization)


def lmde():
    s = [source("SRC-TND7143", digest=h(7143)),
         source("SRC-AER-DPS", digest=h(7143), same="SRC-TND7143", title="duplicate registry entry of TN D-7143"),
         source("SRC-A14DPS", access=BLOCKED, rights_=rights(REVIEW))]
    fam = [EngineFamily("FAM-LMDE", "LM Descent Engine")]
    var = [EngineVariant("VAR-LMDE", "FAM-LMDE", "LMDE")]
    cfg = [EngineConfiguration("CFG-LMDE-FINAL", "VAR-LMDE", "final design (variable-area injector)",
                               Missing(MissingReason.NOT_AUDITED)),
           EngineConfiguration("CFG-LMDE-DEV", "VAR-LMDE", "development (fixed-area helium injection)",
                               Missing(MissingReason.NOT_AUDITED))]
    ops = [OperatingPoint("OP-LMDE-FTP", "CFG-LMDE-FINAL", "fixed throttle point (92.5%)"),
           OperatingPoint("OP-LMDE-MIN", "CFG-LMDE-FINAL", "minimum throttle (10%)")]
    k = "CFG-LMDE-FINAL"
    parts = [("SHE", T.PRESSURANT_TANK, STG), ("FHEX", T.HEAT_EXCHANGER, STG), ("REG", T.REGULATOR, STG),
             ("SOL", T.VALVE, STG), ("QCV", T.CHECK_VALVE, STG), ("OXT", T.TANK, STG), ("FUT", T.TANK, STG),
             ("TRIM", T.ORIFICE, STG), ("FCV", T.VALVE, ENG), ("TCA", T.ACTUATOR, ENG), ("SOV", T.VALVE, ENG),
             ("INJ", T.INJECTOR, ENG), ("FILM", T.ORIFICE, ENG), ("TC", T.COMBUSTION_CHAMBER, ENG),
             ("NOZ", T.NOZZLE_EXTENSION, ENG), ("AMB", T.AMBIENT_SINK, AMB)]
    comps = [Component(f"LMDE-{n}", SubjectRef(CFG, k), t, n, o) for n, t, o in parts]
    sch = [Schematic("SCH-TND7143-F3", "SRC-TND7143", "Figure 3, p.4", "The final DPS design",
                     SchematicProvenance.ORIGINAL_AGENCY, "NASA MSC", "legible"),
           Schematic("SCH-TND7143-F7", "SRC-TND7143", "Figure 7, p.8", "Variable area of the descent engine",
                     SchematicProvenance.ORIGINAL_AGENCY, "NASA MSC", "legible")]
    c = lambda n: f"LMDE-{n}"  # noqa: E731
    L = "TN D-7143 Figs. 3, 7"
    nodes = [node(x.component_id, x.component_type, x.label, x.ownership, SH, L, x.component_id) for x in comps]
    edges = [
        edge("e1", c("SHE"), c("FHEX"), FLUID, "He", "helium heating", SH, L),
        edge("e2", c("FHEX"), c("REG"), FLUID, "He", "warmed helium", SH, L),
        edge("e3", c("REG"), c("SOL"), FLUID, "He", "regulated", SH, L),
        edge("e4", c("SOL"), c("QCV"), FLUID, "He", "regulated", SH, L),
        edge("e5", c("QCV"), c("OXT"), FLUID, "He", "ullage", SH, L),
        edge("e6", c("QCV"), c("FUT"), FLUID, "He", "ullage", SH, L),
        edge("e7", c("OXT"), c("TRIM"), FLUID, "N2O4", "feed", SH, L),
        edge("e8", c("TRIM"), c("FCV"), FLUID, "N2O4", "engine feed", SH, L),
        edge("e9", c("FUT"), c("FCV"), FLUID, "A-50", "engine feed", SH, L),
        edge("e10", c("FUT"), c("FHEX"), FLUID, "A-50", "fuel bypass through heat exchanger", SH, L),
        edge("e11", c("FCV"), c("SOV"), FLUID, "propellants", "throttled flow", SH, L),
        edge("e12", c("SOV"), c("INJ"), FLUID, "propellants", "to injector", SH, L),
        edge("e13", c("SOV"), c("FILM"), FLUID, "A-50", "wall film", SH, L),
        edge("e14", c("FILM"), c("TC"), FLUID, "A-50", "wall film", SH, L),
        edge("e15", c("INJ"), c("TC"), FLUID, "propellants", "injection", SH, L),
        edge("e16", c("TC"), c("NOZ"), FLUID, "combustion gas", "expansion", SH, L),
        edge("e17", c("NOZ"), c("AMB"), FLUID, "combustion gas", "exhaust", SH, L),
        edge("e18", c("TCA"), c("FCV"), LINK, None, "ganged to cavitating venturis", SH, L),
        edge("e19", c("TCA"), c("INJ"), LINK, None, "drives injector sleeve", SH, L),
    ]
    topo = [TopologyGraph("TOPO-LMDE", SubjectRef(CFG, k), "DPS stage + engine", SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH,
                          ("SCH-TND7143-F3", "SCH-TND7143-F7"), (),
                          Completeness(False, ("burst disks and relief valves", "pilot valves")), tuple(nodes), tuple(edges))]
    P = SubjectRef
    a = [
        num("LMDE-THRUST-MAX", P(CFG, k), "performance.thrust", "Maximum-rated thrust: 10 500 lb", 10500, "lb",
            "SRC-TND7143", "p.8", kind=ValueKind.MAXIMUM, cond=Conditions(environment=Environment.UNKNOWN)),
        num("LMDE-ISP", P(CFG, k), "performance.specific_impulse", "305 lbf-sec/lbm", 305, "lbf-sec/lbm",
            "SRC-TND7143", "p.8", kind=ValueKind.DESIGN_VALUE,
            cond=Conditions(environment=Environment.UNKNOWN, isp_basis=IspBasis.UNKNOWN,
                            qualifiers=(Qualifier("condition", "end of duty cycle"),))),
        num("LMDE-MIN-THROTTLE", P(CFG, k), "performance.throttle_setting", "10 percent", 10, "%", "SRC-TND7143",
            "p.10", op="OP-LMDE-MIN", kind=ValueKind.MINIMUM),
        Assertion("LMDE-PC", P(CFG, k), "performance.chamber_pressure", Missing(MissingReason.NOT_REPORTED,
                  "not printed in the pages read"), "", "", pc(PressureBasis.UNKNOWN), ValueKind.UNKNOWN, None,
                  Admissibility.ADMITTED, "SRC-TND7143", "pp.1-36", OPENED),
        Assertion("LMDE-A14-PC", P(CFG, k), "performance.chamber_pressure", Missing(MissingReason.ACCESS_BLOCKED),
                  "", "", pc(PressureBasis.UNKNOWN), ValueKind.UNKNOWN, None, Admissibility.ADMITTED,
                  "SRC-A14DPS", "nasa.gov ALSJ 404", BLOCKED),
    ]
    return s, fam, var, cfg, ops, comps, sch, topo, a, []


# --------------------------------------------------------------------- RD-170 (third-party reconstruction)


def rd170():
    s = [source("SRC-RKWL-1990", SourceAuthority.B, primacy=SourcePrimacy.SECONDARY),
         source("SRC-PARIS-PLACARD-1989", access=SourceAccess.SEARCH_RESULT_ONLY, rights_=rights(REVIEW),
                title="RD-170 Paris Air Show placard (known only through transcription)")]
    fam = [EngineFamily("FAM-RD170", "RD-170 family")]
    var = [EngineVariant("VAR-RD170", "FAM-RD170", "RD-170"), EngineVariant("VAR-RD180", "FAM-RD170", "RD-180")]
    cfg = [EngineConfiguration("CFG-RD170", "VAR-RD170", "Energia booster engine", Missing(MissingReason.NOT_AUDITED))]
    ops = []
    k = "CFG-RD170"
    parts = [("LPOP", T.BOOSTER_PUMP), ("LPFP", T.BOOSTER_PUMP), ("HPOP", T.PUMP), ("HPFP", T.PUMP),
             ("KICK", T.PUMP), ("TURB", T.TURBINE), ("PB1", T.PREBURNER), ("PB2", T.PREBURNER)] + \
            [(f"TCA{i}", T.THRUST_CHAMBER) for i in range(1, 5)]
    comps = [Component(f"RD170-{n}", SubjectRef(CFG, k), t, n, ENG) for n, t in parts]
    sch = [Schematic("SCH-RD170-RKWL", "SRC-RKWL-1990", "PDF p.19 (briefing p.569)",
                     "Soviet RD-170 Propulsion System Schematic Diagram (Based on 1989 Paris Air Show Display Photos)",
                     SchematicProvenance.THIRD_PARTY_RECONSTRUCTION, "Rockwell International", "legible; '?' on paths")]
    c = lambda n: f"RD170-{n}"  # noqa: E731
    L = "Rockwell reconstruction p.569"
    nodes = [node(x.component_id, x.component_type, x.label, x.ownership, SH, L, x.component_id) for x in comps]
    edges = [edge("e1", c("LPOP"), c("HPOP"), FLUID, "LOX", "feed", SH, L),
             edge("e2", c("LPFP"), c("HPFP"), FLUID, "RP-1", "feed", SH, L),
             edge("e3", c("HPOP"), c("PB1"), FLUID, "LOX", "preburner oxidizer", SH, L),
             edge("e4", c("HPOP"), c("PB2"), FLUID, "LOX", "preburner oxidizer", SH, L),
             edge("e5", c("HPFP"), c("KICK"), FLUID, "RP-1", "kick stage", SH, L),
             edge("e6", c("KICK"), c("PB1"), FLUID, "RP-1", "preburner fuel", SH, L),
             edge("e7", c("KICK"), c("PB2"), FLUID, "RP-1", "preburner fuel", SH, L),
             edge("e8", c("PB1"), c("TURB"), FLUID, "ox-rich gas", "turbine drive", SH, L, merge="G1"),
             edge("e9", c("PB2"), c("TURB"), FLUID, "ox-rich gas", "turbine drive", SH, L, merge="G1"),
             edge("e10", c("HPOP"), c("LPOP"), FLUID, "LOX", "LP pump liquid turbine drive", SH, L),
             edge("e11", c("TURB"), c("HPOP"), SHAFT, None, "single shaft", SH, L),
             edge("e12", c("TURB"), c("HPFP"), SHAFT, None, "single shaft", SH, L)] + [
        edge(f"x{i}", c("TURB"), c(f"TCA{i}"), FLUID, "ox-rich gas", "turbine exhaust to chamber", SH if i == 1 else INF,
             L, split="X1") for i in range(1, 5)]
    topo = [TopologyGraph("TOPO-RD170", SubjectRef(CFG, k), "RD-170 as reconstructed by Rockwell", SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH,
                          ("SCH-RD170-RKWL",), (), Completeness(False, ("valves and control", "start system", "cooling circuits")),
                          tuple(nodes), tuple(edges))]
    P = SubjectRef
    a = [
        num("RD170-THRUST-SL", P(CFG, k), "performance.thrust", "Poussee au sol - 740 ts", 740, "t", "SRC-RKWL-1990",
            "PDF p.16 placard transcription", cond=Conditions(environment=Environment.SEA_LEVEL),
            first_stated_by="SRC-PARIS-PLACARD-1989"),
        num("RD170-PC", P(CFG, k), "performance.chamber_pressure", "250 kgs/cm2", 250, "kgs/cm2", "SRC-RKWL-1990",
            "PDF p.16", cond=pc(PressureBasis.UNKNOWN), first_stated_by="SRC-PARIS-PLACARD-1989"),
        num("RD170-MR-258", P(CFG, k), "propellants.mixture_ratio", "MR 2.58", 2.58, ":1", "SRC-RKWL-1990", "PDF p.16",
            cond=Conditions(mixture_ratio_form=MixtureRatioForm.OXIDIZER_TO_FUEL, mixture_ratio_basis=MixtureRatioBasis.UNKNOWN)),
        num("RD170-MR-247", P(CFG, k), "propellants.mixture_ratio", "MR = 2.47", 2.47, ":1", "SRC-RKWL-1990", "PDF p.22",
            cond=Conditions(mixture_ratio_form=MixtureRatioForm.OXIDIZER_TO_FUEL, mixture_ratio_basis=MixtureRatioBasis.UNKNOWN)),
    ]
    x = [Conflict("CF-RD170-MR", "propellants.mixture_ratio", ("RD170-MR-258", "RD170-MR-247"),
                  ConflictResolution.UNRESOLVED, (), "Both printed in one briefing; neither tied to the placard.")]
    lin = [LineageEdge("LIN-RD180", LineageKind.DERIVED_FROM, SubjectRef(VAR, "VAR-RD180"), SubjectRef(VAR, "VAR-RD170"),
                       ("SRC-RKWL-1990",))]
    return s, fam, var, cfg, ops, comps, sch, topo, a, x, lin


def stress_corpus(**replace) -> EngineEvidenceCorpus:
    parts = {k: [] for k in ("sources", "families", "variants", "configurations", "operating_points", "units",
                             "aliases", "lineage", "components", "schematics", "topologies", "assertions", "conflicts")}
    for builder in (rs25, j2, rl10, lmde, rd170):
        out = builder()
        s, fam, var, cfg, ops, comps, sch, topo, a, x = out[:10]
        for key, items in (("sources", s), ("families", fam), ("variants", var), ("configurations", cfg),
                           ("operating_points", ops), ("components", comps), ("schematics", sch),
                           ("topologies", topo), ("assertions", a), ("conflicts", x)):
            parts[key] += items
        if len(out) > 10:
            parts["lineage"] += out[10]
    parts["units"] = [PropulsionUnit("UNIT-SII", PropulsionUnitKind.STAGE_PROPULSION, "S-II stage propulsion",
                                     (UnitMember(SubjectRef(CFG, "CFG-J2-230K"), 5, "main engines"),))]
    parts.update(replace)
    return EngineEvidenceCorpus(**{k: tuple(v) for k, v in parts.items()})
