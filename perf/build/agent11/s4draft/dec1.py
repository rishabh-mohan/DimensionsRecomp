# -*- coding: utf-8 -*-
# dec1.py - record decision 1 (Toy Pad tags = yes, the user, 17:27) in S4-DRAFT §4a item 1 and
# FINDINGS-AND-CHANGES.md Q1 (task #10 after the 17:27 relaunch = old #35, Agent 11).
# Usage: python build\agent11\s4draft\dec1.py --dry | --apply
# --dry writes nothing. --apply takes hashed backups first, then writes both files (LF, no BOM).
import datetime
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'


def P(rel):
    return os.path.join(ROOT, *rel.split('/'))


HOLD = P('perf-notes/WINDOW-HOLD.txt')
DRY = '--dry' in sys.argv
APPLY = '--apply' in sys.argv
if DRY == APPLY:
    print('usage: dec1.py --dry | --apply')
    sys.exit(2)
fails = []


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def fail(m):
    fails.append(m)
    print('FAIL:', m)


def die(m):
    print('FAIL:', m)
    sys.exit(1)


if os.path.exists(HOLD):
    die('perf-notes/WINDOW-HOLD.txt exists: stop')

# ---------------------------------------------------------------- source check
s2 = open(P('perf-notes/SESSION2.md'), 'rb').read().decode('utf-8').split('\n')
L = s2[2654 - 1]
for s in ['**Decision 1 (Toy Pad tags): yes** (user, 17:27)', 'Batman, Gandalf, Wyldstyle',
          'under the 02:11 harness-only rules (user-mode only, no drivers or system-wide installs, never in a staged `build/agent2/*-bin`, saves isolated in the run folder, builds at <= 2 threads)',
          'S4b queue rows 7, 20 and 23 (level loads) are no longer skipped',
          "C1 ON's verify-mode level load (b2r §21 A) can run",
          'Agent 11 records it in S4-DRAFT §4a and FINDINGS Q1']:
    if s not in L:
        fail('SESSION2 L2654 lacks %r' % s)
if not s2[2647 - 1].startswith('## 17:36 Agent 1: resumed after the agy-grid relaunch'):
    fail('SESSION2 L2647 heading')

RULES = ('user-mode only, no drivers or system-wide installs, never in a staged `build/agent2/*-bin`, '
         'saves isolated in the run folder, builds at ≤ 2 threads')

FILES = [
    ('perf-notes/S4-DRAFT.md', '14C2A482', 476, 'build/agent11/s4draft/S4-DRAFT', [
        ('4a item 1 head',
         '1. **Toy Pad tags** (F Q1). May Agent 3 use generated virtual Toy Pad tags (Batman, Gandalf, Wyldstyle) in its hidden-desktop test runs?',
         '1. **Toy Pad tags** (F Q1): **answered yes** (the user, 17:27; SESSION2 L2654). May Agent 3 use generated virtual Toy Pad tags (Batman, Gandalf, Wyldstyle) in its hidden-desktop test runs?'),
        ('4a item 1 answer',
         '   - Until you answer: no.\n2. **simde** (F Q2).',
         '   - **Answer (the user, 17:27): yes.** Agent 3 may use them in its hidden-desktop test runs under the 02:11 harness-only rules: '
         + RULES + ' (SESSION2 L2654). So the S4b queue\'s level-load rows 7, 20 and 23 are no longer skipped, '
         "C1 ON's verify-mode level load (b2r §21 A) can run, and so can fix (i) ON's level load (§2b step 3). "
         'Until 17:27 the default was no.\n2. **simde** (F Q2).'),
        ('decisions item 3',
         '3. **The user questions in §4a:** Toy Pad tags, simde,',
         '3. **The user questions in §4a:** Toy Pad tags (**answered yes**, the user, 17:27), simde,'),
        ('2b fix (i) level load',
         'title, menu walk and one level load (the level load needs §4a Q1);',
         'title, menu walk and one level load (the level load needed §4a Q1: answered yes, 17:27);'),
        ('row 4 level load',
         'A level load needs Toy Pad figures or the user |',
         "A level load needs Toy Pad figures or the user (generated virtual tags are allowed in Agent 3's runs since 17:27, §4a Q1) |"),
        ('row 24 until Q1',
         'menus + attract only until §4a Q1:',
         'menus + attract only until §4a Q1 (answered yes, 17:27):'),
    ]),
    ('perf-notes/FINDINGS-AND-CHANGES.md', 'A0B7ABAA', 365, 'build/agent11/a11-backups/FINDINGS-AND-CHANGES', [
        ('Q1',
         'With them, the B check can also cover the pause menu and a level change. Saves stay in the run folder. Until you answer: no.',
         'With them, the B check can also cover the pause menu and a level change. Saves stay in the run folder. '
         '**Answered 17:27: yes.** Agent 3 may use them in its hidden-desktop test runs under the rules set at 02:11 for its '
         'test harness: user mode only, no drivers or system-wide installs, never inside a staged build folder '
         '(`build/agent2/*-bin`), saves kept in the run folder, and builds at 2 threads or fewer. So the three level-load '
         "runs in the S4b check queue (rows 7, 20 and 23) are back in, and the re-upload fix C1's verify-mode level load, "
         'which C1 needs before it can ever be turned on, can now run.'),
        ('leads C1 level',
         'a menu walk and a level load (a level needs Toy Pad figures or you at the controls);',
         'a menu walk and a level load (a level needs Toy Pad figures or you at the controls; since 17:27, generated tags are allowed in Agent 3\'s runs, question 1);'),
    ]),
]

