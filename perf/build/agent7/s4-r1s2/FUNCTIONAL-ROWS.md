# S4 #19 (R1 stage 2, `d3d12_async_submit`) functional rows for Agent 3 (Agent 7, FIRST DRAFT 23:33)

> Draft written in the last minutes before tonight's windows. To re-check in the morning: the busy and slow-state
> commands per row, the row minutes, and whether Agent 3 wants the soak split from row e. SOAK.md is still to come.
>
> Corrected 11-23 09:04 (task #33): row e's "proves" cell (§2): queries drain at cp.cpp:4306-4308, not at the
> CheckSubmissionFence drain (cp.cpp:4022-4026), and no row shows the tile-mapping flushes (RATE-REQUEST.md §10.8).
>
> Corrected 11-23 09:39 (task #33): row e's query drains also cite cp.cpp:6055 (the EndQuery in
> DisableHostOcclusionQueries).

Bin under test: `<DEVOFF4B-S4R1S2>` = devoff4b + [s4-r1s2.diff](s4-r1s2.diff) (full SDK rebuild), suggested dir
`build/agent2/devoff4b-s4r1s2-bin`. Reference bin: `build/agent2/devoff4b-bin` (S4b without #19); its runs are Agent
3's S4b rows (s4b01, s4b10, s4b11, s4b13, s4b15, s4b25, s4bL0), so most rows need no new reference run.
Staging only: nothing here has run, and the bin is still to be built (Monday, after Agent 10's rating).
Line numbers are after-file numbers (`new/sdk/`), as in [NOTE.md](NOTE.md).

Queue rows: [queue-s4r1s2.jsonl](queue-s4r1s2.jsonl) (s4r1s2-a, -b, -i, -j, -c, -d, -f, -e, -g).

## 0. Before any row

1. Agent 2 applies the diff to the S4b SDK (snap1), builds at <= 2 threads, and stages the bin with MANIFEST.txt.
2. `bincheck.py` finds all 3 needles in the bin (the SDK's binary: legodimensions.exe or rexruntime.dll), and
   devoff4b-bin has none of them:
   - `d3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off` (cp.cpp:1944)
   - `d3d12_async_submit: submitting splits on the submit thread ({} slots)` (cp.cpp:1956)
   - `d3d12_async_submit: frame={} submission={} chunks={} queued_max={}` (prefix of the counter format, cp.cpp:4581)
3. Agent 3 creates `build\agent3\s4b\ready-s4r1s2`. Split rows also wait for `ready-N` (Agent 3's `<N>`); replace
   `<N>` as for s4b10.
4. Run only on an idle host: no window running, HOLD absent, hostload.csv clang++ = 0.

## 1. Pass rules for every row

1. Clean exit, no fail markers, no .dmp, no hang (s4b_check.py's run.json / fail-marker / exit checks).
2. Logs: compare with the named reference run using `python -B build/agent10/bgate/logdiff.py --min-level info --base
   <ref run> --cand <run>`, or `python -B build/agent3/s4b/s4b_check.py --cand <run> --base <ref run> --allow-new
   'd3d12_async_submit: ' --out-dir build\agent3\s4b\s4r1s2\checks`. Only the keys named in the row may be NEW; no new
   WARN or ERROR key.
3. #19 lines (game.log):
   - INIT `d3d12_async_submit: submitting splits on the submit thread (3 slots)`: exactly once when on with split > 0;
   - counter `d3d12_async_submit: frame= submission= chunks= queued_max= full_waits= full_wait_us= drains_waited=
     drain_wait_us= worker_us=` (about every 10 s): chunks rising, queued_max <= 3;
   - the #18 counter `d3d12_submit_split: ... splits= failed= ...`: failed = 0;
   - never `failed to create the submit thread`.
4. Validity, as for the S4b rows: busy < 0.97 where the row has frame stats, and the sys.csv slow state (E-core MHz
   < 800 for >= 3 rows) is absent or the row is read only up to the onset
   (`powershell -NoProfile -File bench/agent11/timerq_slowstate.ps1 -Root build\agent3\runs -Since <stamp>`).

## 2. Rows

| row | cvars on `<DEVOFF4B-S4R1S2>` | reference run (devoff4b-bin) | proves | min |
|---|---|---|---|---|
| a | none | s4b01 | OFF equivalence: logdiff NEW 0, MORE 0, GONE 0; no #18/#19 line | 4.4 |
| b | `d3d12_async_submit=true` (split 0), 90 s, no route | - | exactly 1 WARN (cp.cpp:1944); no INIT, no counter, no split line | 1.9 |
| i | `d3d12_submit_split_kb=<N>` | s4b10 | stage 1 unchanged by the #19 diff: NEW 0, GONE 0 (MORE only in split counter lines); failed 0 | 4.4 |
| j | split 16 + async | s4b11 | stress: queued_max <= 3, full_waits > 0 expected, failed 0, no hang | 4.4 |
| c | split `<N>` + async | s4b10 | ON identity: NEW = INIT + counter keys only; chunks > 0 | 4.4 |
| d | split `<N>` + async + `framerate_limit=0`, 180 s, StatsWarmup 20 | s4b25 | W7's s19 arm: proof lines, submissions and chunks per frame (functional only) | 3.4 |
| f | split `<N>` + `d3d12_readback_memexport=true` + async | s4b13 | the PublishOnDemandMemexport drain (cp.cpp:3266-3270): NEW = async keys only | 4.4 |
| e | `framerate_limit=0` + split `<N>` + async, level route, 600 s | s4bL0 | 10-min soak: level load (the shared-memory tile-mapping flush, shared_memory.cpp:492, runs only if a new tiled range is mapped, and the counter line does not tell it apart from the drains; texture_cache.cpp:1255 needs resolution scaling, which no row sets), queries (held_query > 0; their EndSubmission calls at cp.cpp:6055 and :6111 drain at cp.cpp:4306-4308), counters monotonic | 9.3 |
| g | `d3d12_debug=true` + split `<N>` + async (needs ready-dbg) | s4b15 | no new debug-layer message keys | 4.4 |

Total about 41 min of runs plus about 10 min of checks. Without `<N>` (a, b, j): about 11 min.

- **Submissions per frame (h):** from the counter lines of c, d and e: (Δsubmission / Δframe) and (Δchunks / Δframe)
  between consecutive lines. Expected K ≈ splits per frame + 1 (the OnPrimaryBufferEnd and swap submits stay
  synchronous, cp.cpp:2624-2636).
- **Drain cost:** drains_waited and drain_wait_us per frame (c, d, e). The OnPrimaryBufferEnd submit drains about once
  per frame, so drains_waited ≈ frames is expected; drain_wait_us per frame says how much of the moved work comes back.
- **Optional (k), cold pipeline cache:** if Agent 3 has a cold-cache recipe for devoff, one run of c with it shows
  held_pipelines > 0 and no new keys.
- **Shutdown with splits queued:** every row with async closes while splits may be queued; pass rule 1 plus no
  'D3D12 Submit' thread left (ShutdownAsyncSubmit joins it, cp.cpp:4646-4666).
- **Device loss:** no safe way to cause it on purpose; a code read for Agent 10 (NOTE.md, shutdown and failure paths).
