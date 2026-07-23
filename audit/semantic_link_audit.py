#!/usr/bin/env python3
"""Semantic link audit, internal half (roadmap: Trust & scrutiny).

The integrity gate proves every internal link RESOLVES; this proves every
link that CLAIMS an identity lands on that identity. Three layers, all
offline, total coverage:

  A. identity  — every items/<slug>.html declares (in <title>) the same
                 docket code its slug encodes.
  B. anchors   — every <a> whose visible text or title= claims a docket
                 code ("AR 2025-33", "Policy Order 2025 #165") links to
                 that item's page — the anchor-claim vs target-code check.
  C. db cross  — every portal href and reader link on an item page is
                 checked against the db: Detail_LegiFile?ID=N must be the
                 LegiFile the db records for this item; FileOpen?…ID=F and
                 docs/F.html must be attachments of this item; PrimeGov
                 /portal/item/P must carry this item's tracking.

Also writes the external crawl manifest (what each live URL is *supposed*
to contain, plus the archived sha256 for PDFs) for the online half.

    python3 site/semantic_link_audit.py site/out
"""
import json
import re
import sqlite3
import sys
from collections import Counter
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT.parent / "Data" / "cambridge.db"

A_TAG = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.S | re.I)
HREF = re.compile(r"""href=["']([^"']+)["']""")
TITLE_ATTR = re.compile(r"""title=["']([^"']+)["']""")
TAGS = re.compile(r"<[^>]+>")
PAGE_TITLE = re.compile(r"<title>(.*?)</title>", re.S)

# stem form (AR 2025-33 / POR 2025 #165) — prefix, year, number
STEM = re.compile(r"\b(POR|PO|CMA|AR|ARS|APP|RES|ORD|COF|CHS|HS|HR|COM)"
                  r"[  -](\d{4})[  ]?[-#](\d+)\b")
# humanized form (Policy Order 2025 #165)
NAMES = {
    "policy order": ("por", "po"),
    "city manager's agenda": ("cma",),
    "city manager’s agenda": ("cma",),
    "awaiting report status update": ("ars",),
    "awaiting report": ("ar",),
    "application & petition": ("app",), "application &amp; petition": ("app",),
    "resolution": ("res",), "ordinance": ("ord",),
    "communication from a city officer": ("cof",),
    "committee hearing schedule": ("chs", "hs", "hr"),
    "hearing schedule": ("hs", "hr"),
}
HUMAN = re.compile(r"\b(" + "|".join(re.escape(n) for n in NAMES) + r")"
                   r"\s+(\d{4})\s*#(\d+)", re.I)

ITEM_HREF = re.compile(r"(?:^|/)items/([a-z]+-\d{4}-\d+)\.html(?:#.*)?$")
DOCS_HREF = re.compile(r"(?:^|/)docs/(\d+)\.html(?:#.*)?$")
LEGIFILE = re.compile(r"Detail_LegiFile\.aspx\?ID=(\d+)", re.I)
FILEOPEN = re.compile(r"FileOpen\.aspx\?Type=(\d+)&(?:amp;)?ID=(\d+)", re.I)
PG_ITEM = re.compile(r"primegov\.com/portal/item/(\d+)", re.I)


def norm(prefix, year, num):
    return f"{prefix.lower()}-{year}-{int(num)}"


def claims_in(text):
    """Every docket-code claim in a blob of text, as candidate slug sets."""
    text = unescape(TAGS.sub(" ", text))
    out = []
    for m in STEM.finditer(text):
        p, y, n = m.groups()
        cands = {norm(p, y, n)}
        if p == "PO":
            cands.add(norm("POR", y, n))
        if p in ("CHS", "HS", "HR"):
            cands |= {norm(q, y, n) for q in ("CHS", "HS", "HR")}
        out.append((m.group(0), cands))
    for m in HUMAN.finditer(text):
        name, y, n = m.groups()
        cands = {norm(p, y, n) for p in NAMES[name.lower()]}
        out.append((m.group(0), cands))
    return out


def tracking_slug(tracking):
    """db tracking ('POR 2025 #165', 'COM 2026-08', 'COM 94 #2026') -> slug."""
    if not tracking:
        return None
    m = re.match(r"([A-Za-z]+)[ -](\d+)[ ]?[-#][ ]?(\d+)", tracking.strip())
    if not m:
        return None
    p, a, b = m.groups()
    if len(a) == 4:
        y, n = a, b
    elif len(b) == 4:
        y, n = b, a                    # 'COM 94 #2026' is reversed
    else:
        y, n = str(2000 + int(a)), b   # 'ARS-24-23' = two-digit year first
    return norm(p, y, n)


