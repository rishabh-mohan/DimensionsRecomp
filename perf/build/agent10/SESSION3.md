# M10 (successor of Agent 10): session 3 log

- 01:26 S3T-10 received: rate #19 (`build/agent7/s4-r1s2/`, RATE-REQUEST 1C2B8688A43ED4DC). Read BRIEF-COMMON, HANDOFF, RESUME (7616A164..., unchanged) §2, §6, §7.
- 01:27 Base check: the 6 orig/ files == `git show 5350b1d:<path>` == snap1 == live SDK worktree (LF). Started E10.1 (queue-ops / flush-caller / Execute-state code read, writes `session3/sub-r19-queueops.md`).
- 01:30 Re-applied the diff to a scratch copy of orig/ (`-c core.autocrlf=false`): 5 files byte-equal to new/sdk; scratch deleted. SHA256SUMS: all present entries match.
- 01:36 #19 rated: `session3/r19-rating.md` (296658C50E4D4973). (a) SAFE as a default-off test bed; (b) SAFE-IF, 6 conditions; (c) ACCEPTED. 2 SHOULD (S1: move row g earlier; S2: no #19 ON combined with #33 ON, the counters build, native bins or res scaling), 8 NIT. F-CA does not apply. E10.1's sub-report `session3/sub-r19-queueops.md` (E03648C6). Sent.
- 01:42 #26 CG26 rated: `session3/r26-cg26.md` (423FE10F96F475DE). SAFE-IF for W10, 7 conditions, 1 SHOULD (the hidden-desktop functional run first), 3 NIT. Re-ran Agent 9's kit: PASS (`build/agent10/cg26-check/`, report E2B0E2E7). Control exe vs snap1-off: only the PE timestamp differs (`scratch/bindiff.py`). Sent.
- 01:46 C1 verify-only fix rated: `session3/c1-verify-fix-rating.md` (AFBFFBDF47C7CFC5). Code SAFE; build devoff4bv SAFE-IF (S1: keep the shared snap1-sdk `rexgpu-xenos.dll` E3CB99CF intact); rows s4bV0f, then s4b07f, SAFE-IF (S2: s4b_check.py branches plus a bin check, to be rated as a runner change). 3 NIT. Sent.
- 01:51 #33 nohunk5 (57CFA8AD) + diag (d) (6CF9377E) rated: `session3/r33-nohunk5-diagd.md` (B24EE8E2A9645299). Both SAFE; build SAFE-IF (a fresh 5350b1d tree per bin, E3CB99CF intact, DLL needles). S1: four bins rebuild rexgpu-xenos, so build one at a time. 3 NIT. The scratch apply reproduced TESTPLAN §0 and the (d) column; scratch deleted. Sent.
- 01:54 Q=500 default-ON (28F0D1DE) rated for the final build: `session3/q500-default-rating.md` (DB5D1282FFFF5F8D). Code SAFE; default ON SAFE-IF, 5 conditions (step-B gates, the shipped combination, land late or -D -1, harness first, compile/bin checks). S1: `off` on old bins logs a WARN that every expect file forbids. S2: env is the only end-user off switch. 3 NIT. The scratch apply gave 74115EEA == new/; scratch deleted. Sent.
- 01:55 Queue empty. Open on call: runner changes (M3's s4b_check.py for s4bV0f/s4b07f), M4's repin_check.ps1 edit (order: key check [4] L291 fix, then native4b in `$oldBins` L390, then `$PINS` L130).
- 01:58 M3 read-out tools reviewed (wc_proof.py DDDEFD75, s4b_check.py E075FCD5 vs bak-0628, postcheck.ps1 8054C296 vs bak-0628, f10_rule.py 3B849D2E): `session3/m3-readout-review.md` (D7806C9E4CA8CE14). SAFE to use. S1: s4bV0 must require verify armed. S2: f10_rule's "recovered" accepts any later line, so require progress. S3: wc_proof cg26 has no bin-identity check. 4 NIT. wc_proof on cg26b0: PASS 9/9 (exe 45952D17). Sent. Waiting for M8's runner changes.
- 02:13 M8 staged runner improvements rated: `session3/m8-runner-rating.md` (C08604D842289E35). SAFE-IF for an off-night install, 5 conditions:
  - C1: install with no launcher running and the base hashes matched; copy all three sampler files at once; restage windows afterwards.
  - C2: patch the sys_selftest header.
  - C3: don't compare rows with and without warm-ups, or rows from before and after the install.
  - C4: a smoke run must pass first.
  - C5: the first `warmup_runs > 0` use is the smoke run.
  - frame_summary SAFE.
  - S1: the snapshot defaults ON in every sys_csv row. M8's tests show wall stalls (`sample_ms_max` 351-468 ms vs 5-14 ms) at ~10 ms CPU; fall back to ProcEvery 0 if the idle smoke fails.
  - No process touching. `nongame_load` is INFO only (run-timing L592-598). 7 NIT.
  - All 5 diffs match a fresh `diff --no-index`. Sent.
- 02:14 Overseer: timed windows run ~03:45-06:35. From 03:40 until the Overseer lifts it: read_file/write_file only, no run_command. Nothing queued; idle.
- 02:37 M7 #19 rows package (queue A17F398B, r19_gate 1DD4A89E, check_queue 298BB3EC, ROWS 5BC93446) and the MP tools (README 1ADBAF96) rated: `session3/r19-rows-mp-rating.md` (F8ECBC2EB3A617C7).
  - Package SAFE-IF. Re-ran: selftest 50/50, check_queue 183 PASS, gate d on s4bN16 FAIL+INCOMPLETE as expected. A synthetic no-op log gives exactly 1 incomplete, 0 fails, 0 flags.
  - Q2 confirmed with C1 (exact-JSON no-op rule, plus the ref r19r25 must also show 0 splits).
  - Q3: confirmed for c and f; objected for i and g (S1) -> i16 and g16 substitutes.
  - Q5 confirmed.
  - MP calls confirmed with C4: no LS-info switch, so add `--ls info` or write the rule down. S2: MP2 on native is log equivalence only.
  - Sent.

## 02:43 #19 build method ruling (r19-build-method.md A813D340F52DA743)
- M2's dependency-scoped recompile for devoff4b-r19-bin: ACCEPT-IF. It replaces r19-rating (a) item 2 for this bin.
- Evidence (my own read-only scans, scripts in scratch-r19build/):
  - snap1-sdk .ninja_deps: the 2 headers are included only by the 9 rexgpu-xenos Release objects;
  - game builds: 0 consumers;
  - the DLL exports 4 plugin names, with no static importers;
  - the PCH is independent of both headers;
  - all includes are angle-bracket with the full path.
- Conditions:
  - C1 CTL compare must really PASS against E3CB99CF;
  - C2 overlay -I on all 9 commands;
  - C3 PCH reused unchanged;
  - C4 only the DLL changes (check TracyClient by hand), exports unchanged;
  - C5 needles;
  - C6 the r19-rating conditions stand.
- 3 NITs: priority normal, no Tracy check, tool hashes in MANIFEST.
- Sent to the Overseer at 02:43.

## 03:12 Post-window drafts (session3/postwin-rating.md, sha pending)
- M3's post-window drafts: SAFE-IF. Written with read_file/write_file only, under the quiet rule.
- Hashes are the ones the Overseer gave; I did not recompute them.
- Conditions:
  - P1 re-confirm the live, draft and bin hashes at launch;
  - P2 nothing goes live before the windows end;
  - P3 a 1a/1b pass needs both arms PASS? on the kit's own run dirs, kit exit 0, no_wait x0, and s33_fields exit 0 for 1b;
  - P4 move old check.txt/.s33.txt aside before a re-run;
  - P5 quiet-host caveat on F.
- SHOULD:
  - S1 deps scan of pipeline_cache.h/frame_stats.h before go-postwin;
  - S2 s33base2 manual kit run.
- NITs: N1-N5.
- Sent to the Overseer at 03:12. sha8 to follow once run_command is allowed.

## 06:28 Quiet rule lifted; postwin sha and S1
- postwin-rating.md sha256 3B0C445D8402924D, 9350 B, CR 0, style check clean.
- S1 deps scan PASS (session3/postwin-s1-depscan.md).
  - snap1-sdk: pipeline_cache.h has 8 consumers and frame_stats.h has 5. Their union is 10 rexgpu-xenos objects, the same as the 10 ON objects in the s33 and s33d MANIFESTs.
  - snap1-off and snap1-on: 0 consumers.
- Sent to the Overseer.

## 06:41 Night read-out cross-check (session3/readout-night-xcheck.md 25BF9B1CFDC1C00E)
- READOUT-NIGHT (196D312D): CONFIRMED for C, W10 and W8a; no BLOCKER.
- Own checks:
  - frame re-read of 36 kept WC runs (fps = 1000/mean frame time);
  - proof lines 51/51 OK;
  - GPU plateau from round 2, win3 lowest GPU clock;
  - bins/env/frame source for the 5 passes;
  - script review.
- S1: the median rise comes from C1's bimodal short-frame mode (<1 ms: 1.9 % -> ~20 %, same draw work per frame).
- S2: scope (light route, uncapped, AC, laptop thermal limit).
- S3: win3 supported as timed. P2 neutral; dropping it = untimed config.
- S4: cg26 +121 MHz in 6/6 rounds.
- N1-N5 doc fixes.
- win3 clock difference = effect: at most ~1.2 points of the +7.7 % fps is clock-mediated.
- Sent to the Overseer.

## 06:44 run_gates runexp rating (session3/run_gates-runexp-rating.md)
- M12's `<run>` env expansion in G9 (live 0F7C7B97, installed at 06:35 with the Overseer's go): SAFE.
- Checks:
  - the LF-normalised diff applied to the backup gives exactly 0F7C7B97;
  - logic review: no false-PASS path;
  - selftest 59/59 (my run);
  - re-gate GATES lines are identical except W8a G9 FAIL->PASS.
