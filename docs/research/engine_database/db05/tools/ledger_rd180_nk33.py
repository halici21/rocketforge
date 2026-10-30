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

# ------------------------------------------------------------------ RD-180 manufacturer figures
SFN0, SFN2, GK, PNP = "SRC-SFN-RD180-2000", "SRC-SFN-RD180-2002", "SRC-GLAVKOSMOS-RD180", "SRC-PNP-RD180"
D(SFN0, identifier="spaceflightnow.com/atlas/ac201/000514rd180.html (posted 14 May 2000)", title="RD-180 fact sheet (Atlas 3A AC-201)",
  tier="C", rights_checked="Spaceflight Now page; site copyright; no reuse licence", rights_class="VALUES_WITH_ATTRIBUTION",
  note="'RD-180 facts' table credited 'Source: Pratt & Whitney/NPO Energomash'.")
D(SFN2, identifier="spaceflightnow.com/atlas/ac204/020219rd180.html (posted 19 Feb 2002)", title="RD-180 fact sheet (Atlas 3B AC-204)",
  tier="C", rights_checked="Spaceflight Now page; site copyright; no reuse licence", rights_class="VALUES_WITH_ATTRIBUTION",
  note="The same fact sheet as the 2000 page, word for word; not mined twice.")
D(GK, identifier="trade.glavkosmos.com/rd-180/ (Glavkosmos export catalogue, English page)", title="RD-180 (Glavkosmos product page)", tier="B",
  rights_checked="Roscosmos export agency page; terms of use, no reuse licence", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Parameter table; counts launches to 01.09.2019.")
D(PNP, identifier="pnp.ru (Parlamentskaya Gazeta), article on NPO Energomash's reply to Elon Musk on RD-180 and Raptor",
  title="В «Энергомаше» ответили на слова Илона Маска о превосходстве двигателя Raptor над российским РД-180", tier="D",
  rights_checked="news site; site copyright", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Quotes Energomash engineers; one sentence gives the manufacturer's chamber pressure, another the certification margin.")
LS = "SFN 'RD-180 facts' table (page text), credited Pratt & Whitney/NPO Energomash"
LK = "Glavkosmos RD-180 parameter table (page text)"
_S = {"configuration": "RD-180 (Atlas III fact sheet, 2000)"}
_K = {"configuration": "RD-180 (Glavkosmos catalogue)"}
A(RD, "performance.thrust_sl", None, "Nominal thrust (sea level) 860,200 lb", 860200, "lb", _S, SFN0, LS, db0=None)
A(RD, "performance.thrust_vac", None, "Nominal thrust (vacuum) 933,400 lb", 933400, "lb", _S, SFN0, LS, db0=None)
A(RD, "performance.isp_sl", None, "Specific impulse (sea level) 311.3 sec", 311.3, "s", _S, SFN0, LS, db0=None)
A(RD, "performance.isp_vac", None, "Vacuum specific impulse 337.8 sec", 337.8, "s", _S, SFN0, LS, db0=None)
A(RD, "performance.pc", None, "Chamber pressure 3,722 psia", 3722, "psia", dict(_S, pc_station="UNSTATED"), SFN0, LS, db0=None)
A(RD, "nozzle.area_ratio", None, "Nozzle area ratio 36.87:1", 36.87, ":1", _S, SFN0, LS, db0=None)
A(RD, "propellants.mixture_ratio", None, "Mixture ratio 2.72", 2.72, "(-)", _S, SFN0, LS, db0=None)
A(RD, "performance.throttle_range", None, "Throttle range 40-100%", "40 -> 100", "%", _S, SFN0, LS, db0=None,
  note="The page's prose says 'Forty to 100 percent continuous throttling'; gimbal +-8 degrees; length 140 in, diameter 118 in.")
A(RD, "mechanical.mass", None, "Total system dry weight 11,889 lb", 11889, "lb", dict(_S, definition="total system dry"), SFN0, LS, db0=None)
A(RD, "performance.thrust", None, "Thrust, earth / void, tf 390/423", "390 / 423", "tf", _K, GK, LK, db0=None,
  note="3,825 / 4,148 kN, 859,800 / 932,600 lbf DERIVED.")
A(RD, "performance.isp", None, "Specific impulse, earth / void, s 311 / 339", "311 / 339", "s", _K, GK, LK, db0=None)
A(RD, "performance.pc", None, "Pressure in the combustion chamber, kgf / cm2 261.7", 261.7, "kgf/cm^2", dict(_K, pc_station="UNSTATED"), GK, LK, db0=None,
  note="3,722 psi DERIVED: the fact sheet's value.")
A(RD, "mechanical.mass", None, "Weight, dry / dipped, kg 5480/5950", "5480 / 5950", "kg", dict(_K, definition="dry / filled"), GK, LK, db0=None,
  note="12,081 / 13,117 lb DERIVED.")
A(RD, "performance.throttle_range", None, "Thrust range,% 100-47", "47 -> 100", "%", _K, GK, LK, db0=None)
A(RD, "performance.pc", None, "«Энергомаш» сертифицировал двигатель РД-180 с 10% запасом, то есть давление в его камере сгорания выше 280 атмосфер",
  "> 280", "atm", {"configuration": "RD-180", "basis": "certification margin, not a rating"}, PNP, "pnp.ru article text", db0=None,
  note="Same article: 'по данным производителя НПО «Энергомаш»' 261.7 kgf/cm2.")

C("CF-DB05-RD180-PC", engine_id=RD, field_path="performance.pc", db0_conflict_id="CF-ANCHOR_USSR-1; CF-USSR-4",
  claims=[["Chamber pressure (psia) 3,560 (1995 estimate)", TM, L40],
          ["a chamber pressure of 3,734 psia (2001)", GE, LG],
          ["Chamber pressure 3,722 psia (P&W/NPO Energomash fact sheet)", SFN0, LS],
          ["Pressure in the combustion chamber, kgf / cm2 261.7", GK, LK],
          ["> 280 atm with a 10% certification margin", PNP, "article text"],
          ["266.7 bar", "SRC-KOD-RD180", "DB-0 search summary (never opened)"]],
  resolution="PARTIALLY_RESOLVED", kind="primary_value_found",
  explanation="The manufacturer's value is 261.7 kgf/cm2 (Glavkosmos; quoted again in the 2019 article), which is the "
              "3,722 psia of the P&W/NPO Energomash fact sheet. The 1995 NASA 3,560 psia is a pre-design estimate. The "
              "2001 NASA 3,734 psia (Purdue's figure) is 0.3 percent higher and unexplained. The '> 280 atm' is a "
              "certification margin, not a rating. 266.7 bar was never opened. No source prints a station.")
C("CF-DB05-RD180-MASS", engine_id=RD, field_path="mechanical.mass", db0_conflict_id="CF-ANCHOR_USSR-6",
  claims=[["Dry weight (lb) 11,675 (1995 estimate)", TM, L40], ["Total system dry weight 11,675 lbs. (2001)", GE, LG],
          ["Total system dry weight 11,889 lb (fact sheet, 2000)", SFN0, LS],
          ["Weight, dry / dipped, kg 5480/5950", GK, LK],
          ["11,675 lb ('weight')", "SRC-PURDUE-RD180", "page table (fetched; small page)"],
          ["Масса, сухая/залитая, кг 5480 / 5950 (maker page, 2017)", "SRC-DB05-ENERGOMASH-RD180-2017", "'Технические характеристики' table (archive capture 2017-06-28)"]],
  resolution="UNRESOLVED", kind="different_epoch",
  explanation="Three numbers: 11,675 lb (the 1995 NASA estimate, repeated in 2001 and by Purdue), 11,889 lb (the 2000 "
              "P&W/NPO fact sheet, 'total system dry') and 5,480 kg = 12,081 lb (Glavkosmos, 'dry'). The definitions "
              "differ in wording only; which mass belongs to which build or scope is not stated. NPO Energomash's "
              "own page (archive capture of June 2017) prints the same 5480 / 5950 kg as Glavkosmos.")
C("CF-DB05-RD180-THROTTLE", engine_id=RD, field_path="performance.throttle_range", db0_conflict_id="CF-ANCHOR_USSR-3",
  claims=[["Throttle range (%) 50 (1995 estimate)", TM, L40], ["50 – 100 % continuous throttling (2001)", GE, LG],
          ["Throttle range 40-100% (fact sheet, 2000 and 2002)", SFN0, LS], ["Thrust range,% 100-47", GK, LK]],
  resolution="UNRESOLVED", kind="definition",
  explanation="Three floors in opened documents: 50 percent (NASA 1995 and 2001), 40 percent (P&W/NPO fact sheet) and 47 "
              "percent (Glavkosmos). None says whether its range is qualified, demonstrated or a flight limit. DB-0's "
              "'47%-100%' for the 2002 page is not on it: the 2002 page prints 40-100%.")
C("CF-DB05-RD180-MR", engine_id=RD, field_path="propellants.mixture_ratio", db0_conflict_id="CF-ANCHOR_USSR-5",
  claims=[["Mixture ratio 2.6 (1995 estimate)", TM, L40], ["2.6:1", "SRC-PURDUE-RD180", "page table (fetched; small page)"],
          ["Mixture ratio 2.72 (fact sheet)", SFN0, LS]],
  resolution="EXPLAINED", kind="different_epoch",
  explanation="2.72 is the manufacturers' fact-sheet value for the built engine; 2.6 is the 1995 NASA pre-design "
              "estimate, which Purdue repeats.")
C("CF-DB05-RD180-THRUST", engine_id=RD, field_path="performance.thrust_sl / performance.thrust_vac", db0_conflict_id="CF-ANCHOR_USSR-7",
  claims=[["Nominal thrust (lb) Sea level 827,000 / Vacuum 900,000 (1995 estimate)", TM, L40],
          ["Nominal thrust (sea level) 860,200 lb / (vacuum) 933,400 lb", SFN0, LS],
          ["Thrust, earth / void, tf 390/423", GK, LK],
          ["860,400 lb SL / 933,000 lb vac", "SRC-PURDUE-RD180", "DB-0 search summary"]],
  resolution="EXPLAINED", kind="different_epoch",
  explanation="The fact sheet (860,200 / 933,400 lb) and Glavkosmos (390 / 423 tf = 859,800 / 932,600 lbf DERIVED) agree "
              "within rounding; Purdue's figures are the same rounded. The 1995 NASA 827,000 / 900,000 lb are a "
              "pre-design estimate, and the same study asks for a 5 percent uprate.")
C("CF-DB05-RD180-AREA-RATIO", engine_id=RD, field_path="nozzle.area_ratio", db0_conflict_id="CF-ANCHOR_USSR-4",
  claims=[["Nozzle area ratio 36.87:1", SFN0, LS], ["Area Ratio 36.4:1", "SRC-PURDUE-RD180", "page table (fetched; small page)"]],
  resolution="UNRESOLVED", kind="rating_or_rounding",
  explanation="1.3 percent apart; Purdue cites nothing, and no opened document gives a second manufacturer value.")

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

# ------------------------------------------------------------------ RD-170 thrust (Wave 2 seed; DB-0 CF-USSR-1)
C("CF-DB05-RD170-THRUST", engine_id="ENG-SU-RD-170", field_path="performance.thrust_sl / performance.thrust_vac", db0_conflict_id="CF-USSR-1",
  claims=[["Poussee au sol - 740 ts; Poussee dans le vide - 806 ts (placard, via Rockwell)", "SRC-NTRS-19910018906", "PDF p.16"],
          ["7250 kN SL / 7900 kN vac", "SRC-WIKI-RD170", "DB-0 search summary (never opened)"],
          ["740 tf SL / 806 tf vac (RD-171M)", "SRC-GLAVKOSMOS-RD171M", "DB-0 search summary (never opened)"],
          ["7.8 MN vac (RD-171M)", "SRC-IAC13-20083", "DB-0 search summary (never opened)"],
          ["7900 kN SL (RD-171)", "SRC-LLMPEDIA", "DB-0 search summary (never opened)"]],
  resolution="EXPLAINED", kind="rating_or_rounding",
  explanation="The placard Rockwell transcribed (740 / 806 metric tons) is 7,257 / 7,904 kN DERIVED, the encyclopedia's "
              "figures rounded. The 7.8 MN is the same vacuum value rounded down for the RD-171M, and the 7900 kN 'sea "
              "level' is the vacuum value mislabelled. NASA's 1994 CFD paper (NTRS 19950002748) uses 1,777,000 lbf, "
              "7,904 kN, as its input: the same vacuum figure. No conflict remains beyond rounding; the placard values "
              "stay withheld for their own reason (a transcription).")

# ------------------------------------------------------------------ RD-171M (Glavkosmos; IAC-13 abstract)
R171 = "ENG-RU-RD-171M"
GK171, IAC = "SRC-GLAVKOSMOS-RD171M", "SRC-IAC13-20083"
D(GK171, identifier="trade.glavkosmos.com/rd-171-m/ (Glavkosmos export catalogue, English page)", title="RD-171M (Glavkosmos product page)",
  tier="B", rights_checked="Roscosmos export agency page; terms of use, no reuse licence", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Parameter table; counts launches to 01.09.2019.")
D(IAC, identifier="IAC-13,C4,P,2.p1,x20083 (Levochkin, Pushkarev, Semenov et al., NPO Energomash, 2013); IAF archive abstract page",
  title="LOX-kerosene liquid rocket engine with a thrust of 9.8 MN", tier="B",
  rights_checked="IAF archive abstract; full paper not opened", rights_class="METADATA_ONLY",
  note="Abstract only; NPO Energomash authors.")
LK171 = "Glavkosmos RD-171M parameter table (page text)"
LIAC = "IAC-13 x20083 abstract (page text)"
_K1 = {"configuration": "RD-171M (Glavkosmos catalogue)"}
A(R171, "performance.pc", None, "Pressure in the combustion chamber, kgf / cm2 250", 250, "kgf/cm^2", dict(_K1, pc_station="UNSTATED"), GK171, LK171, db0=None,
  note="Same table: thrust 740 / 806 tf, Isp 309 / 337 s, throttle 105-49 %, 'more than 1000 fire tests'.")
A(R171, "mechanical.mass", None, "Weight, dry / dipped, kg 9300 / 10300", "9300 / 10300", "kg", dict(_K1, definition="dry / filled"), GK171, LK171, db0=None)
A(R171, "performance.pc", None, "the pressure in the combustion chamber=25.9MPa", 25.9, "MPa",
  {"configuration": "RD-171M", "basis": "'reached a certain maximum parameters'"}, IAC, LIAC, db0=None,
  note="Same sentence: Isp in vacuum 3273.2 m/s (333.8 s DERIVED), thrust in vacuum 7.8 MN.")
C("CF-DB05-RD171M-PC", engine_id=R171, field_path="performance.pc", db0_conflict_id="CF-USSR-2",
  claims=[["Pressure in the combustion chamber, kgf / cm2 250", GK171, LK171],
          ["the pressure in the combustion chamber=25.9MPa (maximum reached)", IAC, LIAC]],
  resolution="EXPLAINED", kind="different_operating_point",
  explanation="250 kgf/cm2 is 24.5 MPa DERIVED, the catalogue value; the 2013 abstract calls its 25.9 MPa a maximum the "
              "production engine 'reached', consistent with the catalogue's thrust range up to 105 percent.")
C("CF-DB05-RD171M-MASS", engine_id=R171, field_path="mechanical.mass", db0_conflict_id="CF-USSR-3",
  claims=[["Weight, dry / dipped, kg 9300 / 10300", GK171, LK171], ["9750 kg (RD-170)", "SRC-WIKI-RD170", "DB-0 search summary (never opened)"]],
  resolution="PARTIALLY_RESOLVED", kind="different_variant",
  explanation="The opened catalogue gives 9,300 kg dry for the RD-171M. The 9,750 kg was reported for the RD-170, another "
              "variant, from a page never opened; nothing opened gives an RD-170 mass.")

# ------------------------------------------------------------------ RD-0120 (Buran-Energia; RussianSpaceWeb)
R120 = "ENG-SU-RD-0120"
BE, RSW = "SRC-BURAN-ENERGIA-CARAC", "SRC-RSW-RD0120"
D(BE, identifier="buran-energia.com/energia/energia-carac.php (Vassili Petrovitch)", title="Energia's main characteristics", tier="D",
  rights_checked="page footer 'Copyright (c) 2006-2026 | All Rights Reserved'", rights_class="RESTRICTED_REFERENCE",
  note="Enthusiast site; one characteristics table without sources.")
D(RSW, identifier="russianspaceweb.com/rd0120.html (Anatoly Zak)", title="Energia's super-engine might get a second life", tier="D",
  rights_checked="RussianSpaceWeb page; author's copyright", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Journalistic history of the RD-0120 and its proposed restoration; no sources per value.")
A(R120, "performance.thrust", None, "Thrust on the sea level, tf 147.6 / Thrust in vacuum, tf 190", "147.6 / 190", "tf",
  {"configuration": "Energia core stage engine"}, BE, "Energia characteristics table (page text)", db0=None,
  note="1,447 / 1,863 kN DERIVED.")
A(R120, "mechanical.gimbal_range", None, "the capability to gimbal up to 11 degrees along two perpendicular axis", 11, "deg",
  {"configuration": "Energia core stage engine"}, RSW, "RussianSpaceWeb page text", db0=None)
C("CF-DB05-RD0120-THRUST-GIMBAL", engine_id=R120, field_path="performance.thrust / mechanical.gimbal_range", db0_conflict_id="CF-USSR-14",
  claims=[["Thrust in vacuum, tf 190; on the sea level 147.6", BE, "characteristics table"],
          ["gimbal up to 11 degrees along two perpendicular axis", RSW, "page text"],
          ["1961 kN vac / 1526 kN SL @106%; Isp SL 354 s; gimbal +/-7 deg", "SRC-WIKI-RD0120", "DB-0 search summary (never opened)"],
          ["тяга в пустоте 200 тс (1,961.3 kN DERIVED); удельный импульс 455 с; давление в КС 223 кг/см2", "SRC-DB05-KBKHA-RD0120",
           "kbkha.ru RD0120 page, 'Характеристики' block (fetched 2026-10-29)"]],
  resolution="PARTIALLY_RESOLVED", kind="different_operating_point",
  explanation="190 tf is 1,863 kN; 1,961 kN is 5 percent higher and is tied to a 106 percent level, so the thrust pair may "
              "be two power levels, but neither opened page names its level. The gimbal angle (11 against 7 degrees) is "
              "open: both opened pages are secondary and the 7 degrees was never opened. The manufacturer's page prints 200 tf "
              "in vacuum, which is 1,961.3 kN: the 1,961 kN figure is KBKhA's headline rating, and 190 tf is a lower level that "
              "no manufacturer document names. KBKhA prints no gimbal angle, so that half stays open.")
