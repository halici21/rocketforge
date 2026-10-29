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
    ("SRC-GE-WELKIN-EN", "Galactic Energy English page: Welkin 50 t class."),
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
  [("91,350 lbf max", "SRC-WIKI-JUPITERA", "W"), ("series final 78,000 lb", "SRC-NASA-MSFC-MERCREDSTONE", "T")],
  "UNRESOLVED", "different_variant",
  "The MSFC page gives 78,000 lb as the final Redstone A-series figure; the 91,350 lbf belongs to a Jupiter-A summary "
  "never opened. Which A-series sub-model (A-6, A-7) each refers to is not stated.")
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
  [("16 March 1926", "SRC-APS-GODDARD", "NF")],
  "UNRESOLVED", None,
  "The APS page fetched has no date in its text; the conflict stays as DB-0 recorded it.")
K("CF-US_HIST-24", "ENG-US-LR101", "performance.thrust",
  [("1,017 lbf tank-fed / 1,060 lbf pressure-fed", "SRC-WIKI-LR101", "W"), ("830 lb tank-fed downrated to 525 lb", "SRC-DTIC-AD0423340", "N"),
   ("~1,012 lb per vernier (RS-27A)", "SRC-PURDUE-RS27A", "T")],
  "UNRESOLVED", "different_variant",
  "Purdue's 1,012 lb is for the RS-27A vernier on Delta II, a later application. The DTIC report was not fetched. Each "
  "figure belongs to a different installation; none is shown to be the LR101 rating.")

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
   ("Z-Stoff = 27 % sodium permanganate solution", "SRC-NASM-A19600013000", "N")],
  "UNRESOLVED", None,
  "Only the AEHS page was read (85 %). The 80 % and the Z-Stoff concentration were not opened.")
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
  [("359 s", "SRC-WIKI-SOYUZ5", "W"), ("361 s", "SRC-WWW1-RD0124", "T"), ("361 s ('RD-124MV')", "SRC-FRONTIER-SOYUZ5", "NF")],
  "UNRESOLVED", "different_variant",
  "One opened Russian page gives 361 s for a 60 t modification; the Soyuz-5 page DB-0 cited does not print 361. Which "
  "variant designation each figure belongs to is not settled.")
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
  [("582 kN; 14.7 MPa; 220 s", "SRC-WIKI-RD0210", "W"), ("593.6 kN; 15 MPa; 230 s", "SRC-RSW-RD0210", "T")],
  "UNRESOLVED", "different_variant",
  "Each figure differs by 2-5 percent; 14.7 MPa is 150 kgf/cm2, so the pressures may be one value in two units. Neither "
  "page cites a source.")
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
  "UNRESOLVED", None, "The Bilibili article delivered no text; nothing opened gives the range.")
K("CF-R2_ASIA-R2A-15", "ENG-CN-YF-100", "performance.thrust_sl",
  [("1,200 kN", "SRC-WIKI-YF100", "W"), ("1,188 kN", "SRC-BILI-CV15113396", "NX")],
  "UNRESOLVED", None, "The Bilibili article delivered no text; nothing opened gives the thrust.")
K("CF-R2_ASIA-R2A-16", "ENG-KR-KRE-075", "performance.pc",
  [("7.0 MPa", "SRC-WIKI-KRE075", "W"), ("60 bars", "SRC-FRWIKI-KRE075", "W"), ("60 bar (design stage, 2009)", "SRC-KSCI-KARI-2009-KRE75", "T")],
  "PARTIALLY_RESOLVED", "different_epoch",
  "The 2009 KARI paper gives 60 bar at the design stage; 7.0 MPa is unsourced and may be a later build. No later KARI "
  "document was opened.")
K("CF-R2_ASIA-R2A-17", "ENG-KR-KRE-075", "performance.thrust_vac",
  [("735.5 kN (stage 1)", "SRC-WIKI-KRE075", "W"), ("75.8 tonf (SL type)", "SRC-NAMU-KRE075", "NF"),
   ("74.8 ton (design, 2009)", "SRC-KSCI-KARI-2009-KRE75", "T")],
  "UNRESOLVED", "different_epoch",
  "Only the 2009 design figure (74.8 t vac) was read; the flown rating was not found in an opened document.")
