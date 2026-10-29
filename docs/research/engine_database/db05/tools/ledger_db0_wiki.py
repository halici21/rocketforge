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
  [("1,615 R (Block II row)", "SRC-NASA-HOPSON-STS104-FRR-2001", "N"), ("1,601 R (other row)", "SRC-NASA-HOPSON-STS104-FRR-2001", "N")],
  "UNRESOLVED", "intra_document",
  "Both values come from one flight-readiness chart that the mirror would not serve on retry (connection failed). "
  + _PRIMARY)
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
  [("1580 psia", "SRC-L3H-RS68A-DS", "N"), ("Chamber pressure 1,488 psi (10.26 MPa)", "SRC-WIKI-RS68", "T")],
  "UNRESOLVED", "different_variant",
  "The encyclopedia gives one chamber pressure for RS-68 and RS-68A together; the manufacturer's datasheet URL and its "
  "product page return 404, and the ULA Delta IV user's guide (2013) prints thrust, Isp and area ratio but no chamber "
  "pressure. " + _PRIMARY)
K("CF-R2_SCHEM-R2-2", "ENG-US-RS-68A", "performance.isp_vac",
  [("411 s", "SRC-L3H-RS68A-DS", "N"), ("RS-68A: 411.9 s", "SRC-WIKI-RS68", "T"),
   ("having a vacuum specific impulse of 411.9 sec", "SRC-DB05-ULA-DELTA4-UG-2013", "U15")],
  "EXPLAINED", "rating_or_rounding",
  "The launch provider's 2013 user's guide prints 411.9 s vacuum for the RS-68A, as the encyclopedia does. The 411 s "
  "seen in a search summary of the 404 datasheet is the same figure without its decimal.")
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
  [("9,700 kg / 62 s", "SRC-NASM-A19600013000", "N"), ("9,000 kg / 60 s", "SRC-NASM-A19790951000", "N")],
  "UNRESOLVED", None, "Both Smithsonian records were unreachable on retry. " + _PRIMARY)
K("CF-R2_SCHEM-R2-13", "ENG-DE-A4-ENGINE", "propellants.load_mass",
  [("~9,700 kg LOX over 60 s", None, "X"), ("4,200 kg water-alcohol + 5,500 kg LOX", None, "X")],
  "UNRESOLVED", "definition",
  "No source ids. 4,200 + 5,500 = 9,700 kg, so one claim is likely total propellant mislabelled as LOX. " + _PRIMARY)
K("CF-R2_USSR-R2-11", "ENG-SU-RD-107A", "performance.thrust_vac",
  [("vac: 1,021.3 kN", "SRC-WIKI-SOYUZFG", "T"), ("vac: 1,019.93 kN", "SRC-WIKI-SOYUZ-CSG", "T"), ("thrust(Vac) 1,020 kN", "SRC-WIKI-RD107", "T")],
  "EXPLAINED", "rating_or_rounding", "Three encyclopedia pages within 0.14 percent: one value at different precision.")
K("CF-R2_USSR-R2-12", "ENG-SU-RD-216", "aliases.index",
  [("RD-216 (GRAU index: 8D514)", "SRC-WIKI-RD215", "T"), ("11D614", None, "X")],
  "UNRESOLVED", None, "The article gives 8D514 for the RD-216 module; 11D614 has no source. " + _PRIMARY)
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
  [("Date 1962-1968 (infobox)", "SRC-WIKI-RD270", "T"), ("designed ... in 1960-1970 (prose)", "SRC-WIKI-RD270", "T")],
  "UNRESOLVED", "intra_document", "One article gives two spans, infobox against prose. " + _PRIMARY)
K("CF-USSR-17", "ENG-SU-RD-270", "history.period",
  [("Date 1962-1968 (infobox)", "SRC-WIKI-RD270", "T"), ("designed ... in 1960-1970 (prose)", "SRC-WIKI-RD270", "T")],
  "UNRESOLVED", "intra_document", "Same pair as CF-DB05-E-R2_USSR-R2-17.")
K("CF-TAXONOMY-TAX-4", "ENG-SU-RD-270", "history.cancellation",
  [("designed ... in 1960-1970", "SRC-WIKI-RD270", "T"), ("Date 1962-1968", "SRC-WIKI-RD270", "T")],
  "UNRESOLVED", "intra_document", "Same pair as CF-DB05-E-R2_USSR-R2-17.")
K("CF-R2_USSR-R2-18", "ENG-RU-S5-98M", "performance.isp_vac",
  [("Specific impulse, vacuum 328.6 seconds", "SRC-WIKI-S598M", "T"), ("326 s", None, "X")],
  "UNRESOLVED", None, "The second value has no source. " + _PRIMARY)
