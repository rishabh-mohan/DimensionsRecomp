#!/usr/bin/env python3
"""Pooled formal read-out (Agent 7, task #21): the run-matrix passes of one window read as one data set, read-only.

Usage:
  python -B build\\agent7\\readout\\pool_readout.py DIR [DIR ...] [-o OUT.md] [--json OUT.json] [--label NAME]
         [--ref ARM] [--drop TOKENS] [--variant LABEL=TOKENS] ... [--alpha 0.05] [--putil 90] [--emhz 600]
         [--slow-emhz 800] [--slow-rows 3] [--light-ms MS] [--all] [--self-check] [--normal-priority]

TOKENS (comma-separated): a run name with its HHMM- prefix (0407-q125-r1; unique over the passes), pK:arm-rN (a run
of pass K), pK:rN (every run of round N of pass K) or pK (all of pass K).

Pooling (the convention of Agent 8's make_pool.py, so readout.py on a make_pool.py dir gives the same pooled
numbers): passes in the order given; pass k's scored rounds are shifted by the rounds of the passes before it (W9:
pass 2 rounds 1-4 -> 5-8); seq runs 1..N over the passes; cold runs stay unscored and are left out.

Numbers come from readout.py / noise_methods.py (imported from build/agent7/w4b-noise, not copied):
  T-std, B-block T-std over the pooled rounds (every round is a block, so a shift between the passes sits in the
  round terms), the round test that picks one, guards (a)-(c) and G11, exactly as readout.py on the pooled set.
Added here:
  - pass term: nested F test of a pass block on one-way T-std; arm x pass: nested F test of per-arm pass terms on
    B-block T-std (does an arm's delta differ between the passes?);
  - per pass: readout.py's numbers for each pass alone (its own hT_ref); --self-check compares them with
    readout.py's analyse() on each folder (they must match);
  - CPU: process cores (results.csv cpu_cores_mean) and the threads.csv busy % of Main XThread, GPU Commands and
    rex::thread::TimerQueue: arm mean, change vs the ref with a pooled 95 % CI (linear), GM delta with the pooled
    CI, one-way and B-block;
  - paired within-round deltas (noise_methods.paired) on T-std / raw median ms and fps, the T-std tails and cores;
  - PROPOSAL.md S3 counts per arm: planned (plan.txt), timed, failed (status, exit code, KILLED close, runner exit),
    STUCK-LOCK episodes by owner lr / site, hang dumps (*.dmp under the run dir), slow-state runs (Agent 11's math:
    sys.csv e_eff_mhz < 800 for 3+ rows in a row from the first frame), host CPU at each hang (sys.csv row);
  - --variant: the pool re-read without those runs (the read-out 'without the flagged runs');
  - a run table with the host state per run (frames, cores, thread busy, eff / P / E MHz, P / E util, slow rows).
Writes only -o and --json; without -o it prints the markdown. Below Normal priority unless --normal-priority.
Stdlib only, one thread.
"""
import argparse
import collections
import csv
import glob
import hashlib
import importlib.util
import json
import math
import os
import pickle
import re
import statistics
import sys
import time

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, '..', 'w4b-noise'))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RO = _load('readout', os.path.join(KIT, 'readout.py'))
N, NC, W = RO.N, RO.NC, RO.W
fmt, sgn, num = RO.fmt, RO.sgn, RO.num
KEYS, LABEL, SIGN, MAIN, TAILS, BLOCK = RO.KEYS, RO.LABEL, RO.SIGN, RO.MAIN, RO.TAILS, RO.BLOCK

CPU = (('cores', 'cpu cores'), ('gpu_busy', 'GPU Commands busy %'), ('main_busy', 'Main XThread busy %'),
       ('tq_busy', 'TimerQueue busy %'))
THREADS = (('main_busy', 'Main XThread'), ('gpu_busy', 'GPU Commands'), ('tq_busy', 'rex::thread::TimerQueue'))
PAIRED = (('t_std', 'p50_ms', 'T-std median ms'), ('t_std', 'fps', 'T-std fps'), ('raw', 'p50_ms', 'raw median ms'),
          ('raw', 'fps', 'raw fps'), ('t_std', 'p99_ms', 'T-std p99 ms'), ('t_std', 'low1_fps', 'T-std 1 % low fps'),
          ('cpu', 'cores', 'cpu cores'))
ROWKEYS = ('seq', 'round', 'rep', 'status', 'valid_timing', 'exit_code', 'close', 'runner_exit', 'frames',
           'window_s', 'median_ms', 'p99_ms', 'fps_mean', 'cpu_cores_mean', 'eff_mhz', 'idle_min_s', 'fg_share',
           'light_phase', 'flags_excluding', 'flags_info', 'excluded', 'scored')
EP_START = 'still not acquired after'
LR_RE = re.compile(r'lr\s*=\s*(?:0x)?([0-9A-Fa-f]{8})')
TS_RE = re.compile(r'^\[(\d{4}-\d\d-\d\d) (\d\d):(\d\d):(\d\d(?:\.\d+)?)\]')
DUMP_RE = re.compile(r'Minidump written to\s+(\S+)')
SITES = (('L1', ('83FAF188', '83FAF200', '83FBF868')), ('L2', ('83FB09F0',)))


# ---------------------------------------------------------------- per-run extras
def read_csv(path):
    try:
        with open(path, newline='', encoding='utf-8-sig') as fh:
            return list(csv.DictReader(fh))
    except (OSError, csv.Error):
        return None


def sha256(path):
    try:
        with open(path, 'rb') as fh:
            return hashlib.sha256(fh.read()).hexdigest().upper()
    except OSError:
        return None


def hhmmss(epoch):
    return time.strftime('%H:%M:%S', time.localtime(epoch)) if epoch else None


def thread_busy(rd):
    rows = read_csv(os.path.join(rd, 'threads.csv')) if rd else None
    out = {}
    for key, name in THREADS:
        vals = [num(r.get('busy_pct')) for r in rows or [] if (r.get('name') or '').startswith(name)]
        vals = [v for v in vals if v is not None]
        if vals:
            out[key] = sum(vals)
    return out


