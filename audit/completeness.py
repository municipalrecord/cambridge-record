"""School Committee Completeness count for one year, over a built tree.
    completeness.py TREE VOTES_DIR YEAR [OUT.csv]
Four lists, each from the record's own rows, never from the pages:
  1. every meeting the district's portal lists (Data/Audits/sc_YEAR/
     portal_YEAR.csv) has a meeting page;
  2. every School Committee agenda item note in the vault for the year has
     an item page;
  3. every numbered item the minutes act on (votes_school.csv, main and
     charter rows the builder shows) has an item page that names that
     night, the second item of a reused number on its own page (SCB-1,
     Data/Curated/sc_reused_codes.csv), minutes-only items on theirs (SCB-2);
  4. that act also shows on the night's meeting page (a tile with its code).
A row that fails is printed and written to OUT; the exit code is the count."""
import csv, html, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
tree, votes, year = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
out = sys.argv[4] if len(sys.argv) > 4 else None
SC = tree / "boards" / "school-committee"
VAULT = (Path.home() / "Projects/record-onboarding-data/cambridge/"
         "school-committee-checks/vault/City Boards/School Committee/Items")


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def text(p):
    t = p.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<(script|style).*?</\1>", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def vkey(c):
    return re.sub(r"^(c?)0*(\d+)-0*(\d+)$", r"\1\2-\3", slug(c.lstrip("#")))


# page names pad the number ("sc-19-02"); the tables do not ("19-2")
PAGES = {}
for p_ in SC.glob("sc-*.html"):
    m_ = re.fullmatch(r"sc-(c?\d+-\d+)(-\d{4}-\d{2}-\d{2})?", p_.stem)
    if m_:
        PAGES[vkey(m_.group(1)) + (m_.group(2) or "")] = p_


def item_page(code, split_from=""):
    k = vkey(code) + (f"-{split_from}" if split_from else "")
    return PAGES.get(k, SC / f"sc-{k}.html")


def named(d, t):
    """the night named on the page, as an ISO date or "May 7, 2019"."""
    from datetime import date
    y, m, dd = map(int, d.split("-"))
    return d in t or date(y, m, dd).strftime("%b ") + f"{dd}, {y}" in t


rows, fails = [], []
def check(kind, key, ok, why=""):
    rows.append((kind, key, "ok" if ok else "missing", why))
    if not ok:
        fails.append((kind, key, why))

# 1. meetings
for r in csv.DictReader(open(ROOT / f"Data/Audits/sc_{year}/portal_{year}.csv",
                             encoding="utf-8")):
    p = SC / f"{r['date']}-school-committee-{slug(r['mtype'])}.html"
    check("meeting", f"{r['date']} {r['mtype']}", p.exists(), p.name)

# 2. agenda items in the vault
for n in sorted(VAULT.glob("SC *.md")):
    fm = n.read_text(encoding="utf-8", errors="replace")[:400]
    d = re.search(r"^date: (\d{4})", fm, flags=re.M)
    if not d or d.group(1) != year:
        continue
    code = n.stem[3:]
    check("agenda item", code, item_page(code).exists(), item_page(code).name)

# 3 and 4. acts in the minutes
split = {}
for r in csv.DictReader(open(ROOT / "Data/Curated/sc_reused_codes.csv",
                             encoding="utf-8")):
    split.setdefault(r["code"].lstrip("#"), []).append(r)
seen = set()
for v in csv.DictReader(open(votes / "votes_school.csv", encoding="utf-8")):
    if v["date"][:4] != year or v["status"] not in ("parsed", "confirmed"):
        continue
    if v["scope"] not in ("main", "charter"):
        continue
    key = (v["date"], v["mtype"], v["code"])
    if key in seen:
        continue
    seen.add(key)
    p = item_page(v["code"])
    for s in split.get(v["code"], ()):
        first = "stays with the first item" in (v.get("note") or "")
        if v["date"] > s["from_date"] or (
                v["date"] == s["from_date"] and not first):
            p = item_page(v["code"], s["from_date"])
    ok = p.exists() and named(v["date"], text(p))
    check("act: item page", f"{v['date']} {v['code']}", ok,
          p.name + ("" if p.exists() else " (no page)"))
    m = SC / f"{v['date']}-school-committee-{slug(v['mtype'])}.html"
    c = v["code"].lstrip("#")
    yy, nn = re.fullmatch(r"(C?\d+)-0*(\d+)", c).groups()
    ok = m.exists() and re.search(r"(?<![\d-])#?" + yy + r"-0*" + nn +
                                  r"(?!\d)", text(m)) is not None
    check("act: meeting tile", f"{v['date']} {v['code']}", ok, m.name)

kinds = {}
for k, _key, res, _w in rows:
    kinds.setdefault(k, [0, 0])[res == "ok"] += 1
for k, (bad, good) in kinds.items():
    print(f"{year} {k}: {good + bad} rows, {bad} missing")
for f in fails:
    print("MISSING", *f)
if out:
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["list", "key", "result", "page"])
        w.writerows(rows)
sys.exit(min(len(fails), 255))
