# 13 — Thermochemistry Verification and Validation Plan

How Phase 5B proves its chemistry is right, what it checks against, how
tolerances are chosen, and what the acceptance gates are.

**Status:** specification. No test is implemented and **no reference value is
quoted in this document**. Values are transcribed from their sources in Phase
5B, with their rounding boxes, exactly as the compressible campaign did. Writing
numbers here from memory would be the fabrication this project forbids.

---

## 1. The problem this plan has to solve

The compressible campaign had an unusually good position: Anderson's appendices
print isentropic, normal-shock and Prandtl–Meyer tables to five or six
significant figures, so 2 320 published values could be checked directly, and
the physics is closed-form so an independent oracle was a few dozen lines.

Chemistry is harder in three specific ways.

**There is no closed form.** An equilibrium composition is the solution of a
constrained minimisation. There is no expression to differentiate and check.

**The reference standard is a program, not a table.** CEA is the standard, and
its published outputs cover selected cases rather than a dense grid.

**The answer depends on the thermodynamic database.** Two runs with different
species data legitimately differ. A disagreement is not automatically a defect,
which makes "is this right?" a harder question than it was for γ = 1.4 air.

The response is to lean much harder on **provider-independent invariants** —
conservation laws that must hold regardless of who computed the state or which
database they used — and to treat published comparisons as one tier among
several rather than as the whole of validation.

---

## 2. Test tiers

| Tier | What it checks | Needs a provider? | Runs on a clean checkout? |
| --- | --- | --- | --- |
| **T1 Structural** | types, units, invariants, refusals, architecture rules | no | yes |
| **T2 Invariant** | conservation laws on every state produced | no (stub is enough) | yes |
| **T3 Oracle** | provider states against an independent in-tree computation | yes | skipped if absent |
| **T4 Published** | against transcribed CEA / literature values | yes | skipped if absent |
| **T5 Cross-provider** | Cantera against RocketCEA on the same case | both | skipped if absent |
| **T6 Coupling** | the handshake into frozen Compressible v1 | yes | skipped if absent |

T1 and T2 are the backbone: they must run and pass **with no chemistry library
installed**, which is the current state of this machine. A campaign whose entire
value depends on an optional dependency is a campaign that does not run.

---

## 3. Reference sources

Named here; transcribed in Phase 5B.

| Source | Provides | Role |
| --- | --- | --- |
| **NASA RP-1311 Part I** (Gordon & McBride, 1994) | the CEA method: equations, Gibbs minimisation formulation, derivative expressions | the theory this layer's contracts describe |
| **NASA RP-1311 Part II** (McBride & Gordon, 1996) | program description, worked examples with printed output | worked cases for T4 |
| **NASA SP-273** (Gordon & McBride, 1971) | the original method and extensive tabulated performance | worked cases for T4 |
| **NASA TP-2002-211556** / Glenn coefficient reports | NASA 9-term polynomial coefficients and their validity ranges | species data for the in-tree oracle |
| **Sutton & Biblarz, *Rocket Propulsion Elements*** | representative chamber temperatures, γ, M̄, c\* for common pairs | sanity bands, not precision checks |
| **Live RocketCEA** | dense, arbitrary-case comparison | T5, developer-side only |

**Transcription discipline**, unchanged from the compressible campaign:

* every value carries its source, table, page and the run conditions it came
  from;
* the **rounding box** is derived from the printed precision, and the tolerance
  is derived by re-solving at the corners of that box — never chosen to make a
  test pass;
* a published value that does not reproduce is investigated as a
  convention/basis/version question **before** the implementation is suspected;
* if it still does not reproduce, it is documented as an explained REVIEW with
  the reason, not deleted and not silently loosened.

**Sutton's tables are sanity bands and are labelled as such.** They are
condensed, rounded and often for unstated conditions. Using them as precision
references would be a mistake in the opposite direction from ignoring them: they
are excellent at catching an answer that is wrong by 30 %, and useless at
catching one wrong by 0.5 %.

---

## 4. Tolerance policy

The rule that governed every compressible tolerance governs these:

> **A tolerance is derived from the reference's precision and the physics, and
> is fixed before the comparison is run. It is never widened to accommodate a
> disagreement.**

Expected tolerance classes, with their justifications:

