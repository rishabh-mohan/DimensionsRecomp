# rev_edit4.py - REVIEW.md: the 21:25 (Agent 10) and 21:29 (Agent 1) MUSTs on 3EFC5312, my concurrence, and README 581A03DB.
# One-match substitutions, sha gate. Usage: python rev_edit4.py [--apply]
import hashlib, sys, shutil, datetime, os
D = r'<workspace>\build\agent11\launcher-review'
P = os.path.join(D, 'REVIEW.md')
GATE = '7CFEBAF8B9E832F4F7CF50571DC3C9382E8F696E7BCFD310C9589317277FC863'
apply = len(sys.argv) > 1 and sys.argv[1] == '--apply'
b = open(P, 'rb').read()
h = hashlib.sha256(b).hexdigest().upper()
if h != GATE:
    print('GATE FAIL', h); sys.exit(1)
t = b.decode('utf-8')
subs = [
    # 0 status line
    (r'''interims: v3 at 21:15, CD64BC93 and 3EFC5312 at 21:25)**''',
     r'''interims: v3 at 21:15, CD64BC93 and 3EFC5312 at 21:25, the 21:25/21:29 MUSTs and README 581A03DB at 21:35)**'''),
    # 1 Files: README 581A03DB row
    ("| (20:53:42) | README.md | 39ECF5C21234B500… | 16,507 B; only searched so far (L117, L163, L170, L202); full read in the formal pass |\n",
     "| (20:53:42) | README.md | 39ECF5C21234B500… | 16,507 B; only searched so far (L117, L163, L170, L202); full read in the formal pass |\n"
     "| (21:28:05) | README.md | 581A03DB66D34A276684F1AEC242FD0B14290C58748302C706DC9CEBF4F81D13 | 21,508 B, 263 LF lines, no CR. Copy, diff and grep: [r-2128-581A03DB](r-2128-581A03DB/). Interim read below; full read in the formal pass |\n"),
    # 2 verdict heading + the MUSTs paragraph
    ("## Verdict so far: SAFE (Agent 10's (5) driver fix is in since v3); the formal verdict waits for the final version\n",
     "## Verdict so far: SAFE once the 21:29 MUSTs are in; the formal verdict waits for the final version\n\n"
     "The MUSTs (Agent 10 at 21:25, Agent 1 at 21:29, SESSION2 L2910-2913; I agree with all three): `Stop-Tree` without `taskkill /T` (the PassThru kill added in CD64BC93 can reach processes outside the runner's tree through PID reuse: see the (8) row of the CD64BC93/3EFC5312 interim below); the 3-name driver allowlist back on top of the path rule; and the hard stop at 07:30, not 07:45. The README must then match. Agent 1's SHOULD: re-check `Get-BuildProcs` in `Start-WindowLocked`.\n"),
    # 3 (5) row: allowlist MUST
    (r'''<br>- static6 (CD64 rule): all 72 driver uses in the 27 matrix files are forward-slash strings (thread-cpu.ps1 63, pso-stats-at-end.ps1 7, io-counters.ps1 2). No arm is refused for its driver. |''',
     r'''<br>- static6 (CD64 rule): all 72 driver uses in the 27 matrix files are forward-slash strings (thread-cpu.ps1 63, pso-stats-at-end.ps1 7, io-counters.ps1 2). No arm is refused for its driver.<br>- **MUST (Agent 10 at 21:25; Agent 1 made it a MUST at 21:29, SESSION2 L2911; I agree):** put the 3-name allowlist back on top of the path rule (thread-cpu, pso-stats-at-end, io-counters). It refuses no current arm, and it keeps out sys-csv.ps1 (the runner's own helper, not an arm driver) and any .ps1 added to drivers\ before the double-click. README R121 must then name the 3 files. |'''),
    # 4 (7) row: Get-BuildProcs SHOULD
    (r'''| Agent 10's (7) last checks | Done, as in v3 (L672-697). `Start-WindowLocked` now also checks the latest start (L687). |''',
     r'''| Agent 10's (7) last checks | Done, as in v3 (L672-697). `Start-WindowLocked` now also checks the latest start (L687).<br>- **SHOULD (Agent 10, 21:25; Agent 1, 21:29, SESSION2 L2912; I agree):** re-check the build processes (`Get-BuildProcs`) there too, as the gate does. |'''),
    # 5 (8) row heading
    (r'''| Agent 10's (8) PassThru | **Done** (SHOULD).<br>''',
     r'''| Agent 10's (8) PassThru | **Done (SHOULD), but `Stop-Tree` needs a MUST-FIX and the hard stop must move to 07:30** (below).<br>'''),
    # 6 (8) row: hard stop 07:30
    (r'''<br>- Every second it checks for a STOP file and for the end time + `$GraceMinutes` (15 min) (L789-805).<br>''',
     r'''<br>- Every second it checks for a STOP file and for the end time + `$GraceMinutes` (15 min) (L789-805).<br>- **MUST (Agent 1, 21:29, SESSION2 L2913): the hard stop is 07:30, not 07:45.** Today it is the end time + 15 min = 07:45 (`$hardEnd`), and README R47, R176 and R242 say 07:45 too. For example, default `$GraceMinutes` to 0, or cap `$hardEnd` at the end time.<br>'''),
    # 7 (8) row: Stop-Tree MUST-FIX
    (r'''<br>- `Stop-Tree` (L761-779) runs `taskkill /PID <runner> /T /F`, falls back to `Kill()`, and logs whether the runner is gone.<br>''',
     r'''<br>- `Stop-Tree` (L761-779) runs `taskkill /PID <runner> /T /F`, falls back to `Kill()`, and logs whether the runner is gone.<br>- **MUST-FIX (Agent 10, 21:25; Agent 1, 21:29, SESSION2 L2910; I confirm it):** `/T` follows ParentProcessId with no creation-time check. A process whose parent has exited is therefore taken for a child of whatever later process reuses that PID, at any level of the runner's tree. My read-only census at 21:27 ([pidreuse-check.txt](pidreuse-check.txt), 365 processes) found 9 such orphans, among them explorer.exe, firefox.exe and Discord.exe in the user session. A hit would kill explorer.exe and everything under it, far outside the five approved apps. The fix, as Agent 10 proposes: take one Win32_Process snapshot and walk down from the runner, keeping only children whose CreationDate is at or after their parent's; kill those and the runner. If the snapshot fails, use only `$P.Kill()` plus the build\agent2 legodimensions sweep, never `/T`. Optional hardening: kill the runner first, by its handle, so it can't start the next run (its PID can't be reused while the launcher holds the handle); re-check each target's StartTime right before killing it; and walk once more for late spawns.<br>'''),
    # 8 F5 row: Agent 1's approval + README
    (r'''<br>- The README wording (R21, R53) is still to check in the full read. |''',
     r'''<br>- **Approved by Agent 1 at 21:29** (SESSION2 L2914): on this PC "Copilot" is the Microsoft 365 Copilot app (Microsoft.MicrosoftOfficeHub, the only Copilot installed), and the Store Roblox app (Windows10Universal, path-checked) is the player.<br>- README 581A03DB names both, with the path check (R21, R55). |'''),
    # 9 README row
    (r'''| README | **Unchanged since 20:53:42** (39ECF5C2). Still to add:<br>- the F1 keys (R117, R163, R170);<br>- the driver rule (R119: a plain `drivers/<name>.ps1`);<br>- the 06:45 latest start;<br>- the 14 h rule (a start before 17:30 is refused too);<br>- the new test hooks (R244). |''',
     r'''| README | **Updated at 21:28:05** (581A03DB), read as a diff against 39ECF5C2 ([r-2128-581A03DB/diff-readme.txt](r-2128-581A03DB/diff-readme.txt): 41 lines new, 30 gone). R = 581A03DB's lines.<br>- Now in: the 11 F1 keys (R119, R163, R167, R174); the plain `drivers/<name>.ps1` rule (R121); the 06:45 latest start (R12, R46, R125, R156, R189); the 14 h rule (R23, R242); the close list with the Copilot app, the Store Roblox app and the path check (R21, R55); STOP during a window (R217); the runner's .out/.err files (R175, R234); exit codes 2 and 1 (R238); the new hooks and the `run` test group (R251-253, R258).<br>- To change with the MUSTs: the hard stop (R47, R176, R242 say 07:45); the kill text (R176: `taskkill /T /F`); the driver rule (R121: the 3 names).<br>- Nit: a start before 17:30 is refused too. R23 says only "after 07:30", but "start it in the evening" covers it. |'''),
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
