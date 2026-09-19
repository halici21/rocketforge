# RocketForge — Current Product Design Audit R2

Audit only. No production code, theme, asset, test or packaging file was
modified in this run.

Basis: 48 captures of the current build (1920×1080 dark primary, plus
1366×768, 2560×1440 and 1920×1080 light), each opened and inspected
individually. Engineering gates — tests, warnings, memory, solve-call
parity — were deliberately excluded from judgement.

## The one-sentence finding

**RocketForge's best analysis surfaces already exist, and the product
opens on its worst ones.**

Isentropic Flow's default tab shows fourteen equal-weight numbers and no
visual; its third tab holds a 620 px full-width chart with a quantity
selector, a log-axis toggle and an M = 1 reference. Nozzle Lab's default
tab shows twenty-two equal-weight numbers and no nozzle; its second tab
holds a regime band map with named thresholds and a 440 px shock-station
chart. Both hidden surfaces are good. Both default surfaces are
calculators. That inversion, repeated across six to eight modules, is
where most of the "collection of calculators" impression comes from — and
it is cheaper to fix than anything else in this report.

## Classification

Closest current category: **a well-organised collection of calculators
with unusually rigorous scientific discipline.** Three screens (Rocket
Performance, the Oblique Shock and Thermochemistry pilots) reach
*scientific desktop application*. None of the product reaches *mature
CAD/CAE workstation*, because Analysis mode has no toolbar, no persistent
model tree, no docking and no multi-view — Engine Design has all four.

## Score

Overall **5.5 / 10** — coherent and functional, not yet premium. An
independent reviewer given only the screenshots scored it **4 / 10**. The
gap is a weighting difference, not a factual one; both agree the product
is below professional-commercial standard and well above broken. See
`acceptance/design_audit_r2/second_review.json`.

## What is genuinely good

These are real strengths, not consolation:

- **Scientific credibility is visible, not just internal.** Provenance
  rows, honesty labels, refusal states, published-reference checks with
  PASS/residual columns, explicit friction-factor convention, stale
  semantics. Very few products in this class show their work this openly.
- **Rocket Performance** is a genuine three-zone workbench: input rail,
  a data-driven nozzle that actually changes with the solved area ratio,
  and a result rail with Isp as an unmistakable hero. Both reviewers
  independently named it the strongest screen.
- **Nozzle Lab's Regimes tab** — a regime band map with the current state
  marked and thresholds named, over a real chart. The second-best
  composition in the product, and almost nobody will see it.
- **The Obsidian/Champagne dark register**: warm neutral surfaces, no pure
  black, accent genuinely restrained.
- **Engine Design's grammar**: browser, canvas, contextual inspector,
  dock, toolbar, breadcrumb. It is the only part of the product that is
  structurally a workbench.

## What looks weak, amateur or unfinished

- **Dead space is the product's dominant visual characteristic.** Fluid
  Properties ~55% empty. Trade Study Results ~55% empty below the table.
  Isentropic's input rail ~270 px of nothing. Home at 2560×1440 ~65%
  empty — the content simply does not reflow.
- **Truncated table headers beside unused width.** Trade Study Results
  shows "Chamber temperatur…", "Characteristic veloci…", "Specific
  impulse Isp…" while roughly 950 px of table width sits empty. This is
  the kind of defect a reviewer notices in the first two seconds.
- **A clipped axis title.** The rotated y-axis label on the Trade Study
  sweep renders as a single stray glyph at the plot's left margin.
- **Tick values are raw data-range divisions**: 335.62 / 340.07 / 344.51
  / 348.95 / 353.39. A scientific audience reads that as unfinished.
- **Two chart palettes.** Trade Study draws blue; every other chart in
  the product draws champagne.
- **Light theme is not fully treated.** In light mode the Rocket
  Performance nozzle loses its interior fill entirely and becomes an
  unfilled outline on cream — the body/section distinction that carries
  the drawing in dark is simply gone.