def slow_state(rd, emhz, min_rows, win):
    """Agent 11's timerq_slowstate.ps1 math: sys.csv rows from the first frame (run.json ff_signal_epoch_s) on;
    low = e_eff_mhz < emhz; onset = start of the first run of min_rows+ low rows; slow_pct = low / rows. Also the
    low rows inside the measured window (sys.json window_start/end_epoch)."""
    rj = W.load_json(os.path.join(rd, 'run.json')) if rd else None
    ff = num((rj or {}).get('ff_signal_epoch_s')) if isinstance(rj, dict) else None
    rows = read_csv(os.path.join(rd, 'sys.csv')) if rd else None
    if not rows or not ff or ff <= 0:
        return None
    s = [(num(r.get('epoch_s')), num(r.get('e_eff_mhz'))) for r in rows
         if (r.get('epoch_s') or '') != '' and (r.get('e_eff_mhz') or '') != '']
    s = [(t, e) for t, e in s if t is not None and e is not None and t - ff >= 0]
    if not s:
        return None
    low = run = 0
    onset = first = None
    for t, e in s:
        if e < emhz:
            low += 1
            run += 1
            if run == 1:
                first = t - ff
            if run >= min_rows and onset is None:
                onset = first
        else:
            run = 0
    lw = nw = None
    if win and win[0] and win[1]:
        sw = [e for t, e in s if win[0] <= t <= win[1]]
        lw, nw = sum(1 for e in sw if e < emhz), len(sw)
    return {'onset_s': onset, 'slow_pct': 100.0 * low / len(s), 'low_rows': low, 'rows': len(s),
            'span_s': s[-1][0] - ff, 'low_rows_window': lw, 'rows_window': nw}


def sod(h, m, s):
    return int(h) * 3600 + int(m) * 60 + float(s)


def host_at(rd, ts):
    """The sys.csv row nearest to a game.log time stamp (local wall clock), within 2 s."""
    m = re.match(r'^\d{4}-\d\d-\d\d (\d\d):(\d\d):(\d\d(?:\.\d+)?)$', ts or '')
    rows = read_csv(os.path.join(rd, 'sys.csv')) if (rd and m) else None
    if not rows:
        return None
    t = sod(*m.groups())
    best = None
    for r in rows:
        mw = re.match(r'^(\d\d):(\d\d):(\d\d(?:\.\d+)?)$', (r.get('wall') or '').strip())
        if mw:
            dt = abs(sod(*mw.groups()) - t)
            if best is None or dt < best[0]:
                best = (dt, r)
    if not best or best[0] > 2.0:
        return None
    r = best[1]
    return {'wall': r.get('wall'), 'cpu_util_pct': num(r.get('cpu_util_pct')), 'p_util_pct': num(r.get('p_util_pct')),
            'e_util_pct': num(r.get('e_util_pct')), 'e_eff_mhz': num(r.get('e_eff_mhz'))}


def stuck(rd):
    """STUCK-LOCK episodes (a 'still not acquired after' line starts one) with the owner lr and site, the hang dumps
    the log names, and every *.dmp file under the run dir."""
    eps, named, lines = [], [], 0
    for lp in sorted(glob.glob(os.path.join(rd, 'game*.log'))) if rd else []:
        cur = None
        try:
            with open(lp, encoding='utf-8', errors='replace') as fh:
                for ln in fh:
                    if 'STUCK-LOCK' in ln:
                        lines += 1
                        if EP_START in ln:
                            m = TS_RE.match(ln)
                            cur = {'log': os.path.basename(lp), 'owner_lr': None,
                                   'ts': ('%s %s:%s:%s' % m.groups()) if m else None}
                            eps.append(cur)
                        elif cur is not None and cur['owner_lr'] is None and 'owner' in ln:
                            mm = LR_RE.search(ln)
                            if mm:
                                cur['owner_lr'] = mm.group(1).upper()
                    if 'Minidump written to' in ln:
                        mm = DUMP_RE.search(ln)
                        if mm:
                            named.append(mm.group(1))
        except OSError:
            pass
    for e in eps:
        lr = e['owner_lr']
        e['site'] = next((s for s, lrs in SITES if lr in lrs), 'other' if lr else '?')
        e['host'] = host_at(rd, e['ts'])
    dmps = sorted(os.path.relpath(p, rd) for p in glob.glob(os.path.join(rd, '**', '*.dmp'), recursive=True)) \
        if rd else []
    return {'episodes': eps, 'lines': lines, 'dumps_named': named, 'dmp_files': dmps}


def planned(d):
    """(Counter of planned scored runs per arm, Counter of planned cold runs) from plan.txt; (None, None) without."""
    try:
        with open(os.path.join(d, 'plan.txt'), encoding='utf-8', errors='replace') as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None, None
    out, cold = collections.Counter(), collections.Counter()
    for ln in lines:
        m = re.match(r'^round\s+\d+\s+(.*)$', ln)
        if m:
            out.update(m.group(1).split())
        m = re.match(r'^cold\s+(\S+)\s', ln)
        if m:
            cold[m.group(1)] += 1
    return out, cold


def failed(x):
    r = x['row']
    why = []
    if (r.get('status') or '').strip() != 'OK':
        why.append('status %s' % r.get('status'))
    ex = (r.get('exit_code') or '').strip().lower()
    if ex not in ('', '0', '0x00000000'):
        why.append('exit %s' % r.get('exit_code'))
    if 'kill' in (r.get('close') or '').lower():
        why.append('close %s' % r.get('close'))
    if (r.get('runner_exit') or '').strip() not in ('', '0'):
        why.append('runner_exit %s' % r.get('runner_exit'))
    return why


