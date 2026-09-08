"""The NASA CEA v3 thermochemistry provider.

Implements the Phase 5B ``ThermochemistryProvider`` protocol structurally --
no inheritance, no registration. Nothing here is imported by
``physics.thermochemistry``; the arrow points from this adapter down to the
abstraction, and never back.

The pipeline, in order, and the order is the point:

    validated RocketForge request      (the request validated itself)
        -> provider-specific mapping   (CEA names, field width, T ranges)
        -> CEA solve
        -> raw snapshot                (values copied out immediately)
        -> unit conversion             (once, in units.py)
        -> RocketForge ChamberGas
        -> scientific post-validation  (element balance, state identities)
        -> Solution[ChamberGas]

A result that CEA reports as converged is still rejected if it fails element
conservation. "The solver said it converged" is not the same claim as "the
answer conserves atoms", and only the second one is checkable here.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from types import ModuleType

from rocketforge.core.result import Diagnostic, Severity, Solution, Status
from rocketforge.physics.thermochemistry import (
    DEFAULT_THERMO_TOLERANCES,
    ChamberEquilibriumRequest,
    ChamberGas,
    ChemistryMode,
    Composition,
    CompositionBasis,
    ElementalInventoryBasis,
    EquilibriumConstraint,
    ExpansionMode,
    ProviderCapabilities,
    ProviderCapability,
    Species,
    ThermochemistryProvenance,
    ThermochemistryTolerances,
    check_element_balance,
    validate_chamber_gas,
)

from .availability import CEAAvailability, check_availability, load_cea
from .errors import CEAMappingError
from .enthalpy_coupling import (
    CEA_REFERENCE_PRESSURE,
    ReactantEnthalpyCorrection,
    ReactantEnthalpyPolicy,
    ReactantFluidBinding,
    mixture_enthalpy_correction,
    reactant_mass_fractions,
    sensible_enthalpy_increment,
)
from .mapping import (
    CEAChamberInput,
    CEARawChamberResult,
    assigned_enthalpy_temperature,
    build_chamber_input,
    solve_chamber_raw,
    to_chamber_gas,
)
from .naming import PROVIDER_ID
from .oracle import run_rocket_oracle
from .resources import CEAResources, discover_resources
from .species import build_species_table, cea_molar_masses

__all__ = ["CEAThermochemistryProvider", "CEA_CAPABILITIES", "PROVIDER_VERSION"]

#: This adapter's own version, distinct from the ``cea`` distribution's.
PROVIDER_VERSION = "1.0-phase5c"

#: What NASA CEA declares it can do.
#:
#: Every entry is something Phase 5B-0 or Phase 5C exercised against the real
#: library. ``KINETICS`` is absent because CEA is an equilibrium code and
#: claiming it would be a lie that a capability check could not catch.
#: ``ROCKET_PERFORMANCE`` is present -- CEA genuinely returns c*, Cf and Isp --
#: and declaring it does **not** move ownership of rocket performance out of
#: ``engineering.nozzle``; it says oracle values can be had.
CEA_CAPABILITIES = ProviderCapabilities(
    supported=frozenset({
        ProviderCapability.HP_EQUILIBRIUM,
        ProviderCapability.SP_EQUILIBRIUM,
        ProviderCapability.COMPOSITION,
        ProviderCapability.CONDENSED_PHASES,
        ProviderCapability.CONDENSED_PHASE_REPORTING,
        ProviderCapability.LIQUID_REACTANTS,
        ProviderCapability.CUSTOM_REACTANT_TEMPERATURE,
        ProviderCapability.CUSTOM_REACTANTS,
        ProviderCapability.CUSTOM_SPECIES_SET,
        ProviderCapability.EQUILIBRIUM_EXPANSION,
        ProviderCapability.FROZEN_EXPANSION,
        ProviderCapability.FREEZE_LOCATION_CONTROL,
        ProviderCapability.PRESSURE_RATIO_EXPANSION,
        ProviderCapability.AREA_RATIO_EXPANSION,
        ProviderCapability.NATIVE_EQUILIBRIUM_GAMMA,
        ProviderCapability.ROCKET_PERFORMANCE,
        ProviderCapability.TRANSPORT_PROPERTIES,
        ProviderCapability.IONISED_SPECIES,
    }),
    # Validated ranges, deliberately conservative and stated rather than
    # tolerated: a request outside them is refused with the range named.
    pressure_range=(1.0e3, 1.0e9),
    mixture_ratio_range=(0.01, 100.0),
    temperature_ceiling=20000.0,
)

#: Tolerances for validating a *provider's* output.
#:
#: Both relaxations are measured, and both are named categories rather than a
#: loosening of RocketForge's own strict values:
#:
#: * identity checks run at ``provider_identity_rel_tol`` (1e-5) because CEA
#:   computed cp, cv and density on its own pre-2019 gas constant, a 5.7e-06
#:   difference from CODATA;
#: * element conservation runs at ``provider_element_balance_rel_tol`` (1e-6)
#:   because CEA's own equilibrium solver leaves a residual reaching 1.9e-08
#:   across the measured operating range, worst at fuel-rich conditions.
#:
#: The strict values remain in force for RocketForge's own arithmetic, and the
#: mutation proofs in ``tests/providers/cea/`` show that a real defect still
#: fails at these looser settings by orders of magnitude.
_PROVIDER_TOLERANCES: ThermochemistryTolerances = ThermochemistryTolerances(
    state_identity_rel_tol=DEFAULT_THERMO_TOLERANCES.provider_identity_rel_tol,
    element_balance_rel_tol=DEFAULT_THERMO_TOLERANCES.provider_element_balance_rel_tol,
)


class CEAThermochemistryProvider:
    """RocketForge's adapter onto NASA CEA v3.

    Construct once and reuse: the CEA module is imported lazily on first use
    and the species tables are cached per product set, so repeated solves do
    not re-read the thermodynamic database. Phase 5B-0 measured a warm chamber
    solve at 44 microseconds against 0.216 ms for a cold setup, which is the
    whole reason reuse is worth having.

    Concurrency policy: **serial, in-process**. Phase 5B-0 measured four
    threads running roughly 0.85x of serial -- slower, not faster -- so there
    is nothing to gain and a shared native library to lose. No lock is added
    either, because no cross-request contamination was observed in the
    A/B/A/B/A leakage tests and a lock with no evidence behind it is
    superstition.
    """

    provider_id: str = PROVIDER_ID
    version: str = PROVIDER_VERSION
    capabilities: ProviderCapabilities = CEA_CAPABILITIES

    def __init__(self, *, tolerances: ThermochemistryTolerances | None = None) -> None:
        self._module: ModuleType | None = None
        self._resources: CEAResources | None = None
        self._availability: CEAAvailability | None = None
        self._species_cache: dict[tuple[str, ...], dict[str, Species]] = {}
        self._assigned_enthalpy: dict[str, float | None] = {}
        self._tolerances = tolerances or _PROVIDER_TOLERANCES

    # -- availability ------------------------------------------------------

    @property
    def availability(self) -> CEAAvailability:
        """Whether CEA can be used, cached after the first check."""
        if self._availability is None:
            self._availability = check_availability()
        return self._availability

    @property
    def is_available(self) -> bool:
        return self.availability.is_usable

    def _cea(self) -> ModuleType:
        if self._module is None:
            self._module = load_cea()
            self._resources = discover_resources(self._module)
        return self._module

    def resources(self) -> CEAResources:
        """The data files CEA is actually using. Imports CEA if needed."""
        self._cea()
        assert self._resources is not None
        return self._resources

    # -- provenance --------------------------------------------------------

    def provenance(self,
                   species_set: tuple[str, ...] = (),
                   reactant_conditions: dict[str, float] | None = None,
                   enthalpy_policy: ReactantEnthalpyPolicy =
                       ReactantEnthalpyPolicy.PROVIDER_NATIVE,
                   corrections: tuple[ReactantEnthalpyCorrection, ...] = (),
                   ) -> ThermochemistryProvenance:
        """Who computed a result, against which database, in which mode.

        Available before anything is solved, so an interface can show what is
        installed without computing. The database hash identifies the file the
        solve will actually use -- in a frozen bundle that is the bundled copy,
        because the path is derived from the imported module.
        """
        availability = self.availability
        resources = self.resources() if availability.is_usable else None
        return ThermochemistryProvenance(
            provider_id=self.provider_id,
            provider_version=self.version,
            library_version=availability.library_version or availability.version,
            database="thermo.lib",
            database_version=availability.version,
            database_sha256=resources.thermo_sha256 if resources else "",
            chemistry_mode=ChemistryMode.EQUILIBRIUM,
            equilibrium_constraint=EquilibriumConstraint.HP,
            species_set=tuple(species_set),
            reactant_conditions=dict(reactant_conditions or {}),
            options={
                "cea_gas_constant_J_per_kmolK": repr(
                    getattr(self._module, "R", "")) if self._module else "",
                "frozen_bundle": str(bool(resources.frozen)) if resources else "",
                "thermo_lib_path": resources.thermo_path if resources else "",
                # v1.1. Always recorded, under both policies, so that a result
                # can never be silent about which reactant-energy model made it.
                "reactant_enthalpy_policy": enthalpy_policy.value,
                "reactant_enthalpy_corrections": repr(
                    [c.as_mapping() for c in corrections]) if corrections else "",
                "cea_reference_pressure_Pa": repr(CEA_REFERENCE_PRESSURE)
                    if corrections else "",
            },
            warnings=(() if availability.is_validated
                      else (f"cea {availability.version} is not a validated "
                            f"version; {availability.detail}",)),
        )

    # -- species -----------------------------------------------------------

    def species_table(self, names: Iterable[str]) -> dict[str, Species]:
        """RocketForge :class:`Species` records for the named CEA species.

        Public because a caller holding a result needs them to do anything with
        its composition: converting mole fractions to mass fractions, or asking
        which entries are condensed, both require molar mass and phase, and
        ``ChamberGas`` carries a composition rather than a species table.

        Returns domain records only -- no CEA object crosses this boundary --
        and shares the provider's cache, so asking for a result's own species
        set costs nothing after the solve that produced it.
        """
        return dict(self._species_for(tuple(names)))

    def _species_for(self, product_species: tuple[str, ...],
                     extra: tuple[str, ...] = ()) -> dict[str, Species]:
        key = tuple(sorted(set(product_species) | set(extra)))
        cached = self._species_cache.get(key)
        if cached is None:
            resources = self.resources()
            cached = build_species_table(
                self._cea(), key,
                database="thermo.lib",
                database_version=resources.thermo_short)
            self._species_cache[key] = cached
        return cached

    # -- the native performance oracle -------------------------------------

    def rocket_oracle(
        self,
        request: ChamberEquilibriumRequest,
        *,
        area_ratio: float,
        expansion_mode: ExpansionMode = ExpansionMode.EQUILIBRIUM,
    ):
        """CEA's own rocket performance for this case. **An oracle, not a path.**

        NASA CEA computes c*, Cf and Isp itself, and this method returns those
        numbers. They exist to be *compared against*: RocketForge's performance
        is computed by ``rocketforge.engineering.nozzle`` from its own
        equations, and nothing in the production performance chain calls this.
        A result that assigned a value from here to a RocketForge performance
        field would be reporting CEA's answer under RocketForge's name.

        It is also a **separate CEA run** from ``solve_chamber``: a chamber
        state does not carry a performance figure, and this cannot be derived
        from one. Callers therefore invoke it explicitly rather than as a side
        effect of changing a nozzle input.

        Args:
            request: The same validated request ``solve_chamber`` takes, so the
                two runs are demonstrably the same case.
            area_ratio: Ae/At, supersonic.
            expansion_mode: How chemistry is treated through the nozzle.

        Returns:
            A :class:`CEARocketOracle` recording the values with the conditions
            that produced them.
        """
        if not isinstance(request, ChamberEquilibriumRequest):
            raise CEAMappingError(
                f"expected a ChamberEquilibriumRequest, got "
                f"{type(request).__name__}")

        molar_masses = self._blend_molar_masses(request)
        chamber_input = build_chamber_input(request, molar_masses=molar_masses)

        # The chamber input carries both weight vectors at full reactant
        # length with disjoint support; the oracle call wants each side's own
        # slots. Read the split from the support and check it rather than
        # assuming a layout: a silent mis-split would swap fuel and oxidiser,
        # which produces a plausible number for the wrong case.
        fuel_slots = tuple(index for index, weight
                           in enumerate(chamber_input.fuel_weights)
                           if weight != 0.0)
        oxidiser_slots = tuple(index for index, weight
                               in enumerate(chamber_input.oxidiser_weights)
                               if weight != 0.0)
        if not fuel_slots or not oxidiser_slots:
            raise CEAMappingError(
                "one side of the mixture carries no weight; the oracle call "
                "cannot be built from this mapping")
        if set(fuel_slots) & set(oxidiser_slots):
            raise CEAMappingError(
                "the fuel and oxidiser weight vectors overlap; the oracle "
                "call cannot be built from this mapping")
        if max(fuel_slots) > min(oxidiser_slots):
            raise CEAMappingError(
                "the reactant slots are not ordered fuel first; the oracle "
                "call cannot be built from this mapping")

        names = chamber_input.reactant_names
        temperatures = chamber_input.reactant_temperatures
        return run_rocket_oracle(
            self._cea(),
            fuel_names=tuple(names[i] for i in fuel_slots),
            oxidiser_names=tuple(names[i] for i in oxidiser_slots),
            fuel_weights=tuple(chamber_input.fuel_weights[i]
                               for i in fuel_slots),
            oxidiser_weights=tuple(chamber_input.oxidiser_weights[i]
                                   for i in oxidiser_slots),
            reactant_temperatures=tuple(
                temperatures[i] for i in fuel_slots + oxidiser_slots),
            of_ratio=chamber_input.of_ratio,
            chamber_pressure=float(request.chamber_pressure),
            area_ratio=float(area_ratio),
            product_species=chamber_input.product_species,
            expansion_mode=expansion_mode,
        )

    # -- the production operation -----------------------------------------

    def solve_chamber(
        self,
        request: ChamberEquilibriumRequest,
        *,
        enthalpy_policy: ReactantEnthalpyPolicy =
            ReactantEnthalpyPolicy.PROVIDER_NATIVE,
        fluid_provider: object | None = None,
        reactant_bindings: Mapping[str, ReactantFluidBinding] | None = None,
    ) -> Solution[ChamberGas]:
        """Solve a chamber equilibrium at constant enthalpy and pressure.

        Raises for a malformed request or a provider failure; reports
        non-convergence and failed post-validation through the returned
        ``Solution``. Those are three different things and stay that way.

        **NASA CEA Provider v1.1.** The three keyword arguments are additive
        and default to the v1.0 behaviour exactly: ``PROVIDER_NATIVE`` applies
        no correction, produces a zero-valued correction field, and reproduces
        every accepted Phase 5 result bit for bit. The policy that was used is
        recorded in provenance either way, so no result is ever silent about
        which model produced it.

        Under ``FLUID_SENSIBLE_CORRECTION`` a reactant whose CEA entry carries
        an *assigned* enthalpy -- one CEA does not vary with temperature --
        receives ``h_fluid(T, p) - h_fluid(T_ref, p_ref)`` from the supplied
        fluid provider. A reactant CEA already treats as temperature-dependent
        receives nothing, which is what stops the sensible term being counted
        twice.
        """
        if not isinstance(request, ChamberEquilibriumRequest):
            raise CEAMappingError(
                f"expected a ChamberEquilibriumRequest, got "
                f"{type(request).__name__}")

        self.capabilities.require(ProviderCapability.HP_EQUILIBRIUM,
                                  self.provider_id)
        self._check_declared_ranges(request)

        module = self._cea()

        # Blend components may need molar masses to convert a mole-basis blend
        # onto CEA's mass weights. Ask CEA for them, so the numbers are its own.
        molar_masses = self._blend_molar_masses(request)
        chamber_input = build_chamber_input(request, molar_masses=molar_masses)

        corrections: tuple[ReactantEnthalpyCorrection, ...] = ()
        if enthalpy_policy is ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION:
            corrections, chamber_input = self._apply_enthalpy_correction(
                chamber_input, fluid_provider, reactant_bindings)

        raw = solve_chamber_raw(module, chamber_input)

        species = self._species_for(chamber_input.product_species,
                                    chamber_input.reactant_names)
        provenance = self.provenance(
            species_set=chamber_input.product_species,
            reactant_conditions=request.reactant_conditions,
            enthalpy_policy=enthalpy_policy,
            corrections=corrections)

        diagnostics: list[Diagnostic] = list(
            self._assigned_enthalpy_diagnostics(chamber_input,
                                                corrections=corrections))
        if not raw.converged:
            return Solution(
                value=None, status=Status.NO_SOLUTION,
                diagnostics=(Diagnostic(
                    code="PROVIDER_NOT_CONVERGED", severity=Severity.ERROR,
                    message="NASA CEA did not converge for this chamber "
                            "equilibrium; no state is returned.",
                    field="converged"),),
                provenance=(provenance,))

        state = to_chamber_gas(raw, species, request, provenance)
        diagnostics.extend(self._post_validate(raw, state, species, request))

        status = Status.OK
        if any(d.severity is Severity.ERROR for d in diagnostics):
            # CEA said it converged, but the answer does not survive checking.
            # That is a no-solution for RocketForge's purposes, and the
            # diagnostics say exactly which check failed rather than
            # "chemistry failed".
            return Solution(value=None, status=Status.NO_SOLUTION,
                            diagnostics=tuple(diagnostics),
                            provenance=(provenance,))
        if any(d.severity is Severity.WARNING for d in diagnostics):
            status = Status.OK_WITH_WARNINGS

        return Solution(value=state, status=status,
                        diagnostics=tuple(diagnostics),
                        provenance=(provenance,))

    # -- internals ---------------------------------------------------------

    def _check_declared_ranges(self, request: ChamberEquilibriumRequest) -> None:
        from .errors import out_of_range
        caps = self.capabilities
        if not caps.pressure_is_in_range(request.chamber_pressure):
            low, high = caps.pressure_range or (0.0, 0.0)
            raise out_of_range("chamber pressure", float(request.chamber_pressure),
                               low, high)
        if not caps.mixture_ratio_is_in_range(request.of_mass):
            low, high = caps.mixture_ratio_range or (0.0, 0.0)
            raise out_of_range("O/F", float(request.of_mass), low, high)

    def _apply_enthalpy_correction(
        self,
        chamber_input: CEAChamberInput,
        fluid_provider: object | None,
        reactant_bindings: Mapping[str, ReactantFluidBinding] | None,
    ) -> tuple[tuple[ReactantEnthalpyCorrection, ...], CEAChamberInput]:
        """Build the sensible correction for every assigned-enthalpy reactant.

        Only assigned-enthalpy reactants are touched. For everything else CEA
        already evaluates the enthalpy at the temperature it was given, and
        adding an increment there would count the same energy twice -- the
        single most dangerous mistake available in this whole coupling, and the
        reason the gate is the measured ``assigned_enthalpy_temperature`` rather
        than a list of names.
        """
        if fluid_provider is None:
            raise CEAMappingError(
                "the fluid sensible-enthalpy correction needs a fluid-property "
                "provider, and none was supplied. It is not defaulted: a "
                "silently chosen property model would change the chamber "
                "temperature without appearing anywhere in the request.")
        bindings = dict(reactant_bindings or {})
        if not bindings:
            raise CEAMappingError(
                "the fluid sensible-enthalpy correction needs a fluid binding "
                "for at least one reactant. A binding names the fluid and, "
                "crucially, the stream pressure -- which has no default.")

        module = self._cea()
        increments: list[float] = []
        corrections: list[ReactantEnthalpyCorrection] = []
        for name, temperature in zip(chamber_input.reactant_names,
                                     chamber_input.reactant_temperatures):
            if name not in self._assigned_enthalpy:
                self._assigned_enthalpy[name] = assigned_enthalpy_temperature(
                    module, name)
            assigned = self._assigned_enthalpy[name]
            binding = bindings.get(name)
            if assigned is None or binding is None:
                # Either CEA already varies this reactant with temperature, or
                # no validated fluid stands behind it. Both mean: change nothing.
                increments.append(0.0)
                continue
            correction = sensible_enthalpy_increment(
                fluid_provider, binding, name, float(temperature),
                float(assigned))
            corrections.append(correction)
            increments.append(correction.delta_h)

        fractions = reactant_mass_fractions(
            chamber_input.fuel_weights, chamber_input.oxidiser_weights,
            chamber_input.of_ratio)
        delta = mixture_enthalpy_correction(fractions, tuple(increments))
        return tuple(corrections), replace(chamber_input,
                                           enthalpy_correction=delta)

    def _assigned_enthalpy_diagnostics(
            self, chamber_input: CEAChamberInput,
            corrections: tuple[ReactantEnthalpyCorrection, ...] = (),
            ) -> list[Diagnostic]:
        """Warn when a reactant temperature cannot affect the answer.

        Several of NASA CEA's reactant entries -- the cryogenic liquids among
        them -- carry a single assigned enthalpy at one reference condition
        instead of a temperature-dependent fit. CEA accepts a different
        temperature for those and then ignores it, so a caller who sets liquid
        oxygen to 95 K silently receives the 90.17 K answer.

        RocketForge does not silently pass that on. The request is still
        honoured, the value is still within the range CEA declares, and the
        result is still correct *for the reactant CEA modelled* -- but the
        caller is told that the temperature they set did not enter the
        calculation. Reported as a warning rather than a refusal because the
        answer is usable and the limitation belongs to the provider's data.
        """
        module = self._cea()
        corrected = {c.reactant_name: c for c in corrections}
        found: list[Diagnostic] = []
        for name, temperature in zip(chamber_input.reactant_names,
                                     chamber_input.reactant_temperatures):
            if name not in self._assigned_enthalpy:
                self._assigned_enthalpy[name] = assigned_enthalpy_temperature(
                    module, name)
            assigned = self._assigned_enthalpy[name]
            if assigned is None:
                continue
            if name in corrected:
                # v1.1: the limitation was corrected rather than merely
                # reported, so the warning is superseded by a record of what
                # was done. It is replaced, never quietly dropped.
                correction = corrected[name]
                found.append(Diagnostic(
                    code="REACTANT_ENTHALPY_FLUID_CORRECTED",
                    severity=Severity.INFO,
                    message=(
                        f"NASA CEA models reactant {name!r} with an assigned "
                        f"enthalpy at {assigned} K. The stream temperature of "
                        f"{temperature} K was represented by adding a sensible "
                        f"enthalpy increment of {correction.delta_h:.6g} J/kg "
                        f"from {correction.provider_label}, evaluated at "
                        f"{correction.requested_pressure} Pa. CEA keeps "
                        "ownership of the chemical reference; only the "
                        "difference between two states of the same fluid was "
                        "supplied."),
                    field="reactant_temperature",
                    detail=dict(correction.as_mapping())))
                continue
            if abs(temperature - assigned) <= 1.0e-9:
                continue
            found.append(Diagnostic(
                code="PROVIDER_ASSIGNED_ENTHALPY_REACTANT",
                severity=Severity.WARNING,
                message=(
                    f"NASA CEA models reactant {name!r} with an assigned "
                    f"enthalpy at {assigned} K, not a temperature-dependent "
                    f"fit. The stream temperature of {temperature} K was "
                    "accepted and did not affect the result; the chamber state "
                    f"is the one for {name!r} at {assigned} K."),
                field="reactant_temperature",
                detail={"requested": float(temperature),
                        "assigned": float(assigned)}))
        return found

    def _blend_molar_masses(self,
                            request: ChamberEquilibriumRequest) -> dict[str, float]:
        """Molar masses for any mole-basis blend components, from CEA."""
        needed: set[str] = set()
        for stream in (request.fuel, request.oxidiser):
            composition = stream.propellant.composition
            if (len(composition.entries) > 1
                    and composition.basis is CompositionBasis.MOLE_FRACTION):
                needed.update(name for name, _ in composition.entries)
        if not needed:
            return {}
        raw = cea_molar_masses(self._cea(), tuple(sorted(needed)))
        from .units import molar_mass_to_si
        return {name: molar_mass_to_si(value) for name, value in raw.items()}

    def _post_validate(
        self,
        raw: CEARawChamberResult,
        state: ChamberGas,
        species: dict[str, Species],
        request: ChamberEquilibriumRequest,
    ) -> list[Diagnostic]:
        """Check the answer before returning it.

        Reports the raw composition sum *before* canonicalisation, checks
        element conservation between the reactants as supplied and the products
        as returned, and runs the state identities at provider tolerance.
        """
        diagnostics: list[Diagnostic] = []

        # Raw composition sum, measured before the domain canonicalised it.
        sum_error = abs(raw.raw_mole_fraction_sum - 1.0)
        if sum_error > self._tolerances.composition_sum_tol:
            diagnostics.append(Diagnostic(
                code="PROVIDER_COMPOSITION_SUM", severity=Severity.ERROR,
                message=f"NASA CEA returned mole fractions summing to "
                        f"{raw.raw_mole_fraction_sum!r}, off unity by "
                        f"{sum_error:.3e}",
                field="composition",
                detail={"raw_sum": raw.raw_mole_fraction_sum,
                        "deviation": sum_error}))
        elif sum_error > 0.0:
            diagnostics.append(Diagnostic(
                code="COMPOSITION_CANONICALISED", severity=Severity.INFO,
                message=f"provider mole fractions summed to "
                        f"{raw.raw_mole_fraction_sum!r}; canonicalised to 1",
                field="composition",
                detail={"raw_sum": raw.raw_mole_fraction_sum}))

        # Element conservation: reactants as supplied against products as
        # returned. Provider-independent, reference-free, and blocking.
        balance = self._element_balance(state, species, request)
        if balance is not None:
            diagnostics.append(balance.to_diagnostic() if balance.passed
                               else Diagnostic(
                                   code="ELEMENT_BALANCE_VIOLATED",
                                   severity=Severity.ERROR,
                                   message=(
                                       "NASA CEA reported convergence, but the "
                                       "products do not conserve the reactants' "
                                       f"atoms: residual {balance.residual:.3e} "
                                       f"exceeds {balance.tolerance:.3e} "
                                       f"({balance.detail})"),
                                   field="element conservation",
                                   detail={"residual": balance.residual,
                                           "tolerance": balance.tolerance}))

        report = validate_chamber_gas(state, species,
                                      tolerances=self._tolerances,
                                      require_provenance=True)
        for check in report.checks:
            if check.applicable and not check.passed:
                diagnostics.append(check.to_diagnostic())

        if raw.num_condensed_candidates > 0:
            present = state.condensed_mass_fraction or 0.0
            diagnostics.append(Diagnostic(
                code="CONDENSED_CANDIDATES", severity=Severity.INFO,
                message=(f"{raw.num_condensed_candidates} condensed species "
                         f"were candidates; mass fraction actually present is "
                         f"{present:.6e}"),
                field="condensed_mass_fraction",
                detail={"candidates": float(raw.num_condensed_candidates),
                        "present": present}))
        return diagnostics

    def _element_balance(self, state: ChamberGas, species: dict[str, Species],
                         request: ChamberEquilibriumRequest):
        """Reactant vs product elemental inventory, per kilogram."""
        of = request.of_mass
        fuel_mass = 1.0 / (1.0 + of)
        oxidiser_mass = of / (1.0 + of)
        weights: dict[str, float] = {}
        for stream, total in ((request.fuel, fuel_mass),
                              (request.oxidiser, oxidiser_mass)):
            composition = stream.propellant.composition
            entries = composition.entries
            if len(entries) == 1:
                name = stream.propellant.provider_names.get(PROVIDER_ID,
                                                            entries[0][0])
                weights[name] = weights.get(name, 0.0) + total
            else:
                mass_basis = composition
                if composition.basis is not CompositionBasis.MASS_FRACTION:
                    return None  # needs conversion data; skip rather than guess
                for name, fraction in mass_basis.entries:
                    weights[name] = weights.get(name, 0.0) + total * fraction
        if any(name not in species for name in weights):
            return None
        reactants = Composition.from_fractions(
            weights, CompositionBasis.MASS_FRACTION)
        return check_element_balance(
            reactants, state.composition, species,
            basis=ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE,
            tolerances=self._tolerances)
