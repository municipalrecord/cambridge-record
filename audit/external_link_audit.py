#!/usr/bin/env python3
"""Semantic link audit, external half (roadmap: Trust & scrutiny).

The two worst live bugs were links that RESOLVED but went to the wrong
place (IQM2 Type-collision; PrimeGov 200-on-error). So this never trusts
a status code: every live target is content-checked against what we
linked it FOR, from the manifest the internal audit writes
(semantic_link_audit.py -> external_link_manifest.json).

  legifile  — Detail_LegiFile pages must show the tracking code (or the
              db title) of the item whose page links them.
  fileopen  — the PDF's bytes are sha256-compared against the hash
              archived at fetch time (doc_meta) — wrong ids and silent
              city-side alterations are the same finding.
  primegov  — GET the portal page (their error pages are HTTP 200 that
              say "run into an error"), then confirm identity via the
              portal's own public search API: quoted-title search must
              return our meeting-item id.

--city somerville audits the Legistar manifest instead
(semantic_link_audit_somerville.py -> external_link_manifest_somerville.json):

  legistar_meeting — MeetingDetail pages must display the event's body
                     name and meeting date.
  legistar_pdf     — legistar1-hosted PDFs, sha256-compared like fileopen.

Bytes that aren't a PDF at all are a city-side condition, not drift, and
carry their own verdicts so sha256 drift stays the only loud finding:
city-serves-non-pdf (legacy Word served at a .pdf URL — vendor behavior)
and city-file-corrupt (header zeroed, trailer intact — unopenable as
served). Anything else non-PDF stays "mismatch" on purpose.

Polite: single-threaded, ~1.2s floor between requests, backs off on
429/5xx, resumable (state in external_link_results*.json — rerun to
retry errors and no-baselines; --recheck to redo everything;
--reclassify to re-verdict just the non-PDF mismatches).

    python3 site/external_link_audit.py [--city C] [--limit N] [--kind K] [--recheck]
"""
import argparse
import hashlib
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT.parent / "Data" / "cambridge.db"
CITY_FILES = {
    "cambridge": (ROOT / "external_link_manifest.json",
                  ROOT / "external_link_results.json"),
    "somerville": (ROOT / "external_link_manifest_somerville.json",
                   ROOT / "external_link_results_somerville.json"),
}
UA = {"User-Agent": "MunicipalRecord/1.0 (semantic link audit; "
                    "contact@municipalrecord.org)"}
PG_SEARCH = "https://cambridgema.primegov.com/api/portal/search"
TAGS = re.compile(r"<[^>]+>")
DELAY = 1.2
OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"   # legacy .doc/.xls header
# the detail prefix written by the unclassified non-PDF branch; --reclassify
# re-checks exactly these rows and nothing else
NON_PDF_PREFIX = "not a PDF ("


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm_ws(s):
    return re.sub(r"\s+", " ", s)


def tracking_variants(tr):
    tr = norm_ws(tr or "").strip()
    if not tr:
        return set()
    v = {tr, tr.replace(" # ", " #"), tr.replace(" #", " # "),
         tr.replace("#", "-").replace(" ", "-"), tr.replace(" ", "-")}
    m = re.match(r"([A-Za-z]+)[ -](\d+)[ ]?[-#][ ]?(\d+)", tr)
    if m:
        p, a, b = m.groups()
        v |= {f"{p} {a} #{b}", f"{p} {a} # {b}", f"{p}-{a}-{b}",
              f"{p} {a}-{b}"}
    return v


class Backoff:
    def __init__(self):
        self.penalty = 0

    def ok(self):
        self.penalty = 0

    def bad(self):
        self.penalty = min((self.penalty or 15) * 2, 600)
        print(f"    … throttled/erroring, sleeping {self.penalty}s",
              flush=True)
        time.sleep(self.penalty)


def fetch(url, data=None, cap=80 * 2 ** 20):
    req = urllib.request.Request(
        url, data=data,
        headers={**UA, **({"Content-Type": "application/json"} if data
                          else {})})
    r = urllib.request.urlopen(req, timeout=45)
    chunks, size = [], 0
    while True:
        c = r.read(2 ** 20)
        if not c:
            break
        chunks.append(c)
        size += len(c)
        if size > cap:
            raise ValueError(f"response exceeds {cap} bytes")
    return r.status, b"".join(chunks), r.headers


