"""Gate extraction output before it reaches the entity graph.

An extraction pass can fail in a way that looks fine: valid JSONL, plausible
records, high row coverage -- and no actual content, because the pass read the
structured `requesters` column and never read the titles. That is exactly how
the first City Manager run failed (7,315 records, 1.0 entities each, every one
the City Manager as "sponsor"), and it would have quietly poisoned the graph.

These checks are cheap and catch it. Run before build_graph.py.
"""
import json, collections, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
CORPUS = ROOT / "corpus"

# Roles that come from the structured `requesters` column rather than from
# reading the title. An extraction consisting only of these is the failure
# mode this module exists to catch.
BOILERPLATE_ROLES = {"sponsor", "requester"}

# Per-shard expectations.
#
# Raw entities-per-item is NOT a usable signal on its own: the verified
# deterministic CMA pass yields 1.14/item because most City Manager items are
# appropriations that name no one, while the failed model pass also sat near
# 1.0. What separates them is whether anything was extracted from the TITLE --
# measured here as the share of items carrying at least one non-boilerplate
# entity. The failed pass scored 0.0%; the verified pass scores 12%.
EXPECT = {
    "cma":     {"min_substantive": 0.05, "kinds": {"person", "gov_body"},
                "roles": {"appointee"}, "target_types": ["CMA"]},
    "landuse": {"min_substantive": 0.40, "kinds": {"address"},
                "roles": {"applicant"}, "target_types": ["APP", "ORD"]},
    "por":     {"min_substantive": 0.30, "kinds": {"gov_body"},
                "roles": {"subject", "target"}, "target_types": ["POR"]},
    "res":     {"min_substantive": 0.50, "kinds": {"person"},
                "roles": {"honoree", "decedent"}, "target_types": ["RES"]},
}


def targets(types):
    p = CORPUS / "items.jsonl"
    if not p.exists():
        return None
    return {json.loads(l)["item_id"] for l in p.open(encoding="utf-8")
            if json.loads(l).get("type") in types}


def check(shard, spec):
    path = CORPUS / f"entities_{shard}.jsonl"
    if not path.exists():
        return None
    rows, bad = [], 0
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    if not rows:
        return [f"{shard}: file exists but holds no parseable records"]

    ents = [e for r in rows for e in (r.get("entities") or [])]
    per = len(ents) / len(rows)
    kinds = collections.Counter(e.get("kind") for e in ents)
    roles = collections.Counter(e.get("role") for e in ents)
    fails = []

    if bad:
        fails.append(f"{shard}: {bad} malformed lines")
    substantive = sum(
        1 for r in rows
        if any((e.get("role") or "") not in BOILERPLATE_ROLES
               for e in (r.get("entities") or [])))
    share = substantive / len(rows)
    if share < spec["min_substantive"]:
        fails.append(
            f"{shard}: only {share:.1%} of items carry a non-boilerplate entity "
            f"(need {spec['min_substantive']:.0%}) -- the pass read the "
            f"requesters column and skipped the titles")
    if len(kinds) < 2:
        fails.append(f"{shard}: only one entity kind present ({list(kinds)}) "
                     f"-- extraction is degenerate")
    if len(roles) < 2:
        fails.append(f"{shard}: only one role present ({list(roles)}) "
                     f"-- extraction is degenerate")
    missing_k = spec["kinds"] - set(kinds)
    if missing_k:
        fails.append(f"{shard}: expected kinds absent: {sorted(missing_k)}")
    missing_r = spec["roles"] - set(roles)
    if missing_r == spec["roles"]:
        fails.append(f"{shard}: none of the expected roles present: "
                     f"{sorted(spec['roles'])}")

    tgt = targets(spec["target_types"])
    if tgt:
        seen = {r.get("item_id") for r in rows}
        cov = len(seen & tgt) / len(tgt)
        if cov < 0.80:
            fails.append(f"{shard}: covers {cov:.1%} of {len(tgt)} target items "
                         f"-- pass did not finish")

    print(f"{shard:9} {len(rows):6} items  {len(ents):7} entities  "
          f"{per:5.2f}/item  substantive={share:5.1%}  "
          f"kinds={len(kinds)} roles={len(roles)}"
          f"{'  OK' if not fails else '  FAIL'}")
    return fails


def main():
    allfails, checked = [], 0
    for shard, spec in EXPECT.items():
        r = check(shard, spec)
        if r is None:
            print(f"{shard:9} (not written yet)")
            continue
        checked += 1
        allfails += r
    print()
    if not checked:
        print("no entity files to validate yet")
        return 0
    if allfails:
        print("VALIDATION FAILED:")
        for f in allfails:
            print(f"  - {f}")
        return 1
    print(f"all {checked} shard(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
