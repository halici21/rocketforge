"""The Qt facade for the Rocket Performance workspace.

The only file in this feature that imports Qt. It holds no equation, no
physical constant and no provider import: every number it publishes was
computed by :mod:`performance_service` from
``rocketforge.engineering.nozzle``, and every string it publishes was written
there too.

Three behaviours are worth reading the code for, because they are the ones a
reasonable implementation gets wrong:

**Changing a nozzle input never re-solves chemistry.** ``calculate`` calls
``solve_performance``, which takes the chamber state as an argument. There is
no provider call anywhere on that path, and no cache that could quietly miss.

**A result is never relabelled.** The header is built from the ``case`` and the
``ChamberOutcome`` the result carries, not from the live input fields. Editing
an input marks the result stale; it does not restate it under new conditions.

**Upstream change invalidates rather than recomputes.** When the
Thermochemistry workspace produces a different chamber state, the performance
result on screen is marked as belonging to a superseded chamber and left
alone. Silently recomputing it would change numbers the user is reading
without being asked; silently keeping it unmarked would attach them to a
chamber that no longer exists.
"""

from __future__ import annotations

import math
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from rocketforge.application.formatting import EM_DASH, format_engineering
from rocketforge.application.rowmodel import RowListModel
from rocketforge.engineering.chamber import ChamberGammaBasis
from rocketforge.engineering.nozzle import PerformanceScale, PerformanceScaleMode
from rocketforge.physics.thermochemistry import GammaStrategy

from . import performance_oracle as oracle
from . import performance_service as service

__all__ = ["RocketPerformanceController"]

#: Decimal places for the readout. Six significant figures is the application
#: default and matches every other analysis page.
DEFAULT_PRECISION = 6

#: How the identity panel describes a residual it considers clean.
IDENTITY_SUMMARY_OK = ("Every internal identity closes to machine precision. "
                       "This checks that the numbers above are consistent with "
                       "each other; it is not a check against reality.")


def _text(value: float | None, precision: int) -> str:
    return format_engineering(value, precision)


def _rounded(value: float | None, precision: int) -> str:
    """The readout rail's formatter. Formatting only -- no arithmetic."""
    return format_engineering(value, precision)


