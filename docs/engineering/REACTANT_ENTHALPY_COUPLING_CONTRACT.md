# Reactant enthalpy coupling — contract

**Status:** implemented and validated as part of **NASA CEA Provider v1.1**.
Closes the assigned-enthalpy limitation carried since Phase 5C.

---

## The limitation this closes

Several of NASA CEA's reactant entries — the cryogenic liquids among them —
carry a single **assigned enthalpy** at one reference condition instead of a
temperature-dependent fit. CEA accepts a different temperature for those and
then ignores it.

Measured, not assumed. `cea.Mixture(["O2(L)"]).calc_property(ENTHALPY, [1.0],
[T])` returns bit-identical values at every T in the declared range, and a
LOX/LCH4 chamber solved at an oxidiser temperature of 86 K, 90.17 K, 95 K and
98 K returned **the same chamber temperature to the last bit** in all four
cases: 3598.2854205339845 K.

Until now RocketForge reported that honestly and stopped there
(`PROVIDER_ASSIGNED_ENTHALPY_REACTANT`). It now corrects it.

---

## The equation

```
h_corrected(T, p) = h_CEA,assigned(T_ref, p_ref)
                    + [ h_fluid(T, p) − h_fluid(T_ref, p_ref) ]
```

**CEA keeps ownership of the chemical/formation reference. The fluid provider
contributes only the sensible increment.**

### Why a difference and never an absolute

A property library's enthalpy zero is its own convention:

| Fluid | CoolProp at NBP | NASA CEA assigned |
| --- | --- | --- |
| O₂(L) | −133 398 J/kg | −405 609 J/kg (= −12 979 J/mol) |
| CH₄(L) | −84 J/kg | −5 562 302 J/kg (= −89 233 J/mol) |
| H₂(L) | ~0 J/kg | −4 470 504 J/kg (= −9 012 J/mol) |

The CEA column is the formation enthalpy of the substance; the CoolProp column
is measured from an arbitrary reference state. They differ by 272 kJ/kg for
oxygen. **Injecting one into the other would silently redefine the formation
enthalpy of oxygen** and produce a chamber temperature that is wrong by
hundreds of kelvin while looking entirely plausible.

What *is* transferable between two conventions is a difference between two
states of the same fluid from the same provider, where both conventions cancel
exactly. A test asserts the two data remain far apart, so that an absolute
injection could never pass unnoticed as a small discrepancy.

---

## The reference state

`T_ref` is **not** read from a docstring. It comes from
`assigned_enthalpy_temperature()`, which determines it empirically: evaluate
the reactant at two temperatures inside its declared range and see whether the
answer moves. If it does not, the enthalpy is assigned, and the assigned
condition is the midpoint of the declared range.

| Reactant | T_ref | p_ref |
| --- | --- | --- |
| `O2(L)` | 90.17 K | 101 325 Pa |
| `CH4(L)` | 111.643 K | 101 325 Pa |
| `H2(L)` | 20.27 K | 101 325 Pa |

`p_ref = CEA_REFERENCE_PRESSURE = 101325.0` Pa — one standard atmosphere,
declared as a named constant in one place. That is the condition CEA's liquid
reactant entries are stated at, and each of the three is a saturated or
slightly subcooled liquid there, which is what makes the reference state a real
state rather than a label. Verified: CoolProp reports all three as `liquid` at
1 atm and their own T_ref.

Every consumer must use the same p_ref, or the two conventions do not cancel.

---

## Which reactants are corrected

**Only those whose CEA entry is assigned-enthalpy.** The gate is the measured
`assigned_enthalpy_temperature()`, not a list of names.

| Reactant kind | Correction | Why |
| --- | --- | --- |
| assigned-enthalpy liquid | **applied** | CEA ignores the temperature; the increment supplies what is missing |
| temperature-dependent (the gases) | **none** | CEA already evaluates the enthalpy at the given temperature; adding an increment would count the same energy twice |
| no validated fluid model | **none** | there is nothing to compute the increment from, and a surrogate would be a physical claim |

The gas case is asserted directly: with both reactants bound to a fluid *and*
the corrected policy active, GOX/GCH4 returns **zero corrections** and a
bit-identical chamber. That is the double-counting test.

---

## Where the correction is applied

At the mixture, in J/kg of propellant:

```
Δh_mix = Σ w_i · Δh_i          w_i from O/F, summing to one
```

then added to the enthalpy CEA computed for its own reactants, before the HP
constraint is formed:

