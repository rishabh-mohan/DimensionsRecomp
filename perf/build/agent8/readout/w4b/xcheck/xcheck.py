#!/usr/bin/env python3
"""Independent cross-check of per-run and per-arm frame statistics of a finished timing matrix (helper of Agent 8,
2026-11-23). Own code, stdlib only; it reads the runner's inputs and writes only into its own xcheck dir.

  python -B xcheck.py w4b|w5 [--dump]

Definitions (learned from frame_summary.py, run-timing.ps1, w4b_readout.py docs; re-implemented here, nothing imported):
  window   perf.csv data rows with 17 integer fields (malformed rows and a last line without newline are not rows);
           first row = the first row whose end offset (byte after its newline) is past run.json
           measure_start.perf_csv_bytes; last row = the shortest run of rows from there whose frame_time_us sum
           (values <= 0 count 0) reaches params.seconds (50 s scored, 30 s cold)
  frames   window rows with frame_time_us > 0 (zero rows stay in the row count only)
  fps      frames / (sum of their frame_time_us / 1e6)            [fps_wall = frames / run.json window_wall_s, info]
  median   nearest rank: sorted[ceil(n * 1/2) - 1] (lower middle for even n); p99 sorted[ceil(n * 99/100) - 1];
           p99.9 sorted[ceil(n * 999/1000) - 1]
  1% low   1e6 * k / (sum of the k largest frame times in us), k = max(1, n // 100)   (Agent 7 add-on, task #26)
  >33      frame_time_us > 33000; >100: > 100000
  cores    game CPU in the window: mean of proc.csv cpu_cores over the rows with phase 'measure' (one row per runner
           sample = run-timing's winCores; proc.csv rounds each to 0.01); slope = cpu_s(last measure row) -
           cpu_s(row before the first measure row), divided by the t_s difference (info)
  timerq   threads.csv busy_pct of the row named rex::thread::TimerQueue (thread-cpu.ps1: thread CPU s / driver window
           s x 100; the driver window starts 1-3 s after the frame window and ends at the measure-end mark)
  arm      over the arm's runs: statistics.median (mean of the two middle values for even n), min, max; delta = arm
           median / reference median - 1; decision: better / worse only when every run of the arm lies outside the
           reference's min..max (fps higher = better, ms lower = better), else overlap; paired by round: per round
           arm / reference - 1, median over the rounds, rounds up (fps) / rounds faster (ms)
"""
import csv
import json
import math
import os
import statistics
import sys

sys.dont_write_bytecode = True
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
TQ_NAME = 'rex::thread::TimerQueue'

CFG = {
    'w4b': dict(
        title='W4b (Window 4b, matrix 20261122-1541)',
        matrix=os.path.join(REPO, 'build', 'agent8', 'matrix', '20261122-1541'),
        out=os.path.join(REPO, 'build', 'agent8', 'readout', 'w4b', 'xcheck'),
        addon=os.path.join(REPO, 'build', 'agent8', 'readout', 'w4b', 'w4b.json'),
        ref='d0', arms=['d0', 'B', 'd3', 'd11t'],
        sets=[('all', 'every scored run (16; B includes run 6 = 1551-B-r2, valid_timing=False)', None),
              ('no6', 'scored runs without run 6 (1551-B-r2) = valid_timing runs (15)', 'valid')],
        pairs=[('d11t', 'd0')]),
    'w5': dict(
        title='W5 (Window 5, matrix 20261122-1756)',
        matrix=os.path.join(REPO, 'build', 'agent8', 'matrix', '20261122-1756'),
        out=os.path.join(REPO, 'build', 'agent8', 'readout', 'w5', 'xcheck'),
        addon=os.path.join(REPO, 'build', 'agent8', 'readout', 'w5', 'w5.json'),
        ref='base', arms=['base', 's0', 'd11', 'd11t', 'd11p'],
        sets=[('all', 'every scored run (15, all valid_timing)', None)],
        pairs=[('d11', 's0'), ('d11t', 's0'), ('d11p', 's0'), ('d11t', 'd11'), ('d11p', 'd11'), ('d11p', 'd11t')]),
}


# ---------------------------------------------------------------- inputs

