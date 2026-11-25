import json, random, statistics as st, sys, os, ctypes
try:
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
except Exception:
    pass
J = sys.argv[1]
d = json.load(open(J, encoding='utf-8'))
runs = d['runs']
print('runs', len(runs))
for r in runs:
    print(r['name'], r['round'], r['slot'], r['arm'], r['count'], r.get('scored'), '%.2f %.3f %.3f %s %.3f' % (r['fps'], r['p99'], r['low1_ms'], r['cores'], r['median']), r.get('gpu'), r.get('nongame'), r.get('m12'), r.get('misses'), r.get('proof_ok'), r.get('func_ok'), r.get('sys31'))
sc = [r for r in runs if r['count'] and 2 <= r['round'] <= 6]
A = [r for r in sc if r['arm'] == 'nf']; B = [r for r in sc if r['arm'] == 'mc']
print('n', len(A), len(B))

def boot(va, vb, n, seed, mode):
    rnd = random.Random(seed); ds = []
    for _ in range(n):
        ra = [va[rnd.randrange(len(va))] for _ in va]
        rb = [vb[rnd.randrange(len(vb))] for _ in vb]
        if mode == 'diff':
            ds.append(st.median(ra) - st.median(rb))
        else:
            ds.append(st.median(ra) / st.median(rb) - 1)
    ds.sort()
    return ds[int(0.025 * n)], ds[int(0.975 * n) - 1]

def exact(va, vb):
    # exact bootstrap distribution of median(ra)-median(rb), n=5 each: median of 5 resampled = order stat k with known probs
    from math import comb
    def pm(v):
        s = sorted(v); n = len(s); out = {}
        for k in range(n):
            # P(median <= s[k]) = P(at least 3 of 5 draws <= s[k])
            def cdf(j):
                p = (j + 1) / n
                return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range((n + 1) // 2, n + 1))
            out[s[k]] = out.get(s[k], 0) + cdf(k) - (cdf(k - 1) if k else 0)
        return out
    pa, pb = pm(va), pm(vb)
    dist = {}
    for x, p in pa.items():
        for y, q in pb.items():
            dist[x - y] = dist.get(x - y, 0) + p * q
    items = sorted(dist.items()); c = 0; lo = hi = None
    for v, p in items:
        c += p
        if lo is None and c > 0.025: lo = v
        if hi is None and c >= 0.975: hi = v
    return lo, hi

for key in ('fps', 'p99', 'low1_ms', 'cores', 'median'):
    va = [r[key] for r in A]; vb = [r[key] for r in B]
    ma, mb = st.median(va), st.median(vb)
    lo, hi = boot(va, vb, 10000, 1, 'diff')
    lo2, hi2 = boot(va, vb, 10000, 7, 'diff')
    elo, ehi = exact(va, vb)
    print('%-8s nf %s mc %s | pt %+.1f%% | seed1 [%+.1f,%+.1f] | seed7 [%+.1f,%+.1f] | exact [%+.1f,%+.1f]' % (
        key, sorted(round(x, 3) for x in va), sorted(round(x, 3) for x in vb), (ma - mb) / mb * 100,
        lo / mb * 100, hi / mb * 100, lo2 / mb * 100, hi2 / mb * 100, elo / mb * 100, ehi / mb * 100))
