"""F-1 evidence opened in DB-0.5."""
from ledger import A, D, S, T, C, BLOCK

F1 = "ENG-US-F-1"
D("SRC-DB05-NTRS-20100027316", identifier="NTRS 20100027316 (Remembering the Giants, Chapter One + Appendix C viewgraphs CP6_0450_Apollo 11 F1-*.ppt)",
  title="Rocketdyne - F-1 Saturn V First Stage Engine (Robert Biggs)", tier="A",
  rights_checked="NTRS PUBLIC_USE_PERMITTED; Rocketdyne viewgraphs reproduced in a NASA publication", rights_class="VALUES_WITH_ATTRIBUTION",
  figures_rights="RIGHTS_REVIEW_REQUIRED", note="NEW source (not in DB-0).")
BLOCK("SRC-RKD-F1-FAMILIARIZATION", "no URL in DB-0 registry; not located in NTRS search this session")
BLOCK("SRC-MSFC-SATURNV-FLIGHTMANUAL", "no URL in DB-0 registry", "MSFC-MAN-503 (NTRS 19750063889) opened as the available flight manual.")

LC = "NTRS 20100027316 PDF p.16, slide 'F-1 Engine Characteristics' (CP6_0450_Apollo 11 F1-6.ppt)"
LF = "NTRS 20100027316 PDF p.16, slide 'F-1 Engine Basic Features' (F1-7.ppt)"
A(F1, "performance.thrust_sl", None, "1,522,000", 1522000, "lb", {"environment": "sea_level"}, "SRC-DB05-NTRS-20100027316", LC, db0=None,
  note="Rating epoch not printed on the slide.")
A(F1, "performance.thrust_vac", None, "1,748,200", 1748200, "lb", {"environment": "vacuum"}, "SRC-DB05-NTRS-20100027316", LC, db0=None)
A(F1, "performance.isp_sl", None, "265.4", 265.4, "s", {"environment": "sea_level"}, "SRC-DB05-NTRS-20100027316", LC, db0=None)
A(F1, "performance.isp_vac", None, "304.1", 304.1, "s", {"environment": "vacuum"}, "SRC-DB05-NTRS-20100027316", LC, db0=None)
A(F1, "performance.pc", None, "1,125", 1125, "psia", {"pc_station": "UNSTATED"}, "SRC-DB05-NTRS-20100027316", LC, db0=None)
A(F1, "propellants.mixture_ratio", None, "2.27", 2.27, ":1", {"mr_basis": "engine mixture ratio"}, "SRC-DB05-NTRS-20100027316", LC, db0=None)
A(F1, "mechanical.mass", None, "18,616", 18616, "lb", {"definition": "UNSTATED"}, "SRC-DB05-NTRS-20100027316", LC, db0=None)
A(F1, "mechanical.dimensions", None, "18.4 feet tall; 12 feet wide", "18.4 x 12", "ft", {}, "SRC-DB05-NTRS-20100027316", LC + " (photo captions)", db0=None)
A(F1, "history.production_deliveries", None, "98", 98, "engines", {}, "SRC-DB05-NTRS-20100027316", LC, db0=None)
A(F1, "test_history.qualification_life", None, "Starts 20; Duration 2,250 seconds; mission duration 165 seconds", "20 / 2250 / 165", "", {}, "SRC-DB05-NTRS-20100027316", LC, db0=None)
A(F1, "nozzle.area_ratio", None, "16:1", 16, ":1", {}, "SRC-DB05-NTRS-20100027316", LF, db0=None)
A(F1, "pumps.configuration", None, "Single unit-single shaft turbopump; two stage impulse turbine drive; dual discharge centrifugal fuel pump; dual discharge centrifugal LOX pump",
  "text", "", {}, "SRC-DB05-NTRS-20100027316", LF, db0=None)
