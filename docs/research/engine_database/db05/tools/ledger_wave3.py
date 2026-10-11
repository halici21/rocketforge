"""DB-2B Wave 3 targeted source verification (2026-10-11): Japan (LE-7, LE-7A, LE-9), Europe (Vulcain,
Vulcain 2, Vinci), China (YF-75, YF-75D, YF-100, and target 7: YF-77).

Only documents opened in this pass. Japanese and Chinese statements are recorded as printed, in the
original language; the English gloss in each note is RocketForge's reading aid, not a translation source
and not corroboration. Scanned pages whose extracted text was garbled were read from rendered page images
(noted per record). Values are recorded whatever the document's rights; whether anything ships is decided by
the production manifest, not here.
"""
from ledger import A, D, S, C, BLOCK

LE7, LE7A, LE9 = "ENG-JP-LE-7", "ENG-JP-LE-7A", "ENG-JP-LE-9"
VUL, VUL2, VINCI = "ENG-FR-VULCAIN", "ENG-FR-VULCAIN-2", "ENG-FR-VINCI"
YF75, YF75D, YF100, YF77 = "ENG-CN-YF-75", "ENG-CN-YF-75D", "ENG-CN-YF-100", "ENG-CN-YF-77"
_NO_NOTICE = "no copyright notice on pages read (extracted text of every page checked 2026-10-11)"
_GLOSS = "RocketForge reading gloss, not a translation source"

# ------------------------------------------------------------------ documents opened in this pass
MERKLE = "SRC-DB05-NTRS-19910018905"
D(MERKLE, identifier="NTRS 19910018905 (conference paper; C. L. Merkle, Pennsylvania State Univ.; Space Transportation Propulsion "
          "Technology Symposium, Penn State, 25-29 June 1990, Vol. 2 pp.527-550)",
  title="A review of liquid rocket propulsion programs in Japan", tier="B",
  rights_checked=f"NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; {_NO_NOTICE}", rights_class="VALUES_WITH_ATTRIBUTION",
  note="A US panel's 1990 review of Japanese programmes, from the open literature and laboratory visits (p.1). Secondary for any "
       "Japanese engine fact: the panel did not build or test the engines. No flow schematic in the paper (contact sheet viewed).")
RICE = "SRC-NTRS-19910018907"
D(RICE, identifier="NTRS 19910018907 (briefing; E. E. Rice, Orbital Technologies Corp.; same symposium, June 1990, pp.583-606)",
  title="Overview of European and other non-US/USSR/Japan launch vehicle and propulsion technology programs", tier="B",
  rights_checked=f"NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; {_NO_NOTICE}", rights_class="VALUES_WITH_ATTRIBUTION",
  note="A US contractor's 1990 overview. Secondary for European and Chinese engine facts. Its China pages describe Long March "
       "vehicles only (no YF engine designation). No flow schematic (contact sheet viewed).")
MEXT = "SRC-MEXT-SAC-1997"
D(MEXT, identifier="宇宙開発委員会 第12回 資料 委12-6 (NASDA 宇宙開発事業団, 平成9年4月9日 = 9 April 1997), hosted by MEXT (mext.go.jp)",
  title="LE－7Aエンジン燃焼試験について", tier="A",
  rights_checked="No notice printed in the 9 pages. Host: MEXT website terms of use (文部科学省ウェブサイト利用規約, read 2026-10-11): "
                 "content usable under CC BY 4.0-compatible terms, numeric data and simple tables declared not subject to copyright; "
                 "but content whose rights belong to a third party (anyone other than the State) is excluded and must be cleared by the "
                 "user. This is NASDA's paper, and NASDA was not the State.",
  rights_class="RIGHTS_REVIEW_REQUIRED",
  note="Primary (the agency developing both engines). A scanned document: extracted text is OCR, garbled on p.3-9; every value below "
       "was read from the rendered page image (p.6, p.7 at 170-200 dpi). Translation title gloss: 'On the LE-7A engine firing tests'.")
JAXA17 = "SRC-JAXA-PRESS-LE9-2017"
D(JAXA17, identifier="資料37-3, 科学技術・学術審議会 研究計画・評価分科会 宇宙開発利用部会 (第37回), JAXA, 2017-09-05; hosted by jaxa.jp",
  title="H3ロケット1段エンジン（LE-9）実機型#1-1 燃焼試験の実施結果について", tier="A",
  rights_checked="No notice printed in the 18 pages. Host: JAXA Terms of Use (global.jaxa.jp/policy.html, read 2026-10-11): materials "
                 "and copyrights are JAXA's; use without permission only for press, scientific research, education or private use.",
  rights_class="RESTRICTED_REFERENCE", figures_rights="RESTRICTED_REFERENCE",
  note="Primary (the agency). Its LE-9 column is the engine at basic-design completion (基本設計を完了, p.3) during prototype "
       "(実機型) engine testing; the LE-7A column is a reference for the flying engine in 2017. Gloss of title: 'Results of the "
       "firing tests of the H3 first-stage engine (LE-9) prototype #1-1'.")
IHI = "SRC-JAXA-AA1740298002"
D(IHI, identifier="IHI技報 Vol.57 No.3 (2017) pp.58-64 (Mizuno, Oguchi, Niiyama, Shimiya; IHI Corporation); AIREX AA1740298002",
  title="H3ロケット1段エンジンLE-9ターボポンプの開発 (Development of Turbopump for LE-9 Engine)", tier="A",
  rights_checked="No notice in the extracted text; footer 'This document is provided by JAXA'. Host: AIREX (JAXA repository) states "
                 "'このリポジトリに保管されているアイテムは、他に指定されている場合を除き、著作権により保護されています' (items are protected "
                 "by copyright unless otherwise indicated); none is indicated. An IHI corporate journal.",
  rights_class="RESTRICTED_REFERENCE", figures_rights="RESTRICTED_REFERENCE",
  note="The turbopump maker's paper. Body text uses an embedded font whose extracted text is mojibake; statements below were read "
       "from the rendered page (p.2).")
