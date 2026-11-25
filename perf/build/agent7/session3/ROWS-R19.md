# ROWS-R19.md: #19 (R1 stage 2, `d3d12_async_submit`) rows package for the morning (M7, S3T-7 A, 2026-11-25)

Paper only: nothing here ran on the #19 bin, which doesn't exist yet. The rows are in
[queue-r19.jsonl](queue-r19.jsonl). M3 appends them to `build\agent3\s4b\queue.jsonl` only when the Overseer says so.
Rating: `build/agent10/session3/r19-rating.md` (296658C5). Source rows: `build/agent7/s4-r1s2/FUNCTIONAL-ROWS.md`
and `SOAK.md`. Formats: M3's `queue-s3.jsonl` and `s4b/queue.jsonl`.

> [!IMPORTANT]
> **Bin placeholder.** `build\agent2\devoff4b-r19-bin` is a placeholder for M2's #19 build: devoff4b +
> `s4-r1s2.diff` 06B0D371, a full SDK rebuild at ≤ 2 threads. If M2 stages it under another name, change only the
> 9 `-BinDir` values of the `r19a`..`r19e` lines, then rerun `check_queue_r19.py` (Q3 checks the name; set `BIN19`
> to the same value).

## 0. Before any row

1. **Bin.** M2 applies #19 to the devoff4b SDK as r19-rating (a) says: syntax check and before-hash check first,
   then copy `new/sdk/` (or `git -c core.autocrlf=false apply`). M2 stages the bin with MANIFEST.txt. `bincheck.py`
   must find these 3 needles in the bin, and none of them in `devoff4b-bin`:
   - `d3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off` (cp.cpp:1944)
   - `d3d12_async_submit: submitting splits on the submit thread ({} slots)` (cp.cpp:1956)
   - `d3d12_async_submit: frame={} submission={} chunks={} queued_max={}` (prefix of cp.cpp:4581)

   Then M3 writes `build\agent3\s4b\ready-r19`.
2. **N** (r19-rating (b) 6: `<N>` comes only from `build\agent3\s4b\ready-N`, which the Overseer authorizes):
   - Tonight's `s4bN16` (title scene at 16 KB, `20261125-014239-s4b-N16-title-split16`) printed the #18 init line
     but **0 `d3d12_submit_split:` lines**. That's correct behaviour: the counter line prints only while a split is
     due (cp.cpp:4466-4476), so no title submission ever reached 16 KB. `r19_gate --row i --n 16` on that run reports
     INCOMPLETE "no split line" ([offline-i-N16.out.txt](offline-i-N16.out.txt)).
   - `s4bN4` (4 KB, ~03:40) either gives split lines, so M3 derives N by READY-N.md option C, or it also prints
     0 lines. Then **fallback A applies: N = 64**.
   - **What fallback A means for these rows** (my reading; the Overseer decides):
     - Row d (title) will have **no** async counter line. The async counter also prints only from
       `EndSubmissionAsync`, that is, only when a split happens (cp.cpp:4566-4580). So r19_gate gives row d
       INCOMPLETE "no split was due at this N", and the W7 s19 arm would be a no-op as well (READY-N.md section 3).
     - If even 4 KB never splits on the title, the natural lists are very small (K is large). Then the M-route rows
       i, c, f, g and the soak e may split only on the heavy frames, or never.
     - **Early warning, no extra cost:** the reference row `r19r10` runs on the old bin before any #19 row. If its
       s4b_check shows `splits > 0` FAIL or no split line at N, rows i, c, f and g will be INCOMPLETE too. Ask the
       Overseer before spending them. Row j (16 KB, M route) still makes sense if `r19r11` splits.
3. **Markers** (all written by M3, each only on the stated word):

| marker | meaning | written when |
|---|---|---|
| `build\agent3\s4b\ready-r19` | #19 bin staged + bincheck PASS | after step 1 |
| `build\agent3\s4b\ready-N` | N on line 1 | Overseer's word (READY-N.md section 5) |
| `build\agent3\s4b\ready-s4b-off`, `ready-dbg` | existing S4b markers | exist |
| `build\agent3\session3\go-quiet` | quiet host: no build, no other game, nobody gaming | exists; ON rows can reset the shared GPU on a fault (rating (b) 3) |
| `build\agent3\session3\go-r19on` | the Overseer's **RUN GO for #19 ON rows** | only after `r19-ok-i` (rating (b) 1: a, b, i pass before any ON row) |
| `build\agent3\session3\r19-ok-<row>` | row passed its gate (section 2) | only when every gate command of the row exits 0 |

