#!/usr/bin/env python3
"""Agent 6, task #16 part 2: the W6 logdiff kit, one command per matrix folder. Read-only, stdlib only.

  python -B build/agent6/w6/w6_kit.py <matrix_dir> [--expect FILE] [--ref ARM] [--matrix-json FILE]
                                      [--out DIR] [--skip-logdiff] [--top N]
  W6 morning:  build\\agent6\\w6\\RUN-W6-LOGDIFF.cmd build\\agent8\\matrix\\<W6 folder>

Runs are the dirs runs/HHMM-<arm>-rN of <matrix_dir>. A cold run (HHMM-cold-<arm>) is its own arm, cold-<arm>, but it
is checked with <arm>'s rules and config. Per run:
  1. Expect rules (--expect, default expect-w6.json next to this file). Each 'require' text must be in the run's
     game*.log set (all rotations), no 'forbid' or 'forbid_all' text may be there, and each 'exact' text must occur
     exactly N times; otherwise FAIL. Texts are substrings of the message part of a line. 'note_all' texts
     (STUCK-LOCK, Minidump written to) -> NOTE. [warning]/[error]/[critical] line totals vs 'levels' -> NOTE when
     they differ. Every 'count' text is counted.
  2. STUCK-LOCK episodes (a 'still not acquired after' line plus the lines after it): critical section, wait, owner
     tid and lr, owner site, the waiter's first caller, the hang dump, and where the stall fell against run.json's
     measured window. Sites: H1 = the owner's lr is in sub_83FAF180 (the L1 fence-wait poll; finding 10) or at
     83FBF868; H2 = in the function holding 83FB09F0; else 'other'. Functions come from the bin's
     legodimensions.map. A stall that overlaps the measured window -> FAIL (that run's timing is invalid); outside
     the window -> NOTE (finding 10 is known and pre-existing).
  3. run.json. cvars (params.cvar, or a cvars dict), env_set and bin_dir vs the arm in matrix.json (the folder's
     copy, else --matrix-json) -> FAIL on any difference. status != OK, valid_timing false, exit code != 0, no
     clean WM_CLOSE exit, killed, or WER -> FAIL. *.dmp files -> FAIL unless they are hang dumps named by STUCK
     episodes (then NOTE). Runner exclusion flags, dialogs, foreign crash dumps, free RAM < 6 GB at start (G10), and
     a log that does not end with the clean-exit lines -> NOTE.
  4. Slow state, with the math of Agent 11's bench/agent11/timerq_slowstate_3mode.ps1: sys.csv rows from the first
     frame on (run.json ff_signal_epoch_s), low = e_eff_mhz < 800, onset_s = start of the first run of 3+ low rows,
     slow_pct = low rows / all rows, span_s = last row. Per arm: slow runs, mean slow_pct, mean onset of slow runs.
  5. Against the reference arm (--ref, default the expect file's 'reference', s0):
     build/agent6/w4b/w4b_logdiff.py writes gate_logdiff FAIL findings, NEW/MORE/GONE warning keys and ONLY keys to
     <out>/logdiff/. build/agent6/w4b/w4b_extra.py writes the exact-text diff, close fields and per-run counts to
     <out>/extra.txt. Both run as child processes at below-normal priority, one after the other. A gate FAIL finding
     or a NEW error/critical key -> FAIL, unless it is a STUCK episode's own line. NEW warning keys, MORE, GONE, and
     ONLY keys that no text of the arm's rules matches -> NOTE.
Writes <out>/w6-summary.txt (also printed) and <out>/w6-data.json. The default <out> is build/agent6/w6/out-<folder>.
Nothing is written into the matrix folder. Exit 0 = no FAIL, 1 = at least one FAIL, 2 = usage error.
"""
import sys
sys.dont_write_bytecode = True
import argparse, csv, datetime, glob, json, os, re, statistics, subprocess, time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
W4B = os.path.join(ROOT, 'build', 'agent6', 'w4b')
DEFAULT_EXPECT = os.path.join(HERE, 'expect-w6.json')
DEFAULT_MATRIX_JSON = os.path.join(ROOT, 'build', 'agent5', 'w6-draft', 'matrix-window6.json')
LINE_RE = re.compile(r'^\[(?P<ts>\d{4}-\d\d-\d\d [0-9:.]+)\] \[(?P<lvl>[a-z]+)\] \[(?P<cat>[^\]]*)\] (?:\[t\d+\] )?(?P<msg>.*)$')
ROT_RE = re.compile(r'^game(?:\.(\d+))?\.log$', re.I)
ARM_RE = re.compile(r'^\d{4}-(cold-[A-Za-z0-9]+|[A-Za-z0-9]+)(?:-|$)')
W4B_ARM_REGEX = r'^runs/\d{4}-(cold-[A-Za-z0-9]+|[A-Za-z0-9]+)(?:-|$)'
EXIT_SEQ = ('Window closing, shutting down', 'Execution complete', 'Title terminated; hard-exiting process')
LEVELS = ('warning', 'error', 'critical')
BELOW_NORMAL = 0x00004000
EMHZ, MINROWS, MIN_FREE_GB = 800.0, 3, 6.0
# STUCK-LOCK text (rexglue-sdk kernel/xboxkrnl/xboxkrnl_rtl.cpp). An episode is 5 [error] 'STUCK-LOCK: ...' lines
# (still not acquired / the owner is tid ... parked at lr= / owner's callers / waiter's callers / GPU thread: PM4)
# and 1 [critical] '[FATAL] Minidump written to hang-<pid>.dmp' line (gate A, s4b-24, s4b-20 game.logs).
EP_START = 'still not acquired after'
EP_TEXTS = ('STUCK-LOCK', 'Minidump written to')
CS_RE = re.compile(r'critical section (0x[0-9A-Fa-f]+)')
AFTER_RE = re.compile(r'still not acquired after ([0-9.]+)\s*s')
OWNER_TID_RE = re.compile(r'owner is tid (0x[0-9A-Fa-f]+|\d+)')
OWNER_LR_RE = re.compile(r'parked at lr=([0-9A-Fa-f]{8})')
OWNER_CALLERS_RE = re.compile(r"owner's callers: ([0-9A-Fa-f]{8}(?:\s*<-\s*[0-9A-Fa-f]{8})*)")
WAITER_LR_RE = re.compile(r"waiter's callers: lr=([0-9A-Fa-f]{8})")
PM4_RE = re.compile(r'PM4 opcode (0x[0-9A-Fa-f]+)')
DUMP_RE = re.compile(r'Minidump written to\s*(.*?)\s*$')
H1_FUNC, H1_CALLER, H2_ADDR = 0x83FAF180, 0x83FBF868, 0x83FB09F0
SUB_RE = re.compile(rb'sub_([0-9A-Fa-f]{8})\b')
_MAPS = {}


