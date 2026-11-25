# #33 pop-in opt-in: first test bin and test plan (M6, session 3, S3T-6)

Paper only. Nothing here is built or run. Builds need the Overseer's LOAD GO (M2 only); game runs need RUN GO.
WS = `games/lego-dimensions-recomp`; paths below are relative to WS. Design and risks: `DESIGN.md` (§7, §8); rating: `build/agent10/t27/r33-popin.md`.

## 0. Files

| File | sha256 | What |
|---|---|---|
| `s33-popin-nohunk5.patch` | 57CFA8ADF1E9007954063A87F406056BB137E2D2D8F2484940BD4E1ABF3704AF | **The first test patch**: rated `s33-popin.patch` (0D23024484CCDEE1…, unchanged) minus hunk #5 (Agent 10 S1), plus N1's 3-line threading comment on `AwaitPipelineCreation()`. 10725 B, 211 lines, LF. Made by `make_nohunk5.py`. |
| `APPLY-CHECK.txt` | — | `apply_check.py`: PASS. Scratch copies of the 4 files from `git show 5350b1d:<path>`, `git -c core.autocrlf=false apply --check/apply/-R --check` exit 0, 4 "Checking patch" lines, no "Skipped patch", no offset/fuzz, LF only. Differs from the full patch only by N1 (pipeline_cache.h) and hunk #5 (`CanEndSubmissionImmediately` byte-identical to 5350b1d). |
| `s33-diagd-on-nohunk5.patch` | 6CF9377E9F09322B88C5870D2F3A9F62AA92FFED9D7C04EB9463C870A4CD746F | Diagnostic (d), stacked on nohunk5 (command_processor.cpp only). **UNRATED.** Cvar `d3d12_resolve_after_drop_log` (bool, false, kRequiresRestart). |
| `s33-popin-nohunk5-diagd.patch` | 797E614284B642267CCB1539AADBC5AD79362467FDD51F13143DBCA287C6DAC0 | nohunk5 + (d) in one patch vs 5350b1d (4 files). **UNRATED.** `DIAGD-CHECK.txt`: PASS; stacked result = combined result. |
| `matrix-s33-draft.json` | 5F14090BB368FA7A… | Agent 8 run-matrix draft (title-idle rows, timing later). `run-matrix.ps1 -PlanOnly` exit 0 (`matrix-s33-planonly.txt`). |
| `harness-s33.json` | 4E30E1353AA87DAE… | Arm table of the harness (cold attract) rows; `--matrix-json` for the kit's harness mode. |
| `expect-s33.json`, `RUN-S33-LOGDIFF.cmd` | see SESSION3.md | Logdiff rules and wrapper (w6 kit). |
| `s33_fields.py` | 57A938D54929CF04… | Slow-frame #33 fields per run (dropped draws, late drops, forced waits ms). Test: `make_test_fields.py` PASS. |
| `diagd_report.py` | 2673214E39B70B73… | Diagnostic (d) report (taint/heal per dest). Test: `test_diagd_report.py` 14 OK. |

Patched result files (LF) for a copy-based build, from `scratch/nohunk5/` (with (d): `scratch/diagd-combined/`):

| File | nohunk5 sha256 | + (d) |
|---|---|---|
| include/rex/graphics/d3d12/pipeline_cache.h | 0BAF28BE633759CD0F9A1A3672CD86D2D75DDE78EC4662DA8D4B5ED9514CF81F | same |
| src/graphics/d3d12/command_processor.cpp | 00EA93D3E9115B01FE6C45A28C39CAB72FF53716A11090602B9FBAD05F28E0FA | 97257A204152DF1BE26C60197146DBC63D0E07D8B7D57B5C1E1DE2C115EDF49D |
| src/graphics/d3d12/pipeline_cache.cpp | C4CB51CC6D2A6429637115F605FF10279FCE59AEDCF8BBC6E2195F92615C86C6 | same |
| src/graphics/frame_stats.h | 9F3C4F9DC58DCA5DF1AB946056ED565C706BC336E652C854132E53FE5B048970 | same |

## 1. Build (M2, after LOAD GO)

1. Source = the SDK tree devoff4b was built from (5350b1d). Never in the live `DimensionsRecomp/rexglue-sdk` worktree in place (BRIEF rule 4): use M2's build copy.
2. Before applying: `git hash-object` of the 4 target files must be the 5350b1d blobs 7e81db3b1402 (pipeline_cache.h), 6f21eb6f220a (command_processor.cpp), 55e9f02ef54b (pipeline_cache.cpp), 8c169b418cb5 (frame_stats.h). Any other blob: stop, report.
3. Apply, one of:
   - copy the 4 files from `build/agent6/s33-popin/scratch/nohunk5/` (or `scratch/diagd-combined/`) over the build copy, then check the sha256 table above; or
   - `git -c core.autocrlf=false apply --verbose --directory=<prefix> <patch>` from the repo that really contains the tree. **Trap (RESUME §7 step 3):** in a tree without its own `.git`, `git -C <tree> apply` uses an outer repo, prints "Skipped patch" for every file and exits 0 having applied nothing. Require 4 "Applied patch … cleanly" lines and zero "Skipped patch", then check the sha256 table. Outside a repo with `.gitattributes`, `core.autocrlf=false` is required (the system gitconfig sets autocrlf=true and git apply then writes CRLF).
