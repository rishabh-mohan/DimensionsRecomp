# RESUME.md review (#27 item 2): drafts 1 and 2, and the final version

Agent 10, Nov 23. I reviewed draft 1 at 06:50 and folded in my helper's fact-check at 06:59. I delta-checked draft 2 at 07:12 and re-based that check on the announced draft 2 at 07:20. I delta-checked the final version at about 08:22-08:36, and its 08:39 update at 08:41. Read only.

## Update at 08:39 (rfinal3; checked 08:41)

Reviewed: `perf-notes/RESUME.md` 7616A164A8EF7B6F…, 51662 B, 381 lines (LF, no CR, no BOM), written 08:39:07 by Agent 11's `rfinal3.py`. Its gate was 9DA0A4C3… and 381 LF, and its backup `build/agent11/resume/RESUME.0839-9DA0A4C3.md` hashes to the 9DA0A4C3… I reviewed.

**Verdict: F1 is fixed, nothing else changed, and the line count is the same. Public safety: PASS (0 hits). No open findings.**

- My `git diff --no-index -U0` from 9DA0A4C3… has 2 hunks, 2 lines in and 2 out: the same lines, in the same order, as Agent 11's `rfinal3-diff.txt` (8BC40D5975F4C565…).
  - L5: the version note adds "and at 08:39 for Agent 10's review".
  - L325 (F1): the installer refused at 06:36, while the night launcher was waiting for GO, and at 07:33:42, when its process check matched pid 33304, not the launcher, which had ended at 07:30:14 (N-4 in `t27/scrnsave-delta.md`; fails safe, run it again). This matches install-log L15 and L21 and my F1 below.
- `build/agent11/resume/facts-perfopt.md` L112 has the same fix (81AA5DE9644A2C6E…, 08:38:54).
- Still 381 lines, so the line numbers in the "Final version" section below hold for 7616A164… too.

## Final version (08:18; checked about 08:22-08:36)

Reviewed: `perf-notes/RESUME.md` final, sha256 9DA0A4C372399DC4…, 381 lines (LF, no CR, no BOM), written 08:18:09; unchanged at my re-hashes from 08:22 to 08:36. Line numbers in this section are this version's.

**Final verdict: accurate on everything I checked. R33-R38 are all resolved. The day-launcher item is complete: its three conditions (condition 1 closed at 07:56) and N1-N6. Public safety: PASS (0 hits). Findings: 0 BLOCKER, 0 SHOULD, 2 NIT: F1, fixed at 08:39 (see "Update at 08:39" above), and F2, which resolved itself at 08:28:57.**

