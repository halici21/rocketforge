"""RS-25 / SSME evidence opened in DB-0.5 (session 2026-10-08)."""
from ledger import A, D, S, T, C

E2 = "ENG-US-SSME-BLOCK-II"
E2A = "ENG-US-SSME-BLOCK-IIA"

# ---- documents (identity verified from the opened document itself) ----
D("SRC-L3HARRIS-RS25-SPEC", identifier="L3Harris L26301 (07/2024)", title="RS-25 Propulsion System (spec sheet)",
  tier="A", rights_checked="(c) 2024 L3Harris Technologies; 'NON-EXPORT CONTROLLED' notice p.2; no reuse licence stated",
  rights_class="VALUES_WITH_ATTRIBUTION", figures_rights="RESTRICTED_REFERENCE")
D("SRC-NASA-RS25-FS2015", identifier="FS-2015-07-064-MSFC", title="NASAfacts: Space Launch System RS-25 Core Stage Engines",
  tier="A", rights_checked="NASA publication (US Government work); no copyright notice", rights_class="PUBLIC_DOMAIN_GOV")
D("SRC-NASA-RS25-FS2025", identifier="MSFC-03-2025-SLS-4963", title="NASAfacts: SLS RS-25 Core Stage Engine",
  tier="A", rights_checked="NASA publication (US Government work); no copyright notice", rights_class="PUBLIC_DOMAIN_GOV")
D("SRC-IBIBLIO-SSMEOVERVIEW", identifier="JSC-19041 (SSME Overview SB1.1, Basic Rev F, 07/07/03)",
  title="Shuttle Booster systems brief: SSME Overview (JSC-19041)", tier="A",
  rights_checked="NASA JSC training document; no copyright notice on pages read; hosted by ibiblio (mirror, not NASA)",
  rights_class="PUBLIC_DOMAIN_GOV", note="DB-0 'JSC-19041 (unverified)' now VERIFIED from page header.")
D("SRC-ENGINEHISTORY-SSMEORIENT-1998", identifier="BC98-04 (Rocketdyne, June 1998)",
  title="Space Transportation System Training Data: Space Shuttle Main Engine Orientation", tier="A",
  rights_checked="Every page stamped 'BOEING PROPRIETARY'; cover 'Use this data for training purposes only'; hosted by enginehistory.org",
  rights_class="RESTRICTED_REFERENCE", figures_rights="RESTRICTED_REFERENCE",
  note="Manufacturer primary. Values usable as research reference with attribution; figures not reproducible. BC98-04 identifier VERIFIED (cover).")
D("SRC-AIAA-97-2687", identifier="AIAA 97-2687; NTRS 19970028362", title="Start with off-nominal propellant inlet pressures (Bradley, Rocketdyne)",
  tier="A", rights_checked="NTRS determination GOV_PUBLIC_USE_PERMITTED, but p.1 prints 'Copyright 1997 by the AIAA, Inc. All rights reserved.'",
  rights_class="RIGHTS_REVIEW_REQUIRED", note="Printed title differs from DB-0 registry title ('Space Shuttle Main Engine Start with Off-Nominal...' is the NTRS title).")
D("SRC-NTRS-20030005845", identifier="AIAA 2002-3581; NTRS 20030005845",
  title="Understanding and Resolution of the Block 2 SSME, STS-104 Engine Shutdown Pressure Surge In-Flight Anomaly (Greene & Kynard, NASA MSFC)",
  tier="A", rights_checked="p.2: '(c) 2002 AIAA ... No copyright is asserted under Title 17, U.S. Code'; NTRS PUBLIC_USE_PERMITTED",
  rights_class="PUBLIC_DOMAIN_GOV")