A(F1, "pumps.shaft_order", None, "LOX pump on top of the shaft, then a fuel pump, then a turbine", "text", "", {}, "SRC-DB05-NTRS-20100027316", "text PDF p.4 (book p.20)", db0=None)
A(F1, "cooling.zones", None, "tube-wall down to the 10:1 expansion, where the turbine exhaust was put into the nozzle through a skirt extension ... double-wall, hot, gas-cooled nozzle extension",
  "text", "", {}, "SRC-DB05-NTRS-20100027316", "text PDF p.4 (book p.20)", db0=None)
A(F1, "ignition_start.method", None, "No auxiliary starting power required; simple tank head start", "tank head start", "", {}, "SRC-DB05-NTRS-20100027316", LF + "; text p.5", db0=None)
A(F1, "fluids.rp1_multipurpose", None, "Turbopump bearing lubrication; Hydraulic power for engine valve actuators and vehicle thrust vector control actuators", "text", "", {},
  "SRC-DB05-NTRS-20100027316", LF, db0=None)
A(F1, "performance.thrust_sl_development", None, "We later ran this engine at 1.8 million pounds of thrust", 1800000, "lb", {}, "SRC-DB05-NTRS-20100027316", "text PDF p.4", db0=None,
  note="Development demonstration, not a rating.")
L5 = "MSFC-MAN-503 p.4-4 (PDF p.61) 'S-IC Stage Propulsion'"
A(F1, "performance.thrust_sl", None, "1,530,000 pound fixed thrust", 1530000, "lb", {"environment": "UNSTATED (S-IC first stage; sea level implied)", "epoch": "SA-503 manual, 25 Nov 1968"},
  "SRC-DB05-NTRS-19750063889", L5, db0=None, note="Third rating value alongside 1,500,000 and 1,522,000; see CF-DB05-F1-RATING.")
A(F1, "nozzle.area_ratio_chamber", None, "bell shaped thrust chamber with a 10:1 expansion ratio, and detachable, conical nozzle extension which increases the thrust chamber expansion ratio to 16:1",
  "10 / 16", ":1", {}, "SRC-DB05-NTRS-19750063889", L5, db0=None)
A(F1, "cooling.nozzle_extension", None, "The thrust chamber is cooled regeneratively by fuel, and the nozzle extension is cooled by gas generator exhaust gases", "text", "", {},
  "SRC-DB05-NTRS-19750063889", L5, db0=None)
A(F1, "gg.flow_and_mr", None, "Total propellant flow rate is approximately 170 lb/sec at a lox/RP-1 mixture ratio of 0.42:1", "170 / 0.42", "lb/sec / :1", {},
  "SRC-DB05-NTRS-19750063889", "MSFC-MAN-503 p.4-5 (PDF p.62) 'Gas Generator'", db0=None)
A(F1, "pressurization.heat_exchanger", None, "The heat exchanger expands lox and cold helium for propellant tank pressurization ... heated by the turbopump exhaust", "text", "", {},
  "SRC-DB05-NTRS-19750063889", "MSFC-MAN-503 p.4-5 'Heat Exchanger'", db0=None)
A(F1, "control.valve_count", None, "two main fuel valves per engine ... two main lox valves on each engine", "2+2", "valves", {}, "SRC-DB05-NTRS-19750063889", "MSFC-MAN-503 p.4-5", db0=None)
A(F1, "ignition_start.hypergol", None, "The IFV prevents thrust chamber ignition until the turbopump pressure has reached 375 psi", 375, "psi", {}, "SRC-DB05-NTRS-19750063889",
  "MSFC-MAN-503 p.4-4 'Hypergol Manifold'", db0=None)

S("SCH-DB05-F1-BIGGS-SCHEM", engine_ids=[F1], source_id="SRC-DB05-NTRS-20100027316", locator="PDF p.17, Appendix C slide 'F-1 Engine Schematic'",
  title="F-1 Engine Schematic", kind="pictorial flow schematic, colour legend Fuel/Oxidizer/Hot Gas, flow arrows",
  viewed_how="rendered at 240 dpi", legible="labels, legend and main-line arrows legible",
  note="Turbine exhaust manifold and nozzle-extension injection are not drawn; text supplies them.")

