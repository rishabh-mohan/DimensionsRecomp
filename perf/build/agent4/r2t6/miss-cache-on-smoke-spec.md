# Miss-cache ON smoke spec: native4, #2 (`LEGO_NATIVE_SHADER_MISS_CACHE`)

Agent 4, board run 2, task #6 item 2 (13:27), for Agent 3.

- **Sources:** b2r §18 (the tests and the expected ON output) and §15.2 items 1-8.
- **Patch:** `build/agent4/s34/shaders-s34.patch` (328BDAE1…); the patched shaders.cpp is 9567FE3F….
- **Functional only:** hidden desktop, never timed. The last launch is at 14:15.

## 1. Env

| Variable | OFF arm | ON arm |
|---|---|---|
| `LEGO_NATIVE_SHADER_MISS_CACHE` | unset | `1` (any non-empty value except `0`) |
| `LEGO_NATIVE_TRACE_DIR` | an absolute path to a new, empty dir | an absolute path to a new, empty dir |

- **Why the trace dir:** it is the only place where the ON-only output and the `unrecognized_shader` events show up.
  - The game creates the dir and appends to `events.tsv`, so each run needs a fresh dir.
  - Use an absolute path, because run-game.ps1 passes `-Env` values through unchanged.
- **Never set:**
  - `LEGO_DUMP_MISSING_SHADERS`: it forces the cache OFF;
  - `LEGO_NATIVE_NO_MEMORY_WATCH`: with no stamp, nothing is cached;
  - `LEGO_GPU_SNAPSHOT_DIR`: with a trace dir, anomalies would schedule snapshot captures;
  - the threaded env (`LEGO_NATIVE_THREADED`, `LEGO_NATIVE_PREPARE_THREADS`, `LEGO_NATIVE_FULL_DRAW_PREPARATION`): n0 is the default serial path.

  run-game.ps1 drops inherited `LEGO_*` variables anyway.
- **The trace dir is not neutral:**
  - it turns off buffer and texture reuse and some draw fast paths (buffers.cpp:438/579, textures.cpp:2564/2689, draw.cpp:4694/4880/5105);
  - it writes one `frame` row per frame.

  So never logdiff a trace run against a run without one.

## 2. Route

- **Bin:** native4 (Agent 2's folder) for both arms.
- **Settings:** n0, the n-row cvars, no input, `-Seconds 300`: boot → title → attract. The reference counts below come from this route.

```
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir <native4-bin> -Seconds 300 -Tag mc-off-t -Cvar "native_settings_frontend=false;native_fps_limit=0;framerate_limit=0" -Env "LEGO_NATIVE_TRACE_DIR=<abs>\mc-off-t"
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir <native4-bin> -Seconds 300 -Tag mc-on-t -Cvar "native_settings_frontend=false;native_fps_limit=0;framerate_limit=0" -Env "LEGO_NATIVE_SHADER_MISS_CACHE=1;LEGO_NATIVE_TRACE_DIR=<abs>\mc-on-t"
```

- **Your native4 OFF route** (b-gate menus) also works, as long as both arms use it: the misses come at the title. Only the switch may differ.
- **Preferred:** these 2 runs, about 5 min each.
- **If only one slot is left:** run ON+trace alone and compare it with your plain native4 OFF run on the same route.
  - C4 still shows whether there is anything to time.
  - logdiff and draws are then only indicative, because only one side has the trace.
  - C3 can't be checked.

## 3. Pass rules (b2r §18)

1. **logdiff:** `python build\agent10\bgate\logdiff.py --base <OFF run> --cand <ON run>` must show NEW 0 / MORE 0. Each run must close cleanly on WM_CLOSE: exit 0, no dumps.
2. **warntypes:** `python build\agent10\nb\warntypes.py --run OFF=<OFF run> --run ON=<ON run>` must show exactly equal counts. The reference per run is native3d n0 (`build/agent8/matrix/20261122-0452/runs/0452-n0-r1/game.log` L410-434):
   - placement missing: VS 0xAC449538 (backing 0xED23D3E0) ×4 and PS 0xAC448F28 (backing 0xED23D540) ×4;
   - unrecognized: VS ×8 and PS ×8;
   - "shader not present in AOT cache": ×2 at start-up;
   - hash=0 lines: 0.
3. **draws/frame:** runstats on `frames.csv` (`draw_calls`) must give the same p10/p50/p90 and scene table as OFF. For reference, native3d n0 gave 1/8/8 over 12,259 frames.
   - The cache can't add draws, because a miss still returns null.
   - **Fewer draws in ON means a stale miss was replayed for a shader that now resolves. That is a FAIL:** send me both run dirs.
4. **`unrecognized_shader` rows in events.tsv** (anomaly 1, no cap; details `guest= 2890175800 stage= 6 ` and `guest= 2890174248 stage= 7 `):
   - ON and OFF must have the same (guest, stage) set and the same rows per frame;
   - don't compare raw counts, because fps is uncapped.
5. **What ON adds:**
   - **game.log: nothing.** The replay prints the identical "placement … missing from AOT index" line through the same shared counter and cap.
   - **events.tsv:** only `shader_miss_cache_insert` rows (anomaly 0, at most 64 per run). Expected:
     ```
     shader_miss_cache_insert  0  stage= 6 guest= 2890175800 physical= 3978548192 span= 408 prefix= 15912534166948381315
     shader_miss_cache_insert  0  stage= 7 guest= 2890174248 physical= 3978548544 span= 2024 prefix= 14374147212387527897
     ```
     - These are VS 0xAC449538 at 0xED23D3E0 and PS 0xAC448F28 at 0xED23D540.
     - The second placement pair from the dump run may add rows: its VS has prefix= 11012490046570465322, and its PS again has prefix= 14374147212387527897.
     - A later row with the same key is a re-insert after a page-granular invalidation.
   - **OFF:** 0 insert rows.
   - **No row for the VS or the PS in ON:** the cache never armed. That is not a safety fail, but there is nothing to time in W8a, so report it.
   - **64 rows within about 1 min:** the cache is thrashing. Report it for W8a.

## 4. Checker

```
python build\agent4\r2t6\mc_smoke_check.py --off <OFF run> --on <ON run> --off-trace <abs>\mc-off-t --on-trace <abs>\mc-on-t
```

- It checks items 2-5: the exact warning lines, draws, the `unrecognized_shader` keys and the insert rows. logdiff is separate.
- Exit 0 means no FAIL. The RESULT line can carry these flags: NO-ARM, THRASH, C2 CHECK.
- v2 (task #25, run and checked as run-2 task #3 at 19:37 on 2026-11-22): C3 no longer needs the same key set. A key seen in both arms matches itself. The placement VS 0xAC449538 and PS 0xAC448F28, plus any `--fixed` address, only match exactly. Any other key seen in one arm only is a heap address. Those keys pair one to one by stage, rows/frame (`--c3-rpf-tol`, 0.10) and first and last row (`--c3-window-s`, 10 s after the median first-row offset). Unmatched keys are listed with the reason.
- Tested:
  - `mc_smoke_selftest.py` passes 15/15 cases (v1: 7/7);
  - real data, 0452-n0-r1 against itself: C1 26/26, C2 SAME (PASS with v1 and v2);
  - v2 on Agent 3's r6 pair: PASS with 91 exact keys, 8 heap pairs and 0 unmatched (v1 failed C3). With `--c3-rpf-tol 0.001` it fails: the two 3.50 / 3.48 rows/frame pairs are unmatched.
