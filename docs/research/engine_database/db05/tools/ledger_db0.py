"""Dispositions of DB-0 anchor assertions after opening sources in DB-0.5.

Outcomes: CONFIRMED (the cited source was opened and prints it), CONFIRMED_OTHER_SOURCE (cited source not opened/blocked
but an opened Tier A/B source prints it), CORRECTED (opened primary prints a different value or source), RECLASSIFIED
(value exists but means something else), UNSUPPORTED (secondary claim; opened primary sources print a different value),
WRONG_VARIANT (value belongs to another configuration), ACCESS_BLOCKED (cited source could not be opened).
Assertions not listed were not checked in this session.
"""
from ledger import X, C

RS = "ENG-US-SSME-BLOCK-II"
for i, o, ev in [(0, "CONFIRMED_OTHER_SOURCE", "JSC-19041 §1.1.2"), (1, "CONFIRMED", "AIAA 2002-3581 p.3"), (2, "CORRECTED", "source is JSC-19041 §1.1.2, not NTRS 20030005845"),
                 (4, "CONFIRMED", "L3Harris L26301"), (5, "CONFIRMED", "L3Harris L26301"), (6, "CONFIRMED", "L3Harris L26301"), (9, "CONFIRMED", "L3Harris L26301"),
                 (10, "CONFIRMED", "FS-2015-07-064-MSFC p.2"), (11, "CONFIRMED_OTHER_SOURCE", "MSFC-03-2025-SLS-4963 p.2 (web page not read)"),
                 (12, "CONFIRMED", "HAER TX-116 p.248"), (13, "CONFIRMED", "JSC-19041 p.1.1-1"), (15, "CONFIRMED", "JSC-19041 p.1.1-1"),
                 (14, "ACCESS_BLOCKED", "Hopson FRR host unreachable"), (16, "CONFIRMED", "L3Harris L26301"), (17, "ACCESS_BLOCKED", "Hopson FRR host unreachable"),
                 (18, "CONFIRMED", "L3Harris L26301"), (19, "ACCESS_BLOCKED", "Hopson FRR"), (20, "ACCESS_BLOCKED", "Hopson FRR"), (21, "ACCESS_BLOCKED", "Hopson FRR"),
                 (22, "ACCESS_BLOCKED", "Hopson FRR"), (23, "CONFIRMED", "L3Harris L26301"), (24, "CONFIRMED", "L3Harris L26301"),
                 (29, "CORRECTED", "L3Harris prints 71,140 hp; NTRS 20180006338 prints 69,000 hp; 76,000 hp unsupported"),
                 (30, "UNSUPPORTED", "L3Harris 23,260 hp; NTRS 20180006338 25,000 hp; 26,800 hp not found"),
                 (33, "UNSUPPORTED", "only primary operating speed found is 22,250 rpm (Block IIA, 104.5%, BC98-04 p.25)"),
                 (34, "CONFIRMED_OTHER_SOURCE", "L3Harris L26301 prints 23,260 hp"),
                 (36, "UNSUPPORTED", "BC98-04 p.25 prints 5,018 rpm (Block IIA, 104.5%)"), (39, "UNSUPPORTED", "BC98-04 p.25 prints 15,519 rpm (Block IIA, 104.5%)"),
                 (37, "UNSUPPORTED", "BC98-04 p.25: LPOTP 100 psia in, 421 psia out (Block IIA, 104.5%)"),
                 (40, "UNSUPPORTED", "BC98-04 p.25: LH2 inlet 30 psia; LPFTP discharge 298 psia callout (Block IIA)"),
                 (41, "CONFIRMED_OTHER_SOURCE", "BC98-04 p.24 'two preburners'"), (42, "CONFIRMED_OTHER_SOURCE", "BC98-04 p.24 fuel-rich"),
                 (43, "CONFIRMED_OTHER_SOURCE", "BC98-04 p.24 fuel-rich"), (44, "CONFIRMED", "JSC-19041 p.1.1-1 (generic '5,000 psia')"),
                 (48, "CONFIRMED_OTHER_SOURCE", "BC98-04 p.27"), (49, "CORRECTED", "BC98-04 p.27: OPOV is driven WITH the FPOV to change thrust; not alone"),
                 (51, "CONFIRMED_OTHER_SOURCE", "BC98-04 p.26 (Block IIA) gives split percentages"), (53, "CORRECTED", "statement is in JSC-19041 p.1.1-1; not verified in NTRS 19860012108"),
                 (54, "CONFIRMED", "L3Harris L26301"), (55, "CONFIRMED", "NTRS 19860012108 p.8"), (56, "CONFIRMED", "NTRS 19860012108 p.8"),
                 (57, "CONFIRMED", "L3Harris L26301"), (59, "UNSUPPORTED", "opened sources print 7,750-7,775 lb (SLS) and ~7,400 lb (2003)")]:
    X(RS, i, o, ev)

