"""Apply the NASA CEA Provider v1.1 additive change to provider.py."""
from __future__ import annotations

import pathlib

p = pathlib.Path("rocketforge/providers/cea/provider.py")
t = p.read_text(encoding="utf-8")

# --- 1. import the coupling vocabulary -----------------------------------
old_import = """from .mapping import (
"""
new_import = """from .enthalpy_coupling import (
    CEA_REFERENCE_PRESSURE,
    ReactantEnthalpyCorrection,
    ReactantEnthalpyPolicy,
    ReactantFluidBinding,
    mixture_enthalpy_correction,
    reactant_mass_fractions,
    sensible_enthalpy_increment,
)
from .mapping import (
"""
assert old_import in t
t = t.replace(old_import, new_import, 1)

# --- 2. the signature ----------------------------------------------------
old_sig = '''    def solve_chamber(
        self, request: ChamberEquilibriumRequest
    ) -> Solution[ChamberGas]:
        """Solve a chamber equilibrium at constant enthalpy and pressure.

        Raises for a malformed request or a provider failure; reports
        non-convergence and failed post-validation through the returned
        ``Solution``. Those are three different things and stay that way.
        """'''
new_sig = '''    def solve_chamber(
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
        """'''
assert old_sig in t
t = t.replace(old_sig, new_sig, 1)

# --- 3. the body ---------------------------------------------------------
old_body = """        molar_masses = self._blend_molar_masses(request)
        chamber_input = build_chamber_input(request, molar_masses=molar_masses)

        raw = solve_chamber_raw(module, chamber_input)

        species = self._species_for(chamber_input.product_species,
                                    chamber_input.reactant_names)
        provenance = self.provenance(
            species_set=chamber_input.product_species,
            reactant_conditions=request.reactant_conditions)

        diagnostics: list[Diagnostic] = list(
            self._assigned_enthalpy_diagnostics(chamber_input))"""
new_body = """        molar_masses = self._blend_molar_masses(request)
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
                                                corrections=corrections))"""
assert old_body in t
t = t.replace(old_body, new_body, 1)

# --- 4. provenance gains the policy --------------------------------------
old_prov = """    def provenance(self,
                   species_set: tuple[str, ...] = (),
                   reactant_conditions: dict[str, float] | None = None,
                   ) -> ThermochemistryProvenance:"""
new_prov = """    def provenance(self,
                   species_set: tuple[str, ...] = (),
                   reactant_conditions: dict[str, float] | None = None,
                   enthalpy_policy: ReactantEnthalpyPolicy =
                       ReactantEnthalpyPolicy.PROVIDER_NATIVE,
                   corrections: tuple[ReactantEnthalpyCorrection, ...] = (),
                   ) -> ThermochemistryProvenance:"""
assert old_prov in t
t = t.replace(old_prov, new_prov, 1)

old_opts = """                "thermo_lib_path": resources.thermo_path if resources else "",
            },"""
new_opts = """                "thermo_lib_path": resources.thermo_path if resources else "",
                # v1.1. Always recorded, under both policies, so that a result
                # can never be silent about which reactant-energy model made it.
                "reactant_enthalpy_policy": enthalpy_policy.value,
                "reactant_enthalpy_corrections": repr(
                    [c.as_mapping() for c in corrections]) if corrections else "",
                "cea_reference_pressure_Pa": repr(CEA_REFERENCE_PRESSURE)
                    if corrections else "",
            },"""
assert old_opts in t
t = t.replace(old_opts, new_opts, 1)

p.write_text(t, encoding="utf-8")
print("provider.py patched (signature, body, provenance)")
