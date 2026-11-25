# CF2 read-out (M8, session 3): shipped native default (nf) vs W8a's mc

Written 2026-11-25 ~12:35, strictly per `confirm/READOUT-PLAN.md` (18F69B57). M10 cross-checks before use.

- Window: out dir `build/agent8/matrix/20261125-1159` (results.csv 65C4B48F). 13 runs = 1 cold (nf, unscored) + 6 rounds × {nf, mc}.
- Script: `confirm/readout_cf.py` 9D75B69E (re-run 13:49 after the CF1 NIT: JSON keys `a`/`b` renamed `a_med`/`b_med`, C2 header note added; numbers unchanged vs B76E636C). It imports `confirm/readout_night.py` 1A5F9BE0, a byte copy of the READOUT-NIGHT code M10 confirmed (25BF9B1C).
  - Bootstrap: **10 000 draws, seed 1**, percentiles 2.5/97.5.
  - Command: `python -B readout_cf.py --window CF2 --hash-bins --json readout-cf2.json build\agent8\matrix\20261125-1159`
  - Full output: `confirm/readout-cf2-tables.md` 23BDE27F, with the per-run table, every variant and the order table. JSON: `readout-cf2.json` 546CC3BE.

## Headline

**nf reproduces mc in the weak form** (S1: "equal" or "not shown different" on all four verdict metrics). Only process cores is "equal". Basis: rounds 2-6, n = 5 per arm, no void, no M12 flag.

| nf vs mc | nf | mc | nf vs mc | 95 % CI | margin | claim | paired rounds (nf < mc) |
|---|---|---|---|---|---|---|---|
| fps mean | 458.8 | 459.9 | -0.2 % | [-0.8, +4.2] | ±3 % | not shown different | +0.7 % [-2.2, +3.8] (3/5) |
| p99 ms | 3.202 | 3.098 | +3.4 % | [-39.8, +11.8] | ±5 % | not shown different | -4.4 % [-26.7, +24.8] (2/5) |
| 1 % low ms | 3.566 | 3.427 | +4.0 % | [-44.7, +23.7] | ±5 % | not shown different | +0.2 % [-30.3, +44.0] (2/5) |
| process cores | 1.829 | 1.835 | -0.3 % | [-4.7, +3.3] | ±5 % | **equal** | -1.3 % [-3.7, +1.3] (3/5) |
| median ms (info) | 2.148 | 2.148 | +0.0 % | [-0.7, +0.1] | ±3 % | (info) equal | -0.2 % (3/5) |

- Arm value = median of the per-run values. The fps column is the median of per-run fps means. Per-run fps comes from frames.json, over the 50 s window.
- **Why the tail CIs are wide:** one run, 1205-mc-r2 (round 2, first in its round), is slower: fps 439.5, p99 4.434, 1 % low 5.097. The other four mc runs are 459-462 fps with p99 2.84-3.10. Two nf runs, 1209-nf-r3 and 1217-nf-r5 (both first in their round), have 1 % lows of 4.24 and 3.98 ms. With n = 5, these runs stretch the bootstrap CIs of the median beyond ±5 %. So the tails read "not shown different", and the data does not support "equal" there.
- **Order (N1):** in both arms the first-in-round runs have worse tails.
  - nf: 1 % low 4.108 ms first vs 3.252 later.
  - mc: 3.475 vs 3.181.
  - nf was first 2×, mc 3×.
  - fps differs by less than 1 % between positions. This position effect explains the tail spread better than an nf-vs-mc difference does.

## Variants

| set | fps mean | p99 | 1 % low | cores |
|---|---|---|---|---|
| **rounds 2-6 (headline)** | -0.2 [-0.8, +4.2] n.s.d. | +3.4 [-39.8, +11.8] n.s.d. | +4.0 [-44.7, +23.7] n.s.d. | -0.3 [-4.7, +3.3] equal |
| rounds 2-6 without M12 flags | same (0 flagged) | | | |
| rounds 1-6 (side note, never decides) | +0.1 [-0.6, +2.6] equal | -0.5 [-25.9, +9.8] n.s.d. | -0.5 [-29.5, +19.9] n.s.d. | -1.1 [-7.5, +1.6] n.s.d. |
| rounds 3-6 (info: round 2 is on the plateau) | -0.5 [-0.8, +0.3] equal | +6.9 [-4.5, +12.4] n.s.d. | +14.0 [-4.1, +28.3] n.s.d. | -1.1 [-4.9, +2.3] equal |

(nf vs mc, % of mc, 95 % bootstrap CI; n.s.d. = not shown different.) No variant changes the verdict. In rounds 3-6 (n = 4, without mc-r2) the nf tail point estimates are worse, +6.9 % (p99) and +14 % (1 % low), but both CIs include 0. If the Overseer needs the tails settled, more rounds are the fix. Changing the scored set after the fact is not.

## Preconditions (plan section 1)

