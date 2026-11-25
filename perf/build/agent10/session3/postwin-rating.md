# Post-window drafts rating (M3: s4bV0f / s4b07f on devoff4bv-bin, #33 rows 1a/1b on devoff4b(-s33)-bin)

M10 (safety reviews), 2026-11-25 03:15. Paper review: read_file and write_file only, because the quiet rule is in force. I ran nothing, and I computed no hashes.

## Files rated (sha256 prefixes from the Overseer's 03:09 message; I could not recompute them)

| file (`build/agent3/session3/post-window/`) | sha256 (Overseer) | notes |
|---|---|---|
| `POSTWIN-PLAN.md` | 4C443FE5 | 96 lines |
| `queue-postwin.jsonl` | 17EBA0F5 | 7 rows |
| `s4b_check.py` (draft) | 09DBCABC | 946 lines; vs live B8014B04 |
| `s4b_check.diff` | E3F446E3 | blob 29cc74f -> 604822a, +71/-1 |
| `postcheck.ps1` (draft) | 8B60EBC3 | 158 lines; vs live 03822B00 |
| `postcheck.diff` | BF406FB2 | blob ff2cc3d -> 2667642 |
| `test_draft.ps1` | 6EDB2725 | writes only to `%TEMP%\m3pw` |

Also read (hashes not recomputed):
- `build/agent6/s33-popin/harness-s33.json` (plan: 4E30E135);
- `build/agent2/devoff4bv-bin/MANIFEST.txt` and `build/agent2/devoff4b-s33-bin/MANIFEST.txt`;
- `build/agent12/session3/c1-verify-fix/RATIONALE.md` L98-122.

Measured against: `c1-verify-fix-rating.md` (AFBFFBDF) and `r33-nohunk5-diagd.md` (B24EE8E2).

## Verdict: SAFE-IF

- Drafts and queue rows: SAFE-IF (conditions P1-P5).
- No BLOCKER. 2 SHOULD, 5 NIT.
- I found no path where the drafted checks print `PASS?` for a bad candidate run.
  - `chk(False)` makes a proof MISS, and any MISS or BASE miss turns the hint into `LOOK`.
  - The new proofs only add MISS chances. The existing BASE items (exit, WM_CLOSE, dumps, crash events, `[error]`/`[critical]`, stuck_lock, protect_failed, clean exit) all still apply to every new row.
- The one false-PASS path is in the #33 kit step, not in s4b_check: the base arm is chosen by row id and not by verdict. P3 covers it.

### Against the C1 verify-fix rating conditions

| C1 rating condition | status in the drafts |
|---|---|
| 1. RUN GO + `go-quiet`, hidden desktop; V0f before 07f | Met. Both rows need `ready-s4b-off` + `go-postwin`, and launch step 6 creates `go-quiet`. Queue order: V0f is line 1, 07f line 2. |
| 2. Cvars at launch only, no runtime flip | Met. Both rows use `-Cvar` at launch only: hold=1, keep_watch=0/1, verify=1. These are s4bV0/s4b07r's sets with only `-BinDir` and `-Tag` changed, as in RATIONALE L98-100. |
| 3. s4b_check knows the ids; bin checked by MANIFEST (my S2) | Met. The aliases are `s4bV0f -> s4bV0` and `s4b07f -> s4b07`, so the branches are unchanged, including my S1 check (`c1_verify_on == 1`). POSTWIN adds three checks: the bin-dir basename, then the run-dir copies of exe DFBE1D43, rexruntime A33801D1 and rexgpu 82A0DE74. All three match the devoff4bv MANIFEST, which I read. |
| 4. Positive controls RATIONALE L102-105, else INCOMPLETE | Met. Details below. |
| 5. STUCK-LOCK: finding-10 rule | Met. The F10 regex now has `s4bV0f?` and `s4b07[rf]`. `stuck_lock` is also a BASE miss. |
| 6. Reading per RATIONALE L107-118 plus my addition | Mostly met: the plan's Reading follows RATIONALE. My addition is missing (N1). |

Positive-control details (condition 4):
- For s4bV0f, the s4bV0 branch checks init-on, first and kept are all 0 (L105: "no keep-watch lines"), and `C1 verify: on` appears x1.
- For s4b07f, the s4b07 branch checks:
  - init-on x1;
  - first kept >= 1;
  - verify on;
  - K == 0 (gate A);
  - kept count rises;
  - G8.
- POSTWIN adds `C1 verify: on` x1, the `story-load` mark, and, for 07f only, last kept >= 32768.
- Any miss gives `LOOK`. The plan and the proof texts call it INCOMPLETE, as required.

### Against the #33 nohunk5/(d) rating conditions

| #33 rating condition | status |
|---|---|
| Row 1 (1a, 1b) first; stop if it fails | Met. Launch step 7: no other #33 row is queued. |
| s33 bin: no_wait needle present, (d) needle absent; exe/rexruntime = devoff4b; no cache/seeds | Met by M2's MANIFEST: needles ON-has `d3d12_pipeline_creation_no_wait`, ON-lacks `d3d12_resolve_after_drop_log`; CTL PASS; exe DFBE1D43 and rexruntime A33801D1; no cache/ listed. POSTWIN pins rexgpu 0B57BBD5. |
| Identity rows on a (d)-free bin | Met. The s33 rows use devoff4b-s33-bin, never s33d. |
| E3CB99CF kept intact | Pinned. The base rows require E3CB99CF in the run dir. |
| r33 N3: never allow no_wait lines in off arms | Met. s33off and s33offsf get no `--allow-new`, the kit gets none, and the no_wait text must appear x0. |

