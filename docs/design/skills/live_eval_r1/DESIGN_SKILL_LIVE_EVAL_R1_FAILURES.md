# Design Skill Live Eval R1 — Failures found, and what was done about them

Two genuine skill deficiencies were found by live evaluation. Both were
fixed under `.claude/skills/` only (no production files touched), both
fixes were general rules rather than hard-coded answers to the exact eval
prompt (per the program's explicit anti-overfit instruction), and both
fixes were verified by rerunning the failed eval plus at least one adjacent
or unseen prompt.

---

## Failure 1 — `rf-engineering-workbench` had no accessibility reflex

**Eval:** 06, technical visual language ("Make RocketForge look much more
technical and aerospace-like.")

**Before:** ROUTED (invoking `rf-engineering-workbench` alone) scored 5/5
on information hierarchy and typography restraint, and **1/5** on
accessibility thinking — it never mentioned contrast, WCAG, or legibility
anywhere. The naive CONTROL condition, with no RocketForge skill at all,
scored only 3/2 on hierarchy/typography but **4/5** on accessibility — it
thought to flag a contrast risk unprompted, something the routed answer,
despite being the more disciplined design overall, did not.

**Root cause:** `rf-engineering-workbench` owns typography/colour/chrome
*restraint*, and the ownership hierarchy correctly assigns contrast/WCAG
mechanics to `qt-ui-design` and `design-review` — but nothing in
`rf-engineering-workbench`'s own text prompted a hand-off to them. A
request that never uses the word "accessibility" (this one didn't) gave
the design-lead skill no trigger to remember that its own territory
(typography, colour, contrast) is exactly where accessibility problems get
introduced.

**Fix (general rule, not the specific prompt):** Added a "Restraint is not
the only thing at stake" subsection to `rf-engineering-workbench`'s
`RF_WORKBENCH_GRAMMAR.md`, plus a short pointer in the main `SKILL.md`:
whenever a change in this skill's territory touches colour, contrast, or
type size, name the need for an accessibility check and route to
`qt-ui-design`/`design-review` before calling the composition finished —
mirroring the existing pattern of routing scientific-content questions to
`rf-scientific-ui-contract`. The fix does not mention eval 6, "technical,"
or "aerospace" anywhere — it is stated as a standing rule triggered by
*any* typography/colour/contrast change, not this specific prompt.

**Verification:**
- Eval 06 rerun (same prompt, fixed skill): routed jumped from 1/5 to
  **5/5** on accessibility thinking, while *keeping* its 5/5 on hierarchy
  and typography restraint — now sweeping all three dimensions cleanly
  against the unchanged control.
- Generalization test (unseen prompt: "redesign the Thermochemistry
  warning state to feel calmer," never used to develop the fix): the
  routed response, invoking `rf-engineering-workbench` +
  `rf-scientific-ui-contract`, produced an explicit "Accessibility /
  contrast — checked" section, read the actual `Theme.qml` token values,
  assessed them informally, and correctly deferred the final verified
  pass to `rf-visual-qa` rather than asserting it had confirmed WCAG
  compliance itself. The fix generalized to a prompt that never mentions
  "technical" or "accessible."

**Outcome:** confirmed fixed, confirmed generalizes, no regression to the
dimensions that were already strong.

---

## Failure 2 — `rf-propulsion-visual-grammar` accepted a component's *name*
as evidence of implementation

**Eval:** 07, Engine Design 3D ("Create a realistic 3D rocket engine...").
This is one of the program's five blocking evals.

**Before:** **Both** conditions blocking-failed on scientific honesty and
fictional-capability avoidance. CONTROL (no skill) claimed chamber and
nozzle had "real sizing numbers" backing a "computed"-material solid,
directly contradicted by its own cited investigation two paragraphs
earlier (chamber sizing and nozzle contour are both explicitly documented
as unimplemented). ROUTED (`rf-propulsion-visual-grammar` +
`rf-qtquick3d-viewport`) made a narrower but still real error: it grouped
**injector** with chamber/nozzle/line as one of "the four grounded
components" with "real solver code" — even though `propellants.py` states
outright that injector geometry is "deliberately absent" and "belong[s] to
`engineering.injector`," a module that does not exist anywhere in the
codebase, and the routed subagent had *read that exact sentence* during
its own investigation.

**Root cause:** the skill correctly instructs "read
`rocketforge/engineering/`... before drawing a single node," but does not
distinguish between a component's *name appearing somewhere in the tree*
(a UI registry entry, a mention inside another module's own "what this
does not do" disclaimer) and an actual implementing module existing for
it. The routed subagent did the reading the skill asked for, and still
drew the wrong conclusion from what it read — because the instruction told
it *to* look, not precisely *what counts* as having found something.

**Fix (general rule, not the specific prompt):** Added a "Verify each
component individually, not the workspace as a whole" subsection to
`rf-propulsion-visual-grammar`'s Engine Design section: confirm an actual
computing module/class/function exists for each candidate component (not
a registry entry, not an incidental mention); treat an explicit "not
implemented" / "deliberately absent" statement anywhere in the code as
final for that component even where other language could be read as
suggestive of support; and when an agent's own written investigation
contradicts its later claim, the investigation wins and the claim must be
revised. The fix names the general failure pattern (name-as-evidence) and
the general resolution rule (investigation outranks an earlier draft's
conclusion) — it does not mention "injector" as a special case to hard-code
around; the same rule would catch the same mistake made about any other
component name.

**Verification:**
- Eval 07 rerun (same prompt, fixed skill, independently re-derived ground
  truth from the source rather than trusting either candidate's
  self-report): routed went from **blocking-fail** (misclassified
  injector as having "real solver code") to a **clean PASS** — scientific
  honesty 5/5, fictional-capability avoidance 5/5, no component rendered
  as solved geometry it does not have, explicit "SYSTEM SCHEMATIC —
  IMPLEMENTED COMPONENTS ONLY" label. The unchanged control response
  (not touched by the fix) still blocking-fails on the same
  self-contradiction as before, which is the expected, correct outcome —
  the fix only had to change the routed condition's behaviour.
- Adjacent-eval regression check (eval 04, nozzle realism — also owned by
  `rf-propulsion-visual-grammar`, previously passing cleanly): rerun
  confirms it still passes cleanly (5/5, no blocking fail) after the fix.
  The fix did not regress the case that was already working.

**Outcome: confirmed fixed on the blocking eval it was written for, confirmed
no regression on the adjacent eval owned by the same skill.**

---

## What was deliberately not done

No fix hard-codes a specific eval prompt, a specific component name as a
special case, or a specific phrase to detect. Both fixes are stated as
standing rules an agent would need to violate on a *different* prompt to
reproduce the original failure — the generalization test for Failure 1
confirms this held on an unseen prompt; Failure 2's adjacent-eval rerun is
the same check for that fix.
