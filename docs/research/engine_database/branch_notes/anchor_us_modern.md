# anchor_us_modern — NOTES

## Access situation (read first)
- WebFetch: `getaddrinfo ENOTFOUND` for every host tried (ntrs.nasa.gov, www.nasa.gov, ibiblio.org, www.hq.nasa.gov, en.wikipedia.org).
- curl: every host returns proxy CONNECT 403 (ntrs, nasa.gov, spacex, blueorigin, rocketlab, ulalaunch, sec.gov, archive.org, dtic, ...).
- WebSearch: this branch got **2 searches** (Apollo DPS and SPS experience reports). The third returned
  "web search budget is used up (limit 200 per turn, shared by every agent)". No workaround was attempted.
- So: **no document was opened, no figure was viewed, and no page locators exist.** schematics.json is empty on purpose.
- To give the anchors something to work with, this branch reuses search-summary findings that sibling branches logged
  (`commercial/_research_log.txt`, `taxonomy/_worklog.txt`). Each such source is marked "relayed ... not seen by this branch".
  Every relayed assertion has confidence=low.
- Builder script (regenerates every file): `scratchpad/anchor_us_modern_build.py`.

## Per-anchor
1. **RS-68A**: nothing obtained. Helium spin start and GG-exhaust roll control are NOT verified (recorded in `missing`).
   To retrieve: ULA Delta IV user's guide, Rocketdyne AIAA JPC papers on RS-68, NTRS Ares V RS-68B studies.
2. **AJ10-190 (OMS)**: helium-regulated feed and GN2-actuated valves are relayed only, and tied to NTRS 19740026212, an id the sibling itself marked "?".
   The topology skeleton puts the He/propellant tanks at subsystem=vehicle (OMS pod). Orion ESM reuse was not audited.
3. **LMDE**: the strongest evidence in this branch. NTRS 19730011150 is "Apollo Experience Report: Descent Propulsion System"
   by Hammock, Currie and Fisher. The TN number D-7143 (Oct 1972) comes from the SAE 730941 citation. The orchestrator's guess "TN D-6837" has no support.
   The abstract names deep throttling and a lightweight cryogenic helium pressurization system as the distinctive features.
   Pintle injector, 10:1 throttling and flow-control-valve mechanisms are NOT verified.
   Flight evaluation: Apollo 15 Mission Report Supplement 4, MSC-05161 (ibiblio 19730023018.pdf).
4. **R-4D-11**: nothing obtained.
5. **Merlin 1D**: 845 kN / 190,000 lbf SL per engine, from the 2025-05-09 Falcon User's Guide (relayed). The 7,605 kN figure is the stage total.
   MVac 981 kN / 220,500 lbf, 397 s burn and 165:1 are in engines.json notes only; the provenance of the area ratio is uncertain.
   The thrust-by-date conflict could not be built because only one dated value was obtained. Pintle injector and TEA-TEB ignition are unverified.
6. **Raptor 2**: 230 tf / 507,000 lbf SL and 1,630 kg come only as the "from" side of a Raptor 3 comparison (ambiguous; relayed).
   The relayed SpaceX wording is "staged-combustion". "Full-flow" and the two preburners are unverified. Pc was not obtained.
7. **BE-4**: 640,000 lbf (2,846 kN), throttling to 220,000 lbf (978 kN), ORSC, LOX/LNG, 2012 start (relayed). The earlier 550,000 lbf rating is CF-1.
   Single preburner and boost pumps are unverified.
8. **BE-3U / BE-3PM**: BE-3U is "open expander", 200,000 lbf vac, throttling to 100,000 lbf. Its thrust history and cycle wording are in conflict (CF-2, CF-3).
   BE-3PM is "tap-off", 110,000 lbf, throttling to 20,000 lbf. These are kept as separate variant records, with cycle treated as a variant attribute.
9. **Rutherford / Rutherford Vacuum**: BLDC motors on LiPo batteries drive impeller pumps (relayed). SL 5,600 lbf (from 5,500), 311 s.
   Vac 5,800 lbf, 343 s; the 2022 page gave 24 kN / 5,500 lbf (CF-4).
   The topology has a non-fluid electrical edge from battery to motor, and the battery's subsystem is ambiguous.
10. **IPD**: FFSC, Rocketdyne+Aerojet, 250 klbf class, LOX/LH2. All of this is SECONDARY_CLAIM via a Spaceflight Now 2006 relay.
    NTRS 20040084662 and 20040129712 are identified but were not opened.
11. **AJ10-137 (SPS)**: NTRS 19730023031 is TN D-7375 / JSC-S-378 by Gibson and Wood (Aug 1973). The JAXA repository marks it "No Copyright".
    Helium primary/secondary regulators at 186/191 psig are relayed from enginehistory.org (Tier D).
    The Aerojet 1971 bipropellant valve improvement summary is NTRS 19710025470.

## Schema breakers seen even at this depth
- Dated re-ratings under one designation (Merlin 1D, BE-4, BE-3U, Rutherford). Engine values need validity dates.
- Stage totals quoted next to engine values (Merlin 7,605 kN; BE-3U 400,000 lbf; Electron 190 kN).
- Manufacturer cycle wording differs from encyclopedic wording (BE-3U "open expander" vs "expander bleed"). This needs a source-wording field plus a normalized enum.
- Cycle varies within a family (BE-3PM tap-off vs BE-3U expander).
- Electric-pump engines need energy (non-fluid) edges and battery fields.
- Pressure-fed engines whose pressurization belongs to the vehicle (OMS pod, SM, LM descent stage), sometimes with redundant regulators at different setpoints.
- Throttleable engines (LMDE, BE-3PM, BE-4) need multiple operating points.
- Ratings in tonnes-force (Raptor) must keep their units.
- Demonstrator powerheads (IPD) may legitimately have no nozzle data.
- Country is multi-valued (Rocket Lab US/NZ).

## Priority retrievals for a follow-up session (with fetch access)
NTRS 19730011150 (DPS), 19730023031 (SPS), 19710025470 (SPS valve), 20040084662/20040129712 (IPD);
ibiblio 19730023018 (A15 DPS eval) and 19700019020 (A9 SPS eval); the ULA Delta IV user's guide; the SpaceX Falcon user's guide 2025-05-09.
The Apollo TNs are the most likely sources of public-domain system schematics (unverified, no figure numbers seen).
