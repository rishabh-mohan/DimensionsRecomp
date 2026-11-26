# E10.2 r2 cross-check of M12 S5 gates fixes

## Hashes (sha256 prefix)
| file | requested (18:03:49) | 18:04:00 copy | current |
|---|---|---|---|
| s5_gates.py | 6CF65B8D ok | 0C91CDFB (r2/s5_gates.py) | D8D17C86 (18:04:25, r2/cur) |
| s5_readout.py | 2940D94D ok | - | C54664D7 (18:05:15, r2/cur) |
| S5-GATES.md | E60549DF ok | - | 1EA4001C |
| READOUT-PLAN-P03.md | 820591C6 ok | - | A4C6EFB3 |
| s5-gates-selftest.txt | 4B66DCDD ok | | |
| s5-readout-selftest.txt | BDB24631 ok | | |
| s5-gates-m10synth-native.txt | 5F1A2604 ok | | |
| READOUT-CMD.txt (new) | | | CD819610 |
| READOUT-TEMPLATE-P03.md (new) | | | D559DD55 |

## Fixes (line numbers = cur D8D17C86 / C54664D7)
- B1 OK: gates L138-144 native-frames.csv then frames.csv (interval_ms+draw_calls); L154-156 no perf.csv -> ft from interval_ms; foff used for cvar L500.
- S1 OK: L200-206 foreign_crash_dumps excluded by basename; L211-218 only legodimensions.exe.<pid>.dmp VOIDs.
- S2 OK: L220-236 status!=OK / valid_timing False / excluded True -> VOID; absent -> PASS n/a; flags_info as info.
- S3 OK: L435-441 statistics.median.
- S4 OK: L380 end/error rows excluded from last_in.
- S5 OK: L504-506 fps None -> cap NODATA; L92 fps None on zero sum; report L625-628; readout L120 drops no-fps runs.
- S6 OK: plan L8 matches matrix-s5-baseline.json; readout L150-160 missing arms, L162-167 no-ref, L177-187 --vs, L104/L123-125 --unscored-tag.
- Extras: numeric cap L515/L530; native_default only with --native-default-ok and |cap-240|<=0.5; cvar order L496; hidden desktop L473 (on_timing_desktop is False).
- NIT paired() L68-71: zeros enter common but ka>0 and kb>0 at L71 drops them -> output unchanged.

## Selftests / synth
All exit 0, empty stderr. r2 copies reproduce 4B66DCDD (35+2) and BDB24631 (10) except path line. cur: gates PASS (+runs-root case), readout PASS 16 checks. Synth on both: byte-identical 5F1A2604.

## Field contract
Checked against live 1805-cold-ship60/run.json (static read): all fields read by gates present with matching names/types; cooldown {met,timed_out,flag,temp_*} found by find_key L395-414 -> PASS. sys.csv (LdSys.cs L32-35), gpu.csv (rt L334) headers match. No BLOCKER.

## NITs
- gates L546-555 align uses post-exit 'end' row (dev -1.09 s on cold-ship60, tol 3.0); slow close >~3 s -> spurious align FLAG (noflag variant only). Exclude end/error as in S4.
- READOUT-CMD.txt L10 hard-codes an absolute profile path.

## Item 4
All can wait; none changes a verdict/headline in this 17-run window (see report).
