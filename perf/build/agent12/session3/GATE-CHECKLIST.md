# Session-3 functional-run gate checklist (M12, S3T-12)

M12, 2026-11-25 ~01:35. Applies to every session-3 functional (untimed) row: M3's `build/agent3/session3/queue-s3.jsonl`
(s4bQ5, f10a3, f10b3, s4b07r, s4bV0, s4bLV, f10aL, f10bL) and the proposed s4b07f / s4bV0f
(`c1-verify-fix/RATIONALE.md`). Nothing here runs a game; M12 applies it read-only to finished run dirs after RUN GO.
Verdicts: PASS, WARN (finding 10 only), CHECK (needs the Overseer's call), INCOMPLETE (positive control or coverage
missing), FAIL.

## Tools (all read-only on run dirs, run at Below Normal, one at a time)

- `build/agent3/s4b/s4b_check.py` (M3): switch proof lines, K/F counts, coverage, errors. Note: it tests only the
  owner lr *range* 83FAF180-83FAF25F for STUCK-LOCK, so it is not the finding-10 verdict.
- `build/agent3/session3/f10_rule.py` (M3): the strict finding-10 rule; exit 0 PASS, 1 WARN, 2 FAIL, 4 error;
  `--no-level` for menu routes.
- `build/agent12/p2c-check/p2c_check.py <run dir>`: P2c memexport full-buffer total must be 0 in P2 rows.
- `build/agent12/session3/manifest_check.py`: the bins' MANIFEST hashes, before the first row and after the last.

## Common gates (every row)

| # | gate | rule | source |
|---|---|---|---|
| C1 | exit | `run.json` exit_code 0, `wer_seen` false, `crash_events` empty, no REX_FATAL | run.json, game.log |
| C2 | bin | `run.json` bin_dir = the queued `-BinDir`; that bin's MANIFEST re-hashes clean | run.json, manifest_check.py |
| C3 | switches as queued | every queued cvar/env has its proof line exactly as expected and nothing else: "C1 keep-watch: on (with physical_protect_hold_global_lock)" ×1 iff keep_watch=true; "C1 verify: on." ×1 iff verify=true; back-off init line ×1 with its Q iff `LEGO_GPU_WAIT_BACKOFF_US` set; "C1 keep-watch: on, but physical_protect_hold_global_lock is off" or "...blocked for this process (native renderer)" = FAIL in a Xenos row | game.log, s4b_check.py |
| C4 | no bad lines | 0 × "Recovered stale physical page protection", "Unhandled guest physical write fault", "PhysicalHeap::Protect failed" | game.log |
| C5 | finding-10 rule | see below; any other STUCK-LOCK = FAIL | f10_rule.py + by hand |
| C6 | dumps | a `hang-*.dmp` is allowed only as part of a finding-10 event; any other dump or crash dump = FAIL | run dir, game.log |
| C7 | coverage | the route's marks reached: level routes (`level-l.txt`) need the `vortex` mark (the level); menu routes `--no-level`. Record steps n/119 and story-load time | input.csv, s4b_check.py |
| C8 | host state | the queued gate holds for the whole row: go-quiet rows = no build/compile/regen running, no other game or heavy load (record the top CPU processes from the row's sys log if present); go-load rows = `cpuload.ps1` running; go-user = user load allowed. A quiet row that ran under a build = CHECK (re-run, Overseer's call), never PASS | M3's queue notes, sys/gpu csv |
| C9 | leftovers | no leftover `legodimensions`/rexlego process after the row; Minecraft is never touched or counted | the queue runner's log |
| C10 | logdiff | warning kinds new against the reference row of the same config (gate_logdiff) = CHECK, not FAIL, unless a fail pattern | Agent 6 / gate_logdiff.py |

## The finding-10 rule (SESSION2 L3128-3132, Agent 1 22:55 + 23:00 correction; RESUME §6 item 3)

A STUCK-LOCK counts as **"WARN, finding 10"** only if **all** hold, else **FAIL**:
1. critical section 0x84959EDC;
2. the owner is the render thread (tid 0x17 in all 4 Nov-22 hangs), parked in sub_83FAF180 at **lr 83FAF188 or
   83FAF200**; the waiter's caller is **lr 82A2A270**;
3. it recovers by itself (game.log goes on after the event), with no crash and no WER;
4. the run still reaches the level. For s4bLV also 3/3 LOADs and K 0 / F 0 over the whole run.

M12 note for M3 (via the Overseer): `f10_rule.py` parses the owner tid but doesn't test it. Apply item 2's tid by
hand: an owner tid other than 0x17 is CHECK (is it still the render thread?), not an automatic WARN.

## Row-specific gates

