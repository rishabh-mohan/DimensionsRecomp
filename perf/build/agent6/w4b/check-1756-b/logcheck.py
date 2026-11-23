#!/usr/bin/env python3
"""Checker B, task #13 (W5 game.log logdiff + perf read-out): game.log part.

Covers B1 (base vs s0 exact-text diff + gate_logdiff for the 9 pairs x 2 directions), B2 (log greps for the
S4a/timer lines), B3 (cold vs warm base: line sets and boot timing), B4 (slow runs vs arm-mates), B5 (clock step).
Independent code, stdlib only.

Inputs (read-only): build/agent8/matrix/20261122-1756/runs/<run>/{game.log,run.json,sys.csv,summary.txt};
bench/agent8/run/gate_logdiff.py (imported read-only: sys.dont_write_bytecode is set and the script is run with
python -B, so no __pycache__ is written there). Output: logcheck-out.txt next to this file.

Normalisation levels for the line-set comparison (each game.log line -> one key; multiset of keys per run):
  R (raw):   '[level] [category] message'; the '[YYYY-MM-DD HH:MM:SS.mmm]' timestamp and the '[tNNN]' thread id are
             dropped; header-less continuation lines are kept as '[raw] text'. Nothing else is changed.
  E (exact): R, plus the run directory in paths ('runs\\NNNN-name') -> 'runs/<run>', plus Toypad payload lines cut
             to their frame header (Write: 'Toypad[Write] 0B 16 55 <len> <cmd>'; Read: 'Toypad[Read] 0B <x> 55 <len>';
             'Toypad[Read ]' -> 'Toypad[Read]'): the rest of a Toypad frame is a message counter plus random
             challenge/response bytes.
  N (normalised): E, plus every 0x-hex literal (handles, addresses) -> '0x#'.
"""
import sys
sys.dont_write_bytecode = True
import calendar
import csv
import datetime
import importlib.util
import json
import os
import re
import statistics
import traceback
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
RUNS_DIR = os.path.join(ROOT, 'build', 'agent8', 'matrix', '20261122-1756', 'runs')
GATE = os.path.join(ROOT, 'bench', 'agent8', 'run', 'gate_logdiff.py')
OUT = os.path.join(HERE, 'logcheck-out.txt')

RUNS = ['1756-cold-base', '1757-base-r1', '1800-s0-r1', '1802-d11-r1', '1804-d11t-r1', '1806-d11p-r1',
        '1808-s0-r2', '1810-d11-r2', '1813-d11t-r2', '1815-d11p-r2', '1817-base-r2', '1819-d11-r3',
        '1821-d11t-r3', '1823-d11p-r3', '1825-base-r3', '1827-s0-r3']
SLOW = ('1808-s0-r2', '1817-base-r2', '1821-d11t-r3')
COLD = '1756-cold-base'
BASE = ['1757-base-r1', '1817-base-r2', '1825-base-r3']
S0 = ['1800-s0-r1', '1808-s0-r2', '1827-s0-r3']
ARMS = ['base', 's0', 'd11', 'd11t', 'd11p']

HDR = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\] \[([a-z]+)\] \[([^\]]*)\] (?:\[t(\d+)\] )?(.*)$')
TOY = re.compile(r'^Toypad\[(Write|Read ?)\]((?: [0-9A-Fa-f]{2})+) *$')
RUNPATH = re.compile(r'runs[\\/]\d{4}-[A-Za-z0-9-]+')
HEX = re.compile(r'0x[0-9A-Fa-f]+')
STALL = re.compile(r'(?i)\b(stall\w*|stuck|hang|hangs|hung|timeout\w*|timed out|deadlock\w*|not responding|'
                   r'watchdog|hitch\w*|slow\w*|freez\w*)\b')

O = []


def w(s=''):
    O.append(s)


def arm_of(r):
    tag = r.split('-', 1)[1]
    return 'cold' if tag == 'cold-base' else tag.rsplit('-', 1)[0]


def short(r):
    return r.split('-', 1)[1]


def arm_runs(a):
    return [r for r in RUNS if arm_of(r) == a]


def naive_secs(s):
    dt = datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')
    return calendar.timegm(dt.timetuple()) + dt.microsecond / 1e6