# ---------------------------------------------------------------- loading
def load_pass(d, p, roff, soff, a):
    runs, order, ref0, title, _ = N.load_runs(d, RO.ns_methods(a))
    rows = W.read_rows(os.path.join(d, 'results.csv')) or []
    mj = W.load_json(os.path.join(d, 'matrix.json')) or {}
    if len(rows) != len(runs):
        raise SystemExit('results.csv changed while reading %s' % d)
    maxr = 0
    for x, r in zip(runs, rows):
        rd = W.resolve_run_dir(d, r)
        s, src = RO.sys_block(rd)
        x['power'] = RO.power_info(s, src)
        fx = (r.get('flags_excluding') or '').strip()
        if x['excluded'] and fx:
            x['why'] = ['excluded (%s)' % fx if y == 'excluded' else y for y in x['why']]
        x['pass'], x['rd'], x['row'] = p, rd, dict((k, r.get(k)) for k in ROWKEYS)
        rv = str(x['round'] or '').strip()
        x['round_pass'] = rv
        if rv.isdigit() and int(rv) > 0:
            maxr = max(maxr, int(rv))
            x['round'] = str(int(rv) + roff)
        sq = str(x['seq'] or '').strip()
        x['seq_pass'] = sq
        if sq.isdigit():
            x['seq'] = str(int(sq) + soff)
        sj = W.load_json(os.path.join(rd, 'sys.json')) if rd else None
        sj = sj if isinstance(sj, dict) else {}
        sw = sj.get('window') if isinstance(sj.get('window'), dict) else {}
        win = (num(sj.get('window_start_epoch')), num(sj.get('window_end_epoch')))
        x['host'] = {'eff_mhz': num(sw.get('eff_mhz_mean')), 'eff_min': num(sw.get('eff_mhz_min')),
                     'p_mhz': num(sw.get('p_eff_mhz_mean')), 'e_mhz': num(sw.get('e_eff_mhz_mean')),
                     'p_util': num(sw.get('p_util_mean')), 'e_util': num(sw.get('e_util_mean')),
                     'cpu_util': num(sw.get('cpu_util_mean')), 'start': hhmmss(win[0])}
        x['cpu'] = dict(thread_busy(rd), cores=x.get('cores_csv'))
        x['slow'] = slow_state(rd, a.slow_emhz, a.slow_rows, win) if rd else None
        x['stuck'] = stuck(rd) if rd else {'episodes': [], 'lines': 0, 'dumps_named': [], 'dmp_files': []}
        x['failed'] = failed(x)
    return runs, order, ref0, title, mj, maxr


def load_pool(dirs, a):
    runs, notes, passes = [], [], []
    order = ref0 = mj0 = title0 = None
    roff = soff = 0
    for p, d in enumerate(dirs, 1):
        d = os.path.abspath(d)
        if not os.path.isfile(os.path.join(d, 'results.csv')):
            raise SystemExit('no results.csv in %s' % d)
        rs, order_p, r0, title, mj, maxr = load_pass(d, p, roff, soff, a)
        if order is None:
            order, ref0, mj0, title0 = list(order_p), r0, mj, title
        else:
            if order_p != order:
                notes.append('pass %d arm order %s differs from pass 1 (%s)' % (p, ', '.join(order_p), ', '.join(order)))
            order.extend(arm for arm in order_p if arm not in order)
            if r0 != ref0:
                notes.append('pass %d ref %s differs from pass 1 ref %s' % (p, r0, ref0))
        pl, pc = planned(d)
        starts = sorted(x['host']['start'] for x in rs if x['host'].get('start'))
        passes.append({'pass': p, 'dir': d, 'rows': len(rs), 'rounds': maxr, 'round_offset': roff, 'seq_offset': soff,
                       'matrix_sha256': sha256(os.path.join(d, 'matrix.json')),
                       'results_sha256': sha256(os.path.join(d, 'results.csv')),
                       'planned': dict(pl) if pl is not None else None,
                       'planned_cold': dict(pc) if pc is not None else None,
                       'first_window': starts[0] if starts else None, 'last_window': starts[-1] if starts else None})
        runs.extend(rs)
        roff += maxr
        soff += len(rs)
    if len(set(p['matrix_sha256'] for p in passes)) > 1:
        notes.append('matrix.json differs between the passes: %s' % ', '.join(str(p['matrix_sha256'])[:16] for p in passes))
    ref, ref_src = RO.pick_ref(mj0, order, ref0, a.ref)
    return runs, order, ref, ref_src, title0, passes, notes


def tokens(text):
    return [t.strip() for t in (text or '').split(',') if t.strip()]


def match(x, tok):
    m = re.match(r'^p(\d+)(?::(.+))?$', tok)
    if m:
        if str(x['pass']) != m.group(1):
            return False
        rest = m.group(2)
        if rest is None:
            return True
        mr = re.match(r'^r(\d+)$', rest)
        if mr:
            return str(x['round_pass']) == mr.group(1)
        return RO.short(x['name']) == rest
    return x['name'] == tok


def select(runs, toks, label):
    hit = set()
    for x in runs:
        x['keep'], x['why'] = x['keep0'], list(x['why0'])
        if x['keep'] and any(match(x, t) for t in toks):
            x['keep'] = False
            x['why'].append(label)
        for t in toks:
            if match(x, t):
                hit.add(t)
    return [t for t in toks if t not in hit]


def set_tstd(runs, hT):
    for x in runs:
        x['t_std'] = N.std_mix(x.get('_TL'), x.get('_TH'), hT)


def kept_hT(runs):
    hs = [x['hT'] for x in runs if x['keep'] and x.get('hT') is not None and 0.0 < x['hT'] < 1.0]
    return statistics.median(hs) if hs else None


