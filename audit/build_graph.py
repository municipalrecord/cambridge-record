"""Resolve extracted entities into a graph and surface investigative leads.

Reads audit/corpus/entities_*.jsonl (produced by the extraction passes) and
emits:
  corpus/entity_index.jsonl  one record per resolved entity
  corpus/leads.md            ranked leads with citations

The lead heuristics are deliberately the patterns that made the DND Homes
teardown pipeline a story: many separately-named shells behind one address,
one party recurring across nominally unrelated matters, and a representative
who turns up for applicants that should have nothing to do with each other.
"""
import json, collections, pathlib, sys, re
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent
CORPUS = ROOT / "corpus"
URL = "https://cambridgerecord.org/items/{}.html"

# Entities that are structurally uninteresting as "players".
SKIP_KINDS = {"gov_body"}

# A parcel address, not a place name. The extraction passes label both
# "address": "139 First Street" and "Harvard Square" / "Alewife" / "Danehy
# Park". Only the first kind can anchor a shell cluster -- grouping private
# entities by "Harvard Square" would manufacture a cluster out of every
# unrelated business in the square.
RE_PARCEL = re.compile(r"^\d+[A-Za-z]?(?:\s*[-&]\s*\d+[A-Za-z]?)*\s+\S")


# "us parcel a" / "us parcel b" -> stem "us parcel"
RE_SERIAL = re.compile(r"^(.*?)[\s\-]+(?:[a-z]|\d{1,3}|i{1,3}|iv|v)$")
# an entity named for the property it holds: "9 wyman road", "30 brookford street"
RE_ADDRNAME = re.compile(
    r"\b\d+[a-z]?\s+\w+(?:\s+\w+)?\s+"
    r"(street|st|road|rd|avenue|ave|lane|place|pl|terrace|way|drive|dr|court|ct)\b")
BURST_DAYS = 120
# Serial matching on resolution titles otherwise yields "june 4 / june 11 /
# june 20" as a shell family. Dates are not entities.
SERIAL_STOPWORDS = {
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "monday", "tuesday",
    "wednesday", "thursday", "friday", "saturday", "sunday", "week", "day",
    "chapter", "section", "article", "phase", "ward", "district", "precinct",
}
# Above this many sponsorships the person is a sitting councillor, not a party.
COUNCILLOR_SPONSOR_FLOOR = 20


def is_parcel(ent):
    return (ent.get("kind") == "address"
            and bool(RE_PARCEL.match((ent.get("name") or "").strip())))


def slug(item_id):
    return item_id.lower().replace(" ", "-").replace("#", "")


def load():
    recs = []
    for p in sorted(CORPUS.glob("entities_*.jsonl")):
        n = 0
        for line in p.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
                n += 1
            except json.JSONDecodeError:
                continue
        print(f"  {p.name}: {n} records", file=sys.stderr)
    return recs


def build(recs):
    ents = collections.defaultdict(lambda: {
        "name": None, "kind": None, "normalized": None,
        "items": [], "roles": collections.Counter(),
        "kinds": collections.Counter(), "names": collections.Counter(),
        "dates": []})
    per_item = collections.defaultdict(list)

    for r in recs:
        iid = r.get("item_id")
        for e in r.get("entities") or []:
            key = (e.get("normalized") or e.get("name") or "").strip().lower()
            if not key:
                continue
            a = ents[key]
            a["normalized"] = key
            a["names"][e.get("name") or key] += 1
            a["kinds"][e.get("kind") or "unknown"] += 1
            a["roles"][e.get("role") or "unknown"] += 1
            a["items"].append(iid)
            if r.get("date"):
                a["dates"].append(r["date"])
            per_item[iid].append(key)

    for key, a in ents.items():
        a["name"] = a["names"].most_common(1)[0][0]
        a["kind"] = a["kinds"].most_common(1)[0][0]
        a["items"] = sorted(set(a["items"]))
        a["count"] = len(a["items"])
        a["first_seen"] = min(a["dates"]) if a["dates"] else None
        a["last_seen"] = max(a["dates"]) if a["dates"] else None
    return ents, per_item


