# dump6 Step C (dump6_post.py + self-test): rating

- Who/when: M10, 2026-11-26 08:25
- Base: dump6-plan-rating.md 5749F60E (C-C1..C-C5, B-C1..B-C7); dump6-stepA-rating.md F7E38737
- Source checked: snap1 shaders.cpp 9567FE3F L146-207 (CaptureMissingPlacementShader)

## Files (sha256/16, computed by M10)

| File | sha256/16 |
|---|---|
| cg7\dump6_post.py (409 lines) | 7887B90A73497D5A |
| cg7\selftest\selftest_dump6.py | 0C7790EE166AA477 |
| cg7\selftest\selftest-dump6.log (15/15 ALL PASS) | 781067628540CA6A |
| cg7\selftest\fixtures\SHA256SUMS.txt | 57DB86E235302D62 |
| cg7\post-real-073150\dump6_post.txt | AB1FD21EA79440C1 |
| cg7\post-real-051154\dump6_post.txt | A61718A909163236 |
| cg7\CG7-report.md | F844C973C286CEA5 |
| cg7\PLAN-dump6.md v2 | 320BA2DB664DCFCB |

## Verdict

SAFE-IF. No BLOCKER. One SHOULD (C-S1), handled as a review-time check so no code change is needed
before B. With this rating, B-C1's "C is rated" part is met.

## What I checked

- C-C1 static: reads its inputs only; writes one file, `<--out>\dump6_post.txt`, into a new dir under
  WS\build\agent16\cg7 (refuses an existing dir or one outside cg7: exit 2). No subprocess, delete or shutil
  calls; ctypes is only used for background priority, as in proof5. Both scripts parse (ast) under `python -B`.
- C-C2 D1: the v3 anchors are carried over exactly: gate regex `wait line 55 current=5 pending=0 \d+ +ok after`,
  prompts anchored `prompts=batman:1/1 gandalf:1/1 wyldstyle:1/1` with space/end look-around, clean exit,
  302/302 + `(last: done)`, the 5 kit exits. Also zone=done (anchored) and the red-18 start.
  D2: stop (last trace frame) >= red + 80 s is a separate gate that yields NOT-REACHED. The red start is
  the first pad 1 `FF 00 00 (... speed 18)` line; the fixture adds an earlier speed-30 red as a decoy. On real
  073150 it gives red 07:44:52.486, which equals my own figure, and stop red+104.5 s.
- C-C3 D3: a target is matched only by (stage, guest) or by identity physical == game.log backing for the same
  stage. physical_hash only produces an information list (L250-257) and never enters `hit`. falsecover and
  falsecover2 (a physical_hash join present, target stays UNMATCHED) show this. Payload ints are decimal
  (`stage=` / `guest=` printed as u32/u64 by LongProbeEvent), so KV `\d+` is correct; 051154 matches 25/25
  targets by guest, which is a positive real test.
- C-C4 D4 states the check that ran: name + size == vb+4+pb + marker == vheader[8:12] + sha256, container_hash
  not recomputed. The layout matches the source (L182-186). D7 counts raw files per stage against identities and
  lists them. The zero bucket is at most 1 per stage by construction, since raw files are named by stage + prefix
  (see C-N1).
- C-C5: there are 11 result cases + 4 refusals, including 2 false-cover cases, d4bad, nodump, notreached,
  gate56, prompts 1/10 and notargets. I re-hashed all 143 fixtures against SHA256SUMS.txt: 0 mismatches,
  143 files on disk. The log shows 15/15 PASS.
  I did not re-run the self-test, because it rewrites fixtures in M16's dir.
- RESULT precedence (INVALID > INCONCLUSIVE > NOT-REACHED > COVERED > PARTIAL > NOT-COVERED) is conservative.
  COVERED needs every target matched and D4 PASS over all identities. Exit 0 only for COVERED.
- Real 073150 output (no dump dir): NOT-COVERED 0/6 with D4 FAIL, as designed. W1 4 targets (VS AB80F350,
  AB64C0E0; PS AB77B580, ABB3F110), W2 2 (VS A7F7A100, PS A7F79ED0). VS draw_missing totals 476+166+1007 = 1649
  match my count. PS targets come from unrecognized rows only, which is stricter and acceptable.

## Ruling: ctl

Report-only in dump6_post is fine. The X1 gate (ctl=0, keystrokes 0) stays in M3's run post and is a hard
part of my B review (B-C4).

## Conditions

1. Run exactly dump6_post.py 7887B90A with `python -B`, after the B run and M3's post, outside any other
   agent's exclusive slot:
   `--trace build\agent3\gameplay\trace-native5d-<stamp>\events.tsv --log <B run dir>\game.log
   --post build\agent3\gameplay\post\gameplay-<stamp>.txt --runlog build\agent3\gameplay\logs\gameplay-<stamp>.txt
   --sidecar build\agent3\gameplay\logs\<stamp>-native.sidecar.out.txt
   --dump-dir build\agent3\gameplay\shader-dumps-native-<stamp> --fp a349d5292f67b127
   --out build\agent16\cg7\post-<stamp>`.
   --fp and --dump-dir are mandatory. Without them the result cannot count.
2. C-S1 review-time check (my B review applies it, and a failure downgrades COVERED to PARTIAL):
   - every MATCHED target's identity event (time listed in the identity block) is at or after the target's
     first row minus 1 s, or the match is by backing;
   - and the identity count is below the 256 capture cap.
   The source says placement addresses are reused (L190-193). An identity captured earlier at the same guest
   with different code would match by guest while the late code was never captured: cap reached, or the
   header validation at L175-180 rejected it.
3. B review will also require: miss-cache inserts 0 (proves dump mode; 073150 had 6); the dump dir exists with
   placement-containers; RESULT and the W1/W2 split are quoted verbatim; DIAGNOSTIC wording only (B-C6).

## B GO

The GO for `RUN-GAMEPLAY.cmd|603916BBDD6710C0213AFDE818619FA16431268DDA343801ACB8EA93C6CB6B5B|nativeonly cand5 zone dump`
is valid once M3 reports the Step A conditions met: 4 live shas = b\; pins, parse and tamper x3; A-C5 dryruns 1-3;
EXPLORE/MANUAL pincheck + dryrun. Plus B-C2..B-C3: CG2 preflight (no lego process, G7 shas), start by 09:30,
hands off, exclusive window. I will confirm M3's report against this list when it arrives.

## Findings

- SHOULD C-S1: a guest match does not check the identity time or the capture cap. Covered by Condition 2 for B;
  fix in code before any E use: print the matched identity's red-relative time and flag EARLY/CAP.
- NIT C-N1: D7 has no explicit zero-bucket line. The prefix the game.log gives (C77B3ABB6F87ACD9) is shown as
  present/absent, which is enough.
- NIT C-N2: the D5 wording "expect 0" is information only and not part of RESULT; keep it that way.
