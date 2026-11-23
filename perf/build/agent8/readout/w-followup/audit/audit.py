#!/usr/bin/env python3
"""audit.py - Agent 8 task #20: read-only follow-up audit of W6 (0009, 0313), W9 (0108, 0401),
W5b (0155, 0451) and W4c (0239) under build/agent8/matrix (helper of Agent 8).

usage:  python -B build/agent8/readout/w-followup/audit/audit.py

Reads only build/agent8/matrix/<stamp>/{results.csv, logs/*.txt, runs/*/{run.json, sys.csv,
sys.json, proc.csv, frames.json, perf.csv, game.log, gpu.csv, driver.out.txt, driver.err.txt,
sys.err.txt}} and this dir's timerq3-<stamp>.csv (bench/agent11/timerq_slowstate_3mode.ps1 output).
Writes only into this dir: audit.md, audit.json, runs.csv, spikes.csv, gamelog.csv.
stdlib only, single thread. Imports build/agent8/readout/w4b/sysaudit/sysaudit.py read-only
(run with python -B so no __pycache__ is written there). If findings.md exists in this dir it is
put at the top of audit.md.

CPU model (per 1 s sys.csv sample; same as the W4b/W5 sysaudit):
  busy_t  = 4*min(1, p_util/100*1700/p_eff) + 8*min(1, e_util/100*f_E/e_eff), f_E = 1.5*base-850
  util_LP = 4*p_util/100 + 8*e_util/100          (utility units, frequency-scaled)
  game    = slope of proc.csv cpu_s over the same 1 s interval
  ng_t = busy_t - game (time based, logical CPUs) ; ng_u = util_LP - game (utility based)
"""
import bisect, csv, json, math, os, re, statistics, sys, time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
MROOT = os.path.join(ROOT, 'build', 'agent8', 'matrix')
sys.path.insert(0, os.path.join(ROOT, 'build', 'agent8', 'readout', 'w4b', 'sysaudit'))
import sysaudit as SA  # noqa: E402
from sysaudit import ff, truthy, read_csv, sod, med, mean, pct, mx, mn, share, f, pc, md, clean  # noqa: E402
import audit5 as X5  # noqa: E402  (section 5; uses this module as __main__ at call time)

MATS = [('W6-1', '20261123-0009'), ('W9-1', '20261123-0108'), ('W5b-1', '20261123-0155'),
        ('W4c', '20261123-0239'), ('W6-2', '20261123-0313'), ('W9-2', '20261123-0401'),
        ('W5b-2', '20261123-0451')]
W6 = ('20261123-0009', '20261123-0313')
SPIKE_RUN = ('20261123-0313', '0352-p2f-r5')
SPIKE_MS = 16.7
TOY_WIN = 0.4
FLUSH_ROWS = 59
FLAG_KEYS = [('ngB_mean', 0.2), ('ngU_mean', 0.2), ('ngB_max', 0.5), ('ngU_max', 0.5)]
BURST_N = 12
SETK = ('ac', 'batt_saver', 'scheme', 'overlay', 'input_desktop', 'screensaver')

ENTRY_RX = re.compile(r'^\[(\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d(?:\.\d+)?)\] \[([A-Za-z]+)\] \[([^\]]*)\] (.*)$')
TID_RX = re.compile(r'^\[t(\d+)\] ?(.*)$')
STUCKLOCK_RX = re.compile(r'STUCK[-_ ]?LOCK', re.I)
SITE_RX = re.compile(r'(?:owner[_ ]?site|site|owner)\s*[=:]\s*([^\s,;)]+)', re.I)
HANG_RX = re.compile(r'\bhang(?:s|ing|ed)?\b|\bhung\b', re.I)
ALARM_RX = re.compile(r'\bexception\b|access violation|\bfatal\b|\bassert(?:ion)?\b|\babort(?:ed|ing)?\b|'
                      r'\bdeadlock\b|\bwatchdog\b|\bcrash(?:ed|es)?\b', re.I)
RL_PATS = [('stuck', re.compile(r'stuck', re.I)), ('dmp/dump', re.compile(r'\.dmp\b|\bdump', re.I)),
           ('crash', re.compile(r'crash', re.I)), ('hang/hung', HANG_RX), ('error', re.compile(r'\berror', re.I)),
           ('critical', re.compile(r'critical', re.I)), ('werfault', re.compile(r'werfault', re.I)),
           ('exception', re.compile(r'exception', re.I)), ('CrossDevice/gate', re.compile(r'crossdevice|quiet|holdback', re.I))]


# ----------------------------------------------------------------------------- helpers
def load_json(p):
    try:
        with open(p, encoding='utf-8-sig') as fh:
            return json.load(fh)
    except Exception:
        return None


def rnd(x, nd=4):
    if isinstance(x, bool) or x is None:
        return x
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return None
        return round(x, nd)
    return x


def mad(v):
    v = clean(v)
    if len(v) < 2:
        return None
    m = statistics.median(v)
    return statistics.median([abs(x - m) for x in v])


def arm_of(tag):
    return re.sub(r'-r\d+$', '', tag or '')


