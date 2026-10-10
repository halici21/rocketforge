"""AJ10-137 / Apollo SPS evidence opened in DB-0.5."""
from ledger import A, D, S, T, C, BLOCK

E = "ENG-US-AJ10-137"
TN = "SRC-NASA-TND7375"
D(TN, identifier="NASA TN D-7375 (JSC S-378, August 1973); NTRS 19730023031", title="Apollo Experience Report - Service Propulsion Subsystem (Gibson & Wood, JSC)",
  tier="A", rights_checked="NASA Technical Note; NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV")
D("SRC-NTRS-20100027319", identifier="NTRS 20100027319 (Remembering the Giants, Chapter Four + Appendix G)", title="Aerojet - AJ10-137 Apollo Service Module Engine (Clay Boyce)",
  tier="A", rights_checked="NTRS PUBLIC_USE_PERMITTED", rights_class="VALUES_WITH_ATTRIBUTION", note="DB-0 'title not seen' -> verified. Speaker recollection.")
D("SRC-AEROJET-SPSVALVE-1971", identifier="NTRS 19710025470", title="Apollo Service Propulsion System Rocket Engine Bipropellant Valve Improvement Program (summary report)",
  tier="B", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="Opened; identity verified from NTRS metadata; not mined.")
D("SRC-NTRS-19740022190", identifier="NTRS 19740022190", title="Apollo 16 mission report. Supplement 2: Service Propulsion system final flight evaluation", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="Opened; not mined.")
BLOCK("SRC-DTIC-AD0368743", "apps.dtic.mil HTTP 403")
BLOCK("SRC-NASA-APOLLO-LIQPROP-OVERVIEW", "no URL in DB-0 registry")
BLOCK("SRC-JAXA-TND7375", "JAXA repository record page only (no file); NASA original opened instead", "Same report reached via NTRS.")

L9 = "TN D-7375 p.5 'Block I Configuration - Engine assembly' (PDF p.9)"
A(E, "performance.pc", "OP-BLOCK-I", "chamber pressure of 102 psia", 102, "psia", {"configuration": "Block I"}, TN, L9, db0=None)
A(E, "performance.thrust_vac", "OP-BLOCK-I", "vacuum thrust of 21 500 pounds", 21500, "lb", {"environment": "vacuum", "configuration": "Block I"}, TN, L9, db0=None,
  note="Printed in the Block I section; Block II changed O/F to 1.6:1.")
A(E, "performance.isp_vac", "OP-BLOCK-I", "The average specific impulse was 309 seconds", 309, "s", {"configuration": "Block I"}, TN, L9, db0=None)
A(E, "nozzle.area_ratio", None, "radiation-cooled nozzle (extending from an area ratio of approximately 6:1 to 62.5:1)", "6 -> 62.5", ":1", {}, TN, L9, db0=None)
A(E, "cooling.zones", None, "ablative-cooled thrust chamber, a radiation-cooled nozzle", "ablative + radiation", "", {}, TN, L9, db0=None)
A(E, "life.starts_and_duration", "OP-BLOCK-I", "capable of at least 36 starts and had an engine firing life of 500 seconds", "36 / 500", "starts / s", {}, TN, L9, db0=None)
A(E, "ignition_start.method", None, "Ignition occurred by means of hypergolic reaction in the thrust chamber", "hypergolic", "", {}, TN, L9, db0=None)
A(E, "control.bipropellant_valve", None, "redundant set of series-parallel ball valves ... actuated by pneumatic pressure ... Gaseous nitrogen, stored in redundant tanks", "text", "", {}, TN, L9, db0=None)
A(E, "propellants.mixture_ratio", "OP-BLOCK-II", "operating propellant ratio as 1.6 pounds of oxidizer per pound of fuel", 1.6, ":1", {"configuration": "Block II"}, TN, "p.6 'Block II Configuration' (PDF p.10)", db0=None)
A(E, "propellants.mixture_ratio", "OP-BLOCK-I", "The 2:1 ratio was used in the Block I vehicles", 2.0, ":1", {"configuration": "Block I"}, TN, "p.3 (PDF p.7)", db0=None)
A(E, "pressurization.helium", None, "High-pressure (4400 psia) helium, stored at ambient temperature and regulated to 180 psia", "4400 -> 180", "psia", {"owner": "service module"}, TN, "p.3 (PDF p.7)", db0=None)
A(E, "pressurization.regulators", None, "Each regulator assembly incorporated a primary and a secondary regulator in series ... the secondary regulator was calibrated to regulate at a higher pressure", "text", "", {},
  TN, "pp.3-4 (PDF pp.7-8)", db0=None)