| Comparison | Class | Justification |
| --- | --- | --- |
| Element balance | ~1e-10 relative | a conservation law; only round-off should appear |
| Mole/mass round trip | ~1e-12 relative | pure arithmetic |
| `R == R_universal / M̄` | ~1e-8 relative | providers may use pre-2019 constants (`09` §7.2) |
| NASA polynomial vs published cp | printed precision | a transcription check |
| Polynomial range-join continuity | value only, loose | fits are matched in value, **not** slope (`09` §2.3) |
| Provider T_c vs published CEA T_c | derived from the printed rounding box | the standard T4 method |
| Cantera vs RocketCEA T_c | **stated, not assumed** | different databases; see below |
| Sutton sanity bands | percent-level, explicitly a band | the source's own precision |

**Cross-provider tolerance is the honest hard case.** Cantera and CEA can
legitimately differ because their species sets and thermodynamic data differ.
Phase 5B must therefore:

1. run the comparison first and **measure** the spread across the reference
   cases;
2. record the measured spread with its cause identified where possible;
3. set the tolerance from that measurement, documented, rather than picking a
   round number that passes.

A tolerance chosen before the measurement would either hide a real defect or
manufacture a failure. This is the one place in the plan where the number cannot
be derived in advance, and saying so now is better than inventing one.

**The rounding-box subtlety already met once.** In the nozzle campaign, a back
pressure built from 4-significant-figure inputs missed an exact threshold by
~1e-4, and the correct response was to compare the published number against the
*computed threshold* rather than to widen `pressure_tol`. The same situation
will arise here wherever a published case sits on a boundary — a condensation
onset, a mode transition — and the same response applies.

---

## 5. T2: the invariants that carry the campaign

These run on **every** state the suite produces, from every provider including
stubs. They need no reference data, which is what makes them the most valuable
tests available.

| # | Invariant | Catches |
| --- | --- | --- |
| I1 | element balance, per element (`09` §3.2) | mis-parsed formula, dropped species, **inverted O/F**, mass-basis slip |
| I2 | mass conservation | the same class, independently |
| I3 | mole fractions sum to 1 | truncation leaking into a `Mixture` (`09` §5.2) |
| I4 | mole↔mass round trip (`09` §5.3) | the commonest chemistry bug in engineering software |
| I5 | `R == R_universal / M̄` (`09` §7.2) | an adapter scaling one and not the other |
| I6 | γ consistent with cp and R **in frozen mode** | a wrong cp, a wrong γ, or the two gammas confused |
| I7 | equilibrium exit T > frozen exit T, same p ratio (`11` §5) | modes silently identical — the failure that looks right |
| I8 | equilibrium M̄ rises during expansion (`11` §5.2) | recombination not actually happening |
| I9 | frozen M̄ exactly constant | "frozen" not actually frozen |
| I10 | γ_frozen ≠ γ_s where dissociation is strong (`11` §4) | an adapter reporting cp/cv for both |
| I11 | enthalpy conserved across the chamber HP solve | the HP problem solved as TP or UV (`11` §3.2) |
| I12 | entropy conserved along an isentropic expansion | the SP problem not actually SP |
| I13 | datum sanity: a known reaction's heat vs its published value | **mixed enthalpy datums** (`09` §3.4, `11` §3.3) |
| I14 | O/F asymmetry: an asymmetric pair gives a distinguishable answer under inversion | O/F ↔ F/O confusion (`09` §6.3) |
| I15 | stoichiometric ratios of the reference pairs reproduce | formula or molar-mass errors |

**I7, I10 and I13 are the three that catch the failures nobody else would.**
Each corresponds to a defect that produces plausible numbers and passes every
other check: modes that are secretly the same, one γ masquerading as two, and a
flame temperature computed on inconsistent energy datums.

I1 and I14 together are this campaign's equivalent of the mass-conservation
argument that settled the Phase 3 §10.6 nozzle erratum — a provider-independent
law that decides the question without appeal to any authority.

---

## 6. Skip policy

The precedent is already in this repository:
`tests/core/test_roots_cross_validation.py` skips cleanly when SciPy is absent,
and the rest of the suite still covers solver correctness in full.

Applied here:

* T3–T6 skip when their provider is absent, with a **reason string naming the
  missing package**;
* skips are counted and reported in any acceptance artifact, never rounded down
  to "all green";
