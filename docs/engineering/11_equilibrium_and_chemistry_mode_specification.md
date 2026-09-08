# 11 — Equilibrium and Chemistry Mode Specification

What "equilibrium" means at the chamber, what it means during an expansion, what
"frozen" means, where the two bracket reality, and what happens when a product
condenses.

**Status:** specification. This document defines the physical meaning of every
mode; `13` defines how each is verified.

---

## 1. Why the modes exist at all

A rocket chamber is not a beaker. The gas leaves it in roughly a millisecond,
expanding through a pressure ratio of 50 to 1000 while its temperature falls by
thousands of kelvin. Chemistry that is instantaneous at 3500 K and 10 MPa is not
instantaneous at 1200 K and 30 kPa.

So there is no single correct chemical description of a nozzle flow. There are
two limits that *are* well defined:

| Limit | Assumption | Physically |
| --- | --- | --- |
| **Equilibrium (shifting)** | chemistry is infinitely fast | composition re-equilibrates at every point |
| **Frozen** | chemistry is infinitely slow | composition is fixed at some upstream station |

Reality lies between them. RocketForge computes both limits, labels which is
which, and **never presents either as "the" answer** (`15` §3). Their separation
is itself the useful engineering output: a wide gap means the chemistry
assumption matters for this design, a narrow one means it does not.

The alternative — finite-rate kinetics — is out of scope for v1 (§9).

---

## 2. The mode enums

```python
class ChemistryMode(Enum):
    """How chemistry is treated when the chamber state is computed."""
    EQUILIBRIUM = "equilibrium"

class ExpansionMode(Enum):
    """How chemistry is treated during expansion."""
    EQUILIBRIUM = "equilibrium"          # shifting: re-equilibrate at each station
    FROZEN = "frozen"                    # composition fixed at the chamber
    FROZEN_AT_THROAT = "frozen_at_throat"  # equilibrium to the throat, then frozen
```

`ChemistryMode` has one member deliberately. The chamber is computed at
equilibrium; there is no "frozen chamber", because freezing requires a prior
composition to freeze *at*, and upstream of the chamber there are only
unreacted propellants. The enum exists so that provenance always carries a
chamber mode field and so that a future kinetic mode has somewhere to go.

`ExpansionMode` is Phase 3's name, used in `01` §5's `expand()` signature.

---

## 3. The chamber: the HP problem

### 3.1 Statement

> **Given** the reactants, their amounts (via O/F), their temperatures and
> phases, and the chamber pressure p_c:
> **find** the product composition and temperature at chemical equilibrium such
> that enthalpy and pressure are unchanged from the reactants.

```
    H(products, T_c, p_c, x_eq)  ==  H(reactants, T_inj, p_c)
    p                            ==  p_c                        (specified)
    element balance                                             (doc 09, section 3.2)
    Gibbs free energy minimised at (T_c, p_c)
```

The result is the **adiabatic flame temperature at constant pressure**, and the
equilibrium composition there. This is CEA's `problem hp` and Cantera's
`equilibrate('HP')`.

### 3.2 Why HP and not something else

The three candidate constraint pairs give three different answers, and choosing
wrongly is a silent error of hundreds of kelvin.

| Problem | Holds constant | Models | Right here? |
| --- | --- | --- | --- |
| **HP** | enthalpy, pressure | a steady-flow reactor at fixed pressure | **yes** |
| UV | internal energy, volume | a sealed constant-volume bomb | no — the chamber is not sealed; it flows |
| TP | temperature, pressure | an isothermal reactor | no — nothing holds the temperature |

The chamber is a steady-flow device: propellant enters, product leaves, and no
work is done on or by the gas between injection and the nozzle entrance. The
steady-flow energy equation with no work and no heat loss conserves **stagnation
enthalpy**, and the chamber's velocity is low enough that stagnation and static
enthalpy are close. Pressure is set by the throat and the mass flow, not by the
chemistry. Hence H and p, hence HP.

A constant-volume (UV) calculation would give a noticeably *higher* temperature
because none of the energy goes into the flow work of pushing product out. That
number is correct for a bomb calorimeter and wrong for a rocket.

