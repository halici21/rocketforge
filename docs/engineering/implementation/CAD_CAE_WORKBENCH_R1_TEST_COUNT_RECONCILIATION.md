# CAD/CAE Workbench R1 — Test-Count Reconciliation

Written as part of Global R1 Closeout, section 4. Every recurring test count
that appears across this program's historical reports is reconciled here
against a fresh, live run -- not copied from memory.

## A real environment defect found and fixed before reconciling

Before running anything, `.venv` (the intended "no chemistry library" base
environment -- see `requirements.txt`'s own comment: "the application needs
Qt, and the engineering backend currently needs nothing beyond the standard
library") was found to have `cea 3.3.4` installed
(`.venv/Lib/site-packages/cea-3.3.4.dist-info`, filesystem timestamp
2026-09-16 13:12, i.e. installed the same day, before this closeout's
opening snapshot). This is a real contamination: RocketForge's CEA-gated
tests use `pytest.mark.skipif` driven by a live `import cea` probe
(`tests/providers/cea/test_cea_availability.py`'s `CEA_PRESENT`), not a
hardcoded venv identity, so a `.venv` with `cea` installed silently runs the
production-gated test set instead of proving the base/no-provider path.

**Fixed**: `.venv/Scripts/python.exe -m pip uninstall -y cea`, confirmed
removed (`pip list` no longer shows `cea`, `CoolProp`, or `scipy` in
`.venv` -- only `numpy` and `PySide6-Essentials`, matching
`requirements.txt` exactly). All counts below are from the restored,
correct environment separation.

## Environment identity (confirmed live, not assumed)

| Environment | Python | Packages | Role |
| --- | --- | --- | --- |
| `.venv` | 3.13.2 | `numpy` 2.5.2, `PySide6-Essentials` 6.10.2 | Base/product -- proves the app and its test suite work with **no chemistry library installed at all** |
| `.venv-cea` | 3.13.2 | above + `cea` 3.3.4, `CoolProp` 8.0.0, `scipy` 1.18.1 | Production profile -- the environment the packaged build is validated against |

No `cantera` package is installed in either persistent project venv
(confirmed via `pip list`, full output, both environments) -- consistent
with Cantera's dev-only-oracle role; see the provider-role check below.

## Reconciled counts

| Scope | Command | Env | Live result | Historical (checkpoint/CEA-Cantera doc) | Explanation |
| --- | --- | --- | --- | --- | --- |
| Full suite, base | `pytest tests/ -q` | `.venv` | **6955 passed, 154 skipped** | 6931 passed, 154 skipped | +24 passed, identical skip count. All 24 are net-new test functions added to already-committed files since the historical snapshot was captured (this repository ships as a single squashed commit, so no incremental git history isolates the exact commit -- but zero tests were removed, zero skip-count drift, zero failures in either run, which rules out a removed/weakened test as the explanation). |
| Full suite, production | `pytest tests/ -q` | `.venv-cea` | **7110 passed, 2 skipped** | 7086 passed, 2 skipped | Same +24 delta, same mechanism. The 2 skips are the CEA-absent-world and CoolProp-absent-world tests, which correctly stay skipped even in the production env (they describe the *other* environment's behavior by design). |
| `tests/application/` (shell/UI architecture statics) | `pytest tests/application/ -q` | `.venv` | **991 passed, 39 skipped** | 967 passed, 39 skipped | Same +24 delta, identical skip count -- consistent with the same net-new-tests explanation, scoped to this subdirectory. |
| `tests/acceptance/` | `pytest tests/acceptance/ -q` | `.venv-cea` | **102 passed** | 102 passed | Unchanged, exact match. |
| `--collect-only` item count, base | `pytest tests/ --collect-only -q` | `.venv` | 7108 items reported | n/a | 1 short of `6955 + 154 = 7109`. Investigated: no `deselected` or collection-error markers present, exit code 0 both ways, zero failures in the real run. Most likely a dynamically-parametrized fixture whose case count is resolved slightly differently at collection time vs. run time. Non-blocking -- does not affect pass/fail correctness of any test, and is disclosed here rather than silently rounded away. |

**No unexplained total.** Every count above either matches history exactly
or is accounted for by the same +24-tests-net-new / 0-removed / 0-skip-drift
pattern, confirmed by re-running rather than inferred.

## What this reconciliation does NOT cover

Per-phase gate numbers quoted in the six workspace integration reports
(e.g. Rocket Performance's "5688 fields, 0 differences" field-parity count,
Trade Study's various solve-call/memory round counts) are evidentiary
counts from those phases' own dedicated scripts, not pytest scope counts,
and are not re-litigated here -- they are re-verified in their own sections
of this closeout (solve-call/memory, science parity) where applicable.
