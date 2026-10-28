"""RD-180 and NK-33 pass (2026-10-28): DB-0 conflicts on two engines no wave seeds, checked against NASA documents
found by NTRS search ('RD-180') and the Aerojet presentation DB-0 cited for the NK-33. Fetched with fetch.py; NASA
TM-108475 Figure 40 viewed as an image, the rest read from the text layer."""
from ledger import A, D, C

RD = "ENG-RU-RD-180"
NK = "ENG-SU-NK-33"
TM = "SRC-DB05-NTRS-19950013232"
GE = "SRC-DB05-NTRS-20010067310"
NAS = "SRC-NAS-DEPS-068011"

D(TM, identifier="NASA-TM-108475; NTRS 19950013232 (compiled by R. Toelle, MSFC, January 1995)",
  title="A 20k Payload Launch Vehicle Fast Track Development Concept Using an RD-180 Engine and a Centaur Upper Stage",
  tier="A", rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; NASA technical memorandum",
  rights_class="PUBLIC_DOMAIN_GOV",
  note="81 pages. An in-house MSFC vehicle study written before the RD-180 existed: its engine data are 'proposed', "
       "'derived' from RD-170 schematics (p.52) or 'scaled off of the RD-170 test data' (Table 5), and the study asks "
       "for a 5 percent uprate. They are estimates, not a manufacturer rating.")
D(GE, identifier="NTRS 20010067310 (H. Richard Ross, Lockheed Martin Stennis Operations, 2001)",
  title="Gas Emission Measurements from the RD 180 Rocket Engine Tests at the NASA Marshall Space Flight Center", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; contractor paper for NASA SSC", rights_class="PUBLIC_DOMAIN_GOV",
  note="10 pages; one bullet list describes the engine tested at MSFC's AETF (p.2). No source given for the list.")
D(NAS, identifier="National Research Council ASEB, 16 Feb 2012 (Jim Long, Aerojet); sites.nationalacademies.org deps_068011.pdf",
  title="Reusability and Hydrocarbon Rocket Engines: Relevant US Industry Experience, Aerojet Perspective", tier="B",
  rights_checked="company presentation hosted by the National Academies; no copyright or reuse notice on the slides read",
  rights_class="RIGHTS_REVIEW_REQUIRED",
  note="24 slides; slide 2 says Aerojet chose not to share technical details openly (ITAR, competition). Slide 12 "
       "(PDF p.13) is the NK-33 performance table.")

# ------------------------------------------------------------------ RD-180, NASA-TM-108475 (1995)
L40 = "NASA-TM-108475 p.52 (PDF p.61) Figure 40 'Characteristics' (viewed as image)"
_P = {"configuration": "proposed RD-180 (MSFC 1995 study; data derived from RD-170 schematics)", "basis": "estimate, not a rating"}
A(RD, "performance.thrust_sl", None, "Nominal thrust (lb) Sea level 827,000", 827000, "lb", _P, TM, L40, db0=None)
A(RD, "performance.thrust_vac", None, "Nominal thrust (lb) Vacuum 900,000", 900000, "lb", _P, TM, L40, db0=None)
A(RD, "performance.isp_sl", None, "Specific impulse (sec) Sea level 309", 309, "s", _P, TM, L40, db0=None)
A(RD, "performance.isp_vac", None, "Specific impulse (sec) Vacuum 337", 337, "s", _P, TM, L40, db0=None)
A(RD, "performance.pc", None, "Chamber pressure (psia) 3,560", 3560, "psia", dict(_P, pc_station="UNSTATED"), TM, L40, db0=None,
  note="Table 5 (p.42) gives the same 3,560 psia at its 100 percent column, with MR 2.6 and 919,792.65 lbf (its thrust "
       "environment not printed; 'uprated 5 percent').")
A(RD, "propellants.mixture_ratio", None, "Mixture ratio 2.6", 2.6, "(-)", _P, TM, L40, db0=None)
A(RD, "performance.throttle_range", None, "Throttle range (%) 50", 50, "%", _P, TM, L40, db0=None,
  note="Printed as one number; the lower limit is read from Table 5, whose columns run 40 to 102 percent.")
A(RD, "mechanical.mass", None, "Dry weight (lb) 11,675", 11675, "lb", dict(_P, definition="dry"), TM, L40, db0=None,
  note="Same figure: wet weight 12,690 lb; length 157 in, diameter 118 in. Table 7 (p.46) books 11,675 lb for the engine.")

