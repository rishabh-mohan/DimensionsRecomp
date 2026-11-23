> **RESUME (run 2, 15:59: task #22 DONE = #24's S4c package (+ #30's CMake option), in R2.22 at the very END; before it
> #17 (#26, R2.17) and #11 (R2.11); Agent 10: OFF SAFE, R2.22.6; keep L1-402 line-stable. Session 3 = #32, #23, #8).** Task
> #32's notes (S5.x) follow the run spec, then #23's (S4.x), S3.x, session 2 and the recipe; session 1, R2.11/17/22.
> - **Task #32, session 3 part 4 (Agent 1, about 07:09; scope addition 07:20): done.**
>   - S5.1: the 1b exit split. The (b) clock list (`build/agent9/b-clock/clock-list.md`) and the HRT check went to
>     Agent 10 at about 07:17. My recommendation was (a). **Agent 1 closed 1b at 07:40 with (a):** recorded as a
>     difference, root cause to S4; the remaining 1b items (whole-tree clock list, HRT check, optional scans) dropped.
>   - S5.2: the merged GPU-wait spin back-off S4 item (S4-DRAFT #24/#25): stage 1 hooks H0/H1 (L1, the fence wait)
>     and H2 (L2, Agent 6's GetData poll; Xenos only), stage 2, the test order and the needs. Draft hook, not
>     compiled: `build/agent9/s4/fence-wait/gpu_wait_backoff.cpp.draft`.
>   - Extra (07:36-07:39): the writers of the two FE timer gate flags from Agent 10's (b) result (S5.1,
>     `build/agent9/b-clock/fe-gate-flags.txt`). 1b closed before they went out, so they went to Agent 11 as an
>     S4 pointer only (not to Agents 10 and 3).
>   - Draft style pass done at 07:45 (S5.2.2). Agent 11 was told, and `@@done 32` was sent, at about 07:47.
>   - Rules: light work, <= 2 threads, no builds, game runs, live-tree edits or subagents. Mine: this file and
>     `build/agent9/**`. Stop by 08:25; notes only from 08:30.
> - **Task #23, session 3 part 3 (Agent 1, about 04:55): S4 analysis. Done: S4.0-S4.3 are written; the summary to
>   Agent 1 and `@@done 23` were sent at about 06:00.** Read-only on the trees, <= 2 threads, no builds, no game runs;
>   notes only from 08:30. Mine: `build/agent9/**`, `bench/agent9/**`, this file; up to 1 subagent (1 used: D
>   `4b8ebd88-9a37-497b-b3e5-c7f72eaea7f7`, step 2, finished; report `build/agent9/s4/scene-walk/REPORT.md`).
>   Steps: 0 review Agent 2's S3e clones (OK sent about 05:05, then moot: S3e is off; S4.0); 1 render-thread GPU-wait
>   spin (S4.1); 2 main scene walk (S4.2); 3 the S4 codegen ranking, marking the items that only save CPU while the
>   render thread is GPU-bound (S4.3).
> - **Scan ban (Agent 1, 05:31):** while Agent 8's game queue runs (until about 07:15), no recursive searches or
>   multi-file scans over the SDK, DimensionsRecomp (including `baseline/DimensionsRecomp`) or build trees; only single
>   files, line ranges, or a grep of one named file. After 07:15, only if Agent 1 asks: the S4.2.5 scans,
>   `HighResolutionTimer` users in `include/`, the `db16cyc` site count, and where `host_timer_resolution_ms` is
>   defined.
> - **Attract window 06:33-07:15 (Agent 1, 05:55):** Agent 8's attract scenes need an idle machine: no builds or
>   compiles, no recursive searches, no reads over ~100 MB, 1 thread, batched tool calls. Writing is fine.
> - **Both windows above are over** (Agent 8's last run ended 07:00:02). Agent 1 allowed targeted read-only scans
>   (<= 2 threads, none of build/ or thirdparty) until 08:15. Done: the `HighResolutionTimer` users and the
>   `host_timer_resolution_ms` definition (S5.1), the `db16cyc` count (S4.1.3 (b)) and the S4.2.5 caller and
>   arming scans. Dropped by Agent 1 at 07:40 (no more optional scans): the vtable dump and the indirect call
>   sites (the probe covers both).
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
> - **State (05:55): task #23 done (S4.0-S4.3); task #8 complete (`@@done 8` 04:46).** nativeB staged 04:34:06
>   (`build/agent2/nativeB-bin`, exe `01C4D5A3E36FAC50`), item 1a all PASS (S3.9). Profile answer and S4 list sent about
>   04:19 (S3.8); Agent 7's tables match; write-tracking reply sent 04:46. nativeB scripts OK 03:50, rb-chain.ps1 -GuardOnly
>   (`65A2CFE4`) OK 04:06 (S3.7). native3d-bin staged 03:46 (S3d, fingerprint `335ff2d47268f3a1`). RESUME check
>   PASS (S3.1). Rollback trees `install/rb1-nolocal` and `install/rb2-nomusttail` are
>   pre-staged (S3.2), with re-pinned copies of Agent 2's tools in `build/agent9/repin/` (S3.5). B's tools reviewed: **ok**
>   (S3.4). **B built clean and was staged at 02:40** (`build/agent2/devoffB-bin`, exe `C3F8686EBDD83340`); the static A/B
>   map check passes (S3.5). **B boot PASS** (Agent 8, 02:49). **B front-end gate PASS** (Agent 10, 03:31; partial
>   coverage: no level, pause, cutscene, save/Quit or toy pad). No rollback; B stays in window 4 (S3.6).
> - **Watching:** nothing (subagent D has finished; no background tasks). `build/agent9/watch-nb.ps1` exited 0 at
>   04:34:06 (nb chain DONE, 0 `FAILED:`; log `build/agent9/logs/watch-nb.txt`); `watch-b.ps1` exited 0 at 02:40.
> - **Rollback trees:** not needed (gate PASS); rb1-nolocal (9.1) and rb2-nomusttail (9.2) stay staged for window 4.
> - **On a later gate failure:** send rb1-nolocal at once (recipe step 9.1) to Agents 1 and 2: tree path,
>   `SHA256SUMS.txt` sha256, config sha256, TUs, and `build/agent9/repin/README.md`. Anything else: investigate, then
>   bisect (S3.2). A crash's `[FATAL] That is legodimensions.exe+0x<RVA>` line:
>   `python build/agent9/addr2sub.py --log <game.log>` (B; `--build A` for devoff2) gives the `sub_` and its
>   `DEFINE_REX_FUNC` line in the generated source.
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

# Session 3 part 4: task #32 (from 07:09)

Task #32 came from Agent 1 at about 07:09.
- **Scope:**
  - finish 1b (b) and record (a) (S5.1);
  - write the merged fence-wait S4 item (S5.2);
  - optionally, draft the stage-1 hook (not compiled).
- **Scope addition (Agent 1, 07:20):** cover Agent 6's second poll, GetData from sub_82BDCFB8. It goes in the same
  item, the same switch family and the loaded-machine test.
- **Agent 1, 07:40:** 1b is closed with (a). Drop the remaining 1b items and put the time into #32 (due 08:20).
- **Rules:** light work only, <= 2 threads, no builds, no game runs, no live-tree edits, no subagents. I own this file
  and `build/agent9/**`. Stop by 08:25.

## S5.1 1b exit split: (b) result and (a) recommendation (07:00-07:40; closed with (a))

Agent 10's 1b tie-break (pair 2) reopened one item, the front-end exit. nativeB leaves the front-end about 12 s
earlier than native3d, and then plays the same scenes.
- Agent 10's options were:
  - (a) accept it and record it;
  - (b) find the guest code that starts the fade and diff its codegen, snap1 vs B3;
  - (c) more runs.
- Agent 1 chose (a) + (b) until Agent 10's diff and Agent 3's RE come in at 08:15.
- **Closed (Agent 1, 07:40): decision (a).** Agent 10 found no codegen change in the whole tree and Agent 3 no
  host-clock difference. It is recorded as a difference; the root cause goes to S4. The remaining 1b items (the
  whole-tree clock list, the HRT check, the optional scans) were dropped.

- **The exit clock follows guest CPU speed, not B's codegen.**

  | Build | Exit INSTALL batch minus FE load (s) |
  |---|---|
  | nativeB | 46.50, 49.70 |
  | native3d | 59.59, 61.34 |
  | devoffB | 68.52, 73.81 |
  | devoff2 | 71.29; 2 runs had no exit by about 79-81 s |

  - native3d and devoff2 have the same A codegen but differ by >= 10 s. The OFF builds overlap: devoff2's one exit
    (71.29 s) lies inside devoffB's 68.52-73.81 s. So the exit time follows the GPU path, which sets how much CPU
    the guest gets, not the codegen.
  - Agent 3 (`build/agent3/logs/fe-native-cb.txt`):
    - the first frame (13.0 s) and the A1 response (72.24/72.23 s) match;
    - then nativeB exits 11.6 s earlier: 49.70 vs 61.34 s after A1, 5446 vs 6298 frames at the same fps.
    - So the clock is not wall time, frames, callbacks or a capped dt sum, and presses don't reset it. It runs about
      23-28 % faster in nativeB.
  - My numbers agree:
    - guest CPU totals are native3d 132/144 s vs nativeB 100/113 s, a ratio of about 1.29;
    - native fps is equal (nativeB 97/110, native3d 105/103);
    - interrupt_dispatches is 0 in native runs, and functions_dispatched is about 185/s in all builds.
- **(b), static, A tree:** `build/agent9/b-clock/clock-list.md` has the full list with TU:line. It went to Agent 10 at
  about 07:20, with the tools (`s6_clock_scan.py`, `fq.py`) and the reports.
  - Time sources: QPC sub_83F9EA20, KeQuerySystemTime, Sleep/KeDelayExecutionThread, and the D3D/XAudio mftb readers.
  - Game clock (NuTime-like, globals 0x848D65EC-0x848D6600):
    - get sub_82A333B8 (111 callers);
    - the timer's "expired?" check, sub_82A786D0 (25 callers, 18 in the FE).
  - Frame dt: app [0x849F5E8C]+2212. The app update sub_82FEB7B8 copies it from +1352 (TU59:14612). Who writes
    +1352 is not identified.
  - FE page timeout, globals 0x849F5F84/88/8C:
    - sub_82FD4868 arms it;
    - event 5 of sub_82FE70C0 adds dt to it, except while paused;
    - on expiry it calls sub_82FE6F98 (page 47 -> request page 56);
    - sub_82FB90B8 cancels it.
  - **Every FE clock found is either a dt sum that stops while paused, or a QPC difference.** At equal fps,
    neither runs faster on a faster guest CPU by itself.
    - What fits Agent 3's constraint: background guest work (streaming, the INSTALL batch, attract preload) that has
      to finish before a timer is armed or a page change is accepted.
    - Static reads can't follow vtables or event delivery, so this is not confirmed.
    - Agent 3 (07:34, host side): every time source the game can read is real time and the same in OFF and native
      builds (mftb, KeQuerySystemTime, KeTimeStampBundle+16, audio completion), and no game thread starts or ends
      between 40 and 150 s. Agent 3 was to mark each source in clock-list.md as real-time or progress-paced for the
      08:15 verdict (moot: 1b closed at 07:40).
- **Agent 10's (b) result (07:36): not a codegen change.** The clock-list functions have identical instruction
  sequences, and the whole tree has 0 sequence mismatches. The item stays open for S4. Its two FE timer gates:
  - arming: sub_82FD4868 arms only if sub_82FB9020 == 1 (byte 0x848E2EA2 == 0 + mode-3 queries of sub_82A832F8);
  - counting: event 5 of sub_82FE70C0 adds dt only while the byte [app]+2288 == 0 (`lbz r10,2288(r11)` after
    `lwz r11,24204(0x849F0000)`, 0x82FE70D4-D8). This is the "paused" test in clock-list.md section 4.
- **Writers of those flags (07:36-07:39; `build/agent9/b-clock/fe-gate-flags.txt`; fq.py and `arm_scan.py`):**
  - 0x848E2EA2: no constant-address store; readers sub_82A75FD8 and sub_82A7EAA0. It is written through a computed
    or indexed address.
  - [app]+2288 = 1: sub_82FE08C8. Its only caller, sub_82FE7E40, runs it when the request byte +2289 is set. It then
    tail-calls sub_82FD7FC0([0x849F5F14], app+2228).
  - [app]+2288 = 0: sub_82FE7E40 when the request byte +2290 is set (after sub_82FC1C78([0x849F5F14], app+2228,
    0)), and sub_82FF68E8 (the only caller of sub_82FD7DA8).
  - sub_82FE7E40 runs once per main-loop pass from sub_82FEB7B8 (also from sub_82FEB798 and sub_83A53560).
  - The requests come from one message handler, sub_82FF63A8 (only caller sub_83AA1170, TU279:28966). When a
    virtual name compare against 0x847AD990 matches, arg 0 sets +2289 (freeze) and arg 1 sets +2290 (resume). Its
    base r27 also holds +2136/+2144, so it is presumably the app. sub_8407C158 writes all three bytes too
    (probably init).
  - So the FE page timeout is frozen between a "freeze" and a "resume" message. If the resume is posted when
    background work finishes, a faster guest CPU resumes the timer sooner, which fits Agent 3's 23-28 %.
  - Next (S4 root cause, not tonight): read the message name at 0x847AD990 and find who posts it. An
    instrumented pair would log the +2288 transitions with QPC times.
- **B can't change the semantics, by construction:**
  - mftb becomes an out-of-line `Clock::QueryGuestTickCount` (the same define in A pch:293 and B pch:297);
  - REX_LOAD/STORE are volatile in both pch files (127-137);
  - B adds only CTR/XER/RESERVED/CR locals;
  - musttail only turns call + return into a jump;
  - ctx.lr is kept.
- **Recommendation: (a).** Record "B leaves the front-end about 12 s earlier on native; the exit follows guest CPU
  speed".
  - It is not a fail item: the same scenes play after the exit. No rollback is needed.
  - Agent 10's snap1 vs B3 diff covers the functions in clock-list.md section 5. If it finds an mftb read, or a flag
    or poll value kept in a local, that would make this a B behaviour change and would override (a). It found none
    (07:36).
- **HRT item (Agent 10's group T): done; Agent 10 can drop it** (clock-list.md section 6, sent about 07:20).
  - include/ has only the inline class (`include/rex/thread.h:150-177`) and the member `timestamp_timer_`
    (`include/rex/kernel/xboxkrnl/module.h:42`).
  - The only Windows user is the KeTimeStampBundle 1 ms tick (`src/kernel/xboxkrnl/xboxkrnl_module.cpp:195`).
  - tests/ and rexlego have no hits.
  - `host_timer_resolution_ms` is defined at `src/system/runtime.cpp:39` (default 0) and used at
    `src/core/threading_win.cpp:235`.
  - S4.1.2 and S4.1.3 (d) are updated to match.

## S5.2 S4 item: GPU-wait spin back-off (merged, including Agent 6's GetData poll)

This item merges five pieces:
- S4.1.3 (a2), which becomes stage 1;
- S4.1.3 (a1), which becomes stage 2;
- Agent 6's (e), which is stage 1 with a zero quantum (`agent6-hang-triage.md` S9 item 4);
- Agent 6's GetData poll (a6h S3.4 and S9 item 4; Agent 1's scope addition, 07:20);
- the probe P1 (S4.1.4).

In S4-DRAFT it is rows #24 (stage 1) and #25 (stage 2). Everything is OFF by default. The gain is CPU and power; fps
improves only through headroom (S4.1.3).

### S5.2.1 Two render-thread loops (static, A tree)

- **L1, the fence wait.** sub_83FBF7D0 (`.248.cpp:35181`) calls the poll step sub_83FAF180 (`.107.cpp:36777`) until
  the GPU has passed fence r4 (block+0, S4.1.1).
  - Owner sites in hang reports: 83FAF188, 83FAF200, 83FBF868.
  - a-prof cost: 0.88 core (S4.1.1).
- **L2, the query poll.** sub_82BDCFB8 (`.429.cpp:7890`; r3 = wrapper {+0 query, +4}, r4 = wait flag, r5 = out):
  1. If +0 == 0: *out = 0, return 1.
  2. One try: GetData sub_83FB09E8(q, out, 4, 0) at 0x82BDCFFC (lr 0x82BDD000).
  3. If it returns 1 (S_FALSE) and the wait flag is set, it calls GetData back to back at 0x82BDD024
     (**lr 0x82BDD028**) until the result isn't 1. There is no yield, sleep or SMT hint.
  4. Then it releases the query (sub_83FB05B0), sets +0 = 0 and +4 = -1, and returns 1. With the wait flag clear,
     it returns 0 instead.
  - GetData (`.422.cpp:37230`) has one static caller, sub_82BDCFB8.
    - For type 9 (occlusion), it returns 1 until the CP has passed the query's fence q+24 and the occlusion slots
      have lost the -275 marker (a6h S3.4).
    - If the fence hasn't been submitted yet (q+24 == dev+11036), it kicks first (sub_83FC0C10 at 0x83FB0A5C). So
      the loop never waits on an unsubmitted fence.
  - Owner site: 83FB09F0. In base1 (`hang-60748.dmp`) the lock owner (render thread, CS 0x84959edc) had 145.6 s of
    user CPU in this loop.
  - L2 never calls sub_83FAF180, so a hook on L1 alone misses it.
- **Native builds replace the query path.** `rexlego/src/gpu_native/queries.cpp:318-321` REX_HOOKs CreateQuery
  sub_83FB2360, IssueQuery sub_83FB0738, GetData sub_83FB09E8 and ReleaseQuery sub_83FB05B0. They are built only with
  `LEGODIMENSIONS_NATIVE_GPU` (`CMakeLists.txt:61-141`).
  - So a GetData hook must be Xenos-only, or the native link fails on a duplicate symbol.
  - `gpu_native/hooks_device.cpp:340` hooks the kick sub_83FC0C10 the same way, which affects P1's kick counter.
  - No rexlego file defines sub_83FBF7D0, sub_83FAF180 or sub_82BDCFB8 today (grep of `rexlego/src`, 07:20). A
    07:30 re-grep finds sub_83FB09E8 and sub_83FC0C10 only in gpu_native (queries.cpp:320, hooks_device.cpp:340).
  - **Agent 3 (07:34, `build/agent3/logs/fe-11024.txt`): native never uses L1's fence.** The native device is zeroed
    and never ring-initialised, so dev+11024 stays 0. sub_83FBF7D0's callers 83FB33E0, 83FBF8A0, 83FBF900, 83FC0C10
    and 83FC0EC0 are all hooked in native; only 83FBFB30, 83FC5730 and 83FC5D68 still reach it. So the item has
    nothing to save on native builds, and stage 1 is built for Xenos only (S5.2.2 Files).

### S5.2.2 Stage 1: back-off hooks, rexlego only (S4-DRAFT #24)

- **Switches** (env, read once with `std::getenv`, like `gpu_native/buffers.cpp:137`):
  - `LEGO_GPU_WAIT_BACKOFF_US=<Q>`:
    - unset = OFF: every hook calls the original at once (one load and a branch per call);
    - Q = 0: pause, then `SwitchToThread` on every later poll (Agent 6's (e));
    - Q > 0: pause, then one `SwitchToThread`, then a Q us sleep per poll.
  - `LEGO_GPU_WAIT_SPIN_US=<S>`: the `_mm_pause` phase of a stalled wait before it yields (default 30, at most 200).
  - `LEGO_GPU_WAIT_STATS=1`: P1's counters (S4.1.4), one log line every 5 s. It also works with the back-off OFF.
- **H0, `REX_HOOK_RAW(sub_83FBF7D0)`, the start of each L1 wait.**
  - It resets the thread's L1 stall clock, then calls `__imp__sub_83FBF7D0`; with STATS it times the call.
  - The waitctx sits on the guest stack, so back-to-back waits can reuse its address. A new wait is therefore
    detected here, not by its address.
- **H1, `REX_HOOK_RAW(sub_83FAF180)`, the L1 poll step.**
  1. Read dev = waitctx+0, block = *(dev+11024), and block+0.
  2. If dev+11069 & 2 (GPU off), or block+0 != waitctx+8 (the fence word moved since the last poll): reset the
     stall clock, with no delay.
  3. Otherwise, back off by the stall time t:
     - t < S: 32 `_mm_pause`, about 1-2.5 us at 1.9 GHz;
     - then `SwitchToThread`;
     - then, for Q > 0, a Q us sleep on a per-thread high-resolution waitable timer
       (`CREATE_WAITABLE_TIMER_HIGH_RESOLUTION`, as in `sample_profiler.cpp:70`).
  4. Call `__imp__sub_83FAF180` unchanged.
  - The caller tests completion before every poll. So a wait whose fence has passed never reaches H1, and one whose
    fence word moved is never delayed (Agent 6's check).
- **H2, `REX_HOOK_RAW(sub_83FB09E8)`, the L2 poll. Xenos builds only** (guarded by a compile define, see Files).
  1. Save lr = ctx.lr at entry, then call `__imp__sub_83FB09E8`.
  2. lr 0x82BDD000 (the one try) resets the L2 stall clock.
  3. lr 0x82BDD028 with r3 == 1 after the call backs off as in H1 step 3. Any other caller or result returns at once.
  - It reads ctx.lr, like the existing host hooks, so it needs skip_lr off. skip_lr is off in every build (S2.2).
  - **Fallback (a6h):** hook sub_82BDCFB8 itself and re-implement its 20-instruction loop. That also works on native
    builds, where its GetData call reaches gpu_native's hook. But it replaces guest code instead of passing through,
    so it needs a closer review.
- **Output-identical** (the S4.1.3 (a1) argument, now for both loops):
  - the guest loops run the same code, with the same completion tests on the same words;
  - neither loop counts polls or has a live timeout. L1's timeout reads KTHREAD+0x58, which the SDK never writes; L2
    has none;
  - the hooks write no guest memory and no guest registers. Only the time of the next poll changes.
  - The guest-visible wall-clock values (dev+22008/22016 and the dev+13836 callback's elapsed value; L1 only) already
    vary from run to run.
- **Cost and risk:**
  - CPU: about -0.7 to -0.8 core while the render thread waits (S4.1.3). L2's share in normal runs is unknown; P1
    measures it.
  - Latency: up to one quantum after the GPU passes the fence, half that on average. The spin phase S keeps short
    waits at today's speed. The sweep measures this.
  - The owner holds the game lock while it waits (CS 0x84959edc in base1). The hook lengthens the hold by at most
    that latency, and it gives the core to the CP thread, which is the lever on a loaded machine (a6h S9 item 4).
  - Risk: medium (wake latency). It doesn't depend on B's Stage A: H1 and H2 pass ctx through and read only r3 and lr.
- **P1 shares the file.** P1's pass-through hooks on sub_83FBF7D0 and sub_83FAF180 have to be H0 and H1, since each
  name can have only one strong definition.
  - It counts waits, polls, polls that saw movement, pauses, yields and sleeps.
  - It counts sleeps whose next poll saw movement, which estimates the latency cost.
  - It counts L2 tries, blocking polls and delayed polls, plus wait-time sums and the S4.1.4 histogram.
  - P1's kick counter (sub_83FC0C10) is Xenos-only, for the same reason as H2.
- **Files (stage 1):**
  - new `DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp`. The draft is
    `build/agent9/s4/fence-wait/gpu_wait_backoff.cpp.draft`, syntax-checked only (R2.11).
  - `DimensionsRecomp/rexlego/CMakeLists.txt`, before :168: inside `if(NOT LEGODIMENSIONS_NATIVE_GPU)`, append
    `src/gpu_wait_backoff.cpp` to `LEGODIMENSIONS_SOURCES` and set `LEGO_GPU_WAIT_HOOK_GETDATA=1` on it
    (`set_property(SOURCE ... APPEND PROPERTY COMPILE_DEFINITIONS ...)`, the pattern of :150-152).
    - Xenos only, since native has nothing to save (S5.2.1, Agent 3).
    - The define stays as a guard: without it H2 and H3 are left out, so a native build that includes the file by
      mistake still links.
  - SDK: nothing. It includes `legodimensions_pch.h` (PPCContext, the REX_LOAD macros, `rex/logging.h`) and
    `rex/hook.h` (`REX_HOOK_RAW`, :49) like `native_lock_elide.cpp:3-4`, plus `windows.h` and `immintrin.h`.
  - Guest loads use the pch's `REX_LOAD_U32` / `REX_LOAD_U8` (`legodimensions_pch.h:120-129`; :124-133 in B's pch,
    same text), the same macros as the generated bodies, including `REX_PHYS_HOST_OFFSET`.
  - Config: env vars only; no toml or cvar change.
- **Draft (07:29; style 07:45; N1-N4 13:18, R2.11):** `build/agent9/s4/fence-wait/gpu_wait_backoff.cpp.draft`.
  It follows this section, plus:
  - H3: a STATS-only kick counter on sub_83FC0C10 (P1), under the same guard as H2;
  - a non-numeric `LEGO_GPU_WAIT_BACKOFF_US` leaves the back-off OFF, with a warning (N1: digits only, both vars);
  - each timer wait is capped at 20 ms, and a failed timer yields instead of sleeping (never `Sleep(1)`);
  - the per-thread timer handle is closed at thread exit (a thread_local RAII object);
  - "sleep, then moved / done / ready" counters estimate the latency cost for each loop.
  - Agent 10's review TODOs are in its header. A style pass (07:45) matched the draft to rexlego: the pch include
    and `__imp__` declarations as in `native_lock_elide.cpp:3-37`, the pch load macros instead of private helpers,
    and the timer as in `sample_profiler.cpp:70-71`. That closed the load-helper TODO.

### S5.2.3 Stage 2: wake on GPU write (S4.1.3 (a1); S4-DRAFT #25), only if stage 1 costs slow frames

- Same hook file. In the stalled phase, H1 and H2 sleep with `WaitOnAddress` on a CP sequence counter (1 ms timeout)
  instead of the Q sleep.
- SDK `src/graphics/command_processor.cpp/.h`: `seq.fetch_add(1)` after every guest-visible CP store, and
  `WakeByAddressAll` when waiters > 0. The stores:
  - EVENT_WRITE_SHD :1415 (L1's fence and L2's q+24);
  - EVENT_WRITE_ZPD :1449 (L2's occlusion slots);
  - REG_TO_MEM :1274, MEM_WRITE :1294, COND_WRITE :1312, EVENT_WRITE_EXT :1419, INTERRUPT :988, and the RPTR
    write-back :314-316.
  - An accessor exports seq and waiters.
  - So one counter serves both loops (Agent 6).
- Link `Synchronization.lib` (`WaitOnAddress`/`WakeByAddressAll`) wherever they are called.
- The no-lost-wake argument and Agent 10's checklist are in S4.1.3 (a1).

### S5.2.4 Test order (Agent 7's metric rule; menus + attract only)

- **Metric rule** (S4-DRAFT L213; `agent7-present.md:307`): score p99, the 1% low and frames > 33 ms per minute next
  to mean fps. p99.9 is secondary. Report per phase in 10 s bins. Run >= 3 runs per arm (5 preferred), alternate the
  arms, and keep the runner, scene and window state the same.
- **Toy Pad:** a level test needs Toy Pad figures. That is user question 1 (S4-DRAFT:268), and it is unanswered.
  Until the user answers, every step uses menus + attract routes only, and the item makes no claim about levels.

0. **Static.** Agent 10 reviewed the hook (b2r S26); syntax compile PASS (R2.11). Agent 2's build passes a map check:
   - sub_83FBF7D0, sub_83FAF180 and (Xenos only) sub_83FB09E8, sub_83FC0C10 resolve to `gpu_wait_backoff.cpp.obj`;
   - hooked aliases 27 -> 31 vs devoffB (N2); `__imp__` names in the generated TUs (`build/agent6/hang/base1-owner.txt`).
1. **P1** (STATS=1, back-off OFF). One profiling run of attract, never a timing run. It measures:
   - waits per frame and the wait-duration histogram;
   - L2 blocking polls per frame.
   - These size S and Q.
2. **Functional** (game slot). Back-off ON at Q = 250, menus + attract route, against an OFF run:
   - gate_logdiff NEW 0 / MORE 0 / flags 0;
   - the same exit codes;
   - no new STUCK-LOCK.
3. **Window sweep** (quiet machine). Arms: OFF, Q = 0 (Agent 6's (e)), 125, 250 and 500 us; >= 3 runs each,
   alternated.
   - Score by the metric rule, plus render-thread and process CPU and GPU Commands busy/blocked.
   - Pick the largest CPU drop with no loss in p99 or the 1% low beyond the run-to-run spread.
   - If every Q loses on p99 or the 1% low, go to stage 2.
4. **Agent 6's loaded-machine arm.** The hook build of devoffB, attract-long, on a loaded machine; hook OFF vs ON
   (step 3's Q); >= 3 runs each.
   - Count STUCK-LOCK reports by owner site (L1: 83FAF188/83FAF200/83FBF868; L2: 83FB09F0) and frames >= 5 s.
   - From the STATS counters, check that no poll was delayed after its fence word moved.
   - The 5 s STUCK-LOCK report stays on as the detector.
5. **Stage 2,** only if needed: steps 0-4 again with the SDK change.

### S5.2.5 What it needs, and from whom (S4 with the user; nothing tonight)

- **Agent 1 / the user:** S4 grants for `DimensionsRecomp/rexlego/src` (the new file) and `CMakeLists.txt`. Stage 2
  adds the SDK grant for `command_processor.cpp/.h`.
- **Agent 2:** the build. devoffB's sources + the file, OFF, the same codegen as devoffB, no regen, <= -j10. Then the
  staged bin with sha256s and the step-0 map check.
- **Agent 10:** the review.
  - Stage 1: no guest writes; the reset rules (H0, moved word, GPU off); the lr gate and S_FALSE == 1; the Xenos-only
    guard; the cost of the OFF path; the per-thread timer; the pch-equivalent loads.
  - Stage 2: the memory-order argument and the SDK diff (S4.1.3 (a1)).
- **Agent 6:** the loaded-machine arm (step 4) and the owner-site counts.
- **Agent 7:** the metric read-out (S4-DRAFT #23).
- **The window-4 runner (Agent 8's role):** steps 1-4.

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

## S4.1 Render-thread GPU-wait spin (step 1): done 05:40

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
  - **Correction to S3.8 (its "GPU-wait spin" bullet): this is a fence wait, not a wait for ring-buffer space.** The
    S3.8 conclusion stands: the render thread waits for the command processor, so faster guest code only spins faster.
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
  - Its only client on Windows is `HighResolutionTimer` (`include/rex/thread.h:150-177`). It is created once, for the
    KeTimeStampBundle 1 ms tick (`src/kernel/xboxkrnl/xboxkrnl_module.cpp:184-199`), whose callback stores
    `Clock::QueryGuestUptimeMillis()` into bundle+16.
  - Basis: a grep of SDK `src` and `rexlego/src` for `CreateRepeating|QueueTimer*` at 05:30, before Agent 1's 05:31
    scan ban. It found only that site and `threading_posix.cpp`, which is built only for UNIX
    (`src/core/CMakeLists.txt:56-76`). `include/`, `tests/` and rexlego were checked at about 07:05: no other user
    (S5.1).
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
  - Agent 11's R3 bundle sets it through the cvar `host_timer_resolution_ms` (S4.1.3 (d)). The cvar is defined at
    `src/system/runtime.cpp:39` (default 0) and used at `src/core/threading_win.cpp:235` (S5.1).

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
   - `HighResolutionTimer` has no other user, including `include/` (Agent 9, about 07:05; S5.1). Agent 10 can drop
     that check.
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
   - Needs: my SDK codegen grant back, a regen + full rebuild, and Agent 10's review of the generated diff.
   - Site count (A tree, 07:32; `build/agent9/s4/spin/db16cyc-sites.txt` from `db16cyc_count.py`): 20 `db16cyc` in
     10 functions, no other `db*cyc` form, and one `cctpl`/`cctpm` pair. Only sub_83FAF180 has them in a counted
     loop (8 per pass x ctr 4 = 32 per poll). The other 9 functions have 1 or 2 each. No `or rX,rX,rX` hint form
     escaped the mnemonic count: the tree's 293 self-moves are `mr r8`-`r11` no-ops.
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

## S4.2 Main scene walk (step 2): done 05:55

Subagent D's static analysis, read-only, no runs: `build/agent9/s4/scene-walk/REPORT.md` (sections 0-5; its helper
scripts and `step1.log`-`step7.log` are in the same folder). `TUn:L` refs are A-tree files
(`baseline/DimensionsRecomp/rexlego/generated/default/legodimensions_recomp.n.cpp`); the walk's guest code is the same
in devoff2, native2 and native3d. The question is Agent 7's n-prof vs a-prof result: Main busy +2.40 ms/f, of which
+1.99 is the sub_82AFAB68 -> sub_82AF9BC0 subtree, 1.006 (13 samples) -> 2.992 (54) ms/f
(`perf-notes/agent7-present.md:413-436` at 05:35; D's `:219-223` refs went stale when Agent 7 edited the file).

### S4.2.1 What the walk is, and what sets its per-frame work

- **It is the UI/HUD layer render, not a 3D scene graph.** The main-loop body sub_82FEB7B8 calls sub_82AFAB68 once per
  iteration (lr 0x82FEBCC0, TU59:14407-14409), and sub_82AFAB68 keeps its own nesting counter (0x8491D674). So one
  depth-0 call is one Main frame.
- **The chain:**
  1. sub_82AFAB68: two loops over the 15 slot pointers at 0x8491D6E0 (TU210:6949-7110, :7224-7336), so at most about
     30 calls of sub_82AF9BC0. They are gated by each slot's active byte p+4040, its mode p+120 and the mode-1 enable
     0x84959FA0.
  2. sub_82AF9BC0, per slot, reaches sub_82FCC500 through an indirect call (hyp, from the profile tree).
  3. sub_82FCC500: while the UI skip counter 0x849F5EF0 is > 0, it decrements it and returns 7 without drawing
     (TU173:11095-11110).
  4. sub_82FCB308: the scene list. Each scene that passes the filters gets scene->vtbl[56] (TU220:13370-13588). The
     loop runs under the lock sub_82A2A260 (lr 0x82FCB474).
  5. sub_82F050B0, per scene: an early exit (sub_82EF4338) and an empty-lists skip, then either two-layer mode (when
     sub_82FBC4D8(*(0x849F5F14)) != 0) or 7 layers, with layer 2 skipped while 0x849E21D0 > 0 (TU340:12582-12840).
  6. sub_82EF8C18, per layer list: a linked list accessed by index, so about n^2/2 hops, and element->vtbl[324] per
     element (TU230:12578-12630).
  7. sub_82F0CCD8, recursive, per element: the only prune is node->vtbl[336] (TU41:10872-10890). Then come a matrix
     compose, 4 more virtual calls, and the children from the iterator that sub_82F0B200 builds (lr 0x82F0CDEC).
- **Text is laid out again on every draw.** sub_82EFE948 calls sub_82EF3B38 -> sub_82EF3180 with no condition
  (TU45:12697-12699): there is no cached layout and no dirty flag. Each call opens a 15,152-byte frame
  (TU34:12285-12294), memsets 13,199 bytes through the memset hook (TU34:12430-12451), measures the string (a
  binary-tree search per glyph pair in sub_82B61580, probably kerning; TU391:7223-7309), and emits the glyphs.
- **Only guest UI state sets the work:** the active slots and their modes, the scenes that pass the filters, the layer
  mode, the list lengths, the visible elements, and the text elements and their lengths. The skip counters 0x849F5EF0
  and 0x849E21D0 and the two-layer switch 0x849F5F14 turn large parts on or off.
- **Nothing on the chain reads a timer, fence, query, vblank or frame delta.** The event object the main loop passes
  down has no time field (TU59:14367-14397). Timing could get in only indirectly: through vtbl[336] or animation state
  in the element classes, or through whatever arms the skip counters.
- **Who writes the switches:**
  - 0x849E21D0: sub_82EFC738 copies *(0x849D36F8) into it when its r27 == 2 (TU129:12296-12307); the walk decrements
    it (TU340:12815).
  - 0x849F5F14: only sub_82FD7DA8 (TU240:14069). About 70 functions read it.
  - 0x849F5EF0: the only lis-addressed store is the decrement (TU173:11106). The arming store uses a computed address,
    so finding it needs a scan (S4.2.5).

### S4.2.2 Native vs Xenos: nothing different reaches the walk

- No query, fence, ring, vblank, resolve or device-state hook is reachable by direct calls within depth 5
  (step6.log:60-82).
  - Native GetData returns real counts (`rexlego/src/gpu_native/queries.cpp:172-194`), but the walk can't reach it;
    it reaches only ReleaseQuery, rarely.
  - It does reach InvalidateGpuCache, which native makes an empty function (`hooks_device.cpp:171-175`). So native is
    cheaper there, not dearer.
  - Limit: the search doesn't follow the 159 (UI/text subtree) / 333 (whole walk) indirect call sites. The native
    profile shows no gpu_native frame under the walk (`build/agent7/prof/an-main-tree-afab.txt:65-114`).
- **Host code inside the walk costs about 0.28 ms/f:** 5 of n-prof's 54 samples are hook leaves (memset 3, memcpy 1,
  the native-only heap-journal free hook 1). memset and memcpy are hooked in both builds and scale with the call count.
  The journal hooks run while `native_scene_diagnostics` is true, its default (kInitOnly,
  `rexlego/src/native_skin_diagnostics.cpp:14-16`). The other ~49 samples (~2.7 ms/f) are guest code.
- **Frontend confound: nil.** D left this to Agent 7; I checked it at 05:45-05:49.
  - `settings_native_hooks.cpp` is compiled only with LEGODIMENSIONS_NATIVE_GPU (:1, :240), and the cvar
    `native_settings_frontend` is defined inside it (:16). So devoff2 has no native-frontend code, and "frontend on in
    a-prof" (agent7-present.md:372) is only a runner toml value that nothing reads.
  - n-prof (`build/agent8/matrix/20261122-0357/runs/0405-n-prof-r1`, native2-bin) ran with
    `--native_settings_frontend=false` (run.json:68). With that, GetBridge returns null (:84), and the hooks call
    `__imp__` and return (for example :140-147).
  - So both runs drew the guest's own frontend.

### S4.2.3 H1 / H2 / H3

- **H1, more work per frame: favoured.**
  - The walk grew x3.0 and its text part about x3.6, while the rest of Main grew only x1.16
    (agent7-present.md:418-432). A uniform slowdown would hit all of Main's guest code alike.
  - sub_82B61580 is a pure guest leaf with no calls, and it went from 0 to 5 samples. No hook can change its cost per
    call.
  - The same subtree is 1.006 vs 0.314 ms/f in two devoff captures (agent7-present.md:433), so UI state alone moves
    it 3x.
- **H2, the same calls but slower:** about 0.3 ms/f of direct host time. A uniform effect (cache, clock) is bounded at
  about 16% by the rest of Main.
  - In a-prof, Main waits 10.37 ms/f in a guest critical section entered through sub_82A2A260
    (agent7-present.md:456), the walk's lock function. The busy-only tree can't tell whether the walk's call site
    (lr 0x82FCB474) is the one; the probe's lock_ns column can.
- **H3, a native-only branch:** the candidates are the skip counters, the two-layer switch, the sub_82EF4338 early
  exit, the empty-lists skip and the slot modes. None reads a GPU value, so H3 needs UI state that depends on timing.
  n-prof and a-prof ran at about the same fps (70.8 vs 67.7), so the frame rate alone can't be that timing.
- **Verdict:** H1 is most likely, with about 0.3 ms/f of H2 on top. Static reads can't exclude H3. The probe settles
  it with one count-only run per build.

### S4.2.4 Call-count probe (REPORT section 3; spec only, nothing built)

- **Files:**
  - a new `rexlego/src/scene_walk_probe.cpp` (+ .h);
  - a CMake option `LEGODIMENSIONS_SCENE_WALK_PROBE`, default OFF, in a block after `CMakeLists.txt:154` (the
    pattern at :143-154);
  - one `#ifdef`'d Add() line in each of the memset and memcpy hooks (`native_memops.cpp:166-185`) and the native
    alloc/free hooks (`native_skin_diagnostics.cpp:176-217`), instead of second hooks (those would be duplicate
    symbols). devoff2 doesn't build that file, so there the probe hooks alloc/free itself, under
    `#ifndef LEGODIMENSIONS_NATIVE_GPU`.
- **Gates:** with the option OFF there are no hook symbols. At run time `LEGO_SCENE_WALK_PROBE=<csv path>` turns it
  on; unset or 0, every wrapper just calls `__imp__`. `LEGO_SCENE_WALK_PROBE_TIMING=0` and `_LEAVES=0` drop the QPC
  columns and the leaf counters.
- **Hooks:** pass-through `REX_HOOK_RAW` wrappers in the style of `tt_lock_trace.cpp:12-14, 105-122`, on 18 targets
  that are unhooked in both builds (step6.log:24-54). The counters are thread_local and count only while the walk
  runs.
- **Frame boundary:** one depth-0 call of sub_82AFAB68 on Main. Swap can't be used: in native it is a hook on the
  render thread, and in devoff it is guest code.
- **Columns** (REPORT 3.3): slot modes; ui_calls and ui_skip; screens; scenes; scene_early; two_layer; layer2_skip;
  lists, list_n and list_hops; nodes and max_depth; visible; text_elems; text_calls and text_chars; measure_calls;
  glyph_calls; 4 leaf counts; memset, memcpy, alloc and free counts; walk_ns, tree_ns, text_ns and lock_ns; and the 4
  switch globals at frame end.
- **Output:** one CSV row per frame (CREATE_NEW; a 64 KB thread_local buffer, so no syscall per frame) and one log line
  every 600 frames. Cost < 0.1 ms/f. The count-only run (TIMING=0) is the clean H1 test.
- **Builds and runs:** Agent 2 builds devoff2-probe (NATIVE_GPU=OFF) and native3d-probe (ON); guest codegen doesn't
  change. Same route and capture window (frames N..N+1800 after the route marker); native with
  `--native_settings_frontend=false`; one count-only and one timed run per build; then capped vs uncapped, to see
  whether the counts follow the frame rate. How to read the result: REPORT 3.8.
- **Needs:** Agent 1's grant for rexlego (written by me or Agent 2), Agent 2's build, Agent 10's review, slot runs.

### S4.2.5 Zero-build A/Bs, items not proposed, scans after 07:15

- **Zero-build A/Bs on native3d** (profile runs in Agent 8's slot, only if Agent 1 wants them):
  - n0: `--native_scene_diagnostics=false`. If the walk drops by more than 0.2 ms/f, default it to false in perf
    builds.
  - n1: `LEGO_NATIVE_MEMOPS=0` (`native_memops.cpp:19-22`), in both builds.
  - Optional: `LEGO_NATIVE_LIGHT_MARKERS=0`.
  - **Limit:** at the slot's 1.3-1.7 sampler rounds/s the walk gets about 54 samples per run (0.055 ms/f each), so
    2se on a run-vs-run difference is about 1.1 ms/f. These runs can catch only a large effect; the probe's walk_ns
    is the real test.
- **Not proposed now:** caching the text layout, or an O(n) replacement for sub_82EF8C18. Both change how guest code
  runs; the O(n) walk is output-identical only if no vtbl[324] callback edits the list. Revisit only if list_hops or
  text_calls turn out large, and after the vtable dump.
- **Scans for after 07:15** (REPORT section 4):
  - who arms 0x849F5EF0 (`lis -31585` + `addi 24304`, or stores through a base near 0x849F5EC0);
  - the callers of sub_82EFC738 and sub_82FD7DA8;
  - a vtable dump for vtbl[336], [324] and [56] (does the visibility test read timers or animation state?);
  - the 159/333 indirect call sites (or rely on the probe).
- **Scan results (07:33-07:35; `build/agent9/s4/scene-walk/scans-s425.txt`, `arm_scan.py`; fq.py, A tree):**
  - 0x849F5EF0: no store arms it at a constant address. fq.py's constant-EA index and a per-function
    lis/addi/addis/ori/mr tracker both find only sub_82FCC500's decrement (TU173:11105). So the arming store goes
    through a pointer that is not a constant in its function, or a copy or fill of the 0x849F5EC0-0x849F5F00 block
    (22 functions write other words of it), or it never happens in normal play. The probe's counter column settles
    it.
  - 0x849E21D0 and 0x849F5F14: the tracker confirms S4.2.1 (sub_82EFC738 TU129:12306 and the walk TU340:12814;
    sub_82FD7DA8 TU240:14068).
  - Callers: sub_82EFC738 has 14, all at 0x82FB7D90-0x82FE6D88, the range of the walk's sub_82FCB308 and
    sub_82FCC500 (list in the file). sub_82FD7DA8 has 1, sub_82FF68E8 (TU246:13425).
  - Not done: the vtable dump and the 159/333 indirect call sites (the probe covers both).
- **My spot-checks of D's claims (A tree), all confirmed:**
  - TU173:11095-11110: 0x849F5EF0 > 0 -> decrement, return 7;
  - TU34:12285-12294 and :12430-12451: the 15,152-byte frame; r5 = 13199, then sub_83E46040 at lr 0x82EF32B8;
  - TU41:10872-10890: vtbl[336] at lr 0x82F0CCFC; low byte 0 -> return;
  - TU230:12578-12630: walk i steps from the head, then element->vtbl[324](element, 0x847BC800) at lr 0x82EF8C84;
  - TU45:12697-12699: `bl 0x82EF3B38` right after the argument stores.

## S4.3 S4 codegen ranking (step 3): done 05:55

S3.8's list, re-ranked with S4.1 and S4.2. Every codegen item needs my SDK codegen grant back, a regen, Agent 2's full
rebuild, Agent 10's review and a game gate. Stage B/C also waits until Stage A passes the full game gate (B passed only
the front-end gate, S3.6).

**Who can gain what:**
- **devoff/PM4 builds (devoff2, devoffB):** GPU Commands / the CP sets the frame (S3.8, S4.1). In a-prof, Main waits
  10.37 ms/f in a guest critical section while the render thread is busy, and the render thread spends 13.0 ms/f in
  the fence spin (agent7-present.md:442-456; S4.1.1). So guest codegen saves CPU and power only; fps can move only
  through power headroom.
- **native builds (native3d, nativeB):** there is no fence spin. BlockOnFence becomes `HostDevice::Synchronize`
  (`rexlego/src/gpu_native/hooks_device.cpp:196-200`) and KickOff returns a scratch marker (:277-287). n-prof's render
  thread waits in a kernel wait (sub_83FA6020) and otherwise runs SwapHook, BindShader and DrawVertices
  (agent7-present.md:457-459). Main is busy in 42.7% of rounds (a-prof 24.6%), render waits on Main 1.05 ms/f
  (:443, :458), and Main is the busier thread in timing (5.31 vs 4.94 ms/f, :504). So Main savings can move native
  fps, once Agent 7's render-thread items land (:492-509).
- **A saving inside the render spin is worth nothing in either regime.** While the thread spins, it only polls
  faster. After (a1)/(a2) it polls a few times per wait, so the per-poll cost stops mattering.

**Marks:** [spin] = the measured saving is inside the devoff render spin: no CPU, no fps. [main] = Main-thread guest
code: real CPU, and fps is possible on native. [all] = every guest thread: real CPU.

1. **Stage B/C** (`non_argument_as_local` + `non_volatile_as_local`, together; S2.1; risk high: the setjmp/longjmp and
   SEH review comes first). [main] [all], but its only profile evidence is [spin].
   - S3.8 based it on about 2 ms/f of `__savegprlr_29`/`__restgprlr_29` on the render thread. All of that is spin
     time. `__savegprlr_29` (self 1.16) sits inside sub_83FAF180 (inclusive 9.98 = self 7.97 + sub_83FA2698 0.85 +
     1.16). `__restgprlr_29` (inclusive 1.08, `__chkstk` 0.23 of it) sits inside sub_83FBF7D0 (13.00 = self 1.94 +
     9.98 + 1.08). Source: `build/agent9/prof/ab-render-a9.txt:75-81, 100, 115-117`. So those 2.2 ms/f are worth 0.
   - Main has almost no save/rest samples: one each of `__savegprlr_27` and `__restgprlr_14`, 0.08 ms/f each
     (`ab-main-a9.txt:78, 169`). Main would gain only from fewer ctx loads and stores of r0/r2/r11/r12/f0/v32-v63 and
     the non-volatiles, for example in tight loops like the walk's hop loop (TU230:12592-12613).
   - Size: unmeasured. B's Stage A set moved Main's guest leaves by -0.51 ms/f (2se 1.28, S3.8); Stage B/C adds the
     rest of S2's -6.47% (all 6 localization keys).
   - It stays first because it is the only item that touches every function on Main.
2. **Flush-mode dataflow across labels** [all]. Unchanged (S3.8 item 4).
3. **PGO devirtualization of `bctrl` sites** [main] [all]. The walk makes 6 virtual calls per drawn element
   (vtbl[336], [340], [332], [344], [348], and [56] per child) and one per list element (vtbl[324]). But indirect
   dispatch is already lean (session 1 notes), so each call saves only a few ns. Sizing it needs an indirect-target
   profile, the probe's nodes/list_n counts and the vtable dump.
4. **Guest memory macro experiments** [all] (`volatile` and the phys-offset compare on every access; session 1, item
   8; `pch_h.inja:128,135-145`). Every hop of the walk's list loop is a guest load. Measured experiment only (risk
   high for volatile, medium for the offset).
5. **`[[unlikely]]` on divide guards** [all]. Unchanged.
6. **The redundant mfmsr/mtmsrd fence** [all]. Unchanged.
7. **musttail for indirect tail calls** [all]. Unchanged.
8. **(b) `db16cyc` -> `_mm_pause`** [spin] (S4.1.3 item 4; half of S3.8 item 2). devoff/PM4 only. It saves no
   OS-visible CPU, only power and HT-sibling time, and it is moot once (a1)/(a2) land.
9. **(c) a codegen spin policy** [spin] (S4.1.3 item 5; the other half of S3.8 item 2). devoff/PM4 only. (a1)/(a2) do
   the same job better, because the hook knows the wake condition.
- **Never for LEGO now: skip_lr** (host code reads `ctx.lr`, S2.2). Unchanged (S3.8 item 3).

**Not codegen, but this is where the real savings are:**
- devoff/PM4: (d) Agent 11's timer change (W4b arm d11t, about -0.85 core), then (a1) or (a2) (about -0.85 or -0.7 to
  -0.8 core); see S4.1.3.
- native: Agent 7's render-thread items (agent7-present.md:492-509), and the scene-walk probe (S4.2.4) before any
  Main fix.
- **Measuring codegen items:** on devoff fps can't move, so the metric is CPU per frame from window-4 timing. The
  slot's profiler (1.3-1.7 rounds/s) can't resolve effects under about 10% (S3.8).

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

## R2.11 (run 2) Task #11: #24 step 0 prep, then #26 and #41 step 1

> Agent 1, 13:05. Reads and notes only: no builds, game runs or git writes; BelowNormal, at most 2 threads.
> Files: `build/agent9/s4/**` and this file. Edits inside L1-402 were line-neutral (L1-3 RESUME, L320-335,
> L366-368), so the citations S4-DRAFT:188, b2r:1360, b2r:1385 and agent12-io-memory:686 still hold.

### R2.11.1 Draft N1-N4 (b2r S26 L1417-1421)

- Draft `build/agent9/s4/fence-wait/gpu_wait_backoff.cpp.draft`: SHA-256
  01D9F8F3464C861401C3BE98F797938619C5DD85B1AEA166B6D9CED053FA19DD, 18,177 B, 395 lines, LF only.
- The rated text is kept as `gpu_wait_backoff.cpp.draft.rated-D176CA8D` (16,485 B, 372 lines).
- Diff `build/agent9/s4/fence-wait/gpu_wait_backoff.n1-n4.diff` (`git diff --no-index`, +45 -22, SHA prefix
  803B8382AA08E6F2).
- **N1:** `ParseUs` starts with `if (!s || *s < '0' || *s > '9') return false;`. Values such as "-5", "+5", " 5"
  log a warning and are ignored (Q stays OFF, S stays 30). This covers both LEGO_GPU_WAIT_BACKOFF_US (:123) and
  LEGO_GPU_WAIT_SPIN_US (:125; new `spin_ok` and REXLOG_WARN). Larger values still clamp to the max.
- **N2:** the Build comment carries the map check: sub_83FBF7D0, sub_83FAF180, sub_83FB09E8, sub_83FC0C10 (H0-H3)
  resolve to `gpu_wait_backoff.cpp.obj`, so devoffB's 27 hooked aliases become 31.
- **N3:** pch citation `legodimensions_pch.h:120-129` in generated/default and `:124-133` in B's batch-nolr pch
  (same text).
- **N4:** `sleep_ticks` (QPC around SleepUs, failures included, only when stats are on); MaybeLog prints
  "sleep_sum {:.2f} ms" after "sleep {}" (26 placeholders, 26 args).
- Unchanged: the H0-H3 logic and the OFF path (env vars unset: every hook goes straight to `__imp__`).

### R2.11.2 Syntax compile: PASS (b2r S26 "Landing OFF needs" item 2)

- Script `build/agent9/s4/fence-wait/syntax_check.ps1`; report
  `build/agent9/s4/fence-wait/syntax-20261122-132450.txt` (RESULT: PASS, exit 0).
- Flags: devoffB's own command for rexlego `src/native_lock_elide.cpp` from
  `build/agent2/snapB-off/compile_commands.json` (469 entries). That is clang 23.1.6, -O3 -std=gnu++23
  -march=x86-64-v3 -msse4.1 -DWIN32_LEAN_AND_MEAN -DNOMINMAX, -isystem snap1-sdk/install/include, no PCH flag, no
  -Wall. Only `-o <obj> -c <src>` is replaced by `-fsyntax-only <src>`, where the source is a copy of the draft
  (`build/agent9/s4/fence-wait/syntax/gpu_wait_backoff.cpp`).

| Compile | Exit | Time | Diagnostics |
|---|---|---|---|
| control (live native_lock_elide.cpp, SHA 17AC1094) | 0 | 163.9 s (cold) | 1: getenv deprecation |
| candidate (a), `-DLEGO_GPU_WAIT_HOOK_GETDATA=1` | 0 | 81 s | 3: getenv deprecation at :123/:125/:129 (expected) |
| candidate (b), no define | 0 | - | the same 3 |

- No new diagnostic text. Positive control (-E): (a) defines sub_83FAF180, sub_83FB09E8, sub_83FBF7D0,
  sub_83FC0C10; (b) defines only sub_83FAF180 and sub_83FBF7D0.
- Lint (-Wall -Wextra, informational): (b) adds only unused kLrGetDataTry, kLrGetDataLoop, kGetDataNotReady
  (:87-89) and t_l2 (:160). Not fixed, to keep the diff to N1-N4. Optional cleanup at landing: put the four under
  `#if LEGO_GPU_WAIT_HOOK_GETDATA`.
- Still open (not part of this task): the S4 grants for `rexlego/src/gpu_wait_backoff.cpp` and CMakeLists.txt,
  landed with #30 and C1 so the native baselines are re-pinned once (another native-fingerprint input, like C1);
  then, after W4b, Agent 2's batch-nolr build with skip_lr off and the map check (H3, 27 -> 31 hooked aliases).

### R2.11.3 #26: db16cyc rebuild cost

- Count: `build/agent9/s4/spin/db16cyc_count.py` over devoffB's
  `build/agent2/snapB/DimensionsRecomp/rexlego/generated/default` (432 .cpp, 464 MB); list in
  `build/agent9/s4/spin/db16cyc-sites-B.txt`. Result: 20 db16cyc sites, 1 cctpl, 1 cctpm, 13 db runs, in 10
  functions, each in its own TU (B numbering):
  - sub_83FAF180 TU383: 8 sites plus the cctpl/cctpm pair (this is H1 of #24);
  - 2 each: sub_83F99F80 TU107, sub_83F9A5B0 TU354, sub_83FCB608 TU389;
  - 1 each: sub_83E66CD8 TU162, sub_83EA90D0 TU265, sub_83E63F38 TU281, sub_83E96348 TU329, sub_83E70320 TU378,
    sub_83E64900 TU394.
- devoffB `.ninja_log`: these 10 TUs take 18.8-36.3 s each (233 s CPU in total). The exe link takes 5.5 s. The
  recomp TUs use a PCH (cmake_pch.hxx.pch 12.0 s). init.cpp.obj takes 99.0 s and register.cpp.obj 101.9 s. The
  whole build took 1,039 s wall and 9,420 s TU CPU.
- Codegen rewrites only files whose text changed (`src/codegen/file_io.h:46-53`, WriteOutcome::Unchanged;
  `codegen_writer.cpp:699-701`), so only those 10 TUs recompile, plus init/register only if their text changes.
- **Caveat:** the skip stamp (`output_stamp.cpp:67-97`, ComputeInputFingerprint) hashes the SDK version, flag
  values and input files, but NOT the codegen binary. A builder-only change leaves the module "up to date", with
  stale TUs. Put the change behind a new flag (OFF by default) or force the regen (a full regen is 129.8 s, 883
  files, `build/agent2/codegen-steps.txt`).
- Pause without a pch change: SIMDe is already in the pch chain (`simde/x86/sse2.h:4770` simde_mm_pause; the
  `_mm_pause()` macro is at :4798), or use `__builtin_ia32_pause`. The pch has no immintrin.
- **Answer: ~2-4 min, not ~35-45.** The 10 TUs compile in parallel (the longest ~36 s), then the link takes 5.5 s.
  The ~130 s regen and the SDK codegen-tool rebuild bring it to ~4-6 min end to end. Add ~100 s if a new flag is
  echoed into init/register. It is ~35-45 min only if the pch, an SDK header or every TU changes (9,420 s TU CPU:
  ~17 min at B's effective ~9x parallelism, ~40 min at -j4).

### R2.11.4 #41 step 1: writers of the front-end gate flags (static, A tree; stopped at 14:00)

Full list with TU:line for every site: `build/agent9/s4/fe-gate/41-step1.txt`. Scan: `build/agent9/s4/fe-gate/addr_scan.py`
-> `addr-scan.txt` (lis-based tracking over 1,540 functions; it reports register formations, x-form accesses and
pointers passed to callees, which fq.py's constant-EA index misses). Callers: `41-callers.txt` (fq.py pickle rebuilt
13:54, 164,786 functions).

- **0x849004EC bits 3/6.** sub_82A832F8 TU411:6120 is Test(n) on a bitset at 0x849004EC (word n>>5, mask 1<<(n&31)),
  so the mode-3 queries test masks 0x08 and 0x40. sub_82A7C080 TU415:5846 is AnySet() over 9 bits (read-only).
  - Bit 6 has one writer: sub_82A9F718 TU18:6499 (`ori 64` through r29 = 0x849004EC). It runs only while AnySet() is
    false and when a loaded block's first word is > 13 (after an FNV-1 check of that word against word +4). It has no
    direct callers (a callback through a function pointer).
  - **Bit 3 has no static writer** (no `ori 8`, no store through a lis-formed base, no generic Set(n); the only pointer
    escape is the read-only AnySet). Unless a data pointer writes it, query 3 is always false.
  - The other sites set 0x04 (8 sites in 7 functions, e.g. sub_82A83570's file-time failure path) or 0x01
    (sub_82A9F670), or clear the word (sub_82A832E8 Reset, sub_82A93660); sub_8408E300 clears the high half at init.
  - **Correction:** "the single writer is sub_82A83570" (s6-clock-report.txt:424, used in S4-DRAFT S1h) came from s6's
    clock-function subset. The tree has 12 writer sites; sub_82A83570 sets only 0x04.
- **Byte 0x848E2EA2.** No writer at all: no constant EA, no base formed in 848E2E00-848E2EBF, no x-form, no pointer into
  the window passed out. 0x848E2EA0 is the same. Readers: sub_82A75FD8 (getter; callers sub_82FB9020, sub_82FBA9E8,
  sub_82FD4868) and sub_82A7EAA0 (caller sub_82FE6CC0). So the byte either keeps the image's initial value (then this
  gate term is constant) or is written through a data pointer or a block copy that starts below the window.
- **[app]+2288** (unchanged since 07:39, `build/agent9/b-clock/fe-gate-flags.txt`): set to 1 by sub_82FE08C8 on the
  freeze request (+2289); set to 0 by sub_82FE7E40 on the resume request (+2290) and by sub_82FF68E8; init
  sub_8407C158; requests from sub_82FF63A8 (only caller sub_83AA1170) on a message match.
- **For the #41 pair:** the terms that can change at run time are bit 6 (a loaded block's version word) and +2288
  (freeze/resume messages). 0x848E2EA2 and bit 3 look constant. Log sub_82A75FD8's and sub_82A832F8's returns with each
  sub_82FD4868 call.
- **Not done (time box):** what installs the sub_82A9F718/sub_82A9F5C8 callbacks; the image's initial byte at
  0x848E2EA2; a wider pointer window for EA2.

### R2.11.5 Review and messages

- Agent 10 re-checked the N1-N4 draft (b2r row 33, S32): all four fixed, no other code change, syntax PASS, S26 stands
  (landing OFF SAFE after the rest of step 0; ON SAFE to test after steps 1-4; nothing UNSAFE).
- Agent 10's note: the STATS line now has sleep_sum before sleep_fail, so a positional parser must be updated. The P1
  parser should key on field names. The draft is not changed for this.
- Sent: `@@to 10, 11` (hash, syntax report, a9 line numbers unchanged, #41 file) and `@@done 11`.

### R2.17 (run 2) Task #17: #26 staged for S4b (db16cyc -> pause), 14:02-14:50

Agent 1's task #17 (14:02): stage #26 so it can go into S4b (u_block came back at 0.93, so C1 goes to an A/B test and
S4b is a full rebuild after W4b). Staging and notes only: no builds, codegen-tool builds, regens, game runs or git
writes; last command 14:50, notes until 15:00, then idle until W4b is done. Agent 2 applies the staged SDK diff in the
S4b snap tree (and #24's grants: gpu_wait_backoff.cpp from draft 01D9F8F3 plus the CMakeLists.txt edit). Everything
is in `build/agent9/s4/spin/db16cyc-pause/`; HASHES.txt has every hash, and stage.py rewrites all staged files
deterministically (a re-run at 14:14 gave identical hashes).

### R2.17.1 Base and hashes

- Live SDK `DimensionsRecomp/rexglue-sdk`, HEAD c5fe668e76853630ffc6df2761e9cd8ed5368476 (`git status` shows
  ` m thirdparty/simde`; not mine). The S4a snap1 copy `build/agent2/snap1/DimensionsRecomp/rexglue-sdk` has the same
  bytes for all three files (S4a didn't touch codegen). All LF, no BOM:
  - src/codegen/builders/system.cpp D1269273636B5A1A57BE6E467CE19326EAEA38F7E0E5A0C157D4B23998D10506 (12,635 B)
    -> new FAD4372074D32D69D5B2CB0B100F283E239A426C3E015DBD66C22BCB693998D2 (12,947 B, +4 lines);
  - include/rex/codegen/config.h D07C575FF2904B8753FA4B4306847375EC2EB69156355947E874AFFFC19F46C2 (6,941 B)
    -> new CD39B0E110D3E0FD9E602446111183CB941478BF9057389BB815F125060D2087 (7,032 B, +1);
  - src/codegen/config.cpp 0ED529B7E5F0F4E7CC0A4551A1C5C3A3191F03D28D491D517850898D5062FCFD (23,576 B)
    -> new 4706A7F22C3859D6DBE8E7A3150B3403548856BAD626952818F7B96B3D5935DF (23,701 B, +2).
- Read only, hashes recorded in HASHES.txt: codegen_writer.cpp 8235C8C7…, project_recompiler.cpp 41E38ADD…,
  output_stamp.cpp 141BA870…, output_partition.cpp 36C396BC….

### R2.17.2 The change: codegen option `db16cyc_pause`, default OFF

- `db16cyc-pause.diff`, SHA-256 AC554DBBD965BF941BADE6391D0E0F483BE075B8A72434EEE8CB9D189ED61452 (1,969 B, +7 lines
  net). Paths are relative to the SDK root: `git apply -p1` or `patch -p1` from there. `patch --binary -p1` onto
  base/ gives exactly new/. The base/ and new/ copies of the three files sit beside it.
- config.h: `bool db16cycPause = false;` after vmxVectorFallbacks. config.cpp: a MergeBool for the TOML root key
  `db16cyc_pause`, after the vmx one. system.cpp build_db16cyc: a 4-line comment, then
  `if (ctx.config().db16cycPause) ctx.println("\tsimde_mm_pause();");` (the `(void)ctx` line goes). cctpl, cctpm
  and cctph stay empty.
- No pch change: simde_mm_pause is in the installed simde/x86/sse2.h:4770 (the native path calls `_mm_pause()`), which
  the generated TUs already use (TU383 has 91 `simde_` uses). The SDK pch doesn't include rex/codegen/config.h
  (function_types.h only forward-declares RecompilerConfig), which is why the `-I` overlay works with the pch.
- OFF is byte-identical. build_db16cyc emitted nothing before and still emits nothing. The flag is not in
  FingerprintModule (project_recompiler.cpp:79-101), and sdkVersion = REXGLUE_VERSION_FLOOR "-"
  REXGLUE_VERSION_CHANNEL (codegen_command.cpp:81) is static. So a rebuilt tool with OFF skips the regen, and even a
  forced regen writes identical files (WriteIfChanged). I left the fingerprint alone on purpose: adding the flag there
  would change it even with OFF.
- ON forces exactly one regen. Emission-only bools reach the stamp through the config toml's content digest
  (cfg.loadedFiles -> inputs, project_recompiler.cpp:65-66; output_stamp.cpp:81-95). So the stamp hashes the toml
  content, not flag values (a correction to the task text; the effect is the same). Removing the line forces one regen
  back.
- An old tool silently ignores the key (ApplyToml has no unknown-key check) and regens to identical output. So the toml
  line must land together with the new tool. Check after the regen: `simde_mm_pause` 20 times, in exactly the 10 TUs
  of R2.17.5.
- init/register: unchanged, so no +100 s. config_flags (codegen_writer.cpp:288-297) holds 8 flags and I didn't add
  this one; the function list and registrations don't change. sources.cmake, the `_funcs.N.h` files (no new
  references) and codegen.partition.json are unchanged too. Only codegen.stamp changes.

### R2.17.3 The toml line goes in the codegen config, not the harness toml

- harness/legodimensions.toml (B763DABBE2C5FE7AFA300B3013EFDEE1FB9BF33E7A0A96738BEAC4BAF474FF54, untouched) is the
  runtime config the EXE reads (its header: rex_app.cpp SetupEnvironment). Codegen never reads it: codegen reads
  rexlego/legodimensions_manifest.toml, which includes legodimensions_config.toml. So the one-line diff is staged
  against each arm's codegen config, and there is no harness diff.
- B: `toml-db16cyc-pause-B.diff` 5D5892D33D09AF9D6889AF5BC991C82CD4443A8F7493053584BF6889261585B3. Base
  build/agent9/install/batch-nolr/legodimensions_config.toml E60EAF1C… (19,002 B), the same as
  build/agent2/snapB/DimensionsRecomp/rexlego/legodimensions_config.toml. The line goes after line 36
  (`musttail_calls = true`); new copy FFC119BF….
- A: `toml-db16cyc-pause-A.diff` 95D901B9784705FA656145487B5611BA95A606E4DBD28FA7BE60C9E93B8F2620. Base the live
  DimensionsRecomp/rexlego/legodimensions_config.toml 7F775847… (18,145 B), the same as snap1's copy. The line goes
  after line 23, before `[functions]`; new copy 11707872….
- Both are CRLF with the one line `db16cyc_pause = true`. Apply from DimensionsRecomp/ with `patch --binary -p1`;
  both were checked (patch onto base = new). Copies are in toml/base-{A,B}/ and toml/new-{A,B}/.

### R2.17.4 Syntax check: PASS

- `syntax_check_codegen.ps1`, run at BelowNormal on 1 thread; report `syntax-20261122-141452.txt`. clang 23.1.6.
  SDK side: the Release entries of build/agent2/snap1-sdk/compile_commands.json (2,277 entries) with the Release pch,
  plus `-I new\include` for the new config.h. Generated side: devoffB's own entry for TU383 in
  build/agent2/snapB-off/compile_commands.json (469 entries).
- system.cpp: control exit 0 (33.2 s), candidate exit 0 (14.2 s), no new diagnostics. Negative run without the
  overlay: exit 1 with "no member named 'db16cycPause'", as expected, which proves the overlay was used.
- config.cpp: control exit 0 (10.8 s), candidate exit 0 (2.8 s), no new diagnostics.
- B TU383 (sha AE1749B6121491A5): control exit 0 (4.3 s). The candidate is TU383 with the 8 predicted pause lines
  inserted (copy at syntax/legodimensions_recomp.383.cpp): exit 0 (4.5 s), no new diagnostics.

### R2.17.5 Predicted ON output

- One added line per site, 20 in all, with no new locals or references. Example, B TU383 from L37123 (sub_83FAF180,
  label loc_83FAF1A0): before, `\t// db16cyc ` is followed by the next `\t// db16cyc `; after, it is followed by
  `\tsimde_mm_pause();`. (The comment has a trailing space.)
- Only these 10 TUs change. OutputPartition::Assign (output_partition.cpp:102-151) puts every known address back in its
  sidecar bucket without re-checking the byte budget, and fileCount/maxFileBytes come from the sidecar:
  - A (S3d/snap1 = baseline partition, sidecar 22C9D89BEA8E8C6E…): TU107 sub_83FAF180 (8), TU116 sub_83F99F80 (2),
    TU205 sub_83FCB608 (2), TU321 sub_83F9A5B0 (2); 1 each: TU125 sub_83E64900, TU153 sub_83EA90D0,
    TU169 sub_83E66CD8, TU284 sub_83E70320, TU304 sub_83E96348, TU432 sub_83E63F38.
  - B (sidecar 9DADABCC6F543432…): TU383 sub_83FAF180 (8), TU107 sub_83F99F80 (2), TU354 sub_83F9A5B0 (2),
    TU389 sub_83FCB608 (2); 1 each: TU162 sub_83E66CD8, TU265 sub_83EA90D0, TU281 sub_83E63F38,
    TU329 sub_83E96348, TU378 sub_83E70320, TU394 sub_83E64900.
  - TU107 exists in both trees but holds different functions. Keep codegen.partition.json: in a fresh output dir the
    partition is rebuilt by size and every TU is renumbered.
- Runtime: PAUSE has no architectural effect, so the output is identical and only timing changes. sub_83FAF180 runs
  cctpl, ctr=4 × 8 db16cyc, cctpm, then tests bit 0x2 of byte +11069: 32 PAUSEs per pass. At ~140 cycles each on
  Skylake and later that is ~4,500 cycles (~1.1-1.5 µs), against the Xenon intent of 512 cycles (~160 ns); much
  shorter on older Intel and on Zen. Today the loop body is empty, so clang probably deletes the loop. Not staged: one
  PAUSE per run of db16cyc.
- Cost: ~130 s regen + the 10 TUs in parallel (~36 s for the longest) + 5.5 s link ≈ 3 min, plus the codegen-tool
  rebuild. S4b is a full rebuild anyway, so #26 adds almost nothing.

### R2.17.6 #41 open items (step 7)

- What installs the sub_82A9F718 (bit 6) and sub_82A9F5C8 (bit 2) callbacks: no function in the generated A tree
  builds either pointer. At all 33 `addi rD,rS,-2280/-2616` sites (findstr-cb.txt), the source register comes from a
  lis with another upper half (the address needs -32086 = 0x82AA). The ori/hex forms (`,63256` `,62920` `0xF718`
  `0xF5C8` `0x82A9F718` `0x82A9F5C8`) have 0 hits. So the pointers live in data, most likely a vtable or a static
  callback table. Finding the installer needs the image's data sections: the table word holding 0x82A9F718, then the
  code that forms that table's address. Details are in build/agent9/s4/fe-gate/41-step1.txt section E; raw output is
  in 41-cb-formation.txt (from cb_formation.py), findstr-cb.txt and findstr-cb2.txt.
- The image's initial byte at 0x848E2EA2: not done. It needs the XEX's decompressed data, or at least the section map
  to tell .data from .bss (= 0), and there is no image reader in the tree.
- Tool note: `start /b x.cmd` runs the batch under cmd /K, so its prompt stays open and the calling task never ends
  (findstr itself took 23 s and 9 s). Use `start "" /belownormal /wait /b cmd /c x.cmd`.

### R2.17.7 Messages

- Sent `@@to 10` at about 14:22: the rating request for #26. It had the diff and toml hashes, the harness-toml
  correction, the syntax report, the A/B TU prediction, init/register unchanged, the PAUSE timing note and the
  old-tool caveat. Agent 10's rating was still pending at 14:30.
- Sent `@@done 17` with the same facts and the #41 result.

### R2.17.8 Agent 10's rating (14:38, b2r row 37, S36)

- Landing OFF: SAFE (only the codegen tool changes, nothing new is emitted, and the option is in neither
  FingerprintModule nor config_flags, so the output stays byte-identical). ON: output-identical, SAFE to test.
  Nothing UNSAFE.
- Agent 10 re-applied all 3 diffs exactly: the SDK diff on base/, live and snap1; toml A on live and snap1; toml B on
  snapB and batch-nolr. The TU383 candidate is the control plus exactly 8 lines. Its census matches the 20 sites in
  10 TUs for both arms, and neither tree has a simde_mm_pause today.
- sub_83FAF180 is the back-off step of 6 GPU-progress poll loops. Its watchdog runs on a loaded clock, so PAUSE
  doesn't stretch it.
- Gates before ON: (1) the toml line and the new tool land in one build, because an old tool takes the stamp (the stamp
  digests the toml) and a later new tool then skips the regen; if that happens, force one regen. (2) Exactly 20 pauses
  in the arm's 10 TUs after the regen. (3) Keep codegen.partition.json. (4) The functional pair plus a frame-time A/B,
  measured apart from #24. If the A/B shows added latency, one PAUSE per db16cyc run is the fallback.
- Task #17 was marked done (files released) at 14:38.

## R2.22 (run 2) Task #22: #24's S4c package (+ #30's CMake option)

### R2.22.1 The task (Agent 1, 15:35)

- "#24 landing prep, part 2". S4a is live and committed (game 1bd322e, SDK 3bb65bb). The asks:
  - stage the rexlego CMakeLists.txt edit that adds gpu_wait_backoff.cpp (draft 01D9F8F3, b2r row 33) as a -p1 diff
    against live, with base/ and new/ copies and sha256s;
  - put #30 (the native-only rexlego CMake option) in the same diff if I can stage it, otherwise say who owns it;
  - a syntax-only compile (<= 2 threads, no ninja) and the expected map change (27 -> 31 hooked aliases);
  - default OFF; it goes in as an incremental S4c on top of Agent 2's S4b; send it to Agent 10 to rate.
- No builds, game runs or git writes.

### R2.22.2 The package (`build/agent9/s4/fence-wait/s4c/`, 15:50-15:57)

- Base: rexlego/CMakeLists.txt 3690D5D7... (51,070 B, 885 CRLF lines), the same in live, snap1 (S4a) and snapB.
- #30 is my item (A9 with A7; spec S4.2.4, S4-DRAFT row 30). Its CMake option can be staged, so the primary diff has
  it (OFF) and a fallback diff leaves it out.
  - The #30 block is 13 lines, including a trailing blank, after base :155 (the blank after TT_LOCK_TRACE's endif() at
    :154). It has `option(LEGODIMENSIONS_SCENE_WALK_PROBE ... OFF)`. Turning it ON without `src/scene_walk_probe.cpp`
    is a FATAL_ERROR. When ON, it appends that file and adds `LEGODIMENSIONS_SCENE_WALK_PROBE=1` to
    native_memops.cpp and native_skin_diagnostics.cpp only, as a source property.
  - The option isn't tied to NATIVE_GPU: the spec has a devoff2-probe and a native3d-probe. The probe sources and the
    #ifdef lines are not drafted.
  - The #24 block is 9 lines, after base :167 (the blank after DEV_PROBES' endif() at :166), before `if(WIN32)`. It
    has 3 comment lines, then the draft header's block: `if(NOT LEGODIMENSIONS_NATIVE_GPU)`, list(APPEND ...
    src/gpu_wait_backoff.cpp), the source-scoped LEGO_GPU_WAIT_HOOK_GETDATA=1 and endif(). NATIVE_GPU's option() is
    at :22 and the sources' set() at :25, both earlier.
- Files (full sha256 in HASHES.txt, 0489BC9F..., written 15:56:57):
  - s4c-24-30.diff (primary) DC02104EA76E0BF6AE6CF28968079B8F18208480B884B536D22F700316EDD019, 20,630 B, +417/-0.
    Hunks: @@ -153,6 +153,19 @@ and @@ -165,6 +178,15 @@, and the new file @@ -0,0 +1,395 @@.
  - s4c-24-only.diff (fallback) A279DC71D6CD4FAA7FE6D5C8B7F968DC657E1E890703EF104AF713B092A36026, 19,555 B,
    +404/-0.
  - new/ CMakeLists 1BF46D78... (52,311 B, 907 CRLF lines); new-24only/ 9A4606A7... (51,537 B, 894 lines). The new/
    TU is the draft, 01D9F8F3 (LF). Its CRLF form, which an in-repo git apply writes with core.autocrlf=true, is
    34D281E0....
  - PACKAGE.md (596E666D...), apply-check.txt, syntax-20261122-155218.txt, expected-map.txt, stage.py (stage / verify
    / hashes), syntax_check_s4c.ps1 and maplines.py. The syntax check's scratch copy of the TU was removed.
- Fix on the way: the first difflib diff aligned hunk 2 oddly (it began with `+endif()`), so stage.py writes the hunks
  by hand at the insertion points. new/ stayed identical; only the diff hashes changed (DDE7CFBE... and F286B485...
  are superseded).

### R2.22.3 Checks (no builds)

- apply-check.txt (15:52:15): PASS for both diffs.
  - Tools: git 2.56.1 (`-c core.autocrlf=false apply --check -v`, apply and `apply -R --check`) and GNU patch 2.8.1
    (`--binary` dry-run and apply), on scratch copies outside any work tree.
  - The results match new/ by sha256 with no stray files. CMake hunk lines are CRLF (34 / 15) and new-file lines LF.
- syntax-20261122-155218.txt: PASS.
  - Setup: clang 23.1.6 -fsyntax-only with the S4a devoff4 flags (build/agent2/snap1-off compile_commands, 477
    entries; snap1 tree plus the snap1-sdk install, no PCH flags), 1 thread, BelowNormal.
  - The control native_lock_elide.cpp exits 0 (34.0 s, 1 getenv warning). The TU exits 0 with the define (39.4 s)
    and without it (13.2 s), with 3 getenv warnings each and no other diagnostic.
  - -E: with the define, sub_83FAF180, sub_83FB09E8, sub_83FBF7D0 and sub_83FC0C10; without it, sub_83FAF180 and
    sub_83FBF7D0. Lint was skipped (light-tasks window).
- expected-map.txt: PASS (devoff4 map DCC51E2B..., 13:30).
  - Today: 27 hooked aliases in 9 objects. The 4 targets are unhooked (sub_X at __imp__sub_X): H0 in recomp .248,
    H1 in .107, H2 in .422 and H3 in .232.
  - After S4c: those 4 sub_ publics move to gpu_wait_backoff.cpp.obj and their __imp__ stay put, 27 -> 31 (29
    without the define). The name sets don't change, and neither do the native maps.
  - Gate: the S4c devoff bin has exactly 4 more hooked aliases than S4b's.

### R2.22.4 Landing notes

- Both trees re-run CMake (7-25 s each). Devoff gets +1 TU and a relink. Native recompiles 3 TUs (R2.22.6 note 1).
- The native fingerprint's first input is CMakeLists.txt (:582-583, which becomes :604-605 after the edit), so S4c
  changes it once, as C1 does in S4b. For one native re-pin, run the native5 pin after S4c, or fold the diff into
  S4b's apply (no file overlap with C1/M1/P2c/r1r2/#26). This is open for Agent 1 (S4-DRAFT L100, L413).
- When copying new/ files, set their mtime to now (Agent 4's rule, 14:41). git apply and patch do that anyway.
- Before ON: b2r section 26 steps 1-4 (P1 controls > 0; the Q=250 vs OFF functional pair; the sweep; Agent 6's
  loaded arm with sleep_fail == 0).

### R2.22.5 Messages

- `@@to 10` (about 15:59): the package for rating, with the hashes, the apply check, the syntax result, the map
  expectation, the #30 note and the re-pin note.
- `@@done 22` went in the same reply.

### R2.22.6 Agent 10's rating (16:15, b2r row 38, S37)

- Landing OFF: SAFE for both s4c-24-30.diff (DC02104E...) and s4c-24-only.diff (A279DC71...). Nothing UNSAFE.
- What Agent 10 re-derived:
  - all 17 HASHES rows;
  - both diffs apply exactly (offsets 0) on 3690D5D7... in live, snap1, snapB and base/, giving new/ 1BF46D78... and
    new-24only 9A4606A7...;
  - the TU is the rated draft 01D9F8F3 (CRLF form 34D281E0..., 18,572 B);
  - the fallback is the primary without #30;
  - no staged S4 diff touches CMakeLists or the 4 hooks;
  - with the env vars unset, nothing is logged and every hook calls `__imp__`.
- Note 1 corrects R2.22.4 and PACKAGE.md ("Native: nothing new compiles"). The CMake edit changes the native
  fingerprint, so the fingerprint step rewrites `generated/native_gpu_build_info.h` (configure_file at CMakeLists
  :777-778, custom command :782-790). device.cpp, shader_archive.cpp and pipeline_library.cpp then recompile before
  the relink. PACKAGE.md stays as rated, because its files are released and it is a HASHES row; b2r row 38
  supersedes that line.
- Note 2: check the map by name and object. S4c's devoff map should have 4 more hooked aliases than S4b's, with each
  new `sub_` in gpu_wait_backoff.cpp.obj and each `__imp__` in the same recomp obj as in S4b's map. Don't check the
  0001: addresses or the .248/.107/.422/.232 numbers: those are devoff4's A-partition numbers, and B differs
  (sub_83FAF180 is TU383 there).
- Note 3: accept the TU as either 01D9F8F3 (LF) or 34D281E0 (CRLF).
- Note 4: re-pin native once, after the last fingerprint change. Three things change it: C1's memory_watch.cpp (S4b),
  this CMake edit, and #26's toml line if #26 goes ON. Agent 1 decides whether to re-pin after S4c or fold S4c into
  S4b.
- Before landing: grants, Agent 2's S4b-then-S4c build, the map check, then the re-pin. #30 ON can't be rated until
  the probe sources exist. #24 ON is still S26 items 4-6, measured apart from #26.
- Task #22 was marked done (files released) at 16:15. No reply was needed.

## R2.33 Task #33: Android feasibility (in progress, 17:08)

- Read-only task, still waiting for Agent 1's 'go' before the 3 research subagents. No tool calls while perf-notes/WINDOW-HOLD.txt exists.
- Working state and the new path:line findings: build/agent9/android/STATUS.md.
- Prompts: build/agent9/android/prompts.md.
- Report: perf-notes/ANDROID-FEASIBILITY.md. It is still the v0 skeleton; v1 is next.


## R2.18: task #18, the CG26 check kit and the #21 pre-read (run 2, 22:04-)

> **RESUME (23:12):** #18 is done (`@@done 18` sent about 23:13). Done: the kit and its tests, the README, the messages
> to Agents 2, 10 and 1 (the 23:13 command correction went to Agents 2 and 10), and the #21 pre-read (R2.18.4).
> Open: nothing. Monday: Agent 2 runs the kit after the CG26 regen. Answer any questions from Agents 2 and 10.
> Rules: read-only, no builds, regens, game runs or git writes. Check `perf-notes/WINDOW-HOLD.txt` before every command.
> Stop at 23:50, or as soon as HOLD appears, and continue in the morning. At most 1 subagent (none used).
> Mine: `build/agent9/**` and this file.

**Task (Agent 1, 22:04):** W10 readiness. Build a read-only check kit for Agent 2's CG26 bin (#26 `db16cyc_pause` ON,
arm A), so that Agent 10's static gates for #26 (b2r row 37, S36) take minutes once CG26 is built. Test it without a
regen, including a failing case. Then pre-read #21 (S4-T1) when Agent 7 sends the staged diff.

### R2.18.1 The kit: `build/agent9/cg26-check/`

- `cg26_check.py` (sha256 `DDBA731CC22D74BD` since 22:53, after the ADVICE text fix; runs 1-2 tested `A179EB13`, see
  R2.18.3). Stdlib only, one thread. It reads `--gen`/`--ref` (~1 GB) and writes
  only `--out` (`report.txt`, `diff-summary.md`, `sites.tsv`).
  - Exit codes: 0 PASS, 1 FAIL, 2 INCOMPLETE (no `--tool`/`--bin`) or a usage error, 3 HELD. HELD means the stop file
    exists or appeared: `--hold`, default `perf-notes/WINDOW-HOLD.txt`, checked on every file read and every MiB
    hashed.
  - The gates (a)-(d) are as in the task. The README lists each check.
- `test_cg26_check.py` (sha256 `40339E0287095AD4`): a mock regen (the pinned A tree plus the 20 pause lines, mock
  stamps, the staged new-A toml and a mock bin), 14 cases, HOLD-aware and resumable (`--reuse-mock --only`).
- `README.md`: the one-line command for CG26 and the test table.
- **The command for Agent 10** (after Agent 2's regen, recompile, relink and staging). Run it on one line from the
  workspace root, after the HOLD check in the README:
  `(Get-Process -Id $PID).PriorityClass = 'BelowNormal'; python build\agent9\cg26-check\cg26_check.py --arm A
  --gen build\agent2\cg26\DimensionsRecomp\rexlego\generated --ref build\agent2\snap1\DimensionsRecomp\rexlego\generated
  --config build\agent2\cg26\DimensionsRecomp\rexlego\legodimensions_config.toml --tool build\agent2\cg26\tool\rexglue.exe
  --tool-sha 9145166CDBEF5500E6E2607ED80AA6FC94CA1772DE2D3E87FF9E13BEAD87D586 --bin build\agent2\devoff4b-cg26-bin
  --out build\agent10\cg26-check; "exit $LASTEXITCODE"`.
  - 22:55 correction: the first version wrapped python in `cmd /c start "" /belownormal /wait /b`. That form always
    reports exit 0 (a `sys.exit(3)` probe gave 0, while the BelowNormal shell gives 3 and python still inherits
    0x4000). The corrected command went to Agents 2 and 10.
- **Tool markers:** `build/agent2/cg26/tool/rexglue.exe` (`9145166CDBEF5500`) contains both `db16cyc_pause` and
  `\tsimde_mm_pause();`. The old tool `build/agent9/bin/rexglue.exe` (`37B32713B7516402`) contains neither.

### R2.18.2 Agent 2's inputs

- **22:15, from me to Agent 2:** a bug in `build/agent2/cg26/cg26-check.py:76-86`. `codegen.build.stamp` holds the
  32-hex fingerprint of `codegen.stamp`, not a path:
  - snap1 `58c23c7e…`, gen-noflag `13d2065a…`, snapB `bc4c7504…`, each the same in both files;
  - so their "differs by the tree path only" check would have failed a correct regen.
- **22:28, Agent 2's fix:**
  - it now requires build stamp == the fingerprint, a changed fingerprint and the same outputs list (883);
  - self-test: `cg26/checks/selftest-stampfix.txt`.
- **22:28, Agent 2's answers:**
  - the ON bin is `build/agent2/devoff4b-cg26-bin`, with no control bin;
  - the control is the relink `cg26/link-ctl` (the 10 pinned TUs from `cg26/tu-ctl`, compared with snap1-off's exe and
    map), kept as evidence only. My kit does not cover it;
  - the MANIFEST comes from `stage-variant.py`: `#` lines, then rows `name<TAB>size<TAB>mtime<TAB>sha256<TAB>source`,
    then `# checks:` lines. My parser takes this format as is;
  - the build is a relink, not a full build: `recompile.py` builds `cg26/tu/*.cpp` with snap1-off's
    compile_commands.json, then `relink.py --ninja snap1-off/build.ninja --replace-file cg26/replace-on.txt`;
  - the base is devoff4b-bin: 5 files with mtime = now, and the exe and map replaced.
- **Agent 2's question (regen wall time), answered from `build/agent9/logs/gen-steps.txt`:**
  - full A-tree regens with the old tool, 886 files, 467 MB: off 118.8 s, off2 117.1 s, off3 101.2 s, off4 73.5 s;
    cpu ≈ wall (one thread);
  - rb2-nomusttail: the tool says "Done in 80.8s" (`gen-rb2-nomusttail.log`);
  - `build/agent2/codegen-steps.txt` has 129.8 s for 883 files;
  - gen-noflag itself is Agent 2's tree, not one of my runs.
- **22:47, Agent 2's plan:**
  - CG26 runs after tonight's windows: Agent 3's two L-route rows first, then CTR, then CG26.
  - Agent 2 runs the kit with `--out build\agent2\cg26\checks\kit18`; Agent 10 runs their own copy.
  - The regen uses cg26's toml (`11707872…`, `db16cyc_pause = true` on line 24).
  - `build/agent2/cg26/stage-cg26.py`, a stage-variant.py wrapper, writes `#` notes with the full uppercase sha256 of the
    tool, the toml and the 10 regen TUs (:41-58). It refuses if a cg26/tu copy differs from the regen TU. So my (a)
    NOTE (full hash or 16-hex prefix, any case) should read yes / yes / 10/10.
  - I said to prefer deleting codegen.stamp over `--ignore-stamp`: stale stamps would give 3 false FAILs in (a).

### R2.18.3 Tests (no regen, build or game run)

- **Run 1** (22:26, checker `E246936B51EB7C6A`), case by case:

| Case | Result | Time | Failing gates | Notes |
|---|---|---|---|---|
| P0 | OK, PASS | 144.6 s, cold | none | |
| F1 | OK, FAIL (16) | 9.2 s | ab | Agent 2's real pre-regen tree. Its codegen.d names snap1's base-A toml `7F775847`. Fingerprint `58c23c7e` == ref. Stamp 11-21 18:15:54 is older than the toml (20:54:29). 0 of 20 pauses. nativeB-bin MANIFEST: (d) PASS. |
| F2 | OK, FAIL (5) | | ab | |
| F3 | OK, FAIL (7) | | abc | TU108:201 in sub_8263D000 |
| F4 | BAD | | ab, want b | Test artifact: the mutation gave TU125 a new mtime, so the "exe newer than the regen" check in (a) failed too. Fix: mutations now keep the file's mtime. |
| F5 | OK, FAIL (3) | | c | partition `6E8EEADC` vs `22C9D89B` |

  Run 1 was stopped during F6 at 22:34. Then:
  - the test was made HOLD-aware (it kills the checker within 1 s of HOLD and restores the mutation);
  - the checker got `--hold`;
  - an H1 case was added (stop file, exit 3);
  - a MANIFEST `source` NOTE was added for the exe and the map.
- **Run 2** (22:37-22:40, checker `A179EB13`, test `40339E02`): mock built in 68.0 s. **ALL OK, 14 of 14.** Log
  `build/agent9/cg26-check/test-20261122-223737.txt`, with per-case reports in `test-20261122-223737/<id>/`:

| Case | Result | Time | Failing gates | Notes |
|---|---|---|---|---|
| P0 | OK, PASS | 15.1 s | none | |
| F1 | OK, FAIL (16) | 7.3 s | ab | Same facts as in run 1. |
| F2 | OK, FAIL (4) | 7.0 s | ab | 19 of 20. sub_83F99F80 has 1 (want 2). |
| F3 | OK, FAIL (7) | 5.9 s | abc | TU108:201 in sub_8263D000 |
| F4 | OK, FAIL (2) | 5.3 s | b | TU125:33896 is not right after its db16cyc line. |
| F5 | OK, FAIL (3) | 4.9 s | c | partition `6E8EEADC` vs `22C9D89B` |
| F6 | OK, FAIL (1) | 3.7 s | d | exe `7E4B6932` vs MANIFEST `DE067EDD` |
| F7 | OK, FAIL (1) | 4.0 s | a | Old tool `37B32713`: neither option string. |
| F8 | OK, FAIL (2) | 3.1 s | a | 0 `db16cyc_pause` lines, and codegen.d names another toml. |
| F9 | OK, FAIL (1) | 2.9 s | a | Stamp 21:28:43 is older than the toml (22:28:43). |
| F10 | OK, FAIL (1) | 2.3 s | b | TU205: first other difference at line 20. |
| F11 | OK, FAIL (1) | 3.4 s | a | Build stamp `0123…` != fingerprint `b3bccb3c…` |
| I1 | OK, INCOMPLETE (2 skipped) | 2.8 s | none | exit 2 |
| H1 | OK, HELD | 0.2 s | none | exit 3, no report |

  After run 2, `mock/` (893 files, 467 MB) was deleted at 22:41. The test rebuilds it in about 70 s.
- **22:53, the ADVICE text fix (from Agent 2's note):**
  - The checker's ADVICE NOTE (cg26_check.py:521-524) and README L58-62 now say to delete
    `generated/default/codegen.stamp` (or pass `--ignore-stamp`).
  - Touching the toml does not force a regen. The SDK fingerprint hashes input contents, not mtimes
    (output_stamp.cpp:67-99).
  - New checker sha256: `DDBA731CC22D74BD`.
  - Checked on the F1 inputs (Agent 2's real pre-regen tree): FAIL (16), with the new text
    (`build/agent9/cg26-check/verify-advice-2253/`).
- **22:55, the command fix:** on the same inputs, the BelowNormal-shell form gives exit 1
  (`build/agent9/cg26-check/verify-cmd-2255/`). The old `cmd /c start` form printed exit 0.

### R2.18.4 The #21 (S4-T1) pre-read: `build/agent9/s4-t1-preread.md` (23:10)

- **Scope:** an independent read of Agent 7's rev-2 staging (diff `46FFD2E9`, +51/-0).
  - Re-hashed at 23:02: before/ = snap1 = live for all 3 files.
  - after/ matches SHA256SUMS.txt.
- **All 4 checks PASS:**
  - The OFF path is unchanged. When the variable is unset there is no Win32 call and no log (nw:340, :346), and n0 never
    calls the hook.
  - The priority is set and undone. Each thread changes only itself through its pseudo-handle, and the setting ends when
    the thread is joined.
  - The change is native-only: gpu_native files only, no CMake change. The fingerprint re-pin is expected.
  - There are no new lock edges. No lock is held at any hook, and the impl takes only leaf locks.
- **Notes, none blocking:**
  - P1: mixed line numbering in RATE-REQUEST, DIFF-REVIEW, FUNCTIONAL-ROWS and the matrix.
  - P2: the fingerprint keys the recipe/seed files and the shader pack. The caches are per exe dir, so there is no
    cross-bin rejection. Under `-NoCold`, r1 of each bin dir is cold: n0 r1 and th3old r1 are cold, th3 r1 is warm.
  - P3: I agree with RATE-REQUEST §10 risks 1-2.
  - P4: the getenv runs on the first chain thread.
  - P5: N3 can't be closed from snap1-off. It is a native-off build, with 0 gpu_native entries.
- **Citations:** `build/agent9/s4-t1-preread-cites.ps1` checked 144 citations, 0 bad (23:10).

### Side note (22:42): Agent 3's s4b17, the P1 run that sizes #24's S and Q (S5.2.4 step 1)

- **Setup:** back-off OFF, stats ON, attract-long, under a `-j 8` build. JSON: `build/agent3/s4b/logs/s4b17.gw.json`. Run:
  `build/agent3/runs/20261122-223103-s4b-17-gw-p1`.
- **L1:** 21926 waits.
  - Histogram: < 50 us 6983, < 200 us 5, < 1 ms 46, < 4 ms 395, >= 4 ms 14497.
  - Total 314.5 s over 81 × 5 s (405 s), max 663 ms.
- **L2:** 21524 tries, 23 waits, 2.75 s, max 1077 ms. 87247 kicks. sleep_fail 0.
- **My read (sent to Agent 3):**
  - L1 is bimodal: 32% of waits are under 50 us, 66% are 4 ms or more, and only 51 fall between 50 us and 1 ms.
  - S (LEGO_GPU_WAIT_SPIN_US, 30) already sits at the short mode. 50 would cover all of it, for about 20 us × 14497
    ≈ 0.3 s of extra spin per 405 s.
  - The long waits average about 21.6 ms ((314.5 s minus at most 2 s of shorter waits) / 14497). So the extra wake-up
    lag of Q = 125-500 us is about 0.3-1.2% of a mean long wait, and at most about 12% of a 4 ms wait.
  - Step 3's sweep on a quiet machine still picks Q. This run was under load, which inflates the waits.