def load_db_context():
    cx = sqlite3.connect(DB)
    lf_title = {str(i): (t or "") for i, t in cx.execute(
        "SELECT item_id, title FROM agenda_items WHERE portal='iqm2'")}
    pg_title = {}
    for iid, tr, pid in cx.execute(
            "SELECT item_id, tracking, portal_id FROM pg_item_uuids "
            "WHERE portal_id != ''"):
        (title,) = next(cx.execute(
            "SELECT title FROM agenda_items WHERE portal='primegov' "
            "AND item_id=?", (iid,)), ("",))
        pg_title[str(pid)] = (tr or "", title or "")
    cx.close()
    return lf_title, pg_title


def check_legifile(url, row, lf_title):
    st, body, _ = fetch(url)
    text = norm_ws(TAGS.sub(" ", body.decode("utf-8", "replace")))
    tr = row.get("expect") or ""
    lid = re.search(r"ID=(\d+)", url).group(1)
    title = norm_ws(lf_title.get(lid, ""))[:80]
    if any(v in text for v in tracking_variants(tr)):
        return "ok", f"page shows {tr!r}"
    if title and title.lower() in text.lower():
        return "ok", f"page shows the item's title (tracking absent)"
    return "mismatch", f"page shows neither {tr!r} nor the item title; " \
                       f"starts: {text[:160]!r}"


def classify_non_pdf(body, ctype):
    """Why bytes at a .pdf URL aren't a PDF, when we can say positively.

    Only classes we've identified get their own verdict; everything else
    falls through to "mismatch" so an unrecognized substitution stays a
    loud finding. Runs before any hash comparison, so no sha256 verdict
    can be reclassified by this.
    """
    if body[:8] == OLE2_MAGIC:
        return "city-serves-non-pdf", \
            f"legacy Word (OLE2) bytes served at a .pdf URL as {ctype} " \
            f"({len(body):,} bytes) — portal vendor behavior, not drift"
    if body[:1024] == b"\0" * 1024 and b"%%EOF" in body[-2048:]:
        zeroed = len(body) - len(body.lstrip(b"\0"))
        return "city-file-corrupt", \
            f"first {zeroed:,} bytes zeroed on the city server (the %PDF- " \
            f"header among them) though the trailer survives — unopenable " \
            f"as served ({len(body):,} bytes, {ctype})"
    return None, None


def check_fileopen(url, row):
    st, body, hdr = fetch(url)
    live = hashlib.sha256(body).hexdigest()
    ctype = (hdr.get("Content-Type") or "").split(";")[0]
    if body[:5] != b"%PDF-":
        verdict, detail = classify_non_pdf(body, ctype)
        if verdict:
            return verdict, detail
        text = norm_ws(TAGS.sub(" ", body[:4000].decode("utf-8", "replace")))
        return "mismatch", f"not a PDF ({ctype}, {len(body)} bytes): " \
                           f"{text[:140]!r}"
    want = row.get("sha256")
    if not want:
        return "no-baseline", f"live sha256 {live} ({len(body):,} bytes) — " \
                              f"no archived hash to compare"
    if live == want:
        return "ok", f"sha256 match ({len(body):,} bytes)"
    return "mismatch", f"sha256 drift: archived {want[:16]}… live {live[:16]}… " \
                       f"({len(body):,} bytes)"


def check_primegov(url, row, pg_title):
    # identity comes from the portal's own search index (the call its UI
    # makes): quoted-title search must return our meeting-item id. The
    # bare GET is advisory only — the shell sometimes prints an error for
    # ids a real browser renders fine (verified live 2026-07-17), so it
    # can't be the verdict.
    pid = re.search(r"/portal/item/(\d+)", url).group(1)
    tr, title = pg_title.get(pid, ("", ""))
    st, body, _ = fetch(url)
    text = norm_ws(TAGS.sub(" ", body.decode("utf-8", "replace")))
    shell = "shell errors on bare GET" if "run into an error" in text.lower() \
        else "shell live"
    if not title:
        return "unverifiable", f"{shell}; no stored title to search the " \
                               f"portal's index with"
    time.sleep(DELAY)
    q = '"' + title.strip().replace('"', "")[:150] + '"'
    _, sbody, _ = fetch(PG_SEARCH, data=json.dumps({"text": q}).encode())
    rows = json.loads(sbody)
    hits = [r for r in rows if r.get("type") == 0 and str(r.get("id")) == pid]
    if hits:
        return "ok", f"portal search confirms id {pid} is " \
                     f"{tr or 'this item'!r} ({shell})"
    others = [str(r.get("id")) for r in rows if r.get("type") == 0][:5]
    return "mismatch", f"portal search for the item's title does not " \
                       f"return id {pid} (returns {others}; {shell})"


