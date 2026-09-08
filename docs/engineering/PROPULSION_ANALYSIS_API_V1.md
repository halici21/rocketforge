# Propulsion Analysis v1.0 — FROZEN

How the four frozen contracts compose into one propulsion-analysis stack, what
each one owns, and what the whole is and is not.

This document does not restate the individual APIs. Each has its own frozen
document, linked below.

---

## The chain

```
  COMPRESSIBLE v1                 frozen at Phase 4G, 22 files byte-identical
        |                         quasi-1D gas dynamics; knows no rocket
        v
  THERMOCHEMISTRY API v1.0        the chamber state, provider-independent
        |                         NASA CEA v1.0 implements it, behind the boundary
        v
  IDEAL ROCKET PERFORMANCE v1.0   c*, Cf, F, c_eff, Isp — RocketForge's own
        |                         over frozen Compressible, never restating it
        v
  TRADE STUDY API v1.0            design space, constraints, objectives, Pareto
        |                         no physics of its own; no rockets in the core
        v
  application/                    the composition root; the only provider wiring
        |
        v
  ui/                             presentation; no equation, no decision algorithm
```

Each arrow is one way. A nozzle is usable without a study around it; a study is
testable without a rocket behind it; the domain is usable without the provider
that implements it.

| Contract | Version | Files | Document |
| --- | --- | --- | --- |
| Thermochemistry API | 1.0 | 13 | [THERMOCHEMISTRY_API_V1.md](THERMOCHEMISTRY_API_V1.md) |
| Ideal Rocket Performance API | 1.0 | 6 | [ROCKET_PERFORMANCE_API_V1.md](ROCKET_PERFORMANCE_API_V1.md) |
| Trade Study API | 1.0 | 12 | [TRADE_STUDY_API_V1.md](TRADE_STUDY_API_V1.md) |
| NASA CEA Provider | 1.0 | 11 | [CEA_PROVIDER_CONTRACT.md](CEA_PROVIDER_CONTRACT.md) |
| Compressible Flow API | 1.0 | 22 | [COMPRESSIBLE_FLOW_API_V1.md](COMPRESSIBLE_FLOW_API_V1.md) |

Manifests and digests: `acceptance/phase_5g/freeze_manifest.json`.

---

## What each layer owns, and what it must never own

| Layer | Owns | Must never own |
| --- | --- | --- |
| `physics.compressible` | area–Mach, choked flow, shocks, nozzle regimes | anything named c\*, Cf, thrust or Isp |
| `physics.thermochemistry` | the chamber state and the provider protocol | any provider, any nozzle, any performance figure |
| `providers.cea` | the CEA mapping and its scientific decisions | the definition of a RocketForge performance quantity |
| `engineering.chamber` | the single-gamma reduction, made explicit | a default gamma choice |
| `engineering.nozzle` | c\*, Cf, F, c_eff, Isp | chemistry, or a second copy of the gas dynamics |
| `engine.studies` | constraints, feasibility, objectives, Pareto, score | any physics, any provider, any Qt |
| `application` | wiring, formatting, orchestration | any equation |
| `ui` | presentation | any equation, any decision algorithm |

**One owner per equation.** A static test asserts that no module outside
`engineering/nozzle/performance.py` defines a function named
`characteristic_velocity`, `thrust_coefficient`, `specific_impulse` or
`effective_exhaust_velocity`.

---

## The three questions, and the three workspaces

| Workspace | Question |
| --- | --- |
| **Thermochemistry** | What chamber state does the chemistry model predict for these propellants at this mixture ratio and pressure? |
| **Rocket Performance** | What ideal propulsion performance follows from that state through this nozzle into this ambient? |
| **Trade Study** | How do evaluated designs compare under explicit objectives and constraints? |

They stay separate. Merging them into one screen would merge three questions
with three different owners and three different kinds of uncertainty.

---

## The scientific contract, stated once

### Chamber (thermochemistry)

Adiabatic equilibrium at constant enthalpy and pressure. The state carries
**two** isentropic exponents — γ_s for a shifting expansion and cp/cv for a
frozen one — several per cent apart. Nothing in the public API is a bare
`gamma`.

### Performance (RocketForge)

```
c*          = sqrt(R T0) / Γ(γ)            = p_c·A_t / ṁ
Cf_momentum = V_e / c*
Cf_pressure = ((p_e − p_a) / p_c) · ε       signed, never clamped
Cf          = Cf_momentum + Cf_pressure    = F / (p_c·A_t)
F           = ṁ·V_e + (p_e − p_a)·A_e      = Cf·p_c·A_t
c_eff       = F / ṁ                        = Cf·c*
Isp         = c_eff / g₀                    in SECONDS
```

Every one of those identities is recomputed and checked on each result;
the worst residual across the acceptance matrix is **0.0**.

**Ideal** means: steady, one-dimensional, inviscid, adiabatic nozzle,
isentropic shock-free expansion, constant-property gas. No efficiency of any
kind is applied, so every figure is an upper bound on a real engine.

### Decision (trade study)

These are **not** physics:

```
feasible          every hard constraint satisfied
dominates(A, B)   A no worse on every objective, strictly better on one
score             Σ wᵢ · normalise(objectiveᵢ)   over the feasible set
```

A score is study-relative. A front is over a sampled grid. Neither is a
property of an engine.

---

## The distinctions the stack exists to preserve

| | |
| --- | --- |
| physics result ≠ objective | a metric is a number; wanting more of it is a decision |
| objective ≠ constraint | one orders, the other excludes |
| constraint ≠ penalty | satisfied or violated; never a score deduction |
| infeasible ≠ failed | a violated limit and an unsolved model are different verdicts |
| warning ≠ failure | a caveat does not withhold a number |
| Pareto ≠ score | dominance never sees a weight |
| ideal ≠ delivered | no efficiency, no loss, no separation model |
| provider c\*/Cf/Isp ≠ RocketForge's | the first is an oracle, the second is the answer |
| reporting threshold ≠ physics threshold | one decides what is printed, the other what is refused |

---

## Provenance

Every integrated result is traceable end to end. From a single trade-study
point one can recover: the study fingerprint, the design-variable values, the
thermochemistry request, the provider and its version, the thermodynamic
database and its SHA-256, the chamber state, the gamma strategy and basis, the
performance model, the nozzle and ambient condition, the raw metrics, and the
objectives, constraints and scoring definition that judged them.

Reconstruction is verified, not asserted:
`acceptance/phase_5g/provenance_chain.json` rebuilds one point from its
recorded provenance and compares.

Provenance is read from the **result's own snapshot**. Editing the interface
cannot relabel a stored result.

---

## Changing a frozen contract

* **Additive** within v1: a new function, a new enum member, a new optional
  field with a default. Regenerate the manifest.
* **Breaking**: a removed or renamed symbol, a reordered dataclass field, a
  changed unit, a changed default, a changed scientific meaning. Requires a
  version bump and a re-run of the validation that supports it.
* **A defect fix that changes a number** is a scientific change even when no
  signature moves: regenerate the evidence and record the change.

The provider is versioned separately from the domain it implements, so a
provider fix does not reopen the Thermochemistry API.

---

## Known limitations

See [PROPULSION_ANALYSIS_LIMITATIONS.md](PROPULSION_ANALYSIS_LIMITATIONS.md).
Every one is a deliberate boundary with a recorded reason, not an oversight.
