# Design Skill Live Eval R1 — Files

## Modified (skill fixes only — no production files touched)

```
.claude/skills/rf-engineering-workbench/SKILL.md
    + pointer to the new accessibility-reflex rule
.claude/skills/rf-engineering-workbench/references/RF_WORKBENCH_GRAMMAR.md
    + "Restraint is not the only thing at stake" subsection

.claude/skills/rf-propulsion-visual-grammar/SKILL.md
    + "Verify each component individually, not the workspace as a whole"
      subsection under "Engine Design: no fictional components"
```

Both are additive edits to existing files; nothing was removed or weakened.
Full diff reasoning in `DESIGN_SKILL_LIVE_EVAL_R1_FAILURES.md`.

## Created — evaluation artifacts

`acceptance/design_skill_live_eval_r1/` — 96 files: 11 eval directories
(`prompt.md`, `control_response.md`, `routed_response.md`,
`candidate_A.md`/`candidate_B.md`, `scores.json`, `reviewer_notes.md` each;
`eval_06_visual_language/` and `eval_07_engine_3d/` additionally carry a
`rerun_after_fix/` subdirectory with the same structure), plus
`_condition_mapping.json`, `aggregate_scores.json`, `blocking_gates.json`,
`acceptance_manifest.md`, and `generalization_line_thermo/response.md`.
Full structure documented in `acceptance_manifest.md` itself.

## Created — documentation

```
docs/design/skills/live_eval_r1/
    DESIGN_SKILL_LIVE_EVAL_R1_CHECKPOINT.md
    DESIGN_SKILL_LIVE_EVAL_R1_METHOD.md
    DESIGN_SKILL_LIVE_EVAL_R1_RESULTS.md
    DESIGN_SKILL_LIVE_EVAL_R1_FAILURES.md
    DESIGN_SKILL_LIVE_EVAL_R1_RECOMMENDATIONS.md
    DESIGN_SKILL_LIVE_EVAL_R1_FILES.md      (this file)
    DESIGN_SKILL_LIVE_EVAL_R1_REPORT.md
```

## Confirmed untouched

`rocketforge/`, production `ui/`, `tests/`, `packaging/`, `main.py`,
`requirements*.txt`, every frozen manifest, and every file under
`docs/` outside the two `docs/design/skills/` trees (this run's own and
the prior Foundation R1 run's). Verified by `git status --short` at both
the opening and closing safety checks (identical: only `.claude/`,
`docs/design/skills/` untracked; `acceptance/` is gitignored and was
already so before this run) and by the base regression suite reporting
the identical `6931 passed, 154 skipped` at both checks.
