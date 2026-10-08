"""RS-25: schematics viewed, verified topology, conflict outcomes."""
from ledger import A, S, T, C, BLOCK

E2 = "ENG-US-SSME-BLOCK-II"
E2A = "ENG-US-SSME-BLOCK-IIA"

A(E2, "turbines.HPOT.max_allowable_speed", None, "approximately 30,000 rpm", 30000, "rpm", {"kind": "limit (shutdown overspeed)"},
  "SRC-IBIBLIO-SSMEOVERVIEW", "JSC-19041 p.97 §1.5.2 'LO2 Prevalve Timing'", db0=None,
  note="Burst speed 38,000 rpm, same paragraph. DB-0 conflict CF-R2_US_CLASSIC-RS-5 cited 'almost 30,000 rpm' as an operating speed; it is a limit.")

# ---- schematics actually viewed ----
S("SCH-DB05-RS25-JSC19041-F11II", engine_ids=[E2], source_id="SRC-IBIBLIO-SSMEOVERVIEW", locator="JSC-19041 p.1.1-4, Figure 1.1-II",
  title="SSME propellant flow schematic", kind="pictorial flow schematic, no state annotations",
  viewed_how="rendered PDF p.4 at 130 and 200 dpi, rotated", legible="labels legible; thin-line arrowheads only partly legible",
  db0_schematic_id="SCH-RS-25D-R2-4",
  note="Labels: H2 inlet, LPFTP, HPFTP, FPOV, Fuel Preburner, MFV, CCV, Main Injector, MCC, Nozzle, MOV, Oxidizer Preburner, OPOV, HPOTP, LPOTP, O2 inlet. Unlabelled sphere near OPOV not identified.")
S("SCH-DB05-RS25-AIAA972687-F1", engine_ids=[E2], source_id="SRC-AIAA-97-2687", locator="AIAA 97-2687 p.1 (PDF p.3), Figure 1, legend 97PD-038-001",
  title="SSME Propellant Flow Schematic", kind="pictorial flow schematic with state annotations",
  viewed_how="rendered PDF p.3 at 110 and 300 dpi", legible="valve labels legible; numeric state annotations ILLEGIBLE in the NTRS bilevel scan",
  db0_schematic_id="SCH-RS-25D-R2-1",
  note="Configuration not stated (1997; 470,000 lb RPL / 3006 psia = pre-large-throat). No numbers digitised.")
S("SCH-DB05-RS25IIA-BC9804-S19", engine_ids=[E2A], source_id="SRC-ENGINEHISTORY-SSMEORIENT-1998", locator="BC98-04 p.25 (slide 19, 9804168c.ppt)",
  title="Block IIA SSME Propellant Flow Schematic, 104.5% of RPL", kind="pictorial flow schematic with p/T/flow/rpm annotations",
  viewed_how="rendered PDF p.25 at 150 dpi", legible="all annotations legible", db0_schematic_id="SCH-RS-25D-R2-6",
  note="DB-0 'NOT located (TOC only seen)' -> located and viewed. Figure rights: BOEING PROPRIETARY marking; not reproducible.")