J2 = "ENG-US-J-2"
for i, o, ev in [(0, "CONFIRMED", "NTRS 20100027318 p.1 'open-cycle gas generator'"), (3, "CONFIRMED", "slide J2-3"), (4, "CONFIRMED", "text p.2"),
                 (5, "CONFIRMED", "slide J2-3"), (6, "CONFIRMED", "Table 1"), (7, "ACCESS_BLOCKED", "DTIC 403; 225,000 lb confirmed in NTRS 20100027318 text p.3 as the qualified version"),
                 (8, "ACCESS_BLOCKED", "ALSJ 404"), (9, "UNSUPPORTED", "no opened primary prints 232,250 lbf"), (11, "CONFIRMED", "Table 1"),
                 (13, "UNSUPPORTED", "primary 425 s"), (14, "CONFIRMED", "text p.2; slide J2-3 gives 717 psia nozzle stagnation"),
                 (15, "UNSUPPORTED", "primary 717 psia"), (17, "CONFIRMED", "slide J2-3"), (19, "UNSUPPORTED", "primary 27.5:1"),
                 (20, "UNSUPPORTED", "primary 2,754 lb basic / 3,492 lb with accessories"), (21, "UNSUPPORTED", "close to 3,492 but not printed"),
                 (22, "UNSUPPORTED", "matches no primary definition"), (23, "CONFIRMED", "text p.2"), (24, "CONFIRMED", "text p.2"),
                 (25, "CONFIRMED_OTHER_SOURCE", "NTRS 20100027318 text p.2 (fuel turbine then oxidizer turbine)"),
                 (27, "CONFIRMED_OTHER_SOURCE", "MSFC-MAN-503 p.5-7"), (31, "CONFIRMED", "text p.2"), (33, "CONFIRMED_OTHER_SOURCE", "text p.2 'conventional centrifugal'"),
                 (38, "CONFIRMED_OTHER_SOURCE", "MSFC-MAN-503 p.5-7"), (43, "ACCESS_BLOCKED", "DTIC 403"), (44, "CONFIRMED_OTHER_SOURCE", "MSFC-MAN-503 p.5-5"),
                 (48, "ACCESS_BLOCKED", "DTIC 403")]:
    X(J2, i, o, ev)
J2S = "ENG-US-J-2S"
for i, o, ev in [(0, "CONFIRMED_OTHER_SOURCE", "NTRS 19940016798 pp.8-9 'tap-off cycle'"), (1, "UNSUPPORTED", "NTRS 20100027318 slide J2-5 shows engine tests from 2/66"),
                 (2, "CONFIRMED", "Table 1"), (4, "CONFIRMED", "Table 1"), (6, "CONFIRMED_OTHER_SOURCE", "NTRS 19940016798 p.9"), (7, "CONFIRMED_OTHER_SOURCE", "NTRS 19940016798 p.9 basic dry weight"),
                 (8, "ACCESS_BLOCKED", "DTIC 403"), (9, "ACCESS_BLOCKED", "DTIC 403"), (11, "ACCESS_BLOCKED", "DTIC 403"), (12, "ACCESS_BLOCKED", "DTIC 403"), (13, "ACCESS_BLOCKED", "DTIC 403"),
                 (14, "CONFIRMED", "NTRS 20080036837 PDF pp.3-4"), (15, "ACCESS_BLOCKED", "generalstaff.org 403")]:
    X(J2S, i, o, ev)
F1 = "ENG-US-F-1"
for i, o, ev in [(2, "CONFIRMED_OTHER_SOURCE", "NTRS 20100027316 slide F1-6"), (3, "CONFIRMED_OTHER_SOURCE", "NTRS 20100027316 slide F1-6"),
                 (4, "UNSUPPORTED", "primary 1,748,200 lb"), (5, "UNSUPPORTED", "primary 1,125 psia"), (6, "UNSUPPORTED", "primary 1,125 psia"),
                 (7, "CONFIRMED_OTHER_SOURCE", "slide F1-6 2.27"), (9, "CORRECTED", "slide F1-6 prints 265.4 s"), (13, "CONFIRMED_OTHER_SOURCE", "slide F1-7; text p.4"),
                 (21, "CONFIRMED_OTHER_SOURCE", "slide F1-7 'two stage impulse turbine'"), (24, "CONFIRMED_OTHER_SOURCE", "MSFC-MAN-503 p.4-5; NTRS 20100027316 text p.4"),
                 (26, "CONFIRMED_OTHER_SOURCE", "slide F1-7"), (29, "CONFIRMED_OTHER_SOURCE", "slide F1-7; MSFC-MAN-503 p.4-4"), (30, "CONFIRMED_OTHER_SOURCE", "MSFC-MAN-503 p.4-4"),
                 (31, "UNSUPPORTED", "primary 18,616 lb (definition unstated)"), (32, "CONFIRMED_OTHER_SOURCE", "slide F1-6")]:
    X(F1, i, o, ev)
H1 = "ENG-US-H-1"
for i in [0, 15, 16, 17, 18, 19, 20, 21, 22, 24, 26]:
    X(H1, i, "CONFIRMED", "SDES-64-415 Vol. VIII §1.1-1.2 (attach to ENG-US-H-1-188K)")