def load_json(p):
    try:
        with open(p, encoding='utf-8-sig') as fh:
            return json.load(fh)
    except Exception as e:  # noqa: BLE001
        return {'_error': '%s: %s' % (os.path.basename(p), e)}


def log_files(rd):
    found = []
    for p in glob.glob(os.path.join(rd, 'game*.log')):
        m = ROT_RE.match(os.path.basename(p))
        if m:
            found.append((int(m.group(1)) if m.group(1) else 0, p))
    found.sort(key=lambda t: -t[0])  # highest rotation index = oldest
    return [p for _, p in found]


def ts_dt(s):
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(s, fmt)
        except (TypeError, ValueError):
            pass
    return None


def kv_norm(items):
    """'k=v' strings or a dict -> {k: v as lower-case text}; Python/JSON booleans become true/false."""
    out = {}
    if isinstance(items, dict):
        items = ['%s=%s' % (k, ('true' if v else 'false') if isinstance(v, bool) else v) for k, v in items.items()]
    for x in items or []:
        x = str(x).strip()
        if x.startswith('--'):
            x = x[2:]
        k, _, v = x.partition('=')
        out[k.strip()] = v.strip().lower()
    return out


def map_funcs(path):
    """Sorted guest function starts from the sub_XXXXXXXX names of a legodimensions.map (cached per path)."""
    if path in _MAPS:
        return _MAPS[path]
    starts = []
    try:
        with open(path, 'rb') as fh:
            starts = sorted(set(int(h, 16) for h in SUB_RE.findall(fh.read())))
    except OSError:
        pass
    _MAPS[path] = starts
    return starts


def func_of(starts, addr):
    lo, hi = 0, len(starts)
    while lo < hi:
        mid = (lo + hi) // 2
        if starts[mid] <= addr:
            lo = mid + 1
        else:
            hi = mid
    return starts[lo - 1] if lo else None


def site_of(lr, starts):
    if lr is None:
        return 'unknown', None
    if not starts:  # no map: exact addresses and a 0x180-byte guess for sub_83FAF180
        if lr == H1_CALLER or H1_FUNC <= lr < H1_FUNC + 0x180:
            return 'H1', None
        return ('H2' if lr == H2_ADDR else 'other'), None
    f = func_of(starts, lr)
    if f == H1_FUNC or lr == H1_CALLER:
        return 'H1', f
    if f is not None and f == func_of(starts, H2_ADDR):
        return 'H2', f
    return 'other', f


