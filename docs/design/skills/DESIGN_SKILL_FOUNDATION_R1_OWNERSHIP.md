# Design Skill Foundation R1 — Ownership

One question per concern, one skill that answers it. No concern in this
list has two owners; where two skills touch the same screen, one defines
the rule and the other enforces or extends it, and that relationship is
stated explicitly below.

## Ownership matrix

| Concern | Owner | Notes |
| --- | --- | --- |
| Application shell / page / workspace composition | `rf-engineering-workbench` | The object-first grammar, card/chrome discipline, progressive disclosure, responsive layout behaviour. |
| CAD/CAE information architecture (model browser / viewport / inspector / dock) | `rf-engineering-workbench` | Direction, not a mandate — extends the existing Engine Design shell pattern. |
| Layout mechanics (Layout.*, anchors, sizing) | `qt-qml` | General Qt6 rule; `rf-engineering-workbench` never restates these. |
| Typography (values, modular scale) | `qt-ui-design` | Token *values* and scale construction. `rf-engineering-workbench` governs how the scale is *assigned to roles* on a RocketForge screen. |
| Color mechanics (contrast measurement, token roles) | `qt-ui-design` (WCAG floor) + `design-review` (independent citation) | RocketForge's actual palette lives in `ui/theme/Theme.qml`; neither skill edits it, both check against it. |
| Scientific color semantics (what a hue may/must not carry) | `rf-scientific-ui-contract` | Colour-never-the-only-cue as it applies to a *result state*, not general UI color theory. |
| Controls (which Qt Quick Control to reach for) | `qt-qml` | General Qt6 rule. |
| Motion / animation | `qt-ui-design` (general duration/easing budgets) + `rf-qml-architecture` (this app's Canvas/animation discipline) | The general budget is Qt-wide; the specific "no idle repaint, no decorative motion beyond the one accepted `Behavior`" rule is RocketForge-specific and lives in `rf-qml-architecture`. |
| Accessibility (keyboard, focus, ARIA-equivalent) | `qt-ui-design` (design-time rules) + `design-review` (independent audit citing WCAG) | Neither owns RocketForge's specific colour-only-state rule — that is `rf-scientific-ui-contract`. |
| Qt/QML architecture — general correctness | `qt-qml` (coding) + `qt-qml-review` (structured six-domain review) | Binding loops, Loader lifecycle, ListView/delegate rules, singleton mechanics, import hygiene. |
| Qt/QML architecture — RocketForge-specific | `rf-qml-architecture` | No-physics-in-QML boundary, stable row-model publication pattern, this app's singleton/controller shape, this app's memory-measurement protocol. Never restates `qt-qml`'s general rules. |
| Qt Quick 3D | `rf-qtquick3d-viewport` | No comparable external skill exists (confirmed by research); this skill also explicitly defers 2D-schematic-honesty rules to `rf-propulsion-visual-grammar` and lifecycle rules to `rf-qml-architecture` rather than restating them for the 3D case. |
| Plots / tables (chart selection, data-ink, proportion) | `rf-scientific-visualization` | Owns the `RFPlotSurface`/`RFLineChart`/`RFEngineeringTable` usage vocabulary and the task-driven proportion rule. |
| Scientific truthfulness of a *schematic drawing* | `rf-propulsion-visual-grammar` | What geometry a workspace's centerpiece may claim, per-domain object definitions, the schematic-vs-solved labeling rule. |
| Scientific truthfulness of a *number, label, or state* | `rf-scientific-ui-contract` | Stale/superseded/refused/unavailable/warning semantics, commonly-mislabeled quantities, the header-vs-drawing failure pattern. |
| Screenshot QA (did it actually render right) | `rf-visual-qa` | The canonical per-workspace state matrix, the discipline that captures are inspected not inferred, the stale-vs-solved fixture. |
| Independent craft/hierarchy critique | `design-review` | General UX heuristic critique with citations, used as the second-opinion layer after `rf-visual-qa`'s RocketForge-specific checks pass. |

## The single-authority hierarchy

```
                    rf-engineering-workbench
                    (composition / shell / chrome — the design lead)
                              |
        +---------------------+---------------------+
        |                     |                      |
rf-propulsion-       rf-scientific-         rf-scientific-
visual-grammar       ui-contract            visualization
(what a schematic    (what a number/state   (chart & table
may draw)            may say)               grammar)
        |                     |                      |
        +---------------------+---------------------+
                              |
                    rf-qml-architecture
              (RocketForge-specific QML/Python rules)
                              |
                    qt-qml / qt-ui-design
              (general Qt6 authority, deferred to,
               never restated)
                              |
                    qt-qml-review
              (mechanical six-domain lint/review layer)
                              |
                    rf-visual-qa
        (RocketForge-specific screenshot truthfulness)
                              |
                    design-review
        (independent, general craft/hierarchy critique —
         final layer, no implementation authority)
```

`rf-qtquick3d-viewport` sits beside `rf-propulsion-visual-grammar` and
`rf-qml-architecture` rather than in the main chain — it only activates when
a 3D viewport is genuinely under discussion, and when active it explicitly
defers to both of them rather than restating their rules for the 3D case.

**There is one design lead** (`rf-engineering-workbench`), not three. It
does not itself decide scientific honesty, QML mechanics, or chart
selection — it decides where things go and how much chrome surrounds them,
and routes to the specialist skill for anything else. This mirrors the
structural pattern found in `jakubkrehel/skills`'s `better-*` family
(reference-only in this project, but its ownership-boundary architecture
was worth imitating directly) and is stated in every custom skill's own
"Ownership" section so the boundary is enforced by the skill text itself,
not only by this document.

## Resolving a request that spans two owners

When a task genuinely needs more than one skill's territory (a full
workspace redesign needs `rf-engineering-workbench` for composition,
`rf-propulsion-visual-grammar` for the schematic, `rf-scientific-ui-contract`
for the numbers, and `rf-qml-architecture` for the implementation), say so
explicitly and work through each skill's section rather than letting one
skill's guidance silently stand in for another's. This is why every custom
skill's "Ownership" section states both what it owns and what it explicitly
does not — a skill that stays silent about its boundary invites exactly the
scope creep this hierarchy exists to prevent.
