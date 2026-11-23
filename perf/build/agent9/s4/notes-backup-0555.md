> **RESUME (session 3: task #23 = S4 analysis, in progress; task #8 done; this block updated 05:05).** Task #23's notes
> (S4.x) come right after the run spec, then session 3 (S3.x), session 2 and the recipe; session 1 is archived at the end.
> - **Task #23, session 3 part 3 (Agent 1, about 04:55): S4 analysis.** Read-only on the trees, <= 2 threads, no builds,
>   no game runs; notes only from 08:30. Mine: `build/agent9/**`, `bench/agent9/**`, this file; up to 1 subagent (1 used:
>   D `4b8ebd88-9a37-497b-b3e5-c7f72eaea7f7`, step 2, writes only `build/agent9/s4/scene-walk/`, report due 06:20).
>   Steps: 0 review Agent 2's S3e clones (**done: OK sent about 05:05 to Agents 2 and 1, S4.0**); 1 render-thread GPU-wait
>   spin (host writers of device+11024/11036 and their rate; ranked S4 proposals with CPU saving, fps effect,
>   output-identical argument, files, risk, default OFF, test plan, Agent 10's checks; S4.1); 2 main scene walk (what
>   sets its per-frame work; call-count probe spec; subagent D; S4.2); 3 keep the S4 codegen ranking current and mark the
>   items that only save CPU while the render thread is GPU-bound (S4.3). Send Agent 1 a 6-10 line summary by about
>   07:00, then `@@done 23: ...`.
> - **Task #8, session 3 (Agent 1, 02:00), done (`@@done 8` sent 04:46):** delete QUIET (done), support Agent 2's build B
>   and the B game gate (rollback = recipe step 9), optional 9-key T8 run at <= 2 threads (done, S3.3). B passed the
>   front-end gate at 03:31 (S3.6); codegen changes still need a new task from Agent 1.
> - **Added by Agent 1 (03:31), answered about 04:19 (S3.8):** whether B's -10.5% `.text` shows up in main-thread or
>   GPU-thread time (no: it is inside the noise of a 1.3 rounds/s profile, and the render thread is a GPU-wait spin), and
>   the S4 codegen candidates. Agent 7's own tables match mine. Agent 7's write-tracking question (+1.19 ms/f): not B
>   (host DLLs identical, sub_82B55588 has the same calls and memory ops); reply sent 04:46 (S3.8).
> - **Added by Agent 1 (03:34):** review Agent 2's nativeB scripts before the build (done; OK sent 03:50, S3.7). After the
>   build, the static check of nativeB against native3d-bin with Agent 10 (task #17 item 1a): mapcmp, warnings, MANIFEST
>   (batch-nolr, END line, sha256s), the native GPU fingerprint against A, and a host-register re-scan of S3d's draw.cpp.
>   **Done 04:42: all PASS (S3.9).** The fingerprint differs from A's by design (it hashes the codegen config and 12
>   generated files; `build/agent9/fpcheck.py` shows those 13 are the only differing inputs).
> - **SG rules:** only Agent 2 builds (<= -j10); every Agent 9 job <= 2 threads (slot scripts); game runs only in Agent 8's
>   slot (functional only); no builds or game runs from 08:30 (window 4 waits for the user, who is asleep until about
>   10:00: questions go to Agent 1). Checkpoint already pushed: game `a0bdaa7`, SDK `90e7ccd`.
> - **State (05:05): task #23 step 0 done, steps 1-3 open; task #8 complete (`@@done 8` 04:46).** nativeB staged 04:34:06
>   (`build/agent2/nativeB-bin`, exe `01C4D5A3E36FAC50`), item 1a all PASS (S3.9). Profile answer and S4 list sent about
>   04:19 (S3.8); Agent 7's tables match; write-tracking reply sent 04:46. nativeB scripts OK 03:50, rb-chain.ps1 -GuardOnly
>   (`65A2CFE4`) OK 04:06 (S3.7). native3d-bin staged 03:46 (S3d, fingerprint `335ff2d47268f3a1`). RESUME check
>   PASS (S3.1). Rollback trees `install/rb1-nolocal` and `install/rb2-nomusttail` are
>   pre-staged (S3.2), with re-pinned copies of Agent 2's tools in `build/agent9/repin/` (S3.5). B's tools reviewed: **ok**
>   (S3.4). **B built clean and was staged at 02:40** (`build/agent2/devoffB-bin`, exe `C3F8686EBDD83340`); the static A/B
>   map check passes (S3.5). **B boot PASS** (Agent 8, 02:49). **B front-end gate PASS** (Agent 10, 03:31; partial
>   coverage: no level, pause, cutscene, save/Quit or toy pad). No rollback; B stays in window 4 (S3.6).
> - **Watching:** subagent D (task #23 step 2, report due 06:20); no background tasks. `build/agent9/watch-nb.ps1` exited 0 at 04:34:06 (nb chain DONE, 0 `FAILED:`;
>   log `build/agent9/logs/watch-nb.txt`); `watch-b.ps1` exited 0 at 02:40.
> - **Rollback trees:** not needed (gate PASS); rb1-nolocal (9.1) and rb2-nomusttail (9.2) stay staged for window 4.
> - **On a later gate failure:** send rb1-nolocal at once (recipe step 9.1) to Agents 1 and 2: tree path, `SHA256SUMS.txt` sha256,
>   config sha256, TUs, and `build/agent9/repin/README.md`. Anything else: investigate, then bisect (S3.2). A crash's
>   `[FATAL] That is legodimensions.exe+0x<RVA>` line: `python build/agent9/addr2sub.py --log <game.log>` (B; `--build A`
>   for devoff2) gives the `sub_` and its `DEFINE_REX_FUNC` line in the generated source.
> - **Session 2 end state (01:25):** agy-grid released my SDK files (`src/codegen`, `include/rex/codegen`, `src/rexglue`,
>   `tests/ppc`, `context.h`) and the live config: don't edit them without a new grant. Live config `7F775847DB9CC2DA...`.
> - **Tool:** `build/agent9/bin/rexglue.exe` sha256 `37B32713B7516402` (recipe step 1), unchanged.
> - **Never build `install/batch`** (skip_lr). B uses only `install/batch-nolr` (`SHA256SUMS.txt` `24CE1493...`, config
>   `E60EAF1C...`, 430 TUs, gate 432).
> - **Codegen variants** go only to `build/agent9/generated/<variant>` (`build/agent9/gen.ps1`); diff them with
>   `build/agent9/diff-gen.ps1`. Pin reference: `build/agent2/gen-noflag/default` (886 files, 490,008,297 B).
> - **CPU:** every Agent 9 job takes the named-mutex slots (`bench/agent9/cpu2.ps1` = 1 slot, `bench/agent9/slots.ps1` =
>   both). QUIET is deleted; while `bench/agent9/QUIET` exists, no new Agent 9 job starts.
> - Session 2 subagents (done): A `4c6c1d7a-313a-48ae-90b6-7f334aa8640f` (T8), B `1742cb67-ba3c-406b-b6f9-bb2a9c5b1695`
>   (flush), C `7b9b6ed5-c2cb-49ac-8eda-faf8db962f21` (musttail/VMX, heavy TUs). Each keeps `bench/agent9/<area>/STATUS.md`
>   and a README.md.

## Run spec for the codegen-options timing run (for Agent 8)

The codegen options change only the generated `.cpp` text (and `PPCImageInfo.codegen_flags` in `legodimensions_init.cpp`).
So they need a regen plus a full game rebuild, done by Agent 2 after Agent 10's review (recipe in "Session 2: regen+build
recipe" below). Compare:

| Build | What | Where |
|---|---|---|
| **A** (reference) | dev OFF build of the S2 sources; codegen byte-identical to the pin | `build/agent2/devoff2-bin` |
| **B** (options) | the same S2 sources (`build/agent2/snapB`) + the batch-nolr codegen (`build/agent9/install/batch-nolr`, config in S2.10), built OFF in `build/agent2/snapB-off` | `build/agent2/devoffB-bin`, staged by Agent 2's `run-b.ps1` (Agent 8's matrices use this path, session 3) |

1. **Functional gate first (B only):** boot to the main menu, load one level, play 2 min, quit.
   - Fail on any `REX_FATAL`, `__builtin_trap`, "Switch case out of range", hang or crash.
   - Compare B's log with A's error/warning set: A had 0 errors and the same 40 warnings as baseline.
   - The risky options are the register-localization ones (`*_as_local`, `cr_compare_so_zero`). A failure there
     means rollback step 1 of the recipe. (`skip_lr` is not in B: host code reads `ctx.lr`, S2.2.)
2. **Timing:** same runner (`bench/agent8/RUN-TIMING-MATRIX.cmd`), same scene, settings and window state. Alternate A/B/A/B,
   at least 3 runs each (5 preferred). The runs are user-started, in a quiet window.
3. **Metrics:** frame time p50/p95/p99, main (game) thread CPU per frame, total process CPU, and boot-to-menu time.
   - If a sampling profile is available, add the top 30 guest functions by samples for A and B. Profiled runs never count as
     timing.
   - Names are stable because both builds share the function list; `sub_XXXXXXXX` addresses don't move.
4. **Expected:** most of the gain comes from Stage A (fewer `ctx.` loads and stores around calls), then from musttail and
   rlwinm. The generated source is 1.83% smaller than the pin (481.0 vs 490.0 MB) and has 13.1% fewer `ctx.` references
   (S2.8). A visible frame-time change is likely only if the
   game thread is CPU-bound in guest code. If the run is GPU- or present-bound, compare CPU per frame instead.

# Session 3 part 3: S4 analysis (task #23, from 04:55)

Task #23 (Agent 1, about 04:55) is a read-only S4 analysis. Steps 0-3 are listed in the RESUME block. No builds or game
runs; notes only from 08:30.

## S4.0 Agent 2's S3e clones (04:50-05:00): OK, no objections (sent about 05:05)

These are tool clones for one possible native3e build (S3d + Agent 4's next draw.cpp write), only at Agent 1's GO.
`build/agent2/make-s3e-clones.py` (`A16E05AD`) generated `prep-s3e.py` (`23536F1F`) and `run-s3e.ps1` (`FD188929`) from
`prep-s3d.py` (`BD4D94DA`) and `run-s3d.ps1` (`FE159F8A`), which are unchanged. It also patched `stop-snap.ps1`
(`C6B75748` -> `705233E5`; backup `stop-snap.ps1.pre-S3e`). The diffs are in `build/agent2/S3e-diffs/`: `8A3BFEE3`
(+36/-32), `794839B6` (+25/-25), `88A5B710` (+2/-1). I re-checked all the hashes at 05:00; they are unchanged since
04:46:40.

- **Moot:** Agent 1 said at 05:04 that S3e is off (native3d passed, so there is no native3e build). My OK crossed
  with that message; nothing more to do.
- **Replay:** `build/agent9/review/s3e_replay.py` runs make-s3e-clones.py in a scratch copy
  (`build/agent9/review/s3e-replay/`) and writes nothing in build/agent2.
  - All 7 outputs are byte-identical to Agent 2's.
  - All files are ASCII, LF only, no BOM. Both .py files compile.
  - The PowerShell parser reports 0 errors for run-s3e.ps1 and stop-snap.ps1.
  - Log: `build/agent9/review/s3e-replay.txt` (RESULT PASS).
- **I reviewed every changed line.**
  - The swaps are right: tag S3d -> S3e; base S3 -> S3d (`STATE-S3d-*.tsv`); REF native3-bin -> native3d-bin; output
    native3e-bin; doc and notes text.
  - The patch-row tags S1/S2/S3/S3e match stage-snap-bin.ps1:166-177. For an S<N><suffix> tag it lists S1..S<N> plus the
    tag itself, and the last row per file wins. So S3e's row supersedes S3d's single draw.cpp row, as notes line 4 says.
  - snap-patch.py accepts S3e (:761). It rejects notes only if they contain a tab (:779); these have none.
- **Guards (regex tests):** run-s3e's guard is stop-snap's driver list, minus run-s3e, plus stage-snap-bin.
  - It doesn't match its own wrapper, so it can't block itself.
  - It matches run-s3d, run-s3, rb-chain, run-rb2, prep-rb1, run-nb, prep-nb, build-snap, stage-snap-bin and run-b.
  - stop-snap matches run-s3e and the same drivers except stage-snap-bin. That gap predates S3e; stage-snap-bin's
    children still die through `taskkill /T` and the snap orphan pattern.
- **Dry runs** (`build/agent9/review/s3e_dryrun.py`; no bytecode, and `open` is wrapped to refuse writes; log
  `build/agent9/review/s3e-dryrun.txt`):
  - The real run gives 8/9 and exits 1. The only FAIL is live draw.cpp == snap1 (`5ea1f3576dcc2f90`, 306,557 B, mtime
    03:34:59), because Agent 4 hasn't written yet.
  - That check stops the script before the rules and notes code. So I also ran main() with the live hash faked
    in-process: 9/9, and the rules and the notes (4 lines each) format correctly.
  - Nothing was written: no S3e-rules.txt, no S3e-notes.txt, no pycache.
  - Agent 2 tested that run-s3e without S3e-notes.txt exits 4 before any build. I did not run run-s3e myself, because it
    writes a log in build/agent2.
- S3d's run took 180 s end to end (03:43:19-03:46:18), so the 08:30 guard (it only checks the start time) leaves plenty
  of room.
- Cosmetic only, not blocking: the stop-snap comment says "04:5x"; run-s3e.ps1 line 2 is 146 characters; the rules
  comment says "live draw.cpp write" where it means "next draw.cpp write".

## S4.1 Render-thread GPU-wait spin (step 1): done 05:50

Static reads only, no runs. Guest refs `.N.cpp:line` are in the A tree
(`baseline/DimensionsRecomp/rexlego/generated/default/legodimensions_recomp.N.cpp`). SDK refs are in the live
`DimensionsRecomp/rexglue-sdk`. Helper greps are in `build/agent9/s4/spin/` (`grep-devfields.txt`, `grep2.ps1` and
`grep2.txt`). Profile numbers come from `build/agent9/prof/ab-render-a9.txt` (a-prof, devoff2, 67.66 fps).

### S4.1.1 What the render thread polls, who writes it, and how often

- **The words.** dev is the D3D device. dev+11024 holds a pointer to a fence block, and dev+11036 is the guest's
  next-fence counter.
  - The render thread's loop polls only **block+0 = *(dev+11024)+0**, the last fence the GPU passed.
  - block+4 holds the ring position at that fence.
  - block+60 is the RPTR write-back (`command_processor.cpp:314-316`, once per ExecutePrimaryBuffer batch). This loop
    doesn't read it.
- **The wait.** sub_83FBF7D0 (`.248.cpp:35181`) sets up a stack waitctx (sub_83FAF088, `.53.cpp:34710`): +0 dev, +4
  kind, +8 last seen block+0, +12/+16 KTHREAD+0x58, +20 mftb.
  - It then loops `while (!done) if (!sub_83FAF180(&waitctx)) break;`.
  - done = `(X - r4) >= (X - block[0])` unsigned, with X = dev+11036. So it waits until the GPU has passed fence r4.
  - **Correction to S3.8 (lines 396-397): this is a fence wait, not a wait for ring-buffer space.** The S3.8 conclusion
    stands: the render thread waits for the command processor, so faster guest code only spins faster.
- **The poll step**, sub_83FAF180 (`.107.cpp:36777-36897`):
  - `cctpl`, a ctr=4 loop of 8 `db16cyc`, then `cctpm`. The codegen emits nothing for these
    (`src/codegen/builders/system.cpp:51-73`), so the loop is 4 empty decrements.
  - It returns 0 if dev+11069 & 2.
  - If block+0 changed, it stores the new value to waitctx+8 and resets waitctx+12.
  - It calls sub_83FA2698 (current thread id, KTHREAD+0x14C).
  - Timeout: `(KTHREAD+0x58 - waitctx+12) >= *(0x847F9AC0)` calls sub_83FC91D0. The SDK never writes KTHREAD+0x58, so
    the difference is always 0 and the timeout never fires. sub_83FC91D0 has 0 samples. 0x847F9AC0 has no generated
    store, so it is an image constant.
- **After the loop**, sub_83FAF0B8 (`.413.cpp:35532-35643`) runs. If kind != 0:
  - it adds the elapsed mftb ticks to the 64-bit counter dev+22016 (kind 3) or dev+22008 (other kinds);
  - if dev+13836 != 0, it calls that callback (r4 = kind, f1 = elapsed x dev+22000 x a constant).
  - These are guest-visible, but they are wall-clock measurements.
- **Guest side of the fence.** sub_83FC0180 (`.222.cpp:36211-36406`) writes 12 PM4 dwords into the command buffer:
  1. INVALIDATE_STATE `0xC0003B00` (mask 0x7FFF).
  2. A type-0 write of reg 0x5C8 = 0x20000 if dev+11072 & 0x80, else NOP `0xC0001000` + `0x77777777`.
  3. EVENT_WRITE_SHD `0xC0025800` (initiator 3): block+4 <- (dev+15324 & 3) | dev+48.
  4. EVENT_WRITE_SHD (initiator 3): **block+0 <- dev+11036**.
  - Addresses are physical | 2 (endian), with physical(p) = (p & 0x1FFFFFFF) + ((((p >> 20) & 0xFFF) + 512) & 0x1000).
  - Then dev+11036 += 2. That counter is guest-only and written by the submitting thread. Ring init (`.386.cpp:34621`)
    sets it to 3 and block+0 to 1.
  - If dev+21940 == 0 and dev+11069 & 2 (GPU off), the CPU writes block+0 and block+4 itself.
  - The other `+11036` stores in the tree (`.144:36789`, `.184:36587`, `.303:37595`, `.45:15416`) belong to other
    structures.
- **Host writer of block+0: only the command processor**, `CommandProcessor::ExecutePacketType3_EVENT_WRITE_SHD`
  (`src/graphics/command_processor.cpp:1393-1416`), on the "GPU Commands" thread, when it reaches the packet.
  - It calls `OnGuestVisibleWrite("EVENT_WRITE_SHD")` at :1396. On D3D12 that is PublishOnDemandMemexport +
    FlushMemexportReadbackBatch (`src/graphics/d3d12/command_processor.cpp:3510-3513`).
  - Then `memory::store(TranslatePhysical(address), GpuSwap(value))` at :1415. Initiator bit 31 is 0, so it writes
    the value, not the counter.
- **Rate: one fence per kick, plus one per frame.**
  - The kick sub_83FC0C10 (`.232.cpp:36773`, about 120 call sites) always calls sub_83FC08D0. That emits the fence
    (`.351.cpp:36006`) when dev+13600 == 0 and !(dev+11068 & 0x80), then submits (sub_83FC06D0).
  - sub_83FCBA68 (`.95.cpp:37025`, probably the Swap path) adds one per frame. It resets the 7 per-frame lists at
    dev+13616..13760, then emits a fence and submits.
  - The kick's own wait (sub_83FBF7D0(dev, 11036-2), then 11069 |= 2) runs only when global 0x84A6A660 != 0, a
    sync/shutdown mode.
  - Nothing counts kicks or fences per frame today (frame_stats has kCpIdle, kFenceWait and others:
    `src/graphics/frame_stats.h:22-32`). The per-frame number needs probe P1 (S4.1.4).
- **Waiters:**
  - sub_83FBF8A0 (`.119:35551`): BlockOnFence(r3), kind 6. It takes the device from 0x820006D8 or 0x820006D4,
    depending on KeGetCurrentProcessType == 2.
  - sub_83FBF900 (`.140:36853`): waits for obj+8's fence, kind 5.
  - Direct calls from sub_83FC0EC0, sub_83FC5D68, sub_83FB33E0, sub_83FBFB30 and sub_83FC5730 (8 sites).
  - The render thread's path is sub_82B73D48 (`.341.cpp:6981`) -> sub_82B73A78 (`.347.cpp:7511`) -> (tail-call frames
    not in the profile) -> sub_83FBF7D0. Which wrapper it uses is unresolved; the proposals don't need it.