# ---------------------------------------------------------------- numbers
def lin_ci(vals, ref, order):
    """Arm means and the change vs the ref with a pooled 95 % CI on the linear scale (df = runs - arms)."""
    if ref not in vals:
        return None
    ss, df = 0.0, 0
    for lst in vals.values():
        v = [y for _, y in lst]
        if len(v) >= 2:
            m = statistics.fmean(v)
            ss += sum((u - m) ** 2 for u in v)
            df += len(v) - 1
    sd = math.sqrt(ss / df) if df else None
    t = N.t975(df) if df else None
    rv = [y for _, y in vals[ref]]
    rm = statistics.fmean(rv)
    arms = collections.OrderedDict()
    for arm in order:
        if arm not in vals:
            continue
        av = [y for _, y in vals[arm]]
        e = {'n': len(av), 'mean': statistics.fmean(av)}
        if arm != ref:
            e['diff'] = e['mean'] - rm
            if sd is not None:
                hw = t * sd * math.sqrt(1.0 / len(av) + 1.0 / len(rv))
                e['ci'] = (e['diff'] - hw, e['diff'] + hw)
        arms[arm] = e
    return {'ref_mean': rm, 'sd': sd, 'df': df, 'arms': arms}


def cpu_block(kept, order, ref):
    rounds, blk = N.round_block(kept)
    out = collections.OrderedDict()
    g = N.getter('cpu')
    for key, label in CPU:
        vals = N.collect(kept, g, key)
        if ref not in vals:
            continue
        out[key] = {'label': label, 'lin': lin_ci(vals, ref, order), 'gm': N.summarize(vals, ref, order, -1),
                    'block': N.ancova(vals, blk, ref, order, -1) if len(rounds) >= 2 else None}
    return out


def paired_block(kept, order, ref):
    out = []
    for field, key, label in PAIRED:
        p = N.paired(kept, N.getter(field), key, ref, order)
        if p:
            out.append({'field': field, 'key': key, 'label': label, 'arms': p})
    return out


def nested(s1, s2, alpha):
    """Nested F test: s2 adds (k2 - k1) covariates to s1 (both fitted on the same runs)."""
    if not s1 or not s2 or s1.get('sd_ln') is None or s2.get('sd_ln') is None:
        return None
    k, df2 = (s2.get('k') or 0) - (s1.get('k') or 0), s2.get('df') or 0
    ss1, ss2 = s1['sd_ln'] ** 2 * s1['df'], s2['sd_ln'] ** 2 * df2
    if k < 1 or df2 < 1 or ss2 <= 0.0:
        return None
    F = max(0.0, ss1 - ss2) / k / (ss2 / df2)
    p = RO.f_sf(F, k, df2)
    return {'F': F, 'df': [k, df2], 'p': p, 'sig': p is not None and p < alpha}


def pass_tests(kept, order, ref, M, alpha):
    ps = sorted(set(x['pass'] for x in kept))
    if len(ps) < 2:
        return None, None
    rounds, blk = N.round_block(kept)
    arms = [arm for arm in order if arm != ref and any(x['arm'] == arm for x in kept)]
    pcov = lambda x: [1.0 if x['pass'] == p else 0.0 for p in ps[1:]]
    icov = lambda x: blk(x) + [1.0 if (x['arm'] == arm and x['pass'] == p) else 0.0 for arm in arms for p in ps[1:]]
    pt, it = {}, {}
    g = N.getter('t_std')
    for key, sign, _ in KEYS:
        vals = N.collect(kept, g, key)
        pt[key] = nested((M.get('T-std') or {}).get(key), N.ancova(vals, pcov, ref, order, sign), alpha)
        it[key] = nested((M.get(BLOCK) or {}).get(key), N.ancova(vals, icov, ref, order, sign), alpha) \
            if len(rounds) >= 2 else None
    return pt, it


def analyse_sel(runs, order, ref, a):
    hT = kept_hT(runs)
    set_tstd(runs, hT)
    R = RO.compute(runs, order, ref, a.alpha, a.putil, a.emhz)
    kept = [x for x in runs if x['keep']]
    R['hT_ref'] = hT
    R['cpu'] = cpu_block(kept, order, ref)
    R['paired'] = paired_block(kept, order, ref)
    R['pass_test'], R['interaction'] = pass_tests(kept, order, ref, R['methods'], a.alpha)
    R['left'] = [(x['name'], x['why']) for x in runs if not x['keep']]
    return R


def counts(runs, order, passes):
    out = collections.OrderedDict()
    for arm in order:
        xs = [x for x in runs if x['arm'] == arm]
        sc = [x for x in xs if x['scored']]
        eps = [(x['name'], e) for x in xs for e in x['stuck']['episodes']]
        out[arm] = {
            'planned': sum((p['planned'] or {}).get(arm, 0) for p in passes),
            'planned_cold': sum((p['planned_cold'] or {}).get(arm, 0) for p in passes),
            'rows': len(xs), 'scored': len(sc), 'timed': sum(1 for x in sc if x['valid']),
            'kept': sum(1 for x in xs if x['keep0']),
            'failed': [(x['name'], x['failed']) for x in xs if x['failed']],
            'stuck_runs': sorted(set(nm for nm, _ in eps)), 'episodes': len(eps),
            'sites': dict(collections.Counter('%s %s' % (e['site'], e['owner_lr']) for _, e in eps)),
            'stuck_lines': sum(x['stuck']['lines'] for x in xs),
            'dumps': [(x['name'], f) for x in xs for f in x['stuck']['dmp_files']],
            'slow_runs': [x['name'] for x in xs if x.get('slow') and x['slow']['onset_s'] is not None],
            'slow_window_runs': [x['name'] for x in xs if x.get('slow') and (x['slow'].get('low_rows_window') or 0) > 0],
            'no_sys': [x['name'] for x in xs if not x.get('slow')],
            'hang_host': [(nm, e['host']) for nm, e in eps]}
    return out


