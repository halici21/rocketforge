# Design Skill Live Eval R1 — Recommendations

## For CAD/CAE Workbench R1

1. **Route as documented in `DESIGN_SKILL_LIVE_EVAL_R1_METHOD.md`'s table**,
   with one addition confirmed by this run: for any prompt that touches
   typography, colour, or chrome (not only ones that say "accessible"),
   pull in `qt-ui-design` alongside `rf-engineering-workbench` rather than
   `rf-engineering-workbench` alone — the fixed skill now names this
   itself, but a human routing the work should not rely on the skill
   remembering it silently forever; treat it as a standing pairing.

2. **Treat Engine Design 3D/CAD work as the highest-scrutiny task in the
   whole redesign.** It is the only case in this run where a routed,
   skill-guided response still blocking-failed on first pass. The failure
   was subtle (a component's *name* appearing in the codebase mistaken for
   its *implementation* existing) and survived a genuine, good-faith
   reading of the source. For this specific workspace: require a second,
   independent pass that lists every proposed "real" component against an
   explicit implementing-module citation before any visual design work
   proceeds, not just a general instruction to "check the code first."

3. **Keep the CONTROL-vs-ROUTED comparison method** for any future skill
   addition or edit, not only for this qualification run. It is cheap
   (each condition is one bounded subagent call) and it is the only method
   in this project that has actually caught a real skill deficiency rather
   than merely confirming intended rules exist in text.

4. **Do not treat a single reviewer's score as final on a blocking
   dimension.** The eval_08 result (both PASS, control edges ahead on
   richness) and the eval_10 result (a genuine tie) show reviewers can and
   do find close calls; where the reviewer's verdict is close, read the
   underlying candidate text yourself before trusting the aggregate number,
   the way this run's own adjudication step did for eval_07.

5. **`rf-visual-qa`'s stale-header fixture caught its intended defect in
   both conditions**, meaning even a naive reviewer, told to "review this
   state for release," found the specific mismatch when the fixture stated
   it explicitly. That is useful information but a weaker signal than
   originally hoped: the fixture proves the *pattern* is catchable, not
   that the *routed skill specifically* is what catches it in a less
   explicit, real-world screenshot review. A stronger future test would
   give the reviewer only a rendered screenshot (or a full state dump
   without narrating the mismatch in the prompt) and see whether the
   mismatch is still found unprompted.

## Skill maintenance

- Re-run this comparison methodology any time a `rf-*` skill is edited for
  reasons other than a live-eval fix (e.g. as part of ordinary CAD/CAE
  Workbench R1 work) — a skill that changes without a live check regresses
  silently, exactly as `rf-engineering-workbench` and
  `rf-propulsion-visual-grammar` were both found to have a real gap despite
  passing every structural check in Foundation R1.
- Keep the `evals/evals.json` files current: add the two fixed-and-verified
  cases from this run (technical-visual-language accessibility check;
  Engine Design component-verification rule) as permanent regression evals
  for their respective skills, not just a one-time check.

## What this run does not settle

- Whether the routed stack holds up on a *much longer, more open-ended*
  redesign task (a full workspace, not a single decision) — every eval
  here was bounded to a single prompt and a single decision. CAD/CAE
  Workbench R1's actual scope is larger than anything tested here.
- Whether two RocketForge skills can give *conflicting* guidance on a real
  task that spans both — this run routed each eval through the skills the
  ownership hierarchy assigns and never tested a genuine ownership
  collision in anger.
- Packaged/runtime behavior of anything proposed — nothing here was
  implemented, by design.
