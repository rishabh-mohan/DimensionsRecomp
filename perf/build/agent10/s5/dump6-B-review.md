# dump6 run B (082648) review: dump6_post + C-S1 + stage6 dry

- Who/when: M10, 2026-11-26 08:49
- Base: dump6-plan-rating.md 5749F60E (B-C4..B-C7, D-C1); dump6-stepC-rating.md B0A9B0C6 (C-S1, Cond 1-3);
  dump6-stepD-rating.md EEE8B6A5 (D Cond 1-4); dump6-B-go-check.md 517729C4

## Files (sha256/16, computed by M10)

| File | sha256/16 |
|---|---|
| cg7\post-20261126-082648\dump6_post.txt | 0B618C450A004F66 |
| cg7\post-20261126-082648-cs1.txt | 8A9174CA5C7A77E4 |
| cg7\cs1_times.py | E0BBBA1867E56F5E |
| cg7\stage6-dry-20261126-082648.txt | 0BD9612AF9312623 |
| gameplay logs\gameplay-20261126-082648.txt (runlog) | 6D5424E1 (per Overseer; read by M10) |
| trace-native5d-20261126-082648\events.tsv (236.9 MB) | 5341E0FC (per Overseer; scanned by M10) |
| M3 DIAGNOSTIC route post | NOT YET RECEIVED |

## Verdict

- (a) B: VALID-PENDING. Everything I can check now holds. Final once M3's DIAGNOSTIC post confirms X1 and the
  route items (B-C4).
- (b) Coverage with C-S1 applied: PARTIAL 7/8 (W1 5/6, W2 COVERED). 0 C-S1 flags. This MEETS the D build gate
  (D-C1, PARTIAL with ≥1 NEW: 5 NEW, all target-linked).
- (c) ABA99710 is an ACCEPTABLE risk for a later cand6 proof (E). If it still misses, E fails honestly; nothing is
  promoted on PARTIAL.
- (d) D-S1 is CLEAN, and stage6 dry PASS. The real stage6 and `native6pack.ps1 plan` are cleared as light steps
  (SAFE-IF below). Pack, bin and check wait for (a) final and the user.

## What I checked

- B-C4 real-log checks (runlog), all hold:
  - DIAGNOSTIC line L3 with the dump env; ZONE L4; CAND5 L5 (gp5d-native, trace-native5d, expect-fp a349d529);
  - verify-bins 0 FAIL on native5pack-bin and bin-native5 (787CD694);
  - L49 keystrokes 0;
  - L50-53: run-game, sidecar, holdwatch and watcher all exit 0; L55 clean exit 0x00000000, dumps 0;
  - L163 GAMEPLAY DONE, post exit 0. The auto post's PASS-WITH-CHECKS (missing draws) is expected in a dump run.
  - LATEST.txt carries ` DIAGNOSTIC dump on, timing invalid`.
  - Sidecar ctl=0 (via dump6_post D1). fp a349d5292f67b127 is in game.log.
- B-C5: outputs are in M3's dirs, plus M16's cg7 post dir. Only one new dump dir (082648).
- B-C7 G7 after the run (08:46): bin-native C5181520, bin-native5 787CD694, native5pack-bin 787CD694,
  LATEST-pack AC7B9053, LATEST-bin 76D0EFB9 all unchanged. Kit ps1 DE16A2D2 / RUN-GAMEPLAY 603916BB = installed.
  0 legodimensions processes.
- Step C Cond 1: dump6_post 7887B90A, with --fp and --dump-dir given (fp True; dump-dir 082648).
- Step C Cond 3:
  - miss-cache inserts 0 (dump mode proven; 073150 had 6);
  - draw_missing rows before red+40 s: 0;
  - D1 PASS; D2 stop red+104.7 s;
  - D4 PASS 5/5 (size = vb+4+pb, marker OK); D5 0 early; D7 1 raw per stage (zero bucket C77B3ABB6F87ACD9).
  - RESULT and split quoted verbatim:
    `RESULT: PARTIAL (7/8 targets matched; unmatched: W1 VS ABA99710); W1 PARTIAL (5/6), W2 COVERED`.