- NITs:
  - the diff is stored as CRLF;
  - no file-exists check;
  - a moved matrix gives a false FAIL.
- INFO: w6_kit still doesn't expand `<run>`.
- Sent to the Overseer.

## 06:55 r19prep-rating.md (335563D8)

- What: M7's #19 chain prep (queue-r19-live 8A6182A9, LAUNCH-R19 88ED9278, r19_path 9D0BE399, make_live 6C858396, r19_gate CA5C036C, check_queue_r19 EB69D799, test_r19 FAC442EC).
- Verdict: SAFE-IF L1 (from WS; every gate call uses `--bin`) and L2 (re-run check_queue on the installed queue).
  - S1: add the memexport restriction to LAUNCH.
  - N1: path16 should require flags == [].
  - N2: `--bin` doesn't check TracyClient.
  - N3: bin_dir is checked by basename only.
- Q1 go-r19on pre-authorization: YES after ok-a, ok-b and ok-i; no FAIL or FLAG; the marker text names the Overseer; revocable by deleting the marker.
- Ran: test_r19 62/62, check_queue 226 PASS, r19_path bin OK.

## 07:07 final-defaults-rating.md (C20B6FDB)

- What: M2 FINAL defaults set (diff 955543F5, table 14B41251, check-defaults 6C7A00EB, plan B87ABA79, verify-diff 9AAF4BB7, predict-fingerprint 1792CDCB).
- Verdict:
  - diff and code: SAFE;
  - build plan: ACCEPT-IF D1-D7 (CTL legs including native B4, rexruntime extension rated before ON, full-SDK fallback only if the unpatched rebuild reproduces the DLLs, shaders.cpp syntax check, PE import/export checks, no writes to snap1-sdk/install, harness rules first);
  - N-A: confirmed;
  - functional set F1-F7 before the confirmation window.
