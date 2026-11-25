# FINAL defaults set (M2, build/agent2/final): rating

M10, 2026-11-25 07:07. Read-only review plus offline checks at BelowNormal. No builds, no compiler processes, no game runs, nothing written outside build/agent10.

## Files rated

| file | sha256 (16) | bytes |
|---|---|---|
| FINAL-DEFAULTS.diff | 955543F5E2E5F4F4 | 20258 |
| DEFAULTS-TABLE.md | 14B412516D7C09A1 | 8501 |
| check-defaults.py | 6C7A00EBF5BD8F00 | 8273 |
| BUILD-PLAN.md | B87ABA79460F5C80 | 9733 |
| verify-diff.py | 9AAF4BB71105A511 | 2356 |
| predict-fingerprint.py | 1792CDCB900CB86F | 1615 |

All files are in `build/agent2/final/`.

## Base

- q500-default-rating.md (DB5D1282);
- readout-night-xcheck.md (25BF9B1C);
- r19-build-method.md (A813D340);
- c1-verify-fix-rating.md (AFBFFBDF);
- matrix-windowC.json (00E3EE97), arm `win3`.

## Verdict

**SAFE-IF.**

- **Diff and code: SAFE.** Every default equals the timed win3 arm. The q500 hunks are M9's, byte for byte. The proof-line and miss-cache hunks change no behaviour except one log line each.
- **Build plan: ACCEPT-IF D1-D7.** The rexruntime recompile extension and the full-SDK fallback are both acceptable under D2 and D3.
- **N-A for native: CONFIRMED.** It is exactly W8a `mc`: the native4b exe with the miss cache ON, on the old snap1-sdk DLLs. N-B stays out until it has its own functional gate and timing pair.
- **The final bins need F1-F7 before a confirmation window.**

## What I checked

### Keys vs the timed arm

matrix-windowC.json `win3` sets 13 cvars plus `framerate_limit=0`, and env BACKOFF 500 / SPIN 30. The diff's changed `REXCVAR_DEFINE` defaults are:
- `clock_lockfree`, `timer_queue_precise_wait`, `shared_memory_single_hold_rearm`, `physical_protect_hold_global_lock`, `physical_protect_keep_watch`, `wait_timeout_round_up`, `precise_guest_sleep`, `tls_bounds_fix`, `cs_spin`, `spinlock_pause_spin`: true;
- `host_timer_throttling_optout`: true;
- `host_timer_resolution_ms`: 1.

That is 12 keys. `physical_protect_keep_watch_verify` stays false, which is the arm's value. `framerate_limit` is not changed: it is the bench's uncapped setting in every arm, s0 included, so not shipping it is correct. The q500 default is 500 and spin stays 30. **Every key equals win3.** CG26 stays off and P2 stays in, as in xcheck S3 option (a).

### Diff integrity

My own re-check is `scratch-final/verify_final.py`. It works in a copy under build/agent10, which is then deleted.
- The 11 before-files in the live tree are byte-identical to `build/agent2/snap1`.
- `git -c core.autocrlf=false apply` gives rc 0.
- All 11 after-hashes equal `final/work/new`, which match the BUILD-PLAN table.
- The `gpu_wait_backoff.cpp` section is identical to `q500-default.diff` (28F0D1DE). So all of my q500 rating conditions carry over.
- I did not run M2's verify-diff.py, because it writes under final/work.

### Proof-line hunks

- **runtime.cpp `LogFinalDefaults`:**
  - It is called once, in `Runtime::Setup`, inside `if (!tool_mode_)`, after `ConfigureHostTiming`.
  - It checks registration (`GetFlagInfo`) before reading.
  - `kSources` matches `enum class Source`: kDefault, kConfig, kEnvironment, kCommandLine, kRuntime.
  - It does not call into the registry while holding its lock. The cost is one startup line.
- **shared_memory.cpp `FinalDefault`:**
  - It logs once, at the end of `InitializeCommon`.
  - It has no registration check. An unknown name prints `name=(default)` (GetFlagSource returns kDefault for unknown names), so check-defaults fails closed (N2).
  - Cross-DLL: rexgpu-xenos now calls `rex::cvar::GetFlagByName` and `GetFlagSource`. Both are exported by the devoff4b rexruntime.dll A33801D1. Old rexgpu-xenos imports 115 names from rexruntime.dll, and these 2 names are new (D5).
- **Miss cache (shaders.cpp):**
  - The old code returned: set, non-empty and not "0", and not capture.
  - The new code returns: if set, value != "0", otherwise the build default (1); and not capture.
  - For W8a `mc` (env `LEGO_NATIVE_SHADER_MISS_CACHE=1`) both give ON, so behaviour is identical. Only the new one-time INFO line is added.
  - `_dupenv_s`, `strcmp`, `free` and REXLOG_INFO are already used or included in the TU.
