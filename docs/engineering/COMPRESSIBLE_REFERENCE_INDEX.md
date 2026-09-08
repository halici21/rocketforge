# Compressible Flow — Reference Index

Every external dataset the subsystem is validated against, what it covers, and
what it costs to compare. All six ship inside the executable.

**Consolidated total: 2 320 published values compared, 2 316 PASS, 4 REVIEW,
0 pending.** Every REVIEW is an explained source anomaly, listed in section 3.

---

## 1. The datasets

### Anderson, *Fundamentals of Aerodynamics*, 6th edition — Appendix A

| | |
| --- | --- |
| File | `anderson6_appendix_a_isentropic.json` |
| Module | isentropic, area-Mach |
| Source | John D. Anderson, Jr., McGraw-Hill, ISBN 9781259129919, pp. 1079-1083 |
| Kind | printed table in a textbook appendix |
| gamma | 1.4 |
| Columns | `p0/p`, `rho0/rho`, `T0/T`, `A/A*` — all stagnation over static |
| Rows | 217, M = 0.02 to 100 |
| Values compared | 868 |
| Result | **866 PASS, 2 REVIEW** |
| Tolerance | half a unit in the last printed figure of each value |
| Packaged | yes |

### Anderson Appendix B

| | |
| --- | --- |
| File | `anderson6_appendix_b_normal_shock.json` |
| Module | normal shock (and, through it, oblique shock and the nozzle) |
| Source | as above, pp. 1085-1088 |
| gamma | 1.4 |
| Columns | `p2/p1`, `rho2/rho1`, `T2/T1`, `p02/p01`, `p02/p1`, `M2` |
| Rows | 168, M1 = 1.00 to 20+ |
| Values compared | 1 008 |
| Result | **1 006 PASS, 2 REVIEW** |
| Tolerance | half a unit in the last printed figure |
| Packaged | yes |

### Anderson Appendix C

| | |
| --- | --- |
| File | `anderson6_appendix_c_prandtl_meyer.json` |
| Module | Prandtl-Meyer |
| Source | as above |
| gamma | 1.4 |
| Columns | `nu`, `mu` — **printed in degrees**, converted on load |
| Rows | 168 |
| Values compared | 336 |
| Result | **336 PASS, 0 REVIEW** |
| Packaged | yes |

### NASA/TM-2006-214086 — Fanno

| | |
| --- | --- |
| File | `fanno_nasa_tm_2006_214086.json` |
| Module | Fanno |
| Source | Kevin J. Melcher, *User Guide for Compressible Flow Toolbox Version 2.1*, NASA Glenn Research Center, January 2006 |
| Kind | printed table in a public-domain government technical report |
| Located because | the supplied Anderson volume has **no Fanno appendix** |
| Table | Example 4.11, Table 4.3, report p. 38 |
| gamma | 1.4 |
| Cases | 6 Mach numbers, 30 values |
| Result | **30 PASS, 0 REVIEW** |
| Note | the printed column is the Fanning group `4 f_F L*/D`; under a Darcy reading every value would be four times smaller, so agreement confirms the convention and not merely the algebra |
| Packaged | yes |

### NASA/TM-2006-214086 — Rayleigh

| | |
| --- | --- |
| File | `rayleigh_nasa_tm_2006_214086.json` |
| Module | Rayleigh |
| Source | as above |
| Table | Example 4.24, Table 4.7 |
| gamma | 1.4 |
| Cases | 12 Mach numbers, 60 values |
| Result | **60 PASS, 0 REVIEW** |
| Packaged | yes |

### Nozzle cases constructed from published rows

| | |
| --- | --- |
| File | `nozzle_anderson6_constructed.json` |
| Module | nozzle |
| Source | Anderson Appendix A (pp. 1079-1083) and Appendix B (pp. 1085-1088) |
| Kind | **constructed** end-to-end cases, not a transcribed worked example |
| gamma | 1.4 |
| Cases | 7, covering all seven regimes; 18 expected values |
| Result | **18 PASS, 0 REVIEW** |
| Tolerance | derived, not chosen: each case re-solved at every corner of the published rounding box with an independent implementation |
| Packaged | yes |

**Why constructed.** The supplied volume has no nozzle appendix and no printed
back-pressure regime table, and Phase 4F was forbidden to invent one. Instead
each case's geometry and back pressure are *built out of* printed values, and
the expected answers are printed values from other rows. The strongest is the
internal-shock case: given only an area ratio and a back pressure assembled
from four printed numbers, the solver must rediscover Appendix A's M = 2.00
area ratio, Appendix B's M = 2.00 jump, and Appendix A's M = 0.40 exit.

**The limitation, stated.** These are published *station* values composed by
RocketForge. The composition is ours; every number in it is the book's.

## 2. How comparison works

* **No interpolation, ever.** A Mach number between two printed rows has no
  reference value, and the comparison says so rather than inventing one.
* **Tolerance comes from the source**, not from convenience: half a unit in the
  last printed significant figure, computed per value from its own magnitude.
* **The engine is self-tested.** `test_reference_engine_selftest.py` corrupts
  in-memory copies of the real tables by 1% and requires the comparison to
  report REVIEW; it also perturbs by 1e-9 and requires it *not* to. A digest
  check asserts the shipped files were never touched.
* **Published tables are never solvers.** No lookup, no interpolation, no
  fitting. Reference data is read in exactly one place — the comparison and its
  tests.

## 3. Known source anomalies

Four REVIEW results, all understood, all with the published value preserved.

| Source | Row | Quantity | Published | RocketForge | Classification |
| --- | --- | --- | --- | --- | --- |
| Anderson App. A, p. 1083 | M = 16 | `T0/T` | 52.29 | 52.20 | **suspected misprint** |
| Anderson App. A, p. 1083 | M = 7.8 | `p0/p` | 8285 | 8285.512 | rounding edge |
| Anderson App. B, p. 1087 | M1 = 5.9 | `p02/p01` | 0.0318 | 0.0317950 | rounding tie |
| Anderson App. B, p. 1087 | M1 = 6.9 | `p02/p01` | 0.0163 | 0.0163450 | rounding tie |

**The M = 16 misprint** is the clearest: `T0/T = 1 + 0.2 M^2` is exactly linear
in M^2, so at M = 16 it is exactly 52.2 with no rounding involved at all. All
216 other rows satisfy that identity at printed precision; this one is out by
18 half-units and its neighbours at M = 15 and M = 17 are both exact. The
digits appear transposed.

The other three are last-digit disagreements of about one half-unit — the
class of difference that appears whenever a value falls near a rounding
boundary.

**None is a RocketForge error, and none was tuned away.** The published values
stay as printed, the comparison reports REVIEW, and that is the correct
outcome.

## 4. The Phase 3 nozzle erratum

Not a dataset, but part of the same trail. Phase 4F found that `03` section
10.6's worked internal-shock example contradicts its own section 12.4
pseudocode, and that the example's numbers lose 38% of the mass flow across the
exit plane. See `ERRATUM_PHASE_3_NOZZLE_SHOCK_EXAMPLE.md`. The corrected values
are pinned as tests, and a second test asserts the incorrect ones are *not*
reproduced.

## 5. What is not used as a reference

* No anonymous web calculator.
* No value generated by RocketForge and later presented as published.
* No interpolated row.
* No textbook prose reproduced beyond numeric values and citation metadata.
