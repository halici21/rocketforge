# QML memory soak — route erratum

**The session soak never entered Thermochemistry or Engine Design.** It said
PASS every time. Fixed on 2026-09-24. The earlier reports are left as written;
this note says which of their statements the defect affects.

## What was wrong

`experiments/qml_memory/soak.py` listed its workspaces as navigation keys and
dropped any key that did not resolve. Two did not:

- `"thermochemistry"`. The key is `"thermochem"`.
- `"enginedesign"`. Engine Design has no key at all: it is an application
  mode (`appMode = "engine"`), not a page.

So every session soak visited Rocket Performance, Fluid Properties, Line,
Trade Study, Isentropic and Nozzle Lab, and nothing else. The lifecycle soak,
meant to alternate Rocket Performance with Thermochemistry, alternated it
with Fluid Properties.

## Statements affected

- `CAD_CAE_WORKBENCH_R1_THERMOCHEMISTRY_INTEGRATION.md`, the row "Memory
  (session soak, 100 rounds, now touching the new schematic)". The soak did
  not touch it. The same holds for the archived
  `acceptance/cad_workbench_r1/memory/soak_session_with_thermochemistry.json`.
- Any other statement that the `experiments/qml_memory/soak.py` session soak
  covers "every workspace".

Not affected:

- The Analysis R2 mixed session (`ANALYSIS_R2_MEMORY_LEAK_CLOSURE.md`). It
  comes from `experiments/analysis_r2_memory/soak.py`, which uses the real
  `"thermochem"` key.
- The Line and Fluid Properties integration soaks: both keys resolved.

## The route contract now

- An unresolved key stops the soak before it measures anything, with
  `FAIL: unresolved navigation keys […]`. Negative control: adding
  `"thermochemistry"` and `"enginedesign"` back makes it exit 1 without
  writing a report.
- Each visit is confirmed by finding the page's own QML type visible in the
  window. Engine Design is confirmed shown in engine mode and hidden again in
  analysis mode.
- In each session round, Thermochemistry solves the bipropellant case and
  the RP-1311 solid grain, and checks each is solved in the mode it names. It
  shows the calculator and the species composition for both, and records the
  solid c* readout when it is shown. It then restores the bipropellant
  chamber, so Rocket Performance's canonical case is unchanged.
- The report carries `required_routes`, `visited_routes` (with counts),
  `missing_routes` and `thermochemistry_result_unchanged`. The verdict fails
  on any missing route.
- `tests/test_qml_memory_harness.py`:
  - checks every soak page against `ui/data/Navigation.qml` on every run,
    CI included;
  - checks the required routes;
  - for local evidence, fails a soak report that cannot say where it went.

## Results with every route visited

Final code, 100 rounds, the same settings as the earlier records:

| Soak | Private | First half | Second half | Page instances | Warnings | Routes |
| --- | --- | --- | --- | --- | --- | --- |
| lifecycle | 124.7 MB | 74.3 MB | 50.4 MB | 0 | 0 | Rocket Performance, Thermochemistry |
| session | 309.9 MB | 214.2 MB | 95.7 MB | 0 | 0 | all 7 pages, Engine Design, Thermochemistry bipropellant/solid/composition/solid c* |

Every route was visited in every round. Both canonical results were unchanged:
Rocket Performance, and Thermochemistry after the bipropellant → solid →
bipropellant round trip. Both soaks pass their verdict. For comparison, the
earlier 100-round records did not visit these routes. Lifecycle, paired with
Fluid Properties: 95.9 MB, 59.6 MB then 36.3 MB. Session: 191.8 MB,
149.8 MB then 42.0 MB.

### Open: a steady per-round tail

The verdict (second half no larger than the first) passes, but the growth
has not stopped:

- Lifecycle grows about 1.0 MB per round in every quarter of the run
  (1.12, 1.08, 0.94, 1.08). With Fluid Properties as the partner page it
  was 0.6 to 0.8.
- Session grows 2.77, 1.95, 2.05, then 1.77 MB per round.

What is known:

- No page instance and no QObject is retained.
- The chemistry path is not the source: 300 real CEA solves (bipropellant,
  solid, bipropellant) in a process without Qt grew 0.00 MB.
- The collector mode is not the source either. At 40 rounds the session soak
  reached 196 MB collecting in one pass and 201 MB incrementally.

The tail is therefore on the Qt/QML side. Earlier reports noted a
mixed-session tail of about 0.78 MB per round without Thermochemistry. It is
recorded here, not investigated: closing it is a memory investigation of its
own.

Visiting Thermochemistry exposed something the old soak could not. Under
Qt's incremental collector, 2 of 8 session soaks logged the warning that
preceded the navigation crash. That is why the application now collects in
one pass: see `NOTATION_NAVIGATION_CRASH.md`. In one-pass mode, 13 of 13
session soaks logged nothing.
