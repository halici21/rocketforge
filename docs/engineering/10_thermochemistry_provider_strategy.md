# 10 — Thermochemistry Provider Strategy

Which external code computes chemical equilibrium, which computes nothing and
only checks, how a provider declares what it can do, and what the application
does when none of them is installed.

**Status:** specification. No provider is implemented, and as of this document
none is installed.

> ### SUPERSEDED IN PART — read this first (2026-09-04)
>
> §5.1 and §5.2 of this document proposed **Cantera as primary solver** and
> **CEA as a developer-side oracle**. The Phase 5B-0 spike disproved the factual
> premise behind that split: NASA CEA **v3** ships a cp313 Windows wheel, needs
> no Fortran toolchain, is Apache-2.0, and exposes a structured API. Cantera, in
> its shipped databases, has **no liquid reactants** and no rocket performance.
>
> **ADR-31 supersedes ADR-20 and ADR-21: NASA CEA v3 is the recommended first
> production provider; Cantera is the independent oracle and the future
> kinetics/transport path.** Evidence:
> `implementation/PHASE_5B0_CEA_CANTERA_PROVIDER_SPIKE.md`.
>
> Everything else in this document — the capability model, the provenance
> requirements, the tabulated-provider rules, the no-silent-fallback rule,
> ADR-19, ADR-22, ADR-23 and ADR-24 — **stands unchanged**. The original text
> below is preserved rather than rewritten, so the reasoning remains auditable.

---

## 1. The environment this has to work in

Measured on 2026-09-03, not assumed:

| Fact | Value |
| --- | --- |
| Python | 3.13.12 |
| Platform | Windows 11 Pro, win32 |
| numpy | 2.4.3 (the one numerical runtime dependency) |
| Cantera | **not installed** |
| RocketCEA | **not installed** |
| CoolProp | **not installed** |
| Runtime requirements | `PySide6-Essentials==6.10.2`, `numpy>=1.26` |
| Dev-only oracle | `scipy>=1.11`, skipped when absent |
| Shipping form | PyInstaller directory bundle, 191.9 MB, 2 072 files |

Three consequences follow directly and shape everything below.

**Python 3.13 is recent enough to be a real constraint.** A library that ships
compiled extensions must have a cp313 Windows wheel or it needs a toolchain the
user does not have. This is not hypothetical for a Fortran-backed package.

**The application is shipped as a frozen bundle, not as a pip install.** Any
provider that reaches the end user must survive PyInstaller: its binary
extensions collected, its data files present, its paths `sys._MEIPASS`-safe. The
compressible phases already proved that resource paths break in a bundle unless
tested there.

**The project's dependency discipline is strict and has been enforced.**
`tests/test_architecture.py` fails the build if a backend module imports SciPy.
Adding a heavyweight chemistry dependency to the runtime is a decision of the
same weight, and Phase 5A does not make it unilaterally — see OQ-2.

---

## 2. The four provider kinds

| Kind | Computes equilibrium? | Ships to the user? | Role |
| --- | --- | --- | --- |
| **Cantera** | yes, Gibbs minimisation | proposed primary, pending OQ-2 | the solver |
| **CEA / RocketCEA** | yes, Gibbs minimisation | **no** — developer-side | the reference standard |
| **Tabulated** | no — interpolates stored results | yes, honestly labelled | offline / no-dependency fallback |
| **In-tree oracle** | partially — a small deliberate subset | test-only | independent verification |

The strategy in one line: **Cantera computes what the user sees, CEA decides
whether Cantera was right, and neither is allowed to be silently absent.**

> **`PHASE_3_SPEC_CONFLICT` — this ordering differs from Phase 3.** `06` §8
> step 3 says "`physics.thermochemistry` interfaces **+ a CEA provider**". The
> conflict is one of *sequencing*, not of architecture — Phase 3 reserves
> `providers/cantera/` in `01` §3 and names Cantera in `06` §2, so it does not
> exclude it. **Phase 3 wins and Phase 5A does not overrule it**: the
> recommendation below is an input to a spike whose outcome the project owner
> rules on (OQ-2), and no code commits to either provider before that ruling.
> Full statement in `14` §1.

---

## 3. Why RocketForge does not write its own equilibrium solver (ADR-19)

The tempting alternative is to implement Gibbs free-energy minimisation
in-tree — it would remove every dependency question below. Phase 5A rejects it
for v1.

**The argument for writing it.** The project already wrote its own Brent solver,
its own PCHIP interpolation and its own gas dynamics rather than taking SciPy,
and those decisions were right: each is a few hundred lines, each is fully
testable against published values, and each removed a heavyweight dependency.

