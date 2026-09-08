# Phase 5A Summary — Thermochemistry and Combustion Architecture

**Phase:** 5A — architecture, data contracts, provider strategy, chamber-state
specification, validation roadmap.
**Type:** specification and design. No production physics code was written.
**Date:** 2026-09-02 to 2026-09-03.

---

## 1. What was produced

| Document | Content |
| --- | --- |
| `PHASE_5A_EXECUTION_CHECKLIST.md` | the mandated checklist, deliverables, topic map |
| `08_thermochemistry_architecture.md` | layer placement, ownership, prohibitions, the `physics.fluids` boundary |
| `09_thermochemistry_data_model_and_api_contracts.md` | every type, field, unit, invariant; the provider protocol |
| `10_thermochemistry_provider_strategy.md` | Cantera, CEA, tabulated, in-tree oracle; capabilities, provenance, selection |
| `11_equilibrium_and_chemistry_mode_specification.md` | HP chamber, SP expansion, frozen, equilibrium, frozen-at-throat, condensed phases |
| `12_combustion_chamber_state_specification.md` | the chamber-state contract and the frozen-compressible handshake |
| `13_thermochemistry_verification_validation_plan.md` | sources, tolerance policy, six test tiers, eleven acceptance gates |
| `14_thermochemistry_future_dependency_map.md` | consumers, build order, iteration loops, the Phase 3 conflict |
| `15_thermochemistry_ui_integration_contracts.md` | display, labelling, refusals, the no-provider state |

Nine deliverables, at the requested names. Doc numbers 08–15 were free, so no
renumbering was needed.

**No production code was modified.** No test was added. The frozen compressible
subsystem was read, and inspected at its public API, but not touched.

---

## 2. Regression gates

| Gate | Result |
| --- | --- |
| Opening (before any Phase 5A work) | **5 285 passed, 1 skipped** in 85.19 s |
| Closing (after all nine documents) | **5 285 passed, 1 skipped** in 81.34 s, exit code 0 |

Identical. No production code was changed, so no change was expected.

**Frozen manifest verified, not assumed.** All 22 files in the Phase 4G frozen
manifest were re-hashed and are **byte-identical** to their recorded digests
(`sha256(bytes)[:16]`, the recipe the manifest uses). The manifest digest
`8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502` therefore
still stands.

### 2.1 An environment trap worth recording

The closing gate was first run with the wrong interpreter and **failed to
collect**: five `tests/application/` modules raised
`ImportError: DLL load failed while importing QtGui` under the miniforge base
Python (3.13.12, conda-forge).

The cause was not a defect and not a regression. The project's canonical
interpreter is **`.venv\Scripts\python.exe` (CPython 3.13.2)**, which
`build_exe.bat` already prefers explicitly; the miniforge base environment has a
PySide6 installation whose Qt DLLs do not load. Under the venv the suite passes
in full.

Two things this cost, recorded so they are not repeated:

* **`python -m pytest` from a shell is not necessarily the project's Python.**
  Use `.venv/Scripts/python.exe -m pytest`.
* **`pytest ... | tail` masks the exit code**, because the pipeline reports
  `tail`'s status. The failed run reported exit 0 while five modules had errored
  during collection. Redirect to a file and check `$?` on pytest itself.

A plausible-looking green that was actually a collection failure is precisely
the class of thing this project's gates exist to catch, so it is written down
rather than quietly fixed.

---

## 3. The decisions, in brief

**The layer.** `physics.thermochemistry` is L1, depends on `core` alone, and
reaches the compressible module through a data contract rather than an import.
It owns species, propellants, mixtures, the O/F convention, `ChamberGas`,
`GasStation` and the provider protocol. It owns no performance figure, no
geometry, no chamber dimension and no external library import.

**The data model.** Mole fractions are the stored composition; the basis travels
with every fraction; O/F is oxidiser mass over fuel mass, always, with the
neighbouring quantities (φ, F/O, stoichiometric ratio) given their own names so
none of them can be mistaken for it. Every enthalpy sits on one absolute datum.

**The providers.** RocketForge does not write its own equilibrium solver in v1.
Cantera is the *proposed* runtime solver and CEA the *reference standard* — but
that ordering conflicts with Phase 3 and is deferred to the project owner (§5).
A tabulated provider is permitted, labelled, and never auto-selected. With no
provider installed, the application refuses and computes nothing.

**The chemistry modes.** The chamber is an HP problem; expansion is an SP
problem; equilibrium and frozen bracket reality and are presented together with
their gap. Condensed phases are detected, reported and refused as input to the
single-phase handshake — with "the provider did not say" treated as unknown, not
as absent. Finite-rate kinetics is out of scope, and deliberately not
half-built.

