# CHECK-W5b: cross-check of `build/agent7/readout/W5b.md` (all 326 lines) + `W9.md` L22-29, L252-256

Read-only checker, 2026-11-23 ~07:35. Sources: the ones in the brief. Extra sources where W5b's numbers lead elsewhere:
- `build/agent8/readout/w5/READOUT.md` (W5's CPU numbers);
- `build/agent8/matrix/20261123-0451/matrix.json` (arms);
- `perf-notes/SESSION2.md` L3171-3173 and L3292-3296.

Hashes were recomputed with Get-FileHash. Arithmetic was redone by hand and with `build/agent7/readout/check/check_w5b.py` (loaded-run test, pass-1 spreads, W5 d11t vs d11).

**Summary: ~830 claims checked (numbers, CIs, n, citations, wording), 11 mismatches: 0 high, 2 medium, 6 low, 3 very low.** No copied number or CI is wrong. The flag sets are the same in every section.

## Mismatches

| # | W5b.md / W9.md line | quoted text | source file:line | correct value / fix | severity |
|---|---|---|---|---|---|
| 1 | W5b L44; L227; L230 | "The CPU saving is reproduced, smaller (-8.6 % vs -13.7 %)"; "it used 13.7 % less game CPU" | `build/agent8/readout/w5/READOUT.md` L28, L116, L119; 0451 `matrix.json` L21 ("Game CPU vs base: d11t -13.7 %"); PROPOSAL.md L72 (drops the reference) | W5's -13.7 % is d11t vs **base**, not vs d11. W5b's -8.6 % is vs d11. Like for like, W5's d11t vs d11 is about **-14.5 %** (0.863 / 1.009; d11 was +0.9 % vs base at READOUT L119; medians at n = 3). "Smaller" still holds. Fix: say "vs base", or use ~-14.5 % vs d11. | medium (wrong reference; conclusion unchanged) |
| 2 | W5b L42 (last column); L308; L311 | "The pick then rests on the loaded runs themselves (d11t lost -3.0 % fps vs d11p -1.1 % at similar load, n = 4 each)" | load-check.md L87-95 (values); W5b L212, L318 (the caveat) | The numbers are right (-2.975 / -1.075; ng_t 3.11 / 3.15). But this post-hoc 4-vs-4 gap carries the pick, and here it appears without its caveat. The gap is -1.9 points: Welch 95 % CI [-4.1, +0.3], p 0.083 (exact permutation p 6/70 = 0.086; Mann-Whitney p 0.11). So it is n.s. Add "(post hoc, n.s.)" in the verdict cell and at L308, as L212 does. | medium (overstated) |
| 3 | W5b L156 | "cores (mean) 2.5585 / 2.347 (-0.2115) / 2.354 (-0.2045) \| pool-W5b.md section 8" | pool-W5b.md section 8 (L236-273, 2-decimal cores) | Section 8's 2-decimal cores give 2.5583 / 2.3483 / 2.3533 (-0.2100 / -0.2050). The 4-digit values come from the 3-decimal per-run cores (0451 summary.md run rows; mine/W5b.md L68-70; pool-W5b.json). Fix the "from" cell. | low (citation) |
| 4 | W5b L152 (also L162) | "The runner's summary for pass 2: d11p -0.21 core with fps unchanged; d11t -0.21 core but fps -0.8 %, with slow r1-r2." | perf-notes/SESSION2.md L3292-3295 | No source is given. summary.md L12-14 has only the medians (cores 2.56 / 2.35 / 2.35). This wording is Agent 1's relay of the runner summary at SESSION2.md L3294-3295 ("r1 and r2 were slow: 2.65 and 2.58 ms"; "fps unchanged"). Cite it. | low (citation) |
| 5 | W5b L165 | "So \"slow r1-r2\" is host load (section 7)." | load-check.md L75, L87-95 | This is correlation only. 0455 / 0459 had ng_t 3.37 / 2.84, but the pass-2 within-arm Spearman is -0.32 (p 0.19), and the most loaded run (0457, 3.76) kept its fps. Say "coincides with host load" or "is most likely host load". | low (wording) |
| 6 | W5b L166 | "Its spreads of 10.1 / 10.3 / 4.4 % come from the fast round 1." | 0155 summary.md L12-14; pool-W5b.md section 8 (seq 2-19 median ms) | The spreads are (max - min) / median of median ms. Without round 1 they are **2.0 / 4.4 / 2.2 %**. Round 1 explains all of d11's spread, most of d11t's (the rest is loaded 0213, 2.606 ms) and only about half of d11p's (the rest is loaded 0209, 2.544 ms). Say "mostly from the fast round 1, plus 0213 / 0209". | low |
| 7 | W5b L224 | "...8.04 in 0213-d11t-r3, 7.60 in 0510-d11t-r3 and 7.49 in 0453-d11-r1, vs 5.95 in 0221 (audit.md L257)" | audit.md L253, L359, L351, L257 | The values are right, but L257 is only 0221's row. Cite L253 / L359 / L351 / L257. | low (citation) |
| 8 | W5b L85 | "so the cause is game-state warm-up" | pool-W5b.md section 8 (light share) | The lighter frame mix (0.979-0.988 vs 0.962-0.978) fits warm-up but doesn't prove it. Say "points to game-state warm-up". | low (wording) |
| 9 | W5b L45; L286 | "Load came back ~6 min after the holdback" / "Then the load came back" | audit.md L37 (and W5b L293) | The timing is right (holdback 04:46-04:49; first rolling-median exceedance 04:55:02, audit L34). "Came back" implies the same load returned, but the audit says the source can't be tied to CrossDeviceService. Say "load rose again". | low (wording) |
| 10 | W5b L21; L322 (also W9.md L20) | "it was added ~23:16 on Nov 22" | perf-notes/SESSION2.md L3171-3173 | Correct ("user answers (23:16)" ... "Defender exclusion: added"), but uncited. Add the citation. | very low |
| 11 | W5b L44 | "1 % low -2.8 [-6.5, +1.0] (W5: -7.7 %), all of it from one run: -0.8 [-2.5, +1.0] without 0221" | pool-W5b.md L105 | Dropping 0221 moves -2.8 to -0.8, so "all" overstates. Say "most of it". | very low |

## Rounding (±1 in the last digit, fine)

- W5b L127: d11p raw fps mean -0.72 (pool paired table, the cited source) vs -0.73 at load-check.md L111.
- W5b L218: "median 1976" vs 1975.5 in cluster-0221.txt. W5b L222: "3.7 s" vs 3.69 s.
- W9.md L255: "(04:54-05:02)" vs windows 04:54:46-05:01:48.

## Notes (not counted as mismatches)

- W5b L44/L228 set W5's T-std CI [+0.5, +16.6] (PROPOSAL L70; matrix.json L21) beside W5b's B-block CI. W5's B-block CI was [+1.6, +15.3]. "Both CIs exclude +8.2 %" holds either way.
- W5b L146: "d11t's count comes from one run". The same bullet then lists 0510 (7/1/0) and 0203 (1/0/0). "Mostly from one run" would be tidier (optional).
- W9.md L29 (agreement):
  - `a7/W9-pool.md` is readout.py run on Agent 8's merged folder. It shares 14 table rows with pool-W9.md (T-std/B-block median ms, fps, p99 and 1 % low; raw median ms and fps), and all 14 are identical.
  - Its CPU, per-pass and variant parts are missing or laid out differently, so they weren't compared.
  - mine/W9.md L47-50 maxima 20.63 / 23.29 / 37.29 match W9.md L249-251.

## Verified OK

- **Hashes:**
  - matrix.json sha256 prefix 23575AAAE9DCBB85 in both folders;
  - results.csv 5A08241AA965ADE4 (0155) / 8C6CC5147A7470E2 (0451);
  - audit.md LastWriteTime 06:38:34 (the "06:38 version"), and every audit line number points at the right rows.
- **Arms (L7-11):** match matrix.json L31-50:
  - d11 = framerate_limit=0 + the 8 timer cvars, env {};
  - d11t = env REX_TIMER_WAIT_BLOCKING=1;
  - d11p = + timer_queue_precise_wait=true;
  - bin devoff4;
  - proofs at RESULTS.md L38 and L55-57.
- **Inputs (L16-36):**
  - windows, G11 and self-check (PASS, 108, diff 0) match pool-W5b.md L4-11;
  - tail-check is verified in 36/36 runs (L11-46);
  - agreement: a7/W5b-pool.md L27/L29/L36/L38 and mine/W5b.md L27-28/L40-41.
- **Verdict table (L42-45):** every number matches its source, apart from the reference in #1 and the wording in #2 and #11.
- **Section 1:**
  - table matches pool L17-19; guard (c) 0/36;
  - NOTEs at RESULTS L31/L32, L9, L94-108;
  - flags at audit L17/L21; union 7 with n 11/8/10; no-loaded 9 with n 11/8/8;
  - 0520 2.90 / 0524 2.88 (audit L364/L366); 0221 2.31 (audit L257).
- **Section 2:**
  - F 4.11 (11, 22), p 0.002; fps F 4.20;
  - round terms +5.1 to +7.8 %, r7 +6.4 % (pool L24); drop-r1-both p 0.186 (pool L182);
  - pass p 0.102 / 0.105; arm x pass 0.601 / 0.612 / 0.308 / 0.370;
  - light share 0.974 / 0.972 / 0.975, F 1.18, p 0.320;
  - round-1 fps 415.1 / 407.0 / 395.9 vs 367.1-393.0; light 0.979-0.988 vs 0.962-0.978; r1 -1.95 / -4.63 (load-check L109/L111);
  - bands 3.3 / 2.9, CV 1.6 / 1.2; ±5.2 / ±6.4 (PROPOSAL L69) vs ±0.6 / ±3.8.
- **Section 3:**
  - all 24 cells (pool L32-46); CPU table (pool L54-57); L119 (load-check L101);
  - paired table (pool L67-71); L133-134 (load-check L106/L108/L110/L112);
  - L136 recomputed from load-check L105: 7/8, mean +0.48, median +0.30;
  - sign p 0.006 / 0.021 / 0.070 recomputed.
- **Tails:** the table and L146-148 were recomputed from tail-check L11-54:
  - p99.9 medians 5.390 / 5.479 / 5.429 and means 5.429 / 6.088 / 5.450; without 0221, 5.58;
  - counts 2/1/0, 46/28/6 and 6/2/0; runs with a frame > 8 ms 2/3/4;
  - longest frames 10.27 / 26.37 / 11.56.
- **Section 4:**
  - 0451 summary.md L12-14: 385.18 / 382.0 / 385.45, -0.83 % / +0.07 %, d median / d p99;
  - 3-decimal core means 2.5585 / 2.347 / 2.354;
  - L163 fps values, audit L25, 0155 summary values, L167.
- **Section 5:**
  - quiet table (load-check L81-83, with medians re-derived from section 8);
  - loaded table, all 63 cells (load-check L87-95), with every vs-arm % and "rest" value recomputed;
  - loaded means -3.0 / -1.1 %, ng_t 3.11 / 3.15, MHz -3.9 / -4.5 %;
  - rho -0.67 (p 0.002) / -0.32 (p 0.19) (load-check L74-75);
  - every 0221 cluster figure (cluster-0221.txt; tail-check L23);
  - L224 frame counts 0 / 7 / 1 (tail-check L19/L37/L29);
  - W5 p99 and 1 % low (PROPOSAL L69-72; RESULTS L103).
- **Section 6:**
  - all 22 rows × 7 cells, n per arm, round p and the labels (7)/(9)/(6)/(2)/(1)/(3) match pool-W5b.md L84-222; d11 n note (L270);
  - L174: cores -0.21 to -0.23 / -0.19 to -0.21;
  - L274: `*` only in all-36 fps and pass-2 raw fps; -0.2 to -0.6 % otherwise;
  - L275: -0.4 to -0.8 %, `*` only in no-slow-d11t;
  - L276-277: load-check L111, and recomputed from section 8 fps;
  - L278: -2.8 to -3.7 %, -5.1, -0.8, -0.6.
- **Flag sets:** identical everywhere:
  - in W5b at L42-45, L65-69, L136 (rounds r3/r7/r8/r9 excluded), L163, L191-203, L268-269, L290, L294;
  - in pool-W5b.md at L84, L112, L126, L140, L154.
- **Section 7:** SESSION2 L2260 and L3291; audit L30, L31/L450, L32-37, L431-434, L450, L34, L33, L422-424, L115, L37.
- **Sections 8-9:** they restate the above consistently. "2 arms x 4 metrics x 3 methods" = the 24 cells.
- **W9.md:**
  - L22: pool-W9.md L11-12 (PASS, 204 numbers, max |diff| 0, both passes);
  - L25-26: audit L211-238, L317-344, L373-402, L16/L20;
  - L27: the file exists; L28 OK; L29: see Notes;
  - L252-256: SESSION2 L3291 (0.81/0.87/0.68 at 04:46-04:49); audit L418, L30-37; first four W5b-2 runs at 04:54:46-05:01:48 with ng_t 2.84-3.76; L256 is hedged.
