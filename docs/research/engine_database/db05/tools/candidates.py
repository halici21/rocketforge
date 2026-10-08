"""Select DB-0.5 regression candidates (SCHEMA_PROPOSAL §6) from emitted assertions."""
import json
from pathlib import Path

DB05 = Path(__file__).resolve().parents[1]
A = json.loads((DB05 / "assertions.json").read_text(encoding="utf-8"))["assertions"]
docs = {d["source_id"]: d for d in json.loads((DB05 / "documents_opened.json").read_text(encoding="utf-8"))["documents"]}
conf = json.loads((DB05 / "conflicts.json").read_text(encoding="utf-8"))["conflicts"]


def pick(engine, source, fields, op=None):
    out = []
    for f in fields:
        hits = [a for a in A if a["engine_id"] == engine and a["source_id"] == source and a["field_path"] == f
                and (op is None or a["operating_point"] in (op, None)) and a["disposition"] == "PROMOTED"]
        assert hits, (engine, source, f)
        out.append(hits[0]["assertion_id"])
    return out


CANDS = [
    dict(candidate_id="RC-DB05-RL10A-3-3A-NOMINAL", engine_id="ENG-US-RL10A-3-3A", configuration="RL10A-3-3A nominal operating point (O/F 5.0, 475 psia)",
         assertions=pick("ENG-US-RL10A-3-3A", "SRC-NTRS-19910018888", ["performance.thrust_vac", "performance.isp_vac", "propellants.mixture_ratio", "nozzle.area_ratio"])
         + pick("ENG-US-RL10A-3-3A", "SRC-NTRS-19950022693", ["performance.pc"]),
         use="ideal-performance check (Pc, O/F, epsilon -> Isp, thrust) with stated efficiency gap; expander-cycle power balance (pump speeds, flows also printed)",
         caveats=["Pc station unstated", "Isp is delivered engine Isp, not ideal"]),
    dict(candidate_id="RC-DB05-J-2S-NOMINAL", engine_id="ENG-US-J-2S", configuration="J-2S nominal (MR 5.5)",
         assertions=pick("ENG-US-J-2S", "SRC-DB05-NTRS-19940016798", ["performance.thrust_vac", "performance.isp_vac", "performance.pc", "propellants.mixture_ratio", "nozzle.area_ratio"]),
         use="ideal-performance check; Pc explicitly at nozzle stagnation", caveats=["slide read visually from a rotated scan (values legible)"]),
    dict(candidate_id="RC-DB05-J-2-230K", engine_id="ENG-US-J-2", configuration="J-2 230,000 lb rating, MR 5.5",
         assertions=pick("ENG-US-J-2", "SRC-NTRS-20100027318", ["performance.thrust_vac", "performance.isp_vac", "performance.pc", "propellants.mixture_ratio", "nozzle.area_ratio"]),
         use="ideal-performance check; Pc explicitly at nozzle stagnation",
         caveats=["thrust rating epoch partially resolved (225K and 230K both primary; this candidate is the 230K row only)", "slide figure rights review required; values usable with attribution"]),
    dict(candidate_id="RC-DB05-RS-25-SLS-109", engine_id="ENG-US-SSME-BLOCK-II", configuration="RS-25 (SLS-adapted Block II) at 109% RPL",
         assertions=pick("ENG-US-SSME-BLOCK-II", "SRC-L3HARRIS-RS25-SPEC", ["performance.thrust_vac", "performance.isp_vac", "performance.pc", "propellants.mixture_ratio", "nozzle.area_ratio"], op="OP-109"),
         use="vacuum ideal-performance check",
         caveats=["power level printed for thrust only; pressure and Isp assumed same sheet (109%) - stated on sheet header, not per line", "manufacturer copyright; values with attribution only", "sea-level thrust excluded: CF-DB05-RS25-SLTHRUST unresolved"]),
    dict(candidate_id="RC-DB05-SPS-BLOCK-I", engine_id="ENG-US-AJ10-137", configuration="Apollo SPS Block I (O/F 2:1)",
         assertions=pick("ENG-US-AJ10-137", "SRC-NASA-TND7375", ["performance.pc", "performance.thrust_vac", "performance.isp_vac"], op="OP-BLOCK-I")
         + pick("ENG-US-AJ10-137", "SRC-NASA-TND7375", ["nozzle.area_ratio"]) + [a["assertion_id"] for a in A if a["engine_id"] == "ENG-US-AJ10-137" and a["operating_point"] == "OP-BLOCK-I" and a["field_path"] == "propellants.mixture_ratio"],
         use="pressure-fed ideal-performance check (N2O4/A-50); Isp printed as an average", caveats=["Isp 'average'", "Block I only; not the Block II flight engine"]),
]
unresolved = {(c["engine_id"], c["field_path"]) for c in conf if c["resolution"] == "UNRESOLVED"}
for c in CANDS:
    srcs = {a["source_id"] for a in A if a["assertion_id"] in c["assertions"]}
    c["sources"] = sorted(srcs)
    c["rights_values"] = sorted({docs[s]["rights_values"] for s in srcs})
    c["unresolved_conflicts_on_fields"] = sorted(f for e, f in unresolved if e == c["engine_id"] and
                                                 any(f.split(" ")[0] in a["field_path"] or a["field_path"] in f for a in A if a["assertion_id"] in c["assertions"]))
    c["status"] = "REGRESSION_CANDIDATE" if not c["unresolved_conflicts_on_fields"] else "BLOCKED_BY_CONFLICT"
NOT = [
    dict(engine_id="ENG-US-F-1", reason="thrust rating epoch UNRESOLVED (1.500 / 1.522 / 1.530 Mlbf)"),
    dict(engine_id="ENG-US-RL10B-2", reason="Pc and Isp intra-document conflict UNRESOLVED (633/644 psi, 465.5/466.5 s)"),
    dict(engine_id="ENG-US-RL10A-4-2", reason="only a Tier B compilation opened; A-4-1/A-4-2 column attribution ambiguous"),
    dict(engine_id="ENG-US-AJ10-190", reason="mixture ratio not found in opened pages; Pc only 'approximately'"),
    dict(engine_id="ENG-US-LMDE", reason="chamber pressure and mixture ratio not found in opened pages"),
    dict(engine_id="ENG-US-H-1-188K", reason="no primary Pc, Isp or MR found (only thrust and turbomachinery)"),
    dict(engine_id="ENG-US-IPD", reason="engine-level documents blocked (DTIC 403)"),
    dict(engine_id="ENG-SU-RD-170", reason="Tier B second-hand transcription; MR intra-document conflict"),
]
(DB05 / "regression_candidates.json").write_text(json.dumps({"notice": "DB-0.5 regression CANDIDATES only. Not accepted physics; nothing here is wired into RocketForge.",
                                                            "rule": "SCHEMA_PROPOSAL.md §6 REGRESSION_CANDIDATE: fetched, values usable with attribution, defined operating point, no UNRESOLVED conflict on the fields used",
                                                            "candidates": CANDS, "not_candidates": NOT}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
for c in CANDS:
    print(c["candidate_id"], c["status"], len(c["assertions"]), c["rights_values"], c["unresolved_conflicts_on_fields"])
