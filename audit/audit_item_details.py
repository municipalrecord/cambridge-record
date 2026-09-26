#!/usr/bin/env python3
"""Re-verification audit of the item-details crawl (status/sponsors/votes).

    python3 audit_item_details.py --sample 150 --seed 20260713

Draws a random sample of crawled items, re-fetches each portal page
fresh, re-parses it with the SAME parser (fetch_item_details.parse), and
compares against what the database holds. Divergences are printed and
written to Data/audit_item_details.csv. Same discipline as the agenda
audit: the sample is seeded (reproducible), the artifact is publishable,
and the miss rate is the headline number, whatever it is.

A status divergence can be legitimate (the clerk acted on the item after
our crawl) — the CSV records both values so a human can adjudicate.
"""
import argparse
import csv
import random
import sqlite3
import time
import urllib.request
from pathlib import Path

from fetch_item_details import DB, UA, URL, parse

OUT = Path(__file__).resolve().parent.parent / "audit_item_details.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20260713)
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()

    db = sqlite3.connect(DB)
    rows = db.execute("SELECT item_id, tracking, status, sponsors "
                      "FROM item_details").fetchall()
    votes = {}
    for iid, seq, result, yeas, nays, absent, present in db.execute(
            "SELECT * FROM item_votes ORDER BY seq"):
        votes.setdefault(iid, []).append((result, yeas, nays))
    db.close()

    rng = random.Random(args.seed)
    sample = rng.sample(rows, min(args.sample, len(rows)))
    print(f"auditing {len(sample)} of {len(rows)} crawled items "
          f"(seed {args.seed})")

    results, n_exact, n_div, n_err = [], 0, 0, 0
    for iid, tracking, status, sponsors in sample:
        try:
            req = urllib.request.Request(URL.format(iid), headers=UA)
            pg = urllib.request.urlopen(req, timeout=30).read().decode(
                "utf-8", "replace")
            st2, sp2, v2 = parse(pg)
            old_v = votes.get(iid, [])
            new_v = [(v["result"], v["yeas"], v["nays"]) for v in v2]
            ok = (st2 == status and sp2 == sponsors and new_v == old_v)
            n_exact += ok
            n_div += (not ok)
            results.append([iid, tracking, "exact" if ok else "DIVERGES",
                            status, st2,
                            sponsors == sp2, old_v == new_v])
            if not ok:
                print(f"  DIVERGES {tracking}: status {status!r} -> {st2!r}"
                      f"{'' if sponsors == sp2 else ' sponsors!'}"
                      f"{'' if old_v == new_v else ' votes!'}")
        except Exception as e:              # noqa: BLE001
            n_err += 1
            results.append([iid, tracking, f"FETCH ERROR: {e}",
                            status, "", "", ""])
        time.sleep(args.sleep)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "tracking", "verdict", "db_status",
                    "live_status", "sponsors_match", "votes_match"])
        w.writerows(results)
    print(f"\n=== ITEM-DETAILS AUDIT (seed {args.seed}) ===")
    print(f"{n_exact}/{len(sample)} exact · {n_div} divergent · "
          f"{n_err} fetch errors → {OUT}")


if __name__ == "__main__":
    main()
