# DB-0 — Flow schematic index

Flow and cycle schematics are a first-class research product: they are what
lets a database hold **topology** rather than a cycle label. This index records
every schematic DB-0 located, with the figure locator where one was seen.

**Read the verification column first.** No document could be opened during
DB-0, so **no schematic was viewed**. Entries are:
- `described_in_text` — a search summary described the figure or its contents
  (sometimes with a figure number, e.g. "Fig. 1" of a named AIAA/NTRS paper);
- `cited_by_other_source` — another source says the figure exists, or the
  document very probably contains one (e.g. a manual whose title says
  "mechanical schematics") and no figure number was seen. These are leads.

`components_visible` lists only components that a summary named. An empty list
means "not described", never "absent". Simplified schematics routinely omit
valves, purge and bleed lines, igniters and instrumentation; DB-1 must store a
topology's completeness at graph level (see SCHEMA_PROPOSAL.md §3.3).

**Rights.** No schematic image is copied into the repository. Rights classes
are provisional (RIGHTS_MATRIX.md): NASA-employee works and US patents are the
only likely redistributable figures; AIAA, JPP, JAXA, ESA, Energomash and
manufacturer figures are restricted references whose **topology facts** may be
extracted with citation, subject to the legal-review questions in
RIGHTS_MATRIX.md §7.

**Strongest leads to open first** (all public-domain candidates):
- SSME: AIAA 97-2687 (Bradley 1997, NTRS 19970028362) Fig. 1, with the
  OPOV / FPOV / MFV / MOV / CCV valve legend; JSC-19041 *SSME Overview*
  Fig. 1.1-II (flow schematic) and Fig. 1.1-III (component diagram).
- RL10: NTRS 19950022693, Figure 1 (expander cycle).
- H-1: Chrysler SDES-64-414 Vol. VIII (NTRS 19650013471), "mechanical
  schematics" in the title.
- F-1 and J-2: Saturn V flight manual (SA-507 edition located).
- LM descent/ascent, Apollo SPS, Shuttle OMS: Apollo Experience Reports
  (TN D-7143, TN D-7375), OMS Workbook 21002, JSC-19950.
- IPD: DTIC ADA397910.
- Generic cycles: the SP-8107 cycle figure (reproduced in NATO RTO-EN-AVT-150-05).
- US patents with engine-cycle figures (several located; see the index).

| Verification | Entries |
|---|---|
| described_in_text | 39 |
| cited_by_other_source | 32 |

| Rights class | Entries |
|---|---|
| RIGHTS_REVIEW_REQUIRED | 42 |
| PUBLIC_DOMAIN_GOV | 13 |
| RESTRICTED_REFERENCE | 9 |
| OPEN_LICENSE | 3 |
| VALUES_WITH_ATTRIBUTION | 2 |
| UNKNOWN | 2 |

## Index

