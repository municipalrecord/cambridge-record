"""Deterministic entity extraction for City Manager's Agenda items.

CMA titles are highly formulaic -- appropriations, grants, transfers, and
appointment lists -- so regex beats a language model here on both precision
and reproducibility. It also cannot get bored 6,000 rows in and start
emitting boilerplate, which is how the model pass failed.

What this does NOT attempt: free-text vendor and organisation names, which
are genuinely irregular. Those stay a model job, layered on top.
"""
import csv, json, re, sys, collections, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SHARD = ROOT / "corpus" / "shards" / "cma.tsv"
OUT = ROOT / "corpus" / "entities_cma.jsonl"

RE_MONEY = re.compile(r"\$\s?([\d][\d,]*(?:\.\d{2})?)")
RE_APPT = re.compile(r"\b(re)?appointment\b", re.I)
# "... as (a|members of) the Foo Commission ..." up to a comma/effective/for
RE_BODY = re.compile(
    r"\bas\s+(?:a\s+|an\s+|members?\s+of\s+)?(?:the\s+)?"
    r"([A-Z][A-Za-z&'\-]*(?:\s+(?:of|on|and|for|the)?\s*[A-Z][A-Za-z&'\-]*)*)"
    r"(?=\s*(?:,|for|effective|while|to\b|$))")
RE_SUFFIX = re.compile(r"^(Jr\.?|Sr\.?|I{2,3}|IV|Esq\.?|M\.?D\.?|Ph\.?D\.?)$", re.I)
RE_PERSON = re.compile(
    r"^(?:Dr\.|Mr\.|Ms\.|Mrs\.|Rev\.)?\s*"
    r"[A-Z][A-Za-z'\-]+(?:\s+[A-Z]\.?)*(?:\s+[A-Z][A-Za-z'\-]+){1,3}$")
RE_STREETNUM = re.compile(r"^\d+[A-Za-z]?\s+\S")
RE_STATEZIP = re.compile(r"^[A-Z]{2}\s+\d{5}")
CITIES = {"cambridge", "boston", "somerville", "medford", "arlington",
          "belmont", "watertown", "brookline", "newton", "malden", "everett"}


def norm_person(name):
    n = re.sub(r"\b(Dr|Mr|Ms|Mrs|Rev)\.?\s+", "", name).strip(" .,")
    n = re.sub(r"\s+", " ", n)
    parts = [p for p in n.split() if not RE_SUFFIX.match(p)]
    if len(parts) < 2:
        return n.lower()
    return f"{parts[-1]}, {' '.join(parts[:-1])}".lower().replace(".", "")


def norm_generic(s):
    s = re.sub(r"\b(llc|inc|corp|co|lp|ltd)\b\.?", "", s, flags=re.I)
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def parse_people(segment):
    """Pull (person, address) pairs out of a post-colon roster."""
    out = []
    for chunk in re.split(r";", segment):
        toks = [t.strip() for t in chunk.split(",") if t.strip()]
        cur, addr = None, []
        for t in toks:
            if RE_SUFFIX.match(t):
                if cur:
                    cur = f"{cur} {t}"
                continue
            if RE_STREETNUM.match(t):
                addr.append(t)
                continue
            if RE_STATEZIP.match(t) or t.lower().rstrip(".") in CITIES:
                if addr:
                    addr.append(t)
                continue
            if RE_PERSON.match(t):
                if cur:
                    out.append((cur, ", ".join(addr) if addr else None))
                cur, addr = t, []
        if cur:
            out.append((cur, ", ".join(addr) if addr else None))
    return out


def parse(row):
    title = row["title"]
    ents, seen = [], set()

    def add(name, kind, role, normalized=None):
        name = name.strip(" .,;:")
        if not name or len(name) < 3:
            return
        key = (normalized or norm_generic(name), role)
        if key in seen:
            return
        seen.add(key)
        ents.append({"name": name, "normalized": normalized or norm_generic(name),
                     "kind": kind, "role": role})

    for r in (row.get("requesters") or "").split(";"):
        r = r.strip()
        if not r:
            continue
        who = r.split(",")[0].strip()
        if RE_PERSON.match(who):
            add(who, "person", "sponsor", norm_person(who))

    is_appt = bool(RE_APPT.search(title))
    role = "reappointee" if re.search(r"\breappointment\b", title, re.I) else "appointee"

    if is_appt and ":" in title:
        head, _, tail = title.partition(":")
        for person, addr in parse_people(tail):
            add(person, "person", role, norm_person(person))
            if addr:
                add(addr, "address", "residence")
        m = RE_BODY.search(head)
        if m:
            add(m.group(1), "gov_body", "subject")
    elif is_appt:
        m = RE_BODY.search(title)
        if m:
            add(m.group(1), "gov_body", "subject")

    amounts = [float(a.replace(",", "")) for a in RE_MONEY.findall(title)]

    return {
        "item_id": row["item_id"], "date": row.get("date") or None, "type": "CMA",
        "dollar_amount": max(amounts) if amounts else None,
        "dollar_amounts": amounts or None,
        "is_appointment": is_appt,
        "entities": ents,
        "extractor": "deterministic",
    }


def main():
    rows = list(csv.DictReader(SHARD.open(encoding="utf-8"), delimiter="\t"))
    n_ent = 0
    kinds, roles = collections.Counter(), collections.Counter()
    with OUT.open("w", encoding="utf-8") as fh:
        for row in rows:
            rec = parse(row)
            n_ent += len(rec["entities"])
            for e in rec["entities"]:
                kinds[e["kind"]] += 1
                roles[e["role"]] += 1
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"{len(rows)} rows -> {n_ent} entities ({n_ent/len(rows):.2f}/item)")
    print("kinds:", kinds.most_common())
    print("roles:", roles.most_common())
    return 0


if __name__ == "__main__":
    sys.exit(main())
