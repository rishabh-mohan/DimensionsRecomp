# -*- coding: utf-8 -*-
# run13.py - S4-DRAFT pass 3 for task #10 (Agent 11): SESSION2 21:55-22:44 (L2921-3124) + Agent 8's GO lines.
# Usage: python run13.py --dry | --apply. One-match edits, sha + line gates, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
DRAFT, HOLD = P('perf-notes/S4-DRAFT.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: run13.py --dry | --apply')
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
fails = []
def fail(m):
    fails.append(m); print('FAIL:', m)
if os.path.exists(HOLD):
    sys.exit('HOLD exists: stop')
raw = open(DRAFT, 'rb').read(); H0 = sha(raw)
print('draft %s %d B %d LF' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('E496D3F6') or raw.count(b'\n') != 519 or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('draft gate FAIL')
old = raw.decode('utf-8')
s2 = open(P('perf-notes/SESSION2.md'), 'rb').read().decode('utf-8').split('\n')
print('SESSION2 %d LF lines' % (len(s2) - 1))
def S(n, *subs):
    for s in subs:
        if s not in s2[n - 1]:
            fail('SESSION2 L%d lacks %r' % (n, s))
# Agent 8's GO lines (PROPOSAL.md rev 22:35) and the promoted copies in bench/agent8/run
GOS = {'6': 'GO W6 matrix-window6.json E50D791B6C38638F718A1AF65EB15EAF543A78AC8EA50B69DD1CC96AB7C9A0D2 only=s0,p2,p2f,p2fc repeats=5',
       '9': 'GO W9 matrix-window9.json CE0AD75792B47D59876C864B39797CD877404F911D12F92E6CC9C4351D747610 only=off,q0,q125,q250,q500 repeats=4',
       '5b': 'GO W5b matrix-window5b.json 23575AAAE9DCBB85C9965AC8A3A8794916FFA881C09C656A6512C7EE462D5F76 only=d11,d11t,d11p repeats=6',
       '4c': 'GO W4c matrix-window4c.json E2E3E4DAAF7D30C7B8B2D28D21911E6EACDA5260963F9B99095EE70C09022396 only=d0,B repeats=6'}
pb = open(P('build/agent8/w-followup/PROPOSAL.md'), 'rb').read(); prop = pb.decode('utf-8')
print('PROPOSAL %s %d B' % (sha(pb)[:8], len(pb)))
for k, g in GOS.items():
    if g not in prop:
        fail('PROPOSAL lacks GO W%s' % k)
    h = sha(open(P('bench/agent8/run/matrix-window%s.json' % k), 'rb').read())
    if h != g.split()[3]:
        fail('promoted W%s is %s' % (k, h[:8]))
if not os.path.exists(P('build/agent11/launcher-review/GO-CHECK.md')):
    fail('GO-CHECK.md missing')
S(2830, '6 arms × 3 repeats'); S(2929, 'Agent 8: promote W6 now')
S(2963, 'G4 is complete', 'w6s3'); S(2965, '**PASS, partial coverage** (to story-load')
S(2966, 'one p2fc + verify run has to reach the level, with a longer cap than 600 s'); S(2967, 'What it lacks is P2')
S(2968, 'C1 without P2 is not cleared, timing arms included,', 'until Agent 12 explains the 92 or a C1-OFF verify baseline')
S(2970, 'its GO is `only=s0,p2,p2f,p2fc`', 'stay out')
S(2972, '**W6 repeats: 5 (Agent 1).**', 'W6 has 4 arms, not 6', '44.5 min', '±2.9 % median ms')
S(2976, '**User (22:10):**'); S(2977, 'Daytime sessions: yes'); S(2978, "Agents may use the PC after tonight's last window")
S(2979, 'Best performance on AC was already set'); S(2980, 'stays in scope**, so W7 stays too')
S(2983, '**New S4 ETA: ~Wed Nov 25.** Tue evening if everything passes the first time; Thu if #19 needs a second try.')
S(2985, 'Agent 8, 22:09', 'only=s0,p2,p2f,p2fc repeats=5`. 21 runs, ~48 min; the launcher accepts it until 06:32', 'stays at -Repeats 3')
S(2990, 'first finding-10 STUCK-LOCK without verify'); S(2999, 's4bV0 (C1-OFF verify control')
S(3001, 'w6s3 PASS (logdiff NEW 0 / MORE 0), so the W6-critical set is complete')
S(3003, '**After the last window:**'); S(3006, 'Agent 12: the W6 read-out')
S(3010, '**C1 OFF**', '**same** STUCK-LOCK'); S(3012, "the 83FAF200 variant of finding 10 isn't caused by C1")
S(3014, '**s4b18 (W9) PASS:**'); S(3015, 's4b18 PASS, s4b24 WARN (finding 10)')
S(3017, 'Agent 2 starts no new build tonight', 'with CG26 (≤ -j10)')
S(3019, 's4bV0 (C1-OFF verify control) has no room before 23:10, so it is first in the post-window queue')
S(3031, "native4b's staging at ~22:55–23:10"); S(3033, 'After the windows: the re-pin rows')
S(3034, "The driver kills it at 23:40 if it isn't done", 'CTR and CG26 build after the windows (≤ -j10)')
S(3035, 'writes the pin record tonight if staging lands before ~23:40'); S(3037, 'nothing compiles during W6–W10')
S(3040, 'Agent 11 rates it SAFE to pin at 23:30 (22:31)', 'run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B, README 0058C8F6')
S(3043, 'W6 r5, then W9 r4 (if s4b17 PASSes), then W5b r6, then W4c r6')
S(3044, '**W8a4 is out of tonight.**', "move to Monday's day session, together with W8b and W10")
S(3047, 'W6 00:15–01:02, W9 01:12–01:57, W5b 02:07–02:47, W4c 02:57–03:24', 'it ends at 03:35')
S(3048, 'every window ends by 04:00', 'W6 03:00, W9 03:02, W5b 03:06, W4c 03:20', 'W4c is dropped first')
S(3049, '`--drop` for recovered hangs', 'with and without the flagged runs'); S(3051, 'fewer than 3 timed runs gets counts only')
S(3052, 'Final GO lines come by 23:45'); S(3055, '**Agent 10 (22:33, b2r row 41/§40', 'SAFE.**')
S(3058, 'All must-fixes are in'); S(3059, 'walks descendants by creation time, plus a PID + start-time check')
S(3060, 'the 3-name driver list'); S(3061, 'Start-WindowLocked checks for builds'); S(3062, '07:30 hard stop (GraceMinutes 0)')
S(3066, '**Approved for the 23:30 freeze**'); S(3067, 'I re-hash all 3 files at 23:30'); S(3068, 'No test may rewrite RUN-NIGHT.cmd after 23:25')
S(3070, 'new delta read from Agent 10'); S(3071, 'checks the W9 / W5b / W4c GO lines')
S(3074, '**Gate B (w6gB, run 20261122-222313): PASS + finding-10 WARN**')
S(3080, '**The W6 functional set is complete:** gates A and B, sides 1/2/3, s4b22, s4b23 and G3. P2 total is 0 on every W6 run.')
S(3081, '4 of 13 runs tonight (w6gA, s4b24, s4b20, w6gB), all recovered, all under the -j8 build', 'It stays a WARN')
S(3084, 'STOP smoke test at 22:34: exit 2'); S(3085, 'go 16/16, gate 13/13', 'hold 4/4, run 5/5, pin 2/2')
S(3087, 'The pins are taken at the 23:45 double-click'); S(3088, 'The day launcher changes approach')
S(3089, 'run-day.ps1, a copy of 16B90FA8 generated by make-run-day.ps1', '-StopAt is allowed and required')
S(3092, 'with hashes by ~23:35. Agents 10/11 rate it after the windows.')
S(3096, "**s4b17 (W9's third gate): PASS** (Agent 3)"); S(3097, 'devoff4b, back-off OFF', '420 s cap', '79/91 steps')
S(3098, 'No dumps, no STUCK-LOCK'); S(3099, 'logdiff vs RA: NEW 0 / MORE 0 apart from the allowed GPU-wait lines')
S(3100, 'l2_tries 21524', 'sleep_fail 0'); S(3101, 'WM_CLOSE took 40.75 s under the -j8 load, a new max but under 60 s')
S(3102, '**W9 is in tonight.**', 'W6 → W9 → W5b → W4c'); S(3103, "w6gB's 3 tags were never placed")
S(3104, 'game.log rotated at 22:23:58', "the sidecar's tail reopened at the old offset")
S(3107, 'gate B counts for W6, with a coverage note ("level load without tags")'); S(3108, "W6's timed runs are title + attract only")
S(3110, 's4bLV (p2fc + verify, cap 1800 s) must run with the fixed sidecar, show 3/3 LOADs and reach the level')
S(3112, 'W6 does not test finding 10'); S(3113, 'never runs the vpad L route')
S(3114, 'CheckSubmissionFence', 'WaitForSingleObject(fence_completion_event_, INFINITE)'); S(3116, 'render tid 0x17 holds CS 0x84959EDC')
S(3118, 'The 5 s detector needs a slow CP'); S(3119, 'Starvation as the cause is not proven, and not ruled out either')
S(3120, 'two untimed vpad L-route rows on the quiet host', 'slow_frame_log_ms=1', 'before any build restarts')
S(3121, "s4b20's set (C1 OFF)"); S(3122, "w6gB's set (p2fc)")
S(3123, 'If both are clean, finding 10 stays a load-only WARN', 'Agents 6/12 study the full-path sync')
T = datetime.datetime.now().strftime('%H:%M'); BK = 'S4-DRAFT.%s-%s.md' % (T.replace(':', ''), H0[:8])
OLD_W6 = "Agent 5's finalize, `build/agent5/w6-draft/matrix-window6.json` (E50D791B…, 21:16), has 6 arms × 3 repeats: s0; p2, p2f and p2fc; f and fc. Agent 8 promotes it once Agent 3's interim W6 rows pass; Agent 1 writes the GO only after all of Agent 3's W6 rows pass (w6s3 ~22:38) and the user has left; repeats follow Agent 7's 22:30 note (L2830, L2847-2850, L2896, L2908). Option for the user at ~23:30: Power mode Best performance before the double-click (L2789)."
NEW_W6 = "Agent 5's finalize, `build/agent5/w6-draft/matrix-window6.json` (E50D791B…, 21:16), has 6 arms (s0; p2, p2f and p2fc; f and fc) and is promoted unchanged as `bench/agent8/run/matrix-window6.json` (L2830, L2929). Its GO line (Agent 8, 22:09) runs 4 of them at repeats=5, `only=s0,p2,p2f,p2fc repeats=5`: 21 runs, ~48 min (Agent 7's formula gives ≈ 44.5 min plus the slower p2fc closes; ~±2.9 % median ms), accepted by the launcher until 06:32; RUN-WINDOW6.cmd, the double-click fallback, stays at -Repeats 3 (L2972, L2985). f and fc stay out: they are C1 without P2, which Agent 10 doesn't clear, timing arms included (L2968-2970). The W6 functional set is complete: gates A and B, sides 1-3, s4b22, s4b23 and G3, with P2 total 0 on every W6 run. Gate B counts with a coverage note, a level load without tags: the sidecar missed a game.log rotation, so none of its 3 tags was placed (L3001, L3074-3080, L3103-3107). W6 times title + attract only, so it doesn't test finding 10 (L3108, L3112-3113). Best performance on AC was already set (L2979)."
LAUNCH_ADD = " All three MUSTs are in: Stop-Tree walks descendants by creation time with a PID + start-time check, the 3-name driver list is back, Start-WindowLocked checks for builds, and the hard stop is 07:30 with GraceMinutes 0 (L3058-3062). SAFE from me (22:31) and from Agent 10 (22:33, b2r row 41/§40) on run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B and README 0058C8F6. Every test on 16B90FA8 passes (go 16/16, gate 13/13, hold 4/4, run 5/5, pin 2/2), and the RUN-NIGHT.cmd STOP smoke test at 22:34 exited 2, as expected (L3040, L3055-3064, L3084-3085). Approved for the 23:30 freeze: Agent 1 re-hashes the 3 files at 23:30, no test rewrites RUN-NIGHT.cmd after 23:25, any later change needs a new delta read from Agent 10, and the pins are taken at the 23:45 double-click (L3066-3070, L3087). The day launcher becomes run-day.ps1, a generated copy of 16B90FA8 that allows -StopAt, in `build/agent5/day-draft/` (hashes by ~23:35); Agents 10 and 11 rate it after the windows (L3088-3092)."
NEW = '\n'.join([
 "- **Since 21:47** (SESSION2 L2921-3124, read at @T@):",
 "  - **The night:** W6 r5, then W9 r4 (s4b17 passed), then W5b r6, then W4c r6; with 10-min gates 00:15-03:24 (03:35 with full runner estimates). Latest GOs, so that every window ends by 04:00: W6 03:00, W9 03:02, W5b 03:06, W4c 03:20; W4c is dropped first. W8a (native4b, after the post-window re-pin), its fallback W8a4, W8b and W10 move to Monday's day session (L3043-3048, L3102). Failed or hung runs are left out of the timing (readout.py `--drop`), every verdict is given with and without the flagged runs, and an arm with fewer than 3 timed runs gets counts only (L3049-3051). Nothing compiles during the windows; no new build starts after native4b's staging, and CTR and CG26 (≤ -j10) build after the windows (L3017, L3034, L3037).",
 "  - **GO lines** (Agent 8's `build/agent8/w-followup/PROPOSAL.md`, rev 22:35; the final ordered lines come by 23:45, L3052): W6 `E50D791B… only=s0,p2,p2f,p2fc repeats=5` (21 runs), W9 `CE0AD757… only=off,q0,q125,q250,q500 repeats=4` (21), W5b `23575AAA… only=d11,d11t,d11p repeats=6` (19), W4c `E2E3E4DA… only=d0,B repeats=6` (13). My check against the arm rules at 22:45 (L3071): all four OK, and each promoted copy in `bench/agent8/run/` matches its GO hash (`build/agent11/launcher-review/GO-CHECK.md`).",
 "  - **W9's gates:** s4b18 PASS, s4b24 a finding-10 WARN (L3014-3015), and s4b17 PASS (Agent 3, 22:41): devoff4b, back-off OFF, 79/91 steps at the 420 s cap, no dumps or STUCK-LOCK, logdiff vs RA NEW 0 / MORE 0 apart from the allowed GPU-wait lines, l2_tries 21524, sleep_fail 0, and WM_CLOSE 40.75 s under the -j8 load, a new max but under 60 s (L3096-3102).",
 "  - **Finding 10:** 4 of 13 runs tonight (w6gA, s4b24, s4b20, w6gB), all recovered and all under the -j8 build; it stays a WARN (L3081). s4b24 is the first without verify, and s4b20 had C1 OFF, so the 83FAF200 variant isn't C1's (L2990, L3010-3012). Agent 6's inferred mechanism: the CP waits on the submission fence in the memexport readback full path while render tid 0x17 holds CS 0x84959EDC; the 5 s detector needs a slow CP, from verify or from CPU starvation (L3114-3119). W6 doesn't test it. The direct test runs after the last window, before builds restart: two untimed vpad L-route rows on the quiet host, s4b20's set (C1 OFF) and w6gB's set (p2fc), with slow_frame_log_ms=1 and tags via the fixed sidecar. If both are clean, finding 10 stays a load-only WARN; if either hangs, Agents 6 and 12 study the full-path sync (L3120-3123).",
 "  - **C1 default-ON** still needs s4bLV (p2fc + verify, cap 1800 s, fixed sidecar) to show 3/3 LOADs and reach the level, which is S21 A (L2966, L3110). C1 without P2 stays uncleared until Agent 12 explains row 7's F 92 or the C1-OFF verify control s4bV0 runs, first in the post-window queue (L2967-2968, L2999, L3019).",
 "  - **The user (22:10):** daytime launcher sessions yes; the agents may use the PC after the last window; Best performance was already set; #19 stays in scope, so W7 stays (L2976-2980). New S4 ETA: ~Wed Nov 25; Tue evening if everything passes the first time, Thu if #19 needs a second try (L2983).",
])
WAIT = "- **Waiting at @T@:** the 23:30 launcher freeze; native4b's staging (expected ~22:55-23:10; the driver kills it at 23:40 if it isn't done) and Agent 4's pin record if it lands before ~23:40 (L3031-3035); Agent 8's final ordered GO lines (by 23:45); the user's double-click (~23:45); W6 from ~00:15. After the windows: the read-outs (Agent 12 for W6), the two finding-10 rows, s4bV0, s4bLV, the re-pin rows and the CG26/CTR builds (L3003-3007, L3033)."
UPD = "- Updated at @T@: the header; Changed since 15:54 (the W6 and launcher items, a \"Since 21:47\" item and Waiting); Still open (Agent 5's launcher); the W6 row; §4b (a 21:55-22:44 entry and Possible changes)."
OPEN_ADD = " At @T@: SAFE from Agents 10 and 11 on run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B and README 0058C8F6, the STOP smoke test seen (exit 2), approved for the 23:30 freeze (SESSION2 L3054-3070, L3084); closed for tonight. The day-launcher files (`build/agent5/day-draft/`) are rated after the windows (L3092)."
OLD_ROW = "As finalized at 21:16: devoff4b, no timer bundle, 6 arms × 3 (s0; p2, p2f, p2fc; f, fc); the GO by Agent 1 after all of Agent 3's W6 rows pass and the user has left (L2830, L2847-2850, L2896, L2908) | s0 / #8 / #8 + #5 / #8 + #5 + #4 (C1 ON, verify off). The #8 + #5 arm times C1 with fix (i) ON in both arms (a12 S4.12 step 7; A10, §25) | 1 + 4 × 3 = 13 | ~33 |"
NEW_ROW = "As run tonight: devoff4b, no timer bundle, `bench/agent8/run/matrix-window6.json` (E50D791B…) with the GO `only=s0,p2,p2f,p2fc repeats=5` (f and fc, C1 without P2, stay out); first of the night, latest GO 03:00; the functional set is complete (L2968-2972, L2985, L3048, L3080) | s0 / #8 / #8 + #5 / #8 + #5 + #4 (C1 ON, verify off). The #8 + #5 arm times C1 with fix (i) ON in both arms (a12 S4.12 step 7; A10, §25) | 1 + 4 × 5 = 21 | ~48 |"
E4B = "- **21:55-22:44 (L2921-3124):** W6 promoted, its GO 4 arms × 5 (`only=s0,p2,p2f,p2fc`; C1 without P2 isn't cleared, so f and fc stay out); the W6 functional set complete (G4, G5 partial, w6s3, gate B without tags); s4b17 and s4b18 PASS, so W9 runs; the night W6 → W9 → W5b → W4c, latest GOs 03:00-03:20, with W8a, W8a4, W8b and W10 on Monday; finding 10 in 4 of 13 runs, all under the -j8 build, a WARN and not C1's, with a direct test after the last window; no build after native4b's staging; the user's 22:10 decisions and the ETA ~Wed Nov 25; the launcher SAFE from both reviewers and approved for the 23:30 freeze; my GO-line check OK (Changed since 15:54)."
OLD_NEXT = "Next: Agent 8's formal read-outs, Agent 3's W6 rows, native4b and Agent 4's re-pin, the W6 promotion and GO, and Agent 5's final launcher."
NEW_NEXT = "Since 21:47: the W6 GO line and functional set, s4b17's PASS, the night order W6 → W9 → W5b → W4c, finding 10's direct test, and the launcher's SAFE and freeze (Changed since 15:54). Next: the windows, Agent 8's and Agent 12's read-outs, the post-window rows (finding 10's two L-route rows, s4bV0, s4bLV and the re-pin) and Monday's day session (W8a, W8b, W10)."
new = old
def sub(name, o, n):
    global new
    c = new.count(o)
    if c != 1:
        fail('sub %s matches %d' % (name, c)); return
    new = new.replace(o, n); print('sub', name)
def line(name, prefix, fn):
    global new
    L = new.split('\n'); ix = [i for i, l in enumerate(L) if l.startswith(prefix)]
    if len(ix) != 1:
        fail('line %s matches %d' % (name, len(ix))); return
    L[ix[0]] = fn(L[ix[0]]); new = '\n'.join(L); print('line', name, 'L%d' % (ix[0] + 1))
sub('D3', 'then at 19:37, 20:07 and 21:47 under task #10', 'then at 19:37, 20:07, 21:47 and @T@ under task #10')
sub('D7', "19:37, 20:07 and 21:47; the 15:54 version is kept in `build/agent11/s4draft/S4-DRAFT.1937-14C2A482.md`, the 19:37 one in `build/agent11/s4draft/S4-DRAFT.2007-0CB74A52.md` and the 20:07 one in `build/agent11/s4draft/S4-DRAFT.2147-0C93A609.md`):",
    "19:37, 20:07, 21:47 and @T@; the 15:54 version is kept in `build/agent11/s4draft/S4-DRAFT.1937-14C2A482.md`, the 19:37 one in `build/agent11/s4draft/S4-DRAFT.2007-0CB74A52.md`, the 20:07 one in `build/agent11/s4draft/S4-DRAFT.2147-0C93A609.md` and the 21:47 one in `build/agent11/s4draft/@BK@`):")
sub('W6 item', OLD_W6, NEW_W6)
line('launcher', "  - **Agent 5's launcher:** F1's 11 env keys", lambda l: l + LAUNCH_ADD)
line('wait', '- **Waiting at 21:47:** ', lambda l: NEW + '\n' + WAIT)
line('upd', '- Updated at 21:47: the header;', lambda l: UPD + '\n' + l)
line('open', "- **Agent 5's launcher** (`bench/agent5/launch/RUN-NIGHT.cmd`;", lambda l: l + OPEN_ADD)
sub('W6 row', OLD_ROW, NEW_ROW)
line('4b', '- **20:30-21:33 (L2779-2919):**', lambda l: l + '\n' + E4B)
sub('next', OLD_NEXT, NEW_NEXT)
# 22:55 additions: Agent 6's 22:52 message (finding-10 mechanism, quiet host, after-S4 candidate)
S(2927, '1244 memexport syncs, against 5-62 normally'); S(3124, 'memexport readback full-path sync')
S(3119, 'All 3 hangs Agent 6 analysed happened under the -j8 build')
if not os.path.exists(P('build/agent6/hang/cp-state-s4b24-s4b20.md')):
    fail('cp-state-s4b24-s4b20.md missing')
sub('N4 quiet', "from verify or from CPU starvation (L3114-3119). W6 doesn't test it.",
    "from verify or from CPU starvation (L3114-3119); it hasn't been seen on a quiet host (Agent 6, `build/agent6/hang/cp-state-s4b24-s4b20.md`). W6 doesn't test it.")
sub('UPD f10', '§4b (a 21:55-22:44 entry and Possible changes).', '§4b (a 21:55-22:44 entry and Possible changes); §5 (finding 10).')
F10_ADD = " Tonight: 4 of 13 functional runs, all recovered and all under the -j8 build, including s4b20 with C1 and verify off; Agent 6's inferred mechanism is the memexport readback full-path sync (`build/agent6/hang/cp-state-s4b24-s4b20.md`), and it hasn't been seen on a quiet host. The direct test is two untimed vpad L-route rows on the quiet host after the last window (SESSION2 L3081, L3112-3123; Changed since 15:54). A later perf candidate, after S4: that full-path sync. Its fast path skips the sync only when the other slot's submission has finished, so with the GPU behind nearly every memexport draw takes the full path (gate A's 9.7 s frame logged 1244 syncs, against 5-62 normally). It isn't measured at normal speed yet; the quiet-host rows (slow_frame_log_ms=1) will give the counts (L2927, L3124; Agent 6, 22:52)."
line('f10', '- **The stuck game lock (finding 10):** v0.2.0 hits it too', lambda l: l + F10_ADD)
for tok, val in (('@T@', T), ('@BK@', BK)):
    if tok in old:
        fail('token %s in draft' % tok)
    new = new.replace(tok, val)
def bad_rows(t):
    out, L, i = set(), t.split('\n'), 0
    while i < len(L):
        if L[i].startswith('|'):
            h, j = L[i].count('|'), i
            while j < len(L) and L[j].startswith('|'):
                if L[j].count('|') != h: out.add(L[j])
                j += 1
            i = j
        else:
            i += 1
    return out
if bad_rows(new) - bad_rows(old):
    fail('table pipe counts changed')
nb = new.encode('utf-8')
if b'\r' in nb or '@T@' in new or '@BK@' in new:
    fail('CR or token left')
print('new %d B, %d LF (+%d)' % (len(nb), nb.count(b'\n'), nb.count(b'\n') - raw.count(b'\n')))
if nb.count(b'\n') != 528:
    fail('expected 528 LF')
ol, nl = old.split('\n'), new.split('\n'); dry = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ol, b=nl, autojunk=False).get_opcodes():
    if tag != 'equal':
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- %d: %s' % (i + 1, ol[i]) for i in range(i1, i2)] + ['+++ %d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]
        print(dry[-1 - (i2 - i1) - (j2 - j1)])
if DRY:
    open(P('build/agent11/s4draft/run13-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk) or sha(open(DRAFT, 'rb').read()) != H0:
    sys.exit('backup exists or draft changed')
open(bk, 'wb').write(raw)
open(DRAFT, 'wb').write(nb); chk = open(DRAFT, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), BK))
