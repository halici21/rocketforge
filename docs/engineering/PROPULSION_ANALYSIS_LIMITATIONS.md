# Propulsion Analysis v1.0 — known limitations

Every entry is a deliberate boundary with a recorded reason. None is an
oversight, and none is hidden from the interface: each one that a user could
walk into is stated on the screen where they would walk into it.

---

## Thermochemistry

### Assigned-enthalpy liquid reactants

NASA CEA models the shipped liquid reactants — `O2(L)`, `CH4(L)`, `H2(L)` —
with an **assigned enthalpy** at a reference temperature rather than a
temperature-dependent one. A stream requested at 95 K is solved with the
enthalpy CEA assigns at 90.17 K.

The requested temperature is therefore recorded but does not enter the
calculation. This is reported as a **warning**
(`PROVIDER_ASSIGNED_ENTHALPY_REACTANT`) carrying both temperatures, and the
warning survives into Rocket Performance and into a trade study's aggregated
diagnostics, verified end to end in
`acceptance/phase_5g/assigned_enthalpy_chain.json`.

**Closed by the fluids foundation, as an opt-in policy.**
`ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION` adds
`h_fluid(T,p) − h_fluid(T_ref,p_ref)` from a validated fluid provider to CEA's
own assigned enthalpy, so the requested temperature reaches the chamber energy
balance while CEA keeps ownership of the chemical reference. See
[REACTANT_ENTHALPY_COUPLING_CONTRACT.md](REACTANT_ENTHALPY_COUPLING_CONTRACT.md).

The limitation above is **still exactly true of `PROVIDER_NATIVE`**, which
remains the default and reproduces every accepted Phase 5 result bit for bit;
the warning and this section stay for it. What has changed is that there is now
a second, validated way to ask the question.

Still deferred: liquid reactant temperature as a *trade-study design variable*.
The physics is now correct, but exposing it as a swept variable is a separate
decision with its own UI and cache implications.

### One production provider

NASA CEA v3 is the only production thermochemistry provider. The architecture
is provider-independent — the domain declares a protocol, the adapter
implements it, and no provider name appears below the application layer — but
there is one implementation. No provider selector is offered, because offering
a choice of one is a false choice.

Cantera remains a development-time oracle and a possible future kinetics path.
It is not a production provider and is not bundled.

### Five propellants

`LOX`, `LCH4`, `LH2`, `GOX`, `GCH4`. Phase 5C validated exactly these end to
end; a sixth would be a data-curation effort with its own provenance
requirements. The catalogue is not expanded to remove the limitation.

### Equilibrium chamber only

The chamber is solved at constant enthalpy and pressure, shifting equilibrium.
No finite-rate chemistry, and no non-adiabatic chamber.

---

## Ideal rocket performance

### Ideal means ideal

No efficiency factor of any kind: no c\* efficiency, no Cf efficiency, no
combustion efficiency, no divergence loss, no viscous or boundary-layer loss,
no separation correction, no two-phase term. Every figure is an **upper bound**
on a real engine, and the gap is several per cent.

The assumption list travels with every result and is a first-class panel in the
interface, not a footnote.

### Constant-property reduction

The model holds gamma and R fixed at the reduced chamber values through the
whole expansion. Real gas is calorically imperfect — cp varies with temperature
even at fixed composition — so this is a modelling choice, made explicit by
requiring a `GammaStrategy` and a `ChamberGammaBasis` with no default.

A consequence: no NASA CEA mode is exactly like-for-like. The nearest partner
is the frozen basis against CEA frozen-at-chamber, and the residual there is a
**closest cross-model difference**, not a validation residual.

### Three nozzle regimes

Overexpanded, ideally expanded and underexpanded — one internal solution
differing only in how p_e compares with p_a. An internal shock, a shock at the
exit plane, a choked subsonic diverging section and an unchoked nozzle are
different internal solutions and are refused by name.

### Mixed-phase chambers are refused, not averaged

Above `SINGLE_PHASE_CONDENSED_LIMIT` the single-gas reduction refuses. Such a
chamber still yields valid thermochemistry metrics; only a study requiring a
performance metric is unevaluable there.

---

## Trade study

### A sampled design space, not an optimiser

The engine evaluates a finite grid the user specified. There is no gradient
method, no genetic algorithm, no Bayesian or surrogate optimisation, and
nothing that searches. Consequently nothing claims a global optimum: the
wording is **best evaluated feasible point**, and a wording audit enforces it
over both the interface and every published controller property.

### A study-relative score

Weighted scoring is optional and off by default. When enabled it uses min–max
normalisation over the **feasible evaluated points of that study**, so the same
physical design scores differently in a study with a different range. That is a
property of the method and is stated wherever a score appears.

### A finite point cap

`MAX_STUDY_POINTS = 20 000`, chosen from measurement rather than taste: at the
cap the generic layer takes 4.73 s and 33 MB, and doubling to 40 000 triples
the total as the quadratic Pareto term turns. Exceeding it refuses the
definition and says by how much; it never samples a subset silently.

### Density impulse

**Closed by the fluids foundation.** `ρ_mix·c_eff` is computed from validated
stream densities at each propellant's own temperature, pressure and phase, and
is available as a trade-study objective. See
[DENSITY_IMPULSE_CONTRACT.md](DENSITY_IMPULSE_CONTRACT.md).

`density_hint` remains untouched by any calculation, exactly as before: it is
display-only reference metadata by Phase 5A/5B contract, and the AST audit that
asserts no module reads it now covers the fluids, coupling and propellant-metric
modules as well.

Still limited: the metric is available only for the three propellants with a
validated fluid model, and it is an additive-volume tank figure, not a stage
mass model.

### Model assumptions are not design variables

One study uses one provider, one chemistry mode, one database, one gamma
strategy and one gamma basis. Comparing two of any of those is two studies:
mixing them into one Pareto front would rank the models rather than the
designs.

---

## Packaging

The bundle audit walks every file and confirms what is present and absent, and
the packaged tours run the real workflows. That establishes **self-containment
of the bundle**, not verified clean-machine operation: no machine without the
development environment was used, and the report does not claim otherwise.

---

## Deferred work

| | |
| --- | --- |
| ~~Reactant enthalpy / fluid-property coupling~~ | **done** — CEA Provider v1.1 |
| ~~Validated liquid density / density impulse~~ | **done** — Propellant Metrics API v1.0 |
| Liquid reactant temperature as a design variable | the physics is now correct; exposing it as a swept variable is a separate decision |
| Methane viscosity validation | CoolProp and NIST use different correlations; blocks the hydraulic components |
| Fluid-device components: line, valve, orifice | `06` §8 step 2, the next roadmap step |
| Delivered-performance efficiency and loss models | c\* and Cf efficiency, divergence, viscous, boundary-layer |
| Real nozzle separation | the current flag is a rule of thumb, not a prediction |
| Finite-rate chemistry | between the frozen and equilibrium brackets |
| Additional production providers | the protocol exists; a second implementation does not |
| Expanded propellant catalogue | a data-curation effort with its own provenance requirements |
| Engine component design integration | injector, chamber geometry, cooling |
| Cycle analysis | pumps, turbines, feed system, balances |
