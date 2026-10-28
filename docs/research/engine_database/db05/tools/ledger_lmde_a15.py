"""Apollo 15 DPS pass (2026-10-28): TRW's final flight evaluation of the LM-10 descent propulsion system (engine
S/N 1046), one of the downloads DB-0.5 had fetched but not read. Pages used were viewed as images."""
from ledger import A, D

E = "ENG-US-LMDE"
A15 = "SRC-MSC-05161-A15S4"

D(A15, identifier="MSC-05161 Supplement 4 (Sept 1972) = TRW 20029-H084-R0-00 (April 1972, Avvenire & Wood); NASA-TM-X-69506; "
                  "NTRS 19730023018 (copy read from ibiblio.org/apollo)",
  title="Apollo 15 Mission Report Supplement 4: Descent Propulsion System Final Flight Evaluation", tier="A",
  rights_checked="NTRS 19730023018 GOV_PUBLIC_USE_PERMITTED; export control NO; TRW report prepared for NASA MSC (contract "
                 "NAS9-12330), no restrictive notice on pages read", rights_class="PUBLIC_DOMAIN_GOV",
  note="118 pages; Summary p.2, Section 4 p.10 and Table 1 p.21 viewed as images.")

_C = {"configuration": "LM-10 descent engine S/N 1046 (Apollo 15)"}
LS = "MSC-05161 Suppl. 4 p.10 (PDF p.20) standard-inlet-conditions table; repeated in the Summary p.2 (PDF p.12) (viewed as image)"
_F = dict(_C, environment="vacuum (flight, corrected to standard inlet conditions)", operating_point="FTP, 33 s after ignition",
          basis="flight analysis result, not a rating")
A(E, "performance.thrust_vac", None, "thrust, 9807 lbf", 9807, "lbf", _F, A15, LS, db0=None,
  note="Same table: ground-test prediction 9791 lbf; performance specification range 9712 - 10027 lbf; 3-sigma repeatability 9742 - 9840.")
A(E, "performance.isp_vac", None, "specific impulse, 305.8 sec", 305.8, "s", _F, A15, LS, db0=None,
  note="Same table: specification '> 305.0'; repeatability 305.14 - 306.46.")
A(E, "propellants.mixture_ratio", None, "propellant mixture ratio, 1.594", 1.594, "(-)", _F, A15, LS, db0=None,
  note="Same table: specification range 1.586 - 1.614.")
A(E, "performance.thrust_vac", None, "Performance Specification Range 9712 - 10027", "9712 - 10027", "lbf",
  dict(_C, environment="vacuum (standard inlet conditions)", operating_point="FTP", basis="performance specification range"), A15, LS, db0=None)
A(E, "feed.engine_inlet_pressure", None, "Oxidizer interface pressure, psia 222.0 / Fuel interface pressure, psia 222.0", "222.0 / 222.0", "psia",
  dict(_C, definition="standard inlet conditions (oxidizer / fuel), 70 °F, thrust acceleration 1.0 lbf/lbm, throat area 54.4 in^2"), A15, LS, db0=None)

LT1 = "MSC-05161 Suppl. 4 p.21 (PDF p.31) Table 1 'LM-10 Descent Propulsion Engine and Feed System Physical Characteristics' (viewed as image)"
A(E, "nozzle.throat_area", None, "Chamber Throat Area, in2 53.495", 53.495, "in^2", dict(_C, basis="engine S/N 1046 acceptance test report (footnote 1)"),
  A15, LT1, db0=None)
A(E, "nozzle.area_ratio", None, "Nozzle Expansion Ratio 54.0", 54.0, ":1", dict(_C, basis="approximate value (footnote 3)"), A15, LT1, db0=None,
  note="Same table: nozzle exit area 2937.6 in^2 (approximate). TN D-7143 p.10 gives the design's columbium skirt as ending at "
       "47.5:1; this report does not say why LM-10's ratio differs, and no opened document records the change. Not filed as a "
       "C() conflict: under the DB-2B rule it would withhold the shipped LMDE cooling-zones text (AS-DB05-US-LMDE-010), an owner "
       "decision. See STATUS.md.")