- **The family rail is four-letter stubs.** FLOW / CHEM / PROP / TRADE /
  FLUID / REF — no icons, no glyph vocabulary. Both reviewers
  independently read it as placeholder art awaiting real icons.
- **The shell announces that it is unfinished**: a "UI PREVIEW" badge
  beside the wordmark, and an "Untitled workspace" selector implying a
  document model the application does not have.

## What creates the "calculator collection" feeling

Four things, in order of contribution:

1. **The default view of most modules is a number grid.** (See the
   one-sentence finding above.)
2. **No focal point.** Fourteen values on Isentropic, twenty-two on
   Nozzle Lab, six on Fluid Properties — all at identical size and
   weight. Nothing tells the eye where the answer is.
3. **The engineering object is missing on most screens.** A page called
   Nozzle Lab, entirely about converging-diverging geometry and an
   internal shock, contains no nozzle in its default state.
4. **Every module looks structurally identical** regardless of what it
   computes: rail, then boxes, then numbers. Switching workspaces feels
   like opening another page rather than entering another engineering
   context.

## What creates an AI-generated-UI impression

Concretely, not as a general worry:

- One-component-per-box composition — Nozzle Lab stacks four bordered
  cards, Isentropic three.
- Generic centred empty states floating in large voids.
- Uppercase micro-labels used as the default section device (9 on
  Isentropic, 13 on Nozzle Lab, 12 on Thermochemistry solved).
- Dashed placeholder wireframe regions labelled INPUTS / VISUALISATION /
  READOUT on the unfinished routes.
- Schematics that look like diagrams but carry little geometric
  information, sitting in the primary position with a disclaimer under
  them. The second reviewer called this the strongest AI tell in the set;
  see the disagreement section below for where I agree and where I do not.

## What creates legacy-engineering clutter

- 10.5 px chart axis type on plots up to 620 px tall.
- Paragraph helper text interleaved into control stacks rather than
  disclosed on demand.
- Provenance occupying a full-height column of roughly the same area as
  the results it annotates.
- Label–value pairs separated by up to ~370 px of empty space.

## Screen-by-screen prescription

### Oblique Shock — P1

Current: the R2 pilot works. Shock angle is a real hero, the cards are
gone, the chart is 320 px. Remaining problems: three tabs where the brief
asked for two, the Study tab is a 47-row table nobody asked to see first,
and the chart still does not mark the solved point on the curve.

Keep: hero treatment, chromeless composition, collision-aware labels.
Remove: the separate Study table tab as a peer of the other two.
Recompose: two modes — Calculator (numbers lead, chart supports) and
Study (chart leads, table becomes a bottom drawer).
Focal object: Calculator → β. Study → the θ–β–M curve.

```
CALCULATOR                                    STUDY
┌──────┬──────────────────────────┐  ┌──────┬──────────────────────────┐
│ M₁   │  β                       │  │ M₁ γ │                          │
│ θ    │  39.3139°                │  │ ──── │                          │
│ γ    │                          │  │ weak │      θ–β–M, 70-75%       │
│      │  M₂ 1.64  p₂/p₁ 1.71     │  │ both │      of content height   │
│ weak │  T₂/T₁ 1.17  Δs/R 0.015  │  │      │      solved point marked │
│ ──── │──────────────────────────│  │ μ    │                          │
│ μ    │                          │  │ θmax │                          │
│ θmax │   θ–β–M, supporting      │  └──────┴──────────────────────────┘
│      │   ~35% height           │   ▸ sweep table (collapsed drawer)
└──────┴──────────────────────────┘
```

### Nozzle Lab — P0

Current: the worst composition in the product. Four bordered cards,
twenty-two equal-weight numbers, no nozzle, and the genuinely good
Regimes view hidden behind a tab.

Keep: the regime band map and the shock-station chart — they are good.
Remove: the Calculator tab as the default; the four-card structure.
Recompose: make Regimes the landing view; put a real nozzle drawing at
the centre with the shock station marked on it.
Focal object: the nozzle with its current regime and shock position.

