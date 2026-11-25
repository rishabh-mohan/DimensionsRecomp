#!/usr/bin/env python3
"""M10: per kept WC run, GPU clock/temp/throttle over (approximately) the timed window, by round/slot/arm.
Window approximation: gpu.csv rows with t_s in [ff_to_window_s .. ff_to_window_s + window_s] measured from the
first gpu.csv row is not exact, so use run.json first_frame_signal_s + ff_to_window_s as start, + frames.window_s."""
import csv, json, os, statistics as st, sys

sys.dont_write_bytecode = True
try:
    import ctypes
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
except Exception:
    pass

def truthy(v):
    return str(v).strip().lower() in ('true', '1', 'yes')

rows_out = []
for pi, d in enumerate(sys.argv[1:], 1):
    with open(os.path.join(d, 'results.csv'), encoding='utf-8-sig', newline='') as f:
        res = list(csv.DictReader(f))
    for r in res:
        rd = r['run_dir']
        with open(os.path.join(rd, 'run.json'), encoding='utf-8-sig') as f2:
            j = json.load(f2)
        ff = j.get('first_frame_signal_s') or 0
        a = ff + float(j.get('ff_to_window_s') or 0)
        b = a + float(j['frames']['window_s'])
        g = []
        p = os.path.join(rd, 'gpu.csv')
        if os.path.exists(p):
            with open(p, encoding='utf-8-sig', newline='') as f3:
                for x in csv.DictReader(f3):
                    t = float(x['t_s'])
                    g.append(x)  # gpu.csv t_s runs 0..~50 s: the driver samples the timed window only
        mhz = [float(x['gr_mhz']) for x in g] or [float('nan')]
        tmp = [float(x['temp_c']) for x in g] or [float('nan')]
        thr = sorted(set(x['throttle'] for x in g))
        rows_out.append((pi, int(r['round']), r['arm'], os.path.basename(rd), len(g), st.mean(mhz), min(mhz), max(tmp),
                         ','.join(thr), r['scored']))

print('| pass | round | arm | run | gpu rows | gr MHz mean | min | temp max | throttle | scored |')
print('|---|---|---|---|---|---|---|---|---|---|')
for x in rows_out:
    print('| %d | %d | %s | %s | %d | %.0f | %.0f | %.0f | %s | %s |' % x)
print()
for rnd in sorted(set(x[1] for x in rows_out)):
    v = [x[5] for x in rows_out if x[1] == rnd and x[4]]
    if not v:
        continue
    print('round %d: gpu MHz mean %.0f (n %d)' % (rnd, st.mean(v), len(v)))
for arm in sorted(set(x[2] for x in rows_out)):
    v = [x[5] for x in rows_out if x[2] == arm and x[1] >= 2 and x[4]]
    if v:
        print('arm %s rounds>=2: gpu MHz mean %.0f range %.0f-%.0f' % (arm, st.mean(v), min(v), max(v)))
