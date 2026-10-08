# DB-0 branch "taxonomy": liquid rocket propulsion architecture taxonomy

## 0. How to read this file (honesty first)

**Access limits this session.**
- WebFetch could not resolve any host (`getaddrinfo ENOTFOUND` for ntrs.nasa.gov, wikipedia.org and google.com).
- curl to every host was refused by the proxy (403).
- The shared WebSearch budget (200 per turn, across all branches) ran out after about 30 searches from this branch.

As a result:
- **No PDF was opened.** Every source in `sources.json` has `access: search_result_only` or `not_retrieved`. Each statement below that carries a source_id was read only in a search-engine summary of that page, and is at best equivalent to SECONDARY_CLAIM until someone opens the source.
- **No NTRS copyright field was viewed.** NTRS items are marked `RIGHTS_REVIEW_REQUIRED`, not `PUBLIC_DOMAIN_GOV`. US patents and US-government web pages are the only items marked public domain.
- **No figure number or page was verified.** Every schematic in `schematics.json` is `described_in_text` or `cited_by_other_source`.

**Tags used below.**
- `[S: SRC-…]`: the claim appeared in the search result for that source.
- `[BG]`: textbook or background knowledge from the model. It was **not verified this session** and must not go into a database as REPORTED. Where possible, the canonical source to check is named, e.g. `check SRC-HUZEL-1992`. Leave every `[BG]` example out of DB-0 until it is confirmed.
- `[INF]`: reasoning or classification by this branch.

**Chapter-level anchors.** These come from the brief, not from opening the books.
- SRC-SUTTON-RPE9:
  - ch. 6: liquid engine fundamentals, feed systems, cycles, pressurization.
  - ch. 8: thrust chambers, cooling, injectors.
  - ch. 10: turbopumps and gas supplies.
  - ch. 11: engine systems, controls, start and integration.
- SRC-NASA-SP125 and SRC-HUZEL-1992 (Huzel & Huang): engine systems, pressurization, turbopumps, thrust chambers. Chapter numbering was not verified.

## 1. Recommended taxonomy structure

The RocketForge LIQ-2 rule, "feed and cycle are separate", is correct. It should go one step further, because the names in common use ("expander bleed", "tap-off", "staged combustion", "open/closed") mix three independent facts about the turbine drive. The recommendation is to record these orthogonal axes per engine variant:

| Axis | Values |
|---|---|
| A. Feed (how propellant gets its pressure) | pressure-fed regulated; blowdown; self-pressurized; pump-fed (turbopump); pump-fed (electric); pump-fed (positive displacement); centrifugal/rotating; hybrid (pressure-fed + boost pump) |
| B1. Turbine drive-gas source (pump-fed with turbines only) | bipropellant gas generator; preburner (fuel-rich / ox-rich / both); main-chamber tap-off; coolant heated in jacket (expander); separate working fluid (H2O2 steam, monopropellant decomposition); solid-propellant gas generator; none (electric / PD with other drive) |
| B2. Turbine exhaust disposition | into main chamber ("closed" / "topping"); overboard duct; into nozzle (film / extension cooling); steering or vernier nozzles; heat exchanger then overboard |
| B3. Fraction of propellant through turbines | partial (one propellant, part flow); full-flow (all of both propellants) |
| C. Tank pressurization (vehicle/stage attribute) | stored gas (ambient / cold, heated / unheated); autogenous; GG or preburner products; chemical (MTI / Tridyne); self-pressurization |
| D. Thrust-chamber and nozzle thermal protection (several per engine, per zone) | regenerative (tube / channel-wall); film; transpiration; dump; radiation; ablative; heat sink |
| E. Injector element type | per SP-8089 classes |
| F. Turbomachinery arrangement | shafts, gearbox, boost pumps, pump/turbine types |
| G. Start and control | start energy source; igniter; throttle and mixture-ratio control effector |
| H. Thrust-chamber arrangement and propellant count | single / multi-chamber with common turbopump / clustered; aerospike; tripropellant; dual-fuel |

**Mapping of the named cycles onto B1/B2/B3** [INF]:

| Common name | B1 drive source | B2 turbine exhaust | B3 flow |
|---|---|---|---|
| Gas generator (open) | bipropellant GG | overboard / nozzle / steering | partial |
| Expander (closed, "topping") | heated coolant | main chamber | partial or full of one propellant |
| Expander bleed / open expander | heated coolant | overboard / nozzle | partial |
| Tap-off (combustion tap-off) | main chamber gas | overboard | partial |
| Staged combustion (fuel-rich) | fuel-rich preburner(s) | main chamber | partial |
| Staged combustion (ox-rich) | ox-rich preburner | main chamber | partial |
| Full-flow staged combustion | fuel-rich + ox-rich preburners | main chamber | full |
| H2O2 steam drive (A4, R-7, Redstone) | separate working fluid | overboard / HEX / pressurization | n/a (third fluid) |
| Electric pump | battery and motor | none | n/a |