### 3.3 The enthalpy on the left-hand side

Two properties of the reactant enthalpy make or break this calculation, and both
were fixed in `09`:

* **it is on the absolute datum** — elements in their reference states at
  298.15 K (`09` §3.4). Reaction energy *is* the difference between product and
  reactant formation enthalpies; on a relative datum that difference is
  meaningless;
* **it is evaluated at the actual injection condition**, not at 298.15 K
  (`09` §4.4). LOX at 90 K carries measurably less enthalpy than notional LOX at
  298 K, including the enthalpy of vaporisation if the datum species is gaseous,
  and that difference shows up directly in T_c.

A calculation that gets either wrong produces a flame temperature that is wrong
by a plausible-looking amount and will pass every internal consistency check.
`13` §5's datum-sanity test exists specifically to catch it.

### 3.4 Adiabatic, and honest about it

HP assumes no heat loss. A real chamber loses heat to the walls, and a
regeneratively cooled engine returns some of it in the fuel. RocketForge:

* computes the **adiabatic** value, which is the standard and comparable
  quantity;
* labels it adiabatic wherever it is shown (`15` §3);
* accounts for regenerative preheating **through the reactant temperature**,
  which is the physically correct channel and is already in the contract
  (`09` §9.3) — not by adjusting the flame temperature afterwards;
* does not apply an efficiency factor inside physics. A c\* efficiency is an
  `engineering` concern (`14` §2), applied where performance lives and visibly.

### 3.5 T₀, not T

The temperature that comes out of the chamber HP problem is the **stagnation**
temperature for the nozzle flow that follows, because it was computed from
stagnation enthalpy. `ChamberGas.temperature` is therefore T₀, exactly as
`06` §4.1's handshake diagram labels it. This is stated because `GasStation`
carries *static* temperature, and one letter's confusion between the two would
propagate through the entire expansion.

---

## 4. The two gammas

For a reacting mixture, two different quantities are both called γ, and they are
not equal.

| Symbol | Definition | Equals |
| --- | --- | --- |
| γ_frozen | cp/cv at **fixed** composition | the classical ratio of specific heats |
| γ_s | −(∂ ln p / ∂ ln v)_s | the **isentropic exponent** of the reacting mixture |

They coincide when composition cannot shift — that is, in frozen flow. In
equilibrium flow they differ, because part of any compression or expansion goes
into shifting the composition rather than into raising or lowering the
temperature. CEA prints the isentropic exponent as `GAMMAs`; the distinction is
visible in its output and is easy to lose in an adapter.

The contract, restating `09` §7.1:

* `ChamberGas.gamma` and `GasStation.gamma` hold **the exponent appropriate to
  the mode that produced the state**;
* the mode is in provenance, and a state without provenance may not enter the
  compressible handshake (`12` §4);
* the difference is material — for hot, highly dissociated products it is a
  several-per-cent effect on γ, which moves exit conditions by far more than any
  tolerance in this project;
* `13` §5 requires a test that the two are *distinguishable* on a case where
  dissociation is strong. An adapter that reports cp/cv for both modes would
  pass every other test in the suite and fail this one.

The same distinction applies to the speed of sound, and it matters at the
throat: the equilibrium sound speed is lower than the frozen sound speed,
because a medium whose composition can shift in response to a pressure
disturbance is more compressible than one whose composition cannot. The sonic
point therefore sits at a different condition in the two modes, which is why
`throat()` is a provider call and not an application of the frozen module's
`p/p₀ = (2/(γ+1))^(γ/(γ−1))` (`09` §9.2).

---

## 5. Expansion: the SP problem

### 5.1 Statement

An ideal nozzle expansion is adiabatic and reversible, hence **isentropic**. So
every station is found by holding entropy at the chamber value and specifying
the pressure:

```
    s(station)  ==  s(chamber)
    p           ==  p_station        (specified)
```

which is CEA's `problem sp` and Cantera's `equilibrate('SP')`. What differs
between the modes is only **whether the composition is allowed to change while
that is done**.

### 5.2 Equilibrium (shifting) expansion

