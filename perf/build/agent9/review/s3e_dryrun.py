"""Agent 9 review: run Agent 2's prep-s3e.py main() read-only, twice:
  1. as is (expect 8/9: live == snap1 because Agent 4 has not written the new draw.cpp yet), and
  2. with the live hash faked (only inside this process) so all 9 checks pass and --dry-run reaches the rules/notes
     formatting code, which a real dry run cannot reach before the new write.
open() inside the module is wrapped to refuse any write mode, so nothing can be written."""
import builtins, importlib.util, io, os, sys

sys.dont_write_bytecode = True  # never write build/agent2/__pycache__

R = r'<workspace>'
P = os.path.join(R, 'build', 'agent2', 'prep-s3e.py')
spec = importlib.util.spec_from_file_location('prep_s3e', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

real_open = builtins.open


def guarded_open(file, mode='r', *a, **k):
    if any(c in mode for c in 'wax+'):
        raise RuntimeError('write attempted: %s %s' % (file, mode))
    return real_open(file, mode, *a, **k)


m.open = guarded_open
real_sha = m.sha
snap = real_sha(m.SNAPF)
live = real_sha(m.LIVE)
print('snap1 draw.cpp %s, live draw.cpp %s, equal %s' % (snap[:16], live[:16], snap == live))


def run(label, argv):
    print('=== %s: prep-s3e.py %s' % (label, ' '.join(argv)))
    sys.argv = ['prep-s3e.py'] + argv
    try:
        m.main()
        code = 0
    except SystemExit as e:
        code = e.code
    print('=== %s exit %s' % (label, code))
    return code


c1 = run('real', [live[:16], '--go', '04:55', '--dry-run'])
FAKE = 'f' * 64


def fake_sha(p):
    return FAKE if os.path.normcase(os.path.abspath(p)) == os.path.normcase(os.path.abspath(m.LIVE)) else real_sha(p)


m.sha = fake_sha
c2 = run('faked live hash', [FAKE[:16], '--go', '04:55', '--dry-run'])
for p in (m.RULES, m.NOTES):
    print('%s exists: %s' % (os.path.basename(p), os.path.exists(p)))
print('RESULT real exit %s (expect 1), faked exit %s (expect 0)' % (c1, c2))
