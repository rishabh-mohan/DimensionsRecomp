#!/usr/bin/env python3
"""W4b noise methods (Agent 7, task #6, was #30): ways to shrink d0's run-to-run band (W4b: +-19.6 % on the run medians of
the frame time), applied read-only to a run-matrix.ps1 output dir.

Usage:
  python -B build\\agent7\\w4b-noise\\noise_methods.py [DIR] [-o OUT.md] [--json OUT.json] [--all]
         [--emhz 800] [--min-rows 3] [--guard-s 1.5] [--roll 201] [--heavy-ms 5.0] [--roll-guard-s 0.5]
         [--trim 0.2] [--bin-s 10]

DIR defaults to build\\agent8\\matrix\\20261122-1541 (W4b). It writes only -o and --json (no __pycache__).

Kept runs: scored, valid timing (--all keeps the others), not excluded, with a perf.csv scored window. Every number
is over the runner's own scored window (frames.json window.first_row / rows of perf.csv frame_time_us, frames <= 0
left out), with bench\\agent7\\w4b_readout\\w4b_readout.py's loaders and definitions: fps = frames / summed frame
time; p50, p99 nearest-rank; 1% low = 1000 / mean of the slowest max(1, n // 100) frame times.

Methods. Each gives per-run values; d0's band as summary.md defines it, (max - min) / median of d0's run values; a
pooled 95 % band; and each arm's delta against d0.
  raw       the run-matrix numbers over the whole window (median ms gives summary.md's +-19.6 %).
  A         phase-matched. Each frame gets the CPU state at its end time (measure_start.epoch_s + summed frame
            time): S = Agent 11's slow state (sys.csv e_eff_mhz < --emhz for >= --min-rows samples in a row; a
            sample covers the interval since the previous sample), F = the rest. Frames within --guard-s of a state
            change, or in a shorter low stretch, are left out. Per run: h = the S share of the classified time;
            A-heavy = the S frames only; A-light = the F frames only; A-std = both mixed at one fixed share h_ref
            (the median h of the kept runs): fps = (1 - h_ref) fps_F + h_ref fps_S; p50, p99 and 1% low over the
            frames weighted so that F fills (1 - h_ref) and S h_ref of the time.
  A2        cross-check of A with a frame-time classifier: S = the centred rolling median of --roll frames >
            --heavy-ms; frames within --roll-guard-s of a switch are left out.
  B         paired within rounds. Per round 100 (arm - d0) / d0; per arm the median over rounds, the range and a
            95 % t band of the mean. B-norm: each run divided by the geometric mean of its round's kept runs, then
            the summary.md band on d0. On raw, A-std, A-heavy and T-std.
            B-block: the two-way model ln v = arm + round, fitted as the ANCOVA below on round dummies; its CI has
            the right df (runs - arms - rounds + 1). B-norm's pooled CI uses runs - arms, so it is too narrow.
  C         trimmed means. C-frames: the --trim trimmed mean frame time per run (fps = 1e6 / it); C-bins: the
            --trim trimmed mean of the run's --bin-s bin values (5 bins: the middle 3).
  T         the runner's own light / heavy split (frames.json light_ms, 4.5 ms; its share_lt_light): T-light =
            the frames < light_ms only, T-heavy = the rest, T-std = both mixed at hT_ref (the median heavy time
            share of the kept runs), as A-std.
  L         ANCOVA: ln(raw value) on the light share (share of frames < light_ms) with the arm as a factor; each
            run is adjusted to the mean light share. The light share comes from the frame times themselves, so L
            hides any effect an arm has on the slow-frame share (the read-out must show the share per arm too).
  D         ANCOVA on sys.json's window host state: E-core MHz, P-core util, both, and the non-game CPU load
            (cpu_util x --cpus - the game's cpu_cores_mean). P util and the cores include the game's own CPU.
  ANCOVA (L, D): SD = residual SD of ln(value), df = runs - arms - covariates; the CI of a delta includes the
            covariate-difference term; the band is summary.md's on the reference arm's adjusted values; F = a
            one-way ANOVA of each covariate on the arm (large F: the covariate moves with the arm).
Pooled 95 % band: s = the pooled within-arm SD of ln(value) over the kept runs, df = runs - arms; for arm vs d0
the geometric-mean delta with exp(+-t(0.975, df) s sqrt(1/n_arm + 1/n_d0)) - 1; "4 vs 4" is that band for two
arms of 4 runs.
Stdlib only, one thread.
"""
import argparse
import bisect
import importlib.util
import json
import math
import os
import statistics
import sys

sys.dont_write_bytecode = True  # no __pycache__ here or next to the imported tools

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
READOUT = os.path.join(REPO, 'bench', 'agent7', 'w4b_readout', 'w4b_readout.py')
DEFAULT_DIR = os.path.join(REPO, 'build', 'agent8', 'matrix', '20261122-1541')
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
        20: 2.086, 25: 2.060, 30: 2.042}
# (key, +1 = higher is better / -1 = lower is better, label, decimals)
METRICS = (('fps', 1, 'fps', 1), ('p50_ms', -1, 'median ms', 3), ('p99_ms', -1, 'p99 ms', 2),
           ('low1_fps', 1, '1% low fps', 1))
# (id, label, per-run field)
METHODS = (('raw', 'raw: whole window (the run-matrix numbers)', 'raw'),
           ('A-std', 'A: phase-matched, sys.csv slow state, mixed at h_ref', 'a_std'),
           ('A-heavy', 'A: slow-state (heavy) frames only', 'a_S'),
           ('A-light', 'A: fast-state (light) frames only', 'a_F'),
           ('A2-std', 'A2: phase-matched, frame-time classifier, mixed at h2_ref', 'a2_std'),
           ('A2-heavy', 'A2: heavy frames only, frame-time classifier', 'a2_S'),
           ('A2-light', 'A2: light frames only, frame-time classifier', 'a2_F'),
           ('T-std', 'T: runner split at light_ms, mixed at hT_ref', 't_std'),
           ('T-light', 'T: frames < light_ms only', 't_L'),
           ('T-heavy', 'T: frames >= light_ms only', 't_H'),
           ('C-frames', 'C: trimmed mean frame time per run', 'c_frames'),
           ('C-bins', 'C: trimmed mean of the bins per run', 'c_bins'))
