#!/usr/bin/env python3
"""mp2_same_frames.py - MP2 "same frames (proxy)" checker for #21 S4-T1 row F1 (M7 / E7.1, session 3).

Implements FUNCTIONAL-ROWS.md F1 pass rule 5 plus the logdiff part of the must-prove map row 2
(build/agent7/s4-t1/FUNCTIONAL-ROWS.md L119-121 and L192; THREADED-PROOFS-TODO.md row MP2). Read-only, stdlib
only, one thread; no game, no build. It lowers its own priority to Below Normal (--normal-priority turns this off).

Run (from the workspace root):
  python -B build/agent7/session3/mp/mp2_same_frames.py --dir <F1 run-matrix out dir> [--arms th3,th3cp3] [--json OUT]
  python -B build/agent7/session3/mp/mp2_same_frames.py --ref <n0-r1> --ref <n0-r2> --cand <run> [--cand ...]

Exit: 0 PASS, 1 FAIL, 2 INCOMPLETE (a run dir, perf.csv window or game log is missing, fewer than 2 ref runs).

Per run (all from the run dir):
  light share   frames.json share_lt_light (the runner's share of window frames < light_ms = 4.5 ms; the same number
                as results.csv light_share and noise_methods.py ls_T). Without it: computed from perf.csv
                frame_time_us over the frames.json window.
  draw_calls    perf.csv column draw_calls over the scored window = perf.csv rows [first_row, first_row + rows) of
                frames.json's window, rows with frame_time_us > 0 only (as noise_methods.py). Valid only when
                frames.json "source" is "perf" (every F1 arm has frames=perf). Otherwise --perf-fallback decides:
                incomplete (default) or whole (every perf.csv row with frame_time_us > 0, noted in the output).
                Stats: p10, p50, p90 (nearest rank, sorted[ceil(p*n)-1], the runner's percentile method), mean, n.
  game log      game.log plus rotated game.N.log, parsed with build/agent10/bgate/logdiff.py's read() and norm()
                (embedded copy if that file is missing).

Checks per candidate run (ref = the reference runs, normally n0-r1 and n0-r2):
  LS   light share inside [min, max] of the ref runs, widened by --ls-pad (absolute, default 0 = the literal rule
       "inside n0's run-to-run range").
  DC   for each of p10, p50, p90 of draw_calls: inside [min, max] of the ref runs ("inside n0-r1 vs n0-r2's spread"),
       widened by --dc-pad (relative, default 0): [min * (1 - pad), max * (1 + pad)].
       --spread-k K (default 0) widens both bands by K x the ref runs' own spread (max - min) on each side.
       A value outside its band prints how far outside, as a multiple of the ref spread.
       If draw_calls is 0 on every ref frame (the native route does not feed perf.csv draw_calls) the DC proxy is
       vacuous: INCOMPLETE, unless --zero-dc info.
  LOG  vs every ref log, at or above --gate-level (default warning):
         NEW   key in the candidate log, in no ref log, not matching --allow-new          -> FAIL
         GONE  key in every ref log, missing from the candidate, not noise, no --allow-gone -> FAIL
         MORE  candidate count > ref max + max(5, ref max) (logdiff's rule), not noise   -> FAIL
       noise = the same key varies between the first two ref logs: present in only one, or
               max(c1, c2) > min(c1, c2) + max(5, min(c1, c2)).
       fail markers (logdiff MARKERS) above the ref max, or no clean-exit line when every ref log has one -> FAIL.
       Keys between --min-level (default info) and --gate-level are listed as INFO only (threaded mode logs its own
       mode lines and drops n0-only ones, e.g. 'Native draw batches', check_n_rows.py L22-25).
"""
import argparse
import collections
import csv
import glob
import importlib.util
import json
import math
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
LOGDIFF = os.path.join(WS, 'build', 'agent10', 'bgate', 'logdiff.py')
LIGHT_MS = 4.5
QS = (('p10', 0.10), ('p50', 0.50), ('p90', 0.90))