def self_check(dirs, PP, a):
    """readout.py's own analyse() on each folder vs this tool's per-pass numbers; returns (ok, lines)."""
    lines, ok = [], True
    for p, d in enumerate(dirs, 1):
        ns = argparse.Namespace(ref=a.ref, rounds=None, drop=None, overlay=None, alpha=a.alpha, putil=a.putil,
                                emhz=a.emhz, all=a.all, light_ms=a.light_ms)
        R1, R2 = RO.analyse(d, ns), PP[p]
        worst, n = 0.0, 0
        for mid in ('raw', 'T-std', BLOCK):
            for key, _, _ in KEYS:
                s1, s2 = (R1['methods'].get(mid) or {}).get(key), (R2['methods'].get(mid) or {}).get(key)
                if (s1 is None) != (s2 is None):
                    worst = float('inf')
                    continue
                if s1 is None:
                    continue
                for arm, e1 in s1['arms'].items():
                    e2 = s2['arms'].get(arm) or {}
                    for f in ('gm_delta_pct', 'delta_pct', 'med'):
                        if e1.get(f) is not None:
                            worst = max(worst, abs(e1[f] - (e2.get(f) if e2.get(f) is not None else float('inf'))))
                            n += 1
                    if e1.get('ci_pct'):
                        worst = max(worst, max(abs(u - v) for u, v in zip(e1['ci_pct'], e2.get('ci_pct') or (1e9, 1e9))))
                        n += 1
        same = R1['decision']['primary'] == R2['decision']['primary'] and abs((R1['hT_ref'] or 0) - (R2['hT_ref'] or 0)) < 1e-12
        good = worst < 1e-9 and same
        ok = ok and good
        lines.append('self-check pass %d (%s): %s, %d numbers, max |diff| %.3g, primary %s / %s' % (
            p, os.path.basename(d), 'PASS' if good else 'FAIL', n, worst, R1['decision']['primary'],
            R2['decision']['primary']))
    return ok, lines


# ---------------------------------------------------------------- markdown
def cic(e, nd=1):
    if not e or e.get('ci_pct') is None:
        return '-'
    return '%s [%s, %s]%s' % (sgn(e['gm_delta_pct'], nd), sgn(e['ci_pct'][0], nd), sgn(e['ci_pct'][1], nd),
                              ' *' if e.get('ci_excludes_0') else '')


def lin_cell(e, nd=2):
    if not e or e.get('diff') is None:
        return '-'
    return '%s [%s, %s]' % (sgn(e['diff'], nd), sgn(e['ci'][0], nd), sgn(e['ci'][1], nd)) if e.get('ci') else sgn(e['diff'], nd)


def test_txt(t):
    return '-' if not t else 'F = %.2f on (%d, %d), p = %s' % (t['F'], t['df'][0], t['df'][1], RO.pfmt(t['p']))


def primary_cells(R, keys=MAIN):
    prim = R['decision']['primary']
    return dict((key, (R['methods'].get(prim) or {}).get(key) or {}) for key in keys)


def render_counts(w, C, passes):
    w('| arm | planned (+cold) | rows | timed | kept | failed | STUCK-LOCK episodes (runs; owner sites) | hang dumps | '
      'slow-state runs (onset; low rows in window) | host CPU at each hang |')
    w('|---|---|---|---|---|---|---|---|---|---|')
    for arm, c in C.items():
        w('| %s | %d (+%d) | %d | %d | %d | %s | %s | %s | %s | %s |' % (
            arm, c['planned'], c['planned_cold'], c['rows'], c['timed'], c['kept'],
            '; '.join('%s (%s)' % (nm, ', '.join(why)) for nm, why in c['failed']) or '0',
            ('%d (%s; %s)' % (c['episodes'], ', '.join(c['stuck_runs']), ', '.join('%s x%d' % kv for kv in c['sites'].items())))
            if c['episodes'] else ('0' if not c['stuck_lines'] else '0 (%d STUCK-LOCK lines without a start)' % c['stuck_lines']),
            ', '.join('%s %s' % d for d in c['dumps']) or '0',
            ('%d: %s' % (len(c['slow_runs']), ', '.join(c['slow_runs']))) if c['slow_runs'] else '0',
            '; '.join('%s cpu %s %% P %s %% E %s MHz' % (nm, fmt((h or {}).get('cpu_util_pct')),
                                                      fmt((h or {}).get('p_util_pct')), fmt((h or {}).get('e_eff_mhz'), 0))
                      for nm, h in c['hang_host']) or '-'))


def render_main(w, R, title_note=''):
    ref, arms = R['ref'], R['arms']
    prim = R['decision']['primary']
    w('- **Primary: %s.** %s%s' % (prim, R['decision']['why'], title_note))
    w('- %s' % RO.round_line(R))
    if R.get('pass_test'):
        w('- Pass term (one-way T-std + pass block): median ms %s; fps %s.' % (
            test_txt(R['pass_test'].get('p50_ms')), test_txt(R['pass_test'].get('fps'))))
    if R.get('interaction'):
        w('- Arm x pass (B-block + per-arm pass terms; does an arm\'s delta differ between the passes?): median ms %s; '
          'fps %s; p99 %s; 1 %% low %s.' % tuple(test_txt(R['interaction'].get(k)) for k in ('p50_ms', 'fps', 'p99_ms',
                                                                                            'low1_fps')))
    w('')
    w('Cells: the GM delta vs %s in %%, with the pooled 95 %% CI; `*` = the CI excludes 0. Bold = the primary.' % ref)
    w('')
    for keys in (MAIN, TAILS):
        R_ = R
        for line in RO.table_head(R_):
            w(line)
        for key in keys:
            for mid in RO.PRIMARIES:
                row = RO.table_row(R_, mid, key, bold=(mid == prim))
                if row:
                    w(row)
        for key in keys:
            row = RO.table_row(R_, 'raw', key)
            if row:
                w(row)
        w('')


def render_cpu(w, R):
    ref, arms = R['ref'], R['arms']
    w('| metric | %s mean | %s |' % (ref, ' | '.join('%s: mean; change [95 %% CI]; GM %% one-way; GM %% B-block' % arm
                                                        for arm in arms)))
    w('|---|---|%s' % ('---|' * len(arms)))
    for key, c in R['cpu'].items():
        lin, gm, bl = c['lin'] or {}, c['gm'] or {}, c['block'] or {}
        cells = []
        for arm in arms:
            le = (lin.get('arms') or {}).get(arm) or {}
            cells.append('%s; %s; %s; %s' % (fmt(le.get('mean'), 2), lin_cell(le), cic((gm.get('arms') or {}).get(arm)),
                                             cic((bl.get('arms') or {}).get(arm))))
        w('| %s | %s | %s |' % (c['label'], fmt(lin.get('ref_mean'), 2), ' | '.join(cells)))
    w('')