Two consequences follow:
- **"Closed cycle" = B2 into the main chamber.** That covers closed expander, staged combustion and FFSC.
- **"Open cycle" = B2 dumped.** That covers GG, tap-off, expander bleed and H2O2 steam.

A pressure-fed engine has **no** B1, B2 or B3. That supports LIQ-2's `CYCLE_WITHOUT_PUMP_FEED`.

`engines.json`'s `cycle` enum (brief) can stay as is. Add `turbine_drive_source` and `turbine_exhaust_disposition` as optional companion fields so that variants such as Vulcain 2 or F-1 (GG with exhaust into the nozzle) and RD-0110 (GG with exhaust into steering nozzles) are not flattened into the same value as a GG with an overboard duct.

## 2. A. Feed systems

### A.1 Pressure-fed, regulated stored gas
- **Definition:** high-pressure inert gas (usually helium) is stepped down through regulators to keep tank pressure roughly constant [S: SRC-NTRS-SP8112 scope; detail BG, check SRC-SUTTON-RPE9 ch.6].
- **Apollo SM SPS (AJ10-137), N2O4/A-50:**
  - Helium passes through pressurizing valves into regulator assemblies. Each assembly has a primary and a secondary regulator in series (186±4 and 191±4 psig set points), then series-parallel quad check valves, with burst-disc relief valves [S: SRC-AEHS-RPE RPE09.31].
  - The engine is pressure-fed [S: SRC-WIKI-AJ10].
- **Shuttle OMS (AJ10-190):**
  - Helium bottle, solenoid valves, regulators, vapor-isolation valves, check valves and relief valves.
  - Engine valves are actuated by a separate GN2 system [S: SRC-NTRS-OMS-1974 (id attribution from summary), SRC-WIKI-OMS].
- **Astra Aether** upper-stage engine is pressure-fed [S: SRC-WIKI-ASTRA].
- **Other well-known examples [BG]:** Apollo LM descent and ascent engines, Agena secondary propulsion, most spacecraft bipropellant systems.

### A.2 Blowdown
- **Definition:** the tank is loaded with propellant plus a gas ullage and is not resupplied, so pressure decays as the ullage expands. Fast draining approaches adiabatic expansion and gives a larger pressure drop [S: SP-8112 search summary context; BG].
- Typical users are hydrazine monopropellant satellites [BG]. No specific liquid main engine was confirmed this session.
- **Distinguish from "pressure-fed":** blowdown is a *subset* of pressure-fed, without regulation. Store `pressure_fed_blowdown` only when a source says blowdown or unregulated.

### A.3 Self-pressurized (vapor-pressure)
- The propellant's own vapor pressure provides feed pressure. Typical cases are N2O, and also CO2 or propane cold-gas systems.
- Background references were found only for N2O monopropellant micro-propulsion (BUAA journal hit) [BG].
- No liquid bipropellant flight engine was confirmed this session. Amateur and university N2O/ethanol engines exist [BG]. Mark this category as **mostly small, experimental or amateur** until a primary source is found.
- Do not confuse with vehicle-level "self-pressurization by boil-off". SRC-WIKI-AUTOGENOUS and a NASA/Martin Marietta ET study (seen in results, not catalogued) treat that as a pressurization (C) topic.

### A.4 Positive-expulsion devices
These are feed sub-architectures of pressure-fed systems for zero-g propellant acquisition.

- **Elastomeric or Teflon bladder:**
  - Apollo SM and CM RCS tanks had a Teflon bladder with a diffuser tube; helium surrounded the bladder and collapsed it [S: SRC-AEHS-RPE RPE09.32].
  - A 1966 JPL-era report says Teflon bladders were the most widely used [S: SRC-NTRS-1966-BLADDER, attribution uncertain].
  - Ranger and Mariner used bladders [S: SRC-SAE-640792 abstract].
- **Metal diaphragm, rolling or collapsing:** elastomers are reactive with common propellants, which motivates metal designs; failure mode is cracking after partial collapse [S: SRC-PATENT-US4216881, SRC-PATENT-US4213545]. A Chinese common-shell tank uses two corrugated diaphragms [S: SRC-IAC11-CORRDIAPHRAGM].
- **Piston:** most efficient for high L/D tanks; uses dynamic seals [S: SRC-PATENT-US4216881]. Flight examples were not confirmed; [BG] Peacekeeper PBV / Minuteman PSRE? Unverified, do not record.
- **Metal bellows:** Gardner curved-convolution bellows in expulsion tanks [S: SRC-PATENT-US4213545].
- **Surface-tension PMD (screens, vanes, sponges):** no source captured this session. [BG] Shuttle OMS/RCS tanks used screen-type propellant acquisition devices; check SP-8112.

