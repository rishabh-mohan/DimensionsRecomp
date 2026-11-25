# FINAL bins: F1-F7 functional gates (M12, session 3, v3 07:59)

Spec: M10 `build/agent10/session3/final-defaults-rating.md` (C20B6FDB) "Functional set before a confirmation window (F)", plus final-build-rating.md (94CC9FA7) for the S1 fix. final_gate rating: M10 `final-gate-rating.md` (AE8EB2A5) SAFE-IF. v2 applies S1-S3, N1, N5 and N6. Bins: `build/agent2/final/BIN-PINS.md` (FE4CD4FF). Bin check 07:36: `final-bins-check-0736.txt`, TOTAL BAD 0. v1 backups: `final_gate.py.v1-4C3F0DC1`, `FINAL-F-GATES.md.v1-E5797623`.

## Gating conditions (AE8EB2A5)

- **G1:** one launch per run dir. F5w is its own run dir and reuses F5's `cache/`.
- **G2:** row_gate.py alone is never a gate on a FINAL bin. Every F row gets row_gate **and** final_gate.
- **G3:** the full final_gate output of the first F1 PASS and the first F5 PASS goes to the Overseer (for M10).
- **G4:** a HOLD (exit 4) stops the chain until the Overseer rules. F5 and F5w always get `--ref build\agent8\matrix\20261125-0359\runs\0400-n0-r1`; without a ref the result is HOLD. A miss-cache HOLD ruling must cite the 0-miss count.

## Tools

