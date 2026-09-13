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
import json, collections, itertools, pathlib, sys, re

ROOT = pathlib.Path(__file__).resolve().parent
CORPUS = ROOT / "corpus"
URL = "https://cambridgerecord.org/items/{}.html"

# Entities that are structurally uninteresting as "players".
SKIP_KINDS = {"gov_body"}


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
    out = []
    by_item = {r.get("item_id"): r for r in recs}

    # 1. Shell-cluster: many distinct private orgs tied to one address.
    addr_orgs = collections.defaultdict(set)
    for r in recs:
        addrs = [e for e in (r.get("entities") or []) if e.get("kind") == "address"]
        orgs = [e for e in (r.get("entities") or []) if e.get("kind") == "org_private"]
        for a in addrs:
            for o in orgs:
                addr_orgs[a.get("normalized") or a.get("name")].add(
                    o.get("normalized") or o.get("name"))
    for addr, orgs in sorted(addr_orgs.items(), key=lambda kv: -len(kv[1])):
        if len(orgs) >= 3:
            out.append(("shell-cluster", len(orgs),
                        f"{len(orgs)} distinct private entities tied to `{addr}`",
                        sorted(orgs)[:12],
                        ents.get(addr, {}).get("items", [])[:8]))

    # 2. Persistent players: private parties recurring over many years.
    for key, a in ents.items():
        if a["kind"] in SKIP_KINDS or a["count"] < 8:
            continue
        if a["first_seen"] and a["last_seen"]:
            span = int(a["last_seen"][:4]) - int(a["first_seen"][:4])
            if span >= 5 and a["kind"] in ("org_private", "firm", "person"):
                out.append(("persistent-player", a["count"],
                            f"`{a['name']}` ({a['kind']}) appears in {a['count']} "
                            f"items across {span} years "
                            f"({a['first_seen'][:4]}-{a['last_seen'][:4]})",
                            [f"roles: {dict(a['roles'])}"], a["items"][:8]))

    # 3. Role conflict: same party both seeking and granting.
    seeking = {"applicant", "petitioner", "vendor", "grantee", "owner", "buyer"}
    granting = {"appointee", "reappointee", "sponsor"}
    for key, a in ents.items():
        r = set(a["roles"])
        if r & seeking and r & granting and a["kind"] == "person":
            out.append(("role-conflict", a["count"],
                        f"`{a['name']}` appears both as {sorted(r & seeking)} "
                        f"and {sorted(r & granting)}",
                        [f"roles: {dict(a['roles'])}"], a["items"][:8]))

    # 4. Repeat representative across unrelated applicants.
    rep_clients = collections.defaultdict(set)
    for r in recs:
        es = r.get("entities") or []
        reps = [e for e in es if e.get("role") == "representative"
                or e.get("kind") == "firm"]
        cli = [e for e in es if e.get("role") in ("applicant", "petitioner", "owner")]
        for rep in reps:
            for c in cli:
                rep_clients[rep.get("normalized") or rep.get("name")].add(
                    c.get("normalized") or c.get("name"))
    for rep, cl in sorted(rep_clients.items(), key=lambda kv: -len(kv[1])):
        if len(cl) >= 4:
            out.append(("repeat-representative", len(cl),
                        f"`{rep}` represents {len(cl)} distinct applicants",
                        sorted(cl)[:12], ents.get(rep, {}).get("items", [])[:8]))

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
            "shell-cluster": "Shell clusters — many named entities, one address",
            "persistent-player": "Persistent players",
            "role-conflict": "Role conflicts — seeking and granting",
            "repeat-representative": "Repeat representatives",
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
