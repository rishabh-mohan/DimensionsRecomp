# -*- coding: utf-8 -*-
# run16.py - S4-DRAFT: the user's 23:16-23:24 answers (Agent 1's 23:25 request to Agent 11): SESSION2 L3171-3199.
# Usage: python run16.py --dry | --apply. One-match edits, sha + line gates, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
DRAFT, HOLD = P('perf-notes/S4-DRAFT.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: run16.py --dry | --apply')
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
fails = []
def fail(m):
    fails.append(m); print('FAIL:', m)
if os.path.exists(HOLD):
    sys.exit('HOLD exists: stop')
raw = open(DRAFT, 'rb').read(); H0 = sha(raw)
print('draft %s %d B %d LF' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('A95013AC') or raw.count(b'\n') != 530 or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('draft gate FAIL')
old = raw.decode('utf-8')
s2 = open(P('perf-notes/SESSION2.md'), 'rb').read().decode('utf-8').split('\n')
print('SESSION2 %d split lines' % len(s2))
def S(n, *subs):
    for s in subs:
        if n > len(s2) or s not in s2[n - 1]:
            fail('SESSION2 L%d lacks %r' % (n, s))
S(3171, '### 23:18 - Agent 1: user answers (23:16)')
S(3172, 'the user is available all day')
S(3173, '**Defender exclusion: added**', 'MsMpEng was at 0% over 5 s at 23:17')
S(3174, "Tonight's windows run with the exclusion", 'Comparisons inside a window are unaffected; comparisons with W4b/W5 and older windows get a caveat')
S(3176, 'the user thinks it was already off', 'NVIDIA Overlay x5, nvsphelper64 and PresentMonService were running, all at 0% CPU with no game running', 'PresentMon used ~1 core during game runs')
S(3177, 'Turning it off is optional and up to the user', "it's the same for every arm tonight")
S(3181, '#19 Agent 6 done', 'expect-w9', 'expect-w5b', 'expect-w4c')
S(3184, 'Day draft: run-day.ps1 D86F6DE0, launcher-ctl.ps1 6DDE3150', "The line in force is Agent 8's final one in build/agent1/night/GO-W6.txt (repeats=5, 21 runs")
S(3186, '### 23:25 - Agent 1: launcher FROZEN; user answers (23:24)')
S(3187, 'Freeze check at 23:24:43')
S(3189, 'All 3 files MATCH: run-night.ps1 16B90FA8', 'RUN-NIGHT.cmd D7A0362B', 'README.md 0058C8F6')
S(3192, 'GO files ready: W6 (repeats=5), W9 (4), W5b (6), W4c (6)')
S(3194, '**The set is frozen.**')
S(3196, '**#33 pop-in: YES, as an optional feature** (opt-in, off by default). #33 and #34 stay in scope.',
  "They need Agent 6's implementation, Agent 10's rating, a build, and the user's look at the pop-in on a visible desktop.")
S(3197, '**Monday: the laptop can sit untouched**', 'day sessions run through RUN-DAY once the day draft is rated and installed in bench\\agent5\\day\\')
S(3198, '**#1 screenshot check: Monday**', "when the user messages that they're free for an hour", 'Stage the kit in the morning',
  'If #33 is built and rated by then, do the pop-in look in the same hour')
S(3199, 'Before that hour starts, no timed window may be running: let it finish, or stop it cleanly.')
# The final GO files must equal the lines checked in GO-CHECK.md (22:45), and the promoted matrices must match their hashes.
GO = {'W6': ('matrix-window6.json', 'E50D791B6C38638F718A1AF65EB15EAF543A78AC8EA50B69DD1CC96AB7C9A0D2', 'only=s0,p2,p2f,p2fc repeats=5'),
      'W9': ('matrix-window9.json', 'CE0AD75792B47D59876C864B39797CD877404F911D12F92E6CC9C4351D747610', 'only=off,q0,q125,q250,q500 repeats=4'),
      'W5b': ('matrix-window5b.json', '23575AAAE9DCBB85C9965AC8A3A8794916FFA881C09C656A6512C7EE462D5F76', 'only=d11,d11t,d11p repeats=6'),
      'W4c': ('matrix-window4c.json', 'E2E3E4DAAF7D30C7B8B2D28D21911E6EACDA5260963F9B99095EE70C09022396', 'only=d0,B repeats=6')}
for w, (js, h, rest) in GO.items():
    got = open(P('build/agent1/night/GO-%s.txt' % w), 'rb').read().decode('utf-8').strip()
    if got != 'GO %s %s %s %s' % (w, js, h, rest):
        fail('GO-%s.txt differs: %r' % (w, got))
    if sha(open(P('bench/agent8/run/' + js), 'rb').read()) != h:
        fail('bench/agent8/run/%s hash differs' % js)
print('GO files checked: %d' % len(GO))
T = datetime.datetime.now().strftime('%H:%M'); BK = 'S4-DRAFT.%s-%s.md' % (T.replace(':', ''), H0[:8])
USER = ("  - **The user (23:16-23:24, L3171-3199):** §4a Q3, Q4 and Q5 are answered (see §4a). Monday: the user is available all day and the laptop "
        "can sit untouched, so the day sessions (W8a, W8b, W10) run through RUN-DAY once Agents 10 and 11 have rated the day draft and Agent 5 has "
        "installed it in `bench/agent5/day/` (L3172, L3197). The launcher set froze at 23:24:43 with all 3 files matching (run-night.ps1 16B90FA8, "
        "RUN-NIGHT.cmd D7A0362B, README 0058C8F6); the GO files in `build/agent1/night/` (W6 r5, W9 r4, W5b r6, W4c r6) equal the lines in my "
        "GO-CHECK, and the promoted matrices still match them; Agent 6's expect files for W9, W5b and W4c are staged (L3181, L3184, L3187-3194).")
Q3A = ("   - **Answer (the user, 23:16; SESSION2 L3173-3177):** a Defender exclusion for the build folder was added at ~23:16 (MsMpEng at 0 % over 5 s "
       "at 23:17), so tonight's windows run with it. Comparisons inside a window are unaffected; comparisons with W4b, W5 and older windows get a "
       "caveat. The user believes the NVIDIA overlay was already off; at 23:17 NVIDIA Overlay ×5, nvsphelper64 and PresentMonService ran at 0 % CPU "
       "with no game running (PresentMon used ~1 core during earlier game runs). Turning it off stays optional and up to the user; whatever its state "
       "at the double-click, it's the same for every arm tonight.")
Q4A = ("   - **Answer (the user, 23:24; L3198-3199): yes, on Monday,** in a one-hour slot when the user messages that they're free. The kit is staged in "
       "the morning; no timed window may be running when the hour starts (let it finish, or stop it cleanly); if #33 is built and rated by then, the "
       "pop-in look happens in the same hour.")
Q5A = ("   - **Answer (the user, 23:24; L3196): yes,** as an opt-in that's off by default, so #33 and #34 stay in scope. They need Agent 6's "
       "implementation, Agent 10's rating, a build, and the user's look at the pop-in on a visible desktop.")
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
def row33(l):
    o, n = "| the user's answer | proposed |", "| the user's answer: **yes**, opt-in and off by default (23:24) | proposed |"
    if l.count(o) != 1:
        fail('row33 cell matches %d' % l.count(o)); return l
    return l.replace(o, n)
sub('D3', 'the old board-run-2 #35; see "Changed since 15:54").', 'the old board-run-2 #35; see "Changed since 15:54"), and at @T@ with the user\'s 23:16-23:24 answers (Agent 1, 23:25).')
sub('D7a', '19:37, 20:07, 21:47 and 22:55-23:02; the 15:54 version', '19:37, 20:07, 21:47, 22:55-23:02 and @T@; the 15:54 version')
sub('D7b', " and the 22:55 one in `build/agent11/s4draft/S4-DRAFT.2302-F25F4E1E.md`):",
    ", the 22:55 one in `build/agent11/s4draft/S4-DRAFT.2302-F25F4E1E.md` and the 23:02 one in `build/agent11/s4draft/@BK@`):")
sub('since', '- **Since 21:47** (SESSION2 L2921-3169, read at 22:55 and 23:02):', '- **Since 21:47** (SESSION2 L2921-3199, read at 22:55, 23:02 and @T@):')
line('user', '  - **native4b (22:57-23:00, L3143-3163):**', lambda l: l + '\n' + USER)
sub('wait', '- **Waiting at 23:02:** the 23:30 launcher freeze; native4b', '- **Waiting at @T@:** native4b')
sub('wait2', "Agent 8's final ordered GO lines and Agent 6's expect files for W9, W5b and W4c (both by 23:45, L3141); Agent 5's day-draft hashes (by 23:35, L3168); the user's double-click (~23:45);",
    "the user's double-click (~23:45; the launcher froze at 23:24:43, and the GO files, Agent 6's expect files and Agent 5's day-draft hashes are in, L3181-3194);")
sub('upd', '- Updated at 22:55 and 23:02 (SESSION2 to L3169): the header;', '- Updated at 22:55, 23:02 and @T@ (SESSION2 to L3199): the header;')
sub('upd2', '§4b (a 21:55-23:01 entry and Possible changes); §5 (finding 10).',
    "§4b (a 21:55-23:25 entry and Possible changes); §5 (finding 10). At @T@ also: Decisions item 3, §4a Q3-Q5, row 33 and the two Q3/Q4 cross-references (the user's answers).")
sub('4b head', '- **21:55-23:01 (L2921-3169):**', '- **21:55-23:25 (L2921-3199):**')
sub('4b tail', "Agent 3's queue stopped at 22:56, with its morning queue (Changed since 15:54).",
    "Agent 3's queue stopped at 22:56, with its morning queue; the launcher frozen at 23:24:43; the user's 23:16-23:24 answers to §4a Q3-Q5 and Monday's RUN-DAY sessions (Changed since 15:54).")
sub('next', "native4b's map check and PSO cache, and the launcher's SAFE and freeze (Changed since 15:54).",
    "native4b's map check and PSO cache, the launcher's SAFE and freeze, and the user's answers to §4a Q3-Q5 (Changed since 15:54).")
sub('dec3', 'Toy Pad tags (**answered yes**, the user, 17:27), simde, Defender/PresentMon, the native screenshot check and no-wait pop-in.',
    'Toy Pad tags (**answered yes**, the user, 17:27), simde (open), Defender/PresentMon (**answered**, 23:16: the exclusion is in; the overlay is believed off), the native screenshot check (**yes, Monday**, 23:24) and no-wait pop-in (**yes, opt-in and off by default**, 23:24).')
line('q3', '   - Until you answer, nobody touches either.', lambda l: l + '\n' + Q3A)
line('q4', '   - Until then, the native option is the miss cache (#2), which changes nothing visible.', lambda l: l + '\n' + Q4A)
line('q5', '   - If not, #33 and #34 are dropped.', lambda l: l + '\n' + Q5A)
line('row33', "| 33 | **Don't wait for pipelines**", row33)
sub('xq4', 'b2r §15.1 items 1-5 and §4a Q4 first.', 'b2r §15.1 items 1-5 and §4a Q4 first (answered at 23:24: the check is on Monday).')
sub('xq3', 'It needs a quiet machine, so it depends on §4a Q3;', 'It needs a quiet machine, so it depends on §4a Q3 (answered at 23:16: the Defender exclusion is in);')
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
if nb.count(b'\n') != 534:
    fail('expected 534 LF')
ol, nl = old.split('\n'), new.split('\n'); dry = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ol, b=nl, autojunk=False).get_opcodes():
    if tag != 'equal':
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- %d: %s' % (i + 1, ol[i]) for i in range(i1, i2)] + ['+++ %d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]
        print(dry[-1 - (i2 - i1) - (j2 - j1)])
if DRY:
    open(P('build/agent11/s4draft/run16-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk) or sha(open(DRAFT, 'rb').read()) != H0:
    sys.exit('backup exists or draft changed')
open(bk, 'wb').write(raw)
open(DRAFT, 'wb').write(nb); chk = open(DRAFT, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), BK))