- **Cost (a-prof):**
  - Render thread F80001A8: busy 13.85 ms/f. sub_83FBF7D0 inclusive 13.00 ms/f (168 of 179 busy samples) =
    **0.88 core**. Of that, sub_83FAF180 is 9.98 (self 7.97) and sub_83FA2698 is 0.85.
  - GPU Commands: busy 8.44 ms/f, blocked 6.35 ms/f.
  - **Second spinner:** the host TimerQueue thread, busy 12.69 ms/f = **0.86 core** (S4.1.2).

### S4.1.2 The TimerQueue spin

- `rex::thread::TimerQueue` (`src/core/timer_queue.cpp:148-295`) is a static object; its thread starts at load.
  - Its only client on Windows is `HighResolutionTimer` (`include/rex/thread.h:147-173`). It is created once, for the
    KeTimeStampBundle 1 ms tick (`src/kernel/xboxkrnl/xboxkrnl_module.cpp:184-199`), whose callback stores
    `Clock::QueryGuestUptimeMillis()` into bundle+16.
  - Basis: a grep of SDK `src` and `rexlego/src` for `CreateRepeating|QueueTimer*` at 05:30, before Agent 1's 05:31
    scan ban. It found only that site and `threading_posix.cpp`, which is built only for UNIX
    (`src/core/CMakeLists.txt:56-76`). Callers in `include/` were not scanned; that waits until after 07:15.
- **Default: `dp::spin_wait`** toward the next deadline (:57-68, :97-108). So the thread spins about 1 ms between
  ticks: 0.86 core for one store per ms.
- **With the env var `REX_TIMER_WAIT_BLOCKING` set** (read once, :42), it waits on a condition variable with
  `wait_until(deadline)` (:110-124). The SDK's own comment (:33-35) says blocking preserves deadlines but OS wake
  jitter differs.
- **Effect of a late wake:** the tick value is computed in the callback, so bundle+16 is never wrong, only staler
  between refreshes.
  - The staleness equals the wake latency: about 1-2 ms with a 1 ms host timer resolution, up to about 15.6 ms at the
    OS default.
  - The setting is `HostTimingConfig::timer_resolution_ms` (`include/rex/threading_timing.h:20-21`; default 0 = OS
    default). `ConfigureHostTiming` applies it (`src/core/threading_win.cpp:226-254`) and logs `Host timer resolution
    set to N ms`.
  - a-prof's game.log, toml and run.json show neither that line nor `REX_TIMER_WAIT_BLOCKING`.
  - The name of the cvar that feeds it: to look up after 07:15.

### S4.1.3 S4 proposals, ranked (all default OFF; all "CPU/power; fps only via headroom")

fps, for all of them:
- The i7-1255U has 2 P-cores (4 logical) + 8 E-cores at a PL1 of about 15 W, and P-cores were seen at about 1.9 GHz.
  So the package is power-limited.
- The two spinners (0.88 + 0.86 core) compete with Main and GPU Commands for P-cores (directly or as HT siblings) and
  for power. Freeing them can raise the clock of the threads on the frame's critical path.
- But frames are bound by the CP/host-GPU path (S3.8), so a gain is possible, not promised.
- Any added wake latency on the render thread can also cost fps if the CP runs dry while it sleeps. GPU Commands is
  blocked 6.35 ms/f, and the split between CP idle and host-GPU fence wait is unknown (P2).

1. **(d) `REX_TIMER_WAIT_BLOCKING=1` with a 1 ms host timer resolution: already in flight (Agent 11's timer change).**
   Env + cvars, no build. Not a new proposal.
   - Agent 8's W4b arm d11t (`bench/agent8/run/matrix-window4.json:37-42`) = devoff2 + Agent 11's ON bundle R3
     (`host_timer_resolution_ms=1`, `host_timer_throttling_optout=true` and 6 more cvars) + the env var.
   - Every d11t game.log must show `Host timer resolution set to 1 ms (background opt-out on)`.
   - d0t (blocking without the 1 ms resolution) was dropped at 03:42.
   - What S4.1 adds:
     - CPU: about -0.85 core (the TimerQueue thread). Afterwards it wakes about 1000 times/s, about 0.01-0.02 core.
     - Why the logic stays identical: the only Windows client is the KeTimeStampBundle tick (S4.1.2). The callback,
       the value formula and the order stay the same; only the refresh time of bundle+16 moves. Its staleness goes
       from microseconds to up to 1-2 ms, so guest code that reads the tick (GetTickCount-style) sees steps of 1-2 ms.
       Without the 1 ms resolution the steps could reach 15.6 ms, so dropping d0t was right.
     - W4b measures the timer change only together with the R3 bundle: there is no d11 arm in W4b, and window 3's d11
       is a cross-window reference. If Agent 1 wants the timer effect alone, that needs a later d11 vs d11t pair in one
       window.
   - Agent 10: after 07:15, confirm that `HighResolutionTimer` has no other user (including `include/`).
2. **(a1) Wake on GPU write: a rexlego hook on the poll step + a CP notify in the SDK. Needs a build.**
   - **Hook:** `sub_83FAF180` via `REX_HOOK_RAW` + `__imp__sub_83FAF180`. The generated `sub_X` is a weak alias of
     `__imp__sub_X`. Same pattern as `rexlego/src/area_watch.cpp:33,324-325` and `icon_probe.cpp:433-436`;
     `include/rex/hook.h:36-49`. It is gated by a new env var, default OFF:
     1. s = seq (acquire); dev = waitctx+0. If dev+11069 & 2, or block+0 != waitctx+8, go to step 3.
     2. waiters++ (seq_cst); if seq == s, `WaitOnAddress(&seq, &s, 4, 1 ms)`; waiters--.
     3. Call `__imp__sub_83FAF180(ctx, base)` unchanged.
   - **SDK:** after every guest-visible store in the CP, do `seq.fetch_add(1)`, and if waiters > 0,
     `WakeByAddressAll(&seq)`. The stores: EVENT_WRITE_SHD :1415, the handlers REG_TO_MEM :1274, MEM_WRITE :1294,
     COND_WRITE :1312, EVENT_WRITE_EXT :1419, EVENT_WRITE_ZPD :1449 and INTERRUPT :988, and the RPTR write-back
     :314-316 (all in `src/graphics/command_processor.cpp`). An accessor exports `seq` and `waiters`.
   - **No lost wake:**
     - the CP stores, then bumps seq;
     - the hook reads seq before re-reading block+0;
     - WaitOnAddress re-compares seq when it registers;
     - the waiter count uses the seq_cst Dekker pattern.
     - The 1 ms timeout catches a missed store site, the CPU fallback write (dev+21940 == 0), and dev+11069 & 2 set by
       another thread.
   - CPU: about -0.85 core. Latency: a fence is seen one wake (about 5-50 us) after the store, instead of within one
     poll (well under 1 us).
   - **Output-identical:**
     - the guest loop runs the same code, with the same completion test on the same word;
     - the hook only delays the next poll until the word may have changed;
     - waitctx is on the guest stack and changes only when block+0 changes, as now;
     - the timeout is dead either way.
     - The only guest-visible differences are dev+22008/22016 and the elapsed value passed to the dev+13836 callback.
       Those are wall-clock values and already vary run to run.
   - Files: a new rexlego hook file (+ its CMake entry); SDK `src/graphics/command_processor.cpp` and `.h`.
   - Needs: Agent 1's grants for both trees, Agent 2's build, Agent 10's review.
   - Risk: medium (SDK change; wake latency). B's Stage A doesn't matter: the hook passes ctx through and reads only r3,
     as the existing hooks in B do.
   - Test: P1 first. Then a functional run in the slot (menus + level route, gate_logdiff). Then window 4, env off vs
     on: render-thread and process CPU, fps p50/p95/p99, GPU Commands busy/blocked, waits per frame.
   - Agent 10: the memory-order argument (x86 TSO, seq_cst counter); the 1 ms safety net; the 11069&2 and CPU-fallback
     paths; the stats-only differences; the cost of the OFF path (one load and a branch per poll).
3. **(a2) Backoff in the same hook, rexlego only (game build, no SDK change).**
   - Step 2 becomes: while block+0 is unchanged, `_mm_pause` for about 20-50 us, then `SwitchToThread`, then sleep for
     a quantum of about 250 us on a high-resolution waitable timer (`CREATE_WAITABLE_TIMER_HIGH_RESOLUTION`, already
     used in `rexlego/src/sample_profiler.cpp:70` and `gpu_native/device.cpp:1806`).
   - CPU: about -0.7 to -0.8 core. Latency: up to one quantum per wait (half on average).
   - Output-identical: the same argument as (a1).
   - Files: rexlego only. Risk: medium (latency).
   - Test: as (a1), with the quantum as an env knob, so window 4 can sweep 0/125/250/500 us.
   - Agent 10: as (a1) without the CP part, plus the quantum's worst case per frame (from P1's waits per frame).
4. **(b) Codegen: `db16cyc` -> `_mm_pause()`** (`src/codegen/builders/system.cpp:51-73`; `cctpl`/`cctpm` stay empty).
   - In sub_83FAF180 that is 32 pauses per poll, about 1-2.5 us at 1.9 GHz. Effect: fewer polls, less power, and more
     of the core for the HT sibling. OS-visible CPU doesn't change.
   - Output-identical: it adds pauses only, with no ctx or memory change.
   - Needs: my SDK codegen grant back, a regen + full rebuild, and Agent 10's review of the generated diff. The
     `db16cyc` site count needs a tree scan (after 07:15).
   - Risk: low. This is S3.8 item 2.
5. **(c) Codegen: a spin policy at hint loops.** The codegen would recognise `cctpl ... db16cyc ... bdnz ... cctpm` and
   call a runtime backoff. It covers every guest spin loop, but it is blind to the wake condition: it has (a2)'s latency
   without (a1)'s wake. Needs a grant + regen + rebuild. Ranked last.

Not proposed: priority or affinity changes for the spinners, and any change to the guest loop's timeout or exit
conditions (those change guest semantics).

### S4.1.4 Probes (spec only; for window 4 or later, no build tonight)

- **P1, fences and waits per frame** (rexlego, env-gated, default OFF). Pass-through hooks that call `__imp__`
  unchanged:
  - sub_83FC0180: fences, split by caller (kick path vs sub_83FCBA68);
  - sub_83FC0C10: kicks;
  - sub_83FBF7D0: waits, with kind r5, thread id, and QPC time around the original;
  - sub_83FAF180: polls per wait.
  - Per frame (the frame counter perf.csv uses): the counts, the wait-time sum, and the deltas of the guest's own
    dev+22008/22016 (read-only).
  - Every 300 frames, log the per-frame mean and p95, and a wait-duration histogram (< 50 us, < 200 us, < 1 ms,
    < 4 ms, >= 4 ms).
  - Many short waits favour (a1); with a few long waits, (a2)'s quantum is harmless.
  - Cost when ON: a few counters and 2 QPC reads per wait. When OFF: one branch per call.
- **P2, CP idle vs host-GPU wait per frame, no build:** one run with `--slow_frame_log_ms=1`.
  - `ReportSlowFrame` (`src/graphics/d3d12/command_processor.cpp:238-284`) logs every frame longer than the threshold,
    with gpu-thread idle (kCpIdle), host-gpu wait (kFenceWait, with count) and the other frame_stats.
  - 0 disables it (:265), and a-prof had 0 such lines. With 1, every frame logs (about 10k lines in 150 s), so it is a
    profiling run, not a timing run.

## S4.2 Main scene walk (step 2): subagent D, report due 06:20

## S4.3 S4 codegen ranking (step 3): pending

# Session 3: build B support (task #8, from 02:00)

## S3.1 RESUME check (02:03): PASS

- Tool `build/agent9/bin/rexglue.exe` sha256 `37B32713...` (= recipe step 1).
- `install/batch-nolr`: all 872 files re-hashed against `SHA256SUMS.txt`, 0 mismatches; `SHA256SUMS.txt` sha256
  `24CE1493...`. Its config and `configs/batch-nolr.toml` are both `E60EAF1C...`.
- The live `rexlego/legodimensions_config.toml` is unchanged (`7F775847...`). My former SDK roots: 0 files changed since the
  23:15 cut.
- No Agent 9 process; 12 logical CPUs; about 278 GB free on C:. `bench/agent9/QUIET` deleted at 02:02.

## S3.2 Rollback trees, pre-staged (chain6, 02:06-02:13)

- `build/agent9/make-batch-config.ps1 -Drop 'k1,k2'` (one string, split on commas, semicolons or spaces) deletes those key
  lines, and a heading comment once all of its keys are gone, then adds `# Rollback (recipe step 9, ...): dropped ...`
  after the title. An unknown key throws and writes no file. Without `-Drop` the output is still `E60EAF1C...`.
- `build/agent9/chain6.ps1` (log `build/agent9/logs/chain6-steps.txt`, exit 0) ran config, gen, install and count2 for both
  trees. They are built only after a B failure and Agent 1's GO.

| Tree | Recipe step | Drops | Config sha256 | Files / `SHA256SUMS.txt` sha256 | TUs (last) | Gate |
|---|---|---|---|---|---|---|
| `build/agent9/install/rb1-nolocal` | 9.1: the gate fails | `ctr_as_local`, `xer_as_local`, `reserved_as_local`, `cr_as_local`, `cr_compare_so_zero` | `AE9F8F967FBB264919A63463CA4958F856C18A0405A4895440D6C36A31084EEC` | 880 / `A966CF18E3EC736F5685CA413A93C7E97B436547560E285894D43D4E1A9ED917` | 434 (`.433.cpp`) | 436 |
| `build/agent9/install/rb2-nomusttail` | 9.2: a TU fails with musttail | `musttail_calls` | `FC034D495DAC395F45CDC0AC0DC7BFD88C8D2046A09590B88563B63BE1C82924` | 870 / `8BDE87171405EC9611B89CD75BADC400DD93BC371CFBA3634B7B446FCF9D7B14` | 429 (`.428.cpp`) | 431 |

- Both gens: no "Code generation blocked", 0 handoff errors (count2: `build/agent9/logs/count2-<tree>.txt` and
  `build/agent9/diff/<tree>/`).
  - rb1 (gen 119.7 s, install 485,519,156 B): no localization-fallback line. `ctx.` refs 13,068,844; compares that read
    `ctx.xer.so` are back to 430,626 (SO = 0 folds: 0). Flush, rotl and musttail (63,167) equal batch-nolr's. All 165,023
    functions are common.
  - rb2 (gen 81.2 s, install 479,926,141 B): musttail 0, every other count unchanged. Its 3 "larger" functions only gain
    hook `extern` declarations that moved with the TU boundaries (`sub_82BB3270`: 5 `NativeCelShading*` externs).
- **Handover:** tree path, `SHA256SUMS.txt` sha256, config sha256 and TU count, to Agents 1 and 2. Agent 2's `prep-b.py` and
  `run-b.ps1` pin batch-nolr (`VARIANT`, `SUMS_SHA`, `CFG_SHA`, the 872-entry count; `$nolr`, the two pins, `$cgNote`), so
  they must be re-pinned first.
