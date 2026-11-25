# MP2 / MP3 proof scripts (#21 S4-T1 threaded proofs, E7.1 for M7, session 3)

Offline, read-only, stdlib-only checkers for the two proofs that were still missing in
`build/agent7/s4-t1/THREADED-PROOFS-TODO.md`:

| file | proof | row | exit |
|---|---|---|---|
| `mp2_same_frames.py` | MP2 "same frames (proxy)" | F1 | 0 PASS / 1 FAIL / 2 INCOMPLETE |
| `mp3_query_seq.py` | MP3 "queries/readbacks complete before the guest reads them" | F3 (`LEGO_NATIVE_QUERY_TRACE_FROM=0`) | same |
| `test_mp.py` | synthetic selftest (25 tests) -> `selftest.out.txt` | | |
| `run_bn.ps1` | helper: runs `python -B ...` at Below Normal, writes output + exit code (made the `offline-*.out.txt`) | | |

Both scripts lower their own priority to Below Normal (`--normal-priority` turns that off), use one thread, and
never start the game or a build. Run them from the workspace root with `python -B`.

## Usage

```
# F1 matrix out dir (runs/<HHMM>-<arm>-r<k>), ref arm n0, candidates th3 and th3cp3 (add th2,th2cp3 if wanted)
python -B build/agent7/session3/mp/mp2_same_frames.py --dir <F1 out dir> [--arms th3,th3cp3] [--json OUT]
# explicit run dirs
python -B build/agent7/session3/mp/mp2_same_frames.py --ref <n0-r1> --ref <n0-r2> --cand <run> [--cand ...]
#   options: --ls-pad ABS  --dc-pad REL  --spread-k K  --perf-fallback incomplete|whole  --zero-dc incomplete|info
#            --light-ms MS  --min-level  --gate-level  --allow-new RE  --allow-gone RE  --no-logdiff  --logdiff PATH

# F3 matrix out dir, ref arm n0q, default comparisons th3q:n0q and th3cp3q:th3q
python -B build/agent7/session3/mp/mp3_query_seq.py --dir <F3 out dir> [--comp CAND:AGAINST ...] [--json OUT]
python -B build/agent7/session3/mp/mp3_query_seq.py --ref <n0q-r1> --ref <n0q-r2> --cand <run> [--cand ...]
#   options: --ref-arm  --noise-arm  --tol (default 0.05)
```

In PowerShell quote comma lists (`--arms 'th3,th3cp3'`), otherwise PowerShell turns them into an array.

## MP2 pass rules (row F1)

