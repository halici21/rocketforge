"""RL10A-3-3 design report pass (2026-10-28): Pratt & Whitney PWA FR-1769, 'Design Report for RL10A-3-3 Rocket
Engine', 28 Feb 1966 (design changes through 31 Jan 1966). The extracted text is clean; the tables used were
also viewed as images. DB-0 held ENG-US-RL10A-3-3 as an UNSOURCED_PLACEHOLDER identity with no values."""
from ledger import A, D, C

R33 = "ENG-US-RL10A-3-3"
R = "SRC-DB05-NTRS-19670005471"

# ------------------------------------------------------------------ document opened in this pass
D(R, identifier="PWA FR-1769, 28 Feb 1966; NASA-CR-80920; contract NAS8-15494; NTRS 19670005471",
  title="Design Report for RL10A-3-3 Rocket Engine", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; contractor report under NASA contract; "
                 "no reproduction notice found in the extracted text",
  rights_class="VALUES_WITH_ATTRIBUTION",
  note="94 pages. Introduction (PDF p.10), Table IV-1 (PDF p.41) and Table V-1 (PDF pp.42-44) viewed as images; "
       "Section I read from text. Values are the contractor's design estimates, not test or flight data.")

# ------------------------------------------------------------------ Introduction (p.ix, PDF p.10)
LI = "PWA FR-1769 p.ix (PDF p.10) 'Introduction' (viewed as image)"
A(R33, "performance.thrust_vac", None, "a rated thrust of 15,000 lb at an altitude of 200,000 ft", 15000, "lb",
  {"environment": "altitude 200,000 ft", "label": "rated thrust"}, R, LI, db0=None)
A(R33, "performance.isp_vac", None, "a nominal specific impulse of 444 sec", 444, "sec",
  {"environment": "altitude 200,000 ft", "mr": 5.0}, R, LI, db0=None)
A(R33, "propellants.mixture_ratio", None, "a nominal oxidizer-to-fuel mixture ratio of 5.0:1", 5.0, ":1",
  {"mr_basis": "oxidizer-to-fuel"}, R, LI, db0=None)
A(R33, "performance.pc", None, "a nominal design chamber pressure of 400 psia", 400, "psia",
  {"pc_station": "UNSTATED"}, R, LI, db0=None, note="Table V-1 of the same report gives 385.2 psia throat total; see CF-DB05-RL10A33-PC.")
A(R33, "nozzle.area_ratio", None, "a nominal nozzle area ratio of 57:1", 57, ":1", {}, R, LI, db0=None)
A(R33, "life.starts_and_duration", None,
  "capable of making at least three starts during a single mission with a nominal running time of 450 sec during a single firing",
  "text", "", {}, R, LI, db0=None)
A(R33, "life.spec", None, "The service life of the engine shall be an accumulated running time of 4000 sec", 4000, "sec", {}, R, LI, db0=None)
A(R33, "architecture.feed", None, "a regeneratively cooled, turbopump-fed engine", "pump_fed", "", {}, R, LI, db0=None)
A(R33, "cooling.thrust_chamber", None, "a regeneratively cooled, turbopump-fed engine", "regenerative", "", {}, R, LI, db0=None)

# ------------------------------------------------------------------ Section I, thrust chamber and piping (text)
A(R33, "architecture.cycle", None,
  "To serve as a heat exchanger to supply turbine power for the propellant pumps ... Thrust chamber exit to turbine inlet; "
  "Turbine discharge to main fuel shutoff valve", "expander_closed", "", {}, R,
  "PWA FR-1769 p.I-17 (PDF p.27) thrust chamber functions; p.I-20 (PDF p.30) propellant piping list", db0=None, status="INFERRED",
  note="The report never prints 'expander'. The chamber jacket powers the turbine and the turbine discharge runs to the main "
       "fuel shutoff valve (not overboard), which is the closed expander cycle DB-0 had only as INFERRED background.")