### A.5 Pump-fed, turbopump
This is the default for boosters; see section B. Note that **"pressure-fed with boost pumps"** is still pump-fed for taxonomy purposes. Tank pressure feeds a low-pressure boost pump, which feeds the main pump [INF].

### A.6 Pump-fed, electric motor
- **Rutherford (Rocket Lab):** brushless DC motors with lithium-polymer batteries drive the pumps. Flown from 2017/2018 [S: SRC-RKLB-BATTERY, SRC-RKLB-PAYLOAD2020].
- **Delphin (Astra Rocket 3, five per stage):** electric-pump-fed; developed in 2012 under the SALVO programme [S: SRC-WIKI-EPUMP, SRC-WIKI-ASTRA].
- As of Dec 2020 these were reported as the only two flown [S: SRC-WIKI-EPUMP]. Later engines, e.g. Chinese or European startups, were NOT_AUDITED.
- Historical electric-pump studies, e.g. 1960s NASA or Aerojet: NOT_AUDITED. The search budget ran out before this was searched.
- **Cycle field:** use `electric_pump`. Thermodynamically there is no turbine at all [INF]. Some literature calls this "electric pump cycle". Battery dead mass is the key trade.

### A.7 Pump-fed, positive-displacement
- **XCOR Aerospace piston pumps:**
  - LOX pumped at Lynx main-engine flow rates in 2012 [S: SRC-SPACEREF-XCOR-LOXPUMP].
  - Kerosene pumps demonstrated earlier; DARPA Phase II flight-type pump for an 1,830 lbf LOX/kerosene engine [S: SRC-SPACENEWS-XCOR-ULA summary].
  - LH2 piston pump tested for ULA [S: SRC-SPACENEWS-XCOR-ULA].
  - Never flown; company closed (2017, [BG]).
  - The pump drive is a "proprietary combined thermodynamic cycle" with no further public detail. Record B1 as `UNKNOWN`.
- Other PD pumps (Ventions, historical gear or vane pumps): NOT_AUDITED.

### A.8 Centrifugal / rotating-engine feed
- **Roton (Rotary Rocket Co., 1996–2001):**
  - LOX/kerosene engine with many small chambers on a rotating ring; propellant pumped by the centrifugal head of the rotation [S: SRC-WIKI-ROTARYROCKET, SRC-FLIGHTGLOBAL-ROTON, SRC-GLOBALSEC-ROTON].
  - Abandoned in June 1999 in favour of a Fastrac derivative [S: SRC-WIKI-ROTARYROCKET].
  - The 1999 hover vehicle flew on rotor-tip H2O2 rockets, not this engine [S: SRC-WIKI-ROTARYROCKET].
  - **Experimental / design-only; never hot-fired as a full engine** (not confirmed either way; mark UNKNOWN).

### A.9 Other feed concepts
- **"Bootstrap":** this is a *start* term (turbopump accelerates on its own drive gas), not a feed category. See G.
- **Gas-pressurized pistons / pump-boosters:** NOT_AUDITED.

## 3. B. Power cycles (pump-fed only)

### B.1 Gas generator (GG, open cycle)
- **Definition:** a separate small combustor burns a fraction of the propellants (usually fuel-rich) to drive the turbine. The turbine exhaust does not enter the main chamber [BG; check SRC-SUTTON-RPE9 ch.6 and ch.10, SRC-NTRS-SP8107 cycle figure (SCH-GENERIC-CYCLES-1)].
- **Examples confirmed this session:**
  - F-1 [S: SRC-WIKI-F1]
  - LR87-5 [S: SRC-WIKI-LR87]
  - RD-0110 and RD-0110R [S: SRC-WIKI-RD0110, SRC-WIKI-RD0110R]
  - Vulcain 2 [S: SRC-WIKI-VULCAIN]
  - LE-5, the original, before LE-5A [S: SRC-WIKI-LE5]
- **[BG] to confirm:** H-1, J-2, RS-27, Merlin 1, RS-68, J-2X, YF-20 family, Viking, RD-0110.

**GG exhaust disposition sub-variants (axis B2):**
1. **Overboard duct or exhaust stack** [BG]: H-1, Merlin 1C/1D (to confirm).
2. **Into nozzle-extension manifold, as film or extension coolant:**
   - F-1: turbine exhaust → heat exchanger → wrap-around manifold → double-wall nozzle extension from 10:1 to 16:1 [S: SRC-WIKI-F1, SRC-AEHS-RPE].
   - Vulcain 2: turbine exhaust re-injected into the lower nozzle as a film [S: SRC-WIKI-VULCAIN, SRC-PATENT-US6996973].
   - J-2X [BG].