K("CF-R2_SC_COMM-R2-11", "ENG-RU-S5-98M", "performance.isp_vac",
  [("Specific impulse, vacuum 328.6 seconds", "SRC-WIKI-S598M", "T"), ("328.1 s", None, "X"), ("~326 s (Briz-KM)", None, "X")],
  "UNRESOLVED", None, "Only the encyclopedia value has a source. " + _PRIMARY)
K("CF-R2_USSR-R2-19", "ENG-SU-11D58M", "performance.thrust_vac / isp_vac",
  [("Thrust, vacuum 79.46 kN; 353 s (infobox)", "SRC-WIKI-RD58", "T"), ("Thrust (Vac) 83.4 kN (variant table)", "SRC-WIKI-RD58", "T"),
   ("83.40 kN, 349 s, 78 bar", "SRC-ASTRONAUTIX-RD58", "N")],
  "UNRESOLVED", "different_variant",
  "One article: an infobox value and a variant table whose columns are separate RD-58 versions. Which column is the "
  "11D58M is not settled; the Astronautica mirror was unreachable.")
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
  [("Second stage Powered by 1 MT-B ... LOX / RP-1", "SRC-WIKI-TRONADOR", "T"), ("MMH / N2O4 pressurised", "SRC-WIKI-TRONADOR", "NF")],
  "UNRESOLVED", "different_epoch",
  "The current revision gives LOX / RP-1 for the MT-B; the MMH / N2O4 wording is not in it (earlier designs). " + _PRIMARY)
K("CF-R2_ASIA-R2A-27", "ENG-AR-VEX-1A-ENGINE", "history.test_date",
  [("26 Feb 2014", "SRC-WIKI-TRONADOR", "NF"), ("In March 2014, a suborbital prototype named VEx-1A failed", "SRC-WIKI-TRONADOR", "T")],
  "UNRESOLVED", None, "The current revision gives March 2014 only. " + _PRIMARY)
K("CF-R2_ASIA-R2A-29", "ENG-CN-WELKIN-VAC", "performance.thrust_vac",
  [("600 kN", "SRC-ORBITCODEX-PALLAS", "N"), ("Thrust, vacuum 500 kilonewtons", "SRC-WIKI-WELKIN", "T")],
  "UNRESOLVED", "different_variant",
  "The 500 kN is the Welkin's vacuum thrust on the encyclopedia page, not a separate vacuum engine; the 600 kN page "
  "refused access. " + _PRIMARY)
K("CF-R2_ASIA-R2A-31", "ENG-ES-TEPREL-C-VAC", "performance.thrust_vac",
  [("50 kN", "SRC-WIKI-TEPREL", "NF"), ("Thrust, vacuum 75 kN (17,000 lbf)", "SRC-WIKI-TEPREL", "T"), ("75 kN", "SRC-SATNOW-TEPRELC", "N")],
  "EXPLAINED", "different_epoch",
  "The current revision prints 75 kN in vacuum, the SatNow figure DB-0 cited; the 50 kN was an earlier revision.")
K("CF-R2_ASIA-R2A-32", "ENG-FR-SEPR-841", "propellants.fuel",
  [("nitric acid oxidiser and TX2 (tri-ethylamine xylidine) fuel", "SRC-WIKI-SEPR84", "T"),
   ("the TX2 fuel of the SEPR 841 was replaced with ... kerosene in the SEPR 844", "SRC-WIKI-SEPR84", "T")],
  "EXPLAINED", "different_variant", "The article gives TX2 for the SEPR 841 and kerosene for the later SEPR 844.")
K("CF-R2_ASIA-R2A-33", "ENG-DE-OTRAG-CRPU-ENGINE", "propellants.oxidizer",
  [("N2O4 (stage infobox)", "SRC-WIKI-OTRAG", "T"), ("nitric acid", None, "X")],
  "UNRESOLVED", None, "The article's infobox says N2O4; the nitric acid claim has no source. " + _PRIMARY)
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
  [("LEROS 4-ET MMH / MON 1310 N", "SRC-WIKI-LEROS", "T"), ("The engine uses MON and hydrazine", "SRC-WIKI-BLUEGHOST", "T")],
  "UNRESOLVED", None, "Two encyclopedia articles disagree (MMH against hydrazine); no Nammo document opened.")
K("CF-R2_SC_COMM-R2-14", "ENG-US-ARROWAY", "cycle",
  [("fuel-rich staged combustion", None, "X"), ("ox-rich staged combustion", None, "X")],
  "UNRESOLVED", None, "Neither claim has a source. " + _PRIMARY)
