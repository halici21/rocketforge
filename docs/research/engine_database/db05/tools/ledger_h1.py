"""H-1 evidence opened in DB-0.5 (Saturn I SA-10 Functional Systems Description, Vol. VIII)."""
from ledger import A, D, S, T, C

H = "ENG-US-H-1-188K"
SRC = "SRC-NTRS-19650013470"
D(SRC, identifier="SDES-64-415, Volume VIII (Chrysler Corp. Space Division, July 1964, contract NAS 8-4016); NTRS 19650013470",
  title="Saturn I Launch Vehicle SA-10 and Launch Complex 37B Functional Systems Description, Volume VIII: H-1 Engine and Hydraulic System",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; NASA contractor technical manual; no restrictive notice on pages read",
  rights_class="PUBLIC_DOMAIN_GOV",
  note="DB-0 described it as '1965 NASA report on the H-1 engine / S-I(B) propulsion'; it is the SA-10 vehicle-specific functional description (S-I stage, eight engines).")
D("SRC-NTRS-19650013471", identifier="SDES-64-414, Volume VIII; NTRS 19650013471", title="Saturn I SA-8 and LC-37B Functional Systems Description, Vol. VIII: H-1 Engine and Hydraulic System",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="Opened; OCR poor; not mined in this pass beyond identity.")
D("SRC-NTRS-19650013583", identifier="SDES-64-415, Volume I; NTRS 19650013583", title="Saturn I SA-10 and LC-37B Functional Systems Description, Vol. I: RP-1 Fuel System",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV",
  note="DB-0 identifier 'SDES-64-415' is the SA-10 set number shared by all its volumes; this is the stage RP-1 system volume, not an H-1 engine schematic.")

L = "SDES-64-415 Vol. VIII §1.2 p.1.1 (PDF p.5)"
A(H, "performance.thrust_sl", None, "188,000 pounds of thrust (nominal rating) at sea level", 188000, "lb", {"environment": "sea_level", "configuration": "Saturn I SA-10 S-I stage"},
  SRC, L, db0=None, note="Vehicle-specific: SA-10, July 1964 design information.")
A(H, "identity.start_mode", None, "single-start, constant-thrust engine", "text", "", {}, SRC, L, db0=None)
A(H, "thrust_chamber.tube_count", None, "292 longitudinal nickel tubes joined by silver brazing", 292, "tubes", {}, SRC, "§1.2.1.1 (PDF p.5)", db0=None)
A(H, "cooling.path", None, "RP-1 fuel is supplied to alternate tubes (down tubes) from a tapered fuel input manifold. Fuel flows through the down tubes, the return manifold, and the up tubes",
  "text", "", {}, SRC, "§1.2.1.1 (PDF p.5)", db0=None)
A(H, "injector.baffles", None, "A copper ring baffle and six copper radial baffles ... divide the injector face into seven separate areas", "1 ring + 6 radial", "", {}, SRC, "§1.2.1.1", db0=None)
A(H, "turbines.power_speed", None, "two-stage, pressure compounding unit that develops 3793 hp at approximately 32,000 rpm", "3793 hp / 32000 rpm", "hp / rpm", {}, SRC, "§1.2.1.2 (PDF p.6)", db0=None)
A(H, "pumps.gearbox", None, "The gearbox provides the necessary linkage and gear reductions to drive the LOX and fuel pumps at approximately 6537 rpm", 6537, "rpm", {}, SRC, "§1.2.1.2 (PDF p.6)", db0=None,
  note="Confirms geared turbopump (SCHEMA_PROPOSAL listed 'geared H-1' as to-verify). Gear ratio ~32,000/6,537 = 4.9 (DERIVED, not printed).")
A(H, "pumps.type", None, "LOX and fuel pumps are single entry, centrifugal units containing an axial-flow inducer, a radial-flow impeller, and diffuser vanes", "text", "", {}, SRC, "§1.2.1.2", db0=None)
A(H, "pumps.accessory_drive", None, "The dual accessory drives rotate at approximately 4000 rpm. Each outboard engine uses one accessory drive to operate the main pump", 4000, "rpm", {}, SRC, "§1.2.1.2", db0=None,
  note="'main pump' = hydraulic pump for gimbal actuators (outboard engines).")
