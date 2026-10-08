# anchor_us_classic — NOTES (run 2026-10-08)

## Status: BLOCKED. No engine data recorded.

What I could reach in this run:
- **WebFetch**: `getaddrinfo ENOTFOUND` for every host tried (ntrs.nasa.gov, en.wikipedia.org, enginehistory.org).
  The rights branch log reports the same thing.
- **curl through the agent proxy**: CONNECT 403 or no response for ntrs.nasa.gov, nasa.gov, history.nasa.gov,
  archive.org, web.archive.org, ibiblio.org, loc.gov, dtic, osti, astronautix, enginehistory. Only github.com
  answered, and `gh` is limited to this session's configured repositories.
- **WebSearch**: one query got through ("SSME Orientation Part A ..."). After that, every call returned
  "web search budget used up (200 per turn, shared by every agent in it)", because the parallel branches
  had already used the budget.

So no Tier A/B document was opened, and no number, figure number, or topology edge could be traced to a source.
Following HONESTY > COVERAGE, I recorded nothing from memory:
- the anchor files hold `variant_scope` plus `missing[*] = ACCESS_BLOCKED` for every field group;
- `assertions`, `operating_points`, and `topology` are empty;
- `schematics.json` and `conflicts.json` are empty;
- in `engines.json`, identity, propellant, and cycle come from the orchestrator's prompt and are marked
  `cycle_status: UNKNOWN`, with an explicit "not verified" note.

## What the one search produced (all `search_result_only`)
- `SRC-ENGINEHISTORY-SSMEORIENT-1998`: Rocketdyne/Boeing "SSME Orientation" handout, June 1998, code BC98-04,
  marked "Rocketdyne and Boeing Proprietary" → rights need review even though it is hosted publicly.
  This is the abbreviated-course handout, *not* the "Part A-Engine" manual.
- `SRC-RRAUCTION-SSMEORIENT-PARTA-1984`: auction listing for "SSME Orientation (Part A-Engine)", Rocketdyne/Rockwell,
  Nov 1984, 199 pp. plus a 52-pp. "SSME Description and Operation" supplement. This predates Block II, so it is
  usable only for Phase I/II context. The task's description of a "Part A/B, 1998" manual mixes up two documents.
- Other hits not opened: ibiblio "SSME Overview.pdf", KSC 167449main_SSMEPF-06, nasa.gov 3.pdf and 3HO.pdf,
  enginehistory SSME1.pdf, LoC item tx1115 (what it is: unknown).

## Retrieval plan for a re-run (task leads; document numbers below are UNVERIFIED)
Re-run when WebFetch/NTRS access works, or with a fresh search budget. Leads named in the task prompt:
- RS-25D: the 1998 SSME Orientation PDF above (rights review), the ibiblio SSME Overview, Biggs "SSME: the first
  twenty years" (AIAA, RESTRICTED_REFERENCE), and NASA SSME fact sheets.
- RL10A-4-2 / RL10B-2: NTRS RL10 papers and P&W/Aerojet datasheets. Binder NASA CR-195478 covers **RL10A-3-3A
  only**, so keep it as a separate variant.
- J-2: Saturn V Flight Manual MSFC-MAN-503 (engine figures), Saturn IB flight manual, NASA SP-4206.
- J-2S: NTRS J-2S reports.
- F-1: Saturn V Flight Manual, Rocketdyne R-3896-1 F-1 Engine Familiarization Training Manual, and the
  Betts & Frederick F-1 reverse-engineering AIAA paper.
- H-1: H-1 engine manuals (number unverified), Saturn IB flight manual.
- LR87-AJ-5: Gemini Launch Vehicle documents, Titan II HAER (Library of Congress).

## Checks the task prompt raises (open questions, not findings)
- F-1 SL thrust: 1.5M vs 1.522M lbf. Are these early vs uprated ratings, or rounding?
- SSME % rated power level: 100% RPL definition; 104.5% vs 109%; Block II vs SLS (RS-25D adapted runs at 109%?).
- J-2: Isp across ratings and PU mixture-ratio settings (a single engine has several operating points).
- RL10A-4-2 "22,300 lbf" vs other quoted values; whether the oxidizer pump is gear-driven from the fuel-pump shaft.
- LR87-AJ-5: one turbopump per chamber vs shared GG. Do not decide this until the HAER or Aerojet docs are read.

## Likely schema breakers (hypotheses to confirm in sources, NOT findings)
Several operating points per engine (RPL %, PU MR steps); several pumps/turbines/preburners each needing its own
id (SSME four turbopumps and two preburners; J-2 separate fuel/LOX turbopumps with turbines in series); a
hydraulic-turbine-driven boost pump (SSME LPOTP); geared shafts (H-1, RL10?); an extendible nozzle with two
area ratios (RL10B-2); turbine exhaust used as nozzle-extension film coolant or heat-exchanger source (F-1);
multi-chamber engines that may or may not share a GG (LR87); a tap-off cycle (J-2S); stage-side items (start tank,
PU valve, autogenous pressurization) that blur the engine/stage boundary.
