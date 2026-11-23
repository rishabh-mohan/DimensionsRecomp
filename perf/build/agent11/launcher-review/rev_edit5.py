# rev_edit5.py - REVIEW.md: interim on B0902106 (the three MUSTs and the SHOULD are in the code), what is still open.
# One-match substitutions, sha gate. Usage: python rev_edit5.py [--apply]
import hashlib, sys, shutil, datetime, os
D = r'<workspace>\build\agent11\launcher-review'
P = os.path.join(D, 'REVIEW.md')
GATE = '0EF46B0DE1AC56360EA21B7A848F9CEF491E00DA7FC83E71015F01F8DBFE434E'
apply = len(sys.argv) > 1 and sys.argv[1] == '--apply'
b = open(P, 'rb').read()
h = hashlib.sha256(b).hexdigest().upper()
if h != GATE:
    print('GATE FAIL', h); sys.exit(1)
t = b.decode('utf-8')

SECTION = r'''## Interim: B0902106 (21:42:43), read as a diff against 3EFC5312

RUN-NIGHT.cmd (F7190AB2) and the README (581A03DB) are unchanged. I read the full 3EFC→B090 diff ([p-2147-B0902106/diff-run-night.txt](p-2147-B0902106/diff-run-night.txt), +89/-27), read L769-874 again in the copy, and ran [pass.ps1](pass.ps1) ([p-2147-B0902106/pass.txt](p-2147-B0902106/pass.txt)): 77,221 B, 1010 LF lines, ASCII, no BOM, PS 5.1 ParseFile 0 errors. Agent 10's delta read (21:48) agrees. Line numbers in this section are B0902106's.

| Item | B0902106 |
|---|---|
| `Stop-Tree` MUST-FIX | **Done** (L769-833). This is the fix Agent 10 proposed, with all three optional hardenings.<br>- No `taskkill` is left in the file.<br>- `Get-Descendants` (L773-793) takes one CIM Win32_Process snapshot (`-OperationTimeoutSec 20 -ErrorAction Stop`) and walks down from the runner, parents first. It follows a child only if its CreationDate is at or after its parent's (L788). The runner's own floor is its StartTime truncated to 1 µs (L810), the precision of CreationDate.<br>- `Stop-One` (L795-802) re-checks right before `Kill()` that the PID's StartTime is within 2 ms of the snapshot's CreationDate (L799). If not, it logs the PID as left alone.<br>- The runner is killed first (L811), so it starts nothing new. `[void]$p.Handle` (L841) keeps its PID from being reused while the launcher runs. Up to 3 walks catch late starts (L813-818).<br>- If the runner's StartTime or the snapshot can't be read, only the runner is killed (L810, L815). Real mode then runs the legodimensions sweep (L820-830, unchanged: this session only, started at or after the window's start, under build\agent2\).<br>- A process with no readable CreationDate is skipped (L776), which errs on the safe side. |
| Driver allowlist MUST | **Done** (L45, L285-294). `$AllowedDrivers` = thread-cpu.ps1, pso-stats-at-end.ps1, io-counters.ps1, checked with `-ccontains` on top of the plain-string path rule (L292). [static6](p-2147-B0902106/static6-out.txt) reads the list (DriverRule v3-list): every driver use in the 26 matrix files is one of the 3 names (thread-cpu 57, pso-stats-at-end 7, io-counters 2). |
| Hard stop 07:30 MUST | **Done** (L24, L843-845). `$GraceMinutes` defaults to 0, so `$hardEnd` is the end time, 07:30. `-GraceMinutes` is still a dry-run-only hook (L65). |
| `Get-BuildProcs` SHOULD | **Done** (L700-703). `Start-WindowLocked` re-checks the build processes, as the gate does. Tests use the fixture's `builds_at_start` list. |
| Also new (fine) | - `-TestFailAfter` (L26, L860) is in `$hookNames`, so it is refused without `-DryRun`. It throws inside `Invoke-Runner`; the catch logs the error and the `finally` calls `Stop-Tree`.<br>- An `$ended` flag (L847-870) makes a Ctrl+C reach `Stop-Tree` in the `finally` too. That path is best-effort: with `-NoNewWindow` the runner shares the console, so a Ctrl+C reaches it as well. Nobody is at the console overnight, and the README's way to stop is the STOP file.<br>- `Log` writes the log files before the console. |
| Unchanged | F1 (exactly the 11 keys), F3, F5, (6) and (7), as in 3EFC5312. |

**W6 under B0902106's rules** (static6): Agent 5's real finalize `build/agent5/w6-draft/matrix-window6.json` (E50D791B) and Agent 8's staged test copy (BD0696DA) pass every arm rule (6 arms each, devoff4b-bin). The template matrix-w6.json (8440B1E4) is refused only for its placeholder bin. 26 files, 8 fully accepted.

**Still open before the formal verdict:**
- README 581A03DB, to match the code:
  - R47: "If a window is somehow still running at 07:45, it stops that window";
  - R176: "the end time + 15 min (07:45)" and `taskkill /T /F`;
  - R242: "end time + 15 min";
  - R251: `-GraceMinutes` with a default of 15, and no `-TestFailAfter`;
  - R121: should name the 3 driver files;
  - R261 (the `run` test group): should list STOP mid-window, the 07:30 kill, `-TestFailAfter` and the child kill;
  - nit: R23 could say that a start before 17:30 is refused too.
- Test evidence on the final hash. summary-run.txt (21:33, on 3EFC5312) failed 3 of 3: t-run-ok timed out; in t-run-stop the STOP was consumed in the gate wait, so no window started; t-run-deadline never reached "window T1 START". Needed: go, gate and run summaries that carry the final hash and pass, with a normal end, STOP mid-window with the fake child killed, the 07:30 kill and `-TestFailAfter`.
- The RUN-NIGHT.cmd STOP-file smoke test (expect exit 2): not seen yet.

'''