**Why the same reasoning does not carry over.** Multi-phase chemical equilibrium
is not the same size of problem:

* it is a constrained minimisation over 30–60 species with element-balance
  constraints, not a scalar root find on a monotone function;
* it needs a curated, internally consistent thermodynamic database — the NASA
  Glenn coefficients for hundreds of species — which is a *data* undertaking
  larger than the code;
* condensed-phase inclusion is a combinatorial question (which condensed species
  are present at this state), and getting it wrong produces plausible wrong
  answers rather than obvious failures;
* the initial-guess and convergence behaviour near condensation boundaries is
  where published implementations put most of their engineering.

The compressible module could be validated against Anderson's appendices to the
last printed digit. An in-house equilibrium solver would be validated against
CEA — which means CEA is the standard anyway, and the honest architecture is to
*call* the standard rather than to reimplement it and then check it against
itself.

**ADR-19: RocketForge does not implement chemical equilibrium in v1. The
physics layer owns the contract; a provider owns the solution.** Revisit only if
every provider option is rejected, in which case the scope is a phase of its own
and not a subsection of one.

The in-tree oracle (§6) is the deliberate exception, and its limits are the
point of it.

---

## 4. Capability declaration

A provider must state what it can do *before* being asked, so the application
can present honest options instead of discovering a limitation through an
exception mid-calculation.

```python
@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """What a provider can actually do. Declared, not discovered."""

    equilibrium_chamber: bool
    frozen_expansion: bool
    equilibrium_expansion: bool
    frozen_at_throat: bool
    condensed_phases: bool             # can it include condensed species at all
    condensed_phase_reporting: bool    # can it report the condensed fraction
    monopropellants: bool
    custom_reactant_temperature: bool  # section 9.3 of doc 09
    custom_species_database: bool
    pressure_range: tuple[float, float]        # [Pa], validated range
    mixture_ratio_range: tuple[float, float]   # [-]
    temperature_ceiling: float | None          # [K], above which data runs out
```

Rules:

* **A capability that is `False` means the corresponding call raises
  `NotImplementedError`, immediately and always.** It must never partially work.
* **A range is the provider's *validated* range, not its *tolerated* range.** A
  call outside it returns a diagnostic naming the range; it does not silently
  extrapolate. This is `ThermoPolynomial`'s out-of-range rule (`09` §2.3) at the
  provider level.
* **Capabilities are static per provider instance**, so the UI can grey out a
  mode with a reason rather than offering it and failing (`15` §4).

---

## 5. Provider roles in detail

### 5.1 Cantera — proposed primary solver

**What it is.** An open-source suite for thermodynamics, kinetics and transport,
with a real multi-phase Gibbs equilibrium solver (`gas.equilibrate('HP')`,
`equilibrate('SP')`) — exactly the two operations this layer needs (`11` §3,
§5). It is a Python-first library with a documented API, it reads YAML
mechanisms, and its thermodynamic data are NASA polynomials on the datum this
layer already fixed (`09` §3.4).

**Why it fits RocketForge specifically.**

* `HP` and `SP` equilibrium are first-class operations, so the chamber and the
  expansion map onto library calls rather than onto a text-file protocol.
* Composition is available at every state, which is what `GasStation` needs and
  what makes an equilibrium expansion possible at all.
* It is installable with pip and is not tied to a Fortran toolchain.
* Its species database is inspectable and versioned, which `09` §2.4 requires.

**What it does not give for free.** Cantera is a general chemistry library, not
a rocket code. RocketForge must supply: the reactant-condition bookkeeping, the
O/F convention, the sonic-throat search (`09` §9.2 `throat()`), the isentropic
exponent γ_s as distinct from cp/cv (`09` §7.1), and a propellant set mapped
onto species and mechanisms. That work is RocketForge's and belongs in the
adapter, not in physics.

**Open risks, not yet resolved.**

* cp313 Windows wheel availability must be confirmed before committing (OQ-2).
* PyInstaller collection of Cantera's data files and extension modules is
  unproven here and must be proven in a bundle, not on a dev machine.
* Bundle size: the shipped directory is already 191.9 MB.
* Its licence must be confirmed compatible with how RocketForge is distributed.

None of these is a reason to reject it; all are reasons that Phase 5B's first
task is a **spike**, not an implementation (`14` §3).

### 5.2 NASA CEA and RocketCEA — the reference standard, developer-side

