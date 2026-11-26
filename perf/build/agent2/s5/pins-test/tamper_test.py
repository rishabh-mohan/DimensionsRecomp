"""Tamper test for RUN-NOPS-SMOKE.cmd pins on a scratch copy of the kit + helpers (no game, no real ps1 run)."""
import os, shutil, subprocess, sys

WS = r'<workspace>'
KIT = os.path.join(WS, r'build\agent2\s5')
TT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tt')
sys.path.insert(0, KIT)
import mkpins  # noqa: E402

if os.path.exists(TT):
    shutil.rmtree(TT)
for rel in mkpins.PINNED + [r'build\agent2\s5\RUN-NOPS-SMOKE.cmd', r'build\agent2\s5\mkpins.py']:
    d = os.path.join(TT, rel)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copy2(os.path.join(WS, rel), d)
tk = os.path.join(TT, r'build\agent2\s5')
cmd = os.path.join(tk, 'RUN-NOPS-SMOKE.cmd')
res = []


def run(name, words, want):
    cp = subprocess.run('cmd /c ""%s" %s"' % (cmd, words), capture_output=True, text=True, errors='replace')
    out = (cp.stdout + cp.stderr).strip().replace('\n', ' | ')
    ok = cp.returncode == want
    res.append(ok)
    print('%s %-34s rc=%d want=%d  %s' % ('PASS' if ok else 'FAIL', name, cp.returncode, want, out[:300]))
    return out


def tamper(rel, how):
    p = os.path.join(TT, rel)
    orig = open(p, 'rb').read()
    if how == 'append':
        open(p, 'ab').write(b' ')
    elif how == 'delete':
        os.remove(p)
    return p, orig


# 1 clean copy (cmd copied byte-exact from the real kit)
run('clean copy pinsonly', 'pinsonly', 0)
# 2..n tamper each pinned file in turn (one-byte append), then restore
for rel in mkpins.PINNED:
    p, orig = tamper(rel, 'append')
    o = run('tamper ' + os.path.basename(rel), 'pinsonly', 3)
    if 'PIN MISMATCH ' + rel not in o:
        res.append(False); print('FAIL   mismatch line does not name', rel)
    open(p, 'wb').write(orig)
# missing helper
p, orig = tamper(r'build\agent2\final\check-defaults.py', 'delete')
run('delete check-defaults.py', 'pinsonly', 3)
open(p, 'wb').write(orig)
# tampered ps1 must refuse before powershell runs, also without pinsonly (dryrun word)
p, orig = tamper(r'build\agent2\s5\nops-smoke-run.ps1', 'append')
o = run('tamper ps1, dryrun word', 'dryrun', 3)
if 'S5 NOPS-SMOKE kit' in o:
    res.append(False); print('FAIL   ps1 ran despite mismatch')
open(p, 'wb').write(orig)
# fail closed: a scratch cmd with one pin line removed must refuse (PINOK 12 of 13), with and without pinsonly
corig = open(cmd, 'rb').read()
lines = corig.split(b'\r\n')
pl = [i for i, l in enumerate(lines) if l.startswith(b'call :pin ')]
open(cmd, 'wb').write(b'\r\n'.join(lines[:pl[3]] + lines[pl[3] + 1:]))
for w in ('pinsonly', 'dryrun'):
    o = run('pin line removed, %s word' % w, w, 3)
    if 'REFUSED: %d of %d pins verified' % (len(pl) - 1, len(pl)) not in o:
        res.append(False); print('FAIL   no fail-closed REFUSED line')
open(cmd, 'wb').write(corig)
# pass-through: stub ps1 + re-pinned scratch cmd -> pins OK, stub runs with the words, its exit code comes back
open(os.path.join(tk, 'nops-smoke-run.ps1'), 'w', newline='\r\n').write(
    "Write-Host ('STUB args=' + ($args -join ' '))\nexit 7\n")
subprocess.run([sys.executable, os.path.join(tk, 'mkpins.py'), '--kit', tk], check=True, capture_output=True)
o = run('stub ps1 pass-through', 'dryrun nozpd', 7)
if 'STUB args=dryrun nozpd' not in o:
    res.append(False); print('FAIL   stub args not passed through')
print('TAMPER TEST', 'ALL PASS' if all(res) else 'FAIL', '(%d checks)' % len(res))
sys.exit(0 if all(res) else 1)