D("SRC-IHI-GIHO-LE9-TP", identifier="AIREX record page for AA1740298002", title="AIREX: H3ロケット1段エンジンLE-9ターボポンプの開発", tier="A",
  rights_checked="AIREX: items protected by copyright unless otherwise indicated", rights_class="RESTRICTED_REFERENCE",
  note="Record page only (bibliographic data, abstract); the paper itself is SRC-JAXA-AA1740298002.")
MHI7A, MHI9 = "SRC-MHI-LE7A", "SRC-MHI-LE9"
D(MHI7A, identifier="mhi.com product page 'H-IIA/B First Stage Engine LE-7A' (undated; as retrieved 2026-10-11)",
  title="H-IIA/B First Stage Engine LE-7A | Mitsubishi Heavy Industries", tier="A",
  rights_checked="'© MITSUBISHI HEAVY INDUSTRIES, LTD.' in the page footer", rights_class="RESTRICTED_REFERENCE",
  figures_rights="RESTRICTED_REFERENCE", note="Manufacturer. Undated page: its values are as of retrieval.")
D(MHI9, identifier="mhi.com product page 'H3 First Stage Engine LE-9' (undated; as retrieved 2026-10-11)",
  title="H3 First Stage Engine LE-9 | Mitsubishi Heavy Industries", tier="A",
  rights_checked="'© MITSUBISHI HEAVY INDUSTRIES, LTD.' in the page footer", rights_class="RESTRICTED_REFERENCE",
  figures_rights="RESTRICTED_REFERENCE", note="Manufacturer. Undated page ('was developed'): its values are as of retrieval.")
D("SRC-MHI-TR55-2", identifier="MHI Technical Review Vol.55 No.2 (2018) abstract page", title="Development of Technologies for Prediction and "
  "Countermeasures for Combustion Stability for LE-9 Engine Booster Stage of H3 Launch Vehicle", tier="A",
  rights_checked="'© MITSUBISHI HEAVY INDUSTRIES, LTD.' in the page footer", rights_class="RESTRICTED_REFERENCE",
  note="Abstract page opened; identity only (combustion-stability work during LE-9 development). Paper PDF not mined.")
D("SRC-JAXA-H2", identifier="global.jaxa.jp H-II Launch Vehicle project page", title="JAXA | H-II Launch Vehicle", tier="A",
  rights_checked="'© 2003 Japan Aerospace Exploration Agency' in the footer; JAXA Terms of Use", rights_class="RESTRICTED_REFERENCE")
D("SRC-JAXAREPO-45156", identifier="JAXA repository (jaxa.repo.nii.ac.jp) record 45156", title="(NAL/NASDA report on LE-7 thrust-chamber "
  "fabrication methods; title as shown in the record)", tier="A",
  rights_checked="JAXA repository record page; 'Copyright' meta; JAXA Terms of Use", rights_class="RESTRICTED_REFERENCE",
  note="Identity only: a structural comparison of four LE-7 thrust-chamber fabrication methods 'designed according to the LE-7 "
       "engine specifications'. No engine value mined.")
BLOCK("SRC-JAXAREPO-44968", "the record page (HTTP 200) rendered only the repository shell without scripts: no content read",
      "JAXA repository record 44968 (preburner evaluation method, per DB-0): the attempt is on record, nothing is evidence.")
IAC17LE9, IAC16LE9 = "SRC-IAC-LE9-2017", "SRC-IAC-LE9-2016"
_IAF = "'© IAF 2006-2026 all rights reserved' in the IAF archive page footer"
D(IAC17LE9, identifier="IAC-17,C4,1,4,x36601 (Kawashima et al., JAXA), IAF archive abstract page",
  title="Design and Development Status of LE-9 Engine for H3 Launch Vehicle", tier="B", rights_checked=_IAF,
  rights_class="RESTRICTED_REFERENCE", note="Author abstract only; the paper was not available.")
D(IAC16LE9, identifier="IAC-16,C4,1,2,x35064 (JAXA), IAF archive abstract page", title="Overview of LE-9 Engine Development for H3 Launch "
  "Vehicle", tier="B", rights_checked=_IAF, rights_class="RESTRICTED_REFERENCE", note="Author abstract only; identity and heritage, no value.")

ESAVUL, ESAV2, ESAVI05, ESAA6 = "SRC-ESA-VULCAIN", "SRC-ESA-V2-TEST", "SRC-ESA-VINCI-60S", "SRC-ESA-A6ENGINES"
_ESA = ("ESA website Terms and conditions (read 2026-10-11): contents 'intended for the personal and non-commercial use of its "
        "users'; ESA 'does not grant the right to resell or redistribute any information, images or material'")
D(ESAVUL, identifier="esa.int 'Vulcain engine' (Ariane; undated, written after 2005)", title="Vulcain engine", tier="A",
  rights_checked=_ESA, rights_class="RESTRICTED_REFERENCE", figures_rights="RESTRICTED_REFERENCE",
  note="Agency retrospective covering both Vulcain and Vulcain 2.")
D("SRC-ESA-ESAMI-VULCAIN", identifier="esa.int esaMI 'Vulcain engine' (redirects to the same page as SRC-ESA-VULCAIN, same bytes)",
  title="Vulcain engine", tier="A", rights_checked=_ESA, rights_class="RESTRICTED_REFERENCE",
  note="Same document as SRC-ESA-VULCAIN (identical download); not counted twice.")
D(ESAV2, identifier="esa.int news, 14 May 2004", title="Successful test for Vulcain 2 engine", tier="A", rights_checked=_ESA,
  rights_class="RESTRICTED_REFERENCE")
D(ESAVI05, identifier="esa.int news, 27 July 2005", title="Thumbs up for 60-second firing", tier="A", rights_checked=_ESA,
  rights_class="RESTRICTED_REFERENCE", note="Vinci during development (Ariane-5 Plus programme).")
D(ESAA6, identifier="esa.int, 5 June 2024", title="The engines of Ariane 6", tier="A", rights_checked=_ESA, rights_class="RESTRICTED_REFERENCE")
D("SRC-ESA-VINCI-HOTFIRE", identifier="esa.int news (ETID demonstrator)", title="First hot firing of next generation rocket engine", tier="A",
  rights_checked=_ESA, rights_class="RESTRICTED_REFERENCE", note="About the ETID demonstrator; mentions Vinci only by relevance. Not mined.")
