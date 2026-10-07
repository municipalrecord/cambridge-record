# Cambridge 2026: the Stage 4 Audit, 3 and 4 October 2026

# Part 3: the census, 4 October 2026

**Verdict: 2026 passes the Audit.** Dan ruled on 4 October 2026 that 2026 passes only at zero errors, and the sample pool was spent. So every row of the Audit's population was read blind against the live build, every miss was fixed in the builder or the curated files, and every row whose pages changed was graded again, until one build had every row clean. On build **f14, all 1,206 rows are clean: 0 wrong, 0 missing.** Gates 1, 2 and 3 pass on f14. The final build, **f16**, is f14 plus the accuracy page's census section and this file: its treediff against f14 changes only `accuracy.html`, `audit/AUDIT_2026.md`, the build stamps and the six re-cut downloads that keep the same pages and text, so every row stands on f16 as on f14.

- **Branch:** `dispatch/cambridge-audit-2026-census-2026-10-04`, from origin/main `32f0efc`. Plan: `docs/cambridge-audit-2026-census-plan.md`, committed before any reading. Progress: `docs/cambridge-audit-2026-census-progress.md`. Everything below is in `Data/Audits/year_2026/audit/census/`.
- **Database:** a byte copy of the fix worktree's `Data/cambridge.db` (sha256 `e3c2bbcc2714ae91b5cfaf6d4123c6539f818949e164e5aac77399adb82a6c3f`), git-ignored. The scratch file was never written. Every change to what the site shows is a script or a curated row on the branch.
- **Control:** the live tree, deploy `1c5efbc355` (build f10 plus the search index). Builds use `--no-index`; the search index is added with `python3 -m pagefind --site site/out --output-subdir pagefind` before the gates, as the ship does.
- **Nothing was deployed, pushed or merged.**

## The population
The Audit's unit, as the first Audit defined it, counted on the live tree (`census/rows.json`, `census/make_census.py`).

