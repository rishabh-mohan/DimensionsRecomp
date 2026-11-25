
## 07:44-07:51 final_gate v2 (M10 SAFE-IF AE8EB2A5)
- final_gate.py 4C3F0DC1 -> 9DCC72EE (diff final_gate-v2.diff C304214C, +166/-22): S1 miss-cache HOLD/FAIL for F7/F5w (and F6 with no line), S2 F2 xenos HOLD on clean switches, S3 F3=devfinal-off-bin / F6=nativefinal-off-bin (env unset or 0), N1 elapsed NOTE, N5 tmp name parent__run__pathsha8 (matrix parent is always `runs`), N6 F5w loaded-vs-saved NOTE, selftest-only _selftest_nobin.
- selftest 35/35 (01470932): 19 synthetic fixture cases + 5 real negatives (n0 F5/F6, win3 F1/F3). neg-win3-F1.txt BC53526C FAIL as expected. FINAL-F-GATES.md v2 9F7A33E6 (G1-G4 recorded).
- 07:53 Overseer: M10 rates final_gate v2 CONFORMS (final-gate-rating.md 2B9A8464). Active gate for F1-F7 under G1-G4; waiting for M3's F rows.
- 07:59 final_gate v3 73F946E7 (diff final_gate-v3.diff 769BB184 vs rebuilt v2 copy final_gate.py.v2-9DCC72EE, +99/-3): F2/F7 route timeouts by route sha (level-l 6F9E6009 / level-l-tail BE08A790 = lines - 7), subset of by-design lines, count = listed lines, steps n/n + stopped_by_script. Over 20 level-l runs, timeouts ran 27-31 (line 55 is sometimes absent; w6-gateB had line 22), so I made fewer than 31 a NOTE instead of the "count = 31" the Overseer asked for. Flagged for a ruling. selftest 56/56 B77C06B5; FINAL-F-GATES.md 1BDC0E5A. M3 dryruns fx1/2/3/4/6/7: bin and switch lines PASS.
- 07:59 Overseer ruling: v3 stands (subset of by-design waits + NOTE). final_gate.py 73F946E7 is FROZEN; no edits unless M10 asks.
- 08:05 M10 final-fx-rating.md F256C60D: v3 SAFE, final_gate 73F946E70D586060 pinned for the F1-F7 chain (C1: frozen until fx7 is gated; I check the sha at every F gate and record it). G3/C3: send the full first F1 PASS and the first F5 PASS to the Overseer. C4: hand markers only after an Overseer ruling.
- 08:12 fx1 F1 PASS (G3 full output sent). 08:19 fx3 F3 PASS.
- 08:26 fx4 F4: row_gate COMMON OK; final_gate exit 1, only FAIL is the --pair proof compare 61 vs 65 (periodic 'protects kept so far' lines 58 vs 54; non-periodic keep-watch lines identical). Overseer ruling ACCEPT -> PASS by ruling (ruling-fx4.md). Post-sprint item PS1: exclude those lines from the F4 compare.
- 08:34 fx2 F2: row_gate COMMON OK (121/121, vortex); final_gate exit 1, only FAIL is elapsed 584.84 s < 590 s floor. Overseer ruling ACCEPT -> PASS by ruling (ruling-fx2.md). PS2: base the F2/F7 floor on route completion. The ruling also covers F7 under the same conditions.
- 08:55 fx7 F7: row_gate COMMON OK (121/121, vortex); final_gate exit 1, only FAIL is elapsed 574.91 s < 590 s floor; s4b LOOK = NEW CONFIG.XML probe vs the menu base. Overseer ruling ACCEPT -> PASS by ruling (ruling-fx7.md); PS3 added. fx5/fx5w/fx6 were not forwarded to me, so I gated them now (G2): final_gate F5/F5w/F6 exit 0 PASS. row_gate on fx5/fx5w shows a matrix-row artifact (queued bin None); s4b LOOK on fx5 (focus=false, Execution complete x0) and fx5w (recording lines gone, warm launch). F1-F7 summary table written. final_gate unfreezes only for PS1-PS3, with an M10 rating before use.
- 08:57 Overseer ruled the fx5/fx5w LOOK items known artifacts; F1-F7 8/8 final. Next: #19 chain (r19r11 ref1 devoff4b-bin split16, launched 08:55:15, ends ~10:10). Gate with r19_gate --bin (L1), per r19prep-rating 335563D8.
- 09:03 Overseer ruling (d) (ruling-r19-d.md 39BC0929): r19r11 ref 1 PASS; standing rule (d) for scene-id-only LOOKs. New helper rule_d.py 7A735870 (read-only): checks an s4b_check file against rule (d) conditions 1-3 and compares mark ids vs --cmp check files (s4b01 for rows based on r19r11). Controls: r19r11 HOLDS; fx7 FAILS (NEW 1), fx5 FAILS (GONE 2 unexpected, no steps); both were ruled separately. Condition 4 = r19_gate output.

