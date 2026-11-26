import subprocess, hashlib, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# rebuild the pre-fix synth (4D25 minus the Z4 hard-exit block) for the diff
syn = open('nops-smoke/synth/synth_post.py', 'rb').read()
a = syn.index(b'# Z4 hard exit:')
b = syn.index(b'del post.fails[:]', a) + len(b'del post.fails[:]') + 1
if syn[b:b + 1] == b'\n':
    pass
open('pins-test/synth-prev.py', 'wb').write(syn[:a] + syn[b:])
pairs = [('pins-test/post-54BA5CF9.py', 'nops_smoke_post.py'), ('pins-test/synth-prev.py', 'nops-smoke/synth/synth_post.py'),
         ('pins-test/cmd-51E7A02E.cmd', 'RUN-NOPS-SMOKE.cmd')]
d = b''.join(subprocess.run(['git', '-c', 'core.autocrlf=false', 'diff', '--no-index', x, y], capture_output=True).stdout
             for x, y in pairs)
open('z4-post-delta.diff', 'wb').write(d)
print(len(d), d.count(b'\n'), hashlib.sha256(d).hexdigest().upper()[:16])
for f in ('nops_smoke_post.py', 'nops-smoke/synth/synth_post.py', 'RUN-NOPS-SMOKE.cmd', 'pins-test/synth-prev.py',
          'nops-smoke/post/nops-smoke-post-20261125-201245-z4fix.txt', 'pins-test/tamper-test.txt', 'z4-post-delta.diff'):
    print(hashlib.sha256(open(f, 'rb').read()).hexdigest().upper(), f)