- **If 9.1 and 9.2 both fail:** make a combined tree (bisect): `make-batch-config.ps1 -Out <n>.toml -Drop '<keys>'`, then
  `gen.ps1 -Variant <n> -ConfigFile build\agent9\configs\<n>.toml`, then `make-install.ps1 -Variant <n>`. `chain6.ps1` is
  the template.
- `build/agent9/logs/install-steps.txt` is UTF-16 LE (`Tee-Object -Append` in Windows PowerShell 5.1). Agent 2's `prep-b.py`
  decodes it by its BOM. Keep appending with `Tee-Object`, as `make-install.ps1` does: a UTF-8 append would mix encodings.

## S3.3 T8 opt9: S2.10's 9 keys = build B's key set (02:18-02:21, one slot)

- `bench/agent9/ppctests/opt9_config.toml` = `tests/ppc/opt_config.toml` minus `skip_lr`. `gen.ps1`, `compile.ps1`,
  `link.ps1` and `runtests.ps1` take `-Variant opt9`; `runtests.ps1` excludes `opt9=cr_so_fold.test_call` by default, as
  for opt. Driver: `build/agent9/ppctests/chainOpt9.ps1`.
- **Result** (`build/agent9/ppctests/compare.md`; logs `build/agent9/ppctests/logs/chainOpt9.txt` and `chainOpt9b.txt`):
  opt9 has 1515 tests: 1513 pass, 1 FAIL, 0 CRASH, 1 excluded, **the same as opt**. The FAIL is `vupkd3d128.test_short2_3`
  (pre-existing, S2.9); the excluded `cr_so_fold.test_call` fails its own run exactly as opt's does (S2.4). default and
  crso, rerun alongside: 1514/1515 each, unchanged.
- **LR-only diff** (`build/agent9/ppctests/opt9_lrdiff.py`): `ppc_test_cases.cpp`, `ppc_config.h` and `ppc_test_decls.h` are
  byte-identical to opt's, so opt9 links opt's cases object. `ppc_test_functions.cpp` differs only in 9 `ctx.lr` lines (5
  `ctx.lr = <imm>` stores, 2 `mtlr`, 2 `mflr` reads); without them the two files are identical.
- Times: gen 8.2 s (1515 TEST_CASEs, 1527 functions), functions TU 12.7 s, link 0.7 s.
- **Fix:** the cases-object fallback loop in `link.ps1` used `$o`, which overwrote `$O` (the pin libs dir: PowerShell names
  are case-insensitive), so the first opt9 link failed with `opt/rexruntime.lib` missing. It is now `$ov`; the relink passed.

## S3.4 Build B review (02:16-02:25): ok

- Reviewed `build/agent2/prep-b.py` (`C0067F18`), `run-b.ps1` (`0D159651`) and `b-chain.ps1` (`AD7C76D7`) against recipe
  steps 3-5 (Agent 2's diffs: `build/agent2/B-diffs/`). All of it matches:
  - install/batch-nolr only: both tools refuse anything else (Agent 2's negative tests refused install/batch 4 times in
    each tool);
  - the pins `SHA256SUMS.txt` `24CE1493...` (872 entries) and config `E60EAF1C...`, in prep-b and again in run-b;
  - the exact `[batch-nolr] END ` tag, read as UTF-16 or UTF-8;
  - `-GenBase ...\install\batch-nolr\generated`; gate 432 (from `sources.cmake`); output `build/agent2/devoffB-bin`, the
    name in Agent 8's matrices;
  - the gen-check, snap-gate, build-snap and stage-snap-bin changes for batch-nolr are comments only.
- **ok** sent to Agents 1 and 2 at 02:25.
- prep-b (02:21-02:22): 872 install files verified, snapB copy verified (24,095 files), step 4 done, gen-check PASS (870/870
  generated files identical, `codegen.d` rewritten to snapB paths). run-b (02:22): pins match, configure 13.6 s, gen-check
  PASS, gate 432 PASS, build from 02:22:46 (-j10, -k 0).
- Agent 8's matrices (fixed in session 3): a-prof uses devoff2-bin, b-gate and b-prof use devoffB-bin. A gate failure means
  9.1 (rb1-nolocal). B's log is diffed against A's ERROR/WARN set with `gate_logdiff.py`. The MENU step uses Agent 3's
  harness in Agent 8's slot.

## S3.5 Build B result (02:40): built clean and staged; static A/B check PASS

- b-chain DONE at 02:40:31 (1,164 s in total). The run-b build exited 0 (1,060 s at -j10, 471/471 steps, 0 `FAILED:` lines).
  `rexruntime.dll` == the snap1-sdk install (`1C45C869...`). Stage exited 0: 7 files in `build/agent2/devoffB-bin`
  (198.3 MB).
  - `legodimensions.exe` 153,588,736 B, sha256 `C3F8686EBDD83340...` (A: 170,334,720 B).
  - `legodimensions.map` `44332E6C8E68508B...`; `MANIFEST.txt` `8709476FF4778768...`. The MANIFEST names install/batch-nolr,
    its END line, the `SHA256SUMS.txt` sha256 and the config sha256.
- Compiler warnings: B has 19, the same count as snap1's full build. All are `-Wdeprecated-declarations` in host code
  (`getenv`, `sscanf`, `_wfopen`, `u8path`); none is in a generated TU.
- `build/agent9/mapcmp.py` (log `build/agent9/logs/mapcmp-AB.txt`; exit 1 if the sets differ) compared A's and B's maps:
  - A and B have the same 164,786 `sub_` publics and the same `__imp__` aliases. The 27 aliases that are not at their `sub_`
    (hooked) are the same set.
  - `.text` went from 159,346,632 to 142,585,352 B (-10.52%).
  - Per-function code size (including padding): 68,442 shrank, 1,835 grew, 94,509 unchanged. The largest growth is
    `sub_82AEE4E0`, 20,432 to 34,576 B.
- `build/agent9/make-repin.py` wrote re-pinned copies of Agent 2's `prep-b.py` and `run-b.ps1` for rb1 and rb2 to
  `build/agent9/repin/` (README and diffs), from `C0067F18`/`0D159651`.
  - It re-ran prep-b's step-1 checks on both trees: PASS.
  - Both copies parse (py_compile and the PowerShell parser).
  - They are used only after a gate failure and Agent 1's GO. Agent 2 owns the tools.
- Profiles: Agent 7 asked Agent 8 to set `framerate_limit=0` on both a-prof and b-prof. That keeps them symmetric, and
  profiles never count as timing. Agent 7's `bench/agent7/prof_main_compare.py` normalises samples per frame.
- `build/agent9/addr2sub.py` maps a host crash address to its symbol. The address comes from the crash handler's
  `[FATAL] That is legodimensions.exe+0x<RVA>` line (`rexglue-sdk/src/core/exception_handler_win.cpp:217`), or is given
  directly as an RVA or Rva+Base. It uses the build's map (`--build B`, the default, or `A`). For a recompiled function, it
  also prints the `DEFINE_REX_FUNC(sub_...)` line in that build's generated source (B: install/batch-nolr; A: `baseline/`).
  - Tested: `+0x1050` is `sub_82620000` in both builds. `+0x1200` is `sub_826319A0` in B and `sub_82631DF8` in A.
  - `--log` picks the lines out of a `game.log`, and other modules are reported as such.
- **B boot PASS** (Agent 8, `build/agent8/runs/0247-devoffB`, 02:47:52-02:49:58): exit 0 after WM_CLOSE in 0.71 s, 0
  not-responding samples, no WER. Its 90 log lines match the 90 lines of Agent 8's `0254-devoff3` boot run (numbers
  normalised). The only differences are the run dir and the random ToyPad challenge bytes. devoff3 is S3 (28 host changes),
  so the gate's A stays devoff2 (S2, B's snapshot).
- The B game gate result is in S3.6.

## S3.6 B game gate (03:05-03:31): front-end PASS (Agent 10), partial coverage

Agent 10's checklist (last section of `perf-notes/agent10-codegen-review.md`; write-up "Route level" there). Agent 8's slot,
Agent 3's harness (blind fixed sleeps, `harness/run-game.ps1`), functional only. A = devoff2 (S2, B's snapshot).
- **Pair 1** (`harness/routes/b-gate-menus.txt`, 37 steps, sha256 `CF803C22...`): A `build/agent3/runs/20261122-030511-bgate-a`,
  B `build/agent3/runs/20261122-030752-bgate-b`.
  - Both: exit 0 after WM_CLOSE (A 3.1 s, B 0.83 s), 37/37 steps, 0 timeouts, no WER or dumps, 0 "not in any registered
    module", 0 watchdog, 0 crash guard, 0 unimplemented-instruction lines. gate_logdiff PASS.
  - The only normalised-key difference: `[NtCreateFile] FAILED: path='d:\INSTALL#_#.DAT'` 102 (A) vs 136 (B), +34 = one
    probe pass. In its 20-s idle tail B left the 220/534 front-end screen on its own: 220/540 for 60 frames, then 218/222,
    with the 34-line INSTALL pass at +144.5 s. A stayed on 220/534 to the end, and so did Agent 3's devoff2 dry run
    (`20261122-030135-bgate-dry`).
  - My 03:21 explanation (an idle timer of about 1,200 frames; A ran its tail at 38.8 fps) was wrong. The tie-break
    refuted it and I withdrew it at 03:29.
- **Tie-break** (`harness/routes/b-gate-menus-long.txt`, the same 36 steps plus a 90-s idle tail, sha256 `1F3559C8...`):
  `build/agent3/runs/20261122-031756-bgate-long-devoff2` and `build/agent3/runs/20261122-032150-bgate-long-devoffB`.
  - Agent 10: both exit 0, 54/54 steps; logdiff NEW 0, MORE 0, flags 0, warnings 142 = 142; GONE only the 4 random Toypad
    challenge keys.
  - Both builds left 220/534 on their own and ran the same sequence: the 60-frame fade, the 34-line INSTALL pass, the
    profile reads, the Toypad light, then the same attract scene signatures in the same order.
- **Idle counts**, from the last pad input to the first 220/540 frame (`build/agent9/idle_frames.py`; log
  `build/agent9/logs/idle-frames.txt`; Agent 10's idlecount.py agrees). The last input frame is the pad-poll count before
  the last press plus its active polls, minus the poll-to-frame offset (3-5 polls; about +/- 2 frames). perf.csv's
  60-row flush blocks don't limit the precision.

  | Run | Exit | Idle frames | Frame time | fps | Since 220/534 appeared |
  |---|---|---|---|---|---|
  | tie-break devoff2 | yes, +143.0 s | 1,122 | 18.88 s | 59.4 | 58.00 s |
  | tie-break devoffB | yes, +141.2 s | 883 | 18.87 s | 46.8 | 62.41 s |
  | pair 1 devoffB | yes, +144.5 s | 1,199 | 20.35 s | 58.9 | 59.19 s |
  | pair 1 devoff2 | no (to the end) | >= 1,119 | >= 26.38 s | 42.4 | >= 65.8 s |
  | dry run devoff2 | no (to the end) | >= 1,572 | >= 26.46 s | 59.4 | >= 62.6 s |

  - The tie-break pair matches in time (0.01 s), not in frames, so the trigger counts time, not frames.
  - None of these separates the 3 exits from the 2 devoff2 no-exits: frames, frame time, time since the screen appeared,
    or the summed interrupt_dispatches (26.9k-31.1k at the exits, 36.4k-40.6k in the no-exit runs).
  - devoff2 left in 1 of 3 identical runs, so pair 1's end divergence is run-to-run variation, not B.
- **Verdict (Agent 10, 03:31):** front-end gate PASS, partial coverage. No rollback; B stays in window 4. Static PASS 02:45,
  boot PASS 02:59, route PASS 03:31.
  - Not covered: level, pause/options, cutscene, level change, save/Quit, the toy pad, and every native item.
  - Agent 10's rule: rollback only if B leaves while devoff2 stays past about 1,300 idle frames. That didn't happen.
- **Perf, pair 1** (information only, hidden desktop, not timing):
  - Mean frame time: B 18.885 ms, A 17.981 ms.
  - Median: B 16.854 ms, A 16.738 ms.
  - p95: B 41.98 ms, A 34.65 ms.
  - Process CPU: B 319.5 s, A 328.2 s.
  - Each run had a slow phase at a different time: B ran at 25-33 fps over perf 70-91 s, and A at 38.8 fps over its last
    20 s. That points to the shared machine, not to either build.
- **Tools:**
  - `build/agent9/gate_scene.py`: per-step draws/vertices segments of two runs (log `build/agent9/logs/gate-scene-AB.txt`).
  - `build/agent9/idle_frames.py RUN_DIR... [--exit D/V]`: idle frames and time from the last input to an exit scene,
    and the INSTALL probe passes.
  - Both are read-only and single-threaded.

## S3.7 nativeB script review (03:36-03:50): OK, no fixes

Agent 1, 03:34: review Agent 2's nativeB scripts before the build (a clone of prep-b/run-b for `build/agent2/snapB3` at S3d,
NATIVE ON, A = `native3d-bin`); it must use `install/batch-nolr` and refuse `install/batch`. After the build: the static
check against native3d-bin with Agent 10 (task #17 item 1a). Verdict OK (no objections) sent to Agents 2 and 1 at 03:50;
it also answers Agent 2's 03:47 request (everything in `build/agent2/RB-diffs/`, Agent 1's nativeB condition 3).
- **prep-nb.py** is made by `build/agent2/make-rb-clones.py` (task #14; Agent 2 ran it at 03:46:24, see "Real run" below). I ran its `main()` unchanged
  with every write redirected to `build/agent9/review/rb-dryrun/` (`build/agent9/review/dryrun-rb-clones.py`; nothing in
  `build/agent2` written; output `build/agent9/review/rb-dryrun-out.txt`):
  - All 5 clones and the stop-snap.ps1 patch are made; every pinned line survives. `prep-nb.py` = 21,099 B, sha256
    `0FAF4A924AEEE498` (py_compile OK); `run-rb1/2.ps1` and the patched `stop-snap.ps1` parse.
  - `--check-only` on the real snap1 and install tree (a test copy logging into rb-dryrun): exit 0, step 1 PASS (872
    files hash-checked, config E60EAF1C, 432 sources), tag S3 (03:41; S3d was applied at 03:42).
  - `--install build/agent9/install/batch`: refused (exit 1) before anything is read.
  - `rexlego/out` (17 files, 643 MB, no reparse points) is copied and size/mtime-checked; the patch rows are checked in
    order S1, S2, S3, S3d (last row wins).
  - snap1's S3 config + the 9-key block = `configs/batch-nolr.toml` (no line only in snap1; S3 has no config row).
  - Host registers: `build/agent9/hostregs2.ps1` on snap1 (S3) = the reviewed 23:53 live-tree set (378/378 unique hits,
    0 new, 0 gone; `build/agent9/logs/host-regs-snap1-S3.txt`). Re-scan `draw.cpp` for S3d.
- **run-nb.ps1** (hand-written, 03:40, sha256 `979F4309EE10E9EF`, 0 parse errors, ASCII, LF): guards (08:30-12:00, -Jobs
  <= 10, driver check); `$nolr` equality, not a link, SHA256SUMS 24CE1493; the notes line must say `copied by prep-nb.py`;
  -Compare from that tag (S3d -> native3d-bin, S3 -> native3-bin), A staged, -Out not; snapB3 config E60EAF1C;
  `rexlego/out/native-gpu` present; `build-snap.ps1 -Phase game -Native -Tag snapB3n -SnapDir snapB3 -GameDir snapB3-on
  -CodegenExe codegen-frozen2.exe -GenBase batch-nolr/generated` (build-snap re-roots Agent 6's flags on -SnapDir and
  -GameDir overrides snap1-on); the rexruntime.dll check; `stage-snap-bin.ps1 -Variant native -CompareBin A` with
  native3d's exe and runtime strings. The diff against run-b.ps1 drops nothing
  (`build/agent9/review/rb-dryrun/RB-diffs/run-nb.ps1.vs-run-b.diff`).
- **Order:** run prep-nb only after native3d-bin is staged, so its log says `snapshot tag S3d` (it accepts S3 too).
- **Optional nits (not blocking):** the driver guard doesn't list `prep-(b|nb|rb\d)\.py` (R5 for the rb clones neither);
  an explicit -Compare isn't checked against the tag; the native GPU fingerprint against A is logged, not enforced (I
  check it in item 1a).
- **Expected at the native gate:** 432 generated TUs (snap1-on had 440, 533 DB entries).
- **Real run (Agent 2, 03:46:24):** byte-identical to my dry run, by sha256: the 5 clones (prep-nb `0FAF4A92`, prep-rb1
  `94C6C916`, prep-rb2 `E0A00373`, run-rb1 `0665AA37`, run-rb2 `118C2D6E`), `stop-snap.ps1` `C6B75748`,
  `stop-snap.ps1.pre-RB` `B9AECC6A`, and all 7 `RB-diffs` (prep-nb `F5B9A4B7`, run-nb vs run-b `48168743`, prep-rb1
  `DA5EDDBC`, run-rb1 `FEECE89A`, prep-rb2 `A6FA98BB`, run-rb2 `C07F412B`, stop-snap `87D09AB2`). Re-hashed at 03:49:
  unchanged; run-nb.ps1 still `979F4309`.
