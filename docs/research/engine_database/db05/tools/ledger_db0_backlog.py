"""DB-0 conflict backlog pass (2026-10-28): the DB-0 conflicts on US engines that DB-0.5 had not reviewed, checked
against documents already opened and against the secondary pages DB-0 cited, fetched now with fetch.py and read from
their text. The Smithsonian F-1 record refused the download (HTTP 403) and was not retried."""
from ledger import A, D, C, BLOCK

J2 = "ENG-US-J-2"
F1 = "ENG-US-F-1"
H1 = "ENG-US-H-1"
LR87_5 = "ENG-US-LR87-AJ-5"
LR87_7 = "ENG-US-LR87-AJ-7"
LR91_5 = "ENG-US-LR91-AJ-5"
LR91_11 = "ENG-US-LR91-AJ-11"
EH1 = "SRC-ENGINEHISTORY-F1"
PH1 = "SRC-PURDUE-H1"
P91 = "SRC-PURDUE-LR91AJ11"
AX = "SRC-ASTRONAUTIX-LR87"
TMS = "SRC-TMS-TITAN2"

# ------------------------------------------------------------------ documents
D(EH1, identifier="enginehistory.org/Rockets/RPE08.11/OneSecond.shtml (Aircraft Engine Historical Society)",
  title="One Second in the Life of the Rocketdyne F-1 Rocket Engine", tier="D",
  rights_checked="page footer copyright Aircraft Engine Historical Society, Inc.; no reuse licence",
  rights_class="VALUES_WITH_ATTRIBUTION",
  note="Popular essay; no references. Same society as RPE08.12 (18,500 lb, repeated here).")
D(PH1, identifier="engineering.purdue.edu/AAE/research/propulsion/Info/rockets/liquids/h1", title="Apollo H-1 (Rocketdyne)", tier="D",
  rights_checked="Purdue University web page; no reuse licence; no source cited for the table", rights_class="VALUES_WITH_ATTRIBUTION",
  note="One 'Engine statistics' table without a rating name, a date or a source.")
D(P91, identifier="engineering.purdue.edu/AAE/research/propulsion/Info/rockets/liquids/lr91aj11", title="LR91-AJ-11 (Aerojet)", tier="D",
  rights_checked="Purdue University web page; no reuse licence; no source cited for the table", rights_class="VALUES_WITH_ATTRIBUTION",
  note="One 'Engine statistics' table; several cells print '????'.")
D(AX, identifier="astronautix.com/l/lr87-5.html (fetched by fetch.py) and astronautix.com/l/lr87-7.html (downloaded 2026-10-28, "
                 "sha256 396ac282f69e50bf53f90908551c7e9d798544686c2134014e366505ce5d99ef)",
  title="Encyclopedia Astronautica: LR87-5; LR87-7", tier="D",
  rights_checked="page footer '(c) Encyclopedia Astronautica'; no reuse licence", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Archive entries, 'kept as they were written'; no source per value. The registry record names four pages; the -3 and "
       "-11 pages were not opened.")
D(TMS, identifier="themilitarystandard.com/missile/titan2/startsequence/", title="Titan II Missile System Start Sequence", tier="E",
  rights_checked="hobby site; no licence; unattributed transcription", rights_class="RESTRICTED_REFERENCE",
  note="Same page as SRC-MILSTD-T2START under its other URL. Reads like a transcribed missile training text, but names none.")
BLOCK("SRC-NASM-F1", "Smithsonian collection record: HTTP 403 to fetch.py; not retried with other means",
      "Its 42,500 gpm stays a search-result claim in CF-DB05-F1-PUMPFLOW.")