3. **Steering or vernier nozzles:**
   - RD-0110: GG output to four swivelling steering nozzles giving pitch, yaw and roll [S: SRC-WIKI-RD0110, SRC-RSW-RD0110].
   - Atlas vernier and H-1 roll control via exhaust: [BG] **not confirmed**. Do not record.
4. **Via a heat exchanger for tank pressurization:**
   - LR87-5: oxidizer superheater in the GG exhaust [S: SRC-MILSTD-T2START].
   - F-1 heat exchanger in the turbine exhaust path [S: SRC-WIKI-F1].
   - J-2 heat exchanger in the turbine-drive gas circuit [S: SRC-PATENT-US7895823].

### B.2 Expander (closed, "topping" in older US usage)
- **Definition:** coolant (usually H2, sometimes CH4) heated in the regenerative jacket drives the turbine, then all of it goes to the injector. There is no combustor for the turbine. Thrust is limited by heat pickup (the square-cube law) [BG; SRC-SUTTON-RPE9 ch.6].
- **[BG] examples to confirm:** RL10 family (all variants), Vinci, YF-75D, RD-0146.
- RL10 "bootstrap" start uses the same heat path; see G.
- **"Topping cycle":** historical US term for cycles whose turbine exhaust goes to the chamber. Some older texts apply it to both closed expander and staged combustion [BG]. Record it as an alias at family level only when the source uses it.

### B.3 Expander bleed, open expander, cooling bleed

Three terms are often conflated. Proposed definitions [INF; partly supported]:

- **Expander bleed / open expander:** a *portion* of the heated coolant drives the turbine and is dumped overboard or into the nozzle. The rest goes to the injector [S: SRC-WIKI-LE5 summary text].
  - The higher turbine pressure ratio (dump to near ambient) allows higher chamber pressure and thrust than closed expander, at an Isp penalty.
  - LE-5A: coolant heated in nozzle and chamber.
  - LE-5B: chamber only [S: SRC-WIKI-LE5].
  - LE-9 is the "world's first large-thrust engine" using expander bleed [S: SRC-MHI-TR55-2], replacing LE-7A's staged combustion [S: SRC-JAXA-LE9TP].
  - JAXA describes expander bleed as a Japanese "open expander" variant [S: SRC-IAC17-LE9].
  - **Conclusion:** "open expander" ≈ "expander bleed" in current Japanese literature. Treat them as aliases of one cycle value, `expander_bleed`.
  - BE-3U is called "open expander" in one Wikipedia revision and "expander bleed" in another (CF-TAX-1). This is consistent with the alias view.
- **"Cooling bleed" or "chamber bleed":** used for LE-5B, where the bleed is taken from the *chamber* cooling circuit only [S: SRC-WIKI-LE5]. This is a sub-variant label, not a separate cycle. Record it as `turbine_drive_source = coolant (chamber jacket only)`.
- **Not to be confused with:**
  1. **"Bleed cycle"** used loosely for GG or tap-off.
  2. **Coolant dumped without driving any turbine.** That is dump cooling (D.4), not a cycle.
  3. **Tap-off** (B.6), where gas is bled from the *combustion* products, not the coolant.
- **Dual expander** (separate H2 and O2 expander loops): concept studies only [BG]. Mark `theoretical/experimental-only` pending source.
- **RL10 bleed:** some RL10 variants were studied or used as "expander bleed" [BG; unverified]. Do not assign without a Pratt & Whitney or Aerojet Rocketdyne primary source.

### B.4 Staged combustion, fuel-rich (closed)
- **Definition:** one or more fuel-rich preburners burn all or most of the fuel with a little oxidizer. The turbine exhaust is fed to the main injector [BG; SRC-SUTTON-RPE9 ch.6].
- **[BG] examples, all need primary confirmation:** RS-25 (two preburners), RD-0120, LE-7/LE-7A, CE-7.5 and its Indian successors.
- LE-7A as staged combustion is indirectly supported by SRC-JAXA-LE9TP.

### B.5 Staged combustion, oxidizer-rich (closed)
- **Russian term:** "ЖРД с дожиганием генераторного газа" ("with afterburning of generator gas"), i.e. staged combustion. "Закрытая схема" = closed scheme; "открытая схема" = open scheme [BG; native terms not searched this session, budget exhausted].
- **[BG] examples, all need primary confirmation:** NK-33/AJ26, RD-170/171/180/191, RD-0124, RD-253 (N2O4/UDMH), YF-100, BE-4, RD-120.
- RD-170 uses one preburner for four chambers [BG], which ties into multi-chamber arrangements (H.1).

