# M9 review: CG26 bin and the W10 shape (S3T-9 item 2)

2026-11-25 01:42, M9 (successor of Agent 9). Paper only: hashing, reading, a depfile compare. No runs, no builds.

## Verdict

**The bin is statically ready for W10.** I agree with M2's two deviations. Two things must still happen before the W10 GO
(section 3): a functional boot of the CG26 bin (it has never been launched) and the Overseer's call on whether M10's
b2r S36 rating covers the bin or M10 signs it off again.

## 1. What I re-checked myself

| check | result |
|---|---|
| kit `build/agent9/cg26-check/cg26_check.py` sha256 | DDBA731CC22D74BD... = RESUME §7 step 2 value (not modified) |
| `build/agent2/cg26/checks/kit18/report.txt` | RESULT PASS, 0 FAIL; (a) toml line + tool 9145166C in one regen, 20/20 pauses; (b) 20 pauses, the 10 R2.17 functions, each TU minus its pauses == reference; (c) 887 files, only the 10 TUs + 3 stamp files differ, partition.json 22C9D89B unchanged, 441 headers unchanged; (d) 7/7 MANIFEST rows |
| bin MANIFEST sha256 | 917AE86E6C0CC9B370901397EF8FD72F65449E5EC9594D14D9902215BBBC1D5C (re-hashed) |
| the 7 bin files re-hashed | all equal the MANIFEST rows (exe 45952D17..., map 1ECC3480...) |
| CG26 vs devoff4b-bin (MANIFEST DE11A914) | 5 of 7 files byte-identical (both DLLs, Tracy, wav, ttf); only exe + map differ. devoff4b's exe source is `snap1-off\legodimensions.exe`, and M2's control relink == snap1-off exe/map except timestamps, so the exe differs only by the 10 ON TUs |
| no `cache/` dir in either bin dir | confirmed (nothing copied between bins) |

## 2. M2's deviations

1. **`cg26/cg26-check.py` accepts a set-equal depfile.** Agree. The diff vs `.pre-S3` is 13 added lines that run only
   when the old byte compare failed, compare target + sorted prerequisites after the cg26->snap1 path swap, and print a
   NOTE. I compared both `codegen.d` files independently: 4 lines each, the same target and the same 3 prerequisites
   (Default.xex, manifest toml, config toml); only the manifest/config order is swapped. The depfile drives rebuild
   tracking only; it is not a codegen output, and my kit (c) still shows every output identical except the 10 TUs.
2. **`mapcheck --mode same` FAIL (1).** Agree it is by design of the script, not a bin defect. The one failing row
   asserts that `gpu_wait_backoff.cpp.obj` defines no `sub_` publics, which holds only for native bins. In the same
   report every real check passes: equal `sub_`/`__imp__sub_` name sets (164786), hooked 31 = devoff4b's 31, the 31
   keep their objects, per-object sets equal devoff4b (448/438 objects). `--mode s4c` vs devoff4-bin PASS, including
   `__imp__sub_83FAF180` staying in `legodimensions_recomp.107.cpp.obj` (the TU with 8 of the 20 pauses).

## 3. Before the W10 GO

1. **Functional boot of CG26** (b2r S36 gate 4, "the OFF/ON functional pair"): one untimed run of
   `devoff4b-cg26-bin` (any manager with RUN GO, hidden desktop is fine) and a logdiff against a devoff4b run: NEW 0,
   exit 0, no STUCK-LOCK, no back-off init line. Without it, W10 is the bin's first launch.
2. **Rating:** RESUME §7 step 2 orders "kit passes -> Agent 10 rates #26 -> W10". b2r S36 (perf-notes/agent10-batch2-review.md
   §36) already rated ON "output-identical, SAFE to test" with 4 gates; the kit covers gates 1-3, item 1 above is gate 4's
   functional half. The Overseer decides whether M10 must sign the built bin again.
3. **Matrix:** M8 writes `matrix-window10.json` (not my file) and stages it with `build/agent8/w-followup/stage-window.ps1`
   (-PlanOnly), as RESUME §7 step 1 asks for every new window.

## 4. What W10 must look like

Template: `bench/agent8/run/matrix-window4c.json` (also a two-bin codegen A/B). Change only title, notes and arms:

| arm | ref | bin | MANIFEST | cvars | env |
|---|---|---|---|---|---|
| `s0` | yes | `build/agent2/devoff4b-bin` | DE11A914079D7DF7 | `framerate_limit=0` | `{}` |
| `cg26` | | `build/agent2/devoff4b-cg26-bin` | 917AE86E6C0CC9B3 | `framerate_limit=0` | `{}` |

- Both arms: frames `perf`, driver `drivers/thread-cpu.ps1`, repeats 6, order roundrobin (start arm alternates),
  warm-up 55 s from first frame, measure 50 s, `min_window_after_ff_s` 60, `sys_csv` true, the runner's usual flags.
- **Every other switch off in both arms:** no `LEGO_GPU_WAIT_*` env (so #24 is OFF), no p2fc cvars, no timer bundle.
  #26's pauses sit in `__imp__sub_83FAF180`, the function #24's hook H1 wraps, so W10 must measure #26 apart from #24
  (b2r S36 gate 4; Agent 9 HANDOFF §5 item 5). A cg26+q500 vs q500 pair is a later, separate question.
- **Cold runs:** `cold_run: true`, and the GO must not use `-ColdShared` or `-NoCold`: the CG26 bin has never run, so it
  needs its own unscored cold run. That makes 2 cold + 12 scored = 14 runs (not RESUME's 13), about 35 min.
- **GPU warm-up:** discarded runs until `gpu.csv` shows the steady clock (5-13 min), per RESUME §7 step 0.
- GO line shape: `GO W10 matrix-window10.json <sha256> only=s0,cg26 repeats=6`.
- **Expected logs:** cg26's game.log text-identical to s0's (codegen-only change, as B was in W4b); no back-off line in
  either arm.
- **Read-out:** per-round paired cg26 - s0 on median frame ms, fps, game CPU cores, and the render-thread (sub_83FAF180
  poller) busy %. PAUSE frees the SMT sibling, so a CPU-only effect is possible (b2r S36: the gain is a hypothesis, cost
  ~1.1-1.5 us per poll). If frame time gets worse, the staged-nowhere fallback is one PAUSE per db16cyc run.