# ------------------------------------------------------------------ Table IV-1 (p.IV-1, PDF p.41)
L4 = "PWA FR-1769 p.IV-1 (PDF p.41) Table IV-1 'RL10A-3-3 Assembly Weight Breakdown' (viewed as image)"
A(R33, "mechanical.mass_dry_basic", None, "Total basic engine weight (based on 3σ maximum) 289.79", 289.79, "lb",
  {"definition": "basic engine weight, 3-sigma maximum estimate; specification 290.00 lb"}, R, L4, db0=None)
A(R33, "mechanical.mass", None, "Total engine weight 301.19", 301.19, "lb",
  {"definition": "basic engine plus nonchargeable instrumentation, brackets and nonflight items"}, R, L4, db0=None)

# ------------------------------------------------------------------ Table V-1, MR 5.0 column (pp.V-1..V-3, PDF pp.42-44)
L5 = "PWA FR-1769 p.V-1 (PDF p.42) Table V-1 'Estimated RL10A-3-3 Engine Design Data', column 5.0 (viewed as image)"
L5c = "PWA FR-1769 p.V-3 (PDF p.44) Table V-1 (continued), Thrust Chamber Assembly, column 5.0 (viewed as image)"
_T = {"basis": "design estimate", "mr": 5.0, "environment": "altitude 200,000 ft"}
A(R33, "performance.pc", None, "Chamber pressure (throat total), psia 385.2", 385.2, "psia", dict(_T, pc_station="throat total"), R, L5, db0=None)
A(R33, "performance.pc", None, "Chamber pressure (injector face static), psia 394.6", 394.6, "psia",
  dict(_T, pc_station="injector face static"), R, L5, db0=None)
A(R33, "performance.mass_flow_fuel", None, "Fuel flow, lb/sec 5.63", 5.63, "lb/sec", _T, R, L5, db0=None)
A(R33, "performance.mass_flow_oxidizer", None, "Oxidizer flow, lb/sec 28.16", 28.16, "lb/sec", _T, R, L5, db0=None)
A(R33, "pumps.fuel.speed_rpm", None, "Fuel Pump ... Speed, rpm 30,250", 30250, "rpm", _T, R, "PWA FR-1769 p.V-2 (PDF p.43) Table V-1 (continued)", db0=None)
A(R33, "pumps.lox.speed_rpm", None, "Oxidizer Pump ... Speed, rpm 12,100", 12100, "rpm", _T, R, L5, db0=None)
A(R33, "performance.cstar", None, "c* (actual), ft/sec 7626", 7626, "ft/sec", dict(_T, efficiency="98.6 percent of shifting"), R,
  "PWA FR-1769 p.V-2 (PDF p.43) Table V-1 (continued)", db0=None)
A(R33, "chamber.throat_diameter", None, "Chamber throat diameter, in. 5.14", 5.14, "in", {}, R, L5c, db0=None)
A(R33, "chamber.lstar", None, "Characteristic length (L*), in. 38.7", 38.7, "in", {}, R, L5c, db0=None)
A(R33, "nozzle.area_ratio", None, "Effective expansion ratio, A/A* 57.1", 57.1, "", {"definition": "effective"}, R, L5c, db0=None)

C("CF-DB05-RL10A33-PC", engine_id=R33, field_path="performance.pc",
  claims=[["a nominal design chamber pressure of 400 psia", R, "p.ix"],
          ["Chamber pressure (throat total), psia 385.2; (injector face static) 394.6", R, "Table V-1 p.V-1"]],
  resolution="PARTIALLY_RESOLVED", kind="intra_document",
  explanation="The introduction's 'nominal design chamber pressure' of 400 psia names no station; the estimate table gives "
              "385.2 psia throat total and 394.6 psia injector face static at the same 15,000 lb, 5.0:1 rating. 400 psia may "
              "be a rounded specification value, but the report does not say so.")
