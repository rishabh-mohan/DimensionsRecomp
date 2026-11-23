"""Agent 9 - dry run of build/agent2/make-rb-clones.py (task #14) for the nativeB script review (Agent 1, 03:34).
Runs its main() unchanged, but every write goes under build/agent9/review/rb-dryrun (reads are unchanged; nothing
under build/agent2 is written). Then: py_compile of the prep clones, and prep-nb.py --check-only on the real snap1
and install tree (a test copy whose LOG/RCLOG/NOTES/DST_ROOT point into rb-dryrun), plus the negative test
--install build/agent9/install/batch, which must be refused before anything is read.
  python build/agent9/review/dryrun-rb-clones.py
"""
import builtins, importlib.util, os, py_compile, subprocess, sys

R = r'<workspace>'
OUT = os.path.join(R, 'build', 'agent9', 'review', 'rb-dryrun')
SRC = os.path.join(R, 'build', 'agent2', 'make-rb-clones.py')
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    p = os.path.join(OUT, f)
    if os.path.isfile(p):
        os.remove(p)

spec = importlib.util.spec_from_file_location('mrc', SRC)
mrc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mrc)
real_open = builtins.open


def safe_open(p, mode='r', *a, **k):
    if any(c in mode for c in 'wax+'):
        q = os.path.abspath(p)
        if not q.lower().startswith(OUT.lower() + os.sep):
            q = os.path.join(OUT, os.path.basename(q))
        print('  (write redirected: %s -> %s)' % (os.path.relpath(p, R), os.path.relpath(q, R)))
        p = q
    return real_open(p, mode, *a, **k)


mrc.open = safe_open
mrc.DIFFS = os.path.join(OUT, 'RB-diffs')
print('== make-rb-clones.py main() (writes redirected)')
rc = mrc.main()
print('main() returned', rc)

print('== py_compile')
for f in sorted(os.listdir(OUT)):
    if f.endswith('.py'):
        try:
            py_compile.compile(os.path.join(OUT, f), cfile=os.path.join(OUT, '__pyc', f + 'c'), doraise=True)
            print('  %s: OK' % f)
        except py_compile.PyCompileError as e:
            print('  %s: FAIL %s' % (f, e))

print('== prep-nb.py --check-only (test copy: logs into rb-dryrun, DST not created)')
t = real_open(os.path.join(OUT, 'prep-nb.py'), encoding='utf-8').read()
subs = [("LOG = os.path.join(A, 'snapB3-prep.txt')", "LOG = os.path.join(%r, 'test-snapB3-prep.txt')" % OUT),
        ("RCLOG = os.path.join(A, 'snapB3-robocopy.log')", "RCLOG = os.path.join(%r, 'test-snapB3-robocopy.log')" % OUT),
        ("NOTES = os.path.join(A, 'snapB3-manifest-notes.txt')", "NOTES = os.path.join(%r, 'test-snapB3-notes.txt')" % OUT),
        ("DST_ROOT = os.path.join(A, 'snapB3')", "DST_ROOT = os.path.join(%r, 'test-snapB3-not-created')" % OUT)]
for a, b in subs:
    n = t.count(a)
    if n != 1:
        sys.exit('STOP: test copy: %r matches %d times' % (a, n))
    t = t.replace(a, b)
tp = os.path.join(OUT, 'test-prep-nb.py')
real_open(tp, 'w', encoding='utf-8', newline='\n').write(t)
for args in (['--check-only'], ['--check-only', '--install', os.path.join(R, 'build', 'agent9', 'install', 'batch')]):
    r = subprocess.run([sys.executable, tp] + args, capture_output=True, text=True)
    print('-- test-prep-nb.py %s -> exit %d' % (' '.join(os.path.relpath(x, R) if os.path.isabs(x) else x for x in args),
                                                   r.returncode))
    for line in (r.stdout + r.stderr).splitlines()[-14:]:
        print('   ' + line[:230])
print('DONE')
