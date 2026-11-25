import json, os, re, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
j = lambda p: json.load(open(os.path.join(R, p), encoding='utf-8-sig'))
wc = j('bench/agent8/run/matrix-windowC.json')
w8 = j('bench/agent8/run/matrix-window8a.json')
c1 = j('build/agent8/session3/confirm/matrix-windowCF1.json')
c2 = j('build/agent8/session3/confirm/matrix-windowCF2.json')
IGN = {'note', 'group', 'repeats', 'ref'}
def arms(m): return {a['id']: a for a in m['arms']}
def strip(a): return {k: v for k, v in a.items() if k not in IGN}
def top(m): return {k: v for k, v in m.items() if k not in ('arms', 'notes', 'title', 'reference')}
print('WC arms', list(arms(wc)), 'W8a arms', list(arms(w8)))
for name, cf, base, ids in (('CF1', c1, wc, ('s0', 'win3')), ('CF2', c2, w8, ('mc', 'n0'))):
    print('==', name, 'top diff vs base:')
    tc, tb = top(cf), top(base)
    for k in sorted(set(tc) | set(tb)):
        if tc.get(k) != tb.get(k):
            print('  ', k, 'cf=', tc.get(k), 'base=', tb.get(k))
    for i in ids:
        a, b = arms(cf).get(i), arms(base).get(i)
        if b is None:
            print('  ', i, 'MISSING in base'); continue
        sa, sb = strip(a), strip(b)
        print('  ', i, 'EQUAL' if sa == sb else 'DIFF', '' if sa == sb else {k: (sa.get(k), sb.get(k)) for k in set(sa) | set(sb) if sa.get(k) != sb.get(k)})
        print('      ignored-field diffs:', {k: (a.get(k), b.get(k)) for k in IGN - {'note'} if a.get(k) != b.get(k)})
# dfoff vs final_gate OFF_SET
sys.path.insert(0, os.path.join(R, 'build', 'agent12', 'session3'))
src = open(os.path.join(R, 'build/agent12/session3/final_gate.py'), encoding='utf-8').read()
off = eval(re.search(r'OFF_SET = (\{.*?\})', src, re.S).group(1))
df = dict(x.split('=', 1) for x in arms(c1)['dfoff']['cvars'])
fl = df.pop('framerate_limit')
print('dfoff == OFF_SET:', df == off, 'framerate_limit', fl, 'env', arms(c1)['dfoff']['env'], len(off))
print('ship', strip(arms(c1)['ship']))
print('nf', strip(arms(c2)['nf']))
print('W8a mc', strip(arms(w8)['mc']) if 'mc' in arms(w8) else None)
