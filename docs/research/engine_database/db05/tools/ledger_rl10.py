"""RL10 evidence opened in DB-0.5."""
from ledger import A, D, S, T, C, BLOCK

R33A, RA42, RB2 = "ENG-US-RL10A-3-3A", "ENG-US-RL10A-4-2", "ENG-US-RL10B-2"

D("SRC-NTRS-19950022693", identifier="NASA CR-195478; AIAA-95-2968; NTRS 19950022693 (contract NAS 3-27186)", title="A Transient Model of the RL10A-3-3A Rocket Engine (Binder, NYMA)",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; export control NO", rights_class="PUBLIC_DOMAIN_GOV", note="DB-0 'title unverified' -> verified.")
D("SRC-NTRS-RL10A33A-MODEL", identifier="NTRS 19950017370", title="An RL10A-3-3A rocket engine model using the rocket engine transient simulator (ROCETS) software",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="Opened; not mined beyond identity.")
D("SRC-NTRS-TM107318", identifier="NASA TM-107318; NTRS 19970010379", title="RL10A-3-3A Rocket Engine Modeling Project", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="Opened (184 pp.); not mined in this pass.")
D("SRC-NTRS-19910018888", identifier="NTRS 19910018888", title="Cryogenic upper stage propulsion: RL10 and derivative engines (P&W viewgraphs)", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="VALUES_WITH_ATTRIBUTION")
D("SRC-NAP-11780", identifier="NRC (2006) doi:10.17226/11780, Appendix D pp.255-260", title="A Review of United States Air Force and Department of Defense Aerospace Propulsion Needs",
  tier="B", rights_checked="National Academies Press web edition; (c) National Academy of Sciences; read online, not reproducible", rights_class="VALUES_WITH_ATTRIBUTION",
  figures_rights="RESTRICTED_REFERENCE", note="Secondary compilation by a review committee (Tier B); values traceable to manufacturers but not first-hand.")
D("SRC-ULA-DIV-INAUGURAL", identifier="AIAA paper PDF hosted by ulalaunch.com", title="Critical events of the inaugural launch of the Boeing Delta IV expendable launch vehicle",
  tier="B", rights_checked="AIAA paper (pp. carry 'American Institute of Aeronautics and Astronautics'); copyright notice not printed on pages read", rights_class="VALUES_WITH_ATTRIBUTION")
D("SRC-ULA-DIV-GPSIIISV02", identifier="ULA mission booklet div_gpsiiisv02_mob.pdf", title="Delta IV GPS III SV02 mission overview", tier="A",
  rights_checked="'Copyright (c) 2019 United Launch Alliance' printed p.1", rights_class="VALUES_WITH_ATTRIBUTION")
BLOCK("SRC-L3HARRIS-RL10-SPEC", "l3harris.com spec-sheet URL and three alternates return HTTP 404/403")
BLOCK("SRC-AIAA-VEHGUIDE-ATLAS", "aiaa.org vehicle-guide URL returns HTTP 404")
BLOCK("SRC-AIAA-VEHGUIDE-DELTA", "aiaa.org vehicle-guide URL returns HTTP 404")
BLOCK("SRC-IAC-2018-43630", "iafastro.directory page returned a 4 kB shell without the paper")

LB = "NASA CR-195478 §3.1 (PDF p.4)"
A(R33A, "pumps.configuration", None, "a two-stage fuel turbine which drives a two-stage fuel pump on a shaft, and a single-stage LOX pump through a gear box", "text", "", {},
  "SRC-NTRS-19950022693", LB, db0=None, note="Confirms gearbox on the LOX pump (SCHEMA_PROPOSAL 'geared RL10 ox pump (to verify)').")
A(R33A, "pumps.fuel.operating_point", "OP-NOMINAL", "a fuel flow of 6 lb/sec is pumped to a pressure of 1100 psia", "6 / 1100", "lb/sec / psia", {}, "SRC-NTRS-19950022693", LB, db0=None)
A(R33A, "pumps.lox.operating_point", "OP-NOMINAL", "30 lb/sec of LOX is pumped to 600 psia", "30 / 600", "lb/sec / psia", {}, "SRC-NTRS-19950022693", LB, db0=None)
A(R33A, "pumps.fuel.speed_rpm", "OP-NOMINAL", "The normal operating speed of the fuel pump is 32000 rpm", 32000, "rpm", {}, "SRC-NTRS-19950022693", LB, db0=None)
A(R33A, "pumps.lox.speed_rpm", "OP-NOMINAL", "the LOX pump speed is 12800 rpm", 12800, "rpm", {}, "SRC-NTRS-19950022693", LB, db0=None)
A(R33A, "performance.pc", "OP-NOMINAL", "the engine's normal operating point of 475 psia and O/F = 5.0", 475, "psia", {"pc_station": "UNSTATED"}, "SRC-NTRS-19950022693", "§4.3 (PDF p.7)", db0=None)
A(R33A, "architecture.cycle", None, "The RL10 engine design (all models) is based on a full expander cycle", "expander_closed", "", {}, "SRC-NTRS-19950022693", "§2.0 (PDF p.4)", db0=None,
  note="Upgrades RL10A-3-3A cycle evidence from INFERRED to REPORTED (Tier A).")
A(R33A, "nozzle.discharge_coefficient", None, "a constant CA of 0.975 was selected", 0.975, "-", {"kind": "model parameter"}, "SRC-NTRS-19950022693", "§4.3 (PDF p.7)", db0=None,
  disposition="NOT_PROMOTED_MODEL_PARAMETER", note="Model-tuning value, not a hardware fact; P&W specified ~0.98.")
L3 = "NTRS 19910018888 PDF p.3 'RL10A-3-3A ENGINE' and 'RL10 EVOLUTION' tables"
A(R33A, "performance.thrust_vac", None, "Vacuum thrust, lb 16,500", 16500, "lb", {"environment": "vacuum"}, "SRC-NTRS-19910018888", L3, db0=None)
A(R33A, "performance.isp_vac", None, "Specific impulse, sec 444.4", 444.4, "s", {"mr": 5.0}, "SRC-NTRS-19910018888", L3, db0=None)
A(R33A, "mechanical.mass", None, "Weight, lb 305", 305, "lb", {}, "SRC-NTRS-19910018888", L3, db0=None)
A(R33A, "propellants.mixture_ratio", None, "Mixture ratio 5:1", 5.0, ":1", {}, "SRC-NTRS-19910018888", L3, db0=None)
A(R33A, "nozzle.area_ratio", None, "Area ratio 61:1", 61, ":1", {}, "SRC-NTRS-19910018888", L3, db0=None)
# DB-2A supplement (2026-10-09): the abstract names the RL10A-3-3A's cycle and
# propellants (the 'full expander' sentence in §2.0 is stated for all RL10 models).
LA = "NASA CR-195478 Abstract (PDF p.3)"
A(R33A, "architecture.cycle", None, "RL10A-3-3A rocket engines ... This hydrogen/oxygen expander cycle engine", "expander", "", {}, "SRC-NTRS-19950022693", LA, db0=None)
A(R33A, "propellants.oxidizer", None, "This hydrogen/oxygen expander cycle engine", "oxygen", "", {}, "SRC-NTRS-19950022693", LA, db0=None)
A(R33A, "propellants.fuel", None, "This hydrogen/oxygen expander cycle engine", "hydrogen", "", {}, "SRC-NTRS-19950022693", LA, db0=None)
A(R33A, "performance.pc", None, "Chamber pressure, psia 475", 475, "psia", {"pc_station": "UNSTATED"}, "SRC-NTRS-19910018888", L3, db0=None,
  note="Same 'RL10A-3-3A ENGINE' table as the thrust, Isp, mixture ratio and area ratio above; the 2026-10-08 pass took Pc only from CR-195478.")
LN = "NRC 2006 (NAP 11780) Appendix D, Table D-4 and text p.256"
A(RA42, "performance.thrust_vac", None, "Thrust (lb) 22,300", 22300, "lb", {"environment": "UNSTATED (vacuum by context)"}, "SRC-NAP-11780", LN, db0=None)
A(RA42, "performance.isp_vac", None, "I sp vacuum (sec) 451", 451, "s", {"environment": "vacuum"}, "SRC-NAP-11780", LN, db0=None)
A(RA42, "nozzle.area_ratio", None, "Nozzle area ratio 84:1", 84, ":1", {}, "SRC-NAP-11780", LN, db0=None)
A(RA42, "propellants.mixture_ratio", None, "Nominal mixture ratio, oxider/fuel 5.5:1", 5.5, ":1", {}, "SRC-NAP-11780", LN, db0=None)
A(RA42, "mechanical.mass", None, "Weight w/nozzle (lb) 386", 386, "lb", {"definition": "with nozzle"}, "SRC-NAP-11780", LN, db0=None)
A(RA42, "mechanical.length", None, "Length, approx. (in.) 91.5; Nozzle extension (in.) 20", "91.5 / 20", "in", {}, "SRC-NAP-11780", LN, db0=None)
A(RA42, "performance.pc", None, "chamber pressure of 610 psi", 610, "psi", {"pressure_basis": "UNSTATED"}, "SRC-NAP-11780", "Appendix D text, RL-10A-4-2 paragraph", db0=None)
A(RA42, "pumps.configuration", None, "equipped with a single turbine and a gearbox that drive the two pumps", "text", "", {}, "SRC-NAP-11780", "Appendix D text", db0=None)
LD2 = "NRC 2006 Appendix D, Table D-2 'Comparison of RL-10 Engine Models', column B-2"
A(RB2, "performance.thrust_vac", None, "Vacuum thrust (lb) 24,750", 24750, "lb", {"environment": "vacuum"}, "SRC-NAP-11780", LD2, db0=None)
A(RB2, "performance.pc", None, "Chamber pressure (psia) 644", 644, "psia", {}, "SRC-NAP-11780", LD2, db0=None)
A(RB2, "performance.pc", None, "chamber pressure of 633 psi", 633, "psi", {}, "SRC-NAP-11780", "Appendix D text, RL-10B-2 paragraph", db0=None)
A(RB2, "performance.isp_vac", None, "Specific impulse (sec) 466.5", 466.5, "s", {}, "SRC-NAP-11780", LD2, db0=None)
A(RB2, "performance.isp_vac", None, "develops an I sp of 465.5 sec", 465.5, "s", {}, "SRC-NAP-11780", "Appendix D text", db0=None)
A(RB2, "nozzle.area_ratio", None, "Expansion ratio 285:1", 285, ":1", {}, "SRC-NAP-11780", LD2, db0=None)
A(RB2, "history.flight_certification", None, "May 1998", "1998-05", "date", {}, "SRC-NAP-11780", LD2, db0=None)
A(RB2, "nozzle.extension", None, "the world's largest carbon-carbon extendible nozzle", "text", "", {}, "SRC-NAP-11780", "Appendix D text", db0=None)
A(RB2, "performance.thrust", None, "Producing 24,750 lb of thrust ... extendible nozzle", 24750, "lb", {"environment": "UNSTATED"}, "SRC-ULA-DIV-INAUGURAL", "p.2 'Vehicle description'", db0=None)
A(RB2, "performance.thrust", None, "a single RL10B-2 engine that produces 24,750 lbf of thrust", 24750, "lbf", {"environment": "UNSTATED"}, "SRC-ULA-DIV-GPSIIISV02", "p.1 'DCSS' paragraph", db0=None)

S("SCH-DB05-RL10A33A-CR195478-F1", engine_ids=[R33A], source_id="SRC-NTRS-19950022693", locator="NASA CR-195478 Figure 1 'RL10A-3-3A Engine System Schematic' (PDF p.13)",
  title="RL10A-3-3A Engine System Schematic", kind="line/pictorial schematic with valve labels and flow arrows",
  viewed_how="rendered at 300 dpi", legible="all labels and arrows legible", db0_schematic_id="SCH-RL10A-3-3A-R2-1")

SH, TX, BO = "SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH"
LS, LT = "CR-195478 Fig. 1", "CR-195478 §§2.0, 3.1, 5.0"
T(R33A, configuration="RL10A-3-3A (Centaur)", schematic_ids=["SCH-DB05-RL10A33A-CR195478-F1"], text_sources=["SRC-NTRS-19950022693"],
  nodes=[
      ("N-FINV", "valve", "Fuel inlet valve (FINV)", "engine", BO, LS),
      ("N-FP1", "pump", "Fuel pump stage 1", "engine", BO, LS),
      ("N-FP2", "pump", "Fuel pump stage 2", "engine", BO, LS),
      ("N-FCV1", "valve", "Interstage cooldown valve (FCV1), vents overboard", "engine", BO, LS),
      ("N-FCV2", "valve", "Fuel-pump discharge cooldown valve, vents overboard", "engine", BO, LS),
      ("N-ORIF", "orifice", "Calibrated orifice", "engine", SH, LS),
      ("N-JACKET", "cooling_jacket", "Thrust chamber / nozzle cooling jacket", "engine", BO, LS),
      ("N-VENT", "venturi", "Venturi", "engine", SH, LS),
      ("N-TURB", "turbine", "Turbine (two-stage)", "engine", BO, LS),
      ("N-TCV", "valve", "Thrust control valve (TCV), turbine bypass", "engine", SH, LS),
      ("N-FSOV", "valve", "Fuel shut-off valve (FSOV)", "engine", BO, LS),
      ("N-OINV", "valve", "Oxidizer inlet valve (OINV)", "engine", BO, LS),
      ("N-LOXP", "pump", "LOX pump (single stage)", "engine", BO, LS),
      ("N-OCV", "valve", "Oxidizer control valve (OCV)", "engine", BO, LS),
      ("N-GEAR", "gearbox", "Gear box", "engine", BO, LS),
      ("N-INJ", "injector", "Injector", "engine", SH, LS),
      ("N-IGN", "igniter", "Ignitor", "engine", SH, LS),
      ("N-TC", "combustion_chamber", "Thrust chamber", "engine", SH, LS),
      ("N-OVBD", "ambient", "Vent overboard", "ambient", BO, LS),
  ],
  edges=[
      ("N-FINV", "N-FP1", "LH2", "feed", SH, LS),
      ("N-FP1", "N-FP2", "LH2", "interstage", SH, LS),
      ("N-FP1", "N-FCV1", "LH2", "interstage cooldown vent", BO, LS + "; §5.0"),
      ("N-FCV1", "N-OVBD", "H2", "vent", BO, LS + "; §5.0"),
      ("N-FP2", "N-FCV2", "LH2", "discharge (cooldown valve tee)", SH, LS),
      ("N-FCV2", "N-OVBD", "H2", "vent", BO, LS + "; §5.0"),
      ("N-FP2", "N-ORIF", "LH2", "pump discharge", SH, LS),
      ("N-ORIF", "N-JACKET", "LH2", "coolant into jacket manifold", BO, LS + "; §2.0"),
      ("N-JACKET", "N-VENT", "GH2", "jacket exit", SH, LS),
      ("N-VENT", "N-TURB", "GH2", "turbine drive (split_group T1)", BO, LS + "; §2.0"),
      ("N-VENT", "N-TCV", "GH2", "turbine bypass (split_group T1)", SH, LS),
      ("N-TCV", "N-FSOV", "GH2", "rejoins turbine exhaust (merge_group T2)", SH, LS),
      ("N-TURB", "N-FSOV", "GH2", "turbine exhaust (merge_group T2)", SH, LS),
      ("N-FSOV", "N-INJ", "GH2", "warm hydrogen to injector", BO, LS + "; §2.0"),
      ("N-OINV", "N-LOXP", "LOX", "feed", SH, LS),
      ("N-LOXP", "N-OCV", "LOX", "discharge", SH, LS),
      ("N-OCV", "N-INJ", "LOX", "oxidizer to injector", SH, LS),
      ("N-INJ", "N-TC", "propellants", "injection", SH, LS),
      ("N-IGN", "N-TC", "spark", "ignition", SH, LS),
      ("N-TURB", "N-FP1", "none", "mechanical_shaft (common shaft)", BO, LS + "; §3.1"),
      ("N-TURB", "N-FP2", "none", "mechanical_shaft (common shaft)", BO, LS + "; §3.1"),
      ("N-TURB", "N-GEAR", "none", "mechanical_shaft", BO, LS + "; §3.1"),
      ("N-GEAR", "N-LOXP", "none", "gear drive (32,000 -> 12,800 rpm at normal point)", BO, LS + "; §3.1"),
  ],
  omissions=["igniter supply and exciter", "tank pressurization taps (not shown)", "LOX tank pressurization (not shown)", "solenoid/pneumatic control", "nozzle exit/ambient node"],
  note="Full (closed) expander: all turbine and bypass hydrogen goes to the injector; only the cooldown valves vent overboard (start/shutdown).")

C("CF-DB05-RL10A33A-MR-ISP", engine_id=R33A, field_path="propellants.mixture_ratio / performance.isp_vac", db0_conflict_id="CF-US_HIST-02",
  claims=[["MR 5:1, Isp 444.4 s (RL10A-3-3A)", "SRC-NTRS-19910018888", "p.3"], ["normal operating point 475 psia and O/F = 5.0", "SRC-NTRS-19950022693", "§4.3"],
          ["A-3-3: Isp 442; A-3-3a: 444", "SRC-NAP-11780", "Table D-2"]],
  resolution="EXPLAINED", kind="different_variant",
  explanation="Two Tier A sources give O/F 5.0 for the RL10A-3-3A. 442.4 s is the RL10A-3-3 value in the P&W evolution table (NAP prints 442 for A-3-3); the DB-0 Purdue pairing of 442.4 s with 5.5:1 mixes variants (INFERRED).")
C("CF-DB05-RL10B2-PC-ISP", engine_id=RB2, field_path="performance.pc / performance.isp_vac", db0_conflict_id="CF-R2_US_CLASSIC-B2-1; CF-R2_US_CLASSIC-B2-3; CF-US_HIST-03",
  claims=[["644 psia; 466.5 s (Table D-2)", "SRC-NAP-11780", "Table D-2"], ["633 psi; 465.5 s (text)", "SRC-NAP-11780", "Appendix D text"]],
  resolution="UNRESOLVED", kind="intra_document",
  explanation="Confirmed as an intra-document inconsistency in the opened page. The 11 psi gap is not a gauge/absolute offset (14.7). Manufacturer data sheet unavailable (HTTP 404).")
C("CF-DB05-RL10B2-THRUST", engine_id=RB2, field_path="performance.thrust_vac", db0_conflict_id="CF-R2_US_CLASSIC-B2-2",
  claims=[["24,750 lb", "SRC-ULA-DIV-INAUGURAL", "p.2"], ["24,750 lbf", "SRC-ULA-DIV-GPSIIISV02", "p.1"], ["24,750 (Table D-2)", "SRC-NAP-11780", "Table D-2"]],
  resolution="RESOLVED", kind="primary_value_found", explanation="Three opened sources agree on 24,750; 24,740/24,800 are rounding/conversion in secondary sources.")
C("CF-DB05-RL10A42-THRUST-ISP", engine_id=RA42, field_path="performance.thrust_vac / isp_vac", db0_conflict_id="CF-R2_US_CLASSIC-A42-2",
  claims=[["22,300 lb; 451 s", "SRC-NAP-11780", "Table D-4"], ["A-4-1 column: 22,300 lb; 610 psia; 451 s (Feb 1994)", "SRC-NAP-11780", "Table D-2"]],
  resolution="PARTIALLY_RESOLVED", explanation="Opened Tier B source agrees with DB-0's L3Harris summary (22,300 / 451). NAP Table D-2 prints the same numbers under 'A-4-1', so the A-4-1/A-4-2 attribution is itself ambiguous. AIAA vehicle guide (450.5 s, 22.9 klbf) unreachable (404).")
