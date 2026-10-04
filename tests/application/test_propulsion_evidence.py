"""The Propulsion Database, read-only: service and controller.

The shipped corpus (today one record, DS-RP1311-E5) is a regression fixture;
every other state -- missing values, withheld rights, a restricted or licensed
source, rights under review, a record with no formulation, an empty corpus, a
malformed file -- is built here, in a temporary folder, from the EV-1 types and
their canonical serialisation. None of it is shipped: only
``rocketforge/data/evidence`` is, and the last tests below prove these fixtures
are not in it.
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

from rocketforge.application.analysis import propulsion_evidence_service as service
from rocketforge.application.analysis.propulsion_evidence_controller import (
    PropulsionEvidenceController,
)
from rocketforge.evidence import (
    AccessClass,
    CustomDefinition,
    Dimension,
    EvidenceError,
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
    reported_values,
    sources_to_json,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHIPPED = ROOT / "rocketforge" / "data" / "evidence"


# --------------------------------------------------------------- test corpora

def _source(sid, shipping, access=AccessClass.PUBLIC_OPEN):
    return SourceReference(
        source_id=sid, organization="Test Org", authors=("A. Author",), title=f"Title of {sid}",
        year=None, identifiers={"report_number": f"R-{sid}"}, locator=f"https://example.invalid/{sid}",
        source_type="report", access_class=access, rights_statement="as stated by the test",
        shipping=shipping, tier=2)


def _value(v, unit, sid, locator="p. 3, Table 2"):
    return ReportedValue(v, unit, sid, locator, ValueStatus.REPORTED)


def _caps(va=EvidenceStatus.REFERENCE_ONLY, vb=EvidenceStatus.NOT_APPLICABLE,
          vc=EvidenceStatus.NOT_APPLICABLE, vd=EvidenceStatus.NOT_APPLICABLE):
    return {Dimension.VA: va, Dimension.VB: vb, Dimension.VC: vc, Dimension.VD: vd}


def _propellant(sid, fractions, **kw):
    ingredients = tuple(IngredientReference(name, frac) for name, frac in fractions)
    base = dict(propellant_id="P-" + sid, source_ids=(sid,), family="test family",
                source_name="test blend", exact_formulation=all(
                    isinstance(f, ReportedValue) for _, f in fractions),
                basis="mass_fraction", ingredients=ingredients,
                density=Missing(MissingReason.NOT_REPORTED, "density not stated"),
                initial_temperature=Missing(MissingReason.UNKNOWN))
    base.update(kw)
    return PropellantReference(**base)


def _record(rid, sid, *, kind=RecordKind.PROPELLANT, propellant=None, caps=None,
            blockers=(), notes=""):
    return EvidenceRecord(
        record_id=rid, title=f"Record {rid}", kind=kind, source_ids=(sid,),
        capabilities=caps or _caps(), capability_notes={Dimension.VA: "note for VA"},
        propellant=propellant, comparison_case_ids=(), executable_key=None,
        blockers=tuple(blockers), notes=notes)


def write_corpus(folder: pathlib.Path, sources, records) -> pathlib.Path:
    (folder / "records").mkdir(parents=True, exist_ok=True)
    (folder / "sources.json").write_text(sources_to_json(sources), encoding="utf-8")
    for record in records:
        (folder / "records" / f"{record.record_id}.json").write_text(
            record_to_json(record), encoding="utf-8")
    return folder


@pytest.fixture()
def mixed(tmp_path):
    """Every shipping state and a gap of every kind, test-only."""
    sources = [
        _source("S-OPEN", ShippingPolicy.VALUES_WITH_ATTRIBUTION),
        _source("S-META", ShippingPolicy.METADATA_ONLY, AccessClass.PAYWALLED),
        _source("S-RESTR", ShippingPolicy.RESTRICTED_REFERENCE, AccessClass.ACCOUNT_RESTRICTED),
        _source("S-LIC", ShippingPolicy.LICENSED_PROVIDER, AccessClass.COMMERCIAL_PRODUCT),
        _source("S-REVIEW", ShippingPolicy.RIGHTS_REVIEW_REQUIRED),
    ]
    withheld = Missing(MissingReason.WITHHELD_RIGHTS, "printed, not shippable")
    records = [
        _record("DS-A-OPEN", "S-OPEN", propellant=_propellant("S-OPEN", [
            ("Oxidiser X", _value(0.7, "mass fraction", "S-OPEN")),
            ("Binder Y", Missing(MissingReason.NOT_REPORTED, "lumped in the source")),
        ], exact_formulation=False), caps=_caps(EvidenceStatus.SOURCE_COMPLETE_CANDIDATE,
                                                 vb=EvidenceStatus.UNDERDEFINED)),
        _record("DS-B-META", "S-META", propellant=_propellant("S-META", [
            ("Oxidiser X", withheld), ("Binder Y", withheld)]),
            caps=_caps(EvidenceStatus.REFERENCE_ONLY), blockers=("values withheld",)),
        _record("DS-C-RESTR", "S-RESTR", kind=RecordKind.REFERENCE,
                caps=_caps(EvidenceStatus.ACCESS_BLOCKED)),
        _record("DS-D-LIC", "S-LIC", kind=RecordKind.REFERENCE, caps=_caps(EvidenceStatus.REFERENCE_ONLY)),
        _record("DS-E-REVIEW", "S-REVIEW", kind=RecordKind.REFERENCE,
                caps=_caps(EvidenceStatus.VALIDATION_CANDIDATE)),
    ]
    return write_corpus(tmp_path / "evidence", sources, records)


@pytest.fixture()
def controller(qt_app, mixed):
    return PropulsionEvidenceController(root=mixed)


# ------------------------------------------------------------------ service

def test_the_shipped_corpus_loads_through_the_ev1_loader():
    corpus = service.load_corpus()
    assert service.evidence_root() == SHIPPED
    ids = [r.record_id for r in corpus.records]
    assert "DS-RP1311-E5" in ids and ids == sorted(ids)
    for record in corpus.records:
        for sid in record.source_ids:
            assert sid in corpus.sources


def test_a_frozen_build_finds_the_evidence_beside_the_reference_tables(monkeypatch, tmp_path):
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path), raising=False)
    assert service.evidence_root() == tmp_path / "rocketforge" / "data" / "evidence"


def test_a_malformed_or_misnamed_file_is_refused_not_skipped(tmp_path, mixed):
    (mixed / "records" / "DS-A-OPEN.json").rename(mixed / "records" / "DS-Z.json")
    with pytest.raises(EvidenceError, match="named by its record_id"):
        service.load_corpus(mixed)
    (mixed / "records" / "DS-Z.json").write_text("{", encoding="utf-8")
    with pytest.raises(EvidenceError):
        service.load_corpus(mixed)
    with pytest.raises(EvidenceError, match="source registry"):
        service.load_corpus(tmp_path / "nowhere")


def test_an_empty_records_folder_is_an_empty_corpus(tmp_path):
    folder = write_corpus(tmp_path / "e", [_source("S-OPEN", ShippingPolicy.VALUES_WITH_ATTRIBUTION)], [])
    assert service.load_corpus(folder).records == ()


def test_a_value_from_a_metadata_only_source_cannot_even_load(tmp_path):
    bad = _record("DS-X", "S-META", propellant=_propellant("S-META", [
        ("Oxidiser X", _value(0.7, "mass fraction", "S-META"))]))
    folder = write_corpus(tmp_path / "x", [_source("S-META", ShippingPolicy.METADATA_ONLY)], [bad])
    with pytest.raises(EvidenceError, match="METADATA_ONLY"):
        service.load_corpus(folder)


def test_filters_read_fields_and_never_rank(mixed):
    corpus = service.load_corpus(mixed)
    by = lambda **kw: [r.record_id for r in service.filter_records(corpus, service.RecordFilter(**kw))]
    assert by() == [r.record_id for r in corpus.records]
    assert by(status=EvidenceStatus.UNDERDEFINED) == ["DS-A-OPEN"]
    assert by(status=EvidenceStatus.UNDERDEFINED, dimension=Dimension.VA) == []
    assert by(dimension=Dimension.VB) == by()           # a dimension alone scopes nothing
    assert by(shipping=ShippingPolicy.LICENSED_PROVIDER) == ["DS-D-LIC"]
    options = service.filter_options(corpus)
    assert [o["key"] for o in options["dimension"]] == ["VA", "VB", "VC", "VD"]
    assert "VERIFIED_NUMERICAL_REFERENCE" not in [o["key"] for o in options["status"]]
    assert [o["key"] for o in options["shipping"]] == [p.value for p in ShippingPolicy]


def test_stored_values_are_shown_exactly_as_stored():
    record = service.load_corpus().record("DS-RP1311-E5")
    keys, rows = service.table_rows(record)
    stored = {r.value for r in reported_values(record)}
    for key, row in zip(keys, rows):
        entry = next(e for e in service.datum_entries(record) if e.key == key)
        if isinstance(entry.datum, ReportedValue):
            assert float(row[1]) == entry.datum.value and float(row[1]) in stored
            assert row[1] == repr(entry.datum.value)        # no display rounding
            assert (row[2], row[3], row[4], row[5]) == (
                entry.datum.unit, entry.datum.status.value, entry.datum.source_id, entry.datum.locator)
        else:
            assert row[1] == "Missing" and row[3] == entry.datum.reason.value
    assert "14.6652984484" in [row[1] for row in rows]
    assert ("Density", "Missing", "", "NOT_REPORTED", "", "") in rows


def test_the_rp1311_record_reads_as_its_evidence_says():
    record = service.load_corpus().record("DS-RP1311-E5")
    caps = {row["dimension"]: row for row in service.capability_rows(record)}
    assert caps["VA"]["status"] == "REGRESSION_LOCKED" and caps["VA"]["applicable"]
    for d in ("VB", "VC", "VD"):
        assert caps[d]["status"] == "NOT_APPLICABLE" and not caps[d]["applicable"]
        assert caps[d]["tone"] == "none"                 # not a failure, not a warning
    comp = service.composition_rows(record)
    assert [r["name"] for r in comp] == ["NH4CLO4(I)", "CHOS-Binder", "AL(cr)", "MgO(cr)", "H2O(L)"]
    assert [r["share"] for r in comp] == [0.7206, 0.1858, 0.09, 0.002, 0.0016]
    binder = comp[1]
    assert binder["definition"] and "HTPB" not in json.dumps(comp) and "PBAN" not in json.dumps(comp)
    assert service.missing_rows(record) == [{"key": "density", "field": "Density",
                                             "reason": "NOT_REPORTED",
                                             "note": record.propellant.density.note}]
    assert service.rights_rows(record, service.load_corpus().sources) == []


def test_capabilities_stay_four_independent_cells():
    for record in service.load_corpus().records:
        rows = service.capability_rows(record)
        assert [r["dimension"] for r in rows] == ["VA", "VB", "VC", "VD"]
        assert {r["tone"] for r in rows} <= {"neutral", "warning", "none"}
        for row in rows:
            assert row["status"] == record.capabilities[Dimension(row["dimension"])].value


def test_withheld_restricted_licensed_and_review_states_ship_no_values(mixed):
    corpus = service.load_corpus(mixed)
    meta = corpus.record("DS-B-META")
    assert service.table_rows(meta)[1] and all(row[1] == "Missing" for row in service.table_rows(meta)[1])
    assert all(r["missing"] and r["share"] == -1.0 for r in service.composition_rows(meta))
    assert "METADATA_ONLY" in service.payload_note(meta, corpus.sources)
    for rid, policy, word in (("DS-C-RESTR", "RESTRICTED_REFERENCE", "restricted"),
                              ("DS-D-LIC", "LICENSED_PROVIDER", "not bundled"),
                              ("DS-E-REVIEW", "RIGHTS_REVIEW_REQUIRED", "not yet reviewed")):
        record = corpus.record(rid)
        assert service.table_rows(record) == ([], [])
        note = service.payload_note(record, corpus.sources)
        assert policy in note and word in note
        rights = service.rights_rows(record, corpus.sources)
        assert [r["policy"] for r in rights] == [policy]
    licensed = service.payload_note(corpus.record("DS-D-LIC"), corpus.sources)
    assert "installed" not in licensed.replace("no installation", "")


def test_underdefined_and_access_blocked_are_cautions_not_errors(mixed):
    corpus = service.load_corpus(mixed)
    vb = service.capability_rows(corpus.record("DS-A-OPEN"))[1]
    assert vb["status"] == "UNDERDEFINED" and vb["tone"] == "warning"
    va = service.capability_rows(corpus.record("DS-C-RESTR"))[0]
    assert va["status"] == "ACCESS_BLOCKED" and va["tone"] == "warning"


def test_a_missing_field_keeps_its_reason_in_every_view(mixed):
    corpus = service.load_corpus(mixed)
    record = corpus.record("DS-A-OPEN")
    binder = service.composition_rows(record)[1]
    assert binder["valueText"] == "Missing · NOT_REPORTED" and binder["share"] == -1.0
    readout = service.datum_readout(record, corpus.sources, "ingredients[1].fraction")
    rows = {r["label"]: r["value"] for r in readout["sections"][0]["rows"]}
    assert rows["Missing reason"] == "NOT_REPORTED" and rows["Note"] == "lumped in the source"
    assert "0" not in rows["Value"]


def test_a_datum_readout_carries_value_unit_status_locator_and_source():
    corpus = service.load_corpus()
    record = corpus.record("DS-RP1311-E5")
    readout = service.datum_readout(record, corpus.sources, "ingredients[1].custom.enthalpy")
    value = {r["label"]: r["value"] for r in readout["sections"][0]["rows"]}
    datum = record.propellant.ingredients[1].custom.enthalpy
    assert value["Stored value"] == repr(datum.value) and value["Unit (as printed)"] == datum.unit
    assert value["Value status"] == "REPORTED" and value["Locator"] == datum.locator
    assert readout["sections"][1]["title"] == datum.source_id
    record_view = service.record_readout(record, corpus.sources)
    flat = json.dumps(record_view)
    assert "rp1311-example5" in flat and "browsing never assesses or runs it" in flat
    for sid in record.source_ids:
        assert corpus.sources[sid].locator in flat


def test_the_service_never_mutates_a_record():
    corpus = service.load_corpus()
    record = corpus.record("DS-RP1311-E5")
    before = record_to_json(record)
    for key in [e.key for e in service.datum_entries(record)]:
        service.datum_readout(record, corpus.sources, key)
    service.table_rows(record); service.composition_rows(record); service.record_readout(record, corpus.sources)
    assert record_to_json(record) == before


def _imports(node) -> list[str]:
    """Absolute module names imported under ``node``, ``from . import x`` resolved to ``x``."""
    imported = []
    for item in ast.walk(node):
        if isinstance(item, ast.Import):
            imported += [a.name for a in item.names]
        elif isinstance(item, ast.ImportFrom):
            base = item.module or ""
            if item.level:
                package = ("rocketforge.application.analysis" if item.level == 1
                           else "rocketforge.application")
                base = f"{package}.{base}" if base else package
                if not item.module:
                    imported += [f"{base}.{a.name}" for a in item.names]
                    continue
            imported.append(base)
    return imported


def test_the_service_and_controller_import_no_solver_path():
    """Browsing cannot solve if the code that browses cannot reach a solver.

    EV-3 adds one door, and only inside the two explicit-action slots: the
    controller imports the CEA compatibility bridge in ``checkCompatibility()``,
    never at module level, so building the controller and browsing never load it.
    """
    forbidden = ("rocketforge.physics", "rocketforge.engineering", "rocketforge.engine",
                 "rocketforge.providers", "rocketforge.comparison", "cea", "CoolProp",
                 "rocketforge.application.analysis.thermochemistry_provider")
    bridge = "rocketforge.application.analysis.evidence_cea_bridge"
    allowed_siblings = {"rocketforge.application.analysis.propulsion_evidence_service",
                        "rocketforge.application.data_paths",
                        "rocketforge.application.analysis.thermochemistry_table_model",
                        "rocketforge.application.rowmodel"}
    folder = ROOT / "rocketforge" / "application" / "analysis"
    for name in ("propulsion_evidence_service.py", "propulsion_evidence_controller.py"):
        tree = ast.parse((folder / name).read_text(encoding="utf-8"))
        imported = _imports(tree)
        bad = [m for m in imported if m.startswith(forbidden)]
        assert not bad, (name, bad)
        top_level = [m for stmt in tree.body if isinstance(stmt, (ast.Import, ast.ImportFrom))
                     for m in _imports(stmt)]
        siblings = {m for m in top_level if m.startswith("rocketforge.application")}
        assert siblings <= allowed_siblings, (name, siblings)
        lazy = {m for m in imported if m.startswith("rocketforge.application")} - siblings
        if name == "propulsion_evidence_service.py":
            assert lazy == set(), (name, lazy)
            continue
        assert lazy == {bridge}, (name, lazy)
        # ... and only the explicit check reaches for it
        owners = [f.name for f in ast.walk(tree) if isinstance(f, ast.FunctionDef)
                  and bridge in _imports(f)]
        assert owners == ["checkCompatibility"], owners


# --------------------------------------------------------------- controller

def test_the_controller_selects_the_first_record_and_lists_all(controller):
    assert controller.recordCount == 5 and controller.visibleCount == 5
    assert controller.selectedRecordId == controller.library.rows()[0]["recordId"]
    sections = [r["section"] for r in controller.library.rows()]
    assert sections == ["Propellants", "Propellants", "References", "References", "References"]
    assert [r["sectionStart"] for r in controller.library.rows()] == [True, False, True, False, False]
    assert controller.emptyState == ""


def test_selection_updates_every_surface(controller):
    controller.selectRecord("DS-B-META")
    assert controller.recordTitle == "Record DS-B-META"
    assert [r["status"] for r in controller.capabilities.rows()] == [
        "REFERENCE_ONLY", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE"]
    # both withheld fractions, and the density and initial temperature the source omits
    assert controller.missingCount == 4 and controller.blockerCount == 1 and controller.rightsCount == 1
    assert controller.tableRowCount == controller.tableModel.rowCount() == 4
    assert controller.inspectionKey == "" and controller.inspectionReadout["kind"] == "record"
    controller.selectRecord("DS-NOT-THERE")                  # ignored, not a stale id
    assert controller.selectedRecordId == "DS-B-META"


def test_a_filter_that_hides_the_selection_selects_the_first_visible_record(controller):
    controller.selectRecord("DS-B-META")
    controller.setFilterShipping("LICENSED_PROVIDER")
    assert controller.visibleCount == 1 and controller.selectedRecordId == "DS-D-LIC"
    assert "1 of 5 records" in controller.filterSummary and controller.hasActiveFilter
    controller.clearFilters()
    assert controller.visibleCount == 5 and controller.selectedRecordId == "DS-D-LIC"


def test_a_filter_that_matches_nothing_says_so_and_selects_nothing(controller):
    controller.setFilterStatus("UNDERDEFINED")
    controller.setFilterDimension("VA")
    assert controller.visibleCount == 0 and controller.emptyState == "no-match"
    assert controller.selectedRecordId == "" and controller.tableRowCount == 0
    assert controller.inspectionReadout == {}
    controller.clearFilters()
    assert controller.emptyState == "" and controller.selectedRecordId


def test_a_status_the_corpus_does_not_hold_is_not_a_filter(controller):
    controller.setFilterStatus("VERIFIED_NUMERICAL_REFERENCE")
    assert controller.filterStatus == "" and not controller.hasActiveFilter


def test_inspection_follows_table_rows_and_resets_with_the_record(qt_app):
    controller = PropulsionEvidenceController()
    controller.selectRecord("DS-RP1311-E5")
    controller.inspectTableRow(8)
    assert controller.inspectionKey == "ingredients[1].custom.molecular_weight"
    assert controller.selectedTableRow == 8
    assert controller.inspectionReadout["title"] == "CHOS-Binder · molecular weight"
    controller.inspectDatum("density")
    rows = controller.inspectionReadout["sections"][0]["rows"]
    assert {"label": "Missing reason", "value": "NOT_REPORTED"} in rows
    controller.inspectDatum("no.such.field")                 # ignored
    assert controller.inspectionKey == "density"
    controller.inspectRecord()
    assert controller.inspectionKey == "" and controller.selectedTableRow == -1


def test_an_empty_corpus_is_stated_not_filled(qt_app, tmp_path):
    folder = write_corpus(tmp_path / "e", [_source("S-OPEN", ShippingPolicy.VALUES_WITH_ATTRIBUTION)], [])
    controller = PropulsionEvidenceController(root=folder)
    assert controller.recordCount == 0 and controller.emptyState == "no-records"
    assert controller.library.count() == 0 and controller.selectedRecordId == ""


def test_a_corpus_that_will_not_load_is_stated_word_for_word(qt_app, mixed):
    (mixed / "records" / "DS-A-OPEN.json").write_text('{"schema_version": 3}', encoding="utf-8")
    controller = PropulsionEvidenceController(root=mixed)
    assert controller.emptyState == "load-error" and "schema_version 3" in controller.loadError
    assert controller.recordCount == 0


# ---------------------------------------------------------- shipping scope

def test_no_test_fixture_record_is_shipped():
    shipped = sorted(p.stem for p in (SHIPPED / "records").glob("*.json"))
    assert not [s for s in shipped if s.startswith(("DS-A-", "DS-B-", "DS-C-", "DS-D-", "DS-E-", "DS-TEST"))]
    sources = json.loads((SHIPPED / "sources.json").read_text(encoding="utf-8"))["sources"]
    assert not [s for s in sources if s["source_id"].startswith(("S-TEST", "S-OPEN", "S-META"))]
