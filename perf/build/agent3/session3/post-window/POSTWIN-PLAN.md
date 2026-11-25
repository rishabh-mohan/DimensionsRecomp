# M3 post-window queue (after the timed windows, ~06:05) - DRAFT for M10's rating

Nothing here is live. Files in this folder:

| File | What |
|---|---|
| `queue-postwin.jsonl` | 7 rows to append to `build/agent3/s4b/queue.jsonl` (6 + optional s33base2) |
| `s4b_check.py` | draft of `build/agent3/s4b/s4b_check.py` (live B8014B04): bin identity + positive controls for the new rows |
| `s4b_check.diff` | `git diff --no-index` live -> draft |
| `postcheck.ps1` | draft of `build/agent3/s4b/postcheck.ps1` (live 03822B00): cases for the new rows + `S33` (Agent 6's kit) |
| `postcheck.diff` | live -> draft |
| `test_draft.ps1` | dry-run of the draft checker on existing runs (results below) |

## Rows (order = file order; the queue takes the first ready row)

| id | bin | args | est | gate |
|---|---|---|---|---|
| s4bV0f | devoff4bv-bin | = s4bV0 (level-l, toypad, 600 s, hold=1 keep_watch=0 verify=1), tag s4b-V0f-c1off-verify-level-vfix | 600 | s4b_check s4bV0 branch + POSTWIN proofs + f10 |
| s4b07f | devoff4bv-bin | = s4b07r (hold=1 keep_watch=1 verify=1), tag s4b-07f-c1v-level-vfix | 600 | s4b07 branch + POSTWIN proofs + f10 |
| s33base | devoff4b-bin | attract-long, 540 s, -GpuLog, no cvars | 570 | check vs s4b03/RA + bin/no_wait proofs |
| s33off | devoff4b-s33-bin | same | 570 | check vs s33base (no allow-new) + **RUN-S33-LOGDIFF row 1a** (ref off) |
| s33basesf | devoff4b-bin | same + slow_frame_log_ms=1 | 570 | check vs s33base, allow slow frame/memexport |
| s33offsf | devoff4b-s33-bin | same + slow_frame_log_ms=1 | 570 | check vs s33basesf (no allow-new) + **row 1b** (ref offsf) + s33_fields.py |
| s33base2 (optional) | devoff4b-bin | = s33base, tag s33-base2 | 570 | base-vs-base spread for 1a; needs extra marker `go-s33base2` |

- V0f before 07f (Agent 12). Cvars at launch only. The arms are copied from `build/agent6/s33-popin/harness-s33.json` (4E30E135).
- Deviation from M6: the runs go to `build/agent3/runs` (the queue's default), not `runs-s33`, so postcheck finds them. The kit gets the run dirs explicitly.
- Every row needs `build\agent3\s4b\ready-s4b-off` and `build\agent3\session3\go-postwin`. go-postwin is created only on the Overseer's word.
- Duration: 600+600+4x570 = 58 min of game time, plus ~1 min of postcheck/quiet-check gaps per row: **~65 min** (~75 min with s33base2).

## What the draft checker adds (POSTWIN block, rows s4bV0f/s4b07f/s33*)

- The run.json bin_dir must be the planned bin.
- The run-dir copies of legodimensions.exe / rexgpu-xenos.dll / rexruntime.dll must match (sha256, first 16) the planned bin's MANIFEST:
  - exe DFBE1D43B28861A6 and rexruntime A33801D1538D6175 on all bins.
  - rexgpu: devoff4b E3CB99CFDEA95E66, devoff4bv 82A0DE742AAAAE44, s33 0B57BBD5D7B96CBD.
- s4bV0f/s4b07f, the positive controls per RATIONALE L102-105 (a miss on any = INCOMPLETE):
  - "C1 verify: on." x1.
  - The route reaches story-load (a level mark).
  - s4b07f only: last "kept so far" >= 32768.
- s4bV0f/s4b07f get a reading note:
  - F count vs s4bV0 F 70 / s4b07r F 51 (devoff4b, quiet host, 11-25).
  - F 0 = the fix removed the race. F > 0 = a non-race source; compare pages.
- s33*:
  - No "d3d12_pipeline_creation_no_wait" text in any game*.log.
  - The cvar is not set in run.json.
  - close_method wm_close.
  - sf rows: slow-frame lines > 0.
- The s4bV0f/s4b07f aliases reuse the s4bV0/s4b07 branches unchanged (incl. M10 S1: verify_on == 1).

## Dry-run results (`test_draft.ps1`, 02:55, at Below Normal)

| test | expected | got |
|---|---|---|
| s4bV0f on the s4bV0 run (devoff4b) | only bin dir + rexgpu MISS | yes: 2 proof misses (bin dir, rexgpu E3CB.. vs 82A0..); controls ok |
| s4b07f on the s4b07r run | same, kept 61440 >= 32768 ok | yes |
| s33base on w6-side3 attract run (devoff4b) | bin proofs ok, no_wait x0 | PASS?, 0 misses |
| s4bV0 on the s4bV0 run | identical to the live tool's output | 0 differing PROOF/VERDICT lines |

- Draft postcheck.ps1: PowerShell parser reports 0 errors.
- The S33 call shape (`cmd /c RUN-S33-LOGDIFF.cmd --run base=<dir> --run off=<dir> --ref off --matrix-json ... --out ...`) was run on two unrelated attract runs with --skip-logdiff:
  - Arms were read and counts printed.
  - Verdict FAIL as expected (wrong bins).

## Pre-launch bin identity (02:57, Get-FileHash, first 16)

| bin | MANIFEST | exe | rexgpu-xenos | rexruntime |
|---|---|---|---|---|
| devoff4bv-bin | 353846A3 (= M2) | DFBE1D43B28861A6 | 82A0DE742AAAAE44 | A33801D1538D6175 |
| devoff4b-s33-bin | 50CC5BE2 (= M2) | DFBE1D43B28861A6 | 0B57BBD5D7B96CBD | A33801D1538D6175 |
| devoff4b-bin | DE11A914 | DFBE1D43B28861A6 | E3CB99CFDEA95E66 | A33801D1538D6175 |

Re-hash just before launch. Optional: run `python -B build/agent3/s4b/bincheck.py build/agent2/devoff4bv-bin --set off` at Below Normal.

## Launch steps (on the Overseer's word, after M10 rates the drafts and the quiet rule is lifted)

1. Back up the live tools:
   - `s4b_check.py` -> `.bak-postwin`
   - `postcheck.ps1` -> `.bak-postwin`
2. Copy the two drafts over the live tools. Python takes effect at once; the postcheck change needs a restart.
3. Re-hash the three bins (table above).
4. Append `queue-postwin.jsonl` to `build/agent3/s4b/queue.jsonl`:
   - Back up the queue first.
   - Drop the s33base2 line if it isn't wanted.
5. Start hostload, postcheck and the queue, with `-LastLaunch`/`-GamesClosed` as the Overseer sets them.
6. Create `build\agent3\session3\go-quiet` and `build\agent3\session3\go-postwin`, plus `go-s33base2` only if wanted.
7. Report each row. Row 1 (1a and 1b) must pass before anything else from #33 (TESTPLAN).

## Reading

- **s4bV0f vs s4bV0 (F 70):**
  - F 0 on the fixed bin: the race was the F source (fix works).
  - F unchanged: a non-race source.
  - Gate A (K 0) is unchanged in either case.
- **s4b07f vs s4b07r (F 51):** same reading. K must stay 0 and kept must stay >= 32768.
- **#33 1a/1b:** pass = the kit's verdict has no FAIL with ref = the OFF arm, and no_wait text x0. Base-vs-off differences should be within the base spread (s33base2, if run).

## 06:28 launch notes (after M10 `build/agent10/session3/postwin-rating.md`: SAFE-IF)

- P1 at 06:28:
  - The live tools were B8014B04 / 03822B00 (the left sides of the diffs).
  - Installed drafts 09DBCABC / 8B60EBC3; backups `*.bak-postwin`.
  - The bins re-hashed the same as the 02:57 table.
  - queue.jsonl backup `queue.jsonl.bak-postwin` (283D2F8E).
  - The rows appended are `queue-postwin-live.jsonl`: s33base2 is dropped (Overseer), and #33 per-row gates are added (below).
- **Stop at the first #33 FAIL: per-row markers.** M3 creates each one by hand after reading the check:
  - `go-s33off`, created when `logs/s33base.check.txt` ends in `VERDICT HINT PASS?`.
  - `go-s33-1b`, created when row 1a passes (P3).
  - `go-s33offsf`, created when `logs/s33basesf.check.txt` ends in `PASS?`.
- **P3 (strict 1a/1b rule).** Row 1a passes only if all three hold:
  1. `logs/s33base.check.txt` and `logs/s33off.check.txt` both end in `VERDICT HINT PASS?`, and they name the run dirs the kit got (`logs/s33off.s33.txt`).
  2. The kit exits 0 with ref = off.
  3. no_wait text appears x0.
  
  Row 1b passes on the same rule for s33basesf/s33offsf, plus `s33_fields.py` exit 0.
- **P4.** Before any re-run, move the old `logs/<id>.check.txt` and `<id>.s33.txt` (and `checks/s33-row1a|1b`) aside to `logs/old/`. Then confirm that the check names the re-run's dir.
- **P5.** The F comparison (s4bV0 F 70, s4b07r F 51) assumes a quiet host. Each report quotes the queue's quiet-check line and the hostload busy rows. If the host was busy, the F comparison is weaker, and the report says so.
- **N1 (M10).** s4b07f F 0 / K 0 settles item 2(b) only for this route. It does not make C1-without-P2 a default or a timing arm. "C1 ships as p2fc" stands until the Overseer decides otherwise (RATIONALE L109-111).
- **N2.** The #33 runs are in `build/agent3/runs` (not M6's `runs-s33`); the kit gets the dirs explicitly. Recorded here and in `build/agent3/SESSION3.md`. M6 owns TESTPLAN, so M6 should note it in the results there.
- **N3.** The s33base check vs RA is a different route: its logdiff is not an identity result. The kit is the gate.
- **N5.** The dry-run outputs are copied to `dryrun/`.
