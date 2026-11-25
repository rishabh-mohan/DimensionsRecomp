import subprocess, os, hashlib, shutil, re
WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))  # M10 N4
W = os.path.join(WS, r'build\agent2\final\work')
DIFF = os.path.join(WS, r'build\agent2\final\FINAL-DEFAULTS.diff')
Q500 = os.path.join(WS, r'build\agent9\session3\q500\q500-default.diff')
V = os.path.join(W, 'verify')
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()
def git(*a, cwd):
    r = subprocess.run(['git', '-c', 'core.autocrlf=false', *a], cwd=cwd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()
ok = True
if os.path.exists(V): shutil.rmtree(V)
files = sorted(set(re.findall(r'^\+\+\+ b/(\S+)', open(DIFF, encoding='utf-8', errors='replace').read(), re.M)))
for f in files:
    os.makedirs(os.path.dirname(os.path.join(V, f)), exist_ok=True)
    shutil.copyfile(os.path.join(WS, f), os.path.join(V, f))  # fresh byte copy of the live (HEAD) file
print('files in diff:', len(files))
for step in (['apply', '--check', DIFF], ['apply', DIFF]):
    rc, o = git(*step, cwd=V); print(' '.join(step[:-1]), rc, o); ok &= rc == 0
for f in files:
    a, b = sha(os.path.join(V, f)), sha(os.path.join(W, 'new', f))
    print('after', a[:16], 'MATCH' if a == b else 'DIFF', f); ok &= a == b
rc, o = git('apply', '-R', '--check', DIFF, cwd=V); print('apply -R --check', rc, o); ok &= rc == 0
rc, o = git('apply', '-R', DIFF, cwd=V); ok &= rc == 0
for f in files:
    a, b = sha(os.path.join(V, f)), sha(os.path.join(WS, f))
    ok &= a == b
print('reverse restores base:', ok)
rc, o = git('apply', '--check', DIFF, cwd=WS); print('apply --check vs LIVE (read-only)', rc, o); ok &= rc == 0
# q500 hunks verbatim: the gpu_wait_backoff.cpp section of FINAL == M9's diff body
def section(text, path):
    parts = re.split(r'(?m)^(?=diff --git )', text)
    for p in parts:
        if f'+++ b/{path}' in p:
            return p[p.index('@@'):]
fin = open(DIFF, 'rb').read().decode('utf-8'); q = open(Q500, 'rb').read().decode('utf-8')
p = 'DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp'
same = section(fin, p) == section(q, p)
print('q500 section identical to M9 diff (28F0D1DE):', same, 'q500 sha', sha(Q500)[:8]); ok &= same
crlf = fin.count('\r\n')
print('CRLF lines in FINAL diff (shaders.cpp only expected):', crlf)
print('RESULT', 'PASS' if ok else 'FAIL')
shutil.rmtree(V)
