# Design Skill Foundation R1 — Files

Every file this run created, in `.claude/skills/` and `docs/design/skills/`.
Nothing under `rocketforge/`, production `ui/`, `packaging/`, or any test
file was created or modified — confirmed by `git status --short` showing
only `.claude/` (untracked, new) at the time of writing this document, and
this `docs/design/skills/` tree.

## `.claude/skills/` — 34 files across 11 skills

### Installed third-party (copied, licensed, unmodified)

```
.claude/skills/qt-qml/
    SKILL.md  README.md  LICENSE.txt  platforms/windsurf.md
.claude/skills/qt-ui-design/
    SKILL.md  README.md  LICENSE.txt
.claude/skills/qt-qml-review/
    SKILL.md  README.md  LICENSE.txt  platforms/windsurf.md
    references/qt-qml-review-checklist.md
    references/lint-scripts/qt_qml_lint.py
.claude/skills/design-review/
    SKILL.md  README.md  CHANGELOG.md  LICENSE
    references/review-rubric.md
```

### Custom RocketForge skills (authored this run)

```
.claude/skills/rf-engineering-workbench/
    SKILL.md
    references/RF_WORKBENCH_GRAMMAR.md
    evals/evals.json

.claude/skills/rf-propulsion-visual-grammar/
    SKILL.md
    evals/evals.json

.claude/skills/rf-scientific-ui-contract/
    SKILL.md

.claude/skills/rf-qml-architecture/
    SKILL.md
    references/RF_QML_LIFECYCLE_RULES.md
    evals/evals.json

.claude/skills/rf-scientific-visualization/
    SKILL.md
    references/RF_PLOT_TABLE_GRAMMAR.md

.claude/skills/rf-visual-qa/
    SKILL.md
    references/RF_SCREENSHOT_MATRIX.md
    evals/evals.json
    evals/stale_header_fixture.json

.claude/skills/rf-qtquick3d-viewport/
    SKILL.md
```

`rf-propulsion-visual-grammar` and `rf-scientific-ui-contract` intentionally
have no `references/` subdirectory — their full content fits in a
right-sized `SKILL.md` (138 and comparable line counts respectively), and a
reference doc that would only restate the same material was judged not
worth the indirection (per `skill-creator`'s own guidance to keep a skill
lean rather than pad it toward a template shape). `rf-qtquick3d-viewport`
likewise has no `references/` — it is itself already the from-scratch
"reference" document, since no external material exists to summarize
elsewhere.

## `docs/design/skills/` — this program's own documentation

```
docs/design/skills/
    DESIGN_SKILL_FOUNDATION_R1_RESEARCH.md
    DESIGN_SKILL_FOUNDATION_R1_MATRIX.md
    DESIGN_SKILL_FOUNDATION_R1_OWNERSHIP.md
    DESIGN_SKILL_FOUNDATION_R1_CUSTOM_SKILLS.md
    DESIGN_SKILL_FOUNDATION_R1_SECURITY.md
    DESIGN_SKILL_FOUNDATION_R1_LICENSES.md
    DESIGN_SKILL_FOUNDATION_R1_EVALS.md
    DESIGN_SKILL_FOUNDATION_R1_FILES.md   (this file)
    DESIGN_SKILL_FOUNDATION_R1_REPORT.md
```

## Nothing else was created or modified

No file under `rocketforge/`, `ui/`, `tests/`, `packaging/`, `main.py`, or
any existing `docs/` file (outside the new `docs/design/skills/` directory)
was touched. `git status --short` immediately before this document was
written showed only the new `.claude/` tree as untracked content — no
modification markers against any tracked file. The base regression suite
(`.venv/Scripts/python.exe -m pytest -q`) was re-run after installation and
reported the identical `6931 passed, 154 skipped` result already on record
from the end of the prior program, which is exactly the expected outcome
of a run that touched zero production files.
