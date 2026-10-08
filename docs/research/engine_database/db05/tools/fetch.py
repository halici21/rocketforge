"""Fetch DB-0.5 P0 documents into a local cache and log access evidence.

Usage: python fetch.py  (reads work_queue.json + sources.json; writes cache/ + access_log.json)
"""
import hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
CACHE = Path(os.environ.get("DB05_CACHE", HERE / "cache"))  # downloaded documents are NOT committed
CACHE.mkdir(exist_ok=True)
LOG = HERE / "access_log.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def curl(url, out):
    r = subprocess.run(["curl", "-sL", "-m", "180", "-A", UA, "-o", str(out), "-w", "%{http_code}|%{content_type}|%{url_effective}", url],
                       capture_output=True, text=True)
    code, ctype, eff = (r.stdout.split("|") + ["", "", ""])[:3]
    return code, ctype, eff


def ntrs_id(s):
    m = re.search(r"(19|20)\d{9}", s or "")
    return m.group(0) if m else None


def main(only=None):
    log = json.loads(LOG.read_text()) if LOG.exists() else {}
    q = json.loads((REPO / "db05/work_queue.json").read_text(encoding="utf-8"))
    src = {x["source_id"]: x for x in json.loads((REPO / "data/sources.json").read_text(encoding="utf-8"))["sources"]}
    want = {}
    for d in q["documents"]:
        if d["priority"] == "P0":
            want[d["source_id"]] = d.get("url") or src.get(d["source_id"], {}).get("url", "")
    for s in q["schematics"]:
        if s["priority"] == "P0":
            want.setdefault(s["source_id"], src.get(s["source_id"], {}).get("url", ""))
    extra = json.loads((HERE / "extra_urls.json").read_text()) if (HERE / "extra_urls.json").exists() else {}
    want.update(extra)
    for sid, url in want.items():
        if only and sid not in only:
            continue
        if sid in log and log[sid].get("ok") and not only:
            continue
        rec = {"source_id": sid, "url": url, "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        if not url:
            rec.update(ok=False, status="NO_URL")
            log[sid] = rec
            continue
        nid = ntrs_id(url) if "ntrs.nasa.gov" in url else None
        if nid:
            meta = CACHE / f"{sid}.ntrs.json"
            code, _, _ = curl(f"https://ntrs.nasa.gov/api/citations/{nid}", meta)
            rec["ntrs_api_http"] = code
            if code == "200":
                m = json.loads(meta.read_text(encoding="utf-8"))
                rec["ntrs_title"] = m.get("title")
                rec["ntrs_copyright"] = (m.get("copyright") or {}).get("determinationType")
                rec["ntrs_export"] = m.get("exportControl")
                rec["ntrs_distribution"] = m.get("distribution")
                rec["ntrs_report_numbers"] = m.get("otherReportNumbers")
                url = f"https://ntrs.nasa.gov/api/citations/{nid}/downloads/{nid}.pdf"
                rec["download_url"] = url
        ext = ".pdf" if url.lower().split("?")[0].endswith(".pdf") or nid or "downloadPdf" in url else ".html"
        out = CACHE / f"{sid}{ext}"
        code, ctype, eff = curl(url, out)
        rec.update(http=code, content_type=ctype, effective_url=eff)
        if out.exists() and out.stat().st_size:
            b = out.read_bytes()
            rec["bytes"] = len(b)
            rec["sha256"] = hashlib.sha256(b).hexdigest()
            rec["is_pdf"] = b[:5] == b"%PDF-"
            if rec["is_pdf"]:
                try:
                    import fitz
                    doc = fitz.open(out)
                    rec["pages"] = doc.page_count
                    rec["text_chars"] = sum(len(p.get_text()) for p in doc)
                except Exception as e:  # noqa: BLE001
                    rec["pdf_error"] = str(e)
        rec["ok"] = code == "200" and rec.get("bytes", 0) > 2000
        rec["file"] = out.name
        log[sid] = rec
        print(sid, code, rec.get("bytes"), rec.get("pages"), rec.get("ntrs_title", "")[:60] if rec.get("ntrs_title") else "", flush=True)
        LOG.write_text(json.dumps(log, indent=1))
    LOG.write_text(json.dumps(log, indent=1))


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
