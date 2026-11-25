# M3 read-out tools review (WC1 gate rows and session-3 rows)

M10, session 3, 2026-11-25 01:55-02:00. Read-only: no runs. I ran `wc_proof.py` once, on the finished cg26b0 run dir, as a tool check.

**Files reviewed**

| file | sha256 (first 16) | compared with |
|---|---|---|
| `build/agent3/session3/wc_proof.py` | DDDEFD756F6DD665 | new, no backup; 104 lines read in full |
| `build/agent3/s4b/s4b_check.py` | E075FCD51E96759B | `s4b_check.py.bak-0628` C8D16E695C139F94 (+21/-4) |
| `build/agent3/s4b/postcheck.ps1` | 8054C2968D1D9836 | `postcheck.ps1.bak-0628` 0A7238B498B0D549 |
| `build/agent3/session3/f10_rule.py` (called by postcheck now) | 3B849D2E0BA1E965 | new; read in full |

**Verdict: SAFE to use tonight, with 3 SHOULD fixes.** No tool turns a crash, a STUCK-LOCK outside finding 10, an [error] line or a wrong init line into PASS:
- s4b_check's BASE list misses on exit, dumps, stuck_lock, error/critical, logdiff NEW/MORE/FLAG, and no clean exit;
- wc_proof requires exit 0 and 0 STUCK-LOCK;
- f10_rule FAILs on a crash or a missing `vortex` mark.

The gaps are proofs that the **right thing ran**: the switch was armed, the bin was right, the load was present, and the lock recovered.

## Findings

- **S1 (SHOULD, s4b_check `s4bV0`).** "C1 verify armed" is only a note (`chk(None, ...)`, L493). If verify fails to arm (a cvar typo, or a bin that won't arm verify with keep-watch off), the row reads F = 0 and K = 0, which "refutes" Agent 12's F > 0 prediction while proving nothing. Rows s4b04/s4b07/w6gA already require it (L451: "without it K = 0 proves nothing"). Make it `chk(n['c1_verify_on'] == 1, ...)`. The same applies to the future s4bV0f/s4b07f branches (C1 rating S2, still open: they are not in the queue or the checker yet; Agent 12's RATIONALE L96-105).
- **S2 (SHOULD, f10_rule "self-recovers").** The SDK logs no "acquired" line: the detector reports once per wait and then keeps waiting silently (`xboxkrnl_rtl.cpp` HEAD L497-545). So f10_rule L94 counts *any* later timestamped non-STUCK line as recovery, including other threads' lines and the WM_CLOSE shutdown lines. A permanent stall after the level is reached, with exit 0, therefore reads WARN (finding 10) instead of FAIL. Fix: require real progress after the event:
  - a route mark after the event (`next_mark` is already computed but not used);
  - or, when the event comes after `vortex`, perf.csv frames advancing for at least 10 s after t0.
  - Until then, the reader checks `next_mark` / perf.csv by hand for every WARN.
- **S3 (SHOULD, wc_proof `cg26`, and any bin-specific row).** No bin-identity proof. A run dir holds its bin copy (`legodimensions.exe`, MANIFEST.txt), so check the exe hash: CG26 45952D171D6204A1, devoff4b DFBE1D43. cg26b0 (20261125-014556) did run the CG26 exe (45952D17, checked), and wc_proof gave PASS 9/9. A cg26 arm run on devoff4b-bin would also pass every current proof.
- **N1 (c1np leaks).** wc_proof's c1np branch doesn't forbid "Host timer resolution set to 1 ms". postcheck's `win3f|c1npf` allow-new (`C1 keep-watch|GPU wait|TimerQueue|Host timer|precise`) is shared, so a leaked d11 cvar in c1npf passes both tools. Give c1npf `--allow-new 'C1 keep-watch'` only and forbid the Host-timer line in wc_proof c1np. More generally, the toml check proves the matrix cvars are present, not that there are no extras.
- **N2 (f10aL/f10bL load proof).** These map to the f10a/f10b proofs, whose "quiet host" check only looks for clang/cl/ninja/link, so a "loaded" run without cpuload passes as loaded. Add a check that `cpuload.log`'s start..end window covers the run (or that sys.csv cpu_util is high).
- **N3 (wiring).** postcheck never runs wc_proof, so WC1's gate needs three outputs read together: `<id>.check.txt` (hint), wc_proof (manual) and `<id>.f10.txt`. For win3f/c1npf/cg26L, s4b_check has no row proofs, and on the L route it doesn't judge the level (scenes are soft); only f10_rule does. Either wire wc_proof into postcheck or write the 3-part pass rule down.
- **N4 (s4bN16/s4bN4).** These take s4b11's proofs, which don't check N. Add `'at %d KB' % N in split_init line`. With 0 split lines the row already reads LOOK (splits > 0 misses), so this fails safe.

Checked and fine:
- the id map (L433-434) covers every new queue id, and the s4bQ5 quantum test uses the raw `row`;
- postcheck's regexes match the queue ids, `Check` passes `--row $id`, F10 runs only on L-route ids, and cg26b0 (menus) gets the default check against s4b01;
- wc_proof win3 checks the env exactly, one precise-wait line, and exactly one ON 500/30/stats-OFF line;
- wc_proof fails safe without the toml (every cvar shows as DIFFER).
