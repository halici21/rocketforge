# CEA / Cantera Thermochemistry Verification Campaign — Checkpoint

Diagnostic/verification run only. No UI redesign, no new thermochemistry
features, no tolerance widening, no provider replacement. Allowed write
paths: `acceptance/cea_cantera_verification/`, `experiments/` (a dedicated
diagnostic subfolder), documentation. `rocketforge/`, `ui/`, `tests/` (other
than a future regression test, if a defect is proven) are read-only for this
campaign.

## Environment (resolved from the live repository, not the prompt's own
historical-context section)

| Environment | Python | Key packages |
| --- | --- | --- |
| `.venv` (base/product) | 3.13.2 | PySide6 6.10.2, no CEA, no Cantera |
| `.venv-cea` (CEA-enabled) | 3.13.2 | `cea` 3.3.4 (Apache-2.0, cp313 wheel), `thermo.lib` SHA-256 `8e5df1cca92d4a48663d1ee5a1372e6508c59cddc2247ceeca32f041a03ec52a` |
| `%TEMP%/rf_cantera_verify` (fresh, this session) | 3.13 | `cantera` 3.2.0, `numpy` 2.5.3 — created from scratch this session specifically because Cantera must never be installed in a persistent project venv (confirmed zero `cantera` references in any `requirements*.txt`) |

Bare `python` on PATH resolves to a miniforge/conda install and is never
used, per standing project policy.

## Gates completed so far

1. **Opening baseline** — `git status --short`: clean except pre-existing
   untracked `.claude/`, `docs/design/skills/` (from prior programs) plus
   this campaign's new `experiments/cea_cantera_verification/` (untracked,
   expected — `acceptance/` is gitignored entirely, confirmed via
   `git check-ignore`). Base regression: `6931 passed, 154 skipped`.
   Production regression (CEA-enabled): `7086 passed, 2 skipped`.
   `tests/acceptance/`: `102 passed`.
2. **Provider architecture resolved from the live repo**: CEA is the
   primary/production thermochemistry provider
   (`rocketforge/providers/cea/`); Cantera is a **secondary, dev-only,
   independent oracle** — confirmed both by the historical decision record
   (`docs/engineering/implementation/PHASE_5B0_CEA_CANTERA_PROVIDER_SPIKE.md`)
   and, independently, by the live architecture of
   `tests/providers/cea/test_cea_cantera_oracle.py` (skips cleanly when the
   Cantera-generated artifact is absent, carries no verdict field of its
   own, labelled Tier 2 / never ground truth).
3. **Reproducibility of the single previously-accepted CH4/O2 oracle
   point** — regenerated fully from scratch: `experiments/phase_5c/
   make_artifacts.py` re-run in `.venv-cea` (regenerates the CEA-side
   artifacts including `cea_operating_matrix.json`, `cea_provider_common_
   case.json`, `cea_performance_benchmark.json`, etc.), then
   `experiments/phase_5c/cantera_oracle.py` re-run in the fresh Cantera
   venv. Result: bit-for-bit match with the historically recorded numbers
   in `acceptance/phase_5c/cantera_oracle_comparison.json`. No drift.
4. **New 12-state cross-provider matrix** —
   `experiments/cea_cantera_verification/cross_provider_matrix.py`
   (gaseous CH4/O2 and H2/O2 only, per the campaign's explicit instruction
   to start with gaseous reactants). Ran clean in all three modes (`cea`,
   `cantera`, `compare`). Worst bulk relative difference across all 12
   states: `1.60e-03`. Worst species relative difference: `5.99e-02`
   (minor species, small mole fraction). No anomalies, no non-finite
   values, no case-order mismatches.
5. **CEA test-suite live re-verification** — all read in full and re-run
   live, not assumed from memory:
   - `test_cea_cantera_oracle.py` — 6 passed
   - `test_reactant_enthalpy_coupling.py` — 25 passed
   - `test_cea_references.py -s` — 10 passed (LOX/LH2 external reference)
   - `test_cea_validation.py` — 15 passed (element conservation + mutation
     tests)
   - `tests/providers/cea/ tests/physics/thermochemistry/
     tests/engineering/test_chamber_handshake.py
     tests/engineering/test_ideal_performance.py` combined — 564 passed,
     1 skipped
6. **O/F sweep inspected** (`acceptance/phase_5c/cea_operating_matrix.json`,
   15 states, 3 pressures x 5 O/F points, CH4/O2): monotonically sane
   trends confirmed — Tc peaks near O/F≈4.0 (mass-stoichiometric for
   CH4+2O2), condensed carbon mass fraction falls monotonically as O/F
   rises (less fuel-rich soot formation), gamma falls as Tc rises (more
   dissociation), Tc rises with chamber pressure at fixed O/F (equilibrium
   shift, less dissociation at higher P) — all physically expected
   directions, no anomalies. `element_residual` is `null` in every row of
   this particular artifact (it does not compute that field itself); the
   dedicated element-conservation check lives in `test_cea_validation.py`
   and is confirmed passing separately.
7. **Packaging** — `packaging/RocketForge.spec` conditionally bundles CEA
   (`thermo.lib`/`trans.lib`, `cea.lib.libcea`) only when present at build
   time, with a graceful degrade message when absent; Cantera has **no
   block at all** in the spec — never bundled, by construction, not by an
   exclusion rule that could silently rot.

No blockers, no failing cases, no production changes so far. No tolerance
was widened, no reference point removed, no provider replaced.

## Campaign complete

All remaining artifacts were written: `acceptance/cea_cantera_verification/
{versions,provider_inventory,cea_verification_part_a,
cantera_verification_part_b,cross_provider_consistency_part_c,
species_comparability,external_triangulation,
rocketforge_integration_part_d,final_verdict}.json` plus the four required
docs under `docs/engineering/verification/`. A genuine external
triangulation (Marzouk 2023, DOI 10.48084/etasr.6132) was found and
reproduced for both a CH4/O2 and an H2/O2 gaseous stoichiometric case.
Closing regression: base `.venv` 6931 passed/154 skipped (identical to
opening), production `.venv-cea` 7086 passed/2 skipped (identical to
opening). No production file changed. Final verdict: **PASS**. See
`docs/engineering/verification/CEA_CANTERA_VERIFICATION_R1.md`.
