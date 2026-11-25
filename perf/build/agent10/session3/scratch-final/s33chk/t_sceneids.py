import os, sys, io, contextlib
WS = r'..\..\..\..\..'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), WS, 'build', 'agent3', 'session3', 's33-rows')))
import s33_sceneids as S
B = os.path.abspath(os.path.join(os.path.dirname(__file__), WS, 'build', 'agent3', 'runs', '20261125-070859-s33-basesf'))
C = os.path.abspath(os.path.join(os.path.dirname(__file__), WS, 'build', 'agent3', 'runs', '20261125-071741-s33-offsf'))
real = S.A.marks
mb = real(B, False, 'off')
pb = S.perf_scenes(B)
st = sorted(pb[1].items(), key=lambda x: -x[1])
order = pb[2]
# a pair of adjacent stable scenes in base order, both stable in cand
pc = S.perf_scenes(C)
adj = [(order[j], order[j + 1]) for j in range(len(order) - 1) if pc[1].get(order[j], 0) > 0 and pc[1].get(order[j + 1], 0) > 0]
print('adjacent stable pairs:', len(adj), adj[:3])
def run(label, row, patch):
    def fake(run_, make, kind='off'):
        m = dict(real(run_, make, kind))
        if run_ == C:
            patch(m)
        return m
    S.A.marks = fake
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = S.main(['x', '--row', row, B, C])
    S.A.marks = real
    res = [l for l in out.getvalue().splitlines() if l.startswith('RESULT') or 'SHOULD' in l]
    print('%-34s rc=%d %s' % (label, rc, ' | '.join(res)))
k = 'after-a1'
a, b = adj[0]
def set_id(i):
    def p(m):
        t, n, _ = m[k]
        m[k] = (t, n, i)
    return p
# base id at mark k is mb[k][2]; set cand to a stable neighbour (pick from adj where first == base id if any)
bid = mb[k][2]
nb = [y for x, y in adj if x == bid] + [x for x, y in adj if y == bid]
print('base id at', k, bid, 'stable neighbours', nb)
run('ON, stable neighbour', 's33onsf', set_id(nb[0] if nb else b))
run('ON, stable non-neighbour', 's33onsf', set_id(st[-1][0] if st[-1][0] != bid else st[-2][0]))
run('ON, unstable id', 's33onsf', set_id('1/2'))
run('gate, stable neighbour', 's33gthr0', set_id(nb[0] if nb else b))
run('OFF row, stable neighbour', 's33offw', set_id(nb[0] if nb else b))
def shift(m):
    t, n, i = m[k]
    m[k] = (t + 1.2, n, i)
run('ON, mark 1.2 s late', 's33onsf', shift)
def drop(m):
    m.pop('after-a2')
run('ON, mark missing', 's33onsf', drop)
