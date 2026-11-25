"""M9 S3T-9 item 3: build the q500-default diff from base/ -> new/ and apply-check it.

Paper only: no compile, no game. Writes only under build/agent9/session3/q500/.
  1. diff = git diff --no-index base new, headers rewritten to WS-relative a/ b/ paths;
  2. --check against the live tree from WS root (WS is not a git repo, so git apply acts as plain patch; no write);
  3. apply on a scratch copy (scratch/DimensionsRecomp/...) with git -c core.autocrlf=false apply, compare to new/;
  4. reverse-apply on the scratch copy, compare to base/.
Exit 0 = all PASS.
"""
import hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
REL = 'DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp'
BASE = os.path.join(HERE, 'base', 'gpu_wait_backoff.cpp')
NEW = os.path.join(HERE, 'new', 'gpu_wait_backoff.cpp')
LIVE = os.path.join(WS, *REL.split('/'))
DIFF = os.path.join(HERE, 'q500-default.diff')
SCR = os.path.join(HERE, 'scratch')
BELOW = 0x00004000  # BELOW_NORMAL_PRIORITY_CLASS
fails = 0


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


def check(name, ok, detail=''):
    global fails
    print(('PASS ' if ok else 'FAIL ') + name + (': ' + detail if detail else ''))
    if not ok:
        fails += 1


def git(args, cwd):
    r = subprocess.run(['git', '-c', 'core.autocrlf=false'] + args, cwd=cwd, capture_output=True,
                       creationflags=BELOW)
    return r.returncode, (r.stdout + r.stderr).decode('utf-8', 'replace').strip()


check('live == base (b0bd3b4 blob, HASHES.txt 01D9F8F3)', sha(LIVE) == sha(BASE), sha(LIVE)[:16])
for p in (BASE, NEW):
    b = open(p, 'rb').read()
    check('%s is LF-only' % os.path.relpath(p, HERE), b.count(b'\r') == 0, '%d B' % len(b))

rc, out = git(['diff', '--no-index', '--no-color', '--output=' + DIFF + '.raw', 'base/gpu_wait_backoff.cpp',
               'new/gpu_wait_backoff.cpp'], HERE)
check('git diff --no-index ran (exit 1 = differences)', rc == 1, out)
raw = open(DIFF + '.raw', 'rb').read().split(b'\n')
outl = []
for ln in raw:
    if ln.startswith(b'diff --git '):
        ln = b'diff --git a/' + REL.encode() + b' b/' + REL.encode()
    elif ln.startswith(b'--- a/'):
        ln = b'--- a/' + REL.encode()
    elif ln.startswith(b'+++ b/'):
        ln = b'+++ b/' + REL.encode()
    outl.append(ln)
open(DIFF, 'wb').write(b'\n'.join(outl))
os.remove(DIFF + '.raw')
d = open(DIFF, 'rb').read()
plus = sum(1 for l in d.split(b'\n') if l.startswith(b'+') and not l.startswith(b'+++'))
minus = sum(1 for l in d.split(b'\n') if l.startswith(b'-') and not l.startswith(b'---'))
print('diff %s  %d B  +%d/-%d  sha256 %s' % (os.path.relpath(DIFF, WS), len(d), plus, minus, sha(DIFF)))

rc, out = git(['rev-parse', '--show-toplevel'], WS)
check('WS root is not inside a git repo (git apply = plain patch there)', rc != 0, out.splitlines()[0] if out else '')
rc, out = git(['apply', '--check', '-v', DIFF], WS)
check('apply --check vs the live tree from WS root (no write)', rc == 0 and 'Skipped' not in out, out.replace('\n', ' | '))
check('live tree untouched by --check', sha(LIVE) == sha(BASE))

if os.path.isdir(SCR):
    shutil.rmtree(SCR)
os.makedirs(os.path.dirname(os.path.join(SCR, *REL.split('/'))))
tgt = os.path.join(SCR, *REL.split('/'))
shutil.copyfile(BASE, tgt)
rc, out = git(['rev-parse', '--show-toplevel'], SCR)
check('scratch is not inside a git repo', rc != 0)
rc, out = git(['apply', '-v', DIFF], SCR)
check('apply on scratch copy', rc == 0 and 'Skipped' not in out, out.replace('\n', ' | '))
check('scratch result == new/ byte for byte', sha(tgt) == sha(NEW), sha(tgt)[:16] + ' vs ' + sha(NEW)[:16])
rc, out = git(['apply', '-R', '-v', DIFF], SCR)
check('reverse apply on scratch', rc == 0 and 'Skipped' not in out, out.replace('\n', ' | '))
check('reverse result == base/ byte for byte', sha(tgt) == sha(BASE))
print('base %s\nnew  %s' % (sha(BASE), sha(NEW)))
print('RESULT: %s (%d FAIL)' % ('PASS' if not fails else 'FAIL', fails))
sys.exit(1 if fails else 0)
