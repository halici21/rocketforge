# DB-4C display — the ideal reference cases in the application, compared, never judged

Status: IMPLEMENTED (2026-11-11). The owner accepted the eight decisions in §1 as recommended (2026-11-10), and
§12 records what was built. This is the scientific-UI review that DB-4C §8 and §10 require before any display. It changes
no computation: `reference_ideal_case.py`, the four cases and every rule in DB-4C stay as they are.

DB-4C (`DB4C_SSME_TDK_IDEAL_REFERENCE.md`) holds four points from two 1985 TDK documents: the SSME current design and
enlarged throat (NASA-CR-178740), and the TDK manual's RL-10 OTV and Advanced Space Engine samples (NASA-CR-178628).
Today their two steps are seen only through `tools/reference_engines/report_ideal_case.py`, run by hand.

## 1. Decisions

| # | Decision | Recommendation | Main alternative |
|---|---|---|---|
| 1 | Where it lives | A new workspace, **Reference Cases**, in the Reference family beside Equations, Propulsion Database and Reference Engines (§3) | A tab in Rocket Performance (rejected in §3) |
| 2 | When it computes | Only on an explicit **Run** for all four points. Never at start-up, never on navigation, nothing persisted | Run each point separately |
| 3 | What shows before a run | The printed values, inputs and declarations of every point, which are data and need no provider. Computed columns read "not run" | An empty page until Run |
| 4 | How the steps are separated | Two panels per point, never one table: step A "TDK printout beside NASA CEA" and step B "RocketForge's reduction beside NASA CEA". No RocketForge-against-printout row anywhere (§5) | A combined table with a step column |
| 5 | How a difference is written | Signed, with its operands named in the column head ("CEA − TDK", "RocketForge − CEA"), the absolute value in its unit beside the relative one. Never a bare percentage, never colour-coded (§6) | Relative only |
| 6 | How points relate on screen | One point at a time. The point list shows each point's source and inputs, never a result, so no screen sets two points' differences side by side (§4) | All four stacked |
| 7 | How much context is visible | All ten declarations, every warning, the case's missing items and its "not recorded" note, always visible on the point's record: nothing behind a tooltip or a collapsed section | Declarations in an inspector |
| 8 | Scope | DB-4C's four points only. DB-4B's Isp ratio is not shown here; it needs its own review (DB-4B §9) | Host DB-4B too |

## 2. What the display may say, and what it may not

It carries DB-4C's meaning unchanged:

- Every step A row is `compared`. The source is an independent code, so no row agrees, disagrees, passes or fails, and
  no bound or tolerance is formed.
- Every step B row is a `model difference`: RocketForge's constant-gamma, calorically perfect reduction beside CEA at the
  same point. It is not an error, and RocketForge's number is not "wrong by" it.
- A step A difference is code and thermodynamic data (TDK 1985 against NASA CEA), plus the declared input
  differences. It is never a RocketForge defect.
- Nothing compares RocketForge with a printout directly, and nothing compares one point with another.
- Nothing here is engine evidence, a catalog value or a regression reference. Regression references stay 0.

So the page never contains the words *error*, *accuracy*, *efficiency*, *loss*, *pass*, *fail*, *agree*,
*validated* or *verified* applied to a row, and no row carries a success or failure tone. §9 makes this a test.

## 3. Where it lives

**Recommended: a workspace of its own in the Reference family.** That family is where the program keeps what it did
not design: equations, measured evidence, the engine corpus. A published printout set beside CEA belongs with them. The
navigation entry would read:

- label "Reference Cases";
- solver note "NASA CEA · RocketForge ideal performance, run on request";
- computed note "Published code printouts beside NASA CEA; compared, never judged".

Rejected homes:

- **Rocket Performance.** Its three views share the controller's single current result, so that switching never
  recomputes and two views can never disagree. A fixed 1985 case is a different case from the user's chamber. Showing
  one there would put a result about another engine beside, or instead of, the result the page's header describes —
  the header-versus-drawing failure in a new form. Its existing "Provider performance" tab already shows step B's kind
  of comparison for the user's own case.
- **Reference Engines.** Its controller is read-only by contract: it loads the corpus once and solves nothing, and it
  imports no provider or comparison code. Step A and step B need five CEA computations per point. Only one point of the
  four is tied to a catalog configuration, and only through its source record. A panel on that record would read as
  evidence about the engine, which DB-4C says it is not.
- **Propulsion Database.** Measured evidence records, read as stored, with nothing solved. The same objection applies.

## 4. Composition

The page follows the reference workspaces' grammar: a browser, a record and a run bar. `rf-engineering-workbench`
owns the chrome when it is built.

