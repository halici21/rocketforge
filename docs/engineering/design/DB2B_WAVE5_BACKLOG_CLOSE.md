# DB-2B Wave 5 — closing the assertion backlog

Status: COMPLETE for the backlog. One configuration ships, and it is not a regression reference. No DB-0.5 assertion
stays undecided.
Baseline: `ded03fc`. Branch `feat/db2b-wave5-backlog-close`.

Unchanged: the DB-1 schema and every gate. No gate was added or loosened.

## Outcome

Before this wave, 62 assertions on 10 engines had never been decided. Now 6 ship and 56 do not. The shipped corpus goes
from 21 to 22 configurations and from 189 to 195 assertions. Nothing already shipped changes.

| Engine | Assertions | Ships | Why the rest do not |
|---|---|---|---|
| RS-68 | 7 | 6 | The mixture ratio prints no direction |
| RD-180 | 26 | 0 | A proposed engine's study, an unsourced list in an open conflict, or pages with no reuse licence |
| NK-33 | 9 | 0 | The owner kept the Aerojet slides withheld |
| H-1 | 6 | 0 | A Purdue table with no source, rating name or date |
| SSME 1971-1981 | 5 | 0 | Printed AAS copyright |
| RD-171M | 3 | 0 | Terms of use with no reuse licence; an abstract only |
| RD-0120 | 2 | 0 | Printed copyright |
| LR87-AJ-5 | 2 | 0 | Printed copyright; a hobby transcription |
| LR87-AJ-7 | 1 | 0 | Printed copyright |
| LR91-AJ-5 | 1 | 0 | A hobby transcription |

## What ships

`CFG-RS68-1999-BASELINE` is the 'RS-68 Engine Performance Baseline' slide of Rocketdyne's October 1999 IAF Congress
slides, before first flight. It is not the flown rating.

| Field | Value | Kind |
|---|---|---|
| Vacuum thrust | 745 klbf | `RATED` |
| Sea-level thrust | 650 klbf | `RATED` |
| Chamber pressure | 1410 psia, station `UNKNOWN` | `RATED` |
| Vacuum Isp | 410 s, printed '410 Avg' | `AVERAGE` |
| Area ratio | 21.5 | `NOMINAL` |
| Weight | the text 'Weight, lb < 15,000' | `OTHER` |

`REGRESSION_CANDIDATE` is `NOT_SUPPORTED`: there is no mixture ratio and the Isp is an average. (At this wave the check
also reported that the thrust claims differ. That was the rule's error, corrected afterwards: see DB-4A §10.)
`PERFORMANCE_REFERENCE` is `PARTIAL`, for
the missing mixture ratio. `ARCHITECTURE` and `TOPOLOGY` are `NOT_SUPPORTED`: no propellants, cycle or graph are
recorded for this configuration.

## Owner decisions of 2026-11-06

- **RS-68 slides' rights reading: accepted.** NTRS public use, not export controlled, and no notice on any of the 64
  slides. They were viewed as contact sheets, and the small text under the logo was read at higher zoom on two slides.
  This is a RocketForge shipping-policy review, not a legal determination. The research record moves from
  `RIGHTS_REVIEW_REQUIRED` to `VALUES_WITH_ATTRIBUTION`.
- **RS-68 sea-level thrust and chamber pressure: shipped** for this configuration only, under
  `CF-DB05-E-US_HIST-04`, which stays `PARTIALLY_RESOLVED`. The throttled column (836 psia) is not admitted.
- **NK-33 Aerojet slides: kept withheld.** A company presentation on a National Academies page has no government
  public-use determination.

## Consequences

- The ULA guide's 705,250 lbf for the RS-68A does not ship: the guide prints 'All rights reserved'. With NASA's blog value
  also withheld, the RS-68A ships no thrust.
- RD-180 stays out of the catalog, and its three unresolved conflicts (mass, throttle, area ratio) stay open in research.
  The MSFC 1995 figures describe an engine proposed before the RD-180 existed.
- Regression references stay at zero. This wave did not change that.
- No conflict moved. The unresolved count stays 32.

## Research records changed

- RS-68 slides: the rights statement and rights class above.
- RS-68 thrust and Isp: the environment words `vacuum` and `sea_level`. The slide prints 'vac', 's/l' and 'vacuum'.

Tests: `tests/research/test_db2b_wave5_promotion.py`.
