import json, random, statistics as st, sys, ctypes, math
try:
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
except Exception:
    pass
d = json.load(open(sys.argv[1], encoding='utf-8'))
runs = d['runs']
print('runs', len(runs), 'keys', sorted(runs[0].keys()))
for r in runs:
    print(r['name'], r['round'], r['slot'], r['arm'], r['count'], '%.2f %.3f %.3f %.3f %.3f' % (r['fps'], r['p99'], r['low1_ms'], r['cores'], r['median']),
          r.get('gpu'), r.get('nongame'), r.get('m12'), r.get('proof_ok'), r.get('func_ok'), r.get('sys31'))

def boot(va, vb, n, seed):
    rnd = random.Random(seed); ds = []
    for _ in range(n):
        ra = [va[rnd.randrange(len(va))] for _ in va]
        rb = [vb[rnd.randrange(len(vb))] for _ in vb]
        ds.append(st.median(ra) - st.median(rb))
    ds.sort()
    return ds[int(0.025 * n)], ds[int(0.975 * n) - 1]

def pm(v):
    from math import comb
    s = sorted(v); n = len(s); out = {}
    def cdf(j):
        p = (j + 1) / n
        return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range((n + 1) // 2, n + 1))
    for k in range(n):
        out[s[k]] = out.get(s[k], 0) + cdf(k) - (cdf(k - 1) if k else 0)
    return out

def exact(va, vb):
    # only valid for odd n (median = order stat)
    if len(va) % 2 == 0 or len(vb) % 2 == 0:
        return None, None
    pa, pb = pm(va), pm(vb); dist = {}
    for x, p in pa.items():
        for y, q in pb.items():
            dist[x - y] = dist.get(x - y, 0) + p * q
    c = 0; lo = hi = None
    for v, p in sorted(dist.items()):
        c += p
        if lo is None and c > 0.025: lo = v
        if hi is None and c >= 0.975: hi = v
    return lo, hi

T975 = {3: 3.182, 4: 2.776}
def paired(A, B, key):
    ba = {r['round']: r[key] for r in A}; bb = {r['round']: r[key] for r in B}
    ks = sorted(set(ba) & set(bb)); l = [math.log(ba[k] / bb[k]) for k in ks]
    m = st.mean(l); se = st.stdev(l) / math.sqrt(len(l)); t = T975[len(l) - 1]
    same = sum(1 for x in l if (x > 0) == (m > 0))
    return (math.exp(m) - 1) * 100, (math.exp(m - t * se) - 1) * 100, (math.exp(m + t * se) - 1) * 100, same, len(l)

def run_set(label, sel):
    print('==', label)
    for a, b in (('win3', 's0'), ('ship', 's0'), ('ship', 'win3')):
        A = [r for r in sel if r['arm'] == a]; B = [r for r in sel if r['arm'] == b]
        for key in ('fps', 'p99', 'low1_ms', 'cores', 'median'):
            va = [r[key] for r in A]; vb = [r[key] for r in B]
            ma, mb = st.median(va), st.median(vb)
            lo, hi = boot(va, vb, 10000, 1); lo2, hi2 = boot(va, vb, 10000, 7); elo, ehi = exact(va, vb)
            ex = ' exact [%+.1f,%+.1f]' % (elo / mb * 100, ehi / mb * 100) if elo is not None else ''
            pp = paired(A, B, key)
            print('%-4s vs %-4s %-7s n %d/%d pt %+.1f%% seed1 [%+.1f,%+.1f] seed7 [%+.1f,%+.1f]%s | paired %+.1f [%+.1f,%+.1f] %d/%d | a %s b %s' % (
                a, b, key, len(va), len(vb), (ma - mb) / mb * 100, lo / mb * 100, hi / mb * 100, lo2 / mb * 100, hi2 / mb * 100, ex,
                pp[0], pp[1], pp[2], pp[3], pp[4], sorted(round(x, 3) for x in va), sorted(round(x, 3) for x in vb)))

sc = [r for r in runs if r['count'] and 2 <= r['round'] <= 6]
run_set('r2-6 headline', sc)
run_set('r2-6 without m12', [r for r in sc if not r.get('m12')])
run_set('r3-6', [r for r in sc if r['round'] >= 3])
run_set('r2-6 without round 3', [r for r in sc if r['round'] != 3])