class RocketPerformanceController(QObject):
    """Application-side facade for the Rocket Performance analysis workspace."""

    inputsChanged = Signal()
    chamberChanged = Signal()
    resultChanged = Signal()
    oracleChanged = Signal()
    requestTab = Signal(int)

    def __init__(self, chamber_source: Any = None,
                 parent: QObject | None = None) -> None:
        """Take the upstream chamber workspace, or nothing.

        ``chamber_source`` is duck-typed: anything with a ``chamber_outcome()``
        method, and optionally a ``resultChanged`` signal to connect to. That
        is enough for the real controller and for a test double, and it keeps
        this class from importing the Thermochemistry controller -- two
        singletons that import each other are a circular import waiting for
        the next feature.
        """
        QObject.__init__(self, parent)

        self._source = chamber_source
        self._case = service.DEFAULT_PERFORMANCE_CASE
        self._precision = DEFAULT_PRECISION
        self._busy = False

        self._outcome = service.EMPTY_OUTCOME
        self._stale = False

        self._oracle = oracle.EMPTY_ORACLE
        self._oracle_mode = "equilibrium"
        self._oracle_busy = False
        self._oracle_chamber: Any = None

        # Rows are published through stable models, never as QVariantList
        # properties a binding re-reads. Handing QML a converted QVariantList
        # on every publication retains memory that neither garbage collector
        # reclaims -- 0.46 MB per recalculation on this page, linear and
        # unbounded. See
        # docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md.
        #
        # The QVariantList properties below still exist and are still correct;
        # they are read by tests and by the smoke tours. What changed is that
        # the interface no longer binds them.
        self._models = {
            "chamber": RowListModel(("label", "value", "unit")),
            # prefixed roles: the delegate IS a PerfMetricReadout, which
            # already owns symbol/value/unit/label/primary
            "headline": RowListModel((("rowKey", "key"),
                                      ("rowSymbol", "symbol"),
                                      ("rowValue", "value"),
                                      ("rowUnit", "unit"),
                                      ("rowLabel", "label"),
                                      ("rowPrimary", "primary"))),
            "cfTerms": RowListModel(("label", "value", "sign")),
            "thrustTerms": RowListModel(("label", "symbol", "value", "sign")),
            "exitState": RowListModel(("symbol", "label", "value", "unit")),
            "trace": RowListModel(("label", "value")),
            # the Model and Provider-comparison tabs. They live in the same
            # stack, so their bindings re-evaluate on every publication whether
            # or not their tab is on screen -- which made them just as
            # expensive as the visible ones.
            "reduction": RowListModel(("label", "value")),
            "identity": RowListModel(("name", "passed", "residual", "scaled",
                                      "tolerance")),
            "provenance": RowListModel(("computed_by", "detail", "model",
                                        "role")),
            "oracle": RowListModel(("label", "value", "unit")),
            "oracleComparison": RowListModel(("label", "rocketforge",
                                              "provider", "difference",
                                              "kind", "reference")),
        }
        # Refresh from the controller's own signals rather than from each
        # place a result is set, so a future code path that publishes a result
        # cannot forget to update the views.
        self.resultChanged.connect(self._refresh_result_models)
        self.resultChanged.connect(self._refresh_oracle_models)
        self.chamberChanged.connect(self._refresh_chamber_model)
        self.oracleChanged.connect(self._refresh_oracle_models)

        signal = getattr(chamber_source, "resultChanged", None)
        if signal is not None:
            signal.connect(self._on_chamber_changed)

    # ==================================================================
    # the upstream chamber
    # ==================================================================

    def _chamber(self):
        """The current chamber outcome, or None when there is no source."""
        if self._source is None:
            return None
        return self._source.chamber_outcome()

    def _accepted_chamber(self):
        """The chamber outcome only if it actually carries a state."""
        chamber = self._chamber()
        return chamber if chamber is not None and chamber.state is not None else None

    def _on_chamber_changed(self) -> None:
        """The upstream workspace produced, or cleared, a chamber state.

        Nothing is recomputed. The existing result keeps its own chamber and
        is reported as superseded, and the oracle panel -- which was run for a
        particular case -- is marked the same way.
        """
        self.chamberChanged.emit()
        self.resultChanged.emit()
        self.oracleChanged.emit()

    @Property(bool, notify=chamberChanged)
    def hasChamber(self) -> bool:
        """Whether an accepted chamber state is available to start from."""
        return self._accepted_chamber() is not None

    @Property(str, notify=chamberChanged)
    def chamberHeadline(self) -> str:
        """The upstream case, as the Thermochemistry workspace states it."""
        chamber = self._accepted_chamber()
        if chamber is None:
            return ""
        from .thermochemistry_service import case_headline

        return case_headline(chamber.case)

    # -- stable row models -------------------------------------------------
    #
    # QML binds these. The QVariantList properties they mirror stay for Python
    # callers -- tests, smoke tours, the parity snapshot -- where a read costs
    # nothing. See QML_MEMORY_ROOT_CAUSE.md for why the interface must not bind
    # the lists directly.

    def _refresh_result_models(self) -> None:
        self._models["headline"].set_rows(self.headlineMetrics)
        self._models["cfTerms"].set_rows(self.thrustCoefficientBreakdown)
        self._models["thrustTerms"].set_rows(self.thrustBreakdown)
        self._models["exitState"].set_rows(self.exitStateRows)
        self._models["trace"].set_rows(self.traceRows)
        self._models["reduction"].set_rows(self.reductionRows)
        self._models["identity"].set_rows(self.identityRows)
        self._models["provenance"].set_rows(self.provenanceRows)

    def _refresh_oracle_models(self) -> None:
        self._models["oracle"].set_rows(self.oracleRows)
        self._models["oracleComparison"].set_rows(self.oracleComparisonRows)

    def _refresh_chamber_model(self) -> None:
        self._models["chamber"].set_rows(self.chamberRows)

    @Property(QObject, constant=True)
    def chamberModel(self) -> QObject:
        return self._models["chamber"]

    @Property(QObject, constant=True)
    def headlineModel(self) -> QObject:
        return self._models["headline"]

    @Property(QObject, constant=True)
    def cfTermsModel(self) -> QObject:
        return self._models["cfTerms"]

    @Property(QObject, constant=True)
    def thrustTermsModel(self) -> QObject:
        return self._models["thrustTerms"]

    @Property(QObject, constant=True)
    def exitStateModel(self) -> QObject:
        return self._models["exitState"]

    @Property(QObject, constant=True)
    def traceModel(self) -> QObject:
        return self._models["trace"]

    @Property(QObject, constant=True)
    def reductionModel(self) -> QObject:
        return self._models["reduction"]

    @Property(QObject, constant=True)
    def identityModel(self) -> QObject:
        return self._models["identity"]

    @Property(QObject, constant=True)
    def provenanceModel(self) -> QObject:
        return self._models["provenance"]

    @Property(QObject, constant=True)
    def oracleModel(self) -> QObject:
        return self._models["oracle"]

    @Property(QObject, constant=True)
    def oracleComparisonModel(self) -> QObject:
        return self._models["oracleComparison"]

    # Counts, so a view can hide an empty section without binding the list.
    @Property(int, notify=resultChanged)
    def cfTermsCount(self) -> int:
        return len(self.thrustCoefficientBreakdown)

    @Property(int, notify=resultChanged)
    def thrustTermsCount(self) -> int:
        return len(self.thrustBreakdown)

    @Property("QVariantList", notify=chamberChanged)
    def chamberRows(self):
        """The chamber state this workspace would start from.

        Shown on the performance page rather than only on the chemistry page:
        a reader deciding whether an Isp is plausible needs the chamber
        temperature and the two gammas in front of them, and sending them to
        another tab to find out is how the wrong gamma gets used.
        """
        chamber = self._accepted_chamber()
        if chamber is None:
            return []
        state = chamber.state
        precision = self._precision
        rows = [
            {"label": "Chamber temperature  T_0", "unit": "K",
             "value": _text(state.temperature, precision)},
            {"label": "Specific gas constant  R", "unit": "J/(kg K)",
             "value": _text(state.gas_constant, precision)},
            {"label": "Mean molar mass  M", "unit": "kg/mol",
             "value": _text(state.molar_mass, precision)},
            {"label": "Equilibrium isentropic exponent  gamma_s", "unit": "",
             "value": _text(state.gamma_equilibrium, precision)},
            {"label": "Frozen exponent  cp/cv", "unit": "",
             "value": _text(state.gamma_frozen, precision)},
        ]
        return rows

    @Property(str, notify=chamberChanged)
    def chamberMissingMessage(self) -> str:
        """Why the workspace has nothing to compute, in the user's terms."""
        if self.hasChamber:
            return ""
        chamber = self._chamber()
        if chamber is None or chamber.kind == "empty":
            return ("No chamber equilibrium has been solved yet. Ideal rocket "
                    "performance starts from one: the chamber temperature, "
                    "the gas constant and gamma all come from it, and nothing "
                    "here is estimated in its place.")
        return (f"The Thermochemistry workspace has no accepted chamber state "
                f"({chamber.status_label}). Solve one there first — the "
                f"performance model refuses rather than substituting a "
                f"plausible gas.")

    # ==================================================================
    # inputs
    # ==================================================================

    @Property("QVariantList", constant=True)
    def gammaStrategyOptions(self):
        return [dict(option) for option in service.GAMMA_STRATEGY_OPTIONS]

    @Property("QVariantList", constant=True)
    def gammaBasisOptions(self):
        return [dict(option) for option in service.GAMMA_BASIS_OPTIONS]

    @Property("QVariantList", constant=True)
    def ambientOptions(self):
        return [dict(option) for option in service.AMBIENT_OPTIONS]

    @Property("QVariantList", constant=True)
    def scaleOptions(self):
        return [dict(option) for option in service.SCALE_OPTIONS]

    @Property(str, notify=inputsChanged)
    def gammaStrategy(self) -> str:
        return self._case.gamma_strategy.value

    @gammaStrategy.setter
    def gammaStrategy(self, value: str) -> None:
        try:
            strategy = GammaStrategy(str(value))
        except ValueError:
            return
        if strategy is self._case.gamma_strategy:
            return
        self._case = self._case.replace(gamma_strategy=strategy)
        self._on_input_changed()

    @Property(str, notify=inputsChanged)
    def gammaBasis(self) -> str:
        return self._case.gamma_basis.value

    @gammaBasis.setter
    def gammaBasis(self, value: str) -> None:
        try:
            basis = ChamberGammaBasis(str(value))
        except ValueError:
            return
        if basis is self._case.gamma_basis:
            return
        self._case = self._case.replace(gamma_basis=basis)
        self._on_input_changed()

    @Property(str, notify=inputsChanged)
    def gammaBasisNote(self) -> str:
        """What the selected basis means. Written in the service, not here."""
        for option in service.GAMMA_BASIS_OPTIONS:
            if option["key"] == self._case.gamma_basis.value:
                return option["note"]
        return ""

    @Property(float, notify=inputsChanged)
    def areaRatio(self) -> float:
        return self._case.area_ratio

    @areaRatio.setter
    def areaRatio(self, value: float) -> None:
        number = self._finite(value)
        if number is None or number == self._case.area_ratio:
            return
        self._case = self._case.replace(area_ratio=number)
        self._on_input_changed()

    @Property(str, notify=inputsChanged)
    def ambientMode(self) -> str:
        return self._case.ambient.mode.value

    @ambientMode.setter
    def ambientMode(self, value: str) -> None:
        try:
            mode = service.AmbientMode(str(value))
        except ValueError:
            return
        if mode is self._case.ambient.mode:
            return
        self._case = self._case.replace(
            ambient=service.AmbientCondition(
                mode, self._case.ambient.custom_pressure))
        self._on_input_changed()

    @Property(float, notify=inputsChanged)
    def ambientPressure(self) -> float:
        """The custom value, in pascals. Editable in every mode.

        Kept even while a preset is selected so that switching to Custom does
        not blank the field the user had already typed.
        """
        return self._case.ambient.custom_pressure

    @ambientPressure.setter
    def ambientPressure(self, value: float) -> None:
        number = self._finite(value, floor=0.0)
        if number is None or number == self._case.ambient.custom_pressure:
            return
        self._case = self._case.replace(
            ambient=service.AmbientCondition(self._case.ambient.mode, number))
        self._on_input_changed()

    @Property(float, notify=inputsChanged)
    def effectiveAmbientPressure(self) -> float:
        """What the model will actually use, whatever the mode."""
        return self._case.ambient.pressure

    @Property(str, notify=inputsChanged)
    def ambientLabel(self) -> str:
        return self._case.ambient.label

    @Property(str, notify=inputsChanged)
    def scaleMode(self) -> str:
        return self._case.scale.mode.value

    @scaleMode.setter
    def scaleMode(self, value: str) -> None:
        try:
            mode = PerformanceScaleMode(str(value))
        except ValueError:
            return
        if mode is self._case.scale.mode:
            return
        if mode is PerformanceScaleMode.NORMALIZED:
            scale = PerformanceScale()
        else:
            existing = self._case.scale.value
            scale = PerformanceScale(
                mode, existing if existing is not None else self._default_size(mode))
        self._case = self._case.replace(scale=scale)
        self._on_input_changed()

    @staticmethod
    def _default_size(mode: PerformanceScaleMode) -> float:
        """A starting size for a newly chosen scale mode.

        Not a physical claim and not a default engine: it is a field value the
        user is expected to replace, offered only because an empty numeric
        field in a mode that requires one cannot be solved at all.
        """
        return 0.01 if mode is PerformanceScaleMode.THROAT_AREA else 10.0

    @Property(float, notify=inputsChanged)
    def scaleValue(self) -> float:
        value = self._case.scale.value
        return 0.0 if value is None else float(value)

    @scaleValue.setter
    def scaleValue(self, value: float) -> None:
        if self._case.scale.mode is PerformanceScaleMode.NORMALIZED:
            return
        number = self._finite(value)
        if number is None or number == self._case.scale.value:
            return
        self._case = self._case.replace(
            scale=PerformanceScale(self._case.scale.mode, number))
        self._on_input_changed()

    @Property(str, notify=inputsChanged)
    def scaleUnit(self) -> str:
        mode = self._case.scale.mode
        if mode is PerformanceScaleMode.THROAT_AREA:
            return "m²"
        if mode is PerformanceScaleMode.MASS_FLOW:
            return "kg/s"
        return ""

    @Property(str, notify=inputsChanged)
    def scaleLabel(self) -> str:
        return self._case.scale.label

    @Property(bool, notify=inputsChanged)
    def scaleNeedsValue(self) -> bool:
        return self._case.scale.is_scaled

    @Property(int, notify=inputsChanged)
    def precision(self) -> int:
        return self._precision

    @precision.setter
    def precision(self, value: int) -> None:
        number = max(3, min(12, int(value)))
        if number == self._precision:
            return
        self._precision = number
        self.inputsChanged.emit()
        self.chamberChanged.emit()
        self.resultChanged.emit()
        self.oracleChanged.emit()

    @Property(str, notify=inputsChanged)
    def caseHeadline(self) -> str:
        """What the *inputs* currently describe. Not what a result describes."""
        return self._case.headline

    @staticmethod
    def _finite(value, *, floor: float | None = None) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(number):
            return None
        if floor is None:
            if number <= 0.0:
                return None
        elif number < floor:
            return None
        return number

    def _on_input_changed(self) -> None:
        """An input moved: the result on screen no longer answers the form."""
        if self._outcome.result is not None or self._outcome.kind != "empty":
            self._stale = True
        self.inputsChanged.emit()
        self.resultChanged.emit()

    @Slot()
    def resetInputs(self) -> None:
        self._case = service.DEFAULT_PERFORMANCE_CASE
        self._on_input_changed()

    # ==================================================================
    # solving
    # ==================================================================

    @Property(bool, notify=resultChanged)
    def busy(self) -> bool:
        return self._busy

    @Slot()
    def calculate(self) -> None:
        """Solve the current case against the current chamber state.

        Calls no provider. The chamber state is read once, here, and handed to
        the service as a value.
        """
        if self._busy:
            return                      # no double submit
        self._busy = True
        self.resultChanged.emit()
        try:
            outcome = service.solve_performance(self._chamber(), self._case)
        finally:
            self._busy = False
        self._outcome = outcome
        self._stale = False
        self.resultChanged.emit()

    def current_case(self):
        """The nozzle and ambient configuration the form currently describes.

        A frozen ``PerformanceCase``. Read by the Trade Study workspace to
        snapshot a study baseline, in Python rather than through a Qt property,
        so no domain record reaches QML.
        """
        return self._case

    @Slot()
    def clearResult(self) -> None:
        self._outcome = service.EMPTY_OUTCOME
        self._stale = False
        self.resultChanged.emit()

    @Slot(int)
    def showTab(self, index: int) -> None:
        self.requestTab.emit(int(index))

    # -- status ---------------------------------------------------------

    @Property(bool, notify=resultChanged)
    def hasResult(self) -> bool:
        return self._outcome.result is not None

    @Property(bool, notify=resultChanged)
    def resultStale(self) -> bool:
        """Whether the inputs have moved since this result was produced."""
        return self._stale

    @Property(bool, notify=resultChanged)
    def chamberSuperseded(self) -> bool:
        """Whether the upstream chamber has changed under this result.

        Compared by identity. Two chamber outcomes with equal numbers are still
        two different answers, and a result that quietly adopted the newer one
        would be labelled with a case it was not computed from.
        """
        if self._outcome.chamber is None:
            return False
        return self._chamber() is not self._outcome.chamber

    @Property(str, notify=resultChanged)
    def statusKind(self) -> str:
        return self._outcome.kind

    @Property(str, notify=resultChanged)
    def statusLabel(self) -> str:
        return self._outcome.status_label

    @Property(str, notify=resultChanged)
    def statusTone(self) -> str:
        return self._outcome.status_tone

    @Property(str, notify=resultChanged)
    def message(self) -> str:
        return self._outcome.message

    @Property(str, notify=resultChanged)
    def resultHeadline(self) -> str:
        """What the *result* is for, from the case it carries."""
        return self._outcome.headline

    @Property(str, notify=resultChanged)
    def solvedChamberPressureText(self) -> str:
        """The chamber pressure the *result* used, for the canvas station.

        The live chamber is the wrong source for a label on the drawing. When
        the chemistry workspace supersedes it, the canvas still shows the
        expansion that was solved; putting the new chamber's pressure on that
        drawing would relabel a result with a condition that did not produce
        it, which is the failure Phase 5D section 133 exists to prevent.

        Taken from the same headline the rest of the application shows, so the
        two can never disagree about what the chamber was.
        """
        chamber = self._outcome.chamber
        if chamber is None:
            return ""
        from .thermochemistry_service import case_headline

        segment = case_headline(chamber.case).split("·")[-1].strip()
        return segment if segment.startswith("p_c ") else ""

    @Property(bool, notify=resultChanged)
    def scaled(self) -> bool:
        return self._outcome.is_scaled

    @Property(str, notify=resultChanged)
    def unscaledNote(self) -> str:
        """Why the engine group is absent, when it is."""
        if self._outcome.result is None or self._outcome.is_scaled:
            return ""
        return ("No engine size was given, so thrust, mass flow and the areas "
                "are not shown. They are withheld rather than defaulted: a "
                "made-up throat area would produce a thrust figure that looks "
                "like an answer.")

    # -- the numbers ----------------------------------------------------

    def _row(self, row: service.PerformanceRow) -> dict:
        return {
            "key": row.key,
            "label": row.label,
            "unit": row.unit,
            "value": _text(row.value, self._precision),
            "qualifier": row.qualifier,
            "emphasis": row.emphasis,
            "help": row.help,
            "available": row.available,
        }

    @Property("QVariantList", notify=resultChanged)
    def resultGroups(self):
        """Every performance number, grouped as the physics groups it.

        The grouping is not decoration. c* is a chamber and throat quantity,
        Cf belongs to the nozzle, and c_eff and Isp are the two multiplied
        together; a flat list invites a reader to take c* for an exhaust
        velocity, which is the most common misreading of these quantities.
        """
        rows = list(service.performance_rows(self._outcome))
        rows.extend(service.thrust_rows(self._outcome))
        if not rows:
            return []
        groups = []
        for group in service.PERFORMANCE_GROUPS:
            members = [self._row(row) for row in rows if row.group == group["key"]]
            if members:
                groups.append({"title": group["title"], "note": group["note"],
                               "rows": members})
        return groups

    @Property("QVariantList", notify=resultChanged)
    def reductionRows(self):
        """The gas reduction that produced these numbers, in full."""
        return [dict(row) for row in service.reduction_rows(self._outcome)]

    @Property("QVariantList", notify=resultChanged)
    def assumptions(self):
        """What the model claims, flat. Present before any result exists."""
        return list(service.assumption_rows(self._outcome))

    @Property("QVariantList", notify=resultChanged)
    def assumptionGroups(self):
        """The same claims, attributed to the layer that made each one."""
        return [{"title": group["title"], "note": group["note"],
                 "items": list(group["items"])}
                for group in service.assumption_groups(self._outcome)
                if group["items"]]

    @Property("QVariantList", notify=resultChanged)
    def diagnostics(self):
        """Everything a reader should know, from both layers, in one list.

        The chamber's own caveats come first and keep their origin. An
        assigned-enthalpy warning raised during the chemistry solve still
        applies to an Isp computed from that chemistry, and dropping it at the
        layer boundary is how a caveat gets lost between two correct
        calculations.
        """
        rows = list(service.inherited_diagnostics(self._outcome))
        rows.extend(service.own_diagnostics(self._outcome))
        return rows

    @Property(int, notify=resultChanged)
    def warningCount(self) -> int:
        return sum(1 for row in self.diagnostics
                   if row.get("severity") in ("warning", "error"))

    @Property("QVariantList", notify=resultChanged)
    def identityRows(self):
        """The internal consistency checks, recomputed for this result."""
        precision = self._precision
        return [{"name": row["name"],
                 "residual": _text(row["residual"], min(3, precision)),
                 "tolerance": _text(row["tolerance"], 3),
                 "passed": row["passed"],
                 "scaled": row["scaled"]}
                for row in service.identity_rows(self._outcome)]

    @Property(str, notify=resultChanged)
    def identitySummary(self) -> str:
        rows = service.identity_rows(self._outcome)
        if not rows:
            return ""
        failures = [row for row in rows if not row["passed"]]
        if not failures:
            return f"{len(rows)} of {len(rows)} — {IDENTITY_SUMMARY_OK}"
        names = ", ".join(row["name"] for row in failures)
        return (f"{len(rows) - len(failures)} of {len(rows)} closed. Failed: "
                f"{names}.")

    @Property(bool, notify=resultChanged)
    def identitiesPassed(self) -> bool:
        rows = service.identity_rows(self._outcome)
        return bool(rows) and all(row["passed"] for row in rows)

    @Property("QVariantList", notify=resultChanged)
    def provenanceRows(self):
        """Who computed what. Two rows, never merged into one."""
        return [dict(row) for row in service.performance_provenance(self._outcome)]

    # ==================================================================
    # the provider's own performance -- an oracle, run only on request
    # ==================================================================

    @Property("QVariantList", constant=True)
    def oracleModes(self):
        return [dict(option) for option in oracle.ORACLE_MODES]

    @Property(str, notify=oracleChanged)
    def oracleMode(self) -> str:
        return self._oracle_mode

    @oracleMode.setter
    def oracleMode(self, value: str) -> None:
        text = str(value)
        if text == self._oracle_mode:
            return
        if text not in {option["key"] for option in oracle.ORACLE_MODES}:
            return
        self._oracle_mode = text
        self.oracleChanged.emit()

    @Property(bool, notify=oracleChanged)
    def oracleBusy(self) -> bool:
        return self._oracle_busy

    @Slot()
    def runOracle(self) -> None:
        """Ask the provider for its own c*, Cf and Isp for this case.

        **This one does call the provider**, which is why it is a separate
        explicit action rather than part of ``calculate``. Nothing in the
        RocketForge performance path reads what it returns.
        """
        chamber = self._accepted_chamber()
        if chamber is None or chamber.case is None or self._oracle_busy:
            return
        self._oracle_busy = True
        self.oracleChanged.emit()
        try:
            outcome = oracle.run_oracle(chamber.case, self._case.area_ratio,
                                        self._oracle_mode)
        finally:
            self._oracle_busy = False
        self._oracle = outcome
        self._oracle_chamber = chamber
        self.oracleChanged.emit()

    @Slot()
    def clearOracle(self) -> None:
        self._oracle = oracle.EMPTY_ORACLE
        self._oracle_chamber = None
        self.oracleChanged.emit()

    @Property(str, notify=oracleChanged)
    def oracleStatus(self) -> str:
        return self._oracle.kind

    @Property(str, notify=oracleChanged)
    def oracleStatusLabel(self) -> str:
        return self._oracle.status_label

    @Property(str, notify=oracleChanged)
    def oracleMessage(self) -> str:
        return self._oracle.message

    @Property(str, notify=oracleChanged)
    def oracleProvider(self) -> str:
        return self._oracle.provider

    @Property(str, notify=oracleChanged)
    def oracleReferenceCondition(self) -> str:
        return self._oracle.reference_condition

    @Property(bool, notify=oracleChanged)
    def oracleStale(self) -> bool:
        """Whether the oracle answer belongs to a superseded chamber or ratio."""
        if not self._oracle.ok:
            return False
        if self._oracle_chamber is not self._accepted_chamber():
            return True
        return self._oracle.area_ratio != self._case.area_ratio

    @Property("QVariantList", notify=oracleChanged)
    def oracleRows(self):
        precision = self._precision
        return [{"label": row["label"], "unit": row["unit"],
                 "value": _text(row["value"], precision)}
                for row in oracle.oracle_rows(self._oracle)]

    @Property("QVariantList", notify=oracleChanged)
    def oracleComparisonRows(self):
        """RocketForge beside the provider, with the residual named honestly.

        Every row says "model difference", because that is what it is: the two
        calculations do not share a model, and no setting of either makes them
        the same one. A per-cent figure here measures a modelling choice, not
        an error in either program.
        """
        result = self._outcome.result
        if result is None:
            return []

        # Evaluated at the provider's own reference conditions rather than at
        # the ambient pressure the user happens to have chosen. The nozzle is
        # re-solved for each; the gas reduction is reused untouched, so no
        # chemistry runs and both figures are demonstrably the same gas as the
        # result above.
        reference = service.reference_condition_results(self._outcome)
        vacuum = reference["vacuum"]
        optimum = reference["optimum"]
        own = {
            "c_star": result.characteristic_velocity,
            "cf_optimum": None if optimum is None else optimum.thrust_coefficient,
            "isp_optimum": None if optimum is None else optimum.specific_impulse,
            "isp_vacuum": None if vacuum is None else vacuum.specific_impulse,
        }
        precision = self._precision
        rows = []
        for row in oracle.oracle_comparison_rows(own, self._oracle):
            difference = row["difference"]
            rows.append({
                "label": row["label"],
                "unit": row["unit"],
                "rocketforge": _text(row["rocketforge"], precision),
                "provider": _text(row["provider"], precision),
                "difference": (EM_DASH if difference is None
                               else f"{difference * 100.0:+.2f} %"),
                "reference": row["reference"],
                "kind": row["kind"],
            })
        return rows

    @Property(str, notify=oracleChanged)
    def oracleComparisonNote(self) -> str:
        """Why a residual here is not an error. Shown with the table, always."""
        if not self._oracle.ok:
            return ""
        return ("RocketForge holds gamma and R constant through the expansion; "
                "the provider is calorically imperfect in every mode it "
                "offers, and re-solves or freezes composition according to the "
                "mode chosen above. No setting of either makes them the same "
                "calculation, so each figure below is a model difference "
                "rather than an error in either program.\n\n"
                "Each row is evaluated at one reference condition on both "
                "sides. RocketForge's values here are therefore not the ones "
                "in the result above unless the ambient pressure happens to "
                "match — comparing a vacuum figure against an "
                "optimum-expansion one would be wrong by the whole pressure "
                "term.")

    # -- the solved snapshot, numerically -----------------------------------
    #
    # Added for the visual pilot. Every one of these is a *read* of the stored
    # ``IdealRocketPerformance``: nothing here computes, converts or rounds a
    # physical quantity, and the hero visualisation exists precisely so QML
    # never has to. They publish the **solved** snapshot, not the live input
    # fields, which is what keeps the drawing and the numbers on one result
    # while an edited input is marked stale.

    def _result(self):
        return self._outcome.result

    @Property(float, notify=resultChanged)
    def solvedAreaRatio(self) -> float:
        """Ae/At of the solved result, or 0 when there is none."""
        result = self._result()
        return 0.0 if result is None else float(result.exit.area_ratio)

    @Property(float, notify=resultChanged)
    def solvedExitMach(self) -> float:
        result = self._result()
        return 0.0 if result is None else float(result.exit.mach)

    @Property(float, notify=resultChanged)
    def solvedExitPressure(self) -> float:
        """Pa."""
        result = self._result()
        return 0.0 if result is None else float(result.exit.pressure)

    @Property(float, notify=resultChanged)
    def solvedAmbientPressure(self) -> float:
        """Pa, as the solved result recorded it."""
        result = self._result()
        return 0.0 if result is None else float(result.exit.ambient_pressure)

    @Property(str, notify=resultChanged)
    def solvedRegime(self) -> str:
        """``overexpanded`` | ``ideally_expanded`` | ``underexpanded``."""
        result = self._result()
        return "" if result is None else str(result.exit.regime)

    @Property(str, notify=resultChanged)
    def regimeLabel(self) -> str:
        """The regime in words, for a reader."""
        return {
            "overexpanded": "Overexpanded",
            "ideally_expanded": "Ideally expanded",
            "underexpanded": "Underexpanded",
        }.get(self.solvedRegime, "")

    @Property(float, notify=resultChanged)
    def solvedRadiusRatio(self) -> float:
        """r_e / r_t for the solved expansion, for drawing only.

        Published here rather than derived in QML. Area goes as radius
        squared, so a schematic that draws an area ratio needs its square root
        -- and the accepted rule that the interface performs only layout
        arithmetic is worth more than the two characters it would save. This is
        a *drawing* quantity: it sizes a picture and reaches no result.
        """
        result = self._result()
        if result is None:
            return 0.0
        from .performance_visual import radius_ratio_for_drawing

        return radius_ratio_for_drawing(result.exit.area_ratio)

    @Property(str, notify=resultChanged)
    def pressureRelationText(self) -> str:
        """The exit/ambient relation and the sign of the pressure term.

        Composed here because it is a statement about the solved result. The
        interface renders it; it does not decide it.
        """
        result = self._result()
        if result is None:
            return ""
        sign = self.pressureThrustSign
        if sign > 0:
            return "exit above ambient — pressure thrust positive"
        if sign < 0:
            return "exit below ambient — pressure thrust negative"
        return "exit matches ambient — pressure thrust zero"

    @Property(int, notify=resultChanged)
    def pressureThrustSign(self) -> int:
        """-1, 0 or +1 for the sign of the pressure term.

        Published as a number rather than left to a colour, so the interface
        can carry the sign in text and shape as well as in tone.
        """
        result = self._result()
        if result is None:
            return 0
        term = float(result.thrust_coefficient_pressure)
        return 1 if term > 0.0 else (-1 if term < 0.0 else 0)

    @Property("QVariantList", notify=resultChanged)
    def headlineMetrics(self) -> list:
        """The four normalised outputs, plus thrust when an engine size exists.

        Ordered by product priority rather than by computation order: the
        readout rail leads with specific impulse because that is the question
        the workspace answers.
        """
        result = self._result()
        if result is None:
            return []
        rows = [
            {"key": "isp", "label": "Specific impulse", "symbol": "Isp",
             "value": _rounded(result.specific_impulse, self._precision),
             "unit": "s", "primary": True},
            {"key": "cf", "label": "Thrust coefficient", "symbol": "Cf",
             "value": _rounded(result.thrust_coefficient, self._precision),
             "unit": "", "primary": False},
            {"key": "cstar", "label": "Characteristic velocity", "symbol": "c*",
             "value": _rounded(result.characteristic_velocity, self._precision),
             "unit": "m/s", "primary": False},
            {"key": "ceff", "label": "Effective exhaust velocity",
             "symbol": "c_eff",
             "value": _rounded(result.effective_exhaust_velocity,
                               self._precision),
             "unit": "m/s", "primary": False},
        ]
        thrust = result.thrust
        if thrust is not None:
            rows.append({"key": "thrust", "label": "Total thrust", "symbol": "F",
                         "value": _rounded(thrust.total, self._precision),
                         "unit": "N", "primary": True})
        return rows

    @Property("QVariantList", notify=resultChanged)
    def thrustCoefficientBreakdown(self) -> list:
        """Momentum and pressure terms, with the pressure sign made explicit."""
        result = self._result()
        if result is None:
            return []
        pressure = float(result.thrust_coefficient_pressure)
        return [
            {"label": "momentum",
             "value": _rounded(result.thrust_coefficient_momentum,
                               self._precision), "sign": ""},
            {"label": "pressure",
             "value": _rounded(pressure, self._precision),
             # A negative value already prints its own minus, so only the
             # positive case needs a sign added. Both produced "- -1.15172".
             "sign": "+" if pressure > 0 else ""},
        ]

    @Property("QVariantList", notify=resultChanged)
    def thrustBreakdown(self) -> list:
        """Momentum and pressure thrust, or empty when no engine size exists."""
        result = self._result()
        if result is None or result.thrust is None:
            return []
        pressure = float(result.thrust.pressure)
        return [
            {"label": "momentum",
             "value": _rounded(result.thrust.momentum, self._precision),
             "sign": ""},
            {"label": "pressure",
             "value": _rounded(pressure, self._precision),
             # A negative value already prints its own minus, so only the
             # positive case needs a sign added. Both produced "- -1.15172".
             "sign": "+" if pressure > 0 else ""},
        ]

    @Property("QVariantList", notify=resultChanged)
    def exitStateRows(self) -> list:
        """The exit-plane state, for the canvas annotations and the trace."""
        result = self._result()
        if result is None:
            return []
        return [
            {"symbol": "M_e", "label": "Exit Mach",
             "value": _rounded(result.exit.mach, self._precision), "unit": ""},
            {"symbol": "p_e", "label": "Exit pressure",
             "value": _rounded(result.exit.pressure, self._precision),
             "unit": "Pa"},
            {"symbol": "T_e", "label": "Exit temperature",
             "value": _rounded(result.exit.temperature, self._precision),
             "unit": "K"},
            {"symbol": "V_e", "label": "Exit velocity",
             "value": _rounded(result.exit.velocity, self._precision),
             "unit": "m/s"},
        ]

    @Property("QVariantList", notify=resultChanged)
    def traceRows(self) -> list:
        """The one-line model trace: which model, which reduction, what state."""
        if self._result() is None:
            return []
        return [
            {"label": "Model", "value": "Ideal \u00b7 constant-property"},
            {"label": "Gamma", "value": f"{self.gammaBasis} at {self.gammaStrategy}"},
            {"label": "Ambient", "value": self.ambientLabel},
            {"label": "Regime", "value": self.regimeLabel},
            {"label": "Scale", "value": self.scaleLabel},
        ]
