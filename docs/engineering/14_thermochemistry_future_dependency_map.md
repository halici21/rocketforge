# 14 — Thermochemistry Future Dependency Map

What consumes this layer, in what order it gets built, where the iteration
loops are, and one conflict with Phase 3's stated sequence that the project
owner must settle.

This document extends `06` for the chemistry branch. It does not replace it.

---

## 1. `PHASE_3_SPEC_CONFLICT` — provider sequencing

**Reported before any implementation, as the standing rule requires.**

| Source | Statement |
| --- | --- |
| `06` §8 step 3 | "`physics.thermochemistry` interfaces **+ a CEA provider**" |
| `10` §5 (this phase) | Cantera is the proposed primary solver; CEA is a developer-side validation oracle and is **not shipped** |

**The scope of the conflict is narrow.** Phase 3 anticipated Cantera
throughout: `01` §3's planned layout reserves `providers/cantera/` alongside
`providers/rocketcea/`, and `06` §2 defines `providers.*` as "adapters onto
CoolProp / CEA / Cantera / tables". So Phase 3 does not exclude Cantera. What it
does say is that the **CEA provider is the one built at step 3**.

Phase 5A's reasoning for the other order is in `10` §5.1–5.2 and rests on facts
measured on this machine on 2026-09-03: Python 3.13.12 on Windows, no Fortran
toolchain, a PyInstaller-shipped application, and RocketCEA's compiled Fortran
extension whose cp313 Windows wheel availability is unconfirmed. Alongside that
sits an independence argument: if CEA is the runtime solver, CEA can no longer
be the independent standard it is validated against.

**Phase 3 wins, and Phase 5A does not overrule it.** This is recorded as
blocking open question **OQ-2**, and the recommended Phase 5B scope (§3) is
written so that **the provider decision is made by a spike whose outcome the
owner rules on** — not assumed by the specification. No code commits to either
provider until that ruling.

Nothing else in this document depends on which way it goes: the protocol, the
data model and the validation plan are provider-agnostic by construction, which
is the property that makes the question safe to defer.

---

## 2. Who consumes this layer

```
    physics.thermochemistry  (ChamberGas, GasStation, provider protocol)
              |
              +--> engineering.chamber
              |        - the gamma-strategy adapter (doc 12 section 8)
              |        - L*, contraction ratio, residence time
              |        - c* efficiency (an engineering factor, never in physics)
              |
              +--> engineering.nozzle
              |        - thrust, Cf, c*, Isp                       (ADR-15)
              |        - delivered performance from the equilibrium
              |          expansion, NOT from the single-gamma path (doc 12 s.7)
              |
              +--> engineering.cooling
              |        - hot-gas composition and transport for the gas-side
              |          correlation; a Bartz-type correlation wants the real
              |          product gas, not air
              |
              +--> engine.balances / engine.cycles
              |        - chamber conditions as a boundary condition for the
              |          whole power balance
              |
              +--> application.*
                       - provider selection, mode choice, provenance display
```

`engineering.injector` is deliberately **absent** from this list. An injector
sizes orifices from mass flow, density and pressure drop — `physics.fluids`
questions (`06` §4.2). It needs the mixture ratio, which is a number it is
given, not a chemistry calculation it performs.

---

## 3. Build order

Refines `06` §8 step 3 into executable steps. Steps 0–2 are provider-agnostic
and can proceed **regardless of how OQ-2 is decided**, which is why they come
first.

| Step | Work | Depends on | Gate |
| --- | --- | --- | --- |
| **0** | **Provider spike** — install candidate(s) on Python 3.13/Windows, run one HP case, freeze a PyInstaller bundle containing it, measure size and startup | nothing | a written finding; **owner rules on OQ-2** |
| **1** | Data model: `Species`, `PropellantDefinition`, `PropellantStream`, `Mixture`, `MixtureRatio`, `ChamberGas`, `GasStation`, provenance | `core` | T1 structural tests green |
| **2** | Protocol + capabilities + a **stub provider**; in-tree oracle; T2 invariants with mutation proofs | step 1 | G1, G2 — green with **no** library installed |
| **3** | The chosen provider adapter | step 0 ruling, step 2 | T3, T4 against transcribed references |
| **4** | `engineering.chamber` handshake adapter, γ strategies, error quantification | step 3, frozen compressible | T6 coupling; frozen manifest unchanged |
| **5** | `engineering.nozzle` performance: c\*, Cf, Isp | step 4 | performance references |
| **6** | UI: propellant selection, mode choice, provenance, refusals (`15`) | step 5 | zero QML warnings; honesty checks |
| **7** | Second provider adapter → T5 cross-provider | step 3 | measured spread documented (G7) |

