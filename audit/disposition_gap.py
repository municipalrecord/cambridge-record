"""Audit the 'no vote or disposition' gap.

Answers five questions with exact counts:
  1. How many no-disposition items already have a recorded outcome in the
     site's own votes-rows / items-rows datasets (i.e. recoverable now)?
  2. Breakdown of the no-disposition set by type and year; anomaly detection.
  3. How many no-disposition items sit on meetings whose minutes are
     'not on file', and what the 'Why not' column says.
  4. Items flagged no-disposition on the page but carrying a disposition in
     their own parsed citation string (cite_disposition).
  5. has_citation=false breakdown, and its correlation with no_disposition.

No network. Reads only files already in the repo.
"""
import json, re, sys, collections, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CORPUS = ROOT / "audit" / "corpus"


def load_dx(name):
    txt = (DATA / name).read_text(encoding="utf-8")
    txt = txt.split("=", 1)[1].strip().rstrip(";")
    return json.loads(txt)


# ---------------------------------------------------------------- join keys
RE_LABEL = re.compile(r"^([A-Za-z]+)[\s\-]+(\d{2,4})[\s\-]*#?\s*(\d+)\s*$")
RE_FILE = re.compile(r"([a-z]+)-(\d{4})-(\d+)\.html$")


def key_from_href(href):
    """'../items/app-2026-39.html' -> 'app-2026-39'. Exact, canonical."""
    if not href:
        return None
    m = RE_FILE.search(href)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def key_from_label(label):
    """'APP 2026 #39' / 'AR-16-1' / 'ORD 2016 # 3' -> 'app-2026-39'."""
    if not label:
        return None
    m = RE_LABEL.match(label.strip())
    if not m:
        return None
    typ, yr, num = m.group(1).lower(), int(m.group(2)), int(m.group(3))
    if yr < 100:                     # AR items use a two-digit year
        yr += 2000
    return f"{typ}-{yr}-{num}"


def row_key(cell):
    """Item cell is either ['LABEL','href'] or a bare 'LABEL' string."""
    if isinstance(cell, list):
        return key_from_href(cell[1]) or key_from_label(cell[0]), cell[0]
    return key_from_label(cell), cell


# ---------------------------------------------------------------- outcomes
NULL_OUTCOMES = {"", "-", "--", "n/a", "none", "no action", "unknown"}


RE_TALLY = re.compile(r"^\s*\d+\s*-\s*\d+(?:\s*-\s*\d+)?\s*$")


def real_outcome(s, voters=None):
    """True when the Outcome cell records an actual disposition.

    Two shapes count. A verb ("ORDER ADOPTED", "PLACED ON FILE") is the
    normal case. A bare tally ("8-0-1") with named voters alongside it is
    also a recorded roll call -- the clerk counted the room -- so it is a
    disposition even though the outcome string has no verb.
    """
    if not s:
        return False
    t = s.strip()
    if t.lower() in NULL_OUTCOMES:
        return False
    if re.search(r"[A-Za-z]{3}", t):
        return True
    return bool(RE_TALLY.match(t) and voters)


