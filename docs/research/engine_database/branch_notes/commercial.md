# DB-0 branch "commercial": notes (as of 2026-10-08)

## Session constraints (read first)
- **WebFetch failed with DNS errors for every host**, and curl egress was refused with a proxy 403. No document was opened directly.
- **Every source is `access: search_result_only`.** Values came from the web-search tool's summaries of the pages. The summaries
  sometimes did not say which of several pages printed a number. Those cases carry "attribution not pinned" in `locator`/`note`.
  Before any of these values is used, re-open the PDF or page and confirm the exact locator.
- **The shared web-search budget (200 per turn) ran out after 16 searches from this branch.** So the sweep stopped at SpaceX,
  Blue Origin, Rocket Lab and part of Firefly. Everything else on the sweep list is a placeholder (see below).
- Output: 65 engine records. 27 have sourced key values and 38 are identity-tracking placeholders. There are 52 sources and
  17 conflicts. No schematics were viewed, so `schematics.json` is empty.

## Placeholder policy
Some engines were never searched: Relativity, Astra, ABL, Virgin Orbit, Ursa Major, Launcher, Stoke, Masten, XCOR, TRW/NG,
AR1/AR22/RS-25E, Intuitive Machines, Spectre, Curie/HyperCurie, Draco/SuperDraco and BE-1/BE-2. Each of these has a record
with `status: unknown`, propellants `NOT_AUDITED`, cycle `UNKNOWN`, no key values, and a notes line that begins "NOT_AUDITED in
this session". Any expectation in the notes (e.g. "Hadley ORSC", "Aeon R GG", "Zenith FFSC") is copied from the sweep brief or
is analyst prior knowledge. It is labelled "to verify" and is **not** data.