def render_paired(w, R):
    arms = R['arms']
    w('Within-round deltas 100 (arm - %s) / %s, one per round in which both ran: mean +- 95 %% t half-width '
      '(df = rounds - 1), median, and the rounds in which the arm was higher.' % (R['ref'], R['ref']))
    w('')
    w('| metric | %s |' % ' | '.join(arms))
    w('|---|%s' % ('---|' * len(arms)))
    for pb in R['paired']:
        cells = []
        for arm in arms:
            e = pb['arms'].get(arm)
            cells.append('-' if not e else '%s +- %s (med %s; higher %d/%d)' % (
                sgn(e['mean'], 2), fmt(e.get('hw95'), 2), sgn(e['med'], 2), e['up'], e['n']))
        w('| %s | %s |' % (pb['label'], ' | '.join(cells)))
    w('')


def render_pass(w, PP, ref, arms):
    w('| pass | kept | primary (round test) | %s |' % ' | '.join('%s: median ms; fps; p99; 1 %% low; cores (change)' % arm
                                                             for arm in arms))
    w('|---|---|---|%s' % ('---|' * len(arms)))
    for p, Rp in PP.items():
        prim = Rp['decision']['primary']
        t = Rp['round_test'].get('p50_ms')
        cells = []
        for arm in arms:
            m = dict((key, ((Rp['methods'].get(prim) or {}).get(key) or {}).get('arms', {}).get(arm)) for key, _, _ in KEYS)
            le = (((Rp['cpu'].get('cores') or {}).get('lin') or {}).get('arms') or {}).get(arm) or {}
            cells.append('%s; %s; %s; %s; %s' % (cic(m['p50_ms']), cic(m['fps']), cic(m['p99_ms']), cic(m['low1_fps']),
                                                 lin_cell(le)))
        w('| %d | %d | %s (%s) | %s |' % (p, sum(1 for x in Rp['runs'] if x['keep']), prim,
                                          ('p = %s' % RO.pfmt(t['p'])) if t else '-', ' | '.join(cells)))
    w('')


def render_variant(w, label, toks, Rv, miss):
    prim = Rv['decision']['primary']
    w('**%s** (left out: %s%s): primary %s; %s' % (
        label, ', '.join(toks), ('; no match: %s' % ', '.join(miss)) if miss else '', prim, RO.round_line(Rv)))
    w('')
    w('| metric | %s |' % ' | '.join('%s (n=%d)' % (arm, Rv['n'].get(arm, 0)) for arm in Rv['arms']))
    w('|---|%s' % ('---|' * len(Rv['arms'])))
    for key, _, lab in KEYS:
        s = (Rv['methods'].get(prim) or {}).get(key) or {}
        w('| %s %s | %s |' % (prim, lab, ' | '.join(cic((s.get('arms') or {}).get(arm)) for arm in Rv['arms'])))
    if prim != 'raw':
        for key, _, lab in KEYS:
            s = (Rv['methods'].get('raw') or {}).get(key) or {}
            if s:
                w('| raw %s | %s |' % (lab, ' | '.join(cic((s.get('arms') or {}).get(arm)) for arm in Rv['arms'])))
    lin = ((Rv['cpu'].get('cores') or {}).get('lin') or {}).get('arms') or {}
    w('| cpu cores change | %s |' % ' | '.join(lin_cell(lin.get(arm)) for arm in Rv['arms']))
    w('')


def render_runs(w, runs, flagset):
    w('| seq | pass | round | arm | run | window start | kept | frames | raw median ms | T-std median ms | raw fps | '
      'raw p99 ms | cores | Main % | GPU % | TQ % | eff MHz | P MHz | E MHz | P util % | E util % | low E rows in '
      'window (onset s) | STUCK | light share | flag |')
    w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for x in sorted(runs, key=lambda y: num(y['seq']) or 0):
        raw, ts, c, h, s = x.get('raw') or {}, x.get('t_std') or {}, x.get('cpu') or {}, x.get('host') or {}, x.get('slow')
        w('| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | '
          '%s | %s | %s | %s |' % (
              x['seq'], x['pass'], x['round'] if x['scored'] else 'cold', x['arm'], x['name'], h.get('start') or '-',
              'yes' if x['keep'] else 'no: ' + ', '.join(x['why']), x['row'].get('frames') or '-',
              fmt(raw.get('p50_ms'), 3), fmt(ts.get('p50_ms'), 3), fmt(raw.get('fps')), fmt(raw.get('p99_ms'), 2),
              fmt(c.get('cores'), 2), fmt(c.get('main_busy')), fmt(c.get('gpu_busy')), fmt(c.get('tq_busy')),
              fmt(h.get('eff_mhz'), 0), fmt(h.get('p_mhz'), 0), fmt(h.get('e_mhz'), 0), fmt(h.get('p_util')),
              fmt(h.get('e_util')), ('%s/%s (%s)' % (s.get('low_rows_window'), s.get('rows_window'),
                                                    fmt(s['onset_s'], 0) if s.get('onset_s') is not None else '-'))
              if s else 'no sys.csv', len(x['stuck']['episodes']) or '', fmt(x.get('ls_T'), 3),
              'yes' if x['name'] in flagset else ''))
    w('')


