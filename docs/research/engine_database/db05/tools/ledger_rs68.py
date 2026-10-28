"""RS-68 baseline from NTRS (2026-10-29): the 1999 IAF Congress slides by Rocketdyne (NTRS 20000025317, scanned, no
text layer; the table slide was rendered and read). The 2009 'Ares V and RS-68B' paper (NTRS 20090014109, already
recorded in ledger_wave2.py) was re-read for its RS-68A thrust increment, which goes into the RS-68 conflict's
explanation rather than an RS-68A assertion."""
from ledger import A, D

RS68 = "ENG-US-RS-68"
M99 = "SRC-DB05-NTRS-20000025317"
D(M99, identifier="NTRS 20000025317 (50th IAF Congress, Amsterdam, 11-12 October 1999)",
  title="Liquid Rocket Propulsion: RS-68 & Linear Aerospike (Terry Murphy, Rocketdyne Propulsion & Power, The Boeing Company)",
  tier="B", rights_checked="NTRS determination GOV_PUBLIC_USE_PERMITTED, but the slides are Boeing-authored; not export controlled",
  rights_class="RIGHTS_REVIEW_REQUIRED",
  note="64 scanned slides without a text layer; the 'RS-68 Engine Performance Baseline' slide (PDF p.11) was rendered and read.")

L11 = "PDF p.11 'RS-68 Engine Performance Baseline' table (rendered scan)"
_R = {"configuration": "RS-68 baseline (1999, before first flight)", "operating_point": "Rated"}
A(RS68, "performance.thrust_vac", None, "Thrust, vac, klbf 745 (Rated) / 440 (Throttled)", 745, "klbf", _R, M99, L11, db0=None)
A(RS68, "performance.thrust_sl", None, "Thrust, s/l, klbf 650 (Rated) / N/A (Throttled)", 650, "klbf", _R, M99, L11, db0=None)
A(RS68, "performance.pc", None, "Chamber pressure, psia 1410 (Rated) / 836 (Throttled)", 1410, "psia", dict(_R, pc_station="UNSTATED"),
  M99, L11, db0=None)
A(RS68, "propellants.mixture_ratio", None, "Engine mixture ratio 6.0", 6.0, "(-)", _R, M99, L11, db0=None)
A(RS68, "performance.isp_vac", None, "Isp, vacuum, sec 410 Avg", 410, "s", dict(_R, basis="average"), M99, L11, db0=None)
A(RS68, "nozzle.area_ratio", None, "Expansion ratio 21.5", 21.5, ":1", _R, M99, L11, db0=None)
A(RS68, "mechanical.mass", None, "Weight, lb < 15,000", "< 15000", "lb", _R, M99, L11, db0=None)
