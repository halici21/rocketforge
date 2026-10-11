"""The Qt facade for the Reference Engines workspace (QML singleton ``ReferenceEngines``, DB-3A).

Read-only. The shipped reference-engine corpus is loaded and admitted once, when
the controller is built; after that every slot here changes only what is on
screen: which configuration, which filter, which graph, what the inspector
reads. Nothing is edited, saved, promoted or solved. At module level this
imports the catalog, the pure projection in :mod:`.reference_engine_view` and
two presentation models; no physics, provider, comparison or solver module.

Everything a view shows is prepared by :mod:`.reference_engine_view`, so QML
never parses evidence, interprets a capability, or places a topology node.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from rocketforge.evidence import EvidenceError

from ..rowmodel import RowListModel
from . import reference_engine_view as view
from .reference_engine_catalog import ReferenceEngineCatalog, load_reference_engines
from .thermochemistry_table_model import ThermoTableModel

__all__ = ["ReferenceEngineController"]

#: Inspector subjects. "" is the selected configuration itself.
_KINDS = ("", "assertion", "source", "capability", "graph", "node", "edge")


class ReferenceEngineController(QObject):
    """Backs the Reference Engines page."""

    filtersChanged = Signal()
    selectionChanged = Signal()
    graphChanged = Signal()
    inspectionChanged = Signal()

    def __init__(self, parent: QObject | None = None, *, path=None) -> None:
        super().__init__(parent)
        self._load_error = ""
        try:
            self._catalog: ReferenceEngineCatalog | None = load_reference_engines(path)
        except (EvidenceError, OSError, ValueError) as error:
            # Refused, not skipped: a corpus that does not admit is a defect the
            # page states, never an empty library that looks like "no engines".
            self._catalog = None
            self._load_error = str(error)
        self._options = view.filter_options(self._catalog) if self._catalog else \
            {"capability": [], "status": [], "cycle": []}
        self._filter = view.EngineFilter()
        self._visible: tuple = ()
        self._selected = ""
        self._views: list[dict] = []
        self._graph_index = -1
        self._kind = ""
        self._key = ""
        self._table_keys: list[str] = []
        self._connection_keys: list[tuple[str, str]] = []
        self._identity: dict = {}

        self._library = RowListModel(("configurationId", "title", "subtitle", "section", "sectionStart",
                                      "capabilities"), self)
        self._capabilities = RowListModel(("capability", "name", "status", "statusLabel", "glyph",
                                           "summary", "more", "meaning"), self)
        self._facts = RowListModel(("assertionId", "group", "groupTitle", "groupNote", "groupStart", "field",
                                    "valueText", ("unitText", "unit"), "kind", "nominal", "conditions", "hasConditions",
                                    "point", "hasPoint", ("statusText", "status"), "sourceId", "recorded", "unitNote"), self)
        self._missing = RowListModel(("quantity", "reason"), self)
        self._context = RowListModel(("assertionId", "level", "field", "valueText", ("unitText", "unit"), "kind", "nominal",
                                      "conditions", "hasConditions", "sourceId"), self)
        self._sources = RowListModel(("sourceId", ("sourceTitle", "title"), "line", "authority", "shipping"), self)
        self._points = RowListModel(("pointId", "pointLabel", "pointNotes"), self)
        self._nodes = RowListModel(("nodeId", ("nodeLabel", "label"), ("nodeType", "type"), "ownership",
                                    "ownershipWord", "engineOwned", "inferred", ("nx", "x"), ("ny", "y"),
                                    ("nw", "w"), ("nh", "h")), self)
        self._edges = RowListModel(("edgeId", "source", "target", ("edgeKind", "kind"), "kindWord", "carrier",
                                    "role", "inferred", "fromLabel", "toLabel", "path", "x3", "y3",
                                    "mx", "my", "ax", "ay", "bx", "by"), self)
        self._omissions = RowListModel((("omissionText", "text"),), self)
        self._graph_choices = RowListModel((("choiceLabel", "label"),), self)
        self._table = ThermoTableModel(self)
        self._connections = ThermoTableModel(self)
        self._apply_filter()

    # ------------------------------------------------------------ corpus

    @Property(str, constant=True)
    def loadError(self) -> str:
        return self._load_error

    @Property(int, constant=True)
    def configurationCount(self) -> int:
        return len(self._catalog.entries()) if self._catalog else 0

    @Property(int, notify=filtersChanged)
    def visibleCount(self) -> int:
        return len(self._visible)

    @Property(str, notify=filtersChanged)
    def emptyState(self) -> str:
        """``""`` when a configuration is shown; else why the library is empty."""
        if self._load_error:
            return "load-error"
        if not self._catalog or not self._catalog.entries():
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
        """Choices the shipped corpus supports: {capability, status, cycle}."""
        return self._options

    @Property(str, notify=filtersChanged)
    def filterSearch(self) -> str:
        return self._filter.search

    @Property(str, notify=filtersChanged)
    def filterCapability(self) -> str:
        return self._filter.capability

    @Property(str, notify=filtersChanged)
    def filterStatus(self) -> str:
        return self._filter.status

    @Property(str, notify=filtersChanged)
    def filterCycle(self) -> str:
        return self._filter.cycle

    @Property(bool, notify=filtersChanged)
    def hasActiveFilter(self) -> bool:
        return self._filter.active

    @Property(str, notify=filtersChanged)
    def filterSummary(self) -> str:
        if not self._catalog:
            return "The reference-engine corpus could not be loaded"
        return view.filter_summary(self._catalog, self._filter, len(self._visible))

    def _offered(self, kind: str, key: str) -> bool:
        return not key or any(option["key"] == key for option in self._options[kind])

    def _set_filter(self, **changes) -> None:
        current = dict(search=self._filter.search, capability=self._filter.capability,
                       status=self._filter.status, cycle=self._filter.cycle)
        current.update(changes)
        new = view.EngineFilter(**current)
        if new != self._filter:
            self._filter = new
            self._apply_filter()

    @Slot(str)
    def setSearch(self, text: str) -> None:
        self._set_filter(search=str(text)[:120])

    # A capability narrows only together with a status: the pair is the filter,
    # so the controls can never say "Topology" while filtering nothing.
    @Slot(str)
    def setFilterCapability(self, key: str) -> None:
        if self._offered("capability", key):
            self._set_filter(capability=key, status=self._filter.status if key else "")

    @Slot(str)
    def setFilterStatus(self, key: str) -> None:
        if self._offered("status", key):
            self._set_filter(status=key)

    @Slot(str)
    def setFilterCycle(self, key: str) -> None:
        if self._offered("cycle", key):
            self._set_filter(cycle=key)

    @Slot()
    def clearFilters(self) -> None:
        self._set_filter(search="", capability="", status="", cycle="")

    def _apply_filter(self) -> None:
        self._visible = view.visible_entries(self._catalog, self._filter) if self._catalog else ()
        rows = view.library_rows(self._catalog, self._visible) if self._catalog else []
        self._library.set_rows(rows)
        self.filtersChanged.emit()
        ids = [row["configurationId"] for row in rows]
        if self._selected not in ids:
            self._select(ids[0] if ids else "")

    # ---------------------------------------------------------- selection

    @Property(str, notify=selectionChanged)
    def selectedConfigurationId(self) -> str:
        return self._selected

    @Slot(str)
    def selectConfiguration(self, cfg: str) -> None:
        if cfg in [e.configuration_id for e in self._visible]:
            self._select(cfg)

    def _select(self, cfg: str) -> None:
        if cfg == self._selected and cfg:
            return
        self._selected = cfg
        c = self._catalog
        if not cfg or c is None:
            self._identity = {}
            for model in (self._capabilities, self._facts, self._missing, self._context, self._sources,
                          self._points):
                model.set_rows([])
            self._table_keys, self._connection_keys, self._views = [], [], []
            self._table.set_table(view.TABLE_COLUMNS, [])
            self._connections.set_table(view.CONNECTION_COLUMNS, [])
        else:
            self._identity = view.identity(c, cfg)
            self._capabilities.set_rows(view.capability_rows(c, cfg))
            facts = []
            for group in view.fact_groups(c, cfg):
                for i, row in enumerate(group["rows"]):
                    facts.append(dict(row, group=group["key"], groupTitle=group["title"],
                                      groupNote=group["note"], groupStart=i == 0))
            self._facts.set_rows(facts)
            self._missing.set_rows(view.missing_rows(c, cfg))
            self._context.set_rows(view.context_rows(c, cfg))
            self._sources.set_rows(view.source_rows(c, cfg))
            self._points.set_rows(self._identity["operatingPoints"])
            self._table_keys, rows = view.assertion_table(c, cfg)
            self._table.set_table(view.TABLE_COLUMNS, rows)
            self._connection_keys, rows = view.connection_table(c, cfg)
            self._connections.set_table(view.CONNECTION_COLUMNS, rows)
            self._views = view.graph_views(c, cfg)
        self._graph_choices.set_rows([{"label": g["label"]} for g in self._views])
        self._kind, self._key = "", ""
        self._set_graph(0 if self._views else -1)
        self.selectionChanged.emit()
        self.inspectionChanged.emit()

    def _id(self, key: str, default=""):
        return self._identity.get(key, default)

    @Property(str, notify=selectionChanged)
    def recordTitle(self) -> str:
        return self._id("label")

    @Property(str, notify=selectionChanged)
    def lineage(self) -> str:
        return self._id("lineage")

    @Property(str, notify=selectionChanged)
    def effective(self) -> str:
        return self._id("effective")

    @Property(bool, notify=selectionChanged)
    def effectiveKnown(self) -> bool:
        return bool(self._id("effectiveKnown", False))

    @Property(str, notify=selectionChanged)
    def aliases(self) -> str:
        return self._id("aliases")

    @Property(str, notify=selectionChanged)
    def recordNotes(self) -> str:
        return self._id("notes")

    @Property(QObject, constant=True)
    def capabilities(self) -> QObject:
        return self._capabilities

    @Property(QObject, constant=True)
    def facts(self) -> QObject:
        return self._facts

    @Property(QObject, constant=True)
    def missing(self) -> QObject:
        return self._missing

    @Property(QObject, constant=True)
    def context(self) -> QObject:
        return self._context

    @Property(QObject, constant=True)
    def sources(self) -> QObject:
        return self._sources

    @Property(QObject, constant=True)
    def operatingPoints(self) -> QObject:
        return self._points

    @Property(int, notify=selectionChanged)
    def factCount(self) -> int:
        return self._facts.count()

    @Property(int, notify=selectionChanged)
    def missingCount(self) -> int:
        return self._missing.count()

    @Property(int, notify=selectionChanged)
    def contextCount(self) -> int:
        return self._context.count()

    @Property(int, notify=selectionChanged)
    def pointCount(self) -> int:
        return self._points.count()

    # ----------------------------------------------------------- topology

    @Property(int, notify=selectionChanged)
    def graphCount(self) -> int:
        return len(self._views)

    @Property(QObject, constant=True)
    def graphChoices(self) -> QObject:
        return self._graph_choices

    @Property(int, notify=graphChanged)
    def graphIndex(self) -> int:
        return self._graph_index

    @Slot(int)
    def selectGraph(self, index: int) -> None:
        if 0 <= index < len(self._views) and index != self._graph_index:
            self._set_graph(index)
            if self._kind in ("graph", "node", "edge"):
                self._kind, self._key = "", ""
                self.inspectionChanged.emit()

    def _set_graph(self, index: int) -> None:
        self._graph_index = index
        g = self._graph()
        self._nodes.set_rows(g["nodes"] if g else [])
        self._edges.set_rows(g["edges"] if g else [])
        self._omissions.set_rows([{"text": o} for o in g["omissions"]] if g else [])
        self.graphChanged.emit()

    def _graph(self) -> dict | None:
        return self._views[self._graph_index] if 0 <= self._graph_index < len(self._views) else None

    def _g(self, key: str, default=""):
        g = self._graph()
        return g[key] if g else default

    @Property(str, notify=graphChanged)
    def graphId(self) -> str:
        return self._g("topologyId")

    @Property(str, notify=graphChanged)
    def graphTitle(self) -> str:
        return self._g("label")

    @Property(str, notify=graphChanged)
    def graphScope(self) -> str:
        return self._g("scope")

    @Property(bool, notify=graphChanged)
    def graphIsUnit(self) -> bool:
        return bool(self._g("unitGraph", False))

    @Property(bool, notify=graphChanged)
    def graphReconstruction(self) -> bool:
        return bool(self._g("reconstruction", False))

    @Property(str, notify=graphChanged)
    def graphProvenance(self) -> str:
        return self._g("provenanceText")

    @Property(str, notify=graphChanged)
    def graphDrawnBy(self) -> str:
        return self._g("drawnBy")

    @Property(bool, notify=graphChanged)
    def graphComplete(self) -> bool:
        return bool(self._g("declaredComplete", False))

    @Property(str, notify=graphChanged)
    def graphCompleteness(self) -> str:
        return self._g("completenessText")

    @Property(str, notify=graphChanged)
    def graphKinds(self) -> str:
        return " · ".join(self._g("kinds", []))

    @Property(bool, notify=graphChanged)
    def graphHasNonEngine(self) -> bool:
        return bool(self._g("hasNonEngine", False))

    @Property(float, notify=graphChanged)
    def graphWidth(self) -> float:
        return float(self._g("width", 0.0))

    @Property(float, notify=graphChanged)
    def graphHeight(self) -> float:
        return float(self._g("height", 0.0))

    @Property(QObject, constant=True)
    def graphNodes(self) -> QObject:
        return self._nodes

    @Property(QObject, constant=True)
    def graphEdges(self) -> QObject:
        return self._edges

    @Property(QObject, constant=True)
    def graphOmissions(self) -> QObject:
        return self._omissions

    # -------------------------------------------------------------- tables

    @Property(QObject, constant=True)
    def tableModel(self) -> QObject:
        return self._table

    @Property("QVariantList", constant=True)
    def tableColumns(self) -> list:
        return [dict(column) for column in view.TABLE_COLUMNS]

    @Property(int, notify=selectionChanged)
    def tableRowCount(self) -> int:
        return len(self._table_keys)

    @Property(int, notify=inspectionChanged)
    def selectedTableRow(self) -> int:
        if self._kind != "assertion":
            return -1
        return self._table_keys.index(self._key) if self._key in self._table_keys else -1

    @Property(QObject, constant=True)
    def connectionModel(self) -> QObject:
        return self._connections

    @Property("QVariantList", constant=True)
    def connectionColumns(self) -> list:
        return [dict(column) for column in view.CONNECTION_COLUMNS]

    @Property(int, notify=selectionChanged)
    def connectionRowCount(self) -> int:
        return len(self._connection_keys)

    @Property(int, notify=inspectionChanged)
    def selectedConnectionRow(self) -> int:
        if self._kind != "edge":
            return -1
        key = (self.graphId, self._key)
        return self._connection_keys.index(key) if key in self._connection_keys else -1

    # ---------------------------------------------------------- inspection

    @Property(str, notify=inspectionChanged)
    def inspectionKind(self) -> str:
        """``""`` for the configuration itself, else assertion/source/capability/graph/node/edge."""
        return self._kind

    @Property(str, notify=inspectionChanged)
    def inspectionKey(self) -> str:
        return self._key

    @Property(str, notify=inspectionChanged)
    def selectedNodeId(self) -> str:
        return self._key if self._kind == "node" else ""

    @Property(str, notify=inspectionChanged)
    def selectedEdgeId(self) -> str:
        return self._key if self._kind == "edge" else ""

    @Property("QVariantMap", notify=inspectionChanged)
    def inspectionReadout(self):
        c, cfg = self._catalog, self._selected
        if c is None or not cfg:
            return {}
        kind, key = self._kind, self._key
        if kind == "assertion":
            return view.assertion_readout(c, cfg, key)
        if kind == "source":
            return view.source_readout(c, key)
        if kind == "capability":
            return view.capability_readout(c, cfg, key)
        if kind == "graph":
            return view.graph_readout(c, cfg, self.graphId)
        if kind == "node":
            return view.node_readout(c, cfg, self.graphId, key)
        if kind == "edge":
            return view.edge_readout(c, cfg, self.graphId, key)
        return view.configuration_readout(c, cfg)

    def _inspect(self, kind: str, key: str) -> None:
        if (kind, key) != (self._kind, self._key):
            self._kind, self._key = kind, key
            self.inspectionChanged.emit()

    @Slot()
    def inspectRecord(self) -> None:
        self._inspect("", "")

    @Slot(str)
    def inspectAssertion(self, assertion_id: str) -> None:
        c, cfg = self._catalog, self._selected
        if c and cfg and assertion_id in {a.assertion_id for a in
                                          (*c.assertions(cfg), *view.context_assertions(c, cfg))}:
            self._inspect("assertion", assertion_id)

    @Slot(str)
    def inspectSource(self, source_id: str) -> None:
        c, cfg = self._catalog, self._selected
        if not (c and cfg):
            return
        cited = {s.reference.source_id for s in c.sources(cfg)}
        cited |= {a.source_id for a in view.unit_assertions(c, cfg)}
        if source_id in cited:
            self._inspect("source", source_id)

    @Slot(str)
    def inspectCapability(self, key: str) -> None:
        if self._selected and key in {cap.value for cap in view.CAPABILITY_ORDER}:
            self._inspect("capability", key)

    @Slot()
    def inspectGraph(self) -> None:
        if self._graph():
            self._inspect("graph", self.graphId)

    @Slot(str)
    def inspectNode(self, node_id: str) -> None:
        g = self._graph()
        if g and node_id in {n["nodeId"] for n in g["nodes"]}:
            self._inspect("node", node_id)

    @Slot(str)
    def inspectEdge(self, edge_id: str) -> None:
        g = self._graph()
        if g and edge_id in {e["edgeId"] for e in g["edges"]}:
            self._inspect("edge", edge_id)

    @Slot(int)
    def inspectTableRow(self, row: int) -> None:
        if 0 <= row < len(self._table_keys):
            self.inspectAssertion(self._table_keys[row])

    @Slot(int)
    def inspectConnectionRow(self, row: int) -> None:
        if not 0 <= row < len(self._connection_keys):
            return
        graph_id, edge_id = self._connection_keys[row]
        index = next(i for i, g in enumerate(self._views) if g["topologyId"] == graph_id)
        if index != self._graph_index:
            self._set_graph(index)
        self._kind, self._key = "", ""
        self.inspectEdge(edge_id)
