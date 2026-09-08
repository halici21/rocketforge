# Fluids foundation — Checkpoint

`physics.fluids` + real cryogenic property provider + reactant enthalpy
coupling + validated liquid density + density impulse.

**No phase number.** The authoritative roadmap orders modules, not phases.
This is `06_future_module_dependency_map.md` §8 **step 1**.

**Status:** ✅ **COMPLETE**

---

## Position

| Field | Value |
| --- | --- |
| CURRENT_SEGMENT | — closed (A through J) |
| LAST_COMPLETED_STEP | STEP 95 — final verdict returned |
| NEXT_STEP | — this workstream is closed |
| NEXT_ACTION | Next module per `06` §8 step 2: `engineering.line` / `valve` / `orifice`. Blocked first on methane viscosity validation. |

---

## Opening gates

| Gate | Result | Accepted baseline | Match |
| --- | --- | --- | --- |
| Base (`.venv`) | **6451 passed, 118 skipped**, exit 0, 70.63 s | 6451 / 118 | ✅ |
| CEA (`.venv-cea`) | **6571 passed, 1 skipped**, exit 0, 82.37 s | 6571 / 1 | ✅ |
| Frozen Compressible | **22 / 22 byte-identical** | 22 / 22 | ✅ |
| THERMOCHEMISTRY API v1.0 | 13 files, `44312c23c71cfd52…` | unchanged | ✅ |
| IDEAL ROCKET PERFORMANCE API v1.0 | 6 files, `d07f4ff9017efdfe…` | unchanged | ✅ |
| TRADE STUDY API v1.0 | 12 files, `912065266fccc6d5…` | unchanged | ✅ |
| NASA CEA PROVIDER v1.0 | 11 files, `0a46b5f089a9cc7a…` | unchanged | ✅ |

---

## Findings from the reading pass (before any code)

**1 — CEA already takes an explicit enthalpy constraint.**
`rocketforge/providers/cea/mapping.py:401` computes
`mixture_enthalpy = reactants.calc_property(ENTHALPY, weights, temperatures)`
and passes `enthalpy_argument(mixture_enthalpy, cea.R)` — i.e. `H/R` — into
`solver.solve(solution, HP, constraint, p_bar, weights)`. The HP constraint is
**already an explicit caller-supplied number**, so a corrected reactant
enthalpy has a supported API path and needs no text parsing, no `thermo.lib`
edit and no hidden global state. To be proven empirically in SEGMENT E, not
assumed.

**2 — The assigned-enthalpy set is already detected empirically.**
`assigned_enthalpy_temperature()` probes each reactant at two temperatures and
returns the assigned temperature only when the enthalpy does not move. That is
exactly the predicate the correction must be gated on, and it doubles as the
built-in **negative control**: for those reactants CEA provably ignores
temperature, so adding a sensible increment cannot double-count. Gaseous
reactants return `None` and must receive no correction.

**3 — `PropellantStream` already carries `pressure`.** Optional, validated
positive. So §107's pressure blocker does **not** require a Thermochemistry API
version bump; it requires the fluids boundary to *demand* a pressure rather
than invent one.

**4 — `density_hint` lives on `PropellantDefinition`** and its own docstring
already says "Bulk density is `physics.fluids`' answer, not this layer's".

**5 — Five production propellants, no RP-1.** LOX, LCH4, LH2, GOX, GCH4. RP-1
is not in the catalogue at all, so §27's surrogate trap cannot be walked into
by accident; it stays unsupported by construction.

**6 — Conventions to mirror:** `ProviderCapability` (StrEnum) +
`ProviderCapabilities` (frozen dataclass, `require()` raises), `Solution[T]`,
frozen slotted dataclasses, provider protocol in `physics`, adapter in
`providers`, provenance record per provider.

---

## SEGMENT E result — the blocking question, answered YES

`acceptance/fluids_foundation/cea_enthalpy_injection_spike.json`.

**CEA does consume an explicitly supplied reactant enthalpy**, through the
official `EqSolver.solve(solution, HP, constraint, p, weights)` path the
adapter already used. No text parsing, no `thermo.lib` edit, no global state.

| Probe | Result |
| --- | --- |
| Shift the H/R constraint by ±5, ±50 | chamber T moves 3592.47 / 3598.66 / 3604.82 / 3658.87 K — **positive control passes** |
| Move LOX 90.17 → 95 K, native | mixture enthalpy **bit-identical**, chamber T identical — the limitation, reproduced |
| Move GOX 298.15 → 320 K | enthalpy and chamber T both move — gases respond natively |

**The basis, decoded and confirmed against CEA's own published values.**
`Mixture.calc_property(ENTHALPY, w, T)` returns **J/kg, mass-specific**:
O2(L) → −12979.000 J/mol, CH4(L) → −89233.222 J/mol, H2(L) → −9012.000 J/mol,
CH4 gas → −74600.186 J/mol. The mixture value is the mass-fraction-weighted
linear combination, reproduced to **0.025 J/kg in 1.58e6** — the residue of
CEA's float32 weight vector (an O/F of 3.4 returns as 3.400000095367432).

## SEGMENT F result — all five blocking coupling checks pass

`acceptance/fluids_foundation/reference_state_identity.json`.

| Check | Result |
| --- | --- |
| **A** at `(T_ref, p_ref)` | both increments **exactly 0.0**; native and corrected **bit-identical** on T, R, M, γ_fr, γ_eq |
| **B** at `T_ref`, 3 bar | increments +288.2 and +105.5 J/kg → ΔT +0.0218 K. A real pressure term, preserved rather than zeroed |
| **C** oxidiser sweep 86→98 K | native T identical at **every** temperature; corrected T strictly monotone. Δh −6955 J/kg at 86 K |
| **D** gas negative control | bindings supplied *and* corrected policy active → **0 corrections applied**, bit-identical. No double counting |
| **E** composition | 28 species both sides, provider element-balance post-validation passed on both |

## State by area

| Area | Status |
| --- | --- |
| Docs read | ✅ propulsion v1 docs, thermochemistry domain, CEA adapter, roadmap §8 |
| Opening regression | ✅ base; CEA pending |
| Freeze manifests | ✅ all five unchanged |
| Fluid domain | ✅ `rocketforge/physics/fluids`, 23 exports, imports only `core` |
| Constant provider | ✅ `providers/fluid_properties/constant.py` |
| Real provider spike | ✅ CoolProp 8.0.0, cp312-abi3 wheel runs on CPython 3.13 |
| Real provider | ✅ `providers/fluid_properties/coolprop.py`, lazy import, HEOS |
| CEA coupling spike | ✅ **YES** — explicit enthalpy is consumed |
| Coupling implementation | ✅ CEA Provider **v1.1**, additive, native default |
| Validated density | ✅ `engineering/propellants`, stream density at the real state |
| Density impulse | ✅ `ρ_mix·c_eff`, both identities checked, Trade Study metric |
| Application / UI | ✅ Fluid Properties workspace, 0 Qt messages |
| Packaging | ✅ 2239 files, 245.0 MB, CoolProp bundled, 7/7 self-tests exit 0 |
| New freeze manifests | ✅ 4 written; CEA v1.0 kept as history |

## Current test counts

Base 6451 / 118 exit 0. CEA pending.

## Current blockers

None for this workstream.

**Carried forward:** methane viscosity is not validated against an independent
source — CoolProp and NIST use different correlations, and the 0.4–1.4 %
disagreement is a model difference rather than evidence about either. Nothing
in this workstream consumes viscosity. It must be resolved before
`engineering.line` / `valve` / `orifice`, which are its first consumers.