def leads(ents, per_item, recs):
    """Rank patterns that look like deliberate structuring.

    The first version of this grouped private entities by shared address and
    called the result a shell cluster. That detects commercial tenant turnover,
    not structuring: 730 Massachusetts Avenue surfaced six "entities" that are
    one restaurant renaming itself across twenty years, and 99 Mount Auburn
    surfaced a succession of nail salons. Shared address alone is worthless.

    What actually separated the DND Homes pipeline from ordinary churn was the
    conjunction of three things, and these heuristics require at least two:
      - a BURST: filings days apart, not decades
      - SERIAL naming: entities differing by one token (US-Parcel A/B/C/D)
      - entities NAMED FOR the parcel they hold ("9 Wyman Road LLC")
    plus a shared human fronting them.
    """
    out = []
    by_item = {r.get("item_id"): r for r in recs}

    def dt(rec):
        d = rec.get("date")
        return date.fromisoformat(d) if d else None

    def priv(r):
        return [e for e in (r.get("entities") or [])
                if e.get("kind") == "org_private"
                and e.get("role") in ("applicant", "petitioner", "owner", "buyer")]

    def reps(r):
        return [e for e in (r.get("entities") or [])
                if e.get("role") == "representative"]

    # -- serialized names: "us parcel a" / "us parcel b" share a stem -------
    stems = collections.defaultdict(set)
    for key, a in ents.items():
        if a["kind"] != "org_private":
            continue
        m = RE_SERIAL.match(key)
        if m and len(m.group(1)) >= 4:
            stem = m.group(1).strip()
            if stem.split()[-1] in SERIAL_STOPWORDS or stem in SERIAL_STOPWORDS:
                continue
            stems[stem].add(key)
    for stem, members in stems.items():
        if len(members) >= 3:
            items = sorted({i for k in members for i in ents[k]["items"]})
            out.append(("serial-entities", 100 + len(members),
                        f"{len(members)} serially-named entities share the stem "
                        f"`{stem}`",
                        sorted(members)[:12], items[:8]))

    # -- entities named for a street -------------------------------------
    named = [a for a in ents.values()
             if a["kind"] == "org_private" and RE_ADDRNAME.search(a["normalized"])]
    by_rep = collections.defaultdict(set)
    for r in recs:
        for rep in reps(r):
            for o in priv(r):
                if RE_ADDRNAME.search(o.get("normalized") or ""):
                    by_rep[rep.get("normalized")].add(o.get("normalized"))
    for rep, orgs in by_rep.items():
        if len(orgs) >= 2:
            items = sorted({i for o in orgs if o in ents for i in ents[o]["items"]})
            out.append(("address-named-shells", 90 + len(orgs),
                        f"`{rep}` fronts {len(orgs)} entities each named for a "
                        f"property",
                        sorted(orgs)[:12], items[:8]))

    # -- bursts: one representative, several private applicants, days apart -
    rep_filings = collections.defaultdict(list)
    for r in recs:
        d = dt(r)
        if not d:
            continue
        for rep in reps(r):
            for o in priv(r):
                rep_filings[rep.get("normalized")].append(
                    (d, o.get("normalized"), r.get("item_id")))
    for rep, fil in rep_filings.items():
        fil.sort()
        for i, (d0, _, _) in enumerate(fil):
            win = [f for f in fil[i:] if (f[0] - d0).days <= BURST_DAYS]
            orgs = {f[1] for f in win}
            if len(orgs) >= 3:
                span = (win[-1][0] - d0).days
                out.append(("filing-burst", 80 + len(orgs),
                            f"`{rep}` filed for {len(orgs)} distinct entities "
                            f"within {span} days ({d0})",
                            sorted(orgs)[:12],
                            sorted({f[2] for f in win})[:8]))
                break

    # -- persistent private players ---------------------------------------
    for key, a in ents.items():
        if a["kind"] not in ("org_private", "firm") or a["count"] < 8:
            continue
        if a["first_seen"] and a["last_seen"]:
            span = int(a["last_seen"][:4]) - int(a["first_seen"][:4])
            if span >= 5:
                out.append(("persistent-player", min(a["count"], 60),
                            f"`{a['name']}` appears in {a['count']} items across "
                            f"{span} years ({a['first_seen'][:4]}-"
                            f"{a['last_seen'][:4]})",
                            [f"roles: {dict(a['roles'])}"], a["items"][:8]))

    # -- role conflict, excluding councillors ------------------------------
    # Every councillor sponsors thousands of orders, so "sponsors AND once
    # applied for something" fires on all of them and means nothing. Require
    # the granting side to be small enough that the person is not simply a
    # sitting member.
    seeking = {"applicant", "petitioner", "vendor", "grantee", "owner", "buyer"}
    granting = {"appointee", "reappointee"}
    for key, a in ents.items():
        if a["kind"] != "person":
            continue
        r = set(a["roles"])
        if a["roles"].get("sponsor", 0) > COUNCILLOR_SPONSOR_FLOOR:
            continue
        if r & seeking and r & granting:
            out.append(("role-conflict", 50 + a["count"],
                        f"`{a['name']}` appears both as {sorted(r & seeking)} "
                        f"and {sorted(r & granting)}",
                        [f"roles: {dict(a['roles'])}"], a["items"][:8]))

    out.sort(key=lambda t: -t[1])
    return out


