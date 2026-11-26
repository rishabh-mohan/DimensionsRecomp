# Cross-check: M12 S5 gates + read-out (fixes B1, S1-S6, P03 read-out)

M10 (with E10.2), 2026-11-25 ~18:15. Static review plus the selftests and the synth on copies (FREEZE-safe, BelowNormal, one at a time). E10.2's full notes: `build/agent10/s5/scratch-m12/r2/FINDINGS-r2.md`.

## Files (re-hashed 18:13; unchanged since E10.2's review)

| File | sha256/16 | Bytes | mtime |
|---|---|---|---|
| s5_gates.py | D8D17C86B624749F | 50452 | 18:04:25 |
| s5_readout.py | C54664D7A9DB8B9F | 17579 | 18:05:15 |
| S5-GATES.md | 1EA4001CBC4CC1DE | 12170 | 18:07:53 |
| READOUT-PLAN-P03.md | A4C6EFB337528B0D | 7706 | 18:06:35 |
| READOUT-CMD.txt | CD819610882DE5D3 | 4329 | 18:07:00 |
| READOUT-TEMPLATE-P03.md | D559DD55C9ECA98A | 3274 | 18:07:41 |
| s5-gates-selftest.txt | A25DFA278EBB5044 | 3225 | 18:08:18 |
| s5-readout-selftest.txt | D543F5C61E26BD4E | 657 | 18:08:22 |
| s5-gates-m10synth-native.txt | 5F1A2604695713E9 | 1409 | 18:01:10 |

