# #21 S4-T1: what the threaded-mode proofs still need (M7, S3T-7, 2026-11-25)

Paper only. Source: FUNCTIONAL-ROWS.md section 3 (must-prove map), RATE-REQUEST.md, Agent 10's rating
`build/agent10/t27/r21-s4t1.md` (5 conditions, NIT N-d), HANDOFF.md section 3.

## Already done (no run needed)

| # | proof | state |
|---|---|---|
| MP4 | CaptureShaderBindings never on PREPARE_THREADS workers | PROVEN statically, `check/MP4-STATIC.md` (FEB0FF3E...); the F-CA caveat is recorded under gap 2 |
| MP5b | device loss with work queued | code read accepted (only device-removed path is pipeline_library.cpp:445; #21 adds no device call) |
| W1 matrix | N-d: W1 had no matrix file | DONE: `matrix-s4t1-w1.json`, queue row s4t1-w1 repointed, check_rows.py ALL CHECKS PASS |
| base | before/ == snap1 (native4b's source, MANIFEST pin 9b40acbbef4c57b3) == live DimensionsRecomp gpu_native (HEAD c9e215f, no gpu_native change since b0bd3b4) | sha256 equal for all 3 files; `git apply --check` from the WS root: before exit 0, -R on after exit 0, negative control exit 1 |

## Still open: needs runs (all wait for LOAD GO)

| # | proof | row | what reads it | tool state |
|---|---|---|---|---|
| MP1 | hash0 ~ 0 in n2/n3, draws/frame and marks = n0, no new warning type | F1 | check_n_rows on th3 / th2 dirs vs n0 | tool exists |
| MP2 | same frames (proxy) | F1 | light share + perf.csv draw_calls distribution vs n0 (n0-r1 vs r2 = noise), logdiff | **script not written** (offered: M7 can write it on paper now) |
| MP3 | queries/readbacks complete before the guest reads them | F3 (QUERY_TRACE_FROM=0) | compare per-query (draws, samples) sequences th3q / th3cp3q vs n0q | **script not written** (offered) |
| MP5a | shutdown with work queued | F1 | every arm closes cleanly within close_timeout_s, no kill | run-matrix result |
| #21 unset | unset == old bin | F1 (b) | th3 (new bin) vs th3old (native4b), read on r2 where both bins are warm | read-out step |
| #21 ON | mode-3 line and roles | F1 rule 3 | th3cp3 / th2cp3 game.log lines | read-out step |
| W8b pre-flight | every arm boots/logs/closes on the W8b bin | W1 | PASS rule in matrix-s4t1-w1.json notes | matrix ready |

## Prerequisites before any of those rows can start

1. LOAD GO from the Overseer.
2. Agent 2 builds native4b + `s4-t1.diff` (sha256 46FFD2E9...) at <= 2 threads; bincheck finds the 3 needles listed in FUNCTIONAL-ROWS.md.
3. `build/agent3/s4b/ready-s4t1` and `ready-later` exist.
4. Copies of matrix-s4t1-f1 / f3 / w1 under `build/agent3/s4b/s4t1/` with `<NATIVE4B-S4T1>` and `<NATIVE4B>` replaced.
5. The new bin gets its own native fingerprint (#21 changes native code) and a re-pin before W8b timing; quote both fingerprints.
6. Agent 10's conditions: throttling opt-out at default; order F1 -> W1 -> W8b; idle host, busy < 0.97, no slow state;
   no cache/seed copies between bin dirs (F1 (b) read on r2); any th2/th3 hang checked against F-CA first.
7. W8b read-out quotes the power scheme.

## Stale command form (tell whoever applies the diff)

README.md L28-30 use `--directory=games/lego-dimensions-recomp/...`, which assumed the git toplevel was
`C:\Users\<user>\.vscode\projects`. The WS is no longer inside a git repo, so from the WS root use
`--directory=build/agent7/s4-t1/before` (verified above). For a real apply to a non-repo tree, add
`-c core.autocrlf=false` or copy `after/` (the global autocrlf=true rewrites line endings).
