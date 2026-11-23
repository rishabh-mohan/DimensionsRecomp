# 1b (b): guest clocks behind the front-end exit (Agent 9, task #32, 07:20)

The analysis is static and covers the A tree only (codegen snap1 = the pin):
`baseline/DimensionsRecomp/rexlego/generated/default/legodimensions_recomp.N.cpp`.
- "TUn:line" means file N, at the function's first line or at the named site.
- Tools (copies in this folder):
  - `s6_clock_scan.py`: 438 TUs, 16.86M lines, 164,786 functions, 40 s; report `s6-clock-report.txt`.
  - `fq.py`: an index of calls, callers and global readers/writers. `python fq.py build` rebuilds the index
    `s6-funcs.pkl` (about 40 s; not copied). `python fq.py show sub_X` prints the guest asm.
- **Not followed:** vtable calls and event delivery. "No static callers" means the function is called through a
  vtable.

## 1. Time sources (library code, 0x83E9xxxx-0x83FDxxxx)

| Function | TU:line | What |
|---|---|---|
| sub_83F9EA20 | 422:37024 | QueryPerformanceCounter (2 mftb) |
| sub_83F9E9E8 | 213:35107 | KeQueryPerformanceFrequency |
| sub_83F9EAE0 | 246:35721 | KeQuerySystemTime |
| sub_83F9F1D8 | 106:35409 | KeQuerySystemTime |
| sub_83F9E198 | 86:36115 | KeDelayExecutionThread |
| sub_83F9E228 | 129:35869 | Sleep (63 callers) |
| sub_83FAF088 | 53:34710 | D3D wait context: stores mftb |
| sub_83FAF0B8 | 413:35532 | D3D wait stats: elapsed mftb |
| sub_83FB2640 | 53:34738 | D3D, mftb |
| sub_83FBF7D0 | 248:35181 | GPU fence wait (S4.1); its mftb is for stats only |

More D3D/XAudio mftb readers (rows in `s6-clock-report.txt`): sub_83FB2510, sub_83FC4748, sub_83FC7858,
sub_83E96140, sub_83E96348, sub_83E969C0, sub_83E97308, sub_83E97420.

## 2. Game clock (NuTime-like), globals 0x848D65EC-0x848D6600

- **Init once:** sub_82A2A2B8 TU107:5507.
  - flag 0x848D65EC;
  - start QPC 0x848D65F0 (64-bit);
  - freq 0x848D65F8;
  - ticks per us 0x848D6600 (freq / 1e6).
- **get:** sub_82A333B8 TU17:5491, (QPC - start) -> [r3]. 111 callers.
- **diff:** sub_82A336A8 TU369:5461. 46 callers.
- **ticks -> seconds (float):** sub_82A334D0 TU110:5538. 38 callers.
- **Timer object** {+8/+12 accumulated ticks, +16 limit (float s), +20 running byte}:
  - sub_82A786D0 TU84:5988, "expired?" = elapsed > limit. 25 callers, 18 of them FE (section 4).
  - sub_82A78668 TU391:6088 stop.
  - sub_82A78620 TU328:5852, probably start.
- **Profiler scopes:** instrumentation only; they don't feed game logic.
  - sub_82A3E238 TU360:5561 begin(id); sub_82A3E2B8 TU217:5706 end(id).
  - Depth is at 0x848D6EC8; the 28-byte entries start at 0x848D7168.
  - The FE per-frame uses id 30.

## 3. Frame dt

- **App object:** its pointer is at 0x849F5E8C. ctor sub_82FF72A0 TU324:13316; field init sub_82FF68E8 TU246:13662.
- **sub_82FEB7B8** TU59:13665 is the main/app update; its caller is sub_82984F80 TU265:4435.
  - At 0x82FEBE18-0x82FEBE30 (TU59:14600-14620) it copies:
    - app+1352 -> +2212 (dt, float s; the store is at TU59:14612);
    - app+1344 -> +2216;
    - [0x82005CD4] / dt -> +2224 (1/dt).
  - Just before that, it increments a per-update counter, [r24+736].
