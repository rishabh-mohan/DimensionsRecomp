# Rating: M16 P1 package native5pack (candidate pack + bin build, no promotion)

Who/when: M10, 2026-11-26 ~06:08 local. Static review: diff reproduced on scratch copies, ast.parse, write-path review of native5pack.py, check script read in full, preflight state checked. No build run.

## Files (sha256/16) - WS\build\agent16\pack\

| file | sha256/16 | note |
|---|---|---|
| P1-native5pack.md | E2445EE82E131551 | package |
| native5pack.py | 7DDFB8B9DD53E0BF | 47926 B, LF |
| native5pack.diff | F5BBAEBE3FBD9927 | vs native4bp.py, +14/-13 |
| native5pack.ps1 | 22245C44E4E94942 | launcher |
| native5pack_check.py | F57713CE9EDBBCD8 | post-checks C1-C6 |
| plan-20261126-060314.txt | 161F7C5472770CA6 | static plan, PLAN OK |
| native4bp.py (base) | 37FD3989 | unchanged |
| native4bp.ps1 (base) | 83A8B01F | unchanged |

Base: the native4bp build of 2025-11-25 17:38 (binwork-20261125-173830, VERDICT PASS, wall 70.1 s), whose output is the pinned native4bp-bin (MANIFEST C5181520).

## Verdict: SAFE-IF (N1-N6) -> GO for pack, then bin, then check

## What I checked

- Diff: `git diff --no-index native4bp.py native5pack.py` on my scratch copies equals native5pack.diff byte for byte once its CRLF are folded to LF (the sources are LF; the .diff file has 90 CRLF). +14/-13, exactly the 4 changes the package lists:
  - the LATEST-pack.txt write becomes a log line;
  - the LATEST-bin.txt write becomes a log line;
  - bin has `pr = None` without `--pack-run`, then fails closed on "pack run has no pack-check.json" before any copy;
  - the `--bin-out` default and the names in log, title and note.
- ps1: diff vs native4bp.ps1 is comments plus the script name (6/6 lines). Idle + affinity 0x3 set before devshell; exit code passed through.
- ast.parse OK for native5pack.py and native5pack_check.py.
- Write paths in native5pack.py: every open-for-write, makedirs, copyfile and os.replace goes through `in_pack()` (abspath must start with WS\build\agent16\pack\), except `makedirs(bw)`, where bw is already in_pack. Subprocesses run with IDLE | NOWIN; a timeout kills only the child tree by PID. No network imports.
- relink runs with cwd = build\agent2\snap1-on (ninja). The identical native4bp recipe ran at 17:38-17:39 and left snap1-on untouched: no top-level entry newer than 2026-11-25 17:00; .ninja_log / .ninja_deps last written 2026-11-22. So the recipe doesn't write there in practice.
- Plan 161F7C54: native5pack.py at Idle (0x40) / 0x3, 143 selected (4 s35 + 139), 2 excluded, 0 input failures, PLAN OK; staged bin native5pack-bin; "(no LATEST-pack.txt)".
- Check script: writes only native5pack-check-<stamp> under pack (refuses a reused dir and a missing bin, exit 2); tool pins verify-bins 80FF4C5F and pe-check F4368C32. C3 references match today: native4bp MANIFEST C5181520, nf2 MANIFEST 4E5E2620, LATEST-pack AC7B9053, LATEST-bin 76D0EFB9 (re-hashed by me).
- Preflight now: no legodimensions process; s5wait status last line is END (RUN-GAMEPLAY 06:00:55, exit 0); perf-notes\WINDOW-HOLD.txt absent; native5pack-bin absent; C: ~154 GB free.

## Conditions

- N1 (serialise): the build runs alone. No game run, dryrun, timed window or other heavy I/O from pack start to check end. M3's zone install, tamper and dryruns come after the check report. Preflight items 1-5 before each of the 3 steps.
- N2 (commands): exactly the two commands in package §3, with `--pack-run` = the run dir step 1 created. Step 2 only on `VERDICT PASS`; step 3 (native5pack_check.py) only on bin `VERDICT PASS`.
- N3 (report): send me
  - pack: pack-log.txt sha + VERDICT line, side-effects.txt content, the "LATEST-pack.txt not written" line, STAGED.tsv row count, index rows old/new;
  - bin: bin-log.txt sha + VERDICT line, every gate line (CTL and ON), MANIFEST sha, exe sha, fp5, the "LATEST-bin.txt not written" line;
  - check: native5pack-check.txt sha + RESULT line.
  I will then re-check read-only that snap1-on and the PINS_BIN files are unchanged (bin has no pin re-check after its run).
- N4 (no promotion): native5pack-bin is not referenced by any kit, pin, LATEST file or default. Any game run on it (the miss-count proof run) needs its own rating; its kit must pin the new MANIFEST, and the first boot is cold (new fingerprint), so no timing from the first boot.
- N5 (failure): any FAIL stops the sequence; report it, no retry or patch without a re-rate. Rollback deletes only the 4 named dirs (run-<S1>, binwork-<S2>, native5pack-bin, native5pack-check-<stamp>).
- N6: any change to the 4 files above -> re-hash, re-rate.

## Findings

- SHOULD S1: bin has no pin re-check or watched-dir diff after its run (pack has both). The evidence from 17:38 says the recipe doesn't write outside pack, and N3 covers it by my after-check. A `check_pins(PINS_BIN)` after stage would close it in the script.
- NIT N1: the header comment (L19) still lists `pack\LATEST-pack.txt` among the pack outputs.
- NIT N2: native5pack.diff was saved with CRLF, so `git apply` refuses it against the LF sources. The content is right. Write future diffs without newline conversion.
- NIT N3: native5pack.ps1 hard-codes the WS absolute path, as native4bp.ps1 does. It's fine in this workspace.
- Note: the visual-change risk (draws that now hit may render differently) and the 22 no-identity guests stay out of scope here, as package §7 says.