# ---- verified topology: Block IIA (schematic slide 19 + text pp.24-27) ----
SH, TX, BO = "SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH"
LS, LT = "BC98-04 p.25 slide 19", "BC98-04 pp.24-27"
T(E2A, configuration="Block IIA at 104.5% RPL", schematic_ids=["SCH-DB05-RS25IIA-BC9804-S19"],
  text_sources=["SRC-ENGINEHISTORY-SSMEORIENT-1998"],
  nodes=[
      ("N-LH2-IN", "engine_inlet", "Hydrogen inlet", "engine", BO, LS),
      ("N-LPFTP-P", "booster_pump", "LPFTP pump", "engine", BO, LS),
      ("N-LPFTP-T", "turbine", "LPFTP turbine (GH2 drive)", "engine", BO, LT),
      ("N-HPFTP-P", "pump", "HPFTP pump", "engine", BO, LS),
      ("N-HPFTP-T", "turbine", "HPFTP turbine", "engine", BO, LS),
      ("N-MFV", "valve", "Main fuel valve (MFV)", "engine", BO, LS),
      ("N-MCC-COOL", "cooling_jacket", "MCC coolant channels (430)", "engine", TX, LT),
      ("N-NOZ-TUBES", "cooling_jacket", "Nozzle coolant tubes (1,080)", "engine", BO, LT),
      ("N-CCV", "valve", "Chamber coolant valve (CCV), nozzle bypass", "engine", BO, LS),
      ("N-PB-FUEL-MIX", "junction", "Nozzle-coolant + CCV merge, preburner fuel supply", "engine", BO, LT),
      ("N-FPB", "preburner_fuel_rich", "Fuel preburner", "engine", BO, LS),
      ("N-OPB", "preburner_fuel_rich", "Oxidizer preburner", "engine", BO, LS),
      ("N-HGM", "manifold", "Hot gas manifold (with coolant spaces)", "engine", BO, LT),
      ("N-MI", "injector", "Main injector", "engine", BO, LS),
      ("N-MCC", "combustion_chamber", "Main combustion chamber", "engine", BO, LS),
      ("N-NOZ", "nozzle", "Nozzle", "engine", SH, LS),
      ("N-AMB", "ambient", "Exhaust", "ambient", SH, LS),
      ("N-LOX-IN", "engine_inlet", "Oxygen inlet", "engine", BO, LS),
      ("N-LPOTP-P", "booster_pump", "LPOTP pump", "engine", BO, LS),
      ("N-LPOTP-T", "turbine_hydraulic", "LPOTP turbine (LOX-driven)", "engine", TX, LT),
      ("N-HPOTP-P", "pump", "HPOTP main pump", "engine", BO, LS),
      ("N-HPOTP-BP", "pump", "Preburner oxidizer boost pump (bottom of HPOTP)", "engine", BO, LT),
      ("N-HPOT", "turbine", "HPOTP turbine", "engine", BO, LS),
      ("N-MOV", "valve", "Main oxidizer valve (MOV)", "engine", BO, LS),
      ("N-FPOV", "valve", "Fuel preburner oxidizer valve (FPOV)", "engine", BO, LS),
      ("N-OPOV", "valve", "Oxidizer preburner oxidizer valve (OPOV)", "engine", BO, LS),
      ("N-HEX", "heat_exchanger", "Heat exchanger coil (LOX -> GOX)", "engine", TX, LT),
      ("N-POGO", "accumulator", "Pogo suppression accumulator (on LP oxidizer duct)", "engine", TX, LT),
      ("N-ASI", "igniter", "Augmented spark igniters (three)", "engine", TX, LT),
      ("N-ET-LH2", "tank_pressurization_port", "ET fuel tank pressurization", "vehicle", TX, LT),
      ("N-ET-LOX", "tank_pressurization_port", "ET oxidizer tank pressurization", "vehicle", TX, LT),
  ],
  edges=[
      ("N-LH2-IN", "N-LPFTP-P", "LH2", "feed", BO, LS),
      ("N-LPFTP-P", "N-HPFTP-P", "LH2", "feed (low-pressure fuel duct)", BO, LT),
      ("N-HPFTP-P", "N-MFV", "LH2", "feed (high-pressure fuel duct)", BO, LT),
      ("N-MFV", "N-MCC-COOL", "H2", "cooling, 19% (split_group F1)", BO, LT),
      ("N-MFV", "N-NOZ-TUBES", "H2", "cooling, 27.5% (split_group F1)", BO, LT),
      ("N-MFV", "N-CCV", "H2", "nozzle bypass, 48.5% (split_group F1)", BO, LT),
      ("N-MCC-COOL", "N-LPFTP-T", "GH2", "turbine drive", BO, LT),
      ("N-LPFTP-T", "N-ET-LH2", "GH2", "tank pressurization tap", BO, LT),
      ("N-LPFTP-T", "N-HGM", "GH2", "HGM coolant, enters both ends", BO, LT),
      ("N-HGM", "N-MI", "GH2", "coolant to dedicated injector cavity", TX, LT),
      ("N-NOZ-TUBES", "N-PB-FUEL-MIX", "H2", "merge (merge_group F2)", BO, LT),
      ("N-CCV", "N-PB-FUEL-MIX", "H2", "merge (merge_group F2)", BO, LT),
      ("N-PB-FUEL-MIX", "N-FPB", "H2", "preburner fuel (50% of fuel)", BO, LT),
      ("N-PB-FUEL-MIX", "N-OPB", "H2", "preburner fuel (26% of fuel)", BO, LT),
      ("N-FPB", "N-HPFTP-T", "H2-rich gas", "turbine drive", BO, LS),
      ("N-OPB", "N-HPOT", "H2-rich gas", "turbine drive", BO, LS),
      ("N-HPFTP-T", "N-HGM", "H2-rich gas", "turbine exhaust", BO, LS),
      ("N-HPOT", "N-HGM", "H2-rich gas", "turbine exhaust", BO, LS),
      ("N-HGM", "N-MI", "H2-rich gas", "hot gas to main injector", BO, LS),
      ("N-MI", "N-MCC", "propellants", "injection", BO, LS),
      ("N-MCC", "N-NOZ", "combustion gas", "expansion", SH, LS),
      ("N-NOZ", "N-AMB", "combustion gas", "exhaust", SH, LS),
      ("N-LOX-IN", "N-LPOTP-P", "LOX", "feed", BO, LS),
      ("N-LPOTP-P", "N-HPOTP-P", "LOX", "feed (low-pressure oxidizer duct)", BO, LT),
      ("N-HPOTP-P", "N-MOV", "LOX", "main flow ~89%", BO, LT),
      ("N-MOV", "N-MI", "LOX", "main oxidizer", BO, LS),
      ("N-HPOTP-P", "N-LPOTP-T", "LOX", "hydraulic turbine drive", BO, LT),
      ("N-LPOTP-T", "N-HPOTP-P", "LOX", "turbine discharge merged with LPOTP pump output", TX, LT),
      ("N-HPOTP-P", "N-HEX", "LOX", "branch to heat exchanger", TX, LT),
      ("N-HEX", "N-ET-LOX", "GOX", "tank pressurization", TX, LT),
      ("N-HEX", "N-POGO", "GOX", "pogo accumulator pressurization", TX, LT),
      ("N-HPOTP-P", "N-HPOTP-BP", "LOX", "11% branch to preburner boost pump", BO, LT),
      ("N-HPOTP-BP", "N-FPOV", "LOX", "preburner oxidizer", BO, LS),
      ("N-HPOTP-BP", "N-OPOV", "LOX", "preburner oxidizer", BO, LS),
      ("N-FPOV", "N-FPB", "LOX", "preburner oxidizer", BO, LS),
      ("N-OPOV", "N-OPB", "LOX", "preburner oxidizer", BO, LS),
      ("N-HPOTP-P", "N-ASI", "LOX", "igniter oxidizer branch", TX, LT),
      ("N-HPFTP-T", "N-HPFTP-P", "none", "mechanical_shaft", BO, LS),
      ("N-HPOT", "N-HPOTP-P", "none", "mechanical_shaft", SH, LS),
      ("N-HPOT", "N-HPOTP-BP", "none", "mechanical_shaft", SH, LS),
      ("N-LPFTP-T", "N-LPFTP-P", "none", "mechanical_shaft", BO, LT),
      ("N-LPOTP-T", "N-LPOTP-P", "none", "mechanical_shaft", BO, LT),
  ],
  omissions=["ASI fuel supply and igniter detail", "helium purge and pneumatic control", "hydraulic actuators",
             "bleed and recirculation valves", "start/shutdown sequence (none shown)", "heat exchanger position on the schematic (unlabelled)",
             "fuel flowmeter labelled but not modelled", "GOX return/recondensation path in the vehicle"],
  note="Edge percentages are fuel- or oxidizer-flow fractions printed in the text (p.24, p.26). HGM-to-injector coolant path and LPOTP-turbine merge are text-only.")