- app+2288 is the paused byte, set by sub_82FE08C8 TU246:13283.
- **Not identified:** the writer of app+1352. The tree has 78 stores at offset 1344/1352 on other bases.

## 4. Front-end

- **FE per-frame:** sub_82FEA350 TU349:13670 (vtable; no static callers). In order:
  1. ProfBegin(30).
  2. If [r30+192]: sub_82FB77E8([0x849F55EC]) + sub_82FD8DD8.
  3. sub_82FBE2A8([0x849F55EC], dt = [r4+20]).
  4. sub_82FE7B90([0x849F5620]).
  5. If FEmgr+172 != -1: request_page sub_82FD8C30 TU326:13568 (FEmgr, page), then +172 = -1.
  6. If +184 == [0x849F562C]: [+152][+168] -> [0x849F562C]+176.
  7. sub_82FE3780; ProfEnd(30).
- **Page timeout timer:** 0x849F5F84 (armed byte), 0x849F5F88 (elapsed float), 0x849F5F8C (limit float).
  - **Arm:** sub_82FD4868 TU293:12534, at 0x82FD4A04-0x82FD4A2C.
    - If sub_82FB9020 TU335:12774 returns true: sub_82FBDFF8 TU432:13441 ([0x849F562C], text, 2, 0); armed = 1;
      elapsed = [0x82005CD0] (probably 0.0); limit = [0x847D4A78] (value not read).
    - Otherwise: sub_82FBDFF8(..., 0, 1), and no timer.
    - It also sets the page id [r30+24] to 47, 17 or 54.
  - **Tick:** sub_82FE70C0 TU107:13872 (event handler, vtable), event 5.
    - If not paused (app+2288) and armed: elapsed += [[ev+16]+20] (dt).
    - If elapsed > limit: armed = 0, then a tail call to sub_82FE6F98.
  - **Fire:** sub_82FE6F98 TU305:12975.
    - If page [r3+24] == 47 and [0x848E1E8C]->vf40(): FEmgr [0x849F5640]+172 = 56 (the next frame's request_page).
    - Otherwise: +168 = 56 and +184 = [p140+224].
    - Its other caller is sub_82FEB4A8 TU52:13234.
  - **Cancel:** sub_82FB90B8 TU415:12960, on message 0x849F6F3C.
  - **So this timer is a dt sum, gated by pause.** At a steady fps it behaves like wall time.
- **Loading indicator,** object [0x849F55EC]:
  - ctor sub_82FC2F78 TU87:13707. It registers handlers for message 0x849F6F3C and 2 others.
  - update sub_82FBE2A8 TU359:13397: idle +104 += dt while hidden; QPC timer at +68. It also calls sub_82A786D0.
  - "shown?" sub_82FB7850 TU383:13107.
  - Animations sub_82FB78F0 TU142:12934 and sub_82FB7A30 TU190:12688 read the app dt +2212.
  - Global readers of 0x849F55EC (`fq-readers-55EC.txt`): sub_82856308, sub_82A04408, sub_82FB78E0, sub_82FBDCB0,
    sub_82FBF6C8, sub_82FC1130, sub_82FC12B8, sub_82FDB800, sub_82FE3CE8, sub_82FEA350. None of them reads
    +104 of the indicator.
- **Delayed-event queue:** sub_82FD5920 TU120:13174 (20 callers, including request_page).
- **The 18 FE callers of "expired?" sub_82A786D0:**
  - sub_82EF8AF8 TU310, sub_82F0E850 TU260, sub_82FBE2A8 TU359, sub_82FBEA60 TU411, sub_82FBF0D0 TU230,
    sub_82FBF890 TU145;
  - sub_82FCD2D0 TU392, sub_82FD4D88 TU181, sub_82FD9708 TU159, sub_82FDDC60 TU82, sub_82FE18C0 TU11,
    sub_82FE2B68 TU138;
  - sub_82FE6038 TU233, sub_82FE63E0 TU194, sub_82FE6BA8 TU111, sub_82FEABF0 TU91, sub_82FEB330 TU415,
    sub_82FED2B8 TU344.
  - Non-FE callers: sub_82A7B5F8, sub_82A7F5A0, sub_82A7FD28, sub_82A95E98, sub_82AAA6E8, sub_82AE2208, sub_838BFD58.
- **FE dt readers with fcmp + fadd:** sub_82F9B9F0 TU213:13106, sub_82FE9298 TU422:13847, sub_82FEB7B8.

## 5. Reading, and (a)

- **Every FE clock found is a pause-gated dt sum or a QPC difference.** At equal fps neither runs faster on a faster
  guest CPU by itself. The fps was equal: nativeB 97/110, native3d 105/103.
- **Agent 3's constraint** (`build/agent3/logs/fe-native-cb.txt`):
  - the first frame and the A1 response match;
  - then nativeB exits 11.6 s earlier: 49.70 vs 61.34 s after A1, 5446 vs 6298 frames.
  - So the trigger's clock follows guest CPU speed, about 23-28 % faster.
  - My CPU totals agree: native3d 132/144 s vs nativeB 100/113 s, a ratio of about 1.29.
- **What fits:** background guest work (streaming, the INSTALL batch, attract preload) that has to finish before a
  timer is armed or a page change is accepted. Static analysis can't confirm this, because it can't follow vtables or
  event delivery.
- **B can't change semantics, by construction:**
  - mftb becomes an out-of-line `Clock::QueryGuestTickCount` (A pch:293, B pch:297);
  - REX_LOAD/STORE are volatile in both pch files (127-137);
  - B adds only CTR/XER/RESERVED/CR locals;
  - musttail only turns call + return into a jump;
  - ctx.lr is kept.
- **Recommendation: (a).**
- **For Agent 10's snap1 vs B3 diff,** these are the functions to check:
  - sub_82FD4868, sub_82FE70C0, sub_82FE6F98, sub_82FB90B8, sub_82FB9020;
  - sub_82FEA350, sub_82FBE2A8, sub_82FEB7B8 (the dt copy);
  - sub_82A786D0, sub_82A333B8, sub_82A334D0.
  - Look for an mftb read kept in a local, or a flag or poll value kept in a local across a call or loop iteration.

## 6. HighResolutionTimer check (Agent 10's item): drop it

The scan was `s5_src_scan.py` (1225 files, 1.0 s; report `s5-src-report.txt`). It covered SDK include/ (339 files),
src/ (606) and tests/ (20), plus rexlego/src (259). There is no rexlego include/ tree.
- **include/:**
  - the only definition is the inline class at `include/rex/thread.h:150-177` (comment at 150, class at 152,
    `CreateRepeating` at 169). S4.1.2 said 147-173.
  - The only other reference is the member `timestamp_timer_` at `include/rex/kernel/xboxkrnl/module.h:42`.
  - `include/rex/thread/timer_queue.h:20-76` declares QueueTimerOnce and QueueTimerRecurring.
- **src/:**
  - the only `CreateRepeating` call is `src/kernel/xboxkrnl/xboxkrnl_module.cpp:195`, the KeTimeStampBundle 1 ms
    tick. Its callback (:184-199) stores `QueryGuestUptimeMillis()` into bundle+16. The value is computed, not
    counted, so it can't drift.
  - Other TimerQueue users: `src/core/threading_posix.cpp` (built for UNIX only) and the implementation,
    `src/core/timer_queue.cpp`.
- **tests/ and rexlego:** 0 hits.
- **Related:**
  - the cvar `host_timer_resolution_ms` is defined at `src/system/runtime.cpp:39` (default 0);
    `host_timer_throttling_optout` is at :42.
  - It is wired at runtime.cpp:142-143 into `timing.timer_resolution_ms` (`include/rex/threading_timing.h:20`), and
    used at `src/core/threading_win.cpp:235`.
  - `REX_TIMER_WAIT_BLOCKING` is read at `src/core/timer_queue.cpp:42`.
