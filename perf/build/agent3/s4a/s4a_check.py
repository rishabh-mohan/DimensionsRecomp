"""Agent 3 S4a (task #5): read-only post-run checks of one candidate run dir against base run dirs.
FUNCTIONAL runs only (hidden desktop); nothing here is a timing number.
usage:
  python build/agent3/s4a/s4a_check.py --cand <run> [--base <run> ...] [--allow-new REGEX ...] [--tq-ref <run>]
         [--no-route-report] [--out-dir build/agent3/s4a/checks]
Reports (text to stdout and <out-dir>/<run>.txt, data to <out-dir>/<run>.json):
  run.json   exit code, dumps, crash events, close method/seconds, elapsed, cvars, extra env, script steps, seed lines
  log        levels, unknown cvars (summary.json), greps over game.log + rotated game.N.log (S4 families, fail lines,
             shader-storage lines, the gap after 'Initializing shader storage')
  logdiff    build/agent10/bgate/logdiff.py vs the bases (min level warning: NEW/MORE/GONE/FLAG; --allow-new families
             are counted apart), plus the NEW keys at info level (S4 info lines show up there)
  scenes     stable scenes (runs of >= 10 identical frames: OFF perf.csv draws/vertices, native frames.csv draws) with
             >= 2 s, base vs cand; and the scene at each route mark (route-report.txt, made by harness/route-report.ps1
             if missing)
  threads    threads-s4a.csv (attach.ps1): CPU % of one core per thread name, first frame + 20 s .. last sample - 10 s
  sys        sys.csv (Agent 8's sys-csv.ps1): slow state = e_eff_mhz < 800 for >= 3 rows in a row after the first frame
"""
import argparse
import csv
import glob
import json
import os
import re
import statistics
import subprocess
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
LOGDIFF = os.path.join(REPO, 'build', 'agent10', 'bgate', 'logdiff.py')
ROUTE_REPORT = os.path.join(REPO, 'harness', 'route-report.ps1')
GREPS = [
    ('s4_upload_hash', r'S4 upload hash: frame'),
    ('slow_frame', r'slow frame #'),
    ('precise_wait', r'TimerQueue: precise wait'),
    ('miss_cache', r'shader_miss_cache'),
    ('protect_failed', r'PhysicalHeap::Protect failed'),
    ('stuck_lock', r'STUCK-LOCK'),
    ('minidump', r'Minidump written'),
    ('fatal', r'\[FATAL\]'),
    ('storage', r'from the storage'),
    ('storage_init', r'Initializing shader storage'),
    ('clean_exit', r'Title terminated; hard-exiting process'),
]
S4_OFF_FAMILIES = ['s4_upload_hash', 'slow_frame', 'precise_wait', 'miss_cache']
LINE = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\] \[([a-z]+)\] \[([^\]]*)\] (?:\[t\d+\] )?(.*)$')
MARK = re.compile(r'^\s*([\d.]+) L(\d+)\s+mark\s+(\S+)\s+->.*\|\s*perf\s+(\S+)\s+scene\s+(\S+)')


def jload(p):
    try:
        with open(p, encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception:
        return None


def game_logs(run):
    fs = [p for p in glob.glob(os.path.join(run, 'game*.log')) if os.path.isfile(p)]
    return sorted(fs, key=os.path.getmtime)


def ts_s(ts):
    h, m, s = ts[11:].split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def scan_logs(run):
    counts = {k: 0 for k, _ in GREPS}
    first = {k: [] for k, _ in GREPS}
    levels = {}
    rx = [(k, re.compile(p)) for k, p in GREPS]
    storage_gap = None
    pending_init = None
    for p in game_logs(run):
        with open(p, encoding='utf-8', errors='replace') as f:
            for ln in f:
                m = LINE.match(ln.rstrip('\r\n'))
                if not m:
                    continue
                ts, lvl, cat, msg = m.groups()
                levels[lvl] = levels.get(lvl, 0) + 1
                if pending_init is not None:
                    storage_gap = round(ts_s(ts) - pending_init, 3)
                    pending_init = None
                for k, r in rx:
                    if r.search(msg):
                        counts[k] += 1
                        if len(first[k]) < (8 if k in ('storage', 'miss_cache', 'stuck_lock') else 2):
                            first[k].append(ln.rstrip('\r\n')[:300])
                        if k == 'storage_init' and storage_gap is None:
                            pending_init = ts_s(ts)
    return counts, first, levels, storage_gap


def run_logdiff(bases, cand, level):
    cmd = [sys.executable, LOGDIFF]
    for b in bases:
        cmd += ['--base', b]
    cmd += ['--cand', cand, '--min-level', level]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=REPO)
    out = r.stdout.splitlines()
    return out, r.returncode


