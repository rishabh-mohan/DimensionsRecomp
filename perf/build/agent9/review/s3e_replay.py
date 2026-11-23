"""Agent 9 review of Agent 2's S3e clones: replay make-s3e-clones.py in a scratch copy (nothing in build/agent2 is
written), then compare every output byte-for-byte with Agent 2's files, and check ASCII/LF/BOM + Python compile."""
import hashlib, os, re, shutil, subprocess, sys

R = r'<workspace>'
A = os.path.join(R, 'build', 'agent2')
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's3e-replay')


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16].upper()


if os.path.isdir(S):
    shutil.rmtree(S)
os.makedirs(S)
for src, dst in (('prep-s3d.py', 'prep-s3d.py'), ('run-s3d.ps1', 'run-s3d.ps1'), ('stop-snap.ps1.pre-S3e', 'stop-snap.ps1')):
    shutil.copyfile(os.path.join(A, src), os.path.join(S, dst))
with open(os.path.join(A, 'make-s3e-clones.py'), encoding='utf-8') as f:
    txt = f.read()
line = "A = r'<workspace>\\build\\agent2'"
assert txt.count(line) == 1, 'A line not found exactly once'
txt = txt.replace(line, 'A = r%r' % S if False else "A = r'%s'" % S)
with open(os.path.join(S, 'make-s3e-clones.replay.py'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(txt)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
p = subprocess.run([sys.executable, os.path.join(S, 'make-s3e-clones.replay.py')], capture_output=True, text=True, env=env)
print('replay exit %d' % p.returncode)
print(p.stdout.rstrip())
if p.stderr.strip():
    print('stderr: ' + p.stderr.rstrip())
ok = p.returncode == 0
for n in ('prep-s3e.py', 'run-s3e.ps1', 'stop-snap.ps1', 'stop-snap.ps1.pre-S3e', 'S3e-diffs/prep-s3e.py.vs-s3d.diff',
          'S3e-diffs/run-s3e.ps1.vs-s3d.diff', 'S3e-diffs/stop-snap.ps1.S3e.diff'):
    a, b = os.path.join(A, *n.split('/')), os.path.join(S, *n.split('/'))
    ha, hb = sha(a), (sha(b) if os.path.exists(b) else 'MISSING')
    same = ha == hb
    ok &= same
    print('%-40s agent2 %s replay %s %s' % (n, ha, hb, 'SAME' if same else 'DIFF'))
# sources unchanged
for n, want in (('prep-s3d.py', 'BD4D94DA'), ('run-s3d.ps1', 'FE159F8A'), ('stop-snap.ps1.pre-S3e', 'C6B75748'),
                ('stop-snap.ps1', '705233E5'), ('prep-s3e.py', '23536F1F'), ('run-s3e.ps1', 'FD188929')):
    h = sha(os.path.join(A, n))
    ok &= h.startswith(want)
    print('%-24s %s quoted %s %s' % (n, h, want, 'OK' if h.startswith(want) else 'MISMATCH'))
# ASCII / LF / BOM
for n in ('prep-s3e.py', 'run-s3e.ps1', 'stop-snap.ps1', 'make-s3e-clones.py'):
    b = open(os.path.join(A, n), 'rb').read()
    asc = all(c < 128 for c in b)
    lf = b'\r' not in b
    bom = b.startswith(b'\xef\xbb\xbf')
    longest = max(len(l) for l in b.split(b'\n'))
    ok &= asc and lf and not bom
    print('%-20s ascii %s lf-only %s bom %s lines %d longest %d' % (n, asc, lf, bom, b.count(b'\n'), longest))
# Python compile in memory (no bytecode written)
for n in ('prep-s3e.py', 'make-s3e-clones.py'):
    src = open(os.path.join(A, n), encoding='utf-8').read()
    compile(src, n, 'exec')
    print('%s compiles' % n)
# diff stats
for n in ('prep-s3e.py.vs-s3d.diff', 'run-s3e.ps1.vs-s3d.diff', 'stop-snap.ps1.S3e.diff'):
    d = open(os.path.join(A, 'S3e-diffs', n), encoding='utf-8').read().splitlines()
    ad = sum(1 for l in d if l.startswith('+') and not l.startswith('+++'))
    de = sum(1 for l in d if l.startswith('-') and not l.startswith('---'))
    print('%s +%d/-%d' % (n, ad, de))
# every remaining base/ref token in the clones, for the semantic review
for n in ('prep-s3e.py', 'run-s3e.ps1'):
    for i, l in enumerate(open(os.path.join(A, n), encoding='utf-8').read().split('\n'), 1):
        toks = re.findall(r'native3(?:-bin|\'s| |\))|S3(?![0-9A-Za-z])|run-s3\\?\.ps1|S3d|snap3d|s3d', l)
        if toks:
            print('  %s:%d %s | %s' % (n, i, ','.join(toks), l.strip()[:120]))
print('RESULT %s' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
