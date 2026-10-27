# Cambridge 2026 Validate, piece 1: planted errors

4 October 2026, Opus 5.5 lead. Plan: `docs/cambridge-validate-2026-plan.md`, piece 1. Progress: `docs/cambridge-validate-2026-progress.md`.

## Result

**31 errors planted. The Audit's checks, as the census ran them, caught 26. Five were missed, one of them gross: a held document released to the public.** Two new total-coverage checks now catch three of the five. The other two are answered in a sentence.

| | Plants |
|---|---|
| Caught by the census re-grade (a blind reading graded against the page) | 24 |
| Caught by a gate the census already ran, and not by the re-grade | 2 (both lying titles) |
| Missed by every check | 5 |
| Of the misses, caught by the new checks T and H | 3 |

The census re-grade raised 27 misses on 391 rows. Every one traces to a plant. It raised none on the roughly 365 rows it re-graded that no plant touched.

## Method
- **Where:** a second worktree, `validate2026-planted`, with its own byte copy of the database and its own clone of the vault's note trees (`~/Projects/cambridge-plant-validate-2026/vault`). Unplanted, it rebuilds byte for byte as the clean baseline v0, and v0 rebuilds f16 (`builds/diff_*`).
- **Draw:** `plant.py draw`, seed **2610050**, from the 2026 rows each kind can apply to, no two plants on one item (`plants.json`). Five first draws reached no page and were drawn again; they are listed in `plants.json` under `did_not_render` with the reason checked for each.
- **Two plants are in the built page, not the model.** The builder takes an item page's title and its address from one name, so a title that lies about its slug cannot arise from the data. Those two were written into the built page's `<title>` after the build (`plant.py apply-output`).
- **Checks run, exactly as the census ran them** (`../run_gates.sh`; results in `../gates/p2/`, the clean baseline in `../gates/v0/`): the build's own guards; the document sweep; Gate 1 offline (L, A, B, C); Gate 2 counts; every vote against the rules; board inventory, completeness, PII, integrity, absence and semantic-link gates; Gate 1 online over every 2026 city link.
- **The census re-grade:** every census row with any changed page, by the census's own rule (`changed_rows.py`): **391 rows** (369 council-night items, 7 committee pages, 14 document pages). Eleven Opus graders on the census's briefs, grading against the census's own round-1 blind readings, not told what was planted (`grader_lanes.json`, `grades/`).

## The table

"Re-grade" is the census re-grade; the row id is the miss it raised. "T" and "H" are the new checks below.

