# Documentation index

RocketForge's engineering process writes down its own history: specs before
a phase, a checkpoint document if it runs long, and a verification/report
document at the end. This page is a map into that, organized by what you're
actually looking for rather than by file-creation order.

**New here?** Start with the root [README.md](../README.md) — this
directory is the paper trail behind its claims, not a second entry point.

## Start here

| If you want to know... | Read |
| --- | --- |
| What's real physics vs. UI mockup, right now | [README.md § Verification and freeze status](../README.md#verification-and-freeze-status) |
| Whether NASA CEA and Cantera are actually correct | [engineering/verification/CEA_CANTERA_VERIFICATION_R1.md](engineering/verification/CEA_CANTERA_VERIFICATION_R1.md) |
| Why Cantera exists but isn't a runtime dependency | [engineering/implementation/PHASE_5B0_CEA_CANTERA_PROVIDER_SPIKE.md](engineering/implementation/PHASE_5B0_CEA_CANTERA_PROVIDER_SPIKE.md) |
| Which RocketForge you are running, and how to build and launch it | [engineering/release/BUILD_AND_LAUNCH.md](engineering/release/BUILD_AND_LAUNCH.md) |
| What Engine Design mode can and can't do | [../acceptance/cad_workbench_r1/engine_component_inventory.json](../acceptance) (gitignored — regenerate locally, or see the summary in the root README) |
| What the `.claude/skills/` design tooling is and why | [design/skills/DESIGN_SKILL_FOUNDATION_R1_REPORT.md](design/skills/DESIGN_SKILL_FOUNDATION_R1_REPORT.md) |

## Architecture & specifications (`engineering/`)

The numbered files are the original phase-by-phase specs, each still the
reference for the API/contract it defines — not superseded just because a
later phase shipped.

* [01_engineering_architecture.md](engineering/01_engineering_architecture.md) — the seven-layer architecture (`core → physics → engineering → engine → providers → application → ui`) and why SciPy/pandas are excluded
* [02_data_model_and_api_contracts.md](engineering/02_data_model_and_api_contracts.md), [04_numerical_methods_and_domain_policy.md](engineering/04_numerical_methods_and_domain_policy.md) — core data types and numerical policy
* [03_compressible_flow_specification.md](engineering/03_compressible_flow_specification.md) → [COMPRESSIBLE_FLOW_API_V1.md](engineering/COMPRESSIBLE_FLOW_API_V1.md), [COMPRESSIBLE_VALIDATION_MATRIX.md](engineering/COMPRESSIBLE_VALIDATION_MATRIX.md) — classic gas dynamics, frozen
* [08_thermochemistry_architecture.md](engineering/08_thermochemistry_architecture.md) → [10_thermochemistry_provider_strategy.md](engineering/10_thermochemistry_provider_strategy.md), [THERMOCHEMISTRY_API_V1.md](engineering/THERMOCHEMISTRY_API_V1.md), [CEA_PROVIDER_CONTRACT.md](engineering/CEA_PROVIDER_CONTRACT.md), [REACTANT_ENTHALPY_COUPLING_CONTRACT.md](engineering/REACTANT_ENTHALPY_COUPLING_CONTRACT.md) — thermochemistry provider architecture and its frozen contracts
* [FLUID_PROPERTIES_API_V1.md](engineering/FLUID_PROPERTIES_API_V1.md), [FLUID_PROPERTY_PROVIDER_CONTRACT.md](engineering/FLUID_PROPERTY_PROVIDER_CONTRACT.md) — fluid properties
* [LINE_API_V1.md](engineering/LINE_API_V1.md), [METHANE_TRANSPORT_VALIDATION.md](engineering/METHANE_TRANSPORT_VALIDATION.md) — line/transport
* [PROPULSION_ANALYSIS_API_V1.md](engineering/PROPULSION_ANALYSIS_API_V1.md), [ROCKET_PERFORMANCE_API_V1.md](engineering/ROCKET_PERFORMANCE_API_V1.md), [PROPULSION_ANALYSIS_LIMITATIONS.md](engineering/PROPULSION_ANALYSIS_LIMITATIONS.md) — chamber+nozzle performance chain (c*, Cf, Isp) and its explicit, stated limits
* [TRADE_STUDY_API_V1.md](engineering/TRADE_STUDY_API_V1.md) — Trade Study's design-space evaluation semantics
* `*_UI_CONTRACT.md` files — what each Analysis page's controller guarantees to the QML layer

## Implementation history (`engineering/implementation/`)

One document (usually `PHASE_*` or a named checkpoint) per completed unit of
work, in the order they happened:

`PHASE_4A` → `4B` → `4C` → `4D` → `4E` → `4F` → `4G` (classic gas dynamics,
built and frozen) → `PHASE_5B0` (CEA vs. Cantera provider decision) →
`5B` → `5C` (thermochemistry core + CEA provider) → `5D` (thermochemistry
UI) → `5E` (ideal rocket performance) → `5F` (trade study) → `5G`
(integrated propulsion acceptance — the v1.0 freeze) →
`FLUIDS_FOUNDATION_AND_REACTANT_COUPLING` (fluid properties) →
`METHANE_TRANSPORT_AND_LINE_IMPLEMENTATION` (line v1.0) →
`ROCKET_PERFORMANCE_VISUAL_ARCHITECTURE_PILOT` (the current visual design,
piloted on one page before nothing else was rolled out further) →
`QML_MEMORY_ROOT_CAUSE` (a diagnosed-and-fixed measurement artifact, not a
real leak) → `CEA_CANTERA_VERIFICATION_CHECKPOINT` (the most recent, see
Verification below).

## Verification campaigns (`engineering/verification/`)

Independent, gated verification runs — not written by the same pass that
built the feature:

* [CEA_CANTERA_VERIFICATION_R1.md](engineering/verification/CEA_CANTERA_VERIFICATION_R1.md) — top-level report
* [CEA_VERIFICATION_DETAILS.md](engineering/verification/CEA_VERIFICATION_DETAILS.md) — NASA CEA, Part A
* [CANTERA_VERIFICATION_DETAILS.md](engineering/verification/CANTERA_VERIFICATION_DETAILS.md) — Cantera, Part B
* [CEA_CANTERA_CROSS_MODEL_COMPARISON.md](engineering/verification/CEA_CANTERA_CROSS_MODEL_COMPARISON.md) — cross-provider consistency and RocketForge-integration audit, Parts C/D

## Design system & tooling (`design/skills/`)

The project-local Agent Skills stack used for UI/visual work, and its live
qualification run:

* [DESIGN_SKILL_FOUNDATION_R1_REPORT.md](design/skills/DESIGN_SKILL_FOUNDATION_R1_REPORT.md) — what was installed and why (ownership matrix, licenses, security review)
* [live_eval_r1/DESIGN_SKILL_LIVE_EVAL_R1_REPORT.md](design/skills/live_eval_r1/DESIGN_SKILL_LIVE_EVAL_R1_REPORT.md) — does it actually change agent behavior, measured against a generic baseline

## A note on the `PHASE_*` naming

Phase numbers reflect the order features were actually built in, not a
roadmap that was planned upfront and then executed — several documents
(`06_future_module_dependency_map.md`,
[PROPULSION_ANALYSIS_LIMITATIONS.md](engineering/PROPULSION_ANALYSIS_LIMITATIONS.md))
are explicit about what's still ahead rather than implying it's covered.
