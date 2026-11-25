# #19 (async submit) chain: cross-gate summary (M12, 2026-11-25)

All 14 rows in ROWS-R19 (5 refs + 9 #19 rows) are **PASS**. Each was cross-gated against M3's run, and every r19_gate json matches M3's. The r19_gate pin is CA5C036CB956BF66.
Bins: **B4** = devoff4b-bin (refs); **B19** = devoff4b-r19-bin (exe DFBE1D43, rexgpu 5DCDD8CB, rexruntime A33801D1).
Rules: **d** = scene-id-only LOOK -> PASS? (ruling-r19-d); **e** = allow-new applied in normalised form (ruling-r19-e); **j** = large drift accepted when the perf.csv load class matches (ruling-r19-j).
Counters are taken from the last line (async `chunks`, `queued_max`, `full_waits`; split `splits`). Slow state is s4b_check `sys.csv slow state` (slow / E median MHz). Busy is n/a on s4b rows.

| row | bin | base (s4b --row) | gate | rule | splits | chunks | qmax | full_waits | slow |
|---|---|---|---|---|---|---|---|---|---|
| r19r11 ref1 split16 | B4 | s4b01 (s4b11) | PASS | d | 69226 | - | - | - | false / 2206 |
| r19r10 ref2 splitN | B4 | s4b01 (s4b10) | PASS -> r19-pathN | d | 181539 | - | - | - | false / 1772 |
| r19r13 ref3 rbme | B4 | s4b01 (s4b13) | PASS | d | 196341 | - | - | - | false / 1845 |
| r19r15 ref4 debug | B4 | s4b01 (s4b15) | PASS | d | 102152 | - | - | - | false / 1953 |
| r19r25 ref5 title | B4 | s4bN16 (s4b25) | PASS | n/a (title) | 109756 | - | - | - | false / 1849 |
| r19a OFF | B19 | s4b01 | PASS | d | - | - | - | - | false / 1746 |
| r19b async, split 0 | B19 | s4b01 (90 s) | PASS (1 'staying off' WARN) | e | - | - | - | - | false / 2615 |
| r19i splitN | B19 | r19r10 | PASS | d | 282244 | - | - | - | false / 2823 |
| r19c async+N | B19 | r19r10 | PASS | d, e | 255831 | 255831 | 3 | 43077 | false / 2191 |
| r19g debug+async+N | B19 | r19r15 | PASS (DRED x1) | d, e | 136129 | 136129 | 3 | 109783 | false / 2146 |
| r19j async+16 (J1) | B19 | r19r11 (+s4b01) | PASS | d, e, j | 67791 | 67826 | 3 | 1126 | false / 2284 |
| r19d W7 title uncapped | B19 | r19r25 | PASS | n/a (title), e | 103846 | 103846 | 2 | 0 | false / 1768 |
| r19f rbme+async+N | B19 | r19r13 | PASS | d, e, j | 253813 | 253903 | 3 | 38835 | false / 1941 |
| r19e W7 level soak | B19 | s4bL0 | PASS (held_query>0) | e | 648929 | 648929 | 3 | 135864 | false / 1784 |

In all ON rows (c g j d f e):
- one segment, init once, `(3 slots)`, failed=0, monotonic, watchdog 0;
- "every split went async" PASS. Across the runs, chunks lead or equal splits by 0-104 (f's maximum), within soak_check's merged-order invariant. The last pair was hand-checked on f and e;
- NEW 0 beyond allow-new, MORE 0, FLAG 0, 0 proof misses, 0 unexpected GONE. Every GONE line is a Toypad packet dump in GONE_OK_DEFAULT.

## W7 conclusion
Both W7 rows pass with real splits:
- **j** (16 KB stress): 12 async lines, chunks 67826, full_waits 1126 > 0, so the FIFO filled and the stress claim holds (J1).
- **e** (10-min level soak, uncapped): 41 async lines, chunks 648929, queued_max 3, held_query > 0, Vortex reached, toypad load-confirms 3/3, slow=false.

Supporting:
- **d** (title, uncapped, s19 arm) ran real splits (1.88 chunks/frame) and never filled the FIFO (queued_max 2, full_waits 0). A3 requires only ≤ 3.
- All runs were on the hidden desktop and are **functional only, not timing**.

## Coverage limits (verbatim)
- **f / S1' (F426CEA0):** "async+split ran clean with readback ON (its normal state); no memexport sync is shown to fire; this stays indirect until r19eL".
- **g / ref 4 (debug):** "proves only runs clean with the debug layer active; InfoQueue is not drained, so d3d12_msg=0 proves nothing". Timing is n/a (debug layer).

## r19e −69 s
The same 121 input steps ran in the same order, with the same 30 timeouts and no skipped section. The time went to:
- the story-load wait (L55, 'lit 99 42 0E'), which succeeded after 1.3 s instead of 42.9 s: −41.6 s;
- the close, 0.80 s instead of 19.43 s: −19.0 s;
- startup and first frame: −4.0 s;
- the vortex wait: −1.6 s;
- per-step jitter: about −3 s.

Story-load to end took 281.1 s vs 284.1 s.

## Post-sprint doc fixes (none applied)
- **PS4** (ROWS-R19 section 2, run 3; M7): timerq_slowstate.ps1 needs the matrix layout and scans 0 runs on flat `build\agent3\runs`. Point the text at s4b_check's `sys.csv slow state` line.
- **LAUNCH-R19 / ROWS-R19 S1 -> S1'** (F426CEA0): readback is ON in every run (harness toml). Row f proves async+split under readback-ON plus the coverage limit above. Proving syncs > 0 under async is follow-up r19eL.
- **allow-new in normalised form** (ruling e): s4b_check matches `--allow-new` against normalised lines (digits -> `#`). The LAUNCH-R19/ROWS-R19 patterns should read `d#d#_async_submit: needs` (b), `d#d#_async_submit: ` (c g j d f) and `d#d#_(async_submit|submit_split)` (e).
- row_gate's single "problem" on rows with a `<N>` cvar is the queue placeholder (the queue fills N=4 from ready-N). Either teach row_gate to substitute it or document it.

Sources: `build\agent12\session3\ROWS-RESULTS.md` (per-row entries and file sha8s), `r19\r19-summary-data.txt`.
