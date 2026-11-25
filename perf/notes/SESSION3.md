# SESSION 3 log (resumed 2026-11-25)

Overseer = grid Agent 4 (acts as old orchestrator Agent 1). Managers M2-M12 = successors of old
Agents 2-12 (subagents). Common brief: `build/agent1/session3/BRIEF-COMMON.md`.

## 11-25 01:15 restart checks (Overseer)

- Both repos on `perf/opt`, equal to `mine/perf/opt` by `git ls-remote`: game c9e215f, SDK 5350b1d.
  `git status`: only ` m rexglue-sdk` and ` M thirdparty/plume` (expected). PASS.
- The user is playing Minecraft (Bedrock) at the visible desktop: no timed windows; machine-load
  policy HOLD (no builds/game runs) until the user OKs load.
- Bins MANIFEST, SCRNSAVE hashes, native pin: delegated to M12 (S3T-1).

## 11-25 01:16 native4b pin announcement (RESUME section 7 step 2, step 5 of the re-pin)

Re-pin steps 0-4 passed (`build/agent4/repin/pin-native4b-2243.txt`, rpb0, rpm4). Announced: the
current native pin is now **native4b, fingerprint 9b40acbbef4c57b3** (was native4 5e3ff55de10f4f64),
pending M12's restart check that `build/agent2/native4b-bin/MANIFEST.txt` is unchanged. M4 then fixes
`build/agent4/repin/repin_check.ps1` in the order of `build/agent4/HANDOFF.md` L29-32.

## 11-25 01:26 user decisions; manager status

- Load policy (user, 01:26): low-priority builds OK (max 2 threads, Idle priority, M2 only, one at
  a time); **no game runs** while the user plays. LOAD GO (builds only) sent to M2.
- agy-grid caps the Overseer at 6 direct reports; user chose to queue M8-M12 as slots free.
  Started: M2, M3, M4, M5, M6, M7 (01:16); M10, M12 (01:26, after M4/M5 finished). Queued: M8, M9, M11.
- M5 S3T-5 done (01:22): all 12 launcher/day-draft hashes match; screensaver registry sane
  (SCRNSAVE.EXE = '' present). N6 is read-out side (note for M12:
  `build/agent5/session3/N6-NOTE-M12.md`). test-day dry-only subset 20/20
  (`summary-s3dry-012200.txt`); the full set wasn't re-run because 3 cases start the real launcher.
  Install script ready, not run: `build/agent5/session3/install-day.ps1` (B79061A2), waits for M11's
  rating. RUN-DAY needs the user away ~1.5-2 h per 13-run window.
- M4 S3T-4 done (01:25): `repin_check.ps1` fixed in HANDOFF order (81BE81D8 -> 4B29240C; backup in
  `repin/superseded/`); dry runs 0 FAIL / 0 WARN on snap1 and native4b-bin. Screenshot kit valid for
  native4b. **Correction:** `LEGO_DUMP_MISSING_SHADERS` is the dump root dir, not a flag
  (shaders.cpp L562-597); the plan in `build/agent4/PLAN-S3T4.md` sets an absolute path. Dump waits
  for RUN GO. Next pin (native4bp) must change the pack-state rule before adding to `$PINS`.

## 11-25 01:28 M7, M12 reports

- M7 S3T-7 done: #19 unchanged and applies to SDK 5350b1d (`build/agent7/session3/check-19-5350.out.txt`).
  Caveats relayed to M10/M2: the `--directory=games/lego-dimensions-recomp/...` apply form is stale
  (the WS is no longer inside a git repo); use `git -c core.autocrlf=false apply` on non-repo trees.
  Soak checker written (`build/agent7/s4-r1s2/soak-check/soak_check.py` CAB5CB2C, 26/26 self-test).
  #21 W1 matrix written (`build/agent7/s4-t1/matrix-s4t1-w1.json` 269E1DBC); threaded-proof TODO in
  `build/agent7/s4-t1/THREADED-PROOFS-TODO.md` (MP2/MP3 scripts not written yet). M7 closed to free
  a slot; restart it for MP2/MP3 or #19 questions.
- M12 S3T-1 PASS: all 13 bins' MANIFESTs re-hash clean (0 mismatch, 0 missing); native4b exe
  DC6484C2 contains fingerprint 9b40acbbef4c57b3. **The native4b pin stands.**
- M11 started (day-draft rating).

## 11-25 01:35 the user left the PC for the night (Minecraft closed)

- Plan: M3's functional rows first (s4bQ5 during the CG26 build; then quiet rows s4bN16, s4b07r +
  s4bV0, s4bLV, f10a3 + f10b3, maybe f10aL/bL; hard stop for new rows 04:15). Then timed windows
  through the night launcher: confirmation window pass 1, W8a, (W10 if rated), pass 2. No window
  after 06:45.
- ready-N: option C (s4bN16 measures K and KiB per list on the title scene).
- M2: CG26 bin staged 01:36, `build/agent2/devoff4b-cg26-bin` (MANIFEST 917AE86E), kit18 static
  PASS. CTR got only its 2 single-TU recompiles (before the stop); no more builds tonight. Morning
  queue: CTR relink, #33 no-hunk-5, devoff4bv, #19. M2 closed to free a slot
  (`build/agent2/session3/BUILD-PLANS.md`).
- M12 S3T-12: C1 verify-only fix staged (`build/agent12/session3/c1-verify-fix/`, diff 66B9254E),
  gate checklist (`GATE-CHECKLIST.md` 99938113); N6 fix OK'd for install into w6-gates.
- 01:37:06 night launcher started on the user's desktop via agy-grid desktop.js (pid 38660): REAL,
  WinSta0\Default, AC, ends 07:30, latest window 06:45, keep-awake ON, 19 files pinned.
- `build/agent1/night/pre-go.ps1` now takes any `W*` window id and `-Latest HH:mm`.
- M10 queue: #19, then #26 CG26 (for W10 tonight), then the C1 verify fix.

## 11-25 01:40 #19 rated (M10, `build/agent10/session3/r19-rating.md` 296658C5)

- (a) build into devoff4b default-off: SAFE (needs a FULL SDK rebuild, <= 2 threads, M2; syntax
  check, before-hash check, copy new/sdk/; MANIFEST + bincheck 3 needles; row a first).