- **rb-chain.ps1** (03:46:19, sha256 `3660069EDC1C187B`, 7,032 B, 0 parse errors; read, not run): variant guard (nb, rb1,
  rb2), -Jobs 1..10, stops 08:30-12:00 and won't start nb from 07:00; an ancestor-aware driver check that does list the
  prep scripts and snap-patch apply (so the guard nit above doesn't apply through the chain); `snap-patch.py verify
  <tag>` (S3/S3d only); prep-<v>.py, then the notes line must name prep-<v>.py at that tag; run-<v>.ps1; logs the staged
  hashes.
- **native3d-bin staged 03:46:18** (`build/agent2/snap3d-run.txt`): build exit 0 (102.7 s), stage exit 0, MANIFEST
  checks 103 PASS / 0 FAIL / 34 NOTE, patch rows S2 18 / S3 28 / S3d 1; exe `B90DF683D0A57A21`, map `1C9AB7E3E471A6BA`,
  MANIFEST `368F9CE650EC56CE`, fingerprint `LEGO Dimensions native GPU 335ff2d47268f3a1`. prep-nb can run now; its log
  must say tag S3d.
- **rb-chain.ps1 -GuardOnly (Agent 2, 03:51; now `65A2CFE4BE73E146`): OK, sent to Agents 2 and 1 at 04:06.** The
  pre-image `rb-chain.ps1.pre-GuardOnly` = `3660069E` (the version reviewed above). My own difflib diff
  (`build/agent9/review/check-guardonly.py`) is byte-identical to `RB-diffs/rb-chain.ps1.GuardOnly.diff` (`443CC9C0`):
  +3/-1, i.e. a comment, `[switch]$GuardOnly`, and `if ($GuardOnly) { ...; exit 0 }` at line 41, after every step-0
  guard (variant, -Jobs, 08:30, nb from 07:00, driver guard) and before `$log`, so it writes nothing. No parameter-prefix
  clash; ASCII, LF, 0 parse errors. Unset (the nb command) it is a no-op. rb-tools-test 48 PASS / 0 FAIL (03:58,
  `build/agent2/rbt-logs/`), including both -GuardOnly cases (exit 0 clean; exit 4 with a fake run-rb2.ps1 process).

## S3.8 a-prof vs b-prof profile: Agent 1's question (04:07-04:19; write-tracking follow-up 04:43-04:46)

- **Question (Agent 1, 03:31):** does B's -10.5% `.text` show up in main-thread or GPU-thread time, and what are the S4
  codegen candidates. Agent 7's own table (`build/agent7/prof/ab-main.txt`, `ab-all.txt`) wasn't there at 04:13, so I
  ran Agent 7's tool on Agent 8's runs myself: `bench/agent7/prof_main_compare.py --top 30` via `cpu2.ps1`
  (PYTHONDONTWRITEBYTECODE=1), all exit 0. Outputs in `build/agent9/prof/`: `ab-main-a9` (Main XThread), `ab-all-a9`
  (`--all-threads`), `ab-render-a9` (`--thread-re '\(F80001A[8C]\)'`) and `ab-gpucmd-a9` (`--thread-re '^GPU
  Commands'`), each a .txt (plus .json for main and all) and a `*.stdout.txt`.
- **Runs** (`build/agent8/matrix/20261122-0357`; profile only, not timing). Agent 8: both were in the hidden-desktop
  slow state (E-cores at about 550 MHz) for most of the window, A and B alike.

| Run | Dir | Frames | fps | Median frame | Runner CPU (cores, mean) |
|---|---|---|---|---|---|
| a-prof (devoff2) | `runs/0357-a-prof-r1` | 10154 | 67.69 | 6.579 ms | 2.72 |
| b-prof (devoffB) | `runs/0401-b-prof-r1` | 10179 | 67.86 | 6.416 ms | 2.64 |

- **The sampling is too sparse to resolve 10%:** 191 vs 188 rounds in 150 s (about 1.3 rounds/s; the tool warns
  "CPU-saturated sampler"), so about 190 samples per thread. Every guest delta below is inside 2se.

| Thread (role) | Busy ms/frame A -> B (2se) | Guest-leaf ms/frame A -> B (2se) | Note |
|---|---|---|---|
| Main XThread (main) | 3.637 -> 3.532 (1.495) | 2.863 -> 2.355 = -0.509 (1.275) | |
| guest XThread F80001A8/AC (render) | 13.852 -> 13.735 (2.933) | 13.388 -> 12.793 = -0.595 (2.857) | about 94% busy (179/191) |
| GPU Commands (host, rexgpu-xenos) | 8.435 -> 9.418 = +0.983 (2.36) | 0 (host code) | blocked 6.35 -> 5.34 |
| TimerQueue (host) | 12.69 -> 11.85 | 0 | busy-spins in a `steady_clock` wait, about 0.86 core |
| all threads | 47.205 -> 47.170 | 20.43 -> 19.15 = -1.28, -6.3% (3.51) | |

- Separately significant, but host: write-tracking arm/protect +1.19 ms/f (2se 1.03), `rex::memory::Protect` /
  PhysicalHeap under sub_82B55588. Probably run variation, not codegen. **Agent 7 asked (04:41) whether B explains
  it** (14 -> 30 samples; EnablePhysicalMemoryAccessCallbacks inclusive 0.077 -> 0.628, GPU Commands re-arm 0.62 ->
  1.26). Checked 04:43-04:45: no. rexruntime.dll (`1C45C86977EC594C`), rexgpu-xenos.dll (`77A5300B885C5274`) and
  TracyClient.dll (`85044850B6C663B5`) are byte-identical in devoff2-bin and devoffB-bin, and neither
  `Protect@memory@rex` nor `EnablePhysicalMemoryAccessCallbacks` is in either exe map, so the write-tracking code is
  the same binary. `build/agent9/fncmp.py` (new, read-only) on sub_82B55588 (A `legodimensions_recomp.18.cpp:7192`,
  B `.418.cpp:7161`, 1040 -> 848 B): the same 5 calls in the same order (sub_82A2A0E8, 3x sub_82BD2808,
  sub_82A2A0E8), the same guest memory ops (REX_LOAD_U16 2, REX_LOAD_U32 7, REX_STORE_U32 1), only `ctx.` refs
  114 -> 95 (output `build/agent9/logs/fncmp-82B55588.txt`, RESULT SAME-CALLS-AND-MEMORY). So B can change only the
  timing against the GPU re-arm, not how much protect work the guest asks for. With 2se-borderline counts in the slow
  state, I call it run variation until a better-sampled profile or repeated a/b runs say otherwise.
- **The render thread is a GPU-wait spin.** Its root is sub_82B73D48; the hot chain is sub_83FBF7D0 (inclusive 13.0/13.1
  ms/f) -> sub_83FAF180 (self 7.97 -> 6.44, inclusive 9.98 -> 8.95) -> sub_83FA2698 (self 0.85 -> 1.26). In
  `build/agent9/install/batch-nolr/generated/default/`: sub_83FAF180 (`legodimensions_recomp.383.cpp` L37098) is a D3D
  ring-buffer/fence poll: `cctpl`, a ctr=4 loop of 8 `db16cyc`, `cctpm`, reads of device+11069/11024/11016/11148, a call
  to sub_83FA2698 (`.363.cpp` L37016: two loads, r13+256 -> +332, a time/fence value), a timeout compare, maybe a call to
  sub_83FC91D0, and a 0/1 return. sub_83FBF7D0 (`.53.cpp` L36902) loops `while (!passed(fence r4, *(+11024))) { if
  (!sub_83FAF180()) break; }`. So the render thread waits for a GPU fence (corrected in S4.1.1; first written here as a
  wait for ring-buffer space): faster guest code spins faster, and the frame doesn't get shorter. fps (+0.16%) is bound
  by the host GPU Commands / command-processor path.
- **Answer:** B's -10.5% `.text` doesn't show measurably in main- or GPU-thread time at this sampling rate. Guest time
  is down on every guest thread (main -0.51, render -0.60, all -1.28 ms/f), each inside the noise. GPU Commands is host
  code, so B can't change it (its +0.98 is noise). The only denser hint is the runner's CPU, 2.72 -> 2.64 cores (-2.9%)
  at the same fps. A real number needs window-4 timing or a profile at a usable sampling rate.
- **Hot-list sizes** (`python build/agent9/mapcmp.py --subs-from build/agent9/prof/ab-all-a9.txt`, output
  `build/agent9/logs/mapcmp-subs-prof.txt`): 79 of 79 found, A 242,144 B -> B 212,176 B (-12.38%). The host-native
  `__savegprlr_27`, `__restgprlr_29` (`native_saverest.cpp.obj`) and sub_83E46040 (`native_memops.cpp.obj`) don't change,
  as expected. Render chain: sub_83FAF180 1072 -> 832 (-22.4%), sub_83FBF7D0 1040 -> 784 (-24.6%), sub_83FA2698 80 -> 80,
  sub_82B73D48 6528 -> 5424 (-16.9%).
- **`mapcmp.py --subs NAMES` / `--subs-from FILE`** (added 04:06): the code size of named functions (`sub_XXXXXXXX` and
  `__save*`/`__rest*_N` tokens in first-seen order; exact name, else the base of a mangled `?name@...` public; default
  output `mapcmp-subs.txt`). The old mode still writes a byte-identical `mapcmp-AB.txt` (`70099735`,
  `logs/mapcmp-AB-recheck.txt`); `logs/mapcmp-subs-test.txt` found 15 of 16 names (`sub_00000000` correctly not).
- **S4 codegen candidates, ranked:**
  1. Stage B/C, `non_argument_as_local` + `non_volatile_as_local` together (S2 table: all 6 localization keys = -6.47%
     generated source against the pin). It removes the `__savegprlr_*`/`__restgprlr_*` calls, which take about 2 ms/f of
     render-thread samples (`__savegprlr_29` self 1.16/1.26, `__restgprlr_29` 0.85/0.63; `__chkstk` under
     `__restgprlr_29` 0.23 -> 0.55, maybe a musttail artifact).
  2. A spin-loop policy for `cctpl ... db16cyc ... bdnz` loops (`_mm_pause` or a yield): saves CPU, not fps.
  3. skip_lr, only after host changes (never for LEGO now).
  4. Flush-mode dataflow across labels.
  5. PGO devirtualization of `bctrl` sites.
  6. Guest memory macro experiments.
  7. `[[unlikely]]` on divide guards.
  8. The redundant mfmsr/mtmsrd fence.
  9. musttail for indirect tail calls.
- **Non-codegen, for Agent 1:** frames are GPU-path bound (rexgpu-xenos command processor); the host TimerQueue
  busy-spins about 0.86 core; the profiler's sampler (1.3 rounds/s here) needs fixing before a profile can resolve
  effects under 10%.
- **Sent** to Agents 1 and 7 at about 04:19. Agent 7's own tables (04:12/04:14) match: `build/agent7/prof/ab-all.txt` is
  identical to `ab-all-a9.txt` (0 of 319 lines differ); `ab-main.txt` (367 lines vs 275) only adds sections (handoff
  Main/render, joint-state tables), and every shared header and summary number is the same. No correction needed.
  Write-tracking reply to Agent 7 at 04:46 (above).

## S3.9 nativeB static check, task #17 item 1a (04:34-04:42)

- **nativeB built and staged** (Agent 2, `rb-chain.ps1 -Variant nb`, 04:12:09-04:34:06, wall 1,316.9 s; run-nb.ps1
  1,219.2 s; ninja 545/545, 0 `FAILED:`; `build/agent9/watch-nb.ps1` exit 0 at 04:34:06): `build/agent2/nativeB-bin`,
  exe `01C4D5A3E36FAC50`, map `C9259B05689E3AA5`, rexruntime `D1D66AC3716835AC`, rexgpu-xenos `EE0A661FB0C30FCB`,
  MANIFEST `E5CBF30A6132B00E`; stage checks 149 PASS / 0 FAIL / 34 NOTE; patch rows S1 0 / S2 18 / S3 28 / S3d 1.
  **All six checks PASS:**
- **mapcmp** (`build/agent9/logs/mapcmp-native.txt`): sub_ set 164,786 = 164,786 (0 only in A, 0 only in B); the
  `__imp__` alias sets are equal; 109 = 109 hooked aliases (not at their sub_), the same set; .text 161,476,587 ->
  144,715,307 B = -16,761,280 B (-10.38%), exactly the OFF devoff2 -> devoffB byte delta (S3.5); sub_ code bytes -10.58%
  (68,370 shrank, 1,835 grew); the same largest shrink/growth lists as OFF; 374/241 TU-local constants only in A/B, as OFF.
- **Native GPU fingerprint: different, as designed.** My expectation ("equal to A's") was wrong: `rexlego/CMakeLists.txt`
  :582-780 (the configured `generate-native-gpu-fingerprint.cmake`) makes it sha256(concatenated file-sha256 hex)[:16]
  over 271 inputs that include `legodimensions_config.toml` and 12 generated files (`legodimensions_recomp.61, 106, 115,
  162, 240, 262, 263, 290, 292, 316, 397.cpp` and `legodimensions_funcs.61.h`), so any codegen change changes it.
  `build/agent9/fpcheck.py` (new, read-only) recomputes both from the trees: A `335ff2d47268f3a1` and B
  `81d1c3a71be3c096`, each equal to its recorded `native-gpu-build.txt`; the same 271 relative paths in the same order;
  13 inputs differ, all codegen (config `7f775847` -> `e60eaf1c` and the 12 generated files); the 258 non-codegen inputs
  (native renderer sources, shader banks, plume, headers) are all equal. Output `build/agent9/logs/fpcheck-native.txt`,
  exit 0, 1.5 s. Agrees with Agent 2 (04:35).
- **Warnings** (`build/agent9/warncmp.py`, new: a signature is the path relative to its snapshot/game/SDK root plus the
  text and flag, line and column dropped; output `build/agent9/logs/warncmp-native.txt`): 225 lines, 50 signatures, 0 in
  generated code; by flag -Wdeprecated-declarations 212, -Wunused-value 12 (miniz.h), -Wswitch 1. 48 of the 50 are in
  A's native/OFF logs (snap1/2/3/3d) or B's OFF log. The other 2 are pre-existing: `thirdparty/plume/contrib/
  D3D12MemoryAllocator/src/D3D12MemAlloc.cpp` -Wswitch (`TYPE_COUNT`, 1 line) and `tools/gpu-aot/prelink_shader_cache.cpp`
  `getenv` deprecated (2 lines). Both sources are byte-identical in snap1 and snapB3 (`D66F6392`, `298BA7AF`) with
  identical normalized compile commands (compile_commands.json), and A's logged native builds are incremental (96, 23,
  8 and 6 steps) and never recompiled them; nativeB's fresh tree built them at steps 7, 8 and 11 of 545. warncmp exits
  1 ("CHECK") on these 2 by design.