### B.6 Full-flow staged combustion (FFSC)
- **Definition:** a fuel-rich and an oxidizer-rich preburner each drive their own turbopump. *All* of both propellants pass through a preburner and turbine, so the main chamber burns only gas-gas [S: SRC-WIKI-RD270, SRC-AFRL-IPD].
- **Real hardware, the complete list per sources:**
  1. RD-270, N2O4/UDMH, 1960–70, cancelled during testing [S: SRC-WIKI-RD270].
  2. IPD, LOX/LH2, about 250 klbf class, powerhead-only demonstrator; 100% power in 2006 [S: SRC-AFRL-IPD, SRC-SFN-IPD-2006, SRC-NTRS-IPD-WPB].
  3. Raptor, LOX/CH4, first flight 25 Jul 2019 on Starhopper [S: SRC-WIKI-RAPTOR].

### B.7 Tap-off (combustion tap-off, hot-gas tap-off)
- **Definition:** hot gas is tapped from the main combustion chamber, usually near the injector face or wall, to drive the turbine, then dumped. Open cycle. The turbine sees higher temperatures [S: SRC-WIKI-COMBTAPOFF].
- **Real hardware:**
  - J-2S, test-fired, never flown [S: SRC-WIKI-COMBTAPOFF, SRC-SECRETPROJ-J2DERIV].
  - BE-3 on New Shepard, flown from 2015; Blue Origin itself uses "tap-off" [S: SRC-BLUE-BE3-2013].
  - "Reaver" (Firefly Alpha) is widely reported as tap-off [BG; **not verified**; do not record without Firefly primary].
- **Tap-off vs combustion tap-off vs staged combustion:** "tap-off" and "combustion tap-off" are the same thing. Staged combustion differs because a *separate* preburner feeds the turbine and the turbine exhaust *enters* the main chamber [INF].
- **Tap-off vs GG:** both are open cycles. The drive-gas source differs: the main chamber versus a separate burner.

### B.8 Separate turbine working fluid (third-fluid drive)
- **H2O2 decomposed catalytically to steam:**
  - R-7 RD-107/RD-108: solid F-30-P-G catalyst; H2O2 pumps driven off the main turbopump; GG exhaust heats N2 for tank pressurization [S: SRC-WIKI-RD107; SRC-MM-R7KIT Tier E for the start sequence].
  - RD-214 [S: SRC-WIKI-RD214].
  - "As was typical by all the descendants of the V-2 rocket technology" [S: SRC-WIKI-RD107 summary].
  - **[BG] to confirm:** A4/V-2 (T-Stoff 80% H2O2 with Z-Stoff permanganate), Redstone A-7, Navaho, Black Arrow Gamma (whose main propellant was HTP, so not a "separate" fluid there), Soyuz third stage? Not confirmed: RD-0110 is LOX/kerosene GG per SRC-WIKI-RD0110, so the brief's suggestion of an HTP Soyuz third stage is **contradicted**.
- **Monopropellant (hydrazine) GG turbine drive:** NOT_AUDITED. [BG] Agena XLR81 used a bipropellant GG, so the brief's suggestion should not be assumed.
- **Solid-propellant GG as continuous turbine drive:** NOT_AUDITED. Solid cartridges as *start* devices are confirmed; see G.
- **Classification:** use `separate_turbine_working_fluid`. It is open, since steam exhaust goes overboard or to a heat exchanger.

### B.9 Electric pump
See A.6. Recommendation: leave the brief's `cycle` field as `electric_pump` and `feed` as `pump_fed_electric`. Do not invent a turbine axis.

### B.10 "Pressure-fed cycle"
This is a misnomer. LIQ-2 is right: cycle = none. The brief's enum value `none_pressure_fed` should be read as "no cycle".

## 4. C. Tank pressurization (vehicle/stage attribute; record on the stage, not the engine)