* **T1 and T2 never skip.** If they would, the campaign has no floor;
* an acceptance verdict states the skipped count explicitly. A run with every
  provider absent is a *weaker* result than one with them present, and the
  artifact must say so rather than presenting the same "passed" line.

This last point is the honesty rule that the Phase 4G packaging limitation
followed: state the limitation, do not blur it.

---

## 7. Two lessons carried forward

**A test that cannot fail is worse than no test.** Phase 4G's reference
self-test mutated `row.values` on a dict — which is a bound method — so it
silently mutated nothing and then "detected corruption" in unmodified data. It
was vacuously green.

The rule this produced, and which applies to every T2 invariant: **each
invariant test must be accompanied by a proof that it bites** — a deliberate
perturbation that the test is shown to catch. For chemistry the perturbations
are obvious and cheap: invert the O/F, drop a species from a mixture, scale a
molar mass, shift an enthalpy datum by a constant, return the chamber γ for both
modes. If a mutation does not fail the suite, the invariant is not being tested.

**Tests must not demand fictional precision.** Phase 4G raised 8 flags at the
Fanno and Rayleigh choking limits by demanding a one-ulp distinction the physics
does not support; the fix was to the test, not the code. The chemistry analogue
is demanding agreement between two providers to more digits than their databases
justify. §4's measure-then-set rule exists to prevent it.

---

## 8. Architecture tests

The suite currently holds 41 rules and passed unchanged through Phase 4G. Phase
5B **adds** rules; it weakens none:

| New rule | Enforces |
| --- | --- |
| `physics.thermochemistry` imports only `core` | `08` §8 |
| no `physics.thermochemistry` → `physics.compressible` | `08` §8 |
| no Cantera / RocketCEA / CoolProp outside `providers.*` | `06` §3, `08` §8 |
| no PySide6 below `application` | existing rule, extended to the new package |
| no `_deg` naming below `application` | existing rule, extended |
| `density_hint` is read by no code path in the layer | `09` §4.2 |
| provider adapters implement the declared protocol | `10` §4 |
| no equilibrium solver in `rocketforge/` | ADR-19 |

The `density_hint` rule is worth its line: a field documented as display-only
becomes a physics input the moment someone needs a density and it is right
there. A test is the only thing that stops it.

---

## 9. Acceptance gates for the thermochemistry phase

Phase 5B does not close until:

| # | Gate |
| --- | --- |
| G1 | T1 and T2 pass with **no** chemistry library installed |
| G2 | Every T2 invariant has a mutation proof that it bites (§7) |
| G3 | Architecture rules extended; **41 existing rules still green** |
| G4 | The full existing suite is unchanged — no compressible regression |
| G5 | The frozen manifest digest is unchanged |
| G6 | Every reference value transcribed with source, run conditions and rounding box |
| G7 | Cross-provider spread **measured and documented** before its tolerance is set |
| G8 | Condensed-phase refusal demonstrated on a case that actually produces one |
| G9 | Provider-absent behaviour demonstrated: refusal, no numbers, no silent fallback |
| G10 | Every displayed result carries mode and provider provenance |
| G11 | Skipped counts reported explicitly, not folded into "passed" |

**G8 needs a real case, not a synthetic one.** An aluminised composition or a
strongly fuel-rich hydrocarbon actually produces condensed species; asserting
the refusal against a hand-built fake state would test the guard clause without
testing that the detection works.

**G9 is the gate this machine can already exercise**, since no provider is
installed here. It should be written first, because it is the state most users
will start in.

---

## 10. What this plan does not claim

Stated plainly, because overclaiming validation is the failure this project
guards against hardest:

* **It does not claim RocketForge's chemistry will be as good as CEA's.** It
  claims RocketForge will call a real solver and check it against CEA.
* **It does not claim published-value coverage comparable to the compressible
  campaign's 2 320.** Chemistry references are sparser; the count will be much
  smaller, and the weight shifts onto T2 invariants.
* **It does not validate two-phase flow.** Those cases are refused (`11` §7.3),
  and a refusal is tested rather than a result.
* **It does not validate kinetics.** Out of scope (`11` §9).
* **It does not validate against experiment.** Every reference here is another
  computation or a table derived from one. Real delivered performance involves
  combustion efficiency, boundary layers, divergence and two-phase losses, none
  of which are in this layer — and `15` §3 requires the UI to say so rather than
  letting an ideal Isp be read as a predicted one.
