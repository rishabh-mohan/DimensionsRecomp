"""M10 read-only re-check of FINAL-DEFAULTS.diff. Writes only under build/agent10/session3/scratch-final/v."""
import hashlib, os, re, shutil, subprocess, sys

WS = os.getcwd()
DIFF = os.path.join(WS, 'build', 'agent2', 'final', 'FINAL-DEFAULTS.diff')
NEW = os.path.join(WS, 'build', 'agent2', 'final', 'work', 'new')
SNAP = os.path.join(WS, 'build', 'agent2', 'snap1')
Q500 = os.path.join(WS, 'build', 'agent9', 'session3', 'q500', 'q500-default.diff')
V = os.path.join(WS, 'build', 'agent10', 'session3', 'scratch-final', 'v')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


text = open(DIFF, 'rb').read().decode('utf-8')
files = sorted(set(re.findall(r'^\+\+\+ b/(\S+)', text, re.M)))
print('files', len(files))
if os.path.exists(V):
    shutil.rmtree(V)
ok = True
for f in files:
    live = os.path.join(WS, f)
    snap = os.path.join(SNAP, f)
    os.makedirs(os.path.dirname(os.path.join(V, f)), exist_ok=True)
    shutil.copyfile(live, os.path.join(V, f))
    s_live = sha(live)
    s_snap = sha(snap) if os.path.exists(snap) else 'MISSING'
    print('before live', s_live[:16], 'snap1', s_snap[:16], 'same' if s_live == s_snap else 'DIFFERENT', f)
    ok &= s_live == s_snap
r = subprocess.run(['git', '-c', 'core.autocrlf=false', 'apply', DIFF], cwd=V, capture_output=True, text=True)
print('apply rc', r.returncode, (r.stdout + r.stderr).strip())
ok &= r.returncode == 0
for f in files:
    a, b = sha(os.path.join(V, f)), sha(os.path.join(NEW, f))
    print('after', a[:16], 'MATCH' if a == b else 'DIFF', f)
    ok &= a == b


def section(t, path):
    for p in re.split(r'(?m)^(?=diff --git )', t):
        if ('+++ b/' + path) in p:
            return p[p.index('\n@' + '@'):]
    return None


p = 'DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp'
q = open(Q500, 'rb').read().decode('utf-8')
same = section(text, p) == section(q, p) and section(q, p) is not None
print('q500 sha', sha(Q500)[:8], 'section identical:', same)
ok &= same
# changed REXCVAR default lines
for m in re.finditer(r'^\+(.*REXCVAR_DEFINE_\w+\(\s*(\w+),\s*(\w+).*)$', text, re.M):
    print('  +default', m.group(2), '=', m.group(3))
for m in re.finditer(r'^\+\s+(\w+), (true|false), "', text, re.M):
    print('  +default', m.group(1), '=', m.group(2), '(macro next line)')
shutil.rmtree(V)
print('RESULT', 'PASS' if ok else 'FAIL')
