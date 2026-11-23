# S4-T1 (#21) functional rows for Agent 3 (Agent 7, task #17, 22:45)

Bin under test: `<NATIVE4B-S4T1>` = native4b + [s4-t1.diff](s4-t1.diff), suggested dir `build/agent2/native4b-s4t1-bin`.
Reference bin: `<NATIVE4B>` = `build/agent2/native4b-bin` (the same S4b sources without #21).
Staging only: nothing here has run, and both bins are still to be built (Monday, after Agent 10's rating).
Diff revision 2 (22:48) fixed review finding S1, the link closure for the gpu-aot fixtures. It moves no call site and
changes no role, log line or row below. Line numbers in the 3 changed files are after-file (revision 2) numbers, as in
RATE-REQUEST.md; before-file numbers are labelled "before" (converted at 23:27 after Agent 9's pre-read, P1). Files that
#21 does not touch have the same numbers in both.

Files:
- queue rows: [queue-s4t1.jsonl](queue-s4t1.jsonl) (s4t1-f1, s4t1-f3, s4t1-w1);
- matrices: [matrix-s4t1-f1.json](matrix-s4t1-f1.json), [matrix-s4t1-f3.json](matrix-s4t1-f3.json), [matrix-w8b-draft.json](matrix-w8b-draft.json);
- static check: [check_rows.py](check_rows.py) → [check_rows.out.txt](check_rows.out.txt), ALL CHECKS PASS (22:48, revision 2; re-run at 23:26 after the line-number edits).

## 0. Before any row

1. Agent 2 applies the diff (RATE-REQUEST.md §2), builds native4b+#21 at ≤ 2 threads, and stages it with MANIFEST.txt.
2. `bincheck.py` on the new `legodimensions.exe` finds all 3 needles, and native4b-bin has none of them:
   - `LEGO_NATIVE_CHAIN_PRIORITY`
   - `Native GPU: chain priority mode {}: {} (LEGO_NATIVE_CHAIN_PRIORITY={})`
   - `Native GPU: chain priority {} tid={} priority={}{} ecoqos={}`
3. Agent 3 creates `build\agent3\s4b\ready-s4t1`. Then copy the 3 matrices to `build\agent3\s4b\s4t1\` and replace the
   placeholders, as for g3q. The copy is listed in each row's `needs`. A bin dir without MANIFEST.txt makes run-matrix
   skip its arms, so the placeholder files cannot run by mistake.
4. Run only on an idle host: no window running, HOLD absent, hostload.csv clang++ = 0.

## 1. Threaded mode: th3 first, th2 as x1 arms

- **th3** (THREADED=1, PREPARE_THREADS=2, FULL_DRAW_PREPARATION=1) is W8b's mode.
  - The present runs on RecorderMain. Today that thread is NORMAL, and it is n3's busiest thread (55 %).
  - #21 raises the recorder, the coordinator and the 2 prepare threads.
  - The pre-onset tail is worse in n3t: 56.8 vs 23.0 frames > 33 ms per min, and swap 6.4 vs 1.6 ms.
  - Full draw preparation is also where MP4's risk sits.
- **th2** (THREADED=1, PREPARE_THREADS=2, SNAPSHOT_STATE=1) gets one run per arm, so the two remaining call sites get
  exercised:
  - the worker (already ABOVE_NORMAL, native_worker.cpp:390; before :349);
  - the RecordingQueue thread, which exists in th2 only (native_recording.cpp:530-533; check/MP4-STATIC.md L79, L122).
- The roles each mode must log come from the code:
  - th3: `coordinator`, `recorder`, `prepare` x2. There is no `worker` line, because WorkerMain hands off to
    CoordinatorMain at :263 before its hook. There is no `recording queue` line either.
  - th2: `worker`, `recording queue` (one per RecordingQueue instance, a weak_ptr singleton at
    native_recording.cpp:174-181), `prepare` x2. There is no `coordinator` and no `recorder` line.

## 2. Rows

Run-dir names: `$D\runs\<HHMM>-<arm>-r<k>`, where `$D` is the row's `-OutDir` (`build\agent3\runs\<id>-<stamp>`). The
snippets use this helper:

```powershell
function R($arm) { @(Get-ChildItem "$D\runs" -Directory | Where-Object Name -match "-$arm-r\d+$" | ForEach-Object FullName) }
```

### F1 = queue row s4t1-f1: unset equivalence, #21 ON identity, MP1, MP2 proxy, MP5a

10 full-length runs, about 26 min (planner 142 s per run, window-3 observed 158 s), plus about 5 min of checks:
**about 31 min**. Matrix args: `-NoCold`.

| arm | bin | env on top of n0 | x | proves |
|---|---|---|---|---|
| n0 (ref) | S4T1 | none | 2 | baseline; 0 `chain priority` lines with the variable unset |
| th3old | OLD | THREADED, PREPARE_THREADS=2, FULL_DRAW | 2 | the unset-equivalence reference |
| th3 | S4T1 | the same as th3old | 2 | the unset path is unchanged (vs th3old); MP1 |
| th3cp3 | S4T1 | th3 + CHAIN_PRIORITY=3 | 2 | ON identity; MP1/MP5a with #21 ON |
| th2 | S4T1 | THREADED, PREPARE_THREADS=2, SNAPSHOT_STATE | 1 | MP1 in th2, unset |
| th2cp3 | S4T1 | th2 + CHAIN_PRIORITY=3 | 1 | ON identity of the worker and recording-queue sites |

**Cold cache (Agent 9's pre-read, P2, 23:12):**
- Each bin dir keeps its own pipeline cache: `<exe dir>/cache/native-pso.bin`, `cache/native-pso-recipes.bin` and
  `<exe dir>/native-pso-seed.bin` (pipeline_library.cpp:99-105, :150-152). At 23:07 neither bin dir had one.
- With round-robin and `-NoCold`, n0 r1 (S4T1) and th3old r1 (OLD) start cold, while th3 r1 follows n0 r1 on the same
  bin and starts warm.
- So (b) is read on r2, where both bins are warm. The all-runs form is informational: if it shows MORE/GONE, look for
  cold-only line types (pipeline compiles) before blaming #21.
- Never copy `cache/` or a seed between bin dirs.

Checks, all read-only:

```powershell
# a) MP1: threaded rows vs n0 (exit 0 = pass)
python -B bench/agent4/check_n_rows.py --baseline (R n0) --rows ((R th3)+(R th3cp3)+(R th3old) | % {"n3=$_"}) ((R th2)+(R th2cp3) | % {"n2=$_"}) --json "$D\check_n_rows.json"
# b) unset equivalence at INFO level: NEW 0, MORE 0, GONE 0, read on r2 (both bins warm; cold-cache note above)
python -B build/agent10/bgate/logdiff.py --min-level info --base "$D\runs\*-th3old-r2*" --cand "$D\runs\*-th3-r2*"
#    informational, all runs (r1 is cold on OLD and warm on S4T1):
python -B build/agent10/bgate/logdiff.py --min-level info --base "$D\runs\*-th3old-r*" --cand "$D\runs\*-th3-r*"
# c) ON adds only the #21 lines: NEW = 'Native GPU: chain priority ...' keys only, MORE 0, GONE 0
python -B build/agent10/bgate/logdiff.py --min-level info --base "$D\runs\*-th3-r*" --cand "$D\runs\*-th3cp3-r*"
python -B build/agent10/bgate/logdiff.py --min-level info --base "$D\runs\*-th2-r*" --cand "$D\runs\*-th2cp3-r*"
# d) the #21 lines per run
Get-ChildItem "$D\runs" -Directory | % { $m = @(Select-String -Path "$($_.FullName)\game*.log" -Pattern 'Native GPU: chain priority'); "{0}: {1}" -f $_.Name, $m.Count; $m | % { '   ' + ($_.Line -replace '^.*Native GPU: ', '') } }
# e) per run: run.json, fail markers, clean exit, threads, sys.csv slow state (one call per run; allow the #21 lines)
foreach ($c in (R th3cp3)+(R th2cp3)) { python -B build/agent3/s4b/s4b_check.py --cand $c --base (R th3)[0] --allow-new 'Native GPU: chain priority' --out-dir build\agent3\s4b\s4t1\checks }
# f) busy and the slow state
python -B bench/agent7/w4b_readout/w4b_readout.py $D --all -o "$D\readout.md" --json "$D\readout.json"
python -B bench/agent8/run/matrix_recheck.py $D --all --drop-slow --slow-emhz 800 --slow-rows 3
powershell -NoProfile -File bench/agent11/timerq_slowstate.ps1 -Root build\agent3\runs -Since <stamp>
# g) MP2 proxy: light share and the raw GM delta, guards only (never a timing verdict)
python -B build/agent7/w4b-noise/readout.py $D
```

For e), take the th2cp3 run's base from `(R th2)` instead.

PASS if all of these hold:
1. check_n_rows exits 0 for every threaded run. That covers THREADED ON once, the n2/n3 mode lines and threads, the
   env, no new warning type (hash=0 included) and a clean close.
2. **Unset equivalence:** th3 vs th3old gives NEW 0 at info level. MORE and GONE are 0, or are explained as noise
   because the same key also varies between th3old-r1 and th3old-r2. n0, th3, th2 and th3old show **0** `chain
   priority` lines.
3. **ON identity:**
   - every cp run has exactly one `chain priority mode 3: priority + EcoQoS opt-out (LEGO_NATIVE_CHAIN_PRIORITY=3)`
     line;
   - th3cp3's thread lines are exactly `coordinator` x1, `recorder` x1 and `prepare` x2;
   - th2cp3's thread lines are `worker` x1, `recording queue` x ≥ 1 and `prepare` x2;
   - every thread line reads `priority=1 ecoqos=opt-out`, with no `(set failed)` and no `opt-out failed`;
   - a run has at most 16 thread lines;
   - in c), the only NEW keys are those lines.
4. **Clean close in every run:** exit 0, no .dmp, close < 60 s, no STUCK-LOCK, and s4b_check's fail markers no higher
   than the base.
5. **MP2 proxy:** the light share of th3 and th3cp3 is inside n0's run-to-run range, and their perf.csv `draw_calls`
   distribution in the window (median, p10, p90) is inside n0-r1 vs n0-r2's spread. native-frames.csv `draw_calls`
   counts only the presenter's 8 draws, so it cannot show this. I compute these numbers from F1's run dirs on Monday.
6. **busy and slow state:** record each run's busiest-thread busy (headroom.json, w4b_readout's busy/SAT column). The
   row's function verdict holds at any busy value. But no remark about priority effects or tails may come from a run
   with busy ≥ 0.97, or from a run in the slow state (sys.csv E-core MHz < 800 for ≥ 3 rows; matrix_recheck
   --drop-slow, timerq_slowstate). If more than half of an arm's runs are SAT or slow, re-run F1 on an idle host.

Optional, at no extra run time: during one th3cp3 window, take
`(Get-Process legodimensions).Threads | Group-Object BasePriority | Select Name,Count`. It should show at least 3 more
threads at priority 9 than the same snapshot in th3.

### F3 = queue row s4t1-f3: MP3 query outcomes

5 Quick runs: n0q x2 (ref), th3q x2 and th3cp3q x1, all with `LEGO_NATIVE_QUERY_TRACE_FROM=0`. That is about 7-12 min
(Quick is about 84 s per run observed; Agent 3's g3q basis is 150 s), plus about 3 min of checks: **about 10-15 min**.
Matrix args: `-Quick -NoCold`.

The trace (queries.cpp:56-69, read once) logs `Native query value frame= fsr= size= query= draws= samples=` at INFO
for frames ≥ FROM, at most 128 lines per FSR mode. These are the guest-visible results. The key is functional only, so
it is not on the F1 night list.

```powershell
foreach ($d in Get-ChildItem "$D\runs" -Directory) { $q = @(Select-String -Path "$($d.FullName)\game*.log" -Pattern 'Native query value'); $u = @(Select-String -Path "$($d.FullName)\game*.log" -Pattern 'unsupported query'); "{0}: query lines {1}, unsupported {2}" -f $d.Name, $q.Count, $u.Count }
python -B bench/agent4/check_n_rows.py --baseline (R n0q) --rows ((R th3q)+(R th3cp3q) | % {"n3=$_"})
```

PASS if all of these hold:
- every run has query lines. If a run has none, the row is UNCLEAR: it needs a route that issues queries.
- 0 `unsupported query` error lines (queries.cpp:53).
- the per-frame (draws, samples) sequence of th3q agrees with n0q at least as well as n0q-r1 agrees with n0q-r2, and
  th3cp3q agrees with th3q the same way. I compare the sequences on Monday.
- check_n_rows passes.

GPU→CPU readbacks other than queries are a code-read item for Agent 10 (RATE-REQUEST.md §9).

### MP4: static proof plus F1 cover (0 run minutes)

[check/MP4-STATIC.md](check/MP4-STATIC.md) (read-only checker, 22:37):
- **PROVEN statically:** no NativePreparationQueue job can reach CaptureShaderBindings in n0, th2 or th3.
- The b2r wording "only on the single capture worker" needs restating:
  - in th2 an inline drainer, typically a guest thread holding the recording gate, can run a capture task;
  - in th3 with FSR3 on, RecorderMain runs :5190/:5217.
  - Its suggested wording is in L21-24.
- #21 changes no call graph. It only sets thread attributes, so it can change interleavings but not which thread runs
  a capture.
- F1's th3/th3cp3 runs exercise the full-preparation paths.
- An optional counter diagnostic (t_on_prepare, MP4-STATIC L138-149) would be its own diff and its own rating. It is
  not part of #21.

### MP5: shutdown (F1) and device loss (code read)

- **MP5a, shutdown while work is queued:** every F1 run closes at the end of its window while the threaded queues are
  live. This is pass rule 4, plus `StopNativeWorker` joining the worker (:637) and the recorder (:638) and
  `StopNativePreparation` running with FullDraw on (:639).
- **MP5b, device loss:** there is no safe way to remove the device on purpose: no TDR tool and no test hook. It becomes
  a code read for Agent 10:
  - the only device-removed handling in gpu_native is pipeline_library.cpp:445;
  - #21 adds no device call, so it cannot change this path.

### W1 = queue row s4t1-w1: W8b pre-flight

- First `run-matrix.ps1 -PlanOnly` on Agent 8's final copy (about 1 min).
- Then 3 Quick runs (`-Quick -NoCold -Repeats 1`), about 4-8 min, plus 2 min of checks: **about 7-10 min**.
- PASS: every arm boots, writes perf.csv, native-frames.csv, sys.csv and headroom.json, and closes cleanly. th3cp
  shows the mode-3 line.
- This is not timing.

## 3. Must-prove map (b2r §15.4, perf-notes/agent10-batch2-review.md L725-730)

| # | must prove | row | mode and why | reference arm | busy / sys.csv | minutes |
|---|---|---|---|---|---|---|
| 1 | hash0 ≈ 0 in n2/n3, draws/frame and marks = n0, no new warning type | F1 (check_n_rows) | th3 (W8b) + th2 x1 (both n-rows) | n0 x2, same bin | busy recorded; function holds when SAT | in F1's 31 |
| 2 | same frames | F1 (proxy: perf.csv draws distribution, light share, logdiff) | th3, the full-preparation path | n0 x2 (n0-r1 vs r2 = noise) | non-SAT, non-slow runs only | in F1's 31 |
| 3 | queries and readbacks complete before the guest reads them | F3 + code read | th3: the present and queries follow the recorder chain | n0q x2 | function only | 10-15 |
| 4 | CaptureShaderBindings never on PREPARE_THREADS workers | static proof + F1 | th2 and th3 (both proven) | - | - | 0 |
| 5 | shutdown / device loss with work queued | F1 closes (a); code read (b) | th3 + th2 | n0 closes | - | 0 extra |
| #21 | unset = old bin; ON lines and roles | F1 | th3 + th2 | th3old (old bin), th3 | - | in F1's 31 |
| W8b | pre-flight | W1 | th3 | n0 | - | 7-10 |

Total about 50-55 min of queue time (F1 31, F3 10-15, W1 7-10). F1 is first, and it alone carries the unset proof
needed before W8b.
