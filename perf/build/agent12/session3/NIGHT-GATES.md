# Night gates, session 3 timed windows (M12, 2026-11-25 06:28-06:35)

Method: `build/agent12/w6-gates/run_gates.ps1` (the w6-gates method) + M6's `build/agent6/w6/w6_kit.py` (logdiff + extra), one at a time, BelowNormal, read-only on the matrix dirs.
Script `night/run-night.ps1`, log `night/run-night.log` (DONE 06:29:28). Outputs: `night/gates-<tag>.txt|.json`, `night/kit-<tag>.txt`, `night/kit-<tag>/`.
Pre-checks: `perf-notes/WINDOW-HOLD.txt` absent. Window-log grep (`NOT killed|could not kill|could not be killed|runner stopped: NO|process list could not be read|left over from the window`) over the window-*.log, runner-*.txt and log.txt files in `bench/agent5/launch/status`: **0 hits**.

Inputs: WC1/WC2/WC3 used `--one-bin --side build\agent3\runs\20261125-025013-f10b3-p2fc-level --gate-a build\agent3\runs\20261125-022357-s4b-LV-p2fcv-level-long` (both rows gated PASS earlier, ROWS-RESULTS.md). W8a used `--one-bin`; W10 used no flags (2 bins). Kit `--ref s0` (W8a: `--ref n0`), default expect-w6.json.

## Per-window table

| window | dir (build/agent8/matrix/) | matrix sha16 | runs | run_gates | kit | quiet / non-game load | verdict |
|---|---|---|---|---|---|---|---|
| WC1 | 20261125-0315 | 00E3EE97A18A3B31 | 17/17 | exit 0: G2-G5 PASS, G8 NEW 0, G9-G12 PASS (G1 MANUAL, G6/G7 CODE) | exit 0; STUCK 0; watchdog 0; NOTEs only | STRICT; 3.04-3.70 cores, 0 flagged | **PASS** |
| W8a | 20261125-0359 | A06E5E3AAEE25B07 | 15/15 | exit 1: G2, G3, G8, G11, G12 PASS; **G9 FAIL** (tool artifact, see below); G10 CHECK; G4-G7 n/a | exit 1 (same artifact); STUCK 0 | STRICT; 3.33-4.66 cores, **1 flagged** (mc r2, 4.66 > median 3.64 + 1) | **PASS after a hand override of G9 (needs Overseer acceptance) + CHECK mc r2** |
| WC2 | 20261125-0440 | D0AE477F26E21A7A | 17/17 | exit 3: **G8 CHECK** (1 NEW line, see below); G2-G5, G9-G12 PASS | exit 0; watchdog 1 (0504-c1np-r3, NOTE benign); STUCK 0 | STRICT; 3.13-3.97 cores, 0 flagged | **PASS** (G8 CHECK cleared by hand) |
| W10 | 20261125-0519 | 289F4B4F008FA0C8 | 13/13 | exit 0: G2 PASS (2 bins), G3, G8 NEW 0, G9-G12 PASS; G4-G7 n/a | exit 0; STUCK 0; cg26 logdiff 0/0/0/0/0 | STRICT; 3.11-3.88 cores, 0 flagged | **PASS**; r26: no cg26 functional FAIL, so the arm stands |
| WC3 | 20261125-0551 | 00E3EE97A18A3B31 (= WC1) | 17/17 | exit 0: all PASS, same as WC1 | exit 0; watchdog 1 (0619-s0-r4, in the s0 reference arm, so not NEW); STUCK 0 | STRICT; 3.06-4.30 cores, 0 flagged | **PASS** |

## Details

**W8a G9 / kit FAIL = tool artifact.** The arm env is `LEGO_NATIVE_FRAME_METRICS=<run>\native-frames.csv`. Neither run_gates.py nor w6_kit expands the `<run>` placeholder, so both see a mismatch. Hand check over all 15 runs: the frame-metrics path is the run's own dir + `\native-frames.csv` and the file exists; `MISS_CACHE=1` is set in mc runs only and absent in n0. **BAD 0.** This is a hand override, not a waiver; the Overseer decides whether to accept it.
**W8a G10 CHECK:** no proof line is known for native_fps_limit / native_settings_frontend. These are common-set cvars and G9's cvar comparison matched apart from the env path.
**W8a kit NOTEs:** W/E/C 66/0/0 vs the expected 40 in all 15 runs (native baseline, the same across arms). The 0417-n0-r5 and 0419-mc-r5 logs end with Toypad lines (exit 0). INFO: 0421-mc-r6 hit the benign Execution-complete race.
**W8a G12 flag:** mc r2 non-game load 4.66 cores (median 3.64 + 1). The gate PASSes; record the run as CHECK, or drop it from the mc read-out if the margin matters.

**WC2 G8 CHECK:** the 1 NEW line is the watchdog line `Shutdown wedged past the close request; hard-exiting.` in 0504-c1np-r3. The kit rates it a NOTE (benign, after WM_CLOSE): it comes after the timed window, so the timing is unaffected. It is a single occurrence; WC3 has the same line in s0 r4 (the reference arm), so it isn't tied to c1np.

**W10 / M10 r26:** the cg26 arm (devoff4b-cg26-bin) has G2 PASS, G3 13/13, G8 NEW 0, kit STUCK 0 and a 0/0/0/0/0 logdiff. Together with cg26b0 and cg26L (PASS, ROWS-RESULTS.md) there is **no cg26 functional FAIL**, so the arm is not voided.

**Kit coverage:** the default expect-w6.json has no rules for the win3, c1np, n0, mc and cg26 arms, so they get "unruled" NOTEs (the win3 ONLY keys are the expected Host timer / precise wait / back-off lines). The kit FAIL/STUCK/watchdog checks still ran on every arm.

## Open
- run_gates.py could expand `<run>` in arm env, which would turn the W8a G9 into a mechanical PASS. Not done: it needs the selftest and a HASHES refresh. Offered to the Overseer.
- G1 (every switch rated) is MANUAL in all windows; that rating belongs to the read-out owner.

## 06:35 update: run_gates <run> fix (Overseer go)
- Overseer accepted the W8a G9 override (12:32Z); mc r2 stays in the read-out.
- run_gates.py (0F7C7B97) now expands <run> in arm env for G9. Re-gate of all 5 windows (`night/runexp/`): W8a G9 FAIL -> PASS 15/15 (exit 1 -> 3; G10 CHECK remains); WC1/WC2/W10/WC3 GATES lines unchanged. Diff: `session3/run_gates-runexp.diff`.