# ---- conflicts ----
C("CF-DB05-RS25-AREARATIO", engine_id=E2, field_path="nozzle.area_ratio", db0_conflict_id="CF-R2_US_CLASSIC-RS-1; CF-ORCH_VERIFY-2",
  claims=[["69:1", "SRC-L3HARRIS-RS25-SPEC", "p.1"], ["77.5 -> 69.5:1 (large throat)", "SRC-NTRS-19860012108", "p.8"],
          ["77.5 to 1", "SRC-IBIBLIO-SSMEOVERVIEW", "JSC-19041 p.1.1-1"]],
  resolution="EXPLAINED", kind="different_configuration",
  explanation="NTRS 19860012108 p.8: the Large Throat MCC 'reduces the nozzle expansion ratio from 77.5 to 69.5:1'; nozzle unchanged. JSC-19041 §1.1.2: Block IIA introduced the larger-throat MCC; AIAA 2002-3581 lists it in the Block 2 package. So 77.5 is pre-Block IIA and JSC-19041's 2003 '77.5 to 1' is stale text. 69 vs 69.5 is rounding.")
C("CF-DB05-RS25-PC", engine_id=E2, field_path="performance.pc", db0_conflict_id="CF-R2_US_CLASSIC-RS-4",
  claims=[["approx. 2,747 psia @RPL; approx. 2,870 @104.5%", "SRC-IBIBLIO-SSMEOVERVIEW", "p.1.1-1"], ["2,994 psia (109% sheet)", "SRC-L3HARRIS-RS25-SPEC", "p.1"],
          ["3006 psia rated chamber pressure @RPL", "SRC-AIAA-97-2687", "p.1-2"], ["3285 -> 3010 psia @109% (large throat)", "SRC-NTRS-19860012108", "p.8"],
          ["2,871 psia @104.5% Block IIA", "SRC-ENGINEHISTORY-SSMEORIENT-1998", "p.25"]],
  resolution="EXPLAINED", kind="different_configuration_and_operating_point",
  explanation="Small-throat RPL 3006 x 1.09 = 3277 ~ 3285 @109%; large throat 2,747 @RPL, 2,870-2,871 @104.5%, 2,994 @109% (2,747 x 1.09 = 2,994 DERIVED). The 1986 study's 3010 @109% is a prediction, 2,994 the flown rating.")
