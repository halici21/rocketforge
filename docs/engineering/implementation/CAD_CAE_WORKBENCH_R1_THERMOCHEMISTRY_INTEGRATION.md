# CAD/CAE Workbench R1 — Thermochemistry integration (full redesign)

Unlike Rocket Performance (shell-wrap only, page already had a full
accepted pilot), Thermochemistry had no object-first centerpiece at all —
confirmed by reading `ThermoCalculator.qml` before writing anything: a
form beside a flat `GridLayout` of `RFResultValue` rows, exactly the
pre-pilot pattern the brief describes. Per the user's explicit choice
("full redesign per workspace now"), this workspace got the same
audit → design → implement → gate treatment the original Rocket
Performance pilot used, not a shell-wrap.

## What was built

**`ui/pages/thermochemistry/ThermoChamberSchematic.qml`** (new) — the
object: reactants → equilibrium chamber → products. Per
`rf-propulsion-visual-grammar` (invoked live before writing a line): CEA
solves a 0-D equilibrium state, not a flow field, so unlike
`PerfNozzleCanvas` there is *no* derived geometry at all — every position
is fixed, chosen for legibility only. Honesty label:
`EQUILIBRIUM STATE SCHEMATIC — NOT A REACTION-FLOW SOLUTION`. All
annotations (oxidiser/fuel/O-F/chamber pressure/products summary) are
sourced from `Thermochemistry.resultConditions` and `.condensed.headline`
— both `notify=resultChanged`, never the live input form — so the
schematic cannot relabel an unsolved edit as though it were the result.

**Tiered hero display** in `ThermoCalculator.qml` — the controller already
marks exactly three rows `emphasis: true` (`temperature`, `molar_mass`,
`gamma`, matching the brief's own "Tc primary, mean molecular mass
meaningful, exact gamma" almost verbatim), but the pre-existing layout gave
all three the same visual weight — three things tied for "large" is not a
hierarchy. Now `temperature` alone is the large hero (matching Isp's role
for Rocket Performance); `molar_mass`/`gamma` are medium-emphasized;
everything else stays in the existing, unmodified Advanced grid, filtered
by key so nothing is shown twice. `ThermoResultHeader`, `ThermoWarnings`,
the Advanced grid, `ThermoProvenance`, `ThermoDiagnostics` — all unchanged.

## Two real bugs found and fixed during this pass, not after

1. **Unqualified property scope failure.** The schematic's annotation
   `Item` originally declared `axis`/`chamberLeft`/`chamberRight`/`chamberHalf`
   and its child `Column`s referenced them unqualified — QML threw
   `ReferenceError: axis is not defined` at runtime despite the properties
   being visually nested correctly. Fixed by giving the `Item` an explicit
   `id` and qualifying every reference. Caught immediately by running the
   headless capture script after the first draft, before assuming it
   worked.
2. **PRODUCTS label overlap at 1366×768** — found by actually opening the
   1366×768 capture, not inferred from 0 Qt warnings (the render is
   syntactically valid either way; only the pixels show the defect). The
   condensed-state summary string ("No condensed phase above reporting
   threshold") had no width bound, so at the narrower floor its `Column`
   grew leftward over the chamber box. Fixed with a bounded, word-wrapped
   column (`Math.min(stations.width * 0.32, 230)`) instead of sizing from
   the text's own `implicitWidth`.

## Gates run

| Gate | Result |
| --- | --- |
| Python files touched | **Zero** (`git diff --stat rocketforge/` empty) — scientific correctness preserved by construction, not just by testing |
| Solve-call parity | calculate: 1 solve. Tab/Dock interaction: **0** additional. Editing an input (O/F 3.4 → 4.2) without recalculating: **0** — marks stale instead, per rf-scientific-ui-contract |
| Stale-vs-solved mismatch fixture (rf-visual-qa's required check) | **PASS**, verified by opening the capture: edited O/F 4.2 in the live form, schematic and hero both still correctly show the OLD solved O/F 3.4 and Tc 3598.29 K, with an "Inputs changed" badge and warning banner |
| States captured and manually inspected | default/below-reporting-threshold (dark 2560/1920/1366, light 1920), stale mismatch, and a fuel-rich O/F=1 case reaching **condensed products present** (Tc correctly drops to 1310.65 K, γ/molar-mass update consistently, PRODUCTS label reads "Condensed products present") |
| Memory (session soak, 100 rounds, now touching the new schematic) | 172.44 MB, second half (38.69) << first half (133.75) — decelerating, matches the pre-Thermochemistry-change soak (173.25 MB) closely, PASS |
| Full regression | base 6931/154, production 7086/2 — unchanged |
| Lint (qt_qml_lint.py) | clean against genuinely new code; all remaining findings cross-checked as pre-existing file conventions (`var`, loose equality, `ORD-1` ordering) already present before this session's edit, or matching `PerfNozzleCanvas.qml`'s own established Canvas-onPaint style exactly |
| `rf-visual-qa` (live Skill call) | asked what states were still missing; correctly named the condensed-present state as worth reaching, which is how the fuel-rich capture above happened |
| `qt-qml-review` (live Skill call) | asked about the unqualified-scope mechanism for the earlier bug; qualifying via explicit `id` confirmed as the correct, unambiguous general fix regardless of the exact QML engine scope-resolution edge case |

## Known remaining gap

The "native vs. corrected assigned enthalpy" state pair
(`rf-visual-qa`'s table) was not captured — reaching it needs a specific
reactant/temperature combination not yet identified, and the
`ThermoWarnings` component that displays it was not modified by this pass
(so it inherits whatever correctness it already had). Not chased further
given this session's length; flagged for a follow-up capture rather than
silently dropped.
