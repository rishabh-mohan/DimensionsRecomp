# S4 #19 (R1 stage 2) 10-minute soak plan (Agent 7, FIRST DRAFT 23:35)

> S4-DRAFT row 19: "functional + a 10-min soak, then a timing A/B". Draft from the last minutes before tonight's
> windows. To add in the morning: a small tested checker for the counter lines (monotonic, per-frame rates).
>
> Corrected 11-23 09:04 (task #33): "What runs": queries drain at cp.cpp:4306-4308, not at the CheckSubmissionFence
> drain (the close takes that one), and no row shows the tile-mapping flushes (RATE-REQUEST.md §10.8).
>
> Corrected 11-23 09:39 (task #33): the soak bullet's query drains also cite cp.cpp:6055 (the EndQuery in
> DisableHostOcclusionQueries).

## What runs

- **Soak = queue row `s4r1s2-e`** ([queue-s4r1s2.jsonl](queue-s4r1s2.jsonl)): 600 s on the toypad level route
  `build\agent3\toypad\routes\level-l.txt` with `framerate_limit=0;d3d12_submit_split_kb=<N>;d3d12_async_submit=true`
  on `<DEVOFF4B-S4R1S2>`. Reference: s4bL0 (the same route and length on devoff4b-bin, `framerate_limit=0`).
  It covers a level load (the shared-memory tile-mapping flush, shared_memory.cpp:492, runs only if a new tiled range
  is mapped, and the counter line does not tell it apart from the drains; texture_cache.cpp:1255 needs resolution
  scaling, which no row sets), gameplay with queries (held_query; their EndSubmission calls at cp.cpp:6055 and :6111
  drain at cp.cpp:4306-4308) and a close at the end with splits possibly queued (ShutdownContext's
  AwaitAllQueueOperationsCompletion, cp.cpp:1971, takes the CheckSubmissionFence drain cp.cpp:4022-4026).
- **Queue pressure = row `s4r1s2-j`** (16 KB splits + async): the FIFO fills (full_waits > 0), queued_max stays <= 3.
- **Manual add-ons, only with a person at the desktop** (otherwise skip; the rows above are the soak):
  1. resize the window and minimize/restore it twice;
  2. alt-tab away for about 10 s and back (the runner sets `--pause_when_unfocused=false`, so rendering continues);
  3. at about 9 min, close the game with the window's close button during gameplay.

## Pass rules

1. No hang, TDR or .dmp; the process exits within close_timeout (60 s) and s4b_check.py finds no fail marker.
2. No new WARN or ERROR key vs s4bL0 (logdiff, `--allow-new 'd3d12_async_submit: '`); never
   `failed to create the submit thread`.
3. The `d3d12_async_submit:` counter lines (about every 10 s, cp.cpp:4581): frame, submission, chunks, full_waits,
   drains_waited and the three `_us` totals never decrease; queued_max <= 3; chunks > 0.
4. The `d3d12_submit_split:` counter lines (cp.cpp:4475): failed = 0; held_query > 0 at least once (queries ran).
5. Report per frame (Δ between the first and last counter line): chunks, submissions, drains_waited, drain_wait_us,
   full_wait_us and worker_us. These feed W7's read-out (how much of the moved work the drains give back).
6. Validity: the sys.csv slow state as in FUNCTIONAL-ROWS.md pass rule 4.

## Not covered

- Device removal: no safe way to cause it; NOTE.md's failure paths are a code read for Agent 10.
- Native builds: #19 is for the devoff (D3D12 command processor) path; the cvar note says to leave it off on native
  builds unless tested there (cp.cpp:121).
