# Agent 7 handoff (Nov 23, before the break)

Paths are relative to the workspace root. Nothing in `build/agent7/` is built into a bin or committed by me.

## Rules that still apply

- Only Agent 1 commits or pushes. The S4b/S4c code is on GitHub: rexglue-sdk `perf/opt` 5350b1d, DimensionsRecomp
  `perf/opt` b0bd3b4.
- Before any command, check that `perf-notes/WINDOW-HOLD.txt` does not exist. If it exists, wait.
- Python: Below Normal, `python -B`, from script files, one process at a time. Read-only on `build/agent8/matrix/**`.
  Never list `build/agent2` recursively; open its files by path.

## What I own

- `build/agent7/**`, all of it.
- `perf-notes/agent7-present.md` is my running notes file from earlier tasks (not touched in task #21).

## State by item

### 1. Formal readouts, task #21: `build/agent7/readout/`. Done.

| file | what | state |
|---|---|---|
| `W9.md` | W9 = `build/agent8/matrix/20261123-0108` + `20261123-0401` (#24 GPU-wait back-off sweep, devoff4b) | final, rev 1 (§10: L20 citation, L88 wording, Agent 8's recompute) |
| `W5b.md` | W5b = `20261123-0155` + `20261123-0451` (TimerQueue wait modes d11 / d11t / d11p, devoff4) | final, rev 1 (§10: the checker's 11 fixes and Agent 8's one slip) |
| `check/CHECK-W5b.md` | read-only checker's report on W5b.md (and W9.md L22-29, L252-256) | ~830 claims, 11 mismatches (0 high), all fixed in rev 1 |
| `check/fixes-rev1.txt` + `check/apply_fixes_rev1.py` | the rev 1 edit list and the all-or-nothing script that applied it (each old text found exactly once; in-place edits keep the line count, so cited line numbers still hold); W9.md L88 was edited by hand | applied 07:44; pre-fix copies `check/W5b-rev0.md`, `check/W9-rev0.md` |
| `build/agent8/readout/w-followup/a7check/W9-W5b-check.md` (Agent 8) | independent recompute of W9 and W5b from results.csv, with separate code | 912 claims: 880 agree, 21 rounding ties, 9 light-share definition, 1 slip (fixed); 0 sign flips, no `*` changes |
| `pool_readout.py` → `pool-W9.md/.json`, `pool-W5b.md/.json` | pooled two-pass read-out; `.pkl` files are data caches | self-check PASS: W9 204 numbers per pass, W5b 108, max abs diff 0 |
| `load_check.py` → `load-check.md` | load (ng_t) vs fps checks, quiet medians, paired counts | done |
| `tail_check.py` → `tail-check.md` | W5b long-frame check per run and arm | 36 of 36 runs match frames.json |
| `cluster_0221.py` → `cluster-0221.txt` | the 0221-d11t-r5 stutter cluster (perf, gpu, proc, sys csv and game.log) | done; cause not identified |
| `recompute_headlines.py` → `headlines-W6-W4c.md` | Agent 8's W6/W4c headline numbers recomputed from results.csv | 116 claims, 114 agree, 2 differ by rounding only |

Verdicts:
- **W9:** pick q500; drop q0; the q125/q250 instability is host-triggered (the q arms are more exposed to it, not
  broken).
- **W5b:** pick d11p, narrowly, over d11t; both save about 0.2 core vs d11, all of it on the TimerQueue thread. The
  runner agrees (d11p −0.2045 core, rounds to −0.20). W5's d11t p99 lead is not reproduced. The post-gate load hit the
  first 4 scored runs; no verdict changes without them. "Narrowly": without the flagged runs the frames can't separate
  d11t and d11p, and the loaded-run gap (−3.0 vs −1.1 % fps, n = 4 each) is post hoc and n.s. (Welch p 0.083).
- Comparisons with W4b/W5 or older carry a caveat: the Defender exclusion for `build/` was added about 23:16 on Nov 22.

Commands (workspace root, Below Normal, one at a time):
- the pool commands are on L6 of `pool-W9.md` and `pool-W5b.md` (they include the `--variant` flag sets);
- `python -B build/agent7/readout/load_check.py -o build/agent7/readout/load-check.md`
- `python -B build/agent7/readout/tail_check.py build/agent8/matrix/20261123-0155 build/agent8/matrix/20261123-0451 -o build/agent7/readout/tail-check.md`
- `python -B build/agent7/readout/cluster_0221.py`
- `python -B build/agent7/readout/recompute_headlines.py -o build/agent7/readout/headlines-W6-W4c.md`

### 2. T-std read-out kit and noise methods, tasks #6 and #14: `build/agent7/w4b-noise/`. Done.

- `RESULTS.md`: noise-method comparison on W4b and W5 (T-std, B-block, guards).
- `readout.py` + `READOUT.md`: one command per matrix folder, markdown + json:
  `python -B build/agent7/w4b-noise/readout.py build/agent8/matrix/<dir> -o <out>.md --json <out>.json`
- `REPEATS.md` + `repeats.py`: 95 % CI half-width per arm for 3-5 repeats and 2-5 arms, with minutes.
- `test_noise_methods.py`: self-test; it reproduces RESULTS.md on W4b and W5. `check-readout/CHECK.md`: checker report.

### 3. S4-T1 (#21) `LEGO_NATIVE_CHAIN_PRIORITY`: `build/agent7/s4-t1/`. Staged and rated, not compiled.

- Diff revision 2, +51/-0, over native_worker.cpp, native_recording.cpp and native_preparation.h. The base is
  `build/agent2/snap1/DimensionsRecomp/rexlego` (the S4b sources native4b is built from). `SHA256SUMS.txt` lists the
  code and diff hashes; `make_s4t1.py` (proofs 1-6) and `check_rows.py` both PASS. Index: `README.md`.
- **Rating** (`build/agent10/t27/r21-s4t1.md`): (a) default-off test bed SAFE; (b) value 3 in F1, F3, W1 and W8b
  SAFE-IF 5 conditions; (c) ACCEPTED with one wording fix and one addition. Both were done on Nov 23:
  - `RATE-REQUEST.md` §15 (rev 2a): the §9.2 wording ("only GetDeviceRemovedReason call", plus the UINT64_MAX guards),
    the 5 conditions and the NITs. Lines 1-297 keep the rated numbering, so Agent 10's citations still hold. sha256
    now `164790BBFFB66CA0…` (rated copy `AFE56587…`).
  - `check/MP4-STATIC.md`, last section: **F-CA recorded under MP4 gap 2.** sha256 now `FEB0FF3EA0A6BBF7…` (rated copy
    `F0920954…`). Neither doc is in SHA256SUMS.txt.
- **F-CA** (`build/agent10/t27/sub-r21-coderead.md` §6): a th2-only deadlock path in the color-alias retire handoff
  that predates #21. Not seen at runtime.
- **Earlier th2 runs: none hung.** 4 runs (s3-n2-0210, 20261122-0452, -0652 n2t, -0657 n2s under
  `build/agent8/matrix/`), about 8.4 min in total on one route, all reached the normal exit with exit code 0. This is
  weak evidence, because nobody knows whether color-alias handoffs happen on that route.
- Open:
  - Agent 2 compiles it into native4b and runs the bincheck; then re-pin the native4b baselines.
  - Rows in the order F1 → W1 → W8b, under Agent 10's 5 conditions: the throttling opt-out cvar at its default; F1
    pass rule 3 before any W8b arm counts; an idle host (busy < 0.97, no slow state); no `cache/` or seed copies
    between bin dirs, and F1 (b) read on r2; any th2 hang, timeout or dump checked against F-CA first.
  - W1 still needs a matrix file with the same three clock-spin cvars as the other rows.
  - My MP2/MP3 sequence comparisons from the F1/F3 output.
  - W8b's read-out must quote the power scheme that the launcher logs. Values 1 and 2 run only if value 3 helps.

### 4. S4 #19 (R1 stage 2, `d3d12_async_submit`): `build/agent7/s4-r1s2/`. Staged; rate request written.

- Done: `NOTE.md` (design), `s4-r1s2.diff` (+320/-1 over 5 SDK files, sha256 `06B0D371...`), `SHA256SUMS.txt`,
  `PROOFS.txt` (P1-P10 PASS), `CHECKS.txt` (`git apply --check`), `FUNCTIONAL-ROWS.md` + `queue-s4r1s2.jsonl` (9 rows,
  about 41 min, first draft), `SOAK.md` (first draft), `matrix-w7-draft.json` (Agent 8 owns the final). Index:
  `README.md`.
- `RATE-REQUEST.md` (task #32, Nov 23): the rate request for Agent 10, b2r style, citing the diff by its sha256.
  Agent 10 rates it after the break; no rating was requested before. Rev 1 fixes an independent read's 3 errors,
  2 gaps and 8 nits.
- Base: the S4b SDK in snap1 (command_processor.cpp = P2c + r1r2).
- Apply: `CHECKS.txt` L22-23's `git -C <sdk root> apply` form skips all 5 files on snap1 and exits 0 (git uses the
  parent repo; `CHECKS.txt` L24 now says so). Copy `new/sdk/` or use the `--directory` form in `RATE-REQUEST.md` §2.
- Open: `<N>` (the #18 split size) waits for Agent 3's ready-N gate; a `clang -fsyntax-only` check once compiles are
  allowed; re-check the rows and the soak, and write the soak's counter-line checker; `queue-s4r1s2.jsonl` row e's
  note still says "tile-mapping flushes" (not owned by task #33; `RATE-REQUEST.md` §15).
- Corrected 11-23 09:04 (task #33): RATE-REQUEST.md rev 1's corrections are now in `FUNCTIONAL-ROWS.md` (row e),
  `SOAK.md` (the soak bullet) and `NOTE.md` (presenter, RetireOnDemandMemexport, S2-2, S2-4); `CHECKS.txt` L24
  warns about the apply form; `matrix-w7-draft.json`'s two cites are fixed.
- Corrected 11-23 09:39 (task #33): the task #33 read found that presenter paint runs on GPU Commands in the default
  paint mode (not only on the UI thread) and a second early return of the refresher; fixing them turned up a second
  harmless exception (a blank paint when the guest output turns inactive). All are fixed in `RATE-REQUEST.md` (§6, §9,
  §11.1) and `NOTE.md`. Row e's query drains also cite cp.cpp:6055, and the `CHECKS.txt` L24 warning is scoped to
  snap1.
- Corrected 11-23 09:59 (task #33), after a re-read of the 09:39 edits: the 09:39 item's attribution (above);
  `RATE-REQUEST.md` §6's paint row (d3d12_presenter.cpp:1173-1202) and "Presenter" cites; `NOTE.md`'s 09:04 note,
  restored as written; `CHECKS.txt` L24's tags, one per time. List: `RATE-REQUEST.md` §15.

### 5. Older items, closed

- `s4-r1r2/`: #18 (R1 stage 1) + #20 step 1, rated SAFE (b2r row 32, §31), part of S4b.
- `s4b-queue/`: the S4b functional-run queue for Agent 3.
- `prof/`, `tail/`, `n-rows/`, `batch1/`, `batch1-perfcsv/`, `b2-*`, `stage-b2*`, `syntax-b2-*`, `tests-*`, `bench/`,
  `unit/`, `obj/`, `sd/`, `native3-check-test/`, `orig/` and the top-level logs: earlier evidence and scratch. No
  open items.

## Open items after the break

1. S4-T1: compile, then F1 → W1 → W8b under Agent 10's 5 conditions (section 3).
2. #19: Agent 10 rates `s4-r1s2/RATE-REQUEST.md`; run the syntax check; get `<N>`; then the build, the rows, the soak
   and W7 (its §13-§15).
3. W9 follow-up window, if wanted: off / q500 / q750 / q1000, with the round-1 order rotated (`readout/W9.md`).
4. Window hygiene from W5b (`readout/W5b.md` §7): a per-run quiet check, 1 s top-process logging, flag or re-run runs
   with ng_t ≥ 2.8, rotate the round-1 order.
5. Optional: a controlled-load d11t vs d11p test (`readout/W5b.md` §8).
6. The 0221-d11t-r5 stutter cluster has no identified cause (`readout/cluster-0221.txt`). In the cluster, all frames
   over 8 ms had buffer_queue_depth 7-8, and the window's only gpu.csv sample under 90 % util (58 %, at T 32.57 s)
   falls at the cluster's start (T 32.6-33.5 s). The
   1 s sys.csv sample that ends 0.3 s after it shows host CPU 69 % and E-core util 72 % (window medians 46 % and 38 %).
   There were no texture or pipeline misses.