- 09:14 r19r10 / r19r13 / r19r15 gated: all PASS (r19_gate 0/0/0, rule_d HOLDS, json = M3's). r19r10 r19_path -> pathN. r19r13 memexport=0 by design. r19r15 DRED x1 proves layer enabled; d3d12_msg=0 vacuous (no info-queue drain).

- 15:14Z Overseer rulings: (1) ref 4 / row g claim only 'runs clean with the debug layer active (no device removal/crash)'; zero validation errors is a coverage limit, break_on_error is a follow-up. (2) M10 ACKed r19_path 4629604E / LAUNCH 2E8287EA (r19prep-rating 74933C80). (3) readback is ON in every run (harness toml d3d12_readback_memexport=true); S1 -> S1' (F426CEA0): f PASS = async+split clean under readback-ON, with a coverage limit; follow-up r19eL proves syncs > 0 under async.

- 09:16 r19r25 gated PASS (r19_gate 0/0/0; s4b vs s4bN16 clean; rule (d) N/A).

- 09:19 r19a gated PASS (r19_gate a 0/0/0, B19 rexgpu 5DCDD8CB; rule (d) HOLDS); agree with r19-ok-a.

- 09:23 r19b gated PASS (ruling e). rule_d updated to 3A556FB7.

- 09:26 r19i gated PASS; agree with r19-ok-i / go-r19on.

- 09:27 Flagged to Overseer: ROWS-R19 run-3 validity command (bench\agent11\timerq_slowstate.ps1 38A3F6AC -Root build\agent3\runs) scans 0 runs (expects <yyyymmdd-hhmm>\runs layout; agent3\runs is flat). Proposed: use s4b_check 'sys.csv slow state' (s4a_check.slow_state, same 800 MHz / 3-row rule); Busy n/a (no field in s4b runs). Awaiting ruling.

- 15:27Z Overseer ruling (run-3 validity, ON rows c/g/j/d/f/e): use s4b_check 'sys.csv slow state' (e_eff_mhz < 800 for 3+ rows from first frame); slow=true -> read up to onset_s, HOLD with onset_s + E median; Busy n/a on s4b rows, stated in each row entry; do not cite timerq_slowstate.ps1 for build\agent3\runs.
- Post-sprint PS4: ROWS-R19 section 2 run 3 doc fix (timerq_slowstate.ps1 needs the matrix layout; scans 0 runs on flat build\agent3\runs). ROWS-R19 is agent7's file: M7 to edit.

- 09:31 r19c gated PASS; rule_d -> DB898659 (also lists info-allowed NEW groups).

- 09:34 r19g gated PASS (coverage limit carried).

- 09:40 r19j gated PASS (J1 full_waits 1126 > 0).

- 09:43 r19d gated PASS (GONE 20 = Toypad packet dumps).
- 09:49 r19f gated PASS (S1' coverage limit carried; final pair 253813/253903 ok).
- 09:57 r19e gated PASS (W7 soak; held_query>0; GONE 57 Toypad dumps; -69 s = story-load wait 41.6 + close 19 + startup 4). #19 chain complete on my side.
- 09:59 R19-SUMMARY.md written (3626A499, 59 lines, 14 rows). #33 install verified: live s4b_check 3DDF1A55 / postcheck 36DC0E05 = drafts; plan/tools hashes match. final_gate.py still 73F946E70D586060.
- 10:12 #33 row 2 s33onsf gated PASS? (GONE 9 Toypad; sfjoin reads game.log only, NOTE).
- 10:16 #33 s33stop1 gated: exit 3 DOES NOT COUNT (clean); GONE 124 Toypad; miss gap ~191-209.5 s puts stop2/3 at exit-3 risk (S1).

- 10:24 s33stop2 gated: DOES NOT COUNT (exit 3, clean, gap 4.124 s); PASS? reading; S1 2 of 2. M3's H0 pattern confirmed; the pre-H0 5-miss sequence is in all runs (H0-23..-17). S sim: 231 80%, 152.7 100% (thin margins).
- 10:32 s33offw gated: PASS?; seed proof OK (2122CCC7/11E1A4B4 = run.json copy_sha256; source is a prefix of the run cache; 297/271 from storage); 0 judged marks differ; GONE 16 Toypad; 2 miss frames.
- 10:43 s33onw gated: PASS? (agree with ruling); seed OK; sceneids 0; drops are the same pipelines (xpso tail: onw 10 records = offw records 2-11); STOPR install verified (CB502E8C / 69C77DA7 / 748AD695).
- 10:47 s33stop3 (S153) gated: PASS, COUNTS (exit 0, 39 misses in window, gap 1.088 s, close 0.85 s); R3 tally 1 of 5; GONE 125 (+1 Toypad Read, first in base at 207.4 s); N5 ok.
- 10:50 s33stop4 (S146) gated: PASS, COUNTS (exit 0, 75 misses in 2 frames incl. H0 n67, gap 0.748 s, close 0.82 s); R3 tally 2 of 5; GONE 124 Toypad; N5 ok.
- 10:57 s33stop5 (S230) gated: PASS, COUNTS (exit 0, 1 miss in window, gap 0.355 s, close 0.74 s, H0+80.67); R3 3 of 5 counted, so row 4 PASS; read-out wording amended (R4).
- 11:03 s33gthr0 gated: PASS? (normalised $S33ON per ruling-s33-gthr0); sole NEW = the gate WARN, verbatim; latch INFO 0 / WARN 1; forced 0; drops 0; 0 judged marks differ; GONE 103 Toypad.
- 11:08 s33gasync gated: PASS? (pre-auth conditions all hold); sole NEW = gate WARN; latch 0/1; forced 0; drops 0; 0 judged differ; GONE 93 Toypad.
- 11:16 s33gbind gated: PASS? (pre-auth conditions all hold); sole NEW = gate WARN; latch 0/1; forced 0; late drops 0; drops 1317/50, all in miss frames, same as OFF; 0 judged differ; GONE 101 Toypad.
- 12:47 s33offd + s33ond gated: both PASS?; offd NEW 0 (+211 allowed diag), 0 judged differ; ond NEW 0, (a3) 0 differ, diagd exit 0, tainted at end 0 in both arms (101/101 and 136/136 healed). #33 rows 2-6 + (d) summary written to ROWS-RESULTS.
