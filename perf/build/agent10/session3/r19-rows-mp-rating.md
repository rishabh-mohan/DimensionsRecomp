# #19 rows package (M7) + #21 MP2/MP3 tools: rating

M10 (successor of Agent 10), 2026-11-25 ~02:40. Paper rating, read-only. No game, build or queue change. I re-ran M7's selftest, the queue check and one gate on a real run (outputs in `build/agent10/session3/scratch-r19rows/`).

## Files rated

| file | sha256 (first 16) | bytes |
|---|---|---|
| `build/agent7/session3/queue-r19.jsonl` | A17F398BC9DA3AFE | 10888 |
| `build/agent7/session3/r19_gate.py` | 1DD4A89EEBAB0929 | 9867 |
| `build/agent7/session3/check_queue_r19.py` | 298BB3EC29D5B3BA | 8814 |
| `build/agent7/session3/ROWS-R19.md` | 5BC934469A24A9B2 | 13975 |
| `build/agent7/session3/test_r19.py` | B017F62CA932D337 | 8574 |
| `build/agent7/session3/SHA256SUMS-r19.txt` | E3E7AE294EB30FF9 | 1298 |
| `build/agent7/s4-r1s2/soak-check/soak_check.py` (imported, unchanged) | CAB5CB2CCA686C67 | - |
| `build/agent7/session3/mp/README-MP.md` | 1ADBAF9679622B13 | 11259 |
| `build/agent7/session3/mp/mp2_same_frames.py` (glance) | 442E2AFC1A06F803 | 27864 |
| `build/agent7/session3/mp/mp3_query_seq.py` (glance) | B63DD35A452CF1B5 | 13541 |

All entries in SHA256SUMS-r19.txt match.

## Base

- My `r19-rating.md` (296658C5), conditions (b) 1-6 plus S1/S2.
- `build/agent3/s4b/s4b-queue.ps1`:
  - `<N>` is replaced from ready-N line 1, L140-142;
  - every `needs` path must exist, L137;
  - waiting rows are passed over, not dropped;
  - `toypad` starts the sidecar, L206.

## Verdict

- **Rows package: SAFE-IF**, under conditions C1-C4 below. It enforces every condition of my rating:
  - (b)1/(b)2, order and stop at the first FAIL: the r19-ok chain plus check Q2/Q4.
  - (b)3, RUN GO: `go-r19on` on every ON row, plus `go-quiet`.
  - (b)4: hang or timeout is a FAIL; the shutdown watchdog in an ON row is a FLAG (exit 3); triage starts from the GPU Commands / D3D12 Submit stacks; STUCK-LOCK follows f10_rule.
  - (b)5/S2, combination guard: Q7, which I checked in the code. It forbids `d3d12_pipeline_creation_no_wait`, `*resolution_scale*`, `native_*`, `-Env` and ctr/native bins, and allows async only on #19 rows.
  - (b)6: `<N>` only via ready-N (Q5).
  - S1: row g runs before j, d, f, e.
- **Bin name** `devoff4b-r19-bin`: fine; it is the name Q3 checks.
- **Q2, row d no-op under fallback A: CONFIRM, with C1.**
- **Q3, r19r10 shows no split at N: CONFIRM for c and f. OBJECT for i and g as worded; C2 gives the fix.**
- **Q5, the 5 ref rows (~21 min): CONFIRM.** They use the devoff4b-bin #18 split path only, which s4bN16 already exercised. r19r11 needs no ready-N and runs first, so it gives early 16 KB split evidence.
- **MP2/MP3 calls: CONFIRM, with C4** on how "LS info-only" is applied. The tools are read-only: they only lower their own priority and write `--json`. No subprocess.

## Checks done

1. `python -B test_r19.py` printed SELFTEST PASS 50/50 (exit 0). `check_queue_r19.py` printed ALL CHECKS PASS (183 checks; exit 0). Both outputs match M7's.
2. `r19_gate --row d --n 16` on the real `20261125-014239-s4b-N16-title-split16` run gives FAIL (no async init) plus INCOMPLETE. That is the expected negative control, and it matches M7's offline-d-N16.
3. **No-op shape, synthetic.** I took the same real log and inserted one async init line `d3d12_async_submit: submitting splits on the submit thread (3 slots)`, which is what a #19 ON run at a non-splitting N prints. `gate(..., 'd', n='16')` then returns:
   - fails `[]`;
   - flags `[]`;
   - incomplete exactly one entry: `at least 2 async counter lines (found 0)  [no async counter line: no split was due at this N]`.

   So a pure no-op can be told apart by machine from every other INCOMPLETE (C1).
4. Read in full: queue-r19.jsonl, r19_gate.py, check_queue_r19.py, ROWS-R19.md, README-MP.md. Also the needs and `<N>` handling of s4b-queue.ps1.
5. r19_gate verdict order: FAIL, then INCOMPLETE, then FLAG, then PASS. The watchdog FLAG shows in the exit code **only** when there is no FAIL and no INCOMPLETE. On an INCOMPLETE row the flag is only in the JSON `flags` list. C1 and C2 cover this.

