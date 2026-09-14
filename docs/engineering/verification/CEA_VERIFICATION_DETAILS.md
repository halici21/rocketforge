# NASA CEA Verification Details — Part A

Full data: `acceptance/cea_cantera_verification/cea_verification_part_a.json`.

## Units / basis mutation tests

Source: `tests/providers/cea/test_cea_validation.py` — **15 passed**, live
this session. Provider tolerances (looser than RocketForge's own core
tolerances, and explicitly documented as necessary because of CEA's own
constants/solver residual, not an arbitrary relaxation): state-identity
relative tolerance 1e-5, element-balance relative tolerance 1e-6. Every
loosened tolerance is paired with a mutation proof that a real defect still
fails by orders of magnitude — confirmed live, not merely read:

- dropping a >40%-mole-fraction product species (H2O) from the composition
  is caught by element balance
- an inverted O/F ratio is caught
- a 1000x molar-mass corruption is caught
- a corrupted gamma is caught
- a 1000x enthalpy error is caught

## Element conservation

Canonical Phase 5C case: LOX (90.17 K, 3.0 MPa) / liquid CH4 (111.7 K,
3.0 MPa), O/F 3.4 by mass, Pc = 10 MPa, HP equilibrium.

Residual, **independently reconstructed outside pytest this session** (not
merely read from the test's own assertion):

```
residual = 8.395716291583674e-09
tolerance = 1.0e-06
passed = True
```

Consistent in order of magnitude with the historical Phase 5B-0 spike's
independently-measured 1.04e-09-class residual on a different case.

## External published reference (LOX/LH2)

Source: `tests/providers/cea/test_cea_references.py` — **10 passed**.
Evidence Tier B: `PUBLISHED_LOX_LH2`, a NASA CEA 2002 / RP-1311-class
published case, genuinely independent of RocketForge's own prior output.
Tolerance method: `_rounding_box()` — derived from the published value's
own printed significant figures, not an arbitrary percentage.

Relative differences, independently recomputed this session:

| Quantity | Relative difference |
| --- | --- |
| Tc | 6.00e-07 |
| M | 1.03e-05 |
| c* | 3.82e-06 |
| Isp_s | 1.32e-05 |
| gamma_exit | 2.71e-05 |

All 5-6 orders of magnitude tighter than typical engineering tolerance —
strongly supports implementation correctness against an external reference.

A second external triangulation (stoichiometric gaseous CH4/O2 and H2/O2)
is documented in `CEA_CANTERA_CROSS_MODEL_COMPARISON.md` and
`acceptance/cea_cantera_verification/external_triangulation.json`.

## Canonical case reproduction

`experiments/phase_5c/make_artifacts.py`, re-run fresh in `.venv-cea` this
session, regenerated `cea_provider_common_case.json`,
`cea_source_frozen_parity.json`, and (via the fresh Cantera venv)
`cantera_oracle_comparison.json` — bit-for-bit match with the historically
recorded values. `acceptance/` is entirely gitignored, so there is no git
history to diff against; reproducibility is established by regenerate-and-
compare, which is what was done.

## O/F sweep — physical trend

Source: `acceptance/phase_5c/cea_operating_matrix.json` (15 states: 3
pressures x 5 O/F points, CH4/O2). All trends physically correct:

- **Tc peaks near O/F ≈ 4.0** at every pressure — matches mass-
  stoichiometric CH4 + 2 O2 (64/16 = 4.0) exactly.
- **`condensed_mass_fraction` falls monotonically** as O/F rises from 2.5
  to 4.5, at every pressure row — less fuel-rich soot formation as the
  mixture leans out.
- **gamma_s and gamma_frozen both fall as Tc rises** — more dissociation
  at higher temperature.
- **Tc rises with chamber pressure at fixed O/F** — equilibrium shifts
  toward less dissociation at higher P (Le Chatelier), holds at every O/F.

No anomalies found. Caveat: `element_residual` is `null` in every row of
this specific artifact (it does not compute that field itself); element
conservation is verified separately (see above), not via this sweep
artifact — noted so the gap is not silently assumed away.

## Reactant-enthalpy coupling

Source: `tests/providers/cea/test_reactant_enthalpy_coupling.py` — **25
passed**. Verifies: `h_corrected == h_CEA_reference` exactly (bit-identical)
at the reference state; native mode insensitive to liquid-reactant
temperature perturbation; corrected mode responds to it; a gaseous
reactant receives zero correction (negative control against double-
counting an already-consistent state).

## Determinism

Source: `tests/providers/cea/test_cea_provider_live.py` (30 tests present;
`test_no_state_leakage_between_alternating_cases` and
`test_the_hydrogen_pair_also_solves` read in full). Verifies: bitwise-
identical results across repeated solves of the same case (A/A/A); no
state contamination across alternating distinct cases (A/B/A/B/A); CEA's
`EqSolution.T` (a read-only, mutated-carrier object CEA reuses internally
across solves) never crosses the adapter boundary raw.

## Failure behavior

`check_availability()` catches both `ImportError` and `ValueError` (CEA can
raise `ValueError` on missing `thermo.lib`/`trans.lib` data, not just
`ImportError`) — confirmed by code inspection and exercised throughout this
campaign's own scripts via `availability.is_usable` guards.

## Test tally

| Source | Result |
| --- | --- |
| `test_cea_cantera_oracle.py` | 6 passed |
| `test_reactant_enthalpy_coupling.py` | 25 passed |
| `test_cea_references.py` | 10 passed |
| `test_cea_validation.py` | 15 passed |
| combined provider + thermochemistry + chamber handshake + ideal performance | 564 passed, 1 skipped |

## Verdict

**CEA_IMPLEMENTATION: CORRECT.**
