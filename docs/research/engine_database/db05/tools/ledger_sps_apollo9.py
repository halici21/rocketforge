"""Apollo 9 SPS pass (2026-10-28): TRW's final flight evaluation of the CSM 104 service propulsion system, a Block II
spacecraft (engine S/N 62), opened for the Block II values CF-DB05-SPS-THRUST lacked and for the helium regulation
value in CF-DB05-SPS-REG. Pages used were viewed as images."""
from ledger import A, D

E = "ENG-US-AJ10-137"
A9 = "SRC-APOLLO9-SPS-FFE"

# ------------------------------------------------------------------ document opened in this pass
D(A9, identifier="TRW 11176-H311-R0-00, 4 Aug 1969 (R. J. Smith, TRW Propulsion Technology Section); NASA-TM-X-62907; "
                 "Apollo 9 mission report supplement 5; NTRS 19700019020 (copy read from ibiblio.org/apollo)",
  title="Apollo 9 CSM 104 Service Propulsion System Final Flight Evaluation", tier="A",
  rights_checked="NTRS 19700019020 GOV_PUBLIC_USE_PERMITTED; export control NO (EAR/ITAR NO); distribution PUBLIC; "
                 "TRW report prepared for NASA MSC, no restrictive notice on pages read",
  rights_class="PUBLIC_DOMAIN_GOV",
  note="78 pages. Text pp.1-41 and Tables 2, 5, 6 viewed as images; Figures 1-24 (PDF pp.55-78) are time-history plots, "
       "not schematics, so the DB-0 lead SCH-AJ10-137-R2-2 'Apollo 9 SPS pressurization system' has no drawing here.")

_C = {"configuration": "Block II (CSM 104, engine S/N 62, injector S/N 120)", "flight": "Apollo 9, SPS burns 2 and 3"}

# ------------------------------------------------------------------ standard inlet conditions performance (p.25, PDF p.30; summary p.3, PDF p.8)
LS = "TRW 11176-H311-R0-00 p.25 (PDF p.30) 'Engine Performance at Standard Inlet Conditions'; repeated in the Summary p.3 (PDF p.8) (viewed as image)"
_S = dict(_C, environment="vacuum (flight, corrected to standard inlet conditions)",
          basis="flight reconstruction (steady-state analysis), not a rating")
A(E, "performance.thrust_vac", None, "The standard inlet conditions thrust ... were 20728 pounds", 20728, "lb", _S, A9, LS, db0=None,
  note="0.9% above the preflight engine model built from acceptance test data, outside the ±0.73% (3-sigma) tolerance.")
A(E, "performance.isp_vac", None, "specific impulse ... 313.9 seconds", 313.9, "s", _S, A9, LS, db0=None)
A(E, "propellants.mixture_ratio", None, "propellant mixture ratio ... 1.587", 1.587, "(-)", _S, A9, LS, db0=None)
A(E, "performance.thrust_vac", None, "slightly greater than the upper acceptance test specification limit of 20705 pounds", 20705, "lb",
  dict(_C, environment="vacuum (standard inlet conditions)", basis="upper acceptance test specification limit"), A9, LS, db0=None,
  note="Only the upper limit is printed; the nominal specification value is not.")
A(E, "feed.engine_inlet_pressure", None, "Oxidizer interface pressure, psia 162 / Fuel interface pressure, psia 169", "162 / 169", "psia",
  dict(_C, definition="standard inlet conditions (oxidizer / fuel), 70 °F, thrust acceleration 1.0 lbf/lbm"), A9, LS, db0=None)

# ------------------------------------------------------------------ predicted Isp (p.26, PDF p.31) and Table 2 (p.42, PDF p.47)
A(E, "performance.isp_vac", None, "The predicted specific impulse at standard inlet conditions, as extrapolated from the ground test data was 313.0 seconds",
  313.0, "s", dict(_C, environment="vacuum (standard inlet conditions)", basis="preflight prediction from sea-level injector acceptance tests and AEDC conversion factors",
                   tolerance="±1.59 s (3-sigma)"), A9, "p.26 (PDF p.31) (viewed as image)", db0=None,
  note="Table 2 prints the same engine constant: Isp_vac (Engine No. 62) = 313.0 lbf-sec/lbm.")
LT2 = "p.42 (PDF p.47) Table 2 'CSM 104 SPS Engine and Feed System Characteristics' (viewed as image)"
A(E, "performance.cstar", None, "C*S.C. (Engine No. 62) = 5934.3 ft/sec", 5934.3, "ft/s",
  dict(_C, basis="engine model constant at standard conditions (MR 1.6, Pc 99 psia, 70 °F, per the characteristic equation)"), A9, LT2, db0=None)
A(E, "nozzle.throat_area", None, "Initial Chamber Throat Area (in.2) 121.6021", 121.6021, "in^2", _C, A9, LT2, db0=None)

# ------------------------------------------------------------------ steady-state tables (pp.45-46, PDF pp.50-51)
_T = "calculated (Propulsion Analysis Program); measured value in the same table"
A(E, "performance.pc", None, "Engine Chamber Pressure, psia ... 100", 100, "psia", dict(_C, burn="2nd SPS burn, FS-1 + 90 s", basis=_T, measured="101"),
  A9, "p.45 (PDF p.50) Table 5 (viewed as image)", db0=None, note="Same column: vacuum thrust 20764 lbf, Isp 313.9 s, MR 1.55.")
A(E, "performance.pc", None, "Engine Chamber Pressure, psia ... 102", 102, "psia", dict(_C, burn="3rd SPS burn, FS-1 + 225 s", basis=_T, measured="104"),
  A9, "p.46 (PDF p.51) Table 6 (viewed as image)", db0=None, note="Same column: vacuum thrust 21011 lbf, Isp 313.9 s, MR 1.55.")

# ------------------------------------------------------------------ pressurization (p.22, PDF p.27; p.36, PDF p.41)
A(E, "pressurization.tank_ullage_pressure", None, "at liftoff the measured tank pressures were 180 psia for oxidizer and 178 psia for fuel",
  "180 / 178", "psia", dict(_C, owner="service module", epoch="liftoff (oxidizer / fuel)"), A9, "p.36 (PDF p.41) (viewed as image)", db0=None,
  note="Same page: expected value 178 psia at first SPS ignition; fuel measurement believed biased about -2 psi. The helium "
       "regulator outlet pressure itself is not printed; p.22 says the CSM 104 regulator stems were replaced before flight.")