D("SRC-CNES-A5-TECH", identifier="cnes.fr 'Ariane 5' (modifié le 23 juin 2025)", title="Ariane 5 | CNES", tier="A",
  rights_checked="'©' credits on the page (e.g. '© CNES/ESA/Arianespace/...'); CNES legal-notice page returned 404", rights_class="RESTRICTED_REFERENCE",
  note="Opened (French); a vehicle history page, no Vulcain engine value mined.")
IAC21VI, IAC15VI, IAC18VI = "SRC-IAC-21-65631", "SRC-IAC-15-28800", "SRC-IAC-18-45921"
D(IAC21VI, identifier="IAC-21,C4,1,5,x65631 (Danous et al., ArianeGroup), abstract PDF on p.iafastro.directory",
  title="ARIANE 6 UPPER LIQUID PROPULSIVE MODULE QUALIFICATION", tier="B", rights_checked=f"no notice in the 1-page abstract PDF; host {_IAF}",
  rights_class="RESTRICTED_REFERENCE", note="Manufacturer authors; abstract only.")
D(IAC15VI, identifier="IAC-15,C4,1,6,x28800 (Snecma, CNES authors), IAF archive abstract page", title="VINCI, the European reference for "
  "Ariane 6 upper stage cryogenic engine", tier="B", rights_checked=_IAF, rights_class="RESTRICTED_REFERENCE")
D(IAC18VI, identifier="IAC-18,C4,1,4,x45921 (Haeseler, ArianeGroup), IAF archive abstract page", title="Vinci Upper Stage Engine Development, "
  "Test, Qualification, and Industrialization", tier="B", rights_checked=_IAF, rights_class="RESTRICTED_REFERENCE")
D("SRC-DLR-VINCI-NOZZLE-2010", identifier="dlr.de news 2010-11-12 (download is a 4-page PDF image of the news item)",
  title="Europe's new upper stage engine reaches an important milestone", tier="A",
  rights_checked="DLR site imprint (not reviewed for reuse); not mined", rights_class="RIGHTS_REVIEW_REQUIRED",
  note="Opened; image-only PDF, not mined in this pass.")
D("SRC-PATENT-US6996973", identifier="US Patent 6,996,973 (USPTO full-text PDF, 6 pages)", title="Method of achieving jet separation of an "
  "un-separated flow in a diverging nozzle", tier="A", rights_checked="USPTO document; host statement not reviewed in this pass",
  rights_class="RIGHTS_REVIEW_REQUIRED", note="Opened; a nozzle-flow method, no Vulcain 2 engine value identified. Not mined.")

BAPI13, BAPI77, XAPI15, XAPI17 = "SRC-IAC13-18525", "SRC-IAC13-17679", "SRC-IAC15-LOXKERO-REVIEW", "SRC-IAC17-41028"
D(BAPI13, identifier="IAC-13,C4,1,1,x18525 (Nan Zhang, Beijing Aerospace Propulsion Institute), IAF archive abstract page",
  title="The Development of LOX/LH2 Engine in China", tier="B", rights_checked=_IAF, rights_class="RESTRICTED_REFERENCE",
  note="The developing institute's author abstract (English as printed).")
D(BAPI77, identifier="IAC-13,C4,1,2,x17679 (Weibin Wang, Dayong Zheng, Guiyu Qiao; BAPI), IAF archive abstract page",
  title="Development Status of the Cryogenic Oxygen/Hydrogen YF-77 Engine for Long-March 5", tier="B", rights_checked=_IAF,
  rights_class="RESTRICTED_REFERENCE", note="Target 7 (see DB2B_WAVE3 design note). Author abstract (English as printed, typos kept).")
D(XAPI15, identifier="IAC-15,C4,1,13,x28419 (Chen Jianhua et al., Xi'an Aerospace Propulsion Institute), IAF archive abstract page",
  title="a review of china's lox/kerosene stage combustion cycle rocket engine", tier="B", rights_checked=_IAF, rights_class="RESTRICTED_REFERENCE")
D(XAPI17, identifier="IAC-17,C4,5,13,x41028 (Xi'an Aerospace Propulsion Institute), IAF archive abstract page",
  title="Sensitivity analysis of static parameters for the LOX/kerosene rocket engine (post-pump swing configuration)", tier="B",
  rights_checked=_IAF, rights_class="RESTRICTED_REFERENCE")
D("SRC-IAC16-YF115", identifier="IAC-16,C4,1,10,x32585 (Xi'an Aerospace Propulsion Institute), IAF archive abstract page",
  title="static characteristic analysis of 180kn lox/kerosene upper stage engine", tier="B", rights_checked=_IAF,
  rights_class="RESTRICTED_REFERENCE", note="Considered for target 7 (YF-115); not selected. Identity only.")
JDSE = "SRC-DB05-JDSE-2021-YF100"
D(JDSE, identifier="深空探测学报 (Journal of Deep Space Exploration) 2021, DOI 10.15982/j.issn.2096-9287.2021.20210003 (陈建华 CHEN Jianhua "
                   "et al.)", title="“长征五号”火箭液氧煤油发动机总体技术 (General Technical Review of Long March 5 Liquid Oxygen Kerosene Engine)",
  tier="B", rights_checked="'Copyright © 北京理工大学出版社 (Beijing Institute of Technology Press)' in the journal site data; "
                           "the journal's open-access and copyright pages render only through scripts and were not read",
  rights_class="RESTRICTED_REFERENCE",
  note="Peer-reviewed paper by the developing institute's engineers. Only the abstract is in the static page (full text loads by "
       "script and was not read).")

BLOCK("SRC-EUCASS2019-VINCI", "eucass-proceedings.eu returned HTTP 403", "VINCI engine paper (EUCASS 2019): discovery lead only.")
BLOCK("SRC-SAFRAN-VINCI-2018", "safran-group.com returned HTTP 403", "Vinci 2018 press release: discovery lead only.")
BLOCK("SRC-ESA-A5ECA-NEWELEM", "esa.int returned HTTP 404 (page moved or removed)", "Ariane 5 ECA new elements.")
BLOCK("SRC-IAC-LE9-2018", "iafastro.directory returned HTTP 429 (rate limited)", "LE-9 preliminary design results (IAC-18).")