A(H, "ignition_start.spgg", None, "SPGG ... delivers a gas flow of approximately 4.68 pounds per second for approximately 1 second", "4.68 / 1", "lb/s / s", {}, SRC, "§1.2.1.3 (PDF p.6)", db0=None)
A(H, "gg.mixture_ratio", None, "The LPGG uses a fuel-to-LOX ratio of approximately 2.924 to 1", 2.924, "fuel/LOX", {"mr_basis": "fuel-to-oxidizer (inverse of O/F)"}, SRC, "§1.2.1.4 (PDF p.6)", db0=None)
A(H, "lubrication.fabu", None, "adds approximately 2.75 percent additive (Oronite 262) by weight to RP-1 for gearbox lubrication and cooling", 2.75, "%", {}, SRC, "§1.2.1.5 (PDF p.6)", db0=None)
A(H, "ignition_start.mlv_opening", None, "When the discharge line fuel pressure reaches approximately 230 psig, Main LOX Valve B49 begins to open", 230, "psig", {}, SRC, "§1.2.2.3 (PDF p.9)", db0=None)
A(H, "ignition_start.lpgg_valve_opening", None, "combustion-chamber pressure ... reaches approximately 115 psig, the control valve assembly opens", 115, "psig", {}, SRC, "§1.2.2.3 (PDF p.10)", db0=None)
A(H, "performance.burn_time_sa10", None, "Approximately 150 seconds after engine ignition, a signal ... initiates engine cutoff", 150, "s", {}, SRC, "§1.2.2.5 (PDF p.10)", db0=None)
A(H, "mechanical.gimbal", None, "plus or minus eight-degree square pattern (outboard engines)", 8, "deg", {}, SRC, "§1.1 (PDF p.5)", db0=None)
LF = "SDES-64-415 Vol. VIII Figure 3-1 p.3.3 (PDF p.32), inboard engine panel"
for f, v, val, u in [("feed.fuel_discharge_upstream_orifice_B4", "968 PSIA", 968, "psia"), ("feed.fuel_discharge_downstream_orifice_B4", "930 PSIA", 930, "psia"),
                     ("feed.lox_discharge", "880 PSIA", 880, "psia"), ("feed.lox_downstream_MLV", "830 PSIA LOX", 830, "psia"),
                     ("feed.fuel_manifold_in", "893 PSIA FUEL", 893, "psia"), ("feed.fuel_return", "812 PSIA FUEL", 812, "psia"),
                     ("injector.fuel_injector_pressure", "FUEL INJECTOR 785 PSIA", 785, "psia"), ("injector.lox_injector_pressure", "LOX INJECTOR 790 PSIA", 790, "psia"),
                     ("gg.fuel_bootstrap_line", "728 PSIA (fuel bootstrap line)", 728, "psia")]:
    A(H, f, None, v, val, u, {"operating_point": "UNSTATED (nominal, SA-10)"}, SRC, LF, db0=None, status="DIGITISED",
      note="Callout read visually from the viewed mechanical schematic; line assignment by callout position.")
# DB-2B Wave 1 supplement (2026-10-09): propellants and turbine drive, re-read from
# SDES-64-415 Vol. VIII text.
A(H, "propellants.oxidizer", None, "The H-1 engine is a single-start, constant-thrust engine that uses LOX and RP-1 as propellant", "liquid_oxygen", "", {}, SRC, L, db0=None)
A(H, "propellants.fuel", None, "The H-1 engine is a single-start, constant-thrust engine that uses LOX and RP-1 as propellant", "rp_1", "", {}, SRC, L, db0=None)
A(H, "architecture.cycle", None, "The liquid propellant gas generator (LPGG) burns RP-1 and LOX to generate the hot gases required to operate the two-stage turbine in the turbopump assembly",
  "gas_generator", "", {}, SRC, "§1.2.1.4 (PDF p.6)", db0=None)

