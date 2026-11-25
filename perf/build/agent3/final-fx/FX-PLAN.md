# FINAL F1-F7 functional queue: DRAFT r2 (M3, 2026-11-25 07:58; r1 07:55)

Draft only: nothing is installed or launched. Every row is FUNCTIONAL ONLY (s4b-queue, hidden desktop).

Spec sources:
- M10 final-defaults-rating C20B6FDB ("Functional set") and final-gate-rating AE8EB2A5 (G1, G4, bins).
- M12 FINAL-F-GATES E5797623 and final_gate.py v2 9DCC72EE (M12 was still revising it at 07:58, see Rulings).
- M2 BIN-PINS FE4CD4FF. check-defaults D9936C56 (final_gate pins this sha).

## Files (build/agent3/final-fx/)

| file | what |
|---|---|
| queue-final-fx.jsonl | 7 rows (6 core + optional fx4) to append to build/agent3/s4b/queue.jsonl |
| matrix-fx5.json | F5 + F5w run-matrix (arms fx5, fx5w). `run-matrix -PlanOnly` exit 0: 2 runs, ~5 min |
| level-l-tail.txt | F2/F7 route = level-l.txt (6F9E6009) lines 13-130 unchanged + `sleep 180` / `mark tail` / `stop` (~730 s) |
| postcheck.ps1 | live postcheck 1025D1F6 + the fx hooks. Installed by copying it over build/agent3/s4b/postcheck.ps1 |
| check_queue_fx.py | the queue checker (`--dryrun` runs run-game -DryRun per row into dryrun/) |
| check-queue-fx.out.txt | checker output: ALL CHECKS PASS (199 ok) |
| note-s4bcheck-on-matrix-run.txt | s4b_check on a run-matrix run: always one BASE miss, `close None` |

## Rows, order and gating

Every row needs `build\agent3\s4b\ready-s4b-off` and `build\agent3\final-fx\go-fx`. Each core row also needs the fx-ok marker of the row before it, so a FAIL or a HOLD (G4) stops the chain: no marker is written, and the next row never starts.

| id | F | bin | switches | route, -Seconds | est s | extra need |
|---|---|---|---|---|---|---|
| fx1 | F1 | devfinal-bin | cvar framerate_limit=0; no env | plain (WC light route), 240 | 270 | - |
| fx3 | F3 | **devfinal-off-bin** | framerate_limit=0 + the 12 old values; env LEGO_GPU_WAIT_BACKOFF_US=off | plain, 240 | 270 | fx-ok-fx1 |
| fx2 | F2 | devfinal-bin | framerate_limit=0; toypad | level-l-tail, 840 | 870 | fx-ok-fx3 |
| fx4 (opt) | F4 | devfinal-bin | framerate_limit=0; env BACKOFF_US=500 | plain, 240 | 270 | go-fx-opt, fx-ok-fx1 |
| fx5 | F5 + F5w | nativefinal-bin | W8a cvars, plain | run-matrix matrix-fx5.json -NoCold | 480 | fx-ok-fx2 |
| fx6 | F6 | **nativefinal-off-bin** | W8a cvars, plain | plain, 240 | 270 | fx-ok-fx5w |
| fx7 | F7 | nativefinal-bin | W8a cvars, plain; toypad | level-l-tail, 840 | 870 | fx-ok-fx6 |

- W8a cvars = `native_settings_frontend=false;native_fps_limit=0;framerate_limit=0`.
- The short proof rows run first, so a bad bin is caught early.
- Run time:
  - Core rows: est 3030 s (~50 min of queue time); real game time ~42 min.
  - With gate gaps (postcheck poll, s4b_check, final_gate, then the marker) the core rows take ~55-60 min wall.
  - The optional row fx4 adds ~4.5 min.

## Checks per row (draft postcheck)

1. **s4b_check, as a reading only.**
   - Bases:
     - fx1/3/4: base s4b01 (fallback S4a r1), allow-new `Final defaults|C1 keep-watch|GPU wait|TimerQueue|Host timer|precise`.
     - fx2: base s4bL0 (fallback lx2), same allow-new.
     - fx6/7: base S4a r5 native4, allow-new `shader miss cache|startup pipeline|pipeline cache`.
     - fx5: base the n0 ref.
     - fx5w: base fx5.
   - Output: `logs\<id>.check.txt`.
2. **The gate: M12's final_gate.py `<run> <F>`.** Output: `logs\<id>.fx.txt`, last line `final_gate exit N`.
   - final_gate joins rotated logs oldest first and reads run.json `env`/`cvars`/`bin_dir`, or `env_set`/`params` for matrix runs.
   - fx4 is gated with `--pair <fx1 run>`.
