# CEA / Cantera Thermochemistry Verification Campaign — R1

Verification/diagnostic campaign only. No UI redesign, no new thermochemistry
features, no tolerance widening, no provider replacement. All production
code, UI, and frozen manifests are unchanged (`git status --short` and the
full regression suites are identical at open and close — see below).

Companion documents: `CEA_VERIFICATION_DETAILS.md` (Part A, NASA CEA),
`CANTERA_VERIFICATION_DETAILS.md` (Part B, Cantera),
`CEA_CANTERA_CROSS_MODEL_COMPARISON.md` (Parts C/D, cross-provider and
RocketForge-integration verification). Checkpoint:
`docs/engineering/implementation/CEA_CANTERA_VERIFICATION_CHECKPOINT.md`.

## Three validation questions, kept separate throughout

- **A — Implementation correctness**: does each provider's adapter do what
  it claims (units, basis, element conservation, mapping)?
- **B — Reference validity**: does each provider's output match an
  independent, external, published reference?
- **C — Cross-provider consistency**: do CEA and Cantera agree with each
  other within a defensible, *evidenced* envelope?

Per the campaign's explicit instruction, CEA-vs-Cantera agreement alone was
never used as proof either is correct — two wrong implementations can
agree. Question B was answered independently for each provider using a
published, third-party reference (see below), before Question C was even
attempted.

## Environment resolved from the live repository

| Environment | Python | Key packages |
| --- | --- | --- |
| `.venv` (base/product) | 3.13.2 | PySide6 6.10.2, no thermochemistry provider |
| `.venv-cea` | 3.13.2 | `cea` 3.3.4 (Apache-2.0), `thermo.lib` SHA-256 `8e5df1cca92d4a48663d1ee5a1372e6508c59cddc2247ceeca32f041a03ec52a` |
| `%TEMP%/rf_cantera_verify` (fresh, session-local) | 3.13 | `cantera` 3.2.0, `numpy` 2.5.3 |

Full detail: `acceptance/cea_cantera_verification/{versions.json,
provider_inventory.json}`.

## Provider architecture (resolved live, not assumed from history)

**NASA CEA is the primary/production thermochemistry provider.** Cantera is
a **secondary, dev-only, independent oracle** — never installed in a
persistent project venv, never imported by `rocketforge/`, never bundled by
`packaging/RocketForge.spec` (no Cantera block exists in the spec at all).
`tests/providers/cea/test_cea_cantera_oracle.py` implements exactly this
architecture: it reads a static JSON artifact and `pytest.skip()`s cleanly
when it is absent, carries no verdict field of its own, and is explicitly
labelled Tier 2 (never ground truth). Confirmed both from the historical
decision record (`PHASE_5B0_CEA_CANTERA_PROVIDER_SPIKE.md`) and, separately,
from the live shape of the current test.

## Headline results

| Question | Verdict |
| --- | --- |
| CEA implementation correct? | **CORRECT** — see `CEA_VERIFICATION_DETAILS.md` |
| Cantera implementation correct (for its declared role)? | **CORRECT** — see `CANTERA_VERIFICATION_DETAILS.md` |
| Cross-provider consistency? | **CONSISTENT within an evidenced Tier-2 envelope** — see `CEA_CANTERA_CROSS_MODEL_COMPARISON.md` |
| RocketForge integration correct? | **CORRECT, with two honest non-blocking caveats** — see `CEA_CANTERA_CROSS_MODEL_COMPARISON.md` |
| Previously-accepted results still reproducible? | **YES** — the Phase 5C CH4/O2 oracle point was regenerated from scratch and matched bit-for-bit |
| Any blocking defect found? | **NO** — none of the campaign's named blocking-failure conditions were observed |

Full artifact: `acceptance/cea_cantera_verification/final_verdict.json`.

## Reproducibility of previously-accepted results

The single previously-accepted CH4/O2 Cantera-oracle comparison point
(`acceptance/phase_5c/cantera_oracle_comparison.json`) was regenerated
completely from scratch this session — both the CEA-side
(`experiments/phase_5c/make_artifacts.py`, run in `.venv-cea`) and the
Cantera-side (`experiments/phase_5c/cantera_oracle.py`, run in a
freshly-created, from-scratch Cantera venv) — and matched the historically
recorded values bit-for-bit. No drift.

## External triangulation (new in this campaign)

A genuinely independent, peer-reviewed, published reference was found and
reproduced exactly for both a CH4/O2 and an H2/O2 gaseous stoichiometric
case (Marzouk, 2023, *Engineering, Technology & Applied Science Research*,
DOI 10.48084/etasr.6132, CC-BY 4.0 — independent runs of NASA's own CEARUN
tool and an independent Cantera/GRI-Mech 3.0 implementation). Reproducing
the exact stated conditions (298.15 K, 1 atm, stoichiometric):

| Case | RocketForge CEA | Published CEARUN | Rel. diff | RocketForge Cantera | Published Cantera/GRI-Mech3 | Rel. diff |
| --- | --- | --- | --- | --- | --- | --- |
| CH4/O2 | 3049.89 K | 3050.12 K | 7.5e-05 | 3051.74 K | 3052.06 K | 1.0e-04 |
| H2/O2 | 3074.32 K | 3074.51 K | 6.2e-05 | 3076.79 K | 3076.92 K | 4.2e-05 |

Full detail: `acceptance/cea_cantera_verification/external_triangulation.json`.

## New 12-state cross-provider matrix

Built and run this session (`experiments/cea_cantera_verification/
cross_provider_matrix.py`), generalising the single accepted CH4/O2 point
into a real matrix: 2 fuels x 3 mixture points x 2 pressures, gaseous
reactants only, per the campaign's explicit instruction to start with
gaseous rather than liquid reactants. Worst bulk relative difference:
1.60e-03. Worst species relative difference (always a minor species):
5.99e-02. No anomalies. Full detail:
`acceptance/cea_cantera_verification/cross_provider_matrix.json`.

## Closing regression

| Suite | Result | Matches opening? |
| --- | --- | --- |
| Base (`.venv`) | 6931 passed, 154 skipped | YES, identical |
| Production (`.venv-cea`) | 7086 passed, 2 skipped | YES, identical |

`git status --short` at close: only pre-existing untracked `.claude/`,
`docs/design/skills/` plus this campaign's own new, expected untracked
files (`experiments/cea_cantera_verification/`,
`docs/engineering/implementation/CEA_CANTERA_VERIFICATION_CHECKPOINT.md`,
`docs/engineering/verification/`) — `acceptance/` is entirely gitignored.
No production file was modified.

## STOP

This campaign is a verification/diagnostic run. It does not redesign the
UI, does not add thermochemistry features, does not change tolerances, and
does not replace either provider. No further phase is begun automatically.