K("CF-R2_ASIA-R2A-21", "ENG-IN-LAM-440-N", "propellants.roles",
  [("MMH fuel / MON-3 oxidizer", "SRC-IAC16-32550", "T"), ("MON 'fuel', UDMH 'oxidizer'", "SRC-SF101-LAM", "N")],
  "RESOLVED", "primary_value_found",
  "The ISRO authors' IAC abstract: 'The propellant combination employed is MON-3 & MMH at a mixture ratio of 1.6'. The "
  "swapped roles were never opened and reverse fuel and oxidizer.")
K("CF-R2_ASIA-R2A-22", "ENG-IN-AGNILET", "performance.thrust",
  [("approximately 3 kN at sea level", "SRC-IE-AGNIBAAN", "T"), ("6.2 kN", "SRC-M3D-AGNIKUL-2026", "T")],
  "UNRESOLVED", "different_variant",
  "Two news pages, 2024 and 2026, give 3 kN and 6.2 kN; neither names the engine variant or condition.")
K("CF-R2_ASIA-R2A-23", "ENG-IN-DHAWAN-1", "performance.thrust",
  [("1.5 kN vac", "SRC-CHANAKYA-DHAWAN1", "N"), ("1.0 kN", "SRC-COLDFACTS-DHAWAN1", "NF")],
  "UNRESOLVED", None, "The fetched page gives no thrust; nothing opened settles it.")
K("CF-R2_ASIA-R2A-24", "ENG-RU-RD-151", "identity.designation",
  [("RD-191", "SRC-WIKI-NARO1", "W"), ("RD-151", "SRC-SPACENEWS-12177", "T"), ("RD-151", "SRC-SFN-KSLV-2010", "T")],
  "EXPLAINED", "different_variant",
  "Two opened news pages name the KSLV first-stage engine RD-151, a derated RD-191; the encyclopedia names the parent "
  "engine.")
K("CF-R2_ASIA-R2A-28", "ENG-CN-WELKIN", "performance.thrust_sl",
  [("50 t", "SRC-GE-WELKIN-EN", "T"), ("400 kN", "SRC-WIKI-WELKIN", "W")],
  "UNRESOLVED", "rating_or_rounding",
  "50 tf is 490 kN DERIVED, 23 percent above 400 kN. The manufacturer's '50 t' may be a class, not a rating; not settled.")
K("CF-R2_ASIA-R2A-30", "ENG-CN-LONGYUN", "performance.thrust",
  [("70 t class", "SRC-36KR-JZYJ", "T"), ("80 t class", "SRC-JIEMIAN-14422448", "T")],
  "UNRESOLVED", "different_epoch", "Two news pages give two classes; neither gives a rating or a date for its figure.")
K("CF-ASIA_OTHER-7", "ENG-CN-YF-23", "performance.thrust_vac",
  [("47.1 kN", "SRC-WIKI-YF23", "W"), ("46.1 kN", "SRC-GS-CZ2D", "T")],
  "UNRESOLVED", "rating_or_rounding", "One digit apart (2 percent); possibly a transcription slip in one source. Neither is primary.")
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
  [("1,371 kN (308,000 lbf)", "SRC-NEWSPACEECON-V21", "T"), ("1,340 kN", "SRC-METALAM-V21", "NF"), ("135 t vacuum", "SRC-3DPI-V21", "NF")],
  "UNRESOLVED", None,
  "Only one opened page gives a figure (1,371 kN); the other two fetched pages print none. Tertiary.")
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
  [("111 kg", "SRC-SATNOW-AESTUS", "T"), ("115 kg", "SRC-ESA-EPS", "N")],
  "UNRESOLVED", "definition", "Only the catalogue was read; whether the masses differ in scope is not stated.")
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
  [("4,200 lb", "SRC-NASM-SUPERSPRITE", "N"), ("4,000 lb", "SRC-DHMUSEUM-SPECTRE", "NF")],
  "UNRESOLVED", None, "The fetched museum page is about the Spectre and gives no Super Sprite figure.")
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
  [("450 N", "SRC-SATCAT-BT4", "T"), ("500 N", "SRC-WIKI-BT4", "W"), ("'produces around 100' (lbf)", "SRC-MECO-CYGNUS-REBOOST-2018", "T")],
  "UNRESOLVED", "rating_or_rounding",
  "100 lbf is 445 N DERIVED, consistent with 450 N; the 500 N has no opened source. No IHI datasheet opened.")
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
  [("635 N", "SRC-NAMMO-LEROS1B", "T"), ("640 N (configured for Juno)", "SRC-AMPAC-JUNO-2011", "NF")],
  "UNRESOLVED", "different_configuration",
  "The maker's page gives 635 N; the Juno 640 N is not on the fetched release text.")