C("CF-DB05-RS25-THRUSTREF", engine_id=E2, field_path="performance.thrust reference condition", db0_conflict_id="CF-US_HIST-18",
  claims=[["approximately 491,000 lbf @104.5% (environment unprinted)", "SRC-NASA-RS25-FS2025", "p.2"],
          ["approximately 470,000 lbs vacuum / 375,000 lbs sea level @RPL", "SRC-IBIBLIO-SSMEOVERVIEW", "p.1.1-1"],
          ["512,300 lb vacuum / 418,000 lb sea level @109%", "SRC-L3HARRIS-RS25-SPEC", "p.1"]],
  resolution="EXPLAINED", kind="definition",
  explanation="470,000 x 1.045 = 491,150 and 470,000 x 1.09 = 512,300 (DERIVED): 491,000 is the vacuum scale.")
C("CF-DB05-RS25-MASS", engine_id=E2, field_path="mechanical.mass", db0_conflict_id="CF-R2_US_CLASSIC-RS-2",
  claims=[["7,774 lb dry", "SRC-L3HARRIS-RS25-SPEC", "p.1"], ["7,775 lbs", "SRC-NASA-RS25-FS2015", "p.2"],
          ["3,515 kg (7,750 lbs.)", "SRC-NASA-RS25-FS2025", "p.1"], ["approximately 7,400 lbs", "SRC-IBIBLIO-SSMEOVERVIEW", "p.1.1-1 (2003)"]],
  resolution="UNRESOLVED", explanation="7,774/7,775/7,750 describe the SLS-adapted engine (insulation, new controller per FS-2015); 7,400 is a 2003 Shuttle-era approximation. Definitions are not printed. Wikipedia 7,004 lb has no primary support among opened documents.")
C("CF-DB05-RS25-PUMPPOWER", engine_id=E2, field_path="pumps.HPFTP.power / pumps.HPOTP.power",
  claims=[["71,140 hp / 23,260 hp", "SRC-L3HARRIS-RS25-SPEC", "p.1"], ["69,000 hp / 25,000 hp", "SRC-NTRS-20180006338", "p.2"]],
  resolution="UNRESOLVED", explanation="Neither prints a power level. DB-0 news values 76,000 / 26,800 hp have no primary support.")
C("CF-DB05-RS25-HPOTPSPEED", engine_id=E2, field_path="pumps.HPOTP.speed_rpm", db0_conflict_id="CF-R2_US_CLASSIC-RS-5",
  claims=[["22,250 rpm (Block IIA, 104.5% RPL)", "SRC-ENGINEHISTORY-SSMEORIENT-1998", "p.25"],
          ["max allowable approximately 30,000 rpm; burst 38,000 rpm", "SRC-IBIBLIO-SSMEOVERVIEW", "p.97"],
          ["28,120 rpm", "SRC-WIKI-RS25", "DB-0 search summary"]],
  resolution="PARTIALLY_RESOLVED", kind="definition",
  explanation="The ~30,000 rpm figure is a limit, not an operating speed. Primary operating speed found only for Block IIA at 104.5%; Block II at 109% not found. 28,120 rpm has no primary support among opened documents.")