def scan_log(rd, pats):
    r = dict(files=[], lines=0, levels=Counter(), cnt=Counter(), first_ts=None, last_ts=None, episodes=[],
             ep_lines=Counter(), other_err=[], other_err_n=0, tail=[], toy=0)
    cur = None
    for fp in log_files(rd):
        try:
            r['files'].append([os.path.basename(fp), os.path.getsize(fp)])
            fh = open(fp, encoding='utf-8', errors='replace')
        except OSError as e:
            r['files'].append([os.path.basename(fp), 'ERROR %s' % e])
            continue
        with fh:
            for raw in fh:
                line = raw.rstrip('\r\n')
                if not line:
                    continue
                r['lines'] += 1
                m = LINE_RE.match(line)
                if m:
                    ts, lvl, msg = m.group('ts'), m.group('lvl'), m.group('msg')
                    r['first_ts'] = r['first_ts'] or ts
                    r['last_ts'] = ts
                else:
                    ts, lvl, msg = None, 'raw', line
                r['levels'][lvl] += 1
                r['tail'] = (r['tail'] + [msg])[-3:]
                if 'Toypad' in msg:
                    r['toy'] += 1
                for p in pats:
                    if p in msg:
                        r['cnt'][p] += 1
                if EP_START in msg:
                    a = AFTER_RE.search(msg)
                    c = CS_RE.search(msg)
                    cur = dict(ts=ts, cs=c.group(1) if c else None, after_s=float(a.group(1)) if a else None,
                               owner_tid=None, owner_lr=None, owner_callers=None, waiter_lr=None, pm4=None, dump=None,
                               lines=0, first=line[:400])
                    r['episodes'].append(cur)
                in_ep = any(t in msg for t in EP_TEXTS)
                if in_ep:
                    r['ep_lines'][lvl] += 1
                    if cur is not None:
                        cur['lines'] += 1
                        x = OWNER_TID_RE.search(msg)
                        if x and cur['owner_tid'] is None:
                            cur['owner_tid'] = x.group(1)
                        x = OWNER_LR_RE.search(msg)
                        if x and cur['owner_lr'] is None:
                            cur['owner_lr'] = x.group(1).upper()
                        x = OWNER_CALLERS_RE.search(msg)
                        if x and cur['owner_callers'] is None:
                            cur['owner_callers'] = [y.upper() for y in re.findall(r'[0-9A-Fa-f]{8}', x.group(1))]
                        x = WAITER_LR_RE.search(msg)
                        if x and cur['waiter_lr'] is None:
                            cur['waiter_lr'] = x.group(1).upper()
                        x = PM4_RE.search(msg)
                        if x and cur['pm4'] is None:
                            cur['pm4'] = x.group(1)
                        x = DUMP_RE.search(msg)
                        if x and cur['dump'] is None:
                            cur['dump'] = x.group(1)
                elif lvl in ('error', 'critical'):
                    r['other_err_n'] += 1
                    if len(r['other_err']) < 5:
                        r['other_err'].append(line[:300])
    r['exit_seq'] = len(r['tail']) == 3 and all(p in l for p, l in zip(EXIT_SEQ, r['tail']))
    return r


def slow_state(rd, ff):
    """Agent 11's timerq_slowstate_3mode.ps1 math (E cores below 800 MHz for 3+ sys.csv rows in a row)."""
    p = os.path.join(rd, 'sys.csv')
    try:
        ff = float(ff)
    except (TypeError, ValueError):
        return None
    if ff <= 0 or not os.path.exists(p):
        return None
    s = []
    with open(p, newline='', encoding='utf-8-sig', errors='replace') as fh:
        for x in csv.DictReader(fh):
            e, ep = x.get('e_eff_mhz'), x.get('epoch_s')
            if e in (None, '') or ep in (None, ''):
                continue
            try:
                e, t = float(e), float(ep) - ff
            except ValueError:
                continue
            if t >= 0:
                s.append((t, e))
    if not s:
        return None
    low = run = 0
    onset = first = None
    for t, e in s:
        if e < EMHZ:
            low += 1
            run += 1
            if run == 1:
                first = t
            if run >= MINROWS and onset is None:
                onset = first
        else:
            run = 0
    return dict(onset_s=onset, slow_pct=100.0 * low / len(s), span_s=s[-1][0], rows=len(s))


def run_facts(rd):
    p = os.path.join(rd, 'run.json')
    if not os.path.exists(p):
        return None
    d = load_json(p)
    c = d.get('close') or {}
    pr = d.get('params') or {}
    cv = d.get('cvars')
    cvars = kv_norm(cv) if isinstance(cv, (dict, list)) and cv else kv_norm(pr.get('cvar') or [])
    ms, me = d.get('measure_start') or {}, d.get('measure_end') or {}
    return dict(
        _error=d.get('_error'), tag=d.get('tag'), status=d.get('status'), valid_timing=d.get('valid_timing'),
        valid_why=d.get('valid_timing_why') or [], problems=d.get('problems') or [], bin_dir=d.get('bin_dir'),
        cvars=cvars, env=kv_norm(d.get('env_set') or {}),
        exit_code=d.get('exit_code', c.get('exit_code')), exit_hex=d.get('exit_code_hex', c.get('exit_code_hex')),
        wm_close=c.get('wm_close_posted'), clean=c.get('clean'), killed=c.get('killed'), exited=c.get('exited'),
        early=d.get('exited_early'), wer=d.get('werfault_seen'), dialogs=d.get('dialogs') or [],
        foreign_dumps=d.get('foreign_crash_dumps') or [], excluded=d.get('excluded'),
        flags_excluding=d.get('flags_excluding') or [], flags=d.get('flags') or [],
        free_gb=d.get('free_ram_gb_at_start'), ff=d.get('ff_signal_epoch_s'), start=d.get('start'),
        nogrowth=d.get('perf_csv_max_no_growth_window_s'), nrw=d.get('not_responding_window_samples'),
        m_start=ms.get('wall'), m_end=me.get('wall'), runner_error=d.get('runner_error'))


def matrix_arms(mj):
    arms = {}
    for a in (mj.get('arms') or []) if isinstance(mj, dict) else []:
        if isinstance(a, dict) and a.get('id'):
            arms[str(a['id']).lower()] = dict(cvars=kv_norm(a.get('cvars') or []), env=kv_norm(a.get('env') or {}),
                                              bin=str(a.get('bin') or ''))
    return arms