# ------------------------------------------------------------------ J-2 specific impulse
C("CF-DB05-J2-ISP", engine_id=J2, field_path="performance.isp_vac", db0_conflict_id="CF-R2_US_CLASSIC-J2-4",
  claims=[["425", "SRC-NTRS-20100027318", "PDF p.14 'J-2 Basic Engine Features'"],
          ["425", "SRC-NTRS-20120016414", "p.1 Table 1"],
          ["421 s (SA-208/504)", "SRC-WIKI-J2", "DB-0 search summary"]],
  resolution="RESOLVED", kind="primary_value_found",
  explanation="Both opened NASA documents print 425 s. The 421 s is a search summary of an encyclopedia row for two "
              "flights, never opened. The AS-501 flight analysis (NTRS 19680026222) shows why one number per flight can "
              "differ: five-engine S-II averages of 424.46 s in the high mixture-ratio region and 429.17 s after the "
              "mixture-ratio cutback, so a flight value of 421 s would describe an operating point, not the rating.")

# ------------------------------------------------------------------ F-1 (AEHS 'One Second')
LE = "AEHS 'One Second' page text, paragraph 'In this one second ...'"
_E = {"configuration": "UNSTATED (Saturn V S-IC engine)", "operating_point": "'maximum power' (no rating named)"}
A(F1, "pumps.LOX.flow_volume", None, "413.5 gallons of liquid oxygen", 413.5, "gal/s", _E, EH1, LE, db0=None,
  note="Per second; 24,810 gpm DERIVED.")
A(F1, "pumps.fuel.flow_volume", None, "258 gallons of RP-1", 258, "gal/s", _E, EH1, LE, db0=None,
  note="Per second; 15,480 gpm DERIVED. Same paragraph: 70 percent (181 gallons) cools the nozzle tubes.")
A(F1, "turbines.T.speed_rpm", None, "has spun 91.5 times", 91.5, "rev/s", _E, EH1, LE, db0=None,
  note="In one second; 5,490 rpm DERIVED. Same paragraph: turbine 55,000 horsepower, rotor 2,500 lb.")
A(F1, "performance.pc", None, "1,125 psig pressure", 1125, "psig", dict(_E, pc_station="UNSTATED"), EH1, LE, db0=None,
  note="Printed as gauge; the 2006 Rocketdyne slide prints the same number as psia. Competing claim in CF-DB05-F1-PC.")

C("CF-DB05-F1-PUMPFLOW", engine_id=F1, field_path="pumps.LOX.flow_volume / pumps.fuel.flow_volume", db0_conflict_id="CF-R2_US_CLASSIC-F1-4",
  claims=[["42,500 gpm", "SRC-NASM-F1", "DB-0 search summary (page refused, HTTP 403)"],
          ["413.5 gallons of liquid oxygen ... 258 gallons of RP-1 (per second)", EH1, "page text"],
          ["15,471 + 24,811 = 40,282 gpm DERIVED", "SRC-WIKI-F1", "DB-0 search summary (fetched, not evidence)"]],
  resolution="PARTIALLY_RESOLVED", kind="rating_or_rounding",
  explanation="The AEHS page gives 413.5 and 258 gallons per second, 24,810 and 15,480 gpm: the encyclopedia's 24,811 and "
              "15,471 gpm agree to within 0.1 percent, so the two are one figure, not two. The 42,500 gpm Smithsonian figure "
              "could not be opened (HTTP 403), and neither opened page names a rating or cites a document, so whether the "
              "5 percent gap is a rating, a pump design point or rounding is not established.")
C("CF-DB05-F1-TURBSPEED", engine_id=F1, field_path="turbines.T.speed_rpm", db0_conflict_id="CF-R2_US_CLASSIC-F1-3",
  claims=[["5,500 rpm", "SRC-WIKI-F1", "DB-0 search summary (fetched, not evidence)"],
          ["has spun 91.5 times (in one second)", EH1, "page text"]],
  resolution="EXPLAINED", kind="rating_or_rounding",
  explanation="91.5 rev/s is 5,490 rpm; 5,500 is the same speed rounded. Neither page is a primary document.")