Composition is re-solved at every station. As the gas cools, dissociated species
recombine — H + OH → H₂O, CO + ½O₂ → CO₂ — and recombination is exothermic. The
released energy raises the temperature above what a fixed-composition expansion
would give, and the extra enthalpy is available to the flow.

Consequences, each of which is a testable expectation (`13` §5):

* exit temperature is **higher** than frozen at the same pressure ratio;
* exit velocity and specific impulse are **higher** than frozen;
* mean molar mass **rises** during expansion as light dissociated fragments
  recombine into heavier stable species;
* γ_s varies along the expansion and is not the chamber value.

This is the **upper bound** on performance for a given propellant pair and
pressure ratio.

### 5.3 Frozen expansion

Composition is fixed at the chamber value and carried unchanged to the exit. The
mixture is then an ordinary non-reacting gas mixture: its cp is the
mole-weighted sum of the species' cp values, and γ = cp/cv.

* recombination energy is never released, so exit temperature is **lower**;
* mean molar mass is **constant** by construction;
* γ still varies with temperature, because species cp values do — frozen does
  **not** mean constant γ. This distinction matters for `12` §5.

This is the **lower bound**.

**`composition is None` on a frozen `GasStation` means "the chamber's
composition", not "unknown"** (`09` §8). Phase 5B must not render it as missing
data.

### 5.4 Frozen at the throat

Equilibrium from the chamber to the throat, frozen from the throat to the exit.

The physical argument: recombination rates scale with density and temperature,
both of which are high up to the throat and fall rapidly after it. Real nozzle
flows tend to stay near equilibrium through the converging section and the
throat, then depart from it in the diverging section. Freezing at the throat is
the standard way to approximate that without kinetics, and it usually sits
closer to measured performance than either pure limit.

It is offered as a **named, explicitly chosen mode** — never as a default that
quietly splits the difference. A user who picks it has chosen a physical
assumption, and the UI says which one (`15` §3).

### 5.5 What is bracketed, and how it is presented

Equilibrium and frozen bracket the real answer. RocketForge's obligation is to
present that honestly:

* both bounds are computable side by side, and `15` §3 encourages showing them
  together;
* neither is labelled "the" performance;
* the **gap between them** is a first-class output, because it tells the user
  whether the chemistry assumption matters for their design;
* no interpolation between the two is offered. A blended number would have no
  physical basis and would be exactly the kind of invented value this project
  refuses.

---

## 6. Mode consistency rules

Rules that Phase 5B enforces at the type level or with explicit checks:

1. **A chamber state and an expansion mode must be compatible.** Expanding a
   `ChamberGas` whose provenance says it was computed in one mode using
   assumptions from another is a construction error, not a warning.
2. **All stations of one expansion share one mode.** A result set never mixes
   equilibrium and frozen stations, except in `FROZEN_AT_THROAT`, where the
   transition station is explicit and labelled.
3. **The mode is in provenance on every state**, so a state can always answer
   what it assumed.
4. **A provider that does not declare a mode's capability must raise** rather
   than substitute a mode it does support (`10` §4). Silently giving frozen
   results when equilibrium was requested is the worst available failure, since
   the numbers look right and are systematically low.

---

## 7. Condensed phases

### 7.1 When they appear

Solid or liquid products form in cases that are not exotic:

* **aluminised solid propellants** — Al₂O₃ is a major product by mass, often
  around a third of it;
* **very fuel-rich hydrocarbon operation** — solid carbon (soot);
* **metallised or exotic formulations** generally;
* **boron, beryllium and similar additives**.

### 7.2 Why they are a problem here, specifically

A condensed phase breaks assumptions that the rest of RocketForge's chain is
built on:

* **The frozen compressible module is a single-phase perfect gas model.** A
  two-phase flow is not a perfect gas, and no choice of γ makes it one.
* **Condensed mass does not expand.** It contributes mass and momentum but not
  pressure work, so the effective performance is lower than a gas-only
  calculation implies.
* **Thermal and velocity lag.** Particles do not stay at the gas temperature or
  velocity; real two-phase-flow losses depend on particle size, which is not in
  any of these data models.
* **The condensed species may itself change phase** during the expansion — Al₂O₃
  freezes in the nozzle, releasing its heat of fusion.

