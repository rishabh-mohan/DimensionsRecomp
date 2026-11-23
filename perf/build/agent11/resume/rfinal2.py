# rfinal2.py - perf-notes/RESUME.md delta after the 08:09 final (Agent 11, task #25): #19's rate request.
# Dry run by default (writes rfinal2-diff.txt only); --apply --t=HH:MM writes the doc after a hashed backup.
# Gate: final sha BDF0E68B..., 381 LF, no CR, no BOM. Every op is keyed to a line number and needs its old
# text exactly once in that line. No line is added or removed, so every line cite stays valid.
import datetime
import difflib
import hashlib
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
P = 'perf-notes/RESUME.md'
EXP = 'BDF0E68B1F4505597D2F70CF69386A1FCABD5EC972DCE16B2CD29A47F314F173'
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


sub(5, "This is the final version (Nov 23, 08:09).",
    "This is the final version (Nov 23, 08:09; updated at {T} for #19's rate request).")

sub(112, "; its proofs P1-P10 pass; not rated yet. Its rate request is task #32 for Agent 7 (docs only, due 11:30 on Nov 23), and Agent 10 rates it after the break;",
    "; diff sha256 06B0D371…; its proofs P1-P10 pass; not compiled, syntax-checked or rated yet. Its rate request is written (`build/agent7/s4-r1s2/RATE-REQUEST.md`, task #32, 08:12 on Nov 23), and Agent 10 rates it after the break;")

sub(274, "#19's rate request: task #32 for Agent 7 (docs only, due 11:30 on Nov 23); Agent 10 rates it after the break (step 3);",
    "#19's rating: Agent 10 rates it after the break from its rate request (`build/agent7/s4-r1s2/RATE-REQUEST.md`, written at 08:12 on Nov 23; step 3);")

sub(282, "not rated yet. Its rate request is task #32 for Agent 7 (docs only, due 11:30 on Nov 23), and Agent 10 rates it after the break. Its `<N>` (the #18 split size) waits for Agent 3's ready-N gate (`build/agent7/HANDOFF.md` §4).",
    "not rated yet. Its rate request (`build/agent7/s4-r1s2/RATE-REQUEST.md`, §16) asks Agent 10, after the break: (a) is it SAFE to build into devoff4b as a default-off test bed; (b) is it SAFE to test ON (`d3d12_submit_split_kb=<N>` plus `d3d12_async_submit=true`) in the rows, the soak and W7; (c) are the threading and ownership rules and the code reads accepted (its §6 and §11). Its `<N>` (the #18 split size) waits for Agent 3's ready-N gate, which wasn't there at 08:10 (RATE-REQUEST §10; `build/agent7/HANDOFF.md` §4).")

sub(283, "Steps: a rate request and a `clang -fsyntax-only` check, Agent 10's rating, a build, then the functional runs and a 10-minute soak.",
    "Steps: the `clang -fsyntax-only` check once compiles are allowed (RATE-REQUEST §10), Agent 10's rating, then Agent 2's build at ≤ 2 threads. Apply by copying `build/agent7/s4-r1s2/new/sdk/` or with the `--directory` form in RATE-REQUEST §2: the snap1 SDK has no `.git`, so `git -C <sdk root> apply` uses a repository outside the workspace, prints \"Skipped patch\" for all 5 files and exits 0 without applying anything. Then the 9 functional rows (~41 min of runs plus ~10 min of checks; `build/agent7/s4-r1s2/FUNCTIONAL-ROWS.md`) and the 10-minute soak (`build/agent7/s4-r1s2/SOAK.md`), whose counter-line checker isn't written yet.")

sub(284, "W7 itself: s0 / #18 / #18 + #19 / #18 + #19 + #20, 17 runs, ~43 min. #18 alone should tie.",
    "W7 itself, as Agent 7's draft (`build/agent7/s4-r1s2/matrix-w7-draft.json`, RATE-REQUEST §14; Agent 8 owns the final): s0 / s18 (#18 at `<N>`) / s19 (#18 + #19), all on one bin, 1 cold + 3 × 4 = 13 runs, ~30-34 min; with the optional s19h (`<N/2>`) 17 runs, ~39-45 min. S4-DRAFT's 4th arm (#18 + #19 + #20) is dropped, because #20's step 2 isn't staged. s18 should tie s0; s19 should lower the GPU Commands thread's ms/f by about the \"D3D12 Submit\" thread's ms/f, less the drains. W7 runs only after (b) is rated SAFE and the rows and the soak pass.")

sub(316, "(`run-night.ps1` L461-467)",
    "(`run-night.ps1` L461-467 in the night's 16B90FA8…)")

sub(375, "| `build/agent7/s4-r1s2/`; ",
    "| `build/agent7/s4-r1s2/` (with `RATE-REQUEST.md`); ")

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
stale = ['task #32 for Agent 7 (docs only', 'due 11:30', 'a rate request and a `clang',
         '#18 + #19 + #20, 17 runs', 'draft 2', 'not installed yet']
for s in stale:
    if s in new:
        fails.append('STALE %r' % s)
newlines = new.split('\n')[:-1]
if len(newlines) != NLF:
    fails.append('LINES %d' % len(newlines))
print('OPS', len(OPS), 'lines', len(lines) - 1, '->', len(newlines))

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

diff = difflib.unified_diff(lines[:-1], newlines, 'RESUME.md 08:09 final', 'RESUME.md rfinal2', lineterm='', n=0)
with open(os.path.join(OUTDIR, 'rfinal2-diff.txt'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(diff) + '\n')
nsha = hashlib.sha256(nb).hexdigest().upper()
print('NEW', nsha, len(nb), 'B', nb.count(b'\n'), 'LF')
if fails:
    for x in fails:
        print('FAIL', x)
    print('ABORT (nothing written)')
    sys.exit(2)
if not APPLY:
    print('DRY OK (diff in build/agent11/resume/rfinal2-diff.txt)')
    sys.exit(0)
bk = os.path.join(OUTDIR, 'RESUME.%s-%s.md' % (datetime.datetime.now().strftime('%H%M'), EXP[:8]))
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