for i, ev in [(25, "SDES-64-415 §1.2.1.3"), (27, "SDES-64-415 §1.2.1.5")]:
    X(H1, i, "CONFIRMED_OTHER_SOURCE", ev)
X(H1, 23, "CONFIRMED", "DERIVED 32,000/6,537 = 4.9 reproduces")
X(H1, 11, "UNSUPPORTED", "SA-10 document: cutoff ~150 s after ignition (vehicle-specific)")
RA = "ENG-US-RL10A-4-2"
for i in [0, 5, 7]:
    X(RA, i, "CONFIRMED_OTHER_SOURCE", "L3Harris sheet 404; NAP 11780 Table D-4 prints the same value")
for i in [3, 4, 6, 10, 13]:
    X(RA, i, "ACCESS_BLOCKED", "AIAA vehicle guide 404")
X(RA, 9, "UNSUPPORTED", "NAP 11780 text: 610 psi")
X(RA, 11, "CONFIRMED_OTHER_SOURCE", "NAP Table D-2/D-4: 84:1")
X(RA, 16, "CONFIRMED_OTHER_SOURCE", "NASA CR-195478 §3.1 (RL10A-3-3A, family context only)")
RB = "ENG-US-RL10B-2"
for i, o, ev in [(0, "CONFIRMED", "ULA inaugural p.2"), (1, "CONFIRMED", "ULA GPS III booklet p.1"), (4, "CONFIRMED", "NAP text"), (5, "CONFIRMED", "NAP Table D-2"),
                 (8, "CONFIRMED", "NAP text"), (9, "CONFIRMED", "NAP Table D-2"), (10, "ACCESS_BLOCKED", "AIAA vehicle guide 404"), (12, "ACCESS_BLOCKED", "AIAA vehicle guide 404"),
                 (13, "CONFIRMED", "NAP Table D-2"), (14, "CONFIRMED", "ULA inaugural p.2 'extendible nozzle' (carbon-carbon wording is NAP's)"),
                 (15, "ACCESS_BLOCKED", "IAF page shell only"), (16, "ACCESS_BLOCKED", "IAF page shell only"), (17, "ACCESS_BLOCKED", "IAF"), (18, "ACCESS_BLOCKED", "IAF")]:
    X(RB, i, o, ev)
SPS = "ENG-US-AJ10-137"
X(SPS, 0, "CONFIRMED", "TN D-7375 title")
X(SPS, 1, "CONFIRMED_OTHER_SOURCE", "TN D-7375 pp.3-4 primary + secondary in series")
X(SPS, 2, "UNSUPPORTED", "TN D-7375 p.3: helium 'regulated to 180 psia'; 186 psig not printed (see CF-DB05-SPS-REG)")
X(SPS, 3, "UNSUPPORTED", "TN D-7375 says only that the secondary regulates higher; 191 psig not printed")
X(SPS, 4, "CONFIRMED", "NTRS 19710025470 title (metadata)")
LM = "ENG-US-LMDE"
for i in [0, 1, 2, 3]:
    X(LM, i, "CONFIRMED", "TN D-7143")
OMS = "ENG-US-AJ10-190"
X(OMS, 0, "CONFIRMED_OTHER_SOURCE", "USA006500 Fig. 2-10")
X(OMS, 1, "CONFIRMED_OTHER_SOURCE", "USA006500 §2.1")
IPD = "ENG-US-IPD"
for i in [4, 5, 9]:
    X(IPD, i, "ACCESS_BLOCKED", "DTIC 403")
for i in [7, 8, 10, 11, 12]:
    X(IPD, i, "ACCESS_BLOCKED", "wpafb.af.mil 403")
for i in [2, 3]:
    X(IPD, i, "CONFIRMED_OTHER_SOURCE", "NTRS 20040084662 abstract")
X(IPD, 6, "CONFIRMED_OTHER_SOURCE", "NTRS 20040084662 abstract 'full flow staged combustion'")
RD = "ENG-SU-RD-170"
for i in [4, 5, 6, 10, 11, 12, 13, 14, 16, 25]:
    X(RD, i, "CONFIRMED", "NTRS 19910018906 PDF p.16 (re-graded Tier B: Rockwell transcription/analysis)")
X(RD, 8, "RECLASSIFIED", "NTRS 19910018906 p.15: Rockwell inference from photographs, not a reported fact (status INFERRED)")
X(RD, 15, "CONFIRMED", "250 kgf/cm2 = 24.52 MPa (DERIVED reproduces)")

C("CF-DB05-SPS-REG", engine_id=SPS, field_path="pressurization.regulator_setpoints",
  claims=[["regulated to 180 psia", "SRC-NASA-TND7375", "p.3 (PDF p.7)"], ["186 psig primary / 191 psig secondary", "SRC-EH-RPE0931", "DB-0 search summary"]],
  resolution="UNRESOLVED", kind="definition_or_epoch",
  explanation="Primary prints a single regulated value in psia; the DB-0 secondary values are psig and per-regulator. Could be design vs flight set points; not resolvable from the opened pages.")