# ------------------------------------------------------------------ LE-7
M16 = "NTRS 19910018905 PDF p.16 (proceedings p.542) 'H-II LAUNCH VEHICLE', bullet 'First Stage -- LE-7' (read from the page image)"
A(LE7, "propellants.oxidizer", None, "First Stage -- LE-7 - LOX/LH2", "LIQUID_OXYGEN", "", {}, MERKLE, M16, db0=None,
  note="The panel's own vehicle overview slide; no rating or value is printed with it.")
A(LE7, "propellants.fuel", None, "First Stage -- LE-7 - LOX/LH2", "LIQUID_HYDROGEN", "", {}, MERKLE, M16, db0=None)
A(LE7, "architecture.cycle", None, "First Stage -- LE-7 - Staged Combustion", "STAGED_COMBUSTION", "", {}, MERKLE, M16, db0=None,
  note="No rich side printed; none is inferred.")
M18 ="NTRS 19910018905 PDF p.18 (proceedings p.544) 'LE-7 Engine For H-2 First Stage'"
A(LE7, "architecture.cycle", None, "Staged Combustion Cycle", "STAGED_COMBUSTION", "", {}, MERKLE, M18, db0=None,
  note="No rich side printed; none is inferred.")
A(LE7, "propellants.oxidizer", None, "Propellant - LOX/LH2", "LIQUID_OXYGEN", "", {}, MERKLE, M18, db0=None)
A(LE7, "propellants.fuel", None, "Propellant - LOX/LH2", "LIQUID_HYDROGEN", "", {}, MERKLE, M18, db0=None)
for f, v, val, u, cond in [("performance.thrust_vac", "Thrust = 265,000 lbf. vac", 265000, "lbf", {"environment": "vacuum"}),
                           ("propellants.mixture_ratio", "Mixture Ratio = 6.0", 6.0, "", {"form": "UNSTATED"}),
                           ("performance.isp", "Specific Impulse = 451 sec", 451, "sec", {"environment": "UNSTATED"}),
                           ("performance.pc", "Chamber Pressure = 2133 psia", 2133, "psia", {"pc_station": "UNSTATED"}),
                           ("nozzle.area_ratio", "Nozzle Area Ratio = 60", 60, "", {}),
                           ("operation.burn_time", "Burn Time = 315 sec", 315, "sec", {}),
                           ("mechanical.mass", "Weight = 3439 lb", 3439, "lb", {"definition": "UNSTATED"})]:
    A(LE7, f, None, v, val, u, {**cond, "status_printed": "Development"}, MERKLE, M18, db0=None,
      note="Printed on the same slide as 'Status - Development' (June 1990): the engine before H-II flight; a panel's summary "
           "of NASDA figures.")
A(LE7, "identity.status", None, "Status - Development", "text", "", {}, MERKLE, M18, db0=None)
M7 = "MEXT 委12-6 (NASDA, 1997-04-09) PDF p.7 図-2 'LE－7エンジン主要諸元' (read from the page image)"
for f, v, val, u, cond, gloss in [
        ("performance.thrust_vac", "推力（真空中）　110 tonf", 110, "tonf", {"environment": "vacuum"}, "thrust (in vacuum)"),
        ("propellants.mixture_ratio", "混合比　6．0", 6.0, "", {"form": "UNSTATED"}, "mixture ratio; direction not printed"),
        ("performance.isp", "比推力　445．6 sec", 445.6, "sec", {"environment": "UNSTATED"}, "specific impulse; environment not printed on this row"),
        ("turbopump.fuel.speed", "液水ターボポンプ回転数　42200 rpm", 42200, "rpm", {}, "LH2 turbopump speed"),
        ("turbopump.oxidizer.speed", "液酸ターボポンプ回転数　18100 rpm", 18100, "rpm", {}, "LOX turbopump speed"),
        ("preburner.gas_temperature", "プリバーナガス温度　810 K", 810, "K", {}, "preburner gas temperature (OCR read 840; image reads 810)"),
        ("mechanical.length", "エンジン全長　3243 mm", 3243, "mm", {}, "engine overall length"),
        ("mechanical.diameter", "エンジン最大径　2610 mm", 2610, "mm", {}, "engine maximum diameter")]:
    A(LE7, f, None, v, val, u, cond, MEXT, M7, db0=None, note=f"Gloss ({_GLOSS}): {gloss}. Table title 主要諸元 = principal specifications.")
A(LE7, "performance.thrust_vac", None, "it offers propulsion of approximately 110 tons in a vacuum", 110, "tons",
  {"environment": "vacuum", "kind": "approximate"}, "SRC-JAXA-H2", "global.jaxa.jp H-II Launch Vehicle page, vehicle description", db0=None)

# ------------------------------------------------------------------ LE-7A
M6 = "MEXT 委12-6 (NASDA, 1997-04-09) PDF p.6 '参考 LE－7Aエンジンの開発概要' (read from the page image)"
A(LE7A, "identity.lineage", None, "このH－ⅡAロケットの第一段エンジンは、H－Ⅱロケットで使用されているLE－7エンジンを改良したLE－7Aです。", "text", "",
  {}, MEXT, M6, db0=None, note=f"Gloss ({_GLOSS}): 'The first-stage engine of this H-IIA is the LE-7A, an improvement of the LE-7 used "
                               "on the H-II.' Lineage only: no LE-7 value is inherited.")
A(LE7A, "propellants", None, "推進薬は、LE－7エンジンと同じ液化水素と液化酸素を推進薬とするエンジンです。", "text", "", {}, MEXT, M6, db0=None,
  note=f"Gloss ({_GLOSS}): 'an engine whose propellants are liquid hydrogen and liquid oxygen, the same as the LE-7.'")