Source: FUNCTIONAL-ROWS.md F1 rule 5 (L119-121: "light share of th3 and th3cp3 inside n0's run-to-run range, perf.csv
`draw_calls` distribution in the window (median, p10, p90) inside n0-r1 vs n0-r2's spread"), must-prove map row 2
(L192: "proxy: perf.csv draws distribution, light share, logdiff; n0 x2 (n0-r1 vs r2 = noise); non-SAT, non-slow
runs only"), THREADED-PROOFS-TODO.md row MP2.

Per run:
- **light share** = `frames.json` `share_lt_light` (share of window frames < 4.5 ms; same number as results.csv
  `light_share` and `build/agent7/w4b-noise/noise_methods.py` `ls_T`). Fallback: computed from perf.csv
  `frame_time_us` over the frames.json window.
- **draw_calls** = perf.csv column `draw_calls`, rows `[first_row, first_row+rows)` of the frames.json window,
  rows with `frame_time_us > 0`; p10/p50/p90 nearest rank (`sorted[ceil(p*n)-1]`, the runner's method). Only when
  frames.json `source == "perf"` (all F1 arms are `frames: perf`); else `--perf-fallback` (default INCOMPLETE).
- **game log** = `game.N.log ... game.log`, parsed with `build/agent10/bgate/logdiff.py` `read()`/`norm()`
  (embedded copy if missing).

Checks per candidate run (band = min..max over all ref-arm runs; the F1 matrix has n0 x2, so = n0-r1 vs n0-r2):

| id | rule | default threshold | source |
|---|---|---|---|
| LS | light share in [min, max] of refs | `--ls-pad 0`, `--spread-k 0` (literal) | L119 |
| DC | p10, p50, p90 each in [min*(1-pad), max*(1+pad)] | `--dc-pad 0`, `--spread-k 0` (literal) | L119-121 |
| DC0 | all ref draw_calls 0 -> proxy vacuous -> INCOMPLETE | `--zero-dc incomplete` | my rule (finding below) |
| LOG NEW | key >= warning in cand, in no ref, not `--allow-new` -> FAIL | gate warning | logdiff.py NEW |
| LOG GONE | key in every ref, missing in cand, not noise -> FAIL | | logdiff.py GONE |
| LOG MORE | cand count > ref max + max(5, ref max), not noise -> FAIL | | logdiff.py MORE rule |
| LOG markers | fail markers above ref max; clean-exit line missing while every ref has it -> FAIL | | logdiff.py MARKERS |
| INCOMPLETE | < 2 ref runs, missing run dir / perf window / log, no candidate run | | |

Noise for LOG = key varies between the first two ref logs (present in one only, or max > min + max(5, min)).
Keys between `--min-level info` and the gate level are listed, not gated (threaded mode logs its own mode lines).
`--spread-k K` widens every band by K x the refs' own spread; an out-of-band value always prints
"outside by X = Y x the ref spread".

## MP3 pass rules (row F3)

Source: FUNCTIONAL-ROWS.md F3 (L131-151; L147 UNCLEAR, L148 unsupported, L149-150 comparisons), matrix-s4t1-f3.json
notes, THREADED-PROOFS-TODO.md row MP3.

Trace line (`DimensionsRecomp/rexlego/src/gpu_native/queries.cpp:56-69`, logged from `GetQueryData` :195 only the
first time a fence-complete result is handed to the guest; cap 128 lines per FSR mode, 6 modes):
`Native query value frame=<n> fsr=<bool> size=<W>x<H> query=<8 hex> draws=<n> samples=<n>`.
Also counted: `Native GPU: unsupported query` (ERROR, queries.cpp:53), `query 0x.. invalidated by failed draw`
(WARNING), `created hardware occlusion query` (info).

Sequence = trace lines in log order; addresses renamed to first-appearance slot. Agreement of two runs =
`difflib.SequenceMatcher(autojunk=False).ratio()` on: `draws`, `visible` (draws, samples>0), `pairs`
(draws, samples), `order` (slot, draws). Info: line count, slots, zero-sample share, median frame lag.

| id | rule | default | source |
|---|---|---|---|
| Q1 | every run has >= 1 trace line, else INCOMPLETE (UNCLEAR) with the reason (no query created / created but no trace) | | L147 |
| Q2 | 0 `unsupported query` lines, else FAIL | | L148 |
| Q3 | each cand run's mean agreement vs the AGAINST runs >= noise - tol, per metric; noise = first two runs of `--noise-arm` (default ref arm n0q) | `--tol 0.05` (my choice) | L149-150 |
| Q4 | failed-draw invalidations <= max(2 x ref max, ref max + 4), else FAIL | | check_n_rows.py warning-type rule |

`--dir` comparisons: `th3q:n0q`, `th3cp3q:th3q` (noise for both from n0q-r1 vs n0q-r2). Rule 4 of F3
(check_n_rows) stays with `bench/agent4/check_n_rows.py`.

## Arm / run dirs read

- F1 (`matrix-s4t1-f1.json`): ref `n0` x2; candidates `th3`, `th3cp3` (default), optional `th2`, `th2cp3`; `th3old`
  is not an MP2 candidate. Files: `runs/<HHMM>-<arm>-r<k>/{frames.json, perf.csv, game*.log}`.
- F3 (`matrix-s4t1-f3.json`): `n0q` x2 (ref + noise), `th3q`, `th3cp3q`. Files: `runs/<HHMM>-<arm>-r<k>/game*.log`.

## Selftest

`python -B test_mp.py -v` -> `selftest.out.txt`: **25 tests, OK** (MP2 14, MP3 11). Each tool has PASS, FAIL and
INCOMPLETE cases, JSON output, explicit and `--dir` modes; MP3 regex checked against the source format string;
rotated logs; address renaming; embedded logdiff == logdiff.py; literal-band tightness; zero draw_calls.

## Offline runs on real data (no new runs)

| file | data | result |
|---|---|---|
| `offline-mp2-s0-vs-s0.out.txt` | agent8/matrix/20261123-0313 (devoff4b, frames=perf) s0-r1,r2 ref vs s0-r3,r4,r5 | FAIL (exit 1): s0-r3 LS 0.9636 vs band [0.9637, 0.9746], 0.01x the ref spread outside. Same config -> spurious literal-band FAIL. DC 226/226/226 all PASS, LOG all PASS |
| `offline-mp2-s0-vs-s0-k1.out.txt` (+ `.json`) | same, `--spread-k 1` | PASS (exit 0) |
| `offline-mp2-0313-dir.out.txt` (+ `.json`) | 0313 `--dir --ref-arm s0 --arms p2,p2f,p2fc` | FAIL (exit 1): 7 LS FAILs (p2 r4,r5 slower; p2fc r1-r5 all faster: 0.9747-0.9815 vs ≤0.9746). DC + LOG PASS for all 15. Shows that LS also moves with speed |
| `offline-mp2-rpm4-n0-vs-n3.out.txt` (+ `.json`) | agent3/runs/rpm4-20261123-0620 (native4-era, native source) n0old-r1 + n0-r1 ref vs n3-r1, n2-r1; `--perf-fallback whole --zero-dc info` | FAIL (exit 1): n3 LOG GONE `Native GPU: unrecognized pixel/vertex shader resource` (8/8 in refs, 0 in n3); n2 LS 0.0008 < 0.0016. perf.csv draw_calls 0 everywhere |
| `offline-mp2-0013-n0-vs-n0-whole.out.txt` | agent8/matrix/20261122-0013 (native2) n0-r1,r2 vs n0-r3,r4, `--perf-fallback whole` | FAIL+INCOMPLETE: DC vacuous (all 0); whole-file LS (includes loading) differs 6-8x the spread -> whole-file LS is meaningless, use only frames=perf windows |
| `offline-mp2-0013-n0-native.out.txt` | 0013 `--dir --ref-arm n0 --arms d0` (native vs xenos route = clearly different) | FAIL (exit 1): LOG GONE 5 native-GPU warning keys in every d0 run; refs INCOMPLETE (native source, no perf window) |
| `offline-mp3-rpm4-title.out.txt` | rpm4 n0old/n0 ref vs n3 (title/attract) | INCOMPLETE (exit 2): 0 trace lines, 0 created queries in every run |
| `offline-mp3-level-routes.out.txt` (+ `.json`) | agent3/runs bgate-long-native3d + nativeB ref vs s4a-r5-off-native4 x2 (level routes, no QUERY_TRACE env) | INCOMPLETE (exit 2): 0 trace lines; 16 created queries and 16 `invalidated by failed draw` in 3 of 4 runs; Q2, Q4 PASS |

## Findings, assumptions, open questions

1. **perf.csv `draw_calls` is 0 on every frame on the native route** (native2 0013 n0, native4 s4a runs, rpm4 n0/n2/n3;
   native-frames.csv `draw_calls` is a constant 8 = presenter draws, FUNCTIONAL-ROWS L120-121). So MP2's DC proxy cannot
   tell anything apart on F1's arms: by default MP2 reports INCOMPLETE "DC proxy vacuous". Decide: accept MP2 = LS +
   logdiff (`--zero-dc info`), or find another per-frame content counter.
2. **The literal 2-run band fails equivalent runs.** Real data: s0-r3 failed by 0.0001 (0.01x the spread) against
   s0-r1/r2. With 2 refs, an exchangeable third run lands outside [min, max] with probability 1/3 per statistic.
   Defaults are kept literal (the written rule); I recommend `--spread-k 1` (or `--ls-pad`) for the rating, and
   reading "outside by Y x the ref spread".
3. **Light share is a timing quantity**: a mode that is faster or slower moves it (p2fc in 0313: all 5 runs above the
   band). For the "same frames" proxy LS should probably be info, or rated together with the speed-up; open for M7.
4. **F3 on the title/attract route will be UNCLEAR**: no title/attract run under build has any
   `created hardware occlusion query` line. Level routes create queries, but in the 3 level runs that do, every created
   query (16/16) was `invalidated by failed draw`, i.e. no result reached the guest, so even with
   `QUERY_TRACE_FROM=0` there may be no trace line. No real run anywhere has a `Native query value` line: the MP3 parser
   is validated only against the source format string (queries.cpp:56-69), not against a real log.
5. New log finding: rpm4 n3-r1 lacks the 8+8 `Native GPU: unrecognized pixel/vertex shader resource` warnings that both
   n0 runs have (one run only; could be logged elsewhere or deduped in threaded mode). MP2 flags it as GONE.
6. Assumptions: run dirs are named `runs/<HHMM>-<arm>-r<k>` (agent8/agent3 matrix runner); frames.json `window`
   `first_row`/`rows` index perf.csv data rows when `source == "perf"`; the band uses all ref-arm runs (F1 has n0 x2);
   MP3 noise for th3cp3q vs th3q comes from the n0q pair (`--noise-arm th3q` to use the th3q pair); `--tol 0.05` and
   pads are my choices, not from the docs; MP3 Q4 reuses check_n_rows' 2x / +4 rule.
7. Only 2 ref runs give a weak noise estimate for both tools; more n0 / n0q repeats would make the bands meaningful.
