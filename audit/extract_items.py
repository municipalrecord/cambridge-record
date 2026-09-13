"""Deterministic extraction of every agenda item into JSONL.

Reads items/*.html and emits one JSON object per item. No network, no LLM --
this is the substrate the corpus audits run on. Fields come straight from the
page markup the site generator already emits (data-cite, .crumbdef, .slot,
.noact, data-sha), so the extract is a faithful view of what we published.
"""
import json, os, re, sys, html
from pathlib import Path

ITEMS = Path(__file__).resolve().parent.parent / "items"
OUT = Path(__file__).resolve().parent / "corpus" / "items.jsonl"

RE_MONO = re.compile(r"<p class='dim kicker'><span class='mono'>([^<]+)</span>")
RE_CRUMB = re.compile(r"<span class='crumbdef' title='[^']*'>(.*?)</span>", re.S)
RE_H1 = re.compile(r"<h1>(.*?)</h1>", re.S)
RE_CITE = re.compile(r'data-cite="(.*?)"', re.S)
RE_SHA = re.compile(r"data-sha='([^']+)'")
RE_SLOTLAB = re.compile(r"<span class='slotlab'>(.*?)</span><div class='slotval'>", re.S)
RE_DIV = re.compile(r"<(/?)div\b[^>]*>")
RE_BOLD = re.compile(r"<b>(.*?)</b>", re.S)
RE_TAG = re.compile(r"<[^>]+>")
RE_ID = re.compile(r"^([A-Z]+)\s+(\d{2}|\d{4})-(\d+)$")
RE_MDATE = re.compile(r"data-mdate='([^']+)'")
RE_DOCLINK = re.compile(r"<a class='([^']*)' href='([^']+)'[^>]*>(.*?)</a>", re.S)
# "..., Cambridge City Council, Jun 8, 2009, Order adopted, 8-1. Via ..."
RE_CITE_PARTS = re.compile(
    r"^(?P<long>.*?)\s+\((?P<id>[^)]+)\),\s+(?P<body>.*?),\s+"
    r"(?P<date>[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})(?P<rest>.*?)\.\s+Via\b", re.S)
MONTHS = {m: i for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def slots(raw):
    """Yield (label, inner_html) for each .slot, matching divs by depth.

    The disposition slot is a timeline: an item can carry several dated
    entries, each its own nested div. A non-greedy regex stops at the first
    nested </div> and silently truncates everything after the first entry,
    which drops later votes entirely.
    """
    for m in RE_SLOTLAB.finditer(raw):
        label = m.group(1)
        start = m.end()
        depth, pos = 1, start
        while depth:
            d = RE_DIV.search(raw, pos)
            if not d:
                yield label, raw[start:]
                break
            depth += -1 if d.group(1) else 1
            pos = d.end()
            if depth == 0:
                yield label, raw[start:d.start()]


def text(s):
    return html.unescape(RE_TAG.sub("", s or "")).strip()


def iso(d):
    m = re.match(r"([A-Z][a-z]{2})\s+(\d{1,2}),\s+(\d{4})", d or "")
    if not m:
        return None
    return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"


def parse(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    rec = {"file": f"items/{path.name}", "url":
           f"https://cambridgerecord.org/items/{path.name}"}

    m = RE_MONO.search(raw)
    rec["item_id"] = text(m.group(1)) if m else None
    if rec["item_id"]:
        im = RE_ID.match(rec["item_id"])
        if im:
            yr = int(im.group(2))
            # AR items use a two-digit year ("AR 16-1")
            if yr < 100:
                yr += 2000
            rec["type"], rec["year"], rec["number"] = (
                im.group(1), yr, int(im.group(3)))

    m = RE_CRUMB.search(raw)
    rec["category"] = text(m.group(1)) if m else None
    m = RE_H1.search(raw)
    rec["title"] = text(m.group(1)) if m else None
    m = RE_SHA.search(raw)
    rec["sha"] = m.group(1) if m else None

    cite = RE_CITE.search(raw)
    rec["cite"] = html.unescape(cite.group(1)) if cite else None
    if rec["cite"]:
        cm = RE_CITE_PARTS.search(rec["cite"])
        if cm:
            rec["date"] = iso(cm.group("date"))
            rec["body"] = cm.group("body").strip()
            # trailing ", Order adopted, 8-1" -> disposition from the citation
            rest = cm.group("rest").strip().lstrip(",").strip()
            rec["cite_disposition"] = rest or None

    # slots: "How it started" / "What happened"
    rec["origin"] = rec["disposition"] = None
    rec["requesters"] = []
    for lab, val in slots(raw):
        lab, body = text(lab).lower(), val
        if "started" in lab:
            rec["origin"] = text(body)
            rec["requesters"] = [text(b) for b in RE_BOLD.findall(body)]
        elif "happened" in lab:
            rec["disposition"] = text(body)

    # Not every item carries a citation button; the meeting date is still
    # recoverable from the city-portal link when it does not.
    rec["has_citation"] = "citebtn" in raw
    if not rec.get("date"):
        m = RE_MDATE.search(raw)
        if m:
            rec["date"] = iso(m.group(1))
            rec["date_from"] = "meeting_link"
    elif rec.get("date"):
        rec["date_from"] = "citation"

    rec["source_links"] = [
        {"kind": k.replace("pdf ", "").strip(), "href": h, "label": text(t)}
        for k, h, t in RE_DOCLINK.findall(raw)
        if "citylink" in k or "pdf" in k]

    rec["no_disposition"] = "class='noact'" in raw
    rec["has_votes"] = "class='allvotes'" in raw and not rec["no_disposition"]
    return rec


def main():
    files = sorted(p for p in ITEMS.glob("*.html")
                   if RE_MONO.search(p.read_text(encoding="utf-8",
                                                 errors="replace")[:4000]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n, bad = 0, 0
    with OUT.open("w", encoding="utf-8") as fh:
        for p in files:
            try:
                rec = parse(p)
            except Exception as e:               # noqa: BLE001
                bad += 1
                print(f"  !! {p.name}: {e}", file=sys.stderr)
                continue
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} items to {OUT} ({bad} failed)")


if __name__ == "__main__":
    main()
