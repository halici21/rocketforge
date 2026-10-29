"""DB-0 conflict web pass (2026-10-28): the open DB-0 conflicts whose secondary pages could be fetched with fetch.py.
Each claim was searched for in the page's extracted text; a value counts as seen only when the number stands in the text
in the sense DB-0 gave it. These are news, museum, catalogue and encyclopedia-style pages: they settle what a page says,
rarely what an engine does, so most records stay open. No assertion is filed from them."""
import json
from pathlib import Path

from ledger import D, C, BLOCK

_REG = {s["source_id"]: s for s in json.loads(
    (Path(__file__).resolve().parents[2] / "data" / "sources.json").read_text(encoding="utf-8"))["sources"]}


def W(sid, note):
    """A fetched web page read from its text; identity as registered by DB-0, title not re-read."""
    s = _REG[sid]
    D(sid, identifier=s["url"], title=s["title"], tier=s["tier"],
      rights_checked="web page fetched by fetch.py on 2026-10-28 and read from its extracted text; site copyright, no "
                     "reuse licence found", rights_class="RIGHTS_REVIEW_REQUIRED", note=note)


def NE(sid, reason):
    BLOCK(sid, reason, "Fetched and searched; the DB-0 claim stays a search-result claim.")


# ------------------------------------------------------------------ pages read
for _sid, _note in [
    ("SRC-NAKEDSCI-NK33", "Russian news page; gives the index 14D15."),
    ("SRC-RSW-RD0124", "RussianSpaceWeb; dimensions as the design intent ('roughly the same as RD-0110')."),
    ("SRC-ENGINEHISTORY-RPE02-2", "AEHS essay on the V-2 engine; 85 % hydrogen peroxide, permanganate catalyst."),
    ("SRC-ENGINEHISTORY-V2", "AEHS V-2 page; 203 s SL / 239 s vac; no 'Triebwerk 39' designation in the text."),
    ("SRC-STARSEM-ST07", "Starsem Soyuz user's manual page text: Fregat 'Restart capability up to 20'."),
    ("SRC-RSW-FREGAT", "RussianSpaceWeb Fregat page: S5.92 323 / 329 s, 1,400 / 2,000 kg modes."),
    ("SRC-LPRE-NPOEM-RD0120UP", "Paper on RD-0120 upgrades; history line 'KVD-1 (RD56) 1962-1974'."),
    ("SRC-IHIFAN-LE9", "IHI fan page: LE-9 LH2 turbopump 41,600 rpm."),
    ("SRC-WEBLIO-LE5", "Japanese dictionary mirror of Wikipedia: LE-5B 137.2 kN; 3 % idle with the turbine not driven."),
    ("SRC-SPACENEWS-33640", "SpaceNews 2001: Vikas chamber pressure raised from 52.5 to 58.5 bar."),
    ("SRC-SLIDESHARE-CRYO", "Slide deck on Indian cryogenic engines: CE-7.5 58 bar nominal."),
    ("SRC-IASGYAN-CE20", "Exam-preparation page: CE-20 19-20 t nominal, 22 t uprated."),
    ("SRC-KSCI-KARI-2009-KRE75", "KARI 2009 conference paper: 75-ton engine design 74.8 t vac, 306.9 s, 60 bar."),
    ("SRC-HF-SPACEYL-ENGINES", "Unsourced question-answer dataset; Vulcain 2 33 kg/s H2."),
    ("SRC-M3D-AGNIKUL-2026", "Trade-press page: Agnilet 6.2 kN."),
    ("SRC-IE-AGNIBAAN", "Indian Express: Agnilet 'approximately 3kN of thrust at sea level'."),
    ("SRC-SPACENEWS-12177", "SpaceNews: KSLV first stage engine named RD-151."),
    ("SRC-SFN-KSLV-2010", "Spaceflight Now 2010: KSLV first stage RD-151."),
    ("SRC-GE-WELKIN-EN", "Galactic Energy English page (fetched 2026-10-28): 'CQ-50 Reusable LOX/Kerosene Engine' 500 kN "
                         "thrust at sea level, 265 s; 600 kN (Vacuum Version), 330 s (Vacuum Version); 40-100 %; CQ-90 "
                         "990 kN / 1160 kN. The Chinese page (List/cid/5) names it 苍穹50 with the same figures."),
    ("SRC-36KR-JZYJ", "36Kr article: Longyun 70 t class."),
    ("SRC-JIEMIAN-14422448", "Jiemian article: Longyun 80 t class."),
    ("SRC-AR-STARLINER-2016", "Aerojet Rocketdyne release: '1,500-pound thrust class OMAC engines'."),
    ("SRC-ARXIV-2107-06795", "arXiv paper: Starliner four 7000 N (1600 lbf) OMAC main engines, twelve 375 N RCS."),
    ("SRC-SATCAT-BT4", "Satellite catalogue page: BT-4 450 N."),
    ("SRC-MECO-CYGNUS-REBOOST-2018", "Repost of Spaceflight Now: BT-4 'produces around 100' (text cut after the number)."),
    ("SRC-SFN-IM1-2024", "Spaceflight Now 2024: VR900 '900 lbf' class."),
    ("SRC-NASA-TALOS", "NASA page: TALOS on MON-25 / MMH."),
    ("SRC-AIRPORTTECH-PEREGRINE", "Trade page: five 667 N main engines and twelve 45 N thrusters on MMH and mixed oxides of nitrogen."),
    ("SRC-NAMMO-LEROS1B", "Nammo product page: LEROS 1b 635 N."),
    ("SRC-NTRS-20140016838", "NASA paper: GPIM carries four 1 N and one 22 N thrusters."),
    ("SRC-NTRS-20170001286", "NASA paper: the GR-1 'awaits its first on-orbit demonstration' on GPIM; GR-22 upgrade testing."),
    ("SRC-IAC11-490N-CN", "IAC 2011 abstract: 490 N engine 2990 N.s/kg at area ratio 154 and 0.68 MPa."),
    ("SRC-IAC03-LAE-CN", "IAC 2003 abstract: 'nominal vacuum specific impulse of 3 030 N . s/kg' at area ratio 154 and 0.68 MPa."),
    ("SRC-SPACEBUCKET-AEON", "Blog: Aeon engines gas generator; up to 23,000 lbf per engine at sea level, 207,000 lbf for nine."),
    ("SRC-AIRPORTTECH-TERRAN1", "Trade page: Aeon 1 and Aeon Vac 'gas generator engine cycle'; no thrust per engine."),
    ("SRC-SFN-TERRAN1-2023", "Spaceflight Now 2023: nine Aeon 1 engines '207,000 pounds of thrust'."),
    ("SRC-MASTEN-ENGINES", "Masten engines page: Broadsword 25,000 lbf sea level."),
    ("SRC-PURDUE-AJ26", "Purdue page: AJ26-NK33A table (339,000 lbf vac, 2,109 psia); no source cited; read for CF-DB05-NK33-PC-THRUST."),
    ("SRC-IAC16-32550", "IAC 2016 abstract by ISRO LPSC authors: LAM 'MON-3 & MMH at a mixture ratio of 1.6', 440 N, area ratio 160."),
    ("SRC-NEWSPACEECON-V21", "Trade page: Vulcain 2.1 1,371 kN (308,000 lbf) vac against the Vulcain 2's 1,359 kN; no sources."),
    ("SRC-KOREASCI-AJ26", "Korean journal page: AJ26 1,680 / 1,510 kN."),
    ("SRC-NSF-LAUNCHERONE-2020", "NASASpaceflight 2020: NewtonFour 5,000 lbf."),
    ("SRC-AVIATIONIST-L1-2020", "The Aviationist 2020: NewtonFour about 6,000 lb."),
    ("SRC-RELATIVITY-PR-2025-03-07", "Relativity release 2025: Aeon R 269,000 lbf."),
    ("SRC-ULA-BE4-FACTSHEET", "ULA fact sheet: BE-4 550,000 lbf."),
    ("SRC-SPACEX-FUG-2025", "Falcon user's guide 2025: Merlin 845 kN (190,000 lbf) SL; MVac 981 kN (220,500 lbf)."),
    ("SRC-WEVOLVER-MERLIN", "Spec aggregator: Merlin 854 kN / 190,000 lbf, 10.8 MPa, 100-57 %, MVac 348 s; no sources."),
    ("SRC-UC-OLLI-SPACEX", "University course page: Merlin 854 kN."),
    ("SRC-SFN-2015-FT", "Spaceflight Now 2015: Merlin 147,000 to 170,000 lbf; MVac 210,000 lbf."),
    ("SRC-SPACEX-PR-M1C-2007", "SpaceX release 2007: Merlin 1C 95,000 lbf SL, over 108,000 lbf vac, 304 s (Falcon 9)."),
    ("SRC-TESLARATI-R2", "Teslarati: Raptor 2 300 bar routine, 321 bar at first static fire."),
    ("SRC-WCCF-RAPTOR-330", "Wccftech: Raptor 330 bar 'consistently' (second-hand)."),
    ("SRC-RL-NEUTRON-PAGE", "Rocket Lab Neutron page: Archimedes 200,000 lbf (890 kN)."),
    ("SRC-RL-ARCH-BUILD", "Rocket Lab release: Archimedes 202,300 lbf (900 kN)."),
    ("SRC-FIREFLY-ALPHA-PAGE", "Firefly Alpha page: 4x Reaver 801 kN (180,072 lbf) vac, 295.6 s; Lightning 70.1 kN."),
    ("SRC-FIREFLY-MIRANDA-RR", "Firefly release: 45,000 lbf per Reaver."),
    ("SRC-RSW-RD191", "RussianSpaceWeb: RD-191 311.2 s SL."),
    ("SRC-GLAVKOSMOS-RD181", "Glavkosmos RD-181 table: 196 / 212 tf, 311 / 339 s, 262.6 kgf/cm2, 2,200 kg."),
    ("SRC-WWW1-RD0124", "Russian page: RD-0124 modification 60 t, 361 s."),
    ("SRC-FRONTIER-SOYUZ5", "Blog-style page: RD-171MV 'approximately 800 tons'; no sea-level figure."),
    ("SRC-GLOBALSEC-SOYUZU", "GlobalSecurity: 11D511 'RD-107', 11D512 'RD-108'."),
    ("SRC-KPI-GLUSHKO", "Ukrainian university page on Glushko: RD-100 / 101 / 103M at 26 / 37 / 44 t."),
    ("SRC-FAS-R2", "FAS R-2 page: RD-101 37,210 / 41,208 kgf; methyl alcohol replaced ethyl alcohol."),
    ("SRC-PLANETARY-GLUSHKO", "Planetary Society: RD-101 35 t (340 kN)."),
    ("SRC-RSW-RD0110", "RussianSpaceWeb: RD-0110 7 MPa, 3,195 m/s, 'Burn time 230 or 240 seconds'."),
    ("SRC-RSW-RD0210", "RussianSpaceWeb: RD-0210 593.6 kN, 15 MPa, 230 s."),
    ("SRC-SATNOW-HM7B", "Product catalogue: HM7B 64.8 kN, 446 s, 165 kg."),
    ("SRC-SATNOW-AESTUS", "Product catalogue: Aestus 111 kg."),
    ("SRC-DLR-VIKING-IMG", "DLR image page: Viking 5 675 / 758 kN."),
    ("SRC-IAC-09-3159", "IAC 2009 abstract: Vexin 'about 28 metric tons'."),
    ("SRC-IAC-10-6759", "IAC 2010 abstract: Valois, the single Diamant B first-stage engine, 35 metric tons."),
    ("SRC-DEUTSCHESMUSEUM-EUROPA", "Museum page: Coralie 262 kN, Astris 22.56 kN, Astris by MBB and ERNO."),
    ("SRC-NASM-HWK109509", "Smithsonian record: HWK 109-509 200-1800 kg, permanganate catalyst."),
    ("SRC-WARBIRDS-ME262", "Me 262 page: 'a single 9.8 kN (2,200 lbf) thrust BMW 109-718'."),
    ("SRC-BCAR-BLUESTEEL", "Blue Steel page: Stentor first chamber 24,000 lbf."),
    ("SRC-ESA-PROMETHEUS", "ESA page: Prometheus cheaper than 'the previous generation of 1200 kN engines'."),
    ("SRC-MHI-LE5B", "MHI page: LE-5B-3 14 ton, 449 s, 285 kg."),
    ("SRC-GS-CZ2D", "GlobalSecurity CZ-2D: YF-23 vernier 46.1 kN."),
    ("SRC-EDA-CZ4C", "Encyclopedia page: CZ-4C third stage YF-40A 'just over 100 kN' each."),
    ("SRC-WEBLIO-YF75D", "Japanese Wikipedia mirror: YF-75D 88.26 kN, 442 s, 470 s."),
    ("SRC-WEBLIO-YF77", "Japanese Wikipedia mirror: YF-77 438 s vac / 333 s SL, 510 / 700 kN, 102 bar."),
    ("SRC-NCSTI-2023-TQ", "Exhibition text: TQ-12 vacuum thrust 80 t, vacuum Isp 350 s, MR 3.5, area ratio 40."),
    ("SRC-BJNEWS-TQ15A", "Beijing News: TQ-15A design range 60-100 %, +11.8 % thrust, +126 m/s Isp."),
    ("SRC-JIEMIAN-TQ", "Jiemian: improved TQ-12 on a test vehicle, '45%-111%' throttling."),
    ("SRC-SPACEPIONEER-TH12", "Space Pioneer page: TH-12 95 t SL, 285 s."),
    ("SRC-SPACEPIONEER-TH12V", "Space Pioneer page: TH-12V 110 t vac, 346 s; 'Cycle Gas generator'; 50-110 %."),
    ("SRC-ITHOME-655315", "IT Home: Space Pioneer 110 t engine full-system hot fire."),
    ("SRC-DESIGNSYS-RM81", "Designation-systems page: XLR81-BA-9 = Bell Model 8096."),
    ("SRC-ASTRONAUTIX-AGENAB", "Encyclopedia Astronautica Agena B: XLR81-BA-7 (8081), XLR81-BA-9 (8096); stage 71.17 kN (15,999 lbf), 285 s."),
    ("SRC-HISTORYOFWAR-X1", "History of War: X-1 engine XLR-11-RM3."),
    ("SRC-FLICKR-MB3", "Museum placard photographed on Flickr: MB-3 (LR79-NA-9) for Thor and Atlas E and F."),
    ("SRC-ENGINEHISTORY-RPE05", "AEHS: MA-5 booster LR89-5 163,211 lbf SL; Atlas E/F MA-3."),
    ("SRC-ASTRONAUTIX-LR89-7", "Encyclopedia Astronautica: LR89-7 213,118 lbf vac."),
    ("SRC-NASA-MSFC-MERCREDSTONE", "MSFC page: Redstone A-series final 78,000 lb."),
    ("SRC-PURDUE-XRS2200", "Purdue page: XRS-2200 261,200 / 206,200 lbf."),
    ("SRC-NTRS-19980174934", "NASA paper: XRS-2200 '200,000+ lbs' SL."),
    ("SRC-PURDUE-RS27A", "Purdue page: RS-27A vernier 1,012 lb."),
    ("SRC-SNOB-172276", "Snob: Energomash quote, '> 280 bar' with a 10 % margin."),
    ("SRC-SFN-IPD-2006", "Spaceflight Now 2006 PWR release: IPD 21 of 26 tests, up to 100 percent power."),
    ("SRC-ESA-BLOG-ART2ENG", "ESA blog 2023: the Artemis II OMS-E 'has flown to space six times already between 2000 and 2002'."),
    ("SRC-AIRPORTTECH-PHX", "Trade page on Phoenix: 'eight 1.0lbf and 5.0lbf ... engines and 12 68.0lbf ... thrusters'; no MR-107N or 300 N."),
    ("SRC-FLIGHTGLOBAL-ROTON", "Flight International: RocketJet 'dozens of small combusters arranged in a ring'."),
    ("SRC-MANIFOLD-STARSHIP", "Prediction-market question page; 'original design was thought to use pure autogenous pressurization'."),
    ("SRC-WCCFTECH-SN10", "Wccftech 2021: 'Prior to SN9, SpaceX used autogenous pressurization'."),
]:
    W(_sid, _note)