- `row_gate.py <run> <id>`: common gates C1-C7, unchanged except on FINAL bins. There the C3 "init line iff cvar/env set" checks are skipped, because the win3 values are code defaults, and it points to final_gate. Backup is `row_gate.py.pre-final`.
- `final_gate.py <run> <F1..F7|F5w> [--ref <native4b n0 run>] [--first <F5 run>] [--pair <F1 run>]`:
  - It reads harness run.json (`cvars`/`env`) and run-matrix run.json (`params.cvar`/`toml_set`/`env_set`).
  - It joins the rotated logs oldest first (game.N.log … game.1.log, game.log) into `final/tmp/<parent>__<run>__<sha8 of path>.joined.log` and runs the rated `check-defaults.py` (D9936C56, sha checked) on that file.
    - N5: the parent of a matrix run dir is always `runs`, so the path hash is what keeps two matrices' `r1` dirs apart.
    - On a rotated log the startup proof lines are in game.1.log, so check-defaults run on game.log alone would FAIL falsely.
  - N1: every report has `NOTE elapsed <s> s (<src>)`. The source is harness `elapsed_s`, or matrix `end - start`.
  - Exit codes: 0 PASS, 1 FAIL, 4 HOLD (Overseer ruling), 2 usage.
  - `--selftest` 56/56 (v3):
    - units;
    - synthetic fixture cases (positive / HOLD / FAIL per row, incl. F3 on devfinal-off and the v3 route-timeout cases; the run-dir binary hash checks are skipped only there, through a parameter the CLI can't reach);
    - real level-l runs s4bV0f/s4b07f as F2: route items and the common checks PASS (except "C1 verify: on": those rows ran verify=1), bin FAIL; w6-gateB (timeout on line 22) → FAIL; cg26L (27 timeouts) → PASS + NOTE;
    - 5 real negative controls that must FAIL closed: native4b n0 as F5 and as F6, win3 (devoff4b) as F1 and as F3, plus n0 vs itself for the miss count.

## Every F row (FAIL if not met)

- run.json: exit 0, not exited early, no WER/dialogs/crash events, no dumps, WM_CLOSE (harness `close_method`, or matrix `close.wm_close_posted` and not killed).
- Log: "Title terminated" x1.
- 0 of each: Recovered stale physical page protection, Unhandled guest physical write fault, PhysicalHeap::Protect failed, BaseHeap::Protect failed, is not a plain number, C1 verify: on, STUCK-LOCK, REX_FATAL, Minidump written to, still not acquired after.
- Bin id:
  - run.json `bin_dir` = the row's bin;
  - that bin's MANIFEST sha = BIN-PINS;
  - run-dir MANIFEST copy (matrix) = pin;
  - run.json exe_sha256 / run-dir exe, rexruntime.dll and rexgpu-xenos.dll = the BIN-PINS file table.

## Per row

| row | bin | switches (from run.json) | proof |
|---|---|---|---|
| F1 | devfinal-bin, WC light route | cvars == {framerate_limit=0}; no `LEGO_GPU_WAIT_*` env | `check-defaults --mode xenos` PASS |
| F2 | devfinal-bin, `level-l-tail` (BE08A790) + toypad, ≥10 min | none of the 12 SDK keys; no `LEGO_GPU_WAIT_*`; framerate_limit=0 (NOTE) | `C1 keep-watch: on (with physical_protect_hold_global_lock)` x1; 0 bad strings / stale; elapsed ≥ 590 s; route script contains `level`; vortex mark; Toypad lines > 0. **Route (v3):** script_sha256 is level-l (6F9E6009) or level-l-tail (BE08A790); steps n/n and stopped_by_script; `timeouts` = count of `timeout_lines`; every timeout line is one of the route's by-design waits (level-l 55 and 58-116 even; tail = those − 7, i.e. 48 and 51-109 odd), otherwise FAIL. Fewer than 31 is a NOTE (27-31 seen over 20 level-l runs). **S2:** xenos mode not PASS → HOLD when the switches are clean (no SDK key, no `LEGO_GPU_WAIT_*`); NOTE when a switch FAIL already explains it |
| F3 | **devfinal-off-bin** (S3) | the 12 old values exactly (DEFAULTS-TABLE L92); env `LEGO_GPU_WAIT_BACKOFF_US=off` (lowercase) | `--mode off` PASS. row_gate's C3 skip on this bin is always paired with this row |
| F4 (opt.) | devfinal-bin | cvars == {framerate_limit=0}; env `LEGO_GPU_WAIT_*` == {BACKOFF_US=500} | xenos PASS; with `--pair <F1>` the proof lines equal F1's, ignoring the source tag (q500 R3) |
| F5 | nativefinal-bin, W8a route | `LEGO_NATIVE_SHADER_MISS_CACHE` unset; no SDK key / back-off env | `--mode native-old` PASS; run-dir exe has `1616ce65e973c583` and not `9b40acbbef4c57b3`; `b/nat/gen-on/native-gpu-build.txt` = `LEGO Dimensions native GPU 1616ce65e973c583`; the row bin's MANIFEST lists A33801D1/E3CB99CF, and the run-dir DLLs = pin; shader-miss warnings (AOT-cache miss, missing from AOT index, unrecognized VS/PS resource) per class and in total ≤ the `--ref` native4b n0 run (HOLD if there's no ref; all 15 W8a runs, n0 and mc: 2/8/8/8 = 26) |
| F5w | nativefinal-bin, 2nd launch, **own run dir** reusing F5's `cache/` (G1) | as F5 | as F5, plus: `--first <F5 run>` has `saved N startup pipeline recipes`, N ≥ 1; this run has `startup pipelines loaded=N … failed=0`, N ≥ 1; `no startup pipeline recipes yet` x0; `ignoring invalid or incompatible pipeline recipes` x0. N6 NOTE: loaded vs the first launch's max saved N. **S1:** if the only native-old FAIL is the absent miss-cache ON line: 0 shader-miss warnings → HOLD, >0 → FAIL |
| F6 | **nativefinal-off-bin** (S3) | env `LEGO_NATIVE_SHADER_MISS_CACHE` unset or `0` (the NOTE says which) | env unset: `Native GPU: shader miss cache OFF (build default)` x1. env 0: `Native GPU: shader miss cache OFF (LEGO_NATIVE_SHADER_MISS_CACHE set)` x1. In both cases ON line x0, miss-cache lines of any kind x1, and native-old shows no FAIL apart from the ON-line count. No miss-cache line at all: 0 misses → HOLD, >0 → FAIL. row_gate's C3 skip on this bin is always paired with this row |
| F7 | nativefinal-bin, level route | as F5 | clean, plus the F2 route items (except C1). **S1:** if the only native-old FAIL is the absent miss-cache ON line: 0 shader-miss warnings → HOLD (M10 N1: the line is logged on the first miss only), >0 → FAIL. Otherwise the native-old result counts |

## Notes for M3's drafts

- check-defaults takes one file. On rotated runs, use final_gate's joined copy (or game.1.log + game.log), not game.log alone.
- The harness run.json has `env` (not `env_set`) and `bin_dir` (no separate bin-id field). final_gate reads both layouts.
- F5w is its own run dir (G1). M3's draft has to say how it reuses F5's `cache/`. The W8a-style recipe files are `cache/native-pso-recipes.bin` and `cache/native-pso.bin`.
- INFO (M10): don't use `physical_protect_keep_watch_verify=true` on devfinal-bin. The gate fails "C1 verify: on" anyway.