**The handshake.** `ChamberGas → PerfectGas + NozzleOperating`, performed by an
adapter in `engineering.chamber`, with an explicitly chosen `GammaStrategy` and
a *measured* statement of what the single-γ reduction cost. The frozen module is
not modified, not extended and not given a γ(x) hook.

**The validation.** Six tiers, weighted toward provider-independent conservation
invariants because chemistry references are sparser than Anderson's appendices
and database-dependent. Every invariant must come with a mutation proof that it
bites.

---

## 4. Architecture decisions

Phase 3's ADRs end at ADR-16, so Phase 5A begins at **ADR-17**.

**ADR-17 — `physics.thermochemistry` is L1, depends only on `core`, and never
imports `physics.compressible`.** The handshake is a data contract. This is what
allows the compressible module to stay frozen while chemistry evolves.

**ADR-18 — Composition is stored as mole fractions; the basis travels with every
fraction; O/F is oxidiser mass ÷ fuel mass, always.** Mass fractions are a
derived view. Equivalence ratio, F/O and the stoichiometric ratio have their own
names and are never called `mixture_ratio`.

**ADR-19 — RocketForge does not implement chemical equilibrium in v1.** Unlike
Brent, PCHIP and the gas-dynamic relations — each a few hundred lines validated
against printed tables — multi-phase Gibbs minimisation needs a curated
thermodynamic database, has a combinatorial condensed-phase question, and would
be validated against CEA anyway. The physics layer owns the contract; a provider
owns the solution.

**ADR-20 — ~~Cantera is the *proposed* primary solver~~ — SUPERSEDED by ADR-31
(2026-09-04).** *Original text, preserved:* Proposed because it offers `HP`/`SP`
equilibrium as first-class operations, exposes composition at every state, is
pip-installable without a Fortran toolchain, and carries an inspectable
versioned database. *Why superseded:* the Phase 5B-0 spike measured that
Cantera's shipped databases contain **no liquid reactants**, so it cannot
represent a cryogenic rocket chamber at all, and it exposes no rocket
performance. See ADR-31.

**ADR-21 — ~~NASA CEA / RocketCEA is a developer-side reference oracle, not a
shipped dependency~~ — SUPERSEDED by ADR-31 (2026-09-04).** *Original text,
preserved:* It is the standard, so it is what results are checked *against*;
making it the runtime solver would forfeit that independence. It also carries a
Fortran extension whose Python 3.13 Windows wheel availability is unconfirmed,
and data files that must survive PyInstaller. It follows the SciPy precedent
already in this repository: `requirements-dev.txt`, tests skip cleanly when
absent. *Why superseded:* the premise about Fortran packaging was **factually
wrong for NASA CEA v3**, which ships a cp313 Windows wheel and needs no
toolchain. See ADR-31.

> **Both ADRs are retained above rather than deleted.** They record what was
> believed and why, which is the point of an ADR log. The reasoning was sound;
> the factual premise about CEA's Python availability was not.

**ADR-22 — A tabulated provider is permitted, always labelled, and never
auto-selected.** It names itself in its provenance, refuses to extrapolate,
states its interpolation error, and is chosen only by the user. The forbidden
pattern remains *user input → table lookup → result presented as computed*.

**ADR-23 — `FluidPropertyProvider` and `ThermochemistryProvider` stay separate
protocols with separate implementations.** One answers questions about a
substance, the other about a reaction. The load-bearing reason is that their
enthalpy datums differ and must never be mixed.

**ADR-24 — With no provider installed, the application refuses and computes
nothing.** No defaults, no placeholders shaped like results, and no silent
fallback to a table. Every compressible page keeps working.

**ADR-25 — Every enthalpy in this layer is absolute, referenced to the elements
in their reference states at 298.15 K and 1 bar.** A `FluidState` enthalpy from
CoolProp or `physics.fluids` is on a different, arbitrary datum and may never be
added to a value from this layer. Mixing datums produces a flame temperature
wrong by hundreds of kelvin that passes every internal consistency check.

**ADR-26 — γ is mode-dependent, and a state whose provenance does not state its
mode may not enter the compressible handshake.** γ_frozen = cp/cv at fixed
composition; the equilibrium isentropic exponent γ_s is a different quantity.
The gap is a several-per-cent effect and is easy to lose in an adapter.

**ADR-27 — `GammaStrategy` is explicit and has no default.** Five named
strategies, each with a documented bias; none is correct. A strategy the user
did not choose produces a number the user cannot interpret.

**ADR-28 — Condensed phases are refused as input to the single-phase
handshake, and "unknown" is not "absent".** A two-phase flow is not a perfect
gas and no γ makes it one. The threshold is a declared constant, not zero and
not a magic number. A gas-only estimate is permitted only as an explicit,
labelled, never-automatic choice.

