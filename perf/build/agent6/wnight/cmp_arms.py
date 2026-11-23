"""Task #19 helper (Agent 6): print the arms of matrix-window9/5b/4c and check
that the W5b / W4c arms are identical (bin, cvars, env) to the arms of the same
name in the W5 / W4b folder matrix.json files that the expect files are tested on.
Read-only. Usage: python -B build/agent6/wnight/cmp_arms.py
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SKIP = ('notes', 'note', 'desc', 'description', 'label', 'comment')


def load(p):
    with open(os.path.join(ROOT, p), encoding='utf-8-sig') as f:
        return json.load(f)


def arms_of(m):
    a = m.get('arms')
    if isinstance(a, dict):
        return dict(a)
    out = {}
    for it in a or []:
        name = it.get('name') or it.get('id') or it.get('arm') or it.get('label')
        out[name] = it
    return out


def j(v, n=None):
    s = json.dumps(v, sort_keys=True)
    return s if n is None or len(s) <= n else s[:n] + '...'


def show(tag, m):
    print('==', tag, 'top keys:', sorted(m.keys()))
    for k in ('reference', 'ref', 'base', 'repeats', 'order', 'cold', 'cold_arm'):
        if k in m:
            print('   ', k, '=', j(m[k], 200))
    for name, arm in arms_of(m).items():
        print('   arm', name)
        for k in sorted(arm.keys()):
            print('      ', k, '=', j(arm[k], 160 if k in SKIP else None))


def cmp(tag, a, b, names):
    A, B = arms_of(a), arms_of(b)
    for n in names:
        if n not in A or n not in B:
            print('CMP', tag, n, 'MISSING in', 'A' if n not in A else 'B')
            continue
        diffs = []
        for k in sorted(set(A[n]) | set(B[n])):
            if k in SKIP:
                continue
            x, y = A[n].get(k), B[n].get(k)
            if j(x) == j(y):
                continue
            if isinstance(x, list) and isinstance(y, list) and sorted(map(j, x)) == sorted(map(j, y)):
                diffs.append((k, 'same set, order differs', ''))
                continue
            if isinstance(x, str) and isinstance(y, str) and x.replace('\\', '/').rstrip('/') == y.replace('\\', '/').rstrip('/'):
                continue
            diffs.append((k, j(x), j(y)))
        print('CMP', tag, n, 'MATCH' if not diffs else 'DIFF')
        for k, x, y in diffs:
            print('      ', k, ':', x, '!=', y)


def main():
    w9 = load('bench/agent8/run/matrix-window9.json')
    w5b = load('bench/agent8/run/matrix-window5b.json')
    w4c = load('bench/agent8/run/matrix-window4c.json')
    f5 = load('build/agent8/matrix/20261122-1756/matrix.json')
    f4 = load('build/agent8/matrix/20261122-1541/matrix.json')
    show('matrix-window9', w9)
    show('matrix-window5b', w5b)
    show('matrix-window4c', w4c)
    print('== folder W5 (1756) arms:', sorted(arms_of(f5).keys()))
    print('== folder W4b (1541) arms:', sorted(arms_of(f4).keys()))
    cmp('W5b-vs-W5folder', w5b, f5, ['d11', 'd11t', 'd11p'])
    cmp('W4c-vs-W4bfolder', w4c, f4, ['d0', 'B'])


if __name__ == '__main__':
    main()
