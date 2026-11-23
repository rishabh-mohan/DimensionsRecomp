#!/usr/bin/env python3
"""Step 6 (read-only): hook inventory from the link maps + bounded direct-call BFS
from the scene-walk hot functions, to see which hooked guest functions sit under the walk.
Writes build/agent9/s4/scene-walk/step6.log. Run via bench/agent9/cpu2.ps1 only."""
import collections
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
GEN = os.path.join(ROOT, 'baseline', 'DimensionsRecomp', 'rexlego', 'generated', 'default')
MAPS = [('devoff2', os.path.join(ROOT, 'build', 'agent2', 'devoff2-bin', 'legodimensions.map')),
        ('native3d', os.path.join(ROOT, 'build', 'agent2', 'native3d-bin', 'legodimensions.map'))]
OUT = os.path.join(HERE, 'step6.log')
genobj = re.compile(r'^legodimensions_recomp\.(\d+)\.cpp\.obj$')
out = open(OUT, 'w', encoding='ascii', errors='replace', newline='\n')


def P(*a):
    out.write(' '.join(str(x) for x in a) + '\n')
    out.flush()


fn_tu = {}
hooked = {}
for tag, path in MAPS:
    h = {}
    with open(path, 'r', encoding='latin-1') as f:
        for line in f:
            p = line.split()
            if len(p) < 4:
                continue
            n = p[1]
            obj = p[-1]
            if n.startswith('__imp__sub_8') and len(n) == 20:
                if tag == 'devoff2':
                    m = genobj.match(obj)
                    if m:
                        fn_tu[n[7:]] = m.group(1)
                continue
            if len(n) == 12 and n.startswith('sub_8'):
                m = genobj.match(obj)
                if m:
                    if tag == 'devoff2':
                        fn_tu.setdefault(n, m.group(1))
                else:
                    h[n] = obj
    hooked[tag] = h

d = hooked['devoff2']
n3 = hooked['native3d']
P('=== hooked guest functions (sub_ symbol provided by a non-generated object)')
P('devoff2', len(d), 'native3d', len(n3), 'generated functions', len(fn_tu))
byobj = collections.defaultdict(list)
for k, v in sorted(n3.items()):
    byobj[('both' if k in d else 'NATIVE-ONLY', v)].append(k)
for (t, obj), names in sorted(byobj.items()):
    P(t, obj, len(names), ' '.join(names))
for k, v in sorted(d.items()):
    if k not in n3:
        P('DEVOFF-ONLY', v, k)

targets = ('sub_82FEB7B8 sub_82AFAB68 sub_82AF9BC0 sub_82FCC500 sub_82FCB308 sub_82F050B0 '
           'sub_82EF8C18 sub_82F0CCD8 sub_82F0B200 sub_82EFE948 sub_82EF3B38 sub_82EF3180 '
           'sub_82EF2FE0 sub_82EF2E28 sub_82EF2368 sub_82B61580 sub_82B62528 sub_82B62C1C '
           'sub_82B53308 sub_82FBC4D8 sub_82EF4338 sub_82EFB260 sub_82FBC588 sub_82FBBB50 '
           'sub_82AF52B0 sub_82B6FC70 sub_82EF0918 sub_82EF0A68 sub_82A2A260 sub_83FB33E0 '
           'sub_82EF9350 sub_83E46040 sub_83E45090 sub_82A34208 sub_82A3E238 sub_82A3E2B8').split()
P('=== probe target providers')
for t in targets:
    P(t, 'tu', fn_tu.get(t), 'devoff2', d.get(t, 'generated'), 'native3d', n3.get(t, 'generated'))

callpat = re.compile(r'\b(sub_8[0-9A-F]{7})\(ctx, base\)')
defpat = re.compile(r'^\s*(?:DEFINE_REX_FUNC|REX_FUNC|PPC_FUNC_IMPL|PPC_FUNC)\((?:__imp__)?(sub_[0-9A-Fa-f]{8})\)', re.M)
fn_callees = {}
loaded = set()


def ensure(tu):
    if tu in loaded:
        return
    loaded.add(tu)
    with open(os.path.join(GEN, 'legodimensions_recomp.%s.cpp' % tu), 'r', encoding='latin-1') as f:
        txt = f.read()
    ms = list(defpat.finditer(txt))
    for i, m in enumerate(ms):
        e = ms[i + 1].start() if i + 1 < len(ms) else len(txt)
        body = txt[m.start():e]
        cs = []
        for c in callpat.findall(body):
            if c not in cs:
                cs.append(c)
        fn_callees[m.group(1)] = (cs, body.count('INDIRECT'))


def bfs(label, roots, maxd, maxn):
    par, depth = {}, {}
    q = collections.deque()
    for r in roots:
        depth[r] = 0
        par[r] = None
        q.append(r)
    hits = {}
    nodes = 0
    capped = False
    nind = 0
    while q:
        fn = q.popleft()
        nodes += 1
        if nodes > maxn:
            capped = True
            break
        if fn in n3 or fn in d:
            hits[fn] = depth[fn]
            continue
        tu = fn_tu.get(fn)
        if tu is None:
            continue
        ensure(tu)
        ent = fn_callees.get(fn)
        if ent is None:
            continue
        nind += ent[1]
        if depth[fn] >= maxd:
            continue
        for c in ent[0]:
            if c not in depth:
                depth[c] = depth[fn] + 1
                par[c] = fn
                q.append(c)

    def path(fn):
        ch = []
        while fn is not None:
            ch.append(fn)
            fn = par[fn]
        return ' <- '.join(ch)

    P('=== BFS', label, 'maxdepth', maxd, 'nodes', nodes, 'capped', capped, 'reached', len(depth),
      'tus_loaded', len(loaded), 'indirect_sites', nind)
    for fn, dep in sorted(hits.items(), key=lambda x: (x[1], x[0])):
        t = 'NATIVE-ONLY' if (fn in n3 and fn not in d) else ('both' if fn in n3 else 'devoff-only')
        P('HOOK', t, n3.get(fn, d.get(fn)), 'depth', dep, path(fn))


bfs('UI/text subtree', ['sub_82FCC500', 'sub_82FCB308', 'sub_82F050B0', 'sub_82EF8C18', 'sub_82F0CCD8',
                        'sub_82EFE948', 'sub_82EF3B38', 'sub_82EF3180', 'sub_82EF2FE0', 'sub_82B61580',
                        'sub_82B62528', 'sub_82B62C1C', 'sub_82B53308'], 5, 6000)
bfs('whole walk from sub_82AFAB68', ['sub_82AFAB68'], 5, 9000)
P('done')
out.close()
