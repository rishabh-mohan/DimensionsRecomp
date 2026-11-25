# #24 Q=500 default-ON: staged diff + risk list for M10 (M9, S3T-9, 2026-11-25)

Paper only: not compiled and not run. Nothing is applied to the live tree.

## Files
| file | sha256 | note |
|---|---|---|
| `q500-default.diff` | 28F0D1DE76F824F0E65B1B056A7D405F9CEBD918B06910B93759A059D25E2611 | 5615 B, +33/-5, header `a/DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp` |
| `base/gpu_wait_backoff.cpp` | 01D9F8F3464C8614... | = live = b0bd3b4 blob, 18177 B, LF-only |
| `new/gpu_wait_backoff.cpp` | 74115EEA26C4AEB2... | 19865 B, LF-only |
| `check.txt` | - | from `make_and_check.py`: RESULT PASS (0 FAIL) |

Apply from the WS root (not a git repo, so git treats it as a plain patch):
`git -c core.autocrlf=false apply --check build/agent9/session3/q500/q500-default.diff`, then the same without `--check`.
The checks covered: --check against the live tree (no write); apply on a scratch copy == new/ byte for byte; reverse == base/; and --check from `build/agent2/snap1` (same TU, exit 0).

## Design
I used a code default plus an env "off" value instead of Agent 9's cvar design. The diff is smaller and has no cvar init-order risk. The cvar/toml route is still open as a follow-up.
- `#ifndef LEGO_GPU_WAIT_BACKOFF_DEFAULT_US` → `500`. A negative value means default OFF. It can be set with `-D`; no CMake edit is needed.
- `constexpr int kDefaultQuantumUs` with `static_assert(<= 2000)`.
- Env `LEGO_GPU_WAIT_BACKOFF_US`:
  - unset or empty → the build default;
  - `off` in any case, exact match → OFF;
  - digits → as before;
  - anything else → WARN, then OFF (as before).
- The ON init line stays byte-identical to the env-q500 line.

## Behaviour: old bin vs new bin
| env value | old bin (b0bd3b4) | new bin |
|---|---|---|
| unset / empty | OFF, no line | ON Q500 (same ON line as env `500`) |
| `off` | WARN invalid → OFF | INFO `GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US=off).` (only when stats is off) |
| digits (`0`, `250`, `500`…) | as set | as set (same) |
| other invalid (`false`, `off `) | WARN → OFF | WARN → OFF (same) |
| build with `-DLEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1` | - | exactly the old behaviour |

So `LEGO_GPU_WAIT_BACKOFF_US=off` gives OFF on both old and new bins. That makes it a safe explicit off value for every arm from now on. Only the log line differs.

## Risks
- **R1 (high): `env {}` arms flip to ON on new bins.** This hits s0/ref arms, M3 functional rows, f10 rows, s4bLV/V0, the W7 s0 arm and the confirmation window. Every off arm must set `LEGO_GPU_WAIT_BACKOFF_US=off`.
  - The launcher allows the value: `run-night.ps1` L41/L275 checks key names only.
  - `stage-window.ps1` (F1Env list, L121) and the GO checks should refuse a missing key on new bins. A bin can be detected as new by the exe string `GPU wait back-off: OFF (`.
  - I have not implemented this because the launcher is pinned.
- **R2: logdiff and gates break.**
  - `build/agent6/wnight/expect-w9.json`, `expect-w5b.json` and `expect-w4c.json` forbid "GPU wait back-off".
  - `w9_envcheck.py` counts those lines.
  - `build/agent12/session3/row_gate.py` L52 uses `GPU wait back-off: ON` as a feature marker.
  - All of these need per-bin rules (new bin + env {} → expect ON; new bin + off → expect the OFF line).
- **R3: provenance.** A default-ON log is identical to an env-q500 log. Only run.json shows which one ran.
- **R4: step-B gates still open.** sleep_fail is now PASS (see below). Still to do:
  - the loaded-machine arm (required);
  - a functional pair, default vs off;
  - a timed confirmation: explicit off / default / env q500, ≥4 reps, 2 passes;
  - a quiet-host repeat;
  - a new-PC sweep.
- **R5: wake latency.** The mean effective sleep is 1.056 ms at Q=500 (s4bQ5) against 0.946 ms at Q=250 (s4b18). So the worst-case added wake latency is about 1 ms per wait.
  - W9 measured only the uncapped title screen.
  - Check levels and the loaded arm before shipping the default.
- **R6: platform.** The high-res waitable timer needs Win10 1803+. If it fails, the code does SwitchToThread on every poll and counts it as sleep_fail. That doesn't hang, but it saves less. Wine/Proton is untested.
- **R7: scope.** Every L1 waiter gets the back-off. `sub_83FAF180` is the finding-10 site, so re-run an f10 quiet pair on a step-B bin.
- **R8: CG26 interaction.** The #26 pauses sit in `__imp__sub_83FAF180`. The CG26 + default-ON combination has never been timed.
- **R9: timer bundle.** The interaction with d11p (`host_timer_resolution_ms=1`) is untimed. That could change both the 1 ms floor (R5) and the saving.
- **R10: native builds.** The TU is compiled only when `NOT LEGODIMENSIONS_NATIVE_GPU` (CMakeLists ~L184-187) and is not a native fingerprint input. So there's no re-pin and the map check stays at 31. Do not edit the stale CMake comment (L181-183): CMakeLists is itself a fingerprint input.
- **R11: env is the only way back.** There's no toml/CLI off switch. End users need the env var or a `-D` rebuild. The cvar design is the follow-up.
- **R12: stale docs.** Notes that say "env {} = OFF" are wrong for new bins. Label bins by whether they include this diff.
- **R13: not compiled.** Run `clang -fsyntax-only` on the TU once compiles are allowed. M10 then rates it.
- **R14: strict parsing.** Only an exact `off` (any case) means OFF. `0` means yield mode, not off. `false`, `no` and `off ` (trailing space) are invalid → WARN → OFF. Write `off` exactly in matrices.

## sleep_fail cross-check (item 4)
`../sleepfail_check.py` → `../sleepfail-s4bQ5.txt`: **PASS (0 FAIL)**.
- Run `build/agent3/runs/20261125-013748-s4b-Q5-gw-q500` (devoff4b-bin, env Q=500 + STATS=1, exit 0).
- 1 init line, ON 500/30/stats.
- 41 stats lines, sleep_fail 0 on all of them.
- 168907 sleeps, sleep_sum 178397.91 ms, 0 STUCK-LOCK.