K("CF-R2_SC_COMM-R2-15", "ENG-US-E-2", "performance.isp_vac",
  [("326 s ('Launcher says')", "SRC-CONTROL-E2-TEST", "N"), ("365 s", None, "X")],
  "UNRESOLVED", None, "The trade page refused access (HTTP 403); 365 s has no source.")
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
  [("315.5 s at 300:1; 311 s at 164:1", "SRC-L3H-LHX-SPECSHEET-2024", "N"), ("specific_impulse_vacuum 312 s", "SRC-WIKI-R4D", "T")],
  "UNRESOLVED", "different_configuration",
  "The specification sheet returns 404; the encyclopedia gives one family value without an area ratio. " + _PRIMARY)
K("CF-US_HIST-04", "ENG-US-RS-68", "performance.thrust_sl / performance.pc",
  [("663,000 pounds-force (2,950 kN) at sea level (prose)", "SRC-WIKI-RS68", "T"), ("RS-68: 2,950 kN (660,000 lbf) (infobox)", "SRC-WIKI-RS68", "T"),
   ("RS-68A Pc 1,580 psia", "SRC-L3H-RS68A-DS", "N")],
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
  [("RFNA + furfuryl alcohol", "SRC-WIKI-WACCORPORAL", "T"), ("aniline (+RFNA)", "SRC-CALTECH-THESIS310", "N")],
  "UNRESOLVED", "different_epoch", "The Caltech thesis page was unreachable on retry. " + _PRIMARY)
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
  [("550,000 lbf (development period)", "SRC-BLUE-ULA-PARTNERSHIP", "N"), ("640,000 lbf (2,846 kN)", "SRC-BLUE-ENGINES", "N")],
  "UNRESOLVED", "different_configuration",
  "Both Blue Origin pages returned HTTP 429 (rate limit). ULA's fact sheet gives 550,000 lbf for Vulcan "
  "(CF-DB05-W-R2_SCHEM-R2-5).")
K("CF-ANCHOR_US_MODERN-1", "ENG-US-BE-4", "performance.thrust_sl",
  [("640,000 lbf (2,846 kN)", "SRC-BLUE-ENGINES-PAGE", "N"), ("550,000 lbf", "SRC-BLUE-PRESS-BE4-EARLY", "N")],
  "UNRESOLVED", "different_epoch", "No URLs registered for these two Blue Origin pages. " + _PRIMARY)
K("CF-COMMERCIAL-COM-10", "ENG-US-BE-3U", "performance.thrust_vac",
  [("160,000 / 173,000 lbf", "SRC-BLUE-NEWS-BE3U-MISC", "N"), ("320,000 -> 400,000 lbf for two engines", "SRC-BLUE-NG-UPGRADE", "N"),
   ("200,000 lbf", "SRC-BLUE-ENGINES", "N")],
  "UNRESOLVED", "different_epoch", "All Blue Origin pages returned HTTP 429. " + _PRIMARY)
K("CF-ANCHOR_US_MODERN-2", "ENG-US-BE-3U", "performance.thrust_vac",
  [("200,000 lbf", "SRC-BLUE-ENGINES-PAGE", "N"), ("173,000 / 160,000 lbf; stage 320,000 -> 400,000 lbf", "SRC-BLUE-PRESS-BE3U-UPDATES", "N")],
  "UNRESOLVED", "different_epoch", "No URLs registered. " + _PRIMARY)
K("CF-TAXONOMY-TAX-1", "ENG-US-BE-3U", "cycle",
  [("open expander", "SRC-WIKI-BE3U", "NF"), ("Cycle Expander bleed", "SRC-WIKI-BE3U", "T")],
  "EXPLAINED", "different_epoch", "The current revision says expander bleed; 'open expander' was an earlier wording.")
K("CF-ANCHOR_US_MODERN-3", "ENG-US-BE-3U", "cycle",
  [("open expander", "SRC-BLUE-ENGINES-PAGE", "N"), ("Cycle Expander bleed", "SRC-WIKI-BE3", "T")],
  "UNRESOLVED", "definition",
  "The encyclopedia now says expander bleed; the maker's page (no URL registered) was not opened. 'Open expander' and "
  "'expander bleed' name the same cycle family.")
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
   ("The EPS stage ... is propelled by the Aestus engine (thrust = 27.5 kN) (October 1994)", "SRC-DB05-ESA-PR-1994-35-EPS", "PR94")],
  "UNRESOLVED", "different_epoch",
  "ESA's EPS page, opened 2026-10-29 via www.esa.int, prints 2.7 tonnes vacuum thrust and more than 1000 s on a GTO "
  "mission. CNES's Ariane 5 page prints 29 kN (2.9 t) in vacuum, which could be 29.6 kN "
  "rounded but is stated as a round figure. ESA's October 1994 release, from the development test campaign, gives "
  "27.5 kN, close to ESA's 2.7 t (26.5 kN). Thrust appears to have risen between the 1994 "
  "development engine and the flown engine (the encyclopedia ties a mixture-ratio change to flight 518), but no "
  "document records the change. No Astrium/Airbus datasheet was reached.")
