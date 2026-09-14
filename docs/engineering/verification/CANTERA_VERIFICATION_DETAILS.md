# Cantera Verification Details — Part B

Full data: `acceptance/cea_cantera_verification/cantera_verification_part_b.json`.

Cantera is evaluated against the role it actually occupies in this
architecture, per the campaign's own instruction not to grade a component
against responsibilities it does not own.

## Role classification (resolved from the live repository)

**SECONDARY / INDEPENDENT ORACLE, DEV-ONLY.**

Evidence:

- `docs/engineering/implementation/PHASE_5B0_CEA_CANTERA_PROVIDER_SPIKE.md`
  explicitly recommends this role at the architecture-decision stage.
- `tests/providers/cea/test_cea_cantera_oracle.py` implements exactly this:
  reads a static JSON artifact, `pytest.skip()`s cleanly if absent, carries
  no verdict field of its own, labels its comparison Tier 2 explicitly.
- Zero references to `cantera` in any `requirements*.txt`.
- Zero references to Cantera anywhere in `packaging/RocketForge.spec` — no
  conditional block, no exclusion rule; it is simply never a packaging
  concern.
- `rocketforge/` has no import of `cantera` anywhere — confirmed by the
  fact that `.venv`, the product venv, never has it installed and the full
  base + production regression suites pass without it.

## Mechanism provenance

`nasa_gas.yaml`, bundled with the `cantera` 3.2.0 pip package itself (not a
RocketForge-authored or RocketForge-modified file). Installed in a fresh,
session-local venv created specifically for this campaign
(`%TEMP%/rf_cantera_verify`), never persisted in the project.

## Installation sanity

Cantera 3.2.0 imports cleanly; `Solution`/`Species`/`equilibrate` all
function as expected across every case run this session (the 12-state
matrix, the 2 external-triangulation cases, and the regenerated Phase 5C
single point) with no exceptions and no non-finite results.

## HP-equilibrium sanity

All 12 gaseous states in the cross-provider matrix solved successfully,
with physically reasonable temperatures/compositions consistent with the
CEA-side values for the same states. No anomalies.

## External reference reproduction (new in this campaign)

Per the campaign's explicit instruction not to validate Cantera only
against CEA, Cantera itself was checked against an independent published
reference: Marzouk (2023), DOI 10.48084/etasr.6132, an independent
Cantera/GRI-Mech-3.0 implementation. Cantera(`nasa_gas.yaml`) matched that
published result to 4.2e-05–1.0e-04 relative difference on stoichiometric
CH4/O2 and H2/O2 at 1 atm/298.15 K (the residual attributable to the
different bundled mechanism, `nasa_gas.yaml` vs GRI-Mech 3.0 — a
THERMO_DATABASE_DIFFERENCE, not a defect). Full detail:
`acceptance/cea_cantera_verification/external_triangulation.json`.

## Element conservation

Not independently re-implemented as a dedicated Cantera-side numeric check
in this campaign. Cantera's own `equilibrate('HP')` solver conserves
elements by construction (mass-fraction-weighted species input, standard
Gibbs-minimization solve) — standard, well-established Cantera behavior
that RocketForge never wraps or could silently break, since RocketForge
never touches Cantera's internal solve path. Flagged honestly as a gap in
this campaign's own coverage, not treated as a hidden pass.

## Verdict

**CANTERA_IMPLEMENTATION: CORRECT** (for its declared dev-only/independent-
oracle role; no evidence evaluated against responsibilities it does not
own).