| Schematic | Engine(s) | Source | Locator | Type / detail | Components (as described) | Usefulness | Rights | Verification | Notes |
|---|---|---|---|---|---|---|---|---|---|
| SCH-GENERIC-BOOSTPUMP-1 |  | SRC-NTRS-SP8107 | pp.53-55 | system_diagram / UNKNOWN | boost pump, main pump | medium | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Page range cited by SRC-PATENT-US5197851; figure existence on those pages not confirmed. |
| SCH-GENERIC-CYCLES-1 |  | SRC-NTRS-SP8107 | figure number NOT known | cycle_schematic / simplified | GG, turbine, pumps, preburner, thrust chamber | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Reproduced in SRC-NATO-ENAVT150-05 per search summary; neither PDF opened. |
| SCH-GENERIC-EXPANDER-R2-1 |  | SRC-NASA-TM4275 | UNKNOWN | cycle_schematic / UNKNOWN |  | medium | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Generic H2/O2 expander cycles; presence of figures not confirmed. |
| SCH-PATENT-US11149691-R2 |  | SRC-PATENT-US11149691 | FIG. numbers not seen | patent_figure / UNKNOWN |  | low | PUBLIC_DOMAIN_GOV | cited_by_other_source |  |
| SCH-PATENT-US4589253-R2 |  | SRC-PATENT-US4589253 | FIG. numbers not seen | patent_figure / UNKNOWN | preburner, cooling jacket heat exchange, turbine | medium | PUBLIC_DOMAIN_GOV | described_in_text |  |
| SCH-PATENT-US6832471-R2 |  | SRC-PATENT-US6832471 | FIG. numbers not seen | patent_figure / UNKNOWN | fuel-rich preburner, platelet heat exchanger/cooler, turbine, main injector | medium | PUBLIC_DOMAIN_GOV | described_in_text | Concept patent (Aerojet). |
| SCH-PATENT-US7900436-R2 |  | SRC-PATENT-US7900436 | FIG. numbers not seen | patent_figure / UNKNOWN | gas generator, hydrogen coolant heat path, two turbopumps | medium | PUBLIC_DOMAIN_GOV | described_in_text |  |
| SCH-RS-25-GOXHEX-1 |  | SRC-PATENT-US5918460 | patent drawings (fig. no. not known) | patent_figure / UNKNOWN | HPOTP turbine exhaust, GOX heat exchanger, tank pressurization line, POGO | medium | PUBLIC_DOMAIN_GOV | described_in_text | Patent figures likely include an SSME flow schematic; not viewed. |
| SCH-CN-YF-75D-1 | ENG-CN-YF-75D | SRC-WIKI-YF75D |  | cycle_schematic / simplified | two-stage axial turbine, lengthened chamber cooling jacket | low | RIGHTS_REVIEW_REQUIRED | described_in_text |  |
| SCH-CN-YF-77-1 | ENG-CN-YF-77 | SRC-WIKI-YF77 |  | cycle_schematic / simplified | gas generator, LOX turbopump, LH2 turbopump, turbine exhausts | medium | RIGHTS_REVIEW_REQUIRED | described_in_text |  |
| SCH-A4-R2-1 | ENG-DE-A4-ENGINE | SRC-V2ROCKET-DESIGN | linked large diagram | system_diagram / UNKNOWN |  | high | RESTRICTED_REFERENCE | cited_by_other_source | Provenance of underlying drawing unknown (possibly wartime German or postwar US exploitation report). |
| SCH-A4-R2-2 | ENG-DE-A4-ENGINE | SRC-NASM-A19790951000 | catalogue text | flow_schematic / simplified | hydrogen peroxide (T-Stoff) + permanganate (Z-Stoff) steam generator, turbine, LOX and alcohol pump impellers, overboar… | medium | VALUES_WITH_ATTRIBUTION | described_in_text | Overboard venting from a separate summary sentence (source attribution among NASM pages uncertain). |
| SCH-ENG-DE-A4-ENGINE-1 | ENG-DE-A4-ENGINE | SRC-NASM-V2-TURBOPUMP | object A19600013000 | installation_schematic / UNKNOWN | turbopump, steam generator, frame | medium | RIGHTS_REVIEW_REQUIRED | described_in_text | Physical artefact + catalogue text, not a drawing. Shows separate-working-fluid architecture (H2O2/permanganate steam generator). |
| SCH-ENG-DE-A4-ENGINE-2 | ENG-DE-A4-ENGINE | SRC-V2ROCKETHISTORY-TP | video overview | system_diagram / UNKNOWN | turbopump, Walter steam generator plant | medium | UNKNOWN | described_in_text | Blog/video; not viewed. |
| SCH-ENG-FR-VEXIN-B-1 | ENG-FR-VEXIN-B | SRC-IAC-09-3159 | paper (full text not accessed) | system_diagram / UNKNOWN | tanks, solid-propellant pressurisation gas generator, water injection | high | RESTRICTED_REFERENCE | cited_by_other_source | Existence of figure INFERRED; abstract describes pressurisation topology. |
| SCH-ENG-FR-VINCI-1 | ENG-FR-VINCI | SRC-DLR-VINCI-NOZZLE-2010 | press release | installation_schematic / UNKNOWN | 3-cone deployable nozzle extension | low | RIGHTS_REVIEW_REQUIRED | described_in_text | Text description only. |
| SCH-ENG-EU-VULCAIN-2-1 | ENG-FR-VULCAIN-2 | SRC-ESA-A5ECA-NEWELEM | NOT_AUDITED | system_diagram / UNKNOWN |  | low | RIGHTS_REVIEW_REQUIRED | described_in_text | Placeholder: no schematic viewed; text-only evidence of a topology feature. Search a Vulcain 2 flow schematic in a follow-up session. Round 2: still none viewe… |
| SCH-VULCAIN-2-1 | ENG-FR-VULCAIN-2 | SRC-ESA-A5ECA-NEWELEM | NOT_AUDITED | system_diagram / UNKNOWN |  | low | RIGHTS_REVIEW_REQUIRED | described_in_text | Placeholder: no schematic viewed; text-only evidence of a topology feature. Search a Vulcain 2 flow schematic in a follow-up session. |
| SCH-VULCAIN-2-TEX-1 | ENG-FR-VULCAIN-2 | SRC-PATENT-US6996973 | patent drawings (fig. no. not known) | patent_figure / UNKNOWN | turbine exhaust pipelines, injection ring, nozzle divergent | medium | PUBLIC_DOMAIN_GOV | described_in_text |  |
| SCH-ENG-GB-SUPER-SPRITE-1 | ENG-GB-SUPER-SPRITE | SRC-NASM-SUPERSPRITE | object A19700331000 | cutaway / UNKNOWN |  | low | RIGHTS_REVIEW_REQUIRED | described_in_text | Physical cutaway; images not viewed. |
| SCH-ENG-IN-CE-20-1 | ENG-IN-CE-20 | SRC-WIKI-CE20 | text description | cycle_schematic / UNKNOWN |  | low | OPEN_LICENSE | described_in_text | Text-only. |
| SCH-ENG-JP-LE-7A-1 | ENG-JP-LE-7A | SRC-WEBLIO-LE7 | text description | cycle_schematic / UNKNOWN |  | low | OPEN_LICENSE | described_in_text | Text-only: H-rich preburner gas drives LH2 and LOX TPs then enters MCC. ja.wikipedia pages usually carry a cycle diagram - not viewed. |
| SCH-JP-LE-9-1 | ENG-JP-LE-9 | SRC-WIKI-LE9 |  | cycle_schematic / simplified | fuel turbopump, ox turbopump, regenerative chamber, bleed turbine exhaust | low | RIGHTS_REVIEW_REQUIRED | described_in_text | Only textual description seen; Wikipedia expander-cycle diagrams exist but not viewed |
| SCH-LE-9-R2-1 | ENG-JP-LE-9, ENG-JP-LE-7A | SRC-JAXA-AA1740298002 | UNKNOWN | cycle_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Text layer garbled; figure not confirmed. |
| SCH-LE-9-R2-2 | ENG-JP-LE-9 | SRC-IAC-LE9-2016 | manuscript (restricted) | cycle_schematic / UNKNOWN |  | high | RESTRICTED_REFERENCE | cited_by_other_source |  |
| SCH-LE-9-R2-3 | ENG-JP-LE-9, ENG-JP-LE-7A | SRC-TEIKYO-LAB001 | photo | cycle_schematic / simplified |  | medium | RESTRICTED_REFERENCE | cited_by_other_source | Figure credited to JAXA on a university page. |
| SCH-LE-X-R2-1 | ENG-JP-LE-X, ENG-JP-LE-9 | SRC-MHI-LEX | UNKNOWN | cycle_schematic / UNKNOWN |  | high | RESTRICTED_REFERENCE | cited_by_other_source | Cited by Wikipedia. |
| SCH-ENG-KR-KRE-075-1 | ENG-KR-KRE-075 | SRC-EUCASS2019-0521 | UNKNOWN | system_diagram / UNKNOWN |  | medium | RIGHTS_REVIEW_REQUIRED | described_in_text | Abstract mentions three control valves; a system figure is likely but NOT seen. |
| SCH-PATENT-US11408373-R2 | ENG-NZ-RUTHERFORD | SRC-PATENT-US11408373 | FIG. numbers not seen | patent_figure / UNKNOWN | battery packs (jettisonable), electric turbopumps | medium | PUBLIC_DOMAIN_GOV | described_in_text | Engine link INFERRED (summary calls it a Rocket Lab patent). |
| SCH-RD-180-R2-1 | ENG-RU-RD-180 | SRC-NTRS-20170000444 | UNKNOWN | system_diagram / UNKNOWN | oxidizer tube (preburner/turbine exhaust), tangential fuel orifices (regen-circuit fuel) | low | RIGHTS_REVIEW_REQUIRED | described_in_text | Element-level, not engine flow. |
| SCH-RD-170-R2-1 | ENG-SU-RD-170, ENG-SU-RD-170 | SRC-JPP-2018-LIOI | Fig. 1 | flow_schematic / UNKNOWN |  | high | RESTRICTED_REFERENCE | described_in_text | Text: 'The Russian RD-170, shown schematically in Fig. 1'. Components not described. |
| SCH-AJ10-137-PRESS-1 | ENG-US-AJ10-137 | SRC-AEHS-RPE | RPE09.31 text | system_diagram / UNKNOWN | He bottles, pressurizing valves, primary/secondary regulators, quad check valves, relief valves, propellant tanks | high | VALUES_WITH_ATTRIBUTION | described_in_text | Primary-source candidates: SRC-IBIBLIO-APOLLO9SPS; Apollo Operations Handbook SPS section (URL history.nasa.gov/afj/aoh/aoh-v1-2-04-sps.pdf seen only quoted in… |
| SCH-AJ10-137-R2-1 | ENG-US-AJ10-137 | SRC-NASA-APOLLO-LIQPROP-OVERVIEW | Figure 22, p. 31 | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | described_in_text | Document identity unresolved (NASA-hosted Apollo liquid propulsion overview). |
| SCH-AJ10-137-R2-2 | ENG-US-AJ10-137 | SRC-APOLLO9-SPS-FFE | UNKNOWN | flow_schematic / UNKNOWN |  | medium | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Report discusses pressurization in depth; figure not confirmed. |
| SCH-AJ10-190-PRESS-1 | ENG-US-AJ10-190 | SRC-NTRS-OMS-1974 | UNKNOWN | system_diagram / UNKNOWN | He bottle, solenoid valves, regulators, vapor isolation valves, check valves, relief valves, GN2 actuation system | medium | RIGHTS_REVIEW_REQUIRED | described_in_text | Component list from search summary; figure not verified. |
| SCH-AJ10-190-R2-1 | ENG-US-AJ10-190 | SRC-USA-OMS21002 | figure list not seen | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Workbooks in this series typically carry pod schematics [BG]. |
| SCH-AJ10-190-R2-2 | ENG-US-AJ10-190 | SRC-JSC-19950 | UNKNOWN | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source |  |
| SCH-AJ10-190-R2-3 | ENG-US-AJ10-190 | SRC-JSC-11174-RevE | OMS/RCS section | system_diagram / detailed |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Flight-controller system drawings (detail level per summary description of handbook type). |
| SCH-AJ10-190-R2-4 | ENG-US-AJ10-190 | SRC-NASA-JSC-CN-7650 | UNKNOWN | system_diagram / simplified |  | medium | RIGHTS_REVIEW_REQUIRED | described_in_text | Summary: 'presents diagrams of the systems'. |
| SCH-F-1-1 | ENG-US-F-1 | SRC-RKD-F1-FAMILIARIZATION | UNKNOWN | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Named in orchestrator brief only; not viewed. |
| SCH-F-1-NE-1 | ENG-US-F-1 | SRC-WIKI-F1 | article text | flow_schematic / UNKNOWN | gas generator, turbine, heat exchanger, exhaust manifold, nozzle extension | medium | OPEN_LICENSE | described_in_text | Text description of topology only; Wikipedia F-1 article is known to carry a NASA flow diagram but not verified this session. |
| SCH-F-1-R2-1 | ENG-US-F-1 | SRC-NASA-SA507-FLIGHTMANUAL | F-1 engine section; figure no. NOT located | system_diagram / UNKNOWN |  | medium | PUBLIC_DOMAIN_GOV | cited_by_other_source | Gigazine summary lists liquid fuel supply system and energy distribution diagram in the F-1 section; no flow figure number seen. |
| SCH-F-1-R2-2 | ENG-US-F-1 | SRC-ENGINEHISTORY-RPE0812 | text | flow_schematic / simplified | gas generator (fuel-rich RP-1/LOX), turbine, heat exchanger, wrap-around turbine exhaust manifold, double-walled nozzle… | medium | RESTRICTED_REFERENCE | described_in_text | Textual flow description, not a figure. |
| SCH-H-1-R2-1 | ENG-US-H-1 | SRC-NTRS-19650013471 | figure list not seen | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | described_in_text | Title explicitly includes 'mechanical schematics' for H-1 engine and hydraulic system; H-1 rating variant not stated. |
| SCH-H-1-R2-2 | ENG-US-H-1 | SRC-NTRS-19650013583 | figure list not seen | installation_schematic / UNKNOWN |  | low | RIGHTS_REVIEW_REQUIRED | described_in_text | Stage-level feed. |
| SCH-H-1-1 | ENG-US-H-1-205K | SRC-RKD-H1-MANUAL | UNKNOWN | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Named in orchestrator brief only; not viewed. |
| SCH-IPD-R2-1 | ENG-US-IPD | SRC-DTIC-ADA397910 | UNKNOWN | cycle_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Abstract only. |
| SCH-IPD-R2-2 | ENG-US-IPD | SRC-DTIC-ADA430218 | slides | cycle_schematic / UNKNOWN |  | medium | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Slides contrast FFSC with SSME fuel-rich SC; whether a schematic is drawn is unconfirmed. |
| SCH-J-2-1 | ENG-US-J-2 | SRC-RKD-J2-MANUAL | UNKNOWN | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Named in orchestrator brief only; not viewed. |
| SCH-J-2-R2-1 | ENG-US-J-2 | SRC-NASA-SA507-FLIGHTMANUAL | J-2 engine section; figure no. NOT located | flow_schematic / UNKNOWN |  | medium | PUBLIC_DOMAIN_GOV | cited_by_other_source | Saturn V flight manuals customarily include engine flow figures [BG]; not confirmed. |
| SCH-J-2-R2-2 | ENG-US-J-2 | SRC-ENGINEHISTORY-RPE0822 | text | flow_schematic / simplified | gas generator, fuel turbine (2-stage velocity-compounded), LOX turbine (2-stage velocity-compounded), MK15 7-stage axia… | medium | RESTRICTED_REFERENCE | described_in_text | Series turbines: GG -> fuel turbine -> LOX turbine -> nozzle. |
| SCH-J-2S-R2-1 | ENG-US-J-2S | SRC-DTIC-AD0867628 | UNKNOWN | system_diagram / UNKNOWN |  | medium | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | ITAR marking reported; access may be restricted. |
| SCH-J-2X-1 | ENG-US-J-2X | SRC-NTRS-20080036837 | UNKNOWN | cycle_schematic / UNKNOWN |  | medium | PUBLIC_DOMAIN_GOV | cited_by_other_source | Existence INFERRED; not viewed. |
| SCH-J-2X-HEX-1 | ENG-US-J-2X | SRC-NASA-J2XBLOG-HEX | blog post | system_diagram / UNKNOWN | heat exchanger, helium, hot gas duct | low | PUBLIC_DOMAIN_GOV | described_in_text |  |
| SCH-LM-APS-R2-1 | ENG-US-LM-ASCENT-ENGINE | SRC-NTRS-19730010173 | figure list not seen | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source |  |
| SCH-LM-APS-R2-2 | ENG-US-LM-ASCENT-ENGINE | SRC-NASA-A10-APS-FFE | UNKNOWN | flow_schematic / UNKNOWN |  | medium | RIGHTS_REVIEW_REQUIRED | cited_by_other_source |  |
| SCH-LMDE-R2-1 | ENG-US-LMDE | SRC-NASA-TND7143 | figure list not seen | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Abstract only; cryogenic helium pressurization is a stated feature. |
| SCH-LR87-5-START-1 | ENG-US-LR87-AJ-5 | SRC-MILSTD-T2START | page text | system_diagram / UNKNOWN | start cartridge, turbopump, gas generator, superheater HEX | medium | UNKNOWN | described_in_text | Usable to build a topology; no figure verified. |
| SCH-LR87-AJ-5-R2-1 | ENG-US-LR87-AJ-5 | SRC-MILSTD-T2START | page text | system_diagram / simplified | 2 regeneratively cooled thrust chambers, 2 pump drive assemblies (fuel pump, oxidizer pump, gearbox, 2 turbine wheels e… | medium | RESTRICTED_REFERENCE | described_in_text | No HAER drawing located; LoC HAER collection is the suggested lead. |
| SCH-RL10A-3-R2-2 | ENG-US-RL10A-3 | SRC-PW-RL10A3-DESIGNREPORT-1966 | UNKNOWN | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Reproduced on Tier E blog (SRC-BLOG-STEVE-RL10) with attribution to P&W Design Report 28 Feb 1966; original not located. |
| SCH-RL10A-3-3A-1 | ENG-US-RL10A-3-3A | SRC-NTRS-TM107318 | UNKNOWN | system_diagram / UNKNOWN |  | high | PUBLIC_DOMAIN_GOV | cited_by_other_source | Existence INFERRED: a component-level engine modeling TM normally includes a flow schematic; orchestrator brief also says RL10 schematics exist in NASA papers.… |
| SCH-RL10A-3-3A-R2-1 | ENG-US-RL10A-3-3A | SRC-NTRS-19950022693 | Figure 1 | cycle_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | described_in_text | Text: 'RL10 engine design (all models) is based on a full expander cycle, as shown in Figure 1'. Components not described. |
| SCH-PATENT-US8250853-R2 | ENG-US-RL10A-4-2 | SRC-PATENT-US8250853 | FIG. numbers not seen | patent_figure / UNKNOWN | LH2 turbopump shaft, gear-driven LOX pump | low | PUBLIC_DOMAIN_GOV | described_in_text | RL10 discussed in background text only; whether a figure depicts RL10 is unknown. RL10 variant not specified; engine link INFERRED. |
| SCH-RS-25-1 | ENG-US-SSME-BLOCK-II, ENG-US-SSME-BLOCK-II | SRC-RKD-SSME-ORIENTATION | UNKNOWN | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Named in orchestrator brief only; not viewed; document not retrieved. |
| SCH-RS-25D-R2-1 | ENG-US-SSME-BLOCK-II, ENG-US-SSME-BLOCK-II | SRC-AIAA-97-2687 | Fig. 1 (legend 97PD-038-001) | flow_schematic / UNKNOWN | oxidizer preburner oxidizer valve (OPOV), fuel preburner oxidizer valve (FPOV), main fuel valve (MFV), main oxidizer va… | high | RIGHTS_REVIEW_REQUIRED | described_in_text | Only the legend's five valves were described in the summary; other components not listed. Engine block shown in 1997 paper not stated (Block I/IIA era likely; … |
| SCH-RS-25D-R2-2 | ENG-US-SSME-BLOCK-II | SRC-AIAA-97-2685 | figure no. unknown | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Summary says companion paper reuses the same schematic. |
| SCH-RS-25D-R2-3 | ENG-US-SSME-BLOCK-II | SRC-ENGINEHISTORY-SSME1 | Figure 3; Photo No. LC86C-4-1315 | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | described_in_text | Caption describes a schematic of the engine system showing relationship of major components. Photo number gives a traceable original (Rocketdyne/NASA photo lab… |
| SCH-RS-25D-R2-4 | ENG-US-SSME-BLOCK-II | SRC-IBIBLIO-SSMEOVERVIEW | Fig. 1.1-II | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | described_in_text | In same drawing set as orbiter MPS and component-location drawings (Fig. 1.1-III). |
| SCH-RS-25D-R2-5 | ENG-US-SSME-BLOCK-II | SRC-IBIBLIO-SSMEOVERVIEW | Fig. 1.1-III | system_diagram / UNKNOWN | high pressure fuel turbopump, fuel preburner, oxidizer preburner, main injector, hot gas manifold | medium | RIGHTS_REVIEW_REQUIRED | described_in_text | Component location drawing, not a flow schematic. |
| SCH-RS-25D-R2-6 | ENG-US-SSME-BLOCK-II, ENG-US-SSME-BLOCK-II | SRC-ENGINEHISTORY-SSMEORIENT-1998 | NOT located (TOC only seen) | flow_schematic / UNKNOWN |  | high | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Existence of a flow schematic in this edition is NOT confirmed; auction listings describe the 1984 edition as containing numerous schematics. |
| SCH-XRS-2200-1 | ENG-US-XRS-2200 | SRC-NTRS-19980174934 | UNKNOWN | system_diagram / UNKNOWN |  | medium | RIGHTS_REVIEW_REQUIRED | cited_by_other_source | Existence INFERRED from paper topic (engine control system); not viewed. |