These supersede 6CF65B8D / 2940D94D (the Overseer's 18:02 brief) and the intermediate 0C91CDFB. Below L672, D8D17C86 is identical to 0C91CDFB.

## Base

- Earlier M12 set FCC073A2 / 8FCFDDB1 (my blocker list B1, S1-S6).
- Runner contract: run-timing.ps1 72B8C69C (run.json L851-904), score3d.py 94612E3E (write_runjson L73-84), run-matrix.ps1 8D647918, matrix-s5-baseline.json 57255790. All rated in 32C73981.

## Verdict

**CONFIRMED.** All fixes are in. The selftests and the synth pass, and the field contract matches the runner with no name or type mismatches. **Nothing must be fixed before the read-out.** The read-out can run as written in READOUT-CMD.txt, under conditions X1-X3.

## What I checked

Line numbers refer to D8D17C86 / C54664D7.

| Item | Result | Where |
|---|---|---|
| B1 native-frames.csv | OK | L138-144: native-frames.csv, then frames.csv (interval_ms, draw_calls). L154-156: with no perf.csv, times come from interval_ms. The cvar uses foff (L500). Selftests B1nativefr / B1noperf. |
| S1 foreign dumps | OK | L200-206: foreign_crash_dumps dropped by basename. L211-218: only legodimensions.exe.&lt;pid&gt;.dmp in the run dir VOIDs. |
| S2 runner verdict | OK (spot-checked) | L220-236: VOID on status != OK, valid_timing False or excluded True. PASS n/a when none of these fields exist. flags_info is shown as info. |
| S3 GPU covariates | OK | L435-441: statistics.median. |
| S4 last_in | OK | L380: end/error rows excluded. |
| S5 fps None | OK | L92, L504-506: cap NODATA with the arm still set. Report guarded at L625-628. The read-out drops runs with no fps (L120). |
| S6 missing arms | OK | readout L150-167: "not run" / "no valid runs" / missing ref. L177-187: `--vs` secondary contrast. L104, L123-125: cold-/warm runs dropped. Verdict counts per arm. |
| cap compare | OK | Numeric at L515/L530. native_default only with `--native-default-ok` and \|cap-240\| <= 0.5. Native cvar fallback at L496. |
| hidden desktop | OK | L473: on_timing_desktop False, consistent with timing-env.ps1 L29. |
| `--runs-root` | OK (spot-checked) | L674-693 reads `tag` from run.json. The default `--scored-tag` `^(?!cold-\|warm\d+-).+-r\d+$` (L638) keeps `ship60-r1`, `natU-r2` etc. and skips `cold-*`/`warm*-`. The live dirs 1805-cold-ship60 / 1809-cold-nat60 / 1812-cold-n4bp60 carry tag `cold-ship60` etc. and are skipped. |
| selftests (cur) | PASS | gates: 35 cases + 2 set rules + runs-root (A25DFA27). readout: 16 checks = 10 old + 6 P03 (D543F5C6). E10.2 reproduced both on copies, exit 0, empty stderr. |
| synth | byte-identical to 5F1A2604 | On both r2 and cur: FLAG, 3d/span/cap PASS, cooldown FLAG (the synth has no record), host NODATA (no sys.csv), draws_source native-frames.csv. |
| field contract | OK | Live run.json (1805-cold-ship60, static read): status OK, valid_timing true, excluded false, pid == input_script.dll_loaded_by_pid, on_timing_desktop true, close_sent_s 165.33, dumps/foreign_crash_dumps [], window_start_s, window_span_s, effective_cap 60 (int), cvars.framerate_limit "60" (string, compared numerically). `cooldown{met,timed_out,...}` (rt L225-228) is found by find_key (L395-414), so cooldown PASSes on M8's runs. sys.csv (LdSys.cs L32-35) and gpu.csv (rt L334) headers have every column the gates read. |
| READOUT-CMD results.csv | OK | run-matrix L720: `arm = $run.id`, `scored = [string](-not (cold -or warm))` ("True"/"False"). Export-Csv at L553. `Group-Object scored, arm` gives "True, ship60" etc. |
| `--ref devfinal2` | OK | The bin key is the bin_dir basename, so it doesn't match nativefinal2 / native4bp. |

**C5 reminder (from 32C73981):** any user input, build or foreign game during the window sets valid_timing false or excluded true, and gate S2 then VOIDs the run. The read-out reports VOID runs and never averages them in (C4).

## The five minor items: must fix or can wait

| Item | Call | Why |
|---|---|---|
| close_sent_s 0.0 falls through the `or` | can wait | The close comes at ~165-275 s, so 0.0 can't occur. If it were null, the fallback elapsed_s is ~2 s later, inside tolerance 3. |
| started_epoch_s offset | can wait | ~0.42 s ($start rt L310 vs $sw L325). That is under 1 of ~120 host samples. Later fix: take the epoch when $sw starts. |
| VOID runs in the host median | can wait | Moves the median by at most one order statistic. FLAG-only, margin 1 core, affects only the noflag variant. |
| T975 = 2.0 for df > 15 | no effect | The largest paired n is 4 (df 3); natU n=2. |
| pct CI is not a ratio CI | can wait; label it | Same resolved/not-resolved call and the same point %. Bounds differ by ~0.2 pp. Label it "diff CI scaled by median(ref)" in the read-out text. |

## Conditions for the read-out

- **X1:** In READOUT-CMD step 2, the gates header must say **14 scored**. A scored run without a readable run.json lands in "skipped (no run.json tag)" instead of being counted. Any shortfall against step 1's results.csv count (True rows = 14) must be listed in the read-out as missing/ERROR, never silently dropped (C4).
- **X2:** Run the read-out only after the window has ended and the FREEZE is lifted, as READOUT-CMD says. The gates read the run dirs, which run-matrix still writes during the window.
- **X3:** Label the pct CI as in the table above. The headline contrasts are nat60 vs ship60 (primary) and n4bp60 vs nat60 (`--vs native4bp:nativefinal2`, secondary). natU is info only (n=2).

## Findings

- **N1 (NIT, optional before the read-out):** gates L546-555, the perf_rows alignment check, still uses the post-exit `end` row (in practice the only row with perf_rows > 0). On cold-ship60 the deviation is -1.09 s against tolerance 3.0. A close more than ~3 s after the last frame would give a spurious align FLAG. That matters only for the noflag variant. Fix: exclude end/error rows, as S4 does.
- **N2 (NIT):** readout paired() L68-71 now keeps zeros in `common`, but the ka>0/kb>0 log filter at L71 still drops them, so the "keeps 0 values" extra changes no output. Harmless.
- **N3 (NIT):** READOUT-CMD.txt L10 hard-codes an absolute profile path. It works on this machine; it is not portable.
