# DB-3A — Reference Engine Database UI v1

Status: implemented on `claude/sweet-volta-55s7ii`, baseline `b94cfc0`.
Scope: the first production, read-only view of the shipped reference-engine
corpus (DB-1 schema, DB-2A + DB-2B Wave 1 + Wave 2 records). No science, data,
rights, conflict, owner-decision, capability-rule, schema, topology, physics,
CEA or provider change.

## Product direction

A dedicated **Reference Engines** workspace (Navigation key `engines`,
appended as item 29 so no existing index moves) in the **Reference** rail
family, beside Equation Library and the Propulsion Database.

It is a separate workspace rather than a mode of the Propulsion Database
because that workspace's controller is built around propellant-formulation
records (composition, CEA compatibility probe, Open in Thermochemistry).
Engine configurations, five capabilities and topology graphs are a different
model, and merging them would have meant redesigning a frozen workspace. The
visual grammar is the same: the library and filters in the left drawer, the
selected configuration in the centre as the object, provenance in the shell
Inspector, and every row in the bottom drawer.

The user flows are:

- **Find an engine.** Search by name, designation, family, alias or id. Filter
  by capability and status, and by recorded cycle, including "No cycle
  recorded".
- **Inspect performance evidence.** Read the operating values with their
  conditions and operating points.
- **Understand what is missing.** "Not in this record" lists the backend's gaps.
- **Inspect topology.** A RocketForge drawing of the graph, with node and edge
  selection, zoom, Fit and Reset.
- **Inspect sources and rights.** Authority and shipping are shown as separate
  sections.

## Architecture

| layer | file | role |
|---|---|---|
| projection | `rocketforge/application/analysis/reference_engine_view.py` | Pure functions: catalog to display rows and readouts. No Qt, no provider, no physics, no I/O. |
| controller | `rocketforge/application/analysis/reference_engine_controller.py` | QML singleton `ReferenceEngines`. Loads and admits the corpus once, through `load_reference_engines()`, then publishes models and readouts. Only view-state slots exist. |
| page | `ui/pages/ReferenceEnginesPage.qml` | Header, library drawer, record, empty state, bottom drawer (Assertions / Connections). |
| parts | `ui/pages/referenceengines/` | `EngineLibrary`, `EngineRecord`, `EngineTopologyView`, `EngineInspector`. |
| wiring | `main.py`, `ui/data/Navigation.qml`, `ui/Main.qml`, `ui/shell/AnalysisInspector.qml` | Registration, route, inspector flag, inspector loader. |

The runtime reads only the shipped admitted corpus, through the existing
`reference_engine_catalog` and the capability API. It never reads
`docs/research`, manifests, DB-0.5 JSON, PDFs or renders. QML neither parses
the catalog nor interprets it: every word, status, group and node position
comes from the projection.

## Honesty rules the projection keeps

- **Values are shown as printed.**
  - A bare printed number takes its printed unit: `1,748,200` with `lb` reads
    `1,748,200 lb`.
  - An excerpt that already carries words, or ends in its unit, is shown
    alone. Nothing is converted, rounded or filled in.
  - An enum also shows the recorded token in words, for example "Recorded as:
    Liquid oxygen".
- **Conditions.** A condition recorded as `UNKNOWN` is shown as unknown. For
  example, RS-25 Block II chamber pressure reads "Pressure station: Unknown",
  and the Inspector reads "Unknown (not stated by the source)". A condition the
  record does not carry is not shown.
- **What the performance reference counts is kept apart.** The group
  "Performance reference values" holds exactly the assertions that the
  PERFORMANCE_REFERENCE evaluation counts: operating values and nozzle area
  ratio. Every other `performance.*` statement is listed under "Other
  performance statements", for example flow rates, throttle points, minimums,
  design values and text. Qualification life, hardware facts and dimensions go
  under "Other recorded facts". An excerpt that does not carry its own unit says
  "Unit as printed: …" beneath it.
- **Context is listed apart.** Values recorded for the variant, the family or a
  propulsion unit that contains the configuration (LMDE: UNIT-LM-DPS-FINAL) are
  listed as context, never as values of the configuration. Every shipped
  assertion is shown somewhere, which a test asserts.
- **The data table keeps the printed text and the recorded value apart.** Its
  "As printed" column is the excerpt itself; "Recorded as" gives the enum in
  words, the stored number exactly (never rounded) or "Text, as printed". A
  cell longer than its column ends in a visible ellipsis and shows whole on
  hover.
- **Missing performance is named.** It comes from the backend's gaps and is
  never a 0 or a dash. No table cell is empty: the cell reads "None printed",
  "None recorded" or "Not tied to one".
- **The five capabilities are reported independently.**
  - Each uses the backend vocabulary, as a word plus a shape (■ ◧ □) on a
    neutral surface. PARTIAL and NOT_SUPPORTED are evidence states, not error
    styling.
  - There is no score, count or overall grade.
  - REGRESSION_CANDIDATE is described as eligibility only.