| Category | Confirmed examples |
|---|---|
| Stored He, ambient, regulated | Apollo SPS [S: SRC-AEHS-RPE]; Shuttle OMS [S: SRC-NTRS-OMS-1974] |
| Stored He, cryogenic bottles submerged in cryogen | Falcon 9 COPVs inside the LOX tanks of both stages; also reported for Antares and Soyuz-2.1b/2.1v [S: SRC-SPACEFLIGHT101-AMOS6]. S-IVB He spheres inside the LH2 tank [S: SRC-STEVEBLOG-SATHE, Tier E]. S-IC He bottles in the LOX tank pressurizing the fuel tank [S: SRC-APOLLOMANIACS-SV, Tier E] |
| Stored He heated in an engine heat exchanger | S-IVB: He warmed in the J-2 heat exchanger, then to the LOX tank [S: SRC-STEVEBLOG-SATHE]; J-2X same concept [S: SRC-NASA-J2XBLOG-HEX] |
| Autogenous GOX from an engine heat exchanger | J-2 heat exchanger heats LOX for LOX-tank pressurization [S: SRC-PATENT-US7895823]; SSME GOX heat exchanger at the HPOTP turbine exit feeds tank pressurization and POGO [S: SRC-PATENT-US5918460]; S-IC LOX tank via engine-heated LOX [S: SRC-APOLLOMANIACS-SV, Tier E] |
| Autogenous GH2 tapped from the engine | S-IVB LH2 tank [S: SRC-STEVEBLOG-SATHE]; Centaur GH2 bled from the RL10s during burns [S: SRC-ULA-TITANCENTAUR]; Shuttle ET (listed as an autogenous user) [S: SRC-WIKI-AUTOGENOUS] |
| Autogenous CH4/O2 | Starship / Super Heavy (Tier E only) [S: SRC-MANIFOLD-STARSHIP]; time-varying, possibly reverted to helium [S: SRC-WCCFTECH-SN10] (CF-TAX-8) |
| Warm gas from GG products | LR87-5 Titan II fuel tank pressurized with fuel-rich GG exhaust [S: SRC-WIKI-LR87] |
| Heated (vaporized) propellant via GG-exhaust heat exchanger | Titan II oxidizer tank: N2O4 vaporized in the "superheater" coils in the GG exhaust [S: SRC-WIKI-LR87, SRC-MILSTD-T2START] |
| Inert gas heated by GG exhaust | R-7 (RD-107/108): N2 heated in a heat exchanger in the GG exhaust [S: SRC-WIKI-RD107] |
| Chemical / main-tank injection (MTI) | NOT_AUDITED. SP-8112 covers pressurization broadly; MTI content not confirmed. [BG] Experimental (1960s Air Force/NASA tests) |
| Tridyne (inert + H2 + O2, catalytically heated) | Patents and concepts only [S: SRC-PATENT-US10495027, SRC-PATENT-US4804520]. **Flight heritage not confirmed**; treat as experimental |
| Self-pressurization (boil-off) | Shuttle ET study concept (not catalogued); N2O systems [BG] |

Several of these confusingly carry the same word "autogenous":
- "Autogenous" in Wikipedia's sense means the propellant itself is heated and returned to its own tank [S: SRC-WIKI-AUTOGENOUS].
- Titan II's fuel tank pressurized with GG *products* is called "autogenous" in SRC-WIKI-LR87. Strictly that is "GG-gas pressurization".

**Recommendation:** split `autogenous_propellant_vapor` from `gg_product_gas` [INF]. Also, "autogenous pressurization" (vehicle) is not a cycle, and should never be stored in the engine `cycle` field.

## 5. D. Cooling / thermal protection
Record these per zone (chamber, throat, nozzle, nozzle extension), because most engines mix them.

- **Regenerative.**
  - Tube-wall: F-1 tubular regen to 10:1 [S: SRC-WIKI-F1]; Vulcain 2 nozzle of brazed tubes (248 tubes is a Tier E dataset figure, do not use) [S: SRC-WIKI-VULCAIN].
  - [BG] H-1, RL10, J-2 tube-wall; SSME MCC, Vulcain and LE-7 milled-channel liner with electroformed close-out; Russian brazed "corrugated / spot-connected shell" construction; additive-manufactured channels (Rutherford chamber is printed [S: SRC-RKLB-BATTERY]); LE-9 HIP-brazed chamber [S: SRC-IAC17-LE9].
- **Film / boundary layer.** F-1 extension cooled by turbine exhaust [S: SRC-WIKI-F1]; Vulcain 2 turbine-exhaust film [S: SRC-WIKI-VULCAIN]. Fuel-rich outer injector rows: [BG].
- **Transpiration.** [BG] Porous Rigimesh injector faces (SSME, J-2) are often cited. *Not confirmed* this session.
- **Dump cooling.**
  - Vulcain 2+ nozzle-extension demonstrator: dump-cooled laser-welded sandwich wall [S: SRC-IAC10-V2PNE].
  - Vulcain 2.1 hydrogen-cooled extension [S: SRC-ESA-V21NE, SRC-IAC19-SWAN].
  - Whether Vulcain 2.1 retains turbine-gas film injection: UNKNOWN.
- **Radiation-cooled extensions.** [BG] RL10B-2 (columbium), Merlin Vacuum, AJ10 variants, R-4D. Not confirmed this session.
- **Ablative.** [BG] RS-68, AJ10 (SPS, OMS), LMDE. Not confirmed this session.
- **Heat sink:** test hardware [BG].