K("CF-EUROPE-11", "ENG-DE-AESTUS", "performance.pc",
  [("chamber_pressure 11 bar", "SRC-WIKI-AESTUS", "T"), ("10.0 bar", "SRC-MECAIND-2020-T1", "N")],
  "UNRESOLVED", None, "The journal table refused access (HTTP 403). " + _PRIMARY)
K("CF-EUROPE-12", "ENG-DE-AESTUS", "propellants.mixture_ratio",
  [("mixture_ratio 1.9", "SRC-WIKI-AESTUS", "T"), ("2.05", "SRC-MECAIND-2020-T1", "N"),
   ("adjusting propellant mixture ratio from 2.05 to 1.90 with a first flight on an Ariane 5 flight 518 on 26 February 2004",
    "SRC-WIKI-AESTUS", "T")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "The encyclopedia's own history section says the mixture ratio was changed from 2.05 to 1.90 in the 1999-2002 "
  "improvements, first flown on flight 518 (2004): two epochs, not two readings of one value. The journal table "
  "refused access (HTTP 403), and no Airbus or ESA document was opened to confirm the change.")
K("CF-EUROPE-23", "ENG-DE-BMW-109-558", "performance.thrust",
  [("3.7 kN for 33 s, followed by 0.588 kN for 24 s", "SRC-WIKI-BMW109558", "T"), ("375 kg falling to 60 kg", "SRC-NASM-BMW109558", "N")],
  "EXPLAINED", "unit",
  "375 kgf is 3.68 kN and 60 kgf 0.588 kN DERIVED: the two describe the same two-level thrust in different units.")
K("CF-EUROPE-24", "ENG-DE-HWK-109-507", "performance.thrust",
  [("590 kgf for 10 s", "SRC-WIKI-HWK109507", "NF"), ("600 -> 400 kg over 10 s", "SRC-NASM-HWK109507", "N")],
  "UNRESOLVED", None,
  "The current revision says the burn lasted about 10 s but prints no thrust; the Smithsonian record refused access. "
  + _PRIMARY)
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
  [("~4.53 kg", "SRC-L3H-BIPROP-2023", "N"), ("~6.58 kg", "SRC-L3H-BIPROP-2024", "N")],
  "UNRESOLVED", "different_epoch", "Both L3Harris datasheet URLs return 404 now. " + _PRIMARY)
K("CF-SPACECRAFT-6", "ENG-US-R-40B", "mechanical.mass",
  [("~10.5 kg", "SRC-L3H-BIPROP-2023", "N"), ("~15.9 kg", "SRC-L3H-BIPROP-2024", "N")],
  "UNRESOLVED", "different_epoch", "Both L3Harris datasheet URLs return 404 now. " + _PRIMARY)
K("CF-SPACECRAFT-7", "ENG-US-MR-103J", "performance.thrust_range",
  [("upper 1.13 N", "SRC-L3H-MONO-2023", "N"), ("upper 1.19 N", "SRC-L3H-MONO-2025", "N")],
  "UNRESOLVED", "different_epoch", "Both L3Harris datasheet URLs return 404 now. " + _PRIMARY)
K("CF-SPACECRAFT-8", "ENG-US-MR-111G", "performance.thrust_range",
  [("1.8-4.9 N", "SRC-L3H-MONO-2023", "N"), ("0.9-5.7 N", "SRC-L3H-MONO-2025", "N")],
  "UNRESOLVED", "different_epoch", "Both L3Harris datasheet URLs return 404 now. " + _PRIMARY)
K("CF-TAXONOMY-TAX-6", "ENG-US-DELPHIN", "performance.thrust_sl",
  [("6,300 lbf", "SRC-ASTRA-R31-PRESSKIT", "N"), ("6,500 lbf", "SRC-ASTRA-R31-PRESSKIT", "N"),
   ("Powered by 5 Delphin, Maximum thrust c. 32,500 lbf (145 kN)", "SRC-WIKI-ASTRA-ROCKET", "T")],
  "UNRESOLVED", "rating_or_rounding",
  "The article gives 32,500 lbf for five engines (6,500 lbf each DERIVED); the press kit returns 404, so its 6,300 "
  "against 6,500 lbf cannot be checked.")

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