**ADR-29 — No finite-rate kinetics in v1.** It needs a validated mechanism, a
stiff coupled integration, a geometry-dependent residence time, and
experimental validation. The architecture leaves room — `ExpansionMode` can gain
a member — but Phase 5A refuses to half-build it, on ADR-14's reasoning.

**ADR-30 — Provider methods raise; `Solution[T]` appears at the engineering
boundary.** This preserves Phase 3's provider error model (`01` §5), keeps
adapters thin, and puts the rich result type where the engineering question is
asked.

---

### Superseding decision, added 2026-09-04 after the Phase 5B-0 spike

**ADR-31 — NASA CEA v3 is the recommended first production rocket
thermochemistry provider. Cantera remains an independent equilibrium oracle and
the future kinetics/transport path.** Supersedes ADR-20 and ADR-21.

The decision is evidence-driven, not authority-driven. "It is NASA" is
explicitly **not** a reason. The measured evidence, all from
`implementation/PHASE_5B0_CEA_CANTERA_PROVIDER_SPIKE.md`:

| Evidence | NASA CEA v3.3.4 | Cantera 3.2.0 |
| --- | --- | --- |
| CPython 3.13 / Windows | cp313 win_amd64 wheel, installs in 17.5 s, **no Fortran toolchain** | cp313 wheel, 19.4 s |
| Licence | Apache-2.0 | BSD-3-Clause |
| API shape | structured Cython API with `.pyi` stubs — **no text parsing** | structured Python API |
| **Cryogenic liquid reactants** | **native** — `O2(L)`, `CH4(L)`, `H2(L)`, `RP-1`, … with valid-T ranges; using gaseous reactants instead shifts Tc by **74.9 K** and Isp by **66 m/s** | **absent from the tested databases** — forcing the ideal-gas phase to 111.6 K silently returns a wrong reactant enthalpy |
| Rocket-oriented calculation | native: chamber/throat/exit stations, area- and pressure-ratio driven | none |
| Equilibrium / frozen expansion, freeze location | native, `n_frz` selects the freeze station | derivable, caller-implemented |
| c\*, Cf, Isp | **native** (oracle capability) | none |
| Equilibrium isentropic exponent γ_s | **native**; differs from frozen cp/cv by **5.7 %** at the tested state | finite-difference only |
| Performance, matched chamber-only workload | **44.2 µs** warm; 1000-point sweep 58 ms | 839.3 µs warm; 1000-point sweep 518 ms |
| PyInstaller | **PASS** with `--collect-data cea --collect-binaries cea`; exact frozen-vs-source parity | **PASS** with `--collect-all cantera`; exact parity |
| Published reference corpus | ships the **NASA RP-1311 Part II worked examples**, 14 of 14 executing | — |

**Cantera's retained roles.** It is an *independent* implementation with an
*independent* database, and on a matched-species common case the two agreed to
9.2e-04 on chamber temperature and 1.05e-04 on γ_s. That independence is worth
keeping as a cross-validation oracle, and Cantera remains the only candidate
for future kinetics, reactor networks and transport (ADR-29 keeps kinetics out
of scope for now).

**What this ADR does not decide.** Whether a compiled chemistry dependency may
enter `requirements.txt` at all remains the project owner's call, and is
evaluated in **Phase 5C**. Phase 5B adds no provider dependency of any kind.

---

## 5. `PHASE_3_SPEC_CONFLICT` — one, reported, not overruled

`06` §8 step 3 specifies "`physics.thermochemistry` interfaces **+ a CEA
provider**". `10` proposes building a Cantera provider first and keeping CEA
developer-side.

**Scope:** sequencing only. Phase 3 reserves `providers/cantera/` in `01` §3 and
names Cantera in `06` §2, so it does not exclude Cantera — it names CEA as the
one built at step 3.

**Resolution: Phase 3 wins.** Phase 5A does not overrule it. The recommended
Phase 5B scope makes the provider decision the output of a spike that the
project owner rules on (OQ-2), and no code commits to either provider before
that ruling. Full statement in `14` §1; cross-referenced in `10` §2.

A second, smaller tension *inside* Phase 3 was found and resolved rather than
reported: `01` §5's `expand()` passes an `area_ratio` into a layer that `06` §2
says never owns nozzle geometry. Resolved in `08` §5.3 by reading a dimensionless
scalar as a boundary condition rather than as geometry — the layer accepts the
number, never an `AreaDistribution`, never a contour, and stores no area. Phase
3's signature is preserved verbatim and a pressure-driven sibling is added
alongside it.

