"""IPD and RD-170 evidence opened in DB-0.5."""
from ledger import A, D, S, T, C, BLOCK

IPD, RD = "ENG-US-IPD", "ENG-SU-RD-170"
W = "SRC-NTRS-IPD-WPB"
D(W, identifier="NTRS 20040084662", title="Facility Activation and Characterization for IPD Workhorse Preburner and Oxidizer Turbopump Hot-Fire Testing at NASA Stennis Space Center (Sass, Raines, Ryan)",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="SRC-NTRS-IPD-20040084662 is the identical file (byte-identical).")
D("SRC-NTRS-IPD-20040084662", identifier="NTRS 20040084662 (= SRC-NTRS-IPD-WPB)", title="(duplicate registry entry)", tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV")
D("SRC-NTRS-IPD-OTPCF", identifier="NTRS 20040129712", title="Facility Activation and Characterization for IPD Oxidizer Turbopump Cold-Flow Testing at NASA Stennis Space Center",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV", note="DB-0 'title not seen' -> verified; facility paper, not mined beyond identity.")
BLOCK("SRC-DTIC-ADA397910", "apps.dtic.mil HTTP 403", "IPD engine schematic lead (SCH-IPD-R2-1) unreachable.")
BLOCK("SRC-DTIC-ADA430218", "apps.dtic.mil HTTP 403", "IPD briefing slides (SCH-IPD-R2-2) unreachable.")
BLOCK("SRC-AF-IPD-2006", "wpafb.af.mil returns HTTP 403")
BLOCK("SRC-NTRS-IPD-20040129712", "registry entry has no URL; same NTRS id opened via SRC-NTRS-IPD-OTPCF")

A(IPD, "performance.thrust", None, "a 250K lbf (1.1 MN) thrust cryogenic hydrogen/oxygen engine technology demonstrator", 250000, "lbf", {"environment": "UNSTATED"}, W, "Abstract and Introduction (PDF p.1)", db0=None)
A(IPD, "architecture.cycle", None, "utilizes a full flow staged combustion engine cycle", "full_flow_staged_combustion", "", {}, W, "Abstract (PDF p.1)", db0=None)
A(IPD, "preburners.OPB.drives", None, "hot combustion gases from an oxygen-rich preburner fed the turbine side of the OTP while liquid oxygen fed the pump side of the OTP", "text", "", {}, W, "PDF p.2", db0=None,
  note="Test-article statement (workhorse preburner standing in for the flight-type IPD oxygen-rich preburner).")
A(IPD, "test_history.component", None, "nine IPD Workhorse Preburner tests ... 12 IPD OTP hot-fire tests ... completed in June 2003", "9 / 12", "tests", {}, W, "Abstract (PDF p.1)", db0=None)
A(IPD, "ignition_start.preburner_igniter", None, "mixture (15%/85% by weight) of Triethylaluminum/Triethylboron (TEA/TEB)", "TEA/TEB 15/85", "% wt", {"scope": "workhorse preburner test"}, W, "PDF p.4", db0=None)

RS = "SRC-NTRS-19910018906"
D(RS, identifier="NTRS 19910018906 (Rockwell International Rocketdyne Division briefing, pp.552-580 of a conference volume)", title="Space transportation propulsion USSR launcher technology, 1990",
  tier="B", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; contractor briefing compiled from public-domain sources (p.12 lists them)", rights_class="VALUES_WITH_ATTRIBUTION",
  note="DB-0 classed it Tier A. Re-graded B: it is a Western analysis; only the transcribed Paris Air Show placard is manufacturer-originated, and that placard was not itself opened.")
LP = "NTRS 19910018906 PDF p.16 'RD-170 Placard' (transcription of the 1989 Paris Air Show display)"
for f, v, val, u in [("performance.thrust_sl", "Poussee au sol - 740 ts (metric tons)", 740, "t"), ("performance.thrust_vac", "Poussee dans le vide - 806 ts (metric tons)", 806, "t"),
                     ("performance.isp_sl", "Impulsion specifique au sol - 308 s", 308, "s"), ("performance.isp_vac", "Impulsion specifique dans le vide - 336 s", 336, "s"),
                     ("performance.pc", "Pression dans la chambre de combustion - 250 kgs/cm2", 250, "kgf/cm2")]:
    A(RD, f, None, v, val, u, {"origin": "manufacturer placard as transcribed by Rockwell"}, RS, LP, db0=None,
      note="Manufacturer value reported second-hand; placard not opened directly. Rockwell's English conversion on the same slide: 1,631,404 / 1,776,908 lb; 3,556 psi.")
A(RD, "architecture.layout", None, "1 turbopump assembly driven by 2 preburners which feed 4 thrust chamber assemblies", "1 TPA / 2 PB / 4 TCA", "", {}, RS, "PDF p.16 (Rockwell text beside the placard)", db0=None)
A(RD, "pumps.shaft_order", None, "single shaft assembly with high pressure fuel pump on the bottom, high pressure oxygen pump in the middle & turbine on top", "text", "", {}, RS, "PDF p.15", db0=None,
  status="INFERRED", note="Rockwell inference from display photographs.")
A(RD, "propellants.mixture_ratio", None, "MR 2.58", 2.58, ":1", {}, RS, "PDF p.16 (Rockwell summary)", db0=None, note="Same document uses MR = 2.47 as its power-balance baseline (PDF p.22, p.26).")
A(RD, "propellants.mixture_ratio", None, "MR = 2.47", 2.47, ":1", {"use": "Rocketdyne power balance baseline"}, RS, "PDF p.22 'ENERGIA Booster Engine Power Balance Analysis by Rocketdyne'", db0=None)

S("SCH-DB05-RD170-RKWL-P19", engine_ids=[RD], source_id=RS, locator="NTRS 19910018906 PDF p.19 (briefing p.569) 'Soviet RD-170 Propulsion System Schematic Diagram (Based on 1989 Paris Air Show Display Photos)'",
  title="Soviet RD-170 Propulsion System Schematic Diagram (Based on 1989 Paris Air Show Display Photos)", kind="THIRD_PARTY_RECONSTRUCTION line schematic (Rockwell), with '?' on uncertain paths",
  viewed_how="rendered at 130 dpi", legible="all labels legible", db0_schematic_id=None,
  note="Not a manufacturer schematic. Edges are 'shown' only in the sense that Rockwell drew them.")

SH = "SHOWN_IN_SCHEMATIC"
LS = "NTRS 19910018906 p.569 (reconstruction)"
T(RD, configuration="RD-170 as reconstructed by Rockwell from 1989 display photos (one of four chambers drawn)", schematic_ids=["SCH-DB05-RD170-RKWL-P19"], text_sources=[RS],
  nodes=[
      ("N-LPOP", "booster_pump", "LP ox pump", "engine", SH, LS),
      ("N-LPFP", "booster_pump", "LP fuel pump", "engine", SH, LS),
      ("N-HPOP", "pump", "HP ox pump", "engine", SH, LS),
      ("N-HPFP", "pump", "HP fuel pump", "engine", SH, LS),
      ("N-KICK", "pump", "Fuel kick pump", "engine", SH, LS),
      ("N-TURB", "turbine", "LOX/fuel turbine (single shaft)", "engine", SH, LS),
      ("N-PB", "preburner_ox_rich", "Ox-rich preburners (2)", "engine", SH, LS),
      ("N-TCA", "thrust_chamber", "Thrust chamber assembly (1 of 4 drawn)", "engine", SH, LS),
      ("N-COOL", "cooling_jacket", "Chamber/nozzle fuel cooling ('?' on nozzle path)", "engine", SH, LS),
  ],
  edges=[
      ("N-LPOP", "N-HPOP", "LOX", "feed", SH, LS),
      ("N-LPFP", "N-HPFP", "RP-1", "feed", SH, LS),
      ("N-HPOP", "N-PB", "LOX", "preburner oxidizer", SH, LS),
      ("N-HPOP", "N-LPOP", "LOX", "LP ox pump turbine drive (liquid)", SH, LS),
      ("N-HPFP", "N-LPFP", "RP-1", "LP fuel pump drive (liquid)", SH, LS),
      ("N-HPFP", "N-KICK", "RP-1", "kick pump", SH, LS),
      ("N-KICK", "N-PB", "RP-1", "preburner fuel", SH, LS),
      ("N-HPFP", "N-COOL", "RP-1", "chamber coolant (to other three chambers too)", SH, LS),
      ("N-COOL", "N-TCA", "RP-1", "fuel to injector", SH, LS),
      ("N-PB", "N-TURB", "ox-rich gas", "turbine drive", SH, LS),
      ("N-TURB", "N-TCA", "ox-rich gas", "turbine exhaust to chambers (to other three chambers too)", SH, LS),
      ("N-TURB", "N-HPOP", "none", "mechanical_shaft", SH, LS),
      ("N-TURB", "N-HPFP", "none", "mechanical_shaft", SH, LS),
  ],
  omissions=["three of four chambers", "valves and control", "start system", "gimbal", "exact LP pump drive taps"],
  note="provenance_class = THIRD_PARTY_RECONSTRUCTION. Every SHOWN_IN_SCHEMATIC here means 'drawn by Rockwell', not 'drawn by NPO Energomash'. Not usable as TOPOLOGY capability without a manufacturer source.")

C("CF-DB05-RD170-PB", engine_id=RD, field_path="preburners.count", db0_conflict_id="CF-R2_USSR-R2-1",
  claims=[["1 turbopump assembly driven by 2 preburners which feed 4 thrust chamber assemblies", RS, "PDF p.16"], ["two Ox-Rich Preburn boxes drawn", RS, "PDF p.19 reconstruction"]],
  resolution="CONFIRMED_SECONDARY", kind="source_grade",
  explanation="The document says 2 preburners, but as Rockwell's reading of display photos. DB-0's 'resolved to 2' stands only at Tier B; no manufacturer document opened.")
C("CF-DB05-RD170-MR", engine_id=RD, field_path="propellants.mixture_ratio", db0_conflict_id="CF-R2_USSR-R2-2",
  claims=[["MR 2.58", RS, "PDF p.16"], ["MR = 2.47 (power balance baseline)", RS, "PDF p.22, p.26"], ["2.63", "SRC-WIKI-RD170", "DB-0"]],
  resolution="UNRESOLVED", kind="intra_document",
  explanation="The opened document itself carries two values; neither is attributed to the placard. A new intra-document conflict, not visible in DB-0.")
C("CF-DB05-RD170-PC", engine_id=RD, field_path="performance.pc", db0_conflict_id="CF-R2_USSR-R2-3",
  claims=[["250 kgs/cm2 (placard transcription)", RS, "PDF p.16"], ["3,556 psi (Rockwell conversion)", RS, "PDF p.16"]],
  resolution="PARTIALLY_RESOLVED", kind="unit",
  explanation="250 kgf/cm2 = 3,556 psi (DERIVED: 250 x 14.223 = 3,556), so the two are one value. 266.7 bar (journalism) remains unsupported.")
