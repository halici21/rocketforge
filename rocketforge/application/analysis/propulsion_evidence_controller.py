"""The Qt facade for the Propulsion Database workspace (QML singleton ``PropulsionEvidence``).

Read-only. The corpus is loaded once, when the controller is built; after that
every browsing slot here changes only what is on screen -- which record, which
filter, which field the inspector reads. Nothing is computed from a record and
nothing is solved: at module level the controller imports the evidence service
and two presentation models, and no physics, provider, comparison or solver
module.

Two slots act, and only when a person asks (EV-3, R1 integration blueprint
section 4):

* :meth:`checkCompatibility` -- PROBE ONLY. Asks the installed NASA CEA
  library, through :mod:`.evidence_cea_bridge` and the provider gateway,
  whether the selected record's formulation can be posed to it. The bridge is
  imported inside the slot, so browsing never even loads it. Solves nothing.
* :meth:`openInThermochemistry` -- NO SOLVE. For an executable record whose
  formulation equals a Thermochemistry case field for field, hands that case
  to the existing Thermochemistry controller (solid mode, the case loaded) and
  asks the shell to show that workspace. The solve stays there, under its own
  Calculate.

Everything a view shows is prepared by :mod:`propulsion_evidence_service` (and,
after a check, by the bridge) from the EV-1 records, so QML never parses
evidence, interprets a status or decides what a shipping policy allows.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from rocketforge.evidence import (
    Dimension,
    EvidenceError,
    EvidenceStatus,
    ShippingPolicy,
)

from ..rowmodel import RowListModel
from . import propulsion_evidence_service as service
from .thermochemistry_table_model import ThermoTableModel

__all__ = ["PropulsionEvidenceController"]


class PropulsionEvidenceController(QObject):
    """Backs the Propulsion Database page."""

    filtersChanged = Signal()
    selectionChanged = Signal()
    inspectionChanged = Signal()
    compatibilityChanged = Signal()
    #: A workspace the shell should show, by Navigation key ("thermochem"),
    #: emitted only after openInThermochemistry() has handed its case over.
    workspaceRequested = Signal(str)

    def __init__(self, parent: QObject | None = None, *, root=None,
                 thermochemistry=None) -> None:
        super().__init__(parent)
        #: The Thermochemistry workspace's controller, duck-typed: the one
        #: place "Open in Thermochemistry" hands a case to. None when this
        #: session has none, and then Open is unavailable, with the reason.
        self._thermochemistry = thermochemistry
        # The explicit compatibility answer for the selected record, or None
        # when nobody has asked. Never cached across records.
        self._compat = None
        self._compat_identity = ""
        self._open_message = ""
        self._load_error = ""
        try:
            self._corpus = service.load_corpus(root)
        except EvidenceError as error:
            # Refused, not skipped: a malformed shipped file is a defect the
            # page states, not one it papers over with an empty library.
            self._corpus = service.EvidenceCorpus(sources={}, records=())
            self._load_error = str(error)
        self._options = service.filter_options(self._corpus)
        self._filter = service.RecordFilter()
        self._visible: tuple = ()
        self._selected_id = ""
        self._inspection_key = ""
        self._table_keys: list[str] = []

        self._library = RowListModel(("recordId", "title", "section", "sectionStart",
                                      "capabilities"), self)
        self._capabilities = RowListModel(("dimension", "dimensionName", "statusLabel",
                                           "tone", "applicable",
                                           ("capabilityNote", "note")), self)
        self._composition = RowListModel((("datumKey", "key"), "name", "definition",
                                          "valueText", "unit", "valueStatus", "missing",
                                          "share"), self)
        self._missing = RowListModel((("datumKey", "key"), "field", "reason",
                                      ("missingNote", "note")), self)
        self._rights = RowListModel(("sourceId", "policy", "meaning"), self)
        # "blockerText", not "text": a delegate cannot redeclare Text.text.
        self._blockers = RowListModel((("blockerText", "text"),), self)
        self._compat_blockers = RowListModel((
            ("blockerCode", "code"), ("blockerCategory", "category"),
            ("blockerField", "field"), ("blockerIngredient", "ingredient"),
            ("blockerName", "name"), ("blockerText", "text")), self)
        # The access gate's restrictions: a separate list, never scientific blockers.
        self._access_rows = RowListModel((
            ("restrictionCode", "code"), ("restrictionField", "field"),
            ("restrictionIngredient", "ingredient"), ("restrictionText", "text")), self)
        self._table = ThermoTableModel(self)
        self._apply_filter()

    # ------------------------------------------------------------ corpus

    @Property(str, constant=True)
    def loadError(self) -> str:
        """The loader's refusal, word for word, when the shipped corpus is malformed."""
        return self._load_error

    @Property(int, constant=True)
    def recordCount(self) -> int:
        return len(self._corpus.records)

    @Property(int, notify=filtersChanged)
    def visibleCount(self) -> int:
        return len(self._visible)

    @Property(str, notify=filtersChanged)
    def emptyState(self) -> str:
        """``""`` when a record is shown; else why the library is empty."""
        if self._load_error:
            return "load-error"
        if not self._corpus.records:
            return "no-records"
        if not self._visible:
            return "no-match"
        return ""

    @Property(QObject, constant=True)
    def library(self) -> QObject:
        return self._library

    # ------------------------------------------------------------ filters

    @Property("QVariantMap", constant=True)
    def filterOptions(self):
        """Choices derived from the shipped records: {dimension, status, shipping}."""
        return self._options

    @Property(str, notify=filtersChanged)
    def filterDimension(self) -> str:
        return "" if self._filter.dimension is None else self._filter.dimension.value

    @Property(str, notify=filtersChanged)
    def filterStatus(self) -> str:
        return "" if self._filter.status is None else self._filter.status.value

    @Property(str, notify=filtersChanged)
    def filterShipping(self) -> str:
        return "" if self._filter.shipping is None else self._filter.shipping.value

    @Property(bool, notify=filtersChanged)
    def hasActiveFilter(self) -> bool:
        return self._filter.active

    @Property(str, notify=filtersChanged)
    def filterSummary(self) -> str:
        """The drawer handle's one line: what is shown, out of what."""
        if self._load_error:
            return "Evidence could not be loaded"
        text = f"{len(self._visible)} of {len(self._corpus.records)} records"
        if self._filter.status is not None:
            scope = self._filter.dimension.value if self._filter.dimension else "any dimension"
            text += f"  ·  {service.status_label(self._filter.status)} in {scope}"
        if self._filter.shipping is not None:
            text += f"  ·  {self._filter.shipping.value}"
        return text

    def _set_filter(self, **changes) -> None:
        current = {"dimension": self._filter.dimension, "status": self._filter.status,
                   "shipping": self._filter.shipping}
        current.update(changes)
        new = service.RecordFilter(**current)
        if new == self._filter:
            return
        self._filter = new
        self._apply_filter()

    @Slot(str)
    def setFilterDimension(self, key: str) -> None:
        self._set_filter(dimension=Dimension(key) if key else None)

    def _offered(self, kind: str, key: str) -> bool:
        return any(option["key"] == key for option in self._options[kind])

    # Only what the filter offers: a status or policy no shipped record holds
    # is not a choice, so the controls and the filter can never disagree.
    @Slot(str)
    def setFilterStatus(self, key: str) -> None:
        if key and not self._offered("status", key):
            return
        self._set_filter(status=EvidenceStatus(key) if key else None)

    @Slot(str)
    def setFilterShipping(self, key: str) -> None:
        if key and not self._offered("shipping", key):
            return
        self._set_filter(shipping=ShippingPolicy(key) if key else None)

    @Slot()
    def clearFilters(self) -> None:
        self._set_filter(dimension=None, status=None, shipping=None)

    def _apply_filter(self) -> None:
        self._visible = service.filter_records(self._corpus, self._filter)
        rows = service.library_rows(self._visible)
        self._library.set_rows(rows)
        self.filtersChanged.emit()
        # A selection the filter hides is not kept invisibly: the first visible
        # record takes its place, or nothing when nothing is visible.
        visible_ids = [row["recordId"] for row in rows]
        if self._selected_id not in visible_ids:
            self._select(visible_ids[0] if visible_ids else "")

    # ---------------------------------------------------------- selection

    def _record(self):
        return self._corpus.record(self._selected_id) if self._selected_id else None

    @Property(str, notify=selectionChanged)
    def selectedRecordId(self) -> str:
        return self._selected_id

    @Slot(str)
    def selectRecord(self, record_id: str) -> None:
        if record_id in [r.record_id for r in self._visible]:
            self._select(record_id)

    def _select(self, record_id: str) -> None:
        if record_id == self._selected_id and record_id:
            return
        self._selected_id = record_id
        record = self._record()
        sources = self._corpus.sources
        if record is None:
            for model in (self._capabilities, self._composition, self._missing,
                          self._rights, self._blockers):
                model.set_rows([])
            self._table_keys = []
            self._table.set_table(service.TABLE_COLUMNS, [])
        else:
            self._capabilities.set_rows(service.capability_rows(record))
            self._composition.set_rows(service.composition_rows(record))
            self._missing.set_rows(service.missing_rows(record))
            self._rights.set_rows(service.rights_rows(record, sources))
            self._blockers.set_rows([{"text": text} for text in record.blockers])
            self._table_keys, rows = service.table_rows(record)
            self._table.set_table(service.TABLE_COLUMNS, rows)
        self._inspection_key = ""
        # An answer belongs to the record it was asked for: a new selection
        # starts from "not checked", never from the previous record's result.
        self._compat = None
        self._compat_identity = ""
        self._open_message = ""
        self._compat_blockers.set_rows([])
        self._access_rows.set_rows([])
        self.selectionChanged.emit()
        self.inspectionChanged.emit()
        self.compatibilityChanged.emit()

    @Property(str, notify=selectionChanged)
    def recordTitle(self) -> str:
        record = self._record()
        return record.title if record else ""

    @Property(str, notify=selectionChanged)
    def recordKind(self) -> str:
        record = self._record()
        return record.kind.value if record else ""

    @Property(bool, notify=selectionChanged)
    def hasPropellant(self) -> bool:
        record = self._record()
        return bool(record and record.propellant is not None)

    @Property(str, notify=selectionChanged)
    def formulationLine(self) -> str:
        """What the source calls the propellant, and its family, as stored."""
        record = self._record()
        if record is None or record.propellant is None:
            return ""
        p = record.propellant
        basis = "mass fraction" if p.basis == "mass_fraction" else p.basis
        exact = "exact formulation" if p.exact_formulation else "not an exact formulation"
        return f"{p.source_name}  ·  {p.family}  ·  {basis}, {exact}"

    @Property(str, notify=selectionChanged)
    def sourceLine(self) -> str:
        """The record's sources, by id and title."""
        record = self._record()
        if record is None:
            return ""
        parts = []
        for sid in record.source_ids:
            source = self._corpus.sources.get(sid)
            parts.append(f"{sid}  ·  {source.title}" if source else sid)
        return "\n".join(parts)

    @Property(str, notify=selectionChanged)
    def recordNotes(self) -> str:
        record = self._record()
        return record.notes if record else ""

    @Property(str, notify=selectionChanged)
    def payloadNote(self) -> str:
        record = self._record()
        return service.payload_note(record, self._corpus.sources) if record else ""

    @Property(QObject, constant=True)
    def capabilities(self) -> QObject:
        return self._capabilities

    @Property(QObject, constant=True)
    def composition(self) -> QObject:
        return self._composition

    @Property(QObject, constant=True)
    def missing(self) -> QObject:
        return self._missing

    @Property(QObject, constant=True)
    def rights(self) -> QObject:
        return self._rights

    @Property(QObject, constant=True)
    def blockers(self) -> QObject:
        return self._blockers

    @Property(int, notify=selectionChanged)
    def missingCount(self) -> int:
        return self._missing.count()

    @Property(int, notify=selectionChanged)
    def blockerCount(self) -> int:
        return self._blockers.count()

    @Property(int, notify=selectionChanged)
    def rightsCount(self) -> int:
        """Cited sources whose shipping policy withholds values."""
        return self._rights.count()

    # -------------------------------------------------------------- table

    @Property(QObject, constant=True)
    def tableModel(self) -> QObject:
        return self._table

    @Property("QVariantList", constant=True)
    def tableColumns(self) -> list:
        return [dict(column) for column in service.TABLE_COLUMNS]

    @Property(int, notify=selectionChanged)
    def tableRowCount(self) -> int:
        return len(self._table_keys)

    @Property(int, notify=inspectionChanged)
    def selectedTableRow(self) -> int:
        try:
            return self._table_keys.index(self._inspection_key)
        except ValueError:
            return -1

    # --------------------------------------------------------- inspection

    @Property(str, notify=inspectionChanged)
    def inspectionKey(self) -> str:
        """``""`` for the record itself, else the path of the field inspected."""
        return self._inspection_key

    @Property("QVariantMap", notify=inspectionChanged)
    def inspectionReadout(self):
        record = self._record()
        if record is None:
            return {}
        if not self._inspection_key:
            readout = service.record_readout(record, self._corpus.sources)
            # R1 section 7: the record inspector carries the CEA assessment and
            # its blockers -- after the record's identity and formulation,
            # before its sources.
            at = 2 if record.propellant is not None else 1
            readout["sections"].insert(at, self._compatibility_section())
            return readout
        return service.datum_readout(record, self._corpus.sources, self._inspection_key)

    @Slot()
    def inspectRecord(self) -> None:
        if self._inspection_key:
            self._inspection_key = ""
            self.inspectionChanged.emit()

    @Slot(str)
    def inspectDatum(self, key: str) -> None:
        record = self._record()
        if record is None or key == self._inspection_key:
            return
        if key not in [e.key for e in service.datum_entries(record)]:
            return
        self._inspection_key = key
        self.inspectionChanged.emit()

    @Slot(int)
    def inspectTableRow(self, row: int) -> None:
        if 0 <= row < len(self._table_keys):
            self.inspectDatum(self._table_keys[row])


    # ------------------------------------------------- CEA compatibility (EV-3)
    #
    # Nothing below runs on selection, filtering, inspection, theme or resize.
    # A record the evidence itself puts outside CEA's scope (no formulation, or
    # VA not applicable) says so from the record alone and offers no check;
    # every other record starts "not checked" until checkCompatibility().

    def _selected_compat(self):
        record = self._record()
        if self._compat is None or record is None or self._compat.record_id != record.record_id:
            return None
        return self._compat

    @Property(str, notify=compatibilityChanged)
    def compatibilityState(self) -> str:
        """NOT_CHECKED, NOT_A_CEA_TARGET or the checked R1 state; "" with no record."""
        record = self._record()
        if record is None:
            return ""
        compat = self._selected_compat()
        if compat is not None:
            # None: the access gate stopped the check before any assessment.
            return compat.state.value if compat.state is not None else service.NOT_EVALUATED
        return service.NOT_CHECKED if service.is_cea_target(record) else service.NOT_A_CEA_TARGET

    @Property(bool, notify=compatibilityChanged)
    def compatibilityChecked(self) -> bool:
        """Whether the state shown is the answer to an explicit check of this record."""
        return self._selected_compat() is not None

    @Property(bool, notify=compatibilityChanged)
    def canCheckCompatibility(self) -> bool:
        """A check is offered only for a record the evidence makes a CEA target."""
        record = self._record()
        return record is not None and service.is_cea_target(record)

    @Property(str, notify=compatibilityChanged)
    def compatibilityLabel(self) -> str:
        state = self.compatibilityState
        return service.compatibility_label(state) if state else ""

    @Property(str, notify=compatibilityChanged)
    def compatibilityTone(self) -> str:
        """The status dot only; the label carries the state."""
        state = self.compatibilityState
        return service.compatibility_tone(state) if state else "none"

    @Property(str, notify=compatibilityChanged)
    def compatibilityMeaning(self) -> str:
        state = self.compatibilityState
        return service.compatibility_meaning(state) if state else ""

    @Property(str, notify=compatibilityChanged)
    def compatibilityIdentity(self) -> str:
        """The provider, library version and thermo.lib hash actually probed; "" if none."""
        return self._compat_identity if self._selected_compat() is not None else ""

    @Property("QVariantList", notify=compatibilityChanged)
    def compatibilityNotes(self) -> list:
        compat = self._selected_compat()
        return list(compat.notes) if compat is not None else []

    @Property(QObject, constant=True)
    def compatibilityBlockers(self) -> QObject:
        return self._compat_blockers

    @Property(bool, notify=compatibilityChanged)
    def accessRestricted(self) -> bool:
        """The explicit check stopped at the access gate (compatibility not evaluated)."""
        compat = self._selected_compat()
        return compat is not None and compat.access is not None and not compat.access.permitted

    @Property(QObject, constant=True)
    def accessRestrictions(self) -> QObject:
        return self._access_rows

    @Property(int, notify=compatibilityChanged)
    def accessRestrictionCount(self) -> int:
        return self._access_rows.count() if self._selected_compat() is not None else 0

    @Property(int, notify=compatibilityChanged)
    def compatibilityBlockerCount(self) -> int:
        return self._compat_blockers.count() if self._selected_compat() is not None else 0

    @Property(bool, notify=compatibilityChanged)
    def canOpenInThermochemistry(self) -> bool:
        """Only after a check found the record executable and equal to a
        Thermochemistry case, and only with a Thermochemistry workspace to open."""
        compat = self._selected_compat()
        return (compat is not None and compat.executable
                and compat.thermochemistry_key is not None
                and self._thermochemistry is not None)

    @Property(str, notify=compatibilityChanged)
    def openUnavailableReason(self) -> str:
        """Why an executable record cannot be opened here; "" otherwise."""
        compat = self._selected_compat()
        if compat is None or not compat.executable:
            return ""
        if self._open_message:
            return self._open_message
        if compat.thermochemistry_key is None:
            return compat.thermochemistry_note
        if self._thermochemistry is None:
            return ("No Thermochemistry workspace is connected to the Propulsion Database "
                    "in this session, so nothing can be opened from here.")
        return ""

    def _compatibility_section(self) -> dict:
        state = self.compatibilityState
        compat = self._selected_compat()
        if compat is None:
            return service.compatibility_section(state)
        open_note = ""
        if compat.executable:
            open_note = self.openUnavailableReason or (
                f"Can be opened as the Thermochemistry case {compat.thermochemistry_key!r}. "
                "It is loaded there, not solved.")
        return service.compatibility_section(
            state, blockers=self._compat_blockers.rows(), identity=self._compat_identity,
            notes=compat.notes, open_note=open_note, restrictions=self._access_rows.rows())

    @Slot()
    def checkCompatibility(self) -> None:
        """PROBE ONLY. The explicit check of the selected record; solves nothing.

        Probes the installed library names through the provider gateway (and
        with that, constructs the provider if this process has not yet). Builds
        a formulation only when nothing blocks it. The record is not changed.
        """
        record = self._record()
        if record is None or not service.is_cea_target(record):
            return
        from . import evidence_cea_bridge as bridge

        compat = bridge.assess(record, self._corpus.sources)
        self._compat = compat
        self._compat_identity = bridge.identity_text(compat.probe)
        self._open_message = ""
        self._compat_blockers.set_rows(bridge.blocker_rows(compat))
        self._access_rows.set_rows(bridge.access_rows(compat))
        self.compatibilityChanged.emit()
        self.inspectionChanged.emit()

    @Slot()
    def openInThermochemistry(self) -> None:
        """NO SOLVE. Hands the verified case to Thermochemistry and asks to show it.

        Sets the workspace to solid mode and loads the catalogue case the
        evidence was verified equal to -- the provider constant stays the
        executable authority -- then emits ``workspaceRequested("thermochem")``.
        Calculate, in that workspace, is the only thing that solves it.
        """
        if not self.canOpenInThermochemistry:
            return
        compat = self._selected_compat()
        key = compat.thermochemistry_key
        thermochemistry = self._thermochemistry
        thermochemistry.formulationKind = "solid"
        thermochemistry.loadSolidFormulation(key)
        case_of = getattr(thermochemistry, "solid_case", None)
        if callable(case_of):
            case = case_of()
            if (getattr(case, "reference_key", None) != key
                    or not getattr(case, "is_published_composition", False)):
                self._open_message = (f"Thermochemistry did not take the case {key!r}; "
                                      "nothing was opened.")
                self.compatibilityChanged.emit()
                self.inspectionChanged.emit()
                return
        self.workspaceRequested.emit("thermochem")
