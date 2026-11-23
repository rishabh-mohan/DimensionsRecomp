# rev_edit6.py - REVIEW.md: the formal verdict on run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B, README 0058C8F6.
# One-match substitutions, sha gate. {T} = the apply time (HH:MM). Usage: python rev_edit6.py [--apply]
import hashlib, sys, shutil, datetime, os
D = r'<workspace>\build\agent11\launcher-review'
P = os.path.join(D, 'REVIEW.md')
GATE = 'C9884F6D836813E3D22CAB147A7A9ADEB3B704C685C38C83904E56AEBE01DFA2'
apply = len(sys.argv) > 1 and sys.argv[1] == '--apply'
T = datetime.datetime.now().strftime('%H:%M')
b = open(P, 'rb').read()
h = hashlib.sha256(b).hexdigest().upper()
if h != GATE:
    print('GATE FAIL', h); sys.exit(1)
t = b.decode('utf-8')

RELAXED = r'''first run FAILed on the test, not the launcher: with `-StrictMinutes 0.25` and the machine loaded, the third sample came at +0.4 min, after the strict phase, so the expected strict-phase wait line never appeared, and the launcher relaxed correctly at 1.05/0.98/1.10 (all ≤ 1.2 cores, spread 0.12). The re-run PASSES (22:28:05, run-tests.ps1 of 22:25:33 with `-StrictMinutes 1`): "strict gate for the first 1 min" wait lines, then "PASS (relaxed)" at +1 min with 1.02/1.02/1.02'''

VERDICT = r'''## Formal verdict ({T}): SAFE

**SAFE: run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B and README 0058C8F6 can be pinned at 23:30 and double-clicked tonight.**
- **Code:** all three MUSTs and the SHOULD are in: `Stop-Tree` without `taskkill`, the 3-name driver allowlist, the hard stop at 07:30, and `Get-BuildProcs` in `Start-WindowLocked`. Since B0902106 only the `Stop-One` catch has changed (Final section). Also in: must-fix F1, F3 and README L151; should-fix F5; and Agent 10's 1-3, 4's CRLF, and (5)-(8).
- **README:** it matches the code. I read it in full; see the Final section.
- **Tests:** Agent 5's tests on 16B90FA8 pass:
  - go 16/16 (22:18:06);
  - hold 4/4 (22:14:35);
  - run 5/5 (22:22:23);
  - gate 12/13 (22:23:57), plus the t-relaxed re-run. t-relaxed's ''' + RELAXED + r'''.
- **Safety:** nothing in them could harm the user's PC or data, or start a window unsafely.
- **Left open (not safety items):**
  - The RUN-NIGHT.cmd STOP-file smoke test (Agent 10's (4), expect exit 2) is still not seen, so the cmd's first real run would be the double-click. A cmd that fails costs the night, not the PC.
  - Re-hash RUN-NIGHT.cmd after any pin-group run (that group appends a line and then restores the file).
  - Ctrl+C is best-effort (documented).
- **Changes:** any change to these three files after this needs a new pass and a new verdict.

**Verdict so far at 21:55** (kept for the record): the MUSTs are in the code (B0902106); SAFE once the README and the tests match.
'''