K("CF-R2_SC_COMM-R2-9", "ENG-US-GR-22", "history.flown",
  [("GPIM includes four 1 N and one 22 N thruster", "SRC-NTRS-20140016838", "T"),
   ("the GR-1 'awaits its first on-orbit demonstration' on GPIM", "SRC-NTRS-20170001286", "T")],
  "UNRESOLVED", "different_epoch",
  "The 2014 paper plans one 22 N thruster on GPIM; the 2017 paper speaks only of the GR-1 on GPIM, while the GR-22 was "
  "still in redesign testing. Whether a GR-22 flew is not stated in either.")
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
  [("1,680 kN", "SRC-KOREASCI-AJ26", "T"), ("1,815 kN", "SRC-SPACEFLIGHT101-ANTARES", "N"), ("3,265 kN for the pair", "SRC-WIKI-ANTARES", "W")],
  "UNRESOLVED", "rating_or_rounding", "Only the Korean journal page was read; its 1,680 kN carries no rating name.")
K("CF-R2_SC_COMM-R2-20", "ENG-US-NEWTONFOUR", "performance.thrust_vac",
  [("5,000 lbf", "SRC-WIKI-LAUNCHERONE", "W"), ("5,000 lbf", "SRC-NSF-LAUNCHERONE-2020", "T"), ("about 6,000 lb", "SRC-AVIATIONIST-L1-2020", "T")],
  "UNRESOLVED", "rating_or_rounding", "Two 2020 news pages give 5,000 and about 6,000 lb; neither cites the maker.")
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
   ("BE-4 Main Engines: 2446.5 kN (550k-lbf) thrust (Sea Level) each", "SRC-DB05-ULA-VULCAN-UG-2023", "VUG")],
  "UNRESOLVED", "different_epoch",
  "ULA's fact sheet and its October 2023 Vulcan user's guide give 550,000 lbf (2446.5 kN) sea level for the Vulcan "
  "installation. The 640,000 lbf is reported by secondary pages as a later Blue Origin uprate; the Blue Origin pages "
  "return HTTP 429, so neither the figure nor its date was opened.")
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
  [("100 %-57 % (SL)", "SRC-WEVOLVER-MERLIN", "T")],
  "UNRESOLVED", None, "The 'down to 40 %' claim has no source; the aggregator's 57 % cites none either.")
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
  [("348 s", "SRC-WEVOLVER-MERLIN", "T"), ("not printed", "SRC-SPACEX-FUG-2025", "T")],
  "UNRESOLVED", None, "SpaceX's guide prints no Isp; the aggregator's 348 s cites no source.")
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
   ("45,000 lbf per engine", "SRC-FIREFLY-MIRANDA-RR", "T")],
  "EXPLAINED", "rating_or_rounding",
  "180,072 lbf for four is 45,018 lbf each DERIVED: the release's 45,000 lbf is the same figure rounded. The 836.3 kN "
  "maximum was not opened.")
K("CF-COMMERCIAL-COM-16", "ENG-US-LIGHTNING", "performance.thrust_vac",
  [("70.1 kN (15,759 lbf)", "SRC-FIREFLY-ALPHA-PAGE", "T"), ("73.0 kN (16.4 klbf) max", "SRC-FIREFLY-PUG-5.2", "N")],
  "UNRESOLVED", "different_operating_point", "Only the nominal page figure was read; the payload guide's maximum was not opened.")
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
  [("12 MR-107N 300 N for landing", "SRC-AIRPORTTECH-PHX", "NF"), ("eight engines", "SRC-NBC-PHX", "NF")],
  "UNRESOLVED", None,
  "Neither fetched page says what DB-0 cited; the trade page's propulsion sentence is garbled ('eight 1.0lbf and 5.0lbf "
  "... engines and 12 68.0lbf ... thrusters'). A JPL or Lockheed document is needed.")
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