SH, TX, BO = "SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH"
LS = "NTRS 20100027316 slide 'F-1 Engine Schematic'"
LT = "NTRS 20100027316 text pp.4-5; MSFC-MAN-503 pp.4-4..4-5"
T(F1, configuration="F-1 (Saturn V S-IC), configuration of the Rocketdyne slide", schematic_ids=["SCH-DB05-F1-BIGGS-SCHEM"],
  text_sources=["SRC-DB05-NTRS-20100027316", "SRC-DB05-NTRS-19750063889"],
  nodes=[
      ("N-TP-LOX", "pump", "LOX pump (dual discharge centrifugal)", "engine", BO, LS),
      ("N-TP-FUEL", "pump", "Fuel pump (dual discharge centrifugal)", "engine", BO, LS),
      ("N-TP-TURB", "turbine", "Two-stage impulse turbine", "engine", BO, LT),
      ("N-MOV1", "valve", "Main Oxidizer Valve No.1", "engine", SH, LS),
      ("N-MOV2", "valve", "Main Oxidizer Valve No.2", "engine", SH, LS),
      ("N-MFV1", "valve", "Main Fuel Valve No.1", "engine", SH, LS),
      ("N-MFV2", "valve", "Main Fuel Valve No.2", "engine", SH, LS),
      ("N-GG", "gas_generator", "Gas Generator (with dual ball valve)", "engine", BO, LS),
      ("N-HYP", "igniter", "Hypergol Manifold", "engine", BO, LS),
      ("N-HEX", "heat_exchanger", "Heat Exchanger (on turbine exhaust)", "engine", BO, LS),
      ("N-TC", "combustion_chamber", "Thrust chamber / injector", "engine", SH, LS),
      ("N-TC-COOL", "cooling_jacket", "Regen tubes to epsilon 10", "engine", TX, LT),
      ("N-NOZEXT", "nozzle_extension", "Gas-cooled nozzle extension (epsilon 10 to 16)", "engine", TX, LT),
      ("N-AMB", "ambient", "Exhaust", "ambient", TX, LT),
      ("N-STAGE-PRESS", "tank_pressurization_port", "LOX and helium for stage tank pressurization", "stage", TX, "MSFC-MAN-503 p.4-5"),
      ("N-HYDRAULIC", "actuator_supply", "RP-1 hydraulic power to engine valves and vehicle TVC actuators", "engine", TX, LT),
  ],
  edges=[
      ("N-TP-LOX", "N-MOV1", "LOX", "discharge 1 (split_group O1)", SH, LS),
      ("N-TP-LOX", "N-MOV2", "LOX", "discharge 2 (split_group O1)", SH, LS),
      ("N-MOV1", "N-TC", "LOX", "main oxidizer", SH, LS),
      ("N-MOV2", "N-TC", "LOX", "main oxidizer", SH, LS),
      ("N-TP-LOX", "N-GG", "LOX", "GG oxidizer", SH, LS),
      ("N-TP-FUEL", "N-MFV1", "RP-1", "discharge 1 (split_group F1)", SH, LS),
      ("N-TP-FUEL", "N-MFV2", "RP-1", "discharge 2 (split_group F1)", SH, LS),
      ("N-MFV1", "N-TC-COOL", "RP-1", "fuel to thrust chamber", BO, LS + "; MSFC-MAN-503 p.4-4"),
      ("N-MFV2", "N-TC-COOL", "RP-1", "fuel to thrust chamber", BO, LS + "; MSFC-MAN-503 p.4-4"),
      ("N-TC-COOL", "N-TC", "RP-1", "coolant to injector", TX, LT),
      ("N-TP-FUEL", "N-GG", "RP-1", "GG fuel", SH, LS),
      ("N-TP-FUEL", "N-HYP", "RP-1", "fuel pushes hypergol into chamber", BO, LS + "; MSFC-MAN-503 p.4-4"),
      ("N-HYP", "N-TC", "hypergol + RP-1", "ignition", BO, LS + "; MSFC-MAN-503 p.4-4"),
      ("N-GG", "N-TP-TURB", "hot gas", "turbine drive", BO, LS + "; MSFC-MAN-503 p.4-5"),
      ("N-TP-TURB", "N-HEX", "hot gas", "turbine exhaust through heat exchanger", TX, "MSFC-MAN-503 p.4-5"),
      ("N-HEX", "N-NOZEXT", "hot gas", "turbine exhaust injected at epsilon 10 through skirt extension; film-cools extension", TX, "NTRS 20100027316 text p.4; MSFC-MAN-503 p.4-4"),
      ("N-NOZEXT", "N-AMB", "turbine exhaust", "exhaust", TX, LT),
      ("N-TC", "N-AMB", "combustion gas", "exhaust", TX, LT),
      ("N-HEX", "N-STAGE-PRESS", "GOX / warm helium", "stage tank pressurization", TX, "MSFC-MAN-503 p.4-5"),
      ("N-TP-FUEL", "N-HYDRAULIC", "RP-1", "hydraulic working fluid", TX, LF + "; MSFC-MAN-503 p.4-4"),
      ("N-TP-TURB", "N-TP-LOX", "none", "mechanical_shaft (single shaft)", BO, LS + "; text p.4"),
      ("N-TP-TURB", "N-TP-FUEL", "none", "mechanical_shaft (single shaft)", BO, LS + "; text p.4"),
  ],
  omissions=["turbine exhaust manifold geometry (not drawn)", "4-way control valve and checkout valve", "gas generator igniters and exhaust igniters",
             "thrust chamber prefill (ethylene glycol) system", "purge systems", "helium supply to the heat exchanger (stage)"],
  note="'HEX -> nozzle extension' order follows MSFC-MAN-503 (heated by turbopump exhaust) and Biggs (exhaust into nozzle at 10:1); not drawn on the slide.")