## 6. E. Injectors
- Element-class taxonomy (SP-8089, not retrieved) [BG]:
  - Non-impinging coaxial: shear coax for LOX/H2 (J-2, RS-25, RL10) and swirl coax (Russian practice).
  - Impinging: like doublet, unlike doublet, triplet, pentad / quadlet.
  - Showerhead.
  - Pintle (moveable or fixed sleeve): TRW LMDE, TR-201, Merlin.
  - Splash plate.
  - Concentric annular.
  - A4 "18-pot" pre-chamber burner-cup head.
- **Confirmed this session:**
  - LE-5B-2 injector with 306 coaxial elements vs 180 on LE-5B [S: SRC-WIKI-LE5].
  - LE-9 varied element lengths plus a resonator for stability [S: SRC-MHI-TR55-2].
- Acoustic cavities and baffles: only the LE-9 resonator is confirmed.

## 7. F. Turbomachinery arrangements
**Confirmed:**
- Single turbopump feeding multiple chambers: RD-0110 (4 chambers) [S: SRC-WIKI-RD0110]; RD-107/108 (4 chambers, plus verniers) [S: SRC-WIKI-RD107].
- R-7 single-axle unit: turbine, ox pump, fuel pump, plus a small H2O2 pump drive [S: SRC-WIKI-RD107].
- Separate fuel and ox turbopumps driven from one GG: F-1 (Wikipedia says one turbine drove "separate fuel and oxygen pumps", which reads as a single shaft) [S: SRC-WIKI-F1].
- FFSC uses two turbopumps, one per preburner [S: SRC-AFRL-IPD].
- LE-9 uses open impellers [S: SRC-IAC17-LE9].
- Boost pumps: SP-8107 pp.53–55 [S: SRC-PATENT-US5197851 citing SRC-NTRS-SP8107].

**[BG] to confirm:**
- Geared turbopumps: H-1, MA-5, RS-27, LR87.
- RS-25: LPFTP, LPOTP, HPFTP (3-stage), HPOTP.
- RD-170: boost pumps driven by a gas turbine (ox) and a hydraulic turbine (fuel).
- J-2: axial fuel pump.
- M-1: axial H2 pump.
- Impulse and reaction turbines; partial admission.

## 8. G. Start and control
- **Solid start cartridge:** LR87 / Titan II. The cartridge burns about 1 s at about 2000 psia into the turbine, then the GG "bootstraps" [S: SRC-MILSTD-T2START, SRC-WIKI-LR87].
- **Gravity / tank-head start to intermediate thrust, then steam drive:** R-7 [S: SRC-MM-R7KIT, Tier E; pyrotechnic ignition per same].
- **Electro-mechanical valves, no pneumatics:** LE-9 [S: SRC-IAC16-LE9, SRC-IAC18-LE9].
- **Closed-loop thrust and mixture-ratio control:** LE-9 [S: IAC-19 52093 summary; not catalogued separately].
- **Wide throttling:** BE-3, 110,000 to 20,000 lbf [S: SRC-BLUE-BE3-2013]. J-2S added throttling and variable mixture ratio [S: SRC-WIKI-COMBTAPOFF via summary].
- **Electric start:** Rutherford (inherent).
- **[BG] to confirm:**
  - RL10 bootstrap / tank-head start.
  - J-2 GH2 start tank.
  - RS-68 helium spin start (unverified).
  - TEA-TEB hypergolic slugs (F-1, Merlin).
  - Augmented spark igniter (J-2, RS-25).
  - RS-25 throttling via the preburner oxidizer valves.
  - RL10 turbine bypass valve.
  - J-2 PU valve.

## 9. H. Other architectures
| Category | Status | Examples |
|---|---|---|
| Multi-chamber, common turbopump | real hardware | RD-0110, RD-107/108 [S]; RD-170, YF-21, RD-8 [BG] |
| Clustered thrusters on one engine | real hardware | Stoke Andromeda [BG, not confirmed] |
| Rotating engine (centrifugal feed) | design / experimental only | Roton [S] |
| Aerospike | test hardware only | Roton design was a spinning aerospike [S: SRC-WIKI-ROTARYROCKET]; XRS-2200 linear aerospike [BG] |
| Tripropellant | ground-test only / studies | RD-701, RD-0750, Li/F2/H2 [BG; all NOT_AUDITED] |
| Dual-fuel / dual-mode | study | [BG] |
| Steering engines and GG-exhaust steering | real hardware | RD-0110 steering nozzles; RD-0110R gimballed 4-nozzle steering engine [S] |
| Electric pump | real hardware | Rutherford, Delphin [S] |
| Piston (PD) pump | test hardware | XCOR [S] |

