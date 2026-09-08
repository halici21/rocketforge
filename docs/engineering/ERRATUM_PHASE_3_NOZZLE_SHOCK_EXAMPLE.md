# Erratum — Phase 3 §10.6 internal-shock worked example

**Status:** `PHASE_3_SPEC_CONFLICT`, raised during Phase 4F before the affected
code was written.
**Raised:** 2026-09-01
**Affects:** `03_compressible_flow_specification.md` §10.6 (two numbers),
`05_verification_and_validation_plan.md` §11.9 summary line (one number).
**Does not affect:** the three critical pressure ratios, the shock-at-exit
identity, the classifier, or any accepted Phase 4A–4E result.

## The contradiction

Section 10.6 gives a verification example for γ = 1.4, Ae/A\* = 2.0 with a
normal shock placed at A_s/A\* = 1.5, and lists six numbers. Section 12.4 gives
the mandatory pseudocode for the same calculation. **They disagree on the last
two.**

The pseudocode, and §10.6's own prose in the paragraph immediately above the
example, both say the downstream flow is referred to a *new, larger* sonic area:

```
A2_star_ratio = 1 / shock.stagnation_pressure_ratio          # A2*/A1*
Me = mach_from_area_ratio(AR_exit / A2_star_ratio, gas, SUBSONIC)
```

> "A₂\* is larger, A_e/A₂\* is smaller, M_e is larger and p_e is lower."

The example's own numbers can only be reproduced by *multiplying* by A₂\*/A₁\*
where the pseudocode divides.

## Which one is right, proved independently

Reproduced with a standalone stdlib script — no RocketForge module involved, a
plain bisection on the textbook relations:

| Quantity | §10.6 example | Independent oracle | Verdict |
| --- | --- | --- | --- |
| M_s1 | 1.8541235267 | 1.8541235267 | agrees |
| M_s2 | 0.6048430465 | 0.6048430465 | agrees |
| p₀₂/p₀₁ | 0.7883594291 | 0.7883594291 | agrees |
| A₂\*/A₁\* | 1.2684569539 | 1.2684569539 | agrees |
| **M_e** | **0.2358088692** | **0.4041969520** | **example wrong** |
| **p_b/p₀** | **0.7584257377** | **0.7044519779** | **example wrong** |

The decisive test is mass conservation, which is not a matter of convention.
For a choked nozzle the mass flow at the exit must equal the mass flow at the
throat, so

    (1 / (A_e/A₂*)) · (A_e/A₁*) · (p₀₂/p₀₁)  =  1

| Path | A/A\* used for the exit | ṁ_exit / ṁ_throat |
| --- | --- | --- |
| §12.4 pseudocode (divide) | 1.5767188582 | **1.000000000000** |
| §10.6 example (multiply) | 2.5369139078 | 0.621510589416 |

The example's numbers lose 38% of the mass flow across the exit plane. They
cannot describe a steady nozzle.

The physical argument is the same one §10.6's prose already makes: a shock
destroys stagnation pressure, so the sonic area the *downstream* flow is
referred to is **larger** than the throat (A₂\* = A₁\*·p₀₁/p₀₂ > A₁\*). The exit
area is fixed, so A_e/A₂\* must be **smaller** than A_e/A₁\* = 2, and 2.537 is
therefore impossible.

## Corrected example

γ = 1.4, Ae/A\* = 2.0, shock at A_s/A\* = 1.5:

    M_s1      = 1.8541235267
    M_s2      = 0.6048430465
    p02/p01   = 0.7883594291
    A2*/A1*   = 1.2684569539
    Ae/A2*    = 1.5767188582
    M_e       = 0.4041969520
    p_b/p0    = 0.7044519779      (between second 0.5134007280 and first 0.9371625024)

## What was implemented

`rocketforge/physics/compressible/nozzle.py` follows §12.4 — the mandatory
pseudocode — and therefore conserves mass. The corrected values above are
pinned as reference tests in `tests/physics/compressible/test_nozzle_reference_cases.py`
alongside the four numbers the example got right, so this cannot silently drift
back.

**No physics was tuned to make an example match.** The example was wrong; the
relations were not touched.

## Suggested document fix (not applied here)

Phase 4F does not edit Phase 3 documents. When Phase 4G opens the specification
for its API freeze, `03` §10.6 should read `M_e = 0.4041969520` and
`p_b/p₀ = 0.7044519779`, and `05` §11.9's summary line should carry the same
corrected back pressure.