**Run bar.** One button, Run all four points, with the provider's state beside it: available, unavailable with its
reason, or running. A second run recomputes everything and keeps nothing from the first. With no chemistry library
installed the button is disabled, the reason is shown, and the printed values stay readable.

**Browser.** Four rows, grouped by document:

- NASA-CR-178740 (1985 SSME report): Current design (3285 psia, ε 77.5); Large Throat (3010 psia, ε 69.5).
- NASA-CR-178628 (1985 TDK manual): RL-10 OTV test engine (394.3 psia, ε 205.03); Advanced Space Engine
  (2287 psia, ε 400.7148).

Each row shows the point's name, its chamber pressure, O/F and area ratio, and its run state after a run (ok,
refused, unavailable). It never shows a difference, so the list cannot be read as a ranking.

**Record**, for the selected point, top to bottom:

1. *Source.* The case title, the full source citation with table and page, the code and its version ("not stated"),
   the database version, and the class: "Independent code: compared, never judged".
2. *Run inputs.* What was run: LH2 20.27 K, LOX 90.17 K, O/F, chamber pressure in psia and Pa, and the area ratio, all
   from the outcome's own run record. Before a run, the same values come from the point record and are labelled
   "to be run at".
3. *Step A — TDK printout beside NASA CEA.* Three rows (§5).
4. *Step B — RocketForge's constant-gamma reduction beside NASA CEA.* Two rows (§5).
5. *Declarations.* The ten lines, in their fixed order, verbatim, then the provider's warnings verbatim, or "none".
6. *What the source does not give.* The case's `missing` items and its notes, which carry the "not recorded" list
   verbatim.

A point that stops shows its reason in place of both step panels, with the kind ("refused" or "unavailable"). It never
shows a partial table, matching the runner's all or nothing.

## 5. The two tables

**Step A — TDK printout beside NASA CEA.** Heading note: "Two codes on the same inputs. A difference is code and
thermodynamic data plus the declared input differences; it is never a RocketForge defect."

| Quantity | TDK 1985, as printed | NASA CEA | CEA − TDK | Kind |
|---|---|---|---|---|
| Chamber temperature | 3635.107 K (6543.192 R) | 3617.574 K, RocketForge's chamber (a CEA equilibrium solve) | −17.533 K (−0.482 %) | compared |
| Vacuum Isp, shifting equilibrium | 465.1311 s | 464.6838 s | −0.4473 s (−0.096 %) | compared |
| Vacuum Isp, frozen at the chamber | 446.7661 s | 447.0315 s | +0.2654 s (+0.059 %) | compared |

The values above are the current design's first-run readings (DB-4C §11). They illustrate the layout only: the page
prints whatever the run returns, and no test pins them.

**Step B — RocketForge's constant-gamma reduction beside NASA CEA.** Heading note: "The same point; the printout takes
no part. RocketForge holds gamma and R constant through the expansion, CEA does not: a model difference, not an error."

| Gamma basis | RocketForge, vacuum | NASA CEA, vacuum, matching expansion | RocketForge − CEA | Kind |
|---|---|---|---|---|
| frozen | 454.4515 s | 447.0315 s (frozen) | +7.4200 s (+1.660 %) | model difference |
| equilibrium | 475.2373 s | 464.6838 s (shifting equilibrium) | +10.5535 s (+2.271 %) | model difference |

Both rows are always shown together. Neither basis is preferred, and neither is highlighted.

## 6. Numbers, signs and units

- A difference is always signed and always names its operands in the column head. The relative value is always
  beside the absolute one, never alone. This is the remedy for DB-4B §9's warning that a bare percentage reads as an
  efficiency.
- No colour, icon or tone encodes a difference's size or sign. Differences use the body text colour, so that +1.66 %
  is not styled as better or worse than −0.10 %. State words (not run, running, ok, refused, unavailable) carry their
  meaning in text as well as tone, so they survive with colour removed.
- Isp is shown in seconds. A printed lbf·s/lbm is numerically the same value, and the column head says "s
  (lbf·s/lbm as printed)". Temperature is shown in kelvin with the printed rankine value in brackets. Both conversions
  are DB-4C's exact ones.
- Printed values keep their printed decimals, so 465.1311 s is never shown as 465.13. Computed values use the same
  decimals as the printed value they stand beside. Run inputs are shown as given; a mixture ratio or area ratio is never
  rounded, the fault DB-4C §15 and §16 fixed in the report.
- Every string is formatted in Python. QML only places text, so the report and the page cannot round differently.

## 7. States

