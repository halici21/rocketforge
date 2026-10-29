"""YF-77 from the developer's 2017 keynote abstract (2026-10-29): IAC-17,C4,1,1,x41861 by Dayong Zheng, Beijing Aerospace
Propulsion Institute (BAPI), IAF archive abstract page. It repeats the IAC-13 abstract's 700 kN and O/F 5.5 but names the
environment ('in vacuum'), which the IAC-13 abstract (ledger_wave3.py, AS-DB05-CN-YF-77-003) leaves unstated."""
from ledger import A, D

YF77 = "ENG-CN-YF-77"
K17 = "SRC-IAC17-41861"
D(K17, identifier="IAC-17,C4,1,1,x41861 (Dayong Zheng, Beijing Aerospace Propulsion Institute), IAF archive abstract page",
  title="KEYNOTE: Development Status of the Cryogenic Oxygen/Hydrogen YF -77 Engine for Long-March 5", tier="B",
  rights_checked="'© IAF 2006-2026 all rights reserved' in the IAF archive page footer", rights_class="RESTRICTED_REFERENCE",
  note="The developing institute's author abstract (English as printed, typos kept). Full paper not reached.")

L = "IAC-17,C4,1,1,x41861 abstract"
A(YF77, "performance.thrust_vac", None, "each engine has a thrust rating of 700-kN in vacuum", 700, "kN",
  {"environment": "vacuum", "operating_point": "Rated"}, K17, L, db0=None)
A(YF77, "propellants.mixture_ratio", None, "at an oxidizer-to-fuel mixture ration (O/F) of 5.5", 5.5, "(-)", {}, K17, L, db0=None,
  note="'ration' as printed.")
A(YF77, "performance.summary", None,
  "with respect to previous Chinese cryogenic Oxygen/Hydrogen engine, such as YF-75 ... a factor of 9 on thrust, a factor of 2.7 "
  "on pressure, a factor of 9 on mass-flow rate", "text", "", {}, K17, L, db0=None,
  note="Ratios only; no absolute chamber pressure is printed, and the pressure station is not named.")
