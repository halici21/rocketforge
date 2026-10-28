"""H-1 200K pass (2026-10-28): two Chrysler Space Division reports on Saturn IB stage S-IB-4 (flown on AS-204),
opened for the 200K rating that CF-DB05-H1-THRUST held as secondary-only. Pages used were viewed as images."""
from ledger import A, D

H200 = "ENG-US-H-1-200K"
ST = "SRC-DB05-NTRS-19660014225"
PR = "SRC-DB05-NTRS-19680003903"

# ------------------------------------------------------------------ documents opened in this pass
D(ST, identifier="Chrysler Corporation Space Division, 25 Feb 1966; NASA-CR-74418; contract NAS8-4016; NTRS 19660014225",
  title="Saturn S-IB Stage Final Static Test Report, Stage S-IB-4", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; NASA contractor report; no restrictive notice on pages read",
  rights_class="PUBLIC_DOMAIN_GOV",
  note="174 pages; acceptance firings SA-32 (17 Jan 1966) and SA-33 (21 Jan 1966). Per-engine site and sea-level thrust "
       "and chamber pressure are in a 'Confidential Supplement' that is not part of this document.")
D(PR, identifier="Chrysler Corporation Space Division TR-P&VE-67-58, 20 Nov 1967; NASA-CR-91467; NTRS 19680003903",
  title="Final Flight Performance Prediction for Saturn AS-204 LM Propulsion System, S-IB-4 Stage", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; NASA contractor report; no restrictive notice on pages read",
  rights_class="PUBLIC_DOMAIN_GOV", note="38 pages; Table 5 (PDF p.19) viewed as image.")

# ------------------------------------------------------------------ S-IB-4 static test report, Section 2 (p.5, PDF p.14)
L2 = "S-IB-4 Final Static Test Report p.5 (PDF p.14) Section 2 'Engine Systems'; repeated in the Summary p.1 (PDF p.10) (viewed as image)"
A(H200, "performance.thrust_sl", None, "All engines produced thrust values within the specified limits of 200K±3 percent", 200000, "lb",
  {"environment": "UNSTATED (stage acceptance firing limit)", "stage": "S-IB-4", "tolerance": "±3 percent",
   "tests": "SA-32, SA-33"}, ST, L2, db0=None,
  note="Printed as '200K'. The rating the S-IB-4 engines were accepted against; the measured values are in the "
       "unavailable Confidential Supplement.")

# ------------------------------------------------------------------ AS-204 prediction, Table 5 (p.13, PDF p.19)
L5 = "TR-P&VE-67-58 p.13 (PDF p.19) Table 5 'Summary of Sea Level Test Data for the AS-204 Stage Engines', Average Engine row (viewed as image)"
_C = {"environment": "sea level", "stage": "S-IB-4 (eight engines, H-4058..H-4062, H-7062..H-7065)",
      "basis": "Rocketdyne engine logs (Past-76 program), average engine"}
A(H200, "performance.thrust_sl", None, "200.53", 200530, "Kips", _C, PR, L5, db0=None,
  note="Same row: static test analysis 201.57 (SA-32) and 201.36 (SA-33) kips; flight prediction 201.98 kips.")
A(H200, "performance.isp_sl", None, "262.60", 262.60, "sec", _C, PR, L5, db0=None)
A(H200, "propellants.mixture_ratio", None, "2.2168", 2.2168, "(-)", dict(_C, mr_basis="UNSTATED"), PR, L5, db0=None)
