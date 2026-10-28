"""F-1 pass (2026-10-28): NASA MSFC's 2013 'Waking a Giant' presentation, found by NTRS title search for the F-1
mass and chamber-pressure conflicts, and the dry weight in the AEHS F-1 chapter that DB-0 cited. Slides viewed as images."""
from ledger import A, D

F1 = "ENG-US-F-1"
F1A = "ENG-US-F-1A"
WG = "SRC-DB05-NTRS-20140011656"
RPE = "SRC-ENGINEHISTORY-RPE0812"

D(WG, identifier="NTRS 20140011656 (Betts, NASA MSFC ER21, presentation, 2013)",
  title="Waking a Giant: Bringing the Saturn F-1 Engine Back to Life", tier="A",
  rights_checked="NTRS GOV_PUBLIC_USE_PERMITTED; NASA presentation, no copyright notice on slides read", rights_class="PUBLIC_DOMAIN_GOV",
  note="28 slides; slides 1, 8 and 13 viewed as images. A 2013 summary by MSFC engineers restoring F-1 hardware; its F-1 "
       "column repeats the 2006 Rocketdyne slide's thrust, Isp and 18,616 lb, but prints the chamber pressure differently.")

L8 = "slide 8 'What is the F-1 Engine?' (PDF p.8, viewed as image)"
L13 = "slide 13 'Engine Comparison, F-1 vs. F-1A' (PDF p.13, viewed as image)"
A(F1, "performance.pc", None, "Chamber Pressure, ns (psia) 982", 982, "psia", {"pc_station": "printed 'ns' (not defined on the slide)"}, WG, L13, db0=None,
  note="Slide 8 prints the same 982 psia without the 'ns'. 'ns' is the usual abbreviation for nozzle stagnation (INFERRED; the "
       "deck gives no legend). Competing claim in CF-DB05-F1-PC.")
A(F1, "mechanical.mass", None, "Weight (lb) 18,616", 18616, "lb", {"definition": "UNSTATED"}, WG, L13, db0=None,
  note="Slide 8: 'Weight: 18,616 lb'. Same number as the 2006 Rocketdyne slide F1-6, again without a definition.")
A(F1, "performance.mass_flow_total", None, "Engine Propellant Flow Rate: 5,737 lb/s", 5737, "lb/s", {}, WG, L8, db0=None)
A(F1A, "performance.pc", None, "Chamber Pressure, ns (psia) ... F-1A 1,161", 1161, "psia", {"pc_station": "printed 'ns'"}, WG, L13, db0=None,
  note="Same column: 1,800,000 lbf sea level, 269.7 s sea level, MR 2.27, 16:1, 19,000 lb.")

A(F1, "mechanical.mass", None, "weighed approximately 18,500 lb dry", 18500, "lb", {"definition": "dry"}, RPE,
  "AEHS RPE08.12 engine description (page text)", db0=None,
  note="Tier D secondary compilation; the only opened source that names a definition (dry), and it is an approximation.")
