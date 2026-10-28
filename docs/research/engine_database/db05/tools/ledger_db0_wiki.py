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
        "X": "no source id (DB-0 search summary or brief)"}


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
  [("85:1", "SRC-AIAA-VEHGUIDE-ATLAS", "N"), ("nozzle_ratio '84:1 or 280:1'", "SRC-WIKI-RL10", "T")],
  "UNRESOLVED", "different_variant",
  "The encyclopedia gives '84:1 or 280:1' for the family, not an RL10A-4-2 row; the AIAA page returns 404. " + _PRIMARY)
K("CF-R2_US_CLASSIC-B2-4", "ENG-US-RL10B-2", "mechanical.mass / control.gimbal_actuation",
  [("dry_weight 301 kg; electro-mechanical", "SRC-WIKI-RL10", "T"), ("277 kg (older revision)", "SRC-WIKI-RL10", "NF"),
   ("hydraulic nozzle gimbal (stage)", "SRC-AIAA-VEHGUIDE-DELTA", "N")],
  "UNRESOLVED", "definition_or_epoch",
  "The current revision prints 301 kg; 277 kg was an older revision. The gimbal actuator wording is about the stage on one "
  "side and the engine on the other. " + _PRIMARY)
K("CF-R2_ASIA-R2A-2", "ENG-JP-LE-7A", "performance.pc",
  [("121 bar (1750 psi)", "SRC-AIAA-VG-H2A", "N"), ("Combustion chamber pressure: 12.0 MPa (1,740 psi)", "SRC-WIKI-LE7", "T")],
  "UNRESOLVED", "rating_or_rounding",
  "12.0 MPa is 120 bar, 0.8 percent below 121 bar; the AIAA page returns 404. No station is named. " + _PRIMARY)
K("CF-ASIA_OTHER-1", "ENG-JP-LE-7A", "performance.pc",
  [("121 bar (1750 psi)", "SRC-AIAA-VG-H2A", "N"), ("Combustion chamber pressure: 12.0 MPa (1,740 psi)", "SRC-WIKI-LE7", "T")],
  "UNRESOLVED", "rating_or_rounding", "Same pair as CF-DB05-E-R2_ASIA-R2A-2.")
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
  "10.2 MPa and 430 s are not in the current revision. " + _PRIMARY)
K("CF-R2_SCHEM-R2-1", "ENG-US-RS-68A", "performance.pc",
  [("1580 psia", "SRC-L3H-RS68A-DS", "N"), ("Chamber pressure 1,488 psi (10.26 MPa)", "SRC-WIKI-RS68", "T")],
  "UNRESOLVED", "different_variant",
  "The encyclopedia gives one chamber pressure for RS-68 and RS-68A together; the manufacturer's datasheet URL returns "
  "404. " + _PRIMARY)
K("CF-R2_SCHEM-R2-2", "ENG-US-RS-68A", "performance.isp_vac",
  [("411 s", "SRC-L3H-RS68A-DS", "N"), ("RS-68A: 411.9 s", "SRC-WIKI-RS68", "T")],
  "UNRESOLVED", "rating_or_rounding", "0.2 percent apart; the datasheet returns 404. " + _PRIMARY)
K("CF-R2_SCHEM-R2-12", "ENG-SU-RD-170", "turbines.main.power",
  [("~200 MW", None, "X"), ("189.3 MW", None, "X")],
  "UNRESOLVED", None, "Neither claim carries a source id. " + _PRIMARY)
NOT_FILED["CF-US_HIST-25"] = ("one claim only, a figure cut off as '188,00' on a page that now returns 404; not a "
                              "conflict, and filing it would withhold the promoted primary H-1 188K thrust")
K("CF-EUROPE-3", "ENG-FR-VULCAIN-2", "performance.thrust_vac",
  [("'2': 1359 kN", "SRC-WIKI-VULCAIN", "T"), ("1340 kN (comparison table)", "SRC-WIKI-VULCAIN", "NF")],
  "UNRESOLVED", "intra_document",
  "The current revision prints 1,359 kN for Vulcain 2 (and 1,324 kN for 2.1); 1,340 kN is no longer in it. " + _PRIMARY)
K("CF-EUROPE-4", "ENG-FR-VULCAIN-2", "performance.pc",
  [("'2': 117.3 bar", "SRC-WIKI-VULCAIN", "T"), ("115 bar", "SRC-MECAIND-2020-T1", "N")],
  "UNRESOLVED", "rating_or_rounding", "The journal table refused access (HTTP 403). " + _PRIMARY)
K("CF-ANCHOR_EU_ASIA-2", "ENG-FR-VULCAIN-2", "performance.pc",
  [("'2': 117.3 bar", "SRC-WIKI-VULCAIN", "T"), ("115 bar", "SRC-MECAIND-2020-T1", "N"), ("115 bar", "SRC-CLASSICISTRANIERI-VULCAIN", "N")],
  "UNRESOLVED", "different_epoch",
  "The 115 bar is in a journal table (403) and an old encyclopedia mirror (403); the current article prints 117.3 bar. "
  + _PRIMARY)
