# Design Skill Foundation R1 — Candidate matrix

Every seriously-considered candidate, scored 1–5 on the requested
dimensions. A meaningless single average is not the point — read the notes
column for what the numbers actually mean for RocketForge; two candidates
with the same average can carry opposite risk profiles.

Legend: Rel = relevance to RocketForge, Qual = instruction quality, Spec =
specificity, Maint = maintenance/currentness, QtC = Qt/QML compatibility,
DeskC = desktop-app compatibility, SciC = scientific-app compatibility,
VisQ = visual-design quality, Lic = license clarity, Sec = security/supply-
chain confidence, Ovl = overlap risk (5 = low risk, i.e. good), SaaS = risk
of generating generic SaaS UI (5 = low risk, i.e. good), CAD = future
CAD-workbench usefulness, 3D = future Qt Quick 3D usefulness.

## Installed

| Candidate | Rel | Qual | Spec | Maint | QtC | DeskC | SciC | VisQ | Lic | Sec | Ovl | SaaS | CAD | 3D | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qt-qml` (TheQtCompanyRnD) | 5 | 5 | 5 | 5 | 5 | 5 | 4 | 3 | 5 | 5 | 4 | 3 | 3 | 2 | **INSTALL** |
| `qt-ui-design` (TheQtCompanyRnD) | 5 | 5 | 5 | 5 | 5 | 5 | 3 | 4 | 5 | 5 | 3 | 3 | 3 | 1 | **INSTALL** |
| `qt-qml-review` (TheQtCompanyRnD) | 4 | 5 | 5 | 5 | 5 | 5 | 3 | 2 | 5 | 5 | 4 | 2 | 2 | 1 | **INSTALL** |
| `design-review` (humbleteam) | 4 | 5 | 4 | 3 | 3 | 4 | 3 | 4 | 5 | 5 | 4 | 4 | 2 | 1 | **INSTALL** |

Notes:

- `qt-qml`/`qt-ui-design`/`qt-qml-review` score low on **Overlap risk**
  relative to a perfect 5 only because `qt-qml-review`'s six-domain
  analysis genuinely overlaps what a from-scratch `rf-qml-architecture`
  could have tried to cover — resolved by explicit division of labor (see
  the ownership document) rather than by rejecting either.
- `qt-ui-design` and `qt-qml-review` score **3D = 1** honestly: neither
  mentions Qt Quick 3D, `qt-qml-profiler` explicitly excludes it. This
  absence is exactly what justified `rf-qtquick3d-viewport`.
- `design-review`'s **Maintenance = 3** reflects genuinely low adoption (3
  stars) rather than staleness (pushed the day before this research) — a
  real but small risk, mitigated by the skill's content being self-
  contained markdown with no external dependency to go stale.

## Reference-only (not installed as an active skill)

| Candidate | Rel | Qual | Spec | Maint | QtC | DeskC | SciC | VisQ | Lic | Sec | Ovl | SaaS | CAD | 3D | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `frontend-design` (anthropics) | 3 | 5 | 4 | 5 | 1 | 2 | 2 | 5 | 5 | 5 | 3 | 2 | 1 | 1 | **REFERENCE ONLY** |
| `tufte-claude-skill` (aref-vc) | 3 | 5 | 5 | 4 | 1 | 2 | 4 | 5 | 5 | 5 | 3 | 4 | 1 | 1 | **REFERENCE ONLY** |
| `qt-qml-profiler` (TheQtCompanyRnD) | 2 | 4 | 4 | 5 | 5 | 2 | 3 | — | 5 | 4 | 4 | — | 2 | 1 | **REFERENCE ONLY** |
| `better-*` family (jakubkrehel, 7 skills) | 2 | 5 | 5 | 5 | 1 | 2 | 2 | 4 | 5 | 4 | 2 | 2 | 1 | 1 | **REFERENCE ONLY** |

Notes:

- `frontend-design` and `tufte-claude-skill` both score **QtC = 1** for the
  same reason: their entire output contract (rendered CSS/web pages,
  self-contained HTML/SVG or React) is not something a QML application can
  consume, and if triggered live they would produce artifacts in the wrong
  format for this repository. Their *conceptual* content (design-tell
  calibration; chart kill-list) is real and was folded into custom skills
  by citation, which is what earns the middling SaaS-risk and VisQ scores
  rather than a flat rejection.
- `qt-qml-profiler`'s low **DeskC** score is specific: its bundled
  automation assumes a CMake C++ build this Python/PySide6 project does not
  have. The skill's *documentation* is fine; its *script* would not run
  here.
- The `better-*` family scores **Ovl = 2** deliberately low: each skill's
  description ("polishes UI," "helps with accessibility") is broad enough
  to compete for triggering with `rf-engineering-workbench`,
  `rf-scientific-ui-contract`, and `design-review` simultaneously, while
  its actual content (exact CSS values, Tailwind mappings, ARIA specifics)
  cannot execute correctly in this codebase — a high-confidence,
  wrong-platform answer is worse than a low-confidence right one, which is
  why this family was not installed despite genuinely excellent writing
  quality (Qual = 5) and a design pattern (the ownership-boundary
  structure) explicitly imitated in every RocketForge custom skill.

## Rejected

| Candidate | Rel | Qual | Maint | Sec | Lic | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `dawitlabs/ui-skills` | 2 | 3 | 2 | 3 | 4 | SaaS/marketing-page framing (`landing`, `ui-init`, a "design-brief interview"); 4 months stale, 5 stars; nothing not already covered by an installed or reference candidate. |
| `violet-hgy/agent-skills-qt-quick-qml` | 2 | ? | 2 | 1 | 1 | 0 stars, no license, days old — not opened past metadata given the strictly superior official Qt Company alternative already installed. |
| `bigzhuodan/claude-skill-qt-design` | 1 | ? | 2 | 1 | 1 | Targets Qt Widgets + QSS, the wrong Qt UI paradigm for a QML application. 0 stars, no license. |
| `AJpon/qt-python-ai-skills` | 2 | ? | 2 | 2 | 3 | 0 stars, generic collection description, no unique content identified beyond the official Qt Company repository's coverage. |
| `liueggy/qt5-skills` | 1 | ? | 1 | ? | ? | Name alone identifies obsolete Qt5-era guidance; rejected on the explicit instruction against that, not opened. |
| `Cai-aa/CAD-Agent-Hub` | 1 | — | — | — | — | CATIA automation via MCP, not UI/UX guidance. Off-topic. |
| `Cai-aa/CAE-Agent-Hub` | 1 | — | — | — | — | Abaqus/ANSYS solver automation via MCP, not UI/UX guidance. Off-topic. |
| `NVIDIA/skills` | 1 | — | — | — | — | GPU-compute/CUDA/DeepStream tooling, zero UI/visualization content. Off-topic despite high star count (3244). |
| `LambdaTest/agent-skills` | 1 | — | — | — | — | Assumes their commercial cloud visual-regression service; RocketForge's offline packaged desktop app already has bespoke, more precisely-tailored capture tooling. |
| `Bbasche/design-review` | 3 | 4 | 2 | 4 | 5 | Genuinely reasonable, but narrower ("frontend UI" framing) and staler (5 months) than the installed `humbleteam/design-review`; passed over as redundant, not defective. |

"?" marks a dimension not scored because the repository was not opened past
metadata — the metadata alone (0 stars, unclear/no license, superseded by a
strictly better alternative already installed) was sufficient grounds to
stop, and opening an unlicensed, zero-adoption repository further to score
every dimension was not a good use of review effort once a clearly
authoritative alternative existed.