# ------------------------------------------------------------------ H-1 family (Purdue table)
LP = "Purdue 'Engine statistics' table (page text)"
_P = {"configuration": "UNSTATED (row prints 205,000 lb sea level; Saturn 1B first stage)"}
A(H1, "performance.thrust_sl", None, "Thrust at Sea Level 205,000 lb", 205000, "lb", _P, PH1, LP, db0=None)
A(H1, "performance.isp_sl", None, "Isp at sea level 263 s", 263, "s", _P, PH1, LP, db0=None)
A(H1, "mechanical.mass", None, "Weight 2009 lb", 2009, "lb", dict(_P, definition="UNSTATED"), PH1, LP, db0=None)
A(H1, "propellants.mixture_ratio", None, "Mixture Ratio 2.23:1", 2.23, "(-)", _P, PH1, LP, db0=None)
A(H1, "performance.pc", None, "Chamber Pressure 700 psia", 700, "psia", _P, PH1, LP, db0=None)
A(H1, "nozzle.area_ratio", None, "Area Ratio 8:1", 8, ":1", _P, PH1, LP, db0=None)
C("CF-DB05-H1-ISP-MASS", engine_id=H1, field_path="performance.isp_sl / mechanical.mass", db0_conflict_id="CF-R2_US_CLASSIC-H1-2",
  claims=[["255 s; 2,200 lb", "SRC-WIKI-H1", "DB-0 search summary (never opened)"],
          ["Isp at sea level 263 s; Weight 2009 lb (row with 205,000 lb)", PH1, "page text"],
          ["average engine 262.60 s at sea level, S-IB-4 (H-1 200K)", "SRC-DB05-NTRS-19680003903", "Table 5 p.13"]],
  resolution="PARTIALLY_RESOLVED", kind="different_variant",
  explanation="The Purdue table prints its 263 s and 2,009 lb beside a 205,000 lb sea-level thrust, so it describes a late "
              "Saturn IB rating, not the H-1 in general; the primary S-IB-4 engine logs (200K rating) average 262.60 s at "
              "sea level, close to it. The 255 s and 2,200 lb were never opened and carry no rating; no opened primary "
              "document gives an H-1 mass, so the mass half stays open.")

# ------------------------------------------------------------------ Titan II (LR87-AJ-5 / LR91-AJ-5)
LT1 = "TMS Titan II page text, Stage I engine paragraph"
LT2 = "TMS Titan II page text, Stage II engine paragraph"
A(LR87_5, "mechanical.gimbal_range", None, "deflection of 5 degrees in any direction from a neutral position", 5, "deg",
  {"configuration": "Titan II missile, Stage I (each thrust chamber)"}, TMS, LT1, db0=None)
A(LR91_5, "mechanical.gimbal_range", None, "deflection of 4 degrees in any direction from a neutral position", 4, "deg",
  {"configuration": "Titan II missile, Stage II sustainer"}, TMS, LT2, db0=None)
C("CF-DB05-LR87-GIMBAL", engine_id=LR87_5, field_path="mechanical.gimbal_range", db0_conflict_id="CF-R2_US_CLASSIC-LR-1",
  claims=[["deflection of 5 degrees (Stage I thrust chambers)", TMS, LT1],
          ["deflection of 4 degrees (Stage II thrust chamber)", TMS, LT2]],
  resolution="EXPLAINED", kind="different_configuration",
  explanation="Not an inconsistency: the page gives 5 degrees for the two Stage I (LR87-AJ-5) chambers and 4 degrees for "
              "the Stage II (LR91-AJ-5) chamber. The 4 degrees is filed on ENG-US-LR91-AJ-5.")

LX5 = "astronautix.com/l/lr87-5.html entry table (page text)"
LX7 = "astronautix.com/l/lr87-7.html entry table (page text)"
A(LR87_5, "performance.pc", None, "Chamber Pressure: 54.00 bar", 54.00, "bar", {"configuration": "Titan II (LR87-5)"}, AX, LX5, db0=None,
  note="Same page, prose: 'Combustion Chamber Pressure: 53.3 atm' (54.0 bar); area ratio 8; mass 739 kg.")
A(LR87_7, "performance.pc", None, "Chamber Pressure: 47.00 bar", 47.00, "bar", {"configuration": "Gemini Titan II (LR87-7)"}, AX, LX7, db0=None,
  note="Same table: area ratio 9, mass 713 kg, O/F 1.9, Isp 296 s vacuum / 258 s sea level.")
