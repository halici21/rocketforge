# NASA CEA solid-propellant representation — research

Phase A of Solid Propellant Thermochemistry R1. No production code was written
before this document existed.

## Source hierarchy actually used

**Level 1 — primary, and unusually strong here.** The `cea` 3.3.4 distribution
installed in this project's production profile ships the **official NASA
RP-1311 worked examples** as runnable code, at
`.venv-cea/Lib/site-packages/cea/samples/rp1311/example1.py … example14.py`,
together with the authoritative API type stub at `cea/lib/libcea.pyi` and the
thermodynamic database at `cea/data/thermo.lib`.

This matters: rather than reading a description of CEA's input semantics and
inferring an implementation, the semantics below are read off NASA's own
example inputs and the shipped API contract, and every number quoted was
produced by running them on this machine.

**Level 2/3** were not needed to answer the blocking questions and are not
cited for any claim below. Where a statement is inference rather than
documented fact, it is marked **[inference]**.

Everything in this document is reproducible with:
`.venv-cea/Scripts/python.exe <path>/samples/rp1311/example5.py`

## The governing example: RP-1311 Example 5

`samples/rp1311/example5.py`, docstring verbatim:

> Example 5 from RP-1311
> - HP equilibrium for a solid propellant blend
> - Includes one custom reactant (CHOS-Binder) not present in thermo.lib

This is a composite AP / binder / aluminium propellant, and it answers most of
the blocking questions on its own.

| Ingredient | Mass fraction | CEA representation |
| --- | --- | --- |
| `NH4CLO4(I)` | 0.7206 | built-in `thermo.lib` species |
| `CHOS-Binder` | 0.1858 | **custom `cea.Reactant`** |
| `AL(cr)` | 0.0900 | built-in |
| `MgO(cr)` | 0.0020 | built-in |
| `H2O(L)` | 0.0016 | built-in |
| **Total** | **1.0000** | |

The custom ingredient, verbatim from the example:

```python
cea.Reactant(
    name="CHOS-Binder",
    formula={"C": 1.0, "H": 1.86955, "O": 0.031256, "S": 0.008415},
    molecular_weight=14.6652984484,
    enthalpy=-2999.082,
    enthalpy_units="cal/mol",
    temperature=298.15,
)
```

Output, run on this machine at 34.023 atm:
`Tc = 2723.021 K · MW = 22.290 · gamma_s = 1.1928 · AL2O3(L) = 0.036724 mole
fraction`.

## The blocking questions

### A — How does CEA define a multi-component reactant mixture?

**Documented fact.** As an ordered list of species handed to `cea.Mixture`,
with a parallel vector of weights. From `libcea.pyi:233`:

```python
class Mixture:
    def __init__(self, species: list[str | Reactant] | None = None,
                 products_from_reactants: bool = False,
                 omit: list[str] = ..., ions: bool = False) -> None: ...
```

The list accepts **built-in species names and custom `Reactant` objects
interchangeably**, which is exactly how Example 5 mixes `"NH4CLO4(I)"` with a
constructed `CHOS-Binder`.

There is no fuel list and no oxidiser list at this level. The mixture is one
list of reactants.

**Consequence:** a formulation of N ingredients is native to CEA. Nothing has
to be invented for RocketForge to express one.

### B — Mole, mass, or wt%? How are they normalised?

**Documented fact.** The solver's native currency is a **weights vector**.
`libcea.pyi:546` — `RocketSolver.solve(self, soln, weights, pc, ...)`, and
`EqSolver.solve(soln, problem, h0_over_R, p, weights)` as used in Example 5.

Example 5 passes `weights = [0.7206, 0.1858, 0.09, 0.002, 0.0016]` and
comments them `# wt fractions`. They sum to exactly 1.

Conversions are explicit helpers, not implicit behaviour —
`Mixture.moles_to_weights`, `Mixture.weights_to_moles`,
`Mixture.of_ratio_to_weights`, `Mixture.chem_eq_ratio_to_of_ratio`
(`libcea.pyi:245-251`).