**What CEA is.** The NASA Glenn Chemical Equilibrium with Applications code: the
de facto standard for rocket propellant performance for decades, and the source
of the numbers that appear in textbooks and on data sheets. RocketCEA is a
Python wrapper around the CEA Fortran source.

**Its role here is validation, not production.** Rationale:

* **It is the standard, so it is the right thing to be checked against.** If
  RocketForge's LOX/CH₄ chamber temperature disagrees with CEA, RocketForge is
  wrong. That is precisely the relationship this project has already used with
  Anderson's appendices for compressible flow, and it works best when the
  reference is *independent of the code under test*. Making CEA the runtime
  solver would destroy that independence.
* **It is the wrong shape for a shipped dependency.** It carries a Fortran
  extension, which on Python 3.13 for Windows means either a matching prebuilt
  wheel or a gfortran toolchain the end user will not have; it needs its data
  files present at runtime; and freezing all of that into a PyInstaller bundle
  is a packaging risk with no upside for the user.
* **Its distribution terms need checking.** CEA is US Government software whose
  historical distribution went through a request process, and RocketCEA's own
  licence must be read before any redistribution. This is a legal question, not
  an engineering one, and Phase 5A does not answer it (OQ-3). Using it as a
  developer-side oracle that is never redistributed sidesteps the question
  entirely for v1 — which is a further reason to place it there.

**How it is used.** Exactly as SciPy is used today: an optional, developer-side
oracle, in `requirements-dev.txt`, with the tests that need it **skipping**
cleanly when it is absent (`13` §6). This pattern is already proven in this
repository by `tests/core/test_roots_cross_validation.py`.

**The fallback if RocketCEA cannot be installed.** Published CEA output — from
NASA SP-273 / RP-1311 and from documented CEA runs — is transcribed into
reference JSON exactly as Anderson's appendices were, with provenance and
rounding boxes. That is a weaker gate than a live oracle because it covers
discrete cases rather than a sweep, and `13` §3 says so plainly rather than
implying equivalence.

### 5.3 The tabulated provider — honest, limited, and never a solver

A `TabulatedProvider` reads stored equilibrium results and interpolates them.
It exists so that the application can do *something* with no chemistry library
installed — which, today, is every installation.

It is bound by the rule this project already holds for compressible flow:
**a table is never presented as a solver.**

| Requirement | Why |
| --- | --- |
| `provenance.provider_name` is `"tabulated:<dataset>-<version>"` | the user sees at a glance that this is interpolated |
| It **refuses** to extrapolate outside its grid — no clamping | the same rule as `09` §2.3 and the compressible module's domain limits |
| It declares a narrow `pressure_range` / `mixture_ratio_range` | capabilities must be honest (§4) |
| Interpolation error is stated in its metadata | a user must be able to know what the interpolation costs |
| The UI labels its results as interpolated (`15` §3) | the honesty rule the manual release gate checks |
| It is never the silent fallback for an absent primary (§7) | a downgrade the user did not notice is the failure mode this project treats as unshippable |

The distinction that keeps this legitimate: the forbidden pattern is *user input
→ table lookup → result presented as computed*. A tabulated provider that
announces itself in its name, its provenance and its UI label is a declared
data source, not a disguised solver. The line is thin and it is held by
labelling, refusal to extrapolate, and never being selected behind the user's
back.

### 5.4 The fluid-property boundary

`FluidPropertyProvider` (`01` §5) and `ThermochemistryProvider` are **separate
protocols with separate implementations**, for the reason `08` §6 gives: one
answers questions about a substance, the other about a reaction.

They are not merged even though CoolProp and Cantera can each do a little of the
other's job:

* a `ThermochemistryProvider` must never be asked for LOX viscosity;
* a `FluidPropertyProvider` must never be asked for a flame temperature;
* **their enthalpy datums differ and are never mixed** (`09` §3.4) — this is the
  concrete hazard that makes the separation load-bearing rather than tidy.

Where a single library backs both, that is two adapter classes over one
dependency, not one class implementing two protocols. Keeping them separate is
what allows CoolProp for fluids and Cantera for chemistry, or either one absent,
without a combinatorial mess.

---

## 6. The in-tree verification oracle

A small, deliberately limited equilibrium calculation lives in `tests/`, never
in `rocketforge/`. It does **not** contradict ADR-19, because its scope is
chosen to be tractable and its limits are the reason it is trustworthy:

**What it does.** For a *specified* set of product species and a *specified*
temperature, evaluate NASA polynomials and check that a claimed equilibrium
state satisfies the conditions it claims to satisfy — element balance, enthalpy
conservation at constant pressure, mass/mole consistency, γ against cp and R.