def below_normal():
    try:
        if os.name == 'nt':
            import ctypes
            k = ctypes.windll.kernel32
            k.GetCurrentProcess.restype = ctypes.c_void_p
            k.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
            return bool(k.SetPriorityClass(k.GetCurrentProcess(), 0x4000))
        os.nice(5)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- logdiff (import, else embedded copy)
class _EmbeddedLogdiff:
    """Copy of build/agent10/bgate/logdiff.py's LEVELS, LINE, MARKERS, EXIT_LINE, NORM, norm() and read()."""
    LEVELS = ['trace', 'debug', 'info', 'warning', 'error', 'critical']
    LINE = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\] \[([a-z]+)\] \[([^\]]*)\] (?:\[t\d+\] )?(.*)$')
    MARKERS = [
        ('not-in-module', re.compile(r'not in any registered module', re.I)),
        ('crash-guard', re.compile(r'crash guard', re.I)),
        ('unimplemented', re.compile(r'unimplemented|REX_UNIMPLEMENTED', re.I)),
        ('exception', re.compile(r'exception|0xC0000409|0xC00000FD|stack overflow|access violation|0xC0000005', re.I)),
        ('watchdog/hang', re.compile(r'watchdog|hang detected|deadlock|timed out', re.I)),
        ('fatal', re.compile(r'fatal|abort|(?<!Title )terminat', re.I)),
    ]
    EXIT_LINE = re.compile(r'Title terminated; hard-exiting process')
    NORM = [
        (re.compile(r'[A-Za-z]:\\[^\s"\']+'), '<path>'),
        (re.compile(r'0x[0-9A-Fa-f]+'), '0x#'),
        (re.compile(r'\b[0-9A-Fa-f]{8,}\b'), '#h'),
        (re.compile(r'\d+(\.\d+)?'), '#'),
    ]

    def norm(self, msg):
        for rx, rep in self.NORM:
            msg = rx.sub(rep, msg)
        return msg[:200]

    def read(self, path):
        keys, levels, marks = collections.Counter(), collections.Counter(), collections.Counter()
        first = last = None
        with open(path, encoding='utf-8', errors='replace') as f:
            for ln in f:
                m = self.LINE.match(ln.rstrip('\r\n'))
                if not m:
                    continue
                ts, lvl, cat, msg = m.groups()
                first = first or ts
                last = ts
                levels[lvl] += 1
                keys[(lvl, cat, self.norm(msg))] += 1
                for name, rx in self.MARKERS:
                    if rx.search(msg):
                        marks[name] += 1
                if self.EXIT_LINE.search(msg):
                    marks['clean-exit'] += 1
        return keys, levels, marks, first, last