| # | Kind | Target | Caught by |
|---|---|---|---|
| 1 | Aye and nay swapped | POR 2026-102, 18 May | re-grade (A383) |
| 2 | Aye and nay swapped | POR 2026-99, 18 May | re-grade (A390) |
| 3 | Tally off by one (stored roll) | POR 2026-98, 18 May | **missed.** The page kept the right 5-2 but added "the city's portal reports a different result"; the grader saw it and graded it benign. Now T. |
| 4 | Tally off by one (sheet bracket) | CMA 2026-255, 14 Sept | re-grade (A619); now also T |
| 5 | A name dropped, tally kept | CMA 2026-51, 9 March | re-grade (A150); now also T |
| 6 | A name dropped from the sheet's roll | CMA 2026-218, 3 Aug | re-grade (A540); now also T |
| 7 | Result flipped | POR 2026-142, 3 Aug | re-grade (A574); votes against the rules |
| 8 | Result flipped | CMA 2026-117, 27 April | re-grade (A272); votes against the rules |
| 9 | Wrong date in the month (a roll) | POR 2026-76, 27 April | re-grade (A287) |
| 10 | Wrong date in the month (a sheet action) | RES 2026-94, 8 June | re-grade (A444, A472) |
| 11 | Wrong body (meeting note moved) | Human Services, 8 April | re-grade (C30); Gate 1 online (the city's agenda and minutes name Human Services) |
| 12 | Wrong body (meeting note moved) | Government Operations, 18 March | re-grade (C18); Gate 1 online (the city's agenda names Government Operations) |
| 13 | Vote on the wrong item (a roll) | RES 2026-99, 22 June | re-grade (A520). The build's own guard held the moved roll back, as the clerk's motion names the other item, so the page lost its roll. |
| 14 | Vote on the wrong item (a roll) | COF 2026-73, 1 June | re-grade (A423, A424) |
| 15 | Vote on the wrong item (a sheet row) | APP 2026-63, 14 Sept | re-grade (A602, A605) |
| 16 | Wrong file behind a page | CMA 2026-1 and COF 2026-1, 12 Jan | re-grade (D007) |
| 17 | Wrong file behind a page | COF 2026-3 and CMA 2026-3, 12 Jan | re-grade (D003) |
| 18 | A title that lies about its slug (in the built page) | CMA 2026-83 | Gate 1 A; the semantic-link gate. The re-grade missed it (A237). |
| 19 | A title that lies about its slug (in the built page) | CMA 2026-104 | Gate 1 A; the semantic-link gate. The re-grade missed it. |
| 20 | Mover changed | RES 2026-101, 22 June | re-grade (A519) |
| 21 | Mover changed | POR 2026-94, 18 May | re-grade (A387) |
| 22 | Sponsor changed | RES 2026-125, 14 Sept | re-grade (A660) |
| 23 | Sponsor changed | POR 2026-101, 11 May | re-grade (A345) |
| 24 | Co-sponsor roll deleted | RES 2026-1, 26 Jan | **missed, and nothing false was shown.** The same vote is stored twice; the second copy kept it on the page. The only change was two steps in a different order, graded benign as in the census. |
| 25 | Co-sponsor roll names the wrong member | POR 2026-31, 9 Feb | re-grade (A084) |
| 26 | The sheet's word over the minutes | CMA 2026-170, 22 June | re-grade (A478) |
| 27 | The sheet's word over the minutes (curated note removed) | CMA 2026-93, 1 June | **missed.** The meeting card showed one of the night's four results. The grader noted it and graded it benign. The census counted the same fault a miss (A418, round 2), on the lead's reading. |
| 28 | A committee vote's tally off by one | CMA 2025-288, Ordinance, 10 Feb | **missed.** It shows only in the data explorer's committee-vote table, which no census row and no gate covers. Now T. |
| 29 | A document hold removed | CMA 2026-156's land plan | **missed, gross.** The held plan, which names private abutting owners, was published. No census row covers a page that did not exist before. The PII gate passed. The completeness gate printed one fewer held document but passed. Now H. |
| 30 | A fictional phone number (555-01xx) in a document | CMA 2026-200 | the build's phone mask blanked the number; the re-grade caught the added sentence (D352) |
| 31 | A part-scanned document made to pass the scan check | CMA 2026-137 | re-grade (D025), on the placeholder text. The download stayed unhosted: another condition held it. |

## The misses, answered
- **New assertion T, a tally equals its names** (`audit/gate1_tally_holds.py`): every 2026 roll we store, minutes rolls, the sheet's brackets and the committee votes shown, has a tally equal to the names on each side. Clean baseline: 0 findings over 897 rolls. Planted tree: 5 findings, plants 3, 4, 5, 6 and 28.
- **New assertion H, held stays held** (same script): every document page the build has and the live tree does not must be named by a `release` row. Clean baseline: 0 new pages. Planted tree: 1 finding, plant 29.
- **Plant 27, in a sentence:** a meeting card that shows one of several results that night is caught only by a page-by-page read, and this time only by the lead's review of the grader's note, as in the census.
- **Plant 24, in a sentence:** a dropped duplicate roll leaves nothing false on the page; there is nothing for a check to catch.
- **The two title plants:** the re-grade does not compare the page's `<title>` with its address. Gate 1 A and the semantic-link gate do, at total coverage, and caught both.

## Gate 1 online on the planted tree
Every 2026 city link, 384, one request every 1.2 s, from a fresh state file with the planted tree's own document sweep (`../gates/p2/gate1_online.json`). Against the census's run on f14: the same 39 portal items its search no longer returns, the same 12 IQM2 files changed by the Clerk's attestation, the same city error pages and packet-continuation notes, and **4 new mismatches: the four city documents behind plants 11 and 12, each naming the committee the meeting really belonged to.** One request timed out. The two wrong-file plants (16, 17) were not seen online: each page links its own file, so the link is right and only the page's label is wrong.

## What this does not show
- The plants are one per row and few per kind. A kind caught twice of twice is not a rate.
- Mover and seconder: the site shows no seconder anywhere, so only the mover could be planted.
- The re-grade used the census's own readings. It tests the grading and the gates, not the readers.
