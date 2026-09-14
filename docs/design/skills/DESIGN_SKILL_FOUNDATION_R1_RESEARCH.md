# Design Skill Foundation R1 — Research

What was actually inspected, with dates and evidence, before any selection
decision. All research was done by reading real repository contents (via
`gh api` against the GitHub REST API and `git clone --depth 1`), not by
summarizing from memory or from a repository's own marketing description.

---

## 1. RocketForge itself, first

Before researching external skills, the following was read directly:

- `README.md` (note: partially stale — describes an earlier UI-only phase;
  the actual application has a full frozen scientific stack behind it, see
  `docs/engineering/implementation/PHASE_5G_INTEGRATED_PROPULSION_ACCEPTANCE.md`
  and the propulsion/fluids/line freeze contracts — this staleness is
  reported, not corrected, since correcting `README.md` is production
  documentation work outside this run's scope).
- `docs/design/` — the Rocket Performance visual audit and pilot report.
- `docs/engineering/implementation/ROCKET_PERFORMANCE_VISUAL_ARCHITECTURE_PILOT.md`,
  `ROCKET_PERFORMANCE_VISUAL_PILOT_CHECKPOINT.md`.
- `docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md`,
  `QML_MEMORY_AND_VISUAL_ROLLOUT_CHECKPOINT.md` — the memory investigation
  from the immediately preceding program.
- `ui/theme/Theme.qml`, `Typography.qml`, `Metrics.qml`, `Motion.qml` — the
  token system.
- `ui/components/` (30 files) — read in full listing, read source for
  `RFPlotSurface.qml`, `RFEngineeringTable.qml`, `RFScrollBar.qml`.
- `ui/pages/` — full listing (17 top-level pages, 10 per-workspace
  subdirectories); read `TradeStudyPage.qml`, `StudyPareto.qml`,
  `StudyResults.qml`, `StudySetup.qml` for the Trade Study
  Pareto-projection discipline already in place.
- `ui/shell/` (`SideNav`, `WorkspaceHost`, `StatusBar`, `TopBar`,
  `SettingsPanel`) and `ui/engine/` (17 files: `EngineCanvas`,
  `EngineInspector`, `BottomPanel`, `ComponentPalette`, etc.) — the existing
  CAD/CAE-shaped shell in the Engine Design workspace.
- `rocketforge/application/rowmodel.py` — the stable row-model pattern from
  the memory investigation.
- `acceptance/qml_memory/` — the actual measurement evidence backing the
  memory root-cause report.
- `.git` status — confirmed a clean working tree before this run began, and
  confirmed no production path (`rocketforge/`, `ui/`) was touched by this
  run's own work.

## 2. Official Anthropic skills — `anthropics/skills`

Fetched via `gh api repos/anthropics/skills/contents/skills` (public repo,
175k+ stars, actively maintained, pushed within the current week).

- **`frontend-design`** — read in full. Apache-2.0 licensed
  (`LICENSE.txt` per-skill). Web/CSS-scoped (discusses hero sections, CSS
  selector specificity, `.section`/`.cta` class conflicts). Its calibration
  section on generic-AI-design tells (warm-cream + terracotta defaults,
  ALL-CAPS eyebrow labels, em-dash-joined meta strings, gradient SaaS
  cards) is genuinely platform-agnostic and was folded into
  `rf-engineering-workbench`'s reference material as citation, not as an
  installed active skill — see the licenses and matrix documents for the
  install-vs-reference reasoning.
- **`skill-creator`** — read in full, including `references/schemas.md`
  pointers and the eval-running/iteration-loop process. Used as the
  authoring authority for every custom skill in this run: frontmatter
  shape, imperative writing style, "explain the why instead of a heavy
  MUST," progressive disclosure via `references/`, and the eval-schema
  conventions (`evals/evals.json`, assertions, grading fields) referenced
  in the evals document.
- The official `template/SKILL.md` was fetched as the minimal frontmatter
  reference.

## 3. Interface specialist skills — `jakubkrehel/skills`

Fetched via `gh api` (MIT license, 6023 stars, pushed within the last two
weeks — current). Eleven skills:
`better-accessibility`, `better-colors`, `better-interface`, `better-layout`,
`better-typography`, `better-ui`, `better-writing`, `break`,
`explain-interface`, `interface-review`, `variant`.

Read the `SKILL.md` head of `better-interface`, `better-ui`,
`better-layout`, `better-typography`, `better-colors`,
`better-accessibility`, and `interface-review` directly. The family's
architecture — a strict ownership boundary stated explicitly in every
skill ("X belongs to Y, never duplicate here") — is an excellent structural
model and was consciously imitated in every RocketForge custom skill's own
"Ownership" section.

The content itself is CSS/web-scoped with **exact, hard-coded values** tied
to that platform: literal `cubic-bezier(0.2, 0, 0, 1)` curves, a companion
`css-cheat-sheet.md` that "maps each declaration to its Tailwind
equivalent," ARIA-specific accessibility guidance. None of this maps onto
QML, which has no CSS, no DOM, no Tailwind, and its own accessibility API
(`Accessible.role`/`Accessible.name`) entirely distinct from ARIA. See the
matrix and licenses documents for why this became reference-only rather
than installed.

## 4. Independent design review — `humbleteam/design-review`

Fetched via `gh api` and `git clone`. MIT license, 3 stars, pushed within
the last day (2026-09-08 at research time) — new and low-adoption, but read
in full because it directly matches the requested role. Platform-agnostic
by construction (works on a screenshot, URL, or HTML snippet — no CSS/React
output requirement), with a real rubric: a 0–4 scoring band with an
explicit tie-break rule, a hard cap of 6 ranked issues, mandatory
Before/After/Why per issue with exactly one citation (a Nielsen heuristic,
a WCAG 2.2 success criterion, or a named platform guideline). No scripts,
no network calls — pure markdown. **Installed.**

A near-duplicate, `Bbasche/design-review` (3 stars, last pushed five months
before this research date, narrower "frontend UI" framing), was checked and
passed over in favor of the humbleteam version's broader input handling and
more rigorous rubric.

## 5. Other UI skill repositories — `dawitlabs/ui-skills`

Fetched via `gh api`. MIT license, 5 stars, last pushed roughly four months
before this research date. Ten skills including `landing`, `ui-init`,
`design-grill` (a "12-question interview" producing a `DESIGN-BRIEF.md`).
The naming and README framing ("landing" pages, brand color coverage
percentages, a design-brief interview workflow) are consumer-website/SaaS
marketing-site oriented — exactly the category the brief said to reject
unless conceptual guidance survives. Read the README in full; found no
guidance not already better covered by `qt-ui-design` (Qt-specific, current)
or already rejected from `jakubkrehel/skills` for the same platform
mismatch. **Rejected wholesale**, staleness and narrow web-marketing scope
both cited.

## 6. Qt / QML / PySide — high-priority search

Searched GitHub repository and code search (`gh api search/repositories`,
`search/code`) for combinations of `QML`, `PySide6`, `Qt Quick`, `agent
skill`, `SKILL.md`. Found and evaluated:

- **`TheQtCompanyRnD/agent-skills`** — "Official Qt AI engineering skills
  for Claude Code," 416 stars, pushed within roughly two months of this
  research date, dual-licensed `LicenseRef-Qt-Commercial OR BSD-3-Clause`
  (the BSD-3-Clause option was used for this project-local copy). Twelve
  skills; read `qt-qml` and `qt-ui-design` in full, `qt-qml-review` and
  `qt-qml-profiler` headers, `metadata.qt-version: "6.x"` confirmed on
  every skill inspected — no Qt5-era guidance present. **`qt-qml`,
  `qt-ui-design`, and `qt-qml-review` installed**; `qt-qml-review`'s bundled
  `references/lint-scripts/qt_qml_lint.py` (1486 lines) was read in full
  and confirmed to import only `json`, `re`, `sys`, `dataclasses`,
  `pathlib`, `typing` — no subprocess, network, file-write, or
  eval/exec calls; a pure static read-only linter. See the security
  document for the full audit trail.
- `qt-qml-profiler` — read its `README.md`: its automation assumes a CMake
  C++ build (`adds -DQT_QML_DEBUG via CMAKE_CXX_FLAGS`) and locates
  `qmlprofiler` via `CMAKE_PREFIX_PATH`/`Qt6_DIR`. RocketForge is a
  Python/PySide6 application packaged with PyInstaller, with no CMake
  build at all — the bundled automation script would not run against this
  project. Its `references/qml-performance-anti-patterns.md` conceptual
  content is still valid and cited as reference material in
  `rf-qml-architecture`. **Reference-only, not installed as an active
  skill.**
- **`violet-hgy/agent-skills-qt-quick-qml`**, **`bigzhuodan/claude-skill-qt-design`**,
  **`AJpon/qt-python-ai-skills`** — all zero-star, single-contributor,
  either unlicensed or unclear-licensed repositories created within days to
  weeks of this research date. `bigzhuodan`'s explicitly targets
  "PySide6/Qt Widgets + QSS" — the wrong Qt UI paradigm entirely (QWidgets
  stylesheets, not Qt Quick/QML declarative bindings), which RocketForge
  does not use anywhere. **All three rejected** — no adoption signal, no
  clear license on two of three, and superseded in every case by the
  official Qt Company repository's quality and authority where their scope
  overlaps at all.
- `liueggy/qt5-skills` — surfaced in search, name alone (`qt5-skills`)
  disqualifies it per the explicit instruction against obsolete Qt5
  guidance; not opened.

## 7. Qt Quick 3D

Searched GitHub code search for `"Qt Quick 3D" filename:SKILL.md` and
`QtQuick3D agent skill`, plus a targeted code search for `Quick3D` scoped to
`repo:TheQtCompanyRnD/agent-skills`. Result: no dedicated Qt Quick 3D skill
found anywhere, including from the Qt Company itself — the only hits inside
their own repository are an explicit *exclusion* note in `qt-qml-profiler`
("Does NOT cover Qt Quick 3D") and incidental references in unrelated
skills (`qt-qml-test`). **Confirmed gap**, per the brief's own anticipated
outcome — see `rf-qtquick3d-viewport` in the custom-skills document.

## 8. Scientific visualization

Searched for scientific/data visualization skills. Found
**`aref-vc/tufte-claude-skill`** (299 stars, MIT license, pushed roughly
three months before this research date) — a thorough distillation of Edward
Tufte's three books into chart-selection rules, a kill-list, a keep-list,
and a 20-item pre-publish checklist. Read `SKILL.md` in full. Its two output
stacks are self-contained HTML/SVG and React+Recharts/D3 — neither renders
inside a QML application, and installing it active would let its own
trigger words ("chart," "visualize," "graph") compete with
`rf-scientific-visualization` and risk producing web scaffolding inside a
Python/QML repository. Its selection principles (no pie charts, no dual
axis, no 3D-on-2D, no rainbow scales on ordered data, direct labels over
legends, range frames, a single applied accent colour, tables for small n)
are platform-agnostic and were folded into `rf-scientific-visualization`'s
`SKILL.md` and its `RF_PLOT_TABLE_GRAMMAR.md` reference, cited by name.
**Reference-only, not installed.**

`NVIDIA/skills` (3244 stars) was checked because it surfaced in a related
search; its full skill listing is CUDA/DeepStream/cuOpt/DICOM/GPU-compute
tooling with zero UI, design, or visualization skills. **Not relevant,
rejected without further review.**

## 9. CAD/CAE UX

Searched for "CAD CAE UX skill," "model browser inspector," and "engineering
workbench" skill content. No mature end-to-end CAD-workbench design-guidance
skill was found. Two superficially matching hits were opened and rejected
as off-topic on inspection:

- `Cai-aa/CAD-Agent-Hub` — MCP servers/automation bridges for controlling
  CATIA (an actual CAD program), not UI/UX design guidance for building a
  CAD-*styled* application.
- `Cai-aa/CAE-Agent-Hub` — MCP servers and solver automation for
  Abaqus/ANSYS Fluent/ANSYS Mechanical/HFSS — real finite-element solver
  automation, not UI design guidance.

**Confirmed gap**, as anticipated — see `rf-engineering-workbench` in the
custom-skills document.

## 10. Visual QA / regression

Beyond `humbleteam/design-review` (installed, see §4), searched for
"visual regression" and "screenshot review skill." `LambdaTest/agent-skills`
surfaced — a commercial cross-browser/visual-regression testing platform's
skill, which assumes their cloud service and API credentials. RocketForge
already has bespoke, precisely-tailored offline capture/comparison tooling
built during the visual pilot and memory investigation
(`experiments/ui_visual_pilot/capture_matrix.py`, `visual_parity.py`,
`accessibility_audit.py`); a cloud dependency adds nothing for an offline
packaged desktop application and introduces a credential/network
dependency this project has no other use for. **Not installed.**
`Bbasche/design-review` — see §4.

## What was not attempted

Live browsing of `github.com/anthropics/skills` and the other repositories
through a rendered web page was not used — `gh api` and `git clone` against
the same repositories give the actual file contents directly and more
reliably than an HTML render, and are the preferred mechanism per this
session's own tool guidance for GitHub URLs.