The `r19-ok` chain makes the queue itself enforce **M10's order a, b, i, c, g, j, d, f, e** and
**"stop at the first FAIL"**: each #19 row needs the previous row's ok marker. After a FAIL, INCOMPLETE or FLAG,
no marker is written until the Overseer decides, and later rows wait (s4b-queue passes over waiting rows; it
doesn't drop them). Reference rows need no chain marker and run first.

## 1. The rows (file order = launch order)

| id | bin | cvars | needs (beyond ready-* + go-quiet) | s4b_check `--row` / base | min |
|---|---|---|---|---|---|
| r19r11 | devoff4b | split 16 | - | s4b11 / s4b01, allow-new `d3d12_submit_split` | 4.4 |
| r19r10 | devoff4b | split N | ready-N | s4b10 / s4b01, allow-new `d3d12_submit_split` | 4.4 |
| r19r13 | devoff4b | split N + readback_memexport | ready-N | s4b13 / s4b01, allow-new `d3d12_submit_split` | 4.4 |
| r19r15 | devoff4b | debug + split N | ready-N, ready-dbg | s4b15 / s4b01, allow-new `d3d12_submit_split` | 4.4 |
| r19r25 | devoff4b | split N + fps uncapped, 180 s, warmup 20, title | ready-N | s4b25 / s4bN16 run | 3.4 |
| **r19a** | #19 | none | - | s4b01 / s4b01 | 4.4 |
| **r19b** | #19 | async (split 0), 90 s, no route | r19-ok-a | (none) / s4b01, allow-new `d3d12_async_submit: needs` | 1.9 |
| **r19i** | #19 | split N | ready-N, r19-ok-b | s4b10 / r19r10 | 4.4 |
| **r19c** | #19 | split N + async | ready-N, go-r19on, r19-ok-i | s4b10 / r19r10, allow-new `d3d12_async_submit: ` | 4.4 |
| **r19g** | #19 | debug + split N + async | ready-N, ready-dbg, go-r19on, r19-ok-c | s4b15 / r19r15, allow-new `d3d12_async_submit: ` | 4.4 |
| **r19j** | #19 | split 16 + async | go-r19on, r19-ok-g | s4b11 / r19r11, allow-new `d3d12_async_submit: ` | 4.4 |
| **r19d** | #19 | split N + async + fps uncapped, 180 s, warmup 20, title | ready-N, go-r19on, r19-ok-j | s4b25 / r19r25, allow-new `d3d12_async_submit: ` | 3.4 |
| **r19f** | #19 | split N + readback_memexport + async | ready-N, go-r19on, r19-ok-d | s4b13 / r19r13, allow-new `d3d12_async_submit: ` | 4.4 |
| **r19e** | #19 | fps uncapped + split N + async, level route, 600 s, toypad | ready-N, go-r19on, r19-ok-f | (none) / s4bL0, allow-new `d3d12_(async_submit\|submit_split)` | 9.3 |

Run time: refs ~21 min; #19 rows ~41 min; checks ~10 min.

- Other routes: the 420 s rows use `harness\routes\b-gate-menus-long.txt`; row e uses
  `build\agent3\toypad\routes\level-l.txt`.
- **Why the refs exist.** S4b rows 10, 11, 13, 15 and 25 were commented out of `queue.jsonl` and never ran (only
  s4b01 and s4bL0 exist under `build\agent3\runs`), so rows i, c, g, j, d and f had no base. If M3 runs one of
  those S4b rows first, drop that `r19r*` line and use the S4b run.
- **"Then soak":** row e is the soak (SOAK.md). Its pass rules are soak_check's rules 3-5 (section 3). SOAK.md's
  manual add-ons (resize, alt-tab, window close) need a person at the desktop, so they are skipped on the hidden
  desktop. W7 timing isn't in this package: it runs only after a..e PASS, and only by the user's double-click
  (rating (b) 2 and 6).

## 2. Gate per row (what M3/M12 run after each row; all at Below Normal, from WS)

Run 1. `s4b_check` (clean exit, fail markers, .dmp, hang, logdiff vs base):
```
python -B build\agent3\s4b\s4b_check.py --cand build\agent3\runs\<run> [--row <s4b row from the table>] --base build\agent3\runs\<base run> [--allow-new "<regex>"] --out-dir build\agent3\s4b\r19\checks
```
Run 2. `r19_gate` (the #18/#19 proof lines; it imports soak_check.py unchanged):
```
python -B build\agent7\session3\r19_gate.py build\agent3\runs\<run> --row <a|b|i|c|g|j|d|f|e> [--n <N>] [--json build\agent3\s4b\r19\checks\<id>.r19.json]
```
(`--n` is the ready-N value; for row j use `--n 16`.)

Run 3. Validity, ON rows: `powershell -NoProfile -File bench/agent11/timerq_slowstate.ps1 -Root build\agent3\runs -Since <stamp>`.
The slow state (E-core MHz < 800 for ≥ 3 rows) must be absent, or the row is read only up to its onset.
Busy < 0.97 where the row has frame stats.

**Verdict:**
- **PASS** = s4b_check has no FAIL, r19_gate exits 0 and the run is valid. M3 then writes `r19-ok-<row>`.
- r19_gate exit 1 FAIL / 2 INCOMPLETE / 3 FLAG: stop and report to the Overseer.
- **Any hang or timeout is a FAIL** (rating (b) 4): no exit within close_timeout 60 s, killed, hold-abort, or run.json
  not OK. Triage starts from the `GPU Commands` stack (DrainAsyncSubmissions, full-ring wait) and the
  `D3D12 Submit` thread, not from F-CA. STUCK-LOCK follows the finding-10 rule (f10_rule.py).

### Expected proof lines per row (r19_gate)

| row | must see in game.log | must NOT see | INCOMPLETE when |
|---|---|---|---|
| a | (nothing #18/#19) | any `d3d12_async_submit` / `d3d12_submit_split` line; logdiff NEW/MORE/GONE 0 at info | - |
| b | exactly 1 `[warning] ... d3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off` | any other async line; #18 init or counter (split = 0). Logdiff: NEW only that key; GONE not judged (90 s, no route) | - |
| i | #18 init `splitting submissions at <N> KB` ×1; `d3d12_submit_split:` lines with failed=0, monotonic, splits > 0 | any `d3d12_async_submit` line; logdiff NEW/GONE ≠ 0 (MORE only on split lines) | no split line (nothing reached N) |
| c, g, f | #18 init ×1 at N; `d3d12_async_submit: submitting splits on the submit thread (3 slots)` ×1; async counter lines (all 9 keys, monotonic, queued_max ≤ 3, chunks > 0 in the last); split lines failed=0; chunks/splits consistent (X2) | `staying off`, `failed to create the submit thread`; a 2nd init (second SetupContext); logdiff NEW beyond `d3d12_async_submit: ` | < 2 async counter lines (no split was due) |
| g extra | s4b_check s4b15: DRED line ≥ 1, no debug-layer enable failure | device removed / TDR / crash | - |
| j | as c, at 16 KB; full_waits > 0 in the last async line | as c | full_waits = 0 (the FIFO never filled: the stress claim is unproven, not a defect) |
| d | as c; reports submissions and chunks per frame (W7 s19 arm, functional only) | as c | no async counter line: the expected outcome under fallback A |
| e | as c, plus held_query > 0 in ≥ 1 split line (queries ran; SOAK.md rule 4); level reached (s4b_check / route marks) | as c; new WARN/ERROR vs s4bL0 | no split line at all |
| ON rows | - | `Shutdown wedged past the close request; hard-exiting.` → **FLAG** (exit 3), even if all else passes (rating (b) 4) | - |

Also check after every ON row: the process closed cleanly while splits may have been queued (ShutdownAsyncSubmit
joins the `D3D12 Submit` thread, cp.cpp:4646-4666). s4b_check's exit, close and kill checks cover that. No
leftover `D3D12 Submit` thread is visible in the log, so a hung close shows up as a timeout, which is a FAIL.

## 3. How soak_check.py is applied

`build/agent7/s4-r1s2/soak-check/soak_check.py` (CAB5CB2C, selftest 26/26, rated with #19) stays unchanged. It
implements SOAK.md rules 3-5 and has only `--row e|j`. r19_gate imports its `parse`, `log_files`, `monotonic` and
`check_events`, then sets which checks gate which row:

| soak_check check | a, b, i | c, g, f, d | j | e |
|---|---|---|---|---|
| A1 init once, no staying-off / create failure | not run (own OFF rules) | gates | gates | gates |
| A2 9 keys, monotonic | - | gates | gates | gates |
| A3 queued_max ≤ 3 | - | gates | gates | gates |
| A4 chunks > 0 / ≥ 2 counter lines | - | gates (0 lines → INCOMPLETE) | gates | gates |
| S1 split keys, failed = 0, monotonic | (r19_gate's own copy for i) | gates | gates | gates |
| S2 held_query > 0 | - | INFO only (menus may run no query) | INFO only | **gates** (no split line → INCOMPLETE) |
| X1, X2 | - | gate | gate | gate |
| J1 full_waits > 0 | - | - | INCOMPLETE if false | - |
| rule-5 per-frame report | - | printed | printed | printed (feeds W7) |

The direct form `python -B build/agent7/s4-r1s2/soak-check/soak_check.py <run> --row e` stays valid for row e:
r19_gate --row e gives the same verdict, plus the two init checks and the watchdog flag.

## 4. Combination guard (rating (b) 5 / S2)

No #19 row and no ref row may set `d3d12_pipeline_creation_no_wait` (#33 hunk 5), a `*resolution_scale*` cvar, a
`native_*` cvar or `-Env`, or use a CTR or native bin. `d3d12_async_submit` appears only on #19 rows. A combination
needs a new rating first. `check_queue_r19.py` Q7 enforces this.

## 5. Files and tests

| file | purpose |
|---|---|
| [queue-r19.jsonl](queue-r19.jsonl) | 5 ref + 9 #19 rows, M3's format (8 comment lines, then JSON lines) |
| [r19_gate.py](r19_gate.py) | per-row line gate, exit 0/1/2/3 |
| [check_queue_r19.py](check_queue_r19.py) | static check of the queue file (Q1-Q8) |
| [test_r19.py](test_r19.py) | selftest: 37 gate cases on synthetic logs + 13 queue cases (12 mutations) |
| [run-offline-r19.ps1](run-offline-r19.ps1) | runs all of the above at Below Normal |

Results (02:21, 11-25):
- `selftest-r19.out.txt`: SELFTEST PASS 50/50.
- `check_queue_r19.out.txt`: ALL CHECKS PASS (183 checks). Q1 also confirms that no id is in queue.jsonl or
  queue-state.jsonl.
- Offline on real runs (negative controls; none of them is a #19 run):

| run | row | result | why |
|---|---|---|---|
| s4b01 | a | PASS | an OFF run has no #18/#19 line |
| cg26b0 | a | PASS | an OFF run has no #18/#19 line |
| s4bN16 | a | FAIL | it has the #18 init |
| s4bN16 | i `--n 16` | INCOMPLETE | no split line |
| s4bN16 | d `--n 16` | FAIL + INCOMPLETE | no async init |
| s4bL0 | b | FAIL | no WARN |
| s4bL0 | e | FAIL | no init lines |

## 6. Open points for the Overseer

1. The bin name is a placeholder (see the top).
2. N: wait for s4bN4. Under fallback A, row d is a planned INCOMPLETE. Say in advance whether that counts as
   "pass, no-op", so the chain can go on to f and e (M3 then writes `r19-ok-d` on your word).
3. Should `r19r10` showing no split at N stop rows i, c, f, g before they run (my suggestion), or let them run
   and come back INCOMPLETE?
4. M3 owns the new markers (`go-r19on`, `r19-ok-*`) and the append. They are new names in M3's folder.
