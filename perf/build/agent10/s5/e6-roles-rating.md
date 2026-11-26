# e6_roles rating (E-C4 by-role reporter, M16)

- Who/when: M10, 2026-11-26 ~09:10
- Base: cand6-kit-rating-E-go.md 07629957 (E-C4), dump6-B-final-and-D-go.md 44372F67 (B 082648 identities)

## Files (WS\build\agent16\cg7)

| File | sha256/16 |
|---|---|
| e6_roles.py | CD2EDB821AA00592 |
| selftest\e6\selftest_e6.py | 71EB4534FD56ED76 |
| selftest\e6\selftest-e6.log (14 cases + 6 refusals, ALL PASS) | 4AAB655FDADD1000 |
| selftest\e6\real-e6.ps1 (runner) | 4214C4FAA554D97F |
| selftest\e6\real-e6.log | 94DA0386E9CFB00C |
| roles-073150\e6_roles.txt | 145EAD8F58A64557 |
| roles-082648\e6_roles.txt | 0D1F979B659FAC27 |

## Verdict

SAFE, information only. It is not a proof tool: E is judged by proof5_post v3 plus E-C2..E-C6. e6_roles only supplies the E-C4 window and role breakdown.

## What I checked

- Read all 274 lines of the code. It streams events.tsv once and counts miss rows per (stage, guest), unrecognized_shader rows, frames, miss-cache inserts and identity backings. Red start is taken from game.log (first pad 1 `FF 00 00` speed 18) and mapped to trace ms through trace-start.json.
- Roles come from the time of a guest's first miss row at >= red+40 s: A-AB7D1200 [43,44), U-ABA99710 [44,45), C-A7F79FD0 [58,77); anything else is OTHER. REFBACK: VS ED25B6A0 and PS ED25B8E0 = A, PS ED25BC80 = U, VS ED65D8C0 and PS ED65DAE0 = C. No VS ref for U (ABA99710 has no identity).
- Windows: W1a red+40..59 s, W1b 59..65 s, W2 65 s..stop, plus TOTAL >= red+40 s and PRE.
- Flags: FP-MISSING (the `Native GPU [%s]` format is verified against real game.logs), MISS-CACHE-OFF (`shader miss cache ON|OFF` verified), DIAGNOSTIC, DUP, BACKING-CONFLICT.
- Side effects: it writes only a new dir under cg7, runs at idle priority, has no RESULT line, and exits 0 (2 = refused).
- Real data:
  - 073150: TOTAL 1649 = the post's late count; A 476 / U 166 / C 1007 / OTHER 0; W1a 642, W1b 0, W2 1007; hygiene ON; DIAG 0.
  - 082648: TOTAL 2119 = the post's late count; A 344 / U 156 / C 1619 / OTHER 0; W1a 500, W1b 213, W2 1406; MISS-CACHE-OFF and DIAGNOSTIC flagged, as expected for the dump run.
  - Both runs match the counts in the kit rating.
  - In 082648, A and C backings AGREE with their refs; U VS backing is unknown.

## Answer to M16's question (fixed bands)

Fixed bands are acceptable. In E, any cand miss at >= red+40 s is already an E-C2 FAIL whatever its role. The role only sets the priority and the follow-up, and I re-classify by hand in the E review.

The risk is that the bands are tight. In 082648 the first rows sit at A +43.5 s and U +44.5 s, each 0.5 s inside its band. A covered-role A miss that shifts by about +0.5 s would be labelled U, "known uncovered": a silent priority downgrade. A logged backing catches this (CONFLICT against the A ref), but an unknown backing does not.

## Conditions

- E-R1: in the E review, accept a U-VS classification only if (a) its backing is unknown or is not another role's ref, and (b) U has a single VS guest. Otherwise treat it as a covered-role, high-priority miss.
- E-R2: e6 TOTAL >= red+40 s must equal proof5_post's late cand-miss count for the same run. Any mismatch is investigated before the E verdict.
- E-R3: if OTHER > 0 or any first row lies within 0.5 s of a band edge, I re-check the role by hand from events.tsv.
- E-R4: run e6_roles from the pinned CD2EDB82 copy only; any edit means a re-rate.

## Findings

- NIT E6-N1: for OTHER, print the nearest role band and its distance in seconds.
- NIT E6-N2: for OTHER, `CONFLICT (X ref)` is misleading wording. Print "backing matches role X" instead.
- NIT E6-N3: the per-guest "unrecognized rows" column is not windowed (for example 486 next to 344 misses). Label it "unrecognized rows (whole run)".
