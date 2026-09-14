# Design Skill Live Eval R1 — Method

## The gap this run closes

Design Skill Foundation R1's own evals document was explicit about its
limitation: it verified that the intended rules exist in each skill's text
and are worded to catch the adversarial prompts, but it did not run the
skills live. This run closes that gap.

## Live invocation availability

Confirmed at the start of this run: all 11 project-local skills
(`design-review`, `qt-qml`, `qt-qml-review`, `qt-ui-design`,
`rf-engineering-workbench`, `rf-propulsion-visual-grammar`,
`rf-qml-architecture`, `rf-qtquick3d-viewport`, `rf-scientific-ui-contract`,
`rf-scientific-visualization`, `rf-visual-qa`) appear as invocable via the
Skill tool in this session, and subagents spawned for this run were able to
call the Skill tool themselves. Live invocation is available — this run
proceeds as a genuine qualification, not `BLOCKED`.

## Two conditions, genuinely independent

**CONTROL** — a fresh subagent (no access to this conversation's history,
so no memory of having authored the skills) given the task prompt and
explicitly forbidden from reading `.claude/skills/` or calling the Skill
tool. It may read the real repository for grounding (as any capable
designer would look at the code before proposing a change), but answers
from general design/engineering judgment only.

**ROUTED** — a fresh subagent given the same task prompt, plus an explicit
instruction to call the Skill tool for the specific skills the ownership
hierarchy (`DESIGN_SKILL_FOUNDATION_R1_OWNERSHIP.md`) assigns to that task,
in order, before answering, and to list which skills it actually invoked.
It is explicitly told not to invoke `qt-qml-review` or `design-review` —
those are review-layer skills in the hierarchy, not authorship skills, and
activating every reviewer during authorship would violate the ownership
model this run is meant to test.

Both conditions are reasoning-only: explicitly forbidden from writing,
editing, or implementing any file other than their own single output
markdown file, which they write themselves via the Write tool. Neither
condition sees the other's output.

## Why subagents rather than self-authoring both sides

The orchestrating session (this one) wrote every RocketForge skill in the
prior run and therefore cannot produce a naive, uncontaminated "control"
response — it already knows the entire ownership hierarchy and every
anti-pattern by name. A fresh subagent with no memory of that work is the
only way to get an honest baseline. This is also why the reviewer (below)
is a third, separate subagent rather than the orchestrator's own read of
the two outputs.

## Routing per eval

| Eval | Skills invoked (routed condition) |
| --- | --- |
| 01 Home | `rf-engineering-workbench` -> `qt-ui-design` |
| 02 Fluid Properties | `rf-engineering-workbench` -> `rf-propulsion-visual-grammar` -> `rf-scientific-visualization` |
| 03 Trade Study axes | `rf-scientific-visualization` -> `rf-scientific-ui-contract` |
| 04 Nozzle realism | `rf-propulsion-visual-grammar` |
| 05 QML animation | `rf-qml-architecture` -> `qt-qml` |
| 06 Technical visual language | `rf-engineering-workbench` |
| 07 Engine Design 3D | `rf-propulsion-visual-grammar` -> `rf-qtquick3d-viewport` |
| 08 Stale snapshot QA | `rf-visual-qa` -> `rf-scientific-ui-contract` |
| 09 Chart/table proportion | `rf-scientific-visualization` -> `rf-engineering-workbench` |
| 10 Responsive 1366x768 | `rf-engineering-workbench` |
| 11 Qt Quick 3D decision | `rf-qtquick3d-viewport` |

## Independent review

Per the program's own instruction to use "the final independent reviewer
selected by the foundation," that role is `design-review`. `design-review`
is built to critique or compare rendered screenshots/URLs/HTML — this run
produces no rendered UI (the hard rule forbids implementation), so its
screenshot-comparison mechanism does not apply directly to two prose design
proposals. Rather than force a bad fit, the independent-review role in this
run is filled by a dedicated reviewer subagent, given both outputs
anonymized as **Candidate A / Candidate B** (label order alternated per
eval to reduce position bias, and the reviewer is not told which is
control and which is routed), the eval's specific pass/fail criteria as
defined in the mega-prompt, and the 15-dimension scoring rubric restricted
to the dimensions relevant to that eval. The reviewer scores both, states a
winner, and is explicitly told not to rewrite either answer. This is
documented here as an honest adaptation, not presented as literally running
`design-review`'s own screenshot rubric.

## Scoring dimensions used

All 15 from the program, scored 0-5 where relevant to a given eval (not
every dimension applies to every eval — e.g. "chart/table task fit" is not
scored for the nozzle-realism eval):

1. Engineering object centrality
2. CAD/CAE workbench character
3. Resistance to generic dashboard/card-grid design
4. Information hierarchy
5. Typography softness/restraint
6. Chart/table task fit
7. Scientific honesty
8. RocketForge semantic correctness
9. QML lifecycle correctness
10. Visual-only interaction solve discipline
11. Responsive desktop thinking
12. Accessibility thinking
13. Fictional-capability avoidance
14. Progressive disclosure
15. Visual QA sensitivity

## Blocking dimensions and pre-registered thresholds

Registered here, before any eval output was scored:

- Blocking dimensions (must score >= 4/5 for the ROUTED condition on every
  eval where the dimension applies): scientific honesty, QML lifecycle
  correctness, visual-only interaction solve discipline,
  fictional-capability avoidance.
- Blocking evals (both must PASS outright, not just score well): eval 03
  (Trade Study view-only semantics), eval 04 (nozzle scientific honesty),
  eval 05 (QML lifecycle), eval 07 (fictional 3D capability), eval 08
  (stale solved-state QA).
- Target mean improvement of ROUTED over CONTROL across the full scoring
  matrix: >= 0.75 points.

If any of these targets prove operationally unsuitable once real scores are
in (for example, a dimension that does not discriminate because both
conditions score identically on it for a structural reason), that will be
stated explicitly in the results document before, not after, being used to
explain a shortfall — per the program's own instruction not to move the
target after seeing results.

## Adjudication rule

Scientific-contract findings outrank aesthetic preference on a science
question. Qt/QML architecture findings outrank visual preference on a
lifecycle question. Where the reviewer subagent's judgement and this
orchestrating session's own domain check disagree (for example, the
reviewer might not know RocketForge's specific Pareto-membership rule well
enough to catch a subtle violation a design-literate but domain-naive
reader would miss), the domain-grounded finding wins, and the disagreement
is recorded rather than silently overridden.
