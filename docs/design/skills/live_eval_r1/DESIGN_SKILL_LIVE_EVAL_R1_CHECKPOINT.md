# Design Skill Live Eval R1 — Checkpoint

| Field | Value |
| --- | --- |
| CURRENT_EVAL | — complete |
| CURRENT_VARIANT | — complete |
| LAST_COMPLETED_STEP | Closing regression run and verified identical to opening; all documentation written |
| NEXT_STEP | none — run complete, verdict delivered |
| NEXT_ACTION | none |
| CURRENT_SCORE | routed 4.77/5, control 3.34/5, improvement +1.43 (target +0.75) |
| CURRENT_FAILURES | two found, both fixed and verified — see `DESIGN_SKILL_LIVE_EVAL_R1_FAILURES.md` |
| PRODUCTION_DIFF_STATE | clean — `git status` identical at open and close; base regression identical (6931 passed, 154 skipped) at open and close |

## Live invocation availability

Confirmed available and used throughout: all 11 project-local skills were
invoked live via the Skill tool by real subagents, not read and
paraphrased. This run was **not** `BLOCKED`.

## Summary of what happened, in order

1. Opening safety check: git status clean, base regression 6931/154 —
   matched the expected baseline from Foundation R1 exactly.
2. 11 eval cases x 2 conditions (control, routed) = 22 generation
   subagents, spawned in parallel, each invoking the ownership-hierarchy-
   assigned skills live via the Skill tool for the routed condition.
3. 11 independent, blind reviewer subagents scored each pair (labeled
   Candidate A/B, order alternated, condition identity withheld).
4. Two genuine skill deficiencies found: `rf-engineering-workbench` had no
   accessibility reflex (eval 06); `rf-propulsion-visual-grammar` accepted
   a component's mere name as evidence of implementation (eval 07, a
   blocking eval — this one mattered for the pass/fail decision).
5. Both fixed under `.claude/skills/` only, as general rules (not
   hard-coded to the exact prompt), per the program's explicit
   anti-overfit instruction.
6. Eval 06 rerun (same prompt) + a generalization test on an unseen prompt
   (Thermochemistry warning state) — fix confirmed working and confirmed
   to generalize.
7. Eval 07 rerun (same prompt, independently re-derived ground truth from
   the source rather than trusting either candidate) + eval 04 adjacent
   regression check (same skill, different eval, previously passing) —
   fix confirmed working, no regression.
8. Aggregate scoring computed from the post-fix state.
9. Closing safety check: git status and base regression both identical to
   opening.
10. All eight required documents written; final verdict delivered.

## Final numbers

See `DESIGN_SKILL_LIVE_EVAL_R1_RESULTS.md` and
`acceptance/design_skill_live_eval_r1/aggregate_scores.json` /
`blocking_gates.json` for full detail. Headline: routed beats control on
9/11 evals, ties on 1, loses narrowly on 1 (both passed the blocking gate
in that case); all 5 blocking evals PASS in the final (post-fix) routed
condition; every blocking-dimension score is 5/5; mean improvement +1.43
against a pre-registered target of +0.75.