C("CF-DB05-RS25-HPFTSPEED", engine_id=E2, field_path="pumps.HPFTP.speed_rpm", db0_conflict_id="CF-R2_US_CLASSIC-RS-6",
  claims=[["34,311 rpm (Rocketdyne HPFTP, Block IIA, 104.5%)", "SRC-ENGINEHISTORY-SSMEORIENT-1998", "p.25"]],
  resolution="UNRESOLVED", explanation="Primary value exists only for the Block IIA (Rocketdyne) HPFTP; the Block II P&W HPFTP speed remains secondary-only.")
BLOCK("SRC-NASA-HOPSON-STS104-FRR-2001", "connection failed (curl exit, HTTP 000) to corpora.tika.apache.org",
      "Hopson STS-104 FRR table values (turbine temperatures) stay unverified.")

D_ = __import__("ledger").D
D_("SRC-NASA-SSME-NPL-DOC", identifier="HAER No. TX-116, Space Transportation System, Part III Space Shuttle Main Engine (page 248 ff.)",
   title="Historic American Engineering Record TX-116: Space Shuttle Main Engine", tier="A",
   rights_checked="HAER documentation for NASA (US Government); no copyright notice on pages read", rights_class="PUBLIC_DOMAIN_GOV",
   note="DB-0 identified it only by URL ('3.pdf'); identity now verified.")
for op, sl, vac in [("OP-RPL", 380000, 470000), ("OP-104.5", 390000, 490000), ("OP-109", 420000, 512000)]:
    A(E2, "performance.thrust_sl", op, f"approximately {sl:,} pounds", sl, "lb", {"environment": "sea_level"}, "SRC-NASA-SSME-NPL-DOC",
      "HAER TX-116 p.248 'Introduction'", db0=("ENG-US-SSME-BLOCK-II", 12, "CONFIRMED") if op == "OP-104.5" else None,
      note="Shuttle-era approximations; configuration not stated (fleet history document).")
    A(E2, "performance.thrust_vac", op, f"approximately {vac:,} pounds ... in a vacuum", vac, "lb", {"environment": "vacuum"}, "SRC-NASA-SSME-NPL-DOC",
      "HAER TX-116 p.248 'Introduction'", db0=None)
C("CF-DB05-RS25-SLTHRUST", engine_id=E2, field_path="performance.thrust_sl",
  claims=[["approx. 380,000 / 390,000 / 420,000 lb at 100 / 104.5 / 109%", "SRC-NASA-SSME-NPL-DOC", "p.248"],
          ["approx. 375,000 lbs at RPL", "SRC-IBIBLIO-SSMEOVERVIEW", "p.1.1-1"], ["418,000 lb at 109%", "SRC-L3HARRIS-RS25-SPEC", "p.1"]],
  resolution="UNRESOLVED", kind="rounding_or_configuration",
  explanation="All are approximations or single-configuration values; 1-1.5% spread. Not reconcilable without a rated-thrust table by block.")

LT8 = "NTRS 19860012108 p.8 (PDF p.8)"
A(E2, "nozzle.area_ratio", None, "reduces the nozzle expansion ratio from 77.5 to 69.5:1", 69.5, ":1", {"configuration": "Large Throat MCC (Block IIA onward)"},
  "SRC-NTRS-19860012108", LT8, db0=("ENG-US-SSME-BLOCK-II", 55, "CONFIRMED"), note="1986 study of the large-throat configuration; nozzle assembly unchanged.")
A(E2, "performance.pc", "OP-109", "The chamber pressure is reduced from 3285 (109% power level) to 3010 psia", 3010, "psia", {"configuration": "Large Throat MCC, predicted"},
  "SRC-NTRS-19860012108", LT8, db0=None, note="Prediction; flown value 2,994 psia (L3Harris).")
A("ENG-US-SSME-BLOCK-I", "nozzle.area_ratio", None, "nozzle expansion ratio ... 77.5", 77.5, ":1", {"configuration": "pre-large-throat MCC"},
  "SRC-NTRS-19860012108", LT8, db0=None, note="Pre-large-throat value; applies to configurations before Block IIA.")
A("ENG-US-SSME-BLOCK-I", "performance.pc", "OP-109", "3285 (109% power level)", 3285, "psia", {"configuration": "pre-large-throat MCC"},
  "SRC-NTRS-19860012108", LT8, db0=None)