A(E, "feed.tank_limit_pressure", "OP-BLOCK-II", "Block II propellant tanks ... limit pressure of 225 psia, a reduction from the Block I value of 240 psia", "225 (240 Block I)", "psia", {}, TN, "p.6 (PDF p.10)", db0=None)
LB = "NTRS 20100027319 p.63 (PDF p.3)"
A(E, "performance.thrust", None, "The general configuration of the SPS engine was 20,000 pounds of thrust", 20000, "lb", {"configuration": "UNSTATED"}, "SRC-NTRS-20100027319", LB, db0=None)
A(E, "performance.pc", None, "chamber pressure of 100 psi", 100, "psi", {}, "SRC-NTRS-20100027319", LB, db0=None)
A(E, "performance.isp_vac", None, "specific impulse (Isp) of 314.5", 314.5, "s", {}, "SRC-NTRS-20100027319", LB, db0=None)
A(E, "nozzle.area_ratio", None, "area ratio of 62.5:1 (exit area to throat area)", 62.5, ":1", {}, "SRC-NTRS-20100027319", LB, db0=None)
A(E, "propellants", None, "nitrogen tetroxide ... and A-50 ... roughly a fifty-fifty mix (hydrazine/UDMH)", "N2O4 / A-50", "", {}, "SRC-NTRS-20100027319", LB, db0=None,
  note="Transcript also says 'nitrous oxide' as a gloss for N2O4; that gloss is a speaker/transcript error and is not recorded.")
A(E, "feed.engine_inlet_pressure", None, "The inlet pressure was only 165 pounds per square inch absolute (psia)", 165, "psia", {}, "SRC-NTRS-20100027319", LB, db0=None)
A(E, "injector.ring_channels", None, "There were twenty-two ring channels in the injector", 22, "rings", {}, "SRC-NTRS-20100027319", LB, db0=None)
A(E, "life.spec", None, "Specification required 750 seconds duration, or fifty engine restarts during a flight", "750 / 50", "s / starts", {}, "SRC-NTRS-20100027319", LB, db0=None)
A(E, "nozzle.materials", None, "columbium down to about the 40:1 area ratio, then titanium the rest of the way", "text", "", {}, "SRC-NTRS-20100027319", "p.11 (PDF)", db0=None)
# DB-2A supplement (2026-10-09): feed system of the Block I engine assembly.
A(E, "architecture.feed", None, "The SPS engine (fig. 3) was a nonthrottleable, gimbaled, pressure-fed rocket engine", "pressure_fed", "", {"configuration": "Block I"}, TN, L9, db0=None,
  note="TN D-7375 names the oxidizer (N2O4, p.13) but not the fuel; propellant identity for the SPS is printed only in the Aerojet chapter, configuration unstated.")
# Review supplement (2026-10-09): the injector of the Block I engine assembly,
# cited by the production SPS graph.
A(E, "injector.type", None, "a bolt-on aluminum injector", "text", "", {"configuration": "Block I"}, TN, L9, db0=None)
A(E, "propellants.mixture_ratio_definition", None, "the SPS could supply a specific impulse of 3 to 5 seconds higher if the oxidizer-to-fuel weight ratio was 1.6: 1 rather than 2: 1",
  "text", "", {}, TN, "p.3 (PDF p.7)", db0=None)

S("SCH-DB05-SPS-TND7375-F2", engine_ids=[E], source_id=TN, locator="TN D-7375 Figure 2 'Service propulsion subsystem propellant feed assembly', p.4 (PDF p.8)",
  title="Service propulsion subsystem propellant feed assembly", kind="pictorial/line schematic of the SM pressurization and feed system",
  viewed_how="rendered at 160 dpi", legible="all labels legible", db0_schematic_id=None,
  note="Vehicle (service module) system schematic, not the engine internals. DB-0 leads SCH-AJ10-137-R2-1/R2-2 pointed to other documents (one unreachable, one not mined).")

