# r2_us_classic: round-2 anchor deep-dive (US classic engines)

Run date 2026-10-08. **35 of the 38 allowed WebSearch calls were used.** WebFetch and curl were not tried (ROUND2.md says they are blocked).
**No document was opened.** Every source has `access: search_result_only` or `not_retrieved`, and every locator reads
"search summary only; page NOT_AUDITED". The raw query-by-query evidence is in `search_log.txt` in this directory.
The build scripts are in `../r2_us_classic_build/`.

Status rules applied:
- A value is REPORTED only when the summary tied it to a named Tier A/B document (an NTRS id, the L3Harris sheet, the Hopson FRR, a ULA paper, AEDC reports).
- Wikipedia, Purdue, NASM, Astronautix, enginehistory and themilitarystandard.com values are SECONDARY_CLAIM.
- Some summaries merged several co-listed documents. Where I had to infer which one said something, the assertion note says "attribution inferred".
- Background knowledge appears below only as [BG], and only as something to verify.

## Outputs
- `anchors/` has 8 anchor files with 253 assertions in total, plus operating points, missing lists, text-derived topology graphs, coverage and schema breakers.
- `engines.json` has 11 records: the 8 anchors, plus the H-1 rating variants -188K, -200K and -205K, which reuse the us_hist ids.
- `sources.json` has 75 sources: 58 new or updated in round 2, the rest carried from the round-1 anchor branch.
- `conflicts.json` has 25 conflicts.
- `schematics.json` is **empty**. No search summary named a specific figure in a specific document. Several results are schematic-bearing documents but were not opened: the ibiblio "SSME Overview" (possibly JSC-19041), the AEDC J-2 and J-2S test reports, NTRS 20100027318, and NTRS 19650013470.

## Per-anchor findings

### RS-25D (SSME Block II)
- **Strongest sources:**
  - The Hopson STS-104 SSME FRR, 28 Jun 2001 (govdocs1 673547.pdf). Its Block I / IIA / II table gives:
    - at 104.5%: MCC Pc 2,870 psia, HPFT discharge 1,615 R, HPOT discharge 1,223 R;
    - at 109%: HPFT discharge 1,638 R and HPOT discharge 1,246 R (Block II); Pc 2,994 psia (Block IIA row);
    - Block I at 109%: 3,291 psia.
    - Caveat: the summary says the extraction is jumbled.
  - The L3Harris RS-25 sheet: Pc 2,994 psia, O/F 6.03, 69:1, 7,774 lb dry, 512,300 lbf vacuum at 109%, 67–109% throttle, H2 pump discharge 6,276 psia, O2 pump discharge 7,268 psia.
- **Area ratio is resolved (CF-RS-1).** The 1986 NASA "Large Throat" study (attribution to NTRS 19860012108 inferred) says enlarging the throat drops the ratio from 77.5 to 69.5 with the nozzle unchanged. So 77.5 and 78 belong to pre-Block IIA engines, and 69/69.5 belongs to Block IIA and Block II.
- **Pump speeds are secondary only:**
  - LPOTP 5,150 rpm, LPFTP 16,185 rpm, HPOTP 28,120 rpm (Wikipedia);
  - P&W HPFTP 36,200 rpm (a forum quoting P&W);
  - HPFTP 35,000 rpm for the Block I era.
  - No Tier A absolute speeds were found. The STS-113 FRR gives only sigma margins.
- **Preburners:** two, both fuel-rich, at about 5,000 psia (a generic overview figure). Element counts of 264 (fuel preburner) and 120 (oxidizer preburner) come from an unidentified patent. No temperatures or MRs were found.
- **Control:** the FPOV sets mixture ratio and the OPOV sets power level. The FPOV is ramped to 56% for fuel-preburner ignition (low confidence).
- **Topology** has 25 nodes and 32 edges, built from text. Missing pieces: MFV, CCV, ASIs, the heat-exchanger supply, the nozzle-coolant return, and the LPOTP turbine discharge return.
- **Excluded on purpose:** "470,000 lb at RPL, MCC 3,006 psia" from a NASA report. It is an earlier configuration, not Block II.
- **Unresolved:** dry mass, 7,774 lb (L3Harris) vs 7,004 lb (Wikipedia "RS-25D") (CF-RS-2).

### RL10A-4-2
- **Values:**
  - L3Harris sheet (Tier A): 22,300 lbf, 451.0 s, MR 5.5, 46-in nozzle (Atlas V).
  - AIAA vehicle guide: Pc 32.1 bar (465 psi), 85:1, 450.5 s.
- **Not found** for this variant: pumps, turbines, cooling, ignition, mass.
- **Topology is family context only.** The anchor's topology is INFERRED from RL10A-3-3A NTRS models: a two-stage fuel pump on the turbine shaft, a gear-driven single-stage LOX pump, design speeds of 30,000 and 12,000 rpm, a turbine bypass controlling Pc, and a PU valve. These are explicitly *not* A-4-2 values.
- **Variant table:** Wikipedia's 84:1 belongs to the RL10A-4 and A-4-1 rows. The A-4-2 row was truncated in the summary.