FINAL = r'''## Final: run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B, README 0058C8F6 (formal pass, {T})

I ran [pass.ps1](pass.ps1) at 22:14 against B0902106, F7190AB2 and 581A03DB ([p-2214-16B90FA8/pass.txt](p-2214-16B90FA8/pass.txt)). I read all three diffs and the whole README, and re-hashed the three files at 22:28 (unchanged since 22:12:38). L = 16B90FA8's lines, R = README 0058C8F6's lines.

| Item | Final |
|---|---|
| run-night.ps1, B090→16B9 | +8/-1 ([diff](p-2214-16B90FA8/diff-run-night.txt)), read in full.<br>- Only the `Stop-One` catch changes. If `Kill()` throws, it waits up to 3 s (`WaitForExit(3000)`), then logs `(ended on its own)` or `(NOT killed: <message>)`.<br>- There is no new kill path, and the 2 ms StartTime re-check before each kill is unchanged.<br>- 77,594 B, 1017 LF lines, ASCII, no BOM, PS 5.1 ParseFile 0 errors. |
| RUN-NIGHT.cmd | The only change since F7190AB2 is C15 ([diff](p-2214-16B90FA8/diff-cmd.txt)): `if not "%RC%"=="0" if not "%RC%"=="2" if not "%RC%"=="3" echo The launcher was interrupted (exit code %RC%, e.g. Ctrl+C)...`. CRLF 19/19, no bare LF, ASCII. Fine. |
| README 0058C8F6 | Read in full (271 LF lines, no CR; [diff against 581A03DB](p-2214-16B90FA8/diff-readme.txt)). Every README item open at 21:55 is fixed:<br>- R23: it starts only between 17:30 and 07:30 (the 14 h rule);<br>- R46-47: the night ends at 07:30, and a window still running then is stopped first;<br>- R121: exactly the 3 driver files; sys-csv.ps1 is refused;<br>- R158: the build/game check is in the last checks;<br>- R177-183: the 07:30 hard stop; the runner killed first, by its handle; the creation-time walk, up to 3 times; "There is no taskkill"; the log lines, with "(already gone)", "(ended on its own)" and "(NOT killed)"; the launcher-error and Ctrl+C paths;<br>- R74-77: Ctrl+C and the Terminate-batch-job prompt;<br>- R245: the exit codes, and state.txt after a Ctrl+C;<br>- R249: the hard stop is the end time itself (07:30); a start before 17:30 or after 07:30 is refused;<br>- R258: the test hooks, with `-GraceMinutes` (default 0), `-TestFailAfter <s>` and `-SkipStartChecks`;<br>- R265: the fixture's `builds_at_start`;<br>- R267-271: the test groups. `run` covers a normal end, STOP, the end-time kill, `-TestFailAfter` and Ctrl+C (send-ctrlc.ps1), and checks that the child is killed. |
| `-SkipStartChecks` | Dry-run only, twice over: it is in `$hookNames` (L65), and both uses also test `$DryRun -and $SkipStartChecks` (L697, L962). It has been there since v3. Fine. |
| W6 under 16B90FA8's rules | [static6](p-2214-16B90FA8/static6-out.txt): 28 files, 10 fully accepted (DriverRule v3-list, 11 env keys).<br>- These pass every arm rule: the promoted `bench/agent8/run/matrix-window6.json` (E50D791B, the same bytes as Agent 5's w6-draft finalize), its check copy (77651D94) and Agent 8's staged test copy (BD0696DA).<br>- The template matrix-w6.json (8440B1E4) is refused only for its placeholder bin. |
| Tests on 16B90FA8 | Agent 5's summaries in build/agent5/launch-test/results/; each first line carries the hash.<br>- go 16/16 PASS (22:18:06).<br>- hold 4/4 PASS (22:14:35).<br>- run 5/5 PASS (22:22:23): normal end, STOP while running, end-time kill, launcher error (`-TestFailAfter 25`), Ctrl+C while running.<br>&nbsp;&nbsp;- Each kill logs the runner killed (after the Ctrl+C, "had already ended"), then "killed (walk 1)" with the fake child powershell.exe and its conhost.exe, then "runner stopped: yes". The harness checks that the fake runner and its child are gone ([t-run-grep-2223.txt](t-run-grep-2223.txt)).<br>&nbsp;&nbsp;- The end-time test reaches the same `$hardEnd` path early, with `-StopAt` and a negative `-GraceMinutes`. In real mode GraceMinutes is 0, so `$hardEnd` is 07:30.<br>&nbsp;&nbsp;- `send-ctrlc.ps1` attaches only to the launcher's own hidden console.<br>- gate 12/13 PASS (22:23:57; read at 22:25, since overwritten by the re-run's summary): t-build, t-build-giveup, t-build-start, t-close, t-stop-start (exit 2), t-stop-wait, t-stop-gate, t-unstable, t-toohigh, t-lowres, t-json, t-real.<br>- t-relaxed: ''' + RELAXED + r''' (summary-gate-relaxed-rerun.txt). |
| Not seen (not safety items) | - The RUN-NIGHT.cmd STOP-file smoke test (Agent 10's (4), expect exit 2). Without it, the cmd's first real run is the user's double-click. bench/agent5/launch/status/ doesn't exist, so the launcher has never run in real mode.<br>- The pin group (t-pin-go, t-pin-gate). It appends a line to RUN-NIGHT.cmd for a few seconds and then restores it, so re-hash the cmd after it runs. |
| Known limits (accepted) | - Ctrl+C is best-effort: with `-NoNewWindow` the runner shares the console. Nobody is at the console overnight, and the STOP file is the documented way to stop.<br>- The walk skips a process with no readable CreationDate (the safe side).<br>- Agent 1's hold manager exits at 07:30 without clearing (F6). Agent 1 clears a stale HOLD in the morning. |

## After the verdict

1. Pin exactly these three hashes at 23:30. A change to any of them after this needs a new [pass.ps1](pass.ps1) run (prevs: [p-2214-16B90FA8](p-2214-16B90FA8/)) and a new verdict.
2. Agent 5: run the RUN-NIGHT.cmd STOP smoke test before 23:30 if possible, and re-hash RUN-NIGHT.cmd after any pin-group run.
3. W6's GO line (Agent 8, 22:09, SESSION2 L2985) is `GO W6 matrix-window6.json E50D791B… only=s0,p2,p2f,p2fc repeats=5`. static6 passes all 6 arms of that file, so the 4-arm subset passes too. The go group's t-good and t-badgo ×7 cover the GO format.
4. Agent 1's daytime launcher plan (22:25, SESSION2 L2984) adds RUN-DAY.cmd and STOP-LAUNCHER.cmd after the night final, and leaves run-night.ps1 unchanged. This verdict doesn't cover them, so they need their own review before the user uses them.'''