| State | What it says | What it must not look like |
|---|---|---|
| Not run | Printed values and inputs; computed columns read "not run" | Zero, a dash read as zero, or an empty table |
| Running | The run bar says running; the previous tables are cleared, not kept beside a running label | A finished result |
| Ok | Both tables, declarations, warnings ("none" when none) | Validated, agreed or passed |
| Refused (one point) | That point's reason and kind, in place of its tables; the other points unaffected | A partial table, or another point's numbers |
| Unavailable (no provider) | The reason from the provider gateway; printed values still shown | A refusal, a failure of RocketForge, or "no data" |

There is no stale state: every input is fixed in the case modules and nothing on the page can change one. A run made
before a provider change is not reused; each Run recomputes everything.

## 8. Architecture

- `rocketforge/application/analysis/reference_case_view.py` (new, pure): turns `IdealCaseOutcome`s and the point
  records into display rows and strings. It has no Qt and no provider. It is the single place where numbers become
  text.
- `rocketforge/application/analysis/reference_case_controller.py` (new): `ReferenceCaseController`, registered in
  `main.build_engine()` as the singleton `ReferenceCases`. It exposes `points`, `selectedIndex`, `runState`,
  `providerState` and row models through `RowListModel`, and the slots `run()` and `select(index)`. It calls
  `run_ideal_cases()` synchronously, as Rocket Performance's `runOracle` does. All four points take about 1 s
  the first time (the provider import) and about 0.02 s after that.
- `ui/pages/ReferenceCasesPage.qml` and `ui/pages/referencecases/` (new), plus an entry in `ui/data/Navigation.qml`'s
  page list and Reference family.
- Layers: the controller sits in `application`, reaches CEA only through `reference_ideal_case` and its existing
  gateways, and imports no provider at module level. `tests/test_architecture.py` stays green unchanged. QML computes
  nothing (`rf-qml-architecture`).

No case module, runner, rule or test of DB-4C changes.

## 9. Tests and visual QA

- **Parity.** For injected outcomes, every number the view module produces equals the report's for the same outcome,
  with the same sign and decimals. A negative control shows that a changed digit is caught.
- **Meaning.** No string the view produces contains the words listed in §2. No row joins two points. No row puts
  RocketForge beside a printout. Both step B bases are always present. A refused point yields no step rows.
- **States.** Not run, ok, one point refused, and provider unavailable each produce the texts in §7. Not run never
  produces a zero.
- **Runtime.** The page loads in the shell. Navigation reaches it and leaves it (`test_shell_navigation_smoke.py`). It
  works with no provider installed.
- **Visual QA** (`rf-visual-qa`): not run, ok, refused and unavailable, at 2560, 1920 and 1366 px, light and dark. It
  also checks with colour removed that no difference is styled.
- One CEA-gated test runs the real four points through the controller and checks structure only. No computed value is
  pinned, as in DB-4C.

## 10. Not in scope

- DB-4B's engine-level Isp ratio (decision 8).
- Charts. Four points with five rows each are read as numbers. A plot of differences across points would be the
  cross-point comparison DB-4C forbids.
- Export, saving or session persistence of a run.
- Any new point, case, rule or computation.

## 11. Rules fixed now

- The page shows what the runner returns, formatted once, in Python. It never recomputes, rounds differently, or fills
  a gap.
- No verdict, tolerance, pass, fail or styled difference, and no row between points or between RocketForge and a
  printout.
- No display change may be made in response to a reading. A change needs its own reason, stated without reference to
  the numbers.
- Regression references stay 0, and engine evidence and the catalog are untouched.

## 12. Implementation (2026-11-11)

Built as §3 to §9 describe, with no decision changed:

- `rocketforge/application/analysis/reference_case_view.py` is the one place a number becomes text.
- `rocketforge/application/analysis/reference_case_controller.py` is `ReferenceCaseController`, the QML singleton
  `ReferenceCases`.
- The page is `ui/pages/ReferenceCasesPage.qml` and `ui/pages/referencecases/` (the point list, the record and a small
  fixed table). Its navigation key is `referencecases`, the fourth item of the Reference family.

The controller reads the provider's availability the first time the page asks for it, and reads it again after each
Run. Choosing a point recomputes nothing.

Tests:

- `tests/application/test_reference_case_view.py`: texts, signs, decimals and their parity with the comparison, with a
  negative control; judging words; and both step B bases.
- `tests/application/test_reference_case_controller.py`: computing only on Run, nothing kept between runs, a refused
  point in each position, an unavailable provider, the lazy availability read, and one CEA-gated real run that checks
  structure only.
- `tests/application/test_reference_cases_runtime.py`: the real shell. Browsing, themes, sizes and re-entry make zero
  runs. The real Run button makes one, and is disabled without CEA. There is no QML warning, no judging word, and no
  accumulating page.

The not run, ok, refused and unavailable states were captured at 2560, 1920 and 1366 px, light and dark, and read: no
difference is styled, and each state is carried in words. No computed value is pinned by any test.