M7A = "MEXT 委12-6 (NASDA, 1997-04-09) PDF p.7 図-2 'LE－7Aエンジン主要諸元' (read from the page image)"
for f, v, val, u, cond, gloss in [
        ("performance.thrust_vac", "推力（真空中）　110 tonf", 110, "tonf", {"environment": "vacuum"}, "thrust (in vacuum)"),
        ("operation.throttling", "推力可変機能あり（混合比制御なし）", "text", "", {}, "thrust variable capability: yes (no mixture-ratio control)"),
        ("propellants.mixture_ratio", "混合比　5．9", 5.9, "", {"form": "UNSTATED"}, "mixture ratio; direction not printed"),
        ("performance.isp", "比推力　441 sec", 441, "sec", {"environment": "UNSTATED"}, "specific impulse; environment not printed on this row"),
        ("turbopump.fuel.speed", "液水ターボポンプ回転数　41200 rpm", 41200, "rpm", {}, "LH2 turbopump speed"),
        ("turbopump.oxidizer.speed", "液酸ターボポンプ回転数　18050 rpm", 18050, "rpm", {}, "LOX turbopump speed"),
        ("preburner.gas_temperature", "プリバーナガス温度　740 K", 740, "K", {}, "preburner gas temperature"),
        ("mechanical.length", "エンジン全長　3765 mm", 3765, "mm", {}, "engine overall length"),
        ("mechanical.diameter", "エンジン最大径　2000 mm", 2000, "mm", {}, "engine maximum diameter")]:
    A(LE7A, f, None, v, val, u, {**cond, "epoch": "1997 development (実機型 prototype engines in test, p.5)"}, MEXT, M7A, db0=None,
      note=f"Gloss ({_GLOSS}): {gloss}. The LE-7A was in development in April 1997 (p.1, p.5): these are its specifications "
           "then, not a delivered rating.")
J3 = "資料37-3 (JAXA, 2017-09-05) PDF p.3 '1. LE-9エンジン基本仕様', column '（参考）LE-7Aエンジン'"
for f, v, val, u, cond, gloss in [
        ("architecture.cycle", "2段燃焼", "STAGED_COMBUSTION", "", {}, "staged combustion (literally 'two-stage combustion'); no rich side"),
        ("performance.thrust_vac", "1100kN（112tonf）", 1100, "kN", {"environment": "vacuum"}, "row 真空中推力 = vacuum thrust"),
        ("performance.isp", "440s", 440, "s", {"environment": "UNSTATED"}, "row 比推力（Isp）; environment not printed"),
        ("mechanical.mass", "1.8ton", 1.8, "ton", {"definition": "UNSTATED"}, "row 重量 = weight"),
        ("mechanical.length", "3.7m", 3.7, "m", {}, "row 全長 = overall length"),
        ("propellants.mixture_ratio", "5.9", 5.9, "", {"form": "UNSTATED", "mr_basis": "engine"}, "row エンジン混合比 = engine mixture ratio; direction not printed"),
        ("performance.pc", "12.3MPa", 12.3, "MPa", {"pc_station": "UNSTATED"}, "row 燃焼圧力 = combustion pressure; station not printed"),
        ("pumps.fuel.discharge_pressure", "28.1MPa", 28.1, "MPa", {}, "row FTP吐出圧力 = LH2 turbopump discharge pressure"),
        ("pumps.oxidizer.discharge_pressure", "26.6MPa", 26.6, "MPa", {}, "row OTP吐出圧力 = LOX turbopump discharge pressure"),
        ("control.valves", "空圧バルブ　オリフィスで作動点調整", "text", "", {}, "pneumatic valves; operating point set by orifices")]:
    A(LE7A, f, None, v, val, u, {**cond, "epoch": "2017 reference for the flying engine"}, JAXA17, J3, db0=None, note=f"Gloss ({_GLOSS}): {gloss}.")
for f, v, val, u, cond in [("propellants", "Propellant Liquid oxygen/ liquid hydrogen", "text", "", {}),
                           ("performance.thrust_vac", "Thrust (vacuum) 112 ton", 112, "ton", {"environment": "vacuum"}),
                           ("performance.isp_vac", "Isp (vacuum) 440sec", 440, "sec", {"environment": "vacuum"}),
                           ("mechanical.mass", "Weight 1,780kg", 1780, "kg", {"definition": "UNSTATED"}),
                           ("mechanical.length", "Length 3,670mm", 3670, "mm", {})]:
    A(LE7A, f, None, v, val, u, {**cond, "epoch": "as retrieved 2026-10-11"}, MHI7A, "mhi.com LE-7A page, 'Main specifications' table", db0=None)

# ------------------------------------------------------------------ LE-9
J3L9 = "資料37-3 (JAXA, 2017-09-05) PDF p.3 '1. LE-9エンジン基本仕様', column 'LE-9エンジン'"
for f, v, val, u, cond, gloss in [
        ("architecture.cycle", "エキスパンダブリード", "EXPANDER_BLEED", "", {}, "expander bleed"),
        ("performance.thrust_vac", "1471kN (150tonf)", 1471, "kN", {"environment": "vacuum"}, "row 真空中推力 = vacuum thrust"),
        ("operation.throttling", "63％スロットリング", 63, "%", {}, "63% throttling (printed under the thrust row)"),
        ("performance.isp", "425s", 425, "s", {"environment": "UNSTATED"}, "row 比推力（Isp）; environment not printed"),
        ("mechanical.mass", "2.4ton", 2.4, "ton", {"definition": "UNSTATED"}, "row 重量 = weight"),
        ("mechanical.length", "3.75m", 3.75, "m", {}, "row 全長 = overall length"),
        ("propellants.mixture_ratio", "5.9", 5.9, "", {"form": "UNSTATED", "mr_basis": "engine"}, "row エンジン混合比; direction not printed"),
        ("performance.pc", "10.0MPa", 10.0, "MPa", {"pc_station": "UNSTATED"}, "row 燃焼圧力; station not printed"),
        ("pumps.fuel.discharge_pressure", "19.0MPa", 19.0, "MPa", {}, "row FTP吐出圧力"),
        ("pumps.oxidizer.discharge_pressure", "17.9MPa", 17.9, "MPa", {}, "row OTP吐出圧力"),
        ("control.valves", "電動バルブ　作動点を連続制御", "text", "", {}, "electrically driven valves; operating point continuously controlled")]:
    A(LE9, f, None, v, val, u, {**cond, "epoch": "2017 basic design complete (基本設計を完了), prototype engine testing"}, JAXA17, J3L9,
      db0=None, note=f"Gloss ({_GLOSS}): {gloss}. A design specification during development, not a flight-engine rating.")
