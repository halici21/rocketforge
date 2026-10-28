"""F-1 rating epoch pass (2026-10-28): the SA-503 manual's engine data table, re-read, and the Apollo-9 (AS-504)
Technical Information Summary, opened for the first time. Only documents opened in this pass."""
from ledger import A, D, C

F1, J2 = "ENG-US-F-1", "ENG-US-J-2"
M503 = "SRC-DB05-NTRS-19750063889"
TIS = "SRC-DB05-NTRS-19700009516"

# ------------------------------------------------------------------ documents opened in this pass
D(TIS, identifier="MSFC R-ASTR-S-69-7, 3 Feb 1969; NASA-TM-X-62654; NASA accession N70-18821; NTRS 19700009516",
  title="Technical Information Summary Apollo-9 (AS-504) Apollo Saturn V Space Vehicle", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; export control NO; MSFC report (US Government work)", rights_class="PUBLIC_DOMAIN_GOV",
  note="90-page scan, read from extracted text and rendered pages; the S-IC section (pp.33-37) was viewed as images.")

# ------------------------------------------------------------------ SA-503 manual, engine data table (re-read)
L503 = "MSFC-MAN-503 p.1-6 (PDF p.13), Figure 1-3 'Saturn V Launch Vehicle', table 'ENGINE DATA' (viewed as image)"
A(F1, "performance.thrust_sl", None, "1,522,000", 1522000, "lb",
  {"environment": "UNSTATED (column 'NOMINAL THRUST EACH')", "epoch": "SA-503 manual, 25 Nov 1968"}, M503, L503, db0=None,
  note="Same row: TOTAL 7,610,000; BURN TIME 150.7SEC. The same manual prints '1,530,000 pound fixed thrust' on p.4-4 "
       "and 'nominal sea level thrust of 7,650,000 pounds total' for the stage; see CF-DB05-F1-RATING-EPOCH.")
A(J2, "performance.thrust_vac", None, "228,000", 228000, "lb",
  {"environment": "UNSTATED (column 'NOMINAL THRUST EACH')", "stage": "S-II (5 engines, TOTAL 1,140,000, BURN TIME 367 SEC)",
   "epoch": "SA-503 manual, 25 Nov 1968"}, M503, L503, db0=None)
A(J2, "performance.thrust_vac", None, "203,000", 203000, "lb",
  {"environment": "UNSTATED (column 'NOMINAL THRUST EACH')", "stage": "S-IVB (1 engine, BURN TIME '156 & 336 SEC')",
   "epoch": "SA-503 manual, 25 Nov 1968"}, M503, L503, db0=None,
  note="A stage-level nominal for the S-IVB engine, not the engine's maximum rating.")

# ------------------------------------------------------------------ AS-504 Technical Information Summary
L35 = "R-ASTR-S-69-7 p.35 (PDF p.36) 'S-IC STAGE STRUCTURE' (viewed as image)"
L19 = "R-ASTR-S-69-7 p.37 (PDF p.38) Figure 19 'F-1 Engine System' (viewed as image)"
A(F1, "performance.thrust_sl", None, "five liquid-fueled Rocketdyne F-1 engines which generate a nominal thrust of 7,610,000 pounds",
  1522000, "lb", {"environment": "UNSTATED", "epoch": "AS-504 (Apollo 9) summary, 3 Feb 1969", "derivation": "7,610,000 / 5 engines"},
  TIS, L35, db0=None, status="INFERRED",
  note="The stage total is printed; the per-engine value is the printed total divided by the five engines it names.")
A(F1, "performance.thrust_sl", None, "1,500,000 lbs Thrust", 1500000, "lb", {"environment": "UNSTATED", "label": "figure annotation"},
  TIS, L19, db0=None, note="The same document's stage text gives 7,610,000 for five engines; the figure keeps the 1.5 Mlbf annotation.")
A(F1, "nozzle.area_ratio", None, "Expansion Ratio 16:1", 16, ":1", {}, TIS, L19, db0=None)
A(F1, "propellants.mixture_ratio", None, "Mixture Ratio - LOX : RP-1 2.27:1", 2.27, ":1", {"mr_basis": "LOX:RP-1"}, TIS, L19, db0=None)

C("CF-DB05-F1-RATING-EPOCH", engine_id=F1, field_path="performance.thrust_sl rating epoch", db0_conflict_id="CF-ORCH_VERIFY-1",
  claims=[["1,522,000 each, 7,610,000 total (engine data table)", M503, "p.1-6"],
          ["1,530,000 pound fixed thrust", M503, "p.4-4"],
          ["nominal thrust of 7,610,000 pounds (five F-1)", TIS, "p.35"],
          ["1,500,000 lbs Thrust (Figure 19)", TIS, "p.37"],
          ["uprate between SA-503 and SA-504 (DB-0 search excerpt)", "SRC-COSMOQUEST-17618", "DB-0"]],
  resolution="PARTIALLY_RESOLVED", kind="different_epoch",
  explanation="The SA-503 crew manual (25 Nov 1968) already tabulates 1,522,000 lb per engine, and the AS-504 summary "
              "(3 Feb 1969) gives the same 7,610,000 lb stage total, so the opened documents do not support an uprate "
              "between SA-503 and SA-504. Both documents also keep an older value (1,530,000 in the manual's prose, "
              "1,500,000 on the AS-504 figure). Whether AS-501 and AS-502 flew at 1,522,000 is not established: no "
              "AS-501 or AS-502 document stating F-1 thrust was opened.")
C("CF-DB05-F1-MR-DIRECTION", engine_id=F1, field_path="propellants.mixture_ratio",
  claims=[["Engine mixture ratio 2.27 (no direction printed)", "SRC-DB05-NTRS-20100027316", "slide F1-6"],
          ["Mixture Ratio - LOX : RP-1 2.27:1 (Figure 19)", TIS, "p.37"]],
  resolution="RESOLVED", kind="primary_value_found",
  explanation="The AS-504 summary prints the direction the Rocketdyne slide left out: 2.27 is oxidizer to fuel (LOX : RP-1).")

# ------------------------------------------------------------------ owner decision of 2026-10-28
# Recorded after the owner kept the shipped 1,125 psia: the AS-504 figure's value joins CF-DB05-F1-PC as a
# competing primary claim (ledger_f1.py) instead of opening a conflict that would withhold the shipped value.
A(F1, "performance.pc", None, "Thrust Chamber Pressure 1105 psia", 1105, "psia", {"pc_station": "UNSTATED"}, TIS, L19, db0=None,
  note="Competing claim in CF-DB05-F1-PC against the 1,125 psia of the 2006 Rocketdyne slide; neither names the station.")