SH, TX, BO = "SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH"
LS, LT = "TN D-7375 Fig. 2", "TN D-7375 pp.3-6"
T(E, configuration="Apollo SPS, Block I text with Fig. 2 feed assembly", schematic_ids=["SCH-DB05-SPS-TND7375-F2"], text_sources=[TN],
  nodes=[
      ("N-HE-TANK", "pressurant_tank", "Helium tanks (2, spherical, 4400 psia)", "vehicle", BO, LS),
      ("N-HE-VALVES", "valve", "Helium isolation valves (2 parallel solenoid poppet)", "vehicle", BO, LS),
      ("N-HE-REG", "regulator", "Helium regulator assemblies (2 parallel; primary+secondary in series)", "vehicle", BO, LS),
      ("N-HE-CHECK", "check_valve", "Helium check-valve assemblies (parallel-series)", "vehicle", BO, LS),
      ("N-HEX-OX", "heat_exchanger", "Propellant/helium heat exchanger, oxidizer line", "vehicle", BO, LS),
      ("N-HEX-FU", "heat_exchanger", "Propellant/helium heat exchanger, fuel line", "vehicle", BO, LS),
      ("N-OX-STOR", "tank", "Oxidizer storage tank", "vehicle", BO, LS),
      ("N-OX-SUMP", "tank", "Oxidizer sump tank", "vehicle", BO, LS),
      ("N-FU-STOR", "tank", "Fuel storage tank", "vehicle", BO, LS),
      ("N-FU-SUMP", "tank", "Fuel sump tank", "vehicle", BO, LS),
      ("N-PUV", "valve", "Propellant-utilization valve (oxidizer)", "vehicle", BO, LS),
      ("N-BIPROP", "valve", "Bipropellant valve (series-parallel ball valves, GN2 actuated)", "engine", TX, LT),
      ("N-INJ", "injector", "Bolt-on aluminum injector", "engine", TX, LT),
      ("N-TC", "combustion_chamber", "Ablative thrust chamber", "engine", TX, LT),
      ("N-NOZ", "nozzle_extension", "Radiation-cooled nozzle extension (6:1 to 62.5:1)", "engine", TX, LT),
      ("N-AMB", "ambient", "Exhaust", "ambient", TX, LT),
  ],
  edges=[
      ("N-HE-TANK", "N-HE-VALVES", "He", "pressurant", BO, LS),
      ("N-HE-VALVES", "N-HE-REG", "He", "pressurant", BO, LS),
      ("N-HE-REG", "N-HE-CHECK", "He", "regulated pressurant", BO, LS),
      ("N-HE-CHECK", "N-HEX-OX", "He", "thermal conditioning (as drawn)", BO, LS),
      ("N-HE-CHECK", "N-HEX-FU", "He", "thermal conditioning (as drawn)", BO, LS),
      ("N-HEX-OX", "N-OX-STOR", "He", "ullage pressurization (as drawn)", SH, LS),
      ("N-HEX-FU", "N-FU-STOR", "He", "ullage pressurization (as drawn)", SH, LS),
      ("N-OX-STOR", "N-OX-SUMP", "N2O4", "series transfer line", BO, LS),
      ("N-FU-STOR", "N-FU-SUMP", "A-50", "series transfer line", BO, LS),
      ("N-OX-SUMP", "N-PUV", "N2O4", "feed through PU valve", BO, LS),
      ("N-PUV", "N-BIPROP", "N2O4", "engine feed", BO, LS + "; " + LT),
      ("N-FU-SUMP", "N-BIPROP", "A-50", "engine feed", BO, LS + "; " + LT),
      ("N-BIPROP", "N-INJ", "N2O4 + A-50", "injection", TX, LT),
      ("N-INJ", "N-TC", "propellants", "hypergolic combustion", TX, LT),
      ("N-TC", "N-NOZ", "combustion gas", "expansion", TX, LT),
      ("N-NOZ", "N-AMB", "combustion gas", "exhaust", TX, LT),
  ],
  omissions=["relief valves and burst diaphragms", "fill/drain/vent disconnects", "propellant gauging", "GN2 actuation system detail",
             "exact helium routing through the propellant-line heat exchangers (drawn; flow sense inferred from text purpose)"],
  note="Feed and pressurization belong to the service module (vehicle), engine owns valve/injector/chamber/nozzle. Pressure-fed, no turbomachinery.")

C("CF-DB05-SPS-THRUST", engine_id=E, field_path="performance.thrust_vac", db0_conflict_id="CF-SPACECRAFT-1",
  claims=[["21 500 pounds vacuum, 102 psia, 309 s (Block I section)", TN, "p.5"], ["20,000 pounds, 100 psi, 314.5 s (general configuration)", "SRC-NTRS-20100027319", "p.63"],
          ["20,500 lbf", "SRC-WIKI-AJ10", "DB-0, not seen"]],
  resolution="PARTIALLY_RESOLVED", kind="different_configuration",
  explanation="The 21,500 lb value is printed for the Block I (O/F 2:1) engine; 20,000 lb is Aerojet's nominal. A Block II flight rating was not found in the pages read; 20,500 lbf remains unsupported by an opened primary document.")