K("CF-ANCHOR_EU_ASIA-3", "ENG-FR-VULCAIN-2", "nozzle.area_ratio",
  [("'2': 58.2:1", "SRC-WIKI-VULCAIN", "T"), ("58.5", "SRC-MECAIND-2020-T1", "N")],
  "UNRESOLVED", "rating_or_rounding",
  "The current revision prints 58.2:1 (the 60:1 table DB-0 saw is gone); the journal table refused access. " + _PRIMARY)

# --- USSR / Russia
K("CF-R2_USSR-R2-6", "ENG-SU-RD-0120", "performance.pc",
  [("210 kgf/cm2 = 20.6 MPa at 100 %", "SRC-JAXA-61856043", "N"), ("chamber_pressure 21.9 MPa", "SRC-WIKI-RD0120", "T")],
  "UNRESOLVED", "different_operating_point",
  "The encyclopedia's infobox quotes 106 % thrust next to its figures; 21.9 / 20.6 is 1.063, consistent with 106 % "
  "against 100 %, but the JAXA paper returned 503 and nothing opened states it.")
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
   ("850 kN (older infobox)", "SRC-WIKI-VIKAS", "NF"), ("799 kN PSLV / 846 kN GSLV HT", "SRC-VAJIRAM-VIKAS", "N")],
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
  [("The basic engine has a mass of 910 lb", "SRC-WIKI-XLR99", "T"), ("915 lb", "SRC-NMUSAF-XLR99", "N")],
  "UNRESOLVED", "rating_or_rounding", "The museum fact sheet refused access (HTTP 403). " + _PRIMARY)
K("CF-US_HIST-12", "ENG-US-S-3D", "performance.thrust",
  [("134,908 pounds of thrust (600.1 kN) at sea level", "SRC-WIKI-S3D", "T"), ("engine_power 150,000 lbf (Jupiter)", "SRC-WIKI-PGM19", "T"),
   ("150,000-205,000 lb depending on model", "SRC-NMUSAF-LR79", "N")],
  "UNRESOLVED", "different_variant",
  "Two articles: the S-3D at 134,908 lbf and the Jupiter missile's engine at 150,000 lbf; the museum's range (403) "
  "suggests several models. " + _PRIMARY)
K("CF-US_HIST-14", "ENG-US-38ALDW-1500", "propellants.fuel",
  [("RFNA + furfuryl alcohol", "SRC-WIKI-WACCORPORAL", "T"), ("aniline (+RFNA)", "SRC-CALTECH-THESIS310", "N")],
  "UNRESOLVED", "different_epoch", "The Caltech thesis page was unreachable on retry. " + _PRIMARY)
K("CF-US_HIST-16", "ENG-US-RS-56-OSA", "performance.thrust",
  [("RS-56-OSA: 60,500 lbf (269.0 kN) sea level", "SRC-WIKI-RS56", "T"), ("1 x RS-56-OSA Maximum thrust 386 kN (87,000 lbf)", "SRC-WIKI-ATLASII", "T")],
  "UNRESOLVED", "different_operating_point",
  "Two articles: a sea-level engine figure and a stage 'maximum' (likely vacuum) figure. Neither names the condition "
  "fully. " + _PRIMARY)
K("CF-US_HIST-20", "ENG-US-TR-201", "history.period",
  [("Date 1972-1988 (infobox)", "SRC-WIKI-TR201", "T"), ("77 during its Delta career between 1974 and 1988", "SRC-WIKI-TR201", "T")],
  "EXPLAINED", "definition", "Development-to-retirement span against flight span, in one article.")
K("CF-US_HIST-23", "ENG-US-M-1", "history.cancellation",
  [("Development abandoned at pre-prototype stage", "SRC-WIKI-M1", "T")],
  "UNRESOLVED", None, "The article states abandonment but DB-0's conflict was about the date, which it does not settle.")
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
  [("thrust(Vac) 29.6 kN", "SRC-WIKI-AESTUS", "T"), ("2.7 t (~26.5 kN)", "SRC-ESA-EPS", "N")],
  "UNRESOLVED", None, "The ESA page was unreachable on retry. " + _PRIMARY)
K("CF-EUROPE-11", "ENG-DE-AESTUS", "performance.pc",
  [("chamber_pressure 11 bar", "SRC-WIKI-AESTUS", "T"), ("10.0 bar", "SRC-MECAIND-2020-T1", "N")],
  "UNRESOLVED", None, "The journal table refused access (HTTP 403). " + _PRIMARY)
K("CF-EUROPE-12", "ENG-DE-AESTUS", "propellants.mixture_ratio",
  [("mixture_ratio 1.9", "SRC-WIKI-AESTUS", "T"), ("2.05", "SRC-MECAIND-2020-T1", "N")],
  "UNRESOLVED", None, "The journal table refused access (HTTP 403). " + _PRIMARY)
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