C("CF-DB05-LR87-7-PC", engine_id=LR87_7, field_path="performance.pc", db0_conflict_id="CF-US_HIST-19",
  claims=[["Chamber Pressure: 47.00 bar (LR87-7)", AX, LX7],
          ["Chamber Pressure: 54.00 bar (LR87-5; for comparison)", AX, LX5]],
  resolution="UNRESOLVED", kind="different_variant",
  explanation="Both values are printed as DB-0 reported them, so not a transcription slip in DB-0. The LR87-7 entry also "
              "prints a different area ratio (9 against 8), so the lower pressure may be a different chamber design rather "
              "than a typing error; no Aerojet or Martin document for the Gemini engine was opened to tell.")

A(LR91_11, "propellants.mixture_ratio", None, "Mixture Ratio 1.78:1", 1.78, "(-)", {"configuration": "UNSTATED"}, P91,
  "Purdue 'Engine statistics' table (page text)", db0=None,
  note="Same table: 105,000 lb vacuum, Isp 316 s vacuum, 1,314 lb, 860 psia, 49.2:1; propellants printed 'LOX/RP-1 or "
       "storables, ground tested with LOX/LH2', so the row may mix variants.")
GD = "SRC-DB05-NTRS-19750004937"
LG = "NTRS 19750004937 PDF p.215 (report p.6-27) Stage II engine performance summary (text layer)"
_G = {"configuration": "Titan IIIE Stage II (LR91AJ-11)", "environment": "vacuum (including roll nozzle)"}
A(LR91_11, "propellants.mixture_ratio", None, "Mixture Ratio 1.79", 1.79, "(-)", _G, GD, LG, db0=None,
  note="Same table: oxidizer 203 lb/sec and fuel 114 lb/sec, a ratio of 1.78 DERIVED.")
A(LR91_11, "performance.thrust_vac", None, "Vacuum Thrust, lb (including Roll Nozzle) 101,000", 101000, "lb", _G, GD, LG, db0=None)
A(LR91_11, "performance.isp_vac", None, "Vacuum Specific Impulse, sec (including Roll Nozzle) 318.7", 318.7, "s", _G, GD, LG, db0=None)
A(LR91_11, "performance.mass_flow_total", None, "Total Flow Rate, lb/sec 317", 317, "lb/s", _G, GD, LG, db0=None,
  note="Same table: operating cycle 225 sec.")
A(LR91_11, "nozzle.area_ratio", None, "Expansion Ratio 49.2:1", 49.2, ":1", _G, GD, LG, db0=None)
C("CF-DB05-LR91-AJ11-MR", engine_id=LR91_11, field_path="propellants.mixture_ratio", db0_conflict_id="CF-US_HIST-05",
  claims=[["1.86", "SRC-WIKI-LR91", "DB-0 infobox summary (never opened)"],
          ["Mixture Ratio 1.78:1", P91, "page text"],
          ["Mixture Ratio 1.79 (oxidizer 203 / fuel 114 lb/sec)", GD, LG]],
  resolution="RESOLVED", kind="primary_value_found",
  explanation="The General Dynamics Convair Titan IIIE/Centaur systems summary prints 1.79 for the LR91AJ-11, and its "
              "flows (203 / 114 lb/sec) give 1.78, Purdue's figure; its 49.2:1 also matches Purdue. The 1.86 was never "
              "opened and names no variant or rating.")

# ------------------------------------------------------------------ Wave 3 engines: DB-0 conflicts on opened values
C("CF-DB05-LE9-ISP", engine_id="ENG-JP-LE-9", field_path="performance.isp_vac",
  db0_conflict_id="CF-R2_ASIA-R2A-4; CF-ASIA_OTHER-4; CF-TAXONOMY-TAX-2",
  claims=[["Isp(vacuum) 425sec", "SRC-MHI-LE9", "Main specifications"],
          ["425s (Sept 2017 press release)", "SRC-JAXA-PRESS-LE9-2017", "PDF p.3"],
          ["LOX/LH2, 1471kN, 425s, 2410kg (2017 abstract)", "SRC-IAC-LE9-2017", "abstract"],
          ["426 s; 432 s (development-era snapshot)", "SRC-WIKI-LE9", "DB-0 search summary (never opened)"]],
  resolution="RESOLVED", kind="primary_value_found",
  explanation="JAXA, MHI and the 2017 IAC abstract all print 425 s. The 426 s and the earlier 432 s are encyclopedia "
              "revisions never opened.")