- **K1:** final_gate F5, F5w and F7 PASS on nativefinal-bin (F1-F7 8/8 PASS, per the Overseer; fx rulings in `build/agent4/session3/`). Bins are pinned in BIN-PINS FE4CD4FF.
- **K2:** `confirm/stage/stage-CF2-115417.txt` C2542EA4: `mode: RECHECK`, `result: OK`. Its line 66 "FUNCTIONAL ONLY" is the stager's own non-interactive preview, not the window.
- **K5:**
  - Runner preflight (`bench/agent5/day/status/runner-CF2-1154.txt`):
    - `desktop WinSta0\Default -> interactive desktop: timing can be valid`
    - `LogonUI not running`
    - `power AC (Win32_Battery status 2, charge 100 %)`
    - `builds none (...)`
    - `screensaver none`
    - both bins `ok (MANIFEST.txt)`
    - quiet gate `STRICT` at 11:59:37 (MsMpEng 0.01/0.01/0.01)
  - Launcher log:
    - 11:54:36 GO ACCEPTED (sha256 ok)
    - 11:54:36 WINDOW-HOLD written
    - 11:59:38 window START
    - 12:26:04 END, runner exit 0 (all runs OK), 26.4 min
    - 12:26:04 HOLD removed
  - M3 (forwarded by the Overseer): `build/agent3/s4b/logs/queue.out.txt` 4391CE28, last written 11:23:04.
    - `11:22:07 DONE s33offd ...`
    - `11:22:07 idle; waiting for: [f10aL,f10bL,s33stop6,s33stop7,s33ond]`
    - `11:23:04 HOLD or PAUSE file: no launch; waiting`
    - nothing after that (PAUSE since 11:23:02)
    - postcheck last line 11:22:27; hostload.ps1 ended at 12:00; M3 game processes 0.

## Which runs count (K4)

- **Counted:** all 12 scored runs. Rounds 2-6 give 5 per arm, so n ≥ 4 holds. The cold run 1159-cold-nf is unscored by design.
- **Proof, all 13 runs PASS:**
  - Every run: MANIFEST.txt sha matches the pin (nf D7C7B706…, mc B63769FE…); the staged exe and DLL shas in the run dir match the MANIFEST (`--hash-bins`); bin_dir matches the arm.
  - nf: env_set has LEGO_NATIVE_FRAME_METRICS and no SHADER_MISS_CACHE; `check-defaults.py` D9936C56 `--mode native-old` PASS. The miss-cache ON line is present, so the S1 exception was not needed.
  - mc: env_set has MISS_CACHE=1 and FRAME_METRICS; no bad strings.
- **Functional, all PASS:** exit 0; no WER, dump or fatal line; STUCK-LOCK 0.
  - Shader-miss warnings: 26 in every run (both arms, cold included), as in W8a.
  - "Level reached" reads as "reached the 50 s window": W8a's timed route is the light route, with no level.
- **Other checks:**
  - sys.csv has 31 columns on every row, in all 13 runs.
  - Runner exclusion flags: none. Every run carries only the info flag `light_share_high`, which is expected on this route and is not an exclusion.
  - Void list: no run void, no arm void.
- **M12 host-load gate** (w6_env_record formula: util × 12 / 100 − game cores): scored-run median 3.58 cores, threshold 4.58, range 3.44-3.95. **0 flagged.**
- **GPU plateau:** gr_mhz median 1740 MHz in every scored round (r1-r6), so round 2 is on the plateau (criterion ≥ 97 % of the rounds 3-6 median, fixed before the data was read). The WC "~1500 MHz" figure belongs to the Xenos route; native runs sit at 1740 on this route. CPU eff MHz: nf 2207, mc 2184 (arm medians).

## S2 (context only)

CF2 has no WC counterpart. W8a's mc vs n0 (median about -29 %, fps about +44 %) is context. CF2's mc arm reproduces W8a's mc level: 459.9 fps here vs 461.4 in W8a rounds 1-6, by the same script. This window is not pooled with W8a.

## Other observations (not verdicts)

- **Thread CPU per frame**, busy % × window / frames, headline runs, medians: Main XThread 1.552 (nf) vs 1.547 (mc) ms/f; rex::thread::TimerQueue 0.502 vs 0.515 ms/f. The next-busiest XThreads have per-run tids, so they can't be paired across runs. No thread is named as the render thread in native threads.csv, so none is claimed as the render thread.
- **Run-timing fix item 7:** run.json `sys_sampler.stop_line` is set in 13/13 runs. Verified.
- **ProcEvery re-check:** sys.json has no `sample_ms_max` key under `run`, so this read-out did not check it. It stays open.

## Deviations from the plan

1. **File name:** `confirm/READOUT-CF2.md` (the Overseer's instruction) instead of section 6's `READOUT-CF.md`.
2. **"Level reached":** read as "reached the 50 s window", since the timed route has no level.
3. **Plateau criterion:** "≥ 97 % of the rounds 3-6 median" was set at 11:40, before the window ran. The plan only says "~1500 MHz in WC".
4. **Render-thread ms/f:** given as the busiest threads by name, because the native threads.csv names no render thread.

sha8 of this file: see the report to the Overseer.
