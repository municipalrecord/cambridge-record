"""The source-precedence ruling, as code. See SOURCE-PRECEDENCE.md.

Import this rather than re-deciding which record wins. An audit that reports a
conflict this module resolves is crying wolf.
"""

# Higher index wins. Edit here and everything downstream follows.
ORDER = [
    "engrossed order",      # legally operative for the act, boilerplate tally
    "city portal",
    "final actions sheet",
    "council minutes",
]
RANK = {s: i for i, s in enumerate(ORDER)}
UNKNOWN = -1


def rank(source):
    return RANK.get((source or "").strip().lower(), UNKNOWN)


def wins(a, b):
    """True if source `a` outranks source `b`."""
    return rank(a) > rank(b)


def resolve(rows, source_key="Source"):
    """Pick the authoritative row from rows describing the same vote."""
    if not rows:
        return None
    return max(rows, key=lambda r: rank(
        r.get(source_key) if isinstance(r, dict) else r[source_key]))


def is_reportable(source_a, source_b):
    """True only when the ruling cannot settle a disagreement.

    Same rank, or either source unrecognised. Everything else is settled and
    must not be raised as a finding.
    """
    ra, rb = rank(source_a), rank(source_b)
    return ra == UNKNOWN or rb == UNKNOWN or ra == rb