**Consequence:** mass fraction is the right canonical internal basis for a
formulation; it is what CEA consumes, with no conversion layer.

### C — Initial reactant temperatures

**Documented fact.** A parallel vector, one temperature per reactant, used to
evaluate the mixture enthalpy that becomes the HP constraint. Example 5:

```python
T_reac = np.array([298.15]*5)
h0 = reac.calc_property(cea.ENTHALPY, weights, T_reac)
solver.solve(solution, cea.HP, h0 / cea.R, p, weights)
```

Temperatures are therefore **per ingredient**, not per formulation. Example 8
uses genuinely different ones per reactant (`[20.27, 90.17]` for LH2/LOX).

### D — Condensed reactant phases

**Documented fact.** Encoded in the species name suffix, from `thermo.lib`:
`(cr)` crystalline, `(L)` liquid, `(I)`/`(II)`/`(III)` crystal phase numbers,
`(a)`/`(b)` allotropes, `(gr)` graphite. Example 5 alone uses `(I)`, `(cr)`
and `(L)`; Example 13 uses `Be(a)`; Example 11 uses `Li(cr)`.

There is no separate phase field — **the phase is part of the identity**.

**Consequence [inference]:** RocketForge must treat the CEA name as the
identity and must not try to derive phase by parsing chemistry, but it may
surface the suffix as a displayed phase.

### E — Ingredients absent from thermo.lib

**Documented fact.** Constructed as a `cea.Reactant`. Verified absent from the
shipped `thermo.lib` in this install: **HTPB, PBAN, CTPB, GAP — zero matches**.
This is not a gap to work around; it is why `Reactant` exists, and why NASA's
own solid example defines its binder rather than naming one.

### F — What a custom ingredient must carry

**Documented fact**, `libcea.pyi:189-208`:

| Field | Meaning |
| --- | --- |
| `name` | label, arbitrary |
| `formula` | elemental stoichiometry, `{"C": 1.0, "H": 1.86955, ...}` |
| `molecular_weight` | per formula unit |
| `enthalpy` | heat of formation / assigned enthalpy |
| `enthalpy_units` | e.g. `"cal/mol"` — **explicit, never assumed** |
| `temperature` | the reference temperature the enthalpy belongs to |

**Consequence:** these six fields are exactly the provenance a RocketForge
ingredient must carry for a custom reactant, and every one of them must come
from the benchmark source rather than be fabricated.

### G — How are polymeric binders represented?

**Documented fact.** As custom reactants carrying an **empirical formula per
unit carbon**, not as a named polymer. NASA's own binder in Example 5 is
`C 1.0 · H 1.86955 · O 0.031256 · S 0.008415` with MW 14.665 — that is one
carbon's worth of polymer, not a monomer or a chain.

Verified: no HTPB/PBAN/CTPB/GAP entry exists in the shipped `thermo.lib`.

**Consequence:** the honest RocketForge representation of HTPB is a
`USER_DEFINED_CEA_REACTANT` whose formula and enthalpy are cited to a source.
A silent `HTPB -> CHx` surrogate is exactly what section 13 of the brief
forbids, and there is no built-in to fall back on.

### H — How are gaseous and condensed products reported?

**Documented fact, two mechanisms.**

1. **By name suffix in the composition.** Example 5's output lists
   `AL2O3(L) 0.036724` in the same mole-fraction mapping as `CO`, `H2`, `HCL`.
   The phase is in the name.
2. **By count on the solution object.** `num_condensed` and `num_gas` are
   properties of the solver/solution (`libcea.pyi:307, 543, 674, 826`).

**Consequence:** condensed products are *not* a separate output channel — they
arrive interleaved with gases and must be split by RocketForge on the phase
suffix. Losing that split is the failure section 19 of the brief names, and it
would be easy to cause by flattening the mapping.