subs = [
    # 0 status line
    (r'''README 581A03DB at 21:35)**''',
     r'''README 581A03DB at 21:35, B0902106 at 21:55)**'''),
    # 1 Files: B0902106 row after the README 581A03DB row
    ("| (21:28:05) | README.md | 581A03DB66D34A276684F1AEC242FD0B14290C58748302C706DC9CEBF4F81D13 | 21,508 B, 263 LF lines, no CR. Copy, diff and grep: [r-2128-581A03DB](r-2128-581A03DB/). Interim read below; full read in the formal pass |\n",
     "| (21:28:05) | README.md | 581A03DB66D34A276684F1AEC242FD0B14290C58748302C706DC9CEBF4F81D13 | 21,508 B, 263 LF lines, no CR. Copy, diff and grep: [r-2128-581A03DB](r-2128-581A03DB/). Interim read below; full read in the formal pass |\n"
     "| p-2147 (21:42:43) | run-night.ps1 | B0902106C4D935810C5747951095053E117165BE36CF8FE1F32B0C0337E8DB33 | 77,221 B, 1010 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy and checks: [p-2147-B0902106](p-2147-B0902106/). Diff 3EFC→B090: +89/-27, read in full. Interim read below |\n"),
    # 2 verdict heading
    ("## Verdict so far: SAFE once the 21:29 MUSTs are in; the formal verdict waits for the final version\n",
     "## Verdict so far: the MUSTs are in the code (B0902106); SAFE once the README and the tests match; the formal verdict waits for the final version\n"),
    # 3 B0902106 paragraph after the MUSTs paragraph
    ("Agent 1's SHOULD: re-check `Get-BuildProcs` in `Start-WindowLocked`.\n",
     "Agent 1's SHOULD: re-check `Get-BuildProcs` in `Start-WindowLocked`.\n\n"
     "**B0902106 (21:42:43) has all three MUSTs and the SHOULD in the code** (see the B0902106 interim below; Agent 10's delta read at 21:48 agrees). Still open: the README lines (R47, R176, R242, R251, R121, R261), test summaries on the final hash (the 21:33 run group failed 3 of 3 on 3EFC5312), and the RUN-NIGHT.cmd STOP smoke test.\n"),
    # 4 Method 8
    ("8. Rules from SESSION2.md (to L2873) and S4-DRAFT.md.",
     "8. Rules from SESSION2.md (to L2919 at 21:47) and S4-DRAFT.md."),
    # 5 new section + Next list
    ("## Next (when Agent 5 asks)\n\n1. Hash the new files and diff them against v2-924321AE.\n2. Re-run the parse, byte and arm checks.\n3. Confirm each fix: Agent 10's 1-8; must-fix F1, F3 and README L151; should-fix F5; optional F4 and F6.\n4. Give the formal verdict to Agents 5 and 1 and update this file.",
     SECTION +
     "## Next (when Agent 5 asks)\n\n1. Run [pass.ps1](pass.ps1) on the final files against p-2147-B0902106 and r-2128-581A03DB; read the diffs and the whole README.\n2. Check the go, gate and run summaries in build/agent5/launch-test/results/ (final hash, PASS, the cases above) and the RUN-NIGHT.cmd STOP smoke test.\n3. Give the formal verdict to Agents 5 and 1 (by 23:00) and update this file."),
]
for i, (o, n) in enumerate(subs):
    c = t.count(o)
    if c != 1:
        print('SUB', i, 'count', c); sys.exit(2)
    t = t.replace(o, n)
nb = t.encode('utf-8')
print(('APPLY' if apply else 'DRY OK'), len(subs), 'subs', len(b), '->', len(nb), 'B', t.count('\n'), 'LF', 'CR', t.count('\r'))
if apply:
    bk = os.path.join(D, 'REVIEW.%s-%s.md' % (datetime.datetime.now().strftime('%H%M'), GATE[:8]))
    shutil.copyfile(P, bk)
    open(P, 'wb').write(nb)
    print('new sha', hashlib.sha256(open(P, 'rb').read()).hexdigest().upper(), 'backup', os.path.basename(bk))
