# check_w5b.py - read-only helper for CHECK-W5b.md (checker for Agent 7's W5b readout).
# Uses only numbers copied from load-check.md L87-95, pool-W5b.md section 8 and W5 READOUT L116/L119.
import itertools
import math
import statistics as st

# loaded runs (ng_t >= 2.8): fps change vs the arm's quiet median, load-check.md L87-95
t = {'0455': -4.7, '0213': -3.5, '0510': -1.5, '0459': -2.2}   # d11t
p = {'0457': 0.1, '0209': -0.9, '0520': -2.6, '0524': -0.9}    # d11p
a = list(t.values())
b = list(p.values())
d = st.mean(a) - st.mean(b)
va, vb = st.variance(a), st.variance(b)
se = math.sqrt(va / len(a) + vb / len(b))
df = (va / len(a) + vb / len(b)) ** 2 / ((va / len(a)) ** 2 / (len(a) - 1) + (vb / len(b)) ** 2 / (len(b) - 1))
print('loaded fps: mean d11t %.3f d11p %.3f diff %.3f se %.3f t %.3f welch df %.2f' % (st.mean(a), st.mean(b), d, se, d / se, df))
try:
    from scipy import stats
    tc = stats.t.ppf(0.975, df)
    pv = 2 * stats.t.sf(abs(d / se), df)
    print('Welch 95%% CI [%.2f, %.2f], p %.3f' % (d - tc * se, d + tc * se, pv))
    print('Mann-Whitney:', stats.mannwhitneyu(a, b, alternative='two-sided'))
except Exception as e:  # scipy missing: permutation test below still runs
    print('no scipy:', e)
allv = a + b
n = len(a)
cnt = tot = 0
for idx in itertools.combinations(range(len(allv)), n):
    g1 = [allv[i] for i in idx]
    g2 = [allv[i] for i in range(len(allv)) if i not in idx]
    tot += 1
    if abs(st.mean(g1) - st.mean(g2)) >= abs(d) - 1e-9:
        cnt += 1
print('exact permutation (mean diff) two-sided p = %d/%d = %.3f' % (cnt, tot, cnt / tot))

# pass-1 median-ms spreads, (max - min) / median, per arm (runner's 0155 summary.md: 10.1 / 10.3 / 4.4 %)
ms = {'d11': [2.288, 2.528, 2.542, 2.526, 2.492, 2.504],
      'd11t': [2.347, 2.496, 2.606, 2.532, 2.498, 2.531],
      'd11p': [2.435, 2.511, 2.544, 2.505, 2.500, 2.489]}
for k, v in ms.items():
    full = (max(v) - min(v)) / st.median(v) * 100
    w = v[1:]
    nr1 = (max(w) - min(w)) / st.median(w) * 100
    print('%s pass-1 median-ms spread: all %.2f %%, without round 1 %.2f %%' % (k, full, nr1))

# W5: game cores vs base, d11t -13.7 %, d11 +0.9 % (W5 READOUT L116, L119) -> d11t vs d11
print('W5 d11t vs d11 cores: %.1f %%' % ((0.863 / 1.009 - 1) * 100))