# ------------------------------------------------------------------ RD-180, Ross (2001)
LG = "NTRS 20010067310 p.2 engine bullet list (text layer)"
_G = {"configuration": "RD-180 tested at MSFC AETF (as described in 2001)"}
A(RD, "performance.pc", None, "2 thrust chambers with a chamber pressure of 3,734 psia", 3734, "psia", dict(_G, pc_station="UNSTATED"), GE, LG, db0=None)
A(RD, "performance.throttle_range", None, "50 – 100 % continuous throttling", "50 -> 100", "%", _G, GE, LG, db0=None)
A(RD, "mechanical.mass", None, "Total system dry weight 11,675 lbs.", 11675, "lb", dict(_G, definition="total system dry"), GE, LG, db0=None,
  note="The same number as NASA-TM-108475's 1995 estimate.")

C("CF-DB05-RD180-PC", engine_id=RD, field_path="performance.pc", db0_conflict_id="CF-ANCHOR_USSR-1; CF-USSR-4",
  claims=[["Chamber pressure (psia) 3,560 (1995 estimate)", TM, L40],
          ["a chamber pressure of 3,734 psia (2001)", GE, LG],
          ["3722 psia", "SRC-SFN-RD180-2000", "DB-0 search summary (never opened)"],
          ["261.7 kgf/cm2; >280 atm with 10% certification margin", "SRC-PNP-RD180", "DB-0 search summary (never opened)"],
          ["266.7 bar", "SRC-KOD-RD180", "DB-0 search summary (never opened)"]],
  resolution="PARTIALLY_RESOLVED", kind="different_epoch",
  explanation="The 1995 NASA value (3,560 psia) is an estimate for an engine not yet built. The 2001 NASA paper prints "
              "3,734 psia, Purdue's figure. 261.7 kgf/cm2 is 3,722 psi DERIVED, the Spaceflight Now value, so the "
              "unopened Russian figure and the 2001 NASA one differ by 0.3 percent; station and gauge are printed by "
              "none. 266.7 bar and the margin claim stay unopened.")
C("CF-DB05-RD180-MASS", engine_id=RD, field_path="mechanical.mass", db0_conflict_id="CF-ANCHOR_USSR-6",
  claims=[["Dry weight (lb) 11,675 (1995 estimate)", TM, L40], ["Total system dry weight 11,675 lbs. (2001)", GE, LG],
          ["11,675 lb ('weight')", "SRC-PURDUE-RD180", "page table (fetched; small page)"],
          ["5,480 kg dry (12,081 lb derived)", "SRC-GLAVKOSMOS-RD180", "DB-0 search summary (never opened)"]],
  resolution="PARTIALLY_RESOLVED", kind="different_epoch",
  explanation="11,675 lb first appears as the 1995 NASA estimate and is repeated unchanged in 2001 and by Purdue, so "
              "the three are one figure. The 5,480 kg is the manufacturer's (as DB-0 reported it), never opened; "
              "whether the built engine differs from the estimate, or the definitions differ, is not established.")
C("CF-DB05-RD180-THROTTLE", engine_id=RD, field_path="performance.throttle_range", db0_conflict_id="CF-ANCHOR_USSR-3",
  claims=[["Throttle range (%) 50 (1995 estimate)", TM, L40], ["50 – 100 % continuous throttling (2001)", GE, LG],
          ["47%-100%; 40 to 100 percent continuous throttling", "SRC-SFN-RD180-2002", "DB-0 search summary (never opened)"],
          ["100-47%", "SRC-GLAVKOSMOS-RD180", "DB-0 search summary (never opened)"]],
  resolution="UNRESOLVED", kind="different_epoch",
  explanation="Both opened NASA documents give a 50 percent floor; the 47 and 40 percent floors are from pages never "
              "opened. Whether the floor was lowered after 2001 is not shown.")
C("CF-DB05-RD180-MR", engine_id=RD, field_path="propellants.mixture_ratio", db0_conflict_id="CF-ANCHOR_USSR-5",
  claims=[["Mixture ratio 2.6 (1995 estimate)", TM, L40], ["2.6:1", "SRC-PURDUE-RD180", "page table (fetched; small page)"],
          ["2.72", "SRC-SFN-RD180-2000", "DB-0 search summary (never opened)"]],
  resolution="PARTIALLY_RESOLVED", kind="different_epoch",
  explanation="Purdue's 2.6 is the 1995 NASA estimate's figure. The 2.72 was never opened; no opened document gives a "
              "mixture ratio for the built engine.")
