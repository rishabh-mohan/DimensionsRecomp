"""One-off: what each sampler shows around the 0221-d11t-r5 long-frame cluster (Agent 7, task #21; read-only).

Reads perf.csv, gpu.csv, proc.csv, sys.csv and game.log of one run and prints what each shows near the
cluster of long frames at window T 32.6-33.5 s (T = sum of frame times from the window's first row).
Writes the same text to build/agent7/readout/cluster-0221.txt.
Run (repo root): python -B build/agent7/readout/cluster_0221.py
"""
import csv
import datetime as dt
import json
import re
import statistics

RD = 'build/agent8/matrix/20261123-0155/runs/0221-d11t-r5/'
OUT = 'build/agent7/readout/cluster-0221.txt'
T0, T1 = 32.6, 33.5      # cluster span (window seconds)
C0, C1 = 28.0, 38.0      # context span shown for the ~1 s samplers
out = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    out.append(s)


def med(xs):
    xs = list(xs)
    return statistics.median(xs) if xs else float('nan')


fj = json.load(open(RD + 'frames.json', encoding='utf-8-sig'))
rj = json.load(open(RD + 'run.json', encoding='utf-8-sig'))
w = fj['window']
off, n = w['first_row'] - 1, w['rows']
ms, me, ps = rj['measure_start'], rj['measure_end'], rj['process_start_mark']
ms_wall = dt.datetime.strptime(ms['wall'], '%Y-%m-%d %H:%M:%S.%f')
win_off_proc = ms['epoch_s'] - ps['epoch_s']


def wall_of(t):
    return (ms_wall + dt.timedelta(seconds=t)).strftime('%H:%M:%S.%f')[:-3]


p('# 0221-d11t-r5 cluster check (cluster_0221.py; read-only)')
p('run dir:', RD)
p('measure_start', ms['wall'], '| measure_end', me['wall'], '| window_wall_s', rj['window_wall_s'])
p('window T 0 = process t_s %.3f; cluster T %.1f-%.1f s = wall %s-%s' % (win_off_proc, T0, T1, wall_of(T0), wall_of(T1)))

# ---- perf.csv (one row per frame)
p('')
p('## perf.csv (one row per frame; window rows %d from row %d)' % (n, w['first_row']))
rows = list(csv.DictReader(open(RD + 'perf.csv', newline='', encoding='utf-8-sig')))[off:off + n]
keys = ['draw_calls', 'command_buffer_stalls', 'buffer_queue_depth', 'functions_dispatched', 'interrupt_dispatches',
        'active_threads', 'apc_queue_depth', 'critical_region_contentions', 'texture_cache_misses',
        'pipeline_cache_misses', 'xma_frames_decoded', 'audio_frame_latency_us']
p('window frames', len(rows))
p('window median', {k: med(float(r[k]) for r in rows) for k in keys})
p('window max', {k: max(float(r[k]) for r in rows) for k in keys})
t = 0.0
sel, over10 = [], []
for r in rows:
    ft = float(r['frame_time_us']) / 1000.0
    t += ft / 1000.0
    if ft > 10.0:
        over10.append(t)
    if T0 <= t <= T1:
        sel.append((t, ft, r))
p('frames > 10 ms in window: %d; in cluster span: %d (T %.2f-%.2f)' % (
    len(over10), sum(1 for x in over10 if T0 <= x <= T1),
    min([x for x in over10 if T0 <= x <= T1] or [float('nan')]),
    max([x for x in over10 if T0 <= x <= T1] or [float('nan')])))
p('frames in T %.1f-%.1f s: %d, median ft %.2f ms' % (T0, T1, len(sel), med(x[1] for x in sel)))
p('cluster sums: texture misses', sum(float(x[2]['texture_cache_misses']) for x in sel),
  '| pipeline misses', sum(float(x[2]['pipeline_cache_misses']) for x in sel),
  '| cb stalls', sum(float(x[2]['command_buffer_stalls']) for x in sel),
  '| critical-region contentions', sum(float(x[2]['critical_region_contentions']) for x in sel))
p('cluster buffer_queue_depth min/max: %s / %s' % (min(float(x[2]['buffer_queue_depth']) for x in sel),
                                                   max(float(x[2]['buffer_queue_depth']) for x in sel)))
p('frames > 8 ms in the span:')
for tt, ft, r in sel:
    if ft > 8.0:
        p('  T %.3f ft %.2f ' % (tt, ft) + ' '.join('%s=%s' % (k, r[k]) for k in keys))

