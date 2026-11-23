# Night windows of 2026-11-23: gate results (task #24)

Agent 12, 2026-11-23 05:58. Text fixes at 06:10, after a read-only check found that every number matches its source.
- **Kit:** `build/agent12/w6-gates/run_gates.py`, with the G12 gap fix of 05:53 (see "Kit fix" below). Its tests
  pass: selftest 51/51, and the W5 and W4b fixtures are OK.
- **Script:** `build/agent12/w6-gates/night/run-night-gates.ps1`. It runs one dir at a time at Below Normal.
- **Outputs** are in `night/`: `out-<W>-<dir>.txt` and `gates-<W>-<dir>.json`. Every `err-*.txt` is empty.
- **Arguments:**
  - W6: `--one-bin`, plus Agent 3's 2026-11-22 side runs and gate A (`--side` for side 1, side 2 and side 3,
    `--gate-a` for gate A);
  - W9 and W5b: `--one-bin`;
  - W4c: none, because it compares two bins.
- **Window logs** are in `bench/agent5/launch/status/`. The kit finds each one by its END line.

## Verdicts: all 7 windows PASS

The two W6 windows PASS with the finding-10 WARN on G8.

| Window | Matrix dir | Window log | Kit exit | Gates not PASS | Verdict |
|---|---|---|---|---|---|
| W6 | `20261123-0009` | `window-W6-0006.log` | 1 | G8 FAIL (raw) | **PASS**: G8 = raw FAIL + "WARN, finding 10, Agent 1 22:25" |
| W9 | `20261123-0108` | `window-W9-0105.log` | 0 | none | **PASS** |
| W5b | `20261123-0155` | `window-W5b-0152.log` | 0 | none | **PASS** |
| W4c | `20261123-0239` | `window-W4c-0236.log` | 0 | none | **PASS** |
| W6 | `20261123-0313` | `window-W6-0310.log` | 1 | G8 FAIL (raw) | **PASS**: G8 = raw FAIL + "WARN, finding 10, Agent 1 22:25" |
| W9 | `20261123-0401` | `window-W9-0358.log` | 0 | none | **PASS** |
| W5b | `20261123-0451` | `window-W5b-0445.log` | 0 | none | **PASS** |

Statuses that are not verdicts:
- G1 is MANUAL in every window. It lists the switches for Agent 10's ratings.
- In W6, G6 and G7 are CODE: met in code.
- In W9, W5b and W4c, G4-G7 are n/a: no arm sets the P2 or keep-watch switches.

## Per window

Every window passes G2, G3, G9, G10, G11 and G12.
- **G3:** every run OK, exit 0x00000000, wm_close, runner exit 0; the arms as planned; the launcher's END says
  exit 0.
- **G8:** 0 stale, fault or Protect-failed lines; logdiff against the reference arm finds 0 FAIL findings and 0 NEW
  messages.

| Window | Runs (scored) | Arms | Non-game load, cores (median) | Flagged runs (> median + 1.0) | Quiet gate | END |
|---|---|---|---|---|---|---|
| W6 0009 | 21 (20) | 4/4 | 3.32-4.64 (3.41) | #8 p2fc r2, 4.64 | STRICT at 00:09:01 | 00:51:52, all runs OK, 42.8 min |
| W9 0108 | 21 (20) | 5/5 | 3.36-3.70 (3.44) | none | STRICT at 01:08:53 | 01:51:23, all runs OK, 42.5 min |
| W5b 0155 | 19 (18) | 3/3 | 3.21-3.81 (3.34) | none | STRICT at 01:55:28 | 02:33:54, all runs OK, 38.4 min |
| W4c 0239 | 13 (12) | 2/2 | 3.26-3.61 (3.34) | none | STRICT at 02:39:45 | 03:05:58, all runs OK, 26.2 min |
| W6 0313 | 21 (20) | 4/4 | 3.28-3.89 (3.42) | none | STRICT at 03:13:21 | 03:56:11, all runs OK, 42.8 min |
| W9 0401 | 21 (20) | 5/5 | 3.35-4.62 (3.51) | #4 q125 r1, 4.62; #12 q125 r3, 4.58 | STRICT at 04:01:16 | 04:44:08, all runs OK, 42.8 min |
| W5b 0451 | 19 (18) | 3/3 | 3.22-4.15 (3.37) | none | STRICT at 04:51:58 | 05:30:42, all runs OK, 38.7 min |