A(LE9, "test_history.engine", None, "定格の約90%の推力での定常性能を取得。得られたデータにより、100%での作動状況を解析的に確認。", "text", "", {}, JAXA17,
  "資料37-3 PDF p.12 '試験結果の評価'", db0=None,
  note=f"Gloss ({_GLOSS}): steady-state performance obtained at about 90% of rated thrust; 100% operation confirmed analytically. "
       "Prototype #1-1 engine, 2017.")
A(LE9, "identity.summary", None, "LE-9's propellants, thrust, Isp, weight, cost are LOX/LH2, 1471kN, 425s, 2410kg and half of the current Japanese "
  "first stage engine, respectively.", "text", "", {"epoch": "2017 development"}, IAC17LE9, "IAC-17,C4,1,4,x36601 abstract", db0=None)
A(LE9, "architecture.cycle", None, "The most important feature is engine cycle; expander bleed cycle.", "EXPANDER_BLEED", "", {}, IAC17LE9,
  "IAC-17,C4,1,4,x36601 abstract", db0=None)
A(LE9, "performance.summary", None, "エンジン推力は 1 471 kN，比推力は 425 s である．", "text", "", {"epoch": "2017 development"}, IHI,
  "IHI技報 57(3) p.59 (PDF p.2) §2.3 エンジン諸元 (read from the page image)", db0=None,
  note=f"Gloss ({_GLOSS}): 'engine thrust is 1471 kN and specific impulse 425 s'. Environment not printed.")
A(LE9, "control.throttling", None, "バルブ駆動方式には電動バルブを採用することで，エンジン推力スロットリングを可能としている．", "text", "", {}, IHI,
  "IHI技報 57(3) p.59 (PDF p.2) §2.3 (read from the page image)", db0=None,
  note=f"Gloss ({_GLOSS}): electric valves enable engine thrust throttling.")
for f, v, val, u, cond in [("propellants", "Propellant Liquid oxygen/liquid hydrogen", "text", "", {}),
                           ("performance.thrust_vac", "Thrust(vacuum) 150ton", 150, "ton", {"environment": "vacuum"}),
                           ("performance.isp_vac", "Isp(vacuum) 425sec", 425, "sec", {"environment": "vacuum"}),
                           ("mechanical.mass", "Weight 2,400kg", 2400, "kg", {"definition": "UNSTATED"}),
                           ("mechanical.length", "Length 3,750mm", 3750, "mm", {}),
                           ("architecture.cycle", "This engine utilizes Japan's unique expander bleed cycle method", "EXPANDER_BLEED", "", {})]:
    A(LE9, f, None, v, val, u, {**cond, "epoch": "as retrieved 2026-10-11"}, MHI9, "mhi.com LE-9 page", db0=None)
S("SCH-DB05-LE9-IHI-FIG2", engine_ids=[LE9], source_id=IHI, locator="IHI技報 57(3) p.59 (PDF p.2) 第2図 'LE-9 エンジンサイクル (2)'",
  title="LE-9 エンジンサイクル / LE-9 engine cycle", kind="engine cycle diagram, colour (LOX blue, LH2 red), flow arrows; credited to the "
  "paper's reference (2), so a reproduction in an IHI paper", viewed_how="rendered PDF page at 120 dpi", legible=True,
  note="Labels: LOX, OTP, MOV, LH2, FTP, MFV, CCV (燃焼室冷却バルブ, chamber cooling valve), TCV (推力コントロールバルブ, thrust control "
       "valve), ノズル. Not transcribed: rights restricted (AIREX copyright statement) and a 2017 development-era figure.")

# ------------------------------------------------------------------ Vulcain
R10 = "NTRS 19910018907 PDF p.10 (briefing p.592) 'Ariane 5 - Vulcain Engine' (read from the page image)"
A(VUL, "architecture.turbomachinery", None, "System Uses Gas Generator; Separate LH2 and LOX Turbopumps", "text", "", {}, RICE, R10, db0=None)
A(VUL, "architecture.cycle", None, "System Uses Gas Generator", "GAS_GENERATOR", "", {}, RICE, R10, db0=None)
A(VUL, "propellants.oxidizer", None, "Propellant LH2/LOX", "LIQUID_OXYGEN", "", {}, RICE, R10, db0=None)
A(VUL, "propellants.fuel", None, "Propellant LH2/LOX", "LIQUID_HYDROGEN", "", {}, RICE, R10, db0=None)
for f, v, val, u, cond in [("performance.thrust_vac", "Vacuum Thrust 1025 kN (230,000 lb)", 1025, "kN", {"environment": "vacuum"}),
                           ("propellants.mixture_ratio", "O/F 5.2", 5.2, "", {"form": "OXIDIZER_TO_FUEL"}),
                           ("performance.isp_vac", "Isp (Vac) 431.6 s", 431.6, "s", {"environment": "vacuum"}),
                           ("performance.pc", "Pc 100 Bars (1450 psi)", 100, "bar", {"pc_station": "UNSTATED"}),
                           ("mechanical.mass", "Engine Mass 1300 kg (2860 lbs)", 1300, "kg", {"definition": "UNSTATED"}),
                           ("turbines.fuel.speed", "LH2 Turbine Speed 34,200 rpm", 34200, "rpm", {}),
                           ("turbines.oxidizer.speed", "LOX Turbine Speed 13,000 rpm", 13000, "rpm", {}),
                           ("turbines.fuel.power", "LH2 Turbine Power 11,300 kW", 11300, "kW", {}),
                           ("turbines.oxidizer.power", "LOX Turbine Speed 2,900 kW", 2900, "kW", {"label_as_printed": "LOX Turbine Speed"})]:
    A(VUL, f, None, v, val, u, {**cond, "epoch": "June 1990 development (first ignition then still scheduled)"}, RICE, R10, db0=None,
      note="A US contractor's 1990 summary of the engine in development; p.2 of the same briefing says thrust and combustion-"
           "pressure increases were under way.")
