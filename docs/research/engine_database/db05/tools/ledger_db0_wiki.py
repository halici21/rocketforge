"""DB-0 conflict encyclopedia pass (2026-10-28): the last 86 DB-0 conflicts, whose claims cite only encyclopedia
pages, URL-less search summaries, or sources that refused access. The encyclopedia pages were fetched with fetch.py
(current revision on 2026-10-28) and searched for each claim; the rest were retried once. An encyclopedia page is
tier D/E and is not evidence of an engine value: these records establish what the cited page says now, whether a
'conflict' is two revisions or two variants on one page, and which side still needs a primary document."""
import json
from pathlib import Path

from ledger import D, C

_REG = {s["source_id"]: s for s in json.loads(
    (Path(__file__).resolve().parents[2] / "data" / "sources.json").read_text(encoding="utf-8"))["sources"]}

for _sid in ["SRC-WIKI-AESTUS", "SRC-WIKI-ARIANE1", "SRC-WIKI-ASTRA-ROCKET", "SRC-WIKI-ATLASII", "SRC-WIKI-BE3",
             "SRC-WIKI-BE3U", "SRC-WIKI-BE4", "SRC-WIKI-BLUEGHOST", "SRC-WIKI-BMW109558", "SRC-WIKI-CE75", "SRC-WIKI-CURIE",
             "SRC-WIKI-CZ1", "SRC-WIKI-ELECTRON", "SRC-WIKI-HM7B", "SRC-WIKI-HS15", "SRC-WIKI-HWK109507", "SRC-WIKI-KBKHM",
             "SRC-WIKI-LE7", "SRC-WIKI-LE9", "SRC-WIKI-LEROS", "SRC-WIKI-M1", "SRC-WIKI-MARC60", "SRC-WIKI-MERLIN",
             "SRC-WIKI-NK15", "SRC-WIKI-NK33", "SRC-WIKI-OTRAG", "SRC-WIKI-PGM19", "SRC-WIKI-R4D", "SRC-WIKI-RAPTOR",
             "SRC-WIKI-RD0120", "SRC-WIKI-RD107", "SRC-WIKI-RD215", "SRC-WIKI-RD263", "SRC-WIKI-RD270", "SRC-WIKI-RD58",
             "SRC-WIKI-RL10", "SRC-WIKI-RL60", "SRC-WIKI-RS56", "SRC-WIKI-RS68", "SRC-WIKI-S3D", "SRC-WIKI-S598M",
             "SRC-WIKI-SEPR84", "SRC-WIKI-SOYUZ-CSG", "SRC-WIKI-SOYUZFG", "SRC-WIKI-SUPERDRACO", "SRC-WIKI-TEPREL",
             "SRC-WIKI-TR107", "SRC-WIKI-TR201", "SRC-WIKI-TRONADOR", "SRC-WIKI-VIKAS", "SRC-WIKI-VIKING", "SRC-WIKI-VULCAIN",
             "SRC-WIKI-WACCORPORAL", "SRC-WIKI-WELKIN", "SRC-WIKI-XLR99", "SRC-WIKI-YF1", "SRC-WIKI-YF73", "SRC-WIKI-YF77"]:
    _s = _REG[_sid]
    D(_sid, identifier=_s["url"], title=_s["title"], tier=_s["tier"],
      rights_checked="English Wikipedia article, current revision fetched by fetch.py on 2026-10-28; text CC BY-SA 4.0",
      rights_class="VALUES_WITH_ATTRIBUTION",
      note="Encyclopedia page read from its text (infobox wikitext and prose); identity as registered by DB-0. Not evidence "
           "of an engine value.")
D("SRC-LLMPEDIA-HM7B", identifier=_REG["SRC-LLMPEDIA-HM7B"]["url"], title=_REG["SRC-LLMPEDIA-HM7B"]["title"], tier="E",
  rights_checked="machine-generated encyclopedia page (the URL names the generating model); no licence found",
  rights_class="RESTRICTED_REFERENCE", note="Language-model output; never evidence. Read only to settle what DB-0 cited.")

_LOC = {"T": "encyclopedia page text, current revision (fetched 2026-10-28)",
        "NF": "fetched; not in the current revision's text",
        "N": "not opened (refused, 404, unreachable, or never fetched)",
        "X": "no source id (DB-0 search summary or brief)",
        "D4": "NRC 2006 (NAP 11780) Appendix D, Table D-4 (opened in an earlier DB-0.5 pass)",
        "J97": "NASDA 委16-4 (1997-05-14) p.1, (1) 第6回燃焼試験結果",
        "P60": "US 6,996,973 B2 description (ESA patent, priority 1999), Vulcain 2 adaptation paragraph",
        "U15": "ULA Delta IV Launch Services User's Guide (June 2013) p.1-5, section 1.2.1 First Stage",
        "U16": "ULA Delta IV Launch Services User's Guide (June 2013) p.1-6, section 1.2.2 Second Stage",
        "CN": "cnes.fr/projets/ariane-5/lanceur, EPS section (fetched 2026-10-29)",
        "PR94": "ESA Press Release N° 35-1994 (14 October 1994), release text",
        "B102": "ESA Bulletin 102 (May 2000) p.2 Table 1 'Technical characteristics of the Vulcain-2 cryogenic engine'",
        "M8": "H-II F8 investigation report (MEXT archive 1335987_007_5.pdf) 別添表８－２",
        "J17": "資料37-3 (JAXA, 2017-09-05) PDF p.3 '1. LE-9エンジン基本仕様', column '（参考）LE-7Aエンジン'",
        "JP": "rocket.jaxa.jp LE-7A engine page, specification table (fetched 2026-10-29)",
        "MH": "三菱重工技報 Vol.53 No.4 (2016) p.37 表1 LE-9エンジン諸元",
        "AT": "jaxa.jp H-IIB F3 LE-7A firing result page (2010-08-19), result table",
        "P2O": "NTRS 19630006100 (MSFC, From Peenemuende to Outer Space, 1962) PDF p.297, chapter 13 propulsion history",
        "M68": "NTRS 19680014530 (Aerojet, M-1 thrust chamber development, NAS 3-2555, 15 May 1968) PDF p.17 Summary, p.19 Introduction, p.201/292 Appendix G",
        "EPS": "esa.int Ariane 5 Storable Propellant Stage (EPS) page text (fetched 2026-10-29)",
        "CPS": "NTRS 20110015783 (NASA HAT, Cryogenic Propulsion Stage, Aug 2011) slide 10 'CPS Engine Options' table",
        "KB": "kbkha.ru engine page, 'Характеристики' block (fetched 2026-10-29)",
        "NL4": "nammo.com LEROS 4 product page: introduction text and specification table (fetched 2026-10-29)",
        "AG1": "argentina.gob.ar/node/71704 (Tronador II programme page), body text",
        "AG2": "argentina.gob.ar/node/390734 (release of 2023-08-01), body text",
        "L3B23": "L3Harris bipropellant sheet 06/2023, table (archive capture 2025-12-06)",
        "L3B24": "L3Harris bipropellant sheet L24789 02/2024, table (archive capture 2024-03-05)",
        "L3M23": "L3Harris monopropellant sheet 06/2023, table (archive capture 2024-02-01)",
        "L3M25": "L3Harris monopropellant sheet 2025-10, table (archive capture 2026-03-25)",
        "AST": "Astra Rocket 3.1 press kit (2020), vehicle table p.5 (archive capture 2020-09-14)",
        "BOE": "blueorigin.com/engines, engine panels (archive capture 2026-07-14)",
        "BOH": "Blue Origin release 2024-09-23 'New Glenn completes second stage hotfire' (archive capture 2024-09-27)",
        "BOU": "Blue Origin release 2025-11-20 on upgraded New Glenn engines (archive capture 2025-12-05)",
        "BOP": "Blue Origin/ULA partnership release (2014), body text (archive capture 2019-07-27)",
        "NV2A": "NASM record A19600013000, description (archive capture 2025-04-05)",
        "NV2B": "NASM record A19790951000, description (archive capture 2025-04-02)",
        "CT310": "CaltechTHESIS record 310 (1947), abstract (archive capture 2025-07-08)",
        "NHWK": "NASM record A19771225000, description (archive capture 2025-04-05)",
        "RS68D": "RS-68A data sheet (Aerojet Rocketdyne, March 2019), Specifications table (archive capture 2023-01-30)",
        "LE2": "launcherspace.com/engine-2, performance list (archive capture 2019-09-20)",
        "KBH14": "kbhmisaeva.ru main.php?id=52 (14D30), 'Характеристики' table (archive capture 2016-03-04)",
        "AEB": "Astrium Aestus brochure, technical data and development history (archive capture 2016-04-30)",
        "OTR78": "NASA TM-75376 (1978), translated text and design box",
        "FRR3": "Hopson STS-104 FRR charts (28 June 2001), p.3 'SSME Engine Comparison' table (govdocs1 673547)",
        "EMENC": "npoenergomash.ru/encikloped/dvizki, engine table row (archive capture 2016-01-09)",
        "SS06": "Vestnik SSAU 2006 (RSC Energia), Table 1 'Основные характеристики ЖРД 11Д58М'",
        "NV2C": "NASM record A19771237000, description (archive capture 2025-04-20)",
        "IPV": "iprofesional.com article 181740 (2014-03-05), body text",
        "X61": "NTRS 19710070145 (XLR99 engine operating experience, 1961) p.2 data list and p.8 Table I"}


def K(db0_id, engine_id, field_path, claims, resolution, kind, explanation):
    """Claims without a source id cannot be ledger claims; they are named in the explanation instead."""
    loose = [t for t, s, k in claims if s is None]
    if len(loose) == len(claims):
        NOT_FILED[db0_id] = "no claim carries a source id"
        return
    if loose:
        explanation = "Unsourced DB-0 claim(s): " + "; ".join(loose) + ". " + explanation
    C("CF-DB05-E-" + db0_id.replace("CF-", ""), engine_id=engine_id, field_path=field_path, db0_conflict_id=db0_id,
      claims=[[t, s, _LOC[k]] for t, s, k in claims if s is not None], resolution=resolution, kind=kind,
      explanation=explanation)


_PRIMARY = "No primary document opened; the record stays open."
NOT_FILED = {}  # DB-0 conflicts with nothing a ledger claim can cite

# --- seed engines
K("CF-R2_US_CLASSIC-RS-7", "ENG-US-SSME-BLOCK-II", "turbines.HPFT.discharge_temperature",
  [("HPFT Discharge Temp (R), 104.5 % power level: Block II 1615", "SRC-NASA-HOPSON-STS104-FRR-2001", "FRR3"),
   ("HPFT Discharge Temp (R), 104.5 % power level: Block IIA 1601", "SRC-NASA-HOPSON-STS104-FRR-2001", "FRR3")],
  "RESOLVED", "different_variant",
  "The flight-readiness chart (28 June 2001), read from another copy of the same government file, has a Block I / "
  "Block IIA / Block II comparison: at 104.5 % the HPFT discharge temperature is 1601 R for Block IIA and 1615 R for "
  "Block II, and the chart's Block II power-level table repeats 1615 R at 104.5 %. 1615 R is the Block II value; "
  "1601 R belongs to Block IIA.")
K("CF-R2_US_CLASSIC-A42-1", "ENG-US-RL10A-4-2", "nozzle.area_ratio",
  [("85:1", "SRC-AIAA-VEHGUIDE-ATLAS", "N"), ("nozzle_ratio '84:1 or 280:1'", "SRC-WIKI-RL10", "T"),
   ("Nozzle area ratio 84:1 (RL10A-4-2 column)", "SRC-NAP-11780", "D4")],
  "PARTIALLY_RESOLVED", "rounding_or_source",
  "The NRC comparison table prints 84:1 for the RL10A-4-2 itself, matching the encyclopedia's 84:1 rather than the "
  "AIAA guide's 85:1 (that page returns 404, so its wording cannot be checked). The NRC report is a secondary, not a "
  "manufacturer datasheet, so the value is better supported but not settled.")
K("CF-R2_US_CLASSIC-B2-4", "ENG-US-RL10B-2", "mechanical.mass / control.gimbal_actuation",
  [("dry_weight 301 kg; electro-mechanical", "SRC-WIKI-RL10", "T"), ("277 kg (older revision)", "SRC-WIKI-RL10", "NF"),
   ("hydraulic nozzle gimbal (stage)", "SRC-AIAA-VEHGUIDE-DELTA", "N"),
   ("The engine gimbal system uses electromechanical actuators", "SRC-DB05-ULA-DELTA4-UG-2013", "U16"),
   ("RL-10B2 column: Engine Dry Mass, lbm 668 (= 303 kg DERIVED)", "SRC-DB05-NTRS-20110015783", "CPS")],
  "RESOLVED", "definition_or_epoch",
  "The current revision prints 301 kg; 277 kg was an older revision. The gimbal half is settled for the Delta IV "
  "installation: the launch provider's 2013 user's guide says the RL10B-2 gimbal system uses electromechanical "
  "actuators. The mass half is settled against 277 kg: NASA's 2011 HAT engine table prints a dry mass of 668 lbm "
  "(303 kg DERIVED), within 1 percent of 301 kg. The 2 kg between them is rounding or scope, not a different engine.")