```
┌────────────┬────────────────────────────────────┬──────────────┐
│ RESERVOIR  │  ═══╗         ╔═══════════         │ REGIME       │
│ p₀ T₀      │      ╲       ╱      ▲              │ Internal     │
│            │       ╲_____╱       │ shock at     │ normal shock │
│ NOZZLE     │        throat    A_s/A_t 1.51      │              │
│ A_t  Ae/At │                                    │ ṁ  7.379     │
│            │  UNCHOKED │▓SHOCK▓│ OVER │ UNDER   │ M_e 0.407    │
│ BACK PRESS │           ▲ current                │ p_e 700 kPa  │
│ ▭────────  │                                    │              │
└────────────┴────────────────────────────────────┴──────────────┘
                ▸ shock station vs back pressure (chart, collapsed)
```

### Thermochemistry — P2

Current: the R2 pilot fixed the dead unsolved state and gave the chamber
temperature a hero. Remaining problem: the chamber schematic occupies
~30% of the primary region while carrying almost no geometric
information — CEA solves a 0-D state, so there is no geometry to draw.

Keep: the honest unsolved state, the hero, the provenance discipline.
Remove: nothing scientific. Reduce the schematic's *size*, not its truth.
Recompose: schematic to a ~120–140 px band that carries station values
(reactants in, O/F, p_c, products out) rather than area; give the
reclaimed space to composition, which is the actual evidence.
Focal object: chamber temperature, with composition promoted beside it.

```
┌────────────┬───────────────────────────────────────────────────┐
│ REACTANTS  │  LOX ──▶┌─────────┐──▶ products                   │
│ LOX  90 K  │  LCH₄ ─▶│ p_c 10  │    no condensed phase         │
│ LCH₄ 112 K │         └─────────┘                               │
│ O/F  3.4   │                                                   │
│ p_c  10    │  3598.29 K        M̄ 0.0218      γ 1.133          │
│            │  ───────────────────────────────────────────────  │
│ [Calculate]│  COMPOSITION (promoted — the real evidence)       │
│            │  H₂O 0.31   CO 0.19   CO₂ 0.11   H₂ 0.09  ...     │
└────────────┴───────────────────────────────────────────────────┘
```

### Trade Study — P1

Current: the sweep now fills the workspace, which was the right fix. But
the chart has a clipped axis title, non-round ticks and the only blue
series in the product; Results has truncated headers and ~55% dead space.

Keep: sweep dominance, the Selected Design inspector, Pareto projection
honesty.
Remove: the permanently-visible bottom summary cards on Results.
Recompose: table sized to content with an evidence dock; axis craft fixed
at shared-component level.
Focal object: the response curve with the selected design marked.

```
┌─────────────────────────────────────────────┬─────────────────┐
│ O/F sweep        [Isp][c*][T₀]  ▢ normalise │ SELECTED DESIGN │
│                                             │ Point 2         │
│   Isp                                       │ O/F 3.24        │
│   353 ┤      ╭──╮                           │ ─────────────── │
│       │    ╭─╯  ╰──╮        ← round ticks   │ Isp   350.803   │
│   345 ┤  ╭─╯       ╰───╮    ← axis title    │ c*   1822.66    │
│       │ ╱   ▲selected   ╰─╮    not clipped  │ T₀   3574.3     │
│   337 ┼─────────────────────                │ Feasible        │
│       2.6      3.4      4.2  O/F            │                 │
└─────────────────────────────────────────────┴─────────────────┘
  ▸ evaluated points table (dock, collapsed by default)
```

### Rocket Performance — P2

Current: the strongest screen. Only real defect is the light-theme fill
loss. Keep everything; fix the theme-aware fill; use it as the template
for Phase 3 rollout.

### Fluid Properties — P1

