"""Unread-download pass, remainder (2026-10-28): the last of the documents DB-0.5 had fetched but not read, plus the
AEHS SPS page (RPE09.31) that DB-0 cited for the SPS regulator set points but never fetched. Web pages were read
from their text; the battery patent's cover was viewed as an image (the PDF has no text layer)."""
from ledger import A, D, BLOCK

SPS = "ENG-US-AJ10-137"
RPE931 = "SRC-EH-RPE0931"

# ------------------------------------------------------------------ AEHS RPE09.31 (SPS)
D(RPE931, identifier="enginehistory.org/Rockets/RPE09.30/RPE09.31.shtml (Aircraft Engine Historical Society, 'Rocket Propulsion Evolution' 9.31)",
  title="Rocket Propulsion Evolution: 9.31 - Service Propulsion System", tier="D",
  rights_checked="page footer 'Copyright (c) 2002-2026 Aircraft Engine Historical Society, Inc.'; no reuse licence",
  rights_class="VALUES_WITH_ATTRIBUTION",
  note="Secondary compilation; its references are AEDC-TR-68-17 and AEDC-TR-69-7 (Block II SPS engine tests), not opened. "
       "Its engine paragraph restates Boyce's Aerojet chapter (20,000 lb, 100 psi, 314 s, 165 psia inlet, 22 rings).")
L931 = "AEHS RPE09.31 'Helium Pressurization Subsystem' (page text)"
A(SPS, "pressurization.regulator_setpoints", None, "The primary regulator setpoint was 186 ± 4 psig while the secondary regulator setpoint was 191 ± 4 psig",
  "186 ± 4 / 191 ± 4", "psig", {"owner": "service module", "configuration": "UNSTATED",
                                 "reference": "All regulator set points were referenced to a bellows assembly that was vented to ambient"},
  RPE931, L931, db0=None,
  note="The reference sentence matters: a set point referenced to an ambient-vented bellows reads as gauge pressure on the "
       "ground and as absolute pressure in vacuum. Same section: tanks filled to 3,600 ± 50 psia, 4,400 psia maximum; relief "
       "diaphragm 219 ± 6 psig.")

# ------------------------------------------------------------------ identity only
D("SRC-AEHS-RPE", identifier="enginehistory.org 'U.S. Manned Rocket Propulsion Evolution' series (registry URL resolves to RPE08.12)",
  title="U.S. Manned Rocket Propulsion Evolution (AEHS)", tier="D",
  rights_checked="page footer copyright Aircraft Engine Historical Society, Inc.", rights_class="VALUES_WITH_ATTRIBUTION",
  note="The registry URL downloads the same bytes as SRC-ENGINEHISTORY-RPE0812. The locator DB-0 gave (RPE09.31, SPS) is now "
       "its own record, SRC-EH-RPE0931.")
D("SRC-ENGINEHISTORY-RPE0812", identifier="enginehistory.org/Rockets/RPE08.11/RPE08.12.shtml", title="Rocket Propulsion Evolution 8.12 (F-1)",
  tier="D", rights_checked="page footer copyright Aircraft Engine Historical Society, Inc.", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Secondary component description of the F-1. Its one value used is the dry weight (ledger_f1_betts.py).")
D("SRC-ENGINEHISTORY-RPE0822", identifier="enginehistory.org/Rockets/RPE08.22/RPE08.22.shtml", title="Rocket Propulsion Evolution 8.22 (J-2)",
  tier="D", rights_checked="page footer copyright Aircraft Engine Historical Society, Inc.", rights_class="VALUES_WITH_ATTRIBUTION",
  note="Secondary J-2 history; read, not mined. Its engine comparison table gives no source per cell, so it cannot settle "
       "CF-DB05-J2-PC or CF-DB05-J2-THRUST.")
D("SRC-SAE-730941", identifier="SAE Technical Paper 730941 (National Aerospace Engineering and Manufacturing Meeting, 1 Feb 1973)",
  title="Flight Experience with Apollo Spacecraft Propulsion Systems (Joseph G. Thibodaux)", tier="B",
  rights_checked="SAE Mobilus abstract page; full text behind login", rights_class="METADATA_ONLY",
  note="DB-0 title 'reference list citing TN D-7143' -> real title verified. The abstract has no engine values.")
D("SRC-MILSTD-T2START", identifier="themilitarystandard.com/missile/titan2/startsequence.php", title="Titan II Missile System Start Sequence",
  tier="E", rights_checked="hobby site; no licence; unattributed transcription", rights_class="RESTRICTED_REFERENCE",
  note="Names the stage I engine LR87-AJ-5 and stage II LR91-AJ-5 and describes the start sequence; no originating "
       "document is cited, so it is not used for any value.")
D("SRC-PATENT-US8250853", identifier="US 8,250,853 B1 (Pinera, Florida Turbine Technologies; filed 2011-02-16, granted 2012-08-28)",
  title="Hybrid expander cycle rocket engine", tier="A", rights_checked="US patent (public record), read on Google Patents",
  rights_class="PUBLIC_DOMAIN_GOV",
  note="Background: the RL10 starts by bootstrap and its 'prior art RL-10' figure drives the LOX pump by a gear off the LH2 "
       "turbopump shaft, one turbine driving both pumps. No variant is named, so nothing is filed on ENG-US-RL10A-4-2.")
D("SRC-PATENT-US11408373", identifier="US 11,408,373 B1 (Beck et al., Rocket Lab USA; filed 2016-06-24, granted 2022-08-09)",
  title="Jettisonable battery systems for powering electrical turbopumps for launch vehicle rocket engine systems", tier="A",
  rights_checked="US patent (public record); USPTO image PDF (no text layer); cover viewed as image", rights_class="PUBLIC_DOMAIN_GOV",
  note="Rocket Lab's own patent for battery-driven electric turbopumps; the cover does not name Rutherford, so nothing is "
       "filed on ENG-NZ-RUTHERFORD.")

BLOCK("SRC-WIKI-F1", "Wikipedia (tertiary encyclopedia): fetched, but not evidence under DB-0.5 rules",
      "Its values stay search-result claims in the conflicts that cite them.")
BLOCK("SRC-JSC-11174-RevE", "Volume I covers sections 1-9 (electrical buses, caution & warning, GNC/TVC signal flow); the OMS and "
      "MPS drawings DB-0 cited are in later sections, not in this file",
      "174 pages scanned by table of contents; Volume II not downloaded.")
