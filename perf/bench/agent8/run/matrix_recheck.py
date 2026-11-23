#!/usr/bin/env python3
"""Recheck a run-matrix output dir: re-derive run validity and per-arm stats from results.csv and each run.json.

Why: run-timing.ps1 (22:00 version) marks a run PROBLEM
  - for ANY new crash dump during the run, even another program's (e.g. ppc_tests.exe.<pid>.dmp), and
  - for SHORT WINDOW when a late 1 s tick shortens the window (perf-notes/agent8-first-boot.md, caveats 1-2).
This script keeps a run whose only problems are foreign dumps or a window of at least --min-cover of the planned
length, then recomputes per-arm stats and deltas against each group's reference, including per-round paired deltas
(roundrobin puts one run of every arm in each round, so pairing cancels slow drift).

Usage:  python bench\\agent8\\run\\matrix_recheck.py <matrix out dir> [--min-cover 0.9] [--write] [--all] [--keep-flagged]
                [--drop-slow] [--slow-emhz 800] [--slow-rows 3]
  --write         also writes <dir>\\recheck.md
  --all           keep runs with valid_timing = False too (agent-launched functional matrices)
  --keep-flagged  keep runs whose run.json has excluded = true (window-4 excluding flags: light_phase,
                  window_before_floor, sys flags on the interactive desktop); by default they are dropped and listed
  --drop-slow     drop runs whose window overlaps the "slow state" (Agent 11's rule, bench/agent11/timerq_slowstate.ps1:
                  sys.csv e_eff_mhz under --slow-emhz for --slow-rows samples in a row). By default such runs are only
                  marked in the `slow` column (onset s after the first-frame signal / share of window samples, `!` = in window)
Stdlib only.
"""
import argparse
import csv
import json
import math
import os
import re
import statistics
import sys

DUMP_RE = re.compile(r'^(?P<exe>.+?)\.(?P<pid>\d+)\.dmp$', re.I)
WALL_RE = re.compile(r'wall between marks ([0-9.]+) s')
GAME_EXE = 'legodimensions.exe'


def num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def load_json(path):
    try:
        with open(path, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x not in (None, '')]
    s = str(v).strip()
    return [s] if s else []


def wall_between_marks(run_dir):
    try:
        with open(os.path.join(run_dir, 'summary.txt'), encoding='utf-8-sig', errors='replace') as f:
            m = WALL_RE.search(f.read())
        return float(m.group(1)) if m else None
    except OSError:
        return None


def classify(rj, row, min_cover):
    """(real problems, benign notes) for one run."""
    real, benign = [], []
    if rj is None:
        probs = [p.strip() for p in (row.get('notes') or '').split(' | ')
                 if p.strip() and not p.strip().lower().startswith('not timing')]
        if row.get('status', '') not in ('OK', 'PROBLEM'):
            real.append('status ' + row.get('status', '?'))
        return real + probs, benign
    pid = str(rj.get('pid', ''))
    planned = num((rj.get('params') or {}).get('seconds'))
    window = num(row.get('window_s'))
    for p in as_list(rj.get('problems')):
        if p.lower().startswith('crash artifacts'):
            arts = as_list(rj.get('artifacts')) or [a.strip() for a in p.split(':', 1)[-1].split(',')]
            mine, foreign = set(), set()
            for a in arts:
                base = os.path.basename(a.strip())
                m = DUMP_RE.match(base)
                if m and not (m.group('exe').lower() == GAME_EXE and m.group('pid') == pid):
                    foreign.add(base)
                else:
                    mine.add(base)
            if mine:
                real.append('crash artifacts of this game: ' + ', '.join(sorted(mine)))
            if foreign:
                benign.append('foreign dumps: ' + ', '.join(sorted(foreign)))
        elif 'SHORT WINDOW' in p.upper():
            if planned and window and window >= min_cover * planned:
                benign.append('short window %.1f of %.0f s' % (window, planned))
            else:
                real.append(p)
        else:
            real.append(p)
    return real, benign


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def slow_state(run_dir, rj, emhz, min_rows):
    """Agent 11's slow-state rule on the run's sys.csv: E-cores under `emhz` MHz for `min_rows` samples in a row
    (rows without e_eff_mhz are skipped, as in timerq_slowstate.ps1). None without sys.csv or a first-frame epoch;
    else {'onset': s after the first-frame signal of the first such stretch (None = never), 'in_window': such a stretch
    overlaps the measure window (run.json sys.window_start_epoch..window_end_epoch), 'win_share': share of window
    samples under emhz (None when the window is unknown)}."""
    ff = num(rj.get('ff_signal_epoch_s'))
    sysb = rj.get('sys') if isinstance(rj.get('sys'), dict) else {}
    ws, we = num(sysb.get('window_start_epoch')), num(sysb.get('window_end_epoch'))
    p = os.path.join(run_dir, 'sys.csv')
    if not ff or not os.path.isfile(p):
        return None
    pts = []
    try:
        with open(p, encoding='utf-8-sig', errors='replace', newline='') as fh:
            for row in csv.DictReader(fh):
                t, e = num(row.get('epoch_s')), num(row.get('e_eff_mhz'))
                if t is None or e is None or t < ff:
                    continue
                pts.append((t, e < emhz))
    except OSError:
        return None
    if not pts:
        return None
    onset, in_win, cur = None, False, []
    for t, low in pts + [(None, False)]:
        if low:
            cur.append(t)
            continue
        if len(cur) >= min_rows:
            if onset is None:
                onset = cur[0]
            if ws is not None and we is not None and cur[0] <= we and cur[-1] >= ws:
                in_win = True
        cur = []
    win = [low for t, low in pts if ws is not None and we is not None and ws <= t <= we]
    return {'onset': None if onset is None else onset - ff, 'in_window': in_win,
            'win_share': (sum(1 for x in win if x) / len(win)) if win else None}