- **The diff.** My `git diff --no-index -U0` from draft 2 (B12032E61CF0D1E1…) to the final has 41 hunks, 72 lines in and 51 out. Agent 11's `build/agent11/resume/rfinal-total-diff.txt` (C18FBD5CA0F34F9A…) has the same 41 hunks, and its in and out lines equal mine as multisets (0 differences either way). I checked the changed lines against their sources, as listed below.
- **R33-R38, all resolved:**
  - R33 (the re-pin order), §7 step 2, L279: Agent 4's order (`build/agent4/HANDOFF.md` L29-32): first the pack-state keying (`$cacheState` 'pack', `repin_check.ps1` L291), then `$oldBins` (L390), then `$PINS` (L130), and never the `$PINS` line alone (REPIN.md L53). Matches `repin_check.ps1` 81BE81D8….
  - R34 (finding 10 predates the sprint), §6 item 3, L215, citing FINDINGS L142 and L146. "#24's query-poll hook" fits L77 (#24 hooks the fence and query polls) and FINDINGS L146.
  - R35 (the pack's state), §7 step 8, L296-297: the scratch pack passed (Nov 22 07:16, `build/agent4/s35/`), no pack bin is built (Agent 4's HANDOFF L16), the attract's 46 VS + 3 PS objects come first (L24-26), and native4bp needs the shader-preparation step (FINDINGS L147), its own re-pin (REPIN.md §4.2) and its own PSO and seed recording (HANDOFF L27, L31, L33).
  - R36 (the findings line), L9, under Numbering (L7): findings 9, 10 and 11, as FINDINGS L141-147 has them.
  - R37 (the 832 MHz cite), L196: W6.md L222-223 and the audit's §5.5.
  - R38: L272 has "(p = 0.07)" and "load is the likely trigger"; L171 says "median frame time".
- **The day-launcher item** (§6 item 6, L223-232): condition 1 closed at 07:56 with the final hashes; condition 2 is README-DAY (9739BCF8…) L138-141; condition 3, Agent 11's rating, is owed after the break; N1-N6 (N4 and N5 at L231, N6 at L232). Matches `t27/scrnsave-delta.md` §5 and Agent 5's HANDOFF L42-57.
- **The other changes, checked against the sources:**
  - Read-outs final: W9.md rev 1 (8C58CAD1…, 07:45:51) and W5b.md rev 1 (6479A611…, 07:44:43), in `build/agent7/readout/`. Cross-checks: 116 claims, 114 agree, 2 differ by rounding only (`headlines-W6-W4c.md` L5; Agent 7's HANDOFF L33); 912 claims, 880 agree, 32 disagree, 0 sign flips (`build/agent8/readout/w-followup/a7check/W9-W5b-check.md` L23-27; the 2.31 misread at L73).
  - The W5b row (L171) against W5b.md rev 1: d11p −0.20 [−0.23, −0.17], −8.0 % (L114, L172); median frame time +0.5 [−0.9, +1.9] and fps −0.7 [−1.8, +0.3] (L254); d11t −0.22 [−0.25, −0.19], −8.6 % (L114), and fps −1.1 [−2.1, −0.0] (L238); 11 of 12 rounds (L185); TimerQueue busy 23 % to ~2 % (L115, L173); the loaded runs −3.0 against −1.1 %, n = 4, p 0.083 (L212, L308); p99 +0.3 [−0.3, +1.0] against W5's +8.2 % (L44, L228); CPU −8.6 % against d11, W5's −13.7 % against its base (L230, L336); host CPU 69 % (L218).
  - The 0221 run's 6 frames over 16.7 ms: I re-derived T from the run's `perf.csv` (window rows from 24840, as `cluster-0221.txt` L6 gives; its 26.37 ms frame lands within 2 ms of the T 32.886 at L21). They are at T 30.80, 32.88, 32.91, 33.07, 33.20 and 33.29 s, so "between T 30.8 and 33.3 s" holds.
  - §8 (L310-331): the install at 07:33:57 with the three "after" hashes (install-log L30-33); 45/45 at 07:34:45, 16/16 at 07:52 with `-StopAt '2026-11-23 11:00'` and the 14 h rule, 27/27 at 07:47 (Agent 5's HANDOFF L14, L16, L35-37); my 07:56 check; pins.txt is a record only (`run-night.ps1` 565D30D4… L967, L973; Agent 5's HANDOFF L25-32; Agent 8's HANDOFF L13); the launcher's exit at 07:30:14 (SESSION2 L3339).
  - #19 (§7 step 3, L282-283), against RATE-REQUEST 5824C87C7BE68A02…: §16's verdicts (a)-(c); `<N>` after Agent 3's ready-N gate (§10; `build/agent3/s4b/ready-N` was absent at 08:10); the clang check, then my rating, then Agent 2's build at ≤ 2 threads; the `--directory` form (L61-63). L283's "a repository outside the workspace" is right: L64-67 say git uses the parent repo two levels above the workspace.
  - #33 (§6 item 10, L248-257) and F-CA (§6 item 8, L236) match `t27/r33-popin.md` and `t27/r21-s4t1.md`. Agent 7's HANDOFF L73-75 (the earlier th2 runs) and L112 (q750 and q1000, cited at L204); Agent 8's HANDOFF open item 1 (L75, cited at L276) and open item 4 (L86-93, cited at L271).
  - §7 step 0 (L261-272) includes the window hygiene, so L298's reference to it holds.
  - Re-pin step 5: I found no announcement in SESSION2.md (last written 07:56) or Agent 1's HANDOFF (8535FD76…). L265, L275 and L279 say it's left, which is right.
- **Findings:**
  - **F1 (NIT), L325:** "The installer refused at 06:36 and at 07:33:41, while a launcher process was still running". That is true at 06:36: the night launcher (pid 19960) was waiting for GO, and all four launcher checks refused (install-log L3, L9-12). At 07:33 the launcher had ended (07:30:14, L15), and there was no mutex refusal like L9. Only the process check fired, at 07:33:42, on pid 33304, which isn't the launcher's pid (L21). That check matches any PowerShell whose command line names run-night.ps1 or run-day.ps1 (N-4 in `t27/scrnsave-delta.md`). So it was a fail-safe false alarm, and the re-run at 07:33:56 installed. Suggested: "...refused at 06:36 (the night launcher was still waiting for GO) and at 07:33:42 (its process check matched pid 33304, not the launcher, which had ended at 07:30:14: N-4, fail-safe, just run it again)". `build/agent11/resume/facts-perfopt.md` L112 has the same words. Both were fixed at 08:39 (see "Update at 08:39" above).
  - **F2 (NIT, resolved), L266:** "Agent 11's is short and points here". At my 08:25 check `build/agent11/HANDOFF.md` didn't exist. It was written at 08:28:57 (C508AD884B177B80…, 54 lines), and its L3 points to RESUME, so L266 now holds. Nothing to do.
- **Info: two other HANDOFFs were behind; their owners fixed them at 08:38-08:39** (their files, not RESUME's):
  - Agent 5's (8315ACF4EE3E37A7…, 07:53:22) L16 and L44-46 said my check of the regenerated day draft was pending. It was done at 07:56: condition 1 is closed. Fixed at 08:39:10 (488D14CA60F4F4F7…): L16 and L44-46 now say condition 1 closed at 07:56.
  - Agent 5's L81-83 listed facts-perfopt.md L110 among the places that quote the old run-matrix.ps1 hash FEDCEB13, and Agent 8's (B38513BC1C6DF667…, 07:56:31) L74 called L110 stale. Since 08:15 (F0C8824646623323…), L110 gives FEDCEB13 only as the pins.txt record, and 1A522CDF since the install. Fixed: Agent 5's L81-83 (08:39:10) and Agent 8's L74 (87F2675C340CECE1…, 08:38:09) now say L110 was updated at 08:15.
- **Public safety: PASS.** 0 hits in the final for the user name, user paths, URLs, e-mail addresses, account and machine names, secrets and file URLs.

## Draft 2 delta (07:12, re-based 07:20)

Reviewed: `perf-notes/RESUME.md` draft 2 as announced, sha256 B12032E61CF0D1E1…, 360 lines, written 07:10:07. Line numbers in this section are this version's. My 07:12 pass read a copy taken mid-edit (BA95FA199D8A3641…, 355 lines, 07:03:09). I diffed the two (21 hunks, 28 lines in and 23 out) and re-checked every changed line. When the final version lands (by ~12:00), it gets the same delta check.

**Draft 2 verdict: accurate on everything I checked. 3 SHOULD items remain (R33-R35), plus NITs (R36-R38). Public safety: PASS (0 hits for the user name, user paths, URLs, e-mail addresses, account and machine names, and secrets). The day-launcher item is there, with its three conditions and N1-N6 (§6 item 6, L219-228).**

- **Resolved:** R1-R24 and R27-R32 (R25 and R26 aren't used).
  - R18: L5 now gives 07:10, the write time.
  - R27: L252 now says that at 07:10 the HANDOFFs of agents 7, 8 and 11 weren't written yet. At 07:15 they still weren't; I re-check at the final version.
  - All 3 wrong facts of draft 1 stay fixed: COMMIT-CHECK (L57), p2fc lower in 9 of 10 rounds with C1 10 of 10 (L165), and W8a as n0 vs mc (L270).
  - Sources I re-checked for the draft 2 figures:
    - W9, Agent 7's read-out (`build/agent7/readout/W9.md` D2B696F9F182FA58…, 07:01:54):
      - q500: −0.75 core [−0.86, −0.64], −30 %;
      - without the 7 flagged runs: −0.79 [−0.84, −0.73], p99 −0.8 % and 1 % low +2.2 % (L35);
      - q125 and q250: −0.72 each (L259, L285);
      - drop q0 (L37);
      - every arm has at least 3 timed runs (L52).
    - W6 (L7, L12, L21, L93, L108, L154, L222-226) and W4c (L7, L8, L49, L118).
    - Agent 12's gates (`build/agent12/w6-gates/NIGHT-RESULTS.md` CB922F33F378FA35…):
      - the waiver (L21, L67);
      - the 3 flagged runs (L44, L49);
      - G10 (L52-53);
      - the G11 overlay (L73-76);
      - W4b and W5 on best_efficiency is from FINDINGS L21.
    - The launcher and day items:
      - `install-log.txt` L1 (day-update refused at 06:36) and L9-10;
      - `day-update.ps1` L59-61;
      - `launcher-ctl.ps1` L79-81;
      - README-DAY L134;
      - `run-matrix.ps1` L14-19, L39 and L332-334;
      - Agent 9's pre-read L168.
    - git (read-only rev-parse and show):
      - `perf/opt` = `mine/perf/opt` in both repos (b0bd3b4 and 5350b1d);
      - `b0bd3b4` touches the 3 named files plus the SDK pointer, and `5350b1d` touches 13 files;
      - `main` = `origin/main` = 895a529, and `toypad-ui` = 516e631.
    - #21 (L109, L234-243) matches `t27/r21-s4t1.md` L8, L51-52, L63 and L76. F-CA (L230-233) matches `t27/sub-r21-coderead.md` L203-211.
- **New in this version, checked against the sources:**
  - Agent 7's pooled W5b numbers (L23, L167), against `build/agent7/readout/pool-W5b.md` (53C6388B32FA63EC…, 07:02:13):
    - 36 of 38 runs kept (L7);
    - d11p: −0.20 core [−0.23, −0.17], −8.0 % (L54); median frame time +0.5 % [−0.9, +1.9] and fps −0.7 % [−1.8, +0.3] (L33, L35); p99 +0.0 % and 1 % low −0.2 %, both CIs across 0 (L42, L44);
    - d11t: −0.22 core [−0.25, −0.19] (L54) and fps −1.1 % [−2.1, −0.0] (L35);
    - TimerQueue busy: 23.17 % for d11, 1.97 % for d11t and 2.08 % for d11p (L57).
  - The long frames (L167), against `build/agent7/readout/tail-check.md` (D59358F3B74998DC…, 06:54:54) L23, L52-54 and L60-80: d11p had 6 frames over 8 ms (d11: 2) and none over 16.7 ms. d11t's 6 frames over 16.7 ms are all in run 0221-d11t-r5, between T 30.8 s and 33.3 s.
  - The fresh clone, the plume steps, the export and the kit re-pin (L13, L118, L125-128, L137, L327), against `build/agent1/HANDOFF.md` (8535FD76FB7371B9…) L7-8, L31, L38, L42-70 and L88-97 (the 07:02 export run: 4529 files, 0 leftovers; nothing pushed).
  - The no-builds rule (L257), against Agent 1's HANDOFF L108-109 and RESUME L212.
  - #19 (L108, L267-268), against `build/agent7/s4-r1s2/README.md` L1, L10 and L13. I counted `s4-r1s2.diff`: 5 files, 320 lines in, 1 out.
  - #33 (L110, L276-277), against `build/agent6/HANDOFF.md` (79763902482E05FB…) L87-107. I counted `s33-popin.patch` (0D23024484CCDEE1…): 4 files, 105 lines in, 24 out.
  - PENDING-DIFFS (L111): its status column is dated 06:30 (L30), and it still lists #33 as design only, under the placeholder name (L39, L65).
  - The new paths exist: `harness/` (L116), `build/agent3/s4b/logs/rpm4.3b.txt` (L264), and `build/agent3/f10/RESULTS.md` and `f10-table.md` (L348).
- **Still open:**
  - **R33 (FIX, SHOULD), L264: the re-pin order.** The text is unchanged; the new rpm4.3b cite is fine.
    - It says "Then come the `$PINS` line and the pack-state keying (REPIN.md L53; Agent 4's HANDOFF, open item 3)".
    - Agent 4's HANDOFF (38CD991AB98EE32E…) L29-32 says to fix `repin_check.ps1` before the next re-pin, in this order:
      1. key check [4]'s old-pin FAIL on the pack state;
      2. add `build/agent2/native4b-bin` to `$oldBins`;
      3. only then add native4b to `$PINS`.
    - Adding the `$PINS` line alone, as REPIN.md L53 says, makes every check of `snap1-on` and `native4b-bin` FAIL, including REPIN section 4.2 step 1 (L30).
    - Suggested: "Then fix `repin_check.ps1` in Agent 4's order (HANDOFF L29-32): the pack-state keying, then `$oldBins`, then the `$PINS` line. Never add the `$PINS` line alone."
  - **R34 (ADD, SHOULD), §6 item 3 (L211-215).** Say that finding 10 predates the sprint. L212 now names load as the likely trigger, but the item still doesn't say the lock is older than S4.
    - v0.2.0 hit the same stuck lock (the same lock, owner and waiting thread), then recovered and finished (FINDINGS L142, L146).
    - L146 also notes that v0.2.0's lock owner polled a GPU query result back to back. #24's query-poll hook (L73) is S4's answer to that loop.
  - **R35 (ADD, SHOULD), §7 step 8 (L278-280): item #1's pack state.**
    - Agent 4's scratch pack passed (Nov 22, 07:16; `build/agent4/s35/`), but no pack bin is built (`build/agent4/HANDOFF.md` L16).
    - The build must also re-run one shader-preparation step (FINDINGS L147).
    - The pack changes the native fingerprint again, so a pack bin needs its own re-pin and its own PSO/seed recording (HANDOFF L31, L33).
  - **R36 (ADD, NIT).** FINDINGS speaks of findings 9, 10 and 11, but RESUME uses only item numbers. Name each finding once:
    - finding 9: the missing native shaders (#1, with #2 as the stopgap);
    - finding 10: the stuck lock (§6 item 3);
    - finding 11: the write-tracking gap that predates the sprint (upstream and v0.2.0). Its first fix is #5 fix (i), which C1 needs (FINDINGS L141; L86).
  - **R37 (FIX, NIT), L192.** "(Agent 8's audit, §5.5)" names no file. Cite W6.md L222-223 (or W4c.md L118). They give the 832 MHz steady clock and point to the audit's §5.5.
  - **R38 (FIX, NIT), new in this version.**
    - L257 says "Finding 10's stall is host-side" next to 0 of 4 against 4 of 6, with no p value. Add "(p = 0.07)", as L212 has; L212 also says load is the likely trigger, not proven. The rule itself is right.
    - L167 "median +0.5 %" is the median frame time (pool-W5b.md L33). Say "median frame time", so it doesn't read as fps next to "fps −0.7 %".

## Draft 1 review (06:50, with the helper's fact-check at 06:59)

Reviewed: `perf-notes/RESUME.md` draft 1, sha256 8BE0AB49EBF1AB52…, 299 lines, written 06:23:49. Line numbers from here on are draft 1's.

**Interim verdict on draft 1: mostly accurate, but 3 facts are wrong, and it needs updates before the break.**
- **Accuracy.**
  - My helper checked §0-§7, §9 and §10 claim by claim (`build/agent10/t27/sub-resume-facts.md`, 43F660F9A854F3F5…, 285 lines).
  - It found 3 wrong facts. I checked all 3 against their sources (R20-R22).
  - Many items are out of date because the work finished after 06:23 (R1, R6, R8, R10, R11, R13, R23, R24).
  - A few are inexact (R3, R5, R7, R18, R28), and two claims have no source (R29).
- **Restart in a week.** The day-launcher item is there (§6 item 6, L194-199). Missing:
  - the three day conditions as a checklist (R2);
  - F-CA (R9);
  - the CG26 kit (R12);
  - the cache rule in step 0 (R15);
  - the desktop/AC rule (R16);
  - the formal read-out figures (R23);
  - Agent 6's two NOTEs (R24);
  - Agent 9's notes (R31);
  - some §10 paths (R30);
  - the git steps for a fresh clone (R32).
- **Public safety: PASS.** My scan and my helper's separate scan both found 0 hits. They looked for the user name, user paths, e-mail addresses, URLs, account names, token or key strings, machine names and IP addresses. R17 has optional wording changes. The export SHOULD (R19) is handled by Agent 1's script.

Kinds:
- UPDATE: true at 06:23 but out of date now.
- FIX: inexact or wrong.
- ADD: missing.

## 1. Day launcher (§6 item 6, L194-199)

Present: the rating, the regeneration step, Agent 11's rating, the install rule, and N1 and N6.

- **R1 (UPDATE, SHOULD), L196.** Condition 1 is met in staged form.
  - `build/agent5/scrnsave-fix/new/day/run-day.ps1` (B67EBD6C…) is generated from run-night.ps1 565D30D4…, which `new/make-run-day.ps1` (4A96B0B9…) pins. My delta-read is SAFE (`build/agent10/t27/scrnsave-delta.md` §4).
  - It closes after the SCRNSAVE install, once three things are done:
    - `build/agent5/scrnsave-fix/day-update.ps1` has copied the files into `build/agent5/day-draft/` and regenerated run-day.ps1 there;
    - `test-day.ps1 -Name all` has passed;
    - I have checked the final hashes.
  - day-update.ps1 refuses until the installed run-night.ps1 is 565D30D4…. It refused at 06:36:00 (`install-log.txt`).
- **R2 (ADD, SHOULD), L194-199.** List the three conditions from `build/agent10/t27/day-draft-rating.md` L6-8 as a numbered checklist:
  1. run-day.ps1 regenerated from the SCRNSAVE-fixed run-night.ps1, test-day.ps1 re-run, and Agent 10's delta-read (R1);
  2. installed into `bench/agent5/day/` only after the night launcher has exited, then the hashes compared;
  3. Agent 11's rating.

  Conditions 2 and 3 wait until after the break (Agent 1, 06:05). No day session runs before all three hold.
- **R3 (FIX, NIT), L198.** "README-DAY L136-139" is right for today's README-DAY.md (9D131EB1…). In the SCRNSAVE-fixed one (A36574ED…) the install section is at L138-141. Cite the section name, or both line ranges.
- **R4 (UPDATE, SHOULD), L199.**
  - N1 is fixed in the generator, and day-update.ps1 L59-61 refuses unless the run-day.diff headers are exactly repo-relative. But `build/agent5/day-draft/run-day.diff` (54E35C18…) keeps the absolute paths with the user name until day-update.ps1 has run. Don't publish `day-draft/` before then.
  - N2 and N3 are fixed in the staged README-DAY.md (A36574ED…) and RUN-DAY.cmd (B08645E9…).
  - N4 (DST-naive time, launcher-ctl.ps1 L79-81) and N5 (README-DAY L134) are harmless.
  - N6 stays open.

## 2. Launchers and the SCRNSAVE fix (§8; §6 item 7; §7 steps 0-1)

Checked, OK:
- L243: RUN-NIGHT.cmd D7A0362B…, run-night.ps1 16B90FA8… and README.md 0058C8F6… are the live hashes (06:38).
- L244: my SAFE is b2r row 41 (~22:33). The freeze at 23:24:43 is Agent 1's.
- L246: `bench/agent5/launch/status/pins.txt` lists 19 files after its header line (pinned 23:47:20 by pid 19960):
  - RUN-NIGHT.cmd and run-night.ps1;
  - 15 files in `bench/agent8/run/`, including `drivers/`;
  - `harness/legodimensions.toml` and `harness/nvml.cs`.
- L248-251:
  - the GO refusal at 00:03:40 (SESSION2 L3215) and the hand fix at 00:05:37 (L3218);
  - Set-ScreensaverNone is run-night.ps1 L461-467, with the delete at L465;
  - run-matrix.ps1 L417 is the plain read.
- L253-255: what the fix changes (`scrnsave-delta.md` §2).
- L257: two pinned files change (run-night.ps1 and run-matrix.ps1; README.md isn't pinned). The launcher pins again at each start (`build/agent5/scrnsave-fix/README.md` L53-55).

Changes:
- **R5 (FIX, NIT), L252.** It says "Agent 5's patch ran at 06:11", but the `new/` files were written at 06:14:32-35 and `hashes.txt` at 06:14:38. Say "staged at 06:14".
- **R6 (UPDATE, SHOULD), L256; also L200, L207 and L212.** "Tests and the reviews by Agents 8 and 10 are pending" is out of date.
  - Tests: `test-scrnsave.ps1 -Set new -E2E` passed 45/45 at 06:14:40 (`results/summary-new-061440.txt`).
  - Agent 10: the fix was rated SAFE at 06:30, and the install tooling SAFE at 06:45 (`build/agent10/t27/scrnsave-delta.md`).
  - `install-scrnsave.ps1 -Check` at 06:36 refused on all four launcher checks because the night launcher was running. That is the designed behaviour, and it copied nothing (`install-log.txt`).
  - Still pending:
    - Agent 8's read;
    - the install after 07:30;
    - the post-install tests (`test-scrnsave.ps1 -Set installed -E2E` and `build/agent5/launch-test/run-tests.ps1 -Group go`);
    - day-update.ps1 and `test-day.ps1 -Name all`.
  - After the install, L243 needs the new hashes:

    | file | new hash |
    |---|---|
    | run-night.ps1 | 565D30D4… |
    | README.md | B7CEBD63… |
    | RUN-NIGHT.cmd | D7A0362B… (unchanged) |
    | run-matrix.ps1 | 1A522CDF… (was FEDCEB13…) |
- **R7 (FIX, NIT), L255.** "This covers Agent 10's condition 1 and N1-N3" is true for the staged files. For `build/agent5/day-draft/` it becomes true only after day-update.ps1 has run (R1, R4).

## 3. Other items

- **R8 (UPDATE + FIX, SHOULD), L106 and L221-222.** #21 is rated (`build/agent10/t27/r21-s4t1.md`):
  - (a) the default-off test bed is SAFE;
  - (b) value 3 in F1, F3, W1 and W8b is SAFE-IF 5 conditions;
  - (c) the MP4 restatement is ACCEPTED, with one wording fix and one addition.

  It is staged as S4-T1 in `build/agent7/s4-t1/`. The env takes 1-3 (1 = priority, 2 = EcoQoS opt-out, 3 = both; unset = no call), and the proposed rows use 3. So "`LEGO_NATIVE_CHAIN_PRIORITY=1`" should read "=3", or "1-3; the rows use 3". In L222, "isn't rated. It needs Agent 10's rating, ..." becomes "is rated; it still needs a build, the threaded-mode proofs and the functional rows".
- **R9 (ADD, SHOULD), §6.** F-CA is a deadlock path in the color-alias retire handoff, in threaded mode th2 only.
  - It predates #21 and was not seen at runtime.
  - #21's condition 5: a th2 hang in any #21 row is checked against F-CA first.
  - Owner: Agent 7. Agent 7 records it under MP4 gap 2 and says whether any earlier th2 run hung (`build/agent10/t27/r21-s4t1.md`, (b) item 5 and the SHOULD; `sub-r21-coderead.md` §6).
  - SESSION2 L3326 says F-CA goes into RESUME's open items.
- **R10 (UPDATE, SHOULD), L188-190.**
  - "Or Agent 12 explains row 7's F 92" is out of date, because Agent 12 has explained it.
    - Without P2, verify's F check races MakeRangeValid's re-hash. C1 without P2 is unverified, not failed.
    - It clears by either:
      - (a) s4bV0, where Agent 12 predicts F > 0; or
      - (b) a verify-only fix that clears `keep_watch_verify_hashes_[page]` inside the valid-bit scope, then a re-run of row 7 that expects F 0.
    - Until then C1 ships only as p2fc (`perf-notes/agent10-batch2-review.md` §41, L2473-2476).
  - For s4bLV, add "quiet host" and "K 0 / F 0 over the whole run" (the rule at SESSION2 L3128-3132).
  - Add: don't turn the verify cvar off at runtime. It gives false F as well as false K (b2r §41, L2470 and L2483).
- **R11 (UPDATE, SHOULD), L191 and L211.** All 4 finding-10 rows passed: f10a, f10b, f10a2 and f10b2 (`build/agent10/t27/f10-rating.md`).
  - Each had 0 STUCK-LOCK events and reached the level with 3/3 tags.
  - Each showed exit 0, no dumps and no WER, with K 0 / F 0 on a quiet host.
  - As planned (SESSION2 L3123), finding 10 stays a load-only WARN.
  - The margin is small: the worst quiet frame was 2.89 s against the 5 s detector, versus 3.99 s in w6s3 under a build (`build/agent3/f10/f10-table.md` L5, L11).
  - In RESUME, name the rating rule (SESSION2 L3128-3132) and keep s4bLV open.
- **R12 (ADD, SHOULD), L216 and L224.** Agent 9's CG26 check kit: `build/agent9/cg26-check/README.md`, with the one-liner at L12.
  - Checker: `cg26_check.py` DDBA731CC22D74BD….
  - Exit codes: 0 PASS, 1 FAIL, 2 INCOMPLETE, 3 HELD.
  - Don't use the `cmd /c start` form sent at 22:43, because it always exits 0.
  - Order:
    1. Agent 2 regenerates, relinks and stages CG26 (`build/agent2/devoff4b-cg26-bin`, not staged yet; partial work in `build/agent2/cg26/`);
    2. the kit passes;
    3. Agent 10 rates #26;
    4. W10 runs.
- **R13 (UPDATE, NIT), L215.** Re-pin step 4 has passed. Agent 3's boot check rpb0 (1 run, `build/agent4/repin/REPIN.md` L67) and matrix rpm4 (4 runs, L78) both passed (`build/agent4/HANDOFF.md` L18; SESSION2 L3325).
  - The runs are `build/agent3/runs/rpb0-20261123-0617` and `rpm4-20261123-0620`.
  - Only step 5, Agent 1's announcement, is left. After it, Agent 4 adds the `$PINS` line (REPIN.md L53).
  - L215 calls both runs "the 4-run rpb0/rpm4 matrix".
  - The re-pin also closes gate 4 of b2r row 40.
- **R14 (ADD, NIT), near L7-12.** Two numbering schemes collide.
  - Grid task numbers (#25-#27) and S4 item numbers (#19, #21, #26, #33) both use `#`.
  - README-DAY.md L136 and `build/agent5/scrnsave-fix/README.md` L1 call the SCRNSAVE fix "task #26", while RESUME's #26 is the codegen pause.
  - One line fixes it: "#N is an S4 item (S4-DRAFT); grid tasks are written 'task #N'."
- **R18 (FIX, NIT), L5.** It says "draft 1 (Nov 23, 06:40)", but the file was written at 06:23:49.

## 4. Fact-check results (my helper; I re-checked the WRONG items)

- **R20 (FIX, SHOULD), L54.** COMMIT-CHECK is now a clean PASS, not "PASS, with 1 WARN about moltenvk".
  - `build/agent2/COMMIT-CHECK.md` (0FAB9726B9B7F2E6…, 06:15) says "RESULT: PASS (main check). Extended checks: PASS." (L18) and "RESULT: PASS; EXTENDED: PASS" (L125).
  - moltenvk is "PASS (note)" (L95). The snap1 copy didn't keep its 10 symlink entries, and no regular file differs (L114).
  - The WARN was in the 05:57 version, which the fact sheet (L37) still quotes.
- **R21 (FIX, SHOULD), L157.** "Faster in 10 of 10 rounds" is wrong for p2fc against s0.
  - By median frame time, p2fc was lower in **9 of 10** rounds (sign test p 0.021; `build/agent8/readout/w-followup/W6.md` 5A7015ECEC4B3B0F… L7, L82).
  - The 10 of 10 belongs to C1 = p2fc − p2f (L12, L86).
  - FINDINGS L14 now words this correctly (9AF761BEDB57191A…, written 06:55), so only RESUME still has the error. My helper read FINDINGS before that update.
- **R22 (FIX, SHOULD), L220.** W8a's arms don't match the staged matrix.
  - RESUME follows the plan row (S4-DRAFT L404: native3d against native4b with #2 on).
  - The staged W8a is **n0 (miss cache off) against mc (`LEGO_NATIVE_SHADER_MISS_CACHE=1`), both on native4b-bin** (`build/agent8/w-followup/matrix-window8a.json` A06E5E3AAEE25B07… L2, L29, L33).
  - Its GO line is `only=n0,mc repeats=6`: 13 runs, 27.4 min, runner 30, not ~33 min (`build/agent8/w-followup/PROPOSAL.md` L78).
  - W8a4 is the same comparison on native4 (n4 against n4mc, L79).
  - The W8a matrices are in `build/agent8/w-followup/`. §10 (L291) only points to `bench/agent8/run/` for matrices.
- **R23 (UPDATE, SHOULD), L5, L17-18, L157, L160-162 and L211.** Agent 8's formal read-outs for W6 (`build/agent8/readout/w-followup/W6.md`, 06:39) and W4c (`W4c.md` 965F323E151D508A…, 06:40) are in. W9 and W5b are not in yet.
  - **W6, p2fc against s0** (10 paired rounds, both passes):
    - median frame time **−10.3 % [−13.6, −6.9]**;
    - fps **+18.0 % [+14.1, +22.0]**;
    - CPU **−0.249 cores [−0.303, −0.195]** (W6.md L7, L82);
    - C1 alone: −10.7 % [−13.1, −8.3] (L12, L86).
  - The runner's −14 % / +22 % / −0.27 core in L18 and L157 are pass-2 figures (W6.md L10). The pooled raw ratios are −12.8 % and +21.8 % (L82).
  - W6's guard (a) warns on the light share (L108). The gain is in the light frames (97-98 % of all frames). The heavy frames get slower: median +2.9 % [+2.3, +3.5].
  - **W4c, B against d0** (6 rounds):
    - median **+2.6 % [−1.2, +6.5]**, lower in 1 of 6 rounds;
    - fps **−1.7 % [−4.9, +1.7]**;
    - CPU **+0.063 cores [−0.007, +0.133]** (W4c.md L7, L49).
  - W4b's +6.4 % fps hint did not repeat (L8). L160's +1.3 % / −0.4 % are the runner's raw figures.
- **R24 (UPDATE, SHOULD), L185-186 and L211.** Agent 6's night logdiffs are done (`build/agent6/wnight/RESULTS.md` BBDA370F2539E3DD…, 06:03).
  - 135 runs in 7 dirs, no FAIL (L7).
  - Only the switch proof lines differ by arm.
  - 0 STUCK-LOCK and 0 dumps (L13).
  - So q500 and d11p need no further logdiff confirmation.
  - Two NOTEs for a restart:
    - 6 runs miss `Execution complete`, a benign race in the hard-exit path (L9);
    - W9 `0128-off-r2` hit the 3 s shutdown watchdog, a first sighting (L10).
- (R25 and R26 are not used.)
- **R27 (NOTE, SHOULD), L11, L209 and L299.** RESUME points to `build/agent<N>/HANDOFF.md`. At 06:57 these existed for agents 2, 4, 5, 6, 9, 10 and 12, and not yet for agents 1, 3, 7, 8 and 11. Re-check before the pause.
- **R28 (FIX, NIT), smaller items.**
  - (a) W4b also ran d11t on devoff2 (`bench/agent8/run/matrix-window4.json` L37, L42). L88-89 ("W5 and W5b") and L139 ("W4b and W4c d0") leave it out.
  - (b) L93-94 and L216 are right that CTR and CG26 aren't built. But partial work exists in `build/agent2/ctr/` and `build/agent2/cg26/`.
  - (c) L155's W4b B fps "+6.0 %" is right as attributed (S4-DRAFT L409). The runner summary and W4c.md L8 give +6.4 %.
  - (d) L87 cites caveats (a)-(f), but S4-DRAFT row 38 (L259) has (a)-(d) and (f), with no (e).
  - (e) L220's "~33 min" for W8a: PROPOSAL.md L78 says 27.4 min (R22).
- **R29 (FIX, NIT), no source found.** Either cite a source or mark these as proposals:
  - L231, "against s0, two passes": FINDINGS L30 says only "a confirmation window", and the older plan (SESSION2 L2943) says against S3d.
  - L270, "at least 3 rounds".
  - My helper also flagged L73's "landing off". That one is backed by b2r row 39: verdict "PASS: SAFE to build", default column OFF.

## 5. Restart in a week: gaps

- **R15 (ADD, SHOULD), §7 step 0.** The cache rule is only in §9 item 3 (L273): re-record the PSO/seed caches, and a seed must match its bin.
  - Put it in step 0 too, with "never copy caches between bins", and point to how cold runs work.
  - Cold runs (`bench/agent8/run/run-matrix.ps1` L14-19, L39 and L332-334):
    - by default, one cold run per bin;
    - with -ColdShared, one shared cold run, and the other bins' first launch is a scored round-1 run;
    - with -NoCold, no cold run.
  - Agent 9's #21 pre-read (P2, `build/agent9/s4-t1-preread.md`) shows the trap: under -NoCold, n0 r1 and th3old r1 start cold while th3 r1 starts warm.
- **R16 (ADD, SHOULD), §7 step 0 or §9 item 5.** Timing counts only under all of these (`bench/agent5/launch/README.md` L7, L16, L157 and L192-194):
  - the user's own desktop (`WinSta0\Default`);
  - not locked;
  - on AC power;
  - nobody at the PC.

  RESUME doesn't say this.
- **Step 0 (L207):** after "the SCRNSAVE fix installed and reviewed", add "its post-install tests passed, and day-update.ps1 has run" (R6).
- **R30 (ADD, SHOULD), §10 (L286-299).** Paths a restart needs that §10 lacks:
  - `build/agent6/wnight/RESULTS.md` (R24);
  - `build/agent8/readout/w-followup/`, the formal read-outs (R23);
  - `build/agent8/w-followup/`, the W8a and W8a4 matrices (R22);
  - `build/agent9/BACKOFF-DEFAULT-ON.md` and `build/agent9/HANDOFF.md` (R31);
  - `build/agent7/s4-t1/` and `build/agent10/t27/r21-s4t1.md` (R8, R9);
  - `build/agent2/ctr/` and `build/agent2/cg26/` (R28 b), and `build/agent9/cg26-check/` (R12);
  - `build/agent4/screenshot-kit/README.md`, since the kit is ready (`build/agent4/HANDOFF.md` L19);
  - `build/agent3/runs/` (the f10, rpb0 and rpm4 runs) and `build/agent3/f10/f10-table.md` (R11, R13).
- **R31 (ADD, SHOULD), L158 and §7 step 11 (L232-239).** Agent 9's notes (`build/agent9/HANDOFF.md`, 3F27B281EBD539D0…):
  - `build/agent9/BACKOFF-DEFAULT-ON.md` holds the design for making the back-off a default. Step 11 needs it, because the back-off is env-only today.
  - W9 pass 2 had 4 "lowclk" runs: q125 r1, q250 r1, q500 r2 and q125 r3 (HANDOFF L157 onwards).
    - They are read as host-driven but not proven (SESSION2 L3323).
    - They explain L158's "unsteady".
    - They aren't the slow-state rule, so L178 stands.
  - Still owed: one untimed Q = 500 run with stats that shows `sleep_fail == 0`. sleep_fail at Q = 500 has never been observed (HANDOFF L152-153).
- **R32 (ADD, NIT), §2/§3.**
  - Git on a fresh clone:
    - how to restore the `mine` remote (`git remote -v` in both repos; keep the account name out of public notes);
    - SESSION2 L3300 plans a second commit at the end of the grace period. If that happens, §2's `b0bd3b4`/`5350b1d` move on.
  - Agent 4's parked threaded-modes plan for W8b (`build/agent4/HANDOFF.md` L20; `bench/agent4/matrix-native-threaded.json`).
- **Also needed:** the finding-10 rule (R11) and the CG26 kit (R12).
- My helper's own gap list is its §4. All of it is covered above (R9, R11, R13, R23, R24, R27, R28 b, R30-R32).

## 6. Public safety

- **Draft 1: PASS.** Notes:
  - "C:" in L280 is a drive letter only.
  - The hardware models (L263-264) are fine.
  - `HKCU\Control Panel\Desktop` (L249) is a generic registry path.
  - The remote is only ever called `mine` (L16, L42).
  - My helper's scan (its §3) agrees, with 0 hits.
- **R17 (optional, NIT).**
  - L174 and L284 name a Defender exclusion for `build/`, which is a local security setting. That is fine in a private note. In a public copy, write "an antivirus exclusion for the build folder" or leave it out.
  - L3 "from ~13:00" is the user's schedule. Drop the hour in a public copy. Two milder mentions: L228 "a one-hour slot at the visible desktop" and L245 "double-clicks it and leaves the PC".
- **R19 (ADD, SHOULD), L112-114.** Many local files contain absolute paths with the user name, for example `build/agent3/s4b/logs/*.holdwatch.out.txt` and `build/agent5/day-draft/run-day.diff` (until R4). Say that any export of `build/` or `bench/` (Agent 1's `build/agent1/perf-export/`) needs a scrub for absolute paths first.
  - *Status 06:51:* Agent 1 has handled the export side. `build/agent1/export/export_perf.py` (A2BD03954190AC86, 216 lines) maps the workspace path to `<workspace>`, and other profile paths and the account name to `<user>`, in plain, JSON-escaped and file:/// forms. It also counts leftovers. The full run is after 07:30.
  - RESUME only needs one line saying that exports go through this script.

## Read / sent

- **Read:**
  - RESUME.md draft 1 in full;
  - SESSION2.md L3106-3132, L3215, L3218 and L3295-3328;
  - b2r §41 (L2466-2485) and row 39;
  - `bench/agent5/launch/status/pins.txt`;
  - `bench/agent5/launch/README.md` L1-16, L157 and L192-194;
  - run-night.ps1 (16B90FA8…) L446-481 and L1012;
  - run-matrix.ps1 L1-40 and L277-334 (the cold-run options);
  - the SCRNSAVE package, including `install-scrnsave.ps1`, `day-update.ps1` and `install-log.txt`;
  - the four f10 check files and `build/agent3/f10/f10-table.md`;
  - the CG26 checker's hash;
  - my helper's `sub-resume-facts.md` (43F660F9A854F3F5…).
- **Spot-checks of my helper's sources:**
  - `build/agent2/COMMIT-CHECK.md` L18, L95, L114, L125;
  - W6.md L7, L10, L12, L82, L86, L108;
  - W4c.md L7, L8, L49;
  - `matrix-window8a.json` L2, L29, L33;
  - PROPOSAL.md L78-79;
  - RESULTS.md L7, L9, L10, L13;
  - `build/agent4/HANDOFF.md` L18-20;
  - `build/agent9/HANDOFF.md` L152-157;
  - REPIN.md L53, L55, L67, L78;
  - FINDINGS L14;
  - the HANDOFF.md list for agents 1-12.
- **Read for the draft 2 delta (07:04-07:20):**
  - RESUME draft 2 in full (the mid-edit copy BA95FA19…), then its diff to the announced B12032E6…;
  - the sources under "Resolved" and "New in this version" above;
  - `build/agent4/HANDOFF.md` L16, L20 and L29-33;
  - FINDINGS L21, L141, L142, L146 and L147;
  - b2r L2210 and L2220 (gate 4 of row 40);
  - `build/agent4/repin/REPIN.md` L19-21;
  - `build/agent9/HANDOFF.md` L150-155;
  - `build/agent2/PENDING-DIFFS.md` L20, L30, L39-40, L65 and L130;
  - the HANDOFF.md list for agents 1-12 at 07:06 and 07:15.
- **Read for the final check (about 08:22-08:36):**
  - the 41 changed hunks of RESUME final (9DA0A4C3…) and the lines they cite;
  - `build/agent11/resume/rfinal-total-diff.txt` (C18FBD5C…);
  - the SCRNSAVE package's `install-log.txt` L1-54;
  - RATE-REQUEST (5824C87C…) L39-78, §10 and §16;
  - W5b.md rev 1 (6479A611…), `cluster-0221.txt` and the 0221 run's `perf.csv` (frame times only);
  - the HANDOFFs of agents 4, 5 (8315ACF4…), 7 (5D8BD9B0…), 8 (B38513BC…) and 11 (C508AD88…, 08:28:57);
  - `build/agent11/resume/facts-perfopt.md` (F0C88246…) L110-112;
  - FINDINGS L141-147;
  - the SESSION2.md tail (to L3355);
  - the other sources cited in the "Final version" section.
- **Read for the 08:39 update (08:39-08:42):** `rfinal3-diff.txt`, `rfinal3-dry.txt` and `rfinal3-apply.txt` in `build/agent11/resume/`; the backup `RESUME.0839-9DA0A4C3.md`; facts-perfopt.md L112; `t27/scrnsave-delta.md` L75 (N-4); and the updated HANDOFFs of agents 5 (488D14CA…) and 8 (87F2675C…).
- **Sent:**
  - 06:49: the interim version, to Agents 11 and 1;
  - 07:03: the fact-check update, to Agents 11 and 1;
  - 07:23: the draft 2 delta (R33-R38), to Agents 11 and 1;
  - about 08:38: the final check (F1 open, F2 resolved), to Agents 11 and 1, with the HANDOFF info to Agents 5 and 8;
  - about 08:44: the check of the 08:39 update (F1 fixed, no open findings), to Agents 11 and 1.