def read_perf(path):
    """Returns (header, rows [(end_offset, frame_time_us)], bad_rows, partial_tail, file_bytes)."""
    with open(path, 'rb') as fh:
        data = fh.read()
    parts = data.split(b'\n')
    header = [h.strip() for h in parts[0].rstrip(b'\r').decode('ascii', 'replace').split(',')]
    width = len(header)
    ci = header.index('frame_time_us')
    off = len(parts[0]) + 1
    rows, bad = [], 0
    for ln in parts[1:-1]:          # parts[-1] = text after the last newline (b'' when the file ends with one)
        off += len(ln) + 1
        fld = ln.rstrip(b'\r').split(b',')
        if len(fld) != width:
            bad += 1
            continue
        try:
            iv = [int(x) for x in fld]
        except ValueError:
            bad += 1
            continue
        rows.append((off, iv[ci]))
    return header, rows, bad, len(parts[-1]) > 0, len(data)


def load_json(path):
    try:
        with open(path, encoding='utf-8-sig') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def read_csv(path):
    if not os.path.isfile(path):
        return None
    with open(path, newline='', encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def fnum(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# ---------------------------------------------------------------- per run

def rank(s, num, den):
    n = len(s)
    k = (num * n + den - 1) // den
    return s[min(max(k, 1), n) - 1]


def run_stats(run_dir, rj):
    header, rows, bad, partial, nbytes = read_perf(os.path.join(run_dir, 'perf.csv'))
    start_b = rj['measure_start']['perf_csv_bytes']
    end_b = rj['measure_end']['perf_csv_bytes'] if rj.get('measure_end') else None
    seconds = float(rj['params']['seconds'])
    first = 0
    while first < len(rows) and rows[first][0] <= start_b:
        first += 1
    acc, n = 0, 0
    for _, v in rows[first:]:
        if acc >= seconds * 1e6:
            break
        acc += v if v > 0 else 0
        n += 1
    win = rows[first:first + n]
    ft = [v for _, v in win if v > 0]
    s = sorted(ft)
    m = len(s)
    tot = float(sum(s))
    k = max(1, m // 100)
    by_end = (sum(1 for e, _ in rows if e <= end_b) - first) if end_b is not None else None
    wall = rj.get('window_wall_s')
    return dict(
        rows_total=len(rows), bad_rows=bad, partial_tail=partial, file_bytes=nbytes,
        first_row=first, rows=n, zero_rows=n - m, short=acc < seconds * 1e6, rows_by_end_bytes=by_end,
        frames=m, window_s=tot / 1e6, fps=m * 1e6 / tot, fps_wall=(m / wall) if wall else None, window_wall_s=wall,
        mean_ms=tot / m / 1000.0,
        median_ms=rank(s, 1, 2) / 1000.0, p99_ms=rank(s, 99, 100) / 1000.0, p999_ms=rank(s, 999, 1000) / 1000.0,
        max_ms=s[-1] / 1000.0, low1_fps=1e6 * k / float(sum(s[-k:])), low1_k=k,
        over33=sum(1 for v in s if v > 33000), over100=sum(1 for v in s if v > 100000),
        light_share=sum(1 for v in s if v < 4500) / m)


def proc_cores(run_dir):
    rows = read_csv(os.path.join(run_dir, 'proc.csv'))
    if not rows:
        return dict(cores=None, cores_n=0, cores_slope=None)
    idx = [i for i, r in enumerate(rows) if r.get('phase') == 'measure' and fnum(r.get('cpu_cores')) is not None]
    if not idx:
        return dict(cores=None, cores_n=0, cores_slope=None)
    vals = [fnum(rows[i]['cpu_cores']) for i in idx]
    slope = None
    i0, i1 = idx[0] - 1, idx[-1]
    if i0 >= 0 and fnum(rows[i0].get('cpu_s')) is not None:
        dt = fnum(rows[i1]['t_s']) - fnum(rows[i0]['t_s'])
        if dt > 0:
            slope = (fnum(rows[i1]['cpu_s']) - fnum(rows[i0]['cpu_s'])) / dt
    return dict(cores=sum(vals) / len(vals), cores_n=len(vals), cores_slope=slope,
                cores_t0=fnum(rows[idx[0]]['t_s']), cores_t1=fnum(rows[i1]['t_s']))


def timerq(run_dir):
    rows = read_csv(os.path.join(run_dir, 'threads.csv'))
    if rows is None:
        return dict(tq_busy=None, tq_cpu_s=None, tq_max=None, tq_rows=0, tq_driver_s=None)
    hit = [r for r in rows if (r.get('name') or '').strip() == TQ_NAME]
    if not hit:
        return dict(tq_busy=None, tq_cpu_s=None, tq_max=None, tq_rows=0, tq_driver_s=None)
    busy = sum(fnum(r['busy_pct']) or 0 for r in hit)
    cpu = sum(fnum(r['cpu_s']) or 0 for r in hit)
    return dict(tq_busy=busy, tq_cpu_s=cpu, tq_max=max(fnum(r['max_busy_pct']) or 0 for r in hit), tq_rows=len(hit),
                tq_driver_s=(cpu / busy * 100.0) if busy else None)


# ---------------------------------------------------------------- comparisons

TOL_REL = 0.001     # 0.1 %
TOL_MS = 0.01       # 0.01 ms


def cmp(field, mine, other, kind):
    """None when within tolerance, else a text. kind: count (exact), ms (abs <= 0.01 ms and rel <= 0.1 %),
    rel (rel <= 0.1 %), share (abs <= 0.001)."""
    if mine is None or other is None:
        return None if (mine is None and other is None) else '%s: mine %s vs %s (one side missing)' % (field, mine, other)
    d = mine - other
    if kind == 'count':
        bad = d != 0
    elif kind == 'ms':
        bad = abs(d) > TOL_MS or (other and abs(d / other) > TOL_REL)
    elif kind == 'share':
        bad = abs(d) > 0.001
    else:
        bad = bool(other) and abs(d / other) > TOL_REL
    if not bad:
        return None
    rel = (' (%+.3f%%)' % (100.0 * d / other)) if other else ''
    return '%s: mine %.6g vs %.6g, diff %+.6g%s' % (field, mine, other, d, rel)


def shown_ok(mine, shown, nd):
    """True when `shown` (printed with nd decimals) is a correct rounding of `mine` (half a unit, both ways)."""
    return abs(mine - shown) <= 0.5 * 10 ** (-nd) + 1e-9


# ---------------------------------------------------------------- arms

def mmm(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return dict(med=statistics.median(vals), lo=min(vals), hi=max(vals), n=len(vals), mean=sum(vals) / len(vals))


def decide(arm_vals, ref_vals, higher_better):
    lo, hi = min(ref_vals), max(ref_vals)
    if higher_better:
        if all(v > hi for v in arm_vals):
            return 'better'
        if all(v < lo for v in arm_vals):
            return 'worse'
    else:
        if all(v < lo for v in arm_vals):
            return 'better'
        if all(v > hi for v in arm_vals):
            return 'worse'
    return 'overlap'


def paired(runs_a, runs_b, key):
    a = {r['round']: r[key] for r in runs_a if r[key] is not None}
    b = {r['round']: r[key] for r in runs_b if r[key] is not None}
    rounds = sorted(set(a) & set(b), key=int)
    rel = [(rd, a[rd] / b[rd] - 1.0) for rd in rounds]
    dif = [(rd, a[rd] - b[rd]) for rd in rounds]
    return dict(rounds=rounds, rel=rel, dif=dif,
                rel_med=statistics.median([d for _, d in rel]) if rel else None,
                dif_med=statistics.median([d for _, d in dif]) if dif else None,
                dif_lo=min([d for _, d in dif]) if dif else None, dif_hi=max([d for _, d in dif]) if dif else None,
                up=sum(1 for _, d in rel if d > 0), down=sum(1 for _, d in rel if d < 0), n=len(rel))


METRICS = (('fps', True, 1), ('median_ms', False, 3), ('p99_ms', False, 2), ('low1_fps', True, 1),
           ('cores', False, 2), ('tq_busy', False, 1))


def arm_block(runs, arm, ref):
    """Per-arm stats and deltas vs ref for one run set."""
    ra = [r for r in runs if r['arm'] == arm]
    rr = [r for r in runs if r['arm'] == ref]
    out = dict(arm=arm, ref=ref, n=len(ra), n_ref=len(rr), runs=[r['name'] for r in ra])
    for key, hb, _ in METRICS:
        st = mmm([r[key] for r in ra])
        out[key] = st
        if st and arm != ref:
            sr = mmm([r[key] for r in rr])
            out['d_' + key] = st['med'] / sr['med'] - 1.0 if sr else None
            out['dec_' + key] = decide([r[key] for r in ra if r[key] is not None],
                                       [r[key] for r in rr if r[key] is not None], hb) if sr else None
            out['pair_' + key] = paired(ra, rr, key)
    return out


# ---------------------------------------------------------------- formatting

def f(v, nd=2, dash='-'):
    return dash if v is None else '%.*f' % (nd, v)


def pct(v, nd=1):
    return '-' if v is None else '%+.*f%%' % (nd, 100.0 * v)


def rng(st, nd):
    return '-' if not st else '%s (%s..%s)' % (f(st['med'], nd), f(st['lo'], nd), f(st['hi'], nd))


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else 'w4b'
    dump = '--dump' in sys.argv
    cfg = CFG[label]
    os.makedirs(cfg['out'], exist_ok=True)
    res = read_csv(os.path.join(cfg['matrix'], 'results.csv'))
    runs, issues = [], []
    for row in res:
        run_dir = row['run_dir']
        name = os.path.basename(run_dir)
        rj = load_json(os.path.join(run_dir, 'run.json'))
        fj = load_json(os.path.join(run_dir, 'frames.json'))
        st = run_stats(run_dir, rj)
        st.update(proc_cores(run_dir))
        st.update(timerq(run_dir))
        st.update(seq=int(row['seq']), round=row['round'], arm=row['arm'], name=name,
                  scored=row['scored'] == 'True', valid=row['valid_timing'] == 'True',
                  cores_runjson=rj.get('window_cpu_cores_mean'), cores_runjson_n=rj.get('window_cpu_samples'))
        # runner checks
        probs = []
        w = fj['window']
        for fld, mine, oth, kind in (
                ('frames.json first_row', st['first_row'], w['first_row'], 'count'),
                ('frames.json rows', st['rows'], w['rows'], 'count'),
                ('frames.json zero_rows', st['zero_rows'], w['zero_rows'], 'count'),
                ('frames.json rows_by_end_bytes', st['rows_by_end_bytes'], w.get('rows_by_end_bytes'), 'count'),
                ('frames.json rows_total', st['rows_total'], fj['rows_total'], 'count'),
                ('frames.json bad_rows', st['bad_rows'], fj['bad_rows'], 'count'),
                ('frames.json frames', st['frames'], fj['frames'], 'count'),
                ('frames.json window_s', st['window_s'], fj['window_s'], 'rel'),
                ('frames.json mean_fps', st['fps'], fj['mean_fps'], 'rel'),
                ('frames.json median_ms', st['median_ms'], fj['median_ms'], 'ms'),
                ('frames.json p99_ms', st['p99_ms'], fj['p99_ms'], 'ms'),
                ('frames.json p99_9_ms', st['p999_ms'], fj['p99_9_ms'], 'ms'),
                ('frames.json max_ms', st['max_ms'], fj['max_ms'], 'ms'),
                ('frames.json over_33ms', st['over33'], fj['over_33ms'], 'count'),
                ('frames.json over_100ms', st['over100'], fj['over_100ms'], 'count'),
                ('frames.json share_lt_light', st['light_share'], fj.get('share_lt_light'), 'share'),
                ('results.csv frames', st['frames'], fnum(row['frames']), 'count'),
                ('results.csv window_s', st['window_s'], fnum(row['window_s']), 'rel'),
                ('results.csv fps_mean', st['fps'], fnum(row['fps_mean']), 'rel'),
                ('results.csv median_ms', st['median_ms'], fnum(row['median_ms']), 'ms'),
                ('results.csv p99_ms', st['p99_ms'], fnum(row['p99_ms']), 'ms'),
                ('results.csv p999_ms', st['p999_ms'], fnum(row['p999_ms']), 'ms'),
                ('results.csv max_ms', st['max_ms'], fnum(row['max_ms']), 'ms'),
                ('results.csv over33', st['over33'], fnum(row['over33']), 'count'),
                ('results.csv over100', st['over100'], fnum(row['over100']), 'count'),
                ('results.csv light_share', st['light_share'], fnum(row['light_share']), 'share'),
                ('results.csv cpu_cores_mean (vs my proc.csv mean)', st['cores'], fnum(row['cpu_cores_mean']), 'rel'),
                ('run.json window_cpu_cores_mean (vs my proc.csv mean)', st['cores'], st['cores_runjson'], 'rel'),
                ('run.json window_cpu_samples', st['cores_n'], st['cores_runjson_n'], 'count')):
            msg = cmp(fld, mine, oth, kind)
            if msg:
                probs.append(msg)
        st['runner_check'] = probs
        for p in probs:
            issues.append('%s: %s' % (name, p))
        runs.append(st)

    # add-on (Agent 8's read-out JSON) per-run comparison
    addon = load_json(cfg['addon'])
    addon_issues = []
    if addon:
        by = {r['name']: r for r in addon['runs']}
        for st in runs:
            a = by.get(st['name'])
            if not a or not a.get('stats'):
                addon_issues.append('%s: not in the add-on JSON' % st['name'])
                continue
            s2 = a['stats']
            for fld, mine, oth, kind in (('frames', st['frames'], s2.get('frames'), 'count'),
                                         ('window_s', st['window_s'], s2.get('window_s'), 'rel'),
                                         ('fps', st['fps'], s2.get('fps'), 'rel'),
                                         ('p50_ms', st['median_ms'], s2.get('p50_ms'), 'ms'),
                                         ('p99_ms', st['p99_ms'], s2.get('p99_ms'), 'ms'),
                                         ('low1_fps', st['low1_fps'], s2.get('low1_fps'), 'rel'),
                                         ('over33', st['over33'], s2.get('over33'), 'count'),
                                         ('game_cores (%s)' % a.get('game_src'), st['cores'], a.get('game_cores'), 'rel')):
                msg = cmp(fld, mine, oth, kind)
                if msg:
                    addon_issues.append('%s: add-on %s' % (st['name'], msg))
        if dump:
            print('ADDON arms keys', {k: (sorted(v.keys()) if isinstance(v, dict) else v) for k, v in list(addon['arms'].items())[:1]})
            print('ADDON deltas', json.dumps(addon['deltas'], default=str)[:3000])

    # arms
    scored = [r for r in runs if r['scored']]
    blocks = {}
    for set_id, set_txt, filt in cfg['sets']:
        rs = [r for r in scored if (filt is None or r[filt])]
        blocks[set_id] = dict(txt=set_txt, runs=rs, arms=[arm_block(rs, a, cfg['ref']) for a in cfg['arms']],
                              pairs=[arm_block(rs, a, b) for a, b in cfg['pairs']])

    write_outputs(label, cfg, runs, issues, addon, addon_issues, blocks)


def write_outputs(label, cfg, runs, issues, addon, addon_issues, blocks):
    out = cfg['out']
    # runs csv
    cols = ['seq', 'round', 'arm', 'name', 'scored', 'valid', 'first_row', 'rows', 'zero_rows', 'rows_by_end_bytes',
            'frames', 'window_s', 'window_wall_s', 'fps', 'fps_wall', 'mean_ms', 'median_ms', 'p99_ms', 'p999_ms',
            'max_ms', 'low1_fps', 'low1_k', 'over33', 'over100', 'light_share', 'cores', 'cores_n', 'cores_slope',
            'cores_runjson', 'tq_busy', 'tq_cpu_s', 'tq_max', 'tq_driver_s', 'runner_check']
    with open(os.path.join(out, 'xcheck_runs.csv'), 'w', newline='', encoding='utf-8') as fh:
        wr = csv.writer(fh)
        wr.writerow(cols)
        for r in runs:
            wr.writerow([('; '.join(r[c]) if c == 'runner_check' else
                          ('%.6f' % r[c] if isinstance(r[c], float) else r[c])) for c in cols])
    # arms csv
    with open(os.path.join(out, 'xcheck_arms.csv'), 'w', newline='', encoding='utf-8') as fh:
        wr = csv.writer(fh)
        wr.writerow(['set', 'kind', 'arm', 'vs', 'n', 'metric', 'median', 'min', 'max', 'mean', 'delta_vs_pct',
                     'decision', 'paired_median_pct', 'paired_up', 'paired_down', 'paired_rounds',
                     'paired_diff_median', 'per_round_pct'])
        for set_id, b in blocks.items():
            for kind, lst in (('arm', b['arms']), ('pair', b['pairs'])):
                for a in lst:
                    for key, _, _ in METRICS:
                        st = a[key]
                        if not st:
                            continue
                        p = a.get('pair_' + key)
                        wr.writerow([set_id, kind, a['arm'], a['ref'] if a['arm'] != a['ref'] else '', st['n'], key,
                                     '%.6f' % st['med'], '%.6f' % st['lo'], '%.6f' % st['hi'], '%.6f' % st['mean'],
                                     ('%.4f' % (100 * a['d_' + key])) if a.get('d_' + key) is not None else '',
                                     a.get('dec_' + key) or '',
                                     ('%.4f' % (100 * p['rel_med'])) if p and p['rel_med'] is not None else '',
                                     p['up'] if p else '', p['down'] if p else '', p['n'] if p else '',
                                     ('%.6f' % p['dif_med']) if p and p['dif_med'] is not None else '',
                                     ' '.join('r%s:%+.2f%%' % (rd, 100 * d) for rd, d in p['rel']) if p else ''])
    # markdown
    L = []
    w = L.append
    w('# Independent cross-check: %s' % cfg['title'])
    w('')
    w('- helper of Agent 8, own code: `build/agent8/readout/w4b/xcheck/xcheck.py %s` (stdlib, reads only; no runner/add-on code imported)' % label)
    w('- inputs: %s (results.csv, runs/*/perf.csv, run.json, frames.json, proc.csv, threads.csv); add-on JSON %s (read as data for the comparison)' % (cfg['matrix'], cfg['addon']))
    w('- reference arm: %s' % cfg['ref'])
    w('')
    w('## Definitions')
    w('')
    for ln in __doc__.split('Definitions', 1)[1].split('\n')[1:]:
        if ln.strip():
            w('    ' + ln.rstrip())
    w('')
    w('## Per run (cold included)')
    w('')
    w('| seq | round | arm | run | scored | valid | rows (first) | frames | window s | fps | fps_wall | median ms | p99 ms | p99.9 ms | max ms | 1% low fps (k) | >33 | >100 | game cores (n) | cores slope | run.json cores | TimerQueue busy % (max 1 s) | runner check |')
    w('|' + '---|' * 23)
    for r in runs:
        w('| %d | %s | %s | %s | %s | %s | %d (%d) | %d | %.3f | %.3f | %s | %.3f | %.3f | %.3f | %.3f | %.1f (%d) | %d | %d | %s (%d) | %s | %s | %s | %s |' % (
            r['seq'], r['round'] if r['scored'] else 'cold', r['arm'], r['name'], 'yes' if r['scored'] else 'no',
            'yes' if r['valid'] else 'NO', r['rows'], r['first_row'], r['frames'], r['window_s'], r['fps'],
            f(r['fps_wall'], 3), r['median_ms'], r['p99_ms'], r['p999_ms'], r['max_ms'], r['low1_fps'], r['low1_k'],
            r['over33'], r['over100'], f(r['cores'], 3), r['cores_n'], f(r['cores_slope'], 3), f(r['cores_runjson'], 3),
            ('%s (%s)' % (f(r['tq_busy'], 1), f(r['tq_max'], 1))) if r['tq_busy'] is not None else '- (no threads.csv)',
            'ok' if not r['runner_check'] else 'DIFF (%d)' % len(r['runner_check'])))
    w('')
    w('Runner check = every run compared with frames.json (first_row, rows, zero_rows, rows_by_end_bytes, rows_total, bad_rows, frames, window_s, mean_fps, median, p99, p99.9, max, >33, >100, share < 4.5 ms), results.csv (frames, window_s, fps_mean, median_ms, p99_ms, p999_ms, max_ms, over33, over100, light_share, cpu_cores_mean) and run.json (window_cpu_cores_mean, window_cpu_samples); tolerance: counts exact, ms |d| <= 0.01 ms and <= 0.1 %, others <= 0.1 %, shares <= 0.001.')
    w('')
    w('### Differences vs frames.json / results.csv / run.json above tolerance')
    w('')
    if issues:
        for i in issues:
            w('- ' + i)
    else:
        w('- none above tolerance (%d runs, %d fields each)' % (len(runs), 29))
    # max abs diffs info
    w('')
    w('### Differences vs the add-on JSON (Agent 8 read-out, per run: frames, window_s, fps, p50, p99, 1% low, >33, game cores)')
    w('')
    if addon is None:
        w('- add-on JSON not found')
    elif addon_issues:
        for i in addon_issues:
            w('- ' + i)
    else:
        w('- none above tolerance')
    for set_id, b in blocks.items():
        w('')
        w('## Arms: %s' % b['txt'])
        w('')
        w('| arm | n | runs | fps | median ms | p99 ms | 1% low fps | game cores (mean) | TimerQueue busy % |')
        w('|---|---|---|---|---|---|---|---|---|')
        for a in b['arms']:
            w('| %s%s | %d | %s | %s | %s | %s | %s | %s (%s) | %s |' % (
                a['arm'], ' (ref)' if a['arm'] == a['ref'] else '', a['n'], ', '.join(a['runs']), rng(a['fps'], 1),
                rng(a['median_ms'], 3), rng(a['p99_ms'], 2), rng(a['low1_fps'], 1), rng(a['cores'], 2),
                f(a['cores']['mean'], 3) if a['cores'] else '-', rng(a['tq_busy'], 1)))
        w('')
        w('Deltas vs %s (arm median / ref median - 1; decision: better/worse only when every run lies outside the ref min..max)' % cfg['ref'])
        w('')
        w('| arm | n vs n | d fps | d median | d p99 | d 1% low | d game cores | paired fps by round: median (up / rounds); per round | paired median ms: median rel (faster / rounds); median diff ms (min..max) | paired game cores: median rel; median diff (min..max); per round |')
        w('|---|---|---|---|---|---|---|---|---|---|')
        for a in b['arms']:
            if a['arm'] == a['ref']:
                continue
            w(fmt_delta(a))
        if b['pairs']:
            w('')
            w('Extra pairs (same rules; first arm vs second arm)')
            w('')
            w('| arm vs | n vs n | d fps | d median | d p99 | d 1% low | d game cores | paired fps by round: median (up / rounds); per round | paired median ms: median rel (faster / rounds); median diff ms (min..max) | paired game cores: median rel; median diff (min..max); per round |')
            w('|---|---|---|---|---|---|---|---|---|---|')
            for a in b['pairs']:
                w(fmt_delta(a, show_vs=True))
    with open(os.path.join(out, 'xcheck_core.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')
    with open(os.path.join(out, 'xcheck_data.json'), 'w', encoding='utf-8') as fh:
        json.dump(dict(runs=runs, blocks={k: dict(txt=v['txt'], arms=v['arms'], pairs=v['pairs'])
                                          for k, v in blocks.items()}, issues=issues, addon_issues=addon_issues),
                  fh, indent=1, default=str)
    print('\n'.join(L))


def fmt_delta(a, show_vs=False):
    pf, pm, pc = a['pair_fps'], a['pair_median_ms'], a['pair_cores']
    return '| %s | %d vs %d | %s %s | %s %s | %s %s | %s %s | %s %s | %s (%d / %d); %s | %s (%d / %d); %s (%s..%s) | %s; %s (%s..%s); %s |' % (
        ('%s vs %s' % (a['arm'], a['ref'])) if show_vs else a['arm'], a['n'], a['n_ref'],
        pct(a['d_fps']), a['dec_fps'], pct(a['d_median_ms']), a['dec_median_ms'], pct(a['d_p99_ms']), a['dec_p99_ms'],
        pct(a['d_low1_fps']), a['dec_low1_fps'], pct(a.get('d_cores')), a.get('dec_cores') or '',
        pct(pf['rel_med']), pf['up'], pf['n'], ' '.join('r%s %s' % (rd, pct(d)) for rd, d in pf['rel']),
        pct(pm['rel_med']), pm['down'], pm['n'], f(pm['dif_med'], 3), f(pm['dif_lo'], 3), f(pm['dif_hi'], 3),
        pct(pc['rel_med']) if pc else '-', f(pc['dif_med'], 3) if pc else '-', f(pc['dif_lo'], 3) if pc else '-',
        f(pc['dif_hi'], 3) if pc else '-', ' '.join('r%s %s' % (rd, pct(d)) for rd, d in pc['rel']) if pc else '-')


if __name__ == '__main__':
    main()
