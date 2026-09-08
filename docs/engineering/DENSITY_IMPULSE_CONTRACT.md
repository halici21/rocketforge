# Density impulse — contract

**Status:** implemented and validated. Owner:
`rocketforge.engineering.propellants` (**PROPELLANT METRICS API v1.0**, frozen).

---

## Where it lives, and why not in `physics.fluids`

Density impulse is **not** fundamental fluid physics, not thermochemistry and
not nozzle physics. It is a derived propulsion/design metric about a *stage*: it
consumes a fluid state, a mixture ratio and a RocketForge performance figure,
and owns none of them.

So it sits in an L2 engineering package, one layer above the property model it
reads. `physics.fluids` answers "what is the density of oxygen at 95 K and
3 bar"; this answers "what volume does a tank of LOX and LCH4 at O/F 3.4
occupy, and how much impulse comes out of it".

---

## O/F orientation

**Oxidiser mass divided by fuel mass**, as everywhere else in this program and
as in NASA CEA. Stated here explicitly because the mass fractions below invert
if it is read the other way, and a bulk density computed from an inverted ratio
is wrong but not absurd.

---

## Stream densities

Each stream's density comes from a `FluidPropertyProvider` at that stream's own
**temperature, pressure and phase**:

```python
stream_density(provider, binding, temperature, pressure) -> StreamDensity
```

* The pressure is the caller's and has **no default**. It is a feed-system
  state; the chamber pressure is a different state entirely, and using it here
  would evaluate liquid oxygen at 100 bar because that number happened to be in
  scope.
* The binding states the phase the model is validated for, and a state found in
  another phase is refused rather than converted.
* **`density_hint` is never read.** It remains display-only reference metadata
  by the Phase 5A/5B contract. An AST audit over every module of this phase
  asserts it, with a two-way negative control.

---

## Bulk propellant density

Under the **additive-volume** approximation:

```
w_f  = 1 / (1 + O/F)
w_ox = (O/F) / (1 + O/F)

1/ρ_mix = w_f/ρ_f + w_ox/ρ_ox

⇔  ρ_mix = (1 + O/F) / (1/ρ_f + (O/F)/ρ_ox)
```

Unit: **kg/m³**.

### What it means, and what it does not

It is the mass of propellant divided by the volume it occupies **in two
separate tanks**. It is *not* the density of a mixture of the two, which is not
a thing that exists at these conditions.

The assumptions travel with every result, as
`ADDITIVE_VOLUME_ASSUMPTIONS`, and are shown wherever the number is:

* the two propellants are stored in separate volumes;
* the tank volumes add: `V = m_f/ρ_f + m_ox/ρ_ox`;
* no chemical mixing — this is not the density of a LOX/fuel solution;
* no ullage volume;
* no tank structure, insulation or residuals;
* no thermal stratification: one temperature per stream.

---

## Density impulse

```
I_d = ρ_mix · c_eff
```

Unit: **kg/(m² s)**, equivalently **N·s/m³** — impulse per unit propellant
*volume*, which is what makes it the metric for a volume-limited stage.

Because `c_eff = Isp · g₀` by RocketForge's own definition, the identity

```
I_d = ρ_mix · Isp · g₀
```

must also hold, and it is **checked on every instance**: the record carries a
`residual`, and the acceptance cases all report `0.0`.

`c_eff` is the canonical input, because density impulse is naturally volumetric
effective exhaust momentum. `Isp` is taken as well so the two spellings can be
*compared* rather than assumed equal.

### There is deliberately no second metric called `ρ·Isp`

`ρ·Isp` and `ρ·Isp·g₀` differ by a factor of 9.80665 and have different units.
One name for two things is how the two get confused, so only the quantity
defined above exists, and a test asserts no field named for the other appears.

`g₀` is `rocketforge.core.constants.STANDARD_GRAVITY` = 9.80665 — the same
constant the performance layer uses, never a second copy.

---

## Availability

Density impulse is available only when **both** streams have a validated
density. If either does not:

* the metric is **absent**, not estimated;
* a trade study that *requires* it marks that point `NOT_EVALUABLE`, which is
  the honest verdict and is a different thing from `INFEASIBLE` — Phase 5F's
  semantics, unchanged;
* nothing falls back to `density_hint`, and nothing substitutes a surrogate.

`PRODUCTION_FLUID_MAPPING` binds `LOX → OXYGEN`, `LCH4 → METHANE`,
`LH2 → HYDROGEN`. `RP-1` is **not** mapped and is not in the production
catalogue at all: it is not a pure fluid, and choosing n-dodecane or a kerosene
surrogate for it would be a physical claim needing its own contract and its own
validation. Asking for it raises `UnmappedPropellantError` by name.

The mapping is explicit and provenance-bearing. **No string-prefix inference**:
nothing asks whether `"O2" in name`, which would map `O2(L)`, `GOX` and a
hypothetical `O2/N2` blend to one fluid and be wrong about the third.

---

## Trade Study integration

Density impulse is available as a first-class trade-study objective, and
**TRADE STUDY API v1.0 was not modified to allow it**. The frozen
`engine.studies` package is generic: it takes metrics from whatever the
evaluator returns, and its metric *table* lives in the application layer, which
no freeze manifest covers. Registering the metric needed no version bump.

Four metrics are registered at the performance stage: `fuel_density`,
`oxidiser_density`, `bulk_propellant_density`, `density_impulse`.

**Fluid evaluation cost is two calls per study, whatever the point count.** A
study varies O/F, chamber pressure, area ratio and ambient pressure — none of
which changes a propellant's tank temperature or its feed pressure — so the
stream states are fixed for the whole study. Measured: 410 design points,
41 chemistry solves, **2** fluid evaluations.

---

## Validation

| Check | Result |
| --- | --- |
| ρ_mix against a hand-computed case (400, 1200, O/F 3) | **800.0** exactly, written down before running |
| I_d against a hand-computed case | **2 400 000.0** kg/(m² s) exactly |
| `ρ_mix·c_eff` against `ρ_mix·Isp·g₀` | residual **0.0** on every case |
| ρ_mix between the two component densities | asserted |
| Equal densities give that density at any O/F | asserted |
| Density responds to stream temperature | 86 K > 90.17 K > 98 K, monotone |
| Cached study metric vs direct recomputation | **160 comparisons, 0 differences**, exact equality |
| Density and chemistry read the same requested state | asserted field by field |
| `density_hint` reached by any of it | **no**, AST audit with negative control |

Artifacts: `density_impulse_cases.json`, `direct_solve_parity.json`,
`state_snapshot_consistency.json`, `integrated_density_study.json`.

---

## What this is not

Density impulse is a **physical/engineering derived metric**. It is not a score,
not a weighted objective and not a penalty. A trade study may use it as an
objective, and its numerical value exists independently of the decision layer —
the same separation Phase 5F froze.

It also says nothing about tank mass, structural fraction, insulation,
boil-off or stage sizing. It is one term a volume-limited stage cares about,
not a stage model.
