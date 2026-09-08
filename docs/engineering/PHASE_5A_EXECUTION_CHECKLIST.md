# Phase 5A — Execution Checklist

Thermochemistry and combustion: architecture, data contracts, provider
strategy, chamber-state specification, validation roadmap.

**Phase 5A writes specifications, not physics.** No production code, no new
tests, no change to the frozen compressible subsystem. The deliverable is a
document set that a future Phase 5B can implement against without reopening
design questions.

---

## Inputs, not work to repeat

Phase 4G closed on 2026-09-02 with **COMPRESSIBLE FLOW v1.0 — ACCEPTED /
FROZEN**. These are givens:

    5 285 passed, 1 skipped
    41 architecture tests green
    0 QML warnings
    2 320 published values checked, 4 explained REVIEW, 0 pending
    593 cross-module identities green
    manual packaged UI release gate PASS
    frozen compressible manifest digest
        8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502

The frozen API is a **dependency** of this phase, never a subject of it.

---

## Constraints

| Rule | Status |
| --- | --- |
| Do not rerun Phase 4G as the primary task | honoured |
| Do not create new Phase 4G acceptance artifacts | honoured |
| Do not edit the frozen Compressible API | honoured |
| Do not add compressible tests for extra assurance | honoured |
| Do not modify the frozen manifest | honoured unless a truly independent blocking defect appears |
| Full suite once at the start, once at the end | opening 5 285 passed / 1 skipped; closing identical (see PHASE_5A_SUMMARY 2.1 on the interpreter trap) |

**Phase 3 still wins.** Where `01`–`07` already fixed a boundary — the
`ChamberGas` handshake, the provider layering, the forbidden dependencies —
Phase 5A elaborates it and does not redesign it. Any genuine contradiction is
reported as `PHASE_3_SPEC_CONFLICT` before the affected part is specified.

---

## Deliverables

Documents `08`–`15` are free; the requested names are used unchanged.

| # | Document | Answers |
| --- | --- | --- |
| 1 | `08_thermochemistry_architecture.md` | where the layer sits, what it owns, what it must never own |
| 2 | `09_thermochemistry_data_model_and_api_contracts.md` | Species, PropellantDefinition, PropellantStream, mixture, thermodynamic state, chamber state, provider protocol |
| 3 | `10_thermochemistry_provider_strategy.md` | Cantera, CEA/RocketCEA, tabulated, in-tree; capabilities, provenance, selection, fallback |
| 4 | `11_equilibrium_and_chemistry_mode_specification.md` | HP chamber, SP expansion, frozen, equilibrium, frozen-at-throat, condensed phases |
| 5 | `12_combustion_chamber_state_specification.md` | the chamber-state contract and the handshake into frozen Compressible v1 |
| 6 | `13_thermochemistry_verification_validation_plan.md` | reference sources, tolerance policy, test tiers, acceptance gates |
| 7 | `14_thermochemistry_future_dependency_map.md` | what consumes this layer, in what order, with what iteration |
| 8 | `15_thermochemistry_ui_integration_contracts.md` | what the interface shows, and what it must never imply |
| 9 | `PHASE_5A_SUMMARY.md` | the decisions, the ADRs, the open questions, the 5B recommendation |

---

## Steps

- [x] 0. Opening regression gate — 5 285 passed, 1 skipped
- [x] 1. Read Phase 3 `01`–`07` for every commitment about this layer
- [x] 2. Confirm document numbering does not conflict (08–15 free)
- [x] 3. `08` architecture: layer, ownership, forbidden dependencies, ADR anchors
- [x] 4. `09` data model: every type, field, unit, orientation, invariant
- [x] 5. `10` provider strategy: roles, capabilities, provenance, selection
- [x] 6. `11` chemistry modes: HP, SP, frozen, equilibrium, condensed phases
- [x] 7. `12` chamber state: the contract and the compressible handshake
- [x] 8. `13` V&V plan: sources, tolerances, tiers, gates
- [x] 9. `14` dependency map: consumers, order, iteration
- [x] 10. `15` UI contracts: display, provenance, honesty rules
- [x] 11. `PHASE_5A_SUMMARY.md`: ADR-17 onward, open questions, 5B scope
- [x] 12. Closing regression gate — expect 5 285 passed, 1 skipped, unchanged
- [x] 13. Verify the frozen compressible digest is untouched
- [x] 14. Final verdict: READY FOR PHASE 5B / NOT READY FOR PHASE 5B

---

## Note on the specification body

The Phase 5A instruction arrived with an unfilled placeholder,
`[PASTE THE PREVIOUS PHASE 5A PROMPT HERE]`, so no numbered specification body
was supplied. This checklist is therefore built from the requirements that
*were* given explicitly: the nine named deliverables and the twenty-five
mandatory discussion topics, which map onto them as follows.

| Topic | Document |
| --- | --- |
| Species model | `09` |
| PropellantDefinition | `09` |
| PropellantStream | `09` |
| blends / composition basis | `09` |
| canonical O/F definition | `09` |
| reactant temperatures and phases | `09`, `11` |
| thermodynamic state contract | `09` |
| chamber-equilibrium HP semantics | `11` |
| frozen chemistry | `11` |
| equilibrium expansion | `11` |
| frozen expansion | `11` |
| condensed-phase policy | `11` |
| provider capabilities | `10` |
| provider provenance | `10` |
| Cantera role | `10` |
| NASA CEA / RocketCEA role | `10` |
| fluid-property-provider boundary | `08`, `10` |
| coupling to frozen Compressible v1 | `12` |
| chamber-state contract | `12` |
| V&V strategy | `13` |
| ADR decisions | `PHASE_5A_SUMMARY.md` |
| blocking open questions | `PHASE_5A_SUMMARY.md` |
| exact Phase 5B recommendation | `PHASE_5A_SUMMARY.md` |

Where the missing body would plausibly have added constraints — the propellant
set in scope, whether a Fortran toolchain is acceptable for RocketCEA, whether
kinetics is wanted later — those are raised as **blocking open questions**
rather than silently decided.