PAIRED_FROM = (('raw', 'raw'), ('a_std', 'A-std'), ('a_S', 'A-heavy'), ('t_std', 'T-std'))
# (id, label, covariate keys of x['cov']); ANCOVA of ln(raw value) with the arm as a factor
COVARIATES = (('L-ls', 'L: ANCOVA on the light share (frames < light_ms)', ('ls_T',)),
              ('D-emhz', 'D: ANCOVA on sys.json E-core MHz', ('e_mhz',)),
              ('D-putil', 'D: ANCOVA on sys.json P-core util', ('p_util',)),
              ('D-emhz+putil', 'D: ANCOVA on E-core MHz and P-core util', ('e_mhz', 'p_util')),
              ('D-nongame', 'D: ANCOVA on the non-game CPU load', ('nongame',)))
COV_INFO = ('ls_T', 'e_mhz', 'p_util', 'nongame', 'e_util', 'cores')


def load_module(name, path):
    """Import a tool by its path (sys.dont_write_bytecode is set, so no .pyc is written next to it)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


W = load_module('w4b_readout', READOUT)
num = W.num


def t975(df):
    """Two-sided 95 % Student t quantile (table; between entries the smaller df, i.e. the wider band)."""
    if df is None or df < 1:
        return None
    if df > 30:
        return 1.96 + (T975[30] - 1.96) * 30.0 / df
    return T975[max(k for k in T975 if k <= df)]


def trimmed_mean(v, p):
    """Mean after dropping floor(p * n) values at each end (all values when that leaves none)."""
    s = sorted(v)
    n = len(s)
    if not n:
        return None
    k = int(math.floor(p * n + 1e-9))
    core = s[k:n - k] if n - 2 * k > 0 else s
    return sum(core) / float(len(core))


def read_sys(rd):
    """sys.csv samples [(epoch_s, e_eff_mhz)] sorted by time, or None without sys.csv."""
    rows = W.read_rows(os.path.join(rd, 'sys.csv')) if rd else None
    if rows is None:
        return None
    return sorted((t, e) for t, e in ((num(r.get('epoch_s')), num(r.get('e_eff_mhz'))) for r in rows)
                  if t is not None and e is not None)


def sys_spans(pts, emhz, min_rows):
    """Agent 11's slow state on sys.csv samples [(epoch, e_eff_mhz)]; a sample covers (previous epoch, epoch].
    Returns (slow, short, cover): slow = [(a, b)] stretches of >= min_rows low samples (e_eff_mhz < emhz) in a row;
    short = shorter low stretches (ambiguous); cover = (first epoch, last epoch), None with < 2 samples."""
    if not pts or len(pts) < 2:
        return [], [], None
    slow, short, cur = [], [], []
    seq = list(zip(pts, pts[1:])) + [((None, None), (None, None))]
    for (t0, _), (t1, e) in seq:
        if e is not None and e < emhz:
            cur.append((t0, t1))
            continue
        if cur:
            (slow if len(cur) >= min_rows else short).append((cur[0][0], cur[-1][1]))
        cur = []
    return slow, short, (pts[0][0], pts[-1][0])


def near_any(t, xs):
    """Distance from t to the nearest value of the sorted list xs (inf when it is empty)."""
    i = bisect.bisect_left(xs, t)
    return min([abs(t - xs[j]) for j in (i - 1, i) if 0 <= j < len(xs)] or [float('inf')])


def label_sys(ends, ms_e, spans, guard_s):
    """Per frame 'S' (slow state), 'F' (fast) or None (outside sys.csv, in a short low stretch, or within guard_s of
    a state change); ends = frame end times in s from the window start, ms_e = the window start epoch."""
    slow, short, cover = spans
    if cover is None or ms_e is None:
        return None
    bounds = sorted(x for a, b in slow + short for x in (a, b))
    out = []
    for c in ends:
        t = ms_e + c
        if t <= cover[0] or t > cover[1] or near_any(t, bounds) < guard_s or any(a < t <= b for a, b in short):
            out.append(None)
        elif any(a < t <= b for a, b in slow):
            out.append('S')
        else:
            out.append('F')
    return out


def label_roll(ft, ends, k, heavy_ms, guard_s):
    """Frame-time classifier: 'S' where the centred rolling median of k frames exceeds heavy_ms, else 'F'; None
    within guard_s of a switch. Returns (labels, switches, rolling medians in ms)."""
    n = len(ft)
    h = max(0, int(k) // 2)
    thr = heavy_ms * 1000.0
    win, lo, hi, raw, meds = [], 0, 0, [], []
    for i in range(n):
        a, b = max(0, i - h), min(n, i + h + 1)
        while hi < b:
            bisect.insort(win, ft[hi])
            hi += 1
        while lo < a:
            del win[bisect.bisect_left(win, ft[lo])]
            lo += 1
        m = win[len(win) // 2]
        meds.append(m / 1000.0)
        raw.append('S' if m > thr else 'F')
    sw = [ends[i - 1] for i in range(1, n) if raw[i] != raw[i - 1]]
    out = [None if near_any(ends[i], sw) < guard_s else raw[i] for i in range(n)]
    return out, len(sw), meds


def split(ft, lab):
    """(F frames, S frames) of a labelled window; (None, None) without labels."""
    if not lab:
        return None, None
    return [v for v, l in zip(ft, lab) if l == 'F'], [v for v, l in zip(ft, lab) if l == 'S']


def std_mix(F, S, h_ref):
    """F and S frames mixed so that F fills (1 - h_ref) and S h_ref of the time: fps; weighted nearest-rank p50 / p99
    (the smallest frame time whose cumulative weight reaches the share); 1% low = 1000 / weighted mean of the slowest
    1 % of the weight; >33 ms per minute mixed the same way. None without F or S frames."""
    if not F or not S or h_ref is None:
        return None
    TF, TS = float(sum(F)), float(sum(S))
    wF, wS = (1.0 - h_ref) / TF, h_ref / TS
    items = sorted([(v, wF) for v in F] + [(v, wS) for v in S])
    tot = (1.0 - h_ref) * len(F) / TF + h_ref * len(S) / TS

    def wq(q):
        acc = 0.0
        for v, wt in items:
            acc += wt
            if acc >= q * tot * (1.0 - 1e-12):
                return v
        return items[-1][0]

    need, acc, sx = 0.01 * tot, 0.0, 0.0
    for v, wt in reversed(items):
        if acc >= need:
            break
        take = min(wt, need - acc)
        acc += take
        sx += take * v
    slow_us = W.SLOW_MS * 1000.0
    o33F, o33S = sum(1 for v in F if v > slow_us), sum(1 for v in S if v > slow_us)
    return {'fps': 1e6 * tot, 'p50_ms': wq(0.5) / 1000.0, 'p99_ms': wq(0.99) / 1000.0,
            'low1_fps': 1e6 * acc / sx if sx > 0 else None,
            'over33_min': (1.0 - h_ref) * o33F * 6e7 / TF + h_ref * o33S * 6e7 / TS, 'h_ref': h_ref}


def agreement(l1, l2):
    """Share of the frames labelled by both classifiers on which they agree."""
    if not l1 or not l2:
        return None
    both = [(p, q) for p, q in zip(l1, l2) if p is not None and q is not None]
    return (sum(1 for p, q in both if p == q) / float(len(both))) if both else None


def run_metrics(x, rd, a):
    """Every per-run number of every method (adds keys to x; _F/_S/_F2/_S2/_meds are temporary frame lists)."""
    rj = W.load_json(os.path.join(rd, 'run.json')) if rd else None
    rj = rj if isinstance(rj, dict) else {}
    fj = W.load_json(os.path.join(rd, 'frames.json')) if rd else None
    fj = fj if isinstance(fj, dict) else {}
    win = fj.get('window') if isinstance(fj.get('window'), dict) else None
    src, col = fj.get('source'), fj.get('column')
    if not win or not col:
        return
    base = os.path.basename(str(fj.get('file') or ''))
    fpath = os.path.join(rd, base) if base else ''
    if not os.path.isfile(fpath):
        fpath = str(fj.get('file') or '')
    first, nrows = int(num(win.get('first_row')) or 0), int(num(win.get('rows')) or 0)
    if not (nrows and os.path.isfile(fpath)):
        return
    _, fts, _ = W.load_frames(fpath, src, col, num(fj.get('scale_to_us')) or 1.0, (), stop_after=first + nrows)
    ft = [v for v in fts[first:first + nrows] if v > 0]
    if not ft:
        return
    ends, c = [], 0.0
    for v in ft:
        c += v
        ends.append(c / 1e6)
    x['raw'] = W.window_stats(ft)
    x['window_s'] = c / 1e6
    # A: the sys.csv slow state per frame
    ms = rj.get('measure_start') if isinstance(rj.get('measure_start'), dict) else {}
    ms_e = num(ms.get('epoch_s'))
    pts = read_sys(rd)
    spans = sys_spans(pts or [], a.emhz, a.min_rows)
    lab = label_sys(ends, ms_e, spans, a.guard_s)
    x['sys_csv'] = pts is not None
    if lab is not None:
        F, S = split(ft, lab)
        x['_F'], x['_S'] = F, S
        x['a_F'], x['a_S'] = W.window_stats(F), W.window_stats(S)
        tf, ts = sum(F) / 1e6, sum(S) / 1e6
        x['F_s'], x['S_s'], x['drop_s'] = tf, ts, x['window_s'] - tf - ts
        x['h'] = ts / (tf + ts) if tf + ts > 0 else None
        wend = ms_e + x['window_s']
        x['slow_spans_win'] = [(max(0.0, s0 - ms_e), min(x['window_s'], s1 - ms_e))
                               for s0, s1 in spans[0] if s1 > ms_e and s0 < wend]
        later = [s0 - ms_e for s0, s1 in spans[0] if s1 > ms_e]
        x['onset_win_s'] = later[0] if later else None
        x['short_lows_win'] = sum(1 for s0, s1 in spans[1] if s1 > ms_e and s0 < wend)
    # A2: the frame-time classifier
    lab2, nsw, meds = label_roll(ft, ends, a.roll, a.heavy_ms, a.roll_guard_s)
    F2, S2 = split(ft, lab2)
    x['_F2'], x['_S2'], x['_meds'] = F2, S2, meds
    x['a2_F'], x['a2_S'] = W.window_stats(F2), W.window_stats(S2)
    tf2, ts2 = sum(F2) / 1e6, sum(S2) / 1e6
    x['h2'] = ts2 / (tf2 + ts2) if tf2 + ts2 > 0 else None
    x['switches2'] = nsw
    x['agree'] = agreement(lab, lab2)
    # C: trimmed means
    tm = trimmed_mean(ft, a.trim)
    x['c_frames'] = {'fps': 1e6 / tm} if tm else None
    good = [b for b in W.stat_bins(ft, a.bin_s) if b.get('frames')]
    x['c_bins'] = ({k: trimmed_mean([b[k] for b in good], a.trim) for k in ('fps', 'p99_ms', 'low1_fps')}
                   if len(good) >= 3 else None)
    x['bins_n'] = len(good)
    # T: the runner's light / heavy split at light_ms (frames.json light_ms; share_lt_light is its frame share)
    lms = a.light_ms if a.light_ms else (num(fj.get('light_ms')) or 4.5)
    thr = lms * 1000.0
    TL, TH = [v for v in ft if v < thr], [v for v in ft if v >= thr]
    x['light_ms'] = lms
    x['_TL'], x['_TH'] = TL, TH
    x['t_L'], x['t_H'] = W.window_stats(TL), W.window_stats(TH)
    x['ls_T'] = len(TL) / float(len(ft))
    x['hT'] = sum(TH) / float(sum(ft))
    x['ls_runner'] = num(fj.get('share_lt_light'))
    # D: host state over the scored window (sys.json 'window')
    sj = W.load_json(os.path.join(rd, 'sys.json'))
    sw = sj.get('window') if isinstance(sj, dict) and isinstance(sj.get('window'), dict) else {}
    cores, cu = x.get('cores_csv'), num(sw.get('cpu_util_mean'))
    x['cov'] = {'ls_T': x['ls_T'], 'e_mhz': num(sw.get('e_eff_mhz_mean')), 'p_util': num(sw.get('p_util_mean')),
                'e_util': num(sw.get('e_util_mean')), 'cpu_util': cu, 'cores': cores,
                'nongame': (cu / 100.0 * a.cpus - cores) if cu is not None and cores is not None else None}


def load_runs(d, a):
    rows = W.read_rows(os.path.join(d, 'results.csv'))
    if rows is None:
        raise SystemExit('no results.csv in %s' % d)
    mj = W.load_json(os.path.join(d, 'matrix.json')) or {}
    cfg = [x for x in (mj.get('arms') or []) if isinstance(x, dict) and x.get('id')]
    ids = [x['id'] for x in cfg]
    present = list(dict.fromkeys(r.get('arm', '') for r in rows))
    order = [i for i in ids if i in present] + [p for p in present if p not in ids]
    ref = next((x['id'] for x in cfg if x.get('ref') and x['id'] in present), None)
    if ref is None:
        ref = mj.get('reference') if mj.get('reference') in present else (order[0] if order else None)
    hist, runs = {}, []
    for r in rows:
        rd = W.resolve_run_dir(d, r)
        x = {'seq': r.get('seq'), 'round': r.get('round'), 'arm': r.get('arm', ''), 'rep': r.get('rep'),
             'name': os.path.basename(rd.rstrip('\\/')) if rd else '',
             'scored': (r.get('scored') or '').strip().lower() == 'true',
             'valid': (r.get('valid_timing') or '').strip().lower() == 'true',
             'excluded': (r.get('excluded') or '').strip().lower() == 'true', 'keep': False, 'why': [],
             'light_share_csv': num(r.get('light_share')), 'cores_csv': num(r.get('cpu_cores_mean'))}
        if rd and os.path.isdir(rd):
            run_metrics(x, rd, a)
        x['keep'] = x['scored'] and (x['valid'] or a.all) and not x['excluded'] and x.get('raw') is not None
        if not x['scored']:
            x['why'].append('cold (unscored)')
        if not x['valid']:
            x['why'].append('not valid timing%s' % (' (kept: --all)' if a.all else ''))
        if x['excluded']:
            x['why'].append('excluded')
        if x.get('raw') is None:
            x['why'].append('no scored frame window')
        meds = x.pop('_meds', None) or []
        if x['keep']:
            for m in meds:
                b = int(m / 0.5)
                hist[b] = hist.get(b, 0) + 1
        runs.append(x)
    return runs, order, ref, mj.get('title', ''), hist


def collect(runs, val, key):
    """{arm: [(run, value)]} over the runs with a value > 0."""
    out = {}
    for x in runs:
        v = val(x, key)
        if v is not None and v > 0:
            out.setdefault(x['arm'], []).append((x, v))
    return out


def summarize(vals, ref, order, sign):
    """summary.md's band on the reference arm, the pooled within-arm SD of ln(value), and per arm the median delta
    (verdict against the band) and the geometric-mean delta with its pooled 95 % CI."""
    if ref not in vals:
        return None
    rv = [v for _, v in vals[ref]]
    rmed = statistics.median(rv)
    band = 100.0 * (max(rv) - min(rv)) / rmed if rmed else None
    ss, df = 0.0, 0
    for lst in vals.values():
        lv = [math.log(v) for _, v in lst]
        if len(lv) >= 2:
            m = statistics.fmean(lv)
            ss += sum((u - m) ** 2 for u in lv)
            df += len(lv) - 1
    sd = math.sqrt(ss / df) if df else None
    t = t975(df) if df else None
    lref = statistics.fmean([math.log(v) for v in rv])
    arms = {}
    for arm in order:
        if arm not in vals:
            continue
        av = [v for _, v in vals[arm]]
        am = statistics.median(av)
        e = {'n': len(av), 'vals': av, 'runs': [x['name'] for x, _ in vals[arm]], 'med': am, 'lo': min(av),
             'hi': max(av)}
        if arm != ref:
            dp = 100.0 * (am - rmed) / rmed
            e['delta_pct'] = dp
            if band is None or abs(dp) <= band:
                e['verdict'] = 'within'
            else:
                e['verdict'] = 'better' if (dp > 0) == (sign > 0) else 'worse'
            dl = statistics.fmean([math.log(v) for v in av]) - lref
            e['gm_delta_pct'] = 100.0 * (math.exp(dl) - 1.0)
            if sd is not None and t is not None:
                hw = t * sd * math.sqrt(1.0 / len(av) + 1.0 / len(rv))
                e['ci_pct'] = (100.0 * (math.exp(dl - hw) - 1.0), 100.0 * (math.exp(dl + hw) - 1.0))
                e['ci_excludes_0'] = (dl - hw > 0) or (dl + hw < 0)
        arms[arm] = e
    hw44 = 100.0 * (math.exp(t * sd * math.sqrt(0.5)) - 1.0) if sd is not None and t is not None else None
    return {'ref': ref, 'ref_vals': rv, 'ref_med': rmed, 'band_pct': band, 'sd_ln': sd,
            'cv_pct': 100.0 * sd if sd is not None else None, 'df': df, 'hw44_pct': hw44, 'arms': arms}


def paired(runs, val, key, ref, order):
    """Per arm: the within-round deltas 100 (arm - ref) / ref, their median, range, mean and 95 % t band."""
    byr = {}
    for x in runs:
        v = val(x, key)
        if v is not None:
            byr.setdefault(x['round'], {})[x['arm']] = v
    out = {}
    for arm in order:
        if arm == ref:
            continue
        rr = [(rnd, r[arm], r[ref]) for rnd, r in sorted(byr.items(), key=lambda kv: num(kv[0]) or 0)
              if arm in r and ref in r and r[ref]]
        if not rr:
            continue
        ds = [100.0 * (av - rv) / rv for _, av, rv in rr]
        n = len(ds)
        sd = statistics.stdev(ds) if n >= 2 else None
        t = t975(n - 1) if n >= 2 else None
        out[arm] = {'n': n, 'rounds': [rnd for rnd, _, _ in rr], 'deltas': ds, 'med': statistics.median(ds),
                    'mean': statistics.fmean(ds), 'range': max(ds) - min(ds), 'sd': sd,
                    'hw95': (t * sd / math.sqrt(n)) if sd is not None and t is not None else None,
                    'up': sum(1 for q in ds if q > 0)}
    return out


def round_norm(runs, val, key):
    """{run name: value / geometric mean of the values of its round's runs}."""
    byr = {}
    for x in runs:
        v = val(x, key)
        if v is not None and v > 0:
            byr.setdefault(x['round'], []).append((x['name'], v))
    out = {}
    for lst in byr.values():
        g = math.exp(statistics.fmean([math.log(v) for _, v in lst]))
        for name, v in lst:
            out[name] = v / g
    return out


def round_block(runs):
    """(rounds, cov) for the two-way model ln v = arm + round: cov(run) = the dummies of the run's round (the first
    round is the base), to be fitted with ancova()."""
    rounds = sorted(set(x['round'] for x in runs), key=lambda r: (num(r) is None, num(r) or 0, str(r)))
    return rounds, (lambda x: [1.0 if x['round'] == r else 0.0 for r in rounds[1:]])


def solve(A, c):
    """x with A x = c for a small square system (Gauss-Jordan, partial pivoting); None when singular."""
    k = len(c)
    M = [[float(v) for v in A[i]] + [float(c[i])] for i in range(k)]
    for col in range(k):
        piv = max(range(col, k), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            return None
        M[col], M[piv] = M[piv], M[col]
        for r in range(k):
            if r != col:
                q = M[r][col] / M[col][col]
                for j in range(col, k + 1):
                    M[r][j] -= q * M[col][j]
    return [M[i][k] / M[i][i] for i in range(k)]


def inverse(A):
    """Inverse of a small square matrix, None when singular."""
    k = len(A)
    cols = [solve(A, [1.0 if i == j else 0.0 for i in range(k)]) for j in range(k)]
    if any(c is None for c in cols):
        return None
    return [[cols[j][i] for j in range(k)] for i in range(k)]


def ancova(vals, cov, ref, order, sign):
    """Pooled within-arm OLS of ln(value) on the covariates cov(run) (a list) with the arm as a factor. Returns
    summarize() over the adjusted values exp(ln v - (x - mean x) . b), with sd_ln, df (runs - arms - covariates),
    hw44 and each arm's CI (with the covariate-difference term) redone for the fitted slopes; plus b (slopes on ln
    value), k and n_dropped (runs without every covariate). None when it can't be fitted."""
    keep, dropped = {}, 0
    for arm, lst in vals.items():
        for x, v in lst:
            c = cov(x)
            if c is None or any(u is None for u in c):
                dropped += 1
                continue
            keep.setdefault(arm, []).append((x, v, [float(u) for u in c]))
    if ref not in keep:
        return None
    allr = [t for lst in keep.values() for t in lst]
    n, G, k = len(allr), len(keep), len(allr[0][2])
    df = n - G - k
    if df < 1:
        return None
    my = dict((arm, statistics.fmean([math.log(v) for _, v, _ in lst])) for arm, lst in keep.items())
    mx = dict((arm, [statistics.fmean([c[i] for _, _, c in lst]) for i in range(k)]) for arm, lst in keep.items())
    Sxx, Sxy = [[0.0] * k for _ in range(k)], [0.0] * k
    for arm, lst in keep.items():
        for _, v, c in lst:
            dx = [c[i] - mx[arm][i] for i in range(k)]
            dy = math.log(v) - my[arm]
            for i in range(k):
                Sxy[i] += dx[i] * dy
                for j in range(k):
                    Sxx[i][j] += dx[i] * dx[j]
    b, Sinv = solve(Sxx, Sxy), inverse(Sxx)
    if b is None or Sinv is None:
        return None
    xbar = [statistics.fmean([c[i] for _, _, c in allr]) for i in range(k)]
    adj = dict((arm, [(x, math.exp(math.log(v) - sum((c[i] - xbar[i]) * b[i] for i in range(k)))) for x, v, c in lst])
               for arm, lst in keep.items())
    s = summarize(adj, ref, order, sign)
    if s is None or s['sd_ln'] is None:
        return None
    sd = math.sqrt(s['sd_ln'] ** 2 * s['df'] / df)  # summarize's df is runs - arms
    t = t975(df)
    for arm, e in s['arms'].items():
        if arm == ref or e.get('gm_delta_pct') is None:
            continue
        d = [mx[arm][i] - mx[ref][i] for i in range(k)]
        q = sum(d[i] * Sinv[i][j] * d[j] for i in range(k) for j in range(k))
        dl = math.log(1.0 + e['gm_delta_pct'] / 100.0)
        hw = t * sd * math.sqrt(1.0 / e['n'] + 1.0 / len(keep[ref]) + q)
        e['ci_pct'] = (100.0 * (math.exp(dl - hw) - 1.0), 100.0 * (math.exp(dl + hw) - 1.0))
        e['ci_excludes_0'] = (dl - hw > 0) or (dl + hw < 0)
    s.update(sd_ln=sd, cv_pct=100.0 * sd, df=df, hw44_pct=100.0 * (math.exp(t * sd * math.sqrt(0.5)) - 1.0), b=b,
             k=k, n_dropped=dropped)
    return s


def covariate_info(kept, order, keys):
    """Per covariate: arm means and a one-way ANOVA F of the covariate on the arm (with its df)."""
    out = {}
    for key in keys:
        g = {}
        for x in kept:
            v = (x.get('cov') or {}).get(key)
            if v is not None:
                g.setdefault(x['arm'], []).append(v)
        allv = [v for lst in g.values() for v in lst]
        if len(g) < 2 or len(allv) <= len(g):
            continue
        m = statistics.fmean(allv)
        ssb = sum(len(lst) * (statistics.fmean(lst) - m) ** 2 for lst in g.values())
        ssw = sum(sum((v - statistics.fmean(lst)) ** 2 for v in lst) for lst in g.values())
        dfb, dfw = len(g) - 1, len(allv) - len(g)
        out[key] = {'means': dict((arm, statistics.fmean(g[arm])) for arm in order if arm in g),
                    'F': (ssb / dfb) / (ssw / dfw) if ssw > 0 else None, 'df': [dfb, dfw], 'n': len(allv)}
    return out


def getter(field):
    return lambda x, k: (x.get(field) or {}).get(k)


def analyse(d, a, command):
    d = os.path.abspath(d)
    runs, order, ref, title, hist = load_runs(d, a)
    kept = [x for x in runs if x['keep']]
    hs = [x['h'] for x in kept if x.get('h') is not None and 0.0 < x['h'] < 1.0]
    h2s = [x['h2'] for x in kept if x.get('h2') is not None and 0.0 < x['h2'] < 1.0]
    h_ref = statistics.median(hs) if hs else None
    h2_ref = statistics.median(h2s) if h2s else None
    hTs = [x['hT'] for x in kept if x.get('hT') is not None and 0.0 < x['hT'] < 1.0]
    hT_ref = statistics.median(hTs) if hTs else None
    for x in runs:
        x['a_std'] = std_mix(x.get('_F'), x.get('_S'), h_ref)
        x['a2_std'] = std_mix(x.get('_F2'), x.get('_S2'), h2_ref)
        x['t_std'] = std_mix(x.get('_TL'), x.get('_TH'), hT_ref)
        for k in ('_F', '_S', '_F2', '_S2', '_TL', '_TH'):
            x.pop(k, None)
    methods = []
    for mid, label, field in METHODS:
        g = getter(field)
        for key, sign, mlabel, nd in METRICS:
            s = summarize(collect(kept, g, key), ref, order, sign)
            if s:
                methods.append(dict(s, method=mid, label=label, key=key, metric=mlabel, nd=nd))
    for mid, label, keys in COVARIATES:
        cv = lambda x, keys=keys: [(x.get('cov') or {}).get(c) for c in keys]
        for key, sign, mlabel, nd in METRICS:
            s = ancova(collect(kept, getter('raw'), key), cv, ref, order, sign)
            if s:
                methods.append(dict(s, method=mid, label=label, key=key, metric=mlabel, nd=nd, covs=list(keys)))
    for field, src in PAIRED_FROM:
        g = getter(field)
        for key, sign, mlabel, nd in METRICS:
            nv = round_norm(kept, g, key)
            s = summarize(collect(kept, lambda x, k, nv=nv: nv.get(x['name']), key), ref, order, sign)
            if s:
                methods.append(dict(s, method='B-norm %s' % src, label='B: round-normalized %s' % src, key=key,
                                    metric=mlabel, nd=3))
    rounds, blk = round_block(kept)
    if len(rounds) >= 2:
        for field, src in PAIRED_FROM:
            g = getter(field)
            for key, sign, mlabel, nd in METRICS:
                s = ancova(collect(kept, g, key), blk, ref, order, sign)
                if s:
                    methods.append(dict(s, method='B-block %s' % src, label='B: two-way, round as a block, %s' % src,
                                        key=key, metric=mlabel, nd=nd, covs=['round %s' % r for r in rounds[1:]]))
    pairs = []
    for field, src in PAIRED_FROM:
        g = getter(field)
        for key, sign, mlabel, nd in METRICS:
            p = paired(kept, g, key, ref, order)
            if p:
                pairs.append({'src': src, 'key': key, 'metric': mlabel, 'nd': nd, 'sign': sign, 'arms': p})
    lsd = [abs(x['ls_T'] - x['ls_runner']) for x in runs if x.get('ls_T') is not None and x.get('ls_runner') is not None]
    return {'dir': d, 'title': title, 'command': command, 'ref': ref, 'order': order, 'params': vars(a),
            'h_ref': h_ref, 'h2_ref': h2_ref, 'hT_ref': hT_ref, 'runs': runs, 'methods': methods, 'paired': pairs,
            'cov_info': covariate_info(kept, order, COV_INFO), 'ls_check_max_abs': max(lsd) if lsd else None,
            'hist_roll_med': {str(k): hist[k] for k in sorted(hist)}}


def fmt(v, nd=1):
    return '-' if v is None else '%.*f' % (nd, v)


def sgn(v, nd=1):
    return '-' if v is None else '%+.*f' % (nd, v)


def report(R):
    out = []
    w = out.append
    ref, order, P = R['ref'], R['order'], R['params']
    others = [arm for arm in order if arm != ref]
    runs = R['runs']
    kept = [x for x in runs if x['keep']]
    w('# W4b noise methods (Agent 7, task #6, was #30)')
    w('')
    w('- dir: `%s`' % R['dir'])
    if R['title']:
        w('- title: %s' % R['title'])
    w('- command: `%s`' % R['command'])
    w('- kept runs: %d of %d (%s); left out: %s' % (
        len(kept), len(runs), ', '.join('%s %d' % (arm, sum(1 for x in kept if x['arm'] == arm)) for arm in order),
        '; '.join('%s (%s)' % (x['name'], ', '.join(x['why'])) for x in runs if not x['keep']) or 'none'))
    w('- reference arm %s. Band = (max - min) / median of the %s runs\' values, as summary.md. Pooled CV = the pooled '
      'within-arm SD of ln(value) over the kept runs; 95 %% band 4 vs 4 = exp(t(0.975, df) x SD x sqrt(1/4 + 1/4)) '
      '- 1.' % (ref, ref))
    w('- A: S = sys.csv e_eff_mhz < %g MHz for >= %d samples in a row (Agent 11), F = the rest; guard %.1f s around '
      'each state change; h = S share of the classified time; h_ref = %s (median h of the kept runs).' % (
          P['emhz'], P['min_rows'], P['guard_s'], fmt(R['h_ref'], 3)))
    w('- A2: S = centred rolling median of %d frames > %.1f ms; guard %.1f s; h2_ref = %s.' % (
        P['roll'], P['heavy_ms'], P['roll_guard_s'], fmt(R['h2_ref'], 3)))
    w('- C: %.0f %% trimmed at each end; bins of %g s.' % (100.0 * P['trim'], P['bin_s']))
    lms = sorted(set(x['light_ms'] for x in runs if x.get('light_ms') is not None))
    w('- T: light = frame time < %s ms (the runner\'s share_lt_light); hT = heavy time share; hT_ref = %s; max |own '
      'light share - frames.json share_lt_light| = %s.' % (', '.join('%g' % v for v in lms) or '-', fmt(R['hT_ref'], 3),
                                                           fmt(R['ls_check_max_abs'], 4)))
    w('- L, D: ANCOVA of ln(raw value) on the covariates with the arm as a factor (see Covariates); runs adjusted to the '
      'mean covariate; df = runs - arms - covariates; --cpus %d for the non-game load.' % P['cpus'])
    w('- B-block: the same ANCOVA on round dummies (the two-way model arm + round) of the raw, A-std, A-heavy and '
      'T-std values; df = runs - arms - rounds + 1. B-norm\'s pooled CI uses df = runs - arms, so it is too narrow.')
    w('')
    w('## Bands and deltas per method')
    w('')
    w('Arm cells: median delta vs %s in %% and the verdict against the %s band (`in` = within).' % (ref, ref))
    w('')
    w('| method | metric | %s runs | %s band %% | pooled CV %% | 95 %% band 4 vs 4 | %s |' % (
        ref, ref, ' | '.join(others)))
    w('|---|---|---|---|---|---|%s' % ('---|' * len(others)))
    for s in R['methods']:
        cells = []
        for arm in others:
            e = s['arms'].get(arm)
            cells.append('-' if not e or e.get('delta_pct') is None else '%s %s (n=%d)' % (
                sgn(e['delta_pct']), 'in' if e['verdict'] == 'within' else e['verdict'], e['n']))
        w('| %s | %s | %s | %s | %s | %s | %s |' % (
            s['method'], s['metric'], ', '.join(fmt(v, s['nd']) for v in s['ref_vals']), fmt(s['band_pct']),
            fmt(s['cv_pct']), fmt(s['hw44_pct']), ' | '.join(cells)))
    w('')
    w('## Pooled 95 %% CIs of the geometric-mean delta vs %s' % ref)
    w('')
    w('`*` = the CI excludes 0.')
    w('')
    w('| method | metric | df | %s |' % ' | '.join(others))
    w('|---|---|---|%s' % ('---|' * len(others)))
    for s in R['methods']:
        cells = []
        for arm in others:
            e = s['arms'].get(arm)
            if not e or e.get('ci_pct') is None:
                cells.append('-')
                continue
            cells.append('%s [%s, %s]%s' % (sgn(e['gm_delta_pct']), sgn(e['ci_pct'][0]), sgn(e['ci_pct'][1]),
                                            ' *' if e['ci_excludes_0'] else ''))
        w('| %s | %s | %d | %s |' % (s['method'], s['metric'], s['df'], ' | '.join(cells)))
    w('')
    w('## Paired within-round deltas vs %s' % ref)
    w('')
    w('| source | metric | arm | rounds | per-round delta % | median | range pp | mean +- 95 % | rounds up |')
    w('|---|---|---|---|---|---|---|---|---|')
    for p in R['paired']:
        for arm, e in p['arms'].items():
            w('| %s | %s | %s | %s | %s | %s | %s | %s +- %s | %d of %d |' % (
                p['src'], p['metric'], arm, ','.join(str(r) for r in e['rounds']),
                ', '.join(sgn(q) for q in e['deltas']), sgn(e['med']), fmt(e['range']), sgn(e['mean']),
                fmt(e['hw95']), e['up'], e['n']))
    w('')
    w('## Covariates (L, D)')
    w('')
    w('F = one-way ANOVA of the covariate on the arm, F(df). A large F means the covariate moves with the arm, so '
      'adjusting for it can remove a real arm effect (5 % critical F: about 3.6 for (3, 11), 3.5 for (4, 10)).')
    w('')
    w('| covariate | runs | F (df) | arm means |')
    w('|---|---|---|---|')
    for key, ci in R['cov_info'].items():
        w('| %s | %d | %s (%d, %d) | %s |' % (key, ci['n'], fmt(ci['F'], 2), ci['df'][0], ci['df'][1],
                                            ', '.join('%s %s' % (arm, fmt(v, 3 if key == 'ls_T' else 2))
                                                      for arm, v in ci['means'].items())))
    w('')
    w('| method | metric | slope(s) on ln(value) | runs without the covariate |')
    w('|---|---|---|---|')
    for s in R['methods']:
        if s.get('covs'):
            w('| %s | %s | %s | %d |' % (s['method'], s['metric'], ', '.join(
                '%s %.5g' % (c, bv) for c, bv in zip(s['covs'], s['b'])), s['n_dropped']))
    w('')
    w('## Runs')
    w('')
    w('| seq | round | arm | kept | raw fps | raw median ms | raw p99 ms | light share (runner) | slow spans in window, '
      's (A) | h (A) | dropped s | fps F | fps S | A-std fps | A-std p99 ms | h (A2) | A2 switches | A/A2 agree | '
      'C-frames fps | C-bins fps |')
    w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for x in runs:
        raw = x.get('raw') or {}
        spans = x.get('slow_spans_win')
        sp = '-' if spans is None else (', '.join('%.1f-%.1f' % s for s in spans) or 'none')
        w('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            x['seq'], x['round'], x['arm'], 'yes' if x['keep'] else 'no', fmt(raw.get('fps')),
            fmt(raw.get('p50_ms'), 3), fmt(raw.get('p99_ms'), 2), fmt(x.get('light_share_csv'), 3), sp,
            fmt(x.get('h'), 3), fmt(x.get('drop_s')), fmt((x.get('a_F') or {}).get('fps')),
            fmt((x.get('a_S') or {}).get('fps')), fmt((x.get('a_std') or {}).get('fps')),
            fmt((x.get('a_std') or {}).get('p99_ms'), 2), fmt(x.get('h2'), 3),
            '-' if x.get('switches2') is None else str(x['switches2']), fmt(x.get('agree'), 3),
            fmt((x.get('c_frames') or {}).get('fps')), fmt((x.get('c_bins') or {}).get('fps'))))
    w('')
    w('## Runs: T split and host state')
    w('')
    w('| seq | round | arm | kept | light share (own) | hT | T-light fps | T-light median ms | T-heavy fps | T-std fps | '
      'A2-light fps | P util %% | E MHz | E util %% | non-game CPUs | game cores |'.replace('%%', '%'))
    w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for x in runs:
        cv = x.get('cov') or {}
        w('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            x['seq'], x['round'], x['arm'], 'yes' if x['keep'] else 'no', fmt(x.get('ls_T'), 3), fmt(x.get('hT'), 3),
            fmt((x.get('t_L') or {}).get('fps')), fmt((x.get('t_L') or {}).get('p50_ms'), 3),
            fmt((x.get('t_H') or {}).get('fps')), fmt((x.get('t_std') or {}).get('fps')),
            fmt((x.get('a2_F') or {}).get('fps')), fmt(cv.get('p_util')), fmt(cv.get('e_mhz'), 0),
            fmt(cv.get('e_util')), fmt(cv.get('nongame'), 2), fmt(cv.get('cores'), 2)))
    w('')
    w('## A2: rolling-median frame time over the kept runs (frames per 0.5 ms)')
    w('')
    w('| rolling median ms | frames |')
    w('|---|---|')
    for k, n in R['hist_roll_med'].items():
        b = int(k)
        w('| %.1f-%.1f | %d |' % (b * 0.5, b * 0.5 + 0.5, n))
    w('')
    return '\n'.join(out) + '\n'


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('dir', nargs='?', default=DEFAULT_DIR, help='run-matrix.ps1 output dir (default: W4b)')
    ap.add_argument('-o', '--out', help='write the markdown report here too')
    ap.add_argument('--json', help='write every number as json here')
    ap.add_argument('--all', action='store_true', help='keep runs that are not valid timing')
    ap.add_argument('--emhz', type=float, default=800.0, help='A: slow state below this E-core MHz (Agent 11)')
    ap.add_argument('--min-rows', type=int, default=3, help='A: for at least this many sys.csv samples in a row')
    ap.add_argument('--guard-s', type=float, default=1.5, help='A: leave out frames this close to a state change')
    ap.add_argument('--roll', type=int, default=201, help='A2: rolling-median length in frames')
    ap.add_argument('--heavy-ms', type=float, default=5.0, help='A2: heavy above this rolling median')
    ap.add_argument('--roll-guard-s', type=float, default=0.5, help='A2: leave out frames this close to a switch')
    ap.add_argument('--trim', type=float, default=0.2, help='C: share trimmed at each end')
    ap.add_argument('--bin-s', type=float, default=10.0, help='C: bin length in s of summed frame time')
    ap.add_argument('--light-ms', type=float, default=None, help='T, L: light below this ms (default: frames.json)')
    ap.add_argument('--cpus', type=int, default=os.cpu_count() or 12, help='D: logical CPUs for the non-game load')
    a = ap.parse_args(argv)
    command = 'python -B build\\agent7\\w4b-noise\\noise_methods.py ' + ' '.join(argv)
    R = analyse(a.dir, a, command)
    text = report(R)
    sys.stdout.write(text)
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    if a.json:
        with open(a.json, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(R, fh, indent=1, default=str)
    return 0


if __name__ == '__main__':
    sys.exit(main())
