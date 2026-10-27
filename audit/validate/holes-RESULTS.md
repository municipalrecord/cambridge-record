# Cambridge 2026 Validate, piece 5: holes at the point of use

5 October 2026, Fable 5.1 lead. Plan: `docs/cambridge-validate-2026-plan.md`, piece 5. Card 2 of 5 October (the mover line) was answered by the recommended option B: one line, no build of movers.

## Result

**Every 2026 page with a hole carries one sentence saying what it does not show. `check_holes.py` reads 0 findings on build h5; the treediff against v0 shows only the inserted sentences.** 1,063 files changed: 317 by a sentence alone, 738 by the day's date stamps and day counters alone (the awaiting-report pages count the days a request has waited), 8 the census's known build noise. Nothing added, nothing removed, nothing else moved.

| Hole | Where | Sentences |
|---|---|---|
| minutes not out; votes read from the verbatim transcript | council meeting pages, 26 Jan, 9 Feb, 2 Mar, 9 Mar | 4 |
| minutes not out; page follows the Final Actions sheet | council meeting pages (already ruled 2 October) | 5, checked |
| committee votes kept off the page | committee meeting pages, 29 meetings, 102 votes | 29 |
| the city's minutes published, never linked by the note | board meeting pages (Planning Board and others) | 4, each with the link |
| scanned page shown blank, no notice | 75 pages on 11 document pages of 2026 | 75 |
| a document a person ruled held, with no card to say so | item pages ORD 2026-8, APP 2026-61 and one more | 3 |
| the clerk names a mover; the page shows none | item pages with a step on a minutes night and no mover known | 247 |
| what each 2026 meeting page is read from | the council page | 1 |
| meetings the city's portal lists after the last one on the site | board index pages, 17 bodies | 17 |
| the School Committee was not in the 2026 check | its page | 1 |

Two more holes were found and are covered by the same sentences: **the council committees' meetings after June 2026 are not on the site at all** (the Ordinance Committee's 7 and 21 July and 19 August, with nine more committee votes; the Housing and Neighborhood committees' joint meeting of 16 September), and the **28 September council meeting** has no page. The site's notes and fetch run behind the city's portal; the board page and the council page now say how many meetings are missing and the latest date. Fetching them is Publish work, not this piece.

## Method
- One sentence per hole, each a `<p class='recnote hole' data-hole=...>` so the check can count them. Wording follows the 2 October line on sheet-only nights. No em dashes.
- **`check_holes.py`** recomputes the expected set from the database, the vault's manifest and the built pages themselves, by rule, not from the builder's lists: the night's record for each council page; `committee_votes` rows and the PrimeGov manifest's minutes for each board page; the dated steps on each item page, the holds files, `item_motions` movers; the PDF behind each empty page section (found by fingerprint, or by code and page count for a packet slice); the portal's meetings after each body's last page. It also asserts no sentence appears anywhere else. `holes.json` holds the counts.
- **`sentence_diff.py`** proves the treediff: every changed page, with the sentences removed and the page fingerprint set aside, equals the control byte for byte, or differs only by a date stamp or day counter, which it names.
- Five builds (h1 to h5): h1 found 19 item pages whose voice vote the check did not recognise (the check was wrong), the Ordinance Committee's July meetings with no page (a new hole, answered), and scan notes on every year (narrowed to 2026 and to pages with no text at all); h2 to h5 settled which dated steps count for the mover line: every roll and portal action, never a charter right (the page already names who exercised it) and never a night whose minutes do not name the item (fix seventeen A.7).
- Gates: `validate/gates/h5/` (run after this file was written; the progress file records the result).

## Limits
- The mover line is one conditional sentence; it does not show the mover. Showing movers is build work with its own read.
- The scan-page notice has no link on packet slices, which carry no portal link of their own; the item page above carries the city's agenda link.
- Sentences are on 2026 pages only. A held document under an older code (two in `document_holds.csv`) and blank scanned pages in older documents carry none.