subs = [
    # 0 status line
    ("Status: **PRE-READ (20:58, updated 21:03; interims: v3 at 21:15, CD64BC93 and 3EFC5312 at 21:25, the 21:25/21:29 MUSTs and README 581A03DB at 21:35, B0902106 at 21:55)**, not yet the formal verdict. The formal verdict follows when Agent 5 asks (hard deadline 23:00, Agent 1 at 21:01).",
     "Status: **FORMAL VERDICT ({T}): SAFE** on run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B and README 0058C8F6 (see the Formal verdict and Final sections below). Before it: pre-read 20:58 (updated 21:03); interims v3 at 21:15, CD64BC93 and 3EFC5312 at 21:25, the 21:25/21:29 MUSTs and README 581A03DB at 21:35, B0902106 at 21:55. Hard deadline 23:00 (Agent 1 at 21:01)."),
    # 1 Files: three final rows after the p-2147 row
    ("| p-2147 (21:42:43) | run-night.ps1 | B0902106C4D935810C5747951095053E117165BE36CF8FE1F32B0C0337E8DB33 | 77,221 B, 1010 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy and checks: [p-2147-B0902106](p-2147-B0902106/). Diff 3EFC→B090: +89/-27, read in full. Interim read below |\n",
     "| p-2147 (21:42:43) | run-night.ps1 | B0902106C4D935810C5747951095053E117165BE36CF8FE1F32B0C0337E8DB33 | 77,221 B, 1010 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy and checks: [p-2147-B0902106](p-2147-B0902106/). Diff 3EFC→B090: +89/-27, read in full. Interim read below |\n"
     "| p-2214 (22:11:21) | run-night.ps1 | 16B90FA8654FAC088FE5A1248DE1754918AACC7667A2126AD14723BFBF939B31 | **Final.** 77,594 B, 1017 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy and checks: [p-2214-16B90FA8](p-2214-16B90FA8/). Diff B090→16B9: +8/-1, read in full |\n"
     "| (21:51:46) | RUN-NIGHT.cmd | D7A0362BE90C12B4F027116B9A5146D1F4C8D109110F885EE8CF62E6769DE6D5 | **Final.** 1,197 B, CRLF (19 CR / 19 LF), no bare LF, ASCII. Diff against F7190AB2: [p-2214-16B90FA8/diff-cmd.txt](p-2214-16B90FA8/diff-cmd.txt) |\n"
     "| (22:12:38) | README.md | 0058C8F61EEAA9F2529145B034433E2FB67344012D114E4103CE8E3A0EB43274 | **Final.** 23,844 B, 271 LF lines, no CR, no BOM. Read in full. Diff against 581A03DB: [p-2214-16B90FA8/diff-readme.txt](p-2214-16B90FA8/diff-readme.txt) |\n"),
    # 2 verdict heading -> formal verdict
    ("## Verdict so far: the MUSTs are in the code (B0902106); SAFE once the README and the tests match; the formal verdict waits for the final version\n",
     VERDICT),
    # 3 Method 8 + 9
    ("8. Rules from SESSION2.md (to L2919 at 21:47) and S4-DRAFT.md.",
     "8. Rules from SESSION2.md (to L3019 at 22:31) and S4-DRAFT.md.\n9. Agent 5's test summaries and console logs in build/agent5/launch-test/results/ (each summary's first line carries the run-night.ps1 hash), and run-tests.ps1 where a test failed. Run-group grep: [t-run-grep-2223.txt](t-run-grep-2223.txt)."),
    # 4 still-open list header in the B090 interim
    ("**Still open before the formal verdict:**",
     "**Still open before the formal verdict** (at 21:55; closed by the final files and tests except the cmd smoke test, see the Final section):"),
    # 5 Next -> Final section + After the verdict
    ("## Next (when Agent 5 asks)\n\n1. Run [pass.ps1](pass.ps1) on the final files against p-2147-B0902106 and r-2128-581A03DB; read the diffs and the whole README.\n2. Check the go, gate and run summaries in build/agent5/launch-test/results/ (final hash, PASS, the cases above) and the RUN-NIGHT.cmd STOP smoke test.\n3. Give the formal verdict to Agents 5 and 1 (by 23:00) and update this file.",
     FINAL),
]
for i, (o, n) in enumerate(subs):
    c = t.count(o)
    if c != 1:
        print('SUB', i, 'count', c); sys.exit(2)
    t = t.replace(o, n.replace('{T}', T))
if '{T}' in t:
    print('PLACEHOLDER LEFT'); sys.exit(3)
nb = t.encode('utf-8')
print(('APPLY' if apply else 'DRY OK'), T, len(subs), 'subs', len(b), '->', len(nb), 'B', t.count('\n'), 'LF', 'CR', t.count('\r'), 'BOM', nb[:3] == b'\xef\xbb\xbf')
if apply:
    bk = os.path.join(D, 'REVIEW.%s-%s.md' % (datetime.datetime.now().strftime('%H%M'), GATE[:8]))
    shutil.copyfile(P, bk)
    open(P, 'wb').write(nb)
    print('new sha', hashlib.sha256(open(P, 'rb').read()).hexdigest().upper(), 'backup', os.path.basename(bk))
