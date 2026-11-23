#!/usr/bin/env python3
"""check-b-d3 (Agent 6 task #5, read-only checker, own code): independent exact-text game.log diff of arms B and d3
against the 4 warm d0 runs of build/agent8/matrix/20261122-1541/runs (W4b), plus crash evidence (run.json fields,
*.dmp, last 3 log lines, grep), the 'Host timer resolution set to' check and the Toypad sequence/cadence check.
Does not use gate_logdiff.py, w4b_logdiff.py or w4b_extra.py. Stdlib only, single-threaded; run with python -B.

Normalisation (otherwise exact text): drop the leading '[timestamp] ' and the '[tNNN] ' thread tag (level and category
stay in the key), replace 'runs\\NNNN-xxx' with 'runs\\<RUN>', strip trailing whitespace. Numbers and hex are kept, so
a changed guest address / count / value is a different message. Toypad[Write]/[Read ] payload lines are reduced to the
frame header (Write: first 5 bytes, Read: first 4) and compared by count (challenge bytes are random). Un-timestamped
lines (the D3D12 feature list) are keys of their own with level 'cont'.
Output: independent_check.txt and independent_check.json next to this script (the text also goes to stdout).
"""
import glob
import json
import os
import re
from collections import Counter, OrderedDict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
RUNS = os.path.join(ROOT, 'build', 'agent8', 'matrix', '20261122-1541', 'runs')
GROUPS = OrderedDict([
    ('d0', ['1542-d0-r1', '1558-d0-r2', '1604-d0-r3', '1611-d0-r4']),
    ('B', ['1545-B-r1', '1551-B-r2', '1606-B-r3', '1613-B-r4']),
    ('d3', ['1547-d3-r1', '1553-d3-r2', '1600-d3-r3', '1615-d3-r4']),
    ('d11t', ['1549-d11t-r1', '1556-d11t-r2', '1602-d11t-r3', '1608-d11t-r4']),
    ('cold-d0', ['1541-cold-d0']),
])
ARMS = ['B', 'd3']
WARN = ('warning', 'error', 'critical')
LINE_RE = re.compile(r'^\[(?P<ts>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d(?:\.\d+)?)\] \[(?P<lvl>[a-z]+)\] \[(?P<cat>[^\]]*)\] '
                     r'(?:\[t\d+\] )?(?P<msg>.*)$')
RUNDIR_RE = re.compile(r'runs([\\/])\d{4}-[A-Za-z0-9_.-]+')
TP_RE = re.compile(r'^Toypad\[(?P<dir>Read |Write)\] (?P<hex>[0-9A-Fa-f]{2}(?: [0-9A-Fa-f]{2})*)$')
ROT_RE = re.compile(r'^game(?:\.(\d+))?\.log$', re.I)
CLEAN_TAIL = ['Window closing, shutting down...', 'Execution complete', 'Title terminated; hard-exiting process.']
TP_ANY = re.compile(r'toypad|portal', re.I)
TP_ALLOWED = [
    ('payload', re.compile(r'^Toypad\[(?:Read |Write)\] ')),
    ('detected frame offset', re.compile(r'^Toypad: detected frame offset')),
    ('pad 0 mode', re.compile(r'^Toypad: pad 0 mode')),
    ('listener active', re.compile(r'^Toypad listener active')),
    ('emulated ToyPad active', re.compile(r'^Toypad: emulated LEGO Dimensions ToyPad active')),
    ('Portal: using emulated', re.compile(r'^Portal: using the emulated ToyPad\.')),
]
GREP = [('STUCK', re.compile(r'STUCK')), ('REX_FATAL', re.compile(r'REX_FATAL')),
        ('unimplemented', re.compile(r'unimplemented', re.I)), ('[critical]', re.compile(r'\[critical\]')),
        ('[error]', re.compile(r'\[error\]'))]
HOST_TIMER = 'Host timer resolution set to'


def log_files(d):
    found = []
    for p in glob.glob(os.path.join(d, 'game*.log')):
        m = ROT_RE.match(os.path.basename(p))
        if m:
            found.append((int(m.group(1)) if m.group(1) else 0, p))
    found.sort(key=lambda t: -t[0])  # oldest (highest rotation index) first
    return [p for _, p in found]