- **Native fingerprint:** predict-fingerprint.py (read-only) recomputes the pinned `9b40acbbef4c57b3` from the 271 current inputs, then predicts `1616ce65e973c583`.
  - Bench impact: each W8a run dir has its own `cache/` ("no startup pipeline recipes yet" in 0402-mc-r1), so every bench run already starts without recipes. The fingerprint change does not change bench timing.
  - User impact: one cold start after the update.

### check-defaults.py modes

Logic:
- `xenos` requires exactly one of each Final-defaults line, every key at the new value with source `default`, the 1 ms, C1, TimerQueue and back-off ON 500/30 lines once each, no OFF line, and none of the 5 bad strings.
- `off` requires the old values from any source, the OFF line, and no 1 ms, C1 or TimerQueue line.
- `native-old` forbids the runtime line and the timer, C1 and TimerQueue lines, and requires the miss-cache line once.
- The PAIR regex fails closed on `unregistered` or a missing source.

My runs:
- `--mode legacy` on 0319-win3-r1: PASS.
- `--mode legacy` on 0317-s0-r1: FAIL (4).
- `--mode xenos` on 0319-win3-r1: FAIL (15), because that log has no Final-defaults lines.

So the tool tells the arms apart. What it can't prove (q500 R3: env unset vs env 500) is stated, and it is left to run.json `env_set` (F1).

### Build plan