R2 = "NTRS 19910018907 PDF p.2 (briefing p.584) 'Summary of Europe's Advanced Propulsion Technology Activities' (read from the page image)"
A(VUL, "history.development", None, "Vulcain H/O Engine Is a Major Development Led by SEP; 1st Ignition Sequence in 7/90; 1st Full Power Firing in 12/90",
  "text", "", {}, RICE, R2, db0=None,
  note="Presented 25-29 June 1990: the July and December 1990 events are a schedule at the time of writing, not a record. "
       "OCR read 'I-I/O'; the image reads 'H/O'.")
A(VUL, "history.performance_growth", None, "Performance Improvements Underway, Including Thrust and Combustion Pressure Increases", "text", "", {},
  RICE, R2, db0=None)
EV = "esa.int 'Vulcain engine' page"
A(VUL, "performance.thrust_vac", None, "the Ariane 5 Vulcain engine could deliver 115 tonnes of thrust in vacuum in its initial version", 115,
  "tonnes", {"environment": "vacuum", "epoch": "initial version"}, ESAVUL, EV, db0=None)
A(VUL, "mechanical.dimensions", None, "The Vulcain engine was 3 m high, 1.76 m in diameter and weighed 1686 kg.", "text", "", {}, ESAVUL, EV, db0=None)
A(VUL, "turbopump.oxidizer", None, "The liquid oxygen turbopump operated at a speed of 13 600 rpm and had a power level of 3 MW.", "text", "", {},
  ESAVUL, EV, db0=None)
A(VUL, "turbopump.fuel", None, "Its hydrogen counterpart turns at 34 000 rpm and has 12 MW of power", "text", "", {}, ESAVUL, EV, db0=None)
A(VUL, "performance.mass_flow", None, "These elements forced the cryogenic propellants at high pressure into the chamber at a rate of 235 kg/sec.",
  235, "kg/sec", {}, ESAVUL, EV, db0=None)
A(VUL2, "performance.thrust", None, "The Vulcain 2 engine delivered a thrust in the order of 130 tonnes.", 130, "tonnes",
  {"environment": "UNSTATED", "kind": "order of magnitude ('in the order of')"}, ESAVUL, EV, db0=None)
A(VUL2, "test_history.engine", None, "the Vulcain 2 engine was successfully tested in the load simulation device at the Lampoldshausen test "
  "facilities of DLR in Germany", "text", "", {"epoch": "May 2004"}, ESAV2, "esa.int news 14 May 2004", db0=None,
  note="With a reinforced nozzle extension after the December 2002 Ariane 5 ECA failure (same page).")

# ------------------------------------------------------------------ Vinci
EV05 = "esa.int news 27 July 2005 'Thumbs up for 60-second firing'"
A(VINCI, "architecture.cycle", None, "This re-ignitable cryogenic engine uses a more efficient expander cycle, which does not require a gas generator "
  "to drive its two turbo-pumps: one for liquid hydrogen (LH2) and one for liquid oxygen (LOX).", "EXPANDER", "", {}, ESAVI05, EV05, db0=None)
A(VINCI, "performance.design_target", None, "Vinci will provide 18 tonnes of thrust in vacuum with a specific impulse of 465 sec.", "text", "",
  {"environment": "vacuum", "epoch": "2005 development", "kind": "programme target (future tense)"}, ESAVI05, EV05, db0=None)
EA6 = "esa.int 'The engines of Ariane 6' (5 June 2024), Vinci section"
A(VINCI, "operation.restarts", None, "It can ignite up to four times in a single Ariane 6 flight", "text", "", {"epoch": "2024"}, ESAA6, EA6, db0=None)
A(VINCI, "performance.thrust", None, "180 Kn of thrust for the Vinci cryogenic engine", 180, "Kn", {"environment": "UNSTATED", "epoch": "2024"},
  ESAA6, EA6, db0=None, note="Unit printed 'Kn'.")
A(VINCI, "architecture.cycle", None, "The VINCI engine is a cryogenic expander cycle engine.", "EXPANDER", "", {}, IAC21VI,
  "IAC-21,C4,1,5,x65631 abstract PDF p.1", db0=None)
A(VINCI, "operation.capabilities", None, "The VINCI has multiple restarts and throttle capabilities that are key elements for the Ariane 6 versatility.",
  "text", "", {}, IAC21VI, "IAC-21,C4,1,5,x65631 abstract PDF p.1", db0=None)
A(VINCI, "architecture.cycle", None, "The Vinci engine concept utilizes the thermodynamic expander cycle without a gas generator", "EXPANDER", "",
  {}, IAC18VI, "IAC-18,C4,1,4,x45921 abstract", db0=None)

# ------------------------------------------------------------------ China
A13 = "IAC-13,C4,1,1,x18525 abstract"
A(YF75, "identity.summary", None, "we developed the YF-75 engine with 8-ton thrust level, which has been the high performance cryogenic upper stage "
  "engine in service since 1994 in china", "text", "", {}, BAPI13, A13, db0=None,
  note="'8-ton thrust level' is a class statement, not a value; environment not printed.")
A(YF75D, "identity.summary", None, "We are now developing the YF-75D upper stage expender cycle engine", "text", "", {"epoch": "2013 development"},
  BAPI13, A13, db0=None, note="'expender' as printed. Development status in 2013; open/closed expander not printed.")
A(YF77, "identity.summary", None, "the YF-77 main engine with 50-ton thrust level for China's new generation launch vehicle CZ-5", "text", "",
  {"epoch": "2013 development"}, BAPI13, A13, db0=None)
A77 = "IAC-13,C4,1,2,x17679 abstract"
A(YF77, "architecture.cycle", None, "The engine utilizes a gas generator cycle", "GAS_GENERATOR", "", {}, BAPI77, A77, db0=None)
A(YF77, "performance.summary", None, "each engine provided 700-kN at an oxidizer-to-fuel mixture ration (O/F) of 5.5", "text", "",
  {"environment": "UNSTATED"}, BAPI77, A77, db0=None, note="'ration' as printed. Environment of the 700 kN not printed.")
