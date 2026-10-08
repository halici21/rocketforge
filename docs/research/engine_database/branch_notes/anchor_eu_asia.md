# anchor_eu_asia — NOTES

## STATUS: SEVERELY INCOMPLETE because the tools were blocked (not because sources are missing)
- WebFetch failed with DNS errors (getaddrinfo ENOTFOUND) on every domain tried: esa.int, www.esa.int,
  ariane5.cnes.fr, en.wikipedia.org, sma.nasa.gov, jaxa.repo.nii.ac.jp. curl CONNECT was rejected by the
  egress proxy (403). No page, PDF or figure could be opened.
- After this branch had made 5 searches, WebSearch returned "web search budget is used up (limit: 200 WebSearch
  calls per turn, shared by every agent in it)". The parallel branches used up the shared budget.
- Result: only Vulcain 2, Vinci and HM7B have evidence, and all of it comes from search-result snippets or
  search-engine summaries (access=search_result_only). The other 10 anchors (Viking 5C, LE-7A, LE-5B, LE-9,
  Vikas, CE-20, CE-7.5, YF-100, YF-77, KRE-075) have stub records marked NOT_AUDITED. Their engines.json
  entries keep the task prompt's descriptions only as notes, with cycle=UNKNOWN. Nothing was filled from memory.
- Fix: re-run this branch on its own (or with a higher CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION) and with
  working WebFetch.

## Vulcain 2
- Strongest sources reached: CNES Ariane 5 technical features (Tier A; 1,390 kN vac) and ESA "Ariane 5 ECA -
  New elements" (Tier A). ESA says the new nozzle lets turbopump exhaust be reinjected into the main system,
  which improves high-altitude performance. That confirms the topology feature asked about. Whether one duct
  or two is used, and which turbopumps' exhaust goes there, was not seen.
- Suppliers: LOX TP by Avio, LH2 TP by Snecma, from an old Wikipedia snapshot (Tier D). "Volvo" was not
  confirmed for any turbopump. The nozzle-extension supplier was not audited.
- Conflicts: thrust_vac 1340 / 1359 / 1390 kN (CF-1); pc 115 vs 117.3 bar (CF-2); epsilon 58.2 / 58.5 / 60 (CF-3).
- Variant trap (CF-4): the search engine attributed the ESA "esaMI" page values (LOX TP 13,600 rpm / ~3 MW;
  LH2 TP 34,000 rpm / ~12 MW; 235 kg/s total; 41.2 kg/s H2) to Vulcain 2. That page is titled "Vulcain engine"
  and probably describes Vulcain 1. These values are not attached as Vulcain 2 assertions.
- Not verified: dump-cooled nozzle extension, GG mixture ratio, turbine data.

## Vinci
- ESA (Tier A snippet): expander cycle, no gas generator, two turbopumps (LH2 and LOX), 60 s firing in 2005
  at full turbopump speed and full pressure.
- IAC-18 (ArianeGroup; author per search summary): the H2 turbopump delivers "more than 300 bar". That is a
  pump discharge pressure; it is not pc, which is 60 bar per Wikipedia.
- EUCASS 2019 (doi:10.1051/eucass/201911481): design heritage from HM7 and Vulcain.
- Wikipedia infobox values (Tier D only): 180 kN, 457.2 s, MR 6.1, epsilon 240, ~550 kg.
- Not audited: closed vs bleed (closed is not explicitly confirmed), the extendable nozzle, restart count and APU.

## HM7B
- GG and regenerative cooling come from Wikipedia and the AIAA web vehicle guide (Tier D).
- Thrust conflict: 62.2 (AIAA guide) / 64.8 (SatNow) / 67 kN (CNES) (CF-5).
- pc: 3.7 MPa in the infobox vs "raised from 30 to 35 bar" in the text (CF-6).
- Burn time: 950 s vs 15 min 45 s (CF-7). No restart (AIAA guide).
- The single turbopump with a gearbox was not verified.
- Schema breaker: one designation is used on Ariane 1-4 H10 and on Ariane 5 ESC-A with different burn
  durations, and sources do not separate the two.

## Schematics
- None were viewed. The one entry is a text-only placeholder for the Vulcain 2 reinjection.
- Rights: ESA/CNES web content and IAC/EUCASS papers are classed RIGHTS_REVIEW_REQUIRED or RESTRICTED_REFERENCE.

## Recommended next pass (priority)
- JAXA Repository papers for LE-7A, LE-9 and LE-5B (expander bleed; 1471 kN).
- ISRO / Current Science for CE-7.5, CE-20 and Vikas.
- 《火箭推进》 for YF-100 and YF-77.
- KARI papers for KRE-075.
- ESA/ArianeGroup brochures for Vulcain 2 and Viking.