# ---- gpu.csv (~1 s; t_s spans 0.4-49.6 s over the 50 s window, so it is window-relative)
p('')
p('## gpu.csv (~1 s samples; t_s is window-relative)')
g = list(csv.DictReader(open(RD + 'gpu.csv', newline='', encoding='utf-8-sig')))
p('rows %d, t_s %.2f-%.2f' % (len(g), float(g[0]['t_s']), float(g[-1]['t_s'])))
p('window median util_gpu %.0f, gr_mhz %.0f, power_w %.2f; min util_gpu %s at t_s %s' % (
    med(float(r['util_gpu']) for r in g), med(float(r['gr_mhz']) for r in g), med(float(r['power_w']) for r in g),
    min(g, key=lambda r: float(r['util_gpu']))['util_gpu'], min(g, key=lambda r: float(r['util_gpu']))['t_s']))
p('rows with util_gpu < 90:', ', '.join('t_s %s util %s' % (r['t_s'], r['util_gpu']) for r in g if float(r['util_gpu']) < 90) or 'none')
p('rows at t_s %.0f-%.0f:' % (C0, C1))
for r in g:
    if C0 <= float(r['t_s']) <= C1:
        p('  t_s %s wall %s pstate %s gr_mhz %s temp %s power %s util_gpu %s util_mem %s throttle %s' % (
            r['t_s'], wall_of(float(r['t_s'])), r['pstate'], r['gr_mhz'], r['temp_c'], r['power_w'], r['util_gpu'],
            r['util_mem'], r['throttle']))

# ---- proc.csv (~1 s; t_s from process start)
p('')
p('## proc.csv (~1 s samples; window T = t_s - %.3f)' % win_off_proc)
pr = list(csv.DictReader(open(RD + 'proc.csv', newline='', encoding='utf-8-sig')))
pw = [r for r in pr if 0.0 <= float(r['t_s']) - win_off_proc <= 50.0]
p('window rows %d, median cpu_cores %.2f, min %.2f, max %.2f' % (
    len(pw), med(float(r['cpu_cores']) for r in pw), min(float(r['cpu_cores']) for r in pw),
    max(float(r['cpu_cores']) for r in pw)))
p('rows at window T %.0f-%.0f:' % (C0, C1))
for r in pr:
    tw = float(r['t_s']) - win_off_proc
    if C0 <= tw <= C1:
        p('  t_s %s T %.2f phase %s cpu_cores %s threads %s handles %s responding %s log_lines %s note %s' % (
            r['t_s'], tw, r['phase'], r['cpu_cores'], r['threads'], r['handles'], r['responding'], r['log_lines'],
            r['note']))

# ---- sys.csv (~1 s; epoch_s)
p('')
p('## sys.csv (~1 s samples, host-wide)')
sy = list(csv.DictReader(open(RD + 'sys.csv', newline='', encoding='utf-8-sig')))
sw = [r for r in sy if 0.0 <= float(r['epoch_s']) - ms['epoch_s'] <= 50.0]
cols = ['cpu_util_pct', 'eff_mhz', 'p_eff_mhz', 'e_eff_mhz', 'p_util_pct', 'e_util_pct']
p('window rows %d, medians: ' % len(sw) + ', '.join('%s %.2f' % (c, med(float(r[c]) for r in sw)) for c in cols))
p('rows at window T %.0f-%.0f:' % (C0, C1))
for r in sy:
    tw = float(r['epoch_s']) - ms['epoch_s']
    if C0 <= tw <= C1:
        p('  wall %s T %.2f ' % (r['wall'], tw) + ' '.join('%s %s' % (c, r[c]) for c in cols) +
          ' fg_game %s input_desktop %s' % (r['fg_game'], r['input_desktop']))

# ---- game.log (timestamped lines)
p('')
p('## game.log')
pat = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]')
lines = []
for ln in open(RD + 'game.log', encoding='utf-8-sig', errors='replace'):
    m = pat.match(ln)
    if m:
        tw = (dt.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f') - ms_wall).total_seconds()
        lines.append((tw, ln.rstrip('\n')))
inwin = [x for x in lines if 0.0 <= x[0] <= 50.0]
p('timestamped lines: %d in all, %d inside the window' % (len(lines), len(inwin)))
before = [x for x in lines if x[0] < T0]
after = [x for x in lines if x[0] > T1]
if before:
    p('last line before the cluster (T %.2f, %.2f s earlier): %s' % (before[-1][0], T0 - before[-1][0], before[-1][1][:170]))
if after:
    p('first line after the cluster (T %.2f): %s' % (after[0][0], after[0][1][:170]))
p('lines inside the cluster span: %d' % sum(1 for x in lines if T0 <= x[0] <= T1))

with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(out) + '\n')
print('wrote', OUT)