### RL10B-2
- **Thrust:** 24,750 lb, from two independent ULA sources (inaugural-launch paper and GPS III booklet).
- **Area ratio:** 285:1, from AIAA and NAP.
- **Chamber pressure has three values (CF-B2-1):** 633 psi and 644 psia (NAP text vs NAP table), and 465 psi (AIAA, the same as its A-4-2 value, so probably a copy error).
- **Nozzle extension:** C-C, three cones, Novoltex/Sepcarb, built by Airbus Safran Launchers, with the NEDS by AR, about 100 in long and just over 84 in exit diameter. Source: the IAC-18 paper 43630 metadata, or the Wikipedia "Nozzle extension" article (attribution inferred). The paper may describe later RL10 builds.
- **Not found:** the stowed area ratio.

### J-2
- **Best Tier A source:** NTRS 20100027318 (a Rocketdyne history chapter hosted by NASA). It gives:
  - up to 230,000 lb;
  - Pc "a little over 700 psia";
  - **MR 5.5 nominal, with capability for 4.5** (two operating points);
  - **a gas generator supplying two turbines running in series**;
  - pumps on opposite sides; area ratio 27.5:1;
  - a start tank that discharges cold GH2 through both turbines, with a helium tank inside the start tank.
- **From Wikipedia:**
  - fuel turbopump: axial, inducer plus 7 stages, 27,000 rpm, 30→1,225 psi, two-stage turbine;
  - oxidizer turbopump: single-stage centrifugal, 8,600 rpm, 1,080 psi, 2,200 bhp;
  - a crossover duct from the fuel turbine to the oxidizer turbine;
  - a start-transient bypass of the oxidizer turbine;
  - start tank refilled from the thrust-chamber fuel inlet manifold.
- **PU valve:** a LOX pump outlet→inlet bypass, with a calibration nozzle (enginehistory RPE08.22 and Wikipedia).
- **Not found:** thrust or Isp at MR 4.5, and a 5.0 setting.
- **Caution:** several summaries mixed in J-2X facts (an oxidizer-tank helium heat exchanger, turbine exhaust dumped along the nozzle extension, 448 s, a single-stage fuel turbopump). These were **not** attached to the J-2.

### F-1
- **Turbopump and turbine:**
  - Wikipedia: turbine 5,500 rpm and 55,000 bhp.
  - enginehistory: 91.5 rev/s, which derives to 5,490 rpm. MK-10 turbopump of 2,500 lb. Two-stage impulse turbine with 109 and 119 blades (33 in and 35 in).
- **Exhaust path:** a NASA text reproduction (Apollo Flight Journal credit) gives a fuel-rich LOX/RP-1 gas generator → turbine → **heat exchanger → wrap-around manifold → bell periphery**, with turbine exhaust film-cooling the extension. The regen chamber runs to 10:1 and the TEG-cooled double-walled extension to 16:1.
- **Ignition:** a hypergol cartridge of TEB with 10–15% TEA, with burst diaphragms, sitting in the high-pressure fuel circuit.
- **Unresolved:**
  - Pc 1,015 psi vs 982 psi (CF-F1-1). The 1,125 psia query hint was not found.
  - The heat exchanger's working fluids were not found.
- **Tier A home for these values:** "Saturn V News Reference: F-1 Engine Fact Sheet" (Dec 1968) at history.msfc.nasa.gov. It was located only through a citation and not retrieved.
- **Correction to round 1:** Rocketdyne R-3896-1 is "Engine Data", not a familiarization training manual (RR Auction listing).

### H-1
- **Key Tier A find:** NTRS 19650013470, a 1965 NASA report. One summary ties it to the H-1 at a **188,000 lb** rating. It gives:
  - major components: thrust chamber, turbopump assembly, liquid-propellant gas generator (LPGG), fuel additive blender unit (FABU);
  - cluster geometry: 4 inboard engines at 32 in, canted 3°, fixed; 4 outboard at 95 in, canted 6°, gimbaled.
- **Turbopump, from an OCR-garbled passage of the same document (engine identity medium):**
  - two-stage turbine, about 3,793 hp at about 32,000 rpm;
  - **gear reduction to the LOX and fuel pumps at about 6,537 rpm** (derived ratio about 4.9);
  - accessory drive at about 4,000 rpm, with an electrically heated bearing.
- **Wikipedia:** an SPGG solid start cartridge (500 V AC, 600–700 psi), then the LPGG; lubrication by an additive blended into the RP-1.
- **Thrust ratings** 188k, 200k and 205k are split into variant records.
- **Unresolved:** Isp at sea level, 255 s vs 263 s; mass, 2,200 lb vs 2,009 lb.