def main():
    CORPUS.mkdir(parents=True, exist_ok=True)
    print("loading entity files...", file=sys.stderr)
    recs = load()
    if not recs:
        print("no entities_*.jsonl found yet -- run after extraction passes finish")
        return 1
    ents, per_item = build(recs)
    print(f"{len(recs)} items, {len(ents)} resolved entities", file=sys.stderr)

    with (CORPUS / "entity_index.jsonl").open("w", encoding="utf-8") as fh:
        for key, a in sorted(ents.items(), key=lambda kv: -kv[1]["count"]):
            fh.write(json.dumps({
                "normalized": key, "name": a["name"], "kind": a["kind"],
                "count": a["count"], "roles": dict(a["roles"]),
                "aliases": [n for n, _ in a["names"].most_common()],
                "first_seen": a["first_seen"], "last_seen": a["last_seen"],
                "items": a["items"],
            }, ensure_ascii=False) + "\n")

    ld = leads(ents, per_item, recs)
    with (CORPUS / "leads.md").open("w", encoding="utf-8") as fh:
        fh.write("# Investigative leads\n\n")
        fh.write(f"Generated from {len(recs)} items and {len(ents)} resolved "
                 f"entities.\n\nEvery lead below is a *pattern in the record*, "
                 "not a finding. Each needs a human to check it against the "
                 "underlying documents before it is worth anything.\n\n")
        by_kind = collections.defaultdict(list)
        for kind, score, desc, detail, items in ld:
            by_kind[kind].append((score, desc, detail, items))
        titles = {
            "serial-entities": "Serially-named entities (US-Parcel A/B/C/D shape)",
            "address-named-shells": "One representative, several entities each named for a property",
            "filing-burst": f"Filing bursts — one representative, 3+ entities within {BURST_DAYS} days",
            "persistent-player": "Persistent private players",
            "role-conflict": "Role conflicts — seeking and appointed",
        }
        for kind, rows in by_kind.items():
            fh.write(f"\n## {titles.get(kind, kind)} ({len(rows)})\n\n")
            for score, desc, detail, items in rows[:40]:
                fh.write(f"- {desc}\n")
                for d in detail[:6]:
                    fh.write(f"  - {d}\n")
                if items:
                    links = ", ".join(f"[{i}]({URL.format(slug(i))})" for i in items)
                    fh.write(f"  - items: {links}\n")
    print(f"wrote {CORPUS/'entity_index.jsonl'} and {CORPUS/'leads.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
