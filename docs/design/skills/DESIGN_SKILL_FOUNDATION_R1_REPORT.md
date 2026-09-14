# RocketForge Design Skill Foundation R1 — Report

Research, evaluation, selection, installation, and validation of the
project-local Agent Skills needed to eventually redesign RocketForge as a
CAD/CAE-style propulsion design workbench. **No production code, QML, or
physics was touched.** This is the tooling foundation only.

Companion documents: `DESIGN_SKILL_FOUNDATION_R1_RESEARCH.md` (what was
inspected), `_MATRIX.md` (scored candidates), `_OWNERSHIP.md` (the
hierarchy), `_CUSTOM_SKILLS.md` (each authored skill's purpose/ownership),
`_SECURITY.md`, `_LICENSES.md`, `_EVALS.md`, `_FILES.md`.

---

## Acceptance checklist

**Research**
- [x] `anthropics/skills` inspected (`frontend-design`, `skill-creator`
      read in full, license and template fetched).
- [x] `jakubkrehel/skills` inspected (7 of 11 skills' `SKILL.md` heads read
      directly).
- [x] `humbleteam/design-review` inspected in full.
- [x] `dawitlabs/ui-skills` inspected (README + skill listing).
- [x] Qt/QML/PySide search performed, high priority as instructed —
      `TheQtCompanyRnD/agent-skills` found and three skills read in full or
      near-full; four low-quality alternatives found and correctly passed
      over.
- [x] Qt Quick 3D search performed — confirmed gap, including inside the
      official Qt Company repository itself.
- [x] Scientific-visualization search performed —
      `aref-vc/tufte-claude-skill` found and read in full.
- [x] CAD/CAE UX skill gap investigated — confirmed gap; two superficially
      matching repositories opened and correctly identified as CAD/CAE
      *automation* tooling, not UI/UX design guidance.

**Selection**
- [x] Unnecessary skills rejected, with reasons recorded (matrix + research
      docs).
- [x] Overlapping skills resolved (ownership doc; no concern has two
      owners).
- [x] One clear design authority: `rf-engineering-workbench`.
- [x] Qt architecture owner explicit: `qt-qml`/`qt-qml-review` for general
      Qt6 correctness, `rf-qml-architecture` for RocketForge-specific rules
      — division stated in both directions.
- [x] Scientific semantics owner explicit: `rf-scientific-ui-contract`
      (numbers/state) and `rf-propulsion-visual-grammar` (schematics),
      with their boundary stated.
- [x] QA chain explicit: `rf-visual-qa` (RocketForge truthfulness) ->
      `design-review` (independent craft critique).

**Security**
- [x] Every installed skill inspected, including the one bundled script
      (`qt_qml_lint.py`, 1486 lines, read in full).
- [x] No suspicious behavior found in anything installed.

**License**
- [x] Every installed/copied skill accounted for (4 skills, all license
      files copied unmodified, BSD-3-Clause option documented and justified
      for the dual-licensed Qt Company skills).

**Custom**
- [x] Only justified custom skills created — each tied to a confirmed
      research gap (`rf-engineering-workbench`, `rf-qtquick3d-viewport`) or
      to RocketForge-specific evidence no general skill could contain
      (the other five).
- [x] Skills are narrow — each states explicit non-ownership.
- [x] Skills use progressive disclosure — `references/` for the deeper
      material, `SKILL.md` kept to the decision-relevant core.
- [x] No giant duplicate skill.

**Eval**
- [x] Dashboard tendency tested (§36, §37).
- [x] Soft-visual-language tendency tested (§42).
- [x] Scientific honesty tested (§38, §43).
- [x] QML lifecycle tested (§39).
- [x] Trade Study view-only semantics tested (§40).
- [x] Screenshot semantic mismatch tested (§41), with a real fixture file
      built.
- [x] 3D fictional-component tendency tested (§43).

Method note: these are structural verifications against the installed
skill text (quoted, located), not live multi-agent benchmark runs — see
`_EVALS.md`'s methodology section for why, and for the concrete
`evals.json`/fixture artifacts left in place to make a real
`skill-creator`-driven benchmark cheap to run next.

**Project**
- [x] Production physics unchanged (nothing under `rocketforge/` touched).
- [x] Production QML unchanged (nothing under `ui/` touched).
- [x] Product behavior unchanged — base regression suite re-run after
      installation, identical `6931 passed, 154 skipped` result as
      immediately before this run began.

---

## Repositories researched

`anthropics/skills`, `jakubkrehel/skills`, `humbleteam/design-review`,
`dawitlabs/ui-skills`, `TheQtCompanyRnD/agent-skills`,
`violet-hgy/agent-skills-qt-quick-qml`, `bigzhuodan/claude-skill-qt-design`,
`AJpon/qt-python-ai-skills`, `liueggy/qt5-skills` (name-only, not opened),
`aref-vc/tufte-claude-skill`, `NVIDIA/skills`, `Cai-aa/CAD-Agent-Hub`,
`Cai-aa/CAE-Agent-Hub`, `LambdaTest/agent-skills` (metadata only),
`Bbasche/design-review`. Full detail in `_RESEARCH.md`.

## Qt / QML skill findings

`TheQtCompanyRnD/agent-skills` is the official Qt Company repository
("Official Qt AI engineering skills for Claude Code"), 416 stars, Qt6-only
(`metadata.qt-version: "6.x"` on every skill checked, no Qt5 guidance
found), dual-licensed with a usable BSD-3-Clause option. Three of its
twelve skills installed: `qt-qml` (coding rules), `qt-ui-design`
(design/audit checklist spanning desktop/web/embedded), `qt-qml-review`
(structured six-domain review with a clean, stdlib-only, read-only bundled
linter). A fourth, `qt-qml-profiler`, was read and kept reference-only —
its automation assumes a CMake C++ build RocketForge does not have (it is
Python/PySide6, packaged with PyInstaller), though its conceptual
performance-anti-patterns content was cited in `rf-qml-architecture`. Every
other Qt-specific candidate found was zero-star, unlicensed or unclearly
licensed, targeted the wrong Qt UI paradigm (Qt Widgets/QSS instead of Qt
Quick/QML), or named itself Qt5-specific — all correctly rejected in favor
of the official, current, properly-licensed alternative.

## Qt Quick 3D skill findings

No dedicated Qt Quick 3D skill was found anywhere, including inside the
official Qt Company repository, which explicitly excludes Qt Quick 3D from
its own profiler skill's scope and has no dedicated skill for it. This is a
confirmed gap, addressed by the custom `rf-qtquick3d-viewport` skill, whose
own `SKILL.md` documents this provenance and recommends re-checking before
a real 3D project begins.

## Candidate matrix

Full scored table (14 dimensions x every seriously-considered candidate)
in `_MATRIX.md`. Summary: 4 installed, 4 kept reference-only (2 for
platform mismatch despite strong content, 1 for build-system mismatch, 1
family for platform mismatch despite an excellent structural pattern
worth imitating), 10 rejected (off-topic, unlicensed/unproven, stale, or
redundant with an installed/reference alternative).

## Rejected skills

`dawitlabs/ui-skills` (SaaS/marketing framing, stale, redundant),
`violet-hgy/agent-skills-qt-quick-qml` / `bigzhuodan/claude-skill-qt-design`
/ `AJpon/qt-python-ai-skills` (zero-star, unclear license, superseded by
the official Qt Company repository), `liueggy/qt5-skills` (obsolete Qt5
guidance, name alone disqualifies), `Cai-aa/CAD-Agent-Hub` /
`Cai-aa/CAE-Agent-Hub` (CAD/CAE software automation, not UI guidance —
off-topic), `NVIDIA/skills` (GPU-compute tooling, zero UI content —
off-topic), `LambdaTest/agent-skills` (commercial cloud dependency
inappropriate for an offline packaged desktop app, and redundant with
RocketForge's own existing capture tooling), `Bbasche/design-review`
(reasonable but redundant with the installed, stronger `humbleteam`
version). Full reasoning in `_MATRIX.md` and `_LICENSES.md`.

## Installed third-party skills

| Repository | Skill | Local path | Owner role | License |
| --- | --- | --- | --- | --- |
| `TheQtCompanyRnD/agent-skills` | `qt-qml` | `.claude/skills/qt-qml/` | General Qt6 QML coding authority | BSD-3-Clause (of dual license) |
| `TheQtCompanyRnD/agent-skills` | `qt-ui-design` | `.claude/skills/qt-ui-design/` | General Qt6 UI/UX design + audit authority | BSD-3-Clause (of dual license) |
| `TheQtCompanyRnD/agent-skills` | `qt-qml-review` | `.claude/skills/qt-qml-review/` | Mechanical, six-domain QML review layer | BSD-3-Clause (of dual license) |
| `humbleteam/design-review` | `design-review` | `.claude/skills/design-review/` | Independent, cited craft/hierarchy critique — final QA layer | MIT |

## RocketForge custom skills

Full purpose/trigger/owns/does-not-own for each in `_CUSTOM_SKILLS.md`.
Names: `rf-engineering-workbench` (design authority/composition),
`rf-propulsion-visual-grammar` (schematic honesty per domain),
`rf-scientific-ui-contract` (number/state honesty),
`rf-qml-architecture` (RocketForge-specific QML/Python architecture, built
directly from the memory investigation's findings),
`rf-scientific-visualization` (charts/tables),
`rf-visual-qa` (RocketForge-specific screenshot truthfulness),
`rf-qtquick3d-viewport` (conditional — evaluate-first 3D viewport rules,
written from scratch since no comparable skill exists anywhere).

## Ownership hierarchy

```
rf-engineering-workbench (design lead)
    |-- rf-propulsion-visual-grammar (schematic content)
    |-- rf-scientific-ui-contract (number/state content)
    |-- rf-scientific-visualization (chart/table content)
    |-- rf-qml-architecture -> defers to qt-qml / qt-ui-design
    |       `-- qt-qml-review (mechanical review layer)
    `-- rf-visual-qa -> design-review (independent final critique)

rf-qtquick3d-viewport: conditional, defers to rf-propulsion-visual-grammar
    and rf-qml-architecture rather than restating either
```

Full detail, including the resolution rule for a request spanning multiple
owners, in `_OWNERSHIP.md`.

## Security review

Every installed skill inspected file-by-file; the one bundled script
(`qt-qml-review`'s `qt_qml_lint.py`, 1486 lines) read in full and confirmed
stdlib-only, read-only, no network/subprocess/eval calls. No skill
installs software, calls out to a network, modifies global configuration,
or writes outside this repository. Full detail, including notes on
candidates that were rejected before a code-level audit was warranted, in
`_SECURITY.md`.

## License review

Four skills copied, all licenses copied unmodified alongside them
(BSD-3-Clause for the three Qt Company skills, chosen from their dual
license since RocketForge holds no commercial Qt license; MIT for
`design-review`). Every reference-only citation in a custom skill names its
source by name in prose rather than reproducing text verbatim. Full detail
in `_LICENSES.md`.

## Evaluation results

All eight adversarial prompts from the program (dashboard tendency x2,
scientific honesty x2, QML lifecycle, Trade Study view-only semantics,
screenshot semantic mismatch, 3D fictional components) map to specific,
quoted, located language in an installed skill — summarized in a table in
`_EVALS.md`. A concrete stale-header-mismatch fixture
(`rf-visual-qa/evals/stale_header_fixture.json`) and `evals.json` files for
four flagship skills were built as artifacts for a future live benchmark
run, which is the recommended next step before this skill set is relied on
for large, unsupervised redesign work.

## Production impact

**NONE.** `git status --short` shows only the new `.claude/skills/` and
`docs/design/skills/` trees; nothing under `rocketforge/`, `ui/`,
`tests/`, or `packaging/` was created or modified. The base regression
suite was re-run after installation and reported the identical
`6931 passed, 154 skipped` already on record.

## Recommended skill routing for CAD/CAE WORKBENCH R1

For the eventual redesign program, in the order a workspace redesign
naturally proceeds:

1. `rf-visual-qa` — capture and actually look at the current state first
   (audit before design, per the accepted pilot's own process).
2. `rf-engineering-workbench` — composition/shell decisions.
3. `rf-propulsion-visual-grammar` — the workspace's schematic content.
4. `rf-scientific-visualization` — any chart/table in the same workspace.
5. `rf-scientific-ui-contract` — check every displayed number/state as the
   design solidifies, not only at the end.
6. `rf-qml-architecture` + `qt-qml` — implementation.
7. `qt-qml-review` — mechanical review pass.
8. `rf-visual-qa` again — capture the finished state, inspect it.
9. `design-review` — independent craft critique as the final layer.
10. `rf-qtquick3d-viewport` — only if a 3D viewport is genuinely on the
    table for that workspace (Engine Design being the most plausible
    candidate today).

One workspace at a time, per `rf-visual-qa`'s own discipline — not a batch
redesign reviewed once at the end.

## Missing capabilities

- No live multi-agent benchmark has yet been run against any custom
  skill — the structural verification in `_EVALS.md` is real but is not a
  substitute for the quantitative loop `skill-creator` itself recommends;
  the `evals.json` scaffolding left behind exists to make that cheap to do
  next.
- `README.md` at the repository root describes an earlier, pre-scientific
  phase of the application and is stale relative to the actual frozen
  propulsion/fluids/line stack — noted, not fixed, since correcting product
  documentation is outside a tooling-foundation run's scope.
- No skill in this set yet has direct, hands-on knowledge of exactly which
  registries `TradeStudyPage`/`StudySetup` currently expose for axis
  selection — `rf-scientific-visualization` states the rule (verify before
  assuming) rather than the current answer, since that answer will drift
  as the Trade Study module evolves and hard-coding it into a skill would
  go stale.

## Readiness

**Is RocketForge now equipped with a coherent project-local skill system
for a CAD/CAE-style propulsion workbench redesign?**

**YES**, with one qualification: this foundation is ready to *start* the
redesign responsibly — every ownership boundary is explicit, every
adversarial failure mode named in the program maps to specific installed-
skill text, and zero production risk was taken to build it. It has not yet
been exercised through a live multi-agent benchmark against real, varied
prompts at the scale `skill-creator`'s own process recommends before fully
trusting a skill set on large unsupervised work — that is the natural next
step, not a blocker to beginning the redesign under normal supervision.
