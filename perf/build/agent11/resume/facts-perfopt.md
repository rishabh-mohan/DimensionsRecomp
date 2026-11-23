# perf/opt fact sheet for perf-notes/RESUME.md (helper for Agent 11, task #25)

Compiled 2026-11-23 05:45-06:20, read-only; **updated 08:16 after the SCRNSAVE install** (§0 items 7-8, the §4 runner note, §5, the §6 re-pin and line numbers). For everything else `perf-notes/RESUME.md` (final, 08:09) is newer. Paths are workspace-relative; sha16 = first 16 hex digits of SHA-256; git ran as `git -C DimensionsRecomp ...` / `git -C DimensionsRecomp/rexglue-sdk ...`. Raw outputs: `build/agent11/resume/scratch/`.

## 0. Read first

1. **Code pushed and verified:** both perf/opt branches = `mine/perf/opt`, 0 ahead/0 behind; 16/16 files match `build/agent2/s4b/HASHES.txt`; `build/agent2/COMMIT-CHECK.md` RESULT PASS (§1).
2. **Plume gitlink `ceaeeee` is not in the local plume clone** (`git cat-file -t` gives "Not a valid object name"); the worktree is at the prepare-script PIN `e0c8871`. Rebuild = check out e0c8871 + prepare_plume.py, not `git submodule update` (§3).
3. **rexglue-sdk is a standalone clone at the submodule path, not an initialized submodule** (`git submodule status`: `-5350b1d`). Its `.gitmodules` maps 23 of 25 gitlinks; `thirdparty/FidelityFX-SDK` (eee08db1688a, since 7bdae77, 2026-09-04) and `thirdparty/snapdragon-gsr` (d926f074bcb9) are missing, so `git submodule status` in the SDK fails ("no submodule mapping found"); a fresh recursive clone probably fails too (untested). Pre-sprint.
4. **CRLF feeds the native fingerprint:** `core.autocrlf=true` in both repos, `* text=auto` in DimensionsRecomp. memory_watch.cpp and rexlego/CMakeLists.txt are LF in git and CRLF in the worktree; fingerprint 9b40acbbef4c57b3 hashes the raw bytes of 271 inputs including both (REPIN.md L3, L36-38). An autocrlf=false or Linux/WSL clone gets another fingerprint. gpu_wait_backoff.cpp is LF in the worktree (not an input).
5. **Every S4 switch defaults OFF (§2).** Always on: #32, P2c counter, C1 native latch, #24 pass-through hooks (Xenos). S3 cvars `pause_safe_order` and `audio_shutdown_detach_worker` default **ON** (c5fe668).
6. **W5b ran on devoff4-bin (S4a), not devoff4b** (§4).
7. **SCRNSAVE fix installed at 07:33:57** (`build/agent5/scrnsave-fix/install-log.txt`), after the night launcher ended at 07:30:14. After the install: `test-scrnsave.ps1 -Set installed -E2E` 45/45 (07:34:45), `build/agent5/launch-test/run-tests.ps1 -Group go` 16/16 (07:52, test-only `-StopAt`), `test-day.ps1 -Name all` 27/27 (07:47); Agent 10 checked them at 07:56 (`build/agent10/t27/scrnsave-delta.md` §5). The day draft was regenerated from the fixed launcher (copied into `build/agent5/day-draft/` at 07:34), which closed day-draft condition 1 (§5).
8. **native4b re-pin: step 4 passed (rpb0, rpm4); step 5, Agent 1's announcement, is left** (§6). **#30's probe sources (`src/scene_walk_probe.cpp/.h`) don't exist** (not committed; `build/agent9/s4/scene-walk/` is analysis only): the option ON fails configure (rexlego/CMakeLists.txt:161-162).
9. Both prepare `--check` runs PASS (06:01-06:04, Below Normal; §3).

## 1. Repos and commits

| repo | perf/opt HEAD | upstream | other local branch | remotes |
|---|---|---|---|---|
| `DimensionsRecomp/` | `b0bd3b4aba5fe4d26572d89910836ee7db48fcea` | `mine/perf/opt`, 0/0 | `main 895a529 [origin/main]` | mine, origin |
| `DimensionsRecomp/rexglue-sdk/` (own .git) | `5350b1de99276b7a7be701bf00914f1ee58ce9bc` | `mine/perf/opt`, 0/0 | `toypad-ui 516e631 [origin/toypad-ui]` | mine, origin |

