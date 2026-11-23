# gw_stats.py <run dir> [--json OUT]: sum the "GPU wait stats (N s): ..." lines of a run by field name
# (QUEUE.md row 17: l1_waits, l1_polls, l2_tries and kicks must all be > 0; l2_tries = 0 means a skip_lr bin
# with H2 silently off). Also prints the back-off/stats init lines, sleep_fail, and the summed wait histograms
# (Agent 9 sizes S and Q from them). Agent 3, 22:34.
import glob, json, os, re, sys

run = sys.argv[1]


def order(p):
    m = re.search(r'game\.(\d+)\.log$', p)
    return -int(m.group(1)) if m else 0


logs = sorted(glob.glob(os.path.join(run, 'game*.log')), key=order)
tot, mx, pos, n, init, per = {}, {}, {}, 0, [], []
for p in logs:
    for line in open(p, encoding='utf-8', errors='replace'):
        if 'GPU wait' in line and 'GPU wait stats' not in line:
            init.append(line.strip()[:220])
            continue
        m = re.search(r'GPU wait stats \(([\d.]+) s\): (.*)$', line)
        if not m:
            continue
        n += 1
        row = {}
        for sec in m.group(2).strip().split(' | '):
            t = sec.split()
            pre = ''
            if t and t[0] in ('L1', 'L2'):
                pre, t = t[0].lower() + '_', t[1:]
            i = 0
            while i < len(t) - 1:
                k, v = t[i], t[i + 1]
                try:
                    val = float(v)
                except ValueError:
                    i += 1
                    continue
                key = pre + k
                row[key] = val
                i += 2
                if i < len(t) and t[i] == 'ms':
                    i += 1
        per.append(row)
        for k, v in row.items():
            if k.endswith('max'):
                mx[k] = max(mx.get(k, 0.0), v)
            else:
                tot[k] = tot.get(k, 0.0) + v
                if v > 0:
                    pos[k] = pos.get(k, 0) + 1

print('logs:', ', '.join(os.path.basename(x) for x in logs))
print('init/other GPU wait lines (%d):' % len(init))
for x in init[:4]:
    print('  ' + x)
print('stats lines: %d' % n)
if not n:
    print('RESULT: NO DATA (no "GPU wait stats" lines)')
    sys.exit(3)
need = ['l1_waits', 'l1_polls', 'l2_tries', 'kicks']
for k in need + ['l1_moved', 'l1_gpu_off', 'l2_waits', 'l2_polls', 'l2_delayed', 'pause', 'yield', 'sleep', 'sleep_fail']:
    print('  %-12s sum %-12g lines>0 %d/%d' % (k, tot.get(k, 0), pos.get(k, 0), n))
print('  L1 sum %.1f ms, max %.3f ms; L2 sum %.1f ms, max %.3f ms; sleep_sum %.1f ms' % (
    tot.get('l1_sum', 0), mx.get('l1_max', 0), tot.get('l2_sum', 0), mx.get('l2_max', 0), tot.get('sleep_sum', 0)))
for pre in ('l1_', 'l2_'):
    h = [(k[len(pre):], tot[k]) for k in tot if k.startswith(pre) and k[len(pre):][:1] in '<>']
    if h:
        print('  %s hist: %s' % (pre[:2].upper(), ' '.join('%s %g' % kv for kv in h)))
bad = [k for k in need if tot.get(k, 0) <= 0]
res = 'PASS' if not bad else 'FAIL (zero: %s%s)' % (', '.join(bad), '; l2_tries = 0 -> skip_lr bin, H2 off' if 'l2_tries' in bad else '')
print('RESULT: %s; sleep_fail %g' % (res, tot.get('sleep_fail', 0)))
if '--json' in sys.argv:
    json.dump({'lines': n, 'sum': tot, 'max': mx, 'lines_pos': pos, 'init': init[:4], 'result': res},
              open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
sys.exit(0 if not bad else 1)
