"""SSME / RS-25 unread-download pass (2026-10-28): six documents DB-0.5 had fetched but not read. Three are mined;
three are identity-verified only because their values repeat documents already opened. Mined pages were viewed as
images (AIAA 97-2685 Figure 2, Biggs p.3) or read from the text layer (KSC fact sheet, one page of prose)."""
from ledger import A, D

E2 = "ENG-US-SSME-BLOCK-II"
EB1 = "ENG-US-SSME-BLOCK-I"
EP1 = "ENG-US-SSME-FPL-PHASE-I"
AI = "SRC-AIAA-97-2685"
KSC = "SRC-NASA-KSC-167449-SSMEPF06"
BIG = "SRC-ENGINEHISTORY-SSME1"

# ------------------------------------------------------------------ documents
D(AI, identifier="AIAA 97-2685; NASA-CR-205360; NTRS 19970028361 (Bradley, Boeing Rocketdyne, 33rd JPC, July 1997)",
  title="Space Shuttle Main Engine Off-Nominal Low Power Level Operation", tier="A",
  rights_checked="NTRS PUBLIC_USE_PERMITTED; cover prints 'For permission to copy or republish, contact the American "
                 "Institute of Aeronautics and Astronautics'", rights_class="RIGHTS_REVIEW_REQUIRED",
  note="DB-0 title 'unverified' -> verified from the cover. Companion of AIAA 97-2687 (same author, same Figure 1 schematic).")
D(KSC, identifier="NASA Facts FS-2005-09-030-KSC (Rev. 2006)", title="Space Shuttle Main Engine Processing Facility", tier="A",
  rights_checked="NASA fact sheet (US Government work); no copyright notice", rights_class="PUBLIC_DOMAIN_GOV",
  note="Two pages about the KSC processing facility; one sentence gives engine size and weight.")
D(BIG, identifier="Biggs, 'Space Shuttle Main Engine, The First Ten Years', Part 1: The Engine (AAS History Series Vol. 13, "
                  "1992, pp.69-122; presented 1989); reprint hosted by enginehistory.org as SSME1.pdf",
  title="Space Shuttle Main Engine - The First Ten Years, Part 1: The Engine (Robert E. Biggs)", tier="B",
  rights_checked="p.1 prints 'Copyright (c) 1992 by American Astronautical Society. This material is reprinted with permission of the AAS.'",
  rights_class="RIGHTS_REVIEW_REQUIRED", figures_rights="RESTRICTED_REFERENCE",
  note="Participant history by a Rocketdyne engineer, describing the engine of 1971-1981. Figure 3 is the same Rockwell "
       "propellant flow schematic (LC86C-4-1315) as other SSME documents; not registered again.")
D("SRC-NASA-3HO", identifier="HAER No. TX-116, Space Transportation System, pp.250-269 'Historical Overview' (nasa.gov files/3HO.pdf)",
  title="Historic American Engineering Record TX-116: SSME historical overview", tier="A",
  rights_checked="HAER documentation for NASA (US Government); no copyright notice on pages read", rights_class="PUBLIC_DOMAIN_GOV",
  note="Development history of the same HAER report as SRC-NASA-SSME-NPL-DOC. Its RPL figures (about 380,000 lb sea level, "
       "470,000 lb vacuum, p.254) repeat that record's p.248 values; not mined again.")
D("SRC-NASA-RS25-WEB", identifier="nasa.gov/reference/space-launch-system-rs-25-core-stage-engine (page code MSFC-12-2025-SLS-5637)",
  title="Space Launch System RS-25 Core Stage Engine (NASA reference page)", tier="A",
  rights_checked="NASA web page (US Government work)", rights_class="PUBLIC_DOMAIN_GOV",
  note="Its values (about 491,000 lbf at 104.5%, about 522,000 lbf at 111%) are the ones already recorded from the "
       "NASA fact sheet MSFC-03-2025-SLS-4963; not mined again.")
