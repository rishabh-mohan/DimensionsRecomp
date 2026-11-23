r"""Task #33 (Agent 7). Run (PowerShell):
python -B bench\agent7\w4b_readout\zero_code_bins.py | Out-File -Encoding ascii bench\agent7\w4b_readout\zero-code-bins.txt
10 s bins of the zero-code runs' scored windows (FUNCTIONAL ONLY, SAT, n=1). Read-only. Per bin: frames, fps, >33 count, p99, E-core MHz median/min, busy median. Then >33 ms frames vs the rest:
mean of the native-frames.csv columns. Slow onset = first of 3+ consecutive sys.csv samples with e_eff_mhz < 800."""
import os
import sys
import statistics
import importlib.util

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
spec = importlib.util.spec_from_file_location('w4b', os.path.join(HERE, 'w4b_readout.py'))
w4b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w4b)

RUNS = [('n2t', r'build\agent8\matrix\20261122-0652\runs\0652-n2t-r1'),
        ('n3t', r'build\agent8\matrix\20261122-0655\runs\0655-n3t-r1'),
        ('n2s', r'build\agent8\matrix\20261122-0657\runs\0657-n2s-r1')]
COLS = ('frame_slot_wait_ms', 'frame_slot_wait_calls', 'sync_ms', 'sync_calls', 'present_cpu_ms',
        'present_submit_cpu_ms', 'acquire_cpu_ms', 'swap_present_cpu_ms', 'pipeline_creations',
        'pipeline_creation_ms', 'callbacks_pending', 'draw_calls', 'issue_ms', 'tail_ms')


def p99(v):
    s = sorted(v)
    return w4b.nearest_rank(s, 99, 100) if s else None


for arm, rel in RUNS:
    rd = os.path.join(ROOT, rel)
    fj = w4b.load_json(os.path.join(rd, 'frames.json'))
    rj = w4b.load_json(os.path.join(rd, 'run.json')) or {}
    first, n = int(fj['window']['first_row']), int(fj['window']['rows'])
    _, fts, xs = w4b.load_frames(os.path.join(rd, 'native-frames.csv'), 'native', 'interval_ms', 1000.0, COLS,
                                 stop_after=first + n)
    win = fts[first:first + n]
    pre_s = sum(fts[:first]) / 1e6
    series, wwin, note = w4b.game_cpu(rd, rj, fj)
    ws, we = wwin
    ff_e = w4b.num(rj.get('ff_signal_epoch_s'))
    srows = w4b.read_rows(os.path.join(rd, 'sys.csv')) or []
    ss = sorted((w4b.num(r.get('epoch_s')), w4b.num(r.get('e_eff_mhz')), w4b.num(r.get('p_eff_mhz')),
                 w4b.num(r.get('cpu_util_pct')), w4b.num(r.get('cpu_perf_pct'))) for r in srows
                if w4b.num(r.get('epoch_s')) is not None)
    onset = None
    for i in range(len(ss) - 2):
        if all(ss[j][1] is not None and ss[j][1] < 800 for j in (i, i + 1, i + 2)):
            onset = ss[i][0]
            break
    print('== %s %s' % (arm, rel))
    print('window: ws=%.3f we=%.3f (%.1f s); ws - ff_signal = %s s; frame time before first_row = %.1f s; '
          'slow onset (3x E<800) = %s' % (
              ws, we, we - ws, '-' if ff_e is None else '%.1f' % (ws - ff_e), pre_s,
              '-' if onset is None else '%.1f s after ws (%s s after ff)' % (
                  onset - ws, '-' if ff_e is None else '%.1f' % (onset - ff_e))))
    # 10 s bins on the frame time line from the window start
    cum, bins = 0.0, {}
    tags = []
    for k, ft in enumerate(win):
        cum += ft / 1e6
        b = min(5, int((cum - 1e-9) // 10))
        bins.setdefault(b, []).append(ft)
        tags.append(b)
    print('bin | t (s from ws) | frames | fps | >33 | p99 ms | E MHz med (min) | P MHz med | busy med | slow')
    for b in sorted(bins):
        v = bins[b]
        e0, e1 = ws + 10 * b, ws + 10 * (b + 1)
        smp = [s for s in ss if e0 <= s[0] < e1]
        em = [s[1] for s in smp if s[1] is not None]
        pm = [s[2] for s in smp if s[2] is not None]
        bz = [min(1.0, s[3] / s[4]) for s in smp if s[3] is not None and s[4]]
        slow = onset is not None and e1 > onset
        print('%d | %d-%d | %d | %.1f | %d | %.1f | %s (%s) | %s | %s | %s' % (
            b, 10 * b, 10 * (b + 1), len(v), len(v) / (sum(v) / 1e6), sum(1 for x in v if x > 33000),
            p99(v) / 1000.0, '%.0f' % statistics.median(em) if em else '-', '%.0f' % min(em) if em else '-',
            '%.0f' % statistics.median(pm) if pm else '-', '%.3f' % statistics.median(bz) if bz else '-',
            'SLOW' if slow else ''))
    # before / after onset
    if onset is not None and onset < we:
        cut = onset - ws
        cum, a, b_ = 0.0, [], []
        for ft in win:
            cum += ft / 1e6
            (a if cum < cut else b_).append(ft)
        for name, v in (('before onset', a), ('after onset', b_)):
            if v:
                t = sum(v) / 1e6
                print('%s: %.1f s, fps %.1f, >33 %d = %.1f/min, p99 %.1f ms' % (
                    name, t, len(v) / t, sum(1 for x in v if x > 33000),
                    60.0 * sum(1 for x in v if x > 33000) / t, p99(v) / 1000.0))
    # >33 ms frames vs rest
    slowf = [k for k, ft in enumerate(win) if ft > 33000]
    rest = [k for k, ft in enumerate(win) if ft <= 33000]
    print('column | mean over >33 ms frames (n=%d) | mean over the rest (n=%d)' % (len(slowf), len(rest)))
    for c in COLS:
        if c not in xs:
            continue
        col = xs[c][first:first + n]
        def m(idx):
            vals = [col[k] for k in idx if col[k] is not None]
            return statistics.fmean(vals) if vals else float('nan')
        print('%s | %.3f | %.3f' % (c, m(slowf), m(rest)))
    # where the >33 frames sit: gaps between them (clustered or spread)
    cum, times = 0.0, []
    for ft in win:
        cum += ft / 1e6
        if ft > 33000:
            times.append(cum)
    if len(times) > 1:
        gaps = sorted(b - a for a, b in zip(times, times[1:]))
        print('>33 frame gaps s: median %.2f, p10 %.2f, p90 %.2f; within 0.5 s of another: %d of %d' % (
            statistics.median(gaps), gaps[len(gaps) // 10], gaps[(9 * len(gaps)) // 10],
            sum(1 for i, t in enumerate(times) if (i > 0 and t - times[i - 1] <= 0.5) or
                (i + 1 < len(times) and times[i + 1] - t <= 0.5)), len(times)))
    print()