- (b) ON in rows/soak/W7: SAFE-IF 6 conditions (stop at first FAIL; a, b, i before any ON row;
  order a,b,i,c,g,j,d,f,e then W7; any hang = FAIL, triage from GPU Commands / D3D12 Submit stacks;
  no combination with #33 ON, CTR, native or res scaling without re-rate; N only from ready-N).
- (c) ACCEPTED; no BLOCKER; SHOULDs S1 (row g earlier), S2 (combination guard); 8 NITs. F-CA does
  not apply (native-only).
- #19 build goes into the morning build queue. M10 now rates #26 CG26, then the C1 verify fix.
- M12: N6 installed in `build/agent12/w6-gates/` (run_gates.py BD511202, selftest 54/54).

## 11-25 01:43 s4bQ5 PASS (M12) - q500's functional check is closed

- Run `build/agent3/runs/20261125-013748-s4b-Q5-gw-q500` (devoff4b, 213 s): exit 0, 0 STUCK-LOCK,
  1 init line (quantum 500, spin 30, stats ON), **41/41 stats lines with sleep_fail 0** (three
  independent checks). RESUME section 6 item 1's q500 condition holds.
- M9: CG26 bin statically ready for W10 (`build/agent9/session3/CG26-W10-REVIEW.md`); needs the
  untimed boot cg26b0 (added to M3's queue) and M10's sign-off; M8 drafts matrix-window10.json.

## 01:45-01:50
- M6 S3T-6 DONE (paper): `build/agent6/s33-popin/s33-popin-nohunk5.patch` 57CFA8AD (apply-check PASS vs 5350b1d), diag (d) patches (unrated), TESTPLAN.md 90DF23DE, logdiff kit w6_kit.py CD320502 (+watchdog note, harness mode). M6 killed to free a slot (work in files).
- Decision: diagnostic (d) goes in a separate bin `devoff4b-s33d-bin`; rows 1a/1b identity on the (d)-free bin.
- M10 rated #26 CG26 **SAFE-IF** for W10 (`build/agent10/session3/r26-cg26.md` 423FE10F): fixed bins s0=devoff4b (DE11A914)/cg26 (917AE86E), env {}, own caches (cg26 cold first), per-run functional check on each cg26 run, STUCK-LOCK per finding-10 rule per arm. Forwarded to M8. M10 queue: C1 verify fix -> #33 nohunk5 delta + (d).
- s4bQ5 gated PASS by M12. s4bN16 running (since 01:42:39).

## 01:47
- M10 rated C1 verify-only fix (`build/agent10/session3/c1-verify-fix-rating.md` AFBFFBDF): code **SAFE**; build devoff4bv **SAFE-IF** (M2, Idle, ≤2 threads, rexgpu-xenos target only; check before-hash A4A31038 first; build into a copy, never overwrite the shared snap1-sdk/install/bin/rexgpu-xenos.dll E3CB99CF; devoff4b/cg26/native4b MANIFESTs must still verify after staging); rows s4bV0f then s4b07f **SAFE-IF** (RUN GO, hidden desktop, launch-time cvars only, s4b_check.py needs s4b07f/s4bV0f branches + devoff4bv bin check — M3 edit, M10 to rate; positive controls per RATIONALE L102-105; "ships as p2fc" stands, no C1-without-P2 default without Overseer decision). Morning queue: M2 builds devoff4bv; M3 adds s4b_check branches (after tonight's rows).

## 01:48
- M8 staged 4 windows (stage-window.ps1 -Promote -VerifyFiles, PlanOnly OK, bin MANIFESTs 0 FAIL). GO files written + sha verified: `build/agent1/night/GO-WC1.txt` (matrix-windowC.json 00E3EE97, s0/win3/c1np/p2fc x4, 17 runs ~39 min), `GO-W8a.txt` (matrix-window8a.json A06E5E3A, n0/mc x7, 15 runs ~35 min), `GO-WC2.txt` (matrix-windowC2.json D0AE477F, reversed file order, ~39 min), `GO-W10.txt` (matrix-window10.json 289F4B4F, s0/cg26 x6, 13 runs ~30 min; deviation: launcher always passes -ColdShared, so cg26's round-1 run is its cold run; read-out reports round 1 separately).
- C read-out: round 1 = GPU warm-up, dropped; rounds 2-4 scored; WC1+WC2 pool to 6 scored runs per arm.
- Gates before WC1: functional PASS for win3 (never run as a full set) and c1np. Asked M3 to add rows win3f + c1npf after cg26b0, drop f10aL/f10bL, and report "M3 IDLE" (~03:30 expected) so the windows can start early.

## 01:48 (b)
- s4bN16 INCOMPLETE as a measurement (0 split counter lines: no submission reached 16 KiB on the title scene); functionally clean. Added s4bN4 (4 KB) at queue end; if 0 lines again -> fallback A (W7 title arms can't show #18).
- M9 S3T-9 DONE: Q=500 default-ON diff `build/agent9/session3/q500/q500-default.diff` 28F0D1DE (apply-check PASS, not compiled; env "off" = explicit OFF, safe on old bins); risks `RISKS-FOR-M10.md` (R1: env {} arms flip ON on new bins -> off arms must set LEGO_GPU_WAIT_BACKOFF_US=off). s4bQ5 sleep_fail own check PASS (mean 1.056 ms/sleep). M9 killed (work in files). M10 to rate the diff for the final build.

## 01:49
- **User (01:48): screenshot checks and visual decisions can be done through the Discord bot, without touching the PC.** So the screenshot check and the #33 eye review (row 3) no longer need the user at the desk: run them on the visible desktop while nobody is at the PC (like timed windows), capture screenshots/clips, and send them to the user via my replies for a verdict. Keep/drop decisions also by Discord.
- Added row cg26L (level-route functional on devoff4b-cg26-bin) after f10b3, since cg26b0 (menus route) can't show level reached.

## 01:51
- M11 S3T-11: day-draft launcher + installer **SAFE-IF** (`build/agent11/session3/day-draft-rating.md` 430E8049; run-day.ps1 differs from the running night launcher only in the 7 `# DAY:` lines; installer writes only `bench\agent5\day\`, refuses non-empty target; dry run REFUSED while night launcher runs, as designed). Install conditions: (1) after night launcher ended (state.txt `ended`, pid 38660 gone, plan check `checks OK` exit 0); (2) by hand: no legodimensions/build/test-day running; (3) `-Install -NoOptional`; (4) accept only exit 0 + all `target OK` + "night set unchanged", else delete only `bench\agent5\day\` and report; (5) day session only when the user confirms away for the whole session; only the Overseer writes GO. M11 killed (work in files). Plan: install after 07:30.

## 01:51 (b)
- M10 rated #33 nohunk5 (57CFA8AD) **SAFE** under r33 conditions and diag (d) (6CF9377E, separate bin devoff4b-s33d-bin) **SAFE** (`build/agent10/session3/r33-nohunk5-diagd.md` B24EE8E2). Build SAFE-IF: clean 5350b1d + exactly that bin's patch (build M6's 57CFA8AD, not M2's 4061ED2D; name it in MANIFEST); keep snap1-sdk/install/bin/rexgpu-xenos.dll E3CB99CF intact (devoff4b/cg26/native4b MANIFESTs verify after each build); needles: s33 DLL has d3d12_pipeline_creation_no_wait and NOT d3d12_resolve_after_drop_log, s33d has both; exe/rexruntime == devoff4b-bin; no cache/seeds. S1: #19, devoff4bv, s33, s33d all rebuild rexgpu-xenos -> one at a time, fresh tree each, before/after hashes in each MANIFEST. Rows 1a/1b first; stop if they fail. #19 S2 stands (no #33 ON + #19 ON without re-rating). Morning M2 queue: CTR relink/stage, devoff4bv, s33, s33d, #19.
- cg26b0 **PASS** (M12; run `20261125-014556-cg26b0-boot-menus`, logdiff vs s4b01 NEW/MORE/FLAG 0) with 1 coverage CHECK: menu path diverged after the 3rd A (cold first launch, first frame 9.1 s vs 4.5 s; time-based route). Decision: no repeat; cg26L (level route) closes r26 condition 4.
- 01:52 M3: queue now win3f (launched 01:50:03) -> c1npf -> s4b07r -> s4bV0 -> s4bLV -> f10a3 -> f10b3 -> cg26L -> s4bN4; projected IDLE ~03:43. cvars/env for win3f/c1npf generated from matrix-windowC.json by script; new `build/agent3/session3/wc_proof.py` (DDDEFD75) checks the matrix proof lines. M12 already has the ids.
- 01:54 M10 rated q500 default-ON (`build/agent10/session3/q500-default-rating.md` DB5D1282): code SAFE; default ON in final build SAFE-IF 5 conds (all step-B gates incl. level frame-time tails; time the shipped combo if CG26/d11p ship; land late, OFF-needing bins get -DLEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1 in MANIFEST; harness first: new-bin off arms set `off`, stage/GO checks refuse missing key; clang -fsyntax-only + real build, marker literal, native fingerprint unchanged). S1: `off` is NOT gate-clean on old bins (WARN line) -> old-bin arms keep env {}. S2: document `off` in release notes or land a cvar follow-up.
- 01:57 M3: win3f PASS (run `20261125-015006-win3f-level`, exit 0, 425 s, level reached, STUCK-LOCK 0, wc_proof 14/14, s4b_check vs s4bL0 NEW/MORE 0, f10_rule PASS). Awaiting M12's gate. TimerQueue <15 % not checked here (WC1 sys_csv will show it).
- 01:58 M10 reviewed M3's read-out tools (`build/agent10/session3/m3-readout-review.md` D7806C9E): SAFE tonight; S1 s4bV0 must require c1_verify_on==1; S2 f10_rule "self-recovers" too loose (needs route mark/frames advancing); S3 wc_proof needs exe-hash bin identity. Sent fixes to M3, hand-check rules to M12.
- 01:59 M12: **win3f PASS** (gates WC1; exe DFBE1D43, cvars/env == matrix win3 arm, all 4 proof lines x1, K0/F0, 0 STUCK-LOCK, logdiff NEW 0 beyond expected). c1npf pending.
- 02:04 M3 landed M10's fixes (backups *.bak-0158): s4b_check B8014B04 (s4bV0 needs verify_on, N in split init line), f10_rule F6B47350 (recovery = perf.csv growth over a >=10 s input step pair, else FAIL), wc_proof 6CFD8F3D (exe-hash bin identity; c1np/cg26 forbid Host-timer line), postcheck 03822B00 (wc_proof wired). Re-runs: win3f PASS 15/15, cg26b0 PASS 10/10. Re-test side effect: old w6gA now FAIL (548 s event, no step pair after) -> M12 hand-checking (artifact vs real stall; w6gA backs p2fc).
- 02:05 **c1npf PASS** (M3 + M12; exe DFBE1D43, cvars == matrix c1np, keep-watch x1, no verify/timer/precise/back-off lines, 0 STUCK-LOCK). **Both WC1 gate rows PASS -> WC1 eligible** once M3 is idle. s4b07r launched 02:04:36.
- 02:07 M12: w6gA = TOOL ARTIFACT (route stuck in a wait_log from 372 s; frames kept advancing after the 548 s event). p2fc backing stands. s4b20/w6gB slow recovery = the known finding-10 ramp. Asked M3 for an f10_rule follow-up (frames advancing counts as recovery inside a wait_log).
- 02:07 M8 item 4 staged (not installed) in `build/agent8/session3/staged/`: run-matrix.ps1 72370A1E (warmup_runs, kind/over8/over10/over16_7 columns; run loop untested), frame_summary.py 987E0EC0, sampler LdSys.cs/sys-csv.ps1/sys_summary.py (nongame_cores, disk, top procs; nongame_load INFO flag). Install only with no launcher pinned, then restage windows. Sent to M10 for rating. M8 quiet during windows.
- 02:10 M3: f10_rule D049928C (perf.csv frame fallback inside wait_log; recovered = >=10 s of frames after the stall frame with >= max(2, half pre-event pace)). Re-tests unchanged; w6gA event now finding 10 (recovered); w6gA stays FAIL only on the known level=False (route timed out). No --no-level re-judge needed.
- 02:13 M10 rated M8's runner improvements SAFE-IF for an off-night install (`build/agent10/session3/m8-runner-rating.md` C08604D8): install with no launcher running, re-check base hashes, 3 sampler files in one step, restage windows; patch selftest header; never mix warm/no-warm or pre/post-install sys rows; smoke run first (11-item checklist; idle machine sample_ms_max < 50 ms, no 5 s periodicity in >8 ms frames; else -ProcEvery default 0). top procs record user process names -> don't publish run dirs.
- 02:14 Started M7-successor (paper: #19 rows queue package + #21 MP2/MP3 proof scripts; no run_command after 03:40).
- 02:14 M3: s4b07r PASS (C1 + verify, quiet host: K=0, **F=51** vs 92 under compile load -> F not just a load effect; 0 STUCK-LOCK). s4bV0 (C1 off + verify) launched 02:14:18; its F vs 51 decides M12's prediction. (C1 verify-only fix devoff4bv + s4b07f should drop F to ~0 if F is the hash-0 gap fault.)
- 02:24 M3: s4bV0 PASS (C1 off + verify: verify on x1, K=0, **F=70** vs 51 with C1 on) -> M12's prediction confirmed: F pages are not caused by keep-watch (verify-side gap fault; C1 verify-only fix should remove them). s4bLV (p2fc + verify, 1800 s cap) launched 02:23:55, ends ~02:54.

## 02:32 user: "you have the entire PC, feel free to max out CPU/GPU/RAM"
- Decision: pull the morning builds into tonight. Build cap (≤2 threads, Idle) lifted by the user. Timing rules unchanged (no builds during timed windows or hang-sensitive rows). Plan: M3 holds its queue after s4bLV (~02:55) until `build\agent1\night\ROWS-RESUME.txt`; new M2 (successor, conv a657e030) builds at full speed, one at a time from fresh trees: devoff4bv -> devoff4b-s33-bin -> devoff4b-s33d-bin -> devoff4b-ctr-bin -> (#19 devoff4b-r19-bin if time); hard stop 03:35. Then rows f10a3, f10b3, cg26L, s4bN4 (~04:15), then timed windows WC1 -> W8a -> WC2 -> W10 (~04:20-07:00; W10 drops if it can't start by 06:45). New bins' rows (s4bV0f/s4b07f, #33 1a/1b) can run right after the windows.
- M7 S3T-7 DONE (paper): #19 rows package `build/agent7/session3/queue-r19.jsonl` A17F398B (5 ref rows + a,b,i,c,g,j,d,f,e chained by markers; ON rows need go-r19on), r19_gate.py 1DD4A89E, check_queue_r19.py (183 checks PASS), test 50/50, ROWS-R19.md 5BC93446; #21 MP2/MP3 tools in `build/agent7/session3/mp/` (selftest 25/25). Decisions: fallback A -> row d planned no-op INCOMPLETE, chain continues; no-split ref -> split-dependent rows held; MP2 --spread-k 1, LS info-only, --zero-dc info on native; F3 UNCLEAR until a level route with succeeding queries. Sent to M10 to rate. M7 killed (work in files).
- 02:34 **s4bLV PASS** (M12; p2fc + verify, K 0 / **F 0**, P2c 0, 0 STUCK-LOCK) -> C1 default-on condition 1 met. F 0 vs 51 (s4b07r) / 70 (s4bV0): p2fc timing or single_hold_rearm narrows the verify race (one run each, not conclusive). s4bLV ended early (route end 558 s); M3's queue had already launched f10a3 at 02:33:24 -> let it finish (~02:44), then HOLD + COMPILE GO; build hard stop 03:45.
- 02:36 M10 rated #19 rows package **SAFE-IF** (`build/agent10/session3/r19-rows-mp-rating.md` F8ECBC2E). Q2 no-op confirmed with machine conditions (r19_gate exit 2, only "no async counter line" incomplete, ref r19r25 also 0 splits). Q3: hold c/f OK, but i and g must be replaced by 16 KB versions i16/g16 (TODO: add to SPEC19 + re-point chain before the #19 queue runs; no re-rating if only that). C3: e INCOMPLETE ends chain; W7 needs j + e PASS with real splits. MP2: decision (b) — verdict = LOG checks (+DC where draw_calls > 0), LS read as info from JSON; native routes = "frame identity not proven". NIT: add exe-vs-MANIFEST check at row a.
- 02:40 M3 HOLD (queue waits for ROWS-RESUME.txt; LastLaunch 04:50, GamesClosed 05:00). f10a3 PASS by f10 rule (STUCK-LOCK 0, level reached), hint LOOK: one hostload sample saw ninja (M2's prep query, 02:36). s4bLV: P2 memexport total 0 -> P2 gate closes.
- 02:41 **COMPILE GO** to M2 (builds 1-4; #19 awaiting M10 ruling on a 9-TU dependency-scoped recompile vs full SDK rebuild). Hard stop 03:45.
- 02:41 M12: **f10a3 PASS** (quiet-host stands: ninja 1/12 samples, not in top-4, cpu normal). Finding 10 did not reproduce on the quiet host (Agent 3's 0/4 -> 0/5).
- 02:43 M10: #19 build method **ACCEPT-IF** (`build/agent10/session3/r19-build-method.md` A813D340): 9-TU recompile + rexgpu-xenos relink replaces "full SDK rebuild" (ninja deps verified; DLL is a plugin with 4 exports, ABI unchanged; no ODR risk). Blockers: CTL relink == E3CB99CF except timestamp; overlay -I first on all 9 commands. Forwarded to M2.
- 02:49 M2: **all 5 bins built + staged by 02:47:30** (full cores; CTL relinks == devoff4b except TimeDateStamp; shared DLL E3CB99CF intact; devoff4b/cg26/native4b MANIFESTs 0 FAIL after each; exe DFBE1D43 + rexruntime A33801D1 == devoff4b in all):
  - devoff4bv-bin MANIFEST 353846A3 (DLL 82A0DE74; C1 verify fix)
  - devoff4b-s33-bin 50CC5BE2 (DLL 0B57BBD5; nohunk5 57CFA8AD; needles PASS)
  - devoff4b-s33d-bin 0B1CD3C2 (DLL 962D88D6; + diag (d); needles PASS)
  - devoff4b-ctr-bin A5367CB5 (DLL FACCF87F; deferred counters)
  - devoff4b-r19-bin 1EBF1163 (DLL 5DCDD8CB; #19; M10 C1-C5 PASS in `build/agent2/s33/r19/r19-checks.txt`; -MD/-MF SHOULD not done)
  - Method fix: CTL first DIFFed on __FILE__ slashes -> --fwd-src + -fmacro-prefix-map. Each compile ~8-9 s, link ~1.5 s.
- 02:50 ROWS-RESUME.txt written; M3 runs f10b3, cg26L, s4bN4 then IDLE -> timed windows start (~03:25). M3 drafts a post-window queue (s4bV0f/s4b07f on devoff4bv; #33 rows 1a/1b) for ~06:05+, M10 to rate.
- 02:57 M12: **f10b3 PASS** (p2fc, STUCK-LOCK 0; quiet pair 3 = 0/2 for finding 10; P2c 0). Note: e_eff median 1763 MHz (f10a3 1846) vs ~2600-2740 on earlier rows; host is a laptop (i7-1255U, Balanced plan; at 02:57 % processor performance ~200 with a game running), so likely thermal/power drift. Within-window round-robin handles it; read-outs should report per-run clocks and treat cross-window comparisons with the existing caveat.

- 03:04 cg26L PASS (M3): 20261125-025738-cg26L-level, devoff4b-cg26-bin, level route, exit 0, level True, tags 3/3, STUCK-LOCK 0, quiet host 0/12, logdiff vs s4bL0 NEW 0. Only known LOOK hints (pads-white timing, XNetLogon stub). Passed to M12 for gating. s4bN4 launched 03:04:24.

- 03:09 s4bN4 PASS (M12): split lines present at 4 KB (18 counter lines, failed 0). Fallback A not needed. Ready-N: K=1.25 subs/frame, ~312 fps, N = 3.1-5.1 KiB (~4 KiB). f10aL/f10bL skipped so the windows can start. M3 told to go idle, M12 to go quiet.

- 03:10 M3 IDLE 03:08, M12 QUIET 03:09, ready-N=4 written by M3. Fixed a pre-go.ps1 bug: the hashtable $latest collided with the [string]$Latest param (PowerShell names ignore case), renamed it to $latestTbl (backup pre-go.ps1.bak-0310). Pre-go READY. WC1 GO written (see the line below). Quiet rule now applies to all managers; M10 is rating M3's post-window drafts (read/write only).


- 03:12 The user allowed closing Codex. Its node runtime (pid 27644) is gone. codex-windows-sandbox-service (pid 6288, an idle Windows service) did not stop and was left alone: stopping it would need elevation. No more commands until WC1 ends.

- 03:12 M10 rated the post-window drafts (`build/agent10/session3/postwin-rating.md`): SAFE-IF. Conditions P1-P5: hash checks at launch; live only after the windows end; strict 1a/1b pass rule (both check.txt PASS? on the kit's run dirs, kit exit 0, no_wait x0, s33_fields exit 0); move old check/s33 txt aside before any re-run; quiet-host caveat for F. SHOULD: S1 ninja_deps scan before go-postwin (M10 runs it after the quiet rule lifts); S2 s33base2 needs a manual kit run. NITs N1-N5. The sha8 is pending until commands are allowed.

- 03:50 WC1 END: runner exit 0 (all runs OK), 34.6 min, out build/agent8/matrix/20261125-0315 (window start 03:15:51 after a 6-min MsMpEng wait). 03:56 pre-go W8a (-Latest 06:41) with -Go (result in the next line if it fails).


- 04:29 W8a END: runner exit 0 (all runs OK), 30.5 min, out build/agent8/matrix/20261125-0359. 04:37 WC2 pre-go -Latest 06:38 -Go.


- 05:14 WC2 END: runner exit 0 (all runs OK), 34.7 min, out build/agent8/matrix/20261125-0440. 05:16 W10 pre-go -Latest 06:41 -Go.


- 05:45 W10 END: runner exit 0 (all runs OK), 26.4 min, out build/agent8/matrix/20261125-0519. 05:48 decision: there is time before 06:45, so I GO a repeat of WC1 (same matrix/sha; call it WC3 in read-outs) to give each C arm 9 scored runs (rounds 2-4 of WC1, WC2 and WC3). Expected end ~06:26.


- 06:25 WC3 (WC1 repeat) END: runner exit 0 (all runs OK), 34.6 min, out build/agent8/matrix/20261125-0551. All 5 timed windows are done, each exit 0 and all runs OK.
- 06:27 Runner summaries (preliminary, before the formal read-outs):
  - W8a (native4b, every switch OFF): mc (LEGO_NATIVE_SHADER_MISS_CACHE=1) is 2.15 ms vs n0 3.00 ms median, −28.6% median, −34.1% p99, 461 vs 320 fps, the same 1.86-1.89 cores. All 7 mc runs (2.14-2.21) beat all 7 n0 runs (2.80-3.09): FASTER outside noise.
  - W10: cg26 is 2.06 ms vs s0 1.99 ms, +3.3%, within the ±12.8% noise. No timing gain from CG26.
  - No further window: neither verdict would change. 06:28 quiet rule lifted.
- 06:28 Dispatched:
  - M12: night gates + logdiffs for the 5 windows → NIGHT-GATES.md.
  - M8: READOUT-NIGHT.md (C pooled from 3 windows, rounds 2-4, 9 runs per arm; W10 with round 1 separate; W8a CI).
  - M10: postwin sha8 + S1 scan, then cross-check M8's W10/W8a read-outs.
  - M3: install the post-window drafts and wait for my go after S1.
  - No builds until M3's rows are done (F is sensitive to host load).

- 06:29 M10: postwin-rating.md = 3B0C445D. S1 deps scan PASS (postwin-s1-depscan.md B3470463): the header consumers are exactly the 10 rexgpu-xenos objects listed in the s33/s33d MANIFESTs, with 0 in the game builds. M3 has my go for the post-window queue (after P1). The night watchdog cron (task-120) was stopped because it is stale.

- 06:29 M3 post-window queue live. P1 OK: drafts installed (s4b_check 09DBCABC, postcheck 8B60EBC3, backups *.bak-postwin) and the bins re-hashed unchanged. #33 stop-at-first-FAIL is enforced with hand-made per-row markers. s4bV0f launched 06:29:31. ETA: s4b07f ~06:40, s33 rows ~06:51-07:35.

- 06:32 M12 night gates (NIGHT-GATES.md 7533DD5E): all 5 windows PASS.
  - WC1 and WC3: clean, STRICT.
  - WC2: G8 CHECK (one "Shutdown wedged past the close request" watchdog line after WM_CLOSE in c1np-r3; the same line is in WC3 s0-r4) cleared as a NOTE.
  - W10: clean; no cg26 functional FAIL, so the arm stands.
  - W8a: G9 FAIL was a tool artifact (the <run> path in env isn't expanded); the hand check of 15 runs is BAD 0. I accepted the override. mc r2 had high non-game load; M8 reports with and without it.
  - The window logs have 0 kill/stop failures.
  - M12 told to teach run_gates.py to expand <run> (selftest, M10 rates).

- 06:35 M8 READOUT-NIGHT.md (196D312D): 79/79 runs clean (exit 0, no WER or dumps, STUCK 0).
  - C (WC1+WC2+WC3 pooled, rounds 2-4, n=9 per arm):
    - win3 vs s0 FASTER: fps +7.7% [+6.3,+8.7], p99 −14.8% [−17.1,−14.0], 1% low −17.0%, process cores −38.7% [−40.3,−35.2]. TimerQueue 1.0-2.1% (meets the <15% gate; the other arms are at 19-22%).
    - c1np and p2fc vs s0: fps +4.0% each, cores about −7%; p99 and 1% low overlap.
    - win3 vs p2fc: fps +3.6%, p99 −15.5%, cores −34%.
    - c1np vs p2fc: all overlap, so P2 adds nothing measurable.
    - Caveat: the median frame time rises ~5% in all arms while mean fps rises (shape change), so judge by fps, p99 and 1% low.
    - Order effects ≤0.8%. Clock difference: win3 2243 vs s0 2019 MHz, attributed to the lower load.
  - W10: NEUTRAL with or without round 1 (median +3.3% [−4.4,+7.7]). M10's r26 conditions are met. CG26 gives no timing gain.
  - W8a: mc FASTER in every variant: median −28.6% [−30.9,−27.5], fps +44.2%, p99 −34.1%, 1% low −34.3%, the same cores. Robust without mc-r2 or without round 1.
  - Sent to M10 for a cross-check.

- 06:39 s4bV0f PASS (M3): devoff4bv-bin, C1 off + verify. K0/F0 vs F70 for s4bV0 on devoff4b, so the verify fix removes the race as the F source (quiet host: hostload 0/35). The 2(b) question is settled for this route only; "C1 ships as p2fc" stands. Passed to M12. s4b07f launched 06:38:58.

- 06:41 M12 gated s4bV0f: PASS (bin check, positive controls, manifest_check BAD 0/19).
- 06:41 M10 cross-check (readout-night-xcheck.md 25BF9B1C): CONFIRMED for C, W10 and W8a.
  - The median rise is explained: C1 adds a short-frame mode (<1 ms frames go from 1.9% to ~20%, with the same draw work). win3 also cuts >4 ms frames from 6.3% to 2.0%.
  - The win3 clock gain is an effect, not a confounder (at most ~1.2 of the +7.7 points come through the clock).
  - W10: neutral within about ±4% fps.
  - W8a: mc's gain is not clock-driven.
- Decisions (proposed, keep/drop to confirm with the user):
  - SHIP win3 (p2fc cvars + timer bundle + precise wait + back-off/spin env, q500 via the code default under M10's DB5D1282 conditions). KEEP P2 inside it (M10 option a: the shipped set equals the timed set).
  - CG26 not on by default (no timing case).
  - mc (native shader miss cache) is the default in the native path whenever native ships.
  - Scope note for the write-up: one light route, uncapped (~450-490 fps), AC power only; the idle/battery cost of host_timer_resolution_ms=1 is unmeasured; at a 60 fps cap the gain is CPU headroom and tail, not fps.

- 06:42 Dispatched the day prep:
  - M2: final-build defaults diff (win3 as the code default + q500 per DB5D1282 + native miss-cache default) → build/agent2/final/; no build until M3's rows end and M10 has rated it.
  - New M7 (conv 755c6d86): #19 row chain prep (SPEC19 i16/g16, ready-N=4, queue-r19-live.jsonl for M3), to launch after M3's post-window queue (~07:35) once M10 has rated it.

- 06:44 M10 rated M12's run_gates <run> fix SAFE (run_gates-runexp-rating.md CF84959C; selftest 59/59 re-run; the re-gate matches). The mechanical W8a G9 PASS replaces the hand override in the night records. NITs: store the diff as LF; add a G9 note that the native-frames.csv file exists; add a moved-folder note to W6-GATES.md. w6_kit.py still doesn't expand <run> (INFO).
- 06:43 M8 READOUT-NIGHT.md updated → 290BB029 (N1-N5 + S1/S2). M8's runner install is approved: copy + selftest after 07:30, smoke run only in a slot between M3's queues.

- 06:49 s4b07f PASS (M3): devoff4bv-bin, C1 + keep_watch + verify. K0/F0 vs F51 for s4b07r (kept 2→65536; quiet host 0/34). Together with V0f, the verify fix removes F in both C1 states, so C1 itself makes no bad pages on this route. "C1 ships as p2fc" stands (P2 kept per the 06:41 decision). Passed to M12. s33base launched 06:48:23.

- 06:52 M12 gated s4b07f: PASS (C1-without-P2 clean on this route, 2(b) settled; not a default). M7 finished the #19 prep: queue-r19-live.jsonl 8A6182A9, LAUNCH-R19.md 88ED9278, r19_path.py, edited r19_gate/check_queue/test (62/62, 226 checks pass), ~76 min on the N path. Sent to M10 for rating. Append only after the post-window rows; current order kept.

- 06:56 M10 rated r19prep SAFE-IF (r19prep-rating.md 335563D8). L1: gates from WS with --bin. L2: check_queue on the installed queue. S1: memexport restriction line in LAUNCH (M7 adding it). go-r19on PRE-AUTHORIZED by me at 06:56 under M10's Q1 terms (r19-ok-a/b/i from clean --bin gates, no FAIL/FLAG/unplanned INCOMPLETE; revocable by deleting the marker). M3 briefed for after the #33 rows, leaving a slot for M8's smoke run first.

- 06:57 s33base (20261125-064824-s33-base): Hint LOOK. The only miss is BASE logdiff GONE XNetLogonGetTitleID STUB (RA base = a different route, M10 N3; the same GONE as in f10a3/f10b3/cg26L). My ruling (a): a LOOK with only that GONE = PASS? for postwin P3 point 1. Any other miss, NEW, FLAG or proof miss stops #33. go-s33off authorized. Passed to M12.

- 07:01 M2's FINAL defaults set (build/agent2/final/, FINAL-DEFAULTS.diff 955543F5, 11 files):
  - 12 SDK cvar defaults = win3 (8 rexruntime TUs + 1 rexgpu-xenos TU);
  - q500 byte-identical to M9's diff;
  - native miss cache on by default (fingerprint 9b40…→1616…, first launch cold);
  - "Final defaults:" proof lines;
  - check-defaults.py.
  - Decision: native N-A (new native exe + old snap1-sdk DLLs = as timed in W8a).
  - Sent to M10 for rating. Build slot after the #33 rows (~07:35), then M8 smoke, then the #19 chain, then the final functional set; the confirmation window needs a timed slot (user away).

## 07:01-07:32 (Overseer)
- #33 row 1 PASS (M12, ROWS-RESULTS 36F19CFC): s33base PASS? (a), s33off PASS? (a2 = mark-timing-only BASE miss, same marks/order, <1 s, no NEW/FLAG/proof), s33basesf PASS? (a2), s33offsf PASS?. Row 1a/1b kits exit 0, no_wait x0, s33_fields exit 0. Off-arm baseline: 1286 dropped draws / 48 frames (last #12707), 0 late drops, 0 forced waits.
- postcheck fixes: 123FD6D0 (kit output via %TEMP%) -> 1025D1F6 (M10 Q1/Q2: clear dirs, copy -ErrorAction Stop, explicit exit lines). M10: SAFE-IF -> CONFORMS (postcheck-0706-rating.md 6783F5AB).
- Final defaults: M10 SAFE-IF (final-defaults-rating.md C20B6FDB; build plan final-build-rating.md DF596C16, B1-B5). M2 build go 07:26: prep PASS, fsyntax 19/19, rt/gpu/xe/nat/xeoff/natoff all PASS (CTL == ref except TimeDateStamp; pe-check; mapcheck). Not staged yet: M10 checking post-rating edits to build-final.py (5BE1F221) and fsyntax.py (66C7D740).
- Night launcher ended 07:30:04 (deadline, exit 0). M8 runner install INSTALLED 07:30 (run-matrix 72370A1E etc.), selftest running.
- Day installer plan check REFUSED (exit 2): it pins night run-matrix 1A522CDF, now 72370A1E after M8's install. M8 to prepare re-pinned copies for M10 rating; day launcher not installed.

## 07:32-08:30 (Overseer)
- **Final bins** staged and pinned by M2 (build/agent2/BIN-PINS.md FE4CD4FF): devfinal-bin F9C2BE72, devfinal-off-bin 3F4B7BEB (back-off default -1), nativefinal-bin D7C7B706 (N-A; fp 1616ce65e973c583), nativefinal-off-bin 0C67CBD6 (miss cache default 0). M10 B1-B5 CONFORM (final-build-rating.md 94CC9FA7). M12 manifest check over 23 bins: 0 bad.
- **M8 runner:** selftest OK 28/0 after the $r/$R case-collision fix (sys_selftest 5C2D2038). Smoke out-0734 4/4 OK. ProcEvery stays 5: the ABBA test shows the stalls are host-caused.
- **07:46-07:47 installs (Overseer, no launcher running):**
  - day launcher, with M8's re-pinned install-day.ps1 D2D1D11F (M10 SAFE, day-repin-rating.md 42982AFF) -> bench/agent5/day/;
  - run-timing.ps1 75F4B527 -> 9CCE9827 (stop_line regex fix; M10 SAFE-IF R1).
- **final_gate** (M12) v3 73F946E70D586060, PINNED and FROZEN until fx7 is gated (M10 final-fx-rating.md B21AD5EA, SAFE-IF C1-C4). Ruling: F2/F7 level-route timeouts are accepted as by-design waits plus a NOTE. postcheck installed D204503F (C1 gate hash, S1 F-GATE line, S2 cache refusal).
- **08:09 F1-F7 queue** installed by M3 (build/agent3/final-fx/, queue-final-fx.jsonl 72DF558A; check_queue_fx ALL PASS). It stops launching at 13:30.
  - F1 fx1 PASS (M12 + M10: G3 real positive, all 13 keys source default).
  - F3 fx3 PASS (devfinal-off-bin, check-defaults --mode off PASS).
  - F4 fx4: final_gate exit 1, and the only FAIL was the --pair proof compare (61 vs 65). The cause is the periodic "C1 keep-watch: N protects kept so far" lines (54 vs 58); the 7 startup proof lines are identical (I verified, and M12 cross-checked). **Ruling: F4 PASS** (build/agent4/session3/ruling-fx4.md). The gate stays frozen; post-sprint fix PS1 is to exclude the periodic line. go-fx was held 08:23-08:25, then restored.
  - fx2 running (ends ~08:37). Order: fx5 -> fx5w -> fx6 -> fx7.
- **Confirmation drafts** (M8, build/agent8/session3/confirm/): CF1 ship/s0/win3 x6 (~44 min), CF2 nf/mc x6 (~30 min); READOUT-PLAN 18F69B57. M10 SAFE-IF K1-K5 (confirm-rating.md 31AD69BA). Waiting for the user to be away.
- **#33 rows 2-7 + (d)** draft (M3, build/agent3/session3/s33-rows/): M10 SAFE-IF C1-C5 (s33-rows-rating.md B6EFB444), then fixes CONFORM (9D96775F): s33_sceneids FA78C672 (stable > 0 s in both runs, ON rows only), postcheck 36DC0E05, READING-S33 976818B4, PLAN 37CF0E82. Ruling (a3) is refined: on ON rows, a SHOULD NO (non-neighbour stable id) = HOLD for the Overseer. Install only after F1-F7 and #19.

## 08:30-08:56 (Overseer)
- **F1-F7 are complete.** F1, F3, F5, F5w and F6 PASS on the gate. F2, F4 and F7 PASS by Overseer ruling:
  - ruling-fx4.md: the periodic "protects kept so far" lines in the --pair compare.
  - ruling-fx2.md: the 590 s floor is a calibration error. The route takes 551-585 s and finished 121/121.
  - ruling-fx7.md: the floor, plus the NEW CONFIG.XML probe vs the menu-only native base. That probe appears x1 in 21 of 24 level runs on both backends, and x0 in the native menu runs.
  - All three rulings are in build/agent4/session3/.
  - Post-sprint gate fixes PS1-PS3 are recorded in M12's ROWS-RESULTS.
- M10 confirmed fx5/fx5w as real positives (final-fx-rating.md CA6FCFBE):
  - "shader miss cache ON (build default)" x1 on the miss path. F6 shows the OFF line, so the switch is proven both ways.
  - Warm path: seed 10456 B, loaded=1 compiled=0 failed=0, all 12 pipelines from the seed.
  - Write-up limit: game.log shows no cache *effect* (the miss mix is identical at 26). The effect rests on code identity with W8a mc and the CF2 timing.
- #33 rows draft: CONFORMS (s33-rows-rating.md 9D96775F). READING-S33 → C960C0C9, with the SHOULD NO = HOLD ruling.
- **08:55: the #19 chain was installed by M3** (queue 053147D1 → 5194F3A3; L2 check_queue_r19 --expect-n 4 ALL PASS 226). r19r11 launched 08:55:15, ending ~10:10.
- CF1/CF2: K1 is met. They wait for the user to be away (K5).

## 08:56-09:28 (Overseer)
- **#19 reference rows PASS** (all on `--bin build\agent2\devoff4b-bin`; M3 gated them and M12 cross-gated): r19r11 (i16), r19r10 (path N, N=4, r19-pathN), r19r13 (rbme), r19r15 (debug), r19r25 (title).
- **#19-bin rows** (`--bin build\agent2\devoff4b-r19-bin`; exe DFBE1D43, rexgpu 5DCDD8CB, rexruntime A33801D1):
  - r19a PASS -> r19-ok-a.
  - r19b PASS by ruling (e) -> r19-ok-b.
  - r19i PASS -> r19-ok-i.
  - **go-r19on** written by M3 at 09:25 (pre-authorized; M12 agrees).
  - r19c (async ON, base r19r10) launched 09:25. Still to run: g, j, d, e, f (LAUNCH-R19).
- **New rulings** (build/agent4/session3/):
  - ruling-r19-d.md (rule d): a BASE miss on scene ids only still counts as route coverage (PASS?) if all of these hold:
    - same marks and order, n/n steps;
    - the drift is stated with the ids;
    - NEW 0 beyond allow-new, MORE 0, FLAG 0;
    - 0 proof misses, 0 unexpected GONE, 0 errors;
    - r19_gate clean.
  - ruling-r19-e.md: allow-new patterns are matched in logdiff-normalised form (digits -> #). Allowed lines are quoted verbatim.
- **Coverage limits for the #19 read-out:**
  - S1' (M10, r19prep-rating F426CEA0): readback memexport is ON in every run (harness toml L65). A row f PASS means async plus split ran clean with readback ON, which is the normal state. The cvar is never set to false. The LAUNCH S1 line will be corrected after the chain. The follow-up row r19eL (M3 draft, not installed) would lift this limit.
  - Row g / ref 4: they prove only "runs clean with the debug layer active". The SDK never drains InfoQueue, so d3d12_msg=0 proves nothing. The debug-validation pair r19vr/vg/vw (M10 SAFE-IF H1-H6) is PARKED because of the WER/JIT-prompt risk. A post-sprint InfoQueue drain patch is preferred.
  - ON-row validity check: s4b_check's `sys.csv slow state` line (if slow, read only up to onset_s and HOLD); Busy n/a on s4b rows. timerq_slowstate.ps1 scans 0 runs in the flat build\agent3\runs layout, so it is not cited (M12 heads-up, approved).

## 09:28-10:00 (Overseer)
- **#19 chain DONE: 14/14 PASS** (5 refs + a, b, i, c, g, j, d, f, e). Each row was gated by M3 and cross-gated by M12. Slow state is false on all 14. M12 summary: build/agent12/session3/R19-SUMMARY.md 3626A499.
  - c: async ON, split 4. 21+21 counter lines, queued_max 3, failed 0. Every split went async; the last pair is equal at 255831.
  - g: debug layer + async. DRED x1. Coverage limit: proves only "runs clean with debug layer active".
  - j: split 16 + async. chunks 67826, full_waits 1126 (J1).
    - The drift was the largest so far. **ruling-r19-j.md**: PASS? by rule (d), because the perf.csv load profile matches (dc median 226/226, p90 4385/4379).
    - M12: vs s4b01, r19j followed the old path; the base r19r11 was the run that went one screen ahead.
  - d: title route, uncapped. chunks 103846, queued_max 2 (full_waits 0 is fine on a light load). GONE 20 = Toypad packet dumps.
  - f: readback memexport ON + async. chunks 253903. Load class matches (the ruling-r19-j method). The S1' coverage limit is carried.
  - e: 10-min level soak. 41+41 lines, chunks 648929, held_query > 0. 119/119 steps; Vortex reached; toypad 3/3. GONE 57 = Toypad dumps.
    - Elapsed is 69 s shorter than s4bL0, with no step skipped: story-load wait −41.6 s, close −19.0 s, startup −4.0 s, vortex −1.6 s, jitter about −3 s.
  - **W7 met** (j + e with real splits).
- ON-row validity check: s4b_check's slow_state, approved (see above). PS4 = the timerq_slowstate doc fix.
- Post-sprint doc fixes: LAUNCH-R19 S1 -> S1'; allow-new written in normalised form; row_gate `<N>` placeholder artifact.
- **#33 rows 2-6 + (d) installed** by M3 at 09:58 (S33-ROWS-PLAN steps 1-7). Live s4b_check 3DDF1A55, postcheck 36DC0E05 (restarted), queue 69C77DA7; .bak-s33r 09DBCABC/D204503F/5194F3A3. I verified the hashes. **go-s33r** written 09:59. Row 2 (s33onsf) is next; about 84 min core.

## 10:00-10:55 (Overseer)
- **Row 2 s33onsf: PASS?** (M3 + M12). Frames >=100 ms: 20 vs 67 (offsf). Frames >=250 ms: 4 vs 12. Cost: dropped draws 2484 over 85 frames, vs 1286 over 48 frames. This no_wait dropped-draw cost goes to the row 3 eye review.
- **Row 4 (onstop) started badly.** stop1 (S 203) and stop2 (S 205) both gave exit 3: their close windows fell into a quiet gap.
  - M3 found the cause: miss bursts are locked to the 67-miss frame H0, which drifts between 132.7 and 149.4 s. M12 confirmed it (s33-h0 B5DA7B49).
  - **STOPR re-time:** STOPR rev 2 583C40E2 picks S by simulation. My first hand guesses (181/211/215) scored only about 30%.
    - M10 rated it SAFE-IF R1-R5 (build/agent10/session3/stopR-rating.md B67F3E2C). Checker r3 9F993FE4 CONFORMS; r3 fixed a false FAIL in dryrun, which does not write seconds_requested.
    - Installed per R1: PAUSE file, wait for the HOLD/PAUSE line, then [IO.File]::Replace. Never use Move-Item on queue.jsonl. Live queue CB502E8C, .bak-stopR 69C77DA7. PAUSE was in place 10:39:36-10:40:08. M12 verified.
    - STOPR.md rev 3 DEE60586 is a doc-only change.
- **Row 4: PASS** (M10 R3). Counted 3 of 5 planned (TESTPLAN onstop x5, reduced to >=3 by the STOPR budget). All 5 runs closed cleanly with wm_close.

  | run | S | exit | gap | in window | close |
  |---|---|---|---|---|---|
  | stop1 | 203 | 3 | 12.307 | 0 | 0.71 s |
  | stop2 | 205 | 3 | 4.124 | 0 | 1.26 s |
  | stop3 | 153 | 0 | 1.088 | 39 | 0.85 s (H0+14.19) |
  | stop4 | 146 | 0 | 0.748 | 75 | 0.82 s (H0+1.07) |
  | stop5 | 230 | 0 | 0.355 | 1 | 0.74 s (H0+80.67) |

  - Final wording (M12 amendment, per R4): "PASS — 3 counted of 5 planned (TESTPLAN onstop x5, reduced to >= 3 by the STOPR budget, Overseer 16:17Z): stop3 S153, stop4 S146, stop5 S230 counted; stop1 S203 / stop2 S205 exit 3 (clean, not counted, outside the budget); stop6/stop7 not run (R3). All 5 stop runs clean wm_close (0.71-1.26 s), wedge 0. No exit 1 occurred, so the S1 attribution question did not arise; no OFF stop control was run."
  - M12 cross-gated all 5 runs (stop5 at 10:57: s4b_check PASS?, NEW 0 beyond no_wait info, 0 judged marks differ, GONE 124 all Toypad). The closes during a miss burst were no slower than the quiet ones. Files: build/agent12/session3/s33/ (s33-stoptable A6E7EF2D, ROWS-RESULTS A0973EF0).
- **Row 5: PASS?** s33offw: seed proof OK, with misses in only 2 frames.
  - s33onw: M3 put it on HOLD because of READING L53 ("drops long after boot").
  - **ruling-s33onw.md** made it PASS?: 30 drops in 2 frames, identical to the OFF arm. M12 proved through the xpso records that these are the same pipelines. Frames >=100 ms dropped from 89 to 37.
  - Doc fix: READING-S33 L53 should say "beyond the OFF arm".
- **Row 6 started:** go-s33gthr0 written 10:54. Gate rules:
  - latch: `INFO not-waiting 0, WARN ignored 1`;
  - forced waits 0, late drops 0;
  - any INFO line = STOP; any differing judged mark = STOP.
  - Order: gthr0, then gasync, then gbind, then (d) offd and ond.
- Finding for the async PSO work: no_wait still lets a pipeline create land on the frame path (frame #7366: a 322 ms pipeline create with no_wait ON).

## 10:55-11:16 (Overseer)
- **Row 6 DONE: all 3 gate arms PASS?** (M3 + M12), --bin build\agent2\devoff4b-s33-bin, base offsf.
  - The live check showed LOOK (NEW 1) on every arm. The only new line is the planned gate WARN `[warning] [gpu] d#d#_pipeline_creation_no_wait ignored: it needs async_shader_compilation, pipeline creation threads and bindless resources`. postcheck passes $S33ON in raw form (`d3d12_...`), so the WARN cannot match the allow-new filter.
  - **ruling-s33-gthr0.md** (ruling-r19-e applied): $S33ON is read in normalised form. A read-only checks-norm re-check is the row's s4b reading. gasync and gbind were pre-authorised under exact-WARN-only conditions.

  | arm | cvar | checks-norm | GONE (all Toypad) | dropped draws | frames >=250 ms (offsf 12) |
  |---|---|---|---|---|---|
  | gthr0 | threads=0 | F47C1579 | 103 | 0 | 17 |
  | gasync | async_shader_compilation=false | 0AD4C0EC | 93 | 0 | 8 |
  | gbind | d3d12_bindless=false | 1B7FBCC4 | 101 | 1317/50 (offsf 1286/48) | 33 (22.2 s vs 6.7 s) |

  - On all arms: latch INFO 0 / WARN 1, forced waits 0, late drops 0, 0 judged marks differ, errors 0, PROOF ok.
  - gbind drops: M12's s33_dropmiss (979431C6) shows all 50 drop frames are miss frames. The last drop equals the last miss, the same pattern as OFF; async creation stays on in that arm.
  - Info: bindless=false is much heavier (n67 frame 5102 ms vs 897 ms; 12289 frames rendered vs 22697).
  - M12 files: build/agent12/session3/s33/, ROWS-RESULTS DD6F8924.
- (d) s33offd started 11:14 (540 s, devoff4b-s33d-bin); ond follows.

## 11:16-12:45 (Overseer)
- **(d) s33offd: PASS?** (M3). NEW 0, GONE 8 (0 unexpected), FLAG 0. The 3 allowed info keys are the planned `resolve after drop` lines (211). Warnings 142 = offsf. 0 judged marks differ.
- **(d) s33ond: PASS?** (M3, base offd; read like row 2). NEW 0, MORE 0, FLAG 0, GONE 10 (0 unexpected). The only info NEW is the no_wait INFO line. diagd exit 0. M12 cross-gate requested 12:45.

  | | offd | ond |
  |---|---|---|
  | diag lines | 211 | 308 |
  | after-drops | 110 | 172 |
  | healed | 101 | 136 |
  | tainted at end | 0 | 0 |
  | heal latency med/p95/max s | 0.082/0.705/11.713 | 0.040/0.310/11.799 |

- **#33: all planned rows are read** (2, 4, 5, 6, (d)). Row 3 (the user's eye review) still gates any recommendation; row 7 stays blocked.
- **The user was away from 11:22.** M3 PAUSEd its queue at 11:23:02 (my hold message crossed its go-s33ond write; go-s33ond was deleted before any launch). M2 confirmed it was quiet.
  - The user started RUN-DAY at 11:27 (deadline 12:45).
  - **CF1:** K2 promoted (bench\agent8\run\matrix-windowCF1.json D36A40CA), stage-confirm -Recheck OK (stage-CF1-112410). GO written 11:34; accepted 11:34:52.
    - **The quiet gate refused it at 11:51:00 on the deadline.** MsMpEng ran at about 1 core from 11:35 to 11:45, then CrossDeviceService spiked to 0.79 at 11:46-11:48. Nothing ran.
  - **CF2:** K2 promoted (DF8A2D3B), Recheck OK (stage-CF2-115417). GO written 11:54; accepted 11:54:37; START 11:59:38; END 12:26:04, runner exit 0, 13/13 OK, out build\agent8\matrix\20261125-1159.
- **CF2 read-out** (M8, build/agent8/session3/confirm/READOUT-CF2.md 5C601D91): **nf reproduces mc, weak S1 form.** Rounds 2-6, n=5/arm, 0 void, 0 M12-flagged.
  - fps 458.8 vs 459.9, −0.2% [−0.8, +4.2]: not shown different.
  - p99 3.202 vs 3.098 ms, +3.4% [−39.8, +11.8]: not shown different.
  - 1% low 3.566 vs 3.427 ms, +4.0% [−44.7, +23.7]: not shown different.
  - cores 1.829 vs 1.835, −0.3% [−4.7, +3.3]: EQUAL.
  - Every run was at 1740 MHz (plateau). Proof and functional checks 13/13; 26 shader misses per run, as in W8a.
  - The tails are wide because of first-in-round runs (mc-r2 439.5 fps / p99 4.43). With n=5, one run sets a bootstrap bound.
  - **M10: CONFIRMED** (build/agent10/session3/cf2-check.md EFA8501D; CIs reproduced exactly).
    - C1: CF1 uses the same plateau code and the 0.97 threshold.
    - C2: quote the tails as "not shown different", never "equal".
- **CF1 is still open.** It needs a new day-launcher session.
  - The user allowed me to restart RUN-DAY with return 20:15 (end 20:00). But agy-grid's `open` approval for RUN-DAY.cmd came back "not allowed" twice (timeout while the user was away).
  - I won't route around that dialog. CF1 waits for the user to start RUN-DAY or to approve the dialog.

## 12:45-12:52 (Overseer)
- **M12 cross-gated (d): offd PASS?** (check 2D4CD316), **ond PASS?** (check 84ADB604; diagd exit 0). Diag comparison s33_diagcmp 01839EC8:
  - tainted at end 0 on both arms;
  - the same 2 slow destinations (1ADB0000, 1BD00000) in both arms;
  - last taint about 185 s before close;
  - not covered: pixel-level corruption (that is row 3, the user's eye review).
  - M12 ROWS-RESULTS now 36B412D5 (includes the "#33 rows 2-6 + (d)" summary). No FAIL/STOP on any #33 row.
- The 11:27 day launcher ended on its deadline at 12:45:12 (exit 0).
- **New day session:** the user re-sent the agy-grid approval and allowed it; I opened RUN-DAY.cmd at 12:49:58 and typed the return time `20:15` and `Y` (the user approved these inputs at 12:05). Launcher pid 24624, REAL, ends 20:00:00, 19 files pinned.
- **CF1:** stage-confirm -Recheck OK at 12:50:54 (stage-CF1-125054.txt; 19 runs, about 44 min). M3 queue still PAUSEd; M2 quiet. GO written 12:51:08, accepted 12:51:19; waiting for the quiet gate.

## 12:52-13:50 (Overseer)
- **CF1 ran: START 12:55:20, END 13:34:18, runner exit 0, 19/19 OK**; out build\agent8\matrix\20261125-1255. HOLD 12:51:19-13:34:18. M3's queue logged nothing between 12:44:30 and 13:42:47 (it ended at LastLaunch with nothing launched).
- **CF1 read-out** (M8, build/agent8/session3/confirm/READOUT-CF1.md D4D13F23; readout_cf.py 9D75B69E; rounds 2-6, n=5/arm): **CF1 CONFIRMS the night result.**

  | pair | fps | p99 | 1% low | cores |
  |---|---|---|---|---|
  | win3 vs s0 | +10.0 [+7.5,+11.4] | -16.1 [-19.5,-14.7] | -17.7 [-19.6,-3.8] | -38.5 [-41.6,-29.2] |
  | night WC win3 vs s0 | +7.7 [+6.3,+8.7] | -14.8 [-17.1,-14.0] | -17.0 [-18.0,-14.9] | -38.7 [-40.3,-35.2] |
  | ship vs s0 | +10.2 [+6.8,+11.5] | -15.5 [-17.9,-13.9] | -17.3 [-19.2,-14.6] | -38.8 [-41.1,-27.1] |
  | ship vs win3 | n.s.d. | n.s.d. | n.s.d. | n.s.d. |

  - ship vs win3: not shown different on all four, equal on none (weak form, as CF2). The wide cores CI comes from round 3 (busy host); paired cores +0.3% [-3.9,+4.5] is info only.
  - 0 void; proof 19/19; func 19/19; M12 flagged 1 (1311-ship-r3), no claim depends on it; GPU on plateau (0.97 rule).
  - **M10: CONFIRMED-WITH-CHANGES** (build/agent10/session3/cf1-check.md 5A21C759): CIs reproduced exactly; C1/C2 met; W1-W3 + NIT applied by M8 (numbers unchanged). READOUT-CF2 now 888DEB9B (sha refs only).
- M3 removed the PAUSE (13:42:47); stopR\dryrun\ deleted. M2 cleared for builds (none queued).
- Next: #33 row 3 kit (M3, for a visible-desktop screenshot pass sent to the user via Discord); keep/drop decisions asked of the user at 13:49.

## 14:31-15:05 (Overseer) - user decisions
- The user was at the PC from 14:31. Verbatim (15:04, Discord): "to the recommended options for anything that can be done while I'm away, for 4 run it and I'll review the screenshots later".
  1. **win3 settings as the shipped defaults (P2): KEEP** (night + CF1).
  2. **native renderer (mc) as the default: KEEP** (night W8a + CF2).
  3. **CG26: stays OFF.**
  4. **#33 row 3:** run now, the user reviews the screenshots later. #33 stays OFF (not recommended) until the user's verdict.
- Row 3: RUN-ROW3.cmd (M3 kit, build/agent3/session3/s33-rows/row3/, ROW3-KIT.md C129718A) opened via computer-cli at 15:04 with the user's approval; order OFF then ON (TESTPLAN L60 lists onsf then offsf; the order doesn't matter for an eye review); OFF arm START 15:04:36 on the visible desktop. Minecraft not running.

## 15:04-15:27 (Overseer) - #33 row 3 ran
- RUN-ROW3.cmd on the visible desktop: OFF 15:04:36-15:12:26 exit 0 (run 20261125-150437-s33-row3-off), ON 15:12:46-15:20:36 exit 0 (run 20261125-151247-s33-row3-on); 91/91 input steps each; row3_post.py exit 0; 16 pairs; auto shots ON 244 / OFF 288.
- At the drop moments ON visibly misses draws for at most 0.3 s: w01 black (first 3D + load), w04 12.4k shot brick rubble missing (35 now / 176 in +-0.5 s), w05 portal core missing (40), w07 mouth/teeth missing (154 / 462). OFF shows the "Compiling shaders, please wait" notice and stalls instead. All 7 persistence stills: 0 dropped, no visible difference.
- One Discord "computer use" toast (from my 15:08 screen check) overlapped the game window's bottom-right corner for a few seconds of OFF capture.
- Review page for the user: brain artifact row3-review.md. **Verdict pending; #33 stays OFF until then.**

## 15:28-15:46 (Overseer) - #33 row 3 verdict
- The user reviewed the 16 side-by-sides on Discord (posted 15:43 via a webhook the user gave; the agy-grid bot token was not used: it is held from agent shells on purpose) and on the PC (Photos, opened via computer-cli).
- Options offered: "a) acceptable: the short pop-in is a fair trade for fewer stalls -> #33 becomes a suggested setting (still off by default); b) keep #33 off; c) something stays wrong (stop rule)".
- **User verdict, verbatim (15:45): "a"**
- **#33 `d3d12_pipeline_creation_no_wait`: SUGGESTED setting, default stays OFF.** TESTPLAN section 4 condition 3 met; rows 2, 4, 5, 6, (d) PASS/PASS? (M12 cross-gated); row 7 (debug layer) left out as accepted.

## 15:46-15:55 (Overseer) - wrap-up state
- RESUME.md top block rewritten (Session 3 update 15:50).
- Repos unchanged since Nov 23: DimensionsRecomp c9e215f, SDK 5350b1d (only the expected ` m rexglue-sdk`, ` M thirdparty/plume`; SDK ` m thirdparty/simde`, ` ? thirdparty/fmt`). The final defaults exist only as `build/agent2/final/FINAL-DEFAULTS.diff` 955543F5 (bins: `build/agent2/final/BIN-PINS.md`); #33 as `build/agent2/session3/s33-popin-no5.patch`. A code commit means applying these to the repos first; asked the user before doing it.
- Open list (post-sprint):
  - builds: #21 (s4-t1.diff 46FFD2E9) + F1/F3/W1; the InfoQueue drain patch;
  - doc fixes: READING-S33 L53; S33-ROWS-PLAN/postcheck `$S33ON` normalised; row 4 seconds; s4b_check L439 comment; slowframe_join rotated logs; row_gate `<N>`; LAUNCH-R19 S1 -> S1' + normalised allow-new; "attribution open" wording;
  - reviews: PS1-PS4 (M12, rated by M10);
  - rows: r19eL (M3 draft), f10aL/f10bL (go-load absent);
  - fixes: CTR bin rows; M4 attract shader dump/native4bp; w6_kit `<run>`; f10_rule tid; M10 run_gates NITs (diff 17740F27); route-end stop trigger; M8 NITs (ProcEvery sample_ms_max, K0/F0 mapping line, M12 median 3.25 vs 3.255);
  - cleanup: dryrun dirs (final-fx, post-window, s33-rows\dryrun);
  - screenshot kit (native4 vs standard; needs native4bp).
- 15:48 user, verbatim: "yeah, go ahead" -> commit code (FINAL-DEFAULTS + s33-no5, once M2's apply-check passes) and the refreshed notes to perf/opt, push to `mine` (SDK first, then gitlink; no force; never origin/main).
- 15:51 user, verbatim: "yeah, do that" -> after the push, M2 builds one bin pair from the committed source (FINAL-DEFAULTS + s33-no5) and smoke-checks it (ETA ~17:30-18:00).

## 15:55-15:58 (Overseer) - code commit + push
- M2 COMMIT-PLAN.md D787291C (build/agent2/session3/commit-plan/). Its catch: the rows ran on M6's s33-popin-nohunk5.patch 57CFA8AD, not M2's no5 4061ED2D (comment-only difference); committed 57CFA8AD.
- SDK perf/opt: 1ba3cdb "S4 final defaults: ship the win3 timer and physical-protect defaults" (final-sdk.diff CEEF11E5, 9 files, after-hashes == plan), a7e79c0 "d3d12: add d3d12_pipeline_creation_no_wait (opt-in, default off) (#33)" (4 files, after-hashes == devoff4b-s33 sources).
- Superproject perf/opt: 2de88ce "S4 final defaults: GPU wait back-off 500 us, native shader miss cache on; SDK at S4 final" (final-super.diff 3AAEEB9F + gitlink 5350b1d -> a7e79c0). Staged blobs checked: gpu_wait_backoff.cpp 74115EEA; shaders.cpp 88D8CC7F = LF form of the built CRLF copy 4B8250E9 (EOL-only difference).
- Pushed to `mine`, no force: SDK 5350b1d..a7e79c0, superproject c9e215f..2de88ce; ls-remote matches. Plume/simde/fmt not staged.
- Next: M2 part B (final2 bins from the committed source, M10 rates the tool diffs, M8 runs the smoke boots); then the notes export refresh as a separate notes commit.

## 16:05-16:58 (Overseer) - final2 bins from the committed source
- M10 rated M2's final2 tools CONFORMS (build/agent10/session3/final2-tools-rating.md 366294FD; P1-P3 met, NITs applied).
- M2 built and staged from SDK a7e79c0 + superproject 2de88ce: devfinal2-bin MANIFEST 4A4A13EDFBFF6A5F, nativefinal2-bin MANIFEST 4E5E2620F38F7D09 (nativefinal2 now has the new SDK DLLs, not N-A). Pins: build/agent2/final2/BIN-PINS.md 33F74799. CTL legs reproduce the reference bins (TimeDateStamp only); needles, pe-check, mapcheck, verify-bins all PASS. EOL: overlay = committed blob in the snap1 base's EOL form (shaders.cpp CRLF 4B8250E9 -> fingerprint 1616ce65e973c583).
- M8 smoke (build/agent8/session3/SMOKE-FINAL2.md BE4B94F6):
  - Part 1, plain first-boot per bin (16:13, 16:18): clean exit, check-defaults PASS (xenos: 13 keys default + back-off line; native: miss cache ON), 0 `d3d12_pipeline_creation_no_wait` lines. No first 3D: with no input the game stays at the title screen (max 228 draws). The CF route also never leaves the front end (CF1 ship peaks 226-228 draws), so "uncapped fps" in CF1/CF2 is a front-end scene.
  - Part 2, RUN-SMOKE3D.cmd (B0B52007; attract-long.txt input, 240 s per arm), opened via computer use with the user's approval (the first request at 16:28 auto-declined while the user was away; user, 16:47: "I'll approve it, it gets auto declined if I don't respond"). 16:47:52-16:56:27, ALL PASS: xenos first 3D 625 draws at ~83 s after launch (max 15746), native 3D by proxy (199 new native GPU lines from 95 s); clean exits; check-defaults PASS; 0 no_wait lines. Screenshot of xenos 3D at 16:50 (brain artifact smoke3d-xenos.png); the native screenshot came after the arm ended.
- Result: the pushed source builds, boots to 3D on both renderers with the shipped defaults, and #33 stays off by default.