Current: ~55% empty, six values with no hero, provenance occupying a
result-sized column. Recompose to two measured columns with density as
hero and provenance behind a disclosure. No schematic — correct, since
the provider returns no sampled boundary data.

### Line — P2

Current: acceptable. The straight-pipe schematic is honest and the Darcy
convention is stated. Reduce schematic height, promote Δp to hero.

### Engine Design — keep

Current: the strongest *grammar* in the product; genuinely a workbench.
Two defects: the canvas sits ~70% empty when the demo loads without a
fit, and "STUDIES planned" placeholder rows remain in the browser after
Analysis-mode placeholders were hidden. Do not restyle it to match
Analysis; fix those two and leave it alone.

### Analysis navigation — P2

Current: the 64 px family rail plus contextual drawer is a genuine
improvement and should be kept. Two problems: the four-letter stubs need
real icons, and the rail shows no indication of which families hold
solved work — the state information that made the old browser useful was
lost in the narrowing.

### Home — P1

Current: honest and quiet, but at 2560 it is a narrow link column in
65% emptiness, and it adds little over the rail. Either make it a real
engineering start surface (recent cases with their actual result
headlines) or remove it and reopen the last active workspace.

## Shared component verdict

| Component | Verdict | Reason |
| --- | --- | --- |
| `RFLineChart` | **REDESIGN** | Nice-number ticks, own type scale, solved-point marking, theme-aware strokes, one palette. Not a rewrite — its structure is sound. |
| `RFPlotSurface` | **REFINE** | Fix the clipped rotated axis title; share the tick and type rules with RFLineChart rather than diverging. |
| `RFEngineeringTable` | **REFINE** | Header truncation and width distribution. Numeric alignment is already correct. |
| `RFPanel` | **REFINE** | `chromeless` should become the default and the border the exception, not the reverse. |
| `RFResultValue` | **KEEP** | The hero scale added in R2 works. It simply is not used widely enough. |
| `RFStatusChip` | **REFINE** | Too many states rendered as identical pills; the important ones do not outrank the routine ones. |
| Property rows | **REFINE** | The field control is good; the rails around it need structure and on-demand help text. |
| Navigation | **REFINE** | Keep the two-level model; add icons and per-family state. |
| Tabs | **REDESIGN** | The defaulting is the product's single biggest problem — which tab opens is a design decision, not a detail. |
| Toolbar | **KEEP** in Engine Design; **ADD** in Analysis — its absence is why Analysis does not read as CAD/CAE. |

## Disagreement with the independent reviewer

The second reviewer called the Thermochemistry and Line schematics
"placeholder art in the primary position", named their disclaimer captions
the strongest AI tell in the set, and recommended making them data-driven
— "station-coloured, proportioned to actual state".

They are right about the proportion and wrong about the remedy. CEA solves
a 0-D equilibrium state and `engineering.line` solves distributed friction
in a straight pipe; neither produces geometry. "Proportioned to actual
state" would mean drawing a shape the physics never computed, which is the
one thing this product has consistently refused to do — and the disclaimer
they read as a tell is precisely why it has not. The correct action is
their own alternative: shrink the schematic and let it carry the state it
genuinely has, rather than inventing proportion it does not.

Adopt the size reduction. Reject the fabrication. Recorded rather than
reconciled.

## Recommended implementation order

1. **Default-view inversion** — make the existing analysis surfaces the
   landing view. Highest impact per unit of work in the entire product.
2. **Chart craft** — ticks, clipped title, one palette, chart type scale,
   theme-aware fills.
3. **Hierarchy rollout** — one hero per workspace, using the pattern
   already proven on three screens.
4. **Space discipline** — reflow to columns, size panels to content,
   use width above 1920.
5. **Object restoration** — a real nozzle in Nozzle Lab; schematics that
   carry no geometry reduced to glyph scale.
6. **Chrome and identity** — rail icons, remove the preview badge, hide
   the remaining planned placeholders in Engine Design.
