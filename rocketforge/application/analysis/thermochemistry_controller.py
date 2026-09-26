"""The QObject the Thermochemistry workspace binds to.

One controller for four views -- Calculator, Composition, Sweep, References --
because they share one thing and it is the important one: **the current result**.
Switching sub-tab must not re-solve, and two views must never be able to show
states from different calculations. A single owner of the current
``ChamberOutcome`` is what makes that structurally impossible rather than
merely intended.

    inputs  --Calculate-->  ChamberOutcome (immutable)
                                |
              +-----------------+-----------------+
              |                 |                 |
          Calculator       Composition       Provenance

Everything scientific happens below this file. The controller validates what
the interface typed, hands a ``ChamberCase`` to the service, and republishes
what comes back as display rows. It contains no chemistry, no unit conversion
beyond the pressure display boundary, and no formula.

**No provider import at module level.** ``main.py`` builds this controller at
start-up so QML has a singleton to bind to; the gateway defers every provider
import to first use, so a launch that never opens this workspace never loads
NASA CEA. An architecture test enforces it.

The Qt surface is declared here in full rather than inherited, for the reason
recorded in :mod:`analysis_behaviour`: PySide6 builds a corrupt metaobject when
a subclass declares a property that notifies with a base-class signal.
"""

from __future__ import annotations

import math

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication

from ..formatting import EM_DASH, format_engineering
from ..species_notation import species_label
from ..visualization.selection import AnalysisSelection
from . import thermochemistry_reference as reference
from . import thermochemistry_sweep as sweep
from .thermochemistry_provider import (
    CHEMISTRY_MODE_LABEL,
    CONSTRAINT_LABEL,
    MODEL_SUMMARY,
    PROVIDER_LABEL,
    availability,
    propellant_named,
    propellant_options,
)
from .thermochemistry_service import (
    GROUP_ADVANCED,
    GROUP_PRIMARY,
    OUTCOME_EMPTY,
    ChamberCase,
    ChamberOutcome,
    DEFAULT_CASE,
    assigned_enthalpy_notes,
    case_headline,
    condensed_summary,
    diagnostic_rows,
    provenance_details,
    provenance_summary,
    result_rows,
    solve_case,
    species_rows,
    species_set,
)
from .thermochemistry_solid_service import (
    CSTAR_LIMITATIONS,
    MODEL_BOUNDARY_NOTE,
    SolidCase,
    default_solid_case,
    is_solid_case,
    solid_conditions,
    solid_formulation_named,
    solid_formulation_options,
    solid_ingredient_named,
    solid_ingredient_options,
    solve_solid_case,
)
from .thermochemistry_table_model import ThermoTableModel

__all__ = ["ThermochemistryController"]

#: Pressure units the input accepts. Display only -- the case, the request and
#: every stored result stay in pascals, and changing the unit re-renders
#: without re-solving (Phase 5D §106, §107).
PRESSURE_UNITS: tuple[dict, ...] = (
    {"key": "Pa", "label": "Pa", "to_pa": 1.0, "decimals": 0, "step": 1.0e5},
    {"key": "bar", "label": "bar", "to_pa": 1.0e5, "decimals": 3, "step": 1.0},
    {"key": "MPa", "label": "MPa", "to_pa": 1.0e6, "decimals": 4, "step": 0.1},
)

#: Display-only floors for the composition table. Every one of these hides
#: rows; none of them changes the result. The label says "display" for exactly
#: that reason (Phase 5D §47, §48).
#:
#: The labels read "at least", not "greater than", because that is what the
#: filter does: a row whose fraction equals the threshold is kept. A label
#: promising one comparison while the code performs the other is a small lie
#: that a user would only find by counting rows.
TRACE_THRESHOLDS: tuple[dict, ...] = (
    {"label": "Show all", "value": 0.0},
    {"label": "\u2265 1e-12", "value": 1.0e-12},
    {"label": "\u2265 1e-9", "value": 1.0e-9},
    {"label": "\u2265 1e-6", "value": 1.0e-6},
    {"label": "\u2265 1e-4", "value": 1.0e-4},
)

#: How many species a sweep chart will draw at once. A practical drawing limit,
#: not a limit on the data: every species stays in the result and in the
#: selectable list (Phase 5D §69).
MAX_SWEEP_SPECIES = 6

#: How many species the Calculator's chamber-state view lists. The full set,
#: every species the provider returned, stays on the Composition view.
LEADING_SPECIES = 6

_COMPOSITION_COLUMNS = (
    {"key": "species", "label": "Species", "kind": "text", "align": "left"},
    {"key": "phase", "label": "Phase", "kind": "text", "align": "left"},
    {"key": "mole", "label": "Mole fraction  X", "kind": "number",
     "decimals_hint": 6},
    {"key": "mass", "label": "Mass fraction  Y", "kind": "number",
     "decimals_hint": 6},
)


