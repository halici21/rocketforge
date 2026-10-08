"""AJ10-190 / Shuttle OMS engine evidence opened in DB-0.5."""
from ledger import A, D, S, T, C, BLOCK

E = "ENG-US-AJ10-190"
WB, TM, EV = "SRC-USA-OMS21002", "SRC-JSC-19950", "SRC-DB05-NTRS-19850008634"
D(WB, identifier="USA006500 Rev. A (OMS 21002, 10 Oct 2006)", title="Orbital Maneuvering System Workbook OMS 21002", tier="A",
  rights_checked="p.1: 'Copyright (c) 2004 by United Space Alliance, LLC ... sponsored by NASA under Contract NNJ06VA01C. The U.S. Government retains a paid-up, nonexclusive, irrevocable worldwide license ... All other rights are reserved by the copyright owner.'",
  rights_class="VALUES_WITH_ATTRIBUTION", figures_rights="RIGHTS_REVIEW_REQUIRED")
D(TM, identifier="JSC-19950 (OMS 2102, April 1995)", title="Orbital Maneuvering System Orbiter Systems Training Manual", tier="A",
  rights_checked="NASA JSC training manual; no copyright notice on cover", rights_class="PUBLIC_DOMAIN_GOV")
D(EV, identifier="NTRS 19850008634", title="Orbital Maneuvering system design evolution", tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV",
  note="NEW source (not in DB-0).")
D("SRC-NTRS-OMS-1974", identifier="NTRS 19740026212", title="Orbital maneuvering subsystem functional path analysis for performance monitoring fault detection and annunciation",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV",
  note="DB-0 title 'Shuttle OMS pressure-fed propulsion subsystem description' and 'identity unverified' -> actual title verified; not mined.")
D("SRC-NASA-JSC-CN-7650", identifier="JSC-CN-7650; NTRS 20100038459", title="On-Orbit Propulsion OMS/RCS", tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED",
  rights_class="PUBLIC_DOMAIN_GOV", note="NTRS id 20100038459 VERIFIED (DB-0 'possibly ... unverified'). Slides; not mined.")
BLOCK("SRC-NTRS-19740026212", "registry entry has no URL; same NTRS id opened via SRC-NTRS-OMS-1974")

A(E, "performance.thrust", None, "Each OMS engine produces 6000 lbs of thrust", 6000, "lb", {"environment": "UNSTATED (vacuum by use)"}, WB, "USA006500 Rev. A, Section 1 introduction (PDF p.11)", db0=None)
A(E, "performance.isp_vac", None, "with an ISP (Specific Impulse) of 313 seconds", 313, "s", {}, WB, "USA006500 Rev. A (PDF p.11)", db0=None)
A(E, "performance.thrust", None, "Each OMS engine produces 6000 lb of thrust", 6000, "lb", {}, TM, "JSC-19950 (PDF p.8)", db0=None)
A(E, "performance.isp_vac", None, "ISP (Specific Impulse) of 313 seconds", 313, "s", {}, TM, "JSC-19950 (PDF p.8)", db0=None)
A(E, "performance.pc", None, "normal Pc during a burn is between 100 and 106 percent, which corresponds to a pressure of approximately 130 psia", 130, "psia", {"note": "100-106% band"}, WB, "USA006500 p.2-4 (PDF p.19)", db0=None,
  note="JSC-19950 (1995) prints '100 and 102 percent' for the same sentence (PDF p.16).")
A(E, "control.bipropellant_valves", None, "two fuel valves in series and two oxidizer valves in series ... Each fuel valve is mechanically linked to an oxidizer valve ... driven open ... by pneumatic pistons ... held in the closed position by springs",
  "text", "", {}, WB, "USA006500 §2.1 p.2-2 (PDF p.17)", db0=None)
A(E, "cooling.path", None, "the oxidizer line runs directly to the engine injector plate. The fuel, however, is used to cool the engine ... routed through a cooling jacket around the thrust chamber", "text", "", {},
  WB, "USA006500 p.2-3 (PDF p.18)", db0=None)
A(E, "cooling.channels", None, "regeneratively cooled by fuel flowing in a single pass through nontubular coolant channels ... 120 longitudinal, milled, rectangular-shaped passages", 120, "channels", {}, EV,
  "NTRS 19850008634 (PDF pp.11-12)", db0=None)
A(E, "nozzle.area_ratio", None, "thrust chamber assembly extends to a 6:1 area ratio ... nozzle extended from the regeneratively cooled interface to an area ratio of 55:1", "6 / 55", ":1", {}, EV, "PDF pp.10-12", db0=None)
A(E, "nozzle.extension", None, "radiation cooled and was constructed entirely of columbium", "text", "", {}, EV, "PDF p.12", db0=None)
A(E, "injector.type", None, "like-on-like pattern composed of eight photo-etched platelets ... acoustic cavities", "text", "", {}, EV, "PDF p.11", db0=None)
A(E, "thrust_chamber.geometry", None, "distance from the injection plane to the throat is 15.9 inches", 15.9, "in", {}, EV, "PDF p.12", db0=None)

S("SCH-DB05-OMS-WB-F21", engine_ids=[E], source_id=WB, locator="USA006500 Rev. A Figure 2-1 'OMS schematic' p.2-1 (PDF p.16)", title="OMS schematic",
  kind="engine line schematic with valves, cooling jacket and flow arrows", viewed_how="rendered at 140 dpi", legible="all labels and arrows legible")
S("SCH-DB05-OMS-WB-F210", engine_ids=[E], source_id=WB, locator="USA006500 Rev. A Figure 2-10 'Propellant and helium supply schematic' p.2-12 (PDF p.27)",
  title="Propellant and helium supply schematic", kind="pod pressurization/feed line schematic", viewed_how="rendered at 140 dpi", legible="all labels legible")