def read_log(r):
    with open(os.path.join(RUNS_DIR, r, 'game.log'), 'rb') as fh:
        text = fh.read().decode('utf-8', errors='replace')
    lines = []
    for i, ln in enumerate(text.split('\n')):
        ln = ln.rstrip('\r')
        if not ln.strip():
            continue
        m = HDR.match(ln)
        if m:
            d = dict(n=i + 1, ts=m.group(1), lvl=m.group(2), cat=m.group(3), tid=m.group(4), msg=m.group(5))
        else:
            d = dict(n=i + 1, ts=None, lvl=None, cat=None, tid=None, msg=ln)
        t = TOY.match(d['msg']) if d['ts'] else None
        d['toy'] = (t.group(1).strip(), t.group(2).split()) if t else None
        lines.append(d)
    return lines


def load_json(r, name='run.json'):
    with open(os.path.join(RUNS_DIR, r, name), 'r', encoding='utf-8-sig') as fh:
        return json.load(fh)


def key(d, level):
    msg = d['msg']
    if level >= 1:
        msg = RUNPATH.sub('runs/<run>', msg)
        if d['toy']:
            kind, b = d['toy']
            msg = 'Toypad[%s] %s' % (kind, ' '.join(b[:5 if kind == 'Write' else 4]))
    if level >= 2:
        msg = HEX.sub('0x#', msg)
    if d['ts'] is None:
        return '[raw] ' + msg
    return '[%s] [%s] %s' % (d['lvl'], d['cat'], msg)


def fmtv(vals):
    return ' '.join('%2d' % v for v in vals)


def group_report(title, runs, level, logs, show=True, skip_class=()):
    cs = {r: Counter(key(d, level) for d in logs[r]) for r in runs}
    union = set()
    for c in cs.values():
        union |= set(c)
    common = [k for k in union if all(cs[r][k] > 0 for r in runs)]
    flagged = []
    for k in sorted(union):
        vals = [cs[r][k] for r in runs]
        if min(vals) == 0 or len(set(vals)) > 1:
            flagged.append((k, vals))
    w('%s [level %s] runs: %s' % (title, 'REN'[level], ' '.join(short(r) for r in runs)))
    w('  lines per run: %s' % ' '.join(str(sum(cs[r].values())) for r in runs))
    w('  distinct keys: union %d, in all runs %d, flagged (missing in a run or unequal counts) %d'
      % (len(union), len(common), len(flagged)))
    if show:
        for k, vals in flagged:
            if classify(k) in skip_class:
                continue
            w('    %s  %s' % (fmtv(vals), k[:170]))
    return cs, flagged


def classify(k):
    if 'Toypad[Write]' in k or 'Toypad[Read' in k:
        return 'toypad'
    if RUNPATH.search(k):
        return 'run-path'
    if 'IoDismountVolumeByFileHandle' in k:
        return 'iodismount'
    return 'other'