S("SCH-DB05-H1-SA10-F31", engine_ids=[H], source_id=SRC, locator="SDES-64-415 Vol. VIII, Figure 3-1 'H-1 Engine and Hydraulic System - Mechanical Schematic', p.3.3 (PDF p.32 fold-out)",
  title="H-1 Engine and Hydraulic System - Mechanical Schematic", kind="mechanical (line) schematic with finding numbers B1..B305, valve states and pressure callouts; inboard, outboard and hydraulic panels",
  viewed_how="rendered fold-out at 300 dpi, rotated, inboard panel viewed at ~180 dpi effective", legible="finding numbers and pressure callouts legible",
  db0_schematic_id="SCH-H-1-R2-1",
  note="DB-0 linked SCH-H-1-R2-1 to the SA-8 volume (NTRS 19650013471) and SCH-H-1-R2-2 to 19650013583 (RP-1 stage system); the H-1 engine schematic viewed here is in the SA-10 Vol. VIII (19650013470).")

SH, TX, BO = "SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH"
LS, LT = "Fig. 3-1 (PDF p.32)", "SDES-64-415 Vol. VIII §1.2 (PDF pp.5-10)"
T(H, configuration="H-1 188,000 lb, Saturn I SA-10 inboard engine", schematic_ids=["SCH-DB05-H1-SA10-F31"], text_sources=[SRC],
  nodes=[
      ("N-TP-LOX", "pump", "LOX pump (B8)", "engine", BO, LS),
      ("N-TP-FUEL", "pump", "Fuel pump (B8)", "engine", BO, LS),
      ("N-GEARBOX", "gearbox", "Turbopump gearbox (B8)", "engine", BO, LT),
      ("N-TURB", "turbine", "Two-stage turbine (B19)", "engine", BO, LS),
      ("N-SPGG", "start_cartridge", "Solid propellant gas generator (B20)", "engine", BO, LS),
      ("N-LPGG", "gas_generator", "Liquid propellant gas generator (B22)", "engine", BO, LS),
      ("N-LPGG-CV", "valve", "LPGG control valve assembly (B23)", "engine", BO, LS),
      ("N-ORIF-B4", "orifice", "Fuel discharge orifice (B4)", "engine", BO, LS),
      ("N-MFV", "valve", "Main fuel valve (B39)", "engine", BO, LS),
      ("N-MLV", "valve", "Main LOX valve (B49)", "engine", BO, LS),
      ("N-FIV", "valve", "Fuel igniter valve (B46)", "engine", BO, LS),
      ("N-HYP", "igniter", "Hypergol cartridge / igniter (B2 area)", "engine", BO, LS),
      ("N-FABU", "lubricant_blender", "Fuel additive blender unit (B15)", "engine", BO, LS),
      ("N-TC-COOL", "cooling_jacket", "Thrust chamber tubes (292, down/up)", "engine", BO, LT),
      ("N-INJ", "injector", "Injector (fuel/LOX alternate rings)", "engine", BO, LS),
      ("N-TC", "combustion_chamber", "Thrust chamber (B28)", "engine", BO, LS),
      ("N-HEX", "heat_exchanger", "Heat exchanger assembly (B30)", "engine", BO, LS),
      ("N-LOX-TANK-PRESS", "tank_pressurization_port", "Inflight LOX tank pressurization (via check valve B173)", "stage", BO, LS),
      ("N-OVBD", "ambient", "Overboard (lube drain, turbine exhaust)", "ambient", BO, LS),
  ],
  edges=[
      ("N-TP-FUEL", "N-ORIF-B4", "RP-1", "fuel discharge (968 -> 930 psia callouts)", BO, LS + "; §1.2.2.3"),
      ("N-ORIF-B4", "N-MFV", "RP-1", "main fuel", BO, LS + "; §1.2.2.3"),
      ("N-MFV", "N-TC-COOL", "RP-1", "fuel manifold -> down tubes -> return manifold -> up tubes", BO, LS + "; §1.2.1.1, §1.2.2.3"),
      ("N-TC-COOL", "N-INJ", "RP-1", "fuel injector manifold", BO, LS + "; §1.2.2.3"),
      ("N-TP-FUEL", "N-FABU", "RP-1", "branch to blender (split_group F1)", BO, LS + "; §1.2.2.3"),
      ("N-FABU", "N-GEARBOX", "RP-1 + Oronite 262", "gearbox lube and cooling", BO, LS + "; §1.2.1.5"),
      ("N-GEARBOX", "N-OVBD", "lubricant", "lube drain via relief valve B13", BO, LS + "; §1.2.2.3"),
      ("N-TP-FUEL", "N-FIV", "RP-1", "primary ignition branch (split_group F1)", BO, LS + "; §1.2.2.3"),
      ("N-FIV", "N-HYP", "RP-1", "pushes hypergol to injector face", BO, LS + "; §1.2.1.1"),
      ("N-HYP", "N-TC", "hypergol", "ignition", BO, LS + "; §1.2.1.1"),
      ("N-TP-FUEL", "N-MLV", "RP-1", "MLV opening control pressure via orifice B1 (split_group F1)", BO, LS + "; §1.2.2.3"),
      ("N-TP-LOX", "N-MLV", "LOX", "LOX discharge (880 psia callout)", BO, LS + "; §1.2.2.3"),
      ("N-MLV", "N-INJ", "LOX", "LOX dome and injector (830 psia callout downstream)", BO, LS + "; §1.2.2.3"),
      ("N-MLV", "N-HEX", "LOX", "branch downstream of MLV via check valve B24 and orifices B29", BO, LS + "; §1.2.2.4"),
      ("N-HEX", "N-LOX-TANK-PRESS", "GOX", "via check valve B173", BO, LS + "; §1.2.2.4"),
      ("N-MLV", "N-LPGG-CV", "LOX", "LOX bootstrap line via orifice B21 (tap downstream of MLV as drawn; text gives no tap point)", BO, LS + "; §1.2.2.3"),
      ("N-TC-COOL", "N-LPGG-CV", "RP-1", "fuel bootstrap line from fuel manifold via orifice B32 (728 psia callout)", BO, LS + "; §1.2.2.3"),
      ("N-LPGG-CV", "N-LPGG", "LOX + RP-1", "GG propellants (opens at ~115 psig chamber pressure)", BO, LS + "; §1.2.2.3"),
      ("N-SPGG", "N-TURB", "solid propellant gas", "start: through part of LPGG to turbine", BO, LS + "; §1.2.2.3"),
      ("N-LPGG", "N-TURB", "hot gas (fuel-rich)", "turbine drive", BO, LS + "; §1.2.2.3"),
      ("N-TURB", "N-OVBD", "turbine exhaust", "turbine exhaust duct", BO, LS + "; §1.2.2.2"),
      ("N-INJ", "N-TC", "propellants", "injection", BO, LS),
      ("N-TURB", "N-GEARBOX", "none", "mechanical_shaft (~32,000 rpm)", TX, "§1.2.1.2"),
      ("N-GEARBOX", "N-TP-LOX", "none", "gear reduction (~6,537 rpm)", TX, "§1.2.1.2"),
      ("N-GEARBOX", "N-TP-FUEL", "none", "gear reduction (~6,537 rpm)", TX, "§1.2.1.2"),
  ],
  omissions=["GN2 purge network (shown, not modelled)", "drain manifolds B44/B47", "fuel bleed-back orifice B48 to suction", "Conax valve B2 shutdown path",
             "outboard engine aspirator B27 and hydraulic system", "position of the heat exchanger in the turbine exhaust (drawn near exhaust; heating medium not stated in text)"],
  note="Inboard engine panel. Outboard engines add the closed-loop hydraulic system and the turbine exhaust aspirator.")

C("CF-DB05-H1-THRUST", engine_id="ENG-US-H-1", field_path="performance.thrust_sl", db0_conflict_id="CF-R2_US_CLASSIC-H1-1",
  claims=[["188,000 pounds (nominal rating) at sea level, SA-10", SRC, "§1.2 p.1.1"]],
  resolution="PARTIALLY_RESOLVED", kind="different_variant",
  explanation="Primary value confirmed for the SA-10 (188K) configuration and attached to ENG-US-H-1-188K, not the family anchor. 200K/205K ratings remain secondary-only.")