3. **F5 matrix row.** The queue-state record has `matrix_out`, not `run`, so the draft adds a matrix branch:
   - It finds `<matrix_out>\runs\*-fx5-r1` and `*-fx5w-r1`.
   - fx5 is gated `F5 --ref build\agent8\matrix\20261125-0359\runs\0400-n0-r1` (M12 d).
   - fx5w is gated `F5w --first <fx5 run> --ref <n0>`.
4. **Markers.**
   - With `-FxAuto`: postcheck writes `fx-ok-<id>` only when final_gate exits 0 and the reading is clean:
     - harness rows: s4b_check hint PASS?;
     - fx5: final_gate only;
     - fx5w: final_gate plus the seed check.
   - Without `-FxAuto`: M3 reads the logs and writes the marker by hand. The install uses `-FxAuto` (ruling 3).
5. **Self-test of the new functions** (AST-loaded from the draft, run on old runs). All 8 cases as expected:
   - seed check PASS on a real seeded pair; wrong source and missing seed both caught;
   - final_gate on n0 as F5 gives exit 1;
   - markers only on exit 0.

## F5w cache carry-over (M10 G1, M12 c)

- There is no env or cvar for the native cache path: pipeline_library.cpp uses `<exe dir>\cache\`. So F5w uses the runner's documented seed step:
  - matrix arm `"seed_cache": "fx5"`;
  - run-matrix passes the fx5 run of this matrix to `run-timing.ps1 -SeedCache`.
- run-timing then:
  - copies **only** `native-pso.bin` and `native-pso-recipes.bin` from `<fx5 run>\cache\` into the new fx5w run dir's `cache\`, before launch;
  - does not start the game if either file is missing;
  - records `seed_cache {requested, source_dir, recipes_only false, dest, files[name, source, bytes, sha256]}` in fx5w's run.json.
- fx5w is a fresh run dir (one launch per dir). No logs are carried over.
- The postcheck seed check confirms:
  - `source_dir` == `<fx5 run>\cache`;
  - exactly those 2 files, not recipes_only;
  - the sha256 of each file equals fx5's cache file.
- final_gate F5w then needs:
  - first launch saved ≥1 recipe;
  - `startup pipelines loaded>=1 failed=0`;
  - no "no startup pipeline recipes yet";
  - no "ignoring invalid or incompatible".

## Rulings applied (Overseer 07:55)

1. **Timeouts:** M12 changes final_gate to accept exactly the level routes' by-design timeouts. The draft final_gate already lists level-l-tail.txt by sha (BE08A790), so that file must not change.
2. **Bins:** final_gate v2 maps F3 → devfinal-off-bin and F6 → nativefinal-off-bin. F6 accepts the plain `OFF (build default)` line. `$FxGate` keeps F3/F6. fx3e/fx6e are dropped.
3. **Markers:** install with `-FxAuto`.
   - A marker is written only on final_gate exit 0 plus a clean s4b reading. fx5 uses final_gate only; fx5w uses final_gate plus the seed check.
   - HOLD or FAIL writes no marker. M12 gates every row in parallel. If M12 or M10 objects, the Overseer stops the chain.
4. **F7 HOLD:** v2 gives HOLD only when the miss-cache line is absent AND there are 0 misses; with >0 misses it is a FAIL. The Overseer rules on a HOLD.
5. **Window:** reinstall s4b-queue with `-LastLaunch 13:30 -GamesClosed 14:00`.
6. **check-defaults:** D9936C56C5E04B98…, the same as the pin.

**Still open:** M12 was still revising final_gate.py at draft time (v2 9DCC72EE → E91D5870 → A6DE594F at 07:58; selftest 54/54). At install, run check_queue_fx with `--fg-sha8 <the sha8 M10 rated>`. Without it, the checker only prints the sha and checks ROW_BIN against the queue bins.

## Install (on the Overseer's go only)

1. Back up queue.jsonl.
2. Re-run `check_queue_fx.py <file to install> --fg-sha8 <rated>`, then append the 7 rows.
3. Back up postcheck.ps1 as `.bak-fx`, copy the draft over it, parse-check it, and restart it between checks with `-FxAuto`.
4. Restart s4b-queue with `-LastLaunch 13:30 -GamesClosed 14:00`.
5. Create `go-fx` (and `go-fx-opt` only if told).
6. Report each row id + final_gate exit to the Overseer for M12.