4. Stage `build/agent2/devoff4b-s33-bin` (provisional name; with (d) as a second bin: `devoff4b-s33d-bin`) with its MANIFEST.txt. Fresh bin dir: never copy `cache/` or seeds from devoff4b-bin.
5. R8 (compile risk) closes only with this build. A compile error in the patched lines goes back to M6 (and then to Agent 10 for a re-rate if the fix changes code).

**Decision for the Overseer:** (d) in the first bin (one bin, row 1 then proves identity for both cvars off; needs Agent 10's rating of the (d) patch first) or a second bin later (first bin = rated code + N1 comment only). DESIGN §9: (d) is not needed for the opt-in test bin, only before #33 is suggested as a setting.

## 2. Runs

All rows below are FUNCTIONAL (hidden desktop) except row 3, and need RUN GO. One game at a time; check `perf-notes/WINDOW-HOLD.txt` first. Harness command per arm of `harness-s33.json` (run from WS):

```
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir <bin> -Seconds <seconds> -GpuLog ^
  -Tag s33-<arm> -RunsRoot build\agent6\runs-s33 -InputScript harness\routes\attract-long.txt -Cvar "<cvars;joined>"
```

e.g. `-BinDir build\agent2\devoff4b-s33-bin -Seconds 540 -Tag s33-onsf -Cvar "slow_frame_log_ms=1;d3d12_pipeline_creation_no_wait=true"`.
Every harness run is cold (fresh run dir and user/cache) unless `-SeedXenos` is given.

Order: row 1 first (Agent 10 condition 2). If row 1 fails, stop: nothing else runs.

| # | Arms (harness-s33.json) | Pass | Stop / watch |
|---|---|---|---|
| 1a | `base` vs `off` (no extra cvars) | Same code path: logdiff NEW 0 / MORE 0 / GONE 0 / ONLY 0 beyond run-to-run noise; W/E/C equal to base; exit 0 via WM_CLOSE; no `d3d12_pipeline_creation_no_wait` text at all; Xenos storage (`user\cache\shaders\shareable\*.xsh/*.xpso`) sizes equal or within the run-to-run spread of two base runs; pm, frames and first-frame time within noise. | Any `d3d12_pipeline_creation_no_wait` line, a new warning/error key, a dump, STUCK-LOCK in a new site. |
| 1b | `basesf` vs `offsf` (`slow_frame_log_ms=1`) | The slow-frame key differs only by the 3 appended fields (one ONLY + one GONE key: NOTE, expected). `s33_fields.py offsf`: `dropped draws` > 0 only in frames that have misses or follow them within one submission; `forced pipeline waits 0.0 (0x)` in every line. | forced waits > 0 with the cvar off = bug. |
| 2 | `offsf` (ref) vs `onsf` | INFO line exactly once; frames ≥ 250 ms at the scene points (first 3D frame, H0, the 67-miss burst ~H0+21 s, the 12.4k shot) drop to the non-compile residue (PRE / heavy / fence-wait / depth-only classes in `attrib.py`); `dropped draws` > 0 after misses; forced waits ≈ 0 **read by ms, not calls** (N2); pm unchanged. | `late drops` > 0 (drops long after a burst: failed pipeline); forced waits ms > 0 (memexport/query pipelines in a burst); any DXGI / device-removed / debug error. |
| 3 | user, visible desktop, `onsf` then `offsf` | The user judges pop-in at the first 3D frame, the load transition and the 12.4k shot; no **persistent** wrong textures. | Persistent wrong UI panel / reflection / portrait / minimap = lost resolve source (DESIGN §7): stop, keep the cvar off. |
| 4 | `onstop` ×5 (`-Seconds` 203/205/207/209/211) | Each run: exit 0 via WM_CLOSE, no dump, no WER, no hang in the Shutdown join. A run counts only if its log has pipeline misses within ~2 s before `Window closing, shutting down` (else re-run with a shifted -Seconds). | A wedge: the W9 watchdog line `Shutdown wedged past the close request; hard-exiting.` is a NOTE in the kit; in an ON run against none in OFF, report it. |
| 5 | `offwarm` vs `onwarm` (both `-SeedXenos <offsf run>\user\cache\shaders\shareable`, same bin) | Same as offwarm apart from at most a few dropped draws right after the storage load. | Drops long after boot. |
| 6 | `gthr0`, `gasync`, `gbindful` | Exactly one `d3d12_pipeline_creation_no_wait ignored` WARN (W = base + 1, NOTE), no INFO line, otherwise row-1 behaviour (`forced pipeline waits 0.0 (0x)`). | INFO line in a gate arm. |
| 7 | optional: `onsf` + D3D12 debug layer | No root-signature/PSO mismatch, no draw without PSO. | R6-type messages. |
| (d) | `offd` vs `ond` (bin with (d)) | Measurement, not pass/fail: per-dest taints, heal latency, dests still tainted at end. Frontbuffer-like dests taint and heal every frame; the danger is dests **never healed** (in `ond` but not in `offd`). Required before #33 is suggested as a setting (Agent 10 S2, DESIGN §9 item 5). | `diagd_report.py` WARN (counter drift) = bug in the diagnostic, exit 1. |

Hunk #5 is not in this bin. It can become its own arm (own bin) after row 2 is in.

### Row 3 at the visible desktop

Only with the user present and agreeing, after rows 1-2 pass. From the pane, on the user's desktop (agy-grid's sanctioned path):