D("SRC-L3HARRIS-RS25-WEB", identifier="l3harris.com/all-capabilities/rs-25-engine", title="RS-25 Engine (L3Harris capabilities page)",
  tier="A", rights_checked="L3Harris web page; site copyright; no reuse licence", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Specification box repeats the L26301 spec sheet (109%: 512,300 lb vacuum, 418,000 lb sea level, 2,994 psia, 452 / 366 s, "
       "69:1, O/F 6.0) except weight, printed here as 7,775 lb against the sheet's 7,774 lb; added to CF-DB05-RS25-MASS as a claim.")

# ------------------------------------------------------------------ AIAA 97-2685 Figure 2 (p.2, PDF p.4)
LF2 = "AIAA 97-2685 p.2 (PDF p.4) Figure 2 'The SSME is the First Reusable Large, Liquid Rocket Engine' (viewed as image)"
_A = {"configuration": "UNSTATED (1997 paper; 3006 psia at RPL is the pre-large-throat value)"}
A(EB1, "performance.thrust_vac", "OP-RPL", "Rated power level (RPL) 100% 470,000 lbs", 470000, "lb", dict(_A, environment="UNSTATED"), AI, LF2, db0=None)
A(EB1, "performance.pc", "OP-RPL", "Rated chamber pressure 3006 psia", 3006, "psia", _A, AI, LF2, db0=None,
  note="Same value as AIAA 97-2687 p.1-2.")
A(EB1, "performance.isp_vac", "OP-RPL", "Specific impulse at altitude 453.5 seconds", 453.5, "s", dict(_A, environment="altitude"), AI, LF2, db0=None)
A(EB1, "performance.throttle_range", None, "Throttle range 65 to 109%", "65 -> 109", "% RPL", _A, AI, LF2, db0=None,
  note="The paper's tests ran the engine down to 17% RPL (off-nominal).")
A(EB1, "mechanical.mass", None, "Weight 7000 lbs", 7000, "lb", dict(_A, definition="UNSTATED"), AI, LF2, db0=None)
A(EB1, "life.design", None, "Design life 27,000 seconds, 55 starts", "27,000 / 55", "s / starts", _A, AI, LF2, db0=None)

# ------------------------------------------------------------------ KSC fact sheet (p.1)
A(E2, "mechanical.mass", None, "weighs approximately 7,000 pounds (3,150 kilograms)", 7000, "lb",
  {"configuration": "UNSTATED (shuttle main engine, 2006 revision)", "definition": "UNSTATED"}, KSC, "FS-2005-09-030-KSC p.1 (text layer)", db0=None,
  note="Same sentence: 14 feet (4.2 meters) long and 7.5 feet (2.25 meters) in diameter at the end of its nozzle.")

# ------------------------------------------------------------------ Biggs, Part 1 (pp.2-3)
LB3 = "Biggs Part 1 p.3 (viewed as image)"
_B = {"configuration": "SSME as designed and developed 1971-1981 (operating point not stated)"}
A(EP1, "performance.thrust_vac", "OP-RPL", "It produces a rated thrust of 470,000 pounds (vacuum)", 470000, "lb", dict(_B, environment="vacuum"),
  BIG, "Biggs Part 1 p.2 'The Engine' (text layer)", db0=None)
A(EP1, "performance.isp_vac", None, "a specific impulse greater than 453 pounds of thrust per pound of propellant per second", "> 453", "s",
  _B, BIG, "Biggs Part 1 p.2 'The Engine' (text layer)", db0=None)
A(EP1, "pumps.HPFTP.speed_rpm", None, "The three-stage centrifugal pump, operating at 35,000 rpm", 35000, "rpm", _B, BIG, LB3, db0=None,
  note="Same paragraph: discharge 'over 6,000 psia'; LPFTP turboinducer 15,000 rpm, inlet 30 psia, discharge over 250 psia.")
A(EP1, "pumps.HPOTP.speed_rpm", None, "The dual inlet single stage centrifugal main impeller, operating at almost 30,000 rpm", "almost 30,000", "rpm",
  _B, BIG, LB3, db0=None, note="Same paragraph: discharge about 4,500 psia; LPOTP 5,000 rpm, inlet 100 psia, discharge over 400 psia.")
A(EP1, "cycle.flow_split", None, "80 percent of the fuel (LH2) is burned in the two preburners with 12 percent of the oxidizer (LOX)",
  "80% fuel / 12% oxidizer to preburners", "", _B, BIG, LB3, db0=None)
