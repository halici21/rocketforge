"""LM Descent Engine evidence opened in DB-0.5 (NASA TN D-7143)."""
from ledger import A, D, S, T, C, BLOCK

E = "ENG-US-LMDE"
TN = "SRC-NASA-TND7143"
D(TN, identifier="NASA TN D-7143 (MSC S-349, March 1973); NTRS 19730011150", title="Apollo Experience Report - Descent Propulsion System (Hammock, Currie, Fisher; MSC)",
  tier="A", rights_checked="NASA Technical Note; NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV",
  note="TN number VERIFIED on the report documentation page. SRC-NASA-AER-DPS is the identical file (byte-identical download).")
D("SRC-NASA-AER-DPS", identifier="NTRS 19730011150 = NASA TN D-7143", title="Apollo experience report: Descent propulsion system", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="Duplicate registry entry of SRC-NASA-TND7143 (same PDF).")
BLOCK("SRC-NASA-A14DPSPERF", "nasa.gov ALSJ file returns HTTP 404")
BLOCK("SRC-UNT-MOCAT-946-31648", "mocat.library.unt.edu returns HTTP 403")
BLOCK("SRC-NASA-ALSJ-AERINDEX", "index page opened (HTTP 200) but it is a link list, not evidence", "Index only; no assertion depends on it.")

LR = "TN D-7143 p.8 'Descent Engine' design requirements (PDF p.12)"
A(E, "performance.throttle_ratio", None, "Throttling ratio: 10:1", 10, ":1", {}, TN, LR, db0=None)
A(E, "performance.thrust_max", None, "Maximum-rated thrust: 10 500 lb", 10500, "lb", {"environment": "UNSTATED (vacuum by mission)"}, TN, LR, db0=None)
A(E, "mechanical.gimbal", None, "Gimbaling: ±6° in the Y and Z axes", 6, "deg", {}, TN, LR, db0=None)
A(E, "life.duty_cycle", None, "Duty-cycle life: 1000 sec", 1000, "s", {}, TN, LR, db0=None)
A(E, "feed.regulated_pressure", None, "Pressure fed: 210 psia (later changed to 246 psia)", "210 -> 246", "psia", {}, TN, LR + "; p.4 (PDF p.9)", db0=None)
A(E, "propellants", None, "N2O4 (oxidizer); 50 percent UDMH and 50 percent hydrazine (fuel)", "N2O4 / A-50", "", {}, TN, LR, db0=None)
A(E, "performance.isp_vac", None, "Specific impulse (end of duty cycle): 305 lbf-sec/lbm", 305, "lbf-sec/lbm", {"condition": "end of duty cycle"}, TN, LR, db0=None)
A(E, "performance.fixed_throttle_point", None, "FTP was optimized at 92.5 percent of maximum-rated thrust (10 500 lb)", 92.5, "%", {}, TN, "p.8 (PDF p.12)", db0=None)
A(E, "performance.min_throttle", None, "The minimum-throttle point was 10 percent of the rated thrust", 10, "%", {}, TN, "p.10 (PDF p.14)", db0=None)
A(E, "cooling.zones", None, "thrust chamber was ablatively cooled to an area ratio of 16:1 ... sheet-metal columbium-alloy skirt extending from 16:1 to 47.5:1 ... Cooling of the nozzle extension was by radiation",
  "16 / 47.5", ":1", {}, TN, "p.10 (PDF p.14)", db0=None)
A(E, "control.shutoff_valves", None, "fuel-actuated shutoff valves were parallel-series redundant ball valves", "text", "", {}, TN, "p.10 (PDF p.14)", db0=None)
A(E, "control.throttle_actuator", None, "The throttle actuator was a triple-redundant, electrically driven device", "text", "", {}, TN, "p.10 (PDF p.14)", db0=None)
A(E, "pressurization.she", None, "storing very dense helium at approximately 10 R in a highly thermally insulated pressure vessel ... fuel-to-helium heat exchanger ... second pass ... approximately 40 F",
  "text", "", {"owner": "descent stage"}, TN, "p.4 'Pressurization System' (PDF p.9)", db0=None)
A(E, "pressurization.regulation", None, "a decision was made in October 1966 to use only parallel redundancy in the pressure regulation system (single regulators in each leg)", "text", "", {},
  TN, "p.4 (PDF p.9)", db0=None)

S("SCH-DB05-LMDE-TND7143-F3", engine_ids=[E], source_id=TN, locator="TN D-7143 Figure 3 'The final DPS design', p.4 (PDF p.9)",
  title="The final DPS design", kind="line schematic of descent-stage pressurization and feed", viewed_how="rendered at 150 dpi", legible="all labels legible")
S("SCH-DB05-LMDE-TND7143-F6", engine_ids=[E], source_id=TN, locator="TN D-7143 Figure 6 'Descent-engine schematic, fixed-area helium injection', p.8 (PDF p.13)",
  title="Descent-engine schematic, fixed-area helium injection", kind="engine valve schematic (development configuration)", viewed_how="rendered at 150 dpi",
  legible="all labels legible", db0_schematic_id="SCH-LMDE-R2-1", note="Development (helium-injection) configuration, not the flight variable-area design.")
S("SCH-DB05-LMDE-TND7143-F7", engine_ids=[E], source_id=TN, locator="TN D-7143 Figure 7 'Variable area of the descent engine', p.8 (PDF p.13)",
  title="Variable area of the descent engine", kind="engine valve and injector schematic with flow arrows", viewed_how="rendered at 150 dpi", legible="all labels legible")