# ------------------------------------------------------------------ fetched, not evidence
NE("SRC-NAMU-KRE075", "Namuwiki mirror; the 75.8 tonf DB-0 cited is not in the extracted text")
NE("SRC-COLDFACTS-DHAWAN1", "news page; no thrust value in the text")
NE("SRC-NEWSPACETRACKER-IMPROP", "company profile page; no engine thrust in the text")
NE("SRC-AMPAC-JUNO-2011", "the 640 N DB-0 cited is not in the extracted text")
NE("SRC-SATNOW-BROADSWORD", "only catalogue navigation came through; no product values")
NE("SRC-SPACEX-UPDATES", "script-rendered page; six characters of text")
NE("SRC-SPACEX-STARSHIP-SPECS", "script-rendered page; six characters of text")
NE("SRC-APS-GODDARD", "the launch date DB-0 cited is not in the extracted text")
NE("SRC-METALAM-V21", "trade article on additive parts; no thrust value")
NE("SRC-3DPI-V21", "trade article on the nozzle; no thrust value")
NE("SRC-DHMUSEUM-SPECTRE", "museum page on the Spectre; the Super Sprite 4,000 lb is not in it")
NE("SRC-NASA-TND7151", "no usable text layer (1.5 kB extracted)")
NE("SRC-NAKEDSCI-RAPTOR", "the 266.7 bar DB-0 cited is not in the extracted text")
NE("SRC-SSAU-2587", "the gas-generator wording DB-0 cited is not in the extracted text")
NE("SRC-SPACENEWS-79146", "paywall page; article text not delivered")
NE("SRC-NBC-PHX", "news article; no engine count in the text")
NE("SRC-BILI-CV15113396", "script-rendered page; no text extracted")

# ------------------------------------------------------------------ conflicts
_LOC = {"T": "page text (fetched 2026-10-28)", "NF": "fetched; value not in its extracted text",
        "NX": "fetched; no extractable text", "W": "DB-0 search summary (encyclopedia; not evidence)",
        "N": "DB-0 search summary (never opened)",
        "A5": "Ariane 5 User's Manual Issue 5 Rev 2 (2016) p.1-7 EPC table and p.A4-2",
        "A5H": "Ariane 5 User's Manual Issue 5 Rev 2 (2016) p.1-7 ESC-A table and p.A4-3",
        "CN": "cnes.fr/projets/ariane-5/lanceur, stage sections (fetched 2026-10-29; the old CNES URL redirects here)",
        "VUG": "ULA Vulcan Launch Systems User's Guide (October 2023) p.1-4 Table 1.4-1",
        "B102": "ESA Bulletin 102 (May 2000) p.2 Table 1 'Technical characteristics of the Vulcain-2 cryogenic engine' and text",
        "B123": "ESA Bulletin 123 (August 2005) p.18 'The Vulcain-2 main engine' / p.19 ESC-A section",
        "SP45R": "NASA SP-45 Mercury Project Summary (1963) PDF p.88 Figure 4-13 'Mercury-Redstone configuration' and p.83",
        "SP45A": "NASA SP-45 Mercury Project Summary (1963) PDF p.94-97, Atlas propulsion system text",
        "EPS": "esa.int Ariane 5 Storable Propellant Stage (EPS) page text (fetched 2026-10-29)",
        "KB": "kbkha.ru engine page, 'Характеристики' block (fetched 2026-10-29)",
        "JD": "深空探测学报 2021 8(4) p.4 (PDF p.4) 表 3, full text via the journal's PDF preview link",
        "PUG53": "Firefly Alpha Payload User's Guide 5.3 (2026-09) p.6 vehicle overview",
        "K11": "한국추진공학회지 15(6) (2011) p.2 section 2.1 '주요 규격'",
        "PX8": "NTRS 20080034655 (Grover and Cichy, JPL, 'Overview of the Phoenix EDL System Architecture', AIAA 2008) p.2",
        "PX4": "NTRS 20070014659 (Phoenix EDL presentation, 2nd IPPW, August 2004) slide 10 'Phoenix Terminal Descent Phase'",
        "JPK": "NASA Juno Launch press kit (2011) p.15 'Propulsion System'",
        "NH95": "NASA History article (2021-03-17), body text",
        "UM21": "CALT user's manual chapter 2, Table 2-1 'Technical Parameters' p.2-2",
        "AUG": "Antares OSP-3 User's Guide Release 1.1 (2013) section 2.2.1 'Main Engine System' (mirror page 15)",
        "EA6": "esa.int 'The engines of Ariane 6' (05/06/2024), Vulcain 2.1 characteristics box",
        "WBT": "en.wikipedia.org BT-4 (rocket engine), current revision fetched 2026-10-29: infobox and 'Known variations' list",
        "JZ6": "jzyjspace.com products_list/6.html, Longyun product text (fetched 2026-10-29)",
        "AGP": "agnikul.in/product, Agnibaan 'Base Shroud' panel (fetched 2026-10-29)",
        "VO1": "LauncherOne Service Guide v2.1 (Aug 2020), section 1.4 figure, PDF p.10 (archive capture 2021-05-07)",
        "VO2": "virginorbit.com/technology, LauncherOne panel (archive capture 2021-01-17)",
        "SX18": "spacex.com/falcon9, Merlin Vacuum panel (archive capture 2018-02-08)",
        "SXU2": "Falcon 9 Payload User's Guide Rev 2 (2015-10-21), PDF p.11 text and table (archive capture 2017-03-14)",
        "MX16": "twitter.com/elonmusk status 728753234811060224, 2016-05-06 (archive capture 2017-02-05)",
        "BOU": "Blue Origin release 2025-11-20 on upgraded New Glenn engines (archive capture 2025-12-05)",
        "BOE": "blueorigin.com/engines, engine panels (archive capture 2026-07-14)",
        "NV2A": "NASM record A19600013000, description (archive capture 2025-04-05)",
        "NSS": "NASM record A19700331000 (Super Sprite), description (archive capture 2025-04-05)",
        "G17": "NTRS 20170001286 (Masse et al., GR-1/GR-22 advancements) p.2, section II",
        "R69": "NTRS 19690029231 (Apollo SM-LM RCS engine development program summary, vol. 1, 1969) PDF p.10 and p.125"}


def K(db0_id, engine_id, field_path, claims, resolution, kind, explanation):
    C("CF-DB05-W-" + db0_id.replace("CF-", ""), engine_id=engine_id, field_path=field_path, db0_conflict_id=db0_id,
      claims=[[t, s, _LOC[k]] for t, s, k in claims], resolution=resolution, kind=kind, explanation=explanation)


# --- US classic and historic
C("CF-DB05-W-R2_US_CLASSIC-RS-3", engine_id="ENG-US-SSME-BLOCK-II", field_path="propellants.mixture_ratio",
  db0_conflict_id="CF-R2_US_CLASSIC-RS-3",
  claims=[["6.03:1", "SRC-L3HARRIS-RS25-SPEC", "p.1 'Mixture Ratio Oxidizer/Fuel' (read in the RS-25 pass)"],
          ["Mixture Ratio (O/F): 6.0", "SRC-L3HARRIS-RS25-WEB", "specification box (read in the RS-25 pass)"]],
  resolution="EXPLAINED", kind="rating_or_rounding",
  explanation="Both are the manufacturer's: the specification sheet prints 6.03:1 and the web page 6.0, the same ratio "
              "to one decimal.")
K("CF-R2_US_CLASSIC-LR-2", "ENG-US-LR87-AJ-5", "identity.engine_count",
  [("twin motors considered a single unit", "SRC-WIKI-LR87", "W"), ("only fireable as a unit", "SRC-WIKITALK-LR87", "W"),
   ("one engine assembly, two chambers, two TPAs", "SRC-TMS-TITAN2", "T")],
  "EXPLAINED", "definition",
  "A counting convention, not a factual conflict: every claim describes one assembly of two thrust chambers, each with its "
  "own turbopump. The DB-0.5 record counts one engine with two chambers.")
K("CF-US_HIST-06", "ENG-US-BELL-8096", "identity.designation / performance.isp_vac",
  [("XLR81-BA-11; Isp 280 s", "SRC-WIKI-BELL8000", "W"), ("XLR81-BA-9 = Model 8096", "SRC-DESIGNSYS-RM81", "T"),
   ("71.2 kN, 291 s", "SRC-ASTRONAUTIX-AGENAB", "NF")],
  "PARTIALLY_RESOLVED", "different_variant",
  "Two pages agree that the Bell 8096 is the XLR81-BA-9 (Astronautica: 'Later models used a further improved XLR81-BA-9 "
  "(Bell Model 8096)'); the BA-11 attribution is the encyclopedia's alone. The Agena B page does not print 71.2 kN or "
  "291 s: its stage table gives 71.17 kN and 285 s for the Bell 8081 stage. No opened page gives an 8096 Isp.")
K("CF-US_HIST-07", "ENG-US-BELL-8081", "performance.thrust",
  [("71 kN (16,000 lbf)", "SRC-WIKI-BELL8000", "W"), ("70.7 kN (15,890 lbf)", "SRC-ASTRONAUTIX-AGENAB", "NF")],
  "PARTIALLY_RESOLVED", "rating_or_rounding",
  "The Agena B page prints 'Thrust 71.17 kN (15,999 lbf)' for the stage with the Bell 8081, not the 70.7 kN DB-0 cited; "
  "71.17 kN rounds to the encyclopedia's 71 kN. Both are tertiary.")
K("CF-US_HIST-08", "ENG-US-XLR11", "identity.designation",
  [("X-1 = XLR11-RM-5", "SRC-WIKI-XLR11", "W"), ("5,900 lbf; 345 lb incl. turbopump", "SRC-NMUSAF-XLR11", "N"),
   ("X-1 engine XLR-11-RM3", "SRC-HISTORYOFWAR-X1", "T")],
  "UNRESOLVED", "different_variant",
  "Opened: one popular history page names the X-1 engine XLR-11-RM3. The RM-5 and the thrust and mass figures were not "
  "opened. Different X-1 airframes may have carried different sub-variants; no document says which.")
K("CF-US_HIST-11", "ENG-US-LR79-NA-9", "applications",
  [("Thor IRBM and Atlas E and F", "SRC-FLICKR-MB3", "T"), ("Atlas E/F used MA-3 (LR89/LR105)", "SRC-ENGINEHISTORY-RPE05", "T")],
  "EXPLAINED", "definition",
  "The museum placard says the MB-3 was designed for Thor and Atlas E and F; the AEHS page says Atlas E and F flew the "
  "MA-3 system. Both can hold: the MA-3 boosters (LR89-NA-5) were derived from the same family. The placard's wording is "
  "about lineage, not the engine installed on Atlas E/F.")
K("CF-US_HIST-13", "ENG-US-NAA-75-110-A-6", "performance.thrust",
  [("91,350 lbf max", "SRC-WIKI-JUPITERA", "W"), ("series final 78,000 lb", "SRC-NASA-MSFC-MERCREDSTONE", "T"),
   ("Model A-7 engine / Thrust: 78,000 lb (Mercury-Redstone); 'Since the A-7 engine was new, extensive test firings were made'",
    "SRC-DB05-NTRS-19630012071", "SP45R")],
  "PARTIALLY_RESOLVED", "different_variant",
  "The MSFC page gives 78,000 lb as the final Redstone A-series figure and names the A-7 on Mercury-Redstone; NASA "
  "SP-45 (1963) prints 'Model A-7 engine, Thrust 78,000 lb' in its configuration figure. So 78,000 lb is the A-7 "
  "rating, not a competing A-6 value. The A-6's 91,350 lbf (a Jupiter-A summary, never opened; possibly a hydyne "
  "rating) still has no document.")
K("CF-US_HIST-15", "ENG-US-LR89-NA-7", "identity.designation / performance.thrust",
  [("MA-5 booster = LR89-5, 163,211 lbf SL", "SRC-ENGINEHISTORY-RPE05", "T"), ("LR89-7, 213,118 lbf vac", "SRC-ASTRONAUTIX-LR89-7", "T"),
   ("pair 1,896 kN", "SRC-WIKI-MA5", "W"), ("pair 1,901.6 kN", "SRC-WIKI-ATLASG", "W")],
  "EXPLAINED", "different_variant",
  "The opened pages describe two engines: the LR89-5 (163,211 lbf SL) and the LR89-7 (213,118 lbf vac). The figures are "
  "for different models and conditions, not two readings of one rating.")
