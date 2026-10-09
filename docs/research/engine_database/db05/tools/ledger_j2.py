"""J-2 and J-2S evidence opened in DB-0.5."""
from ledger import A, D, S, T, C, BLOCK

J2, J2S = "ENG-US-J-2", "ENG-US-J-2S"

D("SRC-NTRS-20100027318", identifier="NTRS 20100027318 (Remembering the Giants, Chapter Two + Appendix D viewgraphs CP6_0450_J2-2..5.ppt)",
  title="Rocketdyne - J-2 Saturn V 2nd & 3rd Stage Engine (Paul Coffman)", tier="A",
  rights_checked="NTRS PUBLIC_USE_PERMITTED; NASA SP compilation; Rocketdyne viewgraphs reproduced by NASA", rights_class="VALUES_WITH_ATTRIBUTION",
  figures_rights="RIGHTS_REVIEW_REQUIRED", note="Manufacturer engineer recollection plus manufacturer viewgraphs; printed in NASA publication.")
D("SRC-DB05-NTRS-19750063889", identifier="MSFC-MAN-503 (25 Nov 1968); NTRS 19750063889", title="Saturn V Flight Manual SA-503", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED, but p.A (PDF p.3) prints 'Reproduction for non-government use of the information or illustrations contained in this publication is not permitted without specific approval of the issuing service.'",
  rights_class="RIGHTS_REVIEW_REQUIRED", note="NEW source (not in DB-0). Replaces the unreachable SA-507 manual (history.nasa.gov 404).")