def load_logdiff(path=LOGDIFF):
    """(module-like object, source text): logdiff.py imported by path, else the embedded copy."""
    try:
        if path and os.path.isfile(path):
            spec = importlib.util.spec_from_file_location('logdiff_a10', path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for name in ('read', 'norm', 'LEVELS', 'MARKERS'):
                getattr(mod, name)
            return mod, path
    except Exception:
        pass
    return _EmbeddedLogdiff(), 'embedded copy of logdiff.py'


# ---------------------------------------------------------------- run dir readers
def log_files(path):
    """Oldest first: game.N.log ... game.1.log, game.log (soak_check.py's order)."""
    if os.path.isfile(path):
        return [path]
    if not os.path.isdir(path):
        return []
    rot = []
    for p in glob.glob(os.path.join(path, 'game.*.log')):
        m = re.match(r'game\.(\d+)\.log$', os.path.basename(p))
        if m:
            rot.append((int(m.group(1)), p))
    files = [p for _, p in sorted(rot, reverse=True)]
    if os.path.isfile(os.path.join(path, 'game.log')):
        files.append(os.path.join(path, 'game.log'))
    return files


def read_log(LD, run):
    """Merged (keys, marks) over the run's log files; None without a log."""
    files = log_files(run)
    if not files:
        return None
    keys, marks = collections.Counter(), collections.Counter()
    for p in files:
        k, _, m, _, _ = LD.read(p)
        keys.update(k)
        marks.update(m)
    return {'files': files, 'keys': keys, 'marks': marks}


def load_json(p):
    try:
        with open(p, encoding='utf-8-sig') as fh:
            return json.load(fh)
    except Exception:
        return None


def num(v):
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def nearest_rank(sorted_v, p):
    if not sorted_v:
        return None
    i = max(0, min(len(sorted_v) - 1, int(math.ceil(p * len(sorted_v))) - 1))
    return sorted_v[i]


def read_perf(path, first=None, rows=None):
    """[(frame_time_us, draw_calls)] for perf.csv rows [first, first + rows) (all rows when first is None)."""
    out = []
    with open(path, newline='', encoding='utf-8', errors='replace') as fh:
        rd = csv.reader(fh)
        head = next(rd, None)
        if not head:
            return None
        head = [h.strip() for h in head]
        if 'frame_time_us' not in head or 'draw_calls' not in head:
            return None
        it, idc = head.index('frame_time_us'), head.index('draw_calls')
        for i, r in enumerate(rd):
            if first is not None and i < first:
                continue
            if first is not None and rows is not None and i >= first + rows:
                break
            if len(r) <= max(it, idc):
                continue
            ft, dc = num(r[it]), num(r[idc])
            if ft is None or dc is None:
                continue
            out.append((ft, dc))
    return out


def run_metrics(run, perf_fallback='incomplete', light_ms=None):
    """Per-run numbers: light share, draw_calls stats, notes; 'missing' lists what made it incomplete."""
    x = {'run': run, 'name': os.path.basename(os.path.normpath(run)), 'missing': [], 'notes': []}
    if not os.path.isdir(run):
        x['missing'].append('no run dir')
        return x
    fj = load_json(os.path.join(run, 'frames.json'))
    fj = fj if isinstance(fj, dict) else {}
    win = fj.get('window') if isinstance(fj.get('window'), dict) else {}
    src = fj.get('source')
    perf = os.path.join(run, 'perf.csv')
    first, nrows = num(win.get('first_row')), num(win.get('rows'))
    rows = None
    if not os.path.isfile(perf):
        x['missing'].append('no perf.csv')
    elif src == 'perf' and first is not None and nrows:
        rows = read_perf(perf, int(first), int(nrows))
        x['window'] = 'perf.csv rows %d..%d (frames.json window)' % (int(first), int(first + nrows) - 1)
    elif perf_fallback == 'whole':
        rows = read_perf(perf)
        x['window'] = 'whole perf.csv (--perf-fallback whole; frames.json source %s)' % (src or 'none')
        x['notes'].append('draw_calls over the whole perf.csv, not the scored window')
    else:
        x['missing'].append('no perf.csv scored window (frames.json source %s; F1 arms use frames=perf; '
                            '--perf-fallback whole reads the whole file)' % (src or 'missing'))
    if rows is not None:
        rows = [(ft, dc) for ft, dc in rows if ft > 0]
        if not rows:
            x['missing'].append('perf.csv window has no frames')
        else:
            dcs = sorted(dc for _, dc in rows)
            x['dc'] = dict((k, nearest_rank(dcs, p)) for k, p in QS)
            x['dc']['mean'] = sum(dcs) / len(dcs)
            x['dc']['n'] = len(dcs)
    ls = num(fj.get('share_lt_light'))
    lms = light_ms or num(fj.get('light_ms')) or LIGHT_MS
    if ls is not None and light_ms is None:
        x['ls'], x['ls_src'] = ls, 'frames.json share_lt_light (light_ms %g)' % lms
    elif rows:
        x['ls'] = sum(1 for ft, _ in rows if ft < lms * 1000.0) / float(len(rows))
        x['ls_src'] = 'perf.csv frame_time_us < %g ms over %s' % (lms, x.get('window'))
    else:
        x['missing'].append('no light share (frames.json share_lt_light and perf.csv window both missing)')
    return x


# ---------------------------------------------------------------- arm discovery
def arm_runs(d, arm):
    """Run dirs of an arm in a run-matrix out dir: runs/<HHMM>-<arm>-r<k>, ordered by k then name
    (FUNCTIONAL-ROWS.md L51's helper: Name -match "-$arm-r\\d+$")."""
    base = os.path.join(d, 'runs')
    if not os.path.isdir(base):
        return []
    rx = re.compile(r'-%s-r(\d+)$' % re.escape(arm))
    out = []
    for n in os.listdir(base):
        m = rx.search(n)
        if m and os.path.isdir(os.path.join(base, n)):
            out.append((int(m.group(1)), n, os.path.join(base, n)))
    return [p for _, _, p in sorted(out)]


# ---------------------------------------------------------------- checks
class Result:
    def __init__(self):
        self.lines, self.fails, self.incomplete = [], [], []

    def check(self, cond, msg, incomplete=False):
        tag = 'PASS' if cond else ('INCOMPLETE' if incomplete else 'FAIL')
        self.lines.append('%-10s %s' % (tag, msg))
        if not cond:
            (self.incomplete if incomplete else self.fails).append(msg)

    def info(self, msg):
        self.lines.append('           ' + msg)

    @property
    def verdict(self):
        return 'FAIL' if self.fails else ('INCOMPLETE' if self.incomplete else 'PASS')


def fmt(v, nd=3):
    return '-' if v is None else ('%.*f' % (nd, v) if isinstance(v, float) and v != int(v) else '%g' % v)


def varies(c1, c2):
    """logdiff's MORE threshold applied between the two noise logs (absent in one = varies)."""
    if (c1 == 0) != (c2 == 0):
        return True
    lo, hi = min(c1, c2), max(c1, c2)
    return hi > lo + max(5, lo)


def compile_all(pats):
    return [re.compile(p) for p in (pats or [])]


def logdiff_check(LD, res, name, cand_log, ref_logs, min_level, gate_level, allow_new, allow_gone, max_list=8):
    levels = list(LD.LEVELS)
    lo, gate = levels.index(min_level), levels.index(gate_level)
    bmax, bseen = collections.Counter(), collections.Counter()
    for r in ref_logs:
        for k, n in r['keys'].items():
            bmax[k] = max(bmax[k], n)
            bseen[k] += 1
    n1 = ref_logs[0]['keys'] if len(ref_logs) >= 1 else collections.Counter()
    n2 = ref_logs[1]['keys'] if len(ref_logs) >= 2 else collections.Counter()
    have_noise = len(ref_logs) >= 2

    def lvl(k):
        return levels.index(k[0]) if k[0] in levels else 0

    def show(k):
        return '[%s] [%s] %s' % k

    new_g, new_i, gone_g, gone_i, more_g, more_i, noise = [], [], [], [], [], [], []
    for k, n in sorted(cand_log['keys'].items()):
        if lvl(k) < lo:
            continue
        if k not in bmax:
            if lvl(k) >= gate and not any(rx.search(k[2]) for rx in allow_new):
                new_g.append('x%d %s' % (n, show(k)))
            else:
                new_i.append('x%d %s' % (n, show(k)))
        elif n > bmax[k] + max(5, bmax[k]):
            item = 'x%d (ref max %d) %s' % (n, bmax[k], show(k))
            if have_noise and varies(n1.get(k, 0), n2.get(k, 0)):
                noise.append('MORE ' + item)
            elif lvl(k) >= gate:
                more_g.append(item)
            else:
                more_i.append(item)
    for k in sorted(k for k, s in bseen.items() if s == len(ref_logs)):
        if k in cand_log['keys']:
            continue
        item = '(ref %s) %s' % ('/'.join(str(r['keys'].get(k, 0)) for r in ref_logs), show(k))
        if lvl(k) >= gate and not any(rx.search(k[2]) for rx in allow_gone):
            if have_noise and varies(n1.get(k, 0), n2.get(k, 0)):
                noise.append('GONE ' + item)
            else:
                gone_g.append(item)
        elif lvl(k) >= lo:
            gone_i.append(item)

    def lst(xs):
        return ('; ' + ' | '.join(xs[:max_list]) + (' | ... (%d more)' % (len(xs) - max_list) if len(xs) > max_list
                                                       else '')) if xs else ''

    res.check(not new_g, '%s LOG: no NEW key at >= %s (%d)%s' % (name, gate_level, len(new_g), lst(new_g)))
    res.check(not gone_g, '%s LOG: no GONE key at >= %s outside the noise (%d)%s'
              % (name, gate_level, len(gone_g), lst(gone_g)))
    res.check(not more_g, '%s LOG: no MORE key at >= %s outside the noise (%d)%s'
              % (name, gate_level, len(more_g), lst(more_g)))
    mmax = collections.Counter()
    for r in ref_logs:
        for mk, _ in LD.MARKERS:
            mmax[mk] = max(mmax[mk], r['marks'][mk])
    over = ['%s=%d (ref max %d)' % (mk, cand_log['marks'][mk], mmax[mk]) for mk, _ in LD.MARKERS
            if cand_log['marks'][mk] > mmax[mk]]
    res.check(not over, '%s LOG: fail markers no higher than the ref max%s' % (name, ': ' + ', '.join(over) if over
                                                                               else ''))
    every_exit = all(r['marks']['clean-exit'] for r in ref_logs)
    res.check(not every_exit or cand_log['marks']['clean-exit'] > 0,
              '%s LOG: clean-exit line present%s' % (name, '' if every_exit else ' (not every ref log has one: not gated)'))
    res.info('%s LOG info (>= %s, < %s): NEW %d%s' % (name, min_level, gate_level, len(new_i), lst(new_i)))
    res.info('%s LOG info: GONE %d%s' % (name, len(gone_i), lst(gone_i)))
    res.info('%s LOG info: MORE %d%s' % (name, len(more_i), lst(more_i)))
    if noise:
        res.info('%s LOG noise-explained (key also varies between %s and %s): %d%s'
                 % (name, ref_logs[0]['name'], ref_logs[1]['name'], len(noise), lst(noise)))
    return {'new_gated': new_g, 'new_info': new_i, 'gone_gated': gone_g, 'gone_info': gone_i,
            'more_gated': more_g, 'more_info': more_i, 'noise': noise, 'markers_over': over}


def evaluate(refs, groups, a, LD=None):
    """refs: ref run dirs; groups: [(label, [cand run dirs])]. Returns (Result, data dict)."""
    LD = LD or load_logdiff(a.logdiff)[0]
    res = Result()
    data = {'refs': [], 'groups': [], 'params': {k: v for k, v in vars(a).items() if k not in ('json',)}}
    R = [run_metrics(r, a.perf_fallback, a.light_ms) for r in refs]
    res.check(len(refs) >= 2, 'ref runs: %d (need 2: n0-r1 vs n0-r2 = noise)%s'
              % (len(refs), ': ' + ', '.join(os.path.basename(os.path.normpath(r)) for r in refs) if refs else ''),
              incomplete=True)
    for x in R:
        if x['missing']:
            res.check(False, 'ref %s: %s' % (x['name'], '; '.join(x['missing'])), incomplete=True)
        else:
            res.info('ref %s: light share %s (%s); draw_calls p10/p50/p90 %s/%s/%s mean %s n %d; %s'
                     % (x['name'], fmt(x['ls'], 5), x['ls_src'], fmt(x['dc']['p10']), fmt(x['dc']['p50']),
                        fmt(x['dc']['p90']), fmt(x['dc']['mean'], 1), x['dc']['n'], x.get('window')))
        x['log'] = read_log(LD, x['run']) if os.path.isdir(x['run']) else None
        if x['log'] is None and not a.no_logdiff:
            res.check(False, 'ref %s: no game log' % x['name'], incomplete=True)
        data['refs'].append({k: v for k, v in x.items() if k != 'log'})
    ok = [x for x in R if not x['missing']]
    band_ls = band_dc = None
    spread = {}
    k_s = a.spread_k
    if len(ok) >= 2:
        lss = [x['ls'] for x in ok]
        spread['ls'] = max(lss) - min(lss)
        band_ls = (min(lss) - a.ls_pad - k_s * spread['ls'], max(lss) + a.ls_pad + k_s * spread['ls'])
        band_dc = {}
        for k, _ in QS:
            v = [x['dc'][k] for x in ok]
            spread[k] = max(v) - min(v)
            band_dc[k] = (min(v) * (1.0 - a.dc_pad) - k_s * spread[k], max(v) * (1.0 + a.dc_pad) + k_s * spread[k])
        if all(x['dc']['mean'] == 0 for x in ok):
            # Seen on every native-route run checked (native2/native4, e.g. agent3/runs/rpm4-20261123-0620 n0/n3):
            # the native path does not feed perf.csv draw_calls, so the DC proxy cannot tell anything apart.
            res.check(a.zero_dc == 'info', 'DC proxy vacuous: perf.csv draw_calls is 0 on every ref frame (native route '
                      'does not feed it); --zero-dc %s' % a.zero_dc, incomplete=True)
        res.info('noise band (ref runs %s): light share [%s, %s] (--ls-pad %g); draw_calls %s (--dc-pad %g); '
                 '--spread-k %g' % (', '.join(x['name'] for x in ok), fmt(band_ls[0], 5), fmt(band_ls[1], 5), a.ls_pad,
                                    ', '.join('%s [%s, %s]' % (k, fmt(band_dc[k][0], 1), fmt(band_dc[k][1], 1))
                                              for k, _ in QS), a.dc_pad, k_s))

    def outside(v, band, sp):
        d = band[0] - v if v < band[0] else (v - band[1] if v > band[1] else 0.0)
        if d <= 0:
            return ''
        return ' (outside by %s = %s x the ref spread %s)' % (fmt(float(d), 5), ('%.2f' % (d / sp)) if sp else 'inf',
                                                              fmt(float(sp), 5))
    ref_logs = [dict(x['log'], name=x['name']) for x in R if x.get('log')]
    allow_new, allow_gone = compile_all(a.allow_new), compile_all(a.allow_gone)
    for label, cands in groups:
        g = {'label': label, 'runs': []}
        res.check(bool(cands), '%s: candidate runs found: %d' % (label, len(cands)), incomplete=True)
        for c in cands:
            x = run_metrics(c, a.perf_fallback, a.light_ms)
            name = '%s %s' % (label, x['name'])
            for nt in x['notes']:
                res.info('%s: note: %s' % (name, nt))
            if x['missing']:
                res.check(False, '%s: %s' % (name, '; '.join(x['missing'])), incomplete=True)
            if 'ls' in x:
                if band_ls:
                    ok_ls = band_ls[0] <= x['ls'] <= band_ls[1]
                    res.check(ok_ls, '%s LS: light share %s %s [%s, %s]%s'
                              % (name, fmt(x['ls'], 5), 'inside' if ok_ls else 'NOT inside', fmt(band_ls[0], 5),
                                 fmt(band_ls[1], 5), outside(x['ls'], band_ls, spread['ls'])))
                else:
                    res.check(False, '%s LS: light share %s, no ref band' % (name, fmt(x['ls'])), incomplete=True)
            if 'dc' in x:
                if band_dc:
                    for k, _ in QS:
                        lo, hi = band_dc[k]
                        ok_dc = lo <= x['dc'][k] <= hi
                        res.check(ok_dc, '%s DC: draw_calls %s %s %s [%s, %s]%s'
                                  % (name, k, fmt(x['dc'][k]), 'inside' if ok_dc else 'NOT inside', fmt(lo, 1),
                                     fmt(hi, 1),
                                     outside(x['dc'][k], band_dc[k], spread[k])))
                    res.info('%s: draw_calls mean %s n %d; %s' % (name, fmt(x['dc']['mean'], 1), x['dc']['n'],
                                                                  x.get('window')))
                else:
                    res.check(False, '%s DC: no ref band' % name, incomplete=True)
            if not a.no_logdiff:
                lg = read_log(LD, c) if os.path.isdir(c) else None
                if lg is None:
                    res.check(False, '%s LOG: no game log' % name, incomplete=True)
                elif not ref_logs:
                    res.check(False, '%s LOG: no ref logs' % name, incomplete=True)
                else:
                    x['logdiff'] = logdiff_check(LD, res, name, lg, ref_logs, a.min_level, a.gate_level,
                                                 allow_new, allow_gone)
            g['runs'].append(x)
        data['groups'].append(g)
    data['band'] = {'ls': band_ls, 'dc': band_dc, 'spread': spread}
    return res, data


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('--dir', help='F1 run-matrix out dir (runs/<HHMM>-<arm>-r<k>)')
    ap.add_argument('--ref-arm', default='n0', help='reference arm in --dir mode (default n0)')
    ap.add_argument('--arms', default='th3,th3cp3', help='candidate arms in --dir mode, comma-separated '
                                                         '(default th3,th3cp3; th2,th2cp3 can be added)')
    ap.add_argument('--ref', action='append', default=[], help='reference run dir (repeat; first two = noise pair)')
    ap.add_argument('--cand', action='append', default=[], help='candidate run dir (repeat)')
    ap.add_argument('--ls-pad', type=float, default=0.0, help='absolute widening of the light-share band (default 0)')
    ap.add_argument('--dc-pad', type=float, default=0.0, help='relative widening of the draw_calls bands (default 0)')
    ap.add_argument('--spread-k', type=float, default=0.0,
                    help='widen every band by K x the ref runs\' own spread (max - min) on each side (default 0)')
    ap.add_argument('--light-ms', type=float, default=None, help='recompute light share from perf.csv at this '
                                                                 'threshold instead of frames.json share_lt_light')
    ap.add_argument('--perf-fallback', choices=['incomplete', 'whole'], default='incomplete',
                    help='frames.json source is not perf: incomplete (default) or the whole perf.csv')
    ap.add_argument('--zero-dc', choices=['incomplete', 'info'], default='incomplete',
                    help='perf.csv draw_calls is 0 on every ref frame (native route): incomplete (default) or '
                         'info (DC proxy reported but not gated; MP2 then rests on LS + logdiff)')
    ap.add_argument('--min-level', default='info', help='lowest log level listed (default info)')
    ap.add_argument('--gate-level', default='warning', help='lowest log level that can FAIL (default warning)')
    ap.add_argument('--allow-new', action='append', default=[], help='regex on the normalized message: a NEW key '
                                                                     'that matches is info only (repeat)')
    ap.add_argument('--allow-gone', action='append', default=[], help='regex: a GONE key that matches is info only')
    ap.add_argument('--no-logdiff', action='store_true', help='skip the log diff')
    ap.add_argument('--logdiff', default=LOGDIFF, help='path of logdiff.py (default: build/agent10/bgate/logdiff.py)')
    ap.add_argument('--json', help='write the result as JSON')
    ap.add_argument('--normal-priority', action='store_true', help="don't lower this process to Below Normal")
    return ap.parse_args(argv)


def main(argv=None):
    a = parse_args(sys.argv[1:] if argv is None else list(argv))
    if not a.normal_priority:
        below_normal()
    LD, ld_src = load_logdiff(a.logdiff)
    for lv in (a.min_level, a.gate_level):
        if lv not in LD.LEVELS:
            print('INCOMPLETE unknown level %s (levels: %s)' % (lv, ', '.join(LD.LEVELS)))
            return 2
    if a.dir:
        refs = arm_runs(a.dir, a.ref_arm)
        groups = [(arm, arm_runs(a.dir, arm)) for arm in [s.strip() for s in a.arms.split(',') if s.strip()]]
    else:
        refs, groups = a.ref, [('cand', a.cand)]
    if not a.dir and not (a.ref or a.cand):
        print('INCOMPLETE give --dir, or --ref and --cand')
        return 2
    res, data = evaluate(refs, groups, a, LD)
    print('mp2_same_frames %s (logdiff: %s)' % (a.dir or 'explicit runs', ld_src))
    for ln in res.lines:
        print(ln)
    print('RESULT: %s (%d failed, %d incomplete)' % (res.verdict, len(res.fails), len(res.incomplete)))
    if a.json:
        data.update(verdict=res.verdict, checks=res.lines, fails=res.fails, incomplete=res.incomplete,
                    logdiff=ld_src, dir=a.dir)
        with open(a.json, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(data, fh, indent=1, default=str)
    return 1 if res.fails else (2 if res.incomplete else 0)


if __name__ == '__main__':
    sys.exit(main())