| row | extra gates | PASS means |
|---|---|---|
| s4bQ5 (q500 stats, menus route, user load OK) | back-off init line ×1 with Q = 500 and spin 30; **`sleep_fail == 0` in every stats line**; stats lines present (else INCOMPLETE) | q500's functional precondition (RESUME §6 item 1) |
| s4bN4 (4 KB re-run of s4bN16, Overseer 01:47) | as s4bN16 at 4 KB; 0 counter lines again → record fallback A (W7 title arms can't show #18) | the ready-N measurement, second try |
| cg26b0 (first boot of devoff4b-cg26-bin, s4b01 args, menus-long, default switches) | bin = devoff4b-cg26-bin, MANIFEST 917AE86E, exe 45952D17; 0 STUCK-LOCK; **no** back-off init line; logdiff vs s4b01 NEW 0; M10 r26 cond 4 (exit 0, no dump/WER, K 0 / F 0; "level reached" N/A on the menu route, recorded as such) | S1 of r26-cg26.md; W10 depends on it |
| cg26L (devoff4b-cg26-bin, s4b07r shape: L route + toypad, 600 s, no cvars/env; Overseer 01:49) | bin/MANIFEST/exe as cg26b0; r26 cond 4: exit 0, no dump/WER, `vortex` reached, K 0 / F 0 (trivially 0 with verify off, noted); C5 strict (r26 cond 5: STUCK-LOCK count reported); no back-off init line; no keep-watch/verify lines | r26 cond 4 on a level route |
| win3f (full win3 arm of matrix-windowC.json) | every cvar/env of the arm matches the matrix exactly (p2fc set + 8 timer cvars + timer_queue_precise_wait; env BACKOFF 500 / SPIN 30); back-off init "quantum 500 us, spin 30 us" ×1; keep-watch init ×1, no verify line; precise-wait proof line; C5 strict; P2c 0 if a level route; level reached if a level route | gates WC1 |
| c1npf (hold_global_lock + keep_watch, verify=false) | keep-watch init "on (with physical_protect_hold_global_lock)" ×1; 0 "C1 verify" lines; K/F 0; C4 zero; C5 strict; level reached if a level route | gates WC1 |
| s4bN16 (READY-N option C: s4b25's title args, `d3d12_submit_split_kb=16;framerate_limit=0`, no route, 180 s, quiet preferred) | `d3d12_submit_split:` counter lines present (else INCOMPLETE: no N can be read); splits > 0; `failed` 0 and `held_*` ~0 over the run (else CHECK: too few splits were due); 0 BASE misses vs RT beyond `d3d12_submit_split` (postcheck); C7 = no route (title scene), C5 with `--no-level`; record Δsubmission, Δsplits, Δframe → K = (Δsub − Δsplits)/Δframe, KiB/frame ≈ 16·Δsplits/Δframe + leftover, N = ½·KiB/frame/K (M12 reports the numbers; M3/Overseer set ready-N) | the ready-N measurement (added 01:39) |
| f10a3 / f10b3 (quiet) | C5 strict; f10b3 (p2fc) also P2c total 0 and the p2fc proof lines (kw_on, first kept protect, no verify line) | finding 10 doesn't reproduce quietly (add to Agent 3's 0/4) |
| f10aL / f10bL (controlled load) | C5 strict; a finding-10 WARN is an expected possible outcome here, recorded with its time and dump; f10bL P2c 0 | load vs quiet comparison (RESUME §6 item 3 follow-ups) |
| s4b07r (row 7 quiet, devoff4b) | K/F counts; F pages, threads, times vs INSTALL*.DAT bursts; positive control as RATIONALE.md | reports F (expected > 0 if the race shows without load) |
| s4bV0 (C1 off, devoff4b) | no keep-watch lines; "C1 verify: on." ×1; F count, pages, thread | option (a): F > 0 on ~01AE8000-022BF000 confirms the race; F 0 refutes it (C1 suspect) |
| s4b07f / s4bV0f (devoff4bv) | as RATIONALE.md "Row-7 re-run plan" | option (b): s4b07f F 0 / K 0 with its positive control |
| s4bLV (p2fc + verify, 1800 s) | 3/3 LOADs; `vortex` reached; K 0 / F 0 over the whole run; positive control (kw_on, first kept protect, kept count growing, verify on); P2c 0; the fixed sidecar in use; C5 strict | the first of C1's two default-on conditions (RESUME §6 item 2) |

## Waivers

Only the Overseer waives, by message, per run dir; M12 records the waiver text and time next to the raw verdict
(as for gate A/B on Nov 22: raw FAIL + "WARN, finding 10, Agent 1 22:25").

## FINAL bins (07:41)

The F1-F7 gates for M2's FINAL bins (devfinal, devfinal-off, nativefinal, nativefinal-off) are in `FINAL-F-GATES.md` and `final_gate.py`. On a FINAL bin, row_gate.py skips the C3 init-line checks; final_gate.py checks those lines instead, through the rated check-defaults.py.