C("CF-DB05-VULCAIN-MASS", engine_id="ENG-FR-VULCAIN", field_path="mechanical.mass", db0_conflict_id="CF-EUROPE-2; CF-EUROPE-5",
  claims=[["Engine Mass 1300 kg (2860 lbs) (June 1990, in development)", "SRC-NTRS-19910018907", "PDF p.10"],
          ["The Vulcain engine was 3 m high, 1.76 m in diameter and weighed 1686 kg", "SRC-ESA-VULCAIN", "Vulcain page"],
          ["1300 kg; 1800 kg (Vulcain 2)", "SRC-HANDWIKI-VULCAIN", "DB-0 search summary (never opened)"],
          ["Le moteur Vulcain qui l'équipait avait été conçu par Snecma Moteurs, et pesait 1 650 kg", "SRC-DB05-CNES-A5-LANCEUR",
           "cnes.fr/projets/ariane-5/lanceur, EPC section (fetched 2026-10-29)"]],
  resolution="UNRESOLVED", kind="different_epoch",
  explanation="Both opened values are for the first Vulcain: the 1990 briefing describes it in development; the ESA page "
              "describes 'the Ariane 5 Vulcain engine ... in its initial version' and gives 1686 kg. DB-0's CF-EUROPE-5 "
              "set that 1686 kg against a Vulcain 2 mass; on the page it belongs to Vulcain 1, so CF-EUROPE-5 has no "
              "opened Vulcain 2 value. Whether 1300 kg became 1686 kg by growth or by a different definition is not stated. "
              "CNES's Ariane 5 page (opened 2026-10-29) gives a third flight-era figure, 1 650 kg, also undefined.")
C("CF-DB05-VINCI-IGNITIONS", engine_id="ENG-FR-VINCI", field_path="operation.restarts", db0_conflict_id="CF-EUROPE-7",
  claims=[["It can ignite up to four times in a single Ariane 6 flight", "SRC-ESA-A6ENGINES", "Vinci section"],
          ["up to 3 restarts", "SRC-WIKI-VINCI", "DB-0 search summary (never opened)"],
          ["max 4 ignitions per mission", "SRC-SAFRAN-VINCI-2018", "DB-0 search summary (HTTP 403)"],
          ["up to five times", "SRC-ESA-VINCI-HOTFIRE", "identity-verified only; value not transcribed"]],
  resolution="PARTIALLY_RESOLVED", kind="definition",
  explanation="ESA's 2024 page gives four ignitions, the same as 'three restarts' once the first ignition is counted. The "
              "'five times' is on an earlier ESA test-news page that DB-0.5 verified but did not transcribe; whether it was "
              "a design goal is not shown by an opened document.")

# ------------------------------------------------------------------ IPD (Wave 2)
C("CF-DB05-IPD-THRUST", engine_id="ENG-US-IPD", field_path="performance.thrust", db0_conflict_id="CF-R2_SCHEM-R2-14",
  claims=[["a 250K lbf (1.1 MN) thrust cryogenic hydrogen/oxygen engine", "SRC-NTRS-IPD-WPB", "abstract"],
          ["a 250k-lb-thrust, full-flow, staged-combustion", "SRC-DB05-NTRS-20050243602", "text"],
          ["1,112,000 N (250,000 lbf)", "SRC-DTIC-ADA397910", "DB-0 search summary (access blocked)"],
          ["250,000 lb (1,110 kN)", "SRC-FLIGHTGLOBAL-IPD", "DB-0 search summary (never opened)"]],
  resolution="EXPLAINED", kind="rating_or_rounding",
  explanation="Every value is the 250,000 lbf design class, converted and rounded differently (1.1 MN, 1,110 kN, "
              "1,112,000 N). The opened NASA documents print it as a programme goal, not a measured rating.")
