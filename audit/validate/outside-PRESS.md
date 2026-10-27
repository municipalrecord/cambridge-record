# Cambridge 2026 Validate, piece 4: checked against Cambridge Day

4 October 2026, Opus 5.5 lead. Plan: `docs/cambridge-validate-2026-plan.md`, piece 4.

## Result

**Of 12 votes Cambridge Day reported, 9 agree with our pages on everything the story states, 2 agree in part, and none contradicts the record.** The one count that differs is a story's rounding. The minutes print the count our page shows. The twelfth story reports a briefing, not a vote.

| | Votes |
|---|---|
| Checked, in the rule's order | 25 |
| Reported by Cambridge Day | 12 |
| Agree on every fact the story states | 9 |
| Agree in part | 2 |
| The story reports no vote | 1 |
| Not reported | 13 |

## Method
- **The source:** Cambridge Day (cambridgeday.com), the local news site. It is a source Cambridge's own files do not supply. No records request was made.
- **The votes, by the plan's rule** (`votes.json`): every split roll on a 2026 council night, then ordained ordinances, then every failure, in that order, until 12 had a story. 42 qualified; the reader reached 12 at the 25th.
- **Blind:** a Sonnet reader searched Cambridge Day with only the night, the codes and the city's agenda title (`votes_for_reader.json`). It never saw our pages or data (`press_readings.jsonl`). The lead compared each story with our page.
- **Where they differ:** the minutes are read again, as the record's rule says. A disagreement is published as a question, never fixed by editing.

## The twelve

| # | Night | Item | Cambridge Day | Our page | |
|---|---|---|---|---|---|
| 1 | 26 Jan | ORD 2025-17, Cambridge Street zoning | ordained as amended, 6-3, names | became law as amended, 6-3, same names | agree |
| 3 | 26 Jan | CMA 2026-4, federal update | a briefing; no vote reported | placed on file | no vote in the story |
| 7 | 9 Mar | CMA 2026-51, $400,000 settlement | approved 6-2-1, names | adopted 6-2, one absent, same names | agree |
| 9 | 30 Mar | POR 2026-32, resident parking fee | passed 7-2; Flaherty and Simmons no | adopted as amended 7-2, same two no | agree |
| 10 | 27 Apr | POR 2026-76, Garden Street | passed 5-4, names | adopted 5-4, same names | agree |
| 12 | 11 May | POR 2026-101, foreign policy process | 6-3 vote table, names; result not stated | adopted 6-3, same names | agree in part |
| 16 | 18 May | POR 2026-98, ShotSpotter | passed 5-2-2, names; tabling failed 5-4 | adopted, 5 yes, 2 no, 2 present, same names; tabling failed 4-5 | agree |
| 17 | 18 May | POR 2026-99, direct election of the mayor | 7-1-1, Zusy no, Al-Zubi present; Al-Zubi amendment failed 7-2 | adopted as amended, 7 yes, Zusy no, Al-Zubi present; amendment failed 2-7 | agree |
| 22 | 1 June | POR 2026-111, tree protection | unanimous; McGovern amendment 8-1, Zusy no | same | agree |
| 23 | 1 June | POR 2026-115, ShotSpotter | passed 5-2-2; **calling the question passed 6-3**; reconsideration failed 3-6 | adopted 5-2-2; **ending debate carried 6-2, one present**; reconsideration failed 3-6 | agree in part: see below |
| 24 | 8 June | CMA 2026-174, Ahern Field turf report | tabled 5-3, Nolan absent | tabled 5-3, Nolan absent | agree |
| 25 | 8 June | POR 2026-122, Flaherty's ShotSpotter order | failed 2-6, Flaherty and Simmons yes, Nolan absent | voted down 2-6, same | agree |

**The one difference, read against the minutes.** POR 2026-115, 1 June: Cambridge Day says the motion to call the question passed 6-3. The minutes, page 21, print "Yes – 6, No – 2, Present – 1. Motion passed." Our page shows 6-2 with one present. The page equals the minutes; the story counted Councillor Zusy's "present" with the noes.

## Limits
- Four matches rest on the story's subject and date rather than a quoted order: #7, #10, #12 and #16. Each story's count and names agree with the vote matched.
- The reader's fetch tool summarises pages. Where a count or a name mattered, it asked again for the story's exact sentence; a detail may still be off.
- 12 votes, all on contested council items from January to June. Committee votes, documents and the quieter business of the year are not tested by the press.
