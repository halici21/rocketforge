"""EV-3: the CEA compatibility bridge, and the explicit-action boundary around it.

Two halves.

**The bridge** (R1 integration blueprint section 4): RP-1311 Example 5 is
executable and verified where NASA CEA is installed, and "provider unavailable"
-- not blocked -- where it is not; an incomplete source definition is blocked
naming the field; an absent library name is named with the thermo.lib hash; a
formulation that does not close is refused, never normalised; a source-defined
ingredient stays source-defined; nothing is dropped, substituted or re-spelled;
a payload withheld by shipping policy stops at the separate access gate --
compatibility is not evaluated, and no scientific blocker is invented; a record
with no formulation, or with VA not applicable, is not a CEA target. Library
names are probed once per process per thermo.lib identity. None of it solves.

**The boundary**: building the controller, selecting, filtering and inspecting
cost zero probes and zero solves; only ``checkCompatibility()`` probes (still
zero solves); only ``openInThermochemistry()`` hands a case over (zero solves),
and an answer never outlives the selection it was asked for.

Every synthetic record here is built from the EV-1 types in a temporary folder
and is test-only; the shipped corpus is only ever read.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from rocketforge.application.analysis import evidence_cea_bridge as bridge
from rocketforge.application.analysis import propulsion_evidence_service as service
from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis.propulsion_evidence_controller import (
    PropulsionEvidenceController,
)
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
    record_to_json,
    sources_to_json,
)
from rocketforge.providers.cea_solid import RP1311_EXAMPLE5

State = bridge.CompatibilityState
ROOT = pathlib.Path(__file__).resolve().parents[2]
SHIPPED = ROOT / "rocketforge" / "data" / "evidence"
RP1311 = "DS-RP1311-E5"
FAKE_SHA = "f" * 64

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable, reason=f"NASA CEA provider unavailable ({_STATUS.status})")


# ------------------------------------------------------------------ builders

OPEN, META = "S-EV3-OPEN", "S-EV3-META"


def _source(sid, shipping):
    return SourceReference(
        source_id=sid, organization="Test Org", authors=("A. Author",), title=f"Title of {sid}",
        year=None, identifiers={"report_number": f"R-{sid}"},
        locator=f"https://example.invalid/{sid}", source_type="report",
        access_class=AccessClass.PUBLIC_OPEN, rights_statement="as stated by the test",
        shipping=shipping, tier=2)


TEST_SOURCES = {OPEN: _source(OPEN, ShippingPolicy.VALUES_WITH_ATTRIBUTION),
                META: _source(META, ShippingPolicy.METADATA_ONLY)}


def _v(value, unit, sid=OPEN):
    return ReportedValue(value, unit, sid, "p. 3, Table 2", ValueStatus.REPORTED)


def _binder(**overrides):
    parts = dict(formula={"C": _v(1.0, "atoms per formula unit"),
                          "H": _v(1.5, "atoms per formula unit")},
                 enthalpy=_v(-1000.0, "cal/mol"),
                 reference_temperature=_v(298.15, "K"),
                 molecular_weight=_v(13.5, "g/mol"))
    parts.update(overrides)
    return CustomDefinition(**parts)


def _ingredients(ox=0.8, binder=0.2, *, ox_name="NH4CLO4(I)", custom=None):
    return (IngredientReference("Oxidiser A", _v(ox, "mass fraction"), ox_name),
            IngredientReference("Binder X", _v(binder, "mass fraction"), None,
                                custom if custom is not None else _binder()))


def _propellant(ingredients=None, sid=OPEN, **kw):
    ingredients = ingredients if ingredients is not None else _ingredients()
    base = dict(propellant_id="P-EV3", source_ids=(sid,), family="test family",
                source_name="test blend",
                exact_formulation=all(isinstance(i.fraction, ReportedValue) for i in ingredients),
                basis="mass_fraction", ingredients=ingredients,
                density=Missing(MissingReason.NOT_REPORTED),
                initial_temperature=_v(298.15, "K", sid) if sid == OPEN
                else Missing(MissingReason.WITHHELD_RIGHTS))
    base.update(kw)
    return PropellantReference(**base)


def _record(rid="DS-EV3-A", propellant="default", *, sid=OPEN, va=EvidenceStatus.SOURCE_COMPLETE_CANDIDATE,
            kind=RecordKind.PROPELLANT, executable_key=None):
    if propellant == "default":
        propellant = _propellant(sid=sid)
    return EvidenceRecord(
        record_id=rid, title=f"Record {rid}", kind=kind, source_ids=(sid,),
        capabilities={Dimension.VA: va, Dimension.VB: EvidenceStatus.NOT_APPLICABLE,
                      Dimension.VC: EvidenceStatus.NOT_APPLICABLE,
                      Dimension.VD: EvidenceStatus.NOT_APPLICABLE},
        capability_notes={}, propellant=propellant, comparison_case_ids=(),
        executable_key=executable_key, blockers=(), notes="")


def shipped():
    corpus = service.load_corpus()
    return corpus, corpus.record(RP1311)


def codes(assessment):
    return [b.code for b in assessment.blockers]


# ------------------------------------------------------------- instruments


@pytest.fixture()
def counters(monkeypatch):
    """Counting wrappers: probes (gateway availability, provider construction,
    library probes) and solves (every solid/bipropellant chamber and c* path)."""
    import rocketforge.providers.cea as cea_pkg
    import rocketforge.providers.cea_solid as cea_solid
    import rocketforge.providers.cea_solid.cstar as cea_cstar
    import rocketforge.providers.cea_solid.provider as cea_solid_provider
    from rocketforge.application.analysis import thermochemistry_controller as thermo_controller
    from rocketforge.application.analysis import thermochemistry_service as thermo_service
    from rocketforge.application.analysis import thermochemistry_solid_service as solid_service

    counts = {"probe": {}, "solve": {}}

    def wrap(owner, attr, kind):
        original = getattr(owner, attr)
        label = f"{getattr(owner, '__name__', owner)}.{attr}"

        def counted(*args, **kwargs):
            counts[kind][label] = counts[kind].get(label, 0) + 1
            return original(*args, **kwargs)
        monkeypatch.setattr(owner, attr, counted)

    for name in ("availability", "chamber_provider", "provider_provenance", "_cea_module",
                 "probe_solid_library_species", "solid_ingredient_catalogue"):
        wrap(gateway, name, "probe")
    for owner in (cea_solid, cea_solid_provider):
        wrap(owner, "library_species_available", "probe")
    wrap(cea_pkg.CEAThermochemistryProvider, "__init__", "probe")
    for owner, name in ((gateway, "solve_solid_chamber_state"),
                        (gateway, "solve_solid_equilibrium_cstar"),
                        (solid_service, "solve_solid_chamber_state"),
                        (solid_service, "solve_solid_equilibrium_cstar"),
                        (solid_service, "solve_solid_case"),
                        (thermo_controller, "solve_solid_case"),
                        (thermo_controller, "solve_case"),
                        (thermo_service, "solve_case"),
                        (cea_solid, "solve_solid_chamber"),
                        (cea_solid, "solve_solid_chamber_raw"),
                        (cea_solid, "solve_solid_equilibrium_cstar"),
                        (cea_solid_provider, "solve_solid_chamber"),
                        (cea_solid_provider, "solve_solid_chamber_raw"),
                        (cea_cstar, "solve_solid_equilibrium_cstar"),
                        (cea_pkg.CEAThermochemistryProvider, "solve_chamber")):
        wrap(owner, name, "solve")
    counts["total"] = lambda kind: sum(counts[kind].values())
    return counts


@pytest.fixture()
def fake_library(monkeypatch):
    """The gateway probe answered by a stated library: every name is present
    except those in ``absent``. Records exactly which names were asked."""
    state = {"absent": set(), "asked": []}

    def probe(names):
        asked = tuple(dict.fromkeys(names))
        state["asked"].append(asked)
        return gateway.LibrarySpeciesProbe(
            usable=True, names=asked,
            present=tuple(n for n in asked if n not in state["absent"]),
            absent=tuple(n for n in asked if n in state["absent"]),
            status="stub", library_version="stub", database="thermo.lib",
            database_sha256=FAKE_SHA)
    monkeypatch.setattr(gateway, "probe_solid_library_species", probe)
    return state


@pytest.fixture(autouse=True)
def fresh_probe_cache(monkeypatch):
    """Every test starts with no library name known to this process."""
    monkeypatch.setattr(gateway, "_species_probes", {})


# ======================================================================
# the bridge
# ======================================================================


@requires_cea
def test_rp1311_is_executable_and_verified_against_the_probed_library(counters):
    corpus, record = shipped()
    before = record_to_json(record)
    result = bridge.assess(record, corpus.sources)
    assert result.state is State.EXECUTABLE_VERIFIED and result.executable
    assert result.blockers == ()
    # the identity actually probed, and it is the database the record's source names
    assert result.probe.usable and result.probe.library_version == "3.3.4"
    assert result.probe.database == "thermo.lib"
    assert result.probe.database_sha256 == \
        corpus.sources["S-NASA-CEA-334"].identifiers["thermo_lib_sha256"]
    assert result.probe.present == ("NH4CLO4(I)", "AL(cr)", "MgO(cr)", "H2O(L)")
    # equal to the executable authority, field for field, so Open may load it
    assert bridge.formulation_differences(result.formulation, RP1311_EXAMPLE5) == ()
    assert result.thermochemistry_key == "rp1311-example5"
    assert record_to_json(record) == before
    assert counters["total"]("probe") > 0
    assert counters["probe"]["rocketforge.providers.cea_solid.library_species_available"] == 1
    assert counters["total"]("solve") == 0, counters["solve"]


def test_rp1311_without_a_provider_is_unavailable_not_blocked(absent_gateway, counters):
    corpus, record = shipped()
    result = bridge.assess(record, corpus.sources)
    assert result.state is State.PROVIDER_UNAVAILABLE
    assert result.blockers == () and result.formulation is None
    assert not result.probe.usable and result.probe.present == result.probe.absent == ()
    assert result.probe.status == "not_installed"
    assert "unavailable (not_installed)" in bridge.identity_text(result.probe)
    assert counters["total"]("solve") == 0
    assert "rocketforge.providers.cea_solid.library_species_available" not in counters["probe"]


@pytest.mark.skipif(_STATUS.usable, reason="the base environment has no NASA CEA")
def test_rp1311_in_the_base_environment_is_provider_unavailable(counters):
    corpus, record = shipped()
    assert bridge.assess(record, corpus.sources).state is State.PROVIDER_UNAVAILABLE
    assert counters["total"]("solve") == 0


@pytest.mark.parametrize("part", ["enthalpy", "reference_temperature", "formula"])
def test_a_missing_custom_datum_blocks_naming_the_field(fake_library, counters, part):
    binder = _binder(**{part: Missing(MissingReason.NOT_REPORTED, "not printed")})
    record = _record(propellant=_propellant(_ingredients(custom=binder)))
    result = bridge.assess(record, TEST_SOURCES)
    assert result.state is State.BLOCKED_INCOMPLETE_CUSTOM
    [blocker] = result.blockers
    assert blocker.code == "CUSTOM_THERMO_INCOMPLETE" and blocker.category == "evidence"
    assert blocker.field == f"ingredients[1].custom.{part}" and blocker.ingredient == "Binder X"
    assert "NOT_REPORTED" in blocker.detail and result.formulation is None
    assert counters["total"]("solve") == 0


def test_an_absent_library_name_is_named_with_the_thermo_hash(fake_library):
    fake_library["absent"] = {"UNOBTANIUM(cr)"}
    record = _record(propellant=_propellant(_ingredients(ox_name="UNOBTANIUM(cr)")))
    result = bridge.assess(record, TEST_SOURCES)
    assert result.state is State.BLOCKED and result.formulation is None
    [blocker] = result.blockers
    assert (blocker.code, blocker.category, blocker.name, blocker.database_sha256) == (
        "LIBRARY_SPECIES_ABSENT", "library", "UNOBTANIUM(cr)", FAKE_SHA)
    assert "UNOBTANIUM(cr)" in blocker.detail and FAKE_SHA in blocker.detail
    assert fake_library["asked"] == [("UNOBTANIUM(cr)",)]          # the custom binder is not probed


def test_a_sum_of_098_is_refused_not_normalised(fake_library, counters):
    record = _record(propellant=_propellant(_ingredients(ox=0.78, binder=0.20)))
    before = record_to_json(record)
    result = bridge.assess(record, TEST_SOURCES)
    assert result.state is State.UNDERDEFINED and result.formulation is None
    assert codes(result) == ["MASS_FRACTION_SUM"]
    assert "0.98" in result.blockers[0].detail and "not normalised" in result.blockers[0].detail
    assert record_to_json(record) == before
    assert [i.fraction.value for i in record.propellant.ingredients] == [0.78, 0.20]
    assert counters["total"]("solve") == 0


def test_a_source_defined_ingredient_stays_custom_with_exact_fractions(fake_library):
    corpus, record = shipped()
    result = bridge.assess(record, corpus.sources)
    assert result.state is State.EXECUTABLE_VERIFIED
    built = result.formulation
    # nothing dropped, order kept, fractions exactly as stored
    assert len(built.ingredients) == len(record.propellant.ingredients) == 5
    assert built.mass_fractions == tuple(i.fraction.value for i in record.propellant.ingredients)
    binder = built.ingredients[1]
    assert binder.name == "CHOS-Binder" and binder.custom is not None
    stored = record.propellant.ingredients[1].custom
    assert dict(binder.custom.formula) == {e: v.value for e, v in stored.formula.items()}
    assert binder.custom.heat_of_formation == stored.enthalpy.value
    assert binder.custom.heat_of_formation_units == stored.enthalpy.unit == "cal/mol"
    assert binder.custom.molecular_weight == stored.molecular_weight.value
    assert "S-NASA-CEA-334" in binder.custom.source
    text = json.dumps([i.name for i in built.ingredients])
    assert not any(word in text for word in ("HTPB", "PBAN", "GAP"))
    # custom names are never probed as library species
    assert fake_library["asked"] == [("NH4CLO4(I)", "AL(cr)", "MgO(cr)", "H2O(L)")]


def test_a_missing_fraction_is_named_and_the_ingredient_never_dropped(fake_library):
    ingredients = (IngredientReference("Oxidiser A", _v(0.8, "mass fraction"), "NH4CLO4(I)"),
                   IngredientReference("Binder X", Missing(MissingReason.NOT_REPORTED, "lumped"),
                                       None, _binder()))
    result = bridge.assess(_record(propellant=_propellant(ingredients)), TEST_SOURCES)
    assert result.state is State.UNDERDEFINED and result.formulation is None
    assert codes(result) == ["NOT_EXACT_FORMULATION", "VALUE_MISSING"]
    missing = result.blockers[1]
    assert missing.field == "ingredients[1].fraction" and missing.ingredient == "Binder X"
    assert "NOT_REPORTED" in missing.detail and "not read as zero" in missing.detail


def test_a_withheld_payload_is_a_rights_block_not_a_scientific_one(fake_library, counters):
    withheld = Missing(MissingReason.WITHHELD_RIGHTS, "printed, not shippable")
    ingredients = (IngredientReference("Oxidiser A", withheld, "NH4CLO4(I)"),
                   IngredientReference("Binder X", withheld, None, _binder(
                       formula=withheld, enthalpy=withheld, reference_temperature=withheld,
                       molecular_weight=withheld)))
    record = _record("DS-EV3-META", _propellant(ingredients, sid=META), sid=META)
    result = bridge.assess(record, TEST_SOURCES)
    # the separate access gate stopped it: compatibility was not evaluated
    assert result.state is None and not result.evaluated and not result.executable
    assert result.access is not None and not result.access.permitted
    assert bridge.access_gate(record, TEST_SOURCES) == result.access
    restrictions = result.access.restrictions
    assert {r.code for r in restrictions} == {"WITHHELD_RIGHTS"}
    assert "ingredients[0].fraction" in [r.field for r in restrictions]
    assert "initial_temperature" in [r.field for r in restrictions]
    assert all("METADATA_ONLY" in r.policies and "METADATA_ONLY" in r.detail
               for r in restrictions)
    # rights are not a scientific state, and no scientific blocker is invented
    assert "WITHHELD_RIGHTS" not in {s.value for s in State}
    assert result.state not in (State.UNDERDEFINED, State.PROVIDER_UNAVAILABLE,
                                State.BLOCKED, State.BLOCKED_INCOMPLETE_CUSTOM)
    assert result.blockers == () and bridge.blocker_rows(result) == []
    assert result.formulation is None
    assert [row["code"] for row in bridge.access_rows(result)] == ["WITHHELD_RIGHTS"] * len(
        restrictions)
    # nothing was probed and nothing solved
    assert fake_library["asked"] == [] and result.probe is None
    assert counters["total"]("probe") == 0 and counters["total"]("solve") == 0


def test_a_permitted_record_passes_the_access_gate_into_the_assessment(fake_library):
    record = _record()
    assert bridge.access_gate(record, TEST_SOURCES).permitted
    result = bridge.assess(record, TEST_SOURCES)
    assert result.evaluated and result.access.permitted and result.access.restrictions == ()
    assert result.state is State.EXECUTABLE_SOURCE_COMPLETE
    assert fake_library["asked"] == [("NH4CLO4(I)",)]


def test_kno3_phase_names_are_probed_verbatim_and_never_mapped(fake_library):
    fake_library["absent"] = {"KNO3(cr)"}
    record = _record(propellant=_propellant(_ingredients(ox_name="KNO3(cr)")))
    result = bridge.assess(record, TEST_SOURCES)
    assert fake_library["asked"] == [("KNO3(cr)",)]
    assert result.state is State.BLOCKED and result.blockers[0].name == "KNO3(cr)"
    assert "KNO3(a)" not in json.dumps(bridge.blocker_rows(result))


@requires_cea
def test_kno3_phase_names_against_the_real_library(counters):
    """KNO3(cr) is not a thermo.lib name; KNO3(a) is. Neither stands in for the other."""
    cr = bridge.assess(_record(propellant=_propellant(_ingredients(ox_name="KNO3(cr)"))),
                       TEST_SOURCES)
    assert cr.state is State.BLOCKED
    assert [(b.code, b.name) for b in cr.blockers] == [("LIBRARY_SPECIES_ABSENT", "KNO3(cr)")]
    assert cr.blockers[0].database_sha256 == cr.probe.database_sha256 != ""
    a = bridge.assess(_record(propellant=_propellant(_ingredients(ox_name="KNO3(a)"))),
                      TEST_SOURCES)
    assert "KNO3(a)" in a.probe.present and "LIBRARY_SPECIES_ABSENT" not in codes(a)
    assert counters["total"]("solve") == 0


@pytest.mark.parametrize("record", [
    _record("DS-EV3-REF", None, kind=RecordKind.REFERENCE),
    _record("DS-EV3-NA", va=EvidenceStatus.NOT_APPLICABLE),
], ids=["no-propellant", "va-not-applicable"])
def test_not_a_cea_target_is_decided_from_the_record_alone(record, fake_library, counters):
    result = bridge.assess(record, TEST_SOURCES)
    assert result.state is State.NOT_A_CEA_TARGET
    assert result.blockers == () and result.probe is None and result.formulation is None
    assert not service.is_cea_target(record)
    assert fake_library["asked"] == [] and counters["total"]("probe") == 0
    assert counters["total"]("solve") == 0


def test_no_surrogate_is_substituted_for_an_undefined_binder(fake_library):
    ingredients = (IngredientReference("Oxidiser A", _v(0.8, "mass fraction"), "NH4CLO4(I)"),
                   IngredientReference("HTPB", _v(0.2, "mass fraction")))
    result = bridge.assess(_record(propellant=_propellant(ingredients)), TEST_SOURCES)
    assert result.state is State.UNDERDEFINED and codes(result) == ["NO_THERMO_DEFINITION"]
    assert result.blockers[0].ingredient == "HTPB"
    assert fake_library["asked"] == [("NH4CLO4(I)",)]              # "HTPB" is never looked up


def test_an_ambiguous_definition_is_not_resolved_automatically(fake_library):
    ingredients = (IngredientReference("Oxidiser A", _v(0.8, "mass fraction"), "NH4CLO4(I)"),
                   IngredientReference("Binder X", _v(0.2, "mass fraction"), "C(gr)", _binder()))
    result = bridge.assess(_record(propellant=_propellant(ingredients)), TEST_SOURCES)
    assert result.state is State.UNDERDEFINED and codes(result) == ["AMBIGUOUS_THERMO_DEFINITION"]


def test_units_as_printed_are_refused_not_converted(fake_library):
    record = _record(propellant=_propellant(_ingredients(custom=_binder(
        reference_temperature=_v(25.0, "degC")))))
    result = bridge.assess(record, TEST_SOURCES)
    assert result.state is State.BLOCKED and codes(result) == ["UNIT_NOT_ACCEPTED"]
    assert "degC" in result.blockers[0].detail and "not converted" in result.blockers[0].detail


def test_physics_refusal_is_reported_word_for_word(fake_library):
    record = _record(propellant=_propellant(_ingredients(custom=_binder(
        enthalpy=_v(-100.0, "kJ/kg")))))
    result = bridge.assess(record, TEST_SOURCES)
    assert result.state is State.BLOCKED and codes(result) == ["PHYSICS_REFUSED"]
    assert "heat_of_formation_units" in result.blockers[0].detail
    assert result.blockers[0].category == "physics"


def test_a_source_complete_record_without_a_catalogue_case_cannot_be_opened(fake_library):
    result = bridge.assess(_record(), TEST_SOURCES)
    assert result.state is State.EXECUTABLE_SOURCE_COMPLETE and result.formulation is not None
    assert result.thermochemistry_key is None
    assert "no Thermochemistry case" in result.thermochemistry_note
    assert result.notes == ()


def test_an_executable_key_whose_case_differs_is_not_opened_in_its_place(fake_library):
    result = bridge.assess(_record(executable_key="rp1311-example5"), TEST_SOURCES)
    assert result.executable and result.thermochemistry_key is None
    assert "differs" in result.thermochemistry_note
    unknown = bridge.assess(_record(executable_key="no-such-case"), TEST_SOURCES)
    assert unknown.thermochemistry_key is None and "no-such-case" in unknown.thermochemistry_note


def test_formulation_differences_names_each_changed_field():
    from dataclasses import replace
    binder = RP1311_EXAMPLE5.ingredients[1]
    changed = replace(RP1311_EXAMPLE5, ingredients=(
        RP1311_EXAMPLE5.ingredients[0],
        replace(binder, custom=replace(binder.custom, heat_of_formation=-2999.0)),
        *RP1311_EXAMPLE5.ingredients[2:]))
    assert bridge.formulation_differences(RP1311_EXAMPLE5, RP1311_EXAMPLE5) == ()
    [difference] = bridge.formulation_differences(changed, RP1311_EXAMPLE5)
    assert "CHOS-Binder enthalpy" in difference


def test_a_molecular_weight_the_source_omits_is_noted_not_invented(fake_library):
    record = _record(propellant=_propellant(_ingredients(custom=_binder(
        molecular_weight=Missing(MissingReason.NOT_REPORTED)))))
    result = bridge.assess(record, TEST_SOURCES)
    assert result.executable and result.formulation.ingredients[1].custom.molecular_weight is None
    assert any("derive it from the formula" in note for note in result.notes)


# ======================================================================
# the explicit-action boundary
# ======================================================================


def write_corpus(folder, extra_records=()):
    """The shipped RP-1311 record and its sources, plus test-only records."""
    corpus = service.load_corpus()
    (folder / "records").mkdir(parents=True)
    (folder / "sources.json").write_text(
        sources_to_json([*corpus.sources.values(), *TEST_SOURCES.values()]), encoding="utf-8")
    for record in (*corpus.records, *extra_records):
        (folder / "records" / f"{record.record_id}.json").write_text(
            record_to_json(record), encoding="utf-8")
    return folder


EXTRA = (
    _record("DS-EV3-A"),
    _record("DS-EV3-REF", None, kind=RecordKind.REFERENCE),
    _record("DS-EV3-SUM", _propellant(_ingredients(ox=0.78, binder=0.20))),
)


@pytest.fixture()
def corpus_root(tmp_path):
    return write_corpus(tmp_path / "evidence", EXTRA)


class FakeThermochemistry:
    """What openInThermochemistry() may touch: the mode, the loader, the case."""

    def __init__(self):
        self.formulationKind = "bipropellant"
        self.loaded: list[str] = []
        self.calculated = 0

    def loadSolidFormulation(self, key):
        self.loaded.append(key)

    def calculate(self):                      # never called by the bridge or the controller
        self.calculated += 1


def browse(controller):
    """Everything a person can do on the page without asking for a check."""
    for rid in [row["recordId"] for row in controller.library.rows()]:
        controller.selectRecord(rid)
        for name in ("compatibilityState", "compatibilityChecked", "canCheckCompatibility",
                     "compatibilityLabel", "compatibilityTone", "compatibilityMeaning",
                     "compatibilityIdentity", "compatibilityNotes", "compatibilityBlockerCount",
                     "canOpenInThermochemistry", "openUnavailableReason", "inspectionReadout",
                     "recordTitle", "formulationLine", "payloadNote", "tableRowCount"):
            getattr(controller, name)
        for row in range(controller.tableRowCount):
            controller.inspectTableRow(row)
            controller.inspectionReadout
        controller.inspectRecord()
        controller.openInThermochemistry()            # not offered: must do nothing
    controller.setFilterStatus("REGRESSION_LOCKED")
    controller.setFilterDimension("VA")
    controller.setFilterShipping("VALUES_WITH_ATTRIBUTION")
    controller.clearFilters()


def test_browsing_probes_nothing_and_solves_nothing(qt_app, corpus_root, counters):
    thermo = FakeThermochemistry()
    controller = PropulsionEvidenceController(root=corpus_root, thermochemistry=thermo)
    browse(controller)
    assert counters["total"]("probe") == 0, counters["probe"]
    assert counters["total"]("solve") == 0, counters["solve"]
    assert thermo.loaded == [] and thermo.formulationKind == "bipropellant"


def test_a_target_opens_not_checked_and_a_non_target_says_so_without_a_probe(
        qt_app, corpus_root, counters):
    controller = PropulsionEvidenceController(root=corpus_root)
    controller.selectRecord(RP1311)
    assert controller.compatibilityState == "NOT_CHECKED" and not controller.compatibilityChecked
    assert controller.compatibilityLabel == "Not checked" and controller.compatibilityTone == "none"
    assert controller.canCheckCompatibility and not controller.canOpenInThermochemistry
    assert controller.compatibilityIdentity == "" and controller.compatibilityBlockerCount == 0
    assert "installed" not in controller.compatibilityMeaning      # no provider claim unprobed
    section = controller.inspectionReadout["sections"][2]
    assert section["title"] == "CEA compatibility"
    assert {"label": "State", "value": "Not checked"} in section["rows"]
    controller.selectRecord("DS-EV3-REF")
    assert controller.compatibilityState == "NOT_A_CEA_TARGET"
    assert not controller.canCheckCompatibility and not controller.compatibilityChecked
    controller.checkCompatibility()                    # not offered: does nothing
    assert controller.compatibilityState == "NOT_A_CEA_TARGET"
    assert counters["total"]("probe") == 0 and counters["total"]("solve") == 0


def test_the_explicit_check_probes_and_does_not_solve(qt_app, corpus_root, counters):
    controller = PropulsionEvidenceController(root=corpus_root)
    controller.selectRecord(RP1311)
    controller.checkCompatibility()
    assert controller.compatibilityChecked
    assert counters["total"]("probe") > 0
    assert counters["total"]("solve") == 0, counters["solve"]
    if _STATUS.usable:
        assert controller.compatibilityState == "EXECUTABLE_VERIFIED"
        assert counters["probe"]["rocketforge.providers.cea_solid.library_species_available"] == 1
        assert "8e5df1cca92d4a48" in controller.compatibilityIdentity
        assert controller.compatibilityTone == "success"
    else:
        assert controller.compatibilityState == "PROVIDER_UNAVAILABLE"
        assert controller.compatibilityTone == "neutral"
        assert "unavailable" in controller.compatibilityIdentity
    assert not controller.canOpenInThermochemistry           # no Thermochemistry wired here
    rows = {r["label"] for r in controller.inspectionReadout["sections"][2]["rows"]}
    assert "Provider" in rows


def test_an_answer_belongs_to_the_record_it_was_asked_for(qt_app, corpus_root, fake_library):
    controller = PropulsionEvidenceController(root=corpus_root)
    controller.selectRecord("DS-EV3-SUM")
    controller.checkCompatibility()
    assert controller.compatibilityState == "UNDERDEFINED"
    assert controller.compatibilityBlockerCount == 1
    assert controller.compatibilityBlockers.rows()[0]["code"] == "MASS_FRACTION_SUM"
    controller.selectRecord("DS-EV3-A")                        # B shows its own state
    assert controller.compatibilityState == "NOT_CHECKED" and not controller.compatibilityChecked
    assert controller.compatibilityBlockerCount == 0 and controller.compatibilityBlockers.count() == 0
    assert controller.compatibilityIdentity == ""
    controller.selectRecord("DS-EV3-SUM")                      # nothing is cached either
    assert controller.compatibilityState == "NOT_CHECKED"
    controller.setFilterStatus("REGRESSION_LOCKED")            # a filter that moves the selection
    assert controller.selectedRecordId == RP1311 and controller.compatibilityState == "NOT_CHECKED"


def test_open_hands_the_published_case_to_thermochemistry_and_solves_nothing(
        qt_app, corpus_root, fake_library, counters):
    from rocketforge.application.analysis.thermochemistry_controller import (
        ThermochemistryController,
    )
    from rocketforge.application.analysis.thermochemistry_solid_service import default_solid_case

    thermo = ThermochemistryController()
    controller = PropulsionEvidenceController(root=corpus_root, thermochemistry=thermo)
    requested = []
    controller.workspaceRequested.connect(requested.append)
    controller.selectRecord(RP1311)
    record = service.load_corpus(corpus_root).record(RP1311)
    before = record_to_json(record)
    assert not controller.canOpenInThermochemistry                 # not before a check
    controller.openInThermochemistry()
    assert requested == [] and thermo.formulationKind == "bipropellant"

    controller.checkCompatibility()
    assert controller.compatibilityState == "EXECUTABLE_VERIFIED"
    assert controller.canOpenInThermochemistry and controller.openUnavailableReason == ""
    controller.openInThermochemistry()
    assert requested == ["thermochem"]
    assert thermo.formulationKind == "solid"
    case = thermo.solid_case()
    assert case == default_solid_case()                            # the published RP-1311 case
    assert case.reference_key == "rp1311-example5" and case.is_validated_operating_point
    assert not thermo.hasResult                                    # loaded, not solved
    assert counters["total"]("solve") == 0, counters["solve"]
    assert record_to_json(controller._corpus.record(RP1311)) == before


def test_open_is_unavailable_without_a_thermochemistry_workspace(qt_app, corpus_root, fake_library):
    controller = PropulsionEvidenceController(root=corpus_root)
    requested = []
    controller.workspaceRequested.connect(requested.append)
    controller.selectRecord(RP1311)
    controller.checkCompatibility()
    assert controller.compatibilityState == "EXECUTABLE_VERIFIED"
    assert not controller.canOpenInThermochemistry
    assert "No Thermochemistry workspace" in controller.openUnavailableReason
    controller.openInThermochemistry()
    assert requested == []


def test_a_source_complete_record_says_why_it_cannot_be_opened(qt_app, corpus_root, fake_library):
    thermo = FakeThermochemistry()
    controller = PropulsionEvidenceController(root=corpus_root, thermochemistry=thermo)
    controller.selectRecord("DS-EV3-A")
    controller.checkCompatibility()
    assert controller.compatibilityState == "EXECUTABLE_SOURCE_COMPLETE"
    assert not controller.canOpenInThermochemistry
    assert "no Thermochemistry case" in controller.openUnavailableReason
    controller.openInThermochemistry()
    assert thermo.loaded == [] and thermo.calculated == 0


def test_a_blocked_record_offers_no_open(qt_app, corpus_root, fake_library):
    thermo = FakeThermochemistry()
    controller = PropulsionEvidenceController(root=corpus_root, thermochemistry=thermo)
    controller.selectRecord("DS-EV3-SUM")
    controller.checkCompatibility()
    assert not controller.canOpenInThermochemistry and controller.openUnavailableReason == ""
    rows = controller.inspectionReadout["sections"][2]["rows"]
    assert any(r["label"] == "Mass fraction sum" for r in rows)


def test_browsing_never_loads_the_bridge_physics_or_a_provider():
    """Proved in a clean interpreter: constructing and browsing imports none of
    it; the explicit check is what loads the bridge (the positive control)."""
    code = (
        "import sys, os\n"
        "os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')\n"
        "from PySide6.QtGui import QGuiApplication\n"
        "app = QGuiApplication(sys.argv[:1])\n"
        "from rocketforge.application.analysis.propulsion_evidence_controller import "
        "PropulsionEvidenceController\n"
        "c = PropulsionEvidenceController()\n"
        "for rid in [r['recordId'] for r in c.library.rows()]:\n"
        "    c.selectRecord(rid); c.inspectionReadout; c.compatibilityState\n"
        "    c.canOpenInThermochemistry; c.inspectTableRow(0); c.inspectionReadout\n"
        "c.setFilterStatus('REGRESSION_LOCKED'); c.clearFilters()\n"
        "watch = lambda: sorted(m for m in sys.modules if m == 'cea' or m.startswith(("
        "'rocketforge.physics', 'rocketforge.providers', "
        "'rocketforge.application.analysis.evidence_cea_bridge', "
        "'rocketforge.application.analysis.thermochemistry_provider')))\n"
        "print(watch())\n"
        "c.checkCompatibility()\n"
        "print('rocketforge.application.analysis.evidence_cea_bridge' in watch())\n")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout.split()
    assert out[0] == "[]" and out[-1] == "True", out


# ======================================================================
# closure: once-per-process library probes, and the separate access gate
# ======================================================================


@pytest.fixture()
def stub_library(monkeypatch):
    """A usable provider whose thermo.lib identity and names the test states.

    Environment-independent: availability, the module and the provenance are
    stubs, and ``library_species_available`` records every name actually asked.
    """
    import types

    import rocketforge.providers.cea_solid as cea_solid

    state = {"sha": "a" * 64, "absent": {"KNO3(cr)"}, "asked": []}
    monkeypatch.setattr(gateway, "availability", lambda **_: gateway.ProviderAvailability(
        status="available", usable=True, version="stub", library_version="3.3.4"))
    monkeypatch.setattr(gateway, "_cea_module", lambda: object())
    monkeypatch.setattr(gateway, "provider_provenance", lambda: types.SimpleNamespace(
        database="thermo.lib", database_sha256=state["sha"]))

    def available(_module, names):
        names = tuple(names)
        state["asked"].append(names)
        return tuple(n for n in names if n not in state["absent"])
    monkeypatch.setattr(cea_solid, "library_species_available", available)
    return state


def test_library_names_are_probed_once_per_process_per_identity(stub_library):
    first = gateway.probe_solid_library_species(["NH4CLO4(I)", "KNO3(cr)"])
    assert first.probed == ("NH4CLO4(I)", "KNO3(cr)")
    assert first.present == ("NH4CLO4(I)",) and first.absent == ("KNO3(cr)",)
    again = gateway.probe_solid_library_species(["KNO3(cr)", "NH4CLO4(I)"])
    assert again.probed == ()                                  # answered, not re-asked
    assert again.present == ("NH4CLO4(I)",) and again.absent == ("KNO3(cr)",)
    assert again.database_sha256 == first.database_sha256
    more = gateway.probe_solid_library_species(["NH4CLO4(I)", "AL(cr)"])
    assert more.probed == ("AL(cr)",)                          # only the new name
    assert stub_library["asked"] == [("NH4CLO4(I)", "KNO3(cr)"), ("AL(cr)",)]


def test_another_thermo_lib_identity_is_probed_afresh(stub_library):
    gateway.probe_solid_library_species(["NH4CLO4(I)"])
    stub_library["sha"] = "b" * 64                             # a different database
    other = gateway.probe_solid_library_species(["NH4CLO4(I)"])
    assert other.probed == ("NH4CLO4(I)",) and other.database_sha256 == "b" * 64
    assert len(stub_library["asked"]) == 2


def test_resetting_the_provider_drops_the_probe_cache(stub_library):
    gateway.probe_solid_library_species(["NH4CLO4(I)"])
    gateway.reset_provider_state()
    assert gateway.probe_solid_library_species(["NH4CLO4(I)"]).probed == ("NH4CLO4(I)",)


def test_an_unavailable_provider_probes_nothing_and_caches_nothing(monkeypatch):
    monkeypatch.setattr(gateway, "availability", lambda **_: gateway.ProviderAvailability(
        status="not_installed", usable=False, detail="stub: not installed"))
    result = gateway.probe_solid_library_species(["NH4CLO4(I)"])
    assert not result.usable and result.probed == () and result.absent == ()
    assert gateway._species_probes == {}


def test_repeated_checks_reuse_names_but_never_an_assessment(qt_app, corpus_root, stub_library):
    controller = PropulsionEvidenceController(root=corpus_root)
    controller.selectRecord("DS-EV3-A")
    controller.checkCompatibility()
    first_state = controller.compatibilityState
    controller.checkCompatibility()                            # a second explicit check
    assert controller.compatibilityState == first_state == "EXECUTABLE_SOURCE_COMPLETE"
    assert stub_library["asked"] == [("NH4CLO4(I)",)]         # the name asked once
    controller.selectRecord("DS-EV3-SUM")                      # same name, other record
    assert controller.compatibilityState == "NOT_CHECKED"     # no answer carried over
    controller.checkCompatibility()
    assert controller.compatibilityState == "UNDERDEFINED"
    assert stub_library["asked"] == [("NH4CLO4(I)",)]


WITHHELD = Missing(MissingReason.WITHHELD_RIGHTS, "printed, not shippable")
META_RECORD = _record("DS-EV3-META", _propellant(
    (IngredientReference("Oxidiser A", WITHHELD, "NH4CLO4(I)"),
     IngredientReference("Binder X", WITHHELD, None, _binder(
         formula=WITHHELD, enthalpy=WITHHELD, reference_temperature=WITHHELD,
         molecular_weight=WITHHELD))), sid=META), sid=META)


def test_the_page_says_not_evaluated_for_a_withheld_record_and_probes_nothing(
        qt_app, tmp_path, counters):
    root = write_corpus(tmp_path / "evidence", (META_RECORD,))
    controller = PropulsionEvidenceController(root=root)
    controller.selectRecord("DS-EV3-META")
    assert controller.compatibilityState == "NOT_CHECKED"
    controller.checkCompatibility()
    assert controller.compatibilityState == "NOT_EVALUATED"
    assert controller.accessRestricted and controller.accessRestrictionCount > 0
    assert controller.compatibilityBlockerCount == 0         # no scientific blocker
    label, meaning = controller.compatibilityLabel, controller.compatibilityMeaning
    assert label == "Not evaluated · access restricted"
    for word in ("incompatible", "Blocked", "Underdefined", "unavailable", "absent"):
        assert word not in label and word not in meaning
    assert "not evaluated" in meaning and "says nothing about the chemistry" in meaning
    assert controller.compatibilityTone == "neutral" and not controller.canOpenInThermochemistry
    rows = controller.inspectionReadout["sections"][2]["rows"]
    assert any(r["label"] == "Access" for r in rows)
    assert not any(r["label"].startswith("Withheld") for r in rows)
    assert counters["total"]("probe") == 0 and counters["total"]("solve") == 0
    controller.selectRecord(RP1311)                            # the gate's answer stays put
    assert controller.compatibilityState == "NOT_CHECKED" and not controller.accessRestricted
