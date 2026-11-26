import subprocess, hashlib, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
pairs = [('pins-test/ps1-1D93442E.ps1', 'nops-smoke-run.ps1'), ('pins-test/cmd-AF57C90E.cmd', 'RUN-NOPS-SMOKE.cmd'),
         ('pins-test/mkpins-prev.py', 'mkpins.py')]
d = b''.join(subprocess.run(['git', '-c', 'core.autocrlf=false', 'diff', '--no-index', a, b], capture_output=True).stdout
             for a, b in pairs)
open('kit-d1-delta.diff', 'wb').write(d)
print(len(d), d.count(b'\n'), hashlib.sha256(d).hexdigest().upper()[:16])
for f in ('RUN-NOPS-SMOKE.cmd', 'nops-smoke-run.ps1', 'nops_smoke_post.py', 'mkpins.py', 'pins-test/tamper_test.py',
          'pins-test/tamper-test.txt', 'pins-test/guard_regex_test.ps1', 'kit-d1-delta.diff'):
    print(hashlib.sha256(open(f, 'rb').read()).hexdigest().upper(), f)