- **MANIFEST** (269 lines): names batch-nolr (`build/agent9/bin/rexglue.exe` `37b32713`, `configs/batch-nolr.toml`, no
  skip_lr); the END line is identical to devoffB-bin's (`END files=872 bytes=481074943 TUs=430 ...
  config_sha=E60EAF1CEB575572`); SHA256SUMS `24ce1493`, 872 entries verified at 04:12:13; config `e60eaf1c`. I re-hashed
  the 8 staged files: each sha256 is in the MANIFEST, and rexruntime.dll, rexgpu-xenos.dll and TracyClient.dll equal
  native3d-bin's.
- **Gate** (`build/agent2/snapB3n-native-gate.log`): 525 DB entries, 432 generated TUs (sources.cmake lists 432),
  RESULT PASS, as expected (snap1-on: 533 and 440).
- **Host registers** (`build/agent9/hostregs2.ps1 -Root build\agent2\snapB3\DimensionsRecomp`, output
  `build/agent9/logs/host-regs-S3d.txt`): 1,101 files, 685 hits, 378 unique; against
  `build/agent9/diff/batch-nolr/host-regs.txt`: 0 new, 0 gone. S3d's draw.cpp adds no host access to
  ctx.ctr/cr/xer/reserved/fpscr/lr.
- **Sent** to Agents 10, 1 and 2 at 04:46, then `@@done 8`.

# Session 2: codegen options (task #8, re-issued 17:52)

All new options are root keys of the codegen TOML (`include/rex/codegen/config.h:105-109`, parsed at
`src/codegen/config.cpp:119-128`). They default to **false** in the SDK, and LEGO turns them on in its config (S2.10).
- None of the new keys is in `configFlags`, so they don't change `PPCImageInfo.codegen_flags`. The upstream keys
  (`skip_lr`, `*_as_local`) are in it. The batch sets the four `*_as_local` keys, so its `codegen_flags` differ from the
  pin's, which is one reason it needs a full rebuild.
- With every option off, the output is the pin's (T1: 883 of 886 files identical; the other 3 are `codegen.d` and two
  stamps).
- No header in the generated-code closure changed, and the SDK runtime needs no change.
- Sizes: B = bytes and MB = 10^6 B, of `generated/default`.

## S2.1 Summary

| Key | What it does | Correctness evidence | Delta in LEGO's generated code | Expected gain | Proposal |
|---|---|---|---|---|---|
| `skip_lr` (upstream key) | No `ctx.lr` store per `bl`/`bctrl`/`blrl` and no `mflr`/`mtlr` moves. Bodies that use LR as data keep LR (my LR-user rule) | Guest side: S2.2, fixture D (2 LR-use cases), T8 opt, guest exposure scan (S2.8), Agent 10 Review 4 rows 17-20 SAFE. **Host side: UNSAFE for LEGO** (Agent 10 row 21): hooks and `XexGetProcedureAddress` read `ctx.lr` to identify the caller (S2.2) | the 23:28 skip_lr batch: `ctx.lr` writes 719,232 → 5; 462.1 MB vs 481.0 MB without it | small, at every call | **OFF for LEGO** (dropped 23:51); possible once the host readers are gone |
| Stage A: `ctr_as_local`, `xer_as_local`, `reserved_as_local`, `cr_as_local` | CTR, XER, the lwarx reservation and CR0-7 become C++ locals. 425 functions keep ctx (per-function fallback) | S2.2; fixture D; handoff check is a hard error (0 hits in LEGO); T8 opt; Agent 10 rows 8 and 13; host-register scan clean (S2.2) | batch-nolr: `ctx.` refs 13.19M → 11.46M (−13.1%): 0.43M from the SO fold, 0.03M from flush elision, about 0.09M from rlwinm (the source register appears once instead of twice), the rest (about 1.18M) from Stage A. With skip_lr (locA): 490.0 → 468.3 MB (−4.42%) | the largest: fewer ctx loads and stores at every call and return | ON |
| `cr_compare_so_zero` | Compares use SO = 0 instead of loading XER.SO, where SO is provably 0 | S2.4 proof; Agent 10 Review 3 SAFE; test F | alone: 0 B (a no-op for LEGO); with Stage A: −1.73 MB | one load less per compare; dead CR stores fold | ON (it only acts with `xer_as_local`) |
| `rlwinm_lowering` | `rlwinm`/`rlwnm`/`rlwimi` as a 32-bit rotate and mask | S2.3: 408.7M evaluations, 0 mismatches; GF(2) proof; 35 asm tests; Agent 10 SAFE | 91,606 sites lowered (all but the 6,336 wrapping masks) | x64: 5 → 3, 7 → 4, 7 → 4 instructions | ON |
| `flush_mode_elision` | No flush-mode switch at 23 mode-independent builders | S2.5: 368.3M evaluations, 0 failures, 5/5 controls detected; Agent 10 Review 4 row 17 SAFE | −0.94 MB; switch lines −22.3% | fewer MXCSR writes in mixed FPU/VMX code | ON |
| `musttail_calls` | Guest tail calls as `[[clang::musttail]] return f(ctx, base);` | S2.6: emit test 480/0, acceptance 5/5, depth test; Agent 10 SAFE-IF | +1.15 MB; 63,167 sites | a guaranteed `jmp`, bounded stack, no call/ret pair | ON, never in Tracy builds |
| `vmx_vector_fallbacks` | SSE forms for 8 scalar VMX lane loops | S2.6: 148.6M cases × 3 configs, 0 mismatches; Agent 10 SAFE | 109 sites | x64 at v3: vrlw 31 → 10, vsrab 29 → 21 instructions | ON |
| `skip_msr` | | | | | OFF (STATUS decision 4) |
| Stage B/C: `non_argument_as_local` + `non_volatile_as_local` | r0, r2, r11, r12, f0, v32-v63 and the non-volatiles become locals; `__save*`/`__rest*` are elided | the fallback covers them; `non_argument_as_local` alone is a hard error (Agent 10 rows 8 and 13) | all 6 localization keys: −6.47% | more than Stage A | later, both together, after Stage A passes the game gate |

## S2.2 Register localization (item 1)

**Per-function fallback** (`BuildRegisterFallback`, `src/codegen/codegen_writer.cpp:162-235`; used by every `*_as_local` key)
- The pin rejected the whole config when any `*_as_local` key met an interior `body =` entry. That reject is gone.
  Instead, these functions keep all their registers in `ctx` (`BuilderContext::registersInCtx`, checked at
  `builders/context.cpp:53-113`):
  - every interior entry, meaning an entry inside another function's blocks: the 5 `body =` entries plus the ones codegen
    finds itself;
  - every body owner;
  - every function with a control transfer into an interior entry;
  - the `__save*`/`__rest*` helpers, which are interior entries of each other.
- The task said 7 `body =` entries; the config has 5 (lines 28, 31, 33, 37 and 45).
- LEGO: "Register localization fallback: 425 functions keep registers in ctx (155 interior entries, 5 of them body=;
  5 more body owners, 29 callers, 236 save/restore helpers)". That is out of about 165,000 functions.
- Why ctx mode is enough at those boundaries: a ctx-mode function stores every register to `ctx` before each call and
  return, and reloads it after, which is the pin's convention. The localized fields are the ones the upstream options already
  treat as dead across calls (CTR, XER, the reservation, the volatile CR fields) or as each function's own (CR2-CR4).
- **Safety net:** every branch, call or tail call into an interior entry from a function that localizes registers is
  counted (`check_register_handoff`, `builders/context.cpp:181-189`). Any count above 0 blocks codegen ("Code generation
  blocked: N control transfers reach an interior entry with localized registers", `codegen_writer.cpp:598-621`). LEGO: 0.
- **Combination check:** `non_argument_as_local` without `non_volatile_as_local` is a hard error (`codegen_writer.cpp:500`):
  the save/restore helpers read r11 and r12 from ctx. Agent 10 rated the combination UNSAFE (row 8); the hard error is row 13.
- **Host-register scan for Stage A** (`build/agent9/hostregs.ps1` → `build/agent9/diff/batch-nolr/host-regs.txt`; 685
  hits in 1,101 files of `rexlego/src` and the SDK's `src`/`include`). Host code touches `ctx.cr*`, `ctx.ctr`, `ctx.xer` or
  `ctx.reserved` only in these places:
  - self-contained `REX_HOOK_RAW` reimplementations (native_lock_elide: 7 functions; crash_guards: 2; native_constants,
    native_atomics, native_memops, native_saverest);
  - the xthread context save/restore (lines 1170-1386);
  - console fingerprint diagnostics.

  None of them reads a caller's CR/CTR/XER on entry. The host writes (native_atomics `SetCr0`, native_memops 76-77) are
  ABI-volatile, and no caller reads them. The 7 mid-asm hooks take GPRs only, and fpscr is not localized. One caveat:
  `LEGO_NATIVE_MEMOPS_VALIDATE=1` (a diagnostic mode, off by default) compares `ctx.ctr`/`cr0` with the generated memset's.
  Under Stage A the generated routine leaves them unchanged in ctx, so the validator reports a false "Native memset
  mismatch" and falls back to the generated result, which is still correct.

**skip_lr** (an upstream key; the codegen supports it now, but LEGO can't use it: host code reads `ctx.lr`)
- **Not for LEGO (Agent 10 Review 4 row 21: UNSAFE; dropped from S2.10 at 23:51).** Host code reads `ctx.lr` to
  identify its guest caller. Under skip_lr no guest code writes `ctx.lr`, so it holds whatever the last host-side or ctx-mode
  writer left, e.g. `0xBCBCBCBC` from `FunctionDispatcher::Execute` (`function_dispatcher.cpp:124-129`). Functional readers:
  - `rexlego/src/gpu_native/hooks_buffer.cpp:388-389` → `:268-276`: the `sub_83FC49E8` hook drains the native worker's
    queued pool copies only when `ctx.lr == 0x83F9B660`. Without the drain the copies race with the header rewrite (Agent 10).
  - `rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_modules.cpp:155-177`: `XexGetProcedureAddress` picks the thunk module from
    `ctx.lr`. With `0xBCBCBCBC`, `AllocateThunk` fails (3 LEGO call sites, all status-checked) (Agent 10).
  - `rexlego/src/native_slot_growth.cpp:63,76`: the Grow/Release thunks return r3 = 0 unless `ctx.lr` is `0x82A33FC4` or
    `0x82A3B88C`, so native slot growth would be off (found by me).
  - `rexlego/src/settings_native_hooks.cpp:174`: the pause-menu Back-row hook needs `ctx.lr == 0x839D11B0` (found by me).
  - Diagnostics only (wrong caller names, no behaviour change): hooks_buffer 309/326/367/400, hooks_state 257,
    crash_reporter.h 79/96, name_trace 79/86, draw 5748, native_skin_diagnostics 124-235, settings_native_bridge 762,
    console_commands 947/1017, xboxkrnl_rtl 524/622/655.
  - My guest-side exposure scan (below) can't see host readers; that's how I missed them. To enable skip_lr later: the
    owners replace these `ctx.lr` decisions (e.g. a mid-asm hook at the call site), or a codegen option keeps the `ctx.lr`
    store at calls to imports and to listed functions.
- With the key on, `bl`, `bctrl` and `blrl` store no `ctx.lr`, and `mflr`/`mtlr` emit nothing (control_flow.cpp:67, 104
  and 190; system.cpp:245 and 313). That is safe where LR only carries the return address: `blr` is `return;` either way,
  and the prologue's `mflr r12` / epilogue's `mtlr r12` only move it through the stack.
- **New: bodies that use LR as data keep LR** (`codegen_writer.cpp:350-388`; `BuilderContext::trackLr()`,
  context.cpp:41-42). A body keeps every LR write and read, exactly as without skip_lr, if it contains either:
  - a `bclrl`, i.e. `blrl` or a conditional form (word & 0xFC0007FF == 0x4C000021);
  - a `bl` that `build_bl` emits as a local goto (`classifyTarget` gives InternalLabel; the `bl $+4; mflr rX` address idiom).
  
  LEGO (the 23:28 skip_lr batch): "skip_lr: 1 functions use LR as data (blrl, or bl to a local label) and keep LR". That
  function is `sub_83E5C830` (`mtlr r3; blrl`, an indirect call through LR). Its 5 LR writes were the only ones left in that
  batch (off3: 719,232).
- **Residual guest-side risk:** a function that reads its *incoming* LR as data reads a stale `ctx.lr`. Examples: a
  `mflr r3; blr` return-address helper, `_ReturnAddress`-style logging, or `mtctr`/`bctr` through a saved LR. Upstream
  skip_lr has the same limit.
- **Guest exposure scan of the skip_lr batch** (`build/agent9/lrscan.py`, output `build/agent9/diff/batch/lrscan.tsv`, 104 s): after
  each `mflr rX`, every read of rX up to its next write must be a store to the stack (`stw`/`std`/`stwu rX,d(r1)`) or an
  `mtlr`. Text order over-approximates control flow; the scanner flags the synthetic positives and passes the samples.
  - 128,920 `mflr` in 165,023 functions; 1 flagged: `sub_83E49CA0`, a setjmp (it saves f14-f31, r13-r31, CR, r1 and LR
    into the buffer at r3, LR at offset 308, and returns 0; 2 call sites).
  - Only a longjmp reads that saved LR, and the pin can't longjmp either: the restore's `blr` is `return;`, and LEGO's
    config sets no setjmp/longjmp address. So the stale value changes nothing the pin could do.
- **Fixture D** (`tests/regression/emit_interior_entries.cpp`, binary `regression_interior_entries`) covers 7
  register-localization fallback cases, 5 switch-table fallback cases, the safety net, 2 skip_lr LR-use cases (`blrl` and
  `bl $+4`) and 16 rejection cases. Run7 (tool `37B32713B7516402`, 23:16): PASS, all cases including the 2 LR-use cases.
- **Batch output** (count2 batch-nolr vs off3, `build/agent9/diff/batch-nolr/summary.txt`): the same 165,023 functions
  (0 only in either). `ctx.` references 13,192,705 → 11,464,410 (−13.1%); `ctx.lr` writes unchanged (719,232). Function
  text 459,057,937 → 450,116,310 B (−1.95%): 46,385 functions smaller, 76,225 equal, 42,413 larger; per-function ratio p1
  0.908, p5 0.953, p50 1.000, p95 1.085, p99 1.114. The body owner `sub_8307C528` stays in ctx mode (`ctx.cr6`,
  `ctx.ctr`) and gains 1 musttail (`__restgprlr_27`). The median sample `sub_82827AD0` shows the set without skip_lr:
  `cr6` and `ctr` as locals, compares with `{}`, the tail call to `__restgprlr_29` as musttail, and every `mflr` and
  `ctx.lr =` store kept.
- **batch vs batch-nolr** (`build/agent9/lrdiff.py` → `build/agent9/diff/batch-nolr/lrdiff-batch-vs-nolr.txt`, 80 s):
  after dropping each line that contains `ctx.lr`, 165,017 of 165,023 functions are identical. The other 6 differ only by 7
  hook `extern` declarations that moved to another TU (TU boundaries shift). So batch-nolr is exactly the skip_lr batch
  with the LR lines put back, and the batch's checks (samples, rlwinm hand check, flush counts) carry over. The skip_lr
  batch had `ctx.` refs −21.2% and function text −6.06% (median 0.923).

**Deltas** (from the END lines in `build/agent9/logs/gen-steps.txt`; one TU is 2 files, plus 10 fixed files)

| Variant | Keys | Files | TUs | Bytes | vs pin |
|---|---|---|---|---|---|
| pin (`build/agent2/gen-noflag`) | none | 886 | 438 | 490,008,297 | |
| off3 (dev tool) | none | 886 | 438 | 490,008,269 | −28 B (`codegen.d` paths) |
| locA | skip_lr + Stage A | 846 | 418 | 468,331,963 | −4.42% |
| crsoA | locA + `cr_compare_so_zero` | 842 | 416 | 466,602,388 | −4.78% |
| locAll | all 6 localization keys | 828 | 409 | 458,291,109 | −6.47% |
| batch (superseded 23:51) | S2.10 + `skip_lr` | 834 | 412 | 462,089,412 | −5.70% |
| **batch-nolr** | S2.10 (9 keys, no `skip_lr`) | 870 | 430 | 481,048,529 | −1.83% |

There are fewer TUs because the partitioner fills each TU up to a size budget.

## S2.3 `rlwinm_lowering` (item 2)

- **Pin:** every `rlwinm`, `rlwnm` and `rlwimi` is a 64-bit rotate of the doubled word, then a 64-bit mask.
- **With the key on** (`builders/logical.cpp:281` rlwimi, `:301` rlwinm, `:319` rlwnm; helpers in `builders/rotate_mask.h`):
  masks with mb ≤ me become a 32-bit rotate and a 32-bit mask. Wrapping masks (mb > me) keep the pin form.
- **Evidence** (subagent A, `bench/agent9/rlwinm/README.md`):
  - every (sh, mb, me) for all three instructions: 408,680,448 evaluations, 0 mismatches;
  - sensitivity: 33,792 of 33,792 wrong pairings detected for rlwinm, and the same for rlwimi;
  - proof: both texts are GF(2)-linear in (rA, rS) (the OR'd parts are bit-disjoint, so OR acts as XOR), so agreement
    on the basis vectors means agreement on every input;
  - `tests/ppc/asm/instr_rlw_lowering.s`: 35 tests, which T8 runs with the key on;
  - Agent 10 Review 2 row 9: SAFE. Agent 10 re-derived the 35 tests (77 checks) with 0 mismatches.
- x64 at the game's flags: rotate + mask 5 → 3 instructions, rlwimi 7 → 4, rlwnm 7 → 4.
- **Delta in LEGO** (count2, off3 → batch-nolr; the same in the skip_lr batch): `__builtin_rotateleft64` 101,824 → 10,218 and the doubled-word text
  `.u64 << 32), ` 97,942 → 6,336, so 91,606 `rlw*` sites are lowered. The 6,336 left are wrapping masks: in batch TUs 0-2,
  104 of the 104 generic sites have mb > me. The other 3,882 `rotateleft64` are 64-bit `rld*` forms, unchanged.
  `__builtin_rotateleft32` +503 (rotate-and-mask forms; `rotlwi` already used it).
- **By eye** (`build/agent9/diff/batch/rlw-samples.txt`, made by `build/agent9/rlwsample.py`):
  - `rlwinm r11,r30,1,0,30`: `__builtin_rotateleft64(ctx.r30.u32 | (ctx.r30.u64 << 32), 1) & 0xFFFFFFFE` →
    `ctx.r30.u32 << 1`;
  - `rlwimi r11,r10,3,0,28` → `(ctx.r10.u32 << 3) | (ctx.r11.u64 & 0xFFFFFFFF00000007)`;
  - `rlwimi r11,r31,2,0,30` → `(__builtin_rotateleft32(ctx.r31.u32, 2) & 0xFFFFFFFE) | (ctx.r11.u64 & 0xFFFFFFFF00000001)`;
  - the wrapping `rlwinm r9,r10,0,9,7` keeps the pin text.

## S2.4 Cheaper CR compare (`cr_compare_so_zero`) and lazy XER.CA (item 3)

**Pin:** each compare stores the `lt`, `gt`, `eq` and `so` bytes, and `so` is loaded from `xer.so`: 4 byte stores plus
1 load. **With the key on:** in a function where XER.SO is provably 0 at every compare, the compare's XER operand is `{}`
(SO = 0, `builders/helpers.h:68`). The load goes away and the `so` store becomes a constant, which clang drops when CR is a
local that nothing reads.

**Why SO is 0** (comment at `codegen_writer.cpp:320-330`; per-function rule at `function_graph.cpp:569-573`)
1. Generated code writes XER.SO in two places only: `mtxer` (`build_mtspr`, system.cpp:356) and mid-asm hooks that take
   `xer`. The OE forms (`addo` etc.) set only CA; SO isn't modelled.
2. Every runtime `PPCContext` starts with SO = 0, and the runtime only copies it (`XThread::SaveContext/LoadContext`).
   - ThreadState value-initializes it, and so do `GuestToHostFunction`, the auto-isolating `ImportFunction` call and the
     hook call contexts.
   - A local XER is zero-initialized (`PPCXERRegister xer{}`).
3. So SO is 0 at every compare in two cases (bodies are scanned through their `body =` owners):
   - the body contains no writer and its XER is a local;
   - the body contains no writer, and no body that keeps XER in ctx has a writer (`ctxXerWritten`).
4. The one exception is `rex::CallFrame` (hook.h), which leaves XER uninitialized. A guest call through it reads an
   indeterminate SO with or without the key, and no LEGO code uses it.
- **LEGO:** there is one SO writer, `sub_83E5C88C` (an `mtxer`).
  - Without `xer_as_local` its XER is in ctx, so no function folds and the key is a no-op (crso equals off3 byte for byte).
  - With Stage A its XER is a local like every other function's. Batch INFO line: "cr_compare_so_zero: 1 functions write
    XER.SO (0 keep XER in ctx); the others compare with SO = 0". Every function except the writer folds: crsoA − locA =
    −1,729,575 B. There the fold is exactly what clang could do itself if the local XER never escaped.
  - Batch counts: all 430,626 integer compares that read `ctx.xer` in off3 compare with `{}` (the writer has no compares).
  - The writer is a context-restore routine: it loads r14-r31, f14-f31, FPSCR, CR, XER, CTR, r2 and r1 from the buffer at
    r4, then `mtlr r3; blr`. Its `blr` is `return;` in the pin too, so it never jumps to r3. With Stage A the CR, XER and
    CTR it restores are locals that die at the return: the assumption `*_as_local` makes for every function. Nothing else
    in LEGO sets SO, so a restored SO = 1 needs a buffer built with SO = 1. The game gate covers it.
- **Evidence:** Agent 10 Review 3 row 16: SAFE at the default and sound when ON; "turn on after ask F". Ask F is test F
  plus the crso/crsoA diffs (done). Test F = `tests/ppc/asm/instr_cr_so_fold.s`: an `mtxer` SO writer with compares in the
  same function, in a callee, and after a clear, run by T8 with the key on.
  - T8 (23:30): test_same and test_clear pass in default, opt and crso. test_call passes in default and crso, where the
    callee reads `ctx.xer`; crso's functions differ from default only in 255 compare lines (`ctx.xer` → `{}`), all in test
    binaries without `mtxer`.
  - Under opt, test_call is excluded: `xer_as_local` makes XER dead across calls (upstream semantics), so the callee
    compares with SO = 0 (r3 = 0x48000020, as predicted). That is the Stage A assumption, not the fold.

**Lazy XER.CA: not a separate option.** With `xer_as_local`, a CA write that nothing reads is a dead store to a local, and
clang deletes it. CA values that feed `adde`, `subfe` or `addze` stay. Only the 425 fallback functions keep eager CA in
ctx, as the pin does. A codegen liveness pass would only help those 425, so I dropped it. I also dropped the inert keys
that session 1 proposed (`cr_bit_liveness`, `lazy_xer_ca`, `flush_mode_dataflow`).

## S2.5 `flush_mode_elision` (item 4)

- **The "77 sites"** are the 75 builders that call `ctx.emit_set_flush_mode(enable)`, plus its declaration and definition.
- **Method** (subagent B, `bench/agent9/flush/README.md`): the harness compiles each builder's emitted statements with the
  game's flags and runs them with FTZ/DAZ on and off under all 4 rounding modes. That is 368,252,256 case evaluations, plus
  exhaustive exponent-0 sweeps.
- **Result:**
  - **23 builders are mode-independent** (bit-identical in both modes): fabs, fnabs, fneg, fmr, fcfid, fctidz, fctiwz;
    lfd, lfdx, lfdu, lfdux, stfd, stfdx, stfdux, stfiwx, stfdu; vrfin, vrfiz, vctsxs, vcfsx, vcfux, vctuxs, vpkd3d128, and
    their 128 aliases.
  - With the key on they call `emitFlushModeUnlessIndependent` (`builders/flush_mode.h:23`), which emits nothing and leaves
    `ctx.csrState` unchanged. So the next mode-dependent op still switches exactly when it needs to.
  - The other 52 depend on the mode and keep their switch. 5 of them are controls the harness must flag, and it flags all 5.
  - So 23 of the "77" are provably redundant, not all 77.
- **Equivalence:**
  - Guest-visible results are bit-identical. The flush bits aren't architected guest state: `mffs` returns only RN,
    `mtfsf` keeps the flush bits, and every MXCSR exception is masked.
  - The one difference: host code on the guest thread (imports, MMIO handlers, mid-asm hooks) can run in the other flush
    mode for longer. It already can today, because integer code and calls never switch the mode (README "Accepted
    non-equivalence").
- **Delta:**
  - Replay over the pin's output: 136,802 → 106,248 switch lines (−30,554, −22.3%). The scanner is validated: it
    reproduces all 136,802 switch lines, with 0 mismatches.
  - Generated bytes: flush − off3 = −940,061 B.
  - Batch output (count2): `FlushMode` 136,802 → 106,248, exactly the replay's prediction. Sample `sub_8395B690`: 3 switch
    lines → 1.
- **Not done:** a dataflow pass across labels (estimate: 76,587 switch lines with the key on), and the asm test
  `instr_flush_independent.s`.
- **Review:** Agent 10 Review 4 row 17 (log row corrected 23:46): SAFE at the default (byte-identical) and SAFE when ON.

## S2.6 `musttail_calls` and `vmx_vector_fallbacks` (item 5)

**musttail** (subagent C, `bench/agent9/musttail/README.md`; code at `builders/context.cpp:191-300`)
- **What changes:** a guest tail call (a `b` to another function) becomes `[[clang::musttail]] return f(ctx, base);`
  instead of `f(ctx, base); return;`. clang then has to emit a `jmp` or fail the compile, so tail chains no longer grow the
  host stack.
- **Skipped (the pin text stays):** SEH bodies, setjmp callers, call text that isn't a plain direct call (longjmp/setjmp,
  `__save*`/`__rest*` calls elided under Stage C, the SEH-funclet handoff, unresolved targets), and indirect tail calls.
  A plain `b __restgprlr_NN` epilogue is an ordinary tail call and gets musttail. LEGO's config sets no setjmp/longjmp
  address.
- **Batch:** 63,167 sites (count2), the same as the musttail-only variant. Sample `sub_82C10CD8`: three
  `sub_82C10C10(ctx, base); return;` → `[[clang::musttail]] return sub_82C10C10(ctx, base);`.
- **Evidence:**
  - emit test: 480 checks, 0 failures.
  - acceptance: 5/5; the negative cases (SEH, try, a Tracy zone, a signature mismatch) fail as expected.
  - TU 61 at -O3: 101 tail `jmp` against 73, and 0 call → ret pairs against 19.
  - depth test (1M hops, 1 MB stack): at -O2 with an escaped local it overflows today and passes with musttail.
- **Scale:** 63,167 sites in LEGO; the generated source grows by 1,154,646 B.
- **Agent 10 row 11: SAFE-IF**, and all three conditions hold for the batch:
  - (a) Off in Tracy builds (`REXGLUE_PROFILE_GUEST_FUNCTIONS` + `REXGLUE_ENABLE_PROFILING`). A Tracy zone has a destructor,
    so musttail fails to compile there. The game's Release builds have no Tracy. C's README proposes a `REX_MUSTTAIL` template
    guard; templates aren't mine to edit.
  - (b) Caller and callee signatures are identical. Every guest function is `void(PPCContext&, uint8_t*)`.
  - (c) No mid-asm hook keeps a pointer to a caller local. LEGO's 7 hooks take only GPRs (r3, r4, r8-r11, r19, r22, r26,
    r30), which stay in ctx under Stage A.
- **All-TU compile:** Agent 2's full build is the all-TU check. If any TU fails, drop `musttail_calls` (rollback step 2).

**VMX fallbacks** (subagent C, `bench/agent9/vmx/README.md`)
- **What changes:** `vsubsws`, `vsrb`, `vsrab`, `vrlw`, `vsraw`, `vsrw`, `vpkuhus` and `vpkuwus` (vector.cpp:326, 919, 951,
  1010, 1100, 1123, 1235, 1278) get SSE forms instead of per-lane loops. `vpku*` gets one only when vD aliases neither
  input, because the scalar form is wrong when vD == vB (pre-existing, S2.9).
- **Evidence:** 148,555,140 cases × 3 configs (SSE4.1, x86-64-v3, no native), 0 mismatches against the scalar form.
  Agent 10 row 10: SAFE.
- **x64 at v3:** vrlw 31 → 10 instructions, vsrab 29 → 21.
- **LEGO:** 109 sites (vsraw 44, vsubsws 26, vsrw 19, vpkuhus 14, vsrab 6).

## S2.7 Test infrastructure (T8)

- **`recompile-tests --config <toml>`** (`src/rexglue/commands/test_recompiler.cpp`): loads an SDK codegen TOML without
  `file_path` (the options are preset once), with a per-binary config. It used to fail with "Missing required field:
  file_path".
- **REGISTER_OUT on CR fields** is dropped with a WARN under `cr_as_local`, because CR is then a local the harness can't
  read back. The 6 extra opt failures in the first pass were exactly these: divdu 10/11, divwu 13/14, mulhwu 7/8.
- **ParseTestSpecs** no longer swallows the test after an unannotated label. The count goes from 1496 to 1515:
  `test_tailcall_uncond`, test F's 3, and 15 vpkd3d128/vupkd3d128 tests that had no blank line before their label.
- **`src/codegen/test_support.cpp`:** a `b`/`bc` to another test's entry is now a real tail call. Before, seq.test_tailcall_chain
  and cond_taken crashed with 0xC0000409 in every variant.
- **Test files:** `tests/ppc/opt_config.toml` holds the 10 keys of the skip_lr batch (S2.10's 9 plus `skip_lr`, which keeps
  T8 coverage of the upstream key and my LR-user rule), and test F is `tests/ppc/asm/instr_cr_so_fold.s`.
- **Proposed, not mine to apply:** a `ppc_tests_opt` suite in `tests/ppc/CMakeLists.txt` (A's README §(c)), and listing
  `ppc_config.h` as an OUTPUT of the custom command.
- **First pass** (old tool `E35C3D09AB3DA2B6`): default 1494/1496, opt 1488/1496.
- **Rerun** (final tool `37B32713B7516402`, 23:30; subagent A, `bench/agent9/ppctests/README.md`): 1515 tests per config.
  - default 1514/1515, crso 1514/1515, opt (`tests/ppc/opt_config.toml`, all 10 batch keys) 1513/1514 plus test F's
    test_call excluded (S2.4).
  - The one failure is the same in all three: `vupkd3d128.test_short2_3`, one of the 15 tests the parser fix brought back.
    Its generated code is identical in every config: a pre-existing emitter gap (S2.9), not an option bug.
  - No crashes: the 4 seq tail-call tests pass everywhere, with musttail in opt. The 6 opt REGISTER_OUT cr failures are
    gone (gen.log: "dropped 6 REGISTER_OUT cr expectations").
  - **For S2.10's 9 keys** (opt minus `skip_lr` = build B's key set): the opt9 run (session 3, S3.3) gives 1513/1514
    plus `test_call` excluded, the same as opt, with the same single pre-existing failure. Its generated functions differ
    from opt's only in 9 `ctx.lr` lines; the cases, config and decls files are byte-identical.

## S2.8 Verification matrix

| Check | Result |
|---|---|
| T1: all options off = pin | off4 with the final tool `37B32713`: 883/886 files identical. The other 3 are `codegen.d` (−28 B) and 2 stamps, as for off3 (`build/agent9/logs/chain4-steps.txt`). PASS |
| Fixture D (`regression_interior_entries`) | run7 on the final tool: PASS (7 fallback, 5 switch-table, safety net, 2 skip_lr LR-use, 16 rejection cases) |
| T8 default / crso / opt / opt9, 1515 tests each | default 1514/1515; crso 1514/1515 (255 compare lines differ from default); opt 1513/1514, plus test F's `test_call` excluded (S2.4). The one failure, `vupkd3d128.test_short2_3`, is the same in all three and pre-existing (S2.9). No crashes (S2.7). opt has the 10 keys including `skip_lr`. opt9 (S2.10's 9 keys = B's, session 3) is the same as opt: 1513/1514 plus `test_call` excluded (S3.3) |
| Batch variant (batch-nolr, 23:52, `build/agent9/logs/chain5-steps.txt`) | 870 files, 481,048,529 B (pin: 886 files, 490,008,269 B; −1.83%), 430 TUs (last `legodimensions_recomp.429.cpp`), 81.1 s. No "Code generation blocked", 0 handoff errors. INFO: "Register localization fallback: 425 functions keep registers in ctx (155 interior entries, 5 of them body=; 5 more body owners, 29 callers, 236 save/restore helpers)"; "cr_compare_so_zero: 1 functions write XER.SO (0 keep XER in ctx)". Superseded: the 23:18 skip_lr batch (834 files, 462,089,412 B, −5.70%, 412 TUs; it also printed "skip_lr: 1 functions use LR as data … and keep LR") |
| Counts, off3 vs batch-nolr (`build/agent9/diff/batch-nolr/summary.txt`) | `DEFINE_REX_FUNC` 165,023 in both, none only in one. `ctx.` refs 13,192,705 → 11,464,410 (−13.1%). Flush-mode switch lines 136,802 → 106,248 (exactly B's replay prediction). `ctx.lr` writes 719,232 in both (no skip_lr). Pin-form rotates 97,942 → 6,336 (91,606 lowered; the rest are wrapping masks); `rotl64` 101,824 → 10,218, `rotl32` 11,405 → 11,908. `[[clang::musttail]]` 0 → 63,167. Compares that read `ctx.xer.so`: 430,626 → 0, all now SO = 0. Lines +17,800. Function text −1.95%; per-function size ratio p1 0.908, p50 1.000, p99 1.114. (The skip_lr batch: `ctx.` refs −21.2%, `ctx.lr` writes 5, lines −830,382, function text −6.06%) |
| Sample functions by eye | batch-nolr (`build/agent9/diff/batch-nolr/samples`), correct: `sub_82827AD0` (median ratio 1.000: `cr6`/`ctr` locals, `{}` compares, musttail to `__restgprlr_29`, every `mflr` and `ctx.lr =` kept) and `sub_8395B690` (flush 3 → 1: the switches before `stfd` and `fmr` go, the one before `stfs` stays). The skip_lr batch, which differs from batch-nolr only in LR lines (lrdiff row), all correct: `sub_82FC12B8` (median ratio), `sub_82C10CD8` (3 musttail), `sub_8395B690` (flush 3 → 1), `sub_83048108` (SO fold), `sub_8307C528` (body owner: stays in ctx, 1 musttail to `__restgprlr_27`), `sub_83E5C88C` (the XER.SO writer, a context restore; its CR/XER/CTR are locals), `sub_83E5C830` (keeps LR: `mtlr r3; blrl`). rlwinm in TUs 0-2: 2,239 sites lowered, 104 generic (all wrapping masks); lowered forms checked by hand (`build/agent9/diff/batch/rlw-samples.txt`) |
| skip_lr guest exposure scan (superseded: skip_lr is off, S2.2; the scan can't see host readers) (`build/agent9/lrscan.py` → `build/agent9/diff/batch/lrscan.tsv`) | 128,920 `mflr` in 165,023 functions; 1 flagged: `sub_83E49CA0`, a setjmp. It saves f14-f31, r13-r31, CR, r1 and LR into the buffer at r3, then returns 0 (2 callers). Only a longjmp reads that LR, and the pin can't longjmp either (no setjmp/longjmp address in the config), so there's no regression |
| batch vs batch-nolr (`build/agent9/lrdiff.py` → `build/agent9/diff/batch-nolr/lrdiff-batch-vs-nolr.txt`, 00:00) | After dropping the lines that contain `ctx.lr`: 165,017 of 165,023 functions are identical; the other 6 differ only by 7 hook `extern` declarations that moved to another TU. `ctx.lr` lines: 7 vs 848,153. PASS: the batch's checks carry over to batch-nolr |
| Heavy TUs at game flags (`bench/agent9/musttail/heavy_batch.txt`; skip_lr batch, 23:31) | TUs 304/233/52, the same functions as baseline: `.obj` 88%, `.text` 84% of baseline. These synthetic TUs took 3.3× baseline's compile CPU (169.7 vs 51.1 s), but that's the harness: each one pulls its functions from 219-246 batch TUs and includes all their funcs headers. The real batch TUs compiled as-is (TUs 2, 179, 248 and 215; 1.03-1.77 MB) cost 9.5-10.9 s CPU per source MB, against 6.0-11.2 for the baseline TUs, so the full build should take about baseline's time. Synthetic TU 61 failed (its hook externs live in other TUs: a harness artifact); real TU 215 compiled. batch-nolr TUs are the same code plus the LR lines |
| Agent 10 | rows 8-16 SAFE or SAFE-IF. Review 4 (log row corrected 23:46): rows 17-20 (flush elision, the LR-user rule, test infra and fixture D, inert-key removal) are SAFE at the default (byte-identical) and SAFE when ON. Row 21: `skip_lr` itself is UNSAFE for LEGO (host `ctx.lr` readers, S2.2), so it is dropped and batch-nolr regenerated. Condition 1 is met (Agent 10, 00:12): its own per-function diff (`build/agent10/review/r5/lrdiff-report.txt`) finds batch-nolr's LR statements equal to off4's in all 165,023 functions, the same 165,017 + 6 split as my lrdiff, and `SHA256SUMS.txt` matching all 872 files. Row 21 now lists my two extra readers. Conditions 2 (T8), 3 (off4 = pin) and 5 (fixture D) are met |
| Game gate (Agent 8) | B built clean by Agent 2, 02:22:46-02:40:30 (S3.5). **Front-end gate PASS** (Agent 10, 03:31; partial coverage), on `build/agent2/devoffB-bin` against devoff2, in Agent 8's slot with Agent 3's menu harness; tie-break with a 90-s idle tail (S3.6) |

## S2.9 Pre-existing bugs (documented, not fixed: a fix would change the default output)

- **MTCTR constant:** `function_graph.cpp:632` uses 0x7C0003A6, but `mtctr` is 0x7C0903A6, so late jump-table detection
  is dead code. The handoff check (S2.2) catches any interior entry it would have missed.
- **vpkd3d128 type 4 (NORMSHORT4), shift 3** writes `u16[8..9]`, out of bounds of a 128-bit vector.
- **Scalar `vpkuhus`/`vpkuwus` are wrong when vD == vB.** LEGO has 14 `vpkuhus128` sites, none aliased.
- Only the helper-based compares use `compareXer` (Agent 10 note b). That's a missed fold, not a bug.
- **vupkd3d128 SHORT2 overflow** (found by T8's restored tests): unpacking -32768 gives 0x403F8000, but the test expects the
  QNaN 0x7FC00000 (Xenia's negative-overflow rule). The same code is generated with every option set.

## S2.10 Exact config (proposal; I don't edit the live file)

Insert these root keys into `DimensionsRecomp/rexlego/legodimensions_config.toml` after line 22, before `[functions]`
(line 24), with CRLF line endings. The 5 `body =` entries stay as they are. This is the block that
`build/agent9/make-batch-config.ps1` writes (in `configs/batch-nolr.toml` it is lines 24-38, `[functions]` moves to line 40).
`skip_lr` was in it until 23:51: it is dropped because host code reads `ctx.lr` (S2.2).

```toml
# Codegen options (task #8, Agent 9). Root keys: they must come before [functions].
# Stage A register localization. The body= entries, their owners and their callers keep registers in ctx automatically.
ctr_as_local = true
xer_as_local = true
reserved_as_local = true
cr_as_local = true
# Compares use SO = 0 where XER.SO is provably 0 (it changes nothing without xer_as_local).
cr_compare_so_zero = true
rlwinm_lowering = true
flush_mode_elision = true
vmx_vector_fallbacks = true
# Never in a Tracy build (REXGLUE_PROFILE_GUEST_FUNCTIONS + REXGLUE_ENABLE_PROFILING): musttail fails to compile there.
musttail_calls = true
# Not for LEGO: skip_lr (host hooks and XexGetProcedureAddress read ctx.lr as the caller), skip_msr (STATUS decision 4).
# Later: non_argument_as_local + non_volatile_as_local (Stage B/C: together, after the gate).
```

# Session 2: regen+build recipe (for Agent 2)

0. **Prerequisites:** Agent 10 Review 4: rows 17-20 SAFE, and row 21 (skip_lr UNSAFE for LEGO) is resolved by dropping
   skip_lr and regenerating (done, 23:52); T8 opt green (done, S2.7); the heavy TUs compile (S2.8). Agent 1
   gives the slot.
1. **Tool:** `build/agent9/bin/rexglue.exe` (built 23:16), sha256
   `37B32713B7516402344BB4DDB402A3CD4131353ADC1AEF10E1602122E9B6036A`, with the pin's `rexruntime.dll` and `TracyClient.dll` next
   to it. The pin tool can't be used, because it rejects `body =` together with localization keys.
2. **Regen** (I run it; the output is kept):
   - `build/agent9/make-batch-config.ps1 -Out batch-nolr.toml` writes `build/agent9/configs/batch-nolr.toml`: the live
     config with the S2.10 block after line 22 (BOM and CRLF kept; it checks that removing the block gives back the live
     file). 19,002 B, sha256 `E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090`.
   - `gen.ps1 -Variant batch-nolr -ConfigFile build\agent9\configs\batch-nolr.toml` copies that file byte for byte and
     writes `build/agent9/generated/batch-nolr/default` (870 files, 481,048,529 B, 430 TUs; 23:52, 81 s). Gate: no "Code
     generation blocked", 0 handoff errors (both hold).
   - Superseded: `configs/batch.toml` (`B2727250…`, with `skip_lr`) and `generated/batch` (23:18). Kept for diffs only.
3. **Install tree** (`build/agent9/make-install.ps1 -Variant batch-nolr`, in baseline layout) at
   `build/agent9/install/batch-nolr/`:
   - `generated/rexglue.cmake`: baseline's;
   - `generated/default/`: the batch-nolr output, with baseline's `codegen.d` (same deps: xex, manifest, config);
   - `legodimensions_config.toml`: the exact config the regen used (= `configs/batch-nolr.toml`);
   - `SHA256SUMS.txt`; the END line in `build/agent9/logs/install-steps.txt` gives the file count and the last TU.
   - Built 23:54: 872 files, 481,074,943 B, 430 TUs, last `legodimensions_recomp.429.cpp`. Config sha256
     `E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090` (= `configs/batch-nolr.toml`); `SHA256SUMS.txt`
     sha256 `24CE1493FB8DAE37E00B556EB8871D633921E44378D960DE4359B104B16CDB8E` (872 lines).
   - **Do not build `build/agent9/install/batch`** (23:28, 836 files, SHA256SUMS `53ECB4DA…`): it has `skip_lr`. It stays
     only for diffs.
4. **Copy into the snapshot** (`<SNAP>` = `build/agent2/snapB`: snap1 at S2, with `generated` as a real directory). The config goes first, so the touched generated
   files, `codegen.build.stamp` included, end up newer than it.
   - **Never** do this in the dev tree: its `generated` is a junction to `baseline\...\generated`, and `/MIR` through it would
     overwrite the baseline. The script stops if `generated` is a link (snap1's is a real directory).
   - robocopy exit codes 0-7 mean success.
   ```powershell
   $S = '<SNAP>\DimensionsRecomp\rexlego'
   if ((Get-Item "$S\generated" -Force).LinkType) { throw "$S\generated is a link: stop" }
   Copy-Item build\agent9\install\batch-nolr\legodimensions_config.toml "$S\legodimensions_config.toml" -Force
   robocopy build\agent9\install\batch-nolr\generated "$S\generated" /MIR /NFL /NDL /NP
   if ($LASTEXITCODE -ge 8) { throw "robocopy failed: $LASTEXITCODE" }
   # robocopy keeps the gen-time mtimes, which are older than existing objects, so ninja would skip TUs: touch everything
   $now = Get-Date; Get-ChildItem "$S\generated" -Recurse -File | ForEach-Object { $_.LastWriteTime = $now }
   ```
5. **Agent 2's tools** (Agent 2 has made these changes):
   - `gen-check.py --base build/agent9/install/batch-nolr/generated --snap … --snap-rex …` instead of baseline's 887 files.
   - A generic `codegen-frozen2.exe` takes its required list from `sources.cmake`: the batch-nolr's last TU is
     `legodimensions_recomp.429.cpp`, not baseline's `.437.cpp`.
   - The snap gate expects 432 TUs (430 + init + register). Agent 2 also checks `SHA256SUMS.txt` and the config sha256
     from step 3.
6. **Build** in a fresh build dir, `build/agent2/snapB-off` (NATIVE_GPU=OFF, x86-64-v3, against `snap1-sdk/install`). It's a
   full build (PCH, 430 TUs, init, register) at -j10, about 13-21 min. Expect about baseline's time: real batch TUs
   compile at 9.5-10.9 s CPU per source MB (baseline 6.0-11.2, S2.8 heavy TUs), and the source is 1.83% smaller.
7. **Stage** it with the `.map`: `run-b.ps1` stages B in `build/agent2/devoffB-bin`, the path Agent 8's matrices use
   (session 3; earlier notes said `codegen1-bin`).
8. **Agent 8:** `bench/agent8/run/matrix-codegen-check.json` (functional gate), then `matrix-codegen.json` (timing,
   user-started, in a quiet window).
9. **Rollback, in this order** (each one: delete the keys from the block in `make-batch-config.ps1`, then rerun steps 2-4
   and rebuild):
   1. The gate fails: drop the four `*_as_local` keys and `cr_compare_so_zero`. Keep rlwinm, flush, vmx and musttail.
      (`skip_lr` is already out: S2.2.)
   2. A TU fails to compile with musttail: drop `musttail_calls`.
   3. Anything else: bisect by key. The keys are independent, except that `cr_compare_so_zero` only matters with
      `xer_as_local`.

   Pre-staged in session 3 (S3.2): 9.1 = `build/agent9/install/rb1-nolocal`, 9.2 = `build/agent9/install/rb2-nomusttail`
   (configs made with `make-batch-config.ps1 -Drop`). Agent 2's `prep-b.py` and `run-b.ps1` pin batch-nolr, so a rollback
   build also needs them re-pinned to the tree's hashes.

# Session 1 (archived): recompiler codegen quality (task #8). PARTIAL: analysis and resume plan

**Status (2026-11-21, ~12:40):** analysis only. The toolchain from Agent 2 is not here yet: there is no
`env/devshell.ps1` and no `build/sdk`, only the clang 23.1.6 tarball in `toolchain/_downloads`. So nothing
was built, measured or changed. Per Agent 1's 12:24 directive, I edited no file in `DimensionsRecomp` or
`rexglue-sdk`; `git status` is clean in both. No subagents were used. **There are no before/after instruction
counts yet**; the method for getting them is in "Resume plan" below.

SDK = `DimensionsRecomp/rexglue-sdk` (branch `perf/opt`, pin `2897c31`). All `file:line` refs below are
relative to the SDK root and are at that pin. Win estimates come from reading the code, not from measurement.

## Ranking

| # | Opportunity | Where | Expected win | Risk | Provable on PPC suite? | Proposed default |
|---|---|---|---|---|---|---|
| 1 | LEGO enables **none** of the register-localization options. **Blocked today**: LEGO's 7 interior `body =` entries make codegen reject every `*_as_local` flag | `rexlego/legodimensions_config.toml`, `src/codegen/codegen_writer.cpp:52-55` | **Large**: removes most `ctx.` store/reload traffic at every call/return, and the `__save*/__rest*` prologue/epilogue memory traffic | Med-high (interior bodies, setjmp/longjmp, SEH, r11/r12 helper args) | No. Needs game validation (plus the suite variant in step 4) | `skip_lr` now (stage 0); stages A, B, C after the interior-body fix (section 1) |
| 2 | Every compare and record form stores 4 CR bytes and reads XER.SO | `include/rex/ppc/context.h:88-94`, `src/codegen/builders/helpers.h:79-84,143-169` | Medium | Low via `cr_as_local`; medium via liveness | Liveness variant: yes | `cr_as_local` (stage A); liveness = new option OFF |
| 3 | Eager XER.CA on `srawi/sraw/sradi/srad/addic/subfic` | `builders/logical.cpp:348-400`, `builders/arithmetic.cpp:47-54,255-261` | Small-med | Low-med | Yes | `xer_as_local` (stage A); liveness = new option OFF |
| 4 | `rlwinm/rlwimi/rlwnm` always lowered as a 64-bit rotate of a doubled word | `builders/logical.cpp:279-307` | Small (clang may fold some of it already; measure) | Low (pure expression identity) | **Yes** (plus an exhaustive unit test) | ON if suite and asm counts confirm |
| 5 | Flush-mode (MXCSR) state forgotten at every label and after calls | `builders/context.cpp:373-382`, `src/codegen/function_graph.cpp:594`, `include/rex/ppc/context.h:190-202` | Medium in mixed FPU/VMX loops | Medium | Partially | New option OFF |
| 6 | Tail calls are emitted as call+return with no guaranteed `jmp` (no `musttail`) | `builders/context.cpp:341-344`, `resources/templates/codegen/_indirect_call.inja:22-38` | Small-med (stack depth, `ret` mispredicts) | Medium (clang-only attribute) | Yes (asm shows `jmp`) | New option OFF |
| 7 | Scalar fallbacks in VMX emitters (`// TODO: vectorize`) | `builders/vector.cpp:173-180` (vlogefp), `:324-333` (vsubsws) | Small unless hot in a profile | Low (vsubsws exact) / results change (vlogefp) | vsubsws: yes | vsubsws ON if green; vlogefp OFF |
| 8 | Guest memory macros: `volatile`, plus a phys-offset compare on every access | `resources/templates/codegen/pch_h.inja:128,135-145` | Unknown, possibly medium | High (volatile) / med (offset) | No | Measured experiment only, OFF |