- **G10:** every scored run is valid. The proof lines are OK in every run, every run had ≥ 6 GB free RAM, and no
  scored run was in the slow state.
- **Flagged runs:** the flag is information for the read-out, not a failure. With a flagged run, also give each
  verdict without the rounds that hold it (W6-GATES R3).

## W6

- **G4 PASS 4/4**, all T=0: side 1 (p2f), side 2 (p2fc), side 3 (p2fc, attract) and gate A (p2fc + verify).
- **G5 PASS:** gate A has verify on, first kept 1, K 0 and F 0.
- **G8:**
  - 0 stale, fault or Protect-failed lines in 25 runs (the 21 timed runs plus the 4 side runs);
  - keep-watch on and keeping in 8/8;
  - logdiff against s0: 0 FAIL findings, and 0 NEW messages in 21/21 runs.
- **The raw G8 FAIL has one source.** Verbatim, with the kit's two spaces:
  `side gate A (20261122-210906-w6-gateA-p2fcv-level):  1 [critical] lines`.
  That line is gate A's finding-10 minidump (`hang-36276.dmp`), waived by Agent 1 at 22:25.
  **The timed runs are clean.**
- Both W6 windows use the same 2026-11-22 side runs and gate A, so G4, G5 and the waiver are the same in both.

## Environment (G11, G12)

- **G11 PASS in all 7:**
  - overlay `best_performance` in every run, with no change inside any window;
  - scheme Balanced, AC 1, battery saver 0.
  - **W5 ran under `best_efficiency`.** Compare the night windows with each other, but don't compare absolute
    numbers with W5. This matters for W5b.
- **G12 PASS in all 7:**
  - STRICT, with MsMpEng 0.00/0.00/0.00 and OfficeClickToRun 0.00/0.00/0.00 in every window;
  - CrossDeviceService 0.03-0.07;
  - each gate line falls in the window's start minute (0 min).
- **Window logs, checked by hand:** I grepped for Agent 5's kill lines
  (`NOT killed|could not kill|could not be killed|runner stopped: NO|process list could not be read|left over from
  the window`, plus `!!!` and `killed`). There are 0 hits in all 7, so no process was left over.

## Kit fix in this task (G12)

- **The bug:** the first run (05:47) had G12 CHECK in all 7 windows, with text such as "the window started at
  00:09, 1440 min later".
  - `w6_env_record.py` computed `(start - gate) % 1440`.
  - Each gate line came 1-58 s after the dir's HH:MM:00 (:01, :53, :28, :45, :21, :16 and :58, in window order).
    So the small negative gap wrapped to just under 1440 min, which printed as 1440 in 4 windows and 1439 in 3.
  - Exits were 3 (W6: 1).
- **The fix (05:53):**
  - a signed gap, unwrapped across midnight;
  - a gate line inside the start minute is 0 min;
  - a WARN (→ G12 CHECK) when the gate line is more than 30 min before the start, or after it.
- **Tests** (`night/recheck-kit.ps1`, 05:54):
  - w6_env_record selftest 16/16 (+4 gap checks). It was re-run at 06:07 after a fix to one test label: 16/16;
  - run_gates selftest 51/51 (+2);
  - W5 `EXPECT: OK (57/57)`;
  - W4b `EXPECT: OK (53/53)`.
- **Re-run of the 7 windows (05:54-05:55):** only G12 changed, from CHECK to PASS. Exits went from 3 to 0, and
  W6 stays at 1.
- **The read-only checker** also confirmed the fix's edge cases: exactly 30 min passes, 1 min after the start is a
  CHECK, and 23:59:59 against dir 0000 is 0 min. One cosmetic point: a gap from 30 to 30.5 min prints "30 min
  later" together with the WARN, because of rounding. The status is still right.
- `HASHES.txt` is regenerated: see the task #24 list in its header.