K("CF-R2_ASIA-R2A-2", "ENG-JP-LE-7A", "performance.pc",
  [("121 bar (1750 psi)", "SRC-AIAA-VG-H2A", "N"), ("Combustion chamber pressure: 12.0 MPa (1,740 psi)", "SRC-WIKI-LE7", "T"),
   ("メイン燃焼圧力 約120kgf／cm2a (firing test 6, 1997-05-09, 277 s)", "SRC-DB05-NASDA-LE7A-FT6-1997", "J97"),
   ("メイン燃焼圧力 １２．２ＭＰａ (design table, with 燃焼室混合比 ６．２)", "SRC-DB05-MEXT-H2F8-REPORT", "M8"),
   ("燃焼圧力 12.3MPa (（参考）LE-7Aエンジン column)", "SRC-JAXA-PRESS-LE9-2017", "J17"),
   ("燃焼圧力 12.3MPa (LE-7A)", "SRC-DB05-JAXA-LE7A-ENGINE-PAGE", "JP"),
   ("燃焼圧力 [MPa] 12.3（主燃焼室） (LE-7A)", "SRC-DB05-MHI-GIHO-534036", "MH"),
   ("メイン燃焼圧力 約 12.3 Mpa （ 11.7 〜 13.2）, H-IIB F3 LE-7A 性能確認試験 2010", "SRC-DB05-JAXA-H2BF3-LE7A-AT", "AT")],
  "RESOLVED", "unsupported_secondary",
  "Every agency and manufacturer document opened prints 12.3 MPa for the flying LE-7A main chamber: JAXA's 2017 LE-9 "
  "briefing (already filed as AS-DB05-JP-LE-7A-018), JAXA's engine page, MHI's 2016 technical review (主燃焼室, so the "
  "station is the main chamber) and a 2010 JAXA performance-confirmation firing (about 12.3 MPa measured against a planned 11.7-13.2). The "
  "2000 committee report's design table gives 12.2 MPa at mixture ratio 6.2, an earlier design point, and the 1997 "
  "development firing ran at about 120 kgf/cm2a (11.77 MPa). Neither 12.0 MPa nor 121 bar is printed by any of them: "
  "both are secondary values, and 12.0 MPa may be the 1997 120 kgf/cm2 read as bar-like MPa.")
K("CF-ASIA_OTHER-1", "ENG-JP-LE-7A", "performance.pc",
  [("121 bar (1750 psi)", "SRC-AIAA-VG-H2A", "N"), ("Combustion chamber pressure: 12.0 MPa (1,740 psi)", "SRC-WIKI-LE7", "T"),
   ("メイン燃焼圧力 約120kgf／cm2a (firing test 6, 1997-05-09, 277 s)", "SRC-DB05-NASDA-LE7A-FT6-1997", "J97"),
   ("メイン燃焼圧力 １２．２ＭＰａ (design table, with 燃焼室混合比 ６．２)", "SRC-DB05-MEXT-H2F8-REPORT", "M8"),
   ("燃焼圧力 12.3MPa (（参考）LE-7Aエンジン column)", "SRC-JAXA-PRESS-LE9-2017", "J17"),
   ("燃焼圧力 12.3MPa (LE-7A)", "SRC-DB05-JAXA-LE7A-ENGINE-PAGE", "JP"),
   ("燃焼圧力 [MPa] 12.3（主燃焼室） (LE-7A)", "SRC-DB05-MHI-GIHO-534036", "MH"),
   ("メイン燃焼圧力 約 12.3 Mpa （ 11.7 〜 13.2）, H-IIB F3 LE-7A 性能確認試験 2010", "SRC-DB05-JAXA-H2BF3-LE7A-AT", "AT")],
  "RESOLVED", "unsupported_secondary",
  "Same claims and reading as CF-DB05-E-R2_ASIA-R2A-2.")
K("CF-R2_ASIA-R2A-3", "ENG-JP-LE-9", "performance.pc",
  [("chamber_pressure 10.0 MPa", "SRC-WIKI-LE9", "T"), ("12.4 MPa (archived snapshot)", "SRC-WIKI-LE9", "NF")],
  "EXPLAINED", "different_epoch",
  "Two revisions of one encyclopedia article: the current one prints 10.0 MPa; 12.4 MPa is not in it and was a "
  "development-era snapshot. Neither is a JAXA or MHI value.")
K("CF-ASIA_OTHER-3", "ENG-JP-LE-9", "performance.pc",
  [("chamber_pressure 10.0 MPa", "SRC-WIKI-LE9", "T"), ("12.4 MPa (archived snapshot)", "SRC-WIKI-LE9", "NF")],
  "EXPLAINED", "different_epoch", "Same pair as CF-DB05-E-R2_ASIA-R2A-3.")
K("CF-R2_ASIA-R2A-13", "ENG-CN-YF-77", "performance.thrust_sl / pc / isp / burn_time",
  [("518 kN SL, 10.1 MPa, 428.0 / 316.7 s", "SRC-WIKI-YF77", "T"), ("'dual 510 kN (sea level)'; 10.2 MPa, 430 s", "SRC-WIKI-YF77", "NF")],
  "UNRESOLVED", "intra_document",
  "The current infobox prints 518 kN, 10.1 MPa and 428.0 / 316.7 s, while its own prose says 510 kN at sea level; "
  "10.2 MPa and 430 s are not in the current revision. The developer's two abstracts opened (IAC-13 x17679, IAC-17 "
  "x41861) print only 700 kN in vacuum at O/F 5.5 and 'a factor of 2.7 on pressure' over the YF-75, so none of these "
  "values is checked. No full paper was reached.")
K("CF-R2_SCHEM-R2-1", "ENG-US-RS-68A", "performance.pc",
  [("Chamber Pressure: 1580 psia [full power] / 820 psia [minimum power]", "SRC-L3H-RS68A-DS", "RS68D"),
   ("Chamber pressure 1,488 psi (10.26 MPa)", "SRC-WIKI-RS68", "T")],
  "RESOLVED", "primary_value_found",
  "The maker's RS-68A data sheet (March 2019, read from an archive capture at rocket.com) gives 1580 psia at full power "
  "(10.89 MPa DERIVED) and 820 psia at minimum power. The encyclopedia's 1,488 psi, printed for RS-68 and RS-68A "
  "together, is not the RS-68A rating; whether it is the flown RS-68's is CF-DB05-E-US_HIST-04.")
K("CF-R2_SCHEM-R2-2", "ENG-US-RS-68A", "performance.isp_vac",
  [("Isp, Vacuum: 411 sec", "SRC-L3H-RS68A-DS", "RS68D"), ("RS-68A: 411.9 s", "SRC-WIKI-RS68", "T"),
   ("having a vacuum specific impulse of 411.9 sec", "SRC-DB05-ULA-DELTA4-UG-2013", "U15")],
  "EXPLAINED", "rating_or_rounding",
  "The launch provider's 2013 user's guide prints 411.9 s vacuum for the RS-68A, as the encyclopedia does. The 411 s "
  "on the maker's data sheet (archive capture read 2026-10-30) is the same figure without its decimal.")
K("CF-R2_SCHEM-R2-12", "ENG-SU-RD-170", "turbines.main.power",
  [("~200 MW", None, "X"), ("189.3 MW", None, "X")],
  "UNRESOLVED", None, "Neither claim carries a source id. " + _PRIMARY)
NOT_FILED["CF-US_HIST-25"] = ("one claim only, a figure cut off as '188,00' on a page that now returns 404; not a "
                              "conflict, and filing it would withhold the promoted primary H-1 188K thrust")
K("CF-EUROPE-3", "ENG-FR-VULCAIN-2", "performance.thrust_vac",
  [("'2': 1359 kN", "SRC-WIKI-VULCAIN", "T"), ("1340 kN (comparison table)", "SRC-WIKI-VULCAIN", "NF"),
   ("Vulcain-2 column: Vacuum Thrust 301243 lbf (= 1340.0 kN DERIVED); 432 s; 115 bar (2011)", "SRC-DB05-NTRS-20110015783", "CPS")],
  "PARTIALLY_RESOLVED", "intra_document",
  "The current revision prints 1,359 kN for Vulcain 2 (and 1,324 kN for 2.1); 1,340 kN is no longer in it. Arianespace's "
  "2016 user's manual prints 1,390 kN maximum in vacuum, which neither revision matches (see CF-DB05-W-ANCHOR_EU_ASIA-1). "
  "NASA's 2011 HAT engine table prints 301,243 lbf, which is 1,340.0 kN exactly, so the removed 1,340 kN has an agency "
  "document behind it; 1,359 kN has none.")
