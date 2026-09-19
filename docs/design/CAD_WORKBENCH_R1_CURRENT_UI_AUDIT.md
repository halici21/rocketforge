# CAD/CAE Workbench R1 — current UI audit

Evidence: `acceptance/cad_workbench_r1/current_ui_audit/` (8 headless
captures, 1920x1080 and 1366x768, dark and light, `0` Qt warnings once
`QT_QPA_FONTDIR` is pointed at a real font directory under the offscreen
platform — see the harness note in
`experiments/cad_workbench_r1/capture_current_shell.py`). Captured from the
real running application (`.venv-cea`), not mockups.

## Correction to this program's own premise

The brief assumes a "home experience" resembling a SaaS dashboard (activity
feed, KPI cards, project cards) that needs simplifying. **That page does not
exist.** `window.currentPageIndex` defaults to `0`, which is Isentropic
Flow — the first Analysis page. There is no dashboard to strip out. The real
question for Home (§43-44 of the brief) is *what the landing experience
should be*, not *what to remove from one*. Recorded here so later steps
build on what is actually true rather than the brief's inherited assumption.

## Finding: Engine Design already implements most of the target shell grammar

This is the single most important finding of this audit, and it changes the
shape of the upcoming shell-prototype comparison.

`engine_demo_dark_1920x1080.png` shows Engine Design, today, unmodified:

| Region | What it already is |
| --- | --- |
| Left (`EngineProjectPanel`, `ComponentPalette`) | A real **Model/System Browser** — the architecture tree grouped by subsystem (Feed System, Combustion, Expansion, Studies), not a flat page list |
| Center (`EngineCanvas`) | A real **Engineering Viewport** — typed-port schematic, pan/zoom/selection |
| Right (`EngineInspector`) | A real **Contextual Inspector** — architecture, contents, performance rows that stay as `—` with an explicit "Engine performance needs the solver" note rather than a fabricated number |
| Bottom (`BottomPanel`: Problems/Results/Messages) | A real, already-collapsible **Analysis Dock** |

Selection already flows through the system (canvas ↔ project tree ↔
inspector, confirmed against `EngineInspector.qml`'s selection-routing
described in the README). Honesty discipline is already present and good:
the empty state reads "Build your engine architecture... Drag components
from the palette, or load the demo engine," not a fake result; the loaded
demo shows `pc: —`, `L*: —`, "Engine performance needs the solver. These
rows exist to show where it will appear, and stay empty until then."

**Consequence for the shell-prototype phase:** the brief's conceptual shell
(§34) is not a novel invention to design from nothing — it is substantially
what Engine Design mode already is. The actual open design question is
narrower and harder than "invent a CAD shell": *should Analysis mode's
fourteen solver-backed pages adopt this same object-first grammar, stay a
distinct page-oriented mode with a shared visual language, or land somewhere
between?* Shell prototypes A/B/C should be framed around that question, not
around redesigning Engine Design's shell from a blank page.

## Analysis mode (`analysis_default_dark_1920x1080.png`, `..._1366x768.png`)

Already reasonably disciplined, not a form-and-card pile:

* Two-column calculator: input panel (`SOLVE FROM`, mono numeric fields,
  `PRESETS`, `MODEL` assumptions prose) + results panel (`RESULTS`, mono
  aligned values grouped by physical category) + a `REFERENCE CHECK` panel
  spanning both, each row PASS-badged against a cited published source.
* Left nav is a flat, grouped page list (Compressible Flow › Fundamentals /
  Wave Systems / Duct Flow / Applications / Analysis, then Thermochemistry,
  Rocket Performance, Trade Study, Fluids and Feed, Rocket Engine) — this
  *is* the page-oriented pattern the brief objects to (§32.2), and it is a
  real gap relative to Engine Design's object-first grammar.
* Section labels are uppercase with tracking (`SOLVE FROM`, `RESULTS`,
  `PRESETS`, `REFERENCE CHECK`) — moderate, not a "micro-label wall": five
  section headers on the densest page, not one per field.
* 1366×768: reflows correctly, no horizontal scroll, no global tiny-scale —
  the page scrolls vertically past the fold instead, matching README's
  documented behavior.
* Ember accent (`#D97F45`) used narrowly: active nav item bar, `Calculated`
  chip, focus states. Not flooded.

## Palette (current, from `ui/theme/Theme.qml`, both read in full)

Current identity is **Graphite / Ember**, not Obsidian / Champagne:
window `#131519`, surface `#191C21`, text `#E7E9EC`, accent `#D97F45`
(warm orange, "heat without alarm"). This is a real, deliberate,
already-good design system (documented surface ladder, one hairline
everywhere, no gradients, colour-never-alone selection marking) — the R1
palette change is a genuine token-value swap on top of working
infrastructure, not a rescue of a broken one.

## Typography / spacing (current, from `Typography.qml` / `Metrics.qml`)

Already close to what the brief asks for: humanist sans for prose, mono
only for engineering quantities and units (not the whole UI), spacing scale
already fixed at 2/4/8/12/16/20/24/32/40 (a superset of the brief's
suggested 8/16/24/40/64 — RocketForge's own scale is finer-grained and
already in use everywhere; kept as-is rather than replaced). Section-label
uppercase tracking is 1.1 — moderate, already restrained.

## Defects found (for the shared semantic layer, not per-page patches)

* **Font warnings under the offscreen capture harness are environment-only.**
  `QT_QPA_FONTDIR` was unset; captures without it render every glyph as a
  missing-tofu box. Not a product defect — recorded so the next person
  capturing evidence for this program does not misdiagnose it as one.
* `Theme.textMuted` contrast has not yet been re-verified against the
  *current* Graphite/Ember palette in this program (§26/§36 of the brief);
  see the open item in the checkpoint. The known prior concern was recorded
  against an earlier palette iteration and must be re-measured, not assumed
  either passing or failing.

## What this audit does NOT cover yet

Trade Study, Thermochemistry, Line, Fluid Properties, and the seven other
Analysis pages were not individually captured in this pass — the Isentropic
Flow landing page is representative of the *pattern* (two-pane
calculator + flat nav), and per-workspace audits are scoped to each
workspace's own migration step (brief §86-88), not the shell-level audit.