```python
corrected = mixture_enthalpy + chamber_input.enthalpy_correction
constraint = enthalpy_argument(corrected, cea_module.R)
solver.solve(solution, cea_module.HP, constraint, pressure_bar, weights)
```

This is the **official API path the adapter already used**: `EqSolver.solve`
with an `HP` constraint has always taken a caller-supplied enthalpy. No text
parsing, no `thermo.lib` edit, no hidden global state.

**Why the mixture rather than each reactant.**
`Mixture.calc_property(ENTHALPY, weights, temperatures)` returns the
mass-fraction-weighted specific enthalpy in J/kg — established by measurement,
not assumed: it reproduces CEA's own published assigned values exactly
(O₂(L) −12 979 J/mol, CH₄(L) −89 233 J/mol, H₂(L) −9 012 J/mol, CH₄ gas
−74 600 J/mol), and the mixture value reproduces the mass-weighted sum of the
single-reactant values to **0.025 J/kg in 1.58 × 10⁶** — the residue of CEA's
float32 weight vector, which returns an O/F of 3.4 as 3.400000095367432.

Because that combination is linear in the mass fractions, adding one number to
the mixture enthalpy is algebraically identical to correcting each reactant and
re-mixing, and it leaves CEA's own weights untouched.

---

## The two policies

```python
class ReactantEnthalpyPolicy(StrEnum):
    PROVIDER_NATIVE = "provider_native"
    FLUID_SENSIBLE_CORRECTION = "fluid_sensible_correction"
```

`PROVIDER_NATIVE` is exactly what CEA does alone — including ignoring the
temperature and including the original warning. It reproduces every accepted
Phase 5 result bit for bit, which is what makes old results still reproducible.

`FLUID_SENSIBLE_CORRECTION` is the new mode. It requires a fluid provider and a
binding per reactant; neither is defaulted, because a silently chosen property
model would change the chamber temperature without appearing in the request.

**The policy is recorded in provenance under both policies**, so no result is
ever silent about which reactant-energy model produced it.

---

## Pressure

`ReactantFluidBinding` requires a `pressure`, and it is the **stream's own**
feed pressure.

**Chamber pressure is not feed pressure.** They are different states, and until
feed-system physics exists the feed pressure must be an explicit input. A
static audit asserts that no module in this phase passes a chamber pressure
into a fluid request, with a negative control that fires on the substitution.

The practical consequence is not theoretical: at a feed pressure of 1 atm, a
LOX stream requested at 95 K is a **gas**, and the correction is refused by
name rather than computed on the wrong branch.

---

## What is validated

`acceptance/fluids_foundation/reference_state_identity.json`

| Check | Result |
| --- | --- |
| At `(T_ref, p_ref)`: every increment | **exactly 0.0** |
| At `(T_ref, p_ref)`: native vs corrected | **bit-identical** on T, R, M̄, γ_fr, γ_eq |
| At `T_ref`, 3 bar | +288.2 and +105.5 J/kg → ΔT +0.0218 K. A real pressure term, preserved |
| Oxidiser sweep 86 → 98 K, native | one chamber temperature, identical at every point |
| Oxidiser sweep 86 → 98 K, corrected | strictly monotone; Δh −6955 J/kg at 86 K |
| GOX/GCH4 with bindings and corrected policy | 0 corrections, bit-identical |
| Element balance | provider post-validation passed on every corrected solve |

The reference-state identity is **bit-exact and cannot be otherwise**: at the
reference state every increment is exactly zero, and zero times any weight is
zero, so the float32 weight residue cannot reach it.

---

## Provenance

Every corrected reactant records: reactant name, fluid, requested T and p, CEA
reference T and p, `h_fluid` at both states, the increment, the fluid provider,
its version and its backend. Enough to recompute the correction independently,
which is the test a provenance record has to pass.

The diagnostic `REACTANT_ENTHALPY_FLUID_CORRECTED` **supersedes**
`PROVIDER_ASSIGNED_ENTHALPY_REACTANT` rather than dropping it: under the
corrected policy the old warning is gone and the new record is present, and a
test asserts both halves.

---

## Limitations

* Three fluids. A propellant without a validated fluid model receives no
  correction and says so.
* Single-phase liquid only. A two-phase or gaseous state at the requested
  condition is refused, not interpolated.
* The increment is a **sensible enthalpy** term. It does not model a change of
  phase, a heat of solution, or ortho/para hydrogen conversion.
* CoolProp and NASA CEA are two independent models. The correction makes the
  reactant *state* right within CEA's chemistry; it does not reconcile the two
  models, and no claim is made that it does.