---

## 6. Open questions

None of these blocks starting Phase 5B (§7 explains why).

| # | Question | Blocks | Recommendation |
| --- | --- | --- | --- |
| **OQ-1** | Which propellant pairs ship in v1? | reference-case selection (step 3) | LOX/LH₂, LOX/CH₄, LOX/RP-1, N₂O₄/MMH — the four with the densest published CEA coverage |
| **OQ-2** | Cantera or CEA first — and is a heavyweight chemistry dependency acceptable at all, given the strict dependency discipline and the 191.9 MB bundle? | step 3 | run the spike (step 0), then rule |
| **OQ-3** | RocketCEA and NASA CEA licensing and redistribution terms | shipping CEA | a legal question, not an engineering one; keeping CEA developer-side avoids it for v1 |
| **OQ-4** | May `physics.thermochemistry` import `physics.fluids`? | reactant phase handling at the margins | no for v1; the datum separation (ADR-25) is easier to hold with no import |
| **OQ-5** | Is finite-rate kinetics wanted in a later version? | how much room to leave | the enum already accommodates it; no further work now |
| **OQ-6** | The condensed-phase refusal threshold | step 3 | set it from measured trace fractions in real provider output, and document the measurement |
| **OQ-7** | Bundle-size budget for the shipped application | step 0's outcome | needed to interpret the spike, not to run it |

**OQ-2 is the one that matters.** The others are either deferrable, cheap, or
answerable from evidence the spike will produce anyway.

---

## 7. Recommendation for Phase 5B

**Scope: the provider-agnostic foundation, plus a decision spike.**

| Step | Work | Blocked by an open question? |
| --- | --- | --- |
| **0** | **Provider spike.** Install the candidates on Python 3.13/Windows. Run one HP case each. Freeze a PyInstaller bundle containing one. Measure wheel availability, bundle size, startup cost, data-file survival. Write the finding. **The owner rules on OQ-2.** | no — it *answers* OQ-2 |
| **1** | Data model: `Species`, `PropellantDefinition`, `PropellantStream`, `Mixture`, `MixtureRatio`, `ChamberGas`, `GasStation`, provenance, per `09` | no |
| **2** | Protocol, capabilities, a stub provider, the in-tree oracle, and the T2 invariants **with their mutation proofs** | no |

Steps 0–2 are the recommended Phase 5B. Steps 3–7 (`14` §3) follow once OQ-2 is
ruled on.

**Why this is the right cut.**

* Steps 1 and 2 are where the design risk lives, and **neither depends on which
  provider wins**. The protocol, the data model and the invariants are
  provider-agnostic by construction.
* They are testable on this machine **exactly as it is configured today**, with
  no chemistry library installed. Gates G1 and G2 (`13` §9) are reachable now.
* Writing the invariants before any real provider exists means the tests are
  built to catch defects rather than fitted to whatever the first provider
  returns. Reversing that order is how a suite ends up ratifying an
  implementation instead of checking it.
* The spike runs in parallel because it is an investigation, not a commitment.

**What Phase 5B must not do:** modify `physics/compressible/`, add a γ(x) hook,
default the `GammaStrategy`, auto-select the tabulated provider, ship a number
without its mode and provider labels, or weaken any of the 41 architecture
rules.

---

## 8. Note on the Phase 5A instruction

The Phase 5A instruction ended with an unfilled placeholder —
`[PASTE THE PREVIOUS PHASE 5A PROMPT HERE]` — so no numbered specification body
arrived. This phase was therefore executed from the requirements that *were*
stated explicitly: the nine named deliverables, the twenty-five mandatory
discussion topics, and the required verdict format. All are covered; the mapping
is in `PHASE_5A_EXECUTION_CHECKLIST.md`.

Constraints the missing body would plausibly have imposed are raised as open
questions in §6 rather than silently decided — the propellant set (OQ-1),
the acceptability of a Fortran toolchain (OQ-2, OQ-3), and whether kinetics is
wanted later (OQ-5).

---

## 9. Verdict

Closing regression gate: **5 285 passed, 1 skipped** in 81.34 s, exit code 0 —
identical to the opening gate. No production code changed, so no change was
expected, and none occurred. All 22 frozen-manifest files were re-hashed and are
byte-identical (§2).

**READY FOR PHASE 5B**

Nine specification documents define the layer, its data model, its providers,
its chemistry modes, its coupling to the frozen compressible subsystem, its
validation plan, its dependents and its interface contracts. Fourteen ADRs
(17–30) record the decisions. One Phase 3 conflict is reported and left to the
owner rather than overruled. Seven open questions are recorded, none of which
blocks the recommended Phase 5B scope of steps 0–2.
