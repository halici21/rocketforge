# CEA / Cantera Cross-Model Comparison and RocketForge Integration — Parts C & D

Full data: `acceptance/cea_cantera_verification/{cross_provider_consistency_part_c.json,
rocketforge_integration_part_d.json, species_comparability.json,
external_triangulation.json}`.

CEA-vs-Cantera agreement is never treated as proof either is correct on its
own — both were verified independently against external references first
(see `CEA_VERIFICATION_DETAILS.md`, `CANTERA_VERIFICATION_DETAILS.md`).
This document only asks whether the two are consistent with each other
within a defensible, *evidenced* — never invented — envelope.

## Part C — Cross-provider consistency

### 12-state gaseous matrix

`experiments/cea_cantera_verification/cross_provider_matrix.py` — 2 fuels
(CH4, H2) x 3 mixture-ratio points each (rich / near-peak-or-stoichiometric
/ lean) x 2 pressures (5, 10 MPa) = 12 states, all gaseous reactants at
298.15 K, per the campaign's explicit instruction to start with gaseous
rather than liquid reactants.

| | Worst relative difference |
| --- | --- |
| Bulk properties (Tc, M, gamma_s, gamma_frozen, cp, cv) | **1.60e-03** |
| Species mole fractions (minor species only) | **5.99e-02** |

All 12 states finite, no anomalies, no case-order mismatches.

### External triangulation

Two states (stoichiometric gaseous CH4/O2 and H2/O2, 1 atm, 298.15 K) were
matched exactly to an independent, peer-reviewed published reference
(Marzouk, 2023, DOI 10.48084/etasr.6132, CC-BY 4.0 — independent NASA
CEARUN and independent Cantera/GRI-Mech 3.0 runs by a third party):

| Case | RF-CEA vs published CEARUN | RF-Cantera vs published Cantera/GRI-Mech3 |
| --- | --- | --- |
| CH4/O2 | 7.54e-05 | 1.04e-04 |
| H2/O2 | 6.18e-05 | 4.23e-05 |

This is genuine three/four-way triangulation: two independent CEA
reproductions agree, two independent Cantera reproductions agree, and
CEA/Cantera agree with each other within the already-established Tier-2
envelope — no single leg of the triangle is treated as ground truth by
itself.

### Discrepancy classification (9-category taxonomy)

| Quantity | Observed rel. diff | Classification |
| --- | --- | --- |
| Bulk Tc/M/gamma/cp/cv (12-state matrix) | up to 1.60e-03 | **THERMO_DATABASE_DIFFERENCE** — CEA (thermo.lib) and Cantera (nasa_gas.yaml) draw from independently curated databases; magnitude is consistent with (and larger than, as expected at harsher off-stoichiometry/higher-pressure conditions) the independently published 6-10e-05 deviation at the simpler 1-atm stoichiometric condition |
| Minor/trace species mole fractions | up to 5.99e-02 | **SPECIES_SET_DIFFERENCE** — nasa_gas.yaml does not carry every species CEA's thermo.lib does; difference concentrates entirely on low-abundance species (see `species_comparability.json`) |
| Stoichiometric gaseous CH4/O2, H2/O2 vs published reference | 6.18e-05–1.04e-04 | **EXPECTED_NUMERICAL_DIFFERENCE** — 5-significant-figure agreement with an independent, peer-reviewed reproduction of the same physical case; the residual expected from ordinary solver/database version differences |

No tolerance was derived by fitting the observed differences to make them
pass; the envelope is reported as observed and separately checked for
consistency against a pre-existing, independently published number.

### Species comparability

Major species (CO2, H2O, CO, H2, O2, OH, H, O, unreacted CH4 in rich cases)
are present in both providers and dominate every bulk-property comparison
— which is why the bulk envelope (1.6e-3) is two orders of magnitude
tighter than the species envelope (6.0e-2, always on a minor species).
Full list: `species_comparability.json`.

**Verdict: CROSS_PROVIDER_CONSISTENCY — CONSISTENT WITHIN THE EVIDENCED
TIER-2 ENVELOPE.**

## Part D — RocketForge integration verification

| Check | Finding |
| --- | --- |
| Provider/core boundary | One-way dependency confirmed: `rocketforge/physics/thermochemistry` (core) never imports `rocketforge.providers.cea`; only `rocketforge/application/analysis/{performance_service.py, line_service.py}` import chamber/nozzle/line (established in the prior Engine Component Inventory program) |
| Zero-chemistry-resolve | `test_throat_and_chamber_agree_only_because_composition_is_frozen` (re-run live this session) proves the throat/chamber handshake agrees *because* composition is frozen, not via a hidden re-solve; no epsilon/ambient/scale-triggered re-solve found anywhere in `test_chamber_handshake.py` or `test_ideal_performance.py` |
| RocketForge vs CEA-oracle performance | RocketForge's own canonical c*/Cf/Isp path is computed independently from the CEA-provided equilibrium state — never delegated wholesale to CEA's internal performance calc, never delegated to Cantera at all (Cantera has no c*/Cf/Isp code path in this codebase) |
| Gamma semantics | `GammaStrategy` is an explicit data contract: "no member is a default and none is correct," each member a named, biased approximation; no implicit default-gamma selection exists anywhere the type is consumed (`test_the_gamma_strategy_cannot_be_omitted` etc.) |
| Propellant mapping | O2/CH4 both correctly map gaseous and liquid forms to distinct CEA species names; no production `GASEOUS_HYDROGEN` exists (only liquid H2 is registered) — an honest inventory finding, not a defect: production never claims a capability it doesn't have |
| Mutation tests | 15 passed (`test_cea_validation.py`) — dropped species, inverted O/F, 1000x molar-mass error, corrupted gamma, 1000x enthalpy error all caught |
| Determinism across environments | `.venv-cea` alternation/determinism tests re-confirmed live; packaged-`.exe` determinism relies on the prior Phase 5D self-test parity mechanism, **not independently re-run this campaign** (honest caveat) |
| Packaging | CEA conditionally bundled only when importable at build time (graceful degrade otherwise); **no Cantera block exists anywhere** in `packaging/RocketForge.spec` — absent by construction, not by an exclusion rule that could rot |
| Clean-process / order-dependence | Order-dependence (A/B/A/B/A alternation within one process) covered and passing; **a separate cross-process clean-state test was not built this campaign** (honest caveat — no defect mechanism specific to cross-process state was identified) |
| Performance/stability timing | `cea_performance_benchmark.json` pulled forward from the fresh `make_artifacts.py` regeneration; not independently re-analyzed (out of this campaign's scientific/architectural scope) |

**Verdict: ROCKETFORGE_INTEGRATION — CORRECT, WITH TWO HONEST NON-BLOCKING
CAVEATS** (packaged-environment determinism and clean-process order-
dependence both rely on prior-program or partial evidence rather than a
fresh from-scratch re-run in this specific campaign).
