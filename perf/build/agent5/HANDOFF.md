# Agent 5 hand-off (23 Nov 2026, before the break)

Agent 5 worked on the native renderer's upload path and then on the timing infrastructure: the matrices, the overnight
launcher, the day launcher draft and the W6 matrix. All paths below are relative to the workspace root. My running notes
are in `perf-notes/agent5-uploads.md`. They stop at 22 Nov 23:14, and this file covers what happened after that.
`bench/agent5`, `build/agent5` and `perf-notes` are not tracked by the enclosing repo (its `.gitignore` ignores the
workspace folder). My source changes are committed in the nested repos, and only Agent 1 commits. "Task #N" means a
board task number, not an S4 item number from `perf-notes/RESUME.md`.

## 1. State at the break

| area | state | key files |
|---|---|---|
| **SCRNSAVE.EXE fix** (task #26, 23 Nov) | installed on 23 Nov at 07:33:57 (`install-scrnsave.ps1`), after the night launcher had ended at 07:30:14 and Agents 8 (OK) and 10 (SAFE, `build/agent10/t27/scrnsave-delta.md`) had read the delta: run-matrix.ps1 FEDCEB13 -> 1A522CDF, run-night.ps1 16B90FA8 -> 565D30D4, launch README.md 0058C8F6 -> B7CEBD63 (full hashes in the fix's README). After the install: test-scrnsave.ps1 (4D46A8E2) `-Set installed -E2E` 45/45 PASS (07:34:45) and the launcher's dry-run go group 16/16 PASS (07:52:00, with `-StopAt`). Undo: copy the fix's `base/` back | `build/agent5/scrnsave-fix/` (README.md, the diff, the tests, install-log.txt) |
| **Night launcher** (run-2 task #4, old #27) | idle; nothing scheduled. The 22-23 Nov run (pid 19960, started 23:47:20) refused 1 GO (00:03:40, the SCRNSAVE bug; Agent 1 fixed the value by hand at 00:05:37) and ran 7 windows, all with runner exit 0, the last ending at 05:30:42. It ended at 07:30:14 (deadline, exit 0), put the screensaver back (ScreenSaveActive=0, SCRNSAVE.EXE '') and released keep-awake. Now RUN-NIGHT.cmd D7A0362B (unchanged), run-night.ps1 565D30D4, README.md B7CEBD63. Pins and tests: below this table | `bench/agent5/launch/` (run-night.ps1, RUN-NIGHT.cmd, README.md, status/) |
| **Day launcher draft** (spec approved 22 Nov 22:40) | staged, not installed (`bench/agent5/day/` does not exist). Regenerated at 07:34:10 from run-night.ps1 565D30D4: run-day.ps1 B67EBD6C, run-day.diff 3D0E8753 (repo-relative paths), make-run-day.ps1 4A96B0B9, launcher-ctl.ps1 6DDE3150, RUN-DAY.cmd B08645E9, STOP-LAUNCHER.cmd CE27332F, test-day.ps1 410FB2EC, README-DAY.md 9739BCF8. `test-day.ps1 -Name all`: 27/27 PASS (07:47:14). Agent 10: SAFE-IF (05:57); at 07:56 it checked these hashes, the run-day.diff headers and the test results, which closed its condition 1 (`build/agent10/t27/scrnsave-delta.md` section 5). Agent 11: not rated. See open item 1 | `build/agent5/day-draft/` |
| **W6 matrix** (finalized 22 Nov 21:16) | promoted by Agent 8 as `bench/agent8/run/matrix-window6.json` (E50D791B) and `bench/agent8/RUN-WINDOW6.cmd` (3F31CBA8). It ran twice overnight with `only=s0,p2,p2f,p2fc repeats=5` (21 runs each): `build/agent8/matrix/20261123-0009` and `-0313`, both runner exit 0. I have not read the results out. | `build/agent5/w6-draft/` (FINAL.txt, finalize-w6.ps1) |
| **M1** non-temporal upload copy (tasks #7, #18) | landed: in S4b / devoff4b-bin with its switch OFF, committed in rexglue-sdk 5350b1d (23 Nov 05:40). Correctness gate 22/22 + 18/18 groups (231,392 cases); G4 passed (notes L1022-L1033, L1111) | `build/agent5/s4-m1/` (m1-nontemporal-copy.diff EBECE86E, HASHES.txt), `bench/agent5/m1_copybench*.{cpp,ps1}`, `build/agent5/m1_copybench.exe` |
| **Upload path items 1-3** (task #4, 21 Nov): run-based SSSE3 untile, no staging zero-fills, SIMD byte swaps | landed in S1, on by default (notes L68, L300) | upload code in `DimensionsRecomp/rexlego/src/gpu_native/` (hashes at notes L420-L429) |
| **Upload batch 2**: `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD` A/B switch, 64 MB staging pool `LEGO_NATIVE_TEXTURE_STAGING_POOL`, Agent 4's edit (a) | landed in S2, both switches default OFF. Agent 10 cleared it (perf-notes/agent10-batch2-review.md section 9). Committed in DimensionsRecomp a0bdaa7. Devoff bins (NATIVE_GPU=OFF) contain none of it | same; S1 copies in `build/agent5/pre-batch2/` |
| Upload tests and benches | all PASS (notes L433-L467). Untile RGBA8 1024x1024 tiled 13.97 -> 1.77 ms (7.9x), R8 linear 55.7x, BC3 2.1-2.7x; byte swap 3.0-21.9x (notes L479-L507) | `bench/agent5/test_*.cpp`, `bench_*.cpp`, `*_reference.h`, `build.ps1`, `run_gpuaot_cpu.ps1`; results in `build/agent5/` (bench_*_v3*.txt, b2-*.log, gpuaot-b2fix/) |
| Upload timing matrices (do not edit: their hashes went to Agents 8 and 1) | `bench/agent5/matrix-native-uploads.json` 15BB7822: its s-rows ran (22 Nov 04:38, `build/agent8/matrix/20261122-0438`); the u0/u1/u2 arms did not. `-45.json` 114A0242 (16 runs, about 41 min) and `-x5.json` 62F58F2B (11 runs, about 28 min): PlanOnly OK, not run | `bench/agent5/matrix-native-uploads*.json` |
| Load phase (task #15), S4 slow frames (task #20) | done. Task #20: a-vol shows 1.87 invalidations and 3847 KB per frame, almost all from one 3844 KB buffer locked whole about once per frame (notes L873-L903) | `bench/agent5/load_phase.py`, `load-phase-test.*`, `s4_slowframe.py`, `matrix-s4-invalvol.json` 9D6A6F2C, `build/agent5/s4/` |

**Night launcher pins after task #26: nobody has to re-pin.** `bench/agent5/launch/status/pins.txt` (written 22 Nov
23:47:20) still lists run-matrix.ps1 FEDCEB13 and run-night.ps1 16B90FA8. It is only the record of that start:
run-night.ps1 writes it (L973) and never reads it back. Each start hashes the launcher, RUN-NIGHT.cmd and the runner
files again (L967, `Get-Pins` L195, file list L184-194), and the checks before and after each window (L688, L739, L900)
compare with those in-memory hashes. So the next RUN-NIGHT.cmd start pins run-matrix.ps1 1A522CDF and run-night.ps1
565D30D4, and it rewrites pins.txt once its start checks pass. A refused start leaves the old file as it is. This was
read from the code; the launcher was not started to test it. The only hard-coded pin in the launcher files is
make-run-day.ps1's `$Want` (565D30D4) in the day draft.

**Night launcher dry-run tests:** `build/agent5/launch-test/run-tests.ps1 -Group go|gate|hold|pin|run` (fake runner,
`-DryRunTag` mutex and status folder; results in `build/agent5/launch-test/results/`). A launcher refuses a start after
07:30 unless it gets `-StopAt`, because its default end (the next 07:30) would be more than 14 h away. So in the daytime
add `-StopAt 'yyyy-MM-dd HH:mm'` (option added 23 Nov, used for the go group). Run the `run` group in the evening
without it (t-run-ok expects the 07:30 default), and the `pin` group only while no launcher runs.

## 2. Open items

1. **Day launcher draft** (`build/agent5/day-draft/`; staged, not installed). A day session needs all three of Agent 10's
   conditions (`build/agent10/t27/day-draft-rating.md` L6-8):
   1. run-day.ps1 regenerated from the fixed run-night.ps1, test-day.ps1 re-run, and Agent 10's delta check: **done**
      on 23 Nov (see the day launcher row in section 1). Agent 10 closed this condition at 07:56
      (`build/agent10/t27/scrnsave-delta.md` section 5).
   2. Installed into `bench/agent5/day/` only while no night launcher runs, then the hashes compared (README-DAY.md,
      install section).
   3. Agent 11's rating. Not done yet.

   After the install, tell Agent 12 that day windows write to `bench\agent5\day\status\`, not to the night launcher's
   `status\` (N6). Known and harmless: N4 (launcher-ctl.ps1 L79-81 uses naive local time, so on a DST-change day the
   90 min / 14 h bounds can be off by an hour) and N5 (a night launcher closed with the X leaves its
   screensaver-saved.txt where the day launcher doesn't look; `\d` at run-day.ps1 L68 can give exit 3 instead of 2 for
   odd hand-typed input). run-day.ps1 is generated: any later change to `bench/agent5/launch/run-night.ps1` needs
   make-run-day.ps1's `$Want` pin moved, run-day.ps1 regenerated in `build/agent5/day-draft/` and
   `test-day.ps1 -Name all` re-run.
2. **The overnight windows are not read out.** No owner is assigned; W6 is my matrix. The seven output folders are
   `build/agent8/matrix/20261123-0009` and `-0313` (W6), `-0108` and `-0401` (W9), `-0155` and `-0451` (W5b) and
   `-0239` (W4c), each with `summary.md`, `results.csv` and `plan.txt`. Every runner exit was 0, and the quiet gate was
   strict for every GO. The launcher's record of the GOs, the gate values and the one refused GO (00:03:40, the
   SCRNSAVE bug) is in `bench/agent5/launch/status/`. C1's realised u needs W6's two untimed side runs, p2f and p2fc
   with the upload hash log (notes L1046; Agents 12 and 3).
3. **Upload A/B timing** needs a user window, and Agent 1 decides which matrix: `bench/agent5/matrix-native-uploads-45.json`
   (16 runs, about 41 min) or `-x5.json` (11 runs, about 28 min). Score the load phase with `bench/agent5/load_phase.py`
   (notes, "Session 3, task #15"). After the A/B, `upload_legacy_paths.h` and both switches can be removed.
4. **Manual scenes not done:** the first Toy Pad placement, the first level load, and TEST-20 in the default, legacy and
   pool modes.
5. **M1 follow-ups:** the copybench's GB/s part never ran, because it needs a quiet machine
   (`bench/agent5/m1_copybench.ps1`); an OFF/ON functional pair in the game; P3 must be rebased onto M1.
6. **Upload follow-ups** (notes L565-L570): pool the depth staging path (`textures.cpp:1417`); extend the run copier to
   volumes (`GetTiledOffset3D`) if s0 still shows `decode-content-hash` dominating.
7. **Pre-existing gpu-aot test failures**, not caused by my changes and left to the test owners: the
   `test_upload_buffer_pool` budget, `test_texture_upload_capture` and stale mocks.
8. **Agent 4's (b) `LookupBorrowed`:** reviewed, not applied. What a later session must check is at notes L555-L563.
9. **Out-of-date facts elsewhere:**
   - `build/agent5/s4-m1/NOTE.md` L3 still says the M1 diff is "staged only". It has landed (section 1).
   - `build/agent5/w6-draft/README.md` still names the placeholder bin and the 13-run plan. The promoted matrix
     (section 1) is the one in force. `build/agent5/w6-draft/matrix-w6.json` is now 8440B1E4..., which no other file
     records.
   - The old run-matrix.ps1 hash FEDCEB13... is still quoted in computed `pins.txt` files (the night launcher's re-pins
     itself, see section 1) and in staging records. Since task #26 the file is 1A522CDF...;
     `build/agent11/resume/facts-perfopt.md` L110 was updated to say so at 08:15.
10. **Cleanup:** see section 3.

## 3. Files that name the user folder (do not publish as they are)

Absolute paths that include the user folder appear in these files. Most are tool output, and several are hashed by a
HASHES.txt, so they were left as they are:
- `bench/agent5/launch/status/` and `status-dryrun/`, `build/agent5/day-draft/results/` and `status-dryrun/`,
  `build/agent5/launch-test/results/` and `gate-build-real.json`
- `build/agent5/w6-draft/FINAL.txt`, `finalize-console.txt`, `check/FINAL.txt`
- `build/agent5/s4-m1/syntax-*.txt`, `copybench-*.txt` (hashed in s4-m1/HASHES.txt)
- `bench/agent5/s4m1_mkdiff.py`, `bench/agent5/load-phase-test.csv`, `.json`
- `build/agent5/cc-*.log`, `test_staging_pool_v3.exe`, `gpuaot-*/`, `retention-*/`, `decode-poison*/`

None in: the night launcher set and its README, the day-draft scripts and README-DAY.md, `run-day.diff` (since task
#26), the W6 matrix and cmd, the four matrices, `build/agent5/scrnsave-fix/`, this file.

Safe to delete later (scratch or superseded): `bench/agent5/__pycache__/`, `bench/agent5/launch/status-dryrun/`,
`build/agent5/day-draft/status-dryrun/`, `build/agent5/w6-draft/check/` (a pipeline check with a stand-in bin),
`build/agent5/gpuaot-b2/` (superseded by gpuaot-b2fix, notes L469), `build/agent5/pre-item2/`, `pre-item3/`,
`build/agent5/s4-m1/bench-prev/`. Keep `bench/agent5/launch/status/` until the overnight windows are read out.