Items 2 and 3 are mostly subsumed by item 1: once CR and XER are locals, clang's own dead-store elimination
drops dead CR bits and CA. The codegen liveness passes only pay off for functions that must stay in ctx mode
(SEH, setjmp and interior-body functions), or if stage A cannot ship. Since stage A is blocked today, they are
also the fallback until the interior-body fix lands.

---

## 1. Register localization: the biggest lever, and config only

**Evidence**
- The options exist: `include/rex/codegen/config.h:94-101` (`skipLr`, `skipMsr`, `ctrAsLocalVariable`,
  `xerAsLocalVariable`, `reservedRegisterAsLocalVariable`, `crRegistersAsLocalVariables`,
  `nonArgumentRegistersAsLocalVariables`, `nonVolatileRegistersAsLocalVariables`). All default to `false`.
  They are parsed as **root-level keys** of any included TOML at `src/codegen/config.cpp:103-116`
  (`skip_lr`, `skip_msr`, `ctr_as_local`, `xer_as_local`, `reserved_as_local`, `cr_as_local`,
  `non_argument_as_local`, `non_volatile_as_local`).
- LEGO sets none of them. `rexlego/legodimensions_config.toml` contains only comments, `[functions]` (line 24)
  and 7 `[[midasm_hook]]`. `legodimensions_manifest.toml.example` contains only `[project]`/`[entrypoint]`
  plus `includes = ["legodimensions_config.toml"]`.
