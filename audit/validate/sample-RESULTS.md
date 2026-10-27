# Cambridge 2026 Validate, piece 3: a new blind sample of 100 rows, two readers

4 October 2026, Opus 5.5 lead. Plan: `docs/cambridge-validate-2026-plan.md`, piece 3.

## Result

**0 of 100 rows wrong (95% interval 0% to 3.6%).** Two rows were graded "missing" for one kind the census had already ruled benign: scanned pages shown blank with no notice. Counted as misses, the rate is **2 of 100 (0.2% to 7.0%)**. Both readings are given; the accuracy page prints both.

| | Rows |
|---|---|
| Exact | 62 |
| Benign | 36 (30 of them: no mover line where the clerk names a mover) |
| Missing | 2 (D425, D450: scanned pages blank, no notice) |
| Wrong | 0 |

**Said plainly:** this sample tests the census itself. The census called all 1,206 rows clean. A fresh draw, read by two new readers who never saw the census's readings and graded by graders who never saw its grades, found no row the census should have caught as wrong. With 100 rows, the true rate of wrong rows the census let through is very likely under 3.6%.

## Method
- **Population** (`population.json`, written before the draw): the census's 1,206 rows, less the 121 it read twice and less the 24 rows that cover Dan's piece-2 votes. 1,061 rows: A 578, C 38, D 445.
- **Draw** (`draw.py`, `sample.json`): seed **2610052**, a seeded shuffle within each stratum, in proportion to the census: A 55, C 4, D 41.
- **Readers:** two independent sets of Sonnet readers, S1 and S2, five lanes each, on the census's own reader briefs and task lists, blind to our pages, to the census and to each other (`readings/`).
- **Graders:** six Opus graders on the census's grader briefs, comparing both readings with the census's final build (f16, rebuilt here as v0 and proven identical). They saw only this sample's readings, never the census's (`row.py`, `grades/`).
- **Interval:** Clopper-Pearson, as the Audit used.

## The readers
- **They agreed on every graded fact in 97 of 100 rows.** The three disagreements: two rows where S1 left out two blanket roll calls that S2 listed (incomplete, not wrong), and D220, where S2 said the minutes held no private details and they do.
- **Reader error rate:** S1 got 0 rows wrong; S2 got 1 (D220).

## The two "missing" rows
D425 (CMA 2026-244, the City Solicitor's three-page opinion) and D450 (APP 2026-55's letter, permit form and artwork) are packet slices whose scanned pages have no text layer. Our page shows those pages blank, with no notice and no link to read them. Nothing false is shown, and no download of ours is offered, as ruled. The census graded six rows of this kind benign. The point-of-use rule says a blank must never be left to read as "no", so **piece 5 gives every such page a notice.**

## Notes for the lead, not misses
- **14 committee pages for 2026 have no minutes link** though the city has published minutes for them (found on C43). Nothing false is shown. Piece 5 adds it to the inventory of holes.
- **A216 (CMA 2026-74):** the minutes print the second-reading roll under CMA 2026-74; the clerk's sheet files it under the ordinance sub-item, and our ordinance page shows it. The CMA page does not mention it. Graded benign, as the census graded it after fix round 1.
- **D067:** a credit-rating agency's analysts' work contacts are masked as if private, and the item page still offers the city's original. Over-masking, graded benign.
- Some readers and graders wrote helper scripts into a shared temp folder and overwrote one another's scripts. Every output file holds only its own rows, one per id; no reading or grade was affected.