SH, TX, BO = "SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH"
L1, L10, LT = "USA006500 Fig. 2-1", "USA006500 Fig. 2-10", "USA006500 §§2.1-2.2"
T(E, configuration="Shuttle OMS pod (one engine)", schematic_ids=["SCH-DB05-OMS-WB-F21", "SCH-DB05-OMS-WB-F210"], text_sources=[WB, EV],
  nodes=[
      ("N-HE", "pressurant_tank", "Helium tank (one per pod)", "vehicle", BO, L10),
      ("N-HEV", "valve", "Helium press valves A and B (parallel)", "vehicle", BO, L10),
      ("N-REG", "regulator", "Dual pressure regulators (each leg)", "vehicle", SH, L10),
      ("N-VIV", "valve", "Vapor isolation valves (oxidizer leg)", "vehicle", SH, L10),
      ("N-CK", "check_valve", "Check valves", "vehicle", SH, L10),
      ("N-OXT", "tank", "Oxidizer tank", "vehicle", SH, L10),
      ("N-FUT", "tank", "Fuel tank", "vehicle", SH, L10),
      ("N-TIV", "valve", "Tank isolation valves A/B (parallel)", "vehicle", BO, L10),
      ("N-BPV1", "valve", "Bipropellant valve 1 (linked fuel+ox ball valves)", "engine", BO, L1),
      ("N-BPV2", "valve", "Bipropellant valve 2 (linked fuel+ox ball valves)", "engine", BO, L1),
      ("N-N2", "actuator_supply", "GN2 to valve pistons (engine control valves)", "engine", BO, L1),
      ("N-JACKET", "cooling_jacket", "Cooling jacket (single pass, 120 channels, to epsilon 6)", "engine", BO, L1),
      ("N-INJ", "injector", "Injector plate", "engine", SH, L1),
      ("N-TC", "combustion_chamber", "Thrust chamber", "engine", SH, L1),
      ("N-NOZ", "nozzle_extension", "Columbium radiation-cooled nozzle (6:1 to 55:1)", "engine", BO, L1),
      ("N-AMB", "ambient", "Exhaust", "ambient", SH, L1),
  ],
  edges=[
      ("N-HE", "N-HEV", "He", "pressurant", SH, L10),
      ("N-HEV", "N-REG", "He", "pressurant", SH, L10),
      ("N-REG", "N-VIV", "He", "to oxidizer leg", SH, L10),
      ("N-VIV", "N-CK", "He", "oxidizer leg", SH, L10),
      ("N-REG", "N-CK", "He", "fuel leg", SH, L10),
      ("N-CK", "N-OXT", "He", "ullage", SH, L10),
      ("N-CK", "N-FUT", "He", "ullage", SH, L10),
      ("N-OXT", "N-TIV", "N2O4", "feed", SH, L10),
      ("N-FUT", "N-TIV", "MMH", "feed", SH, L10),
      ("N-TIV", "N-BPV1", "N2O4 + MMH", "to bipropellant valves", SH, L10),
      ("N-BPV1", "N-BPV2", "N2O4 + MMH", "series valves", SH, L1),
      ("N-BPV2", "N-INJ", "N2O4", "oxidizer directly to injector", BO, L1 + "; p.2-3"),
      ("N-BPV2", "N-JACKET", "MMH", "fuel to aft end of cooling jacket", BO, L1 + "; p.2-3"),
      ("N-JACKET", "N-INJ", "MMH", "warmed fuel to injector", SH, L1),
      ("N-INJ", "N-TC", "propellants", "hypergolic injection", SH, L1),
      ("N-TC", "N-NOZ", "combustion gas", "expansion", SH, L1),
      ("N-NOZ", "N-AMB", "combustion gas", "exhaust", SH, L1),
      ("N-N2", "N-BPV1", "GN2", "pneumatic piston actuation", BO, L1 + "; p.2-2"),
      ("N-N2", "N-BPV2", "GN2", "pneumatic piston actuation", BO, L1 + "; p.2-2"),
      ("N-N2", "N-JACKET", "GN2", "post-burn purge of fuel line and jacket", TX, "USA006500 p.2-7 (PDF p.22)"),
  ],
  omissions=["crossfeed lines and valves between pods", "relief valves (shown, not modelled)", "propellant gauging", "thermal control heaters",
             "gimbal actuators (TVC)", "N2 tank, regulator and accumulator detail"],
  note="Two figures combined at the bipropellant-valve interface. Vehicle (pod) owns tanks and pressurization.")

C("CF-DB05-OMS-ISP", engine_id=E, field_path="performance.isp_vac", db0_conflict_id="CF-SPACECRAFT-3",
  claims=[["313 seconds", WB, "PDF p.11"], ["313 seconds", TM, "PDF p.8"], ["316 s / 313 s", "SRC-WIKI-OMS", "DB-0"]],
  resolution="RESOLVED", kind="primary_value_found", explanation="Two Tier A training documents (1995, 2006) print 313 s. 316 s has no primary support among opened documents.")
C("CF-DB05-OMS-PCBAND", engine_id=E, field_path="performance.pc normal band",
  claims=[["100 and 106 percent ... approximately 130 psia", WB, "PDF p.19"], ["100 and 102 percent ... approximately 130 psia", TM, "PDF p.16"]],
  resolution="EXPLAINED", kind="different_epoch", explanation="Same sentence in the 1995 and 2006 editions; band widened between editions. The ~130 psia reference value is unchanged.")
