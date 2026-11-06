# DB-2B Wave 4 — US design and test documents

Status: PARTIAL. Four configurations ship, none of them a regression reference. The owner reviewed the
three new sources' rights readings and decided the RL10A-3-3 chamber pressure on 2026-11-06.
Baseline: `5841361`. Branch `feat/db2b-wave4-us-design-corpus`.

Frozen and unchanged: the DB-1 schema; source, rights and conflict admission; value-kind and Missing
semantics; the text-basis, excerpt and mixture-ratio gates; the owner mechanisms; and the number matcher.
One gate changed, by owner decision: the chamber-pressure station gate also accepts the recorded words `throat total`
and `injector face static`. Every other word still reads `UNKNOWN`. The one Wave 4 conflict the owner decided is
`CF-DB05-RL10A33-PC`.

## Why these four

After Wave 3, 95 DB-0.5 assertions on 14 engines had never been decided, and this wave's transcription of the F-1A
column made it 100. Wave 4 takes four engines whose values sit in NASA technical documents and decides 38 of them.
The other 62, on 10 engines, stay undecided. This wave did not assess their sources.

## Outcome per target

| Target | Configuration | Promoted | Withheld | Why withheld |
|---|---|---|---|---|
| RL10A-3-3 | `CFG-RL10A-3-3-FR1769` | 20 | 2 | The 400 psia names no station; the cycle is inferred, the report never prints "expander" |
| LR91AJ-11 | `CFG-LR91-AJ-11-T3E` | 4 | 2 | Mixture ratio has no printed direction; the Purdue row has no source |
| H-1, 200K rating | `CFG-H1-200K-S-IB-4` | 2 | 2 | The 200K is an acceptance band with no environment; mixture ratio has no printed direction |
| F-1A | `CFG-F1A-MSFC-2013` | 5 | 1 | Mixture ratio has no printed direction |

The promoted total is 31 and the withheld total is 7. The shipped corpus goes from 17 to 21 configurations and
from 156 to 187 assertions. Nothing already shipped changes.

## What each configuration is, and is not

- **RL10A-3-3**: Pratt & Whitney's design estimates (PWA FR-1769, 1966) at 15,000 lb and mixture ratio 5.0. These
  are not test or flight data.
- **LR91AJ-11**: the Titan IIIE stage II engine in the same systems summary that carries the LR87AJ-11. Thrust and
  Isp include the roll nozzle.
- **H-1, 200K rating**: the average engine of stage S-IB-4's sea-level logs, 200.53 kips and 262.60 s. It is an
  `AVERAGE`, never a rating.
- **F-1A**: one column of a 2013 NASA MSFC comparison slide that names no underlying document, so the source is
  `SECONDARY`. The weight is undefined and the slide's "ns" has no legend.

## Research records changed

The wave corrected four research records. Each was checked against the document, and none moves a conflict.

| Record | Change | Why |
|---|---|---|
| FR-1769 rights statement | "no reproduction notice" became "no copyright notice on pages read" | Same finding, in the wording the rights gate reads. The cover was viewed and the extracted text checked on 2026-11-06 |
| FR-1769 effective expansion ratio | Unit "A/A*" | A printed number carries its unit |
| H-1 200K thrust | Value 200.53, not 200530 | The unit is Kips, so 200530 Kips would have overstated it a thousandfold |
| LR91AJ-11 and H-1 200K conditions | Environment `vacuum` and `sea_level`, roll nozzle in its own key | The gate reads only those environment words |

The F-1A column's other five cells were transcribed from slide 13, which was viewed as an image on 2026-11-06.

## Owner decisions

**Rights readings, accepted 2026-11-06** (a RocketForge shipping-policy review, not a legal determination):
`SRC-DB05-NTRS-19670005471`, `SRC-DB05-NTRS-19680003903`, `SRC-DB05-NTRS-20140011656`. Source tiers are unchanged, so
the F-1A slide stays `SECONDARY`.

**Chamber pressure, decided 2026-11-06.** 385.2 psia (throat total) and 394.6 psia (injector face static) are to ship
at their own stations, and 400 psia stays withheld. They are design estimates, not a regression reference.

## Boundaries

- No figure, topology or schematic ships.
- No value is averaged, chosen or derived. The LR91AJ-11 flows imply a mixture ratio, and it is not carried.
- `REGRESSION_CANDIDATE` is `NOT_SUPPORTED` for all four configurations, and DB-4A's result stays zero accepted.
- `tests/application/test_reference_engine_regression.py` pins the corpus hash, which this wave updated. DB-4A's
  review logic and verdicts are unchanged.

Tests: `tests/research/test_db2b_wave4_promotion.py`.