T = datetime.datetime.now().strftime('%H%M')
out = []
for rel, h8, nlines, bkbase, subs in FILES:
    raw = open(P(rel), 'rb').read()
    h0 = sha(raw)
    print('%s %s… %d B, %d lines' % (rel, h0[:8], len(raw), raw.count(b'\n')))
    if not h0.startswith(h8):
        fail('%s is not %s' % (rel, h8))
        continue
    if raw.count(b'\n') != nlines:
        fail('%s line count' % rel)
    if b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
        fail('%s CR/BOM' % rel)
    old = raw.decode('utf-8')
    new = old
    for name, o, n in subs:
        c = new.count(o)
        if c != 1:
            fail('%s: sub %r matches %d times' % (rel, name, c))
            continue
        ln = new[:new.index(o)].count('\n') + 1
        new = new.replace(o, n)
        print('  sub %-22s at L%d' % (name, ln))
    nb = new.encode('utf-8')
    if b'\r' in nb or nb.startswith(b'\xef\xbb\xbf'):
        fail('%s: new text CR/BOM' % rel)
    if nb.count(b'\n') != nlines:
        fail('%s: new line count %d' % (rel, nb.count(b'\n')))
    print('  new %d B, %d lines' % (len(nb), nb.count(b'\n')))
    # leftover scan
    for i, l in enumerate(new.split('\n')):
        if any(k in l for k in ['Toy Pad', 'Toypad', 'level load', 'Q1']):
            p = max(l.find('Toy Pad'), l.find('level load'), l.find('Q1'))
            print('  scan L%d: …%s…' % (i + 1, l[max(0, p - 110):p + 110]))
    out.append((rel, raw, h0, nb, '%s.%s-%s.md' % (bkbase, T, h0[:8])))

if DRY:
    print('DRY RUN: %d failures; nothing written' % len(fails))
    sys.exit(1 if fails else 0)
if fails:
    die('%d failures; nothing written' % len(fails))
if os.path.exists(HOLD):
    die('perf-notes/WINDOW-HOLD.txt exists: stop')
for rel, raw, h0, nb, bk in out:
    if os.path.exists(P(bk)):
        die('backup exists: ' + bk)
    open(P(bk), 'wb').write(raw)
    if sha(open(P(bk), 'rb').read()) != h0:
        die('backup hash mismatch: ' + bk)
    if sha(open(P(rel), 'rb').read()) != h0:
        die('%s changed during the run' % rel)
    open(P(rel), 'wb').write(nb)
    chk = open(P(rel), 'rb').read()
    print('WROTE %s sha256 %s, %d B, %d lines, CR %d, BOM %s; backup %s' % (
        rel, sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), chk.startswith(b'\xef\xbb\xbf'), bk))