def slow_txt(s):
    if s is None:
        return '-'
    if s['onset'] is None:
        return 'no'
    return '%s s / %s%%%s' % (f(s['onset'], 0), f(None if s['win_share'] is None else 100 * s['win_share'], 0),
                              ' !' if s['in_window'] else '')


def f(v, nd=2, dash='-'):
    return dash if v is None else ('%.*f' % (nd, v))


def hrv(x, key, sub=None):
    """A number from the run's headroom.json (drivers/thread-cpu.ps1), or None."""
    h = x.get('hr') or {}
    if sub:
        h = h.get(sub) or {}
    return num(h.get(key))


def arm_stats(rows):
    meds = [r['median'] for r in rows if r['median'] is not None]
    top1 = [v for v in (hrv(r, 'top1_busy_pct') for r in rows) if v is not None]
    win = sum(r['window'] or 0 for r in rows)
    o33 = sum(r['over33'] or 0 for r in rows)
    o100 = sum(r['over100'] or 0 for r in rows)
    return {
        'n': len(rows),
        'med': med(meds), 'lo': min(meds) if meds else None, 'hi': max(meds) if meds else None,
        'p99': med([r['p99'] for r in rows]), 'p999': med([r['p999'] for r in rows]),
        'o33': (o33 / win * 60) if win > 0 else None, 'o100': (o100 / win * 60) if win > 0 else None,
        'cpu': med([r['cpu'] for r in rows]),
        'cpu_lo': min([r['cpu'] for r in rows if r['cpu'] is not None], default=None),
        'cpu_hi': max([r['cpu'] for r in rows if r['cpu'] is not None], default=None),
        'boot': med([r['boot'] for r in rows]), 'fps': med([r['fps'] for r in rows]),
        'top1': med(top1), 'top1_lo': min(top1, default=None), 'top1_hi': max(top1, default=None),
        'thr_cores': med([hrv(r, 'sum_busy_cores') for r in rows]),
        'gpu': med([hrv(r, 'util_mean', 'gpu') for r in rows]), 'gpu_p90': med([hrv(r, 'util_p90', 'gpu') for r in rows]),
        'hrn': sum(1 for r in rows if r.get('hr')),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('dir')
    ap.add_argument('--min-cover', type=float, default=0.9)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--keep-flagged', action='store_true')
    ap.add_argument('--drop-slow', action='store_true')
    ap.add_argument('--slow-emhz', type=float, default=800.0)
    ap.add_argument('--slow-rows', type=int, default=3)
    a = ap.parse_args()
    d = a.dir
    res = os.path.join(d, 'results.csv')
    if not os.path.isfile(res):
        sys.exit('no results.csv in %s' % d)
    with open(res, encoding='utf-8-sig', errors='replace', newline='') as fh:
        rows = list(csv.DictReader(fh))
    mj = load_json(os.path.join(d, 'matrix.json')) or {}
    arms = mj.get('arms') or []
    order = [x.get('id') for x in arms] or list(dict.fromkeys(r['arm'] for r in rows))
    group_of = {x.get('id'): x.get('group', '') for x in arms}
    for r in rows:
        group_of.setdefault(r['arm'], r.get('group', ''))
    refs = {}
    for x in arms:
        if x.get('ref'):
            refs.setdefault(x.get('group', ''), x.get('id'))
    for g in dict.fromkeys(group_of[i] for i in order if i in group_of):
        if g not in refs:
            ids = [i for i in order if group_of.get(i) == g]
            refs[g] = mj.get('reference') if mj.get('reference') in ids else ids[0]

    out = []
    w = out.append
    w('# Matrix recheck: %s' % os.path.abspath(d))
    w('')
    if mj.get('title'):
        w('%s' % mj['title'])
        w('')
    runs = []
    for r in rows:
        rd = r.get('run_dir', '')
        rj = load_json(os.path.join(rd, 'run.json')) if rd else None
        real, benign = classify(rj, r, a.min_cover)
        scored = r.get('scored', '').lower() == 'true'
        valid = r.get('valid_timing', '').lower() == 'true'
        has_frames = num(r.get('median_ms')) is not None
        rjd = rj or {}
        fx = as_list(rjd.get('flags_excluding'))
        fi = as_list(rjd.get('flags_info'))
        excluded = bool(rjd.get('excluded')) or bool(fx)
        light = rjd.get('light') or {}
        slow = slow_state(rd, rjd, a.slow_emhz, a.slow_rows) if rd else None
        slow_win = bool(slow and slow['in_window'])
        keep = (scored and has_frames and not real and (valid or a.all) and (not excluded or a.keep_flagged)
                and not (a.drop_slow and slow_win))
        why = []
        if not scored:
            why.append('unscored (cold)')
        if not has_frames:
            why.append('no frame stats')
        if not valid:
            why.append('not timing (%s)' % '; '.join(as_list((rj or {}).get('valid_timing_why'))) if rj else 'not timing')
        if excluded:
            why.append('EXCLUDED: %s%s' % (', '.join(fx) or 'excluded', ' (kept: --keep-flagged)' if a.keep_flagged else ''))
        if slow_win and a.drop_slow:
            why.append('SLOW STATE in window (E-cores < %.0f MHz, onset %s s): dropped (--drop-slow)' % (a.slow_emhz, f(slow['onset'], 0)))
        runs.append({
            'seq': r.get('seq'), 'round': r.get('round'), 'arm': r['arm'], 'rep': r.get('rep'), 'status': r.get('status'),
            'scored': scored, 'keep': keep, 'real': real, 'benign': benign, 'why': why,
            'excluded': excluded, 'fx': fx, 'fi': fi, 'ff': num(rjd.get('ff_to_window_s')),
            'light': num(light.get('share_lt_light')), 'rundir': rd, 'slow': slow, 'slow_win': slow_win,
            'median': num(r.get('median_ms')), 'p99': num(r.get('p99_ms')), 'p999': num(r.get('p999_ms')),
            'over33': num(r.get('over33')), 'over100': num(r.get('over100')), 'window': num(r.get('window_s')),
            'cpu': num(r.get('cpu_cores_mean')), 'boot': num(r.get('boot_s')), 'fps': num(r.get('fps_mean')),
            'marks': wall_between_marks(rd) if rd else None,
            'planned': num(((rj or {}).get('params') or {}).get('seconds')),
            'hr': load_json(os.path.join(rd, 'headroom.json')) if rd else None,
        })

    kept = [x for x in runs if x['keep']]
    flagged = [x for x in runs if x['scored'] and x['excluded']]
    slowed = [x for x in runs if x['scored'] and x['slow_win']]
    w('%d result rows; %d scored runs kept (%d of them with only benign problems); min window cover %.0f%%%s; '
      '%d scored runs flagged excluded (%s); %d scored runs with the slow state in their window (E-cores < %.0f MHz '
      'for %d+ samples; %s).'
      % (len(runs), len(kept), sum(1 for x in kept if x['benign']), 100 * a.min_cover,
         '; valid_timing ignored (--all)' if a.all else '', len(flagged),
         'kept: --keep-flagged' if a.keep_flagged else 'dropped', len(slowed), a.slow_emhz, a.slow_rows,
         'dropped: --drop-slow' if a.drop_slow else 'kept; --drop-slow drops them'))
    w('')
    w('## Runs')
    w('')
    w('| seq | round | arm | rep | status | kept | median ms | fps | p99 ms | >33 | >100 | window s | marks s | ff->win s | light | slow | cpu cores | top1 thread busy % (name) | gpu util % | flags | notes |')
    w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for x in runs:
        notes = x['real'] + x['benign'] + ([] if x['keep'] else x['why'])
        if x['hr'] and (x['hr'].get('partial') or x['hr'].get('timed_out')):
            notes = notes + ['headroom partial: %s' % (x['hr'].get('partial_why') or 'timed out')]
        t1n = (x['hr'] or {}).get('top1_name') or (x['hr'] or {}).get('top1_tid') or ''
        flags = ' '.join(['%s!' % s for s in x['fx']] + x['fi'])
        w('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            x['seq'], x['round'], x['arm'], x['rep'], x['status'], 'yes' if x['keep'] else 'no',
            f(x['median']), f(x['fps'], 1), f(x['p99'], 1), f(x['over33'], 0), f(x['over100'], 0), f(x['window'], 1),
            f(x['marks'], 1), f(x['ff'], 1), f(x['light'], 3), slow_txt(x['slow']), f(x['cpu']),
            ('%s (%s)' % (f(hrv(x, 'top1_busy_pct'), 1), t1n)) if x['hr'] else '-',
            f(hrv(x, 'util_mean', 'gpu'), 0), flags or '-', '; '.join(notes).replace('|', '/')))
    w('')
    w('`marks s` is the wall time between the measure marks (summary.txt `align` line); it should be close to the planned window. '
      '`ff->win s` is first-frame signal to window start (floor: min_window_after_ff_s); `light` is the share of window '
      'frames under light_ms; flags ending in `!` are excluding flags. `slow` is the slow-state onset in s after the '
      'first-frame signal / the share of window sys.csv samples with the E-cores under %.0f MHz; `!` = a stretch of %d+ '
      'such samples overlaps the window (Agent 11: not a result); `no` = never; `-` = no sys.csv.' % (a.slow_emhz, a.slow_rows))
    w('')
    if flagged:
        w('## Flagged runs')
        w('')
        w('| seq | arm | rep | excluding flags | info flags | run dir |')
        w('|---|---|---|---|---|---|')
        for x in flagged:
            w('| %s | %s | %s | %s | %s | %s |' % (x['seq'], x['arm'], x['rep'], ', '.join(x['fx']) or '-', ', '.join(x['fi']) or '-',
                                                os.path.basename(x['rundir'] or '') or '-'))
        w('')

    stats = {}
    for arm in order:
        rs = [x for x in kept if x['arm'] == arm]
        if rs:
            stats[arm] = arm_stats(rs)
    w('## Arms (kept runs)')
    w('')
    w('| group | arm | ref | n | median of medians (min..max) ms | p99 ms | p99.9 ms | >33 ms per min | >100 ms per min | cpu cores (min..max) | boot s | fps | top1 thread busy % (min..max), n | thread cores | gpu util % mean (p90) |')
    w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for arm in order:
        s = stats.get(arm)
        if not s:
            continue
        g = group_of.get(arm, '')
        w('| %s | %s | %s | %d | %s (%s..%s) | %s | %s | %s | %s | %s (%s..%s) | %s | %s | %s (%s..%s), %d | %s | %s (%s) |' % (
            g, arm, '*' if refs.get(g) == arm else '', s['n'], f(s['med'], 3), f(s['lo'], 3), f(s['hi'], 3),
            f(s['p99'], 1), f(s['p999'], 1), f(s['o33'], 1), f(s['o100'], 2), f(s['cpu']), f(s['cpu_lo']), f(s['cpu_hi']),
            f(s['boot'], 1), f(s['fps'], 1), f(s['top1'], 1), f(s['top1_lo'], 1), f(s['top1_hi'], 1), s['hrn'],
            f(s['thr_cores']), f(s['gpu'], 0), f(s['gpu_p90'], 0)))
    w('')

    w('## Deltas against each group reference')
    w('')
    w('| group | arm | vs | delta median ms (%) | paired by round: median delta (min..max), rounds faster | delta p99 ms | delta >33/min | delta cpu cores | delta fps % | paired delta top1 busy pts (n) | verdict |')
    w('|---|---|---|---|---|---|---|---|---|---|---|')
    lines = []
    for arm in order:
        g = group_of.get(arm, '')
        ref = refs.get(g)
        if arm == ref or arm not in stats or ref not in stats:
            continue
        s, t = stats[arm], stats[ref]
        dm = s['med'] - t['med'] if None not in (s['med'], t['med']) else None
        pct = (100.0 * dm / t['med']) if dm is not None and t['med'] else None
        rk = {}
        for x in kept:
            rk.setdefault(x['round'], {})[x['arm']] = x['median']
        pairs = [v[arm] - v[ref] for k, v in sorted(rk.items(), key=lambda kv: num(kv[0]) or 0)
                 if arm in v and ref in v and None not in (v[arm], v[ref])]
        pmed = med(pairs)
        faster = sum(1 for p in pairs if p < 0)
        if None in (s['lo'], s['hi'], t['lo'], t['hi']):
            verdict = '-'
        elif s['hi'] < t['lo']:
            verdict = 'FASTER: every run below the reference range'
        elif s['lo'] > t['hi']:
            verdict = 'SLOWER: every run above the reference range'
        else:
            verdict = 'within noise (ranges overlap)'
        dp99 = s['p99'] - t['p99'] if None not in (s['p99'], t['p99']) else None
        d33 = s['o33'] - t['o33'] if None not in (s['o33'], t['o33']) else None
        dcpu = s['cpu'] - t['cpu'] if None not in (s['cpu'], t['cpu']) else None
        dfps = (100.0 * (s['fps'] - t['fps']) / t['fps']) if None not in (s['fps'], t['fps']) and t['fps'] else None
        rt = {}
        for x in kept:
            rt.setdefault(x['round'], {})[x['arm']] = hrv(x, 'top1_busy_pct')
        tpairs = [v[arm] - v[ref] for v in rt.values() if arm in v and ref in v and None not in (v[arm], v[ref])]
        w('| %s | %s | %s | %s (%s%%) | %s (%s..%s), %d of %d | %s | %s | %s | %s | %s | %s |' % (
            g, arm, ref, f(dm, 3), f(pct, 1), f(pmed, 3), f(min(pairs) if pairs else None, 3),
            f(max(pairs) if pairs else None, 3), faster, len(pairs), f(dp99, 1), f(d33, 1), f(dcpu),
            f(dfps, 1), ('%s (%d)' % (f(med(tpairs), 1), len(tpairs))) if tpairs else '-', verdict))
        lines.append('%s vs %s: median %s vs %s ms (delta %s, %s%%; paired %s, %d/%d rounds faster), fps %s vs %s (%s%%), p99 %s vs %s, '
                     '>33/min %s vs %s, >100/min %s vs %s, cpu %s vs %s cores, top1 thread busy %s vs %s %% (paired %s); ref range %s..%s; n %d/%d; %s' % (
                         arm, ref, f(s['med'], 2), f(t['med'], 2), f(dm, 2), f(pct, 1), f(pmed, 2), faster, len(pairs),
                         f(s['fps'], 1), f(t['fps'], 1), f(dfps, 1),
                         f(s['p99'], 1), f(t['p99'], 1), f(s['o33'], 1), f(t['o33'], 1), f(s['o100'], 2), f(t['o100'], 2),
                         f(s['cpu']), f(t['cpu']), f(s['top1'], 1), f(t['top1'], 1), f(med(tpairs), 1),
                         f(t['lo'], 2), f(t['hi'], 2), s['n'], t['n'], verdict))
    w('')
    w('## One-line results')
    w('')
    for ln in lines:
        w('- ' + ln)
    text = '\n'.join(out) + '\n'
    sys.stdout.write(text)
    if a.write:
        with open(os.path.join(d, 'recheck.md'), 'w', encoding='utf-8') as fh:
            fh.write(text)


if __name__ == '__main__':
    main()
