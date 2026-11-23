# rfinal3.py - perf-notes/RESUME.md delta after Agent 10's final review (Agent 11, task #25):
# NIT F1 (build/agent10/t27/resume-review.md B3AE5716..., "Final version"): the 07:33:42 refusal was the
# installer's process check matching pid 33304 (N-4, fail-safe), not a running launcher.
# Dry run by default (writes rfinal3-diff.txt only); --apply --t=HH:MM writes the doc after a hashed backup.
# Gate: sha 9DA0A4C3..., 381 LF, no CR, no BOM. Every op is keyed to a line number and needs its old
# text exactly once in that line. No line is added or removed, so every line cite stays valid.
import datetime
import difflib
import hashlib
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
P = 'perf-notes/RESUME.md'
EXP = '9DA0A4C372399DC4877D26EFBE908736911D5BBD4B4B9621EF244DA479193665'
NLF = 381
OUTDIR = 'build/agent11/resume'
APPLY = '--apply' in sys.argv
T = None
for a in sys.argv[1:]:
    if a.startswith('--t='):
        T = a[4:]
if APPLY and not T:
    print('ABORT: --apply needs --t=HH:MM')
    sys.exit(1)
if not T:
    T = datetime.datetime.now().strftime('%H:%M')

raw = open(P, 'rb').read()
sha = hashlib.sha256(raw).hexdigest().upper()
fails = []
if sha != EXP:
    fails.append('GATE sha ' + sha)
if raw.count(b'\r'):
    fails.append('GATE CR')
if raw.startswith(b'\xef\xbb\xbf'):
    fails.append('GATE BOM')
if raw.count(b'\n') != NLF:
    fails.append('GATE LF %d' % raw.count(b'\n'))
if fails:
    print('ABORT', fails)
    sys.exit(1)
print('GATE OK', sha[:8], len(raw), 'B,', NLF, 'LF')
lines = raw.decode('utf-8').split('\n')
assert lines[-1] == '' and len(lines) == NLF + 1

OPS = []


def sub(n, old, new):
    OPS.append((n, old, new))


sub(5, "This is the final version (Nov 23, 08:09; updated at 08:18 for #19's rate request).",
    "This is the final version (Nov 23, 08:09; updated at 08:18 for #19's rate request and at {T} for Agent 10's review).")

sub(325, "The installer refused at 06:36 and at 07:33:41, while a launcher process was still running, as designed.",
    "The installer refused at 06:36, while the night launcher was still waiting for GO, as designed, and at 07:33:42, when its process check matched pid 33304, not the launcher, which had ended at 07:30:14 (Agent 10's N-4 in `build/agent10/t27/scrnsave-delta.md`: the check matches any PowerShell whose command line names run-night.ps1 or run-day.ps1, so it fails safe; just run it again).")

out = lines[:]
for n, old, nw in OPS:
    l = out[n - 1]
    c = l.count(old)
    if c != 1:
        fails.append('OP L%d count %d: %r' % (n, c, old[:70]))
        continue
    out[n - 1] = l.replace(old, nw)
new = '\n'.join(out)
new = new.replace('{T}', T)
nb = new.encode('utf-8')

# ---- checks
if '{T}' in new:
    fails.append('PLACEHOLDER left')
if '\r' in new or new.startswith('\ufeff'):
    fails.append('CR/BOM in output')
pers = re.findall(r'<user>|rishabh', new, re.I)
pub = re.findall(r'github|https?://|file:///|[A-Za-z]:\\|\\Users\\|/Users/', new, re.I)
if pers:
    fails.append('PERSONAL %d' % len(pers))
if pub:
    fails.append('PUBLIC %r' % pub[:5])
stale = ['07:33:41, while a launcher process', 'refused at 06:36 and at 07:33']
for s in stale:
    if s in new:
        fails.append('STALE %r' % s)
newlines = new.split('\n')[:-1]
if len(newlines) != NLF:
    fails.append('LINES %d' % len(newlines))
changed = [i + 1 for i in range(NLF) if newlines[i] != lines[i]]
print('OPS', len(OPS), 'changed lines', changed, 'lines', len(lines) - 1, '->', len(newlines))

# backticked repo paths that should exist (report only)
miss = set()
for m in re.finditer(r'`((?:build|bench|perf-notes|harness)/[^`\s]*)`', new):
    pth = m.group(1)
    if '<' in pth:
        continue
    if not os.path.exists(pth):
        miss.add(pth)
for pth in sorted(miss):
    print('  PATH missing (check): ' + pth)

diff = difflib.unified_diff(lines[:-1], newlines, 'RESUME.md 08:18', 'RESUME.md rfinal3', lineterm='', n=0)
with open(os.path.join(OUTDIR, 'rfinal3-diff.txt'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(diff) + '\n')
nsha = hashlib.sha256(nb).hexdigest().upper()
print('NEW', nsha, len(nb), 'B', nb.count(b'\n'), 'LF')
if fails:
    for x in fails:
        print('FAIL', x)
    print('ABORT (nothing written)')
    sys.exit(2)
if not APPLY:
    print('DRY OK (diff in build/agent11/resume/rfinal3-diff.txt)')
    sys.exit(0)
bk = os.path.join(OUTDIR, 'RESUME.%s-%s.md' % (T.replace(':', ''), EXP[:8]))
if os.path.exists(bk):
    print('ABORT backup exists', bk)
    sys.exit(3)
with open(bk, 'wb') as f:
    f.write(raw)
if hashlib.sha256(open(bk, 'rb').read()).hexdigest().upper() != EXP:
    print('ABORT backup mismatch')
    sys.exit(3)
with open(P, 'wb') as f:
    f.write(nb)
chk = open(P, 'rb').read()
if hashlib.sha256(chk).hexdigest().upper() != nsha:
    print('ABORT write mismatch')
    sys.exit(4)
print('WROTE', P, nsha, len(chk), 'B', chk.count(b'\n'), 'LF; backup', bk)