class ThermochemistryController(QObject):
    """Application-side facade for the Thermochemistry analysis workspace."""

    providerChanged = Signal()
    inputsChanged = Signal()
    resultChanged = Signal()
    compositionChanged = Signal()
    sweepInputsChanged = Signal()
    sweepChanged = Signal()
    referenceChanged = Signal()
    requestTab = Signal(int)
    formulationKindChanged = Signal()
    solidInputsChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)

        self._case = DEFAULT_CASE
        #: "bipropellant" or "solid". The workspace computes the same kind of
        #: answer either way -- an equilibrium chamber state -- so the two share
        #: every result surface and differ only in what goes in.
        self._formulation_kind = "bipropellant"
        self._solid_case: SolidCase | None = None
        self._pressure_unit = "MPa"
        self._precision = 6

        self._outcome: ChamberOutcome = ChamberOutcome(kind=OUTCOME_EMPTY)
        self._stale = False
        self._busy = False

        # Composition. The complete species list is kept here; the model below
        # is a filtered *view* of it, rebuilt on demand. Nothing ever removes a
        # species from this tuple.
        self._species: tuple = ()
        self._composition_basis = "mole"
        self._trace_index = 0
        self._species_filter = ""
        self._composition_model = ThermoTableModel(self)

        # Sweep.
        self._sweep_range = sweep.DEFAULT_SWEEP_RANGE
        self._sweep_start = self._sweep_range.start
        self._sweep_end = self._sweep_range.end
        self._sweep_points = self._sweep_range.points
        self._sweep_message = ""
        self._sweep_result: sweep.SweepResult | None = None
        self._sweep_stale = False
        self._sweep_model = ThermoTableModel(self)
        self._sweep_series: dict[str, list] = {}
        self._sweep_species_options: tuple[str, ...] = ()
        self._sweep_species: list[str] = []
        self._sweep_species_basis = "mole"
        self._sweep_species_series: list = []
        # One selection for the sweep's views -- the plots, the table and the
        # Inspector -- keyed by the point's row; the Inspector reads the
        # solved point (sweepPoint), nothing is re-solved. Any change to the
        # sweep (a new run, a clear, an edited input) drops it: point 12 of
        # the old sweep is not point 12 of the new one.
        self._sweep_selection = AnalysisSelection(self)
        self.sweepChanged.connect(self._sweep_selection.clear)

        # References.
        self._reference_case = None
        self._reference_outcome: ChamberOutcome | None = None
        self._reference_rows: tuple = ()

    # ==================================================================
    # provider
    # ==================================================================

    @Property(bool, notify=providerChanged)
    def providerAvailable(self) -> bool:
        return availability().usable

    @Property(str, notify=providerChanged)
    def providerLabel(self) -> str:
        return PROVIDER_LABEL

    @Property(str, notify=providerChanged)
    def providerVersion(self) -> str:
        return availability().library_version

    @Property(str, notify=providerChanged)
    def providerStatus(self) -> str:
        return availability().status

    @Property(str, notify=providerChanged)
    def providerDetail(self) -> str:
        return availability().detail

    @Property(str, notify=providerChanged)
    def providerRemedy(self) -> str:
        return availability().remedy

    @Property(str, notify=providerChanged)
    def providerHeadline(self) -> str:
        return availability().headline

    @Property(str, constant=True)
    def modelSummary(self) -> str:
        return MODEL_SUMMARY

    @Property(str, constant=True)
    def chemistryMode(self) -> str:
        return CHEMISTRY_MODE_LABEL

    @Property(str, constant=True)
    def constraintLabel(self) -> str:
        return CONSTRAINT_LABEL

    @Slot(int)
    def showTab(self, index: int) -> None:
        """Ask the workspace to show one of its four views.

        The same mechanism the Nozzle Lab uses. It exists so that something
        other than a mouse click can move the workspace -- an acceptance
        harness, or a future cross-page link -- without anything synthesising
        desktop input.
        """
        self.requestTab.emit(max(0, min(3, int(index))))

    @Slot()
    def refreshProvider(self) -> None:
        """Re-ask whether a provider is usable, and drop anything it produced.

        A result produced by one provider must never be displayed under another
        provider's name, so re-checking availability clears the result rather
        than recomputing it in place (``15`` §4.1, Phase 5D §23).
        """
        from .thermochemistry_provider import reset_provider_state

        reset_provider_state()
        self._clear_result()
        self._clear_sweep()
        self._reference_outcome = None
        self._reference_rows = ()
        self.providerChanged.emit()
        self.referenceChanged.emit()

    # ==================================================================
    # inputs
    # ==================================================================

    @Property("QVariantList", constant=True)
    def fuelOptions(self):
        return [self._option_dict(option) for option in propellant_options()
                if option.is_fuel]

    @Property("QVariantList", constant=True)
    def oxidiserOptions(self):
        return [self._option_dict(option) for option in propellant_options()
                if option.is_oxidiser]

    @staticmethod
    def _option_dict(option) -> dict:
        return {
            "key": option.key,
            "label": option.label,
            "role": option.role,
            "phase": option.phase,
            "referenceTemperature": option.reference_temperature,
            "providerName": option.provider_name,
            "rangeText": option.range_text,
            "source": option.source,
        }

    @Property(str, notify=inputsChanged)
    def fuel(self) -> str:
        return self._case.fuel

    @fuel.setter
    def fuel(self, value: str) -> None:
        option = propellant_named(str(value))
        if option is None or not option.is_fuel or value == self._case.fuel:
            return
        # Move the stream temperature to the new reactant's own reference
        # condition. Carrying 111.6 K over to liquid hydrogen would be outside
        # the range CEA states for it, and silently keeping an invalid value is
        # worse than moving to a stated one.
        self._case = self._case.replace(
            fuel=str(value), fuel_temperature=option.reference_temperature)
        self._on_input_changed()

    @Property(str, notify=inputsChanged)
    def oxidiser(self) -> str:
        return self._case.oxidiser

    @oxidiser.setter
    def oxidiser(self, value: str) -> None:
        option = propellant_named(str(value))
        if option is None or not option.is_oxidiser or value == self._case.oxidiser:
            return
        self._case = self._case.replace(
            oxidiser=str(value),
            oxidiser_temperature=option.reference_temperature)
        self._on_input_changed()

    @Property(float, notify=inputsChanged)
    def fuelTemperature(self) -> float:
        return self._case.fuel_temperature

    @fuelTemperature.setter
    def fuelTemperature(self, value: float) -> None:
        number = self._positive(value)
        if number is None or number == self._case.fuel_temperature:
            return
        self._case = self._case.replace(fuel_temperature=number)
        self._on_input_changed()

    @Property(float, notify=inputsChanged)
    def oxidiserTemperature(self) -> float:
        return self._case.oxidiser_temperature

    @oxidiserTemperature.setter
    def oxidiserTemperature(self, value: float) -> None:
        number = self._positive(value)
        if number is None or number == self._case.oxidiser_temperature:
            return
        self._case = self._case.replace(oxidiser_temperature=number)
        self._on_input_changed()

    @Property(float, notify=inputsChanged)
    def mixtureRatio(self) -> float:
        return self._case.oxidiser_fuel_ratio

    @mixtureRatio.setter
    def mixtureRatio(self, value: float) -> None:
        number = self._positive(value)
        if number is None or number == self._case.oxidiser_fuel_ratio:
            return
        self._case = self._case.replace(oxidiser_fuel_ratio=number)
        self._on_input_changed()

    @Property(float, notify=inputsChanged)
    def chamberPressure(self) -> float:
        """Chamber pressure in pascals. The canonical value, always."""
        return self._case.chamber_pressure

    @Property(float, notify=inputsChanged)
    def chamberPressureDisplay(self) -> float:
        """The same pressure in the selected display unit."""
        return self._case.chamber_pressure / self._pressure_factor()

    @chamberPressureDisplay.setter
    def chamberPressureDisplay(self, value: float) -> None:
        number = self._positive(value)
        if number is None:
            return
        pascals = number * self._pressure_factor()
        if pascals == self._case.chamber_pressure:
            return
        self._case = self._case.replace(chamber_pressure=pascals)
        self._on_input_changed()

    @Property("QVariantList", constant=True)
    def pressureUnits(self):
        return [dict(unit) for unit in PRESSURE_UNITS]

    @Property(str, notify=inputsChanged)
    def pressureUnit(self) -> str:
        return self._pressure_unit

    @pressureUnit.setter
    def pressureUnit(self, value: str) -> None:
        if value == self._pressure_unit:
            return
        if not any(unit["key"] == value for unit in PRESSURE_UNITS):
            return
        self._pressure_unit = str(value)
        # A display-unit change is not an input change: the stored pressure is
        # untouched, so the existing result stays valid and is not marked stale.
        self.inputsChanged.emit()
        self.resultChanged.emit()
        self.sweepChanged.emit()

    def _pressure_factor(self) -> float:
        for unit in PRESSURE_UNITS:
            if unit["key"] == self._pressure_unit:
                return float(unit["to_pa"])
        return 1.0

    @Property("QVariantMap", notify=inputsChanged)
    def pressureUnitInfo(self):
        for unit in PRESSURE_UNITS:
            if unit["key"] == self._pressure_unit:
                return dict(unit)
        return dict(PRESSURE_UNITS[0])

    @Property(str, notify=inputsChanged)
    def fuelRangeText(self) -> str:
        option = propellant_named(self._case.fuel)
        return option.range_text if option else ""

    @Property(str, notify=inputsChanged)
    def oxidiserRangeText(self) -> str:
        option = propellant_named(self._case.oxidiser)
        return option.range_text if option else ""

    @Property(str, notify=inputsChanged)
    def fuelProviderName(self) -> str:
        option = propellant_named(self._case.fuel)
        return option.provider_name if option else ""

    @Property(str, notify=inputsChanged)
    def oxidiserProviderName(self) -> str:
        option = propellant_named(self._case.oxidiser)
        return option.provider_name if option else ""

    @Property(str, notify=inputsChanged)
    def caseHeadline(self) -> str:
        """What the *form* currently says. Not what the result is for."""
        return case_headline(self._case)

    @staticmethod
    def _positive(value) -> float | None:
        """Accept a strictly positive finite number, refuse anything else.

        Refusal means "leave the stored value alone", never "clamp it into
        range". A silently clamped input is a number the user did not enter
        being used as though they had (Phase 5D §24, §188).
        """
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(number) or number <= 0.0:
            return None
        return number

    def _on_input_changed(self) -> None:
        """An input that defines the calculation moved."""
        if self._outcome.kind != OUTCOME_EMPTY:
            self._stale = True
        if self._sweep_result is not None:
            self._sweep_stale = True
        self.inputsChanged.emit()
        self.resultChanged.emit()
        self.sweepChanged.emit()

    @Slot()
    def resetInputs(self) -> None:
        """Return the form to the validated demonstration case.

        Labelled as an example, never as a recommended design: it is the
        operating point Phase 5C validated end to end, which is a statement
        about evidence and not about engineering merit (Phase 5D §189, §190).
        """
        self._case = DEFAULT_CASE
        self._clear_result()
        self._clear_sweep()
        self.inputsChanged.emit()


    # ==================================================================
    # solid formulations
    # ==================================================================
    #
    # The workspace answers the same question for a solid grain that it answers
    # for a bipropellant: what is the equilibrium state of the chamber. So the
    # two modes share every result surface -- readouts, species table, condensed
    # summary, provenance -- and differ only in what goes in.
    #
    # Deliberately absent: burn rate, grain geometry, motor performance and
    # every reference-performance quantity (c*, Cf, Isp) -- R1.1 and beyond.
    # No disabled control or "coming soon" panel stands in for them.

    @Property(str, notify=formulationKindChanged)
    def formulationKind(self) -> str:
        return self._formulation_kind

    @formulationKind.setter
    def formulationKind(self, value: str) -> None:
        kind = str(value).strip().lower()
        if kind not in ("bipropellant", "solid") or kind == self._formulation_kind:
            return
        self._formulation_kind = kind
        # A result belongs to the mode that produced it: switching neither
        # relabels it nor leaves it on screen under the other mode's inputs.
        self._clear_result()
        self._clear_sweep()
        self.formulationKindChanged.emit()
        self.inputsChanged.emit()
        self.solidInputsChanged.emit()

    @Property(bool, notify=formulationKindChanged)
    def isSolid(self) -> bool:
        return self._formulation_kind == "solid"

    @Property(str, constant=True)
    def modelBoundaryNote(self) -> str:
        """What a solid result does and does not claim."""
        return MODEL_BOUNDARY_NOTE

    def solid_case(self) -> SolidCase:
        if self._solid_case is None:
            self._solid_case = default_solid_case()
        return self._solid_case

    def _set_solid_case(self, case: SolidCase) -> None:
        if case == self._solid_case:
            return
        self._solid_case = case
        # An edit after a solve marks the displayed result stale. It is kept on
        # screen, dimmed, still labelled with the case that produced it --
        # never deleted, never silently refreshed.
        if self._outcome.state is not None:
            self._stale = True
        self.solidInputsChanged.emit()
        self.resultChanged.emit()

    # -- reference formulations ------------------------------------------

    @Property("QVariantList", constant=True)
    def solidFormulationOptions(self):
        return [{"key": o.key, "label": o.label, "reference": o.reference,
                 "isReferenceCase": o.is_reference_case}
                for o in solid_formulation_options()]

    @Property(str, notify=solidInputsChanged)
    def solidFormulationLabel(self) -> str:
        case = self.solid_case()
        option = case.reference()
        if case.is_published_composition:
            return option.label
        if option is not None:
            return f"Edited from {option.label}"
        return "Custom formulation"

    @Property(str, notify=solidInputsChanged)
    def solidFormulationReference(self) -> str:
        option = self.solid_case().reference()
        return option.reference if option else ""

    @Property(bool, notify=solidInputsChanged)
    def solidIsReferenceCase(self) -> bool:
        """The published grain at a published operating point, exactly."""
        return self.solid_case().is_validated_operating_point

    @Property(str, notify=solidInputsChanged)
    def solidReferenceNote(self) -> str:
        """What the published source does and does not vouch for here."""
        case = self.solid_case()
        option = case.reference()
        if option is None:
            return ""
        if case.is_validated_operating_point:
            return f"Reference / validation case · {option.reference}"
        if case.is_published_composition:
            return (f"Published composition · {option.reference} · this "
                    "operating point differs from the published one")
        return ""

    @Property(bool, notify=solidInputsChanged)
    def solidEdited(self) -> bool:
        case = self.solid_case()
        return case.reference_key is not None and not case.is_published_composition

    @Slot(str)
    def loadSolidFormulation(self, key: str) -> None:
        option = solid_formulation_named(str(key))
        if option is None:
            return
        self._set_solid_case(SolidCase(
            ingredients=option.ingredients,
            chamber_pressure=option.chamber_pressure,
            initial_temperature=option.initial_temperature,
            reference_key=option.key))

    @Slot()
    def resetSolidFormulation(self) -> None:
        """Return the grain to its published composition."""
        self._solid_case = default_solid_case()
        self._clear_result()
        self.solidInputsChanged.emit()

    # -- the grain -------------------------------------------------------

    @Property("QVariantList", notify=solidInputsChanged)
    def solidIngredients(self):
        """The grain, as editable rows.

        ``percent`` is what the editor shows and what a propellant chemist
        writes; ``fraction`` is what the physics layer is given. The division
        by 100 happens once, here. ``temperature`` is the temperature CEA is
        given for that reactant; ``assignedTemperature`` is non-empty when the
        reactant's enthalpy is fixed at another one and the grain temperature
        therefore cannot reach it.
        """
        case = self.solid_case()
        rows = []
        for index, (key, fraction) in enumerate(case.ingredients):
            option = solid_ingredient_named(key)
            custom = option is not None and option.representation == "custom"
            assigned = option.assigned_temperature if option else None
            if custom:
                representation = "custom · assigned enthalpy"
            elif option is not None and option.phase:
                representation = f"thermo.lib · {option.phase}"
            else:
                representation = "thermo.lib"
            rows.append({
                "index": index,
                "key": key,
                "name": option.name if option else key,
                "fraction": fraction,
                "percent": fraction * 100.0,
                "percentText": f"{fraction * 100.0:.3f}",
                "isCustom": custom,
                "representation": representation,
                "source": option.source if option else "",
                "temperatureText": f"{case.initial_temperature:g} K",
                "assignedTemperatureText": (
                    f"{assigned:g} K" if assigned is not None else ""),
                "temperatureIgnored": (
                    assigned is not None
                    and abs(assigned - case.initial_temperature) > 1e-9),
            })
        return rows

    @Property("QVariantList", notify=solidInputsChanged)
    def solidAddableIngredients(self):
        """Catalogue ingredients not already in the grain."""
        present = set(self.solid_case().keys)
        return [{"key": o.key, "name": o.name,
                 "label": (f"{o.name}  (custom)" if o.representation == "custom"
                           else species_label(o.name))}
                for o in solid_ingredient_options() if o.key not in present]

    @Slot(str)
    def addSolidIngredient(self, key: str) -> None:
        """Add an ingredient at 0 %, so the total does not move by itself."""
        key = str(key)
        case = self.solid_case()
        if solid_ingredient_named(key) is None or key in case.keys:
            return
        self._set_solid_case(case.replace(
            ingredients=case.ingredients + ((key, 0.0),)))

    @Slot(int)
    def removeSolidIngredient(self, index: int) -> None:
        """Remove one ingredient. The others are not rescaled to compensate."""
        case = self.solid_case()
        if not 0 <= index < len(case.ingredients) or len(case.ingredients) <= 1:
            return
        ingredients = case.ingredients[:index] + case.ingredients[index + 1:]
        self._set_solid_case(case.replace(ingredients=ingredients))

    @Slot(int, float)
    def setSolidMassPercent(self, index: int, percent: float) -> None:
        """Set one ingredient's mass percent, in [0, 100].

        The total is **not** renormalised afterwards. Silently rescaling the
        others would change inputs the user did not touch; instead the running
        total is shown and a grain that does not close refuses to solve.
        """
        case = self.solid_case()
        if not 0 <= index < len(case.ingredients):
            return
        try:
            number = float(percent)
        except (TypeError, ValueError):
            return
        if not math.isfinite(number) or number < 0.0 or number > 100.0:
            return
        key, old = case.ingredients[index]
        fraction = number / 100.0
        if fraction == old:
            return
        ingredients = list(case.ingredients)
        ingredients[index] = (key, fraction)
        self._set_solid_case(case.replace(ingredients=tuple(ingredients)))

    @Property(float, notify=solidInputsChanged)
    def solidMassTotalPercent(self) -> float:
        return self.solid_case().mass_fraction_sum * 100.0

    @Property(str, notify=solidInputsChanged)
    def solidMassTotalText(self) -> str:
        return f"{self.solidMassTotalPercent:.3f} %"

    @Property(bool, notify=solidInputsChanged)
    def solidMassBalanced(self) -> bool:
        """Whether the grain closes at 100 %, within the domain's tolerance."""
        return self.solid_case().is_balanced

    # -- operating point -------------------------------------------------

    @Property(float, notify=solidInputsChanged)
    def solidChamberPressureDisplay(self) -> float:
        return self.solid_case().chamber_pressure / self._pressure_factor()

    @solidChamberPressureDisplay.setter
    def solidChamberPressureDisplay(self, value: float) -> None:
        number = self._positive(value)
        if number is None:
            return
        self._set_solid_case(self.solid_case().replace(
            chamber_pressure=number * self._pressure_factor()))

    @Property(float, notify=solidInputsChanged)
    def solidGrainTemperature(self) -> float:
        return self.solid_case().initial_temperature

    @solidGrainTemperature.setter
    def solidGrainTemperature(self, value: float) -> None:
        number = self._positive(value)
        if number is None:
            return
        self._set_solid_case(self.solid_case().replace(initial_temperature=number))

    @Property("QVariantList", notify=resultChanged)
    def solidConditions(self):
        """The condition snapshot behind the **displayed** solid result.

        Read from the outcome's own case, so editing the form cannot relabel an
        existing result -- the same rule the bipropellant path follows.
        """
        case = self._outcome.case
        if not is_solid_case(case):
            return []
        return [dict(row) for row in solid_conditions(case)]



    # -- CEA equilibrium characteristic velocity -------------------------
    #
    # Read from the outcome, like every other result: a stale result keeps the
    # c* of the case that produced it. Shown only when every validity check
    # passed; a refused c* is shown as refused, with the reason, never as a
    # number. Not placed under any "performance" heading, because it is not a
    # motor performance figure.

    def _solid_cstar(self):
        if not is_solid_case(self._outcome.case) or self._outcome.state is None:
            return None
        return self._outcome.characteristic_velocity

    @Property(bool, notify=resultChanged)
    def solidCStarShown(self) -> bool:
        return self._solid_cstar() is not None

    @Property(bool, notify=resultChanged)
    def solidCStarAvailable(self) -> bool:
        cstar = self._solid_cstar()
        return bool(cstar is not None and cstar.available)

    @Property(str, notify=resultChanged)
    def solidCStarText(self) -> str:
        """At most six significant figures, whatever the precision setting.

        Measured: starting CEA from a different condensed phase moves Example
        5's c* by 2.1e-06 relative. A seventh figure would be solver noise.
        """
        cstar = self._solid_cstar()
        if cstar is None or not cstar.available:
            return EM_DASH
        return format_engineering(cstar.value, min(self._precision, 6))

    @Property(str, notify=resultChanged)
    def solidCStarRefusal(self) -> str:
        cstar = self._solid_cstar()
        return cstar.refusal if cstar is not None else ""

    @Property(str, notify=resultChanged)
    def solidCStarCondensedNote(self) -> str:
        """The condensed-phase assumption, with the mass it applies to."""
        cstar = self._solid_cstar()
        if cstar is None:
            return ""
        fraction = cstar.condensed_mass_fraction
        share = ("" if fraction is None else
                 f" Condensed products are {fraction * 100.0:.1f} % of the "
                 "mass here.")
        return cstar.condensed_assumption + share

    @Property("QVariantList", constant=True)
    def solidCStarLimitations(self):
        """What this number is not. Stated every time it is shown."""
        return list(CSTAR_LIMITATIONS)

    # ==================================================================
    # calculate
    # ==================================================================

    @Property(bool, notify=resultChanged)
    def busy(self) -> bool:
        return self._busy

    def _set_busy(self, value: bool) -> None:
        """One flag, both notifications.

        Calculate and Run sweep are disabled by the same property, and they
        live on different tabs bound to different signals. Emitting only the
        one the current operation belongs to would leave the other button's
        binding stale.
        """
        self._busy = bool(value)
        self.resultChanged.emit()
        self.sweepChanged.emit()

    @Slot()
    def calculate(self) -> None:
        """Solve the current case and republish everything derived from it."""
        if self._busy:
            return                      # no double submit
        self._set_busy(True)
        try:
            outcome = (solve_solid_case(self.solid_case())
                       if self.isSolid else solve_case(self._case))
        finally:
            self._set_busy(False)
        self._adopt(outcome)

    def _adopt(self, outcome: ChamberOutcome) -> None:
        self._outcome = outcome
        self._stale = False
        self._species = species_rows(outcome) if outcome.state is not None else ()
        self._rebuild_composition()
        self.resultChanged.emit()
        self.compositionChanged.emit()

    def _clear_result(self) -> None:
        self._outcome = ChamberOutcome(kind=OUTCOME_EMPTY)
        self._stale = False
        self._species = ()
        self._composition_model.clear()
        self.resultChanged.emit()
        self.compositionChanged.emit()

    @Slot()
    def clearResult(self) -> None:
        self._clear_result()

    def current_case(self) -> ChamberCase:
        """The operating point the form currently describes.

        A frozen record, so a caller that keeps one keeps exactly what it read.
        Used by the Trade Study workspace to snapshot a study baseline; a study
        built from it does not follow later edits to this form.
        """
        return self._case

    def chamber_outcome(self) -> ChamberOutcome:
        """The current outcome, for another application controller to consume.

        A plain Python method rather than a Qt property, and that is the whole
        design: a ``ChamberOutcome`` carries a ``ChamberGas``, so exposing it
        to QML would put a physics object in the interface. The Rocket
        Performance workspace reads it here, in Python, and publishes only
        formatted rows.

        Returned by reference and never copied. The object is frozen, so a
        consumer holding one holds exactly the state that produced it even
        after this controller has moved on to another case -- which is what
        lets a performance result keep saying which chamber it belongs to.
        """
        return self._outcome

    # -- status ---------------------------------------------------------

    @Property(bool, notify=resultChanged)
    def hasResult(self) -> bool:
        return self._outcome.state is not None

    @Property(bool, notify=resultChanged)
    def resultStale(self) -> bool:
        """Whether the inputs have moved since this result was produced."""
        return self._stale

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
    def statusMessage(self) -> str:
        return self._outcome.message

    @Property(str, notify=resultChanged)
    def statusField(self) -> str:
        return self._outcome.field

    @Property(str, notify=resultChanged)
    def resultHeadline(self) -> str:
        """The conditions **this result** was produced under.

        Read from the outcome's own case, so editing the form cannot relabel an
        existing result (Phase 5D §133, §134).
        """
        return case_headline(self._outcome.case)

    @Property("QVariantList", notify=resultChanged)
    def resultConditions(self):
        """The full condition snapshot behind the displayed result."""
        case = self._outcome.case
        if case is None:
            return []
        if is_solid_case(case):
            # A solid result. Its conditions are a formulation, not a pair of
            # streams and a ratio, so they are built by the solid service.
            return [dict(row) for row in solid_conditions(case)]
        fuel = propellant_named(case.fuel)
        oxidiser = propellant_named(case.oxidiser)
        factor = self._pressure_factor()
        return [
            {"label": "Fuel", "value": case.fuel,
             "note": fuel.provider_name if fuel else ""},
            {"label": "Oxidiser", "value": case.oxidiser,
             "note": oxidiser.provider_name if oxidiser else ""},
            {"label": "O/F", "value": f"{case.oxidiser_fuel_ratio:g}",
             "note": "oxidiser mass / fuel mass"},
            {"label": "Chamber pressure",
             "value": f"{case.chamber_pressure / factor:g} {self._pressure_unit}",
             "note": f"{case.chamber_pressure:g} Pa"},
            {"label": "Fuel temperature",
             "value": f"{case.fuel_temperature:g} K", "note": ""},
            {"label": "Oxidiser temperature",
             "value": f"{case.oxidiser_temperature:g} K", "note": ""},
            {"label": "Model", "value": MODEL_SUMMARY, "note": ""},
        ]

    # -- readouts -------------------------------------------------------

    @Property(int, notify=resultChanged)
    def precision(self) -> int:
        return self._precision

    @precision.setter
    def precision(self, value: int) -> None:
        digits = max(3, min(12, int(value)))
        if digits == self._precision:
            return
        self._precision = digits
        self._composition_model.setPrecision(digits)
        self._sweep_model.setPrecision(digits)
        self.resultChanged.emit()
        self.referenceChanged.emit()

    def _row_dicts(self, group: str):
        return [
            {
                "key": row.key,
                "label": row.label,
                "qualifier": row.qualifier,
                "unit": row.unit,
                "value": (format_engineering(row.value, self._precision)
                          if row.available else EM_DASH),
                "raw": float("nan") if row.value is None else float(row.value),
                "available": row.available,
                "emphasis": row.emphasis,
                "help": row.help,
            }
            for row in result_rows(self._outcome) if row.group == group
        ]

    @Property("QVariantList", notify=resultChanged)
    def resultRows(self):
        return self._row_dicts(GROUP_PRIMARY)

    @Property("QVariantList", notify=resultChanged)
    def advancedRows(self):
        return self._row_dicts(GROUP_ADVANCED)

    # -- diagnostics ----------------------------------------------------

    @Property("QVariantList", notify=resultChanged)
    def diagnostics(self):
        return [self._diagnostic_dict(row)
                for row in diagnostic_rows(self._outcome)]

    @Property("QVariantList", notify=resultChanged)
    def warnings(self):
        """Warnings and errors only. Info rows live in the full list."""
        return [self._diagnostic_dict(row)
                for row in diagnostic_rows(self._outcome, include_info=False)]

    @staticmethod
    def _diagnostic_dict(row) -> dict:
        return {
            "code": row.code,
            "severity": row.severity,
            "title": row.title,
            "message": row.message,
            "field": row.field,
            "known": row.known,
        }

    @Property(int, notify=resultChanged)
    def warningCount(self) -> int:
        return len(diagnostic_rows(self._outcome, include_info=False))

    @Property("QVariantList", notify=resultChanged)
    def assignedEnthalpyNotes(self):
        """The blocking Phase 5D warning, expanded into its three numbers.

        Requested temperature, the temperature the provider's model actually
        used, and which reactant. All three are shown, because "temperature
        ignored" without them is not something a user can act on (§33).
        """
        return [
            {
                "reactant": note["reactant"],
                "requested": note["requested"],
                "assigned": note["assigned"],
                "requestedText": f"{note['requested']:g} K",
                "assignedText": f"{note['assigned']:g} K",
                "message": note["message"],
            }
            for note in assigned_enthalpy_notes(self._outcome)
        ]

    # -- provenance -----------------------------------------------------

    @Property("QVariantMap", notify=resultChanged)
    def provenanceSummary(self):
        return provenance_summary(self._outcome)

    @Property("QVariantList", notify=resultChanged)
    def provenanceRows(self):
        return [dict(row) for row in provenance_details(self._outcome)]

    @Property("QVariantList", notify=resultChanged)
    def speciesSet(self):
        return list(species_set(self._outcome))

    # ==================================================================
    # composition
    # ==================================================================

    @Property(QObject, constant=True)
    def compositionModel(self) -> QObject:
        return self._composition_model

    @Property("QVariantList", constant=True)
    def compositionColumns(self):
        return [dict(column) for column in _COMPOSITION_COLUMNS]

    @Property(bool, notify=compositionChanged)
    def hasComposition(self) -> bool:
        return bool(self._species)

    @Property(str, notify=compositionChanged)
    def compositionBasis(self) -> str:
        return self._composition_basis

    @compositionBasis.setter
    def compositionBasis(self, value: str) -> None:
        if value not in ("mole", "mass") or value == self._composition_basis:
            return
        # A basis change is a display change. The stored composition keeps its
        # own canonical basis; both fractions were already carried on every row
        # (Phase 5D §44).
        self._composition_basis = str(value)
        self._rebuild_composition()
        self.compositionChanged.emit()

    @Property("QVariantList", constant=True)
    def traceThresholds(self):
        return [dict(entry) for entry in TRACE_THRESHOLDS]

    @Property(int, notify=compositionChanged)
    def traceThresholdIndex(self) -> int:
        return self._trace_index

    @traceThresholdIndex.setter
    def traceThresholdIndex(self, value: int) -> None:
        index = max(0, min(len(TRACE_THRESHOLDS) - 1, int(value)))
        if index == self._trace_index:
            return
        self._trace_index = index
        self._rebuild_composition()
        self.compositionChanged.emit()

    @Property(float, notify=compositionChanged)
    def traceThreshold(self) -> float:
        return float(TRACE_THRESHOLDS[self._trace_index]["value"])

    @Property(str, notify=compositionChanged)
    def speciesFilter(self) -> str:
        return self._species_filter

    @speciesFilter.setter
    def speciesFilter(self, value: str) -> None:
        text = str(value)
        if text == self._species_filter:
            return
        self._species_filter = text
        self._rebuild_composition()
        self.compositionChanged.emit()

    def _visible_species(self) -> list:
        """The rows the table shows. A **view**, computed from the full set.

        The full set stays in ``self._species`` untouched, which is what makes
        raising and lowering the threshold reversible with the original values
        intact (Phase 5D §47, §114).
        """
        threshold = self.traceThreshold
        needle = self._species_filter.strip().lower()
        key = "mole_fraction" if self._composition_basis == "mole" else "mass_fraction"
        rows = []
        for row in self._species:
            if getattr(row, key) < threshold:
                continue
            if needle and needle not in row.name.lower():
                continue
            rows.append(row)
        if self._composition_basis == "mass":
            rows.sort(key=lambda row: (-row.mass_fraction, row.name))
        return rows

    def _rebuild_composition(self) -> None:
        visible = self._visible_species()
        rows = [(row.label, row.phase, row.mole_fraction, row.mass_fraction)
                for row in visible]
        kinds = ["condensed" if row.is_condensed else "" for row in visible]
        labels = ["CONDENSED" if row.is_condensed else "" for row in visible]
        self._composition_model.set_table(_COMPOSITION_COLUMNS, rows,
                                          kinds=kinds, labels=labels)
        self._composition_model.setPrecision(self._precision)

    @Property("QVariantList", notify=compositionChanged)
    def condensedRows(self):
        """Indices of the condensed species **in the current view**.

        The table marks them through the same gutter mechanism the compressible
        tables use for the sonic line, so a condensed species is annotated
        rather than merely typed as "solid" in a column. Recomputed with the
        view, because a display filter changes which row is which.
        """
        return [index for index, row in enumerate(self._visible_species())
                if row.is_condensed]

    @Property(int, notify=compositionChanged)
    def speciesTotal(self) -> int:
        return len(self._species)

    @Property(int, notify=compositionChanged)
    def speciesShown(self) -> int:
        return self._composition_model.rowCount()

    @Property(int, notify=compositionChanged)
    def speciesHidden(self) -> int:
        return max(0, len(self._species) - self._composition_model.rowCount())

    @Property(str, notify=compositionChanged)
    def hiddenSummary(self) -> str:
        """How much was hidden, and how much of the mixture it accounts for.

        Truncation is declared with both numbers, never silently (``09`` §5.2).
        """
        hidden = self.speciesHidden
        if not hidden:
            return ""
        visible = {row.name for row in self._visible_species()}
        key = "mole_fraction" if self._composition_basis == "mole" else "mass_fraction"
        total = math.fsum(getattr(row, key) for row in self._species
                          if row.name not in visible)
        basis = "X" if self._composition_basis == "mole" else "Y"
        return (f"{hidden} species hidden by the display threshold, "
                f"Σ{basis} = {total:.3e}. They remain in the result.")

    @Property(str, notify=compositionChanged)
    def compositionSums(self) -> str:
        if not self._species:
            return ""
        mole = math.fsum(row.mole_fraction for row in self._species)
        mass = math.fsum(row.mass_fraction for row in self._species)
        return f"ΣX = {mole:.9f}   ΣY = {mass:.9f}   over all {len(self._species)} species"

    # -- condensed ------------------------------------------------------

    @Property("QVariantMap", notify=compositionChanged)
    def condensed(self):
        """What the result says about condensed products, in four states.

        Never derived from a count of candidate condensed species: the
        canonical production case has candidates in its product set and
        6.24e-08 of mass actually present (Phase 5D §4, §51, §52).

        The two "not present" states are kept apart. A measured 6.24e-08 is not
        zero, so it is reported as *below the reporting threshold* -- with both
        the exact fraction and the threshold -- rather than as none.

        ``species`` lists the condensed species the composition actually
        contains, in every known state; ``state`` is what says whether they are
        present or merely below the level this workspace reports.
        """
        summary = condensed_summary(self._outcome, self._species)
        fraction = summary["fraction"]
        return {
            "state": summary["state"],
            "known": bool(summary["known"]),
            "present": bool(summary["present"]),
            "fraction": float("nan") if fraction is None else float(fraction),
            "fractionText": (EM_DASH if fraction is None
                             else format_engineering(fraction, self._precision)),
            "threshold": float(summary["threshold"]),
            "thresholdText": f"{summary['threshold']:.0e}",
            "headline": summary["headline"],
            "detail": summary["detail"],
            "species": [row.name for row in summary["species"]],
        }

    @Property("QVariantMap", notify=compositionChanged)
    def leadingSpecies(self):
        """The few species that make up most of the solved mixture.

        Taken from the full solved set in the service's own order -- mole
        fraction, descending (``species_rows``) -- and independent of the
        Composition view's threshold, filter and basis, which are display
        settings of another view. No fraction is recomputed; the only
        arithmetic is the sum of the fractions shown, which says how much of
        the mixture the short list accounts for.
        """
        leaders = list(self._species[:LEADING_SPECIES])
        if not leaders:
            return {"rows": [], "shown": 0, "total": 0, "sumText": ""}
        share = math.fsum(row.mole_fraction for row in leaders)
        return {
            "rows": [{"name": row.name, "label": row.label, "phase": row.phase,
                      "condensed": row.is_condensed,
                      "fraction": float(row.mole_fraction),
                      "text": format_engineering(row.mole_fraction, self._precision)}
                     for row in leaders],
            "shown": len(leaders),
            "total": len(self._species),
            "sumText": format_engineering(share, self._precision),
        }

    @Slot(result=str)
    def copyComposition(self) -> str:
        """Copy the visible composition table as tab-separated text.

        For a person, not a program: species in chemical notation ("HCl",
        "MgCl2") as the table shows them, and every number exactly as the
        table displays it at the current precision. The provider's own
        identifiers ("HCL", "MgCL2") are what the composition is keyed by; no
        machine export of this table exists, so no identifier-keyed export
        changed when the labels did.
        """
        text = self._composition_model.tableAsText()
        self._copy(text)
        return text

    # ==================================================================
    # sweep
    # ==================================================================

    @Property(float, notify=sweepInputsChanged)
    def sweepStart(self) -> float:
        return self._sweep_start

    @sweepStart.setter
    def sweepStart(self, value: float) -> None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return
        if number == self._sweep_start:
            return
        self._sweep_start = number
        self._on_sweep_input_changed()

    @Property(float, notify=sweepInputsChanged)
    def sweepEnd(self) -> float:
        return self._sweep_end

    @sweepEnd.setter
    def sweepEnd(self, value: float) -> None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return
        if number == self._sweep_end:
            return
        self._sweep_end = number
        self._on_sweep_input_changed()

    @Property(int, notify=sweepInputsChanged)
    def sweepPoints(self) -> int:
        return self._sweep_points

    @sweepPoints.setter
    def sweepPoints(self, value: int) -> None:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return
        if number == self._sweep_points:
            return
        self._sweep_points = number
        self._on_sweep_input_changed()

    @Property(int, constant=True)
    def maxSweepPoints(self) -> int:
        return sweep.MAX_SWEEP_POINTS

    def _on_sweep_input_changed(self) -> None:
        self._sweep_message = self._validate_sweep()
        if self._sweep_result is not None:
            self._sweep_stale = True
        self.sweepInputsChanged.emit()
        self.sweepChanged.emit()

    def _validate_sweep(self) -> str:
        try:
            sweep.validate_range(self._sweep_start, self._sweep_end,
                                 self._sweep_points)
        except sweep.SweepRangeError as error:
            return str(error)
        return ""

    @Property(bool, notify=sweepInputsChanged)
    def sweepRangeValid(self) -> bool:
        return self._validate_sweep() == ""

    @Property(str, notify=sweepInputsChanged)
    def sweepRangeMessage(self) -> str:
        return self._sweep_message or self._validate_sweep()

    @Property(float, notify=sweepInputsChanged)
    def sweepStep(self) -> float:
        if self._sweep_points < 2 or self._sweep_end <= self._sweep_start:
            return float("nan")
        return (self._sweep_end - self._sweep_start) / (self._sweep_points - 1)

    @Property("QVariantList", notify=sweepChanged)
    def sweepFixedConditions(self):
        """Everything the sweep holds constant, from the sweep's own case.

        Shown beside the charts, because a trend is meaningless without the
        conditions it was taken under (Phase 5D §56, §79).
        """
        result = self._sweep_result
        case = result.case if result is not None else self._case
        factor = self._pressure_factor()
        return [
            {"label": "Fuel", "value": case.fuel},
            {"label": "Oxidiser", "value": case.oxidiser},
            {"label": "Fuel temperature", "value": f"{case.fuel_temperature:g} K"},
            {"label": "Oxidiser temperature",
             "value": f"{case.oxidiser_temperature:g} K"},
            {"label": "Chamber pressure",
             "value": f"{case.chamber_pressure / factor:g} {self._pressure_unit}"},
            {"label": "Provider", "value": PROVIDER_LABEL},
            {"label": "Model", "value": MODEL_SUMMARY},
        ]

    @Slot()
    def runSweep(self) -> None:
        """Run the sweep. Explicit, never on a keystroke (Phase 5D §140)."""
        if self._busy:
            return
        message = self._validate_sweep()
        if message:
            self._sweep_message = message
            self.sweepInputsChanged.emit()
            return
        self._set_busy(True)
        try:
            span = sweep.SweepRange(self._sweep_start, self._sweep_end,
                                    self._sweep_points)
            result = sweep.run_sweep(self._case, span)
        finally:
            self._set_busy(False)
        self._adopt_sweep(result)

    def _adopt_sweep(self, result: sweep.SweepResult) -> None:
        self._sweep_result = result
        self._sweep_stale = False
        self._sweep_message = ""

        self._sweep_model.set_table(
            sweep.sweep_columns(), sweep.sweep_rows(result),
            kinds=["failed" if not point.ok
                   else ("warning" if point.warned else "")
                   for point in result.points],
            labels=["NO SOLUTION" if not point.ok else ""
                    for point in result.points])
        self._sweep_model.setPrecision(self._precision)

        # Chart series are computed once, here, rather than on every repaint.
        self._sweep_series = {
            entry["key"]: self._segments(sweep.series_for(result, entry["key"]))
            for entry in sweep.SWEEP_QUANTITIES
        }
        self._sweep_species_options = sweep.species_in_sweep(result)
        if not self._sweep_species:
            self._sweep_species = list(self._sweep_species_options[:5])
        self._rebuild_species_series()
        self.sweepChanged.emit()

    @staticmethod
    def _segments(segments) -> list:
        return [[dict(point) for point in segment] for segment in segments]

    def _clear_sweep(self) -> None:
        self._sweep_result = None
        self._sweep_stale = False
        self._sweep_model.clear()
        self._sweep_series = {}
        self._sweep_species_options = ()
        self._sweep_species_series = []
        self.sweepChanged.emit()

    @Slot()
    def clearSweep(self) -> None:
        self._clear_sweep()

    @Property(bool, notify=sweepChanged)
    def hasSweep(self) -> bool:
        return self._sweep_result is not None

    @Property(bool, notify=sweepChanged)
    def sweepStale(self) -> bool:
        return self._sweep_stale

    @Property(int, notify=sweepChanged)
    def sweepSolvedCount(self) -> int:
        return 0 if self._sweep_result is None else self._sweep_result.solved_count

    @Property(int, notify=sweepChanged)
    def sweepFailedCount(self) -> int:
        return 0 if self._sweep_result is None else self._sweep_result.failed_count

    @Property(float, notify=sweepChanged)
    def sweepElapsedMs(self) -> float:
        if self._sweep_result is None:
            return float("nan")
        return self._sweep_result.elapsed_seconds * 1000.0

    @Property(QObject, constant=True)
    def sweepModel(self) -> QObject:
        return self._sweep_model

    @Property("QVariantList", constant=True)
    def sweepColumns(self):
        return [dict(column) for column in sweep.sweep_columns()]

    @Property("QVariantList", notify=sweepChanged)
    def sweepWarnings(self):
        """One row per distinct warning, with the points it covers.

        Forty-one identical assigned-enthalpy rows would bury everything else,
        so repeated provider warnings are aggregated. The per-point diagnostics
        are unchanged and remain reachable through point inspection (§78).
        """
        if self._sweep_result is None:
            return []
        return [dict(entry) for entry in sweep.aggregated_warnings(self._sweep_result)]

    @Property("QVariantList", notify=sweepChanged)
    def sweepFailedRows(self):
        """Row indices of the points that produced no state."""
        if self._sweep_result is None:
            return []
        return [index for index, point in enumerate(self._sweep_result.points)
                if not point.ok]

    @Property("QVariantList", notify=sweepChanged)
    def sweepFailedRatios(self):
        """The O/F values that produced no state, for marking on a chart."""
        if self._sweep_result is None:
            return []
        return [{"value": point.oxidiser_fuel_ratio, "axis": "x",
                 "label": "no solution"}
                for point in self._sweep_result.failed]

    @Slot(str, result="QVariantList")
    def sweepSeries(self, key: str):
        """Segments for one quantity. Each segment is drawn as its own line."""
        return self._sweep_series.get(str(key), [])

    @Slot(str, result="QVariantMap")
    def sweepAxis(self, key: str):
        meta = sweep.quantity_meta(str(key))
        label = meta["label"]
        if meta["unit"]:
            label = f"{label}  [{meta['unit']}]"
        return {"label": label, "unit": meta["unit"],
                "qualifier": meta["qualifier"], "raw": meta["label"]}

    @Slot(str, result="QVariantMap")
    def sweepMaximum(self, key: str):
        """The largest sampled value, labelled as a sampled maximum.

        Not an optimum. Phase 5B-0 measured different quantities peaking at
        different O/F, so a peak in one response says nothing about a design
        (Phase 5D §12, §77).
        """
        if self._sweep_result is None:
            return {}
        best = sweep.maximum_in_range(self._sweep_result, str(key))
        if best is None:
            return {}
        meta = sweep.quantity_meta(str(key))
        return {
            "of": best["of"],
            "value": best["value"],
            "text": f"Maximum {meta['label']} in sweep: "
                    f"{format_engineering(best['value'], self._precision)}"
                    f"{(' ' + meta['unit']) if meta['unit'] else ''} "
                    f"at O/F {best['of']:g}",
        }

    # -- species series --------------------------------------------------

    @Property("QVariantList", notify=sweepChanged)
    def sweepSpeciesOptions(self):
        return list(self._sweep_species_options)

    @Property("QVariantList", notify=sweepChanged)
    def sweepSpecies(self):
        return list(self._sweep_species)

    @Property(str, notify=sweepChanged)
    def sweepSpeciesBasis(self) -> str:
        return self._sweep_species_basis

    @sweepSpeciesBasis.setter
    def sweepSpeciesBasis(self, value: str) -> None:
        if value not in ("mole", "mass") or value == self._sweep_species_basis:
            return
        self._sweep_species_basis = str(value)
        self._rebuild_species_series()
        self.sweepChanged.emit()

    @Slot(str)
    def toggleSweepSpecies(self, name: str) -> None:
        """Add or remove one species from the plotted set.

        Refuses to add beyond :data:`MAX_SWEEP_SPECIES` -- a drawing limit, not
        a data limit. Nothing is removed from the sweep result (§69).
        """
        name = str(name)
        if name in self._sweep_species:
            self._sweep_species.remove(name)
        elif len(self._sweep_species) < MAX_SWEEP_SPECIES:
            self._sweep_species.append(name)
        else:
            return
        self._rebuild_species_series()
        self.sweepChanged.emit()

    def _rebuild_species_series(self) -> None:
        result = self._sweep_result
        if result is None:
            self._sweep_species_series = []
            return
        self._sweep_species_series = [
            {"name": name,
             "segments": self._segments(
                 sweep.species_series_for(result, name,
                                          self._sweep_species_basis))}
            for name in self._sweep_species
        ]

    @Property("QVariantList", notify=sweepChanged)
    def sweepSpeciesSeries(self):
        return list(self._sweep_species_series)

    @Property(str, notify=sweepChanged)
    def sweepSpeciesAxis(self) -> str:
        return ("Mole fraction  X" if self._sweep_species_basis == "mole"
                else "Mass fraction  Y")

    # -- point inspection -------------------------------------------------

    @Slot(int, result="QVariantMap")
    def sweepPoint(self, row: int):
        """One sweep point, for hover or row selection.

        Carries no performance quantity. There is no c*, no Cf and no Isp in a
        Phase 5D sweep point, because RocketForge owns none of them (§72).
        """
        result = self._sweep_result
        if result is None or not (0 <= row < len(result.points)):
            return {}
        point = result.points[row]
        outcome = point.outcome
        return {
            "row": row,
            "of": point.oxidiser_fuel_ratio,
            "ok": point.ok,
            "status": outcome.status_label,
            "tone": outcome.status_tone,
            "message": outcome.message,
            "warned": point.warned,
            "temperature": point.value_of("temperature"),
            "molarMass": point.value_of("molar_mass"),
            "gamma": point.value_of("gamma"),
            "density": point.value_of("density"),
            "diagnostics": [self._diagnostic_dict(entry)
                            for entry in diagnostic_rows(outcome,
                                                         include_info=False)],
        }

    @Property(QObject, constant=True)
    def sweepSelection(self) -> QObject:
        return self._sweep_selection

    @Slot(int)
    def selectSweepPoint(self, row: int) -> None:
        """Select a solved (or failed) sweep point by its row."""
        result = self._sweep_result
        if result is None or not (0 <= row < len(result.points)):
            return
        ratio = result.points[row].oxidiser_fuel_ratio
        self._sweep_selection.select("tableRow", str(row), float(ratio),
                                     f"O/F {ratio:.4g}", "sweep")

    @Slot(float)
    def selectSweepNear(self, ratio: float) -> None:
        """Select the swept point whose O/F is nearest ``ratio`` (a real sample)."""
        result = self._sweep_result
        if result is None or not result.points or not math.isfinite(ratio):
            return
        row = min(range(len(result.points)),
                  key=lambda i: abs(result.points[i].oxidiser_fuel_ratio - ratio))
        self.selectSweepPoint(row)

    @Slot(result=str)
    def copySweep(self) -> str:
        text = self._sweep_model.tableAsText()
        self._copy(text)
        return text

    # ==================================================================
    # references
    # ==================================================================

    def _reference(self):
        if self._reference_case is None:
            self._reference_case = reference.reference_case()
        return self._reference_case

    @Property(str, notify=referenceChanged)
    def referenceTitle(self) -> str:
        return self._reference().title

    @Property(str, notify=referenceChanged)
    def referenceLevel(self) -> str:
        case = self._reference()
        return f"Level {case.level} — {case.level_name}" if case.level else case.level_name

    @Property(str, notify=referenceChanged)
    def referenceCitation(self) -> str:
        return self._reference().citation

    @Property("QVariantList", notify=referenceChanged)
    def referenceSourceRows(self):
        return [dict(row) for row in reference.source_rows(self._reference())]

    @Property("QVariantList", notify=referenceChanged)
    def referenceNotCompared(self):
        """What the source publishes that this workspace deliberately omits.

        Stated rather than silently dropped: the source carries c*, Isp and an
        exit gamma, RocketForge owns none of them yet, and the dataset records
        no value for any of them (Phase 5D §84, §171).
        """
        return [dict(entry) for entry in self._reference().not_compared]

    @Property(bool, notify=referenceChanged)
    def referenceHasRun(self) -> bool:
        return self._reference_outcome is not None

    @Property(str, notify=referenceChanged)
    def referenceVerdict(self) -> str:
        return reference.overall_verdict(self._reference_rows)

    @Property(str, notify=referenceChanged)
    def referenceStatusMessage(self) -> str:
        outcome = self._reference_outcome
        return "" if outcome is None else outcome.message

    @Property("QVariantList", notify=referenceChanged)
    def referenceRows(self):
        return [
            {
                "key": row.key,
                "label": row.label,
                "published": format_engineering(row.published, self._precision),
                "computed": (format_engineering(row.computed, self._precision)
                             if row.computed is not None else EM_DASH),
                "unit": row.unit,
                "difference": (f"{row.relative_difference:.3e}"
                               if math.isfinite(row.relative_difference)
                               else EM_DASH),
                "tolerance": f"{row.tolerance:.3e}",
                "verdict": row.verdict,
                "passed": row.passed,
            }
            for row in self._reference_rows
        ]

    @Slot()
    def runReference(self) -> None:
        """Solve the stored reference case exactly as published.

        The conditions come from the shipped dataset, never from the Calculator
        form, so nothing the user typed can masquerade as the reference case
        (Phase 5D §87).
        """
        case = self._reference()
        outcome = reference.run_reference(case)
        self._reference_outcome = outcome
        self._reference_rows = reference.compare(case, outcome)
        self.referenceChanged.emit()

    # ==================================================================
    # shared
    # ==================================================================

    def _copy(self, text: str) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)