def main():
    votes = load_dx("votes-rows.6b5758f6.js")
    irows = load_dx("items-rows.c5cd69ae.js")
    crows = load_dx("committee-votes-rows.fceb901a.js")
    meets = load_dx("meetings-rows.0b4cf293.js")

    items = [json.loads(l) for l in (CORPUS / "items.jsonl").open(encoding="utf-8")]
    for r in items:
        r["key"] = key_from_href(r["file"]) or key_from_label(r["item_id"])
    by_key = {}
    dupe_keys = 0
    for r in items:
        if r["key"] in by_key:
            dupe_keys += 1
        by_key[r["key"]] = r

    out = collections.OrderedDict()
    out["total_items"] = len(items)
    out["unique_keys"] = len(by_key)
    out["duplicate_keys"] = dupe_keys
    nod = [r for r in items if r.get("no_disposition")]
    out["no_disposition"] = len(nod)
    out["has_votes_true"] = sum(1 for r in items if r.get("has_votes"))
    out["has_citation_false"] = sum(1 for r in items if not r.get("has_citation"))

    # ------------------------------------------------ Q1: recoverable joins
    # votes-rows: best outcome per item key
    vote_idx = collections.defaultdict(list)
    v_unjoinable = 0
    for row in votes["rows"]:
        k, lab = row_key(row[0])
        if not k:
            v_unjoinable += 1
            continue
        vote_idx[k].append({"label": lab, "date": row[1], "outcome": row[2],
                            "yes": row[3], "no": row[4], "source": row[7]})
    item_idx = collections.defaultdict(list)
    i_unjoinable = 0
    for row in irows["rows"]:
        k, lab = row_key(row[0])
        if not k:
            i_unjoinable += 1
            continue
        item_idx[k].append({"label": lab, "outcome": row[1], "sponsors": row[2]})
    cttee_idx = collections.defaultdict(list)
    for row in crows["rows"]:
        if not row[2]:
            continue
        k, lab = row_key(row[2])
        if k:
            cttee_idx[k].append({"date": row[0], "committee": row[1],
                                 "outcome": row[3], "tally": row[4]})

    out["votes_rows"] = len(votes["rows"])
    out["votes_rows_unjoinable_label"] = v_unjoinable
    out["votes_distinct_keys"] = len(vote_idx)
    out["votes_keys_matching_corpus"] = sum(1 for k in vote_idx if k in by_key)
    out["items_rows"] = len(irows["rows"])
    out["items_rows_unjoinable_label"] = i_unjoinable
    out["items_distinct_keys"] = len(item_idx)
    out["items_keys_matching_corpus"] = sum(1 for k in item_idx if k in by_key)
    out["cttee_rows_with_item"] = sum(1 for r in crows["rows"] if r[2])
    out["cttee_distinct_keys"] = len(cttee_idx)

    recoverable = []
    q1 = collections.Counter()
    for r in nod:
        k = r["key"]
        vm = [v for v in vote_idx.get(k, [])
              if real_outcome(v["outcome"], v["yes"] or v["no"])]
        im = [v for v in item_idx.get(k, []) if real_outcome(v["outcome"])]
        cm = [v for v in cttee_idx.get(k, []) if real_outcome(v["outcome"])]
        if vm:
            o = vm[0]["outcome"].strip()
            if RE_TALLY.match(o):
                o = f"Recorded roll call {o} (outcome verb absent from the clerk's sheet)"
            src, best, conf = "votes-rows", o, "high"
            q1["votes-rows"] += 1
        elif im:
            src, best, conf = "items-rows", im[0]["outcome"], "high"
            q1["items-rows"] += 1
        elif cm:
            src = "committee-votes-rows"
            best = f'{cm[0]["outcome"]} ({cm[0]["committee"]}, {cm[0]["date"]})'
            conf = "medium"
            q1["committee-votes-rows"] += 1
        else:
            q1["none"] += 1
            continue
        # confidence: medium when the same key carries conflicting outcomes
        allo = {o["outcome"] for o in vm + im}
        if len(allo) > 1:
            conf = "medium"
        recoverable.append({
            "item_id": r["item_id"], "url": r["url"], "key": k,
            "type": r.get("type"), "year": r.get("year"), "date": r.get("date"),
            "current": "no disposition", "recovered_outcome": best,
            "source": src, "confidence": conf,
            "n_vote_rows": len(vm), "n_item_rows": len(im),
            "distinct_outcomes": sorted(allo) if len(allo) > 1 else None,
        })
    out["q1_recoverable_total"] = len(recoverable)
    out["q1_by_source"] = dict(q1)
    out["q1_by_confidence"] = dict(collections.Counter(x["confidence"] for x in recoverable))
    out["q1_recoverable_by_type"] = dict(collections.Counter(x["type"] for x in recoverable).most_common())
    out["q1_recoverable_by_year"] = dict(sorted(collections.Counter(x["year"] for x in recoverable).items()))

    # sanity: items NOT flagged no_disposition that also match (control group)
    have = [r for r in items if not r.get("no_disposition")]
    ctrl = sum(1 for r in have
               if any(real_outcome(v["outcome"]) for v in vote_idx.get(r["key"], []))
               or any(real_outcome(v["outcome"]) for v in item_idx.get(r["key"], [])))
    out["control_dispositioned_items_matching_rows"] = ctrl
    out["control_dispositioned_items"] = len(have)

    # ------------------------------------------------ Q2: type x year
    by_type = collections.Counter()
    tot_type = collections.Counter()
    cell = collections.Counter()
    tot_cell = collections.Counter()
    by_year = collections.Counter()
    tot_year = collections.Counter()
    for r in items:
        t, y = r.get("type"), r.get("year")
        tot_type[t] += 1
        tot_year[y] += 1
        tot_cell[(t, y)] += 1
        if r.get("no_disposition"):
            by_type[t] += 1
            by_year[y] += 1
            cell[(t, y)] += 1
    out["q2_by_type"] = {t: {"no_disp": by_type[t], "total": tot_type[t],
                             "pct": round(100 * by_type[t] / tot_type[t], 1)}
                         for t, _ in tot_type.most_common()}
    out["q2_by_year"] = {y: {"no_disp": by_year[y], "total": tot_year[y],
                             "pct": round(100 * by_year[y] / tot_year[y], 1)}
                         for y in sorted(tot_year) if y}
    grid = {}
    for (t, y), n in sorted(tot_cell.items(), key=lambda kv: (str(kv[0][0]), kv[0][1] or 0)):
        if not y:
            continue
        grid.setdefault(t, {})[y] = {"no_disp": cell[(t, y)], "total": n,
                                     "pct": round(100 * cell[(t, y)] / n, 1)}
    out["q2_grid"] = grid

    # --- anomaly detection -------------------------------------------
    # The dominant structural fact is a cliff: the site's outcome datasets
    # (votes-rows / items-rows) carry essentially nothing before 2016, so
    # every 2004-2015 cell is ~100% no-disposition and a whole-corpus
    # median is meaningless. Anomalies are therefore scored separately:
    #   (a) the era cliff itself, reported as coverage per year;
    #   (b) within the modern era (2016+), cells out of line with the
    #       type's own modern-era median.
    import statistics
    MODERN = 2016
    out["q2_era_split"] = {}
    for lo, hi, lab in [(2004, 2015, "legacy_2004_2015"), (2016, 2026, "modern_2016_2026")]:
        tot = sum(v for (t, y), v in tot_cell.items() if y and lo <= y <= hi)
        nd = sum(v for (t, y), v in cell.items() if y and lo <= y <= hi)
        out["q2_era_split"][lab] = {"total": tot, "no_disp": nd,
                                    "pct": round(100 * nd / tot, 1),
                                    "share_of_all_no_disp": round(100 * nd / len(nod), 1)}
    anomalies = []
    for t, years in grid.items():
        mod = {y: v for y, v in years.items() if y >= MODERN and v["total"] >= 20}
        if len(mod) < 4:
            continue
        pcts = [v["pct"] for v in mod.values()]
        med = statistics.median(pcts)
        for y, v in sorted(mod.items()):
            if abs(v["pct"] - med) >= 10 and v["no_disp"] >= 5:
                anomalies.append({"type": t, "year": y, "pct": v["pct"],
                                  "type_modern_median_pct": med,
                                  "total": v["total"], "no_disp": v["no_disp"],
                                  "delta": round(v["pct"] - med, 1)})
    out["q2_modern_anomalies"] = sorted(anomalies, key=lambda a: -a["delta"])
    # modern-era no-disposition breakdown (the genuinely suspicious set)
    modn = [r for r in nod if (r.get("year") or 0) >= MODERN]
    out["q2_modern_no_disp_total"] = len(modn)
    out["q2_modern_no_disp_by_type"] = dict(
        collections.Counter(r.get("type") for r in modn).most_common())
    out["q2_modern_no_disp_by_year"] = dict(
        sorted(collections.Counter(r.get("year") for r in modn).items()))
    out["q2_modern_no_disp_by_type_year"] = {
        t: dict(sorted(collections.Counter(
            r.get("year") for r in modn if r.get("type") == t).items()))
        for t in {r.get("type") for r in modn}}

    # ------------------------------------------------ Q3: meetings/minutes
    BODY = {"Cambridge City Council": "City Council"}
    mins = {}
    whynot = collections.Counter()
    for row in meets["rows"]:
        date, body, meeting, nitems, minutes, why = row[:6]
        mins.setdefault((date, body), []).append((minutes, why))
    out["meetings_rows"] = len(meets["rows"])
    out["meetings_minutes_counts"] = dict(collections.Counter(r[4] for r in meets["rows"]))

    q3 = collections.Counter()
    for r in nod:
        d = r.get("date")
        b = BODY.get(r.get("body"), r.get("body")) or "City Council"
        if not d:
            q3["no_date_on_item"] += 1
            continue
        hit = mins.get((d, b))
        if not hit:
            q3["no_matching_meeting_row"] += 1
            continue
        vals = {m for m, _ in hit}
        if vals == {"on file"}:
            q3["minutes_on_file"] += 1
        elif vals == {"not on file"}:
            q3["minutes_not_on_file"] += 1
            for m, w in hit:
                whynot[w or "(blank)"] += 1
        else:
            q3["mixed"] += 1
    out["q3"] = dict(q3)
    out["q3_whynot_top"] = whynot.most_common(12)
    # same for all items, for contrast
    q3all = collections.Counter()
    for r in items:
        d = r.get("date")
        b = BODY.get(r.get("body"), r.get("body")) or "City Council"
        hit = mins.get((d, b)) if d else None
        if not hit:
            q3all["unmatched"] += 1
        else:
            vals = {m for m, _ in hit}
            q3all["on file" if vals == {"on file"} else
                  ("not on file" if vals == {"not on file"} else "mixed")] += 1
    out["q3_all_items"] = dict(q3all)
    # cross: recoverable items on not-on-file meetings
    rec_keys = {x["key"] for x in recoverable}
    q3rec = collections.Counter()
    for r in nod:
        if r["key"] not in rec_keys:
            continue
        d, b = r.get("date"), BODY.get(r.get("body"), r.get("body")) or "City Council"
        hit = mins.get((d, b)) if d else None
        if not hit:
            q3rec["unmatched"] += 1
        else:
            vals = {m for m, _ in hit}
            q3rec["on file" if vals == {"on file"} else
                  ("not on file" if vals == {"not on file"} else "mixed")] += 1
    out["q3_recoverable_vs_minutes"] = dict(q3rec)
    # why 'no_matching_meeting_row' happens: the meetings table itself has
    # year-sized holes, so those items cannot even be tested against minutes.
    cc_dates = collections.Counter(
        r[0][:4] for r in meets["rows"] if r[1] == "City Council")
    out["q3_council_meeting_rows_by_year"] = dict(sorted(cc_dates.items()))
    unm = [r for r in nod if r.get("date") and
           (r["date"], BODY.get(r.get("body"), r.get("body")) or "City Council") not in mins]
    out["q3_unmatched_by_year"] = dict(sorted(collections.Counter(r.get("year") for r in unm).items()))
    all_dates = {d for d, _ in mins}
    out["q3_unmatched_date_absent_from_table_entirely"] = sum(
        1 for r in unm if r["date"] not in all_dates)


    # ------------------------------------------------ Q4: cite_disposition
    q4 = [r for r in nod if (r.get("cite_disposition") or "").strip()]
    out["q4_no_disp_but_cite_disposition"] = len(q4)
    out["q4_examples"] = [{"item_id": r["item_id"], "url": r["url"],
                           "cite_disposition": r["cite_disposition"]}
                          for r in q4[:15]]
    out["q4_cite_disposition_values"] = collections.Counter(
        (r["cite_disposition"] or "").strip() for r in q4).most_common(15)
    out["cite_disposition_present_overall"] = sum(
        1 for r in items if (r.get("cite_disposition") or "").strip())

    # ------------------------------------------------ Q5: has_citation
    nc = [r for r in items if not r.get("has_citation")]
    out["q5_no_citation_total"] = len(nc)
    out["q5_by_type"] = {t: {"no_cite": c, "total": tot_type[t],
                             "pct": round(100 * c / tot_type[t], 1)}
                         for t, c in collections.Counter(r.get("type") for r in nc).most_common()}
    out["q5_by_year"] = {y: {"no_cite": c, "total": tot_year[y],
                             "pct": round(100 * c / tot_year[y], 1)}
                         for y, c in sorted(collections.Counter(r.get("year") for r in nc).items()) if y}
    # 2x2 contingency
    a = sum(1 for r in items if not r["has_citation"] and r["no_disposition"])
    b_ = sum(1 for r in items if not r["has_citation"] and not r["no_disposition"])
    c_ = sum(1 for r in items if r["has_citation"] and r["no_disposition"])
    d_ = sum(1 for r in items if r["has_citation"] and not r["no_disposition"])
    out["q5_contingency"] = {"no_cite_and_no_disp": a, "no_cite_and_disp": b_,
                             "cite_and_no_disp": c_, "cite_and_disp": d_}
    out["q5_phi"] = round((a * d_ - b_ * c_) /
                          (((a + b_) * (c_ + d_) * (a + c_) * (b_ + d_)) ** 0.5), 4)
    out["q5_no_cite_date_from"] = dict(collections.Counter(r.get("date_from") for r in nc))
    # recoverability among no-citation items
    out["q5_no_cite_recoverable"] = sum(1 for x in recoverable
                                        if not by_key[x["key"]]["has_citation"])

    # -------------------------------------------- recoverability tiers
    # Tier A: a shipped dataset already records an outcome for this item.
    # Tier B: no shipped outcome, but the site's own meetings table says the
    #         clerk's minutes for that meeting ARE on file -- the record
    #         exists and has simply not been extracted.
    # Tier C: minutes not on file -- genuinely absent from the city's record.
    # Tier D: untestable (meeting missing from the meetings table, or the
    #         item carries no date at all).
    tierA = {x["key"] for x in recoverable}
    tiers = collections.Counter()
    tier_era = collections.defaultdict(collections.Counter)
    for r in nod:
        era = "legacy_2004_2015" if (r.get("year") or 0) <= 2015 else "modern_2016_2026"
        if r["key"] in tierA:
            t = "A_shipped_outcome"
        else:
            d = r.get("date")
            b = BODY.get(r.get("body"), r.get("body")) or "City Council"
            hit = mins.get((d, b)) if d else None
            if not hit:
                t = "D_untestable"
            else:
                vals = {m for m, _ in hit}
                t = ("B_minutes_on_file" if vals == {"on file"} else
                     "C_minutes_not_on_file" if vals == {"not on file"} else
                     "D_untestable")
        tiers[t] += 1
        tier_era[t][era] += 1
    out["recoverability_tiers"] = dict(tiers)
    out["recoverability_tiers_by_era"] = {k: dict(v) for k, v in tier_era.items()}
    # do the no-disposition items carry a link back to the city's document?
    out["no_disp_source_link_counts"] = dict(collections.Counter(
        len(r.get("source_links") or []) for r in nod).most_common())
    out["no_disp_with_any_source_link"] = sum(
        1 for r in nod if r.get("source_links"))
    out["no_disp_with_source_link_by_era"] = {
        "legacy_2004_2015": sum(1 for r in nod if r.get("source_links") and (r.get("year") or 0) <= 2015),
        "modern_2016_2026": sum(1 for r in nod if r.get("source_links") and (r.get("year") or 0) >= 2016)}

    (CORPUS / "disposition_gap_stats.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")

    with (CORPUS / "recoverable_dispositions.jsonl").open("w", encoding="utf-8") as fh:
        for x in sorted(recoverable, key=lambda r: (r["type"] or "", r["year"] or 0)):
            fh.write(json.dumps({
                "item_id": x["item_id"], "url": x["url"],
                "current": "no disposition",
                "recovered_outcome": x["recovered_outcome"],
                "source": x["source"], "confidence": x["confidence"],
            }, ensure_ascii=False) + "\n")
    print(json.dumps(out, indent=2, default=str)[:12000])
    print("... wrote", CORPUS / "disposition_gap_stats.json")
    print("... wrote", len(recoverable), "rows to recoverable_dispositions.jsonl")


if __name__ == "__main__":
    main()