K("CF-US_HIST-17", "ENG-US-XRS-2200", "performance.thrust_vac / performance.thrust_sl",
  [("266,000 / 204,000 lbf", "SRC-WIKI-XRS2200", "W"), ("261,200 / 206,200 lbf", "SRC-PURDUE-XRS2200", "T"),
   ("200,000+ lbs SL", "SRC-NTRS-19980174934", "T")],
  "PARTIALLY_RESOLVED", "rating_or_rounding",
  "The NASA paper gives only '200,000+ lbs' at sea level, consistent with both pairs; Purdue's 261,200 / 206,200 lbf has "
  "no cited source. No opened primary gives the rated pair.")
K("CF-US_HIST-21", "ENG-US-GODDARD-1926-LIQUID-ROCKET-MOTOR", "history.first_flight",
  [("16 March 1926", "SRC-APS-GODDARD", "NF"),
   ("On March 16, 1926, he set up his rocket ... fueled with gasoline and liquid oxygen, on a farm in Auburn, Massachusetts",
    "SRC-DB05-NASA-GODDARD-95", "NH95")],
  "CONFIRMED_SECONDARY", None,
  "The APS page fetched has no date in its text. NASA's history article prints 16 March 1926; DB-0's 18 March came from "
  "an unrecorded page and has no opened source. NASA's article is a retrospective, not Goddard's own record, so the "
  "date stands at Tier B.")
K("CF-US_HIST-24", "ENG-US-LR101", "performance.thrust",
  [("1,017 lbf tank-fed / 1,060 lbf pressure-fed", "SRC-WIKI-LR101", "W"), ("830 lb tank-fed downrated to 525 lb", "SRC-DTIC-AD0423340", "N"),
   ("~1,012 lb per vernier (RS-27A)", "SRC-PURDUE-RS27A", "T"),
   ("one sustainer engine having 57,000 pounds of thrust and two vernier engines having 1,000 pounds of thrust each "
    "(Mercury-Atlas, 1963)", "SRC-DB05-NTRS-19630012071", "SP45A")],
  "PARTIALLY_RESOLVED", "different_variant",
  "Purdue's 1,012 lb is for the RS-27A vernier on Delta II, a later application. The DTIC report was not fetched. Each "
  "figure belongs to a different installation; none is shown to be the LR101 rating. NASA SP-45 (1963) gives the "
  "Mercury-Atlas (Atlas D) verniers 1,000 lb each, a round figure consistent with the 1,017 lbf tank-fed value; the "
  "830/525 lb history and the 1,060 lbf pressure-fed figure still have no opened document.")

# --- USSR / Russia
K("CF-R2_USSR-R2-5", "ENG-SU-NK-33", "aliases.index",
  [("14D15", "SRC-NAKEDSCI-NK33", "T"), ("14D15", "SRC-WIKI-NK33", "W")],
  "CONFIRMED_SECONDARY", None, "The opened news page prints the same index; no primary seen.")
K("CF-R2_USSR-R2-7", "ENG-RU-RD-0124", "control.gimbal",
  [("engine gimballed in two planes", "SRC-RSW-RD0124", "T"), ("each of 4 chambers gimbals on a single axis", "SRC-WIKI-RD0124", "W")],
  "EXPLAINED", "definition",
  "Both can hold: four chambers each swivelling in one plane give the engine control in two planes. The opened page "
  "speaks of the engine, the encyclopedia of the chambers.")
K("CF-R2_USSR-R2-8", "ENG-RU-RD-0124", "dimensions",
  [("2,327 x 1,470 mm, roughly the same as RD-0110 (design intent)", "SRC-RSW-RD0124", "T")],
  "EXPLAINED", "different_epoch",
  "The opened page states the dimensions as the design goal of fitting the RD-0110 envelope; they are not measured "
  "dimensions of the built engine.")
K("CF-R2_USSR-R2-9", "ENG-DE-A4-ENGINE", "propellants.h2o2_concentration",
  [("85 %; Ca/K/Na permanganate", "SRC-ENGINEHISTORY-RPE02-2", "T"), ("80 % test strength", "SRC-V2ROCKETHISTORY", "N"),
   ("Z-Stoff, a catalyst consisting of a 27% solution of sodium permanganate", "SRC-NASM-A19600013000", "NV2A")],
  "UNRESOLVED", None,
  "The AEHS page gives 85 %; the Smithsonian V-2 record (read 2026-10-29 from an archive capture) confirms the 27 % "
  "sodium permanganate Z-Stoff but gives no peroxide concentration. The 80 % page sits behind a bot check and was not "
  "read.")
K("CF-R2_USSR-R2-16", "ENG-RU-S5-92", "performance.isp_vac / operations.starts",
  [("Restart capability up to 20", "SRC-STARSEM-ST07", "T"), ("50 starts; 327 / 316 s", "SRC-WIKI-S592", "W"),
   ("323 / 329 s; 1,400 / 2,000 kg", "SRC-RSW-FREGAT", "T")],
  "PARTIALLY_RESOLVED", "different_operating_point",
  "Starsem's user manual gives up to 20 restarts; the 50 is encyclopedia-only. The two Isp pairs are tied to the engine's "
  "two thrust modes, but the opened RussianSpaceWeb page does not say which mode each Isp belongs to.")
K("CF-R2_USSR-R2-20", "ENG-RU-11D58MF", "cycle",
  [("'oxidizer gas generator' drives TPA", "SRC-SSAU-2587", "NF"), ("ox-rich staged combustion", "SRC-WIKI-RD58", "W")],
  "UNRESOLVED", None, "The SSAU page's text did not contain the wording DB-0 cited; nothing settles the cycle.")
K("CF-R2_USSR-R2-21", "ENG-RU-KVD-1", "history.development_period",
  [("11D56 development 1965-1972", "SRC-WIKI-KVD1", "W"), ("KVD-1 (RD56) 1962-1974", "SRC-LPRE-NPOEM-RD0120UP", "T")],
  "UNRESOLVED", "definition",
  "The opened paper gives 1962-1974; the encyclopedia's 1965-1972 was not opened. The spans may count different phases "
  "(programme against engine development); neither says. The thrust part of the DB-0 conflict was not reached.")
K("CF-USSR-5", "ENG-RU-RD-191", "performance.isp_sl",
  [("310.7 s", "SRC-WIKI-RD191", "W"), ("311.2 s", "SRC-RSW-RD191", "T"), ("311 s (RD-181)", "SRC-GLAVKOSMOS-RD181", "T")],
  "UNRESOLVED", "rating_or_rounding",
  "0.2 percent apart. The Glavkosmos figure is for the RD-181, a variant. No manufacturer RD-191 table was opened.")
K("CF-USSR-6", "ENG-RU-RD-0124MS", "performance.isp_vac",
  [("359 s", "SRC-WIKI-SOYUZ5", "W"), ("361 s", "SRC-WWW1-RD0124", "T"), ("361 s ('RD-124MV')", "SRC-FRONTIER-SOYUZ5", "NF"),
   ("РД0124МС: тяга в пустоте 60,34 тс; удельный импульс тяги в пустоте 361 с; давление в КС 155 кг/см2", "SRC-DB05-KBKHA-RD0124MS", "KB"),
   ("РД0124: тяга в пустоте 30 тс; удельный импульс тяги 359 с; давление в КС 160 кг/см2", "SRC-DB05-KBKHA-RD0124", "KB")],
  "RESOLVED", "different_variant",
  "The manufacturer's pages settle it: KBKhA prints 361 s for the RD0124MS (60.34 tf, the Soyuz-5 second-stage engine) "
  "and 359 s for the RD0124 (14D23, 30 tf, Soyuz-2.1b third stage). 361 s is the RD-0124MS value; 359 s is the parent "
  "engine's, attached to the wrong variant in the encyclopedia summary.")
K("CF-USSR-7", "ENG-SU-RD-117", "aliases.index",
  [("RD-117 = 11D511; RD-118 = 11D512", "SRC-WIKI-RD107", "W"), ("11D511 'RD-107'; 11D512 'RD-108'", "SRC-GLOBALSEC-SOYUZU", "T")],
  "EXPLAINED", "definition",
  "GlobalSecurity attaches the family names RD-107 / RD-108 to the 11D511 / 11D512 indices used on Soyuz-U, which are "
  "the RD-117 / RD-118 builds; both pages name the same hardware at different levels of the family.")
K("CF-USSR-8", "ENG-SU-RD-100", "performance.thrust_sl",
  [("26 t", "SRC-KPI-GLUSHKO", "T"), ("33 t (+30 % over V-2)", "SRC-HISTORYRISE-GLUSHKO", "N")],
  "UNRESOLVED", None, "Only the 26 t page was opened; 33 t stays a search-result claim.")
K("CF-USSR-9", "ENG-SU-RD-101", "performance.thrust",
  [("37,210 kgf SL / 41,208 kgf vac", "SRC-FAS-R2", "T"), ("37 t (ground)", "SRC-KPI-GLUSHKO", "T"), ("35 t (340 kN)", "SRC-PLANETARY-GLUSHKO", "T")],
  "PARTIALLY_RESOLVED", "rating_or_rounding",
  "FAS (37,210 kgf) and KPI (37 t) agree; the Planetary Society's 35 t is 6 percent lower and gives no source or "
  "condition.")
K("CF-USSR-10", "ENG-SU-RD-101", "propellants.fuel",
  [("methyl alcohol replaced ethyl alcohol", "SRC-FAS-R2", "T")],
  "UNRESOLVED", None, "Only the FAS page was read; no second opened source confirms or contradicts the change.")
K("CF-USSR-15", "ENG-SU-RD-0110", "performance.pc / performance.isp_vac / operations.burn_time",
  [("6.8 MPa; 325 s; 250 s", "SRC-WIKI-RD0110", "W"), ("7 MPa; 3,195 m/s; 'Burn time 230 or 240 seconds'", "SRC-RSW-RD0110", "T")],
  "PARTIALLY_RESOLVED", "rating_or_rounding",
  "3,195 m/s is 325.8 s DERIVED, the encyclopedia's 325 s; 7 MPa against 6.8 MPa is rounding. The burn time stays open: "
  "the opened page itself gives two values (230 or 240 s), neither 250 s.")
K("CF-USSR-16", "ENG-SU-RD-0210", "performance.thrust_vac / performance.pc / operations.burn_time",
  [("582 kN; 14.7 MPa; 220 s", "SRC-WIKI-RD0210", "W"), ("593.6 kN; 15 MPa; 230 s", "SRC-RSW-RD0210", "T"),
   ("тяга в пустоте (одного двигателя) 59,36 тс; удельный импульс 326,5 с; давление в КС 150 кг/см2", "SRC-DB05-KBKHA-RD0210", "KB")],
  "PARTIALLY_RESOLVED", "different_variant",
  "Each figure differs by 2-5 percent. The manufacturer's Proton-K second-stage page prints 59.36 tf per engine "
  "(582.1 kN DERIVED) and 150 kgf/cm2 (14.7 MPa DERIVED), matching the 582 kN / 14.7 MPa set; 593.6 kN and 15 MPa have "
  "no document. KBKhA prints no burn time, so 220 against 230 s stays open.")
K("CF-USSR-18", "ENG-RU-RD-171MV", "performance.thrust",
  [("7,887 kN vac (family)", "SRC-WIKI-RD170", "W"), ("7,257 kN SL (stage 1)", "SRC-WIKI-SOYUZ5", "W"),
   ("'approximately 800 tons'", "SRC-FRONTIER-SOYUZ5", "T")],
  "UNRESOLVED", "different_variant",
  "The opened page gives only 'approximately 800 tons' without a condition; the other figures are encyclopedia values for "
  "the family or the stage.")
K("CF-ANCHOR_USSR-2", "ENG-SU-RD-170", "performance.pc",
  [("266.7 bar", "SRC-NAKEDSCI-RAPTOR", "NF"), ("> 280 bar (10 % margin)", "SRC-SNOB-172276", "T")],
  "EXPLAINED", "definition",
  "Not two ratings: the '> 280 bar' is an Energomash claim of a 10 percent certification margin, as in "
  "CF-DB05-RD180-PC. The 266.7 bar is not in the Naked Science text that was fetched.")

# --- Asia
K("CF-R2_ASIA-R2A-5", "ENG-JP-LE-9", "pumps.speed_rpm",
  [("41,600 rpm (pump not legible)", "SRC-IHI-GIHO-LE9-TP", "NX"), ("LH2 turbopump 41,600 rpm", "SRC-IHIFAN-LE9", "T")],
  "PARTIALLY_RESOLVED", "definition",
  "The IHI fan page attaches 41,600 rpm to the LH2 turbopump; the IHI technical review's own pump label could not be "
  "read. The value is not settled from a primary.")
K("CF-R2_ASIA-R2A-6", "ENG-JP-LE-5B", "performance.throttle_range",
  [("3 % (turbine not driven)", "SRC-WEBLIO-LE5", "T"), ("5 % idle mode", "SRC-WIKI-LE5", "W"), ("3 % tank head (LE-5B-2 table)", "SRC-WIKI-LE5", "W")],
  "EXPLAINED", "definition",
  "Two modes: the 3 % tank-head idle without turbine drive, and a 5 % idle mode. The opened mirror and the encyclopedia "
  "describe different low-thrust modes, not one value.")
K("CF-R2_ASIA-R2A-7", "ENG-JP-LE-5B", "performance.thrust_vac",
  [("LE-5B 137.2 kN", "SRC-WEBLIO-LE5", "T"), ("LE-5B-3 137 kN", "SRC-WIKI-LE5", "W")],
  "EXPLAINED", "rating_or_rounding", "137 kN is 137.2 kN rounded; the variant labels differ, not the value.")
K("CF-ASIA_OTHER-5", "ENG-JP-LE-5B-3", "performance.thrust_vac",
  [("137 kN", "SRC-WIKI-LE5", "W"), ("14 ton", "SRC-MHI-LE5B", "T")],
  "EXPLAINED", "rating_or_rounding", "14 tf is 137.3 kN DERIVED; the manufacturer's figure is the encyclopedia's rounded.")