### I — Chamber equilibrium vs equilibrium vs frozen expansion

**Documented fact.** Three distinct things, three distinct API paths:

| Case | API |
| --- | --- |
| Chamber HP equilibrium only | `EqSolver` + `solve(soln, cea.HP, h0/R, p, weights)` — Example 5 |
| Rocket, equilibrium expansion | `RocketSolver.solve(...)` with `n_frz=None` — Examples 8, 9 |
| Rocket, frozen expansion | same call with `n_frz=<station index>` — Example 12, `n_frz=2` (frozen from the throat) |

`iac: bool = True` selects the infinite-area combustor; Example 9 shows the
finite-area (FAC) form via `ac_at`.

**Consequence:** equilibrium and frozen are one integer apart in the same
call, which makes it trivially easy to report one as the other. They must be
carried as distinct, labelled results — never merged.

### J — Which CEA rocket outputs are usable as reference data?

**Documented fact**, from `RocketSolution` (`libcea.pyi:576+`): `T`, `P`,
`density`, `M`, `MW`, `enthalpy`, `entropy`, `gibbs_energy`, `gamma_s`,
`cp_eq`, `cp_fr`, `cv_eq`, `cv_fr`, `Mach`, `sonic_velocity`, `ae_at`,
`c_star`, `coefficient_of_thrust`, `Isp`, `Isp_vacuum`, `mole_fractions`,
`num_condensed`.

**Consequence:** `c_star`, `coefficient_of_thrust`, `Isp`, `Isp_vacuum` are
available and are precisely the quantities RocketForge also computes itself.
That overlap is the reason sections 21-22 of the brief insist they be stored
as *reference*, never as RocketForge's answer.

### K — Why CEA theoretical performance is not delivered performance

**Documented fact from the model's own construction**, plus **[inference]** on
the consequences. CEA solves a one-dimensional, adiabatic, chemical-equilibrium
(or frozen) expansion of a homogeneous working fluid from a stagnation
chamber. It therefore contains no combustion inefficiency, no heat loss to the
walls, no boundary layer, no divergence loss, no finite-rate chemistry, no
erosive burning, and — most significantly for a metalised solid — **no
particle lag or two-phase flow loss**, even though it will happily report a
condensed phase like the `AL2O3(L)` above.

**Consequence:** a metalised solid propellant is exactly the case where
theoretical and delivered Isp diverge most, and it is the case this program's
first benchmark exercises. The label required by section 25 is not a
formality.

## What this establishes for the architecture

1. A multi-ingredient formulation is **native** to CEA; nothing must be
   invented, and no bipropellant O/F is required. Example 5 reports
   `o/f 0.000` and solves correctly.
2. The canonical internal basis should be **mass fraction summing to 1**,
   because that is what the solver consumes.
3. **Per-ingredient temperature** is required, not a single case temperature.
4. A custom ingredient needs six provenance-backed fields, all citable.
5. Condensed products must be **split from gases by name suffix**, and a
   `num_condensed` count is available as a cross-check.
6. Equilibrium and frozen expansion must be **separate labelled results**.
7. CEA's `c_star` / `Cf` / `Isp` are **reference data**, structurally separate
   from RocketForge's own performance chain.

## Existing architecture — where O/F is actually assumed

Audited with file/line evidence, not inferred (section 7).

```
ChamberEquilibriumRequest            requests.py:83-85
    fuel: PropellantStream
    oxidiser: PropellantStream       <- role-checked, requests.py:100-107
    oxidiser_fuel_ratio: MixtureRatio
        |
build_chamber_input()                mapping.py:282
        |  splits into DISJOINT weight vectors
        v
CEAChamberInput                      mapping.py:100-103
    fuel_weights / oxidiser_weights  mapping.py:323-324
    of_ratio  (must be > 0)          mapping.py:116-117   <- blocks a solid case
        |
solve_chamber_raw()                  mapping.py:393
        |
    reactants.of_ratio_to_weights(ox, fuel, of)   mapping.py:413-416
        |  ONE weights vector from here on
    reactants.calc_property(ENTHALPY, weights, T) mapping.py:417-419
        v
    CEA EqSolver
```