| Stratum | A row is | Rows |
|---|---|---|
| A | an item on a 2026 council night (every item link on the 23 meeting pages) | 663 |
| C | a 2026 council-committee meeting page (12 committees, the Roundtable, the Social Housing Task Force) | 44 |
| D | a 2026 document page that prints a meeting (the f10 sweep, Build's 43 and the 20 withheld pages included) | 499 |
| **All** | | **1,206** |

A is three more than the first Audit's 660 (PET 2026-3, and POR 2025-172 and -173 on the 12 January Calendar). Out of scope, as before: School Committee; boards that are not council committees; the committee votes kept off pages by design.

## Method
- **Readers:** Sonnet, blind (the city's documents and a locator only; `census/READER_*.md`, `census/tasks_*.json`). 65 lanes of about 25 rows; a night kept together. **Double reads:** a seeded 10%, **seed 2610048**, 121 rows read again by a different reader.
- **Graders:** Opus (`census/GRADER_*.md`), 29 lanes. Each grader saw every blind reading of its rows (`census/row.py`): this round's, the double read where drawn, and the seven samples' earlier readings of the same row (A 655, C 43, D 207). Where readings disagreed the grader read the source.
- **The lead** read every miss against the source and our page, raised misses from clean grades where a second Opus reading or consistency required it, and overruled four to benign with the evidence written down (`census/r1/lead_notes.md`, `r1/misses.json`, `r2/lead_notes.md`).
- **Re-reads** followed fix twenty's proof by changed pages, on the Audit's unit: each build was diffed against the tree each row was graded on (`audit/fix/treediff.py`); a row with any changed page (its item page and meeting page; its board page; its document page, download and the item pages linking it) was graded whole again by a fresh Opus grader against the blind readings; every other row was carried. Six re-cut downloads that keep the same pages and text in every build are noise (`r2/noise.json`).
- **The ledger** (`census/ledger.json`, `ledger.py`) proves the stop rule row by row: each row's last grade is clean and every one of its pages is byte-identical between the tree it was graded on and f14. It was computed with the f12 and f13 trees present (scratchpad clones, removed afterwards to free space; each build's diffs stay in `census/builds/`).

## The rounds
| Round | Tree | Rows graded | Carried | Wrong | Missing | Fixed in |
|---|---|---|---|---|---|---|
| r1 | live (f10) | 1,206 | 0 | 23 | 6 | f12 |
| r2 | f12 | 349 | 857 | 0 | 1 | f13 |
| r3 | f13 | 47 (1 June) | 1,159 | 0 | 0 | |
| r4 | f14 (Dan's two rulings) | 4 | 1,202 | 0 | 0 | |

f11 was built and rejected before any reading: it released 10 documents the live site holds (see below) and unmasked one phone number written with a leading 1.

### Round 1: 29 misses (23 wrong, 6 missing)
- **Downloads of scanned pages (7):** D025, D129, D313, D425, D433, D450, D452. The extraction flags a file as a scan only when it is wholly one, so slices with scanned attachments were offered whole. D452 (APP 2026-63's sign permit) carried the applicant's own email and phone on a scan page. Fixed: `_has_scanned_page` in `_orig_btn`; a download is hosted only when no page is an image without text, unless a person released the document.
- **Public commenters' home streets (9 pages):** D157, D254, D261, D266, D289, D301, D302, D309, and D157's same minutes. The masker read only "street, Cambridge, MA". Fixed: `_COMMENTER` also stops at the verb; `_COMMENTER_NO` masks a numbered home address before any town or the verb (ordinal streets, streets with no suffix, other towns); City Hall and the city's buildings stay.
- **The packet-tail note (3):** D362 named another item's pages; D421 and D430 started a page late. Fixed in `packet_tail_note`: the range starts after the text's own cut, and no note is written when the pages after the cut carry another item's code.
- **The phone mask (1):** D101's table of counts read as phones. Fixed: bare digits never inside a longer number or across a line break (`redact.PHONE`); the leading-1 form kept.
- **A wrong meeting (1):** D166, a hearing schedule filed under 30 March by a date it mentions in passing. Fixed: only an "In City Council" stamp names the meeting.
- **Council-night items (8):** A216 (a filing voice vote under the clerk's misprinted CMA 2026-24) and A163 (the misprinted CMA 2026-252) by a cited `minutes_text_recode` row and the builder reading the night's text with the slip corrected; A380 (a joint motion's "adopt" given to the communication) by `_own_clauses`; A348 (the sheet's "and placed on file" on a policy order) by `minutes_close_act`; A053 (one roll shown as two) by `one_roll_closes`; A150 (a transcript-only filing voice vote) by a cited `voice_step` row; A010 and A144 (a second act or the hearing missing from a card) by cited `card_note` rows.
- **A committee page (1):** C42, two agenda communications folded into the opening text. Fixed: `split_folded_items`.
- **Overruled to benign (4):** A076 (the city's own 9 February agenda lists the item); D106, D184, D241 (scans a person released by hand; their downloads are by design). A272 was raised and then returned to benign in round 2 (adopt and approve name one act).

### Round 2: 1 miss
A418: the 1 June budget card showed one of four results. Fixed by a cited `card_note` (the General Fund as amended 8-0-1, the Water Fund 9-0, the communication placed on file). A303 was flagged and ruled benign: the same wording and sheet word as CMA 2026-52 to -58, graded correct since fix round 6.

### Rounds 3 and 4: none
Round 3 re-graded the 47 rows of 1 June on f13. Round 4 graded the four rows Dan's rulings changed on f14.

## Dan's rulings, 4 October 2026
1. **The Rise Up Cambridge report** (CMA 2026-28, 108 pages): publish in full. It was held on false matches; it has no resident's address, phone or email; it thanks researchers by name and tells six participants' stories by first name. Released in `document_holds.csv`.
2. **The police log of contacts with immigration agents** (CMA 2026-246): keep the memo and the log; black out the private person named as the subject of an inquiry and a couple's home street. Three cited `redact` rows and a new `name` marker. The name and the street appear in 0 files on f14.

## Kept held, not released
The narrower phone pattern and the wider commenter mask would have released 10 documents the live site holds: 8 from before 2026 and two sets of minutes (CC 2026-5, the council minutes of 30 June 2025; CC 2026-95, D491). The census does not release a document on a pattern it has not proved complete. They stay held exactly as live (`Data/Curated/census_kept_held.csv`, checked wherever the resident test runs) until a person reads them.

## The final count on f14
**1,206 rows: 773 exact, 433 benign, 0 wrong, 0 missing.** Benign kinds, each listed once with its count:

| Kind | Rows |
|---|---|
| The clerk names a mover; the page has no mover line for that step | 333 |
| A city office's or organisation's contact detail blanked (over-redaction) | 27 |
| A committee vote kept off the committee page by design | 20 |
| A voice vote on the council's own business not listed | 11 |
| Steps listed out of order | 6 |
| Scanned pages shown blank with no note | 6 |
| A cut clerk's stamp or title fragment on a card or heading | 5 |
| A typing slip in a heading (mostly the city's own) | 3 |
| Joint meeting filed under one committee; a released scan's download; a held page with no city link (3 each) | 9 |
| Ten more kinds of one or two rows each (`census/ledger.json` with the grade files) | 13 |

## Gates on f14
- **Gate 1 offline:** 0 findings over 1,172 pages (`census/gates/f14/gate1_offline.log`). Every vote against the rules: 0 `no-rule`. 497 of 497 document pages name a real meeting their item was on. Integrity: 0 broken internal links over 54,140 pages.
- **Gate 1 online, every city link on the 2026 pages (384, not a sample; one request every 1.2 s; `census/gate1_online_census.py`, results `census/gates/gate1_online.json`):** **no link opened the wrong record.** 323 confirmed (138 portal items, 103 compiled documents, 51 meetings, 21 IQM2 items, 10 IQM2 files hash-exact). Exceptions, each read: 40 portal items the portal's own search no longer returns by title (22 seen so in earlier audits; the database ties each to its page's code; not proof either way); 5 compiled documents that return the city's error page, not a PDF (city-side); 4 compiled documents the gate holds no claim for, each a "packet continues" note opening the very packet its slice came from (the 16 June and 7 July Ordinance Committee packets, the 6 August Roundtable, the 28 September council packet); 12 IQM2 files whose bytes changed, every one by the Clerk's 12 January adoption attestation ("Order Adopted by a yea and nay vote ... A true copy; ATTEST"), one also with its appointees' names re-flowed (9 fetched again and diffed by the lead). City-amended, benign.
- **Gate 2:** 0 wrong counts (497 document page counts; the check now compares a page with no download against the item's own pages, as the text is cut).
- **Gate 3:** the accuracy page's 2026 section leads with the census (rows read, 30 mistakes found and fixed, zero wrong or missing now, the benign kinds and counts, dated 4 October 2026); the sample history stays beneath it. The rulebook's "How we check a vote" is unchanged.

## What is not checked
School Committee; boards that are not council committees; committee votes kept off pages by design; mover and seconder as a total check; documents of years before 2026 that quote the same public commenters (a 22 June commenter's street is on 18 archive pages of 2009 to 2014); the 10 documents kept held until read.

## For Dan
- **Land and ship** are yours. The live site still shows every fault fixed here, the commenter streets and the scan download with an applicant's phone among them, until the ship.
- **Ten held documents** to read when there is time (`census_kept_held.csv`): some are likely held on false phone matches.

---

# Part 1: the samples, 3 and 4 October 2026 (unchanged)

**Verdict: 2026 does not pass the Audit.** Gates 1, 2 and 3 pass on the fix builds. The sample bar does not. Seven fresh samples have been drawn. Not one met the bar, which was set before the first draw: at most 2 misses in 130, and none with a wrong outcome, tally, name on a side or record identity. The last sample, graded on build f7, found **3 of 130 (2.3%, 95% interval 0.5% to 6.6%)**. The item pool is now spent: only 4 item-nights remain that no sample has drawn, so a further fresh sample of this size cannot be drawn without reusing rows.

- **Branch:** `dispatch/cambridge-audit-2026-fix-2026-10-03`, cut from the first Audit's `abea674`. Plan: `docs/cambridge-audit-2026-fix-plan.md`; each addendum was written before its draw. Progress and handoff: `docs/cambridge-audit-2026-fix-progress.md`.
- **Database (ruling 4):** a byte copy of `~/Projects/cambridge-plant-scratch-fix12/cambridge.db`, the file the live site was built from. sha256 at copy `156b3f481863d8b058a56438913bd22d8cffeaed5d67a1dd598ec8fae05f89ec`. It is git-ignored (1.02 GB), so it is not committed. Every change made to the copy is a script on the branch: the rules rows (`build_bodies_rules.py`), the vote checks (`vote_rules.py --write`), and 4 sponsor fields (`re/fix_stamp_sponsors.py`). The scratch file was never written.
- **Nothing was deployed, pushed or merged.** The live site still shows every fault listed here as fixed.

## The samples

Every sample: Sonnet blind readers saw only the city's documents and a locator; Opus graders compared each reading with the build under audit; the lead read every miss against the source. No row was drawn twice. Intervals are Clopper-Pearson.

| # | Seed | Build graded | Rows (A / C / D) | Misses | Rate (95% interval) | The misses |
|---|---|---|---|---|---|---|
| 1 | 2610033 | live (first Audit) | 80 / 20 / 30 | 6 | 4.6% (1.7 to 9.8) | A34, A60, C16, D20, D21, D25 (Part 2) |
| 2 | 2610041 | f2 | 80 / 20 / 30 | 3 | 2.3% (0.5 to 6.6) | A18 sponsor, C7 identity, D30 slice |
| 3 | 2610043 | f3 | 96 / 4 / 30 | 2 | 1.5% (0.2 to 5.4) | C1 reschedule notice, D27 slice |
| 4 | 2610044 | f4 | 100 / 0 / 30 | 5 | 3.8% (1.3 to 8.7) | A18 card count, A37 label, D6 and D14 privacy, D29 withheld |
| 5 | 2610045 | f5 | 100 / 0 / 30 | 2 | 1.5% (0.2 to 5.4) | A84 outcome tag, D18 another item's page |
| 6 | 2610046 | f6 | 100 / 0 / 30 | 3 | 2.3% (0.5 to 6.6) | A24, A85 sheet word over minutes, D30 privacy |
| 7 | 2610047 | f7 | 100 / 0 / 30 | 3 | 2.3% (0.5 to 6.6) | A48 absent member, D24 privacy, D28 slice |

- **Across samples 2 to 7:** 18 misses in 780 rows, 2.3% (1.4% to 3.6%). The rate has not fallen below about 2%, because each sample finds a new, rare kind of fault, each fixed in the next build.
- **Said plainly:** sampling again after each fix is a run of tests, so no single later sample carries a first sample's weight. The third and fifth met the count (2 of 130), but the fifth's two misses were of the barred kinds, and the third passes only on the lead's reading of C1 (below). Neither is offered as a pass.
- **Every miss, its source page and ours:** `audit/re*/result_*.json` (`read_by_lead`) and each sample's `sample/grades/`.

## Gate 1, integrity and identity: passes on the fix builds
- **Offline, every 2026 page:** 0 findings on f2, f3, f4, f5, f6 and f7 (`audit/re/f*/gate1_offline.log`). The first Audit's live finding (COF 2026-15's link to a cancelled meeting) stays fixed.
- **Votes against the rules (ruling 1):** 1,061 votes. No-rule 31 to 0; recompute-match 668 to 698; ambiguous-threshold 1 (ORD 2025-17, the Cambridge Street districts: silent on Housing Choice and of that kind; passes under R-20 and R-20b alike, 6-3); recompute-differs 3, each now flagged on its page; printed result not located 73 (as before); no-count 286. The four 2026 ordinations pass under either zoning rule: ORD 2025 #17 6-3 on 26 January, ORD 2026 #1 8-1, ORD 2026 #5 and #6 9-0. No 2026 outcome changes under the new rows.
- **Online, seeded city links:** seed 2610041 on f2 (142 links) and seed 2610044 on f4. No link opened the wrong record. Exceptions, of the first Audit's kinds: portal items the portal's own search no longer confirms (12 on f2, 13 on f4; the database ties each to its page's code; not proof either way); city error pages (3, 2); IQM2 files whose bytes changed (2, 12): every one differs by the Clerk's later adoption attestation ("In City Council January 12, 2026. Order Adopted by a yea and nay vote ... Attest"), one of them also with its appointees' names re-flowed. Read and benign.
- **Document sweep:** every 2026 document page names a real meeting its item was on (500 of 500 on f2 to f6; 499 of 499 on f7 after one more hold).

## Gate 2, derived numbers: passes on the fix builds
0 wrong counts on f2 to f7 (`audit/re/f*/gate2_counts.log`). Nothing ranks, rates or scores anyone on a 2026 page.

## Gate 3, policy: passes on the fix builds (ruling 3)
- **Rulebook:** "How we check a vote" and "The Clerk's result always wins", as written, under the mechanics section (`rulebook.html#checking-votes`).
- **Accuracy page:** a new top section, "2026, read against the Clerk's record", with the first sample (6 of 130) and the latest (3 of 130), both dated, every miss of the first listed with the city's page and ours, the seeds, and this file linked.
- **The flag (ruling 2):** "Count does not match" and one sentence, driven by `vote_checks` (`recompute-differs`), on POR 2026-76 (27 April; the Clerk's "Motion passed" restored, "Minutes, page 19" linked) and AR 2026-22 and AR 2026-35 (3 August; the sheet's 0 to 0, minutes not published). No em dashes in any of it.

## The rulings applied (3 October 2026)
1. **Rules rows** R-19 (loan orders, 2/3 FULL, yeas and nays), R-20 (zoning, 2/3 FULL), R-20b (Housing Choice zoning, simple majority, UNSPEC, from 14 January 2021), R-21 (a committee's motion, majority of votes cast, PRESENT, common law). In `survey.md` and the evidence folder (record-onboarding `a9641469`, sources hashed, Needham's bytes) and in the town-onboarding `rules-layer.md`. Two points kept as ruled and noted, not resolved: the statute's Housing Choice text reads "a simple majority of all members"; Needham dates the split 14 April 2021.
2. **The flag**, as above.
3. **The Gate 3 text**, as above.
4. **The database**, as above.

## The fix rounds (each diffed against the live tree and every changed page read)
| Round | Build | Fixed | Pages changed (beyond build noise) |
|---|---|---|---|
| 1 | f1, f2 | the flag; A34 (agenda positions count as named; 8 pages lose a false "minutes do not record" line); A60 (a two-count sheet row follows the minutes' one roll); C16 (agenda items numbered under "Roll call"); Gate 3 text | 18 |
| 2 | f3 | C7 (Social Housing Task Force no longer filed as the Housing Committee); A18 (a charter-right holder no longer read as a sponsor: 4 rows, census-read); D30 (a slice cut at a second cover now says the packet continues and links it); 12 public commenters' home streets blacked out (Dan's CC 2026-47 precedent) | 50 |
| 3 | f4 | C1 (a "rescheduled" or "cancelled" notice kept: 2 notes); D27 (a slice keeps its own vote certification: 2 slices) | 8 |
| 4 | f5 | D6, D14 (no hosted download of a scanned, withheld or blacked-out document: 11 downloads withdrawn, the city's link kept); A37 (an item named by subject counts as named: 3 pages); A18 (a card says "voice vote, N present" where the minutes say so) | 15 |
| 5 | f6 | A84 ("ELIGIBLE TO BE ..." kept whole as a stamp); D18 (a slice ends at another item's uncoded letter: 2 slices) | 6 |
| 6 | f7 | A24, A85 (the minutes' second reading, or approve and file, is the card's act, the sheet's word labelled: 8 cards); D30 (an OCR'd scan treated as a scan; the Lincoln land plan held) | 12 |
| 7 | f8 | A48 (an absent member the sheet names is named under a voice vote); D24 (a commenter's street before ", Cambridge, MA" after "public comment" blacked out in any shape, and such a document not hosted); D28 (a certification title cut at its charter-right stamp: 4 slices regain their own certification and cover) | read on f8 |

- **Vault notes** (shared, not on the branch; before and after copies in `audit/fix/vault_notes/`): 2 February Roundtable, 24 June Social Housing Task Force (the old Housing Committee note set aside), 18 March Government Operations, 15 April Health and Environment.
- **Side effect, for Dan:** document page addresses depend on order, so every hold renames later document pages (as the first Audit noted). Old links to those pages will open a neighbour after the next ship.

## The lead's calls, written down
- **C1 (third sample)** classed a wrong fact, not a wrong identity: the page is the city's own 18 March agenda; it lost the notice that the meeting moved.
- **A4 (second sample)** overruled to benign: the city's 9 February portal agenda (CompiledDocument 7607, p.7) lists the Public Weighers item as Awaiting Report item 4, as our page does.
- **D29 (fourth sample)** kept held: the grader found a business's contacts only, and one contractor street it could not confirm as a home.
- **The Lincoln land plan (CMA 2026-156)** held: private abutting owners named on a recorded plan.
- **The slicer's refusal at a second cover** kept: it never files an unnumbered page under a guess. The page now says the packet continues.

## What is not checked
School Committee; boards that are not council committees; 109 of 111 2026 committee votes (off pages by design); 73 printed outcomes the script cannot locate; 42 hosted originals with no archived hash; mover and seconder as a total check; documents of years before 2026 that quote the same public commenters (not swept).

## Open decisions for the editor
How to judge 2026 now that the sample pool is spent; publishing these fixes; four held documents (D29's sign application, the Lincoln land plan, the Rise Up Cambridge report, the presentation pages after a second cover sheet); and the two open notes on R-20b.

---

# Part 2: the first Audit, 3 October 2026 (unchanged)


**Verdict: 2026 does not pass the Audit.** Gate 1 fails. Gate 2 passes once the fix round's build is used. Gate 3 fails. The fresh sample's miss rate is **6 of 130 (4.6%, 95% interval 1.7% to 9.8%)**, above the bar set before the draw (at most 2).

- **Audited:** the live tree (`site/deploys/cambridge-record`, deploy 98507d644, code at main `1f1fbc3`), against a private copy of the production database.
- **Branch:** `dispatch/cambridge-audit-2026-10-03`. Plan: `docs/cambridge-audit-2026-plan.md`, written before any draw. Everything below is in `Data/Audits/year_2026/audit/`.
- **Seed:** 2610033, new to Cambridge. Draw: `draw_sample.py`. Sample: `sample/sample.json`.
- **Nothing was deployed or pushed.** Fixes are on the branch only.

## Gate 1, integrity and identity: FAIL

### Offline, every 2026 page (`gate1_offline.py`): one finding on live, none after the fix
- **Scope:** 1,178 pages (23 council meetings, 609 item pages, 44 council-committee meetings, 502 document pages).
- **Internal links:** 28,069 checked, all resolve. The site-wide gate also finds 0 broken across 54,143 pages.
- **Identity:** every item, meeting and committee page's title carries the code or date its address encodes. Every "b" page says another item has its number. All 502 document pages name a real meeting of the right kind that their item was on (doc sweep).
- **Anchor claims:** 1,944 links whose text names a code; all land on that code's page.
- **City links against the database:** 393 PrimeGov item links, 449 PrimeGov meeting links, 21 IQM2 item links, 35 IQM2 file links, 489 hosted originals (288 hash-exact, 159 packet slices we cut, 42 with no archived hash).
- **Finding G1-1 (fixed):** COF 2026-15's link, labelled "The city's agenda for this meeting: Mar 4, 2026", opened the cancelled 23 February roundtable. Confirmed live: the city's page says "THIS MEETING HAS BEEN CANCELLED". Cause, read in the code: the builder took the first template it found for a code, cancelled meetings included.

### The downloads (found by Gate 2's counts and the document graders): FAIL on live, fixed
- **Finding G1-2 (fixed):** 11 of 156 packet-slice "Download original PDF" files held more pages than the item's own. The page text was cut at the item's end; the download was not.
  - Ten carried other items' vote certifications or pages: CMA 2026-161, -164; POR 2026-110, -118 (119 pages for 4), -139 (37 for 2), -171 (28 for 3); RES 2026-89, -90, -94; COF 2026-103.
  - **APP 2026-63's download was 212 pages for 32.** The extra pages are the packet's residents' communications section: 21 non-government email addresses.
  - Cause, read in the code: `readers.py` trims the slice's text, but `_orig_btn` in `build_site.py` copied the untrimmed file.
- **Finding G1-3 (fixed):** 8 pre-2026 item pages offered 31 PrimeGov files that belong to 2026 items. CMA 2022-205 offered 24 January 2026 appointment orders of CMA 2026-11. Cause, read in the code: one query joined attachments to items by number alone; PrimeGov item 17187 is CMA 2026-11 and IQM2 item 17187 is CMA 2022-205.
- **Side effect, listed:** the Joint Housing and Finance minutes of 3 December 2025 (attachment of CC 2026-1) were offered only on POR 2022-275 by that bug. After the fix no page offers them; CC 2026-1's own page never did. Unexplained why.

### Votes against the rules (`vote_rules.py`, every 2026 vote): FAIL
1,061 votes: 327 minutes roll calls, 19 portal votes, 713 Final Actions results, 2 committee votes shown on pages.

| Verdict | Count |
|---|---|
| recompute-match | 668 |
| no-count (voice votes, "[VV9]", "[UNANIMOUS]", charter rights) | 286 |
| printed result not located by the script | 73 |
| **no-rule** | **31** |
| **recompute-differs** | **3** |

- **V1, no-rule (31).** The rules table has no row for three kinds of 2026 vote.
  - 24 votes adopt loan orders. General Laws c. 44 sections 1 and 2 need two-thirds of all members.
  - 5 votes ordain zoning ordinances. Chapter 40A section 5 needs two-thirds of all members.
  - 2 committee votes (Ordinance Committee, 10 February). Rule R-14 sets a quorum, not a threshold.
  - None would change outcome: every one has 6 or more yes votes, or fails under either rule.
- **V2, recompute-differs, not flagged (1).** POR 2026-76, 27 April 2026. The minutes (p.19) print "Yes - 4, No - 5. Motion passed." on the Mayor's motion for reconsideration. Under the charter (section 2-6) four of nine fails. **Our pages say "The motion to reconsider failed 4–5."** That silently replaces the clerk's printed result, which the rules forbid. Read by the lead in the minutes.
- **V3, recompute-differs, not flagged (2).** AR 2026-22 and AR 2026-35, 3 August 2026. The Final Actions sheet (pp.27-28) prints "Report Accepted and Placed on File [0 TO 0]", "YEAS: None". The meeting page shows "Report accepted and placed on file" with no count and no flag. The minutes for that night are not published, so what happened in the room is unexplained.
- **Not located (73).** In 63 of these the yes count is 7 or more, or 1 or fewer, so no rule in the table could change the outcome. The close ones were read by hand: 3 match, 1 is V2 above. The rest are listed in `vote_rules.csv`.
- **Read by the graders, not counted here:** on 26 January the clerk said "nine in the affirmative and two in the negative" on a suspension where seven voted yes. The site shows 7-2 with the right names.

### Online, a seeded sample of city links (`gate1_online.py`): passes, with listed exceptions
- **Population:** 381 distinct city links on 2026 pages. 63 drawn on seed 2610033, plus every city link on a sampled page: 150 checked, one request at a time, 1.2 seconds apart.
- **Results:**
  - PrimeGov meetings: 24 of 24 show the claimed date.
  - Committee agendas and minutes: 56 of 59 show the committee and date. 3 committee "packet" links (Finance 9 and 30 April, Ordinance 16 June) send the city's server to its "PublishedDocumentError" page. That is city-side, and listed.
  - IQM2 items: 7 of 7.
  - IQM2 files: 5 of 6 hash-exact. CMA 2026-3's order changed on the city's server on 28 August 2026: the Clerk added the attestation "Order Adopted by a yea and nay vote: Yeas 9; Nays 0". City-amended, benign.
  - PrimeGov items: 43 confirmed by the portal's own search. **11 unconfirmed:** the search no longer returns those older meeting-item numbers by title or by code. The database ties each to the page's code. This is not proof either way.
- **No link opened the wrong record.** The only wrong one found anywhere is G1-1, which the offline check found.

## The fresh sample (the chain): 6 misses in 130

**Unit:** a record as a reader meets it on our page, followed out to the city's own document. Build read every 2026 night end to end, so no vote is unread by Build. The Audit therefore draws from the database and the pages, never from Build's reading files, and carries no Build grade. 43 Build-checked document pages were left out of the document pool.

**Method:** Sonnet blind readers saw only the city's documents and a locator (`READER_*.md`). Opus graders compared each reading with the live pages (`GRADER_*.md`). The lead read every miss against the source.

| Stratum | Pool | n | exact | benign | wrong | missing | miss rate (95% interval) |
|---|---|---|---|---|---|---|---|
| A, item on a night | 660 | 80 | 69 | 9 | 2 | 0 | 2.5% (0.3% to 8.7%) |
| C, committee meeting | 44 | 20 | 8 | 11 | 0 | 1 | 5.0% (0.1% to 24.9%) |
| D, document page | 461 | 30 | 27 | 0 | 3 | 0 | 10.0% (2.1% to 26.5%) |
| **All** | | **130** | **104** | **20** | **5** | **1** | **4.6% (1.7% to 9.8%)** |

Intervals are Clopper-Pearson. **Bar, set before the draw: at most 2 misses, and none with a wrong outcome, tally, name or record identity.** Not met: 6 misses, one of them a wrong identity (D21). No sampled row had a wrong outcome, tally or name.

### Every miss
1. **A34, RES 2026-82, 18 May.** The page says "The council's minutes of that night do not record this item; the result is the city's portal's." That is false. The minutes (p.21) adopt "Resolutions #1-2, and 4-7" on a voice vote of nine, and the sheet confirms #2 is RES 2026-82. The outcome shown is right. **The same false line is on RES 2026-81 and RES 2026-85 to -88.** Cause unexplained: the minutes number the resolutions by agenda position and nothing matched them. Not fixed.
2. **A60, CMA 2026-152, 18 May.** The minutes (p.8) record one motion "to approve and place on file", 9-0 by roll call. The meeting card says "Approved, 9–0–0; placed on file (voice vote, 9 present)": the sheet's version, with no label. The item page follows the minutes. Not fixed.
3. **C16, Roundtable/Working Meeting, 2 February.** The agenda numbers two survey presentations. The page shows only the purpose line. Not fixed.
4. **D20, ORD 2026-8, the residents' zoning petition (3 August).** The document page showed the petitioner's home address and personal email, and the signature sheet's names and home addresses. The 14-page download did too. **Fixed:** held (`Data/Curated/document_holds.csv`).
5. **D21, CMA 2026-11's appointment orders.** The document page is right, but the 2022 item CMA 2022-205 offered this order and 23 more for download. **Fixed:** G1-3.
6. **D25, APP 2026-61, curb cut (14 September).** The page showed no text (a scan), but the item page offered the 40-page download, whose third page carries the applicant's personal phone and email. **Fixed:** held under fix eighteen's A.8 rule.

### Benign, listed
- Committee votes in the minutes that the site keeps off committee pages by design (C1, 3, 5, 6, 8, 12, 13, 14, 15).
- Two joint meetings filed under one committee (C14, C20); the text says joint.
- Steps out of order on POR 2026-99 and POR 2026-94.
- Voice votes of the body not shown; a lower-case month; one garbled title.

## Gate 2, derived numbers: PASS on the fix build (11 wrong on live)
2026 pages compute counts only. Nothing ranks, rates or scores anyone, and no rate appears on any 2026 page.

| Number | What it counts | Frame, floor | Stated limit at point of use | Check (`gate2_counts.py`) |
|---|---|---|---|---|
| Section counts on a meeting page, "Policy Orders (17)" | the cards in that section | not a rate: none needed | none needed | 171 of 171 |
| "97 agenda items" in a meeting's summary | the cards on the page | not a rate | none needed | 23 of 23 |
| "Voted yes (4)", "Absent (2)" | the names under it | not a rate | the roll's source is named ("from the council's minutes") | 251 of 251 |
| Tallies beside rolls, "4–5" | yes and no names in the roll | not a rate | the same | 76 of 76 |
| "(voice vote, 9 present)" and the names under it | members the clerk records present, or who cast recorded votes that night | not a rate | yes: "A voice vote records the outcome, not individual positions… Showing the members who cast recorded votes at this meeting" | read, not machine-counted |
| "Agenda Items (3)" on a committee page | the items listed | not a rate | none needed | 44 of 44 |
| "N pages" on a document page | the pages of the download | not a rate | none needed | **live 491 of 502; fix build 500 of 500** (the 11 are G1-2) |

- A count copied from the clerk ("[8-0-1]", "voice vote of nine members") is a quotation, not a statistic.
- **Outside 2026's scope:** the councillor league table, career pages and pair pages cover every year from 1942. The brief places them outside this audit. They are not new, and the CLAUDE.md hold on new statistics is kept. Their denominators are a whole-corpus question for a later Audit.

## Gate 3, policy: FAIL
| Requirement | Where | State |
|---|---|---|
| Unofficial, not affiliated, from named primary sources | every footer; `sources.html` | met |
| Corrections policy: spelling corrected and listed; name, date, tally, outcome never | `corrections.html` | met |
| The minutes win over the portal | `corrections.html` | met |
| Which vote rules were applied, from where; a printed outcome always wins | nowhere | **missing.** The rulebook quotes the charter and rules, but says nothing of checking votes against them. V2 shows the site does not yet follow the second half. |
| Accuracy page with the real miss rate | `accuracy.html` | **stale.** It reports a July 2026 link and title audit and a votes audit of crawled IQM2 items. It has no 2026 rate, and it printed the build date as "Audited 2026-10-03" (fixed on the branch). |

Draft text for both missing statements: `docs/cambridge-audit-2026-policy-draft.md`. Not on any page.

## The fix round (one round)
Build `a2` (`--no-pull --no-index --hold-who=<live tree>`, same school votes folder as the ship build) against the live tree. 49 files changed, 7 removed. Each one was read (`changed_pages_a2.json`):

| Fix | Before (live) | After (a2) |
|---|---|---|
| Downloads cut to the item's own pages (`_orig_btn`) | 11 slice downloads longer than the item; APP 2026-63 with 21 non-government emails | 0; APP 2026-63 is 32 pages, no non-government email |
| Meeting link skips cancelled meetings and follows the label's date | 1 wrong (COF 2026-15) | 0; it opens template 10185, 4 March 2026 |
| Attachments joined by portal as well as number | 8 pre-2026 pages, 31 links to 2026 files | 0 |
| Two holds (ORD 2026-8 petition, APP 2026-61) | both published | both held; their pages and downloads gone |
| Accuracy page date | "Audited 2026-10-03" (the build date) | "Results written 2026-09-11" (the results file's date) |

- **Gate checks on a2:** Gate 1 offline 0 findings. Gate 2 counts 0 wrong. PII gate clean. Integrity gate: 2 broken links, both to the search index the build skipped on purpose.
- **Side effect, for Dan:** holding APP 2026-61 renamed 17 later packet document pages. Every one is byte-identical to a live page apart from its own address. Document addresses depend on order, so any hold can repoint an old link to a different document.
- **No fresh draw owed:** no vote, item or date row changed. The changes are build code, two curated holds and one page date.

## What is not checked
- School Committee: outside scope.
- Board pages of bodies that are not council committees.
- 109 of 111 2026 committee votes are kept off pages by design; only the 2 shown were checked.
- 73 printed outcomes the script could not locate.
- The 42 hosted originals with no archived hash (no-baseline).
- Mover and seconder were checked where readers and pages both named them, not as a total check.

## For Dan
1. **Privacy, live now.** The live site still serves APP 2026-63's 212-page download with residents' emails, and the ORD 2026-8 petition with home addresses. The fixes are on the branch, not deployed. Landing and shipping are your word.
2. **Rules rows** for loan orders, zoning ordinances and committee votes (V1). This is a survey change in record-onboarding with a reading of the law.
3. **How a page flags a printed result the arithmetic does not support** (V2, V3). This is reader-facing wording.
4. **The Gate 3 text** in the draft file.
5. **The three unfixed misses:** the RES 2026 positional match on six pages, the CMA 2026-152 card, and the 2 February roundtable items.