D("SRC-NTRS-19860012108", identifier="NTRS 19860012108",
  title="Performance predictions for an SSME configuration with an enlarged throat", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED", rights_class="PUBLIC_DOMAIN_GOV")
D("SRC-NTRS-20180006338", identifier="NTRS 20180006338",
  title="Overview of RS-25 Adaptation Hot-Fire Test Series for SLS, Status and Lessons Learned (Vetcha et al.)", tier="A",
  rights_checked="NTRS PUBLIC_USE_PERMITTED; Jacobs/ESSCA contractor authors", rights_class="VALUES_WITH_ATTRIBUTION")

# ---- assertions: Block II / RS-25D (SLS-adapted) ----
A(E2, "performance.thrust_sl", "OP-109", "418,000 lb", 418000, "lb", {"environment": "sea_level", "power_level_pct": 109},
  "SRC-L3HARRIS-RS25-SPEC", "p.1 'SPECIFICATIONS' box, 'Maximum Thrust: (109% Power Level) At Sea Level'", db0=None,
  note="Spec sheet describes the SLS RS-25; Block II hardware adapted for SLS.")
A(E2, "performance.thrust_vac", "OP-109", "512,300 lb", 512300, "lb", {"environment": "vacuum", "power_level_pct": 109},
  "SRC-L3HARRIS-RS25-SPEC", "p.1 SPECIFICATIONS, 'In Vacuum'", db0=("ENG-US-SSME-BLOCK-II", 9, "CONFIRMED"))
A(E2, "performance.isp_vac", "OP-109", "452.3 sec", 452.3, "s", {"environment": "vacuum", "isp_basis": "engine (unstated)"},
  "SRC-L3HARRIS-RS25-SPEC", "p.1 SPECIFICATIONS, 'Specific Impulse In Vacuum'", db0=None,
  note="Fills DB-0 missing 'performance.isp_vac'. Operating point not printed next to Isp; listed under the 109% sheet.")
A(E2, "performance.pc", "OP-109", "2,994 psia", 2994, "psia", {"pressure_basis": "abs", "pc_station": "UNKNOWN"},
  "SRC-L3HARRIS-RS25-SPEC", "p.1 SPECIFICATIONS, 'Pressures ... Chamber Pressure'", db0=("ENG-US-SSME-BLOCK-II", 16, "CONFIRMED"),
  note="Power level not printed beside the pressure block; sheet header is 109%.")
A(E2, "pumps.HPFTP.discharge_pressure", "OP-109", "6,276 psia", 6276, "psia", {"pressure_basis": "abs"},
  "SRC-L3HARRIS-RS25-SPEC", "p.1 'Hydrogen Pump Discharge'", db0=("ENG-US-SSME-BLOCK-II", 23, "CONFIRMED"))
A(E2, "pumps.HPOTP.discharge_pressure", "OP-109", "7,268 psia", 7268, "psia", {"pressure_basis": "abs"},
  "SRC-L3HARRIS-RS25-SPEC", "p.1 'Oxygen Pump Discharge'", db0=("ENG-US-SSME-BLOCK-II", 24, "CONFIRMED"),
  note="Which HPOTP stage (main vs preburner boost) is not stated; 7,268 exceeds the Block IIA main-pump figure, so it is likely the boost-stage discharge [INFERRED, not promoted].")
A(E2, "pumps.HPFTP.power", None, "71,140 hp", 71140, "hp", {}, "SRC-L3HARRIS-RS25-SPEC", "p.1 'Power: High Pressure Pumps Hydrogen'",
  db0=("ENG-US-SSME-BLOCK-II", 29, "CORRECTED"), note="DB-0 held 76,000 hp from a news summary (SECONDARY_CLAIM).")
A(E2, "pumps.HPOTP.power", None, "23,260 hp", 23260, "hp", {}, "SRC-L3HARRIS-RS25-SPEC", "p.1 'Power: High Pressure Pumps Oxygen'",
  db0=("ENG-US-SSME-BLOCK-II", 34, "CONFIRMED_PRIMARY"), note="Same number DB-0 held from Wikipedia; now primary. DB-0 news value 26,800 hp is not supported.")
A(E2, "nozzle.area_ratio", None, "69:1", 69, ":1", {"definition": "exit/throat"}, "SRC-L3HARRIS-RS25-SPEC", "p.1 'Area Ratio Exit/Throat'",
  db0=("ENG-US-SSME-BLOCK-II", 54, "CONFIRMED"))
A(E2, "propellants.mixture_ratio", None, "6.03:1", 6.03, ":1", {"mr_basis": "unstated (oxidizer/fuel)"}, "SRC-L3HARRIS-RS25-SPEC",
  "p.1 'Mixture Ratio Oxidizer/Fuel'", db0=("ENG-US-SSME-BLOCK-II", 6, "CONFIRMED"))
A(E2, "performance.throttle_range", None, "67% - 109%", "67-109", "%", {"reference": "RPL"}, "SRC-L3HARRIS-RS25-SPEC", "p.1 'Throttle Range'",
  db0=("ENG-US-SSME-BLOCK-II", 18, "CONFIRMED"))
A(E2, "mechanical.mass_dry", None, "7,774 lb", 7774, "lb", {}, "SRC-L3HARRIS-RS25-SPEC", "p.1 'Weight Dry'", db0=("ENG-US-SSME-BLOCK-II", 57, "CONFIRMED"))
A(E2, "mechanical.dimensions", None, "168 in. long 96 in. wide", "168 x 96", "in", {}, "SRC-L3HARRIS-RS25-SPEC", "p.1 'Dimensions'", db0=None)
A(E2, "performance.thrust", "OP-109", "512,000 pounds", 512000, "lb", {"environment": "vacuum"}, "SRC-NASA-RS25-FS2015",
  "p.2 body text 'will produce 512,000 pounds of vacuum thrust'; facts box 'Thrust ... 512,000 pounds'", db0=("ENG-US-SSME-BLOCK-II", 10, "CONFIRMED"),
  note="Facts box omits the environment; body text says vacuum.")
A(E2, "mechanical.mass", None, "7,775 lbs.", 7775, "lb", {}, "SRC-NASA-RS25-FS2015", "p.2 'RS-25 Engine Facts: Size/Weight ... 7,775 lbs.'", db0=None)
A(E2, "performance.thrust_vac", "OP-109", "512,300 lbs. (vacuum)", 512300, "lb", {"environment": "vacuum"}, "SRC-NASA-RS25-FS2025", "p.1 'RS-25 Engine Facts'", db0=None)
A(E2, "performance.thrust_sl", "OP-109", "418,000 lbs. (sea level)", 418000, "lb", {"environment": "sea_level"}, "SRC-NASA-RS25-FS2025", "p.1 'RS-25 Engine Facts'", db0=None)
A(E2, "mechanical.mass", None, "3,515 kg (7,750 lbs.)", 7750, "lb", {}, "SRC-NASA-RS25-FS2025", "p.1 'RS-25 Engine Facts: Weight'", db0=None,
  note="Differs from 7,774 lb (L3Harris) and 7,775 lbs (FS-2015): see conflict CF-DB05-RS25-MASS.")
A(E2, "performance.thrust", "OP-104.5", "approximately 491,000 lbf", 491000, "lbf", {"environment": "UNSTATED"}, "SRC-NASA-RS25-FS2025",
  "p.2 col.1 'routinely operated in flight at 104.5%, or approximately 491,000 lbf'", db0=("ENG-US-SSME-BLOCK-II", 11, "CONFIRMED_OTHER_SOURCE"),
  note="Environment not printed; 512,300 x 104.5/109 = 491,150 so it matches the vacuum scale [DERIVED check, not a promotion].")
A(E2, "performance.thrust", "OP-111", "approximately 522,000 lbf", 522000, "lbf", {"environment": "UNSTATED"}, "SRC-NASA-RS25-FS2025",
  "p.2 col.1 'tested up to 111% thrust or approximately 522,000 lbf'", db0=None)
A(E2, "pumps.HPFTP.power", None, "69,000 horsepower", 69000, "hp", {}, "SRC-NTRS-20180006338", "p.2 para.1", db0=None,
  note="Conflicts with L3Harris 71,140 hp; neither prints an operating point (CF-DB05-RS25-PUMPPOWER).")
A(E2, "pumps.HPOTP.power", None, "25,000 horsepower", 25000, "hp", {}, "SRC-NTRS-20180006338", "p.2 para.1", db0=None)
A(E2, "history.block_II_first_flight", None, "STS-104, launched July 2001 ... first flight of a single Block 2 SSME", "STS-104 (2001-07)", "",
  {}, "SRC-NTRS-20030005845", "p.2 Abstract; p.3 Introduction (engine unit 2051)", db0=None, note="Fills DB-0 missing field history.block_II_first_flight.")
A(E2, "identity.block_package", None,
  "Two Transfer Tube Phase 2+ Powerhead; Single-Tube Heat Exchanger; Large Throat Main Combustion Chamber; Advanced Technology HPOTP; Advanced Technology HPFTP (HPFTP/AT)",
  "list", "", {}, "SRC-NTRS-20030005845", "p.3 Introduction, bullet list", db0=("ENG-US-SSME-BLOCK-II", 1, "CONFIRMED"))
A(E2, "identity.block_definition", None, "the newest Block II engine adds a new Pratt & Whitney high-pressure fuel turbopump (HPFTP) to the Block IIA engine",
  "text", "", {}, "SRC-IBIBLIO-SSMEOVERVIEW", "JSC-19041 p.1.1-2 §1.1.2", db0=("ENG-US-SSME-BLOCK-II", 0, "CONFIRMED_PRIMARY"))
A(E2, "identity.block_IIA_change", None, "The modification between the Block IA SSME and the Block IIA was a larger throat MCC", "text", "", {},
  "SRC-IBIBLIO-SSMEOVERVIEW", "JSC-19041 p.1.1-2 §1.1.2", db0=("ENG-US-SSME-BLOCK-II", 2, "SOURCE_CORRECTED"),
  note="DB-0 attributed this to NTRS 20030005845; that paper lists the Large Throat MCC in the Block 2 package but does not state the IA->IIA step.")
A(E2, "performance.pc", "OP-104.5", "approximately 2,870 psia", 2870, "psia", {"pressure_basis": "abs", "station": "MCC"}, "SRC-IBIBLIO-SSMEOVERVIEW",
  "JSC-19041 p.1.1-1 §1.1.1 para.3", db0=("ENG-US-SSME-BLOCK-II", 15, "CONFIRMED"))
A(E2, "performance.pc", "OP-RPL", "approximately 2,747 psia", 2747, "psia", {"pressure_basis": "abs", "station": "MCC"}, "SRC-IBIBLIO-SSMEOVERVIEW",
  "JSC-19041 p.1.1-1 §1.1.1 paras.2-3", db0=("ENG-US-SSME-BLOCK-II", 13, "CONFIRMED"))
A(E2, "preburners.pressure", None, "high pressure (5,000 psia)", 5000, "psia", {}, "SRC-IBIBLIO-SSMEOVERVIEW", "JSC-19041 p.1.1-1 §1.1.1 para.3",
  db0=("ENG-US-SSME-BLOCK-II", 44, "CONFIRMED_PRIMARY"), note="Generic round number in an overview; not a measured preburner Pc.")
A(E2, "cooling.coolant", None, "Hydrogen fuel is used to cool all combustion devices directly exposed to high-temperature combustion products", "text", "",
  {}, "SRC-IBIBLIO-SSMEOVERVIEW", "JSC-19041 p.1.1-1 §1.1.1 para.3", db0=("ENG-US-SSME-BLOCK-II", 53, "SOURCE_ADDED"))
A(E2, "performance.throttle_range_shuttle", None, "67 to 104 percent of the RPL; FPL 109 percent of RPL via SPEC 51", "67-104 (109 FPL)", "%", {},
  "SRC-IBIBLIO-SSMEOVERVIEW", "JSC-19041 p.1.1-1 §1.1.1 para.2", db0=None)
A(E2, "mechanical.gimbal", None, "±10.5° for pitch and ±8.5° for yaw", "10.5/8.5", "deg", {}, "SRC-IBIBLIO-SSMEOVERVIEW", "JSC-19041 p.1.1-1 §1.1.1 para.2", db0=None)
# Rejected / not promoted from JSC-19041 for Block II
A(E2, "nozzle.area_ratio", None, "77.5 to 1", 77.5, ":1", {}, "SRC-IBIBLIO-SSMEOVERVIEW", "JSC-19041 p.1.1-1 §1.1.1 para.3", db0=None,
  disposition="REJECTED_FOR_VARIANT", note="Pre-large-throat value (NTRS 19860012108 p.8) printed in a 2003 Block II brief; contradicts the brief's own §1.1.2. Kept as evidence of stale text.")
A(E2, "performance.thrust_vac", "OP-RPL", "approximately 470,000 lbs", 470000, "lb", {"environment": "vacuum"}, "SRC-IBIBLIO-SSMEOVERVIEW",
  "JSC-19041 p.1.1-1 §1.1.1 para.2", db0=None, note="Rated-power-level reference thrust; sea level 'approximately 375,000 lbs.'")
A(E2, "performance.thrust_sl", "OP-RPL", "approximately 375,000 lbs.", 375000, "lb", {"environment": "sea_level"}, "SRC-IBIBLIO-SSMEOVERVIEW",
  "JSC-19041 p.1.1-1 §1.1.1 para.2", db0=None)

# ---- Block IIA (Rocketdyne BC98-04 slide 19 / p.25 and pp.24-27 text) ----
for f, v, u, loc in [
    ("pumps.LPFTP.speed_rpm", "15,519 rpm", 15519, "p.25 (slide 19) LPFTP callout"),
    ("pumps.HPFTP.speed_rpm", "34,311 rpm", 34311, "p.25 (slide 19) HPFTP callout"),
    ("pumps.LPOTP.speed_rpm", "5,018 rpm", 5018, "p.25 (slide 19) LPOTP callout"),
    ("pumps.HPOTP.speed_rpm", "22,250 rpm", 22250, "p.25 (slide 19) HPOTP callout"),
    ("performance.pc", "2,871 psia", 2871, "p.25 (slide 19) MCC callout"),
    ("preburners.FPB.chamber", "1,310°F 4,793 psia", "1310 F / 4793", "p.25 (slide 19) fuel preburner callout"),
    ("preburners.OPB.chamber", "871°F 4,812 psia", "871 F / 4812", "p.25 (slide 19) oxidizer preburner callout"),
    ("turbines.HPFT.discharge", "1,087°F 3,091 psia 149 lb/sec", "1087 F / 3091 / 149", "p.25 (slide 19) fuel-side hot gas callout"),
    ("turbines.HPOT.discharge", "728°F 3,099 psia 68 lb/sec", "728 F / 3099 / 68", "p.25 (slide 19) oxidizer-side hot gas callout"),
    ("feed.LH2_inlet", "-423°F 30 psia 155 lb/sec", "-423 F / 30 / 155", "p.25 (slide 19) hydrogen inlet callout"),
    ("feed.LOX_inlet", "-297°F 100 psia 934 lb/sec", "-297 F / 100 / 934", "p.25 (slide 19) oxygen inlet callout"),
    ("pumps.HPOTP_boost.discharge", "-258°F 6,939 psia 92 lb/sec", "-258 F / 6939 / 92", "p.25 (slide 19) HPOTP preburner-pump callout"),
    ("pumps.LPOTP.discharge", "-291°F 421 psia 1,120 lb/sec", "-291 F / 421 / 1120", "p.25 (slide 19) LPOTP discharge callout"),
]:
    A(E2A, f, "OP-104.5", v, u, "as printed", {"power_level_pct": 104.5, "configuration": "Block IIA"}, "SRC-ENGINEHISTORY-SSMEORIENT-1998",
      loc, db0=None, status="DIGITISED",
      note="Read visually from the annotated schematic (VIEWED). Block IIA, not Block II: Block II replaces the HPFTP, so these do not transfer.")
A(E2A, "propellants.mixture_ratio", None, "6.032 to 1", 6.032, ":1", {"mr_basis": "main combustion chamber"}, "SRC-ENGINEHISTORY-SSMEORIENT-1998",
  "p.24 'Propellant Flow Analysis (1 of 3)'", db0=None)
A(E2A, "cooling.fuel_split", None, "MCC coolant 19%; nozzle tubes 27.5%; CCV bypass 48.5%; FPB 50% vs OPB 26% (of fuel)", "19/27.5/48.5; 50/26", "%",
  {}, "SRC-ENGINEHISTORY-SSMEORIENT-1998", "p.26 'Propellant Flow Analysis (2 of 3)' Fuel Flow", db0=("ENG-US-SSME-BLOCK-II", 51, "CONFIRMED_PRIMARY_OTHER_VARIANT"))
A(E2A, "cooling.channel_counts", None, "430 MCC coolant channels; 1,080 nozzle tubes", "430/1080", "count", {}, "SRC-ENGINEHISTORY-SSMEORIENT-1998",
  "p.26 Fuel Flow", db0=None)
A(E2A, "propellants.preburner_split", None, "76 percent of the hydrogen flow and 11 percent of the oxygen flow are injected into two preburners", "76/11", "%",
  {}, "SRC-ENGINEHISTORY-SSMEORIENT-1998", "p.24 General", db0=None)
A(E2A, "control.valve_roles", None, "The FPOV is driven alone to maintain mixture ratio in the MCC, while the OPOV is driven with the FPOV to increase or decrease thrust",
  "text", "", {}, "SRC-ENGINEHISTORY-SSMEORIENT-1998", "p.27 Engine Control", db0=("ENG-US-SSME-BLOCK-II", 48, "CONFIRMED_PRIMARY_OTHER_VARIANT"),
  note="DB-0 (Wikipedia) said OPOV controls power level alone; primary text says OPOV+FPOV together set thrust (assertion 49 CORRECTED in substance).")
A(E2A, "control.ccv_schedule", None, "CCV between half open at 67 percent thrust (MPL) and fully open at 100 percent thrust (and above)", "text", "", {},
  "SRC-ENGINEHISTORY-SSMEORIENT-1998", "p.27 Engine Control", db0=None)
