#!/usr/bin/env python3
"""Accuracy audit: verify a random sample of agenda items against the
city's own portal, so the site can publish evidence-backed accuracy claims
(and find real bugs).

    python3 audit_agenda_items.py [--n 1000] [--seed 20260712] [--attach 200]

For each sampled IQM2 agenda item:
  1. fetch the city's Detail_LegiFile.aspx?ID=<item_id> page,
  2. parse the tracking code + title the CITY currently displays,
  3. compare (whitespace-normalized) against what OUR db says,
  4. check the city page mentions our meeting_date,
  5. check whether our site built a page for the item (stems like
     'POR 2019-275'; resident COM/CRT items deliberately have no page).
For a subsample, also verify the attachment PDF still resolves at the
city (FileOpen id -> %PDF magic bytes).

Writes Data/audit_agenda_items.csv (one row per item, resumable) and
prints a summary. Politeness: 1.0s between requests — a full run of 1,000
takes ~20 minutes. The seed is fixed and recorded so anyone can re-draw
the exact same sample and check the checker.
"""
import argparse
import csv
import html
import random
import re
import sqlite3
import time
import urllib.request
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "cambridge.db"
OUT_CSV = Path(__file__).resolve().parent.parent / "audit_agenda_items.csv"
SITE_OUT = Path(__file__).resolve().parent.parent.parent / "site" / "out"
LEGI = "https://cambridgema.iqm2.com/Citizens/Detail_LegiFile.aspx?ID="
FILEOPEN = "https://cambridgema.iqm2.com/Citizens/FileOpen.aspx?Type=4&ID="
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
DELAY = 1.0
MON = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

FIELDS = ["item_id", "tracking", "meeting_date", "portal_http",
          "tracking_match", "title_match", "date_found",
          "site_page", "attach_check", "note"]


def norm(s):
    """Comparison form: unescape entities, collapse whitespace, strip."""
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip()


def slug_stem(tracking):
    """'POR 2019 #275' -> 'por-2019-275' (the site's item page slug)."""
    stem = tracking.replace(" #", "-")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", stem.lower())).strip("-")


def fetch(url, tries=3):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            r = urllib.request.urlopen(req, timeout=30)
            return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""
        except Exception:
            if attempt == tries - 1:
                return 0, b""
            time.sleep(3)


def parse_portal(page_bytes):
    """City page -> (tracking, title) as the city currently displays them.
    <title> format: '{TRACKING} {TITLE} - Cambridge City, MA'."""
    t = page_bytes.decode("utf-8", "replace")
    # the H1 is the canonical full title; <title> carries tracking + title
    h1 = re.search(r'class="LegiFileHeading"[^>]*>\s*(.*?)\s*</', t, re.S)
    m = re.search(r"<title>\s*(.*?)\s*</title>", t, re.S)
    if not m:
        return "", ""
    full = re.sub(r"\s*-\s*Cambridge City, MA$", "", norm(m.group(1)))
    # two tracking eras: 'POR 2019 #275' and 'AR-19-82'
    tm = re.match(r"([A-Z]{2,4}(?: \d{1,4} #\d{1,4}|-\d{2,4}-\d{1,4}))\s*(.*)",
                  full)
    track, title = (tm.group(1), tm.group(2)) if tm else ("", full)
    if h1:
        title = norm(h1.group(1))
    return track, title