- Findings: S1 check-defaults should require the full back-off line (stats OFF; GetData hook built). NITs N1-N5.
- Ran: scratch-final/verify_final.py PASS, predict-fingerprint, check-defaults x3, pe_scan, ninja target map.

## 07:09 postcheck-0706-rating.md (702BBC78)

- What: M3 live postcheck.ps1 123FD6D0 vs bak-0706 8B60EBC3 (S33 kit output via %TEMP% plus a copy).
- Verdict: SAFE-IF.
  - Q1: clear $tmp and checks\<row> before use.
  - Q2: copy errors must be visible (ErrorAction Stop, COPY FAILED in $f and $x; copy only on exit 0 or 1).
- Exit code still propagates; this cannot PASS a bad run.

## final-build-rating.md (DF596C16), ~07:25

- **Rated:** M2's D2 build driver (build-final 740E5945, prep-final 83F732CA, pe-check F4368C32, pe-diff FF5C661C, fsyntax E9E4E131) plus the D3 configure delta and the check-defaults S1 fix (D9936C56).
- **Verdict:**
  - D2: SAFE-IF (B1-B3).
  - D3: SAFE-IF (B4-B5).
  - S1: CONFORMS. My run of check-defaults on 0319-win3-r1 in legacy mode gave PASS.