def scenes(run, kind):
    """stable scenes: key -> seconds (runs of >= 10 identical frames)."""
    acc = {}
    if kind == 'native':
        p = os.path.join(run, 'frames.csv')
        kcol, tcol, tdiv = ('draw_calls',), 'interval_ms', 1000.0
    else:
        p = os.path.join(run, 'perf.csv')
        kcol, tcol, tdiv = ('draw_calls', 'vertices_processed'), 'frame_time_us', 1e6
    if not os.path.isfile(p):
        return None
    cur, n, secs = None, 0, 0.0
    with open(p, newline='', encoding='utf-8', errors='replace') as f:
        for row in csv.DictReader(f):
            try:
                key = '/'.join(str(int(float(row[c]))) for c in kcol)
                dt = float(row[tcol]) / tdiv
            except (KeyError, ValueError, TypeError):
                continue
            if key != cur:
                if cur is not None and n >= 10:
                    acc[cur] = acc.get(cur, 0.0) + secs
                cur, n, secs = key, 0, 0.0
            n += 1
            secs += dt
    if cur is not None and n >= 10:
        acc[cur] = acc.get(cur, 0.0) + secs
    return acc


def marks(run, make, kind='off'):
    """scene at each route mark: median of the 30 perf.csv rows on disk at the mark (input.csv perf_bytes), like
    harness/route-report.ps1 (which takes minutes; --route-report runs it as well). native: frames.csv draws (n<draws>)."""
    if make and not os.path.isfile(os.path.join(run, 'route-report.txt')) and os.path.isfile(os.path.join(run, 'input.csv')):
        subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ROUTE_REPORT, '-RunDir', run],
                       capture_output=True, text=True, cwd=REPO)
    ip, pp = os.path.join(run, 'input.csv'), os.path.join(run, 'perf.csv')
    if not os.path.isfile(ip) or not os.path.isfile(pp):
        return None
    with open(pp, 'rb') as f:
        perf = f.read()
    fr = None
    if kind == 'native' and os.path.isfile(os.path.join(run, 'frames.csv')):
        fr = {}
        with open(os.path.join(run, 'frames.csv'), newline='', encoding='utf-8', errors='replace') as f:
            for r in csv.DictReader(f):
                try:
                    fr[int(r['frame'])] = int(float(r['draw_calls']))
                except (KeyError, ValueError, TypeError):
                    pass
    out = {}
    with open(ip, newline='', encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            if r.get('cmd') != 'mark':
                continue
            try:
                pb = int(float(r['perf_bytes']))
            except (KeyError, ValueError, TypeError):
                continue
            lines = perf[:pb].decode('utf-8', 'replace').splitlines()
            if pb < len(perf) and lines:
                lines = lines[:-1] if not perf[:pb].endswith(b'\n') else lines
            data = lines[1:]
            sc = '-'
            if fr is not None:
                nrow = len(data)
                ds = [fr[k] for k in range(max(2, nrow - 29), nrow + 1) if k in fr]
                if ds:
                    sc = 'n%d' % statistics.median(ds)
            elif data:
                ds, vs = [], []
                for ln in data[-30:]:
                    c = ln.split(',')
                    try:
                        ds.append(int(c[2]))
                        vs.append(int(c[4]))
                    except (IndexError, ValueError):
                        pass
                if ds:
                    sc = '%d/%d' % (statistics.median(ds), statistics.median(vs))
            out[r.get('args')] = (float(r.get('t_s') or 0), str(len(data)), sc)
    return out


def threads(run, rj, sj):
    p = os.path.join(run, 'threads-s4a.csv')
    if not os.path.isfile(p) or not rj or not sj or sj.get('first_frame_s') is None:
        return None
    ff = float(rj['started_epoch_s']) + float(sj['first_frame_s'])
    rows = {}
    last = 0.0
    with open(p, newline='', encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            e = float(r['epoch_s'])
            last = max(last, e)
            try:
                cyc = int(r.get('cycles') or 0)
            except ValueError:
                cyc = 0
            rows.setdefault(r['tid'], []).append((e, r['name'], float(r['cpu_ms']), cyc))
    # ticks advance: per TimerQueue thread, every sample-to-sample step of the cycle counter must rise
    ticks = {}
    for tid, xs in rows.items():
        xs.sort(key=lambda x: x[0])
        nm = xs[-1][1] or xs[0][1] or ''
        if 'TimerQueue' not in nm:
            continue
        steps = [(xs[i][0] - xs[i - 1][0], xs[i][3] - xs[i - 1][3]) for i in range(1, len(xs))]
        flat = [round(xs[i][0] - ff, 1) for i in range(1, len(xs)) if xs[i][3] <= xs[i - 1][3]]
        ticks[tid] = {'name': nm, 'samples': len(xs), 'steps': len(steps), 'non_rising': len(flat), 'non_rising_at_s': flat[:10],
                      'step_s_median': round(statistics.median([s[0] for s in steps]), 2) if steps else None,
                      'span_s': [round(xs[0][0] - ff, 1), round(xs[-1][0] - ff, 1)]}
    t0, t1 = ff + 20.0, last - 10.0
    if t1 - t0 < 20:
        return {'window_s': round(t1 - t0, 1), 'by_name': {}, 'note': 'window too short', 'ticks': ticks}
    by_name = {}
    for tid, xs in rows.items():
        inw = [x for x in xs if t0 <= x[0] <= t1]
        if len(inw) < 2:
            continue
        a, b = inw[0], inw[-1]
        name = b[1] or a[1] or '(unnamed)'
        pct = (b[2] - a[2]) / ((t1 - t0) * 1000.0) * 100.0
        d = by_name.setdefault(name, {'pct': 0.0, 'threads': 0})
        d['pct'] += pct
        d['threads'] += 1
    for d in by_name.values():
        d['pct'] = round(d['pct'], 2)
    return {'window_s': round(t1 - t0, 1), 'window': [round(t0 - ff, 1), round(t1 - ff, 1)], 'by_name': by_name, 'ticks': ticks}


def frame_rows(run, kind):
    p = os.path.join(run, 'frames.csv' if kind == 'native' else 'perf.csv')
    if not os.path.isfile(p):
        return None
    with open(p, 'rb') as f:
        return max(0, f.read().count(b'\n') - 1)


def log_epoch(ts):
    """game.log timestamps are local wall clock: '2026-11-22 13:17:57.935' -> epoch seconds."""
    return time.mktime(time.strptime(ts[:19], '%Y-%m-%d %H:%M:%S')) + float('0' + ts[19:])


def slow_state(run, rj, sj, emhz=800.0, minrows=3):
    p = os.path.join(run, 'sys.csv')
    if not os.path.isfile(p) or not rj or not sj or sj.get('first_frame_s') is None:
        return None
    ff = float(rj['started_epoch_s']) + float(sj['first_frame_s'])
    low = run_ = 0
    onset = first = None
    xs = []
    util = []
    with open(p, newline='', encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            if not r.get('e_eff_mhz') or not r.get('epoch_s'):
                continue
            t = float(r['epoch_s']) - ff
            if t < 0:
                continue
            e = float(r['e_eff_mhz'])
            xs.append(e)
            if r.get('cpu_util_pct'):
                util.append(float(r['cpu_util_pct']))
            if e < emhz:
                low += 1
                run_ += 1
                if run_ == 1:
                    first = t
                if run_ >= minrows and onset is None:
                    onset = first
            else:
                run_ = 0
    if not xs:
        return {'rows': 0}
    return {'rows': len(xs), 'onset_s': None if onset is None else round(onset, 1), 'slow_pct': round(100.0 * low / len(xs), 1),
            'e_eff_mhz_median': round(statistics.median(xs)), 'cpu_util_pct_median': round(statistics.median(util), 1) if util else None,
            'slow': onset is not None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cand', required=True)
    ap.add_argument('--base', action='append', default=[])
    ap.add_argument('--allow-new', action='append', default=[])
    ap.add_argument('--tq-ref', default='')
    ap.add_argument('--route-report', action='store_true')
    ap.add_argument('--out-dir', default=os.path.join(REPO, 'build', 'agent3', 's4a', 'checks'))
    a = ap.parse_args()
    cand = os.path.abspath(a.cand)
    bases = [os.path.abspath(b) for b in a.base]
    rj = jload(os.path.join(cand, 'run.json')) or {}
    sj = jload(os.path.join(cand, 'summary.json')) or {}
    kind = 'native' if os.path.isfile(os.path.join(cand, 'frames.csv')) else 'off'
    res = {'run': os.path.basename(cand), 'kind': kind}
    L = []
    say = L.append
    say('# s4a_check %s (%s)' % (os.path.basename(cand), kind))
    env = {k: v for k, v in (rj.get('env') or {}).items() if k not in ('LEGO_NATIVE_FRAME_METRICS', 'AGENT3_VPAD')}
    isc = rj.get('input_script') or {}
    res['runjson'] = {k: rj.get(k) for k in ('exit_code', 'exit_code_hex', 'dumps', 'crash_events', 'wer_seen', 'close_method',
                                             'close_seconds', 'elapsed_s', 'seconds_requested', 'cvars', 'exited_early')}
    res['runjson']['env_extra'] = env
    res['runjson']['script'] = os.path.basename(isc.get('script') or '') or None
    res['runjson']['steps'] = '%s/%s' % (isc.get('steps_done'), isc.get('steps_total')) if isc else None
    res['runjson']['peak_threads'] = (rj.get('process') or {}).get('peak_threads')
    extra_args = [x for x in (rj.get('command_line') or '').split() if x.startswith('--') and not re.match(
        r'--(log_file|log_flush_interval|perf_log_csv|native_settings_load|discord_rpc|audio_mute|pause_when_unfocused|input_backend)=', x)]
    res['runjson']['extra_args'] = extra_args
    say('run.json: exit %s (%s) dumps %d crash_events %d wer %s; close %s %.2f s; elapsed %s of %s s; cvars %s; args %s; env %s; script %s steps %s' % (
        rj.get('exit_code'), rj.get('exit_code_hex'), len(rj.get('dumps') or []), len(rj.get('crash_events') or []), rj.get('wer_seen'),
        rj.get('close_method'), float(rj.get('close_seconds') or 0), rj.get('elapsed_s'), rj.get('seconds_requested'),
        json.dumps(rj.get('cvars') or {}), ' '.join(extra_args) or '-', json.dumps(env) if env else '-', res['runjson']['script'],
        res['runjson']['steps']))
    if rj.get('dumps'):
        say('  dumps: %s' % ', '.join(os.path.basename(str(d if isinstance(d, str) else d.get('path', d))) for d in rj['dumps']))
    sx = rj.get('seed_xenos')
    if sx:
        res['seed_storage_log'] = sx.get('storage_log')
        for ln in (sx.get('storage_log') or [])[:6]:
            say('  seed storage: %s' % str(ln)[:260])
    lg = sj.get('log') or {}
    res['summary'] = {'verdict': sj.get('verdict'), 'first_frame_s': sj.get('first_frame_s'), 'levels': lg.get('levels'),
                      'errors': (lg.get('errors') or [])[:5], 'unknown_cvars': lg.get('unknown_cvars')}
    say('summary: verdict %s; first frame %s s; levels %s; unknown cvars %s; errors %s' % (
        sj.get('verdict'), sj.get('first_frame_s'), json.dumps(lg.get('levels')), lg.get('unknown_cvars'), len(lg.get('errors') or [])))
    counts, first, levels, gap = scan_logs(cand)
    res['greps'] = counts
    res['grep_first'] = first
    res['storage_init_gap_s'] = gap
    res['log_files'] = [os.path.basename(p) for p in game_logs(cand)]
    say('log files %s; greps %s; gap after "Initializing shader storage" %s s' % (
        ','.join(res['log_files']), ' '.join('%s=%d' % (k, v) for k, v in counts.items()), gap))
    for k in ('storage', 'precise_wait', 'miss_cache', 'stuck_lock', 'protect_failed', 's4_upload_hash', 'slow_frame'):
        for ln in first[k]:
            say('  %s: %s' % (k, ln))
    res['s4_lines_off'] = sum(counts[k] for k in S4_OFF_FAMILIES)
    nfr = frame_rows(cand, kind)
    res['frame_rows'] = nfr
    if nfr:
        say('frames (%s rows) %d; per frame: s4_upload_hash %.3f slow_frame %.3f' % (
            'frames.csv' if kind == 'native' else 'perf.csv', nfr, counts['s4_upload_hash'] / nfr, counts['slow_frame'] / nfr))
    if first['precise_wait'] and rj.get('started_epoch_s') and sj.get('first_frame_s') is not None:
        m = LINE.match(first['precise_wait'][0])
        if m:
            dt = log_epoch(m.group(1)) - (float(rj['started_epoch_s']) + float(sj['first_frame_s']))
            res['precise_wait_vs_first_frame_s'] = round(dt, 2)
            say('  precise_wait line level [%s], %.2f s %s the first frame' % (m.group(2), abs(dt), 'before' if dt < 0 else 'AFTER'))
    if bases:
        allow = [re.compile(x) for x in a.allow_new]
        out, rc = run_logdiff(bases, cand, 'warning')
        new = [l for l in out if l.startswith('NEW ')]
        more = [l for l in out if l.startswith('MORE ')]
        gone = [l for l in out if l.startswith('GONE ')]
        flag = [l for l in out if l.startswith('FLAG ')]
        new_allowed = [l for l in new if any(r.search(l) for r in allow)]
        more_allowed = [l for l in more if any(r.search(l) for r in allow)]
        out_i, _ = run_logdiff(bases, cand, 'info')
        new_i = [l for l in out_i if l.startswith('NEW ')]
        toy = re.compile(r'\] Toypad\[(Read |Write)\] ')
        gone_other = [l for l in gone if not toy.search(l)]
        new_i_other = [l for l in new_i if not toy.search(l)]
        res['logdiff'] = {'bases': [os.path.basename(b) for b in bases], 'NEW': len(new) - len(new_allowed), 'NEW_allowed': len(new_allowed),
                          'MORE': len(more) - len(more_allowed), 'MORE_allowed': len(more_allowed), 'GONE': len(gone),
                          'GONE_non_toypad': len(gone_other), 'FLAG': len(flag),
                          'NEW_info': len(new_i), 'NEW_info_non_toypad': len(new_i_other), 'rc': rc, 'new': new[:20], 'more': more[:20],
                          'gone': gone[:30], 'flag': flag, 'new_info': new_i_other[:25]}
        say('logdiff vs %s: NEW %d (+%d allowed) MORE %d (+%d allowed) GONE %d (%d non-Toypad) FLAG %d; NEW at info %d (%d non-Toypad)' % (
            ','.join(res['logdiff']['bases']), len(new) - len(new_allowed), len(new_allowed), len(more) - len(more_allowed),
            len(more_allowed), len(gone), len(gone_other), len(flag), len(new_i), len(new_i_other)))
        for l in [x for x in new if x not in new_allowed] + [x for x in more if x not in more_allowed] + flag:
            say('  ' + l[:300])
        for l in gone_other[:12]:
            say('  ' + l[:220])
        for l in new_i_other[:12]:
            say('  info ' + l[:260])
        base0 = bases[0]
        _, _, lv_b, _ = scan_logs(base0)
        res['levels_cand_vs_base0'] = {'cand': levels, 'base': lv_b}
        say('levels (game*.log) cand %s vs %s %s; [error] %d vs %d' % (json.dumps(levels), os.path.basename(base0), json.dumps(lv_b),
                                                                       levels.get('error', 0), lv_b.get('error', 0)))
        sc_c, sc_b = scenes(cand, kind), scenes(base0, kind)
        if sc_c is not None and sc_b is not None:
            major_b = {k: v for k, v in sc_b.items() if v >= 2.0}
            major_c = {k: v for k, v in sc_c.items() if v >= 2.0}
            missing = sorted(k for k in major_b if sc_c.get(k, 0.0) < 0.5)
            extra = sorted(k for k in major_c if sc_b.get(k, 0.0) < 0.5)
            res['scenes'] = {'base': os.path.basename(base0), 'base_major': {k: round(v, 1) for k, v in sorted(major_b.items(), key=lambda x: -x[1])},
                             'cand_major': {k: round(v, 1) for k, v in sorted(major_c.items(), key=lambda x: -x[1])},
                             'missing_in_cand': missing, 'extra_in_cand': extra}
            say('scenes (>= 2 s) base %s: %s' % (os.path.basename(base0), ' '.join('%s:%.0fs' % kv for kv in sorted(major_b.items(), key=lambda x: -x[1])[:10])))
            say('scenes (>= 2 s) cand: %s' % ' '.join('%s:%.0fs' % kv for kv in sorted(major_c.items(), key=lambda x: -x[1])[:10]))
            say('  missing in cand: %s; extra in cand: %s' % (missing or '-', extra or '-'))
        mc, mb = marks(cand, a.route_report, kind), marks(base0, a.route_report, kind)
        if mc and mb:
            same, diff = [], []
            for name, (t, perf, sc) in mb.items():
                if name in mc:
                    (same if mc[name][2] == sc else diff).append((name, sc, mc[name][2]))
            res['marks'] = {'same': len(same), 'diff': [list(x) for x in diff], 'cand': {k: v[2] for k, v in mc.items()}}
            say('route marks: %d same scene, %d differ%s' % (len(same), len(diff), (': ' + ' '.join('%s %s->%s' % d for d in diff)) if diff else ''))
            say('  cand marks: %s' % ' '.join('%s=%s' % (k, v[2]) for k, v in mc.items()))
    th = threads(cand, rj, sj)
    if th is not None:
        res['threads'] = th
        top = sorted(th['by_name'].items(), key=lambda x: -x[1]['pct'])[:12]
        say('threads (%% of one core, window %s s from the first frame, %s s): %s' % (th.get('window'), th['window_s'],
            ' | '.join('%s x%d %.1f' % (k, v['threads'], v['pct']) for k, v in top)))
        tq = {k: v for k, v in th['by_name'].items() if 'TimerQueue' in k}
        say('  TimerQueue: %s' % (json.dumps(tq) if tq else 'no thread named *TimerQueue*'))
        for tid, tk in (th.get('ticks') or {}).items():
            say('  TimerQueue ticks (tid %s): %d samples over %s s (step median %s s), cycles non-rising in %d of %d steps %s' % (
                tid, tk['samples'], tk['span_s'], tk['step_s_median'], tk['non_rising'], tk['steps'], tk['non_rising_at_s'] or ''))
        if a.tq_ref:
            ref = os.path.abspath(a.tq_ref)
            th_r = threads(ref, jload(os.path.join(ref, 'run.json')), jload(os.path.join(ref, 'summary.json')))
            if th_r:
                tq_r = {k: v for k, v in th_r['by_name'].items() if 'TimerQueue' in k}
                res['threads_ref'] = {'run': os.path.basename(ref), 'timerqueue': tq_r, 'window_s': th_r['window_s']}
                say('  TimerQueue in %s: %s' % (os.path.basename(ref), json.dumps(tq_r) if tq_r else 'none'))
    ss = slow_state(cand, rj, sj)
    res['slow_state'] = ss
    say('sys.csv slow state: %s' % (json.dumps(ss) if ss is not None else 'no sys.csv'))
    os.makedirs(a.out_dir, exist_ok=True)
    stem = os.path.join(a.out_dir, os.path.basename(cand))
    with open(stem + '.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1)
    with open(stem + '.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