K("CF-EUROPE-4", "ENG-FR-VULCAIN-2", "performance.pc",
  [("'2': 117.3 bar", "SRC-WIKI-VULCAIN", "T"), ("115 bar", "SRC-MECAIND-2020-T1", "N"), ("Chamber pressure 115 bar", "SRC-DB05-ESA-BULLETIN-102-VULCAIN2", "B102")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "ESA's May 2000 Vulcain-2 table prints 115 bar, the journal's value. The 117.3 bar of the current encyclopedia has no "
  "primary behind it here; it may be a later flight value, but no document says so.")
K("CF-ANCHOR_EU_ASIA-2", "ENG-FR-VULCAIN-2", "performance.pc",
  [("'2': 117.3 bar", "SRC-WIKI-VULCAIN", "T"), ("115 bar", "SRC-MECAIND-2020-T1", "N"), ("115 bar", "SRC-CLASSICISTRANIERI-VULCAIN", "N"),
   ("Chamber pressure 115 bar", "SRC-DB05-ESA-BULLETIN-102-VULCAIN2", "B102")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "The 115 bar is in a journal table (403) and an old encyclopedia mirror (403); the current article prints 117.3 bar. "
  "ESA's May 2000 table also prints 115 bar (see CF-DB05-E-EUROPE-4); no primary gives 117.3 bar.")
K("CF-ANCHOR_EU_ASIA-3", "ENG-FR-VULCAIN-2", "nozzle.area_ratio",
  [("'2': 58.2:1", "SRC-WIKI-VULCAIN", "T"), ("58.5", "SRC-MECAIND-2020-T1", "N"),
   ("the divergent portion 4 of the nozzle, which currently exhibits for the Vulcain 2 engine an area ratio R equal to 60 "
    "for a specific impulse of 433 seconds", "SRC-DB05-PATENT-US6996973", "P60"),
   ("Section ratio 58.5", "SRC-DB05-ESA-BULLETIN-102-VULCAIN2", "B102")],
  "PARTIALLY_RESOLVED", "rating_or_rounding",
  "The current revision prints 58.2:1 (the 60:1 table DB-0 saw is gone); the journal table refused access. The one "
  "agency document opened, an ESA patent (priority 1999, before Vulcain 2 first flew), gives 'equal to 60' in an "
  "illustration of the invention: a round design-era figure, likely the source of the 60:1 rendering, and not precise "
  "enough to choose between 58.2 and 58.5. ESA's May 2000 Vulcain-2 table prints 'Section ratio 58.5', the journal's "
  "value; 58.2 has no primary behind it here. A development-era table, not a flight datasheet.")

# --- USSR / Russia
K("CF-R2_USSR-R2-6", "ENG-SU-RD-0120", "performance.pc",
  [("210 kgf/cm2 = 20.6 MPa at 100 %", "SRC-JAXA-61856043", "N"), ("chamber_pressure 21.9 MPa", "SRC-WIKI-RD0120", "T"),
   ("тяга в пустоте 200 тс; удельный импульс 455 с; давление в КС 223 кг/см2", "SRC-DB05-KBKHA-RD0120", "KB")],
  "PARTIALLY_RESOLVED", "different_operating_point",
  "The encyclopedia's infobox quotes 106 % thrust next to its figures; 21.9 / 20.6 is 1.063, consistent with 106 % "
  "against 100 %, but the JAXA paper returned 503 (again on 2026-10-29). The manufacturer KBKhA prints 223 kgf/cm2 "
  "(21.87 MPa DERIVED) beside 200 tf vacuum thrust, so 21.9 MPa is the manufacturer's headline figure; 200 tf against "
  "the 190 tf seen elsewhere (1.053) tracks 223 against 210 (1.062), so the pair looks like two power levels. 210 "
  "kgf/cm2 at 100 % is still unopened.")
K("CF-R2_USSR-R2-10", "ENG-DE-A4-ENGINE", "propellants.consumed",
  [("approx. 9700 kg (21,400 lb.) of liquid oxygen ... during the sixty-second burning time", "SRC-NASM-A19600013000", "NV2A"),
   ("nearly 9,000 kg (20,000 lb) of alcohol and liquid oxygen ... during the 60-second burning time", "SRC-NASM-A19790951000", "NV2B"),
   ('approx. 4200 kg (9200 lb) of water alcohol and 5500 kg (12,200 lb) of liquid oxygen ... during the 60-second burning time', 'SRC-DB05-NASM-A19771237000', 'NV2C')],
  "PARTIALLY_RESOLVED", "definition",
  "Both Smithsonian records, read from archive captures, give a 60-second burn (not 62 s). They name different "
  "quantities: about 9,700 kg of liquid oxygen alone in one, nearly 9,000 kg of alcohol and oxygen together in the other. "
  "Read literally they contradict each other, since oxygen alone exceeds the combined total; neither cites a source. "
  "A third Smithsonian record (A19771237000, read 2026-10-31) splits the flow as about 4,200 kg water-alcohol and "
  "5,500 kg liquid oxygen, which sums to the 9,700 kg the first record calls oxygen. See CF-DB05-E-R2_SCHEM-R2-13.")
K("CF-R2_SCHEM-R2-13", "ENG-DE-A4-ENGINE", "propellants.load_mass",
  [("~9,700 kg LOX over 60 s", None, "X"), ("4,200 kg water-alcohol + 5,500 kg LOX", None, "X"),
   ("approx. 9700 kg (21,400 lb.) of liquid oxygen ... during the sixty-second burning time", "SRC-NASM-A19600013000", "NV2A"),
   ('approx. 4200 kg (9200 lb) of water alcohol and 5500 kg (12,200 lb) of liquid oxygen ... during the 60-second burning time', 'SRC-DB05-NASM-A19771237000', 'NV2C')],
  "PARTIALLY_RESOLVED", "definition",
  "4,200 + 5,500 = 9,700 kg. A Smithsonian record (A19771237000, archive capture read 2026-10-31) gives exactly that "
  "split, about 4,200 kg water-alcohol and 5,500 kg liquid oxygen over 60 s, so the 9,700 kg another Smithsonian record "
  "calls liquid oxygen is the total of both propellants, mislabelled. A third record's 'nearly 9,000 kg' of both stays "
  "lower. All are museum descriptions, not German documents.")
K("CF-R2_USSR-R2-11", "ENG-SU-RD-107A", "performance.thrust_vac",
  [("vac: 1,021.3 kN", "SRC-WIKI-SOYUZFG", "T"), ("vac: 1,019.93 kN", "SRC-WIKI-SOYUZ-CSG", "T"), ("thrust(Vac) 1,020 kN", "SRC-WIKI-RD107", "T")],
  "EXPLAINED", "rating_or_rounding", "Three encyclopedia pages within 0.14 percent: one value at different precision.")
K("CF-R2_USSR-R2-12", "ENG-SU-RD-216", "aliases.index",
  [("RD-216 (GRAU index: 8D514)", "SRC-WIKI-RD215", "T"), ("11D614", None, "X"),
   ("РД-216 (8Д514) ... 1958-1960 Сер. для I ст. Р-14; РД-216М (11Д614) ... 1966-1968", 'SRC-DB05-ENERGOMASH-ENCYCL-2016', "EMENC")],
  "RESOLVED", "different_variant",
  "The maker's engine table (NPO Energomash, archive capture of 2016) lists РД-216 as 8Д514 and РД-216М as 11Д614: "
  "two variants, each index correct for its own engine.")
K("CF-R2_USSR-R2-13", "ENG-SU-RD-263", "performance.thrust_vac",
  [("thrust(Vac) 1128 kN", "SRC-WIKI-RD263", "T"), ("1130 kN", "SRC-WIKI-RD263", "NF")],
  "EXPLAINED", "rating_or_rounding", "The current revision prints 1,128 kN; 1,130 kN is the same rounded.")
K("CF-R2_USSR-R2-14", "ENG-SU-RD-264", "aliases.index",
  [("RD-263 ... GRAU index: 15D117", "SRC-WIKI-RD263", "T"), ("RD-264 = 15D117", None, "X")],
  "PARTIALLY_RESOLVED", None,
  "The article attaches 15D117 to the RD-263, so the unsourced 'RD-264 = 15D117' contradicts it. Not settled from a "
  "primary.")
K("CF-R2_USSR-R2-15", "ENG-RU-S5-92", "aliases.index",
  [("17D61", None, "X"), ("S5.144: Used on the control module 17D61 of the Ikar", "SRC-WIKI-KBKHM", "T")],
  "PARTIALLY_RESOLVED", "definition",
  "The design-bureau article uses 17D61 for the Ikar control module, not for an engine; the unsourced claim attaches it "
  "to the S5.92.")
K("CF-R2_USSR-R2-17", "ENG-SU-RD-270", "history.end",
  [("Date 1962-1968 (infobox)", "SRC-WIKI-RD270", "T"), ("designed ... in 1960-1970 (prose)", "SRC-WIKI-RD270", "T"),
   ('РД-270 (8Д420) ... Годы разработки 1962-1969; Проект для I ст. РН УР-700 по лунной программе; ОИ', 'SRC-DB05-ENERGOMASH-ENCYCL-2016', 'EMENC')],
  "PARTIALLY_RESOLVED", "definition",
  "The maker's engine table (NPO Energomash, archive capture of 2016) gives the RD-270's years of development as "
  "1962-1969 and its status as a project for the UR-700 lunar rocket that reached fire tests. Neither encyclopedia span "
  "matches: 1962 agrees with the infobox start, 1969 with neither end. The maker gives no cancellation date.")
K("CF-USSR-17", "ENG-SU-RD-270", "history.period",
  [("Date 1962-1968 (infobox)", "SRC-WIKI-RD270", "T"), ("designed ... in 1960-1970 (prose)", "SRC-WIKI-RD270", "T"),
   ('РД-270 (8Д420) ... Годы разработки 1962-1969; Проект для I ст. РН УР-700 по лунной программе; ОИ', 'SRC-DB05-ENERGOMASH-ENCYCL-2016', 'EMENC')],
  "PARTIALLY_RESOLVED", "definition", "As CF-DB05-E-R2_USSR-R2-17: the maker's table gives 1962-1969.")
K("CF-TAXONOMY-TAX-4", "ENG-SU-RD-270", "history.cancellation",
  [("designed ... in 1960-1970", "SRC-WIKI-RD270", "T"), ("Date 1962-1968", "SRC-WIKI-RD270", "T"),
   ('РД-270 (8Д420) ... Годы разработки 1962-1969; Проект для I ст. РН УР-700 по лунной программе; ОИ', 'SRC-DB05-ENERGOMASH-ENCYCL-2016', 'EMENC')],
  "PARTIALLY_RESOLVED", "definition",
  "As CF-DB05-E-R2_USSR-R2-17: the maker's table ends development in 1969 and records fire tests only; it prints no "
  "cancellation date.")
K("CF-R2_USSR-R2-18", "ENG-RU-S5-98M", "performance.isp_vac",
  [("Specific impulse, vacuum 328.6 seconds", "SRC-WIKI-S598M", "T"), ("326 s", None, "X"),
   ("Тяга 2000 кгс ... Удельный импульс тяги 328,6 с", "SRC-DB05-KBKHM-14D30-2016", "KBH14")],
  "RESOLVED", "primary_value_found",
  "The maker's 14D30 page (KB Khimmash, archive captures of 2013 and 2016) prints 328.6 s at 2000 kgf, mixture ratio "
  "2.0 and 100 kgf/cm2, the encyclopedia's figure. The 326 s has no source.")
K("CF-R2_SC_COMM-R2-11", "ENG-RU-S5-98M", "performance.isp_vac",
  [("Specific impulse, vacuum 328.6 seconds", "SRC-WIKI-S598M", "T"), ("328.1 s", None, "X"), ("~326 s (Briz-KM)", None, "X"),
   ("Удельный импульс тяги 328,6 с", "SRC-DB05-KBKHM-14D30-2016", "KBH14")],
  "RESOLVED", "primary_value_found",
  "The maker's 14D30 page (archive captures of 2013 and 2016) prints 328.6 s. The 328.1 s and ~326 s have no source; "
  "the Briz-KM figure may be a stage-level value but nothing opened says so.")
K("CF-R2_USSR-R2-19", "ENG-SU-11D58M", "performance.thrust_vac / isp_vac",
  [("Thrust, vacuum 79.46 kN; 353 s (infobox)", "SRC-WIKI-RD58", "T"), ("Thrust (Vac) 83.4 kN (variant table)", "SRC-WIKI-RD58", "T"),
   ("83.40 kN, 349 s, 78 bar", "SRC-ASTRONAUTIX-RD58", "N"),
   ("Тяга, кН 85; Удельный импульс тяги, с 356; Давление в камере, МПа 7,9; степень расширения сопла 280 (2006)", "SRC-DB05-SSAU-420-2006", "SS06")],
  "PARTIALLY_RESOLVED", "different_configuration",
  "The developer's 2006 paper (RSC Energia) gives the 11D58M 85 kN, 356 s and 7.9 MPa with the carbon-carbon nozzle "
  "extension of expansion ratio 280, which replaced a ratio-94 extension and added about 4.5 s in flight. So the Isp "
  "spread (349-356 s) follows the nozzle fitted; the 83.4 and 79.46 kN figures are not printed by the developer and "
  "their configuration is not stated.")
K("CF-USSR-11", "ENG-SU-NK-15", "performance.thrust_vac / pc / isp_vac",
  [("thrust(Vac) 1544 kN, 7.85 MPa, 318 s", "SRC-WIKI-NK15", "T"), ("1753 kN, 14.50 MPa, 331 s", "SRC-WIKI-NK15", "NF")],
  "EXPLAINED", "different_variant",
  "The current revision prints only 1,544 kN / 7.85 MPa / 318 s. 1,753 kN, 14.50 MPa and 331 s match the NK-33 "
  "(the NK-33 article prints 14.83 MPa and 331 s), so the second set was an NK-33 figure on the NK-15 page.")
K("CF-USSR-12", "ENG-SU-NK-33", "aliases.index",
  [("14D15", "SRC-WIKI-NK33", "NF")],
  "PARTIALLY_RESOLVED", None,
  "The English article does not print 14D15 (it cites 11D111 for the NK-33); the Russian news page in CF-DB05-W-R2_USSR-R2-5 "
  "does. Index assignment not settled from a primary.")
K("CF-USSR-13", "ENG-US-AJ26-59", "lineage",
  [("NK-43 -> AJ26-59", "SRC-WIKI-AJ26", "N"), ("NK-43 variant listed as AJ26-60", "SRC-WIKI-NK33", "NF")],
  "UNRESOLVED", None, "The mirror refused access (401) and the NK-33 article's text does not carry the claim. " + _PRIMARY)
K("CF-USSR-19", "ENG-SU-RD-253", "aliases.index", [], "UNRESOLVED", None,
  "DB-0 recorded the conflict without any claim; nothing to check.")

# --- Asia, Europe, other
K("CF-R2_ASIA-R2A-8", "ENG-IN-VIKAS", "performance.thrust",
  [("maximum thrust of 725 kN (original); upgraded ... 800 kN", "SRC-WIKI-VIKAS", "T"), ("Thrust 821 kN (infobox)", "SRC-WIKI-VIKAS", "T"),
   ("850 kN (older infobox)", "SRC-WIKI-VIKAS", "NF"), ("799 kN PSLV / 846 kN GSLV HT", "SRC-VAJIRAM-VIKAS", "NF")],
  "EXPLAINED", "different_epoch",
  "One article describes successive builds: 725 kN original, 800 kN after the 58.5 bar uprate, 6 % more from 2018. The "
  "values are epochs, not readings of one rating (see the SpaceNews 52.5-58.5 bar record).")
K("CF-R2_ASIA-R2A-11", "ENG-IN-CE-7-5", "performance.thrust_vac",
  [("Maximum thrust (Vacuum) - 73.55 kN", "SRC-WIKI-CE75", "T"), ("Chamber pressure 5.8 MPa (58 bar) / 7.5 MPa (75 bar)", "SRC-WIKI-CE75", "T")],
  "EXPLAINED", "unit",
  "The '75 kN max' was a misreading: the 75 on the page is the 75 bar chamber pressure; the thrust is 73.55 kN.")
K("CF-R2_ASIA-R2A-18", "ENG-FR-VIKING-5C", "performance.pc",
  [("58.5 bar", "SRC-FRWIKI-VIKING", "N"), ("chamber_pressure 5.5 MPa", "SRC-WIKI-VIKING", "T")],
  "UNRESOLVED", None, "The French page refused access (HTTP 403). " + _PRIMARY)
K("CF-R2_ASIA-R2A-25", "ENG-KP-HWASONG-15-FIRST-STAGE-ENGINE", "geometry.chamber_count",
  [("Engine 1 Paektusan ... 788 kN", "SRC-WIKI-HS15", "T"), ("two combustors fed by common turbopump", "SRC-WIKI-HS15", "T")],
  "EXPLAINED", "definition", "One article: one engine with two combustors on a common turbopump. Counting, not conflict.")
K("CF-R2_ASIA-R2A-26", "ENG-AR-MT-B", "propellants",
  [("Second stage Powered by 1 MT-B ... LOX / RP-1", "SRC-WIKI-TRONADOR", "T"), ("MMH / N2O4 pressurised", "SRC-WIKI-TRONADOR", "NF"),
   ("monometil hidracina como combustible y tetróxido de nitrógeno/ácido nítrico como oxidante para la etapa superior ... "
    "Motor de Tipo Presurizado", "SRC-DB05-ARGGOB-TRONADOR2", "AG1"),
   ("prototipo del motor de segunda etapa que llevará la versión final del Tronador II ... cuyo combustible es oxígeno "
    "líquido y kerosene (2023)", "SRC-DB05-ARGGOB-2023-08-01", "AG2")],
  "EXPLAINED", "different_epoch",
  "The Argentine government's own pages print both: the programme page's configuration gives a pressure-fed MMH / "
  "N2O4-nitric acid upper stage, and the 1 August 2023 release tests a LOX / kerosene prototype of the second-stage "
  "engine for the final Tronador II. The upper stage changed propellants between the two designs; the 'MT-B' name "
  "itself is not printed on either page.")
K("CF-R2_ASIA-R2A-27", "ENG-AR-VEX-1A-ENGINE", "history.test_date",
  [("26 Feb 2014", "SRC-WIKI-TRONADOR", "NF"), ("In March 2014, a suborbital prototype named VEx-1A failed", "SRC-WIKI-TRONADOR", "T"),
   ("el lanzamiento se hizo el último miércoles 26 de febrero. Pero el vector Vex 1A, que logró despegar unos dos metros, "
    "... se estrelló", "SRC-DB05-IPROFESIONAL-VEX1A-2014", "IPV"),
   ("En marzo del 2014 se realizó desde el Centro Espacial Punta Indio la primera prueba de un vehículo experimental que "
    "fue denominado Vex1A", "SRC-DB05-ARGGOB-TRONADOR2", "AG1")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "A news report of 5 March 2014 dates the VEx-1A launch failure to Wednesday 26 February 2014 (a Wednesday), after "
  "attempts in December, January and on 24 February; the government spoke of it only in March. The government's own "
  "programme page, written later, says 'En marzo del 2014'. A report published on 5 March cannot describe a later "
  "March launch, so 26 February is the better-supported date, but the official page still disagrees.")
K("CF-R2_ASIA-R2A-29", "ENG-CN-WELKIN-VAC", "performance.thrust_vac",
  [("600 kN", "SRC-ORBITCODEX-PALLAS", "N"), ("Thrust, vacuum 500 kilonewtons", "SRC-WIKI-WELKIN", "T"),
   ("CQ-50: 600kN (Vacuum Version) Vacuum Thrust; 330s (Vacuum Version)", "SRC-GE-WELKIN-EN", "T")],
  "RESOLVED", "primary_value_found",
  "The maker's engine page (fetched 2026-10-28) prints 600 kN for the CQ-50 vacuum version, against 500 kN for the "
  "sea-level engine at sea level. The encyclopedia's 500 kN 'vacuum' figure matches the maker's sea-level number, "
  "not its vacuum version.")
K("CF-R2_ASIA-R2A-31", "ENG-ES-TEPREL-C-VAC", "performance.thrust_vac",
  [("50 kN", "SRC-WIKI-TEPREL", "NF"), ("Thrust, vacuum 75 kN (17,000 lbf)", "SRC-WIKI-TEPREL", "T"), ("75 kN", "SRC-SATNOW-TEPRELC", "N")],
  "EXPLAINED", "different_epoch",
  "The current revision prints 75 kN in vacuum, the SatNow figure DB-0 cited; the 50 kN was an earlier revision.")
K("CF-R2_ASIA-R2A-32", "ENG-FR-SEPR-841", "propellants.fuel",
  [("nitric acid oxidiser and TX2 (tri-ethylamine xylidine) fuel", "SRC-WIKI-SEPR84", "T"),
   ("the TX2 fuel of the SEPR 841 was replaced with ... kerosene in the SEPR 844", "SRC-WIKI-SEPR84", "T")],
  "EXPLAINED", "different_variant", "The article gives TX2 for the SEPR 841 and kerosene for the later SEPR 844.")
K("CF-R2_ASIA-R2A-33", "ENG-DE-OTRAG-CRPU-ENGINE", "propellants.oxidizer",
  [("N2O4 (stage infobox)", "SRC-WIKI-OTRAG", "T"), ("nitric acid", None, "X"),
   ("As low cost fuel, a mixture of simple diesel oil and nitric acid is proposed (1978)", "SRC-DB05-NTRS-19790003958", "OTR78")],
  "PARTIALLY_RESOLVED", None,
  "A 1978 press account, translated by NASA as TM-75376, describes OTRAG's propellants as diesel oil and nitric acid, so "
  "the nitric acid claim has a contemporary source. It is a magazine article, not a design document, and does not "
  "say whether the acid was inhibited or fuming; the encyclopedia's N2O4 has no source opened.")
K("CF-R2_ASIA-R2A-34", "ENG-JP-MB-60", "aliases.name",
  [("MARC-60 ... also known as MB-60, MB-XX, and RS-73", "SRC-WIKI-MARC60", "T"),
   ("MARC-60 (MB-60), same thrust class ... designed as a joint effort by Boeing and Mitsubishi", "SRC-WIKI-RL60", "T")],
  "EXPLAINED", "definition",
  "Both articles name MB-60 an alias of MARC-60; the RL60 article lists it as a comparable engine, not as the RL60.")
K("CF-R2_SC_COMM-R2-1", "ENG-US-SUPERDRACO", "performance.isp_sl",
  [("specific_impulse_sea_level 235 s", "SRC-WIKI-SUPERDRACO", "T"), ("~240 s (derived)", "SRC-WIKI-SUPERDRACO", "NF")],
  "UNRESOLVED", None, "The article prints 235 s; the ~240 s was a DB-0 derivation, not a printed value. " + _PRIMARY)
K("CF-R2_SC_COMM-R2-2", "ENG-US-SUPERDRACO", "performance.thrust",
  [("71 kN (16,000 lbf), individually; 32,000 lbf, dual-engine cluster", "SRC-WIKI-SUPERDRACO", "T"),
   ("capable of 73,000 newtons ... throttled to 68,170 newtons during DragonFly testing", "SRC-WIKI-SUPERDRACO", "T")],
  "EXPLAINED", "different_operating_point",
  "One article: 71 kN per engine, 32,000 lbf per two-engine pod, 73 kN capability and 68.17 kN as throttled in tests.")
K("CF-R2_SC_COMM-R2-8", "ENG-GB-LEROS-4-ET", "propellants.fuel",
  [("LEROS 4-ET MMH / MON 1310 N", "SRC-WIKI-LEROS", "T"), ("The engine uses MON and hydrazine", "SRC-WIKI-BLUEGHOST", "T"),
   ("LEROS 4 (parent): '321 second Isp, MON/ Hydrazine apogee engine' in the text; 'Propellant MON-3/MMH' in the specification "
    "table", "SRC-DB05-NAMMO-LEROS4", "NL4")],
  "PARTIALLY_RESOLVED", "definition",
  "Two encyclopedia articles disagree (MMH against hydrazine). The maker's page for the parent LEROS 4 does the same "
  "within itself: its prose says 'MON/ Hydrazine' and its specification table says MON-3/MMH, so 'hydrazine' is the "
  "maker's loose family wording and the tabulated fuel is MMH. No Nammo page for the 4-ET variant was found, so the "
  "4-ET fuel is inferred from the parent, not printed.")
K("CF-R2_SC_COMM-R2-14", "ENG-US-ARROWAY", "cycle",
  [("fuel-rich staged combustion", None, "X"), ("ox-rich staged combustion", None, "X")],
  "UNRESOLVED", None, "Neither claim has a source. " + _PRIMARY)
K("CF-R2_SC_COMM-R2-15", "ENG-US-E-2", "performance.isp_vac",
  [("326 s ('Launcher says')", "SRC-CONTROL-E2-TEST", "NF"), ("365 s", None, "X"),
   ("Performance: 365s specific impulse (Second stage nozzle). First stage nozzle - 327s vacuum, 290s sea level",
    "SRC-DB05-LAUNCHER-E2-PAGE-2019", "LE2")],
  "EXPLAINED", "different_configuration",
  "The maker's 2019 Engine-2 page (archive capture) gives 365 s for the second-stage (vacuum) nozzle and 327 s vacuum / "
  "290 s sea level for the first-stage nozzle, so 365 s and the ~326 s describe two nozzles. The trade article, read "
  "from an archive capture, prints no specific impulse; DB-0's 326 s is 1 s from the maker's 327 s. These are 2019 "
  "design figures.")
K("CF-R2_SC_COMM-R2-17", "ENG-NZ-CURIE", "propellants",
  [("In August 2020 Rocket Lab indicated that the kick stage uses an unspecified liquid bi-propellant", "SRC-WIKI-CURIE", "T"),
   ("Viscous liquid monopropellant ... [citation needed]", "SRC-WIKI-ELECTRON", "T")],
  "EXPLAINED", "different_epoch",
  "The Curie article separates the original monopropellant engine from the 2020 bipropellant version; the Electron "
  "article's stage box keeps the older, uncited entry.")
K("CF-R2_SC_COMM-R2-19", "ENG-US-TR-107", "performance.thrust",
  [("Thrust, sea-level 4,900 kN (1,100,000 lbf)", "SRC-WIKI-TR107", "T"),
   ("TR-106 engine, a similar throttleable engine of about half the thrust", "SRC-WIKI-TR107", "T")],
  "EXPLAINED", "definition",
  "DB-0 inverted the sentence: the TR-106 has about half the TR-107's thrust, not the other way round. No conflict.")
K("CF-R2_SCHEM-R2-4", "ENG-US-RAPTOR-2", "performance.pc",
  [("330 (tonnes of thrust, not bar)", "SRC-WIKI-RAPTOR", "T"), ("250 bar", None, "X")],
  "UNRESOLVED", "unit",
  "The 330 found on the article is a thrust goal in tonnes, not a chamber pressure; the 250 bar has no source. See "
  "CF-DB05-W-COMMERCIAL-COM-7 for the reported 300-330 bar.")
K("CF-R2_SCHEM-R2-6", "ENG-US-BE-4", "performance.pc",
  [("134 bar (older revision via mirror)", "SRC-WIKI-BE4", "NF"), ("chamber_pressure 140 bar", "SRC-WIKI-BE4", "T")],
  "EXPLAINED", "different_epoch", "Two revisions: the current one prints 140 bar. Neither is a Blue Origin value.")
K("CF-R2_SCHEM-R2-10", "ENG-US-R-4D-11", "performance.isp_vac",
  [("R-4D-11 378-511 N 164:1 = 311 sec (lbf/lbm) 300:1= 315.5 sec (lbf/lbm)", "SRC-L3H-LHX-SPECSHEET-2024", "L3B24"),
   ("specific_impulse_vacuum 312 s", "SRC-WIKI-R4D", "T")],
  "PARTIALLY_RESOLVED", "different_configuration",
  "The maker's February 2024 sheet, read from an archive capture, gives the R-4D-11 by nozzle: 311 s at area ratio 164:1 "
  "and 315.5 s at 300:1. The encyclopedia's 312 s names no area ratio and matches neither row; it has no maker source.")
K("CF-US_HIST-04", "ENG-US-RS-68", "performance.thrust_sl / performance.pc",
  [("663,000 pounds-force (2,950 kN) at sea level (prose)", "SRC-WIKI-RS68", "T"), ("RS-68: 2,950 kN (660,000 lbf) (infobox)", "SRC-WIKI-RS68", "T"),
   ("RS-68A Chamber Pressure: 1580 psia", "SRC-L3H-RS68A-DS", "RS68D")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "The encyclopedia's 663,000 and 660,000 lbf are one 2,950 kN rounded two ways. Rocketdyne's 1999 baseline (NTRS "
  "20000025317, p.11) rates the RS-68 at 650 klbf sea level, 745 klbf vacuum and 1,410 psia before first flight, so the "
  "encyclopedia's 663,000 lbf and 1,488 psi are a later rating with no primary opened. NASA's 2009 Ares V paper gives "
  "the RS-68A as 39,000 lbf above the RS-68; 663,000 + 39,000 = 702,000 lbf DERIVED matches NASA's 702,000 lb for the "
  "RS-68A (CF-DB05-RS68A-THRUST), which supports 663,000 lbf as the flown RS-68 rating without a document saying so.")
K("CF-US_HIST-09", "ENG-US-XLR99-RM-1", "mechanical.mass",
  [("The basic engine has a mass of 910 lb", "SRC-WIKI-XLR99", "T"), ("915 lb", "SRC-NMUSAF-XLR99", "N"),
   ("Dry weight - 910 pounds; Table I Spec. 91M (March 1961) dry 910 lb, wet 1,025 lb", "SRC-DB05-NTRS-19710070145", "X61")],
  "RESOLVED", "primary_value_found",
  "The museum fact sheet refused access (HTTP 403). The 1961 AFFTC/NASA paper on XLR99 operating experience prints "
  "a dry weight of 910 pounds for the present engine, and its specification table shows the growth from 540 lb "
  "(initial proposal) through 856 lb (Spec. 91F, 1958) to 910 lb (Spec. 91M, 1961); wet weight is 1,025 lb. 910 lb "
  "is the documented dry mass; 915 lb has no document.")
K("CF-US_HIST-12", "ENG-US-S-3D", "performance.thrust",
  [("134,908 pounds of thrust (600.1 kN) at sea level", "SRC-WIKI-S3D", "T"), ("engine_power 150,000 lbf (Jupiter)", "SRC-WIKI-PGM19", "T"),
   ("150,000-205,000 lb depending on model", "SRC-NMUSAF-LR79", "N"),
   ("to modify the Atlas S-3 engine for use in the Jupiter missile. This S-3D engine produced a thrust of 150,000 lb",
    "SRC-DB05-NTRS-19630006100", "P2O")],
  "PARTIALLY_RESOLVED", "different_variant",
  "Two articles: the S-3D at 134,908 lbf and the Jupiter missile's engine at 150,000 lbf; the museum's range (403) "
  "suggests several models. MSFC's 1962 history volume states that the S-3D, Rocketdyne's Jupiter modification of "
  "the Atlas S-3, 'produced a thrust of 150,000 lb', which documents the shipped 150,000 lb Jupiter value. The "
  "134,908 lbf (600.1 kN) sea-level figure, perhaps an early or Thor-related rating, still has no document.")
K("CF-US_HIST-14", "ENG-US-38ALDW-1500", "propellants.fuel",
  [("RFNA + furfuryl alcohol", "SRC-WIKI-WACCORPORAL", "T"),
   ("The Wac Corporal is a sounding rocket of 590 lbs. gross weight using red fuming nitric acid and aniline as propellants (1947)",
    "SRC-CALTECH-THESIS310", "CT310")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "A 1947 GALCIT engineer's thesis (abstract read from an archive capture) describes the WAC Corporal as burning red "
  "fuming nitric acid and aniline, so the aniline claim has a contemporary source. The encyclopedia's furfuryl alcohol "
  "has none opened; the vehicle may have flown aniline, furfuryl alcohol or a blend at different times.")
K("CF-US_HIST-16", "ENG-US-RS-56-OSA", "performance.thrust",
  [("RS-56-OSA: 60,500 lbf (269.0 kN) sea level", "SRC-WIKI-RS56", "T"), ("1 x RS-56-OSA Maximum thrust 386 kN (87,000 lbf)", "SRC-WIKI-ATLASII", "T")],
  "EXPLAINED", "different_operating_point",
  "Two articles: a sea-level engine figure and a stage 'maximum' figure printed beside the vacuum Isp (316 s). The RS-56 "
  "article gives the OSA 220 s at sea level and 316 s in vacuum; 60,500 lbf x 316/220 = 86,900 lbf (386.5 kN) "
  "DERIVED, matching the 386 kN / 87,000 lbf. The two are the same engine at sea level and in vacuum. No primary was "
  "opened for either value.")
K("CF-US_HIST-20", "ENG-US-TR-201", "history.period",
  [("Date 1972-1988 (infobox)", "SRC-WIKI-TR201", "T"), ("77 during its Delta career between 1974 and 1988", "SRC-WIKI-TR201", "T")],
  "EXPLAINED", "definition", "Development-to-retirement span against flight span, in one article.")
K("CF-US_HIST-23", "ENG-US-M-1", "history.cancellation",
  [("Development abandoned at pre-prototype stage", "SRC-WIKI-M1", "T"),
   ("The work accomplished in the thrust chamber development for the M-1 Engine prior to phaseout of the program; "
    "funding limitations resulting from the phaseout ... necessitated that testing be limited to only a few tests with "
    "one injector and an uncooled chamber; firings on Test Stand H-8, July and August 1966", "SRC-DB05-NTRS-19680014530", "M68")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "The article states abandonment but DB-0's conflict was about the date. Aerojet's 1968 final thrust-chamber report "
  "for NASA Lewis says the work ended with the programme's 'phaseout', after funding cuts reduced testing to a few "
  "uncooled-chamber firings in July and August 1966. A 1965 cancellation before any hardware test is therefore wrong "
  "for the thrust chamber; the engine itself was never assembled, which fits 'pre-prototype'. The report does not "
  "print the phase-out date, so the cancellation year stays 1966 or later, unconfirmed.")
K("CF-COMMERCIAL-COM-5", "ENG-US-MERLIN-1A", "performance.thrust_sl",
  [("produced 340 kN (76,000 lbf) of thrust", "SRC-WIKI-MERLIN", "T"), ("340 kN / 77,000 lbf", "SRC-WIKI-MERLIN", "NF")],
  "EXPLAINED", "unit", "340 kN is 76,435 lbf DERIVED; the current revision prints 76,000 lbf. 77,000 was an older rounding.")
K("CF-COMMERCIAL-COM-8", "ENG-US-RAPTOR-1", "performance.thrust_sl",
  [("Raptor 1: 185 tf", "SRC-WIKI-RAPTOR", "T"), ("Max demonstrated Raptor thrust is ~225 tons (Musk post, cited)", "SRC-WIKI-RAPTOR", "T")],
  "EXPLAINED", "different_operating_point", "A nominal value and a maximum demonstrated in test, in one article.")
K("CF-COMMERCIAL-COM-9", "ENG-US-BE-4", "performance.thrust_sl",
  [("delivers 550,000-lbf of thrust at sea level (2014)", "SRC-BLUE-ULA-PARTNERSHIP", "BOP"),
   ("BE-4 Thrust : 640,000 lbf (2,846 kN)", "SRC-BLUE-ENGINES", "BOE"),
   ("demonstrated 625,000 lbf ... will achieve 640,000 lbf later this year, with propellant subcooling increasing the current "
    "thrust capability from the existing 550,000 lbf (2025-11-20)", "SRC-BLUE-NG-UPGRADE", "BOU")],
  "EXPLAINED", "different_epoch",
  "Blue Origin's own releases, read from archive captures, date both numbers: 550,000 lbf at sea level from the 2014 "
  "announcement through 2025, and 640,000 lbf from propellant subcooling announced on 20 November 2025, which the engines "
  "page now prints. ULA's 550,000 lbf for Vulcan is the earlier rating (CF-DB05-W-R2_SCHEM-R2-5).")
K("CF-ANCHOR_US_MODERN-1", "ENG-US-BE-4", "performance.thrust_sl",
  [("640,000 lbf (2,846 kN)", "SRC-BLUE-ENGINES-PAGE", "N"), ("550,000 lbf", "SRC-BLUE-PRESS-BE4-EARLY", "N"),
   ("BE-4 Thrust : 640,000 lbf (2,846 kN)", "SRC-BLUE-ENGINES", "BOE"),
   ("increasing the current thrust capability from the existing 550,000 lbf (2025-11-20)", "SRC-BLUE-NG-UPGRADE", "BOU")],
  "EXPLAINED", "different_epoch",
  "The same pair as CF-DB05-E-COMMERCIAL-COM-9: Blue Origin's November 2025 release calls 550,000 lbf the existing "
  "capability and 640,000 lbf the subcooled uprate, which its engines page now prints.")
K("CF-COMMERCIAL-COM-10", "ENG-US-BE-3U", "performance.thrust_vac",
  [("originally designed to yield up to 160,000 lbf of vacuum thrust ... will fly at 173,000 lbf (2024-09-23)", "SRC-BLUE-NEWS-BE3U-MISC", "BOH"),
   ("two BE-3Us ... increasing from the original design of 320,000 lbf (1,423 kN) to 400,000 lbf (1,779 kN); demonstrated "
    "211,658 lbf (2025-11-20)", "SRC-BLUE-NG-UPGRADE", "BOU"),
   ("BE-3U Thrust : 200,000 lbf (890 kN)", "SRC-BLUE-ENGINES", "BOE")],
  "EXPLAINED", "different_epoch",
  "Blue Origin's releases, read from archive captures, give a dated series: 160,000 lbf vacuum design, 173,000 lbf for "
  "NG-1 (September 2024), and an uprate to 200,000 lbf per engine (400,000 for two) announced in November 2025, the "
  "figure the engines page prints. A time series, not a disagreement.")
K("CF-ANCHOR_US_MODERN-2", "ENG-US-BE-3U", "performance.thrust_vac",
  [("200,000 lbf", "SRC-BLUE-ENGINES-PAGE", "N"), ("173,000 / 160,000 lbf; stage 320,000 -> 400,000 lbf", "SRC-BLUE-PRESS-BE3U-UPDATES", "N"),
   ("BE-3U Thrust : 200,000 lbf (890 kN)", "SRC-BLUE-ENGINES", "BOE"),
   ("originally designed to yield up to 160,000 lbf of vacuum thrust ... will fly at 173,000 lbf", "SRC-BLUE-NEWS-BE3U-MISC", "BOH")],
  "EXPLAINED", "different_epoch", "The same series as CF-DB05-E-COMMERCIAL-COM-10, now read in Blue Origin's own releases.")
K("CF-TAXONOMY-TAX-1", "ENG-US-BE-3U", "cycle",
  [("open expander", "SRC-WIKI-BE3U", "NF"), ("Cycle Expander bleed", "SRC-WIKI-BE3U", "T")],
  "EXPLAINED", "different_epoch", "The current revision says expander bleed; 'open expander' was an earlier wording.")
K("CF-ANCHOR_US_MODERN-3", "ENG-US-BE-3U", "cycle",
  [("open expander", "SRC-BLUE-ENGINES-PAGE", "N"), ("Cycle Expander bleed", "SRC-WIKI-BE3", "T"),
   ("BE-3U is an open-expander cycle engine.", "SRC-BLUE-ENGINES", "BOE"),
   ("BE-3U's elegant expander bleed design", "SRC-BLUE-NEWS-BE3U-MISC", "BOH")],
  "EXPLAINED", "definition",
  "Blue Origin itself uses both terms: its engines page calls the BE-3U 'an open-expander cycle engine' and its September "
  "2024 release speaks of its 'expander bleed design'. Open expander and expander bleed are two names for the same cycle.")
K("CF-COMMERCIAL-COM-17", "ENG-US-MERLIN-1D-BLOCK-5", "performance.isp",
  [("282 s SL / 311 s vac, flagged 'Figures ... do not reflect current engine performance'", "SRC-WIKI-MERLIN", "T"),
   ("282 / 311 s (c. 2013)", "SRC-SLR-F9-SMA", "N")],
  "EXPLAINED", "different_epoch",
  "The article itself marks 282 / 311 s as outdated; they are the c. 2013 figures, not Block 5 values.")
K("CF-EUROPE-8", "ENG-FR-HM7B", "performance.pc",
  [("Chamber pressure 3.7 MPa (37 bar)", "SRC-WIKI-HM7B", "T"), ("increasing the chamber pressure from 30 to 35 bar", "SRC-WIKI-HM7B", "T")],
  "UNRESOLVED", "intra_document", "One article: an infobox of 37 bar and a history line ending at 35 bar. " + _PRIMARY)
K("CF-ANCHOR_EU_ASIA-6", "ENG-FR-HM7B", "performance.pc",
  [("Chamber pressure 3.7 MPa (37 bar); from 30 to 35 bar", "SRC-WIKI-HM7B", "T"), ("Chamber pressure 35.3 bar", "SRC-LLMPEDIA-HM7B", "T")],
  "UNRESOLVED", "intra_document",
  "As CF-DB05-E-EUROPE-8; the 35.3 bar comes from a machine-generated page and is not evidence of anything.")
K("CF-EUROPE-10", "ENG-DE-AESTUS", "performance.thrust_vac",
  [("thrust(Vac) 29.6 kN", "SRC-WIKI-AESTUS", "T"),
   ("The vacuum thrust of the Aestus engine was 2.7 tonnes (~26.5 kN DERIVED)", "SRC-ESA-EPS", "EPS"),
   ("avec 29 kN (2,9 tonnes) de poussée dans le vide", "SRC-DB05-CNES-A5-LANCEUR", "CN"),
   ("The EPS stage ... is propelled by the Aestus engine (thrust = 27.5 kN) (October 1994)", "SRC-DB05-ESA-PR-1994-35-EPS", "PR94"),
   ("Thrust vacuum 29.6 kN; mixture ratio (TC) 1.9 [the 'performance enhanced Aestus', first flown on flight 518 in 2004]",
    "SRC-DB05-ASTRIUM-AESTUS-BROCHURE", "AEB")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "ESA's EPS page, opened 2026-10-29 via www.esa.int, prints 2.7 tonnes vacuum thrust and more than 1000 s on a GTO "
  "mission. CNES's Ariane 5 page prints 29 kN (2.9 t) in vacuum, which could be 29.6 kN "
  "rounded but is stated as a round figure. ESA's October 1994 release, from the development test campaign, gives "
  "27.5 kN, close to ESA's 2.7 t (26.5 kN). Thrust appears to have risen between the 1994 "
  "development engine and the flown engine (the encyclopedia ties a mixture-ratio change to flight 518), but no "
  "document records the change. The maker's brochure (EADS Astrium, archive capture read 2026-10-30) gives 29.6 kN "
  "vacuum at mixture ratio 1.9 and records the 1999-2002 change from 2.05 to 1.9 first flown on flight 518, so 29.6 kN "
  "is the maker's figure for the later engine. It does not print a thrust for the 2.05 engine, so 27.5 kN and 2.7 t "
  "remain unconfirmed as the earlier rating.")
K("CF-EUROPE-11", "ENG-DE-AESTUS", "performance.pc",
  [("chamber_pressure 11 bar", "SRC-WIKI-AESTUS", "T"), ("10.0 bar", "SRC-MECAIND-2020-T1", "N"),
   ("about 3000 K at a combustion pressure of 11 bar; Combustion chamber pressure 11 bar", "SRC-DB05-ASTRIUM-AESTUS-BROCHURE", "AEB")],
  "RESOLVED", "primary_value_found",
  "The maker's brochure (EADS Astrium, archive capture) gives a combustion chamber pressure of 11 bar, the "
  "encyclopedia's value. The journal's 10.0 bar was never read (HTTP 403; no archive capture) and may describe the "
  "earlier engine; the brochure does not say the pressure changed.")
K("CF-EUROPE-12", "ENG-DE-AESTUS", "propellants.mixture_ratio",
  [("mixture_ratio 1.9", "SRC-WIKI-AESTUS", "T"), ("2.05", "SRC-MECAIND-2020-T1", "N"),
   ("adjusting propellant mixture ratio from 2.05 to 1.90 with a first flight on an Ariane 5 flight 518 on 26 February 2004",
    "SRC-WIKI-AESTUS", "T")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "The encyclopedia's own history section says the mixture ratio was changed from 2.05 to 1.90 in the 1999-2002 "
  "improvements, first flown on flight 518 (2004): two epochs, not two readings of one value. The maker's brochure "
  "(EADS Astrium, archive capture read 2026-10-30) states the same change: 'adjusted from 2.05 to 1.9', first flown on "
  "flight 518. The journal table refused access (HTTP 403).")
K("CF-EUROPE-23", "ENG-DE-BMW-109-558", "performance.thrust",
  [("3.7 kN for 33 s, followed by 0.588 kN for 24 s", "SRC-WIKI-BMW109558", "T"), ("375 kg falling to 60 kg", "SRC-NASM-BMW109558", "N")],
  "EXPLAINED", "unit",
  "375 kgf is 3.68 kN and 60 kgf 0.588 kN DERIVED: the two describe the same two-level thrust in different units.")
K("CF-EUROPE-24", "ENG-DE-HWK-109-507", "performance.thrust",
  [("590 kgf for 10 s", "SRC-WIKI-HWK109507", "NF"),
   ("The initial thrust of 600 kg (1300 lb.) declined to 400 kg (900 lb.) during the 10 second duration", "SRC-NASM-HWK109507", "NHWK")],
  "PARTIALLY_RESOLVED", "different_operating_point",
  "The Smithsonian record, read from an archive capture, gives a blow-down: 600 kg at ignition falling to 400 kg over "
  "the 10 s burn as the air bottles emptied. DB-0's 590 kgf is within 2 percent of the initial figure, but the current "
  "encyclopedia revision no longer prints it, so its source is not seen.")
K("CF-EUROPE-28", "ENG-FR-HM7", "identity.designation",
  [("HM7 (history section)", "SRC-WIKI-HM7B", "NF"), ("Third stage Powered by 1 HM7-A", "SRC-WIKI-ARIANE1", "T")],
  "EXPLAINED", "definition", "HM7-A is the Ariane 1 build of the HM7; the names describe one engine at two levels.")
K("CF-ASIA_OTHER-6", "ENG-CN-YF-1", "geometry.chamber_count",
  [("YF-1: Configuration Chamber 1", "SRC-WIKI-YF1", "T"), ("1 YF-2A (4 x YF-1A)", "SRC-WIKI-CZ1", "T")],
  "EXPLAINED", "definition", "The YF-1 is single-chamber; the YF-2A is a four-engine module of YF-1A. Naming, not conflict.")
K("CF-ASIA_OTHER-9", "ENG-CN-YF-73", "history.first_flight",
  [("First flight 1984-01-29", "SRC-WIKI-YF73", "T"), ("1987-01-29 (mirror copies)", "SRC-WIKI-YF73", "NF")],
  "EXPLAINED", "rating_or_rounding",
  "The article prints 1984-01-29; the mirror's 1987 is a transcription slip (same day and month).")
K("CF-SPACECRAFT-5", "ENG-US-R-42", "mechanical.mass",
  [("R-42 890 N 305 sec ... 4.53 kg", "SRC-L3H-BIPROP-2023", "L3B23"), ("~6.58 kg", "SRC-L3H-BIPROP-2024", "N"),
   ("R-42 890 N 305 sec ... 4.53 kg (02/2024 edition)", "SRC-L3H-LHX-SPECSHEET-2024", "L3B24")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "Two maker sheets, June 2023 and February 2024, read from archive captures, both give the R-42 4.53 kg. The July 2024 "
  "sheet with 6.58 kg has no archive capture, so whether it describes a heavier build or another definition is not seen.")
K("CF-SPACECRAFT-6", "ENG-US-R-40B", "mechanical.mass",
  [("R-40B 4,000 N 293 sec ... 10.5 kg", "SRC-L3H-BIPROP-2023", "L3B23"), ("~15.9 kg", "SRC-L3H-BIPROP-2024", "N"),
   ("R-40B 4,000 N 293 sec ... 10.5 kg (02/2024 edition)", "SRC-L3H-LHX-SPECSHEET-2024", "L3B24")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "The June 2023 and February 2024 maker sheets both give the R-40B 10.5 kg. The July 2024 sheet's 15.9 kg has no archive "
  "capture and stays unread.")
K("CF-SPACECRAFT-7", "ENG-US-MR-103J", "performance.thrust_range",
  [("MR-103J 1.13-0.19 N", "SRC-L3H-MONO-2023", "L3M23"), ("MR-103J 0.043-0.27 (0.19-1.19) [lbf (N)]", "SRC-L3H-MONO-2025", "L3M25")],
  "EXPLAINED", "different_epoch",
  "Both maker sheets read from archive captures. The 2023 edition gives 1.13-0.19 N; the October 2025 edition gives "
  "0.043-0.27 lbf with 0.19-1.19 N in parentheses. The later sheet carries the higher upper limit; which edition is current "
  "is a matter of date, and 0.27 lbf is 1.20 N DERIVED.")
K("CF-SPACECRAFT-8", "ENG-US-MR-111G", "performance.thrust_range",
  [("MR-111G 4.9-1.8 N", "SRC-L3H-MONO-2023", "L3M23"), ("MR-111G 1 lbf 0.2-1.3 (0.9-5.7) [lbf (N)]", "SRC-L3H-MONO-2025", "L3M25")],
  "EXPLAINED", "different_epoch",
  "Both maker sheets read from archive captures: 4.9-1.8 N in the 2023 edition, 0.2-1.3 lbf (0.9-5.7 N) in the October "
  "2025 edition. The range was widened between editions.")
K("CF-TAXONOMY-TAX-6", "ENG-US-DELPHIN", "performance.thrust_sl",
  [("Thrust per Engine 6,300 lbf SL ... Total Thrust 31,500 lbf SL", "SRC-ASTRA-R31-PRESSKIT", "AST"), ("6,500 lbf", "SRC-ASTRA-R31-PRESSKIT", "NF"),
   ("Powered by 5 Delphin, Maximum thrust c. 32,500 lbf (145 kN)", "SRC-WIKI-ASTRA-ROCKET", "T")],
  "RESOLVED", "primary_value_found",
  "Astra's Rocket 3.1 press kit (2020), read from an archive capture, gives 6,300 lbf per Delphin at sea level and "
  "31,500 lbf for five. It prints no 6,500 lbf; the encyclopedia's 32,500 lbf total (6,500 each DERIVED) has no maker "
  "source. Later Rocket 3.x builds are not covered by the kit.")

D("SRC-DB05-NASDA-LE7A-FT6-1997", identifier="宇宙開発委員会 第16回 資料 委16-4 (1997-05-14), MEXT archive PDF",
  title="LE－7Aエンジン燃焼試験結果（種子島第6回）について", tier="A",
  rights_checked="Japanese government committee document on the MEXT site; reuse terms not reviewed",
  rights_class="RIGHTS_REVIEW_REQUIRED",
  note="3 pages, text layer. Read for the LE-7A pc conflicts only: development firing test 6 (1997-05-09), 277 s, main "
       "combustion pressure about 120 kgf/cm2a, LH2 turbopump about 41,600 rpm, LOX turbopump about 18,100 rpm.")

D("SRC-DB05-PATENT-US6996973", identifier="US 6,996,973 B2 (ESA, inventor C. Dujarric; priority FR 9903742, 1999-03-25), Google Patents text",
  title="Method of achieving jet separation of an un-separated flow in a divergent nozzle body of a rocket engine", tier="B",
  rights_checked="US patent text, public record", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Read for the Vulcain 2 area ratio only: 'area ratio R equal to 60 for a specific impulse of 433 seconds' (environment "
       "of the 433 s not printed), Psep about 0.22 bar.")
D("SRC-DB05-NTRS-20170008949", identifier="NTRS 20170008949",
  title="Carbon-Carbon Nozzle Extension Development in Support of In-Space and Upper-Stage Liquid Rocket Engines", tier="A",
  rights_checked="NTRS determination GOV_PUBLIC_USE_PERMITTED; not export controlled", rights_class="VALUES_WITH_ATTRIBUTION",
  note="27 pages. Searched for the RL10B-2 mass (CF-DB05-E-R2_US_CLASSIC-B2-4): the paper describes the RL10B-2 C-C "
       "nozzle extension history but prints no engine mass. No value taken.")

D("SRC-DB05-ULA-DELTA4-UG-2013", identifier="Delta IV Launch Services User's Guide, June 2013 (United Launch Alliance; DoD public release 13-S-1948)",
  title="Delta IV Launch Services User's Guide", tier="B",
  rights_checked="'Copyright © 2013 by United Launch Alliance. All rights reserved'; cleared for public release",
  rights_class="RESTRICTED_REFERENCE",
  note="293 pages, text layer. Read sections 1.2.1-1.2.2 (pp. 1-5 to 1-7): RS-68A 3137kN (705,250 lbf) sea level, 411.9 s "
       "vacuum, 21.5 to 1; RL10B-2 110 kN (24,750 lb), 465 s, electromechanical gimbal actuators. No chamber pressure or "
       "engine mass. Used as conflict claims only; no assertion taken.")

D("SRC-DB05-ARIANESPACE-A5UM-I5R2", identifier="Ariane 5 User's Manual, Issue 5 Revision 2, October 2016 (Arianespace); copy hosted as a DelftX course asset on edX",
  title="Ariane 5 User's Manual", tier="B", rights_checked="'Arianespace©' in every page header; not obtained from arianespace.com",
  rights_class="RESTRICTED_REFERENCE",
  note="271 pages, text layer. Read the EPC and ESC-A tables (p.1-7) and the Ariane 5 ECA description (pp.A4-2, A4-3). HM7B: 67 kN, 'maximum thrust in vacuum', 446 s, 945 s. Vulcain 2 960 kN (SL) / "
       "1390 kN (vacuum), 'maximum thrust in vacuum', Isp ~310 s (SL) / 432 s (vacuum), 540 s. No chamber pressure, area ratio "
       "or flow rates. Used as conflict claims only; no assertion taken.")

# LE-7A chamber pressure primaries (2026-10-29): used as conflict claims only; LE-7A is not carried (wave-3 manifest)
D("SRC-DB05-JAXA-LE7A-ENGINE-PAGE", identifier="rocket.jaxa.jp/rocket/engine/le7/ (JAXA Space Transportation Technology Directorate)",
  title="LE-7A｜エンジン｜H-IIAロケット｜ロケット｜JAXA 宇宙輸送技術部門", tier="A", rights_checked="'©Japan Aerospace Exploration Agency'",
  rights_class="RESTRICTED_REFERENCE",
  note="Specification table: LE-7 / LE-7A short nozzle / LE-7A long nozzle. 燃焼圧力 12.7MPa (LE-7), 12.3MPa (LE-7A); MR 6.0 / 5.9 / "
       "5.9; 膨張比 約51.6 / 約38.7 / 約46.7; LH2 TP 42,200 / 41,900 / 41,900 回転/min.")
D("SRC-DB05-MHI-GIHO-534036", identifier="三菱重工技報 Vol.53 No.4 (2016) pp.36-43",
  title="H3ロケット１段用LE-9エンジンの燃焼安定性向上", tier="A", rights_checked="MHI technical review PDF; reuse terms not reviewed",
  rights_class="RESTRICTED_REFERENCE",
  note="Table 1 (p.37) compares LE-9, LE-7A and LE-5B. LE-7A: 1098 kN vacuum, MR 5.9, 燃焼圧力 12.3（主燃焼室） MPa, 440 s, "
       "expansion 47, 1.8 t, 3.7 m.")
D("SRC-DB05-MEXT-H2F8-REPORT", identifier="宇宙開発委員会 H-II F8 failure investigation report, MEXT archive 1335987_007_5.pdf",
  title="Ｈ－Ⅱロケット８号機打上げ失敗の原因究明及び今後の対策について", tier="A",
  rights_checked="Japanese government committee document on the MEXT site; reuse terms not reviewed",
  rights_class="RIGHTS_REVIEW_REQUIRED",
  note="12 pages. 別添表８－２ gives LE-7A design values beside the LE-7: main combustion pressure 12.2 MPa (LE-7 12.7), preburner "
       "21.5 MPa, chamber mixture ratio 6.2, 1098 kN vacuum (1074 kN in parentheses), 4295 m/s.")
D("SRC-DB05-JAXA-H2BF3-LE7A-AT", identifier="jaxa.jp/projects/rockets/h2b/engine/le7a/10/08/02_j.html",
  title="H-IIBロケット3号機用LE-7Aエンジンの燃焼試験結果", tier="A", rights_checked="JAXA web page", rights_class="RESTRICTED_REFERENCE",
  note="2010-08-19 performance-confirmation firing (性能確認試験) at Tashiro, 50 s: メイン燃焼圧力 約 12.3 Mpa (planned 11.7-13.2), fuel TP 42,100 rpm, oxidizer TP 18,400 rpm. "
       "A measured test value, not a rating.")

D("SRC-DB05-CNES-A5-LANCEUR", identifier="cnes.fr/projets/ariane-5/lanceur (CNES Ariane 5 project page, French)",
  title="Ariane 5 — le lanceur", tier="A", rights_checked="CNES web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Static text (11 kB extracted). Vulcain 'pesait 1 650 kg'; Vulcain 2 '1 390 kN (139 tonnes) de poussée dans le vide'; HM-7B "
       "'jusqu'à 15 minutes et 45 secondes' and '67 kN (6,7 tonnes)'; Aestus '29 kN (2,9 tonnes) de poussée dans le vide'. Used as "
       "conflict claims only.")

D("SRC-DB05-ULA-VULCAN-UG-2023", identifier="Vulcan Launch Systems User's Guide, October 2023 (United Launch Alliance)", title="Vulcan Launch Systems User's Guide",
  tier="B", rights_checked="ULA user's guide PDF; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="85 pages. Table 1.4-1 and p.1-5: BE-4 2446.5 kN (550k-lbf) sea level each. Used as a conflict claim only.")

D("SRC-DB05-ESA-BULLETIN-102-VULCAIN2", identifier="ESA Bulletin 102 (May 2000), D. Coulon, Coulon102.pdf", tier="A",
  title="Vulcain-2 Cryogenic Engine Passes First Test with New Nozzle Extension",
  rights_checked="ESA Bulletin article on esa.int; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="2 pages, text layer. Table 1 (development era, after the 1999 P5 firings): vacuum thrust 1 350 kN, specific impulse 433 s, "
       "chamber pressure 115 bar, mixture ratio 6.10, section ratio 58.5, total propellant flow 320 kg/s, mass 1935 kg, LOX TP "
       "12 600 rpm, LH2 TP 35 500 rpm. Text: MR raised from 5.3 to 6.1; thrust 1145 to 1350 kN; LH2 TP nominal 35680 rpm, "
       "14.29 MW, 44.9 kg/s. Used as conflict claims only.")

D("SRC-DB05-ESA-BULLETIN-123-A5ECA", identifier="ESA Bulletin 123 (August 2005), U. L. Berkes, bul123b_berkes.pdf", title="Ariane-5 ECA", tier="A",
  rights_checked="ESA Bulletin article on esa.int; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="6 pages, text layer. Vulcain-2 '1350 kN compared with the 1100 kN of Vulcain-1', up to 540 s; ESC-A 'maximum of 970 "
       "seconds of propelled flight', HM-7B 'thrust of 65 kN in vacuum, with a specific impulse of 447 seconds'. Used as conflict "
       "claims only.")

D("SRC-DB05-ESA-PR-1994-35-EPS", identifier="ESA Press Release N° 35-1994 (14 October 1994)",
  title="Ariane 5 - Successful first long duration test of the storable propellant stage", tier="A",
  rights_checked="ESA press release on esa.int; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Aestus 'thrust = 27.5 kN'; 'consumes, in vacuo, in 1130 seconds' 3.2 t MMH and 6.3 t N2O4; nominal operation about 1100 s; "
       "EPS long-duration firing 1075 s on 5 October 1994. No chamber pressure or mixture ratio. Used as a conflict claim only.")

D("SRC-DB05-NTRS-19710070145", identifier="NTRS 19710070145", title="XLR99 engine operating experience", tier="A",
  rights_checked="NTRS determination GOV_PUBLIC_USE_PERMITTED", rights_class="VALUES_WITH_ATTRIBUTION",
  note="12 pages, OCR text layer (D. R. Bellman, N. E. DeMar, 1961). Data list: dry weight 910 pounds; Isp 250 s SL, "
       "265 s at 45,000 ft; rated thrust 50,000 lb SL, 57,000 lb at 45,000 ft; area ratio 9.8; pc 600 psia. Table I "
       "lists dry and wet weights by specification. Used as a conflict claim only.")

D("SRC-DB05-NTRS-19630006100", identifier="NTRS 19630006100", title="From Peenemuende to Outer Space (MSFC commemorative volume, 1962)",
  tier="B", rights_checked="NTRS determination GOV_PUBLIC_USE_PERMITTED", rights_class="VALUES_WITH_ATTRIBUTION",
  note="841 pages, OCR text layer; papers by Marshall staff. Chapter 13 (PDF p.297-300): the Jupiter S-3D 'produced a "
       "thrust of 150,000 lb' on LOX/RP-1, first Jupiter launch with it March 1957; H-1 fixed thrust 188,000 lb; 1.5 "
       "million lb engine (F-1) contract early 1959. A retrospective agency history rather than an engine test report, "
       "so tier B. Used as a conflict claim only.")

D("SRC-DB05-NTRS-19680014530", identifier="NTRS 19680014530 (Aerojet-General, contract NAS 3-2555)",
  title="Development of liquid oxygen/liquid hydrogen thrust chamber for the M-1 engine", tier="A",
  rights_checked="NTRS determination GOV_PUBLIC_USE_PERMITTED", rights_class="VALUES_WITH_ATTRIBUTION",
  note="305 pages, OCR text layer (15 May 1968). Design point: thrust 1,500,000 lb with a 40:1 nozzle (1,200,000 lb with "
       "a 2:1 uncooled chamber), Pc (plenum) 1,000 psia, MR 5.49, 2,872 lb/s O2 and 524 lb/s H2. Work described is that "
       "done 'prior to phaseout of the program'; uncooled-chamber firings on Test Stand H-8 in July-August 1966. Used as "
       "a conflict claim only.")

D("SRC-DB05-NAMMO-LEROS4", identifier='https://www.nammo.com/products/space/space-propulsion-thrusters-and-engines/leros-4/', title="LEROS 4 Interplanetary Engine (Nammo product page)", tier="A",
  rights_checked="manufacturer web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. LEROS 4 prose: '321 second Isp, MON/ Hydrazine apogee engine delivers a thrust of 1000 N', range 900-1100 N; specification table: Propellant MON-3/MMH, MR 1.65 (1.5-1.8), 321 s minimum, inlet 15.4 bara, mass 8.41 kg, max single firing 3,600 s. No LEROS 4-ET page. Used as a conflict claim only.")

D("SRC-DB05-IPROFESIONAL-VEX1A-2014", identifier='https://www.iprofesional.com/negocios/181740-tronador-ii-estallo-a-dos-metros-del-suelo-el-cohete-de-fabricacion-nacional', title="Tronador II: estalló a dos metros del suelo el cohete de fabricación nacional (iProfesional)",
  tier="C", rights_checked="news article; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. iProfesional news article, datePublished 2014-03-05: 'el lanzamiento se hizo el último miércoles 26 de febrero. Pero el vector Vex 1A, que logró despegar unos dos metros, ... se estrelló'; earlier attempts in December, mid-January and 24 February. The follow-up article of 2014-03-06 (181837) says the government first gave information on 'el lanzamiento del cohete efectuado el 26 de febrero desde la localidad de Pipinas'. Used as a conflict claim only.")

D("SRC-DB05-ARGGOB-TRONADOR2", identifier='https://www.argentina.gob.ar/node/71704', title='Tronador II (Argentina.gob.ar, CONAE programme page)', tier="A",
  rights_checked="government web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Undated programme page: 'En marzo del 2014 se realizó desde el Centro Espacial Punta Indio la primera prueba de un vehículo experimental que fue denominado Vex1A, utilizando como combustible hidracina y tetróxido de nitrógeno/ácido nítrico como oxidante'; configuration: 'monometil hidracina como combustible y tetróxido de nitrógeno/ácido nítrico como oxidante para la etapa superior', first stage LOX/kerosene; 'Etapa superior: Empuje en tierra en el rango de 1,5 a 4 toneladas (entre 2 y 5,5 toneladas en vacío). Motor de Tipo Presurizado.' Used as a conflict claim only.")

D("SRC-DB05-ARGGOB-2023-08-01", identifier='https://www.argentina.gob.ar/node/390734', title='Se llevó a cabo un ensayo de motor clave para el lanzador Tronador II (Argentina.gob.ar, 2023-08-01)', tier="A",
  rights_checked="government web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Government release of 1 August 2023: a prototype of the 'motor de segunda etapa que llevará la versión final del Tronador II' (engine RS2) was tested at Valthe, Córdoba; 'tecnología desarrollada y fabricada en el país, cuyo combustible es oxígeno líquido y kerosene'. Used as a conflict claim only.")

D("SRC-L3H-BIPROP-2023", identifier='https://web.archive.org/web/20251206122630/https://www.l3harris.com/sites/default/files/2023-07/AJRD-LHX_Bipropellant_Rocket_Engines_SpecSheet_CMYK_061423_APPROVED.pdf', title='AJRD/L3Harris Bipropellant Rocket Engines spec sheet (06/2023)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. 2-page L3Harris sheet '© 2023 ... la0151 23 | 06/2023', archive capture of 2025-12-06. Table rows: 'R-42 890 N 305 sec ... 4.53 kg'; 'R-40B 4,000 N 293 sec ... 10.5 kg'. Used as a conflict claim only.")

D("SRC-L3H-LHX-SPECSHEET-2024", identifier='https://web.archive.org/web/20240305132343/https://www.l3harris.com/sites/default/files/2024-02/L24789-AJRD-LHX-Bipropellant-Rocket-Engines-SpecSheet-APPROVED-022224.pdf', title='Bipropellant Rocket Engines spec sheet (L24789, 02/2024)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. 2-page L3Harris sheet '© 2024 ... L24789 | 02/2024', archive capture of 2024-03-05. Rows: 'R-4D-11 378-511 N 164:1 = 311 sec (lbf/lbm) 300:1= 315.5 sec ... 164:1= 3.76 kg 300:1= 4.31 kg'; 'R-42 890 N 305 sec ... 4.53 kg'; 'R-40B 4,000 N 293 sec ... 10.5 kg'. Used as a conflict claim only.")

D("SRC-L3H-MONO-2023", identifier='https://web.archive.org/web/20240201063211/https://www.l3harris.com/sites/default/files/2023-07/AJRD-LHX_Monopropellant_Rocket_Engines_SpecSheet_CMYK_061423_APPROVED.pdf', title='AJRD/L3Harris Monopropellant Rocket Engines spec sheet (06/2023)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. 2-page L3Harris sheet, archive capture of 2024-02-01. Rows (thrust in N): 'MR-103J 1.13-0.19 N 224-202 sec ... 0.37 kg'; 'MR-111G 4.9-1.8 N 229-219 sec ... 0.37 kg'. Used as a conflict claim only.")

D("SRC-L3H-MONO-2025", identifier='https://web.archive.org/web/20260325113549/https://www.l3harris.com/sites/default/files/2025-10/l3harris-ar-monopropellant-rocket-engines.pdf', title='L3Harris AR monopropellant rocket engines sheet (Oct 2025)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. 2-page L3Harris sheet (2025-10 path), archive capture of 2026-03-25; thrust in lbf with N in parentheses. Rows: 'MR-103J 0.2 lbf 0.043-0.27 (0.19-1.19) 202-224 ...'; 'MR-111G 1 lbf 0.2-1.3 (0.9-5.7) 219-230 ...'. Used as a conflict claim only.")

D("SRC-ASTRA-R31-PRESSKIT", identifier='https://web.archive.org/web/20200914021239/https://astra.com/wp-content/uploads/2020/08/Rocket-3.1-Launch-Press-Kit.pdf', title='Rocket 3.1 Launch Press Kit (Astra, 2020)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. 6-page Astra press kit, archive capture of 2020-09-14. Vehicle table (p.5): 'Engines Delphin Aether Engine Qty 5 1 Thrust per Engine 6,300 lbf SL 665 lbf vacuum Total Thrust 31,500 lbf SL'. No 6,500 lbf figure is printed. Used as a conflict claim only.")

D("SRC-BLUE-ENGINES", identifier='https://web.archive.org/web/20260714070950/https://www.blueorigin.com/engines', title='Blue Origin engines page (capture of 2026-07-14)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Blue Origin engines page, archive capture of 2026-07-14: 'BE-4 Thrust : 640,000 lbf (2,846 kN) with deep throttle capability to 220,000 lbf (978 kN)'; 'BE-3U Thrust : 200,000 lbf (890 kN) with ability to throttle to 100,000 lbf (445 kN)'; 'BE-3U is an open-expander cycle engine.' Read from the archive; blueorigin.com itself was not contacted. Used as a conflict claim only.")

D("SRC-BLUE-NEWS-BE3U-MISC", identifier='https://web.archive.org/web/20240927010748/https://www.blueorigin.com/news/new-glenn-completes-second-stage-hotfire', title='New Glenn completes second stage hotfire (Blue Origin release, 2024-09-23)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Blue Origin release datePublished 2024-09-23, archive capture of 2024-09-27: 'BE-3U's elegant expander bleed design ...'; 'Each of the two BE-3Us that will fly on NG-1 were originally designed to yield up to 160,000 lbf of vacuum thrust. The engine has outperformed throughout its test campaign and will fly at 173,000 lbf'. Used as a conflict claim only.")

D("SRC-BLUE-NG-UPGRADE", identifier='https://web.archive.org/web/20251205152358/https://www.blueorigin.com/news/new-glenn-upgraded-engines-subcooled-components-drive-enhanced-performance', title='New Glenn upgraded engines, subcooled components drive enhanced performance (Blue Origin release, 2025-11-20)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Blue Origin release datePublished 2025-11-20, archive capture of 2025-12-05: 'BE-4 has already demonstrated 625,000 lbf on the test stand at current propellant conditions and will achieve 640,000 lbf later this year, with propellant subcooling increasing the current thrust capability from the existing 550,000 lbf'; 'The total thrust of the two BE-3Us ... is increasing from the original design of 320,000 lbf (1,423 kN) to 400,000 lbf (1,779 kN) thrust over the next few missions. BE-3U has already demonstrated 211,658 lbf ...'. Used as a conflict claim only.")

D("SRC-BLUE-ULA-PARTNERSHIP", identifier='https://web.archive.org/web/20190727222445/https://www.blueorigin.com/news/ula-and-blue-origin-announce-partnership-to-develop-new-american-rocket-engine', title='ULA and Blue Origin Announce Partnership To Develop New American Rocket Engine (2014)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Blue Origin release of 2014, archive capture of 2019-07-27: 'The BE-4 is a liquid oxygen, liquefied natural gas (LNG) rocket engine that delivers 550,000-lbf of thrust at sea level. Two BE-4s will power each ULA booster, providing 1,100,000-lbf thrust at liftoff.' Used as a conflict claim only.")

D("SRC-NASM-A19600013000", identifier='https://web.archive.org/web/20250405012409/https://airandspace.si.edu/collection-objects/turbopump-steam-generator-and-frame-v-2-rocket-engine/nasm_A19600013000', title='Turbopump, Steam Generator and Frame, V-2 Rocket Engine (NASM A19600013000)', tier="D",
  rights_checked="record read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Smithsonian NASM record A19600013000 (V-2 turbopump, steam generator and frame), archive capture of 2025-04-05: 'liquid oxygen and 75% alcohol'; 'At a thrust of 25 metric tons (about 56,000 lb)'; 'The turbopump had to move approx. 9700 kg (21,400 lb.) of liquid oxygen from the tanks to the engine during the sixty-second burning time.' Used as a conflict claim only.")

D("SRC-NASM-A19790951000", identifier='https://web.archive.org/web/20250402174429/https://airandspace.si.edu/collection-objects/turbopump-v-2-cutaway/nasm_A19790951000', title='Turbopump, V-2, Cutaway (NASM A19790951000)', tier="D",
  rights_checked="record read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Smithsonian NASM record A19790951000 (V-2 turbopump, cutaway), archive capture of 2025-04-02: 'This pump moved nearly 9,000 kg (20,000 lb) of alcohol and liquid oxygen from the tanks to the combustion chamber during the 60-second burning time.' Used as a conflict claim only.")

D("SRC-CALTECH-THESIS310", identifier='https://web.archive.org/web/20250708113841/https://thesis.library.caltech.edu/310/', title='Gas Generation by Chemical Reaction for Pressurizing Liquid Rocket Propellants', tier="B",
  rights_checked="record read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. CaltechTHESIS record 310, 'Gas Generation by Chemical Reaction for Pressurizing Liquid Rocket Propellants' (Engineer's thesis, GALCIT, defended June 1947; DOI 10.7907/7T6E-3D20), abstract read from archive capture of 2025-07-08: 'The Wac Corporal is a sounding rocket of 590 lbs. gross weight using red fuming nitric acid and aniline as propellants.' Used as a conflict claim only.")

D("SRC-NASM-HWK109507", identifier='https://web.archive.org/web/20250405013608/https://si.edu/object/rocket-engine-walter-hwk-109-507:nasm_A19771225000', title='Rocket Engine, Walter HWK 109-507 (A19771225000)', tier="D",
  rights_checked="record read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note='Fetched 2026-10-29. Smithsonian record nasm_A19771225000 (Walter HWK 109-507), archive capture of 2025-04-05: \'Hydrogen peroxide in 80% concentration (codenamed "T-Stoff") was mixed with a calcium permanganate catalyst ("Z-Stoff")\'; \'The initial thrust of 600 kg (1300 lb.) declined to 400 kg (900 lb.) during the 10 second duration of the engine due to dropping air pressure from bottles\'. Used as a conflict claim only.')

D('SRC-L3H-RS68A-DS', identifier='https://web.archive.org/web/20230130163723/https://www.rocket.com/sites/default/files/documents/RS-68A_data_sheet.pdf', title='RS-68A data sheet', tier='A',
  rights_checked="maker data sheet read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-30. Aerojet Rocketdyne RS-68A data sheet (cp0283 15 RS-68, REV 3-19, dated March 2019), read from the Internet Archive capture of 2023-01-30 at www.rocket.com (the l3harris supplier URL is 404). Specifications, full power / minimum power: 'Thrust (Vacuum): 800K lbf / 412K lbf'; 'Thrust (Sea Level): 705K lbf / 318K lbf'; 'Chamber Pressure: 1580 psia / 820 psia'; 'Engine Mixture Ratio: 5.97 / 5.99'; 'Isp, Vacuum: 411 sec / 411 sec'; 'Isp, Sea Level: 362 sec / 317 sec'; height 17.1 ft, weight 14,740 lbs, diameter 8 ft, expansion ratio 21.5 (column layout of the extracted text; values in the order of the labels). Used as a conflict claim only.")

D('SRC-DB05-LAUNCHER-E2-PAGE-2019', identifier='https://web.archive.org/web/20190920102132/https://launcherspace.com/engine-2', title="Engine-2 (Launcher Inc. web page, captured 2019-09-20)", tier="A",
  rights_checked="maker web page read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-30. Launcher Inc. 'Engine-2' web page, Internet Archive capture of 2019-09-20: 'Generating 10 tonne-force of thrust per engine (22,000 lbf)'; 'Optimal oxidizer / fuel mixture ratio (2.62)'; 'Performance: 365s specific impulse (Second stage nozzle). First stage nozzle - 327s vacuum, 290s sea level'. Design figures, before the 2022 full-scale test. The trade article of May 2022 (control.com, archive capture 2022-05-10) prints 22,046 lbf, mixture ratio 2.62 and 100 bar but no specific impulse. Used as a conflict claim only.")

D('SRC-DB05-KBKHM-14D30-2016', identifier='https://web.archive.org/web/20160304054857/http://kbhmisaeva.ru/main.php?id=52', title='Двигатель 14Д30. Разгонный блок «Бриз-М» (KB Khimmash im. A.M. Isaeva web page, captured 2016-03-04)', tier="A",
  rights_checked="maker web page read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-30. KB Khimmash (Isaev) page for the 14D30 (S5.98M) Briz-M main engine, Internet Archive capture of 2016-03-04 (same table in the 2013-04-23 capture; the page is gone from the 2021 site). 'Тяга 2000 кгс'; 'Массовое соотношение расходов компонентов топлива 2,0 ±0,04'; 'Удельный импульс тяги 328,6 с'; 'Давление в камере 100 кгс/см2'; 'Число оборотов ротора ТНА 54 000 об/мин'; dry mass 95 kg; 8 starts; 3,200 s total, 2,500 s longest single burn. Propellants AT/UDMH. No condition printed for the impulse (an upper-stage engine). Used as a conflict claim only.")

D('SRC-DB05-ASTRIUM-AESTUS-BROCHURE', identifier='https://web.archive.org/web/20160430023049/http://www.space-propulsion.com/brochures/launcher-propulsion/Aestus.pdf', title='AESTUS: Upper Stage Engine (EADS Astrium Space Transportation brochure, space-propulsion.com)', tier="A",
  rights_checked="maker brochure read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-30. EADS Astrium brochure, 4 pages, read from the Internet Archive capture of 2016-04-30 (undated; mentions the first ATV launch of March 2008). Text: developed at Ottobrunn 1988-1995, first operational flight on 502 (30 October 1997); 'combustion temperature ... about 3000 K at a combustion pressure of 11 bar'; 'a delta-qualification programme was performed in 1999 - 2002. Here, the propellant mixture ratio of Aestus was adjusted from 2.05 to 1.9. Subsequently, the first operational flight of the performance enhanced Aestus was on Ariane 5 flight 518, launched on 26 February 2004.' Technical data (labels and values in order): N2O4/MMH; specific impulse vacuum 324 s; thrust vacuum 29.6 kN; propellant mass flow rate 9.3 kg/s; mixture ratio (TC) 1.9; engine feed pressure 17.7 bar; combustion chamber pressure 11 bar; overall engine length 2.2 m; thrust chamber mass 111 kg; nominal single firing 1100 s (the area-ratio and exit-diameter values did not extract). Used as a conflict claim only.")

D('SRC-DB05-NTRS-19790003958', identifier="NASA TM-75376; NTRS 19790003958", title='Otrag rocket experiments in Africa (NASA TM-75376; Der Spiegel No. 33, 1978, pp. 52-65)', tier="B",
  rights_checked="translation of a copyrighted magazine article; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-30. NASA Technical Memorandum TM-75376 (NTRS 19790003958, December 1978), 35-page translation of a Der Spiegel article of August 1978. It describes the idea of 'fueling rocket engines with commercial diesel oil and nitric acid instead of with expensive special fuels' and, in a box on the design, 'As low cost fuel, a mixture of simple diesel oil and nitric acid is proposed'. A contemporary press account, not a design document; OCR is poor. Used as a conflict claim only.")

D('SRC-NASA-HOPSON-STS104-FRR-2001', identifier='govdocs1 corpus 673547.pdf (also 675066 / 655318 hits)', title='STS-104 SSME Flight Readiness Review (Hopson), 28 June 2001', tier='A',
  rights_checked="US government briefing charts in a public corpus; values only", rights_class="RESTRICTED_REFERENCE",
  note="Read 2026-10-31. G. Hopson, 'Atlantis STS-104 ... SSME Block II' flight-readiness charts dated 28 June 2001 (file 104Prog.PPT), 6 pages, govdocs1 file 673/673547.pdf read 2026-10-31 from the Digital Corpora archive. Page 3 'SSME Engine Comparison': at 104 / 104.5 / 104.5 % for Block I / Block IIA / Block II, MCC Pc 3140 / 2870 / 2870 psia, HPFT discharge temperature 1694 / 1601 / 1615 R, HPOT discharge 1340 / 1215 / 1223 R; at 109 %, Pc 3291 / 2994 / 2994, HPFT 1718 / 1629 / 1638 R, HPOT 1374 / 1234 / 1246 R; Block II by power level 100-111 %: Pc 2747-3050 psia, HPFT 1594-1658 R. Used as a conflict claim only.")

D('SRC-DB05-SSAU-420-2006', identifier='https://journals.ssau.ru/vestnik/article/download/420/423', title='Внедрение соплового насадка радиационного охлаждения из УУКМ на камеру маршевого двигателя 11Д58М разгонного блока ДМ-SL (Vestnik SSAU, 2006)', tier="A",
  rights_checked="open-access journal article; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-31. A.V. Mezhevov, V.I. Skoromnov, A.V. Kozlov, N.N. Tupitsyn, V.G. Khaspekov (RSC Energia), Vestnik SSAU 2006, 6 pages. 'Таблица 1. Основные характеристики ЖРД 11Д58М': РГ-1 / О2ж; 'Тяга, кН 85'; 'Удельный импульс тяги, с 356'; 'Давление в камере, МПа 7,9'; 'Соотношение компонентов топлива 2,82'; 'Геометрическая степень расширения сопла 280'; 7 starts; 1200 s total. The table is for the engine with the new carbon-carbon nozzle extension (НРО-М), which raised the geometric expansion ratio from 94 to 280; flight tests on DM-SL gave a mean Isp gain of 4.5 s (the English abstract says 4 s). Used as a conflict claim only.")

D('SRC-DB05-NASM-A19771237000', identifier='https://web.archive.org/web/20250420052236/https://airandspace.si.edu/collection-objects/rocket-engine-turbopump-and-accessories-v-2/nasm_A19771237000', title='Rocket Engine, Turbopump and Accessories, V-2 (Smithsonian NASM record A19771237000)', tier="B",
  rights_checked="museum record read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-31. Smithsonian NASM record A19771237000, Internet Archive capture of 2025-04-20 (the live site refused the request): 'The turbopump moved approx. 4200 kg (9200 lb) of water alcohol and 5500 kg (12,200 lb) of liquid oxygen from the tanks to the engine during the 60-second burning time. Driving the turbopump was the steam generator, which used hydrogen peroxide mixed with a catalyst.' No peroxide concentration. Gift of Thiokol, from Reaction Motors. Used as a conflict claim only.")