def load_db():
    cx = sqlite3.connect(DB)
    legifile, attach, pg = {}, {}, {}
    for iid, tr in cx.execute(
            "SELECT item_id, tracking FROM agenda_items WHERE portal='iqm2'"):
        legifile[str(iid)] = tr
    # item ids collide across portals (iqm2 and primegov both use small
    # integers) — every join is keyed by (portal, item_id) or it recreates
    # the exact confusion this audit exists to catch
    for po, iid, file in cx.execute(
            "SELECT portal, item_id, file FROM item_attachments"):
        attach.setdefault(re.sub(r"\.pdf$", "", file or ""),
                          set()).add((po, str(iid)))
    # pre-backfill items carry their (single) attachment on the item row
    for po, iid, file in cx.execute(
            "SELECT portal, item_id, file FROM agenda_items WHERE file != ''"):
        attach.setdefault(re.sub(r"\.pdf$", "", file or ""),
                          set()).add((po, str(iid)))
    itemtrack = {(po, str(iid)): tr for po, iid, tr in cx.execute(
        "SELECT portal, item_id, tracking FROM agenda_items")}
    for iid, tr, pid in cx.execute(
            "SELECT item_id, tracking, portal_id FROM pg_item_uuids"):
        if pid:
            pg[str(pid)] = tr or itemtrack.get(("primegov", str(iid)))
    sha = dict(cx.execute("SELECT file, sha256 FROM doc_meta"))
    cx.close()
    return legifile, attach, itemtrack, pg, sha


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out")
    legifile, attach, itemtrack, pg, sha = load_db()
    att_slugs = {f: {tracking_slug(itemtrack.get(k)) for k in ids} - {None}
                 for f, ids in attach.items()}

    findings = []          # (layer, source page, evidence)
    stats = Counter()
    manifest = {}          # url -> {kind, expect, sha256, sources}

    # auditors/practice-* carry deliberately planted discrepancies (the
    # certification exercise) — auditing them would flag the curriculum
    pages = [f for f in root.rglob("*.html")
             if "pagefind" not in f.parts
             and not (f.parts[-2:-1] == ("auditors",)
                      and f.name.startswith("practice-"))]

    ITEM_PAGE = re.compile(r"^[a-z]+-\d{4}-\d+$")

    # --- A. identity: slug vs <title> ---------------------------------
    for f in sorted((root / "items").glob("*.html")):
        if not ITEM_PAGE.match(f.stem):
            continue        # index + type-explainer pages carry no code
        slug_ = f.stem
        t = f.read_text(errors="replace")
        m = PAGE_TITLE.search(t)
        title = unescape(m.group(1)) if m else ""
        cl = claims_in(title)
        stats["item pages"] += 1
        if not cl:
            findings.append(("A", f.relative_to(root),
                             f"title declares no code: {title[:80]!r}"))
        elif not any(slug_ in cands for _, cands in cl):
            findings.append(("A", f.relative_to(root),
                             f"title says {cl[0][0]!r}, slug says {slug_}"))

    # --- B + C + manifest ---------------------------------------------
    for f in pages:
        rel = f.relative_to(root)
        page_slug = f.stem if rel.parts[0] == "items" \
            and ITEM_PAGE.match(f.stem) else None
        t = f.read_text(errors="replace")
        for m in A_TAG.finditer(t):
            attrs, inner = m.groups()
            hm = HREF.search(attrs)
            if not hm:
                continue
            href = unescape(hm.group(1))
            tm = TITLE_ATTR.search(attrs)
            text = TAGS.sub(" ", inner) + " " + (tm.group(1) if tm else "")

            # resolve relative hrefs against the page's own directory so
            # same-directory links ("por-2025-1.html" inside items/) are
            # seen — matching on the raw string silently skips them
            resolved = None
            if not href.startswith(("http:", "https:", "mailto:", "#")):
                p = href.split("#")[0].split("?")[0]
                if p:
                    base = root if p.startswith("/") else f.parent
                    try:
                        resolved = (base / p.lstrip("/")).resolve() \
                            .relative_to(root.resolve()).as_posix()
                    except (OSError, ValueError):
                        resolved = None

            # B: claim in anchor vs internal item target
            im = ITEM_HREF.search(resolved) if resolved else None
            cl = claims_in(text)
            if im:
                stats["item links"] += 1
                if cl:
                    stats["item links w/ claim"] += 1
                    target = im.group(1)
                    if not any(target in cands for _, cands in cl):
                        findings.append(("B", rel,
                                         f"anchor {cl[0][0]!r} -> items/{target}.html"))

            # B: claim in anchor vs reader-page target (answer links)
            dm = DOCS_HREF.search(resolved) if resolved else None
            if dm and cl:
                stats["docs links w/ claim"] += 1
                slugs = att_slugs.get(dm.group(1), set())
                if slugs and not any(slugs & cands for _, cands in cl):
                    findings.append(("B", rel,
                                     f"anchor {cl[0][0]!r} -> docs/{dm.group(1)}.html "
                                     f"which belongs to {sorted(slugs)}"))

            # C: reader pages link the FileOpen endpoint for their own
            # document — the id in the URL must be the page's own doc id
            if rel.parts[0] == "docs" and re.match(r"^\d+$", f.stem):
                fo = FILEOPEN.search(href)
                if fo:
                    stats["fileopen links (readers)"] += 1
                    fid = fo.group(2)
                    if fid != f.stem:
                        findings.append(("C", rel,
                                         f"reader for doc {f.stem} links "
                                         f"FileOpen ID={fid}"))
                    manifest.setdefault(href, {
                        "kind": "fileopen", "expect": f"doc {f.stem}",
                        "sha256": sha.get(f"{fid}.pdf"),
                        "sources": []})["sources"].append(str(rel))

            # C: portal hrefs on item pages, checked against the db
            if page_slug:
                lm = LEGIFILE.search(href)
                if lm:
                    stats["legifile links"] += 1
                    tr = legifile.get(lm.group(1))
                    tslug = tracking_slug(tr)
                    if lm.group(1) not in legifile:
                        findings.append(("C", rel,
                                         f"LegiFile ID={lm.group(1)} unknown to db"))
                    elif tslug is None:
                        findings.append(("C", rel,
                                         f"LegiFile ID={lm.group(1)} tracking "
                                         f"{tr!r} unparseable"))
                    elif tslug != page_slug:
                        findings.append(("C", rel,
                                         f"LegiFile ID={lm.group(1)} is {tr!r}, "
                                         f"page is {page_slug}"))
                    mrow = manifest.setdefault(href, {
                        "kind": "legifile", "expect": tr, "sources": []})
                    mrow["sources"].append(str(rel))
                fo = FILEOPEN.search(href)
                if fo:
                    stats["fileopen links"] += 1
                    fid = fo.group(2)
                    slugs = att_slugs.get(fid, set())
                    if not slugs:
                        # older items declare their pdf in the vault note,
                        # not the db — db silence is not a conflict; the
                        # external crawl hash-checks these directly
                        stats["fileopen unverifiable offline"] += 1
                    elif page_slug not in slugs:
                        findings.append(("C", rel,
                                         f"FileOpen ID={fid} belongs to {sorted(slugs)}, "
                                         f"page is {page_slug}"))
                    mrow = manifest.setdefault(href, {
                        "kind": "fileopen", "expect": page_slug,
                        "sha256": sha.get(f"{fid}.pdf"), "sources": []})
                    mrow["sources"].append(str(rel))
                pm = PG_ITEM.search(href)
                if pm:
                    stats["primegov links"] += 1
                    tr = pg.get(pm.group(1))
                    tslug = tracking_slug(tr)
                    if tslug is None:
                        findings.append(("C", rel,
                                         f"PrimeGov portal id {pm.group(1)} unknown to db"))
                    elif tslug != page_slug:
                        findings.append(("C", rel,
                                         f"PrimeGov portal id {pm.group(1)} is {tr!r}, "
                                         f"page is {page_slug}"))
                    mrow = manifest.setdefault(href, {
                        "kind": "primegov", "expect": tr, "sources": []})
                    mrow["sources"].append(str(rel))

    out = ROOT / "external_link_manifest.json"
    out.write_text(json.dumps(manifest, indent=1))

    # stats snapshot for the published results page (links_audit) — the
    # page must cite the run's numbers, not re-derive them
    from datetime import date
    (ROOT / "semantic_link_stats.json").write_text(json.dumps({
        "date": date.today().isoformat(), "pages": len(pages),
        "stats": dict(stats), "findings": len(set(findings)),
        "manifest_urls": len(manifest)}, indent=1))

    print(f"semantic link audit (internal) — {len(pages):,} pages scanned")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v:,}")
    print(f"  external manifest: {len(manifest):,} distinct URLs "
          f"-> {out.name}")
    uniq = sorted(set(findings), key=lambda x: (x[0], str(x[1])))
    if not uniq:
        print("CLEAN — every identity-bearing link lands on its identity.")
    else:
        print(f"{len(uniq)} findings:")
        for layer, rel, ev in uniq[:80]:
            print(f"  [{layer}] {rel}  ::  {ev}")
        if len(uniq) > 80:
            print(f"  … {len(uniq) - 80} more")
    sys.exit(1 if uniq else 0)


if __name__ == "__main__":
    main()