- **Findings:** SHOULD S1, fsyntax per-set TU counts. NITs N1-N5.
- Sent to the Overseer.

## final-build-rating.md post-edit note (94CC9FA7), ~07:32

- **CONFORMS:**
  - build-final 5BE1F221: the freshness gate now checks the output file, and it fails closed. A dry-run never creates that output file.
  - fsyntax 66C7D740: the S1 count gate is in place.
- Both diffs reverse to the rated hashes. Sent to the Overseer.

## day-repin-rating.md (302E29D8), ~07:37

- **(1) install-day re-pin D2D1D11F: SAFE.**
  - The only change is the run-matrix pin 1A522CDF → 72370A1E plus the comment.
  - M11's 430E8049 rating, conditions 1-5, carries over.
  - $Night doesn't need the other 5 files.
  - N1: one stray CRLF.
- **(2) sys_selftest 5C2D2038: SAFE.**
  - Changes: the C2 31-column header, plus the $nCsv capture before the $r/$R collision.
  - No logic change.
  - N2/N3: there is no saved copy of the C9E2CD42 intermediate.
- Sent to the Overseer.

## final-gate-rating.md (AE8EB2A5), ~07:45

- **Rated:** M12 final_gate.py (4C3F0DC1) and the row_gate FINAL C3 skip (E290FD80).
- **Verdict:** SAFE-IF, conditions G1-G4:
  - one launch per run dir;
  - row_gate is never a gate on its own on FINAL bins;
  - the first F1 and F5 PASS outputs get reviewed;
  - a HOLD stops the chain.
- **SHOULD:**
  - S1: automatic N1 HOLD/FAIL by miss count, also for F5w.
  - S2: F2 xenos result → HOLD.
  - S3: no gate row covers runs on the OFF bins.
- **NITs:** N1-N6.
- Sent to the Overseer.

## day-repin-rating.md addendum (42982AFF), ~07:48

- run-timing stop_line fix 9CCE9827: SAFE-IF.
  - One line changed (L503), text only.
  - R1: install only when no launcher or runner is running, then confirm the hash.
- ProcEvery=5: no objection.
- Sent to the Overseer.

- 07:53 final_gate v2 (9DCC72EE, diff C304214C, selftest 35/35): CONFORMS. Section appended to final-gate-rating.md -> 2B9A8464. Sent.
- 07:56 confirm-rating.md (M8 CF1/CF2 drafts: CF1 D36A40CA, CF2 DF8A2D3B, stage-confirm 448D6FAD reproduced): SAFE-IF K1-K5, S1-S2, N1-N3 -> 31AD69BA. Recommended GO: CF1 only=ship,s0,win3 repeats=6 (or ship,s0 x6), CF2 only=nf,mc x6. Sent.

## SESSION3 ~08:05 final-fx-rating.md F256C60D

- Rated final_gate v3 73F946E7 (SAFE) + M3 F1-F7 install draft r2 (SAFE-IF C1-C4, S1-S2, N1-N5). Pin final_gate 73F946E70D586060.
- Checks: v3 diff reproduces 73F946E7; postcheck draft = live 1025D1F6 + diff; marker paths fail closed; check_queue_fx --fg-sha8 73F946E7 read-only exit 0 (135 ok).
- Sent verdict + sha8 to the Overseer.