Sources: `git branch -vv`, `git rev-parse HEAD`, `git rev-list --left-right --count perf/opt@{upstream}...perf/opt` (scratch/git1.txt). `git ls-tree`: b0bd3b4 has rexglue-sdk 5350b1d and plume ceaeeee; 1bd322e has rexglue-sdk 3bb65bb. `.gitmodules` at b0bd3b4: rexglue-sdk (`branch = perf/opt`), DimensionsModManager, DimensionsSaveConverter (both not checked out, COMMIT-CHECK L71-72), thirdparty/plume.

**`git log --oneline -12 perf/opt`** (2026, local time):
- DimensionsRecomp: `b0bd3b4` 11-23 05:40 **S4b/S4c** (memory_watch keep-watch, GPU wait back-off hooks, probe option; SDK → S4b) · `1bd322e` 11-22 14:56 **S4a** (gpu_native shader miss cache #2, default OFF; SDK → S4a) · `08933a7` 05:02 S3d (draw.cpp +5) · `001336f` 02:21 S3 inputs (native settings fix (a)) · `a0bdaa7` 01:50 checkpoint, batches 1-2 · pre-sprint: `127e04b` (11-16), `d94c2fd f1ddad6 6834b23 c62dcb8 cbd2c39 abb1c75` (October).
- rexglue-sdk: `5350b1d` 11-23 05:40 **S4b** (C1 v3 keep-watch, M1 non-temporal copy, P2 counter, r1r2, db16cyc_pause) · `3bb65bb` 11-22 14:56 **S4a** (upload diag, P2, fix (i), precise timer wait, #32) · `c5fe668` 02:21 S3 default flips · `90e7ccd` 01:50 checkpoint (batches 1-2, exit fix, codegen options) · pre-sprint: `2897c31 47b59e0 5dc986f 7c69781 b71efb4 0fd6724 f7c8f5e 05ebaec` (Oct 7 and earlier).

**`git show --stat`:**
- `5350b1d`: 13 files, +1027/-15. include/rex/{codegen/config.h 1, graphics/d3d12/command_processor.h 19, graphics/d3d12/deferred_command_list.h 3, graphics/shared_memory.h 13, system/xmemory.h 29}; src/{codegen/builders/system.cpp 8, codegen/config.cpp 2, graphics/d3d12/command_processor.cpp 103, graphics/d3d12/deferred_command_list.cpp 404, graphics/d3d12/shared_memory.cpp 75, graphics/primitive_processor.cpp 6, graphics/shared_memory.cpp 138, system/xmemory.cpp 241}.
- `b0bd3b4`: 4 files, +424/-1. rexglue-sdk → 5350b1d; rexlego/CMakeLists.txt +22; rexlego/src/gpu_native/memory_watch.cpp +6; rexlego/src/gpu_wait_backoff.cpp +395 (new).
- S4a for reference: `3bb65bb` 5 files +268/-7; `1bd322e` SDK pointer + gpu_native/shaders.cpp +229/-11.

**`git status --short`:** DimensionsRecomp ` m rexglue-sdk` (the simde content inside) and ` M thirdparty/plume`; rexglue-sdk ` m thirdparty/simde`. Nothing untracked, nothing else. Dirty trees: **plume** (detached at e0c8871; plume_d3d12.cpp, plume_d3d12.h, plume_vulkan.cpp modified) and **simde** (HEAD 71fd833 = gitlink; simde/x86/sse.h modified). Both intentionally uncommitted (SESSION2 L3310).

**Integrity:** HASHES "after" = worktree = committed blobs, 16/16 (scratch/hashes-out.txt §A; memory_watch.cpp and CMakeLists.txt after LF→CRLF). COMMIT-CHECK.md (05:57): worktree == HEAD == snap1 for 773 + 1347 files; diff-tree = HASHES, no extras; extended WARN 1 (SDK `thirdparty/moltenvk`: 8 include entries differ from snap1) (L8, L14-17, L25-28, L53, L108-110). `git ls-files --eol`: CMakeLists.txt, memory_watch.cpp, shaders.cpp `i/lf w/crlf`; gpu_wait_backoff.cpp `i/lf w/lf` (misc2.txt L1-23). Notes and scripts are not pushed; Agent 1 stages the export in `build/agent1/perf-export/` (SESSION2 L3311).

## 2. New switches

Defaults: `git grep -n` on the committed trees (scratch/lines.txt). Completeness: `git diff -U0 c5fe668 5350b1d` and `git diff -U0 08933a7 b0bd3b4 -- rexlego`, filtered for cvar/getenv/option/define (scratch/switchdiff.txt): nothing else. Rating = S4-DRAFT §1 row (line), which cites Agent 10's b2r rows.

**SDK @5350b1d** (cvars unless noted)
| # | switch | default (definition) | batch | purpose | rating | tested |
|---|---|---|---|---|---|---|
| 38 | `timer_queue_precise_wait` | false, kInitOnly (src/core/timer_queue.cpp:31) | S4a | high-res waitable timer in TimerQueue | SAFE off; caveats (a)-(f) before a flip (L259) | W5b d11p |
| - | `REX_TIMER_WAIT_BLOCKING` | env, presence-only (timer_queue.cpp:59) | pre-S4 | blocking TimerQueue wait | existing | W5b d11t |
| 7 | `shared_memory_upload_hash_log` | false (src/graphics/d3d12/shared_memory.cpp:40) | S4a | per-frame upload-hash log | SAFE; functional runs only (L206) | not timed |
| 8 | `shared_memory_single_hold_rearm` | false (src/graphics/shared_memory.cpp:34) | S4a | P2: one global-lock hold per re-arm | SAFE; ON output-identical (L207) | W6 p2/p2f/p2fc |
| 5 | `physical_protect_hold_global_lock` | false (src/system/xmemory.cpp:46) | S4a | fix (i), Protect race | SAFE; ON is a correctness change (L204) | W6 p2f/p2fc |
| 4 | `physical_protect_keep_watch` | false, kInitOnly (xmemory.cpp:55) | S4b | C1 v3 keep-watch; needs #5 ON | OFF SAFE; ON SAFE to test (L203) | W6 p2fc |
| 4 | `physical_protect_keep_watch_verify` | false, kRequiresRestart (graphics/shared_memory.cpp:43) | S4b | C1 verify, functional only | as #4 | p2fc: false |
| 11 | `shared_memory_upload_nontemporal_copy` | false (d3d12/shared_memory.cpp:50) | S4b | M1 non-temporal upload copy | SAFE; output-identical (L210) | not timed |
| 18 | `d3d12_submit_split_kb` | uint32 0 = off, kInitOnly (d3d12/command_processor.cpp:109) | S4b | R1: split end-of-frame submit | SAFE test bed, no win alone; OFF on native (L222) | W7 not run |
| 20 | `REX_D3D12_DEFERRED_COUNTERS` | compile-time 0 (d3d12/deferred_command_list.cpp:21-27); no filter cvar | S4b | R2 step 1 counters | SAFE (L224) | none |
| 26 | `db16cyc_pause` | codegen toml, false (src/codegen/config.cpp:129-130; `rexlego/legodimensions_config.toml`) | S4b | db16cyc → `_mm_pause`; needs regen | OFF SAFE; ON after 4 gates (L237) | W10 not run |
| 32 | none, **always on** | d3d12/pipeline_cache.cpp:564 | S4a | warm-boot pipeline fix | output-identical (L248) | functional |
| P2c | none, **always on** | d3d12/command_processor.cpp: `memexport full-buffer Nx (total M)` on the slow-frame line (only with `slow_frame_log_ms`) | S4b | memexport fallback count | SAFE (L207) | none |

**DimensionsRecomp @b0bd3b4 (rexlego)**
| # | switch | default (definition) | batch | purpose | rating | tested |
|---|---|---|---|---|---|---|
| 2 | `LEGO_NATIVE_SHADER_MISS_CACHE` | env, unset/0 = off; forced off by `LEGO_DUMP_MISSING_SHADERS` (gpu_native/shaders.cpp:209, 223-224) | S4a, native | shader-miss stopgap cache | SAFE; output-identical (L201) | W8a, after break |
| 24 | `LEGO_GPU_WAIT_BACKOFF_US` | env, unset/empty = off; 0 = yield; Q>0 = sleep Q µs, max 2000 (src/gpu_wait_backoff.cpp:123) | S4c | GPU-wait back-off, Xenos only | OFF SAFE; ON SAFE to test (L235) | W9 q0-q500 |
| 24 | `LEGO_GPU_WAIT_SPIN_US` | env, 30, max 200 (:125); only with back-off ON | S4c | spin before yield | with #24 | 30 in W9 |
| 28→24 | `LEGO_GPU_WAIT_STATS` | env, unset = off (:129) | S4c | P1 counters every 5 s | with #24 | functional |
| 24 | `LEGO_GPU_WAIT_HOOK_GETDATA` | define 0 (:68-69); CMakeLists.txt:187 sets 1 when `NOT LEGODIMENSIONS_NATIVE_GPU` | S4c | H2/H3 hooks; pass-through while env unset (L235) | with #24 | in devoff4b |
| 30 | `LEGODIMENSIONS_SCENE_WALK_PROBE` | CMake option OFF (CMakeLists.txt:159; FATAL_ERROR :161-162) | S4c | scene-walk probe build | diagnostic only (L241) | none |
| 4 | none, **always on** | memory_watch.cpp +6, constinit latch (§21 gate C) | S4b | keeps C1 off in native | with #4 | none |

**Flags:** no S4 default is ON. Default ON (S3, c5fe668): `pause_safe_order` (src/ui/rex_app.cpp:71), `audio_shutdown_detach_worker` (src/audio/audio_system.cpp:47-48). The 8 d11 cvars (batches 1-2, SDK) default off: `host_timer_resolution_ms` 0 (src/system/runtime.cpp:39), `host_timer_throttling_optout` (:42), `precise_guest_sleep` (src/system/xthread.cpp:55), `tls_bounds_fix` (:59), `wait_timeout_round_up` (src/system/xobject.cpp:35), `cs_spin` (src/kernel/xboxkrnl/xboxkrnl_rtl.cpp:51), `spinlock_pause_spin` (xboxkrnl_threading.cpp:49), `clock_lockfree` (src/core/clock.cpp:26). `framerate_limit` 0 (src/graphics/command_processor.cpp:64).

## 3. Third-party rebuild (scripts and patches are tracked)

- **plume:** `DimensionsRecomp/tools/gpu-aot/prepare_plume.py` (5,505 B), PIN `e0c8871b930dc1a6544bf457f2348c456b9d7e13` (L9). Usage (argparse L64-67): `python tools/gpu-aot/prepare_plume.py [checkout] [--check]`; checkout defaults to `thirdparty/plume`; `--check` = "Verify only; do not modify the checkout". Refuses unless HEAD == PIN (L89-91), then applies in order, skipping applied ones (L70-78, L93-110), `tools/gpu-aot/patches/plume-{lego, state-cache, vulkan-readback, buffer-address, adapter-query, graphics-read, winsdk-compat}.patch`. winsdk-compat (640 B, from a0bdaa7) = S1+p2: `static_cast<D3D12_HEAP_TYPE>(5)` for GPU_UPLOAD, because this host has Windows SDK 10.0.22621 (patch L9).
  - Commands: `git -C DimensionsRecomp/thirdparty/plume checkout e0c8871b930dc1a6544bf457f2348c456b9d7e13`; then in `DimensionsRecomp/`: `python tools/gpu-aot/prepare_plume.py`, then `... --check`. Today: exit 0, "PASS: public Plume e0c8871b... with native fence/resize/command-allocation fixes, opt-in state cache and Vulkan readback".
- **simde:** `DimensionsRecomp/rexglue-sdk/scripts/prepare_simde.py` (4,135 B), PIN `71fd833d9666141edcd1d3c109a80e228303d8d7` (L9) = SDK gitlink; argparse L57-60. Patch `rexglue-sdk/patches/simde-native-m64-stream.patch` (1,122 B; `simde_mm_stream_pi` in simde/x86/sse.h, native `__m64` on Windows Clang). In `rexglue-sdk/` (patches/README.md L5-10): `python3 scripts/prepare_simde.py`, then `... --check` (`python` works here). Test: `python3 tests/regression/test_prepare_simde.py /tmp/rex-simde-preparation` (README L22-24). Today: exit 0, "PASS: SIMDe 71fd833d... with native __m64 streaming-store fix".

## 4. Bins and arms

`build/agent2/<name>-bin/`: Release, game x86-64-v3, SDK x86-64-v2; Xenos 8 files, native 9 (+amd_fidelityfx_dx12.dll). sha16: scratch/hashes-out.txt §B; content: MANIFEST L1-2.

| bin | MANIFEST sha16 | content |
|---|---|---|
| devoff1 | 1E81AA5E0C8A4309 | S1, 11-21 21:07 |
| devoff2 | B87DC2D2CA22379F | S2 (STATE-S2-2315), 11-21 23:18; W4c d0 |
| devoff3 | B9C5175DA1904235 | S3 (STATE-S3-0241), 11-22 02:44; W5 base |
| devoff4 | 16DCC9399239E577 | **S4a** = S3d + #7 #8 #5 #38 off + #32, 11-22 13:31; **W5b** |
| devoff4b | DE11A914079D7DF7 | **S4b** = S4a + C1 v3, M1, P2c, r1r2, #26 + S4c #24/#30, all off (STATE-S4b-1950), 11-22 20:49; **W6, W9** |
| devoffB | 8709476FF4778768 | codegen B from S2 (batch-nolr), 11-22 02:40; W4c B |
| native / native2 / native3 | 91F2F817B0D6D205 / D6E7F14F23373FA7 / B50FE8D4A16565DA | native S1 / S2 / S3 |
| native3d | 368F9CE650EC56CE | S3 + draw.cpp (STATE-S3d-0342), fp 335ff2d47268f3a1 |
| native4 | 00D33D4FFB46776D | S4a + #2 off, fp 5e3ff55de10f4f64 |
| native4b | B63769FE46CC0459 | S4b + C1 memory_watch + S4c CMake, fp 9b40acbbef4c57b3, 11-22 22:40; not pinned (§6) |
| nativeB | E5CBF30A6132B00E | S3d + codegen B, fp 81d1c3a71be3c096 |

**Arms** (`bench/agent8/run/matrix-window*.json`): all have `framerate_limit=0`, driver `drivers/thread-cpu.ps1`, `sys_csv` true; 5 s settle + 55 s warm-up from the first frame + 50 s measured (matrix-window6.json L27); one unscored cold run per window. GO lines and matrix sha256: `build/agent8/w-followup/PROPOSAL.md` L19-22.

| window (matrix sha16, lines) | bin | arms | GO | runs pass 1 / 2 (`build/agent8/matrix/`) |
|---|---|---|---|---|
| W6 (E50D791B, L32-49) | devoff4b | s0: none; p2: `shared_memory_single_hold_rearm=true`; p2f: + `physical_protect_hold_global_lock=true`; p2fc: + `physical_protect_keep_watch=true`, `physical_protect_keep_watch_verify=false` (arms f, fc defined, not run) | `only=s0,p2,p2f,p2fc repeats=5` | 20261123-0009 / -0313 |
| W9 (CE0AD757, L32-45) | devoff4b | off: none; q0/q125/q250/q500: env `LEGO_GPU_WAIT_BACKOFF_US`=0/125/250/500 + `LEGO_GPU_WAIT_SPIN_US=30` | `only=off,q0,q125,q250,q500 repeats=4` | -0108 / -0401 |
| W5b (23575AAA, L32-50) | **devoff4** | d11: `host_timer_resolution_ms=1` + true for `host_timer_throttling_optout, precise_guest_sleep, wait_timeout_round_up, cs_spin, spinlock_pause_spin, clock_lockfree, tls_bounds_fix`; d11t: + env `REX_TIMER_WAIT_BLOCKING=1`; d11p: + `timer_queue_precise_wait=true` | `only=d11,d11t,d11p repeats=6` | -0155 / -0451 |
| W4c (E2E3E4DA, L30-33) | d0 devoff2, B devoffB | none | `only=d0,B repeats=6` | -0239 / skipped |

(Superseded: the formal read-outs are final; see RESUME §5. The S4-DRAFT line cites here are from 06:19.) Runner summaries, not readouts (S4-DRAFT L402, L406, L408, L409): **W6** p2fc −11.8% [−14%] median frame time, +21% [+22%] fps, −0.22 [−0.27] core vs s0, faster in 10/10 rounds; p2, p2f flat; readout must check p2fc p99.9 (6.49 vs 5.74 ms). **W9** q500 −0.70 to −0.79 core (−28 to −31%), fps +1%, p99 4.62 vs 4.98 ms; q125/q250 smaller and unsteady in pass 2; lean q500. **W5b** d11p −0.20 [−0.21] core, fps flat; d11t −0.23 [−0.21] core but fps −0.8% in pass 2; lean d11p. **W4c** B +1.3% median, −0.4% fps; lean drop B. Readouts in progress: `build/agent8/readout/w-followup/{a7,mine,pool,audit}`.

## 5. Launcher

- **Night launcher `bench/agent5/launch/`** (installed since 07:33:57): README.md B7CEBD635D847D4C (0058C8F61EEAA9F2 during the night; same 271 lines, the README cites below hold), RUN-NIGHT.cmd D7A0362BE90C12B4 (unchanged), run-night.ps1 565D30D40DC5025A (16B90FA8654FAC08 during the night), status/pins.txt 1DEAF685AF8D641F. pins.txt L1: "pinned 2026-11-22 23:47:20 by launcher pid 19960; any change refuses the next window". L2-20 pin **19 files**: RUN-NIGHT.cmd, run-night.ps1; `bench/agent8/run/` boot_report.py, common.ps1, drivers/{io-counters.ps1, LdSys.cs, pso-stats-at-end.ps1, sys-csv.ps1, thread-cpu.ps1}, frame_summary.py, gate_logdiff.py, matrix_recheck.py, run-matrix.ps1 (FEDCEB13 in pins.txt; 1A522CDFE9DC36F8 since the install), run-timing.ps1, sys_summary.py, timing-env.ps1, winhelper.cs; `harness/legodimensions.toml` (B763DABB), `harness/nvml.cs` (9F6E6E3B). All 19 matched at 06:12 (hashes-out.txt §D L106-124); since the install, run-night.ps1 and run-matrix.ps1 differ. pins.txt is only a record: the next start re-hashes the files (run-night.ps1 L967), rewrites pins.txt once its start checks pass (L973) and compares in memory (L688, L739, L900), so nobody re-pins by hand. README: pins L141-149; no start after 06:45, exit 07:30 (L12, L46-47); screensaver "(None)" L53, hand restore L81-84; env allow-list L119; session/AC L157; quiet gate L186-196. last-result.txt 05:30:42 (W5b pass 2 done); the launcher ended at 07:30:14 at its deadline (exit 0), restored the screensaver and released keep-awake (RESUME §8).
- **The problem (SESSION2 L3215-3221):** at 23:47:20 `Set-ScreensaverNone` (run-night.ps1 L461-467; line numbers in this bullet are the night's 16B90FA8) removed `HKCU\Control Panel\Desktop` `SCRNSAVE.EXE` (L465; its value had been ''). run-matrix.ps1 L417 reads `$scr.'SCRNSAVE.EXE'` under `Set-StrictMode -Version 2` (common.ps1 L4; run-night.ps1 L30), which throws on a missing value, so `-PlanOnly` exited 1 and the first GO was refused at 00:03:40. Fixed by hand at 00:05:37 (SCRNSAVE.EXE = '' re-created; no pinned file touched). Restore at exit: L469-480. Installed at 07:33:57, after the launcher ended (07:30:14); Agent 8 read the runner hunk (OK), and Agent 10 rated the delta (06:30) and the install tooling (06:45) SAFE (SESSION2 L3220, L3304, L3312; `build/agent10/t27/scrnsave-delta.md`).
- **Fix `build/agent5/scrnsave-fix/`** (Agent 5, task #26): patch run 06:11:37-47; installed at 07:33:57 (`install-log.txt`; the installer refused at 06:36 while the night launcher ran, as designed, and at 07:33:42 because its process check matched pid 33304, not the launcher, which had ended at 07:30:14: Agent 10's N-4, a fail-safe false alarm; the re-run at 07:33:56 installed). Scripts: patch-scrnsave.ps1 580B166BEEFF9FC0 (edited 06:08; ED8BC9530573A898 at 05:58), test-scrnsave.ps1 1728215653013A5A, e2e-driver.ps1 50C9D6DE05DBCC81. Outputs: scrnsave-fix.diff 425833AC9185A86D and hashes.txt BB7CF7CC79118F33 (18 entries, all equal to my re-hash at 06:12). The patch refuses unless the 8 sources have their base sha256 (L12-21: run-matrix FEDCEB13, run-night 16B90FA8, README 0058C8F6, make-run-day 17413F8A, run-day D86F6DE0, run-day.diff 54E35C18, README-DAY 9D131EB1, RUN-DAY.cmd 4B5489B4), and it writes only in its folder (L1-6). It passed at 06:11, so the installed files were unchanged then. It also covers condition 1 and N1-N3 of `build/agent10/t27/day-draft-rating.md` (L1-2). New files (scratch/diffstat.txt):
  - new/run-matrix.ps1 1A522CDFE9DC36F8: L417-419 (+3/−3) read the 4 screensaver values through `Get-P` (PSObject.Properties), so a missing value reads as '' (patch L48-71).
  - new/run-night.ps1 565D30D40DC5025A: sets SCRNSAVE.EXE to '' instead of removing it and logs the value; restore removes it again if it was missing at the start (+3/−2; L73-97).
  - new/README.md B7CEBD635D847D4C (L100-116); new/make-run-day.ps1 4A96B0B947D0796B (new night sha; repo-relative diff paths, N1; L118-137); new/day/run-day.ps1 B67EBD6C2C9A378C and new/day/run-day.diff F5EC971E843DE9E4 (regenerated); new/README-DAY.md A36574ED62088080 (N1, N2, note; L139-150; superseded by the day draft's README-DAY 9739BCF8952146D9); new/RUN-DAY.cmd B08645E9D4296AC1 (N3, CRLF kept; L152-164).
  - Tests use a scratch key `HKCU:\Software\Agent5-scrnsave-test\Desktop` and a fake `[LdNight]`; `-E2E` runs `run-matrix.ps1 -PlanOnly` with redirected registry reads (test-scrnsave.ps1 L1-8). Tests: before the install 45/45 (`-Set new -E2E`, 06:14:40, `results/summary-new-061440.txt`); after it 45/45 (`-Set installed -E2E`, 07:34:45, `results/summary-installed-073444.txt`), plus go 16/16 and test-day 27/27 (§0 item 7). The install changed 2 pinned files (run-night.ps1, run-matrix.ps1); the next start pins the new hashes by itself (see the night-launcher bullet above).
- **Day draft `build/agent5/day-draft/`** (first version 11-22 22:46-23:13; regenerated on Nov 23 from 07:34; hashes as Agent 10 verified them at 07:56): README-DAY.md 9739BCF8952146D9, RUN-DAY.cmd B08645E9D4296AC1, STOP-LAUNCHER.cmd CE27332F354B1DBB, launcher-ctl.ps1 6DDE3150B72D6B0D, make-run-day.ps1 4A96B0B947D0796B, run-day.diff 3D0E8753683A17AA, run-day.ps1 B67EBD6C2C9A378C, test-day.ps1 410FB2ECBA7B72B9, `results/`, `status-dryrun/`. run-day.ps1 is generated from the installed run-night.ps1 565D30D4 and has the fixed SCRNSAVE code (Set-ScreensaverNone L462, restore L470; StrictMode L30); its host values match the night launcher's (L48, L62, L170, L712). Conditions: 1 (the SCRNSAVE fix) closed at 07:56 (`build/agent10/t27/scrnsave-delta.md` §4-§5); 2 (install into `bench/agent5/day/`, which doesn't exist yet, only after both ratings; README-DAY L138-141) and 3 (Agent 11's rating, with Agent 10, a board task after the break) are open.

## 6. Baselines and a new PC

- **Baselines:** Xenos base devoff3 (S3d line; W5, `build/agent8/matrix/20261122-1756`; S4-DRAFT L393, L401); s0 devoff4 (W5, W5b) and devoff4b (W6 s0, W9 off); W4c d0 = devoff2. Native n-rows: native3d `build/agent8/matrix/20261122-0452` (0452-n0-r1, 0454-n2-r1, 0456-n3-r1), replaced by native4b's n0/n2/n3 after the re-pin (REPIN.md L90). Fingerprint pins: native4 5e3ff55de10f4f64 (current), native3d 335ff2d47268f3a1 (frozen), nativeB 81d1c3a71be3c096 (REPIN.md L14-22).
- **Re-pin `build/agent4/repin/`:** REPIN.md; repin_check.ps1 (dry run by default; `-Go` needs `-W4bDone`, SESSION2 L2550); matrix-repin-native4b.json, -native4b-boot.json, -packhit.json; superseded/; **pin-native4b-2243.txt** (0 FAIL/0 WARN; built = recomputed = 9b40acbbef4c57b3 from 271 inputs listed at CMakeLists.txt L604-787; MANIFEST B63769FE46CC0459). Steps 0, 1, 1b, 2, 3 done; **step 4 passed**: the boot check rpb0 (`build/agent3/runs/rpb0-20261123-0617`, fingerprint 9b40acbbef4c57b3) and the 4-run matrix rpm4 (`build/agent3/runs/rpm4-20261123-0620`; check log `build/agent3/s4b/logs/rpm4.3b.txt`), PASS on every section 3(b) check (`build/agent4/HANDOFF.md` L18); **step 5 (Agent 1's announcement) is left**, then the repin_check.ps1 fixes in Agent 4's order (RESUME §7 step 2). `$PINS` changes only after step 5 (REPIN.md L43-55; on a fail it stays native4); `$PINS` is not in `bench/agent8/run/*.ps1|*.py`, only cited at REPIN.md L53. nativeB4b and native4bp not built (REPIN.md L94-111). native4b starts PSO-cold: its fingerprint rejects native4's recipes/seed (SESSION2 L3148-3162). Older copies: `build/agent9/repin/`, `build/agent9/make-repin.py`.
- **A new, stronger PC:** "a new PC needs new baselines" (SESSION2 L3303, L2981). Even here, arms are compared only within one window and host state (PROPOSAL.md L92; S4-DRAFT L385-390: after the 08:29 update, Intel DTT ext 9.1.10501.3322, IPF 3.4.1009.0, KB5132057, OS build 26300.10075; DTT runs the power limits behind the slow state); nothing may compile during a window (PROPOSAL.md L87-90). To do: rebuild or copy the bins and check MANIFESTs (matrices hard-code bin paths and manifests; GO lines pin each matrix sha256); re-measure every arm from s0/off with the cold run; re-check the values below; the native fingerprint carries over only with byte-identical inputs (§0.4); re-record PSO/seed caches (`-SeedXenos build\agent3\seed\devoff2-214` must match the bin, S4-DRAFT L248, L252); the -j8/-j10 Below Normal limits and S4-DRAFT §3 times (L419-431) are this host's.
- **Host:** i7-1255U, 2 P + 8 E cores, 12 logical (perf-notes/agent11-kernel.md L119, numbering L452); GeForce MX570 1,934 MB (perf-notes/agent3-run-harness.md L356); Windows NT 10.0.26300.

| hard-coded value | file:line |
|---|---|
| quiet-gate processes MsMpEng, OfficeClickToRun, CrossDeviceService | bench/agent5/launch/run-night.ps1 L48 |
| MinRamGB 6, MinDiskGB 6, QuietCores 0.1, RelaxMaxCores 1.2, RelaxSpread 0.2, DeadlineSlackMin 10 | run-night.ps1 L62; README L186-196 |
| GiveUpMinutes 120, StrictMinutes 30, MaxRunHours 14, LatestStartTime 6.75, exit 07:30 | run-night.ps1 L16-17, L46-47 |
| disk check on C:; `powercfg /getactivescheme` | run-night.ps1 L169, L711 (L710 in the night's 16B90FA8) |
| runs refuse below 6 GB free RAM | bench/agent8/run/run-matrix.ps1 L401; run-timing.ps1 L50; first-boot.ps1 L15; common.ps1 L29 |
| scored window ≥ 60 s after first frame | run-matrix.ps1 L59, L308 |
| slow state: E-core clock < 800 MHz | matrix_recheck.py L203 (used L113, L261) |
| P/E core classes; best_efficiency GUID 961cc777-2547-4f9d-8174-7d86181b8a7a | drivers/LdSys.cs L5-25, L619; drivers/sys-csv.ps1 L131 |
| NVIDIA NVML GPU 0 (else warning, no gpu.csv) | drivers/thread-cpu.ps1 L59-84; harness/nvml.cs L1-32 |
| WER dump paths | common.ps1 L204-216 |
| CPU count read at run time (not hard-coded) | run-timing.ps1 L196; first-boot.ps1 L47 |
| bin paths, MANIFESTs, matrix sha256 | matrix-window*.json; PROPOSAL.md L19-22 |
| 19 launcher pins; native fingerprint pins | pins.txt L2-20; REPIN.md L14-22, L53 |
| Windows SDK 10.0.22621 workaround | tools/gpu-aot/patches/plume-winsdk-compat.patch L9 |

run-day.ps1 (B67EBD6C) repeats the launcher values at L48, L62, L170, L712.
