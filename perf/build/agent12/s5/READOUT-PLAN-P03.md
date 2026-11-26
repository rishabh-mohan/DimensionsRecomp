# S5 Phase 0.3 baseline - read-out plan (M12, 2026-11-25)

Descriptive baseline: **devfinal2** (xenos, ship60) vs **nativefinal2** (nat60) vs **native4bp** (n4bp60), all at **cap60**, plus **nativefinal2 uncapped** (natU, info), on route `harness/routes/attract-long.txt` (gameplay attract, virtual pad). Exact commands: `READOUT-CMD.txt`; report template: `READOUT-TEMPLATE-P03.md`.
Tools: `s5_gates.py` (validity, per-run metrics) then `s5_readout.py` (arm summaries, contrasts). Gates: `S5-GATES.md`.

## 1. Run plan (recommendation to M8 / Overseer)

- **Arms as run** (M8's final `build/agent8/s5/matrix-s5-baseline.json`, sha8 57255790): **ship60** (devfinal2, cap 60, reference) x4, **nat60** (nativefinal2, cap 60) x4, **n4bp60** (native4bp-bin, MANIFEST C5181520, cap 60) x4, **natU** (nativefinal2, native_fps_limit=0 written explicitly) x2. That is 14 scored runs plus 3 unscored cold runs (`cold-ship60`, `cold-nat60`, `cold-n4bp60`, each ending at first frame + 160 s), 17 in total, in 4 round-robin rounds. There is **no xenos uncapped arm**; none is required. Missing (bin, cap) cells are listed as "not run" (or "no valid runs" if all were dropped) and their contrasts are skipped with a note. The uncapped arm therefore has no devfinal2 reference: natU is read via natU vs nat60 (info) only.
- **Settings:** span **120 s** from the **sustained ≥1500-draw anchor** (all frames ≥1500 for 1 s); a run ends at first frame + 270 s (warm-up 90 + window 180), about 274 s from launch; every run starts game-cache-cold in its own user_data_root (seed_xenos null); cooldown to < 72 °C before each run (timeout 90 s); sys.csv on; interactive desktop.
- **Run dirs** (run-matrix + common.ps1 New-RunDir): `build\agent8\s5\matrix\<yyyyMMdd-HHmm>\runs\<HHmm>-<tag>`. On a name collision `-r<i>` is appended to the dir name, so the tag is read from run.json, not from the dir name. Scored tags are `<arm>-r<k>` (k = round 1-4); unscored tags are `cold-<arm>` and `warm<j>-<arm>` (warm-ups: 0 in this matrix).
- **Native uncapped:** native_fps_limit=0 is passed explicitly, so **no `--native-default-ok`** (a cap of 240 on natU would correctly VOID).

## 2. Gates (per run)

Run the gates **once over the whole set** (set rules need every run). Pass the **scored run dirs only**: `--runs-root <matrix out>\runs` keeps the dirs whose run.json tag matches `^(?!cold-|warm\d+-).+-r\d+$` and lists the skipped ones in the header. `s5_readout.py` also drops tags `cold-*` / `warm<j>-*` as "unscored", as a second guard. In PowerShell 5.1, `>` writes UTF-16: use Start-Process `-RedirectStandardOutput` (exact commands: `READOUT-CMD.txt`).

```
python -B build\agent12\s5\s5_gates.py --runs-root <matrix out>\runs --span 120 --cap auto --route harness\routes\attract-long.txt --json build\agent12\s5\p03\p03-gates.json
```

- `--cap auto`: runner/cvar cap 60 → cap60 arm; else uncapped arm (cap ≠ 0 → VOID). If the runner records no cap at all, run the gates per arm with `--cap 60` / `--cap none` instead (one call per cap; the set rules then work per cap, which is fine).
- **VOID** (dropped): runner status ≠ OK, valid_timing false or runner excluded (as score3d); crash/unclean close or own-pid dump (foreign dumps are info), seeded, no 3D (no frame ≥600) or no anchor, SHORT or span ≥5 s past end of 3D, input script failure, script dead before window end or press in window, HW brake share > 5 %, host VOID (AC off, battery saver, screensaver, user input, game not foreground, game not alive, scheme/overlay change), cap60 run > 61.5 fps or cap ≠ 60, uncapped run with cap ≠ 0.
- **FLAG** (kept in primary, dropped in the sensitivity variant): no cooldown record / timed out, thermal within-arm outlier (> 0.25 from arm median), host nongame > set median + 1 core, sys.csv missing (NODATA), anchor late / unsustained, runner window start ≠ gate anchor by > 1 s, axis misalignment > 3 s, uncapped run that looks capped at 60, cap NODATA (no window frames / frame-time sum 0; such a run has no fps and is dropped from the read-out as "no metrics").
- **Info only (never void):** cap60 run below 57 fps = "GPU-bound" (expected for xenos at ~34-46 fps); thermal-limited share (xenos 0.5-0.8 SwThermal is the steady state).

## 3. Metrics (per run, scoring window only)

| metric | definition |
|---|---|
| fps | window frames / window seconds |
| median, p99 ms | frame time; p99 nearest rank |
| 1 % low ms | mean of the slowest max(1, n//100) frames (higher = worse) |
| max ms | slowest frame |
| frames ≥100 / ≥250 ms | count and per minute |
| GPU util %, clock MHz, W, temp °C | median of 1 Hz NVML samples in the window |
| thermal share | share of window samples with SwThermal or HwThermal (0x20 \| 0x40) |
| power-cap share, start temp, nongame cores | covariates |

## 4. Read-out

```
python -B build\agent12\s5\s5_readout.py build\agent12\s5\p03\p03-gates.json --ref devfinal2 --vs native4bp:nativefinal2 --json build\agent12\s5\p03\p03-readout.json
python -B build\agent12\s5\s5_readout.py build\agent12\s5\p03\p03-gates.json --ref devfinal2 --vs native4bp:nativefinal2 --exclude-flagged --json build\agent12\s5\p03\p03-readout-noflag.json
```

- **Arms:** (bin dir basename, cap arm): devfinal2-bin/60 = ship60, nativefinal2-bin/60 = nat60, native4bp-bin/60 = n4bp60, nativefinal2-bin/none = natU. Missing cells (e.g. devfinal2 uncapped) are printed as "not run" and never required. Gate verdict counts per arm (PASS/FLAG/VOID, scored runs) are printed in the header and stored in JSON `verdicts`.
- **Per arm (CF1 method):** median per metric, 95 % percentile bootstrap CI of the median (20000 draws, seed 1), range, n. n 1 → no CI.
- **Contrasts:**
  1. **Primary: nat60 vs ship60** (nativefinal2-bin/60 : devfinal2-bin/60, "bin vs ref"): difference of medians, as % of devfinal2, with bootstrap CI; plus a paired-by-round log-ratio t-CI as cross-check (rounds with both arms valid).
  2. **Secondary: n4bp60 vs nat60** (native4bp-bin/60 : nativefinal2-bin/60, "secondary native4bp:nativefinal2", from `--vs`): does the missing-draw fix cost or gain fps / p99? Same CI method, paired by round.
  3. **Info:** natU vs nat60 ("uncapped vs cap60 (info)", n 2 vs 4); n4bp60 vs ship60 is also printed ("bin vs ref") and is info only. Uncapped has no devfinal2 arm: the read-out prints "bin-vs-ref contrast not available".
- **Wording:** "A higher" / "A lower" only when the CI excludes 0; otherwise "not resolved". Never "equal"/"no difference"; no equivalence claims. Tails (p99, 1 % low, max, ≥100/≥250 ms) are noisy at n 3-5: report them descriptively with ranges.
- **Variants:** (a) all valid runs (VOID dropped) = primary; (b) `--exclude-flagged`; (c) optional `--anchor-mode first` gates run to show anchor sensitivity (xenos may start ~20 s early in the pre-3D phase; treat as info).
- **Report table:** per cap: arm medians [CI] for fps, p99, 1 % low, ≥100/≥250 per min, max, GPU util/clock/W, thermal share; contrast row (% of devfinal2 [CI], paired CI); void list with reasons; flag list with reasons.
- **Host-load confound (added 18:40 after M16's finding; POST-HOC, NON-GATING):** `s5_confound.py p03-gates.json --vs nat60:ship60 --vs n4bp60:nat60 --vs n4bp60:ship60`. Per run: nongame cores mean, effective CPU MHz mean, MsMpEng cores (sys.csv top_cpu), game cores, thermal share / GPU temp, per-second corr(nongame, frames/s), and low-load seconds (nongame < 4 cores) fps / median vs high-load seconds. Per arm: median [range]. Confound check: PRESENT when the arm nongame medians differ by > 1.0 core or the eff-MHz medians by > 10 %. Post-hoc low-load contrasts: difference of arm medians with a bootstrap CI as above. It never changes a gate verdict or a contrast; s5_gates.py is unchanged. The read-out states the confound next to every arm contrast and never says "n4bp X % slower" without it.

## 5. Preconditions / open items

- Runner contract (S5-GATES.md §assumptions 1-7): sys.csv with nongame_cores, cooldown record, effective cap, window_start_s (sustained rule), gpu.csv t_s from launch, -Seconds ≥ 270, interactive desktop.
- **Native end of 3D not yet observed** (smoke closed at 240 s). The first native P0.3 run shows whether span 120 stays inside the 3D; if the span gate flags/voids native runs, shorten to the span the data allows and rerun the gates on the whole set (re-scoring is offline; no rerun of the game needed).
- Thermal is a covariate: compare GPU clock/W/temp medians next to fps; do not adjust fps for it.