def key_norm(t):
    """Normalize a rule text the way w4b_logdiff normalizes its keys (gate_logdiff.norm, read-only import)."""
    try:
        p = os.path.join(ROOT, 'bench', 'agent8', 'run')
        if p not in sys.path:
            sys.path.insert(0, p)
        import gate_logdiff
        return gate_logdiff.norm(t)
    except Exception:
        return re.sub(r'\b0x[0-9A-Fa-f]+\b|\d+', '#', t)


def norm_path(p):
    return os.path.normcase(os.path.normpath(str(p or ''))).replace('\\', '/').rstrip('/')


def fmt(v, spec='%s'):
    return '-' if v is None else (spec % v)


def run_tool(args, log_path):
    t0 = time.time()
    flags = BELOW_NORMAL if os.name == 'nt' else 0
    with open(log_path, 'w', encoding='utf-8') as fh:
        p = subprocess.run([sys.executable, '-B'] + args, stdout=fh, stderr=subprocess.STDOUT, cwd=ROOT,
                           creationflags=flags)
    return p.returncode, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('matrix')
    ap.add_argument('--expect', default=DEFAULT_EXPECT)
    ap.add_argument('--ref', help="reference arm (default: the expect file's 'reference')")
    ap.add_argument('--matrix-json', default=None, help='used when the folder has no matrix.json (default: %s)'
                    % os.path.relpath(DEFAULT_MATRIX_JSON, ROOT))
    ap.add_argument('--out', help='output dir (default build/agent6/w6/out-<matrix folder name>)')
    ap.add_argument('--skip-logdiff', action='store_true', help='skip w4b_logdiff.py and w4b_extra.py')
    ap.add_argument('--top', type=int, default=30)
    a = ap.parse_args()
    t_start = time.time()
    mdir = os.path.abspath(a.matrix)
    if not os.path.isdir(os.path.join(mdir, 'runs')):
        print('no runs/ folder in %s' % mdir)
        return 2
    ex = load_json(a.expect)
    if ex.get('_error'):
        print('expect file: %s' % ex['_error'])
        return 2
    ref = (a.ref or ex.get('reference') or 's0').lower()
    out = os.path.abspath(a.out or os.path.join(HERE, 'out-' + os.path.basename(mdir.rstrip('\\/'))))
    if norm_path(out).startswith(norm_path(mdir) + '/') or norm_path(out) == norm_path(mdir):
        print('refusing to write inside the matrix folder: %s' % out)
        return 2
    os.makedirs(out, exist_ok=True)
    mj_path = os.path.join(mdir, 'matrix.json')
    if not os.path.exists(mj_path):
        mj_path = a.matrix_json or DEFAULT_MATRIX_JSON
    mj = load_json(mj_path) if os.path.exists(mj_path) else {'_error': 'missing %s' % mj_path}
    marms = matrix_arms(mj)
    rules = {str(k).lower(): v for k, v in (ex.get('arms') or {}).items()}
    forbid_all = list(ex.get('forbid_all') or [])
    note_all = list(ex.get('note_all') or [])
    levels_exp = ex.get('levels') or {}
    count_pats = list(ex.get('count') or [])
    pats = []
    for p in count_pats + forbid_all + note_all + [t for r in rules.values() for k in ('require', 'forbid')
                                                    for t in (r.get(k) or [])] + \
            [t for r in rules.values() for t in (r.get('exact') or {})]:
        if p not in pats:
            pats.append(p)

    rdirs = sorted(d for d in glob.glob(os.path.join(mdir, 'runs', '*'))
                   if os.path.isdir(d) and (log_files(d) or os.path.exists(os.path.join(d, 'run.json'))))
    runs, arms = {}, defaultdict(list)
    for rd in rdirs:
        name = os.path.basename(rd)
        m = ARM_RE.match(name)
        arm = m.group(1).lower() if m else '?'
        base_arm = arm[5:] if arm.startswith('cold-') else arm
        R = dict(name=name, arm=arm, rules_arm=base_arm, fail=[], note=[])
        R['log'] = scan_log(rd, pats)
        R['facts'] = run_facts(rd)
        R['slow'] = slow_state(rd, (R['facts'] or {}).get('ff'))
        R['dumps'] = sorted(os.path.relpath(x, rd) for x in glob.glob(os.path.join(rd, '**', '*.dmp'), recursive=True))
        runs[name] = R
        arms[arm].append(name)

    # ---- per-run checks
    for name, R in runs.items():
        L, F, rl = R['log'], R['facts'], rules.get(R['rules_arm'])
        fail, note = R['fail'], R['note']
        if not L['files']:
            fail.append('no game*.log')
        if rl is None:
            note.append('no rules for arm %s in the expect file' % R['rules_arm'])
            rl = {}
        for t in rl.get('require') or []:
            if not L['cnt'][t]:
                fail.append('missing required "%s"' % t)
        for t in list(rl.get('forbid') or []) + forbid_all:
            if L['cnt'][t]:
                fail.append('forbidden "%s" x%d' % (t, L['cnt'][t]))
        for t, n in (rl.get('exact') or {}).items():
            if L['cnt'][t] != int(n):
                fail.append('"%s" x%d, expected exactly %d' % (t, L['cnt'][t], int(n)))
        for t in note_all:
            if L['cnt'][t]:
                note.append('"%s" x%d' % (t, L['cnt'][t]))
        lv = {k: L['levels'][k] for k in LEVELS}
        if levels_exp and any(lv[k] != int(levels_exp.get(k, lv[k])) for k in LEVELS):
            note.append('levels W/E/C %d/%d/%d, expected %s/%s/%s' % (
                lv['warning'], lv['error'], lv['critical'],
                levels_exp.get('warning', '-'), levels_exp.get('error', '-'), levels_exp.get('critical', '-')))
        if L['other_err_n']:
            note.append('%d error/critical line(s) outside STUCK episodes, e.g. %s' % (L['other_err_n'], L['other_err'][0]))
        if L['files'] and not L['exit_seq']:
            note.append('log does not end with the clean-exit lines: %r' % L['tail'])
        # STUCK episodes
        ms, me = ts_dt((F or {}).get('m_start')), ts_dt((F or {}).get('m_end'))
        ep_dumps = set()
        for ep in L['episodes']:
            lr = int(ep['owner_lr'], 16) if ep['owner_lr'] else None
            mp = None
            for cand in (os.path.join(str((F or {}).get('bin_dir') or ''), 'legodimensions.map'),
                         os.path.join(mdir, 'runs', name, 'legodimensions.map')):
                if os.path.exists(cand):
                    mp = os.path.abspath(cand)
                    break
            starts = map_funcs(mp) if (mp and lr is not None) else []
            ep['site'], fn = site_of(lr, starts)
            ep['owner_func'] = ('sub_%08X+0x%X' % (fn, lr - fn)) if fn is not None else None
            if ep['waiter_lr'] and starts:
                wf = func_of(starts, int(ep['waiter_lr'], 16))
                ep['waiter_func'] = ('sub_%08X+0x%X' % (wf, int(ep['waiter_lr'], 16) - wf)) if wf else None
            else:
                ep['waiter_func'] = None
            ep['map'] = os.path.relpath(mp, ROOT) if mp else None
            t1 = ts_dt(ep['ts'])
            t0 = (t1 - datetime.timedelta(seconds=ep['after_s'])) if (t1 and ep['after_s'] is not None) else t1
            if t1 is None or ms is None or me is None:
                ep['window'] = 'unknown'
            elif t1 < ms:
                ep['window'] = 'before'
            elif t0 > me:
                ep['window'] = 'after'
            else:
                ep['window'] = 'IN'
            ep['stall_start'] = t0.strftime('%H:%M:%S.%f')[:-3] if t0 else None
            if ep['dump']:
                ep_dumps.add(os.path.basename(ep['dump'].strip('"\'')).lower())
            txt = 'STUCK-LOCK %s %s after %ss, owner tid %s lr=%s (%s, %s), waiter lr=%s, stall from %s, window %s' % (
                ep['ts'][11:23] if ep['ts'] else '?', ep['cs'], fmt(ep['after_s']), ep['owner_tid'], ep['owner_lr'],
                ep['site'], ep['owner_func'] or 'no map', ep['waiter_lr'], ep['stall_start'], ep['window'])
            (fail if ep['window'] == 'IN' else note).append(txt + (' -> timing invalid' if ep['window'] == 'IN' else ''))
        for dp in R['dumps']:
            if os.path.basename(dp).lower() in ep_dumps or (L['episodes'] and os.path.basename(dp).lower().startswith('hang-')):
                note.append('hang dump %s' % dp)
            else:
                fail.append('dump file %s with no STUCK episode naming it' % dp)
        # run.json
        if F is None:
            fail.append('no run.json')
        else:
            if F['_error']:
                fail.append('run.json unreadable: %s' % F['_error'])
            if F['status'] != 'OK':
                fail.append('status %s, problems %s' % (F['status'], F['problems']))
            if F['valid_timing'] is False:
                fail.append('valid_timing false: %s' % F['valid_why'])
            if F['runner_error']:
                fail.append('runner_error %s' % F['runner_error'])
            if F['exit_code'] is None:
                note.append('no exit code in run.json')
            elif str(F['exit_code']) not in ('0',):
                fail.append('exit code %s (%s)' % (F['exit_code'], F['exit_hex']))
            if F['wm_close'] is False or F['clean'] is False:
                fail.append('close: wm_close_posted=%s clean=%s' % (F['wm_close'], F['clean']))
            if F['killed']:
                fail.append('killed')
            if F['early']:
                fail.append('exited early')
            if F['wer']:
                fail.append('WER seen')
            if F['dialogs']:
                note.append('dialogs %s' % F['dialogs'][:3])
            if F['foreign_dumps']:
                note.append('foreign crash dumps %d' % len(F['foreign_dumps']))
            if F['excluded'] or F['flags_excluding']:
                note.append('runner excluded: %s' % (F['flags_excluding'] or F['excluded']))
            try:
                if F['free_gb'] is not None and float(F['free_gb']) < MIN_FREE_GB:
                    note.append('free RAM %.1f GB at start (< %g, G10)' % (float(F['free_gb']), MIN_FREE_GB))
            except (TypeError, ValueError):
                pass
            ma = marms.get(R['rules_arm'])
            if ma is None:
                note.append('arm %s not in %s' % (R['rules_arm'], os.path.basename(mj_path)))
            else:
                if F['cvars'] != ma['cvars']:
                    miss = sorted('%s=%s' % kv for kv in ma['cvars'].items() if F['cvars'].get(kv[0]) != kv[1])
                    extra = sorted('%s=%s' % kv for kv in F['cvars'].items() if ma['cvars'].get(kv[0]) != kv[1])
                    fail.append('cvars differ from matrix.json: missing/changed %s, extra/changed %s' % (miss, extra))
                if F['env'] != ma['env']:
                    fail.append('env_set %s, matrix.json %s' % (F['env'], ma['env']))
                if ma['bin'] and not norm_path(F['bin_dir']).endswith(norm_path(ma['bin'])):
                    fail.append('bin_dir %s, matrix.json %s' % (F['bin_dir'], ma['bin']))
        R['verdict'] = 'FAIL' if fail else ('NOTE' if note else 'PASS')

    # ---- logdiff tools
    tools = {}
    ld_data = None
    if not a.skip_logdiff:
        ld_out = os.path.join(out, 'logdiff')
        rc, dt = run_tool([os.path.join(W4B, 'w4b_logdiff.py'), mdir, '--base', '^%s$' % re.escape(ref),
                           '--arm-regex', W4B_ARM_REGEX, '--out', ld_out, '--top', str(a.top)],
                          os.path.join(out, 'logdiff.log'))
        tools['w4b_logdiff'] = dict(rc=rc, s=round(dt, 1), out=ld_out, log=os.path.join(out, 'logdiff.log'))
        if os.path.exists(os.path.join(ld_out, 'data.json')):
            ld_data = load_json(os.path.join(ld_out, 'data.json'))
        cargs = []
        for p in count_pats:
            cargs += ['--count', p]
        rc, dt = run_tool([os.path.join(W4B, 'w4b_extra.py'), mdir, '--base', ref, '--out',
                           os.path.join(out, 'extra.txt')] + cargs, os.path.join(out, 'extra.log'))
        tools['w4b_extra'] = dict(rc=rc, s=round(dt, 1), out=os.path.join(out, 'extra.txt'),
                                  log=os.path.join(out, 'extra.log'))
        for k, v in tools.items():
            if v['rc'] != 0:
                print('%s exited %s, see %s' % (k, v['rc'], v['log']))

    # ---- per-arm roll-up
    arm_rows, arm_data = [], {}
    order = [ref] + sorted(x for x in arms if x != ref)
    for arm in order:
        if arm not in arms:
            continue
        names = arms[arm]
        rr = [runs[n] for n in names]
        rl = rules.get(arm[5:] if arm.startswith('cold-') else arm) or {}
        ep = [e for R in rr for e in R['log']['episodes']]
        sites = Counter(e['site'] for e in ep)
        cnt = lambda t: [R['log']['cnt'][t] for R in rr]  # noqa: E731
        slows = [R['slow'] for R in rr if R['slow']]
        slow_runs = [s for s in slows if s['onset_s'] is not None]
        A = dict(runs=names, verdict='PASS', fail=[], note=[],
                 stuck=len(ep), stuck_sites=dict(sites), stuck_in_window=sum(1 for e in ep if e['window'] == 'IN'),
                 minidump=sum(cnt('Minidump written to')) if 'Minidump written to' in pats else None,
                 recovered=cnt('Recovered stale physical page protection'),
                 unhandled=cnt('Unhandled guest physical write fault'),
                 protect_failed=[x + y for x, y in zip(cnt('PhysicalHeap::Protect failed'), cnt('BaseHeap::Protect failed'))],
                 levels=['%d/%d/%d' % (R['log']['levels']['warning'], R['log']['levels']['error'],
                                       R['log']['levels']['critical']) for R in rr],
                 slow=dict(runs=len(slows), slow_runs=len(slow_runs),
                           mean_slow_pct=round(statistics.mean(s['slow_pct'] for s in slows), 1) if slows else None,
                           mean_onset_s=round(statistics.mean(s['onset_s'] for s in slow_runs), 1) if slow_runs else None),
                 dumps=sum(len(R['dumps']) for R in rr), counts={t: cnt(t) for t in count_pats})
        pa = ((ld_data or {}).get('per_arm') or {}).get(arm)
        if pa is not None:
            stuck_arm = bool(ep)
            is_ep = lambda k: any(t in k for t in EP_TEXTS)  # noqa: E731
            rule_texts = [t for k in ('require',) for t in (rl.get(k) or [])] + list((rl.get('exact') or {}).keys()) + count_pats
            # logdiff keys are normalized ("1 ms" -> "# ms"), so match the normalized rule texts too
            rule_texts = rule_texts + [key_norm(t) for t in rule_texts]
            g_fail = list((pa.get('fails') or {}).keys())
            g_unexpl = []
            for f in g_fail:
                rn = f.split(':', 1)[0].replace('\\', '/').split('/')[-1]
                Rf = runs.get(rn)
                crit_ok = (Rf is not None and '[critical]' in f and Rf['log']['levels']['critical'] ==
                           Rf['log']['ep_lines']['critical'] and Rf['log']['ep_lines']['critical'] > 0)
                if not crit_ok:
                    g_unexpl.append(f)
            new = pa.get('new') or []
            new_ec = [x['key'] for x in new if not x['key'].startswith('[warning]') and not (stuck_arm and is_ep(x['key']))]
            new_w = [x['key'] for x in new if x['key'].startswith('[warning]') and not (stuck_arm and is_ep(x['key']))]
            only = pa.get('only') or []
            only_unnamed = [x['key'] for x in only if not any(t in x['key'] for t in rule_texts)
                            and not (stuck_arm and is_ep(x['key']))]
            A['logdiff'] = dict(fail=len(g_fail), fail_unexplained=g_unexpl, new=len(new), new_err=new_ec,
                                new_warn=new_w, more=[x['key'] for x in pa.get('more') or []],
                                gone=[x['key'] for x in pa.get('gone') or []], only=len(only), only_unnamed=only_unnamed,
                                only_keys=[x['key'] for x in only])
            for f in g_unexpl:
                A['fail'].append('logdiff gate FAIL: %s' % f)
            for k in new_ec:
                A['fail'].append('logdiff NEW error/critical key: %s' % k[:200])
            for k in new_w:
                A['note'].append('logdiff NEW warning key: %s' % k[:200])
            for k in A['logdiff']['more']:
                A['note'].append('logdiff MORE: %s' % k[:200])
            for k in A['logdiff']['gone']:
                A['note'].append('logdiff GONE: %s' % k[:200])
            for k in only_unnamed:
                A['note'].append('logdiff ONLY key that no rule names: %s' % k[:200])
        elif ld_data is not None and arm != ref:
            A['note'].append('arm missing from logdiff data.json')
        for R in rr:
            A['fail'] += ['%s: %s' % (R['name'], x) for x in R['fail']]
            A['note'] += ['%s: %s' % (R['name'], x) for x in R['note']]
        A['verdict'] = 'FAIL' if A['fail'] else ('NOTE' if A['note'] else 'PASS')
        arm_data[arm] = A

    # ---- report
    o = []
    w = o.append
    w('W6 logdiff kit (Agent 6, task #16): %s' % mdir)
    w('expect %s (reference %s); matrix.json %s%s' % (os.path.relpath(os.path.abspath(a.expect), ROOT), ref,
                                                     os.path.relpath(os.path.abspath(mj_path), ROOT),
                                                     ' (ERROR %s)' % mj['_error'] if mj.get('_error') else ''))
    w('runs %d in %d arms: %s' % (len(runs), len(arms), '; '.join('%s=%d' % (k, len(arms[k])) for k in order if k in arms)))
    absent = sorted(set(rules) - set(x[5:] if x.startswith('cold-') else x for x in arms))
    if absent:
        w('arms in the expect file with no run here: %s' % ', '.join(absent))
    unruled = sorted(x for x in arms if (x[5:] if x.startswith('cold-') else x) not in rules)
    if unruled:
        w('arms here with no rules in the expect file (NOTE): %s' % ', '.join(unruled))
    if ref not in arms:
        w('WARNING: no runs of the reference arm %s; the logdiff has no base' % ref)
    w('')
    w('Per arm. stuck = STUCK-LOCK episodes (sites; IN = in the measured window); recov/unh/pfail = Recovered stale'
      ' protection / Unhandled write fault / Protect failed lines per run; W/E/C = warning/error/critical lines per'
      ' run; slow = slow runs/runs, mean slow_pct, mean onset s; logdiff vs %s = gate FAIL findings/NEW/MORE/GONE/'
      'ONLY keys' % ref)
    w('  %-10s %-4s %-7s %-22s %-5s %-10s %-10s %-10s %-26s %-22s %s' % (
        'arm', 'runs', 'verdict', 'stuck', 'dumps', 'recov', 'unh', 'pfail', 'W/E/C', 'slow', 'logdiff F/N/M/G/O'))
    any_fail = False
    for arm in order:
        A = arm_data.get(arm)
        if A is None:
            continue
        any_fail = any_fail or A['verdict'] == 'FAIL'
        st = '%d %s%s' % (A['stuck'], ','.join('%s=%d' % kv for kv in sorted(A['stuck_sites'].items())) or '',
                          (' IN=%d' % A['stuck_in_window']) if A['stuck_in_window'] else '')
        s = A['slow']
        sl = '%d/%d %s%% %ss' % (s['slow_runs'], s['runs'], fmt(s['mean_slow_pct']), fmt(s['mean_onset_s']))
        ld = A.get('logdiff')
        lds = ('%d/%d/%d/%d/%d' % (ld['fail'], ld['new'], len(ld['more']), len(ld['gone']), ld['only'])) if ld else \
            ('(reference)' if arm == ref else '-')
        w('  %-10s %-4d %-7s %-22s %-5d %-10s %-10s %-10s %-26s %-22s %s' % (
            arm, len(A['runs']), A['verdict'], st, A['dumps'], A['recovered'], A['unhandled'], A['protect_failed'],
            ' '.join(A['levels']), sl, lds))
    w('')
    w('Per run. exit = run.json exit code; close = WM_CLOSE posted/clean; seq = log ends with the clean-exit lines;'
      ' stuck = episodes; slow = onset s / slow_pct / span s (sys.csv rows); nogrowth = perf.csv max no-growth s in'
      ' the window; free = GB at start')
    w('  %-18s %-8s %-7s %-6s %-5s %-9s %-4s %-9s %-5s %-4s %-20s %-8s %-5s %s' % (
        'run', 'arm', 'verdict', 'status', 'exit', 'close', 'seq', 'W/E/C', 'stuck', 'dmp', 'slow', 'nogrowth', 'free',
        'lines'))
    for name in sorted(runs):
        R = runs[name]
        F, L, s = R['facts'] or {}, R['log'], R['slow']
        sl = ('%s/%.0f/%.0f (%d)' % (fmt(s['onset_s'], '%.0f'), s['slow_pct'], s['span_s'], s['rows'])) if s else '-'
        w('  %-18s %-8s %-7s %-6s %-5s %-9s %-4s %-9s %-5d %-4d %-20s %-8s %-5s %d' % (
            name, R['arm'], R['verdict'], F.get('status'), fmt(F.get('exit_code')),
            '%s/%s' % (F.get('wm_close'), F.get('clean')), 'ok' if L['exit_seq'] else 'NO',
            '%d/%d/%d' % (L['levels']['warning'], L['levels']['error'], L['levels']['critical']), len(L['episodes']),
            len(R['dumps']), sl, fmt(F.get('nogrowth')), fmt(F.get('free_gb')), L['lines']))
    w('')
    eps = [(name, e) for name in sorted(runs) for e in runs[name]['log']['episodes']]
    w('STUCK-LOCK episodes: %d (H1 = owner parked in sub_83FAF180, the L1 fence-wait poll; finding 10)' % len(eps))
    for name, e in eps:
        w('  %s %s cs %s after %ss | owner tid %s lr=%s %s (%s) callers %s | waiter lr=%s %s | PM4 %s | stall from %s,'
          ' window %s | dump %s'
          % (name, e['ts'], e['cs'], fmt(e['after_s']), e['owner_tid'], e['owner_lr'], e['site'],
             e['owner_func'] or 'no map', '<-'.join((e['owner_callers'] or [])[:4]) or '-', e['waiter_lr'],
             e['waiter_func'] or '', e['pm4'], e['stall_start'], e['window'], e['dump']))
    w('')
    w('Reasons, FAIL first (per arm: its runs, then its logdiff findings)')
    nr = 0
    for kind in ('fail', 'note'):
        for arm in order:
            A = arm_data.get(arm)
            for x in (A or {}).get(kind, []):
                w('  %s %-8s %s' % (kind.upper(), arm, x))
                nr += 1
    if not nr:
        w('  none')
    w('')
    w('Counts per arm (lines containing each expect count text; one number per run, run-dir order)')
    for t in count_pats:
        row = '; '.join('%s=%s' % (arm, arm_data[arm]['counts'][t]) for arm in order if arm in arm_data)
        w('  %-60s %s' % (t[:60], row))
    w('')
    w('ONLY keys per arm vs %s (any level, not Toypad; in no %s run), from w4b_logdiff' % (ref, ref))
    for arm in order:
        ld = (arm_data.get(arm) or {}).get('logdiff')
        if ld:
            w('  %s: %d%s' % (arm, ld['only'], (' (not named by a rule: %d)' % len(ld['only_unnamed'])) if ld['only_unnamed'] else ''))
            for k in ld['only_keys'][:a.top]:
                w('    %s' % k[:220])
    w('')
    for k, v in tools.items():
        w('%s: exit %s in %.1f s -> %s (log %s)' % (k, v['rc'], v['s'], os.path.relpath(v['out'], ROOT),
                                                   os.path.relpath(v['log'], ROOT)))
    if a.skip_logdiff:
        w('logdiff tools skipped (--skip-logdiff)')
    w('verdict: %s; runtime %.1f s; output %s' % ('FAIL' if any_fail else 'no FAIL', time.time() - t_start,
                                                 os.path.relpath(out, ROOT)))
    txt = '\n'.join(o)
    with open(os.path.join(out, 'w6-summary.txt'), 'w', encoding='utf-8') as fh:
        fh.write(txt + '\n')
    data = dict(matrix=mdir, expect=os.path.abspath(a.expect), matrix_json=os.path.abspath(mj_path), reference=ref,
                generated=datetime.datetime.now().isoformat(timespec='seconds'), tools=tools, arms=arm_data,
                runs={n: dict(arm=R['arm'], verdict=R['verdict'], fail=R['fail'], note=R['note'], slow=R['slow'],
                              dumps=R['dumps'], facts=R['facts'],
                              log=dict(files=R['log']['files'], lines=R['log']['lines'],
                                       levels=dict(R['log']['levels']), counts=dict(R['log']['cnt']),
                                       episodes=R['log']['episodes'], exit_seq=R['log']['exit_seq'],
                                       other_err=R['log']['other_err'], first_ts=R['log']['first_ts'],
                                       last_ts=R['log']['last_ts']))
                      for n, R in runs.items()})
    with open(os.path.join(out, 'w6-data.json'), 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=1, default=str)
    print(txt)
    return 1 if any_fail else 0


if __name__ == '__main__':
    sys.exit(main())