- **Blocker:** the LEGO config declares 7 callable interior entries, e.g. `0x8307CA78 = { body = 0x8307C528 }`
  (config lines 25-45ff; the `body` key is parsed at `src/codegen/config.cpp:200-204`). Codegen **rejects
  interior body entries** when any of `ctr/xer/reserved/cr/non_argument/non_volatile_as_local` is on
  (`src/codegen/codegen_writer.cpp:52-55`: "interior body entries require all register localization options
  disabled"). The reason: values live across the jump into the body (CR, CTR, r11/r12, frame pointer r31)
  would sit in two different functions' locals. `skip_lr` and `skip_msr` are not in that check.
  **Prerequisite codegen work (in my area, `src/codegen/**`):** keep the affected functions in ctx mode.
  - Extend the existing per-function fallback (`localizeNonVolatiles()` =
    `non_volatile_as_local && !fn.sharesRegisters()`, `context.cpp:47-49`) to every localization flag.
  - Apply it to the body owners, the interior entries, and every function that branches into an interior
    entry.
  - Then relax the global reject.

  With all flags off, nothing changes, so the off-path stays byte-identical.
- With no localization, every guest register, CR field, XER, CTR and v-register access is emitted as `ctx.X`
  (`builders/context.cpp:51-112`). Functions are `void f(PPCContext& __restrict ctx, uint8_t* base)`
  (`include/rex/ppc/func.h:45`). Inside a call-free stretch, clang can keep fields in host registers, but it
  has to store every modified field before each call and each return, and reload everything after each call.
  Guest code calls often (`bl` every few dozen instructions), so this ctx traffic is the main overhead of the
  generated code. Dead values (CR bits, CA, r0/r11/r12 scratch) are written back as well.
- Prologue/epilogue: in ctx mode every `bl __savegprlr_N` / `__restgprlr_N` / `__savevmx_*` saves and
  restores the non-volatiles through guest memory (byteswapped). Under `non_volatile_as_local`, the SDK elides
  these helpers (`builders/context.cpp:201-209`, gated on the global flag on purpose). That covers the task's
  "prologue and epilogue overhead" item.
- Upstream XenonRecomp, which this codegen descends from, has the same options as opt-in optimizations that
  need per-game validation. As far as I remember, Unleashed Recompiled ships with all of them on; I have not
  verified that here.

**Proposed change** (game config only, root keys **above** the `[functions]` header):
```toml
# Stage 0: works today (not blocked by interior bodies). Drops one ctx.lr store per bl
# (control_flow.cpp:64-65,102,187) and the mflr/mtlr moves (system.cpp:244-248,312-316).
skip_lr = true
# Stage A: needs the interior-body fix above
ctr_as_local = true
xer_as_local = true
reserved_as_local = true
cr_as_local = true
# Stage B
non_argument_as_local = true    # r0 r2 r11 r12, f0, v32-v63 (context.cpp:53-80)
# Stage C: needs setjmp/longjmp and SEH review first
non_volatile_as_local = true    # r14-r31, f14-f31, v14-v31, v64-v127; elides __save*/__rest*
# skip_msr: do NOT enable. It removes the global-lock emulation (see risks).
```

**Risks, per flag** (`skip_lr` and `skip_msr` checked in this SDK; the others partly from the XenonRecomp
lineage)
- `skip_lr`: `bl`/`bcl`/`bctrl` stop writing `ctx.lr` (`control_flow.cpp:64-65,102,187`), and `mflr`/`mtlr`
  emit nothing (`system.cpp:244-248,312-316`). `blr` is already a C `return`, so LR is only data.
  - Breaks: code that reads LR as data (`bl $+4; mflr` PC-relative tricks, or `mtlr`+`blr` used as a computed
    jump), and runtime diagnostics that read `ctx.lr`.
  - `mflr r12` before `__savegprlr` saves a stale value, which is harmless because nothing branches on it.
  - Overall: low-medium risk, small but broad win.
- `skip_msr`: **high risk, do not enable.** In this SDK, `mtmsrd r13` is the kernel global lock:
  `REX_ENTER_GLOBAL_LOCK()`, otherwise `REX_LEAVE_GLOBAL_LOCK()`, with seq_cst fences (`system.cpp:318`
  onward). `mfmsr` returns `REX_CHECK_GLOBAL_LOCK()` (`system.cpp:250-258`; macros at `pch_h.inja:313-332`).
  Skipping them removes that mutual exclusion.
- `ctr_as_local`, `reserved_as_local`: low risk. `mtctr; bctrl` consumes CTR immediately, and `lwarx/stwcx.`
  pairs are always in the same function.
- `xer_as_local`: XER is not part of the ABI across calls. SO becomes a zero-initialized local
  (`function_graph.cpp:720-755`), so clang folds the `so` store of every compare to a constant. Real hardware
  keeps SO sticky across functions; no compiled code relies on that.
- `cr_as_local`: cr2-cr4 are callee-saved in the ABI, and per-function locals preserve them trivially. The
  risk is the reverse: a hand-written helper that *returns* a result in CR to its caller. Rare, but check
  the runtime-library helpers.
- `non_argument_as_local`: the `__savevmx_*`/`__restvmx_*`/`__savefpr*` helpers take **r11/r12 as implicit
  pointer arguments**. With only stage B on, they are real calls (the elision at `context.cpp:205-209` keys on
  `non_volatile_as_local`), and inside the helper r12 is a fresh zero local. That means save/restore to the
  wrong address. **Check this first**, or enable B only together with C.
- `non_volatile_as_local`:
  - setjmp/longjmp: the setjmp sequence is `env = ctx; ppc_setjmp(); if (ret) ctx = env;`
    (`context.cpp:184-192`). It restores ctx but not locals, so localized non-volatiles of the setjmp frame
    are wrong after a longjmp. LEGO sets no `setjmp_address`/`longjmp_address`.
  - SEH: funclets get localized values through ctx (`sharesRegisters`, `context.cpp:211-215`), so this case is
    already handled.
  - Guest C++ EH or stack unwinding that reads saved registers from guest stack frames breaks once the saves
    are elided.
- Mid-asm hooks take registers by reference, which works with locals.

**Verify** (once a build exists)
1. Regenerate LEGO for each stage into `build/agent9/gen-{base,0,A,B,C}`, using a copy of the manifest under
   `build/agent9` whose `includes` points at a stage config. Then record:
   - total generated size and `ctx.` occurrence count per TU;
   - x64 instruction counts of 5-10 hot functions (taken from other agents' profiles).
2. Game check for each stage: boot, title screen, one level, the bench harness (frame time, guest CPU%).
3. PPC suite variant: `recompile-tests` always uses a default `RecompilerConfig`
   (`src/rexglue/commands/test_recompiler.cpp:348`) and reads results back from ctx. Add `--config <toml>` and
   run the suite with the stage flags. Only assertions on ABI-visible state stay valid in that mode (r3, f1,
   v2, memory, r1); tests that check r0/r11/r12, CR, XER or CTR in ctx have to be tagged out. This proves
   local-mode codegen is self-consistent. It does **not** prove game-level ABI assumptions.
   `src/rexglue/**` is not in my owned set, so this needs its owner or Agent 1's OK.

## 2. CR compare: 4 byte stores and an XER.SO load per compare

**Evidence:** `CRRegister::compare` (`include/rex/ppc/context.h:88-94`) writes `lt`, `gt`, `eq`, `so`, and
`so` comes from `xer.so`. It is emitted for every `cmp*` (`helpers.h:143-169`) and after every record-form `.`
instruction (`helpers.h:79-84`). With CR in ctx, all four stores must happen before the next call or return,
even though a branch usually reads one bit of a field that is consumed right away.

**Proposed**
- (a) Stage A `cr_as_local` + `xer_as_local`. Clang then deletes the unread bits and fuses cmp+setcc+test+jcc
  into cmp+jcc.
- (b) For functions that stay in ctx: an option `cr_liveness` (OFF). Do a backward per-function scan and emit
  only the bits read before the next overwrite, e.g. `ctx.cr0.eq = a == b;`. Treat any call, return,
  indirect branch, `mfcr` or unknown successor as making all bits live. That keeps it provable on the suite,
  which reads CR from ctx at return.

**Verify:** `instr_cmp*` and the record-form tests in `tests/ppc/asm`, plus the `seq_branch_*` tests; count CR
byte stores (`mov byte ptr [rcx+off]`) in the x64 asm before and after.

## 3. Eager XER.CA computation

**Evidence:** `build_srawi/sraw/sradi/srad` (`builders/logical.cpp:348-400`) always compute and store CA,
roughly `(rS < 0) & ((rS & lowmask) != 0)`. So do `addic` (`arithmetic.cpp:47-54`) and `subfic`
(`arithmetic.cpp:255-261`). CA is read only by `adde/addze/addme/subfe/subfze/subfme` and `mfxer`. The usual
reader is `srawi; addze` (signed divide by 2^n). Most `srawi`s are sign-extending scales whose CA is dead.

**Proposed:** stage A `xer_as_local` lets clang drop dead CA. For ctx-mode functions, add an option
`ca_liveness` (OFF): precompute `ca_live_after[insn]` (live if a CA reader comes before a CA writer on any
path; call, return, indirect jump, `mfxer` or exit count as live), and skip the CA expression when it is dead.

**Verify:** the `instr_<op>.s` tests for every touched mnemonic, `seq_branch_carry.s`, and the `test_equiv_*`
cases that use addic/subfe. The suite reads `ctx.xer.ca` at return, so the conservative exit rule is exactly
what it checks.

## 4. Rotate-and-mask lowering (provable, so it can be default ON)

**Evidence:** `build_rlwinm` (`builders/logical.cpp:290-297`) emits
`rA.u64 = __builtin_rotateleft64(rS.u32 | (rS.u64 << 32), SH) & MASK64` for every form. That includes the very
common `slwi/srwi/clrlwi/clrrwi/extrwi/rotlwi`. `rlwimi` (`:279-288`) and `rlwnm` (`:299-307`) use the same
doubled-word form. Whether clang reduces this to a 32-bit shift or rotate is unknown, so measure first.

**Proposed** (only for the non-wrapping `mb <= me` case, where the mask lies inside the low word, so the
upper 32 bits are 0 in both forms):
```cpp
// mb <= me: mask inside low word, upper 32 bits zero -> 32-bit idiom
const uint32_t m = mask32(mb, me);                    // PPC bits mb..me
if (sh == 0)              println("\t{}.u64 = {}.u32 & 0x{:X};", rA, rS, m);
else if (me <= 31 - sh)   println("\t{}.u64 = ({}.u32 << {}) & 0x{:X};", rA, rS, sh, m);       // no wrapped bits in mask
else if (mb >= 32 - sh)   println("\t{}.u64 = ({}.u32 >> {}) & 0x{:X};", rA, rS, 32 - sh, m);  // only wrapped bits
else                      println("\t{}.u64 = __builtin_rotateleft32({}.u32, {}) & 0x{:X};", rA, rS, sh, m);
// mb > me (wrapping mask sets upper-word bits): keep the existing 64-bit form
```
Use the same split for `rlwnm` when the shift is variable: `rotl32` plus the mask. For `rlwimi`, the insert
mask is likewise low-word-only when `mb <= me`.

**Risk:** low, since this is a pure function of `(x, sh, mb, me)`.

**Verify:**
- New exhaustive unit test in `tests/unit/codegen`: all 32x32x32 `(sh, mb, me)` combinations times random
  `x`, comparing the reference doubled-word expression with the new idiom (milliseconds to run).
- `instr_rlwinm.s`, which already covers wrapping masks (`rlwinm_10/11/12`), plus `instr_rlwimi.s`,
  `instr_rlwnm.s`, `instr_rldicl.s`, `instr_rldicr.s`, then the full suite.
- Evidence: x64 instruction counts of the rlwinm test functions before and after.

## 5. Flush-mode (MXCSR) churn

**Evidence:** every scalar FP emitter calls `ctx.emit_set_flush_mode(false)` (`builders/floating_point.cpp`,
about 25 sites at lines 22-233). VMX float emitters call `emit_set_flush_mode(true)` (e.g.
`builders/vector.cpp:175`). `emit_set_flush_mode` (`context.cpp:373-382`) emits
`ctx.fpscr.enableFlushMode()/disableFlushMode()` whenever the tracked state changes. But the state resets to
Unknown at **every label** (`function_graph.cpp:594`) and after calls. As a result:
- the first FP instruction of every branch-target block and every post-call block emits the check again;
- each check is a `stmxcsr` read plus a conditional `ldmxcsr` (`include/rex/ppc/context.h:190-202`), and
  `ldmxcsr` is expensive (it is partially serializing);
- loops that mix scalar `fmuls` with VMX128 math flip FTZ/DAZ twice per iteration.

**Proposed**
- (a) Option `flush_mode_dataflow` (OFF): forward dataflow over the blocks. A block's entry state is known
  when all of its predecessors are known and agree; calls leave the state Unknown.
- (b) Before that, measure: count the toggle sites per function in the generated LEGO TUs, then check whether
  hot loops contain both modes.

**Do not** let scalar FP run under FTZ/DAZ: denormal results would change.

**Verify:** fp (`instr_f*`) and vector (`instr_v*`) tests, plus a new `tests/ppc` sequence test that mixes
`fadd` and `vaddfp` across a loop back-edge with denormal inputs.

## 6. Guaranteed tail calls (`musttail`)

**Evidence:** a conditional tail call emits `f(ctx, base); return;` (`context.cpp:341-344`). Unconditional
`b`/`bctr` tail paths and indirect dispatch (`_indirect_call.inja:22-38`, which does a range check, a table
load and a null check, already marked `[[likely]]`/`[[unlikely]]`) are also call+return. Clang usually
sibcalls these at -O2 anyway. It does **not** when a local's address escapes: the `PPCContext env` for
setjmp, locals passed by reference to mid-asm hooks, or SEH frames. Without the sibcall, long guest tail-call
chains grow the host stack.

**Proposed:** an option `use_musttail` (OFF). Define `REX_MUSTTAIL` in `pch_h.inja` as `[[clang::musttail]]`
under `__clang__` and empty otherwise. Emit `REX_MUSTTAIL return f(ctx, base);`, which is valid for `void`
because all guest functions share one signature.

**Risk:** clang rejects musttail when the prototypes differ or when objects with non-trivial destructors are
in scope. Escaped-local frames must skip it.

**Verify:** check the x64 asm for `jmp` instead of `call`+`ret`. Add a `seq_tailcall_*.s` test to `tests/ppc`
if none exists.

## 7. VMX scalar fallbacks

- `build_vlogefp` (`vector.cpp:173-180`, `// TODO: vectorize`) makes 4 scalar `log2f` calls. A vector
  polynomial like the existing `vexptefp` one (`:156-167`) would change results, so it is not provable:
  option OFF.
- `build_vsubsws` (`:324-333`) does 4 scalar saturating subtracts through 64-bit temps. An exact SSE4.1 form
  fits within x86-64-v2:
  `r = a - b; ovf = srai((a ^ b) & (a ^ r), 31); sat = srai(a, 31) ^ 0x7FFFFFFF; r = blendv(r, sat, ovf)`.
  Keep the existing VSCR.SAT behaviour.
- Next session, grep `TODO: vectorize` to list the rest; I only skimmed `vector.cpp`, which is 1562 lines.
  This is only worth doing if these instructions show up hot in a LEGO profile.

## 8. Guest memory macros (measured experiments only)

**Evidence:** `REX_LOAD_*`/`REX_STORE_*` (`pch_h.inja:135-145`) go through `volatile` pointers, and on Win32
they add `REX_PHYS_HOST_OFFSET(addr)` = `(addr >= 0xE0000000) ? 0x1000 : 0` (`:128`). So every guest access
costs add, cmp, cmov/setcc, a volatile load and a bswap. `volatile` blocks load merging, redundant-reload
elimination and load folding into ALU ops. It is probably deliberate (cross-thread spin waits), so **do not
remove it globally**.

**Experiments** (options OFF, game-validated):
- (a) For r1-relative (stack) accesses, skip the phys offset. This needs confirmation that guest stacks are
  never allocated at or above 0xE0000000.
- (b) Drop `volatile` only on r1-relative accesses, since stack memory is thread-private. The risk is a stack
  object handed to another thread and spin-waited on in the same function.

`movbe` would fuse load and bswap, but it is x86-64-v3, so it would need CPUID dispatch. Out of scope.

## Not perf, but should be fixed

`BuilderContext::emit_load_d_form/emit_load_x_form` and the two store emitters use `static char mm_macro[64]`
(`builders/context.cpp:536, 556, 576, 596`). If codegen ever emits functions on parallel threads, they race
and can emit the wrong macro. The fix is a stack buffer. Output stays byte-identical, so it is trivially
provable. A grep of `src/codegen` and `src/rexglue/commands` for `std::thread`, `std::async`, `parallel_for`,
`std::execution`, thread pools and `jthread` found nothing, so codegen looks single-threaded today and the race
is latent. Low priority.

## Smaller notes

- Divide guards (`arithmetic.cpp:100-147`) are required. `arithmetic.cpp` has no `[[likely]]`/`[[unlikely]]`
  anywhere. If the guards are emitted as `if` statements, mark the divide-by-zero and overflow paths
  `[[unlikely]]`. That only changes block layout, so it is provable on the suite.
- `mfmsr`/`mtmsrd` emit `std::atomic_thread_fence(seq_cst)` (an `mfence` on x64) next to an atomic RMW on the
  lock count (`lock xadd`), which is already a full barrier on x86. Dropping the redundant fence is only worth
  it if lock sequences show up hot. Not provable on the suite, so OFF.
- `strchr(name, '.')` record-form detection (`helpers.h:63-65`) runs at codegen time only, so no runtime cost.
- Locals are zero-initialized with `{}` (`function_graph.cpp:720-755`). Clang drops most dead inits.
  Negligible.
- Indirect dispatch is already lean. The next step would be profile-guided devirtualization of hot
  vtable/`bctrl` sites (a guarded direct call), which needs profile data. Future work.

## Resume plan (once Agent 2's env exists)

1. Run `. env/devshell.ps1`. Configure the SDK into `build/agent9/sdk` (Ninja, Release, with the option that
   enables `tests/`; check `tests/CMakeLists.txt` for its name). Build `rexglue`, `ppc_tests` and the codegen
   unit tests with `ninja -j4`. Run `ctest -L ppc` and the codegen unit tests: **the baseline must be green**.
2. Baseline evidence:
   - copy the generated `ppc_test_functions.cpp` into `bench/agent9/baseline/`;
   - compile it with `clang++ -O2 -march=x86-64-v2 -S`;
   - write `bench/agent9/count_insns.ps1` to split the asm by function and count instructions;
   - do the same for 3-5 hot LEGO TUs.
3. Implement and measure in this order, one at a time:
   - the per-function ctx-mode fallback for interior bodies (section 1). It unblocks every `*_as_local` flag
     for LEGO. Check that output with all flags off is byte-identical, and that LEGO codegen accepts stage A;
   - #4 rlwinm: provable, default ON if green;
   - the `mm_macro` fix and the divide-guard `[[unlikely]]`;
   - #6 `use_musttail`;
   - #3/#2 liveness options;
   - #5 flush dataflow.

   Every new option is OFF by default, and the OFF path must produce byte-identical output (check with a diff
   of the generated TUs). After each change, run the full PPC suite and the codegen unit tests, and save the
   before/after counts to `bench/agent9/`.
4. Ask the owner of `src/rexglue/**` for the `recompile-tests --config` hook. Then run the suite with the
   stage flags.
5. Game: roll out stage 0 (`skip_lr`, possible right away), then stages A, B and C in
   `legodimensions_config.toml`, one at a time. Regenerate (about 470 MB), build, then boot and bench with the
   bench owner, and record the results here.
6. Coordinate with Agent 10 before touching anything in `include/rex/ppc/*` (needed for #2(b), possibly #5).

## What I did not get to read

- `src/codegen/builders/`: `comparison.cpp`, `control_flow.cpp` (only the `skipLr` sites), `memory.cpp`,
  `system.cpp` (only lines 240-330), `instruction_dispatch.cpp`. `floating_point.cpp` and `vector.cpp` were
  only grepped and skimmed.
- `src/codegen/codegen_writer.cpp` apart from lines 46-60 (the interior-body check), and `function_graph.cpp`
  outside lines 300-760.
- `include/rex/ppc/intrinsics.h`, `stack.h`, and the rest of `function.h` (all Agent 10's).
- `tests/unit/codegen/*`, and the templates other than `pch_h.inja`, `_indirect_call.inja`, `init_cpp.inja`.
- The `ctr/xer/cr/reserved_as_local` emit paths beyond `context.cpp:51-112`.
- The callers of the setjmp/longjmp and SEH paths (I read `context.cpp:174-215` itself).
- The `body =` entries past config line 45, and which functions branch into the 7 interior entries. That
  list sizes the ctx-mode fallback.