def date_variants(iso):
    """'2019-09-09' -> strings the portal might show the date as."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return []
    y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
    return [f"{MON[mo]} {d}, {y}", f"{mo}/{d}/{y}", f"{mo:02d}/{d:02d}/{y}"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260712)
    ap.add_argument("--attach", type=int, default=200,
                    help="how many of the sampled items also get a PDF check")
    args = ap.parse_args()

    db = sqlite3.connect(DB)
    rows = db.execute(
        "SELECT item_id, tracking, title, meeting_date, file FROM agenda_items "
        "WHERE portal='iqm2' AND item_id != '' AND tracking != ''").fetchall()
    db.close()
    rng = random.Random(args.seed)
    sample = rng.sample(rows, min(args.n, len(rows)))
    attach_ids = {r[0] for r in rng.sample(sample, min(args.attach, len(sample)))}

    done = {}
    if OUT_CSV.exists():
        with open(OUT_CSV, encoding="utf-8") as f:
            done = {r["item_id"]: r for r in csv.DictReader(f)}
    out = open(OUT_CSV, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(out, fieldnames=FIELDS)
    if not done:
        w.writeheader()

    checked = 0
    for item_id, tracking, title, mdate, file in sample:
        if str(item_id) in done:
            continue
        row = {"item_id": item_id, "tracking": tracking, "meeting_date": mdate,
               "attach_check": "", "note": ""}

        status, page = fetch(LEGI + str(item_id))
        row["portal_http"] = status
        if status == 200 and page:
            p_track, p_title = parse_portal(page)
            row["tracking_match"] = (
                "exact" if p_track == norm(tracking) else
                "MISMATCH" if p_track else "unparsed")
            ours, theirs = norm(title), p_title
            row["title_match"] = (
                "exact" if theirs == ours else
                "case" if theirs.casefold() == ours.casefold() else
                "prefix" if theirs and (ours.startswith(theirs) or
                                        theirs.startswith(ours)) else
                "MISMATCH" if theirs else "unparsed")
            if row["title_match"] == "prefix":
                row["note"] = (f"truncated side: "
                               f"{'ours' if len(ours) < len(theirs) else 'theirs'}"
                               f" ({len(ours)} vs {len(theirs)} chars)")
            if row["title_match"] == "MISMATCH":
                for i, (a, b) in enumerate(zip(ours, theirs)):
                    if a != b:
                        row["note"] = f"diverge@{i}: ours…{ours[i:i+40]!r} theirs…{theirs[i:i+40]!r}"
                        break
                else:
                    row["note"] = f"len {len(ours)} vs {len(theirs)}"
            body = norm(page.decode("utf-8", "replace"))
            row["date_found"] = ("yes" if any(v in body for v in
                                              date_variants(mdate)) else "no")
        else:
            row["tracking_match"] = row["title_match"] = row["date_found"] = "n/a"
            row["note"] = "portal page unavailable"

        stem = slug_stem(tracking)
        row["site_page"] = ("yes" if (SITE_OUT / "items" / f"{stem}.html").exists()
                            else "none")

        if item_id in attach_ids and file:
            time.sleep(DELAY)
            st, data = fetch(FILEOPEN + file.replace(".pdf", ""))
            row["attach_check"] = ("pdf-ok" if st == 200 and data[:4] == b"%PDF"
                                   else f"FAIL({st})")

        w.writerow(row)
        out.flush()
        checked += 1
        if checked % 50 == 0:
            print(f"  {checked} checked (+{len(done)} previously)", flush=True)
        time.sleep(DELAY)

    out.close()
    # summary over the whole csv
    with open(OUT_CSV, encoding="utf-8") as f:
        allr = list(csv.DictReader(f))
    n = len(allr)
    def c(field, val):
        return sum(1 for r in allr if r[field] == val)
    print(f"\n=== AUDIT SUMMARY (n={n}, seed={args.seed}) ===")
    print(f"portal 200:        {c('portal_http', '200')}")
    print(f"tracking exact:    {c('tracking_match', 'exact')}  "
          f"mismatch: {c('tracking_match', 'MISMATCH')}  "
          f"unparsed: {c('tracking_match', 'unparsed')}")
    print(f"title exact:       {c('title_match', 'exact')}  case: {c('title_match', 'case')}  "
          f"prefix: {c('title_match', 'prefix')}  MISMATCH: {c('title_match', 'MISMATCH')}")
    print(f"date on page:      {c('date_found', 'yes')} / {n - c('date_found', 'n/a')}")
    print(f"site page present: {c('site_page', 'yes')}")
    ac = [r for r in allr if r["attach_check"]]
    print(f"attachments ok:    {sum(1 for r in ac if r['attach_check'] == 'pdf-ok')} / {len(ac)}")
    bad = [r for r in allr if "MISMATCH" in (r["title_match"], r["tracking_match"])]
    for r in bad[:20]:
        print(f"  !! {r['tracking']} (id {r['item_id']}): {r['note'][:140]}")


if __name__ == "__main__":
    main()