def check_legistar_meeting(url, row):
    # MeetingDetail URLs come from the API's own EventInSiteURL — the
    # identity check is that the page displays the event we linked it
    # for: its body name and its meeting date.
    st, body_bytes, _ = fetch(url)
    text = norm_ws(TAGS.sub(" ", body_bytes.decode("utf-8", "replace")))
    body, date = row.get("body") or "", row.get("date") or ""
    y, m, d = date.split("-") if date.count("-") == 2 else ("", "", "")
    variants = {date, f"{int(m or 0)}/{int(d or 0)}/{y}",
                f"{m}/{d}/{y}"} - {""}
    if body and body.lower() not in text.lower():
        return "mismatch", f"page does not show body {body!r}; " \
                           f"starts: {text[:160]!r}"
    if variants and not any(v in text for v in variants):
        return "mismatch", f"page shows {body!r} but not its date {date}"
    return "ok", f"page shows {body!r} and {date}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", choices=sorted(CITY_FILES), default="cambridge")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--kind", choices=["legifile", "fileopen", "primegov",
                                       "legistar_pdf", "legistar_meeting"])
    ap.add_argument("--recheck", action="store_true")
    ap.add_argument("--reclassify", action="store_true",
                    help="re-check only the mismatches whose bytes weren't a "
                         "PDF, to split the city-side classes out of "
                         "'mismatch' without re-crawling; sha256 verdicts "
                         "are never in this set")
    args = ap.parse_args()
    manifest_path, results_path = CITY_FILES[args.city]

    manifest = json.loads(manifest_path.read_text())
    results = json.loads(results_path.read_text()) \
        if results_path.exists() else {}
    lf_title, pg_title = load_db_context() \
        if args.city == "cambridge" else ({}, {})
    backoff = Backoff()

    todo = []
    for url, row in manifest.items():
        if args.kind and row["kind"] != args.kind:
            continue
        prev = results.get(url)
        if args.reclassify:
            if not (prev and prev["verdict"] == "mismatch"
                    and str(prev.get("detail", "")).startswith(NON_PDF_PREFIX)):
                continue
        elif prev and not args.recheck and prev["verdict"] not in (
                "error", "unreachable", "no-baseline"):
            continue
        todo.append((url, row))
    todo.sort(key=lambda x: (x[1]["kind"], x[0]))
    if args.limit:
        todo = todo[:args.limit]

    print(f"external semantic link audit — {len(todo):,} to check "
          f"({len(manifest):,} in manifest, {len(results):,} done)",
          flush=True)
    t0 = time.time()
    for i, (url, row) in enumerate(todo, 1):
        kind = row["kind"]
        try:
            if kind == "legifile":
                verdict, detail = check_legifile(url, row, lf_title)
            elif kind in ("fileopen", "legistar_pdf"):
                verdict, detail = check_fileopen(url, row)
            elif kind == "legistar_meeting":
                verdict, detail = check_legistar_meeting(url, row)
            else:
                verdict, detail = check_primegov(url, row, pg_title)
            backoff.ok()
        except urllib.error.HTTPError as e:
            verdict, detail = "unreachable", f"HTTP {e.code}"
            if e.code in (429, 503):
                backoff.bad()
        except Exception as e:                       # noqa: BLE001
            verdict, detail = "error", str(e)[:160]
        results[url] = {"kind": kind, "expect": row.get("expect"),
                        "verdict": verdict, "detail": detail,
                        "checked_at": now(),
                        "sources": row.get("sources", [])[:3]}
        if verdict not in ("ok",):
            print(f"  [{verdict}] {url}\n      {detail}", flush=True)
        if i % 25 == 0 or i == len(todo):
            results_path.write_text(json.dumps(results, indent=1))
            rate = i / (time.time() - t0)
            print(f"  … {i}/{len(todo)} ({rate * 3600:.0f}/h)", flush=True)
        time.sleep(DELAY)

    results_path.write_text(json.dumps(results, indent=1))
    from collections import Counter
    c = Counter(v["verdict"] for v in results.values())
    print("verdicts:", dict(c))
    sys.exit(0)


if __name__ == "__main__":
    main()
