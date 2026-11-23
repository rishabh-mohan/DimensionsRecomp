# One-match edits of REVIEW.md (Agent 11's own file): add the v3 interim read. Gate: 368931AE (21:03).
import hashlib, shutil, sys

P = 'build/agent11/launcher-review/REVIEW.md'
GATE = '368931AE54D5BAEA9C28D2C05C7F4253F558A240E153687337C1B910433E1F61'
b = open(P, 'rb').read()
h = hashlib.sha256(b).hexdigest().upper()
if h != GATE:
    sys.exit('GATE FAIL ' + h)
s = b.decode('utf-8')
assert '\r' not in s

ROW_CMD = '| v2 (20:51:01) | RUN-NIGHT.cmd | F7190AB228CF0EF90980103B04F079AFC5CE23BC92E3390A3A539D2C25CD5EAF | 1,012 B, CRLF (18 CR / 18 LF) |\n'
V3ROW = ('| v3 (21:01:12) | run-night.ps1 | 163D76596E575D8D4684417869AE8C8D67E92CE7E38D17BD1172014BBD0DAF69 | 63,759 B, 846 LF lines, ASCII, no BOM, '
         'ParseFile 0 errors. Copy: [v3-163D7659](v3-163D7659/). Diff: [diff-v2-v3.txt](diff-v2-v3.txt) (+81/-23). Interim read below |\n')

NEXT = '## Next (when Agent 5 asks)\n'
V3SEC = '''## Interim: v3 run-night.ps1 163D7659 (21:01:12), read as a diff against v2

RUN-NIGHT.cmd (F7190AB2) and the README (39ECF5C2) are unchanged since v2. Line numbers in this section are v3's.

| Item | v3 |
|---|---|
| Agent 10's (5) driver | **Done** (L37, L272-284). `$AllowedDrivers` = thread-cpu.ps1, io-counters.ps1, pso-stats-at-end.ps1. Only a plain string passes: `-cmatch '^drivers[/\\\\]([A-Za-z0-9_-]+\\.ps1)$'`, and the resolved path must equal `$RunDir\\drivers\\<name>`, exist and be pinned. Objects, and so args, are refused. [static6.ps1](static6.ps1) on v3 ([static6-out-163D7659.txt](static6-out-163D7659.txt)): all 66 driver uses in the 26 matrix files are those 3 names, so the rule refuses no existing arm. sys-csv.ps1 (in drivers\\ but not in the list) is the runner's own sys_csv helper (run-matrix.ps1 L422-424), not an arm driver. |
| Agent 10's (6) 14 h | **Done** (L38 `$MaxRunHours = 14`; start check L795). Side effect: a start before 17:30 is refused too, so the README should say "start it after 17:30". Tonight's ~23:45 start is 7.75 h before 07:30. |
| Agent 10's (7) last checks | **Done** (L656-680). `Start-Window` closes the programs first, then holds the matrix json open with read sharing until the runner ends. `Start-WindowLocked` then re-checks pins, bins, the deadline, the desktop, LogonUI, AC power and Sync-Hold right before the runner. The dry-run guard in Close-Programs is per process (L500), so moving the call is safe. |
| Note: separate try in the finally | **Done** (`Try-Step` L78, L837-841: screensaver first, then HOLD, keep-awake, state). |
| Agent 10's (8) PassThru | Not yet (SHOULD). |
| F1 env keys | Not yet (Agent 8's list is due 21:45). |
| F3 06:45 | Not yet (MUST). |
| F5 apps | **Not met yet.** v3 adds `$CopilotRx` = `\\\\WindowsApps\\\\Microsoft\\.(Copilot\\|Windows\\.Ai\\.Copilot)_` for the process names Copilot and Microsoft.Copilot (L49-50). Neither package is installed here ([static3-out.txt](static3-out.txt)), so it still closes nothing on this PC. Still needed: copilotapphost and copilotapp_proxy under `\\WindowsApps\\Microsoft.MicrosoftOfficeHub_`, and Windows10Universal under `\\WindowsApps\\ROBLOXCORPORATION.ROBLOX_`. `MainModule.FileName` can be denied for packaged apps, so a fallback via Win32_Process.ExecutablePath (QueryFullProcessImageName) is safer. |
| Also new in v3 (all fine) | Unknown arguments are refused (L28). Without `[CmdletBinding()]`, a typo like `-DryRunn` would have run REAL mode. A GO that can't be deleted is refused. Bins are re-hashed after the run, and each post-run check has its own try. Clear-Hold retries 5 times and stops once the HOLD isn't ours. Only this session's processes are closed. Timestamps use the invariant culture. |

**W6 and the follow-up candidates under v3's rules** (static6): Agent 8's staged `build/agent8/w6-stage/test/matrix-window6.json` (BD0696DA, devoff4b-bin, 6 arms) passes every arm rule. So do matrix-window4.json (6CA4AC6E: d0, B, d3, d0t, d11t), matrix-window5-s3d.json (4D7D689B) and matrix-codegen.json (40CF4072), which hold the arms for SESSION2 L2885's follow-up windows. The draft matrix-w6.json (D6388096) fails only on its placeholder bin `build/agent2/S4b-bin-TBD`.

'''

SUBS = [
    (ROW_CMD, ROW_CMD + V3ROW),
    (NEXT, V3SEC + NEXT),
    ('Status: **PRE-READ (20:58, updated 21:03)**', 'Status: **PRE-READ (20:58, updated 21:03; v3 interim 21:15)**'),
]
for old, new in SUBS:
    n = s.count(old)
    if n != 1:
        sys.exit('MATCH FAIL n=%d: %s' % (n, old[:70]))
    s = s.replace(old, new)

# table sanity: every table row in the new section has the same pipe count as its header (escaped \\| excluded)
import re
sec = s[s.index('## Interim: v3'):s.index(NEXT)]
rows = [r for r in sec.split('\n') if r.startswith('|')]
counts = {len(re.findall(r'(?<!\\)\|', r)) for r in rows}
if len(counts) != 1:
    sys.exit('TABLE FAIL %s' % sorted(counts))

if '--apply' in sys.argv:
    shutil.copyfile(P, 'build/agent11/launcher-review/REVIEW.2103-368931AE.md')
    out = s.encode('utf-8')
    open(P, 'wb').write(out)
    print('APPLIED', hashlib.sha256(out).hexdigest().upper(), len(out), 'B', s.count('\n'), 'LF', 'rows', len(rows), 'pipes', counts)
else:
    print('DRY OK', len(SUBS), 'subs', s.count('\n'), 'LF', 'rows', len(rows), 'pipes', counts)
