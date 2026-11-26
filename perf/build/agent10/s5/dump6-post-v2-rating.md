# dump6_post v2 re-rate (B-N1 + C-S1)

M10, 2026-11-26 08:55. Re-rates dump6-stepC-rating B0A9B0C6 (v1 7887B90A) for the B-N1 / C-S1 fold-in. Read-only: I ran nothing and read only the diff, the code and the logs.

## Base

| File (WS\build\agent16\cg7) | sha256/16 |
|---|---|
| dump6_post.py (v2) | 2AD999BD6763B4B4 |
| v1\dump6_post.py | 7887B90A73497D5A |
| dump6_post-v2.diff (57 lines) | AA6A3A26E76DBA76 |
| selftest\selftest_dump6.py | 0C2C93483F798F7C |
| selftest\selftest-dump6-v2.log | C5423855420A107C |
| selftest\real-v2.log | 7CAEBE62EECA376B |
| post-v2-082648\dump6_post.txt | 70F1076D7F718759 |

Fixture SUMS 0B2B22EB (455 files) as reported in the log; I did not re-hash it.

## Verdict

**SAFE**, for future dump runs only. It is still not a proof tool: E uses proof5_post v3 plus E-C2..C4. C-S1 (B0A9B0C6) and B-N1 (2090CDB5) are closed.

**M16's CAP question:** keep CAP flagging every match, backing included. That is conservative, and real runs are far below the cap (5 identities against 256).

## What I checked

**B-N1, true first row (scan L95, L131):**
- `allfirst.setdefault((st, g), ts)` runs for every unrecognized_shader and draw_missing_* row with a valid stage and guest. It runs before the `ts < t1` window clip, so it records the first row anywhere in the trace.
- Units are trace ms. Identity events have `d['ms'] = ts` from the same clock.
- Fallback `R['allfirst'].get((st, g), f0)`: the key always exists for a target, because a target row was itself recorded, so the fallback never fires.

**C-S1 (main D3):**
- A guest match gets EARLY unless some identity of it is at ≥ true first − 1000 ms.
- A backing match is OK at any time.
- `cap = len(ids) >= 256` adds CAP to every match.
- A flag keeps the match listed, but the window is at best `PARTIAL (n/n; C-S1 flagged k)`. COVERED needs `not nf`, and RESULT COVERED needs `not flagged_all`.
- The flag summary line is printed before RESULT. The RESULT order is unchanged.

**Selftest log C5423855, 19 cases ALL PASS:**
- The 11 v1 cases give the same RESULTs.
- The 4 refusal cases exit 2.
- The 4 new cases:
  - **cs1-early:** identity at red−10 s, true first +45 → PARTIAL, EARLY.
  - **cs1-truefirst:** pre-window rows at +20 s, identity at +20.0005 → COVERED. This proves the true first row is used and not the window-clipped +45.
  - **cs1-backing-early:** backing match with identity at red−5 s → COVERED, "OK (backing)".
  - **cs1-cap:** 4 + 252 = 256 identities → PARTIAL, all 4 matches flagged CAP, D4 still PASS.

**Real data:**
- real-v2.log: 082648 PARTIAL 7/8 (unmatched W1 VS ABA99710); 073150 NOT-COVERED 0/6; 051154 INCONCLUSIVE. All three equal v1.
- post-v2-082648 L66: "identity events 5 … below cap; flagged matches: none".
- All 7 matches are guest matches, each with the identity at its true first row: +43.5/+43.5/+44.5/+59.0/+59.0. W2 shows true first +59.0 against a window first of +65.0, which is B-N1 working.

## Findings

- **NIT V2-N1:** a guest match still can't tell guest-address reuse apart when an older identity at the same guest exists after the true first row and the newer capture silently failed. container_hash isn't recomputed because there is no xxhash. This is residual and informational only: E's proof5 miss counts are the real test.
- **NIT V2-N2:** real-v2.log keeps only the RESULT lines. For a future run, also keep the C-S1 summary line in that log. The full text is in post-v2-*\dump6_post.txt.