SH, TX, BO = "SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH"
L3, L7, LT = "TN D-7143 Fig. 3", "TN D-7143 Fig. 7", "TN D-7143 pp.4-10"
T(E, configuration="LM descent propulsion system, final design (variable-area injector)", schematic_ids=["SCH-DB05-LMDE-TND7143-F3", "SCH-DB05-LMDE-TND7143-F7"],
  text_sources=[TN],
  nodes=[
      ("N-SHE", "pressurant_tank", "Supercritical helium tank (with internal He-He heat exchanger)", "vehicle", BO, L3),
      ("N-AHE", "pressurant_tank", "Ambient helium start tank", "vehicle", SH, L3),
      ("N-FHEX", "heat_exchanger", "Fuel-helium heat exchanger (two helium passes)", "vehicle", BO, L3),
      ("N-REG", "regulator", "Pressure regulators (parallel legs)", "vehicle", BO, L3),
      ("N-SOL", "valve", "Latching solenoid valves", "vehicle", BO, L3),
      ("N-QCV", "check_valve", "Quad check valves", "vehicle", SH, L3),
      ("N-OX-TANKS", "tank", "Oxidizer tanks (2)", "vehicle", SH, L3),
      ("N-FU-TANKS", "tank", "Fuel tanks (2)", "vehicle", SH, L3),
      ("N-TRIM", "orifice", "Trim orifice", "vehicle", SH, L3),
      ("N-FCV", "valve", "Flow-control valves (variable-area cavitating venturi)", "engine", BO, L7),
      ("N-TCA", "actuator", "Thrust-control actuator (links FCVs and injector sleeve)", "engine", BO, L7),
      ("N-SOV", "valve", "Propellant shutoff valve assembly (parallel-series ball valves)", "engine", BO, L7),
      ("N-INJ", "injector", "Variable-area pintle injector (fixed pintle, adjustable sleeve)", "engine", BO, L7),
      ("N-FILM", "orifice", "Fixed-fuel orifice for cooling chamber wall", "engine", SH, L7),
      ("N-TC", "combustion_chamber", "Ablative combustion chamber (to 16:1)", "engine", BO, L7),
      ("N-NOZ", "nozzle_extension", "Radiation-cooled columbium skirt (16:1 to 47.5:1)", "engine", TX, LT),
      ("N-AMB", "ambient", "Exhaust", "ambient", TX, LT),
  ],
  edges=[
      ("N-SHE", "N-FHEX", "He", "helium heating (first and second pass)", BO, L3 + "; p.4"),
      ("N-AHE", "N-REG", "He", "start pressurant (as drawn)", SH, L3),
      ("N-FHEX", "N-REG", "He", "warmed helium to regulators", BO, L3 + "; p.4"),
      ("N-REG", "N-SOL", "He", "regulated pressurant", SH, L3),
      ("N-SOL", "N-QCV", "He", "regulated pressurant", SH, L3),
      ("N-QCV", "N-OX-TANKS", "He", "ullage", SH, L3),
      ("N-QCV", "N-FU-TANKS", "He", "ullage", SH, L3),
      ("N-OX-TANKS", "N-TRIM", "N2O4", "feed", SH, L3),
      ("N-TRIM", "N-FCV", "N2O4", "engine feed", SH, L3),
      ("N-FU-TANKS", "N-FCV", "A-50", "engine feed", SH, L3),
      ("N-FU-TANKS", "N-FHEX", "A-50", "fuel bypass line through heat exchanger", SH, L3),
      ("N-FHEX", "N-FCV", "A-50", "bypass return to fuel feed (as drawn)", SH, L3),
      ("N-FCV", "N-SOV", "propellants", "throttled flow", SH, L7),
      ("N-SOV", "N-INJ", "propellants", "to injector manifolds", BO, L7 + "; p.10"),
      ("N-SOV", "N-FILM", "A-50", "fuel film for wall cooling", SH, L7),
      ("N-FILM", "N-TC", "A-50", "wall film", SH, L7),
      ("N-INJ", "N-TC", "propellants", "hypergolic injection", BO, L7),
      ("N-TC", "N-NOZ", "combustion gas", "expansion", TX, LT),
      ("N-NOZ", "N-AMB", "combustion gas", "exhaust", TX, LT),
      ("N-TCA", "N-FCV", "none", "mechanical linkage", SH, L7),
      ("N-TCA", "N-INJ", "none", "mechanical linkage to adjustable orifice sleeve", SH, L7),
  ],
  omissions=["burst disks, relief valves and squib valves", "propellant gaging", "pilot valves / actuator pressure lines (fuel-actuated SOV)", "thrust neutralizers (vents)",
             "filters", "which fuel-feed point the HEX bypass rejoins (drawn only)"],
  note="Two figures combined: Fig. 3 (stage) and Fig. 7 (engine valves/injector). Throttling is by variable-area cavitating venturis ganged with the injector sleeve.")

C("CF-DB05-LMDE-REPORTNO", engine_id=E, field_path="identity.report_number", db0_conflict_id="CF-ANCHOR_US_MODERN-6",
  claims=[["NASA TN D-7143, MSC S-349, March 1973", TN, "report documentation page (PDF p.2)"]],
  resolution="RESOLVED", kind="primary_value_found", explanation="Report number verified on the document itself.")