None of this can be recovered by "using the mixture γ". A single-γ two-phase
model is wrong in a way that no tolerance covers.

### 7.3 The policy

> **Condensed phases are detected, reported, and refused as input to the
> single-phase compressible handshake. They are never silently averaged into a
> gas.**

Concretely:

| Situation | Behaviour |
| --- | --- |
| Provider reports no condensed species | normal path |
| Provider reports condensed species, fraction available | `ChamberGas.condensed_mass_fraction` is set; a `Diagnostic` records it; the state is valid *as chemistry* |
| That state is offered to the compressible handshake | **refused** by `12` §4's precondition, with a diagnostic naming the fraction and why |
| Provider cannot report whether condensed species are present | treated as **unknown, not absent** — the handshake is refused, because "it did not say" is not "there are none" |
| User wants a gas-only approximation anyway | only via an explicit, named, labelled choice — never a default; see §7.4 |

The refusal threshold is a declared constant, not a magic number, and it is not
zero: trace condensed fractions at the 1e-6 level are numerical noise in a
provider's species list, not a two-phase flow. `13` §4 fixes the value and the
justification; the principle is that the threshold is *stated*, and that a
result near it says so rather than flipping silently between two behaviours.

### 7.4 The escape hatch, and its guard rails

There is a legitimate engineering use for a gas-phase-only estimate with the
condensed mass excluded. If Phase 5B offers it:

* it is an explicit mode with a name that says what it does — not a fallback;
* the discarded mass fraction is reported alongside every number it produces;
* the result is labelled an estimate that omits two-phase effects, everywhere it
  appears, including in any export;
* it is never selected automatically.

This mirrors the tabulated provider (`10` §5.3): a limited method is acceptable
when it is chosen deliberately and labelled honestly, and unacceptable when it
is a silent substitute for a better one.

---

## 8. The refusal rule, stated generally

`08` §10 promised this rule; here it is in full:

> **A state that the downstream model cannot represent is refused, not
> approximated.**

The chemistry layer is allowed to produce states the rest of RocketForge cannot
consume — a two-phase equilibrium is a legitimate chemical result. What is
forbidden is passing such a state into a model whose assumptions it violates and
letting the model return a number anyway.

This is the same principle as the compressible module refusing a Prandtl–Meyer
turn beyond ν_max, an oblique shock beyond θ_max, or a Fanno duct longer than
its choking length. In each case the honest output is a refusal with a reason,
and in each case the temptation is a plausible-looking number. The chemistry
layer inherits the rule because it is the same failure.

---

## 9. Not in v1: finite-rate kinetics

Finite-rate chemistry would compute what actually happens between the two
limits, by integrating species production rates along the nozzle.

**Excluded from v1**, for reasons of scope rather than value:

* it requires a validated **reaction mechanism**, not just thermodynamic data,
  and mechanism selection is a research judgement with a large effect on the
  answer;
* it turns the expansion into a stiff ODE integration coupled to the flow
  solution — a different numerical problem from anything RocketForge currently
  solves, and one where an in-house integrator would need its own validation
  campaign;
* it needs a nozzle geometry and a residence-time distribution, which would pull
  `engineering` concerns into `physics` and break `08` §4;
* validating it needs experimental data, not published tables — a materially
  harder V&V problem than `13` sets out.

The architecture leaves room: `ExpansionMode` is an enum that can gain a member,
provider capabilities already declare per-mode support, and nothing in the data
model assumes exactly two limits. What Phase 5A refuses to do is half-build it —
the same discipline ADR-14 applied when it rejected a partially wired
variable-γ path in the compressible module.

---

## 10. Mode summary

| Mode | Composition | Bounds | Use |
| --- | --- | --- | --- |
| Chamber `EQUILIBRIUM` | solved at T_c, p_c | — | the only chamber mode |
| `EQUILIBRIUM` expansion | re-solved at each station | upper bound | ideal performance |
| `FROZEN` expansion | fixed at chamber | lower bound | conservative estimate |
| `FROZEN_AT_THROAT` | equilibrium to throat, then fixed | between | closest single-assumption approximation |
| finite-rate | integrated | — | **not in v1** (§9) |
