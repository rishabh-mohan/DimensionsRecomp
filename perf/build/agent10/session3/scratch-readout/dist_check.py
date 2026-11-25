#!/usr/bin/env python3
"""M10 cross-check of M8's night read-out (read-only). Per-arm pooled frame-time shape, mean vs median,
short-frame share, within-arm clock slope for fps, and a run-level recompute of the WC contrasts.
Usage: python -B dist_check.py PASSDIR... (rounds >= 2, kept rule as readout_night.py)."""
import csv, json, math, os, statistics as st, sys

sys.dont_write_bytecode = True
try:
    import ctypes
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
except Exception:
    pass

def truthy(v):
    return str(v).strip().lower() in ('true', '1', 'yes')

def window(rd, fj):
    w = fj['window']; first, n = w['first_row'], w['rows']
    scale = float(fj.get('scale_to_us') or 1.0) / 1000.0
    path = os.path.join(rd, os.path.basename(fj.get('file') or 'perf.csv'))
    out = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        r = csv.reader(f); hdr = next(r); ci = hdr.index(fj.get('column') or 'frame_time_us')
        for i, row in enumerate(r):
            if i < first: continue
            if i >= first + n: break
            out.append(float(row[ci]) * scale)
    return out

def q(s, p):
    return s[max(0, math.ceil(p * len(s)) - 1)]

min_round = 2
arms = {}
runs = []
for d in sys.argv[1:]:
    with open(os.path.join(d, 'results.csv'), encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            if not (truthy(r['scored']) and r['status'] == 'OK' and truthy(r['valid_timing']) and not truthy(r['excluded'])
                    and int(r['round']) >= min_round):
                continue
            rd = r['run_dir']
            with open(os.path.join(rd, 'run.json'), encoding='utf-8-sig') as f2:
                j = json.load(f2)
            fj = j['frames']
            ft = window(rd, fj)
            s = sorted(ft)
            mean = sum(ft) / len(ft)
            rec = dict(arm=r['arm'], name=os.path.basename(rd), n=len(ft), mean=mean, median=q(s, .5),
                       fps_count=fj['frames'] / fj['window_s'], fps_meanft=1000.0 / mean, fps_json=fj['mean_fps'],
                       eff=float(r['eff_mhz']) if r.get('eff_mhz') else None, ft=s, ngl=r.get('flags_info'))
            # time covered by the window frames vs window_s (does the frame source cover the window?)
            rec['cover'] = sum(ft) / 1000.0 / fj['window_s']
            runs.append(rec)
            arms.setdefault(r['arm'], []).append(rec)

print('kept runs', len(runs))
print('| arm | n | p1 | p5 | p10 | p25 | p50 | p75 | p90 | p95 | p99 | mean | mean-p50 | <1.0ms | <1.5ms | >3.0ms | >4.0ms | cover |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for a, v in arms.items():
    allft = sorted(x for r in v for x in r['ft'])
    m = sum(allft) / len(allft)
    N = len(allft)
    lt = lambda t: sum(1 for x in allft if x < t) / N * 100
    gt = lambda t: sum(1 for x in allft if x > t) / N * 100
    print('| %s | %d | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %+.3f | %.1f%% | %.1f%% | %.1f%% | %.1f%% | %.4f |' % (
        a, len(v), q(allft, .01), q(allft, .05), q(allft, .10), q(allft, .25), q(allft, .5), q(allft, .75), q(allft, .9),
        q(allft, .95), q(allft, .99), m, m - q(allft, .5), lt(1.0), lt(1.5), gt(3.0), gt(4.0), st.mean(r['cover'] for r in v)))

print()
print('fps definitions per arm (median of runs): frames/window_s | 1000/mean_ft | frames.json mean_fps')
for a, v in arms.items():
    print('  %s: %.1f | %.1f | %.1f ; arm mean of fps_json %.1f' % (a, st.median(r['fps_count'] for r in v),
          st.median(r['fps_meanft'] for r in v), st.median(r['fps_json'] for r in v), st.mean(r['fps_json'] for r in v)))

# share of total time spent in frames above / below the s0 median, per arm
print()
print('time decomposition: ms per frame contributed by frames above 3 ms, per arm (mean over frames)')
for a, v in arms.items():
    allft = [x for r in v for x in r['ft']]
    N = len(allft)
    print('  %s: total %.3f ms/f; from frames <=2.5 ms %.3f; 2.5-3.5 %.3f; >3.5 %.3f' % (
        a, sum(allft) / N, sum(x for x in allft if x <= 2.5) / N, sum(x for x in allft if 2.5 < x <= 3.5) / N,
        sum(x for x in allft if x > 3.5) / N))

# within-arm clock slope for fps (log fps residual vs eff MHz)
xs, ys = [], []
for a, v in arms.items():
    lm = st.mean(math.log(r['fps_json']) for r in v)
    for r in v:
        if r['eff']:
            xs.append(r['eff']); ys.append((math.exp(math.log(r['fps_json']) - lm) - 1) * 100)
mx, my = st.mean(xs), st.mean(ys)
sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys)); sxx = sum((x - mx) ** 2 for x in xs); syy = sum((y - my) ** 2 for y in ys)
print()
print('within-arm fps residual vs eff MHz: r = %.2f, slope %+.2f %%fps per 100 MHz over %d runs' % (
    sxy / math.sqrt(sxx * syy), sxy / sxx * 100, len(xs)))
for a, v in arms.items():
    print('  %s eff MHz mean %.0f range %.0f-%.0f' % (a, st.mean(r['eff'] for r in v), min(r['eff'] for r in v), max(r['eff'] for r in v)))