- **Sources keep authority and rights apart.** The source Inspector shows
  technical authority separately from rights and shipping. An owner-reviewed
  reading is labelled as a RocketForge shipping-policy review, not a legal
  determination.

## Topology viewer

- **What is drawn.** Exactly the graph's own nodes and edges: no inferred
  node or edge, no merging. It is a RocketForge rendering and never the
  source figure.
- **Layout.**
  - Deterministic and presentation-only. Columns follow fluid-flow order;
    back edges are set aside by a depth-first pass in the graph's node order.
    A node with no fluid edge sits in its neighbour's column. Rows follow
    barycenter order.
  - Wires are orthogonal and run only through the empty column gaps and row
    gaps between boxes. A wire leaves its source's right side and enters its
    target's left side, at different heights, and overlapping wires get
    separate lanes. So no wire passes under a box it does not connect, and no
    two wires share a run unless they share an end. Tests check both for every
    shipped graph.
  - Python computes the positions and wire corner points.
  - The page states: "Connectivity is evidence; position is not."
- **Banners and chips.**
  - A third-party reconstruction (RD-170) gets a bordered banner naming who
    drew it.
  - A provenance chip and a completeness chip ("Incomplete by its own account
    · N known omissions") are shown, and the omissions are listed under the
    drawing.
  - A graph drawn for a propulsion unit says so (LMDE / UNIT-LM-DPS-FINAL).
- **Ownership.** Engine components have a solid outline. Stage, vehicle and
  ambient components have a dashed outline and name their owner.
- **Edge kinds.** Each kind has its own dash pattern and is named in the
  legend, never shown by colour alone. Every edge has an arrowhead.
- **Selection.** A node or an edge handle opens the Inspector. The
  Connections table gives keyboard and table access to every edge. Zoom, Fit
  and Reset change only the view.
- **No topology.** A configuration without a graph shows "No topology ships
  for this configuration" and draws nothing.

## Zero-solve and read-only evidence

`tests/application/test_reference_engines_runtime.py` drives the real shell
offscreen.

- **Instrument.** Every public function in physics, engineering, engine,
  providers and comparison is wrapped, as are the service solve entry points
  and the provider-gateway probes.
- **Controls.** A positive control and a negative control (real Isentropic
  solves) prove the instrument can see calls.
- **Sequence.** The test runs: enter; search; every filter through the QML
  controls; zero match and Clear; all 16 configurations, ten of them read in
  detail; every
  Inspector subject; zoom; both tables; the library drawer; both themes; three
  sizes; and leave and re-enter three times.
- **Watchers.** `open` and `io.open` (which `pathlib` uses) are watched, as
  are socket connections. Each watcher has its own positive control: a
  deliberate read and a deliberate connection that it must see.
- **Construction.** A fresh controller built under the instrument makes 0
  calls and reads only files under `rocketforge/data/evidence/engines`.
- **Result: 0 calls.** Browsing opens no file, and no socket connects. There
  are no Qt warnings, no edit, save or solve controls, no "validated" or score
  claims, and one page instance after re-entry.

The controller exposes no mutating slot, which a test asserts.

## Visual QA

`experiments/db3a_reference_engines/capture.py <out_dir>` captures the matrix.

- **Matrix.** 2560×1440, 1920×1080 and 1366×768, light and dark, for J-2, F-1,
  H-1 188K, LMDE final, J-2S, IPD, RD-170, RS-68A, LR87AJ-11 and RL10B-2.
- **Views.** For each, the record top and the topology panel, plus node,
  assertion and source Inspector states, the data drawer, and a no-match state.
- **Storage.** Captures are written outside the repository and are not
  committed.

QA findings fixed:

- A printed unit was appended to sentence excerpts (for example "…10 percent
  of the rated thrust %").
- Long table cells printed over the next column. In `RFEngineeringTable`, a
  left-aligned word cell now ends in a visible ellipsis and shows whole on
  hover. Number cells are unchanged.
- The header subtitle ran under the chips at 1366 px with the Inspector open.
- The status shapes were too small to read.
- Edge handles covered node labels.

Independent review findings fixed:

- Curved wires passed under boxes they did not connect, which drew connections
  the graph does not hold. They are now replaced by gap-only orthogonal
  routing.
- A silent cell clip could hide "Unknown". It is now replaced by a visible
  ellipsis plus a hover.
- Wording: what the performance reference counts, including area ratio.
- Unit notes on sentence excerpts.
- Propulsion-unit assertions are now shown.
- An exact "Recorded as" column.
- An edge's accessible name now gives its from and to.
- A source link from an assertion.
- One tautological test was rewritten, and the runtime watchers were made
  complete.

## Packaging

The new QML lives under `ui/`, and the controller lives in the `rocketforge`
package. Both ship through the existing mechanism that already carries `ui/`
and `data/evidence/engines`. No packaging change was needed.

## Not in scope

- No editing, import or promotion.
- No regression acceptance.
- No unit conversion.
- No reference record drives a design or a solver.