D("SRC-NTRS-20120016414", identifier="NTRS 20120016414", title="System Engineering and Technical Challenges Overcome in the J-2X Rocket Engine Development Project",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="DB-0 'title not seen' -> title verified.")
D("SRC-NTRS-20080036837", identifier="NTRS 20080036837", title="From Concept to Design: Progress on the J-2X Upper Stage Engine for the Ares I Crew Launch Vehicle and the Ares V Cargo Launch Vehicle",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV")
D("SRC-DB05-NTRS-19940016798", identifier="NASA contract NAS8-39210, DCN 1-1-PP-02147, DR-4 (Rocketdyne, April 1993); NTRS 19940016798",
  title="Advanced Transportation System Studies, Technical Area 3, Alternate Propulsion Subsystem Concepts: J-2S Restart Study Task Final Report",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; contractor report (Rockwell International Rocketdyne)", rights_class="PUBLIC_DOMAIN_GOV",
  note="NEW source. Scanned rotated; OCR unusable; pages read visually.")
for sid in ["SRC-DTIC-AEDC-J2-SET", "SRC-DTIC-AD0867628", "SRC-DTIC-AD0874400", "SRC-DTIC-AEDC-J2S-SET"]:
    BLOCK(sid, "apps.dtic.mil returns HTTP 403 (and a 1.4 kB block page) to direct requests from this environment")
BLOCK("SRC-GENERALSTAFF-J2S-STUDY-1969", "generalstaff.org returns HTTP 403")
BLOCK("SRC-NASA-ALSJ-CSM02", "nasa.gov ALSJ path returns HTTP 404")
BLOCK("SRC-NASA-SA507-FLIGHTMANUAL", "history.nasa.gov/ap12fj/pdf/a12_sa507-flightmanual.pdf returns HTTP 404", "SA-503 manual (NTRS 19750063889) opened instead; it is a different vehicle's manual.")

# ---- J-2 ----
L3 = "NTRS 20100027318 PDF p.14, Appendix D slide 'J-2 Basic Engine Features' (CP6_0450_J2-3.ppt)"
A(J2, "performance.thrust_vac", None, "230,000", 230000, "lb", {"environment": "vacuum", "label": "Nominal vacuum thrust"}, "SRC-NTRS-20100027318", L3,
  db0=None, note="Rating epoch not stated on the slide; Coffman text p.3 says qualification tests were on 'the 225,000-pound version'.")
A(J2, "performance.isp_vac", None, "425", 425, "s", {"environment": "vacuum"}, "SRC-NTRS-20100027318", L3, db0=None)
A(J2, "performance.pc", None, "717", 717, "psia", {"pc_station": "nozzle stagnation", "pressure_basis": "abs"}, "SRC-NTRS-20100027318", L3, db0=None,
  note="Resolves 'a little over 700 psia' (text p.2). Station explicitly printed.")
A(J2, "propellants.mixture_ratio", None, "5.5:1", 5.5, ":1", {"mr_basis": "engine mixture ratio calibration (O/F)"}, "SRC-NTRS-20100027318", L3, db0=None)
A(J2, "mechanical.mass_dry_basic", None, "2,754", 2754, "lb", {"definition": "basic engine dry weight"}, "SRC-NTRS-20100027318", L3, db0=None)
A(J2, "mechanical.mass_dry_with_accessories", None, "3,492", 3492, "lb", {"definition": "engine dry weight (including accessories)"}, "SRC-NTRS-20100027318", L3, db0=None)
A(J2, "nozzle.area_ratio", None, "27.5:1", 27.5, ":1", {}, "SRC-NTRS-20100027318", L3 + "; text p.2", db0=None)
A(J2, "propellants.mixture_ratio_alternate", None, "capability of operating at a mixture ratio 4.5:1", 4.5, ":1", {}, "SRC-NTRS-20100027318", "text p.2 (book p.30)", db0=None)
A(J2, "pumps.fuel.type", None, "The fuel turbopump was an axial machine", "axial", "", {}, "SRC-NTRS-20100027318", "text p.2", db0=None)
A(J2, "pumps.ox.type", None, "The oxidizer turbopump was a fairly conventional centrifugal device", "centrifugal", "", {}, "SRC-NTRS-20100027318", "text p.2", db0=None)
A(J2, "turbines.arrangement", None, "series turbine arrangement, through the fuel turbopump and then over into the oxidizer turbopump, with a bypass for calibration and a heat exchanger ... before dumping into the thrust chamber at the nozzle midpoint",
  "text", "", {}, "SRC-NTRS-20100027318", "text p.2 (book p.30)", db0=None)
A(J2, "cooling.tube_pattern", None, "fully tubular thrust chamber with a fuel inlet at the reduced epsilon portion of the nozzle ... one tube down for every two tubes up", "text", "",
  {}, "SRC-NTRS-20100027318", "text p.2", db0=None)
A(J2, "history.production_count", None, "We delivered 152 production engines", 152, "engines", {}, "SRC-NTRS-20100027318", "text p.2, repeated p.3", db0=None)
A(J2, "performance.thrust_vac_qualified", None, "the 225,000-pound version of the engine, fifty-nine of which were delivered", 225000, "lb", {}, "SRC-NTRS-20100027318", "text p.3", db0=None)
A(J2, "performance.thrust_vac", None, "230 (klbf)", 230, "klbf", {"environment": "vacuum"}, "SRC-NTRS-20120016414", "p.1 Table 1 'Evolution of J-2X Requirements with J-2 and J-2S'", db0=None)
A(J2, "performance.isp_vac", None, "425", 425, "s", {}, "SRC-NTRS-20120016414", "p.1 Table 1", db0=None)
A(J2, "mechanical.mass_dry", None, "3492", 3492, "lb", {}, "SRC-NTRS-20120016414", "p.1 Table 1", db0=None)
A(J2, "turbines.drive", None, "Both turbopumps are powered in series by a single gas generator, which utilizes the same propellants as the thrust chamber", "text", "", {},
  "SRC-DB05-NTRS-19750063889", "MSFC-MAN-503 p.5-5 (PDF p.91) 'J-2 Rocket Engine'", db0=None)
A(J2, "control.mixture_ratio", None, "controlled by bypassing liquid oxygen from the discharge side of the oxidizer turbopump to the inlet side through a servovalve", "text", "", {},
  "SRC-DB05-NTRS-19750063889", "MSFC-MAN-503 p.5-5", db0=None)
A(J2, "pressurization.ownership", None, "lox tank pressurized by flowing lox through the heat exchanger in the oxidizer turbine exhaust duct; LH2 tank pressurized by GH2 from the thrust chamber fuel manifold",
  "text", "", {}, "SRC-DB05-NTRS-19750063889", "MSFC-MAN-503 p.5-5 and p.5-7", db0=None)
A(J2, "control.hydraulic_pump_drive", None, "The main hydraulic pump is driven by the oxidizer turbopump turbine", "text", "", {}, "SRC-DB05-NTRS-19750063889", "MSFC-MAN-503 p.5-5", db0=None)
A(J2, "ignition_start.spin_start", None, "STDV opens, allowing pressurized GH2 to flow through the series turbine drive system", "text", "", {},
  "SRC-DB05-NTRS-19750063889", "MSFC-MAN-503 p.5-7 'Engine Start Sequence'", db0=None)
A(J2, "ignition_start.ox_turbine_bypass", None, "During the start sequence the normally open oxidizer bypass valve permits a percentage of the gas to bypass the oxidizer turbine", "text", "", {},
  "SRC-DB05-NTRS-19750063889", "MSFC-MAN-503 p.5-7", db0=None)
# DB-2A supplement (2026-10-09): the 'Description' block of the same slide as the
# 230,000 lb performance table, re-read from the opened PDF (p.14).
A(J2, "architecture.feed", None, "Pump-fed, liquid-propellant rocket engine", "pump_fed", "", {}, "SRC-NTRS-20100027318", L3 + ", 'Description'", db0=None)
A(J2, "propellants.oxidizer", None, "Propellants: liquid oxygen & liquid hydrogen", "liquid_oxygen", "", {}, "SRC-NTRS-20100027318", L3 + ", 'Description'", db0=None)
A(J2, "propellants.fuel", None, "Propellants: liquid oxygen & liquid hydrogen", "liquid_hydrogen", "", {}, "SRC-NTRS-20100027318", L3 + ", 'Description'", db0=None)
A(J2, "architecture.cycle", None, "Turbine drive: gas generator burning main propellants", "gas_generator", "", {}, "SRC-NTRS-20100027318", L3 + ", 'Description'", db0=None)
A(J2, "cooling.thrust_chamber", None, "Tubular-wall thrust chamber, regeneratively cooled", "regenerative", "", {}, "SRC-NTRS-20100027318", L3 + ", 'Description'", db0=None)
A(J2, "turbomachinery.arrangement", None, "Separate oxidizer & fuel turbopumps", "text", "", {}, "SRC-NTRS-20100027318", L3 + ", 'Description'", db0=None)
# Review supplement (2026-10-09): Coffman passages the production J-2 graph cites
# as its text basis, recorded so that every cited passage is a ledger entry.
A(J2, "ignition_start.start_tank", None, "it was this start tank that would discharge cold hydrogen through the two turbines to get the engine started",
  "text", "", {}, "SRC-NTRS-20100027318", "text p.2", db0=None)
A(J2, "pressurization.oxygen", None, "a heat exchanger to heat up oxygen for tank pressurization (or helium in some instances)", "text", "", {},
  "SRC-NTRS-20100027318", "text p.2", db0=None)
A(J2, "ignition_start.igniter", None, "The thrust chamber was ignited by an augmented spark igniter in the middle with two spark plugs", "text", "", {},
  "SRC-NTRS-20100027318", "text p.4", db0=None)
A(J2, "turbines.drive_source", None, "there was a gas generator that was fed with fuel and oxygen off the main propellants ducts. The gas generator drove the turbomachinery",
  "text", "", {}, "SRC-NTRS-20100027318", "text p.2", db0=None)
A(J2, "turbines.exhaust_dump", None, "There was a 2:1 split, and we used the opening at the 2:1 split to dump the hot gas into the nozzle of the thrust chamber",
  "text", "", {}, "SRC-NTRS-20100027318", "text p.2", db0=None)

# ---- J-2S ----
L9 = "NTRS 19940016798 PDF p.9 slide 'J-2S Basic Engine Features' (SC91c-12-1055), page rotated"
A(J2S, "performance.thrust_vac", None, "265,000", 265000, "lb", {"environment": "vacuum", "label": "Nominal vacuum thrust"}, "SRC-DB05-NTRS-19940016798", L9, db0=None)
A(J2S, "performance.isp_vac", None, "436", 436, "s", {"environment": "vacuum"}, "SRC-DB05-NTRS-19940016798", L9, db0=None)
A(J2S, "performance.pc", None, "1,200", 1200, "psia", {"pc_station": "nozzle stagnation"}, "SRC-DB05-NTRS-19940016798", L9, db0=None)
A(J2S, "propellants.mixture_ratio", None, "5.5:1", 5.5, ":1", {"mr_basis": "engine mixture ratio calibration O/F"}, "SRC-DB05-NTRS-19940016798", L9, db0=None)
A(J2S, "mechanical.mass_dry_basic", None, "3,235", 3235, "lb", {"definition": "basic engine dry weight"}, "SRC-DB05-NTRS-19940016798", L9, db0=None)
A(J2S, "mechanical.mass_dry_with_accessories", None, "3,800", 3800, "lb", {"definition": "including accessories"}, "SRC-DB05-NTRS-19940016798", L9, db0=None)
A(J2S, "architecture.cycle", None, "Tap-off turbine drive cycle", "tap_off", "", {}, "SRC-DB05-NTRS-19940016798", L9 + "; PDF p.8 text 'changed to a tap-off cycle to eliminate the gas generator'",
  db0=None, note="Upgrades DB-0 engine cycle_status for ENG-US-J-2S from SECONDARY_CLAIM to REPORTED (Tier A).")
A(J2S, "nozzle.area_ratio", None, "40:1", 40, ":1", {}, "SRC-DB05-NTRS-19940016798", L9, db0=None)
A(J2S, "propellants.mixture_ratio_alternates", None, "capability to operate at mixture ratios of 5.0 and 4.5 upon command", "5.0; 4.5", ":1", {}, "SRC-DB05-NTRS-19940016798", "PDF p.8 text", db0=None)
A(J2S, "operating_modes.idle", None, "a feature for low thrust operation known as 'Idle Mode' ... for propellant tank settling, on orbit maneuvering, and rapid engine chilldown prior to firing",
  "text", "", {}, "SRC-DB05-NTRS-19940016798", "PDF p.8 text", db0=None)
A(J2S, "test_history.production_configuration", None, "6 Engines, 273 Tests, 30,858 sec; R&D configuration totalled 10,756 sec", "6/273/30858", "", {}, "SRC-DB05-NTRS-19940016798", L9, db0=None)
A(J2S, "performance.thrust_vac", None, "265 (klbf)", 265, "klbf", {}, "SRC-NTRS-20120016414", "p.1 Table 1", db0=None)
A(J2S, "performance.isp_vac", None, "436", 436, "s", {}, "SRC-NTRS-20120016414", "p.1 Table 1", db0=None)
A(J2S, "pumps.designation", None, "J-2S Mk. 29 turbopump design", "Mk-29", "", {}, "SRC-NTRS-20080036837", "PDF p.3 and p.4", db0=None,
  note="J-2X used it as point of departure; 'single-stage fuel turbopump design' stated as the J-2S point-of-departure (PDF p.3).")
for label, val in [("J-2S Engine Development bar start (ATP)", "1965"), ("1st 27.5:1 test", "2/66"), ("1st 40:1 test", "6/68"),
                   ("Dynamic Stability", "2/71"), ("Ready for Qual", "10/71"), ("Final Rpt", "3/74")]:
    A(J2S, f"history.timeline.{label}", None, val, val, "date", {}, "SRC-NTRS-20100027318",
      "NTRS 20100027318 PDF p.15, slide 'Apollo Era J-2 Engines' (CP6_0450_J2-5.ppt) timeline", db0=None, status="DIGITISED",
      note="Read from a viewed timeline chart; bar positions approximate, labels printed.")
# DB-2B Wave 1 supplement (2026-10-09): the 'Description' block of the same J-2S
# viewgraph (NTRS 19940016798 PDF p.9), re-read from the rendered page.
L9D = L9 + ", 'Description'"
A(J2S, "architecture.feed", None, "Pump-fed liquid propellant rocket engine", "pump_fed", "", {}, "SRC-DB05-NTRS-19940016798", L9D, db0=None)
A(J2S, "propellants.oxidizer", None, "Propellants - liquid oxygen & liquid hydrogen", "liquid_oxygen", "", {}, "SRC-DB05-NTRS-19940016798", L9D, db0=None)
A(J2S, "propellants.fuel", None, "Propellants - liquid oxygen & liquid hydrogen", "liquid_hydrogen", "", {}, "SRC-DB05-NTRS-19940016798", L9D, db0=None)
A(J2S, "cooling.thrust_chamber", None, "Tubular-wall thrust chamber, regen cooled", "regenerative", "", {}, "SRC-DB05-NTRS-19940016798", L9D, db0=None)

# ---- schematics ----
S("SCH-DB05-J2-COFFMAN-S4", engine_ids=[J2], source_id="SRC-NTRS-20100027318", locator="PDF p.15, Appendix D slide 'J-2 Engine Schematic' (CP6_0450_J2-4.ppt)",
  title="J-2 Engine Schematic", kind="pictorial flow schematic, colour legend Fuel/Oxidizer/Hot Gas, flow arrows",
  viewed_how="rendered at 110 and 260 dpi", legible="all labels and legend legible; arrows legible on main lines")
S("SCH-DB05-J2-SA503-F57", engine_ids=[J2], source_id="SRC-DB05-NTRS-19750063889", locator="MSFC-MAN-503 p.5-8 (PDF p.93), Figure 5-7 sheet 1 of 3 'S-II Engine Start'",
  title="S-II Engine Start", kind="pictorial start-sequence flow figure with numbered callouts and fluid legend",
  viewed_how="rendered at 120 dpi", legible="labels legible; hatching distinguishes fluids but turbine order is not unambiguous from hatching alone",
  db0_schematic_id="SCH-J-2-R2-1", note="DB-0 lead pointed at SA-507; SA-503 equivalent figure viewed instead.")

SH, TX, BO = "SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH"
LS = "NTRS 20100027318 slide J2-4"
LT = "NTRS 20100027318 text p.2; MSFC-MAN-503 pp.5-5..5-7"
T(J2, configuration="J-2 (Saturn S-II/S-IVB), configuration of the Rocketdyne slide", schematic_ids=["SCH-DB05-J2-COFFMAN-S4", "SCH-DB05-J2-SA503-F57"],
  text_sources=["SRC-NTRS-20100027318", "SRC-DB05-NTRS-19750063889"],
  nodes=[
      ("N-LOX-IN", "engine_inlet", "Oxidizer inlet", "engine", SH, LS),
      ("N-OTP-P", "pump", "Liquid oxygen pump (centrifugal)", "engine", BO, LS),
      ("N-OTP-T", "turbine", "Oxidizer turbopump turbine", "engine", BO, LT),
      ("N-FTP-P", "pump", "Liquid hydrogen pump (axial)", "engine", BO, LS),
      ("N-FTP-T", "turbine", "Fuel turbopump turbine", "engine", BO, LT),
      ("N-MRCV", "valve", "Mixture ratio control valve (PU valve)", "engine", BO, LS),
      ("N-MOV", "valve", "Main oxygen valve", "engine", SH, LS),
      ("N-MFV", "valve", "Main fuel valve", "engine", SH, LS),
      ("N-GGV", "valve", "Gas generator valve", "engine", SH, LS),
      ("N-GG", "gas_generator", "Gas generator", "engine", BO, LS),
      ("N-OTBV", "valve", "Oxidizer turbine bypass", "engine", BO, LS),
      ("N-HEX", "heat_exchanger", "Heat exchanger (in oxidizer turbine exhaust duct)", "engine", BO, LS),
      ("N-STANK", "energy_store_start_tank", "GH2 start tank", "engine", BO, LS),
      ("N-INJ", "injector", "Thrust chamber injector / dome", "engine", SH, LS),
      ("N-TC-COOL", "cooling_jacket", "Tubular-wall thrust chamber (regen)", "engine", BO, LT),
      ("N-TC", "combustion_chamber", "Thrust chamber", "engine", SH, LS),
      ("N-NOZ-DUMP", "nozzle_injection_port", "Hot-gas manifold at nozzle 2:1 tube split (nozzle midpoint)", "engine", TX, LT),
      ("N-AMB", "ambient", "Exhaust", "ambient", SH, LS),
      ("N-LOX-TANK-PRESS", "tank_pressurization_port", "O2 for tank pressurization", "stage", BO, LS),
      ("N-LH2-TANK-PRESS", "tank_pressurization_port", "H2 for tank pressurization", "stage", BO, LS),
      ("N-ASI", "igniter", "Augmented spark igniter", "engine", TX, "MSFC-MAN-503 p.5-7; NTRS 20100027318 text p.4"),
      ("N-HYD-PUMP", "hydraulic_pump", "Main hydraulic pump (TVC)", "engine", TX, "MSFC-MAN-503 p.5-5"),
  ],
  edges=[
      ("N-LOX-IN", "N-OTP-P", "LOX", "feed", SH, LS),
      ("N-OTP-P", "N-MOV", "LOX", "main oxidizer", SH, LS),
      ("N-MOV", "N-INJ", "LOX", "main oxidizer", SH, LS),
      ("N-OTP-P", "N-GGV", "LOX", "GG oxidizer branch", SH, LS),
      ("N-GGV", "N-GG", "LOX", "GG oxidizer", SH, LS),
      ("N-OTP-P", "N-MRCV", "LOX", "discharge-to-inlet bypass (MR control)", BO, LS + "; MSFC-MAN-503 p.5-5"),
      ("N-MRCV", "N-OTP-P", "LOX", "return to pump inlet", BO, LS + "; MSFC-MAN-503 p.5-5"),
      ("N-OTP-P", "N-HEX", "LOX", "branch to heat exchanger", BO, LS + "; MSFC-MAN-503 p.5-5"),
      ("N-HEX", "N-LOX-TANK-PRESS", "GOX", "tank pressurization", BO, LS + "; MSFC-MAN-503 p.5-5"),
      ("N-FTP-P", "N-MFV", "LH2", "main fuel", SH, LS),
      ("N-MFV", "N-TC-COOL", "LH2", "regen coolant (fuel inlet at reduced-epsilon nozzle station)", BO, LS + "; NTRS 20100027318 text p.2"),
      ("N-TC-COOL", "N-INJ", "H2", "coolant to injector", TX, "NTRS 20100027318 text p.2 (tubes down then up)"),
      ("N-FTP-P", "N-GG", "LH2", "GG fuel branch (downstream of pump, upstream of MFV as drawn)", SH, LS),
      ("N-INJ", "N-LH2-TANK-PRESS", "GH2", "tap from thrust chamber fuel manifold", BO, LS + "; MSFC-MAN-503 p.5-5"),
      ("N-INJ", "N-STANK", "GH2", "line between injector manifold and start tank as drawn (refill role not verified)", SH, LS),
      ("N-STANK", "N-FTP-T", "GH2", "spin start through series turbine drive (via STDV)", BO, LS + "; MSFC-MAN-503 p.5-7"),
      ("N-GG", "N-FTP-T", "hot gas", "turbine drive, first in series", BO, LS + "; NTRS 20100027318 text p.2"),
      ("N-FTP-T", "N-OTP-T", "hot gas", "crossover to oxidizer turbine (split_group H1)", BO, LS + "; NTRS 20100027318 text p.2"),
      ("N-FTP-T", "N-OTBV", "hot gas", "bypass around oxidizer turbine (split_group H1)", BO, LS + "; MSFC-MAN-503 p.5-7"),
      ("N-OTP-T", "N-HEX", "hot gas", "turbine exhaust through heat exchanger", BO, LS + "; MSFC-MAN-503 p.5-5"),
      ("N-HEX", "N-NOZ-DUMP", "hot gas", "dump into nozzle at 2:1 split (merge_group H2)", BO, LS + "; NTRS 20100027318 text p.2"),
      ("N-OTBV", "N-NOZ-DUMP", "hot gas", "bypass rejoins exhaust (merge_group H2)", SH, LS),
      ("N-INJ", "N-TC", "propellants", "injection", SH, LS),
      ("N-TC", "N-AMB", "combustion gas", "exhaust", SH, LS),
      ("N-NOZ-DUMP", "N-AMB", "turbine exhaust", "exhaust via nozzle", TX, "NTRS 20100027318 text p.2"),
      ("N-FTP-T", "N-FTP-P", "none", "mechanical_shaft (direct drive)", TX, "MSFC-MAN-503 p.5-5 'direct drive turbopumps'"),
      ("N-OTP-T", "N-OTP-P", "none", "mechanical_shaft (direct drive)", TX, "MSFC-MAN-503 p.5-5"),
      ("N-OTP-T", "N-HYD-PUMP", "none", "mechanical drive of main hydraulic pump", TX, "MSFC-MAN-503 p.5-5"),
  ],
  omissions=["ASI propellant supply lines", "pneumatic (helium) control system", "propellant bleed valves and recirculation (stage)",
             "start tank fill/vent valves", "GG fuel valve detail", "exact position of the GG fuel tap relative to the MFV (as drawn only)"],
  note="Both turbines are in series (fuel first). Turbine exhaust is dumped at the nozzle 2:1 tube split, not overboard.")

C("CF-DB05-J2-PC", engine_id=J2, field_path="performance.pc", db0_conflict_id="CF-R2_US_CLASSIC-J2-2",
  claims=[["717 psia (nozzle stagnation)", "SRC-NTRS-20100027318", "slide J2-3"], ["a little over 700 psia", "SRC-NTRS-20100027318", "text p.2"],
          ["763 psi", "SRC-WIKI-J2", "DB-0 search summary"]],
  resolution="RESOLVED", kind="primary_value_found",
  explanation="Primary manufacturer value 717 psia at nozzle stagnation for the 230,000 lb / MR 5.5 J-2. 763 psi has no support in any opened primary document; it may be an injector-face value or a different rating (not verified).")
C("CF-DB05-J2-MASS", engine_id=J2, field_path="mechanical.mass", db0_conflict_id="CF-R2_US_CLASSIC-J2-3",
  claims=[["2,754 lb basic engine dry; 3,492 lb including accessories", "SRC-NTRS-20100027318", "slide J2-3"], ["3492 lb", "SRC-NTRS-20120016414", "Table 1"],
          ["3,942 lb dry", "SRC-WIKI-J2", "DB-0"], ["3,480 lb", "SRC-PURDUE-J2", "DB-0"], ["3,170 lb", "SRC-ASTRONAUTIX-J2", "DB-0"]],
  resolution="EXPLAINED", kind="definition",
  explanation="Two primary definitions exist (basic vs including accessories). 3,480 is close to 3,492; 3,942 looks like a transposition of 3,492 (INFERRED, not verified); 3,170 matches neither primary value.")
C("CF-DB05-J2-THRUST", engine_id=J2, field_path="performance.thrust_vac", db0_conflict_id="CF-R2_US_CLASSIC-J2-1; CF-US_HIST-10",
  claims=[["230,000 lb nominal vacuum", "SRC-NTRS-20100027318", "slide J2-3"], ["225,000-pound version (qualification; 59 delivered)", "SRC-NTRS-20100027318", "text p.3"],
          ["230 klbf", "SRC-NTRS-20120016414", "Table 1"], ["232,250 lbf", "SRC-WIKI-J2", "DB-0"]],
  resolution="PARTIALLY_RESOLVED", kind="different_epoch",
  explanation="Primary text confirms two ratings (225,000 lb, then 230,000 lb). Which flights used which rating, and the 232,250 lbf figure, are not established by opened documents (AEDC reports blocked).")
C("CF-DB05-J2S-DATES", engine_id=J2S, field_path="history dates", db0_conflict_id="CF-US_HIST-22; CF-TAXONOMY-TAX-5",
  claims=[["J-2S development bar 1965-1972; 1st 27.5:1 test 2/66; 1st 40:1 test 6/68; ready for qual 10/71; final report 3/74", "SRC-NTRS-20100027318", "slide J2-5"]],
  resolution="PARTIALLY_RESOLVED", kind="different_event",
  explanation="Primary timeline shows engine testing from 1966 and 40:1 configuration from 1968; '1969 first successful test' is not supported or contradicted by an opened document.")
C("CF-DB05-J2S-CYCLE", engine_id=J2S, field_path="architecture.cycle",
  claims=[["Tap-off turbine drive cycle; changed to a tap-off cycle to eliminate the gas generator", "SRC-DB05-NTRS-19940016798", "PDF pp.8-9"]],
  resolution="RESOLVED", kind="primary_value_found", explanation="DB-0 held tap_off as SECONDARY_CLAIM only; now Tier A.")
