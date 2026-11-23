# -*- coding: utf-8 -*-
# fnd3.py - FINDINGS-AND-CHANGES.md: the user's 23:16-23:24 answers to Q3, Q4 and Q5 (Agent 1's 23:25 request to Agent 11).
# Usage: python fnd3.py --dry | --apply. One-match edits, sha + line gates, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
DOC, HOLD = P('perf-notes/FINDINGS-AND-CHANGES.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: fnd3.py --dry | --apply')
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
fails = []
def fail(m):
    fails.append(m); print('FAIL:', m)
if os.path.exists(HOLD):
    sys.exit('HOLD exists: stop')
raw = open(DOC, 'rb').read(); H0 = sha(raw)
print('findings %s %d B %d LF' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('9799EABB') or raw.count(b'\n') != 367 or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('findings gate FAIL')
old = raw.decode('utf-8')
s2 = open(P('perf-notes/SESSION2.md'), 'rb').read().decode('utf-8').split('\n')
print('SESSION2 %d split lines' % len(s2))
def S(n, *subs):
    for s in subs:
        if n > len(s2) or s not in s2[n - 1]:
            fail('SESSION2 L%d lacks %r' % (n, s))
S(3172, 'the user is available all day')
S(3173, '**Defender exclusion: added**', 'MsMpEng was at 0% over 5 s at 23:17')
S(3174, "Tonight's windows run with the exclusion", 'Comparisons inside a window are unaffected; comparisons with W4b/W5 and older windows get a caveat')
S(3176, 'the user thinks it was already off', 'NVIDIA Overlay x5, nvsphelper64 and PresentMonService were running, all at 0% CPU with no game running', 'PresentMon used ~1 core during game runs')
S(3177, 'Turning it off is optional and up to the user', "it's the same for every arm tonight")
S(3196, '**#33 pop-in: YES, as an optional feature** (opt-in, off by default). #33 and #34 stay in scope.',
  "They need Agent 6's implementation, Agent 10's rating, a build, and the user's look at the pop-in on a visible desktop.")
S(3197, '**Monday: the laptop can sit untouched**', 'day sessions run through RUN-DAY once the day draft is rated and installed in bench\\agent5\\day\\')
S(3198, '**#1 screenshot check: Monday**', "when the user messages that they're free for an hour", 'Stage the kit in the morning',
  'If #33 is built and rated by then, do the pop-in look in the same hour')
S(3199, 'Before that hour starts, no timed window may be running: let it finish, or stop it cleanly.')
Q3A = (" **Answered 23:16:** you added a Defender exclusion for the build folder (~23:16; Defender was at 0 % over 5 s at 23:17), so tonight's "
       "windows run with it. Comparisons inside a window are unaffected; comparisons with windows 4b and 5 and older ones get a caveat. You believe "
       "the NVIDIA overlay was already off. At 23:17 the overlay's processes and PresentMonService were running at 0 % CPU with no game running "
       "(PresentMon used about one core during earlier game runs). Turning it off stays optional and up to you: whatever its state at the "
       "double-click, it's the same for every arm tonight.")
Q4A = (" **Answered 23:24: yes, on Monday,** in a one-hour slot once you message that you're free. The agents stage the kit in the morning, and no "
       "timed window may be running when the hour starts (it finishes first, or is stopped cleanly). If the pop-in mode (question 5) is built and "
       "rated by then, you look at the pop-in in the same hour. On Monday you're available all day and the laptop can sit untouched, so the "
       "daytime windows run through the day launcher (RUN-DAY) once it's rated and installed.")
Q5A = (" **Answered 23:24: yes,** as an optional mode that's off by default, so the item (#33) and its companion (#34) stay in S4's scope. They "
       "still need Agent 6's implementation, Agent 10's rating, a build, and your look at the pop-in on a visible desktop.")
new = old
def sub(name, o, n):
    global new
    c = new.count(o)
    if c != 1:
        fail('sub %s matches %d' % (name, c)); return
    new = new.replace(o, n); print('sub', name)
sub('q3', 'Window 4 keeps both as they are, so that it matches window 3. Until you answer, nobody touches either.',
    'Window 4 keeps both as they are, so that it matches window 3. Until you answer, nobody touches either.' + Q3A)
sub('q4', 'Until then, the native option for S4 is the stopgap that only remembers the miss, which changes nothing visible.',
    'Until then, the native option for S4 is the stopgap that only remembers the miss, which changes nothing visible.' + Q4A)
sub('q5', 'If not, that item and its companion are dropped from S4.', 'If not, that item and its companion are dropped from S4.' + Q5A)
nb = new.encode('utf-8')
if b'\r' in nb:
    fail('CR')
print('new %d B, %d LF (+%d)' % (len(nb), nb.count(b'\n'), nb.count(b'\n') - raw.count(b'\n')))
if nb.count(b'\n') != 367:
    fail('expected 367 LF')
ol, nl = old.split('\n'), new.split('\n'); dry = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ol, b=nl, autojunk=False).get_opcodes():
    if tag != 'equal':
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- %d: %s' % (i + 1, ol[i]) for i in range(i1, i2)] + ['+++ %d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]
        print(dry[-1 - (i2 - i1) - (j2 - j1)])
if DRY:
    open(P('build/agent11/s4draft/fnd3-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
T = datetime.datetime.now().strftime('%H%M'); bk = P('build/agent11/s4draft/FINDINGS-AND-CHANGES.%s-%s.md' % (T, H0[:8]))
if os.path.exists(bk) or sha(open(DOC, 'rb').read()) != H0:
    sys.exit('backup exists or findings changed')
open(bk, 'wb').write(raw)
open(DOC, 'wb').write(nb); chk = open(DOC, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), os.path.basename(bk)))