K("CF-R2_ASIA-R2A-9", "ENG-IN-VIKAS", "performance.pc",
  [("52.5 -> 58.5 bar (2001)", "SRC-SPACENEWS-33640", "T"), ("6.2 MPa", "SRC-WIKI-VIKAS", "W")],
  "EXPLAINED", "different_epoch",
  "SpaceNews reports the 2001 uprate from 52.5 to 58.5 bar; 6.2 MPa is a later figure from the encyclopedia. The "
  "values are different builds, not one.")
K("CF-R2_ASIA-R2A-10", "ENG-IN-CE-7-5", "performance.pc",
  [("5.8 MPa / 7.5 MPa", "SRC-WIKI-CE75", "W"), ("58 bar nominal", "SRC-SLIDESHARE-CRYO", "T")],
  "PARTIALLY_RESOLVED", "different_operating_point",
  "The slide deck's 58 bar is the encyclopedia's 5.8 MPa; the 7.5 MPa has no opened source. Which station or operating "
  "point each refers to is not stated.")
K("CF-R2_ASIA-R2A-12", "ENG-IN-CE-20", "performance.thrust_vac",
  [("186.36 kN", "SRC-WIKI-CE20", "W"), ("200 kN", "SRC-WIKI-CE20", "W"), ("19-20 t nominal, 22 t uprated", "SRC-IASGYAN-CE20", "T")],
  "EXPLAINED", "different_epoch",
  "The opened page separates the nominal 19-20 t (186-196 kN DERIVED) from a 22 t uprate; the encyclopedia figures sit "
  "in that range. Tertiary only.")
K("CF-R2_ASIA-R2A-14", "ENG-CN-YF-100", "performance.throttle_range",
  [("65-105 %", "SRC-WIKI-YF100", "W"), ("65-100 %", "SRC-BILI-CV15113396", "NX")],
  "UNRESOLVED", None, "The Bilibili article delivered no text. The developing institute's 2021 paper (full text read "
  "2026-10-29) states only 大范围推力和混合比调节 ('wide-range thrust and mixture-ratio regulation'), with no range.")
K("CF-R2_ASIA-R2A-15", "ENG-CN-YF-100", "performance.thrust_sl",
  [("1,200 kN", "SRC-WIKI-YF100", "W"), ("1,188 kN", "SRC-BILI-CV15113396", "NX"),
   ("表 3 国内外液氧煤油发动机性能对比: YF-100 / 新一代运载火箭 / 补燃循环 / 地面推力 1 200 kN / 地面比冲 2 942 m/s",
    "SRC-DB05-JDSE-2021-YF100", "JD")],
  "RESOLVED", "primary_value_found",
  "The Bilibili article delivered no text. The developing institute's own 2021 paper (Xi'an Aerospace Propulsion "
  "Institute, Journal of Deep Space Exploration 8(4), full text read 2026-10-29) prints 地面推力 (sea-level thrust) 1 200 kN "
  "in its Table 3, matching the IAC-15 abstract's '1200kN engine'. 1 188 kN has no opened document.")