**Steps 1 and 2 are the ones to start on.** They are the majority of the design
risk, they are testable on this machine exactly as it is configured today, and
they are unaffected by OQ-2. Step 0 runs in parallel because it is an
investigation, not a commitment.

**Step 2 before step 3 is deliberate.** Writing the invariants and their
mutation proofs against a stub, before any real provider exists, means the tests
are built to catch defects rather than fitted to whatever the first provider
happens to return. Reversing the order is how a test suite ends up ratifying an
implementation instead of checking it.

---

## 4. Iteration loops

Chemistry introduces the first genuinely coupled loops in the project. Each is
named here so it is designed rather than discovered.

### 4.1 Chamber pressure ↔ mass flow (inner, tight)

```
    p_c  ->  ChamberGas  ->  c*  ->  mdot = p_c A_t / c*
      ^                                       |
      +---------------------------------------+
```

For a **fixed** p_c this is not a loop at all — it is one evaluation. It becomes
a loop only when the feed system sets the flow and the chamber sets the
pressure. Converges quickly because c\* is weakly dependent on p_c.

**Each iterate is an equilibrium solve**, so it is expensive. `10` §9's caching
question applies: memoising on the exact input tuple is safe and valuable, and
the compressible module's `lru_cache` on nozzle criticals is the precedent —
including its cache-correctness test proving no cross-case leakage.

### 4.2 Regenerative cooling ↔ reactant temperature (outer, slow)

```
    fuel injection temperature  ->  ChamberGas  ->  hot-gas state
              ^                                          |
              |                                    heat into coolant
              +------------------------------------------+
```

The physically correct channel for regenerative preheating (`11` §3.4): heat
returns to the cycle by raising the reactant temperature, which is an input to
the HP problem — not by adjusting a flame temperature afterwards.

This loop is slow and weakly coupled, and it is the one most likely to be run
open-loop in early versions. That is acceptable; what is not acceptable is
running it open-loop while presenting the result as coupled.

### 4.3 Mixture ratio ↔ performance (a study, not a solve)

Sweeping O/F to find peak Isp is an **outer study** over independent solves. It
belongs in `engine.studies` (`08` §3), not in the chemistry layer.

Worth stating because peak-Isp O/F is a headline number and there is a standing
temptation to compute it inside the layer that knows the chemistry. Two reasons
not to: the optimum depends on the *expansion*, so it is a performance question,
not a chemistry one; and the peak is broad and shifts with pressure ratio and
chemistry mode, so an unqualified "optimum O/F" would be a number without its
conditions attached.

### 4.4 What must never become a loop

**The chemistry must not iterate with the frozen compressible module.** No
scheme where `nozzle.solve` returns a result that is fed back to re-solve the
chemistry, which is fed back to re-solve the nozzle. That would be a
variable-γ nozzle solver assembled out of a constant-γ one, which is exactly the
partially-wired path ADR-14 forbids — and it would carry the frozen module's
authority without its assumptions.

Where composition varies along the expansion, the provider's own equilibrium
expansion is the answer (`12` §7). Two separate paths, each labelled; never a
loop that blurs them.

---

## 5. Forbidden dependencies, extending `06` §3

| Forbidden | Why |
| --- | --- |
| `physics.thermochemistry` → `physics.compressible` | data contract only (`08` §8) |
| `physics.thermochemistry` → `providers.*` | inversion of the protocol (`06` §3) |
| `physics.thermochemistry` → Cantera / CEA / CoolProp | provider layer only |
| `engineering.chamber` → `providers.*` directly | it receives an injected provider |
| `engineering.nozzle` → `physics.thermochemistry` for performance from a single-γ solve | `12` §7 |
| `engine.*` → a provider singleton | selection is `application`'s (`10` §7.1) |
| Any module → `PropellantDefinition.density_hint` for a calculation | `09` §4.2, enforced by test |

---

## 6. What this unblocks

Completing steps 1–5 makes these possible for the first time:

* **real propellant performance** — c\*, Cf, Isp for an actual pair, replacing
  the em dashes the Engine Design page currently shows honestly (checklist item
  9.8 in the Phase 4G manual gate);
* **nozzle sizing against a real gas** — the frozen quasi-1D solver applied to
  a chemically computed γ and R rather than to air;
* **regime analysis for real engines** — the Phase 4F back-pressure regimes and
  internal shock location, at chamber conditions that exist;
* **cycle balances** — chamber conditions as a boundary condition for the pump
  and turbine work;
* **cooling** — a gas-side correlation with the real product gas.

The Engine Design page's em dashes are the marker to watch. They are currently
correct: no chemistry, so no performance number, and the page says so instead of
inventing one. Step 5 is what earns the right to replace them, and until then
they stay.