C("CF-DB05-RD180-THRUST", engine_id=RD, field_path="performance.thrust_sl / performance.thrust_vac", db0_conflict_id="CF-ANCHOR_USSR-7",
  claims=[["Nominal thrust (lb) Sea level 827,000 / Vacuum 900,000 (1995 estimate)", TM, L40],
          ["860,200 lb SL / 933,400 lb vac", "SRC-SFN-RD180-2000", "DB-0 search summary (never opened)"],
          ["860,400 lb SL / 933,000 lb vac", "SRC-PURDUE-RD180", "DB-0 search summary"]],
  resolution="UNRESOLVED", kind="different_epoch",
  explanation="The 1995 figures are pre-design estimates, and the same study asks for a 5 percent uprate. The two 860k / "
              "933k figures agree with each other but neither was opened as evidence of the delivered rating.")

# ------------------------------------------------------------------ NK-33, Aerojet 2012
LN = "Aerojet ASEB presentation slide 12 'NK-33 Features And Performance' (PDF p.13, text layer)"
_N = {"configuration": "NK-33 (Aerojet's description, 2012)", "operating_point": "100% throttle"}
A(NK, "performance.thrust_vac", "OP-100", "Thrust (vac/SL), klbf 377 / 338", 377, "klbf", dict(_N, environment="vacuum"), NAS, LN, db0=None)
A(NK, "performance.thrust_sl", "OP-100", "Thrust (vac/SL), klbf 377 / 338", 338, "klbf", dict(_N, environment="sea level"), NAS, LN, db0=None)
A(NK, "performance.isp_vac", "OP-100", "ISP (vac/SL), sec 331 / 297", 331, "s", _N, NAS, LN, db0=None)
A(NK, "performance.isp_sl", "OP-100", "ISP (vac/SL), sec 331 / 297", 297, "s", _N, NAS, LN, db0=None)
A(NK, "performance.pc", "OP-100", "Main Chamber Pressure, psi 2,109", 2109, "psi", dict(_N, pc_station="main chamber (gauge or absolute not printed)"), NAS, LN, db0=None)
A(NK, "propellants.mixture_ratio", "OP-100", "Main Chamber Mixture Ratio 2.6:1", 2.6, "(-)", _N, NAS, LN, db0=None,
  note="Same slide: preburner mixture ratio 59; turbine inlet temperature 670 °F.")
A(NK, "performance.throttle_range", None, "Throttle Range 50 - 100%", "50 -> 100", "%", _N, NAS, LN, db0=None)
A(NK, "nozzle.area_ratio", None, "Nozzle Area Ratio 27.7:1", 27.7, ":1", _N, NAS, LN, db0=None)
A(NK, "mechanical.mass", None, "Weight, lbm 2,985", 2985, "lbm", dict(_N, definition="UNSTATED"), NAS, LN, db0=None,
  note="Purdue's AJ26-NK33A page prints 2725 lb; not filed as a conflict (a different, Americanised configuration).")
C("CF-DB05-NK33-PC-THRUST", engine_id=NK, field_path="performance.pc / performance.thrust", db0_conflict_id="CF-R2_USSR-R2-4",
  claims=[["Thrust (vac/SL), klbf 377 / 338; Main Chamber Pressure, psi 2,109", NAS, LN],
          ["Thrust in Vacuum 339,000 lbf; Chamber Pressure 2109 psia (AJ26-NK33A)", "SRC-PURDUE-AJ26", "page table"],
          ["14.83 MPa (2,151 psi); 1510 kN SL; 1680 kN vac", "SRC-WIKI-NK33", "DB-0 search summary (never opened)"]],
  resolution="PARTIALLY_RESOLVED", kind="definition",
  explanation="Aerojet prints 338 klbf sea level and 377 klbf vacuum. Purdue's 339,000 lbf labelled 'vacuum' is the "
              "sea-level figure: its own Isp pair (331 / 297) is Aerojet's, so the label is the slip. 2,109 is printed "
              "by both (psi by Aerojet, psia by Purdue). The 14.83 MPa (2,151 psi) was never opened; whether it is "
              "another station or absolute against gauge is not established.")