**The finding that shapes the whole design:** `of_ratio_to_weights` is a
*constructor* for the weights vector, and nothing downstream of line 416 ever
sees `of_ratio` again. Enthalpy evaluation, the solver call, the parser and
the chamber result are already reactant-count-agnostic — they consume
`weights` and `reactant_temperatures` and nothing else.

RP-1311 Example 5 confirms this from the other side: it never builds an O/F
at all, passes a 5-element weights vector straight to the solver, and CEA
reports `o/f 0.000` while solving correctly.

| Layer | Verdict |
| --- | --- |
| `ChamberEquilibriumRequest` | **bipropellant-specific** — requires two role-checked streams and a MixtureRatio |
| `CEAChamberInput` | **bipropellant-specific** — `of_ratio > 0` is enforced at `mapping.py:116` |
| `solve_chamber_raw` from line 417 onward | **reusable unchanged** |
| enthalpy evaluation, solver call | **reusable unchanged** |
| parser, `ChamberGas`, species, composition | **reusable unchanged** [inference, to be proven in Phase E] |
| `Phase`, `Composition`, `CompositionBasis`, `Species` | **reusable unchanged** |

The additive boundary is therefore narrow and well-defined: a second request
type and a second input builder that supplies `weights` directly, joining the
existing path at the point where O/F has already been discarded.

## Phase A gate (section 58)

| Gate item | Status |
| --- | --- |
| CEA solid-formulation input semantics documented | **YES** — Mixture accepts a list of names and custom Reactants |
| wt% / mass semantics documented | **YES** — weights vector, mass fractions summing to 1 |
| custom reactant semantics documented | **YES** — six fields, `libcea.pyi:189-208` |
| condensed output semantics documented | **YES** — phase in the name suffix, plus `num_condensed` |
| equilibrium / frozen rocket semantics documented | **YES** — `n_frz`, `iac`, `ac_at` |
| at least 3 valid benchmark candidates found | **QUALIFIED — see below** |
| each benchmark's missing data identified | **YES** — `acceptance/solid_propellant_r1/benchmark_inventory.json` |

### The qualification, stated plainly

Three candidates meet the section 28 bar for NUMERICAL_VALIDATION, and all
three are official NASA RP-1311 cases that run on this machine. But only
**one of them — Example 5 — is a solid propellant.** The other two validate
mechanisms this feature needs (multi-reactant weights with a condensed
reactant and a condensed insert; the frozen/equilibrium separation) rather
than a solid formulation.

Both independent solid-propellant sources found (Nakka KNDX and KNSU) fail
section 28 for concrete, individually listed reasons: their outputs come from
PROPEP rather than CEA, their product tables are published only as images,
and neither publishes a heat of formation for its sugar — which is fatal,
because sucrose and dextrose are **not** in `thermo.lib` (verified), so the
custom reactant cannot be constructed from those sources at all.

Section 27 asks for coverage including **Case A, a simple non-metalized solid
formulation.** No NUMERICAL_VALIDATION source for that case was found. It
cannot be manufactured: section 3 forbids an assistant-invented composition,
and section 29 forbids reverse-engineering a formulation from plotted
performance.

**Consequence for the program.** Section 34 forbids passing a benchmark on
chamber temperature alone, and section 77 question 7 asks whether published,
direct-CEA and RocketForge values agree across benchmarks. With one
solid-propellant numerical benchmark, that question can be answered honestly
for a metalized AP/binder/Al composite and for the underlying mechanisms —
but not for a non-metalized solid, and not for solid *reference rocket
performance*, because Example 5 defines no expansion.