## Conditions

- **P1: confirm the hashes at launch.**
  - Before step 2, the live tools must still be B8014B04 and 03822B00, which are the diffs' left sides. Otherwise the diffs are stale: regenerate them and bring them back.
  - The drafts copied in must be 09DBCABC and 8B60EBC3, the versions I rated.
  - Re-hash the three bins as the plan says.
- **P2: P1-P5 of this file are run conditions.** Nothing goes live and `go-postwin` stays absent until the Overseer lifts the quiet rule and the timed windows have ended (the plan already says this).
- **P3: the #33 row 1 pass rule needs both arms valid.**
  - Postcheck's `B 's33base' ''` takes the latest s33base run by id, whatever its verdict.
  - So a crashed or short base arm could still go into the kit, and a likewise-broken off arm might then "match" it.
  - Row 1a passes only if all three hold:
    1. `logs/s33base.check.txt` and `logs/s33off.check.txt` both end in `VERDICT HINT PASS?` and name the run dirs the kit got (`logs/s33off.s33.txt`);
    2. the kit exits 0 with ref = off;
    3. no_wait text appears x0.
  - Row 1b passes on the same rule for s33basesf and s33offsf, plus `s33_fields.py` exit 0.
- **P4: re-runs.**
  - Postcheck skips any id whose `logs/<id>.check.txt` already exists. A re-run of s33base or s33off would therefore get no new check and no new kit run, while `B` hands the re-run's dir to later rows.
  - For any re-run: move the old `logs/<id>.check.txt` (and `<id>.s33.txt`) aside first, or run the check and the kit by hand. Then confirm that the run dir named in the check file is the re-run's.
- **P5: s4bV0f/s4b07f reading.**
  - The F counts are compared with s4bV0 F 70 / s4b07r F 51. Those come from 02:04-02:14 on a quiet host.
  - The post-window rows must also run with the `go-quiet` gate (postcheck's host_quiet info line). If the host was busy, treat the F comparison as weaker and say so in the report.

## Findings

- **S1 (SHOULD): consumer scan for the s33 bin's changed headers.** M2 built devoff4b-s33-bin dependency-scoped: 10 TUs, including the header `include/rex/graphics/d3d12/pipeline_cache.h` and the private `src/graphics/frame_stats.h`.
  - That is the same method I ruled ACCEPT-IF for #19 (`r19-build-method.md`), and its CTL compare PASSes.
  - But my consumer scan covered only #19's two headers. Once commands are allowed, before `go-postwin`, run this (BelowNormal, read-only, ~2 s): `python build/agent10/session3/scratch-r19build/ninja_deps_scan.py build/agent2/<snap1-sdk|snap1-off|snap1-on>/.ninja_deps d3d12/pipeline_cache.h graphics/frame_stats.h`
  - Expect 10 rexgpu-xenos objects in snap1-sdk and 0 in the game builds. If anything outside rexgpu-xenos shows up, hold the s33 rows.
  - Row 1a would probably catch a layout mismatch anyway (crash or log divergence), but the scan makes it certain.
- **S2 (SHOULD): s33base2 is never compared automatically.** The plan says it gives "the base spread for 1a", but postcheck only runs s4b_check on it against s4b03/RA. If it runs, also run the kit by hand: `--run base=<s33base> --run base2=<s33base2> --ref base` (or s4b_check `--cand s33base2 --base s33base`). Read 1a's base-vs-off differences against that spread.
- **N1.** Add my C1-rating reading line to POSTWIN-PLAN "Reading": s4b07f F 0 / K 0 settles item 2(b) only for this route. It does not make C1-without-P2 a default or a timing arm; "C1 ships as p2fc" stands until the Overseer decides otherwise. RATIONALE L109-111 says nearly the same.
- **N2.** The `runs-s33` -> `build/agent3/runs` deviation is fine:
  - The kit gets the dirs explicitly (`--run ARM=DIR`).
  - The matrix-json `RunsRoot` text is only a note.
  - POSTWIN pins the bin by hash; the kit compares only the listed cvar keys.
  - Record the deviation in M6's TESTPLAN results so later #33 rows look in `build/agent3/runs`.
- **N3.** `s33base` is s4b_check'ed against `B 's4b03' $RA`, which is a different route (attract vs attract-long) with u-diag cvars on RA. Scenes, marks and GONE are then not judged (the base scenario differs), and the NEW lists are info only. This is harmless for safety, because the kit is the gate. Just don't read the s33base logdiff as an identity result.
- **N4.** The postcheck S33 call writes the kit output to `build/agent3/s4b/checks/s33-row1a|1b`. A re-run overwrites it (see P4). Keep the first output if a re-run happens.
- **N5.** `test_draft.ps1` writes to `%TEMP%\m3pw` (outside the WS). That's fine for a dry run. Copy the 4 result files into `post-window/` if they are to be cited as evidence.

## Read / sent

- Read:
  - all 7 files in the table, including the draft `s4b_check.py` L440-946 (`row_proofs`, `main`, hint logic) and the full draft `postcheck.ps1`;
  - `harness-s33.json`;
  - both bin MANIFESTs;
  - RATIONALE L98-122.
- Sent at 03:15: the verdict to the Overseer. This file's sha256 is not computed (no run_command window); I will send it once commands are allowed.