**What it does not do.** It does not find the equilibrium composition. It
verifies a state that a provider produced.

This is the same instrument the compressible campaign used to settle the Phase 3
§10.6 erratum: an independent stdlib computation that checks a conservation law
the implementation must satisfy regardless of how it got there. It needs no
chemistry library, so it runs on every checkout, including this one where none
is installed. `13` §5 makes it universal.

Its permitted tools follow the existing rule: standard library, plus `Decimal`,
`Fraction`, `mpmath` or SciPy **as oracles in tests only** — never in
`rocketforge/`.

---

## 7. Selection, absence and the no-silent-fallback rule

### 7.1 Selection

`application` chooses the provider and injects it (`01` §3, `08` §8). There is
no global, no module-level singleton and no import-time probing inside physics.
Selection order is explicit and user-visible:

1. an explicitly configured provider, if the user chose one;
2. otherwise the first *available* provider in a declared preference order;
3. otherwise **none** — see §7.2.

### 7.2 What happens when nothing is installed

Today, that is the actual state of this machine, so it is the default case and
not an edge case.

**The rule: the application says so, and computes nothing.**

* The thermochemistry UI shows an explicit unavailable state naming what is
  missing and how to install it (`15` §7).
* No number is displayed. Not a default, not a placeholder that looks like a
  result, not a value from a table that the user did not choose.
* Every other page continues to work — the compressible subsystem has no
  chemistry dependency and must not acquire one.
* The test suite passes in full, with provider-dependent tests **skipped and
  reported as skipped** (`13` §6).

**A tabulated provider is never auto-selected to paper over an absent primary.**
Falling back silently would put interpolated numbers on screen in the place
where computed numbers normally appear, which is exactly the class of defect the
Phase 4G manual gate treated as unshippable. The user may *choose* the tabulated
provider; the application may not choose it for them.

### 7.3 Switching providers clears results

Changing the provider invalidates every displayed chemistry result immediately.
This is the project's standing "never leave stale calculation state on screen"
rule, and it bites harder here than anywhere so far: two providers can produce
numbers that differ by a few per cent, which is small enough to look like a
valid update and large enough to be a wrong answer. `15` §4 specifies the
behaviour.

---

## 8. Provenance requirements per provider

Every `ChamberGas` and `GasStation` carries `ThermochemistryProvenance`
(`09` §11). Per provider, at minimum:

| Provider | `provider_name` | `provider_version` | Must also record |
| --- | --- | --- | --- |
| Cantera | `"Cantera"` | `cantera.__version__` | mechanism file and its version, species count, `equilibrate` solver and tolerances |
| RocketCEA | `"RocketCEA"` | package version | the CEA version wrapped, the exact card deck sent |
| Tabulated | `"tabulated:<dataset>-<version>"` | dataset version | grid bounds, interpolation scheme, stated interpolation error |
| Test stub | `"stub:<purpose>"` | — | must be impossible to mistake for a real result |

The test stub's name is required to be recognisably a stub because a stub value
escaping into an acceptance artifact would be a fabricated number, and this
project has already had one near miss with a mutation helper that silently did
nothing (`13` §7 keeps that lesson).

---

## 9. Version pinning and reproducibility

A chemistry result is only reproducible if the data behind it is pinned.

* The **provider version** and the **species database version** are both in
  provenance and both appear in any acceptance artifact.
* A reference case records the versions it was generated under. If a later
  version changes the answer beyond tolerance, that is a finding to be
  investigated and documented — **not** a tolerance to be widened. This is the
  rule that has governed every reference comparison in this project so far, and
  it is restated here because chemistry data updates are a real and recurring
  source of small changes.
* Upgrading a provider is a deliberate act with a re-validation run attached,
  not an incidental consequence of `pip install -U`.

---

## 10. Summary of decisions

| Decision | ADR |
| --- | --- |
| No in-house equilibrium solver in v1; providers own the solution | ADR-19 |
| Cantera is the proposed primary solver, pending a packaging spike | ADR-20 |
| CEA / RocketCEA is a developer-side reference oracle, not shipped | ADR-21 |
| A tabulated provider is permitted, labelled, and never auto-selected | ADR-22 |
| Fluid-property and thermochemistry providers stay separate protocols | ADR-23 |
| With no provider installed the application refuses rather than substitutes | ADR-24 |

Full ADR statements are in `PHASE_5A_SUMMARY.md` §4.
