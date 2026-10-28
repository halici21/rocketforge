"""J-2 AS-501 flight pass (2026-10-28): Rocketdyne R-7450-1, the J-2 performance analysis of flight AS-501
(Apollo 4), S-II and S-IVB stages. Its tables are flight reconstructions, not ratings; read from rendered pages."""
from ledger import A, D

J2 = "ENG-US-J-2"
R = "SRC-DB05-NTRS-19680026222"

# ------------------------------------------------------------------ document opened in this pass
D(R, identifier="Rocketdyne R-7450-1, 17 May 1968; NASA-CR-61991; contract NAS8-19; NTRS 19680026222",
  title="J-2 Engine Performance Analysis of Flight AS-501 (Apollo 4), S-II and S-IVB Stages", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; contractor report under NASA contract; "
                 "no reproduction notice found in the extracted text (poor OCR)",
  rights_class="VALUES_WITH_ATTRIBUTION",
  note="320-page scan. Summary (PDF p.22), Table 10 (PDF p.78), Table 11 (PDF p.81), Table 16 (PDF p.122) and "
       "Table 28 (PDF p.266) were viewed as images. Engines: S-II J2026, J2043, J2030, J2035, J2028; S-IVB J2031.")

# ------------------------------------------------------------------ S-II stage, Table 16 (p.107, PDF p.122)
L16 = "R-7450-1 p.107 (PDF p.122) Table 16 'Reconstructed Average Engine Performance' (viewed as image)"
_S2_HI = {"basis": "flight reconstruction", "flight": "AS-501", "stage": "S-II (five-engine average)",
          "region": "High Mixture Ratio Region (156 to 426 seconds)", "environment": "flight altitude"}
_S2_LO = dict(_S2_HI, region="50 Seconds After Mixture Ratio Cutback to Cutoff Signal (476 to 520 seconds)")
_NOTE16 = "A flight reconstruction of the AS-501 engines, not a rating; the report names no rating for them."
A(J2, "performance.thrust_vac", None, "225,362.8", 225362.8, "pounds", _S2_HI, R, L16, db0=None, note=_NOTE16)
A(J2, "propellants.mixture_ratio", None, "5.45114", 5.45114, "", _S2_HI, R, L16, db0=None)
A(J2, "performance.isp_vac", None, "424.46", 424.46, "seconds", _S2_HI, R, L16, db0=None)
A(J2, "performance.thrust_vac", None, "187.236", 187236, "pounds", _S2_LO, R, L16, db0=None,
  note="Printed '187.236' in a column of pounds; the per-engine rows (183,097 to 192,195) show it is 187,236.")
A(J2, "propellants.mixture_ratio", None, "4.67886", 4.67886, "", _S2_LO, R, L16, db0=None)
A(J2, "performance.isp_vac", None, "429.17", 429.17, "seconds", _S2_LO, R, L16, db0=None)

# ------------------------------------------------------------------ S-IVB stage, Table 28 (p.248, PDF p.266)
L28 = "R-7450-1 p.248 (PDF p.266) Table 28 'Average Engine Reconstructed Performance' (viewed as image)"
_S4 = {"basis": "flight reconstruction", "flight": "AS-501", "stage": "S-IVB (engine J2031)",
       "region": "High Mixture Ratio Region, First Burn", "environment": "flight altitude"}
A(J2, "performance.thrust_vac", None, "223,278", 223278, "pounds", _S4, R, L28, db0=None, note=_NOTE16)
A(J2, "propellants.mixture_ratio", None, "5.5231", 5.5231, "o/f", _S4, R, L28, db0=None)
A(J2, "performance.isp_vac", None, "423.28", 423.28, "seconds", _S4, R, L28, db0=None)

# ------------------------------------------------------------------ engine J2026, Table 11 (p.71, PDF p.81)
L11 = "R-7450-1 p.71 (PDF p.81) Table 11 'Mainstage Performance, Engine J2026 (No. 1)' (viewed as image)"
A(J2, "performance.pc", None, "776.3", 776.3, "psia",
  {"pc_station": "UNSTATED (row 'Thrust Chamber Pressure'; the report's figures plot 'Thrust Chamber Injector End Pressure')",
   "basis": "engine acceptance test, standard altitude conditions", "engine_serial": "J2026"}, R, L11, db0=None,
  note="One engine's acceptance value, beside its 228,766 lb thrust and 5.526 mixture ratio. p.69 says flight chamber "
       "pressure was calculated from acceptance thrust coefficients and the measured value read about 5 psi low.")
