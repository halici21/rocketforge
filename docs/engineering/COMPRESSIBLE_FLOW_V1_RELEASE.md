# Fundamental Compressible Flow — v1.0 Release Note

**Status: ACCEPTED / FROZEN, 2026-09-02.** The subsystem is complete, verified,
packaged, and checked by hand in the shipped executable — 56 of 56 manual items
PASS, including all seven blocking honesty checks. See
`acceptance/phase_4g/MANUAL_EXE_RELEASE_CHECKLIST.md`.

---

## What this is

A calorically perfect gas-dynamics library, and the interface that exercises it.
Ten modules, built over Phases 4A-4F and audited in 4G:

* **PerfectGas** — gamma, R, cp, cv, speed of sound
* **Isentropic** — the four ratios, the sonic references, the Mach angle, three
  closed-form inverses
* **Area-Mach** — A/A* and its two-branch numerical inverse
* **Mass flow** — MFP, Gamma, mass flux, choking, the critical ratios
* **Normal shock** — the jump relations, the pitot ratio, four inverses
* **Prandtl-Meyer** — nu, nu_max, expansion and compression turns
* **Oblique shock** — theta-beta-M, theta_max, weak and strong roots
* **Fanno** — adiabatic duct friction and its choking length
* **Rayleigh** — heat exchange, thermal choking, both critical points
* **C-D nozzle** — three critical pressure ratios, seven back-pressure regimes,
  internal shock location, and the distributed solution

Every one of them is usable from a plain Python prompt with no interface
running. Nine worked examples in `examples/compressible/` demonstrate the
public API, and they are executed by the test suite so they cannot rot.

## What it assumes

Steady, one-dimensional (quasi-one-dimensional for the nozzle), inviscid,
calorically perfect: constant gamma, constant R. Adiabatic except in Rayleigh
flow. Isentropic except across a shock, in Fanno flow, and in Rayleigh flow.

## What it does not model

Variable gamma · real-gas behaviour · reacting, frozen or equilibrium chemistry ·
viscous losses · boundary layers · finite shock thickness · flow separation ·
shock-boundary-layer interaction · turbulence · multidimensional flow ·
external plumes · combustion.

And, deliberately, no rocket performance: no thrust, no thrust coefficient, no
characteristic velocity, no specific impulse, no nozzle efficiency, no discharge
coefficient. Those belong to an engineering layer that will call this one.

## How it was validated

**Against published tables.** 2 320 printed values from six datasets — Anderson's
Appendices A, B and C, two NASA/TM-2006-214086 tables, and seven nozzle cases
constructed from printed rows. 2 316 PASS. The four REVIEW results are
documented source anomalies, chief among them a transposed digit in Appendix A's
M = 16 row; the published values are preserved and nothing was tuned to match
them.

**Against itself.** 593 cross-module identity tests over four gammas: the
mass-flow parameter against the area relation, the shock against the ideal gas
law and against the isentropic module, the shock as a Fanno-Rayleigh
intersection, the expansion as an isentropic process, the oblique shock as a
normal shock at its normal component, and the nozzle against everything it
composes.

**Against its own contract.** A machine-readable API snapshot, enforced by 84
tests: signatures, result fields, enum values, immutability, the absence of
default branches and of any hidden gas.

**In total.** 5 285 tests, run twice with identical results, one skip (an
optional SciPy oracle).

## What is frozen

Public symbol names, argument meaning, branch semantics, units, result-field
meaning, ratio orientation and status meaning — the surface described in
`COMPRESSIBLE_FLOW_API_V1.md`. Implementation may still change; the contract
may not, except through a version bump or a recorded erratum.

Frozen 2026-09-02 at manifest digest
`8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502`
(22 physics and core files, listed in `acceptance/phase_4g/ACCEPTANCE_MANIFEST.md`).

## Known limits

Documented in `COMPRESSIBLE_NUMERICAL_LIMITS.md`. In short: most of these
relations are flat at the sonic point, so inverting them near M = 1 resolves a
Mach number to about 1e-6 rather than 1e-15. The oblique roots merge within 1%
of theta_max. Nozzle back pressures closer than 1e-9 of a threshold are not
distinguished. These are properties of the equations in double precision, not
defects, and the module says so rather than implying more precision than it has.

## Known source anomalies

Four, all pinned and explained in `COMPRESSIBLE_REFERENCE_INDEX.md` §3: one
suspected misprint and three last-digit rounding edges in the published tables.
Separately, `ERRATUM_PHASE_3_NOZZLE_SHOCK_EXAMPLE.md` records a worked example
in the project's own specification whose numbers violate continuity; the
implementation follows the specification's pseudocode, and tests reject the
incorrect values.

## Documents

| Document | What it answers |
| --- | --- |
| `COMPRESSIBLE_FLOW_API_V1.md` | what may be depended on |
| `COMPRESSIBLE_FLOW_THEORY_MAP.md` | how the modules relate |
| `COMPRESSIBLE_REFERENCE_INDEX.md` | where every published number came from |
| `COMPRESSIBLE_VALIDATION_MATRIX.md` | what kind of evidence backs each capability |
| `COMPRESSIBLE_NUMERICAL_LIMITS.md` | what float64 can and cannot resolve here |
| `COMPRESSIBLE_PERFORMANCE_BASELINE.md` | how fast it is, on one machine |
| `ERRATUM_PHASE_3_NOZZLE_SHOCK_EXAMPLE.md` | the specification erratum |

## Runtime dependencies

PySide6 for the interface, numpy for the backend. Nothing else. SciPy is a
development-only cross-validation oracle and is not installed by
`requirements.txt`.
