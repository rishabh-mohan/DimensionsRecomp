"""Non-vacuity probe for check 3 (A): shows what gate_logdiff.scan() returns for a run dir. Read-only, stdlib, no bytecode."""
import sys
sys.dont_write_bytecode = True
import importlib.util, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
GATE_PY = os.path.join(ROOT, 'bench', 'agent8', 'run', 'gate_logdiff.py')
RUNS = os.path.join(ROOT, 'build', 'agent8', 'matrix', '20261122-1756', 'runs')
spec = importlib.util.spec_from_file_location('gate_logdiff_ro', GATE_PY)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
ure = re.compile(gate.UNIMPL_DEFAULT)


def shape(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return repr(v)[:80]
    if isinstance(v, dict):
        return 'dict(%d)' % len(v)
    if hasattr(v, '__len__'):
        return '%s(%d)' % (type(v).__name__, len(v))
    return type(v).__name__


S = {}
for n in ('1800-s0-r1', '1804-d11t-r1'):
    s = gate.scan(os.path.join(RUNS, n), ure)
    S[n] = s
    if isinstance(s, dict):
        print(n, {k: shape(v) for k, v in s.items()})
    else:
        print(n, shape(s))
f, notes, match, diff = gate.compare(S['1800-s0-r1'], S['1804-d11t-r1'], 50)
print('compare s0-r1 vs d11t-r1: findings', len(f), 'notes', len(notes), 'match', shape(match),
      {k: shape(v) for k, v in diff.items()} if isinstance(diff, dict) else shape(diff))