## 10. Look-alike terms that are not equivalent (summary)
1. **"Open expander" vs "expander bleed" vs "cooling bleed":**
   - The first two are aliases [S: SRC-IAC17-LE9 framing].
   - "Cooling / chamber bleed" names *where* the drive coolant is heated (LE-5B chamber-only). It is not a different cycle.
   - Dump cooling drives no turbine.
2. **Tap-off vs combustion tap-off vs hot-gas tap-off:** all the same. Staged combustion differs in having a separate preburner and a closed turbine exhaust.
3. **"Closed cycle" vs "staged combustion":** closed also includes closed expander. Not every closed cycle is staged combustion.
4. **GG vs "bleed cycle":** "bleed" is ambiguous; avoid it as a value.
5. **Pressure-fed vs blowdown:** blowdown ⊂ pressure-fed.
6. **Autogenous pressurization (vehicle) vs any cycle:** different object (stage vs engine). Also split propellant-vapor autogenous from GG-product pressurization (Titan II naming).
7. **"Topping cycle"** is a historical US umbrella term; do not map it to a single value without context.
8. **Electric pump-fed vs pressure-fed:** an electric pump is pump-fed (high pump Δp, low tank pressure).
9. **"Bootstrap" (start method) vs "booster pump"** (turbomachinery) vs "booster" (role).

## 11. Public-domain schematic hunt (status)
No schematic page or figure was opened this session, because fetching was blocked. Of the items requested by the brief, these are the candidate locations, all **unverified**:

| Engine / system | Candidate source | Status |
|---|---|---|
| Generic cycles | SP-8107 cycle figure (via SRC-NATO-ENAVT150-05) | cited_by_other_source |
| J-2S | NTRS "J-2S Improvement Study, System Description" (referenced in SRC-SECRETPROJ-J2DERIV) | id not seen |
| IPD | NTRS 20040084662 / 20040129712 / 20060004818 / 20050041816 (seen as IPD-related results) | contents unknown |
| Apollo SPS | SRC-IBIBLIO-APOLLO9SPS; Apollo Operations Handbook SPS PDF (history.nasa.gov path quoted in a forum post) | unverified |
| Shuttle OMS | SRC-NTRS-OMS-1974 | unverified |
| SSME | Patent SRC-PATENT-US5918460 drawings (likely an SSME schematic) | unverified |
| F-1 / S-IC | NTRS 19660010358 (appeared in the S-IC search; title not seen) | unverified |
| S-IV / S-IVB | NTRS 19650013467 (S-IV LH2 storage pressurization) | low relevance |

- **Not searched (budget exhausted):** RL10, J-2, H-1, RS-68, LMDE, Titan LR87/LR91 schematics, A4, RD-170/180 (AIAA), NK-33/AJ26, Vulcain (ESA), LE-7, LE-5B (JAXA), RD-0120.
- **Merlin:** no public schematic is expected [BG].
- **Rights:** none confirmed. Patents are public domain as text. USPTO drawings are generally reproducible, but check the third-party content inside them.

## 12. Gaps and next steps (priority order)
1. Re-run with working WebFetch. Open the NTRS citation pages for SP-8107, SP-8112, SP-125, SP-8089 and SP-8087 to record the copyright field and figure numbers. Then confirm every `[BG]` example in sections 3–9.
2. Russian-language search: "схема ЖРД с дожиганием", "газогенератор на перекиси водорода", "бустерный насос гидротурбина РД-170".
3. Firefly Reaver cycle; Stoke Andromeda; RL10 expander-bleed claims; RS-68 start method; Atlas MA-5 / H-1 exhaust use for roll.
4. Flight heritage of MTI, Tridyne and monoprop-GG turbine drives. All are currently NOT_AUDITED or experimental-only.
5. Historical electric-pump and PD-pump studies (1960s NASA/AF).

## 13. Recommended anchor engines from this branch (for topology diversity)

| Engine | Why |
|---|---|
| J-2S | Best-documented tap-off; NASA reports exist |
| IPD | Public-funded FFSC with NTRS papers |
| LE-9 | Expander-bleed booster with IAC and JAXA papers |
| RD-0110 | GG exhaust to steering nozzles, multi-chamber single turbopump |
| LR87-5 | Solid-cartridge start, GG-product and vaporized-oxidizer pressurization |
| F-1 | GG exhaust to nozzle-extension film, heat exchanger in exhaust |
| Rutherford | Electric pump |
| Apollo SPS AJ10-137 | Regulated pressure-fed, redundant regulators |
| R-7 RD-107/108 | H2O2 steam drive, multi-chamber with verniers |
