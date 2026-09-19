# CAD/CAE Workbench R1 — Structural Recovery Checkpoint

## RECOVERY_STATE

**PASS.** Full reasoning in
`docs/engineering/implementation/CAD_CAE_WORKBENCH_R1_STRUCTURAL_RECOVERY_FINAL.md`.
The product transformation the four prior workspace-redesign phases did
not achieve — a genuinely different shell composition, not the old
application with a palette and a collapsible sidebar — is now real,
verified by an independent blind review that identified the change as
structural rather than cosmetic.

| Field | Value |
| --- | --- |
| GLOBAL_SHELL_STATE | Recomposed. `SideNav` is now a state-aware Browser (`WorkspaceState` singleton, `RFBrowserItem` rows) rather than a page list; a genuine Home overview (`HomePage.qml`) now exists where none did before; both reuse Engine Design's own already-proven Browser/Inspector/Dock grammar rather than inventing a new one. |
| SHARED_COMPONENT_STATE | `RFPanel` gained an opt-in `chromeless` property (zero effect on any of its ~30 other consumers); `RFLineChart` gained real hover/cursor inspection (additive, zero effect on static rendering, verified against a real production consumer). `RFEngineeringTable` audited and found comparatively solid — not touched, correctly lower priority. |
| PLOT_SYSTEM_STATE | `RFLineChart` (ten real production consumers, the primitive users actually see) given a working hover crosshair + numerical readout — previously entirely absent from both chart primitives in this codebase. `RFPlotSurface` (Trade Study's own primitive, one consumer, unmigrated workspace) left as-is this phase — documented, not silently dropped. |
| TABLE_SYSTEM_STATE | Unchanged. Audited, found to already meet the bar (dense tabular figures, sticky header, non-filled special-row treatment, working scroll). |
| PROPERTY_EDITOR_STATE | Unchanged. Out of this phase's actual leverage — the audit found the page skeleton and shell, not the input-row grammar, was the dominant "still looks old" signal. |
| HOME_STATE | Built from nothing. Lists the five persistent-state workspaces plus Engine Design, each row showing that workspace's own live `statusLabel` (never a live input), no cards. |
| ACCEPTED_WORKSPACE_RECOMPOSITION_STATE | Line, Thermochemistry, Fluid Properties: primary object/result `RFPanel` now `chromeless:true`, Provenance/input panels stay bordered. Rocket Performance: already chromeless from its original pilot, confirmed unchanged. All four workspaces' own accepted scientific centerpieces, hierarchies, and stale-state behavior preserved exactly — recomposed into the new shell, not redesigned. |
| SKILL_EFFECT_STATE | `rf-engineering-workbench`, `rf-scientific-visualization`, `qt-ui-design` invoked live this phase with traceable recommendation → decision → implementation → rendered-evidence chains, recorded in `acceptance/cad_workbench_r1_structural_recovery/skill_design_trace.json`. `design-space-science-deck` not invoked — palette was correctly out of scope per the brief's own instruction to demote it. |
| VISUAL_DELTA_STATE | PASS. Independent blind subagent review (no prior context, "Candidate A/B" only) selected the after-state on all five required screens and named the reason as spatial/compositional, not palette — quoted in full in the final report. |
| SCIENCE_STATE | PASS. Zero Python files touched this phase. |
| SOLVE_CALL_STATE | PASS. Line and Fluid Properties re-verified after the full shell recomposition: 1 solve/evaluate per explicit action, 0 for every Browser/Dock/navigation/theme/resize/stale-edit interaction. |
| MEMORY_STATE | PASS. 191.84MB, decelerating, zero page-instance growth, zero Qt warnings, 100 rounds. |
| ACCESSIBILITY_STATE | Not regressed by construction: every new state distinction (Browser stale suffix, hover readout) carries text, not colour alone, following this program's own established rule; a dedicated fresh accessibility audit pass was not re-run this phase (the existing Theme-level contrast audit from the four-workspace-accepted checkpoint was not touched, since no new colour tokens were introduced). |
| BLOCKERS | None new. Carried forward: Thermochemistry's native-vs-corrected assigned-enthalpy capture gap; the `QVariantList`-vs-`RowListModel` cross-workspace investigation (Rule 1, still not migrated, still documented); the previously-documented mixed-session memory tail. New, deliberately deferred (not blocking): `RFLineChart`'s ten legacy consumers didn't get a full grid/tick visual redesign beyond the hover addition; the Browser's two-line row density is a documented opportunity, not a defect; `RFPlotSurface` hover was not added since its one consumer is Trade Study, unmigrated. |

## Real regressions found and fixed during this phase, not after

1. `HomePage.qml` referenced `EngineModel` without importing `../engine/model` — runtime `ReferenceError`, caught immediately by requiring zero Qt warnings on every capture, not inferred from a clean-looking screenshot.
2. `RFLineChart.qml`'s new hover overlay wrote `onHoverPointChanged` directly on the Canvas item for a property that lives on `root` — the same QML-scope failure class found earlier in this program (`ThermoChamberSchematic.qml`), fixed with the same established local-property-mirror idiom.
3. `HomePage.qml` hardcoded `"Thermochemistry"` as a duplicate label string, tripping this project's own cross-workspace guard test (`test_no_compressible_page_was_modified_by_this_phase`) — fixed by sourcing every label from `Navigation.items` instead, which is also a genuine deduplication, not a workaround.
4. The Browser's new two-line state-aware rows pushed the Engine Design entry below the fold at 1920×1080 — not caught by any capture in the required matrix (it only shows up at full rail height), caught by the independent blind review, fixed with this project's own established `ScrollBar.AlwaysOn`-when-overflowing precedent from `AnalysisDock`/Rocket Performance's own history.
5. The chart hover readout could overlap a data-driven guide-line label when hovering near it — found by opening the actual hover capture (not inferred), fixed by anchoring the readout to a fixed plot corner instead of following the cursor.

## Not started

Trade Study and Engine Design workspace recomposition, per the brief's
explicit instruction. The global shell now supports both — Engine Design
already used this grammar before this phase even began, and Trade Study's
own chart-heavy composition can adopt `RFPlotSurface`'s frameless
discipline directly when its turn comes, per the design thesis's own
stated sequencing.