```
node "C:\Users\<user>\.vscode\projects\agy-grid\src\desktop.js" powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\agent2\devoff4b-s33-bin -Seconds 540 -Tag s33-row3-on -RunsRoot build\agent6\runs-s33 -InputScript harness\routes\attract-long.txt -Cvar "slow_frame_log_ms=1;d3d12_pipeline_creation_no_wait=true"
```

then the same with `-Tag s33-row3-off -Cvar "slow_frame_log_ms=1"`. The pad route drives the game; the user only watches (first 3D frame ~launch+151 s, H0 ~launch+180 s, burst ~H0+21 s, the 12.4k shot later). Record the user's verdict verbatim in `SESSION3.md`. Never run while the user is playing Minecraft without asking.

## 3. Checks (logdiff commands)

Run each at BelowNormal, one process at a time. `RUN-S33-LOGDIFF.cmd` wraps `w6_kit.py` with `--expect build\agent6\s33-popin\expect-s33.json`; exit 0 no FAIL, 1 FAIL, 2 usage, 3 HOLD.

```
:: row 1a (harness mode)
build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd --run base=<base dir> --run off=<off dir> --ref off --matrix-json build\agent6\s33-popin\harness-s33.json --out build\agent6\s33-popin\out-row1a
:: row 1b, 2, 6
build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd --run basesf=<dir> --run offsf=<dir> --run onsf=<dir> --run gthr0=<dir> --run gasync=<dir> --run gbindful=<dir> --ref offsf --matrix-json build\agent6\s33-popin\harness-s33.json --out build\agent6\s33-popin\out-row2
:: row 4, 5
build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd --run offsf=<dir> --run onstop=<dir1> ... --run offwarm=<dir> --run onwarm=<dir> --ref offsf --matrix-json build\agent6\s33-popin\harness-s33.json --out build\agent6\s33-popin\out-row45
:: a run-matrix.ps1 folder of matrix-s33-draft.json (timing later, or -Quick functional)
build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd build\agent8\matrix\<folder> --ref off
build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd build\agent8\matrix\<folder> --ref offsf --out build\agent6\s33-popin\out-<folder>-sf
```

Reading the kit: `--ref` is always a patched cvar-off arm, so the slow-frame text is the same and only counts move; MORE/GONE slow-frame keys between onsf and offsf are the measurement. Benign hard-exit race (no `Execution complete`, `Title terminated; hard-exiting process.`, exit 0) = INFO. `Shutdown wedged past the close request; hard-exiting.` = WATCHDOG NOTE (seen once so far: W9 20261123-0108 `0128-off-r2`, an OFF run on the base bin; so one such NOTE alone is not a #33 finding).

Field and scene reports:

```
python -B build\agent6\s33-popin\s33_fields.py --arm offsf=<dir> --arm onsf=<dir> --out build\agent6\s33-popin\out-row2\fields.txt
python -B build\agent6\attract-stalls\attrib.py --thresh 250 <offsf dir> <onsf dir>
python -B build\agent6\attract-stalls\slowframe_join.py <onsf dir> --min-ms 250
python -B build\agent6\s33-popin\diagd_report.py --arm offd=<dir> --arm ond=<dir> --out build\agent6\s33-popin\out-diagd\report.txt --json build\agent6\s33-popin\out-diagd\report.json
```

Agent 3's s4b kit (if a row goes through it; N3): ON and gate rows add `--allow-new d3d12_pipeline_creation_no_wait`; OFF rows never.

```
python -B build\agent3\s4b\s4b_check.py --cand <onsf dir> --base <offsf dir> --allow-new d3d12_pipeline_creation_no_wait --out-dir build\agent6\s33-popin\checks
python -B build\agent3\s4b\s4b_check.py --cand <off dir> --base <base dir> --out-dir build\agent6\s33-popin\checks
```

## 4. Agent 10's conditions (carried)

1. Default false, `kRequiresRestart` (in the patch). 2. Row 1 identity first. 3. The user's row-3 review gates any recommendation. 4. No hunk #5 in the first bin (done). Plus S2: (d) before #33 is suggested as a setting. N1 applied (comment only, needs a re-rate glance), N2/N3 in this plan, N4 (`build/agent2/PENDING-DIFFS.md`) is M2's file.
