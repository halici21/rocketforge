# DB-0 — Liquid rocket engine architecture taxonomy

Research document, not a specification. It proposes how a future RocketForge
engine database should classify architectures, and it records the evidence that
each category is real hardware. Nothing here changes LIQ-2's accepted
`feed`/`cycle` enumeration. It is the input DB-1 will use to decide whether that
enumeration needs to grow.

## 0. Evidence tags used in this document

DB-0 ran without document access (see
[DB0_RESEARCH_OVERVIEW.md §3](DB0_RESEARCH_OVERVIEW.md#3-how-the-research-was-actually-done)),
so every claim carries one of these tags:

| Tag | Meaning |
| --- | --- |
| `[S: SRC-…]` | Seen in a search-result summary of that source (registry: [SOURCE_REGISTRY.md](SOURCE_REGISTRY.md)). At best a secondary claim until someone opens the document. |
| `[BG]` | Textbook/background knowledge. Not verified this session. It may justify a category and name a verification target, but it never becomes a REPORTED value. |
| `[INF]` | Classification reasoning by DB-0. |

Chapter anchors for the textbook definitions are given at chapter level only:
Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed. (2017), ch. 6 (feed
systems, cycles, pressurization), ch. 8 (thrust chambers, injectors, cooling),
ch. 10 (turbopumps), ch. 11 (engine systems, control, start); Huzel & Huang,
NASA SP-125 (1967/1971) and its 1992 AIAA revision. Neither book was opened
during DB-0. Page-level locators are DB-1 work.

## 1. The central recommendation: classify by orthogonal axes, not by one label

LIQ-2 already separates **feed** from **cycle** and refuses a cycle on a
pressure-fed engine (`CYCLE_WITHOUT_PUMP_FEED`). DB-0 confirms that rule and
finds that it should be pushed further. The names in common use ("expander
bleed", "tap-off", "staged combustion", "open/closed", "autogenous") each mix
up to three independent facts about how the turbine is driven. Real engines
then differ inside one name: a gas-generator engine may dump its turbine gas
overboard (H-1, [BG]), into the nozzle extension (F-1, Vulcain 2), or through
steering nozzles (RD-0110). A single `cycle` value cannot tell these apart.

Proposed axes, recorded **per engine variant** (or per configuration where a
block changes them):

| Axis | What it answers | Values (proposal) |
| --- | --- | --- |
| A. Feed | How does propellant get its pressure? | `pressure_fed_regulated`, `pressure_fed_blowdown`, `pressure_fed_unspecified`, `self_pressurized`, `pump_fed_turbopump`, `pump_fed_electric`, `pump_fed_positive_displacement`, `rotating_centrifugal`, `UNKNOWN` |
| B1. Turbine drive source | Where does the turbine gas come from? (pump-fed with turbines only) | `bipropellant_gas_generator`, `preburner_fuel_rich`, `preburner_ox_rich`, `preburners_both`, `main_chamber_tap_off`, `heated_coolant_expander`, `separate_working_fluid` (H2O2 steam, monopropellant), `solid_gas_generator`, `none` |
| B2. Turbine exhaust disposition | Where does the turbine gas go? Repeatable: one engine may have several. | `main_chamber` ("closed"), `overboard_duct`, `nozzle_film_or_extension`, `steering_or_vernier_nozzles`, `heat_exchanger_then_overboard`, `tank_pressurization` |
| B3. Turbine flow fraction | Does all propellant pass a turbine? | `partial`, `full_flow` |
| C. Tank pressurization | A **stage/vehicle** attribute, never the engine `cycle`. | see §4 |
| D. Thermal protection | Per zone (chamber, throat, nozzle, extension). | see §5 |
| E. Injector | Element class per SP-8089. | see §6 |
| F. Turbomachinery arrangement | Shafts, gears, boost pumps, pump/turbine types. | see §7 |
| G. Start and control | Start energy source, igniter, throttle and mixture-ratio effectors. | see §8 |
| H. Chamber arrangement and propellant count | single / multi-chamber with common turbopump / clustered / aerospike / tripropellant | see §9 |

The named cycles become **derived labels** over B1–B3, which keeps every
historical name usable as a search alias without making it the data:

| Common name | B1 drive source | B2 turbine exhaust | B3 |
| --- | --- | --- | --- |
| Gas generator ("open") | bipropellant GG | overboard / nozzle / steering / HEX | partial |
| Expander (closed; older US "topping") | heated coolant | main chamber | partial or full flow of one propellant |
| Expander bleed = open expander | heated coolant | overboard / nozzle | partial |
| Tap-off (combustion tap-off) | main chamber gas | overboard | partial |
| Staged combustion, fuel-rich | fuel-rich preburner(s) | main chamber | partial |
| Staged combustion, ox-rich | ox-rich preburner(s) | main chamber | partial |
| Full-flow staged combustion | fuel-rich + ox-rich preburners | main chamber | full |
| H2O2 steam drive (A4, R-7, Redstone) | separate working fluid | overboard / HEX | n/a (third fluid) |
| Electric pump | battery + motor (no turbine) | — | — |
| Pressure-fed | — (no cycle) | — | — |

Consequences [INF]:
- **"Closed cycle" = B2 contains `main_chamber`.** That is closed expander,
  staged combustion and FFSC. Not every closed cycle is staged combustion.
- **"Open cycle" = turbine gas dumped.** That is GG, tap-off, expander bleed
  and third-fluid drives.
- A pressure-fed engine has no B1, B2 or B3. Its "pressure-fed cycle" label is
  a misnomer.

## 2. A — Feed architecture

### A.1 Pressure-fed, regulated stored gas
- **Definition.** A high-pressure inert gas, usually helium, is regulated down
  to an almost constant tank pressure [BG; Sutton ch. 6, Table 6-3; RocketForge
  SYS-4 implements the Sutton §6.5 mass relations].
- **Hardware examples:**
  - Apollo SM SPS (AJ10-137): helium regulator assemblies with primary and
    secondary regulators in series (186 ± 4 and 191 ± 4 psig set points), quad
    check valves and burst-disc relief valves [S: SRC-AEHS-RPE, Tier D].
  - Shuttle OMS (AJ10-190): helium bottle, regulators, check and relief
    valves. Engine valves are actuated by a separate GN2 system [S:
    SRC-NTRS-OMS-1974, attribution from summary].
  - Astra Aether upper-stage engine [S: SRC-WIKI-ASTRA-ROCKET].
- **Boundary finding.** In every pressure-fed case DB-0 saw, the pressurant,
  regulators and check valves belong to the **spacecraft or stage**, not the
  engine (LM descent stage supercritical helium; Orion crew-module helium)
  [S: spacecraft branch, see ANCHOR_ENGINE_CORPUS.md]. A database that stores
  "regulated" on the engine record is storing an installation fact.

### A.2 Blowdown
- **Definition.** The tank holds propellant plus a gas ullage that is not
  replenished, so pressure (and thrust) decay as the ullage expands [BG; Sutton
  §6.4: "gas temperatures, pressures and the resulting thrust all steadily
  decrease", quoted in SYS-4].
- Blowdown is a **subset** of pressure-fed. Store `pressure_fed_blowdown` only
  when a source says blowdown or unregulated.
- Typical users are hydrazine monopropellant spacecraft [BG]. No liquid
  **engine-level** blowdown record was confirmed in DB-0. Blowdown is almost
  always a spacecraft-system mode that a given thruster can be run in, which is
  another argument for keeping feed on the installation.

### A.3 Self-pressurized (vapour pressure)
- The propellant's own vapour pressure feeds it (N2O, also CO2 or propane cold
  gas) [BG].
- No flight bipropellant **liquid** main engine was confirmed. Mark the
  category **small / experimental / amateur** until a primary source is found.
- Do not confuse with vehicle-level "self-pressurization" by boil-off, which
  is a §4 tank-pressurization topic.

### A.4 Positive-expulsion and propellant-management devices (sub-architectures of pressure-fed)
These map to RocketForge SYS-3 `ManagementMode` (`DIAPHRAGM`, `BLADDER`,
`PISTON`, `BELLOWS`, `SURFACE_TENSION`), which already has the right shape.
- **Bladder:** Apollo SM and CM RCS tanks used Teflon bladders around a
  diffuser tube, collapsed by surrounding helium [S: SRC-AEHS-RPE]; Ranger and
  Mariner used bladders [S: SRC-SAE-640792].
- **Metal diaphragm:** elastomer reactivity motivated metal designs; failure
  mode is cracking after partial collapse [S: SRC-PATENT-US4216881,
  SRC-PATENT-US4213545]. A Chinese common-shell tank uses two corrugated
  diaphragms [S: SRC-IAC11-CORRDIAPHRAGM].
- **Piston:** most efficient for high L/D tanks [S: SRC-PATENT-US4216881].
  Flight examples not confirmed.
- **Bellows:** curved-convolution metal bellows [S: SRC-PATENT-US4213545].
- **Surface-tension PMD (screens, vanes, sponges):** [BG] Shuttle OMS/RCS
  tanks. Not confirmed this session.

All of these are **tank/installation** hardware. None is engine-owned.

### A.5 Pump-fed, turbopump
The default for boosters and large upper stages. "Pressure-fed with a boost
pump" is still pump-fed [INF].

### A.6 Pump-fed, electric motor
- **Rutherford (Rocket Lab, NZ/US):** brushless DC motors on lithium-polymer
  batteries drive the pumps; flown since 2017 [S: SRC-RKLB-BATTERY,
  SRC-RKLB-PAYLOAD-INCREASE].
- **Delphin (Astra Rocket 3):** electric-pump-fed [S: SRC-WIKI-EPUMP,
  SRC-WIKI-ASTRA-ROCKET].
- As of December 2020 these two were reported as the only flown electric-pump
  engines [S: SRC-WIKI-EPUMP]. Later engines are NOT_AUDITED.
- Recommended encoding: `feed = pump_fed_electric`, `cycle = electric_pump`,
  B1 = `none`. Do not invent a turbine. The energy store (battery mass and
  energy, motor power) is a new subsystem that no other architecture has.

### A.7 Pump-fed, positive displacement
- **XCOR piston pumps:** LOX pumped at Lynx main-engine flow rates (2012) [S:
  SRC-SPACEREF-XCOR-LOXPUMP]; kerosene pumps earlier; an LH2 piston pump tested
  for ULA [S: SRC-SPACENEWS-XCOR-ULA]. Never flown. The pump drive is described
  only as a "proprietary combined thermodynamic cycle", so its drive source is
  `UNKNOWN`.
- Status: **test hardware**, not flight.

### A.8 Rotating / centrifugal feed
- **Roton (Rotary Rocket Co.):** a ring of small chambers rotated so that
  centrifugal head pumps the propellant [S: SRC-WIKI-ROTARYROCKET,
  SRC-FLIGHTGLOBAL-ROTON]. Abandoned in 1999 for a Fastrac derivative. The 1999
  hover vehicle flew on rotor-tip H2O2 rockets, not this engine.
- Status: **design / experimental only**. Whether a full engine was hot-fired
  is UNKNOWN.

### A.9 Terms that look like feed categories but are not
- **"Bootstrap"** is a start method (§8), not a feed type.
- **"Booster pump"** is turbomachinery (§7). **"Booster"** is a vehicle role.

## 3. B — Power cycles (pump-fed only)

### B.1 Gas generator (open)
- **Definition.** A separate small combustor burns a fraction of the
  propellants, usually fuel-rich, to drive the turbine. The turbine exhaust
  does not enter the main chamber [BG; Sutton ch. 6, ch. 10; SP-8107 cycle
  figure, see FLOW_SCHEMATIC_INDEX.md].
- **Examples with search evidence:** F-1 [S: SRC-WIKI-F1], LR87-5 [S:
  SRC-WIKI-LR87], RD-0110 [S: SRC-WIKI-RD0110], Vulcain 2 [S:
  SRC-WIKI-VULCAIN], LE-5 (original) [S: SRC-WIKI-LE5], J-2 and J-2X (NTRS
  papers per the us_hist branch), RS-68A, Merlin 1D (Tier D only — SpaceX
  publishes no cycle wording), YF-77, YF-75, CE-20, Vikas, KRE-075 (see master
  list for per-engine evidence).
- **Exhaust-disposition sub-variants (axis B2), the reason one label fails:**
  1. Overboard duct or stack: [BG] H-1, Merlin 1C/1D (to confirm).
  2. Into the nozzle extension as film or extension coolant: F-1 turbine
     exhaust → heat exchanger → wrap-around manifold → double-wall extension
     from ε 10 to 16 [S: SRC-WIKI-F1, SRC-AEHS-RPE]; Vulcain 2 turbine exhaust
     re-injected into the nozzle [S: SRC-ESA-A5ECA-NEWELEM (Tier A, summary),
     SRC-PATENT-US6996973]; J-2X [BG].
  3. Steering or vernier nozzles: RD-0110 GG output to four swivelling
     steering nozzles [S: SRC-WIKI-RD0110, SRC-RSW-RD0110]. Atlas vernier and
     H-1 roll control by turbine exhaust: [BG], **not confirmed**, not recorded.
  4. Through a heat exchanger for tank pressurization: LR87-5 oxidizer
     superheater in the GG exhaust [S: SRC-MILSTD-T2START]; F-1 heat exchanger
     [S: SRC-WIKI-F1]; J-2 heat exchanger [S: SRC-PATENT-US7895823].

### B.2 Expander (closed)
- **Definition.** Coolant (usually H2, sometimes CH4) heated in the
  regenerative jacket drives the turbine, then all of it is injected. There is
  no turbine combustor. Heat pickup limits thrust (the square-cube argument)
  [BG; Sutton ch. 6].
- **Examples:** RL10 family [BG; NTRS RL10 papers seen as URLs only]; Vinci
  ("expander cycle, no gas generator", ESA [S, Tier A summary]); YF-75D (closed
  expander, asia branch [S]); MR10 (ex-M10, Avio, LOX/methane closed expander
  derived from KBKhA RD-0146 [S, europe branch]); RD-0146 [BG].
- **"Topping cycle"** is a historical US umbrella term applied to cycles whose
  turbine exhaust enters the chamber. Some older texts use it for both closed
  expander and staged combustion [BG]. Keep it as an alias at family level, and
  only where a source uses it.

### B.3 Expander bleed (= open expander) and "chamber bleed"
- **Definition.** Part of the heated coolant drives the turbine and is dumped;
  the rest is injected. The larger turbine pressure ratio buys chamber pressure
  and thrust at an Isp penalty [S: SRC-WIKI-LE5 summary; BG].
- **Examples:**
  - LE-5A: coolant heated in nozzle and chamber; LE-5B: chamber only [S:
    SRC-WIKI-LE5].
  - LE-9 (H3 first stage): "world's first large-thrust engine" using expander
    bleed, replacing LE-7A's staged combustion [S: SRC-MHI-TR55-2,
    SRC-IHI-GIHO-LE9-TP].
  - BE-3U: Blue Origin calls it "open expander" [S: Blue Origin page via the
    commercial branch].
  - BE-7: Blue Origin calls it "dual-expander" [S: Blue Origin page]. The
    sub-architecture behind that word was not resolved.
- **Alias resolution.** JAXA presents expander bleed as its "open expander"
  variant [S: SRC-IAC-LE9-2017]. DB-0 therefore treats **open expander ≡
  expander bleed** (one value, two aliases). The Wikipedia disagreement on
  BE-3U's label is consistent with that (conflict CF-TAXONOMY-1).
- **"Chamber bleed" / "cooling bleed"** (LE-5B) says **where** the drive
  coolant is heated (chamber jacket only). It is a sub-variant attribute, not a
  third cycle.
- **Not the same as:** dump cooling (coolant dumped without driving a turbine,
  §5); tap-off (gas from combustion products, B.5); the loose phrase "bleed
  cycle", sometimes used for GG. Avoid "bleed cycle" as a value.

### B.4 Staged combustion, fuel-rich (closed)
- **Definition.** One or more fuel-rich preburners burn most of the fuel with
  a little oxidizer; the turbine exhaust goes to the main injector [BG].
- **Examples:** RS-25/SSME (two preburners) [BG; NTRS SSME docs not opened];
  RD-0120 [S, ussr branch]; LE-7 and LE-7A (fuel-rich staged combustion) [S:
  asia branch, JAXA/MHI summaries]; CE-7.5 [BG/secondary].

### B.5 Staged combustion, oxidizer-rich (closed)
- **Russian terminology.** "ЖРД с дожиганием (генераторного газа)" — engine
  "with afterburning of the generator gas" — is the Russian term for staged
  combustion; "закрытая схема" (closed scheme) and "открытая схема" (open
  scheme) parallel the English open/closed [BG; to verify against a Russian
  textbook]. A machine translation of "дожигание" as "afterburning" must not be
  read as an afterburner in the aircraft sense.
- **Examples:** RD-180 ("LOx rich, closed cycle, staged combustion", ULA-hosted
  paper title and summary [S]); RD-170/171/171M, RD-191/181, RD-0124, RD-253 /
  RD-275 (N2O4/UDMH), NK-9/15/33 [S, ussr branch, mostly secondary]; YF-100,
  YF-115 [S, asia branch]; BE-4 [S: Blue Origin page]; Archimedes [S: Rocket
  Lab page]; RFA Helix and Ursa Major Hadley [BG/unverified].
- **Preburner count is engine-specific and disputed** (RD-170: one versus two
  preburners is unresolved in DB-0; see CONFLICT_LEDGER.md). The schema must
  allow 1..n preburners per engine and per side.

### B.6 Full-flow staged combustion (FFSC)
- **Definition.** A fuel-rich and an oxidizer-rich preburner each drive their
  own turbopump. All of both propellants pass a preburner and turbine; the main
  chamber burns gas with gas [S: SRC-WIKI-RD270, SRC-AF-IPD-2006].
- **All real hardware found:**
  1. RD-270 (N2O4/UDMH, 1960s–70s, ground-tested, cancelled) [S: SRC-WIKI-RD270].
  2. Integrated Powerhead Demonstrator (LOX/LH2, powerhead only, reached
     100% power in 2006) [S: SRC-AF-IPD-2006, SRC-SFN-IPD-2006].
  3. Raptor (LOX/CH4, first flight 2019). SpaceX itself says "staged
     combustion"; "full-flow" comes from secondary sources [S: commercial
     branch]. This is a source-tier gap worth recording, not a doubt about the
     hardware.

### B.7 Tap-off (combustion tap-off, hot-gas tap-off)
- **Definition.** Hot gas is tapped from the main combustion chamber to drive
  the turbine, then dumped. Open cycle. The turbine sees hotter gas than in a
  GG [S: SRC-WIKI-TAPOFF].
- **Examples:** J-2S (test-fired, never flown) [S: SRC-WIKI-TAPOFF,
  SRC-SECRETPROJ-J2DERIV; USAF altitude test reports AD0874400, AD0867628 seen
  as identifiers]; BE-3 / BE-3PM ("tap-off", Blue Origin's own wording) [S:
  SRC-BLUE-BE3-DEBUT]; Firefly Reaver, Lightning and Miranda ("patented tap-off
  cycle", Firefly's own wording) [S: commercial branch].
- "Tap-off" ≡ "combustion tap-off" ≡ "hot-gas tap-off". Staged combustion
  differs in having a separate preburner and turbine exhaust that goes to the
  chamber.

### B.8 Separate turbine working fluid (third-fluid drive)
- **H2O2 decomposed to steam:** A4/V-2 (T-Stoff / Z-Stoff) [S: europe branch,
  secondary]; HWK 109-509 (two sources disagree on the catalyst, CF in ledger);
  R-7 RD-107/108 (solid catalyst; H2O2 pumps driven from the main turbopump; N2
  heated in the GG exhaust for tank pressurization) [S: SRC-WIKI-RD107]; RD-214
  [S: SRC-WIKI-RD214]; Redstone A-7 [BG].
- **Correction to a common assumption:** the Soyuz third stage's RD-0110 is a
  LOX/kerosene GG, not an H2O2 steam drive [S: SRC-WIKI-RD0110].
- **Monopropellant (hydrazine) GG turbine drive:** NOT_AUDITED.
- **Solid-propellant GG as a continuous drive:** NOT_AUDITED. Solid cartridges
  as **start** devices are confirmed (§8).
- Encoding: `cycle = separate_turbine_working_fluid`, B1 =
  `separate_working_fluid`, with the working fluid named. This needs a third
  propellant line in the propellant system (H2O2 plus catalyst), so a
  two-propellant schema breaks here.
- **British HTP engines** (Gamma, Stentor, Sprite): HTP is the **main
  oxidizer** and also drives the turbine, so it is not a separate fluid there
  [S: europe branch, JBIS 1990]. Do not apply this category mechanically to
  every HTP engine.

### B.9 Electric pump — see A.6.

### B.10 Pressure-fed — no cycle (LIQ-2 rule upheld).

## 4. C — Tank pressurization (stage/vehicle attribute)

| Category | Hardware evidence |
| --- | --- |
| Stored He, ambient, regulated | Apollo SPS [S: SRC-AEHS-RPE]; Shuttle OMS [S: SRC-NTRS-OMS-1974] |
| Stored He, cold bottles submerged in a cryogen | Falcon 9 COPVs in the LOX tanks; reported also for Antares and Soyuz-2.1b/v [S: SRC-SPACEFLIGHT101-AMOS6]; S-IVB He spheres in the LH2 tank [S: Tier E]; S-IC He bottles in the LOX tank [S: Tier E] |
| Stored He heated in an engine heat exchanger | S-IVB: He warmed in the J-2 heat exchanger for the LOX tank [S: Tier E]; J-2X same concept [S: SRC-NASA-J2XBLOG-HEX] |
| Autogenous GOX from an engine heat exchanger | J-2 [S: SRC-PATENT-US7895823]; SSME GOX heat exchanger at the HPOTP turbine exit feeding tank pressurization and POGO [S: SRC-PATENT-US5918460] |
| Autogenous GH2 tapped from the engine | S-IVB LH2 tank [S: Tier E]; Centaur GH2 bled from the RL10s [S: SRC-ULA-TITANCENTAUR]; Shuttle ET [S: SRC-WIKI-AUTOGENOUS] |
| Autogenous CH4/O2 | Starship / Super Heavy [S: Tier E only; possibly time-varying, CF-TAXONOMY-8] |
| GG product gas | Titan II fuel tank pressurized with fuel-rich GG exhaust [S: SRC-WIKI-LR87] |
| Vaporized propellant via a GG-exhaust heat exchanger | Titan II oxidizer tank: N2O4 vaporized in the superheater coils [S: SRC-WIKI-LR87, SRC-MILSTD-T2START] |
| Inert gas heated by GG exhaust | R-7 (RD-107/108): N2 heated in the GG exhaust [S: SRC-WIKI-RD107] |
| Chemical / main-tank injection (MTI) | NOT_AUDITED; [BG] 1960s experiments only |
| Tridyne (inert + H2 + O2, catalytically heated) | Patents and concepts only [S: SRC-PATENT-US10495027, SRC-PATENT-US4804520]; flight heritage not confirmed → **experimental** |
| Self-pressurization (boil-off / vapour) | Concept studies and N2O systems [BG] |

Two terminology traps:
1. **"Autogenous" means two things in the literature.** Strictly, the
   propellant itself is heated and returned to its own tank [S:
   SRC-WIKI-AUTOGENOUS]. Titan II's fuel tank, pressurized with GG **products**,
   is also called "autogenous" [S: SRC-WIKI-LR87]. DB-1 should store
   `autogenous_propellant_vapour` and `gg_product_gas` as different values.
2. **Autogenous pressurization is not a cycle.** It lives on the stage. Where
   the engine supplies the heat exchanger or the bleed port, the engine record
   gets a **port** (a pressurization tap or HEX node in the topology), and the
   stage record owns the pressurization system. RocketForge SYS-4 already
   records autogenous and warm-gas as intent only, which matches this.

## 5. D — Cooling and thermal protection (record per zone)

Nearly every large engine mixes methods, so a single `cooling` value is
always lossy. Proposed zones: `injector_face`, `chamber`, `throat`,
`nozzle_regen_section`, `nozzle_extension`.

| Method | Evidence |
| --- | --- |
| Regenerative, brazed tube wall | F-1 to ε 10 [S: SRC-WIKI-F1]; Vulcain 2 brazed-tube nozzle (tube count only in a Tier E dataset — not used) [S: SRC-WIKI-VULCAIN]; [BG] H-1, J-2, RL10 |
| Regenerative, milled channel + electroformed / brazed close-out | [BG] SSME MCC, Vulcain, LE-7; LE-9 HIP-brazed chamber [S: SRC-IAC-LE9-2017] |
| Regenerative, additively manufactured | Rutherford printed chamber [S: SRC-RKLB-BATTERY] |
| Russian brazed corrugated / spot-connected double wall | [BG], to verify against a Russian design text |
| Film / boundary layer | F-1 extension cooled by turbine exhaust; Vulcain 2 turbine-exhaust film [S]; fuel-rich outer injector rows [BG] |
| Transpiration | [BG] porous (Rigimesh) injector faces on SSME and J-2 are often cited; **not confirmed** |
| Dump cooling | Vulcain 2+ nozzle-extension demonstrator, dump-cooled laser-welded sandwich wall [S: SRC-IAC10-V2PNE]; Vulcain 2.1 hydrogen-cooled extension [S: SRC-ESA-V21NE] |
| Radiation | Merlin 1C Vacuum niobium extension [S: commercial branch]; Shuttle PRCS R-40A columbium [S: spacecraft branch]; R-4D-11 C-103 [BG/datasheet not opened] |
| Ablative | [BG] RS-68, AJ10 (SPS, OMS?), LMDE, Merlin 1A ("ablative", Wikipedia only) |
| Ceramic (radiation) | Akatsuki OME silicon-nitride chamber [BG; NOT_AUDITED] |
| Heat sink | test hardware only [BG] |

**Status note.** Several widely repeated cooling assignments (OMS
regeneratively cooled with fuel; SPS and LMDE ablative) were **not confirmed**
in DB-0 and stay out of the data as REPORTED values.

## 6. E — Injector architecture

Element classes (SP-8089 is the canonical reference; not opened) [BG]:

| Class | Typical use / examples |
| --- | --- |
| Non-impinging coaxial, shear | LOX/H2 (J-2, RS-25, RL10) [BG]; LE-5B-2 has 306 coaxial elements vs 180 on LE-5B [S: SRC-WIKI-LE5] |
| Coaxial, swirl (bi-swirl) | Russian practice [BG] |
| Impinging like-doublet / unlike-doublet / triplet / pentad / quadlet | storable and kerosene engines [BG] |
| Showerhead | early engines [BG] |
| Pintle (fixed or moving sleeve) | TRW LMDE, TR-201, Merlin [BG; LMDE pintle **not verified**, Merlin pintle Tier D only] |
| Splash plate | [BG] |
| Concentric annular / slot | [BG] |
| Burner-cup ("pot") head | A4: 18 pre-chamber cups [BG] |

**Stability devices** are separate from the element type: baffles, acoustic
cavities and resonators. LE-9 uses varied element lengths plus a resonator [S:
SRC-MHI-TR55-2]. Store them as a list, never as a boolean.

## 7. F — Turbomachinery arrangement

| Feature | Evidence and notes |
| --- | --- |
| One turbopump feeding several chambers | RD-0110 (4 chambers) [S]; RD-107/108 (4 chambers + verniers) [S]; RD-170 (4 chambers), RD-180 (2), RD-0124 (4) [S/BG] |
| Engine **module** of several complete engines | YF-21 = 4 × YF-20, YF-24, YF-2 are modules [S: asia branch]; "four chambers share one turbopump" for YF-21 was **not** confirmed |
| Single-shaft integrated turbopump | R-7: turbine, ox pump, fuel pump plus a small H2O2 pump on one axle [S: SRC-WIKI-RD107]; F-1 Mk10 single turbine for both pumps [S: SRC-WIKI-F1] |
| Separate fuel and ox turbopumps | FFSC (one per preburner) [S: SRC-AF-IPD-2006]; Vulcain 2 (LOX TP by Avio, LH2 TP by Snecma) [S, Tier D]; LE-7A [BG]; J-2 with turbines in series [BG] |
| Geared turbopumps | [BG] H-1, MA-5, RS-27, LR87, HM7B — all to verify; RL10 gear-driven ox pump [BG] |
| Boost (low-pressure) pumps | SP-8107 pp. 53–55 cited by SRC-PATENT-US5197851; [BG] RS-25 LPFTP (gas-turbine driven) and LPOTP (hydraulic-turbine driven by LOX); RD-170 boost pumps: ox by gas turbine, fuel by hydraulic turbine (to verify) |
| Multi-stage pumps / axial pumps | [BG] SSME HPFTP 3-stage; J-2 fuel pump axial; M-1 axial H2 pump |
| Impeller form | LE-9 open impellers [S: SRC-IAC-LE9-2017] |
| Multiple preburners | RS-25 (2), Raptor (2), IPD (2), RD-270 (2) [S/BG] |

Schema consequence: a turbopump is **not** a field of the engine. It is an
assembly that owns shafts; shafts own pumps, turbines, inducers and gearboxes;
pumps feed one or more downstream nodes. Hydraulic turbines driven by liquid
propellant (LPOTP, RD-170 fuel boost) have to be representable as turbines
whose working fluid is a liquid.

## 8. G — Start and control

| Function | Evidence |
| --- | --- |
| Solid start cartridge | LR87 / Titan II: about 1 s at about 2000 psia into the turbine, then the GG takes over [S: SRC-MILSTD-T2START, SRC-WIKI-LR87] |
| Gravity / tank-head start, then steam drive | R-7 [S: Tier E] |
| Bootstrap / tank-head start | [BG] RL10, Vinci, other expanders |
| Stored-gas spin start | [BG] J-2 GH2 start tank; RS-68 helium spin (**unverified**) |
| Hypergolic ignition slugs (TEA-TEB) | [BG] F-1, Merlin; Merlin TEA-TEB Tier D only |
| Pyrotechnic / chemical ampoule | [BG] RD-170 triethylaluminium ampoule; R-7 pyrotechnic ignition [S: Tier E] |
| Augmented spark igniter | [BG] J-2, RS-25 |
| Catalyst bed | monopropellant thrusters (MR series etc.) |
| Electric start | Rutherford (inherent) |
| Electro-mechanical valves, no pneumatics | LE-9 [S: SRC-IAC-LE9-2016, SRC-IAC-LE9-2018] |
| Closed-loop thrust and mixture-ratio control | LE-9 [S: IAC-19 summary] |
| Deep throttling | BE-3 110,000 → 20,000 lbf [S: SRC-BLUE-BE3-DEBUT]; BE-4 640,000 → 220,000 lbf [S]; MR-80B > 100:1 [S]; J-2S throttling and variable MR [S] |
| Throttle effectors | [BG] RS-25 preburner oxidizer valves; RL10 turbine bypass valve; J-2 PU (mixture-ratio) valve; LMDE flow-control valves with variable-area injector (unverified) |

Schema consequence: start and control are **sequences and effectors**, not
fields. A throttle range is meaningful only together with the operating points
it spans and the effector that moves between them.

## 9. H — Chamber arrangement and unusual architectures

| Category | Status | Examples |
| --- | --- | --- |
| Multi-chamber with common turbopump | flight | RD-107/108, RD-0110, RD-170/171/180, RD-0124, RD-8 |
| Clustered engine module sold under one designation | flight | YF-21, YF-24, YF-2; Stoke Andromeda ring of thrusters [BG] |
| Main chambers plus verniers or steering chambers on one turbopump | flight | RD-107 (2 verniers), RD-108 (4), RD-0110 (steering nozzles), RD-0212 = RD-0213 + RD-0214 steering engine [S: ussr branch] |
| Rotating engine | design / experimental | Roton |
| Linear aerospike | test hardware | XRS-2200 ("pump-fed GG engine with a linear aerospike", NTRS paper [S]); RS-2200 cancelled |
| Tripropellant | ground test / study | RD-701, RD-0750, Li/F2/H2 [BG; NOT_AUDITED] |
| Dual-fuel / dual-mode | studies | [BG] |
| Powerhead-only demonstrator | test hardware | IPD (no flight nozzle) |
| Water-quenched solid GG pressurizing a liquid engine | flight | Diamant A Vexin B (pressure-fed engine with no turbopump; a slow-burning solid GG, quenched with water, pressurized its tanks) [S: Rothmund IAC-09, europe branch] |

The Vexin B finding also corrects a widespread error: "water injection into the
gas generator" is often attached to the Viking engine. DB-0 found no source for
that on Viking. The water-quenched gas generator belongs to Vexin B.

## 10. Categories that look equivalent but are not

1. **Open expander / expander bleed / chamber bleed / dump cooling.** The first
   two are aliases. "Chamber bleed" says where the coolant is heated. Dump
   cooling drives no turbine.
2. **Tap-off vs staged combustion.** Both take hot gas to a turbine. Tap-off
   takes it from the main chamber and dumps it. Staged combustion uses a
   separate preburner and injects the exhaust.
3. **Closed cycle vs staged combustion.** Closed also includes closed expander.
4. **GG vs "bleed cycle".** "Bleed" is ambiguous. Avoid it as a value.
5. **Pressure-fed vs blowdown.** Blowdown ⊂ pressure-fed.
6. **Autogenous pressurization vs any cycle.** Different object (stage vs
   engine), and "autogenous" itself splits into propellant-vapour vs GG-product.
7. **"Topping cycle."** A historical US umbrella term. Do not map it to one
   value without context.
8. **Electric-pump-fed vs pressure-fed.** Electric pumps are pump-fed.
9. **"Bootstrap" (start) vs "booster pump" (turbomachinery) vs "booster"
   (role).**
10. **Engine vs engine module vs propulsion system.** YF-21 (module of four
    YF-20), RD-0212 (propulsion system = RD-0213 + RD-0214), Atlas MA-5
    (propulsion system, alias only) are not single engines.
11. **Staged combustion "with afterburning" (Russian "с дожиганием").**
    A translation artefact, not a different cycle.
12. **Gas generator vs "turbine exhaust used for X".** The disposition is a
    separate axis (B2). It should not spawn new cycle names such as "GG with
    nozzle injection cycle".

## 11. Category coverage verdict

| Category | Real hardware found? | Strongest evidence class in DB-0 |
| --- | --- | --- |
| Pressure-fed regulated | yes (flight) | Tier D summaries, Tier A reports seen as identifiers |
| Blowdown (engine-level) | spacecraft systems only | background |
| Self-pressurized liquid main engine | not confirmed → experimental/amateur | background |
| Positive expulsion (bladder, diaphragm, bellows) | yes (flight tanks) | patents, SAE abstract |
| Turbopump | yes | many |
| Electric pump | yes (flight: Rutherford, Delphin) | manufacturer pages |
| Positive-displacement pump | test hardware only (XCOR) | trade press |
| Rotating centrifugal feed | design/experimental only (Roton) | encyclopedic/trade |
| Gas generator (all B2 sub-variants) | yes | mixed |
| Closed expander | yes | agency summaries |
| Expander bleed / open expander | yes (LE-5A/5B, LE-9, BE-3U) | agency / manufacturer |
| Fuel-rich staged combustion | yes | mixed |
| Ox-rich staged combustion | yes | mixed; Glavkosmos/ULA Tier A summaries |
| Full-flow staged combustion | yes (RD-270 ground, IPD ground, Raptor flight) | mixed |
| Tap-off | yes (J-2S ground, BE-3 flight, Firefly flight) | manufacturer pages |
| Separate working fluid (H2O2) | yes | secondary |
| Monopropellant GG turbine drive | NOT_AUDITED | — |
| Solid GG continuous turbine drive | NOT_AUDITED (start cartridges only confirmed) | — |
| Tridyne pressurization | patents/concepts → experimental | patents |
| Main-tank injection | NOT_AUDITED | — |
| Aerospike | test hardware (XRS-2200) | NTRS paper summary |
| Tripropellant | ground test / study | background |