def render(P):
    out = []
    w = out.append
    R, PP, C = P['primary'], P['per_pass'], P['counts']
    ref, arms = R['ref'], R['arms']
    runs = R['runs']
    kept = [x for x in runs if x['keep']]
    w('# Pooled read-out: %s' % (P['label'] or ' + '.join(os.path.basename(p['dir']) for p in P['passes'])))
    w('')
    if P.get('title'):
        w('- title: %s' % P['title'])
    for p in P['passes']:
        w('- pass %d: `%s` (%d rows; rounds %d-%d pooled; windows %s-%s; results.csv sha256 %s...)' % (
            p['pass'], p['dir'], p['rows'], p['round_offset'] + 1, p['round_offset'] + p['rounds'],
            p['first_window'] or '-', p['last_window'] or '-', str(p['results_sha256'])[:16]))
    w('- command: `%s`' % P['command'])
    w('- ref **%s** (%s); arms %s; pooled rounds %s; kept %d of %d runs (%s); left out: %s.' % (
        ref, P['ref_src'], ', '.join(arms), ', '.join(str(r) for r in R['rounds']), len(kept), len(runs),
        ', '.join('%s %d' % kv for kv in R['n'].items()),
        '; '.join('%s (%s)' % (nm, ', '.join(why)) for nm, why in R['left']) or 'none'))
    w('- T split: light = frame time < %s ms; pooled hT_ref = %s; per pass %s.' % (
        ', '.join('%g' % v for v in R.get('light_ms') or []) or '-', fmt(R.get('hT_ref'), 3),
        ', '.join('%d: %s' % (p, fmt(Rp.get('hT_ref'), 3)) for p, Rp in PP.items())))
    w('- G11 power: %s' % P['g11']['line'])
    for nt in P.get('notes') or []:
        w('- note: %s' % nt)
    for ln in P.get('self_check') or []:
        w('- %s' % ln)
    w('')
    w('## 1. Runs per arm (PROPOSAL.md S3)')
    w('')
    render_counts(w, C, P['passes'])
    w('')
    w('## 2. Primary result (pooled)')
    w('')
    render_main(w, R)
    w('## 3. CPU (process cores and thread busy)')
    w('')
    w('Change = arm mean - %s mean with the pooled 95 %% CI (linear, df = runs - arms). GM %% = GM delta with the pooled '
      'CI on ln (one-way, then B-block over the pooled rounds); `*` = the CI excludes 0.' % ref)
    w('')
    render_cpu(w, R)
    w('## 4. Paired within-round deltas (pooled rounds)')
    w('')
    render_paired(w, R)
    w('## 5. Per pass (each pass alone, readout.py numbers)')
    w('')
    w('Cells: the primary\'s GM delta [95 % CI] for median ms; fps; p99; 1 % low; then the cores change [95 % CI].')
    w('')
    render_pass(w, PP, ref, arms)
    if P['variants']:
        w('## 6. Variants (the pool without the listed runs)')
        w('')
        for v in P['variants']:
            render_variant(w, v['label'], v['tokens'], v['R'], v['missing'])
    w('## 7. Guards (pooled)')
    w('')
    ga, gb, gc = R['guards']['a'], R['guards']['b'], R['guards']['c']
    if ga and ga.get('F') is not None:
        w('- (a) Light share per arm: %s. One-way F = %.2f on (%d, %d), p = %s: %s.' % (
            ', '.join('%s %s' % (arm, fmt(v, 3)) for arm, v in ga['means'].items()), ga['F'], ga['df'][0], ga['df'][1],
            RO.pfmt(ga['p']), 'WARNING, an arm may move the mix (read T-light / T-heavy and raw)' if ga['warn'] else 'OK'))
    w('- (b) Raw CI vs the %s CI (overlap = agrees): %s.' % (R['decision']['primary'], '; '.join(
        '%s: %s' % (LABEL[key], ', '.join('%s %s' % kv for kv in gb.get(key, {}).items()) or '-') for key in MAIN)))
    w('- (c) Host flag (sys.json window P util >= %g %% and E MHz < %g): %d of %d kept runs%s.' % (
        gc['putil'], gc['emhz'], len(gc['flagged']), len(kept),
        (' (%s)' % ', '.join(gc['flagged'])) if gc['flagged'] else ''))
    if ga and ga.get('warn'):
        w('')
        for line in RO.table_head(R):
            w(line)
        for key in MAIN:
            for mid in ('T-light', 'T-heavy'):
                row = RO.table_row(R, mid, key)
                if row:
                    w(row)
    w('')
    w('## 8. Runs (pooled order; host state over the measured window)')
    w('')
    w('Main / GPU / TQ %% = threads.csv busy %% of Main XThread, GPU Commands and rex::thread::TimerQueue. eff / P / E '
      'MHz and util = sys.json window means. Low E rows = sys.csv rows in the window with E-core MHz < %g (onset = '
      'Agent 11\'s slow-state onset from the first frame, - = none).' % P['params']['slow_emhz'])
    w('')
    render_runs(w, runs, set(gc['flagged']))
    return '\n'.join(out) + '\n'


# ---------------------------------------------------------------- json and main
def r_json(R):
    out = dict((k, R.get(k)) for k in ('ref', 'order', 'arms', 'n', 'rounds', 'unbalanced_rounds', 'alpha', 'hT_ref',
                                       'light_ms', 'decision', 'round_test', 'guards', 'methods', 'cpu', 'paired',
                                       'pass_test', 'interaction', 'left'))
    return out


