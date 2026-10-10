"""DB-2B Wave 2 targeted source completion (2026-10-10): RL10A-4-2, RL10B-2, RD-170, IPD, RS-68A,
LR87, Rutherford. Only documents opened in this pass, or already opened in DB-0.5."""
from ledger import A, D, S, T, C, BLOCK

RA42, RB2, RD, IPD = "ENG-US-RL10A-4-2", "ENG-US-RL10B-2", "ENG-SU-RD-170", "ENG-US-IPD"
R68A, LR11 = "ENG-US-RS-68A", "ENG-US-LR87-AJ-11"
RUT, RUTV = "ENG-NZ-RUTHERFORD", "ENG-NZ-RUTHERFORD-VACUUM"
_NO_NOTICE = "no copyright notice on pages read (extracted text of every page checked 2026-10-10)"

# ------------------------------------------------------------------ documents opened in this pass
D("SRC-DB05-NTRS-20090014109", identifier="NTRS 20090014109 (conference paper; Creech, Taylor, Bellamy, NASA MSFC)", title="Ares V and RS-68B",
  tier="A", rights_checked=f"NTRS PUBLIC_USE_PERMITTED; export control NO; {_NO_NOTICE}", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Describes the RS-68A upgrade relative to the RS-68 (p.4). Prints absolute values for the RS-68B and J-2X only.")
D("SRC-DB05-NTRS-20090014116", identifier="NTRS 20090014116 (presentation; Creech, NASA MSFC)", title="Update on the Ares V to Support Heavy Lift for U.S. Space Exploration Policy",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; export control NO", rights_class="PUBLIC_DOMAIN_GOV",
  note="Opened; RS-68B and J-2X only, no RS-68A value.")
D("SRC-NASA-PSP-BLOG-WORKHORSE", identifier="NASA Science blog, Parker Solar Probe, 2018-08-11 'Workhorse Rocket to Carry NASA's Parker Solar Probe'",
  title="Workhorse Rocket to Carry NASA's Parker Solar Probe", tier="A",
  rights_checked="NASA web page (US Government work); no copyright notice in the page text (checked 2026-10-10)", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Agency launch-day blog, not an engine document: identity and a headline thrust only.")
D("SRC-NASA-PSP-PRESSKIT-2018", identifier="NASA Parker Solar Probe press kit, August 2018", title="Parker Solar Probe (press kit)", tier="A",
  rights_checked="NASA publication (US Government work)", rights_class="PUBLIC_DOMAIN_GOV", note="Opened (42 pp.); no RS-68 or RS-68A statement.")
D("SRC-DB05-NTRS-19750004937", identifier="General Dynamics Convair report CASD-LVP73-007; NTRS 19750004937", title="Titan IIIE/Centaur D-1T Systems Summary",
  tier="A", rights_checked=f"NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; {_NO_NOTICE}", rights_class="PUBLIC_DOMAIN_GOV",
  note="Programme contractor's systems summary (Titan IIIE stage I engine LR87AJ-11, section 6.2.3; Figure 6-20 viewed).")
D("SRC-DB05-NTRS-19750013258", identifier="NASA TM; NTRS 19750013258", title="Titan/Centaur T/C-1 post flight evaluation report", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="Opened (387 pp.); flight data, not mined in this pass.")
D("SRC-DB05-NTRS-20100032986", identifier="NTRS 20100032986 (Dougherty)", title="Liquid Rocket Engine Testing - Historical Lecture: Simulated Altitude Testing at AEDC",
  tier="B", rights_checked="NTRS PUBLIC_USE_PERMITTED", rights_class="VALUES_WITH_ATTRIBUTION", note="Opened; names 'LR-87 (Titan IIIC)' as tested at AEDC J-4; not mined.")
D("SRC-DB05-NTRS-19730004741", identifier="Aerospace Corp. ATR-73(7257)-1; NTRS 19730004741", title="Empirical evaluation of pump inlet compliance", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="Opened; LR87 pump dynamics study, no engine variant identified; not mined.")
D("SRC-DB05-NTRS-19720022122", identifier="Martin Marietta MCR-72-107; NTRS 19720022122", title="Investigation of characteristics of feed system instabilities", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="Opened; LR87 feed-system study, no engine variant identified; not mined.")
D("SRC-DB05-NTRS-20050243602", identifier="NTRS 20050243602 (conference paper; Huebner, Saiyed, Swith)",
  title="Advanced Development Projects for Constellation From The Next Generation Launch Technology Program Elements", tier="A",
  rights_checked=f"NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; {_NO_NOTICE}", rights_class="PUBLIC_DOMAIN_GOV",
  note="IPD section pp.5-6: programme identity, objectives and test status.")
D("SRC-DB05-NTRS-20060004818", identifier="NTRS 20060004818 (preprint; Steele, Molder, Hudson et al.)",
  title="Uncertainty Evaluation of Computational Model Used to Support the Integrated Powerhead Demonstrator Project", tier="A",
  rights_checked=f"NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; {_NO_NOTICE}", rights_class="PUBLIC_DOMAIN_GOV",
  note="Facility activation model study; one engine statement (p.1).")
D("SRC-DB05-NTRS-19950002748", identifier="NTRS 19950002748 (conference paper; Wang, McConnaughey, Warsi, NASA MSFC)",
  title="CFD assessment of the carbon monoxide and nitric oxide formation from RD-170 hot-fire testing", tier="B",
  rights_checked=f"NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; {_NO_NOTICE}", rights_class="PUBLIC_DOMAIN_GOV",
  note="NASA analysis of an RD-170 test, not an engine document: graded B for engine facts. Its 1,777,000 lbf is a CFD input, not transcribed.")
D("SRC-DB05-NTRS-19950025328", identifier="NTRS 19950025328 (conference paper; Wang, McConnaughey, Warsi)",
  title="CFD assessment of the pollutant environment from RD-170 propulsion system testing", tier="B",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="Opened; the same study at length; not mined.")
D("SRC-DB05-NTRS-20140011176", identifier="NTRS 20140011176 (Baumeister, NASA GRC)", title="RL10 Engine Ability to Transition from Atlas to Shuttle/Centaur Program",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV",
  note="Opened; RL10A-3-3A and RL10A-3-3B only, nothing on the RL10A-4-2.")
D("SRC-ULA-CENTAUR-ICLT4", identifier="4th Int. Conf. on Launcher Technology, Liege, 3-6 Dec 2002 (Rudman, Austad, Lockheed Martin); PDF hosted by ulalaunch.com",
  title="The Centaur Upper Stage Vehicle", tier="B",
  rights_checked="'Copyright 2002 Lockheed Martin Corporation' printed p.2", rights_class="RESTRICTED_REFERENCE", figures_rights="RESTRICTED_REFERENCE",
  note="Names the RL10A-4 variants by vehicle; prints no RL10A-4-2 performance value.")
D("SRC-RL-PRESSKIT-2017", identifier="Rocket Lab press kit, May 2017 (MED17_001)", title="Rocket Lab Press Kit 2017", tier="A",
  rights_checked="'(c) Rocket Lab USA 2017' printed p.8", rights_class="RESTRICTED_REFERENCE", figures_rights="RESTRICTED_REFERENCE",
  note="Manufacturer. Identity and headline architecture; no engine performance value.")
D("SRC-RL-500-TESTS", identifier="Rocket Lab news release, 31 Jan 2018", title="Rocket Lab reaches 500 Rutherford engine test fires", tier="A",
  rights_checked="'(c)2026 Rocket Lab USA' in the site footer", rights_class="RESTRICTED_REFERENCE", figures_rights="RESTRICTED_REFERENCE")
D("SRC-RKLB-PAYLOAD-INCREASE", identifier="Rocket Lab news release, 4 Aug 2020",
  title="Rocket Lab Increases Electron Payload Capacity, Enabling Interplanetary Missions and Reusability", tier="A",
  rights_checked="'(c)2026 Rocket Lab USA' in the site footer", rights_class="RESTRICTED_REFERENCE", figures_rights="RESTRICTED_REFERENCE")
D("SRC-RL-ELECTRON-PAGE", identifier="rocketlabusa.com Electron page (retrieved 2026-10-08)", title="Electron | Rocket Lab", tier="A",
  rights_checked="'(c)2026 Rocket Lab USA' in the site footer", rights_class="RESTRICTED_REFERENCE", figures_rights="RESTRICTED_REFERENCE",
  note="Undated page: its values are as of retrieval.")

BLOCK("SRC-DB05-NTRS-20040075665", "NTRS record is an abstract only; the download URL returned HTTP 000 (no file)",
      "Transient Simulation of the IPD Rocket Engine: the paper itself was not reached.")
BLOCK("SRC-DB05-NTRS-20050041816", "NTRS record is an abstract only; the download URL returned HTTP 404",
      "Facility Activation and Characterization for IPD Turbopump Testing.")
BLOCK("SRC-USAFM-LR87", "nationalmuseum.af.mil returns HTTP 403 to direct requests", "USAF Museum LR87 fact sheet (discovery lead).")

# ------------------------------------------------------------------ RS-68A
B = "SRC-NASA-PSP-BLOG-WORKHORSE"
A(R68A, "identity.vehicle", None, "three Common Booster Cores, each with an RS-68A engine", "text", "", {"vehicle": "Delta IV Heavy"}, B,
  "NASA blog 2018-08-11, paragraph on the Delta IV Heavy", db0=None)
A(R68A, "performance.thrust", None, "Each engine produces 702,000 pounds of thrust", 702000, "lb", {"environment": "UNSTATED"}, B,
  "NASA blog 2018-08-11, paragraph on the Delta IV Heavy", db0=None,
  note="Environment not printed per engine; the same sentence gives a 'combined total liftoff thrust of more than 2.1 million pounds'.")
AR = "SRC-DB05-NTRS-20090014109"
A(R68A, "changes.thrust", None, "Engine thrust is increased 39,000 pounds force by modifying the turbine nozzles from axis-symmetric to 3 dimensional to reduce turbine blade loading and to expand the operational range of both the fuel and oxidizer turbopumps",
  "text", "", {"relative_to": "RS-68"}, AR, "NTRS 20090014109 p.4, RS-68B Engine section", db0=None,
  note="A change relative to the RS-68, not an RS-68A value.")
A(R68A, "changes.injector", None, "Specific impulse is improved by increasing the number of the main injector combustion elements which improves mixing and combustion efficiency",
  "text", "", {"relative_to": "RS-68"}, AR, "NTRS 20090014109 p.4, RS-68B Engine section", db0=None)
A(R68A, "changes.reliability", None, "Other AATS funded improvements to the RS-68A engine include a new bearing material that is more resistant to stress corrosion cracking, improved processing of the 2nd stage fuel turbopump blisk to reduce cracking potential, improved oxidizer turbopump chill sensor and an improved hot gas temperature sensor",
  "text", "", {}, AR, "NTRS 20090014109 p.4, RS-68B Engine section", db0=None)
A(R68A, "gas_generator.igniter", None, "An improved gas generator igniter that has less foreign object debris potential is also under development and expected to be included in the RS-68A certification program",
  "text", "", {}, AR, "NTRS 20090014109 p.4, RS-68B Engine section", db0=None, note="Printed as expected, in 2009.")
C("CF-DB05-RS68A-THRUST", engine_id=R68A, field_path="performance.thrust",
  claims=[["Each engine produces 702,000 pounds of thrust (environment not printed)", B, "NASA blog 2018-08-11"],
          ["705,000 lbf sea level (DB-0 search-result excerpt; data sheet HTTP 404, never opened)", "SRC-L3H-RS68A-DS", "DB-0"]],
  resolution="PARTIALLY_RESOLVED", kind="rating_or_rounding",
  explanation="The only opened statement is NASA's 702,000 lb with no environment. The manufacturer figure was seen only in a search excerpt; whether the two are one rating rounded differently is not established.")

# ------------------------------------------------------------------ LR87AJ-11 (Titan IIIE stage I)
G = "SRC-DB05-NTRS-19750004937"
GT, GS = "CASD-LVP73-007 PDF p.30 (report p.2-1) propulsion summary", "CASD-LVP73-007 PDF p.209 (report p.6-21) engine performance summary"
A(LR11, "performance.thrust", None, "LR87AJ-11: Rated Thrust 520,000 lb", 520000, "lb", {"environment": "UNSTATED"}, G, GT, db0=None)
A(LR11, "performance.isp_vac", None, "LR87AJ-11: Rated Isp 301.1 sec (vac)", 301.1, "s", {"environment": "vacuum"}, G, GT, db0=None)
A(LR11, "propellants.fuel", None, "LR87AJ-11: Propellants Aerozine 50", "aerozine_50", "", {}, G, GT, db0=None)
A(LR11, "propellants.oxidizer", None, "LR87AJ-11: Propellants Nitrogen Tetroxide", "nitrogen_tetroxide", "", {}, G, GT, db0=None)
A(LR11, "architecture.cooling_feed", None, "Both the Stage I and Stage II engines are regeneratively cooled, turbopump fed engines.", "text", "", {}, G,
  "CASD-LVP73-007 PDF p.32 (report p.2-3)", db0=None)
A(LR11, "architecture.layout", None, "the LR87AJ-11 rocket engine to be a pair of identical engines attached to a single frame and mounted on the vehicle. These individual engines, designated Subassembly 1, and Subassembly 2, are designed to operate simultaneously under a single control system.",
  "text", "", {}, G, "CASD-LVP73-007 PDF p.207 (report p.6-19)", db0=None)
A(LR11, "turbines.drive_source", None, "Gas generators are operated by propellant from the discharge lines to drive the turbines which maintain propellant flow.", "text", "", {}, G,
  "CASD-LVP73-007 PDF p.208 (report p.6-20)", db0=None)
A(LR11, "architecture.feed", None, "Both the Stage I and Stage II engines are regeneratively cooled, turbopump fed engines.", "pump_fed", "", {}, G,
  "CASD-LVP73-007 PDF p.32 (report p.2-3)", db0=None)
A(LR11, "architecture.cycle", None, "Gas generators are operated by propellant from the discharge lines to drive the turbines which maintain propellant flow.",
  "gas_generator", "", {}, G, "CASD-LVP73-007 PDF p.208 (report p.6-20)", db0=None)
A(LR11, "control.method", None, "The engine is hydraulically balanced and requires no thrust controls. It is preset to operate at a certain level (i. e., consume propellant at a fixed rate) by the use of orifices.",
  "text", "", {}, G, "CASD-LVP73-007 PDF p.208 (report p.6-20)", db0=None)
A(LR11, "performance.pc", None, "Combustion in the thrust chambers produces gas at pressures over 800 psia", 800, "psia", {"bound": "over"}, G,
  "CASD-LVP73-007 PDF p.208 (report p.6-20)", db0=None, note="A lower bound, not an operating value.")
A(LR11, "performance.thrust", None, "Altitude Thrust, lb 520,000", 520000, "lb", {"environment": "altitude"}, G, GS, db0=None)
A(LR11, "performance.isp", None, "Altitude Specific Impulse, sec 301.1", 301.1, "s", {"environment": "altitude"}, G, GS, db0=None)
A(LR11, "performance.mass_flow_total", None, "Total Flow Rate, lb/sec 1,727", 1727, "lb/s", {}, G, GS, db0=None)
A(LR11, "performance.mass_flow_oxidizer", None, "Oxidizer Flow Rate, lb/sec 1,135", 1135, "lb/s", {}, G, GS, db0=None)
A(LR11, "performance.mass_flow_fuel", None, "Fuel Flow Rate, lb/sec 592", 592, "lb/s", {}, G, GS, db0=None)
A(LR11, "propellants.mixture_ratio", None, "Mixture Ratio 1.915", 1.915, "", {}, G, GS, db0=None,
  note="No direction printed. The same table's flows (1,135 oxidizer, 592 fuel) would make it O/F, but that is a derivation, not print.")
A(LR11, "performance.operating_cycle", None, "Operating Cycle, sec 165", 165, "s", {}, G, GS, db0=None)
A(LR11, "nozzle.area_ratio", None, "Expansion Ratio 15:1", 15, ":1", {}, G, GS, db0=None)

S("SCH-DB05-LR87AJ11-GD-F620", engine_ids=[LR11], source_id=G, locator="NTRS 19750004937 PDF p.210 (report p.6-22), Figure 6-20",
  title="LR87AJ-11 propellant fill and bleed schematic", kind="pictorial fill-and-bleed schematic, legend Fuel/Oxidizer/Lube oil and component symbols",
  viewed_how="rendered at 110 and 200 dpi", legible="labels and legend legible; line shading legible; unshaded lines (empty at fill) not identifiable by fluid",
  note="Both subassemblies drawn with the vehicle tanks above. Drawn in a programme contractor's report.")
SH, TX, BO = "SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH"
LF = "NTRS 19750004937 PDF p.210 Figure 6-20"
T(LR11, configuration="LR87AJ-11, Titan IIIE stage I (CASD-LVP73-007), subassembly 1 of 2", schematic_ids=["SCH-DB05-LR87AJ11-GD-F620"],
  text_sources=[G],
  nodes=[
      ("N-FTANK", "tank", "Stage I fuel tank", "vehicle", SH, LF),
      ("N-OTANK", "tank", "Stage I oxidizer tank", "vehicle", SH, LF),
      ("N-FP", "pump", "Fuel pump (turbopump)", "engine", SH, LF),
      ("N-OP", "pump", "Oxidizer pump (turbopump)", "engine", SH, LF),
      ("N-TURB", "turbine", "Turbine (turbopump)", "engine", BO, f"{LF}; PDF p.208"),
      ("N-GG", "gas_generator", "Gas generator", "engine", BO, f"{LF}; PDF p.208"),
      ("N-FCV", "check_valve", "Fuel check valve (gas generator)", "engine", SH, LF),
      ("N-OCV", "check_valve", "Oxidizer check valve (gas generator)", "engine", SH, LF),
      ("N-SC", "start_cartridge", "Start cartridge", "engine", SH, LF),
      ("N-OV", "valve", "Oxidizer valve (thrust chamber valve)", "engine", BO, f"{LF}; PDF p.208"),
      ("N-FV", "valve", "Fuel valve (thrust chamber valve)", "engine", BO, f"{LF}; PDF p.208"),
      ("N-ACT", "actuator", "Thrust chamber valve actuator", "engine", SH, LF),
      ("N-TC", "combustion_chamber", "Thrust chamber", "engine", BO, f"{LF}; PDF p.208"),
      ("N-SKIRT", "nozzle_extension", "Ablative skirt", "engine", SH, LF),
      ("N-FH", "heat_exchanger", "Fluid heater (in the turbine exhaust)", "engine", SH, LF),
      ("N-AMB", "ambient", "Ambient (turbine exhaust overboard)", "ambient", SH, LF),
  ],
  edges=[
      ("N-FTANK", "N-FP", "fuel", "feed", SH, LF),
      ("N-OTANK", "N-OP", "oxidizer", "feed", SH, LF),
      ("N-OP", "N-OV", "oxidizer", "pump discharge to thrust chamber valve", SH, LF),
      ("N-OV", "N-TC", "oxidizer", "main oxidizer to thrust chamber", SH, LF),
      ("N-FP", "N-FV", "fuel", "pump discharge to thrust chamber valve", SH, LF),
      ("N-FV", "N-TC", "fuel", "main fuel to thrust chamber", SH, LF),
      ("N-FP", "N-FCV", "fuel", "gas generator bootstrap from the discharge line", BO, f"{LF}; PDF p.208"),
      ("N-OP", "N-OCV", "oxidizer", "gas generator bootstrap from the discharge line", BO, f"{LF}; PDF p.208"),
      ("N-FCV", "N-GG", "fuel", "gas generator fuel", SH, LF),
      ("N-OCV", "N-GG", "oxidizer", "gas generator oxidizer", SH, LF),
      ("N-GG", "N-TURB", "hot gas", "turbine drive", BO, f"{LF}; PDF p.208"),
      ("N-SC", "N-TURB", "hot gas", "start spin-up", SH, LF),
      ("N-TURB", "N-FP", "none", "mechanical_shaft", SH, LF),
      ("N-TURB", "N-OP", "none", "mechanical_shaft", SH, LF),
      ("N-TURB", "N-FH", "hot gas", "turbine exhaust", SH, LF),
      ("N-FH", "N-AMB", "hot gas", "turbine exhaust overboard", SH, LF),
      ("N-TC", "N-SKIRT", "hot gas", "nozzle flow", SH, LF),
      ("N-FP", "N-ACT", "fuel", "fuel pressure actuates the thrust chamber valves", BO, f"{LF}; PDF p.211"),
  ],
  omissions=["subassembly 2 (identical, per the text)", "lube oil pump, reservoir and heat exchanger circuit", "gas cooler and autogenous tank pressurization",
             "pressure sequencing valve, LTCV pot and actuator linkages", "fluid heater fluid circuit", "regenerative cooling path through the chamber",
             "cavitating venturis and balance orifices", "prevalves and fill and bleed lines", "instrumentation and pressure switch"],
  note="provenance_class = ORIGINAL_CONTRACTOR (drawn in General Dynamics Convair's Titan IIIE/Centaur systems summary). Regenerative cooling is stated in the text (PDF p.32) but its path is not drawn.")

# ------------------------------------------------------------------ RL10B-2
A(RB2, "propellants.combination", None, "The second-stage Pratt & Whitney RL10B-2 engine derives its power from liquid oxygen and liquid hydrogen cryogenic propellants and is used on all Delta IV configurations.",
  "text", "", {}, "SRC-ULA-DIV-INAUGURAL", "p.2 'Vehicle description'", db0=None)
_RB2_PROP = "The second-stage Pratt & Whitney RL10B-2 engine derives its power from liquid oxygen and liquid hydrogen cryogenic propellants"
A(RB2, "propellants.oxidizer", None, _RB2_PROP, "liquid_oxygen", "", {}, "SRC-ULA-DIV-INAUGURAL", "p.2 'Vehicle description'", db0=None)
A(RB2, "propellants.fuel", None, _RB2_PROP, "liquid_hydrogen", "", {}, "SRC-ULA-DIV-INAUGURAL", "p.2 'Vehicle description'", db0=None)
A(RB2, "nozzle.extension", None, "the engine possesses an extendible nozzle designed for boost-phase environments and longer second-stage burn durations",
  "text", "", {}, "SRC-ULA-DIV-INAUGURAL", "p.2 'Vehicle description'", db0=None)

# ------------------------------------------------------------------ RL10A-4-2 (identity only; the source is copyrighted)
CT = "SRC-ULA-CENTAUR-ICLT4"
A(RA42, "identity.vehicle_and_lineage", None, "The Atlas V vehicles use the RL10A-4-2 engine, which was successfully flown on the maiden voyage of the Atlas V program. The –2 engine has the benefits of the –1B engine, and also incorporates several new features that improve engine reliability and performance.",
  "text", "", {}, CT, "PDF p.9 'Engine System'", db0=None)
A(RA42, "identity.sibling_variants", None, "The Titan Centaur uses the RL10A- 4-1A. The Atlas IIIA and IIIB vehicles use the RL10A-4-1B version of this engine",
  "text", "", {}, CT, "PDF p.9 'Engine System'", db0=None, note="RL10A-4-1A and RL10A-4-1B are separate variants; nothing here gives their values.")

# ------------------------------------------------------------------ IPD
N = "SRC-DB05-NTRS-20050243602"
A(IPD, "identity.programme", None, "The Integrated Powerhead Demonstrator (IPD) Program began in 1994 at the Air Force Research Laboratory (AFRL) with the goal of designing, fabricating, and testing a 250k-lb-thrust, full-flow, staged-combustion cycle engine.",
  "text", "", {}, N, "NTRS 20050243602 p.5", db0=None)
A(IPD, "identity.contractors", None, "AFRL has contracts with Pratt Whitney Rocketdyne and Aerojet", "text", "", {}, N, "NTRS 20050243602 p.5", db0=None)
A(IPD, "turbomachinery.components", None, "Component testing of the oxygen turbopump and preburner was completed by October 2003, and the hydrogen turbopump and preburner component testing was completed by August 2004.",
  "text", "", {}, N, "NTRS 20050243602 p.6", db0=None)
A(IPD, "test_history.engine", None, "To date, the IPD has performed 6 successful startup sequence tests, and the latest test achieved approximately 90% power level at the peak of this start- transient test.",
  "text", "", {}, N, "NTRS 20050243602 p.6", db0=None, note="Status as of the 2005 paper.")
_IPD_ABS = "The Integrated Powerhead Demonstrator (IPD) is a 250K lbf (1.1 MN) thrust cryogenic hydrogen/oxygen engine technology demonstrator"
A(IPD, "propellants.oxidizer", None, _IPD_ABS, "liquid_oxygen", "", {"read_as": "cryogenic oxygen"}, "SRC-NTRS-IPD-WPB", "Abstract (PDF p.1)", db0=None)
A(IPD, "propellants.fuel", None, _IPD_ABS, "liquid_hydrogen", "", {"read_as": "cryogenic hydrogen"}, "SRC-NTRS-IPD-WPB", "Abstract (PDF p.1)", db0=None)
A(IPD, "architecture.cycle", None, "a new hydrogen-fueled, full-flow, staged combustion rocket engine", "full_flow_staged_combustion", "", {},
  "SRC-DB05-NTRS-20060004818", "NTRS 20060004818 p.1 Introduction", db0=None)

# ------------------------------------------------------------------ RD-170
A(RD, "architecture.layout", None, "RD-170 is a regeneratively cooled four-nozzle clustered engine which burns Kerosene fuel with liquid oxygen and was used to thrust Energia launch vehicles.",
  "text", "", {}, "SRC-DB05-NTRS-19950002748", "NTRS 19950002748 p.2 Discussion", db0=None,
  note="A NASA analyst's description, not a manufacturer document.")
_RD_CFD = "RD-170 is a regeneratively cooled four-nozzle clustered engine which burns Kerosene fuel with liquid oxygen"
A(RD, "propellants.oxidizer", None, _RD_CFD, "liquid_oxygen", "", {}, "SRC-DB05-NTRS-19950002748", "NTRS 19950002748 p.2 Discussion", db0=None)
A(RD, "propellants.fuel", None, _RD_CFD, "kerosene", "", {}, "SRC-DB05-NTRS-19950002748", "NTRS 19950002748 p.2 Discussion", db0=None,
  note="Printed 'Kerosene'; not RP-1 (the Rockwell reconstruction labels the line RP-1).")

# ------------------------------------------------------------------ Rutherford (manufacturer statements; every source is copyrighted)
PK = "SRC-RL-PRESSKIT-2017"
A(RUT, "architecture.summary", None, "Rutherford is a state of the art oxygen and kerosene pump fed engine specifically designed from scratch for Electron, using an entirely new propulsion cycle.",
  "text", "", {"scope": "Rutherford in general"}, PK, "PDF p.3 'About Rutherford engine'", db0=None)
A(RUT, "pumps.drive", None, "A unique feature of Rutherford is the high-performance electric propellant pumps which reduce mass and replace hardware with software.",
  "text", "", {"scope": "Rutherford in general"}, PK, "PDF p.3 'About Rutherford engine'", db0=None)
A(RUT, "manufacturing.additive", None, "Rutherford is the first engine of its kind to use 3D printing for all primary components.", "text", "", {"scope": "Rutherford in general"}, PK,
  "PDF p.3 'About Rutherford engine'", db0=None)
A(RUT, "identity.stage_count", None, "Ignition of the nine Rutherford engines powering Electron’s first stage", "text", "", {}, PK, "PDF p.5 launch timeline", db0=None)
A(RUTV, "identity.stage", None, "The vacuum Rutherford engine on Stage 2 ignites", "text", "", {}, PK, "PDF p.5 launch timeline", db0=None)
T18 = "SRC-RL-500-TESTS"
A(RUT, "performance.thrust_sl", None, "sea level versions on Electron’s first stage producing 24 kN (5,500 lbf) of thrust and has a specific impulse of 311 s (3.05 km/s)",
  5500, "lbf", {"environment": "sea_level", "epoch": "release of 31 Jan 2018"}, T18, "release of 31 Jan 2018, 'About the Rutherford engine'", db0=None)
A(RUTV, "performance.thrust_vac", None, "the vacuum optimized version operating on Electron’s second stage produces a max thrust of 24 kN (5,500 lbf) of thrust and has a specific impulse of 343 s (3.36 km/s)",
  5500, "lbf", {"environment": "vacuum", "epoch": "release of 31 Jan 2018"}, T18, "release of 31 Jan 2018, 'About the Rutherford engine'", db0=None)
A(RUT, "mechanical.mass", None, "Weighing just 35 kg each, nine Rutherford engines propel Rocket Lab’s Electron launch vehicle", 35, "kg", {"epoch": "release of 31 Jan 2018"}, T18,
  "release of 31 Jan 2018, 'About the Rutherford engine'", db0=None)
A(RUT, "manufacturing.printed_parts", None, "With a 3D printed combustion chamber, injectors, pumps, and main propellant valves", "text", "", {"scope": "Rutherford in general"}, T18,
  "release of 31 Jan 2018", db0=None)
T20 = "SRC-RKLB-PAYLOAD-INCREASE"
A(RUT, "performance.thrust_sl", None, "The sea level versions on Electron’s first stage now produce 5,600 lbf of thrust (up from 5,500 lbf, with a specific impulse of 311 s (3.05 km/s).",
  5600, "lbf", {"environment": "sea_level", "epoch": "release of 4 Aug 2020"}, T20, "release of 4 Aug 2020, 'About the Rutherford Engine'", db0=None)
A(RUTV, "performance.thrust_vac", None, "The vacuum optimized version operating on Electron’s second stage now produces a max thrust of 5,800 lbf of thrust and has a specific impulse of 343 s (3.36 km/s).",
  5800, "lbf", {"environment": "vacuum", "epoch": "release of 4 Aug 2020"}, T20, "release of 4 Aug 2020, 'About the Rutherford Engine'", db0=None)
A(RUT, "pumps.drive", None, "Rutherford uses an entirely new propulsion cycle of brushless DC electric motors and high-performance lithium polymer batteries to drive its propellant pumps.",
  "text", "", {"scope": "Rutherford in general"}, T20, "release of 4 Aug 2020, 'About the Rutherford Engine'", db0=None)
EP = "SRC-RL-ELECTRON-PAGE"
A(RUT, "performance.stage_thrust", None, "First Stage 9 Sea-level Rutherford Engines Lift-off Thrust: 190 kN (43,000 lbf) Peak Thrust: 224 kN (50,600 lbf) ISP: 311 seconds",
  "text", "", {"scope": "nine engines", "epoch": "as retrieved 2026-10-08"}, EP, "Electron page, 'Rutherford Engine' panel", db0=None)
A(RUTV, "performance.thrust_vac", None, "Second Stage Single Vacuum Rutherford Engine Total Thrust: 25.8 kN (5,800 lbf) ISP: 343 seconds",
  5800, "lbf", {"epoch": "as retrieved 2026-10-08"}, EP, "Electron page, 'Rutherford Engine' panel", db0=None)
C("CF-DB05-RUTHERFORD-SL-THRUST", engine_id=RUT, field_path="performance.thrust_sl",
  claims=[["24 kN (5,500 lbf) (31 Jan 2018)", T18, "release"], ["now produce 5,600 lbf (up from 5,500 lbf) (4 Aug 2020)", T20, "release"]],
  resolution="EXPLAINED", kind="different_epoch",
  explanation="The 2020 release itself says the sea-level engine went from 5,500 to 5,600 lbf: two epochs, not a disagreement.")
C("CF-DB05-RUTHERFORD-VAC-THRUST", engine_id=RUTV, field_path="performance.thrust_vac",
  claims=[["max thrust of 24 kN (5,500 lbf) (31 Jan 2018)", T18, "release"], ["now produces a max thrust of 5,800 lbf (4 Aug 2020)", T20, "release"],
          ["Total Thrust: 25.8 kN (5,800 lbf) (as retrieved 2026)", EP, "Electron page"]],
  resolution="PARTIALLY_RESOLVED", kind="different_epoch",
  explanation="The 2020 release says 'now', so 5,800 lbf is a later epoch than 5,500 lbf, but it does not say what changed; the 2018 vacuum figure equals the 2018 sea-level figure.")