K("CF-R2_ASIA-R2A-16", "ENG-KR-KRE-075", "performance.pc",
  [("7.0 MPa", "SRC-WIKI-KRE075", "W"), ("60 bars", "SRC-FRWIKI-KRE075", "W"), ("60 bar (design stage, 2009)", "SRC-KSCI-KARI-2009-KRE75", "T"),
   ("연소기 압력 : 60 bar (2011 specification)", "SRC-DB05-KSPE-2011-KRE75", "K11")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "The 2009 KARI paper gives 60 bar at the design stage; 7.0 MPa is unsourced and may be a later build. No later KARI "
  "document was opened.")
K("CF-R2_ASIA-R2A-17", "ENG-KR-KRE-075", "performance.thrust_vac",
  [("735.5 kN (stage 1)", "SRC-WIKI-KRE075", "W"), ("75.8 tonf (SL type)", "SRC-NAMU-KRE075", "NF"),
   ("74.8 ton (design, 2009)", "SRC-KSCI-KARI-2009-KRE75", "T"),
   ("주요 규격: 진공 추력 75 tf; 진공 비추력 297 sec; 연소기 압력 60 bar (2011)", "SRC-DB05-KSPE-2011-KRE75", "K11")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "KARI's 2011 test-range paper lists the engine's main specification as 75 tf vacuum (735.5 kN DERIVED, exactly the "
  "encyclopedia's figure), 297 s and 60 bar; the 2009 combustor design paper gave 74.8 t. So 735.5 kN is KARI's 2011 "
  "specification. The 75.8 tf (sea-level-type, user-edited wiki) and the flown Nuri rating have no opened document.")
K("CF-R2_ASIA-R2A-21", "ENG-IN-LAM-440-N", "propellants.roles",
  [("MMH fuel / MON-3 oxidizer", "SRC-IAC16-32550", "T"), ("MON 'fuel', UDMH 'oxidizer'", "SRC-SF101-LAM", "N")],
  "RESOLVED", "primary_value_found",
  "The ISRO authors' IAC abstract: 'The propellant combination employed is MON-3 & MMH at a mixture ratio of 1.6'. The "
  "swapped roles were never opened and reverse fuel and oxidizer.")
K("CF-R2_ASIA-R2A-22", "ENG-IN-AGNILET", "performance.thrust",
  [("approximately 3 kN at sea level", "SRC-IE-AGNIBAAN", "T"), ("6.2 kN", "SRC-M3D-AGNIKUL-2026", "T"),
   ("Agnilet, that can propel the vehicle with its 6.2kN thrust capacity", "SRC-DB05-AGNIKUL-PRODUCT", "AGP")],
  "PARTIALLY_RESOLVED", "different_variant",
  "The maker's Agnibaan page gives Agnilet a 6.2 kN thrust capacity, the 2026 figure. The 2024 news page's 'approximately "
  "3 kN at sea level' has no maker document; whether it is an earlier build or another condition is not stated.")
K("CF-R2_ASIA-R2A-23", "ENG-IN-DHAWAN-1", "performance.thrust",
  [("1.5 kN vac", "SRC-CHANAKYA-DHAWAN1", "N"), ("1.0 kN", "SRC-COLDFACTS-DHAWAN1", "NF")],
  "UNRESOLVED", None, "The fetched page gives no thrust; nothing opened settles it.")
K("CF-R2_ASIA-R2A-24", "ENG-RU-RD-151", "identity.designation",
  [("RD-191", "SRC-WIKI-NARO1", "W"), ("RD-151", "SRC-SPACENEWS-12177", "T"), ("RD-151", "SRC-SFN-KSLV-2010", "T")],
  "EXPLAINED", "different_variant",
  "Two opened news pages name the KSLV first-stage engine RD-151, a derated RD-191; the encyclopedia names the parent "
  "engine.")
K("CF-R2_ASIA-R2A-28", "ENG-CN-WELKIN", "performance.thrust_sl",
  [("CQ-50 Reusable LOX/Kerosene Engine: 500kN Thrust at Sea Level; 265s Specific Impulse at Sea Level", "SRC-GE-WELKIN-EN", "T"),
   ("400 kN", "SRC-WIKI-WELKIN", "W")],
  "RESOLVED", "primary_value_found",
  "DB-0 read the maker's page as '50 t'. The page itself (fetched 2026-10-28) prints 500 kN at sea level for the CQ-50 "
  "(苍穹50, 'Welkin') engine; the Chinese page gives the same. The encyclopedia's 400 kN has no maker support.")
K("CF-R2_ASIA-R2A-30", "ENG-CN-LONGYUN", "performance.thrust",
  [("70 t class", "SRC-36KR-JZYJ", "T"), ("80 t class", "SRC-JIEMIAN-14422448", "T"),
   ("“龙云”发动机的海平面推重比＞80，海平面推力70吨，真空版推力80吨，推力调节范围32%~106%", "SRC-DB05-JZYJ-LONGYUN", "JZ6")],
  "EXPLAINED", "different_variant",
  "The maker's product page prints both figures: 70 t sea-level thrust and 80 t for the vacuum version. The two news "
  "pages each quote one of them; no conflict remains.")
K("CF-ASIA_OTHER-7", "ENG-CN-YF-23", "performance.thrust_vac",
  [("47.1 kN", "SRC-WIKI-YF23", "W"), ("46.1 kN", "SRC-GS-CZ2D", "T"),
   ("LM-3C Table 2-1: DaFY21-1(Vernier) Thrust (kN) 11.8x4; Specific Impulse 2910.5 N.s/kg", "SRC-DB05-CALT-LM3C-UM-1998", "UM21"),
   ("LM-2E Table 2-1: DaFY21-1(verniers) Thrust (kN) 11.8x4; Specific Impulse 2834.11 N.s/kg (in vacuum)", "SRC-DB05-CALT-LM2E-UM-1999", "UM21")],
  "PARTIALLY_RESOLVED", "different_variant",
  "Not a transcription slip. The GlobalSecurity CZ-2D table pairs its 46.1 kN vernier figure with 2762 N.s/kg and calls "
  "the stage-2 verniers 'four YF-23 verniers'; CALT's own LM-3C (1998) and LM-2E (1999) manuals give the four "
  "DaFY21-1 verniers 11.8 kN each, 47.2 kN DERIVED, at 2910.5 and 2834.11 N.s/kg. The vernier rating differs between "
  "vehicles and manuals; the encyclopedia's 47.1 kN is close to CALT's 47.2. No document opened gives the CZ-2D "
  "figure from its own maker (SAST), or prints YF-23 and DaFY21-1 as the same unit.")
K("CF-ASIA_OTHER-8", "ENG-CN-YF-40", "performance.thrust_vac",
  [("103 kN", "SRC-WIKI-YF40", "W"), ("100.85 kN (stage, two YF-40)", "SRC-WIKI-CZ4B", "W"),
   ("just over 100 kN each engine (YF-40A)", "SRC-EDA-CZ4C", "T")],
  "UNRESOLVED", "different_variant",
  "The opened page puts 'just over 100 kN' on each YF-40A; the CZ-4B summary's 100.85 kN is for two engines. Variant "
  "and per-engine scope are mixed; not settled.")
K("CF-ASIA_OTHER-10", "ENG-CN-YF-75D", "performance.thrust_vac",
  [("88.36 kN, 442.6 s, 780 s", "SRC-WIKI-YF75D", "W"), ("88.26 kN, 442 s, 470 s", "SRC-WEBLIO-YF75D", "T")],
  "UNRESOLVED", "rating_or_rounding",
  "Two encyclopedia renderings (the opened page mirrors Japanese Wikipedia). Thrust and Isp agree within 0.1 percent; the "
  "burn time (470 against 780 s) does not, and neither cites a primary.")
K("CF-ASIA_OTHER-11", "ENG-CN-YF-77", "performance.isp",
  [("430 s vac / 310.2 s SL", "SRC-WIKI-YF77", "W"), ("438 s vac / 333 s SL", "SRC-WEBLIO-YF77", "T")],
  "UNRESOLVED", None, "Two encyclopedia renderings (English and Japanese) disagree; no primary opened.")
K("CF-ASIA_OTHER-12", "ENG-CN-YF-115", "performance.thrust_vac",
  [("17,850 kgf (175.0 kN)", "SRC-SF101-CZ6", "N"), ("176.5 kN", "SRC-WIKI-YF115", "W"), ("'180 kN' class (title)", "SRC-IAC16-YF115", "NX")],
  "UNRESOLVED", "rating_or_rounding", "The IAC abstract delivered no text; '180 kN' is a class name in its title.")
K("CF-ASIA_OTHER-13", "ENG-CN-TQ-12", "performance.isp_vac",
  [("337 s (sea-level nozzle)", "SRC-WIKI-TQ12", "W"), ("vacuum Isp 350 s; area ratio 40", "SRC-NCSTI-2023-TQ", "T")],
  "UNRESOLVED", "different_variant",
  "The exhibition text gives 350 s with area ratio 40 for 'TQ-12'; whether that is the flown sea-level engine or a "
  "vacuum-optimised build is not stated.")
K("CF-ASIA_OTHER-14", "ENG-CN-TQ-15A", "performance.throttle_range",
  [("design range 60-100 %; +11.8 % thrust; +126 m/s", "SRC-BJNEWS-TQ15A", "T"), ("55-110 %; +9 %; +130 m/s", "SRC-JIEMIAN-TQ", "NF")],
  "PARTIALLY_RESOLVED", "different_variant",
  "The Beijing News text gives 60-100 % for the TQ-15A. The Jiemian article does not print 55-110 %: it gives '45%-111%' "
  "for an improved TQ-12 on a test vehicle, another engine.")
K("CF-ASIA_OTHER-15", "ENG-CN-TH-12", "performance.thrust_sl",
  [("95 t", "SRC-SPACEPIONEER-TH12", "T"), ("1,090 kN (111 t)", "SRC-WIKI-TH12", "W"), ("110 t design", "SRC-ITHOME-655315", "T")],
  "EXPLAINED", "different_variant",
  "The manufacturer's TH-12 page gives 95 t at sea level and its TH-12V page 110 t in vacuum; the 110 t of the news "
  "headline matches the vacuum figure, not a sea-level rating.")
K("CF-ASIA_OTHER-16", "ENG-CN-TH-12", "cycle",
  [("oxidizer-rich gas generator", "SRC-WIKI-TH12", "W"), ("'Cycle Gas generator'", "SRC-SPACEPIONEER-TH12V", "T")],
  "PARTIALLY_RESOLVED", "definition",
  "The manufacturer prints 'gas generator' without 'oxidizer-rich'; the mixture of the generator is not stated anywhere opened.")

# --- Europe
K("CF-R2_ASIA-R2A-20", "ENG-FR-VULCAIN-2", "flows.mdot",
  [("235 kg/s total, 41.2 kg/s H2", "SRC-WIKI-VULCAIN", "W"), ("H2 33 kg/s, LOX 202 kg/s", "SRC-HF-SPACEYL-ENGINES", "T"),
   ("Total propellant flow 320 kg/s; nominal hydrogen flow of 44.9 kg/s", "SRC-DB05-ESA-BULLETIN-102-VULCAIN2", "B102")],
  "PARTIALLY_RESOLVED", "different_variant",
  "ESA's 2000 Vulcain-2 table prints 320 kg/s total and the text a nominal 44.9 kg/s hydrogen flow. Neither the 235 kg/s "
  "nor the 202 + 33 kg/s is a Vulcain 2 figure in it; 235 kg/s and 41.2 kg/s H2 fit the first Vulcain (see "
  "CF-ANCHOR_EU_ASIA-4). A development-era value, not a flight datasheet.")
K("CF-ANCHOR_EU_ASIA-1", "ENG-FR-VULCAIN-2", "performance.thrust_vac",
  [("1,390 kN", "SRC-CNES-A5-TECH", "NX"), ("1,359 kN", "SRC-AIAA-VG-ARIANE", "N"), ("1,359 / 1,340 kN", "SRC-WIKI-VULCAIN", "W"),
   ("~137-138 t", "SRC-ESA-A5ECA-NEWELEM", "N"), ("Vulcain 2's 1,359 kN (305,000 lbf)", "SRC-NEWSPACEECON-V21", "T"),
   ("Thrust 960 kN (SL) 1390 kN (Vacuum); 'develops 1,390 kN maximum thrust in vacuum'", "SRC-DB05-ARIANESPACE-A5UM-I5R2", "A5"),
   ("pour 1 390 kN (139 tonnes) de poussée dans le vide", "SRC-DB05-CNES-A5-LANCEUR", "CN"),
   ("Vacuum thrust 1 350 kN (May 2000 table); 'increases the available thrust from 1145 to 1350 kN'", "SRC-DB05-ESA-BULLETIN-102-VULCAIN2", "B102"),
   ("The new engine provides more thrust - 1350 kN compared with the 1100 kN of Vulcain-1 (August 2005)", "SRC-DB05-ESA-BULLETIN-123-A5ECA", "B123")],
  "PARTIALLY_RESOLVED", "rating_or_rounding",
  "The launch operator's user's manual (Arianespace, 2016) prints 1,390 kN as the Vulcain 2 maximum vacuum thrust, "
  "matching the CNES figure. ESA's May 2000 development table and its August 2005 Ariane-5 ECA article both print "
  "1 350 kN, so the 1 390 kN maximum is a later figure; 1,359 kN appears only in secondary pages and an unopened AIAA guide, and which "
  "epoch it belongs to is not shown. No Safran/ArianeGroup datasheet was reached.")
K("CF-ANCHOR_EU_ASIA-4", "ENG-FR-VULCAIN-2", "flows.mdot_fuel",
  [("41.2 kg/s H2 of 235 kg/s (page titled 'Vulcain engine')", "SRC-ESA-ESAMI-VULCAIN", "NX"), ("33 kg/s H2", "SRC-HF-SPACEYL-ENGINES", "T"),
   ("the nominal operating point of 35680 rpm, 14.29 MW and a hydrogen flow of 44.9 kg/s", "SRC-DB05-ESA-BULLETIN-102-VULCAIN2", "B102")],
  "PARTIALLY_RESOLVED", "different_variant",
  "ESA's 2000 Bulletin gives the Vulcain 2 nominal hydrogen flow as 44.9 kg/s, so neither 41.2 nor 33 kg/s is the "
  "Vulcain 2 value it prints; that supports the DB-0 suspicion that the esaMI page's 41.2 kg/s is the first Vulcain, "
  "though that page gave no text to confirm it.")
K("CF-EUROPE-6", "ENG-FR-VULCAIN-2-1", "performance.thrust_vac",
  [("1,371 kN (308,000 lbf)", "SRC-NEWSPACEECON-V21", "T"), ("1,340 kN", "SRC-METALAM-V21", "NF"), ("135 t vacuum", "SRC-3DPI-V21", "NF"),
   ("Vulcain 2.1 main engine characteristics ... 1371 kN of thrust ... 468 seconds of operation", "SRC-DB05-ESA-A6-ENGINES", "EA6")],
  "RESOLVED", "primary_value_found",
  "ESA's Ariane 6 engines page (2024) prints 1371 kN ('more than 1370 kN' in its text), matching the news page's "
  "1,371 kN. The 1,340 kN and 135 t (1,324 kN DERIVED) are not on their fetched pages; 1,340 kN is Vulcain 2's own "
  "vacuum figure (see CF-DB05-E-EUROPE-3). ESA prints no ambient condition; the vacuum reading follows the news page.")
K("CF-EUROPE-9", "ENG-FR-HM7B", "performance.thrust_vac",
  [("62.2 kN", "SRC-WIKI-HM7B", "W"), ("64.8 kN", "SRC-SATNOW-HM7B", "T"), ("ESC-A table: Thrust 67 kN, Isp 446 s; 'develops 67 kN maximum thrust in vacuum'", "SRC-DB05-ARIANESPACE-A5UM-I5R2", "A5H"),
   ("The HM-7B cryogenic engine provides a thrust of 65 kN in vacuum, with a specific impulse of 447 seconds (2005)", "SRC-DB05-ESA-BULLETIN-123-A5ECA", "B123")],
  "PARTIALLY_RESOLVED", "different_variant",
  "Arianespace's 2016 user's manual prints 67 kN maximum vacuum thrust for the Ariane 5 ESC-A HM7B, so neither 62.2 nor "
  "64.8 kN is the ESC-A maximum. ESA's 2005 Ariane-5 ECA article prints 65 kN at 447 s, so the ESC-A figure itself "
  "moved between 65 and 67 kN across documents. Whether 62.2 kN is an Ariane 4 H10 build is not shown.")
K("CF-ANCHOR_EU_ASIA-5", "ENG-FR-HM7B", "performance.thrust_vac",
  [("67 kN", "SRC-CNES-A5-TECH", "NX"), ("62.2 kN", "SRC-AIAA-VG-ARIANE", "N"), ("64.8 kN", "SRC-SATNOW-HM7B", "T"), ("ESC-A table: Thrust 67 kN, Isp 446 s; 'develops 67 kN maximum thrust in vacuum'", "SRC-DB05-ARIANESPACE-A5UM-I5R2", "A5H"),
   ("pour fournir 67 kN (6,7 tonnes) de poussée dans le vide", "SRC-DB05-CNES-A5-LANCEUR", "CN"),
   ("The HM-7B cryogenic engine provides a thrust of 65 kN in vacuum, with a specific impulse of 447 seconds (2005)", "SRC-DB05-ESA-BULLETIN-123-A5ECA", "B123")],
  "PARTIALLY_RESOLVED", "different_variant",
  "The launch operator's manual prints 67 kN maximum in vacuum for the ESC-A HM7B, as the CNES page was reported to. "
  "The 62.2 and 64.8 kN figures are not explained (see CF-DB05-W-EUROPE-9).")
K("CF-ANCHOR_EU_ASIA-7", "ENG-FR-HM7B", "operations.burn_time",
  [("950 s", "SRC-AIAA-VG-ARIANE", "N"), ("up to 15 min 45 s (945 s)", "SRC-CNES-A5-TECH", "NX"),
   ("ESC-A table: Combustion time 945 s", "SRC-DB05-ARIANESPACE-A5UM-I5R2", "A5H"),
   ("Il fonctionnait jusqu'à 15 minutes et 45 secondes", "SRC-DB05-CNES-A5-LANCEUR", "CN"),
   ("which provides a maximum of 970 seconds of propelled flight (ESC-A stage, 2005)", "SRC-DB05-ESA-BULLETIN-123-A5ECA", "B123")],
  "EXPLAINED", "rating_or_rounding",
  "Arianespace's 2016 user's manual prints 945 s for the ESC-A, matching the CNES figure; the unopened AIAA guide's 950 s "
  "is that value rounded. ESA's 2005 article gives the ESC-A a maximum of 970 s of propelled flight, a capability limit "
  "rather than the combustion time.")
K("CF-EUROPE-13", "ENG-DE-AESTUS", "mechanical.mass",
  [("111 kg", "SRC-SATNOW-AESTUS", "T"), ("The engine weight was 115 kg", "SRC-ESA-EPS", "EPS")],
  "PARTIALLY_RESOLVED", "definition",
  "ESA's EPS page, opened 2026-10-29 via www.esa.int (the m.esa.int host had failed), prints 'The engine weight was "
  "115 kg', so 115 kg is the agency figure. The 111 kg comes from a component catalogue whose source and scope "
  "(with or without gimbal or actuators) are not stated; no Airbus datasheet was reached.")
K("CF-EUROPE-14", "ENG-FR-VIKING-5", "performance.thrust_vac",
  [("758 kN (Viking 5)", "SRC-DLR-VIKING-IMG", "T"), ("760.7 kN (Viking 5C)", "SRC-WIKI-VIKING", "W")],
  "EXPLAINED", "different_variant", "DLR's 758 kN is for the Viking 5; 760.7 kN is reported for the Viking 5C.")
K("CF-EUROPE-15", "ENG-FR-VEXIN-B", "performance.thrust",
  [("301.55 kN", "SRC-WIKI-DIAMANT", "W"), ("about 28 metric tons", "SRC-IAC-09-3159", "T"), ("273.7 kN", "SRC-WIKI-EMERAUDE", "W")],
  "UNRESOLVED", "different_variant",
  "The IAC abstract's 'about 28 metric tons' (275 kN DERIVED) is for the Vexin of Diamant A; the 301.55 kN may be a later "
  "build. No primary figure for the Vexin B was opened.")
K("CF-EUROPE-16", "ENG-FR-VALOIS", "identity.configuration",
  [("1 x Valois", "SRC-WIKI-DIAMANT", "W"), ("Valois, single engine, 35 metric tons", "SRC-IAC-10-6759", "T"),
   ("4 x Vexin C", "SRC-ORBITCODEX-DIAMANTB", "N")],
  "RESOLVED", "primary_value_found",
  "The IAC paper on the Valois engine and the Diamant B first stage, by its authors, describes one Valois engine of 35 "
  "metric tons; the '4 x Vexin C' was never opened.")
K("CF-EUROPE-17", "ENG-FR-CORALIE-ENGINE", "performance.thrust",
  [("270 kN", "SRC-WIKI-EUROPA", "W"), ("262 kN", "SRC-DEUTSCHESMUSEUM-EUROPA", "T")],
  "UNRESOLVED", "rating_or_rounding", "3 percent apart; neither page names a condition.")
K("CF-EUROPE-18", "ENG-DE-ASTRIS", "performance.thrust",
  [("23.3 kN vac / 19.6 kN SL", "SRC-WIKI-ASTRIS-ENGINE", "W"), ("22.56 kN", "SRC-DEUTSCHESMUSEUM-EUROPA", "T")],
  "UNRESOLVED", "different_operating_point", "The museum gives one figure without a condition; it lies between the two.")
K("CF-EUROPE-19", "ENG-DE-ASTRIS", "identity.manufacturer",
  [("Snecma (manufacturer), ERNO (designer)", "SRC-WIKI-ASTRIS-ENGINE", "W"), ("MBB + ERNO", "SRC-DEUTSCHESMUSEUM-EUROPA", "T")],
  "UNRESOLVED", "definition", "The museum names MBB and ERNO for the stage; the engine maker is not named on the opened page.")
K("CF-EUROPE-20", "ENG-DE-HWK-109-509", "performance.thrust",
  [("~17 kN", "SRC-WIKI-HWK109509", "W"), ("200-1800 kg variable", "SRC-NASM-HWK109509", "T")],
  "EXPLAINED", "different_operating_point",
  "Throttleable engine: the Smithsonian gives the range 200-1,800 kgf (17.7 kN DERIVED at the top), which contains the ~17 kN.")
K("CF-EUROPE-21", "ENG-DE-HWK-109-509", "turbines.steam_generator.catalyst",
  [("wire-mesh catalyst", "SRC-WIKI-HWK109509", "W"), ("potassium permanganate catalytic chamber", "SRC-NASM-HWK109509", "T")],
  "UNRESOLVED", "different_variant",
  "The Smithsonian names a permanganate catalyst; the wire-mesh claim is encyclopedia-only. Builds may have differed.")
K("CF-EUROPE-22", "ENG-DE-BMW-109-718", "performance.thrust",
  [("1,250 kg", "SRC-WIKI-BMW109718", "W"), ("a single 9.8 kN (2,200 lbf) thrust BMW 109-718", "SRC-WARBIRDS-ME262", "T")],
  "UNRESOLVED", "rating_or_rounding",
  "1,250 kgf is 12.3 kN DERIVED, 25 percent above 9.8 kN (1,000 kgf). Neither page cites a source.")
K("CF-EUROPE-25", "ENG-GB-STENTOR", "performance.thrust",
  [("24,000 lbf (first chamber)", "SRC-BCAR-BLUESTEEL", "T"), ("20,000 lbf", "SRC-WIKI-STENTOR", "W")],
  "EXPLAINED", "definition",
  "The opened page gives 24,000 lbf for the main chamber alone; the Stentor had a second, cruise chamber, so the two "
  "figures need not describe the same thing. Not settled from a primary.")
K("CF-EUROPE-26", "ENG-GB-SUPER-SPRITE", "performance.thrust",
  [("The Super Sprite had a maximum thrust of 4,200 pounds for 40 seconds, but both the thrust and duration could be adjusted",
    "SRC-NASM-SUPERSPRITE", "NSS"), ("4,000 lb", "SRC-DHMUSEUM-SPECTRE", "NF")],
  "PARTIALLY_RESOLVED", "different_operating_point",
  "The Smithsonian record, read from an archive capture, gives 4,200 lb maximum for 40 s and says thrust and duration "
  "could be adjusted. The 4,000 lb has no source: the de Havilland museum page fetched for it covers the Spectre.")
K("CF-EUROPE-27", "ENG-FR-PROMETHEUS", "performance.thrust",
  [("980 kN SL", "SRC-WIKI-PROMETHEUS", "W"), ("'the previous generation of 1200 kN engines'", "SRC-ESA-PROMETHEUS", "T")],
  "EXPLAINED", "definition",
  "ESA's 1,200 kN describes the previous generation (Vulcain), not Prometheus. The opened page gives no Prometheus thrust.")
K("CF-EUROPE-29", "ENG-DE-A4-ENGINE", "aliases.name",
  [("'Triebwerk 39' not mentioned", "SRC-ENGINEHISTORY-V2", "T")],
  "UNRESOLVED", None, "The opened AEHS page does not use the designation; absence on one page settles nothing.")

# --- spacecraft, commercial and other
K("CF-R2_SC_COMM-R2-3", "ENG-US-STARLINER-OMAC", "performance.thrust / installation.count",
  [("'1,500-pound thrust class OMAC engines'", "SRC-AR-STARLINER-2016", "T"),
   ("four 7000 N (1600 lbf) OMAC main engines; twelve 375 N RCS", "SRC-ARXIV-2107-06795", "T")],
  "EXPLAINED", "rating_or_rounding",
  "The maker's 1,500 lbf 'class' and the paper's 1,600 lbf (7,000 N) agree as class and value. The engine count per "
  "shipset was not found in the release text.")
K("CF-R2_SC_COMM-R2-4", "ENG-JP-BT-4", "performance.thrust_vac",
  [("450 N", "SRC-SATCAT-BT4", "T"), ("500 N", "SRC-WIKI-BT4", "W"), ("'produces around 100' (lbf)", "SRC-MECO-CYGNUS-REBOOST-2018", "T"),
   ("infobox 'Thrust, vacuum 500 N'; variants: 'BT-4 (Cygnus) ... a thrust of 450 N', 'BT-4 (450N) ... 450 N ... 329 s', "
    "'BT-4 (500N) ... a thrust of 500 N ... 329 s'", "SRC-WIKI-BT4", "WBT")],
  "PARTIALLY_RESOLVED", "different_variant",
  "The encyclopedia article, now read, lists distinct BT-4 (450N) and BT-4 (500N) variants and a 450 N Cygnus unit; "
  "its infobox shows the 500 N variant. So 500 N and 450 N name two variants, not a rounding. The Cygnus reboost "
  "page's ~100 lbf (445 N DERIVED) and the catalogue's 450 N fit the 450 N unit. No IHI datasheet opened; the "
  "article's variant list is not evidence of the ratings themselves.")
K("CF-R2_SC_COMM-R2-5", "ENG-US-VR900", "performance.thrust",
  [("900 lbf thrust class", "SRC-SFN-IM1-2024", "T"), ("~4,900 lbf", "SRC-NEWSPACETRACKER-IMPROP", "NF")],
  "UNRESOLVED", "rating_or_rounding",
  "The opened news page gives the 900 lbf class; the 4,900 lbf is not on the fetched page. A 700 lbf summary had no source.")
K("CF-R2_SC_COMM-R2-6", "ENG-US-FRONTIER-DSE", "propellants.fuel",
  [("MON-25 / MMH", "SRC-NASA-TALOS", "T"), ("hydrazine (and MON)", "SRC-SPACENEWS-79146", "NF"),
   ("MMH and mixed oxides of nitrogen (Peregrine main engines)", "SRC-AIRPORTTECH-PEREGRINE", "T")],
  "RESOLVED", "primary_value_found",
  "NASA's TALOS page gives MON-25 / MMH and the trade page agrees on MMH; the 'hydrazine' wording sits behind a paywall "
  "and is the family name, not the fuel.")
K("CF-R2_SC_COMM-R2-7", "ENG-GB-LEROS-1B", "performance.thrust_vac",
  [("635 N", "SRC-NAMMO-LEROS1B", "T"), ("640 N (configured for Juno)", "SRC-AMPAC-JUNO-2011", "NF"),
   ("The Leros-1b main engine is a 645-Newton bi-propellant thruster using hydrazine-nitrogen tetroxide", "SRC-DB05-NASA-JUNO-PK-2011", "JPK")],
  "PARTIALLY_RESOLVED", "different_configuration",
  "The maker's page gives 635 N for the product; NASA's 2011 Juno press kit gives 645 N for the engine as flown on "
  "Juno, so a Juno-specific figure above the catalogue value is printed by a primary document. The 640 N that DB-0 "
  "cited is not on the fetched release text, and no document reconciles 640 with 645 N.")
K("CF-R2_SC_COMM-R2-9", "ENG-US-GR-22", "history.flown",
  [("GPIM includes four 1 N and one 22 N thruster", "SRC-NTRS-20140016838", "T"),
   ("the GR-1 'awaits its first on-orbit demonstration' on GPIM", "SRC-NTRS-20170001286", "T"),
   ("only the 1-N GR-1 thruster is included in the on-orbit demonstration mission phase of the GPIM program although "
    "that program completed mission life demonstrations for both thrusters", "SRC-NTRS-20170001286", "G17")],
  "RESOLVED", "different_epoch",
  "The 2014 paper plans one 22 N thruster on GPIM. The 2017 Aerojet Rocketdyne/NASA Glenn paper, re-read 2026-10-29, "
  "states on p.2 that only the GR-1 is in GPIM's on-orbit phase; the GR-22 prototype cracked in 2014 ground testing and "
  "its redesign was tested in 2015 on internal funding. The GR-22 did not fly on GPIM; no later flight was found.")
K("CF-R2_SC_COMM-R2-10", "ENG-CN-FY-25", "performance.isp_vac",
  [("2990 N.s/kg", "SRC-IAC11-490N-CN", "T"), ("3 030 N . s/kg nominal", "SRC-IAC03-LAE-CN", "T")],
  "UNRESOLVED", "different_epoch",
  "Two IAC abstracts, 2003 and 2011, at the same area ratio (154) and chamber pressure (0.68 MPa) give 3,030 and 2,990 "
  "N.s/kg. Whether both describe the same engine is not stated.")
K("CF-R2_SC_COMM-R2-12", "ENG-US-AEON-1", "performance.thrust",
  [("15,500 SL / 19,500 vac lbf (older listing)", "SRC-SPACEBUCKET-AEON", "NF"), ("23,000 SL / 25,400 vac lbf", "SRC-WIKI-AEONR", "W"),
   ("up to 23,000 lbf SL", "SRC-AIRPORTTECH-TERRAN1", "NF"), ("207,000 pounds for nine engines", "SRC-SFN-TERRAN1-2023", "T")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "Spaceflight Now gives 207,000 lbf for nine engines at liftoff, 23,000 lbf each DERIVED, and the Space Bucket page "
  "prints 'up to 23,000 pounds of force per engine at sea level'. The 15,500 lbf listing is not on the fetched page.")
K("CF-R2_SC_COMM-R2-13", "ENG-US-AEON-1", "cycle",
  [("gas generator engine cycle", "SRC-SPACEBUCKET-AEON", "T"), ("gas generator engine cycle", "SRC-AIRPORTTECH-TERRAN1", "T")],
  "CONFIRMED_SECONDARY", None, "Both opened pages say gas generator; the 'open expander' summary was not on either.")
K("CF-R2_SC_COMM-R2-16", "ENG-US-BROADSWORD", "performance.thrust",
  [("25,000 lbf sea level", "SRC-MASTEN-ENGINES", "T"), ("25,000 lbf vacuum", "SRC-SATNOW-BROADSWORD", "NF")],
  "RESOLVED", "primary_value_found", "The maker's page says sea level; the catalogue's vacuum label was not on the fetched page.")
K("CF-R2_SC_COMM-R2-18", "ENG-US-AJ26-62", "performance.thrust_vac",
  [("1,680 kN", "SRC-KOREASCI-AJ26", "T"), ("1,815 kN", "SRC-SPACEFLIGHT101-ANTARES", "N"), ("3,265 kN for the pair", "SRC-WIKI-ANTARES", "W"),
   ("two AJ26 LOX/RP rocket engines that supply approximately 3,630 kN (816,000 lbf) total vacuum thrust ... can throttle "
    "from 58% to 108%", "SRC-DB05-ORBITAL-ANTARES-UG-2013", "AUG")],
  "PARTIALLY_RESOLVED", "different_operating_point",
  "The vehicle maker's 2013 user's guide gives about 3,630 kN total vacuum thrust for the two engines, 1,815 kN each "
  "DERIVED, which is the unopened 1,815 kN figure. 1,815 / 1,680 = 1.080 DERIVED, equal to the guide's 108 percent "
  "throttle ceiling, so the Korean 1,680 kN is consistent with the 100 percent vacuum rating; but no opened document "
  "says that the 3,630 kN is the 108 percent point. The encyclopedia's 3,265 kN pair carries no condition.")
K("CF-R2_SC_COMM-R2-20", "ENG-US-NEWTONFOUR", "performance.thrust_vac",
  [("5,000 lbf", "SRC-WIKI-LAUNCHERONE", "W"), ("5,000 lbf", "SRC-NSF-LAUNCHERONE-2020", "T"), ("about 6,000 lb", "SRC-AVIATIONIST-L1-2020", "T"),
   ("NEWTONFOUR (N4) 6 min run time ... 5,000 lbf of thrust", "SRC-DB05-VIRGINORBIT-L1SG-2020", "VO1"),
   ("NewtonFour Second stage engine 6 min run time over multiple burns 5,000 lbf", "SRC-DB05-VIRGINORBIT-TECH-2021", "VO2")],
  "RESOLVED", "primary_value_found",
  "The maker's LauncherOne Service Guide (v2.1, August 2020) and its technology page both give NewtonFour 5,000 lbf "
  "(22.2 kN DERIVED). The 'about 6,000 lb' news figure has no maker source; the encyclopedia's 6,000 lbf sentence sits "
  "in its account of the 2015 design. The guide labels the N3 figure 'vacuum thrust' but prints no condition for N4.")
K("CF-R2_SC_COMM-R2-21", "ENG-US-AEON-R", "performance.thrust_sl",
  [("258,000 lbf (2023)", "SRC-RELATIVITY-PR-2023-04-12", "N"), ("269,000 lbf (2025)", "SRC-RELATIVITY-PR-2025-03-07", "T")],
  "EXPLAINED", "different_epoch", "Two dated maker releases; the 2025 figure is the later design value. Only the 2025 one was read.")
K("CF-R2_SCHEM-R2-3", "ENG-US-RAPTOR-3", "performance.thrust_sl",
  [("250 tf (551,000 lbf)", "SRC-SPACEX-UPDATES", "NF"), ("250 tf / 551 klbf", "SRC-SPACEX-STARSHIP-SPECS", "NF")],
  "UNRESOLVED", None, "Both SpaceX pages are script-rendered and delivered no text.")
K("CF-R2_SCHEM-R2-15", "ENG-US-RAPTOR-2", "identity.rating_attribution",
  [("230 tf / 1,630 kg as 'from' values", "SRC-SPACEX-UPDATES", "NF")],
  "UNRESOLVED", None, "The SpaceX page delivered no text.")
K("CF-R2_SCHEM-R2-5", "ENG-US-BE-4", "performance.thrust_sl",
  [("550,000 lbf", "SRC-ULA-BE4-FACTSHEET", "T"), ("640,000 lbf (2,846 kN)", "SRC-BLUE-NEWGLENN-PAGE", "N"),
   ("BE-4 Main Engines: 2446.5 kN (550k-lbf) thrust (Sea Level) each", "SRC-DB05-ULA-VULCAN-UG-2023", "VUG"),
   ("BE-4 Thrust : 640,000 lbf (2,846 kN)", "SRC-BLUE-ENGINES", "BOE"),
   ("will achieve 640,000 lbf later this year, with propellant subcooling increasing the current thrust capability from "
    "the existing 550,000 lbf (2025-11-20)", "SRC-BLUE-NG-UPGRADE", "BOU")],
  "EXPLAINED", "different_epoch",
  "ULA's fact sheet and its October 2023 Vulcan user's guide give 550,000 lbf (2446.5 kN) sea level. Blue Origin's "
  "release of 20 November 2025, read from an archive capture, calls 550,000 lbf the existing capability and 640,000 lbf "
  "the uprate from propellant subcooling, which its engines page now prints. Two dated ratings; whether Vulcan adopts "
  "the uprate is not stated.")
K("CF-R2_SCHEM-R2-7", "ENG-US-MERLIN-1D", "performance.thrust_sl",
  [("845 kN (190,000 lbf)", "SRC-SPACEX-FUG-2025", "T"), ("854 kN / 190,000 lbf", "SRC-WEVOLVER-MERLIN", "T"), ("854 kN", "SRC-UC-OLLI-SPACEX", "T")],
  "EXPLAINED", "unit",
  "190,000 lbf is 845.2 kN DERIVED: SpaceX's own guide is consistent; 854 kN is a digit transposition carried by the two "
  "secondary pages.")
K("CF-COMMERCIAL-COM-1", "ENG-US-MERLIN-1D-BLOCK-5", "performance.thrust_sl",
  [("845 kN (190,000 lbf)", "SRC-SPACEX-FUG-2025", "T"), ("854 kN (190,000 lbf)", "SRC-WEVOLVER-MERLIN", "T")],
  "EXPLAINED", "unit", "As CF-DB05-W-R2_SCHEM-R2-7: 190,000 lbf is 845 kN; 854 kN is a transposition.")
K("CF-R2_SCHEM-R2-8", "ENG-US-MERLIN-1D", "performance.pc",
  [("9.7 MPa (1,410 psi)", "SRC-WIKI-MERLIN", "W"), ("10.8 MPa ('Merlin-1D++' SL)", "SRC-WEVOLVER-MERLIN", "T")],
  "UNRESOLVED", "different_epoch", "Both are secondary and name different builds; SpaceX publishes no chamber pressure in the opened guide.")
K("CF-R2_SCHEM-R2-9", "ENG-US-MERLIN-1D", "performance.throttle_range",
  [("100 %-57 % (SL)", "SRC-WEVOLVER-MERLIN", "T"),
   ("Throttle capability Yes (170,000 lbf to 119,000 lbf sea level) [first stage, per engine]; Yes (210,000 lbf to 81,000 lbf) "
    "[second stage]", "SRC-DB05-SPACEX-F9UG-R2-2015", "SXU2"),
   ("min is ~40% of 1 Merlin", "SRC-DB05-MUSK-X-2016-05-06", "MX16")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "SpaceX's 2015 user's guide gives the first-stage Merlin 1D 170,000 to 119,000 lbf at sea level, 70 % DERIVED (the "
  "vacuum engine 210,000 to 81,000 lbf, 39 % DERIVED). In May 2016 SpaceX's chief executive wrote that the minimum is "
  "'~40% of 1 Merlin', so the 40 % claim has a maker-side source after the guide. That is an informal post, not a "
  "specification; the aggregator's 57 % still has no source, and no current SpaceX document gives a range.")
K("CF-COMMERCIAL-COM-2", "ENG-US-MERLIN-1D", "performance.thrust_sl",
  [("147,000 lbf (v1.1)", "SRC-SFN-2015-FT", "T"), ("170,000 lbf (FT)", "SRC-SFN-2015-FT", "T"), ("190,000 lbf (current)", "SRC-SPACEX-FUG-2025", "T"),
   ("63.5 tf announced; 66.68 tf updated", "SRC-SLR-F9-SMA", "N")],
  "EXPLAINED", "different_epoch",
  "A time series, not a conflict: Spaceflight Now dates the uprate from 147,000 to 170,000 lbf (2015) and SpaceX's 2025 "
  "guide gives 190,000 lbf.")
K("CF-COMMERCIAL-COM-3", "ENG-US-MERLIN-1D-VACUUM", "performance.thrust_vac",
  [("210,000 lbf max (2015)", "SRC-SFN-2015-FT", "T"), ("981 kN (220,500 lbf)", "SRC-SPACEX-FUG-2025", "T"),
   ("~81.6 tf / ~95.3 tf", "SRC-SLR-F9-SMA", "N")],
  "EXPLAINED", "different_epoch", "Time series: 210,000 lbf in 2015, 220,500 lbf in the 2025 guide.")
K("CF-COMMERCIAL-COM-4", "ENG-US-MERLIN-1D-VACUUM", "performance.isp_vac",
  [("348 s", "SRC-WEVOLVER-MERLIN", "T"), ("not printed", "SRC-SPACEX-FUG-2025", "T"),
   ("SpaceX's Merlin vacuum engine has the highest vacuum specific impulse (isp) ... with a vacuum isp of 348 seconds",
    "SRC-DB05-SPACEX-F9-PAGE-2018", "SX18")],
  "RESOLVED", "primary_value_found",
  "SpaceX's own Falcon 9 page (archive capture of 8 February 2018) gives the Merlin Vacuum a vacuum Isp of 348 s, the "
  "aggregator's figure. The 2025 guide omits Isp; it does not contradict the value. Later nozzle-extension variants are "
  "not covered by the 2018 page.")
K("CF-COMMERCIAL-COM-6", "ENG-US-MERLIN-1C", "performance.thrust_sl / performance.isp",
  [("78,000 lbf SL / 90,000 vac / 301 s (Falcon 1)", "SRC-SPACEX-PR-M1C-2007", "NF"),
   ("95,000 lbf SL / over 108,000 vac / 304 s (Falcon 9)", "SRC-SPACEX-PR-M1C-2007", "T"),
   ("350 kN SL / 400 kN vac / 304 s", "SRC-WIKI-MERLIN", "W"), ("43 tf SL / 49 tf vac", "SRC-SLR-F9-SMA", "N")],
  "PARTIALLY_RESOLVED", "different_configuration",
  "The 2007 SpaceX release gives the Falcon 9 configuration (95,000 / 108,000 lbf, 304 s); the Falcon 1 figures DB-0 "
  "attributed to it are not in the fetched text. The encyclopedia's kN pair is an early rating.")
K("CF-COMMERCIAL-COM-7", "ENG-US-RAPTOR-2", "performance.pc",
  [("300 bar routine", "SRC-TESLARATI-R2", "T"), ("321 bar peak at first static fire", "SRC-TESLARATI-R2", "T"),
   ("330 bar 'consistently'", "SRC-WCCF-RAPTOR-330", "T"), ("300 bar by July 2022", "SRC-WIKI-RAPTOR", "W")],
  "EXPLAINED", "different_operating_point",
  "Routine, peak and later test values reported by news sites from Musk's posts; none is a published rating.")
C("CF-DB05-W-COMMERCIAL-COM-13", engine_id="ENG-NZ-RUTHERFORD", field_path="performance.isp_sl",
  db0_conflict_id="CF-COMMERCIAL-COM-13",
  claims=[["The sea level versions on Electron's first stage now produce 5,600 lbf of thrust (up from 5,500 lbf, with a "
           "specific impulse of 311 s (3.05 km/s).", "SRC-RKLB-PAYLOAD-INCREASE", "release of 4 Aug 2020 (read in the Wave 2 pass)"],
          ["First Stage 9 Sea-level Rutherford Engines ... ISP: 311 seconds", "SRC-RL-ELECTRON-PAGE", "Electron page, 'Rutherford Engine' panel"]],
  resolution="UNRESOLVED", kind="definition",
  explanation="Rocket Lab prints 311 s next to the sea-level engine in both places. DB-0's doubt is a plausibility "
              "judgement (311 s is high for kerosene at sea level, so it may be the sea-level engine's vacuum Isp), "
              "not a second source; no document opened states the ambient condition of the 311 s.")
K("CF-COMMERCIAL-COM-14", "ENG-NZ-ARCHIMEDES-VACUUM", "performance.thrust_vac",
  [("200,000 lbf (890 kN)", "SRC-RL-NEUTRON-PAGE", "T"), ("202,300 lbf (900 kN)", "SRC-RL-ARCH-BUILD", "T")],
  "UNRESOLVED", "rating_or_rounding", "Two maker pages, 1 percent apart; the 200,000 may be rounded. Neither names a rating.")
K("CF-COMMERCIAL-COM-15", "ENG-US-REAVER", "performance.thrust",
  [("4x Reaver 801 kN (180,072 lbf) vac", "SRC-FIREFLY-ALPHA-PAGE", "T"), ("836.3 kN max for four", "SRC-FIREFLY-PUG-5.2", "N"),
   ("45,000 lbf per engine", "SRC-FIREFLY-MIRANDA-RR", "T"),
   ("Stage 1 Reaver Engines, Qty 4, Thrust: 836.3 kN [188.0 klbf] (vac), Isp 296 s (vac)", "SRC-DB05-FIREFLY-PUG-5.3", "PUG53")],
  "EXPLAINED", "rating_or_rounding",
  "180,072 lbf for four is 45,018 lbf each DERIVED: the release's 45,000 lbf is the same figure rounded. The 5.2 guide "
  "returned 404; the 5.3 guide (2026-09) prints 836.3 kN (vac) for four without a 'maximum' qualifier, about 4 percent "
  "above the web page's 801 kN, alongside a Lightning figure that also rose (see CF-DB05-W-COMMERCIAL-COM-16).")
K("CF-COMMERCIAL-COM-16", "ENG-US-LIGHTNING", "performance.thrust_vac",
  [("70.1 kN (15,759 lbf)", "SRC-FIREFLY-ALPHA-PAGE", "T"), ("73.0 kN (16.4 klbf) max", "SRC-FIREFLY-PUG-5.2", "N"),
   ("Stage 2 Lightning Engine, Thrust: 73.0 kN [16.4 klbf] (vac), Isp 322 seconds (vac)", "SRC-DB05-FIREFLY-PUG-5.3", "PUG53")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "Both figures are now opened from the maker: the web page prints 70.1 kN and the 2026-09 user's guide 5.3 prints "
  "73.0 kN (vac), both at 322 s. The guide does not call 73.0 kN a maximum, so DB-0's 'max' reading is not supported; "
  "the newer guide (with the stage-1 figure also higher) suggests an uprated rating, but no document says which "
  "figure is current.")
K("CF-SPACECRAFT-2", "ENG-US-R-4D", "performance.thrust_vac",
  [("100 lbf", "SRC-NASA-TND7151", "NF"), ("110 lbf (490 N)", "SRC-WIKI-R4D", "W"),
   ("The nominal thrust of the engine is 100-pounds; Qual engines would have 100 lb. thrust rather than the nominal "
    "95 lb. thrust of the PFRT engine", "SRC-DB05-NTRS-19690029231", "R69")],
  "PARTIALLY_RESOLVED", "different_variant",
  "The NASA report had no usable text layer. Marquardt's 1969 Apollo SM/LM RCS development summary gives the "
  "Apollo engine a nominal 100 lb thrust (raised from 95 lb at PFRT to 100 lb for qualification), so 100 lbf is the "
  "documented Apollo-era value. 110 lbf (490 N) is the later R-4D variant figure, for which no document was opened.")
K("CF-SPACECRAFT-4", "ENG-US-OMS-E-ORION-ESM", "history.heritage_last_flight",
  [("STS-112 (2002)", "SRC-NTRS-20240003648", "N"),
   ("'has flown to space six times already between 2000 and 2002'", "SRC-ESA-BLOG-ART2ENG", "T")],
  "RESOLVED", "primary_value_found",
  "The ESA blog does not say 2011: it says the Artemis II engine from Atlantis flew six times between 2000 and 2002, "
  "matching the NASA paper's last flight on STS-112 (2002). DB-0's '2011' was a misreading.")
K("CF-SPACECRAFT-9", "ENG-US-MR-107N", "installation.count",
  [("12 MR-107N 300 N for landing", "SRC-AIRPORTTECH-PHX", "NF"), ("eight engines", "SRC-NBC-PHX", "NF"),
   ("the lander separates from the parachute/backshell and begins using a system of 12 pulsed thrusters to perform a "
    "gravity turn powered descent", "SRC-DB05-NTRS-20080034655", "PX8"),
   ("12 descent engines, ~300N each. Pulse-width modulated at 10Hz. (2004 baseline)", "SRC-DB05-NTRS-20070014659", "PX4")],
  "RESOLVED", "primary_value_found",
  "Neither fetched news page says what DB-0 cited (the trade page's sentence is garbled: 'eight 1.0lbf and 5.0lbf ... "
  "engines and 12 68.0lbf ... thrusters'). JPL's 2008 architecture paper prints a system of 12 pulsed thrusters for the "
  "powered descent, and the 2004 EDL presentation 12 descent engines of about 300 N each. 'Eight' has no opened "
  "document; it likely counts the smaller attitude thrusters. Neither NASA document names the MR-107N model.")
K("CF-TAXONOMY-TAX-3", "ENG-US-IPD", "history.test_dates",
  [("21 of 26 tests, up to 100 percent power (2006)", "SRC-SFN-IPD-2006", "T"),
   ("integrated engine testing to begin late 2004", "SRC-NTRS-IPD-WPB", "NX")],
  "EXPLAINED", "different_epoch", "A plan against what was achieved; not a conflict about hardware.")
K("CF-TAXONOMY-TAX-7", "ENG-US-ROTON-ROTARY-ENGINE", "geometry.chamber_count",
  [("'dozens of small combusters arranged in a ring'", "SRC-FLIGHTGLOBAL-ROTON", "T"), ("192 (one summary)", "SRC-WIKI-ROTARYROCKET", "W")],
  "UNRESOLVED", None, "The opened article gives no number; 192 is unverified.")
K("CF-TAXONOMY-TAX-8", "ENG-US-RAPTOR", "vehicle.tank_pressurization",
  [("original design pure autogenous; preburner exhaust question for IFT-2/3", "SRC-MANIFOLD-STARSHIP", "T"),
   ("'Prior to SN9, SpaceX used autogenous pressurization'", "SRC-WCCFTECH-SN10", "T")],
  "EXPLAINED", "different_epoch",
  "A vehicle-level scheme that changed between prototypes; not an engine attribute. Recorded so it is not ingested as one.")

D("SRC-DB05-NTRS-19690029231", identifier="NTRS 19690029231", title="Apollo SM-LM RCS engine development program summary report, volume 1",
  tier="A", rights_checked="NTRS determination GOV_PUBLIC_USE_PERMITTED", rights_class="VALUES_WITH_ATTRIBUTION",
  note="180 pages, OCR text layer (The Marquardt Corporation, 1969). 'The nominal thrust of the engine is 100-pounds', "
       "propellants N2O4 and MMH or Aerozine-50; qualification engines 100 lb against the 95 lb PFRT engine. Used as a "
       "conflict claim only.")

D("SRC-DB05-NTRS-19630012071", identifier="NTRS 19630012071 (NASA SP-45)",
  title="Mercury Project Summary including results of the fourth manned orbital flight, May 15 and 16, 1963", tier="A",
  rights_checked="NTRS determination GOV_PUBLIC_USE_PERMITTED", rights_class="VALUES_WITH_ATTRIBUTION",
  note="454 pages, OCR text layer. Figure 4-13 Mercury-Redstone: 'Model A-7 engine, Thrust 78,000 lb', alcohol/LOX, "
       "H2O2 turbopump drive. Atlas: two booster engines of 154,000 lb each, sustainer 57,000 lb, two verniers 1,000 lb "
       "each. Used as conflict claims only.")

D("SRC-ESA-EPS", identifier='https://www.esa.int/Enabling_Support/Space_Transportation/Launch_vehicles/Storable_Propellant_Stage_EPS', title="Ariane 5 Storable Propellant Stage (EPS)", tier="A",
  rights_checked="ESA web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29 from www.esa.int (the registry's m.esa.int URL returned no response on 2026-10-28). Aestus: "
       "pressure-fed, gimbal 16 deg max, 'vacuum thrust ... 2.7 tonnes', more than 1000 s on a GTO mission, 'engine weight "
       "was 115 kg'; EPS loads 3.2 t MMH and 6.6 t N2O4. Used as conflict claims only.")

D("SRC-DB05-KBKHA-RD0120", identifier="https://kbkha.ru/deyatel-nost/raketnye-dvigateli-dlya-kosmicheskoy-otrasli/raketnye-dvigateli-ao-kbha/rd0120/", title="РД0120 (KBKhA engine page)", tier="A",
  rights_checked="manufacturer web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29 from the design bureau's own site. тяга в пустоте 200 тс; удельный импульс 455 с; давление в КС 223 кг/см2; LOX/LH2; Energia core stage. Used as conflict claims only.")

D("SRC-DB05-KBKHA-RD0124", identifier="https://kbkha.ru/deyatel-nost/raketnye-dvigateli-dlya-kosmicheskoy-otrasli/raketnye-dvigateli-ao-kbha/rd0124/", title="РД0124 (KBKhA engine page)", tier="A",
  rights_checked="manufacturer web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29 from the design bureau's own site. тяга в пустоте 30 тс; удельный импульс 359 с; давление в КС 160 кг/см2; LOX/kerosene; 14D23; 300 s main mode. Used as conflict claims only.")

D("SRC-DB05-KBKHA-RD0124MS", identifier="https://kbkha.ru/deyatel-nost/raketnye-dvigateli-dlya-kosmicheskoy-otrasli/raketnye-dvigateli-ao-kbha/rd0124ms/", title="РД0124МС (KBKhA engine page)", tier="A",
  rights_checked="manufacturer web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29 from the design bureau's own site. тяга в пустоте 60,34 тс; удельный импульс в пустоте 361 с; давление в КС 155 кг/см2; LOX/naftil; Soyuz-5 second stage; in development. Used as conflict claims only.")

D("SRC-DB05-KBKHA-RD0210", identifier="https://kbkha.ru/deyatel-nost/raketnye-dvigateli-dlya-kosmicheskoy-otrasli/raketnye-dvigateli-ao-kbha/dvigatelnyj-blok-tri-rd0210-odin-rd0211/", title="Двигательный блок (три РД0210 + один РД0211) (KBKhA engine page)", tier="A",
  rights_checked="manufacturer web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29 from the design bureau's own site. тяга в пустоте (одного двигателя) 59,36 тс; удельный импульс 326,5 с; давление в КС 150 кг/см2; N2O4/UDMH; Proton-K second stage. Used as conflict claims only.")

D("SRC-DB05-FIREFLY-PUG-5.3", identifier='https://fireflyspace.com/wp-content/uploads/2026/09/Alpha-PUG-5.3-1.pdf', title="Alpha Payload User's Guide 5.3 (Firefly Aerospace)", tier="A",
  rights_checked="manufacturer user's guide; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29 (the 5.2 guide DB-0 cited returns 404). 38 pages, text layer. p.6 vehicle overview: Stage 1 four Reaver engines, LOX/RP-1, 'Thrust: 836.3 kN [188.0 klbf] (vac)', Isp 296 s (vac), tap-off; Stage 2 one Lightning engine, 'Thrust: 73.0 kN [16.4 klbf] (vac)', Isp 322 s (vac), tap-off. No 'maximum' qualifier is printed. Used as conflict claims only.")

D("SRC-DB05-KSPE-2011-KRE75", identifier='https://koreascience.kr/article/JAKO201110348675501.pdf', title="Definition of Engine Component Performance Test Range of 75tf Class Gas Generator Cycle Liquid Propellant Rocket Engine",
  tier="A", rights_checked="society journal article; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="7 pages, text layer (Nam C.-H., Moon Y., Seol W.-S., KARI; 한국추진공학회지 15(6), pp.91-97, Dec 2011). Section 2.1 lists the 75 tf-class gas-generator engine's main specification: 진공 추력 75 tf; 진공 비추력 297 sec; LOX/kerosene; 연소기 압력 60 bar; turbopump 10,500 rpm; GG 58 bar; fuel 83 kg/s; oxidizer 176 kg/s. One plain curl got an empty reply on 2026-10-29; fetch.py then retrieved the same 7-page PDF. Used as conflict claims only.")

D("SRC-DB05-NTRS-20080034655", identifier="NTRS 20080034655", title="Overview of the Phoenix Entry, Descent and Landing System Architecture",
  tier="A", rights_checked="NTRS determination GOV_PUBLIC_USE_PERMITTED", rights_class="VALUES_WITH_ATTRIBUTION",
  note="10 pages, text layer (Grover M. R. and Cichy B. D., JPL; AIAA 2008). p.2: the lander 'begins using a system of 12 "
       "pulsed thrusters to perform a gravity turn powered descent'. Used as a conflict claim only.")

D("SRC-DB05-NTRS-20070014659", identifier="NTRS 20070014659", title="Overview of the Phoenix Entry, Descent and Landing System",
  tier="A", rights_checked="NTRS determination PUBLIC_USE_PERMITTED", rights_class="VALUES_WITH_ATTRIBUTION",
  note="12-slide presentation (2nd International Planetary Probe Workshop, August 2004). Slide 10: '12 descent engines, "
       "~300N each. Pulse-width modulated at 10Hz. Current baseline 3 full on.' A design-phase baseline. Used as a "
       "conflict claim only.")

D("SRC-DB05-NASA-JUNO-PK-2011", identifier='https://www.jpl.nasa.gov/news/press_kits/JunoLaunch.pdf', title="Juno Launch press kit (NASA, August 2011)", tier="A",
  rights_checked="NASA public-affairs document; US Government work", rights_class="VALUES_WITH_ATTRIBUTION",
  note="25 pages, text layer (NASA 'Juno Launch' press kit, PDF dated 2011-07-27). p.15 'Propulsion System': 'The Leros-1b main engine is a 645-Newton bi-propellant thruster using hydrazine-nitrogen tetroxide.' p.6: launch mass 3,625 kg. Used as a conflict claim only.")

D("SRC-DB05-NASA-GODDARD-95", identifier='https://www.nasa.gov/history/95-years-ago-goddards-first-liquid-fueled-rocket/', title="95 Years Ago: Goddard's First Liquid-Fueled Rocket (NASA History)", tier="B",
  rights_checked="NASA web page; US Government work", rights_class="VALUES_WITH_ATTRIBUTION",
  note="NASA History feature '95 Years Ago: Goddard's First Liquid-Fueled Rocket' (posted 2021-03-17): 'On March 16, 1926, he set up his rocket, which he later called Nell, fueled with gasoline and liquid oxygen, on a farm in Auburn, Massachusetts.' A retrospective agency history article, not a contemporary record. Used as a conflict claim only.")

D("SRC-DB05-CALT-LM3C-UM-1998", identifier='https://www.globalsecurity.org/space/library/report/1999/lm3cchapter2.pdf', title="LM-3C User's Manual, Chapter 2 (CALT, Issue 1998)", tier="A",
  rights_checked="manufacturer manual marked proprietary, third-party mirror; values only", rights_class="RESTRICTED_REFERENCE",
  note="22 pages, text layer (GlobalSecurity mirror of the CALT manual; pages marked 'CALT'S PROPRIETARY'). Table 2-1 p.2-2: second stage DaFY20-1 (Main) 742 kN, 2922.57 N.s/kg; DaFY21-1 (Vernier) 11.8x4 kN, 2910.5 N.s/kg; text: 'one main engine and four vernier engines on the second stage. The total thrust is 789.1kN.' Used as a conflict claim only.")

D("SRC-DB05-CALT-LM2E-UM-1999", identifier='https://www.globalsecurity.org/space/library/report/1999/lm2echapter2.pdf', title="LM-2E User's Manual, Chapter 2 (CALT, Issue 1999)", tier="A",
  rights_checked="manufacturer manual marked proprietary, third-party mirror; values only", rights_class="RESTRICTED_REFERENCE",
  note="22 pages, text layer (GlobalSecurity mirror of the CALT manual; pages marked 'CALT'S PROPRIETARY'). Table 2-1 p.2-2: DaFY20-1 (main) 741.4 kN, 2922.37 N.s/kg; DaFY21-1 (verniers) 11.8x4 kN, 2834.11 N.s/kg (in vacuum); text: total second-stage thrust 788.5 kN. Used as a conflict claim only.")

D("SRC-DB05-ORBITAL-ANTARES-UG-2013", identifier='https://www.manualsdir.com/manuals/569836/orbital-antares.html?page=15', title="Antares OSP-3 User's Guide, Release 1.1 (Orbital Sciences, July 2013)", tier="A",
  rights_checked="manufacturer guide approved for public release, read from a third-party mirror; values only",
  rights_class="RESTRICTED_REFERENCE", note="Antares OSP-3 User's Guide, Release 1.1, July 2013 (Orbital Sciences Corporation; 'Approved for Public Release, Distribution Unlimited'), read as the text layer of a 99-page third-party mirror (manualsdir.com, pages 2-3 and 15). Section 2.2.1 (mirror page 15): 'The MES consists of two AJ26 LOX/RP rocket engines that supply approximately 3,630 kN (816,000 lbf) total vacuum thrust' ... 'an oxygen-rich, staged combustion cycle that can throttle from 58% to 108%'. Used as a conflict claim only.")

D("SRC-DB05-ESA-A6-ENGINES", identifier='https://www.esa.int/Enabling_Support/Space_Transportation/Ariane/The_engines_of_Ariane_6', title="The engines of Ariane 6 (ESA)", tier="A",
  rights_checked="ESA web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="ESA page 'The engines of Ariane 6' (dated 05/06/2024). Vulcain 2.1 text: 'providing more than 1370 kN of thrust'; 'Vulcain 2.1 main engine characteristics: 154 000 kg of liquid oxygen (LOX) and liquid hydrogen (LH2) consumed; 1371 kN of thrust; 15 mW turbopump power; 468 seconds of operation'; LH2 turbopump 33 000 rpm, 15 MW. No vacuum/sea-level qualifier is printed. Developed by ArianeGroup, Vernon. Used as a conflict claim only.")

D("SRC-WIKI-BT4", identifier="https://en.wikipedia.org/wiki/BT-4_(rocket_engine)", title="BT-4 (rocket engine) (Wikipedia)",
  tier="D", rights_checked="English Wikipedia article, current revision fetched on 2026-10-29; text CC BY-SA 4.0",
  rights_class="VALUES_WITH_ATTRIBUTION",
  note="Encyclopedia page read from its text (infobox and 'Known variations'); identity as registered by DB-0. Not evidence "
       "of an engine value.")

D("SRC-DB05-JZYJ-LONGYUN", identifier='https://www.jzyjspace.com/products_list/6.html', title='龙云发动机 (Longyun engine, Jiuzhou Yunjian product page)', tier="A",
  rights_checked="manufacturer web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Longyun product text: '“龙云”发动机的海平面推重比＞80，海平面推力70吨，真空版推力80吨，推力调节范围32%~106%'; LOX/methane, multi-start, recoverable first-stage engine; 7000 s of hot-fire; 'will fly sub-orbital in 2024' (page not updated since). Used as a conflict claim only.")

D("SRC-DB05-AGNIKUL-PRODUCT", identifier='https://agnikul.in/product/', title='Agnibaan product page (Agnikul Cosmos)', tier="A",
  rights_checked="manufacturer web page; reuse terms not reviewed", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Agnibaan 'Base Shroud' panel: 'houses the world's first single piece 3D printed semi-cryogenic patented rocket engine, Agnilet, that can propel the vehicle with its 6.2kN thrust capacity.' No ambient condition printed. Used as a conflict claim only.")

D("SRC-DB05-VIRGINORBIT-L1SG-2020", identifier='https://web.archive.org/web/20210507125828/https://virginorbit.com/wp-content/uploads/2020/09/LauncherOne-Service-Guide-August-2020.pdf', title='LauncherOne Service Guide, Version 2.1 (Virgin Orbit, August 2020)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Virgin Orbit LauncherOne Service Guide, Version 2.1, August 2020 ('Cleared for Release: 18-S-1862 - As Amended'), 57 pages, read from the Internet Archive capture of 2021-05-07 (the maker's site is gone). Section 1.4 figure (PDF p.10): 'NEWTONTHREE (N3) 3 min run time 73,500 lbf / 327 kN vacuum thrust LOX/RP-1 Pump-Fed Engine'; 'NEWTONFOUR (N4) 6 min run time ... 5,000 lbf of thrust'. The N4 figure carries no vacuum/sea-level qualifier. Used as a conflict claim only.")

D("SRC-DB05-VIRGINORBIT-TECH-2021", identifier='https://web.archive.org/web/20210117214058/https://virginorbit.com/technology/', title='Technology (Virgin Orbit web page, captured 2021-01-17)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Virgin Orbit technology page, Internet Archive capture of 2021-01-17: 'NewtonFour Second stage engine 6 min run time over multiple burns 5,000 lbf'; 'NewtonThree First stage engine 3 min run time ~75,000 lbf'. Used as a conflict claim only.")

D("SRC-DB05-SPACEX-F9-PAGE-2018", identifier='https://web.archive.org/web/20180208031148/http://www.spacex.com/falcon9', title='Falcon 9 (SpaceX web page, captured 2018-02-08)', tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. SpaceX Falcon 9 page, Internet Archive capture of 2018-02-08 (the live page is script-rendered). Merlin Vacuum panel: 'SpaceX's Merlin vacuum engine has the highest vacuum specific impulse (isp) ... of any American liquid oxygen/kerosene engine with a vacuum isp of 348 seconds'; second stage 'Burn Time 397 sec Thrust 934 kN 210,000 lbf'; first stage 'Thrust At Sea Level 7,607 kN 1,710,000 lbf Thrust In Vacuum 8,227 kN 1,849,500 lbf'. Used as a conflict claim only.")

D("SRC-DB05-SPACEX-F9UG-R2-2015", identifier='https://web.archive.org/web/20170314002928/http://www.spacex.com/sites/spacex/files/falcon_9_users_guide_rev_2.0.pdf', title="Falcon 9 Launch Vehicle Payload User's Guide, Rev 2 (SpaceX, 21 October 2015)", tier="A",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. SpaceX Falcon 9 Payload User's Guide Rev 2, 21 October 2015 ('Approved for Public Release'), 69 pages, read from the Internet Archive capture of 2017-03-14. PDF p.11: 'Nine SpaceX Merlin engines power the Falcon 9 first stage with up to 756 kN (170,000 lbf) thrust per engine at sea level'; table: second stage 934 kN (vacuum) (210,000 lbf); 'Throttle capability Yes (170,000 lbf to 119,000 lbf sea level) Yes (210,000 lbf to 81,000 lbf)'. Used as a conflict claim only.")

D("SRC-DB05-MUSK-X-2016-05-06", identifier='https://web.archive.org/web/20170205184532/https://twitter.com/elonmusk/status/728753234811060224', title='Elon Musk on Twitter, 6 May 2016 (status 728753234811060224)', tier="B",
  rights_checked="maker material read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Post by SpaceX's chief executive, 6 May 2016 (data-time 1462579247), read from the Internet Archive capture of 2017-02-05: 'Max is just 3X Merlin thrust and min is ~40% of 1 Merlin. Two outer engines shut off before the center does.' (about the landing burn). An informal statement, not a specification. Used as a conflict claim only.")

D("SRC-NASM-SUPERSPRITE", identifier='https://web.archive.org/web/20250405012001/https://airandspace.si.edu/collection-objects/rocket-engine-liquid-fuel-super-sprite-cut-away/nasm_A19700331000', title='Rocket Engine, Liquid Fuel, Super Sprite, Cut Away (A19700331000)', tier="D",
  rights_checked="record read from an Internet Archive capture; values only", rights_class="RESTRICTED_REFERENCE",
  note="Fetched 2026-10-29. Smithsonian NASM record A19700331000 (Super Sprite, cut-away), archive capture of 2025-04-05: 'The Super Sprite had a maximum thrust of 4,200 pounds for 40 seconds, but both the thrust and duration could be adjusted to fit different mission needs.' Overall 620 lb. Used as a conflict claim only.")