Engines from the sweep list that got no record, because no verified designation was available: Agile Space Industries
thrusters, Vector-R engines, Phantom Space, Armadillo Aerospace, Garvey Spacecraft, Microcosm Scorpius, Rotary Rocket Roton,
Kistler K-1/AJ26 (cross-reference to the Russia branch's NK-33), Frontier Aerospace (Peregrine), Gilmour Space. They are the
next-session work list.

## Key findings (sourced)
- **Merlin lineage**, sorted by ratings that the sources give:
  - 1A: ablative, 340 kN (Wikipedia only), flew in 2006 and 2007.
  - 1B: 380/420 kN, never flown (Wikipedia only).
  - 1C (SpaceX 2007 press release, reproduced on another site): the Falcon 1 configuration is 78 klbf SL / 90 klbf vac / 301 s.
    The Falcon 9 configuration is 95 klbf SL / >108 klbf vac / 304 s.
  - 1C Vacuum: 411 kN, 342 s, niobium radiative extension, first flight 2010-06-04.
  - 1D: 147 klbf, then FT at 170 klbf (Spaceflight Now 2015), then the current 845 kN / 190 klbf (Falcon User's Guide 2025-05-09).
  - MVac: 981 kN, 397 s burn, 165:1 (SpaceX).
  - The 1C was split into Falcon 1 and Falcon 9 configuration records because SpaceX itself published two ratings.
  - SpaceX publishes **no Isp and no cycle wording** on the pages that were seen. "Gas generator" and the 282/311 s values
    come only from Tier D sources (Space Launch Report data sheets hosted at sma.nasa.gov, and Wikipedia), and they date
    from the 2013 v1.1 era.
- **Raptor**:
  - SpaceX (updates page): Raptor 3 is 250 tf SL (Raptor 2 was 230 tf) and 275 tf vac (Raptor 2 RVac was 258 tf). The
    sea-level engine mass went from 1,630 kg to 1,525 kg.
  - Raptor 3 first flew on Starship Flight 12, 2026-05-22. One booster engine shut down and the ship lost one Raptor 3
    vacuum engine. Flight 13 flew on 2026-07-24.
  - Cycle: SpaceX says "staged-combustion". "Full-flow" (FFSC) comes from secondary sources only.
  - Chamber pressure: Musk said 300 bar routinely for Raptor 2 (press). Test peaks were 321 bar and 330 bar. **No source for
    350 bar was found.**
- **Blue Origin** (all Tier A company pages):
  - BE-4: ORSC, LOX/LNG, 640 klbf (2,846 kN), throttles to 220 klbf. The development-era rating was 550 klbf, which works out
    to 2,447 kN by conversion. That likely explains the brief's "2400 vs 2450 kN".
  - BE-3PM: tap-off, 110 klbf, throttles to 20 klbf.
  - BE-3U: "open expander" (expander bleed), now 200 klbf. Earlier ratings were 160 and 173 klbf, and the 2 × 160 → 2 × 200
    klbf uprate is documented.
  - BE-7: "dual-expander", 10 klbf, throttles to 2 klbf.
- **Rocket Lab**:
  - Rutherford electric pump: brushless DC motors and LiPo batteries drive impeller pumps. The SL engine is 5,600 lbf
    (was 5,500) and the vacuum engine is 5,800 lbf at 343 s.
  - Flag: the "311 s" Isp labelled as sea level is physically suspect.
  - Archimedes: ORSC, 165 klbf (733 kN), 102% power on its first hot fire on 2024-08-08. The vacuum version is 200 klbf
    (890 kN); an earlier figure was 202.3 klbf (900 kN).
  - Neutron debut slipped to 2026 (Spaceflight Now, 2025-11). A stage tank ruptured in January 2026. An August 2026 relay
    of SpaceNews said Q4 2026 is not guaranteed and 2027 is possible. **No flight is confirmed as of 2026-10.**
- **Firefly**:
  - The company confirms a "patented tap-off cycle" for Reaver, Lightning and Miranda.
  - Alpha page: stage 1 is 801 kN vac for 4 Reaver at 295.6 s. Stage 2 is 70.1 kN for Lightning at 322 s.
  - User's Guide 5.2 maximums: 836.3 kN and 73.0 kN.
  - Miranda: 230 klbf. The same release gives Reaver as 45 klbf.

## Weak or uncertain areas
- Several "manufacturer" values are attributed to a specific press release only because the search summary said "an earlier
  update" or "press releases". Those are marked "not pinned".
- Rocket Lab's country: the company is headquartered in the US and the engines were developed in NZ. IDs use `NZ`, and the
  country field is "US/NZ".
- Status of Alpha after 2025, and of New Shepard, BE-7 and Blue Moon in 2026: NOT_AUDITED.
- First-flight years for BE-4 (Vulcan 2024), BE-3U (New Glenn 2025) and Merlin 1D (2013) are analyst knowledge. They were not
  sourced this session and are only stated in the notes and period fields with that label.
- Patents US 11,149,691 / 11,708,804 / 11,970,996 (staged combustion with an integrated preburner) appeared in an Archimedes
  search. **Their assignee was not seen. Do not link them to Rocket Lab.**

## Recommended anchor engines from this branch
1. **BE-4**: Tier A for cycle, propellant, thrust and throttle; a clean ORSC methane-class reference.
2. **Merlin 1D Block 5 / MVac**: Tier A thrust, burn time and area ratio (165:1). Isp and cycle are a proprietary gap, which
   is a good test of the "missing is valid" handling.
3. **Rutherford**: the only Tier A electric-pump-fed orbital engine.
4. **Raptor 3**: Tier A thrust and mass, with a dated 2026 flight debut.
5. **BE-3PM**: Tier A tap-off cycle statement.

## Next-session priorities
Get WebFetch access, or a larger search budget. Then:
1. Open the Falcon User's Guide and the Electron / Neutron / Alpha user's guides to pin locators.
2. Work through the FAA environmental assessments: Starship 2022 PEA, New Glenn LC-36, Neutron Wallops, Alpha VSFB.
3. Sweep the unaudited list, starting with Hadley, Aeon R, Zenith, E2, NewtonThree and VR900, and look for primary
   sources on cycles.