def hms(x):
    if x is None:
        return '-'
    x = x % 86400.0
    h = int(x // 3600)
    m = int((x - h * 3600) // 60)
    s = x - h * 3600 - m * 60
    return f'{h:02d}:{m:02d}:{s:06.3f}'


def at(ends, dts, t):
    """index of the sample whose interval (end-dt, end] contains t, else None"""
    if t is None or not ends:
        return None
    i = bisect.bisect_left(ends, t - 1e-9)
    if i >= len(ends):
        return None
    if ends[i] - dts[i] < t <= ends[i] + 1e-6:
        return i
    return None


def err_lines(p):
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding='utf-8', errors='replace') as fh:
            L = [x.strip() for x in fh if x.strip()]
    except OSError:
        return None
    return {'n': len(L), 'distinct': sorted(set(x[:140] for x in L))[:5]}


def scan_gamelog(path):
    o = {'exists': os.path.exists(path), 'bytes': None, 'lines': 0, 'entries': 0, 'levels': Counter(),
         'stuck': 0, 'stuck_lock': 0, 'stuck_lock_sites': Counter(), 'error': 0, 'critical': 0, 'hang': 0,
         'alarm': 0, 'examples': {}, '_entries': []}
    if not o['exists']:
        return o
    o['bytes'] = os.path.getsize(path)

    def ex(k, ln):
        L = o['examples'].setdefault(k, [])
        if len(L) < 3:
            L.append(ln[:220])
    with open(path, encoding='utf-8', errors='replace') as fh:
        for raw in fh:
            ln = raw.rstrip('\r\n')
            o['lines'] += 1
            m = ENTRY_RX.match(ln)
            lvl = None
            if m:
                o['entries'] += 1
                lvl = m.group(3).lower()
                o['levels'][lvl] += 1
                rest = m.group(5)
                tm = TID_RX.match(rest)
                tid, msg = (tm.group(1), tm.group(2)) if tm else ('', rest)
                o['_entries'].append((sod(m.group(2)), lvl, m.group(4), tid, msg))
            low = ln.lower()
            if 'stuck' in low:
                o['stuck'] += 1
                ex('stuck', ln)
                if STUCKLOCK_RX.search(ln):
                    o['stuck_lock'] += 1
                    sm = SITE_RX.search(ln)
                    site = sm.group(1) if sm else re.sub(r'0x[0-9a-fA-F]+|\d+', '#', ln.split('STUCK', 1)[-1])[:80]
                    o['stuck_lock_sites'][site] += 1
            if lvl in ('error', 'err') or '[error]' in low:
                o['error'] += 1
                ex('error', ln)
            if lvl in ('critical', 'crit', 'fatal') or '[critical]' in low:
                o['critical'] += 1
                ex('critical', ln)
            if HANG_RX.search(ln):
                o['hang'] += 1
                ex('hang', ln)
            if ALARM_RX.search(ln):
                o['alarm'] += 1
                ex('alarm', ln)
    return o


def find_dmps(rdir):
    hits, looked = [], []

    def chk(d):
        looked.append(os.path.relpath(d, rdir))
        try:
            for e in os.listdir(d):
                if e.lower().endswith(('.dmp', '.mdmp', '.hdmp')):
                    hits.append(os.path.relpath(os.path.join(d, e), rdir))
        except OSError:
            pass
    chk(rdir)
    u = os.path.join(rdir, 'user')
    if os.path.isdir(u):
        chk(u)
        try:
            for e in os.listdir(u):
                p = os.path.join(u, e)
                if os.path.isdir(p):
                    chk(p)
        except OSError:
            pass
    return hits, looked


def load_gpu(rdir, local_off):
    p, d = os.path.join(rdir, 'gpu.csv'), os.path.join(rdir, 'driver.out.txt')
    if not (os.path.exists(p) and os.path.exists(d)) or local_off is None:
        return []
    with open(d, encoding='utf-8', errors='replace') as fh:
        first = fh.readline()
    m = re.match(r'^(\d\d:\d\d:\d\d(?:\.\d+)?)\s+\+([\d.]+)s', first)
    if not m:
        return []
    start = sod(m.group(1)) - float(m.group(2))
    out = []
    for x in read_csv(p):
        t = ff(x.get('t_s'))
        if t is None:
            continue
        y = dict(x)
        y['epoch'] = start + t + local_off
        y['wall'] = hms(start + t)
        out.append(y)
    return out


def load_proc_rows(rdir, off):
    out = []
    if off is None:
        return out
    for x in read_csv(os.path.join(rdir, 'proc.csv')):
        t = ff(x.get('t_s'))
        if t is None:
            continue
        y = dict(x)
        y['epoch'] = t + off
        out.append(y)
    return out


# ----------------------------------------------------------------------------- per run
def audit_run(lab, stamp, idx, name, rdir, res):
    r = {'window': lab, 'stamp': stamp, 'idx': idx, 'run': name, 'rdir': rdir, 'err': None}
    rr = SA.match_results(res, name) or {}
    r['in_results'] = bool(rr)
    r['scored'] = truthy(rr.get('scored')) if 'scored' in rr else ('cold' not in name)
    r['valid'] = truthy(rr.get('valid_timing')) if 'valid_timing' in rr else None
    r['arm'] = rr.get('arm') or arm_of(name.split('-', 1)[1] if '-' in name else name)
    r['arm_label'] = r['arm'] if r['scored'] else ('cold-' + r['arm'] if not r['arm'].startswith('cold') else r['arm'])
    for k in ('excluded', 'flags_excluding', 'flags_info', 'status', 'round'):
        r[k] = rr.get(k, '')
    for k in ('fps_mean', 'median_ms', 'p99_ms', 'p999_ms', 'max_ms', 'over33', 'fg_share', 'idle_min_s',
              'cpu_cores_mean', 'eff_mhz', 'window_s', 'frames'):
        r['res_' + k] = ff(rr.get(k))
    rj, S, pts, xs, ms, me, ffe, off = SA.process_run(rdir, name)
    r['tag'] = rj.get('tag', '')
    sysrows = read_csv(os.path.join(rdir, 'sys.csv'))
    bym = {}
    for x in sysrows:
        e = ff(x.get('epoch_s'))
        if e is not None:
            bym[e] = x
    for s in S:
        x = bym.get(s['epoch']) or {}
        s['batt_saver'] = x.get('batt_saver', '')
        s['batt_pct'] = x.get('batt_pct', '')
    W = [s for s in S if s['phase'] == 'window']
    U = [s for s in S if s['phase'] == 'warmup']
    A = [s for s in S if s['phase'] != 'nogame']
    r['win'] = SA.phase_stats(W, pts, xs, ms, me)
    r['wu'] = SA.phase_stats(U, pts, xs, ffe, ms)
    for st, X in ((r['win'], W), (r['wu'], U)):
        st['e_eff_min'] = mn([s['e_eff'] for s in X])
        st['p_eff_min'] = mn([s['p_eff'] for s in X])
        st['p_util_max'] = mx([s['p_util'] for s in X])

    def vset(X, k):
        return sorted(set(str(s.get(k, '')) for s in X))
    r['sets_win'] = {k: vset(W, k) for k in SETK}
    r['sets_run'] = {k: vset(A, k) for k in SETK}

    def idle_resets(phases):
        n, prev = 0, None
        for s in S:
            v = s.get('idle_s')
            if v is not None and prev is not None and v < prev - 0.5 and s['phase'] in phases:
                n += 1
            if v is not None:
                prev = v
        return n
    r['idle_resets_win'] = idle_resets(('window',))
    r['idle_resets_run'] = idle_resets(('boot', 'warmup', 'window', 'after'))
    sj = load_json(os.path.join(rdir, 'sys.json')) or {}
    r['sj_flags'] = sj.get('flags')
    for part in ('window', 'run'):
        p = sj.get(part) or {}
        r['sj_' + part] = {k: p.get(k) for k in ('rows', 'span_s', 'max_gap_s', 'idle_min_s', 'input_events',
                                                 'fg_game_share', 'game_alive_all', 'desktop_not_default_rows',
                                                 'screensaver_rows')}
        ch, first = {}, {}
        for k in ('ac', 'batt_saver', 'batt_pct', 'scheme', 'overlay'):
            v = p.get(k)
            if isinstance(v, dict):
                first[k] = v.get('first')
                if v.get('changes'):
                    ch[k] = v.get('changes')
        r['sj_%s_changes' % part] = ch
        r['sj_%s_first' % part] = first

    def chg_list(part, sets, fg_check):
        L = []
        sjp = r['sj_' + part]
        for k, v in r['sj_%s_changes' % part].items():
            L.append('%s changes %s' % (k, json.dumps(v)[:90]))
        if (sjp.get('input_events') or 0) > 0:
            L.append('input_events %s' % sjp['input_events'])
        if fg_check and sjp.get('fg_game_share') is not None and sjp['fg_game_share'] < 1:
            L.append('fg %s' % sjp['fg_game_share'])
        if (sjp.get('desktop_not_default_rows') or 0) > 0:
            L.append('desktop_not_default_rows %s' % sjp['desktop_not_default_rows'])
        if (sjp.get('screensaver_rows') or 0) > 0:
            L.append('screensaver_rows %s' % sjp['screensaver_rows'])
        for k in SETK:
            if len(sets[k]) > 1:
                L.append('%s %s' % (k, '/'.join(sets[k])))
        return L
    r['chg_win'] = chg_list('window', r['sets_win'], True)
    if r['idle_resets_win']:
        r['chg_win'].append('idle_s resets %d' % r['idle_resets_win'])
    r['chg_run'] = chg_list('run', r['sets_run'], False)
    if r['idle_resets_run']:
        r['chg_run'].append('idle_s resets %d' % r['idle_resets_run'])
    r['log'] = scan_gamelog(os.path.join(rdir, 'game.log'))
    r['dmps'], r['dmp_dirs'] = find_dmps(rdir)
    r['werfault_seen'] = rj.get('werfault_seen')
    r['foreign_crash_dumps'] = rj.get('foreign_crash_dumps')
    r['rj_crashkeys'] = {k: v for k, v in rj.items() if re.search(r'crash|dump|werfault|stuck|(^|_)hang', k, re.I)}
    r['driver_err'] = err_lines(os.path.join(rdir, 'driver.err.txt'))
    r['sys_err'] = err_lines(os.path.join(rdir, 'sys.err.txt'))
    r['build_procs_window'] = rj.get('build_procs_window')
    r['build_procs_warmup'] = rj.get('build_procs_warmup')
    r['ticks_skipped'] = rj.get('ticks_skipped')
    r['ticks_skipped_window'] = rj.get('ticks_skipped_window')
    r['ms'], r['me'], r['ffe'], r['proc_off'] = ms, me, ffe, off
    r['local_off'] = med([s['epoch'] - s['sod'] for s in S if s.get('sod') is not None])
    r['start_wall'] = S[0]['wall'][:8] if S else ''
    lo = r['local_off']
    r['win_wall'] = (hms(ms - lo)[:8] + '-' + hms(me - lo)[:8]) if (ms and me and lo is not None) else ''
    toy = []
    if lo is not None:
        for (t, lvl, cat, tid, msg) in r['log']['_entries']:
            if t is not None and msg.startswith('Toypad['):
                e = t + lo
                if toy and e - toy[-1][-1] <= 0.25:
                    toy[-1].append(e)
                else:
                    toy.append([e])
    r['toypad'] = [g[0] for g in toy]
    r['_S'], r['_pts'], r['_xs'] = S, pts, xs
    return r


# ----------------------------------------------------------------------------- folder analysis
def robust_flags(sc, key, min_delta):
    out = {}
    for r in sc:
        v = r['win'].get(key)
        rest = clean([x['win'].get(key) for x in sc if x is not r])
        if v is None or len(rest) < 3:
            out[r['run']] = None
            continue
        m = statistics.median(rest)
        d = mad(rest)
        z = (v - m) / (1.4826 * d) if d else None
        above = v > max(rest)
        flag = above and (z is None or z >= 3) and (v - m) >= min_delta
        out[r['run']] = {'v': v, 'rest_med': m, 'rest_max': max(rest), 'z': z, 'above_rest_max': above,
                         'delta': v - m, 'flag': flag}
    return out


def analyse_folder(lab, stamp, runs):
    sc = [r for r in runs if r['scored'] and not r.get('err')]
    F = {'window': lab, 'stamp': stamp, 'n_runs': len(runs), 'n_scored': len(sc)}
    armmed = {}
    for a in sorted(set(r['arm'] for r in sc)):
        armmed[a] = med([r['res_fps_mean'] for r in sc if r['arm'] == a])
    for r in runs:
        r['fps_rel'] = (r['res_fps_mean'] / armmed[r['arm']]) if (r in sc and r['res_fps_mean'] and armmed.get(r['arm'])) else None
    flags = {key: robust_flags(sc, key, mind) for key, mind in FLAG_KEYS}
    for r in sc:
        r['rflags'] = {key: flags[key].get(r['run']) for key, _ in FLAG_KEYS}
        same = clean([x['win']['ngB_mean'] for x in sc if x['arm'] == r['arm'] and x is not r])
        d = mad(same)
        r['z_arm_ngB'] = ((r['win']['ngB_mean'] - statistics.median(same)) / (1.4826 * d)) if (same and d and r['win']['ngB_mean'] is not None) else None
    pool = {k: pct([s[k] for r in sc for s in r['_S'] if s['phase'] == 'window'], 90) for k in ('ngB', 'ngU')}
    for r in sc:
        W = [s for s in r['_S'] if s['phase'] == 'window']
        r['burst'] = {k: sum(1 for s in W if s.get(k) is not None and pool[k] is not None and s[k] > pool[k]) for k in ('ngB', 'ngU')}
        r['burst_n'] = len(W)
        r['burst_walls'] = [s['wall'][:8] for s in W if s.get('ngB') is not None and pool['ngB'] is not None and s['ngB'] > pool['ngB']]
    for r in sc:
        why = []
        for key, mind in FLAG_KEYS:
            fl = r['rflags'].get(key)
            if fl and fl['flag']:
                why.append('%s %.2f > rest max %.2f (rest med %.2f, z %s)' % (key, fl['v'], fl['rest_max'], fl['rest_med'], f(fl['z'], 1)))
        if r['burst']['ngB'] >= BURST_N:
            why.append('ng_t bursts %d/%d > folder p90 %.2f' % (r['burst']['ngB'], r['burst_n'], pool['ngB']))
        if r['chg_win']:
            why.append('window change: ' + '; '.join(r['chg_win']))
        r['flag_why'] = why
    arms = []
    for a in sorted(set(r['arm'] for r in sc)):
        X = [r for r in sc if r['arm'] == a]
        arms.append({'arm': a, 'n': len(X), 'fps_med': med([r['res_fps_mean'] for r in X]),
                     'game_med': med([r['win']['game_slope'] for r in X]),
                     'ngB_mean_med': med([r['win']['ngB_mean'] for r in X]), 'ngB_mean_min': mn([r['win']['ngB_mean'] for r in X]),
                     'ngB_mean_max': mx([r['win']['ngB_mean'] for r in X]),
                     'ngB_max_max': mx([r['win']['ngB_max'] for r in X]),
                     'ngU_mean_med': med([r['win']['ngU_mean'] for r in X]), 'ngU_mean_min': mn([r['win']['ngU_mean'] for r in X]),
                     'ngU_mean_max': mx([r['win']['ngU_mean'] for r in X]),
                     'P_util_med': med([r['win']['P_util_mean'] for r in X]), 'E_mhz_med': med([r['win']['e_eff_mean'] for r in X]),
                     'E_mhz_min': mn([r['win']['e_eff_min'] for r in X]), 'e_lt800_max': mx([r['win']['e_lt800_share'] for r in X]),
                     'fg_min': mn([r['win']['fg_game_share'] for r in X]),
                     'flagged': [r['run'] for r in X if r['flag_why']]})
    sp = {}
    for key in ('ngB_mean', 'ngU_mean', 'P_util_mean', 'e_eff_mean'):
        x = [r['win'][key] for r in sc]
        sp[key + '|fps_rel'] = SA.spearman(x, [r['fps_rel'] for r in sc], nperm=2000)
    sp['seq|ngB_mean'] = SA.spearman([float(r['idx']) for r in sc], [r['win']['ngB_mean'] for r in sc], nperm=2000)
    sp['seq|ngU_mean'] = SA.spearman([float(r['idx']) for r in sc], [r['win']['ngU_mean'] for r in sc], nperm=2000)
    F.update({'pool_p90': pool, 'arms': arms, 'spearman': sp, 'arm_fps_med': armmed,
              'ngB_mean_med': med([r['win']['ngB_mean'] for r in sc]), 'ngB_mean_min': mn([r['win']['ngB_mean'] for r in sc]),
              'ngB_mean_max': mx([r['win']['ngB_mean'] for r in sc]), 'ngU_mean_med': med([r['win']['ngU_mean'] for r in sc]),
              'ngU_mean_min': mn([r['win']['ngU_mean'] for r in sc]), 'ngU_mean_max': mx([r['win']['ngU_mean'] for r in sc]),
              'game_med': med([r['win']['game_slope'] for r in sc]), 'P_util_med': med([r['win']['P_util_mean'] for r in sc]),
              'E_mhz_med': med([r['win']['e_eff_mean'] for r in sc]), 'E_mhz_min': mn([r['win']['e_eff_min'] for r in sc]),
              'flagged': {r['run']: r['flag_why'] for r in sc if r['flag_why']}})
    return F


# ----------------------------------------------------------------------------- frames (W6)
def read_perf(rdir):
    with open(os.path.join(rdir, 'perf.csv'), 'rb') as fh:
        data = fh.read()
    lines = data.split(b'\n')
    starts, pos = [], 0
    for ln in lines:
        starts.append(pos)
        pos += len(ln) + 1
    hdr = lines[0].decode('utf-8', 'replace').strip().lstrip('\ufeff').split(',')
    rows, rstarts = lines[1:], starts[1:]
    while rows and not rows[-1].strip():
        rows.pop()
        rstarts.pop()
    return hdr, rows, rstarts, len(data)


def perf_window(rdir, keep_rows=False):
    fj = load_json(os.path.join(rdir, 'frames.json')) or {}
    w = fj.get('window') or {}
    first, n = int(w.get('first_row')), int(w.get('rows'))
    sb = w.get('start_bytes')
    hdr, rows, rstarts, size = read_perf(rdir)
    conv = None
    if sb is not None:
        j = bisect.bisect_left(rstarts, int(sb))
        conv = (j - first) if (j < len(rstarts) and rstarts[j] == int(sb)) else 'no row starts at start_bytes'
    col = {h: i for i, h in enumerate(hdr)}
    fi = col.get('frame_time_us', 0)
    frames, T, zeros = [], 0.0, 0
    for k in range(n):
        i = first + k
        if i >= len(rows):
            break
        vals = rows[i].decode('utf-8', 'replace').strip().split(',')
        ft = ff(vals[fi]) if fi < len(vals) else None
        if ft is None:
            continue
        if ft <= 0:
            zeros += 1
            continue
        t0 = T
        T += ft / 1e6
        frames.append((k, i, t0, T, ft / 1000.0, vals))
    o = {'fj': fj, 'win': w, 'first': first, 'rows': n, 'conv': conv, 'hdr': hdr, 'col': col, 'frames': frames,
         'zeros': zeros, 'sum_s': T, 'n_rows_file': len(rows), 'bytes': size}
    if keep_rows:
        o['all_rows'] = rows
    return o


def pcol(vals, col, name):
    i = col.get(name)
    return ff(vals[i]) if (i is not None and i < len(vals)) else None


def w6_frames(r, keep_rows=False, pw=None):
    pw = pw if pw is not None else perf_window(r['rdir'], keep_rows)
    fr = pw['frames']
    msv = [x[4] for x in fr]
    medft = statistics.median(msv) if msv else None
    lag = FLUSH_ROWS * medft / 1000.0 if medft else 0.0
    ms_e, lo = r['ms'], r['local_off']
    S = r['_S']
    ends, dts = [s['epoch'] for s in S], [s['dt'] for s in S]
    proc = load_proc_rows(r['rdir'], r['proc_off'])
    pends = [p['epoch'] for p in proc]
    pdts = [pends[0] - (ms_e - 1e9)] + [pends[i] - pends[i - 1] for i in range(1, len(pends))] if pends else []
    if pdts:
        pdts[0] = 1.0
    toy = r['toypad']
    ents = [(t + lo, lvl, cat, tid, msg) for (t, lvl, cat, tid, msg) in r['log']['_entries'] if t is not None and lo is not None]
    col = pw['col']
    spikes = []
    for (k, i, t0, t1, msx, vals) in fr:
        if msx <= SPIKE_MS:
            continue
        hi = ms_e + t1
        lo_e = hi - lag
        mid = 0.5 * (lo_e + hi)
        si = at(ends, dts, mid)
        s = S[si] if si is not None else {}
        si_lo, si_hi = at(ends, dts, lo_e), at(ends, dts, hi)
        pi = at(pends, pdts, mid)
        p = proc[pi] if pi is not None else {}
        near_toy = min(toy, key=lambda e: abs(e - mid)) if toy else None
        near_log = min(ents, key=lambda e: abs(e[0] - mid)) if ents else None
        spikes.append({'run': r['run'], 'stamp': r['stamp'], 'window': r['window'], 'arm': r['arm_label'],
                       'scored': r['scored'], 'k': k, 'row': i, 'file_line': i + 2, 't_start_s': t0, 't_end_s': t1,
                       'ms': msx, 'est_epoch_lo': lo_e, 'est_epoch_hi': hi,
                       'est_wall': hms(mid - lo) if lo is not None else '-',
                       'sys_wall': s.get('wall', ''), 'sys_samples_differ_over_lag': (si_lo != si_hi),
                       'p_util': s.get('p_util'), 'e_util': s.get('e_util'), 'p_eff': s.get('p_eff'), 'e_eff': s.get('e_eff'),
                       'busy_t': s.get('busyB'), 'util_LP': s.get('utilLP'), 'game': s.get('game'),
                       'ng_t': s.get('ngB'), 'ng_u': s.get('ngU'), 'idle_s': s.get('idle_s'), 'fg_game': s.get('fg_game'),
                       'proc_cpu_cores': ff(p.get('cpu_cores')), 'proc_threads': ff(p.get('threads')),
                       'proc_responding': p.get('responding', ''),
                       'pipeline_cache_misses': pcol(vals, col, 'pipeline_cache_misses'),
                       'texture_cache_misses': pcol(vals, col, 'texture_cache_misses'),
                       'command_buffer_stalls': pcol(vals, col, 'command_buffer_stalls'),
                       'critical_region_contentions': pcol(vals, col, 'critical_region_contentions'),
                       'draw_calls': pcol(vals, col, 'draw_calls'), 'active_threads': pcol(vals, col, 'active_threads'),
                       'functions_dispatched': pcol(vals, col, 'functions_dispatched'),
                       'toypad_dt_s': (near_toy - mid) if near_toy is not None else None,
                       'log_dt_s': (near_log[0] - mid) if near_log else None,
                       'log_msg': (near_log[4][:70] if near_log else '')})
    mids = [ms_e + x[3] - lag / 2 for x in fr]
    toyrows = []
    me = r['me'] if r['me'] else ms_e + pw['sum_s']
    for e in toy:
        if not (ms_e - TOY_WIN <= e <= me + TOY_WIN):
            continue
        j0, j1 = bisect.bisect_left(mids, e - TOY_WIN), bisect.bisect_right(mids, e + TOY_WIN)
        loc = [fr[j][4] for j in range(j0, j1)]
        jm = max(range(j0, j1), key=lambda j: fr[j][4]) if j1 > j0 else None
        toyrows.append({'epoch': e, 'T_s': e - ms_e, 'wall': hms(e - lo) if lo is not None else '-',
                        'max_ms': max(loc) if loc else None, 'n_frames': len(loc),
                        'max_frame_dt_s': (mids[jm] - e) if jm is not None else None,
                        'spike': bool(loc) and max(loc) > SPIKE_MS})
    bins = {}
    for x in fr:
        b = int(x[3] // (2 * TOY_WIN))
        bins[b] = max(bins.get(b, 0.0), x[4])
    bvals = sorted(bins.values())
    fj = pw['fj']
    chk = {'frames_json_frames': fj.get('frames'), 'my_frames': len(fr), 'frames_json_max_ms': fj.get('max_ms'),
           'my_max_ms': max(msv) if msv else None, 'frames_json_over33': fj.get('over_33ms'),
           'my_over33': sum(1 for v in msv if v > 33.0), 'frames_json_window_s': fj.get('window_s'), 'my_sum_s': pw['sum_s'],
           'zero_rows': pw['zeros'], 'row_convention_offset': pw['conv']}
    o = {'run': r['run'], 'stamp': r['stamp'], 'window': r['window'], 'arm': r['arm_label'], 'scored': r['scored'],
         'n_frames': len(fr), 'n_gt16': sum(1 for v in msv if v > SPIKE_MS), 'n_gt33': chk['my_over33'],
         'max_ms': chk['my_max_ms'], 'p999_ms': pct(msv, 99.9), 'median_ms': medft, 'lag_s': lag, 'check': chk,
         'spikes': spikes, 'toypad': toyrows, 'bin_max_median': med(bvals), 'bin_max_p90': pct(bvals, 90),
         'n_bins': len(bvals)}
    o['_pw'] = pw if keep_rows else None
    o['_proc'] = proc if keep_rows else None
    return o


def spike_detail(r, fo):
    pw = fo['_pw']
    fr = pw['frames']
    j = max(range(len(fr)), key=lambda q: fr[q][4])
    k, i, t0, t1, msx, vals = fr[j]
    lag, ms_e, lo = fo['lag_s'], r['ms'], r['local_off']
    hi = ms_e + t1
    lo_e = hi - lag
    mid = 0.5 * (lo_e + hi)
    D = {'run': r['run'], 'k': k, 'row': i, 'file_line': i + 2, 't_start_s': t0, 't_end_s': t1, 'ms': msx,
         'window_first_row': pw['first'], 'window_rows': pw['rows'], 'row_convention_offset': pw['conv'],
         'start_bytes': pw['win'].get('start_bytes'), 'measure_start_epoch': ms_e, 'measure_start_wall': hms(ms_e - lo),
         'lag_s': lag, 'est_epoch_lo': lo_e, 'est_epoch_hi': hi, 'est_wall_lo': hms(lo_e - lo), 'est_wall_hi': hms(hi - lo),
         'frac_of_window': t1 / pw['sum_s'] if pw['sum_s'] else None}
    rows = pw['all_rows']
    D['perf_hdr'] = pw['hdr']
    D['perf_rows'] = []
    for q in range(max(0, i - 3), min(len(rows), i + 4)):
        D['perf_rows'].append([q, q + 2] + rows[q].decode('utf-8', 'replace').strip().split(','))
    S = r['_S']
    ends, dts = [s['epoch'] for s in S], [s['dt'] for s in S]
    cand = sorted(set(x for x in (at(ends, dts, lo_e), at(ends, dts, mid), at(ends, dts, hi)) if x is not None))
    D['sys_idx'] = cand
    D['sys'] = []
    if cand:
        for q in range(max(0, cand[0] - 1), min(len(S), cand[-1] + 2)):
            s = S[q]
            D['sys'].append({'in_frame_second': q in cand, 'wall': s['wall'], 'epoch': s['epoch'], 'dt': s['dt'],
                             'cpu_util': s.get('util'), 'cpu_perf': s.get('perf'), 'p_util': s.get('p_util'),
                             'e_util': s.get('e_util'), 'p_eff': s.get('p_eff'), 'e_eff': s.get('e_eff'),
                             'busy_t': s.get('busyB'), 'util_LP': s.get('utilLP'), 'game': s.get('game'),
                             'ng_t': s.get('ngB'), 'ng_u': s.get('ngU'), 'idle_s': s.get('idle_s'),
                             'fg_game': s.get('fg_game'), 'input_desktop': s.get('input_desktop'),
                             'overlay': s.get('overlay'), 'phase': s.get('phase')})
    proc = fo['_proc']
    pends = [p['epoch'] for p in proc]
    D['proc'] = []
    if pends:
        pi = bisect.bisect_left(pends, mid)
        for q in range(max(0, pi - 2), min(len(proc), pi + 2)):
            p = proc[q]
            D['proc'].append({'covers_frame': (q == pi), 'epoch': p['epoch'], 'wall': hms(p['epoch'] - lo),
                              **{k2: p.get(k2, '') for k2 in ('t_s', 'phase', 'cpu_cores', 'cpu_s', 'ws_mb', 'commit_mb',
                                                               'threads', 'handles', 'responding', 'log_lines',
                                                               'perf_csv_bytes', 'free_ram_gb', 'note')}})
    gpu = load_gpu(r['rdir'], lo)
    D['gpu'] = []
    if gpu:
        ge = [g['epoch'] for g in gpu]
        gi = bisect.bisect_left(ge, mid)
        for q in range(max(0, gi - 2), min(len(gpu), gi + 2)):
            g = gpu[q]
            D['gpu'].append({'after_frame': g['epoch'] >= mid, 'wall': g['wall'], 'dt_s': g['epoch'] - mid,
                             **{k2: g.get(k2, '') for k2 in ('t_s', 'pstate', 'gr_mhz', 'mem_mhz', 'temp_c', 'power_w',
                                                              'util_gpu', 'util_mem', 'throttle')}})
    D['log'] = []
    for (t, lvl, cat, tid, msg) in r['log']['_entries']:
        if t is None or lo is None:
            continue
        e = t + lo
        if abs(e - mid) <= 2.0:
            D['log'].append({'wall': hms(t), 'dt_s': e - mid, 'level': lvl, 'cat': cat, 'tid': tid, 'msg': msg[:90]})
    th = os.path.join(r['rdir'], 'threads.csv')
    D['threads_top'] = []
    if os.path.exists(th):
        T = read_csv(th)
        T.sort(key=lambda x: -(ff(x.get('busy_pct')) or 0))
        D['threads_top'] = [{k2: x.get(k2) for k2 in ('tid', 'name', 'busy_pct', 'max_busy_pct')} for x in T[:6]]
    return D


# ----------------------------------------------------------------------------- runner logs
def scan_runner_logs(mdir):
    d = os.path.join(mdir, 'logs')
    out = {'files': 0, 'lines': 0, 'counts': Counter(), 'examples': {}, 'dmp_top': []}
    for dd in (mdir, d):
        try:
            out['dmp_top'] += [os.path.join(os.path.basename(dd), e) for e in os.listdir(dd) if e.lower().endswith(('.dmp', '.mdmp'))]
        except OSError:
            pass
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith('.txt'):
            continue
        out['files'] += 1
        with open(os.path.join(d, fn), encoding='utf-8', errors='replace') as fh:
            for ln in fh:
                out['lines'] += 1
                for labx, rx in RL_PATS:
                    if rx.search(ln):
                        out['counts'][labx] += 1
                        ex = out['examples'].setdefault(labx, [])
                        if len(ex) < 2:
                            ex.append('%s: %s' % (fn, ln.strip()[:170]))
    return out


# ----------------------------------------------------------------------------- report
def load_timerq(stamp):
    p = os.path.join(HERE, 'timerq3-%s.csv' % stamp)
    return read_csv(p) if os.path.exists(p) else []


def chg_s(L):
    return '; '.join(L) if L else 'none'


def main():
    t_start = time.time()
    L = []
    P = L.append
    J = {'generated': time.strftime('%Y-%m-%d %H:%M:%S'), 'script': os.path.relpath(__file__, ROOT),
         'matrices': {}, 'timerq3': {}, 'w6_frames': {}, 'spike_detail': None, 'gamelog': {}, 'runner_logs': {},
         'interpretation': {}, 'w5b_compare': {}}
    allruns, folders = [], {}
    for lab, stamp in MATS:
        mdir = os.path.join(MROOT, stamp)
        res = read_csv(os.path.join(mdir, 'results.csv'))
        rd = os.path.join(mdir, 'runs')
        names = sorted(d for d in os.listdir(rd) if os.path.isdir(os.path.join(rd, d)))
        runs = []
        for i, name in enumerate(names, 1):
            try:
                runs.append(audit_run(lab, stamp, i, name, os.path.join(rd, name), res))
            except Exception as ex:
                runs.append({'window': lab, 'stamp': stamp, 'idx': i, 'run': name, 'err': repr(ex), 'scored': False})
        folders[stamp] = {'lab': lab, 'runs': runs, 'F': analyse_folder(lab, stamp, [r for r in runs if not r.get('err')]),
                          'rl': scan_runner_logs(mdir), 'tq': load_timerq(stamp)}
        allruns += runs
    errs = [(r['stamp'], r['run'], r['err']) for r in allruns if r.get('err')]

    # interpretation check
    WS = [s for r in allruns if not r.get('err') for s in r['_S'] if s['phase'] in ('window', 'warmup')]
    bP = [s['bP_raw'] for s in WS if s.get('modelB') == 'B']
    bE = [s['bE_raw'] for s in WS if s.get('modelB') == 'B']
    J['interpretation'] = {'samples': len(WS), 'fallback_Bbase': sum(1 for s in WS if s.get('modelB') == 'Bbase'),
                           'base_min': mn([s['base'] for s in WS]), 'base_max': mx([s['base'] for s in WS]),
                           'bP_raw_gt1.02': share(bP, lambda x: x > 1.02), 'bP_raw_max': mx(bP), 'bP_raw_med': med(bP),
                           'bE_raw_gt1.02': share(bE, lambda x: x > 1.02), 'bE_raw_max': mx(bE), 'bE_raw_med': med(bE),
                           'e_eff_min': mn([s['e_eff'] for s in WS]), 'p_eff_min': mn([s['p_eff'] for s in WS]),
                           'e_lt800_n': sum(1 for s in WS if s['e_eff'] is not None and s['e_eff'] < 800),
                           'overlay_values': sorted(set(str(s.get('overlay')) for s in WS)),
                           'scheme_values': sorted(set(str(s.get('scheme')) for s in WS))}

    # W6 frames
    w6 = {}
    detail = None
    fbs = {}
    for stamp in X5.FB_STAMPS:
        for r in folders[stamp]['runs']:
            if r.get('err'):
                continue
            keep = (stamp, r['run']) == SPIKE_RUN
            try:
                pw = perf_window(r['rdir'], keep)
                fbs[(stamp, r['run'])] = X5.frame_bins(r, pw)
                if stamp not in W6:
                    continue
                fo = w6_frames(r, keep_rows=keep, pw=pw)
            except Exception as ex:
                w6[(stamp, r['run'])] = {'run': r['run'], 'err': repr(ex)}
                continue
            finally:
                pw = None
            if keep:
                detail = spike_detail(r, fo)
                fo['_pw'] = None
                fo['_proc'] = None
            w6[(stamp, r['run'])] = fo

    # ------------------------------------------------------------------ markdown
    P('# Task #20 follow-up audit: W6, W9, W5b, W4c (read-only)')
    P('')
    P('Generated %s by `%s` (helper of Agent 8). Inputs: `build/agent8/matrix/<stamp>/` for %s. '
      'Writes only into `build/agent8/readout/w-followup/audit/`.' % (J['generated'], J['script'].replace('\\', '/'),
                                                                     ', '.join('%s=%s' % (a, b) for a, b in MATS)))
    if errs:
        P('')
        P('**Run errors:** ' + '; '.join('%s/%s %s' % e for e in errs))
    fpath = os.path.join(HERE, 'findings.md')
    if os.path.exists(fpath):
        P('')
        with open(fpath, encoding='utf-8') as fh:
            P(fh.read().rstrip())
    P('')
    P('## Method')
    P('')
    P('- 1 s sys.csv samples, interval (previous epoch, epoch]; phase by the sample midpoint: window = run.json measure_start..measure_end, warm-up = first frame..measure_start.')
    P('- busy_t (time based, logical CPUs of 12) = 4*min(1, p_util/100*1700/p_eff) + 8*min(1, e_util/100*f_E/e_eff), f_E = 1.5*base_mhz - 850 (from 12*base = 4*1700 + 8*f_E). '
      'util_LP (utility units) = 4*p_util/100 + 8*e_util/100. game = slope of proc.csv cpu_s over the same interval. '
      '**ng_t = busy_t - game** (non-game CPU occupancy, cores), **ng_u = util_LP - game** (utility based, Agent 1 style).')
    P('- With P and E clocks at ~1.96-1.98 GHz (above the 1.7 GHz nominal), utility over-counts busy time by eff/nominal, so ng_u reads ~1 core above ng_t here; '
      'ng_t is the occupancy number. No run of these folders had the slow state (E < 800 MHz), so neither measure is clock-distorted the way W4b/W5 were.')
    P('- "non-game" includes everything outside legodimensions.exe: the run harness samplers (sys-csv, thread-cpu driver with NVML, proc sampler), dwm, the GPU driver/kernel (DPC/ISR), Defender and other services. '
      'There is no per-process data for non-game processes in the matrix folders.')
    P('- Flag rule per folder (scored runs): value above the max of the other scored runs AND robust z = (v - median_rest)/(1.4826*MAD_rest) >= 3 AND v - median_rest >= 0.2 cores (means) / 0.5 cores (1 s max); '
      'bursts: 1 s window samples above the folder-pooled p90 of ng_t (expected ~5 of 50), flagged at >= %d; any power/overlay/AC/input/fg/desktop change in the window.' % BURST_N)

    # ---- 1. slow state
    P('')
    P('## 1. Slow state (bench/agent11/timerq_slowstate_3mode.ps1, E < 800 MHz for 3+ samples after the first frame)')
    P('')
    rows = []
    for lab, stamp in MATS:
        tq = folders[stamp]['tq']
        J['timerq3'][stamp] = tq
        arms = []
        for x in tq:
            if x['arm'] not in arms:
                arms.append(x['arm'])
        for a in arms:
            X = [x for x in tq if x['arm'] == a]
            sl = [x for x in X if x.get('onset_s', '-') != '-']
            rows.append([lab, stamp[-4:], a, '/'.join(sorted(set(x['mode'] for x in X))), len(X), len(sl),
                         ' '.join('%s:%s' % (x['run'][:4], x['onset_s']) for x in sl) or '-',
                         f(mean([ff(x['slow_raw']) for x in X]), 1), f(mx([ff(x['slow_raw']) for x in X]), 1),
                         '/'.join(sorted(set(x['ms1'] for x in X))), ','.join(sorted(set(x['flags'] for x in X if x['flags']))) or '-'])
    L.extend(md(['window', 'folder', 'arm', 'mode', 'runs', 'slow runs', 'onset_s (run:onset)', 'mean slow_pct', 'max slow_pct', 'ms1 lines', 'flags'], rows))
    I = J['interpretation']
    P('')
    P('Cross-check from sys.csv (all runs, window + warm-up samples, n=%d): e_eff min %s MHz, samples with E < 800 MHz: %d; p_eff min %s MHz; overlay values %s; scheme values %s.'
      % (I['samples'], f(I['e_eff_min'], 0), I['e_lt800_n'], f(I['p_eff_min'], 0), '/'.join(I['overlay_values']), '/'.join(I['scheme_values'])))
    P('timerq3 .txt files are the script\'s console tables (PowerShell `>` = UTF-16); the .csv files hold the same rows.')

    # ---- 2. sys.csv audit
    P('')
    P('## 2. sys.csv disturbance audit (scored window, 50 s; cold runs shown unscored, 30 s)')
    P('')
    P('Busy-share check (model B, window + warm-up samples): busy_P raw > 1.02 in %s %% (max %s), busy_E raw > 1.02 in %s %% (max %s); base_mhz %s-%s; Bbase fallback samples %d. '
      'A busy share above 1 would mean the formula over-counts; values stay <= ~1, so the time-based reading holds.'
      % (pc(I['bP_raw_gt1.02'], 1), f(I['bP_raw_max'], 3), pc(I['bE_raw_gt1.02'], 1), f(I['bE_raw_max'], 3),
         f(I['base_min'], 0), f(I['base_max'], 0), I['fallback_Bbase']))
    hdr = ['#', 'run', 'win wall', 'fps', 'game', 'ng_t mean', 'ng_t max', 'ng_u mean', 'ng_u max', 'z_t', 'z_u', 'z_t arm',
           'bursts t/u', 'P util %', 'E MHz (min)', 'fg %', 'idle min s', 'change in window', 'change in run', 'flag']
    for lab, stamp in MATS:
        Fd = folders[stamp]
        F = Fd['F']
        P('')
        P('### %s (%s): %d runs, %d scored; folder-pooled ng_t p90 %s, ng_u p90 %s' % (lab, stamp, F['n_runs'], F['n_scored'], f(F['pool_p90']['ngB']), f(F['pool_p90']['ngU'])))
        P('')
        rows = []
        for r in Fd['runs']:
            if r.get('err'):
                rows.append([r['idx'], r['run'], 'ERROR ' + r['err'][:60]] + [''] * (len(hdr) - 3))
                continue
            w = r['win']
            rf = r.get('rflags') or {}
            zt = (rf.get('ngB_mean') or {}).get('z') if rf else None
            zu = (rf.get('ngU_mean') or {}).get('z') if rf else None
            rows.append([r['idx'], r['run'] + ('' if r['scored'] else ' (unscored)'), r['win_wall'], f(r['res_fps_mean'], 1),
                         f(w['game_slope']), f(w['ngB_mean']), f(w['ngB_max']), f(w['ngU_mean']), f(w['ngU_max']),
                         f(zt, 1), f(zu, 1), f(r.get('z_arm_ngB'), 1),
                         ('%d/%d' % (r['burst']['ngB'], r['burst']['ngU'])) if r.get('burst') else '-',
                         f(w['P_util_mean'], 1), '%s (%s)' % (f(w['e_eff_mean'], 0), f(w['e_eff_min'], 0)),
                         pc(w['fg_game_share']), f(w['idle_min'], 0), chg_s(r['chg_win']), chg_s(r['chg_run']),
                         ('FLAG: ' + ' | '.join(r['flag_why'])) if r.get('flag_why') else '-'])
        L.extend(md(hdr, rows))
        sp = F['spearman']
        P('')
        P('Folder: ng_t mean median %s [%s..%s], ng_u mean median %s [%s..%s], game median %s cores, P util median %s %%, E MHz median %s (min %s). '
          'Spearman (scored runs): ng_t mean vs fps_rel rho %s (n=%s, p=%s); ng_u mean vs fps_rel rho %s (p=%s); run order vs ng_t mean rho %s (p=%s).'
          % (f(F['ngB_mean_med']), f(F['ngB_mean_min']), f(F['ngB_mean_max']), f(F['ngU_mean_med']), f(F['ngU_mean_min']), f(F['ngU_mean_max']),
             f(F['game_med']), f(F['P_util_med'], 1), f(F['E_mhz_med'], 0), f(F['E_mhz_min'], 0),
             f(sp['ngB_mean|fps_rel'][0], 2), sp['ngB_mean|fps_rel'][1], f(sp['ngB_mean|fps_rel'][2], 3),
             f(sp['ngU_mean|fps_rel'][0], 2), f(sp['ngU_mean|fps_rel'][2], 3),
             f(sp['seq|ngB_mean'][0], 2), f(sp['seq|ngB_mean'][2], 3)))
        P('Flagged: ' + ('; '.join('%s: %s' % (k, ' | '.join(v)) for k, v in F['flagged'].items()) if F['flagged'] else 'none'))

    # ---- per-arm summary
    P('')
    P('### Per-arm summary (scored runs; medians over runs of per-run window values)')
    P('')
    rows = []
    for lab, stamp in MATS:
        for a in folders[stamp]['F']['arms']:
            rows.append([lab, a['arm'], a['n'], f(a['fps_med'], 1), f(a['game_med']),
                         '%s [%s..%s]' % (f(a['ngB_mean_med']), f(a['ngB_mean_min']), f(a['ngB_mean_max'])), f(a['ngB_max_max']),
                         '%s [%s..%s]' % (f(a['ngU_mean_med']), f(a['ngU_mean_min']), f(a['ngU_mean_max'])),
                         f(a['P_util_med'], 1), '%s (%s)' % (f(a['E_mhz_med'], 0), f(a['E_mhz_min'], 0)),
                         pc(a['e_lt800_max']), pc(a['fg_min']), ','.join(a['flagged']) or '-'])
    L.extend(md(['window', 'arm', 'n', 'fps med', 'game med', 'ng_t mean med [min..max]', 'ng_t 1 s max', 'ng_u mean med [min..max]',
                 'P util med %', 'E MHz med (min)', 'E<800 max %', 'fg min %', 'flagged'], rows))

    # ---- cross-folder
    P('')
    P('### Folder level, in time order (scored runs)')
    P('')
    rows = []
    for lab, stamp in MATS:
        F = folders[stamp]['F']
        sc = [r for r in folders[stamp]['runs'] if r.get('scored') and not r.get('err')]
        rows.append([lab, stamp, sc[0]['win_wall'][:5] + '-' + sc[-1]['win_wall'][-8:-3] if sc else '-', F['n_scored'],
                     '%s [%s..%s]' % (f(F['ngB_mean_med']), f(F['ngB_mean_min']), f(F['ngB_mean_max'])),
                     '%s [%s..%s]' % (f(F['ngU_mean_med']), f(F['ngU_mean_min']), f(F['ngU_mean_max'])),
                     f(F['game_med']), f(F['P_util_med'], 1), f(F['E_mhz_med'], 0), len(F['flagged'])])
    L.extend(md(['window', 'folder', 'windows', 'n', 'ng_t mean med [min..max]', 'ng_u mean med [min..max]', 'game med', 'P util med', 'E MHz med', 'flagged runs'], rows))

    # ---- W5b-2 vs W5b-1
    P('')
    P('### W5b-2 (0451) vs W5b-1 (0155): CrossDeviceService holdback check')
    P('')
    P('Agent 8\'s note: the quiet gate held W5b-2 back while CrossDeviceService ran at 0.7-0.9 core, 04:46-04:49; W5b-2\'s cold run started 04:51:59. '
      'No sys.csv covers 04:46-04:49 (W9-2\'s last run ended ~04:44). A carry-over would show as higher ng_t in W5b-2 than in W5b-1 for the same arm, largest in the first runs.')
    P('')
    f1 = [r for r in folders['20261123-0155']['runs'] if not r.get('err')]
    f2 = [r for r in folders['20261123-0451']['runs'] if not r.get('err')]
    rows = []
    cmp_ = {}
    for a in ('d11', 'd11t', 'd11p'):
        X1 = [r for r in f1 if r['scored'] and r['arm'] == a]
        X2 = [r for r in f2 if r['scored'] and r['arm'] == a]
        v = {}
        for key in ('ngB_mean', 'ngU_mean', 'game_slope', 'P_util_mean', 'e_eff_mean'):
            v[key] = (med([r['win'][key] for r in X1]), med([r['win'][key] for r in X2]))
        fps = (med([r['res_fps_mean'] for r in X1]), med([r['res_fps_mean'] for r in X2]))
        cmp_[a] = {'n': (len(X1), len(X2)), 'fps': fps, **v}
        rows.append([a, '%d/%d' % (len(X1), len(X2)), '%s / %s' % (f(v['ngB_mean'][0]), f(v['ngB_mean'][1])),
                     f(v['ngB_mean'][1] - v['ngB_mean'][0]) if None not in v['ngB_mean'] else '-',
                     '%s / %s' % (f(v['ngU_mean'][0]), f(v['ngU_mean'][1])),
                     f(v['ngU_mean'][1] - v['ngU_mean'][0]) if None not in v['ngU_mean'] else '-',
                     '%s / %s' % (f(v['game_slope'][0]), f(v['game_slope'][1])), '%s / %s' % (f(v['P_util_mean'][0], 1), f(v['P_util_mean'][1], 1)),
                     '%s / %s' % (f(v['e_eff_mean'][0], 0), f(v['e_eff_mean'][1], 0)), '%s / %s' % (f(fps[0], 1), f(fps[1], 1))])
    L.extend(md(['arm', 'n 1/2', 'ng_t mean med 1 / 2', 'diff', 'ng_u mean med 1 / 2', 'diff', 'game 1 / 2', 'P util 1 / 2', 'E MHz 1 / 2', 'fps 1 / 2'], rows))
    P('')
    P('W5b-2 runs in order (window ng_t mean / ng_u mean; warm-up ng_t mean):')
    P('')
    rows = []
    for r in f2:
        rows.append([r['idx'], r['run'] + ('' if r['scored'] else ' (unscored)'), r['win_wall'], f(r['win']['ngB_mean']), f(r['win']['ngU_mean']),
                     f(r['wu']['ngB_mean']), f(r['win']['game_slope'])])
    L.extend(md(['#', 'run', 'window', 'ng_t mean', 'ng_u mean', 'warm-up ng_t mean', 'game'], rows))
    sc2 = [r for r in f2 if r['scored']]
    sc1 = [r for r in f1 if r['scored']]
    early2, late2 = sc2[:3], sc2[3:]
    cmp_['early3_vs_rest_W5b2_ngB'] = (med([r['win']['ngB_mean'] for r in early2]), med([r['win']['ngB_mean'] for r in late2]))
    cmp_['early3_vs_rest_W5b1_ngB'] = (med([r['win']['ngB_mean'] for r in sc1[:3]]), med([r['win']['ngB_mean'] for r in sc1[3:]]))
    c1 = [r for r in f1 if not r['scored']]
    c2 = [r for r in f2 if not r['scored']]
    P('')
    P('First 3 scored runs vs the other 15, ng_t mean median: W5b-2 %s vs %s; W5b-1 %s vs %s. Cold runs (window/warm-up ng_t mean): W5b-1 %s %s/%s, W5b-2 %s %s/%s.'
      % (f(cmp_['early3_vs_rest_W5b2_ngB'][0]), f(cmp_['early3_vs_rest_W5b2_ngB'][1]), f(cmp_['early3_vs_rest_W5b1_ngB'][0]),
         f(cmp_['early3_vs_rest_W5b1_ngB'][1]), c1[0]['run'] if c1 else '-', f(c1[0]['win']['ngB_mean']) if c1 else '-',
         f(c1[0]['wu']['ngB_mean']) if c1 else '-', c2[0]['run'] if c2 else '-', f(c2[0]['win']['ngB_mean']) if c2 else '-',
         f(c2[0]['wu']['ngB_mean']) if c2 else '-'))
    J['w5b_compare'] = cmp_

    # ---- 3. frames
    P('')
    P('## 3. Frames over 16.7 ms in W6 (0009 = W6-1, 0313 = W6-2)')
    P('')
    P('Window rows = frames.json window.first_row .. first_row+rows-1 (0-based data rows of perf.csv, header excluded; checked against window.start_bytes per run: "row conv" 0 = match). '
      'T = summed frame_time_us from the window start (T start = frame began, T end = frame ended). '
      'Wall time: measure_start epoch + T end, minus 0..%d unflushed rows at the start mark (perf.csv flushes every 60 rows), i.e. up to "lag" s earlier; '
      'the est. wall is the middle of that range. sys/proc values are the 1 s sample containing it.' % FLUSH_ROWS)
    if detail:
        D = detail
        P('')
        P('### 3.1 The 45.67 ms frame: %s/%s' % SPIKE_RUN)
        P('')
        P('- frames.json window: first_row %s, rows %s, start_bytes %s; row convention offset %s (0 = first_row is the 0-based data row starting at start_bytes).'
          % (D['window_first_row'], D['window_rows'], D['start_bytes'], D['row_convention_offset']))
        P('- The frame: window frame #%d (0-based), perf.csv data row %d (file line %d incl. header), **%.2f ms**, T start %.3f s, **T end %.3f s** from the window start (%.1f %% into the 50 s window).'
          % (D['k'], D['row'], D['file_line'], D['ms'], D['t_start_s'], D['t_end_s'], 100 * (D['frac_of_window'] or 0)))
        P('- measure_start %s (epoch %.3f); estimated wall of the frame end %s .. %s (lag %.3f s).'
          % (D['measure_start_wall'], D['measure_start_epoch'], D['est_wall_lo'], D['est_wall_hi'], D['lag_s']))
        P('')
        P('perf.csv rows around it (per-frame counters):')
        P('')
        L.extend(md(['data row', 'file line'] + D['perf_hdr'], [[str(x) for x in row] for row in D['perf_rows']]))
        P('')
        P('sys.csv samples (1 s; "in" = the interval containing the frame end estimate range):')
        P('')
        L.extend(md(['in', 'wall (end)', 'phase', 'cpu util', 'perf', 'P util', 'E util', 'P MHz', 'E MHz', 'busy_t', 'util_LP', 'game', 'ng_t', 'ng_u', 'idle_s', 'fg', 'desktop', 'overlay'],
                    [['Y' if s['in_frame_second'] else '', s['wall'], s['phase'], f(s['cpu_util'], 1), f(s['cpu_perf'], 1), f(s['p_util'], 1), f(s['e_util'], 1),
                      f(s['p_eff'], 0), f(s['e_eff'], 0), f(s['busy_t']), f(s['util_LP']), f(s['game']), f(s['ng_t']), f(s['ng_u']),
                      f(s['idle_s'], 1), s['fg_game'], s['input_desktop'], s['overlay']] for s in D['sys']]))
        P('')
        P('proc.csv rows (game process; each row covers the second before it):')
        P('')
        L.extend(md(['covers', 'wall', 't_s', 'phase', 'cpu_cores', 'cpu_s', 'ws_mb', 'commit_mb', 'threads', 'handles', 'responding', 'log_lines', 'perf_csv_bytes', 'free_ram_gb', 'note'],
                    [['Y' if p['covers_frame'] else '', p['wall'], p['t_s'], p['phase'], p['cpu_cores'], p['cpu_s'], p['ws_mb'], p['commit_mb'], p['threads'],
                      p['handles'], p['responding'], p['log_lines'], p['perf_csv_bytes'], p['free_ram_gb'], p['note']] for p in D['proc']]))
        if D['gpu']:
            P('')
            P('gpu.csv (NVML, MX570; time = driver start + t_s):')
            P('')
            L.extend(md(['wall', 'dt to frame s', 'pstate', 'gr MHz', 'mem MHz', 'temp C', 'power W', 'util gpu', 'util mem', 'throttle'],
                        [[g['wall'], f(g['dt_s'], 2), g['pstate'], g['gr_mhz'], g['mem_mhz'], g['temp_c'], g['power_w'], g['util_gpu'], g['util_mem'], g['throttle']] for g in D['gpu']]))
        P('')
        P('game.log entries within 2 s of the frame: ' + ('; '.join('%s (dt %+.3f s) [%s] [%s] [t%s] %s' % (x['wall'], x['dt_s'], x['level'], x['cat'], x['tid'], x['msg']) for x in D['log']) or 'none'))
        P('')
        P('threads.csv top threads (whole window): ' + '; '.join('%s %s %s%% (max %s%%)' % (t['tid'], t['name'], t['busy_pct'], t['max_busy_pct']) for t in D['threads_top']))
        J['spike_detail'] = D

    P('')
    P('### 3.2 Per run (scored W6 runs; cold runs listed last)')
    P('')
    rows = []
    allsp = []
    order = []
    for stamp in W6:
        for r in folders[stamp]['runs']:
            if not r.get('err'):
                order.append((stamp, r['run']))
    order.sort(key=lambda k: (not w6[k].get('scored', False) if k in w6 else True, w6.get(k, {}).get('arm', ''), k[0], k[1]))
    for key in order:
        fo = w6.get(key)
        if fo is None or fo.get('err'):
            rows.append([key[0][-4:], key[1], 'ERROR', fo.get('err') if fo else ''] + [''] * 9)
            continue
        c = fo['check']
        nt = len(fo['toypad'])
        ns = sum(1 for t in fo['toypad'] if t['spike'])
        nsp_toy = sum(1 for s in fo['spikes'] if s['toypad_dt_s'] is not None and abs(s['toypad_dt_s']) <= TOY_WIN)
        rows.append([key[0][-4:], fo['run'] + ('' if fo['scored'] else ' (unscored)'), fo['arm'], fo['n_frames'], fo['n_gt16'], fo['n_gt33'],
                     f(fo['max_ms'], 2), f(fo['p999_ms'], 2), c['row_convention_offset'],
                     'ok' if (c['frames_json_frames'] == c['my_frames'] and c['frames_json_over33'] == c['my_over33']) else 'MISMATCH %s/%s %s/%s' % (c['frames_json_frames'], c['my_frames'], c['frames_json_over33'], c['my_over33']),
                     '%d/%d' % (nsp_toy, fo['n_gt16']), '%d/%d' % (ns, nt),
                     ' '.join(f(t['max_ms'], 1) for t in fo['toypad']) or '-', '%s / %s' % (f(fo['bin_max_median'], 1), f(fo['bin_max_p90'], 1)), f(fo['lag_s'], 3)])
        allsp += fo['spikes']
    L.extend(md(['pass', 'run', 'arm', 'frames', '>16.7', '>33', 'max ms', 'p99.9 ms', 'row conv', 'vs frames.json', 'spikes within 0.4 s of Toypad',
                 'Toypad ex. with a >16.7 ms frame', 'max ms within 0.4 s of each Toypad ex.', 'baseline 0.8 s bin max med / p90', 'lag s'], rows))
    P('')
    sc_sp = [s for s in allsp if s['scored']]
    P('### 3.3 Every frame over 16.7 ms (scored W6 runs: %d frames in %d runs; cold runs: %d)'
      % (len(sc_sp), len(set((s['stamp'], s['run']) for s in sc_sp)), len(allsp) - len(sc_sp)))
    P('')
    rows = []
    for s in sorted(allsp, key=lambda s: (not s['scored'], s['arm'], s['stamp'], s['run'], s['k'])):
        rows.append([s['stamp'][-4:], s['run'] + ('' if s['scored'] else ' (unscored)'), s['arm'], s['k'], s['row'], f(s['t_start_s'], 3), f(s['t_end_s'], 3),
                     f(s['ms'], 2), s['est_wall'], s['sys_wall'][:8] + ('*' if s['sys_samples_differ_over_lag'] else ''),
                     f(s['p_util'], 1), f(s['e_eff'], 0), f(s['ng_t']), f(s['ng_u']), f(s['game']), f(s['proc_cpu_cores']),
                     f(s['pipeline_cache_misses'], 0), f(s['texture_cache_misses'], 0), f(s['command_buffer_stalls'], 0),
                     f(s['critical_region_contentions'], 0), f(s['toypad_dt_s'], 3), '%s %s' % (f(s['log_dt_s'], 3), s['log_msg'][:40])])
    L.extend(md(['pass', 'run', 'arm', 'win frame #', 'data row', 'T start s', 'T end s', 'ms', 'est. wall', 'sys sample', 'P util', 'E MHz', 'ng_t', 'ng_u', 'game',
                 'proc cores', 'pipe miss', 'tex miss', 'cb stalls', 'crit cont', 'nearest Toypad dt s', 'nearest game.log line dt s'], rows))
    P('')
    P('(* = the lag range spans two sys.csv samples.) Toypad exchange = game.log Toypad[Write]/[Read] lines within 0.25 s; dt = log time - frame estimate (positive: the log line is later).')
    arm_ct = {}
    for key in order:
        fo = w6.get(key)
        if not fo or fo.get('err') or not fo['scored']:
            continue
        a = arm_ct.setdefault((key[0], fo['arm']), [0, 0, 0, 0])
        a[0] += 1
        a[1] += fo['n_gt16']
        a[2] += fo['n_gt33']
        a[3] += fo['n_frames']
    P('')
    P('Per arm and pass (scored): ' + '; '.join('%s %s: %d runs, %d frames >16.7 ms, %d >33 ms (of %d frames)' % (k[0][-4:], k[1], v[0], v[1], v[2], v[3]) for k, v in sorted(arm_ct.items(), key=lambda kv: (kv[0][1], kv[0][0]))))
    J['w6_frames'] = {'%s/%s' % k: {kk: vv for kk, vv in v.items() if not kk.startswith('_')} for k, v in w6.items()}
    J['w6_arm_counts'] = {'%s/%s' % k: v for k, v in arm_ct.items()}

    # ---- 4. game.log
    P('')
    P('## 4. game.log, dumps and crash markers (all runs, all 7 folders)')
    P('')
    P('Per run: game.log lines; levels from the `[time] [level] [cat]` prefix; STUCK = any line containing "stuck" (case-insensitive), STUCK-LOCK owner site parsed from site=/owner= if present; '
      '[error]/[critical] by level or literal tag; hang = \\bhang(s|ing|ed)?\\b or \\bhung\\b; alarm = exception/access violation/fatal/assert/abort/deadlock/watchdog/crash. '
      '.dmp/.mdmp/.hdmp searched in the run dir, user\\ and user\\* (one level). run.json werfault_seen / foreign_crash_dumps.')
    P('')
    rows = []
    gl_rows = []
    for lab, stamp in MATS:
        R = [r for r in folders[stamp]['runs'] if not r.get('err')]
        agg = Counter()
        sites = Counter()
        exs = {}
        for r in R:
            lg = r['log']
            agg['runs'] += 1
            agg['logs'] += 1 if lg['exists'] else 0
            agg['lines'] += lg['lines']
            for lv, n in lg['levels'].items():
                agg['lvl_' + lv] += n
            for k in ('stuck', 'stuck_lock', 'error', 'critical', 'hang', 'alarm'):
                agg[k] += lg[k]
            sites.update(lg['stuck_lock_sites'])
            for k, v in lg['examples'].items():
                exs.setdefault(k, [])
                exs[k] += ['%s: %s' % (r['run'], x) for x in v][:2]
            agg['dmp'] += len(r['dmps'])
            agg['wer_true'] += 1 if r['werfault_seen'] else 0
            agg['foreign'] += len(r['foreign_crash_dumps'] or []) if isinstance(r['foreign_crash_dumps'], list) else (1 if r['foreign_crash_dumps'] else 0)
            agg['drv_err_runs'] += 1 if (r['driver_err'] and r['driver_err']['n']) else 0
            gl_rows.append([lab, stamp, r['run'], r['arm_label'], lg['exists'], lg['bytes'], lg['lines'], lg['entries'],
                            lg['levels'].get('info', 0), lg['levels'].get('warning', 0), lg['error'], lg['critical'], lg['stuck'],
                            lg['stuck_lock'], json.dumps(dict(lg['stuck_lock_sites'])) if lg['stuck_lock_sites'] else '', lg['hang'], lg['alarm'],
                            ';'.join(r['dmps']), r['werfault_seen'], json.dumps(r['foreign_crash_dumps']),
                            (r['driver_err'] or {}).get('n', ''), (r['sys_err'] or {}).get('n', ''),
                            ' | '.join((r['sys_err'] or {}).get('distinct', []))])
        other_lv = {k[4:]: v for k, v in agg.items() if k.startswith('lvl_') and k not in ('lvl_info', 'lvl_warning')}
        rows.append([lab, stamp, agg['runs'], agg['logs'], agg['lines'], agg['lvl_info'], agg['lvl_warning'], agg['error'], agg['critical'],
                     agg['stuck'], agg['stuck_lock'], json.dumps(dict(sites)) if sites else '-', agg['hang'], agg['alarm'],
                     json.dumps(other_lv) if other_lv else '-', agg['dmp'], agg['wer_true'], agg['foreign'], agg['drv_err_runs']])
        J['gamelog'][stamp] = {'agg': dict(agg), 'stuck_lock_sites': dict(sites), 'examples': exs}
    L.extend(md(['window', 'folder', 'runs', 'game.log', 'lines', 'info', 'warning', '[error]', '[critical]', 'STUCK', 'STUCK-LOCK', 'owner sites', 'hang', 'alarm',
                 'other levels', '.dmp', 'werfault_seen', 'foreign dumps', 'driver.err non-empty'], rows))
    exl = []
    for lab, stamp in MATS:
        for k, v in J['gamelog'][stamp]['examples'].items():
            for x in v[:2]:
                exl.append('- %s %s: %s' % (lab, k, x))
    P('')
    P('Example lines for non-zero categories: ' + ('' if exl else 'none (no stuck/error/critical/hang/alarm line in any game.log).'))
    L.extend(exl[:30])
    sysd = Counter()
    for r in allruns:
        if not r.get('err') and r.get('sys_err'):
            for x in r['sys_err']['distinct']:
                sysd[x] += 1
    P('')
    P('sys.err.txt distinct lines (runs): ' + ('; '.join('"%s" (%d)' % kv for kv in sysd.most_common(5)) or 'none'))
    P('')
    P('Runner logs (`logs/*.txt`, text only) keyword counts per folder, with examples:')
    P('')
    rows = []
    for lab, stamp in MATS:
        rl = folders[stamp]['rl']
        J['runner_logs'][stamp] = {'files': rl['files'], 'lines': rl['lines'], 'counts': dict(rl['counts']), 'examples': rl['examples'], 'dmp_top': rl['dmp_top']}
        rows.append([lab, stamp, rl['files'], rl['lines']] + [rl['counts'].get(k, 0) for k, _ in RL_PATS] + [';'.join(rl['dmp_top']) or '-'])
    L.extend(md(['window', 'folder', 'files', 'lines'] + [k for k, _ in RL_PATS] + ['.dmp (root/logs)'], rows))
    exl = []
    for lab, stamp in MATS:
        for k, v in folders[stamp]['rl']['examples'].items():
            exl.append('- %s %s: %s' % (lab, k, ' || '.join(v)))
    if exl:
        P('')
        L.extend(exl)

    # ---- 5. follow-up items
    try:
        X5.section5(P, L, J, folders, fbs)
    except Exception:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        J['extra_error'] = tb
        P('')
        P('**Section 5 error:**')
        P('')
        P('```')
        P(tb)
        P('```')

    # ---- files
    P('')
    P('## Files')
    P('')
    for fn in ('audit.md', 'audit.json', 'runs.csv', 'spikes.csv', 'gamelog.csv', 'audit.py', 'audit5.py', 'findings.md'):
        P('- `build/agent8/readout/w-followup/audit/%s`' % fn)
    for lab, stamp in MATS:
        P('- `build/agent8/readout/w-followup/audit/timerq3-%s.csv` / `.txt` (%s)' % (stamp, lab))
    P('')
    P('Runtime %.1f s.' % (time.time() - t_start))

    # ------------------------------------------------------------------ files
    with open(os.path.join(HERE, 'audit.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')
    wk = ['n', 'game_slope', 'game_cores_mean', 'busyB_mean', 'utilLP_mean', 'ngB_mean', 'ngB_med', 'ngB_p90', 'ngB_max', 'ngB_min',
          'ngU_mean', 'ngU_med', 'ngU_p90', 'ngU_max', 'P_util_mean', 'p_util_max', 'E_util_mean', 'p_eff_mean', 'p_eff_min', 'e_eff_mean',
          'e_eff_min', 'P_busy_pct', 'E_busy_pct', 'P_sat_share', 'E_sat_share', 'e_lt800_share', 'slow_run_max', 'idle_min',
          'fg_game_share', 'bP_raw_max', 'bE_raw_max']
    with open(os.path.join(HERE, 'runs.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['window', 'stamp', 'idx', 'run', 'arm', 'scored', 'valid_timing', 'excluded', 'flags_excluding', 'flags_info', 'fps_mean', 'fps_rel',
                    'res_max_ms', 'res_over33', 'res_fg_share', 'res_idle_min_s', 'win_wall', 'z_ngB_mean', 'z_ngU_mean', 'z_arm_ngB', 'burst_ngB',
                    'burst_ngU', 'chg_win', 'chg_run', 'flag'] + ['win_' + k for k in wk] + ['wu_' + k for k in wk])
        for r in allruns:
            if r.get('err'):
                w.writerow([r['window'], r['stamp'], r['idx'], r['run'], 'ERROR ' + r['err']])
                continue
            rf = r.get('rflags') or {}
            w.writerow([r['window'], r['stamp'], r['idx'], r['run'], r['arm_label'], r['scored'], r['valid'], r['excluded'], r['flags_excluding'],
                        r['flags_info'], r['res_fps_mean'], rnd(r.get('fps_rel')), r['res_max_ms'], r['res_over33'], r['res_fg_share'], r['res_idle_min_s'],
                        r['win_wall'], rnd((rf.get('ngB_mean') or {}).get('z')), rnd((rf.get('ngU_mean') or {}).get('z')), rnd(r.get('z_arm_ngB')),
                        (r.get('burst') or {}).get('ngB', ''), (r.get('burst') or {}).get('ngU', ''), chg_s(r['chg_win']), chg_s(r['chg_run']),
                        ' | '.join(r.get('flag_why') or [])] + [rnd(r['win'].get(k)) for k in wk] + [rnd(r['wu'].get(k)) for k in wk])
    spk = ['stamp', 'window', 'run', 'arm', 'scored', 'k', 'row', 'file_line', 't_start_s', 't_end_s', 'ms', 'est_wall', 'est_epoch_lo', 'est_epoch_hi',
           'sys_wall', 'sys_samples_differ_over_lag', 'p_util', 'e_util', 'p_eff', 'e_eff', 'busy_t', 'util_LP', 'game', 'ng_t', 'ng_u', 'idle_s', 'fg_game',
           'proc_cpu_cores', 'proc_threads', 'proc_responding', 'pipeline_cache_misses', 'texture_cache_misses', 'command_buffer_stalls',
           'critical_region_contentions', 'draw_calls', 'active_threads', 'functions_dispatched', 'toypad_dt_s', 'log_dt_s', 'log_msg']
    with open(os.path.join(HERE, 'spikes.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(spk)
        for s in sorted(allsp, key=lambda s: (s['stamp'], s['run'], s['k'])):
            w.writerow([rnd(s.get(k), 6) for k in spk])
    with open(os.path.join(HERE, 'gamelog.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['window', 'stamp', 'run', 'arm', 'game_log', 'bytes', 'lines', 'entries', 'info', 'warning', 'error', 'critical', 'stuck', 'stuck_lock',
                    'stuck_lock_sites', 'hang', 'alarm', 'dmp_files', 'werfault_seen', 'foreign_crash_dumps', 'driver_err_lines', 'sys_err_lines', 'sys_err_distinct'])
        for row in gl_rows:
            w.writerow(row)
    runs_j = []
    for r in allruns:
        d = {}
        for k, v in r.items():
            if k.startswith('_'):
                continue
            if k == 'log':
                v = {kk: (dict(vv) if isinstance(vv, Counter) else vv) for kk, vv in v.items() if not kk.startswith('_')}
            d[k] = v
        runs_j.append(d)
    J['runs'] = runs_j
    for lab, stamp in MATS:
        J['matrices'][stamp] = {'window': lab, **folders[stamp]['F']}
    with open(os.path.join(HERE, 'audit.json'), 'w', encoding='utf-8') as fh:
        json.dump(J, fh, indent=1, default=lambda o: dict(o) if isinstance(o, Counter) else str(o))
    print('wrote audit.md, audit.json, runs.csv, spikes.csv, gamelog.csv in', HERE)
    print('errors:', errs)
    print('runtime %.1f s' % (time.time() - t_start))
    return 0


if __name__ == '__main__':
    sys.exit(main())
