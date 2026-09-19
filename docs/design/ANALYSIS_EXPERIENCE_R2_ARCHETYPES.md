# Analysis Experience R2 — Analysis Archetypes

Three pilots, deliberately related but compositionally different. The
point of the set is that Analysis mode does not get one universal
template.

## Archetype A — single-point analytical solver (Oblique Shock)

The question is "what does this shock do", and the answer is one angle.

- **Focal object**: the shock angle itself, at `Typography.readoutHero`
  (32 px mono, medium). Everything else on the page is smaller.
- **Inputs**: a 290 px chromeless rail — four real controls plus reference
  material (limits, presets, model assumptions) below a divider.
- **Secondary results**: the nine remaining quantities, grouped
  (Geometry / Flow / Shock jump / Total), at readout-small weight. They
  are evidence for the answer, not nine competing answers.
- **Both-branches mode** genuinely has two answers, so it gets two heroes
  rather than an invented single one.
- **Mode switch recomposes the workspace**: Calculator is numbers-led with
  a supporting chart; θ–β–M is chart-led, where the plot is the reason
  the view exists.

## Archetype B — state / physics solver (Thermochemistry)

The question is "what state does this chamber reach", and the object is
the chamber.

- **Focal object**: the equilibrium-chamber schematic, 210 px, present in
  **both** the solved and the unsolved state. In the unsolved state it is
  drawn dimmed with every annotation withheld — structure without claim.
- **Primary result**: chamber temperature at hero scale; mean molar mass
  and isentropic exponent one tier down.
- **Evidence** (composition, provenance, diagnostics) is secondary and
  scrolls beneath, or moves to its own tab.
- The unsolved state is the archetype's real test: it must read as an
  instrument waiting for an input, not as an empty page apologising.

## Archetype C — parametric / trade analysis (Trade Study)

The question is "how does the system respond as this variable changes",
and the object is the evaluated trade itself.

- **Focal object**: the response curves. Each enabled metric takes an
  equal share of the real workspace height, with a 220 px floor — not a
  fixed 200 px card stacked under the controls.
- **Study definition** lives on its own tab, so it does not compete with
  the trade once results exist.
- **Design space** (two or more variables) switches to the scatter/Pareto
  projection, with the Selected Design Inspector carrying the
  single-design detail.

## What the three share

Navigation, typography scale, spacing rhythm, control heights, the
chromeless-by-default surface discipline, the chart grammar
(`RFLineChart` / `RFPlotSurface`), status and stale semantics, champagne
reserved for selection and focus, and provenance treatment. They differ
only where their engineering question differs.
