# Solid Propellant Thermochemistry — Phase 1

A thermochemistry foundation, not a motor. Phase 1 extends the accepted R1
(formulation → CEA HP chamber equilibrium → gas and condensed products →
provenance) with three things: the custom-reactant contract the scope asks
for, the CEA equilibrium characteristic velocity, and a comparison layer for
reference cases.

**Not in scope, and not claimed:** motor Isp, thrust, thrust curve, Pc(t),
nozzle expansion, internal ballistics. Rocket Performance still refuses a solid
chamber.

## Decisions

| | Decision | Where it lives |
| --- | --- | --- |
| D1 | Molecular weight optional; origin recorded as `provided` or `derived` | `CustomReactant.molecular_weight_origin`, and provenance |
| D2 | Equilibrium c\* in the UI, titled "CEA equilibrium characteristic velocity", with its limitations, not under a performance heading | `ThermoCalculator.qml` solid block |
| D3 | R1 committed as its own baseline first | `9c64a3b` |
| D4 | Frozen c\* refused; equilibrium c\* only where convergence and validity checks pass | `rocketforge/providers/cea_solid/cstar.py` |

## Commits

| Commit | Step |
| --- | --- |
| `9c64a3b` | Solid Propellant Thermochemistry R1 (baseline) |
| `7825c27` | custom reactant contract with optional molecular weight |
| `d321af6` | CEA equilibrium characteristic velocity |
| `333f2d3` | reference-case comparison layer |
| `b29153a` | c\* in the Thermochemistry workspace |

## The custom-reactant contract

Required: chemical formula, heat of formation with its units, reference
temperature, source. Optional: molecular weight. No binder preset exists; see
`SOLID_PROPELLANT_MISSING_DATA.md` for what is missing and why.

The molecular weight is not cosmetic when a source states it. Without it CEA
derives one from the formula, and for NASA's Example 5 binder that moves the
chamber temperature by −0.0287 K (−1.05e−05 relative), which is enough to
miss the published value. The reference case therefore keeps the stated one.

## CEA equilibrium characteristic velocity

c\* is a chamber-and-throat quantity. CEA reports it only from its rocket
solver, which will also hand back Isp, a thrust coefficient and exit
conditions. So the rocket solver is confined to one module (`cstar.py`), and
that module is tested to read only the chamber temperature, `c_star` and the
two convergence signals.

What was measured, and what each finding decided:

| Finding | Consequence |
| --- | --- |
| Example 5 c\* is bit-identical at exit pressure ratios of 10, 34.47 and 500 | a nominal ratio is passed to the solver and nothing at the exit is read |
| Frozen from the chamber, Example 5 does not converge (`converged=False`, `last_error=8`), yet CEA still returns 1515.91 m/s | no frozen option exists; a non-converged solve is refused with its reason, never shown as a number |
| The rocket solve's chamber T differs from the HP solve's by 2.6e−11 | the two are cross-checked at 1e−6; a c\* is never paired with a chamber it was not computed from |
| Giving CEA a different starting condensed phase moves c\* by 2.1e−06 | c\* is shown to six significant figures, never more |
| With 16.8 % of the mass condensed, CEA's c\* treats condensed products as moving and exchanging heat with the gas with no lag | stated beside the value every time, with the mass share |

Example 5: **1525.68 m/s** (1525.679777841417), bit-identical to direct CEA.

**The one surprise.** Example 13's c\* reproduces NASA's printout only with the
`BeO(L)` insert NASA's run uses. Its throat sits at exactly 2851.000 K,
beryllium oxide's melting point, where the solution depends slightly on the
starting phase. RocketForge passes no insert and prints 6386.74 against 6386.75
ft/s. The comparison layer reports this as `differs`, which is true, and the
case notes explain it; it is not tolerated away.

**A tooling finding.** The first version detected non-convergence by recording
CEA's warning. Recording a warning raised from CEA's compiled code left 45
extension types uncollectable at interpreter shutdown. This was reproduced
with raw CEA and no RocketForge code, and suppressing the warning instead
avoids it. Convergence is now read from the solution itself.

## The comparison layer

`rocketforge/comparison` is a registered architecture layer that may import
only `core` and `physics`. It compares values it is handed; it cannot run a
solver, so a comparison can never quietly produce the number it checks. It is
named `comparison` because `validation` already means input guarding in this
codebase.

What a comparison may conclude depends on the source:

| Source kind | Verdict |
| --- | --- |
| direct CEA | `agrees` / `differs`, at the case's stated tolerance (usually exactly) |
| NASA printout | `agrees` / `differs`, within half the last printed digit |
| independent code (PROPEP, EXPLO5) | differences only, reported as `compared` |
| experiment | differences only, with the stated uncertainty carried alongside |

Nothing in the layer ranks references or picks a best one, and a test checks
that no such helper exists. A verdict case missing any quantity RocketForge
does not report is `incomplete`, not `agrees`. Units convert with exact factors
only. There is no mole/mass basis conversion: the basis is part of each
quantity's key, so a mole fraction can never be compared with a mass fraction.

External cases enter as plain data through `case_from_mapping`, which requires
source, code and code version, and refuses unknown fields.

`rocketforge/comparison/rp1311.py` is **generated** from NASA's shipped
Examples 5, 12 and 13, run unmodified, with every value at its printed
precision. A test regenerates it byte for byte.

Two guards were found vacuous while building this, and fixed:

- An unregistered top-level package is exempt from every architecture layer
  rule, because the checker returns no layer for it. `comparison` is
  registered, and a synthetic violation proves the rules now reach it.
- The R1 guard against reading Isp from a CEA solution matched `.Isp[` on
  tokenised code, which reads `. Isp [`, so it could never fire. A negative
  control exposed it, and the guard was rewritten.

## Results

| Comparison | Quantities | Verdict |
| --- | --- | --- |
| Example 5 vs NASA printout (Class A) | 50: 10 scalars and all 40 printed species | agrees; tightest row at 0.995 of its bound |
| Example 5 vs direct CEA | 208: T, MW, γ and all 205 species | agrees, bit for bit |
| Example 5 c\* vs direct CEA | 1 | identical |
| Example 12 vs NASA printout (Class B) | chamber p, T, c\* | agrees |
| Example 13 vs NASA printout (Class B) | chamber p, T, c\* | p and T agree; c\* differs, cause measured and recorded |

## Gates, at every step

- both freeze manifests untouched;
- A / solid / A: the canonical bipropellant digest is unchanged before and
  after a solid solve;
- full suites in both environments;
- zero Qt warnings in the captures, which were inspected directly.

Final state: 7274 passed / 2 skipped (`.venv-cea`), 7049 passed / 224 skipped
(base `.venv`).

## Limitations

See `SOLID_PROPELLANT_MISSING_DATA.md` for the full record. In short:

- one solid end-to-end benchmark;
- no non-metalised solid benchmark;
- no solid expansion benchmark, and no published solid c\*;
- no PROPEP, EXPLO5 or experimental data yet (the import path exists);
- no element balance for most solid products.

At 1366×768, the c\* readout sits below the fold in the result column's
scrollable readouts, like the other readouts on this layout; its heading is
visible.

## Next, and not started

Solid Propellant Performance (R1.1) still needs an authoritative solid
expansion benchmark before any Isp, C_f or expansion output. Internal
ballistics comes after that. Neither starts automatically.