C("CF-DB05-F1-RATING", engine_id=F1, field_path="performance.thrust_sl rating epoch", db0_conflict_id="CF-US_HIST-01; CF-ORCH_VERIFY-1",
  claims=[["1,522,000 lb sea level (no epoch printed)", "SRC-DB05-NTRS-20100027316", "slide F1-6"],
          ["1,530,000 pound fixed thrust (SA-503 manual, 25 Nov 1968)", "SRC-DB05-NTRS-19750063889", "p.4-4"],
          ["a million and one-half (design goal)", "SRC-DB05-NTRS-20100027316", "text p.3"]],
  resolution="UNRESOLVED", kind="different_epoch",
  explanation="Three primary values: 1.5 Mlbf design goal, 1.530 Mlbf in the SA-503 crew manual, 1.522 Mlbf in a 2006 Rocketdyne slide. Which flights carried which rating is not established by the opened documents.")
C("CF-DB05-F1-PC", engine_id=F1, field_path="performance.pc", db0_conflict_id="CF-R2_US_CLASSIC-F1-1",
  claims=[["1,125 psia (station unstated)", "SRC-DB05-NTRS-20100027316", "slide F1-6"], ["70 bar (1,015 psi)", "SRC-WIKI-F1", "DB-0"], ["982 psi", "SRC-PURDUE-F1", "DB-0"]],
  resolution="PARTIALLY_RESOLVED", kind="primary_value_found",
  explanation="Manufacturer value 1,125 psia found; the lower secondary values may be nozzle-stagnation values but no opened primary document says so.")
C("CF-DB05-F1-MASS", engine_id=F1, field_path="mechanical.mass", db0_conflict_id="CF-R2_US_CLASSIC-F1-2",
  claims=[["18,616 lb", "SRC-DB05-NTRS-20100027316", "slide F1-6"], ["designed ... with a weight of 18,000 pounds", "SRC-DB05-NTRS-20100027316", "text p.4"],
          ["~18,500 lb dry", "SRC-ENGINEHISTORY-RPE0812", "DB-0"]],
  resolution="UNRESOLVED", kind="definition", explanation="18,616 lb is primary but its definition (dry/burnout) is not printed; 18,000 lb is a design weight.")