- C-S1 (my own trace scan, scratch b_rows.py over events.tsv):
  - The identity event precedes the first unrecognized row by ≤ 7 ms for AB7D1200 (+43.536 / +43.543) and
    A7F79FD0 (+59.025 / +59.030). The PS identities likewise sit at their first rows (cs1 output).
  - A7F79FD0 has 4858 rows, +59.0..+104.7, with no gap > 0.5 s. The W2 "EARLY-WIN" flags are the +65 s window
    boundary clipping one continuous scene, not address reuse, so W2 COVERED stands.
  - 5 identities, far below the 256 cap.
  - Every match is by guest, and AB7D1200 / AB854C80 also agree with their game.log backings
    (ED25B6A0 / ED25B8E0 = identity physical).
- Analog check vs 073150 (same physical backing or role):
  - VS AB80F350 -> AB7D1200 (both backing ED25B6A0);
  - PS AB77B580 -> AB854C80 (both ED25B8E0);
  - PS ABB3F110 -> ABB41A90;
  - W2 VS A7F7A100 / PS A7F79ED0 -> A7F79FD0 / A7F79DA0;
  - VS AB64C0E0 -> ABA99710, the unmatched one.

  So 5 of the 6 073150 targets have a captured container.
- ABA99710: 468 rows, +44.5..+55.8, with the same 7 s gap at +46 as AB7D1200 (co-rendered). It has no identity
  event and no backing line.
  - The snap1 capture returns silently on a container-hash duplicate (L190-193) or on a header/range check
    (L165-180).
  - M16's duplicate theory (same bytes as 56F18006, so the AOT microcode lookup would hit after packing) is
    plausible but unproven. The data here cannot separate the two.
- D-S1 / stage6 dry:
  - base 141 rows, SUMS FA99EB7D; exactly the 2 roots dropped;
  - 5 NEW, 0 same, 0 dup; combined 144 = 139 + 5;
  - each NEW name equals a B identity container_hash (56F180069A723975, E566393ABD204284, 6EE915B02394D8D4,
    F976B389E947A6DA, 4DB01A8D1CE316BA);
  - each NEW sha equals its D4 sha (98E17056 / 18439A7B / CFD5F3E4 / 6D75E47B / 4A14CC86);
  - no NEW file is unlinked to a target.

## Conditions

1. (a) becomes final when M3's DIAGNOSTIC post shows:
   - title gate HIT, prompts 1/1 x3, 302/302, zone=done;
   - X1 ctl=0 and keystrokes 0;
   - DIAGNOSTIC labelling;
   - no claim beyond diagnostic (B-C6).

   B is never a proof base or timing source.
2. Real stage6: default --out-root, after B and outside exclusive windows. It must list the same 5 NEW with the
   same shas as the dry run, RESULT PASS, combined 144, and its combined6 SUMS sha reported.
   Then `native6pack.ps1 plan --input <combined6>`: PLAN OK, 0 bad pins, 148 selected (4 s35 + 144), 0 excluded,
   writes only pack\plan-<stamp>.txt.
3. Pack, bin and check: a separate GO after (a) is final and the user's review, under Step D Cond 4-6.
4. E (cand6): its post must report the ABA99710 analog explicitly, by role (VS co-drawn with the AB7D1200 analog,
   ~+44.5 s after red). E-C2 (0 misses ≥ red+40 s) stays the bar. A remaining ABA99710 miss = E FAIL, with no
   re-labelling as PASS. The E kit word and post get their own ratings (E-C1..E-C5).

## Findings

- NIT B-N1: dump6_post's C-S1 needs the true first row, not the window first row. Fold cs1_times' "true first"
  logic into dump6_post before E use, as the C-S1 code fix.
- NIT B-N2: ABA99710 has no backing line because the game.log warnings are capped at 16. A dump run with a
  per-guest warning (or an identity "duplicate of" event) would settle the duplicate theory. Not needed before E.