### LR87-AJ-5
- **Source quality:** the best source is themilitarystandard.com (Tier D; ex-crew technical pages that appear to paraphrase USAF technical orders).
- **Configuration:**
  - two regen thrust chambers and two identical turbopumps;
  - **each turbopump has a fuel pump, an oxidizer pump, a gearbox, and two balanced turbine wheels**;
  - each turbine stage has a nozzle diaphragm.
- **Start and thrust:** a solid starter cartridge burning about 1 s at about 2,000 psia; 430,000 lb at sea level.
- **Pressurization:**
  - the oxidizer "super heater" is stainless coils in the gas-generator exhaust outlet on **sub-assembly 2 only**;
  - Wikipedia: autogenous pressurization, with fuel-rich gas-generator gas for the fuel tank and evaporated NTO for the oxidizer tank.
- **Wikipedia values:** Pc 5.4 MPa, 8:1, MR 1.93, Isp 297 s vacuum / 259 s sea level.
- **Gas-generator count per engine is UNKNOWN** (one per sub-assembly is INFERRED).
- **HAER:** only CA-2408 (the 395-D launch complex) was found. There is no engine HAER.
- **Caution:** one summary said "only the verniers were solid propellant rockets". That contradicts the start-cartridge evidence and is not recorded. [BG] Titan II verniers were not solid rockets; verify.

### J-2S
- **Cycle:** tap-off (Wikipedia and its 2007 mirror; SECONDARY_CLAIM).
- **Performance:** 265,000 lbf and 436 s (NTRS 20120016414 table, carried from round 1). Idle modes of about 4k and 50k lbf (round 1).
- **AEDC test reports:**
  - TR-70-150: 10 idle firings in 1969, with a noncompartmented injector, 1,408.2 s total.
  - TR-70-204: 11 firings at 80,000–108,000 ft, with a full-face oxidizer injector for idle.
  - TR-70-38: tests J4-1902-08/-11/-12.
  - The mapping from AD numbers to TR numbers is not verified.
- **Study report:** "J-2S Improvement Study, System Description", D5-15772-2, 30 Apr 1969 (generalstaff.org; NTRS 19690072871 unverified).
- **J-2X link:** NTRS 20080036837 says the J-2X used the J-2S Mk.29 turbopumps as its point of departure.
- **Not found:** Pc and area ratio. The hints 1,246 psia and 40:1 are unconfirmed.

## Schema breakers seen across these anchors (all are in the anchor files)
1. **Several operating points per variant:**
   - % RPL levels (RS-25);
   - PU mixture-ratio steps (J-2);
   - idle and main modes (J-2S);
   - successive thrust ratings under one designation (H-1, F-1, J-2).
2. **Several turbomachines with different drive media:**
   - RS-25: hot gas, regen-heated GH2, and a liquid-LOX hydraulic turbine;
   - J-2: turbines in series across two shafts;
   - RL10, H-1 and LR87: gearboxes with several output speeds;
   - RS-25 HPOTP: two pumps on one shaft with different discharge pressures.
3. **Turbine exhaust doing other jobs:** as nozzle-extension coolant after a heat exchanger (F-1), as a tank pressurant source (LR87), and as main-injector fuel (RS-25 closed cycle). Tap-off makes the chamber the turbine gas source (J-2S).
4. **Multi-chamber, single-unit engine with asymmetric sub-assemblies** (LR87).
5. **Geometry that changes in flight:** the deployable nozzle (RL10B-2). Also two area ratios with different cooling inside one nozzle (F-1).
6. **Consumable start devices:** solid cartridges (H-1, LR87), a hypergol cartridge (F-1), and a refillable start tank (J-2).
7. **Engine/stage boundary blur:** tank pressurization taps, pogo accumulator, cluster cant and gimbal by position (H-1), and ducts routed through tanks (Titan).
8. **Non-propulsive propellant uses:** fuel as bearing lubricant (F-1, H-1 FABU).

## Next retrieval targets (when fetch works)
- RS-25:
  - the ibiblio SSME Overview (JSC-19041?);
  - the Hopson FRR original slide (to settle 1,601 vs 1,615 R);
  - NTRS 20030005845 and 19860012108.
- F-1: the MSFC F-1 Engine Fact Sheet (1968) and the Rocketdyne R-3896-1 Engine Data volume.
- H-1: open NTRS 19650013470 and 19650013471. Confirm the engine identity and the turbopump numbers on the page.
- J-2: NTRS 20100027318 pages, the AEDC J-2 reports' schematic figures, and the Saturn IB News Reference (Scribd).
- J-2S: NTRS 19690072871 and 19690073042, and the AEDC-TR-70-150/-204/-38 PDFs.
- LR87: USAF Titan II technical orders, Aerojet LR87 reports, and the Gemini GLV engine documents (for the AJ-7 contrast).