def parse_ts(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f' if '.' in s else '%Y-%m-%d %H:%M:%S')


def parse_run(name):
    d = os.path.join(RUNS, name)
    files = log_files(d)
    recs, raw = [], []
    for fp in files:
        with open(fp, 'rb') as fh:
            text = fh.read().decode('utf-8', errors='replace')
        for line in text.split('\n'):
            line = line.rstrip('\r')
            if not line.strip():
                continue
            raw.append(line)
            m = LINE_RE.match(line)
            if m:
                ts, lvl, cat, msg = parse_ts(m.group('ts')), m.group('lvl'), m.group('cat'), m.group('msg')
            else:
                ts, lvl, cat, msg = None, 'cont', '', line
            msg = RUNDIR_RE.sub(lambda mm: 'runs' + mm.group(1) + '<RUN>', msg).rstrip()
            tp = TP_RE.match(msg)
            tpdir = tpbytes = None
            keymsg = msg
            if tp:
                tpdir = tp.group('dir')
                tpbytes = tp.group('hex').upper().split()
                keymsg = 'Toypad[%s] %s ..' % (tpdir, ' '.join(tpbytes[:5 if tpdir == 'Write' else 4]))
            key = ('[%s] [%s] %s' % (lvl, cat, keymsg)) if lvl != 'cont' else '[cont] ' + keymsg
            recs.append(dict(ts=ts, lvl=lvl, cat=cat, msg=msg, key=key, tpdir=tpdir, tpbytes=tpbytes, raw=line))
    return dict(name=name, dir=d, files=files, recs=recs, raw=raw, keys=Counter(r['key'] for r in recs))


def rel(ts, base):
    return None if ts is None or base is None else round((ts - base).total_seconds(), 3)


def crash(p):
    d = p['dir']
    rjp = os.path.join(d, 'run.json')
    rj = {}
    if os.path.exists(rjp):
        with open(rjp, encoding='utf-8-sig') as fh:
            rj = json.load(fh)
    close = rj.get('close') or {}
    dumps = []
    for pat in ('*.dmp', '*.mdmp', '*.hdmp'):
        dumps += [os.path.relpath(x, d) for x in glob.glob(os.path.join(d, '**', pat), recursive=True)]
    tail = [r['msg'] for r in p['recs'][-3:]]
    greps = OrderedDict((label, [l for l in p['raw'] if rx.search(l)]) for label, rx in GREP)
    return OrderedDict(
        run_json_found=bool(rj), status=rj.get('status'), problems=rj.get('problems'),
        exit_code_hex=rj.get('exit_code_hex'), close_exit_code_hex=close.get('exit_code_hex'),
        exited_early=rj.get('exited_early'), close_killed=close.get('killed'),
        close_exit_wait_s=close.get('exit_wait_s'), close_wm_close_repost_s=close.get('wm_close_repost_s'),
        werfault_seen=rj.get('werfault_seen'), foreign_crash_dumps=rj.get('foreign_crash_dumps'),
        dialogs=rj.get('dialogs'), not_responding_samples=rj.get('not_responding_samples'),
        perf_csv_stalled=rj.get('perf_csv_stalled'), valid_timing=rj.get('valid_timing'),
        valid_timing_why=rj.get('valid_timing_why'), build_procs_window=rj.get('build_procs_window'),
        excluded=rj.get('excluded'), flags=rj.get('flags'), run_json_log_lines=rj.get('log_lines'),
        my_lines=len(p['recs']), dumps=dumps, tail=tail, tail_clean=tail == CLEAN_TAIL,
        grep_counts=OrderedDict((k, len(v)) for k, v in greps.items()),
        grep_examples=OrderedDict((k, v[:3]) for k, v in greps.items() if v),
        host_timer_lines=[l for l in p['raw'] if HOST_TIMER in l])


def toypad(p):
    recs = p['recs']
    writes = [r for r in recs if r['tpdir'] == 'Write']
    reads = [r for r in recs if r['tpdir'] == 'Read ']
    first_ts = next((r['ts'] for r in recs if r['ts'] is not None), None)
    t0 = writes[0]['ts'] if writes else None
    close_ts = next((r['ts'] for r in recs if r['msg'] == CLEAN_TAIL[0]), None)
    cmds = [r['tpbytes'][4] if len(r['tpbytes']) > 4 else '?' for r in writes]
    b1w = [r for r, c in zip(writes, cmds) if c == 'B1']
    b1 = [rel(r['ts'], t0) for r in b1w]
    wctr = [int(r['tpbytes'][5], 16) for r in writes if len(r['tpbytes']) > 5]
    rctr = [int(r['tpbytes'][4], 16) for r in reads if len(r['tpbytes']) > 4]
    other = [r['raw'] for r in recs if TP_ANY.search(r['msg']) and not any(rx.search(r['msg']) for _, rx in TP_ALLOWED)]
    allowed = Counter(lbl for r in recs for lbl, rx in TP_ALLOWED if rx.search(r['msg']))
    det_w = [' '.join(r['tpbytes']) for r, c in zip(writes, cmds) if c not in ('B1', 'B3')]
    det_r = [' '.join(r['tpbytes']) for r in reads if ' '.join(r['tpbytes'][:4]) != '0B 0C 55 09']
    return OrderedDict(
        writes=len(writes), reads=len(reads), cmd_seq=cmds, b1_s_after_first_write=b1,
        b1_gaps_s=[round(y - x, 3) for x, y in zip(b1, b1[1:])],
        b1_s_after_first_log=[rel(r['ts'], first_ts) for r in b1w],
        first_write_s_after_first_log=rel(t0, first_ts), close_s_after_first_write=rel(close_ts, t0),
        close_s_after_first_log=rel(close_ts, first_ts),
        last_b1_to_close_s=(round(rel(close_ts, t0) - b1[-1], 3) if b1 and close_ts and t0 else None),
        write_counters=wctr, read_counters=rctr,
        counters_ok=(wctr == list(range(1, len(wctr) + 1)) and rctr == wctr),
        b1_always_followed_by_b3=all(i + 1 < len(cmds) and cmds[i + 1] == 'B3' for i, c in enumerate(cmds) if c == 'B1'),
        write_headers=dict(Counter(' '.join(r['tpbytes'][:5]) for r in writes)),
        read_headers=dict(Counter(' '.join(r['tpbytes'][:4]) for r in reads)),
        det_payloads=det_w + det_r, allowed_line_counts=dict(sorted(allowed.items())), other_toypad_lines=other)


def main():
    P = OrderedDict()
    for g, names in GROUPS.items():
        for n in names:
            P[n] = parse_run(n)
    group_of = {n: g for g, names in GROUPS.items() for n in names}
    lvl_of = {}
    for p in P.values():
        for r in p['recs']:
            lvl_of.setdefault(r['key'], r['lvl'])
    out = []
    w = out.append
    J = OrderedDict()

    def gw(key):  # groups (runs) that have the key
        return ' '.join('%s %d/%d' % (g, sum(1 for n in names if P[n]['keys'][key]), len(names))
                        for g, names in GROUPS.items() if any(P[n]['keys'][key] for n in names))

    def gm(key):  # groups (runs) that lack the key
        return ' '.join('%s %d/%d' % (g, sum(1 for n in names if not P[n]['keys'][key]), len(names))
                        for g, names in GROUPS.items() if any(not P[n]['keys'][key] for n in names))

    w('== 1. per-run overview: non-empty lines, log files, levels, distinct keys ==')
    for n, p in P.items():
        lv = Counter(r['lvl'] for r in p['recs'])
        w('  %-13s %-7s %3d lines, files %s, %s, %d keys' % (
            n, group_of[n], len(p['recs']), ','.join(os.path.basename(f) for f in p['files']) or 'NONE',
            ' '.join('%s=%d' % kv for kv in sorted(lv.items())), len(p['keys'])))
    d0 = GROUPS['d0']
    d0_union = set().union(*(set(P[n]['keys']) for n in d0))
    d0_all = set.intersection(*(set(P[n]['keys']) for n in d0))
    w('')
    w('== 2. d0-internal: keys present in some but not all 4 warm d0 runs (d0 counts r1..r4) ==')
    for k in sorted(d0_union - d0_all):
        w('  %s  %s  [%s]' % ([P[n]['keys'][k] for n in d0], k, gw(k)))
    J['d0_partial_keys'] = sorted(d0_union - d0_all)

    for arm in ARMS:
        runs = GROUPS[arm]
        arm_union = set().union(*(set(P[n]['keys']) for n in runs))
        A = [OrderedDict(key=k, lvl=lvl_of[k], per_run=OrderedDict((n, P[n]['keys'][k]) for n in runs), groups=gw(k))
             for k in sorted(arm_union - d0_union)]
        Bm = []
        for k in sorted(d0_all):
            miss = [n for n in runs if not P[n]['keys'][k]]
            if miss:
                Bm.append(OrderedDict(key=k, lvl=lvl_of[k], missing_in=miss, d0_counts=[P[n]['keys'][k] for n in d0],
                                      groups_missing=gm(k)))
        C, D = [], []
        for k in sorted(arm_union | d0_union):
            cs = [P[n]['keys'][k] for n in d0]
            lo, hi = min(cs), max(cs)
            outr = OrderedDict((n, P[n]['keys'][k]) for n in runs if not lo <= P[n]['keys'][k] <= hi)
            if outr:
                (C if lvl_of[k] in WARN else D).append(OrderedDict(key=k, lvl=lvl_of[k], d0_counts=cs, outside=outr))
        w('')
        w('== 3. arm %s (%s) vs warm d0 ==' % (arm, ', '.join(runs)))
        w('(a) messages in some %s run and in no warm d0 run (any level): %d' % (arm, len(A)))
        for x in A:
            w('    %s  per-run %s  groups having it: %s' % (x['key'], list(x['per_run'].values()), x['groups']))
        w('(b) messages in all 4 d0 runs but missing from some %s run: %d' % (arm, len(Bm)))
        for x in Bm:
            w('    %s  missing in %s  d0 %s  groups missing it: %s' % (x['key'], x['missing_in'], x['d0_counts'],
                                                                     x['groups_missing']))
        w('(c) warning/error/critical messages with a per-run count outside d0 min..max: %d' % len(C))
        for x in C:
            w('    %s  d0 %s  outside %s' % (x['key'], x['d0_counts'], dict(x['outside'])))
        w('(d) [extra] info/cont messages with a per-run count outside d0 min..max: %d' % len(D))
        for x in D:
            w('    %s  d0 %s  outside %s' % (x['key'], x['d0_counts'], dict(x['outside'])))
        J['arm_' + arm] = OrderedDict(a_only_in_arm=A, b_gone=Bm, c_warn_count_outside=C, d_info_count_outside=D)

    w('')
    w('== 4. crash evidence (run.json fields, dumps, last 3 log lines, grep STUCK/REX_FATAL/unimplemented(i)/[critical]/[error]) ==')
    CR = OrderedDict()
    for n in GROUPS['d0'] + GROUPS['B'] + GROUPS['d3'] + GROUPS['cold-d0']:
        c = crash(P[n])
        CR[n] = c
        w('  %-13s status=%s problems=%s exit=%s close.exit=%s early=%s killed=%s exit_wait_s=%s repost_s=%s wer=%s '
          'foreign_dumps=%s dialogs=%s notresp=%s perf_stalled=%s | valid_timing=%s why=%s build_procs_window=%s '
          'excluded=%s | dumps=%s tail_clean=%s lines run.json/mine=%s/%s | grep %s' % (
              n, c['status'], c['problems'], c['exit_code_hex'], c['close_exit_code_hex'], c['exited_early'],
              c['close_killed'], c['close_exit_wait_s'], c['close_wm_close_repost_s'], c['werfault_seen'],
              c['foreign_crash_dumps'], c['dialogs'], c['not_responding_samples'], c['perf_csv_stalled'],
              c['valid_timing'], c['valid_timing_why'], c['build_procs_window'], c['excluded'], c['dumps'],
              c['tail_clean'], c['run_json_log_lines'], c['my_lines'],
              ' '.join('%s=%d' % kv for kv in c['grep_counts'].items())))
        if not c['tail_clean']:
            w('      tail: %s' % c['tail'])
        for k, v in c['grep_examples'].items():
            for l in v:
                w('      GREP %s: %s' % (k, l))
    J['crash'] = CR

    w('')
    w("== 5. '%s' lines per run ==" % HOST_TIMER)
    HT = OrderedDict()
    for g, names in GROUPS.items():
        HT[g] = OrderedDict((n, sum(1 for l in P[n]['raw'] if HOST_TIMER in l)) for n in names)
        w('  %-7s %s' % (g, '  '.join('%s:%d' % kv for kv in HT[g].items())))
    for n in GROUPS['d11t']:
        for l in P[n]['raw']:
            if HOST_TIMER in l:
                w('    e.g. %s: %s' % (n, l))
                break
    J['host_timer'] = HT

    w('')
    w('== 6. Toypad (cmd = 5th byte of each Toypad[Write]; B1 times in s after the first Toypad write) ==')
    TP = OrderedDict()
    for n in GROUPS['d0'] + GROUPS['B'] + GROUPS['d3'] + GROUPS['cold-d0'] + GROUPS['d11t']:
        t = toypad(P[n])
        TP[n] = t
        w('  %-13s W/R %2d/%-2d seq %-32s B1 at %-34s gaps %-24s first write @%-6s close @%-7s last B1->close %-7s '
          'ctr_ok %s B1->B3 %s other %d' % (
              n, t['writes'], t['reads'], ' '.join(t['cmd_seq']), t['b1_s_after_first_write'], t['b1_gaps_s'],
              t['first_write_s_after_first_log'], t['close_s_after_first_write'], t['last_b1_to_close_s'],
              t['counters_ok'], t['b1_always_followed_by_b3'], len(t['other_toypad_lines'])))
        for l in t['other_toypad_lines']:
            w('      OTHER TOYPAD LINE: %s' % l)
    w('  (first write @ = s after the first log line; close @ = s after the first Toypad write)')
    det = Counter(tuple(t['det_payloads']) for t in TP.values())
    w('  deterministic payloads (B0/C0 writes + their 2 reads, all bytes): %d distinct set(s) over %d runs' % (
        len(det), len(TP)))
    alw = Counter(tuple((k, v) for k, v in sorted(t['allowed_line_counts'].items()) if k != 'payload')
                  for t in TP.values())
    w('  non-payload Toypad line count patterns (excluding payload lines): %s' % [dict(k) for k in alw])
    hdr = Counter(tuple(sorted(set(t['write_headers']) | set(t['read_headers']))) for t in TP.values())
    w('  distinct header sets over all runs: %d -> %s' % (len(hdr), [list(h) for h in hdr]))
    for g in ('d0', 'B', 'd3', 'd11t'):
        b1s = [TP[n]['b1_s_after_first_write'] for n in GROUPS[g]]
        maxlen = max(len(x) for x in b1s)
        rng = []
        for i in range(maxlen):
            v = [x[i] for x in b1s if len(x) > i]
            rng.append('#%d %s..%s (n=%d)' % (i + 1, min(v), max(v), len(v)))
        gaps = [gp for n in GROUPS[g] for gp in TP[n]['b1_gaps_s']]
        lbc = [TP[n]['last_b1_to_close_s'] for n in GROUPS[g]]
        cl = [TP[n]['close_s_after_first_write'] for n in GROUPS[g]]
        w('  %-5s W/R %s | B1 %s | B1 gaps %s..%s | last B1->close %s | close@ %s' % (
            g, ['%d/%d' % (TP[n]['writes'], TP[n]['reads']) for n in GROUPS[g]], '; '.join(rng),
            min(gaps) if gaps else None, max(gaps) if gaps else None, lbc, cl))
    J['toypad'] = TP

    w('')
    w('== 7. cross-check items per arm ==')
    for arm in ARMS:
        runs = GROUPS[arm]
        X = J['arm_' + arm]
        new_warn = [x for x in X['a_only_in_arm'] if x['lvl'] in WARN]
        more = [x for x in X['c_warn_count_outside'] if any(v > max(x['d0_counts']) for v in x['outside'].values())]
        less = [x for x in X['c_warn_count_outside'] if any(v < min(x['d0_counts']) for v in x['outside'].values())]
        gone_warn = [x for x in X['b_gone'] if x['lvl'] in WARN]
        w('  %s: NEW warn/err/crit keys %d | MORE (warn count > d0 max) %d | LESS (< d0 min) %d | GONE warn %d | '
          'GONE any level %d | ONLY-in-arm any level %d | info/cont count outside d0 range %d' % (
              arm, len(new_warn), len(more), len(less), len(gone_warn), len(X['b_gone']), len(X['a_only_in_arm']),
              len(X['d_info_count_outside'])))
        w('     Toypad W/R %s (d0 %s)' % (['%d/%d' % (TP[n]['writes'], TP[n]['reads']) for n in runs],
                                         ['%d/%d' % (TP[n]['writes'], TP[n]['reads']) for n in d0]))
        w('     exit %s | tail clean %s | dumps %s | WER %s | killed %s | early %s | status %s | host-timer lines %s' % (
            [CR[n]['exit_code_hex'] for n in runs], [CR[n]['tail_clean'] for n in runs],
            [len(CR[n]['dumps']) for n in runs], [CR[n]['werfault_seen'] for n in runs],
            [CR[n]['close_killed'] for n in runs], [CR[n]['exited_early'] for n in runs],
            [CR[n]['status'] for n in runs], [HT[arm][n] for n in runs]))
    txt = '\n'.join(out)
    with open(os.path.join(HERE, 'independent_check.txt'), 'w', encoding='utf-8') as fh:
        fh.write(txt + '\n')
    with open(os.path.join(HERE, 'independent_check.json'), 'w', encoding='utf-8') as fh:
        json.dump(J, fh, indent=1)
    print(txt)


if __name__ == '__main__':
    main()
