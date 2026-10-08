"""Emit DB-0.5 artifacts from the ledgers + access log into the repo (docs/research/engine_database/db05)."""
import json, collections, sys
from pathlib import Path

import ledger
import ledger_db0, ledger_rs25, ledger_rs25b, ledger_j2, ledger_f1, ledger_h1, ledger_rl10, ledger_sps, ledger_lmde, ledger_oms, ledger_ipd_rd170  # noqa: F401

HERE = Path(__file__).parent
PKG = Path(__file__).resolve().parents[2]
OUT = PKG / "db05"
SESSION = "2026-10-08"
NOTICE = ("DB-0.5 research evidence. Not a production runtime asset. Every record here was produced by opening the "
          "document itself in session " + SESSION + " (see documents_opened.json); search summaries were not used as evidence.")

log = json.loads((HERE / "access_log.json").read_text())
sources = json.loads((PKG / "data/sources.json").read_text(encoding="utf-8"))
src_ids = {s["source_id"] for s in sources["sources"]}
engines = {e["id"] for e in json.loads((PKG / "data/engines.json").read_text(encoding="utf-8"))["engines"]}

used_by_assert = collections.Counter(a["source_id"] for a in ledger.ASSERTIONS)
used_by_sch = {s["source_id"] for s in ledger.SCHEMATICS.values()}
errors = []

# ---- documents ----
docs = []
for sid, rec in sorted(log.items()):
    d = ledger.DOCS.get(sid)
    if sid not in src_ids and not d:
        continue  # exploratory download, never read and not a registered source: a lead, not evidence
    entry = dict(source_id=sid, url_requested=rec.get("url"), download_url=rec.get("download_url"), http_status=rec.get("http"),
                 bytes=rec.get("bytes"), sha256=rec.get("sha256"), pdf_pages=rec.get("pages"), retrieved_utc=rec.get("time_utc"),
                 ntrs_copyright_determination=rec.get("ntrs_copyright"), ntrs_title=rec.get("ntrs_title"),
                 ntrs_export_control=(rec.get("ntrs_export") or {}).get("isExportControl"))
    if sid in ledger.BLOCKED or not rec.get("ok"):
        b = ledger.BLOCKED.get(sid, {})
        reason = b.get("reason") or (f"HTTP {rec.get('http')}" + (" (no URL in registry)" if rec.get("status") == "NO_URL" else ""))
        if rec.get("ok") and sid in ledger.BLOCKED:
            entry.update(read_level="FETCHED_NOT_EVIDENCE", status_note=reason, note=b.get("note", ""))
        else:
            entry.update(read_level="ACCESS_BLOCKED", status_note=reason, note=b.get("note", ""))
    elif d:
        level = "READ_AND_MINED" if (used_by_assert[sid] or sid in used_by_sch) else "IDENTITY_VERIFIED_ONLY"
        entry.update(read_level=level, **{k: v for k, v in d.items() if k != "source_id"})
        entry["assertions"] = used_by_assert[sid]
    else:
        entry.update(read_level="FETCHED_NOT_READ", status_note="downloaded; not inspected in this session")
    docs.append(entry)
for sid in ledger.BLOCKED:
    if sid not in log:
        docs.append(dict(source_id=sid, read_level="ACCESS_BLOCKED", status_note=ledger.BLOCKED[sid]["reason"], note=ledger.BLOCKED[sid]["note"]))
for sid in ledger.DOCS:
    if sid not in log:
        errors.append(f"DOCS entry without access-log record: {sid}")

# ---- validation ----
new_sources = [sid for sid in ledger.DOCS if sid not in src_ids]
for a in ledger.ASSERTIONS:
    if a["engine_id"] not in engines: errors.append(f"unknown engine {a['engine_id']}")
    if a["source_id"] not in ledger.DOCS: errors.append(f"assertion source not opened: {a['source_id']} {a['assertion_id']}")
    if not a["locator"]: errors.append(f"no locator {a['assertion_id']}")
for s in ledger.SCHEMATICS.values():
    if s["source_id"] not in ledger.DOCS: errors.append(f"schematic source not opened {s['schematic_id']}")
for eid, t in ledger.TOPOLOGIES.items():
    ids = [n["id"] for n in t["nodes"]]
    if len(ids) != len(set(ids)): errors.append(f"dup node in {eid}")
    for e in t["edges"]:
        if e["from"] not in ids or e["to"] not in ids: errors.append(f"edge ref {eid} {e}")
    for sch in t["schematic_ids"]:
        if sch not in ledger.SCHEMATICS: errors.append(f"topology schematic missing {sch}")
for c in ledger.CONFLICTS:
    for cl in c["claims"]:
        if cl[1] not in src_ids and cl[1] not in ledger.DOCS: errors.append(f"conflict claim source unknown {c['conflict_id']} {cl[1]}")
