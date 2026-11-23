# Re-pin on native4b: the 3d line's pin moves from native4 to native4b (S4b + S4c)

- **Only two fingerprint inputs change:** `rexlego/src/gpu_native/memory_watch.cpp` 19AE1606 -> 70829846 (C1 v3's rexlego half) and `rexlego/CMakeLists.txt` 3690D5D7 -> 1BF46D78 (S4c: #24 + #30). **Expected native4b fingerprint: `9b40acbbef4c57b3`.** The 19:51 dry run recomputed it on snap1 as applied at 19:50:19, and it equals the prediction from the staged after-files (`dryrun-snap1-1951.txt` [4]).
- **Who does what:** Agent 2's S4b driver applies and builds (`prep-s4b.py`, `run-s4b.ps1`). Agent 4 runs `repin_check.ps1` as a dry run only (no `-Go` tonight). Agent 3 runs the boot check and the 4-run matrix. Agent 1 announces the pin.
- **Timing:** devoff4b ~20:30, native4b ~21:00, then devoff4b-ctr, and devoff4b-cg26 only if Agent 10's gates hold. The pin record takes ~1-3 min and Agent 3's 5 runs ~20 min, so the pin is due ~21:20-21:40.
- **Not tonight:** the B line (nativeB4b-bin) and the pack bin (native4bp: built after the break for the user's visual check, and pinned only after the user's yes). See section 4.

Agent 4, run-2 task #12 (2026-11-22 ~20:15). Adapted from the 14:40 version (task #20: native5 / devoff5), now in `superseded/REPIN-1440-native5.md`; its matrix is `superseded/matrix-repin-native5.json`. `repin_check.ps1` is a dry run by default: it reads only and writes only its report. `-Go` is not used tonight.

## 1. What changes

### 1.1 Bins and pins

| bin | native fingerprint | MANIFEST sha256 (16) | role tonight |
|---|---|---|---|
| `build/agent2/native4-bin` | `5e3ff55de10f4f64` | 00D33D4FFB46776D | the current 3d-line pin (S4a, #2 OFF) and the "before" (n0old); frozen |
| `build/agent2/native4b-bin` | expected `9b40acbbef4c57b3` | from step 3 | the pin candidate: the S4b + S4c native build, every switch OFF (Agent 2's `<S4B-NAT>`) |
| `build/agent2/native3d-bin` | `335ff2d47268f3a1` | 368F9CE650EC56CE | frozen older pin. native4b's n0/n2/n3 replace its n-row baseline (`build/agent8/matrix/20261122-0452/runs/`: `0452-n0-r1`, `0454-n2-r1`, `0456-n3-r1`) |
| `build/agent2/nativeB-bin` | `81d1c3a71be3c096` | E5CBF30A6132B00E | stays the B pin (section 4.1) |
| `build/agent2/devoff4b-bin`, `devoff4b-ctr-bin`, `devoff4b-cg26-bin` | none (Xenos builds) | MANIFEST only | Agent 3's S4b queue; not part of the re-pin |
| `build/agent2/nativeB4b-bin` | - | - | not tonight |
| `build/agent2/native4bp-bin` | - | - | the pack bin; not tonight |

Nothing else consumes the fingerprint, so there is nothing to regenerate. The shader caches key on shader hashes, not on the fingerprint.

### 1.2 The two input changes

| input (snap1 tree) | before (native4) | after (native4b) | how it lands |
|---|---|---|---|
| `rexlego/src/gpu_native/memory_watch.cpp` | 19AE1606C6DB7273, 7,613 B, 166 CRLF | **70829846C4F321A9**, 8,054 B, **172 CRLF / 0 bare LF** | C1's rexlego half. `build/agent12/s4-c1/keep-watch-rexlego.diff` (4D0C1079, v1, reused by C1 v3) is LF-only, so `git -c core.autocrlf=false apply --check` fails on the CRLF file. Instead, copy the staged after-file `build/agent12/s4-c1/new/game/rexlego/src/gpu_native/memory_watch.cpp` (CRLF) and set its mtime to now. After landing, the file must hash 70829846 (compose file [5]). |
| `rexlego/CMakeLists.txt` | 3690D5D76AA9FBED, 51,070 B, 885 CRLF | **1BF46D7878BA9A25**, 52,311 B, 907 CRLF / 0 bare LF | S4c, `build/agent9/s4/fence-wait/s4c/s4c-24-30.diff` (DC02104EA76E0BF6). It adds #30's option `LEGODIMENSIONS_SCENE_WALK_PROBE` (OFF) and #24's new TU `src/gpu_wait_backoff.cpp` inside `if(NOT LEGODIMENSIONS_NATIVE_GPU)` (Xenos builds only, with `LEGO_GPU_WAIT_HOOK_GETDATA=1`). |

Agent 2's `prep-s4b.py` applied both to `build/agent2/snap1/DimensionsRecomp` at 19:50:19, setting mtime = now on every copy.

- **Not inputs:** the SDK diffs (C1 v3 `keep-watch-v3.diff` DECCFE33, M1 EBECE86E, P2c 29E02E24, r1r2 BD0C4A93, #26 db16cyc_pause AC554DBB) and `src/gpu_wait_backoff.cpp` (01D9F8F3, LF; native builds don't compile it). They change the bin, but not the fingerprint.
- **Must not change in snap1:** the other 269 inputs, notably `rexlego/legodimensions_config.toml` and `generated/default/legodimensions_recomp.*.cpp` / `legodimensions_funcs.*.h`. #26's toml line and regen go only into devoff4b-cg26's copy, never into snap1. If they reached snap1, the fingerprint would differ from `9b40acbbef4c57b3`.
- **The input list:** 271 files, taken from a block in CMakeLists.txt. The block sits at lines 582-765 before S4c and 604-787 after; its text is identical, so only file bytes change. The list includes CMakeLists.txt itself and memory_watch.cpp, but not gpu_wait_backoff.cpp.
- **Where it shows:** the build computes the fingerprint from the listed inputs (`generate-native-gpu-fingerprint.cmake` in the build dir) and writes it to `native-gpu-build.txt` and `native_gpu_build_info.h`. The game logs it as `Native GPU [<fp>]`, and the bin's MANIFEST.txt carries it as `native GPU <fp>`. `repin_check.ps1` [4] recomputes it the same way.
- **The mtime trap:** ninja ignores a copied file whose mtime is old. The build would then keep the old objects and the old fingerprint. Every copy gets mtime = now (prep-s4b.py does this), and [3] warns on a staged mtime.

## 2. Steps

| step | who | what | pass | status |
|---|---|---|---|---|
| 0 | Agent 4 | pre-check: `repin_check.ps1 -Line snap1` (dry run) | [1] staged files match their records; [4] expected = recomputed | done 19:51 (`dryrun-snap1-1951.txt`): [1]-[4] ok, expected = recomputed = `9b40acbbef4c57b3`. Its one FAIL ([5] on native4-bin) was a script bug, fixed at 20:08: the frozen old bins are now info |
| 1 | Agent 2 | apply C1 v3 + S4c to snap1 (`prep-s4b.py`) | [3] shows both applied | done 19:50:19 |
| 1b | Agent 4 | dry run after the CMake re-run of snap1-on (native4b's configure): `& .\build\agent4\repin\repin_check.ps1 -Line snap1 -Report build\agent4\repin\dryrun-native4b-1b-<HHMM>.txt` | [3] memory_watch.cpp 70829846, 172 CRLF / 0 bare LF; CMakeLists.txt 1BF46D78 with #24 in. [4] recomputed = expected = `9b40acbbef4c57b3`. The fingerprint goes to Agents 2 and 1 | waits for Agent 2's word that snap1-on's CMake re-run is done (a `snap1-on/build.ninja` newer than 19:50:19 shows it too). Step 3 waits for this confirmation (Agent 1, 20:30) |
| 2 | Agent 2 | `run-s4b.ps1`: SDK build + install, devoff4b (snap1-off), native4b with configure (snap1-on), staged to `build/agent2/native4b-bin` | build OK, MANIFEST written | ~21:00 |
| 3 | Agent 4 | pin record (dry run): `& .\build\agent4\repin\repin_check.ps1 -Line snap1 -BinDir build\agent2\native4b-bin -FullHash -Report build\agent4\repin\pin-native4b-<HHMM>.txt` | [4] built = recomputed = `9b40acbbef4c57b3`, not 5e3ff55de10f4f64. [5] native4b-bin's MANIFEST fingerprint = built, and not an old pin | after step 2 |
| 4 | Agent 3 | section 3: (a) the boot check, (b) the 4-run matrix | section 3 | ~20 min after step 3 |
| 5 | Agent 1 | announces the pin | (a) and (b) pass | - |

After step 5, Agent 4 adds `'9b40acbbef4c57b3' = 'native4b (S4b + S4c)'` to `$PINS` in repin_check.ps1. Not before: with it in `$PINS`, [4] and [5] would flag native4b itself as an old pin. Even after step 5, that one line is not enough: [4] (L373) would then FAIL section 4.2 step 1's dry run, where snap1-on still builds and recomputes to `9b40acbbef4c57b3`, and [5] would FAIL `-BinDir build\agent2\native4b-bin`. Key those rules on the pack state first (`build/agent4/HANDOFF.md`, open item 3).

**On a fail at any step**, the pin stays on native4 (`5e3ff55de10f4f64`), and native4b-bin is parked, not deleted. Send the reports or run dirs to Agents 4 and 2.

## 3. For Agent 3 (after step 3)

Both are functional, agent-slot runs: hidden desktop OK, not timing. Check `perf-notes/WINDOW-HOLD.txt` before each launch.

Always pass `-OutDir` under `build\agent3\runs\`. Without it, run-matrix writes to `build\agent8\matrix\<yyyyMMdd-HHmm>`, and Agent 1's HOLD manager takes that as a window: every agent pauses and Agent 2's build stops. Below, `<stamp>` is `yyyyMMdd-HHmm`, for example `-OutDir "build\agent3\runs\repin-$(Get-Date -Format yyyyMMdd-HHmm)"`.

### (a) The boot check, with the frontend on

`native3_boot_check.py` group A needs the effective `native_settings_frontend=true`. Every arm of the matrix in (b) runs with it false, so the boot check gets its own 1-run matrix:

1. `bench\agent8\run\run-matrix.ps1 -Matrix build\agent4\repin\matrix-repin-native4b-boot.json -NoPrompt -OutDir build\agent3\runs\repin-boot-<stamp>` (1 run, ~4 min). Arm b0 runs native4b-bin with `native_settings_frontend=true` on the command line, uncapped, and `LEGO_NATIVE_FRAME_METRICS=<run>\native-frames.csv`. The check reads `native-frames.csv`, while `harness/run-game.ps1` writes `frames.csv`, so use this matrix rather than a run-game boot.
2. `python bench\agent7\native3_boot_check.py build\agent3\runs\repin-boot-<stamp>\runs\<HHMM>-b0-r1 --bin-dir build\agent2\native4b-bin`

Pass: exit 0, meaning no FAIL in A, B or C, plus D's identity lines. D is info-only and never FAILs on its own, so read its lines:
- A: frontend true.
- B: no throw/fatal line, a present line after 'Native write tracking', run.json OK, no dumps, and >= 600 native-frames.csv rows.
- C: bilinear present.
- D: a `PASS native GPU fingerprint: MANIFEST 9b40acbbef4c57b3, game.log 9b40acbbef4c57b3` line. The check skips this line without a message when either side is missing, so a missing line is a fail. D also needs PASS on the two fix (a) MANIFEST rows: `settings_registry.cpp: ... -> 4EC71328...` (or 8BA19C5F) and `settings_preferences.cpp: ... -> 9CBE6DBF...`. The VERDICT line should read `D=PASS` with no `(N WARN)`. Send me any other D WARN (frame column gaps, runner window, perf.csv rows). It doesn't block the pin by itself, but I'll look at it.

### (b) The matrix: identity against native4, and the new n-row baseline

`bench\agent8\run\run-matrix.ps1 -Matrix build\agent4\repin\matrix-repin-native4b.json -NoPrompt -OutDir build\agent3\runs\repin-<stamp>` (4 runs, ~15 min). The run dirs are `build\agent3\runs\repin-<stamp>\runs\<HHMM>-<arm>-r1`, and `<n0old>`, `<n0>`, `<n2 dir>` and `<n3 dir>` below are those dirs. n0old runs on native4-bin; n0, n2 and n3 run on native4b-bin. The settings are those of S3's N1-N3 (`bench/agent4/s3/matrix-native3d-functional.json`): `native_settings_frontend=false`, uncapped, `drivers/thread-cpu.ps1`, a 30 s warm-up from the first frame (run-matrix's default `min_window_after_ff_s` of 60 makes it 60 s), then a 60 s window.

Pass:
- `python build\agent10\bgate\logdiff.py --base <n0old> --cand <n0>`: NEW 0 and MORE 0, apart from the `Native GPU [<fp>]` line. One more change is expected: if n0old has `slow frame` lines, n0's carry P2c's new `| memexport full-buffer Nx (total N)` suffix.
- None of the S4b families appears on any arm, since every switch is OFF at defaults:
  - no `C1 keep-watch` line (C1 prints only with `physical_protect_keep_watch` on; QUEUE.md row 2: "No C1 line");
  - no `d3d12_submit_split` or `deferred_counters` line (r1r2: cvar-gated, D3D12 path);
  - no `GPU wait back-off` line (native builds don't compile #24).
- n0's draws per frame (p10/p50/p90) match n0old's; no new warning type; a clean WM_CLOSE in all 4 runs.
- n2 has `Native draw batches: parallel workers=2` and no hash=0 lines. n3 has no `Native draw batches` line and no hash=0 lines.
- `python bench\agent4\check_n_rows.py --baseline <n0> --rows n2=<n2 dir> n3=<n3 dir>` exits 0.

If all pass, n0/n2/n3 replace native3d's `0452-n0-r1` / `0454-n2-r1` / `0456-n3-r1` as the n-row baseline. On a fail, send the run dirs to Agents 4 and 2; the pin stays on native4.

### (c) The pack-hit check: not tonight (section 4.2)

## 4. Not tonight

### 4.1 The B line (nativeB4b-bin)

- nativeB-bin (`81d1c3a71be3c096`) stays the B pin as staged.
- Agent 2's S4b SDK build installs into `snap1-sdk/install`, which snapB-off / snapB3-on link. From now on, a B-line rebuild links the S4b SDK. The options are to clone snap1-sdk first or accept that (agent2-baseline L28-29).
- When the B line comes: the same steps with `-Line snapB3` (build dir snapB3-on), after Agent 2's B build (~35 min more). Its matrix runs n0old on nativeB-bin and n0/n2/n3 on the new B bin.

### 4.2 The pack bin (native4bp)

Steps 1-2 build the pack bin for the checks in `build/agent4/r2t6/VISUAL-CHECK.md` and the user's look (`build/agent4/screenshot-kit/README.md`). Steps 3-4 make it the pin, a second re-pin (~20 min). They start only after the user's yes:

1. `repin_check.ps1 -Line snap1 -Pack` (dry run) plans the s35 pack copies.
2. Agent 2 applies them, builds with `cmake -D LEGO_NATIVE_RUNTIME_SHADER_CACHE=...` (the s35 runtime-cache.cpp), and stages the result to `build/agent2/native4bp-bin`.
3. `repin_check.ps1 -Line snap1 -Pack -BinDir build\agent2\native4bp-bin` must show the 4 pack hashes in the prelinked cache.
4. Agent 3 runs `matrix-repin-packhit.json`: t0 on native4b-bin, t0p on native4bp-bin, 2 runs, ~12 min.

On a fail, the pack bin is parked and the pin stays on native4b.

## Sources

- Agent 1's run-2 task #12 (19:41); SESSION2 L2694-2730 (19:31-19:49).
- `build/agent2/s4b-compose-1932-c1v3.txt`: the S4b order and diff hashes; [5] is C1's rexlego landing rule.
- `perf-notes/S4-DRAFT.md` L258 (the #24 / #30 CMake edit). For C1 v3's landing hash and the CRLF rule: L73 (the landing check: memory_watch.cpp must hash 70829846; the rexlego diff is LF-only and the file is CRLF, so copy the staged new/ file), L66 and L293 (keep-watch-v3.diff DECCFE33, then the unchanged rexlego diff, keeping CRLF) and L16 (the build gate: memory_watch.cpp with CRLF). These line numbers are from its 20:07:54 version.
- `perf-notes/agent2-baseline.md` L1-29 and L592 (the bin names, the snap1-sdk caveat).
- `build/agent9/s4/fence-wait/s4c/HASHES.txt`; `build/agent12/s4-c1/` (orig/new memory_watch.cpp); the bins' MANIFEST.txt.
- `build/agent7/s4b-queue/QUEUE.md` rows 2 and 5; `bench/agent7/native3_boot_check.py` (group A, native-frames.csv); `harness/run-game.ps1` (frames.csv).
- Reports in `build/agent4/repin/`: `dryrun-snap1-1951.txt`, then the step 1b and step 3 reports as they come.