- **TU-to-target mapping:** I checked it in `snap1-sdk/CMakeFiles/impl-Release.ninja`. The 8 rexruntime TUs (including rexcore's clock.cpp and timer_queue.cpp) link only into the rexruntime DLLs; shared_memory.cpp links only into rexgpu-xenos.
- **No header changes:** so the exports, import libraries and PCH are unaffected.
- **rexruntime lineage:** devoff4b's `rexruntime.dll` (MANIFEST source snap1-off) is A33801D1, the same file as `snap1-sdk/install/bin/rexruntime.dll` and snap1-on's. So snap1-sdk is the right base and ccdb for B1.

### Config

- `SaveConfig` writes only non-default values.
- The win3 run's `legodimensions.toml` contains none of the 12 keys, only `framerate_limit = 60`, which the command line outranks.
- devoff4b-bin and native4b-bin ship no toml.
- So no saved config pins the old values, and a plain launch shows `(default)`.

## Conditions

### Build (D)

- **D1 CTL legs.** Each one must reproduce the reference except the TimeDateStamp; on any other difference, STOP:
  - B1 per DLL: the 9 unpatched TUs, recompiled and relinked, must equal A33801D1 (rexruntime) and E3CB99CF (rexgpu-xenos).
  - B2: the exe must equal DFBE1D43.
  - **Add a B4 CTL leg:** the 4 native TUs, recompiled with the unpatched shaders.cpp (fingerprint stays 9b40), plus a relink, must equal the native4b exe.
- **D2 rexruntime extension.** Send me the recompile.py/relink.py diff to rate before the ON leg. The link rsp for `rexruntime.dll` must come from snap1-sdk impl-Release.ninja and must include the 2 rexcore.dir objects. The rexruntime CTL leg passing (D1) is the required proof that the extension is correct.
- **D3 Full-SDK fallback.** ACCEPT-IF a full Release rebuild of an *unpatched* fresh snap1-sdk copy (same configure) reproduces A33801D1 and E3CB99CF except the TimeDateStamp and debug-directory fields; list every differing byte range. If it does not, STOP and report. Do not ship fallback DLLs whose unpatched leg has not reproduced the reference.
- **D4 Syntax checks.** Add `shaders.cpp` (snap1-on flags) to the `-fsyntax-only` set: it has new code too (lambda, REXLOG_INFO). That makes 4 TUs.
- **D5 PE checks:**
  - exports of both new DLLs == devoff4b's;
  - new rexgpu-xenos imports from rexruntime.dll == the old 115 + exactly `GetFlagByName` and `GetFlagSource`;
  - no other import changes in either DLL;
  - the import table of the new Xenos exe == devoff4b's.
- **D6 Never write `snap1-sdk/install` or any staged bin.** Work only in fresh copies. Re-verify devoff4b-bin, devoff4b-cg26-bin and native4b-bin MANIFESTs after each staging (0 FAIL), as the plan says.
- **D7 Harness rules (BUILD-PLAN section "Harness rules", which is q500 condition 4) are installed before the first run on any new bin:**
  - new-bin off arms set `LEGO_GPU_WAIT_BACKOFF_US=off` and the 12 old cvar values;
  - expect files are per bin;
  - the default arm is named explicitly.

### Functional set before a confirmation window (F)

- **F1 devfinal-bin, plain launch on the WC light route:**
  - cvars only `framerate_limit=0`;
  - run.json `env_set` has no `LEGO_GPU_WAIT_*`;
  - `check-defaults.py --mode xenos` PASS;
  - the run is valid (no WER, no dialogs, clean exit);
  - the bin id is in run.json.
- **F2 devfinal-bin, level route** (level-l with toypad, at least 10 min, the route class win3 was never timed on):
  - clean;
  - 0 bad strings;
  - the C1 line once;
  - no stale-protection recovery.
- **F3 devfinal-bin OFF arm** (12 old values + `off`): `--mode off` PASS. This proves the user and bench off switches work on the new code.
- **F4 Optional:** devfinal-bin with explicit env 500 gives the same proof lines as F1. This documents q500 R3.
- **F5 nativefinal-bin (N-A) on the W8a route:**
  - `--mode native-old` PASS;
  - the fingerprint is `1616ce65e973c583` in the exe and in native-gpu-build.txt;
  - the MANIFEST shows rexruntime A33801D1 and rexgpu E3CB99CF;
  - shader-miss warnings are no higher than in a native4b n0 run on the same route;
  - a second launch in the same dir loads the recipes saved by the first, so the warm path works with the new fingerprint.
- **F6 nativefinal-bin with `LEGO_NATIVE_SHADER_MISS_CACHE=0`:** the line reads `OFF (LEGO_NATIVE_SHADER_MISS_CACHE set)`.
- **F7 nativefinal-bin level route:** clean.

## Findings

- **SHOULD S1** check-defaults `xenos` (and `legacy`) match only the prefix `GPU wait back-off: ON (quantum 500 us, spin 30 us)`. Require the full timed line, `...; stats OFF; GetData hook built.` (as in 0319-win3-r1). Otherwise a STATS run, which must never count as timing, or an exe without the GetData hook could still PASS.
- **SHOULD S2** = D1's B4 CTL leg. BUILD-PLAN B4 has none, unlike B1 and B2.
- **SHOULD S3** = D4 (shaders.cpp syntax check).
- **NIT N1** The miss-cache line is logged on the first `ShaderMissCacheEnabled()` call, that is, the first placement-shader miss path. On a route with no miss, `native-old` FAILs falsely, but it fails closed. Use the W8a route for F5.
- **NIT N2** `FinalDefault` in shared_memory.cpp has no `GetFlagInfo` check (runtime.cpp has one). It fails closed in check-defaults.
- **NIT N3** `native-old` does not forbid a `Final defaults (GPU):` line. Add a 0-count check; it would catch the new rexgpu being staged by mistake.
- **NIT N4** verify-diff.py and predict-fingerprint.py hard-code an absolute WS path under the user profile, and verify-diff.py writes and deletes `final/work/verify`. That is fine for M2; others should not run them as they are.
- **NIT N5** DEFAULTS-TABLE says the before-files are byte-identical "in live HEAD". I verified the live working tree == snap1, not the HEAD blobs.
- **INFO** The defaults now hold from DLL load, before command-line parsing. In win3 they took effect after parsing. Only code that runs before the parse can see a difference (startup only); F1 and F2 cover it.
- **INFO** The C1 verify-mode fix (c1-verify-fix-rating) is not in FINAL. verify stays false, as timed. Don't use `physical_protect_keep_watch_verify=true` on devfinal-bin for proofs.
- **INFO** Packaging: the native release folder must carry the old DLLs (N-A). F5's MANIFEST check and N3 catch a mix-up.
- **INFO** Scope (xcheck S2) is carried correctly in DEFAULTS-TABLE: the idle and battery cost of the 1 ms timer plus throttling opt-out is unmeasured.

## Read / Sent

- Read:
  - all 6 files;
  - the after-tree runtime.cpp and shaders.cpp;
  - snap1 cvar.h and cvar.cpp (Source enum, GetFlagSource, SaveConfig);
  - snap1 shaders.cpp (old `ShaderMissEnvironmentSet`);
  - matrix-windowC.json and the W8a matrix.json;
  - win3 and mc run dirs.
- Ran (read-only):
  - `scratch-final/verify_final.py` (PASS);
  - predict-fingerprint.py;
  - check-defaults.py in 3 combinations;
  - pe_scan exports and imports;
  - the ninja target mapping.
- Sent: verdict plus sha8 to the Overseer.