## Conditions

- **C1 (Q2: when a row may be marked "no-op").** M3 may write `r19-ok-d` marked no-op only if all of these hold:
  1. r19_gate exits 2, and its `--json` has `fails == []`, `flags == []`, and `incomplete` equal to exactly the single "no async counter line: no split was due at this N" entry. That means the async init ×1 and the #18 init at N were both seen.
  2. s4b_check has no FAIL (clean exit, no dump, no hang, logdiff vs r19r25 within allow-new), and the run is valid per ROWS-R19 section 2, run 3.
  3. The ref r19r25 also has 0 `d3d12_submit_split:` counter lines at the same N. If the ref splits and row d doesn't, that is a discrepancy: stop and report.

  Any other INCOMPLETE, any FLAG, or a hang/crash stops the chain. The marker text says `no-op (fallback A, N=<N>)`. The W7 s19 arm is then a no-op: don't time it as a #19 arm and don't report a #19 speed-up from it.
- **C2 (Q3: what to run instead of holding).** Define "r19r10 shows no split" by machine: `r19_gate --row i --n <N>` on r19r10 is INCOMPLETE with only the "no split line" entry. Then:
  - **Row i must not be skipped.** My rating (b)1 needs an OFF split proof on the #19 bin before any ON row. Replace i with **i16**: split 16, no async, #19 bin, base r19r11, `r19_gate --row i --n 16`. Running i at N anyway as a no-op under the C1 rule would only prove the init, so prefer i16.
  - **Row g must not be skipped.** My S1 needs the debug-layer ON row with real splits before soak e and W7. Replace g with **g16**: debug + split 16 + async, `s4b_check --row s4b15` (DRED line, no debug-layer enable failure), base r19r15 with `--allow-new "d3d12_(async_submit|submit_split)"`, `r19_gate --row j --n 16`. Use the j rule set; J1 (full_waits) INCOMPLETE is acceptable here.
  - Rows c and f may be held as no-op, chain-wise. But until f has passed with real splits, no ON use may set `d3d12_readback_memexport=true`. That cvar is not set in e or W7, so the drain path stays untested but unused.
  - Run j as written. It is then the first ON row with real splits.
  - i16 and g16 are new queue lines. Add them to `check_queue_r19.py` SPEC19 (with the chain re-pointed) and re-run it before the append. Small, so no re-rating is needed if only these two rows and the chain change.
- **C3 (end of chain).**
  - Row e INCOMPLETE (no split line on the level route at N) ends the chain. W7 doesn't run, since it would be a no-op.
  - The #19 final report lists, per row, whether splits really happened (`chunks > 0` in the last async line). W7 needs at least j plus e PASS with real splits; no-op rows don't count.
- **C4 (MP2 "LS info-only").** mp2_same_frames has no LS-info switch: with `--spread-k 1` an LS line can still FAIL and set exit 1. Do one of these two:
  - (a) add a `--ls info` option. A small tool diff; send it to me, quick rating.
  - (b) write into the F1 row notes that the MP2 verdict is the LOG checks only (plus DC where draw_calls > 0) and LS lines are read as info. The reader then quotes the JSON, not the exit code.

  Don't override an exit-1 FAIL by hand without that written rule.

## Findings

- **S1 (SHOULD), C2:** "held" for i and g would break my rating's (b)1 and S1. Use the 16 KB substitutes.
- **S2 (SHOULD):** with `--zero-dc info` and LS as info, MP2 on native routes is **log equivalence only**. Record it in the #21 proof table as "MP2 = no NEW/GONE/MORE log keys; frame identity not proven", not as "same frames".
- **N1:** r19_gate checks no bin identity. A row that by mistake ran on devoff4b-bin would pass row a. Same as my M3 review S3. Add a check that the run dir's exe hash equals the hash in `devoff4b-r19-bin` MANIFEST for r19 rows and DFBE1D43 for refs, either in s4b_check or by hand at row a.
- **N2:** r19r25's s4b_check base is s4bN16 (16 KB) while it runs at N. Whether the init line `at N KB` vs `at 16 KB` counts as NEW/GONE depends on logdiff's number normalisation. If it shows, it is the known init key; not a defect.
- **N3:** row b fails if SetupContext ever runs twice (2 WARN lines). That's correct per the rule; just know where it comes from.
- **N4:** MP3's parser was never validated on a real `Native query value` line (README finding 4). Eyeball the first real F3 trace before trusting its numbers. F3 stays UNCLEAR as you said.
- **N5:** the ROWS-R19 section 1 note "Drop a ref line if M3 already ran that S4b row" changes the base: update the r19 rows' `--base` too.

## Read/Sent

Read: the files in the table; `r19-rating.md`; `s4b-queue.ps1` L1-25, L44, L137-142, L206-221; marker listing (`ready-dbg`, `ready-s4b-off`, `go-quiet` exist; `ready-N`, `ready-r19` and `go-r19on` don't yet).

Sent to the Overseer on writing.