def load_gate():
    spec = importlib.util.spec_from_file_location('gate_logdiff_checkerb', GATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GATE_CACHE = {}


def gate_pairs(gl, pairs, label):
    rx = re.compile(gl.UNIMPL_DEFAULT)

    def sc(r):
        if r not in GATE_CACHE:
            GATE_CACHE[r] = gl.scan(os.path.join(RUNS_DIR, r, 'game.log'), rx)
        return GATE_CACHE[r]

    w('%s: gate_logdiff.compare(scan(A), scan(B), 25) per ordered pair; FAIL = len(findings), NEW = new_in_b_total, '
      'MORE = count_changes_total, GONE = gone_in_b_total' % label)
    tot = dict(FAIL=0, NEW=0, MORE=0, GONE=0, notes=0)
    for a, b in pairs:
        f, n, m, d = gl.compare(sc(a), sc(b), 25)
        sa, sb = sc(a), sc(b)
        w('  A %-14s B %-14s FAIL %d NEW %d MORE %d GONE %d notes %d | warn kinds/lines A %d/%d B %d/%d | unimpl A %d B %d'
          ' | levels B %s' % (a, b, len(f), d['new_in_b_total'], d['count_changes_total'], d['gone_in_b_total'], len(n),
                              len(sa['warn']), sum(sa['warn'].values()), len(sb['warn']), sum(sb['warn'].values()),
                              sa['unimpl'], sb['unimpl'], dict(sorted(sb['levels'].items()))))
        for x in f:
            w('     FAIL: %s' % x[:200])
        for x in d['new_in_b']:
            w('     NEW: %d %s' % (x['count'], x['msg'][:150]))
        for x in d['gone_in_b']:
            w('     GONE: %d %s' % (x['count'], x['msg'][:150]))
        for x in d['count_changes']:
            w('     MORE: A %d B %d %s' % (x['a'], x['b'], x['msg'][:150]))
        for x in n:
            w('     note: %s' % x[:200])
        tot['FAIL'] += len(f)
        tot['NEW'] += d['new_in_b_total']
        tot['MORE'] += d['count_changes_total']
        tot['GONE'] += d['gone_in_b_total']
        tot['notes'] += len(n)
    w('  totals over %d ordered pairs: %s' % (len(pairs), tot))
    return tot


class Run:
    def __init__(self, r):
        self.r = r
        self.lines = read_log(r)
        self.j = load_json(r)
        j = self.j
        self.f = j['qpc_frequency']
        self.ps = j.get('process_start_mark') or {}
        self.ms = j['measure_start']
        self.me = j['measure_end']
        anchor = self.ps if self.ps.get('wall') else self.ms
        self.off = anchor['epoch_s'] - naive_secs(anchor['wall'])
        self.off_ms = self.ms['epoch_s'] - naive_secs(self.ms['wall'])
        self.off_me = self.me['epoch_s'] - naive_secs(self.me['wall'])
        self.hdr = [d for d in self.lines if d['ts']]

    def ep(self, d):
        return naive_secs(d['ts']) + self.off

    def first(self, pat, last=False):
        hits = [d for d in self.hdr if pat in d['msg']]
        if not hits:
            return None
        return hits[-1] if last else hits[0]


MILESTONES = [
    ('d3d12', 'Direct3D 12 device and OS features', False),
    ('font', 'UI font loaded', False),
    ('runtime', 'Startup: constructing the runtime', False),
    ('arena', 'Reserving the guest memory arena', False),
    ('functab', 'Function table initialized', False),
    ('xexpatch', 'XEX patch applied', False),
    ('launch', 'Startup: launching the module', False),
    ('shaderst', 'Initializing shader storage', False),
    ('setintr', 'SetInterruptCallback', False),
    ('skipcut', 'Skip cutscenes', False),
    ('audio', 'audio endpoint', False),
    ('hdr_fail', 'INSTALL0_2.HDR', False),
    ('toyW1', 'Toypad[Write]', False),
    ('xambg', 'XamBackgroundDownloadSetMode', False),
    ('dat_fail', 'INSTALL0_2.DAT', False),
    ('dat_last', 'INSTALL0_18.DAT', True),
    ('closing', 'Window closing', False),
    ('execdone', 'Execution complete', False),
    ('termin', 'Title terminated', False),
]


def med(xs):
    return statistics.median(xs) if xs else float('nan')


def section_inventory(R):
    w('== 0. Inventory')
    have = sorted(x for x in os.listdir(RUNS_DIR) if os.path.isdir(os.path.join(RUNS_DIR, x)))
    w('run dirs under runs/: %d; equal to the 16 expected: %s' % (len(have), have == sorted(RUNS)))
    if have != sorted(RUNS):
        w('  dirs: %s' % have)
    w('%-15s %-5s %-12s %-30s %5s %4s %4s %5s %5s %4s %4s %4s %s' % (
        'run', 'arm', 'bin', 'env / extra cvars', 'lines', 'hdr', 'raw', 'notid', 'info', 'warn', 'err', 'crit',
        'other levels'))
    configs = {}
    for r in RUNS:
        x = R[r]
        j = x.j
        lv = Counter(d['lvl'] for d in x.hdr)
        notid = sum(1 for d in x.hdr if d['tid'] is None)
        env = ','.join('%s=%s' % kv for kv in sorted((j.get('env_set') or {}).items()))
        cv = [c for c in (j.get('params', {}).get('cvar') or []) if c != 'framerate_limit=0']
        configs.setdefault(arm_of(r), set()).add((os.path.basename(j.get('bin_dir', '')), env, tuple(cv),
                                                  j.get('params', {}).get('seconds'),
                                                  j.get('params', {}).get('warmup_s')))
        other = {k: v for k, v in lv.items() if k not in ('info', 'warning', 'error', 'critical')}
        w('%-15s %-5s %-12s %-30s %5d %4d %4d %5d %5d %4d %4d %4d %s' % (
            r, arm_of(r), os.path.basename(j.get('bin_dir', '')), (env + (' +%d cvars' % len(cv) if cv else ''))[:30],
            len(x.lines), len(x.hdr), len(x.lines) - len(x.hdr), notid, lv['info'], lv['warning'], lv['error'],
            lv['critical'], other or '-'))
    w('configurations per arm (bin, env, extra cvars, seconds, warmup_s):')
    for a in ['cold'] + ARMS:
        for c in sorted(configs.get(a, ())):
            w('  %-5s %s' % (a, c))
    w('raw (header-less) lines, run 1757-base-r1: %s' % [d['msg'][:60] for d in R['1757-base-r1'].lines if not d['ts']])
    w()


def section_b1(R, gl):
    w('== B1. base (S3d: 1757-base-r1, 1817-base-r2, 1825-base-r3) vs s0 (S4a: 1800-s0-r1, 1808-s0-r2, 1827-s0-r3)')
    logs = {r: R[r].lines for r in RUNS}
    runs = BASE + S0
    for level in (0, 1, 2):
        cs, flagged = group_report('B1', runs, level, logs, show=(level > 0))
        if level == 0:
            cls = Counter(classify(k) for k, _ in flagged)
            w('  level R flagged keys by class: %s' % dict(sorted(cls.items())))
            for k, vals in flagged:
                if classify(k) != 'toypad':
                    w('    %s  %s' % (fmtv(vals), k[:170]))
            tp = [(k, v) for k, v in flagged if classify(k) == 'toypad']
            w('  level R toypad keys flagged: %d (each run has its own random challenge/response payloads); '
              'toypad payload keys common to all 6 runs: %d' % (
                  len(tp), len([k for k in set().union(*[set(c) for c in cs.values()])
                                if classify(k) == 'toypad' and all(cs[r][k] for r in runs)])))
        sep = [(k, v) for k, v in flagged if max(v[:3]) < min(v[3:]) or max(v[3:]) < min(v[:3])]
        w('  arm-separating keys (base count range disjoint from the s0 range): %d' % len(sep))
        for k, v in sep:
            w('    %s  %s' % (fmtv(v), k[:170]))
        notall = [(k, v) for k, v in flagged if classify(k) not in ('toypad', 'iodismount', 'run-path')]
        w('  flagged keys other than Toypad / IoDismount / run-path: %d' % len(notall))
    w('IoDismountVolumeByFileHandle variants per run (all 16):')
    for r in RUNS:
        c = Counter(re.search(r'IoDismountVolumeByFileHandle\((0x[0-9a-fA-F]+)\)', d['msg']).group(1)
                    for d in R[r].hdr if 'IoDismountVolumeByFileHandle(' in d['msg'])
        w('  %-15s %s' % (r, dict(c)))
    w('[warning] / [error] / [critical] line counts per log (all 16):')
    for r in RUNS:
        lv = Counter(d['lvl'] for d in R[r].hdr)
        w('  %-15s warning %d error %d critical %d' % (r, lv['warning'], lv['error'], lv['critical']))
    pairs = [(a, b) for a in BASE for b in S0] + [(b, a) for a in BASE for b in S0]
    tot = gate_pairs(gl, pairs, 'B1 gate')
    w('B1 gate verdict: FAIL/NEW/MORE/GONE all 0 in every pair: %s' % (
        all(v == 0 for k, v in tot.items() if k != 'notes')))
    w()


B2PATS = [('HostTimerRes', 'Host timer resolution set to'), ('CouldNotSet', 'Could not set the host timer resolution'),
          ('OptOutFail', 'Timer resolution power throttling'), ('TQprecise', 'TimerQueue: precise wait'),
          ('TimerQueue', 'TimerQueue'), ('S4hash', 'S4 upload hash'), ('C1keep', 'C1 keep-watch'),
          ('envBlock', 'REX_TIMER_WAIT_BLOCKING'), ('cvarPrec', 'timer_queue_precise_wait'),
          ('shaderMiss', 'shader_miss'), ('NativeGPU', 'Native GPU'), ('AOTidx', 'missing from AOT index')]


def section_b2(R):
    w('== B2. log greps for the S4a / timer lines (substring counts per game.log)')
    w('%-15s %-5s ' % ('run', 'arm') + ' '.join('%-12s' % lab for lab, _ in B2PATS))
    ex = {}
    for r in RUNS:
        row = []
        for lab, pat in B2PATS:
            hits = [d for d in R[r].lines if pat in d['msg']]
            row.append(len(hits))
            if hits and lab not in ex:
                ex[lab] = '%s: %s' % (r, key(hits[0], 0)[:150])
        w('%-15s %-5s ' % (r, arm_of(r)) + ' '.join('%-12d' % v for v in row))
    w('first example per pattern: %s' % (ex or '-'))
    for lab, pat in B2PATS[:4]:
        w('  %-13s base/cold/s0 runs with a hit: %s' % (
            lab, [r for r in RUNS if arm_of(r) in ('base', 'cold', 's0') and any(pat in d['msg'] for d in R[r].lines)]
            or 'none'))
    w()


def section_b3(R, gl):
    w('== B3. 1756-cold-base vs the 3 warm base runs')
    logs = {r: R[r].lines for r in RUNS}
    runs = [COLD] + BASE
    for level in (1, 2):
        group_report('B3', runs, level, logs)
    gate_pairs(gl, [(b, COLD) for b in BASE] + [(COLD, b) for b in BASE], 'B3 gate')
    labels = ['first'] + [m[0] for m in MILESTONES]
    tabs = {}
    for r in RUNS:
        x = R[r]
        t0 = x.ep(x.hdr[0])
        ps = x.ps.get('epoch_s')
        rel0, relps = {}, {}
        rel0['first'] = 0.0
        relps['first'] = t0 - ps if ps is not None else None
        for lab, pat, last in MILESTONES:
            d = x.first(pat, last)
            rel0[lab] = (x.ep(d) - t0) if d else None
            relps[lab] = (x.ep(d) - ps) if (d and ps is not None) else None
        tabs[r] = (rel0, relps)
    for which, name in ((1, 'seconds after process_start_mark (run.json; game.log time -> epoch via the run.json wall/epoch '
                             'offset)'), (0, 'seconds after the first game.log line')):
        w('milestones, %s:' % name)
        w('  %-9s ' % 'line' + ' '.join('%8s' % short(r)[:8] for r in RUNS))
        for lab in labels:
            vals = [tabs[r][which][lab] for r in RUNS]
            w('  %-9s ' % lab + ' '.join('%8s' % ('-' if v is None else '%.3f' % v) for v in vals))
        w('  cold vs warm base (median, min..max of base-r1/r2/r3):')
        for lab in labels:
            wv = [tabs[r][which][lab] for r in BASE if tabs[r][which][lab] is not None]
            cv = tabs[COLD][which][lab]
            if not wv or cv is None:
                continue
            w('    %-9s cold %8.3f  warm %8.3f (%.3f..%.3f)  cold-warm_median %+8.3f' % (
                lab, cv, med(wv), min(wv), max(wv), cv - med(wv)))
    w('run.json boot/timing fields:')
    fields = []
    for r in RUNS:
        j = R[r].j
        x = R[r]
        ps = x.ps
        f = x.f
        fields.append([
            ('start', j.get('start')), ('end', j.get('end')),
            ('boot_s', j.get('boot_s')), ('first_frame_signal_s', j.get('first_frame_signal_s')),
            ('warmup_start_s', j.get('warmup_start_s')),
            ('ff_epoch-ps_epoch', round(j['ff_signal_epoch_s'] - ps['epoch_s'], 3) if j.get('ff_signal_epoch_s') and ps.get('epoch_s') else None),
            ('ms_qpc-ps_qpc_s', round((x.ms['qpc'] - ps['qpc']) / f, 3) if ps.get('qpc') else None),
            ('window_qpc_s', round((x.me['qpc'] - x.ms['qpc']) / f, 3)),
            ('window_wall_s', j.get('window_wall_s')),
            ('params.warmup_s', j.get('params', {}).get('warmup_s')), ('params.seconds', j.get('params', {}).get('seconds')),
            ('ff_to_window_s', j.get('ff_to_window_s')), ('close.exit_wait_s', (j.get('close') or {}).get('exit_wait_s')),
            ('log_lines', j.get('log_lines')), ('free_ram_gb_at_start', j.get('free_ram_gb_at_start')),
            ('light.install_dat_fail', (j.get('light') or {}).get('install_dat_fail')),
        ])
    for i, (name, _) in enumerate(fields[0]):
        w('  %-22s ' % name + ' '.join('%s=%s' % (short(r), fields[k][i][1]) for k, r in enumerate(RUNS)
                                       if (i > 1 or True)))
    w()


def toy_info(x):
    writes = [d for d in x.hdr if d['toy'] and d['toy'][0] == 'Write']
    reads = [d for d in x.hdr if d['toy'] and d['toy'][0] == 'Read']
    other = [d for d in x.hdr if 'Toypad' in d['msg'] and not d['toy']]
    seq = [d['toy'][1][4] for d in writes]
    t0 = x.ep(writes[0]) if writes else None
    b1 = [x.ep(d) - t0 for d in writes if d['toy'][1][4] == 'B1']
    iv = [b - a for a, b in zip(b1, b1[1:])]
    cl = x.first('Window closing')
    close = x.ep(cl) - t0 if (cl and t0 is not None) else None
    return dict(W=len(writes), R=len(reads), other=len(other), seq=seq, b1=b1, iv=iv, close=close, t0=t0,
                cmds=Counter(seq))


def section_b4(R):
    w('== B4. slow runs (1808-s0-r2, 1817-base-r2, 1821-d11t-r3) vs the other runs of their arm')
    w('%-15s %-5s %-4s %5s %4s %4s %4s %5s %4s %4s %5s %-34s %-28s %-22s %6s' % (
        'run', 'arm', 'slow', 'lines', 'warn', 'err', 'crit', 'stall', 'toyW', 'toyR', 'toyO', 'write cmd sequence',
        'B1 s after 1st Toypad write', 'B1 intervals s', 'close'))
    T = {}
    for r in RUNS:
        x = R[r]
        lv = Counter(d['lvl'] for d in x.hdr)
        st = [d for d in x.lines if STALL.search(d['msg'])]
        t = toy_info(x)
        T[r] = t
        w('%-15s %-5s %-4s %5d %4d %4d %4d %5d %4d %4d %5d %-34s %-28s %-22s %6s' % (
            r, arm_of(r), 'SLOW' if r in SLOW else '', len(x.lines), lv['warning'], lv['error'], lv['critical'], len(st),
            t['W'], t['R'], t['other'], ' '.join(t['seq'])[:34], '[' + ', '.join('%.1f' % v for v in t['b1']) + ']',
            '[' + ', '.join('%.1f' % v for v in t['iv']) + ']', '%.1f' % t['close'] if t['close'] is not None else '-'))
        for d in st[:3]:
            w('      stall-word hit: %s' % key(d, 0)[:160])
    w('Toypad write cmd counts: ' + '; '.join('%s %s' % (short(r), dict(sorted(T[r]['cmds'].items()))) for r in RUNS))
    w('runs with 12 writes / 12 reads: %s' % [r for r in RUNS if T[r]['W'] == 12 and T[r]['R'] == 12])
    w('runs with 8 writes / 8 reads: %s' % [r for r in RUNS if T[r]['W'] == 8 and T[r]['R'] == 8])
    w('per-arm line differences (level E; runs of one arm; flagged = missing in a run or unequal counts):')
    logs = {r: R[r].lines for r in RUNS}
    for a in ARMS:
        group_report('  arm %s' % a, arm_runs(a), 1, logs)
    w('largest timestamp gaps inside the measure window [measure_start.epoch_s, measure_end.epoch_s] '
      '(game.log time -> epoch; the window edges count as points):')
    for r in RUNS:
        x = R[r]
        ms, me = x.ms['epoch_s'], x.me['epoch_s']
        inw = [d for d in x.hdr if ms <= x.ep(d) <= me]
        pts = [(ms, 'measure_start')] + [(x.ep(d), lab(d)) for d in inw] + [(me, 'measure_end')]
        gaps = sorted(((pts[i + 1][0] - pts[i][0], pts[i][1], pts[i + 1][1], pts[i][0] - ms) for i in range(len(pts) - 1)),
                      reverse=True)
        allg = sorted(((x.ep(x.hdr[i + 1]) - x.ep(x.hdr[i]), lab(x.hdr[i]), lab(x.hdr[i + 1])) for i in range(len(x.hdr) - 1)),
                      reverse=True)
        w('  %-15s %-4s window %.3f s (epoch) / %.3f s (qpc), %2d lines in window; top gaps: %s | log-wide max gap %.2f s '
          '(%s -> %s)' % (
              r, 'SLOW' if r in SLOW else '', me - ms, (x.me['qpc'] - x.ms['qpc']) / x.f, len(inw),
              '; '.join('%.2f s at +%.1f (%s -> %s)' % (g, t, a, b) for g, a, b, t in gaps[:3]),
              allg[0][0], allg[0][1], allg[0][2]))
        w('      in-window lines (s after measure_start): %s' % ', '.join('%.2f %s' % (x.ep(d) - ms, lab(d)) for d in inw))
    w('summary.txt / run.json health per run:')
    for r in RUNS:
        x = R[r]
        j = x.j
        try:
            with open(os.path.join(RUNS_DIR, r, 'summary.txt'), 'r', encoding='utf-8-sig', errors='replace') as fh:
                sm = fh.read().splitlines()
        except OSError:
            sm = []
        hits = [s for s in sm if STALL.search(s) or 'STUCK' in s.upper()]
        cl = j.get('close') or {}
        w('  %-15s status %s problems %s valid_timing %s perf_csv_stalled %s max_no_growth_s %s not_responding %s/%s '
          'werfault %s dialogs %d exit %s clean %s killed %s flags %s excluded %s ticks_skipped_window %s | summary.txt '
          'stall/STUCK lines %d%s' % (
              r, j.get('status'), j.get('problems'), j.get('valid_timing'), j.get('perf_csv_stalled'),
              j.get('perf_csv_max_no_growth_window_s'), j.get('not_responding_samples'),
              j.get('not_responding_window_samples'), j.get('werfault_seen'), len(j.get('dialogs') or []),
              j.get('exit_code'), cl.get('clean'), cl.get('killed'), j.get('flags'), j.get('excluded'),
              j.get('ticks_skipped_window'), len(hits), (': ' + ' | '.join(h.strip()[:90] for h in hits[:3])) if hits else ''))
    w()
    return T


def lab(d):
    if d['toy']:
        kind, b = d['toy']
        return ('W' + b[4]) if kind == 'Write' else 'R'
    return d['msg'][:28]


def section_b5(R):
    w('== B5. clock step = (measure_end.epoch_s - measure_start.epoch_s) - (measure_end.qpc - measure_start.qpc) / '
      'qpc_frequency')
    w('%-15s %10s %10s %9s %9s %9s %9s %9s %9s %s' % (
        'run', 'qpc_win_s', 'epoch_win', 'step', 'step_ps_ms', 'off_ok', 'cl-me_ep', 'cl-me_qpc', 'diff',
        'sys.csv: max |d(epoch)-d(t_s)| (row, walls), total drift, t0'))
    for r in RUNS:
        x = R[r]
        q = (x.me['qpc'] - x.ms['qpc']) / x.f
        e = x.me['epoch_s'] - x.ms['epoch_s']
        step = e - q
        sps = ((x.ms['epoch_s'] - x.ps['epoch_s']) - (x.ms['qpc'] - x.ps['qpc']) / x.f) if x.ps.get('qpc') else None
        offok = abs(x.off - x.off_ms) < 0.002 and abs(x.off - x.off_me) < 0.002
        cl = x.first('Window closing')
        c_ep = x.ep(cl) - x.me['epoch_s'] if cl else None
        pred_me = x.ps['epoch_s'] + (x.me['qpc'] - x.ps['qpc']) / x.f if x.ps.get('qpc') else None
        c_q = x.ep(cl) - pred_me if (cl and pred_me) else None
        rows, best, tot, t0 = sys_jumps(r)
        w('%-15s %10.4f %10.3f %+9.4f %+9.4f %9s %9.3f %9.3f %+9.3f  %+.3f s at row %d (%s -> %s, t_s %s -> %s); total %+.3f; '
          'epoch0-t0 - ps_epoch %+.3f' % (
              r, q, e, step, sps if sps is not None else float('nan'), offok, c_ep, c_q, c_q - c_ep, best[0], best[1],
              rows[best[1] - 1]['wall'], rows[best[1]]['wall'], rows[best[1] - 1]['t_s'], rows[best[1]]['t_s'], tot,
              t0 - x.ps['epoch_s']))
    x = R['1757-base-r1']
    rows, best, tot, t0 = sys_jumps('1757-base-r1')
    eb, ea = float(rows[best[1] - 1]['epoch_s']), float(rows[best[1]]['epoch_s'])
    tb, ta = float(rows[best[1] - 1]['t_s']), float(rows[best[1]]['t_s'])
    pre = [d for d in x.hdr if x.ep(d) <= eb]
    post = [d for d in x.hdr if x.ep(d) >= ea]
    mid = [d for d in x.hdr if eb < x.ep(d) < ea]
    t_ms = (x.ms['qpc'] - x.ps['qpc']) / x.f
    t_me = (x.me['qpc'] - x.ps['qpc']) / x.f
    w('1757-base-r1 jump: sys.csv rows %d->%d: epoch %.3f -> %.3f (wall %s -> %s), t_s %.3f -> %.3f; measure window in '
      'qpc time after process start: %.3f .. %.3f s' % (best[1] - 1, best[1], eb, ea, rows[best[1] - 1]['wall'],
                                                        rows[best[1]]['wall'], tb, ta, t_ms, t_me))
    w('  last game.log line before the jump: %s %s' % (pre[-1]['ts'], key(pre[-1], 1)[:100]) if pre else '  none before')
    w('  game.log lines between the two sys.csv samples: %d' % len(mid))
    w('  first game.log line after the jump: %s %s' % (post[0]['ts'], key(post[0], 1)[:100]) if post else '  none after')
    w('  game.log lines after the jump: %d (%s)' % (len(post), ', '.join(key(d, 1)[:40] for d in post)))
    t = toy_info(x)
    w('  base-r1 close offset after the first Toypad write: %.3f s; other runs: %s' % (
        t['close'], ', '.join('%s %.1f' % (short(r), toy_info(R[r])['close']) for r in RUNS if r != '1757-base-r1')))
    spans = {r: R[r].ep(R[r].first('Window closing')) - R[r].ep(R[r].hdr[0]) for r in RUNS}
    w('  first line -> Window closing (log time): %s' % ', '.join('%s %.2f' % (short(r), spans[r]) for r in RUNS))
    w()


def sys_jumps(r):
    with open(os.path.join(RUNS_DIR, r, 'sys.csv'), 'r', newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))
    best = None
    for i in range(1, len(rows)):
        de = float(rows[i]['epoch_s']) - float(rows[i - 1]['epoch_s'])
        dt = float(rows[i]['t_s']) - float(rows[i - 1]['t_s'])
        d = de - dt
        if best is None or abs(d) > abs(best[0]):
            best = (d, i)
    tot = (float(rows[-1]['epoch_s']) - float(rows[0]['epoch_s'])) - (float(rows[-1]['t_s']) - float(rows[0]['t_s']))
    t0 = float(rows[0]['epoch_s']) - float(rows[0]['t_s'])
    return rows, best, tot, t0


def main():
    R = {r: Run(r) for r in RUNS}
    gl = load_gate()
    w('checker B logcheck.py: %s' % datetime.datetime.now().isoformat(timespec='seconds'))
    w('tz offsets (run.json epoch_s - wall as UTC): %s' % sorted(set(round(R[r].off, 3) for r in RUNS)))
    w()
    for fn in (section_inventory,):
        fn(R)
    section_b1(R, gl)
    section_b2(R)
    section_b3(R, gl)
    section_b4(R)
    section_b5(R)


if __name__ == '__main__':
    rc = 0
    try:
        main()
    except Exception:
        w('!!! EXCEPTION')
        w(traceback.format_exc())
        rc = 1
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(O) + '\n')
    print('logcheck rc %d, %d lines -> %s' % (rc, len(O), OUT))
    sys.exit(rc)
