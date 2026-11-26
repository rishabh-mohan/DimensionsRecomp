# dump6 Step A kit draft (corrected 08:16): rating

- Who/when: M10, 2026-11-26 08:18
- Base: dump6-plan-rating.md 5749F60E (A-C1..A-C6); live kit = a\ copies
- Draft dir: WS\build\agent3\drafts\dump6-20261126\

## Files (sha256/16, computed by M10)

| File | a\ (= live) | b\ (new) |
|---|---|---|
| gameplay-run.ps1 | 691B70ADA6C55839 | DE16A2D29C0F040A |
| RUN-GAMEPLAY.cmd | B2B2BE248085E167 | 603916BBDD6710C0 |
| RUN-EXPLORE.cmd | 5B05E10FEF89EF56 | B6E8DAD4DB9E51C1 |
| RUN-MANUAL.cmd | 6A0AEECAF97BF643 | 6B5C3FC6D0271D82 |
| dump6.diff | | 657AC28FE43EB754 |

## Verdict

SAFE-IF (conditions below are the plan's A-C5/A-C6 restated for 4 files). No BLOCKER, no SHOULD.

## What I checked

- A-C1 gate, ps1 L67: `$Dump -and -not ($Manual -or (cand5 and zone in $words))`. nativeonly is
  enforced by L73 (cand5 needs nativeonly), xenosonly by L68. Using `$words` at L67 is correct:
  `$Cand5`/`$Zone` are set later.
- A-C2: hand trace of all 13 must-exit-2 cases, all exit 2 before the lock
  (`cand5 zone dump` via L73; `... xenosonly` via L68; `cand5 explore zone dump nativeonly` and
  `cand5 manual dump nativeonly` via L72; the 8 old cases unchanged). Allowed: `nativeonly cand5 zone dump`,
  `manual dump nativeonly`. Self-test list L261-262 carries all 13.
- A-C3: DIAGNOSTIC Say L144 (dump run, timing invalid, miss cache OFF); LATEST.txt suffix
  `DIAGNOSTIC dump on, timing invalid` on route (L357) and manual (L345). gameplay_post.py unchanged
  (GPPIN_03 E33DF654). The manual-dump Say wording also changes; acceptable.
- A-C4: tag gp5d (L201), trace `trace-native5d-<stamp>` (L137), consistent at L146/L204/L216/L225/L302/L303/L319;
  watcher filters `*-$Tag*` (gameplay-watch L113), so gp5d logs are picked up. Dump env L209 unchanged.
- ps1 b: PS ParseFile 0 errors; no BOM, same as a.
- RUN-GAMEPLAY.cmd: only GPPIN_01 -> DE16A2D2 plus a 2-line rem extension; CRLF 58/58 (a 56/56).
  GPPIN_02/03/04 unchanged.
- RUN-EXPLORE.cmd, RUN-MANUAL.cmd: exactly one line differs each, GPPIN_01 691B70AD -> DE16A2D2;
  CRLF 57/57 unchanged. The correction is needed: without it both would refuse with exit 3.
- No other file in build\agent3\gameplay pins the ps1 or any of the 3 cmd shas (search for the 4 old
  sha8s hits only the 3 live cmds' GPPIN_01 lines).

## Conditions

1. Install all 4 files together (a partial install leaves a cmd refusing with exit 3). Backup = a\; rollback = copy a\ back.
2. I2-style after install: the 4 live shas equal the b\ shas above; pins ok; PS 5.1 parse 0 errors;
   live tamper x3 -> exit 3, restored -> exit 0.
3. A-C5 dryruns, all exit 0 with logs:
   1. `dryrun nativeonly cand5 zone dump`: dump env line, ZONE, CAND5 and DIAGNOSTIC lines, verify-bins
      on both bins, SIDECAR with zone args and no then-mark, no dump dir left behind, 13 exit-2 cases ok, ALL PASS;
   2. `dryrun nativeonly cand5 zone`: no dump env line;
   3. `dryrun manual dump nativeonly`: passes.
4. RUN-EXPLORE.cmd and RUN-MANUAL.cmd each pass their pincheck and one dryrun (exit 0).
5. B GO line (only after 3-4 pass and dump6_post.py is rated, per B-C1):
   `RUN-GAMEPLAY.cmd|603916BBDD6710C0213AFDE818619FA16431268DDA343801ACB8EA93C6CB6B5B|nativeonly cand5 zone dump`.

## Findings

- NIT S-A-N1: RUN-GAMEPLAY.cmd grew 2 lines (rem block) while EXPLORE/MANUAL did not; harmless, note only.