def run_json(x, flagset):
    rec = RO.run_rec(x, flagset)
    rec.update(dict((k, x.get(k)) for k in ('pass', 'round_pass', 'seq_pass', 'rd', 'row', 'cpu', 'host', 'slow',
                                            'failed')))
    rec['stuck'] = x.get('stuck')
    return rec


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('dirs', nargs='+', help='run-matrix.ps1 output dirs of one window, in pass order')
    ap.add_argument('-o', '--out', help='write the markdown here (without -o: stdout)')
    ap.add_argument('--json', help='write the numbers as json here')
    ap.add_argument('--label', help='window name for the title, e.g. W9')
    ap.add_argument('--ref', help='reference arm (default: matrix.json)')
    ap.add_argument('--drop', help='leave these runs out of every number (TOKENS)')
    ap.add_argument('--variant', action='append', default=[], help='LABEL=TOKENS: also read the pool without these')
    ap.add_argument('--alpha', type=float, default=0.05)
    ap.add_argument('--putil', type=float, default=90.0, help='host flag: sys.json window P util at or above this')
    ap.add_argument('--emhz', type=float, default=600.0, help='host flag: and E-core MHz below this')
    ap.add_argument('--slow-emhz', type=float, default=800.0, help="slow state: E-core MHz below this (Agent 11)")
    ap.add_argument('--slow-rows', type=int, default=3, help='slow state: this many low rows in a row')
    ap.add_argument('--light-ms', type=float, default=None, help='T split in ms (default: frames.json light_ms)')
    ap.add_argument('--all', action='store_true', help='keep runs that are not valid timing')
    ap.add_argument('--self-check', action='store_true', help="compare each pass with readout.py's analyse()")
    ap.add_argument('--normal-priority', action='store_true', help="don't lower this process to Below Normal")
    ap.add_argument('--cache', help='also pickle the computed numbers here (re-render later with --from-cache)')
    ap.add_argument('--from-cache', help='skip the analysis: render the numbers pickled by an earlier --cache run '
                                         '(DIRS are then ignored)')
    return ap.parse_args(argv)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    a = parse_args(argv)
    if not a.normal_priority:
        RO.below_normal()
    if a.from_cache:
        with open(a.from_cache, 'rb') as fh:
            P = pickle.load(fh)
        if a.variant:
            add_variants(P, a)
        return emit(P, a)
    if a.self_check and a.drop:
        raise SystemExit('--self-check compares the full passes; run it without --drop')
    command = 'python -B build\\agent7\\readout\\pool_readout.py ' + ' '.join(
        ('"%s"' % s) if (' ' in s or ';' in s) else s for s in argv if s != '--cache' and not s.endswith('.pkl'))
    runs, order, ref, ref_src, title, passes, notes = load_pool(a.dirs, a)
    for x in runs:
        x['keep0'], x['why0'] = x['keep'], list(x['why'])
    base = tokens(a.drop)
    # per pass (the --drop selection, each pass with its own hT_ref)
    miss = select(runs, base, '--drop')
    if miss:
        notes.append('--drop %s matches no run' % ', '.join(miss))
    PP = collections.OrderedDict()
    for p in sorted(set(x['pass'] for x in runs)):
        rs = [x for x in runs if x['pass'] == p]
        Rp = analyse_sel(rs, order, ref, a)
        PP[p] = Rp
    sc_ok, sc_lines = (None, [])
    if a.self_check:
        sc_ok, sc_lines = self_check([p['dir'] for p in passes], PP, a)
    variants = []
    for v in a.variant:
        label, _, toks = v.partition('=')
        tk = tokens(toks)
        miss_v = select(runs, base + tk, label.strip() or 'variant')
        variants.append({'label': label.strip(), 'tokens': tk, 'missing': [t for t in miss_v if t in tk],
                         'R': analyse_sel(runs, order, ref, a)})
    select(runs, base, '--drop')
    R = analyse_sel(runs, order, ref, a)
    C = counts(runs, order, passes)
    P = {'tool': 'pool_readout.py', 'label': a.label, 'title': title, 'command': command, 'passes': passes,
         'ref_src': ref_src, 'notes': notes,
         'params': dict((k, v) for k, v in vars(a).items() if k not in ('out', 'json', 'cache', 'from_cache')),
         'primary': R, 'per_pass': PP, 'variants': variants, 'counts': C, 'g11': RO.g11(runs),
         'self_check': sc_lines, 'self_check_ok': sc_ok, 'all_runs': runs}
    if a.cache:
        try:
            with open(a.cache, 'wb') as fh:
                pickle.dump(P, fh, protocol=pickle.HIGHEST_PROTOCOL)
            sys.stdout.write('wrote %s\n' % a.cache)
        except Exception as ex:  # a cache is a convenience only
            sys.stdout.write('cache not written: %r\n' % (ex,))
    return emit(P, a)


def add_variants(P, a):
    """--from-cache with --variant: read the cached pool again without more runs (no run data is re-loaded).
    Variants whose label is already in the cache are kept as they are."""
    runs, R = P['all_runs'], P['primary']
    ref = R['ref']
    order = R.get('order') or [ref] + [arm for arm in R['arms'] if arm != ref]
    base = tokens((P.get('params') or {}).get('drop'))
    have = set(v['label'] for v in P['variants'])
    added = []
    for v in a.variant:
        label, _, toks = v.partition('=')
        label = label.strip() or 'variant'
        if label in have:
            continue
        tk = tokens(toks)
        miss_v = select(runs, base + tk, label)
        P['variants'].append({'label': label, 'tokens': tk, 'missing': [t for t in miss_v if t in tk],
                              'R': analyse_sel(runs, order, ref, a)})
        added.append(label)
    select(runs, base, '--drop')
    P['primary'] = analyse_sel(runs, order, ref, a)  # same selection as before, so the same numbers
    if added:
        P['notes'].append('variant(s) %s added later from the cache (--from-cache: same runs, nothing re-loaded)'
                          % ', '.join(added))


def emit(P, a):
    R, PP, variants, runs = P['primary'], P['per_pass'], P['variants'], P['all_runs']
    sc_ok, sc_lines = P['self_check_ok'], P['self_check']
    text = render(P)
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
        sys.stdout.write('wrote %s\n' % a.out)
    else:
        sys.stdout.write(text)
    for ln in sc_lines:
        sys.stdout.write(ln + '\n')
    if a.json:
        flagset = set(R['guards']['c']['flagged'])
        J = dict((k, P[k]) for k in ('tool', 'label', 'title', 'command', 'passes', 'ref_src', 'notes', 'params',
                                     'counts', 'g11', 'self_check', 'self_check_ok'))
        J['primary'] = r_json(R)
        J['per_pass'] = dict((str(p), r_json(Rp)) for p, Rp in PP.items())
        J['variants'] = [{'label': v['label'], 'tokens': v['tokens'], 'missing': v['missing'], 'R': r_json(v['R'])}
                         for v in variants]
        J['runs'] = [run_json(x, flagset) for x in runs]
        with open(a.json, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(J, fh, indent=1, default=str)
        sys.stdout.write('wrote %s\n' % a.json)
    return 0 if sc_ok in (None, True) else 3


if __name__ == '__main__':
    sys.exit(main())