## SESSION3 ~08:20 G3 F1 OK + s33-rows-rating.md B6EFB444

- final-fx-rating.md: G3 section appended (now B21AD5EA). First F1 PASS = real positive: my check-defaults xenos run PASS, 13 keys (default), single game.log.
- s33-rows-rating.md: M3 #33 rows 2-7 + (d) SAFE-IF C1-C5, S1, N1-N6. Addendum for M3's (a3) fix (s33_sceneids BD344A9D): needs stable > 0 s, ON rows only.
- Sent both to the Overseer.

- 08:30 s33-rows-rating.md addendum: M3's C1-C5/S1 fixes CONFORM (s33_sceneids FA78C672, postcheck 36DC0E05 +81/-0 vs D204503F, READING 976818B4, PLAN 37CF0E82). NIT: quote the neighbour SHOULD line in ON-row readings. File now 9D96775F. Sent.

- 08:41 final-fx-rating.md addendum: first F5/F5w PASS CONFIRMED real (miss-cache ON line x1 on the miss path with env unset; warm reload 10456 B, loaded=1/0/0, 0 new pipelines on fx5w; N6 1=1 is the route's full set). INFO: cache effect not visible in logs (26 = n0 = mc). C3 closed. File now CA6FCFBE. Sent.

- 09:07 r19prep-rating.md addendum: provenance ACK. r19_path 9D0BE399→4629604E = N1 only (`not flags` on path16; pathN branch identical); LAUNCH 88ED9278→2E8287EA = S1 line only (+3/-0). Rated versions rebuilt from my 06:52 read, hash-exact. File now 74933C80. Sent.

- 09:14 r19prep-rating.md addendum: #19 S1 ruling CONCUR with amendment. Readback memexport is ON in every run (harness toml d3d12_readback_memexport=true; readback_memexport default true), so S1 was ill-posed; restated as S1' (read-out: async+readback indirectly covered). Counter is `memexport syncs`, not full-buffer (0 in all f10 lines). Optional r19eL spec given. File now F426CEA0. Sent.

- 09:15 Overseer CONCUR on S1' (F426CEA0). r19eL is on the follow-up list (after the chain and the #33 rows). Open: LAUNCH S1→S1' wording after the chain; r19eL PASS lifts S1'.
- 09:20 r19prep-rating.md addendum: #19 debug-layer validation pair r19vr/r19vg (+ optional r19vw control), SAFE-IF H1-H6 (AeDebug vsjitdebugger, Auto unset; WER path untested). VEHs pass breakpoint through. New sha 4972A927. Sent to the Overseer.
- 09:20 Overseer parked r19vr/vg/vw for this sprint (WER/JIT prompt risk, H2). InfoQueue drain patch = post-sprint item, to be rated separately. ref 4 / row g coverage limit stands.
- 10:32 stopR-rating.md B67F3E2C: STOPR rev 2 (583C40E2 / queue CB502E8C) SAFE-IF R1-R5; install via PAUSE + queue.out.txt confirmation + [IO.File]::Replace (PS 5.1 Move-Item not atomic, queue has EAP Stop); checker r3 9F993FE4 CONFORMS. Sent to the Overseer.
- 12:38 cf2-check.md EFA8501D: CF2 read-out (5C601D91) CONFIRMED; CIs reproduced exactly (boot_check 79E90DB0); C1 plateau same for CF1, C2 tails wording; NITs N1-N5. Sent.
- 13:47 cf1-check.md 5A21C759: CF1 read-out (C8CFD115) CONFIRMED-WITH-CHANGES; CIs reproduced exactly (boot_check1 9DDEAEC8); C1/C2 met; no claim depends on round 3; W1 required (weak-form S1 wording), W2/W3 recommended; C3/C4; NITs N1-N3. Sent.
- 16:09 final2-tools-rating.md 366294FD: prep-final2/fsyntax2/build-final2 diffs (DEBC8312/C6724DBB/1A8F4FB1) CONFORMS; blobs+gitlink+EOL reproduced, B2 PCH reuse SAFE (ninja deps 10 users, pch clean); P1-P3, NITs N1-N3. Sent.