seen = set()
for x in ledger.DB0_DISPOSITIONS:
    a = json.loads((PKG / "data/anchors" / f"{x['engine_id']}.json").read_text(encoding="utf-8"))
    if x["db0_assertion_index"] >= len(a["assertions"]): errors.append(f"bad db0 index {x}")
    else: x["db0_field_path"] = a["assertions"][x["db0_assertion_index"]]["field_path"]; x["db0_value"] = a["assertions"][x["db0_assertion_index"]]["value"]; x["db0_source_id"] = a["assertions"][x["db0_assertion_index"]]["source_id"]
    k = (x["engine_id"], x["db0_assertion_index"])
    if k in seen: errors.append(f"duplicate disposition {k}")
    seen.add(k)
if errors:
    print("\n".join(errors)); sys.exit(1)

OUT.mkdir(exist_ok=True)
(OUT / "topology").mkdir(exist_ok=True)


def dump(name, key, items):
    (OUT / name).write_text(json.dumps({"notice": NOTICE, key: items}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


dump("documents_opened.json", "documents", docs)
dump("assertions.json", "assertions", ledger.ASSERTIONS)
dump("schematics_viewed.json", "schematics", list(ledger.SCHEMATICS.values()))
dump("conflicts.json", "conflicts", ledger.CONFLICTS)
dump("db0_dispositions.json", "dispositions", ledger.DB0_DISPOSITIONS)
for eid, t in ledger.TOPOLOGIES.items():
    (OUT / "topology" / f"{eid}.json").write_text(json.dumps({"notice": NOTICE, **t}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

# ---- sources.json update: access state + new sources ----
DOC_TYPES = {"SRC-DB05-NTRS-19750063889": ("flight manual", 1968), "SRC-DB05-NTRS-20100027316": ("conference chapter + viewgraphs", 2006),
             "SRC-DB05-NTRS-19680026222": ("flight performance report", 1968), "SRC-DB05-NTRS-19940016798": ("contractor final report", 1993),
             "SRC-DB05-NTRS-19670005471": ("design report", 1967), "SRC-DB05-NTRS-19850008634": ("technical paper", 1985)}
by_id = {s["source_id"]: s for s in sources["sources"]}
read = {d["source_id"]: d for d in docs if d["read_level"] in ("READ_AND_MINED", "IDENTITY_VERIFIED_ONLY")}
for sid, d in read.items():
    if sid in by_id:
        s = by_id[sid]
        s["access"] = "fetched"
        s["tier"] = d["tier"]
    else:
        rec = log[sid]
        stype, year = DOC_TYPES.get(sid, ("document", None))
        sources["sources"].append(dict(source_id=sid, title=d["title_as_printed"], authors=[], organization="NASA (NTRS)", year=year,
                                       source_type=stype, identifier=d["identifier_verified"], url=rec.get("url"), tier=d["tier"],
                                       primary="primary", rights=d["rights_values"], rights_basis=d["rights_statement_checked"], engines=[],
                                       locators="", access="fetched", notes="Added in DB-0.5 (" + SESSION + "); see db05/documents_opened.json.",
                                       branches=["db05"]))
for d in docs:
    if d["read_level"] == "ACCESS_BLOCKED" and d["source_id"] in by_id and by_id[d["source_id"]]["access"] == "search_result_only":
        by_id[d["source_id"]]["access"] = "not_retrieved"
sources["notice"] = ("DB-0 research data. Not a production runtime asset. DB-0 values were read from web-search result summaries "
                     "(see DB0_RESEARCH_OVERVIEW.md section 3). Sources with access 'fetched' were opened in DB-0.5 (" + SESSION + "); "
                     "see db05/documents_opened.json.")
(PKG / "data/sources.json").write_text(json.dumps(sources, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
import csv
cols = ["source_id", "title", "organization", "year", "source_type", "identifier", "url", "tier", "primary", "rights", "access", "engines"]
with open(PKG / "data/source_registry.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(cols)
    for s in sources["sources"]:
        w.writerow(["" if s.get(c) is None else ("; ".join(s[c]) if c == "engines" else s[c]) for c in cols])

# ---- stats ----
lv = collections.Counter(d["read_level"] for d in docs)
disp = collections.Counter(a["disposition"] for a in ledger.ASSERTIONS)
dbo = collections.Counter(a["db0_link"]["outcome"] for a in ledger.ASSERTIONS if a["db0_link"])
res = collections.Counter(c["resolution"] for c in ledger.CONFLICTS)
print("documents:", dict(lv))
print("tier of READ docs:", collections.Counter(d["tier"] for d in read.values()))
print("assertions:", len(ledger.ASSERTIONS), dict(disp), "status", dict(collections.Counter(a["status"] for a in ledger.ASSERTIONS)))
print("db0 outcomes:", dict(dbo))
print("schematics viewed:", len(ledger.SCHEMATICS), "topologies:", {k: (len(v["nodes"]), len(v["edges"])) for k, v in ledger.TOPOLOGIES.items()})
print("conflicts:", len(ledger.CONFLICTS), dict(res))
print("db0 dispositions:", dict(collections.Counter(x["outcome"] for x in ledger.DB0_DISPOSITIONS)))
print("new sources:", new_sources)
print("per engine:", dict(collections.Counter(a["engine_id"] for a in ledger.ASSERTIONS)))