A(YF77, "identity.installation", None, "Two YF-77 engines fly on the core stage of the Long-March 5 launch vehicle.", "text", "", {}, BAPI77, A77,
  db0=None)
A15 = "IAC-15,C4,1,13,x28419 abstract"
A(YF100, "identity.summary", None, "The rocket engine, which is called YF-100, is a 1200kN LOX/ Kerosene rocket engine.", "text", "",
  {"environment": "UNSTATED"}, XAPI15, A15, db0=None, note="Environment of the 1200 kN not printed.")
A(YF100, "architecture.cycle", None, "YF-100 is a single chamber rocket engine that utilizes an oxidizer-rich staged combustion cycle.",
  "OXIDIZER_RICH_STAGED_COMBUSTION", "", {}, XAPI15, A15, db0=None)
A(YF100, "identity.derivative_configuration", None, "a new general configuration of the engine has been developed. The characteristic of this "
  "configuration，which is also called post-pump swing general configuration", "text", "", {}, XAPI17, "IAC-17,C4,5,13,x41028 abstract",
  db0=None, note="A distinct (post-pump swing) configuration of the YF-100: never merged into the baseline.")
AJ = "深空探测学报 2021 DOI 10.15982/j.issn.2096-9287.2021.20210003, 摘要"
A(YF100, "architecture.cycle", None, "高压补燃液氧煤油发动机应用于“长征五号”（CZ-5）运载火箭助推模块，该发动机采用高压补燃循环", "STAGED_COMBUSTION", "",
  {"configuration": "CZ-5 booster module engine"}, JDSE, AJ, db0=None,
  note=f"Gloss ({_GLOSS}): 'the high-pressure staged-combustion LOX/kerosene engine is used on the CZ-5 booster modules; it uses a "
       "high-pressure staged-combustion cycle'. 补燃 (literally 'supplementary/after-burning') is the Chinese term for staged "
       "combustion; the rich side is not printed here.")
A(YF100, "operation.capabilities", None, "具有高性能、自身起动、大范围推力和混合比调节、结构紧凑等特点", "text", "", {"configuration": "CZ-5 booster module engine"},
  JDSE, AJ, db0=None, note=f"Gloss ({_GLOSS}): 'high performance, self-starting, wide-range thrust and mixture-ratio regulation, compact'.")

# ------------------------------------------------------------------ conflicts (none is averaged or chosen)
C("CF-DB05-LE7-EPOCH", engine_id=LE7, field_path="performance.thrust_vac, performance.isp",
  claims=[["Thrust = 265,000 lbf. vac; Specific Impulse = 451 sec (Status - Development, June 1990)", MERKLE, "PDF p.18"],
          ["推力（真空中） 110 tonf; 比推力 445．6 sec (主要諸元, April 1997)", MEXT, "PDF p.7"],
          ["approximately 110 tons in a vacuum", "SRC-JAXA-H2", "H-II page"]],
  resolution="UNRESOLVED", kind="different_epoch",
  explanation="1990 figures are for the engine in development (a US panel's summary); 1997 and later agency figures describe the "
              "flying engine. No opened document says what changed between them.")
C("CF-DB05-LE7A-EPOCH", engine_id=LE7A, field_path="performance.thrust_vac, performance.isp, mechanical",
  claims=[["推力（真空中） 110 tonf; 比推力 441 sec; 全長 3765 mm (prototype development, April 1997)", MEXT, "PDF p.7"],
          ["1100kN（112tonf）; 440s; 3.7m (reference column, Sept 2017)", JAXA17, "PDF p.3"],
          ["Thrust (vacuum) 112 ton; Isp (vacuum) 440sec; Length 3,670mm (as retrieved 2026)", MHI7A, "Main specifications"]],
  resolution="UNRESOLVED", kind="different_epoch",
  explanation="The 1997 values are the engine's specifications during development; the 2017 and manufacturer values describe the "
              "flying engine. No opened document records the change; nothing from one epoch fills the other.")
C("CF-DB05-LE9-THRUST-LEVEL", engine_id=LE9, field_path="performance.thrust_vac",
  claims=[["1471kN (150tonf)", JAXA17, "PDF p.3"], ["1 500 kN レベル (abstract)", IHI, "PDF p.1"], ["エンジン推力は 1 471 kN", IHI, "PDF p.2"]],
  resolution="EXPLAINED", kind="rating_or_rounding",
  explanation="'1 500 kN level' is the same paper's class statement; its own §2.3 prints 1 471 kN.")
C("CF-DB05-VULCAIN-THRUST", engine_id=VUL, field_path="performance.thrust_vac",
  claims=[["Vacuum Thrust 1025 kN (230,000 lb) (June 1990, in development)", RICE, "PDF p.10"],
          ["115 tonnes of thrust in vacuum in its initial version", ESAVUL, "Vulcain page"]],
  resolution="PARTIALLY_RESOLVED", kind="different_epoch",
  explanation="The 1990 briefing itself says thrust and combustion-pressure increases were under way (p.2): the 1990 value is "
              "pre-growth. The flown value is known only from ESA's restricted page; the change is not documented.")
C("CF-DB05-VULCAIN-TURBOPUMPS", engine_id=VUL, field_path="turbines.speed, turbines.power",
  claims=[["LH2 34,200 rpm / 11,300 kW; LOX 13,000 rpm / 2,900 kW (June 1990)", RICE, "PDF p.10"],
          ["LOX 13 600 rpm, 3 MW; LH2 34 000 rpm, 12 MW", ESAVUL, "Vulcain page"]],
  resolution="UNRESOLVED", kind="different_epoch",
  explanation="Development-era and later agency figures differ; whether by epoch or rounding is not established.")
C("CF-DB05-VINCI-EPOCH", engine_id=VINCI, field_path="performance.thrust",
  claims=[["Vinci will provide 18 tonnes of thrust in vacuum with a specific impulse of 465 sec (July 2005, a target)", ESAVI05, "news"],
          ["180 Kn of thrust (June 2024, environment not printed)", ESAA6, "Vinci section"]],
  resolution="UNRESOLVED", kind="different_epoch",
  explanation="A 2005 development target and a 2024 figure for the qualified engine; not averaged, not equated.")
